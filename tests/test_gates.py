#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
"""The gates are code, so they are tested like code.

They used to be a hundred and thirty lines of Python inside YAML strings, where
nothing could import them, lint them, or run them without a GitHub runner. Two
real defects passed through that layer and were found in production:

* a duplicate `run:` key that stopped the workflow parsing, so a whole release
  produced no result of any kind while appearing to have failed its proofs;
* a gate that looked for a disclosure and never for the contradiction, which
  passed on a README whose opening sentence said the opposite of its body.

Both were invisible locally because there was nothing to run. Each gate now
answers `check() -> list[str]`, empty meaning clean, and each is exercised here
against the real tree and against a mutated copy of it — because a gate that has
never failed is a gate nobody has tested.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import shutil

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATES = ROOT / "scripts" / "gates"

GATE_NAMES = [
    "check_funding",
    "check_frozen_counts",
    "check_anchor_disclosure",
    "check_version_consistency",
]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, GATES / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def tree(tmp_path):
    """A working copy, so a mutation test cannot damage the real repository."""
    dst = tmp_path / "repo"
    dst.mkdir()
    for rel in ("README.md", "CITATION.cff", "CHANGELOG.md", "VERSION",
                "index.html", "stats.html", "support.html"):
        shutil.copy2(ROOT / rel, dst / rel)
    (dst / "data").mkdir()
    for rel in ("payment.json", "ecosystem-registry.json", "radar.json", "curated.json"):
        shutil.copy2(ROOT / "data" / rel, dst / "data" / rel)
    (dst / "docs").mkdir()
    shutil.copy2(ROOT / "docs" / "METHODOLOGY.md", dst / "docs" / "METHODOLOGY.md")
    (dst / "assets").mkdir()
    shutil.copy2(ROOT / "assets" / "app.js", dst / "assets" / "app.js")
    (dst / ".github").mkdir()
    shutil.copy2(ROOT / ".github" / "FUNDING.yml", dst / ".github" / "FUNDING.yml")
    return dst


# --------------------------------------------------------------------------
# every gate is importable, callable, and clean on the real tree
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", GATE_NAMES)
def test_the_gate_is_a_module_with_a_check_function(name):
    mod = load(name)
    assert callable(getattr(mod, "check", None)), f"{name} has no check()"
    assert (mod.__doc__ or "").strip(), f"{name} has no docstring saying what it enforces"


@pytest.mark.parametrize("name", GATE_NAMES)
def test_the_gate_passes_on_the_committed_tree(name):
    problems = load(name).check(ROOT)
    assert problems == [], f"{name} fails on the repository as committed: {problems}"


# --------------------------------------------------------------------------
# and fails when the thing it guards is broken
# --------------------------------------------------------------------------

def test_funding_notices_a_foreign_address(tree):
    p = tree / "support.html"
    p.write_text(p.read_text() + "\n<!-- DBadAhqVNWf7dyEznukxCufNS5rjuP5MTp -->\n")
    problems = load("check_funding").check(tree)
    assert any("foreign" in x for x in problems), problems


def test_funding_notices_the_two_files_drifting_apart(tree):
    import json
    p = tree / "data" / "ecosystem-registry.json"
    d = json.loads(p.read_text())
    d["funding"]["address"] = "DBadAhqVNWf7dyEznukxCufNS5rjuP5MTp"
    p.write_text(json.dumps(d))
    problems = load("check_funding").check(tree)
    assert any("drifted" in x for x in problems), problems


def test_funding_notices_a_checksum_failure(tree):
    import json
    addr = json.loads((tree / "data" / "payment.json").read_text())["address"]
    broken = addr[:-1] + ("A" if addr[-1] != "A" else "B")
    for rel in ("data/payment.json", "data/ecosystem-registry.json",
                "support.html", "assets/app.js", ".github/FUNDING.yml"):
        p = tree / rel
        p.write_text(p.read_text().replace(addr, broken))
    problems = load("check_funding").check(tree)
    assert any("Base58Check" in x for x in problems), problems


def test_frozen_counts_notices_a_static_project_badge(tree):
    p = tree / "README.md"
    p.write_text(p.read_text() +
                 "\n[![x](https://img.shields.io/badge/tracked-120%2B%20BCI%20projects-blue)](y)\n")
    problems = load("check_frozen_counts").check(tree)
    assert any("120" in x for x in problems), problems


def test_frozen_counts_notices_a_near_miss_number_in_prose(tree):
    p = tree / "README.md"
    p.write_text(p.read_text() + "\nThe page lists 31 near misses today.\n")
    problems = load("check_frozen_counts").check(tree)
    assert any("near misses" in x for x in problems), problems


def test_anchor_disclosure_notices_a_silent_readme(tree):
    p = tree / "README.md"
    p.write_text(p.read_text().replace("ecosystem anchor", "ECOSYSTEM PLACEHOLDER"))
    problems = load("check_anchor_disclosure").check(tree)
    assert any("does not mention" in x for x in problems), problems


def test_anchor_disclosure_notices_the_universal_claim_returning(tree):
    p = tree / "README.md"
    p.write_text(p.read_text().replace("Almost every project here cleared",
                                       "Every project here cleared"))
    problems = load("check_anchor_disclosure").check(tree)
    assert any("universal gate" in x for x in problems), problems


def test_anchor_disclosure_does_not_flag_the_qualified_sentence(tree):
    """The regression that made this gate reject its own fix."""
    text = (tree / "README.md").read_text()
    assert "Almost every project here cleared" in text, "fixture no longer covers this"
    assert load("check_anchor_disclosure").check(tree) == []


def test_version_consistency_notices_a_bumped_root(tree):
    (tree / "VERSION").write_text("99.9.9\n")
    problems = load("check_version_consistency").check(tree)
    assert len(problems) >= 4, f"a lone VERSION bump produced only {problems}"


def test_version_consistency_notices_a_stale_citation(tree):
    """Targeted at the  line, not .

    The first draft of this test replaced the first occurrence of "version: "
    and hit  instead, so the mutation never touched what the gate
    reads and the test reported a gate failure that was its own.
    """
    p = tree / "CITATION.cff"
    s = re.sub(r"^version: .+$", "version: 99.9.9", p.read_text(), count=1, flags=re.M)
    p.write_text(s)
    problems = load("check_version_consistency").check(tree)
    assert any("CITATION" in x for x in problems), problems
