"""The API index is a front door that can never lie.

data/api.json is built by walking the assembled artifact: an endpoint appears
only if the file exists in the deploy. The catalog holds descriptions; the
artifact holds the truth.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_api_index as A  # noqa: E402


def _site(tmp_path, files):
    for rel, body in files.items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding="utf-8")
    return tmp_path


def test_lists_only_what_exists(tmp_path):
    site = _site(tmp_path, {
        "data/radar.json": json.dumps({"generated_at": "2026-07-16T06:00:00+00:00"}),
        "feeds/new.xml": "<rss/>",
    })
    idx = A.build_index(site)
    paths = [e["path"] for e in idx["endpoints"]]
    assert "data/radar.json" in paths
    assert "feeds/new.xml" in paths
    assert "data/signals.json" not in paths        # absent file, absent claim
    assert "data/projects.csv" not in paths


def test_generated_at_comes_from_the_data(tmp_path):
    site = _site(tmp_path, {
        "data/radar.json": json.dumps({"generated_at": "2026-07-16T06:00:00+00:00"})})
    assert A.build_index(site)["generated_at"] == "2026-07-16T06:00:00+00:00"


def test_schema_pointer_only_when_schema_shipped(tmp_path):
    with_schema = A.build_index(_site(tmp_path / "a", {
        "data/signals.json": "{}",
        "data/signals.schema.json": "{}"}))
    sig = next(e for e in with_schema["endpoints"] if e["path"] == "data/signals.json")
    assert sig["schema"].endswith("data/signals.schema.json")

    without = A.build_index(_site(tmp_path / "b", {"data/signals.json": "{}"}))
    sig2 = next(e for e in without["endpoints"] if e["path"] == "data/signals.json")
    assert "schema" not in sig2                    # no shipped schema, no pointer


def test_every_endpoint_carries_the_contract_fields(tmp_path):
    site = _site(tmp_path, {"data/radar.json": "{}", "feed.xml": "<rss/>"})
    idx = A.build_index(site)
    for e in idx["endpoints"]:
        assert e["url"].startswith(A.BASE + "/")
        assert e["kind"] and e["description"] and e["stability"]
        assert isinstance(e["bytes"], int) and e["bytes"] >= 0


def test_index_is_deterministic_and_versioned(tmp_path):
    site = _site(tmp_path, {"data/radar.json": json.dumps({"generated_at": "x"})})
    a, b = A.build_index(site), A.build_index(site)
    assert a == b
    assert a["api_version"] == 1
    assert a["licensing"]["commercial"].endswith("connect@axonos.org")
    assert [e["path"] for e in a["endpoints"]] == sorted(e["path"] for e in a["endpoints"])


def test_empty_site_yields_empty_but_valid_index(tmp_path):
    idx = A.build_index(tmp_path)
    assert idx["endpoints"] == []
    assert idx["api_version"] == 1
