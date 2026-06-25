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
    try:
        d = json.loads(txt)
        return json.dumps({"projects": d.get("projects"), "counts": d.get("counts")}, sort_keys=True)
    except Exception:  # noqa: BLE001
        return txt


def norm_feed(txt):
    return re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", txt)


NORMALIZERS = {"data/radar.json": norm_radar, "feed.xml": norm_feed}


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
    print(f"  {path}: FAILED HTTP {code}: {body.get('message')}")
    return False


def main():
    if not TOKEN or not REPO:
        print("Missing GITHUB_TOKEN / GITHUB_REPOSITORY")
        sys.exit(1)
    changed = put("data/radar.json", "radar: refresh ecosystem data [skip ci]")
    fs_changed = put("data/first_seen.json", "radar: update first_seen log [skip ci]")
    feed_changed = put("feed.xml", "radar: refresh feed [skip ci]")
    if not (changed or fs_changed or feed_changed):
        print("No meaningful change — nothing committed.")


if __name__ == "__main__":
    main()
