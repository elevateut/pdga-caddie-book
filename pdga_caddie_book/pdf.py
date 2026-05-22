"""PDF export via Playwright.

Wraps Playwright's chromium PDF API. Used by the `pdga-caddie-book pdf`
subcommand to convert generated HTML scorecards (or any other HTML) to PDF.

Install Playwright + browser bundle separately:
    pip install pdga-caddie-book[pdf]
    playwright install chromium
"""

from __future__ import annotations

import os
from typing import Sequence


def export_pdfs(
    html_files: Sequence[str],
    output_dir: str | None = None,
    page_format: str = "Letter",
    margin: str = "0.25in",
) -> list[str]:
    """Render each HTML file to a same-named PDF.

    Returns list of PDF paths written.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise SystemExit(
            "Playwright is required for PDF export. Install with:\n"
            "    pip install 'pdga-caddie-book[pdf]'\n"
            "    playwright install chromium"
        ) from e

    written: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Size viewport to Letter portrait at 96dpi so JS clientHeight/scrollHeight
        # measurements during auto-fit match the final printed dimensions.
        ctx = browser.new_context(viewport={"width": 816, "height": 1056})
        for src in html_files:
            src_abs = os.path.abspath(src)
            dest_dir = output_dir or os.path.dirname(src_abs)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, os.path.basename(src).replace(".html", ".pdf"))
            page = ctx.new_page()
            page.emulate_media(media="print")
            page.goto(f"file://{src_abs}", wait_until="networkidle")
            # If the page declares it runs an auto-fit step, wait for it.
            try:
                page.wait_for_function(
                    "() => document.documentElement.getAttribute('data-fit-done') === '1'",
                    timeout=3000,
                )
            except Exception:
                pass  # page doesn't use auto-fit; ignore
            # Warn if any auto-fit element bottomed out — notes will be illegible.
            if page.locator("[data-fit-overflow]").count() > 0:
                print(
                    f"WARN {os.path.basename(src)}: notes overflowed even at 2-col + 5px font. "
                    "Consider shortening note text or splitting into a dedicated layout."
                )
            page.pdf(
                path=dest,
                format=page_format,
                print_background=True,
                margin={"top": margin, "bottom": margin, "left": margin, "right": margin},
            )
            page.close()
            written.append(dest)
        browser.close()
    return written
