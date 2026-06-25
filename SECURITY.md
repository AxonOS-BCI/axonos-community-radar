# Security Policy

The Open BCI Ecosystem Radar renders data derived automatically from public GitHub
search. We take the integrity of that pipeline seriously.

## Reporting a vulnerability

Email **security@axonos.org** with a description and reproduction steps. Please do
not open a public issue for security reports. We aim to acknowledge within 72 hours
and to coordinate disclosure within 90 days.

## Scope

- `index.html` — XSS, CSP bypass, unsafe link handling.
- `data/radar.json` / `feed.xml` — data poisoning or injection via auto-discovered repos.
- `scripts/radar.py` — API abuse, token handling, rate-limit safety.

## Hardening already in place

- All repository-derived text is HTML-escaped before rendering; links are restricted
  to `https://github.com/…` via an allowlist check.
- A Content-Security-Policy meta restricts sources (`default-src 'self'`, images only
  from shields.io / contrib.rocks / avatars, no framing, no form actions).
- `scripts/radar.py` validates its own output (field presence, project cap, and an
  `https://github.com/` URL allowlist) and refuses to write a malformed data file, so
  CI never commits poisoned data.

## Supported versions

The latest `main` is supported. This project is an ecosystem map, not a medical device.
