# Wunderment 26 — reference event

This is the actual `event.yaml` ElevateUT ships for the Wunderment 26 tournament at The Wasatch Wunder (Wasatch Mountain State Park, Midway, UT — May 30–31, 2026). It exercises every section of the `event.yaml` schema and serves as the canonical example for the project.

## Files

| File | What |
|------|------|
| `event.yaml` | The full event config — pools, hole overrides, sponsors, welcomes, schedule, custom slides |
| `layouts.json` | Snapshot of the PDGA Tournament Manager layouts for event 101284, fetched via `pdga-caddie-book pull 101284` |

## Building

You'll need image and font assets that are not bundled with this repo. To run this example end-to-end:

```bash
# 1. Drop hole map photos / sponsor logos / TD photos / etc. into ./images/
#    File names referenced by event.yaml:
#      images/wunderment-logo.png
#      images/elevateut-logo.png
#      images/wunder-logo.png
#      images/hole_01.jpg ... images/hole_18.jpg
#      images/hole_02_a.jpg images/hole_02_b.jpg   (per-pool variants)
#      images/hole_12_short.jpg                     (C pool variant)
#      images/parking-map.jpg images/camping-map.jpg
#      images/nick-jennings.jpg images/scott-belchak.jpg
#      images/westside-logo.svg images/howmz-logo.svg images/another-round-logo.png
#      images/uswdgc-logo-white.png

# 2. Drop font files into ./fonts/
#      fonts/ArticulatCF-Heavy.otf
#      fonts/ArticulatCF-DemiBold.ttf
#      fonts/ArticulatCF-Medium.otf
#      fonts/ArticulatCF-Normal.ttf

# 3. Build the slide decks
pdga-caddie-book build event.yaml --output build-output

# 4. Build the printable scorecards
pdga-caddie-book scorecards event.yaml --output build-output

# 5. Convert scorecards to PDF
pdga-caddie-book pdf build-output/scorecard-*.html
```

To rebuild the layouts cache after Nick edits the layout in PDGA TM:

```bash
pdga-caddie-book pull 101284 --output layouts.json --pretty
```

## What's interesting about this example

- **5 layouts, 3 pools** — A/B pools play different layouts each day; C pool plays the same 18-hole layout both days (note `same_as_previous: true` on day 2)
- **Per-pool image overrides** — Hole 2 has different physical hazard markings per pool, so A and B see different photos (`images.per_pool.{A,B}.["2"]`)
- **Per-layout image override** — C pool plays hole 12 from a different basket position, gets a dedicated photo (`images.per_layout`)
- **C Pool callout** — `rules.callouts.C` renders an attention-grabbing alert box only on the C Pool caddie book reminding players to look for the white-flag short pads
- **Pool-specific creek rule** — A/B pools have OB creek; C pool gets mandatory relief. Encoded as `rules.items[].text_by_pool.C`
- **Long welcome split across two pages** — `td_welcome.pages` is an array; each entry becomes its own slide with "continued →" / signature handling
- **Custom slide** — The USWDGC volunteer recruitment slide (`custom_slides.uswdgc_volunteers`) is raw HTML injected after the sponsors slide
- **Single-column rotated scorecard backs** — The auto-fit binary search in `scorecards.py` finds the largest legible font for each pool's notes density (A pool: ~11px, B pool: ~9px due to verbose hazard descriptions, C pool: ~12px)

## Live deployment

The built caddie books are deployed to:

- A pool: [elevateut.org/caddy/wunderment/a](https://elevateut.org/caddy/wunderment/a)
- B pool: [elevateut.org/caddy/wunderment/b](https://elevateut.org/caddy/wunderment/b)
- C pool: [elevateut.org/caddy/wunderment/c](https://elevateut.org/caddy/wunderment/c)
