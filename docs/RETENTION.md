# Data Retention — AxonOS Community Radar

Everything the radar stores is **public GitHub metadata about repositories**
(names, stars, topics, timestamps). No personal data beyond public repository
owner handles is collected, and nothing is collected about visitors — the site
has no analytics, no cookies, no tracking.

## What is kept, and for how long

| Store | Contents | Retention | Enforced by |
|---|---|---|---|
| `data/radar.json` | Current snapshot of tracked projects | Latest only (overwritten each scan) | pipeline |
| `data/history.json` | Per-snapshot star counts for the top 200 + field totals | **45 days** rolling | `HISTORY_RETENTION_DAYS` in `scripts/radar.py` |
| `data/first_seen.json` | First-discovery timestamps | While a repo is on the radar, plus **400 days** after it leaves | `FIRST_SEEN_TTL_DAYS` in `scripts/radar.py` |
| `data/status.json`, `data/last_run.json` | Last pipeline run's stats / outcome | Latest only (overwritten) | pipeline |
| Workflow artifacts (`radar-data-*`) | Disaster-recovery data snapshots | **90 days** | `retention-days` in `radar.yml` |
| Git history | Every published change to the above | Indefinite (it *is* the audit trail) | git |

The prune rules run automatically inside every scan — retention is code, not
policy prose.

## Removal requests

If a repository owner does not want their **public** repository listed:
add the repo (or owner) to `exclude_repos` / `exclude_owners` in
`data/seeds.json` via an issue or PR. Exclusion takes effect on the next scan;
the entry then ages out of `first_seen.json` under the 400-day TTL, and out of
`history.json` within 45 days. Git history is not rewritten — it records what
was public at the time.

## GDPR note

The dataset consists of public technical facts about repositories. Repository
owner handles appear only as part of the public `owner/name` identifier.
Should any processing question arise, contact **connect@axonos.org**.
