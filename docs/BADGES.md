# AxonOS Radar — Badges

Every project on the map carries a live, embeddable badge: its **BRS** (BCI
Relevance Score, 0–100) and relevance tier, rendered by shields.io straight
from the radar's published data. The badge is **derived, never granted** —
whatever the engine scored on the last scan is what the badge says. It updates
when the map updates (every ~3 hours) and no hand can edit it, which is exactly
what makes it worth embedding.

## Embed yours

Find your project on the [map](https://axonos-bci.github.io/axonos-community-radar/),
open its evidence ledger (tap the BRS chip), and press **Copy badge** — or build
the Markdown yourself:

```markdown
[![AxonOS Radar](https://img.shields.io/endpoint?url=https%3A%2F%2Faxonos-bci.github.io%2Faxonos-community-radar%2Fbadges%2FOWNER%2FREPO.json)](https://axonos-bci.github.io/axonos-community-radar/)
```

Replace `OWNER%2FREPO` with your path (keep `%2F` for the slash). Every badge
endpoint is also listed with ready-to-paste Markdown in
[`badges/index.json`](https://axonos-bci.github.io/axonos-community-radar/badges/index.json).

## Reading the colour

| Colour | Band |
|:--|:--|
| 🟢 `34d399` | BRS ≥ 80 — explicit, load-bearing BCI work |
| 🔵 `2dd4ff` | BRS 60–79 — solid |
| 🟡 `fbbf24` | BRS 40–59 — on the map, developing |
| ⚪ `8a97a6` | scored qualitatively (no numeric BRS) |

Nothing below BRS 40 is on the map at all — inclusion is scored, not curated.

## Freshness and integrity

The endpoint carries `cacheSeconds: 10800` (one engine scan period); shields
re-fetches on that cadence. The message text is produced by the same pipeline
that builds the map — see the [methodology](METHODOLOGY.md) and the
[Data API](API.md). If your score looks wrong, the evidence ledger on your
project's card shows exactly which signals produced it.

---

<sub>© The AxonOS Project / Denis Yermakou · [axonos.org](https://axonos.org) · connect@axonos.org</sub>
