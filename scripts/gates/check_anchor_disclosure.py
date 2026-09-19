#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""While the payload force-includes projects, the docs must say so — and must
not say the opposite.

Some AxonOS repositories are placed in the map as ecosystem anchors rather than
admitted by the gate. Two separate obligations follow, and shipping only the
first is what happened in 16.2.0: the disclosure appeared three hundred lines
down while the opening sentence still claimed a universal gate.

So this checks both directions. See docs/DECISIONS.md for why the patterns are
anchored rather than substrings.

    python3 scripts/gates/check_anchor_disclosure.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

DOCS = ("README.md", "docs/METHODOLOGY.md")

#: Claims that a universal gate applies. `(?<!almost )` matters: the corrected
#: sentence contains the wrong one as a substring, so an unanchored list flagged
#: its own fix.
CONTRADICTIONS = (
    r"kept only if its BRS clears the gate",
    r"(?<!almost )every project here cleared a scored gate",
    r"(?<!almost )every project cleared the gate",
    r"(?<!almost )all projects here cleared",
)


def forced(root: pathlib.Path = ROOT) -> list[str]:
    projects = json.loads((root / "data" / "radar.json").read_text(encoding="utf-8"))["projects"]
    return [p["full_name"] for p in projects if p.get("ecosystem")]


def check(root: pathlib.Path = ROOT) -> list[str]:
    names = forced(root)
    if not names:
        return []
    problems = []
    for doc in DOCS:
        text = (root / doc).read_text(encoding="utf-8")
        if "ecosystem anchor" not in text.lower():
            problems.append(
                f"{doc} does not mention the ecosystem anchors, and "
                f"{len(names)} repositories are in the map as one")
        for bad in CONTRADICTIONS:
            if re.search(bad, text, re.I):
                problems.append(f"{doc} still claims a universal gate: {bad!r}")
    return problems


def main() -> int:
    problems = check()
    for p in problems:
        print(f"::error::{p}")
    if problems:
        return 1
    names = forced()
    print(f"{len(names)} ecosystem anchors in the map, named in the docs"
          if names else "no force-included projects in the payload")
    return 0


if __name__ == "__main__":
    sys.exit(main())
