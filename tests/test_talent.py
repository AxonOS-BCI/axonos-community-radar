"""The Talent view: every number derives from the map; scope stated honestly."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_talent as T  # noqa: E402


def _p(name, stars=10, brs=70, health=60, mods=("EEG",), cat="Decoding & ML", lang="Python"):
    return {"full_name": name, "stars": stars, "brs": brs, "category": cat,
            "language": lang, "signals": {"overall": health},
            "facets": {"modality": list(mods)}}


def _radar(projects, builders=None):
    return {"generated_at": "2026-07-27T15:11:57+00:00",
            "projects": projects, "builders": builders or []}


def test_owner_aggregation():
    d = T.build(_radar([_p("o/a", stars=5, brs=60), _p("o/b", stars=7, brs=90)]))
    b = d["builders"][0]
    assert (b["owner"], b["project_count"], b["total_stars"], b["best_brs"]) == ("o", 2, 12, 90)
    assert b["projects"] == ["o/a", "o/b"]


def test_median_health_is_a_median():
    d = T.build(_radar([_p("o/a", health=40), _p("o/b", health=60), _p("o/c", health=100)]))
    assert d["builders"][0]["median_health"] == 60


def test_sorted_by_stars_then_projects():
    d = T.build(_radar([_p("small/x", stars=1), _p("big/y", stars=100)]))
    assert [b["owner"] for b in d["builders"]] == ["big", "small"]


def test_engine_meta_enriches_not_sources():
    builders_meta = [{"owner": "o", "owner_type": "Organization", "followers": 42,
                      "total_stars": 999999}]   # wrong number on purpose
    d = T.build(_radar([_p("o/a", stars=5)], builders_meta))
    b = d["builders"][0]
    assert b["owner_type"] == "Organization" and b["followers"] == 42
    assert b["total_stars"] == 5                 # derived, not copied


def test_clusters_count_builders_once():
    d = T.build(_radar([_p("o/a", mods=("EEG",)), _p("o/b", mods=("EEG", "MEG"))]))
    assert d["clusters"]["EEG"] == {"builders": 1, "projects": 2, "stars": 20}
    assert d["clusters"]["MEG"]["builders"] == 1


def test_nulls_stay_null():
    d = T.build(_radar([{"full_name": "o/a", "stars": None, "brs": None,
                         "signals": None, "facets": None}]))
    b = d["builders"][0]
    assert b["best_brs"] is None and b["median_health"] is None and b["total_stars"] == 0


def test_scope_is_stated():
    d = T.build(_radar([_p("o/a")]))
    assert "contributor" in d["scope"]


def test_deterministic():
    r = _radar([_p("o/a"), _p("z/b", stars=99), _p("o/c", mods=("MEG",))])
    assert json.dumps(T.build(r), sort_keys=True) == json.dumps(T.build(r), sort_keys=True)
