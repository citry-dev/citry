"""Tests for the README benchmark images: their file names, the README block, and the page they are drawn from."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from docs_site._internal.components import benchmark_chart
from docs_site._internal.components.benchmark_text import BenchmarkText
from docs_site._internal.components.error_benchmark import chart_view
from docs_site.scripts import benchmark_images, benchmark_readme

ERRORS_START, ERRORS_END = benchmark_readme.markers("errors")
SPEED_START, SPEED_END = benchmark_readme.markers("speed")

BUCKETS = [
    {"id": "static-error", "label": "Static error"},
    {"id": "static-warning", "label": "Static warning"},
    {"id": "runtime-error", "label": "Runtime error"},
    {"id": "runtime-warning", "label": "Runtime warning"},
    {"id": "missed", "label": "Missed"},
]


def _data(outcomes: dict[str, list[tuple[str, str | None]]]) -> dict[str, Any]:
    # Each framework's list gives one (status, bucket) pair per mistake.
    mistakes = len(next(iter(outcomes.values())))
    return {
        "run": "20990101T000000Z",
        "frameworks": [{"key": key, "name": f'{key.title()} "x"'} for key in outcomes],
        "categories": [{"id": "names", "heading": "Names"}],
        "buckets": BUCKETS,
        "codes": [],
        "mistakes": [{"id": f"m{index}", "title": f"M{index}", "category": "names"} for index in range(mistakes)],
        "results": [
            {
                "framework": key,
                "mistake": f"m{index}",
                "status": status,
                "bucket": bucket,
                "cell": "E",
                "reason": None,
                "evidence": [],
            }
            for key, rows in outcomes.items()
            for index, (status, bucket) in enumerate(rows)
        ],
    }


def _sample() -> dict[str, Any]:
    # Beta and gamma tie on two, and alpha's not-applicable mistake counts for
    # nothing, so the order holds only if both rules are followed.
    return _data(
        {
            "alpha": [("ported", "static-error"), ("not-applicable", None), ("ported", "missed")],
            "beta": [("ported", "static-error"), ("ported", "static-warning"), ("ported", "missed")],
            "gamma": [("ported", "static-warning"), ("ported", "static-error"), ("ported", "runtime-error")],
        },
    )


def _speed(report: str = "composed-0123456789ab") -> dict[str, Any]:
    # Alpha is listed first, so it is the chart's reference (Citry's place in
    # the real data), and it ties with Gamma, so the order holds only if equal
    # totals keep the data's order.
    def row(name: str, total: float) -> dict[str, Any]:
        return {"name": name, "group": None, "total_ms": total, "phases_ms": {"server": total}}

    return {
        "source": {"report_id": report, "outputs": 1400},
        "loads": [
            {"id": "first", "frameworks": [row("Alpha", 900)]},
            {
                "id": benchmark_readme.SPEED_LOAD,
                "frameworks": [row("Alpha", 300.4), row('Beta "x"', 1250.5), row("Gamma", 300.4), row("Delta", 99.6)],
            },
        ],
    }


def test_image_names_hold_the_chart_the_run_the_bytes_hash_and_the_theme() -> None:
    name = benchmark_readme.image_name("errors", "20990101T000000Z", b"png bytes", "dark")
    digest = hashlib.sha256(b"png bytes").hexdigest()[:12]
    assert name == f"errors-20990101T000000Z-{digest}-dark.png"
    assert benchmark_readme.parse_image_name(name) == {
        "chart": "errors",
        "run": "20990101T000000Z",
        "hash": digest,
        "theme": "dark",
    }
    # Different bytes from the same run get a different name, never the same file.
    assert benchmark_readme.image_name("errors", "20990101T000000Z", b"other bytes", "dark") != name
    assert benchmark_readme.parse_image_name("errors-run-123-light.png") is None
    # The runner names a second run in the same second with a "-2" suffix.
    second = benchmark_readme.image_name("errors", "20990101T000000Z-2", b"png bytes", "light")
    assert benchmark_readme.parse_image_name(second) == {
        "chart": "errors",
        "run": "20990101T000000Z-2",
        "hash": digest,
        "theme": "light",
    }
    # A speed report id ends in hex digits like the hash; the hash is still
    # read from the end of the name.
    speed = benchmark_readme.image_name("speed", "composed-0123456789ab", b"png bytes", "light")
    assert benchmark_readme.parse_image_name(speed) == {
        "chart": "speed",
        "run": "composed-0123456789ab",
        "hash": digest,
        "theme": "light",
    }


@pytest.mark.parametrize(
    ("chart", "run", "theme", "message"),
    [
        ("errors", "20990101T000000Z", "sepia", "Unknown image theme"),
        ("errors", "../escape", "light", "only letters, digits, and hyphens"),
        ("pie", "20990101T000000Z", "light", "Unknown README chart"),
    ],
)
def test_image_names_reject_values_that_do_not_fit_a_url(chart: str, run: str, theme: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        benchmark_readme.image_name(chart, run, b"png", theme)


def test_alt_text_counts_match_the_sorted_chart() -> None:
    data = _sample()
    shares = benchmark_readme.static_shares(data)
    # Alpha's not-applicable mistake leaves it 1 of 2.
    assert [(count, applicable) for _, count, applicable in shares] == [(2, 3), (2, 3), (1, 2)]
    # The README's alt text reads the bars from top to bottom, with the
    # number drawn beside each bar.
    rows = chart_view(data, sort="share", scale="applicable")["rows"]
    assert [f"{count} of {applicable}" for _, count, applicable in shares] == [row["total"] for row in rows]
    assert [name for name, _, _ in shares] == [row["name"] for row in rows]


@pytest.mark.parametrize(
    "change",
    [{"bucket": None}, {"status": "missing", "bucket": None}],
)
def test_counts_refuse_a_case_without_a_result(change: dict[str, Any]) -> None:
    # Data written with --allow-partial can hold a case nobody wrote or scored
    # yet; a README count built from it would look final while missing it.
    data = _sample()
    data["results"][0].update(change)
    with pytest.raises(ValueError, match="alpha / m0 has no result"):
        benchmark_readme.static_shares(data)


def test_readme_block_links_both_images_and_escapes_the_alt_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark_readme, "VERSION_NOTES", {"20990101T000000Z": "Citry 9.9.9, synthetic."})
    block = benchmark_readme.readme_block("errors", _sample(), light_name="light.png", dark_name="dark.png")

    assert block.startswith(ERRORS_START)
    assert block.endswith(ERRORS_END)
    assert benchmark_readme.image_names_in(block) == ["dark.png", "light.png"]
    assert f'srcset="{benchmark_readme.ASSET_URL}/dark.png"' in block
    assert f'src="{benchmark_readme.ASSET_URL}/light.png"' in block
    # A quote in a framework name is escaped rather than ending the attribute.
    assert "Beta &quot;x&quot; 2 of 3, Gamma &quot;x&quot; 2 of 3, Alpha &quot;x&quot; 1 of 2." in block
    assert "3 frameworks" in block
    # The version the run measured stands beside the counts.
    assert "Citry 9.9.9, synthetic. Each bar counts only" in block


def test_errors_block_puts_the_hint_between_the_intro_and_the_image(monkeypatch: pytest.MonkeyPatch) -> None:
    # The landing card reads intro, hint, chart; the README keeps that order.
    monkeypatch.setattr(benchmark_readme, "VERSION_NOTES", {"20990101T000000Z": "Citry 9.9.9, synthetic."})
    monkeypatch.setattr(benchmark_readme, "ERRORS_HINT", "Synthetic hint")
    block = benchmark_readme.readme_block("errors", _sample(), light_name="light.png", dark_name="dark.png")
    paragraphs = [" ".join(part.split()) for part in block.split("\n\n")]
    intro = paragraphs.index(benchmark_readme.errors_intro(_sample()))
    assert paragraphs[intro + 1] == "Synthetic hint"
    assert paragraphs[intro + 2].startswith("<picture>")


def test_speed_totals_match_the_sorted_chart() -> None:
    data = _speed()
    totals = benchmark_readme.speed_totals(data)
    # The README's alt text reads the bars from top to bottom, with the
    # number drawn beside each bar, as the landing page draws the chart.
    view = benchmark_chart.chart_view(data, benchmark_readme.SPEED_LOAD, sort="total", phases=False, compact=True)
    assert [name for name, _ in totals] == [row["name"] for row in view["rows"]]
    assert [benchmark_readme.format_ms(total) for _, total in totals] == [row["total"] for row in view["rows"]]
    # Equal totals keep the data's order.
    assert [name for name, _ in totals][1:3] == ["Alpha", "Gamma"]


def test_speed_block_links_both_images_and_lists_every_total(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark_readme, "SPEED_VERSION_NOTES", {"composed-0123456789ab": "Citry 9.9.9."})
    data = _speed()
    block = benchmark_readme.readme_block("speed", data, light_name="light.png", dark_name="dark.png")

    assert block.startswith(SPEED_START)
    assert block.endswith(SPEED_END)
    assert f"## {benchmark_readme.HEADINGS['speed']}" in block
    assert benchmark_readme.image_names_in(block) == ["dark.png", "light.png"]
    assert benchmark_readme.SPEED_DETAILS_URL in block
    # Every framework and its total, fastest first, with a quote escaped
    # rather than ending the attribute.
    assert "Delta 100 ms, Alpha 300 ms, Gamma 300 ms, Beta &quot;x&quot; 1,250 ms." in block
    flat = " ".join(block.split())
    assert benchmark_readme.speed_intro(data) in flat
    assert benchmark_readme.speed_note(data) in flat
    assert "Citry 9.9.9." in flat


def test_speed_block_needs_a_version_note_for_the_report(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark_readme, "SPEED_VERSION_NOTES", {})
    with pytest.raises(ValueError, match="No version note for speed benchmark report composed-0123456789ab"):
        benchmark_readme.readme_block("speed", _speed(), light_name="light.png", dark_name="dark.png")


def test_speed_note_names_the_citry_of_the_report_citry_came_from(monkeypatch: pytest.MonkeyPatch) -> None:
    # Other frameworks measured again in a newer report must not relabel
    # Citry's older numbers with the newer report's Citry version.
    monkeypatch.setattr(benchmark_readme, "SPEED_VERSION_NOTES", {"older": "Citry 1.0.0.", "newer": "Citry 2.0.0."})
    data = _speed()
    data["source"].update(report_id="newer", citry_report_id="older")
    assert benchmark_readme.speed_note(data).startswith("Citry 1.0.0.")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda data: data["loads"].pop(), "has no 'second' load"),
        (lambda data: data["loads"][1].update(frameworks=[]), "has no frameworks to draw"),
    ],
)
def test_speed_totals_refuse_a_load_the_chart_cannot_draw(change: Any, message: str) -> None:
    data = _speed()
    change(data)
    with pytest.raises(ValueError, match=message):
        benchmark_readme.speed_totals(data)


@pytest.mark.parametrize("part", ["errors-intro", "errors-hint", "errors-note", "speed-intro", "speed-note"])
def test_benchmark_text_prints_the_readme_sentence(part: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # The landing page prints each shared sentence through this tag, so it
    # must print exactly what the README block holds.
    monkeypatch.setattr(benchmark_readme, "VERSION_NOTES", {"20990101T000000Z": "Citry 9.9.9, synthetic."})
    monkeypatch.setattr(benchmark_readme, "SPEED_VERSION_NOTES", {"composed-0123456789ab": "Citry 9.9.9."})
    monkeypatch.setattr(
        benchmark_readme,
        "load_data",
        lambda chart="errors": _sample() if chart == "errors" else _speed(),
    )
    chart = part.split("-")[0]
    data = benchmark_readme.load_data(chart)
    block = benchmark_readme.readme_block(chart, data, light_name="light.png", dark_name="dark.png")
    text = str(BenchmarkText(part=part)).strip()
    assert text
    assert text in " ".join(block.split())


def test_readme_block_needs_a_version_note_for_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark_readme, "VERSION_NOTES", {})
    with pytest.raises(ValueError, match="No version note for error benchmark run 20990101T000000Z"):
        benchmark_readme.readme_block("errors", _sample(), light_name="light.png", dark_name="dark.png")


def test_counts_use_the_short_names_only_when_asked() -> None:
    data = _sample()
    data["frameworks"][1]["key"] = "django-components"
    for record in data["results"]:
        if record["framework"] == "beta":
            record["framework"] = "django-components"
    assert benchmark_readme.static_shares(data, short_names=True)[0][0] == "django-components"
    assert benchmark_readme.static_shares(data)[0][0] == 'Beta "x"'


@pytest.mark.parametrize(
    ("change", "message"),
    [
        # An unknown status, which the chart would also refuse.
        (lambda data: data["results"][0].update(status="skipped"), "alpha / m0 has an unknown status 'skipped'"),
        # A repeated record would count twice.
        (lambda data: data["results"].append(dict(data["results"][0])), "more than one record for alpha / m0"),
        # A missing record would count for nobody.
        (lambda data: data["results"].pop(0), r"no record for: \['alpha / m0'\]"),
        # A record for a framework the data does not list.
        (
            lambda data: data["results"].append({**data["results"][0], "framework": "omega"}),
            "omega / m0 names a framework or mistake the data does not list",
        ),
    ],
)
def test_counts_need_exactly_one_known_record_per_case(change: Any, message: str) -> None:
    data = _sample()
    change(data)
    with pytest.raises(ValueError, match=message):
        benchmark_readme.static_shares(data)


def test_replace_block_swaps_only_the_marked_text() -> None:
    readme = f"intro\n{ERRORS_START}\nold\n{ERRORS_END}\n{SPEED_START}\nold\n{SPEED_END}\noutro\n"
    assert (
        benchmark_readme.replace_block(readme, "errors", "NEW")
        == f"intro\nNEW\n{SPEED_START}\nold\n{SPEED_END}\noutro\n"
    )
    assert (
        benchmark_readme.replace_block(readme, "speed", "NEW")
        == f"intro\n{ERRORS_START}\nold\n{ERRORS_END}\nNEW\noutro\n"
    )


@pytest.mark.parametrize(
    ("readme", "message"),
    [
        ("no markers here\n", "exactly one"),
        (
            f"{ERRORS_START}\n{ERRORS_END}\n{ERRORS_START}\n{ERRORS_END}\n",
            r"markers on lines \[1, 2, 3, 4\]",
        ),
        (f"{ERRORS_END}\n{ERRORS_START}\n", "line 1, before its start marker"),
    ],
)
def test_replace_block_refuses_missing_doubled_or_reversed_markers(readme: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        benchmark_readme.replace_block(readme, "errors", "NEW")


def test_page_carries_the_font_inline_and_the_chosen_theme() -> None:
    page = benchmark_images.page_html("<figure>chart</figure>", "dark")
    # A page with no address cannot follow the stylesheet's relative font path.
    assert benchmark_images.FONT_URL not in page
    assert "data:font/woff2;base64," in page
    assert '<html data-theme="dark">' in page
    assert "<figure>chart</figure>" in page


def test_speed_page_frames_the_chart_like_the_landing_card() -> None:
    # The speed chart's bar colours come from the landing card's class and
    # the landing shell around it, both styled by the landing page's CSS.
    page = benchmark_images.page_html("<figure>chart</figure>", "light", benchmark_images.FRAMES["speed"])
    assert 'class="readme-chart prose landing-benchmark-card"><figure>chart</figure>' in page
    assert '<div class="landing-shell">' in page
    assert "--bench-bar-reference" in page


def test_saving_never_overwrites_an_existing_image(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark_readme, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(benchmark_readme, "ASSET_DIR", tmp_path / "assets")

    name = benchmark_images._save("errors", "20990101T000000Z", b"first", "light")
    path = tmp_path / "assets" / name
    assert path.read_bytes() == b"first"
    # A file under the same name is left exactly as it was.
    path.write_bytes(b"published")
    assert benchmark_images._save("errors", "20990101T000000Z", b"first", "light") == name
    assert path.read_bytes() == b"published"
