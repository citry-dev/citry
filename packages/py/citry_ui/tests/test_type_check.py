"""Citry UI's component JavaScript and Vue templates have no TypeScript errors under `citry check --types`."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import citry_ui
from citry_lsp.typescript import TypeScriptUnavailableError, find_typescript_compiler

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


def test_citry_ui_component_javascript_has_no_typescript_errors(tmp_path):
    path_entries = _typescript_path()
    (tmp_path / "app_without_i18n.py").write_text(_APP_WITHOUT_I18N, encoding="utf-8")
    (tmp_path / "app_with_i18n.py").write_text(_APP_WITH_I18N, encoding="utf-8")
    python_path = os.pathsep.join(filter(None, (str(tmp_path), os.environ.get("PYTHONPATH"))))
    environment = {**os.environ, "PATH": os.pathsep.join(path_entries), "PYTHONPATH": python_path, "NO_COLOR": "1"}
    environment.pop("FORCE_COLOR", None)

    # Each check spends most of its time in TypeScript and ty, so both apps are checked at the same time.
    runs = {
        module: subprocess.Popen(
            [sys.executable, "-m", "citry", "--app", f"{module}:engine", "check", "--types", "--format", "json"],
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
        # because the report also carries Citry's own template findings and
        # ty's findings in Citry UI's templates, which this test does not
        # cover yet.
        assert returncode in {0, 1}, f"{module}: {stderr}"
        payload = json.loads(stdout)
        assert payload["mode"] == "registry", f"{module}: {payload.get('app_failure')}"
        assert not any("--types did not run" in note for note in payload["notes"]), payload["notes"]
        typed = [item for item in payload["findings"] if item["code"].startswith("citry.typescript.")]
        reports[module] = "\n".join(f"- {item['origin']}: {item['code']} {item['message']}" for item in typed)

    assert reports == {"app_without_i18n": "", "app_with_i18n": ""}, "\n".join(
        f"TypeScript errors in Citry UI ({module}):\n{report}" for module, report in reports.items() if report
    )
