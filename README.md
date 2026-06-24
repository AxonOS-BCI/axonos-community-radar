<div align="center">

# 📡 &nbsp;Open BCI Ecosystem Radar

**A living, auto-updated map of the open brain–computer-interface field.**
Discover the projects, tools and people building neurotech in the open — and help the ecosystem grow.

[![CI](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/ci.yml)
[![Radar](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/radar.yml/badge.svg)](https://github.com/AxonOS-BCI/axonos-community-radar/actions/workflows/radar.yml)
[![Stars](https://img.shields.io/github/stars/AxonOS-BCI/axonos-community-radar?color=fbbf24)](https://github.com/AxonOS-BCI/axonos-community-radar/stargazers)
[![Contributors](https://img.shields.io/github/contributors/AxonOS-BCI/axonos-community-radar?color=22d3ee)](https://github.com/AxonOS-BCI/axonos-community-radar/graphs/contributors)
[![Last commit](https://img.shields.io/github/last-commit/AxonOS-BCI/axonos-community-radar?color=a78bfa)](https://github.com/AxonOS-BCI/axonos-community-radar/commits/main)
[![License](https://img.shields.io/badge/license-MIT-3fb950)](LICENSE)

### [▶ &nbsp;Open the live radar](https://axonos-bci.github.io/axonos-community-radar/)

</div>

---

## What this is

The **Open BCI Ecosystem Radar** is a continuously-updated, public map of the open brain–computer-interface world. It scans public GitHub data every 6 hours and renders an interactive radar — projects grouped by category, with the most recently active work nearest the centre. It is a single place to **discover, follow and connect** with the people building open neurotech.

It is a community project of [AxonOS](https://axonos.org), an open real-time neural operating system for BCIs.

## Why it exists — and why you'd join

Open BCI work is scattered across hundreds of repos, labs and disciplines. This radar pulls it into one living view so newcomers can find the field, builders can find each other, and good work gets seen.

- **Discover** — one map of the open BCI ecosystem, always fresh.
- **Get on the radar** — put your project in front of the community in one click.
- **Be recognised** — contributors are credited automatically (below), from real Git history.
- **Belong** — a low-noise, technical community around open neurotech.

## Put a project on the radar

Two honest, low-friction ways — projects are discovered **live**, so every link stays real:

1. **One-field issue** — [suggest a project](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new?template=add-project.yml).
2. **Pull request** — add a topic or sharpen a category keyword in [`data/seeds.json`](data/seeds.json).

New to the project? Grab a [good first issue](https://github.com/AxonOS-BCI/axonos-community-radar/contribute) and read [CONTRIBUTING](CONTRIBUTING.md).

## How it works

The radar is generated from **public GitHub topic search** — public, non-archived, non-fork repositories matching a curated set of BCI / neurotech / real-time / privacy topics, ranked by recent activity and stars. Rings show recency; sectors group projects by category. **Categorisation is heuristic and opinionated**, the data refreshes automatically every 6 hours, and the result is a discovery map — **not an endorsement or a quality ranking**.

Our engagement is deliberate and low-noise: star only genuinely relevant repos, react only to genuinely relevant releases, open PRs only when they add technical value, and prefer tests, docs, reproducibility, benchmarks and protocol notes. No mass-follows, no auto-comments.

## Run locally

```bash
git clone https://github.com/AxonOS-BCI/axonos-community-radar.git
cd axonos-community-radar
python3 -m http.server 8080
```

Open `http://127.0.0.1:8080`. To refresh the data locally with a GitHub token: `GH_TOKEN=… python3 scripts/radar.py`.

## Community

[Discussions](https://github.com/AxonOS-BCI/axonos-community-radar/discussions) &nbsp;·&nbsp; [Medium](https://medium.com/@AxonOS) &nbsp;·&nbsp; [axonos.org](https://axonos.org) &nbsp;·&nbsp; [AxonOS on GitHub](https://github.com/AxonOS-org)

## Contributors

Every person who shapes the radar — thank you.

<a href="https://github.com/AxonOS-BCI/axonos-community-radar/graphs/contributors"><img src="https://contrib.rocks/image?repo=AxonOS-BCI/axonos-community-radar" alt="Contributors"></a>

---

<div align="center">

© The AxonOS Project / Denis Yermakou &nbsp;·&nbsp; axonos.org &nbsp;·&nbsp; connect@axonos.org &nbsp;·&nbsp; security@axonos.org

</div>
