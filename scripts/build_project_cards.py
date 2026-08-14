#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Denis Yermakou <connect@axonos.org>
# Part of The AxonOS Project — https://axonos.org
"""The AxonOS project cards, with a stage nobody types.

The stage badges on the front page were written by hand into the HTML, and by
the time anyone looked they were wrong: the radar was labelled Beta at version
14.0.0 after three months of running every three hours, the conformance suite
was Beta while four RFCs' vectors were enforcing its rules in another
repository's CI, and five cards pointed at the string "1" instead of a URL.

Changing the labels would have fixed today and guaranteed the same drift in a
month, because the defect is not the labels. It is that a fact about a
repository was being asserted somewhere the repository cannot reach.

## What decides the stage

Two things a repository publishes about itself, and nothing else:

**The version in its manifest.** Below 0.1.0 is early, below 1.0.0 is beta,
at or above 1.0.0 is stable. That is what semantic versioning means, and a
project claiming otherwise is arguing with its own manifest.

**Whether a release object exists.** A tag is not a release. A repository with
no release has published nothing a consumer can depend on, whatever its version
says, so it cannot be beyond `active` no matter how mature the code is.

Nothing here reads a curated list of opinions. If a stage looks wrong, the
answer is to cut a release or bump a version, which is the honest way to change
what a page says about you.

## Why "beta" for the kernel is correct and stays

The kernel is at 0.4.1 with forty-three machine-checked proofs and no hardware
measurements: the validation repository is empty and says so, the 972 µs figure
is observed without published traces, and the reference firmware documents a
stubbed wrap-tracking extension. A page calling that shipped would be telling a
reader it is ready to depend on.

This project spent a week removing three claims of exactly that shape. The
generator will not produce one, and no override exists to force it, because an
override is how the hand-written labels started.

    python3 build_project_cards.py --write index.html
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

#: The repositories, with the area each belongs to and the sentence that says
#: what it is. Descriptions are here because they are editorial and a
#: repository description is a different thing written for a different reader;
#: stage, version and URL are never here, because those are facts the
#: repository owns.
PROJECTS: list[dict] = [
    {"repo": "AxonOS-org/axonos-kernel", "area": "Kernel",
     "text": "Real-time no_std kernel: deterministic scheduler, SPSC queues, "
             "monotonic time, capability model."},
    {"repo": "AxonOS-org/axonos-consent", "area": "Consent & Protocol",
     "text": "The consent state machine, with six machine-checked proofs over "
             "grant, revocation and expiry."},
    {"repo": "AxonOS-org/axonos-protocol", "area": "Consent & Protocol",
     "text": "The wire format: one encoding, decoded byte-identically in five "
             "languages."},
    {"repo": "AxonOS-org/axonos-signal-pipeline", "area": "Signal & ML",
     "text": "Deterministic fixed-point conditioning. Same input, same bytes, "
             "any machine."},
    {"repo": "AxonOS-org/axonos-standard", "area": "Standard",
     "text": "The specification the RFCs are tracked against."},
    {"repo": "AxonOS-org/axonos-conformance", "area": "Standard",
     "text": "Byte-exact vectors for RFC-0005, 0006, 0008 and 0009, re-derived "
             "from published constants rather than transcribed."},
    {"repo": "AxonOS-BCI/axonos-community-radar", "area": "Community",
     "text": "This radar: an auditable map of the open BCI field, rescored "
             "every three hours."},
    {"repo": "AxonOS-org/axonos-brs", "area": "Community",
     "text": "The scoring rule itself, published so any score on the radar can "
             "be recomputed from public data."},
    {"repo": "AxonOS-org/axonos-hal", "area": "Kernel",
     "text": "The contract with silicon: a timing budget that refuses, and "
             "re-closes at every operating point."},
    {"repo": "AxonOS-org/axonos-rfcs", "area": "Standard",
     "text": "Nine RFCs. The two in draft say why they are draft."},
    {"repo": "AxonOS-org/ask-axonos", "area": "Community",
     "text": "Ask anything about AxonOS. Every answer carries its source, or "
             "says it does not have one."},
]

#: Stage from version, and the reason each boundary is where it is.
#:
#: These are semantic versioning's own meanings rather than a scale invented
#: here. A project that dislikes its stage can change its version, which is the
#: honest way to change what a page says about it.
def stage_for(version: str | None, has_release: bool) -> tuple[str, str, str]:
    """Return (css class, label, why)."""
    if not version:
        return ("st-planned", "Planned",
                "no manifest version could be read")
    try:
        parts = tuple(int(p) for p in re.split(r"[.\-+]", version)[:3])
    except ValueError:
        return ("st-planned", "Planned", f"version {version!r} is not a number")

    if not has_release:
        # A tag is not a release, and a repository with no release object has
        # published nothing anyone can depend on. This project's own release
        # rule says the same thing about its own pushes.
        return ("st-active", "Active",
                f"version {version}, and no release published yet")
    if parts >= (1, 0, 0):
        return ("st-shipped", "Shipped", f"version {version}, released")
    if parts >= (0, 1, 0):
        return ("st-beta", "Beta", f"version {version}, released, pre-1.0")
    return ("st-early", "Early", f"version {version}")


class RateLimited(Exception):
    """The API refused, which is not the same as the file being absent.

    The first version returned None for both, so a rate limit looked exactly
    like a repository that states no version — and the generator reported two
    projects as Planned that had stated theirs correctly. One of them had read
    fine ten minutes earlier, which is the tell: a file does not stop existing
    between runs, and a quota does.
    """


def fetch(path: str) -> dict | list | None:
    req = urllib.request.Request(
        f"{API}/{path.lstrip('/')}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "axonos-radar-cards",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # The file is genuinely not there. That is an answer.
            return None
        if e.code in (403, 429):
            raise RateLimited(f"{e.code} on {path}") from e
        raise RateLimited(f"HTTP {e.code} on {path}") from e
    except Exception as e:  # noqa: BLE001
        raise RateLimited(f"{type(e).__name__} on {path}") from e


def read_version(repo: str) -> str | None:
    """The version a repository states about itself.

    Tried in the order a maintainer would expect it to be authoritative:
    VERSION, then Cargo.toml, then package.json. A repository with none of
    these has not stated a version, and the card says so rather than guessing.
    """
    # Read through raw.githubusercontent first: it does not consume the API
    # quota, and eleven repositories at four calls each was enough to exhaust
    # it mid-run. The API is the fallback, for a private repository where raw
    # is not reachable.
    for path, pattern in (
        ("VERSION", r"^\s*([0-9]+\.[0-9]+\.[0-9]+)"),
        ("Cargo.toml", r'^\s*version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"'),
        ("package.json", r'"version"\s*:\s*"([0-9]+\.[0-9]+\.[0-9]+)"'),
        # CITATION.cff is a legitimate place to state a version and two
        # repositories here use it as their only one: the conformance suite and
        # the RFCs ship no manifest because neither is a package. The first
        # version of this reader knew three files and called both Planned,
        # which is a fact about the reader rather than about them.
        #
        # Anchored on ^version: so cff-version, which is the file format's
        # version and not the project's, cannot be mistaken for it.
        ("CITATION.cff", r'^version:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?'),
    ):
        body = None
        try:
            req = urllib.request.Request(
                f"https://raw.githubusercontent.com/{repo}/main/{path}",
                headers={"User-Agent": "axonos-radar-cards"},
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise RateLimited(f"raw {e.code} on {repo}/{path}") from e
        except Exception as e:  # noqa: BLE001
            raise RateLimited(f"raw {type(e).__name__} on {repo}/{path}") from e
        if body is None:
            continue
        m = re.search(pattern, body, re.M)
        if m:
            return m.group(1)
    return None


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def build() -> tuple[str, list[str]]:
    cards, notes = [], []
    for p in PROJECTS:
        repo = p["repo"]
        try:
            version = read_version(repo)
            rel = fetch(f"repos/{repo}/releases/latest")
        except RateLimited as e:
            # Stop rather than continue. Continuing produces a page where some
            # cards are facts and others are quota exhaustion, and nothing on
            # the page says which is which.
            print(f"::error::the API stopped answering at {repo}: {e}")
            print("  Nothing written. With gh installed, run:")
            print("    GITHUB_TOKEN=$(gh auth token) python3 scripts/build_project_cards.py --write index.html")
            raise
        has_release = isinstance(rel, dict) and "tag_name" in rel
        cls, label, why = stage_for(version, has_release)
        notes.append(f"{repo.split('/')[-1]:<26} {label:<8} {why}")

        # The version is shown on the card. A stage without the number behind it
        # is an assertion; with it, a reader can check the claim in one click.
        badge = f'<span class="ax-ver">{esc(version)}</span>' if version else ""
        cards.append(
            f'        <a class="ax-card" href="https://github.com/{esc(repo)}" '
            f'target="_blank" rel="noopener">'
            f'<div class="ax-top">'
            f'<span class="ax-stage {cls}">{label}</span>'
            f'<span class="ax-area">{esc(p["area"])}</span>{badge}</div>'
            f'<h3>{esc(repo.split("/")[-1])}</h3>'
            f'<p>{esc(p["text"])}</p></a>'
        )
    return "\n".join(cards), notes


def write(path: pathlib.Path, cards: str) -> int:
    t = path.read_text(encoding="utf-8")
    start = t.find('<div class="ax-grid">')
    if start < 0:
        print("::error::the ax-grid block is not in this file")
        return 1
    open_at = t.index(">", start) + 1
    depth, i = 1, open_at
    while depth and i < len(t):
        nxt_open = t.find("<div", i)
        nxt_close = t.find("</div>", i)
        if nxt_close < 0:
            print("::error::the ax-grid block never closes")
            return 1
        if 0 <= nxt_open < nxt_close:
            depth += 1
            i = nxt_open + 4
        else:
            depth -= 1
            i = nxt_close + 6
    end = i - 6

    new = t[:open_at] + "\n" + cards + "\n    " + t[end:]
    path.write_text(new, encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", metavar="HTML")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        cards, notes = build()
    except RateLimited:
        return 2
    print(f"  {len(PROJECTS)} projects, stage derived from version and release:")
    for n in notes:
        print(f"    {n}")

    unresolved = sum(1 for n in notes if "no manifest version" in n)
    if unresolved:
        # A card that cannot read its repository is a card asserting nothing,
        # and publishing a page full of those is worse than not rebuilding.
        print(f"::error::{unresolved} repositories did not answer; refusing to "
              f"write a page that would mark them Planned by accident")
        return 1

    if args.dry_run or not args.write:
        return 0
    return write(pathlib.Path(args.write), cards)


if __name__ == "__main__":
    sys.exit(main())

