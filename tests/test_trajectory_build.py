"""Merged trajectories: measured points only, engine points win, capped."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_trajectory as T  # noqa: E402


def _hist(*snaps):
    return {"version": 1, "snapshots": [
        {"snapshot_at": ts, "stars": stars, "meta": {}} for ts, stars in snaps]}


def test_history_points_carry_null_brs():
    m = T.build(_hist(("2026-07-01T00:00:00+00:00", {"a/b": 10})), {})
    assert m["a/b"] == [["2026-07-01T00:00:00+00:00", None, 10, None]]


def test_series_is_time_ordered():
    m = T.build(_hist(("2026-07-02T00:00:00+00:00", {"a/b": 12}),
                      ("2026-07-01T00:00:00+00:00", {"a/b": 10})), {})
    assert [p[2] for p in m["a/b"]] == [10, 12]


def test_engine_point_wins_and_completes():
    hist = _hist(("2026-07-16T14:00:00+00:00", {"a/b": 20}))
    eng = {"a/b": [["2026-07-16T14:00:00+00:00", 71, None, 64]]}
    m = T.build(hist, eng)
    assert m["a/b"] == [["2026-07-16T14:00:00+00:00", 71, 20, 64]]


def test_engine_only_project_included():
    m = T.build(_hist(), {"new/one": [["2026-07-16T14:00:00+00:00", 55, 3, 60]]})
    assert m["new/one"][0][1] == 55


def test_cap_keeps_most_recent():
    snaps = [(f"2026-07-01T{i:02d}:00:00+00:00", {"a/b": i}) for i in range(24)]
    snaps += [(f"2026-07-02T{i:02d}:00:00+00:00", {"a/b": 100 + i}) for i in range(24)]
    snaps += [(f"2026-07-03T{i:02d}:00:00+00:00", {"a/b": 200 + i}) for i in range(24)]
    snaps += [(f"2026-07-04T{i:02d}:00:00+00:00", {"a/b": 300 + i}) for i in range(24)]
    snaps += [(f"2026-07-05T{i:02d}:00:00+00:00", {"a/b": 400 + i}) for i in range(10)]
    m = T.build(_hist(*snaps), {})
    assert len(m["a/b"]) == 96
    assert m["a/b"][-1][2] == 409                 # newest kept
    assert m["a/b"][0][2] == 10                   # 106 points − 96 = oldest 10 dropped


def test_malformed_inputs_never_crash():
    m = T.build({"snapshots": [{"snapshot_at": None, "stars": {"a/b": 1}},
                               {"snapshot_at": "t", "stars": "nope"}]},
                {"a/b": "nope", "c/d": [["t", 1], [None, 1, 2, 3]]})
    assert m == {}


def test_output_matches_shipped_schema():
    import jsonschema
    schema = json.load(open(os.path.join(os.path.dirname(__file__), "..",
                                         "data", "trajectory.schema.json")))
    m = T.build(_hist(("2026-07-01T00:00:00+00:00", {"a/b": 10})),
                {"a/b": [["2026-07-16T00:00:00+00:00", 70, 11, 60]]})
    jsonschema.validate(m, schema)
