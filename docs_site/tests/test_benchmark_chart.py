"""Tests for the benchmark chart component and the script that feeds it data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from lxml import html

from docs_site._internal.components.benchmark_chart import (
    DATA_PATH,
    BenchmarkChart,
    BenchmarkChartMarkup,
    axis_ticks,
    chart_view,
)
from docs_site.scripts import benchmark_data
from docs_site.scripts.benchmark_data import GROUPS, build, embedded_report_data, extract


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
    samples.append({**_sample("citry", 1, {"server": 999.0}, 0.0), "count": 140})
    result = extract(_report(samples), _manifest())

    first = result["loads"][0]["frameworks"]
    assert first[0] == {
        "key": "citry",
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
    # Every number came from this report, so it kept nothing from another.
    assert result["source"]["kept_from"] == []


def test_extract_rejects_phases_that_do_not_add_up() -> None:
    samples = _all_samples()
    samples[0]["ready_elapsed_ms"] += 5
    with pytest.raises(ValueError, match="citry load 1: phases do not add up"):
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


def _current() -> dict[str, Any]:
    # The data file as an earlier, complete report left it: every framework
    # measured in run "older-run", with totals of 37 ms and more.
    manifest = {
        **_manifest(),
        "id": "older-report",
        "composed_at": "2026-01-01T00:00:00+00:00",
        "citry_configuration": "older Citry",
        "cell_provenance": {
            f"{key}/1400": {"latency": "measured", "latency_run": "older-run"}
            for _, members in GROUPS
            for key, _ in members
        },
    }
    samples = [
        _sample(key, load, {"server": 30.0 + index, "browser_after": 5.0}, 2.0)
        for load in (1, 2)
        for index, key in enumerate(key for _, members in GROUPS for key, _ in members)
    ]
    return extract(_report(samples), manifest)


def _rerun(apps: tuple[str, ...] = ("citry", "jinja_htmx_alpine")) -> tuple[str, dict[str, Any]]:
    # A later report that measured only a few frameworks, each at 11 ms on the
    # first load and 12 ms on the second.
    manifest = {
        **_manifest(),
        "id": "newer-report",
        "citry_configuration": "newer Citry",
        "cell_provenance": {f"{app}/1400": {"latency": "measured", "latency_run": "newer-run"} for app in apps},
    }
    samples = [
        _sample(app, load, {"server": 3.0 + load, "browser_after": 5.0}, 2.0) for load in (1, 2) for app in apps
    ]
    return _report(samples), manifest


def _row(data: dict[str, Any], load: str, key: str) -> dict[str, Any]:
    entries = next(entry for entry in data["loads"] if entry["id"] == load)["frameworks"]
    return next(row for row in entries if row["key"] == key)


def test_only_takes_the_named_frameworks_and_keeps_the_rest_from_the_current_file() -> None:
    current = _current()
    data, controls = build(*_rerun(), only=["citry"], current=current)

    assert _row(data, "first", "citry") == {
        **_row(current, "first", "citry"),
        "total_ms": 11.0,
        "phases_ms": {"server": 4.0, "browser_after": 5.0, "layout_wait": 2.0},
        "measured_in_run": "newer-run",
    }
    # The control framework keeps its earlier numbers; only Citry is published.
    jinja = _row(data, "second", "jinja_htmx_alpine")
    assert jinja == {**_row(current, "second", "jinja_htmx_alpine"), "retained": True}
    assert jinja["measured_in_run"] == "older-run"
    keys = [row["key"] for row in data["loads"][0]["frameworks"]]
    assert keys == [key for _, members in GROUPS for key, _ in members]
    assert all(row["retained"] for load in data["loads"] for row in load["frameworks"] if row["key"] != "citry")

    source = data["source"]
    assert (source["report_id"], source["citry_report_id"]) == ("newer-report", "newer-report")
    assert source["citry_configuration"] == "newer Citry"
    assert source["kept_from"] == [
        {
            "report_id": "older-report",
            "composed_at": "2026-01-01T00:00:00+00:00",
            "frameworks": [key for key in keys if key != "citry"],
        },
    ]
    # Jinja's kept first-load total is 37 + 3 ms; the report measured 11 ms.
    assert controls == [
        "Jinja + HTMX + Alpine, first load: 11.0 ms in the report, 40.0 ms kept (-72.5%); "
        "server 4.0 against 33.0, browser 5.0 against 5.0 ms",
        "Jinja + HTMX + Alpine, second load: 12.0 ms in the report, 40.0 ms kept (-70.0%); "
        "server 5.0 against 33.0, browser 5.0 against 5.0 ms",
    ]


def test_only_keeps_citry_build_from_the_report_citry_came_from() -> None:
    current = _current()
    current["source"]["citry_build"] = {"source_commit": "older-commit"}
    # A file written before citry_report_id existed took Citry from its report.
    del current["source"]["citry_report_id"]
    data, _ = build(*_rerun(("reflex",)), only=["reflex"], current=current)

    source = data["source"]
    assert (source["report_id"], source["citry_report_id"]) == ("newer-report", "older-report")
    assert source["citry_configuration"] == "older Citry"
    assert source["citry_build"] == {"source_commit": "older-commit"}
    assert _row(data, "first", "citry")["retained"] is True
    assert _row(data, "first", "reflex")["measured_in_run"] == "newer-run"


def test_a_second_merge_still_names_the_report_that_measured_each_kept_entry() -> None:
    first, _ = build(*_rerun(("citry",)), only=["citry"], current=_current())
    document, manifest = _rerun(("reflex",))
    second, _ = build(document, {**manifest, "id": "newest-report"}, only=["reflex"], current=first)

    others = [key for _, members in GROUPS for key, _ in members if key not in {"citry", "reflex"}]
    assert second["source"]["kept_from"] == [
        {"report_id": "newer-report", "composed_at": None, "frameworks": ["citry"]},
        {"report_id": "older-report", "composed_at": "2026-01-01T00:00:00+00:00", "frameworks": others},
    ]
    assert (second["source"]["citry_report_id"], second["source"]["citry_configuration"]) == (
        "newer-report",
        "newer Citry",
    )


def test_only_refuses_to_keep_an_entry_the_same_report_measured() -> None:
    # Taking only Jinja from the report that already supplied Citry would
    # mark Citry's entry as kept from the very report being read.
    document, manifest = _rerun()
    merged, _ = build(document, manifest, only=["citry"], current=_current())
    with pytest.raises(ValueError, match="citry: the current data file already took its numbers from this report"):
        build(document, manifest, only=["jinja_htmx_alpine"], current=merged)
    # Taking the same frameworks again from the same report gives the same file.
    assert build(document, manifest, only=["citry"], current=merged)[0] == merged


def test_only_refuses_a_control_that_fails_the_checks() -> None:
    document, manifest = _rerun()
    rows = embedded_report_data(document)["samples"]
    next(row for row in rows if row["app"] == "jinja_htmx_alpine")["status"] = "failed"
    with pytest.raises(ValueError, match=r"cannot compare the control frameworks \['jinja_htmx_alpine'\]"):
        build(_report(rows), manifest, only=["citry"], current=_current())


def _without(data: dict[str, Any], key: str) -> dict[str, Any]:
    loads = [
        {**load, "frameworks": [row for row in load["frameworks"] if row["key"] != key]} for load in data["loads"]
    ]
    return {**data, "loads": loads}


@pytest.mark.parametrize(
    ("only", "current", "message"),
    [
        (["citry", "svelte"], _current(), r"does not draw: \['svelte'\]"),
        (["reflex"], _current(), r"did not measure \['reflex'\]"),
        (["citry"], _without(_current(), "nuxt"), "nuxt load 1: not named with --only and not in the current"),
        (["citry"], None, "needs that file"),
        ([], _current(), "at least one framework"),
    ],
)
def test_only_refuses_a_framework_neither_source_can_supply(
    only: list[str], current: dict[str, Any] | None, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        build(*_rerun(), only=only, current=current)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("scenario", "board (other-revision)"),
        ("outputs", 140),
        ("observations_per_framework_and_load", 3),
        ("host", {"system": "Linux"}),
        ("browser", "chromium 2.0"),
        ("network", "shaped"),
        ("cache", "warm"),
        ("compression", "gzip"),
    ],
)
def test_only_refuses_numbers_measured_another_way(field: str, value: Any) -> None:
    current = _current()
    current["source"][field] = value
    with pytest.raises(ValueError, match=f"cannot share a chart: {field}: the report has"):
        build(*_rerun(), only=["citry"], current=current)


def test_only_refuses_a_current_file_that_does_not_record_a_compared_field() -> None:
    current = _current()
    del current["source"]["browser"]
    message = r"browser: the report has 'chromium 1\.0', the current data file does not record it"
    with pytest.raises(ValueError, match=message):
        build(*_rerun(), only=["citry"], current=current)


def test_main_keeps_entries_from_the_file_it_rewrites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    document, manifest = _rerun()
    (tmp_path / "report.html").write_text(document, encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps(_current()), encoding="utf-8")
    monkeypatch.setattr(benchmark_data, "DATA_PATH", data_path)

    assert benchmark_data.main([str(tmp_path), "--only", "citry"]) == 0
    written = json.loads(data_path.read_text(encoding="utf-8"))
    assert _row(written, "first", "nuxt")["retained"] is True
    assert "Jinja + HTMX + Alpine, first load" in capsys.readouterr().out

    # A refused merge leaves the file as it was and says why.
    assert benchmark_data.main([str(tmp_path), "--only", "reflex"]) == 1
    assert json.loads(data_path.read_text(encoding="utf-8")) == written
    assert "did not measure ['reflex']" in capsys.readouterr().err

    # A data file that is missing, unreadable or of another shape is
    # reported by name instead of ending in a traceback.
    for content in ("{", "[]"):
        data_path.write_text(content, encoding="utf-8")
        assert benchmark_data.main([str(tmp_path), "--only", "citry"]) == 1
        assert "data.json" in capsys.readouterr().err
    data_path.unlink()
    assert benchmark_data.main([str(tmp_path), "--only", "citry"]) == 1
    assert "data.json" in capsys.readouterr().err
    assert benchmark_data.main([str(tmp_path / "missing"), "--only", "citry"]) == 1
    assert "report.html" in capsys.readouterr().err


@pytest.mark.parametrize("load", ["first", "second"])
def test_checked_in_data_renders(load: str) -> None:
    # Guards the data file's shape, not its numbers: every load it lists must
    # draw without an unknown phase or an empty chart.
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    view = chart_view(data, load)
    assert view["rows"]
    assert view["ticks"][-1]["label"].endswith(" ms")


def test_chart_can_leave_out_the_table_but_keeps_its_label(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("docs_site._internal.components.benchmark_chart._load_data", _data)
    with_table = html.fromstring(str(BenchmarkChart(load="first", title="First load")).strip())
    without_table = html.fromstring(str(BenchmarkChart(load="first", title="First load", show_table=False)).strip())

    assert with_table.xpath(".//table")
    assert not without_table.xpath(".//table | .//details")
    # The plot's label still gives screen readers every total.
    label = without_table.xpath(".//*[@role='img']")[0].attrib["aria-label"]
    assert label.endswith("Alpha 200 ms, Beta 300 ms, Gamma 100 ms.")


def test_chart_view_can_sort_by_total_without_groups() -> None:
    # Alpha, the reference, is in the middle by total; Beta and Gamma share a
    # group whose heading must go once the rows are reordered.
    view = chart_view(_data(), "first", sort="total")
    assert [row.get("name") for row in view["rows"]] == ["Gamma", "Alpha", "Beta"]
    assert not [row for row in view["rows"] if row["heading"]]
    assert [row["is_reference"] for row in view["rows"]] == [False, True, False]
    assert view["summary"].endswith("Gamma 100 ms, Alpha 200 ms, Beta 300 ms.")
    # The default keeps the data's order under its group headings.
    assert [row["heading"] for row in chart_view(_data(), "first")["rows"]] == [None, "Group B", None, None]


def test_chart_view_can_draw_totals_without_phases() -> None:
    view = chart_view(_data(), "first", phases=False, compact=True)
    # One bar per framework, no legend, and Citry's bar in its own colour.
    assert view["legend"] == []
    alpha, beta, _gamma = (row for row in view["rows"] if not row["heading"])
    assert len(alpha["segments"]) == 1
    assert "var(--bench-bar-reference" in alpha["segments"][0]["style"]
    assert "var(--bench-bar," in beta["segments"][0]["style"]
    # Without an axis, the slowest bar (Beta, 300 ms) fills the track.
    assert beta["segments"][0]["style"].startswith("width: 100.000%")
    assert view["compact"] is True
    # The table under a chart still lists every phase.
    assert view["columns"] == ["Server builds the page", "Browser work and later requests"]


def test_chart_view_rejects_an_unknown_sort() -> None:
    with pytest.raises(ValueError, match="Unknown benchmark chart sort 'name'"):
        chart_view(_data(), "first", sort="name")


def test_chart_tag_draws_the_compact_chart(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("docs_site._internal.components.benchmark_chart._load_data", _data)
    compact = html.fromstring(
        str(BenchmarkChart(load="first", title="First", sort="total", phases=False, compact=True)).strip()
    )
    assert "bench-chart--compact" in compact.xpath("//figure")[0].attrib["class"]
    # A chart without phases has no legend list at all.
    assert not compact.xpath("//ul")
    plain = html.fromstring(str(BenchmarkChart(load="first", title="First")).strip())
    assert plain.xpath("//figure")[0].attrib["class"] == "bench-chart"
