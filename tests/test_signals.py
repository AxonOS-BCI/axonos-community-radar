"""The Signals surface: what changed, and the promise that it stays stable.

A feed reader's contract is the id. If a signal's id churned between scans, every
reader would re-alert on the same fact every three hours — which is how people
learn to ignore a feed. Ids are therefore derived from (kind, project, ISO week)
and nothing else: the same fact keeps one identity for the week it is true.
"""
import json
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_signals as B  # noqa: E402

GEN = "2026-07-16T10:00:00+00:00"


def _radar(projects):
    return {"generated_at": GEN, "projects": projects}


def _p(name, **kw):
    base = {"full_name": name, "html_url": f"https://github.com/{name}",
            "brs": 71, "category": "EEG", "stars": 40,
            "facets": {"modality": ["EEG"]}}
    base.update(kw)
    return base


def test_flags_become_signals():
    payload = B.build_signals(_radar([
        _p("a/new", is_new=True),
        _p("b/rise", rising=True, stars_delta_7d=12),
        _p("c/cool", falling=True, stars_delta_7d=-4),
        _p("d/quiet"),
    ]), {"a/new": "2026-07-14T00:00:00+00:00"})
    assert payload["counts"] == {"new": 1, "rising": 1, "cooling": 1}
    kinds = {s["project"]["full_name"]: s["kind"] for s in payload["signals"]}
    assert kinds == {"a/new": "new", "b/rise": "rising", "c/cool": "cooling"}


def test_quiet_ecosystem_yields_no_signals():
    """No flags is a valid state — it must produce an empty feed, not noise."""
    payload = B.build_signals(_radar([_p("x/quiet"), _p("y/quiet")]), {})
    assert payload["signals"] == []
    assert payload["counts"] == {"new": 0, "rising": 0, "cooling": 0}


def test_ids_are_stable_across_runs_in_the_same_week():
    r = _radar([_p("a/new", is_new=True)])
    first = B.build_signals(r, {})["signals"][0]["id"]
    second = B.build_signals(r, {})["signals"][0]["id"]
    assert first == second


def test_id_changes_with_week_not_with_scan():
    """Same fact, later scan, same week -> same id. Next week -> new id."""
    a = B.build_signals(_radar([_p("a/new", is_new=True)]), {})["signals"][0]["id"]
    later_same_week = {"generated_at": "2026-07-17T22:00:00+00:00",
                       "projects": [_p("a/new", is_new=True)]}
    b = B.build_signals(later_same_week, {})["signals"][0]["id"]
    next_week = {"generated_at": "2026-07-24T10:00:00+00:00",
                 "projects": [_p("a/new", is_new=True)]}
    c = B.build_signals(next_week, {})["signals"][0]["id"]
    assert a == b
    assert a != c


def test_id_is_unique_per_kind_for_one_project():
    payload = B.build_signals(_radar([_p("a/x", is_new=True, rising=True, stars_delta_7d=5)]), {})
    ids = [s["id"] for s in payload["signals"]]
    assert len(ids) == len(set(ids)) == 2


def test_evidence_is_carried_not_invented():
    payload = B.build_signals(_radar([_p("b/rise", rising=True, stars_delta_7d=12)]),
                              {"b/rise": "2026-01-01T00:00:00+00:00"})
    assert payload["signals"][0]["evidence"] == {"stars_delta_7d": 12}


def test_rising_is_ordered_by_measured_velocity():
    payload = B.build_signals(_radar([
        _p("slow/one", rising=True, stars_delta_7d=3),
        _p("fast/two", rising=True, stars_delta_7d=99),
    ]), {})
    rising = [s["project"]["full_name"] for s in payload["signals"] if s["kind"] == "rising"]
    assert rising == ["fast/two", "slow/one"]


def test_feeds_are_valid_rss_and_sliced(tmp_path):
    payload = B.build_signals(_radar([
        _p("a/new", is_new=True), _p("b/rise", rising=True, stars_delta_7d=8),
    ]), {})
    B.write_all(payload, tmp_path)
    for name in ("signals.xml", "new.xml", "rising.xml"):
        xml.dom.minidom.parse(str(tmp_path / "feeds" / name))
    assert (tmp_path / "data" / "signals.json").exists()
    new_xml = (tmp_path / "feeds" / "new.xml").read_text()
    assert "a/new" in new_xml and "b/rise" not in new_xml
    rising_xml = (tmp_path / "feeds" / "rising.xml").read_text()
    assert "b/rise" in rising_xml and "a/new" not in rising_xml


def test_feed_escapes_hostile_project_names(tmp_path):
    """A repo name is attacker-controlled text; it must never break the XML."""
    payload = B.build_signals(_radar([
        _p("evil/<script>&\"'", is_new=True, html_url="https://github.com/evil/x?a=1&b=2"),
    ]), {})
    B.write_all(payload, tmp_path)
    doc = xml.dom.minidom.parse(str(tmp_path / "feeds" / "signals.xml"))
    assert doc.getElementsByTagName("item")


def test_guid_matches_signal_id(tmp_path):
    payload = B.build_signals(_radar([_p("a/new", is_new=True)]), {})
    B.write_all(payload, tmp_path)
    xml_txt = (tmp_path / "feeds" / "signals.xml").read_text()
    assert payload["signals"][0]["id"] in xml_txt


def test_output_is_json_serializable_and_versioned(tmp_path):
    payload = B.build_signals(_radar([_p("a/new", is_new=True)]), {})
    B.write_all(payload, tmp_path)
    on_disk = json.loads((tmp_path / "data" / "signals.json").read_text())
    assert on_disk["version"] == 1
    assert on_disk["week"] == "2026-W29"
