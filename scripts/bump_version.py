#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""Move every surface that states the version, in one step.

    python3 scripts/bump_version.py 16.11.1

The version is stated in nine places: VERSION, the README badge and its
citation, CITATION.cff and its release date, the footer chips of index.html
and stats.html, this repository's own project card, and the social card,
which draws it. 16.10.0 to 16.11.0 each forgot at least one of them, and CI
caught it after the push. Write the CHANGELOG entry first — its heading,
`## [X.Y.Z] — YYYY-MM-DD — "Title"`, is the source of the version and the
date — then run this; it rewrites the rest, redraws the card, and runs the
version gate. Nothing is guessed: each surface must be found exactly once.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def edit(rel: str, pattern: str, new: str) -> None:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    out, n = re.subn(pattern, new, text, flags=re.M)
    if n != 1:
        sys.exit(f"{rel}: expected one match for {pattern!r}, found {n}")
    p.write_text(out, encoding="utf-8")


def load(rel: str):
    """A sibling script as a module: no subprocess, no shell."""
    spec = importlib.util.spec_from_file_location(pathlib.Path(rel).stem, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if len(sys.argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
        print(__doc__)
        return 2
    new = sys.argv[1]
    top = re.search(r"^## \[([0-9.]+)\] — (\d{4}-\d{2}-\d{2})",
                    (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
    if not top or top.group(1) != new:
        print(f"Write the CHANGELOG entry first: the top heading must be ## [{new}] — YYYY-MM-DD — \"Title\"")
        return 2
    date = top.group(2)
    (ROOT / "VERSION").write_text(new + "\n", encoding="utf-8")
    v = r"[0-9]+\.[0-9]+\.[0-9]+"
    edit("README.md", rf"badge/version-{v}-", f"badge/version-{new}-")
    edit("README.md", rf"version = \{{{v}\}}", f"version = {{{new}}}")
    edit("CITATION.cff", rf"^version: {v}$", f"version: {new}")
    edit("CITATION.cff", r'^date-released: .*$', f'date-released: "{date}"')
    edit("index.html", rf'<span class="vchip">Radar v{v}</span>', f'<span class="vchip">Radar v{new}</span>')
    edit("index.html", rf'<span class="ax-ver">{v}</span></div><h3>axonos-community-radar</h3>',
         f'<span class="ax-ver">{new}</span></div><h3>axonos-community-radar</h3>')
    edit("stats.html", rf'<span class="vchip">v{v}</span>', f'<span class="vchip">v{new}</span>')
    card, argv = load("scripts/build_og_image.py"), sys.argv
    sys.argv = ["build_og_image.py", "--write"]
    try:
        if card.main() != 0:
            return 1
    finally:
        sys.argv = argv
    errs = load("scripts/gates/check_version_consistency.py").check(ROOT)
    for e in errs:
        print(f"::error::{e}")
    if not errs:
        print(f"every surface says {new}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
