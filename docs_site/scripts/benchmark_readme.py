"""
Write and check the benchmark chart blocks in the repository README.

The README shows two benchmark charts as PNGs, because GitHub and PyPI show a
README without the docs site's stylesheet, so the charts' HTML would not draw:
the error chart (how early each framework reports the same mistakes) and the
speed chart (how long the same page takes to become usable).
``docs_site/scripts/benchmark_images.py`` takes the screenshots; this module
decides what the README says around them: the heading, the sentences from
the landing page's card, the image links, and the alt text that lists every
framework's number for readers who cannot see the image.

Everything here is computed from the two data files the docs site draws,
``docs_site/data/error_prevention.json`` and
``docs_site/data/benchmark_time_to_interactive.json``, so the README and the
docs site's charts tell the same story. The landing page shows the same
sentences through ``<c-benchmark-text>``, which calls the functions here. The
``readme_benchmark_charts`` validator rebuilds each block with these
functions and fails when the README no longer matches the data, for example
after a new benchmark run, until someone reruns the image script.

This module uses only the standard library, because the validator loads it
by file path, where the ``docs_site`` package and the docs dependencies may
be missing.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import textwrap
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
# The landing page repeats each README heading; the validator checks it there.
LANDING_PATH = REPO_ROOT / "docs_site" / "content" / "index.md"
DATA_PATH = REPO_ROOT / "docs_site" / "data" / "error_prevention.json"
SPEED_DATA_PATH = REPO_ROOT / "docs_site" / "data" / "benchmark_time_to_interactive.json"

# The images live on `main` for good: a release's PyPI page keeps loading the
# file it was published with, so a file here is never overwritten or deleted.
ASSET_DIR = REPO_ROOT / "docs" / "assets" / "benchmarks"
# PyPI renders the README on its own domain, where a repository path would
# not resolve, so the README links each image by its absolute URL.
ASSET_URL = "https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/benchmarks"
DETAILS_URL = "https://citry.dev/about/benchmarks/#errors-how-we-measured"
SPEED_DETAILS_URL = "https://citry.dev/about/benchmarks/#how-the-numbers-were-taken"

# The README carries one block per chart, in this order. The name appears in
# the block's marker comments and starts each of its image file names.
CHARTS = ("errors", "speed")

# Each block's heading, which the landing page's section repeats word for word.
HEADINGS = {
    "errors": "Catch mistakes early",
    "speed": "Python at JavaScript speed",
}

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

# One line above the error chart tells a first-time reader which way is good
# before they decode the legend's five colours.
ERRORS_HINT = "More green = earlier feedback = better"

# Which Citry each error benchmark run measured, as the README says it under
# the chart. A released 0.6.0 reports far fewer mistakes before the app runs
# than this run's code, so the README must not show the count without the
# version.
VERSION_NOTES = {
    "20261021T182412Z": "Citry 0.7.0, measured before its release.",
}

# The speed chart shows the second page load: the first one includes work a
# server does once, such as loading templates, which a visitor rarely waits for.
SPEED_LOAD = "second"

# Which Citry each speed benchmark report measured, and how many times, keyed
# by the id of the report Citry's numbers come from (``citry_report_id`` in
# the data file's source). The data file records neither in a form the README
# can quote, so each report's note lives here.
SPEED_VERSION_NOTES = {
    "composed-70d4a8802900": "Citry 0.6.0, one run per framework.",
    "composed-be3f44cc4b6e": "Citry 0.7.0, measured before its release, one run per framework.",
}

# A file name records the chart, the benchmark run it shows, the first
# characters of the PNG's SHA-256, and the colour theme. The run ties the
# image to the data; the hash gives a redrawn image of the same run a new
# name instead of replacing a file a published page may load.
HASH_LENGTH = 12
THEMES = ("light", "dark")
# The run id may hold hyphens: the error runner adds "-2" to a second run that
# starts in the same second, and a speed report id looks like
# "composed-70d4a8802900". The fixed-length hash and the theme at the end
# keep the name unambiguous.
_RUN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")
_NAME_RE = re.compile(
    r"(?P<chart>errors|speed)-(?P<run>[A-Za-z0-9][A-Za-z0-9-]*)-(?P<hash>[0-9a-f]{12})-(?P<theme>light|dark)\.png"
)

# The README wraps its sentences at this width, so a diff of the block stays
# readable.
_WRAP = 72


def markers(chart: str) -> tuple[str, str]:
    """
    Return the comments that start and end one chart's README block.

    Both renderers hide comments, so readers see only the block itself.
    """
    if chart not in CHARTS:
        msg = f"Unknown README chart {chart!r}; use one of {list(CHARTS)}"
        raise ValueError(msg)
    return f"<!-- benchmark-chart:{chart} start -->", f"<!-- benchmark-chart:{chart} end -->"


def load_data(chart: str = "errors") -> dict[str, Any]:
    """Read the benchmark data file the docs site draws the given chart from."""
    path = DATA_PATH if chart == "errors" else SPEED_DATA_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def run_id(chart: str, data: dict[str, Any]) -> str:
    """Return the id of the benchmark run a chart's data comes from; image names start with it."""
    return str(data["run"] if chart == "errors" else data["source"]["report_id"])


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
    Return the sentence that says which Citry the error chart measured.

    The data file does not record the version, so each run's note lives in
    ``VERSION_NOTES``. A run without one raises ``ValueError``, so a new run
    cannot reach the README or the landing page under an old run's version.
    """
    try:
        return VERSION_NOTES[data["run"]]
    except KeyError:
        msg = (
            f"No version note for error benchmark run {data['run']}; add one to VERSION_NOTES in "
            "docs_site/scripts/benchmark_readme.py"
        )
        raise ValueError(msg) from None


def errors_intro(data: dict[str, Any]) -> str:
    """Return the sentence that introduces the error chart, with the counts from the data."""
    return (
        f"We built the same app in {len(data['frameworks'])} frameworks and made the same "
        f"{len(data['mistakes'])} mistakes in each."
    )


def errors_note(data: dict[str, Any]) -> str:
    """Return the note under the error chart: the Citry version and what each bar counts."""
    return f"{version_note(data)} Each bar counts only the mistakes that apply to that framework."


def format_ms(value: float) -> str:
    """Return a time as whole milliseconds with a thousands separator, as the speed chart prints it."""
    return f"{value:,.0f} ms"


def speed_totals(data: dict[str, Any]) -> list[tuple[str, float]]:
    """
    Return each framework's name and total time on the README's page load, fastest first.

    This is the order of the speed chart drawn with ``sort="total"``, so the
    alt text reads the bars from top to bottom; equal totals keep the data
    file's order. Raises ``ValueError`` when the data has no such load or the
    load has no frameworks, since the chart could not draw either.
    """
    loads = {entry["id"]: entry for entry in data["loads"]}
    if SPEED_LOAD not in loads:
        msg = f"Speed benchmark data has no {SPEED_LOAD!r} load; it has {sorted(loads)}"
        raise ValueError(msg)
    frameworks = loads[SPEED_LOAD]["frameworks"]
    if not frameworks:
        msg = f"Speed benchmark load {SPEED_LOAD!r} has no frameworks to draw"
        raise ValueError(msg)
    # Python's sort is stable, so equal totals keep the data's order.
    return sorted(((row["name"], row["total_ms"]) for row in frameworks), key=lambda row: row[1])


def speed_intro(data: dict[str, Any]) -> str:
    """Return the sentence that introduces the speed chart, with the page size from the data."""
    entries = data["source"]["outputs"]
    return f"Time until a page with {entries:,} entries is usable, the second time the server builds it."


def speed_note(data: dict[str, Any]) -> str:
    """
    Return the note under the speed chart: the Citry version, the number of runs, and how to read the bars.

    The note belongs to the report Citry's numbers come from, which can be
    older than the data's newest report when the other frameworks were
    measured again. A data file without ``citry_report_id`` took every number
    from its one report. A report without an entry in
    ``SPEED_VERSION_NOTES`` raises ``ValueError``, so a new report cannot
    appear under an old one's version.
    """
    report = data["source"].get("citry_report_id", data["source"]["report_id"])
    try:
        note = SPEED_VERSION_NOTES[report]
    except KeyError:
        msg = (
            f"No version note for speed benchmark report {report}; add one to SPEED_VERSION_NOTES in "
            "docs_site/scripts/benchmark_readme.py"
        )
        raise ValueError(msg) from None
    return f"{note} Shorter is faster."


def image_name(chart: str, run: str, png: bytes, theme: str) -> str:
    """Return the file name for one theme's PNG of a chart drawn from the given benchmark run."""
    markers(chart)
    if theme not in THEMES:
        msg = f"Unknown image theme {theme!r}; use one of {list(THEMES)}"
        raise ValueError(msg)
    if not _RUN_RE.fullmatch(run):
        # The run id goes into a URL and a file name, so it must stay plain.
        msg = f"Benchmark run id {run!r} must contain only letters, digits, and hyphens"
        raise ValueError(msg)
    digest = hashlib.sha256(png).hexdigest()[:HASH_LENGTH]
    return f"{chart}-{run}-{digest}-{theme}.png"


