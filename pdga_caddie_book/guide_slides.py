"""Slide builders for event guides (spectator, competitor).

Guide slides are per-event, not per-pool. They use a guide_key (e.g.
"spectator") to look up colors via Event.pool_color(guide_key) and
guide-specific config via Event.guide_config(guide_key).
"""

from __future__ import annotations

from .config import Event
from .slides import _section, _eyebrow, _title, _divider, GRADIENT


def guide_cover(event: Event, guide_key: str) -> str:
    gc = event.pool_color(guide_key)
    cfg = event.guide_config(guide_key) or {}
    em = event.event_meta
    brand = event.brand

    logo_src = cfg.get("cover_logo") or brand.get("primary_logo")
    primary = ""
    if logo_src:
        primary = (
            f'<img src="{event.asset(logo_src)}" alt="{em.get("name", "")}" '
            'style="max-width:320px; max-height:180px; object-fit:contain;">'
        )

    org_logos = ""
    logos = []
    if brand.get("org_logo"):
        logos.append(f'<img src="{event.asset(brand["org_logo"])}" alt="Organizer" style="height:40px; opacity:0.85;">')
    if brand.get("venue_logo"):
        logos.append(f'<img src="{event.asset(brand["venue_logo"])}" alt="Venue" style="height:40px; opacity:0.85;">')
    if logos:
        org_logos = (
            '<div style="display:flex; gap:24px; align-items:center; justify-content:center;">'
            + "".join(logos)
            + "</div>"
        )

    guide_title = cfg.get("title", guide_key.title() + " Guide")
    subtitle = cfg.get("subtitle", "")

    inner = f"""
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:24px; min-height:calc(100vh - 60px); padding:8px 0;">
        {primary}
        <div>
          <div style="font-size:18px; font-weight:700; letter-spacing:0.18em; text-transform:uppercase; color:{gc["accent"]};">{em.get("name", "")}</div>
          <div style="font-size:48px; font-weight:900; text-transform:uppercase; color:#ffffff; line-height:1; margin:10px 0;">{guide_title}</div>
          <div style="font-size:24px; color:rgba(255,255,255,0.75); margin-bottom:10px;">{em.get("dates", "")}</div>
          <div style="font-size:13px; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:{gc["accent"]};">{subtitle or em.get("tagline", "")}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:10px;">
          {org_logos}
          <div style="font-size:12px; color:rgba(255,255,255,0.4);">Swipe to navigate &rarr;</div>
        </div>
      </div>"""
    return _section(inner, gc["bg"])


def welcome(event: Event, guide_key: str) -> str:
    cfg = event.guide_config(guide_key) or {}
    gc = event.pool_color(guide_key)
    w = cfg.get("welcome") or {}
    if not w:
        return ""

    paragraphs = "".join(
        f'<p style="margin-bottom:12px;">{p}</p>' for p in (w.get("paragraphs") or [])
    )

    inner = f"""
      <div style="display:flex; flex-direction:column; justify-content:center; min-height:70vh;">
      {_eyebrow(w.get("eyebrow", "Welcome"), gc["accent"])}
      {_title(w.get("headline", "Welcome"))}
      {_divider(gc["accent"])}
      <div style="font-size:20px; line-height:1.5; color:#2a323d; text-align:left; max-width:460px; margin:0 auto;">
        {paragraphs}
      </div>
      </div>"""
    return _section(inner)


def etiquette(event: Event, guide_key: str) -> str:
    cfg = event.guide_config(guide_key) or {}
    gc = event.pool_color(guide_key)
    e = cfg.get("etiquette") or {}
    if not e:
        return ""

    items = e.get("items") or []
    compact = len(items) > 4
    pad = "6px" if compact else "10px"
    font = "16px" if compact else "19px"
    lh = "1.35" if compact else "1.5"
    rows = []
    for i, item in enumerate(items):
        border = "border-bottom:1px solid #e5eaef;" if i < len(items) - 1 else ""
        icon = item.get("icon", "")
        icon_html = f'<span style="margin-right:8px;">{icon}</span>' if icon else ""
        rows.append(
            f'<div style="padding:{pad} 0; {border}">'
            f'{icon_html}<strong style="color:{gc["accent"]};">{item.get("label", "")}:</strong> '
            f'{item.get("text", "")}</div>'
        )

    callout = ""
    co = e.get("callout") or {}
    if co.get("headline") or co.get("body"):
        callout = f"""
        <div style="background:{gc["accent"]}; border-radius:10px; padding:10px 14px; text-align:left; margin-bottom:10px; max-width:440px; margin-left:auto; margin-right:auto;">
          <div style="font-size:15px; font-weight:900; color:#0c1116; text-transform:uppercase; line-height:1.2;">{co.get("headline", "")}</div>
          {f'<p style="font-size:14px; color:#0c1116; margin-top:4px; line-height:1.3;">{co.get("body", "")}</p>' if co.get("body") else ''}
        </div>"""

    inner = f"""
      {_eyebrow(e.get("eyebrow", "Spectator Etiquette"), gc["accent"])}
      {_title(e.get("headline", "How to Watch"))}
      {_divider(gc["accent"])}
      {callout}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:{font}; line-height:{lh}; color:#2a323d;">
        {''.join(rows)}
      </div>"""
    return _section(inner)


