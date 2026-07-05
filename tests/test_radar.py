"""Tests for the radar data pipeline — relevance, categorisation, determinism, safety."""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import radar  # noqa: E402

CORE = {"bci", "eeg", "neurotechnology"}
CONTEXT = {"real-time", "privacy", "rust", "no-std"}
KEYWORDS = ["eeg", "bci", "neural", "neuro", "cortical", "prosthe"]
CATS = {
    "Decoding & ML": ["machine-learning", "deep-learning", "decoding"],
    "Hardware & Acquisition": ["eeg", "hardware", "electrode"],
    "Real-time & Embedded": ["no-std", "real-time", "rtos"],
}


def test_core_topic_is_relevant():
    repo = {"topics": ["eeg", "python"], "description": "an eeg toolkit", "full_name": "a/x", "language": "Python"}
    assert radar.is_relevant(repo, CORE, CONTEXT, KEYWORDS) is True


def test_context_plus_keyword_is_relevant():
    repo = {"topics": ["real-time"], "description": "neural decoder firmware", "full_name": "a/x", "language": "Rust"}
    assert radar.is_relevant(repo, CORE, CONTEXT, KEYWORDS) is True


def test_generic_context_without_keyword_is_dropped():
    # a generic privacy/real-time repo with no neuro signal must be excluded
    repo = {"topics": ["privacy", "real-time"], "description": "a fast VPN proxy list", "full_name": "v/proxy", "language": "Go"}
    assert radar.is_relevant(repo, CORE, CONTEXT, KEYWORDS) is False


def test_password_manager_is_dropped():
    repo = {"topics": ["cryptography", "rust"], "description": "secure password manager", "full_name": "x/pw", "language": "Rust"}
    assert radar.is_relevant(repo, CORE, CONTEXT, KEYWORDS) is False


def test_short_keyword_is_word_anchored():
    # regression: short keywords like 'erp' must not substring-match unrelated words
    # ('cleverpad', 'interpreter'); matching is anchored at a word start.
    kw = KEYWORDS + ["erp", "lfp"]
    midi = {"topics": ["no-std"], "description": "firmware for cleverpad midi controller", "full_name": "d/open-cleverpad", "language": "Rust"}
    lang = {"topics": ["no-std"], "description": "a language interpreter with z3", "full_name": "o/mimi", "language": "Rust"}
    assert radar.is_relevant(midi, CORE, CONTEXT, kw) is False
    assert radar.is_relevant(lang, CORE, CONTEXT, kw) is False
    # a genuine standalone 'erp' (event-related potential) still matches
    erp = {"topics": ["signal-processing"], "description": "a P300 erp classifier", "full_name": "a/erp", "language": "Python"}
    assert radar.is_relevant(erp, CORE, {"signal-processing"}, kw) is True


def test_categorise_ml():
    repo = {"topics": ["eeg", "deep-learning"], "description": "deep learning for EEG", "full_name": "t/braindecode", "language": "Python"}
    assert radar.categorise(repo, CATS) == "Decoding & ML"


def test_categorise_embedded():
    repo = {"topics": ["no-std", "real-time"], "description": "bare metal rtos", "full_name": "t/rt", "language": "Rust"}
    assert radar.categorise(repo, CATS) == "Real-time & Embedded"


def test_score_is_deterministic_within_slot():
    # days_since from a fixed snapshot must be stable regardless of call time
    snap = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
    d1 = radar.days_since("2026-06-10T00:00:00Z", snap)
    d2 = radar.days_since("2026-06-10T00:00:00Z", snap)
    assert d1 == d2 == 14


def test_snapshot_aligns_to_six_hour_slot():
    _, snap = radar.snapshot_now()
    assert snap.hour in (0, 6, 12, 18)
    assert snap.minute == 0 and snap.second == 0


def test_validate_rejects_non_github_url():
    bad = {"counts": {"total": 1}, "projects": [{"full_name": "a/x", "html_url": "javascript:alert(1)", "category": "Other"}]}
    try:
        radar.validate(bad, 120)
    except AssertionError:
        return
    raise AssertionError("validate should have rejected a non-github url")


def test_validate_accepts_clean_payload():
    ok = {"counts": {"total": 1}, "projects": [{"full_name": "a/x", "html_url": "https://github.com/a/x", "category": "Decoding & ML"}]}
    radar.validate(ok, 120)


