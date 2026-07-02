<div align="center">

# 📡 &nbsp;AxonOS Radar

### The open brain–computer-interface field, mapped automatically.

#### A living, momentum-first map of open BCI — discovered live from public GitHub, refreshed every three hours.

[![Live](https://img.shields.io/badge/live-axonos--bci.github.io-a78bfa?style=flat-square)](https://axonos-bci.github.io/axonos-community-radar/)
[![CI](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-4.3.0-0a4a8f?style=flat-square)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-475569?style=flat-square)](LICENSE)
[![Data](https://img.shields.io/badge/data-refreshed%20every%206h-2dd4ff?style=flat-square)](#-how-a-project-gets-on-the-radar)
[![Runtime deps](https://img.shields.io/badge/runtime%20deps-zero-34d399?style=flat-square)](#-architecture)
[![CSP](https://img.shields.io/badge/CSP-strict-34d399?style=flat-square)](#-data--privacy)

**[🛰️ Open the live radar →](https://axonos-bci.github.io/axonos-community-radar/)** &nbsp;•&nbsp; **[📈 Statistics](https://axonos-bci.github.io/axonos-community-radar/stats.html)** &nbsp;•&nbsp; **[➕ Add a project](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new?template=add-project.yml)** &nbsp;•&nbsp; **[📰 RSS](https://axonos-bci.github.io/axonos-community-radar/feed.xml)**

</div>

---

**AxonOS Radar** is a continuously-updated, public map of the open brain–computer-interface world. Every three hours it scans **public GitHub metadata**, keeps only what is genuinely BCI/neuro-relevant, labels *why* each project qualifies, ranks the field by a neutral discovery score, and renders it as an interactive radar, a card grid, a statistics dashboard, and a self-updating GitHub issue. It is, in spirit, a **momentum tracker for the open neurotech field** — surfacing what's active, what's rising, and who's building, on *real, verifiable signals* rather than hype.

It is an open community project from **[AxonOS](https://axonos.org)** — an open, real-time neural operating system for BCIs.

> **Discovery, not endorsement.** Inclusion never implies quality, safety, or clinical fitness, and listing transfers no ownership. Categories are heuristic; scores are discovery signals. **AxonOS itself is ranked by the same formula as everyone else** — there is no self-boosting, and no figure on this map is hand-curated to flatter anyone.

## 💡 &nbsp;What it does, and why it's useful

The open BCI field is scattered across hundreds of repositories with no single, honest place to see it. The Radar is that place:

- **For researchers & builders** — discover the libraries, decoders, hardware and protocols that actually exist, see what's gaining momentum, and find the people building multiple projects worth following.
- **For newcomers** — one map of the field, grouped by what each project *does*, with a transparent reason for every entry.
- **For anyone evaluating the space** — a neutral, reproducible read-out: every link is real, every project is discovered live, and the ranking formula is published. Nothing is fabricated.

> **The anti-hype contract.** Every link is real. Every project is discovered live from public data. The score is `log₁₀(stars+1) × 10 + recency` — published, neutral, and applied to all. *Rising* reflects measured 7-day star velocity, not opinion.

## ⚡ &nbsp;Quick start — use it in 30 seconds

| You want to… | Do this |
|:--|:--|
| **See the field** | Open the [live radar](https://axonos-bci.github.io/axonos-community-radar/). Three tabs: **Projects**, **Builders**, **Methodology**. |
| **Find something specific** | Press <kbd>/</kbd> to search, or filter by category, language, *active 30d*, or *new*. |
| **See momentum & trends** | Open the [Statistics](https://axonos-bci.github.io/axonos-community-radar/stats.html) page — growth over time, categories, evidence, top builders, rising projects. |
| **Follow new launches** | Subscribe to the [RSS feed](https://axonos-bci.github.io/axonos-community-radar/feed.xml), or watch the auto-updating **Live Ecosystem Stats** issue. |
| **Add a project** | [Open a one-field issue](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new?template=add-project.yml) — it's discovered on the next scan. |
| **Build on the data** | Fetch [`data/radar.json`](data/radar.json) (schema: [`data/radar.schema.json`](data/radar.schema.json)). It's plain, versioned JSON. |

**Listed projects can show this badge:** &nbsp; [![On AxonOS Radar](https://axonos-bci.github.io/axonos-community-radar/assets/on-axonos-radar.svg)](https://axonos-bci.github.io/axonos-community-radar/)

```md
[![On AxonOS Radar](https://axonos-bci.github.io/axonos-community-radar/assets/on-axonos-radar.svg)](https://axonos-bci.github.io/axonos-community-radar/)
```

## 🧭 &nbsp;The three views

| View | What it shows |
|:--|:--|
| **Projects** | The interactive radar (categories as sectors, recency as distance, stars as size) and a searchable, filterable card grid. Each card carries its real GitHub topics, an **evidence tier**, and a **Rising** or **Falling** badge when it's moving either way. |
| **Builders** | A leaderboard of *owners with 2+ tracked projects* — total stars, active projects, and their focus areas. The people, not just the repos. |
| **Methodology** | The inclusion rule, the four evidence tiers, and the scoring formula — in the product, not buried in docs. |

## ✨ &nbsp;New in 4.3.0 — momentum, both directions

The report grew from a snapshot into a **motion picture** of the field, and the
pipeline got a hardening pass driven by an external-style audit:

* **How the field moved** — headline deltas (projects, stars, active, rising) across the last week of snapshots, measured from `data/history.json`, never estimated.
* **Star trajectories** — real per-project star curves across scans for the top of the field.
* **Declining** — projects losing stars are shown with the same prominence as risers; hiding degradation would be dishonest cartography.
* **Category health matrix** — size, reach, active-share, movers both ways and median push age, per category.
* **Licence posture** — declared / unclear (NOASSERTION) / missing, now distinguished correctly.
* **Pipeline health panel** — the radar reports on itself from `data/status.json`: scan stats, enrichment coverage, archived exclusions, search saturation, API budget.
* **Fairer ranking** — enrichment now covers a buffer beyond the cap before the final cut (kills the top-N sampling bias); archived repos leave the ranking; category ties break deterministically.
* **Self-diagnosing** — every run writes `data/last_run.json`; a twice-daily health monitor watches the *published* data and maintains a single self-closing alert issue if it goes stale.
* **Deeper docs** — [threat model](docs/THREAT_MODEL.md) · [incident response](docs/INCIDENT_RESPONSE.md) · [data retention](docs/RETENTION.md) · [SBOM](docs/SBOM.md).

## 🔬 &nbsp;How a project gets on the radar

The radar is generated entirely from **public GitHub topic search** — no scraping, no private data, no third-party services. A repository is kept if it has **either**:

1. a **core** BCI/neuro topic (`bci`, `eeg`, `ecog`, `neurotechnology`, `neural-interface`, …), **or**
2. a **context** topic (`signal-processing`, `embedded-rust`, `no-std`, `privacy`, …) **plus** an anchored neuro keyword in its metadata.

Keyword matching is anchored at word boundaries, so a project about a *MIDI controller* never slips in on the substring `mi`. Every kept project is then assigned an **evidence tier** that states *why* it's here:

| Tier | Meaning |
|:--|:--|
| ![L3](https://img.shields.io/badge/L3-explicit%20BCI-34d399?style=flat-square) | Carries a direct brain–computer-interface / neural-interface topic. |
| ![L2](https://img.shields.io/badge/L2-neural%20signal-2dd4ff?style=flat-square) | A neural-signal topic or keyword (EEG, ECoG, EMG, spike sorting, motor imagery…). |
| ![L1](https://img.shields.io/badge/L1-context%2Bkeyword-a78bfa?style=flat-square) | A context topic **plus** an anchored neuro keyword. |
| ![L0](https://img.shields.io/badge/L0-weak%20(review)-fb7185?style=flat-square) | Included but flagged — a borderline match that may be a false positive. |

**Categorisation** is weighted, not naïve: a keyword in the repository **name** is the strongest signal, an exact **topic** match is strong, a description hit is weak, and ties break toward the more *specific* category — so a repo named `*-protocol` lands in **Protocols & OS**, not a generic bucket it merely brushes against.

**Stable & safe.** Recency is measured from a fixed six-hour snapshot, so unchanged projects keep their place. First-seen timestamps live in `data/first_seen.json`, so **new** means genuine discovery. If more than a quarter of the topic queries fail, the run aborts *without writing* — the last good map is preserved, never replaced with a half-empty one. The result is committed through the GitHub API, which signs the commit, so the data history stays **Verified**.

## 📊 &nbsp;The data — a small, honest API

Everything the UI shows is plain, versioned JSON you can build on:

| File | Contents |
|:--|:--|
| [`data/radar.json`](data/radar.json) | The dataset — projects with category, evidence tier, inclusion reason, stars, deltas, `rising`, and a `builders[]` roll-up. Schema: [`radar.schema.json`](data/radar.schema.json). |
| [`data/history.json`](data/history.json) | Per-snapshot aggregates (totals, active, new, rising, stars) — the time series behind the growth chart and *Rising*. |
| [`feed.xml`](feed.xml) | RSS of newly-discovered projects. |
| [`data/seeds.json`](data/seeds.json) | The topics, keywords, categories, and thresholds that define the scan. |

## 🏗️ &nbsp;Architecture

```
axonos-community-radar/
├── index.html              # the radar UI — three views, vanilla JS, strict script-CSP
├── stats.html              # the statistics dashboard
├── assets/
│   ├── app.js              # all UI logic (externalised → script-src 'self')
│   └── app.css             # all styles
├── data/
│   ├── seeds.json          # core/context topics, neuro keywords, categories, thresholds
│   ├── radar.json          # generated dataset (committed via the GitHub API → Verified)
│   ├── history.json        # per-snapshot aggregates for trends & Rising
│   ├── first_seen.json     # durable first-seen timestamps for the "new" flag
│   └── radar.schema.json   # JSON Schema for radar.json
├── feed.xml                # generated RSS of newly-discovered projects
├── scripts/
│   ├── radar.py            # discovery → relevance → evidence tier → categorise → score (stdlib only)
│   ├── publish_data.py     # commits data via the GitHub API only when it meaningfully changes
│   ├── publish_stats_issue.py  # upserts ONE living stats issue every 6h
│   └── validate_payload.py # strict, dependency-free dataset validator
├── tests/
│   └── test_radar.py       # relevance, categorisation, determinism, safety, regressions
└── .github/workflows/
    ├── radar.yml           # every 6h: scan → validate → publish → update stats issue
    └── ci.yml              # JSON/XML/Python/HTML/CSP/secret gates on every push
```

> **Zero runtime dependencies.** The page is vanilla JavaScript; the pipeline uses only the Python standard library. The only CI-time packages (`pytest`, `jsonschema`) are version-pinned in [`requirements-ci.txt`](requirements-ci.txt).

## 🧬 &nbsp;Within AxonOS

The Radar is the community-facing edge of a larger open project. The engineering it points back to:

| Repository | Role |
|:--|:--|
| [`axonos-kernel`](https://github.com/AxonOS-org/axonos-kernel) | The real-time `no_std` neural kernel — scheduler, time, capability. |
| [`axonos-protocol`](https://github.com/AxonOS-org/axonos-protocol) | The AxonOS Consent Protocol on the wire — `no_std`, zero-alloc. |
| [`axonos-consent`](https://github.com/AxonOS-org/axonos-consent) | Kernel-level consent FSM with formally-bounded withdrawal latency. |
| [`axonos-signal-pipeline`](https://github.com/AxonOS-org/axonos-signal-pipeline) | Fixed-point DSP chain: raw frame → epoch → features → decision. |
| [`axonos-standard`](https://github.com/AxonOS-org/axonos-standard) | The normative AxonOS Standard and claims catalogue. |
| [`axonos-e2e-demo`](https://github.com/AxonOS-org/axonos-e2e-demo) | Synthetic signal → typed intent, bit-for-bit reproducible. |

## 📑 &nbsp;Citation

If you reference AxonOS Radar in academic or technical work, please cite it:

```bibtex
@software{yermakou_axonos_radar_2026,
  author  = {Yermakou, Denis},
  title   = {{AxonOS Radar: a living map of the open brain--computer-interface field}},
  year    = {2026},
  url     = {https://github.com/AxonOS-BCI/axonos-community-radar},
  version = {3.4.0}
}
```

GitHub's **"Cite this repository"** button (from [`CITATION.cff`](CITATION.cff)) generates APA and BibTeX automatically.

## 🔐 &nbsp;Data & privacy

The radar shows only **public** repository metadata GitHub already exposes through its search API (name, description, topics, stars, language, last-push date). It stores no personal data and sets no cookies. The UI is self-contained — vanilla JS under a Content-Security-Policy with **externalised scripts** (no inline script execution, no external network requests, no trackers). To request removal of a project, add it to the exclude list in [`data/seeds.json`](data/seeds.json) or [open an issue](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new) — see [`SECURITY.md`](SECURITY.md) and the [data-retention policy](docs/RETENTION.md).

## 🤝 &nbsp;Contributing

The map is only as alive as its community, and the bar to help is deliberately low — [open a one-field issue](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new?template=add-project.yml) to add a project, talk neurotech in [Discussions](https://github.com/AxonOS-BCI/axonos-community-radar/discussions), or send a PR (see [`CONTRIBUTING.md`](CONTRIBUTING.md)).

> **Engagement policy.** This project models the community it wants to see: we **star** only genuinely relevant repositories, **react** only to genuinely relevant releases, and **open PRs** only when they add real technical value. No mass-follows, no auto-comments, no low-signal noise.

## 📄 &nbsp;License

Released under the [MIT License](LICENSE) — free to use, fork and build on. The generated data is derived from public GitHub metadata; inclusion implies no endorsement.

<div align="center">
<br>
<sub>© The AxonOS Project / Denis Yermakou &nbsp;·&nbsp; <a href="https://axonos.org">axonos.org</a> &nbsp;·&nbsp; <a href="https://medium.com/@AxonOS">medium.com/@AxonOS</a> &nbsp;·&nbsp; connect@axonos.org &nbsp;·&nbsp; security@axonos.org</sub>
</div>
