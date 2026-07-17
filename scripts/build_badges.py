#!/usr/bin/env python3
"""Build per-project scored badges (v12.0 "Badges").

Every project on the map gets a live, embeddable badge — its BRS and relevance
tier, served as a shields.io endpoint straight from the deployed dataset:

  badges/<owner>/<repo>.json    shields endpoint (schemaVersion 1)
  badges/index.json             catalog: badge URL + ready-to-paste markdown

The badge is *derived*, never granted: whatever the engine scored on the last
scan is what the badge says. It updates when the map updates and it cannot be
edited by hand — which is exactly what makes it worth embedding.

Deploy-time and pure: reads the published dataset, writes into the artifact,
commits nothing.

    python3 scripts/build_badges.py --out _site
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

SITE = "https://axonos-bci.github.io/axonos-community-radar"
LABEL = "AxonOS Radar"

# GitHub owner/repo segments: word chars, dots, dashes. Anything else is not a
# GitHub name and must not become a filesystem path.
SAFE = re.compile(r"^[A-Za-z0-9._-]+$")

TIER_SHORT = {
    "L4_EXPLICIT_BCI": "Explicit BCI",
    "L3_STANDARD_OR_HARDWARE": "BCI standard/HW",
    "L3_MODALITY_OR_PARADIGM": "BCI modality",
    "L2_NEURO_TERM": "Neuro-adjacent",
}

# Colour tells the band at a glance; the gate at 40 means nothing lower is on
# the map at all.
def color_for(brs) -> str:
    if not isinstance(brs, (int, float)):
        return "8a97a6"
    if brs >= 80:
        return "34d399"   # emerald — explicit, load-bearing
    if brs >= 60:
        return "2dd4ff"   # cyan — solid
    return "fbbf24"       # amber — kept, developing


def message_for(p: dict) -> str:
    brs = p.get("brs")
    tier = TIER_SHORT.get(p.get("relevance_tier") or "", "")
    if isinstance(brs, (int, float)):
        return f"BRS {int(brs)}" + (f" · {tier}" if tier else "")
    return tier or "on the map"


def badge_for(p: dict) -> dict:
    return {
        "schemaVersion": 1,
        "label": LABEL,
        "labelColor": "0b1220",
        "message": message_for(p),
        "color": color_for(p.get("brs")),
        "cacheSeconds": 10800,   # one engine scan period
    }


def embed_markdown(full_name: str) -> str:
    endpoint = f"{SITE}/badges/{full_name}.json"
    img = "https://img.shields.io/endpoint?url=" + quote(endpoint, safe="")
    return f"[![{LABEL}]({img})]({SITE}/)"


def build(radar: dict, out_dir: Path) -> dict:
    badges_dir = out_dir / "badges"
    index = {"generated_at": radar.get("generated_at"),
             "label": LABEL, "count": 0, "projects": {}}
    for p in radar.get("projects", []):
        full = p.get("full_name") or ""
        parts = full.split("/")
        if len(parts) != 2 or not all(SAFE.match(seg) for seg in parts):
            continue   # not a GitHub name; never let it shape a path
        owner, repo = parts
        d = badges_dir / owner
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{repo}.json").write_text(
            json.dumps(badge_for(p), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        index["projects"][full] = {
            "badge": f"{SITE}/badges/{full}.json",
            "brs": p.get("brs"),
            "relevance_tier": p.get("relevance_tier"),
            "markdown": embed_markdown(full),
        }
    index["count"] = len(index["projects"])
    badges_dir.mkdir(parents=True, exist_ok=True)
    (badges_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return index


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    ap.add_argument("--radar", default="data/radar.json")
    a = ap.parse_args()
    radar = json.loads(Path(a.radar).read_text(encoding="utf-8"))
    index = build(radar, Path(a.out))
    print(f"badges ok: {index['count']} projects -> {a.out}/badges/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
