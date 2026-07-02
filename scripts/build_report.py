#!/usr/bin/env python3
"""Build report.html — a comprehensive, professional "State of Open BCI" report
generated from the radar data and committed straight into the repo, so
https://axonos-bci.github.io/axonos-community-radar/report.html is always a
one-click, exhaustive snapshot of the field.

Design goal: the density and polish of a Visual-Capitalist infographic plus a
Gartner-style quadrant. Implementation is deliberately boring and bulletproof:
a single static HTML file, zero JavaScript, all styling in assets/report.css,
every chart pre-rendered as inline SVG using presentation attributes only — so
it renders identically everywhere and cannot break under the strict CSP.

Honest by construction: every figure is a real public-GitHub signal; the same
scoring formula ranks every project including AxonOS; nothing is fabricated,
boosted, or invented from data we do not have.
"""
from __future__ import annotations

import html
import json
import math
import os
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "AxonOS-BCI/axonos-community-radar")


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def k(n):
    n = n or 0
    return (f"{n / 1000:.1f}k".replace(".0k", "k")) if n >= 1000 else str(n)


def pages_url():
    owner, _, name = REPO.partition("/")
    return f"https://{owner.lower()}.github.io/{name}/"


# --------------------------------------------------------------------------- #
# charts
# --------------------------------------------------------------------------- #
def quadrant_svg(projects, cidx):
    """Reach x engagement map. Real-pixel viewBox (760x480) so labels stay a
    consistent, legible size at any width instead of scaling with the container."""
    items = [x for x in projects if (x.get("stars") or 0) > 0]
    if len(items) < 4:
        return ""
    items = sorted(items, key=lambda x: -(x.get("_score") or 0))[:14]
    reach = [math.log10((x.get("stars") or 0) + 1) for x in items]
    eng = [(x.get("forks") or 0) / (x.get("stars") or 1) for x in items]
    rmin, rmax, emin, emax = min(reach), max(reach), min(eng), max(eng)

    def nrm(v, lo, hi):
        return 0.5 if hi - lo < 1e-9 else min(0.93, max(0.07, (v - lo) / (hi - lo)))

    W, H = 760.0, 480.0
    X0, X1, Y0, Y1 = 120.0, 724.0, 42.0, 392.0
    mx, my = (X0 + X1) / 2, (Y0 + Y1) / 2
    s = [f'<svg class="quad" viewBox="0 0 {W:.0f} {H:.0f}" role="img" '
         'aria-label="Reach versus engagement quadrant of open BCI projects">']
    s.append(f'<rect class="q-bg-1" x="{mx:.1f}" y="{Y0:.1f}" width="{X1-mx:.1f}" height="{my-Y0:.1f}"/>')
    s.append(f'<rect class="q-bg-2" x="{X0:.1f}" y="{Y0:.1f}" width="{mx-X0:.1f}" height="{my-Y0:.1f}"/>')
    s.append(f'<rect class="q-bg-3" x="{X0:.1f}" y="{my:.1f}" width="{mx-X0:.1f}" height="{Y1-my:.1f}"/>')
    s.append(f'<rect class="q-bg-4" x="{mx:.1f}" y="{my:.1f}" width="{X1-mx:.1f}" height="{Y1-my:.1f}"/>')
    for f in (0.25, 0.5, 0.75):
        gx = X0 + (X1 - X0) * f
        gy = Y0 + (Y1 - Y0) * f
        s.append(f'<line class="q-grid" x1="{gx:.1f}" y1="{Y0:.1f}" x2="{gx:.1f}" y2="{Y1:.1f}"/>')
        s.append(f'<line class="q-grid" x1="{X0:.1f}" y1="{gy:.1f}" x2="{X1:.1f}" y2="{gy:.1f}"/>')
    s.append(f'<rect class="q-frame" x="{X0:.1f}" y="{Y0:.1f}" width="{X1-X0:.1f}" height="{Y1-Y0:.1f}"/>')
    s.append(f'<line class="q-axis" x1="{mx:.1f}" y1="{Y0:.1f}" x2="{mx:.1f}" y2="{Y1:.1f}"/>')
    s.append(f'<line class="q-axis" x1="{X0:.1f}" y1="{my:.1f}" x2="{X1:.1f}" y2="{my:.1f}"/>')
    s.append(f'<text class="q-qlabel" x="{X1-10:.1f}" y="{Y0+20:.1f}" text-anchor="end">Pillars</text>')
    s.append(f'<text class="q-qlabel" x="{X0+10:.1f}" y="{Y0+20:.1f}">Widely watched</text>')
    s.append(f'<text class="q-qlabel" x="{X0+10:.1f}" y="{Y1-12:.1f}">Emerging</text>')
    s.append(f'<text class="q-qlabel" x="{X1-10:.1f}" y="{Y1-12:.1f}" text-anchor="end">Dev favourites</text>')
    s.append(f'<text class="q-axtitle" x="{mx:.1f}" y="{H-16:.1f}" text-anchor="middle">'
             'Engagement \u2014 forks per star \u2192</text>')
    s.append(f'<text class="q-axtitle" x="28" y="{my:.1f}" text-anchor="middle" '
             f'transform="rotate(-90 28 {my:.1f})">Reach \u2014 stars, log \u2192</text>')
    # Draw every dot; place labels greedily (highest score first) and skip any
    # label that cannot sit clear of those already placed, so nothing overlaps.
    placed = []  # (x0, x1, y) bounding boxes of labels already drawn
    for x, rv, ev in zip(items, reach, eng):
        px = X0 + nrm(ev, emin, emax) * (X1 - X0)
        py = Y1 - nrm(rv, rmin, rmax) * (Y1 - Y0)
        rad = 5.0 + math.log10((x.get("stars") or 0) + 1) * 2.3
        s.append(f'<circle class="q-dot qc-{cidx(x.get("category"))}" cx="{px:.1f}" '
                 f'cy="{py:.1f}" r="{rad:.1f}"/>')
        lab = esc((x.get("repo") or x.get("full_name") or "?")[:18])
        right = px <= mx  # label to the right for left-half dots, else to the left
        anchor = "start" if right else "end"
        tx = px + (rad + 7) if right else px - (rad + 7)
        est_w = len(lab) * 7.1 + 6.0
        x0 = tx if right else tx - est_w
        x1 = tx + est_w if right else tx
        for dy in (4.5, 15.0, -8.0, 25.0, -18.0):  # try baseline, then nudge
            ty = py + dy
            if ty < Y0 + 11 or ty > Y1 - 4:
                continue
            clash = any(abs(ty - py2) < 12 and not (x1 < bx0 or x0 > bx1)
                        for bx0, bx1, py2 in placed)
            if not clash:
                placed.append((x0, x1, ty))
                s.append(f'<text class="q-lab" x="{tx:.1f}" y="{ty:.1f}" '
                         f'text-anchor="{anchor}">{lab}</text>')
                break
    s.append("</svg>")
    return "".join(s)


