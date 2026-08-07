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
from pathlib import Path

import pytest

from docs_site._internal import cli
from docs_site._internal._vendor.mike_versions import Versions
from docs_site._internal.assemble import AssembleOutcome
from docs_site._internal.build import BuildOutcome
from docs_site._internal.project import load_docs_project
from docs_site._internal.versioning import BUILD_INFO_NAME, write_build_info, write_manifest

_PAGE = "<html><body>hi</body></html>"


def test_build_cli_forwards_detached_version_flag(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_run(output, **kwargs):
        captured["output"] = output
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(cli, "_run_build", fake_run)

    assert (
        cli.main(
            [
                "build",
                "--docs-version",
                "1.0.0",
                "--no-update-versions-manifest",
                "-o",
                str(tmp_path / "snapshot"),
            ]
        )
        == 0
    )
    assert captured["docs_version"] == "1.0.0"
    assert captured["update_versions_manifest"] is False


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
    # The source guards run before the build and, under `strict`, a warning from
    # any page fails them. That returns early and never reaches the search-index
    # branch this test is about, so the guards are stubbed to pass and the test
    # covers only its own subject.
    monkeypatch.setattr("docs_site._internal.guards.run_guards", lambda *_args, **_kwargs: ([], True))

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


@pytest.mark.parametrize(
    "tags",
    [
        "0.3.0\ncitry@0.3.0\n",
        "citry@v0.3.0\ncitry@0.3.0\n",
    ],
)
def test_git_tag_ref_map_rejects_normalized_collisions(tmp_path: Path, monkeypatch, tags: str) -> None:
    monkeypatch.setattr(
        cli,
        "_git",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [],
            0,
            stdout=tags,
            stderr="",
        ),
    )

    with pytest.raises(ValueError, match=r"both produce docs version '0\.3\.0'"):
        cli._git_tag_ref_map(tmp_path)


def test_build_tag_uses_exact_ref_and_registers_snapshot(
    tmp_path: Path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    versions = tmp_path / "versions"
    captured: dict[str, object] = {}
    monkeypatch.setattr(cli, "_git_tag_ref_map", lambda _repo: {"1.2.3": "citry@1.2.3"})

    def fake_factory(repo, ref_map):
        captured["repo"] = repo
        captured["ref_map"] = ref_map

        def build_one(tag, version, version_dir):
            captured["build"] = (tag, version, version_dir)
            version_dir.mkdir(parents=True)
            (version_dir / BUILD_INFO_NAME).write_text("{}", encoding="utf-8")
            (version_dir / "index.html").write_text(_PAGE, encoding="utf-8")
            return "built"

        return build_one

    monkeypatch.setattr(cli, "_make_build_one", fake_factory)

    assert cli._run_build_tag("citry@1.2.3", versions, repo_root=tmp_path) == 0
    assert captured == {
        "repo": tmp_path,
        "ref_map": {"1.2.3": "citry@1.2.3"},
        "build": ("1.2.3", "1.2.3", versions / "1.2.3"),
    }
    manifest = (versions / "versions.json").read_text(encoding="utf-8")
    assert '"version": "1.2.3"' in manifest
    assert '"latest"' in manifest
    assert (versions / "latest" / "index.html").is_file()
    assert "Built citry@1.2.3 as docs version 1.2.3" in capsys.readouterr().out


def test_build_one_skips_checkout_without_builder(tmp_path: Path) -> None:
    # The commit has no docs_site/ builder, so build_one skips the tag rather than
    # trying to build it. This exercises the real worktree add / remove path.
    repo = tmp_path / "repo"
    _init_git_repo(repo, ["citry@0.1.0"])

    build_one = cli._make_build_one(repo, {"0.1.0": "citry@0.1.0"})
    result = build_one("0.1.0", "0.1.0", tmp_path / "versions" / "0.1.0")

    assert result == "skipped_no_builder"


def test_build_one_preserves_snapshot_when_old_builder_fails(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    version_dir = tmp_path / "versions" / "1.0.0"
    version_dir.mkdir(parents=True)
    sentinel = version_dir / "keep.txt"
    sentinel.write_text("known good", encoding="utf-8")

    def fake_git(_repo, *args, **_kwargs):
        if args[:3] == ("worktree", "add", "--detach"):
            worktree = Path(args[3])
            docs = worktree / "docs_site"
            docs.mkdir(parents=True)
            (docs / "__main__.py").touch()
            (docs / "versioning.py").touch()
            (docs / "cli.py").write_text("# old builder\n", encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    def fake_run(command, **_kwargs):
        staged = Path(command[command.index("-o") + 1])
        staged.mkdir(parents=True, exist_ok=True)
        (staged / "partial.html").write_text("partial", encoding="utf-8")
        (staged / BUILD_INFO_NAME).write_text("{}", encoding="utf-8")
        return subprocess.CompletedProcess(command, 1, stdout="old builder failed", stderr="")

    monkeypatch.setattr(cli, "_git", fake_git)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    build_one = cli._make_build_one(repo, {"v1.0.0": "deadbeef"})

    with pytest.raises(RuntimeError, match="old builder failed"):
        build_one("v1.0.0", "1.0.0", version_dir)

    assert sentinel.read_text(encoding="utf-8") == "known good"
    assert not (version_dir / "partial.html").exists()
    assert {path.name for path in version_dir.parent.iterdir()} == {"1.0.0"}


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
