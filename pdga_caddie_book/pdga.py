#!/usr/bin/env python3
"""Fetch PDGA Tournament Manager layouts for a given tournament — public, no auth.

Two-step flow against public PDGA endpoints:

  1. GET https://www.pdga.com/apps/tournament/live-api/live_results_fetch_event?TournID={id}
     -> { data: { Name, Layouts: [{ LayoutID, CourseID, CourseName, Name, Holes, Par, ... }], ... } }

  2. GET https://www.pdga.com/apps/tournament/manager/{id}/courserules?LayoutID={lid}&Display=details
     -> HTML page with a <table> of (Hole, Tee, Target, Par, Feet, Notes) rows
        plus a "General Notes" paragraph and the layout title.

Output shape:

  {
    "tournament_id": "...",
    "tournament_name": "...",
    "layouts": {
      "{layout_id}": {
        "LayoutID": int,
        "CourseID": int,
        "CourseName": str,
        "Name": str,
        "Holes": int,
        "Par": int,
        "Length": int,
        "Units": "feet",
        "GeneralNotes": str,
        "Detail": {
          "{display_order}": {
            "Label": str,    # course hole number (e.g. "9", "10A")
            "Tee":   str,
            "Target": str,
            "Par":   int,
            "Length": int,
            "Notes": str
          }
        }
      }
    }
  }

PDGA serves these endpoints behind Cloudflare. We send a realistic browser
User-Agent so we're not flagged.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any

BASE = "https://www.pdga.com"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GET {url} → HTTP {e.code}\n{body[:400]}")


def fetch_event_meta(tournament_id: str) -> dict[str, Any]:
    """Returns the live-results event metadata (includes Layouts list)."""
    url = f"{BASE}/apps/tournament/live-api/live_results_fetch_event?TournID={tournament_id}"
    text = _get(url)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Event API returned non-JSON for {tournament_id}:\n{text[:400]}")


class _CourseRulesParser(HTMLParser):
    """Parses the courserules HTML page into a structured layout dict.

    The page layout is:
      <title>Course Rules - {Tournament Name} - {Layout Name} </title>
      ...
      <h1>{Tournament Name}</h1>
      <h2>{Layout Name}</h2>
      <p class="notes">{General Notes}</p>
      <table>
        <thead><tr><th>Hole</th><th>Tee</th><th>Target</th><th>Par</th><th>Feet</th><th>Notes</th></tr></thead>
        <tbody>
          <tr>
            <th class="hole">9</th>
            <td class="tee">Long</td>
            <td class="target">A</td>
            <td class="par">3</td>
            <td class="length">230</td>
            <td class="notes">Hole 9: A Pool - A Position Round 1.</td>
          </tr>
          ...
        </tbody>
      </table>
    """

    def __init__(self):
        super().__init__()
        self._buf: list[str] = []
        self._capture = False
        self._row_open = False
        self._current_cell_class: str | None = None
        self._current_row: dict[str, str] = {}
        self.rows: list[dict[str, str]] = []
        self.title: str = ""
        self.layout_name: str = ""
        self.general_notes: str = ""
        self._in_h2 = False
        self._in_general_notes = False
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag == "title":
            self._in_title = True
            self._capture = True
            self._buf = []
        elif tag == "h2":
            self._in_h2 = True
            self._capture = True
            self._buf = []
        elif tag == "p" and "notes" in cls:
            self._in_general_notes = True
            self._capture = True
            self._buf = []
        elif tag == "tr":
            self._row_open = True
            self._current_row = {}
        elif tag in ("th", "td") and self._row_open:
            self._current_cell_class = cls.strip()
            self._capture = True
            self._buf = []

    def handle_endtag(self, tag: str):
        text = "".join(self._buf).strip()
        if tag == "title" and self._in_title:
            self.title = text
            self._in_title = False
            self._capture = False
        elif tag == "h2" and self._in_h2:
            self.layout_name = text
            self._in_h2 = False
            self._capture = False
        elif tag == "p" and self._in_general_notes:
            self.general_notes = text
            self._in_general_notes = False
            self._capture = False
        elif tag in ("th", "td") and self._row_open and self._current_cell_class is not None:
            self._current_row[self._current_cell_class] = text
            self._capture = False
            self._current_cell_class = None
        elif tag == "tr" and self._row_open:
            # Keep data rows only — skip the <thead> header row whose "hole" cell is literally "Hole"
            hole_val = self._current_row.get("hole", "").strip()
            if hole_val and hole_val.lower() != "hole":
                self.rows.append(self._current_row)
            self._row_open = False
            self._current_row = {}

    def handle_data(self, data: str):
        if self._capture:
            self._buf.append(data)


def fetch_layout_detail(tournament_id: str, layout_id: int) -> dict[str, Any]:
    """Fetch one layout's full hole-by-hole detail by scraping courserules HTML."""
    url = f"{BASE}/apps/tournament/manager/{tournament_id}/courserules?LayoutID={layout_id}&Display=details"
    html = _get(url)
    p = _CourseRulesParser()
    p.feed(html)

    detail: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(p.rows, start=1):
        try:
            par = int(row.get("par", "0").strip() or 0)
        except ValueError:
            par = 0
        try:
            length = int(row.get("length", "0").strip() or 0)
        except ValueError:
            length = 0
        detail[str(i)] = {
            "Label": row.get("hole", "").strip(),
            "Tee": row.get("tee", "").strip(),
            "Target": row.get("target", "").strip(),
            "Par": par,
            "Length": length,
            "Notes": row.get("notes", "").strip(),
        }

    return {
        "LayoutTitle": p.title,
        "LayoutName": p.layout_name,
        "GeneralNotes": p.general_notes,
        "Detail": detail,
    }


