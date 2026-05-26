# `event.yaml` schema reference

This is the complete schema for the `event.yaml` file. See [`examples/wunderment-26/event.yaml`](../examples/wunderment-26/event.yaml) for a working reference.

Everything is optional unless marked **required**. The builder degrades gracefully — sections you don't define are simply not rendered.

## Top-level structure

```yaml
event: { ... }            # Tournament identity
brand: { ... }            # Logos + typography
deploy: { ... }           # Hosting URLs + OG image patterns
pools: { A: { ... }, B: { ... }, ... }  # Pool definitions (caddie books)
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
guides: { ... }           # Spectator / competitor guides
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

## `pools` — Pool definitions

Required for caddie books. Can be empty (`pools: {}`) if you're only building guides.

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

## `guides` — Spectator and competitor guides

Guides are per-event (not per-pool). They produce a single HTML slide deck for spectators, competitors, or any other audience. Guides reuse shared sections (`schedule`, `parking`, `camping`, `sponsors`, `special_thanks`, `back_cover`) and add guide-specific content.

Build with:
```bash
pdga-caddie-book spectator-guide event.yaml -o output/
pdga-caddie-book competitor-guide event.yaml -o output/
```

```yaml
guides:
  spectator:
    title: "Spectator Guide"                      # Shown on cover + HTML title
    subtitle: "25th Anniversary • Salt Lake City"  # Cover subtitle
    description: "Your guide to watching..."       # OG/meta description
    og_image: images/spectator-og.jpg              # Social preview image
    color:
      bg: "#003462"
      accent: "#FABE28"
      light: "#E8EEF5"

    # -- Welcome slide --
    welcome:
      eyebrow: "Welcome"
      headline: "Welcome to the Event"
      paragraphs:
        - "First paragraph..."
        - "Second paragraph..."

    # -- Venue map --
    venue_map:
      eyebrow: "Event Venues"
      headline: "Four Courses, One Valley"
      map: images/valley-map.png
      body: "Optional descriptive text below the map."

    # -- Spectator etiquette --
    etiquette:
      eyebrow: "Spectator Etiquette"
      headline: "How to Be a Great Gallery"
      callout:                                      # Optional alert box above rules
        headline: "No spectator ropes"
        body: "Maintain 6 feet from all OB ropes."
      items:
        - { label: "Quiet on the tee", text: "No talking during throws" }
        - { label: "Stay behind players", text: "Gallery follows behind" }

    # -- How to follow play --
    how_to_watch:
      eyebrow: "Following Play"
      headline: "How to Watch"
      items:
        - { label: "Lead card", text: "Top-scoring group with full gallery" }
        - { label: "Live scoring", text: "Follow on UDisc Live" }

    # -- Courses overview --
    courses_headline: "The Courses"
    courses:
      - name: "Brighton Resort"
        description: "Alpine mountain course at 9,000 ft."
        image: images/brighton.jpg                  # Optional thumbnail
        url: "https://example.com/caddy/brighton/a"
        url_text: "View Caddie Book"

    # -- Additional info slides (any number) --
    info_slides:
      - eyebrow: "Altitude Advisory"
        headline: "9,000 Feet"
        image: images/elevation-guide.png
        paragraphs: ["Brighton sits at 8,755 ft..."]
        items:
          - { label: "Hydrate", text: "Drink twice as much water" }
        background: "#ffffff"                       # Optional bg color

    # -- Food & drink --
    food_drink:
      eyebrow: "Food & Drink"
      headline: "Food & Beverage"
      items:
        - { label: "Beer", text: "Uinta Brewing" }

    # -- Local rules / know-before-you-go --
    local_rules:
      eyebrow: "Know Before You Go"
      headline: "Important Info"
      callout:
        headline: "No dogs in the canyon"
        body: "Watershed protection law."
      items:
        - { label: "Tickets", text: "VIP and GA day passes available" }

    # -- Override default slide order (optional) --
    slide_order:
      - guide_cover
      - welcome
      - schedule
      - venue_map
      - etiquette
      - how_to_watch
      - courses
      - info_slides
      - parking
      - camping
      - food_drink
      - local_rules
      - sponsors
      - special_thanks
      - back_cover
```

Default spectator guide slide order:
```
guide_cover, welcome, schedule, venue_map, etiquette, how_to_watch,
courses, info_slides, parking, camping, food_drink, local_rules,
sponsors, special_thanks, back_cover
```

All sections are optional — omit any block and its slide is skipped. `schedule`, `parking`, `camping`, `sponsors`, `special_thanks`, and `back_cover` are shared with caddie books (defined at the top level of event.yaml, not inside `guides:`).

See [`examples/uswdgc-2026/event.yaml`](../examples/uswdgc-2026/event.yaml) for a full working example.

---

## Slide builders

Each top-level section maps to a builder in [`pdga_caddie_book/slides.py`](../pdga_caddie_book/slides.py) (caddie books) or [`pdga_caddie_book/guide_slides.py`](../pdga_caddie_book/guide_slides.py) (guides). To customize the visual design, edit those files directly — there's intentionally no theming layer beyond pool/guide colors. The intent is that visual identity comes from `brand` + `pools.*.color` / `guides.*.color`; structural slide design is the package's responsibility.

If you need fundamentally different slide layouts, file an issue or PR — the builders are small and self-contained.
