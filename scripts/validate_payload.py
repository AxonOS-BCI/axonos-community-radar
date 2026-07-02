#!/usr/bin/env python3
"""
Strict validator for the published data/radar.json payload.

Zero runtime dependencies (stdlib only). Used both as a CI gate and as an
importable function in tests. It is the executable half of the public data
contract documented in docs/DATA_MODEL.md.

Design: validate_payload(payload) returns a LIST of human-readable error
strings. An empty list means the payload is valid. The CLI exits non-zero if
any error is found.

It is forward-compatible: a v2 payload is validated against the v2 invariants;
a payload with "version": 3 must additionally carry evidence_tier and
inclusion_reason on every project (see the v3 spec).

Usage:
    python3 scripts/validate_payload.py                 # validates data/radar.json
    python3 scripts/validate_payload.py path/to.json
    python3 scripts/validate_payload.py --check         # same as default path
"""
from __future__ import annotations

import json
import urllib.parse
import sys

GITHUB_PREFIX = "https://github.com/"


def _is_safe_github_url(url, min_segments=2) -> bool:
    """Exact-host check: https://github.com/<...> with >= min_segments path parts
    (repos need 2: owner/repo). Blocks look-alike hosts like github.com.evil.com."""
    if not isinstance(url, str):
        return False
    try:
        q = urllib.parse.urlparse(url)
        segs = [s for s in q.path.split("/") if s]
        return q.scheme == "https" and q.netloc == "github.com" and len(segs) >= min_segments
    except Exception:
        return False
    try:
        q = urllib.parse.urlparse(url)
        return q.scheme == "https" and q.netloc == "github.com" and q.path.count("/") >= 2
    except Exception:
        return False
MAX_DESC = 240
DEFAULT_CAP = 2000
ALLOWED_TIERS = {
    "L3_EXPLICIT_BCI",
    "L2_NEURAL_SIGNAL",
    "L1_CONTEXT_PLUS_NEURO",
    "L0_WEAK_ADJACENT",
}


def _is_nonneg_int(v) -> bool:
    # bool is a subclass of int; reject it explicitly.
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def validate_payload(payload, cap: int = DEFAULT_CAP):
    """Return a list of error strings. Empty list == valid."""
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["payload is not a JSON object"]

    projects = payload.get("projects")
    if not isinstance(projects, list):
        return ["'projects' must be a list"]
    if len(projects) > cap:
        errors.append(f"too many projects: {len(projects)} > cap {cap}")

    counts = payload.get("counts")
    if isinstance(counts, dict):
        total = counts.get("total")
        if isinstance(total, int) and total < 0:
            errors.append("counts.total is negative")

    is_v3 = payload.get("version") == 3
    seen: set[str] = set()

    for i, r in enumerate(projects):
        tag = f"projects[{i}]"
        if not isinstance(r, dict):
            errors.append(f"{tag} is not an object")
            continue

        # full_name (required, unique, case-insensitive)
        fn = r.get("full_name")
        if not (isinstance(fn, str) and fn.strip()):
            errors.append(f"{tag} missing or empty full_name")
        else:
            key = fn.lower()
            if key in seen:
                errors.append(f"{tag} duplicate full_name {fn!r}")
            seen.add(key)

        # html_url MUST be a github.com https URL. This rejects javascript:,
        # http://, and look-alike hosts like https://github.com.evil.com/ .
        url = r.get("html_url")
        if not _is_safe_github_url(url):
            errors.append(f"{tag} html_url is not a https://github.com/ URL: {url!r}")

        # description length cap
        desc = r.get("description")
        if isinstance(desc, str) and len(desc) > MAX_DESC:
            errors.append(f"{tag} description exceeds {MAX_DESC} chars ({len(desc)})")

        # numeric fields
        for nf in ("stars", "forks"):
            if nf in r and r[nf] is not None and not _is_nonneg_int(r[nf]):
                errors.append(f"{tag} {nf} must be a non-negative integer, got {r[nf]!r}")

        # category required
        if not r.get("category"):
            errors.append(f"{tag} missing category")

        # array-typed fields, when present
        for af in ("topics", "matched_topics", "matched_keywords"):
            if af in r and not isinstance(r[af], list):
                errors.append(f"{tag} {af} must be an array")

        # star-velocity sanity (only when present): a delta cannot exceed
        # the current star count (impossible jump).
        stars = r.get("stars")
        if isinstance(stars, int):
            for df in ("stars_delta_7d", "stars_delta_30d"):
                d = r.get(df)
                if isinstance(d, int) and d > stars:
                    errors.append(f"{tag} {df} ({d}) exceeds current stars ({stars}) — impossible jump")

        # first_seen must not be in the future relative to the snapshot
        fs, snap = r.get("first_seen"), payload.get("snapshot_at")
        if isinstance(fs, str) and isinstance(snap, str) and fs > snap:
            errors.append(f"{tag} first_seen {fs!r} is after snapshot_at {snap!r}")

        # v3-only invariants
        if is_v3:
            tier = r.get("evidence_tier")
            if not tier:
                errors.append(f"{tag} missing evidence_tier (required at version 3)")
            elif tier not in ALLOWED_TIERS:
                errors.append(f"{tag} unknown evidence_tier {tier!r}")
            if not r.get("inclusion_reason"):
                errors.append(f"{tag} missing inclusion_reason (required at version 3)")

    # v3 consistency: counts and builders must agree with the data
    builders = payload.get("builders")
    if is_v3:
        n = len(projects)
        if isinstance(counts, dict):
            if counts.get("total") is not None and counts["total"] != n:
                errors.append(f"counts.total ({counts['total']}) != number of projects ({n})")
            rising_n = sum(1 for r in projects if isinstance(r, dict) and r.get("rising"))
            if counts.get("rising") is not None and counts["rising"] != rising_n:
                errors.append(f"counts.rising ({counts['rising']}) != projects with rising=true ({rising_n})")
            if isinstance(builders, list) and counts.get("builders") is not None and counts["builders"] != len(builders):
                errors.append(f"counts.builders ({counts['builders']}) != len(builders) ({len(builders)})")
        if isinstance(builders, list):
            seen_owner = set()
            for j, b in enumerate(builders):
                if not isinstance(b, dict):
                    errors.append(f"builders[{j}] is not an object"); continue
                ow = (b.get("owner") or "").lower()
                if ow in seen_owner:
                    errors.append(f"builders[{j}] duplicate owner {b.get('owner')!r}")
                seen_owner.add(ow)
                bp = b.get("projects")
                if isinstance(bp, list) and isinstance(b.get("project_count"), int) and b["project_count"] != len(bp):
                    errors.append(f"builders[{j}] project_count ({b['project_count']}) != len(projects) ({len(bp)})")
                bu = b.get("html_url") or ""
                if not _is_safe_github_url(bu, 1):
                    errors.append(f"builders[{j}] html_url is not a github.com URL: {bu!r}")

    return errors


def main(argv) -> int:
    path = "data/radar.json"
    args = [a for a in argv if a != "--check"]
    if args:
        path = args[0]
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except FileNotFoundError:
        print(f"validate_payload: file not found: {path}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"validate_payload: {path} is not valid JSON: {exc}")
        return 2

    errors = validate_payload(payload)
    if errors:
        print(f"validate_payload: {len(errors)} problem(s) in {path}:")
        for e in errors:
            print(f"  - {e}")
        return 1
    n = len(payload.get("projects", []))
    ver = payload.get("version", 2)
    print(f"validate_payload: {path} ok (version {ver}, {n} projects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
