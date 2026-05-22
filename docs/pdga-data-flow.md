# PDGA data flow

How `pdga-caddie-book` reads canonical layout data from PDGA Tournament Manager — without requiring PDGA credentials, app tokens, or any TD-side setup.

## TL;DR

```
PDGA event page                       Your event.yaml
─────────────────                     ──────────────────
www.pdga.com/tour/event/{id}          pdga_tournament_id: {id}
                                              │
                                              ▼
              ┌──────────────────────────────────────────┐
              │  pdga-caddie-book pull {id}              │
              │                                          │
              │  1. GET live-api/live_results_fetch_event│
              │     → { Layouts: [{ LayoutID, ... }] }   │
              │                                          │
              │  2. For each LayoutID:                   │
              │     GET courserules?LayoutID={lid}       │
              │     → HTML with hole-by-hole rows        │
              │                                          │
              │  3. Merge → layouts.json                 │
              └──────────────────────────────────────────┘
                                              │
                                              ▼
                                          layouts.json
                                              │
                                              ▼
              ┌──────────────────────────────────────────┐
              │  pdga-caddie-book build event.yaml       │
              │  ─ merge PDGA layouts + event yaml ─     │
              │  ─ apply hole_overrides ─                │
              │  ─ render reveal.js HTML ─               │
              └──────────────────────────────────────────┘
```

## The two PDGA endpoints

Both are **public** — no auth required, no token in any header. We use a realistic browser User-Agent because PDGA is fronted by Cloudflare and rejects default `python-urllib` user-agents.

### 1. Layout index — Live Results API

```
GET https://www.pdga.com/apps/tournament/live-api/live_results_fetch_event?TournID={tournament_id}

Response:
{
  "data": {
    "Name": "Wunderment 26 (CEP Charity - Rated) - Presented by Westside",
    "Layouts": [
      {
        "LayoutID": 758489,
        "CourseID": 12345,
        "CourseName": "The Wasatch Wunder",
        "Name": "A Pool - Day 1",
        "Holes": 21,
        "Par": 63,
        "Length": 5330
      },
      ...
    ]
  }
}
```

Used to enumerate which layouts exist for a tournament, and get top-level totals.

### 2. Per-layout detail — Tournament Manager HTML

```
GET https://www.pdga.com/apps/tournament/manager/{tournament_id}/courserules?LayoutID={layout_id}&Display=details

Response: HTML page containing a <table> like:
   <table>
     <thead><tr><th>Hole</th><th>Tee</th><th>Target</th><th>Par</th><th>Feet</th><th>Notes</th></tr></thead>
     <tbody>
       <tr>
         <th class="hole">9</th>
         <td class="tee">Long</td>
         <td class="target">A</td>
         <td class="par">3</td>
         <td class="length">230</td>
         <td class="notes">A Position Round 1.</td>
       </tr>
       ...
     </tbody>
   </table>
```

We scrape this with a stdlib `html.parser.HTMLParser` subclass — see `pdga_caddie_book/pdga.py:_CourseRulesParser`. No `beautifulsoup4` dependency.

## Output shape

The fetcher's JSON output:

```json
{
  "tournament_id": "101284",
  "tournament_name": "Wunderment 26 (CEP Charity - Rated) - Presented by Westside",
  "layouts": {
    "758489": {
      "LayoutID": 758489,
      "CourseID": 12345,
      "CourseName": "The Wasatch Wunder",
      "Name": "A Pool - Day 1",
      "Holes": 21,
      "Par": 63,
      "Length": 5330,
      "Units": "feet",
      "GeneralNotes": "",
      "Detail": {
        "1": {
          "Label": "9",
          "Tee": "Long",
          "Target": "A",
          "Par": 3,
          "Length": 230,
          "Notes": "A Position Round 1."
        },
        "2": { "Label": "10", ... },
        ...
      }
    },
    ...
  }
}
```

`Detail` is keyed by **display order** (the position in the round, starting at 1) rather than course hole number. This makes round-robin layouts (where you start on hole 9 and end on hole 8) trivial to render in order — the keys reflect play order directly.

The `Label` field carries the displayed course hole number (`"9"`, `"10A"`, `"2/3"` for combo holes, etc.). You override notes by display order in `event.yaml`:

```yaml
hole_overrides:
  "758489":            # LayoutID
    "1":               # Display order — this is the hole that plays FIRST (course hole 9)
      notes: "A Position Round 1 — flagged hazard on left of green"
```

## Rate limiting

The skill makes 1 + N requests per `pull` (one for the layout index, N for the layout details). For a typical Wunder-scale event (5 layouts) that's 6 requests. We do not implement explicit rate-limiting — PDGA's public endpoints have been responsive in testing, and one event's pull is short-lived.

For consumers running many pulls in parallel, the `elevateut_league` PDGA Services client uses a 300ms minimum spacing between requests. If you build a multi-event tool on top of `pdga.fetch_layouts()`, do the same.

## Caching

By convention, `event.yaml` lives next to a `layouts.json` cache. The builder picks up the cache automatically:

```
my-event/
├── event.yaml
└── layouts.json          # checked in; refreshed via `pdga-caddie-book pull`
```

Refresh the cache after the TD changes anything in PDGA Tournament Manager:

```bash
pdga-caddie-book pull 101284 --output my-event/layouts.json --pretty
```

Commit `layouts.json` to your repo so builds are deterministic and don't require a live PDGA fetch.
