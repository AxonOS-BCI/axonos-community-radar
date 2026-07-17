"""Per-project badges: derived, never granted, and path-safe.

The badge says whatever the engine scored on the last scan — nothing else can
put words on it. And a project's name is attacker-influenced text that becomes
a filesystem path, so anything that is not a GitHub-shaped owner/repo never
touches the disk.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_badges as B  # noqa: E402


def _radar(projects):
    return {"generated_at": "2026-07-16T14:21:13+00:00", "projects": projects}


def _p(name, brs=87, tier="L4_EXPLICIT_BCI"):
    return {"full_name": name, "brs": brs, "relevance_tier": tier}


def test_shields_schema(tmp_path):
    B.build(_radar([_p("a/b")]), tmp_path)
    b = json.loads((tmp_path / "badges" / "a" / "b.json").read_text())
    assert b["schemaVersion"] == 1
    assert b["label"] == "AxonOS Radar"
    assert b["message"] == "BRS 87 · Explicit BCI"
    assert b["cacheSeconds"] == 10800


def test_color_bands_with_boundaries():
    assert B.color_for(100) == "34d399" and B.color_for(80) == "34d399"
    assert B.color_for(79) == "2dd4ff" and B.color_for(60) == "2dd4ff"
    assert B.color_for(59) == "fbbf24" and B.color_for(40) == "fbbf24"
    assert B.color_for(None) == "8a97a6"


def test_no_brs_is_honest():
    m = B.message_for({"brs": None, "relevance_tier": None})
    assert m == "on the map"          # no number invented


def test_hostile_names_never_touch_disk(tmp_path):
    hostile = [
        _p("../../etc/passwd"), _p("a/../b"), _p("a/b/c"),
        _p("owner/re<script>"), _p("just-one-segment"), _p(""),
    ]
    idx = B.build(_radar(hostile + [_p("good/name")]), tmp_path)
    assert idx["count"] == 1
    written = sorted(str(f.relative_to(tmp_path)) for f in tmp_path.rglob("*.json"))
    assert written == ["badges/good/name.json", "badges/index.json"]


def test_dots_and_dashes_are_normal_github_names(tmp_path):
    idx = B.build(_radar([_p("dot.owner/repo-name.js")]), tmp_path)
    assert idx["count"] == 1
    assert (tmp_path / "badges" / "dot.owner" / "repo-name.js.json").exists()


def test_index_carries_ready_markdown(tmp_path):
    idx = B.build(_radar([_p("a/b")]), tmp_path)
    e = idx["projects"]["a/b"]
    assert e["badge"].endswith("/badges/a/b.json")
    assert "img.shields.io/endpoint?url=" in e["markdown"]
    assert "https%3A%2F%2F" in e["markdown"]          # endpoint URL is encoded
    assert e["markdown"].startswith("[![AxonOS Radar](")


def test_deterministic(tmp_path):
    r = _radar([_p("a/b"), _p("c/d", brs=61, tier="L2_NEURO_TERM")])
    a = B.build(r, tmp_path / "x")
    b = B.build(r, tmp_path / "y")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
