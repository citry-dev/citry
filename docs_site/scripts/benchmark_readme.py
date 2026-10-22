"""
Write and check the benchmark chart block in the repository README.

The README shows the error benchmark chart as a PNG, because GitHub and PyPI
show a README without the docs site's stylesheet, so the chart's HTML would
not draw. ``docs_site/scripts/benchmark_images.py``
takes the screenshots; this module decides what the README says around them:
the heading, one sentence, the image links, and the alt text that lists every
framework's count for readers who cannot see the image.

Everything here is computed from ``docs_site/data/error_prevention.json``, so
the README and the docs site's charts tell the same story. The
``readme_benchmark_charts`` validator rebuilds the block with these functions
and fails when the README no longer matches the data, for example after a new
benchmark run, until someone reruns the image script.

This module uses only the standard library, because the validator loads it
by file path, where the ``docs_site`` package and the docs dependencies may
be missing.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
DATA_PATH = REPO_ROOT / "docs_site" / "data" / "error_prevention.json"

# The images live on `main` for good: a release's PyPI page keeps loading the
# file it was published with, so a file here is never overwritten or deleted.
ASSET_DIR = REPO_ROOT / "docs" / "assets" / "benchmarks"
# PyPI renders the README on its own domain, where a repository path would
# not resolve, so the README links each image by its absolute URL.
ASSET_URL = "https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/benchmarks"
DETAILS_URL = "https://citry.dev/about/benchmarks/#errors-how-we-measured"

# The block sits between these two comments. Both renderers hide comments, so
# readers see only the block itself.
START_MARKER = "<!-- benchmark-chart:errors start -->"
END_MARKER = "<!-- benchmark-chart:errors end -->"

# The README asks for this display width; the image script draws the chart at
# the same width, twice as many pixels, so the text stays sharp.
IMAGE_WIDTH = 720

# The buckets in which a tool reported the mistake before the app ran. Their
# sum is the number beside each bar in the chart.
STATIC_BUCKETS = ("static-error", "static-warning")
# Every status a record can have; the chart rejects any other, and so does
# this module, so the two cannot count the same data differently.
_STATUSES = frozenset({"ported", "not-applicable", "prevented", "missing"})

# Shorter names for the compact chart on the landing page and in the README.
# Only django-components drops its "+ HTMX + Alpine": it is a component
# library, and the suffix would wrap its name onto three lines on a phone.
# The chart component reads this table too, so the image and its alt text
# name every framework the same way.
SHORT_NAMES = {"django-components": "django-components"}

# Which Citry each error benchmark run measured, as the README says it under
# the chart. A released 0.6.0 reports far fewer mistakes before the app runs
# than this run's code, so the README must not show the count without the
# version. The landing page's error card repeats the same sentence.
VERSION_NOTES = {
    "20261021T182412Z": "Citry 0.6.1, measured before its release.",
}

# A file name records the chart, the benchmark run it shows, the first
# characters of the PNG's SHA-256, and the colour theme. The run ties the
# image to the data; the hash gives a redrawn image of the same run a new
# name instead of replacing a file a published page may load.
HASH_LENGTH = 12
THEMES = ("light", "dark")
# The run id may hold hyphens: the error runner adds "-2" to a second run that
# starts in the same second. The fixed-length hash and the theme at the end
# keep the name unambiguous.
_RUN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")
_NAME_RE = re.compile(r"errors-(?P<run>[A-Za-z0-9][A-Za-z0-9-]*)-(?P<hash>[0-9a-f]{12})-(?P<theme>light|dark)\.png")


def load_data() -> dict[str, Any]:
    """Read the error benchmark data file the docs site draws."""
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def static_shares(data: dict[str, Any], *, short_names: bool = False) -> list[tuple[str, int, int]]:
    """
    Return each framework's name, its count of mistakes reported before the app ran, and how many apply to it.

    The list is ordered from the highest share (count divided by the mistakes
    that apply) to the lowest, and frameworks with equal shares keep the data
    file's order. This is the order of the chart drawn with ``sort="share"``,
    so the alt text reads the bars from top to bottom. With ``short_names``,
    a framework listed in ``SHORT_NAMES`` gets its shorter name, as in that
    chart.

    Like the chart, it needs exactly one record per framework and mistake, and
    raises ``ValueError`` on a missing, repeated, or unknown record.
    """
    keys = [framework["key"] for framework in data["frameworks"]]
    expected = {(key, mistake["id"]) for key in keys for mistake in data["mistakes"]}
    seen: set[tuple[str, str]] = set()
    counts = dict.fromkeys(keys, 0)
    # A mistake applies to a framework unless it has no equivalent there or
    # the framework's design prevents it.
    applicable = dict.fromkeys(keys, 0)
    for record in data["results"]:
        pair = (record["framework"], record["mistake"])
        label = f"{pair[0]} / {pair[1]}"
        # A repeated or stray record would count twice or count for nobody,
        # and the chart drawn from the same data would disagree.
        if pair not in expected:
            msg = f"Error benchmark record {label} names a framework or mistake the data does not list"
            raise ValueError(msg)
        if pair in seen:
            msg = f"Error benchmark data has more than one record for {label}"
            raise ValueError(msg)
        seen.add(pair)
        status = record["status"]
        if status not in _STATUSES:
            msg = f"Error benchmark record {label} has an unknown status {status!r}"
            raise ValueError(msg)
        if status == "missing" or (status == "ported" and record["bucket"] is None):
            # Data written by `error_benchmark_data.py --allow-partial` can
            # hold cases nobody wrote or scored yet. The README has no room to
            # say a count is incomplete, so it refuses them.
            msg = (
                f"Error benchmark case {label} has no result; "
                "regenerate docs_site/data/error_prevention.json without --allow-partial "
                "before drawing the README chart"
            )
            raise ValueError(msg)
        if status == "ported":
            applicable[pair[0]] += 1
            if record["bucket"] in STATIC_BUCKETS:
                counts[pair[0]] += 1
    absent = sorted(expected - seen)
    if absent:
        msg = f"Error benchmark data has no record for: {[f'{key} / {mistake}' for key, mistake in absent]}"
        raise ValueError(msg)
    empty = [key for key, count in applicable.items() if not count]
    if empty:
        msg = f"Error benchmark frameworks have no mistakes that apply to them: {empty}"
        raise ValueError(msg)
    names = {
        framework["key"]: SHORT_NAMES.get(framework["key"], framework["name"]) if short_names else framework["name"]
        for framework in data["frameworks"]
    }
    rows = [(names[key], counts[key], applicable[key]) for key in keys]
    # Python's sort is stable, so equal shares keep the data's order.
    return sorted(rows, key=lambda row: -row[1] / row[2])


def version_note(data: dict[str, Any]) -> str:
    """
    Return the sentence that says which Citry the README's error chart measured.

    The data file does not record the version, so each run's note lives in
    ``VERSION_NOTES``. A run without one raises ``ValueError``, so a new run
    cannot reach the README under an old run's version.
    """
    try:
        return VERSION_NOTES[data["run"]]
    except KeyError:
        msg = (
            f"No version note for error benchmark run {data['run']}; add one to VERSION_NOTES in "
            "docs_site/scripts/benchmark_readme.py, and update the note on the landing page's error card"
        )
        raise ValueError(msg) from None


def image_name(run: str, png: bytes, theme: str) -> str:
    """Return the file name for one theme's PNG of the given benchmark run."""
    if theme not in THEMES:
        msg = f"Unknown image theme {theme!r}; use one of {list(THEMES)}"
        raise ValueError(msg)
    if not _RUN_RE.fullmatch(run):
        # The run id goes into a URL and a file name, so it must stay plain.
        msg = f"Benchmark run id {run!r} must contain only letters, digits, and hyphens"
        raise ValueError(msg)
    digest = hashlib.sha256(png).hexdigest()[:HASH_LENGTH]
    return f"errors-{run}-{digest}-{theme}.png"


