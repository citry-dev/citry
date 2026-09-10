"""Exercise immutable package tags against a local Git remote."""

import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from scripts import release_tag


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        [shutil.which("git") or "/usr/bin/git", *args], cwd=repo, text=True, capture_output=True, check=True
    ).stdout.strip()


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "init", "-b", "main", str(repo))
    git(repo, "config", "user.name", "Release tests")
    git(repo, "config", "user.email", "release@example.test")
    manifest = repo / "packages/py/citry/pyproject.toml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('[project]\nversion = "1.2.3"\n')
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Initial package")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "origin", "main")
    monkeypatch.setenv("RELEASE_APP_TOKEN", "synthetic-test-token")
    return repo, git(repo, "rev-parse", "HEAD")


def test_create_and_retry(repository: tuple[Path, str]) -> None:
    repo, commit = repository
    assert not release_tag.validate(repo, "citry", commit, "citry@1.2.3")
    release_tag.create(repo, "citry", commit, "citry@1.2.3")
    first = git(repo, "rev-parse", "citry@1.2.3")
    release_tag.create(repo, "citry", commit, "citry@1.2.3")
    assert git(repo, "cat-file", "-t", first) == "tag"
    assert git(repo, "rev-parse", "citry@1.2.3") == first


@pytest.mark.parametrize(
    ("package", "sha", "tag"),
    [
        ("unknown", None, "citry@1.2.3"),
        ("citry", "abc", "citry@1.2.3"),
        ("citry", None, "citry@1.2.4"),
        ("citry", None, "refs/heads/main"),
    ],
)
def test_invalid_identity(repository: tuple[Path, str], package: str, sha: str | None, tag: str) -> None:
    repo, commit = repository
    with pytest.raises(release_tag.ReleaseTagError):
        release_tag.validate(repo, package, sha or commit, tag)


def test_unmerged_commit(repository: tuple[Path, str]) -> None:
    repo, _ = repository
    git(repo, "commit", "--allow-empty", "-m", "Unpublished work")
    with pytest.raises(release_tag.ReleaseTagError, match="merge-base"):
        release_tag.validate(repo, "citry", git(repo, "rev-parse", "HEAD"), "citry@1.2.3")


def test_lightweight_tag(repository: tuple[Path, str]) -> None:
    repo, commit = repository
    git(repo, "tag", "citry@1.2.3", commit)
    git(repo, "push", "origin", "refs/tags/citry@1.2.3")
    with pytest.raises(release_tag.ReleaseTagError, match="not annotated"):
        release_tag.validate(repo, "citry", commit, "citry@1.2.3")


def test_wrong_tag_target(repository: tuple[Path, str]) -> None:
    repo, commit = repository
    git(repo, "commit", "--allow-empty", "-m", "Later work")
    git(repo, "tag", "-a", "citry@1.2.3", "-m", "Wrong target")
    git(repo, "push", "origin", "refs/tags/citry@1.2.3")
    with pytest.raises(release_tag.ReleaseTagError, match="different commit"):
        release_tag.validate(repo, "citry", commit, "citry@1.2.3")


def test_remote_error_is_not_absence(repository: tuple[Path, str]) -> None:
    repo, commit = repository
    original = release_tag._git

    def failed_query(path: Path, *args: str, authenticated: bool = False) -> subprocess.CompletedProcess[str]:
        if args[0] == "ls-remote":
            return subprocess.CompletedProcess(args, 128, "", "network failure")
        return original(path, *args, authenticated=authenticated)

    with (
        patch.object(release_tag, "_git", side_effect=failed_query),
        pytest.raises(
            release_tag.ReleaseTagError,
            match="query the remote",
        ),
    ):
        release_tag.create(repo, "citry", commit, "citry@1.2.3")
    assert not git(repo, "tag", "--list")


def test_concurrent_identical_creation(repository: tuple[Path, str]) -> None:
    repo, commit = repository
    original = release_tag._git

    def race(path: Path, *args: str, authenticated: bool = False) -> subprocess.CompletedProcess[str]:
        result = original(path, *args, authenticated=authenticated)
        if args[0] == "push":
            assert result.returncode == 0
            return subprocess.CompletedProcess(args, 1, "", "concurrent writer won")
        return result

    with patch.object(release_tag, "_git", side_effect=race):
        release_tag.create(repo, "citry", commit, "citry@1.2.3")
    assert release_tag.validate(repo, "citry", commit, "citry@1.2.3")


