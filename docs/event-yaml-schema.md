# `event.yaml` schema reference

This is the complete schema for the `event.yaml` file. See [`examples/wunderment-26/event.yaml`](../examples/wunderment-26/event.yaml) for a working reference.

Everything is optional unless marked **required**. The builder degrades gracefully — sections you don't define are simply not rendered.

## Top-level structure

```yaml
event: { ... }            # Tournament identity
brand: { ... }            # Logos + typography
deploy: { ... }           # Hosting URLs + OG image patterns
pools: { A: { ... }, B: { ... }, ... }  # REQUIRED — at least one
hole_overrides: { ... }   # Per-hole text/par/length overrides
images: { ... }           # Hole image resolution rules
schedule: [ ... ]         # Multi-day event schedule
parking: { ... }
camping: { ... }
td_welcome: { ... }
ed_welcome: { ... }
rules: { ... }
sponsors: { ... }
special_thanks: { ... }
back_cover: { ... }
custom_slides: { ... }    # Raw-HTML slide injection
slide_order: [ ... ]      # Override the default slide order
```

---

## `event` — Tournament identity

```yaml
event:
  name: "Wunderment 26"              # Required for title bars
  tagline: "The Wasatch Wunder · Midway, UT"
  dates: "May 30–31, 2026"
  location: "Midway, UT"
  pdga_tournament_id: 101284         # Required if you want layouts auto-fetched
  description: "Player-facing description, used in <meta description>"
```

## `brand` — Logos and typography

```yaml
brand:
  primary_logo: images/main-logo.png       # Cover + back cover circle
  org_logo:     images/org-logo.png        # Footer
  venue_logo:   images/venue-logo.png      # Footer
  font_family_css: "Articulat CF, sans-serif"
  fonts:
    - { file: fonts/Brand-Heavy.otf, family: "Articulat CF", weight: 900 }
    - { file: fonts/Brand-Medium.otf, family: "Articulat CF", weight: 500 }
```

Each `fonts[]` entry becomes an `@font-face` declaration. File extensions `.otf`/`.ttf` set the format automatically.

## `deploy` — Hosting URLs

Used to build absolute URLs for Open Graph/Twitter social previews.

```yaml
deploy:
  url_base: "https://example.com/caddy/my-event"
  # {pool} is replaced with the lowercase pool key (a, b, c, ...)
  og_image_pattern: "images/og-pool-{pool}.jpg"
```

## `pools` — Pool definitions **(required)**

The keys (`A`, `B`, `C`, ...) determine URL slugs (`pool-a-slides.html`) and the highlighted pool in the assignment overview.

```yaml
pools:
  A:
    name: "A Pool"                                # Display name
    divisions: "MPO, MP40, MA1"                   # Shown on rules slide
    description: "Championship layout"             # Shown on overview
    cover_subtitle: "Long pads, full difficulty"  # Optional cover-only subtitle
    players_per_card: 5                            # Default 5 (used in scorecards)
    color:
      bg:     "#2C4A2E"   # Dark — used for cover/day-intro backgrounds
      accent: "#5C7A4A"   # Mid — used for eyebrows, progress bars, borders
      light:  "#E8F0E4"   # Pale — pill backgrounds, info-row fills
      name:   "Forest Green"   # Optional label
    days:
      - { label: "Day 1", date: "Saturday, May 30", layout_id: 758489 }
      - { label: "Day 2", date: "Sunday, May 31",   layout_id: 758491 }
      # When a pool plays the same layout both days:
      # - { label: "Day 2", layout_id: 758489, same_as_previous: true }
```

`layout_id` values come from `pdga-caddie-book pull <tournament_id>` — see [`docs/pdga-data-flow.md`](pdga-data-flow.md).

## `hole_overrides` — Custom hole text

PDGA notes are often terse; this lets you write richer ground-rules per layout. Keyed by `LayoutID` → `display_order` (string).

```yaml
hole_overrides:
  "758489":                                      # The LayoutID from PDGA
    "1": { notes: "A Position Round 1" }
    "9": { notes: "Dual mandos. DZ between mandos. OB right past logs..." }
    "12":
      notes: "Mando LEFT — must throw past the mando trees"
      par: 4                                     # You can override any PDGA field
      length: 350
```

Display order is the position in the round (1 = first hole played). Override keys are case-insensitive — `notes`, `par`, `length`, `tee`, `target`, and `label` are all normalized to PDGA's casing.

## `images` — Hole image resolution

```yaml
images:
  base_dir: images
  default_pattern: "hole_{hole:02d}.jpg"       # {hole} = course hole number
  no_map_holes: ["10A", "10B", "2/3"]          # Show "No map available" placeholder

  # Per-pool override: pool A sees hole_02_a.jpg, pool B sees hole_02_b.jpg
  per_pool:
    A: { "2": "hole_02_a.jpg" }
    B: { "2": "hole_02_b.jpg" }

  # Per-layout override: this layout plays hole 12 from a different basket
  per_layout:
    "758495": { "12": "hole_12_short.jpg" }
```

