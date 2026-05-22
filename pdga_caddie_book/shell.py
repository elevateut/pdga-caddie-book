"""Outer reveal.js HTML shell — head/meta/css/init script wrapped around slides."""

from __future__ import annotations

from .config import Event

REVEAL_VERSION = "5.1.0"
REVEAL_BASE = f"https://cdn.jsdelivr.net/npm/reveal.js@{REVEAL_VERSION}/dist"


def _font_faces(event: Event) -> str:
    """Generate @font-face declarations from brand.fonts entries."""
    fonts = (event.brand.get("fonts") or [])
    if isinstance(fonts, dict):
        fonts = [fonts]
    lines = []
    for f in fonts:
        if not isinstance(f, dict):
            continue
        if not f.get("file") or not f.get("family"):
            continue
        fmt = "opentype" if f["file"].endswith(".otf") else "truetype"
        weight = f.get("weight", 400)
        lines.append(
            f'@font-face {{ font-family: "{f["family"]}"; '
            f'src: url("{f["file"]}") format("{fmt}"); '
            f"font-weight: {weight}; }}"
        )
    return "\n    ".join(lines)


def render(event: Event, pool_key: str, slides_html: str) -> str:
    pc = event.pool_color(pool_key)
    em = event.event_meta
    pool = event.pools.get(pool_key) or {}
    pool_slug = pool_key.lower()
    deploy = event.raw.get("deploy") or {}
    url_base = (deploy.get("url_base") or "").rstrip("/")
    og_pattern = deploy.get("og_image_pattern") or ""
    og_image = og_pattern.format(pool=pool_slug) if og_pattern else ""
    og_url = f"{url_base}/{pool_slug}" if url_base else ""

    title = f'{em.get("name", "")} — {pool.get("name", pool_key)} Caddie Book'
    description = em.get("description") or em.get("tagline") or ""
    social_desc = em.get("tagline") or em.get("description") or ""

    font_family = event.font_family_css()
    font_faces = _font_faces(event)

    og_meta = ""
    if og_image and og_url:
        og_meta = f"""  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{social_desc}">
  <meta property="og:image" content="{url_base}/{og_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:url" content="{og_url}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{social_desc}">
  <meta name="twitter:image" content="{url_base}/{og_image}">"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
{og_meta}
  <link rel="stylesheet" href="{REVEAL_BASE}/reveal.css">
  <link rel="stylesheet" href="{REVEAL_BASE}/theme/white.css">
  <style>
    {font_faces}
    :root {{ --r-main-font: {font_family}; --r-heading-font: {font_family}; }}
    html, body {{ background: #0c1116; margin: 0; padding: 0; height: 100%; overflow: hidden; }}
    .reveal {{ font-family: {font_family}; }}
    .reveal .slides {{ text-align: center; }}
    .reveal .slides section {{
      padding: 14px 14px 36px !important;
      box-sizing: border-box;
      height: 100% !important;
      overflow-y: auto;
      overflow-x: hidden;
      -webkit-overflow-scrolling: touch;
    }}
    .reveal .slides p {{ line-height: 1.45; }}
    .reveal .progress {{ color: {pc["accent"]}; height: 4px; }}
    .reveal .controls {{ color: {pc["accent"]}; bottom: 4px !important; right: 4px !important; }}
    .reveal .controls button {{ width: 32px; height: 32px; }}
    .reveal p {{ margin: 0; }}
    .reveal .slides section::-webkit-scrollbar {{ display: none; }}
    .reveal .slides section {{ scrollbar-width: none; }}
  </style>
</head>
<body>
  <div class="reveal">
    <div class="slides">
{slides_html}
    </div>
  </div>
  <script src="{REVEAL_BASE}/reveal.js"></script>
  <script>
    Reveal.initialize({{
      hash: true,
      touch: true,
      controls: true,
      progress: true,
      center: false,
      transition: 'slide',
      width: window.innerWidth,
      height: window.innerHeight,
      margin: 0,
      minScale: 1,
      maxScale: 1,
    }});
    window.addEventListener('resize', () => {{
      Reveal.configure({{ width: window.innerWidth, height: window.innerHeight }});
      Reveal.layout();
    }});
  </script>
</body>
</html>"""
