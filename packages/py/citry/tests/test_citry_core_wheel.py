from __future__ import annotations

import hashlib
import json
import posixpath
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

import pytest
import tomllib
from scripts import citry_core_wheel

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

_WHEEL_NAME = "citry_core-1.0.0-cp311-abi3-x.whl"
_CACHE_KEY = "citry-core-wheel-v1-Linux-X64-ubuntu24-abc"


@pytest.mark.parametrize(
    "path",
    [
        "Cargo.toml",
        "Cargo.lock",
        "rust-toolchain.toml",
        ".cargo/config.toml",
        "crates/x/src/lib.rs",
        "crates/x/Cargo.toml",
        "crates/x/build.rs",
        "third_party/rust/ruff",
        "third_party/rust/vize_atelier_core/src/lib.rs",
        "packages/py/citry_core/LICENSE-vize",
        "packages/py/citry_core/README.md",
        "packages/py/citry_core/pyproject.toml",
        "packages/py/citry_core/citry_core/__init__.py",
    ],
)
def test_native_wheel_input_selects_files_that_reach_the_wheel(path: str) -> None:
    assert citry_core_wheel._is_native_wheel_input(PurePosixPath(path))


@pytest.mark.parametrize(
    "path",
    [
        "crates/x/tests/test_x.rs",
        "crates/x/benches/bench.rs",
        "crates/x/README.md",
        "crates/x/AGENTS.md",
        "crates/x/docs/agent/INDEX.md",
        "packages/py/citry_core/tests/test_template_parser.py",
        "packages/py/citry_core/CHANGELOG.md",
        "packages/py/citry/citry/__init__.py",
        "docs/codebase.md",
    ],
)
def test_native_wheel_input_skips_files_that_stay_out_of_the_wheel(path: str) -> None:
    assert not citry_core_wheel._is_native_wheel_input(PurePosixPath(path))


class _Repo:
    """A throwaway git repo whose index feeds the digest, as the real checkout's does."""

    def __init__(self, root: Path) -> None:
        git = shutil.which("git")
        assert git is not None
        self.root = root
        self._git = git
        self._run("init", "-q")
        self.write("pyproject.toml", '[tool.uv]\nbuild-constraint-dependencies = ["maturin==1.0.0"]\n')
        self.write("Cargo.toml", "[workspace]\n")

    def _run(self, *arguments: str) -> None:
        subprocess.run([self._git, *arguments], cwd=self.root, check=True)

    def write(self, relative: str, text: str) -> None:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        # The digest reads the index, so a file counts only once it is staged.
        self._run("add", relative)

    def digest(self, **keywords: Any) -> str:
        return citry_core_wheel.native_source_digest(repo_root=self.root, **keywords)


@pytest.fixture
def repo(tmp_path: Path) -> _Repo:
    result = _Repo(tmp_path)
    result.write("crates/demo/src/lib.rs", "pub fn one() {}\n")
    result.write("third_party/rust/vize_atelier_core/src/lib.rs", "one\n")
    result.write("crates/demo/tests/test_demo.rs", "one\n")
    return result


# One file per `_NATIVE_PATHS` entry, so every selected folder or file is shown
# to change the digest. Cutting an entry from the selection fails its case, and
# adding an entry without a sample fails the coverage check below.
_NATIVE_SAMPLES = {
    ".cargo": ".cargo/config.toml",
    "Cargo.lock": "Cargo.lock",
    "Cargo.toml": "Cargo.toml",
    "crates": "crates/demo/src/lib.rs",
    "packages/py/citry_core": "packages/py/citry_core/pyproject.toml",
    "rust-toolchain.toml": "rust-toolchain.toml",
    "third_party/rust": "third_party/rust/vize_atelier_core/src/lib.rs",
}


def test_every_native_path_has_a_digest_sample() -> None:
    assert set(_NATIVE_SAMPLES) == set(citry_core_wheel._NATIVE_PATHS)
    for sample in _NATIVE_SAMPLES.values():
        assert citry_core_wheel._is_native_wheel_input(PurePosixPath(sample))


