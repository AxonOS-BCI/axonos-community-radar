#!/usr/bin/env python3
"""
AxonOS Radar — data refresher (v3).

Honest, hardened data pipeline:
  * Relevance filtering — keep a repo only if it carries a core BCI/neuro topic, or a
    context topic plus a neuro keyword. Generic VPN/password/embedded repos are dropped.
  * Deterministic scoring — recency from the current 6-hour snapshot slot, so unchanged
    projects keep the same score between refreshes.
  * Partial-failure safe — if more than FAIL_RATIO of topic queries fail, abort WITHOUT
    writing, so the last-good committed data is preserved (no half-empty radar).
  * Durable identity — `first_seen` is tracked in a dedicated data/first_seen.json that
    survives corruption of radar.json (bootstrapped from radar.json on first migration),
    so a bad read can never flag the whole ecosystem as "new".
  * Rate-limit aware, response-size capped, timezone-robust, self-validating.
  * Emits an RSS feed (XML-correct escaping) of the newest projects. No auto-engagement.
"""
import base64  # noqa: F401  (kept for parity; not required at runtime)
import json
import os
import re
import functools
import sys
import time
import math
import urllib.parse
import urllib.request
import urllib.error
from xml.sax.saxutils import escape as _xescape
from datetime import datetime, timezone
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "data", "seeds.json")
OUT = os.path.join(ROOT, "data", "radar.json")
FIRST_SEEN = os.path.join(ROOT, "data", "first_seen.json")
FEED = os.path.join(ROOT, "feed.xml")

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
SELF_REPO = os.environ.get("GITHUB_REPOSITORY", "AxonOS-BCI/axonos-community-radar").lower()
SITE = "https://axonos-bci.github.io/axonos-community-radar/"

MAX_RESPONSE_BYTES = 8 * 1024 * 1024   # cap a single API response
FAIL_RATIO = 0.25                       # abort if more than this fraction of topics fail
FIRST_SEEN_TTL_DAYS = 400               # bound the first_seen log

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "AxonOS-Community-Radar"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def xesc(s):
    """XML-correct escaping for element content and attribute values."""
    return _xescape(str(s if s is not None else ""), {'"': "&quot;", "'": "&apos;"})


def gh_json(url, retries=3):
    """GET JSON with rate-limit backoff and a response-size cap."""
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError("API response exceeds size cap")
                time.sleep(0.7)  # respectful spacing — intentionally serial
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("unexpected API response shape")
                return data
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                reset = exc.headers.get("X-RateLimit-Reset")
                if exc.headers.get("X-RateLimit-Remaining") == "0" and reset:
                    wait = min(max(int(reset) - int(time.time()), 5), 90)
                    print(f"  rate limited — sleeping {wait}s")
                    time.sleep(wait)
                    continue
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise exc
    return {"items": []}


def load_seeds():
    with open(SEEDS, encoding="utf-8") as fh:
        return json.load(fh)


def load_first_seen(snap_iso):
    """
    Durable first_seen map. Order of resolution:
      1. data/first_seen.json (source of truth).
      2. If absent, bootstrap from radar.json's existing first_seen values (migration).
      3. If radar.json is present but corrupt, abort (do NOT reset — that would flood NEW).
    """
    if os.path.exists(FIRST_SEEN):
        try:
            with open(FIRST_SEEN, encoding="utf-8") as fh:
                d = json.load(fh)
            if isinstance(d, dict):
                return {k: v for k, v in d.items() if isinstance(v, str)}
        except Exception as exc:  # noqa: BLE001
            print(f"CRITICAL: first_seen.json is corrupt ({exc}); aborting to avoid NEW flood.")
            sys.exit(1)
    # bootstrap from radar.json if it exists
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as fh:
                prev = json.load(fh)
            return {p["full_name"]: p.get("first_seen") or snap_iso
                    for p in prev.get("projects", []) if p.get("full_name")}
        except Exception as exc:  # noqa: BLE001
            print(f"CRITICAL: radar.json present but unreadable ({exc}); aborting to preserve identity.")
            sys.exit(1)
    return {}