def parse_image_name(name: str) -> dict[str, str] | None:
    """Split an image file name into its chart, run, hash, and theme, or return None if it is not one."""
    match = _NAME_RE.fullmatch(name)
    return match.groupdict() if match else None


def readme_block(chart: str, data: dict[str, Any], light_name: str, dark_name: str) -> str:
    """
    Return one chart's README block, markers included, for the given data and image files.

    The block holds the heading, the intro, the image in both themes, and the
    note with a link to the method. GitHub picks the dark image for a reader
    in dark mode. PyPI may ignore the ``<source>``; each image carries its own
    background, so either works.
    """
    if chart == "errors":
        shares = static_shares(data, short_names=True)
        counts = ", ".join(f"{name} {count} of {applicable}" for name, count, applicable in shares)
        alt = (
            "Bar chart of how the mistakes that apply to each framework ended. "
            f"Mistakes reported before the app runs: {counts}."
        )
        # The hint sits between the intro and the image, as on the landing card.
        paragraphs = [errors_intro(data), ERRORS_HINT]
        note, details, source = errors_note(data), DETAILS_URL, DATA_PATH
    else:
        totals = ", ".join(f"{name} {format_ms(total)}" for name, total in speed_totals(data))
        alt = f"Bar chart of the time until the page is usable, fastest first: {totals}."
        paragraphs = [speed_intro(data)]
        note, details, source = speed_note(data), SPEED_DETAILS_URL, SPEED_DATA_PATH
    start, end = markers(chart)
    lines = [
        start,
        "<!-- Written by `python -m docs_site.scripts.benchmark_images` from",
        f"     {source.relative_to(REPO_ROOT).as_posix()}. Rerun it rather than",
        "     editing this block by hand. -->",
        "",
        f"## {HEADINGS[chart]}",
        "",
    ]
    for paragraph in paragraphs:
        lines += [textwrap.fill(paragraph, _WRAP), ""]
    lines += [
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
        textwrap.fill(note, _WRAP),
        f"[How we measured]({details})",
        end,
    ]
    return "\n".join(lines)