def test_feed_is_wellformed_xml():
    import xml.dom.minidom as minidom
    projects = [{"full_name": "a/x", "html_url": "https://github.com/a/x", "description": "d & <b>", "category": "Other", "first_seen": "2026-06-24T12:00:00+00:00"}]
    xml = radar.build_feed(projects, datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc))
    minidom.parseString(xml)  # raises if malformed (escaping works)
    assert "<rss" in xml and "a/x" in xml


def test_publish_normalizers():
    import publish_data as pd
    a = '{"generated_at":"t1","projects":[{"full_name":"a/x"}],"counts":{"total":1}}'
    b = '{"generated_at":"t2","projects":[{"full_name":"a/x"}],"counts":{"total":1}}'
    c = '{"generated_at":"t2","projects":[{"full_name":"a/x"},{"full_name":"b/y"}],"counts":{"total":2}}'
    assert pd.norm_radar(a) == pd.norm_radar(b)   # timestamp-only diff ignored
    assert pd.norm_radar(a) != pd.norm_radar(c)   # project change detected
    f1 = "<rss><lastBuildDate>x</lastBuildDate><item>a</item></rss>"
    f2 = "<rss><lastBuildDate>y</lastBuildDate><item>a</item></rss>"
    assert pd.norm_feed(f1) == pd.norm_feed(f2)


def test_days_since_naive_timestamp_assumes_utc():
    from datetime import datetime, timezone
    snap = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
    # a naive timestamp (no Z/offset) must be treated as UTC, not crash
    assert radar.days_since("2026-06-10T00:00:00", snap) == 14


def test_validator_rejects_malicious_fixture():
    import json
    import validate_payload as vp
    fx = os.path.join(os.path.dirname(__file__), "fixtures", "malicious-radar.json")
    with open(fx, encoding="utf-8") as fh:
        payload = json.load(fh)
    errors = vp.validate_payload(payload)
    assert errors, "validator must reject the malicious payload"
    assert any("github.com" in e for e in errors), "must flag the non-github URL"


def test_validator_accepts_clean_payload():
    import validate_payload as vp
    payload = {"version": 3, "counts": {"total": 1}, "projects": [{
        "full_name": "owner/repo", "html_url": "https://github.com/owner/repo",
        "description": "clean", "stars": 5, "forks": 1, "language": "Rust",
        "category": "Signal Processing", "evidence_tier": "L3_EXPLICIT_BCI",
        "inclusion_reason": "Explicit BCI topic."}]}
    assert vp.validate_payload(payload) == []


def test_validator_rejects_lookalike_host():
    import validate_payload as vp
    payload = {"version": 2, "counts": {"total": 1}, "projects": [{
        "full_name": "a/b", "html_url": "https://github.com.evil.com/a/b",
        "category": "Other"}]}
    assert any("github.com" in e for e in vp.validate_payload(payload))


def test_validator_flags_impossible_star_jump():
    import validate_payload as vp
    payload = {"version": 3, "counts": {"total": 1}, "projects": [{
        "full_name": "a/b", "html_url": "https://github.com/a/b", "category": "Other",
        "stars": 10, "stars_delta_7d": 999,
        "evidence_tier": "L0_WEAK_ADJACENT", "inclusion_reason": "x"}]}
    assert any("impossible jump" in e for e in vp.validate_payload(payload))


# ── v3 data-model tests ──────────────────────────────────────────────────────

def test_evidence_tier_explicit_bci():
    repo = {"full_name": "o/r", "topics": ["bci", "eeg"], "description": "a bci toolkit"}
    tier, reason, mt, mk = radar.evidence_for(repo, {"bci"}, set(), ["eeg", "bci"])
    assert tier == "L3_EXPLICIT_BCI"
    assert "bci" in mt and "BCI" in reason


def test_evidence_tier_neural_signal():
    repo = {"full_name": "o/r", "topics": ["eeg"], "description": "eeg signal lib"}
    tier, *_ = radar.evidence_for(repo, set(), set(), ["eeg"])
    assert tier == "L2_NEURAL_SIGNAL"


def test_evidence_tier_context_plus_keyword():
    repo = {"full_name": "o/r", "topics": ["real-time"], "description": "prosthetic control"}
    tier, *_ = radar.evidence_for(repo, set(), {"real-time"}, ["prosthe"])
    assert tier == "L1_CONTEXT_PLUS_NEURO"


