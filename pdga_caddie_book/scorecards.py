"""Printable duplex scorecard generator.

Each generated file is one Letter-portrait page with 3 stacked scorecards on
the front (cut apart at the dashed lines) and 3 stacked hole-notes cards on
the back. Print duplex, flip on short edge — back is auto-rotated 180° so it
lands right-side-up on each cut card.

Driven by the same event.yaml + PDGA layouts as the slide builder.
"""

from __future__ import annotations

import os
from typing import Any

from .config import Event, load_event

# Lighter stripe shade for alternate player rows; derived from pool.color.light
# at render time by adjusting alpha. For predictability we just match light.
STRIPE_FALLBACK = "#f7f7f7"


def _day_span(pool: dict, day_index: int) -> list[dict]:
    """This day plus the days after it that repeat its layout (same_as_previous).

    One card covers the whole span, so its header names every day it is played.
    """
    days = pool.get("days") or []
    span = [days[day_index]]
    for d in days[day_index + 1:]:
        if not d.get("same_as_previous"):
            break
        span.append(d)
    return span


def _span_label(pool: dict, day_index: int) -> str:
    return " &amp; ".join(d.get("label", "") for d in _day_span(pool, day_index))


def _span_date(pool: dict, day_index: int) -> str:
    return " &amp; ".join(d.get("date", "") for d in _day_span(pool, day_index))


def _single_card(event: Event, pool_key: str, day_index: int) -> str:
    pool = event.pools[pool_key]
    pc = event.pool_color(pool_key)
    layout = event.layout_for_day(pool_key, day_index)
    if not layout:
        return ""

    num_players = pool.get("players_per_card", 5)
    holes = event.hole_rows(layout["LayoutID"])
    total_par = layout.get("Par", sum(h.get("Par", 0) for _, h in holes))
    total_len = layout.get("Length", sum(h.get("Length", 0) for _, h in holes))
    nholes = len(holes)

    hole_num_cells = "".join(f'<th class="hole-col">{h.get("Label", o)}</th>' for o, h in holes)
    tee_cells = "".join(f'<td class="info-cell tee-cell">{h.get("Tee", "")}</td>' for _, h in holes)
    target_cells = "".join(f'<td class="info-cell target-cell">{h.get("Target", "")}</td>' for _, h in holes)
    par_cells = "".join(f'<td class="info-cell par-cell">{h.get("Par", "")}</td>' for _, h in holes)
    dist_cells = "".join(f'<td class="info-cell dist-cell">{h.get("Length", "")}</td>' for _, h in holes)

    player_rows = ""
    for _ in range(num_players):
        score_cells = "".join('<td class="score-cell"></td>' for _ in holes)
        player_rows += f'<tr class="player-row"><td class="name-cell"></td>{score_cells}<td class="score-cell total-score"></td></tr>\n'

    em = event.event_meta
    title = f'{em.get("name", "Tournament")} &mdash; {pool.get("name", pool_key)}'
    meta = f'{_span_label(pool, day_index)} &bull; {_span_date(pool, day_index)} &bull; {nholes}h &bull; Par {total_par} &bull; {total_len:,}ft'

    return f"""<div class="card">
  <div class="card-header">
    <div class="card-title">{title}</div>
    <div class="card-meta">{meta}</div>
  </div>
  <table>
    <tr>
      <th class="label-col" rowspan="4"></th>
      {hole_num_cells}
      <th class="total-header" rowspan="4">Tot</th>
    </tr>
    <tr class="info-row">{tee_cells}</tr>
    <tr class="info-row">{target_cells}</tr>
    <tr class="info-row">{par_cells}</tr>
    <tr class="dist-row">
      <th class="name-header">Player</th>
      {dist_cells}
      <td class="total-info">{total_par}</td>
    </tr>
    {player_rows}
  </table>
</div>"""


def _notes_card(event: Event, pool_key: str, day_index: int) -> str:
    pool = event.pools[pool_key]
    pc = event.pool_color(pool_key)
    layout = event.layout_for_day(pool_key, day_index)
    if not layout:
        return ""

    holes = event.hole_rows(layout["LayoutID"])

    rows = "\n".join(
        f'<div class="note-row"><span class="note-hole">{h.get("Label", o)}</span>'
        f'<span class="note-text">{h.get("Notes", "")}</span></div>'
        for o, h in holes
    )

    em = event.event_meta
    title = f'{em.get("name", "Tournament")} &mdash; {pool.get("name", pool_key)}'
    rules = event.raw.get("rules") or {}
    creek_item = next((i for i in (rules.get("items") or []) if (i.get("label") or "").lower() == "creek"), None)
    creek_text = "OB"
    if creek_item:
        creek_text = (creek_item.get("text_by_pool") or {}).get(pool_key) or creek_item.get("text", "OB")
    meta = f'{_span_label(pool, day_index)} &bull; Hole Notes &bull; Creek = {creek_text} &bull; Roads = OB'

    return f"""<div class="card notes-card">
  <div class="card-header">
    <div class="card-title">{title}</div>
    <div class="card-meta">{meta}</div>
  </div>
  <div class="notes-columns">{rows}</div>
</div>"""


