#!/usr/bin/env python3
"""
AxonOS Radar — data refresher (v3).

Honest, hardened data pipeline:
  * Relevance filtering — keep a repo only if it carries a core BCI/neuro topic, or a
    context topic plus a neuro keyword. Generic VPN/password/embedded repos are dropped.
  * Deterministic scoring — recency from the current 6-hour snapshot slot, so unchanged
    projects keep the same score between refreshes.
  * Partial-failure safe — if more than FAIL_RATIO of topic queries fail, abort WITHOUT
    writing, so the last-good committed data is preserved (no half-empty radar).
  * Durable identity — `first_seen` is tracked in a dedicated data/first_seen.json that
    survives corruption of radar.json (bootstrapped from radar.json on first migration),
    so a bad read can never flag the whole ecosystem as "new".
  * Rate-limit aware, response-size capped, timezone-robust, self-validating.
  * Emits an RSS feed (XML-correct escaping) of the newest projects. No auto-engagement.
"""
import base64  # noqa: F401  (kept for parity; not required at runtime)
import json
import os
import re
import functools
import sys
import time
import math
import urllib.parse
import urllib.request
import urllib.error
from xml.sax.saxutils import escape as _xescape
from datetime import datetime, timezone
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "data", "seeds.json")
OUT = os.path.join(ROOT, "data", "radar.json")
FIRST_SEEN = os.path.join(ROOT, "data", "first_seen.json")
FEED = os.path.join(ROOT, "feed.xml")

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
SELF_REPO = os.environ.get("GITHUB_REPOSITORY", "AxonOS-BCI/axonos-community-radar").lower()
SITE = "https://axonos-bci.github.io/axonos-community-radar/"

MAX_RESPONSE_BYTES = 8 * 1024 * 1024   # cap a single API response
FAIL_RATIO = 0.25                       # abort if more than this fraction of topics fail
FIRST_SEEN_TTL_DAYS = 400               # bound the first_seen log

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "AxonOS-Community-Radar"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def _is_safe_github_url(url, min_segments=2) -> bool:
    """Exact-host check: https://github.com/<...> with >= min_segments path parts
    (repos need 2: owner/repo). Blocks look-alike hosts like github.com.evil.com."""
    if not isinstance(url, str):
        return False
    try:
        q = urllib.parse.urlparse(url)
        segs = [s for s in q.path.split("/") if s]
        return q.scheme == "https" and q.netloc == "github.com" and len(segs) >= min_segments
    except Exception:
        return False
    try:
        q = urllib.parse.urlparse(url)
        return q.scheme == "https" and q.netloc == "github.com" and q.path.count("/") >= 2
    except Exception:
        return False


def xesc(s):
    """XML-correct escaping for element content and attribute values."""
    return _xescape(str(s if s is not None else ""), {'"': "&quot;", "'": "&apos;"})


def gh_json(url, retries=3):
    """GET JSON with rate-limit backoff and a response-size cap."""
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError("API response exceeds size cap")
                time.sleep(0.7)  # respectful spacing — intentionally serial
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("unexpected API response shape")
                return data
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                reset = exc.headers.get("X-RateLimit-Reset")
                if exc.headers.get("X-RateLimit-Remaining") == "0" and reset:
                    wait = min(max(int(reset) - int(time.time()), 5), 90)
                    print(f"  rate limited — sleeping {wait}s")
                    time.sleep(wait)
                    continue
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise exc
    return {"items": []}


def load_seeds():
    with open(SEEDS, encoding="utf-8") as fh:
        return json.load(fh)