def venue_map(event: Event, guide_key: str) -> str:
    cfg = event.guide_config(guide_key) or {}
    gc = event.pool_color(guide_key)
    vm = cfg.get("venue_map") or {}
    if not vm:
        return ""

    if isinstance(vm, str):
        vm = {"map": vm}

    img = ""
    if vm.get("map"):
        alt = vm.get("alt", "Event venue map")
        img = (
            f'<img src="{event.asset(vm["map"])}" alt="{alt}" '
            'style="width:100%; max-height:62vh; border-radius:8px; '
            'object-fit:contain; margin:-6px 0 8px;">'
        )

    body = ""
    if vm.get("body"):
        body = f'<p style="font-size:15px; color:#5a6675; line-height:1.4; max-width:440px; margin:4px auto 0;">{vm["body"]}</p>'

    inner = f"""
      {_eyebrow(vm.get("eyebrow", "Venue Map"), gc["accent"])}
      {_title(vm.get("headline", "Event Venues"))}
      {_divider(gc["accent"])}
      {img}
      {body}"""
    return _section(inner)


def how_to_watch(event: Event, guide_key: str) -> str:
    cfg = event.guide_config(guide_key) or {}
    gc = event.pool_color(guide_key)
    htw = cfg.get("how_to_watch") or {}
    if not htw:
        return ""

    items = htw.get("items") or []
    compact = len(items) > 5
    pad = "6px" if compact else "10px"
    font = "16px" if compact else "19px"
    lh = "1.35" if compact else "1.5"
    rows = []
    for i, item in enumerate(items):
        border = "border-bottom:1px solid #e5eaef;" if i < len(items) - 1 else ""
        rows.append(
            f'<div style="padding:{pad} 0; {border}">'
            f'<strong style="color:{gc["accent"]};">{item.get("label", "")}:</strong> '
            f'{item.get("text", "")}</div>'
        )

    inner = f"""
      {_eyebrow(htw.get("eyebrow", "Following Play"), gc["accent"])}
      {_title(htw.get("headline", "How to Watch"))}
      {_divider(gc["accent"])}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:{font}; line-height:{lh}; color:#2a323d;">
        {''.join(rows)}
      </div>"""
    return _section(inner)


def food_drink(event: Event, guide_key: str) -> str:
    cfg = event.guide_config(guide_key) or {}
    gc = event.pool_color(guide_key)
    fd = cfg.get("food_drink") or {}
    if not fd:
        return ""

    items = fd.get("items") or []
    compact = len(items) > 4
    pad = "6px" if compact else "10px"
    font = "16px" if compact else "19px"
    lh = "1.35" if compact else "1.5"
    rows = []
    for i, item in enumerate(items):
        border = "border-bottom:1px solid #e5eaef;" if i < len(items) - 1 else ""
        rows.append(
            f'<div style="padding:{pad} 0; {border}">'
            f'<strong style="color:{gc["accent"]};">{item.get("label", "")}:</strong> '
            f'{item.get("text", "")}</div>'
        )

    center = "display:flex; flex-direction:column; justify-content:center; min-height:70vh;" if len(items) <= 5 else ""
    inner = f"""
      <div style="{center}">
      {_eyebrow(fd.get("eyebrow", "Food &amp; Drink"), gc["accent"])}
      {_title(fd.get("headline", "Food &amp; Beverage"))}
      {_divider(gc["accent"])}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:{font}; line-height:{lh}; color:#2a323d;">
        {''.join(rows)}
      </div>
      </div>"""
    return _section(inner)


