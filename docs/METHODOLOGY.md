# AxonOS Radar — methodology

AxonOS Radar is a map of the open brain–computer-interface field, built from
public GitHub metadata. This page explains exactly how it works, so that the
result is auditable rather than asserted.

## The five things to know first

- **Inclusion is not endorsement.** A repository appearing here is not a
  recommendation, certification, or safety judgement.
- **Categories are heuristic.** They are assigned from topics and keywords and
  can be wrong. They describe, they do not rank.
- **Scores are discovery signals, not quality, safety, or clinical ratings.**
- **GitHub topics are self-declared** by repository maintainers.
- **AxonOS projects are not boosted.** They are ranked by the same formula as
  everyone else, and the radar excludes its own repository.

## Source data

The radar queries the public GitHub topic-search API for a curated set of
topics (`data/seeds.json`), restricted to public, non-archived, non-fork
repositories at or above a small star threshold. Only public metadata is used:
repository name and URL, description, topics, stars, forks, language, license
metadata, and last-push time. No emails, no profiles, no analytics, no cookies,
no third-party trackers.

## Inclusion rules

A repository is included only if it has a relevant topic **and** an anchored
neuro keyword in its metadata (word-boundary matched, so `midi` does not match
`mi`). Generic adjacency alone is not enough. The exact signals that caused
inclusion are recorded per project as `matched_topics` and `matched_keywords`.

## Evidence tiers

Each project is labelled with why it qualifies:

- `L3_EXPLICIT_BCI` — an explicit BCI/BMI/brain-computer-interface topic.
- `L2_NEURAL_SIGNAL` — EEG/ECoG/MEG/neural-signal/neurofeedback signal.
- `L1_CONTEXT_PLUS_NEURO` — a context topic (signal-processing, embedded,
  real-time, privacy) plus an anchored neuro keyword.
- `L0_WEAK_ADJACENT` — weak adjacency; included only with multiple weak signals
  and flagged as a possible false positive.

## Scoring

The discovery score combines reach and recency:

```
score = log10(stars + 1) * 10 + max(0, 60 - days_since_push) * 0.5
```

It favours visible, recently active work. It is a sorting aid, not a verdict.

## Ecosystem Health signals

Every project carries a `signals` block: an overall **Health** score (0–100) and
a set of 0–100 sub-scores, computed by `scripts/signals.py`. The design rule is
strict: **score only what public GitHub metadata can verify, and omit — never
fabricate — everything else.** No extra API calls are made; every input is a
field the enrichment phase already fetched. AxonOS is scored by the identical
function as every other repository — there is no identity-based special-casing
(a unit test asserts two otherwise-identical repos score the same regardless of
name).

**Sub-scores and their inputs**

| Dimension | Input (all real GitHub signals) | Rule (summary) |
|:--|:--|:--|
| `maintenance` | `days_since_push` | ≤7d → 100, ≤30 → 85, ≤90 → 65, ≤180 → 45, ≤365 → 25, else 10 |
| `momentum` | `commits_52w` (52-week commit total) | `min(100, log10(commits+1) × 40)`; omitted if the histogram was unavailable |
| `adoption` | `stars`, `releases_count`, `total_downloads` | `min(60, log10(stars+1)×20) + min(20, releases×2) + min(20, log10(dl+1)×5)` |
| `team` | `contributors` | 1→20, 2→40, 3–4→55, 5–9→70, 10–24→85, 25+→100; omitted if unknown/0 |
| `license` | SPDX id | OSI-recognised → 100, other named licence → 70, unclassifiable file → 40, none → 0 |
| `docs` | `description`, `homepage`, licence file | +40 / +30 / +30 — *presence of pointers*, **not** documentation quality |

**Overall**

```
overall = round( Σ(score_d × weight_d) / Σ(weight_d) )   over measured dimensions d
weights = maintenance .22, momentum .20, adoption .20, team .16, license .12, docs .10
```

When a dimension's input is missing for a repo, that dimension is dropped from
the sum and the remaining weights are renormalised — so an un-enriched repo is
scored fairly on what is known rather than being pushed down by hard zeros. The
`basis` field records completeness: `enriched` (commits **and** contributors
present), `search-only` (neither — momentum and team not measured), or `partial`
(one of the two).

**Bands** (UI labels): `strong` ≥ 80, `solid` ≥ 60, `developing` ≥ 40, `early`
below 40.

**Verifiable badges** are derived purely from the same real fields:
`osi-licensed`, `actively-maintained` (push ≤ 30d), `has-releases`,
`multi-contributor` (≥ 3). Nothing self-asserted is ever shown.

