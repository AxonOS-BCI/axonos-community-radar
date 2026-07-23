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
- Spot a miscategorized project? Open an issue — the ledger behind every score
  is public, so pointing at exactly which signal is wrong is fast; the scoring
  logic itself now lives in the private engine, so a fix has to land there, but
  a clear report is most of the work.
- Polish the radar UI (`index.html`) — accessibility, mobile, legend.
- Improve docs.

## Local development

```bash
python3 -m http.server 8080   # preview the page at http://127.0.0.1:8080,
                               # against the data/radar.json already committed
pip install -r requirements-ci.txt --break-system-packages
python3 -m pytest tests/      # run the test suite
python3 scripts/validate_payload.py data/radar.json   # check the current data
```

`index.html` is a single self-contained file (no build, no dependencies).
Discovery and scoring run entirely inside the private engine (`axonos-radar-core`)
on its own schedule — there's no local equivalent to "refresh the data" here;
everything under `scripts/` in *this* repo is the showcase and sync tooling
(badges, signals, exports, API index, validation), not the scanner itself.

## Engagement policy (please follow)

When acting on what the radar surfaces:

1. Star only genuinely relevant repositories.
2. React only to releases that are genuinely relevant.
3. Open PRs only when they add real technical value.
4. Prefer tests, docs, reproducibility, benchmarks and protocol notes.
5. No mass-follows, no auto-comments, no low-signal noise.

## Conduct

By participating you agree to our [Code of Conduct](CODE_OF_CONDUCT.md).