def check_data(chart: str, data: dict[str, Any]) -> None:
    """Raise ``ValueError`` when a chart's data cannot be drawn, before any image is taken."""
    if chart == "errors":
        static_shares(data)
        version_note(data)
    else:
        speed_totals(data)
        speed_note(data)
    run_id_value = run_id(chart, data)
    if not _RUN_RE.fullmatch(run_id_value):
        msg = f"Benchmark run id {run_id_value!r} must contain only letters, digits, and hyphens"
        raise ValueError(msg)


def find_block(readme: str, chart: str) -> tuple[int, int]:
    """
    Return where one chart's block starts and ends in the README text.

    The start is the offset of the start marker and the end is the offset just
    past the end marker. A README with no block, or with more than one, raises
    ``ValueError`` naming the line, since the script would not know which
    block to rewrite.
    """
    start_marker, end_marker = markers(chart)
    starts = [match.start() for match in re.finditer(re.escape(start_marker), readme)]
    ends = [match.end() for match in re.finditer(re.escape(end_marker), readme)]
    if len(starts) != 1 or len(ends) != 1:
        lines = sorted(readme.count("\n", 0, offset) + 1 for offset in starts + ends)
        where = f" (markers on lines {lines})" if lines else ""
        msg = f"README needs exactly one {start_marker} ... {end_marker} pair{where}"
        raise ValueError(msg)
    if ends[0] < starts[0]:
        line = readme.count("\n", 0, ends[0]) + 1
        msg = f"README has the {chart} benchmark chart end marker on line {line}, before its start marker"
        raise ValueError(msg)
    return starts[0], ends[0]


def replace_block(readme: str, chart: str, block: str) -> str:
    """Return the README text with one chart's block replaced by ``block``."""
    start, end = find_block(readme, chart)
    return readme[:start] + block + readme[end:]


def image_names_in(block: str) -> list[str]:
    """Return the file names of every benchmark image the block links, in order."""
    return re.findall(re.escape(ASSET_URL) + r"/([^\"'\s>]+)", block)
