#!/usr/bin/env python3
"""Build the Talent view (v13.0 "Talent").

Who builds across the open BCI field, and where expertise clusters — derived
entirely from the scored map. For every owner with a kept project:

  projects, total stars, active-in-30d, best BRS, median health,
  modality / category / language spread

plus the field-level clusters: for each modality, how many builders and
projects carry it and at what weight. Builder-level by design — a true
contributor graph needs per-repo contributor lists the dataset does not carry,
and this file never pretends otherwise.

Deploy-time and pure: reads the published dataset, writes into the artifact,
commits nothing.

    python3 scripts/build_talent.py --out _site
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def _owner(full_name: str) -> str:
    return full_name.split("/", 1)[0] if "/" in (full_name or "") else ""


def build(radar: dict) -> dict:
    projects = [p for p in radar.get("projects", []) if _owner(p.get("full_name", ""))]
    by_owner: dict = {}
    for p in projects:
        by_owner.setdefault(_owner(p["full_name"]), []).append(p)

    # engine's builders[] carries identity extras (owner_type, followers) —
    # used as enrichment where present, never as the source of the numbers
    engine_meta = {b.get("owner"): b for b in radar.get("builders", [])
                   if isinstance(b, dict) and b.get("owner")}

    builders = []
    for owner, ps in by_owner.items():
        brs_vals = [p["brs"] for p in ps if isinstance(p.get("brs"), (int, float))]
        health_vals = [(p.get("signals") or {}).get("overall") for p in ps]
        health_vals = [h for h in health_vals if isinstance(h, (int, float))]
        mods: dict = {}
        cats: dict = {}
        langs: dict = {}
        for p in ps:
            for m in (p.get("facets") or {}).get("modality", []) or []:
                mods[m] = mods.get(m, 0) + 1
            c = p.get("category")
            if c:
                cats[c] = cats.get(c, 0) + 1
            lang = p.get("language")
            if lang:
                langs[lang] = langs.get(lang, 0) + 1
        meta = engine_meta.get(owner, {})
        builders.append({
            "owner": owner,
            "url": f"https://github.com/{owner}",
            "owner_type": meta.get("owner_type"),
            "followers": meta.get("followers"),
            "project_count": len(ps),
            "total_stars": sum(p.get("stars") or 0 for p in ps),
            "active_projects_30d": meta.get("active_projects_30d"),
            "best_brs": max(brs_vals) if brs_vals else None,
            "median_health": (round(statistics.median(health_vals), 1)
                              if health_vals else None),
            "modalities": dict(sorted(mods.items(), key=lambda kv: (-kv[1], kv[0]))),
            "categories": sorted(cats, key=lambda k: (-cats[k], k))[:3],
            "languages": sorted(langs, key=lambda k: (-langs[k], k))[:3],
            "projects": sorted(p["full_name"] for p in ps),
        })
    builders.sort(key=lambda b: (-b["total_stars"], -b["project_count"], b["owner"]))

    clusters: dict = {}
    for p in projects:
        for m in (p.get("facets") or {}).get("modality", []) or []:
            c = clusters.setdefault(m, {"builders": set(), "projects": 0, "stars": 0})
            c["builders"].add(_owner(p["full_name"]))
            c["projects"] += 1
            c["stars"] += p.get("stars") or 0
    clusters_out = {m: {"builders": len(c["builders"]), "projects": c["projects"],
                        "stars": c["stars"]}
                    for m, c in sorted(clusters.items(),
                                       key=lambda kv: -kv[1]["projects"])}

    return {
        "version": 1,
        "generated_at": radar.get("generated_at"),
        "scope": "builder-level (owners of kept projects); a contributor graph "
                 "requires per-repo contributor data the map does not carry",
        "count": len(builders),
        "builders": builders,
        "clusters": clusters_out,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    ap.add_argument("--radar", default="data/radar.json")
    a = ap.parse_args()
    radar = json.loads(Path(a.radar).read_text(encoding="utf-8"))
    payload = build(radar)
    out = Path(a.out) / "data" / "talent.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"talent ok: {payload['count']} builders · "
          f"{len(payload['clusters'])} modality clusters -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
