"""Ecosystem intelligence for the AxonOS Community Radar.

Two jobs GitHub search alone cannot do, and which a *flagship* radar of the
open BCI field must:

1. **Guaranteed inclusion.** Anchor projects — the AxonOS repos themselves and
   a hand-picked set of field-defining BCI works — are fetched *by name*, so
   they appear even with zero stars or no topics (a brand-new kernel repo has
   neither). They are flagged `ecosystem: true` and carry a short, honest
   `ecosystem_role`, never a fake star boost.

2. **Relationships, not just rows.** For anchor owners we resolve real,
   citeable signals from the public GitHub API: the maintaining org/user, its
   type, its public members (the people behind it), and which anchor repos
   share contributors — turning a list of repos into a map of who builds what,
   together.

Everything here degrades safely: no token, rate-limit, or 404 → the field is
simply omitted. Nothing is fabricated; every derived fact has a GitHub source.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API = "https://api.github.com"
_UA = "AxonOS-Community-Radar (+https://axonos.org)"


def _get_once(url, token, accept):
    req = urllib.request.Request(url, headers={
        "User-Agent": _UA,
        "Accept": accept,
        **({"Authorization": f"Bearer {token}"} if token else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 (allowlisted host)
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:  # noqa: BLE001
        return 0, None


def _get(url, token, accept="application/vnd.github+json"):
    """GET returning (status, json_or_none). Never raises.

    Anchor repos may live in a *different* org than the one running the scan.
    A workflow's built-in GITHUB_TOKEN is an installation token scoped to its
    own repository; against another org's public repos the /repos endpoint can
    answer 403/404 even though the data is public. So: try WITH the token
    first (best rate limit for same-org calls), and if that is not a 200 and a
    token was used, retry WITHOUT it — public metadata needs no auth. This
    makes ecosystem resolution work across orgs while staying degrade-safe.
    """
    status, data = _get_once(url, token, accept)
    if status != 200 and token:
        status2, data2 = _get_once(url, None, accept)
        if status2 == 200:
            return status2, data2
    return status, data


def _repo_record(data):
    """Shape a /repos/{o}/{r} payload into the radar's internal repo dict."""
    lic = (data.get("license") or {}).get("spdx_id")
    return {
        "full_name": data.get("full_name"),
        "html_url": data.get("html_url") or f"https://github.com/{data.get('full_name')}",
        "description": (data.get("description") or "").strip()[:400],
        "topics": [t.lower() for t in (data.get("topics") or [])][:20],
        "stars": int(data.get("stargazers_count") or 0),
        "forks": int(data.get("forks_count") or 0),
        "language": data.get("language") or "",
        "pushed_at": data.get("pushed_at") or "",
        "updated_at": data.get("updated_at") or "",
        "created_at": data.get("created_at") or "",
        "license": lic or None,
        "has_license": bool(lic and lic != "NOASSERTION"),
        "open_issues": int(data.get("open_issues_count") or 0),
        "homepage": (data.get("homepage") or "").strip()[:200],
        "archived": bool(data.get("archived")),
        "disabled": bool(data.get("disabled")),
        "fork": bool(data.get("fork")),
    }


def fetch_anchor_repos(anchors, token, log=print):
    """Fetch each anchor repo by name. `anchors` maps "owner/repo" -> {role,...}.

    Returns (records, meta). Records are internal repo dicts flagged
    ecosystem=True with ecosystem_role/ecosystem_note. Missing repos are noted
    in meta but never faked.
    """
    records, missing, degraded = [], [], []
    for full_name, info in anchors.items():
        info = info or {}
        status, data = _get(f"{API}/repos/{full_name}", token)
        if status == 200 and data:
            rec = _repo_record(data)
        else:
            # API unreachable (cross-org token, rate limit, outage). The repo is
            # known and curated — include it from the anchor entry itself so a
            # flagship project is never dropped from its own radar. Live figures
            # (stars/pushed_at/language) fill in on the next reachable scan.
            missing.append(full_name)
            log(f"  ecosystem: anchor {full_name} API unavailable (HTTP {status}) "
                f"\u2014 including from curated entry")
            owner, _, name = full_name.partition("/")
            rec = {
                "full_name": full_name,
                "html_url": f"https://github.com/{full_name}",
                "description": info.get("note", ""),
                "topics": [], "stars": 0, "forks": 0, "language": "",
                "pushed_at": "", "updated_at": "", "created_at": "",
                "license": None, "has_license": False, "open_issues": 0,
                "homepage": "", "archived": False, "disabled": False, "fork": False,
            }
            degraded.append(full_name)
        rec["ecosystem"] = True
        rec["ecosystem_role"] = info.get("role", "")
        rec["ecosystem_note"] = info.get("note", "")
        rec["ecosystem_group"] = info.get("group", "AxonOS")
        records.append(rec)
        log(f"  ecosystem: +{full_name} ({rec['stars']}\u2605, role='{rec['ecosystem_role']}')")
    return records, {"anchors_requested": len(anchors),
                     "anchors_found": len(records),
                     "anchors_api_missing": missing,
                     "anchors_degraded": degraded}


