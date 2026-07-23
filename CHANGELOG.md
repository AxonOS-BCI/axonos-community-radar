# Changelog

## [12.0.4] — 2026-07-22 — "the front door, permanently"

### Fixed
- `report.html`'s "Live map" / "Dashboard" / "GitHub" links pointed at
  `axonos-radar-core` (the private engine, no public Pages site) instead of
  this repo — the same bug patched once before and silently overwritten by
  the next engine sync, because the fix lived in the wrong place. The
  correction now lives in `sync_engine_data.py` itself, applied to the
  fetched body on every sync before it's ever committed — it survives every
  future sync instead of being undone by it, and becomes a no-op
  automatically once the engine's own template is corrected upstream.
- `CONTRIBUTING.md` told a new contributor to run
  `GH_TOKEN=… python3 scripts/radar.py` to refresh data locally — that file
  was deleted at the 8.0.0 open-core cutover, so this was a guaranteed
  `FileNotFoundError` on the first thing the guide asked anyone to try.
  Replaced with what's actually runnable now (preview, tests, validator)
  and an honest note that discovery/scoring has no local equivalent anymore.
- `docs/RETENTION.md` attributed retention constants to `scripts/radar.py`
  (deleted) and `radar.yml` (disabled) in three separate table rows — all
  three now correctly say the private engine.
- `ROADMAP.md`'s "Where we are" line still said v10.0 while the table two
  lines below it already correctly showed v12.0 shipped — updated the
  summary to match the table it was supposed to summarize.

## [12.0.3] — 2026-07-20 — "check what you actually ship"

### Fixed
- The pipeline-health alert linked to `actions/workflows/radar.yml`, which
  hasn't existed since the 8.0.0 open-core cutover (only `radar.yml.disabled`
  remains) — a broken link inside the exact message meant to help diagnose a
  broken pipeline. Now points at `sync.yml`, the workflow that's actually
  live in this repo, with a note to check `axonos-radar-core`'s own Actions
  if the engine itself is the silent one.
- CI's schema check for `data/signals.json` looked for that file in the
  checkout and always found nothing — `build_signals.py` is explicit that
  it's "deploy-time and pure ... commits nothing," so the file never exists
  there. The check always printed "skip" and never actually validated
  anything. CI now builds signals.json the same way the real deploy does
  and validates that output, matching the coverage `trajectory.json` (which
  *is* committed) already had for real.

## [12.0.2] — 2026-07-19 — "the second click"

### Fixed
- In-page tab links (the "Where to start" cards' `#axonos`/`#builders`/etc.
  anchors) only worked on a fresh page load. `location.hash` was read once,
  at load time, with no `hashchange` listener — so clicking one of these
  links after the page was already open changed the URL but never called
  `switchView()`, and the target tab silently stayed hidden. The read is now
  wrapped in `applyHash()` and re-run on every `hashchange`, so the same
  links work whether they're the first thing you click or the tenth.

## [12.0.1] — 2026-07-19 — "the documentation catches up"

Four fixes, none of them architectural — the pattern common to all four is
that the code had already moved on and the prose describing it hadn't.

### Fixed
- `SECURITY.md`'s Scope and Hardening sections still named `scripts/radar.py`,
  removed at the 8.0.0 open-core cutover; both now name the files that
  actually do the work today (`sync_engine_data.py`, `validate_payload.py`).
- `docs/THREAT_MODEL.md`'s Accepted Risks still described `assets/app.js` as
  rendering card content via `innerHTML` from escaped strings. That was true
  once; the codebase has carried zero `innerHTML` calls (all `textContent`)
  for several releases. The stale entry is removed rather than corrected in
  place, since the risk it described no longer exists.
- CI's schema validation step checked `data/radar.json` against
  `data/radar.schema.json` and stopped there — `data/signals.schema.json`
  and `data/trajectory.schema.json` are shipped and advertised in the API
  index, but nothing ever validated live data against either. Both are now
  actually enforced, not just pointed to.
- `validate_payload.py`'s invariant gate was hardcoded to payload versions
  `(3, 4)`. The live payload has been on version 5 for some time, which means
  every v3/v4 invariant — required `evidence_tier`/`inclusion_reason`, and
  all four `counts.*` reconciliation checks — has been silently skipped on
  every run, with no warning and a green check mark throughout. Verified
  directly against live production data before extending the known-version
  set: 120/120 projects still carry both legacy fields, and all four counts
  reconcile, so version 5 is added to the known set rather than exempted from
  checking. Any future unrecognized version now fails the build loudly
  instead of silently skipping the invariants it doesn't know how to check.

## [12.0.0] — 2026-07-16 — "Badges"

### Added
- **A live scored badge for every project** — `badges/<owner>/<repo>.json`,
  a shields.io endpoint carrying the project's BRS and relevance tier, derived
  from the engine's last scan. Never hand-granted; refreshes with the map
  (`cacheSeconds: 10800`). `badges/index.json` catalogs every badge with
  ready-to-paste Markdown; **Copy badge** on each evidence ledger does the same
  in one tap. Guide: [docs/BADGES.md](docs/BADGES.md).
- **Trajectory groundwork** — the engine now persists per-project time series
  (`data/trajectory.json`: BRS, stars, health per scan; 96-point window,
  45-day retention), schema'd and pre-cataloged in the API front door. History
  accrues from 2026-07-16; nothing is backfilled.
- The README's Ecosystem Intelligence dashboard re-rendered from the current
  dataset.

### Fixed
- Scheduled site deploys were inert (the deploy job's event guard predated the
  schedule trigger); the safety clock now deploys.
- The publish-token preflight gained a write probe (an unreferenced git blob),
  catching read-only fine-grained tokens before the publish step reports 403s.

## [10.0.0] — 2026-07-16 — "Feed"

The map becomes a Data API anyone can build on — with a front door that cannot
promise what the deploy does not carry.

### Added
- **`data/api.json`** — the machine-readable index of everything the radar
  publishes: every endpoint with its kind, stability grade, schema pointer, and
  byte size; the freshness contract (engine cron → sync → deploy); CORS and
  caching conventions; the licensing terms. Built at deploy time by walking the
  assembled artifact, so an endpoint is listed only if the file exists.
