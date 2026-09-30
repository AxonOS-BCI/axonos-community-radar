#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""One design system across every page, measured rather than assumed.

15.3.0 raised `--faint` from #6b7488 (4.29:1 on this background, below WCAG AA)
to #828da1 (6.02:1) — in `assets/app.css`. The token was declared in two more
stylesheets, `support.css` and `stats.css`, and nobody changed those. So the
support and stats pages went on shipping text that failed contrast for weeks
after the fix, on the smallest labels, where the bar is hardest to clear.

A token copied into three files is three tokens. This fails if any stylesheet
declares a shared token differently from the others, and if any text token on
any page falls below AA.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Stylesheets this repository does not own. report.css arrives with report.html
#: from the private engine every scan (the commits are the bot's "refresh report
#: page"), so an edit made here is overwritten within three hours. Holding it to
#: the house tokens here would make this test flap with every sync; its own
#: palette is the engine's to change.
ENGINE_OWNED = {"report.css"}

ALL_SHEETS = sorted((ROOT / "assets").glob("*.css"))
SHEETS = [p for p in ALL_SHEETS if p.name not in ENGINE_OWNED]
TEXT_TOKENS = ("ink", "dim", "faint")
BG = "#06070b"


def declared(path: pathlib.Path) -> dict[str, str]:
    root = re.search(r":root\s*\{([^}]*)\}", path.read_text(encoding="utf-8"))
    if not root:
        return {}
    return {k: v.lower() for k, v in re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", root.group(1))}


def _lin(c: int) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def contrast(fg: str, bg: str) -> float:
    def lum(h):
        r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
        return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)
    a, b = lum(fg), lum(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def test_there_are_stylesheets_to_check():
    assert len(SHEETS) >= 4, [p.name for p in SHEETS]


@pytest.mark.parametrize("token", TEXT_TOKENS + ("bg", "accent"))
def test_a_shared_token_has_one_value_everywhere_it_is_declared(token):
    values = {p.name: declared(p).get(token) for p in SHEETS}
    values = {k: v for k, v in values.items() if v}
    assert len(set(values.values())) <= 1, (
        f"--{token} differs between stylesheets: {values}. A token copied into several "
        f"files is several tokens; change all of them or none")


def _aa_cases():
    for p in ALL_SHEETS:
        if p.name in ENGINE_OWNED:
            # A real failure on a live page: --faint #6b7789 is 4.31:1 on the
            # report's #090c11. The fix belongs in the engine's report template.
            # Strict, so the day the engine fixes it this XPASSes, fails, and
            # the marker has to be removed rather than lingering as a stale excuse.
            yield pytest.param(p, id=p.name, marks=pytest.mark.xfail(
                strict=True, reason="report.css is rendered by the private engine; "
                                    "its --faint fails AA and must be fixed there"))
        else:
            yield pytest.param(p, id=p.name)


@pytest.mark.parametrize("sheet", list(_aa_cases()))
def test_every_text_token_passes_aa_on_the_page_background(sheet):
    toks = declared(sheet)
    bg = toks.get("bg", BG)
    for t in TEXT_TOKENS:
        if t in toks:
            ratio = contrast(toks[t], bg)
            assert ratio >= 4.5, f"{sheet.name}: --{t} {toks[t]} is {ratio:.2f}:1, AA asks 4.5"


def test_faint_stays_below_dim_so_the_hierarchy_survives():
    for p in SHEETS:
        t = declared(p)
        if "faint" in t and "dim" in t:
            assert contrast(t["faint"], BG) < contrast(t["dim"], BG), \
                f"{p.name}: --faint is no longer quieter than --dim"
