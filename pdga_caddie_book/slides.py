"""Individual slide builders — pure functions returning HTML `<section>` strings.

Each builder takes the Event + the pool key being built and returns one
`<section>` of reveal.js markup. The builder.py module composes the final
slide deck by calling these in the configured order.

Styling is inline — keeps the output self-contained and avoids CSS conflicts
when embedded in a host page (a future feature).
"""

from __future__ import annotations

from typing import Any

from .config import Event




# ---------------------------------------------------------------------------
# Small style helpers
# ---------------------------------------------------------------------------
def _section(content: str, bg: str) -> str:
    return f'<section data-background-color="{bg}">{content}</section>'


def _eyebrow(text: str, color: str) -> str:
    return (
        f'<div style="font-size:15px; font-weight:700; letter-spacing:0.16em; '
        f'text-transform:uppercase; color:{color}; margin-bottom:6px;">{text}</div>'
    )


def _title(text: str, th: dict) -> str:
    return (
        f'<div style="font-size:30px; font-weight:900; text-transform:uppercase; '
        f'color:{th["ink"]}; margin-bottom:10px;">{text}</div>'
    )


def _panel(th: dict, pc: dict) -> tuple[str, str, str]:
    """Card fill, heading colour and body colour.

    A light theme tints the card with the pool colour and keeps the page's own text
    colours. A dark theme sets `panel`/`on_panel` and both text roles collapse to it.
    """
    return th["panel"] or pc["light"], th["on_panel"] or th["ink"], th["on_panel"] or th["body"]


def _divider(th: dict, color: str | None = None) -> str:
    bg = color if color else th["gradient"]
    return f'<div style="width:60px; height:3px; background:{bg}; margin:0 auto 16px;"></div>'



# ---------------------------------------------------------------------------
# Painted scenery (themes with `scenery: true`)
# ---------------------------------------------------------------------------
# The Wunderfall sunset: stepped bands, a cream sun disc behind the event mark,
# three ridges, a pine strip and a grain wash. Values are lifted from the 2026
# poster; see Events/wunderfall-26/BRAND-GUIDE.md.
BANDS = ("#3d1811", "#742818", "#a83a1d", "#d0571f", "#ea7d2c", "#f39c3a", "#f6b04a")
RIDGES = ("#e08a3c", "#b9451f", "#6b2617")


def _bands_css(height: int) -> str:
    """Hard-edged sunset bands over `height` px, darkest at the top."""
    stops, y = [], 0
    for i, c in enumerate(BANDS):
        h = round(height * (0.128 if i < len(BANDS) - 1 else 0.232))
        stops.append(f"{c} {y}px, {c} {y + h}px")
        y += h
    return f"linear-gradient(180deg, {', '.join(stops)})"


def _scenery(event: Event, uid: str, height: int, logo_px: int) -> str:
    """Sky band + sun disc + event mark + ridges + trees, absolutely placed."""
    brand = event.brand
    ridge_h, tree_h = round(height * 0.28), round(height * 0.10)
    mark = ""
    if brand.get("primary_logo"):
        d = logo_px
        mark = (
            f'<div style="position:absolute; left:50%; top:{round(height * 0.12)}px; width:{d + 12}px; height:{d + 12}px; '
            f'margin-left:-{(d + 12) // 2}px; border-radius:50%; background:#f9e3a8;"></div>'
            f'<img src="{event.asset(brand["primary_logo"])}" alt="" style="position:absolute; left:50%; '
            f'top:{round(height * 0.12) + 6}px; width:{d}px; height:{d}px; margin-left:-{d // 2}px; display:block;">'
        )
    ridge_pts = (
        '<polygon fill="%s" points="0,80 70,20 130,95 200,130 280,148 400,155 520,140 640,160 760,145 880,165 1000,135 1080,85 1140,45 1200,90 1200,300 0,300"></polygon>'
        '<polygon fill="%s" points="0,150 120,128 240,172 360,192 480,178 600,205 720,182 840,208 960,180 1080,145 1200,170 1200,300 0,300"></polygon>'
        '<polygon fill="%s" points="0,210 150,190 300,228 450,212 600,238 750,218 900,244 1050,224 1200,205 1200,300 0,300"></polygon>' % RIDGES
    )
    return f"""
      <div style="position:absolute; left:0; top:0; width:100%; height:{height}px; background:{_bands_css(height)};"></div>
      {mark}
      <svg viewBox="0 0 1200 300" preserveAspectRatio="none" style="position:absolute; left:0; top:{height - ridge_h}px; width:100%; height:{ridge_h}px; display:block;">{ridge_pts}</svg>
      <svg viewBox="0 0 1200 100" preserveAspectRatio="none" style="position:absolute; left:0; top:{height - tree_h}px; width:100%; height:{tree_h}px; display:block;">
        <defs><pattern id="tr-{uid}" x="0" y="0" width="64" height="100" patternUnits="userSpaceOnUse">
          <polygon fill="#1b140f" points="18,8 24,30 21,30 29,52 25,52 34,76 2,76 11,52 7,52 15,30 12,30"></polygon>
          <polygon fill="#1b140f" points="50,30 55,48 52,48 59,66 56,66 63,80 37,80 44,66 41,66 48,48 45,48"></polygon>
          <rect fill="#1b140f" x="0" y="76" width="64" height="24"></rect>
        </pattern></defs>
        <rect fill="url(#tr-{uid})" x="0" y="0" width="1200" height="100"></rect>
      </svg>"""


