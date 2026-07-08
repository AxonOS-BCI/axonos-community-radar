#!/usr/bin/env python3
"""
Commit refreshed radar data through the GitHub Contents API.

Why: commits created via the Contents API with the Actions token are signed by
GitHub (web-flow) and show as **Verified**, unlike a plain `git commit` from the
runner which is unsigned. This keeps the repository's commit history green.

Only commits a file when its meaningful content changed (timestamp-only diffs in
radar.json / feed.xml are ignored), so the history is not spammed.
"""
import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error

REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
BRANCH = os.environ.get("GITHUB_REF_NAME") or "main"
API = f"https://api.github.com/repos/{REPO}/contents/"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": "radar-publish",
    "X-GitHub-Api-Version": "2022-11-28",
}


def api(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {}


def get_remote(path):
    code, body = api("GET", f"{API}{path}?ref={BRANCH}")
    if code == 200 and "content" in body:
        return body["sha"], base64.b64decode(body["content"]).decode("utf-8")
    return None, None


def norm_radar(txt):
    """Meaningful-change detector: everything except run timestamps. Projects
    carry the enriched fields inside them, and builders are included too, so a
    change in ONLY enriched/builder data still publishes (audit fix)."""
    try:
        d = json.loads(txt)
        return json.dumps({"projects": d.get("projects"), "counts": d.get("counts"),
                           "builders": d.get("builders")}, sort_keys=True)
    except Exception:  # noqa: BLE001
        return txt


def norm_last_run(txt):
    try:
        d = json.loads(txt)
        d.pop("at", None)   # timestamp-only diffs do not spam the history
        return json.dumps(d, sort_keys=True)
    except Exception:  # noqa: BLE001
        return txt


def norm_feed(txt):
    return re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", txt)


def norm_json(txt):
    try:
        return json.dumps(json.loads(txt), sort_keys=True)
    except Exception:  # noqa: BLE001
        return txt


def norm_weekly(txt):
    try:
        d = json.loads(txt)
        d.pop("generated_at", None)
        return json.dumps(d, sort_keys=True)
    except Exception:  # noqa: BLE001
        return txt


NORMALIZERS = {"data/radar.json": norm_radar, "data/history.json": norm_json,
               "feed.xml": norm_feed, "data/last_run.json": norm_last_run,
               "data/weekly.json": norm_weekly}


# Files whose PUT failure must fail the whole step. A missing radar.json /
# history / feed / report commit is a real publish failure, not a no-op; the
# old code printed the error but still exited 0, so a broken token or API
# outage looked green. These are tracked and surfaced as a non-zero exit.
FAILURES: list[str] = []


def put(path, message):
    with open(path, encoding="utf-8") as f:
        local = f.read()
    sha, remote = get_remote(path)
    if remote is not None:
        norm = NORMALIZERS.get(path, lambda x: x)
        if norm(local) == norm(remote):
            print(f"  {path}: unchanged — skip")
            return False
    payload = {"message": message, "content": base64.b64encode(local.encode()).decode(), "branch": BRANCH}
    if sha:
        payload["sha"] = sha
    code, body = api("PUT", f"{API}{path}", payload)
    if code in (200, 201):
        v = (body.get("commit") or {}).get("verification") or {}
        print(f"  {path}: committed {(body.get('commit') or {}).get('sha','')[:8]} (verified={v.get('verified')})")
        return True
    msg = f"{path}: FAILED HTTP {code}: {body.get('message')}"
    print(f"  {msg}")
    FAILURES.append(msg)
    return False


def main():
    if not TOKEN or not REPO:
        print("Missing GITHUB_TOKEN / GITHUB_REPOSITORY")
        sys.exit(1)
    changed = put("data/radar.json", "radar: refresh ecosystem data [skip ci]")
    hist_changed = put("data/history.json", "radar: update star history [skip ci]")
    fs_changed = put("data/first_seen.json", "radar: update first_seen log [skip ci]")
    feed_changed = put("feed.xml", "radar: refresh feed [skip ci]")
    report_changed = put("report.html", "radar: refresh report page [skip ci]")
    status_changed = put("data/status.json", "radar: update status [skip ci]")
    if os.path.exists("data/last_run.json"):
        put("data/last_run.json", "radar: record run outcome [skip ci]")
    if os.path.exists("data/weekly.json"):
        put("data/weekly.json", "radar: refresh weekly digest [skip ci]")
    if not (changed or hist_changed or fs_changed or feed_changed or report_changed or status_changed):
        print("No meaningful change — nothing committed.")
    if FAILURES:
        print(f"\n{len(FAILURES)} file(s) failed to publish — failing the step:")
        for m in FAILURES:
            print(f"  - {m}")
        sys.exit(1)


if __name__ == "__main__":
    main()
