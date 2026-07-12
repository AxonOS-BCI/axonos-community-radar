# AxonOS Radar — Roadmap

The public plan. This mirrors the GitHub Project board
([Roadmap](https://github.com/users/AxonOS-BCI/projects/1)); the board is the
live source of truth, this file is the readable summary. Inclusion of an item
here is intent, not a promise of date.

Every item carries an **Area** (`engine` · `ui` · `data` · `infra` · `docs`), a
**Priority**, and a **Target** milestone. Open work is tracked as issues with the
matching labels (see `.github/ISSUE_TEMPLATE/` and `scripts/setup_labels.sh`).

---

## Shipped — v7.0.0 · "The Relevance Engine"

- **BCI Relevance Engine** (`engine`) — scored, auditable inclusion via the BCI
  Relevance Score (BRS 0–100) with a signed evidence ledger; `neural`
  disambiguation by anchor. Generic ML is filtered out with a recorded reason.
- **Domain intelligence** (`engine`) — per-repo facets (modality / paradigm /
  signal-chain stage / standards), the modality × stage **coverage matrix**, and
  the **standards interoperability graph**.
- **Map tab** (`ui`) — coverage heatmap with desert callouts and a
  standards-graph view.

---

## Next — v7.1 · "Legible" (Area: ui, docs)

Small, high-value polish that makes what already exists obvious to a first-time
visitor.

- **Per-card BRS badge + "why included" ledger** (`ui`, high) — **shipped.** Each
  card carries its BCI Relevance Score; tapping it reveals the signed evidence
  ledger inline (every +/− signal with its reason) without leaving the card.
  Plus a **Relevance (BRS)** sort. This is the transparency differentiator, now
  visible. (Remaining under this milestone: map hover polish, a relevance-tier
  filter.)
- **Public Roadmap wiring** (`docs`, high) — this file, a Roadmap nav link on the
  site, a board link in the README, and structured issue templates so every
  request lands on the board already triaged.
- **Map polish** (`ui`, med) — legend, hover detail on coverage cells, and a
  one-line reading guide ("bright = crowded, empty = opening").
- **Tier filter** (`ui`, low) — filter the project grid by `relevance_tier`.

---

## v7.2 · "Dashboards" — rich per-project & ecosystem analytics (Area: ui, data)

The headline visual feature. The direction is the dense, dark, investor/audit-
grade dashboard style captured in two reference images kept in the repo:
[`docs/assets/dashboard-example-audit.jpg`](assets/dashboard-example-audit.jpg)
and
[`docs/assets/dashboard-example-gap-analysis.jpg`](assets/dashboard-example-gap-analysis.jpg)
— multi-panel, information-rich, one screen that answers a whole question. The
radar's version is built **from radar data** (not hand-entered), so it stays
live and honest.

**Per-project mini-dashboard** (on each card / a project detail view):

- **Stars sparkline** (`data`) — from `history.json` snapshots we already keep.
- **BRS-over-time** (`data`) — recompute BRS per historical snapshot and plot the
  trend; a rising BRS means a project is getting *more* BCI-focused.
- **52-week commit-activity strip** and **release cadence** (`data`) — from the
  enrichment we already fetch.
- **Facet chips** (`ui`) — modality / paradigm / signal-chain stage / standards,
  linked into the ecosystem views.

**Ecosystem dashboard** (a new tab or an upgraded Stats page), styled like the
examples:

- **Coverage heatmap** (have it) promoted into the dashboard grid.
- **Standards interoperability graph** (have it) as a proper node-link diagram,
  not just hubs — repos as nodes, shared standards as edges.
- **BRS distribution** histogram and **tier breakdown** — the shape of relevance
  across the field.
- **Category / language / momentum** panels — reach and recency at a glance.
- **Signal-chain completeness** bars per modality — where the ecosystem is thin.

**Delivery options to decide in the issue:**

1. *Interactive* — client-side charts (a tiny zero-dependency canvas/SVG layer,
   consistent with the radar's no-framework rule) rendered from `radar.json`.
   Live, responsive, no build step. Preferred for the site.
2. *Static PNG* — a `scripts/build_dashboard.py` (matplotlib) that renders a
   shareable dashboard image on each refresh, committed like `og-image.png`.
   Best for social cards, READMEs, and investor decks. Matches the example
   aesthetic exactly.

Likely: ship **both** — interactive on the site, a generated PNG for sharing.

> Note on scope: the example dashboards mix radar-derived data (repos, coverage,
> competitive landscape) with AxonOS-internal figures (valuation, revenue, FMEA,
> IEC 62304). The radar edition shows **only** what it can derive from public
> data and its own engine — no hand-entered business figures — so it never drifts
> from the truth it measures.

---

## v8.0 · "Open-core" — sustainability & premium signals (Area: infra, data)

Direction under discussion (see the open-core note in `docs/METHODOLOGY.md` /
project discussion). The public radar, its data, and its transparency stay free
and open. New, higher-effort **premium** value is built behind an API /
subscription without weakening the free tier:

- **Premium enrichment** (`data`) — curated funding / domicile / clinical signals.
- **Historical analytics & alerts** (`data`) — "new BCI repo", "BRS jump",
  custom watchlists, weekly ecosystem digests.
- **Dataset-as-a-service** (`infra`) — the engine's *output* (the live map) as a
  licensed feed for scouts, labs, and investors.

The engine's *increment* (valuable new signals) is what gets protected; the
published map and its evidence ledger stay open, because transparency is the
moat, not obscurity.

---

## How to propose something

Open a **Feature request** or **Bug report** issue (templates prefill Area /
Priority and auto-label). Triaged items land on the
[Roadmap board](https://github.com/users/AxonOS-BCI/projects/1).

`axonos.org · medium.com/@AxonOS · axonosorg@gmail.com`
