"""Tests for the benchmark chart component and the script that feeds it data."""

from __future__ import annotations

import json
from typing import Any

import pytest
from lxml import html

from docs_site._internal.components.benchmark_chart import DATA_PATH, BenchmarkChartMarkup, axis_ticks, chart_view
from docs_site.scripts.benchmark_data import GROUPS, embedded_report_data, extract


def _framework(name: str, group: str | None, server: float, browser: float) -> dict[str, Any]:
    return {
        "name": name,
        "group": group,
        "total_ms": server + browser,
        "phases_ms": {"server": server, "browser_after": browser},
    }


def _data() -> dict[str, Any]:
    # Two loads whose largest total (450) is in the second load, so the shared
    # axis is only right if both loads are read.
    return {
        "loads": [
            {
                "id": "first",
                "frameworks": [
                    _framework("Alpha", None, 100, 100),
                    _framework("Beta", "Group B", 50, 250),
                    _framework("Gamma", "Group B", 10, 90),
                ],
            },
            {"id": "second", "frameworks": [_framework("Alpha", None, 150, 300)]},
        ],
    }


@pytest.mark.parametrize(
    ("maximum", "expected"),
    [
        (844, [0, 200, 400, 600, 800, 1000]),
        (450, [0, 100, 200, 300, 400, 500]),
        (1000, [0, 200, 400, 600, 800, 1000]),
        (12, [0, 2.5, 5, 7.5, 10, 12.5]),
        (0.9, [0, 0.2, 0.4, 0.6, 0.8, 1.0]),
    ],
)
def test_axis_ticks_are_round_and_cover_the_maximum(maximum: float, expected: list[float]) -> None:
    assert axis_ticks(maximum) == expected


def test_axis_ticks_reject_an_empty_chart() -> None:
    with pytest.raises(ValueError, match="positive maximum"):
        axis_ticks(0)


def test_chart_view_shares_one_axis_across_loads() -> None:
    view = chart_view(_data(), "first")

    # 450 ms in the second load sets a 0 to 500 ms axis for the first load too.
    assert [tick["label"] for tick in view["ticks"]] == [f"{value} ms" for value in range(0, 501, 100)]
    # The reference line sits at the first framework's 200 ms total.
    assert view["reference"] == {"label": "Alpha 200 ms", "style": "left: 40.000%"}


def test_chart_view_rejects_unknown_loads_and_phases() -> None:
    with pytest.raises(ValueError, match="Unknown benchmark load 'third'"):
        chart_view(_data(), "third")

    data = _data()
    data["loads"][0]["frameworks"][0]["phases_ms"]["mystery"] = 1.0
    with pytest.raises(ValueError, match="cannot name: \\['mystery'\\]"):
        chart_view(data, "first")


def test_rendered_chart_draws_groups_bars_and_table() -> None:
    view = chart_view(_data(), "first")
    figure = html.fromstring(str(BenchmarkChartMarkup(title="First load", view=view)))

    # Only named groups get a heading, once each.
    assert [node.text_content() for node in figure.xpath(".//*[@class='bench-chart__heading']")] == ["Group B"]
    rows = figure.xpath(".//*[contains(@class, 'bench-chart__row ')] | .//*[@class='bench-chart__row']")
    assert [row.xpath("string(.//*[@class='bench-chart__name'])") for row in rows] == ["Alpha", "Beta", "Gamma"]
    assert "bench-chart__row--reference" in rows[0].attrib["class"]
    assert "bench-chart__row--reference" not in rows[1].attrib["class"]

    # Segment widths are each phase's share of the 500 ms axis.
    beta_segments = rows[1].xpath(".//*[@class='bench-chart__segment']")
    assert [segment.attrib["style"].split(";")[0] for segment in beta_segments] == ["width: 10.000%", "width: 50.000%"]
    assert beta_segments[0].attrib["title"] == "Server builds the page: 50.0 ms"

    # The bars expose one text alternative; the table carries every value.
    plot = figure.xpath(".//*[@role='img']")[0]
    assert plot.attrib["aria-label"].endswith("Alpha 200 ms, Beta 300 ms, Gamma 100 ms.")
    table_rows = figure.xpath(".//table/tbody/tr")
    assert [row.xpath("string(th)") for row in table_rows] == ["Alpha", "Beta", "Gamma"]
    assert [cell.text_content() for cell in table_rows[1].xpath("td")] == ["50.0", "250.0", "300.0"]
    # The legend lists only phases this load uses, in stacking order.
    assert [item.text_content().strip() for item in figure.xpath(".//ul[@class='bench-chart__legend']/li")] == [
        "Server builds the page",
        "Browser work and later requests",
    ]


