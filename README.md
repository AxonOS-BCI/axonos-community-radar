<div align="center">

# 📡 &nbsp;AxonOS Radar

### The open brain–computer-interface field, mapped automatically.

#### A living, momentum-first map of open BCI — discovered live from public GitHub, refreshed every three hours.

[![Live](https://img.shields.io/badge/live-axonos--bci.github.io-a78bfa?style=flat-square)](https://axonos-bci.github.io/axonos-community-radar/)
[![CI](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-6.0.1-0a4a8f?style=flat-square)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-475569?style=flat-square)](LICENSE)
[![Data](https://img.shields.io/badge/data-refreshed%20every%203h-2dd4ff?style=flat-square)](#-how-a-project-gets-on-the-radar)
[![Runtime deps](https://img.shields.io/badge/runtime%20deps-zero-34d399?style=flat-square)](#-architecture)
[![CSP](https://img.shields.io/badge/CSP-strict-34d399?style=flat-square)](#-data--privacy)
[![SAST](https://img.shields.io/badge/SAST-bandit%20blocking-34d399?style=flat-square)](docs/THREAT_MODEL.md)
[![Pages](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/pages.yml/badge.svg?branch=main)](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/pages.yml)

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

## 🩹 &nbsp;The pains this radar closes

Open BCI has real, recurring pains. v6 maps each one to a mechanism you can verify — not a promise:

| The field's pain | What the radar does about it |
|:--|:--|
| **Fragmentation.** Hundreds of scattered repos, no single map. | The live radar + card grid, refreshed every 3 hours, with a published inclusion rule and an evidence tier on every entry. |
| **Abandonment blindness.** Projects die quietly; people build on corpses. | **Health** (recency, 52-week commits, team breadth) + **Rising/Falling** from measured star velocity — decay is visible before you depend on it. |
| **The trust question: *"can I build on this?"*** | **Foundation signals** — seven checkable facts per repo (licence file, README, CONTRIBUTING, code of conduct, `CITATION.cff`, `SECURITY.md`, CI workflows). Facts, not vibes; absence of evidence shows as absence, never as a fabricated zero. |
| **Integration guesswork.** Every stack speaks its own protocol. | **Interop tags** — "who speaks LSL / BrainFlow / BIDS / OpenBCI…" detected from a committed vocabulary, filterable in one tap. |
| **Reproducibility friction.** Getting field data into a notebook is an afternoon. | Stable endpoints incl. **`data/projects.ndjson`** (one project per line — pandas/jq/DuckDB-ready) and a CI-validated JSON Schema. |
| **Opaque rankings.** Most "top BCI" lists are editorial. | Every formula is published, every signal is documented, and a **documentation-coverage gate fails CI** if any shipped signal, tag or endpoint is unexplained. |

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
| **Methodology** | The inclusion rule, evidence tiers, scoring, **Foundation signals**, **interop detection** and the full **data-endpoints contract** — in the product, not buried in docs. |

## 🧱 &nbsp;New in 6.0 — Solid Ground

Two new honest axes on every card, and the radar grows into a **data product**:

- **Foundation `n/7`** — seven checkable repository facts (community profile, root `CITATION.cff`, root `SECURITY.md`, CI workflows). The tooltip lists every ✓/✗; the UI recomputes the count locally and never trusts a shipped number. Sort the whole field by Foundation from the sort bar.
- **"Speaks" interop pills** — 20 protocols/formats/toolkits/hardware/runtimes detected word-boundary-strictly from topics & descriptions against a reviewable vocabulary ([`data/interop-vocab.json`](data/interop-vocab.json)). One tap filters the field to *everything that speaks LSL*.
- **`data/projects.ndjson`** — the dataset, one project per line, built at deploy time.
- **A documentation-coverage CI gate** — nothing on a card ships unexplained, mechanically.
- Payload contract → **v4**, fully backward-compatible; fabrication guards extended (unknown interop tags and inconsistent foundation counts are rejected). Health scoring unchanged, so historical series stay comparable.

## 🩺 &nbsp;New in 5.1 — the field, scored honestly

The radar stops being a list and becomes an **instrument**. Every project now
carries an **Ecosystem Health** read-out: a single 0–100 score plus six
sub-scores, computed **only from real public GitHub signals the scan already
fetches** — no extra API calls, no surveys, no self-assessment.

| Dimension | Measured from |
|:--|:--|
| **Maintenance** | How recently the repo was pushed to. |
| **Momentum** | The real 52-week commit total — is development sustained? |
| **Adoption** | Stars, published releases, and real release download counts. |
| **Team** | Contributor breadth — more than a bus-factor of one? |
| **Licence** | Whether an OSI-recognised licence grants clear reuse rights. |
| **Doc signals** | Presence of a description, homepage, and licence file. |

The overall score is a weighted mean of **only the dimensions we could measure**
for a given repo — anything unmeasurable is **left out, not guessed**, and a repo
that wasn't enriched this cycle is flagged `search-only`. We deliberately do
**not** score conformance, security posture, or test quality: none can be read
reliably from search metadata, so scoring them would be fiction. **AxonOS is
scored by the exact same rules as everyone else** — by construction, not by
promise (its own repos currently sit in the *developing* band; the score has no
way to flatter anyone). The full formula is published in
[`docs/METHODOLOGY.md`](docs/METHODOLOGY.md), enforced by the JSON Schema, and
covered by unit tests. In the UI it's a band-coloured meter on every card with
the breakdown in the tooltip, plus a **Health** sort. Newcomers get a new
persona-based **“Where to start”** entry point.

> **Health is a triage signal, not a verdict.** A high score means a repo looks
> well-maintained, adopted, and clearly licensed — **never** that it is correct,
> safe, or fit for clinical use.

## ✨ &nbsp;New in 5.0.x — the field, in motion

A major release line: the pipeline got faster and fairer, the UI became a
shareable instrument, every page renders through DOM-safe code with zero
`innerHTML` on data paths, and the map carries an optional Dogecoin support
card (the radar has no paywalled features — funding just keeps it free for
everyone).

**Pipeline**
* **Parallel enrichment** — a 4-worker stdlib thread pool with a shared, locked API budget cuts scan wall-time ~3–4× at the same politeness per connection.
* **Saturated-topic recovery** — when GitHub search reports more matches than a topic pull returned, one bounded `sort=stars` pass recovers big-but-quiet classics, through **exactly the same relevance gate** as everything else.
* **`data/weekly.json`** — a ~1 KB movement digest (field deltas, top movers, entrants) computed server-side each scan; the map, the stats page and the report all read the same numbers.
* **Builders, enriched** — the Builders board now shows account type (ORG/USER) and followers from public owner profiles.
* **min_stars = 2** and hyphen-aware keyword matching sharpen inclusion.

**Experience**
* **This-week strip** on the map and stats; **Momentum chart** (rising vs falling per snapshot) on the stats page.
* **Evidence-tier filter** (L3/L2/L1/L0), **↓ Falling** quick filter, **licence markers** on cards, **density toggle**, `Esc` clears search — all encoded in shareable `#` permalinks.
* **Category trend arrows** and **owner columns** in the printable report.

**Engineering honesty**
* **Pages deploys as one artifact per scan** (`pages.yml`) — killing the cosmetic red ✗ storm from per-commit Jekyll builds. One-time setup: *Settings → Pages → Source = GitHub Actions*.
* **Zero `innerHTML`** across `app.js` and `stats.js`; the stats page's inline `<style>` (silently blocked by our own strict CSP!) now lives in `assets/stats.css` where the CSP allows it.
* **Six independent CI jobs** (data integrity, Python quality, frontend + jsdom smoke, report build, security, release hygiene); **bandit is blocking**; every action **SHA-pinned with truthful version labels**; the JSON Schema is a full typed contract.

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
| [`data/radar.json`](data/radar.json) | The dataset — projects with category, evidence tier, inclusion reason, stars, deltas, `rising`, a `signals` health block, and a `builders[]` roll-up. Schema: [`radar.schema.json`](data/radar.schema.json). |
| [`data/history.json`](data/history.json) | Per-snapshot aggregates (totals, active, new, rising, stars) — the time series behind the growth chart and *Rising*. |
| [`data/projects.ndjson`](https://axonos-bci.github.io/axonos-community-radar/data/projects.ndjson) | **New in 6.0** — one project per line, key-sorted, built at deploy time. `pd.read_json(url, lines=True)` and you're done. |
| [`data/interop-vocab.json`](data/interop-vocab.json) | **New in 6.0** — the interop vocabulary: the exact word-boundary patterns behind every "Speaks" tag. Open to review and PRs. |
| [`feed.xml`](feed.xml) | RSS of newly-discovered projects. |
| [`data/seeds.json`](data/seeds.json) | The topics, keywords, categories, and thresholds that define the scan. |
| [`data/ecosystem.json`](https://axonos-bci.github.io/axonos-community-radar/data/ecosystem.json) | **New in 5.2** — the AxonOS *organism manifest*: every AxonOS account and repository with its role, live Health signals for radar-tracked repos, and the canonical voluntary-support block. Built at deploy time from [`data/ecosystem-registry.json`](data/ecosystem-registry.json) + the live scan. |
| [`data/badge-ecosystem.json`](https://axonos-bci.github.io/axonos-community-radar/data/badge-ecosystem.json) | **New in 5.2** — a [shields.io endpoint](https://shields.io/badges/endpoint-badge) carrying the ecosystem's live pulse. Embed anywhere: `![AxonOS ecosystem](https://img.shields.io/endpoint?url=https%3A%2F%2Faxonos-bci.github.io%2Faxonos-community-radar%2Fdata%2Fbadge-ecosystem.json)` |

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
│   ├── signals.py          # Ecosystem Health: transparent 0–100 scores from real GitHub signals
│   ├── publish_data.py     # commits data via the GitHub API only when it meaningfully changes
│   ├── publish_stats_issue.py  # upserts ONE living stats issue every scan
│   └── validate_payload.py # strict, dependency-free dataset validator
├── tests/
│   └── test_radar.py       # relevance, categorisation, determinism, safety, regressions
└── .github/workflows/
    ├── radar.yml           # every 3h: scan → validate → publish → update stats issue
    └── ci.yml              # JSON/XML/Python/HTML/CSP/secret gates on every push
```

> **Zero runtime dependencies.** The page is vanilla JavaScript; the pipeline uses only the Python standard library. The only CI-time packages (`pytest`, `jsonschema`) are version-pinned in [`requirements-ci.txt`](requirements-ci.txt).

### Deployment note

The site ships as a **single Pages artifact per scan** via `pages.yml` (no
Jekyll). One-time repository setting: **Settings → Pages → Source = "GitHub
Actions"**. The schedule runs at **:17 past every third hour (UTC)** — offset
from the top of the hour by design to avoid the crowd.

## 🧬 &nbsp;Within AxonOS

The Radar is the community-facing edge of a larger open project. As of 5.0.3 these repositories appear **inside the radar itself** — as ecosystem anchors with a live "AxonOS ecosystem" panel mapping the people and shared maintainers behind them (see the map's top section). The engineering it points back to:

| Repository | Role |
|:--|:--|
| [`axonos-kernel`](https://github.com/AxonOS-org/axonos-kernel) | The real-time `no_std` neural kernel — scheduler, time, capability. |
| [`axonos-protocol`](https://github.com/AxonOS-org/axonos-protocol) | The AxonOS Consent Protocol on the wire — `no_std`, zero-alloc. |
| [`axonos-consent`](https://github.com/AxonOS-org/axonos-consent) | Kernel-level consent FSM with formally-bounded withdrawal latency. |
| [`axonos-signal-pipeline`](https://github.com/AxonOS-org/axonos-signal-pipeline) | Fixed-point DSP chain: raw frame → epoch → features → decision. |
| [`axonos-standard`](https://github.com/AxonOS-org/axonos-standard) | The normative AxonOS Standard and claims catalogue. |
| [`axonos-e2e-demo`](https://github.com/AxonOS-org/axonos-e2e-demo) | Synthetic signal → typed intent, bit-for-bit reproducible. |

## 💛 &nbsp;Support the organism

Everything in the AxonOS ecosystem — this radar, the [Neural Boundary Game](https://github.com/AxonOS-BCI/neural-boundary-game), the [open-source neural OS](https://github.com/AxonOS-org) — is free and open: **no paywalls, no ads, no tracking, no tokens**. If it's useful to you, a voluntary Dogecoin tip is the direct way to fuel the work:

<div align="center">

**[💛 Support page — one ecosystem, one address](https://axonos-bci.github.io/axonos-community-radar/support.html)**

`DMwHAhqVNWf7dyEznukxCufNS5rjuP5MTp` &nbsp;·&nbsp; [verify on-chain](https://dogechain.info/address/DMwHAhqVNWf7dyEznukxCufNS5rjuP5MTp)

</div>

Contributions are voluntary — not purchases, not investments, and no product entitlement is granted (everything is already free). Commercial licensing is a separate written-agreement channel: [connect@axonos.org](mailto:connect@axonos.org).

## 📑 &nbsp;Citation


If you reference AxonOS Radar in academic or technical work, please cite it:

```bibtex
@software{yermakou_axonos_radar_2026,
  author  = {Yermakou, Denis},
  title   = {{AxonOS Radar: a living map of the open brain--computer-interface field}},
  year    = {2026},
  url     = {https://github.com/AxonOS-BCI/axonos-community-radar},
  version = {6.0.1}
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
