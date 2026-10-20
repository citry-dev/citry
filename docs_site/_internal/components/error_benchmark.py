"""
``<c-error-benchmark-chart title="..." />`` and ``<c-error-benchmark-table />``
draw the error-prevention benchmark: the same developer mistakes written in
each framework, and how early each framework reported them.

The chart gives each framework one bar, split by how the mistakes ended, from
"error before running" (best) to "missed, no visible change" (worst); the
benchmark calls these six outcomes buckets. The table shows every mistake in
every framework as the short code the benchmark report uses.

The results come from ``docs_site/data/error_prevention.json``, which
``docs_site/scripts/error_benchmark_data.py`` writes from a benchmark report.
Like ``<c-benchmark-chart />``, both are plain HTML and CSS built at docs-build
time and reuse its ``bench-chart`` classes, so the two benchmark pages look
alike and the names stay real text on a phone.
"""

from __future__ import annotations

import json
from collections import Counter
from functools import cache
from pathlib import Path
from typing import Any

from markupsafe import Markup

from citry import Component
from docs_site._internal.util import flatten_for_markdown

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "error_prevention.json"

# One color per bucket the benchmark report defines. Greens mean the mistake
# was reported before the app ran, oranges at runtime, and red and dark gray
# that nothing reported it. In the green and orange pairs the lighter shade is
# the warning, so a warning reads as a weaker form of the error beside it. The labels come from
# the data file, which copies them from the report.
BUCKET_COLORS: dict[str, str] = {
    "static-error": "#2f855a",
    "static-warning": "#9ae6b4",
    "runtime-error": "#dd6b20",
    "runtime-warning": "#f6c177",
    "silent": "#c53030",
    "never": "#4a5568",
}

# Records that sit outside the six buckets still take their share of the bar,
# so every bar is as long as the number of mistakes. They follow the six
# buckets, so every bar's green part starts at the left edge. A run that skips
# the runtime check, or lacks a case, has "not scored" or "no case written"
# records, and the page shows them rather than drawing short bars.
NOT_SCORED = "not-scored"
NO_CASE = "no-case"
DOES_NOT_APPLY = "does-not-apply"
EXTRA_PARTS: dict[str, tuple[str, str]] = {
    NOT_SCORED: (
        "Not scored",
        "repeating-linear-gradient(135deg, #cbd5e0 0 3px, #edf2f7 3px 6px)",
    ),
    NO_CASE: ("No case written", "#a0aec0"),
    DOES_NOT_APPLY: ("Does not apply", "#cbd5e0"),
}


def _percent(count: int, total: int) -> str:
    return f"{count / total * 100:.3f}%"


def _part(record: dict[str, Any], buckets: set[str]) -> str:
    """Return the chart part a record counts towards: a bucket id or an extra part."""
    label = f"{record['framework']} / {record['mistake']}"
    status = record["status"]
    if status in {"not-applicable", "prevented"}:
        return DOES_NOT_APPLY
    if status == "missing":
        return NO_CASE
    if status != "ported":
        msg = f"Error benchmark record {label} has an unknown status {status!r}"
        raise ValueError(msg)
    bucket = record["bucket"]
    if bucket is None:
        return NOT_SCORED
    if bucket not in buckets:
        # A bucket the chart has no label or color for would draw an
        # unexplained part of the bar.
        msg = f"Error benchmark record {label} has a bucket the chart cannot name: {bucket!r}"
        raise ValueError(msg)
    return bucket


def _checked_buckets(data: dict[str, Any]) -> list[dict[str, str]]:
    unknown = [row["id"] for row in data["buckets"] if row["id"] not in BUCKET_COLORS]
    if unknown:
        msg = f"Error benchmark data has buckets the chart has no color for: {unknown}"
        raise ValueError(msg)
    return data["buckets"]


