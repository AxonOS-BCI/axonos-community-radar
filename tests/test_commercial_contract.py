#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""What is sold, and only what can be delivered.

Version 1 of `data/commercial.json` sold "10 000" and "200 000 API requests a
month" and a "custom scan cadence". There was no authenticated API and no second
scan schedule. The contract test checked that the page repeated those figures
faithfully — so CI enforced, on every push, that the site kept promising
software nobody had written.

Version 2 sells what one existing mechanism can deliver: a private GitHub
repository that the engine writes into. This test binds `pro.html` to that
contract through data attributes rather than prose, and refuses the claims that
version 1 made.
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = (ROOT / "pro.html").read_text(encoding="utf-8")
SUPPORT = (ROOT / "support.html").read_text(encoding="utf-8")
C = json.loads((ROOT / "data" / "commercial.json").read_text(encoding="utf-8"))
PAY = json.loads((ROOT / "data" / "payment.json").read_text(encoding="utf-8"))


def plan(key):
    return C["plans"][key]


def ents(key):
    p = plan(key)
    return p["entitlements"] if "entitlements" in p else ents(p["grants"])


def block(key) -> str:
    """The <article> the page renders for one plan."""
    m = re.search(rf'<article[^>]*data-plan="{key}"[^>]*>(.*?)</article>', PAGE, re.S)
    assert m, f"pro.html renders no card for {key}"
    return m.group(1)


# ------------------------------------------------------------------ contract

def test_the_contract_is_version_two():
    assert C["schema_version"] == 2


def test_the_contract_sells_nothing_that_does_not_exist():
    """The claims version 1 made, and that CI enforced, stay out."""
    flat = json.dumps(C).lower()
    for gone in ("api_requests", "requests_month", "custom_scan_cadence"):
        assert gone not in flat, f"commercial.json sells {gone!r} again; there is no such system"
    assert C["provisioning"]["automated"] is False
    assert C["delivery"]["model"] == "private_github_repository"


def test_a_granting_plan_carries_no_entitlements_of_its_own():
    assert "entitlements" not in plan("launch_annual")
    assert plan("launch_annual")["grants"] == "premium_pro"


# ---------------------------------------------------------- page == contract

def test_every_price_on_the_page_is_the_contract_price():
    for key in ("premium", "premium_pro", "launch_annual"):
        m = re.search(r'data-price="(\d+)"', block(key))
        assert m, f"{key} card has no data-price"
        assert int(m.group(1)) == plan(key)["price"]["amount"], (
            f"{key}: page {m.group(1)}, contract {plan(key)['price']['amount']}")


def test_every_rendered_entitlement_matches_the_contract():
    for key in ("premium", "premium_pro"):
        e = ents(key)
        for field, shown in re.findall(r'data-ent="(\w+)">([^<]+)<', block(key)):
            want = e[field]
            assert str(want).lower() == shown.strip().lower(), (
                f"{key}.{field}: page says {shown!r}, contract says {want!r}")


def test_the_premium_card_does_not_promise_pro_features():
    for field in ("field_watches", "written_brief"):
        assert f'data-ent="{field}"' not in block("premium"), (
            f"the Premium card shows {field}, which Premium does not include")


def test_the_page_does_not_sell_an_api_quota_or_a_faster_scan():
    flat = re.sub(r"<[^>]+>", " ", PAGE).lower()
    assert not re.search(r"\d[\d\s,]*\s*(api\s+)?requests\s+(a|per)\s+month", flat), \
        "the page sells an API request quota; there is no API to meter"
    assert "custom cadence" not in flat and "own cadence" not in flat, \
        "the page promises a scan schedule other than the public one"
    assert "every three hours" in flat


def test_the_launch_uri_pays_the_canonical_address_the_exact_amount():
    uris = re.findall(r'href="(dogecoin:[^"]+)"', PAGE)
    assert uris, "no one-click payment on the page"
    for raw in uris:
        u = urllib.parse.urlparse(raw.replace("&amp;", "&"))
        assert u.path == PAY["address"], f"{raw} pays another address"
        amt = urllib.parse.parse_qs(u.query).get("amount", [None])[0]
        if amt is not None:
            assert float(amt) == float(plan("launch_annual")["price"]["amount"])


def test_the_page_states_the_first_digest_window_from_the_contract():
    days = C["provisioning"]["first_digest_within_days"]
    words = {7: "seven"}.get(days, str(days))
    assert f"within {words} days" in PAGE, "the page and the contract disagree on the first-digest window"


def test_the_order_id_flow_is_on_the_page():
    fmt = C["provisioning"]["order_id_format"]
    example = re.search(r"AXR-\d{4}-\d{6}", PAGE)
    assert example, "the page shows no order id"
    assert re.fullmatch(fmt.replace("YYYY", r"\d{4}").replace("NNNNNN", r"\d{6}"), example.group(0))


def test_every_never_statement_is_rendered():
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", PAGE)).lower()
    for claim in ("never buys a place on the public map",
                  "never changes a score",
                  "taken away to make a paid version"):
        assert claim in flat, f"the page no longer says: {claim!r}"


# ------------------------------------------------------------ the two pages

def test_only_the_canonical_address_appears_on_either_page():
    for name, text in (("pro.html", PAGE), ("support.html", SUPPORT)):
        found = set(re.findall(r"\bD[1-9A-HJ-NP-Za-km-z]{25,40}\b", text))
        assert found <= {PAY["address"]}, f"{name} carries a foreign address: {found - {PAY['address']}}"
        assert PAY["address"] in text, f"{name} does not carry the canonical address"


def test_support_no_longer_sells_and_points_at_the_offer():
    assert 'data-plan=' not in SUPPORT and "plan-grid" not in SUPPORT, \
        "plans are back on the support page; they live on pro.html"
    assert 'href="./pro.html"' in SUPPORT


def test_the_warnings_that_protect_a_payer_are_present():
    low = PAGE.lower()
    assert "cannot be reversed" in low
    assert "seed phrase" in low and "private key" in low