def donut_svg(cats_sorted, cidx, total):
    """Category donut. Real-pixel viewBox (200x200) so the centre label renders
    at its literal size."""
    cx = cy = 100.0
    R = 92.0
    ang = -math.pi / 2
    s = ['<svg class="donut" viewBox="0 0 200 200" role="img" aria-label="Projects by category">']
    for name, cnt in cats_sorted:
        frac = cnt / total if total else 0
        a1 = ang + frac * 2 * math.pi
        x0, y0 = cx + R * math.cos(ang), cy + R * math.sin(ang)
        x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        large = 1 if (a1 - ang) > math.pi else 0
        s.append(f'<path class="qc-{cidx(name)}" d="M{cx:.1f} {cy:.1f} L{x0:.2f} {y0:.2f} '
                 f'A{R:.1f} {R:.1f} 0 {large} 1 {x1:.2f} {y1:.2f} Z"/>')
        ang = a1
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R*0.62:.1f}" fill="#0e141d"/>')
    s.append(f'<text class="donut-mid-n" x="{cx:.1f}" y="{cy-3:.1f}">{total}</text>')
    s.append(f'<text class="donut-mid-l" x="{cx:.1f}" y="{cy+20:.1f}">PROJECTS</text>')
    s.append("</svg>")
    return "".join(s)


