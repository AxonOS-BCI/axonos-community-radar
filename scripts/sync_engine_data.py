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

#: Public relay: the engine uploads the payload as release assets on *this*
#: repository, and this workflow collects it from there.
#:
#: This exists to fix a provenance defect, not a transport one. The engine used
#: to commit here directly with a user PAT, and GitHub does not sign
#: API-created commits for user identities — so every automated commit on the
#: public map had been unsigned since 2026-07-17 while the same code path with
#: this workflow's own token produces signed ones. Uploading an asset creates no
#: commit, so the PAT can hand over the data without being the author of
#: anything, and the writer becomes the one identity GitHub will sign for.
#:
#: The relay is public by construction — assets on a public repository — so no
#: credential is needed to read it, and the ENGINE_READ_TOKEN that a private
#: engine would otherwise require is no longer needed at all.
RELAY_TAG = os.environ.get("RELAY_TAG", "data-latest")
RELAY = f"https://github.com/{REPO}/releases/download/{RELAY_TAG}/"
API = f"https://api.github.com/repos/{REPO}/contents/"

# The engine's *output* only. Never engine source — this repo is the showcase.
# report.html and the badge are rendered by the engine; ecosystem.json and the
# exports are built here at deploy time and must not be synced. report.html
# is handled separately by sync_report_html() below, not in this list — see
# that function's docstring for why.
FILES = [
    ("data/radar.json", "radar: refresh ecosystem data [skip ci]"),
    ("data/history.json", "radar: update star history [skip ci]"),
    ("data/first_seen.json", "radar: update first_seen log [skip ci]"),
    ("data/status.json", "radar: update status [skip ci]"),
    ("data/last_run.json", "radar: record run outcome [skip ci]"),
    ("data/weekly.json", "radar: refresh weekly digest [skip ci]"),
    ("data/badge-ecosystem.json", "radar: refresh ecosystem badge [skip ci]"),
    ("data/trajectory.json", "radar: extend trajectory series [skip ci]"),
    ("feed.xml", "radar: refresh feed [skip ci]"),
]


ENGINE_READ_TOKEN = os.environ.get("ENGINE_READ_TOKEN") or ""

# Why the last fetch returned nothing — "absent" (404/403: private engine or
# unpublished file) reads very differently from "transient" (5xx, timeout):
# the first is a configuration state, the second just means try again in 3h.
# Conflating them once produced the misleading "engine is private" message
# during a plain upstream hiccup.
FETCH_ERR = {"kind": None}


def fetch_raw(path: str):
    """Read one engine file. Public raw first; if the engine is private and an
    ENGINE_READ_TOKEN is provided (fine-grained, engine repo only, Contents:
    Read), fall back to the authenticated Contents API. Read-only by
    construction: this token cannot write anywhere even if leaked."""
    FETCH_ERR["kind"] = None
    # The relay first: it is public, needs no credential, and is the path whose
    # commits are signed. The engine's raw URLs remain as a fallback for the
    # case where the engine is public and the relay has not run yet.
    for base, label in ((RELAY, "relay"), (RAW, "raw")):
        url = base + (path.replace("/", "__") if label == "relay" else path)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "radar-sync"})
            with urllib.request.urlopen(req, timeout=30) as r:
                FETCH_ERR["kind"] = None
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            FETCH_ERR["kind"] = "absent" if e.code in (403, 404) else "transient"
        except Exception:  # noqa: BLE001
            FETCH_ERR["kind"] = "transient"
    if not ENGINE_READ_TOKEN:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{ENGINE_REPO}/contents/{path}?ref={ENGINE_BRANCH}",
            headers={"User-Agent": "radar-sync",
                     "Accept": "application/vnd.github.raw+json",
                     "Authorization": f"Bearer {ENGINE_READ_TOKEN}",
                     "X-GitHub-Api-Version": "2022-11-28"})
        with urllib.request.urlopen(req, timeout=30) as r:
            FETCH_ERR["kind"] = None
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        FETCH_ERR["kind"] = "absent" if e.code in (403, 404) else "transient"
    except Exception:  # noqa: BLE001
        FETCH_ERR["kind"] = "transient"
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


def sync_report_html() -> None:
    """Fetch, correct, and (if needed) commit report.html — unconditionally,
    every run, independent of whether data/radar.json itself is newer.

    v12.0.4 first tried this correction inside the main FILES loop, gated
    behind the same "is the engine's data newer than what we have" check as
    everything else. That never actually fired in production: the push path
    (the engine's own direct commit, with no correction) routinely lands
    data/radar.json and the uncorrected report.html in the same scan, so by
    the time this script runs, r_at <= l_at is already true and main()
    returns before the FILES loop is ever reached. The correction was
    correct; it was simply unreachable. This function has no such gate — it
    runs first, every invocation, so within one sync interval (worst case
    ~20 minutes, per pages.yml's own comment on the offset between the
    engine's scan and this script's schedule) any wrong link the push path
    just committed gets corrected, rather than staying wrong indefinitely.
    """
    body = fetch_raw("report.html")
    if body is None:
        print("· report.html: not published by the engine — skip")
        return
    fixed = body.replace(
        "axonos-bci.github.io/axonos-radar-core",
        "axonos-bci.github.io/axonos-community-radar",
    ).replace(
        "github.com/AxonOS-BCI/axonos-radar-core",
        "github.com/AxonOS-BCI/axonos-community-radar",
    )
    if fixed != body:
        print("· report.html: corrected axonos-radar-core links from the engine template")
    code, cur = api("GET", f"{API}report.html?ref={BRANCH}")
    sha = cur.get("sha") if code == 200 else None
    if code == 200 and "content" in cur:
        if base64.b64decode(cur["content"]).decode("utf-8") == fixed:
            print("· report.html: identical — skip")
            return
    payload = {"message": "radar: refresh report page [skip ci]", "branch": BRANCH,
               "content": base64.b64encode(fixed.encode()).decode()}
    if sha:
        payload["sha"] = sha
    code, res = api("PUT", f"{API}report.html", payload)
    if code in (200, 201):
        v = ((res.get("commit") or {}).get("verification") or {}).get("verified")
        print(f"· report.html: committed (verified={v})")
    else:
        print(f"· report.html: PUT failed ({code})")


