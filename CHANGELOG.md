# Changelog

## [3.1.1] - 2026-06-26

### Changed
- Rewrote the README into a deep, accurate project document modelled on the AxonOS house style: what it does and **why it's useful**, a 30-second **quick-start**, the three views, the inclusion rule with **evidence tiers**, the transparent **scoring** formula, the data files ("a small, honest API"), an updated architecture tree, and the Radar's place **within AxonOS** — with every badge verified true and every internal link checked.

### Fixed
- Removed a typo and stale claims from the previous README (it predated the v3 three-view UI, the statistics page, evidence tiers, and the live stats issue).

## [3.1.0] - 2026-06-26

First public beta of the v3 experience.

### Added
- **Three-view UI** in the radar: **Projects** (the map and grid), **Builders** (a leaderboard of owners with 2+ tracked projects), and **Methodology** (inclusion rule, evidence tiers L3–L0, and the transparent scoring formula). Tabs are wired via event listeners — no inline handlers.
- **Externalised front-end:** all JavaScript moved to `assets/app.js` and all CSS to `assets/app.css`.
- **Strict script CSP:** `script-src 'self'` — inline script execution is no longer allowed (the XSS backstop). Inline `style=` colour attributes remain, so `style-src` keeps `'unsafe-inline'`; this is stated honestly rather than over-claimed.

### Changed
- **Categorisation rewritten** (`categorise()`): a keyword in the repository name is the strongest signal, an exact topic match is strong, a description hit is weak, and ties break toward the more specific category. This fixes systematic mis-bucketing — e.g. `*-protocol`, `*-consent`, and `*-sdk` repositories now land in **Protocols & OS** instead of generic buckets they merely brushed against. Re-categorising the current dataset moved 40 of 106 projects and grew Protocols & OS from 2 to 16.
- **Broader inclusion:** `min_stars` lowered from 3 to 1 (more of the field is discovered on the next scan; weak matches are honestly labelled by evidence tier and quality flags rather than hidden), and the **Protocols & OS** keyword set expanded (consent, interop, conformance, mmp, middleware, kernel, os, sdk, …) with the duplicate `openbci` removed.
- CI now checks the externalised `assets/app.js`, guards against a regression to inline-script CSP, and requires the asset files.

### Notes
- Full removal of `'unsafe-inline'` from `style-src` (class-based colours) is deferred to a later patch; the current CSP is described accurately.

## [3.0.0-alpha.4] - 2026-06-26

### Added
- **Live stats issue:** the scheduled workflow now publishes the ecosystem statistics into **one living GitHub issue** (`scripts/publish_stats_issue.py`) — at-a-glance metrics, delta since the last refresh, biggest 7-day movers, new-this-week, a top-builders leaderboard, and category/evidence breakdowns. It edits a single marker-tagged issue in place every 6 hours instead of opening new issues, in the spirit of a momentum-first industry tracker.
- `radar.yml` gains `issues: write` and a publish step.

### Changed
- Removed the old one-off "review digest" issue path from `radar.py` (superseded by the living stats issue).

## [3.0.0-alpha.3] - 2026-06-26

### Added
- **Live statistics dashboard** (`stats.html`): ecosystem growth over time (from `history.json`), category and evidence-tier distributions, a top-builders leaderboard, language breakdown, and rising projects — a self-contained, zero-dependency page that refreshes with the data every 6 hours. Linked from the map as **Stats**.
- Each `history.json` snapshot now carries aggregate `meta` (total, active, new, rising, total stars), so the growth curve is multi-metric and accumulates every scheduled run.
- CI validates `history.json` and the new `stats.html` (integrity + inline-JS syntax).

## [3.0.0-alpha.2] - 2026-06-26

### Fixed
- **Rising now persists:** `publish_data.py` commits `data/history.json` (previously generated but never published, so 7-day star velocity could not accumulate across scheduled runs).
- **UI:** the filter bar no longer sticks under the nav, so project cards are never hidden behind it while scrolling; the nav is more opaque and anchor scrolling accounts for its height.
- Removed the `has_release` field (the GitHub Search API does not return it, so it was misleadingly always false).
- Case-insensitive de-duplication of repositories in the scan loop.
- `docs/METHODOLOGY.md` inclusion rule corrected to match the code (core topic **or** context topic **plus** keyword).
- README no longer claims a "strict" CSP while inline styles/scripts remain (claim made accurate pending the asset split).

