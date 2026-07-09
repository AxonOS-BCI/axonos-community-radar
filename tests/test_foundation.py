# Tests for the v6 foundation signals in scripts/enrich.py.
# Network is monkeypatched; the contract under test is: checkable facts only,
# indeterminate evidence -> no field (never a fabricated zero).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import enrich  # noqa: E402


def test_parse_community_profile_maps_files_and_health():
    data = {"health_percentage": 71, "files": {
        "license": {"key": "mit"}, "readme": {"url": "x"},
        "contributing": None, "code_of_conduct": {"key": "cc"}}}
    got = enrich._parse_community_profile(data)
    assert got == {"license_file": True, "readme": True, "contributing": False,
                   "code_of_conduct": True, "health_pct": 71}


def test_parse_community_profile_rejects_garbage():
    assert enrich._parse_community_profile(None) is None
    assert enrich._parse_community_profile([1, 2]) is None
    out = enrich._parse_community_profile({"health_percentage": 999, "files": {}})
    assert out["health_pct"] is None


def test_assemble_counts_seven_keys():
    prof = {"license_file": True, "readme": True, "contributing": False,
            "code_of_conduct": False, "health_pct": 55}
    got = enrich._foundation_assemble(prof, citation=True, security=False, ci=True)
    assert got["count"] == 4
    assert set(enrich.FOUNDATION_KEYS) <= set(got)
    assert got["health_pct"] == 55


def _fake_gh(mapping):
    """Return a gh_get replacement keyed by URL suffix."""
    def fake(url, token, spacing=0.15):
        for suffix, resp in mapping.items():
            if url.endswith(suffix):
                return resp
        raise AssertionError(f"unexpected URL {url}")
    return fake


def test_foundation_happy_path(monkeypatch):
    mapping = {
        "/community/profile": (200, {"health_percentage": 80, "files": {
            "license": {}, "readme": {}, "contributing": {},
            "code_of_conduct": None}}, {}),
        "/contents/CITATION.cff": (200, {"name": "CITATION.cff"}, {}),
        "/contents/SECURITY.md": (404, None, {}),
        "/actions/workflows": (200, {"total_count": 3}, {}),
    }
    monkeypatch.setattr(enrich, "gh_get", _fake_gh(mapping))
    fnd, limited = enrich.foundation("acme/x", "tok")
    assert not limited
    assert fnd["citation"] is True and fnd["security_policy"] is False
    assert fnd["ci"] is True and fnd["count"] == 5


def test_foundation_rate_limited_anywhere(monkeypatch):
    mapping = {"/community/profile": (429, None, {})}
    monkeypatch.setattr(enrich, "gh_get", _fake_gh(mapping))
    fnd, limited = enrich.foundation("acme/x", "tok")
    assert fnd is None and limited is True


def test_foundation_indeterminate_evidence_skips_field(monkeypatch):
    # a 500 on SECURITY.md must NOT become "no security policy"
    mapping = {
        "/community/profile": (200, {"health_percentage": 10, "files": {}}, {}),
        "/contents/CITATION.cff": (404, None, {}),
        "/contents/SECURITY.md": (500, None, {}),
        "/actions/workflows": (200, {"total_count": 0}, {}),
    }
    monkeypatch.setattr(enrich, "gh_get", _fake_gh(mapping))
    fnd, limited = enrich.foundation("acme/x", "tok")
    assert fnd is None and limited is False


def test_foundation_profile_missing_skips_field(monkeypatch):
    mapping = {"/community/profile": (404, None, {})}
    monkeypatch.setattr(enrich, "gh_get", _fake_gh(mapping))
    fnd, limited = enrich.foundation("acme/x", "tok")
    assert fnd is None and limited is False