def _records(data: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    """Index the records by framework and mistake, and check that none is missing."""
    records = {(row["framework"], row["mistake"]): row for row in data["results"]}
    absent = [
        f"{framework['key']} / {mistake['id']}"
        for framework in data["frameworks"]
        for mistake in data["mistakes"]
        if (framework["key"], mistake["id"]) not in records
    ]
    if absent:
        # A missing record would draw a short bar and an empty table cell.
        msg = f"Error benchmark data has no record for: {absent}"
        raise ValueError(msg)
    return records


def chart_view(data: dict[str, Any]) -> dict[str, Any]:
    """
    Turn the benchmark data into what the chart template draws.

    Each framework gets one bar in the data's order; the first framework (the
    data file lists Citry first) gets a bold name. The bar's parts follow the
    data's bucket order, then any extra parts, so a reader can compare the
    green "error before running" part across bars from the same left edge.
    """
    buckets = _checked_buckets(data)
    records = _records(data)
    if not data["frameworks"] or not data["mistakes"]:
        msg = "Error benchmark data has no frameworks or no mistakes to draw"
        raise ValueError(msg)
    total = len(data["mistakes"])
    bucket_ids = {row["id"] for row in buckets}
    counts = {
        framework["key"]: Counter(
            _part(records[framework["key"], mistake["id"]], bucket_ids) for mistake in data["mistakes"]
        )
        for framework in data["frameworks"]
    }

    # Every bucket keeps its legend entry and table column even at zero, since
    # "no framework reached this bucket" is itself a result. An extra part
    # appears only when some framework has it.
    parts = [(row["id"], row["label"], BUCKET_COLORS[row["id"]]) for row in buckets]
    parts += [
        (key, label, color)
        for key, (label, color) in EXTRA_PARTS.items()
        if any(count[key] for count in counts.values())
    ]
    # A mistake that does not apply takes no room, so a bar is as long as the
    # mistakes that apply to its framework, and only the longest bar spans the
    # full width. The table below still counts the ones that do not apply.
    drawn = [part for part in parts if part[0] != DOES_NOT_APPLY]
    applicable = {
        key: sum(count for part, count in framework_counts.items() if part != DOES_NOT_APPLY)
        for key, framework_counts in counts.items()
    }
    axis = max(applicable.values())

    rows = [
        {
            "name": framework["name"],
            "is_reference": index == 0,
            "segments": [
                {
                    "style": f"width: {_percent(counts[framework['key']][key], axis)}; background: {color}",
                    "title": f"{label}: {counts[framework['key']][key]}",
                }
                for key, label, color in drawn
                if counts[framework["key"]][key]
            ],
        }
        for index, framework in enumerate(data["frameworks"])
    ]
    # The bar parts are hidden from screen readers, so the chart's label
    # carries every count instead.
    totals = "; ".join(
        f"{framework['name']}: "
        + ", ".join(
            f"{label} {counts[framework['key']][key]}" for key, label, _ in parts if counts[framework["key"]][key]
        )
        for framework in data["frameworks"]
    )
    return {
        "legend": [{"label": label, "style": f"background: {color}"} for _, label, color in drawn],
        "rows": rows,
        "summary": f"Stacked bar chart of {total} mistakes. {totals}.",
    }


def table_view(data: dict[str, Any]) -> dict[str, Any]:
    """
    Turn the benchmark data into the full matrix of mistakes and frameworks.

    Mistakes are grouped under their category's heading, in the data's
    category order and then its mistake order. A category with no mistakes
    gets no heading. A cell's tint is its bucket's color; a cell outside the
    six buckets stays plain.
    """
    buckets = {row["id"] for row in _checked_buckets(data)}
    records = _records(data)
    categories = [row["id"] for row in data["categories"]]
    stray = sorted({row["category"] for row in data["mistakes"]} - set(categories))
    if stray:
        # The table only draws mistakes under a heading, so these would vanish.
        msg = f"Error benchmark data has mistakes in categories it does not list: {stray}"
        raise ValueError(msg)

    groups = []
    for category in data["categories"]:
        mistakes = [row for row in data["mistakes"] if row["category"] == category["id"]]
        if not mistakes:
            continue
        rows = []
        for mistake in mistakes:
            cells = []
            for framework in data["frameworks"]:
                record = records[framework["key"], mistake["id"]]
                part = _part(record, buckets)
                # The evidence is what each tool printed; with none, the reason
                # explains a not-applicable or prevented cell.
                title = "\n".join(record["evidence"]) or record.get("reason") or None
                cells.append(
                    {
                        "text": record["cell"],
                        "style": f"--error-bench-tint: {BUCKET_COLORS[part]}" if part in BUCKET_COLORS else None,
                        "title": title,
                    },
                )
            rows.append({"title": mistake["title"], "cells": cells})
        ids = [mistake["id"] for mistake in mistakes]
        counts = [_caught_total(records, framework["key"], ids, buckets) for framework in data["frameworks"]]
        groups.append({"heading": category["heading"], "counts": counts, "rows": rows})

    every = [mistake["id"] for mistake in data["mistakes"]]
    return {
        # The meanings come from the report, which also writes the cells.
        "codes": data["codes"],
        "frameworks": [row["name"] for row in data["frameworks"]],
        "counts": [_caught_total(records, framework["key"], every, buckets) for framework in data["frameworks"]],
        "groups": groups,
    }


def _caught_total(
    records: dict[tuple[str, str], dict[str, Any]], framework: str, mistake_ids: list[str], buckets: set[str]
) -> str:
    """Count the mistakes a framework reported at all, out of those that apply to it, as "(caught/total)"."""
    scored = [
        records[framework, mistake] for mistake in mistake_ids if records[framework, mistake]["status"] == "ported"
    ]
    # The first four buckets are the ones in which a tool or the running app
    # reported the mistake; the last two are misses.
    reported = [row for row in BUCKET_COLORS if row in buckets][:4]
    caught = sum(_part(record, buckets) in reported for record in scored)
    return f"({caught}/{len(scored)})"


@cache
def _load_data() -> dict[str, Any]:
    # Read once per process; the build renders the page once per output format.
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


# Stands in for a line break in a cell's title while the markup is joined onto
# one line. Tool output does not normally contain this private-use character;
# if it did, the title would only show an extra line break.
_TITLE_BREAK = "\ue000"


def _as_block(markup: str) -> Markup:
    # Blank lines around the block keep the Markdown pass from joining it to a
    # neighbouring paragraph.
    return Markup(f"\n\n{flatten_for_markdown(markup)}\n\n")  # noqa: S704 - built in this module from checked-in data


class ErrorBenchmarkChartMarkup(Component):
    """The chart's HTML, before it is flattened for the Markdown pass."""

    transparent = True

    class Kwargs:
        title: str
        view: dict

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"title": kwargs.title, **kwargs.view}

    # As in <c-benchmark-chart />, the bars are one role="img" element whose
    # label lists every count, so screen readers skip the bar parts. The plot
    # has no axis: each part's count is in its title and its label.
    template = """
      <figure class="bench-chart bench-chart--counts">
        <figcaption class="bench-chart__title">{{ title }}</figcaption>
        <ul class="bench-chart__legend">
          <li c-for="item in legend">
            <span
              class="bench-chart__swatch"
              c-style="item['style']"
              aria-hidden="true"
            ></span>
            {{ item['label'] }}
          </li>
        </ul>
        <div
          class="bench-chart__plot"
          role="img"
          c-aria-label="title + '. ' + summary"
        >
          <div
            c-for="row in rows"
            class="bench-chart__row"
            c-class="{'bench-chart__row--reference': row['is_reference']}"
            aria-hidden="true"
          >
            <span class="bench-chart__name">{{ row['name'] }}</span>
            <span class="bench-chart__bar">
              <span
                c-for="segment in row['segments']"
                class="bench-chart__segment"
                c-style="segment['style']"
                c-title="segment['title']"
              ></span>
            </span>
          </div>
        </div>
      </figure>
    """