def test_evidence_tier_weak_adjacent():
    repo = {"full_name": "o/r", "topics": ["electrophysiology"], "description": "sim"}
    tier, *_ = radar.evidence_for(repo, set(), {"signal-processing"}, ["electrophysiolog"])
    assert tier == "L0_WEAK_ADJACENT"


def test_builders_need_two_projects():
    projects = [
        {"full_name": "acme/a", "stars": 10, "active": True, "category": "X", "language": "Rust"},
        {"full_name": "acme/b", "stars": 5, "active": False, "category": "X", "language": "Python"},
        {"full_name": "solo/c", "stars": 99, "active": True, "category": "Y", "language": "C"},
    ]
    builders = radar.build_builders(projects)
    assert len(builders) == 1 and builders[0]["owner"] == "acme"
    assert builders[0]["project_count"] == 2 and builders[0]["total_stars"] == 15


def test_enrich_preserves_existing_fields_and_first_run_not_rising():
    from datetime import datetime, timezone
    p = {"full_name": "o/r", "category": "Keep", "stars": 100, "active": True, "is_new": True, "_score": 1.2}
    seeds = {"core_topics": ["bci"], "context_topics": [], "neuro_keywords": ["eeg"]}
    snap = datetime(2026, 6, 26, tzinfo=timezone.utc)
    radar.enrich_v3([p], seeds, snap, {"version": 1, "snapshots": []})
    assert p["category"] == "Keep" and p["_score"] == 1.2 and p["is_new"] is True
    assert "evidence_tier" in p and p["owner"] == "o"
    assert p["rising"] is False and p["stars_delta_7d"] == 0  # first run never rising


def test_rising_detects_star_velocity():
    from datetime import datetime, timezone, timedelta
    snap = datetime(2026, 6, 26, 0, 0, 0, tzinfo=timezone.utc)
    old = (snap - timedelta(days=8)).isoformat()
    history = {"version": 1, "snapshots": [{"snapshot_at": old, "stars": {"o/r": 100}}]}
    projects = [{"full_name": "o/r", "stars": 120, "active": True}]
    seeds = {"core_topics": ["bci"], "context_topics": [], "neuro_keywords": ["eeg"]}
    radar.enrich_v3(projects, seeds, snap, history)
    assert projects[0]["stars_delta_7d"] == 20
    assert projects[0]["rising"] is True  # 20 >= max(2, ceil(120*0.05)=6)


