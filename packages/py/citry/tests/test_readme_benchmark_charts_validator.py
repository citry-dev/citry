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


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """A README with an up-to-date block, its two images, and the data file, all under tmp_path."""
    helper = readme_benchmark_charts._helper()
    helper.README_PATH = tmp_path / "README.md"
    helper.DATA_PATH = tmp_path / "data.json"
    helper.ASSET_DIR = tmp_path / "assets"
    helper.ASSET_DIR.mkdir()
    data = _data()
    helper.DATA_PATH.write_text(json.dumps(data), encoding="utf-8")
    names = {}
    for theme in helper.THEMES:
        png = f"{theme} image".encode()
        names[theme] = helper.image_name(data["run"], png, theme)
        (helper.ASSET_DIR / names[theme]).write_bytes(png)
    block = helper.readme_block(data, light_name=names["light"], dark_name=names["dark"])
    helper.README_PATH.write_text(f"# Project\n\n{block}\n\nMore text.\n", encoding="utf-8")
    monkeypatch.setattr(readme_benchmark_charts, "_helper", lambda: helper)
    return helper


def test_an_up_to_date_block_passes(repo: ModuleType) -> None:
    assert readme_benchmark_charts.check() == []


def test_a_new_run_fails_until_the_images_are_redrawn(repo: ModuleType) -> None:
    repo.DATA_PATH.write_text(json.dumps(_data(run="21000101T000000Z")), encoding="utf-8")
    problems = readme_benchmark_charts.check()
    assert len(problems) == 2
    assert "README.md:3 shows benchmark run 20990101T000000Z, but the data has run 21000101T000000Z" in problems[0]
    assert "python -m docs_site.scripts.benchmark_images" in problems[0]


def test_a_changed_count_fails(repo: ModuleType) -> None:
    repo.DATA_PATH.write_text(json.dumps(_data(second_is_static=False)), encoding="utf-8")
    assert readme_benchmark_charts.check() == [
        "README.md:3 benchmark chart block does not match the data; "
        "rerun `uv run --no-sync python -m docs_site.scripts.benchmark_images`"
    ]


def test_a_missing_or_changed_image_fails(repo: ModuleType) -> None:
    light, dark = sorted(repo.ASSET_DIR.iterdir(), key=lambda path: "dark" in path.name)
    light.unlink()
    dark.write_bytes(b"redrawn in place")
    problems = readme_benchmark_charts.check()
    assert any(f"links {light.name}, which is not in docs/assets/benchmarks/" in problem for problem in problems)
    assert any(f"{dark.name} changed after it was written" in problem for problem in problems)


def test_a_hand_edited_block_fails(repo: ModuleType) -> None:
    readme = repo.README_PATH.read_text(encoding="utf-8")
    repo.README_PATH.write_text(readme.replace("Alpha 2", "Alpha 9"), encoding="utf-8")
    assert "does not match the data" in readme_benchmark_charts.check()[0]


@pytest.mark.parametrize(
    ("readme", "message"),
    [
        ("# Project without a chart block\n", "README.md: README needs exactly one"),
        (
            "<!-- benchmark-chart:errors start -->\nno images\n<!-- benchmark-chart:errors end -->\n",
            "README.md:1 benchmark chart block must link one light and one dark image",
        ),
    ],
)
def test_a_missing_block_or_image_link_fails(repo: ModuleType, readme: str, message: str) -> None:
    repo.README_PATH.write_text(readme, encoding="utf-8")
    problems = readme_benchmark_charts.check()
    assert len(problems) == 1
    assert problems[0].startswith(message)
