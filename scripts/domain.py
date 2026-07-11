#!/usr/bin/env python3
"""
AxonOS Radar — Domain Intelligence (v7).

A list of repositories, however well filtered, is something you could assemble
by hand on GitHub. The value this module adds is the thing you *cannot* get by
browsing: it reads the BCI ecosystem as a **connected system**.

For every kept repository it extracts four structured, deterministic facets:

  * modality        — which biosignals it works with (EEG/ECoG/EMG/fNIRS/MEG/…)
  * paradigm        — which BCI paradigms (P300/SSVEP/motor-imagery/neurofeedback)
  * signal_chain    — which stages of the acquisition→application pipeline it covers
  * standards       — which field standards it speaks (LSL/BIDS/EDF/FIF/OpenBCI/…)

From those it builds two views nobody else publishes:

  * The Standards Interoperability Graph — the connective tissue of the field.
    Which repos emit/consume LSL (the real-time streaming lingua franca), which
    speak EDF (file interchange), which speak BIDS (dataset layout). Two repos
    that share a standard can pipe into each other; that is an interoperability
    edge, computed from evidence rather than asserted.

  * The Signal-Chain Coverage Matrix — a modality × pipeline-stage grid. It makes
    the ecosystem's shape legible at a glance: where the field is crowded, and
    where it is a desert (e.g. ECoG decoding, or fNIRS real-time acquisition).

Pure stdlib, deterministic, unit-tested. Vocabularies are shared with the
relevance engine so the two always agree on what a term means.

    facets(repo)            -> {modality, paradigm, signal_chain, standards}
    coverage_matrix(projs)  -> {stages, modalities, cells, totals}
    standards_graph(projs)  -> {standards:[{standard, repos, count}], edges:[...]}
"""
from __future__ import annotations

import re

import relevance as _R

# Ordered pipeline stages — the spine of a BCI system, source → sink.
SIGNAL_CHAIN = ["Acquisition", "Preprocessing", "Feature extraction", "Decoding", "Application"]

# Stage vocabularies. A term is matched as a topic or a whole word in the text.
_STAGE_TERMS = {
    "Acquisition": {
        "acquisition", "amplifier", "adc", "daq", "electrode", "electrodes",
        "headset", "wearable", "driver", "record", "recording", "capture",
        "board", "openbci", "brainflow", "cyton", "ganglion", "ads1299",
        "biosignal-acquisition", "data-acquisition", "streaming", "stream",
    },
    "Preprocessing": {
        "filter", "filtering", "notch", "band-pass", "bandpass", "highpass",
        "lowpass", "artifact", "artefact", "denoise", "denoising", "ica",
        "re-reference", "referencing", "epoch", "epoching", "resample",
        "resampling", "preprocess", "preprocessing", "cleaning", "detrend",
    },
    "Feature extraction": {
        "feature", "features", "feature-extraction", "csp", "psd",
        "spectral", "spectrum", "wavelet", "riemannian", "covariance",
        "connectivity", "band-power", "bandpower", "coherence", "erp",
        "time-frequency", "power-spectra", "aperiodic",
    },
    "Decoding": {
        "decode", "decoding", "classifier", "classification", "prediction",
        "regression", "deep-learning", "machine-learning", "neural-decoding",
        "model", "inference", "tokenization", "manifold-learning",
        "geometric-deep-learning",
    },
    "Application": {
        "neurofeedback", "biofeedback", "speller", "control", "closed-loop",
        "closed-loop-control", "prosthesis", "prosthetic", "wheelchair",
        "cursor", "gamma-entrainment", "brain-mapping", "application", "app",
        "assistive", "rehabilitation", "game",
    },
}


def _norm(repo: dict) -> tuple[set, str]:
    name = (repo.get("full_name") or "").split("/")[-1].lower()
    desc = (repo.get("description") or "").lower()
    topics = {str(t).lower() for t in (repo.get("topics") or [])}
    text = " ".join([name.replace("-", " "), desc, " ".join(topics).replace("-", " ")])
    return topics, re.sub(r"\s+", " ", text)


