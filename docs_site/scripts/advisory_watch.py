# ruff: noqa: T201 - a maintenance script that prints its progress to stdout
"""
Draw the README's advisory graphic and write the README block around it.

Citry's maintainers read the security advisories other frameworks and
libraries publish and check Citry for the same kinds of bug. The README and
the docs landing page each show a section about it: a heading, one sentence
with the number of advisories, a graphic with Citry's logo in the middle and
each project around it, and a short note with a link to the security page.

The numbers come from ``docs_site/data/advisory_watch.json``. This module
turns that file into:

- two SVG files, one for a light page and one for a dark page, which the
  README shows through ``<picture>``. A browser blocks scripts in an SVG
  shown as an image but runs its CSS, so the dashed lines still move toward
  Citry, and they stand still for a reader who asked the system for reduced
  motion;
- the README block between the ``advisory-watch`` marker comments;
- the same graphic as inline SVG for the landing page, coloured by the
  site's CSS color variables so the site's theme toggle recolours it (see
  ``docs_site/_internal/components/advisory_watch.py``).

Run it from the repository root after the data changes::

    uv run --no-sync python -m docs_site.scripts.advisory_watch

Each SVG goes to ``docs/assets/advisories/`` under a name that holds the
as-of month and a hash of the file, and an existing file is never
overwritten: a released package's PyPI page keeps loading the image it was
published with. The ``readme_advisory_watch`` validator redraws everything
from the data and fails when the README or the files fall behind.

This module uses only the standard library, because the validator loads it
by file path, where the ``docs_site`` package may not be importable.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import re
import sys
import textwrap
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
# The landing page repeats the README heading; the validator checks it there.
LANDING_PATH = REPO_ROOT / "docs_site" / "content" / "index.md"
DATA_PATH = REPO_ROOT / "docs_site" / "data" / "advisory_watch.json"
MARK_PATH = REPO_ROOT / "docs_site" / "static" / "img" / "citry-mark.svg"

# Files here stay on `main` for good, for the released PyPI pages that load
# them, so the README links them by absolute URL (PyPI renders it on its own
# domain, where a repository path would not resolve).
ASSET_DIR = REPO_ROOT / "docs" / "assets" / "advisories"
ASSET_URL = "https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/advisories"
DETAILS_URL = "https://citry.dev/security/#how-we-check"

HEADING = "Monitoring vulnerabilities across the ecosystem"
START_MARKER = "<!-- advisory-watch start -->"
END_MARKER = "<!-- advisory-watch end -->"

THEMES = ("light", "dark")
HASH_LENGTH = 12
_NAME_RE = re.compile(r"advisories-(?P<as_of>\d{4}-\d{2})-(?P<hash>[0-9a-f]{12})-(?P<theme>light|dark)\.svg")
_AS_OF_RE = re.compile(r"(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])")
_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)  # fmt: skip

# The README asks for this display width, and the SVG is drawn at it.
IMAGE_WIDTH = 720
IMAGE_HEIGHT = 360
# The README wraps its sentences at this width, so a diff stays readable.
_WRAP = 72

# Where each project's circle sits, placed by hand so the names clear each
# other, the lines, and the logo. A project in the data without a place here
# stops the script, since an automatic place could put it on top of another.
POSITIONS: dict[str, tuple[int, int]] = {
    "Django": (110, 128),
    "Next.js": (592, 92),
    "Angular": (214, 272),
    "Nuxt": (604, 262),
    "Svelte": (478, 78),
    "devalue": (238, 80),
    "React": (452, 296),
    "Vue": (664, 180),
    "Jinja": (64, 262),
}

# Colours for the two README files, copied from the site's CSS color
# variables in docs_site/static/css/tokens.css,
# with the card drawn like the README benchmark charts (--c-bg fill,
# --c-border edge). The landing page passes CSS variables instead.
FILE_COLORS = {
    "light": {
        "card": "#f2f4f7", "edge": "#d0d5db", "ink": "#2a2d3d",
        "accent": "#0d8a8a", "halo": "#ffffff", "ring": "#d6dbe4", "muted": "#525b6e",
    },
    "dark": {
        "card": "#151825", "edge": "#2d3043", "ink": "#e5e0d4",
        "accent": "#3eb4b4", "halo": "#1c1f2b", "ring": "#353a52", "muted": "#b3aa9a",
    },
}  # fmt: skip
INLINE_COLORS = {
    "card": "none", "edge": "none", "ink": "var(--landing-ink)",
    "accent": "var(--c-accent)", "halo": "var(--landing-panel)", "ring": "var(--landing-line)",
    "muted": "var(--landing-muted)",
}  # fmt: skip
_FONT = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def load_data(path: Path = DATA_PATH) -> dict[str, Any]:
    """Read the advisory data file."""
    return json.loads(path.read_text(encoding="utf-8"))


def check_data(data: dict[str, Any]) -> None:
    """
    Raise ``ValueError`` when the data cannot be drawn or does not add up.

    The total is stored as well as each count, so a count edited without the
    total (or the reverse) fails here rather than reaching the README.
    """
    as_of = data.get("as_of")
    if not isinstance(as_of, str) or not _AS_OF_RE.fullmatch(as_of):
        msg = f"advisory data 'as_of' must be a month like '2026-11', got {as_of!r}"
        raise ValueError(msg)
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        msg = "advisory data needs a non-empty 'projects' list"
        raise ValueError(msg)
    seen: set[str] = set()
    for project in projects:
        name, count = project.get("name"), project.get("count")
        if not isinstance(name, str) or not name:
            msg = f"advisory project needs a name, got {project!r}"
            raise ValueError(msg)
        if name in seen:
            msg = f"advisory project {name!r} is listed twice"
            raise ValueError(msg)
        seen.add(name)
        # bool is an int in Python, and True must not count as one advisory.
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            msg = f"advisory project {name!r} needs a whole count of at least 1, got {count!r}"
            raise ValueError(msg)
        if name not in POSITIONS:
            msg = f"advisory project {name!r} has no place in the graphic; add it to POSITIONS in advisory_watch.py"
            raise ValueError(msg)
    total = sum(project["count"] for project in projects)
    if data.get("total") != total:
        msg = f"advisory data 'total' is {data.get('total')!r}, but the project counts add up to {total}"
        raise ValueError(msg)


def intro(data: dict[str, Any]) -> str:
    """Return the sentence under the heading, with the total from the data."""
    return (
        f"We read {data['total']:,} security advisories from other frameworks and libraries "
        "and checked Citry for each kind of bug that could apply to it."
    )


def note(data: dict[str, Any]) -> str:
    """Return the note under the graphic, which says how current the numbers are."""
    match = _AS_OF_RE.fullmatch(data["as_of"])
    if match is None:
        msg = f"advisory data 'as_of' must be a month like '2026-11', got {data['as_of']!r}"
        raise ValueError(msg)
    month = _MONTHS[int(match["month"]) - 1]
    return f"Advisories published up to {month} {match['year']}. A monthly job lists new GitHub advisories for review."


def alt_text(data: dict[str, Any]) -> str:
    """Return the alt text, which lists every project's count for readers who cannot see the graphic."""
    counts = ", ".join(f"{project['name']} {project['count']:,}" for project in data["projects"])
    return (
        "Diagram: Citry's logo in the middle, linked to each project whose advisories we read, "
        f"with that project's number of advisories: {counts}."
    )


