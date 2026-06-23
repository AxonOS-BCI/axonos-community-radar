#!/usr/bin/env bash
set -Eeuo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"

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
)

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

RAW="$TMP/repos.tsv"
DEDUP="$TMP/repos.dedup.tsv"
BODY="$TMP/radar.md"

: > "$RAW"

for T in "${TOPICS[@]}"; do
  gh api -X GET search/repositories \
    -f q="topic:$T archived:false fork:false" \
    -f sort=updated \
    -f order=desc \
    -f per_page=25 \
    --jq '.items[]? | [
      .full_name,
      (.stargazers_count | tostring),
      (.forks_count | tostring),
      (.language // ""),
      .pushed_at,
      .html_url,
      ((.description // "") | gsub("\t";" ") | gsub("\n";" "))
    ] | @tsv' >> "$RAW" || true
done

awk -F '\t' '!seen[$1]++' "$RAW" \
  | sort -t $'\t' -k2,2nr \
  > "$DEDUP"

NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

cat > "$BODY" <<EOF2
# AxonOS Community Radar

Updated: \`$NOW\`

This issue is a review queue, not an auto-spam bot.

## Recommended actions

- Star relevant repositories after review.
- Watch projects that are strategically important.
- Add useful issues or PRs only when there is clear technical value.
- Use 🚀 reaction only for releases that are genuinely relevant to AxonOS.
- Avoid generic comments.

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

## AxonOS contribution angles

High-signal contribution types:

- deterministic test vectors
- README scope corrections
- Rust `no_std` compatibility notes
- CI hardening
- reproducibility checks
- security boundary documentation
- protocol conformance examples
- benchmark fixtures
- issue triage with concrete reproduction steps

Low-signal actions to avoid:

- generic "great project" comments
- repeated 🚀 reactions without review
- mass following maintainers
- opening issues only to advertise AxonOS
EOF2

ISSUE_NUMBER="$(
  gh issue list \
    --state open \
    --json number,title \
    --jq '.[] | select(.title=="AxonOS Community Radar") | .number' \
    | head -n1
)"

if [ -z "$ISSUE_NUMBER" ]; then
  gh issue create \
    --title "AxonOS Community Radar" \
    --body-file "$BODY" \
    --label "radar" || gh issue create \
      --title "AxonOS Community Radar" \
      --body-file "$BODY"
else
  gh issue edit "$ISSUE_NUMBER" --body-file "$BODY"
fi
