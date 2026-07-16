#!/usr/bin/env python3
"""Build the Data API index (v10.0 "Feed").

One machine-readable front door for everything the radar publishes:
``data/api.json`` lists every endpoint with its kind, description, stability
grade, and schema pointer — plus the freshness contract and the licensing
terms. Everything a consumer needs to build on the feed without reading the
repository.

Built at deploy time by WALKING THE ASSEMBLED ARTIFACT: an endpoint is listed
only if the file actually exists in ``_site``, so the index can never promise
something the deploy does not carry. Descriptions live here; existence is
verified there.

    python3 scripts/build_api_index.py --out _site
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://axonos-bci.github.io/axonos-community-radar"
API_VERSION = 1

# path -> (kind, stability, schema, description)
CATALOG = {
    "data/radar.json": (
        "dataset", "stable", "data/radar.schema.json",
        "The scored map: every kept project with its BRS, evidence ledger, facets "
        "(modality / paradigm / stage / standards), health signals, and deltas; plus "
        "the coverage matrix, standards graph, and builders board."),
    "data/radar.schema.json": (
        "schema", "stable", None,
        "JSON Schema for data/radar.json."),
    "data/signals.json": (
        "dataset", "stable", "data/signals.schema.json",
        "What changed this week: new / rising / cooling, each with the measured "
        "evidence that produced it. Ids are stable per (kind, project, ISO week)."),
    "data/signals.schema.json": (
        "schema", "stable", None,
        "JSON Schema for data/signals.json."),
    "data/projects.ndjson": (
        "export", "stable", None,
        "One project per line (NDJSON) — streams straight into pandas, jq, DuckDB."),
    "data/projects.csv": (
        "export", "stable", None,
        "Flat CSV of the map's core columns — spreadsheets, BI tools, quick sorts."),
    "data/ecosystem.json": (
        "dataset", "stable", None,
        "The AxonOS ecosystem manifest with live repo signals."),
    "data/badge-ecosystem.json": (
        "badge", "stable", None,
        "Shields.io endpoint badge: project count and median health, live."),
    "data/history.json": (
        "dataset", "stable", None,
        "Aggregate snapshots over time — totals, stars, category mix per scan."),
    "data/weekly.json": (
        "dataset", "stable", None,
        "The week in one small file: deltas the UI reads instantly."),
    "data/status.json": (
        "ops", "stable", None,
        "Last-scan operational read-out: scanned, dropped, failed topics, rate budget."),
    "data/last_run.json": (
        "ops", "stable", None,
        "Outcome of the most recent engine run — ok flag, reason, counts."),
    "data/first_seen.json": (
        "dataset", "stable", None,
        "First-seen timestamp per project — the discovery log behind the 'new' flag."),
    "data/interop-vocab.json": (
        "vocabulary", "stable", None,
        "The open interop vocabulary: 20 tags, 52 patterns — the matcher is open too."),
    "feed.xml": (
        "feed", "stable", None,
        "RSS of new arrivals on the map."),
    "feeds/signals.xml": (
        "feed", "stable", None,
        "RSS — every signal (new + rising + cooling)."),
    "feeds/new.xml": (
        "feed", "stable", None,
        "RSS — newly discovered BCI projects only."),
    "feeds/rising.xml": (
        "feed", "stable", None,
        "RSS — measured 7-day momentum only."),
}


def build_index(site: Path) -> dict:
    generated = None
    radar = site / "data" / "radar.json"
    if radar.exists():
        try:
            generated = json.loads(radar.read_text(encoding="utf-8")).get("generated_at")
        except Exception:  # noqa: BLE001
            generated = None
    endpoints = []
    for path, (kind, stability, schema, desc) in sorted(CATALOG.items()):
        f = site / path
        if not f.exists():
            continue
        e = {"path": path, "url": f"{BASE}/{path}", "kind": kind,
             "stability": stability, "bytes": f.stat().st_size, "description": desc}
        if schema and (site / schema).exists():
            e["schema"] = f"{BASE}/{schema}"
        endpoints.append(e)
    return {
        "api_version": API_VERSION,
        "generated_at": generated or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "base": BASE,
        "freshness": {
            "contract": "The engine scans every 3 hours; the site syncs and redeploys on its own "
                        "clock minutes later. generated_at above is the scan this deploy carries.",
            "engine_cron": "17 */3 * * *",
            "monitor": "a health workflow alerts on staleness twice daily",
        },
        "conventions": {
            "cors": "GitHub Pages serves Access-Control-Allow-Origin: * — fetch from anywhere.",
            "caching": "Standard ETag / conditional GET; poll politely (the data moves every 3h).",
            "stability": "additive within api_version; removals or renames bump api_version",
        },
        "licensing": {
            "data": "Free to use with attribution — link to the radar. The map stays free.",
            "commercial": "Licensed feeds, SLAs, and custom slices for funds and labs: "
                          "connect@axonos.org",
        },
        "endpoints": endpoints,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    a = ap.parse_args()
    site = Path(a.out)
    payload = build_index(site)
    out = site / "data" / "api.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"api index ok: {len(payload['endpoints'])} endpoints -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
