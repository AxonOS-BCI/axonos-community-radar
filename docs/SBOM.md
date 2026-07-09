# Software Bill of Materials (SBOM) — AxonOS Community Radar

Format: human-readable inventory (SPDX-lite spirit). Regenerated with every
release; this file corresponds to **v6.0.0**.

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
| Vanilla JS / HTML / CSS (this repo) | v6.0.0 | MIT | `assets/app.js`, `assets/stats.js`, styles — no frameworks, no CDN imports |

The site loads **no external scripts, styles, or fonts**. The strict CSP
(`script-src 'self'; style-src 'self'`, no `unsafe-inline`) makes that a
verified property, not a promise.

## CI/CD (GitHub Actions, all SHA-pinned; pins enforced by a CI gate)

| Action | Pinned SHA | Tag | Used in |
|---|---|---|---|
| `actions/checkout` | `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` | v7.0.0 | ci.yml, radar.yml, health.yml, pages.yml |
| `actions/upload-artifact` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | v7.0.1 | radar.yml (data snapshots) |
| `actions/configure-pages` | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` | v6.0.0 | pages.yml |
| `actions/upload-pages-artifact` | `fc324d3547104276b827a68afc52ff2a11cc49c9` | v5.0.0 | pages.yml |
| `actions/deploy-pages` | `cd2ce8fcbc39b97be8ca5fce6e763baed58fa128` | v5.0.0 | pages.yml |

CI-only Python packages (never shipped, used for tests/validation only) are
pinned in `requirements-ci.txt` (`pytest==8.3.4`, `jsonschema==4.23.0`) and their
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

### CI-only Node dependency

| Package | Where | Why |
| --- | --- | --- |
| `jsdom` (installed per-run via `npm install --no-save`) | ci.yml → frontend job | Functional UI smoke: boots the real `index.html` + `app.js` against fixture data and asserts cards, filters, permalinks and licence markers actually work. Never shipped; the site itself remains zero-dependency vanilla JS. |