**Deliberately not scored.** Conformance, security posture, and test quality are
*not* part of Health. They cannot be read reliably from search metadata, so
assigning them numbers would be fabrication — the opposite of the point. Health
is a triage signal to help you find well-maintained, adopted, clearly-licensed
work; it is **never** a claim that a project is correct, safe, or fit for
clinical use.

## Rising

Rising is based on 7-day star velocity from `data/history.json`:

```
rising = stars_delta_7d >= max(2, ceil(stars * 0.05))
```

Missing history yields a delta of zero; the first scan does not mark everything
as rising.

## Falling

Symmetry with rising (v4.3.0): negative movement is shown, not hidden.

```
falling = stars_delta_7d <= -2
```

Falling projects keep their place in the ranking — the flag is information,
not a penalty.

## Two meanings of "active"

`active` means **code recency**: last `git push` within 30 days. Because a
push is not the only life sign (issues, discussions, metadata edits update
`updated_at` instead), v4.3.0 also records `community_active` — pushed *or*
updated within 30 days. The headline "Active (30d)" count keeps the stricter
push-based meaning.

## Archived repositories

The search query excludes archived repos, and any repo found to be archived or
disabled **during enrichment** is removed from the ranking (it no longer
displaces active projects). The number removed is published in
`data/status.json` as `excluded_archived`.

## Enrichment buffer (sampling-bias fix)

Ranking happens in two passes. The base score (stars + recency) orders all
candidates; then the pipeline enriches a **buffer of cap + 30** projects — not
just the final cap — recomputes the full score with the enriched terms
(downloads, contributors, commit activity, releases), re-sorts, and only then
cuts to the cap. A project just below the base-score line can therefore earn
its way in on real adoption signals.

## Search-cap honesty

GitHub Search hard-caps any query at 1 000 results, and the radar additionally
pulls a bounded number per topic by design. When a topic reports more matches
than were pulled, that topic is counted in `status.json` as
`search_saturated_topics` — the radar is a **high-recall sample of the most
relevant and recently active work**, and it says so rather than claiming
exhaustiveness.

## Category tie-breaking

Categorisation is scored (name hit > topic hit > description hit). Ties break
deterministically: higher score → more specific category (the fixed
`CATEGORY_PRIORITY` order) → alphabetical. Two identical inputs always land in
the same category.

## Removal and correction

To remove or correct an entry, open an issue or a pull request editing the
denylist in `data/seeds.json`. Removal requests are honoured.

## No auto-engagement

The radar never stars, follows, or comments on any repository. It reads public
metadata and publishes a map. Any optional digest issue is created only inside
this repository and never interacts with external projects.


## v5 pipeline mechanics

**Saturated-topic recovery.** GitHub search caps what one `sort=updated` pull
returns. When `total_count` exceeds what we pulled for a topic, the scanner
issues **one** extra `sort=stars` page for that topic. Recovered items pass
through **the same `ingest()` gate** (self/dedup, exclusions, fork/archived,
`min_stars`, relevance) as the main scan — recovery widens coverage, never
loosens inclusion. The count is published as `recovered_by_stars_pass`.

**Inclusion floor.** `min_stars` is **2**: one self-star no longer qualifies,
while genuinely young projects still surface quickly. Multi-word neuro
keywords also carry hyphen variants (`brain-machine`, `spike-sorting`,
`motor-imagery`) so GitHub topic syntax matches as well as prose.

**Categorisation notes.** Category keywords may match a whole topic or a
hyphen-token inside one (so `eeg` matches `eeg-analysis`). Seed keywords are
curated to contain no generic tokens, which is what keeps token matching
safe; the deterministic tie-break is unchanged. The AxonOS-relevance
dimensions use **word-boundary** matching ('api' does not fire inside
'rapid').

**Parallel enrichment etiquette.** Enrichment runs on 4 threads sharing one
locked budget; each worker keeps the same per-request spacing as the serial
version, and every worker stops as soon as the remaining rate limit
approaches the reserve. A 429 anywhere stops everyone.

**`data/weekly.json`.** After the history snapshot is appended, the scanner
derives a ~1 KB digest — deltas vs the closest snapshot ≤ 8 days back, top
risers/fallers by `stars_delta_7d`, and this scan's entrants. The map strip,
the stats page and the report all read this one file, so every surface shows
identical numbers.

**Builders owner data.** For the small Builders list only, the scanner reads
each owner's public profile once (`type`, `followers`). This is display
context, not a ranking input — builder ordering is unchanged.