def load_first_seen(snap_iso):
    """
    Durable first_seen map. Order of resolution:
      1. data/first_seen.json (source of truth).
      2. If absent, bootstrap from radar.json's existing first_seen values (migration).
      3. If radar.json is present but corrupt, abort (do NOT reset — that would flood NEW).
    """
    if os.path.exists(FIRST_SEEN):
        try:
            with open(FIRST_SEEN, encoding="utf-8") as fh:
                d = json.load(fh)
            if isinstance(d, dict):
                return {k: v for k, v in d.items() if isinstance(v, str)}
        except Exception as exc:  # noqa: BLE001
            print(f"CRITICAL: first_seen.json is corrupt ({exc}); aborting to avoid NEW flood.")
            sys.exit(1)
    # bootstrap from radar.json if it exists
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as fh:
                prev = json.load(fh)
            return {p["full_name"]: p.get("first_seen") or snap_iso
                    for p in prev.get("projects", []) if p.get("full_name")}
        except Exception as exc:  # noqa: BLE001
            print(f"CRITICAL: radar.json present but unreadable ({exc}); aborting to preserve identity.")
            sys.exit(1)
    return {}


def save_first_seen(mapping, current_names, snap):
    """Persist, pruning stale entries (not current and older than the TTL)."""
    pruned = {}
    for fn, iso in mapping.items():
        if fn in current_names:
            pruned[fn] = iso
            continue
        try:
            if (snap - datetime.fromisoformat(iso)).days <= FIRST_SEEN_TTL_DAYS:
                pruned[fn] = iso
        except Exception:  # noqa: BLE001
            pruned[fn] = iso
    with open(FIRST_SEEN, "w", encoding="utf-8") as fh:
        json.dump(pruned, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def repo_text(repo):
    return " ".join([
        " ".join(repo.get("topics") or []), repo.get("language") or "",
        repo.get("full_name") or "", repo.get("description") or "",
    ]).lower()


@functools.lru_cache(maxsize=8)
def _kw_pattern(keywords):
    """Word-start-anchored keyword regex (prefix match). Prevents short keywords like
    'erp'/'lfp' from matching inside unrelated words ('interpreter', 'cleverpad')."""
    return re.compile(r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")", re.IGNORECASE)


def is_relevant(repo, core, context, keywords):
    topics = {t.lower() for t in (repo.get("topics") or [])}
    if topics & core:
        return True
    if topics & context and _kw_pattern(tuple(keywords)).search(repo_text(repo)):
        return True
    return False


CATEGORY_PRIORITY = ["Protocols & OS", "Privacy & Security", "Decoding & ML",
                     "Signal Processing", "Hardware & Acquisition", "Real-time & Embedded"]


def categorise(repo, categories):
    """Weighted categorisation: a keyword in the repo NAME is the strongest
    signal, an exact topic match is strong, a description hit is weak. Ties are
    broken toward the more specific category (CATEGORY_PRIORITY order) so that,
    e.g., a repo literally named '*-protocol' lands in Protocols & OS rather than
    a generic bucket it merely brushes against."""
    name = (repo.get("full_name") or "").split("/")[-1].lower()
    topics = set(t.lower() for t in (repo.get("topics") or []))
    topic_tokens = set()
    for t in topics:
        topic_tokens.add(t)
        topic_tokens.update(t.split("-"))
    desc = (repo.get("description") or "").lower()
    scores = {}
    for cat, kws in categories.items():
        s = 0
        for kw in kws:
            kwl = kw.lower()
            if re.search(r"(^|[-_/])" + re.escape(kwl) + r"($|[-_/])", name):
                s += 4
            if kwl in topics or kwl in topic_tokens:
                s += 3
            elif kwl in desc:
                s += 1
        scores[cat] = s
    best, best_s = "Other", 0
    for cat in CATEGORY_PRIORITY:
        if scores.get(cat, 0) > best_s:
            best, best_s = cat, scores[cat]
    for cat, s in scores.items():
        if cat not in CATEGORY_PRIORITY and s > best_s:
            best, best_s = cat, s
    return best


def snapshot_now():
    now = datetime.now(timezone.utc)
    slot = (now.hour // 6) * 6
    return now, now.replace(hour=slot, minute=0, second=0, microsecond=0)


def days_since(iso, snap):
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, (snap - dt).days)
    except Exception:  # noqa: BLE001
        return 9999


def build_feed(projects, generated):
    items = sorted([p for p in projects if p.get("first_seen")],
                   key=lambda p: p["first_seen"], reverse=True)[:25]
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>',
             "<title>AxonOS Radar — new projects</title>",
             f"<link>{xesc(SITE)}</link>",
             "<description>Newly discovered open brain-computer-interface projects.</description>",
             f"<lastBuildDate>{xesc(format_datetime(generated))}</lastBuildDate>"]
    for p in items:
        try:
            pub = format_datetime(datetime.fromisoformat(p["first_seen"]))
        except Exception:  # noqa: BLE001
            pub = format_datetime(generated)
        url = p.get("html_url") or SITE
        parts.append("<item>"
                     f"<title>{xesc(p['full_name'])}</title>"
                     f"<link>{xesc(url)}</link>"
                     f'<guid isPermaLink="true">{xesc(url)}</guid>'
                     f"<category>{xesc(p.get('category') or 'Other')}</category>"
                     f"<pubDate>{xesc(pub)}</pubDate>"
                     f"<description>{xesc(p.get('description') or p.get('category') or '')}</description>"
                     "</item>")
    parts.append("</channel></rss>")
    return "\n".join(parts) + "\n"


