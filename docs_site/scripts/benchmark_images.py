# ruff: noqa: T201 - a maintenance script that prints its progress to stdout
"""
Draw the README's benchmark chart as PNGs and point the README at them.

GitHub and PyPI show a README without the docs site's stylesheet, so the
README cannot embed the chart itself. This script renders the same
``<c-error-benchmark-chart>`` markup the landing page uses (its compact
version: frameworks ordered by the share of their mistakes reported before
the app runs, highest first, with the legend under the bars), with the
site's own stylesheet and font, and takes a screenshot in the light and the
dark theme.

Each PNG goes to ``docs/assets/benchmarks/`` under a name that holds the
benchmark run and a hash of the image, for example
``errors-20261021T182412Z-3f2a9c41d0b7-light.png``. The script never
overwrites an existing file: a released package's PyPI page
keeps loading the image it was published with, so changing that file would
change an old release's page. A new run, or a redrawn chart, gets a new file.

The script then rewrites the README block between the
``benchmark-chart:errors`` markers (see ``benchmark_readme.py``) so it links
the new files and lists the new counts in its alt text.

Run it from the repository root after the error benchmark data changes; it
needs Playwright and a Chromium binary::

    uv run --no-sync python -m docs_site.scripts.benchmark_images
"""

from __future__ import annotations

import base64
import sys
from typing import Any

from docs_site._internal.components.error_benchmark import ErrorBenchmarkChartMarkup, chart_view
from docs_site.scripts import benchmark_readme

CSS_DIR = benchmark_readme.REPO_ROOT / "docs_site" / "static" / "css"
FONT_PATH = benchmark_readme.REPO_ROOT / "docs_site" / "static" / "fonts" / "InterVariable.woff2"
# tokens.css loads the font by a path relative to itself, which means nothing
# in a page with no address, so the page carries the font inline instead.
FONT_URL = "../fonts/InterVariable.woff2"

# Two device pixels per CSS pixel keep the text sharp on a high-density screen
# while the README still displays the image at IMAGE_WIDTH.
SCALE = 2

# The page loads the docs site's own stylesheets, so the chart has the same
# colours, spacing, and font as on citry.dev. The wrapper is a `.prose`
# block, like a docs page, because that is where the legend's list rules
# apply. The chart's caption is hidden: the README heading above the image
# names the chart. The rounded border sets the image apart from GitHub's page
# in either theme, and the transparent corners outside it blend in.
PAGE = """<!doctype html>
<html data-theme="{theme}"><head><meta charset="utf-8"><style>
{css}
html, body {{ margin: 0; background: transparent; }}
.readme-chart {{
  box-sizing: border-box;
  width: {width}px;
  max-width: none;
  padding: 20px 24px 18px;
  border: 1px solid var(--c-border);
  border-radius: 12px;
  background: var(--c-bg);
}}
.readme-chart .bench-chart {{ margin: 0; }}
.readme-chart .bench-chart__title {{ display: none; }}
</style></head>
<body><div class="readme-chart prose">{chart}</div></body></html>"""


def chart_markup(data: dict[str, Any]) -> str:
    """Return the chart's HTML, drawn with the same options as on the landing page (docs_site/content/index.md)."""
    view = chart_view(data, sort="share", scale="applicable", short_names=True, compact=True)
    title = "Mistakes reported before the app runs, out of those that apply"
    return str(ErrorBenchmarkChartMarkup(title=title, view=view))


def page_html(chart: str, theme: str) -> str:
    """Return a self-contained page that shows the chart in one theme."""
    font = base64.b64encode(FONT_PATH.read_bytes()).decode("ascii")
    tokens = (CSS_DIR / "tokens.css").read_text(encoding="utf-8").replace(FONT_URL, f"data:font/woff2;base64,{font}")
    site = (CSS_DIR / "site.css").read_text(encoding="utf-8")
    return PAGE.format(theme=theme, css=f"{tokens}\n{site}", width=benchmark_readme.IMAGE_WIDTH, chart=chart)


def main() -> int:
    """Screenshot the chart in both themes, save new files, and rewrite the README block."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415 - optional dependency
    except ImportError:
        print(
            "error: Playwright is not installed. Install it with"
            " `uv sync --extra social-cards` and `playwright install chromium`.",
            file=sys.stderr,
        )
        return 1

    # Check the README and the data before drawing anything, so a missing
    # marker or an incomplete run leaves no image files behind.
    readme = benchmark_readme.README_PATH.read_text(encoding="utf-8")
    data = benchmark_readme.load_data()
    try:
        benchmark_readme.find_block(readme)
        benchmark_readme.static_shares(data)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    chart = chart_markup(data)
    names: dict[str, str] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for theme in benchmark_readme.THEMES:
                # The colour scheme matters as well as data-theme: the
                # stylesheet's prefers-color-scheme rules must agree with it.
                page = browser.new_page(
                    viewport={"width": benchmark_readme.IMAGE_WIDTH + 40, "height": 600},
                    device_scale_factor=SCALE,
                    color_scheme="dark" if theme == "dark" else "light",
                )
                try:
                    page.set_content(page_html(chart, theme), wait_until="load")
                    page.wait_for_function("document.fonts.ready.then(() => true)")
                    png = page.locator(".readme-chart").screenshot(omit_background=True)
                finally:
                    page.close()
                names[theme] = _save(data["run"], png, theme)
        finally:
            browser.close()

    block = benchmark_readme.readme_block(data, light_name=names["light"], dark_name=names["dark"])
    updated = benchmark_readme.replace_block(readme, block)
    if updated != readme:
        benchmark_readme.README_PATH.write_text(updated, encoding="utf-8")
        print("updated README.md")
    else:
        print("README.md already up to date")
    return 0


def _save(run: str, png: bytes, theme: str) -> str:
    """Write one PNG under its run-and-hash name unless that file exists; return the name."""
    name = benchmark_readme.image_name(run, png, theme)
    path = benchmark_readme.ASSET_DIR / name
    where = path.relative_to(benchmark_readme.REPO_ROOT)
    # The hash is part of the name, so an existing file already holds these
    # exact bytes. Leaving it untouched keeps every published link stable.
    if path.exists():
        print(f"kept  {where}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)
        print(f"wrote {where}")
    return name


if __name__ == "__main__":
    sys.exit(main())
