"""Tests for app-worker environment-file isolation and validation."""

from __future__ import annotations

import os

import pytest

from citry_lsp.environment import (
    EnvironmentFileError,
    _merge_environment,
    resolve_environment_file,
    worker_environment,
)


def test_environment_file_resolves_against_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    assert resolve_environment_file(workspace, ".config/citry.env") == workspace / ".config" / "citry.env"


def test_environment_file_overlays_inherited_values_without_mutating_process(tmp_path, monkeypatch):
    environment_file = tmp_path / ".env"
    environment_file.write_text(
        'CITRY_ENV_BASE=file\nCITRY_ENV_EXPANDED=${CITRY_ENV_BASE}-value\nCITRY_ENV_QUOTED="two words"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CITRY_ENV_BASE", "inherited")
    monkeypatch.delenv("CITRY_ENV_EXPANDED", raising=False)
    monkeypatch.delenv("CITRY_ENV_QUOTED", raising=False)

    environment = worker_environment(environment_file)

    assert environment is not None
    assert environment["CITRY_ENV_BASE"] == "file"
    assert environment["CITRY_ENV_EXPANDED"] == "file-value"
    assert environment["CITRY_ENV_QUOTED"] == "two words"
    assert os.environ["CITRY_ENV_BASE"] == "inherited"
    assert "CITRY_ENV_EXPANDED" not in os.environ
    assert "CITRY_ENV_QUOTED" not in os.environ


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("CITRY_ENV_MISSING\n", "has no value"),
        ("invalid-name=value\n", "is not portable"),
        ('CITRY_ENV_BROKEN="unterminated\n', "invalid dotenv syntax"),
        (b"CITRY_ENV_VALUE=\xff\n", "not valid UTF-8"),
    ],
)
def test_environment_file_rejects_invalid_content_without_leaking_values(tmp_path, source, message):
    environment_file = tmp_path / ".env"
    if isinstance(source, bytes):
        environment_file.write_bytes(source)
    else:
        environment_file.write_text(source, encoding="utf-8")

    with pytest.raises(EnvironmentFileError, match=message):
        worker_environment(environment_file)


def test_environment_file_must_be_a_readable_regular_file(tmp_path):
    with pytest.raises(EnvironmentFileError, match="does not exist"):
        worker_environment(tmp_path / "missing.env")
    with pytest.raises(EnvironmentFileError, match="regular file"):
        worker_environment(tmp_path)


def test_environment_parse_failure_does_not_include_file_values(tmp_path):
    environment_file = tmp_path / ".env"
    environment_file.write_text(
        "CITRY_ENV_PRIVATE=do-not-report-this-value\nBROKEN: do-not-report-this-line\n",
        encoding="utf-8",
    )

    with pytest.raises(EnvironmentFileError) as error:
        worker_environment(environment_file)

    assert "do-not-report" not in str(error.value)


def test_windows_environment_overlay_collapses_case_insensitive_keys():
    assert _merge_environment(
        {"Path": "inherited", "KEEP": "yes"},
        {"PATH": "configured"},
        case_insensitive=True,
    ) == {"PATH": "configured", "KEEP": "yes"}


def test_unconfigured_worker_environment_inherits_without_copying():
    assert worker_environment(None) is None
