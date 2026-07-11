#!/usr/bin/env python3
"""
AxonOS Radar — Relevance Engine (v7).

The radar's old inclusion test was a boolean: keep a repo if it carried a
context topic (e.g. ``machine-learning``) plus any neuro keyword. That let
generic ML in, because the keyword list contained the single most ambiguous
word in the field — ``neural``. "dynamic **neural** networks" (PyTorch) is
indistinguishable, to a membership test, from "**neural** interface".

This module replaces the boolean with a transparent, deterministic
**BCI Relevance Score (BRS, 0..100)** built from a *signed evidence ledger*:
every positive and negative signal is recorded with its points and a
human-readable reason, so inclusion is auditable rather than opaque. The
decisive idea is **disambiguation by anchor**: the word ``neural`` only counts
as neuroscience when it sits next to a neuro anchor (interface, signal,
decoding, implant, recording, prosthetic...). ``neural network`` / ``neural
net`` / ``deep learning`` with *no* unambiguous neuro anchor is negative
evidence — it is generic ML and is penalised, not rewarded.

Pure stdlib, importable, unit-tested. The rubric here is the published
contract (docs/METHODOLOGY.md, "Relevance Engine (v7)").

    score(repo) -> dict  # {brs, decision, tier, ledger:[{points,reason,kind}], anchors:{...}}
"""
from __future__ import annotations

import re

# ── Gate ─────────────────────────────────────────────────────────────────────
# A repo is kept iff its BRS is at or above this threshold. Calibrated (against
# the live ecosystem snapshot, see tests/test_relevance.py) so that ONE
# unambiguous field signal — an acquisition modality (EEG/ECoG/EMG/fNIRS/MEG),
# a field standard (LSL/EDF/BIDS/FIF/OpenBCI/BrainFlow), named BCI hardware, an
# explicit BCI topic, or a BCI paradigm — clears the bar alone, while a single
# *ambiguous* neuro word (electrophysiology, shared with cardiology) needs a
# genuine neural context to pass, and generic ML — even ML that says "neural" —
# falls far below it.
GATE = 40

# ── Vocabularies ─────────────────────────────────────────────────────────────
# Explicit BCI topics, split by specificity:
#   HARD — concretely names the interface. Decisive AND shields a repo from the
#          generic-ML penalty (a repo literally tagged brain-computer-interface
#          that also says "machine learning" is doing BCI-ML, like pyRiemann).
#   SOFT — a broad self-label people apply loosely. Scores well, but does NOT
#          shield the neuromorphic / generic-ML penalties, so a personal
#          spiking-NN repo that merely tags itself "neurotechnology" still falls.
EXPLICIT_BCI_HARD = {
    "bci", "bmi", "brain-computer-interface", "brain-machine-interface",
    "brain-computer-interfaces", "brain-machine-interfaces", "brain-computer",
    "brain-machine", "neuroprosthetics", "neuroprosthetic",
    "neural-interface", "neural-interfaces",
}
EXPLICIT_BCI_SOFT = {"neurotechnology", "neurotech"}
EXPLICIT_BCI = EXPLICIT_BCI_HARD | EXPLICIT_BCI_SOFT

# Acquisition modalities — unambiguous physiological recording types. These
# words do not occur in generic ML.
MODALITY_TERMS = {
    "eeg": "EEG", "electroencephalography": "EEG", "electroencephalogram": "EEG",
    "ecog": "ECoG", "electrocorticography": "ECoG",
    "emg": "EMG", "electromyography": "EMG",
    "fnirs": "fNIRS", "nirs": "fNIRS",
    "meg": "MEG", "magnetoencephalography": "MEG",
    "eog": "EOG", "electrooculography": "EOG",
    "lfp": "spikes/LFP", "local-field-potential": "spikes/LFP",
    "spike-sorting": "spikes/LFP", "spike-train": "spikes/LFP",
    "single-unit": "spikes/LFP", "multi-unit": "spikes/LFP",
    "neuropixels": "spikes/LFP", "intracortical": "spikes/LFP",
}

# Field standards / interchange formats. Present ONLY in neuro/BCI software;
# each is very strong positive evidence and doubles as the interop tissue.
STANDARD_TERMS = {
    "lsl": "LSL", "labstreaminglayer": "LSL", "lab-streaming-layer": "LSL",
    "lab-streaming": "LSL", "pylsl": "LSL", "liblsl": "LSL", "xdf": "LSL",
    "bids": "BIDS", "brain-imaging-data-structure": "BIDS", "eeg-bids": "BIDS",
    "edf": "EDF", "edf+": "EDF", "bdf": "EDF", "gdf": "EDF", "european-data-format": "EDF",
    "fif": "FIF/MNE", "mne-python": "FIF/MNE", "mne": "FIF/MNE",
    "openbci": "OpenBCI", "brainflow": "BrainFlow",
    "openvibe": "OpenViBE", "fieldtrip": "FieldTrip", "eeglab": "EEGLAB",
    "neo-python": "Neo", "neurodata-without-borders": "NWB", "nwb": "NWB", "pynwb": "NWB",
}