def save_first_seen(mapping, current_names, snap):
    """Persist, pruning stale entries (not current and older than the TTL)."""
    pruned = {}
    for fn, iso in mapping.items():
        if fn in current_names:
            pruned[fn] = iso
            continue
        try:
            if (snap - datetime.fromisoformat(iso)).days <= FIRST_SEEN_TTL_DAYS:
                pruned[fn] = iso
        except Exception:  # noqa: BLE001
            pruned[fn] = iso
    with open(FIRST_SEEN, "w", encoding="utf-8") as fh:
        json.dump(pruned, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def repo_text(repo):
    return " ".join([
        " ".join(repo.get("topics") or []), repo.get("language") or "",
        repo.get("full_name") or "", repo.get("description") or "",
    ]).lower()


@functools.lru_cache(maxsize=8)
def _kw_pattern(keywords):
    """Word-start-anchored keyword regex (prefix match). Prevents short keywords like
    'erp'/'lfp' from matching inside unrelated words ('interpreter', 'cleverpad')."""
    return re.compile(r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")", re.IGNORECASE)


def is_relevant(repo, core, context, keywords):
    topics = {t.lower() for t in (repo.get("topics") or [])}
    if topics & core:
        return True
    if topics & context and _kw_pattern(tuple(keywords)).search(repo_text(repo)):
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
    return now, now.replace(hour=slot, minute=0, second=0, microsecond=0)


def days_since(iso, snap):
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, (snap - dt).days)
    except Exception:  # noqa: BLE001
        return 9999


def build_feed(projects, generated):
    items = sorted([p for p in projects if p.get("first_seen")],
                   key=lambda p: p["first_seen"], reverse=True)[:25]
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>',
             "<title>AxonOS Radar — new projects</title>",
             f"<link>{xesc(SITE)}</link>",
             "<description>Newly discovered open brain-computer-interface projects.</description>",
             f"<lastBuildDate>{xesc(format_datetime(generated))}</lastBuildDate>"]
    for p in items:
        try:
            pub = format_datetime(datetime.fromisoformat(p["first_seen"]))
        except Exception:  # noqa: BLE001
            pub = format_datetime(generated)
        url = p.get("html_url") or SITE
        parts.append("<item>"
                     f"<title>{xesc(p['full_name'])}</title>"
                     f"<link>{xesc(url)}</link>"
                     f'<guid isPermaLink="true">{xesc(url)}</guid>'
                     f"<category>{xesc(p.get('category') or 'Other')}</category>"
                     f"<pubDate>{xesc(pub)}</pubDate>"
                     f"<description>{xesc(p.get('description') or p.get('category') or '')}</description>"
                     "</item>")
    parts.append("</channel></rss>")
    return "\n".join(parts) + "\n"


