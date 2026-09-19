#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""Every surface that states a version states the same one.

VERSION is the root. A half-finished bump is invisible to a reader and to a
citation, and this repository publishes both.

    python3 scripts/gates/check_version_consistency.py
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def check(root: pathlib.Path = ROOT) -> list[str]:
    v = (root / "VERSION").read_text(encoding="utf-8").strip()
    readme = (root / "README.md").read_text(encoding="utf-8")
    cff = (root / "CITATION.cff").read_text(encoding="utf-8")
    chlog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    errs = []

    if f"version-{v}-" not in readme:
        errs.append(f"README badge != {v}")
    m = re.search(r"version = \{([^}]+)\}", readme)
    if not m or m.group(1) != v:
        errs.append(f"README bibtex {m.group(1) if m else '?'} != {v}")
    m = re.search(r"^version: (.+)$", cff, re.M)
    if not m or m.group(1).strip() != v:
        errs.append(f"CITATION.cff != {v}")
    m = re.search(r"^## \[([0-9.]+)\]", chlog, re.M)
    if not m or m.group(1) != v:
        errs.append(f"CHANGELOG top {m.group(1) if m else '?'} != {v}")
    for page in ("index.html", "stats.html"):
        if f"v{v}" not in (root / page).read_text(encoding="utf-8"):
            errs.append(f"{page} footer chip != v{v}")
    return errs


def main() -> int:
    errs = check()
    for e in errs:
        print(f"::error::{e}")
    if errs:
        return 1
    v = (ROOT / "VERSION").read_text().strip()
    print(f"version {v} consistent across VERSION/README badge/bibtex/CITATION/CHANGELOG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
