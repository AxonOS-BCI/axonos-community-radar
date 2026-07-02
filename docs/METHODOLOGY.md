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
