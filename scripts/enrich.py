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


def owner_extra(owner, token):
    """Public owner profile bits for the Builders board: account type and
    followers. One call per owner; used only for the small builders list."""
    code, data, _ = gh_get(f"{API}/users/{owner}", token)
    if code == 429:
        return None, True
    if code != 200 or not isinstance(data, dict):
        return {}, False
    return {"owner_type": (data.get("type") or ""),
            "followers": int(data.get("followers") or 0)}, False


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
    """52 weekly commit totals. Returns (total_52w, last_12_weeks, limited).

    GitHub answers 202 while it is still computing the histogram; a single short
    retry usually resolves it. If it is still pending we return None (meaning
    "unknown, not zero") so a fresh repo is never mislabelled as inactive."""
    code, data, _ = gh_get(f"{API}/repos/{fn}/stats/commit_activity", token)
    if code == 202:
        time.sleep(2.5)
        code, data, _ = gh_get(f"{API}/repos/{fn}/stats/commit_activity", token)
    if code == 429:
        return None, None, True
    if code == 202:
        return None, None, False   # still computing — unknown, not zero
    if code != 200 or not isinstance(data, list) or not data:
        return 0, [], False
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
    }.get(key, _https_only(val))


def _https_only(val):
    """Custom FUNDING.yml entries: accept only well-formed https URLs.
    http:// and free-form strings that merely start with 'http' are rejected
    (audit: open-redirect surface in the funding pill)."""
    if not isinstance(val, str) or not val.startswith("https://"):
        return ""
    try:
        q = urllib.parse.urlparse(val)
        return val if (q.scheme == "https" and q.netloc) else ""
    except Exception:  # noqa: BLE001
        return ""


# ── Foundation signals (v6) ─────────────────────────────────────────────────
# Answers the field's most practical trust question — "can I build on this?" —
# with checkable facts only: community-profile files, a root CITATION.cff, a
# root SECURITY.md, and whether CI workflows exist. Absence of evidence is
# recorded as absence (no `foundation` field), never as a fabricated zero.

FOUNDATION_KEYS = ("license_file", "readme", "contributing", "code_of_conduct",
                   "citation", "security_policy", "ci")


def _parse_community_profile(data) -> dict | None:
    """Booleans from GET /repos/{fn}/community/profile."""
    if not isinstance(data, dict):
        return None
    files = data.get("files") or {}
    hp = data.get("health_percentage")
    return {
        # API contract: each entry is an object when the file exists, null
        # when it does not — so presence is `is not None`, not truthiness.
        "license_file": files.get("license") is not None,
        "readme": files.get("readme") is not None,
        "contributing": files.get("contributing") is not None,
        "code_of_conduct": files.get("code_of_conduct") is not None,
        "health_pct": int(hp) if isinstance(hp, int) and 0 <= hp <= 100 else None,
    }


def _foundation_assemble(profile: dict, citation: bool, security: bool,
                         ci: bool) -> dict:
    out = dict(profile)
    out["citation"] = bool(citation)
    out["security_policy"] = bool(security)
    out["ci"] = bool(ci)
    out["count"] = sum(1 for k in FOUNDATION_KEYS if out.get(k))
    return out


def _exists_at(fn, path, token):
    """(exists: bool | None, limited). None = indeterminate (network/5xx) —
    the caller then skips the whole foundation block rather than guess."""
    code, _, _ = gh_get(f"{API}/repos/{fn}/contents/{path}", token)
    if code == 429:
        return None, True
    if code == 200:
        return True, False
    if code == 404:
        return False, False
    return None, False


def foundation(fn, token):
    """Foundation dict for one repo, or (None, limited) when it cannot be
    established honestly this cycle."""
    code, data, _ = gh_get(f"{API}/repos/{fn}/community/profile", token)
    if code == 429:
        return None, True
    profile = _parse_community_profile(data) if code == 200 else None
    if profile is None:
        return None, False
    citation, limited = _exists_at(fn, "CITATION.cff", token)
    if limited:
        return None, True
    security, limited = _exists_at(fn, "SECURITY.md", token)
    if limited:
        return None, True
    code, wf, _ = gh_get(f"{API}/repos/{fn}/actions/workflows", token)
    if code == 429:
        return None, True
    if code != 200 or not isinstance(wf, dict):
        ci = None
    else:
        ci = int(wf.get("total_count") or 0) > 0
    if citation is None or security is None or ci is None:
        return None, False
    return _foundation_assemble(profile, citation, security, ci), False


