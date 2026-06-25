<div align="center">

# 📡 &nbsp;AxonOS Radar

### A living map of the open brain–computer-interface field

*Discover, follow and connect with the people building open neurotech — automatically, every six hours.*

<br>

[![Live](https://img.shields.io/badge/live-axonos--bci.github.io-a78bfa?style=flat-square)](https://axonos-bci.github.io/axonos-community-radar/)
[![CI](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/AxonOS-BCI/axonos-community-radar?style=flat-square&color=2dd4ff)](https://github.com/AxonOS-BCI/axonos-community-radar/commits/main)
[![Data](https://img.shields.io/badge/data-refreshed%20every%206h-2dd4ff?style=flat-square)](#how-it-works)
[![Runtime deps](https://img.shields.io/badge/runtime%20deps-zero-34d399?style=flat-square)](#architecture)

<br>

**[🛰️ Open the live radar →](https://axonos-bci.github.io/axonos-community-radar/)** &nbsp;•&nbsp; **[➕ Add a project](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new?template=add-project.yml)** &nbsp;•&nbsp; **[💬 Discussions](https://github.com/AxonOS-BCI/axonos-community-radar/discussions)** &nbsp;•&nbsp; **[📰 RSS](https://axonos-bci.github.io/axonos-community-radar/feed.xml)**

</div>

---

## What this is

**AxonOS Radar** is a continuously-updated, public map of the open brain–computer-interface world. It scans public GitHub data every six hours and renders an interactive radar and card grid — projects grouped by category, with the most recently active work nearest the centre, freshly-discovered work flagged as **new**, and the whole field searchable and filterable.

It exists to give the open-neurotech community a single, honest place to **discover, follow and connect** — and to do it without hype: every link is real, every project is discovered live, and nothing is hand-curated to flatter anyone.

It is an open community project from **[AxonOS](https://axonos.org)** — an open, real-time neural operating system for BCIs.

## How it works

The radar is generated entirely from **public GitHub topic search** — no scraping, no private data, no third-party services.

- **Relevance, not noise.** A repository is kept only if it carries a *core* BCI/neuro topic (`bci`, `eeg`, `neurotechnology`, …), **or** a *context* topic (`signal-processing`, `embedded-rust`, `no-std`, `privacy`, …) **together with** a neuro keyword in its text. Keyword matching is anchored at word starts, so a project about a *MIDI controller* or an *interpreter* never slips in on a stray substring.
- **Stable positioning.** Recency is measured from a fixed six-hour snapshot, so a project that hasn't changed keeps its place — the map doesn't jitter between refreshes.
- **Durable "new" flags.** First-seen timestamps are tracked in `data/first_seen.json`, so the **new** badge reflects genuine discovery, not a reshuffle.
- **Safe by construction.** If more than a quarter of the topic queries fail (rate limits, outages), the run aborts *without* writing — the last good map is preserved rather than replaced with a half-empty one.

The result is committed back to the repository through the GitHub API, which signs the commit — so the data history stays **Verified**.

## Features

- 🛰️ **Interactive radar** — categories as coloured sectors, recency as distance from centre, stars as size.
- 🗂️ **Card grid** — a clean, scannable view with real GitHub topics on every card.
- 🔀 **Sort** — by activity, stars, newest, or A–Z (an explicit, Apple-style segmented control).
- 🎛️ **Filter** — by category (with live counts), language, *active in the last 30 days*, and *new*.
- 🔗 **Shareable views** — every filter and sort is reflected in the URL, so a filtered radar is a link you can send.
- 🔎 **Keyboard** — press <kbd>/</kbd> to jump straight to search.
- 📰 **RSS feed** — follow freshly-discovered projects from any reader.
- ♿ **Accessible** — ARIA roles, keyboard-operable controls, and a live text alternative for the radar.
- 🔒 **Self-contained** — vanilla JS, a strict Content-Security-Policy, no external requests, no trackers.

## Contributing

The map is only as alive as its community — and the bar to help is deliberately low.

- **Put a project on the radar.** Building or using something open in BCI / neurotech? [Open a one-field issue](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new?template=add-project.yml), or add a topic via PR to [`data/seeds.json`](data/seeds.json). Projects are discovered live, so every entry stays real.
- **Talk neurotech.** Share work, papers and questions in [Discussions](https://github.com/AxonOS-BCI/axonos-community-radar/discussions).
- **Improve the radar itself.** PRs that add genuine value are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

### Engagement policy

This project models the kind of community it wants to see. We **star** only genuinely relevant repositories, **react** only to genuinely relevant releases, and **open PRs** only when they add real technical value. No mass-follows, no auto-comments, no low-signal noise.

## Architecture

```
axonos-community-radar/
├── index.html              # the radar UI — vanilla JS, self-contained, CSP-hardened
├── data/
│   ├── seeds.json          # core/context topics, neuro keywords, categories
│   ├── radar.json          # generated dataset (committed via the GitHub API → Verified)
│   └── first_seen.json     # durable first-seen timestamps for the "new" flag
├── feed.xml                # generated RSS of newly-discovered projects
├── og-image.png            # social share card
├── scripts/
│   ├── radar.py            # the discovery + relevance + scoring pipeline (stdlib only)
│   └── publish_data.py     # commits data via the GitHub API only when it meaningfully changes
├── tests/
│   └── test_radar.py       # relevance, categorisation, determinism, safety, regressions
└── .github/workflows/
    ├── radar.yml           # every 6h: scan → validate → publish
    └── ci.yml              # JSON/XML/Python/HTML/CSP/secret gates on every push
```

**Zero runtime dependencies** — the page is vanilla JavaScript, and the pipeline uses only the Python standard library.

## Data & privacy

The radar shows only **public** repository metadata that GitHub already exposes through its search API (name, description, topics, stars, language, last-push date). It stores no personal data and sets no cookies. To request removal of a project, add it to the exclude list in `data/seeds.json` or [open an issue](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new) — see [`SECURITY.md`](SECURITY.md).

## License

Released under the [MIT License](LICENSE) — free to use, fork and build on.

<div align="center">
<br>
<sub>© The AxonOS Project / Denis Yermakou &nbsp;·&nbsp; <a href="https://axonos.org">axonos.org</a> &nbsp;·&nbsp; <a href="https://medium.com/@AxonOS">medium.com/@AxonOS</a> &nbsp;·&nbsp; connect@axonos.org &nbsp;·&nbsp; security@axonos.org</sub>
</div>