def validate(payload, cap):
    p = payload.get("projects", [])
    assert isinstance(p, list), "projects must be a list"
    assert len(p) <= cap, f"too many projects: {len(p)} > {cap}"
    assert payload["counts"]["total"] >= 0, "negative total"
    for r in p:
        assert r.get("full_name"), "project missing full_name"
        assert _is_safe_github_url(r.get("html_url")), f"suspicious url: {r.get('html_url')!r}"
        assert r.get("category"), "project missing category"


# ─────────────────────────────────────────────────────────────────────────────
# v3 enrichment: evidence tiers, matched signals, quality flags, builders,
# star-velocity (rising), and AxonOS relevance. All additive — every v2 field is
# preserved so older consumers keep working. Inclusion is not endorsement.
# ─────────────────────────────────────────────────────────────────────────────

HISTORY = os.path.join(ROOT, "data", "history.json")
HISTORY_RETENTION_DAYS = 45
HISTORY_MAX_REPOS = 200

EXPLICIT_BCI_TOPICS = {
    "bci", "bmi", "brain-computer-interface", "brain-machine-interface",
    "brain-computer-interfaces", "brain-machine-interfaces", "brain-computer",
    "neurotechnology", "neurotech",
}
NEURAL_SIGNAL_TOPICS = {
    "eeg", "ecog", "meg", "emg", "eog", "neural-signal", "neural-signals",
    "neurofeedback", "electroencephalography", "lfp", "spikes", "spike-sorting",
}
STRONG_NEURAL_KW = {
    "eeg", "ecog", "meg", "bci", "brain-computer", "neural", "cortical", "neuro",
    "electroenceph", "motor-imagery", "p300", "ssvep", "neuron", "spike",
}
AXON_DIMS = {
    "acquisition": {"ads1299", "openbci", "electrode", "amplifier", "acquisition", "adc", "daq", "8-channel"},
    "signal_pipeline": {"filter", "fir", "iir", "notch", "band-pass", "feature", "dsp", "preprocessing", "csp", "artifact"},
    "protocol": {"lsl", "lab-streaming", "stream", "protocol", "websocket", "mqtt", "osc", "wire"},
    "privacy": {"privacy", "consent", "encryption", "gdpr", "secure", "differential-privacy"},
    "runtime": {"real-time", "rtos", "no-std", "embedded", "deterministic", "firmware", "cortex"},
    "sdk": {"sdk", "api", "library", "framework", "bindings"},
}


def _matched_signals(repo, core, context, keywords):
    tset = {t.lower() for t in (repo.get("topics") or [])}
    relevant = core | context | EXPLICIT_BCI_TOPICS | NEURAL_SIGNAL_TOPICS
    matched_topics = sorted(tset & relevant)
    txt = repo_text(repo)
    matched_keywords = sorted({k for k in keywords if re.search(r"\b" + re.escape(k), txt)})
    return matched_topics, matched_keywords, tset


