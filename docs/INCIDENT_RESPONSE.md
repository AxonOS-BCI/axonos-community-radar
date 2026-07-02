# Incident Response — AxonOS Community Radar

Contact: **security@axonos.org** · Acknowledgement target: 72 hours (see SECURITY.md).
This plan covers the radar pipeline and its published site.

## Severity classes

| Class | Definition | Examples | Response target |
|---|---|---|---|
| **P1** | Visitors are being harmed or misled at scale | XSS actually executing on the Pages site; data replaced with malicious links | Same day: take down / roll back first, analyse second |
| **P2** | Data integrity broken, no active visitor harm | Tampered `radar.json` committed; poisoned `first_seen`; ranking manipulation | ≤ 72 h |
| **P3** | Pipeline reliability | Scans failing repeatedly; stale data alert firing; rate-limit lockout | Next maintenance window |
| **P4** | Hardening gaps, reports without exploitation | Audit findings, dependency advisories | Next minor release |

## Response procedure

1. **Confirm & classify.** Reproduce from the published site (not just the
   checkout). Check `data/last_run.json`, `data/status.json`, the Actions run
   log, and the health-monitor issue.
2. **Contain (P1/P2).** Disable the schedule if the pipeline itself is the
   vector (`Actions → AxonOS Radar → ⋯ → Disable workflow`). For a poisoned
   site, roll back first (below) — a wrong-but-safe snapshot beats a live
   exploit.
3. **Roll back.** All data is in git and every scan keeps a 90-day artifact:
   * `git revert <bad commit(s)>` on `main` (data commits are individual
     API-signed commits, so reverts are surgical), or
   * restore files from the `radar-data-<run_id>` artifact of the last good
     run and commit them.
   Pages redeploys from `main` automatically.
4. **Eradicate.** Fix the root cause; add a regression test or CI gate that
   would have caught it; if a secret may have leaked, rotate it (the Actions
   token is per-run and expires by itself).
5. **Communicate.** For P1/P2, post a short factual note in the repository
   (pinned issue or README banner): what happened, the affected window, what
   was fixed. No speculation, no minimising.
6. **Post-mortem (P1/P2).** Within a week, add an entry to
   `docs/incidents/` (`YYYY-MM-DD-title.md`): timeline · impact · root cause ·
   fix · prevention. Blameless, specific, permanent.

## Forensics checklist

* Which commit introduced the bad data? (`git log -- data/`)
* What does the Actions log of that run show? (retained 90 days)
* Does the workflow-artifact snapshot match the commit? (divergence ⇒ the
  Contents API path, not the pipeline, is the vector)
* Any settings/permissions changes in the repo audit log?

## Recovery verification

After any rollback or fix: CI green on `main`, `report.html` regenerated from
clean data, health monitor reports HEALTHY on its next run, and the alert
issue (if any) has auto-closed.
