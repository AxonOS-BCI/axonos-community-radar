"""Guards the living-digest lookup against spawning duplicate issues.

The digest keeps ONE issue and edits it in place. The dangerous path is the
lookup: if it cannot enumerate open issues and answers "nothing found", the
caller creates a second living issue that then updates forever alongside the
first. This happened in production — a 403 (rate-limited / under-scoped token)
was treated as "no issue exists".

Contract under test:
  * listing failed, for ANY reason      -> "RETRY"  (caller must skip)
  * listing succeeded, no marker        -> None     (safe to create)
  * listing succeeded, marker present   -> that issue (edit in place)
  * several markers (an old duplicate)  -> the OLDEST, so they converge
"""
import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
os.environ.setdefault("GITHUB_REPOSITORY", "o/r")
os.environ.setdefault("GITHUB_TOKEN", "x")

import publish_stats_issue as psi  # noqa: E402

BOT = {"login": "github-actions[bot]"}


def _issue(number, marked=True, author=BOT):
    return {"number": number, "user": author,
            "body": (psi.MARKER + "\nbody") if marked else "unrelated"}


def _stub_api(monkeypatch, result):
    """Point the module's HTTP layer at a canned result or exception."""
    def fake(method, path, payload=None):
        if callable(result):
            return result(method, path)
        return result
    monkeypatch.setattr(psi, "_api", fake)


@pytest.mark.parametrize("exc", [
    urllib.error.HTTPError("u", 403, "rate limited", {}, None),   # the real-world case
    urllib.error.HTTPError("u", 401, "bad creds", {}, None),
    urllib.error.HTTPError("u", 502, "bad gateway", {}, None),
    urllib.error.URLError("network down"),
    ValueError("malformed json"),
])
def test_failed_listing_never_creates(monkeypatch, exc):
    """Any lookup failure must say RETRY — never 'nothing found'."""
    def boom(method, path):
        raise exc
    _stub_api(monkeypatch, boom)
    assert psi.find_issue() == "RETRY"


def test_non_list_response_is_retry(monkeypatch):
    """An error object where a list was expected is not 'nothing found'."""
    _stub_api(monkeypatch, {"message": "API rate limit exceeded"})
    assert psi.find_issue() == "RETRY"


def test_clean_listing_allows_create(monkeypatch):
    """A successful listing with no marker is the one safe path to create."""
    _stub_api(monkeypatch, [_issue(1, marked=False)])
    assert psi.find_issue() is None


def test_marker_is_adopted(monkeypatch):
    _stub_api(monkeypatch, [_issue(1, marked=False), _issue(7)])
    got = psi.find_issue()
    assert got and got["number"] == 7


def test_duplicates_converge_on_oldest(monkeypatch):
    """If a duplicate already exists, keep editing the oldest one."""
    _stub_api(monkeypatch, [_issue(9), _issue(2), _issue(5)])
    got = psi.find_issue()
    assert got and got["number"] == 2


def test_foreign_marker_is_ignored(monkeypatch):
    """Only the Actions bot is trusted — a user can't hijack the digest."""
    _stub_api(monkeypatch, [_issue(4, author={"login": "someone-else"})])
    assert psi.find_issue() is None


def test_marker_beyond_first_page_is_found(monkeypatch):
    """A marker past 100 open issues must not be missed (that means duplicate)."""
    page1 = [_issue(n, marked=False) for n in range(100, 200)]
    page2 = [_issue(3)]

    def paged(method, path):
        return page2 if "page=2" in path else page1

    _stub_api(monkeypatch, paged)
    got = psi.find_issue()
    assert got and got["number"] == 3
