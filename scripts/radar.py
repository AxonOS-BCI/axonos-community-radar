#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY", "AxonOS-BCI/axonos-community-radar")

if not TOKEN:
    print("FAIL: GH_TOKEN/GITHUB_TOKEN is empty", file=sys.stderr)
    sys.exit(1)

TOPICS = [
    "bci",
    "brain-computer-interface",
    "neurotechnology",
    "neurotech",
    "neural-interface",
    "neural-signal-processing",
    "eeg",
    "emg",
    "neuroscience",
    "signal-processing",
    "embedded-rust",
    "no-std",
    "real-time",
    "microkernel",
    "formal-verification",
    "privacy",
    "cryptography",
    "zero-copy",
    "rust",
    "cortex-m",
]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "AxonOS-Community-Radar",
}

def gh_json(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

repos = {}

for topic in TOPICS:
    query = f"topic:{topic} archived:false fork:false"
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
        "q": query,
        "sort": "updated",
        "order": "desc",
        "per_page": "20",
    })

    print(f"Scanning topic:{topic}")

    try:
        data = gh_json(url)
    except Exception as exc:
        print(f"WARN: search failed for topic:{topic}: {exc}")
        continue

    for item in data.get("items", []):
        full_name = item.get("full_name")
        if not full_name:
            continue

        repos[full_name] = {
            "full_name": full_name,
            "stars": int(item.get("stargazers_count") or 0),
            "forks": int(item.get("forks_count") or 0),
            "language": item.get("language") or "",
            "pushed_at": item.get("pushed_at") or "",
            "url": item.get("html_url") or "",
            "description": (item.get("description") or "").replace("\n", " ").replace("|", "\\|"),
        }

items = sorted(repos.values(), key=lambda r: r["stars"], reverse=True)

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

body = []
body.append("# AxonOS Community Radar")
body.append("")
body.append(f"Updated: `{now}`")
body.append("")
body.append("This is a review queue, not an auto-spam bot.")
body.append("")
body.append("## Daily action rule")
body.append("")
body.append("- Star: max 3–5 relevant repositories.")
body.append("- Follow: max 1–2 real maintainers.")
body.append("- PR/Issue: only if there is concrete technical value.")
body.append("- Rocket reaction: only after manual review of a real release.")
body.append("- No generic comments.")
body.append("")
body.append("## Repository candidates")
body.append("")
body.append("| # | Repo | Stars | Forks | Language | Pushed | Notes |")
body.append("|---:|---|---:|---:|---|---|---|")

for index, item in enumerate(items[:120], start=1):
    body.append(
        f"| {index} | [{item['full_name']}]({item['url']}) | "
        f"{item['stars']} | {item['forks']} | {item['language']} | "
        f"{item['pushed_at']} | {item['description']} |"
    )

body.append("")
body.append("## Recent release candidates")
body.append("")

checked = 0
for item in items:
    if checked >= 40:
        break
    checked += 1

    full = item["full_name"]

    try:
        release = gh_json(f"https://api.github.com/repos/{full}/releases/latest")
    except Exception:
        continue

    rel_url = release.get("html_url")
    rel_name = release.get("name") or release.get("tag_name")
    rel_date = release.get("published_at")

    if rel_url and rel_name:
        body.append(f"- [{full} — {rel_name}]({rel_url}) — {rel_date}")

body.append("")
body.append("## High-signal AxonOS contribution angles")
body.append("")
body.append("- deterministic test vectors")
body.append("- README scope corrections")
body.append("- Rust `no_std` compatibility notes")
body.append("- CI hardening")
body.append("- reproducibility checks")
body.append("- privacy/security boundary documentation")
body.append("- protocol conformance examples")
body.append("- benchmark fixtures")
body.append("- issue triage with concrete reproduction steps")
body.append("")
body.append("## Low-signal actions to avoid")
body.append("")
body.append("- generic comments")
body.append("- mass reactions")
body.append("- mass following maintainers")
body.append("- opening issues just to advertise AxonOS")

body_path = "/tmp/axonos-community-radar.md"

with open(body_path, "w", encoding="utf-8") as f:
    f.write("\n".join(body) + "\n")

def run(cmd):
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

subprocess.run(
    [
        "gh", "label", "create", "radar",
        "--repo", REPO,
        "--description", "AxonOS community radar",
        "--color", "8A6F35",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

existing = run([
    "gh", "issue", "list",
    "--repo", REPO,
    "--state", "open",
    "--json", "number,title",
    "--jq", '.[] | select(.title=="AxonOS Community Radar") | .number',
])

issue_number = existing.stdout.strip().splitlines()[0] if existing.stdout.strip() else ""

if issue_number:
    cmd = [
        "gh", "issue", "edit", issue_number,
        "--repo", REPO,
        "--body-file", body_path,
    ]
else:
    cmd = [
        "gh", "issue", "create",
        "--repo", REPO,
        "--title", "AxonOS Community Radar",
        "--body-file", body_path,
        "--label", "radar",
    ]

result = run(cmd)

if result.returncode != 0:
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

print("OK: AxonOS Community Radar issue updated")
