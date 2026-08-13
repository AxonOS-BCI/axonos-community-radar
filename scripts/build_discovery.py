#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Denis Yermakou <connect@axonos.org>
# Part of The AxonOS Project — https://axonos.org
"""Make the map legible to machines that are not browsers.

The map publishes eighteen JSON files, an RSS feed, a schema and a scored
ledger per project. A person arriving through a link finds all of it. A crawler
finds the front page, and an aggregator that indexes open-source ecosystems
finds nothing at all, because nothing here says what the data is or where it
starts.

That is not a marketing gap. It is the same defect this project keeps finding
in itself: a property that exists and cannot be discovered is close enough to a
property that does not exist. The scoring rule was public for months and the
README mentioned it zero times; this is that, one layer out.

## What this generates, and what each is for

**`robots.txt`** — states that crawling is welcome and points at the sitemap.
Absent, a crawler applies its own defaults, and some of those defaults are "do
not index JSON".

**`sitemap.xml`** — every page and every published dataset, with the timestamp
the payload itself carries. Not a list of URLs a human typed: the entries are
derived from what the deploy actually produced, so a file that stops being
published stops being advertised.

**`.well-known/dataset.json`** — a DCAT-shaped description at the location
data-catalogue harvesters look first. This is the one that reaches aggregators
rather than search engines.

**`schema.org` graph** — the site is already a `WebSite`; it is also a
`Dataset` with a licence, a maintainer, a distribution list and a temporal
coverage. A search engine that understands the first will show a name; one that
understands the second can say what the data contains and when it was measured.

## What this deliberately does not do

It does not claim rankings, popularity or authority for any project on the map.
The structured data describes **the dataset**, not the projects inside it. A
`Dataset` that asserted quality judgements about third-party repositories would
be putting this project's opinion into somebody else's search result, and the
map's whole argument is that inclusion is discovery rather than endorsement.

It adds no tracking, no analytics and no third-party script. Discoverability
and surveillance are different things that are usually shipped together.

    python3 build_discovery.py --out _site
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

SITE = "https://axonos-bci.github.io/axonos-community-radar"

#: Pages, with why each exists. A sitemap that lists URLs without knowing what
#: they are cannot set a sensible change frequency, and a wrong frequency is
#: worse than none: it teaches a crawler to come back at the wrong time.
PAGES = [
    ("", "hourly", "1.0", "the live map"),
    ("/report.html", "hourly", "0.9", "the field report, rebuilt every scan"),
    ("/stats.html", "hourly", "0.7", "aggregate statistics"),
    ("/support.html", "monthly", "0.3", "how to support the work"),
]

#: Datasets, with the shape a harvester needs. Only files that are actually
#: published: this list is checked against the built site and an entry with no
#: file fails the build rather than advertising a 404.
DATASETS = [
    ("data/radar.json", "application/json",
     "Every scored project, with the evidence ledger that produced its score"),
    ("data/considered.json", "application/json",
     "Projects that fell below the gate, with their scores and what each lacked"),
    ("data/history.json", "application/json",
     "Snapshot history: star counts and activity over time"),
    ("data/trajectory.json", "application/json",
     "Per-project movement across snapshots"),
    ("data/ecosystem.json", "application/json",
     "Dependency relationships between mapped projects"),
    ("data/radar.schema.json", "application/schema+json",
     "JSON Schema for the payload, versioned"),
    ("feed.xml", "application/rss+xml",
     "New projects, as they enter the map"),
]


def robots() -> str:
    return f"""# The AxonOS Radar welcomes crawling.
#
# Everything here is public GitHub metadata, recompiled every three hours and
# published with the rule that produced it. There is nothing to hide behind a
# disallow, and a crawler that applies its own defaults may skip the JSON,
# which is the part worth having.
#
# © 2026 Denis Yermakou — The AxonOS Project · https://axonos.org

User-agent: *
Allow: /

# The datasets, explicitly. Some crawlers exclude JSON unless told otherwise.
Allow: /data/
Allow: /feeds/
Allow: /.well-known/

# No crawl-delay. The site is static, served from a CDN, and a delay would
# only make an index staler than the data it describes.

