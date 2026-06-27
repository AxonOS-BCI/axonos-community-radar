#!/usr/bin/env python3
"""Publish/update ONE living GitHub issue with the radar's ecosystem statistics.

Zero runtime dependencies. The issue carries a hidden marker; this script finds
that one issue and edits it in place (or creates it the first time), so there is
always exactly one always-current "live dashboard" issue rather than a flood of
new issues. Runs after radar.py + publish_data.py in the scheduled workflow.

Posture: inclusion is not endorsement; figures are discovery signals, not
quality, safety, or clinical ratings; AxonOS is ranked like everyone else.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")  # "owner/name"
MARKER = "<!-- axonos-radar-stats -->"
TITLE = "\U0001F4E1 AxonOS Radar \u2014 Live Ecosystem Stats"
API = "https://api.github.com"


def _api(method, path, body=None):
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "axonos-radar-stats",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def k(n):
    n = n or 0
    return (f"{n / 1000:.1f}k".replace(".0k", "k")) if n >= 1000 else str(n)


def bar(v, mx, width=12):
    if mx <= 0:
        return ""
    return "\u2588" * (max(1, round(v / mx * width)) if v else 0)


def pages_url(repo):
    owner, _, name = repo.partition("/")
    return f"https://{owner.lower()}.github.io/{name}/"


def build_body(radar, history, repo):
    p = radar.get("projects", [])
    c = radar.get("counts", {})
    builders = radar.get("builders", [])
    base = pages_url(repo)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tot = c.get("total", len(p))
    stars = sum(int(x.get("stars") or 0) for x in p)
    active = c.get("active_30d", sum(1 for x in p if x.get("active")))
    new = c.get("new", sum(1 for x in p if x.get("is_new")))
    rising = c.get("rising", sum(1 for x in p if x.get("rising")))
    nbuild = len(builders) or c.get("builders", 0)

    snaps = sorted(history.get("snapshots", []), key=lambda s: s.get("snapshot_at", ""))
    delta = ""
    if len(snaps) >= 2:
        prev = snaps[-2].get("meta") or {}
        dp = tot - (prev.get("total") or tot)
        ds = stars - (prev.get("total_stars") or stars)
        if dp or ds:
            delta = f"_\u0394 since last refresh: {dp:+d} projects \u00b7 {ds:+d} \u2605_"

    L = [MARKER, f"# {TITLE}\n",
         "> The open brain\u2013computer-interface field, tracked automatically from public GitHub "
         "metadata. **Inclusion is not endorsement; figures are discovery signals, not quality, "
         "safety, or clinical ratings.** AxonOS is ranked by the same formula as everyone else.\n",
         f"**Updated:** {now} \u00b7 refreshes every 6h \u00b7 [\U0001F4C8 live stats]({base}stats.html) "
         f"\u00b7 [\U0001F5FA map]({base}) \u00b7 "
         f"[\u2795 add a project](https://github.com/{repo}/issues/new?template=add-project.yml)\n",
         "## \U0001F4CA At a glance\n",
         "| Projects | Total \u2605 | Active 30d | New (7d) | \U0001F525 Rising | \U0001F3D7 Builders |",
         "|---:|---:|---:|---:|---:|---:|",
         f"| **{tot}** | **{k(stars)}** | {active} | {new} | {rising} | {nbuild} |"]
    if delta:
        L.append("\n" + delta)

    ris = sorted([x for x in p if x.get("rising")], key=lambda x: -(x.get("stars_delta_7d") or 0))[:5]
    if ris:
        L.append("\n## \U0001F525 Rising \u2014 biggest 7-day movers\n")
        for i, x in enumerate(ris, 1):
            L.append(f"{i}. **[{x['full_name']}]({x['html_url']})** \u2191 +{x.get('stars_delta_7d', 0)}/7d "
                     f"\u00b7 \u2605 {x.get('stars', 0)} \u00b7 _{x.get('category', '')}_")

    nw = [x for x in p if x.get("is_new")][:6]
    if nw:
        L.append("\n## \U0001F195 New this week\n")
        for x in nw:
            d = (x.get("description") or "").strip()
            d = (d[:80] + "\u2026") if len(d) > 80 else d
            L.append(f"- **[{x['full_name']}]({x['html_url']})** \u00b7 \u2605 {x.get('stars', 0)} "
                     f"\u00b7 _{x.get('category', '')}_" + (f" \u2014 {d}" if d else ""))

    if builders:
        L.append("\n## \U0001F3C6 Top builders\n")
        L.append("| # | Owner | Projects | \u2605 total | Active | Focus |")
        L.append("|--:|---|--:|--:|--:|---|")
        for i, b in enumerate(builders[:6], 1):
            focus = " \u00b7 ".join((b.get("top_categories") or [])[:2])
            L.append(f"| {i} | [{b['owner']}]({b['html_url']}) | {b.get('project_count', 0)} | "
                     f"{k(b.get('total_stars', 0))} | {b.get('active_projects_30d', 0)} | {focus} |")

    cats = {}
    for x in p:
        cats[x.get("category", "Other")] = cats.get(x.get("category", "Other"), 0) + 1
    if cats:
        mx = max(cats.values())
        L.append("\n## \U0001F5C2 By category\n")
        for name, v in sorted(cats.items(), key=lambda t: -t[1]):
            L.append(f"`{name:<22}` {bar(v, mx)} **{v}**  ")

    tiers = {}
    for x in p:
        t = x.get("evidence_tier")
        if t:
            tiers[t] = tiers.get(t, 0) + 1
    if tiers:
        order = ["L3_EXPLICIT_BCI", "L2_NEURAL_SIGNAL", "L1_CONTEXT_PLUS_NEURO", "L0_WEAK_ADJACENT"]
        lab = {"L3_EXPLICIT_BCI": "L3 explicit BCI", "L2_NEURAL_SIGNAL": "L2 neural signal",
               "L1_CONTEXT_PLUS_NEURO": "L1 context+keyword", "L0_WEAK_ADJACENT": "L0 weak (review)"}
        L.append("\n## \U0001F52C Evidence\n")
        L.append(" \u00b7 ".join(f"**{lab[t]}** {tiers[t]}" for t in order if t in tiers))

    L.append("\n---")
    L.append(f"*An [AxonOS](https://axonos.org) community project \u00b7 "
             f"[methodology](https://github.com/{repo}/blob/main/docs/METHODOLOGY.md) \u00b7 "
             "auto-generated every 6 hours \u2014 do not edit by hand.*")
    return "\n".join(L)


def find_issue():
    try:
        issues = _api("GET", f"/repos/{REPO}/issues?state=open&per_page=100")
    except Exception:  # noqa: BLE001
        return None
    for it in issues:
        if "pull_request" in it:
            continue
        if MARKER in (it.get("body") or ""):
            return it
    return None


def main():
    if not TOKEN or not REPO:
        print("publish_stats_issue: missing GITHUB_TOKEN / GITHUB_REPOSITORY")
        return 0
    try:
        radar = json.load(open("data/radar.json", encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print("publish_stats_issue: cannot read radar.json:", e)
        return 0
    try:
        history = json.load(open("data/history.json", encoding="utf-8"))
    except Exception:  # noqa: BLE001
        history = {"snapshots": []}

    body = build_body(radar, history, REPO)
    existing = find_issue()
    if existing:
        if (existing.get("body") or "").strip() == body.strip():
            print("publish_stats_issue: no change, issue", existing["number"])
            return 0
        _api("PATCH", f"/repos/{REPO}/issues/{existing['number']}", {"title": TITLE, "body": body})
        print("publish_stats_issue: updated issue", existing["number"])
    else:
        try:
            created = _api("POST", f"/repos/{REPO}/issues",
                           {"title": TITLE, "body": body, "labels": ["radar-stats"]})
        except urllib.error.HTTPError:
            created = _api("POST", f"/repos/{REPO}/issues", {"title": TITLE, "body": body})
        print("publish_stats_issue: created issue", created.get("number"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