def mark_paths(path: Path = MARK_PATH) -> list[tuple[str, str]]:
    """
    Return the logo's two paths as (path data, stroke width), read from the artwork file.

    Reading the file, rather than copying its numbers, keeps the graphic in
    step with the one drawing every other logo is made from.
    """
    paths = re.findall(r'<path d="([^"]+)" stroke-width="([^"]+)"', path.read_text(encoding="utf-8"))
    # The mark is two strokes: the C and the 3.
    if len(paths) != 2:
        msg = f"{path} should hold the mark's two paths, found {len(paths)}"
        raise ValueError(msg)
    return paths


def _toward(px: float, py: float, cx: float, cy: float, r: float) -> tuple[float, float]:
    """Return the point at distance r from (cx, cy) in the direction of (px, py)."""
    a = math.atan2(py - cy, px - cx)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def svg(data: dict[str, Any], colors: dict[str, str], *, inline: bool = False) -> str:
    """
    Return the graphic as SVG text, drawn with the given colours.

    Each project is a circle sized by its count, with the count inside and
    the name beside it, joined to Citry's logo by a curved dashed line whose
    dashes move toward the logo. A line in one corner says what the numbers
    count. A file (``inline=False``) draws its own card; the inline version
    leaves the card to the landing page. Both carry the alt text as their
    label, since only it lists every count in words.

    Every class and animation name starts with ``aw-`` (advisory watch):
    inline, the SVG's stylesheet applies to the whole page, so plain names
    would clash.
    """
    mark = mark_paths()
    w, h = IMAGE_WIDTH, IMAGE_HEIGHT
    cx, cy, halo = w / 2, 178, 46
    biggest = max(project["count"] for project in data["projects"])
    font = "inherit" if inline else _FONT
    # The dashes move toward Citry because each line is drawn from the project
    # to the logo and `stroke-dashoffset` counts down, toward the line's end.
    style = (
        f".aw-root text{{font-family:{font};fill:{colors['ink']}}}"
        ".aw-root .aw-count{font-weight:700}"
        ".aw-root .aw-name{font-weight:650;letter-spacing:-.02em}"
        f".aw-root .aw-line{{fill:none;stroke:{colors['accent']};stroke-width:1.4;stroke-opacity:.7;"
        "stroke-linecap:round;stroke-dasharray:4 8;animation:aw-flow 1.6s linear infinite}"
        f".aw-root .aw-node{{fill:{colors['accent']};fill-opacity:.14;stroke:{colors['accent']};stroke-width:1.5}}"
        f".aw-root .aw-halo{{fill:{colors['halo']};stroke:{colors['ring']};stroke-width:1.5}}"
        f".aw-root .aw-mark{{fill:none;stroke:{colors['accent']}}}"
        f".aw-root .aw-legend{{fill:{colors['muted']}}}"
        "@keyframes aw-flow{to{stroke-dashoffset:-12}}"
        "@media (prefers-reduced-motion:reduce){.aw-root .aw-line{animation:none}}"
    )
    size = "" if inline else f' width="{w}" height="{h}"'
    label = f'role="img" aria-label="{html.escape(alt_text(data))}"'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" class="aw-root" viewBox="0 0 {w} {h}"{size} {label}>']
    out.append(f"<style>{style}</style>")
    if not inline:
        out.append(
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"'
            f' fill="{colors["card"]}" stroke="{colors["edge"]}"/>'
        )
    lines, nodes = [], []
    for index, project in enumerate(data["projects"]):
        name, count = project["name"], project["count"]
        x, y = POSITIONS[name]
        # Area grows with the count, so radius follows its square root.
        r = 7 + 21 * math.sqrt(count / biggest)
        ex, ey = _toward(x, y, cx, cy, halo + 5)
        # The line leaves the circle sideways, toward the logo, then bends in.
        side = 1 if cx > x else -1
        sx = x + side * (r + 4)
        # A staggered start keeps the dashes from marching in step.
        lines.append(
            f'<path class="aw-line" d="M{sx:.1f} {y} Q{(sx + ex) / 2:.1f} {y} {ex:.1f} {ey:.1f}"'
            f' style="animation-delay:-{index * 0.16:.2f}s"/>'
        )
        count_size = 9.5 + r * 0.32
        name_size = 14 + 10 * math.sqrt(count / biggest)
        # A circle above the logo carries its name on top, so the line that
        # leaves it downward does not cross the name.
        name_y = y - r - 7 if y < cy - 60 else y + r + name_size + 2
        nodes.append(
            f'<circle class="aw-node" cx="{x}" cy="{y}" r="{r:.1f}"/>'
            f'<text class="aw-count" x="{x}" y="{y + count_size * 0.36:.1f}" text-anchor="middle"'
            f' font-size="{count_size:.1f}">{count:,}</text>'
            f'<text class="aw-name" x="{x}" y="{name_y:.1f}" text-anchor="middle"'
            f' font-size="{name_size:.1f}">{html.escape(name)}</text>'
        )
    out += lines + nodes
    mark_w = 50
    mark_h = mark_w * 73 / 83
    # The artwork file lists the 3 first and the C second.
    (three_path, three_width), (c_path, c_width) = mark
    out.append(
        f'<circle class="aw-halo" cx="{cx:.0f}" cy="{cy}" r="{halo}"/>'
        f'<svg class="aw-mark" x="{cx - mark_w / 2:.1f}" y="{cy - mark_h / 2:.1f}"'
        f' width="{mark_w}" height="{mark_h:.1f}" viewBox="0.5 13.5 83 73">'
        f'<path d="{three_path}" stroke-width="{three_width}" stroke-linecap="round"/>'
        f'<path d="{c_path}" stroke-width="{c_width}"/></svg>'
    )
    # Without this line nothing visible says what the numbers in the circles
    # count, and a reader could take them for problems found in Citry.
    out.append(
        f'<text class="aw-legend" x="18" y="{h - 16}" font-size="12">'
        "Number in each circle: that project's published security advisories</text>"
    )
    out.append("</svg>")
    return "".join(out)


