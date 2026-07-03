#!/usr/bin/env python3
"""Pipeline health monitor (audit fix: silent-failure detection).

Reads the PUBLISHED Pages copy of data/status.json and data/last_run.json —
i.e. what the world actually sees, not the checkout — and decides whether the
radar is healthy:

  * STALE   — status.generated_at older than MAX_AGE_HOURS (scans run every
              3 hours; 12h of silence means several consecutive failures).
  * FAILED  — the last recorded run ended with ok=false.

On a problem it opens (or updates) a single, marker-identified alert issue.
On recovery it closes that issue with a comment. One issue, no spam, and only
issues created by the Actions bot are ever touched (marker-collision defense).

Zero dependencies; exits 0 even when unhealthy — the ALERT is the signal, a
red health-run would just be noise on top.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "AxonOS-BCI/axonos-community-radar")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
OWNER, _, NAME = REPO.partition("/")
PAGES = f"https://{OWNER.lower()}.github.io/{NAME}/"
API = f"https://api.github.com/repos/{REPO}"
MARKER = "<!-- axonos-radar-health-alert f3a91c2e -->"
MAX_AGE_HOURS = 12
BOT_LOGINS = ("github-actions[bot]", "github-actions")

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "axonos-radar-health",
           "X-GitHub-Api-Version": "2022-11-28"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def fetch_json(url):
    # Cache-busting query defeats CDN caching in front of GitHub Pages —
    # without it a stale cached status.json can trigger false alerts.
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}_t={int(time.time())}"
    req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"],
                                               "Cache-Control": "no-cache, no-store, must-revalidate",
                                               "Pragma": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
            return json.loads(r.read(4 * 1024 * 1024).decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  fetch failed: {url}: {type(exc).__name__}")
        return None


def api_json(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {}
    except Exception as exc:  # noqa: BLE001
        print(f"  api failed: {type(exc).__name__}")
        return 0, {}


def find_alert():
    code, items = api_json("GET", "/issues?state=open&per_page=100&creator=github-actions%5Bbot%5D")
    if code != 200 or not isinstance(items, list):
        return None
    for it in items:
        author = ((it.get("user") or {}).get("login") or "")
        if author in BOT_LOGINS and MARKER in (it.get("body") or ""):
            return it
    return None


def diagnose():
    problems = []
    status = fetch_json(PAGES + "data/status.json")
    if status is None:
        problems.append("published data/status.json is unreachable")
    else:
        gen = status.get("generated_at") or ""
        try:
            dt = datetime.fromisoformat(gen)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            print(f"  status.generated_at = {gen} (age {age_h:.1f}h)")
            if age_h > MAX_AGE_HOURS:
                problems.append(f"data is STALE: last scan {age_h:.1f}h ago "
                                f"(threshold {MAX_AGE_HOURS}h; scans run every 3h)")
        except Exception:  # noqa: BLE001
            problems.append(f"status.generated_at unparsable: {gen!r}")
    last = fetch_json(PAGES + "data/last_run.json")
    if last is not None and last.get("ok") is False:
        problems.append(f"last pipeline run FAILED: {last.get('reason', 'unknown')}")
    return problems


def main():
    print(f"Health check for {PAGES}")
    problems = diagnose()
    alert = find_alert()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    if problems:
        body = "\n".join([
            MARKER,
            "## \u26a0\ufe0f Radar pipeline health alert", "",
            f"Automated check at `{now}` found:", "",
            *[f"- {p}" for p in problems], "",
            f"Runs: https://github.com/{REPO}/actions/workflows/radar.yml",
            "",
            "_This issue is maintained automatically by the health monitor: it updates "
            "in place while the problem persists and closes itself on recovery._",
        ])
        if alert:
            api_json("PATCH", f"/issues/{alert['number']}", {"body": body})
            print(f"UNHEALTHY — alert issue #{alert['number']} updated")
        else:
            code, created = api_json("POST", "/issues", {
                "title": "\u26a0\ufe0f Radar pipeline health alert",
                "body": body, "labels": ["pipeline-health"]})
            print(f"UNHEALTHY — alert issue created "
                  f"(#{created.get('number', '?')}, HTTP {code})")
        return 0

    print("HEALTHY")
    if alert:
        api_json("POST", f"/issues/{alert['number']}/comments",
                 {"body": f"\u2705 Recovered at `{now}` — data is fresh again. Closing."})
        api_json("PATCH", f"/issues/{alert['number']}", {"state": "closed"})
        print(f"recovery: alert issue #{alert['number']} closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