@pytest.mark.parametrize("relative", sorted(_NATIVE_SAMPLES.values()))
def test_native_source_digest_changes_with_each_native_path(repo: _Repo, relative: str) -> None:
    # Edit a file that is already tracked, so the change shows only if the
    # folder or file is selected, not merely because a new entry appeared.
    repo.write(relative, "one\n")
    before = repo.digest(extra_paths=())

    repo.write(relative, "two\n")

    assert repo.digest(extra_paths=()) != before


def test_native_source_digest_changes_with_the_python_half_of_the_package(repo: _Repo) -> None:
    relative = "packages/py/citry_core/citry_core/__init__.py"
    repo.write(relative, "one\n")
    before = repo.digest(extra_paths=())

    repo.write(relative, "two\n")

    assert repo.digest(extra_paths=()) != before


def test_native_source_digest_changes_with_a_build_constraint(repo: _Repo) -> None:
    before = repo.digest(extra_paths=())

    repo.write("pyproject.toml", '[tool.uv]\nbuild-constraint-dependencies = ["maturin==2.0.0"]\n')

    assert repo.digest(extra_paths=()) != before


@pytest.mark.parametrize("relative", citry_core_wheel._RECIPE_PATHS)
def test_native_source_digest_changes_with_each_default_recipe_path(repo: _Repo, relative: str) -> None:
    repo.write(relative, "one\n")
    # The default `extra_paths` are the real recipe, so dropping one fails here.
    before = repo.digest()

    repo.write(relative, "two\n")

    assert repo.digest() != before


def test_native_source_digest_changes_with_the_ruff_submodule_commit(repo: _Repo) -> None:
    def pin(commit: str) -> None:
        repo._run("update-index", "--add", "--cacheinfo", f"160000,{commit},third_party/rust/ruff")

    pin("1" * 40)
    before = repo.digest(extra_paths=())

    pin("2" * 40)

    assert repo.digest(extra_paths=()) != before


def test_native_source_digest_changes_with_the_cache_version(repo: _Repo) -> None:
    assert repo.digest(version="v1", extra_paths=()) != repo.digest(version="v2", extra_paths=())


def test_native_source_digest_ignores_files_and_settings_outside_the_wheel(repo: _Repo) -> None:
    before = repo.digest(extra_paths=())

    repo.write("crates/demo/tests/test_demo.rs", "two\n")
    repo.write("crates/demo/README.md", "docs\n")
    repo.write(
        "pyproject.toml",
        '[tool.uv]\nbuild-constraint-dependencies = ["maturin==1.0.0"]\n\n[tool.ruff]\nline-length = 119\n',
    )

    assert repo.digest(extra_paths=()) == before