def file_svg(data: dict[str, Any], theme: str) -> str:
    """Return the README file for one theme."""
    if theme not in THEMES:
        msg = f"Unknown image theme {theme!r}; use one of {list(THEMES)}"
        raise ValueError(msg)
    return svg(data, FILE_COLORS[theme]) + "\n"


def inline_svg(data: dict[str, Any]) -> str:
    """Return the graphic for the landing page, coloured by the site's CSS variables."""
    return svg(data, INLINE_COLORS, inline=True)


def image_name(data: dict[str, Any], content: str, theme: str) -> str:
    """Return the file name for one theme's SVG: the as-of month, a hash of the file, and the theme."""
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:HASH_LENGTH]
    return f"advisories-{data['as_of']}-{digest}-{theme}.svg"


def parse_image_name(name: str) -> dict[str, str] | None:
    """Split an image file name into its as-of month, hash, and theme, or return None if it is not one."""
    match = _NAME_RE.fullmatch(name)
    return match.groupdict() if match else None


def readme_block(data: dict[str, Any], light_name: str, dark_name: str) -> str:
    """Return the README block, markers included, for the given data and image files."""
    return "\n".join(
        [
            START_MARKER,
            "<!-- Written by `python -m docs_site.scripts.advisory_watch` from",
            f"     {DATA_PATH.relative_to(REPO_ROOT).as_posix()}. Rerun it rather than",
            "     editing this block by hand. -->",
            "",
            f"## {HEADING}",
            "",
            textwrap.fill(intro(data), _WRAP),
            "",
            "<picture>",
            "  <source",
            '    media="(prefers-color-scheme: dark)"',
            f'    srcset="{ASSET_URL}/{dark_name}"',
            "  >",
            "  <img",
            f'    src="{ASSET_URL}/{light_name}"',
            f'    alt="{html.escape(alt_text(data))}"',
            f'    width="{IMAGE_WIDTH}"',
            "  >",
            "</picture>",
            "",
            textwrap.fill(note(data), _WRAP),
            f"[How we check]({DETAILS_URL})",
            END_MARKER,
        ]
    )


