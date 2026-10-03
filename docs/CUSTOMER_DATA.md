# Customer data, and how Radar PRO is delivered

The public map and a paying customer's data are different things. The map
publishes public GitHub metadata; this file is about everything a purchase
adds. The short version is on [terms.html](../terms.html).

## What the customer owns

The watchlist and field watches they define, the briefs and digests prepared
for them, and every customer-specific dataset in their delivery repository.

## What AxonOS keeps, and why

Only what the service, security and the law require: billing records for as
long as tax law requires, the correspondence needed to serve the customer, and
the watchlist while the subscription runs.

## The delivery repository

| Question | Answer |
|:--|:--|
| Who owns it? | AxonOS creates one private repository per customer |
| Who is admin? | AxonOS |
| Who gets access? | The GitHub accounts the customer names, invited with the read role |
| Can the customer export everything? | Yes: `git clone` copies every file and its full history |
| After cancellation? | AxonOS stops writing and, as the customer chooses, transfers the repository to them or deletes it; the watchlist leaves the engine within thirty days |
| If AxonOS is unavailable? | Nothing is delivered; the repository stays readable on GitHub, and every missed day extends the term |
| If GitHub's API fails? | That delivery does not happen; the gap is noted and the term extended, as the contract states |
| If the repository is deleted? | It is recreated on request; history the customer did not clone cannot be restored |
| GitHub Enterprise? | Not supported; delivery is on github.com |
| Webhooks? | GitHub-native: added to the repository by AxonOS at the customer's request, sent by GitHub to the customer's endpoint. AxonOS does not proxy webhook traffic |

## Isolation between customers

Each customer has their own repository, and a delivery is generated from one
watchlist and written to that customer's repository only; no file is shared
between customers. The delivery code runs in the private engine, not in this
repository, so this repository cannot test that isolation — and does not claim
to.

## Privacy, export and deletion

Requests for a copy, a correction or a deletion go to connect@axonos.org. No
standard data processing agreement is published; a customer's own is reviewed
on request.
