#!/usr/bin/env python3
"""Build the Signals feed from the published radar data (v9.0 "Signals").

The map already *knows* what changed — every scan the engine marks projects
new / rising / cooling from measured deltas. This module turns those flags
into a durable, subscribable alert surface:

  data/signals.json   machine-readable alerts with stable ids
  feeds/signals.xml   RSS — everything
  feeds/new.xml       RSS — newly discovered BCI projects
  feeds/rising.xml    RSS — projects gaining momentum (7-day star velocity)

Deploy-time and pure: reads only the already-published dataset, writes only
into the site artifact, commits nothing. Signal ids are deterministic
(kind + project + ISO week), so a signal keeps one identity for the week it
is true and feed readers never see duplicates.

    python3 scripts/build_signals.py --out _site
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

SITE = "https://axonos-bci.github.io/axonos-community-radar"

KIND_META = {
    "new":    ("New on the radar",   "A new open BCI project was discovered and scored"),
    "rising": ("Rising",             "Measured 7-day star velocity — momentum, not opinion"),
    "cooling": ("Cooling",           "Losing velocity — visible before you build on it"),
}


def _iso_week(ts: str) -> str:
    try:
        d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        d = datetime.now(timezone.utc)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _sig_id(kind: str, full_name: str, week: str) -> str:
    return hashlib.sha256(f"{kind}:{full_name}:{week}".encode()).hexdigest()[:16]


def _project_ref(p: dict) -> dict:
    return {
        "full_name": p.get("full_name"),
        "url": p.get("html_url") or f"https://github.com/{p.get('full_name')}",
        "brs": p.get("brs"),
        "relevance_tier": p.get("relevance_tier"),
        "category": p.get("category"),
        "modality": (p.get("facets") or {}).get("modality", []),
        "stars": p.get("stars"),
    }


def build_signals(radar: dict, first_seen: dict) -> dict:
    generated = radar.get("generated_at") or datetime.now(timezone.utc).isoformat()
    week = _iso_week(generated)
    signals = []
    for p in radar.get("projects", []):
        name = p.get("full_name")
        if not name:
            continue
        if p.get("is_new"):
            signals.append({
                "id": _sig_id("new", name, week), "kind": "new",
                "project": _project_ref(p),
                "evidence": {"first_seen": first_seen.get(name)},
                "detected_at": generated,
            })
        if p.get("rising"):
            signals.append({
                "id": _sig_id("rising", name, week), "kind": "rising",
                "project": _project_ref(p),
                "evidence": {"stars_delta_7d": p.get("stars_delta_7d")},
                "detected_at": generated,
            })
        if p.get("falling"):
            signals.append({
                "id": _sig_id("cooling", name, week), "kind": "cooling",
                "project": _project_ref(p),
                "evidence": {"stars_delta_7d": p.get("stars_delta_7d")},
                "detected_at": generated,
            })
    order = {"new": 0, "rising": 1, "cooling": 2}
    signals.sort(key=lambda s: (order[s["kind"]],
                                -(s["evidence"].get("stars_delta_7d") or 0),
                                s["project"]["full_name"] or ""))
    return {
        "version": 1,
        "generated_at": generated,
        "week": week,
        "counts": {k: sum(1 for s in signals if s["kind"] == k) for k in KIND_META},
        "signals": signals,
    }


def _rss(title: str, desc: str, path: str, items: list) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0"><channel>',
           f"<title>{escape(title)}</title>",
           f"<link>{SITE}/</link>",
           f"<description>{escape(desc)}</description>"]
    for s in items:
        p = s["project"]
        kind_h, _ = KIND_META[s["kind"]]
        ev = s["evidence"]
        if ev.get("stars_delta_7d"):
            detail = "+{} stars in 7 days".format(ev["stars_delta_7d"])
        elif ev.get("first_seen"):
            detail = "first seen " + str(ev["first_seen"])[:10]
        else:
            detail = ""
        brs = " · BRS {}".format(p["brs"]) if isinstance(p.get("brs"), (int, float)) else ""
        title = "[{}] {}".format(kind_h, p["full_name"])
        desc = "{}{} · {} · {}".format(kind_h, brs, detail, p.get("category") or "").strip(" ·")
        out += ["<item>",
                "<title>{}</title>".format(escape(title)),
                "<link>{}</link>".format(escape(p["url"])),
                '<guid isPermaLink="false">{}</guid>'.format(s["id"]),
                "<description>{}</description>".format(escape(desc)),
                "</item>"]
    out.append("</channel></rss>")
    return "\n".join(out) + "\n"


def write_all(payload: dict, out_dir: Path) -> None:
    data_dir = out_dir / "data"
    feeds_dir = out_dir / "feeds"
    data_dir.mkdir(parents=True, exist_ok=True)
    feeds_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "signals.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sig = payload["signals"]
    (feeds_dir / "signals.xml").write_text(_rss(
        "AxonOS Radar — Signals", "New, rising, and cooling across the open BCI field",
        "feeds/signals.xml", sig), encoding="utf-8")
    (feeds_dir / "new.xml").write_text(_rss(
        "AxonOS Radar — New BCI projects", "Newly discovered and scored open BCI projects",
        "feeds/new.xml", [s for s in sig if s["kind"] == "new"]), encoding="utf-8")
    (feeds_dir / "rising.xml").write_text(_rss(
        "AxonOS Radar — Rising", "Projects gaining measured 7-day momentum",
        "feeds/rising.xml", [s for s in sig if s["kind"] == "rising"]), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    ap.add_argument("--radar", default="data/radar.json")
    ap.add_argument("--first-seen", dest="first_seen", default="data/first_seen.json")
    a = ap.parse_args()
    radar = json.loads(Path(a.radar).read_text(encoding="utf-8"))
    try:
        first_seen = json.loads(Path(a.first_seen).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — first_seen is enrichment, not a dependency
        first_seen = {}
    payload = build_signals(radar, first_seen)
    write_all(payload, Path(a.out))
    c = payload["counts"]
    print(f"signals ok: {c['new']} new, {c['rising']} rising, {c['cooling']} cooling "
          f"-> {a.out}/data/signals.json + feeds/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
