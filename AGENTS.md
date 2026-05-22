# AGENTS.md

Instructions for AI agents (Claude Code, GitHub Copilot Agent, Cursor, etc.) working in this repo.

The full guidance lives in [CLAUDE.md](CLAUDE.md) — it's identical regardless of which agent you are. Read it first.

## TL;DR for any agent

1. **PDGA Tournament Manager is the canonical source for hole text.** Don't add `hole_overrides` to the Wunder example. If the TD wants different wording, they update PDGA TM and we re-pull.
2. **Don't speculate about PDGA's authenticated v3 API.** It returned errors we couldn't diagnose; we use public endpoints only. Don't write claims about how its access model works.
3. **Single-column scorecard backs, no header, no whitespace.** User explicitly rejected two-column variants and header text on the back. The binary-search auto-fit + `justify-content: space-between` finds the largest legible font without trailing whitespace.
4. **Use inches in print CSS, never `vh`/`vw`.** Print viewport ≠ browser viewport. The whole point of `pdf.py`'s explicit 816×1056 viewport + `emulate_media('print')` is making them match.
5. **Wait for `data-fit-done`** in the PDF builder. Skipping it ships unreadable output.

For everything else — modules, build commands, deploy flow, code style, what NOT to do — see [CLAUDE.md](CLAUDE.md).
