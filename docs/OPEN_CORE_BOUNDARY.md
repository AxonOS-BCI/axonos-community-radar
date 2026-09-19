# The open-core boundary

What is public, what is not, and why — stated once so it can be argued with.

This document exists because "open core" is usually a marketing word. Here it is
a line drawn through a running system, and the useful question is not whether
the line exists but **whether the public side is enough to check the private
side's claims**. That is the test this page is written against.

Last reviewed against the repository at v16.5.0.

---

## Public, and staying public

Everything below is published without an account, a key, a rate limit or a
paywall, under the repository's licence. Moving any of it behind payment would
be manufacturing scarcity out of something already given away, and this project
does not do that.

| | Where |
|:--|:--|
| Every project in the map, with its score | [`data/radar.json`](../data/radar.json) |
| The evidence behind every score — each signal, its points, its reason | `relevance_ledger`, in the same payload |
| The rule that combines them | [`axonos-brs`](https://github.com/AxonOS-org/axonos-brs), a separate open crate |
| The near misses, with what each lacked | [`data/considered.json`](../data/considered.json) |
| Every historical snapshot | [`data/history.json`](../data/history.json) |
| Star and score trajectories | [`data/trajectory.json`](../data/trajectory.json) |
| The schemas | [`data/radar.schema.json`](../data/radar.schema.json) |
| The public API and its manifest | [`docs/API.md`](API.md), `data/api.json` |
| RSS: the main feed and the signal feeds | `feed.xml`, `feeds/*.xml` |
| Methodology | [`docs/METHODOLOGY.md`](METHODOLOGY.md) |
| Health and freshness | `data/status.json`, `data/build.json` |
| Payment and pricing contracts | [`data/payment.json`](../data/payment.json), [`data/commercial.json`](../data/commercial.json) |
| The full git history of all of it | this repository |

**The data is free and so is its past.** A dataset you can only see the present
of is not auditable, so the history stays open too.

---

## Not public

| | Why |
|:--|:--|
| The scanner implementation | It holds the API credentials and the search strategy. Publishing it publishes the token handling and hands a gaming manual to anyone who wants one. |
| The discovery and seed strategy | Same reason. Which corners of GitHub get searched, and in what order, is the part most easily gamed once known. |
| The scheduler | Operational. |
| Customer computation, watchlists, credentials | Other people's data. |

---

## What that costs the reader, stated plainly

An independent party **can** recompute any published score from the published
evidence using the published rule. That is the claim this project makes and it
holds.

An independent party **cannot** reproduce the candidate universe — the set of
repositories that were looked at in the first place. The scanner is private, so
what it chose to examine is taken on trust. No amount of published evidence
closes that gap, and no wording here should be read as closing it.

What partly compensates: [`data/considered.json`](../data/considered.json)
publishes the near misses with their scores and their shortfalls, and the funnel
publishes how many repositories were scanned, how many cleared, how many were
force-included as ecosystem anchors and how many fell below the listing floor.
That makes the *shape* of the selection checkable even where the selection
itself is not. It is not the same thing as reproducibility and is not offered
as such.

---

## Where commercial value comes from

Not from taking anything away. From work that does not exist in the public data:

- scanning a list the public scan does not cover, on a cadence agreed for it
- delivery — alerts by mail or webhook, when something changes
- a request quota against an authenticated key
- exports and slices shaped for someone's own pipeline

Prices and entitlements are in [`data/commercial.json`](../data/commercial.json)
and are checked against the rendered page by CI, because a price that lives only
in markup drifts — this one already did, three times.

---

## What is not built

Stated here rather than implied by silence. There is **no billing backend**: no
order state machine, no automated provisioning, no quota enforcement service, no
tenant isolation layer, no API key store. Payment is a Dogecoin transaction and
an email; provisioning is manual.

Anything on the public pages that would require such a system to exist would be
a claim about software that has not been written, and this project treats that
as the same defect as a wrong number.
