# AxonOS Radar — Roadmap

The public plan. This mirrors the GitHub Project board
([Roadmap](https://github.com/users/AxonOS-BCI/projects/1)); the board is the
live source of truth, this file is the readable summary. Inclusion of an item
here is intent, not a promise of date.

Every item carries an **Area** (`engine` · `ui` · `data` · `infra` · `docs`), a
**Priority**, and a **Target** milestone. Open work is tracked as issues with the
matching labels (see `.github/ISSUE_TEMPLATE/` and `scripts/setup_labels.sh`).

**Where we are — v8.1:** the map is scored, the evidence behind every call is
public, the engine is private, and the Stats page is a live dashboard.

---

## The arc — to v17

| Version | Theme | Status |
|:--:|:--|:--|
| **7.0** | The Relevance Engine | ✅ shipped |
| **7.1** | Legible | ✅ shipped |
| **7.2** | Dashboards (generated) | ✅ shipped |
| **8.0** | Open-core | ✅ shipped |
| **8.1** | Dashboards, live | ✅ shipped |
| **9.0** | Signals | next |
| **10.0** | Feed | planned |
| **11.0** | Trajectory | planned |
| **12.0** | Badges | planned |
| **13.0** | Talent | planned |
| **14.0** | Capital | planned |
| **15.0** | Standards | planned |
| **16.0** | Frontier | planned |
| **17.0** | The Atlas | the destination |

---

## Shipped — v7.0.0 · "The Relevance Engine"

- **BCI Relevance Engine** (`engine`) — scored, auditable inclusion via the BCI
  Relevance Score (BRS 0–100), built from a signed evidence ledger. Generic ML is
  dropped with a recorded reason, not silently.
- **Domain intelligence** (`engine`) — per-repo facets (modality / paradigm /
  signal-chain stage / standards), a coverage matrix, and a standards graph.
- **Map tab** (`ui`) — coverage heatmap with desert callouts and a
  standards-interoperability view.

## Shipped — v7.1.0 · "Legible"

- **Per-card BRS badge + "why included" ledger** (`ui`) — each card carries its
  score; tapping it unfolds the signed evidence ledger (every `+`/`−` signal with
  its plain-language reason). Keyboard-accessible.
- **Relevance (BRS) sort** (`ui`).
- **Public roadmap wiring** (`docs`) — this file, a Roadmap nav link on the site,
  issue templates with Area/Priority auto-labels, and a label taxonomy script.

## Shipped — v7.2 · "Dashboards" (generated)

- **BCI Ecosystem Intelligence dashboard** (`data`) — a dense, investor-grade
  one-pager rendered entirely from radar data: KPI strip, signal-chain coverage,
  BRS distribution, modality landscape, standards & interoperability, health
  bands, players (BRS × reach), momentum, composition, top builders. Embedded in
  the README; regenerated on a schedule by the private engine.
- **No hand-entered figures** — every panel is computed from public GitHub
  signals and the engine's own output, so the sheet cannot drift from the truth
  it reports.

## Shipped — v8.0 · "Open-core"

- **The scoring/discovery engine moved fully private** (`infra`) — relevance,
  domain, radar, enrich, signals, ecosystem, and the report/publish pipeline live
  only in the private engine repository. This showcase is the UI, the published
  dataset, and the open utilities.
- **Licensing is unambiguous** (`docs`) — MIT covers exactly what remains; the
  engine is proprietary and no longer sits inside an MIT tree.
- **Transparency is unchanged** (`data`) — the evidence ledger on every project,
  the interop vocabulary, the seed config, the schema, and every published
  dataset stay open. Transparency is the moat, not obscurity.
- **v8.0.1** — restored the showcase-side deploy utilities that the slimming had
  removed along with the engine, fixed a duplicate-alert path in the health
  monitor, and added a CI gate: workflows may only reference files that exist.

## Shipped — v8.1 · "Dashboards, live"

- **The Stats page is a live dashboard** (`ui`) — the engine's own output,
  rendered client-side from `radar.json`, zero dependencies:
  - **Signal-chain coverage** — modality × stage heatmap, with the empty cells
    (the field's openings) called out.
  - **Relevance distribution** — the BRS histogram, with the gate and the mean.
  - **Standards & interoperability** — which standards win, and how many projects
    are wired to each.
  - **Ecosystem health** — maturity bands and the median.
- **Deploy fixed** (`infra`) — the site now deploys the engine's published data on
  a clock. The open-core cutover had left Pages waiting on a workflow that no
  longer exists, so scans were published but never deployed.

---

## Next — v9.0 · "Signals" (Area: data, infra)

Turn the map into an instrument that tells *you* when something changes, instead
of asking you to come and look.

- **Watchlists** (`data`, high) — follow a modality, a standard, an owner, or a
  BRS band.
- **Alerts** (`data`, high) — "a new BCI repo appeared", "a project's BRS
  jumped", "a tracked project is cooling".
- **Weekly ecosystem digest** (`data`, med) — the living issue, delivered.
- **Feeds per slice** (`infra`, med) — an RSS/JSON feed per watchlist.

## v10.0 · "Feed" — dataset-as-a-service (Area: infra)

The engine's *output* — the live, scored map — as a licensed feed for scouts,
labs, and investors. The free map and its transparency stay free; this is the
higher-effort value built beside it, never a gate on the public tier.

## v11.0 · "Trajectory" — historical analytics (Area: data)

- **BRS-over-time** — recompute BRS per historical snapshot and plot the arc.
- **Stars sparkline** and a **52-week commit-activity strip** — from the snapshots
  and signals already kept.
- **Cohorts** — how projects that appeared together go on to fare.

## v12.0 · "Badges" — the due-diligence marker (Area: ui, infra)

- **Scored badge** — `AxonOS Radar · BRS 95 · Explicit BCI`, embeddable, live.
- **Verified badge** — a reviewed quality signal projects apply for.
- The two-sided flywheel: projects want the badge; investors read it as an
  independent, evidence-backed diligence signal.

## v13.0 "Talent" · v14.0 "Capital" · v15.0 "Standards"

The contributor and builder graph; funding and domicile signals; conformance
tracking (LSL / BIDS / NWB) and clinical-readiness posture.

## v16.0 "Frontier" · v17.0 "The Atlas"

Adjacent domains (neuromodulation, neuroprosthetics, spatial compute) — and then
the destination: the canonical, real-time intelligence platform for neurotech.

---

## How to influence this

Open a [Feature request](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new/choose)
or a [Bug report](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new/choose)
— the engine's reasoning is recorded, so mis-score corrections are fast. Items
with real demand move up.

<sub>© The AxonOS Project / Denis Yermakou · axonos.org · connect@axonos.org</sub>
