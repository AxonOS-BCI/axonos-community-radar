#!/usr/bin/env bash
# Create the radar's label taxonomy so issues land on the Roadmap board already
# structured. Idempotent: `gh label create --force` updates colour/description if
# a label already exists. Requires the GitHub CLI (`gh auth login` first).
#
#   bash scripts/setup_labels.sh
#
set -euo pipefail
REPO="AxonOS-BCI/axonos-community-radar"

label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force; }

echo "Creating labels on $REPO …"

# ── type ──────────────────────────────────────────────────────────────────
label "type:feature"   "a2eeef" "New capability or improvement"
label "type:bug"       "d73a4a" "Something is wrong"
label "type:chore"     "cfd3d7" "Maintenance, refactor, deps"

# ── area ──────────────────────────────────────────────────────────────────
label "area:engine"    "5319e7" "Relevance / domain scoring"
label "area:ui"        "1d76db" "Site, map, cards, charts"
label "area:data"      "0e8a16" "Enrichment, history, exports"
label "area:infra"     "555555" "CI/CD, hosting, API"
label "area:docs"      "c5def5" "Methodology, roadmap, docs"

# ── priority ──────────────────────────────────────────────────────────────
label "priority:high"  "b60205" "Blocks real use"
label "priority:med"   "fbca04" "Clear value"
label "priority:low"   "0e8a16" "Nice to have"

# ── workflow ──────────────────────────────────────────────────────────────
label "needs-triage"   "ededed" "Awaiting first review"
label "good-first-issue" "7057ff" "Approachable entry point"
label "help-wanted"    "008672" "Extra attention wanted"

echo "Done. Tip: in the Project board, add a Fields → Single-select 'Area' and"
echo "'Priority' and a workflow that sets them from these labels automatically."