# Named BCI/neuro acquisition hardware and headsets — unambiguous.
HARDWARE_TERMS = {
    "openbci", "muse-eeg", "muse-headband", "emotiv", "epoc", "neuralink",
    "blackrock", "plexon", "intan", "g.tec", "gtec", "ads1299", "ads1298",
    "neuropixels", "cyton", "ganglion", "unicorn-hybrid", "brainvision",
    "biosemi", "neurosky", "flexeeg", "freeeeg",
}

# BCI experimental paradigms — unambiguous.
PARADIGM_TERMS = {
    "p300": "P300", "p3-speller": "P300", "p300-speller": "P300",
    "ssvep": "SSVEP", "steady-state-visual": "SSVEP",
    "motor-imagery": "Motor imagery", "motor-imagry": "Motor imagery",
    "erp": "ERP", "event-related-potential": "ERP", "evoked-potential": "ERP",
    "erd": "ERD/ERS", "ers": "ERD/ERS",
    "neurofeedback": "Neurofeedback", "biofeedback": "Neurofeedback",
    "mi-bci": "Motor imagery", "c-vep": "c-VEP", "code-vep": "c-VEP",
}

# Unambiguous neuro terms (not modalities/standards/hardware/paradigms above).
NEURO_TERMS = {
    "electrophysiology", "electrophysiological", "cortical", "subcortical",
    "neurostimulation", "neuromodulation", "deep-brain-stimulation", "dbs",
    "brain-signal", "brain-signals", "brainwave", "brainwaves",
    "neural-signal", "neural-signals", "neural-decoding", "neural-recording",
    "neural-implant", "neural-implants", "neural-control", "neural-activity",
    "motor-cortex", "sensorimotor", "prosthesis-control",
}

# Anchors that legitimise the ambiguous word "neural": if "neural" appears
# adjacent to one of these, it is neuroscience, not an ML "neural network".
NEURAL_ANCHOR_NEXT = {
    "interface", "interfaces", "signal", "signals", "signalling", "decoding",
    "implant", "implants", "recording", "recordings", "activity", "control",
    "data", "prosthesis", "prosthetic", "stimulation", "spike", "spikes",
    "electrode", "electrodes", "oscillation", "oscillations",
}

# ── Negative-evidence vocabularies (the anti-PyTorch disambiguation) ──────────
# Generic ML-framework identity. If the repo NAME *is* one of these (or the
# text is dominated by it) and there is no BCI anchor, it is not a BCI project.
ML_FRAMEWORK_NAMES = {
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "jax", "mxnet",
    "caffe", "caffe2", "theano", "paddlepaddle", "mindspore", "flax", "haiku",
    "transformers", "huggingface", "diffusers", "detectron2", "yolov5", "yolov8",
    "ultralytics", "fastai", "lightning", "pytorch-lightning", "onnx", "tvm",
}
ML_GENERIC_TERMS = {
    "deep-learning", "deep learning", "machine-learning", "machine learning",
    "neural-network", "neural-networks", "neural network", "neural networks",
    "neural-net", "neural net", "convolutional", "transformer", "large-language",
    "llm", "gpt", "chatbot", "stable-diffusion", "reinforcement-learning",
    "computer-vision", "gpu-acceleration", "autograd", "tensor",
}
# Neuromorphic / spiking-NN ML: neuroscience-flavoured vocabulary, but these
# are ML libraries, not BCI. Penalised unless a real BCI anchor is present.
NEUROMORPHIC_TERMS = {
    "spiking-neural-network", "spiking-neural-networks", "spiking neural",
    "neuromorphic", "snn", "leaky-integrate-and-fire", "surrogate-gradient",
    "event-driven", "loihi",
}
# Neuroimaging (structural/functional MRI, PET) — a different field from BCI.
NEUROIMAGING_TERMS = {
    "mri", "fmri", "smri", "pet-imaging", "freesurfer", "voxel", "voxels",
    "dti", "tractography", "diffusion-mri", "cortical-surface", "brainweb",
    "ants", "fsl", "spm12", "nifti", "dicom", "neuroimaging", "morphometry",
}
# AI-agent / LLM-tooling — false positives on words like "cortex", "memory".
AI_AGENT_TERMS = {
    "ai-agent", "ai-agents", "agent-memory", "llm-agent", "autonomous-agent",
    "prompt-engineering", "rag", "vector-database", "embeddings-store",
    "artificial-intelligence", "anthropic", "openai-api",
}
# Cardiac electrophysiology shares the word "electrophysiology" with neural
# ephys but is a different field. These terms mark a cardiac repo.
CARDIAC_TERMS = {
    "cardiac", "cardiology", "heart", "myocardial", "myocardium", "monodomain",
    "bidomain", "ecg-only", "electrocardiography", "ventricular", "atrial",
}
# Weak neural-context booster: only ever counts *alongside* another neuro
# signal (never alone — "neuroscience" by itself is too broad and appears in
# brain simulators). It lets an ambiguous ephys tool with real neural context
# reach the gate, without opening the door to cardiac solvers or simulators.
NEURAL_CONTEXT = {
    "neuroscience", "neurophysiology", "neurophysiological", "neuroinformatics",
    "brain", "neuron", "neurons", "synaptic", "ephys", "ieeg",
}


