# Software Bill of Materials (SBOM) — AxonOS Community Radar

Format: human-readable inventory (SPDX-lite spirit). Regenerated with every
release; this file corresponds to **v4.3.0**.

The design goal is a supply chain small enough to list by hand.

## Runtime (the pipeline)

| Component | Version pin | License | Role |
|---|---|---|---|
| CPython standard library | `python3` as provided by `ubuntu-latest` (3.12.x) | PSF-2.0 | Entire pipeline runtime — **zero third-party runtime packages** |

`scripts/*.py` import only: `base64, json, os, re, functools, sys, time, math,
urllib, xml.sax.saxutils, datetime, email.utils, html, collections`.

## Frontend (the published site)

| Component | Version | License | Role |
|---|---|---|---|
| Vanilla JS / HTML / CSS (this repo) | v4.3.0 | MIT | `assets/app.js`, `assets/stats.js`, styles — no frameworks, no CDN imports |

The site loads **no external scripts, styles, or fonts**. The strict CSP
(`script-src 'self'; style-src 'self'`, no `unsafe-inline`) makes that a
verified property, not a promise.

## CI/CD (GitHub Actions, all SHA-pinned; pins enforced by a CI gate)

| Action | Pinned SHA | Tag | Used in |
|---|---|---|---|
| `actions/checkout` | `f43a0e5ff2bd294095638e18286ca9a3d1956744` | v4 | ci.yml, radar.yml, health.yml |
| `actions/upload-artifact` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | v4.6.2 | radar.yml (data snapshots) |

CI-only Python packages (never shipped, used for tests/validation only) are
pinned in `requirements-ci.txt`: `jsonschema`, `pytest` and their
dependencies.

## External services consumed

| Service | What for | Data direction |
|---|---|---|
| `api.github.com` | Repository discovery + enrichment (public data) | read |
| GitHub Contents API | Publishing data commits (Verified signatures) | write (repo only) |
| GitHub Pages | Hosting the static site | publish |
| `img.shields.io` | README badges (rendered by the *viewer's* browser on github.com, not by the site) | none from the site |

## Verification

* `CI → "Actions are pinned to a commit SHA"` fails on any unpinned action.
* `CI → "Secret scan"` fails on token/key patterns in the tree.
* Dependabot (`.github/dependabot.yml`) proposes action-SHA updates weekly.