def find_block(readme: str) -> tuple[int, int]:
    """
    Return where the block starts and ends in the README text.

    The end is the offset just past the end marker. No block, more than one,
    or an end before the start raises ``ValueError``, since the script would
    not know what to rewrite.
    """
    starts = [m.start() for m in re.finditer(re.escape(START_MARKER), readme)]
    ends = [m.end() for m in re.finditer(re.escape(END_MARKER), readme)]
    if len(starts) != 1 or len(ends) != 1:
        msg = f"README needs exactly one {START_MARKER} ... {END_MARKER} pair"
        raise ValueError(msg)
    if ends[0] < starts[0]:
        msg = "README has the advisory-watch end marker before its start marker"
        raise ValueError(msg)
    return starts[0], ends[0]


def replace_block(readme: str, block: str) -> str:
    """Return the README text with the block replaced by ``block``."""
    start, end = find_block(readme)
    return readme[:start] + block + readme[end:]


def image_names_in(block: str) -> list[str]:
    """Return the file names of every advisory image the block links, in order."""
    return re.findall(re.escape(ASSET_URL) + r"/([^\"'\s>]+)", block)


def save(name: str, content: str, asset_dir: Path | None = None) -> bool:
    """Write one SVG unless a file of that name exists; return whether it wrote one."""
    # Read ASSET_DIR at call time, so a caller that points it elsewhere is obeyed.
    path = (asset_dir or ASSET_DIR) / name
    # The hash is part of the name, so an existing file already holds these
    # exact bytes. Leaving it alone keeps every published link stable.
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    """Draw both SVGs from the data, save new files, and rewrite the README block."""
    readme = README_PATH.read_text(encoding="utf-8")
    data = load_data()
    # Check everything before writing, so bad data leaves no files behind.
    try:
        check_data(data)
        find_block(readme)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    names = {}
    for theme in THEMES:
        content = file_svg(data, theme)
        names[theme] = image_name(data, content, theme)
        wrote = save(names[theme], content)
        print(f"{'wrote' if wrote else 'kept '} docs/assets/advisories/{names[theme]}")
    updated = replace_block(readme, readme_block(data, names["light"], names["dark"]))
    if updated != readme:
        README_PATH.write_text(updated, encoding="utf-8")
        print("updated README.md")
    else:
        print("README.md already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
