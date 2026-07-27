"""The provenance readout: honest counts, and never a blocker on API weather."""
import os
import sys
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import check_provenance as P  # noqa: E402


def _rows(*spec):
    """spec: (author, verified) tuples -> rows shaped like fetch_commits'."""
    return [(f"sha{i:04d}", who, ver, "" if ver else "unsigned")
            for i, (who, ver) in enumerate(spec)]


def test_summary_counts_per_author():
    s = P.summarise(_rows(("github-actions[bot]", True), ("github-actions[bot]", True),
                          ("AxonOS-BCI", False)))
    assert s["github-actions[bot]"] == [2, 2]
    assert s["AxonOS-BCI"] == [0, 1]


def test_reports_share_and_passes_without_threshold(monkeypatch, capsys):
    monkeypatch.setattr(P, "fetch_commits",
                        lambda limit, repo: _rows(("bot", True), ("user", False)))
    monkeypatch.setattr(sys, "argv", ["p", "--limit", "2"])
    assert P.main() == 0
    out = capsys.readouterr().out
    assert "1/2" in out and "50%" in out


def test_threshold_fails_when_share_is_low(monkeypatch, capsys):
    monkeypatch.setattr(P, "fetch_commits",
                        lambda limit, repo: _rows(("bot", True), ("user", False),
                                                  ("user", False), ("user", False)))
    monkeypatch.setattr(sys, "argv", ["p", "--limit", "4", "--min-verified", "0.9"])
    assert P.main() == 1
    assert "below the required" in capsys.readouterr().out


def test_threshold_passes_when_share_is_high(monkeypatch):
    monkeypatch.setattr(P, "fetch_commits",
                        lambda limit, repo: _rows(("bot", True), ("bot", True)))
    monkeypatch.setattr(sys, "argv", ["p", "--limit", "2", "--min-verified", "1.0"])
    assert P.main() == 0


def test_names_the_newest_unsigned_commit(monkeypatch, capsys):
    monkeypatch.setattr(P, "fetch_commits",
                        lambda limit, repo: _rows(("user", False), ("bot", True)))
    monkeypatch.setattr(sys, "argv", ["p"])
    P.main()
    assert "newest unsigned: sha0000 by user" in capsys.readouterr().out


def test_api_failure_never_blocks(monkeypatch, capsys):
    def boom(limit, repo):
        raise urllib.error.HTTPError("u", 403, "rate limited", {}, None)
    monkeypatch.setattr(P, "fetch_commits", boom)
    monkeypatch.setattr(sys, "argv", ["p", "--min-verified", "1.0"])
    assert P.main() == 0                      # a rate limit is not a repo defect
    assert "skipping" in capsys.readouterr().out


def test_empty_result_is_not_a_failure(monkeypatch):
    monkeypatch.setattr(P, "fetch_commits", lambda limit, repo: [])
    monkeypatch.setattr(sys, "argv", ["p", "--min-verified", "1.0"])
    assert P.main() == 0
