#!/usr/bin/env bash
set -Eeuo pipefail

export GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

if [ -z "${GH_TOKEN:-}" ]; then
  echo "FAIL: GH_TOKEN/GITHUB_TOKEN is empty"
  exit 1
fi

REPO="${GITHUB_REPOSITORY:-AxonOS-BCI/axonos-community-radar}"

TOPICS=(
  bci
  brain-computer-interface
  neurotechnology
  neurotech
  neural-interface
  neural-signal-processing
  eeg
  emg
  neuroscience
  signal-processing
  embedded-rust
  no-std
  real-time
  microkernel
  formal-verification
  privacy
  cryptography
  zero-copy
)

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

RAW="$TMP/repos.tsv"
DEDUP="$TMP/repos.dedup.tsv"
BODY="$TMP/radar.md"

: > "$RAW"

echo "== Radar repo: $REPO =="

for T in "${TOPICS[@]}"; do
  echo "Scanning topic:$T"

  gh api -X GET search/repositories \
    -f q="topic:$T archived:false fork:false" \
    -f sort=updated \
    -f order=desc \
    -f per_page=20 \
    --jq '.items[]? | [
      .full_name,
      (.stargazers_count | tostring),
      (.forks_count | tostring),
      (.language // ""),
      .pushed_at,
      .html_url,
      ((.description // "") | gsub("\t";" ") | gsub("\n";" "))
    ] | @tsv' >> "$RAW" || {
      echo "WARN: search failed for topic:$T"
      continue
    }
done

if [ ! -s "$RAW" ]; then
  echo "WARN: no repositories found"
  echo -e "AxonOS-org/axonos-standard\t0\t0\tMarkdown\t$(date -u +"%Y-%m-%dT%H:%M:%SZ")\thttps://github.com/AxonOS-org/axonos-standard\tFallback AxonOS standard repository" > "$RAW"
fi

awk -F '\t' '!seen[$1]++' "$RAW" \
  | sort -t $'\t' -k2,2nr \
  > "$DEDUP"

NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

cat > "$BODY" <<EOF2
# AxonOS Community Radar

Updated: \`$NOW\`

This is a review queue, not an auto-spam bot.

## Daily action rule

- Star: max 3–5 relevant repositories.
- Follow: max 1–2 real maintainers.
- PR/Issue: only if there is concrete technical value.
- Rocket reaction: only after manual review of a real release.
- No generic comments.

## Repository candidates

| # | Repo | Stars | Forks | Language | Pushed | Notes |
|---:|---|---:|---:|---|---|---|
EOF2

i=0
while IFS=$'\t' read -r FULL STARS FORKS LANG PUSHED URL DESC; do
  i=$((i+1))
  SAFE_DESC="$(printf '%s' "$DESC" | sed 's/|/\\|/g')"

  printf '| %s | [%s](%s) | %s | %s | %s | %s | %s |\n' \
    "$i" "$FULL" "$URL" "$STARS" "$FORKS" "$LANG" "$PUSHED" "$SAFE_DESC" >> "$BODY"
done < "$DEDUP"

cat >> "$BODY" <<'EOF2'

## Recent release candidates

EOF2

checked=0
while IFS=$'\t' read -r FULL STARS FORKS LANG PUSHED URL DESC; do
  [ "$checked" -ge 40 ] && break
  checked=$((checked+1))

  latest="$(gh api "/repos/$FULL/releases/latest" 2>/dev/null || true)"
  [ -z "$latest" ] && continue

  rel_url="$(printf '%s' "$latest" | jq -r '.html_url // empty')"
  rel_name="$(printf '%s' "$latest" | jq -r '.name // .tag_name // empty')"
  rel_date="$(printf '%s' "$latest" | jq -r '.published_at // empty')"

  [ -z "$rel_url" ] && continue

  echo "- [$FULL — $rel_name]($rel_url) — $rel_date" >> "$BODY"
done < "$DEDUP"

cat >> "$BODY" <<'EOF2'

## High-signal AxonOS contribution angles

- deterministic test vectors
- README scope corrections
- Rust `no_std` compatibility notes
- CI hardening
- reproducibility checks
- privacy/security boundary documentation
- protocol conformance examples
- benchmark fixtures
- issue triage with concrete reproduction steps

## Low-signal actions to avoid

- generic "great project" comments
- mass 🚀 reactions
- mass following maintainers
- opening issues just to advertise AxonOS
EOF2

gh label create radar \
  --repo "$REPO" \
  --description "AxonOS community radar" \
  --color "8A6F35" >/dev/null 2>&1 || true

ISSUE_NUMBER="$(
  gh issue list \
    --repo "$REPO" \
    --state open \
    --json number,title \
    --jq '.[] | select(.title=="AxonOS Community Radar") | .number' \
    | head -n1
)"

if [ -z "$ISSUE_NUMBER" ]; then
  gh issue create \
    --repo "$REPO" \
    --title "AxonOS Community Radar" \
    --body-file "$BODY" \
    --label "radar"
else
  gh issue edit "$ISSUE_NUMBER" \
    --repo "$REPO" \
    --body-file "$BODY"
fi

echo "OK: radar issue updated"
