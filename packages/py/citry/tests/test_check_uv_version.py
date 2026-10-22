"""The repository gate stops before its phases when the uv on PATH is older than the repository's uv pin."""

import json
import subprocess
from pathlib import Path

import pytest
from scripts import check


@pytest.fixture
def uv_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    # A synthetic pin keeps the test independent of the current release value.
    pin_file = tmp_path / "pyodide-build.json"
    pin_file.write_text(json.dumps({"uv": "1.4.2"}), encoding="utf-8")
    monkeypatch.setattr(check, "_UV_PIN_FILE", pin_file)
    return "1.4.2"


def _uv_reports(monkeypatch: pytest.MonkeyPatch, output: str | None) -> None:
    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        assert command == ["uv", "--version"]
        # None stands for a machine without uv on PATH.
        if output is None:
            raise FileNotFoundError(2, "No such file or directory", "uv")
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

    monkeypatch.setattr(check.subprocess, "run", fake_run)


# A `+build` suffix names the same release as the pin.
@pytest.mark.parametrize("version", ["1.4.2", "1.4.2+3", "1.4.10", "2.0.0"])
def test_the_pinned_or_a_newer_uv_passes(uv_pin: str, monkeypatch: pytest.MonkeyPatch, version: str) -> None:
    del uv_pin
    # 1.4.10 is newer than 1.4.2, which a text comparison would get wrong.
    _uv_reports(monkeypatch, f"uv {version} (abc123 2026-10-21 aarch64-apple-darwin)\n")
    assert check._uv_version_result() is None


def test_an_older_uv_stops_the_agent_gate_before_any_phase(
    uv_pin: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _uv_reports(monkeypatch, "uv 1.3.9 (Homebrew 2026-07-28 aarch64-apple-darwin)\n")

    def no_phases(*_: object, **__: object) -> list[tuple[str, list[str]]]:
        raise AssertionError("no phase may run with an older uv")

    monkeypatch.setattr(check, "_phases", no_phases)
    assert check.main(["--reporter", "agent"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "FAILED"
    [phase] = report["phases"]
    assert phase["name"] == "uv version"
    assert phase["command"] == "uv --version"
    assert phase["exitCode"] == 1
    assert phase["details"].startswith(f"uv 1.3.9 found; this repository needs uv {uv_pin} or later")


def test_a_missing_uv_stops_the_streaming_gate(
    uv_pin: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _uv_reports(monkeypatch, None)
    monkeypatch.setattr(check, "_phases", lambda *_, **__: pytest.fail("no phase may run without uv"))
    assert check.main([]) == 1
    stderr = capsys.readouterr().err
    assert "uv was not found on PATH" in stderr
    assert f"needs uv {uv_pin} or later" in stderr


@pytest.mark.parametrize("version", ["1.4.2rc1", "1.4.2-alpha.1", "nightly"])
def test_a_pre_release_or_unreadable_uv_fails(uv_pin: str, monkeypatch: pytest.MonkeyPatch, version: str) -> None:
    # A pre-release of the pinned version comes before it, so it may lack what the pin added.
    _uv_reports(monkeypatch, f"uv {version}\n")
    result = check._uv_version_result()
    assert result is not None
    assert f"needs uv {uv_pin} or later" in str(result["details"])


@pytest.mark.parametrize("config", [{}, {"uv": "latest"}])
def test_an_unreadable_pin_is_reported_instead_of_raised(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, config: dict[str, str]
) -> None:
    pin_file = tmp_path / "pyodide-build.json"
    pin_file.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(check, "_UV_PIN_FILE", pin_file)
    monkeypatch.setattr(check, "_REPO_ROOT", tmp_path)
    result = check._uv_version_result()
    assert result is not None
    assert "must record the uv version" in str(result["details"])
