# Software Bill of Materials (SBOM) — AxonOS Community Radar

Format: human-readable inventory (SPDX-lite spirit). Meant to be regenerated
with every release; this file had drifted to v7.0.0's state for five
releases before this correction — verified by hand against v12.0.4 rather
than assumed current. If it's stale again, that promise still isn't being
kept mechanically; see the CI check below meant to at least catch the
sharpest-edged version of that drift.

The design goal is a supply chain small enough to list by hand.

## Runtime (the pipeline)

| Component | Version pin | License | Role |
|---|---|---|---|
| CPython standard library | `python3` as provided by `ubuntu-latest` (3.12.x) | PSF-2.0 | Entire pipeline runtime — **zero third-party runtime packages** |

`scripts/*.py` import only: `argparse, base64, csv, datetime, hashlib, io,
json, math, os, pathlib, re, sys, time, urllib.error, urllib.parse,
urllib.request, xml.sax.saxutils`.

## Frontend (the published site)

| Component | Version | License | Role |
|---|---|---|---|
| Vanilla JS / HTML / CSS (this repo) | v12.0.4 | MIT | `assets/app.js`, `assets/stats.js`, `assets/support.js`, styles — no frameworks, no CDN imports |

The site loads **no external scripts, styles, or fonts**. The strict CSP
(`script-src 'self'; style-src 'self'`, no `unsafe-inline`) makes that a
verified property, not a promise.

## CI/CD (GitHub Actions, all SHA-pinned; pins enforced by a CI gate)

| Action | Pinned SHA | Tag | Used in |
|---|---|---|---|
| `actions/checkout` | `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` | v7.0.0 | ci.yml, sync.yml, health.yml, pages.yml, stats-issue.yml, release.yml |
| `actions/configure-pages` | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` | v6.0.0 | pages.yml |
| `actions/upload-pages-artifact` | `fc324d3547104276b827a68afc52ff2a11cc49c9` | v5.0.0 | pages.yml |
| `actions/deploy-pages` | `cd2ce8fcbc39b97be8ca5fce6e763baed58fa128` | v5.0.0 | pages.yml |

`radar.yml` and the `actions/upload-artifact` pin both belonged to this
repo's own scan workflow, retired at the 8.0.0 open-core cutover — scanning,
and whatever artifact retention it uses, now happens entirely inside the
private engine and isn't part of this repo's own SBOM.

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