def _grain(uid: str) -> str:
    return (
        f'<svg style="position:absolute; left:0; top:0; width:100%; height:100%; pointer-events:none; '
        f'mix-blend-mode:multiply; opacity:0.16;" preserveAspectRatio="none">'
        f'<filter id="gr-{uid}"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="7" stitchTiles="stitch"></feTurbulence>'
        f'<feColorMatrix type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.25  0 0 0 0 0.2  0 0 0 1 0"></feColorMatrix></filter>'
        f'<rect width="100%" height="100%" filter="url(#gr-{uid})"></rect></svg>'
    )


# ---------------------------------------------------------------------------
# Cover / back cover
# ---------------------------------------------------------------------------
def cover(event: Event, pool_key: str) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    pool = event.pools[pool_key]
    em = event.event_meta
    brand = event.brand

    org_logos = ""
    if brand.get("org_logo") or brand.get("venue_logo"):
        logos = []
        if brand.get("org_logo"):
            logos.append(f'<img src="{event.asset(brand["org_logo"])}" style="height:56px;">')
        if brand.get("venue_logo"):
            logos.append(f'<img src="{event.asset(brand["venue_logo"])}" style="height:56px;">')
        org_logos = (
            '<div style="display:flex; gap:24px; align-items:center; justify-content:center;">'
            + "".join(logos)
            + "</div>"
        )

    primary = ""
    if brand.get("primary_logo"):
        primary = (
            f'<img src="{event.asset(brand["primary_logo"])}" '
            'style="width:240px; border-radius:50%;">'
        )

    if th["scenery"]:
        # Sky over the top half, then a solid plate carrying the pool name and the marks.
        inner = f"""
      <div style="position:absolute; left:0; top:0; right:0; bottom:0; overflow:hidden;">
        {_scenery(event, f"cv{pool_key.lower()}", 470, 258)}
        <div style="position:absolute; left:0; top:470px; right:0; bottom:0; background:{th["bg"]}; display:flex; flex-direction:column; align-items:center; text-align:center; padding:26px 14px 16px; box-sizing:border-box;">
          <div style="font-size:15px; font-weight:700; letter-spacing:0.22em; text-transform:uppercase; color:{th["gold"]};">{em.get("name", "")}</div>
          <div style="margin-top:14px; width:100%; background:{pc["bg"]}; border-top:2px solid {pc["accent"]}; border-bottom:2px solid {pc["accent"]}; padding:14px 0; font-size:60px; font-weight:900; text-transform:uppercase; color:{th["on_pool"]}; line-height:1;">{pool.get("name", pool_key)}</div>
          <div style="margin-top:16px; font-size:22px; font-weight:700; color:{th["ink"]};">{em.get("dates", "")}</div>
          <div style="margin-top:8px; font-size:15px; font-weight:700; letter-spacing:0.18em; text-transform:uppercase; color:{th["gold"]};">{em.get("tagline", "")}</div>
          <div style="margin-top:14px; width:180px; height:2px; background:#b9451f;"></div>
          <div style="margin-top:auto; display:flex; flex-direction:column; align-items:center; gap:12px;">
            {org_logos}
            <div style="font-size:15px; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; color:{th["muted"]};">Swipe to navigate &rarr;</div>
          </div>
        </div>
        {_grain(f"cv{pool_key.lower()}")}
      </div>"""
        return _section(inner, th["bg"])

    inner = f"""
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:space-between; height:calc(100vh - 60px); padding:8px 0;">
        {primary}
        <div>
          <div style="font-size:20px; font-weight:700; letter-spacing:0.18em; text-transform:uppercase; color:{pc["accent"]};">{em.get("name", "")}</div>
          <div style="font-size:72px; font-weight:900; text-transform:uppercase; color:{th["on_pool"]}; line-height:1; margin:12px 0;">{pool.get("name", pool_key)}</div>
          <div style="font-size:28px; color:{th["cover_sub"]}; margin-bottom:14px;">{em.get("dates", "")}</div>
          <div style="font-size:15px; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:{pc["accent"]};">{em.get("tagline", "")}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:14px;">
          {org_logos}
          <div style="font-size:15px; color:rgba(255,255,255,0.5);">Swipe to navigate &rarr;</div>
        </div>
      </div>"""
    return _section(inner, pc["bg"])