### Added
- Project cards now surface the v3 signal: an **evidence-tier** chip (L3/L2/L1/L0, with the inclusion reason on hover) and a **Rising** badge.
- `scripts/validate_payload.py` additionally checks v3 consistency: `counts` match the data, builder `project_count` matches its project list, builder owners are unique and GitHub-hosted.
- Pinned CI dependencies (`requirements-ci.txt`).

### Notes
- This is a pre-release. The full three-view UI (Projects / Builders / Methodology), the asset split, and the strict CSP without `unsafe-inline` land in v3.0.0-beta.

## [3.0.0-alpha.1] - 2026-06-26

### Added (data model v3 — ecosystem intelligence, additive)
- `radar.json` is now **version 3**: every project carries `evidence_tier` (L3_EXPLICIT_BCI / L2_NEURAL_SIGNAL / L1_CONTEXT_PLUS_NEURO / L0_WEAK_ADJACENT), a human-readable `inclusion_reason`, `matched_topics`, `matched_keywords`, `quality_flags`, `owner`/`repo`, license metadata, `stars_delta_7d` / `stars_delta_30d`, `rising`, and an `axon_relevance` map.
- **Builders** aggregation (`builders[]`): owners with two or more listed projects, with totals, activity, and top categories/languages.
- **Rising** via 7-day star velocity, backed by a new `data/history.json` (45-day retention, ≤200 repos/snapshot, corrupt-safe).
- `data/radar.schema.json` — the formal, published v3 data contract; validated in CI.

### Notes
- Fully additive: all v2 fields are preserved, so the current UI keeps working. The three-view UI (Projects / Builders / Methodology) and strict-CSP frontend land in the v3.0.0-beta milestone.
- AxonOS projects are ranked by the same formula as everyone else and the radar excludes its own repository.

## [2.2.1] - 2026-06-26

### Added
- `scripts/validate_payload.py` — strict, zero-dependency validator for the published `data/radar.json` (rejects non-`github.com` URLs, over-long descriptions, malformed numerics, duplicate names; v3-forward).
- `docs/DATA_MODEL.md` and `docs/METHODOLOGY.md` — the public data contract and the transparency surface (inclusion is not endorsement; AxonOS is not boosted).
- `tests/fixtures/malicious-radar.json` plus regression tests proving the validator rejects HTML/URL injection payloads and impossible star jumps.
- `assets/on-axonos-radar.svg` — static badge listed projects can display.

### Changed
- CI now validates the published `radar.json`, fails on any GitHub Action not pinned to a 40-char commit SHA, and `actions/checkout` is now SHA-pinned in both workflows.

