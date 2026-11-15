"""The release check of citry-lsp and citry pairs picks the right releases and skips a pair only when allowed."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest
from scripts import lsp_citry_pairs

if TYPE_CHECKING:
    from pathlib import Path

_FILE = [{"yanked": False}]


@pytest.mark.parametrize(
    ("releases", "major", "expected"),
    [
        pytest.param({"0.9.0": _FILE, "1.0.0": _FILE, "1.2.0": _FILE}, 1, "1.0.0", id="oldest-of-the-major"),
        pytest.param({"0.9.0": _FILE, "1.0.0rc1": _FILE, "1.1.0": _FILE}, 1, "1.1.0", id="skips-pre-release"),
        pytest.param({"1.0.0": [{"yanked": True}], "1.0.1": _FILE}, 1, "1.0.1", id="skips-yanked"),
        pytest.param({"1.0.0": [], "1.0.1": _FILE}, 1, "1.0.1", id="skips-empty-release"),
        pytest.param({"0.9.0": _FILE, "2.0.0": _FILE}, 1, None, id="none-in-the-major"),
        pytest.param({"1.0.0": _FILE, "2.1.0": _FILE, "2.0.3": _FILE}, 2, "2.0.3", id="later-major"),
        pytest.param({"1.10.0": _FILE, "1.9.0": _FILE}, 1, "1.9.0", id="numeric-order"),
    ],
)
def test_oldest_in_major(releases: dict[str, list[dict[str, bool]]], major: int, expected: str | None) -> None:
    assert lsp_citry_pairs.oldest_in_major(releases, major) == expected


def test_a_0x_candidate_skips_without_asking_pypi(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(_package: str) -> None:
        raise AssertionError

    monkeypatch.setattr(lsp_citry_pairs, "published_releases", fail)

    assert lsp_citry_pairs.pick_other_release("citry-lsp", "0.9.0", None) is None
    assert "no pair is promised" in capsys.readouterr().out


def test_no_release_of_the_other_package_skips_with_a_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(lsp_citry_pairs, "published_releases", lambda _package: {"0.4.0": _FILE})

    assert lsp_citry_pairs.pick_other_release("citry-lsp", "1.0.0", None) is None
    assert "PyPI has no citry-lsp 1.x release yet" in capsys.readouterr().out


def test_the_oldest_release_of_the_major_is_paired(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lsp_citry_pairs, "published_releases", lambda _package: {"1.0.0": _FILE, "1.3.0": _FILE})

    assert lsp_citry_pairs.pick_other_release("citry", "1.4.0", None) == "1.0.0"


def test_a_chosen_release_wins() -> None:
    assert lsp_citry_pairs.pick_other_release("citry", "0.1.0", "0.9.0") == "0.9.0"


def test_wheel_version_reads_the_file_name(tmp_path: Path) -> None:
    assert lsp_citry_pairs.wheel_version(tmp_path / "citry_lsp-1.2.3-py3-none-any.whl") == "1.2.3"
    with pytest.raises(SystemExit):
        lsp_citry_pairs.wheel_version(tmp_path / "citry_lsp-1.2.3.tar.gz")


@pytest.mark.parametrize(
    ("has_tag", "shallow", "expected_fetch"),
    [
        pytest.param(True, "false", None, id="tag-present-no-fetch"),
        pytest.param(False, "false", ["git", "fetch", "--quiet", "origin"], id="full-clone-keeps-history"),
        pytest.param(False, "true", ["git", "fetch", "--quiet", "--depth", "1", "origin"], id="shallow-clone"),
    ],
)
def test_tag_checkout_never_makes_a_full_clone_shallow(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, has_tag: bool, shallow: str, expected_fetch: list[str] | None
) -> None:
    commands: list[list[str]] = []

    def probe(command: list[str]) -> subprocess.CompletedProcess[str]:
        if "--verify" in command:
            return subprocess.CompletedProcess(command, 0 if has_tag else 1, "", "")
        return subprocess.CompletedProcess(command, 0, shallow + "\n", "")

    monkeypatch.setattr(lsp_citry_pairs, "probe", probe)
    monkeypatch.setattr(lsp_citry_pairs, "run", lambda command, **_options: commands.append(command))

    lsp_citry_pairs.tag_checkout("citry-lsp", "1.0.0", tmp_path / "checkout")

    fetches = [command[:-1] for command in commands if command[1] == "fetch"]
    assert fetches == ([] if expected_fetch is None else [expected_fetch])
    assert commands[-1][:2] == ["git", "worktree"]
