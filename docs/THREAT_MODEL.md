# Threat Model — AxonOS Community Radar

Version: 7.0.0 · Review cadence: with every minor release, or after any security report.

The radar is a **read-only aggregator of public GitHub metadata** published as a
static site. It holds no user data, no secrets beyond the ephemeral Actions
token, and takes no input from visitors. That makes the interesting attack
surface the *pipeline and its outputs*, not the site.

## Assets

| Asset | Why it matters |
|---|---|
| `data/radar.json`, `data/history.json`, `data/first_seen.json`, `data/status.json`, `data/last_run.json` | The product. Integrity of these files *is* the project's credibility. |
| `report.html`, `index.html`, `stats.html`, `assets/*.js` | Executed in visitors' browsers. |
| GitHub Actions token (per-run) | Can write repo contents and issues while a run lives. |
| Ranking neutrality | The public promise that AxonOS is scored like everyone else. |

## Threats and mitigations (STRIDE)

**Spoofing.**
*Look-alike project URLs* (`github.com.evil.com`) → exact-host allowlist
`_is_safe_github_url` in the pipeline **and** `safeUrl()` in both frontends;
`validate_payload.py` re-checks every URL before publish. *Stats-issue
hijacking via marker collision* → the publisher and the health monitor only
touch issues **created by `github-actions[bot]`** that carry the marker.

**Tampering.**
*A compromised or hand-edited `radar.json`* → CI schema validation, the
malicious-payload fixture test, and (v4.3.0) **frontend ingress validation**:
every field the UI renders is type-coerced and URL-checked in
`sanitizeData()` before any DOM work, with `esc()` as the second wall.
*Future-dated `first_seen` (makes a project "new" forever, poisons the RSS
feed)* → clamped at bootstrap, healed on read, rejected by `validate()`, and
gated in CI. *Force-push data loss* → every scan uploads a 90-day data
snapshot artifact independent of git history.

**Repudiation.**
All data commits go through the Contents API and are **signed by GitHub
(Verified)**; `data/last_run.json` records the outcome (and failure reason) of
every pipeline run.

**Information disclosure.**
The pipeline reads only public API data and publishes only public data. The
Actions token never appears in outputs; CI runs a secret-pattern scan on every
push. Repository *view counts* are owner-private on GitHub, so the radar
deliberately never shows them rather than approximating.

**Denial of service.**
*Silent pipeline death* → the health monitor reads the **published** Pages
data twice a day and maintains a single self-closing alert issue when data
goes stale (>12 h) or the last run failed. *API-quota exhaustion* → serial
requests, response-size caps, early enrichment stop with head-room, and a
rate-limit start/end record in `status.json`. *Half-empty publishes after
partial API failure* → the >25 % topic-failure abort preserves the last good
snapshot.

**Elevation of privilege.**
Workflows run with the minimum permissions they need (`contents: write`,
`issues: write` only where used); every action is **pinned to a full commit
SHA** and CI enforces that pin; Dependabot proposes bumps. The runtime has
**zero third-party dependencies** — the supply chain is CPython's standard
library plus pinned actions.

## Accepted risks

* GitHub Search caps any query at 1 000 results; the radar additionally caps
  per-topic pulls by design. Saturated topics are **counted and published**
  (`search_saturated_topics`) instead of pretending exhaustiveness — see
  METHODOLOGY.
* GitHub Pages is a single-region host. A CDN in front is a deliberate
  non-goal for now; the entire dataset is a public JSON anyone can mirror.

## Out of scope

Visitor authentication (there are no accounts), server-side attacks (there is
no server), and the security of the listed third-party projects themselves —
**inclusion is not endorsement**.
