#!/usr/bin/env python3
"""Tests for the v7 domain intelligence (scripts/domain.py): facet extraction,
the modality × signal-chain coverage matrix, and the standards-interoperability
graph. Deterministic and offline."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import domain as D  # noqa: E402


def _repo(name, desc="", topics=None):
    return {"full_name": name, "description": desc, "topics": topics or []}


# ── facet extraction ─────────────────────────────────────────────────────────

def test_facets_modality_and_standard():
    f = D.facets(_repo("mne/mne", "EEG and MEG analysis with MNE", ["eeg", "meg", "mne"]))
    assert "EEG" in f["modality"] and "MEG" in f["modality"]
    assert "FIF/MNE" in f["standards"]


def test_facets_signal_chain_stages():
    f = D.facets(_repo("x/pipe", "acquisition, filtering and decoding of EEG", ["eeg"]))
    assert "Acquisition" in f["signal_chain"]
    assert "Preprocessing" in f["signal_chain"]
    assert "Decoding" in f["signal_chain"]


def test_facets_paradigm():
    f = D.facets(_repo("x/p300", "A P300 speller", ["p300", "ssvep"]))
    assert "P300" in f["paradigm"]
    assert "SSVEP" in f["paradigm"]


def test_facets_are_sorted_lists():
    f = D.facets(_repo("x/y", "EEG ECoG EMG", ["eeg", "ecog", "emg"]))
    for key in ("modality", "paradigm", "signal_chain", "standards"):
        assert isinstance(f[key], list)
    assert f["modality"] == sorted(f["modality"])


def test_facets_empty_for_nonspecific_repo():
    f = D.facets(_repo("x/proto", "A consent protocol specification", ["protocol"]))
    assert f["modality"] == [] and f["paradigm"] == [] and f["standards"] == []


# ── coverage matrix ──────────────────────────────────────────────────────────

def _with_facets(repos):
    for r in repos:
        r["facets"] = D.facets(r)
    return repos


def test_coverage_matrix_shape_and_counts():
    repos = _with_facets([
        _repo("a/eeg1", "EEG acquisition and decoding", ["eeg"]),
        _repo("b/eeg2", "EEG decoding classifier", ["eeg"]),
        _repo("c/emg", "EMG acquisition", ["emg"]),
    ])
    cov = D.coverage_matrix(repos)
    assert cov["stages"] == D.SIGNAL_CHAIN
    assert cov["n_projects"] == 3
    # each grid row has one cell per stage
    for row in cov["grid"]:
        assert len(row["cells"]) == len(D.SIGNAL_CHAIN)
    # EEG row should have a positive Decoding count (two EEG decoders)
    eeg_row = next(r for r in cov["grid"] if r["modality"] == "EEG")
    dec_idx = D.SIGNAL_CHAIN.index("Decoding")
    assert eeg_row["cells"][dec_idx] >= 2


def test_coverage_matrix_reveals_desert():
    # a modality with zero coverage should simply not appear as a populated row
    repos = _with_facets([_repo("a/eeg", "EEG decoding", ["eeg"])])
    cov = D.coverage_matrix(repos)
    assert "fNIRS" not in cov["modalities"]


def test_coverage_matrix_empty_input():
    cov = D.coverage_matrix([])
    assert cov["n_projects"] == 0
    assert cov["grid"] == []


# ── standards graph ──────────────────────────────────────────────────────────

def test_standards_graph_hubs_and_edges():
    repos = _with_facets([
        _repo("a/mne1", "MNE FIF", ["mne", "fif"]),
        _repo("b/mne2", "Another MNE tool", ["mne"]),
        _repo("c/lsl", "LSL streaming", ["lsl"]),
    ])
    g = D.standards_graph(repos)
    fif = next(s for s in g["standards"] if s["standard"] == "FIF/MNE")
    assert fif["count"] == 2
    # a/mne1 and b/mne2 share FIF/MNE → exactly one interoperability edge
    assert g["interop_edges"] == 1
    assert g["n_repos_with_standards"] == 3


def test_standards_graph_sorted_by_count_desc():
    repos = _with_facets([
        _repo("a/mne1", "MNE", ["mne"]),
        _repo("b/mne2", "MNE", ["mne"]),
        _repo("c/edf", "EDF", ["edf"]),
    ])
    g = D.standards_graph(repos)
    counts = [s["count"] for s in g["standards"]]
    assert counts == sorted(counts, reverse=True)


def test_standards_graph_no_standards():
    repos = _with_facets([_repo("a/x", "no standards here", ["protocol"])])
    g = D.standards_graph(repos)
    assert g["n_standards"] == 0
    assert g["interop_edges"] == 0


def test_graph_and_matrix_deterministic():
    repos = _with_facets([_repo("a/eeg", "EEG decoding with MNE", ["eeg", "mne"])])
    assert D.coverage_matrix(list(repos)) == D.coverage_matrix(list(repos))
    assert D.standards_graph(list(repos)) == D.standards_graph(list(repos))