def _sample(app: str, page_load: int, segments: dict[str, float], layout_wait: float) -> dict[str, Any]:
    ready = sum(segments.values())
    return {
        "app": app,
        "count": 1400,
        "action": "initial",
        "page_load": page_load,
        "status": "ok",
        "ready_elapsed_ms": ready,
        "layout_extra_wait_ms": layout_wait,
        "layout_endpoint": "second-rAF-layout-opportunity-v1",
        "layout_inclusive_elapsed_ms": ready + layout_wait,
        "latency_phase": {
            "status": "measured",
            "segments": [{"key": key, "ms": ms} for key, ms in segments.items()],
        },
    }


def _report(samples: list[dict[str, Any]]) -> str:
    payload = json.dumps({"samples": samples})
    return f'<html><script id="report-data" type="application/json">{payload}</script></html>'


def _manifest() -> dict[str, Any]:
    return {
        "id": "synthetic",
        "browser": {"engine": "chromium", "version": "1.0"},
        "host": {"node": "private-host", "system": "Darwin"},
        "inputs": {
            "inputs": {
                "profile": {
                    "scenario": "board",
                    "network": "loopback",
                    "cache": "cold",
                    "compression": "identity",
                },
            },
        },
        "cell_provenance": {"reflex/1400": {"latency": "retained", "latency_run": "older-run"}},
    }


def _all_samples() -> list[dict[str, Any]]:
    keys = [key for _, members in GROUPS for key, _ in members]
    return [
        _sample(key, load, {"server": 10.0 * (index + 1), "browser_after": 5.0}, 2.0)
        for load in (1, 2)
        for index, key in enumerate(keys)
    ]


def test_extract_keeps_totals_phases_and_provenance() -> None:
    samples = _all_samples()
    # A sample from another size or action must not leak into the chart.
    samples.append({**_sample("citry_vue", 1, {"server": 999.0}, 0.0), "count": 140})
    result = extract(_report(samples), _manifest())

    first = result["loads"][0]["frameworks"]
    assert first[0] == {
        "key": "citry_vue",
        "name": "Citry",
        "group": None,
        "total_ms": 17.0,
        "phases_ms": {"server": 10.0, "browser_after": 5.0, "layout_wait": 2.0},
        "measured_in_run": None,
        "retained": False,
    }
    assert next(row for row in first if row["key"] == "reflex")["retained"] is True
    # The host name identifies a machine, so it stays out of the docs.
    assert result["source"]["host"] == {"system": "Darwin"}


def test_extract_rejects_phases_that_do_not_add_up() -> None:
    samples = _all_samples()
    samples[0]["ready_elapsed_ms"] += 5
    with pytest.raises(ValueError, match="citry_vue load 1: phases do not add up"):
        extract(_report(samples), _manifest())


def test_extract_rejects_a_missing_framework() -> None:
    samples = [row for row in _all_samples() if row["app"] != "nuxt"]
    with pytest.raises(
        ValueError, match="nuxt load 1: expected one observation, which succeeded; found 0 with 0 successful"
    ):
        extract(_report(samples), _manifest())


def test_embedded_report_data_needs_the_data_script() -> None:
    with pytest.raises(ValueError, match="no embedded report data"):
        embedded_report_data("<html></html>")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"layout_inclusive_elapsed_ms": 1.0}, "layout wait does not close the gap"),
        ({"layout_endpoint": "older-endpoint"}, "not measured with second-rAF"),
        ({"latency_phase": {"status": "unavailable", "segments": []}}, "phases were not measured"),
    ],
)
def test_extract_rejects_rows_the_report_would_not_draw_as_measured(change: dict[str, Any], message: str) -> None:
    samples = _all_samples()
    samples[0].update(change)
    with pytest.raises(ValueError, match=message):
        extract(_report(samples), _manifest())


def test_extract_rejects_a_repeated_observation() -> None:
    samples = _all_samples()
    samples.append(dict(samples[0]))
    with pytest.raises(ValueError, match="found 2 with 2 successful"):
        extract(_report(samples), _manifest())


@pytest.mark.parametrize("load", ["first", "second"])
def test_checked_in_data_renders(load: str) -> None:
    # Guards the data file's shape, not its numbers: every load it lists must
    # draw without an unknown phase or an empty chart.
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    view = chart_view(data, load)
    assert view["rows"]
    assert view["ticks"][-1]["label"].endswith(" ms")
