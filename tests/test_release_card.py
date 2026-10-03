#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""This repository's own project card carries the version the commit carries.

`scripts/build_project_cards.py` reads each repository's VERSION from its
default branch, so on the push of a release commit the generator already sees
the new version. 16.10.1 and 16.10.2 shipped the card one version behind —
16.10.2 on the mistaken reading that the card follows the latest *release* —
and the release-hygiene job went red on both. The card and VERSION change in
the same commit; this fails before CI has to.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_the_radar_card_states_this_commit_s_version():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<span class="ax-ver">([^<]+)</span></div><h3>axonos-community-radar</h3>', html)
    assert m, "index.html has no card for this repository"
    assert m.group(1) == version, f"the card says {m.group(1)}, VERSION says {version}"


def test_the_readme_figure_ships_in_both_themes():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "```mermaid" not in readme, "the README figure is a drawing, not a generated chart"
    for theme in ("dark", "light"):
        rel = f"assets/readme/how-it-works-{theme}.svg"
        assert rel in readme, f"the README does not reference {rel}"
        svg = (ROOT / rel).read_text(encoding="utf-8")
        assert svg.startswith("<svg") and "aria-label=" in svg and "<script" not in svg.lower()
