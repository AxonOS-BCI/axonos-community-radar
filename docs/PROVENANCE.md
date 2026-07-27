# Commit provenance

This repository publishes numbers about other people's projects. The least it
can do is make its own history checkable. This page states exactly how every
commit here is produced, which ones carry a cryptographic signature, and how to
verify all of it yourself without trusting this page.

## The three writers

| Writer | How the commit is made | Appears as | Signed |
|:--|:--|:--|:--|
| **Release commits** | Made on the maintainer's device with `git commit -S`, pushed to `main` | `Denis Yermakou` | ✅ by the maintainer's key |
| **Sync workflow** (`sync.yml`) | GitHub Contents API, authenticated with the workflow's built-in `GITHUB_TOKEN` | `github-actions[bot]` | ✅ by GitHub |
| **Engine publish path** | The same Contents API, authenticated with a user PAT held by the private engine | the PAT owner | ❌ unsigned |

The third row is the interesting one, because the first two prove the mechanism
works. GitHub signs commits it creates on your behalf through the API when the
caller is an *App* identity — and a workflow's `GITHUB_TOKEN` is exactly that.
The identical API call authenticated with a *personal access token* is treated
as that person pushing, and GitHub does not sign it.

Both paths write byte-identical files. The difference exists only in the
history, which is why it went unnoticed for a while and why it is measured now.

## Why two writers exist at all

The map is refreshed by a deliberate dual path: the private engine can push its
scan output here, and this repository independently pulls the same data on its
own schedule. Neither is a single point of failure. The cost of that redundancy
was that whichever path ran first wrote the commit — and when the engine
repository became private, the pull path went blind and the PAT path became the
only writer.

The arrangement from v13.1.0 keeps the redundancy without the cost:

1. This repository pulls with its own `GITHUB_TOKEN` (signed commits), using an
   optional read-only `ENGINE_READ_TOKEN` secret when the engine is private.
2. The engine's publish path runs in **fallback mode** — it publishes only when
   the data here has aged past a threshold, i.e. only when the pull path has
   actually stopped working.

Normal operation is therefore fully signed, the map still cannot freeze, and a
rare unsigned commit is itself a useful alarm: it means the pull path failed.

## Verify it yourself

Signature status, straight from GitHub, for the last 30 commits:

```bash
python3 scripts/check_provenance.py --limit 30
```

The same thing without this repository's code, using the API directly:

```bash
gh api repos/AxonOS-BCI/axonos-community-radar/commits \
  --jq '.[] | "\(.sha[0:8]) \(.commit.verification.verified) \(.author.login)"'
```

Or locally, against the raw objects — a signed commit carries a `gpgsig`
header, and no API is involved in checking that:

```bash
git cat-file commit HEAD | head -20
```

The health workflow runs the first of these on its schedule and prints the
result into its job summary, so provenance drift shows up without anyone
remembering to look.

## What a signature does and does not mean

A signature says *this key's holder produced this content*. It says nothing
about whether the content is correct. Signed nonsense is still nonsense — which
is why the data itself is guarded separately, by the contract gate on the sync
path, the schema validation in CI, and the plausibility gates described in
[docs/METHODOLOGY.md](METHODOLOGY.md).

Old commits are **not** retroactively signed here, and won't be. Signing history
after the fact with today's key would manufacture a provenance claim that isn't
true, which is precisely the thing this page exists to avoid.

---

<sub>© The AxonOS Project / Denis Yermakou · [axonos.org](https://axonos.org) · connect@axonos.org</sub>
