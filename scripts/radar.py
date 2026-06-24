#!/usr/bin/env python3
"""
Open BCI Ecosystem Radar — data refresher.

Scans public GitHub topic search for active open BCI / neurotech / real-time /
privacy / signal-processing projects, categorises them heuristically, and writes
a public data/radar.json that the published radar page renders.

Honest by construction: only public search data, deduplicated and capped, with a
generated_at timestamp and the exact criteria recorded in the output. No
auto-comments, no reactions, no follows. Optionally (RADAR_ISSUE=1) posts a
maintainer-only review digest as an issue.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "data", "seeds.json")
OUT = os.path.join(ROOT, "data", "radar.json")

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
SELF_REPO = os.environ.get("GITHUB_REPOSITORY", "AxonOS-BCI/axonos-community-radar").lower()

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "AxonOS-Community-Radar",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def gh_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_seeds():
    with open(SEEDS, encoding="utf-8") as fh:
        return json.load(fh)


def categorise(repo, categories):
    hay = " ".join([
        " ".join(repo.get("topics") or []),
        (repo.get("language") or ""),
        (repo.get("full_name") or ""),
        (repo.get("description") or ""),
    ]).lower()
    best, best_score = "Other", 0
    for cat, kws in categories.items():
        score = sum(1 for kw in kws if kw.lower() in hay)
        if score > best_score:
            best, best_score = cat, score
    return best


def main():
    seeds = load_seeds()
    topics = seeds.get("topics", [])
    categories = seeds.get("categories", {})
    max_per_topic = int(seeds.get("max_per_topic", 25))
    max_projects = int(seeds.get("max_projects", 120))
    min_stars = int(seeds.get("min_stars", 0))

    repos = {}
    for topic in topics:
        q = f"topic:{topic} archived:false fork:false"
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
            "q": q, "sort": "updated", "order": "desc", "per_page": str(max_per_topic),
        })
        print(f"Scanning topic:{topic}")
        try:
            data = gh_json(url)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: search failed for topic:{topic}: {exc}")
            continue
        for item in data.get("items", []):
            fn = item.get("full_name")
            if not fn or fn.lower() == SELF_REPO:
                continue
            if int(item.get("stargazers_count") or 0) < min_stars:
                continue
            repos[fn] = {
                "full_name": fn,
                "html_url": item.get("html_url"),
                "description": (item.get("description") or "").strip(),
                "stars": int(item.get("stargazers_count") or 0),
                "forks": int(item.get("forks_count") or 0),
                "language": item.get("language") or "",
                "pushed_at": item.get("pushed_at") or "",
                "topics": item.get("topics") or [],
            }

    now = datetime.now(timezone.utc)
    out = []
    for r in repos.values():
        try:
            pushed = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
            days = (now - pushed).days
        except Exception:  # noqa: BLE001
            days = 9999
        import math
        score = math.log10(r["stars"] + 1) * 10 + max(0, 60 - days) * 0.5
        r["days_since_push"] = days
        r["active"] = days <= 30
        r["category"] = categorise(r, categories)
        r["_score"] = round(score, 3)
        out.append(r)

    out.sort(key=lambda x: x["_score"], reverse=True)
    out = out[:max_projects]

    payload = {
        "version": 1,
        "generated_at": now.replace(microsecond=0).isoformat(),
        "source": "GitHub topic search (public)",
        "criteria": (
            "Public, non-archived, non-fork repositories matching curated BCI / "
            "neurotech / real-time / privacy topics, ranked by recent activity and "
            "stars. Categorisation is heuristic and opinionated."
        ),
        "refresh": "every 6 hours via GitHub Actions",
        "topics": topics,
        "counts": {
            "total": len(out),
            "active_30d": sum(1 for r in out if r["active"]),
        },
        "projects": out,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"Wrote {OUT}: {len(out)} projects ({payload['counts']['active_30d']} active in 30d)")

    # Optional maintainer-only review digest (ethical: no auto-engagement)
    if os.environ.get("RADAR_ISSUE") == "1" and TOKEN:
        top = out[:25]
        lines = ["# Open BCI Ecosystem — review digest", "",
                 f"Generated {payload['generated_at']} · {len(out)} projects.", "",
                 "Engagement policy: star only relevant repos; react only to genuinely "
                 "relevant releases; open PRs only when they add technical value; prefer "
                 "tests, docs, reproducibility, benchmarks and protocol notes; no low-signal comments.", ""]
        for r in top:
            lines.append(f"- [{r['full_name']}]({r['html_url']}) — ⭐{r['stars']} · {r['language'] or 'n/a'} · {r['category']} · pushed {r['days_since_push']}d ago")
        body = "\n".join(lines)
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{SELF_REPO}/issues",
                data=json.dumps({"title": f"Radar review digest — {now.date()}", "body": body}).encode("utf-8"),
                headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=30)
            print("Posted review digest issue.")
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: could not post digest issue: {exc}")


if __name__ == "__main__":
    main()