def parse_image_name(name: str) -> dict[str, str] | None:
    """Split an image file name into its run, hash, and theme, or return None if it is not one."""
    match = _NAME_RE.fullmatch(name)
    return match.groupdict() if match else None


def readme_block(data: dict[str, Any], light_name: str, dark_name: str) -> str:
    """
    Return the README block, markers included, for the given data and image files.

    GitHub picks the dark image for a reader in dark mode. PyPI may ignore the
    ``<source>``; each image carries its own background, so either works.
    """
    frameworks = len(data["frameworks"])
    mistakes = len(data["mistakes"])
    shares = static_shares(data, short_names=True)
    counts = ", ".join(f"{name} {count} of {applicable}" for name, count, applicable in shares)
    note = version_note(data)
    alt = (
        "Bar chart of how the mistakes that apply to each framework ended. "
        f"Mistakes reported before the app runs: {counts}."
    )
    return "\n".join(
        [
            START_MARKER,
            "<!-- Written by `python -m docs_site.scripts.benchmark_images` from",
            "     docs_site/data/error_prevention.json. Rerun it rather than editing",
            "     this block by hand. -->",
            "",
            "## Catch mistakes early",
            "",
            f"We built the same app in {frameworks} frameworks and made the same",
            f"{mistakes} mistakes in each.",
            "",
            "<picture>",
            "  <source",
            '    media="(prefers-color-scheme: dark)"',
            f'    srcset="{ASSET_URL}/{dark_name}"',
            "  >",
            "  <img",
            f'    src="{ASSET_URL}/{light_name}"',
            # A framework name with a quote in it must not end the attribute.
            f'    alt="{html.escape(alt)}"',
            f'    width="{IMAGE_WIDTH}"',
            "  >",
            "</picture>",
            "",
            f"{note} Each bar counts only the mistakes that apply to that framework.",
            f"[How we measured]({DETAILS_URL})",
            END_MARKER,
        ],
    )


def find_block(readme: str) -> tuple[int, int]:
    """
    Return where the block starts and ends in the README text.

    The start is the offset of the start marker and the end is the offset just
    past the end marker. A README with no block, or with more than one, raises
    ``ValueError`` naming the line, since the script would not know which
    block to rewrite.
    """
    starts = [match.start() for match in re.finditer(re.escape(START_MARKER), readme)]
    ends = [match.end() for match in re.finditer(re.escape(END_MARKER), readme)]
    if len(starts) != 1 or len(ends) != 1:
        lines = sorted(readme.count("\n", 0, offset) + 1 for offset in starts + ends)
        where = f" (markers on lines {lines})" if lines else ""
        msg = f"README needs exactly one {START_MARKER} ... {END_MARKER} pair{where}"
        raise ValueError(msg)
    if ends[0] < starts[0]:
        line = readme.count("\n", 0, ends[0]) + 1
        msg = f"README has the benchmark chart end marker on line {line}, before its start marker"
        raise ValueError(msg)
    return starts[0], ends[0]


def replace_block(readme: str, block: str) -> str:
    """Return the README text with its benchmark chart block replaced by ``block``."""
    start, end = find_block(readme)
    return readme[:start] + block + readme[end:]


def image_names_in(block: str) -> list[str]:
    """Return the file names of every benchmark image the block links, in order."""
    return re.findall(re.escape(ASSET_URL) + r"/([^\"'\s>]+)", block)
