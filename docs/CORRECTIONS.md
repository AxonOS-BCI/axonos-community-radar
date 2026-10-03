# Corrections and exclusions

Anyone can challenge anything on the map or in a brief. Corrections leave a
trace: nothing published is silently rewritten.

## How to ask

Open an issue in this repository, or write to connect@axonos.org, with:

- **Claim** — what the map or the brief says
- **Current evidence** — what it rests on, as published
- **Counter-evidence** — what shows otherwise
- **Requested correction** — what you want changed
- **Source** — where the counter-evidence can be checked

## Dispositions

`Accepted` · `Partially accepted` · `Rejected` · `No change` — each with its
reason, in the issue or the reply. An accepted correction to a brief produces a
new revision; the earlier one is kept. A change to the map is recorded in the
changelog.

## Why a repository may be excluded

Exclusion goes through `exclude_repos` / `exclude_owners` in
[`data/seeds.json`](../data/seeds.json), takes effect on the next scan, and is
recorded below with its reason. Only these reasons count:

| Reason | Example |
|:--|:--|
| False positive | "BCI" meaning something other than brain–computer interfaces |
| Private or security issue | Information that should not be public |
| Legal requirement | A valid legal request |
| Accidental inclusion | A repository the scan should never have read |
| Duplicate | The same project under two names |
| Non-qualifying repository | An owner's request to leave the map of their own public repository |

*An owner disliking a score is not a reason.* The score is recomputed from the
evidence; disagreeing with the evidence is a correction request, above.

## The register

| Repository | Reason | Since |
|:--|:--|:--|
| `SUSE/BCI-dockerfile-generator` | False positive: SUSE Base Container Images | 16.10.1 |
| `lebidan/sbnd` | False positive: neural decoders for error-correcting codes | 16.10.1 |
| `scouter-project/scouter` | False positive: an application-performance monitor | 16.10.1 |
