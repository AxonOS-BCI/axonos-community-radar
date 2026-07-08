#!/usr/bin/env python3
"""
Ecosystem Health Signals — a transparent, reproducible maturity read-out.

This turns the radar from a discovery list into an *instrument*: for every
project it computes a small set of 0-100 sub-scores and one overall score,
using ONLY real, public GitHub metadata the enrichment phase already fetched
(licence, last-push recency, 52-week commit total, contributor count, releases,
release downloads, description/homepage presence). Nothing here is invented,
nothing is hand-tuned per project, and AxonOS is scored by the exact same
function as every other repository.

Deliberately NOT scored: conformance, security posture, test quality, or
documentation *quality* — none of those can be read reliably from GitHub search
metadata, so scoring them would be fabrication. We score only what we can
verify, and we say which dimensions we could measure for each repo.

Design mirrors validate_payload.py: pure stdlib, importable, and unit-tested.
The rules below are the published contract (see docs/METHODOLOGY.md).

    score_project(project) -> dict   # {overall, license, maintenance, ...}
"""
from __future__ import annotations

import math

# Dimensions and their weight in the overall score. A dimension is dropped from
# the overall (and its weight redistributed) when its input signal is missing
# for a given repo, so an un-enriched repo is scored fairly on what we do know.
WEIGHTS = {
    "maintenance": 0.22,   # is work still happening?
    "momentum": 0.20,      # is development sustained over the year?
    "adoption": 0.20,      # do people actually use it?
    "team": 0.16,          # is it more than a bus-factor of one?
    "license": 0.12,       # can it legally be reused?
    "docs": 0.10,          # are the basic pointers (desc/site/licence) present?
}

# SPDX identifiers GitHub returns that grant clear open-source reuse rights.
_OSI_SPDX = {
    "MIT", "MIT-0", "APACHE-2.0", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "BSD-3-CLAUSE-CLEAR",
    "ISC", "MPL-2.0", "GPL-2.0", "GPL-3.0", "GPL-2.0-ONLY", "GPL-2.0-OR-LATER",
    "GPL-3.0-ONLY", "GPL-3.0-OR-LATER", "LGPL-2.1", "LGPL-3.0", "LGPL-2.1-ONLY",
    "LGPL-2.1-OR-LATER", "LGPL-3.0-ONLY", "LGPL-3.0-OR-LATER", "AGPL-3.0",
    "AGPL-3.0-ONLY", "AGPL-3.0-OR-LATER", "EPL-2.0", "EPL-1.0", "UNLICENSE",
    "ZLIB", "BSL-1.0", "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "MS-PL", "OSL-3.0",
    "ECL-2.0", "POSTGRESQL", "NCSA", "0BSD", "WTFPL", "ARTISTIC-2.0", "CECILL-2.1",
}


def _clamp(v: float) -> int:
    return int(max(0, min(100, round(v))))


def _license_score(project):
    """Reuse clarity from the SPDX id GitHub already classified."""
    spdx = (project.get("license") or "").upper()
    if spdx in _OSI_SPDX:
        return 100
    if spdx and spdx != "NOASSERTION":
        return 70          # a real licence GitHub could name, just not on our OSI list
    if project.get("has_license"):
        return 40          # a LICENSE file exists but GitHub could not classify it
    return 0               # no licence detected — reuse rights unclear


def _maintenance_score(project):
    """Recency of the last push. days_since_push is always present."""
    d = project.get("days_since_push")
    if d is None or d >= 9000:
        return None
    d = int(d)
    if d <= 7:
        return 100
    if d <= 30:
        return 85
    if d <= 90:
        return 65
    if d <= 180:
        return 45
    if d <= 365:
        return 25
    return 10


def _momentum_score(project):
    """Sustained development over the year, from the real 52-week commit total.
    Returns None when the histogram was unavailable (GitHub still computing, or
    the repo was not enriched) so momentum does not read as a hard zero."""
    if project.get("activity_pending"):
        return None
    c = project.get("commits_52w")
    if c is None:
        return None
    return _clamp(math.log10(int(c) + 1) * 40.0)   # 10→40, 100→80, 1000→100(cap)


