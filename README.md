<div align="center">

# AxonOS Radar

### The scored map of the open brain–computer-interface ecosystem

Every public BCI/neurotech repository on GitHub — **discovered, scored, and explained.**
Not a hand-curated list. A living, evidence-backed intelligence engine.

[![Live](https://img.shields.io/badge/live-axonos--bci.github.io-a78bfa?style=flat-square)](https://axonos-bci.github.io/axonos-community-radar/)
[![Roadmap](https://img.shields.io/badge/roadmap-to%20v17-f59e0b?style=flat-square)](https://github.com/users/AxonOS-BCI/projects/1)
[![Projects](https://img.shields.io/badge/tracked-120%2B%20projects-46d0e0?style=flat-square)](https://axonos-bci.github.io/axonos-community-radar/)
[![Data](https://img.shields.io/badge/data-open%20JSON%20API-34d399?style=flat-square)](https://axonos-bci.github.io/axonos-community-radar/data/radar.json)

**[Open the radar →](https://axonos-bci.github.io/axonos-community-radar/)**

</div>

---

## What this is

The BCI field is scattered across hundreds of GitHub repositories with no map. AxonOS
Radar is that map — but it doesn't just *list* projects, it **scores** them. A purpose-built
relevance engine reads every candidate, decides whether it's genuinely a brain–computer
interface project (not generic ML that happens to say "neural"), and shows you **exactly why**.
The result is the first honest, continuously-updated intelligence layer for neurotech software.

---

## The engine — what it does

| Capability | What it delivers |
|:--|:--|
| **BCI Relevance Score (BRS 0–100)** | Every repo is scored, not guessed. A gate at 40 keeps the field clean — generic ML frameworks are filtered out with a recorded reason. |
| **Signed evidence ledger** | Each inclusion carries the full list of `+`/`−` signals and their plain-language reasons. Tap any card → see *why it's here*. No black box. |
| **`neural` disambiguation** | Distinguishes "neural interface" (kept) from "neural network / deep learning" (dropped) by anchoring on genuine neuro-evidence. |
| **Domain intelligence** | Per-project facets: **modality** (EEG · ECoG · EMG · fNIRS · MEG · spikes/LFP), **paradigm** (P300 · SSVEP · MI · neurofeedback), **signal-chain stage**, and **standards**. |
| **Coverage matrix** | The ecosystem as a modality × pipeline-stage grid — *where it's crowded, and where the open gaps are.* |
| **Standards & interoperability graph** | Which standards dominate (LSL · BIDS · EDF · NWB · MNE/FIF · BrainFlow · OpenBCI) and how projects interconnect. |
| **Health & maturity signals** | A multi-dimension read-out per project — activity, release cadence, community — rolled into a 0–100 maturity score. |
| **Momentum tracking** | Rising, new, and cooling projects, week over week, from a persistent snapshot history. |
| **Foundation & talent signals** | Owners building multiple tracked projects; the people behind the field, not just the repos. |

> The scoring engine itself is proprietary. What's **open** is the map it produces, the
> evidence behind every decision, and the data API. Transparency is the moat — not obscurity.

---

## Why it matters — the scoreboard for BCI

The radar is becoming the **canonical reference layer** for the neurotech ecosystem. Three audiences, one map:

| For… | What they get |
|:--|:--|
| **Investors & VCs** | A due-diligence signal that doesn't come from a pitch deck. BRS, evidence tier, momentum, and ecosystem position — an independent, continuously-updated read on *what's real* in BCI. |
| **Builders & researchers** | Discovery and credibility. Get scored, get seen, get placed on the map next to the standards and players in your modality. |
| **The ecosystem** | The first honest census of open BCI software — where the field is dense, where it's thin, and where it's heading. |

### Badges as an investment marker

A high BRS with a strong evidence tier is a **verifiable quality signal**. As the badge program
rolls out, projects will embed their radar badge — `AxonOS Radar · BRS 95 · Explicit BCI` — the
way they embed a build-passing badge today. For a VC, that badge is a **one-glance
due-diligence marker**: independently scored, evidence-backed, momentum-aware. For a project,
it's a reason to want in. That two-sided pull — projects wanting the badge, investors trusting
it — is the flywheel.

**[→ Get your project on the radar](#get-on-the-radar)**

---

## The evidence system

Every project lands in a tier, and every tier is earned from recorded evidence:

| Tier | Meaning | Example evidence |
|:--|:--|:--|
| **L4 — Explicit BCI** | Names itself a brain–computer interface | `brain-computer-interface`, `bci` topics; explicit BCI hardware |
| **L3 — Standard / Hardware** | Wired into the field's tooling | LSL · BIDS · OpenBCI · BrainFlow · NWB; acquisition hardware |
| **L3 — Modality / Paradigm** | Works a real biosignal or paradigm | EEG · ECoG · EMG · fNIRS; P300 · SSVEP · motor-imagery |
| **L2 — Neuro term** | Genuine neuro-evidence, weaker signal | electrophysiology, cortical, neural-decoding (anchored) |
| **L1 — Weak keep** | Borderline, kept with a low score | passes the gate but flagged |
| **L0 — Rejected** | Generic ML / off-topic | recorded reason; not shown |

---

## The data — an open, honest API

No key, no signup. The map is JSON.

| Endpoint | What it is |
|:--|:--|
| [`data/radar.json`](https://axonos-bci.github.io/axonos-community-radar/data/radar.json) | The full scored payload — projects, BRS, ledgers, facets, coverage matrix, standards graph |
| [`data/history.json`](https://axonos-bci.github.io/axonos-community-radar/data/history.json) | Star & momentum snapshots over time |
| [`data/first_seen.json`](https://axonos-bci.github.io/axonos-community-radar/data/first_seen.json) | Durable first-seen dates (NEW detection) |
| [`feed.xml`](https://axonos-bci.github.io/axonos-community-radar/feed.xml) | RSS of newly-tracked projects |
| [`data/badge-ecosystem.json`](https://axonos-bci.github.io/axonos-community-radar/data/badge-ecosystem.json) | Shields endpoint for the live project count |

---

## BCI Ecosystem Intelligence dashboard

A dense, investor-grade one-page dashboard — relevance distribution, signal-chain coverage,
standards & interoperability, ecosystem health, momentum, players, and composition — rendered
entirely from radar data, **no hand-entered figures**. Published as a weekly market-intelligence
report.

*Preview and the full weekly report: see the pinned links on the [organization profile](https://github.com/AxonOS-BCI).*

---

## Roadmap — to v17

The radar is early. Here's the arc from today to the canonical neurotech intelligence platform:

| Version | Theme | What ships |
|:--:|:--|:--|
| **7.0** | The Relevance Engine | ✅ Scored inclusion (BRS) · evidence ledger · domain intelligence |
| **7.1** | Legible | ✅ Per-card BRS badge · inline "why included" ledger · Relevance sort |
| **7.2** | Dashboards | Interactive + generated **Ecosystem Intelligence** dashboards |
| **8.0** | Open-core | Premium enrichment behind the free, transparent map |
| **9.0** | Signals | Watchlists & alerts — "new BCI repo", "BRS jump", weekly digests |
| **10.0** | Feed | Dataset-as-a-service — the live map as a licensed API |
| **11.0** | Trajectory | Historical analytics — BRS-over-time, cohorts, momentum trends |
| **12.0** | **Badges** | Verified, embeddable project badges — the due-diligence marker |
| **13.0** | Talent | Contributor & builder graph — the neurotech talent map |
| **14.0** | Capital | Funding & domicile signals — who raised, where, and when |
| **15.0** | Standards | Compliance tracking — LSL/BIDS/NWB conformance, clinical readiness |
| **16.0** | Frontier | Adjacent domains — neuromodulation, neuroprosthetics, spatial compute |
| **17.0** | **The Atlas** | The canonical, real-time intelligence platform for neurotech |

Live board: **[Roadmap →](https://github.com/users/AxonOS-BCI/projects/1)**

---

## Get on the radar

| You want to… | Do this |
|:--|:--|
| **Get your project listed & scored** | It's automatic — the engine discovers public BCI repos. To flag one, open a [Feature request](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new/choose). |
| **Fix a mis-score** | Open a [Bug report](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new/choose) — the engine's reasoning is recorded, so corrections are fast. |
| **Use the data** | Hit the [JSON API](https://axonos-bci.github.io/axonos-community-radar/data/radar.json). Attribution appreciated. |
| **License the intelligence feed** | For funds, scouts, and labs: `connect@axonos.org`. |

---

## The three views

| View | What it shows |
|:--|:--|
| **Projects** | The interactive radar + searchable card grid — each with its BRS badge, evidence ledger, and Rising/New/Falling status |
| **Map** | The ecosystem as a system — coverage heatmap (with desert callouts) + standards-interoperability |
| **Builders** | Owners with 2+ tracked projects — the people behind the field |
| **Methodology** | The inclusion rule, evidence tiers, scoring, and the full data contract — in the product |

---

## Data & privacy

Only public GitHub metadata is processed. No private data, no tracking. The engine reads what
GitHub already shows the world, and scores it.

## License

The published data and this showcase are open. The relevance/scoring engine is proprietary to
The AxonOS Project.

---

<div align="center">

© The AxonOS Project / Denis Yermakou

**axonos.org · [medium.com/@AxonOS](https://medium.com/@AxonOS) · axonosorg@gmail.com**

</div>
