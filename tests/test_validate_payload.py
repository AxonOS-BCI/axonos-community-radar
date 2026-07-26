# Tests for scripts/validate_payload.py — the executable half of the public
# data contract (docs/DATA_MODEL.md). This file didn't exist before v12.0.6;
# every other script under scripts/ has one. Focused on brs/relevance_tier/
# relevance_ledger (added in v12.0.6 — previously unvalidated anywhere in the
# pipeline) plus a few pre-existing invariants that had no dedicated coverage.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_payload  # noqa: E402


def _project(**kw):
    base = {
        "full_name": "someone/some-repo",
        "html_url": "https://github.com/someone/some-repo",
        "category": "Decoding & ML",
        "evidence_tier": "L2_NEURAL_SIGNAL",
        "inclusion_reason": "matched a real signal",
    }
    base.update(kw)
    return base


def _payload(*projects):
    return {"version": 5, "generated_at": "2026-07-24T00:00:00+00:00", "projects": list(projects)}


# --- brs -----------------------------------------------------------------

def test_brs_in_range_is_valid():
    errs = validate_payload.validate_payload(_payload(_project(brs=55)))
    assert errs == []


def test_brs_boundary_values_are_valid():
    errs = validate_payload.validate_payload(_payload(
        _project(brs=0),
        _project(full_name="x/y", html_url="https://github.com/x/y", brs=100),
    ))
    assert errs == []


def test_brs_above_100_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(brs=150)))
    assert any("brs" in e for e in errs)


def test_brs_negative_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(brs=-1)))
    assert any("brs" in e for e in errs)


def test_brs_wrong_type_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(brs="high")))
    assert any("brs" in e for e in errs)


def test_brs_bool_is_rejected():
    # bool is a subclass of int in Python -- isinstance(True, int) is True,
    # so this needs its own explicit guard, which is why it gets its own test.
    errs = validate_payload.validate_payload(_payload(_project(brs=True)))
    assert any("brs" in e for e in errs)


def test_brs_absent_is_fine():
    # Ecosystem-manifest entries never go through BRS discovery -- absence
    # is not an error. (Verified against live data before choosing this:
    # 4 of 120 current projects have no brs.)
    errs = validate_payload.validate_payload(_payload(_project()))
    assert errs == []


# --- relevance_tier --------------------------------------------------------

def test_relevance_tier_real_values_are_valid():
    for tier in ("L4_EXPLICIT_BCI", "L3_STANDARD_OR_HARDWARE", "L3_MODALITY_OR_PARADIGM", "L2_NEURO_TERM"):
        errs = validate_payload.validate_payload(_payload(_project(relevance_tier=tier)))
        assert errs == [], f"{tier} should be valid, got {errs}"


def test_relevance_tier_bad_shape_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(relevance_tier="super_relevant")))
    assert any("relevance_tier" in e for e in errs)


def test_relevance_tier_out_of_range_l_number_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(relevance_tier="L9_EXPLICIT_BCI")))
    assert any("relevance_tier" in e for e in errs)


def test_relevance_tier_lowercase_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(relevance_tier="l4_explicit_bci")))
    assert any("relevance_tier" in e for e in errs)


# --- relevance_ledger -------------------------------------------------------

def test_relevance_ledger_well_formed_is_valid():
    ledger = [{"points": 55, "kind": "core", "reason": "Explicit BCI topic (bci)"}]
    errs = validate_payload.validate_payload(_payload(_project(relevance_ledger=ledger)))
    assert errs == []


def test_relevance_ledger_not_a_list_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(relevance_ledger="not a list")))
    assert any("relevance_ledger" in e for e in errs)


def test_relevance_ledger_entry_missing_points_is_rejected():
    ledger = [{"kind": "core", "reason": "x"}]
    errs = validate_payload.validate_payload(_payload(_project(relevance_ledger=ledger)))
    assert any("points" in e for e in errs)


def test_relevance_ledger_entry_missing_kind_is_rejected():
    ledger = [{"points": 10, "reason": "x"}]
    errs = validate_payload.validate_payload(_payload(_project(relevance_ledger=ledger)))
    assert any("kind" in e for e in errs)


def test_relevance_ledger_entry_missing_reason_is_rejected():
    ledger = [{"points": 10, "kind": "core"}]
    errs = validate_payload.validate_payload(_payload(_project(relevance_ledger=ledger)))
    assert any("reason" in e for e in errs)


def test_relevance_ledger_entry_not_an_object_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(relevance_ledger=["not an object"])))
    assert any("relevance_ledger[0]" in e for e in errs)


# --- pre-existing invariants, previously exercised only by manual runs -----

def test_html_url_must_be_github():
    errs = validate_payload.validate_payload(_payload(_project(html_url="https://evil.example.com/x")))
    assert any("html_url" in e or "github" in e.lower() for e in errs)


def test_html_url_lookalike_host_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(html_url="https://github.com.evil.com/x/y")))
    assert any("html_url" in e or "github" in e.lower() for e in errs)


def test_description_over_240_chars_is_rejected():
    errs = validate_payload.validate_payload(_payload(_project(description="x" * 241)))
    assert any("description" in e for e in errs)


def test_description_at_240_chars_is_valid():
    errs = validate_payload.validate_payload(_payload(_project(description="x" * 240)))
    assert errs == []


def test_real_current_data_is_fully_clean():
    # The actual live payload should always validate with zero errors --
    # if this fails, either real data regressed or a rule above is wrong.
    import json
    path = Path(__file__).resolve().parents[1] / "data" / "radar.json"
    payload = json.loads(path.read_text())
    errs = validate_payload.validate_payload(payload)
    assert errs == []