def test_stats_issue_digest_renders_analytics():
    """The living issue must embed a Gartner-style quadrant + category pie (Mermaid)."""
    import importlib.util
    import os
    here = os.path.dirname(__file__)
    path = os.path.join(here, "..", "scripts", "publish_stats_issue.py")
    spec = importlib.util.spec_from_file_location("pstats", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    radar = {
        "counts": {"total": 3},
        "projects": [
            {"full_name": "a/x", "repo": "x", "html_url": "https://github.com/a/x",
             "stars": 1200, "forks": 300, "days_since_push": 0, "_score": 9,
             "category": "Decoding & ML", "language": "Python", "evidence_tier": "L3_EXPLICIT_BCI"},
            {"full_name": "b/y", "repo": "y", "html_url": "https://github.com/b/y",
             "stars": 400, "forks": 200, "days_since_push": 1, "_score": 7,
             "category": "Signal Processing", "language": "Rust", "evidence_tier": "L2_NEURAL_SIGNAL"},
            {"full_name": "c/z", "repo": "z", "html_url": "https://github.com/c/z",
             "stars": 90, "forks": 12, "days_since_push": 3, "_score": 5,
             "category": "Decoding & ML", "language": "Python", "evidence_tier": "L1_CONTEXT_PLUS_NEURO"},
            {"full_name": "d/w", "repo": "w", "html_url": "https://github.com/d/w",
             "stars": 50, "forks": 30, "days_since_push": 2, "_score": 4,
             "category": "Hardware", "language": "C", "evidence_tier": "L2_NEURAL_SIGNAL"},
        ],
        "builders": [],
    }
    body = mod.build_body(radar, {"snapshots": []}, "owner/repo")
    assert "```mermaid" in body
    assert "quadrantChart" in body
    assert "pie showData" in body
    assert body.startswith("<!-- axonos-radar-stats -->")
    # quadrant points must be inside the plotting range, not fabricated beyond [0,1]
    import re
    for xs, ys in re.findall(r"\[([\d.]+), ([\d.]+)\]", body):
        assert 0.0 <= float(xs) <= 1.0 and 0.0 <= float(ys) <= 1.0


def test_report_html_renders_and_is_csp_safe():
    """report.html must render all key sections with zero inline styles/scripts (strict CSP)."""
    import importlib.util
    import os
    here = os.path.dirname(__file__)
    path = os.path.join(here, "..", "scripts", "build_report.py")
    spec = importlib.util.spec_from_file_location("breport", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    radar = {
        "counts": {"total": 3},
        "projects": [
            {"full_name": "a/x", "repo": "x", "html_url": "https://github.com/a/x", "stars": 1200,
             "forks": 300, "days_since_push": 0, "_score": 9, "active": True,
             "category": "Decoding & ML", "language": "Python", "evidence_tier": "L3_EXPLICIT_BCI"},
            {"full_name": "b/y", "repo": "y", "html_url": "https://github.com/b/y", "stars": 400,
             "forks": 200, "days_since_push": 1, "_score": 7, "active": True,
             "category": "Signal Processing", "language": "Rust", "evidence_tier": "L2_NEURAL_SIGNAL"},
            {"full_name": "c/z", "repo": "z", "html_url": "https://github.com/c/z", "stars": 90,
             "forks": 12, "days_since_push": 3, "_score": 5, "active": False,
             "category": "Hardware & Acquisition", "language": "C", "evidence_tier": "L2_NEURAL_SIGNAL"},
            {"full_name": "d/w", "repo": "w", "html_url": "https://github.com/d/w", "stars": 50,
             "forks": 30, "days_since_push": 2, "_score": 4, "active": True,
             "category": "Decoding & ML", "language": "Python", "evidence_tier": "L1_CONTEXT_PLUS_NEURO"},
        ],
        "builders": [{"owner": "a", "html_url": "https://github.com/a", "project_count": 2,
                      "total_stars": 1600, "active_projects_30d": 2, "top_categories": ["Decoding & ML"]}],
    }
    out = mod.build(radar)
    assert 'style="' not in out and "<script" not in out and "<style" not in out
    assert "Content-Security-Policy" in out and "assets/report.css" in out
    assert 'class="quad"' in out and 'class="donut"' in out
    assert "All 4 tracked resources" in out  # full-field table present
    # every project appears in the full table
    for fn in ("a/x", "b/y", "c/z", "d/w"):
        assert fn in out


def test_v4_scoring_and_curated():
    """v4: multi-signal score is monotone + graceful; curated merge is honest."""
    import importlib.util, os
    here = os.path.dirname(__file__)
    def load(name):
        spec = importlib.util.spec_from_file_location(name, os.path.join(here, "..", "scripts", name + ".py"))
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
    radar = load("radar"); enrich = load("enrich")
    bare = {"stars": 1000, "days_since_push": 5}
    rich = {"stars": 1000, "days_since_push": 5, "total_downloads": 50000,
            "contributors": 80, "commits_52w": 1200, "releases_count": 15}
    assert radar.compute_score(rich) > radar.compute_score(bare) > 0
    assert radar.compute_score({"stars": 10}) > 0  # graceful with no enriched fields
    # funding platform keys are recognised
    assert "open_collective" in enrich._FUND_KEYS and "github" in enrich._FUND_KEYS
    # Link-header contributor count
    hdr = {"Link": '<https://api.github.com/x?per_page=1&page=42>; rel="last"'}
    assert enrich._last_page(hdr) == 42


# ── v4.3.0: audit-driven logic ───────────────────────────────────────────────
import json  # noqa: E402

def test_norm_excl_handles_messy_entries():
    got = radar._norm_excl([" Owner/Repo/ ", "owner2/repo2@main", "OWNER3", "", None])
    assert got == {"owner/repo", "owner2/repo2", "owner3"}


def test_categorise_tiebreak_is_deterministic():
    cats = {"Decoding & ML": ["decoder"], "Signal Processing": ["decoder"]}
    repo = {"full_name": "x/decoder", "topics": [], "description": ""}
    a = radar.categorise(repo, cats)
    b = radar.categorise(repo, dict(reversed(list(cats.items()))))
    assert a == b == "Decoding & ML"  # priority order, insertion-order independent


def test_quality_flags_split_unclear_from_missing():
    missing = radar.quality_flags_for({"license": None, "has_license": False,
                                       "description": "x", "topics": ["a"],
                                       "days_since_push": 1}, "L3_EXPLICIT_BCI")
    unclear = radar.quality_flags_for({"license": "NOASSERTION", "has_license": False,
                                       "description": "x", "topics": ["a"],
                                       "days_since_push": 1}, "L3_EXPLICIT_BCI")
    ok = radar.quality_flags_for({"license": "MIT", "has_license": True,
                                  "description": "x", "topics": ["a"],
                                  "days_since_push": 1}, "L3_EXPLICIT_BCI")
    assert missing["missing_license"] and not missing["unclear_license"]
    assert unclear["unclear_license"] and not unclear["missing_license"]
    assert not ok["missing_license"] and not ok["unclear_license"]


def test_falling_flag_and_counts():
    snap = datetime(2026, 7, 2, tzinfo=timezone.utc)
    hist = {"snapshots": [
        {"snapshot_at": "2026-06-24T00:00:00+00:00", "stars": {"a/b": 100, "c/d": 100}},
    ]}
    seeds = {"core_topics": ["bci"], "context_topics": [], "neuro_keywords": []}
    projects = [
        {"full_name": "a/b", "stars": 95, "topics": ["bci"], "description": "",
         "pushed_at": "2026-07-01T00:00:00Z", "days_since_push": 1, "license": "MIT"},
        {"full_name": "c/d", "stars": 100, "topics": ["bci"], "description": "",
         "pushed_at": "2026-07-01T00:00:00Z", "days_since_push": 1, "license": "MIT"},
    ]
    _, counts = radar.enrich_v3(projects, seeds, snap, hist)
    byname = {p["full_name"]: p for p in projects}
    assert byname["a/b"]["falling"] is True and byname["a/b"]["stars_delta_7d"] == -5
    assert byname["c/d"]["falling"] is False
    assert counts["falling"] == 1


def test_feed_skips_future_first_seen():
    gen = datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc)
    xml = radar.build_feed([
        {"full_name": "ok/now", "first_seen": "2026-07-01T00:00:00+00:00",
         "html_url": "https://github.com/ok/now", "category": "Other"},
        {"full_name": "bad/future", "first_seen": "2027-01-01T00:00:00+00:00",
         "html_url": "https://github.com/bad/future", "category": "Other"},
    ], gen)
    assert "ok/now" in xml and "bad/future" not in xml


def test_validate_rejects_future_first_seen():
    payload = {"snapshot_at": "2026-07-02T00:00:00+00:00",
               "counts": {"total": 1},
               "projects": [{"full_name": "a/b", "html_url": "https://github.com/a/b",
                             "category": "Other",
                             "first_seen": "2027-01-01T00:00:00+00:00"}]}
    try:
        radar.validate(payload, 10)
        assert False, "future first_seen must be rejected"
    except AssertionError as e:
        assert "future first_seen" in str(e)


def test_load_first_seen_bootstrap_clamps_future(tmp_path, monkeypatch):
    snap_iso = "2026-07-02T00:00:00+00:00"
    radar_json = tmp_path / "radar.json"
    radar_json.write_text(json.dumps({"projects": [
        {"full_name": "a/b", "first_seen": "2027-09-09T00:00:00+00:00"},
        {"full_name": "c/d", "first_seen": "2026-01-01T00:00:00+00:00"},
    ]}), encoding="utf-8")
    monkeypatch.setattr(radar, "FIRST_SEEN", str(tmp_path / "first_seen.json"))
    monkeypatch.setattr(radar, "OUT", str(radar_json))
    got = radar.load_first_seen(snap_iso)
    assert got["a/b"] == snap_iso            # clamped
    assert got["c/d"] == "2026-01-01T00:00:00+00:00"


def test_write_last_run_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(radar, "LAST_RUN", str(tmp_path / "last_run.json"))
    radar.write_last_run(False, "topic_fail_ratio_exceeded", failed_topics=["eeg"])
    d = json.loads((tmp_path / "last_run.json").read_text())
    assert d["ok"] is False and d["reason"] == "topic_fail_ratio_exceeded"
    assert d["failed_topics"] == ["eeg"] and "at" in d
    radar.write_last_run(True)
    d = json.loads((tmp_path / "last_run.json").read_text())
    assert d["ok"] is True and d["reason"] == ""


def test_publish_norm_last_run_ignores_timestamp():
    import publish_data
    a = json.dumps({"ok": True, "reason": "", "at": "2026-07-02T00:00:00+00:00"})
    b = json.dumps({"ok": True, "reason": "", "at": "2026-07-02T06:00:00+00:00"})
    c = json.dumps({"ok": False, "reason": "x", "at": "2026-07-02T06:00:00+00:00"})
    assert publish_data.norm_last_run(a) == publish_data.norm_last_run(b)
    assert publish_data.norm_last_run(a) != publish_data.norm_last_run(c)


def test_report_movement_and_d7cell():
    import build_report
    hist = {"snapshots": [
        {"snapshot_at": "2026-06-26T00:00:00+00:00",
         "meta": {"total": 100, "total_stars": 1000, "active_30d": 50, "rising": 2},
         "stars": {"a/b": 10}},
        {"snapshot_at": "2026-07-02T00:00:00+00:00",
         "meta": {"total": 105, "total_stars": 1100, "active_30d": 55, "rising": 4},
         "stars": {"a/b": 14}},
    ]}
    mv = build_report.movement(hist)
    assert mv["delta"] == {"total": 5, "total_stars": 100, "active_30d": 5, "rising": 2}
    assert build_report.star_series(hist, "a/b") == [10, 14]
    assert "rise" in build_report._d7cell({"stars_delta_7d": 3})
    assert "fall" in build_report._d7cell({"stars_delta_7d": -3})
    assert build_report._d7cell({"stars_delta_7d": 0}) == "\u2014"


# ════════════════════════════ v5.0.0 additions ════════════════════════════

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "data", "seeds.json")

