# Changelog

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