def test_failed_push_is_not_success(repository: tuple[Path, str]) -> None:
    repo, commit = repository
    original = release_tag._git

    def failed_push(path: Path, *args: str, authenticated: bool = False) -> subprocess.CompletedProcess[str]:
        if args[0] == "push":
            return subprocess.CompletedProcess(args, 1, "", "permission denied")
        return original(path, *args, authenticated=authenticated)

    with (
        patch.object(release_tag, "_git", side_effect=failed_push),
        pytest.raises(
            release_tag.ReleaseTagError,
            match="push failed",
        ),
    ):
        release_tag.create(repo, "citry", commit, "citry@1.2.3")


@pytest.mark.parametrize("package", sorted(release_tag.PACKAGE_BY_KEY))
def test_package_manifest_mapping(repository: tuple[Path, str], package: str) -> None:
    repo, _ = repository
    spec = release_tag.PACKAGE_BY_KEY[package]
    manifest = repo / spec.manifest
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text('{"version": "2.3.4"}' if spec.manifest_kind == "json" else '[project]\nversion = "2.3.4"\n')
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Selected package")
    git(repo, "push", "origin", "main")
    commit = git(repo, "rev-parse", "HEAD")
    release_tag.create(repo, package, commit, f"{spec.tag_prefix}2.3.4")
    assert release_tag.validate(repo, package, commit, f"{spec.tag_prefix}2.3.4")


@pytest.mark.parametrize("version", ['"01.2.3"', '"1.2"', "123", '"1.2.3/injected"'])
def test_invalid_manifest_version(repository: tuple[Path, str], version: str) -> None:
    repo, _ = repository
    (repo / "packages/py/citry/pyproject.toml").write_text(f"[project]\nversion = {version}\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Invalid manifest")
    git(repo, "push", "origin", "main")
    with pytest.raises(release_tag.ReleaseTagError, match="version is invalid"):
        release_tag.validate(repo, "citry", git(repo, "rev-parse", "HEAD"), "citry@1.2.3")


def test_missing_credential(repository: tuple[Path, str], monkeypatch: pytest.MonkeyPatch) -> None:
    repo, commit = repository
    monkeypatch.delenv("RELEASE_APP_TOKEN")
    with pytest.raises(release_tag.ReleaseTagError, match="TOKEN is missing"):
        release_tag.create(repo, "citry", commit, "citry@1.2.3")
    assert not release_tag.validate(repo, "citry", commit, "citry@1.2.3")


def test_remote_fetch_failure(repository: tuple[Path, str]) -> None:
    repo, commit = repository
    release_tag.create(repo, "citry", commit, "citry@1.2.3")
    original = release_tag._git

    def failed_fetch(path: Path, *args: str, authenticated: bool = False) -> subprocess.CompletedProcess[str]:
        if args[0] == "fetch" and args[-1].startswith("refs/tags/"):
            return subprocess.CompletedProcess(args, 128, "", "network failure")
        return original(path, *args, authenticated=authenticated)

    with (
        patch.object(release_tag, "_git", side_effect=failed_fetch),
        pytest.raises(
            release_tag.ReleaseTagError,
            match="git fetch failed",
        ),
    ):
        release_tag.validate(repo, "citry", commit, "citry@1.2.3")


def test_tag_object_sha_is_not_a_release_commit(repository: tuple[Path, str]) -> None:
    repo, commit = repository
    git(repo, "tag", "-a", "source-alias", commit, "-m", "Source alias")
    tag_object = git(repo, "rev-parse", "source-alias")
    with pytest.raises(release_tag.ReleaseTagError, match="must name a commit object"):
        release_tag.create(repo, "citry", tag_object, "citry@1.2.3")
    assert not git(repo, "ls-remote", "--tags", "origin", "refs/tags/citry@1.2.3")
    assert not git(repo, "tag", "--list", "citry@1.2.3")


@pytest.mark.parametrize("remote", [False, True])
def test_annotation_internal_name_must_match(repository: tuple[Path, str], remote: bool) -> None:
    repo, commit = repository
    git(repo, "tag", "-a", "different-release", commit, "-m", "Different release")
    git(repo, "update-ref", "refs/tags/citry@1.2.3", git(repo, "rev-parse", "different-release"))
    if remote:
        git(repo, "push", "origin", "refs/tags/citry@1.2.3")
    with pytest.raises(release_tag.ReleaseTagError, match="different internal identity"):
        release_tag.create(repo, "citry", commit, "citry@1.2.3")
    if not remote:
        assert not git(repo, "ls-remote", "--tags", "origin", "refs/tags/citry@1.2.3")
