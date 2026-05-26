"""Event configuration — load event.yaml, merge with PDGA layout data.

The Event class is a thin wrapper around the parsed YAML dict, plus helpers
that handle the cross-cutting concerns:

  - Resolving asset paths relative to the event.yaml file
  - Looking up a hole's effective fields (PDGA → overrides → defaults)
  - Resolving the right hole image (per-pool / per-layout overrides)
  - Skipping the rendering of "Day 2" content when a pool repeats Day 1
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_POOL_COLOR = {
    "bg": "#2C3E50",
    "accent": "#4A6FA5",
    "light": "#E8EEF5",
    "name": "Default",
}

DEFAULT_NO_MAP_HOLES: list[str] = []
DEFAULT_IMAGE_PATTERN = "hole_{hole:02d}.jpg"
DEFAULT_FONT_FAMILY = "system-ui, -apple-system, Helvetica, Arial, sans-serif"

# Map YAML-idiomatic lowercase override keys → PDGA's response casing.
# Anything not in this map passes through unchanged.
_OVERRIDE_KEY_MAP = {
    "notes": "Notes",
    "par": "Par",
    "length": "Length",
    "tee": "Tee",
    "target": "Target",
    "label": "Label",
}


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------
@dataclass
class Event:
    """Parsed event.yaml + PDGA layout data, with helper accessors."""

    raw: dict[str, Any]
    pdga: dict[str, Any]
    base_dir: str  # directory containing event.yaml (asset paths resolved from here)
    output_assets_subdir: str = "images"  # where images live, relative to output

    # ---- top-level shortcuts ----

    @property
    def event_meta(self) -> dict[str, Any]:
        return self.raw.get("event") or {}

    @property
    def brand(self) -> dict[str, Any]:
        return self.raw.get("brand") or {}

    @property
    def pools(self) -> dict[str, dict[str, Any]]:
        return self.raw.get("pools") or {}

    @property
    def hole_overrides(self) -> dict[str, dict[str, Any]]:
        return self.raw.get("hole_overrides") or {}

    @property
    def images_cfg(self) -> dict[str, Any]:
        return self.raw.get("images") or {}

    @property
    def pdga_layouts(self) -> dict[str, dict[str, Any]]:
        return (self.pdga or {}).get("layouts") or {}

    # ---- asset path resolution ----

    def asset(self, relpath: str | None) -> str | None:
        """Translate an event-relative path into an output-relative one.

        We currently emit asset paths exactly as written in the YAML — the user
        is responsible for placing them at the right path in the output dir.
        This indirection exists so we can later add absolute-path rewriting,
        copy-on-build, etc.
        """
        if not relpath:
            return None
        return relpath

    def font_family_css(self) -> str:
        return self.brand.get("font_family_css") or DEFAULT_FONT_FAMILY

    # ---- layout / hole accessors ----

    def layout_for_day(self, pool_key: str, day_index: int) -> dict[str, Any] | None:
        """Resolve the PDGA layout dict for a given pool's day."""
        pool = self.pools.get(pool_key) or {}
        days = pool.get("days") or []
        if day_index >= len(days):
            return None
        layout_id = str(days[day_index].get("layout_id") or "")
        return self.pdga_layouts.get(layout_id)

    def hole_image(
        self,
        course_hole: str,
        pool_key: str,
        layout_id: str | int | None,
    ) -> str | None:
        """Resolve the hole image filename for a hole — honors all overrides.

        Order of precedence:
            1. per_layout override (most specific)
            2. per_pool override
            3. default pattern (e.g. "hole_03.jpg")

        Returns None if the hole is in `no_map_holes`.
        """
        cfg = self.images_cfg
        base_dir = cfg.get("base_dir") or "images"
        no_map = cfg.get("no_map_holes") or DEFAULT_NO_MAP_HOLES
        if course_hole in no_map:
            return None

        # per_layout override
        per_layout = (cfg.get("per_layout") or {}).get(str(layout_id) or "")
        if per_layout and course_hole in per_layout:
            return f"{base_dir}/{per_layout[course_hole]}"

        # per_pool override
        per_pool = (cfg.get("per_pool") or {}).get(pool_key)
        if per_pool and course_hole in per_pool:
            return f"{base_dir}/{per_pool[course_hole]}"

        # default pattern — only applies to numeric hole labels
        pattern = cfg.get("default_pattern") or DEFAULT_IMAGE_PATTERN
        try:
            num = int(course_hole)
            return f"{base_dir}/{pattern.format(hole=num)}"
        except ValueError:
            return None

    def hole_for(
        self,
        layout_id: str | int,
        display_order: str | int,
    ) -> dict[str, Any]:
        """Return the merged hole dict (PDGA + overrides) for one hole.

        Override keys are normalized to PDGA's casing (`notes` → `Notes`),
        so users can write idiomatic lowercase YAML without it silently
        falling through.
        """
        layout = self.pdga_layouts.get(str(layout_id)) or {}
        pdga_hole = (layout.get("Detail") or {}).get(str(display_order)) or {}
        overrides = (self.hole_overrides.get(str(layout_id)) or {}).get(str(display_order)) or {}
        normalized = {_OVERRIDE_KEY_MAP.get(k, k): v for k, v in overrides.items()}
        return {**pdga_hole, **normalized}

    def hole_rows(self, layout_id: str | int) -> list[tuple[str, dict[str, Any]]]:
        """Yield (display_order, merged_hole) pairs in PDGA order."""
        layout = self.pdga_layouts.get(str(layout_id)) or {}
        detail = layout.get("Detail") or {}
        out = []
        # PDGA returns string keys ordered 1..N
        for order in sorted(detail.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            out.append((order, self.hole_for(layout_id, order)))
        return out

    # ---- color helpers ----

    def pool_color(self, key: str) -> dict[str, str]:
        """Color scheme for a pool or guide key."""
        c = (self.pools.get(key) or {}).get("color") or {}
        if not c:
            c = (self.guide_config(key) or {}).get("color") or {}
        return {**DEFAULT_POOL_COLOR, **c}

    def guide_config(self, guide_key: str) -> dict[str, Any] | None:
        """Return the config dict for a guide (spectator, competitor, etc.)."""
        return (self.raw.get("guides") or {}).get(guide_key)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_event_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_pdga_layouts(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_event(
    event_yaml_path: str,
    pdga_layouts_path: str | None = None,
) -> Event:
    """Load event.yaml and the matching PDGA layouts JSON.

    If `pdga_layouts_path` is None, looks for `layouts.json` next to the YAML.
    If that doesn't exist either, fetches fresh from PDGA TM using the
    `event.pdga_tournament_id` field.
    """
    raw = load_event_yaml(event_yaml_path)
    base_dir = os.path.dirname(os.path.abspath(event_yaml_path))

    # Resolve PDGA data
    if pdga_layouts_path is None:
        candidate = os.path.join(base_dir, "layouts.json")
        if os.path.exists(candidate):
            pdga_layouts_path = candidate

    if pdga_layouts_path and os.path.exists(pdga_layouts_path):
        pdga = load_pdga_layouts(pdga_layouts_path)
    else:
        tournament_id = (raw.get("event") or {}).get("pdga_tournament_id")
        if not tournament_id:
            # No PDGA data needed — guide-only builds work without layouts
            pdga = {"layouts": {}}
        else:
            from . import pdga as pdga_mod
            pdga = pdga_mod.fetch_layouts(str(tournament_id))

    return Event(raw=raw, pdga=pdga, base_dir=base_dir)
