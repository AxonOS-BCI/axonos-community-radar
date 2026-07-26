# AxonOS Radar — data model

`data/radar.json` is a public data contract. Anything that consumes it (the
web UI, the RSS feed, third-party tools) can rely on the guarantees below.
The contract is enforced in CI by `scripts/validate_payload.py`, which is the
executable form of this document.

## Source and posture

The dataset is derived **only** from public GitHub repository metadata returned
by the GitHub topic-search API. No private data, no profile scraping, no
analytics. Inclusion is not endorsement; categories are heuristic; the score is
a discovery signal, not a quality, safety, or clinical rating. See
`docs/METHODOLOGY.md`.

## Top level

| field | type | notes |
|---|---|---|
| `version` | integer | schema version. Current: `5`. `2`–`4` remain valid and are still validated (`scripts/validate_payload.py`'s `KNOWN_VERSIONS`). |
| `generated_at` | string (ISO-8601) | when the file was produced. |
| `snapshot_at` | string (ISO-8601) | the 6-hour slot the scan is aligned to. |
| `min_stars` | integer | minimum stars for inclusion. |
| `counts` | object | `total`, `active_30d`, `new`, `rising`, `builders`, `health_strong`, `health_median`, `interop_tagged`, `foundation_checked`. |
| `projects` | array | the project objects below. |
| `builders` | array | owner-aggregated objects (2+ tracked projects). |
| `coverage_matrix`, `standards_graph` | object | modality×stage and interoperability-standard read-outs — see `docs/METHODOLOGY.md`. |

## Project object

Guaranteed invariants (validated in CI):

- `full_name` — non-empty string, unique case-insensitively.
- `html_url` — **must** start with `https://github.com/`. Any other scheme or
  host (`javascript:`, `http://`, `https://github.com.evil.com/`, …) is
  rejected before publication. This is the primary anti-injection guarantee.
- `description` — string, at most **240** characters.
- `stars`, `forks` — non-negative integers when present.
- `category` — non-empty string from the published taxonomy.
- `topics`, `matched_topics`, `matched_keywords` — arrays when present.
- `stars_delta_7d` / `stars_delta_30d` — when present, never exceed the current
  `stars` (an impossible jump fails validation).

### Relevance scoring (BRS) — the current primary system

Every project discovered through the normal scan carries:

- `brs` — integer **0–100**, the BCI Relevance Score. The inclusion gate is
  40; nothing below it is published. Validated in CI to be a number in range.
- `relevance_tier` — a string matching `L[0-4]_UPPER_SNAKE_NAME` (for
  example `L4_EXPLICIT_BCI`, `L3_STANDARD_OR_HARDWARE`,
  `L3_MODALITY_OR_PARADIGM`, `L2_NEURO_TERM`). The exact tier vocabulary is
  intentionally not enumerated here — new tiers are additive — but the shape
  is enforced.
- `relevance_ledger` — an array of `{points, kind, reason}` objects, one per
  signal that contributed to `brs` (`kind` is currently one of `core`,
  `neuro`, `modality`, `paradigm`, `standard`, `hardware`, additive over
  time). Every point in `brs` traces to a ledger line with a plain-language
  `reason` — this is what "tap a score and the ledger unfolds" on the live
  radar is reading.

`brs`/`relevance_tier`/`relevance_ledger` are **not** present on
ecosystem-manifest entries — AxonOS's own repositories that are force-included
by name rather than discovered (see `CHANGELOG.md`'s `5.0.3` entry) never run
through BRS discovery at all. Consumers should treat their absence as "not
discovered, deliberately catalogued" rather than a missing value.

### Legacy fields (v3, retained for continuity)

Superseded by the BRS system above but still present and still validated,
purely so existing consumers built against the v3 shape don't break:

- `evidence_tier` — one of `L3_EXPLICIT_BCI`, `L2_NEURAL_SIGNAL`,
  `L1_CONTEXT_PLUS_NEURO`, `L0_WEAK_ADJACENT` — **required at `version: 3`
  and above**. Note this is a fixed four-value enum distinct from the newer
  `relevance_tier`'s open `L0`–`L4` vocabulary; the two are not
  interchangeable despite the similar names.
- `inclusion_reason` — a human-readable sentence, required alongside it.
- `quality_flags` — `possible_false_positive`, `low_metadata`,
  `missing_license`, `no_recent_activity`.
- `owner`, `repo`, `license`, `has_license`, `has_release`, `rising`,
  `axon_relevance`.

Consumers should treat unknown fields as forward-compatible additions and must
not assume the absence of a field from a lower schema version.

## Stability

Field removals or type changes are breaking and will bump `version`. New
optional fields are additive and will not.
