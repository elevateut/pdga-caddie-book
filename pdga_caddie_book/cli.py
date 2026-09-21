"""Command-line entry for pdga-caddie-book.

Subcommands:
  pull             — fetch all layouts for a PDGA tournament ID
  init             — scaffold a new event directory
  build            — render the reveal.js caddie books for every pool
  scorecards       — render printable duplex scorecards
  spectator-guide  — render a spectator guide
  pdf              — export HTML files to PDF via Playwright
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def cmd_pull(args: argparse.Namespace) -> int:
    from . import pdga

    result = pdga.fetch_layouts(str(args.tournament_id))
    out = json.dumps(result, indent=2 if args.pretty else None)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Wrote {args.output} — {len(result.get('layouts') or {})} layout(s)")
    else:
        print(out)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    from importlib import resources

    target = os.path.abspath(args.name)
    if os.path.exists(target) and not args.force:
        print(f"Refusing to overwrite existing directory: {target} (use --force)", file=sys.stderr)
        return 2
    os.makedirs(os.path.join(target, "images"), exist_ok=True)
    os.makedirs(os.path.join(target, "fonts"), exist_ok=True)

    # Copy the example yaml as a starting point
    example_pkg = resources.files("pdga_caddie_book").joinpath("..", "examples", "wunderment-26", "event.yaml")
    # Resources may not work from site-packages; fall back to a minimal template
    template = _minimal_event_yaml(args.tournament_id)
    yaml_path = os.path.join(target, "event.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"Created {yaml_path}")
    print(f"Next: edit {yaml_path}, drop hole images into {target}/images/, then run:")
    print(f"  pdga-caddie-book pull {args.tournament_id or '<id>'} --output {target}/layouts.json")
    print(f"  pdga-caddie-book build {yaml_path}")
    return 0


def _minimal_event_yaml(tournament_id: int | None) -> str:
    return f"""# Minimal pdga-caddie-book event config.
# Run `pdga-caddie-book pull {tournament_id or '<your-id>'}` to verify your layout IDs.

event:
  name: "My Tournament 2026"
  tagline: "Course · City, ST"
  dates: "Month DD–DD, 2026"
  location: "City, ST"
  pdga_tournament_id: {tournament_id or 0}

brand:
  primary_logo: images/logo.png

# Where the books are hosted. og_image_pattern names each pool's share image (the preview card
# when the link is shared); `pdga-caddie-book og` renders them.
deploy:
  url_base: "https://example.com/caddy/my-event"
  og_image_pattern: "images/og-pool-{pool}.jpg"

pools:
  A:
    name: "A Pool"
    divisions: "MPO, MA1"
    color: {{ bg: "#2C4A2E", accent: "#5C7A4A", light: "#E8F0E4" }}
    days:
      - {{ label: "Day 1", date: "Saturday", layout_id: 0 }}

rules:
  items:
    - {{ label: "OB", text: "All marked OB plays as OB" }}

back_cover:
  headline: "See you out there."