def _match_terms(mapping: dict, topics: set, text: str) -> list[str]:
    """Return the sorted distinct *labels* for terms present. `mapping` maps a
    search term to a display label (dict); a set maps each term to itself."""
    out = set()
    items = mapping.items() if isinstance(mapping, dict) else ((t, t) for t in mapping)
    for term, label in items:
        if term in topics or re.search(r"(?<![a-z0-9])" + re.escape(term.replace("-", " ")) + r"(?![a-z0-9])", text):
            out.add(label)
    return sorted(out)


def facets(repo: dict) -> dict:
    """Extract the four structured domain facets for a repository."""
    topics, text = _norm(repo)
    modality = _match_terms(_R.MODALITY_TERMS, topics, text)
    paradigm = _match_terms(_R.PARADIGM_TERMS, topics, text)
    standards = _match_terms(_R.STANDARD_TERMS, topics, text)
    chain = [stage for stage in SIGNAL_CHAIN if _match_terms(_STAGE_TERMS[stage], topics, text)]
    return {
        "modality": modality,
        "paradigm": paradigm,
        "signal_chain": chain,
        "standards": standards,
    }


# Canonical modality order for the coverage matrix rows.
_MODALITY_ORDER = ["EEG", "ECoG", "EMG", "fNIRS", "MEG", "EOG", "spikes/LFP"]


def coverage_matrix(projects: list[dict]) -> dict:
    """Build the modality × signal-chain coverage grid.

    Each project is expected to carry a ``facets`` dict (attach with facets()).
    A project contributes to cell (modality, stage) once if it has both. The
    result is fully deterministic and additive.
    """
    seen_mods, cells = set(), {}
    stage_totals = {s: 0 for s in SIGNAL_CHAIN}
    for p in projects:
        f = p.get("facets") or {}
        mods = f.get("modality") or []
        stages = f.get("signal_chain") or []
        for m in mods:
            seen_mods.add(m)
        for s in stages:
            stage_totals[s] += 1
        for m in mods:
            for s in stages:
                cells[f"{m}|{s}"] = cells.get(f"{m}|{s}", 0) + 1
    modalities = [m for m in _MODALITY_ORDER if m in seen_mods] + sorted(seen_mods - set(_MODALITY_ORDER))
    grid = []
    for m in modalities:
        row = {"modality": m, "cells": [cells.get(f"{m}|{s}", 0) for s in SIGNAL_CHAIN]}
        row["total"] = sum(row["cells"])
        grid.append(row)
    return {
        "stages": SIGNAL_CHAIN,
        "modalities": modalities,
        "grid": grid,
        "stage_totals": [stage_totals[s] for s in SIGNAL_CHAIN],
        "n_projects": len(projects),
    }


def standards_graph(projects: list[dict]) -> dict:
    """Build the standards-interoperability view.

    For each standard, the repositories that speak it. Two repositories that
    share a standard can interoperate through it — we surface each standard as a
    hub with its member repos, plus a compact edge count (pairs that share at
    least one standard) so the UI can show how connected the ecosystem is.
    """
    by_std: dict[str, list[str]] = {}
    per_repo_stds: dict[str, set] = {}
    for p in projects:
        fn = p.get("full_name") or ""
        stds = (p.get("facets") or {}).get("standards") or []
        if stds:
            per_repo_stds[fn] = set(stds)
        for s in stds:
            by_std.setdefault(s, []).append(fn)
    standards = [
        {"standard": s, "count": len(repos), "repos": sorted(repos)}
        for s, repos in sorted(by_std.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]
    # interoperability edges: unordered repo pairs sharing >= 1 standard
    repos = sorted(per_repo_stds)
    edges = 0
    for i in range(len(repos)):
        for j in range(i + 1, len(repos)):
            if per_repo_stds[repos[i]] & per_repo_stds[repos[j]]:
                edges += 1
    return {
        "standards": standards,
        "n_standards": len(standards),
        "n_repos_with_standards": len(per_repo_stds),
        "interop_edges": edges,
    }
