#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""One wallet address, checksum-valid, in every place that can take a payment.

A Dogecoin transfer is irreversible, so this is the gate with the worst failure
mode in the repository. It ran as twenty-eight lines of Python inside a YAML
string, where it could not be run locally, linted, or covered by a test.

Why the root is `data/payment.json`: see docs/DECISIONS.md.

    python3 scripts/gates/check_funding.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

ALPH = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58check(s: str) -> bool:
    """Base58Check with Dogecoin's version byte, so a typo fails here."""
    n = 0
    for ch in s:
        if ch not in ALPH:
            return False
        n = n * 58 + ALPH.index(ch)
    try:
        raw = n.to_bytes(25, "big")
    except OverflowError:
        return False
    return (raw[0] == 0x1E
            and hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4] == raw[-4:])


def check(root: pathlib.Path = ROOT) -> list[str]:
    """Return a list of problems; empty means the funding surface is consistent."""
    problems: list[str] = []
    pay = json.loads((root / "data" / "payment.json").read_text(encoding="utf-8"))
    reg = json.loads((root / "data" / "ecosystem-registry.json").read_text(encoding="utf-8"))["funding"]

    if reg["address"] != pay["address"]:
        problems.append(
            f"ecosystem-registry.json has drifted from data/payment.json: "
            f"{reg['address']} vs {pay['address']}")

    addr = pay["address"]
    if not b58check(addr):
        problems.append(f"{addr} fails Base58Check")

    for rel in ("assets/app.js", "support.html", ".github/FUNDING.yml"):
        p = root / rel
        if not p.exists():
            problems.append(f"{rel} is missing")
            continue
        text = p.read_text(encoding="utf-8")
        if addr not in text:
            problems.append(f"{rel} does not carry the canonical address")
        others = set(re.findall(r"\bD[1-9A-HJ-NP-Za-km-z]{25,40}\b", text)) - {addr}
        if others:
            problems.append(f"{rel} carries a foreign D-address: {sorted(others)}")
    return problems


def main() -> int:
    problems = check()
    for p in problems:
        print(f"::error::{p}")
    if problems:
        return 1
    addr = json.loads((ROOT / "data" / "payment.json").read_text())["address"]
    print(f"funding consistency ok: {addr} (Base58Check valid, single-source)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
