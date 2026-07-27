#!/usr/bin/env python3
"""Build per-project trajectories (v11.0 "Trajectory").

Two honest sources, merged into one series per project:

  data/history.json      per-project STAR counts, one point per engine scan —
                         real, measured, accruing since 2026-06-26
  data/trajectory.json   per-project [t, BRS, stars, health] points persisted
                         by the engine — accruing since 2026-07-16

Output — ``_site/data/trajectory.json`` in the published schema:
``{full_name: [[iso_ts, brs, stars, health], ...]}``. Points derived from the
star history carry ``null`` for BRS and health: those values were not measured
then, and this file never invents a number. Nothing is backfilled, nothing is
interpolated; the series is exactly what was observed, capped to the most
recent 96 points per project.

Deploy-time and pure: reads the published dataset, writes into the artifact,
commits nothing.

    python3 scripts/build_trajectory.py --out _site
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CAP = 96


def _parse_history(history: dict) -> dict:
    """history.json -> {name: {iso_ts: stars}}"""
    out: dict = {}
    for snap in (history or {}).get("snapshots", []):
        ts = snap.get("snapshot_at")
        stars = snap.get("stars")
        if not ts or not isinstance(stars, dict):
            continue
        for name, n in stars.items():
            out.setdefault(name, {})[ts] = n
    return out


def _parse_engine(traj: dict) -> dict:
    """engine trajectory.json -> {name: {iso_ts: (brs, stars, health)}}"""
    out: dict = {}
    if not isinstance(traj, dict):
        return out
    for name, pts in traj.items():
        if not isinstance(pts, list):
            continue
        for pt in pts:
            if isinstance(pt, list) and len(pt) == 4 and pt[0]:
                out.setdefault(name, {})[pt[0]] = (pt[1], pt[2], pt[3])
    return out


def build(history: dict, engine_traj: dict) -> dict:
    stars_by = _parse_history(history)
    engine_by = _parse_engine(engine_traj)
    merged: dict = {}
    for name in sorted(set(stars_by) | set(engine_by)):
        by_ts: dict = {}
        for ts, n in stars_by.get(name, {}).items():
            by_ts[ts] = [ts, None, n, None]
        for ts, (brs, n, health) in engine_by.get(name, {}).items():
            if ts in by_ts:                     # engine point wins: it carries more
                prev_stars = by_ts[ts][2]
                by_ts[ts] = [ts, brs, n if n is not None else prev_stars, health]
            else:
                by_ts[ts] = [ts, brs, n, health]
        pts = [by_ts[ts] for ts in sorted(by_ts)]
        if pts:
            merged[name] = pts[-CAP:]
    return merged


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    ap.add_argument("--history", default="data/history.json")
    ap.add_argument("--engine", default="data/trajectory.json")
    a = ap.parse_args()
    try:
        history = json.loads(Path(a.history).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        history = {}
    try:
        engine_traj = json.loads(Path(a.engine).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — engine series lands via sync when available
        engine_traj = {}
    merged = build(history, engine_traj)
    out = Path(a.out) / "data" / "trajectory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    pts = sum(len(v) for v in merged.values())
    brs_pts = sum(1 for v in merged.values() for p in v if p[1] is not None)
    print(f"trajectory ok: {len(merged)} projects · {pts} points "
          f"({brs_pts} with BRS) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