def test_https_only_funding():
    import enrich
    assert enrich._https_only("https://example.com/fund") == "https://example.com/fund"
    assert enrich._https_only("http://example.com") == ""
    assert enrich._https_only("httpevil-not-a-url") == ""
    assert enrich._https_only("https://") == ""
    assert enrich._https_only(None) == ""


def test_kw_hit_word_boundaries():
    import radar
    assert radar._kw_hit("api", "a public api for eeg")
    assert not radar._kw_hit("api", "rapid decoding")
    assert not radar._kw_hit("adc", "broadcast tools")
    assert radar._kw_hit("adc", "ads1299 adc driver")
    assert radar._kw_hit("real-time", "hard real-time kernel")


def test_seeds_min_stars_and_hyphen_keywords():
    seeds = json.load(open(SEEDS, encoding="utf-8"))
    assert seeds["min_stars"] == 2
    kw = seeds["neuro_keywords"]
    for h in ("brain-machine", "spike-sorting", "motor-imagery"):
        assert h in kw, f"hyphen variant missing: {h}"


def test_build_weekly_deltas_and_movers():
    import radar
    hist = {"snapshots": [
        {"snapshot_at": "2026-06-26T00:00:00+00:00",
         "meta": {"total": 10, "total_stars": 1000, "active_30d": 5, "rising": 2}},
        {"snapshot_at": "2026-07-03T00:00:00+00:00",
         "meta": {"total": 12, "total_stars": 1500, "active_30d": 7, "rising": 3}},
    ]}
    projects = [
        {"full_name": "a/up", "stars": 100, "stars_delta_7d": 9, "is_new": True},
        {"full_name": "a/down", "stars": 90, "stars_delta_7d": -3, "is_new": False},
        {"full_name": "a/flat", "stars": 10, "stars_delta_7d": 0, "is_new": False},
    ]
    w = radar.build_weekly(projects, hist, "2026-07-03T00:00:00+00:00")
    assert w["delta"] == {"total": 2, "total_stars": 500, "active_30d": 2, "rising": 1}
    assert [x["full_name"] for x in w["top_risers"]] == ["a/up"]
    assert [x["full_name"] for x in w["top_fallers"]] == ["a/down"]
    assert w["entrants"] == ["a/up"]