def courses_overview(event: Event, guide_key: str) -> str:
    cfg = event.guide_config(guide_key) or {}
    gc = event.pool_color(guide_key)
    courses = cfg.get("courses") or []
    if not courses:
        return ""

    cards = []
    for course in courses:
        link = ""
        if course.get("url"):
            link = (
                f'<a href="{course["url"]}" target="_blank" rel="noopener" '
                f'style="font-size:14px; font-weight:700; color:#0faec5; text-decoration:underline;">'
                f'{course.get("url_text", "View Course")}</a>'
            )

        img = ""
        if course.get("image"):
            img = (
                f'<img src="{event.asset(course["image"])}" '
                f'style="width:64px; height:64px; border-radius:8px; object-fit:cover; flex-shrink:0;">'
            )

        cards.append(f"""
          <div style="background:{gc['light']}; border-radius:12px; padding:14px 16px; margin-bottom:12px; text-align:left; display:flex; gap:14px; align-items:flex-start;">
            {img}
            <div style="overflow-wrap:break-word; min-width:0;">
              <div style="font-size:20px; font-weight:900; text-transform:uppercase; color:#0c1116; line-height:1.1; margin-bottom:4px;">{course.get('name', '')}</div>
              <p style="font-size:15px; line-height:1.4; color:#2a323d; margin-bottom:4px;">{course.get('description', '')}</p>
              {link}
            </div>
          </div>""")

    inner = f"""
      {_eyebrow("Courses", gc["accent"])}
      {_title(cfg.get("courses_headline", "The Courses"))}
      {_divider(gc["accent"])}
      <div style="max-width:440px; margin:0 auto;">
        {''.join(cards)}
      </div>"""
    return _section(inner)


def local_rules(event: Event, guide_key: str) -> str:
    cfg = event.guide_config(guide_key) or {}
    gc = event.pool_color(guide_key)
    lr = cfg.get("local_rules") or {}
    if not lr:
        return ""

    items = lr.get("items") or []
    compact = len(items) > 5
    pad = "5px" if compact else "8px"
    font = "16px" if compact else "19px"
    lh = "1.35" if compact else "1.5"
    rows = []
    for i, item in enumerate(items):
        border = "border-bottom:1px solid #e5eaef;" if i < len(items) - 1 else ""
        rows.append(
            f'<div style="padding:{pad} 0; {border}">'
            f'<strong style="color:{gc["accent"]};">{item.get("label", "")}:</strong> '
            f'{item.get("text", "")}</div>'
        )

    callout = ""
    co = lr.get("callout") or {}
    if co.get("headline") or co.get("body"):
        callout = f"""
        <div style="background:{gc["accent"]}; border-radius:10px; padding:10px 14px; text-align:left; margin-bottom:10px; max-width:440px; margin-left:auto; margin-right:auto;">
          <div style="font-size:15px; font-weight:900; color:#0c1116; text-transform:uppercase; line-height:1.2;">{co.get("headline", "")}</div>
          {f'<p style="font-size:14px; color:#0c1116; margin-top:4px; line-height:1.35;">{co.get("body", "")}</p>' if co.get("body") else ''}
        </div>"""

    inner = f"""
      {_eyebrow(lr.get("eyebrow", "Know Before You Go"), gc["accent"])}
      {_title(lr.get("headline", "Local Rules"))}
      {_divider(gc["accent"])}
      {callout}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:{font}; line-height:{lh}; color:#2a323d;">
        {''.join(rows)}
      </div>"""
    return _section(inner)