def evidence_for(repo, core, context, keywords):
    """Return (evidence_tier, inclusion_reason, matched_topics, matched_keywords)."""
    matched_topics, matched_keywords, tset = _matched_signals(repo, core, context, keywords)
    explicit = sorted(tset & EXPLICIT_BCI_TOPICS)
    neural = sorted(tset & NEURAL_SIGNAL_TOPICS)
    strong = [k for k in matched_keywords if k in STRONG_NEURAL_KW]
    if explicit:
        tier = "L3_EXPLICIT_BCI"
        reason = f"Explicit BCI topic ({', '.join(explicit[:3])})."
    elif neural or strong:
        tier = "L2_NEURAL_SIGNAL"
        sig = ", ".join((neural or strong)[:2])
        reason = f"Neural-signal topic or keyword ({sig})."
    elif (tset & context) and matched_keywords:
        tier = "L1_CONTEXT_PLUS_NEURO"
        ctx = ", ".join(sorted(tset & context)[:2])
        reason = f"Context topic {ctx} plus neuro keyword ({', '.join(matched_keywords[:2])})."
    else:
        tier = "L0_WEAK_ADJACENT"
        reason = "Weak adjacent signal; flagged for review."
    return tier, reason, matched_topics, matched_keywords


def quality_flags_for(repo, tier):
    return {
        "possible_false_positive": tier == "L0_WEAK_ADJACENT",
        "low_metadata": not (repo.get("description") or "").strip() or not (repo.get("topics") or []),
        "missing_license": not bool(repo.get("has_license")),
        "no_recent_activity": int(repo.get("days_since_push") or 9999) > 180,
    }


def axon_relevance_for(repo):
    txt = repo_text(repo)
    return {dim: round(min(1.0, sum(1 for k in kws if k in txt) * 0.34), 2)
            for dim, kws in AXON_DIMS.items()}


def load_history():
    if os.path.exists(HISTORY):
        try:
            with open(HISTORY, encoding="utf-8") as fh:
                h = json.load(fh)
            if isinstance(h, dict) and isinstance(h.get("snapshots"), list):
                return h
            raise ValueError("unexpected shape")
        except Exception as exc:  # noqa: BLE001
            if os.environ.get("RADAR_REBUILD_HISTORY") == "1":
                print(f"WARN: history.json corrupt; rebuilding ({exc}).")
                return {"version": 1, "snapshots": []}
            print(f"CRITICAL: history.json corrupt ({exc}); aborting "
                  "(set RADAR_REBUILD_HISTORY=1 to reset).")
            sys.exit(1)
    return {"version": 1, "snapshots": []}


def _stars_delta(history, full_name, current_stars, snap, days):
    cutoff = snap.timestamp() - days * 86400
    best = None
    for snp in history.get("snapshots", []):
        try:
            t = datetime.fromisoformat(snp["snapshot_at"]).timestamp()
        except Exception:  # noqa: BLE001
            continue
        if t <= cutoff and full_name in (snp.get("stars") or {}):
            if best is None or t > best[0]:
                best = (t, snp["stars"][full_name])
    return 0 if best is None else current_stars - int(best[1])


def update_history(history, projects, snap, snap_iso):
    top = sorted(projects, key=lambda p: int(p.get("stars") or 0), reverse=True)[:HISTORY_MAX_REPOS]
    stars_map = {p["full_name"]: int(p.get("stars") or 0) for p in top}
    meta = {
        "total": len(projects),
        "active_30d": sum(1 for p in projects if p.get("active")),
        "new": sum(1 for p in projects if p.get("is_new")),
        "rising": sum(1 for p in projects if p.get("rising")),
        "total_stars": sum(int(p.get("stars") or 0) for p in projects),
    }
    snaps = [s for s in history.get("snapshots", []) if s.get("snapshot_at") != snap_iso]
    snaps.append({"snapshot_at": snap_iso, "meta": meta, "stars": stars_map})
    cutoff = snap.timestamp() - HISTORY_RETENTION_DAYS * 86400

    def keep(s):
        try:
            return datetime.fromisoformat(s["snapshot_at"]).timestamp() >= cutoff
        except Exception:  # noqa: BLE001
            return False

    snaps = [s for s in snaps if keep(s)]
    snaps.sort(key=lambda s: s["snapshot_at"])
    return {"version": 1, "snapshots": snaps}