Sitemap: {SITE}/sitemap.xml
"""


def sitemap(built: pathlib.Path) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # The payload's own timestamp, not the build's. A sitemap that says the data
    # changed when the build ran is claiming freshness the data may not have.
    stamp = now
    try:
        payload = json.loads((built / "data" / "radar.json").read_text(encoding="utf-8"))
        stamp = (payload.get("generated_at") or now)[:10]
    except Exception:  # noqa: BLE001
        pass

    rows = []
    for path, freq, prio, _why in PAGES:
        rows.append(
            f"  <url>\n"
            f"    <loc>{escape(SITE + path)}</loc>\n"
            f"    <lastmod>{stamp}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{prio}</priority>\n"
            f"  </url>"
        )
    for path, _mime, _desc in DATASETS:
        rows.append(
            f"  <url>\n"
            f"    <loc>{escape(f'{SITE}/{path}')}</loc>\n"
            f"    <lastmod>{stamp}</lastmod>\n"
            f"    <changefreq>hourly</changefreq>\n"
            f"    <priority>0.8</priority>\n"
            f"  </url>"
        )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def dataset_descriptor(built: pathlib.Path) -> dict:
    """DCAT-shaped, at the path catalogue harvesters probe."""
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    projects = 0
    try:
        payload = json.loads((built / "data" / "radar.json").read_text(encoding="utf-8"))
        stamp = payload.get("generated_at", stamp)
        projects = len(payload.get("projects", []))
    except Exception:  # noqa: BLE001
        pass

    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "The AxonOS Radar — open brain-computer interface projects",
        "description": (
            "A scored map of open-source brain-computer interface work, "
            "recompiled every three hours from public GitHub metadata. Each "
            "project carries the evidence ledger that produced its score, and "
            "the scoring rule is published as a separate Rust crate, so any "
            "score here can be recomputed from public data. Inclusion is "
            "discovery, not endorsement."
        ),
        "url": SITE,
        "identifier": f"{SITE}/data/radar.json",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isAccessibleForFree": True,
        "dateModified": stamp,
        "creator": {
            "@type": "Person",
            "name": "Denis Yermakou",
            "email": "connect@axonos.org",
            "url": "https://axonos.org",
        },
        "publisher": {
            "@type": "Organization",
            "name": "The AxonOS Project",
            "url": "https://axonos.org",
        },
        "keywords": [
            "brain-computer interface", "BCI", "neurotechnology",
            "EEG", "open source", "electrophysiology", "neural interface",
        ],
        "variableMeasured": [
            {"@type": "PropertyValue", "name": "brs",
             "description": "Relevance score, 0-100, produced by the published rule"},
            {"@type": "PropertyValue", "name": "relevance_ledger",
             "description": "The evidence that produced the score, item by item"},
            {"@type": "PropertyValue", "name": "stars_delta_7d",
             "description": "Change in stars over seven days"},
        ],
        "measurementTechnique": (
            "Public GitHub metadata, scored by axonos-brs, an open Rust crate. "
            "No private data, no estimation, no human curation of the score."
        ),
        "distribution": [
            {
                "@type": "DataDownload",
                "encodingFormat": mime,
                "contentUrl": f"{SITE}/{path}",
                "description": desc,
            }
            for path, mime, desc in DATASETS
        ],
        # A count is a fact about this snapshot, so it carries the snapshot's
        # own timestamp rather than being asserted in the abstract.
        "size": f"{projects} projects as of {stamp[:10]}",
        "citation": (
            "Yermakou, D. (2026). The AxonOS Radar. The AxonOS Project. "
            f"{SITE}"
        ),
    }


def build(out: pathlib.Path) -> int:
    if not out.is_dir():
        print(f"::error::{out} does not exist; run this after the site is assembled")
        return 1

    missing = [p for p, _m, _d in DATASETS if not (out / p).exists()]
    if missing:
        # Advertising a file that is not there sends a harvester to a 404 and
        # teaches it that this catalogue is unreliable. Better to fail here.
        print(f"::error::these datasets are advertised and not built: {missing}")
        return 1

    (out / "robots.txt").write_text(robots(), encoding="utf-8")
    (out / "sitemap.xml").write_text(sitemap(out), encoding="utf-8")
    wk = out / ".well-known"
    wk.mkdir(exist_ok=True)
    (wk / "dataset.json").write_text(
        json.dumps(dataset_descriptor(out), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    n = len(PAGES) + len(DATASETS)
    print(f"  robots.txt · sitemap.xml ({n} entries) · .well-known/dataset.json")
    print(f"  {len(DATASETS)} datasets described, all verified present")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="_site", help="the assembled site directory")
    args = ap.parse_args()
    return build(pathlib.Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
