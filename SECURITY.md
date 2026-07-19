# Security Policy

The AxonOS Radar renders data derived automatically from public GitHub
search. We take the integrity of that pipeline seriously.

## Reporting a vulnerability

Email **security@axonos.org** with a description and reproduction steps. Please do
not open a public issue for security reports. We aim to acknowledge within 72 hours
and to coordinate disclosure within 90 days.

## Scope

- `index.html`, `assets/app.js` / `assets/stats.js` — XSS, CSP bypass, unsafe link handling.
- `data/radar.json` / `feed.xml` — data poisoning or injection via auto-discovered repos.
- `scripts/sync_engine_data.py` — cross-repo data pull, token handling, rate-limit safety.
- `scripts/validate_payload.py` — payload validation gate (this is what CI and the sync
  step both run before any data is trusted).

## Hardening already in place

- All repository-derived text is rendered via `textContent`, never `innerHTML` — zero
  HTML-interpretation of repo-derived strings; links are restricted to
  `https://github.com/…` via an exact-host allowlist (`safeUrl()` / `_is_safe_github_url()`),
  which also rejects look-alike hosts such as `github.com.evil.com`.
- A Content-Security-Policy meta restricts sources (`default-src 'self'`, images only
  from shields.io / contrib.rocks / avatars, no framing, no form actions).
- `scripts/validate_payload.py` validates the published payload (required fields, a
  project cap, description-length cap, an `https://github.com/` URL allowlist, and
  range checks on every score/signal) and CI fails the build on any violation, so a
  malformed or poisoned data file is never published.

## Supported versions

The latest `main` is supported. This project is an ecosystem map, not a medical device.

## Removing a project (takedown)

The radar lists public repositories discovered by topic. To remove one, add its
`owner/name` to `exclude_repos` (or the owner to `exclude_owners`) in
`data/seeds.json` via a pull request, or open an issue — it drops on the next
6-hour refresh. This is the project's lightweight moderation/takedown valve; there
is no manual approval gate, by design, so the map stays live.

## Privacy

The page collects no personal data, sets no cookies, and runs no analytics or
tracking. It renders only public GitHub repository metadata. Badge and contributor
images are loaded from shields.io and contrib.rocks (their own privacy terms apply);
the Content-Security-Policy restricts image sources to those hosts.
