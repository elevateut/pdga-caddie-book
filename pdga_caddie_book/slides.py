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

GRADIENT = "linear-gradient(90deg,#f4764b,#f8bd3c)"


# ---------------------------------------------------------------------------
# Small style helpers
# ---------------------------------------------------------------------------
def _section(content: str, bg: str = "#ffffff") -> str:
    return f'<section data-background-color="{bg}">{content}</section>'


def _eyebrow(text: str, color: str) -> str:
    return (
        f'<div style="font-size:15px; font-weight:700; letter-spacing:0.16em; '
        f'text-transform:uppercase; color:{color}; margin-bottom:6px;">{text}</div>'
    )


def _title(text: str) -> str:
    return (
        f'<div style="font-size:30px; font-weight:900; text-transform:uppercase; '
        f'color:#0c1116; margin-bottom:10px;">{text}</div>'
    )


def _divider(color: str | None = None) -> str:
    bg = color if color else GRADIENT
    return f'<div style="width:60px; height:3px; background:{bg}; margin:0 auto 16px;"></div>'


# ---------------------------------------------------------------------------
# Cover / back cover
# ---------------------------------------------------------------------------
def cover(event: Event, pool_key: str) -> str:
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

    inner = f"""
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:space-between; height:calc(100vh - 60px); padding:8px 0;">
        {primary}
        <div>
          <div style="font-size:20px; font-weight:700; letter-spacing:0.18em; text-transform:uppercase; color:{pc["accent"]};">{em.get("name", "")}</div>
          <div style="font-size:72px; font-weight:900; text-transform:uppercase; color:#ffffff; line-height:1; margin:12px 0;">{pool.get("name", pool_key)}</div>
          <div style="font-size:28px; color:#D4B896; margin-bottom:14px;">{em.get("dates", "")}</div>
          <div style="font-size:15px; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:{pc["accent"]};">{em.get("tagline", "")}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:14px;">
          {org_logos}
          <div style="font-size:13px; color:rgba(255,255,255,0.5);">Swipe to navigate &rarr;</div>
        </div>
      </div>"""
    return _section(inner, pc["bg"])


def back_cover(event: Event, pool_key: str) -> str:
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
            f'style="font-size:20px; font-weight:700; color:#D4B896; letter-spacing:0.06em; '
            f'text-decoration:underline;">{text}</a>'
        )

    inner = f"""
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:space-between; height:calc(100vh - 60px); padding:8px 0;">
        {primary}
        <div style="text-align:center;">
          <div style="font-size:30px; font-weight:900; color:#ffffff; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">{bc.get("headline", "")}</div>
          <div style="font-size:16px; color:rgba(255,255,255,0.6);">{bc.get("subhead", "")}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:18px;">
          {org_logos}
          {url_link}
        </div>
      </div>"""
    return _section(inner, pc["bg"])


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
def schedule(event: Event, pool_key: str) -> str:
    pc = event.pool_color(pool_key)
    sched = event.raw.get("schedule") or []
    if not sched:
        return ""

    blocks = []
    for day in sched:
        rows = []
        for ev in day.get("events", []):
            rows.append(
                f'<div style="padding:5px 0; border-bottom:1px solid #e5eaef;">'
                f'<strong>{ev.get("time", "")}</strong> &mdash; {ev.get("text", "")}</div>'
            )
        # Last row gets no bottom border
        if rows:
            rows[-1] = rows[-1].replace("border-bottom:1px solid #e5eaef;", "")
        blocks.append(
            f'<div style="font-weight:900; font-size:22px; color:{pc["accent"]}; margin-bottom:4px;">'
            f'{day.get("day", "")}</div>'
            + "".join(rows)
            + '<div style="height:10px;"></div>'
        )

    name = event.event_meta.get("name", "")
    inner = f"""
      {_eyebrow("Schedule of Events", pc["accent"])}
      {_title(name)}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:18px; line-height:1.5; color:#2a323d;">
        {''.join(blocks)}
      </div>"""
    return _section(inner)