def validate(payload, cap):
    p = payload.get("projects", [])
    assert isinstance(p, list), "projects must be a list"
    assert len(p) <= cap, f"too many projects: {len(p)} > {cap}"
    assert payload["counts"]["total"] >= 0, "negative total"
    for r in p:
        assert r.get("full_name"), "project missing full_name"
        assert (r.get("html_url") or "").startswith("https://github.com/"), f"suspicious url: {r.get('html_url')!r}"
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
    snap_iso = snap.isoformat()
    fseen = load_first_seen(snap_iso)

    repos, scanned, dropped, failed = {}, 0, 0, []
    for topic in topics:
        q = f"topic:{topic} archived:false fork:false"
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "updated", "order": "desc", "per_page": str(max_per_topic)})
        print(f"Scanning topic:{topic}")
        try:
            data = gh_json(url)
        except Exception as exc:  # noqa: BLE001  (resilience: collect, decide after loop)
            print(f"  WARN: search failed for topic:{topic}: {type(exc).__name__}: {exc}")
            failed.append(topic)
            continue
        for item in data.get("items", []):
            scanned += 1
            fn = item.get("full_name")
            if not fn or fn.lower() == SELF_REPO or fn in repos:
                continue
            if fn.split("/")[0].lower() in excl_owners or fn.lower() in excl_repos:
                continue
            if int(item.get("stargazers_count") or 0) < min_stars:
                continue
            if not is_relevant(item, core, context, keywords):
                dropped += 1
                continue
            repos[fn] = {
                "full_name": fn, "html_url": item.get("html_url"),
                "description": (item.get("description") or "").strip()[:240],
                "stars": int(item.get("stargazers_count") or 0),
                "forks": int(item.get("forks_count") or 0),
                "language": item.get("language") or "",
                "pushed_at": item.get("pushed_at") or "",
                "topics": (item.get("topics") or [])[:12],
            }

    # Partial-failure safeguard: preserve last-good data rather than publishing a half-empty radar.
    if topics and len(failed) / len(topics) > FAIL_RATIO:
        print(f"CRITICAL: {len(failed)}/{len(topics)} topic queries failed "
              f"(> {int(FAIL_RATIO*100)}%). Aborting WITHOUT writing to preserve committed data.")
        sys.exit(1)

    out = []
    for r in repos.values():
        days = days_since(r["pushed_at"], snap)
        first_seen = fseen.get(r["full_name"]) or snap_iso
        fseen[r["full_name"]] = first_seen
        try:
            is_new = (snap - datetime.fromisoformat(first_seen)).days <= new_days
        except Exception:  # noqa: BLE001
            is_new = False
        r.update({"days_since_push": days, "active": days <= 30,
                  "category": categorise(r, categories), "first_seen": first_seen,
                  "is_new": is_new,
                  "_score": round(math.log10(r["stars"] + 1) * 10 + max(0, 60 - days) * 0.5, 3)})
        out.append(r)

    out.sort(key=lambda x: x["_score"], reverse=True)
    out = out[:max_projects]

    payload = {
        "version": 2, "generated_at": now.replace(microsecond=0).isoformat(),
        "snapshot_at": snap_iso, "source": "GitHub topic search (public)",
        "criteria": ("Public, non-archived, non-fork repositories that carry a core BCI/neuro "
                     "topic, or a context topic plus a neuro keyword. Ranked by recency (from the "
                     "6-hour snapshot slot) and stars. Categorisation is heuristic and opinionated."),
        "refresh": "every 6 hours via GitHub Actions", "min_stars": min_stars,
        "topics_failed": len(failed), "topics": topics,
        "counts": {"total": len(out), "active_30d": sum(1 for r in out if r["active"]),
                   "new": sum(1 for r in out if r["is_new"])},
        "projects": out,
    }
    validate(payload, max_projects)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    save_first_seen(fseen, set(repos.keys()), snap)
    with open(FEED, "w", encoding="utf-8") as fh:
        fh.write(build_feed(out, now))
    print(f"Wrote {len(out)} projects (scanned {scanned}, dropped {dropped} off-topic, "
          f"{len(failed)} topics failed, {payload['counts']['active_30d']} active, "
          f"{payload['counts']['new']} new). first_seen + feed updated.")

    if os.environ.get("RADAR_ISSUE") == "1" and TOKEN:
        lines = ["# AxonOS Radar — review digest", "",
                 f"Generated {payload['generated_at']} · {len(out)} projects.", "",
                 "Engagement policy: star only relevant repos; react only to genuinely relevant "
                 "releases; open PRs only when they add technical value; no low-signal noise.", ""]
        for r in out[:25]:
            lines.append(f"- [{r['full_name']}]({r['html_url']}) — ⭐{r['stars']} · "
                         f"{r['language'] or 'n/a'} · {r['category']}{' · NEW' if r['is_new'] else ''}")
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
