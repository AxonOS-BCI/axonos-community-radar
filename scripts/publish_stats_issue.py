#!/usr/bin/env python3
"""Publish/update ONE living GitHub issue with the radar's ecosystem statistics.

The issue is rendered as a Visual-Capitalist-style data report with a
Gartner-style quadrant. GitHub renders the embedded Mermaid ``quadrantChart``
and ``pie`` natively inside the issue, so the result reads like real analytics
rather than a wall of numbers.

Every figure comes from real public-GitHub signals. The quadrant axes are
honest and labelled as such (adoption = stars on a log scale; momentum =
recency, with recent star-growth folding in as velocity history accumulates).
We do NOT fabricate "vision", "execution", or "hype" scores from data we do
not have.

Zero runtime dependencies. The issue carries a hidden marker; this script finds
that one issue and edits it in place (or creates it the first time), so there is
always exactly one always-current "live dashboard" issue rather than a flood of
new issues. Runs after radar.py + publish_data.py in the scheduled workflow.

Posture: inclusion is not endorsement; figures are discovery signals, not
quality, safety, or clinical ratings; AxonOS is ranked like everyone else.
"""
from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")  # "owner/name"
MARKER = "<!-- axonos-radar-stats -->"
# The health monitor owns its own alert issue; the janitor must never close it.
HEALTH_MARKER = "<!-- axonos-radar-health-alert f3a91c2e -->"
TITLE = "\U0001F4E1 AxonOS Radar \u2014 The State of Open BCI"
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


def bar(v, mx, width=14):
    if mx <= 0:
        return ""
    return "\u2588" * (max(1, round(v / mx * width)) if v else 0)


def pages_url(repo):
    owner, _, name = repo.partition("/")
    return f"https://{owner.lower()}.github.io/{name}/"


def _mq_label(x):
    s = x.get("repo") or x.get("full_name") or "?"
    for ch in '"[]':
        s = s.replace(ch, "")
    return s[:22]


def _nrm(v, lo, hi):
    if hi - lo < 1e-9:
        return 0.5
    return min(0.97, max(0.03, (v - lo) / (hi - lo)))


def mermaid_quadrant(projects):
    """Gartner-style quadrant on REAL, raw GitHub axes that actually vary.

    Y = reach (log10 stars). X = engagement = forks-per-star, i.e. how much
    the community builds on a project versus simply watching it. Engagement is
    size-independent, so it gives genuine 2-D spread. Positions are relative to
    the projects shown; labels are descriptive, not a vision/quality judgement.
    (Star-velocity is not used while history is still accumulating, rather than
    fabricating a momentum axis that does not yet have data behind it.)
    """
    items = [x for x in projects if (x.get("stars") or 0) > 0]
    if len(items) < 4:
        return ""
    items = sorted(items, key=lambda x: -(x.get("_score") or 0))[:14]
    ys = [math.log10((x.get("stars") or 0) + 1) for x in items]
    xs = [(x.get("forks") or 0) / (x.get("stars") or 1) for x in items]
    ymin, ymax, xmin, xmax = min(ys), max(ys), min(xs), max(xs)
    out = ["```mermaid", "quadrantChart",
           "    title Reach vs Engagement - the open BCI field (public GitHub signals)",
           "    x-axis Watched --> Built upon",
           "    y-axis Niche --> Widely adopted",
           "    quadrant-1 Pillars",
           "    quadrant-2 Widely watched",
           "    quadrant-3 Emerging",
           "    quadrant-4 Developer favourites"]
    for x, ly, lx in zip(items, ys, xs):
        out.append(f'    "{_mq_label(x)}": [{_nrm(lx, xmin, xmax):.3f}, {_nrm(ly, ymin, ymax):.3f}]')
    out.append("```")
    return "\n".join(out)