def test_build_weekly_needs_two_snapshots():
    import radar
    hist = {"snapshots": [{"snapshot_at": "2026-07-03T00:00:00+00:00", "meta": {"total": 1}}]}
    assert radar.build_weekly([], hist, "2026-07-03T00:00:00+00:00") is None


def test_owner_extra_parses_and_handles_429(monkeypatch):
    import enrich
    monkeypatch.setattr(enrich, "gh_get",
                        lambda url, tok: (200, {"type": "Organization", "followers": 7}, {}))
    info, limited = enrich.owner_extra("acme", "t")
    assert info == {"owner_type": "Organization", "followers": 7} and not limited
    monkeypatch.setattr(enrich, "gh_get", lambda url, tok: (429, None, {}))
    info, limited = enrich.owner_extra("acme", "t")
    assert info is None and limited
    monkeypatch.setattr(enrich, "gh_get", lambda url, tok: (404, None, {}))
    info, limited = enrich.owner_extra("ghost", "t")
    assert info == {} and not limited


def test_norm_weekly_ignores_generated_at():
    import publish_data as pub
    a = json.dumps({"generated_at": "T1", "delta": {"total": 1}})
    b = json.dumps({"generated_at": "T2", "delta": {"total": 1}})
    c = json.dumps({"generated_at": "T2", "delta": {"total": 9}})
    assert pub.norm_weekly(a) == pub.norm_weekly(b)
    assert pub.norm_weekly(a) != pub.norm_weekly(c)