def _norm(repo: dict) -> tuple[str, str, set, str]:
    """Return (name, description-lower, topic-set-lower, combined-text-lower)."""
    name = (repo.get("full_name") or "").split("/")[-1].lower()
    desc = (repo.get("description") or "").lower()
    topics = {str(t).lower() for t in (repo.get("topics") or [])}
    homepage = (repo.get("homepage") or "").lower()
    text = " ".join([name.replace("-", " "), desc, " ".join(topics).replace("-", " "), homepage])
    text = re.sub(r"\s+", " ", text)
    return name, desc, topics, text


def _has(term: str, text: str, topics: set) -> bool:
    """Word-boundary membership: as a topic, or as a whole word/phrase in text.
    Hyphens in a term are treated as spaces so 'motor-imagery' matches 'motor
    imagery' too. 'adc' must not fire inside 'broadcast'."""
    if term in topics:
        return True
    t = term.replace("-", " ")
    return re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", text) is not None


def _neural_is_neuro(text: str) -> bool | None:
    """Classify occurrences of the ambiguous word 'neural'.
    Returns True if it appears with a neuro anchor (→ neuroscience), False if it
    only ever appears as 'neural network/net' (→ ML), None if 'neural' absent."""
    hits = list(re.finditer(r"(?<![a-z])neural\s+([a-z]+)", text))
    if "neural" not in text:
        return None
    if not hits:
        return None
    saw_anchor = any(m.group(1) in NEURAL_ANCHOR_NEXT for m in hits)
    saw_ml = any(m.group(1) in {"network", "networks", "net", "nets"} for m in hits)
    if saw_anchor:
        return True
    if saw_ml:
        return False
    return None


