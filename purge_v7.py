#!/usr/bin/env python3
"""One-off: apply the v7 relevance engine to the committed radar.json so the
live site is clean immediately (the scheduled pipeline will maintain it going
forward). Re-scores every project, drops those below the BRS gate, attaches
brs/tier/ledger/facets to the survivors, and rebuilds the derived aggregates."""
import json, os, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
import relevance, domain, radar  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
RADAR = os.path.join(ROOT, "data", "radar.json")
FEED = os.path.join(ROOT, "feed.xml")
BADGE = os.path.join(ROOT, "data", "badge-ecosystem.json")
HISTORY = os.path.join(ROOT, "data", "history.json")

d = json.load(open(RADAR, encoding="utf-8"))
projects = d.get("projects", [])
kept, dropped = [], []
for p in projects:
    rel = relevance.score(p)
    if rel["decision"] != "keep":
        dropped.append(p.get("full_name"))
        continue
    p["brs"] = rel["brs"]
    p["relevance_tier"] = rel["tier"]
    p["relevance_ledger"] = rel["ledger"]
    p["facets"] = domain.facets(p)
    kept.append(p)

print(f"kept {len(kept)} / {len(projects)} · dropped {len(dropped)}")

# rebuild derived aggregates over the survivors
builders = radar.build_builders(kept)
coverage = domain.coverage_matrix(kept)
stdgraph = domain.standards_graph(kept)


def _count(flag):
    return sum(1 for p in kept if p.get(flag))


healthy = [p for p in kept if isinstance(p.get("signals"), dict)]
counts = dict(d.get("counts", {}))
counts.update({
    "total": len(kept),
    "active_30d": _count("active"),
    "new": _count("is_new"),
    "rising": _count("rising"),
    "falling": _count("falling"),
    "community_active_30d": _count("community_active"),
    "builders": len(builders),
    "foundation_checked": sum(1 for p in kept if isinstance(p.get("foundation"), dict)),
    "interop_tagged": sum(1 for p in kept if p.get("interop")),
})
if healthy:
    counts["health_strong"] = sum(1 for p in healthy if p["signals"].get("overall", 0) >= 80)
    ov = sorted(p["signals"].get("overall", 0) for p in healthy)
    counts["health_median"] = ov[len(ov) // 2]

d["version"] = 5
d["projects"] = kept
d["builders"] = builders
d["counts"] = counts
d["coverage_matrix"] = coverage
d["standards_graph"] = stdgraph
d["ecosystem_count"] = sum(1 for p in kept if p.get("ecosystem"))
d["criteria"] = (
    "Public, non-archived, non-fork repositories that clear the BCI Relevance Engine (v7): "
    "a scored, auditable gate that keeps a repo only when the weight of BCI-specific evidence "
    "— acquisition modality, field standard, named hardware, explicit BCI topic or paradigm — "
    "exceeds generic-ML signals. Each kept repo carries its signed evidence ledger."
)
meth = dict(d.get("methodology", {}))
meth.update({"relevance_version": "7.0", "domain_version": "7.0"})
d["methodology"] = meth

json.dump(d, open(RADAR, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(RADAR, "a").write("")  # ensure file handle flushed
with open(RADAR, "a", encoding="utf-8") as fh:
    fh.write("\n")

# regenerate the RSS feed and the ecosystem badge from survivors
now = datetime.now(timezone.utc)
with open(FEED, "w", encoding="utf-8") as fh:
    fh.write(radar.build_feed(kept, now))

if os.path.exists(BADGE):
    b = json.load(open(BADGE, encoding="utf-8"))
    b["message"] = str(len(kept))
    json.dump(b, open(BADGE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(BADGE, "a", encoding="utf-8").write("\n")

# prune stale repos from history stars maps (cosmetic, keeps history honest)
if os.path.exists(HISTORY):
    h = json.load(open(HISTORY, encoding="utf-8"))
    keep_names = {p["full_name"] for p in kept}
    for snap in h.get("snapshots", []):
        sm = snap.get("stars")
        if isinstance(sm, dict):
            snap["stars"] = {k: v for k, v in sm.items() if k in keep_names}
    json.dump(h, open(HISTORY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(HISTORY, "a", encoding="utf-8").write("\n")

print("radar.json, feed.xml, badge, history rewritten")
print("coverage stages:", coverage["stage_totals"], "| standards:", stdgraph["n_standards"],
      "| interop edges:", stdgraph["interop_edges"])
