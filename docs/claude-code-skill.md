# Using pdga-caddie-book as a Claude Code skill

If you use [Claude Code](https://docs.claude.com/claude-code), you can wire `pdga-caddie-book` up as a slash command so Claude can run the whole workflow (pull → build → PDF → deploy) without you reaching for the CLI.

## Install the package

```bash
pip install pdga-caddie-book[pdf]
playwright install chromium
```

## Drop in the skill

Create the skill directory:

```bash
mkdir -p ~/.claude/skills/caddie-book
```

Save the file below at `~/.claude/skills/caddie-book/SKILL.md`:

````markdown
---
name: caddie-book
description: |
  Generate phone-optimized caddie books and printable scorecards for a
  PDGA-sanctioned disc golf tournament using `pdga-caddie-book`.
  Pass an event directory containing `event.yaml`. Pulls layouts from PDGA
  Tournament Manager, builds reveal.js slide decks per pool, builds duplex
  scorecards, and optionally exports PDFs.
---

## Workflow

When the user invokes `/caddie-book`, choose the right subcommand based on
their request:

| User intent | Run |
|-------------|-----|
| "pull layouts for event N" or "refresh PDGA data" | `pdga-caddie-book pull <id> --output <event_dir>/layouts.json --pretty` |
| "scaffold a new caddie book for event N" | `pdga-caddie-book init <name> --tournament-id <id>` |
| "build the caddie books" / "rebuild the slides" | `pdga-caddie-book build <event_dir>/event.yaml --output <event_dir>/output` |
| "build the scorecards" / "print the scorecards" | `pdga-caddie-book scorecards <event_dir>/event.yaml --output <event_dir>/output` |
| "make PDFs of the scorecards" | `pdga-caddie-book pdf <event_dir>/output/scorecard-*.html` |
| "make the share images" / "og image" / "link preview" | `pdga-caddie-book og <event_dir>/event.yaml` |
| "rebuild everything" | run `build`, `og`, `scorecards`, then `pdf` in sequence |

If the user names a pool (e.g. "rebuild A pool only"), add `--pool A`.

## Important conventions

- The user's event directory should contain `event.yaml`. Cache the PDGA layouts
  to `layouts.json` next to the yaml. Commit both to source control.
- After building, always show the user where the output files landed.
- **Every caddie book ships with a share image.** The books are passed around as links, and their
  `og:image` tags point at `deploy.og_image_pattern`. Make sure `event.yaml` sets `deploy.url_base` and
  `deploy.og_image_pattern`, run `og` after `build` (and again whenever the event name, dates, tagline,
  pool names, colours or logos change), and treat a `WARN ... share image` line from `build` as a blocker
  for deploying. After deploying, fetch each image URL and confirm it returns a 1200x630 image.
- If they ask to deploy, check whether they have a static-host workflow already
  configured (Vercel, Netlify, Cloudflare Pages, GitHub Pages). If yes, copy
  the built HTMLs to the right path and let them push. If no, ask.

## When to refuse

- If the user has not run `pull` and there's no `layouts.json`, run `pull` first
  rather than failing the build with a live-fetch fallback (faster + repeatable).
- If they edit the YAML and the build complains about a layout_id mismatch,
  re-run `pull` — PDGA layouts can be deleted/renumbered by the TD.

## Reference

- Project: https://github.com/elevateut/pdga-caddie-book
- Schema: `pdga-caddie-book --help` and `docs/event-yaml-schema.md`
````

That's it — Claude can now drive the whole pipeline.

## Example session

```
You: /caddie-book pull layouts for tournament 101284 to ~/my-event

Claude runs: pdga-caddie-book pull 101284 --output ~/my-event/layouts.json --pretty
            → Wrote ~/my-event/layouts.json — 5 layout(s)

You: /caddie-book rebuild everything in ~/my-event

Claude runs: pdga-caddie-book build ~/my-event/event.yaml --output ~/my-event/output
            pdga-caddie-book scorecards ~/my-event/event.yaml --output ~/my-event/output
            pdga-caddie-book pdf ~/my-event/output/scorecard-*.html
```

## Going further

You can extend the skill with project-specific knowledge — for example, if you
always deploy caddie books to `elevateut-web/public/caddy/<event>/`, add a
"Deploy" step that copies the built HTMLs there and runs `git commit` in that
repo. Skills compose well; keep the auto-fit logic to `pdga-caddie-book` and
let the skill handle your team's deploy conventions.
