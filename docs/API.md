# AxonOS Radar — Data API

The live, scored map of the open BCI ecosystem, as data. Everything the radar
publishes is served as static, versioned, machine-readable endpoints over
GitHub Pages — no keys, no rate negotiation, CORS open. This page is the human
contract; the machine contract is [`data/api.json`](https://axonos-bci.github.io/axonos-community-radar/data/api.json),
which is rebuilt on every deploy by walking the artifact, so it can never list
an endpoint the deploy does not carry.

**Base URL:** `https://axonos-bci.github.io/axonos-community-radar/`

## The endpoints

| Path | Kind | What it is |
|:--|:--|:--|
| `data/api.json` | index | The front door: every endpoint, stability, schema pointers, freshness, licensing |
| `data/radar.json` | dataset | The scored map — BRS, evidence ledger, facets, health, deltas, coverage matrix, standards graph, builders ([schema](https://axonos-bci.github.io/axonos-community-radar/data/radar.schema.json)) |
| `data/signals.json` | dataset | What changed this week — new / rising / cooling with measured evidence ([schema](https://axonos-bci.github.io/axonos-community-radar/data/signals.schema.json)) |
| `data/projects.ndjson` | export | One project per line — pandas, jq, DuckDB |
| `data/projects.csv` | export | Core columns, flat — spreadsheets, BI |
| `data/history.json` | dataset | Aggregate snapshots over time |
| `data/weekly.json` | dataset | The week's deltas in one small file |
| `data/first_seen.json` | dataset | Discovery log — first-seen timestamp per project |
| `data/ecosystem.json` | dataset | AxonOS ecosystem manifest with live signals |
| `data/interop-vocab.json` | vocabulary | The open interop vocabulary (matcher is open too) |
| `data/status.json` · `data/last_run.json` | ops | Last-scan read-out and outcome |
| `data/badge-ecosystem.json` | badge | Shields.io endpoint — live count + median health |
| `feed.xml` · `feeds/signals.xml` · `feeds/new.xml` · `feeds/rising.xml` | feeds | RSS — arrivals, all signals, new only, rising only |

## Freshness

The engine scans every 3 hours (`17 */3 * * *` UTC); the site syncs and
redeploys minutes later on its own clock, with a health monitor alerting on
staleness twice daily. `generated_at` — present in `api.json`, `radar.json`,
and `signals.json` — is the scan the deploy you're reading actually carries.
Poll politely: the data cannot move faster than the scan.

## Conventions

- **CORS**: GitHub Pages serves `Access-Control-Allow-Origin: *` — fetch from
  a browser, a notebook, a serverless function, anywhere.
- **Caching**: standard `ETag` / conditional GET. Send `If-None-Match` and you
  pay nothing when nothing changed.
- **Stability**: additive within `api_version` (currently `1`). Removing or
  renaming a field or endpoint bumps `api_version`. New fields may appear at
  any time; parse tolerantly.
- **Signal identity**: a signal's `id` is derived from *(kind, project, ISO
  week)* — the same fact keeps one identity for the week it is true, so feed
  readers never re-alert on the same thing.

## Quick starts

```bash
# The whole map, scored
curl -s https://axonos-bci.github.io/axonos-community-radar/data/radar.json | jq '.counts'
```

```python
# pandas: one line to a DataFrame
import pandas as pd
df = pd.read_json("https://axonos-bci.github.io/axonos-community-radar/data/projects.ndjson",
                  lines=True)
df.nlargest(10, "brs")[["full_name", "brs", "stars", "category"]]
```

```js
// What changed this week
const r = await fetch("https://axonos-bci.github.io/axonos-community-radar/data/signals.json");
const { counts, signals } = await r.json();
```

```bash
# Subscribe to momentum only
https://axonos-bci.github.io/axonos-community-radar/feeds/rising.xml
```

## Licensing

The map is free to use **with attribution** — link back to the radar. That
tier stays free; transparency is the moat.

**Licensed feeds, SLAs, custom slices, and redistribution** for funds, labs,
and platforms: [connect@axonos.org](mailto:connect@axonos.org).

---

<sub>© The AxonOS Project / Denis Yermakou · [axonos.org](https://axonos.org) · connect@axonos.org</sub>
