"""
How ``citry check`` treats findings in components from a registered library.

An app cannot change a library's code, so by default the check leaves those
findings out of the report and its exit status, and one note counts them.
``--include-libraries`` or ``LintSettings.include_libraries`` reports them.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, cast

import pytest

from citry import Citry, Component, ComponentLibrary, LibraryComponent, LintSettings
from citry.__main__ import main
from citry._app_selection import CheckAppSelection
from citry._checker import check_project

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class CBroken(LibraryComponent):
    template = """
      <p>{{ missing_in_library }}</p>
    """


LIBRARY = ComponentLibrary("test-ui", (CBroken,))
NOTE = (
    "left out 1 finding in components from the registered library 'test-ui'; pass --include-libraries to report them"
)


def _engine(**settings: object) -> Citry:
    engine = Citry(autodiscover=False, **settings)  # type: ignore[arg-type]
    engine.register_library(LIBRARY)
    return engine


def test_findings_in_library_components_are_left_out_and_counted(tmp_path: Path) -> None:
    engine = _engine()

    class AppCard(Component):
        citry = engine
        template = """
          <p>{{ missing_in_app }}</p>
        """

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # The app's own finding still fails the check; the library's is counted.
    assert [finding.origin.rsplit(".", 2)[-2] for finding in report.findings] == ["AppCard"]
    assert report.exit_code == 1
    assert report.skipped_library_findings == (("test-ui", 1),)
    assert report.all_notes[-1] == NOTE


def test_an_app_that_only_registers_a_library_checks_clean(tmp_path: Path) -> None:
    report = check_project(CheckAppSelection(spec="app:engine", engine=_engine()), tmp_path)

    assert report.findings == ()
    assert report.exit_code == 0
    assert NOTE in report.all_notes


@pytest.mark.parametrize("source", ["argument", "setting"])
def test_library_findings_are_reported_when_asked_for(tmp_path: Path, source: str) -> None:
    engine = _engine(lint=LintSettings(include_libraries=True)) if source == "setting" else _engine()

    report = check_project(
        CheckAppSelection(spec="app:engine", engine=engine),
        tmp_path,
        include_libraries=source == "argument",
    )

    assert [finding.origin.rsplit(".", 2)[-2] for finding in report.findings] == ["CBroken"]
    assert report.exit_code == 1
    assert report.skipped_library_findings == ()
    assert not any(note.startswith("left out ") for note in report.all_notes)


def test_a_subclass_of_a_library_component_keeps_its_findings(tmp_path: Path) -> None:
    engine = _engine()
    installed = engine.register_library(LIBRARY)

    class MyBroken(installed[CBroken]):  # type: ignore[misc,valid-type]
        citry = engine

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # The inherited template is also the app's, so its finding stays.
    assert len(report.findings) == 1
    assert "missing_in_library" in report.findings[0].message
    assert report.exit_code == 1
    assert report.skipped_library_findings == ()


class CData(LibraryComponent):
    class Kwargs:
        value: str

    def js_data(self, kwargs, slots):
        return {"value": kwargs.value}

    template = """
      <p>data</p>
    """


DATA_LIBRARY = ComponentLibrary("data-ui", (CData,))


def test_a_subclass_finding_in_inherited_code_is_the_apps(tmp_path: Path) -> None:
    engine = Citry(autodiscover=False)
    installed = engine.register_library(DATA_LIBRARY)

    # The subclass changes the input that the inherited js_data() sends, so
    # the finding is about the subclass although it points at library code.
    class MyData(installed[CData]):  # type: ignore[misc,valid-type]
        citry = engine

        class Kwargs:
            value: bytes

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    assert [finding.origin.rsplit("(", 1)[-1] for finding in report.findings] == [
        f"{MyData.__module__}.{MyData.__qualname__}.js_data)"
    ]
    assert report.skipped_library_findings == ()


class CThemed(CBroken):
    pass


THEME_LIBRARY = ComponentLibrary("theme-ui", (CThemed,))


def test_code_two_libraries_share_is_left_out_and_counted_once(tmp_path: Path) -> None:
    engine = _engine()
    engine.register_library(THEME_LIBRARY)

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # A theme library built on another library brings no app code, so the
    # template both use is left out, and counted once.
    assert report.findings == ()
    assert report.skipped_library_findings == (("test-ui", 1),)


def test_include_libraries_must_be_a_bool() -> None:
    with pytest.raises(TypeError, match="include_libraries must be True or False"):
        LintSettings(include_libraries="false")  # type: ignore[arg-type]


def _run_main(args: list[str]) -> int:
    try:
        return main(args)
    except SystemExit as exc:
        return cast("int", exc.code)


@pytest.fixture
def app_spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """An app module that registers the test library and nothing else."""
    (tmp_path / "check_libraries_app.py").write_text(
        "from citry import Citry, ComponentLibrary, LibraryComponent\n"
        "class CBroken(LibraryComponent):\n"
        '    template = """\n'
        "      <p>{{ missing_in_library }}</p>\n"
        '    """\n'
        "engine = Citry(autodiscover=False)\n"
        "engine.register_library(ComponentLibrary('test-ui', (CBroken,)))\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.chdir(tmp_path)
    yield "check_libraries_app:engine"
    sys.modules.pop("check_libraries_app", None)


def test_the_command_prints_the_count_and_passes(app_spec: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert _run_main(["--app", app_spec, "check"]) == 0
    assert f"citry check: note: {NOTE}\n" in capsys.readouterr().err


def test_the_command_reports_library_findings_with_the_flag(
    app_spec: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run_main(["--app", app_spec, "check", "--include-libraries", "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert [item["origin"].rsplit(".", 2)[-2] for item in payload["findings"]] == ["CBroken"]
    assert not any(note.startswith("left out ") for note in payload["notes"])