def bars_svg(items, violet=False):
    """Horizontal bars rendered as HTML+CSS: text is normal HTML (crisp and a
    consistent size everywhere), and bar length uses pre-defined width classes so
    no inline styles are needed (strict-CSP safe). Replaces the old tiny-viewBox
    SVG bars whose labels scaled with the container and collided."""
    if not items:
        return ""
    mx = max(v for _, v in items) or 1
    vv = " v" if violet else ""
    rows = []
    for label, v in items:
        pct = int(round((v / mx) * 100))
        rows.append(
            f'<div class="lb-row"><span class="lb-lab">{esc(str(label))}</span>'
            f'<span class="lb-bar"><i class="lb-fill{vv} w{pct}"></i></span>'
            f'<span class="lb-val">{k(v)}</span></div>')
    return '<div class="lb">' + "".join(rows) + "</div>"


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #
def leaderboard_svg(items, violet=False):
    return bars_svg(items, violet)  # HTML bars \u2014 see bars_svg


def sparkline_svg(values, w=40.0, h=11.0):
    vals = [int(v or 0) for v in (values or [])]
    if len(vals) < 2:
        return ""
    mx = max(vals) or 1
    n = len(vals)
    pts = " ".join(f"{i/(n-1)*w:.1f},{h-(v/mx)*(h-1.5)-0.75:.1f}" for i, v in enumerate(vals))
    return (f'<svg class="spark" viewBox="0 0 {w:.0f} {h:.0f}" preserveAspectRatio="none" '
            f'role="img" aria-label="activity"><polyline class="spark-l" points="{pts}"/></svg>')


