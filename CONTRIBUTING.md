# Contributing to the AxonOS Radar

Thank you for helping map and grow the open BCI ecosystem! Every contribution — a project, a keyword, a docs fix, a UI tweak — makes the radar more useful.

## Add a project to the radar

Projects are discovered **live** from public GitHub topic search, so links are always real. To get a project included:

- **Easiest:** open a [project suggestion issue](https://github.com/AxonOS-BCI/axonos-community-radar/issues/new?template=add-project.yml).
- **Direct:** open a PR editing [`data/seeds.json`](data/seeds.json):
  - add a relevant **topic** to `topics` (the project should carry that GitHub topic), or
  - add a **keyword** under the right entry in `categories` so projects get categorised correctly.

Keep additions on-topic (BCI / neurotech / real-time / privacy / signal-processing / cognitive infrastructure). The radar is a discovery map, not a promo board.

## Good first issues

- Add a missing topic or category keyword.
- Improve a project's categorisation heuristic in `scripts/radar.py`.
- Polish the radar UI (`index.html`) — accessibility, mobile, legend.
- Improve docs.

## Local development

```bash
python3 -m http.server 8080            # preview the page at http://127.0.0.1:8080
GH_TOKEN=… python3 scripts/radar.py    # refresh data/radar.json locally
```

`index.html` is a single self-contained file (no build, no dependencies). `scripts/radar.py` uses only the Python standard library.

## Engagement policy (please follow)

When acting on what the radar surfaces:

1. Star only genuinely relevant repositories.
2. React only to releases that are genuinely relevant.
3. Open PRs only when they add real technical value.
4. Prefer tests, docs, reproducibility, benchmarks and protocol notes.
5. No mass-follows, no auto-comments, no low-signal noise.

## Conduct

By participating you agree to our [Code of Conduct](CODE_OF_CONDUCT.md).