def build_builders(projects, min_projects=2):
    by = {}
    for p in projects:
        owner = (p.get("full_name") or "/").split("/")[0]
        b = by.setdefault(owner, {
            "owner": owner, "html_url": f"https://github.com/{owner}",
            "project_count": 0, "total_stars": 0, "active_projects_30d": 0,
            "_cats": {}, "_langs": {}, "projects": [],
        })
        b["project_count"] += 1
        b["total_stars"] += int(p.get("stars") or 0)
        if p.get("active"):
            b["active_projects_30d"] += 1
        if p.get("category"):
            b["_cats"][p["category"]] = b["_cats"].get(p["category"], 0) + 1
        if p.get("language"):
            b["_langs"][p["language"]] = b["_langs"].get(p["language"], 0) + 1
        b["projects"].append(p["full_name"])
    builders = []
    for b in by.values():
        if b["project_count"] < min_projects:
            continue
        b["top_categories"] = [c for c, _ in sorted(b["_cats"].items(), key=lambda x: -x[1])[:3]]
        b["top_languages"] = [lng for lng, _ in sorted(b["_langs"].items(), key=lambda x: -x[1])[:3]]
        del b["_cats"], b["_langs"]
        builders.append(b)
    builders.sort(key=lambda x: (x["total_stars"], x["project_count"]), reverse=True)
    return builders


def enrich_v3(projects, seeds, snap, history):
    """Add v3 fields to each project in place; return (builders, counts)."""
    core = {t.lower() for t in seeds.get("core_topics", [])}
    context = {t.lower() for t in seeds.get("context_topics", [])}
    keywords = [k.lower() for k in seeds.get("neuro_keywords", [])]
    for p in projects:
        owner, _, repo = (p.get("full_name") or "/").partition("/")
        p["owner"], p["repo"] = owner, repo
        if "has_license" not in p:
            p["has_license"] = bool(p.get("license"))
        p.setdefault("license", p.get("license"))
        tier, reason, mt, mk = evidence_for(p, core, context, keywords)
        p["evidence_tier"], p["inclusion_reason"] = tier, reason
        p["matched_topics"], p["matched_keywords"] = mt, mk
        p["quality_flags"] = quality_flags_for(p, tier)
        stars = int(p.get("stars") or 0)
        p["stars_delta_7d"] = _stars_delta(history, p["full_name"], stars, snap, 7)
        p["stars_delta_30d"] = _stars_delta(history, p["full_name"], stars, snap, 30)
        p["rising"] = p["stars_delta_7d"] >= max(2, math.ceil(stars * 0.05))
        p["axon_relevance"] = axon_relevance_for(p)
    builders = build_builders(projects)
    counts = {
        "total": len(projects),
        "active_30d": sum(1 for p in projects if p.get("active")),
        "new": sum(1 for p in projects if p.get("is_new")),
        "rising": sum(1 for p in projects if p.get("rising")),
        "builders": len(builders),
    }
    return builders, counts