def info_slide(event: Event, guide_key: str) -> str | list[str]:
    """Render any additional info_slides defined in the guide config.

    Each entry in guide.info_slides is rendered as its own section:
      info_slides:
        - eyebrow: "Altitude Advisory"
          headline: "9,000 Feet"
          image: images/elevation-guide.png
          paragraphs: [...]
          items: [...]
    """
    cfg = event.guide_config(guide_key) or {}
    gc = event.pool_color(guide_key)
    slides_cfg = cfg.get("info_slides") or []
    if not slides_cfg:
        return []

    out = []
    for slide in slides_cfg:
        has_items = bool(slide.get("items"))
        has_img = bool(slide.get("image"))
        img = ""
        if has_img:
            max_h = "36vh" if has_items else "54vh"
            img = (
                f'<img src="{event.asset(slide["image"])}" '
                f'style="width:100%; max-height:{max_h}; border-radius:8px; '
                f'object-fit:contain; margin-bottom:8px;">'
            )

        paragraphs = "".join(
            f'<p style="margin-bottom:8px;">{p}</p>'
            for p in (slide.get("paragraphs") or [])
        )

        items = slide.get("items") or []
        compact = len(items) > 3 or has_img
        pad = "5px" if compact else "8px"
        font = "15px" if compact else "18px"
        lh = "1.35" if compact else "1.5"
        rows = []
        for i, item in enumerate(items):
            border = "border-bottom:1px solid #e5eaef;" if i < len(items) - 1 else ""
            rows.append(
                f'<div style="padding:{pad} 0; {border}">'
                f'<strong style="color:{gc["accent"]};">{item.get("label", "")}:</strong> '
                f'{item.get("text", "")}</div>'
            )

        body = ""
        if paragraphs or rows:
            body = f"""
            <div style="font-size:{font}; line-height:{lh}; color:#2a323d; text-align:left; max-width:460px; margin:0 auto;">
              {paragraphs}
              {''.join(rows)}
            </div>"""

        bg = slide.get("background", "#ffffff")
        text_color = "#ffffff" if bg != "#ffffff" else "#0c1116"
        eyebrow_color = gc["accent"] if bg == "#ffffff" else "rgba(255,255,255,0.7)"

        inner = f"""
          {_eyebrow(slide.get("eyebrow", ""), eyebrow_color)}
          <div style="font-size:30px; font-weight:900; text-transform:uppercase; color:{text_color}; margin-bottom:10px;">{slide.get("headline", "")}</div>
          {_divider(gc["accent"])}
          {img}
          {body}"""
        out.append(_section(inner, bg))
    return out


def guide_back_cover(event: Event, guide_key: str) -> str:
    gc = event.pool_color(guide_key)
    cfg = event.guide_config(guide_key) or {}
    brand = event.brand
    bc = event.raw.get("back_cover") or {}

    logo_src = cfg.get("cover_logo") or brand.get("primary_logo")
    primary = ""
    if logo_src:
        primary = (
            f'<img src="{event.asset(logo_src)}" alt="{event.event_meta.get("name", "")}" '
            'style="max-width:280px; max-height:140px; object-fit:contain;">'
        )

    org_logos = ""
    logos = []
    if brand.get("org_logo"):
        logos.append(f'<img src="{event.asset(brand["org_logo"])}" alt="Organizer" style="height:40px; opacity:0.85;">')
    if brand.get("venue_logo"):
        logos.append(f'<img src="{event.asset(brand["venue_logo"])}" alt="Venue" style="height:40px; opacity:0.85;">')
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
            f'style="font-size:18px; font-weight:700; color:{gc["accent"]}; letter-spacing:0.06em; '
            f'text-decoration:underline;">{text}</a>'
        )

    inner = f"""
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:28px; min-height:calc(100vh - 60px); padding:8px 0;">
        {primary}
        <div style="text-align:center;">
          <div style="font-size:28px; font-weight:900; color:#ffffff; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px;">{bc.get("headline", "")}</div>
          <div style="font-size:15px; color:rgba(255,255,255,0.6);">{bc.get("subhead", "")}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:14px;">
          {org_logos}
          {url_link}
        </div>
      </div>"""
    return _section(inner, gc["bg"])


def guide_parking(event: Event, guide_key: str) -> str:
    """Guide-specific parking slide — uses guide accent color for callout
    and vertically centers sparse content."""
    gc = event.pool_color(guide_key)
    p = event.raw.get("parking") or {}
    if not p:
        return ""

    img = ""
    if p.get("map"):
        img = (
            f'<img src="{event.asset(p["map"])}" '
            'style="width:100%; max-height:46vh; border-radius:8px; '
            'object-fit:contain; margin-bottom:10px;">'
        )

    callout = ""
    co = p.get("callout") or {}
    if co.get("headline") or co.get("body"):
        callout = f"""
        <div style="background:{gc["accent"]}; border-radius:8px; padding:10px 14px; text-align:left; margin-bottom:10px; max-width:440px; margin-left:auto; margin-right:auto;">
          <div style="font-size:17px; font-weight:900; color:#0c1116; text-transform:uppercase; line-height:1.2;">{co.get("headline", "")}</div>
          {f'<p style="font-size:15px; color:#0c1116; margin-top:4px; line-height:1.35;">{co.get("body", "")}</p>' if co.get("body") else ''}
        </div>"""

    body = ""
    if p.get("body"):
        body += f'<p>{p["body"]}</p>'
    if p.get("footnote"):
        body += f'<p style="font-size:15px; color:#5a6675; margin-top:4px;">{p["footnote"]}</p>'

    has_map = bool(p.get("map"))
    center = "" if has_map else "display:flex; flex-direction:column; justify-content:center; min-height:70vh;"
    inner = f"""
      <div style="{center}">
      {_eyebrow("Parking", gc["accent"])}
      {_title("Parking &amp; Passes")}
      {img}
      {callout}
      <div style="text-align:left; max-width:440px; margin:0 auto; font-size:18px; line-height:1.5; color:#2a323d;">
        {body}
      </div>
      </div>"""
    return _section(inner)