def back_cover(event: Event, pool_key: str) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    brand = event.brand
    bc = event.raw.get("back_cover") or {}

    primary = ""
    if brand.get("primary_logo"):
        primary = (
            f'<img src="{event.asset(brand["primary_logo"])}" '
            'style="width:240px; border-radius:50%;">'
        )

    org_logos = ""
    logos = []
    if brand.get("org_logo"):
        logos.append(f'<img src="{event.asset(brand["org_logo"])}" style="height:56px;">')
    if brand.get("venue_logo"):
        logos.append(f'<img src="{event.asset(brand["venue_logo"])}" style="height:56px;">')
    if logos:
        org_logos = (
            '<div style="display:flex; gap:24px; align-items:center; justify-content:center;">'
            + "".join(logos)
            + "</div>"
        )

    url_link = ""
    if bc.get("url"):
        text = bc.get("url_text") or bc["url"].replace("https://", "").rstrip("/")
        url_link = (
            f'<a href="{bc["url"]}" target="_blank" rel="noopener" '
            f'style="font-size:20px; font-weight:700; color:{th["cover_sub"]}; letter-spacing:0.06em; '
            f'text-decoration:underline;">{text}</a>'
        )

    ground = th["bg"] if th["scenery"] else pc["bg"]
    inner = f"""
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:space-between; height:calc(100vh - 60px); padding:8px 0;">
        {primary}
        <div style="text-align:center;">
          <div style="font-size:30px; font-weight:900; color:{th["on_pool"]}; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">{bc.get("headline", "")}</div>
          <div style="font-size:16px; color:{th["on_pool_muted"]};">{bc.get("subhead", "")}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:18px;">
          {org_logos}
          {url_link}
        </div>
      </div>"""
    return _section(inner, ground)


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
def schedule(event: Event, pool_key: str) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    sched = event.raw.get("schedule") or []
    if not sched:
        return ""

    blocks = []
    for day in sched:
        rows = []
        for ev in day.get("events", []):
            rows.append(
                f'<div style="padding:5px 0; border-bottom:1px solid {th["hairline"]};">'
                f'<strong>{ev.get("time", "")}</strong> &mdash; {ev.get("text", "")}</div>'
            )
        # Last row gets no bottom border
        if rows:
            rows[-1] = rows[-1].replace(f'border-bottom:1px solid {th["hairline"]};', "")
        blocks.append(
            f'<div style="font-weight:900; font-size:22px; color:{pc["accent"]}; margin-bottom:4px;">'
            f'{day.get("day", "")}</div>'
            + "".join(rows)
            + '<div style="height:10px;"></div>'
        )

    name = event.event_meta.get("name", "")
    inner = f"""
      {_eyebrow("Schedule of Events", pc["accent"])}
      {_title(name, th)}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:18px; line-height:1.5; color:{th["body"]};">
        {''.join(blocks)}
      </div>"""
    return _section(inner, th["bg"])


