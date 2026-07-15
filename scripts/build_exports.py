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
"""
from __future__ import annotations

import argparse
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
    print(f"exports ok: projects.ndjson ({n} lines) -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
