# ruff: noqa: T201 - a maintenance script that prints its progress to stdout
"""
Derive every raster the project ships from the one piece of artwork.

The C3 mark is drawn once, as strokes in ``docs_site/static/img/``: a square
frame (``citry-icon.svg``) for anything that sits in a square slot, and a wide
frame (``citry-mark.svg``) for anything that sits beside text. Each PNG below is
a screenshot of one of those two at a different size. Generating them rather
than hand-exporting means a change to the artwork reaches every icon by
re-running this script, with nothing left behind on the old drawing.

Browser and phone icons, into ``docs_site/static/img/``:

- ``favicon.svg`` - a copy of the artwork. Modern browsers prefer it, and
  because it carries its own ``prefers-color-scheme`` rule it is the only icon
  that follows the reader's theme.
- ``favicon-16.png`` / ``favicon-32.png`` - the classic tab sizes, transparent,
  for browsers that do not take an SVG icon.
- ``favicon.png`` - a 512px copy, and also the image a chat app or social site
  shows when it unfurls a link to a page that has no card of its own.
- ``apple-touch-icon.png`` - 180px for the iOS home screen.

Everything else that carries the mark:

- ``docs/assets/citry-wordmark.png`` - the mark with the project's name beside
  it, for the top of a README. GitHub, PyPI, and the VS Code Marketplace all
  render a README, and PyPI needs the image as a PNG behind an absolute URL, so
  a PNG is what they all get.
- ``docs/assets/citry-mark.png`` - the mark on its own, for anywhere the name is
  already spelled out next to it.
- ``docs/assets/citry-avatar.png`` - 512px square for the GitHub organisation
  and repository profile pictures, which have to be uploaded by hand.
- ``packages/editors/vscode/images/icon.png`` - 256px for the VS Code
  Marketplace listing.

Most files are transparent. The three that are not (the iOS icon, the
link-preview image, and the GitHub profile picture) each get a white ground
because their host composites transparency into something unpredictable: iOS
fills it with black, a chat client uses whatever its own theme is, and GitHub
shows a profile picture against both. Those three also hold the artwork away
from the edges, because each of those hosts rounds the corners of what it is
given.

A PNG cannot follow a theme, so they are all drawn in the light-mode teal, which
is the brand colour and reads on both a white page and a dark one.

Run it after editing the artwork; it needs Playwright and a Chromium binary::

    uv run --no-sync python docs_site/scripts/icons.py
"""

from __future__ import annotations

import base64
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IMG_DIR = REPO_ROOT / "docs_site" / "static" / "img"

# The two framings of the same drawing: square for icons, wide for lockups.
SQUARE_ART = IMG_DIR / "citry-icon.svg"
WIDE_ART = IMG_DIR / "citry-mark.svg"

# The artwork's light-mode stroke, forced so a PNG never depends on the machine
# that rendered it. Matches --c-accent in docs_site/static/css/tokens.css.
BRAND_TEAL = "#0d8a8a"

# Used by the icons that cannot be transparent (see the module docstring). The
# inset keeps the artwork clear of the corners those hosts round off.
SOLID_GROUND = "#ffffff"
SOLID_INSET = 0.12


@dataclass(frozen=True)
class IconSpec:
    """One raster file to write: where it goes, how big, on what ground, how far inset."""

    path: Path
    width: int
    height: int
    art: Path
    ground: str = ""  # empty means a transparent background
    inset: float = 0.0  # fraction of the canvas left clear on each side

    def describe(self) -> str:
        """One line for the run log."""
        ground = self.ground if self.ground else "transparent"
        where = self.path.relative_to(REPO_ROOT)
        return f"{where!s:<48} {self.width:>4}x{self.height:<4} {ground}"


def _square(path: Path, size: int, *, solid: bool = False) -> IconSpec:
    """A square icon cut from the square artwork."""
    return IconSpec(
        path=path,
        width=size,
        height=size,
        art=SQUARE_ART,
        ground=SOLID_GROUND if solid else "",
        inset=SOLID_INSET if solid else 0.0,
    )


# The wide artwork's frame is 83 by 73 units, so a wide PNG keeps that ratio.
def _wide(path: Path, width: int) -> IconSpec:
    """A wide lockup cut from the wide artwork, at the artwork's own proportions."""
    return IconSpec(path=path, width=width, height=round(width * 73 / 83), art=WIDE_ART)