def resolve_owner(owner, token):
    """Public profile for an anchor owner (org or user): type, name, bio,
    location, blog, followers, public repo count. All from /users/{owner}.
    Returns {} on any failure."""
    status, d = _get(f"{API}/users/{owner}", token)
    if status != 200 or not isinstance(d, dict):
        return {}
    return {
        "login": d.get("login") or owner,
        "type": d.get("type") or "",
        "name": (d.get("name") or "").strip(),
        "company": (d.get("company") or "").strip(),
        "blog": (d.get("blog") or "").strip(),
        "location": (d.get("location") or "").strip(),
        "bio": (d.get("bio") or "").strip()[:200],
        "followers": int(d.get("followers") or 0),
        "public_repos": int(d.get("public_repos") or 0),
        "html_url": d.get("html_url") or f"https://github.com/{owner}",
        "created_at": d.get("created_at") or "",
    }


def org_members(owner, token, limit=8):
    """Public members of an org = the people behind it. Empty for users or when
    membership is private. Each: login, html_url, avatar."""
    status, d = _get(f"{API}/orgs/{owner}/public_members?per_page={limit}", token)
    if status != 200 or not isinstance(d, list):
        return []
    return [{"login": m.get("login"), "html_url": m.get("html_url"),
             "avatar_url": m.get("avatar_url")} for m in d if m.get("login")][:limit]


def repo_contributor_logins(full_name, token, limit=30):
    """Set of contributor logins for a repo (bots filtered). Used to detect
    shared-maintainer links between anchor repos."""
    status, d = _get(f"{API}/repos/{full_name}/contributors?per_page={limit}", token)
    if status != 200 or not isinstance(d, list):
        return set()
    out = set()
    for c in d:
        login = c.get("login") or ""
        if login and not login.endswith("[bot]") and c.get("type") != "Bot":
            out.add(login)
    return out


def build_ecosystem_graph(anchor_records, token, log=print):
    """From anchor repos, resolve owners, their members, and shared-contributor
    links between repos. Returns a dict the report/UI can render as a real map
    of the ecosystem. Fully degradable — partial data is fine, absent is fine.
    """
    owners = {}
    contrib_sets = {}
    for rec in anchor_records:
        fn = rec["full_name"]
        owner = fn.split("/")[0]
        if owner not in owners:
            prof = resolve_owner(owner, token)
            if prof:
                if prof.get("type") == "Organization":
                    prof["members"] = org_members(owner, token)
                owners[owner] = prof
        contrib_sets[fn] = repo_contributor_logins(fn, token)

    # Shared-maintainer edges between anchor repos (undirected, deduped).
    links = []
    names = [r["full_name"] for r in anchor_records]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            shared = contrib_sets.get(names[i], set()) & contrib_sets.get(names[j], set())
            if shared:
                links.append({"a": names[i], "b": names[j],
                              "shared": sorted(shared)[:6],
                              "weight": len(shared)})
    links.sort(key=lambda e: -e["weight"])

    # People index: who contributes across the most anchor repos.
    person_repos = {}
    for fn, cs in contrib_sets.items():
        for login in cs:
            person_repos.setdefault(login, []).append(fn)
    key_people = sorted(
        ({"login": p, "repos": sorted(rs), "reach": len(rs)}
         for p, rs in person_repos.items() if len(rs) >= 2),
        key=lambda x: -x["reach"])[:12]

    log(f"  ecosystem graph: {len(owners)} owners, {len(links)} shared-maintainer links, "
        f"{len(key_people)} cross-repo people")
    return {
        "owners": owners,
        "links": links,
        "key_people": key_people,
        "repo_count": len(anchor_records),
    }
