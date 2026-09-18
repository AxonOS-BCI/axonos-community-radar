#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""The payment address and the prices are data with a test, not markup.

Two histories sit behind this file.

The prices lived only in HTML, and drifted three times: €9 and €29 became $99
and $500 while the older pair survived elsewhere on the page; a Subscribe button
pointed for weeks at a Sponsors page that was never enabled; and the launch
offer arrived beside two monthly plans with no stated relationship between them.
Each was found by a person reading the page, which is the slowest and least
reliable detector available.

The payment address has a worse failure mode. A Dogecoin transaction is
irreversible: an address wrong by one character in the QR, or in the `dogecoin:`
URI, or in the copy button, sends a stranger's money somewhere nobody controls,
and nothing on the page would look wrong. So the address is checked here in
every place it appears, against one canonical file, on every push.

`data/payment.json` and `data/commercial.json` are those canonical files. If the
rendered page and the contract disagree, this fails.
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = (ROOT / "support.html").read_text(encoding="utf-8")
PAYMENT = json.loads((ROOT / "data" / "payment.json").read_text(encoding="utf-8"))
COMMERCIAL = json.loads((ROOT / "data" / "commercial.json").read_text(encoding="utf-8"))

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58check_ok(addr: str) -> bool:
    """Base58Check, so a mistyped address fails here rather than on chain."""
    import hashlib

    num = 0
    for ch in addr:
        if ch not in B58:
            return False
        num = num * 58 + B58.index(ch)
    raw = num.to_bytes(25, "big")
    return hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4] == raw[-4:]


# --------------------------------------------------------------------------
# payment integrity
# --------------------------------------------------------------------------

def test_the_canonical_address_is_a_valid_dogecoin_address():
    addr = PAYMENT["address"]
    assert addr.startswith("D"), addr
    assert _b58check_ok(addr), f"{addr} fails Base58Check"


def test_every_address_on_the_page_is_the_canonical_one():
    """No second D-address, anywhere, in any form."""
    addr = PAYMENT["address"]
    found = set(re.findall(r"\bD[1-9A-HJ-NP-Za-km-z]{25,40}\b", PAGE))
    assert addr in found, "the canonical address is not on the page"
    assert found == {addr}, f"the page carries a foreign address: {found - {addr}}"


def test_the_payment_uri_carries_the_canonical_address_and_the_launch_amount():
    uris = re.findall(r'href="(dogecoin:[^"]+)"', PAGE)
    assert uris, "no dogecoin: URI on the page"
    launch = COMMERCIAL["plans"]["launch_annual"]["price"]
    for raw in uris:
        u = urllib.parse.urlparse(raw.replace("&amp;", "&"))
        assert u.path == PAYMENT["address"], f"{raw} pays a different address"
        q = urllib.parse.parse_qs(u.query)
        if "amount" in q:
            assert float(q["amount"][0]) == float(launch["amount"]), (
                f"{raw} asks for {q['amount'][0]}, the contract says {launch['amount']}"
            )


def test_the_qr_and_the_explorer_point_at_the_canonical_address():
    addr = PAYMENT["address"]
    assert PAYMENT["qr"].split("/")[-1] in PAGE, "the QR named in payment.json is not on the page"
    assert addr in PAYMENT["explorer"], "payment.json's explorer link is for another address"
    assert PAYMENT["explorer"] in PAGE.replace("&amp;", "&"), \
        "the explorer link on the page is not the one in payment.json"
    # The QR's alt text names the address it encodes, so a swapped image is visible.
    alts = re.findall(r'alt="[^"]*?(D[1-9A-HJ-NP-Za-km-z]{25,40})[^"]*"', PAGE)
    for a in alts:
        assert a == addr, f"a QR is labelled with {a}"


def test_the_page_warns_that_payment_is_irreversible():
    low = PAGE.lower()
    assert "irreversible" in low, "the page does not say crypto payments are irreversible"
    assert "seed" in low and "private key" in low, \
        "the page does not warn that a seed phrase is never requested"


# --------------------------------------------------------------------------
# commercial contract
# --------------------------------------------------------------------------

def _plan(key):
    return COMMERCIAL["plans"][key]


def test_every_price_on_the_page_comes_from_the_contract():
    rendered = re.findall(r'class="plan-p">([^<]+)<', PAGE)
    rendered = [r.replace("&nbsp;", " ").strip() for r in rendered]
    expected = []
    for key in ("launch_annual", "premium", "premium_pro"):
        pr = _plan(key)["price"]
        if pr["currency"] == "USD":
            expected.append(f"${pr['amount']}")
        else:
            expected.append(f"{pr['amount']:,}".replace(",", " "))
    assert rendered == expected, f"page shows {rendered}, contract says {expected}"


def test_the_quotas_and_seats_on_the_page_match_the_contract():
    flat = PAGE.replace("&nbsp;", " ")
    for key in ("premium", "premium_pro"):
        e = _plan(key)["entitlements"]
        q = f"{e['api_requests_month']:,}".replace(",", " ")
        assert q in flat, f"{key}: quota {q} is not on the page"
    pro = _plan("premium_pro")["entitlements"]
    assert re.search(rf"\b(five|{pro['seats']})\s+seats", flat, re.I), \
        "the PRO seat count is not stated on the page"


def test_the_launch_offer_states_its_term_and_what_it_grants():
    launch = _plan("launch_annual")
    assert launch["grants"] == "premium_pro"
    assert launch["entitlements"] == _plan("premium_pro")["entitlements"], (
        "launch_annual claims to grant Premium PRO but lists different entitlements"
    )
    flat = PAGE.replace("&nbsp;", " ").lower()
    assert "twelve months" in flat or f"{launch['term_months']} months" in flat
    assert "premium pro" in flat, "the launch offer does not name what it grants"


def test_the_vague_claims_that_preceded_this_contract_stay_out():
    """Each of these was on the page and each overstated what is sold."""
    for bad in ("Everything on this page",
                "Full functionality",
                "every seat that comes with it",
                "scan budget"):
        assert bad.lower() not in PAGE.lower(), f"the page still says {bad!r}"


def test_monthly_and_prepaid_are_not_described_as_the_same_thing():
    flat = PAGE.lower()
    assert "prepaid" in flat, "the annual offer is not described as prepaid"
    assert not re.search(r"paid plans are a service</b>,\s*billed monthly", flat), \
        "the terms still call every paid plan monthly while one is annual"


def test_the_page_says_provisioning_is_manual():
    assert COMMERCIAL["provisioning"]["automated"] is False
    flat = PAGE.lower()
    assert "provisioning is manual" in flat, \
        "the contract says provisioning is manual and the page does not"
    assert "order id" in flat, "the page does not mention an order id"
    assert PAYMENT["contact"] in PAGE, "the contact address is not the one in payment.json"


def test_cadence_is_not_promised_as_a_number():
    """PRO offers a custom cadence; a specific interval would be a promise."""
    flat = PAGE.lower()
    assert "agreed at provisioning" in flat or "agreed during provisioning" in flat, \
        "the page does not say the cadence is agreed rather than fixed"