def fetch_layouts(tournament_id: str) -> dict[str, Any]:
    """Fetch all layouts for a tournament."""
    meta = fetch_event_meta(tournament_id)
    data = meta.get("data") or {}
    layouts_list = data.get("Layouts") or []
    tourn_name = data.get("Name") or ""

    out_layouts: dict[str, dict[str, Any]] = {}
    for layout in layouts_list:
        lid = layout.get("LayoutID")
        if not lid:
            continue
        detail = fetch_layout_detail(tournament_id, lid)

        # Compute totals from detail if event endpoint didn't supply them
        par_total = sum(h["Par"] for h in detail["Detail"].values()) or layout.get("Par") or 0
        length_total = sum(h["Length"] for h in detail["Detail"].values()) or layout.get("Length") or 0
        holes_count = len(detail["Detail"]) or layout.get("Holes") or 0

        out_layouts[str(lid)] = {
            "LayoutID": lid,
            "CourseID": layout.get("CourseID") or 0,
            "CourseName": layout.get("CourseName") or "",
            "Name": layout.get("Name") or detail["LayoutName"],
            "Holes": holes_count,
            "Par": par_total,
            "Length": length_total,
            "Units": "feet",
            "GeneralNotes": detail["GeneralNotes"],
            "Detail": detail["Detail"],
        }

    return {
        "tournament_id": str(tournament_id),
        "tournament_name": tourn_name,
        "layouts": out_layouts,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch PDGA TM layouts (public, no auth required).")
    p.add_argument("tournament_id", help="PDGA tournament ID (e.g. 101284 for Wunderment 26)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    p.add_argument("--summary", action="store_true", help="Print a human-readable summary instead of JSON")
    p.add_argument(
        "--layouts-only",
        action="store_true",
        help="Skip per-layout HTML fetch — return only the layout index from the event API",
    )
    args = p.parse_args()

    if args.layouts_only:
        meta = fetch_event_meta(args.tournament_id)
        data = meta.get("data") or {}
        result = {
            "tournament_id": str(args.tournament_id),
            "tournament_name": data.get("Name", ""),
            "layouts": {
                str(l.get("LayoutID")): {
                    "LayoutID": l.get("LayoutID"),
                    "CourseID": l.get("CourseID"),
                    "CourseName": l.get("CourseName"),
                    "Name": l.get("Name"),
                    "Holes": l.get("Holes"),
                    "Par": l.get("Par"),
                    "Length": l.get("Length"),
                }
                for l in (data.get("Layouts") or [])
                if l.get("LayoutID")
            },
        }
    else:
        result = fetch_layouts(args.tournament_id)

    if args.summary:
        print(f"Tournament {result['tournament_id']}: {result['tournament_name']}")
        print(f"  {len(result['layouts'])} layout(s)")
        for lid, layout in result["layouts"].items():
            name = layout.get("Name", "(unnamed)")
            holes = layout.get("Holes", "?")
            par = layout.get("Par", "?")
            length = layout.get("Length", "?")
            print(f"    [{lid}] {name} — {holes}h, par {par}, {length}ft")
            for h in (layout.get("Detail") or {}).values():
                lbl = h["Label"]
                print(f"        h{lbl:>3}: {h['Tee']:>5} -> {h['Target']}, par {h['Par']}, {h['Length']}ft")
        return 0

    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
