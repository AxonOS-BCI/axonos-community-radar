#!/usr/bin/env python3
"""Enrichment phase for the radar (v4).

For each discovered repository this fetches the deeper, *real* signals the
search API does not return: team size (contributors), adoption (release
download totals + release cadence), maintenance activity (52-week commit
histogram), community funding channels (FUNDING.yml), and a few repo extras
(true watchers, size, open issues, homepage, archived state).

Everything here is a genuine public GitHub signal. Nothing is invented. Data
that GitHub simply does not have — money raised, legal domicile — is NOT
guessed here; it comes only from a hand-curated, source-cited overrides file
(data/curated.json), merged separately in radar.py and clearly marked.

The phase is rate-limit aware and never fails the pipeline: any repo that
errors is left with enriched=False and the scan continues.
"""
from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
UA = "AxonOS-Community-Radar-enrich"


def _headers(token):
    h = {"Accept": "application/vnd.github+json", "User-Agent": UA,
         "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def gh_get(url, token, spacing=0.15):
    """GET returning (status, parsed, headers). Handles arrays, 202, 404, 403."""
    req = urllib.request.Request(url, headers=_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
            body = r.read(8 * 1024 * 1024)
            time.sleep(spacing)
            txt = body.decode("utf-8") if body else ""
            return r.status, (json.loads(txt) if txt else None), dict(r.headers)
    except urllib.error.HTTPError as e:
        hdrs = dict(e.headers or {})
        if e.code in (403, 429) and hdrs.get("X-RateLimit-Remaining") == "0":
            return 429, None, hdrs
        return e.code, None, hdrs
    except (urllib.error.URLError, TimeoutError, ValueError):
        return 0, None, {}


def rate_remaining(token):
    code, data, _ = gh_get(f"{API}/rate_limit", token, spacing=0)
    if code == 200 and data:
        return int(((data.get("resources") or {}).get("core") or {}).get("remaining", 0))
    return None


def _last_page(headers):
    """Parse the last page number from a Link header (used to count contributors)."""
    link = headers.get("Link") or headers.get("link") or ""
    for part in link.split(","):
        if 'rel="last"' in part:
            seg = part[part.find("<") + 1:part.find(">")]
            q = urllib.parse.urlparse(seg).query
            pg = urllib.parse.parse_qs(q).get("page", ["1"])[0]
            try:
                return int(pg)
            except ValueError:
                return None
    return None


def contributors_count(fn, token):
    code, data, headers = gh_get(f"{API}/repos/{fn}/contributors?per_page=1&anon=true", token)
    if code == 429:
        return None, True
    if code != 200:
        return None, False
    last = _last_page(headers)
    if last is not None:
        return last, False
    return (len(data) if isinstance(data, list) else 0), False


def releases_info(fn, token):
    code, data, _ = gh_get(f"{API}/repos/{fn}/releases?per_page=100", token)
    if code == 429:
        return None, True
    if code != 200 or not isinstance(data, list):
        return {"releases_count": 0, "total_downloads": 0,
                "latest_release_tag": "", "latest_release_at": ""}, False
    downloads = 0
    for rel in data:
        for asset in rel.get("assets") or []:
            downloads += int(asset.get("download_count") or 0)
    latest = data[0] if data else {}
    return {"releases_count": len(data), "total_downloads": downloads,
            "latest_release_tag": latest.get("tag_name") or "",
            "latest_release_at": latest.get("published_at") or ""}, False


def commit_activity(fn, token):
    """52 weekly commit totals. Returns (total_52w, last_12_weeks list)."""
    code, data, _ = gh_get(f"{API}/repos/{fn}/stats/commit_activity", token)
    if code == 429:
        return None, None, True
    if code != 200 or not isinstance(data, list) or not data:
        return 0, [], False  # 202 = GitHub still computing; treat as no data
    weeks = [int(w.get("total") or 0) for w in data]
    return sum(weeks), weeks[-12:], False


_FUND_KEYS = ("github", "patreon", "open_collective", "ko_fi", "tidelift",
              "community_bridge", "liberapay", "issuehunt", "lfx_membership",
              "polar", "buy_me_a_coffee", "thanks_dev", "custom")


def funding(fn, token):
    for path in (".github/FUNDING.yml", "FUNDING.yml", "docs/FUNDING.yml"):
        code, data, _ = gh_get(f"{API}/repos/{fn}/contents/{path}", token)
        if code == 429:
            return None, None, True
        if code == 200 and data and data.get("content"):
            try:
                text = base64.b64decode(data["content"]).decode("utf-8", "ignore")
            except Exception:  # noqa: BLE001
                return [], "", False
            platforms, primary = [], ""
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("#") or ":" not in line:
                    continue
                key = line.split(":", 1)[0].strip().lower()
                val = line.split(":", 1)[1].strip().strip("[]\"' ")
                if key in _FUND_KEYS and key not in platforms:
                    platforms.append(key)
                    if not primary and val:
                        primary = _funding_url(key, val)
            return platforms, primary, False
    return [], "", False


def _funding_url(key, val):
    val = val.split(",")[0].strip().strip("\"'[] ")
    return {
        "github": f"https://github.com/sponsors/{val}",
        "patreon": f"https://patreon.com/{val}",
        "open_collective": f"https://opencollective.com/{val}",
        "ko_fi": f"https://ko-fi.com/{val}",
        "liberapay": f"https://liberapay.com/{val}",
        "buy_me_a_coffee": f"https://buymeacoffee.com/{val}",
        "polar": f"https://polar.sh/{val}",
    }.get(key, val if val.startswith("http") else "")


def repo_extra(fn, token):
    code, data, _ = gh_get(f"{API}/repos/{fn}", token)
    if code == 429:
        return None, True
    if code != 200 or not isinstance(data, dict):
        return {}, False
    return {
        "watchers": int(data.get("subscribers_count") or 0),
        "size_kb": int(data.get("size") or 0),
        "open_issues": int(data.get("open_issues_count") or 0),
        "homepage": (data.get("homepage") or "").strip(),
        "archived": bool(data.get("archived")),
        "disabled": bool(data.get("disabled")),
    }, False


def enrich_repos(projects, token, max_enrich=200, keep_headroom=200, log=print):
    """Enrich projects in place (highest-scoring first). Returns a stats dict.

    Stops early if the remaining rate-limit budget approaches keep_headroom, so
    the run never exhausts the token. Repos left un-enriched keep enriched=False.
    """
    ordered = sorted(projects, key=lambda p: -(p.get("_score") or p.get("stars") or 0))
    remaining = rate_remaining(token)
    if remaining is not None:
        log(f"  enrich: rate-limit remaining={remaining}")
    enriched = errors = 0
    stopped = False
    for i, p in enumerate(ordered):
        p.setdefault("enriched", False)
        if i >= max_enrich or stopped:
            break
        if remaining is not None and remaining <= keep_headroom:
            log(f"  enrich: stopping early to preserve budget (remaining={remaining})")
            break
        fn = p.get("full_name")
        if not fn:
            continue
        try:
            cc, limited = contributors_count(fn, token)
            if limited:
                stopped = True
                break
            if cc is not None:
                p["contributors"] = cc
            rel, limited = releases_info(fn, token)
            if limited:
                stopped = True
                break
            p.update(rel)
            total52, spark, limited = commit_activity(fn, token)
            if limited:
                stopped = True
                break
            p["commits_52w"], p["activity_spark"] = total52, spark
            plats, purl, limited = funding(fn, token)
            if limited:
                stopped = True
                break
            p["funding_platforms"], p["funding_url"] = plats, purl
            extra, limited = repo_extra(fn, token)
            if limited:
                stopped = True
                break
            p.update(extra)
            p["enriched"] = True
            enriched += 1
            if remaining is not None:
                remaining -= 5
        except Exception as exc:  # noqa: BLE001  (never fail the whole scan)
            errors += 1
            log(f"  enrich: {fn} failed: {type(exc).__name__}")
    return {"enriched": enriched, "errors": errors, "attempted": min(len(ordered), max_enrich),
            "rate_limit_stop": stopped}
