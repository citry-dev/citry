"""
``<c-benchmark-chart load="first" title="..." />`` draws one stacked bar chart
of the framework benchmark: how long each framework's page takes to become
ready for input, split into the phases the time went to.

The numbers come from ``docs_site/data/benchmark_time_to_interactive.json``,
which ``docs_site/scripts/benchmark_data.py`` writes from a benchmark report.
The chart is plain HTML and CSS built at docs-build time, with no script: the
names and totals stay real text, so they stay readable on a phone, where a
scaled-down SVG would shrink them, and the theme's colour tokens apply to them.
A table with the same numbers sits under the chart for screen readers and for
anyone who wants exact values. A page with less room, such as the landing
page, can leave it out with ``c-show_table="False"``; the chart's label still reads
every total to a screen reader.
"""

from __future__ import annotations

import json
import math
from functools import cache
from pathlib import Path
from typing import Any, Literal

from markupsafe import Markup

from citry import Component
from docs_site._internal.util import flatten_for_markdown

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "benchmark_time_to_interactive.json"

# Phase colours follow the benchmark report, so a reader who knows the report
# recognises them. The layout wait is a lighter purple than the report's,
# because the report's purple is hard to tell from the blue next to it, most of
# all for colour-blind readers.
PHASES: dict[str, tuple[str, str]] = {
    "browser_before": ("Before the page request", "#627d98"),
    "server": ("Server builds the page", "#2f855a"),
    "exchange_residual": ("Other request time", "#d69e2e"),
    "response_receive": ("Page download", "#dd6b20"),
    "browser_after": ("Browser work and later requests", "#3182ce"),
    "unclassified": ("Not split into phases", "#a0aec0"),
    "layout_wait": ("Wait for the next layout", "#b794f4"),
}

# Five intervals give six labelled grid lines; more would crowd the labels
# on a phone.
_MAX_TICK_INTERVALS = 5


def axis_ticks(maximum: float) -> list[float]:
    """
    Return round tick values from 0 up to the first one at or above ``maximum``.

    The step is 1, 2, 2.5 or 5 times a power of ten, the smallest that needs no
    more than five intervals, so 844 gives 0, 200, ..., 1,000.
    """
    if maximum <= 0:
        msg = "The chart needs a positive maximum to draw an axis"
        raise ValueError(msg)
    magnitude = 10 ** math.floor(math.log10(maximum / _MAX_TICK_INTERVALS))
    step = next(
        magnitude * factor for factor in (1, 2, 2.5, 5, 10) if magnitude * factor * _MAX_TICK_INTERVALS >= maximum
    )
    count = math.ceil(maximum / step)
    # Rounding drops float noise such as 0.6000000000000001 from fractional steps.
    return [round(step * index, 10) for index in range(count + 1)]


def _ms(value: float) -> str:
    # Whole milliseconds with a thousands separator; the decimals stay in the table.
    return f"{value:,.0f} ms"


def _percent(value: float, axis_max: float) -> str:
    return f"{value / axis_max * 100:.3f}%"


# The row orders ``chart_view`` accepts: the data file's own order, with its
# group headings, or the total time from fastest to slowest.
SORT_ORDERS = ("data", "total")

# In a chart without phases, every bar is one colour and Citry's stands out.
# A page can set these variables to its own colours; the landing page does.
_TOTAL_BAR = "var(--bench-bar, #a0aec0)"
_REFERENCE_BAR = "var(--bench-bar-reference, var(--c-accent))"


