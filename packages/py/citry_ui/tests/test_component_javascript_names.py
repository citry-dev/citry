"""Citry UI's `$component` definitions pass the `citry check` component JavaScript rules."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import citry_ui

# `citry check` reports the components whose source lives in the current
# directory, so the check runs from the installed package itself.
_CITRY_UI_PACKAGE = Path(citry_ui.__file__).resolve().parent

_APP = """import citry_ui
from citry import Citry

engine = Citry(autodiscover=False)
engine.register_library(citry_ui)
"""


def test_citry_ui_component_javascript_has_no_check_findings(tmp_path):
    # Each component script runs in its own scope, so a helper defined in one
    # component's script is not visible from another's. A call to it throws a
    # ReferenceError only when that branch runs in the browser. The
    # `citry.component-js.*` rules catch that, and unknown members and
    # undeclared emits, without a browser. They read the `$component`
    # definition only, not code before it or Dependencies scripts.
    (tmp_path / "citry_ui_names_app.py").write_text(_APP, encoding="utf-8")
    python_path = os.pathsep.join(filter(None, (str(tmp_path), os.environ.get("PYTHONPATH"))))
    environment = {**os.environ, "PYTHONPATH": python_path, "NO_COLOR": "1"}
    environment.pop("FORCE_COLOR", None)

    # A separate process keeps this registration of Citry UI out of the test session.
    result = subprocess.run(
        [sys.executable, "-m", "citry", "--app", "citry_ui_names_app:engine", "check", "--format", "json"],
        cwd=_CITRY_UI_PACKAGE,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    # Status 1 is expected, because the report also carries template findings
    # that this test does not cover (GitHub issue #149).
    assert result.returncode in {0, 1}, result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "registry", payload.get("app_failure")
    component_js = [
        f"- {item['origin']}: {item['code']} {item['message']}"
        for item in payload["findings"]
        if item["code"].startswith("citry.component-js.")
    ]
    assert component_js == [], "Component JavaScript findings in Citry UI:\n" + "\n".join(component_js)
