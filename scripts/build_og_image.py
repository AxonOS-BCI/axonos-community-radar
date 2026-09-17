#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""Build og-image.png, the card that appears when the radar is shared.

The previous card was committed as a binary with no source, which meant its
text could not be checked against anything and drifted: it advertised
"auto-refreshed every 6h" while every other surface — the README, the page
footer, the changelog, the workflow cron — said three hours. A social preview
is the one image most people see before they see the site, and nothing in the
repository could tell it was wrong.

So the card is generated from this file. The strings it draws are read from
`VERSION` and passed in, the cadence is asserted against `.github/workflows/`
before anything is drawn, and `tests/test_og_image.py` fails if the committed
PNG stops matching what this script produces.

    python3 scripts/build_og_image.py --check     # verify the committed file
    python3 scripts/build_og_image.py --write     # regenerate it
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "assets" / "foundation-banner.jpg"
OUT = ROOT / "og-image.png"

W, H = 1200, 630

BG_TOP = (10, 17, 33)
BG_BOTTOM = (6, 9, 18)
INK = (232, 238, 244)
DIM = (154, 163, 184)
FAINT = (130, 141, 161)
CYAN = (45, 212, 255)

PILLS = [
    ("Hardware", (45, 212, 255)),
    ("Decoding & ML", (167, 139, 250)),
    ("Real-time", (52, 211, 153)),
    ("Privacy", (248, 113, 113)),
]

FONT_DIR = pathlib.Path("/usr/share/fonts/truetype/dejavu")


def cadence_hours() -> int:
    """The refresh cadence, read from the workflow rather than remembered."""
    text = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    m = re.search(r"cron:\s*['\"]\s*\d+\s+\*/(\d+)", text)
    if not m:
        raise SystemExit("could not read the deploy cadence from pages.yml")
    return int(m.group(1))


def font(name: str, size: int):
    from PIL import ImageFont

    return ImageFont.truetype(str(FONT_DIR / name), size)


def build():
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (W, H), BG_BOTTOM)
    draw = ImageDraw.Draw(img)

    # Vertical gradient, drawn rather than shipped as a flat fill so the card
    # has the same depth as the site it advertises.
    for y in range(H):
        t = y / (H - 1)
        draw.line(
            [(0, y), (W, y)],
            fill=tuple(round(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)),
        )

    # The Foundation banner supplies the right third. It is cropped to the dog
    # and the gold arcs beside it, then faded into the background on its left
    # edge so the seam is not a vertical line across the card.
    art = Image.open(ART).convert("RGB")
    crop = art.crop((600, 0, art.width, art.height))
    scale = H / crop.height
    crop = crop.resize((round(crop.width * scale), H), Image.LANCZOS)

    mask = Image.new("L", crop.size, 255)
    fade = 200
    mdraw = ImageDraw.Draw(mask)
    for x in range(fade):
        mdraw.line([(x, 0), (x, crop.height)], fill=round(255 * (x / fade) ** 1.6))
    img.paste(crop, (W - crop.width, 0), mask)

    # Wordmark
    draw.ellipse([56, 44, 82, 70], fill=CYAN)
    draw.text((94, 46), "AxonOS", font=font("DejaVuSans-Bold.ttf", 22), fill=INK)

    draw.text((56, 150), "AxonOS Radar", font=font("DejaVuSans-Bold.ttf", 68), fill=INK)

    sub = font("DejaVuSans.ttf", 27)
    draw.text((58, 250), "An auditable map of open", font=sub, fill=DIM)
    draw.text((58, 288), "brain–computer interface work.", font=sub, fill=DIM)

    # Pills
    pf = font("DejaVuSans-Bold.ttf", 17)
    x = 58
    for label, colour in PILLS:
        w = draw.textlength(label, font=pf)
        box = [x, 366, x + w + 46, 366 + 38]
        draw.rounded_rectangle(box, radius=19, outline=colour, width=2)
        draw.ellipse([x + 16, 381, x + 24, 389], fill=colour)
        draw.text((x + 32, 374), label, font=pf, fill=INK)
        x = box[2] + 12

    hours = cadence_hours()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    foot = (
        f"axonos.org  ·  rescored every {hours}h  ·  every score carries its "
        f"evidence  ·  v{version}"
    )
    draw.text((58, 548), foot, font=font("DejaVuSans.ttf", 17), fill=FAINT)

    return img


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    img = build()
    import io

    from PIL import Image

    # Quantised to 256 colours. A card built around a photograph is a large
    # PNG — 423 kB at full depth — and this file has to travel inside a patch.
    # 168 kB at 256 colours is indistinguishable at the size a social card is
    # ever shown, and the choice is written down here rather than left as an
    # unexplained artefact in the repository.
    flat = img.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
    buf = io.BytesIO()
    flat.save(buf, "PNG", optimize=True)
    made = buf.getvalue()

    if args.write:
        OUT.write_bytes(made)
        print(f"wrote {OUT.name}: {len(made)} bytes, {img.width}x{img.height}")
        return 0

    if args.check:
        if not OUT.exists():
            print("::error::og-image.png is missing")
            return 1
        have = OUT.read_bytes()
        if hashlib.sha256(have).hexdigest() != hashlib.sha256(made).hexdigest():
            print("::error::og-image.png does not match what build_og_image.py produces")
            print("::error::run: python3 scripts/build_og_image.py --write")
            return 1
        print(f"og-image.png matches its generator ({len(have)} bytes)")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