def chart_view(
    data: dict[str, Any],
    load: str,
    *,
    sort: str = "data",
    phases: bool = True,
    compact: bool = False,
) -> dict[str, Any]:
    """
    Turn the benchmark data into what the template draws for one page load.

    With the defaults, as on the Benchmarks page, every load in ``data``
    shares one axis, so the first-load and second-load charts on a page can be
    compared by eye. The vertical line marks the first framework's total; the
    data file lists Citry first for that reason. Bars follow the data's order
    under its group headings and are split into the phases the time went to.

    The options draw the shorter version the landing page uses:

    - ``sort="total"`` orders the bars from fastest to slowest. Group headings
      are left out, because a group's rows would no longer sit together.
      Equal totals keep the data's order.
    - ``phases=False`` draws each bar as one total, with no legend, and
      Citry's bar in the accent colour.
    - ``compact`` leaves out the axis and the dashed line (see
      ``bench-chart--compact`` in site.css), and scales the bars to this
      load's slowest framework, which then spans the whole track.
    """
    if sort not in SORT_ORDERS:
        msg = f"Unknown benchmark chart sort {sort!r}; use one of {list(SORT_ORDERS)}"
        raise ValueError(msg)
    loads = {entry["id"]: entry for entry in data["loads"]}
    if load not in loads:
        msg = f"Unknown benchmark load {load!r}; the data has {sorted(loads)}"
        raise ValueError(msg)
    frameworks = loads[load]["frameworks"]
    if not frameworks:
        msg = f"Benchmark load {load!r} has no frameworks to draw"
        raise ValueError(msg)
    unknown = {phase for row in frameworks for phase in row["phases_ms"]} - PHASES.keys()
    if unknown:
        # A phase without a label and colour would draw an unexplained gap.
        msg = f"Benchmark data has phases the chart cannot name: {sorted(unknown)}"
        raise ValueError(msg)

    ticks = axis_ticks(max(row["total_ms"] for entry in data["loads"] for row in entry["frameworks"]))
    # A chart with no axis has no round number to end on, so its slowest bar
    # fills the track instead.
    axis_max = max(row["total_ms"] for row in frameworks) if compact else ticks[-1]
    # Only phases that occur in this load get a legend entry and a table column.
    used_phases = [key for key in PHASES if any(key in row["phases_ms"] for row in frameworks)]

    # The reference is picked before sorting, so Citry keeps its bold name and
    # colour wherever its bar lands.
    reference = frameworks[0]
    ordered = list(frameworks)
    if sort == "total":
        # Python's sort is stable, so equal totals keep the data's order.
        ordered.sort(key=lambda row: row["total_ms"])

    rows: list[dict[str, Any]] = []
    group: object = object()
    for row in ordered:
        # A heading opens each named group; a row without a group (Citry's)
        # has none, and a sorted chart has no groups to open.
        if sort == "data" and row["group"] != group:
            group = row["group"]
            if group is not None:
                rows.append({"heading": group})
        is_reference = row is reference
        if phases:
            segments = [
                {
                    "style": f"width: {_percent(row['phases_ms'][key], axis_max)}; background: {PHASES[key][1]}",
                    "title": f"{PHASES[key][0]}: {row['phases_ms'][key]:,.1f} ms",
                }
                for key in used_phases
                if key in row["phases_ms"]
            ]
        else:
            color = _REFERENCE_BAR if is_reference else _TOTAL_BAR
            segments = [
                {
                    "style": f"width: {_percent(row['total_ms'], axis_max)}; background: {color}",
                    "title": f"Total: {row['total_ms']:,.1f} ms",
                },
            ]
        rows.append(
            {
                "heading": None,
                "name": row["name"],
                "total": _ms(row["total_ms"]),
                "is_reference": is_reference,
                "segments": segments,
            },
        )

    # The screen-reader label reads the totals in the order of the bars.
    totals = ", ".join(f"{row['name']} {_ms(row['total_ms'])}" for row in ordered)
    summary = (
        f"Stacked bar chart of total time in milliseconds: {totals}."
        if phases
        else f"Bar chart of total time in milliseconds: {totals}."
    )
    legend = [{"label": PHASES[key][0], "style": f"background: {PHASES[key][1]}"} for key in used_phases]
    return {
        # A chart without phases needs no key to its colours.
        "legend": legend if phases else [],
        "rows": rows,
        "ticks": [{"label": f"{tick:,.10g} ms", "style": f"left: {_percent(tick, axis_max)}"} for tick in ticks],
        "reference": {
            "label": f"{reference['name']} {_ms(reference['total_ms'])}",
            "style": f"left: {_percent(reference['total_ms'], axis_max)}",
        },
        "summary": summary,
        "columns": [PHASES[key][0] for key in used_phases],
        "table": [
            {
                "name": row["name"],
                "cells": [
                    f"{row['phases_ms'][key]:,.1f}" if key in row["phases_ms"] else "0.0" for key in used_phases
                ],
                "total": f"{row['total_ms']:,.1f}",
            }
            for row in frameworks
        ],
        "compact": compact,
    }


