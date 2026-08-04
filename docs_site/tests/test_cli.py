"""
Tests for the ``versions-check`` and ``build-all`` command-line commands.

``versions-check`` is exercised through ``cli.main`` (the real argparse path)
against small synthetic ``versions/`` trees under ``tmp_path``. ``build-all`` is
driven through its handler with an injected ``repo_root`` pointing at a throwaway
git repo built here, so the tag selection, the ``citry@`` prefix stripping, and
the worktree ``build_one`` run end-to-end without touching the real tags or
rebuilding anything heavy.
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from docs_site._internal import cli
from docs_site._internal._vendor.mike_versions import Versions
from docs_site._internal.assemble import AssembleOutcome
from docs_site._internal.build import BuildOutcome
from docs_site._internal.project import load_docs_project
from docs_site._internal.versioning import write_build_info, write_manifest

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_PAGE = "<html><body>hi</body></html>"


def test_build_check_fails_when_search_index_fails(
    monkeypatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setattr(
        cli,
        "build_site",
        lambda **_kwargs: BuildOutcome(
            output_dir=tmp_path,
            search_ok=False,
            search_message="pagefind failed",
        ),
    )

    assert cli._run_build_check(strict=True) == 1
    assert "Search index failed: pagefind failed" in capsys.readouterr().out


def test_build_check_uses_one_project_for_guards_and_build(monkeypatch, tmp_path: Path) -> None:
    project = load_docs_project()
    loads: list[object] = []
    contexts: list[object] = []
    builds: list[object] = []

    def fake_load(_config):
        loads.append(object())
        return project

    def fake_guards(context, **_kwargs):
        contexts.append(context)
        return [], True

    def fake_build(**kwargs):
        builds.append(kwargs["project"])
        return BuildOutcome(output_dir=tmp_path, search_ok=True)

    monkeypatch.setattr("docs_site._internal.project.load_docs_project", fake_load)
    monkeypatch.setattr("docs_site._internal.guards.run_guards", fake_guards)
    monkeypatch.setattr(cli, "build_site", fake_build)

    assert cli._run_build_check(strict=True) == 0
    assert len(loads) == 1
    assert builds == [project]
    assert [context.project for context in contexts] == [project, project]


def test_assemble_command_fails_for_partial_build(
    monkeypatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "docs_site._internal.assemble.assemble_site",
        lambda **_kwargs: AssembleOutcome(
            output_dir=tmp_path,
            failed=1,
            errors=[("broken.md", "RuntimeError: broken")],
            search_ok=True,
        ),
    )

    assert cli._run_assemble(None, build=True) == 1
    output = capsys.readouterr().out
    assert "1 page(s) failed" in output
    assert "broken.md: RuntimeError: broken" in output


def test_assemble_command_fails_without_search_index(
    monkeypatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "docs_site._internal.assemble.assemble_site",
        lambda **_kwargs: AssembleOutcome(
            output_dir=tmp_path,
            search_ok=False,
            search_message="pagefind failed",
        ),
    )

    assert cli._run_assemble(None, build=True) == 1
    assert "Search index failed: pagefind failed" in capsys.readouterr().out


def _make_version(root: Path, version: str, *, pages: tuple[str, ...] = ("index.html",)) -> Path:
    """A built version dir under ``root``: a build stamp plus the given pages."""
    vdir = root / version
    write_build_info(vdir, version=version, source_sha="deadbeef")
    for rel in pages:
        page = vdir / rel
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(_PAGE, encoding="utf-8")
    return vdir


def _write_versions(root: Path, entries: list[tuple[str, tuple[str, ...]]]) -> None:
    """Write a ``versions.json`` manifest from ``(version, aliases)`` entries."""
    versions = Versions()
    for version, aliases in entries:
        versions.add(version, aliases=list(aliases), update_aliases=True)
    write_manifest(root, versions)


def _init_git_repo(path: Path, tags: list[str]) -> None:
    """Create a throwaway git repo with one commit and the given tags (no docs builder)."""
    path.mkdir(parents=True, exist_ok=True)

    def run(*args: str) -> None:
        subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True)  # noqa: S607

    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")
    run("config", "commit.gpgsign", "false")
    (path / "README.md").write_text("hi\n", encoding="utf-8")
    run("add", "-A")
    run("commit", "-q", "-m", "init")
    for tag in tags:
        run("tag", tag)


# --- versions-check -------------------------------------------------------------


def test_versions_check_passes_on_clean_tree(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _write_versions(root, [("0.1.0", ())])

    rc = cli.main(["versions-check", "--versions-dir", str(root)])

    assert rc == 0
    assert "All guards passed" in capsys.readouterr().out


def test_versions_check_flags_orphan_and_exits_nonzero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # The manifest lists a version with no dir on disk (the shape of an unreleased
    # version left in the manifest); the command must report it and exit 1.
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _write_versions(root, [("0.1.0", ()), ("0.9.0", ())])

    rc = cli.main(["versions-check", "--versions-dir", str(root)])

    out = capsys.readouterr().out
    assert rc == 1
    assert "0.9.0" in out
    assert "does not exist" in out


def test_versions_check_missing_tree_is_a_pass(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # No committed version tree yet (pre-bootstrap) is a valid, passing state.
    root = tmp_path / "versions"  # never created

    rc = cli.main(["versions-check", "--versions-dir", str(root)])

    assert rc == 0
    assert "nothing to check" in capsys.readouterr().out


def test_versions_check_strict_flag_still_passes_clean_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # --strict is accepted and, since the version guards emit no warnings, a clean
    # tree still passes under it.
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _write_versions(root, [("0.1.0", ())])

    rc = cli.main(["versions-check", "--strict", "--versions-dir", str(root)])

    assert rc == 0
    assert "All guards passed" in capsys.readouterr().out


# --- build-all ------------------------------------------------------------------


def test_build_all_dry_run_reports_up_to_date_and_stale(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = tmp_path / "repo"
    # citry-core@1.3.0 is a sibling package's tag: it must be excluded, not read as
    # docs version 1.3.0, so only two versions are considered.
    _init_git_repo(repo, ["citry@0.1.0", "citry@0.2.0", "citry-core@1.3.0"])
    cfg = tmp_path / "docs_versions.yml"
    cfg.write_text('versions:\n  oldest: "0.0.1"\n', encoding="utf-8")  # default pattern, low floor
    versions_root = tmp_path / "versions"
    # Stamp 0.2.0 as already built from its tag's commit -> up-to-date; 0.1.0 has
    # no dir -> stale.
    sha = cli._tag_sha(repo, "citry@0.2.0")
    write_build_info(versions_root / "0.2.0", version="0.2.0", source_sha=sha)

    rc = cli._run_build_all(versions_root, cfg, dry_run=True, repo_root=repo)

    out = capsys.readouterr().out
    assert rc == 0
    assert "Would consider 2 version(s)" in out
    lines = [line for line in out.splitlines() if line.strip().startswith(("0.1.0", "0.2.0"))]
    assert any(line.startswith("  0.2.0") and "up-to-date" in line for line in lines)
    assert any(line.startswith("  0.1.0") and "BUILD" in line for line in lines)
    assert out.index("0.2.0") < out.index("0.1.0")  # newest-first


def test_build_one_skips_checkout_without_builder(tmp_path: Path) -> None:
    # The commit has no docs_site/ builder, so build_one skips the tag rather than
    # trying to build it. This exercises the real worktree add / remove path.
    repo = tmp_path / "repo"
    _init_git_repo(repo, ["citry@0.1.0"])

    build_one = cli._make_build_one(repo, {"0.1.0": "citry@0.1.0"})
    result = build_one("0.1.0", "0.1.0", tmp_path / "versions" / "0.1.0")

    assert result == "skipped_no_builder"


def test_builder_probe_accepts_flat_and_internal_layouts(tmp_path: Path) -> None:
    flat = tmp_path / "flat"
    internal = tmp_path / "internal"
    for docs_dir in (flat, internal):
        docs_dir.mkdir()
        (docs_dir / "__main__.py").touch()
    (flat / "versioning.py").touch()
    (internal / "_internal").mkdir()
    (internal / "_internal" / "versioning.py").touch()

    assert cli._has_docs_builder(flat)
    assert cli._has_docs_builder(internal)


def test_build_all_in_non_git_dir_fails_cleanly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # A directory that is not a git checkout: enumerating tags fails, and build-all
    # turns that into a clean message and a nonzero exit rather than a traceback.
    not_a_repo = tmp_path / "empty"
    not_a_repo.mkdir()

    rc = cli._run_build_all(tmp_path / "versions", None, dry_run=True, repo_root=not_a_repo)

    assert rc == 1
    assert "git checkout" in capsys.readouterr().out


def test_serve_targets_the_internal_asgi_app(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {}

    def fake_run(app: str, **kwargs) -> None:
        called["app"] = app
        called["kwargs"] = kwargs

    monkeypatch.setattr("uvicorn.run", fake_run)

    assert cli._run_serve("127.0.0.1", 8123, reload=False) == 0
    assert called == {
        "app": "docs_site._internal.serve:create_local_app",
        "kwargs": {"host": "127.0.0.1", "port": 8123, "reload": False, "factory": True},
    }
