#!/usr/bin/env python3
"""Measure the signature provenance of recent commits on the default branch.

Every automated commit in this repository is created through the GitHub
Contents API, and GitHub signs API-created commits when the caller is a GitHub
App identity — which is what a workflow's built-in ``GITHUB_TOKEN`` is. Commits
made with the same API but a *user* PAT are attributed to that user and left
unsigned. Both transports write the same files, so the difference is invisible
in the data and visible only here.

This script makes it visible: it reads the verification status GitHub reports
for the last N commits and prints who signed what. Report-only by default; pass
``--min-verified`` to turn it into a gate.

    python3 scripts/check_provenance.py --limit 30
    python3 scripts/check_provenance.py --limit 30 --min-verified 0.9

Needs a token only for the API's rate limit (any read token; in Actions the
default ``GITHUB_TOKEN`` is enough). Read-only: it never writes anything.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import urllib.error
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "AxonOS-BCI/axonos-community-radar")
TOKEN = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "")


def fetch_commits(limit: int, repo: str = REPO):
    """Return [(sha, author_name, verified, reason), ...] newest first."""
    url = f"https://api.github.com/repos/{repo}/commits?per_page={min(limit, 100)}"
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "radar-provenance",
               "X-GitHub-Api-Version": "2022-11-28"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    out = []
    for c in data:
        commit = c.get("commit") or {}
        ver = commit.get("verification") or {}
        author = (commit.get("author") or {}).get("name") or "?"
        login = ((c.get("author") or {}).get("login")) or author
        out.append((c.get("sha", "")[:8], login,
                    bool(ver.get("verified")), ver.get("reason") or ""))
    return out


def summarise(rows):
    by_author = collections.defaultdict(lambda: [0, 0])   # [verified, total]
    for _sha, who, verified, _reason in rows:
        by_author[who][1] += 1
        if verified:
            by_author[who][0] += 1
    return by_author


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--min-verified", type=float, default=None,
                    help="fail when the verified share falls below this (0..1)")
    ap.add_argument("--repo", default=REPO)
    a = ap.parse_args()

    try:
        rows = fetch_commits(a.limit, a.repo)
    except urllib.error.HTTPError as e:
        print(f"· provenance: GitHub API returned HTTP {e.code} — skipping "
              "(rate limit or no access; this check never blocks on API weather)")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"· provenance: could not reach the API ({str(e)[:80]}) — skipping")
        return 0

    if not rows:
        print("· provenance: no commits returned — skipping")
        return 0

    verified = sum(1 for r in rows if r[2])
    share = verified / len(rows)
    print(f"provenance: {verified}/{len(rows)} of the most recent commits on "
          f"{a.repo} are signed ({share:.0%})")
    for who, (v, t) in sorted(summarise(rows).items(), key=lambda kv: -kv[1][1]):
        mark = "✓" if v == t else ("·" if v else "✗")
        print(f"  {mark} {who:<26} {v}/{t} signed")
    if verified < len(rows):
        first_unsigned = next(r for r in rows if not r[2])
        print(f"  newest unsigned: {first_unsigned[0]} by {first_unsigned[1]}"
              f"{' (' + first_unsigned[3] + ')' if first_unsigned[3] else ''}")

    if a.min_verified is not None and share < a.min_verified:
        print(f"::error::signed share {share:.0%} is below the required "
              f"{a.min_verified:.0%}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
