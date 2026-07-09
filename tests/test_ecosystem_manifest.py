"""Tests for scripts/build_ecosystem_manifest.py - the organism's pulse.

Covers: manifest structure, live-signal joining, degrade-safe behaviour with a
missing radar.json, the shields endpoint contract, and the single-source rule
for the DOGE address (registry == app.js == support.html == FUNDING.yml).
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import build_ecosystem_manifest as bem  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _registry():
    with open(os.path.join(ROOT, "data", "ecosystem-registry.json"), encoding="utf-8") as f:
        return json.load(f)


def _radar():
    with open(os.path.join(ROOT, "data", "radar.json"), encoding="utf-8") as f:
        return json.load(f)


def test_manifest_structure_and_roles():
    m = bem.build_manifest(_registry(), _radar())
    assert m["schema"] == "axonos-ecosystem-v1"
    names = {r["full_name"] for r in m["repos"]}
    assert "AxonOS-BCI/axonos-community-radar" in names
    assert "AxonOS-BCI/neural-boundary-game" in names
    assert "AxonOS-org/axonos-kernel" in names
    for r in m["repos"]:
        assert r["url"] == f"https://github.com/{r['full_name']}"
        assert r["role"] and r["what"], f"{r['full_name']} missing role/what"


def test_live_signals_join():
    m = bem.build_manifest(_registry(), _radar())
    hub = next(r for r in m["repos"] if r["full_name"] == "AxonOS-BCI/axonos-community-radar")
    # The radar tracks itself as an ecosystem anchor, so live signals must join.
    assert "live" in hub and 0 <= hub["live"]["health"] <= 100


def test_degrade_safe_without_radar():
    m = bem.build_manifest(_registry(), None)
    assert m["repos"] and "radar" not in m
    b = bem.build_badge(None)
    assert b["schemaVersion"] == 1 and b["message"] == "live radar"


def test_badge_contract_with_radar():
    b = bem.build_badge(_radar())
    assert b["schemaVersion"] == 1
    assert re.match(r"^\d+ projects · health \d+$", b["message"])
    assert b["label"] == "AxonOS ecosystem"


def test_funding_block_is_donation_only():
    f = _registry()["funding"]
    assert f["kind"] == "voluntary-donation"
    assert f["address"].startswith("D") and 26 <= len(f["address"]) <= 40
    assert f["uri"] == f"dogecoin:{f['address']}"
    joined = " ".join(f["terms"]).lower()
    assert "not purchases" in joined and "irreversible" in joined


def test_doge_address_single_source():
    """One address across the whole repo: registry, app.js, support page, FUNDING."""
    addr = _registry()["funding"]["address"]
    for rel in ("assets/app.js", "support.html", ".github/FUNDING.yml"):
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            assert addr in fh.read(), f"{rel} does not carry the canonical DOGE address"


def test_cli_end_to_end(tmp_path):
    out = tmp_path / "site-data"
    rc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "build_ecosystem_manifest.py"),
         "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, check=False)
    assert rc.returncode == 0, rc.stderr
    m = json.loads((out / "ecosystem.json").read_text())
    b = json.loads((out / "badge-ecosystem.json").read_text())
    assert m["funding"]["currency"] == "DOGE" and b["schemaVersion"] == 1
