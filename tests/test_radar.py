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
