"""
The repository's pytest settings make a deprecation warning fail the test.

The `filterwarnings` setting in the root pyproject.toml turns every
deprecation warning into an error, so a test run cannot carry one unnoticed.
The few warnings that Citry cannot fix are listed there as named exceptions.
"""

from __future__ import annotations

import importlib
import re
import warnings
from pathlib import Path
from typing import Any

import pytest
import tomllib
import yaml  # type: ignore[import-untyped]

import citry
from citry._caller_warnings import warn_at_caller

_REPO_ROOT = Path(__file__).resolve().parents[4]
_EXAMPLES_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "py--examples--tests.yml"


def _pytest_settings() -> dict[str, Any]:
    document = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return document["tool"]["pytest"]["ini_options"]


def test_only_named_exceptions_follow_the_deprecation_errors():
    filters = _pytest_settings()["filterwarnings"]
    # A later entry wins over an earlier one, so the two errors come first
    # and everything after them is an exception.
    assert filters[:2] == ["error::DeprecationWarning", "error::PendingDeprecationWarning"]
    for entry in filters[2:]:
        # pytest splits an entry on colons into action, message, class,
        # module and an optional line number.
        fields = entry.split(":")
        assert len(fields) >= 4, entry
        action, message, category, module = fields[:4]
        # An empty message, class or module would ignore far more than the
        # one warning the entry's comment names, which is how a blanket
        # `ignore::DeprecationWarning` would slip in.
        assert action == "ignore", entry
        assert message, entry
        assert category, entry
        assert module, entry


def test_the_async_fixture_loop_scope_is_set():
    # pytest-asyncio warns when it is unset, and the warning is a deprecation
    # that the `filterwarnings` entries in pyproject.toml turn into an error
    # before any test runs.
    assert _pytest_settings()["asyncio_default_fixture_loop_scope"] == "function"


# This test has no `filterwarnings` mark of its own, so it passes only when
# the `filterwarnings` setting in the root pyproject.toml is in force for this
# run. Run it without `-W`, which overrides the setting.
def test_deprecation_warnings_fail_a_test_run():
    with pytest.raises(citry.CitryDeprecationWarning, match="old feature"):
        warn_at_caller("old feature", citry.CitryDeprecationWarning)
    with pytest.raises(DeprecationWarning, match="old library function"):
        warnings.warn("old library function", DeprecationWarning, stacklevel=1)
    with pytest.raises(PendingDeprecationWarning, match="soon deprecated"):
        warnings.warn("soon deprecated", PendingDeprecationWarning, stacklevel=1)


def test_example_workflow_flags_name_a_warning_class_that_exists():
    # When the module that a `-W` flag names cannot be imported, pytest only
    # warns and runs without the rule, so a misspelled module in the workflow
    # would turn the rule off with no failure to show for it. A misspelled
    # class name stops pytest, but this test also names the right class.
    workflow = yaml.safe_load(_EXAMPLES_WORKFLOW.read_text(encoding="utf-8"))
    flags = [
        step["env"]["PYTEST_ADDOPTS"]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "PYTEST_ADDOPTS" in step.get("env", {})
    ]
    assert flags
    for flag in flags:
        found = re.fullmatch(r"-W error::(?P<module>[\w.]+)\.(?P<name>\w+)", flag)
        assert found, flag
        category = getattr(importlib.import_module(found["module"]), found["name"])
        assert issubclass(category, DeprecationWarning)