# ---------------------------------------------------------------------------
# Parking
# ---------------------------------------------------------------------------
def parking(event: Event, pool_key: str) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    p = event.raw.get("parking") or {}
    if not p:
        return ""

    img = ""
    if p.get("map"):
        img = (
            f'<img src="{event.asset(p["map"])}" '
            'style="max-width:100%; max-height:46vh; border-radius:8px; '
            'object-fit:contain; margin-bottom:10px;">'
        )

    callout = ""
    co = p.get("callout") or {}
    if co.get("headline") or co.get("body"):
        callout = f"""
        <div style="background:{th["callout"]}; border-radius:8px; padding:12px 16px; text-align:left; margin-bottom:10px;">
          <div style="font-size:19px; font-weight:900; color:{th["on_callout"]}; text-transform:uppercase; line-height:1.2;">{co.get("headline", "")}</div>
          {f'<p style="font-size:17px; color:{th["on_callout_muted"]}; margin-top:6px; line-height:1.35;">{co.get("body", "")}</p>' if co.get("body") else ''}
        </div>"""

    body = ""
    if p.get("body"):
        body += f'<p>{p["body"]}</p>'
    if p.get("footnote"):
        body += f'<p style="font-size:15px; color:{th["muted"]}; margin-top:4px;">{p["footnote"]}</p>'

    inner = f"""
      {_eyebrow("Parking", pc["accent"])}
      {_title("Parking &amp; Passes", th)}
      {img}
      {callout}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:18px; line-height:1.5; color:{th["body"]};">
        {body}
      </div>"""
    return _section(inner, th["bg"])


# ---------------------------------------------------------------------------
# Camping
# ---------------------------------------------------------------------------
def camping(event: Event, pool_key: str) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    c = event.raw.get("camping") or {}
    if not c:
        return ""

    img = ""
    if c.get("map"):
        img = (
            f'<img src="{event.asset(c["map"])}" '
            'style="max-width:100%; max-height:42vh; border-radius:8px; '
            'object-fit:contain; margin-bottom:12px;">'
        )

    items = c.get("items") or []
    rows = []
    for i, item in enumerate(items):
        border = f'border-bottom:1px solid {th["hairline"]};' if i < len(items) - 1 else ""
        rows.append(
            f'<div style="padding:8px 0; {border}">'
            f'<strong>{item.get("label", "")}:</strong> {item.get("text", "")}</div>'
        )

    inner = f"""
      {_eyebrow("Camping", pc["accent"])}
      {_title("Camping Info", th)}
      {img}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:19px; line-height:1.5; color:{th["body"]};">
        {''.join(rows)}
      </div>"""
    return _section(inner, th["bg"])


# ---------------------------------------------------------------------------
# Pool assignments
# ---------------------------------------------------------------------------
def pools_overview(event: Event, pool_key: str) -> str:
    th = event.theme
    panel_bg, panel_fg, panel_body = _panel(th, event.pool_color(pool_key))
    pc = event.pool_color(pool_key)
    cards = []
    for key, pool in event.pools.items():
        c = event.pool_color(key)
        border = (
            f"border:2px solid {c['accent']};"
            if key == pool_key
            else f"border-left:3px solid {c['accent']};"
        )
        cards.append(f"""
            <div style="background:{th['panel'] or c['light']}; border-radius:10px; padding:16px 18px; margin-bottom:14px; {border}">
              <div style="font-weight:900; font-size:26px; color:{c['accent']}; line-height:1.05;">{pool.get('name', key)}</div>
              <div style="margin-top:4px;{f" color:{panel_fg};" if th["on_panel"] else ""}">{pool.get('divisions', '')}</div>
              <div style="font-size:16px; color:{th["on_panel"] or th["muted"]}; margin-top:4px;">{pool.get('description', '')}</div>
            </div>""")

    inner = f"""
      {_eyebrow("Pool Assignments", pc["accent"])}
      <div style="font-size:30px; font-weight:900; text-transform:uppercase; color:{th["ink"]}; margin-bottom:14px;">{"Three Pools" if len(event.pools) == 3 else f"{len(event.pools)} Pools"}</div>
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:19px; line-height:1.5; color:{th["body"]};">
        {''.join(cards)}
      </div>
      <p style="font-size:15px; color:{th["muted"]}; margin-top:14px;">Your pool is highlighted above.</p>"""
    return _section(inner, th["bg"])


