"""Template errors stop clean-copy qualification before tests or server startup."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from examples._internal.catalog import CATALOG_PATH, EXAMPLES_ROOT, load_catalog
from examples._internal.qualify import LINKS_NOT_CHECKED_CODES, project_environment, qualify_project

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


# The catalog `citry check` takes its diagnostic codes from.
CATALOG_JSON = EXAMPLES_ROOT.parent / "packages" / "protocol" / "diagnostics" / "v1" / "catalog.json"

# What `citry check` prints when it loaded a Citry instance that no web
# framework integration mounted.
LINKS_NOT_CHECKED_NOTE = (
    "citry check: note: Links such as '/' were not checked, because no web framework "
    "integration told Citry which paths your app serves. Point --app at the module that "
    "calls citry.contrib.flask.mount(), citry.contrib.fastapi.mount(), or "
    'citry.contrib.django.urlpatterns(), or set rule_unknown_url to "ignore". '
    "[citry.check.url-checker-missing]\n"
)


@pytest.mark.parametrize("project_id", ["starter-django", "starter-fastapi", "starter-flask"])
def test_framework_check_that_skips_links_stops_qualification(tmp_path: Path, project_id: str) -> None:
    project = next(project for project in load_catalog() if project.id == project_id)
    with patch("examples._internal.qualify.run_checked", return_value=LINKS_NOT_CHECKED_NOTE) as run:
        with pytest.raises(RuntimeError, match="did not check links"):
            qualify_project(project, tmp_path, project_environment(), None, 1)
    # Only the check ran, so the note stopped qualification before the tests.
    assert [call.args[0] for call in run.call_args_list] == [project.check]


def test_bare_asgi_check_may_leave_links_unchecked(tmp_path: Path) -> None:
    # A hand-written ASGI router has no integration that knows its paths, so
    # the note is expected and qualification carries on.
    project = next(project for project in load_catalog() if project.id == "starter-asgi")
    with (
        patch("examples._internal.qualify.run_checked", return_value=LINKS_NOT_CHECKED_NOTE) as run,
        patch("examples._internal.qualify.running_server"),
    ):
        qualify_project(project, tmp_path, project_environment(), None, 1)
    assert [call.args[0] for call in run.call_args_list] == [project.check, project.test]


def test_link_note_codes_exist_in_the_diagnostic_catalog() -> None:
    # qualify.py cannot import citry here, so it names the note codes by hand;
    # this keeps them in step with the catalog that `citry check` prints from.
    catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    codes = {entry["code"] for entry in catalog["diagnostics"]}
    assert set(LINKS_NOT_CHECKED_CODES) <= codes