- **`data/signals.schema.json`** — JSON Schema for the signals feed, beside the
  existing `radar.schema.json`; the live payload validates against it in CI.
- **`data/projects.csv`** — the map's core columns, flat (RFC 4180), for
  spreadsheets and BI, beside the NDJSON stream. Column order is part of the
  contract.
- **`docs/API.md`** — the human contract: endpoints, freshness, conventions,
  stability policy, quick starts (curl / pandas / fetch), licensing. The free
  tier is free with attribution; licensed feeds, SLAs, and custom slices for
  funds and labs via connect@axonos.org.

## [9.0.0] — 2026-07-16 — "Signals"

The map stops waiting to be looked at, and starts being able to reach the reader.
And the pipeline that feeds it no longer depends on a single credential.

### Fixed
- **The map had been frozen for four days while everything looked busy.** Every
  scheduled scan produced good data; the engine's run then failed on one step —
  the cross-repo publish — and the *next* step, which persists the engine's own
  state and needs no token at all, was skipped by the implicit `if: success()`.
  So a single broken credential froze both copies at once and nothing said why.
  The engine now persists its state **before** the cross-repo hop, and this repo
  **pulls** the engine's published data on its own schedule with its own
  `GITHUB_TOKEN` (`scripts/sync_engine_data.py`, `sync.yml`) — a path that has
  no cross-repo credential to expire or mis-scope. Both paths may run; whichever
  lands first wins and the other skips on identical content.
- **Scheduled runs get dropped.** GitHub silently skips schedules under load, and
  a single tick can vanish. Sync runs on two staggered ticks; a redundant tick
  costs one conditional GET when the data is already current.

### Added
- **Signals** (`data/signals.json`) — what changed this week: **new**, **rising**,
  **cooling**, each carrying the measured evidence that produced it (7-day star
  velocity, first-seen date). Ids are derived from kind + project + ISO week, so
  a fact keeps one identity for the week it is true and a reader is never
  re-alerted on the same thing.
- **Feeds per slice** — `feeds/signals.xml` (everything), `feeds/new.xml` (new
  BCI projects only), `feeds/rising.xml` (momentum only). RSS 2.0, stable guids.
- **A watchlist on the Stats page** — the Signals panel filters by kind and by
  modality, entirely client-side, and links every slice's feed.
- **The digest keeps exactly one issue.** A janitor closes duplicate digests and
  retires bot issues from an older format whose numbers are frozen in the past,
  each with an explanation and a pointer to the live one. It never touches a
  human's issue, and never the health monitor's alert.
- **The publish token now says why.** A preflight (in the engine) identifies the
  token, whether it can see the target, whether it has push, and whether a branch
  ruleset would refuse the write — turning an opaque `403` into an instruction.

## [8.1.0] — 2026-07-16 — "Dashboards, live"

The Stats page becomes the live dashboard the generated report already was — and
the site can deploy the engine's data again.