# ---------------------------------------------------------------------------
# Parking
# ---------------------------------------------------------------------------
def parking(event: Event, pool_key: str) -> str:
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
        <div style="background:#f4764b; border-radius:8px; padding:12px 16px; text-align:left; margin-bottom:10px;">
          <div style="font-size:19px; font-weight:900; color:#ffffff; text-transform:uppercase; line-height:1.2;">{co.get("headline", "")}</div>
          {f'<p style="font-size:17px; color:rgba(255,255,255,0.95); margin-top:6px; line-height:1.35;">{co.get("body", "")}</p>' if co.get("body") else ''}
        </div>"""

    body = ""
    if p.get("body"):
        body += f'<p>{p["body"]}</p>'
    if p.get("footnote"):
        body += f'<p style="font-size:15px; color:#5a6675; margin-top:4px;">{p["footnote"]}</p>'

    inner = f"""
      {_eyebrow("Parking", pc["accent"])}
      {_title("Parking &amp; Passes")}
      {img}
      {callout}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:18px; line-height:1.5; color:#2a323d;">
        {body}
      </div>"""
    return _section(inner)


# ---------------------------------------------------------------------------
# Camping
# ---------------------------------------------------------------------------
def camping(event: Event, pool_key: str) -> str:
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
        border = "border-bottom:1px solid #e5eaef;" if i < len(items) - 1 else ""
        rows.append(
            f'<div style="padding:8px 0; {border}">'
            f'<strong>{item.get("label", "")}:</strong> {item.get("text", "")}</div>'
        )

    inner = f"""
      {_eyebrow("Camping", pc["accent"])}
      {_title("Camping Info")}
      {img}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:19px; line-height:1.5; color:#2a323d;">
        {''.join(rows)}
      </div>"""
    return _section(inner)


# ---------------------------------------------------------------------------
# Pool assignments
# ---------------------------------------------------------------------------
def pools_overview(event: Event, pool_key: str) -> str:
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
            <div style="background:{c['light']}; border-radius:10px; padding:16px 18px; margin-bottom:14px; {border}">
              <div style="font-weight:900; font-size:26px; color:{c['accent']}; line-height:1.05;">{pool.get('name', key)}</div>
              <div style="margin-top:4px;">{pool.get('divisions', '')}</div>
              <div style="font-size:16px; color:#5a6675; margin-top:4px;">{pool.get('description', '')}</div>
            </div>""")

    inner = f"""
      {_eyebrow("Pool Assignments", pc["accent"])}
      <div style="font-size:30px; font-weight:900; text-transform:uppercase; color:#0c1116; margin-bottom:14px;">{"Three Pools" if len(event.pools) == 3 else f"{len(event.pools)} Pools"}</div>
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:19px; line-height:1.5; color:#2a323d;">
        {''.join(cards)}
      </div>
      <p style="font-size:15px; color:#5a6675; margin-top:14px;">Your pool is highlighted above.</p>"""
    return _section(inner)


