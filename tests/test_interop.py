# Tests for scripts/interop.py — the interop-detection layer (v6).
# Word-boundary discipline is the whole point: these tests pin the exact
# false-positive traps the vocabulary was designed around.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import interop  # noqa: E402


def _p(**kw):
    base = {"topics": [], "description": "", "homepage": ""}
    base.update(kw)
    return base


def test_vocab_loads_and_is_wellformed():
    tags = interop.load_vocab()
    assert len(tags) >= 15
    assert all(t["tag"] == t["tag"].lower() for t in tags)
    assert len({t["tag"] for t in tags}) == len(tags)  # unique


def test_topic_match_simple():
    assert interop.detect(_p(topics=["brainflow", "eeg"])) == ["brainflow"]


def test_description_match_case_insensitive():
    got = interop.detect(_p(description="Streams EEG over LSL to OpenBCI Cyton"))
    assert got == ["lsl", "openbci"]


def test_unity_does_not_fire_inside_community():
    assert interop.detect(_p(description="A community of researchers")) == []
    assert "unity" in interop.detect(_p(topics=["unity3d"]))
    assert "unity" in interop.detect(_p(description="Built with Unity."))


def test_mne_does_not_fire_inside_mnemonic():
    assert interop.detect(_p(description="mnemonic tricks for studying")) == []
    assert interop.detect(_p(topics=["mne-python"])) == ["mne"]


def test_ble_does_not_fire_inside_possible():
    assert interop.detect(_p(description="the best possible decoder")) == []
    assert interop.detect(_p(description="streams over BLE")) == ["ble"]


def test_ros_requires_specific_forms_not_bare_ros():
    # bare "ros" is too collision-prone (rosetta, roster) — the vocabulary
    # deliberately requires ros2 / ros-noetic / ros-humble / full name.
    assert interop.detect(_p(description="rosters and rosetta")) == []
    assert interop.detect(_p(topics=["ros2"])) == ["ros"]
    assert interop.detect(_p(description="Robot-Operating-System bridge")) == ["ros"]


def test_muse_requires_qualified_forms():
    assert interop.detect(_p(description="a muse for poets")) == []
    assert interop.detect(_p(topics=["muse-lsl"])) == ["lsl", "muse"]


def test_homepage_contributes():
    assert interop.detect(_p(homepage="https://timeflux.io")) == ["timeflux"]


def test_empty_metadata_yields_empty():
    assert interop.detect(_p()) == []


def test_result_sorted_unique_and_capped():
    desc = ("lsl brainflow bids edf eeglab openvibe timeflux openbci emotiv "
            "neurosity ads1299 arduino esp32")
    got = interop.detect(_p(description=desc))
    assert got == sorted(got)
    assert len(got) == interop.MAX_TAGS_PER_PROJECT


def test_annotate_counts_tagged_projects():
    ps = [_p(topics=["brainflow"]), _p(description="nothing relevant"), _p(topics=["lsl"])]
    n = interop.annotate_interop(ps)
    assert n == 2
    assert ps[0]["interop"] == ["brainflow"]
    assert ps[1]["interop"] == []


def test_known_tags_matches_vocab():
    assert interop.known_tags() == {t["tag"] for t in interop.load_vocab()}
