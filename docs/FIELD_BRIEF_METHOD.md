# How a Field Brief is made

The map is automatic. The Field Brief is the one product in which a person
checks the work, so this file states exactly what that person does, what they
may conclude, and how a reader can trace each line back to its source.

## The steps

1. **Radar detection.** Candidates come from the published Radar snapshot the
   brief names (`snapshot_id`, below). Nothing is added from memory.
2. **Repository verification.** The repository is opened: it exists, is public,
   and is what its description says.
3. **BCI relevance verification.** The analyst reads the code and README, not
   only the topics, and records a relevance verdict: *In scope*, *Adjacent*,
   *Concept only* or *Excluded*.
4. **Activity verification.** Recent commits, releases and issues are read
   against the dates in the snapshot.
5. **Organisation identity.** Who owns the repository: an organisation, a
   person, a company. A GitHub owner is not assumed to be an employer, and a
   contributor is not assumed to be a founder.
6. **Primary sources.** The official repository, company site, paper,
   registry or regulatory filing.
7. **Secondary sources.** Reputable databases such as Crunchbase, reputable
   press, interviews.
8. **Disposition.** One per finding (below).
9. **Confidence.** Per dimension (below).
10. **Dates and versions.** Review date, report version, methodology version and
    snapshot id, on every brief.

## Dispositions

| Disposition | Meaning |
|:--|:--|
| `CONFIRMED` | Supported by at least one primary source, checked on the review date |
| `PROBABLE` | Supported by secondary sources; no primary source contradicts it |
| `AMBIGUOUS` | Sources disagree, or the evidence fits more than one reading |
| `FALSE_POSITIVE` | The Radar surfaced it, and the evidence shows it does not belong |
| `INSUFFICIENT_EVIDENCE` | Too little public evidence to say; nothing is filled in to cover the gap |

## Sources, by tier

| Tier | Sources | Use |
|:--|:--|:--|
| 1 · Primary | Official repository, company site, paper, registry, regulatory filing | Can confirm |
| 2 · Secondary | Reputable databases (Crunchbase), reputable press, interviews | Can support |
| 3 · Discovery only | Social media, aggregators, directories | Can point; never confirms |

## Confidence

Given separately, never combined into a score: **BCI relevance**, **identity**,
**activity**, and, where the brief names a company, **commercial identity** —
each *High*, *Medium* or *Low*.

## Provenance of a brief

Every brief carries: report id, `snapshot_id` (the `generated_at` of the
`data/radar.json` it was built from), Radar version, methodology version (the
rule version the payload names), schema version, generated and reviewed
timestamps, a source register and a revision number. A correction produces a
new revision; the earlier one is kept.

## What a brief is not

Not investment advice, not an acquisition recommendation, not a security audit,
not a clinical or regulatory assessment, and not a market forecast.

## The sample

[`sample.html`](../sample.html) shows four pages of a brief built from the
snapshot of 3 October 2026, with its relevance verdicts and one cited builder
profile.
