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

Version 3 (16.10.0) is paid by bank transfer against an invoice. The Dogecoin
launch year is withdrawn from sale: a fund or a lab cannot route a purchase
through a single public crypto address, so PRO carries no crypto at all and
Dogecoin stays where it belongs, on the support page, as a voluntary tip. A
one-off Field Brief is sold, the written brief is defined, and the sample page
that shows it is linked from the offer.
"""
from __future__ import annotations

import json
import pathlib
import re
import urllib.parse

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = (ROOT / "pro.html").read_text(encoding="utf-8")
SUPPORT = (ROOT / "support.html").read_text(encoding="utf-8")
SAMPLE = (ROOT / "sample.html").read_text(encoding="utf-8")
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

def test_the_contract_is_version_three():
    assert C["schema_version"] == 3


def test_the_contract_sells_nothing_that_does_not_exist():
    """The claims version 1 made, and that CI enforced, stay out."""
    flat = json.dumps(C).lower()
    for gone in ("api_requests", "requests_month", "custom_scan_cadence"):
        assert gone not in flat, f"commercial.json sells {gone!r} again; there is no such system"
    assert C["provisioning"]["automated"] is False
    assert C["delivery"]["model"] == "private_github_repository"


def test_the_dogecoin_launch_year_is_no_longer_sold():
    assert "launch_annual" not in C["plans"]
    assert all(p["price"]["currency"] in C["payment"]["currencies"] for p in C["plans"].values())


def test_payment_is_a_bank_transfer_against_an_invoice():
    assert C["payment"]["rail"] == "bank_transfer"
    assert C["payment"]["crypto_accepted"] is False
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", PAGE)).lower()
    assert "bank transfer" in flat and "invoice" in flat
    assert C["payment"]["statement"].lower() in flat, "the page does not state the payment rail as the contract does"


# ---------------------------------------------------------- page == contract

def test_every_price_on_the_page_is_the_contract_price():
    for key in ("premium", "premium_pro", "field_brief"):
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


def test_the_offer_carries_no_crypto_payment():
    assert "dogecoin:" not in PAGE, "pro.html offers a crypto payment; PRO is invoiced"
    assert PAY["address"] not in PAGE, "pro.html carries the Dogecoin address; it belongs on support.html"


def test_every_invoice_request_reaches_the_canonical_inbox():
    links = re.findall(r'href="(mailto:[^"]+)"', PAGE)
    asks = [l for l in links if "invoice" in urllib.parse.unquote(l).lower()]
    assert len(asks) >= 3, "each plan needs its own invoice request"
    assert all(l.startswith("mailto:connect@axonos.org") for l in asks)


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

def test_only_the_canonical_address_appears_and_only_on_support():
    for name, text in (("pro.html", PAGE), ("support.html", SUPPORT), ("sample.html", SAMPLE)):
        found = set(re.findall(r"\bD[1-9A-HJ-NP-Za-km-z]{25,40}\b", text))
        assert found <= {PAY["address"]}, f"{name} carries a foreign address: {found - {PAY['address']}}"
    assert PAY["address"] in SUPPORT, "support.html does not carry the canonical address"


def test_support_no_longer_sells_and_points_at_the_offer():
    assert 'data-plan=' not in SUPPORT and "plan-grid" not in SUPPORT, \
        "plans are back on the support page; they live on pro.html"
    assert 'href="./pro.html"' in SUPPORT


def test_the_warnings_that_protect_a_payer_are_present():
    """Crypto moved to the support page in 16.10.0, and its warnings with it."""
    low = SUPPORT.lower()
    assert "cannot be reversed" in low
    assert "seed phrase" in low and "private key" in low


# --------------------------------------------------------------- guarantees

def _items(side: str) -> list[str]:
    m = re.search(rf'<div data-guarantee="{side}">(.*?)</div>', PAGE, re.S)
    assert m, f"pro.html has no {side!r} guarantee column"
    return [re.sub(r"\s+", " ", x).strip() for x in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]


def test_the_page_promises_exactly_what_the_contract_promises():
    """Word for word. A promise that differs between the page and the contract
    is two promises, and the customer reads the page."""
    assert _items("yes") == C["guarantees"]["we_guarantee"]


def test_the_page_names_exactly_the_limits_the_contract_names():
    shown = [x.replace("&#x27;", "'").replace("’", "'") for x in _items("no")]
    assert shown == C["guarantees"]["we_do_not_guarantee"]


def test_the_terms_are_rendered_as_the_contract_states_them():
    m = re.search(r'<dl class="plain" data-terms>(.*?)</dl>', PAGE, re.S)
    assert m, "pro.html renders no terms block"
    shown = dict((k.strip(), v.strip()) for k, v in re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", m.group(1), re.S))
    shown = {k.replace("&#x27;", "'"): v.replace("&#x27;", "'") for k, v in shown.items()}
    assert shown == C["terms"]


def test_the_brief_is_defined_and_its_sample_is_shipped_and_linked():
    b = C["brief"]
    assert b["pages"] and b["sections"] and b["sources"]
    assert (ROOT / b["sample"]).exists(), "the contract names a sample page that is not there"
    assert f'href="./{b["sample"]}"' in PAGE, "the offer does not link to its sample"
    assert "3 October 2026" in SAMPLE, "the sample does not say which day of data it shows"


def test_no_promise_the_record_cannot_support():
    """'Usually sooner' was suggested for the first-digest window. There have
    been no deliveries yet, so there is nothing for 'usually' to describe."""
    low = PAGE.lower()
    for claim in ("usually sooner", "typically within", "most customers", "on average"):
        assert claim not in low, f"the page states a track record that does not exist: {claim!r}"


# ---------------------------------------------------------- phantom services

PUBLIC_DOCS = ("README.md", "docs/API.md", "docs/OPEN_CORE_BOUNDARY.md", "pro.html", "support.html", "sample.html")


@pytest.mark.parametrize("doc", PUBLIC_DOCS)
def test_no_public_page_offers_a_service_that_does_not_exist(doc):
    """The contract stopped selling an API quota in 16.7.0. The README and the
    API reference went on offering 'licensed feeds, SLAs and custom slices' for
    two more releases. A service offered anywhere is offered."""
    text = re.sub(r"<[^>]+>", " ", (ROOT / doc).read_text(encoding="utf-8"))
    for phantom in (r"\bSLAs?\b", r"licen[cs]ed feeds?", r"requests?\s+(a|per)\s+month",
                    r"custom (scan )?cadence", r"intelligence feed"):
        hit = re.search(phantom, text, re.I)
        assert not hit, f"{doc} offers {hit.group(0)!r}, which nothing delivers"


def test_one_contact_address_for_commercial_questions():
    for doc in ("README.md", "pro.html", "support.html", "sample.html"):
        assert "support@axonos.org" not in (ROOT / doc).read_text(encoding="utf-8"), \
            f"{doc} names support@axonos.org; every other surface uses connect@axonos.org"
