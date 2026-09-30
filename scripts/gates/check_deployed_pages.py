#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""Every page this site links to is a page the deploy actually ships.

16.7.0 added `pro.html`, linked it from the navigation of every page, rendered
it in a real browser at two widths, clicked its buttons — and never added it to
the list of files `pages.yml` copies into the Pages artefact. The deploy copies
an explicit list on purpose, so tooling never leaks onto the public host. The
consequence was a PRO link on every page that answered 404.

Every local test passed, because every local test opened the file from disk.
None of them looked at the one step between the repository and the site.

This reads the deploy's own copy command and checks it against the links: a
page linked from any page must be deployed, and every root-level page must be
either deployed or named here as deliberately withheld.

    python3 scripts/gates/check_deployed_pages.py
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Root-level HTML that exists but is intentionally not published. Empty today;
#: a page added here must say why.
WITHHELD: dict[str, str] = {}


def deployed(root: pathlib.Path = ROOT) -> set[str]:
    wf = yaml.safe_load((root / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8"))
    for job in wf["jobs"].values():
        for step in job.get("steps") or []:
            if "Assemble" in (step.get("name") or ""):
                return set(re.findall(r"\b([\w-]+\.html)\b", step.get("run", "")))
    raise RuntimeError("pages.yml has no Assemble step; the deploy manifest cannot be read")


def check(root: pathlib.Path = ROOT) -> list[str]:
    ships = deployed(root)
    problems = []
    pages = sorted(p.name for p in root.glob("*.html"))
    for name in pages:
        if name not in ships and name not in WITHHELD:
            problems.append(f"{name} exists at the root but the deploy does not copy it "
                            f"and it is not listed as withheld")
        text = (root / name).read_text(encoding="utf-8")
        for target in sorted(set(re.findall(r'href="\./([\w-]+\.html)', text))):
            if target not in ships:
                problems.append(f"{name} links to {target}, which the deploy does not ship — "
                                f"a 404 on the live site")
    return problems


def main() -> int:
    problems = check()
    for p in problems:
        print(f"::error::{p}")
    if problems:
        return 1
    print(f"every linked page is deployed: {', '.join(sorted(deployed()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
