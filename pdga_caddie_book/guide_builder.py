"""Orchestrator for event guides (spectator, competitor).

Guides are per-event (not per-pool). They reuse shared slide builders
from slides.py (schedule, parking, camping, sponsors, etc.) and add
guide-specific slides from guide_slides.py.
"""

from __future__ import annotations

import os
from typing import Callable

from . import guide_slides, slides
from .config import Event, load_event
from .shell import render_guide

SPECTATOR_ORDER = [
    "guide_cover",
    "welcome",
    "schedule",
    "venue_map",
    "etiquette",
    "how_to_watch",
    "courses",
    "info_slides",
    "parking",
    "camping",
    "food_drink",
    "local_rules",
    "sponsors",
    "special_thanks",
    "back_cover",
]

GUIDE_BUILDERS: dict[str, Callable] = {
    "guide_cover": guide_slides.guide_cover,
    "welcome": guide_slides.welcome,
    "etiquette": guide_slides.etiquette,
    "venue_map": guide_slides.venue_map,
    "how_to_watch": guide_slides.how_to_watch,
    "food_drink": guide_slides.food_drink,
    "courses": guide_slides.courses_overview,
    "local_rules": guide_slides.local_rules,
    "info_slides": guide_slides.info_slide,
    "sponsors": guide_slides.guide_sponsors,
    "parking": guide_slides.guide_parking,
    "back_cover": guide_slides.guide_back_cover,
}

SHARED_BUILDERS: dict[str, Callable] = {
    "schedule": slides.schedule,
    "camping": slides.camping,
    "special_thanks": slides.special_thanks,
}


def _expand_one(event: Event, guide_key: str, slide_id: str) -> list[str]:
    if slide_id in GUIDE_BUILDERS:
        result = GUIDE_BUILDERS[slide_id](event, guide_key)
    elif slide_id in SHARED_BUILDERS:
        result = SHARED_BUILDERS[slide_id](event, guide_key)
    else:
        return []
    if isinstance(result, list):
        return [r for r in result if r]
    if result:
        return [result]
    return []


def _resolved_order(event: Event, guide_key: str) -> list[str]:
    cfg = event.guide_config(guide_key) or {}
    return list(cfg.get("slide_order") or SPECTATOR_ORDER)


def build_guide(event: Event, guide_key: str) -> str:
    order = _resolved_order(event, guide_key)
    sections = []
    for slide_id in order:
        sections.extend(_expand_one(event, guide_key, slide_id))
    return render_guide(event, guide_key, "\n".join(sections))


def build_event_guides(
    event_yaml_path: str,
    output_dir: str,
    guide_key: str = "spectator",
    pdga_layouts_path: str | None = None,
) -> list[str]:
    event = load_event(event_yaml_path, pdga_layouts_path=pdga_layouts_path)
    if not event.guide_config(guide_key):
        raise SystemExit(
            f"No `guides.{guide_key}` section found in {event_yaml_path}. "
            f"Add a `guides:` block with a `{guide_key}:` entry to generate this guide."
        )
    os.makedirs(output_dir, exist_ok=True)
    html = build_guide(event, guide_key)
    out_path = os.path.join(output_dir, f"{guide_key}-guide.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return [out_path]