def test_movement_prefers_weekly():
    import build_report as br
    weekly = {"span_from": "A", "span_to": "B",
              "delta": {"total": 3, "total_stars": 50, "active_30d": 1, "rising": 0},
              "now": {"total": 20, "total_stars": 900, "active_30d": 10, "rising": 2}}
    mv = br.movement({"snapshots": []}, weekly)
    assert mv["delta"]["total"] == 3 and mv["now"]["total_stars"] == 900
    assert br.movement({"snapshots": []}, {"bogus": 1}) == br._movement_from_history({"snapshots": []})


def test_history_meta_has_categories():
    import radar
    hist = {"version": 1, "snapshots": []}
    projects = [{"full_name": "a/x", "stars": 1, "category": "Decoding & ML"},
                {"full_name": "a/y", "stars": 1, "category": "Decoding & ML"},
                {"full_name": "a/z", "stars": 1, "category": "Privacy & Security"}]
    from datetime import datetime, timezone
    snap = datetime(2026, 7, 3, tzinfo=timezone.utc)
    out = radar.update_history(hist, projects, snap, "2026-07-03T00:00:00+00:00")
    cats = out["snapshots"][-1]["meta"]["categories"]
    assert cats == {"Decoding & ML": 2, "Privacy & Security": 1}


def test_schema_accepts_v5_fields():
    import jsonschema
    schema = json.load(open(os.path.join(ROOT, "data", "radar.schema.json"), encoding="utf-8"))
    doc = json.load(open(os.path.join(ROOT, "data", "radar.json"), encoding="utf-8"))
    if doc.get("projects"):
        doc["projects"][0].update({"falling": True, "community_active": True,
                                   "updated_at": "2026-07-01T00:00:00Z"})
    if doc.get("builders"):
        doc["builders"][0].update({"owner_type": "Organization", "followers": 3})
    jsonschema.validate(doc, schema)


def test_schema_rejects_bad_html_url():
    import jsonschema, copy
    schema = json.load(open(os.path.join(ROOT, "data", "radar.schema.json"), encoding="utf-8"))
    doc = copy.deepcopy(json.load(open(os.path.join(ROOT, "data", "radar.json"), encoding="utf-8")))
    assert doc.get("projects"), "need at least one live project"
    doc["projects"][0]["html_url"] = "https://github.com/"
    try:
        jsonschema.validate(doc, schema)
        raise AssertionError("schema accepted owner-less github URL")
    except jsonschema.ValidationError:
        pass


# ════════════════════════ v5.0.3: ecosystem ════════════════════════

def test_ecosystem_record_shape():
    import ecosystem
    data = {"full_name": "AxonOS-org/axonos-kernel",
            "html_url": "https://github.com/AxonOS-org/axonos-kernel",
            "description": "kernel", "topics": ["Rust", "BCI"], "stargazers_count": 0,
            "forks_count": 0, "language": "Rust", "pushed_at": "2026-07-01T00:00:00Z",
            "license": {"spdx_id": "MIT"}, "archived": False}
    r = ecosystem._repo_record(data)
    assert r["full_name"] == "AxonOS-org/axonos-kernel"
    assert r["stars"] == 0 and r["has_license"] is True
    assert r["topics"] == ["rust", "bci"]  # lowercased


