#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Denis Yermakou <connect@axonos.org>
"""Check report.html against the thing it actually is.

The previous gate required `report.html` to name this repository's release. It
could not hold, and the reason is structural rather than careless: the report is
rendered and published by the *scanner*, a separate repository with its own
version file, every three hours. So a correct release here — with the report
re-rendered at the new version — was overwritten by the next scan with a report
stamped at the scanner's version, and this gate then failed on the file the
release had just fixed. Synchronising the two numbers would have delayed the
next divergence by exactly one release.

There is one product and one version of it, and it is this repository's. The
report no longer claims to carry it. What it carries is the identity of the
snapshot it renders, which is derived from the payload on the page and therefore
cannot disagree with it — so that is what is checked here, along with the two
properties that were always the point:

1. the report renders the payload this repository publishes, not an older one;
2. it leaks no link into the private scanner.

A version string cannot be checked here without recreating the defect, so it
is not.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_SKEW_HOURS = 12.0


def fail(msg: str) -> int:
    print(f"::error::{msg}")
    return 1


def main() -> int:
    report = ROOT / "report.html"
    payload = ROOT / "data" / "radar.json"
    if not report.exists():
        return fail("report.html is absent")
    html = report.read_text(encoding="utf-8", errors="replace")

    if "axonos-radar-core" in html:
        return fail("report.html leaks a link into the private scanner")

    m = re.search(r"Snapshot\s+([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2})", html)
    if not m:
        return fail("report.html carries no snapshot identity — it should say which "
                    "payload it renders")
    stamped = m.group(1)

    if not payload.exists():
        print(f"report.html: links clean, snapshot {stamped} (no payload to compare)")
        return 0

    try:
        gen = json.loads(payload.read_text(encoding="utf-8")).get("generated_at", "")
    except Exception as e:  # noqa: BLE001
        return fail(f"data/radar.json is unreadable: {e}")

    expected = str(gen)[:16].replace("T", " ")
    if stamped != expected:
        # Not fatal on its own: the scanner publishes the report and the payload
        # in separate commits, so one can land a moment before the other. It is
        # fatal when the gap is large, because that means the report is stale.
        try:
            a = datetime.fromisoformat(stamped.replace(" ", "T")).replace(tzinfo=timezone.utc)
            b = datetime.fromisoformat(expected.replace(" ", "T")).replace(tzinfo=timezone.utc)
            skew = abs((a - b).total_seconds()) / 3600
        except Exception:  # noqa: BLE001
            return fail(f"report.html renders snapshot {stamped}, payload says {expected}")
        if skew > MAX_SKEW_HOURS:
            return fail(f"report.html renders snapshot {stamped} but the payload is "
                        f"{expected} — {skew:.1f}h apart, so the report is stale")
        print(f"report.html: links clean, snapshot {stamped}, payload {expected} "
              f"({skew:.1f}h apart, within tolerance)")
        return 0

    print(f"report.html: links clean, snapshot {stamped} matches the payload")
    return 0


if __name__ == "__main__":
    sys.exit(main())
