#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""One bar, one house stylesheet, on every page this repository owns.

The navigation was written four times, once per page stylesheet, and the four
had drifted: two were 52 px tall and one was sized by padding, two were 1140 px
wide and one 960, weights of 500 and 550, stacking levels of 50 and 40. Moving
between pages, the bar shifted by a few pixels and changed its links — the map
offered AxonOS and Medium, the stats page offered neither, the support page had
no RSS. Small, and exactly the kind of thing that makes a product look like four
sites.

`assets/house.css` owns the bar now. This fails if a page stops loading it, if
a page's links differ from the others', if the current page is not the one
marked, or if a page stylesheet starts restyling the bar again.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Pages this repository owns. report.html is rendered by the scanning engine on
#: every scan and carries the engine's own bar until its template moves here.
PAGES = {"index.html": "Map", "stats.html": "Stats", "support.html": "Support", "pro.html": "PRO", "sample.html": "PRO"}
PAGE_CSS = ("app.css", "stats.css", "support.css", "product.css")
EXPECTED = ["Map", "Report", "Stats", "PRO", "Support", "RSS", "GitHub"]


def bar(name: str) -> str:
    html = (ROOT / name).read_text(encoding="utf-8")
    bars = re.findall(r'<nav class="gnav[^"]*"[^>]*>.*?</nav>', html, re.S)
    assert len(bars) == 1, f"{name} has {len(bars)} global bars"
    return bars[0]


@pytest.mark.parametrize("name", PAGES)
def test_every_page_loads_the_house_stylesheet_first(name):
    html = (ROOT / name).read_text(encoding="utf-8")
    sheets = re.findall(r'<link rel="stylesheet" href="(?:\./)?assets/([a-z]+\.css)">', html)
    assert sheets and sheets[0] == "house.css", f"{name} loads {sheets}; house.css must come first"


@pytest.mark.parametrize("name", PAGES)
def test_every_page_offers_the_same_links_in_the_same_order(name):
    labels = [re.sub(r"<[^>]+>", "", x).strip()
              for x in re.findall(r'<a class="nav-link[^"]*"[^>]*>(.*?)</a>', bar(name), re.S)]
    assert labels == EXPECTED, f"{name} bar reads {labels}"


@pytest.mark.parametrize("name,current", PAGES.items())
def test_the_current_page_and_only_it_is_marked(name, current):
    marked = re.findall(r'<a class="nav-link[^"]*"[^>]*aria-current="page"[^>]*>(.*?)</a>', bar(name))
    assert marked == [current], f"{name} marks {marked}, should mark {current}"


@pytest.mark.parametrize("css", PAGE_CSS)
def test_no_page_stylesheet_restyles_the_bar(css):
    text = (ROOT / "assets" / css).read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    for sel in (r"(?<![\w-])nav\s*\{", r"\.gnav(?![\w-])(?!\.static)", r"\.nav-link\b", r"\.nav-in\b", r"\.brand\b"):
        hits = re.findall(sel + r"[^{}]*\{", text)
        assert not hits, f"{css} restyles the shared bar: {hits[:2]}"


def test_the_bar_is_defined_once_and_the_wordmark_stays_for_screen_readers():
    house = (ROOT / "assets" / "house.css").read_text(encoding="utf-8")
    assert ".gnav{" in house and ".gnav .nav-link{" in house
    for name in PAGES:
        assert '<span class="bt">AxonOS Radar</span>' in bar(name), \
            f"{name}: the brand name must stay in the markup when a phone hides it visually"