def mermaid_pie(cats):
    if not cats:
        return ""
    out = ["```mermaid", "pie showData", "    title Projects by category"]
    for name, v in sorted(cats.items(), key=lambda t: -t[1]):
        out.append(f'    "{name.replace(chr(34), "")}" : {v}')
    out.append("```")
    return "\n".join(out)


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
    big = sum(1 for x in p if (x.get("stars") or 0) >= 1000)
    langs_n = len({x.get("language") for x in p if x.get("language")})

    snaps = sorted(history.get("snapshots", []), key=lambda s: s.get("snapshot_at", ""))
    delta = ""
    if len(snaps) >= 2:
        prev = snaps[-2].get("meta") or {}
        dp = tot - (prev.get("total") or tot)
        ds = stars - (prev.get("total_stars") or stars)
        if dp or ds:
            delta = f"_\u0394 since last refresh: {dp:+d} projects \u00b7 {ds:+d} \u2605_"

    L = [MARKER, f"# {TITLE}\n",
         "> A data snapshot of the open brain\u2013computer-interface field, compiled automatically "
         "from public GitHub metadata and refreshed every six hours. **Inclusion is not endorsement; "
         "every figure is a discovery signal, not a quality, safety, or clinical rating.** AxonOS is "
         "ranked by the same formula as every other project.\n",
         f"**Updated** {now} \u00b7 [\U0001F4C8 dashboard]({base}stats.html) \u00b7 [\U0001F5FA map]({base}) "
         f"\u00b7 [data]({base}data/radar.json)\n"]

    L += ["## The field at a glance\n",
          "| Projects | Total \u2605 | \u2265 1k \u2605 | Active 30d | New (7d) | \U0001F525 Rising | "
          "\U0001F3D7 Builders | Languages |",
          "|---:|---:|---:|---:|---:|---:|---:|---:|",
          f"| **{tot}** | **{k(stars)}** | {big} | {active} | {new} | {rising} | {nbuild} | {langs_n} |"]
    if delta:
        L.append("\n" + delta)

    # Ecosystem Health — surface the per-project maturity read-out in the bot's
    # own output. Numbers come straight from the signals block in radar.json.
    scored = [x for x in p if isinstance(x.get("signals"), dict)]
    if scored:
        hmed = c.get("health_median")
        if hmed is None:
            ov = sorted(x["signals"]["overall"] for x in scored)
            hmed = ov[len(ov) // 2]
        strong = c.get("health_strong", sum(1 for x in scored if x["signals"]["overall"] >= 80))
        top = sorted(scored, key=lambda x: -x["signals"]["overall"])[:5]
        L.append("\n## \U0001FA7A Ecosystem Health \u2014 maturity from public signals\n")
        L.append(f"_Median Health **{hmed}/100** across {len(scored)} projects \u00b7 **{strong}** in the "
                 f"strong band (\u2265 80). Computed only from real GitHub signals \u2014 maintenance, "
                 f"momentum, adoption, team, licence and doc signals. A triage read-out, **not** a "
                 f"quality, safety, or clinical rating; AxonOS is scored by the same rules as everyone._\n")
        L.append("| # | Project | Health | Maint | Mom | Adopt | Team |")
        L.append("|--:|---|--:|--:|--:|--:|--:|")
        _dash = "\u2014"
        for i, x in enumerate(top, 1):
            s = x["signals"]
            mm = s.get("maintenance", _dash)
            mo = s.get("momentum", _dash)
            ad = s.get("adoption", _dash)
            tm = s.get("team", _dash)
            L.append(f"| {i} | [{x['full_name']}]({x['html_url']}) | **{s['overall']}** | "
                     f"{mm} | {mo} | {ad} | {tm} |")

    mq = mermaid_quadrant(p)
    if mq:
        L.append("\n## \U0001F9ED Ecosystem quadrant \u2014 reach \u00d7 engagement\n")
        L.append(mq)
        L.append("\n_How to read it: the vertical axis is **reach** (stars, log scale); the horizontal axis "
                 "is **engagement** \u2014 forks per star, i.e. how much the community builds on a project "
                 "rather than just watching it. Both are raw public-GitHub metrics and positions are relative "
                 "to the projects shown \u2014 a descriptive ecosystem map, not a quality or vision ranking._")

    cats = {}
    for x in p:
        cats[x.get("category", "Other")] = cats.get(x.get("category", "Other"), 0) + 1
    pie = mermaid_pie(cats)
    if pie:
        L.append("\n## \U0001F5C2 Ecosystem by category\n")
        L.append(pie)

    ris = sorted([x for x in p if x.get("rising")], key=lambda x: -(x.get("stars_delta_7d") or 0))[:5]
    if ris:
        L.append("\n## \U0001F525 Rising \u2014 biggest 7-day movers\n")
        L.append("| # | Project | 7-day | \u2605 | Category |")
        L.append("|--:|---|--:|--:|---|")
        for i, x in enumerate(ris, 1):
            L.append(f"| {i} | [{x['full_name']}]({x['html_url']}) | +{x.get('stars_delta_7d', 0)} | "
                     f"{x.get('stars', 0)} | {x.get('category', '')} |")

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

    tiers = {}
    for x in p:
        t = x.get("evidence_tier")
        if t:
            tiers[t] = tiers.get(t, 0) + 1
    if tiers:
        order = ["L3_EXPLICIT_BCI", "L2_NEURAL_SIGNAL", "L1_CONTEXT_PLUS_NEURO", "L0_WEAK_ADJACENT"]
        lab = {"L3_EXPLICIT_BCI": "L3 explicit BCI", "L2_NEURAL_SIGNAL": "L2 neural signal",
               "L1_CONTEXT_PLUS_NEURO": "L1 context+keyword", "L0_WEAK_ADJACENT": "L0 weak (review)"}
        mx = max(tiers.values())
        L.append("\n## \U0001F52C Evidence tiers\n")
        for t in order:
            if t in tiers:
                L.append(f"`{lab[t]:<20}` {bar(tiers[t], mx)} **{tiers[t]}**  ")

    langs = {}
    for x in p:
        lg = x.get("language")
        if lg:
            langs[lg] = langs.get(lg, 0) + 1
    if langs:
        top = sorted(langs.items(), key=lambda t: -t[1])[:8]
        mx = top[0][1]
        L.append("\n## \U0001F4BB Languages\n")
        for name, v in top:
            L.append(f"`{name:<14}` {bar(v, mx)} **{v}**  ")

    L.append("\n---")
    L.append(f"*An [AxonOS](https://axonos.org) community project \u00b7 "
             f"[methodology](https://github.com/{repo}/blob/main/docs/METHODOLOGY.md) \u00b7 "
             "compiled automatically every 6 hours from public GitHub signals \u2014 do not edit by hand. "
             "Inclusion is discovery, not endorsement.*")
    return "\n".join(L)


def find_issue():
    """Find the living stats issue, or return "RETRY" if we could not look.

    The ONLY safe reason to create a new issue is a *successful* enumeration
    that found no marker. Any failure to enumerate must NOT fall through to
    "create", or a failed lookup spawns a duplicate living digest that then
    updates forever alongside the original. The previous version guarded only
    5xx and returned None on everything else — so a 403 (rate-limited or
    under-scoped token), a 401, or a network blip silently created a duplicate.
    403 is by far the likeliest failure here, which made the guard miss the
    common case.

    Also pages through all open issues (a marker past the first 100 would
    otherwise be missed and duplicated), and when several markers already exist
    adopts the OLDEST — so any duplicates converge instead of multiplying.
    """
    found = []
    page = 1
    while page <= 10:
        try:
            batch = _api("GET", f"/repos/{REPO}/issues?state=open&per_page=100&page={page}")
        except Exception:  # noqa: BLE001
            return "RETRY"          # never create on an unverified listing
        if not isinstance(batch, list):
            return "RETRY"
        for it in batch:
            if "pull_request" in it:
                continue
            author = ((it.get("user") or {}).get("login") or "")
            if author not in ("github-actions[bot]", "github-actions"):
                continue   # marker collision defense: only trust the Actions bot
            if MARKER in (it.get("body") or ""):
                found.append(it)
        if len(batch) < 100:
            break
        page += 1
    if not found:
        return None                  # listing complete and clean → safe to create
    return min(found, key=lambda it: it.get("number") or (1 << 30))



def _list_open_bot_issues():
    """Every open issue authored by the Actions bot, or "RETRY" if we could not
    enumerate. Same discipline as find_issue(): never act on an unverified list."""
    out, page = [], 1
    while page <= 10:
        try:
            batch = _api("GET", f"/repos/{REPO}/issues?state=open&per_page=100&page={page}")
        except Exception:  # noqa: BLE001
            return "RETRY"
        if not isinstance(batch, list):
            return "RETRY"
        for it in batch:
            if "pull_request" in it:
                continue
            author = ((it.get("user") or {}).get("login") or "")
            if author in ("github-actions[bot]", "github-actions"):
                out.append(it)
        if len(batch) < 100:
            break
        page += 1
    return out


def _close(number, why):
    """Close one issue with a reason. Never deletes — a closed issue keeps its
    history and can be reopened; deletion is irreversible and stays manual."""
    try:
        _api("POST", f"/repos/{REPO}/issues/{number}/comments", {"body": why})
        _api("PATCH", f"/repos/{REPO}/issues/{number}", {"state": "closed"})
        print(f"publish_stats_issue: closed #{number}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"publish_stats_issue: could not close #{number}: {e}")
        return False


def janitor(keep_number):
    """Keep exactly one living digest, and retire the bot's abandoned ones.

    Two kinds of litter accumulate on a repo whose digest is a living issue:
      1. duplicates of the current digest (a failed lookup once created a
         second one), and
      2. issues from an older digest format, orphaned when the marker changed —
         they can never be updated again, so they sit at the top of the Issues
         tab showing numbers from weeks ago, which is worse than showing none.

    Both get closed with an explanation and a pointer to the live one. Only the
    Actions bot's own issues are ever touched: a human's issue is never closed
    by a bot, and the health monitor's alert is left to the monitor.
    """
    issues = _list_open_bot_issues()
    if issues == "RETRY":
        print("publish_stats_issue: cannot enumerate issues; skipping cleanup")
        return
    closed = 0
    for it in issues:
        n = it.get("number")
        if n == keep_number:
            continue
        body = it.get("body") or ""
        title = it.get("title") or ""
        if HEALTH_MARKER in body:
            continue                      # the monitor owns its own alert
        if MARKER in body:
            closed += _close(n, f"Superseded — the live digest is #{keep_number}. "
                                f"Closing this duplicate so the radar keeps exactly one.")
        elif "axonos" in title.lower():
            closed += _close(n, f"Retired — this issue was published by an older digest "
                                f"format and can no longer be updated, so its numbers are "
                                f"frozen in the past. The live digest is #{keep_number}.")
    if closed:
        print(f"publish_stats_issue: retired {closed} stale bot issue(s)")


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
    if existing == "RETRY":
        print("publish_stats_issue: GitHub API unavailable; skipping to avoid duplicate issues")
        return 0
    if existing:
        if (existing.get("body") or "").strip() == body.strip():
            print("publish_stats_issue: no change, issue", existing["number"])
            janitor(existing["number"])
            return 0
        _api("PATCH", f"/repos/{REPO}/issues/{existing['number']}", {"title": TITLE, "body": body})
        print("publish_stats_issue: updated issue", existing["number"])
        janitor(existing["number"])
    else:
        try:
            created = _api("POST", f"/repos/{REPO}/issues",
                           {"title": TITLE, "body": body, "labels": ["radar-stats"]})
        except urllib.error.HTTPError:
            created = _api("POST", f"/repos/{REPO}/issues", {"title": TITLE, "body": body})
        print("publish_stats_issue: created issue", created.get("number"))
        if created.get("number"):
            janitor(created["number"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
