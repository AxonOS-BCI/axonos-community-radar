# Decisions

Why some things here are the way they are. These explanations used to live as
long comments inside `.github/workflows/ci.yml`, which turned a file that should
read as an executable contract into an incident archive. The reasons still
matter — a maintainer who deletes a guard without knowing what it caught will
reintroduce the defect — but they belong somewhere a person reads on purpose.

Each entry is short, names what went wrong, and says what enforces the decision
now.

---

## D-1 · `data/payment.json` is the only root for the wallet address

**What happened.** The funding gate read the canonical address from
`data/ecosystem-registry.json` while `tests/test_support_contract.py` read it
from `data/payment.json`. Two files independently holding an address for
irreversible transfers, agreeing only because nothing had yet made them
disagree.

**Decision.** `payment.json` is the root. The registry entry names it as its
source and carries a copy for convenience only.

**Enforced by.** `scripts/gates/check_funding.py` — fails if the copy drifts,
and checks Base58Check on the address, its presence in `support.html`,
`assets/app.js` and `.github/FUNDING.yml`, and the absence of any other
D-address in those files.

---

## D-2 · The QR is decoded, never described

**What happened.** A check named for the QR read the `alt` attribute in the
HTML, and the mutation test that "proved" it edited that same attribute. Nothing
had ever opened the image. A replaced SVG encoding another wallet would have
passed every check while the page looked correct.

**Decision.** The image is decoded and its payload compared with
`payment.json`. A decode that cannot run is a failure, not a skip, because a
silently skipped decode is exactly how the gap survived.

**Enforced by.** `tests/test_qr_integrity.py`, with the decoder pinned in
`requirements-ci.txt`.

---

## D-3 · Claim checks are anchored, not substrings

**What happened.** A gate forbade the sentence "Every project here cleared a
scored gate". The corrected sentence — "**Almost** every project here cleared a
scored gate" — contains it, so the fix failed the check written to enforce it.

**Decision.** Patterns carry `(?<!almost )` and similar. A qualifier in front of
a claim changes the claim; a checker that cannot see the qualifier is reading
letters rather than meaning.

**Enforced by.** `scripts/gates/check_anchor_disclosure.py`, and
`tests/test_gates.py` asserts the qualified sentence passes *and* the bare one
fails.

---

## D-4 · A disclosure existing is not the contradiction being absent

**What happened.** The same gate checked that "ecosystem anchors" appeared
somewhere in the README. It did — three hundred lines below an opening sentence
claiming the opposite. The check passed.

**Decision.** Both directions are checked: the disclosure must be present and
the contradicting claims must be absent.

**Enforced by.** `scripts/gates/check_anchor_disclosure.py`.

---

## D-5 · No live count is frozen into prose

**What happened.** The README carried "tracked 120+ BCI projects" on a static
badge, three lines above a live endpoint badge measuring the same thing, and
"31 near misses" in a diagram. The map is rescored every three hours.

**Decision.** Counts live in the badge endpoint and `data/status.json`. Prose
names no figure that moves.

**Enforced by.** `scripts/gates/check_frozen_counts.py`.

---

## D-6 · `cancel-in-progress: true` on the deploy

**What happened.** With it `false`, GitHub holds one running and one pending run
per group and cancels the *pending* one when a third arrives. The triggers
cluster within thirty minutes, so a stuck head held the group and everything
behind it died queued. The site served a fifteen-day-old build while every check
reported success.

**Decision.** Newest deploy wins. And the delivery script cancels nothing: a
later version of it cancelled unfinished runs before dispatching its own, which
killed the run carrying the commit it had just pushed.

**Enforced by.** `.github/workflows/pages.yml`, and by the health monitor
returning non-zero on the unhealthy path — which it did not originally do.

---

## D-7 · A timestamp in the future is a fault, not freshness

**What happened.** `validate_payload.py` accepted a payload dated 2099. Staleness
is measured as `now − generated_at`, so a forward-dated payload is permanently
fresh and the freeze monitor can never fire — the fifteen-day outage again, by a
different route.

**Decision.** Refused beyond five minutes of clock skew, and reported as its own
fault on both the scan clock and the deploy clock.

**Enforced by.** `scripts/validate_payload.py`, `scripts/health_check.py`,
`tests/test_future_timestamps.py`.

---

## D-8 · Policy logic lives in `scripts/gates/`, not in YAML

**What happened.** Two real defects passed through logic embedded in workflow
strings: a duplicate `run:` key that stopped the file parsing — so a release
produced no result of any kind while appearing to fail its proofs — and D-4
above. Neither was findable locally, because there was nothing to run.

**Decision.** YAML orchestrates. Policy is versioned source with a `check()`
function returning a list of problems, and a test for every failure path.

**Enforced by.** `tests/test_gates.py`, which asserts each gate is importable,
documented, clean on the committed tree, and *fails* on a mutated copy of it.
