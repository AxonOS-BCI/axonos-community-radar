# Tests for scripts/build_exports.py — the NDJSON data-product layer (v6).
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import build_exports  # noqa: E402


def test_ndjson_one_valid_line_per_project():
    payload = {"projects": [
        {"full_name": "a/b", "stars": 1, "interop": ["lsl"]},
        {"full_name": "c/d", "stars": 2},
    ]}
    nd = build_exports.build_ndjson(payload)
    lines = nd.strip().split("\n")
    assert len(lines) == 2
    parsed = [json.loads(x) for x in lines]
    assert parsed[0]["full_name"] == "a/b" and parsed[1]["stars"] == 2
    assert nd.endswith("\n")


def test_ndjson_deterministic_key_order():
    payload = {"projects": [{"b": 1, "a": 2}]}
    assert build_exports.build_ndjson(payload).startswith('{"a":2,"b":1}')


def test_ndjson_skips_non_dicts_and_handles_empty():
    assert build_exports.build_ndjson({"projects": []}) == ""
    nd = build_exports.build_ndjson({"projects": ["junk", {"x": 1}]})
    assert nd == '{"x":1}\n'


def test_main_writes_file(tmp_path):
    data = tmp_path / "radar.json"
    data.write_text(json.dumps({"projects": [{"full_name": "a/b"}]}), encoding="utf-8")
    out = tmp_path / "site"
    rc = build_exports.main(["--data", str(data), "--out", str(out)])
    assert rc == 0
    got = (out / "projects.ndjson").read_text(encoding="utf-8")
    assert json.loads(got.strip())["full_name"] == "a/b"


def test_real_payload_exports_cleanly(tmp_path):
    rc = build_exports.main(["--out", str(tmp_path)])
    assert rc == 0
    lines = (tmp_path / "projects.ndjson").read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 40           # v7 relevance-gated dataset (junk purged: ~62 real BCI repos)
    json.loads(lines[0]); json.loads(lines[-1])
