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
| `version` | integer | `2` for the current dataset; `3` for the ecosystem-intelligence schema. |
| `generated_at` | string (ISO-8601) | when the file was produced. |
| `snapshot_at` | string (ISO-8601) | the 6-hour slot the scan is aligned to. |
| `min_stars` | integer | minimum stars for inclusion. |
| `counts` | object | `total`, and (v3) `active_30d`, `new`, `rising`, `builders`. |
| `projects` | array | the project objects below. |
| `builders` | array | (v3) owner-aggregated objects. |

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

### v3 additions

At `version: 3` every project additionally carries:

- `evidence_tier` — one of `L3_EXPLICIT_BCI`, `L2_NEURAL_SIGNAL`,
  `L1_CONTEXT_PLUS_NEURO`, `L0_WEAK_ADJACENT` (why the repo qualifies).
- `inclusion_reason` — a human-readable sentence.
- `matched_topics`, `matched_keywords` — the exact signals that matched.
- `quality_flags` — `possible_false_positive`, `low_metadata`,
  `missing_license`, `no_recent_activity`.
- `owner`, `repo`, `license`, `has_license`, `has_release`, `rising`,
  `axon_relevance` — see the v3 specification.

Consumers should treat unknown fields as forward-compatible additions and must
not assume the absence of a v3 field in a v2 payload.

## Stability

Field removals or type changes are breaking and will bump `version`. New
optional fields are additive and will not.
