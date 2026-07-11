#!/usr/bin/env python3
"""Tests for the v7 relevance engine (scripts/relevance.py).

The engine's whole job is to tell real BCI software from generic ML that merely
shares vocabulary. These tests pin that behaviour on concrete, real-world repo
shapes: the ML junk that used to leak in MUST drop, the genuine BCI tools MUST
stay, and the ``neural`` disambiguation MUST distinguish "neural network" from
"neural interface". Everything here is deterministic and offline.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import relevance as R  # noqa: E402


def _repo(name, desc="", topics=None, homepage=""):
    return {"full_name": name, "description": desc, "topics": topics or [], "homepage": homepage}


# ── the junk that used to leak in must now be rejected ───────────────────────

GENERIC_ML_JUNK = [
    _repo("pytorch/pytorch", "Tensors and dynamic neural networks in Python with strong GPU acceleration",
          ["deep-learning", "machine-learning", "gpu", "autograd"]),
    _repo("tensorflow/tensorflow", "An open source machine learning framework for everyone",
          ["deep-learning", "machine-learning", "deep-neural-networks"]),
    _repo("keras-team/keras", "Deep learning for humans", ["deep-learning", "machine-learning", "jax"]),
    _repo("norse/norse", "Deep learning with spiking neural networks (SNNs) in PyTorch",
          ["deep-learning", "machine-learning", "gpu"]),
    _repo("BindsNET/bindsnet", "Simulation of spiking neural networks (SNNs) using PyTorch",
          ["machine-learning", "gpu-computing", "neurons"]),
    _repo("fangwei123456/spikingjelly", "An open-source deep learning framework for spiking neural networks",
          ["deep-learning", "machine-learning", "pytorch"]),
    _repo("aramis-lab/clinica", "Software platform for clinical neuroimaging studies",
          ["bids-format", "freesurfer", "brainweb"]),
    _repo("cdeust/Cortex", "Accountable memory for AI agents — it forgets on purpose",
          ["agent-memory-system", "anthropic", "artificial-intelligence", "causal-inference"]),
    _repo("max-talanov/1", "personal repository",
          ["neurotechnology", "spiking-neural-networks", "machine-learning", "machine-consciousness"]),
]


def test_generic_ml_is_rejected():
    for repo in GENERIC_ML_JUNK:
        res = R.score(repo)
        assert res["decision"] == "drop", f"{repo['full_name']} should be dropped, got brs={res['brs']}"


def test_pytorch_scores_deeply_negative():
    # not just below the gate — the framework identity + generic-ML vocabulary
    # should push the raw score well negative, a comfortable margin.
    res = R.score(GENERIC_ML_JUNK[0])
    assert res["raw"] < 0


# ── genuine BCI/neuro tools must be kept ─────────────────────────────────────

REAL_BCI = [
    _repo("mne-tools/mne-python", "MNE: Magnetoencephalography (MEG) and Electroencephalography (EEG)",
          ["eeg", "meg", "mne", "neuroscience"]),
    _repo("braindecode/braindecode", "Deep learning software to decode EEG, ECG or MEG signals",
          ["deep-learning", "eeg", "ecog", "electroencephalography"]),
    _repo("brainflow-dev/brainflow", "BrainFlow is a library intended to obtain, parse and analyze EEG data",
          ["bci", "eeg", "emg", "brainflow"]),
    _repo("NeuroTechX/moabb", "Mother of All BCI Benchmarks", ["bci", "eeg", "benchmark"]),
    _repo("pyRiemann/pyRiemann", "Machine learning for multivariate data through Riemannian geometry",
          ["bci", "eeg", "riemannian-geometry"]),
    _repo("PerlinWarp/pyomyo", "PyoMyo - Python Opensource Myo armband library",
          ["emg", "myo", "myo-armband"]),
    _repo("sccn/liblsl", "C++ lsl library for multi-modal time-synched data transmission",
          ["lsl", "lab-streaming-layer"]),
    _repo("NeuralEnsemble/elephant", "Elephant is the Electrophysiology Analysis Toolkit",
          ["electrophysiology", "neurophysiology", "neuroscience"]),
    _repo("openbci/OpenBCI_GUI", "GUI for the OpenBCI biosensing boards", ["openbci", "eeg"]),
]


def test_real_bci_is_kept():
    for repo in REAL_BCI:
        res = R.score(repo)
        assert res["decision"] == "keep", f"{repo['full_name']} should be kept, got brs={res['brs']}"


def test_pyriemann_kept_despite_ml_wording():
    # the disambiguation win: real BCI-ML (says "machine learning" but tagged
    # bci+eeg) is kept, unlike pytorch which says the same words without anchor.
    assert R.is_relevant(REAL_BCI[4])


# ── the 'neural' disambiguation ──────────────────────────────────────────────

def test_neural_network_is_not_neuro():
    assert R._neural_is_neuro("dynamic neural networks in python") is False


def test_neural_interface_is_neuro():
    assert R._neural_is_neuro("a neural interface for prosthetic control") is True


def test_neural_absent_returns_none():
    assert R._neural_is_neuro("eeg signal processing toolkit") is None


def test_neural_network_repo_without_anchor_drops():
    repo = _repo("someone/nn-lib", "A fast neural network library", ["deep-learning", "neural-network"])
    assert R.score(repo)["decision"] == "drop"


# ── single unambiguous signals clear the gate alone ──────────────────────────

def test_single_modality_clears_gate():
    assert R.is_relevant(_repo("x/eeg-tool", "EEG analysis", ["eeg"]))


def test_single_standard_clears_gate():
    assert R.is_relevant(_repo("x/edf-io", "Read and write EDF files", ["edf"]))


def test_single_hardware_clears_gate():
    assert R.is_relevant(_repo("x/openbci-driver", "Driver for OpenBCI Cyton", ["openbci", "cyton"]))


# ── cardiac electrophysiology is a different field ───────────────────────────

def test_cardiac_electrophysiology_dropped():
    repo = _repo("x/heart-sim", "Cardiac electrophysiology solver, monodomain model",
                 ["cardiac", "electrophysiology", "monodomain-model"])
    assert R.score(repo)["decision"] == "drop"


# ── structural guarantees ────────────────────────────────────────────────────

def test_ledger_is_signed_and_explained():
    res = R.score(REAL_BCI[2])  # brainflow
    assert res["ledger"], "kept repo must carry an evidence ledger"
    for entry in res["ledger"]:
        assert set(entry) == {"points", "kind", "reason"}
        assert isinstance(entry["points"], int)
        assert entry["reason"]


def test_score_is_deterministic():
    a = R.score(REAL_BCI[0])
    b = R.score(REAL_BCI[0])
    assert a == b


def test_brs_is_clamped_0_100():
    for repo in REAL_BCI + GENERIC_ML_JUNK:
        res = R.score(repo)
        assert 0 <= res["brs"] <= 100


def test_empty_repo_drops_cleanly():
    res = R.score(_repo("x/empty", "", []))
    assert res["decision"] == "drop"
    assert res["brs"] == 0
