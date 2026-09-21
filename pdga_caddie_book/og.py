"""Share images (og:image) for each pool's caddie book, rendered from the cover slide.

A caddie book is passed around as a link, so the preview card is the first thing most
players see. The shell already writes `og:image` meta tags from `deploy.og_image_pattern`;
this module makes the files those tags point at. Without them a shared link has no preview.

The card is the cover turned on its side, 1200x630:
- themes with `scenery` (sunset): the painted sky, sun disc, event mark, ridges and pines on
  the left, the cover's text on the dark ground on the right;
- other themes: the event mark on the pool colour on the left, the cover's text on the right.

Rendered with Playwright's Chromium (the same dependency as `pdf`), so the real logo files
and the event's own fonts are used and nothing is generated.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .config import Event, load_event
from .shell import _font_faces
from .slides import RIDGES, _grain, _scenery

OG_W, OG_H = 1200, 630
DEFAULT_PATTERN = "images/og-pool-{pool}.jpg"


def og_relpath(event: Event, pool_key: str) -> str | None:
    """Event-relative path of a pool's share image, or None when no pattern is set."""
    pattern = (event.raw.get("deploy") or {}).get("og_image_pattern")
    return pattern.format(pool=pool_key.lower()) if pattern else None


def book_url(event: Event, pool_key: str) -> str:
    base = ((event.raw.get("deploy") or {}).get("url_base") or "").rstrip("/")
    return f"{base}/{pool_key.lower()}".replace("https://", "").replace("http://", "") if base else ""


def share_warnings(event: Event, pool_keys: list[str]) -> list[str]:
    """What stops a pool's book from showing a preview when its link is shared."""
    deploy = event.raw.get("deploy") or {}
    if not deploy.get("url_base"):
        return ["no deploy.url_base: the books carry no share metadata (og:title, og:image)"]
    if not deploy.get("og_image_pattern"):
        return [f'no deploy.og_image_pattern: shared links will have no preview image. '
                f'Add og_image_pattern: "{DEFAULT_PATTERN}" and run `pdga-caddie-book og`']
    out = []
    for key in pool_keys:
        rel = og_relpath(event, key)
        if rel and not os.path.exists(os.path.join(event.base_dir, rel)):
            out.append(f"missing share image {rel} for pool {key}: run `pdga-caddie-book og`")
    return out


def _logos(event: Event, height: int) -> str:
    brand = event.brand
    imgs = [f'<img src="{event.asset(brand[k])}" style="height:{height}px;">'
            for k in ("org_logo", "venue_logo") if brand.get(k)]
    return f'<div style="display:flex; gap:18px; align-items:center;">{"".join(imgs)}</div>' if imgs else "<div></div>"


