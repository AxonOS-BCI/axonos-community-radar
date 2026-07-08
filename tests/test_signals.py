"""Tests for Ecosystem Health Signals — bounds, honesty, and determinism.

The guarantees these lock in: every sub-score stays in 0..100, dimensions with
no input are omitted (not silently zeroed), the overall is a weighted mean of
only-measured dimensions, badges are strictly derived from real fields, and the
same repo always scores the same (no hidden state, no per-name special-casing).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import signals  # noqa: E402


def _repo(**kw):
    base = {"full_name": "acme/widget", "stars": 100, "days_since_push": 10,
            "license": "MIT", "has_license": True, "commits_52w": 200,
            "contributors": 6, "releases_count": 5, "total_downloads": 1000,
            "description": "a real description", "homepage": "https://acme.dev"}
    base.update(kw)
    return base


def test_overall_in_range_and_dimensions_bounded():
    s = signals.score_project(_repo())
    assert 0 <= s["overall"] <= 100
    for dim in ("license", "maintenance", "momentum", "adoption", "team", "docs"):
        assert 0 <= s[dim] <= 100


def test_osi_license_full_marks_no_license_zero():
    assert signals.score_project(_repo(license="Apache-2.0"))["license"] == 100
    assert signals.score_project(_repo(license="MIT"))["license"] == 100
    z = signals.score_project(_repo(license=None, has_license=False))
    assert z["license"] == 0
    # a real but unclassifiable licence lands between the two, never at 0 or 100
    mid = signals.score_project(_repo(license="NOASSERTION", has_license=True))
    assert mid["license"] == 40


def test_search_only_repo_omits_momentum_and_team():
    # no commits_52w and no contributors -> both dimensions dropped, basis flagged
    r = _repo()
    del r["commits_52w"]
    del r["contributors"]
    s = signals.score_project(r)
    assert "momentum" not in s
    assert "team" not in s
    assert s["basis"] == "search-only"
    assert 0 <= s["overall"] <= 100   # still scored on the remaining dimensions


def test_partial_basis_when_one_signal_present():
    r = _repo()
    del r["contributors"]
    s = signals.score_project(r)
    assert s["basis"] == "partial"
    assert "momentum" in s and "team" not in s


def test_activity_pending_suppresses_momentum():
    s = signals.score_project(_repo(activity_pending=True))
    assert "momentum" not in s


def test_maintenance_bands_are_monotonic():
    fresh = signals.score_project(_repo(days_since_push=3))["maintenance"]
    month = signals.score_project(_repo(days_since_push=20))["maintenance"]
    stale = signals.score_project(_repo(days_since_push=400))["maintenance"]
    assert fresh > month > stale


def test_team_rewards_more_contributors():
    solo = signals.score_project(_repo(contributors=1))["team"]
    small = signals.score_project(_repo(contributors=6))["team"]
    big = signals.score_project(_repo(contributors=40))["team"]
    assert solo < small < big == 100


def test_zero_contributors_treated_as_unknown_not_zero():
    s = signals.score_project(_repo(contributors=0))
    assert "team" not in s   # 0 is "unknown split", not a measured 0


def test_badges_are_derived_only_from_real_fields():
    s = signals.score_project(_repo(license="MIT", days_since_push=5,
                                    releases_count=3, contributors=5))
    assert set(s["badges"]) == {"osi-licensed", "actively-maintained",
                                "has-releases", "multi-contributor"}
    bare = signals.score_project(_repo(license=None, has_license=False,
                                       days_since_push=400, releases_count=0,
                                       contributors=1))
    assert bare["badges"] == []


def test_score_is_deterministic():
    r = _repo()
    assert signals.score_project(dict(r)) == signals.score_project(dict(r))


def test_no_per_name_special_casing():
    # two identical repos with different names must score identically —
    # proves AxonOS (or anyone) is never boosted by identity.
    a = signals.score_project(_repo(full_name="AxonOS-org/axonos-kernel"))
    b = signals.score_project(_repo(full_name="someone/unrelated"))
    assert a["overall"] == b["overall"]


def test_band_thresholds():
    assert signals.band(90) == "strong"
    assert signals.band(70) == "solid"
    assert signals.band(45) == "developing"
    assert signals.band(10) == "early"


def test_annotate_attaches_signals_in_place():
    ps = [_repo(), _repo(full_name="b/c")]
    signals.annotate(ps)
    assert all(isinstance(p["signals"], dict) and "overall" in p["signals"] for p in ps)