def guide_sponsors(event: Event, guide_key: str) -> list[str]:
    """Two-slide sponsor layout: slide 1 features title + retail sponsors
    with large logos and descriptions; slide 2 is a logo grid of supporting sponsors."""
    gc = event.pool_color(guide_key)
    s = event.raw.get("sponsors") or {}
    cards = s.get("cards") if isinstance(s, dict) else s
    if not cards:
        return []

    featured = []
    grid_logos = []
    for i, sp in enumerate(cards):
        if not sp.get("logo"):
            continue

        if i < 2:
            featured.append(sp)
        else:
            grid_logos.append(sp)

    out = []

    # --- Slide 1: Featured sponsors (title + retail) ---
    if featured:
        feat_cards = []
        for sp in featured:
            logo = (
                f'<img src="{event.asset(sp["logo"])}" alt="{sp.get("name", "")}" '
                f'style="max-height:80px; max-width:220px; object-fit:contain;">'
            )
            if sp.get("url"):
                logo = f'<a href="{sp["url"]}" target="_blank" rel="noopener">{logo}</a>'
            tier = sp.get("description", "").split(".")[0] if sp.get("description") else ""
            desc_rest = ".".join(sp.get("description", "").split(".")[1:]).strip()
            feat_cards.append(f"""
              <div style="background:{gc["bg"]}; border-radius:12px; padding:20px 16px; text-align:center;">
                <div style="height:84px; display:flex; align-items:center; justify-content:center;">{logo}</div>
                <div style="font-size:18px; font-weight:900; color:#ffffff; text-transform:uppercase; margin-top:10px;">{sp.get("name", "")}</div>
                <div style="font-size:11px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:{gc["accent"]}; margin-top:4px;">{tier}</div>
                {f'<div style="font-size:14px; color:rgba(255,255,255,0.7); margin-top:8px; line-height:1.4;">{desc_rest}</div>' if desc_rest else ''}
              </div>""")

        inner = f"""
          <div style="display:flex; flex-direction:column; justify-content:center; min-height:70vh;">
          {_eyebrow("Our Partners", gc["accent"])}
          {_title("Thank You")}
          {_divider(gc["accent"])}
          <div style="display:flex; flex-direction:column; gap:14px; max-width:440px; margin:0 auto;">
            {''.join(feat_cards)}
          </div>
          </div>"""
        out.append(_section(inner))

    # --- Slide 2: Supporting sponsors logo grid ---
    if grid_logos:
        cells = []
        for sp in grid_logos:
            logo_html = (
                f'<img src="{event.asset(sp["logo"])}" alt="{sp.get("name", "")}" '
                f'style="max-height:36px; max-width:100px; object-fit:contain;">'
            )
            if sp.get("url"):
                logo_html = f'<a href="{sp["url"]}" target="_blank" rel="noopener">{logo_html}</a>'
            cells.append(
                f'<div style="display:flex; align-items:center; justify-content:center; '
                f'height:56px; padding:8px; background:{gc["light"]}; border-radius:8px;">'
                f'{logo_html}</div>'
            )

        inquiry = ""
        inquiry_email = s.get("inquiry_email") if isinstance(s, dict) else None
        if inquiry_email:
            inquiry = (
                f'<p style="font-size:12px; color:#5a6675; margin-top:14px;">'
                f'<a href="mailto:{inquiry_email}" style="color:#0faec5; text-decoration:underline;">'
                f'{inquiry_email}</a></p>'
            )

        inner = f"""
          <div style="display:flex; flex-direction:column; justify-content:center; min-height:70vh;">
          {_eyebrow("Supporting Sponsors", gc["accent"])}
          {_title("Thank You")}
          {_divider(gc["accent"])}
          <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:10px; max-width:100%; margin:0 auto;">
            {''.join(cells)}
          </div>
          {inquiry}
          </div>"""
        out.append(_section(inner))

    return out