# ---------------------------------------------------------------------------
# TD / ED welcomes
# ---------------------------------------------------------------------------
def _welcome_page(event: Event, pool_key: str, who: dict, page: dict, eyebrow_text: str, is_last: bool) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    photo = ""
    if who.get("photo"):
        photo = (
            f'<img src="{event.asset(who["photo"])}" '
            f'style="width:72px; height:72px; border-radius:50%; object-fit:cover; '
            f'margin-bottom:6px; border:3px solid {pc["accent"]};">'
        )

    paragraphs = "".join(
        f'<p style="margin-bottom:12px;">{p}</p>' for p in (page.get("paragraphs") or [])
    )

    sig = ""
    if is_last and who.get("name"):
        sig = f"""
        <div style="margin-top:16px; text-align:left; max-width:460px; margin-left:auto; margin-right:auto;">
          <div style="font-weight:700; font-size:17px; color:{th["ink"]};">{who['name']}</div>
          <div style="font-size:15px; color:{th["muted"]};">{who.get('title', '')}</div>
        </div>"""
    elif not is_last:
        sig = f'<div style="margin-top:14px; font-size:15px; color:{th["muted"]}; font-style:italic;">continued &rarr;</div>'

    title = page.get("title", "")
    title_size = "28px" if len(title) < 30 else "24px"

    inner = f"""
      {photo}
      <div style="font-size:15px; font-weight:700; letter-spacing:0.16em; text-transform:uppercase; color:{pc["accent"]}; margin-bottom:4px;">{eyebrow_text}</div>
      <div style="font-size:{title_size}; font-weight:900; text-transform:uppercase; color:{th["ink"]}; margin-bottom:8px; line-height:1.05;">{title}</div>
      <div style="width:60px; height:3px; background:{th["gradient"]}; margin:0 auto 14px;"></div>
      <div style="font-size:20px; line-height:1.5; color:{th["body"]}; text-align:left; max-width:460px; margin:0 auto;">
        {paragraphs}
      </div>
      {sig}"""
    return _section(inner, th["bg"])


def td_welcome(event: Event, pool_key: str) -> list[str]:
    who = event.raw.get("td_welcome") or {}
    pages = who.get("pages") or []
    if not pages:
        return []
    return [
        _welcome_page(event, pool_key, who, page, "From the Tournament Director", i == len(pages) - 1)
        for i, page in enumerate(pages)
    ]


def ed_welcome(event: Event, pool_key: str) -> list[str]:
    who = event.raw.get("ed_welcome") or {}
    if not who:
        return []
    pages = who.get("pages") or [{
        "title": who.get("headline", "Welcome"),
        "paragraphs": who.get("paragraphs") or [],
    }]
    return [
        _welcome_page(event, pool_key, who, page, "From the Executive Director", i == len(pages) - 1)
        for i, page in enumerate(pages)
    ]