def score(repo: dict) -> dict:
    """Compute the BCI Relevance Score and a full signed evidence ledger.

    The return is deterministic and self-describing:
        {
          "brs": int,                 # clamped 0..100
          "raw": int,                 # pre-clamp, can be negative (diagnostic)
          "decision": "keep"|"drop",
          "tier": str,                # human tier label
          "ledger": [ {points, kind, reason}, ... ],  # every signal, signed
          "anchors": { "explicit_bci": bool, "modality": bool, ... },
        }
    """
    name, desc, topics, text = _norm(repo)
    ledger: list[dict] = []

    def add(points: int, kind: str, reason: str):
        ledger.append({"points": points, "kind": kind, "reason": reason})

    # ---- unambiguous BCI anchors (each clears the gate alone) ---------------
    explicit_hard = sorted(t for t in EXPLICIT_BCI_HARD if _has(t, text, topics))
    explicit_soft = sorted(t for t in EXPLICIT_BCI_SOFT if _has(t, text, topics))
    explicit = explicit_hard + explicit_soft
    if explicit_hard:
        add(55, "core", f"Explicit BCI topic ({', '.join(explicit_hard[:2])})")
    elif explicit_soft:
        add(45, "core", f"Neurotech self-label ({', '.join(explicit_soft[:2])})")

    mods = sorted({label for term, label in MODALITY_TERMS.items() if _has(term, text, topics)})
    if mods:
        add(40, "modality", f"Acquisition modality ({', '.join(mods[:3])})")

    stds = sorted({label for term, label in STANDARD_TERMS.items() if _has(term, text, topics)})
    if stds:
        add(45, "standard", f"Field standard/format ({', '.join(stds[:3])})")

    hw = sorted(t for t in HARDWARE_TERMS if _has(t, text, topics))
    if hw:
        add(45, "hardware", f"Named BCI hardware ({', '.join(hw[:2])})")

    paras = sorted({label for term, label in PARADIGM_TERMS.items() if _has(term, text, topics)})
    if paras:
        add(40, "paradigm", f"BCI paradigm ({', '.join(paras[:2])})")

    # Ambiguous neuro terms (shared with cardiology / simulation): weaker, and
    # they need a genuine neural context to reach the gate on their own.
    neuro = sorted(t for t in NEURO_TERMS if _has(t, text, topics))
    if neuro:
        add(25, "neuro", f"Neuro term ({', '.join(neuro[:2])})")

    neural_kind = _neural_is_neuro(text)
    if neural_kind is True:
        add(25, "neuro", "Neuro-anchored 'neural' phrase (e.g. neural interface/signal/decoding)")

    # "concrete" = a real acquisition/standard/hardware/paradigm signal, or a
    # HARD explicit topic. This is what suppresses the neuromorphic penalty — a
    # soft self-label alone must not shield a spiking-NN library.
    concrete = bool(explicit_hard or mods or stds or hw or paras)
    decisive = bool(explicit or mods or stds or hw or paras)
    anchor_present = decisive or bool(neuro or neural_kind is True)

    cardiac = sorted(t for t in CARDIAC_TERMS if _has(t, text, topics))
    # Neural-context booster: lifts an ambiguous neuro term into keep range, but
    # only when there's real neural context AND the repo is not cardiac.
    if (neuro or neural_kind is True) and not decisive and not cardiac:
        ctx = sorted(t for t in NEURAL_CONTEXT if _has(t, text, topics))
        if ctx:
            add(15, "neuro", f"Neural context ({', '.join(ctx[:2])})")

    # credibility: paper-backed (only meaningful once there is an anchor)
    if anchor_present and (repo.get("has_citation")
                           or re.search(r"\bdoi\.org/|\bdoi:\s*10\.", text) or "citation.cff" in text):
        add(10, "provenance", "Paper-backed (DOI / CITATION.cff)")

    # ---- negative evidence (disambiguation) --------------------------------
    if neural_kind is False and not anchor_present:
        add(-40, "neg", "'neural network'/'net' with no neuro anchor — generic ML")

    if (name in ML_FRAMEWORK_NAMES or any(_has(n, text, topics) for n in ML_FRAMEWORK_NAMES)) and not anchor_present:
        add(-60, "neg", "Generic ML-framework identity with no BCI anchor")

    ml_generic = sorted(t for t in ML_GENERIC_TERMS if _has(t, text, topics))
    if ml_generic and not anchor_present:
        add(-40, "neg", f"Generic ML vocabulary ({', '.join(ml_generic[:2])}) with no BCI anchor")

    neuromorphic = sorted(t for t in NEUROMORPHIC_TERMS if _has(t, text, topics))
    if neuromorphic and not concrete:
        add(-35, "neg", f"Neuromorphic/spiking-NN ML ({', '.join(neuromorphic[:2])}) with no BCI-acquisition anchor")

    imaging = sorted(t for t in NEUROIMAGING_TERMS if _has(t, text, topics))
    if imaging and not (explicit or mods or hw or paras):
        add(-30, "neg", f"Neuroimaging ({', '.join(imaging[:2])}) — different field from BCI")

    if cardiac and not (explicit or hw or paras) and "eeg" not in text and "ecog" not in text:
        add(-30, "neg", f"Cardiac electrophysiology ({', '.join(cardiac[:2])}) — different field from BCI")

    agent = sorted(t for t in AI_AGENT_TERMS if _has(t, text, topics))
    if agent and not anchor_present:
        add(-40, "neg", f"AI-agent/LLM tooling ({', '.join(agent[:2])}) — not BCI")

    raw = sum(e["points"] for e in ledger)
    brs = max(0, min(100, raw))
    decision = "keep" if raw >= GATE else "drop"

    # tier label — a legible summary of the strongest positive signal
    if explicit:
        tier = "L4_EXPLICIT_BCI"
    elif stds or hw:
        tier = "L3_STANDARD_OR_HARDWARE"
    elif mods or paras:
        tier = "L3_MODALITY_OR_PARADIGM"
    elif neuro or neural_kind is True:
        tier = "L2_NEURO_TERM"
    elif decision == "keep":
        tier = "L1_WEAK_KEEP"
    else:
        tier = "L0_REJECTED"

    return {
        "brs": brs,
        "raw": raw,
        "decision": decision,
        "tier": tier,
        "ledger": ledger,
        "anchors": {
            "explicit_bci": bool(explicit),
            "modality": bool(mods),
            "standard": bool(stds),
            "hardware": bool(hw),
            "paradigm": bool(paras),
            "neuro_term": bool(neuro or neural_kind is True),
        },
    }


def is_relevant(repo: dict) -> bool:
    """Boolean convenience wrapper over the BRS gate."""
    return score(repo)["decision"] == "keep"
