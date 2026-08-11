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
    current_stable_tag,
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


def test_current_stable_tag_uses_the_newest_exact_release(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str) -> str:
        calls.append(args)
        return "nightly\n0.16.1\n0.15.22"

    monkeypatch.setattr(checker, "_git", fake_git)

    assert current_stable_tag("current") == "0.16.1"
    assert calls == [("tag", "--points-at", "current", "--sort=-version:refname")]


def test_current_stable_tag_declines_non_release_tags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checker, "_git", lambda *_args: "nightly\n0.17.0-beta.1")

    assert current_stable_tag("current") is None


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
        if args[0] == "tag":
            return "0.15.22"
        return "current"

    monkeypatch.setattr(checker, "_git", fake_git)
    monkeypatch.setattr(
        checker,
        "fetch_pin_relation",
        lambda _current_sha, _tag: relation,
    )

    assert changed_files("0.16.0", ("crates/ruff_python_ast",)) == (
        "current",
        "0.15.22",
        release_sha,
        relation,
        [],
    )
    assert calls == [
        ("rev-parse", "HEAD^{commit}"),
        ("tag", "--points-at", "current", "--sort=-version:refname"),
    ]


def test_older_pin_diffs_only_monitored_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str) -> str:
        calls.append(args)
        if args[:2] == ("rev-parse", "HEAD^{commit}"):
            return "current"
        if args[0] == "tag":
            return "0.15.22"
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
        "0.15.22",
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
        (("current", "0.15.22", "release", "behind", ["crates/ruff_cache/src/lib.rs"]), 10),
        (("current", "0.15.22", "release", "behind", []), 0),
        (("current", "0.16.0", "current", "equal", []), 0),
        (("current", None, "", "ahead", []), 0),
    ],
)
def test_command_exit_codes_for_check_results(
    monkeypatch: pytest.MonkeyPatch,
    result: tuple[str, str | None, str, checker.PinRelation, list[str]],
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

    report = format_report("0.16.0", "0.15.22", "current", "release", files)

    assert "file_0.rs" in report
    assert "file_99.rs" in report
    assert "file_100.rs" not in report
    assert "and 5 more" in report


def test_report_links_current_and_latest_release_revisions() -> None:
    report = format_report(
        "0.16.2",
        "0.16.1",
        "80790b348b5188e7fc253665540f442c6ec7dd05",
        "5b48a040974781ba90b47c8df628f8fd9b6c95dd",
        ["crates/ruff_python_ast/src/node.rs"],
    )

    assert "| Citry checkout |" in report
    assert "https://github.com/astral-sh/ruff/releases/tag/0.16.1" in report
    assert "https://github.com/astral-sh/ruff/commit/80790b348b5188e7fc253665540f442c6ec7dd05" in report
    assert "https://github.com/astral-sh/ruff/releases/tag/0.16.2" in report
    assert "https://github.com/astral-sh/ruff/commit/5b48a040974781ba90b47c8df628f8fd9b6c95dd" in report
    assert (
        "https://github.com/astral-sh/ruff/compare/"
        "80790b348b5188e7fc253665540f442c6ec7dd05..."
        "5b48a040974781ba90b47c8df628f8fd9b6c95dd"
    ) in report


def test_report_does_not_guess_a_current_release_tag() -> None:
    report = format_report(
        "0.16.2",
        None,
        "current",
        "release",
        ["crates/ruff_python_ast/src/node.rs"],
    )

    assert "Not on an exact stable release tag" in report