def _full_page(event: Event, pool_key: str, day_index: int) -> str:
    pc = event.pool_color(pool_key)
    light = pc.get("light", "#f5f5f5")
    stripe = pc.get("stripe") or _derive_stripe(light)

    card = _single_card(event, pool_key, day_index)
    notes = _notes_card(event, pool_key, day_index)
    front = card + "\n" + card + "\n" + card
    back = notes + "\n" + notes + "\n" + notes

    pool = event.pools[pool_key]
    em = event.event_meta
    title = f'{em.get("name", "Tournament")} — {pool.get("name", pool_key)} {_span_label(pool, day_index).replace("&amp;", "&")} Scorecard'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    /* Letter portrait at 0.25"/0.3" margins → printable area = 7.9in × 10.5in.
       We size everything in inches so the browser viewport measurements match
       the print page exactly — JS auto-fit logic is then accurate. */
    @page {{ size: letter portrait; margin: 0.25in 0.3in; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ width: 7.9in; }}
    body {{
      font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
      font-size: 9px; color: #1a1a1a;
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }}
    .page {{ width: 7.9in; height: 10.5in; margin: 0 auto; display: flex; flex-direction: column; }}
    .card {{ height: calc(10.5in / 3 - 4px); display: flex; flex-direction: column; border-bottom: 1px dashed #ccc; }}
    .card:last-child {{ border-bottom: none; }}
    .card-header {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 3px; border-bottom: 2px solid {pc["bg"]}; padding-bottom: 2px; }}
    .card-title {{ font-size: 11px; font-weight: 900; text-transform: uppercase; color: {pc["bg"]}; letter-spacing: 0.02em; white-space: nowrap; }}
    .card-meta {{ font-size: 8px; color: #777; white-space: nowrap; }}
    table {{ width: 100%; border-collapse: collapse; flex: 1; table-layout: fixed; }}
    th, td {{ border: 1px solid #bbb; text-align: center; vertical-align: middle; }}
    .label-col {{ width: 160px; min-width: 160px; background: {pc["bg"]}; color: #fff; font-weight: 700; font-size: 6px; letter-spacing: 0.06em; text-transform: uppercase; padding: 1px 2px; border-color: {pc["bg"]}; }}
    .hole-col {{ background: {pc["bg"]}; color: #fff; font-weight: 900; font-size: 9px; padding: 2px 0; border-color: {pc["bg"]}; height: 18px; }}
    .info-row td, .info-row th {{ height: 14px; }}
    .dist-row td, .dist-row th {{ height: 18px; }}
    .info-cell {{ padding: 1px 0; font-size: 8px; background: {light}; }}
    .tee-cell {{ font-size: 7px; font-weight: 600; color: #555; text-transform: uppercase; }}
    .target-cell {{ font-size: 8px; font-weight: 700; color: {pc["bg"]}; text-transform: uppercase; }}
    .par-cell {{ font-weight: 800; color: {pc["bg"]}; font-size: 9px; }}
    .dist-cell {{ font-size: 10px; font-weight: 700; color: #333; }}
    .name-header {{ width: 160px; min-width: 160px; background: {pc["bg"]}; color: #fff; font-weight: 700; font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; padding: 2px 6px; border-color: {pc["bg"]}; text-align: left; }}
    .name-cell {{ width: 160px; min-width: 160px; text-align: left; padding: 2px 6px; font-size: 12px; }}
    .total-header {{ background: {pc["bg"]}; color: #fff; font-weight: 700; font-size: 7px; letter-spacing: 0.04em; text-transform: uppercase; padding: 2px 1px; border-color: {pc["bg"]}; width: 28px; min-width: 28px; }}
    .total-info {{ background: {light}; font-weight: 800; font-size: 9px; color: {pc["bg"]}; padding: 1px; }}
    .total-score {{ background: {light}; font-weight: 900; }}
    .player-row:nth-child(even) .score-cell {{ background: {stripe}; }}
    .player-row:nth-child(even) .name-cell {{ background: {stripe}; }}
    .player-row:nth-child(even) .total-score {{ background: {light}; }}
    .notes-card {{ padding: 0 4px; position: relative; overflow: hidden; }}
    .notes-columns {{ font-size: 10px; line-height: 1.3; }}
    /* Each hole's note is its own block — lets CSS multi-column flow them
       across columns when the .two-col fallback engages. */
    .note-row {{
      break-inside: avoid;
      padding: 0.25em 0.4em;
      border-bottom: 1px solid #ddd;
      color: #333;
      text-align: left;
    }}
    .note-hole {{
      font-weight: 900;
      font-size: 1.25em;
      color: {pc["bg"]};
      margin-right: 0.5em;
      display: inline-block;
      min-width: 1.8em;
    }}
    .note-text {{ font-size: 1em; }}
    .page-break {{ page-break-after: always; break-after: page; }}

    /* Back: each notes card stays in the same horizontal strip as its front
       counterpart (so cuts line up), but the notes content is rotated 90°
       within each strip — read by turning the cut card sideways.
       Card box = 7.9in wide × ~3.4in tall. Pre-rotation, size the column
       swap-side (3.3in wide × 7.7in tall) so the post-rotation bounding box
       (7.7in wide × 3.3in tall) fits the card with a small breathing margin. */
    .back-page .notes-card .notes-columns {{
      position: absolute;
      top: 50%;
      left: 50%;
      width: 3.3in;
      height: 7.7in;
      transform: translate(-50%, -50%) rotate(90deg);
      transform-origin: center center;
      /* Single column, rows stretched to fill the entire container vertically.
         space-between distributes any leftover space evenly between rows so
         the content always reaches both the top and bottom edges — zero
         trailing whitespace regardless of content length. */
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .back-page .notes-card .card-header {{ display: none; }}
    /* Each note row clears its own border so the dividers reach edge-to-edge
       and the visual rhythm of the strip is consistent. */
    .back-page .notes-card .note-row:last-child {{ border-bottom: none; }}
    @media print {{ body {{ margin: 0; }} .page {{ max-width: none; }} }}
  </style>
</head>
<body>
  <div class="page page-break">
{front}
  </div>
  <div class="page back-page">
{back}
  </div>
  <script>
    // Auto-fit each rotated notes column: find the LARGEST font size where
    // all rows still fit inside the container. Combined with the CSS
    // `justify-content: space-between` rule, this means the content always
    // reaches both edges — there is no trailing whitespace.
    //
    // Algorithm: binary search the font-size range [MIN, MAX]. For each
    // candidate, measure scrollHeight vs clientHeight (the post-CSS-rotation
    // layout box, which is what the print PDF will use). Settle on the
    // largest size that doesn't overflow.
    //
    // Runs on `load` so fonts/images are resolved before measurement.
    function fitNotesText() {{
      var cards = document.querySelectorAll('.back-page .notes-card .notes-columns');
      var anyOverflow = false;
      var MIN = 4;
      var MAX = 24;
      var STEP = 0.25;

      function fits(cols, size) {{
        cols.style.fontSize = size + 'px';
        return cols.scrollHeight <= cols.clientHeight;
      }}

      cards.forEach(function (cols) {{
        // Binary search the largest size that fits
        var lo = MIN, hi = MAX, best = MIN;
        while (hi - lo > STEP) {{
          var mid = Math.round(((lo + hi) / 2) / STEP) * STEP;
          if (fits(cols, mid)) {{ best = mid; lo = mid; }}
          else {{ hi = mid; }}
        }}
        // Re-apply the best size for final layout
        cols.style.fontSize = best + 'px';
        cols.setAttribute('data-fit-size', best);
        if (best <= MIN && cols.scrollHeight > cols.clientHeight) {{
          cols.setAttribute('data-fit-overflow', '1');
          anyOverflow = true;
        }}
      }});
      if (anyOverflow) {{
        document.documentElement.setAttribute('data-fit-overflow', '1');
      }}
      document.documentElement.setAttribute('data-fit-done', '1');
    }}
    if (document.readyState === 'complete') {{ fitNotesText(); }}
    else {{ window.addEventListener('load', fitNotesText); }}
  </script>
</body>
</html>"""


def _derive_stripe(light: str) -> str:
    """Approximate a paler stripe color from the pool light bg.

    `light` is a hex color; we lighten it ~50% toward white. Not perfect, but
    avoids requiring colorsys and keeps the schema simple.
    """
    if not light.startswith("#") or len(light) != 7:
        return STRIPE_FALLBACK
    try:
        r = int(light[1:3], 16)
        g = int(light[3:5], 16)
        b = int(light[5:7], 16)
    except ValueError:
        return STRIPE_FALLBACK
    r = min(255, r + (255 - r) // 2)
    g = min(255, g + (255 - g) // 2)
    b = min(255, b + (255 - b) // 2)
    return f"#{r:02x}{g:02x}{b:02x}"


def build_event(
    event_yaml_path: str,
    output_dir: str,
    pdga_layouts_path: str | None = None,
    pool_filter: list[str] | None = None,
) -> list[str]:
    """Render scorecards for every pool/day. Returns list of written file paths."""
    event = load_event(event_yaml_path, pdga_layouts_path=pdga_layouts_path)
    os.makedirs(output_dir, exist_ok=True)
    written = []
    for key, pool in event.pools.items():
        if pool_filter and key not in pool_filter:
            continue
        # A day that repeats the previous day's layout gets no card of its own: the
        # earlier card covers it, and its header names both days (see _day_span).
        for i, day in enumerate(pool.get("days") or []):
            if day.get("same_as_previous"):
                continue
            html = _full_page(event, key, i)
            n = len(_day_span(pool, i))
            days_part = f"day{i + 1}" if n == 1 else f"day{i + 1}-{i + n}"
            fname = f"scorecard-{key.lower()}-{days_part}.html"
            out_path = os.path.join(output_dir, fname)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)
            written.append(out_path)
    return written
