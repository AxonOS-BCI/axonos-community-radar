#!/usr/bin/env python3
"""
Open BCI Ecosystem Radar — data refresher (v2).

Maxed-out, honest data pipeline:
  * Relevance filtering — a repo is kept only if it carries a core BCI/neuro topic,
    or a context topic *plus* a neuro keyword in its name/description/topics. This
    keeps generic VPN / password-manager / embedded repos off the radar.
  * Deterministic scoring — recency is measured from the current 6-hour snapshot
    slot (00/06/12/18 UTC), not wall-clock "now", so a repo that has not changed
    keeps the same score between refreshes (no "jumping" projects).
  * Rate-limit aware — honours GitHub's secondary limits (403 + X-RateLimit-Reset)
    with bounded backoff and a respectful delay between calls.
  * Change tracking — carries forward a stable `first_seen` per repo from the
    previous data file and flags `is_new` within a configurable window.
  * Self-validating — refuses to write a malformed data file (so CI never commits
    garbage), and emits an RSS feed of the newest projects.

Public data only. Categorisation is heuristic and disclosed. No auto-engagement.
"""
import json
import os
import sys
import time
import math
import html
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "data", "seeds.json")
OUT = os.path.join(ROOT, "data", "radar.json")
FEED = os.path.join(ROOT, "feed.xml")

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
SELF_REPO = os.environ.get("GITHUB_REPOSITORY", "AxonOS-BCI/axonos-community-radar").lower()
SITE = "https://axonos-bci.github.io/axonos-community-radar/"

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "AxonOS-Community-Radar"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def gh_json(url, retries=3):
    """GET JSON, honouring rate limits with bounded backoff."""
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                time.sleep(0.7)  # respectful spacing between calls
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                reset = exc.headers.get("X-RateLimit-Reset")
                remaining = exc.headers.get("X-RateLimit-Remaining")
                if remaining == "0" and reset:
                    wait = min(max(int(reset) - int(time.time()), 5), 90)
                    print(f"  rate limited — sleeping {wait}s")
                    time.sleep(wait)
                    continue
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise exc
    return {"items": []}


def load_seeds():
    with open(SEEDS, encoding="utf-8") as fh:
        return json.load(fh)


def load_previous():
    """Return {full_name: first_seen_iso} from the last committed data file."""
    try:
        with open(OUT, encoding="utf-8") as fh:
            prev = json.load(fh)
        return {p["full_name"]: p.get("first_seen") for p in prev.get("projects", []) if p.get("full_name")}
    except Exception:  # noqa: BLE001
        return {}


def repo_text(repo):
    return " ".join([
        " ".join(repo.get("topics") or []),
        repo.get("language") or "",
        repo.get("full_name") or "",
        repo.get("description") or "",
    ]).lower()


def is_relevant(repo, core, context, keywords):
    topics = {t.lower() for t in (repo.get("topics") or [])}
    if topics & core:
        return True
    if topics & context:
        text = repo_text(repo)
        if any(kw in text for kw in keywords):
            return True
    return False


def categorise(repo, categories):
    hay = repo_text(repo)
    best, best_score = "Other", 0
    for cat, kws in categories.items():
        score = sum(1 for kw in kws if kw.lower() in hay)
        if score > best_score:
            best, best_score = cat, score
    return best


def snapshot_now():
    now = datetime.now(timezone.utc)
    slot = (now.hour // 6) * 6
    snap = now.replace(hour=slot, minute=0, second=0, microsecond=0)
    return now, snap


def days_since(iso, snap):
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return max(0, (snap - dt).days)
    except Exception:  # noqa: BLE001
        return 9999


def build_feed(projects, generated):
    items = sorted([p for p in projects if p.get("first_seen")], key=lambda p: p["first_seen"], reverse=True)[:25]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0"><channel>',
        "<title>Open BCI Ecosystem Radar — new projects</title>",
        f"<link>{SITE}</link>",
        "<description>Newly discovered open brain-computer-interface projects.</description>",
        f"<lastBuildDate>{format_datetime(generated)}</lastBuildDate>",
    ]
    for p in items:
        try:
            pub = format_datetime(datetime.fromisoformat(p["first_seen"]))
        except Exception:  # noqa: BLE001
            pub = format_datetime(generated)
        desc = html.escape(p.get("description") or p.get("category") or "")
        parts.append(
            "<item>"
            f"<title>{html.escape(p['full_name'])}</title>"
            f"<link>{html.escape(p.get('html_url') or SITE)}</link>"
            f"<guid isPermaLink=\"true\">{html.escape(p.get('html_url') or SITE)}</guid>"
            f"<category>{html.escape(p.get('category') or 'Other')}</category>"
            f"<pubDate>{pub}</pubDate>"
            f"<description>{desc}</description>"
            "</item>"
        )
    parts.append("</channel></rss>")
    return "\n".join(parts) + "\n"


def validate(payload, cap):
    p = payload.get("projects", [])
    assert isinstance(p, list), "projects must be a list"
    assert len(p) <= cap, f"too many projects: {len(p)} > {cap}"
    assert payload["counts"]["total"] >= 0, "negative total"
    for r in p:
        assert r.get("full_name"), "project missing full_name"
        url = r.get("html_url") or ""
        assert url.startswith("https://github.com/"), f"suspicious url: {url!r}"
        assert r.get("category"), "project missing category"