def build(radar):
    p = radar.get("projects", [])
    c = radar.get("counts", {})
    builders = radar.get("builders", [])
    enriched_any = any(x.get("enriched") for x in p)
    tot_downloads = sum(int(x.get("total_downloads") or 0) for x in p)
    tot_contrib = sum(int(x.get("contributors") or 0) for x in p)
    tot_releases = sum(int(x.get("releases_count") or 0) for x in p)
    funded = [x for x in p if x.get("funding_platforms")]
    curated = [x for x in p if x.get("data_source") == "curated+github"]
    base = pages_url()
    now = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    tot = c.get("total", len(p))
    stars = sum(int(x.get("stars") or 0) for x in p)
    forks = sum(int(x.get("forks") or 0) for x in p)
    active = c.get("active_30d", sum(1 for x in p if x.get("active")))
    new = c.get("new", sum(1 for x in p if x.get("is_new")))
    rising = c.get("rising", sum(1 for x in p if x.get("rising")))
    big = sum(1 for x in p if (x.get("stars") or 0) >= 1000)
    nbuild = len(builders) or c.get("builders", 0)

    cat_counts = {}
    cat_stars = {}
    for x in p:
        cat = x.get("category", "Other")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        cat_stars[cat] = cat_stars.get(cat, 0) + int(x.get("stars") or 0)
    cats_sorted = sorted(cat_counts.items(), key=lambda t: -t[1])
    cat_index = {name: i for i, (name, _) in enumerate(cats_sorted)}

    def cidx(cat):
        return cat_index.get(cat, len(cats_sorted)) % 10

    langs = {}
    for x in p:
        lg = x.get("language")
        if lg:
            langs[lg] = langs.get(lg, 0) + 1
    langs_top = sorted(langs.items(), key=lambda t: -t[1])[:8]

    tier_order = [("L3_EXPLICIT_BCI", "L3 explicit BCI"), ("L2_NEURAL_SIGNAL", "L2 neural signal"),
                  ("L1_CONTEXT_PLUS_NEURO", "L1 context + keyword"), ("L0_WEAK_ADJACENT", "L0 weak (review)")]
    tcount = {}
    for x in p:
        t = x.get("evidence_tier")
        if t:
            tcount[t] = tcount.get(t, 0) + 1
    tier_bars = [(lab, tcount[t]) for t, lab in tier_order if t in tcount]

    sbd = {"10k+": 0, "1k\u201310k": 0, "100\u20131k": 0, "10\u2013100": 0, "< 10": 0}
    for x in p:
        st = x.get("stars") or 0
        key = ("10k+" if st >= 10000 else "1k\u201310k" if st >= 1000 else
               "100\u20131k" if st >= 100 else "10\u2013100" if st >= 10 else "< 10")
        sbd[key] += 1
    star_bars = [(k_, sbd[k_]) for k_ in ("10k+", "1k\u201310k", "100\u20131k", "10\u2013100", "< 10") if sbd[k_]]

    rcd = {"active < 30d": 0, "30\u201390d": 0, "90d\u20131y": 0, "> 1y": 0}
    for x in p:
        d = x.get("days_since_push")
        if d is None:
            continue
        key = ("active < 30d" if d < 30 else "30\u201390d" if d < 90 else
               "90d\u20131y" if d < 365 else "> 1y")
        rcd[key] += 1
    rec_bars = [(k_, rcd[k_]) for k_ in ("active < 30d", "30\u201390d", "90d\u20131y", "> 1y") if rcd[k_]]

    H = []
    A = H.append
    A('<!doctype html><html lang="en"><head>')
    A('<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">')
    A('<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; '
      "img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'none'; form-action 'none'\">")
    A("<title>The State of Open BCI \u2014 AxonOS Radar</title>")
    A('<meta name="description" content="An automatically-generated, exhaustive snapshot of the '
      'open brain\u2013computer-interface field, refreshed every three hours from public GitHub signals.">')
    A('<link rel="stylesheet" href="assets/report.css">')
    A("</head><body>")

    A('<div class="topbar"><span class="dot"></span><b>AxonOS Radar</b><span class="sp"></span>')
    A(f'<a href="{base}">\u2039 Live map</a>&nbsp;&nbsp;'
      f'<a href="{base}stats.html">Dashboard</a>&nbsp;&nbsp;'
      f'<a href="https://github.com/{REPO}">GitHub</a></div>')

    A('<div class="wrap">')

    # hero
    A('<header class="hero"><div class="eyebrow">AxonOS Radar \u00b7 Field Report</div>')
    A('<h1>The State of<br><span class="grad">Open BCI.</span></h1>')
    A('<p class="lede">An exhaustive, automatically-compiled snapshot of every open-source project, '
      'tool and team building brain\u2013computer interfaces in public \u2014 discovered, relevance-filtered '
      'and ranked from public GitHub signals.</p>')
    A(f'<div class="meta"><span>Updated <b>{now}</b></span><i>\u00b7</i><span>Refreshed every 3 hours</span>'
      f'<i>\u00b7</i><span>{tot} resources tracked</span><i>\u00b7</i><span>Inclusion \u2260 endorsement</span></div>')
    A("</header>")

    # KPI band
    kpis = [("Projects", tot, True), ("Total stars", k(stars), False), ("\u2265 1k stars", big, False),
            ("Active (30d)", active, False)]
    if enriched_any:
        kpis += [("Downloads", k(tot_downloads), True), ("Contributors", k(tot_contrib), False),
                 ("Releases", k(tot_releases), False), ("Funded", len(funded), False)]
    kpis += [("New this week", new, False), ("\U0001F525 Rising", rising, False),
             ("Builders", nbuild, False), ("Languages", len(langs), False)]
    A('<div class="kpis">')
    for label, val, acc in kpis:
        A(f'<div class="kpi"><div class="n{" accent" if acc else ""}">{val}</div>'
          f'<div class="l">{label}</div></div>')
    A("</div>")

    # quadrant
    quad = quadrant_svg(p, cidx)
    if quad:
        A('<section id="quadrant"><div class="sec-head"><div class="sec-k">Positioning \u00b7 Gartner-style</div>')
        A("<h2>Reach \u00d7 Engagement quadrant</h2>")
        A("<p>The most relevant projects the radar surfaces, placed by two raw GitHub signals. The "
          "vertical axis is <b>reach</b> (stars, log scale); the horizontal axis is <b>engagement</b> "
          "\u2014 forks per star, i.e. how much the community builds on a project rather than just "
          "watching it.</p></div>")
        A(f'<div class="card quad-wrap">{quad}')
        A('<p class="q-note">Colour encodes category. Positions are relative to the projects shown. '
          "This is a descriptive ecosystem map from public signals \u2014 not a quality, vision, or "
          "clinical ranking.</p></div></section>")

    # category + evidence
    A('<section id="mix"><div class="grid2">')
    A('<div class="card"><div class="sec-head"><div class="sec-k">Composition</div>'
      "<h2>Ecosystem by category</h2></div>")
    A('<div class="donut-row">')
    A(donut_svg(cats_sorted, cidx, tot))
    A('<div class="legend">')
    for name, cnt in cats_sorted:
        A(f'<div class="leg"><span class="sw lg-{cidx(name)}"></span><span class="nm">{esc(name)}</span>'
          f'<span class="ct">{cnt} \u00b7 {k(cat_stars.get(name, 0))}\u2605</span></div>')
    A("</div></div></div>")
    A('<div class="card"><div class="sec-head"><div class="sec-k">Rigor</div>'
      "<h2>Evidence tiers</h2></div>")
    A(bars_svg(tier_bars, violet=True))
    A('<p class="q-note">How strongly each repo signals a genuine BCI focus, from an '
      "explicit statement (L3) down to weak adjacency held for review (L0).</p>")
    A("</div></div></section>")

    # languages
    if langs_top:
        A('<section id="languages"><div class="sec-head"><div class="sec-k">Tooling</div>'
          "<h2>Languages of the field</h2>"
          "<p>What open BCI is actually written in \u2014 by number of tracked projects.</p></div>")
        A(f'<div class="card">{bars_svg(langs_top)}</div></section>')

    # distribution (stars concentration + recency) \u2014 more signal, same solid HTML bars
    A('<section id="dist"><div class="sec-head"><div class="sec-k">Distribution</div>'
      "<h2>How the field is spread</h2>"
      "<p>Two lenses on the tracked projects \u2014 how star reach concentrates, and how "
      'recently each project was last pushed.</p></div><div class="grid2">')
    A('<div class="card"><div class="sec-head"><div class="sec-k">By reach</div>'
      "<h2>Projects per star band</h2></div>")
    A(bars_svg(star_bars))
    A('</div><div class="card"><div class="sec-head"><div class="sec-k">By activity</div>'
      "<h2>Last-push recency</h2></div>")
    A(bars_svg(rec_bars, violet=True))
    A("</div></section>")

    # rising + new
    ris = sorted([x for x in p if x.get("rising")], key=lambda x: -(x.get("stars_delta_7d") or 0))[:8]
    if ris:
        A('<section id="rising"><div class="sec-head"><div class="sec-k">Momentum</div>'
          "<h2>Rising \u2014 biggest 7-day movers</h2></div>")
        A('<div class="tbl-scroll"><table><thead><tr><th>#</th><th>Project</th>'
          '<th class="num">7-day</th><th class="num">Stars</th><th>Category</th></tr></thead><tbody>')
        for i, x in enumerate(ris, 1):
            A(f'<tr><td class="num">{i}</td><td><a class="proj" href="{esc(x.get("html_url"))}">'
              f'{esc(x.get("full_name"))}</a></td><td class="num rise">+{x.get("stars_delta_7d", 0)}</td>'
              f'<td class="num">{k(x.get("stars", 0))}</td><td>{esc(x.get("category"))}</td></tr>')
        A("</tbody></table></div></section>")

    # builders
    if builders:
        A('<section id="builders"><div class="sec-head"><div class="sec-k">People</div>'
          "<h2>Top builders</h2><p>Owners and organisations shipping the most in the open.</p></div>")
        A('<div class="tbl-scroll"><table><thead><tr><th>#</th><th>Owner</th><th class="num">Projects</th>'
          '<th class="num">Stars</th><th class="num">Active</th><th>Focus</th></tr></thead><tbody>')
        for i, b in enumerate(builders[:10], 1):
            focus = " \u00b7 ".join((b.get("top_categories") or [])[:2])
            A(f'<tr><td class="num">{i}</td><td><a class="proj" href="{esc(b.get("html_url"))}">'
              f'{esc(b.get("owner"))}</a></td><td class="num">{b.get("project_count", 0)}</td>'
              f'<td class="num">{k(b.get("total_stars", 0))}</td>'
              f'<td class="num">{b.get("active_projects_30d", 0)}</td><td>{esc(focus)}</td></tr>')
        A("</tbody></table></div></section>")

    # full table
    allp = sorted(p, key=lambda x: -(x.get("_score") or 0))
    # adoption / teams / funding
    top_stars = sorted([x for x in p if x.get("stars")], key=lambda x: -(x.get("stars") or 0))[:8]
    top_forks = sorted([x for x in p if x.get("forks")], key=lambda x: -(x.get("forks") or 0))[:8]

    def _nm(x):
        return x.get("repo") or (x.get("full_name") or "?").split("/")[-1]

    A('<section id="adoption"><div class="sec-head"><div class="sec-k">Reach &amp; adoption</div>'
      "<h2>Who leads the field</h2><p>Leaderboards from real public signals. Stars and engagement are "
      "always available; downloads, teams and funding are fetched per repository during enrichment.</p></div>")
    A('<div class="grid2">')
    A('<div class="card"><div class="sec-head"><div class="sec-k">Reach</div><h2>Most starred</h2></div>')
    A(leaderboard_svg([(_nm(x), x.get("stars") or 0) for x in top_stars]))
    A('</div><div class="card"><div class="sec-head"><div class="sec-k">Engagement</div>'
      "<h2>Most built-on (forks)</h2></div>")
    A(leaderboard_svg([(_nm(x), x.get("forks") or 0) for x in top_forks], violet=True))
    A("</div></div>")
    if enriched_any:
        top_dl = sorted([x for x in p if x.get("total_downloads")],
                        key=lambda x: -(x.get("total_downloads") or 0))[:8]
        top_team = sorted([x for x in p if x.get("contributors")],
                          key=lambda x: -(x.get("contributors") or 0))[:8]
        A('<div class="grid2">')
        A('<div class="card"><div class="sec-head"><div class="sec-k">Adoption</div>'
          "<h2>Most downloaded</h2><p>Total release-asset downloads.</p></div>")
        A(leaderboard_svg([(_nm(x), x.get("total_downloads") or 0) for x in top_dl])
          or '<p class="q-note">No release downloads recorded yet.</p>')
        A('</div><div class="card"><div class="sec-head"><div class="sec-k">People</div>'
          "<h2>Largest teams</h2><p>Distinct contributors.</p></div>")
        A(leaderboard_svg([(_nm(x), x.get("contributors") or 0) for x in top_team], violet=True))
        A("</div></div>")
        if funded:
            from collections import Counter
            plat = Counter()
            for x in funded:
                for pl in x.get("funding_platforms") or []:
                    plat[pl] += 1
            chips = ", ".join(f"{pl.replace('_', ' ')} ({c})" for pl, c in plat.most_common())
            A('<div class="card"><div class="sec-head"><div class="sec-k">Funding</div>'
              "<h2>Funding channels</h2></div>")
            A(f"<p>{len(funded)} of {tot} projects expose a funding channel \u2014 by platform: {chips}.</p>")
            paid = [x for x in curated if x.get("funding_raised_usd")]
            if paid:
                rows = " \u00b7 ".join(
                    f'{esc(x.get("full_name"))} (${k(int(x.get("funding_raised_usd")))}'
                    + (f', {esc(x.get("org_domicile"))}' if x.get("org_domicile") else "") + ")"
                    for x in paid)
                A(f'<p class="q-note">Capital raised / domicile (hand-curated, source-cited): {rows}.</p>')
            A("</div>")
    else:
        A('<div class="card"><p class="q-note"><b>Teams, downloads and funding</b> populate on the first '
          "enriched scan: the pipeline fetches real contributor counts, release-asset download totals, "
          "52-week commit activity and declared FUNDING.yml channels for every project. GitHub exposes "
          "repository page views only to a repo\u2019s own owners, so views are deliberately never "
          "shown rather than approximated.</p></div>")
    A("</section>")

    tpill = {"L3_EXPLICIT_BCI": ("t3", "L3"), "L2_NEURAL_SIGNAL": ("t2", "L2"),
             "L1_CONTEXT_PLUS_NEURO": ("t1", "L1"), "L0_WEAK_ADJACENT": ("t0", "L0")}
    A('<section id="all"><div class="sec-head"><div class="sec-k">Full field</div>'
      f"<h2>All {len(allp)} tracked resources</h2>"
      "<p>Every project on the radar, ranked by discovery score. One table, the whole field \u2014 the "
      "one-click, exhaustive answer.</p></div>")
    enr_head = ('<th class="num">Team</th><th class="num">Downloads</th>'
                '<th class="num">Rel.</th><th class="num">Activity</th>') if enriched_any else ""
    A('<div class="tbl-scroll"><table><thead><tr><th>#</th><th>Project</th><th>Category</th>'
      '<th class="num">Stars</th><th class="num">Forks</th>' + enr_head +
      '<th>Language</th><th>Evidence</th><th class="num">Active</th></tr></thead><tbody>')
    for i, x in enumerate(allp, 1):
        pc, pl = tpill.get(x.get("evidence_tier"), ("", "\u2014"))
        live = '<span class="dotlive">\u25cf</span>' if x.get("active") else '<span class="dotstale">\u25cb</span>'
        desc = (x.get("description") or "").strip()
        desc = (desc[:60] + "\u2026") if len(desc) > 60 else desc
        team = k(x["contributors"]) if x.get("contributors") is not None else "\u2014"
        dls = k(x["total_downloads"]) if x.get("total_downloads") else "\u2014"
        rels = str(x["releases_count"]) if x.get("releases_count") else "\u2014"
        spark = sparkline_svg(x.get("activity_spark")) or "\u2014"
        cur = ""
        if x.get("data_source") == "curated+github" and x.get("funding_raised_usd"):
            dom = f' \u00b7 {esc(x.get("org_domicile"))}' if x.get("org_domicile") else ""
            cur = f'<span class="cur">\U0001F4B0 ${k(int(x["funding_raised_usd"]))}{dom}</span>'
        A(f'<tr><td class="num">{i}</td><td><a class="proj" href="{esc(x.get("html_url"))}">'
          f'{esc(x.get("full_name"))}</a>{cur}'
          + (f'<br><span class="desc">{esc(desc)}</span>' if desc else "")
          + f'</td><td>{esc(x.get("category"))}</td><td class="num">{k(x.get("stars", 0))}</td>'
          f'<td class="num">{k(x.get("forks", 0))}</td>'
          + ((f'<td class="num">{team}</td><td class="num">{dls}</td>'
              f'<td class="num">{rels}</td><td class="num">{spark}</td>') if enriched_any else "")
          + f'<td>{esc(x.get("language") or "\u2014")}</td>'
          f'<td><span class="pill {pc}">{pl}</span></td><td class="num">{live}</td></tr>')
    A("</tbody></table></div></section>")

    # methodology
    A('<section id="method"><div class="sec-head"><div class="sec-k">How this is made</div>'
      "<h2>Methodology &amp; honesty</h2></div>")
    A('<div class="method">')
    A("<p><b>Discovery.</b> A zero-dependency Python pipeline queries the public GitHub API across a "
      "curated set of neurotech topics and keywords, de-duplicates, and relevance-filters every "
      "candidate before it appears here.</p>")
    A("<p><b>Evidence tiers.</b> Each repository is graded L3\u2013L0 by how strongly it signals a genuine "
      "BCI focus, with weak or adjacent matches flagged for review rather than hidden.</p>")
    A("<p><b>Scoring.</b> A single published multi-signal formula \u2014 log-scaled stars and recency, "
      "plus enriched terms for release downloads, contributors and commit activity \u2014 applied "
      "identically to every project. AxonOS is ranked like everyone else and is never boosted.</p>")
    A("<p><b>Enriched signals.</b> Per repository the pipeline additionally fetches real GitHub data: "
      "contributor counts (team size), release-asset download totals (adoption), a 52-week commit-activity "
      "histogram (maintenance) and declared funding channels (FUNDING.yml). GitHub exposes repository page "
      "views only to a repo\u2019s own owners, so views are deliberately not shown rather than approximated.</p>")
    A("<p><b>Money &amp; domicile.</b> Capital raised and legal domicile are not in GitHub; when shown they "
      "come only from a hand-curated, source-cited overrides file and are labelled as such. Nothing is estimated.</p>")
    A("<p><b>The quadrant.</b> Axes are raw GitHub metrics (stars; forks per star), min-max normalised "
      "across the projects shown. It is a descriptive map, not a vision or quality judgement.</p>")
    A("<p><b>Refresh.</b> The whole field is re-scanned every three hours; the last good snapshot is kept "
      "if a scan partially fails, so the map never goes blank.</p>")
    A("<p><b>Honesty.</b> Every number here is a real public signal. Inclusion is discovery, not "
      "endorsement, and nothing is fabricated from data the pipeline does not actually collect.</p>")
    A("</div>")
    A('<div class="disclaimer">This report is a community discovery aid compiled from public GitHub '
      "metadata. Presence here does not imply endorsement, security, or clinical validation of any "
      "project. Figures are point-in-time signals and will change as the field moves.</div>")
    A("</section>")

    A(f'<footer><span>\u00a9 The AxonOS Project</span><a href="https://axonos.org">axonos.org</a>'
      f'<a href="https://medium.com/@AxonOS">medium.com/@AxonOS</a>'
      f'<a href="{base}">Live map</a><span>Generated {now} \u00b7 do not edit by hand</span></footer>')

    A("</div></body></html>")
    return "\n".join(H)


def main():
    try:
        radar = json.load(open("data/radar.json", encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print("build_report: cannot read radar.json:", e)
        return 0
    out = build(radar)
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(out)
    print(f"build_report: wrote report.html ({len(out)} bytes, {len(radar.get('projects', []))} projects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
