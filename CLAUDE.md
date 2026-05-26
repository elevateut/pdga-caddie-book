# CLAUDE.md

How Claude Code should behave in the `pdga-caddie-book` repo.

## What this is

Open-source tool that generates phone-optimized caddie books (reveal.js slide decks), printable duplex scorecards, and event guides (spectator, competitor) for PDGA-sanctioned disc golf tournaments. Driven by a single `event.yaml` per event, plus canonical layout data pulled from PDGA Tournament Manager via public endpoints.

The reference event is Wunderment 26 (`examples/wunderment-26/`) — ElevateUT Disc Golf's tournament at The Wasatch Wunder in Midway, UT.

## Core principles

**PDGA Tournament Manager is the canonical source for hole text.** The Wunder example does NOT use `hole_overrides` — if a ground rule changes, the TD updates PDGA TM and `pdga-caddie-book pull` picks it up on the next build. Don't add hole overrides to `examples/wunderment-26/event.yaml` unless explicitly asked. The override mechanism stays in the package for events where the caddie-book author doesn't have PDGA edit access.

**Don't speculate about PDGA's authenticated APIs.** Earlier work tried the v3 Tournament Manager API at `/apps/tournament/api/{app_name}/...` and got `"Invalid event specified"`. We never conclusively diagnosed why. Do not write authoritative-sounding claims about app binding, TD permissions, FLiPT linking, or anything else regarding v3 access. The docs intentionally only describe what's verified: the public `live-api/live_results_fetch_event` + `courserules?LayoutID=...` HTML scrape path. If asked about v3, say "not used, not conclusively diagnosed" and stop.

## How the pipeline works

```
PDGA Tournament Manager → pdga.fetch_layouts(id) → layouts.json
                                                     ↓
                                          event.yaml + layouts.json
                                                     ↓
                              builder.build_event(...) → pool-{X}-slides.html
                              scorecards.build_event(...) → scorecard-{pool}-day{N}.html
                              guide_builder.build_event_guides(...) → spectator-guide.html
                                                     ↓
                                          pdf.export_pdfs(...) → PDF (via Playwright)
```

Key modules:
- `pdga_caddie_book/pdga.py` — public-endpoint scraper (no auth, no app token)
- `pdga_caddie_book/config.py` — yaml loader + PDGA merge + hole/image resolvers
- `pdga_caddie_book/slides.py` — one fn per slide type, returns reveal.js `<section>` markup
- `pdga_caddie_book/guide_slides.py` — slide builders for event guides (spectator, competitor)
- `pdga_caddie_book/guide_builder.py` — guide orchestrator, reuses shared slides + guide-specific ones
- `pdga_caddie_book/shell.py` — outer reveal.js HTML/CSS/init
- `pdga_caddie_book/builder.py` — caddie book orchestrator, default slide order + custom slide injection
- `pdga_caddie_book/scorecards.py` — printable duplex scorecards w/ rotated single-column back
- `pdga_caddie_book/pdf.py` — Playwright wrapper

## Hard-won gotchas (do not re-litigate)

**CSS units in print mode.** `100vh`/`100vw` resolve to the *browser viewport* (typically 720px tall), NOT the print page. Mix vh/vw with `inch` units and your JS measurements diverge from your PDF output. The scorecard CSS uses inches throughout for exactly this reason. `pdf.py` sets Playwright viewport to 816×1056 (Letter at 96dpi) so the rendering box matches print box.

**Auto-fit must use binary search, not decremental shrink.** The scorecard back's rotated notes panel uses a binary search over font size [4px, 24px] to find the LARGEST font that fits, paired with `justify-content: space-between` to eliminate trailing whitespace. A naive `while size > min and overflowing: size -= 0.5` loop tends to undershoot.

**Don't use 2 columns for the rotated notes.** User explicitly rejected two-column fallbacks: "we don't want two columns" and again "this just makes even more white space. The goal is zero white space." Single column at whatever font size the binary search settles on. If notes are too long to be legible single-col, that's a content problem (notes should be shorter in PDGA), not a layout problem.

**The scorecard back has no header.** User removed it. Don't add it back.

