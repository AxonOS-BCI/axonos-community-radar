#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""Public text keeps internal names out.

Design references, benchmarks and the names of other services we study are
internal working notes; they do not belong in pages, documents, comments or
code that this repository publishes. The names are held below only as
truncated SHA-256 digests, so this file publishes none of them.
"""
from __future__ import annotations

import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
HIDDEN = {"3302cd1c71a05313", "38b703a1b45987fb", "528d3dd93ab7d2b8", "6c121325bd0f751e", "ab1aeaa87644e79f", "bc8b0da63de43cc0", "df6db9c0c9d12405"}
SKIP = {"data", ".git", "node_modules"}
EXT = {".html", ".md", ".css", ".js", ".mjs", ".py", ".yml", ".yaml", ".json", ".txt", ".cff", ".xml", ".svg"}


def tokens(text: str):
    for t in re.findall(r"[a-z0-9][a-z0-9.\-]*[a-z0-9]", text.lower()):
        yield t
        for part in t.split("."):
            yield part


def test_no_published_file_names_an_internal_reference():
    hits = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in EXT or SKIP & set(p.relative_to(ROOT).parts):
            continue
        for t in set(tokens(p.read_text(encoding="utf-8", errors="ignore"))):
            if hashlib.sha256(t.encode()).hexdigest()[:16] in HIDDEN:
                hits.append(str(p.relative_to(ROOT)))
                break
    assert not hits, f"internal names in published files: {sorted(hits)}"
