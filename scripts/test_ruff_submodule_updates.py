# ruff: noqa: S101
"""Tests for the Ruff submodule update checker."""

from pathlib import Path
from subprocess import TimeoutExpired

import pytest
import ruff_submodule_updates as checker
from ruff_submodule_updates import (
    CheckError,
    _parse_comparison,
    changed_files,
    format_report,
    monitored_paths,
)


def test_monitored_paths_come_from_ruff_workspace_dependencies(tmp_path: Path) -> None:
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text(
        """
[workspace.dependencies]
ruff_python_ast = {
    path = "third_party/rust/ruff/crates/ruff_python_ast"
}
ruff_text_size = {
    path = "third_party/rust/ruff/crates/ruff_text_size"
}
other = { path = "crates/other" }
""",
        encoding="utf-8",
    )

    assert monitored_paths(cargo_toml) == (
        "crates/ruff_python_ast",
        "crates/ruff_text_size",
    )


def test_monitored_paths_rejects_a_missing_configuration(tmp_path: Path) -> None:
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text("[workspace.dependencies]\n", encoding="utf-8")

    with pytest.raises(CheckError, match="no Ruff crate paths"):
        monitored_paths(cargo_toml)


@pytest.mark.parametrize(
    ("github_status", "pin_relation"),
    [
        ("ahead", "behind"),
        ("identical", "equal"),
        ("behind", "ahead"),
    ],
)
def test_comparison_maps_release_direction_to_pin_relation(
    github_status: str,
    pin_relation: str,
) -> None:
    assert _parse_comparison({"status": github_status}) == pin_relation


def test_comparison_rejects_diverged_histories() -> None:
    with pytest.raises(CheckError, match="diverged"):
        _parse_comparison({"status": "diverged"})


@pytest.mark.parametrize(
    ("relation", "release_sha"),
    [("equal", "current"), ("ahead", "")],
)
def test_current_or_newer_pin_needs_no_git_diff(
    monkeypatch: pytest.MonkeyPatch,
    relation: checker.PinRelation,
    release_sha: str,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str) -> str:
        calls.append(args)
        return "current"

    monkeypatch.setattr(checker, "_git", fake_git)
    monkeypatch.setattr(
        checker,
        "fetch_pin_relation",
        lambda _current_sha, _tag: relation,
    )

    assert changed_files("0.16.0", ("crates/ruff_python_ast",)) == (
        "current",
        release_sha,
        relation,
        [],
    )
    assert calls == [("rev-parse", "HEAD^{commit}")]


def test_older_pin_diffs_only_monitored_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str) -> str:
        calls.append(args)
        if args[:2] == ("rev-parse", "HEAD^{commit}"):
            return "current"
        if args[:2] == ("rev-parse", "FETCH_HEAD^{commit}"):
            return "release"
        if args[0] == "diff":
            return "crates/ruff_python_ast/src/node.rs"
        return ""

    monkeypatch.setattr(checker, "_git", fake_git)
    monkeypatch.setattr(
        checker,
        "fetch_pin_relation",
        lambda _current_sha, _tag: "behind",
    )

    result = changed_files("0.16.0", ("crates/ruff_python_ast",))

    assert result == (
        "current",
        "release",
        "behind",
        ["crates/ruff_python_ast/src/node.rs"],
    )
    assert calls[-1] == (
        "diff",
        "--name-only",
        "current",
        "release",
        "--",
        "crates/ruff_python_ast",
    )


def test_git_timeout_becomes_checker_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(checker.shutil, "which", lambda _executable: "/usr/bin/git")

    def time_out(*_args: object, **_kwargs: object) -> None:
        raise TimeoutExpired("git", 120)

    monkeypatch.setattr(checker.subprocess, "run", time_out)

    with pytest.raises(CheckError, match="could not complete"):
        checker._git("fetch", "origin")


@pytest.mark.parametrize(
    ("result", "exit_code"),
    [
        (("current", "release", "behind", ["crates/ruff_cache/src/lib.rs"]), 10),
        (("current", "release", "behind", []), 0),
        (("current", "current", "equal", []), 0),
        (("current", "", "ahead", []), 0),
    ],
)
def test_command_exit_codes_for_check_results(
    monkeypatch: pytest.MonkeyPatch,
    result: tuple[str, str, checker.PinRelation, list[str]],
    exit_code: int,
) -> None:
    monkeypatch.setattr(checker, "fetch_latest_tag", lambda: "0.16.0")
    monkeypatch.setattr(
        checker,
        "monitored_paths",
        lambda: ("crates/ruff_cache",),
    )
    monkeypatch.setattr(
        checker,
        "changed_files",
        lambda _tag, _paths: result,
    )

    assert checker.cmd_check() == exit_code


def test_command_returns_error_status_for_expected_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail() -> str:
        raise CheckError("network unavailable")

    monkeypatch.setattr(checker, "fetch_latest_tag", fail)

    assert checker.cmd_check() == 2


def test_command_returns_distinct_status_for_unexpected_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def crash() -> str:
        raise RuntimeError("unexpected")

    monkeypatch.setattr(checker, "fetch_latest_tag", crash)

    assert checker.cmd_check() == 3


def test_report_limits_the_changed_file_list() -> None:
    files = [f"crates/ruff_python_ast/src/file_{index}.rs" for index in range(105)]

    report = format_report("0.16.0", "current", "release", files)

    assert "file_0.rs" in report
    assert "file_99.rs" in report
    assert "file_100.rs" not in report
    assert "and 5 more" in report