# ---------------------------------------------------------------------------
# Sponsors
# ---------------------------------------------------------------------------
def sponsors(event: Event, pool_key: str) -> str:
    th = event.theme
    panel_bg, panel_fg, panel_body = _panel(th, event.pool_color(pool_key))
    pc = event.pool_color(pool_key)
    s = event.raw.get("sponsors") or {}
    cards = s.get("cards") if isinstance(s, dict) else s
    if not cards:
        return ""

    items = []
    for sp in cards:
        logo_w = sp.get("logo_width") or 64
        logo_style = f'width:{logo_w}px; flex-shrink:0;'
        if sp.get("logo_width"):
            logo_style += " align-self:center;"
        else:
            logo_style += f' height:{logo_w}px;'

        cta = ""
        if sp.get("cta"):
            ct = sp["cta"]
            cta = f"""
              <a href="{ct.get("url", "#")}" target="_blank" rel="noopener" style="display:block; background:{th["ink"]}; border-radius:6px; padding:10px 12px; margin-bottom:6px; text-decoration:none;">
                <div style="font-size:15px; font-weight:900; letter-spacing:0.08em; text-transform:uppercase; color:{th["gold"]}; margin-bottom:2px;">{ct.get("eyebrow", "")}</div>
                <div style="font-size:15px; color:{th["on_ink"]}; line-height:1.35;">{ct.get("text", "")}</div>
              </a>"""

        url_link = ""
        if sp.get("url"):
            shown = sp["url"].replace("https://", "").replace("http://", "").rstrip("/")
            url_link = (
                f'<a href="{sp["url"]}" target="_blank" rel="noopener" '
                f'style="font-size:15px; font-weight:700; color:{th["link"]}; '
                f'text-decoration:underline;">{shown}</a>'
            )

        logo_img = ""
        if sp.get("logo"):
            logo_img = f'<img src="{event.asset(sp["logo"])}" style="{logo_style}">'

        items.append(f"""
          <div style="background:{panel_bg}; border-radius:12px; padding:16px 16px; max-width:460px; margin:0 auto 14px; text-align:left; display:flex; gap:14px; align-items:flex-start;">
            {logo_img}
            <div>
              <div style="font-size:22px; font-weight:900; text-transform:uppercase; color:{panel_fg}; line-height:1.1; margin-bottom:4px;">{sp.get('name', '')}</div>
              <p style="font-size:16px; line-height:1.4; color:{panel_body}; margin-bottom:6px;">{sp.get('description', '')}</p>
              {cta}
              {url_link}
            </div>
          </div>""")

    inquiry = ""
    inquiry_email = s.get("inquiry_email") if isinstance(s, dict) else None
    if inquiry_email:
        inquiry = (
            f'<p style="font-size:15px; color:{th["muted"]}; margin-top:10px;">'
            f'Interested in sponsoring? '
            f'<a href="mailto:{inquiry_email}" style="color:{th["link"]}; text-decoration:underline;">'
            f'{inquiry_email}</a></p>'
        )

    inner = f"""
      {_eyebrow("Our Sponsors", pc["accent"])}
      <div style="font-size:32px; font-weight:900; text-transform:uppercase; color:{th["ink"]}; margin-bottom:6px;">Thank You</div>
      {_divider(th)}
      {''.join(items)}
      {inquiry}"""
    return _section(inner, th["bg"])


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def rules(event: Event, pool_key: str) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    r = event.raw.get("rules") or {}
    pool = event.pools.get(pool_key) or {}

    callout = ""
    callouts = r.get("callouts") or {}
    if pool_key in callouts:
        co = callouts[pool_key]
        if isinstance(co, str):
            callout = (
                f'<div style="background:{th["gold"]}; border-radius:10px; padding:12px 14px; '
                f'margin:0 auto 12px; max-width:440px; text-align:left; border:3px solid {th["on_gold"]};">'
                f'<div style="font-size:16px; line-height:1.35; color:{th["on_gold"]};">{co}</div></div>'
            )
        else:
            callout = f"""
            <div style="background:{th["gold"]}; border-radius:10px; padding:12px 14px; margin:0 auto 12px; max-width:440px; text-align:left; border:3px solid {th["on_gold"]};">
              <div style="font-size:15px; font-weight:900; letter-spacing:0.06em; text-transform:uppercase; color:{th["on_gold"]}; margin-bottom:4px;">{co.get('headline', '')}</div>
              <div style="font-size:16px; line-height:1.35; color:{th["on_gold"]};">{co.get('body', '')}</div>
            </div>"""

    items = r.get("items") or []
    rule_lh = "1.45" if callout else "1.55"
    rule_pad = "8px" if callout else "10px"

    rows = []
    for i, item in enumerate(items):
        text = item.get("text", "")
        by_pool = item.get("text_by_pool") or {}
        if pool_key in by_pool:
            text = by_pool[pool_key]
        border = f'border-bottom:1px solid {th["hairline"]};' if i < len(items) - 1 else ""
        rows.append(
            f'<div style="padding:{rule_pad} 0; {border}">'
            f'<strong style="color:{pc["accent"]};">{item.get("label", "")}:</strong> {text}</div>'
        )

    inner = f"""
      {_eyebrow(f"{pool.get('name', pool_key)} Rules", pc["accent"])}
      <div style="font-size:30px; font-weight:900; text-transform:uppercase; color:{th["ink"]}; margin-bottom:2px;">Course Rules</div>
      <div style="font-size:15px; color:{th["muted"]}; margin-bottom:12px;">{pool.get('divisions', '')}</div>
      {callout}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:21px; line-height:{rule_lh}; color:{th["body"]};">
        {''.join(rows)}
      </div>"""
    return _section(inner, th["bg"])


