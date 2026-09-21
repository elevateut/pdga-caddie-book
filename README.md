# pdga-caddie-book

Generate phone-optimized caddie books and printable scorecards for PDGA-sanctioned disc golf tournaments — driven by canonical layouts pulled straight from PDGA Tournament Manager.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)

```
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  PDGA Tournament     │ →  │  pdga-caddie-book    │ →  │  Phone-optimized     │
│  Manager (canonical) │    │  + event.yaml        │    │  reveal.js slides    │
│                      │    │  (your local content)│    │  + printable PDFs    │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

## What it does

Built by [ElevateUT Disc Golf](https://elevateut.com) after running the Wunderment tournament series for several years. Every tournament needs the same artifacts — a digital caddie book players load on their phone, a printable scorecard, a TD welcome, sponsor cards, course rules, hole-by-hole notes. We got tired of rebuilding them in InDesign every event.

This tool:

- **Pulls hole-by-hole layout data from PDGA Tournament Manager** — par, length, tee, target, position labels. Public endpoints, no PDGA credentials required.
- **Generates phone-optimized [reveal.js](https://revealjs.com/) caddie books** — one slide deck per pool, swipe through holes, OG image preview, deep-link friendly.
- **Generates printable duplex scorecards** — 3-up per page, hole notes on the back, short-edge flip.
- **Exports PDFs** via Playwright.
- **Driven by a single `event.yaml`** — sponsors, welcomes, schedule, course rules, per-pool overrides. PDGA data is canonical for layouts; YAML is canonical for everything else.

## Quickstart

```bash
pip install pdga-caddie-book

# Look up your tournament ID on the PDGA event page
# (e.g. https://www.pdga.com/tour/event/101284)

# 1. Pull layouts from PDGA TM (no auth needed)
pdga-caddie-book pull 101284 --output layouts.json

# 2. Bootstrap an event config (edit it to add your sponsors, welcomes, etc.)
pdga-caddie-book init my-event --tournament-id 101284

# 3. Build slide decks (one HTML file per pool)
pdga-caddie-book build my-event/event.yaml --output ./output

# 4. Build printable scorecards
pdga-caddie-book scorecards my-event/event.yaml --output ./output

# 5. Share images (og:image) and PDFs both need Playwright
pip install pdga-caddie-book[pdf]
playwright install chromium
pdga-caddie-book og my-event/event.yaml          # one 1200x630 preview card per pool
pdga-caddie-book pdf ./output/scorecard-*.html
```

Deploy the generated `*-slides.html` to any static host, with the `images/` folder. **Ship the share
images with every deploy.** A caddie book travels as a link in group texts and social posts, and the
books' `og:image` tags point at `deploy.og_image_pattern`: without those files a shared link has no
preview. `build` warns when one is missing. ElevateUT hosts ours on [elevateut.org/caddy/wunderment/a](https://elevateut.org/caddy/wunderment/a).

## Why PDGA-first?

PDGA Tournament Manager is the single source of truth for tournament layouts. TDs already build their layouts there to publish them on the public event page. This tool reads them back so you never duplicate that work — and so your caddie book stays in sync if you tweak a layout after publishing.

Layout text the TD edits in TM (par, length, position labels, tee notes) flows straight through. Anything that isn't layout-shaped — sponsor cards, welcome notes, schedule, course rules — lives in `event.yaml`.

If you want to **override** a specific PDGA note (e.g. PDGA has "OB left", but you want "OB left of the dead tree — mando enforced"), drop it in `event.yaml` under `hole_overrides`. Otherwise PDGA data passes through untouched.

## Example: Wunderment 26

A full working configuration lives at [`examples/wunderment-26/`](examples/wunderment-26/). It's the actual config ElevateUT ships for the Wunderment 26 event at The Wasatch Wunder (Midway, UT) — A/B/C pools, two days, custom rules per pool, sponsors, USWDGC volunteer recruitment slide.

Generated artifacts:
- `pool-a-slides.html` — A Pool caddie book ([live](https://elevateut.org/caddy/wunderment/a))
- `pool-b-slides.html` — B Pool caddie book ([live](https://elevateut.org/caddy/wunderment/b))
- `pool-c-slides.html` — C Pool caddie book ([live](https://elevateut.org/caddy/wunderment/c))
- `scorecard-{pool}-day{n}.html` — printable duplex scorecards

## Event YAML schema

Full schema reference: [`docs/event-yaml-schema.md`](docs/event-yaml-schema.md).

Minimal example:

```yaml
event:
  name: "My Tournament 2026"
  pdga_tournament_id: 101284
  dates: "May 30–31, 2026"
  location: "Midway, UT"

brand:
  logo: images/logo.png
  colors:
    primary: "#2C4A2E"
    accent: "#5C7A4A"

pools:
  A:
    name: "A Pool"
    divisions: "MPO, MP40, MA1"
    days:
      - { label: "Day 1", date: "Saturday, May 30", layout_id: 758489 }
      - { label: "Day 2", date: "Sunday, May 31",   layout_id: 758490 }
    color: { bg: "#2C4A2E", accent: "#5C7A4A", light: "#E8F0E4" }

# Override individual hole notes (PDGA data is used otherwise)
hole_overrides:
  "758489":  # LayoutID
    "14": "Dual mandos. DZ between mandos. Creek bed: optional relief toward tee, no penalty."

sponsors:
  - name: "Westside Discs"
    description: "Player pack disc sponsor."
    url: "https://westsidediscs.com"
```

## CLI reference

```
pdga-caddie-book pull TOURNAMENT_ID [--output FILE]
    Fetch all layouts from PDGA Tournament Manager.

pdga-caddie-book init NAME --tournament-id ID
    Scaffold an event directory with a starter event.yaml.

pdga-caddie-book build EVENT_YAML [--output DIR] [--layouts FILE]
    Generate reveal.js caddie book HTML for every pool.

pdga-caddie-book scorecards EVENT_YAML [--output DIR] [--layouts FILE]
    Generate printable duplex scorecards.

pdga-caddie-book og EVENT_YAML [--output DIR] [--pool KEY]
    Render each pool's share image (og:image, 1200x630) from its cover slide, to
    deploy.og_image_pattern under the event directory. Requires Playwright.

pdga-caddie-book pdf HTML_FILE [HTML_FILE...]
    Export HTML files to PDF via Playwright (requires `pip install .[pdf]`).
```

## Using as a Claude Code skill

If you use [Claude Code](https://docs.claude.com/claude-code), there's a one-file skill wrapper at [`docs/claude-code-skill.md`](docs/claude-code-skill.md). Drop it into `~/.claude/skills/caddie-book/SKILL.md` and Claude can run `/caddie-book` workflows for you.

## Contributing

Issues and PRs welcome. Particularly interested in:
- Additional event format support (singles vs doubles, match play)
- More slide layouts (custom slides currently require editing the YAML's `custom_slides` field with raw HTML)
- Alternate slide engines (impress.js, Spectacle, plain HTML)
- Localization

## Credits

Built by [ElevateUT Disc Golf](https://elevateut.com), a Utah 501(c)(3) nonprofit focused on growing disc golf course infrastructure in Utah.

PDGA Tournament Manager is a service of the [Professional Disc Golf Association](https://pdga.com). This project is not affiliated with or endorsed by the PDGA.

## License

[MIT](LICENSE)