def test_ecosystem_graph_shared_maintainers(monkeypatch):
    import ecosystem
    # two repos share contributor "denis", one has an extra "ava"
    sets = {
        "AxonOS-org/axonos-kernel": {"denis", "ava"},
        "AxonOS-org/axonos-protocol": {"denis"},
    }
    monkeypatch.setattr(ecosystem, "resolve_owner",
                        lambda o, t: {"login": o, "type": "Organization", "name": o})
    monkeypatch.setattr(ecosystem, "org_members", lambda o, t, limit=8: [])
    monkeypatch.setattr(ecosystem, "repo_contributor_logins",
                        lambda fn, t, limit=30, owner_logins=None: sets.get(fn, set()))
    recs = [{"full_name": "AxonOS-org/axonos-kernel"},
            {"full_name": "AxonOS-org/axonos-protocol"}]
    g = ecosystem.build_ecosystem_graph(recs, "tok")
    assert g["links"] and g["links"][0]["shared"] == ["denis"]
    assert g["links"][0]["weight"] == 1
    # denis spans 2 repos → key person
    assert any(kp["login"] == "denis" and kp["reach"] == 2 for kp in g["key_people"])


def test_contributor_logins_excludes_orgs_and_owner(monkeypatch):
    """The owning org account and any Organization-type contributor must be
    filtered out — an org committing to its own repos is not a human
    maintainer (this is what produced the AxonOS-BCI-links-everything bug)."""
    import ecosystem
    payload = [
        {"login": "AxonOS-BCI", "type": "Organization"},  # the owner org
        {"login": "some-bot[bot]", "type": "Bot"},
        {"login": "real-dev", "type": "User"},
    ]
    monkeypatch.setattr(ecosystem, "_get", lambda url, tok, accept=None: (200, payload))
    got = ecosystem.repo_contributor_logins(
        "AxonOS-BCI/axonos-community-radar", "tok",
        owner_logins={"AxonOS-BCI", "AxonOS-org"})
    assert got == {"real-dev"}, f"expected only the human, got {got}"


def test_ecosystem_anchors_flagged(monkeypatch):
    import ecosystem
    monkeypatch.setattr(ecosystem, "_get", lambda url, tok, accept=None: (
        200, {"full_name": "AxonOS-org/axonos-kernel", "stargazers_count": 0,
              "html_url": "https://github.com/AxonOS-org/axonos-kernel",
              "license": {"spdx_id": "MIT"}}))
    anchors = {"AxonOS-org/axonos-kernel": {"role": "Kernel", "note": "core"}}
    recs, meta = ecosystem.fetch_anchor_repos(anchors, "tok")
    assert meta["anchors_found"] == 1 and not meta["anchors_degraded"]
    assert recs[0]["ecosystem"] is True and recs[0]["ecosystem_role"] == "Kernel"


def test_ecosystem_missing_anchor_included_from_curated(monkeypatch):
    """When the API is unreachable, a curated anchor is still included (from its
    curated entry) so a flagship repo is never dropped from its own radar —
    but it is flagged as degraded and carries no fabricated live figures."""
    import ecosystem
    monkeypatch.setattr(ecosystem, "_get", lambda url, tok, accept=None: (404, None))
    recs, meta = ecosystem.fetch_anchor_repos({"o/gone": {"role": "x", "note": "n"}}, "tok")
    assert len(recs) == 1, "curated anchor must still be included"
    assert recs[0]["ecosystem"] is True and recs[0]["ecosystem_role"] == "x"
    assert recs[0]["stars"] == 0 and recs[0]["language"] == ""  # no fabricated figures
    assert meta["anchors_degraded"] == ["o/gone"]


def test_load_anchors_reads_curated():
    import radar
    a = radar.load_anchors()
    # curated.json ships with the AxonOS anchors
    assert any("axonos-kernel" in k.lower() for k in a), "kernel anchor missing"
    assert all(isinstance(v, dict) and "role" in v for v in a.values())
