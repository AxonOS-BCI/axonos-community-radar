#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""What the QR code actually encodes, decoded, not described.

16.3.0 shipped a check called "the QR and the explorer point at the canonical
address" and a release note claiming a swapped QR fails the suite. Neither was
true. The check read the `alt` attribute in the HTML; the mutation that
"proved" it edited that same attribute. Nothing in the repository had ever read
a single pixel of `assets/doge-qr.svg`.

So the attack it was supposed to stop went straight through: correct address in
the text, correct address in the alt, correct filename in `payment.json`, and a
replaced SVG encoding somebody else's wallet. Every check passes and the page
looks right. A claim about a financial instrument that rests on its own label is
not a check, and describing it as one was the more serious half of the mistake.

This decodes the image. The SVG is a path of unit squares, so the module grid is
recovered from the path data, rendered to a bitmap and read by an actual QR
decoder. The decoded payload is then compared with `data/payment.json`.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAYMENT = json.loads((ROOT / "data" / "payment.json").read_text(encoding="utf-8"))
QR_PATH = ROOT / PAYMENT["qr"]

#: Dark-module count of the committed code. A structural fingerprint, checked
#: even where a decoder is unavailable, so a replaced file is never silently
#: unexamined. It is not a substitute for decoding and is not treated as one.
EXPECTED_MODULES = 33
EXPECTED_DARK = 554


def module_grid() -> list[list[int]]:
    """Recover the QR module matrix from the SVG's path data."""
    svg = QR_PATH.read_text(encoding="utf-8")
    d = re.search(r'd="([^"]+)"', svg)
    assert d, f"{QR_PATH.name} has no path data; it is not the QR this expects"
    cells = {
        (int(x), int(y))
        for x, y, _, _ in re.findall(r"M(\d+),(\d+)H(\d+)V(\d+)", d.group(1))
    }
    assert cells, "no modules in the path"
    x0, y0 = min(c[0] for c in cells), min(c[1] for c in cells)
    n = max(max(c[0] for c in cells), max(c[1] for c in cells)) - min(x0, y0) + 1
    return [[1 if (x0 + c, y0 + r) in cells else 0 for c in range(n)] for r in range(n)]


def test_the_qr_file_exists_where_the_contract_says():
    assert QR_PATH.exists(), f"{PAYMENT['qr']} is named in payment.json and is not there"


def test_the_grid_is_the_shape_and_density_it_was():
    """Cheap, dependency-free, and enough to notice a replaced file."""
    grid = module_grid()
    assert len(grid) == EXPECTED_MODULES, \
        f"the QR is {len(grid)} modules across, was {EXPECTED_MODULES}"
    dark = sum(sum(row) for row in grid)
    assert dark == EXPECTED_DARK, (
        f"the QR has {dark} dark modules, was {EXPECTED_DARK} — the image changed; "
        f"if that was deliberate, decode it, confirm the payload and update this number"
    )


def _decode(grid) -> str:
    cv2 = pytest.importorskip(
        "cv2",
        reason="opencv is required to decode the QR; CI installs it from "
               "requirements-ci.txt and the decode is mandatory there",
    )
    import numpy as np

    scale, quiet = 8, 4
    n = len(grid)
    side = (n + 2 * quiet) * scale
    img = np.full((side, side), 255, np.uint8)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v:
                y, x = (r + quiet) * scale, (c + quiet) * scale
                img[y:y + scale, x:x + scale] = 0
    text, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    assert text, "the QR could not be decoded at all"
    return text


def test_the_qr_decodes_to_the_canonical_payment_uri():
    """The whole point. What the camera reads is what the contract says."""
    decoded = _decode(module_grid())
    assert decoded == PAYMENT["uri"], (
        f"the QR encodes {decoded!r}; payment.json says {PAYMENT['uri']!r}"
    )


def test_the_decoded_address_is_the_canonical_one():
    decoded = _decode(module_grid())
    addr = decoded.split(":", 1)[-1].split("?", 1)[0]
    assert addr == PAYMENT["address"], (
        f"the QR pays {addr}, the contract pays {PAYMENT['address']}"
    )


def test_the_decoded_payload_carries_no_amount_or_extra_parameters():
    """The QR is the address. The amount belongs to the plan, not the image."""
    decoded = _decode(module_grid())
    assert "?" not in decoded, (
        f"the QR carries parameters ({decoded!r}); a fixed amount baked into the "
        f"image outlives whatever the page says it is for"
    )