def _adoption_score(project):
    """External usage: stars, published releases, and real release downloads."""
    stars = int(project.get("stars") or 0)
    releases = int(project.get("releases_count") or 0)
    downloads = int(project.get("total_downloads") or 0)
    s = min(60.0, math.log10(stars + 1) * 20.0)
    r = min(20.0, releases * 2.0)
    dl = min(20.0, math.log10(downloads + 1) * 5.0)
    return _clamp(s + r + dl)


def _team_score(project):
    """Breadth of maintainers, from the real contributor count. None when the
    repo was not enriched (contributors absent) so a solo/unknown split is
    not conflated."""
    c = project.get("contributors")
    if c is None:
        return None
    c = int(c)
    if c <= 0:
        return None
    if c == 1:
        return 20
    if c == 2:
        return 40
    if c <= 4:
        return 55
    if c <= 9:
        return 70
    if c <= 24:
        return 85
    return 100


def _docs_score(project):
    """Basic-pointers signal — NOT a judgement of documentation quality, which
    we cannot read from metadata. Scores only what is verifiable: a non-empty
    description, a set homepage, and a clear licence file."""
    score = 0
    if (project.get("description") or "").strip():
        score += 40
    if (project.get("homepage") or "").strip():
        score += 30
    if project.get("has_license") or (project.get("license") or "") not in ("", "NOASSERTION"):
        score += 30
    return _clamp(score)


_DIMS = {
    "license": _license_score,
    "maintenance": _maintenance_score,
    "momentum": _momentum_score,
    "adoption": _adoption_score,
    "team": _team_score,
    "docs": _docs_score,
}


def verifiable_badges(project):
    """True/false labels derived purely from real fields — the only kind of
    badge worth showing (no self-assessed claims). Order is display order."""
    spdx = (project.get("license") or "").upper()
    badges = []
    if spdx in _OSI_SPDX:
        badges.append("osi-licensed")
    d = project.get("days_since_push")
    if isinstance(d, int) and d <= 30:
        badges.append("actively-maintained")
    if int(project.get("releases_count") or 0) > 0:
        badges.append("has-releases")
    if int(project.get("contributors") or 0) >= 3:
        badges.append("multi-contributor")
    return badges


def score_project(project):
    """Return the signals dict for one project. `basis` reports how complete the
    inputs were: 'enriched' (commits + contributors present), 'search-only'
    (neither — momentum/team omitted), or 'partial' (one of the two)."""
    parts = {}
    for name, fn in _DIMS.items():
        v = fn(project)
        if v is not None:
            parts[name] = v

    total_w = sum(WEIGHTS[k] for k in parts)
    overall = (
        _clamp(sum(parts[k] * WEIGHTS[k] for k in parts) / total_w)
        if total_w > 0 else 0
    )

    has_commits = project.get("commits_52w") is not None and not project.get("activity_pending")
    has_team = project.get("contributors") is not None and int(project.get("contributors") or 0) > 0
    basis = "enriched" if (has_commits and has_team) else \
            "search-only" if not (has_commits or has_team) else "partial"

    out = {"overall": overall, "basis": basis, "badges": verifiable_badges(project)}
    out.update(parts)
    return out


def annotate(projects):
    """Attach `signals` to every project in place. Returns the same list."""
    for p in projects:
        p["signals"] = score_project(p)
    return projects


def band(overall):
    """Coarse label for the overall score — used by the UI and the report."""
    if overall >= 80:
        return "strong"
    if overall >= 60:
        return "solid"
    if overall >= 40:
        return "developing"
    return "early"


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "data/radar.json"
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    projects = payload.get("projects", [])
    annotate(projects)
    scored = sorted(projects, key=lambda p: -p["signals"]["overall"])
    print(f"Scored {len(projects)} projects from {path}\n")
    print(f"{'overall':>7}  {'band':<11} {'basis':<12} full_name")
    for p in scored[:25]:
        s = p["signals"]
        print(f"{s['overall']:>7}  {band(s['overall']):<11} {s['basis']:<12} {p['full_name']}")
