"""The sync path is a write path into main — nothing invalid may pass it."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import sync_engine_data as S  # noqa: E402


def _valid_payload():
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "radar.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def _run(monkeypatch, remote_obj, *, newer=True):
    """Drive main() with a canned engine payload; record every PUT."""
    puts = []
    body = json.dumps(remote_obj)
    if newer:
        remote_obj["generated_at"] = "2099-01-01T00:00:00+00:00"
        body = json.dumps(remote_obj)

    def fake_fetch(path):
        S.FETCH_ERR["kind"] = None
        return body if path == "data/radar.json" else None

    def fake_api(method, url, payload=None):
        if method == "PUT":
            puts.append(url)
        return 200, {}

    monkeypatch.setattr(S, "fetch_raw", fake_fetch)
    monkeypatch.setattr(S, "api", fake_api)
    monkeypatch.setattr(S, "sync_report_html", lambda: None)
    monkeypatch.setattr(S, "TOKEN", "t")
    monkeypatch.setattr(S, "REPO", "x/y")
    rc = S.main()
    return rc, puts


def test_valid_payload_passes_the_gate(monkeypatch):
    rc, puts = _run(monkeypatch, _valid_payload())
    assert rc == 0
    assert any("radar.json" in u for u in puts)


def test_corrupt_counts_are_refused_wholesale(monkeypatch):
    bad = _valid_payload()
    bad["counts"]["total"] = 999
    rc, puts = _run(monkeypatch, bad)
    assert rc == 1
    assert puts == []                       # not one file committed


def test_non_json_is_refused(monkeypatch):
    puts = []
    monkeypatch.setattr(S, "fetch_raw",
                        lambda p: "{not json" if p == "data/radar.json" else None)
    monkeypatch.setattr(S, "api",
                        lambda m, u, payload=None: (puts.append(u) or (200, {})) if m == "PUT" else (200, {}))
    monkeypatch.setattr(S, "sync_report_html", lambda: None)
    monkeypatch.setattr(S, "TOKEN", "t")
    monkeypatch.setattr(S, "REPO", "x/y")
    assert S.main() == 1 and puts == []


def test_missing_generated_at_is_refused(monkeypatch):
    puts = []
    monkeypatch.setattr(S, "fetch_raw",
                        lambda p: '{"projects": []}' if p == "data/radar.json" else None)
    monkeypatch.setattr(S, "api",
                        lambda m, u, payload=None: (puts.append(u) or (200, {})) if m == "PUT" else (200, {}))
    monkeypatch.setattr(S, "sync_report_html", lambda: None)
    monkeypatch.setattr(S, "TOKEN", "t")
    monkeypatch.setattr(S, "REPO", "x/y")
    assert S.main() == 1 and puts == []


def test_transient_upstream_says_transient(monkeypatch, capsys):
    def fake_fetch(path):
        S.FETCH_ERR["kind"] = "transient"
        return None
    monkeypatch.setattr(S, "fetch_raw", fake_fetch)
    monkeypatch.setattr(S, "sync_report_html", lambda: None)
    monkeypatch.setattr(S, "TOKEN", "t")
    monkeypatch.setattr(S, "REPO", "x/y")
    assert S.main() == 0
    out = capsys.readouterr().out
    assert "transient" in out and "ENGINE_READ_TOKEN" not in out


def test_private_engine_names_the_remedy(monkeypatch, capsys):
    def fake_fetch(path):
        S.FETCH_ERR["kind"] = "absent"
        return None
    monkeypatch.setattr(S, "fetch_raw", fake_fetch)
    monkeypatch.setattr(S, "sync_report_html", lambda: None)
    monkeypatch.setattr(S, "TOKEN", "t")
    monkeypatch.setattr(S, "REPO", "x/y")
    assert S.main() == 0
    assert "ENGINE_READ_TOKEN" in capsys.readouterr().out
