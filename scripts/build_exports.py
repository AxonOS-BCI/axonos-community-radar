#!/usr/bin/env python3
"""Deploy-time data exports for the AxonOS Radar (v6, "Solid Ground").

Researchers keep re-writing the same three lines of JSON unwrapping to get the
radar into pandas/jq. This builder ships the dataset in the shape those tools
want natively: one project per line (NDJSON), generated straight into the
Pages artifact next to radar.json — zero bot commits, always in sync with the
deployed data, exactly like the ecosystem manifest.

    python3 scripts/build_exports.py --out _site/data

Outputs:
    <out>/projects.ndjson   one JSON object per line, key-sorted, UTF-8
    <out>/projects.csv      the map's core columns, flat — spreadsheets, BI
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_ndjson(payload: dict) -> str:
    """Serialise projects as NDJSON. Deterministic: keys sorted, no floats
    reformatted, one '\\n' terminated line per project."""
    projects = payload.get("projects")
    if not isinstance(projects, list):
        raise ValueError("payload has no 'projects' list")
    lines = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        lines.append(json.dumps(p, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")))
    return "\n".join(lines) + ("\n" if lines else "")




# The flat view: the columns an analyst sorts on. Lists are joined with "|",
# nested structures stay in the NDJSON — a CSV that tries to carry everything
# carries nothing well. Column order is part of the contract.
CSV_COLUMNS = [
    "full_name", "html_url", "category", "brs", "relevance_tier",
    "evidence_tier", "stars", "stars_delta_7d", "forks", "contributors",
    "language", "license", "modality", "paradigm", "stage", "standards",
    "health_overall", "rising", "falling", "is_new", "first_seen",
    "last_commit", "created_at", "description",
]


def _cell(p, col):
    facets = p.get("facets") or {}
    if col in ("modality", "paradigm", "stage", "standards"):
        return "|".join(facets.get(col) or [])
    if col == "health_overall":
        return (p.get("signals") or {}).get("overall", "")
    if col in ("rising", "falling", "is_new"):
        return 1 if p.get(col) else 0
    v = p.get(col)
    return "" if v is None else v


def build_csv(payload: dict) -> str:
    """Deterministic CSV of the core columns; CRLF per RFC 4180."""
    projects = payload.get("projects")
    if not isinstance(projects, list):
        raise ValueError("payload has no 'projects' list")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(CSV_COLUMNS)
    for p in projects:
        if isinstance(p, dict):
            w.writerow([_cell(p, c) for c in CSV_COLUMNS])
    return buf.getvalue()


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "radar.json"))
    ap.add_argument("--out", required=True, help="output directory")
    args = ap.parse_args(argv)

    payload = json.loads(Path(args.data).read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    nd = build_ndjson(payload)
    (out_dir / "projects.ndjson").write_text(nd, encoding="utf-8")
    n = nd.count("\n")
    cv = build_csv(payload)
    (out_dir / "projects.csv").write_text(cv, encoding="utf-8")
    rows = cv.count("\r\n") - 1
    print(f"exports ok: projects.ndjson ({n} lines) + projects.csv ({rows} rows) -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