ICONS = (
    _square(IMG_DIR / "favicon-16.png", 16),
    _square(IMG_DIR / "favicon-32.png", 32),
    _square(IMG_DIR / "favicon.png", 512, solid=True),
    _square(IMG_DIR / "apple-touch-icon.png", 180, solid=True),
    _square(REPO_ROOT / "docs" / "assets" / "citry-avatar.png", 512, solid=True),
    _square(REPO_ROOT / "packages" / "editors" / "vscode" / "images" / "icon.png", 256),
    _wide(REPO_ROOT / "docs" / "assets" / "citry-mark.png", 240),
)

# The wordmark: the mark with the project's name beside it, for the top of a
# README. It is drawn entirely in the brand teal rather than teal-and-ink like
# the site header, because one flat PNG has to sit on a white page and a dark
# one without a second version.
WORDMARK_PATH = REPO_ROOT / "docs" / "assets" / "citry-wordmark.png"
WORDMARK_FONT = REPO_ROOT / "docs_site" / "static" / "fonts" / "InterVariable.woff2"

# Drawn at three times the width the README asks for so it stays sharp on a
# high-density screen. The name is set in the same Inter the site uses, loaded
# from the repository's own copy so the letterforms do not depend on which
# machine ran this script.
WORDMARK_SCALE = 3
WORDMARK_FONT_SIZE = 30 * WORDMARK_SCALE

# Beside the name, the mark sits slightly shorter than the letters rather than
# towering over them. The site header is the reference: a 1rem mark against a
# 1.05rem name, spaced 0.5rem apart (`.djc-logo` in site.css). Holding those two
# proportions here makes the README lockup and the header read as one lockup.
MARK_TO_NAME = 1 / 1.05
GAP_TO_NAME = 0.5 / 1.05

WORDMARK_MARK_HEIGHT = round(WORDMARK_FONT_SIZE * MARK_TO_NAME)
WORDMARK_GAP = round(WORDMARK_FONT_SIZE * GAP_TO_NAME)

# Where the lockup's *ink* is, which is not where its layout box is. A line box
# is only as tall as the line-height, so the tail of the y hangs below it; the
# name's negative letter-spacing and the last glyph's side bearing likewise push
# past the right edge. Cropping to the layout box therefore shaves both. Chromium
# reports the real ink extent through measureText's actualBoundingBox* values, so
# the crop is taken from those and from the mark's own box, whichever reaches
# further on each side.
INK_BOX_SCRIPT = """() => {
  const svg = document.querySelector('.lockup svg');
  const name = document.querySelector('.name');
  const style = getComputedStyle(name);

  const ctx = document.createElement('canvas').getContext('2d');
  ctx.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
  ctx.letterSpacing = style.letterSpacing;
  const m = ctx.measureText(name.textContent);

  // Half-leading splits the difference between the line box and the font's own
  // em box, which is what fixes the baseline inside the line.
  const rect = name.getBoundingClientRect();
  const leading = (rect.height - (m.fontBoundingBoxAscent + m.fontBoundingBoxDescent)) / 2;
  const baseline = rect.top + leading + m.fontBoundingBoxAscent;

  const mark = svg.getBoundingClientRect();
  const left = Math.min(mark.left, rect.left - m.actualBoundingBoxLeft);
  const top = Math.min(mark.top, baseline - m.actualBoundingBoxAscent);
  const right = Math.max(mark.right, rect.left + m.actualBoundingBoxRight);
  const bottom = Math.max(mark.bottom, baseline + m.actualBoundingBoxDescent);

  // Out to whole pixels, so a fractional edge is included rather than sliced.
  const x = Math.floor(left);
  const y = Math.floor(top);
  return { x, y, width: Math.ceil(right) - x, height: Math.ceil(bottom) - y };
}"""

