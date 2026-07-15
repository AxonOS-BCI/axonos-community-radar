"""Build the machine-readable AxonOS ecosystem manifest and the live badge.

One organism, one pulse. This script derives two small JSON artefacts from
data the radar already produces, so they are always in sync with the deployed
dataset and cost ZERO extra bot commits (they are generated at deploy time in
pages.yml, straight into the site artifact):

  data/ecosystem.json        - the organism manifest: every AxonOS account and
                               repository with its role, plus live Health
                               signals for any repo the radar tracks, plus the
                               canonical voluntary-support (DOGE) block.
  data/badge-ecosystem.json  - a shields.io "endpoint" badge document. Any
                               repository in the ecosystem can embed ONE line
                               of Markdown and show the live pulse of the whole
                               organism, refreshed with every deploy:

  https://img.shields.io/endpoint?url=https%3A%2F%2Faxonos-bci.github.io%2Faxonos-community-radar%2Fdata%2Fbadge-ecosystem.json

Sources of truth (nothing is fabricated):
  data/ecosystem-registry.json - hand-maintained registry: accounts, repos,
                                 roles, and the funding block. Versioned.
  data/radar.json              - the live scan (health signals, counts).

Degrade-safe by design: a missing or unreadable radar.json still yields a
valid manifest (roles + funding, no live signals) and a valid badge (label
only), because a broken deploy is worse than a badge without numbers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REGISTRY = "data/ecosystem-registry.json"
RADAR = "data/radar.json"


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001 - degrade-safe: absence is a valid state
        return None


def live_signals_by_name(radar):
    """Map full_name -> compact live block for repos the radar tracks."""
    out = {}
    if not radar:
        return out
    for p in radar.get("projects", []):
        name = p.get("full_name")
        sig = p.get("signals")
        if not name or not isinstance(sig, dict):
            continue
        blk = {"health": sig.get("overall"), "band": sig.get("band")}
        if isinstance(p.get("stars"), int):
            blk["stars"] = p["stars"]
        out[name] = blk
    return out


def build_manifest(registry, radar):
    live = live_signals_by_name(radar)
    repos = []
    for r in registry.get("repos", []):
        row = dict(r)
        row["url"] = f"https://github.com/{r['full_name']}"
        if r["full_name"] in live:
            row["live"] = live[r["full_name"]]
        repos.append(row)
    manifest = {
        "schema": "axonos-ecosystem-v1",
        "name": registry.get("name"),
        "tagline": registry.get("tagline"),
        "canonical_site": registry.get("canonical_site"),
        "hub": registry.get("hub"),
        "accounts": registry.get("accounts", []),
        "repos": repos,
        "funding": registry.get("funding", {}),
    }
    if radar:
        c = radar.get("counts", {})
        manifest["radar"] = {
            "generated_at": radar.get("generated_at"),
            "projects": len(radar.get("projects", [])),
            "health_median": c.get("health_median"),
            "health_strong": c.get("health_strong"),
        }
    return manifest


def build_badge(radar):
    """shields.io endpoint schema. Message carries the live pulse."""
    badge = {
        "schemaVersion": 1,
        "label": "AxonOS ecosystem",
        "color": "2dd4ff",
        "labelColor": "0b0f14",
    }
    c = (radar or {}).get("counts", {})
    n = len((radar or {}).get("projects", []) or [])
    med = c.get("health_median")
    if n and isinstance(med, int):
        badge["message"] = f"{n} projects · health {med}"
    else:
        badge["message"] = "live radar"
    return badge


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="data",
                    help="output directory (default: data; pages.yml uses _site/data)")
    args = ap.parse_args(argv)

    registry = load_json(REGISTRY)
    if not registry:
        print("build_ecosystem_manifest: FATAL - registry missing/unreadable", file=sys.stderr)
        return 1
    radar = load_json(RADAR)

    os.makedirs(args.out, exist_ok=True)
    manifest = build_manifest(registry, radar)
    badge = build_badge(radar)

    mpath = os.path.join(args.out, "ecosystem.json")
    bpath = os.path.join(args.out, "badge-ecosystem.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w", encoding="utf-8") as f:
        json.dump(badge, f, indent=2, ensure_ascii=False)
        f.write("\n")

    live_n = sum(1 for r in manifest["repos"] if "live" in r)
    print(f"build_ecosystem_manifest: wrote {mpath} "
          f"({len(manifest['repos'])} repos, {live_n} with live signals) "
          f"and {bpath} ('{badge['message']}')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