# ---------------------------------------------------------------------------
# Day intro + Hole slides
# ---------------------------------------------------------------------------
def day_intro(event: Event, pool_key: str, day_index: int, repeats_previous: bool = False) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    pool = event.pools[pool_key]
    day = pool["days"][day_index]
    layout = event.layout_for_day(pool_key, day_index)
    brand = event.brand

    primary = ""
    if brand.get("primary_logo"):
        primary = (
            f'<img src="{event.asset(brand["primary_logo"])}" '
            'style="width:180px; border-radius:50%;">'
        )

    org_logos = ""
    logos = []
    if brand.get("org_logo"):
        logos.append(f'<img src="{event.asset(brand["org_logo"])}" style="height:56px;">')
    if brand.get("venue_logo"):
        logos.append(f'<img src="{event.asset(brand["venue_logo"])}" style="height:56px;">')
    if logos:
        org_logos = (
            '<div style="display:flex; gap:24px; align-items:center; justify-content:center;">'
            + "".join(logos)
            + "</div>"
        )

    if repeats_previous or not layout:
        sub = '<div style="font-size:24px; color:rgba(255,255,255,0.9); margin-top:18px;">Same layout as Day 1</div>'
    else:
        holes = layout.get("Holes", "?")
        par = layout.get("Par", "?")
        length = layout.get("Length", 0)
        sub = (
            f'<div style="font-size:26px; color:rgba(255,255,255,0.9); margin-top:18px;">'
            f'{holes} holes &bull; Par {par} &bull; {length:,} ft</div>'
        )

    if th["scenery"]:
        uid = f"dy{pool_key.lower()}{day_index}"
        stat = ("Same layout as Day 1" if (repeats_previous or not layout)
                else f'{layout.get("Holes", "?")} holes &bull; Par {layout.get("Par", "?")} &bull; {layout.get("Length", 0):,} ft')
        inner = f"""
      <div style="position:absolute; left:0; top:0; right:0; bottom:0; overflow:hidden;">
        {_scenery(event, uid, 300, 162)}
        <div style="position:absolute; left:0; top:300px; right:0; bottom:0; background:{th["bg"]}; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:0 16px 84px; box-sizing:border-box;">
          <div style="font-size:15px; font-weight:700; letter-spacing:0.22em; text-transform:uppercase; color:{th["gold"]};">Round {day_index + 1}</div>
          <div style="margin-top:6px; font-size:84px; font-weight:900; text-transform:uppercase; color:{th["ink"]}; line-height:1;">{day.get("label", f"Day {day_index + 1}")}</div>
          <div style="margin-top:18px; width:180px; height:2px; background:#b9451f;"></div>
          <div style="margin-top:18px; font-size:21px; font-weight:700; color:#f6b04a;">{stat}</div>
          <div style="margin-top:8px; font-size:16px; font-weight:700; letter-spacing:0.16em; text-transform:uppercase; color:{th["body"]};">{day.get("date", "")}</div>
        </div>
        <div style="position:absolute; left:0; right:0; bottom:16px; display:flex; align-items:center; justify-content:center; gap:16px;">{org_logos}</div>
        {_grain(uid)}
      </div>"""
        return _section(inner, th["bg"])

    inner = f"""
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:space-between; height:calc(100vh - 60px); gap:16px; padding:8px 0;">
        {primary}
        <div>
          <div style="font-size:96px; font-weight:900; text-transform:uppercase; color:{th["on_pool"]}; line-height:1;">{day.get("label", f"Day {day_index + 1}")}</div>
          {sub}
          <div style="font-size:20px; color:rgba(255,255,255,0.65); margin-top:8px;">{day.get("date", "")}</div>
        </div>
        {org_logos}
      </div>"""
    return _section(inner, pc["bg"])