@cache
def _load_data() -> dict[str, Any]:
    # Read once per process; the build renders the page once per output format.
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


class BenchmarkChartMarkup(Component):
    """The chart's HTML, before it is flattened for the Markdown pass."""

    transparent = True

    class Kwargs:
        title: str
        view: dict
        show_table: bool = True

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        # The view goes first, so a key it gains later cannot replace an input.
        return {**kwargs.view, "title": kwargs.title, "show_table": kwargs.show_table}

    # The bars are one role="img" element whose label lists every total; its
    # inner parts are hidden from screen readers, which get the table instead
    # when the page shows it.
    template = """
      <figure
        class="bench-chart"
        c-class="{'bench-chart--compact': compact}"
      >
        <figcaption class="bench-chart__title">{{ title }}</figcaption>
        <ul
          c-if="legend"
          class="bench-chart__legend"
        >
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
          <div class="bench-chart__guides" aria-hidden="true">
            <span
              c-for="tick in ticks"
              class="bench-chart__gridline"
              c-style="tick['style']"
            ></span>
            <span
              class="bench-chart__reference"
              c-style="reference['style']"
            >
              <span class="bench-chart__reference-label">{{ reference['label'] }}</span>
            </span>
          </div>
          <c-for each="row in rows">
            <div
              c-if="row['heading']"
              class="bench-chart__heading"
              aria-hidden="true"
            >{{ row['heading'] }}</div>
            <div
              c-else
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
              <span class="bench-chart__total">{{ row['total'] }}</span>
            </div>
          </c-for>
          <div class="bench-chart__axis" aria-hidden="true">
            <span
              c-for="tick in ticks"
              class="bench-chart__tick"
              c-style="tick['style']"
            >{{ tick['label'] }}</span>
          </div>
        </div>
        <details
          c-if="show_table"
          class="bench-chart__details"
        >
          <summary>Show the numbers as a table</summary>
          <div class="bench-chart__table-wrap">
            <table>
              <caption>{{ title }}, in milliseconds</caption>
              <thead>
                <tr>
                  <th scope="col">Framework</th>
                  <th c-for="column in columns" scope="col">{{ column }}</th>
                  <th scope="col">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr c-for="row in table">
                  <th scope="row">{{ row['name'] }}</th>
                  <td c-for="cell in row['cells']">{{ cell }}</td>
                  <td><strong>{{ row['total'] }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
      </figure>
    """


class BenchmarkChart(Component):
    """``<c-benchmark-chart load="first" title="..." />`` draws one page load's chart."""

    transparent = True

    class Kwargs:
        # Which page load to draw: an ``id`` from the data file's ``loads``.
        load: str
        # The caption above the chart; the table repeats it.
        title: str
        # Whether a collapsed table with every number follows the chart.
        show_table: bool = True
        # The options below draw the shorter landing-page chart; chart_view
        # explains each one.
        sort: Literal["data", "total"] = "data"
        phases: bool = True
        compact: bool = False

    class Slots:
        pass

    template = "{{ chart }}"

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        view = chart_view(
            _load_data(),
            str(kwargs.load),
            sort=str(kwargs.sort),
            phases=kwargs.phases,
            compact=kwargs.compact,
        )
        chart = BenchmarkChartMarkup(title=str(kwargs.title), view=view, show_table=kwargs.show_table)
        markup = flatten_for_markdown(str(chart))
        # Blank lines around the block keep the Markdown pass from joining it
        # to a neighbouring paragraph.
        return {"chart": Markup(f"\n\n{markup}\n\n")}  # noqa: S704 - built in this module from checked-in data
