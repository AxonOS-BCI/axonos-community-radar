#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""No live count may be frozen into the README.

The map is rescored every three hours, so "120+ BCI projects" on a static badge
and "31 near misses" in a diagram are right on the morning they are written and
wrong by the evening. The live figures belong in the badge endpoint and
data/status.json, which measure them.

    python3 scripts/gates/check_frozen_counts.py
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: A static shields.io badge asserting a project count, and prose asserting a
#: near-miss count. Both have appeared; both went stale the same day.
PATTERNS = (
    (r"img\.shields\.io/badge/[^)\s]*?(\d{2,5})%2B?%20(?:BCI%20)?projects",
     "static badge claiming {} projects"),
    (r"(?<![\w.])(\d{2,4})\s+near\s+miss",
     "prose claiming {} near misses"),
)


def check(root: pathlib.Path = ROOT) -> list[str]:
    text = (root / "README.md").read_text(encoding="utf-8")
    found = []
    for pattern, message in PATTERNS:
        for m in re.finditer(pattern, text):
            found.append("the README freezes a live count: " + message.format(m.group(1)))
    return found


def main() -> int:
    problems = check()
    for p in problems:
        print(f"::error::{p}")
    if problems:
        print("::error::use the live badge endpoint or data/status.json instead")
        return 1
    print("no live count is frozen into the README")
    return 0


if __name__ == "__main__":
    sys.exit(main())
