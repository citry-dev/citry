# ruff: noqa: T201 - a maintenance script that prints its progress to stdout
"""
Draw the README's benchmark charts as PNGs and point the README at them.

GitHub and PyPI show a README without the docs site's stylesheet, so the
README cannot embed the charts themselves. This script renders the same
markup the landing page uses, with the same options, and takes a screenshot
of each chart in the light and the dark theme:

- ``errors``: ``<c-error-benchmark-chart>`` in its compact version,
  frameworks ordered by the share of their mistakes reported before the app
  runs, highest first, with the legend under the bars.
- ``speed``: ``<c-benchmark-chart>`` for the second page load in its compact
  version, one bar per framework, fastest first, with Citry's bar in the
  landing page's blue.

Each PNG goes to ``docs/assets/benchmarks/`` under a name that holds the
chart, the benchmark run, and a hash of the image, for example
``errors-20261021T182412Z-3f2a9c41d0b7-light.png``. The script never
overwrites an existing file: a released package's PyPI page
keeps loading the image it was published with, so changing that file would
change an old release's page. A new run, or a redrawn chart, gets a new file.

The script then rewrites each chart's README block between its
``benchmark-chart:<chart>`` markers (see ``benchmark_readme.py``) so it links
the new files and lists the new numbers in its alt text.

Run it from the repository root after a benchmark's data changes; it
needs Playwright and a Chromium binary. Name the charts to redraw, or none
to redraw both::

    uv run --no-sync python -m docs_site.scripts.benchmark_images speed
"""

from __future__ import annotations

import argparse
import base64
import sys
from typing import Any

from docs_site._internal.components import benchmark_chart, error_benchmark
from docs_site._internal.components.landing import LandingPage
from docs_site.scripts import benchmark_readme

CSS_DIR = benchmark_readme.REPO_ROOT / "docs_site" / "static" / "css"
FONT_PATH = benchmark_readme.REPO_ROOT / "docs_site" / "static" / "fonts" / "InterVariable.woff2"
# tokens.css loads the font by a path relative to itself, which means nothing
# in a page with no address, so the page carries the font inline instead.
FONT_URL = "../fonts/InterVariable.woff2"

# Two device pixels per CSS pixel keep the text sharp on a high-density screen
# while the README still displays the image at IMAGE_WIDTH.
SCALE = 2

# The page loads the docs site's own stylesheets and the landing page's, so
# each chart has the same colours, spacing, and font as on citry.dev. The
# wrapper is a `.prose` block, like a docs page, because that is where the
# legend's list rules apply. The chart's caption is hidden: the README
# heading above the image names the chart. The rounded border sets the image
# apart from GitHub's page in either theme, and the transparent corners
# outside it blend in.
#
# The speed chart takes its bar colours from the landing page's card, so its
# frame also carries the card's class and sits inside the landing page's
# shell, which sets the colours for each theme. The `.readme-chart` rules come
# last, so both images get the same frame; the shell's own page background is
# switched off, or it would show in the corners.
PAGE = """<!doctype html>
<html data-theme="{theme}"><head><meta charset="utf-8"><style>
{css}
html, body {{ margin: 0; background: transparent; }}
.landing-shell {{ min-height: 0; background: none; }}
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
<body><div class="landing-shell"><div class="landing-content">
<div class="{frame}">{chart}</div>
</div></div></body></html>"""

# The frame's classes for each chart; see PAGE.
FRAMES = {
    "errors": "readme-chart prose",
    "speed": "readme-chart prose landing-benchmark-card",
}


def chart_markup(chart: str, data: dict[str, Any]) -> str:
    """Return a chart's HTML, drawn with the same options as on the landing page (docs_site/content/index.md)."""
    if chart == "errors":
        view = error_benchmark.chart_view(data, sort="share", scale="applicable", short_names=True, compact=True)
        title = "Mistakes reported before the app runs, out of those that apply"
        return str(error_benchmark.ErrorBenchmarkChartMarkup(title=title, view=view))
    view = benchmark_chart.chart_view(data, benchmark_readme.SPEED_LOAD, sort="total", phases=False, compact=True)
    # The caption is hidden in the image; it stays only so the markup matches
    # the landing page's.
    title = f"Second load: time until usable, {data['source']['outputs']:,} entries"
    return str(benchmark_chart.BenchmarkChartMarkup(title=title, view=view, show_table=False))


def page_html(chart: str, theme: str, frame: str = FRAMES["errors"]) -> str:
    """Return a self-contained page that shows the chart's HTML in one theme, inside the given frame classes."""
    font = base64.b64encode(FONT_PATH.read_bytes()).decode("ascii")
    tokens = (CSS_DIR / "tokens.css").read_text(encoding="utf-8").replace(FONT_URL, f"data:font/woff2;base64,{font}")
    site = (CSS_DIR / "site.css").read_text(encoding="utf-8")
    css = f"{tokens}\n{site}\n{LandingPage.css}"
    return PAGE.format(theme=theme, css=css, width=benchmark_readme.IMAGE_WIDTH, frame=frame, chart=chart)


def main(argv: list[str] | None = None) -> int:
    """Screenshot the chosen charts in both themes, save new files, and rewrite their README blocks."""
    parser = argparse.ArgumentParser(description="Draw the README's benchmark charts and update their blocks.")
    parser.add_argument(
        "charts",
        nargs="*",
        choices=benchmark_readme.CHARTS,
        help="the charts to redraw (default: all of them)",
    )
    # Redrawing only the chart whose data changed keeps the other chart's
    # files and links as they are: another machine draws slightly different
    # pixels, which would save a new file for an unchanged chart.
    charts = parser.parse_args(argv).charts or list(benchmark_readme.CHARTS)
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
    datasets: dict[str, dict[str, Any]] = {}
    try:
        for chart in charts:
            benchmark_readme.find_block(readme, chart)
            datasets[chart] = benchmark_readme.load_data(chart)
            benchmark_readme.check_data(chart, datasets[chart])
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    names: dict[str, dict[str, str]] = {chart: {} for chart in charts}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for chart in charts:
                markup = chart_markup(chart, datasets[chart])
                for theme in benchmark_readme.THEMES:
                    # The colour scheme matters as well as data-theme: the
                    # stylesheet's prefers-color-scheme rules must agree with it.
                    page = browser.new_page(
                        viewport={"width": benchmark_readme.IMAGE_WIDTH + 40, "height": 600},
                        device_scale_factor=SCALE,
                        color_scheme="dark" if theme == "dark" else "light",
                    )
                    try:
                        page.set_content(page_html(markup, theme, FRAMES[chart]), wait_until="load")
                        page.wait_for_function("document.fonts.ready.then(() => true)")
                        png = page.locator(".readme-chart").screenshot(omit_background=True)
                    finally:
                        page.close()
                    run = benchmark_readme.run_id(chart, datasets[chart])
                    names[chart][theme] = _save(chart, run, png, theme)
        finally:
            browser.close()

    updated = readme
    for chart in charts:
        block = benchmark_readme.readme_block(
            chart,
            datasets[chart],
            light_name=names[chart]["light"],
            dark_name=names[chart]["dark"],
        )
        updated = benchmark_readme.replace_block(updated, chart, block)
    if updated != readme:
        benchmark_readme.README_PATH.write_text(updated, encoding="utf-8")
        print("updated README.md")
    else:
        print("README.md already up to date")
    return 0


def _save(chart: str, run: str, png: bytes, theme: str) -> str:
    """Write one PNG under its chart, run, and hash name unless that file exists; return the name."""
    name = benchmark_readme.image_name(chart, run, png, theme)
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
