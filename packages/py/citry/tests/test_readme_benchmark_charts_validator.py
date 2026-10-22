"""The README benchmark chart validator fails when the README no longer shows the current benchmark data."""

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from scripts.validators import readme_benchmark_charts


def _data(run: str = "20990101T000000Z", second_is_static: bool = True) -> dict[str, Any]:
    # Two frameworks and two mistakes; the flag changes one count, which is
    # what a new benchmark run would do to the alt text.
    bucket = "static-error" if second_is_static else "missed"
    return {
        "run": run,
        "frameworks": [{"key": "alpha", "name": "Alpha"}, {"key": "beta", "name": "Beta"}],
        "mistakes": [{"id": "m1"}, {"id": "m2"}],
        "results": [
            {"framework": "alpha", "mistake": "m1", "status": "ported", "bucket": "static-error"},
            {"framework": "alpha", "mistake": "m2", "status": "ported", "bucket": bucket},
            {"framework": "beta", "mistake": "m1", "status": "ported", "bucket": "missed"},
            {"framework": "beta", "mistake": "m2", "status": "not-applicable", "bucket": None},
        ],
    }


def _speed(total: float = 300) -> dict[str, Any]:
    # A different total changes one number in the alt text, as a new speed
    # report would.
    def row(name: str, value: float) -> dict[str, Any]:
        return {"name": name, "group": None, "total_ms": value, "phases_ms": {"server": value}}

    return {
        "source": {"report_id": "composed-0123456789ab", "outputs": 10},
        "loads": [{"id": "second", "frameworks": [row("Alpha", total), row("Beta", 200)]}],
    }


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """A README with up-to-date blocks for both charts, their images, the data files, and a landing page."""
    helper = readme_benchmark_charts._helper()
    helper.REPO_ROOT = tmp_path
    helper.README_PATH = tmp_path / "README.md"
    helper.LANDING_PATH = tmp_path / "index.md"
    helper.DATA_PATH = tmp_path / "data.json"
    helper.SPEED_DATA_PATH = tmp_path / "speed.json"
    helper.ASSET_DIR = tmp_path / "assets"
    helper.ASSET_DIR.mkdir()
    helper.HEADINGS = {"errors": "Errors heading", "speed": "Speed heading"}
    helper.VERSION_NOTES = {"20990101T000000Z": "Citry 9.9.9, synthetic."}
    helper.SPEED_VERSION_NOTES = {"composed-0123456789ab": "Citry 9.9.9, one run."}
    helper.DATA_PATH.write_text(json.dumps(_data()), encoding="utf-8")
    helper.SPEED_DATA_PATH.write_text(json.dumps(_speed()), encoding="utf-8")
    blocks = []
    for chart in helper.CHARTS:
        data = helper.load_data(chart)
        names = {}
        for theme in helper.THEMES:
            png = f"{chart} {theme} image".encode()
            names[theme] = helper.image_name(chart, helper.run_id(chart, data), png, theme)
            (helper.ASSET_DIR / names[theme]).write_bytes(png)
        blocks.append(helper.readme_block(chart, data, light_name=names["light"], dark_name=names["dark"]))
    helper.README_PATH.write_text(f"# Project\n\n{blocks[0]}\n\n{blocks[1]}\n\nMore text.\n", encoding="utf-8")
    helper.LANDING_PATH.write_text("## Errors heading\n\ntext\n\n## Speed heading\n", encoding="utf-8")
    monkeypatch.setattr(readme_benchmark_charts, "_helper", lambda: helper)
    return helper


def _speed_line(repo: ModuleType) -> int:
    readme = repo.README_PATH.read_text(encoding="utf-8")
    return readme[: readme.index(repo.markers("speed")[0])].count("\n") + 1


def test_an_up_to_date_block_passes(repo: ModuleType) -> None:
    assert readme_benchmark_charts.check() == []


def test_a_new_run_fails_until_the_images_are_redrawn(repo: ModuleType) -> None:
    repo.DATA_PATH.write_text(json.dumps(_data(run="21000101T000000Z")), encoding="utf-8")
    problems = readme_benchmark_charts.check()
    assert len(problems) == 2
    assert (
        "README.md:3 shows errors benchmark run 20990101T000000Z, but the data has run 21000101T000000Z" in problems[0]
    )
    assert "python -m docs_site.scripts.benchmark_images" in problems[0]


def test_a_changed_count_fails(repo: ModuleType) -> None:
    repo.DATA_PATH.write_text(json.dumps(_data(second_is_static=False)), encoding="utf-8")
    assert readme_benchmark_charts.check() == [
        "README.md:3 errors benchmark chart block does not match the data; "
        "rerun `uv run --no-sync python -m docs_site.scripts.benchmark_images errors`"
    ]


