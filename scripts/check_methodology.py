#!/usr/bin/env python3
"""Documentation-coverage gate (v6, "Solid Ground").

The radar's core promise is that every number on screen is *explained*, not
asserted. This gate makes that promise mechanical: every health dimension,
every foundation signal, every interop tag in the vocabulary, and every
published data endpoint MUST be mentioned in the Methodology view
(index.html) and in docs/METHODOLOGY.md — and every interop tag must exist
in the UI label map (assets/app.js). A signal that ships without its
explanation fails CI.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEALTH_DIMS = ("license", "maintenance", "momentum", "adoption", "team", "docs")
FOUNDATION_KEYS = ("license_file", "readme", "contributing", "code_of_conduct",
                   "citation", "security_policy", "ci")
ENDPOINTS = ("data/radar.json", "data/radar.schema.json", "data/ecosystem.json",
             "data/badge-ecosystem.json", "data/projects.ndjson", "feed.xml",
             "data/interop-vocab.json",
             "data/signals.json", "feeds/signals.xml", "feeds/new.xml", "feeds/rising.xml",
             "data/api.json", "data/projects.csv", "data/signals.schema.json",
             "badges/index.json")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    vocab = json.loads(_read(ROOT / "data" / "interop-vocab.json"))
    tags = [t["tag"] for t in vocab["tags"]]
    labels = {t["tag"]: t["label"] for t in vocab["tags"]}

    idx = _read(ROOT / "index.html")
    md = _read(ROOT / "docs" / "METHODOLOGY.md")
    app = _read(ROOT / "assets" / "app.js")

    # 1) Every interop tag: documented (label or slug) in both methodology
    #    surfaces, and present in the UI label map.
    for tag in tags:
        lab = labels[tag]
        rx = re.compile(rf"\b({re.escape(tag)}|{re.escape(lab)})\b", re.IGNORECASE)
        if not rx.search(idx):
            errors.append(f"interop tag {tag!r} not documented in index.html methodology")
        if not rx.search(md):
            errors.append(f"interop tag {tag!r} not documented in docs/METHODOLOGY.md")
        if f"'{tag}'" not in app and f'"{tag}"' not in app:
            errors.append(f"interop tag {tag!r} missing from the UI label map (assets/app.js)")

    # 2) Every foundation signal named in both surfaces.
    human = {"license_file": "licen", "readme": "readme", "contributing": "contributing",
             "code_of_conduct": "code of conduct", "citation": "CITATION.cff",
             "security_policy": "SECURITY.md", "ci": "CI workflow"}
    for key, needle in human.items():
        if needle.lower() not in idx.lower():
            errors.append(f"foundation signal {key!r} ({needle}) not documented in index.html")
        if needle.lower() not in md.lower():
            errors.append(f"foundation signal {key!r} ({needle}) not documented in METHODOLOGY.md")

    # 3) Every health dimension still documented (regression guard).
    for dim in HEALTH_DIMS:
        if dim not in md.lower():
            errors.append(f"health dimension {dim!r} not documented in METHODOLOGY.md")

    # 4) Every published endpoint listed in both surfaces.
    for ep in ENDPOINTS:
        if ep not in idx:
            errors.append(f"endpoint {ep!r} not listed in index.html methodology")
        if ep not in md:
            errors.append(f"endpoint {ep!r} not listed in METHODOLOGY.md")

    if errors:
        for e in errors:
            print(f"  FAIL {e}")
        print(f"check_methodology: {len(errors)} gap(s) — every shipped signal "
              f"must be explained where users read.")
        return 1
    print(f"check_methodology ok: {len(tags)} interop tags, "
          f"{len(FOUNDATION_KEYS)} foundation signals, "
          f"{len(HEALTH_DIMS)} health dimensions, "
          f"{len(ENDPOINTS)} endpoints — all documented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
