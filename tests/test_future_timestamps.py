#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""A timestamp in the future is not freshness. It is the quietest fault here.

Staleness is measured as `now - generated_at`, in the validator's reasoning and
in the monitor's arithmetic alike. A payload dated next year is therefore
permanently fresh: the comparison can never exceed a threshold, and every
downstream check that depends on it stops being able to report anything.

That is not hypothetical for this repository. The site served a fifteen-day-old
build while the monitor reported success every three hours, because the monitor
returned zero on the unhealthy path. This is the same outcome reached by a
different route — a skewed clock upstream — and it needs its own guard, because
the fix for the first one does not cover it.

Both layers are pinned here: the validator refuses to accept such a payload, and
the monitor reports it as a fault rather than passing the test it has made
unfailable.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _run_validator(payload: dict) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        path = f.name
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_payload.py"), path],
            capture_output=True, text=True, cwd=ROOT,
        )
        return r.returncode, r.stdout + r.stderr
    finally:
        pathlib.Path(path).unlink(missing_ok=True)


def _payload() -> dict:
    return json.loads((ROOT / "data" / "radar.json").read_text(encoding="utf-8"))


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_the_live_payload_still_validates():
    code, out = _run_validator(_payload())
    assert code == 0, out


def test_a_payload_from_2099_is_refused():
    p = _payload()
    p["generated_at"] = "2099-01-01T00:00:00+00:00"
    code, out = _run_validator(p)
    assert code != 0, "a payload dated 2099 was accepted"
    assert "future" in out.lower(), out


def test_a_payload_a_few_hours_ahead_is_refused():
    """Not only absurd dates. Eight hours is a plausible timezone bug."""
    p = _payload()
    p["generated_at"] = _iso(datetime.now(timezone.utc) + timedelta(hours=8))
    code, out = _run_validator(p)
    assert code != 0, "a payload eight hours ahead was accepted"


def test_a_payload_seconds_ahead_is_allowed():
    """A payload minted during a run is legitimately a little ahead of us."""
    p = _payload()
    p["generated_at"] = _iso(datetime.now(timezone.utc) + timedelta(seconds=30))
    code, out = _run_validator(p)
    assert code == 0, f"clock skew of thirty seconds was refused:\n{out}"


def test_an_unparsable_timestamp_is_refused():
    p = _payload()
    p["generated_at"] = "last Tuesday"
    code, out = _run_validator(p)
    assert code != 0 and "ISO-8601" in out, out


def _health():
    spec = importlib.util.spec_from_file_location(
        "hc", ROOT / "scripts" / "health_check.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _stub(hc, published: dict):
    hc.fetch_json = lambda url: published.get(url.replace(hc.PAGES, ""))


def test_the_monitor_calls_a_future_scan_a_fault_not_freshness():
    hc = _health()
    now = datetime.now(timezone.utc)
    fresh = _iso(now - timedelta(hours=1))
    _stub(hc, {
        "data/status.json": {"generated_at": "2099-01-01T00:00:00Z"},
        "data/build.json": {"build": "a", "deployed_at": fresh},
        "data/last_run.json": {"ok": True},
    })
    problems = hc.diagnose()
    assert any("FUTURE" in p for p in problems), problems
    assert not any("STALE" in p for p in problems), \
        "a future timestamp must not also be reported as stale"


def test_the_monitor_guards_the_deploy_clock_too():
    """Both clocks fail independently, so both need the guard."""
    hc = _health()
    now = datetime.now(timezone.utc)
    fresh = _iso(now - timedelta(hours=1))
    _stub(hc, {
        "data/status.json": {"generated_at": fresh},
        "data/build.json": {"build": "a", "deployed_at": _iso(now + timedelta(hours=5))},
        "data/last_run.json": {"ok": True},
    })
    problems = hc.diagnose()
    assert any("FUTURE" in p and "deployed_at" in p for p in problems), problems


def test_a_healthy_pair_is_still_silent():
    hc = _health()
    fresh = _iso(datetime.now(timezone.utc) - timedelta(hours=1))
    _stub(hc, {
        "data/status.json": {"generated_at": fresh},
        "data/build.json": {"build": "a", "deployed_at": fresh},
        "data/last_run.json": {"ok": True},
    })
    assert hc.diagnose() == [], "a healthy site reported a problem"