def main():
    seeds = load_seeds()
    core = {t.lower() for t in seeds.get("core_topics", [])}
    context = {t.lower() for t in seeds.get("context_topics", [])}
    keywords = [k.lower() for k in seeds.get("neuro_keywords", [])]
    categories = seeds.get("categories", {})
    topics = seeds.get("core_topics", []) + seeds.get("context_topics", [])
    max_per_topic = int(seeds.get("max_per_topic", 25))
    max_projects = int(seeds.get("max_projects", 120))
    min_stars = int(seeds.get("min_stars", 3))
    new_days = int(seeds.get("new_window_days", 7))
    excl_owners = {o.lower() for o in seeds.get("exclude_owners", [])}
    excl_repos = {r.lower() for r in seeds.get("exclude_repos", [])}

    now, snap = snapshot_now()
    snap_iso = snap.isoformat()
    fseen = load_first_seen(snap_iso)

    repos, seen_lc, scanned, dropped, failed = {}, set(), 0, 0, []
    for topic in topics:
        q = f"topic:{topic} archived:false fork:false"
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "updated", "order": "desc", "per_page": str(max_per_topic)})
        print(f"Scanning topic:{topic}")
        try:
            data = gh_json(url)
        except Exception as exc:  # noqa: BLE001  (resilience: collect, decide after loop)
            print(f"  WARN: search failed for topic:{topic}: {type(exc).__name__}: {exc}")
            failed.append(topic)
            continue
        for item in data.get("items", []):
            scanned += 1
            fn = item.get("full_name")
            key = (fn or "").lower()
            if not fn or key == SELF_REPO or key in seen_lc:
                continue
            seen_lc.add(key)
            if fn.split("/")[0].lower() in excl_owners or fn.lower() in excl_repos:
                continue
            if int(item.get("stargazers_count") or 0) < min_stars:
                continue
            if not is_relevant(item, core, context, keywords):
                dropped += 1
                continue
            repos[fn] = {
                "full_name": fn, "html_url": item.get("html_url"),
                "description": (item.get("description") or "").strip()[:240],
                "stars": int(item.get("stargazers_count") or 0),
                "forks": int(item.get("forks_count") or 0),
                "language": item.get("language") or "",
                "pushed_at": item.get("pushed_at") or "",
                "topics": (item.get("topics") or [])[:12],
                "license": (item.get("license") or {}).get("spdx_id"),
                "has_license": bool((item.get("license") or {}).get("spdx_id")
                                    and (item.get("license") or {}).get("spdx_id") != "NOASSERTION"),
            }

    # Partial-failure safeguard: preserve last-good data rather than publishing a half-empty radar.
    if topics and len(failed) / len(topics) > FAIL_RATIO:
        print(f"CRITICAL: {len(failed)}/{len(topics)} topic queries failed "
              f"(> {int(FAIL_RATIO*100)}%). Aborting WITHOUT writing to preserve committed data.")
        sys.exit(1)

    out = []
    for r in repos.values():
        days = days_since(r["pushed_at"], snap)
        first_seen = fseen.get(r["full_name"]) or snap_iso
        fseen[r["full_name"]] = first_seen
        try:
            is_new = (snap - datetime.fromisoformat(first_seen)).days <= new_days
        except Exception:  # noqa: BLE001
            is_new = False
        r.update({"days_since_push": days, "active": days <= 30,
                  "category": categorise(r, categories), "first_seen": first_seen,
                  "is_new": is_new,
                  "_score": round(math.log10(r["stars"] + 1) * 10 + max(0, 60 - days) * 0.5, 3)})
        out.append(r)

    out.sort(key=lambda x: x["_score"], reverse=True)
    out = out[:max_projects]

    history = load_history()
    builders, counts = enrich_v3(out, seeds, snap, history)

    payload = {
        "version": 3, "generated_at": now.replace(microsecond=0).isoformat(),
        "snapshot_at": snap_iso, "source": "GitHub topic search (public)",
        "criteria": ("Public, non-archived, non-fork repositories that carry a core BCI/neuro "
                     "topic, or a context topic plus a neuro keyword. Ranked by recency (from the "
                     "6-hour snapshot slot) and stars. Categorisation and evidence tiers are heuristic."),
        "refresh": "every 6 hours via GitHub Actions", "min_stars": min_stars,
        "topics_failed": len(failed), "topics": topics,
        "methodology": {"scoring_version": "3.0", "category_version": "3.0",
                        "evidence_version": "3.0", "docs": "docs/METHODOLOGY.md",
                        "note": "Inclusion is not endorsement; AxonOS is not boosted."},
        "counts": counts,
        "projects": out,
        "builders": builders,
    }
    validate(payload, max_projects)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    history = update_history(history, out, snap, snap_iso)
    with open(HISTORY, "w", encoding="utf-8") as fh:
        json.dump(history, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    save_first_seen(fseen, set(repos.keys()), snap)
    with open(FEED, "w", encoding="utf-8") as fh:
        fh.write(build_feed(out, now))
    print(f"Wrote {len(out)} v3 projects + {len(builders)} builders (scanned {scanned}, "
          f"dropped {dropped} off-topic, {len(failed)} topics failed, {counts['active_30d']} active, "
          f"{counts['new']} new, {counts['rising']} rising). history + first_seen + feed updated.")

if __name__ == "__main__":
    main()