def test_native_source_digest_refuses_a_repo_with_no_native_inputs(tmp_path: Path) -> None:
    git = shutil.which("git")
    assert git is not None
    subprocess.run([git, "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="native cache inputs were not found"):
        citry_core_wheel.native_source_digest(repo_root=tmp_path, extra_paths=())


_DEPENDENCY_TABLES = ("dependencies", "dev-dependencies", "build-dependencies")


def _path_dependencies(manifest: dict[str, Any], directory: str) -> set[str]:
    """Return the repo-relative folder of every `path` dependency a Cargo manifest names."""
    tables: list[dict[str, Any]] = []
    workspace = manifest.get("workspace", {})
    tables.append(workspace.get("dependencies", {}))
    # `[patch.<registry>]` tables swap a published crate for a local folder.
    tables.extend(manifest.get("patch", {}).values())
    for holder in (manifest, *manifest.get("target", {}).values()):
        tables.extend(holder.get(name, {}) for name in _DEPENDENCY_TABLES)
    return {
        posixpath.normpath(posixpath.join(directory, specification["path"]))
        for table in tables
        for specification in table.values()
        if isinstance(specification, dict) and "path" in specification
    }


def _tracked_files(repo_root: Path, pathspec: str) -> list[PurePosixPath]:
    """
    Return the tracked entries `pathspec` names, from the index.

    A folder inside a submodule has no entries of its own, so the submodule's
    own entry (the Ruff checkout shows up as one) stands in for it.
    """
    git = shutil.which("git")
    assert git is not None

    def listing(spec: str) -> list[tuple[str, str, str]]:
        result = subprocess.run(
            [git, "ls-files", "--stage", "-z", "--", spec],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return [record.partition("\t") for record in result.stdout.split("\0") if record]

    entries = [PurePosixPath(path) for _metadata, _separator, path in listing(pathspec)]
    if entries:
        return entries
    # The root ("." in `parents`) would list the whole index, so stop before it.
    for parent in PurePosixPath(pathspec).parents:
        if parent == PurePosixPath("."):
            break
        submodules = [
            PurePosixPath(path)
            for metadata, _separator, path in listing(parent.as_posix())
            if metadata.startswith("160000 ") and path == parent.as_posix()
        ]
        if submodules:
            return submodules
    return []


@pytest.mark.skipif(shutil.which("git") is None, reason="git is unavailable")
def test_the_native_selection_covers_every_path_the_real_wheel_build_reads() -> None:
    # The wheel is built from the real checkout, so a new path dependency or
    # license file outside the selection would let a stale wheel be reused.
    root = citry_core_wheel._REPO_ROOT
    root_manifest = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))
    members = list(root_manifest["workspace"]["members"])
    crates = {*members, *_path_dependencies(root_manifest, ".")}
    for member in members:
        member_manifest = tomllib.loads((root / member / "Cargo.toml").read_text(encoding="utf-8"))
        crates |= _path_dependencies(member_manifest, member)

    package = "packages/py/citry_core"
    pyproject = tomllib.loads((root / package / "pyproject.toml").read_text(encoding="utf-8"))
    maturin_manifest = posixpath.normpath(posixpath.join(package, pyproject["tool"]["maturin"]["manifest-path"]))
    crates.add(posixpath.dirname(maturin_manifest))
    # Each metadata file is a tracked file the wheel packs, not a folder.
    files = {f"{package}/pyproject.toml", f"{package}/{pyproject['project']['readme']}"}
    files |= {f"{package}/{pattern}" for pattern in pyproject["project"]["license-files"]}

    # A parser that finds nothing would pass the checks below, so require what is known to exist.
    assert members
    assert any(crate.startswith("third_party/rust/ruff/") for crate in crates)
    assert any(crate.startswith("third_party/rust/vize_") for crate in crates)

    problems = []
    required = [(f"{crate}/Cargo.toml", crate) for crate in sorted(crates)] + [(file, file) for file in sorted(files)]
    for target, source in required:
        under_native_path = any(
            source == native or source.startswith(f"{native}/") for native in citry_core_wheel._NATIVE_PATHS
        )
        accepted = any(citry_core_wheel._is_native_wheel_input(entry) for entry in _tracked_files(root, target))
        if not (under_native_path and accepted):
            problems.append(f"{source} (under a native path: {under_native_path}, input accepted: {accepted})")

    assert not problems, "the wheel build reads these paths but the cache key does not cover them:\n" + "\n".join(
        problems
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git is unavailable")
def test_the_recipe_paths_name_tracked_files_that_build_the_wheel() -> None:
    # The digest skips a recipe path that Git does not track, so a rename
    # would silently drop the file from the key.
    assert set(citry_core_wheel._RECIPE_PATHS) >= {
        ".gitattributes",
        ".github/actions/citry-core-wheel/action.yml",
        ".github/actions/install-rust/action.yml",
        "scripts/citry_core_wheel.py",
    }
    for relative in citry_core_wheel._RECIPE_PATHS:
        assert _tracked_files(citry_core_wheel._REPO_ROOT, relative) == [PurePosixPath(relative)]


def _fake_uv_version(monkeypatch: pytest.MonkeyPatch, uv_version: list[str]) -> None:
    # `cache_key` only asks uv for its version, so a fake keeps the test off a real uv.
    def fake_run(command: list[str], **_keywords: Any) -> subprocess.CompletedProcess[str]:
        assert command[1:] == ["--version"]
        return subprocess.CompletedProcess(command, 0, stdout=f"{uv_version[0]}\n")

    monkeypatch.setattr(citry_core_wheel, "_executable", lambda name: name)
    monkeypatch.setattr(citry_core_wheel.subprocess, "run", fake_run)


def test_cache_key_is_scoped_by_runner_image_uv_and_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_digest = ["source-one"]
    uv_version = ["uv 1.0.0"]
    monkeypatch.setattr(citry_core_wheel, "native_source_digest", lambda **_keywords: source_digest[0])
    _fake_uv_version(monkeypatch, uv_version)

    def key(runner_os: str = "Linux", arch: str = "X64", image: str = "ubuntu24") -> str:
        return citry_core_wheel.cache_key(runner_os, arch, image, repo_root=tmp_path)["cache_key"]

    base = key()
    assert base.startswith("citry-core-wheel-v1-Linux-X64-ubuntu24-")
    assert key() == base
    assert key(runner_os="macOS") != base
    assert key(arch="ARM64") != base
    assert key(image="ubuntu22") != base

    uv_version[0] = "uv 1.0.1"
    assert key() != base
    uv_version[0] = "uv 1.0.0"

    source_digest[0] = "source-two"
    assert key() != base
    assert citry_core_wheel.cache_key("Linux", "X64", "ubuntu24", repo_root=tmp_path)["source_digest"] == "source-two"


def test_cache_key_does_not_depend_on_the_running_python(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(citry_core_wheel, "native_source_digest", lambda **_keywords: "source")
    _fake_uv_version(monkeypatch, ["uv 1.0.0"])

    monkeypatch.setattr(sys, "executable", "/python-3.11/bin/python")
    first = citry_core_wheel.cache_key("Linux", "X64", "ubuntu24", repo_root=tmp_path)
    monkeypatch.setattr(sys, "executable", "/python-3.14/bin/python")
    second = citry_core_wheel.cache_key("Linux", "X64", "ubuntu24", repo_root=tmp_path)

    assert first == second


def test_cache_key_makes_the_runner_prefix_safe_for_a_cache_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(citry_core_wheel, "native_source_digest", lambda **_keywords: "source")
    _fake_uv_version(monkeypatch, ["uv 1.0.0"])

    key = citry_core_wheel.cache_key("Linux", "X64", "ubuntu 24/one", repo_root=tmp_path)["cache_key"]

    assert key.startswith("citry-core-wheel-v1-Linux-X64-ubuntu-24-one-")


def _recorded(wheel_dir: Path, *, cache_key: str = _CACHE_KEY, payload: bytes = b"wheel bytes") -> Path:
    wheel_dir.mkdir(parents=True, exist_ok=True)
    (wheel_dir / _WHEEL_NAME).write_bytes(payload)
    citry_core_wheel.record_wheel(wheel_dir, cache_key)
    return wheel_dir


def test_record_wheel_ties_the_name_bytes_and_key_together(tmp_path: Path) -> None:
    wheel_dir = _recorded(tmp_path / "wheels")

    manifest = json.loads((wheel_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest == {
        "cache_key": _CACHE_KEY,
        "sha256": hashlib.sha256(b"wheel bytes").hexdigest(),
        "wheel": _WHEEL_NAME,
    }


@pytest.mark.parametrize("expected_cache_key", [_CACHE_KEY, None])
def test_verified_wheel_accepts_a_recorded_wheel(tmp_path: Path, expected_cache_key: str | None) -> None:
    wheel_dir = _recorded(tmp_path / "wheels")

    assert citry_core_wheel.verified_wheel(wheel_dir, expected_cache_key) == wheel_dir / _WHEEL_NAME


def _change_bytes(wheel_dir: Path) -> None:
    (wheel_dir / _WHEEL_NAME).write_bytes(b"other bytes")


def _rename_wheel(wheel_dir: Path) -> None:
    (wheel_dir / _WHEEL_NAME).rename(wheel_dir / "citry_core-9.9.9-cp311-abi3-x.whl")


def _remove_manifest(wheel_dir: Path) -> None:
    (wheel_dir / "manifest.json").unlink()


def _make_manifest_a_list(wheel_dir: Path) -> None:
    (wheel_dir / "manifest.json").write_text("[]", encoding="utf-8")


def _break_manifest_json(wheel_dir: Path) -> None:
    (wheel_dir / "manifest.json").write_text("{not json", encoding="utf-8")


def _add_second_wheel(wheel_dir: Path) -> None:
    (wheel_dir / "citry_core-2.0.0-cp311-abi3-x.whl").write_bytes(b"wheel bytes")


@pytest.mark.parametrize(
    ("damage", "match"),
    [
        (_change_bytes, "does not match its manifest"),
        (_rename_wheel, "does not match its manifest"),
        (_remove_manifest, "no valid manifest"),
        (_make_manifest_a_list, "does not match its manifest"),
        (_break_manifest_json, "no valid manifest"),
        (_add_second_wheel, "expected exactly one citry-core wheel"),
    ],
)
def test_verified_wheel_refuses_a_damaged_folder(
    tmp_path: Path,
    damage: Callable[[Path], None],
    match: str,
) -> None:
    wheel_dir = _recorded(tmp_path / "wheels")
    damage(wheel_dir)

    # Both modes refuse, so a job that skips the key check is no easier to fool.
    for expected_cache_key in (_CACHE_KEY, None):
        with pytest.raises(RuntimeError, match=match):
            citry_core_wheel.verified_wheel(wheel_dir, expected_cache_key)


def test_verified_wheel_refuses_a_wheel_recorded_under_another_key(tmp_path: Path) -> None:
    wheel_dir = _recorded(tmp_path / "wheels", cache_key="citry-core-wheel-v1-other")

    with pytest.raises(RuntimeError, match="does not match its manifest or cache key"):
        citry_core_wheel.verified_wheel(wheel_dir, _CACHE_KEY)


def test_verified_wheel_refuses_a_manifest_without_a_key_even_when_no_key_is_expected(tmp_path: Path) -> None:
    wheel_dir = _recorded(tmp_path / "wheels")
    manifest = json.loads((wheel_dir / "manifest.json").read_text(encoding="utf-8"))
    del manifest["cache_key"]
    (wheel_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(RuntimeError, match="does not match its manifest or cache key"):
        citry_core_wheel.verified_wheel(wheel_dir, None)


def test_build_environment_drops_settings_the_key_does_not_cover() -> None:
    environment: Mapping[str, str] = {
        "PATH": "/bin",
        "CARGO_INCREMENTAL": "0",
        "RUSTC_WRAPPER": "sccache",
        "RUSTUP_TOOLCHAIN": "1.85.0",
        "RUSTFLAGS": "-C target-cpu=native",
        "CARGO_ENCODED_RUSTFLAGS": "-Ctarget-cpu=native",
        "CARGO_BUILD_RUSTFLAGS": "-Ctarget-cpu=native",
        "CARGO_BUILD_TARGET": "x86_64-unknown-linux-musl",
        "CARGO_PROFILE_RELEASE_LTO": "off",
        "CARGO_PROFILE_RELEASE_WHEEL_OPT_LEVEL": "0",
        "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS": "-Ctarget-cpu=native",
        "CARGO_TARGET_DIR": "/elsewhere/target",
        "PYO3_PYTHON": "/usr/bin/python3.9",
        "MATURIN_PEP517_ARGS": "--features other",
        "MACOSX_DEPLOYMENT_TARGET": "10.9",
    }

    assert citry_core_wheel._build_environment(environment) == {
        "PATH": "/bin",
        "CARGO_INCREMENTAL": "0",
        "RUSTC_WRAPPER": "sccache",
    }


class _Recorder:
    """Stands in for `subprocess.run`, recording each command and its keywords."""

    def __init__(self, on_run: Callable[[list[str], dict[str, Any]], None] | None = None) -> None:
        self.commands: list[list[str]] = []
        self.keywords: list[dict[str, Any]] = []
        self._on_run = on_run

    def __call__(self, command: list[str], **keywords: Any) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        self.keywords.append(keywords)
        if self._on_run is not None:
            self._on_run(command, keywords)
        return subprocess.CompletedProcess(command, 0)


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _Recorder:
    result = _Recorder()
    monkeypatch.setattr(citry_core_wheel, "_executable", lambda name: name)
    monkeypatch.setattr(citry_core_wheel.subprocess, "run", result)
    return result


def test_install_wheel_checks_the_wheel_then_syncs_then_installs_then_imports(
    tmp_path: Path,
    recorder: _Recorder,
) -> None:
    wheel_dir = _recorded(tmp_path / "wheels")
    repo_root = tmp_path / "repo"

    wheel = citry_core_wheel.install_wheel(
        wheel_dir,
        ["--all-packages", "--group", "e2e"],
        expected_cache_key=_CACHE_KEY,
        repo_root=repo_root,
    )

    assert wheel == wheel_dir / _WHEEL_NAME
    assert recorder.commands == [
        ["uv", "sync", "--locked", "--all-packages", "--group", "e2e", "--no-install-package", "citry-core"],
        ["uv", "pip", "install", "--python", ".venv", "--no-deps", "--reinstall", str(wheel)],
        ["uv", "run", "--no-sync", "python", "-c", citry_core_wheel._SMOKE_IMPORT],
    ]
    assert all(keywords["cwd"] == repo_root and keywords["check"] for keywords in recorder.keywords)


def test_install_wheel_refuses_a_bad_manifest_before_running_any_command(tmp_path: Path, recorder: _Recorder) -> None:
    wheel_dir = _recorded(tmp_path / "wheels")
    _make_manifest_a_list(wheel_dir)

    with pytest.raises(RuntimeError, match="does not match its manifest"):
        citry_core_wheel.install_wheel(wheel_dir, ["--all-packages"], repo_root=tmp_path)

    assert recorder.commands == []


def test_build_wheel_refuses_a_folder_that_already_has_files(tmp_path: Path, recorder: _Recorder) -> None:
    wheel_dir = tmp_path / "wheels"
    wheel_dir.mkdir()
    (wheel_dir / "left-over.txt").write_text("old", encoding="utf-8")

    with pytest.raises(RuntimeError, match="must be empty before a build"):
        citry_core_wheel.build_wheel(wheel_dir, _CACHE_KEY, repo_root=tmp_path)

    assert recorder.commands == []


def test_build_wheel_builds_smoke_tests_and_records_a_wheel_that_verifies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wheel_dir = tmp_path / "out" / "wheels"
    repo_root = tmp_path / "repo"

    def fake_uv_build(command: list[str], _keywords: dict[str, Any]) -> None:
        # Behave like `uv build`: put one wheel in the folder named by --out-dir.
        if command[1] == "build":
            out_dir = Path(command[command.index("--out-dir") + 1])
            (out_dir / _WHEEL_NAME).write_bytes(b"built wheel")

    recorder = _Recorder(fake_uv_build)
    monkeypatch.setattr(citry_core_wheel, "_executable", lambda name: name)
    monkeypatch.setattr(citry_core_wheel.subprocess, "run", recorder)
    # An environment that would change the compiled code without changing the key.
    monkeypatch.setenv("RUSTUP_TOOLCHAIN", "1.85.0")
    monkeypatch.setenv("CARGO_PROFILE_RELEASE_LTO", "off")
    monkeypatch.setenv("CARGO_INCREMENTAL", "0")
    smoked: list[Path] = []
    monkeypatch.setattr(citry_core_wheel, "_smoke_test", smoked.append)

    wheel = citry_core_wheel.build_wheel(wheel_dir, _CACHE_KEY, repo_root=repo_root)

    assert wheel == wheel_dir / _WHEEL_NAME
    assert recorder.commands == [
        [
            "uv",
            "build",
            "--package",
            "citry-core",
            "--wheel",
            "--python",
            sys.executable,
            "--out-dir",
            str(wheel_dir),
            "--config-setting",
            "maturin.build-args=--features abi3-py311 --profile release-wheel",
        ]
    ]
    build_keywords = recorder.keywords[0]
    assert build_keywords["cwd"] == repo_root
    assert "RUSTUP_TOOLCHAIN" not in build_keywords["env"]
    assert "CARGO_PROFILE_RELEASE_LTO" not in build_keywords["env"]
    assert build_keywords["env"]["CARGO_INCREMENTAL"] == "0"
    # The smoke test saw the built wheel, and the manifest it left behind verifies.
    assert smoked == [wheel]
    assert citry_core_wheel.verified_wheel(wheel_dir, _CACHE_KEY) == wheel


def test_build_wheel_does_not_record_a_wheel_that_fails_the_smoke_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wheel_dir = tmp_path / "wheels"

    def fake_uv_build(command: list[str], _keywords: dict[str, Any]) -> None:
        (Path(command[command.index("--out-dir") + 1]) / _WHEEL_NAME).write_bytes(b"broken wheel")

    def failing_smoke_test(_wheel: Path) -> None:
        msg = "import failed"
        raise RuntimeError(msg)

    monkeypatch.setattr(citry_core_wheel, "_executable", lambda name: name)
    monkeypatch.setattr(citry_core_wheel.subprocess, "run", _Recorder(fake_uv_build))
    monkeypatch.setattr(citry_core_wheel, "_smoke_test", failing_smoke_test)

    with pytest.raises(RuntimeError, match="import failed"):
        citry_core_wheel.build_wheel(wheel_dir, _CACHE_KEY, repo_root=tmp_path)

    assert not (wheel_dir / "manifest.json").exists()


def test_smoke_test_installs_the_wheel_in_a_throwaway_environment_and_imports_it(
    tmp_path: Path,
    recorder: _Recorder,
) -> None:
    wheel = tmp_path / _WHEEL_NAME

    citry_core_wheel._smoke_test(wheel)

    create, install, run_import = recorder.commands
    venv = create[-1]
    assert create == ["uv", "venv", "--python", sys.executable, venv]
    assert install == ["uv", "pip", "install", "--python", venv, "--no-deps", str(wheel)]
    # Isolated mode keeps the checkout's own citry_core off the import path.
    assert run_import[1:] == ["-I", "-c", citry_core_wheel._SMOKE_IMPORT]
    assert recorder.keywords[2]["cwd"] != tmp_path


@pytest.mark.parametrize(
    ("argv_tail", "expected"),
    [
        (["--", "--all-packages", "--group", "e2e"], ["--all-packages", "--group", "e2e"]),
        ([], []),
    ],
)
def test_main_install_passes_the_job_sync_arguments_without_the_separator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    argv_tail: list[str],
    expected: list[str],
) -> None:
    calls: list[tuple[Path, list[str], str | None]] = []

    def fake_install(wheel_dir: Path, sync_arguments: list[str], *, expected_cache_key: str | None = None) -> Path:
        calls.append((wheel_dir, sync_arguments, expected_cache_key))
        return wheel_dir / _WHEEL_NAME

    monkeypatch.setattr(citry_core_wheel, "install_wheel", fake_install)

    citry_core_wheel.main(["install", "--wheel-dir", str(tmp_path), *argv_tail])

    assert calls == [(tmp_path, expected, None)]


def test_main_cache_key_writes_a_github_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        citry_core_wheel,
        "cache_key",
        lambda *_arguments: {"cache_key": "the-key", "source_digest": "the-digest"},
    )
    output = tmp_path / "github_output"

    citry_core_wheel.main(
        [
            "cache-key",
            "--runner-os",
            "Linux",
            "--runner-arch",
            "X64",
            "--image-os",
            "ubuntu24",
            "--github-output",
            str(output),
        ],
    )

    assert output.read_text(encoding="utf-8") == "cache_key=the-key\nsource_digest=the-digest\n"
    assert "the-key" in capsys.readouterr().out