# ---------------------------------------------------------------------------
# TD / ED welcomes
# ---------------------------------------------------------------------------
def _welcome_page(event: Event, pool_key: str, who: dict, page: dict, eyebrow_text: str, is_last: bool) -> str:
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
          <div style="font-weight:700; font-size:17px; color:#0c1116;">{who['name']}</div>
          <div style="font-size:14px; color:#5a6675;">{who.get('title', '')}</div>
        </div>"""
    elif not is_last:
        sig = '<div style="margin-top:14px; font-size:14px; color:#5a6675; font-style:italic;">continued &rarr;</div>'

    title = page.get("title", "")
    title_size = "28px" if len(title) < 30 else "24px"

    inner = f"""
      {photo}
      <div style="font-size:14px; font-weight:700; letter-spacing:0.16em; text-transform:uppercase; color:{pc["accent"]}; margin-bottom:4px;">{eyebrow_text}</div>
      <div style="font-size:{title_size}; font-weight:900; text-transform:uppercase; color:#0c1116; margin-bottom:8px; line-height:1.05;">{title}</div>
      <div style="width:60px; height:3px; background:{GRADIENT}; margin:0 auto 14px;"></div>
      <div style="font-size:20px; line-height:1.5; color:#2a323d; text-align:left; max-width:460px; margin:0 auto;">
        {paragraphs}
      </div>
      {sig}"""
    return _section(inner)


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
    page = {
        "title": who.get("headline", "Welcome"),
        "paragraphs": who.get("paragraphs") or [],
    }
    return [_welcome_page(event, pool_key, who, page, "From the Executive Director", True)]


# ---------------------------------------------------------------------------
# Sponsors
# ---------------------------------------------------------------------------
def sponsors(event: Event, pool_key: str) -> str:
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
              <a href="{ct.get("url", "#")}" target="_blank" rel="noopener" style="display:block; background:#0c1116; border-radius:6px; padding:10px 12px; margin-bottom:6px; text-decoration:none;">
                <div style="font-size:13px; font-weight:900; letter-spacing:0.08em; text-transform:uppercase; color:#f8bd3c; margin-bottom:2px;">{ct.get("eyebrow", "")}</div>
                <div style="font-size:14px; color:#ffffff; line-height:1.35;">{ct.get("text", "")}</div>
              </a>"""

        url_link = ""
        if sp.get("url"):
            shown = sp["url"].replace("https://", "").replace("http://", "").rstrip("/")
            url_link = (
                f'<a href="{sp["url"]}" target="_blank" rel="noopener" '
                f'style="font-size:15px; font-weight:700; color:#0faec5; '
                f'text-decoration:underline;">{shown}</a>'
            )

        logo_img = ""
        if sp.get("logo"):
            logo_img = f'<img src="{event.asset(sp["logo"])}" style="{logo_style}">'

        items.append(f"""
          <div style="background:{pc['light']}; border-radius:12px; padding:16px 16px; max-width:460px; margin:0 auto 14px; text-align:left; display:flex; gap:14px; align-items:flex-start;">
            {logo_img}
            <div>
              <div style="font-size:22px; font-weight:900; text-transform:uppercase; color:#0c1116; line-height:1.1; margin-bottom:4px;">{sp.get('name', '')}</div>
              <p style="font-size:16px; line-height:1.4; color:#2a323d; margin-bottom:6px;">{sp.get('description', '')}</p>
              {cta}
              {url_link}
            </div>
          </div>""")

    inquiry = ""
    inquiry_email = s.get("inquiry_email") if isinstance(s, dict) else None
    if inquiry_email:
        inquiry = (
            f'<p style="font-size:14px; color:#5a6675; margin-top:10px;">'
            f'Interested in sponsoring? '
            f'<a href="mailto:{inquiry_email}" style="color:#0faec5; text-decoration:underline;">'
            f'{inquiry_email}</a></p>'
        )

    inner = f"""
      {_eyebrow("Our Sponsors", pc["accent"])}
      <div style="font-size:32px; font-weight:900; text-transform:uppercase; color:#0c1116; margin-bottom:6px;">Thank You</div>
      {_divider()}
      {''.join(items)}
      {inquiry}"""
    return _section(inner)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def rules(event: Event, pool_key: str) -> str:
    pc = event.pool_color(pool_key)
    r = event.raw.get("rules") or {}
    pool = event.pools.get(pool_key) or {}

    callout = ""
    callouts = r.get("callouts") or {}
    if pool_key in callouts:
        co = callouts[pool_key]
        if isinstance(co, str):
            callout = (
                f'<div style="background:#f8bd3c; border-radius:10px; padding:12px 14px; '
                f'margin:0 auto 12px; max-width:440px; text-align:left; border:3px solid #0c1116;">'
                f'<div style="font-size:16px; line-height:1.35; color:#0c1116;">{co}</div></div>'
            )
        else:
            callout = f"""
            <div style="background:#f8bd3c; border-radius:10px; padding:12px 14px; margin:0 auto 12px; max-width:440px; text-align:left; border:3px solid #0c1116;">
              <div style="font-size:15px; font-weight:900; letter-spacing:0.06em; text-transform:uppercase; color:#0c1116; margin-bottom:4px;">{co.get('headline', '')}</div>
              <div style="font-size:16px; line-height:1.35; color:#0c1116;">{co.get('body', '')}</div>
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
        border = "border-bottom:1px solid #e5eaef;" if i < len(items) - 1 else ""
        rows.append(
            f'<div style="padding:{rule_pad} 0; {border}">'
            f'<strong style="color:{pc["accent"]};">{item.get("label", "")}:</strong> {text}</div>'
        )

    inner = f"""
      {_eyebrow(f"{pool.get('name', pool_key)} Rules", pc["accent"])}
      <div style="font-size:30px; font-weight:900; text-transform:uppercase; color:#0c1116; margin-bottom:2px;">Course Rules</div>
      <div style="font-size:15px; color:#5a6675; margin-bottom:12px;">{pool.get('divisions', '')}</div>
      {callout}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:21px; line-height:{rule_lh}; color:#2a323d;">
        {''.join(rows)}
      </div>"""
    return _section(inner)


# ---------------------------------------------------------------------------
# Day intro + Hole slides
# ---------------------------------------------------------------------------
def day_intro(event: Event, pool_key: str, day_index: int, repeats_previous: bool = False) -> str:
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

    inner = f"""
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:space-between; height:calc(100vh - 60px); gap:16px; padding:8px 0;">
        {primary}
        <div>
          <div style="font-size:96px; font-weight:900; text-transform:uppercase; color:#ffffff; line-height:1;">{day.get("label", f"Day {day_index + 1}")}</div>
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
    pc = event.pool_color(pool_key)
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
              <div style="font-size:108px; font-weight:900; color:#2a323d; margin-bottom:10px;">Hole {course_hole}</div>
              <div style="font-size:30px; color:#5a6675;">No map available</div>
            </div>'''

    def pill(label: str, value: str) -> str:
        return f"""
            <div style="flex:1; background:{pc['light']}; border-radius:10px; padding:8px 4px; text-align:center;">
              <div style="font-size:13px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:{pc['accent']}; line-height:1;">{label}</div>
              <div style="font-size:24px; font-weight:900; color:#0c1116; line-height:1.05; margin-top:4px;">{value}</div>
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
            f'<div style="font-size:17px; line-height:1.4; color:#2a323d; '
            f'background:{pc["light"]}; border-left:4px solid {pc["accent"]}; '
            f'border-radius:0 8px 8px 0; padding:11px 13px; text-align:left;">{notes}</div>'
        )

    inner = f"""
      <div style="margin:-14px -14px 10px;">
        {img_html}
      </div>
      <div style="display:flex; gap:6px; margin-bottom:10px;">
        {pills}
      </div>
      <div style="text-align:center; font-size:12px; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; color:{pc["accent"]}; margin-bottom:6px;">Hole {display_order} of {total_holes}</div>
      {notes_block}"""
    return _section(inner)


# ---------------------------------------------------------------------------
# Special thanks
# ---------------------------------------------------------------------------
def special_thanks(event: Event, pool_key: str) -> str:
    pc = event.pool_color(pool_key)
    st = event.raw.get("special_thanks") or {}
    sections = st.get("sections") if isinstance(st, dict) else st
    if not sections:
        return ""

    rows = []
    for s in sections:
        rows.append(f'<div style="font-weight:900; font-size:17px; text-transform:uppercase; letter-spacing:0.08em; color:{pc["accent"]}; margin-bottom:4px;">{s.get("title", "")}</div>')
        rows.append(f'<div style="margin-bottom:12px; font-size:17px; color:#2a323d;">{s.get("body", "")}</div>')

    inner = f"""
      {_eyebrow("Special Thanks", pc["accent"])}
      <div style="font-size:32px; font-weight:900; text-transform:uppercase; color:#0c1116; margin-bottom:8px;">Thank You</div>
      {_divider(pc["accent"])}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:18px; line-height:1.5; color:#2a323d;">
        {''.join(rows)}
      </div>"""
    return _section(inner)


# ---------------------------------------------------------------------------
# Custom (raw HTML)
# ---------------------------------------------------------------------------
def custom(event: Event, pool_key: str, slide_id: str) -> str:
    cs = (event.raw.get("custom_slides") or {}).get(slide_id) or {}
    bg = cs.get("background", "#ffffff")
    html = cs.get("html", "")
    return _section(html, bg)
