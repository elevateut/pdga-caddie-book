"""Orchestrator — composes a full reveal.js deck per pool.

Default slide order:
  cover, schedule, parking, camping, pools, td_welcome, ed_welcome, sponsors,
  rules, [days_and_holes], special_thanks, back_cover

Custom slides defined under `custom_slides` are inserted based on their
`after:` field, which names the slide they should immediately follow.
"""

from __future__ import annotations

import os
from typing import Callable

from . import slides
from .config import Event, load_event
from .shell import render as render_shell

DEFAULT_ORDER = [
    "cover",
    "schedule",
    "parking",
    "camping",
    "pools",
    "td_welcome",
    "ed_welcome",
    "sponsors",
    "rules",
    "days_and_holes",
    "special_thanks",
    "back_cover",
]

# Each builder returns either a single HTML string or a list of HTML strings.
BUILDERS: dict[str, Callable] = {
    "cover": slides.cover,
    "schedule": slides.schedule,
    "parking": slides.parking,
    "camping": slides.camping,
    "pools": slides.pools_overview,
    "td_welcome": slides.td_welcome,
    "ed_welcome": slides.ed_welcome,
    "sponsors": slides.sponsors,
    "rules": slides.rules,
    "special_thanks": slides.special_thanks,
    "back_cover": slides.back_cover,
}


def _build_days_and_holes(event: Event, pool_key: str) -> list[str]:
    """Expand into N day-intro + per-hole slides."""
    pool = event.pools.get(pool_key) or {}
    days = pool.get("days") or []
    out: list[str] = []
    for i, day in enumerate(days):
        repeats = bool(day.get("same_as_previous"))
        out.append(slides.day_intro(event, pool_key, i, repeats_previous=repeats))
        if repeats:
            # Don't re-emit hole slides — Day 1's holes still apply
            continue
        layout = event.layout_for_day(pool_key, i)
        if not layout:
            continue
        total = layout.get("Holes", 0)
        for order, hole in event.hole_rows(layout["LayoutID"]):
            out.append(slides.hole_slide(event, pool_key, i, order, hole, total))
    return out


def _expand_one(event: Event, pool_key: str, slide_id: str) -> list[str]:
    """Run one builder and normalize result to a list of HTML strings."""
    if slide_id == "days_and_holes":
        return _build_days_and_holes(event, pool_key)
    if slide_id.startswith("custom:"):
        return [slides.custom(event, pool_key, slide_id.split(":", 1)[1])]
    builder = BUILDERS.get(slide_id)
    if not builder:
        return []
    result = builder(event, pool_key)
    if isinstance(result, list):
        return [r for r in result if r]
    if result:
        return [result]
    return []


def _resolved_order(event: Event) -> list[str]:
    """Build the final slide order — base order + custom slides injected via `after`."""
    order = list(event.raw.get("slide_order") or DEFAULT_ORDER)
    custom_slides = event.raw.get("custom_slides") or {}
    for cid, cfg in custom_slides.items():
        marker = f"custom:{cid}"
        if marker in order:
            continue
        after = (cfg or {}).get("after")
        if after and after in order:
            idx = order.index(after)
            order.insert(idx + 1, marker)
        else:
            order.append(marker)
    return order


def build_pool(event: Event, pool_key: str) -> str:
    """Render one pool's full HTML caddie book."""
    order = _resolved_order(event)
    sections = []
    for slide_id in order:
        sections.extend(_expand_one(event, pool_key, slide_id))
    return render_shell(event, pool_key, "\n".join(sections))


def build_event(
    event_yaml_path: str,
    output_dir: str,
    pdga_layouts_path: str | None = None,
    pool_filter: list[str] | None = None,
) -> list[str]:
    """Render caddie books for every pool. Returns list of written file paths."""
    event = load_event(event_yaml_path, pdga_layouts_path=pdga_layouts_path)
    os.makedirs(output_dir, exist_ok=True)
    written = []
    for key in event.pools:
        if pool_filter and key not in pool_filter:
            continue
        html = build_pool(event, key)
        out_path = os.path.join(output_dir, f"pool-{key.lower()}-slides.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append(out_path)
    return written