def card_html(event: Event, pool_key: str) -> str:
    """The 1200x630 card as a standalone page (asset paths are event-relative)."""
    th, pc = event.theme, event.pool_color(pool_key)
    pool, em, brand = event.pools[pool_key], event.event_meta, event.brand
    uid = f"og{pool_key.lower()}"
    url = book_url(event, pool_key)
    art_w = 600
    # On the dark ground the pool name sits on a pool-colour plate, as on the cover. The light
    # theme's cover is already the pool colour, so there the name is plain type.
    banner = (f'background:{pc["bg"]}; border-top:3px solid {pc["accent"]}; border-bottom:3px solid {pc["accent"]};'
              if th["scenery"] else "")

    text = f"""
      <div style="font-size:22px; font-weight:700; letter-spacing:0.22em; text-transform:uppercase; color:{th["gold"] if th["scenery"] else th["on_pool_muted"]};">{em.get("name", "")} · Caddie Book</div>
      <div style="margin-top:22px; width:100%; box-sizing:border-box; {banner} padding:22px 0 20px; font-size:112px; font-weight:900; text-transform:uppercase; color:{th["on_pool"]}; line-height:1;">{pool.get("name", pool_key)}</div>
      <div style="margin-top:26px; font-size:40px; font-weight:700; color:{th["ink"] if th["scenery"] else th["cover_sub"]};">{em.get("dates", "")}</div>
      <div style="margin-top:12px; font-size:21px; font-weight:700; letter-spacing:0.18em; text-transform:uppercase; color:{th["gold"] if th["scenery"] else th["on_pool_muted"]};">{em.get("tagline", "")}</div>"""

    if th["scenery"]:
        sky_h = 550   # the sun disc clears the ridges at this height with a 316px mark
        ground = th["bg"]
        art = f'<div style="position:absolute; left:0; top:0; width:{art_w}px; height:{sky_h}px; overflow:hidden;">{_scenery(event, uid, sky_h, 316)}</div>'
        text += f'<div style="margin-top:22px; width:200px; height:3px; background:{RIDGES[1]};"></div>'
        footer_h, muted = OG_H - sky_h, th["muted"]
    else:
        ground = pc["bg"]
        mark = ""
        if brand.get("primary_logo"):
            mark = (f'<img src="{event.asset(brand["primary_logo"])}" style="position:absolute; left:{art_w // 2 - 190}px; '
                    f'top:60px; width:380px; height:380px; border-radius:50%; object-fit:cover;">')
        art = mark
        footer_h, muted = 90, th["on_pool_muted"]

    return f"""<!doctype html><html><head><meta charset="utf-8"><base href="{Path(event.base_dir).as_uri()}/">
<style>
    {_font_faces(event)}
    html, body {{ margin:0; background:{ground}; }}
    .c {{ position:relative; width:{OG_W}px; height:{OG_H}px; overflow:hidden; background:{ground}; font-family:{event.font_family_css()}; }}
</style></head><body><div class="c">
  {art}
  <div style="position:absolute; left:{art_w}px; top:0; right:0; bottom:{footer_h // 3}px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;">{text}
  </div>
  <div style="position:absolute; left:0; right:0; bottom:0; height:{footer_h}px; display:flex; align-items:center; justify-content:space-between; padding:0 34px; box-sizing:border-box;">
    {_logos(event, 60)}
    <div style="font-size:24px; font-weight:700; letter-spacing:0.04em; color:{muted};">{url}</div>
  </div>
  {_grain(uid) if th["scenery"] else ""}
</div></body></html>"""


def build_event(
    event_yaml_path: str,
    pdga_layouts_path: str | None = None,
    pool_filter: list[str] | None = None,
    output_dir: str | None = None,
) -> list[str]:
    """Render one share image per pool. Returns the paths written.

    Files land at `deploy.og_image_pattern` under the event directory (so they deploy with
    the rest of the images), or in `output_dir` if given.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise SystemExit(
            "Playwright is required for share images. Install with:\n"
            "    pip install 'pdga-caddie-book[pdf]'\n"
            "    playwright install chromium"
        ) from e

    event = load_event(event_yaml_path, pdga_layouts_path=pdga_layouts_path)
    keys = [k for k in event.pools if not pool_filter or k in pool_filter]
    written: list[str] = []
    with sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": OG_W, "height": OG_H}, device_scale_factor=1)
        for key in keys:
            rel = og_relpath(event, key) or DEFAULT_PATTERN.format(pool=key.lower())
            dest = os.path.join(output_dir, os.path.basename(rel)) if output_dir else os.path.join(event.base_dir, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            page_path = os.path.join(tmp, f"og-{key.lower()}.html")
            with open(page_path, "w", encoding="utf-8") as f:
                f.write(card_html(event, key))
            page = ctx.new_page()
            page.goto(f"file://{page_path}", wait_until="networkidle")
            page.evaluate("document.fonts.ready")   # never screenshot before the event fonts land
            page.screenshot(path=dest, type="jpeg", quality=88, clip={"x": 0, "y": 0, "width": OG_W, "height": OG_H})
            page.close()
            written.append(dest)
        browser.close()
    return written