### Fixed
- **The site never deployed the engine's scans.** `pages.yml` waited on
  `workflow_run` from "AxonOS Radar" — a workflow that lives in *this* repo and
  was retired in the 8.0 open-core cutover, so the trigger could never fire
  again. Data commits carry `[skip ci]`, which deliberately suppresses the push
  trigger, so nothing deployed them: the engine published, the site stayed
  frozen. Cross-repo `workflow_run` is not possible, so deploys now run on a
  clock (`47 */3 * * *`, ~30 min after the engine's scan lands), alongside the
  existing push and manual triggers.

### Added
- **The Stats page is a live dashboard** — rendered client-side from the
  published `radar.json`, zero dependencies, matching the generated report:
  - **Signal-chain coverage** — modality × stage heatmap, empty cells (the
    field's openings) counted and called out.
  - **Relevance distribution** — the BRS histogram with the gate at 40 and the
    mean.
  - **Standards & interoperability** — which standards win, how many projects are
    wired to each, with the interop-link count.
  - **Ecosystem health** — maturity bands and the median.
  Until now the Stats page used none of the v7 engine's output — no BRS, no
  coverage matrix, no standards graph — so it showed a pre-v7 view of a v8 map.

### Changed
- **ROADMAP.md rewritten to reality** — it still announced v7.1 as "next" and
  v8.0 as "under discussion", both long shipped. It now carries the full arc to
  v17 with honest status, and the README roadmap marks 7.2 / 8.0 / 8.1 shipped.

## [8.0.1] — 2026-07-15 — "Open-core, fixed"

Fixes a regression introduced by the 8.0.0 slimming: three **showcase** scripts
were removed along with the engine, breaking the site deploy.

### Fixed
- **Site deploy was broken.** `pages.yml` calls `build_ecosystem_manifest.py`
  and `build_exports.py` at deploy time, and `health.yml` calls
  `health_check.py` — all three were deleted in 8.0.0, so Deploy Pages failed
  and the live site could not update. They are restored: they are showcase
  utilities, not scoring IP — they only transform data that is already public
  (the live badge, the `projects.ndjson` export) or monitor the published
  pipeline. The slimming line is now drawn by *what a script does*, not by what
  its name resembles.
- **The health monitor could spawn duplicate alert issues.** `find_alert()` read
  any non-200 (e.g. a 403 from a rate-limited token) as "no alert exists" and
  opened another one — the same class of bug just fixed in the stats digest.
  Now any failed lookup skips the bookkeeping instead of duplicating; the
  diagnosis is still printed.

### Added
- **CI gate: workflows may only reference files that exist.** 8.0.0 passed CI
  while the deploy broke, because CI only ran what CI itself listed. Every
  `scripts/*` referenced by an active workflow is now checked to exist — this
  exact failure would have been caught before merge.

## [8.0.0] — 2026-07-13 — "Open-core"

Completes the open-core split. The scoring/discovery engine now lives **solely**
in the private repository; this showcase is the open map, its data, and its UI.

### Changed
- **The relevance/scoring engine is removed from this repository.** All scoring,
  discovery, enrichment, and report-generation code (`relevance`, `domain`,
  `radar`, `enrich`, `signals`, `ecosystem`, `build_*`) now lives only in the
  private engine and is proprietary. This repo is a pure showcase: the
  interactive radar, the ecosystem map, the published dataset, and the open
  interop vocabulary.
- **Licensing is now unambiguous.** The MIT licence covers exactly what remains
  (UI, published data, open utilities) and no longer overlaps the proprietary
  engine. The engine's history remains in git — MIT is not retroactively
  revoked — but future engine development is private-only.
- **CI slimmed to the showcase.** Engine unit tests and the report-build job are
  retired; frontend, data-integrity, security, and release-hygiene gates remain.

### Kept open (transparency)
- The interop vocabulary (`data/interop-vocab.json`) and its matcher
  (`scripts/interop.py`), the seed config (`data/seeds.json`), the data schema,
  and every published dataset remain open. The evidence ledger on every project
  stays fully public — transparency is the moat, not obscurity.

## [7.1.0] — 2026-07-13 — "Legible"

Makes the v7 engine's transparency visible, opens the ecosystem to contributors,
and completes the open-core split — the engine now runs privately and publishes
only its output to this showcase.

### Added
- **Per-card BRS badge + inline evidence ledger** — every project card carries
  its BCI Relevance Score; tapping it unfolds the *signed evidence ledger* (each
  `+`/`−` signal with its plain-language reason) without leaving the card.
  Keyboard-accessible, valid nesting, `aria-expanded` wired. The transparency
  differentiator, made tangible.
- **Relevance (BRS) sort** in the sort bar.
- **BCI Ecosystem Intelligence dashboard** — a dense, investor-grade one-page
  read-out rendered entirely from radar data (relevance distribution, signal-
  chain coverage, standards & interoperability, health, momentum, players,
  composition, builders), embedded in the README.
- **Public roadmap scaffold** — `ROADMAP.md` mirroring the board, structured
  issue templates (feature/bug with Area/Priority auto-labels), a label-taxonomy
  script, and the v7.2 dashboard reference images.
- **Grande-Standard README** — rebuilt and updated for the v7 engine: full
  capability coverage, the badge/VC-diligence funnel, and the roadmap to v17.

### Changed
- **Open-core cutover** — the private engine (`axonos-radar-core`) is now the
  **sole scanner**; this repo's own scan workflow is retired, ending a two-writer
  race on `main`. The weekly digest keeps updating via `stats-issue.yml`.
- `sanitizeData`/`sanitizeProject` now carry `brs`, `relevance_tier`, and
  `relevance_ledger` through to the UI.

### Fixed
- The scheduled pipeline persists state via the Contents API (Verified commits)
  so it satisfies the signed-commit ruleset and history accumulates correctly.

## [7.0.0] — 2026-07-11 — "The Relevance Engine"

A major release that changes *what the radar is*: from a broad discovery list
that leaked generic ML, to a scored, auditable map of the BCI ecosystem as a
connected system.

### Added
- **BCI Relevance Engine** (`scripts/relevance.py`): a scored, auditable
  inclusion gate — the **BCI Relevance Score (BRS, 0–100)** — built from a
  *signed evidence ledger*. Every positive and negative signal is recorded with
  its points and a plain-language reason. The decisive idea is *disambiguation
  by anchor*: `neural` counts as neuroscience only next to a neuro anchor
  (interface/signal/decoding/implant…); `neural network` with no anchor is
  negative evidence. Each project now carries `brs`, `relevance_tier`, and
  `relevance_ledger`. Unit tested in `tests/test_relevance.py`.
- **Domain intelligence** (`scripts/domain.py`): per-repo `facets`
  (modality / paradigm / signal-chain stage / standards) plus two ecosystem
  views published in `radar.json` — `coverage_matrix` (modality × pipeline-stage
  grid, exposing coverage deserts) and `standards_graph` (each standard, the
  repos that speak it, and the count of interoperability edges). Unit tested in
  `tests/test_domain.py`.
- **Map tab** in the UI: a coverage heatmap and a standards-interoperability
  view — the field's shape and its connective tissue, computed from evidence.

### Changed
- Inclusion is now decided by the BRS gate instead of the old boolean topic +
  keyword test. Generic ML — even ML that says "neural" — is filtered out, with
  the reason recorded per rejected repo.
- `radar.json` schema bumped to **version 5** (adds `brs`, `relevance_tier`,
  `relevance_ledger`, `facets`, `coverage_matrix`, `standards_graph`).
- `docs/METHODOLOGY.md` rewritten around the Relevance Engine and Domain
  Intelligence; legacy evidence fields documented as superseded but retained.

### Fixed
- A committed data purge removed 58 off-topic repositories (PyTorch, TensorFlow,
  Keras, spiking-NN ML libraries, neuroimaging pipelines, an AI-agent memory
  project, and other generic-ML noise) that the old boolean had admitted,
  leaving ~62 genuine BCI/neuro projects.

## [6.0.1] — 2026-07-10 — the last mile, instrumented

### Added
- **Release workflow** (`.github/workflows/release.yml`): pushing a `v*` tag
  now creates the GitHub Release automatically — body extracted from the
  matching CHANGELOG section, and the **Latest** badge is claimed only when
  the tag matches the committed `VERSION`, so backfilling a historical tag
  (token-free, via *Run workflow* in the Actions tab) can never steal it.
  Closes the recurring "sidebar still says v5.0.5" class at the mechanism
  level: the sidebar shows Release *objects*, and until now creating them
  depended on a human remembering a token-bearing curl.
- **HTML self-heal**: the deploy now publishes `data/build.json` and injects
  `<meta name="radar-build">` into every deployed page; on boot `app.js`
  compares the two (no-store) and, on mismatch, navigates once per build per
  session to `?b=<build>` — a document URL the cache has never seen. This
  closes the one caching layer `?v=` asset stamping could not cover: the
  HTML document itself surviving in mobile session-restore and showing an
  old footer version over fresh data.

### Notes
- No data-model changes; payload contract stays v4.

## [6.0.0] — 2026-07-10 — "Solid Ground"

### Added
- **Foundation signals.** Seven checkable repository facts per project —
  licence file, README, CONTRIBUTING, code of conduct, root `CITATION.cff`,
  root `SECURITY.md`, and CI workflows — sourced from GitHub's community
  profile, contents and workflows APIs. Shown as an `n/7` chip with a full
  per-check breakdown; **honest-absence rule**: indeterminate evidence means
  no read-out at all, never a fabricated zero. The UI recomputes the count
  locally and never trusts a shipped number.
- **Interop tags — "who speaks to what".** Word-boundary detection of 20
  protocols, formats, toolkits, hardware families and runtimes (LSL,
  BrainFlow, BIDS, EDF, MNE, EEGLAB, OpenViBE, Timeflux, OpenBCI, Emotiv,
  Neurosity, g.tec, Muse, ADS1299, FreeEEG, ROS, Unity, Arduino, ESP32, BLE)
  from topics/description/homepage against a committed, reviewable vocabulary
  (`data/interop-vocab.json`). Zero extra API calls; one-tap "Speaks" facet
  filter; a Foundation sort joins the sort bar; both join the permalink hash.
- **The radar as a data product.** New deploy-time `data/projects.ndjson`
  (one project per line, key-sorted — pandas/jq/DuckDB-ready), an endpoints
  table in the Methodology view, and the JSON Schema extended to the new
  fields.
- **Documentation-coverage gate.** `scripts/check_methodology.py` fails CI if
  any shipped signal, interop tag or endpoint is missing from the Methodology
  view, `docs/METHODOLOGY.md`, or the UI label map — "nothing on a card is
  unexplained" is now enforced mechanically.

### Changed
- Payload contract bumped to **version 4** (fully backward-compatible: every
  new field is optional; version 3 payloads still validate). The validator
  gains fabrication guards for interop (unknown tags rejected) and foundation
  (count must equal its own booleans); `counts` gains `interop_tagged` and
  `foundation_checked` with cross-checked consistency.
- Enrichment performs four additional polite API calls per repo (community
  profile, `CITATION.cff`, `SECURITY.md`, workflows) inside the same shared
  rate-limit budget and headroom reserve.

### Notes
- Health scoring is deliberately **unchanged** — Foundation is a separate,
  factual axis, so historical health series remain comparable.

## [5.2.0] — 2026-07-09

### Added
- **One organism: the ecosystem manifest.** A hand-maintained canonical registry
  (`data/ecosystem-registry.json`) now describes every AxonOS account and
  repository — the radar, the Neural Boundary Game, the profile front door, and
  the seven AxonOS-org engineering repos — with its role and stage. At every
  deploy, `scripts/build_ecosystem_manifest.py` joins the registry with the
  live scan and publishes `data/ecosystem.json`: roles, links, live Health
  signals for radar-tracked repos, and the canonical voluntary-support block.
  Deploy-time generation means the manifest is always in sync with the deployed
  dataset and costs zero bot commits.
- **The live pulse badge.** `data/badge-ecosystem.json` is a shields.io
  endpoint document regenerated at every deploy ("120 projects · health 79").
  Any repository in the ecosystem can embed one line of Markdown and carry the
  organism's live heartbeat.
- **Support page (`support.html`).** A first-class voluntary-support surface:
  the canonical Dogecoin address with copy button, wallet-URI link, QR code,
  on-chain explorer link — and the plain terms mirrored verbatim from
  `CRYPTO_PAYMENT_TERMS.md` (voluntary, no entitlements, irreversible,
  commercial licensing stays a written-agreement/fiat channel). Linked from the
  landing and stats navigation and from a new README section.
- **Sponsor button.** `.github/FUNDING.yml` points the repo's Sponsor button at
  the support page.
- **Funding-consistency CI gate.** One DOGE address, single-sourced from the
  registry, must appear byte-identical in `app.js`, `support.html` and
  `FUNDING.yml`, must pass Base58Check (version 0x1E), and no foreign D-address
  may appear on any of those surfaces. A typo'd or swapped address can no
  longer ship.

## [5.1.1] — 2026-07-08

### Fixed
- **Stale interface after deploy ("two versions at once").** The HTML linked
  `assets/app.css` / `assets/app.js` with no version query, so GitHub Pages'
  long-lived asset cache kept serving the previous CSS/JS under freshly deployed
  markup — the site looked like it was still on the old release. The Pages
  workflow now stamps every shipped CSS/JS URL with the deploy commit SHA
  (`app.css?v=<sha>`), so a new build always has new asset URLs and the browser
  can never show a stale interface again. Source files stay clean; only the
  deployed copies are stamped.

### Changed
- **Deploys are now immediate on source pushes, not just scans.** `pages.yml`
  gained a `push: main` trigger alongside the existing post-scan `workflow_run`.
  Scan commits carry `[skip ci]` (which suppresses the push trigger), so the two
  paths never double-fire: scans deploy via `workflow_run`, feature commits
  deploy via `push` without waiting for the next 3-hourly scan. Queue-only
  concurrency (`cancel-in-progress: false`) is unchanged, so nothing is ever
  cancelled.
- **Public roadmap on the home page.** Added a prominent annotated link to the
  AxonOS project board (`github.com/users/AxonOS-BCI/projects/1`) so visitors
  can follow what's shipped, in progress, and next — in the open.

## [5.1.0] — 2026-07-08

### Added
- **Ecosystem Health signals — the radar's flagship read-out.** Every project
  now carries a transparent `signals` block: a 0–100 **Health** score plus six
  sub-scores (Maintenance, Momentum, Adoption, Team, Licence, Doc signals),
  computed **only from real public GitHub metadata the scan already fetches** —
  no extra API calls, no surveys, no self-assessment. The overall score is a
  weighted mean of *only the dimensions that could be measured* for a repo;
  anything unmeasurable is **left out rather than guessed**, and a repo that was
  not enriched this cycle is flagged `search-only`. Deliberately **not** scored:
  conformance, security posture, and test quality — none can be read reliably
  from search metadata, so scoring them would be fabrication. AxonOS is scored
  by the exact same rules as every other project (its own repos land in the
  "developing" band — the score is neutral by construction). New module
  `scripts/signals.py`, a full published formula in `docs/METHODOLOGY.md`, JSON
  Schema coverage, validator enforcement, and 13 unit tests.
- **Health meter in the UI.** Each card shows a band-coloured Health bar with
  the score and a plain band label (strong / solid / developing / early); the
  full per-dimension breakdown and verifiable badges (`osi-licensed`,
  `actively-maintained`, `has-releases`, `multi-contributor`) live in the
  accessible tooltip. New **Health** sort option, encoded in shareable `#`
  permalinks. All rendered through DOM-safe code — zero `innerHTML`, strict CSP
  intact.
- **"Where to start" onboarding.** A persona-based entry point (Researcher /
  Engineer & contributor / New to neurotech / Building something), each a short
  path of real links into the map, the report, Discussions, and the add-project
  flow. Lowers the barrier for newcomers who don't know which thread to pull.
- **Field-wide health counts** (`counts.health_strong`, `counts.health_median`)
  in `radar.json` and `status.json`.

### Fixed
- **`publish_data.py` no longer fails silently.** A failed Contents-API PUT for
  a tracked file (radar data, history, feed, report, status) now collects the
  error and exits non-zero, so a broken token or API outage surfaces as a red
  step instead of a green no-op.
- **Dead unreachable code removed** from `validate_payload._is_safe_github_url`
  (a second `try` after an unconditional `return`), and the validator now
  enforces the new `signals` block: out-of-range scores or an unknown `basis`
  are rejected — a fabricated health read-out cannot pass the gate.

### Changed
- The Dogecoin support suggestion is now **Đ 1000**, framed as powering a full
  refresh-and-rescore cycle for the whole field. The radar still has **no
  paywalled features** — funding keeps the map, stats, health signals and
  report free for everyone.

## [5.0.5] — 2026-07-05

### Fixed
- **Ecosystem "shared maintainers" was nonsense.** The graph counted the
  owning account (`AxonOS-BCI`) as a contributor, so every repo appeared linked
  to every other "via AxonOS-BCI", and that org account showed up under
  "Building across the stack" as a person spanning 6 repos. Organisation and
  owner accounts are now filtered out of the contributor graph — only real
  humans count. Links whose shared list becomes empty are dropped.

### Changed
- **Ecosystem UX redesigned.** "Building across the stack" and "Shared
  maintainers" are now structured card grids (avatar · name · repo count for
  people; repo-pair · "via …" for links) instead of a vertical run of
  "repo ↔ 1 repo" rows. Both blocks are **omitted entirely when they carry no
  real signal** — no empty filler — while the owner constellation still shows.
## [5.0.4] — 2026-07-05

### Fixed
- **AxonOS was missing from its own radar.** The ecosystem anchor-fetch used a
  workflow's built-in `GITHUB_TOKEN`, which is an installation token scoped to
  the running repository (`AxonOS-BCI`). Requests to the `AxonOS-org` repos
  answered non-200 even though those repos are public, so every anchor was
  silently skipped (`continue`) and AxonOS never appeared — including under the
  "Protocols & OS" filter. Two-part fix: (1) `_get` now retries **without** the
  token on any non-200 when a token was used — public metadata needs no auth,
  so cross-org resolution succeeds; (2) if the API is unreachable entirely, the
  anchor is still **included from its curated entry** (role/note/group), so a
  flagship project is never dropped from its own radar. Degraded anchors carry
  no fabricated live figures — stars/language/pushed_at fill in on the next
  reachable scan, and are reported via `anchors_degraded` in status.

### Changed
- Version strings unified at 5.0.4 (CI gate).
## [5.0.3] — 2026-07-04

A flagship release: the radar now shows **its own field**, maps the **people
and connections** behind the ecosystem, and the Pages deploy is fixed at the
root so it stops failing.

### Added
- **AxonOS in its own radar.** Ecosystem anchor repos (the AxonOS kernel,
  protocol, consent, standard, signal-pipeline, and this radar) are now
  force-included **by name** via `scripts/ecosystem.py` — so they appear even
  with zero stars or no topics — flagged `ecosystem: true` with an honest role,
  **never a fake star boost**. A flagship radar must not omit its own project.
- **Ecosystem constellation** (`#ecosystem` on the map): the maintaining
  org/user profile (type, location, followers, site), the **people** behind it
  (public org members), **contributors who build across multiple ecosystem
  repos**, and **shared-maintainer links** between repos — all live from the
  public GitHub API, every fact source-backed, nothing fabricated.
- **Ecosystem project cards** carry a cyan ◈ AxonOS badge and a one-line role.
- Payload gains an `ecosystem` graph (`owners`, `links`, `key_people`) and
  `ecosystem_count`.

### Fixed
- **Pages deploy failing repeatedly ("Unable to cancel deployment as it's
  finished").** Root cause: `concurrency.cancel-in-progress: true` plus
  multiple triggers made overlapping deploys cancel each other, and a deploy
  that finished mid-cancel errored the whole run. Definitive fix: a **single**
  automatic trigger (`workflow_run` after the scan), **`cancel-in-progress:
  false`** so deploys queue instead of cancelling, and removal of the second
  in-job "retry" deploy step that was itself a second deployment. One clean
  deploy per scan.

### Changed
- Version chips and all version strings unified at 5.0.3 (CI gate enforces it).

## [5.0.2] — 2026-07-04

### Fixed
- **Duplicate donate blocks removed** — a legacy static `.donate` card lived
  inside the AxonOS tab while a second CSS rule collided with the new one; the
  overlap skewed the AxonOS-view text. There is now a single JS-rendered card.
- Version strings unified at 5.0.2 across VERSION, README (badge + bibtex),
  CITATION, CHANGELOG, docs and both page footers (a CI gate enforces this).

### Changed
- **Premium Dogecoin support card**: gradient-ring frame, gold Ð medallion,
  "Dogecoin" pill, Ð 100 suggestion, monospace address with one-tap Copy, and
  a clean vertical stack on mobile. Real DOGE address wired in (card is live).
  Wording makes the free-for-everyone stance explicit — no paywalled features.

## [5.0.1] — 2026-07-03

### Fixed
- **Deploy race eliminated**: each scan used to trigger *two* competing Pages
  deploys (push on `data/**` + `workflow_run`); the loser surfaced as a red ✗.
  Push paths now cover only human-edited site files — the scan's own commits
  are handled solely by `workflow_run`. One scan, one deploy.
- **Deploy retry**: `deploy-pages` occasionally answers "try again later" —
  the workflow now waits 25 s and retries once before going red.
- Stale version strings refreshed: docs (SBOM, THREAT_MODEL) said 4.3.0.

### Added
- **Visible version chip** in the footers of the map and stats pages —
  instantly distinguishes a cached page from the live release. The CI version
  gate now checks both pages too.
- **Dogecoin support card** on the map (opt-in): suggested Ð 100, address with
  one-tap Copy, doge-gold styling. Hidden until an address is configured at
  publish time; funding keeps every feature free for everyone — the radar has
  no paywalled functionality.

## [5.0.0] — 2026-07-03

A major release: faster and fairer pipeline, a shareable instrument of a UI,
DOM-safe rendering everywhere, and a root-cause fix for the red
`pages-build-deployment` runs.

### Added
- **`pages.yml`** — the site now deploys as **one Pages artifact per scan**
  (triggered by radar completion / site-file pushes / manual dispatch), with
  `concurrency: cancel-in-progress`. Kills the superseded-Jekyll-build ✗ storm
  at the root. One-time setup: Settings → Pages → Source = "GitHub Actions".
  `.nojekyll` added for the interim.
- **Parallel enrichment** — stdlib `ThreadPoolExecutor` (4 workers) with a
  shared, locked rate-limit budget; same per-request politeness, ~3–4× less
  wall time. Budget stop and 429 handling are thread-safe.
- **Saturated-topic recovery** — one bounded `sort=stars` page per saturated
  topic recovers big-but-quiet classics through the exact same `ingest()`
  relevance/dedup/exclusion gate as the main scan (`recovered_by_stars_pass`
  in status).
- **`data/weekly.json`** — server-computed movement digest (deltas vs ~7 days,
  top risers/fallers, entrants); consumed by the map strip, the stats page and
  the report so all three show identical numbers. Publisher normalises it and
  commits only on meaningful change.
- **Owner-enriched Builders** — account type (ORG/USER) and follower counts on
  the Builders board (UI, stats, report), bounded to the builders list
  (`owners_enriched` in status).
- **History `meta.categories`** — per-category sizes per snapshot; powers new
  category **trend arrows** in the report once two snapshots carry it.
- **UI v5** — This-week strip; evidence-tier filter chips (L3/L2/L1/L0);
  **↓ Falling** quick filter; **licence markers** (`⚠ no licence` /
  `⚠ licence unclear`) on cards; density toggle; `Esc` clears search; loading
  shimmer; all state (incl. tiers/falling/density) in shareable `#` permalinks.
- **Stats v5** — **Momentum chart** (rising vs falling per snapshot) and a
  This-week line; builders show ORG/USER + followers.
- **Six-job CI** — data-integrity, python-quality, frontend (incl. a
  **functional jsdom UI smoke**), report-build, security (blocking bandit,
  pinned-SHA gate, secret scan, CRLF), release-hygiene (required files,
  version consistency across VERSION/badge/bibtex/CITATION/CHANGELOG, licence
  sanity).
- **Full JSON-Schema contract** — typed properties for every project field,
  `html_url` pattern requires `owner/repo`, `quality_flags` enumerated
  (incl. `unclear_license`), builder `owner_type`/`followers`.

### Changed
- **Every action pinned to verified latest SHAs with truthful labels**:
  checkout v7.0.0, upload-artifact v7.0.1, configure-pages v6.0.0,
  upload-pages-artifact v5.0.0, deploy-pages v5.0.0. (The old `f43a0e5` pin
  was actually checkout **3.6.0** mislabelled "# v4" — fixed; supersedes
  Dependabot PRs #3/#4.)
- `min_stars` 1 → **2**; hyphen variants added for multi-word neuro keywords
  (`brain-machine`, `spike-sorting`, `motor-imagery`).
- `axon_relevance_for` uses **word-boundary** keyword matching ('api' no
  longer fires inside 'rapid').
- Scan workflow timeout 30 → 45 min; forensic artifact step renamed to state
  its 90-day retention explicitly.

### Fixed
- **stats.html was styling-dead under its own strict CSP**: the page declared
  `style-src 'self'` *and* carried an inline `<style>` block, which compliant
  browsers block. Styles extracted to `assets/stats.css`.
- README bibtex citation said `3.4.0` while the project was at 4.3.0 — now CI
  enforces version consistency everywhere.
- `_funding_url` accepted any string starting with "http" (incl. `http://`
  and junk like `httpevil`) — now strict `https://` + urlparse validation.
- Dead `import base64` removed; `__showErr` inline `cssText` moved to a CSS
  class; health-check now cache-busts Pages reads (defeats stale-CDN false
  alerts); CoC points security reports to SECURITY.md.

## [4.3.0] — 2026-07-02

Momentum both ways, a self-diagnosing pipeline, and an audit-driven hardening
pass. The report becomes a motion picture of the field.

### Added
- **Report — How the field moved:** headline weekly deltas (projects, stars, active, rising) computed from `data/history.json`.
- **Report — Star trajectories:** real per-project star curves across snapshots for the top of the field.
- **Report — Declining:** projects losing stars, shown with the same prominence as risers; `falling` flag (`stars_delta_7d ≤ −2`), `counts.falling`, red Δ7d in the full table and a ↓ card badge on the map.
- **Report — New entrants, Category health matrix, Licence posture** (declared / NOASSERTION-unclear / missing), **Pipeline health panel** driven by `data/status.json`.
- **`data/last_run.json`:** machine-readable outcome of every run, including abort reasons (topic-failure ratio, corrupt state files) — published like the rest of the data.
- **Health monitor** (`health.yml` + `scripts/health_check.py`): twice-daily freshness check of the *published* Pages data; maintains a single self-closing alert issue (bot-author verified, marker-collision safe).
- **Data snapshots:** every scan uploads a 90-day workflow artifact of `data/*.json` + `feed.xml` (disaster recovery independent of git history).
- **Frontend ingress validation:** `sanitizeData()` type-coerces every rendered field and allowlists URLs before any DOM work; radar tooltip now builds via `textContent`.
- **`community_active`** (pushed *or* updated ≤ 30d) alongside the stricter push-based `active`.
- **Docs:** `docs/THREAT_MODEL.md`, `docs/INCIDENT_RESPONSE.md`, `docs/RETENTION.md`, `docs/SBOM.md`; METHODOLOGY sections for falling, active semantics, archived exclusion, the enrichment buffer, search-cap honesty and category tie-breaking.
- **Dependabot** for pinned GitHub Actions; `noscript` fallbacks on both pages.

### Changed
- **Fairer ranking:** enrichment now covers a buffer of cap + 30 before the final cut, so a project just under the base-score line can earn its way in on real signals (top-N sampling-bias fix). Archived/disabled repos found during enrichment leave the ranking (`excluded_archived` in status).
- **Deterministic category ties:** score → priority (specificity) → alphabetical.
- **Licence semantics:** `NOASSERTION` is now `unclear_license`, distinct from `missing_license`.
- **Refresh cadence texts** unified to the actual every-3-hours schedule (README, UI, report).
- **Status:** adds `rate_limit` start/end budget, `search_saturated_topics`, `falling`, `community_active_30d`, `excluded_archived`.
- **Workflow:** publish steps no longer run on failed scans (`always()` removed — a failed scan must look failed); job timeout 15 → 30 min.
- `publish_data.py` change detection now includes `builders`; `stats` issue lookup trusts only bot-authored issues.

### Fixed
- Dead unreachable branch in `_is_safe_github_url` (pipeline and its duplicate risk).
- Future-dated `first_seen` is clamped at bootstrap, healed on read, rejected by `validate()`, skipped by the RSS feed, and gated in CI.
- `stats/commit_activity` HTTP 202 (GitHub still computing) is retried once and then recorded as *pending*, never as false "no activity".
- Enriched `homepage` values are kept only when they are `http(s)` URLs.
- Exclude lists in `seeds.json` are normalised (case, slashes, `@ref`) before matching; explicit fork guard after search.
- `_kw_pattern` LRU cache widened 8 → 64 (regex thrash with many keyword sets).

## [4.2.0] - 2026-07-01
### Fixed
- Reach x engagement quadrant: labels are now placed greedily (highest score first) and any label that cannot sit clear of the others is dropped, so dot labels no longer overlap in dense regions. All dots are still shown.
### Changed
- Full-field table now shows the enrichment columns (Team, Downloads, Rel., Activity) only once enrichment data exists, instead of a column of em dashes before the first enriched scan. The columns appear automatically after enrichment runs.

## [4.1.0] - 2026-07-01
### Changed
- Report chart system rebuilt for legibility. Horizontal bars (evidence tiers, languages, leaderboards, distributions) now render as HTML+CSS with pre-defined width classes instead of tiny-viewBox SVG, so labels and values are crisp and a consistent size at any width instead of scaling with the container and colliding. The reach x engagement quadrant and the category donut now use real-pixel viewBoxes so their text renders at its literal size.
### Added
- New "Distribution" section: projects per star band and last-push recency, as two horizontal-bar charts.
- Visible separators in the report header meta line.

## [4.0.0] — 2026-07-01

Serious ETL + professional visualization. The scan gets real depth and the report stops being a summary and becomes a dashboard.

### Added — ETL & enrichment
- **Paginated discovery** — up to 100 results per topic (GitHub's 1000-result cap respected), so broad topics are no longer truncated to a handful.
- **Per-repository enrichment** pulling real GitHub signals: contributor counts (team size), release-asset **download** totals (adoption), a 52-week **commit-activity** histogram (maintenance), declared **funding channels** (FUNDING.yml), true watchers, size, open issues, homepage and archived state. Rate-limit aware; never fails a scan.
- **Multi-signal scoring** — log-scaled stars + recency + enriched terms (downloads, contributors, activity, releases), published and applied identically to every project. AxonOS is never boosted.
- **Honest curated overrides** (`data/curated.json`) for facts GitHub cannot provide — capital raised, legal domicile — source-cited only, never fabricated, empty by default.
- **`data/status.json`** — per-scan observability (counts, enrichment coverage, archived, totals).

### Added — visualization
- **"Who leads the field"** — Most-starred and Most-built-on leaderboards always; Most-downloaded, Largest-teams and a funding-channels panel once enriched.
- **Enriched full-field table** — Team, Downloads, Releases and a 52-week activity **sparkline** per project; a source-cited capital/domicile badge where available.
- **Richer KPI band** — downloads, contributors, releases and funded counts when data is present.

### Honesty
- GitHub exposes repository **page views only to a repo's own owners**, so views are deliberately never shown rather than approximated.
- Money-raised and domicile appear **only** via the curated, source-cited file.

## [3.7.0] - 2026-06-28

### Added
- **A full analytics report, right in the repo.** A new zero-dependency generator (`scripts/build_report.py`) renders `report.html` — a professional, Visual-Capitalist-style *State of Open BCI* report with a Gartner-style **reach × engagement quadrant**, a category donut, evidence-tier and language breakdowns, momentum and builder tables, and a **complete table of every tracked resource**. It is static, strict-CSP (all styling in `assets/report.css`, charts pre-rendered as inline SVG, zero JavaScript), so it renders anywhere and cannot break. Served one click away at `/report.html`.
- The report is committed to the repo and **regenerated every 3 hours**, so the link is always an exhaustive, current snapshot.
- A prominent **Report** link in the radar's nav and hero.

### Changed
- The refresh cadence moves from every 6 hours to **every 3 hours**. `build_report.py` and the data/issue publishers now run with `if: always()`, so the report and data refresh from committed data even if a discovery scan hiccups.
- Fixed `CITATION.cff`, which had drifted to 3.4.0, to track the release version.

## [3.6.2] - 2026-06-28

### Fixed
- **The live issue now refreshes on every release, and the pile of "skipped" workflow runs is gone.** The issue-publishing workflow was path-filtered, so most pushes marked it *skipped* and never ran it — and a newly-added path-filtered workflow does not reliably fire on its own first push either. `stats-issue.yml` now runs on **every push to main** (no path filter), plus a 6-hourly backstop, plus the manual **Run workflow** button, so the living issue always reflects the committed data.

### Changed
- Discovery (`radar.yml`) no longer has a push trigger; it runs on its 6-hourly schedule and on demand. This removes the *skipped* runs that piled up on documentation-only release commits — a full ecosystem scan never needed to run on those.

## [3.6.1] - 2026-06-28

### Fixed
- **The living stats issue now actually refreshes.** Its publish step was the last action in the discovery job and ran only if `radar.py` succeeded — so a transient GitHub-search hiccup (which exits the pipeline) silently skipped the issue update. The step now runs with `if: always()`, refreshing the issue from committed data regardless of discovery health.

### Added
- **`stats-issue.yml`** — a dedicated, manually-dispatchable workflow that updates the living issue on demand (the **Run workflow** button) and whenever the digest code changes, fully decoupled from the discovery pipeline.

### Changed
- Digest-only edits no longer trigger a full discovery run; they are handled by the new workflow instead.

## [3.6.0] - 2026-06-27

### Added
- **Analytics-grade live issue.** The auto-updating stats issue is now rendered as a Visual-Capitalist-style data report with a **Gartner-style quadrant** and a **category pie**, both drawn with native GitHub **Mermaid** so they render right inside the issue. The quadrant maps **reach** (stars, log) against **engagement** (forks per star) — raw public-GitHub signals only, clearly labelled as a descriptive ecosystem map, not a vision/quality ranking. Dense tables for rising, new, builders, evidence tiers and languages round out the report.

### Security / Reliability
- **Stronger URL validation:** `radar.py` and `validate_payload.py` now verify `html_url` with `urllib.parse` (scheme + exact `github.com` host + path), replacing prefix checks — defence-in-depth against look-alike hosts.
- **No duplicate live issues:** on a GitHub 5xx outage the issue publisher now skips the run instead of falling through and creating a second dashboard issue.
- **Pipeline timeout:** the refresh job gets `timeout-minutes: 15` so a hung request can't idle for hours.

### Changed
- Removed the unused `has_release` field from the data schema (it was never populated).
- New pytest guards the issue analytics (quadrant + pie must render).

## [3.5.0] - 2026-06-26

### Added
- **Roadmap momentum** in the AxonOS view: a stage-segmented progress bar with a live "X shipped · Y in build · Z planned — and climbing" summary, and the workstreams now ordered shipped → building → planned so the roadmap reads as forward motion (counts are computed from the cards, so they stay accurate).
- **Download data** (↓ Data) in the project grid header — exports the current dataset as JSON, client-side, with no inline handlers (strict CSP preserved).

### Changed
- Removed the redundant "Add project" button from the top-right of the nav; the hero already carries a prominent "Add your project" call to action.

## [3.4.0] - 2026-06-26

### Added
- **Citation:** a `CITATION.cff` (so GitHub shows a "Cite this repository" button) and a Citation section in the README with ready BibTeX.
- **Publish-fresh-data action:** a button in the Methodology view that opens the scan workflow so a maintainer can rescan on demand and refresh the live stats issue, plus a direct link to that issue. `radar.yml` gains `workflow_dispatch` for manual runs.

### Changed
- Reworded the project description to stand on its own terms.

## [3.3.0] - 2026-06-26

### Fixed
- **Crash on render** (regression in 3.2.0): the review badge read `quality_flags` as an array, but it is an object — `indexOf is not a function` aborted the card render. It now reads the object correctly (and tolerates either shape).

### Added
- **AxonOS view** — a fourth tab that showcases the engineering roadmap (kernel, consent, protocol, signal pipeline, standard, conformance, radar, research, hardware) as premium cards with honest stage badges, linking to each repository and to the public roadmap board.
- **Dogecoin donation** card with one-tap copy-to-clipboard (no inline handlers; strict CSP preserved).
- **Rising sort** — order the field by 7-day star velocity, alongside Activity / Stars / Newest / A–Z.

### Notes
- All additions are class-based and event-listener-wired, so the fully strict CSP (`script-src 'self'; style-src 'self'`, no `unsafe-inline`) is preserved.

## [3.2.0] - 2026-06-26

Premium-UX release: fully strict CSP, plus a review signal on the cards.

### Added
- **Review badge** on project cards: an `⚠ review` chip for entries the pipeline flagged `possible_false_positive` (the L0/weak matches), so borderline inclusions are visible, not hidden.
- A subtle, staggered card entrance — done entirely in CSS (`:nth-child`), no inline styles.

### Changed
- **Fully strict Content-Security-Policy** on both the radar and the statistics page: `script-src 'self'; style-src 'self'`, with **no `unsafe-inline` anywhere**. All dynamic colours are now applied via CSS classes and the CSSOM (`element.style.setProperty`), which CSP permits, rather than inline `style=` attributes. `stats.html`'s JavaScript was externalised to `assets/stats.js` to complete this.
- CI now enforces the strict CSP (fails if `unsafe-inline` reappears in either page) and checks `assets/stats.js`.

### Security
- Removing `unsafe-inline` from `style-src` (and keeping it off `script-src`) closes the last inline-injection avenue; the card render path was already output-encoded, and is now defence-in-depth complete.

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