class ErrorBenchmarkChart(Component):
    """``<c-error-benchmark-chart title="..." />`` draws one bar per framework."""

    transparent = True

    class Kwargs:
        # The caption above the chart; the table repeats it.
        title: str

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        view = chart_view(_load_data())
        return {"chart": _as_block(str(ErrorBenchmarkChartMarkup(title=str(kwargs.title), view=view)))}

    template = """
      {{ chart }}
    """


class ErrorBenchmarkTableMarkup(Component):
    """The full matrix's HTML, before it is flattened for the Markdown pass."""

    transparent = True

    class Kwargs:
        view: dict

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return dict(kwargs.view)

    # Each category is its own <tbody> with a heading row, so a screen reader
    # announces the heading as the start of a group. The table scrolls
    # sideways on a phone rather than squeezing six framework columns. The
    # header and data cells keep their text against the tags, so the text
    # gets no leading or trailing space.
    template = """
      <div class="error-bench-table">
        <div class="bench-chart__table-wrap">
          <table>
            <caption>How each mistake ended, by framework</caption>
            <thead>
              <tr>
                <th scope="col">Mistake</th>
                <th c-for="name in frameworks" scope="col">{{ name }}</th>
              </tr>
              <tr class="error-bench-table__counts">
                <td>(caught/total)</td>
                <td c-for="count in counts">{{ count }}</td>
              </tr>
            </thead>
            <tbody c-for="group in groups">
              <tr class="error-bench-table__heading">
                <th scope="rowgroup">{{ group['heading'] }}</th>
                <td c-for="count in group['counts']">{{ count }}</td>
              </tr>
              <tr c-for="row in group['rows']">
                <th scope="row">{{ row['title'] }}</th>
                <td
                  c-for="cell in row['cells']"
                  class="error-bench-table__cell"
                  c-style="cell['style']"
                  c-title="cell['title']"
                >{{ cell['text'] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <ul class="bench-chart__legend error-bench-table__codes">
          <li c-for="item in codes">
            <code>{{ item['code'] }}</code>
            {{ item['meaning'] }}
          </li>
        </ul>
      </div>
    """


class ErrorBenchmarkTable(Component):
    """``<c-error-benchmark-table />`` draws every mistake in every framework."""

    transparent = True

    # The table draws the whole data file, so it takes no inputs.
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        view = table_view(_load_data())
        # flatten_for_markdown puts the markup on one line, which would turn
        # the line breaks between evidence lines into spaces. A placeholder
        # character carries each break through it, and the character
        # reference that replaces it reads back as a line break in the title.
        for group in view["groups"]:
            for row in group["rows"]:
                for cell in row["cells"]:
                    if cell["title"]:
                        cell["title"] = cell["title"].replace("\n", _TITLE_BREAK)
        markup = _as_block(str(ErrorBenchmarkTableMarkup(view=view)))
        return {"table": Markup(str(markup).replace(_TITLE_BREAK, "&#10;"))}  # noqa: S704 - built in this module from checked-in data

    template = """
      {{ table }}
    """