WORDMARK_PAGE = """<!doctype html>
<html><head><style>
  @font-face {{
    font-family: 'Inter';
    src: url('data:font/woff2;base64,{font}') format('woff2');
    font-weight: 100 900;
  }}
  html, body {{ margin: 0; background: transparent; }}
  /* Room on every side so ink that spills past the layout box still lands on
     the page, and the crop below has something to crop to. */
  body {{ padding: 60px; }}
  .lockup {{
    display: inline-flex; align-items: center; gap: {gap}px;
    font-family: 'Inter', sans-serif;
  }}
  .lockup svg {{ display: block; height: {mark}px; width: auto; }}
  .lockup svg path {{ stroke: {stroke} !important; }}
  .name {{
    color: {stroke};
    font-size: {size}px;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1;
  }}
</style></head>
<body><span class="lockup">{svg}<span class="name">Citry</span></span></body></html>"""

# The artwork is inlined into this page and screenshotted. Forcing the stroke
# here overrides the theme rule the SVG carries, so the output is deterministic.
PAGE = """<!doctype html>
<html><head><style>
  html, body {{ margin: 0; padding: 0; background: {ground}; }}
  .frame {{
    width: {width}px; height: {height}px;
    display: flex; align-items: center; justify-content: center;
    box-sizing: border-box; padding: {pad}px;
  }}
  .frame svg {{ display: block; width: 100%; height: 100%; }}
  .frame svg path {{ stroke: {stroke} !important; }}
</style></head>
<body><div class="frame">{svg}</div></body></html>"""


def main() -> int:
    """Copy the artwork to favicon.svg, then screenshot every raster size."""
    for art in (SQUARE_ART, WIDE_ART):
        if not art.is_file():
            print(f"error: no artwork at {art}", file=sys.stderr)
            return 1

    favicon_svg = IMG_DIR / "favicon.svg"
    shutil.copyfile(SQUARE_ART, favicon_svg)
    print(f"wrote {favicon_svg.relative_to(REPO_ROOT)!s:<48} copied from {SQUARE_ART.name}")

    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415 - optional dependency
    except ImportError:
        print(
            "error: Playwright is not installed. Install it with"
            " `uv sync --extra social-cards` and `playwright install chromium`.",
            file=sys.stderr,
        )
        return 1

    art_source = {path: path.read_text(encoding="utf-8") for path in (SQUARE_ART, WIDE_ART)}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for spec in ICONS:
                spec.path.parent.mkdir(parents=True, exist_ok=True)
                _shoot(browser, art_source[spec.art], spec)
                print(f"wrote {spec.describe()}")
            size = _shoot_wordmark(browser, art_source[WIDE_ART])
            print(f"wrote {WORDMARK_PATH.relative_to(REPO_ROOT)!s:<48} {size} transparent")
        finally:
            browser.close()
    return 0


def _shoot(browser: object, svg: str, spec: IconSpec) -> None:
    """Render the artwork at one size and save it as a PNG."""
    page = browser.new_page(  # type: ignore[attr-defined]
        viewport={"width": spec.width, "height": spec.height},
        device_scale_factor=1,
    )
    try:
        page.set_content(
            PAGE.format(
                svg=svg,
                width=spec.width,
                height=spec.height,
                pad=round(min(spec.width, spec.height) * spec.inset),
                ground=spec.ground or "transparent",
                stroke=BRAND_TEAL,
            ),
            wait_until="load",
        )
        page.screenshot(path=str(spec.path), omit_background=not spec.ground)
    finally:
        page.close()


def _shoot_wordmark(browser: object, svg: str) -> str:
    """Render the mark with the name beside it, cropped to the lockup. Returns its size."""
    font = base64.b64encode(WORDMARK_FONT.read_bytes()).decode("ascii")
    page = browser.new_page(viewport={"width": 1200, "height": 400})  # type: ignore[attr-defined]
    try:
        page.set_content(
            WORDMARK_PAGE.format(
                svg=svg,
                font=font,
                gap=WORDMARK_GAP,
                mark=WORDMARK_MARK_HEIGHT,
                size=WORDMARK_FONT_SIZE,
                stroke=BRAND_TEAL,
            ),
            wait_until="load",
        )
        page.wait_for_function("document.fonts.ready.then(() => true)")
        box = page.evaluate(INK_BOX_SCRIPT)
        page.screenshot(path=str(WORDMARK_PATH), clip=box, omit_background=True)
        return f"{round(box['width']):>4}x{round(box['height']):<4}"
    finally:
        page.close()


if __name__ == "__main__":
    sys.exit(main())
