"""Template errors stop clean-copy qualification before tests or server startup."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from examples._internal.catalog import CATALOG_PATH, load_catalog
from examples._internal.qualify import project_environment, qualify_project

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("project_id", ["starter-standalone", "starter-django"])
def test_failed_template_check_stops_qualification(tmp_path: Path, project_id: str) -> None:
    project = next(project for project in load_catalog() if project.id == project_id)
    environment = project_environment()
    original = environment.copy()
    with patch("examples._internal.qualify.run_checked", side_effect=RuntimeError("template error")) as run:
        with pytest.raises(RuntimeError, match="template error"):
            qualify_project(project, tmp_path, environment, None, 1)
    assert run.call_count == 1
    assert run.call_args.args[:2] == (project.check, tmp_path)
    checked_environment = run.call_args.args[2]
    assert checked_environment["UV_NO_SYNC"] == "1"
    if project.host == "django":
        assert checked_environment["DJANGO_SETTINGS_MODULE"] == "config.settings"
    assert environment == original


def test_template_checks_precede_tests_and_build(tmp_path: Path) -> None:
    project = next(project for project in load_catalog() if project.id == "starter-standalone")
    with patch("examples._internal.qualify.run_checked") as run:
        qualify_project(project, tmp_path, project_environment(), None, 1)
    assert [call.args[0] for call in run.call_args_list] == [project.check, project.test, project.build]


@pytest.mark.parametrize("replacement", ["", "check = []", 'check = "uv run citry check"'])
def test_catalog_rejects_missing_or_malformed_check(tmp_path: Path, replacement: str) -> None:
    source = CATALOG_PATH.read_text(encoding="utf-8")
    command = next(line for line in source.splitlines() if line.startswith("check = "))
    catalog = tmp_path / "catalog.toml"
    catalog.write_text(source.replace(command, replacement, 1), encoding="utf-8")
    with pytest.raises(ValueError, match="check"):
        load_catalog(catalog)