"""


def cmd_build(args: argparse.Namespace) -> int:
    from . import builder

    written = builder.build_event(
        event_yaml_path=args.event,
        output_dir=args.output,
        pdga_layouts_path=args.layouts,
        pool_filter=args.pool,
    )
    for p in written:
        print(f"Wrote {p}")
    _warn_share(args)
    return 0


def _warn_share(args: argparse.Namespace) -> None:
    """A book without a share image previews as a bare link. Say so on every build."""
    from . import og
    from .config import load_event

    event = load_event(args.event, pdga_layouts_path=args.layouts)
    keys = [k for k in event.pools if not args.pool or k in args.pool]
    for w in og.share_warnings(event, keys):
        print(f"WARN {w}", file=sys.stderr)


def cmd_og(args: argparse.Namespace) -> int:
    from . import og

    written = og.build_event(
        event_yaml_path=args.event,
        pdga_layouts_path=args.layouts,
        pool_filter=args.pool,
        output_dir=args.output,
    )
    for p in written:
        print(f"Wrote {p}")
    return 0


def cmd_scorecards(args: argparse.Namespace) -> int:
    from . import scorecards

    written = scorecards.build_event(
        event_yaml_path=args.event,
        output_dir=args.output,
        pdga_layouts_path=args.layouts,
        pool_filter=args.pool,
    )
    for p in written:
        print(f"Wrote {p}")
    return 0


def cmd_guide(args: argparse.Namespace) -> int:
    from . import guide_builder

    written = guide_builder.build_event_guides(
        event_yaml_path=args.event,
        output_dir=args.output,
        guide_key=args.guide_key,
        pdga_layouts_path=args.layouts,
    )
    for p in written:
        print(f"Wrote {p}")
    return 0


def cmd_pdf(args: argparse.Namespace) -> int:
    from . import pdf

    written = pdf.export_pdfs(args.files, output_dir=args.output)
    for p in written:
        print(f"Wrote {p}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdga-caddie-book",
        description="Generate phone-optimized caddie books and printable scorecards for PDGA-sanctioned tournaments.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("pull", help="Fetch all layouts for a PDGA tournament ID")
    sp.add_argument("tournament_id", help="PDGA tournament ID (numeric, from pdga.com/tour/event/N)")
    sp.add_argument("--output", "-o", help="Write JSON to this path (default: stdout)")
    sp.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    sp.set_defaults(func=cmd_pull)

    si = sub.add_parser("init", help="Scaffold a new event directory")
    si.add_argument("name", help="Directory name to create")
    si.add_argument("--tournament-id", type=int, help="Pre-fill the PDGA tournament ID")
    si.add_argument("--force", action="store_true", help="Overwrite existing dir")
    si.set_defaults(func=cmd_init)

    sb = sub.add_parser("build", help="Render reveal.js caddie books (one HTML per pool)")
    sb.add_argument("event", help="Path to event.yaml")
    sb.add_argument("--output", "-o", default="./output", help="Output directory (default: ./output)")
    sb.add_argument("--layouts", help="Path to cached layouts.json (default: layouts.json next to event.yaml, else fetch live)")
    sb.add_argument("--pool", action="append", help="Build only this pool (can repeat)")
    sb.set_defaults(func=cmd_build)

    so = sub.add_parser("og", help="Render each pool's share image (og:image, 1200x630) from the cover")
    so.add_argument("event", help="Path to event.yaml")
    so.add_argument("--output", "-o", help="Write here instead of deploy.og_image_pattern under the event dir")
    so.add_argument("--layouts", help="Path to cached layouts.json")
    so.add_argument("--pool", action="append", help="Only this pool (can repeat)")
    so.set_defaults(func=cmd_og)

    ss = sub.add_parser("scorecards", help="Render printable duplex scorecards")
    ss.add_argument("event", help="Path to event.yaml")
    ss.add_argument("--output", "-o", default="./output", help="Output directory (default: ./output)")
    ss.add_argument("--layouts", help="Path to cached layouts.json")
    ss.add_argument("--pool", action="append", help="Build only this pool (can repeat)")
    ss.set_defaults(func=cmd_scorecards)

    sg = sub.add_parser("spectator-guide", help="Render a spectator guide")
    sg.add_argument("event", help="Path to event.yaml")
    sg.add_argument("--output", "-o", default="./output", help="Output directory (default: ./output)")
    sg.add_argument("--layouts", help="Path to cached layouts.json")
    sg.set_defaults(func=cmd_guide, guide_key="spectator")

    sc_g = sub.add_parser("competitor-guide", help="Render a competitor guide")
    sc_g.add_argument("event", help="Path to event.yaml")
    sc_g.add_argument("--output", "-o", default="./output", help="Output directory (default: ./output)")
    sc_g.add_argument("--layouts", help="Path to cached layouts.json")
    sc_g.set_defaults(func=cmd_guide, guide_key="competitor")

    sd = sub.add_parser("pdf", help="Export HTML files to PDF via Playwright")
    sd.add_argument("files", nargs="+", help="HTML files to export")
    sd.add_argument("--output", "-o", help="Output directory (default: alongside source files)")
    sd.set_defaults(func=cmd_pdf)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
