"""Citry UI's components pass `citry check --types`, and the editor accepts their documented input forms."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import citry_ui
from citry_lsp.engine import DocumentState
from citry_lsp.project import load_project
from citry_lsp.semantic import semantic_diagnostics
from citry_lsp.type_analysis import TyAnalyzer
from citry_lsp.typescript import TypeScriptUnavailableError, find_typescript_compiler

if TYPE_CHECKING:
    from lsprotocol import types

# The Node workspace installs TypeScript here. Only the repository check job
# installs the Node workspace; elsewhere the test skips unless `tsc` is on PATH.
_REPOSITORY_NODE_PROJECT = Path(__file__).resolve().parents[4] / "packages" / "js" / "citry-client"

# `citry check --types` checks the components whose source lives in the
# current directory, so the check runs from the installed package itself.
_CITRY_UI_PACKAGE = Path(citry_ui.__file__).resolve().parent

_APP_WITHOUT_I18N = """import citry_ui
from citry import Citry

engine = Citry(autodiscover=False)
engine.register_library(citry_ui)
"""

# An app that also loads Citry UI's message catalog, as a translated app does.
_APP_WITH_I18N = """import citry_ui
from citry import Citry

engine = Citry(
    autodiscover=False,
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "catalogs": ("citry_ui_i18n",),
        }
    },
)
engine.register_library(citry_ui)
"""


def _typescript_path() -> list[str]:
    """Return a PATH that holds the repository's `tsc` and Node.js, or skip without them."""
    try:
        tsc = Path(find_typescript_compiler(_REPOSITORY_NODE_PROJECT)[0])
    except TypeScriptUnavailableError:
        pytest.skip("repo-local tsc is unavailable; install the Node workspace for this integration check")
    node = shutil.which("node")
    assert node is not None
    # The package-manager shim for `tsc` is a shell script that needs the system tools.
    return [str(tsc.parent), str(Path(node).parent), "/usr/bin", "/bin"]


def test_citry_ui_components_have_no_typescript_or_ty_findings(tmp_path):
    path_entries = _typescript_path()
    (tmp_path / "app_without_i18n.py").write_text(_APP_WITHOUT_I18N, encoding="utf-8")
    (tmp_path / "app_with_i18n.py").write_text(_APP_WITH_I18N, encoding="utf-8")
    python_path = os.pathsep.join(filter(None, (str(tmp_path), os.environ.get("PYTHONPATH"))))
    environment = {**os.environ, "PATH": os.pathsep.join(path_entries), "PYTHONPATH": python_path, "NO_COLOR": "1"}
    environment.pop("FORCE_COLOR", None)

    # Each check spends most of its time in TypeScript and ty, so both apps are checked at the same time.
    runs = {
        module: subprocess.Popen(
            # Citry UI is registered as a library here, so `--include-libraries` asks for its findings.
            [
                sys.executable,
                "-m",
                "citry",
                "--app",
                f"{module}:engine",
                "check",
                "--types",
                "--include-libraries",
                "--format",
                "json",
            ],
            cwd=_CITRY_UI_PACKAGE,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for module in ("app_without_i18n", "app_with_i18n")
    }
    # Wait for both before asserting, and stop both if one hangs, so no check outlives the test.
    try:
        results = {module: (process.communicate(timeout=600), process.returncode) for module, process in runs.items()}
    finally:
        for process in runs.values():
            if process.poll() is None:
                process.kill()
                process.wait()
    reports: dict[str, str] = {}
    for module, ((stdout, stderr), returncode) in results.items():
        # Status 2 means TypeScript or ty did not run. Status 1 is expected,
        # because the report also carries Citry's own template findings,
        # which this test does not cover yet (GitHub issue #149).
        assert returncode in {0, 1}, f"{module}: {stderr}"
        payload = json.loads(stdout)
        assert payload["mode"] == "registry", f"{module}: {payload.get('app_failure')}"
        assert not any("--types did not run" in note for note in payload["notes"]), payload["notes"]
        # TypeScript reports `citry.typescript.*` and ty reports `citry.python.*`.
        typed = [
            item for item in payload["findings"] if item["code"].startswith(("citry.typescript.", "citry.python."))
        ]
        reports[module] = "\n".join(f"- {item['origin']}: {item['code']} {item['message']}" for item in typed)

    assert reports == {"app_without_i18n": "", "app_with_i18n": ""}, "\n".join(
        f"TypeScript or ty findings in Citry UI ({module}):\n{report}" for module, report in reports.items() if report
    )


# A page that passes the heading level and the week start both as template
# text and as numbers, plus one value of each kind that names no level or day.
_FILLS = '<c-fill name="title">T</c-fill><c-fill name="default">B</c-fill>'
_DIGIT_INPUTS_PAGE = f"""<c-CDisclosure heading_level="2">{_FILLS}</c-CDisclosure>
<c-CDisclosure c-heading_level="2">{_FILLS}</c-CDisclosure>
<c-CDisclosure heading_level="7">{_FILLS}</c-CDisclosure>
<c-CAccordion heading_level="4"><c-CAccordionItem value="a">{_FILLS}</c-CAccordionItem></c-CAccordion>
<c-CAccordion heading_level="1"><c-CAccordionItem value="a">{_FILLS}</c-CAccordionItem></c-CAccordion>
<c-CCalendar first_day_of_week="1" />
<c-CCalendar c-first_day_of_week="7" />
<c-CCalendar first_day_of_week="8" />
<c-CDatePicker first_day_of_week="1" />
<c-CDateRange first_day_of_week="0" />
"""
# The lines of `_DIGIT_INPUTS_PAGE` that pass a value outside the list.
_INVALID_LINES = (2, 4, 7, 9)

_DIGIT_INPUTS_APP = """import citry_ui
from pathlib import Path
from citry import Citry, Component

engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
engine.register_library(citry_ui)


class Page(Component):
    citry = engine
    template_file = "page.html"
"""


def test_the_editor_accepts_digit_inputs_as_text_or_numbers(tmp_path):
    # A template attribute always passes text, so the editor must accept
    # `heading_level="2"` as readily as `c-heading_level="2"`, and still
    # flag a value that names no heading level or weekday.
    (tmp_path / "app.py").write_text(_DIGIT_INPUTS_APP, encoding="utf-8")
    template_file = tmp_path / "page.html"
    template_file.write_text(_DIGIT_INPUTS_PAGE, encoding="utf-8")
    # Registering every Citry UI component can take longer than the editor's
    # startup limit on a busy machine. A timeout would load the project
    # without its registry, and the assertion below would fail.
    project = load_project(tmp_path, "app:engine", timeout=300)
    assert project.status.mode == "registry", project.status.message
    document = DocumentState(template_file.as_uri(), "citry-html", _DIGIT_INPUTS_PAGE, 1)
    document.update(_DIGIT_INPUTS_PAGE, 1, project)

    async def check() -> tuple[types.Diagnostic, ...]:
        analyzer = TyAnalyzer(tmp_path)
        try:
            return await semantic_diagnostics(analyzer, document, project, {document.uri: document})
        finally:
            await analyzer.close()

    # A plain `asyncio.run` keeps this package's tests free of an async
    # pytest plugin.
    findings = asyncio.run(check())

    lines = _DIGIT_INPUTS_PAGE.splitlines()
    flagged = [(item.code, lines[item.range.start.line]) for item in findings]
    assert flagged == [("citry.python.invalid-assignment", lines[index]) for index in _INVALID_LINES]
