#!/usr/bin/env python3
"""Pull the engine's published data into this repository. No PAT required.

The scored dataset is produced by the engine repository. Until now it was
*pushed* here with a cross-repo token (PUBLISH_PAT), which made the map's
liveness depend on one credential: when that token broke, every scheduled scan
still produced good data and none of it ever arrived — the map sat frozen for
days while both repositories looked busy.

This is the pull side of the same hop, and it needs no cross-repo credential at
all. It reads the engine's published files over plain HTTPS and commits them
here with the workflow's own GITHUB_TOKEN, which cannot expire and cannot be
mis-scoped. Commits go through the Contents API, so they are GitHub-signed
(Verified) and satisfy a signed-commit ruleset.

It is safe to run alongside the push path: whichever arrives first wins, and the
other sees identical content and skips. If the engine's files are not publicly
readable, this exits 0 with an explanation rather than failing — the push path
remains the fallback.

    ENGINE_REPO=owner/name GITHUB_TOKEN=… python3 scripts/sync_engine_data.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ENGINE_REPO = os.environ.get("ENGINE_REPO", "AxonOS-BCI/axonos-radar-core")
ENGINE_BRANCH = os.environ.get("ENGINE_BRANCH", "main")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
BRANCH = os.environ.get("SYNC_BRANCH", "main")

RAW = f"https://raw.githubusercontent.com/{ENGINE_REPO}/{ENGINE_BRANCH}/"
API = f"https://api.github.com/repos/{REPO}/contents/"

# The engine's *output* only. Never engine source — this repo is the showcase.
# report.html and the badge are rendered by the engine; ecosystem.json and the
# exports are built here at deploy time and must not be synced.
FILES = [
    ("data/radar.json", "radar: refresh ecosystem data [skip ci]"),
    ("data/history.json", "radar: update star history [skip ci]"),
    ("data/first_seen.json", "radar: update first_seen log [skip ci]"),
    ("data/status.json", "radar: update status [skip ci]"),
    ("data/last_run.json", "radar: record run outcome [skip ci]"),
    ("data/weekly.json", "radar: refresh weekly digest [skip ci]"),
    ("data/trajectory.json", "radar: extend trajectory series [skip ci]"),
    ("feed.xml", "radar: refresh feed [skip ci]"),
    ("report.html", "radar: refresh report page [skip ci]"),
]


def fetch_raw(path: str):
    try:
        req = urllib.request.Request(RAW + path, headers={"User-Agent": "radar-sync"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return None if e.code in (403, 404) else None
    except Exception:  # noqa: BLE001
        return None


def api(method: str, url: str, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "radar-sync",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {}
    except Exception as e:  # noqa: BLE001
        return 0, {"message": str(e)}


def generated_at(txt: str):
    try:
        v = json.loads(txt).get("generated_at")
        return datetime.fromisoformat(v.replace("Z", "+00:00")) if v else None
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    if not TOKEN or not REPO:
        print("missing GITHUB_TOKEN / GITHUB_REPOSITORY")
        return 1

    remote_radar = fetch_raw("data/radar.json")
    if remote_radar is None:
        print(f"· {ENGINE_REPO} does not serve data/radar.json publicly — nothing to pull.")
        print("  (Expected if the engine repository is private; the push path still applies.)")
        return 0

    r_at = generated_at(remote_radar)
    try:
        with open("data/radar.json", encoding="utf-8") as f:
            l_at = generated_at(f.read())
    except OSError:
        l_at = None

    if r_at is None:
        print("· engine radar.json has no generated_at — refusing to sync blind.")
        return 0
    if l_at is not None and r_at <= l_at:
        age = (datetime.now(timezone.utc) - l_at).total_seconds() / 3600
        print(f"· already current: engine {r_at.isoformat()} <= here {l_at.isoformat()} "
              f"(age {age:.1f}h) — nothing to do.")
        return 0

    print(f"· engine data is newer: {r_at.isoformat()} > "
          f"{l_at.isoformat() if l_at else '<none>'} — syncing.")

    committed = 0
    for path, message in FILES:
        body = fetch_raw(path)
        if body is None:
            print(f"  {path}: not published by the engine — skip")
            continue
        if path == "report.html":
            # The engine's report template points "Live map" / "Dashboard" /
            # "GitHub" at axonos-radar-core (the private engine's own repo,
            # which has no public Pages site) instead of this repo. A one-off
            # patch to the committed file gets silently overwritten by the
            # next sync, so the correction lives here instead — applied every
            # sync, on the fetched body, before it's ever compared or
            # committed. Once the engine's own template is fixed upstream,
            # this string simply won't be found and becomes a no-op; nothing
            # to remember to undo.
            fixed = body.replace(
                "axonos-bci.github.io/axonos-radar-core",
                "axonos-bci.github.io/axonos-community-radar",
            ).replace(
                "github.com/AxonOS-BCI/axonos-radar-core",
                "github.com/AxonOS-BCI/axonos-community-radar",
            )
            if fixed != body:
                print("  report.html: corrected axonos-radar-core links from the engine template")
            body = fixed
        code, cur = api("GET", f"{API}{path}?ref={BRANCH}")
        sha = cur.get("sha") if code == 200 else None
        if code == 200 and "content" in cur:
            if base64.b64decode(cur["content"]).decode("utf-8") == body:
                print(f"  {path}: identical — skip")
                continue
        payload = {"message": message, "branch": BRANCH,
                   "content": base64.b64encode(body.encode()).decode()}
        if sha:
            payload["sha"] = sha
        code, res = api("PUT", f"{API}{path}", payload)
        if code in (200, 201):
            v = ((res.get("commit") or {}).get("verification") or {}).get("verified")
            print(f"  {path}: committed {((res.get('commit') or {}).get('sha') or '')[:8]} (verified={v})")
            committed += 1
        else:
            print(f"::error::{path}: PUT failed HTTP {code}: {res.get('message')}")
            return 1

    print(f"✓ synced {committed} file(s) from {ENGINE_REPO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