def hole_slide(
    event: Event,
    pool_key: str,
    day_index: int,
    display_order: str,
    hole: dict[str, Any],
    total_holes: int,
) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    panel_bg, panel_fg, panel_body = _panel(th, pc)
    pool = event.pools[pool_key]
    layout_id = str((pool["days"][day_index]).get("layout_id"))
    course_hole = hole.get("Label", display_order)

    img_path = event.hole_image(course_hole, pool_key, layout_id)
    if img_path:
        img_html = (
            f'<img src="{event.asset(img_path)}" '
            'style="max-height:70vh; max-width:100%; width:auto; object-fit:contain; '
            'display:block; margin:0 auto;">'
        )
    else:
        img_html = f'''<div style="height:54vh; display:flex; flex-direction:column; align-items:center; justify-content:center;">
              <div style="font-size:108px; font-weight:900; color:{th["body"]}; margin-bottom:10px;">Hole {course_hole}</div>
              <div style="font-size:30px; color:{th["muted"]};">No map available</div>
            </div>'''

    def pill(label: str, value: str) -> str:
        return f"""
            <div style="flex:1; background:{panel_bg}; border-radius:10px; padding:8px 4px; text-align:center;">
              <div style="font-size:15px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:{pc['accent']}; line-height:1;">{label}</div>
              <div style="font-size:24px; font-weight:900; color:{panel_fg}; line-height:1.05; margin-top:4px;">{value}</div>
            </div>"""

    pills = (
        pill("Tee", hole.get("Tee", "-"))
        + pill("Target", hole.get("Target", "-"))
        + pill("Par", str(hole.get("Par", "-")))
        + pill("Dist", f"{hole.get('Length', 0)}&prime;")
    )

    notes = hole.get("Notes", "") or hole.get("notes", "")
    notes_block = ""
    if notes:
        notes_block = (
            f'<div style="font-size:17px; line-height:1.4; color:{panel_body}; '
            f'background:{panel_bg}; border-left:4px solid {pc["accent"]}; '
            f'border-radius:0 8px 8px 0; padding:11px 13px; text-align:left;">{notes}</div>'
        )

    inner = f"""
      <div style="margin:-14px -14px 10px;">
        {img_html}
      </div>
      <div style="display:flex; gap:6px; margin-bottom:10px;">
        {pills}
      </div>
      <div style="text-align:center; font-size:15px; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; color:{pc["accent"]}; margin-bottom:6px;">Hole {display_order} of {total_holes}</div>
      {notes_block}"""
    return _section(inner, th["bg"])


# ---------------------------------------------------------------------------
# Special thanks
# ---------------------------------------------------------------------------
def special_thanks(event: Event, pool_key: str) -> str:
    th = event.theme
    pc = event.pool_color(pool_key)
    st = event.raw.get("special_thanks") or {}
    sections = st.get("sections") if isinstance(st, dict) else st
    if not sections:
        return ""

    rows = []
    for s in sections:
        rows.append(f'<div style="font-weight:900; font-size:17px; text-transform:uppercase; letter-spacing:0.08em; color:{pc["accent"]}; margin-bottom:4px;">{s.get("title", "")}</div>')
        rows.append(f'<div style="margin-bottom:12px; font-size:17px; color:{th["body"]};">{s.get("body", "")}</div>')

    inner = f"""
      {_eyebrow("Special Thanks", pc["accent"])}
      <div style="font-size:32px; font-weight:900; text-transform:uppercase; color:{th["ink"]}; margin-bottom:8px;">Thank You</div>
      {_divider(th, pc["accent"])}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:18px; line-height:1.5; color:{th["body"]};">
        {''.join(rows)}
      </div>"""
    return _section(inner, th["bg"])


# ---------------------------------------------------------------------------
# Custom (raw HTML)
# ---------------------------------------------------------------------------
def custom(event: Event, pool_key: str, slide_id: str) -> str:
    th = event.theme
    cs = (event.raw.get("custom_slides") or {}).get(slide_id) or {}
    bg = cs.get("background", th["bg"])
    html = cs.get("html", "")
    return _section(html, bg)