All notable changes to AxonOS Radar are documented here.
This project adheres to [Semantic Versioning](https://semver.org).

## [2.2.0] — 2026-06-25

### Changed
- **Renamed to "AxonOS Radar"** (from "Open BCI Radar") across the page, social cards,
  README and release metadata, to avoid confusion with the **OpenBCI** brand.
- **README rebuilt** to the AxonOS Foundation Grande Standard — centred header, true-only
  badges, and full sections (how it works, features, architecture, data & privacy).

### Added
- **Shareable, persistent state** — every filter, sort and view is reflected in the URL
  (`#sort=…&lang=…&cat=…`), so a filtered radar is a link you can send and reload.
- **Live project counts** on each category chip.
- Regenerated social share card under the new name.

## [2.1.0] — 2026-06-25

### Fixed
- **Radar tooltip crash** — the `#tip` element was dropped during the 2.0 redesign, which
  threw "Cannot read properties of null" on radar hover. The element is restored and the
  hover handlers are hardened against a missing node.
- **Relevance false positives** — short keywords (e.g. "erp", event-related potential) were
  substring-matched inside unrelated words ("cl**erp**ad", "int**erp**reter"), letting
  non-BCI repos onto the radar (a MIDI-controller firmware, a systems language, a web
  proxy). Keyword matching is now anchored at word starts; locked with a regression test.

### Added
- **Clear filters** — a pill that appears whenever a filter is active and resets all of them
  in one tap (search, category, language, Active, New).
- **Topic tags on cards** — each project now shows up to three of its real GitHub topics.
- **Keyboard** — press "/" to jump straight to search.
- **Empty state** — when nothing matches, a one-tap "clear all" link.

## [2.0.0] — 2026-06-25

### Changed — major premium redesign
- Complete rebuild to an Apple-tier interface: frosted sticky navigation, refined
  typography and spacing, segmented controls, tasteful motion, fully self-contained.
- **Sort is now an explicit segmented control** (Activity / Stars / Newest / A–Z)
  instead of a cycling toggle — selecting a sort visibly reorders the results, fixing
  the previous UX where the control was unclear.

### Added
- **View switch** — Radar or Grid (segmented), defaulting to the readable card grid.
- **Language filter** — a dropdown populated from the live data.
- **Share** — native share sheet with copy-link fallback.

### Security
- The page no longer loads any external images; the Content-Security-Policy is tightened
  to `img-src 'self' data:` only, making the page fully self-contained.

## [1.1.2] — 2026-06-25

### Added
- **Open Graph / Twitter / JSON-LD** metadata and a branded `og-image.png` for rich
  social-share previews.
- **Accessibility**: ARIA labels, keyboard-activatable filter buttons (`role=button`),
  and a live text alternative describing the radar for screen readers.
- A documented **takedown** path (seeds exclude-list) and a **privacy** note in SECURITY.md.

### Hardened (from external audit, accepted items)
- **Partial-failure safety**: if more than 25% of topic queries fail, the run aborts
  WITHOUT writing, preserving the last-good committed data (no half-empty radar).
- **Durable identity**: `first_seen` now lives in `data/first_seen.json` (bootstrapped
  from radar.json on migration); a corrupt data read aborts instead of flagging the
  whole ecosystem as NEW. Committed via the API alongside the data.
- **XML-correct** feed escaping (`xml.sax.saxutils`), an **8 MB response cap**, an
  API-shape guard, and a **timezone-naive fallback** in recency math.

## [1.1.1] — 2026-06-24

### Fixed
- **Verified commits**: the data-refresh workflow now commits `data/radar.json` and
  `feed.xml` through the GitHub Contents API (`scripts/publish_data.py`), so the
  auto-update commits are GitHub-signed (**Verified**) instead of unsigned runner
  commits. It only commits when project content actually changes (timestamp-only
  diffs are ignored), keeping history clean and green.

## [1.1.0] — 2026-06-24

### Added
- **Relevance filtering** in `scripts/radar.py`: a repository is kept only if it carries
  a core BCI/neuro topic, or a context topic plus a neuro keyword — keeping generic
  projects (VPNs, password managers, generic embedded) off the radar.
- **Deterministic scoring**: recency is measured from a fixed 6-hour snapshot slot, so
  unchanged projects keep a stable position between refreshes (no "jumping").
- **Change tracking**: a stable `first_seen` per project and an `is_new` flag, surfaced
  as `NEW` badges, a **New** filter, and an `is_new` ring on the radar.
- **Stats bar**: projects, new-this-week, active-30d, total stars, categories.
- **Premium project cards** grid alongside the radar, with category pills and activity.
- **RSS feed** (`feed.xml`) of newly discovered projects, plus an `<link rel=alternate>`.
- **Rate-limit handling** (403/429 + `X-RateLimit-Reset`) with bounded backoff.
- **Tests** (`tests/test_radar.py`) for relevance, categorisation, determinism, safety.
- **SECURITY.md** and a Content-Security-Policy.

### Changed
- Radar centering is now CSS-driven (square via `aspect-ratio`, buffer sized from the
  real canvas rect) and readability overhauled (coloured sectors, glowing dots, legible
  ring labels), replacing the parent-width math that caused a right-shift.
- Output `data/radar.json` is now self-validated before write.

### Security
- All repo-derived text is HTML-escaped; links restricted to `https://github.com/…`.

## [1.0.0] — 2026-06-24
- Initial public release: interactive radar, public auto-refreshed data, contribution funnel.