def test_a_missing_or_changed_image_fails(repo: ModuleType) -> None:
    light, dark = sorted(repo.ASSET_DIR.glob("errors-*"), key=lambda path: "dark" in path.name)
    light.unlink()
    dark.write_bytes(b"redrawn in place")
    problems = readme_benchmark_charts.check()
    assert any(f"links {light.name}, which is not in docs/assets/benchmarks/" in problem for problem in problems)
    assert any(f"{dark.name} changed after it was written" in problem for problem in problems)


def test_a_hand_edited_block_fails(repo: ModuleType) -> None:
    readme = repo.README_PATH.read_text(encoding="utf-8")
    repo.README_PATH.write_text(readme.replace("Alpha 2 of 2", "Alpha 9 of 2"), encoding="utf-8")
    assert "does not match the data" in readme_benchmark_charts.check()[0]


@pytest.mark.parametrize(
    ("readme", "message"),
    [
        ("# Project without a chart block\n", "README.md: README needs exactly one"),
        (
            "<!-- benchmark-chart:errors start -->\nno images\n<!-- benchmark-chart:errors end -->\n",
            "README.md:1 errors benchmark chart block must link one light and one dark errors image",
        ),
    ],
)
def test_a_missing_block_or_image_link_fails(repo: ModuleType, readme: str, message: str) -> None:
    # Keep the speed block, so only the errors block is wrong.
    current = repo.README_PATH.read_text(encoding="utf-8")
    start, end = repo.find_block(current, "speed")
    repo.README_PATH.write_text(f"{readme}\n{current[start:end]}\n", encoding="utf-8")
    problems = readme_benchmark_charts.check()
    assert len(problems) == 1
    assert problems[0].startswith(message)


def test_a_run_without_a_version_note_fails(repo: ModuleType) -> None:
    # The README must not show a count without the Citry version it measured.
    repo.VERSION_NOTES = {}
    problems = readme_benchmark_charts.check()
    assert len(problems) == 1
    assert problems[0].startswith("README.md:3 No version note for error benchmark run 20990101T000000Z")


def test_a_new_speed_report_fails_until_the_images_are_redrawn(repo: ModuleType) -> None:
    data = _speed()
    data["source"]["report_id"] = "composed-ba9876543210"
    repo.SPEED_DATA_PATH.write_text(json.dumps(data), encoding="utf-8")
    problems = readme_benchmark_charts.check()
    assert len(problems) == 2
    line = _speed_line(repo)
    assert problems[0].startswith(
        f"README.md:{line} shows speed benchmark run composed-0123456789ab, but the data has run composed-ba9876543210"
    )
    assert "python -m docs_site.scripts.benchmark_images speed" in problems[0]


def test_a_changed_speed_total_fails(repo: ModuleType) -> None:
    repo.SPEED_DATA_PATH.write_text(json.dumps(_speed(total=301)), encoding="utf-8")
    assert readme_benchmark_charts.check() == [
        f"README.md:{_speed_line(repo)} speed benchmark chart block does not match the data; "
        "rerun `uv run --no-sync python -m docs_site.scripts.benchmark_images speed`"
    ]


def test_a_speed_report_without_a_version_note_fails(repo: ModuleType) -> None:
    repo.SPEED_VERSION_NOTES = {}
    problems = readme_benchmark_charts.check()
    assert len(problems) == 1
    assert problems[0].startswith(
        f"README.md:{_speed_line(repo)} No version note for speed benchmark report composed-0123456789ab"
    )


def test_an_image_of_the_other_chart_fails(repo: ModuleType) -> None:
    # A speed image linked from the errors block would pass the hash check,
    # so the chart in its name is checked too.
    readme = repo.README_PATH.read_text(encoding="utf-8")
    errors_light = next(repo.ASSET_DIR.glob("errors-*-light.png")).name
    speed_light = next(repo.ASSET_DIR.glob("speed-*-light.png")).name
    start, end = repo.find_block(readme, "errors")
    block = readme[start:end].replace(errors_light, speed_light)
    repo.README_PATH.write_text(readme[:start] + block + readme[end:], encoding="utf-8")
    problems = readme_benchmark_charts.check()
    assert len(problems) == 1
    assert "errors benchmark chart block must link one light and one dark errors image" in problems[0]


def test_a_landing_page_without_the_readme_heading_fails(repo: ModuleType) -> None:
    repo.LANDING_PATH.write_text("## Errors heading\n\n## Another speed heading\n", encoding="utf-8")
    problems = readme_benchmark_charts.check()
    assert len(problems) == 1
    assert problems[0].startswith("index.md: has no '## Speed heading' section")