**Cuts must align between front and back.** Both sides are 3 horizontal strips stacked top-to-bottom; the dashed cut lines on the front match the strip boundaries on the back. The rotation happens INSIDE each strip (just the notes content), not on the whole back page.

**Playwright PDF wait.** `pdf.py` calls `page.wait_for_function("=> data-fit-done === '1'")` after navigating so the auto-fit JS settles before the PDF is captured. Removing or shortcutting this WILL ship 5px font output.

## Build / verify

```bash
# Rebuild Wunder reference (needs images/ + fonts/ symlinks — see examples/wunderment-26/README.md)
cd /path/to/pdga-caddie-book
python3 -m pdga_caddie_book pull 101284 -o examples/wunderment-26/layouts.json --pretty
python3 -m pdga_caddie_book build examples/wunderment-26/event.yaml -o examples/wunderment-26/build-output
python3 -m pdga_caddie_book scorecards examples/wunderment-26/event.yaml -o examples/wunderment-26/build-output
python3 -m pdga_caddie_book pdf examples/wunderment-26/build-output/scorecard-*.html

# Build USWDGC spectator guide (guide-only, no PDGA layouts needed)
python3 -m pdga_caddie_book spectator-guide examples/uswdgc-2026/event.yaml -o examples/uswdgc-2026/build-output
```

Wunder visual assets (hole photos, brand logos, fonts) live at `/Users/scott/ElevateUT_501c3/Events/wunderment-26/caddie-book/` and are NOT in the public repo. Symlink them into `examples/wunderment-26/{images,fonts}` to make the example build locally.

## Deploy (ElevateUT only)

Wunderment caddie books deploy via the `elevateut-web` repo:

```bash
cp examples/wunderment-26/build-output/pool-a-slides.html /Users/scott/elevateut-web/public/caddy/wunderment/a.html
cp examples/wunderment-26/build-output/pool-b-slides.html /Users/scott/elevateut-web/public/caddy/wunderment/b.html
cp examples/wunderment-26/build-output/pool-c-slides.html /Users/scott/elevateut-web/public/caddy/wunderment/c.html
cd /Users/scott/elevateut-web
git add public/caddy/wunderment/{a,b,c}.html  # stage ONLY these — repo has unrelated dirty state
git commit -m "..."
git push  # Vercel auto-deploys
```

Live URLs:
- https://elevateut.org/caddy/wunderment/a
- https://elevateut.org/caddy/wunderment/b
- https://elevateut.org/caddy/wunderment/c

Guides deploy the same way — copy the `spectator-guide.html` output to the public directory.

## Code style

- Python 3.10+. Format with `ruff format`. Line length 110.
- Default to NO comments. Only write a comment when *why* is non-obvious (workaround, browser quirk, surprising constraint). Never narrate what code does.
- Inline CSS in slide builders is intentional — keeps each `<section>` self-contained so the HTMLs can be embedded in a host page later without style conflicts.
- Pure stdlib + `PyYAML` for the core package. Playwright is the only optional extra (PDF export). Don't add deps casually.
- The PDGA scraper uses `html.parser` stdlib, not BeautifulSoup. Keep it that way.

## What NOT to do

- Don't add hole_overrides to the Wunder example. (PDGA is canonical.)
- Don't write claims about how PDGA v3 access works. (Not verified.)
- Don't reintroduce 2-column scorecard backs. (User rejected.)
- Don't reintroduce the back-page header. (User removed.)
- Don't mix `vh`/`vw` and `inch` units in print CSS. (See gotchas.)
- Don't bypass the `data-fit-done` wait in `pdf.py`. (Ships unreadable PDFs.)
- Don't commit `examples/*/build-output/` or `layouts-cache.json` or `.DS_Store`. (Already gitignored.)
- Don't commit `examples/wunderment-26/{images,fonts}` symlinks. (They point outside the repo.)

## Going further

`docs/event-yaml-schema.md` — full YAML schema reference for new events.
`docs/pdga-data-flow.md` — how the PDGA scraper works + JSON shape.
`docs/claude-code-skill.md` — wrapping this CLI as a Claude Code slash command.
`CONTRIBUTING.md` — project layout, in-scope/out-of-scope, contributor setup.
