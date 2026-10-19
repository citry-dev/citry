"""The benchmark runners refuse a debug build of the native extension."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from benchmarks import native_build

if TYPE_CHECKING:
    from pathlib import Path


def _use_build(monkeypatch: pytest.MonkeyPatch, profile: str, tmp_path: Path) -> None:
    # Stand in for the extension so the test does not depend on how the
    # checkout's own extension was built.
    monkeypatch.setattr(native_build, "_rust", SimpleNamespace(BUILD_PROFILE=profile, __file__=str(tmp_path)))


def test_release_build_passes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(native_build.ALLOW_DEBUG_ENV, raising=False)
    _use_build(monkeypatch, "release", tmp_path)
    native_build.require_release_build()


def test_debug_build_exits_with_the_rebuild_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(native_build.ALLOW_DEBUG_ENV, raising=False)
    _use_build(monkeypatch, "debug", tmp_path)
    with pytest.raises(SystemExit) as raised:
        native_build.require_release_build()
    message = str(raised.value)
    assert native_build.REBUILD_COMMAND in message
    assert native_build.ALLOW_DEBUG_ENV in message


def test_debug_build_runs_when_allowed_and_says_so_on_stderr(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(native_build.ALLOW_DEBUG_ENV, "1")
    _use_build(monkeypatch, "debug", tmp_path)
    native_build.require_release_build()
    captured = capsys.readouterr()
    # Runners that print a JSON report keep stdout clean.
    assert captured.out == ""
    assert "debug build" in captured.err
