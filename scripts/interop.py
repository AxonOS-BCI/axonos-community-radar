#!/usr/bin/env python3
"""Interop detection for the AxonOS Radar (v6, "Solid Ground").

Answers one practical question the BCI field keeps asking: *"which projects
speak which protocols, formats and hardware?"* Detection is deliberately
simple and auditable: word-boundary matching of a committed vocabulary
(data/interop-vocab.json) against the metadata the scan already has —
topics, description, homepage. Zero extra API calls, fully deterministic,
and honestly labelled as heuristic in the Methodology tab.

Design rules:
- Patterns match as whole words (``\\b``) so ``unity`` never fires inside
  ``community`` and ``mne`` never fires inside ``mnemonic``.
- Topics are matched as whole tokens too (a topic is already a word).
- The vocabulary file is the single source of truth; the validator and the
  documentation-coverage gate both read it, so a tag cannot silently exist
  in one layer and not the others.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "data" / "interop-vocab.json"

MAX_TAGS_PER_PROJECT = 8      # sanity cap, enforced here and in the validator
MAX_TAG_LEN = 24


def load_vocab(path: Path = VOCAB_PATH) -> list[dict]:
    """Load and sanity-check the vocabulary. Raises on a malformed file so a
    broken vocab fails the scan loudly instead of silently detecting nothing."""
    data = json.loads(path.read_text(encoding="utf-8"))
    tags = data.get("tags")
    if not isinstance(tags, list) or not tags:
        raise ValueError("interop-vocab.json: 'tags' must be a non-empty list")
    seen: set[str] = set()
    for t in tags:
        tag = t.get("tag")
        if not (isinstance(tag, str) and 0 < len(tag) <= MAX_TAG_LEN
                and re.fullmatch(r"[a-z0-9][a-z0-9-]*", tag)):
            raise ValueError(f"interop-vocab.json: bad tag {tag!r}")
        if tag in seen:
            raise ValueError(f"interop-vocab.json: duplicate tag {tag!r}")
        seen.add(tag)
        pats = t.get("patterns")
        if not (isinstance(pats, list) and pats
                and all(isinstance(p, str) and p for p in pats)):
            raise ValueError(f"interop-vocab.json: tag {tag!r} needs patterns")
        if not isinstance(t.get("label"), str) or not t["label"]:
            raise ValueError(f"interop-vocab.json: tag {tag!r} needs a label")
    return tags


_VOCAB_CACHE: list[dict] | None = None
_MATCHERS_CACHE: list[tuple[str, re.Pattern]] | None = None


def _matchers() -> list[tuple[str, re.Pattern]]:
    """Compile one alternation regex per tag, word-boundary anchored."""
    global _VOCAB_CACHE, _MATCHERS_CACHE
    if _MATCHERS_CACHE is None:
        _VOCAB_CACHE = load_vocab()
        out: list[tuple[str, re.Pattern]] = []
        for t in _VOCAB_CACHE:
            alt = "|".join(f"(?:{p})" for p in t["patterns"])
            out.append((t["tag"], re.compile(rf"\b(?:{alt})\b", re.IGNORECASE)))
        _MATCHERS_CACHE = out
    return _MATCHERS_CACHE


def known_tags() -> set[str]:
    """The set of valid tags — used by validate_payload as the contract."""
    return {tag for tag, _ in _matchers()}


def detect(project: dict) -> list[str]:
    """Return the sorted interop tags detected for one project."""
    parts = []
    topics = project.get("topics")
    if isinstance(topics, list):
        parts.append(" ".join(str(t) for t in topics))
    for f in ("description", "homepage"):
        v = project.get(f)
        if isinstance(v, str):
            parts.append(v)
    hay = " ".join(parts)
    if not hay.strip():
        return []
    found = [tag for tag, rx in _matchers() if rx.search(hay)]
    return sorted(found)[:MAX_TAGS_PER_PROJECT]


def annotate_interop(projects: list[dict]) -> int:
    """Annotate every project in place with p['interop']; return how many
    projects carry at least one tag (for counts.interop_tagged)."""
    tagged = 0
    for p in projects:
        if not isinstance(p, dict):
            continue
        tags = detect(p)
        p["interop"] = tags
        if tags:
            tagged += 1
    return tagged


if __name__ == "__main__":  # tiny self-check, mirrors the CI gate style
    v = load_vocab()
    print(f"interop vocab ok: {len(v)} tags, "
          f"{sum(len(t['patterns']) for t in v)} patterns")
