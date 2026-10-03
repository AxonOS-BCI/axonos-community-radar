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

    # This repository's own project card: the card generator reads VERSION from
    # main, so the card must change in the same commit (16.10.1 and 16.10.2 did not).
    m = re.search(r'<span class="ax-ver">([^<]+)</span></div><h3>axonos-community-radar</h3>',
                  (root / "index.html").read_text(encoding="utf-8"))
    if not m or m.group(1) != v:
        errs.append(f"index.html own project card {m.group(1) if m else '?'} != {v}")

    # The citation's release date is the date of the release it cites.
    top = re.search(r"^## \[([0-9.]+)\] — (\d{4}-\d{2}-\d{2})", chlog, re.M)
    rel = re.search(r'^date-released: "?(\d{4}-\d{2}-\d{2})"?', cff, re.M)
    if top and (not rel or rel.group(1) != top.group(2)):
        errs.append(f"CITATION.cff date-released {rel.group(1) if rel else '?'} != CHANGELOG {top.group(2)}")

    # The social card draws the version; it also records it, so this gate can
    # read it without Pillow (16.10.0 to 16.11.0 shipped a card saying 16.9.0).
    card = root / "og-image.png"
    if card.exists():
        stamped = png_text(card.read_bytes()).get("version")
        if stamped != v:
            errs.append(f"og-image.png is stamped {stamped or 'nothing'}, not {v}: "
                        "run python3 scripts/build_og_image.py --write")
    return errs


def png_text(data: bytes) -> dict[str, str]:
    """tEXt chunks of a PNG, read with the standard library alone."""
    import struct
    out: dict[str, str] = {}
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return out
    i = 8
    while i + 8 <= len(data):
        n, kind = struct.unpack(">I4s", data[i:i + 8])
        body = data[i + 8:i + 8 + n]
        if kind == b"tEXt" and b"\x00" in body:
            k, _, val = body.partition(b"\x00")
            out[k.decode("latin-1")] = val.decode("latin-1")
        if kind == b"IEND":
            break
        i += 12 + n
    return out


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