MAX_FEED_BYTES = 5 * 1024 * 1024


def feed_is_well_formed(body: str):
    """Well-formedness check for engine-served XML, hardened at the input.

    Returns (ok, reason). The classic attacks against a stdlib XML parser all
    arrive through the document prologue: billion-laughs and quadratic-blowup
    need an internal DTD with entity declarations, and XXE needs an external
    one. Rather than trusting a parser to survive them, this refuses any
    document carrying a DOCTYPE or ENTITY declaration outright — a syndication
    feed has no legitimate reason to declare either — and caps the size before
    parsing. What reaches the parser therefore cannot contain the constructs
    the parser is warned about. (External entity expansion is off by default
    in CPython's expat bindings since 3.7.1; this guard closes the internal
    ones too.) stdlib only, per this repository's dependency posture.
    """
    if len(body.encode("utf-8", "ignore")) > MAX_FEED_BYTES:
        return False, f"larger than {MAX_FEED_BYTES // 1024 // 1024} MB"
    head = body[:4096].upper()
    if "<!DOCTYPE" in head or "<!ENTITY" in body.upper():
        return False, "carries a DTD or entity declaration (refused before parsing)"
    try:
        # The two suppressions below are earned by the guard above, not
        # asserted: nothing reaching this parser can carry a DTD or an entity
        # declaration, and its size is capped.
        import xml.dom.minidom as _m  # nosec B408
        _m.parseString(body)  # nosec B318
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:120]
    return True, ""


def main() -> int:
    if not TOKEN or not REPO:
        print("missing GITHUB_TOKEN / GITHUB_REPOSITORY")
        return 1

    sync_report_html()

    remote_radar = fetch_raw("data/radar.json")
    if remote_radar is None:
        if FETCH_ERR["kind"] == "transient":
            print(f"· {ENGINE_REPO}: transient upstream error — leaving data as-is; "
                  "the next tick retries.")
        else:
            print(f"· {ENGINE_REPO} is not readable (private without ENGINE_READ_TOKEN, "
                  "or the file is unpublished) — nothing to pull.")
            print("  The push path still applies. To restore the pull path for a private "
                  "engine, add the ENGINE_READ_TOKEN secret: a fine-grained PAT on the "
                  "engine repo only, Contents: Read.")
        return 0

    # Parse FIRST, loudly. Garbage from the engine is an incident, not a
    # quiet no-op: a red run here is the only signal anyone will get, because
    # every commit below carries [skip ci].
    try:
        payload = json.loads(remote_radar)
    except ValueError as e:
        print(f"::error::engine radar.json is not JSON: {e}")
        return 1
    try:
        r_at = datetime.fromisoformat(str(payload.get("generated_at")).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        print("::error::engine radar.json carries no parsable generated_at — contract broken.")
        return 1
    try:
        with open("data/radar.json", encoding="utf-8") as f:
            l_at = generated_at(f.read())
    except OSError:
        l_at = None
    if l_at is not None and r_at <= l_at:
        age = (datetime.now(timezone.utc) - l_at).total_seconds() / 3600
        print(f"· already current: engine {r_at.isoformat()} <= here {l_at.isoformat()} "
              f"(age {age:.1f}h) — nothing to do.")
        return 0

    print(f"· engine data is newer: {r_at.isoformat()} > "
          f"{l_at.isoformat() if l_at else '<none>'} — syncing.")

    # ── Contract gate. This script is a WRITE PATH into main: whatever it
    # commits deploys to the public site on the next pages tick, and its
    # commits carry [skip ci], so no later check ever looks at them. That
    # combination means validation must happen HERE, before the first PUT —
    # an invalid payload is refused wholesale (no partial syncs), the run
    # goes red with the reasons, the previous data stays live, and the
    # health monitor flags staleness if the engine keeps misbehaving. ──
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from validate_payload import validate_payload  # noqa: E402
    errs = validate_payload(payload)
    if errs:
        print(f"::error::engine payload rejected by the contract gate "
              f"({len(errs)} issue(s)) — nothing committed:")
        for e in errs[:20]:
            print(f"  - {e}")
        return 1
    try:
        import jsonschema
        with open("data/radar.schema.json", encoding="utf-8") as fh:
            jsonschema.validate(payload, json.load(fh))
    except ImportError:
        print("· jsonschema unavailable — invariant gate above still enforced")
    except Exception as e:  # noqa: BLE001
        print(f"::error::engine payload fails the published schema: {str(e)[:200]}")
        return 1
    print(f"· contract gate passed: {len(payload.get('projects') or [])} projects, "
          "invariants + schema clean")

    committed = 0
    for path, message in FILES:
        body = fetch_raw(path)
        if body is None:
            print(f"  {path}: not published by the engine — skip")
            continue
        if path.endswith(".xml"):
            ok, why = feed_is_well_formed(body)
            if not ok:
                print(f"::warning::{path}: engine served unusable XML ({why}) "
                      "— keeping the previous copy this round")
                continue
        elif path.endswith(".json"):
            try:
                json.loads(body)
            except ValueError:
                print(f"::warning::{path}: engine served malformed JSON — "
                      "keeping the previous copy this round")
                continue
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
