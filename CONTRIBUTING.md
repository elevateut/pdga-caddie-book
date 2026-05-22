# Contributing

Thanks for considering a contribution to `pdga-caddie-book`!

## Quick local setup

```bash
git clone git@github.com:elevateut/pdga-caddie-book.git
cd pdga-caddie-book

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[pdf,dev]"
playwright install chromium
```

Verify the install:

```bash
pdga-caddie-book --help
pdga-caddie-book pull 101284 --summary       # Wunderment 26
```

## Building the reference example

The Wunderment 26 event under `examples/wunderment-26/` is the canonical
reference. To rebuild it locally:

```bash
cd examples/wunderment-26
pdga-caddie-book build event.yaml --output build-output
pdga-caddie-book scorecards event.yaml --output build-output
pdga-caddie-book pdf build-output/scorecard-*.html
```

The expected outputs are 3 `pool-*-slides.html` files (caddie books) and
5 `scorecard-*-day*.html` files (one per pool-day combination).

## Project layout

```
pdga_caddie_book/
  pdga.py          PDGA Tournament Manager scraper (public endpoints)
  config.py        event.yaml loader + PDGA-data merger
  slides.py        Reveal.js slide HTML builders (one fn per slide type)
  shell.py         Reveal.js outer HTML / theme / OG meta
  scorecards.py    Printable duplex scorecard HTML (with rotated back notes)
  pdf.py           Playwright PDF export wrapper
  builder.py       Orchestrator — composes the slide deck per pool
  cli.py           argparse subcommands → entry point
```

## Adding a new slide type

1. Add a builder fn to `slides.py` taking `(event, pool_key) -> str` (single
   slide) or `-> list[str]` (multiple slides). Return reveal.js `<section>`
   markup.
2. Register it in `BUILDERS` in `builder.py`.
3. Add it to `DEFAULT_ORDER` at the position you want it to render.
4. Document the YAML schema for it in `docs/event-yaml-schema.md`.

## Testing visual changes

The Wunder example is committed as the regression test. Before opening a PR:

1. Run the build commands above.
2. Open the generated HTMLs in a browser to confirm nothing visual regressed.
3. Generate the PDFs and check the scorecard backs at print scale — the
   auto-fit JS is finicky; manually verify text size + edge alignment.

## Code style

- Python 3.10+, formatted with `ruff format`.
- No comments that just describe what code does — only write comments to
  explain *why* something is non-obvious (a workaround, a constraint, a
  surprising browser behavior).
- Inline CSS in the slide builders is intentional — keeps each section
  self-contained and avoids global styling conflicts when these HTMLs are
  embedded in a host page.

## What's in scope vs out of scope

**In scope:**
- New slide types (gallery, awards, course descriptions, ...)
- More sponsor card variants
- Additional tournament formats (match play, team singles)
- Localization / RTL support
- Alternate output formats (Spectacle, impress.js, plain HTML)
- Improvements to the PDGA scraper resilience

**Out of scope:**
- Doing PDGA registration or check-in (use [DGScene](https://www.discgolfscene.com/) for that)
- Live scoring (use the [PDGA Live Results](https://www.pdga.com/apps/tournament/live/) site)
- TD-side event management

## Reporting bugs

Please include:
- The relevant section of your `event.yaml`
- Your `layouts.json` (or the tournament ID so we can repro)
- The actual vs expected output
- For PDF issues: screenshots at the actual page size

## License

By contributing, you agree your contributions will be licensed under the
MIT License (see [LICENSE](LICENSE)).