def repo_extra(fn, token):
    code, data, _ = gh_get(f"{API}/repos/{fn}", token)
    if code == 429:
        return None, True
    if code != 200 or not isinstance(data, dict):
        return {}, False
    home = (data.get("homepage") or "").strip()
    if home and not (home.startswith("https://") or home.startswith("http://")):
        home = ""   # ingress validation: only http(s) homepages survive
    return {
        "watchers": int(data.get("subscribers_count") or 0),
        "size_kb": int(data.get("size") or 0),
        "open_issues": int(data.get("open_issues_count") or 0),
        "homepage": home,
        "archived": bool(data.get("archived")),
        "disabled": bool(data.get("disabled")),
    }, False


def _enrich_one(p, token):
    """Enrich a single project in place. Returns (ok: bool, limited: bool)."""
    fn = p.get("full_name")
    if not fn:
        return False, False
    cc, limited = contributors_count(fn, token)
    if limited:
        return False, True
    if cc is not None:
        p["contributors"] = cc
    rel, limited = releases_info(fn, token)
    if limited:
        return False, True
    p.update(rel)
    total52, spark, limited = commit_activity(fn, token)
    if limited:
        return False, True
    if total52 is None:
        p["activity_pending"] = True   # GitHub still computing — retried once
    else:
        p["commits_52w"], p["activity_spark"] = total52, spark
    plats, purl, limited = funding(fn, token)
    if limited:
        return False, True
    p["funding_platforms"], p["funding_url"] = plats, purl
    extra, limited = repo_extra(fn, token)
    if limited:
        return False, True
    p.update(extra)
    fnd, limited = foundation(fn, token)
    if limited:
        return False, True
    if fnd is not None:
        p["foundation"] = fnd
    p["enriched"] = True
    return True, False


def enrich_repos(projects, token, max_enrich=200, keep_headroom=200, log=print,
                 workers=4):
    """Enrich projects in place (highest-scoring first). Returns a stats dict.

    v5: runs on a small thread pool (stdlib concurrent.futures) — enrichment is
    pure I/O wait, so 4 polite workers cut wall time ~3-4x while each worker
    keeps the same per-request spacing as before. A shared, locked budget stops
    every worker once the remaining rate limit approaches keep_headroom, so the
    run never exhausts the token. Repos left un-enriched keep enriched=False.
    """
    import concurrent.futures
    import threading

    ordered = sorted(projects, key=lambda p: -(p.get("_score") or p.get("stars") or 0))
    for p in ordered:
        p.setdefault("enriched", False)
    todo = ordered[:max_enrich]

    remaining = rate_remaining(token)
    if remaining is not None:
        log(f"  enrich: rate-limit remaining={remaining}, workers={workers}")

    lock = threading.Lock()
    state = {"remaining": remaining, "enriched": 0, "errors": 0, "stopped": False}

    def budget_ok():
        with lock:
            if state["stopped"]:
                return False
            if state["remaining"] is not None and state["remaining"] <= keep_headroom:
                state["stopped"] = True
                log(f"  enrich: stopping early to preserve budget "
                    f"(remaining={state['remaining']})")
                return False
            return True

    def work(p):
        if not budget_ok():
            return
        try:
            ok, limited = _enrich_one(p, token)
            with lock:
                if limited:
                    state["stopped"] = True
                elif ok:
                    state["enriched"] += 1
                if state["remaining"] is not None:
                    state["remaining"] -= 9   # v6: +community profile, CITATION, SECURITY, workflows
        except Exception as exc:  # noqa: BLE001  (never fail the whole scan)
            with lock:
                state["errors"] += 1
            log(f"  enrich: {p.get('full_name')} failed: {type(exc).__name__}")

    if workers <= 1 or len(todo) <= 2:
        for p in todo:
            work(p)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(work, todo))

    return {"enriched": state["enriched"], "errors": state["errors"],
            "attempted": len(todo), "rate_limit_stop": state["stopped"]}