def main():
    seeds = load_seeds()
    core = {t.lower() for t in seeds.get("core_topics", [])}
    context = {t.lower() for t in seeds.get("context_topics", [])}
    keywords = [k.lower() for k in seeds.get("neuro_keywords", [])]
    categories = seeds.get("categories", {})
    topics = seeds.get("core_topics", []) + seeds.get("context_topics", [])
    max_per_topic = int(seeds.get("max_per_topic", 25))
    max_projects = int(seeds.get("max_projects", 120))
    min_stars = int(seeds.get("min_stars", 3))
    new_days = int(seeds.get("new_window_days", 7))
    excl_owners = {o.lower() for o in seeds.get("exclude_owners", [])}
    excl_repos = {r.lower() for r in seeds.get("exclude_repos", [])}

    now, snap = snapshot_now()
    prev = load_previous()

    repos, kept, scanned, dropped = {}, 0, 0, 0
    for topic in topics:
        q = f"topic:{topic} archived:false fork:false"
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "updated", "order": "desc", "per_page": str(max_per_topic)})
        print(f"Scanning topic:{topic}")
        try:
            data = gh_json(url)
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN: search failed for topic:{topic}: {exc}")
            continue
        for item in data.get("items", []):
            scanned += 1
            fn = item.get("full_name")
            if not fn or fn.lower() == SELF_REPO:
                continue
            owner = fn.split("/")[0].lower()
            if owner in excl_owners or fn.lower() in excl_repos:
                continue
            if int(item.get("stargazers_count") or 0) < min_stars:
                continue
            if fn in repos:
                continue
            if not is_relevant(item, core, context, keywords):
                dropped += 1
                continue
            repos[fn] = {
                "full_name": fn,
                "html_url": item.get("html_url"),
                "description": (item.get("description") or "").strip()[:240],
                "stars": int(item.get("stargazers_count") or 0),
                "forks": int(item.get("forks_count") or 0),
                "language": item.get("language") or "",
                "pushed_at": item.get("pushed_at") or "",
                "topics": (item.get("topics") or [])[:12],
            }
            kept += 1

    out = []
    snap_iso = snap.isoformat()
    for r in repos.values():
        days = days_since(r["pushed_at"], snap)
        first_seen = prev.get(r["full_name"]) or snap_iso
        try:
            is_new = (snap - datetime.fromisoformat(first_seen)).days <= new_days
        except Exception:  # noqa: BLE001
            is_new = False
        r["days_since_push"] = days
        r["active"] = days <= 30
        r["category"] = categorise(r, categories)
        r["first_seen"] = first_seen
        r["is_new"] = is_new
        r["_score"] = round(math.log10(r["stars"] + 1) * 10 + max(0, 60 - days) * 0.5, 3)
        out.append(r)

    out.sort(key=lambda x: x["_score"], reverse=True)
    out = out[:max_projects]

    payload = {
        "version": 2,
        "generated_at": now.replace(microsecond=0).isoformat(),
        "snapshot_at": snap_iso,
        "source": "GitHub topic search (public)",
        "criteria": (
            "Public, non-archived, non-fork repositories that carry a core BCI/neuro topic, "
            "or a context topic plus a neuro keyword. Ranked by recency (from the 6-hour "
            "snapshot slot) and stars. Categorisation is heuristic and opinionated."
        ),
        "refresh": "every 6 hours via GitHub Actions",
        "min_stars": min_stars,
        "topics": topics,
        "counts": {
            "total": len(out),
            "active_30d": sum(1 for r in out if r["active"]),
            "new": sum(1 for r in out if r["is_new"]),
        },
        "projects": out,
    }

    validate(payload, max_projects)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    with open(FEED, "w", encoding="utf-8") as fh:
        fh.write(build_feed(out, now))
    print(f"Wrote {len(out)} projects (scanned {scanned}, dropped {dropped} off-topic, "
          f"{payload['counts']['active_30d']} active, {payload['counts']['new']} new). Feed updated.")

    if os.environ.get("RADAR_ISSUE") == "1" and TOKEN:
        top = out[:25]
        lines = ["# Open BCI Ecosystem — review digest", "",
                 f"Generated {payload['generated_at']} · {len(out)} projects.", "",
                 "Engagement policy: star only relevant repos; react only to genuinely relevant "
                 "releases; open PRs only when they add technical value; no low-signal noise.", ""]
        for r in top:
            lines.append(f"- [{r['full_name']}]({r['html_url']}) — ⭐{r['stars']} · {r['language'] or 'n/a'} · "
                         f"{r['category']}{' · NEW' if r['is_new'] else ''}")
        body = json.dumps({"title": f"Radar review digest — {now.date()}", "body": "\n".join(lines)})
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{SELF_REPO}/issues",
                                         data=body.encode("utf-8"),
                                         headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=30)
            print("Posted review digest issue.")
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: could not post digest issue: {exc}")


if __name__ == "__main__":
    main()