Resolution order: `per_layout` > `per_pool` > `default_pattern`. If nothing resolves and the hole label isn't numeric, you get the "No map available" placeholder.

## `schedule` — Multi-day timeline

```yaml
schedule:
  - day: "Thu, May 29"
    events:
      - { time: "12:00 – 10:00 PM", text: "Camping opens" }
      - { time: "4:30 – 5:00 PM",   text: "Random Draw Doubles signups" }
  - day: "Fri, May 30"
    events:
      - { time: "Friday League", text: "Sanctioned singles" }
```

## `parking` / `camping`

```yaml
parking:
  map: images/parking-map.jpg
  callout:
    headline: "All cars must display a pass"     # Renders in orange alert box
    body: "Pick them up at check-in."
  body: "Tell the front desk staff you're here for the tournament."
  footnote: "Overflow by the dumpsters."

camping:
  map: images/camping-map.jpg
  items:
    - { label: "RV",           text: "Get here early — limited spots." }
    - { label: "Tent camping", text: "First come first serve." }
```

## `td_welcome` / `ed_welcome`

TD welcome can span multiple slides:

```yaml
td_welcome:
  name: "Nick Jennings"
  title: "Tournament Director"
  photo: images/nick.jpg
  pages:
    - title: "Welcome to the Event"
      paragraphs:
        - "First paragraph..."
        - "Second paragraph..."
    - title: "Welcome, Cont'd"
      paragraphs:
        - "Third paragraph..."

ed_welcome:
  name: "Scott Belchak"
  title: "Executive Director"
  photo: images/scott.jpg
  headline: "Disc Golf People Building Disc Golf Things"
  paragraphs:
    - "Single page only — multiple paragraphs OK."
```

## `rules`

```yaml
rules:
  # Optional callout shown ABOVE the rule list, for a specific pool only:
  callouts:
    C:
      headline: "C Pool — Find the WHITE Flags"
      body: "Every tee pad you play has white flags in front of it..."
  items:
    - { label: "Roads",  text: "Any road and beyond = OB" }
    - { label: "Creek",  text: "OB", text_by_pool: { C: "mandatory relief (no penalty)" } }
    - { label: "Hikers", text: "Right of way on Holes 1 & 4" }
```

`text_by_pool.{POOL}` overrides `text` for that pool's caddie book.

## `sponsors`

```yaml
sponsors:
  inquiry_email: scott@example.com   # Shown as "Interested in sponsoring? <email>"
  cards:
    - name: "Westside Discs"
      logo: images/westside-logo.svg
      logo_width: 64                  # Optional, default square 64×64
      description: "Player pack disc sponsor."
      url: "https://westsidediscs.com"
    - name: "HOWMZ"
      logo: images/howmz-logo.svg
      description: "Course sponsor — equipment + labor."
      url: "https://howmz.com"
      cta:                            # Optional highlighted CTA button
        url: "https://howmz.com/jobs"
        eyebrow: "We're Hiring →"
        text: "Framer · Carpenter · Electrician"
```

## `special_thanks`

```yaml
special_thanks:
  sections:
    - { title: "Board of Directors", body: "Name • Name • Name" }
    - { title: "Course Crew",        body: "Name • Name" }
```

## `back_cover`

```yaml
back_cover:
  headline: "See you out there."
  subhead:  "The Course • Town, State"
  url:      "https://elevateut.org"
  url_text: "elevateut.org"        # Optional display override
```

## `custom_slides` — Raw HTML injection

For one-off promo slides (e.g. sister-event recruitment, sponsor showcase, gift card raffle info):

```yaml
custom_slides:
  uswdgc_volunteers:
    after: sponsors            # Insert immediately after the sponsors slide
    background: "#003462"      # Section background color
    html: |
      <div style="...">
        <h1>Volunteer with us</h1>
        <p>...</p>
      </div>
```

Keys are arbitrary slide IDs (alphanumeric/underscore). `after` names a built-in slide ID to follow. If `after` isn't matched, the slide is appended at the end.

## `slide_order` — Override default order

If you skip this, the default is:
```
cover, schedule, parking, camping, pools, td_welcome, ed_welcome,
sponsors, rules, days_and_holes, special_thanks, back_cover
```

The special token `days_and_holes` expands to N day-intro slides plus N×holes hole slides. Custom slides referenced via `after:` are injected into the resolved order.

To customize:

```yaml
slide_order:
  - cover
  - td_welcome
  - sponsors
  - custom:uswdgc_volunteers   # Reference a custom slide directly
  - rules
  - days_and_holes
  - back_cover
```

---

## Slide builders

Each top-level section maps to a builder in [`pdga_caddie_book/slides.py`](../pdga_caddie_book/slides.py). To customize the visual design, edit that file directly — there's intentionally no theming layer beyond pool colors. The intent is that visual identity comes from `brand` + `pools.*.color`; structural slide design is the package's responsibility.

If you need fundamentally different slide layouts, file an issue or PR — the builders are small and self-contained.
