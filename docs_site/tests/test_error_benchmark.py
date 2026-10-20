"""Tests for the error benchmark chart and table and the script that feeds them data."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from lxml import html

from docs_site._internal.components.error_benchmark import (
    DATA_PATH,
    ErrorBenchmarkChartMarkup,
    ErrorBenchmarkTable,
    chart_view,
    table_view,
)
from docs_site.scripts.error_benchmark_data import extract

BUCKETS = [
    {"id": "static-error", "label": "Static error"},
    {"id": "static-warning", "label": "Static warning"},
    {"id": "runtime-error", "label": "Runtime error"},
    {"id": "runtime-warning", "label": "Runtime warning"},
    {"id": "missed", "label": "Missed"},
]


def _record(framework: str, mistake: str, status: str, bucket: str | None, cell: str, **extra: Any) -> dict[str, Any]:
    return {
        "framework": framework,
        "mistake": mistake,
        "status": status,
        "bucket": bucket,
        "cell": cell,
        "reason": None,
        "evidence": [],
        **extra,
    }


def _report() -> dict[str, Any]:
    # Two frameworks and four mistakes. The "empty" category has no mistakes,
    # and the mistakes are listed out of category order, so grouping is only
    # right if the table follows the category list.
    return {
        "run": "synthetic-run",
        "frameworks": [{"key": "alpha", "name": "Alpha"}, {"key": "beta", "name": "Beta"}],
        "categories": [
            {"id": "names", "heading": "Names"},
            {"id": "empty", "heading": "Nothing here"},
            {"id": "types", "heading": "Types"},
        ],
        "buckets": BUCKETS,
        "codes": [{"code": "E", "meaning": "reported in the editor"}],
        "mistakes": [
            {"id": "m1", "title": "First", "category": "names"},
            {"id": "m2", "title": "Second", "category": "types"},
            {"id": "m3", "title": "Third", "category": "names"},
            {"id": "m4", "title": "Fourth", "category": "types"},
        ],
        "results": [
            # "strict" stands for a field the page does not draw.
            _record("alpha", "m1", "ported", "static-error", "E", evidence=["editor: one", "check: two"], strict="E"),
            _record("alpha", "m2", "ported", "static-error", "C"),
            _record("alpha", "m3", "ported", "missed", "M"),
            _record("alpha", "m4", "not-applicable", None, "n/a", reason="No equivalent"),
            _record("beta", "m1", "ported", "runtime-error", "R"),
            _record("beta", "m2", "prevented", None, "P"),
            _record("beta", "m3", "ported", None, "?"),
            _record("beta", "m4", "ported", "missed", "M"),
        ],
    }


def test_extract_keeps_what_the_page_draws_in_a_stable_order() -> None:
    report = _report()
    # The runner logs records in any order; the data file must not depend on it.
    report["results"].reverse()
    data = extract(report, allow_partial=True)

    assert data["run"] == "synthetic-run"
    assert [(row["framework"], row["mistake"]) for row in data["results"]][:2] == [("alpha", "m1"), ("alpha", "m2")]
    assert data["results"][0] == {
        "framework": "alpha",
        "mistake": "m1",
        "status": "ported",
        "bucket": "static-error",
        "cell": "E",
        "reason": None,
        "evidence": ["editor: one", "check: two"],
    }
    # Fields the page does not draw stay out of the docs data.
    assert "strict" not in data["results"][0]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda report: report["results"].pop(), r"no record for: \['beta / m4'\]"),
        (lambda report: report["results"].append(dict(report["results"][0])), "alpha / m1: .*more than one record"),
        (lambda report: report["results"][0].update(bucket="sometimes"), "bucket 'sometimes' is unknown"),
        (lambda report: report["results"][3].update(bucket="missed"), "set on a not-applicable record"),
        (lambda report: report["results"][0].update(status="skipped"), "unknown status 'skipped'"),
        (lambda report: report["results"][0].update(framework="gamma"), "does not list"),
        (lambda report: report["mistakes"][0].update(category="other"), r"categories it does not list: \['other'\]"),
        (lambda report: report["frameworks"].append({"key": "alpha", "name": "Again"}), "frameworks more than once"),
    ],
)
def test_extract_rejects_records_the_page_cannot_draw(change: Any, message: str) -> None:
    report = _report()
    change(report)
    with pytest.raises(ValueError, match=message):
        extract(report, allow_partial=True)


def test_chart_view_stacks_buckets_in_order_then_extra_parts() -> None:
    view = chart_view(extract(_report(), allow_partial=True))

    # Every bucket keeps its place even at zero. "N/A or prevented" sits just
    # before "Missed", and the other extra parts follow.
    assert [item["label"] for item in view["legend"]] == [
        *(bucket["label"] for bucket in BUCKETS[:4]),
        "N/A or prevented",
        "Missed",
        "Not scored",
    ]
    alpha, beta = view["rows"]
    assert alpha["is_reference"] is True
    assert beta["is_reference"] is False
    # Each part's width is its share of all four mistakes, so every bar has
    # the same length.
    assert [segment["title"] for segment in alpha["segments"]] == [
        "Static error: 2",
        "N/A or prevented: 1",
        "Missed: 1",
    ]
    assert alpha["segments"][0]["style"].startswith("width: 50.000%; background: #2f855a")
    assert [segment["title"] for segment in beta["segments"]] == [
        "Runtime error: 1",
        "N/A or prevented: 1",
        "Missed: 1",
        "Not scored: 1",
    ]
    for row in view["rows"]:
        widths = [float(segment["style"].split("%")[0].removeprefix("width: ")) for segment in row["segments"]]
        assert sum(widths) == pytest.approx(100, abs=0.01)



def test_chart_view_draws_a_record_without_a_case_as_its_own_part() -> None:
    report = _report()
    report["results"][6].update(status="missing", cell="-")
    view = chart_view(extract(report, allow_partial=True))
    assert [item["label"] for item in view["legend"]][-1] == "No case written"
    assert view["rows"][1]["segments"][-1]["title"] == "No case written: 1"


def test_chart_view_leaves_out_extra_parts_nobody_has() -> None:
    report = _report()
    report["results"][6].update(bucket="missed", cell="M")
    view = chart_view(extract(report, allow_partial=True))
    assert "Not scored" not in [item["label"] for item in view["legend"]]


def test_views_reject_buckets_and_statuses_they_cannot_name() -> None:
    data = extract(_report(), allow_partial=True)
    unknown_bucket = copy.deepcopy(data)
    unknown_bucket["results"][0]["bucket"] = "mystery"
    with pytest.raises(ValueError, match="alpha / m1 has a bucket the chart cannot name: 'mystery'"):
        chart_view(unknown_bucket)
    with pytest.raises(ValueError, match="cannot name: 'mystery'"):
        table_view(unknown_bucket)

    uncolored = copy.deepcopy(data)
    uncolored["buckets"].append({"id": "mystery", "label": "Mystery"})
    with pytest.raises(ValueError, match=r"no color for: \['mystery'\]"):
        chart_view(uncolored)

    unknown_status = copy.deepcopy(data)
    unknown_status["results"][0]["status"] = "skipped"
    with pytest.raises(ValueError, match="unknown status 'skipped'"):
        chart_view(unknown_status)

    missing = copy.deepcopy(data)
    missing["results"].pop()
    with pytest.raises(ValueError, match=r"no record for: \['beta / m4'\]"):
        chart_view(missing)


def test_table_view_groups_mistakes_by_category() -> None:
    view = table_view(extract(_report(), allow_partial=True))

    # Category order wins over mistake order, and the empty category is skipped.
    assert [(group["heading"], [row["title"] for row in group["rows"]]) for group in view["groups"]] == [
        ("Names", ["First", "Third"]),
        ("Types", ["Second", "Fourth"]),
    ]
    assert view["frameworks"] == ["Alpha", "Beta"]
    first = view["groups"][0]["rows"][0]["cells"]
    assert first[0] == {"text": "E", "style": "--error-bench-tint: #2f855a", "title": "editor: one\ncheck: two"}
    # A cell outside the six buckets stays plain; the reason stands in for
    # missing evidence.
    fourth = view["groups"][1]["rows"][1]["cells"]
    assert fourth[0] == {"text": "n/a", "style": None, "title": "No equivalent"}
    assert view["groups"][0]["rows"][1]["cells"][1] == {"text": "?", "style": None, "title": None}


def test_rendered_chart_draws_rows_and_table() -> None:
    view = chart_view(extract(_report(), allow_partial=True))
    figure = html.fromstring(str(ErrorBenchmarkChartMarkup(title="Mistakes", view=view)))

    rows = figure.xpath(".//*[contains(concat(' ', @class, ' '), ' bench-chart__row ')]")
    assert [row.xpath("string(.//*[@class='bench-chart__name'])") for row in rows] == ["Alpha", "Beta"]
    # The chart has no number column or table: the counts are in the bar
    # parts' titles, and the label screen readers hear lists every count.
    assert not figure.xpath(".//*[@class='bench-chart__total'] | .//table")
    label = figure.xpath(".//*[@role='img']")[0].attrib["aria-label"]
    assert label.startswith("Mistakes. Stacked bar chart of 4 mistakes. Alpha: Static error 2, ")
    assert "Beta: Runtime error 1, " in label


def test_rendered_table_keeps_line_breaks_in_cell_titles(monkeypatch: pytest.MonkeyPatch) -> None:
    data = extract(_report(), allow_partial=True)
    monkeypatch.setattr("docs_site._internal.components.error_benchmark._load_data", lambda: data)
    markup = str(ErrorBenchmarkTable())

    # The markup is on one line for the Markdown pass, but the title still
    # reads back with the line break between the two evidence lines.
    assert "\n" not in markup.strip()
    table = html.fromstring(markup.strip())
    assert table.xpath(".//td/@title")[0] == "editor: one\ncheck: two"
    assert [node.text_content() for node in table.xpath(".//tr[@class='error-bench-table__heading']/th")] == [
        "Names",
        "Types",
    ]
    # Each heading row and the header's second row count the mistakes
    # reported at all, out of those that apply.
    headings = table.xpath(".//tr[@class='error-bench-table__heading']")
    assert [[td.text_content() for td in row.xpath("./td")] for row in headings] == [
        ["(1/2)", "(1/2)"],
        ["(1/1)", "(0/1)"],
    ]
    counts = table.xpath(".//tr[@class='error-bench-table__counts']/td")
    assert [td.text_content() for td in counts] == ["(caught/total)", "(2/3)", "(1/3)"]
    # Each heading labels the rows of its own <tbody>.
    assert table.xpath(".//tr[@class='error-bench-table__heading']/th/@scope") == ["rowgroup", "rowgroup"]


def test_rendered_table_escapes_tool_output(monkeypatch: pytest.MonkeyPatch) -> None:
    data = extract(_report(), allow_partial=True)
    hostile = '<script>alert("x")</script> {{ x }} *em*'
    data["results"][0]["evidence"] = [hostile]
    monkeypatch.setattr("docs_site._internal.components.error_benchmark._load_data", lambda: data)
    markup = str(ErrorBenchmarkTable())

    # Tool output is text: it must not become markup or a template expression.
    assert "<script>" not in markup
    assert html.fromstring(markup.strip()).xpath(".//td/@title")[0] == hostile


def test_checked_in_data_renders() -> None:
    # Guards the data file's shape, not its results: it must draw without an
    # unknown bucket, a missing record, or a stray category.
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert chart_view(data)["rows"]
    assert table_view(data)["groups"]


def test_extract_refuses_an_unscored_case_unless_a_preview_is_asked_for() -> None:
    with pytest.raises(ValueError, match="beta / m3: the case was not scored"):
        extract(_report())
    assert extract(_report(), allow_partial=True)["codes"] == [{"code": "E", "meaning": "reported in the editor"}]
