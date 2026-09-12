from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest
from scripts import python_diagnostic

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("profile", "relative_target"),
    [
        ("citry", "packages/py/citry/tests/test_reload.py"),
        ("citry-core", "packages/py/citry_core/tests/test_template_parser.py::test_compile"),
        ("citry-lsp", "packages/py/citry_lsp/tests/test_engine.py"),
        ("citry-ui", "packages/py/citry_ui/citry_ui/quality/tests/test_scaling.py"),
        ("pygments-citry", "packages/py/pygments_citry/tests/test_lexers.py"),
        ("full-workspace", "packages/py/citry_lsp/tests/test_engine.py::TestEngine::test_open"),
    ],
)
def test_validate_pytest_target_accepts_profile_files_and_node_ids(
    tmp_path: Path,
    profile: str,
    relative_target: str,
) -> None:
    relative_file = relative_target.partition("::")[0]
    target = tmp_path / relative_file
    target.parent.mkdir(parents=True)
    target.touch()

    assert python_diagnostic.validate_pytest_target(profile, relative_target, repo_root=tmp_path) == target


@pytest.mark.parametrize(
    ("profile", "target"),
    [
        ("citry", "packages/py/citry_core/tests/test_template_parser.py"),
        ("citry", "packages/py/citry/tests/e2e/test_runtime_e2e.py"),
        ("citry", "packages/py/citry/tests/test_benchmark_citry.py"),
        ("citry", "packages/py/citry/citry/reload.py"),
        ("citry", "../test_escape.py"),
        ("citry", "--collect-only"),
        ("citry", "packages/py/citry/tests/test_reload.py\n--collect-only"),
        ("citry", "packages/py/citry/tests/test_reload.py::"),
    ],
)
def test_validate_pytest_target_rejects_cross_profile_browser_and_nonliteral_targets(
    tmp_path: Path,
    profile: str,
    target: str,
) -> None:
    file_target = target.partition("::")[0]
    candidate = tmp_path / file_target
    if file_target.startswith("packages/") and "\n" not in target:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.touch(exist_ok=True)

    with pytest.raises(ValueError, match=r"pytest target|pytest node|browser and benchmark"):
        python_diagnostic.validate_pytest_target(profile, target, repo_root=tmp_path)


def test_native_source_digest_tracks_build_inputs_but_ignores_tracked_nonbuild_paths(tmp_path: Path) -> None:
    git = shutil.which("git")
    assert git is not None
    subprocess.run([git, "init", "-q"], cwd=tmp_path, check=True)
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text("[workspace]\n", encoding="utf-8")
    subprocess.run([git, "add", "Cargo.toml"], cwd=tmp_path, check=True)
    original = python_diagnostic.native_source_digest(repo_root=tmp_path)

    source = tmp_path / "crates" / "demo" / "src" / "lib.rs"
    source.parent.mkdir(parents=True)
    source.write_text("pub fn one() {}\n", encoding="utf-8")
    subprocess.run([git, "add", "crates/demo/src/lib.rs"], cwd=tmp_path, check=True)
    changed = python_diagnostic.native_source_digest(repo_root=tmp_path)
    assert changed != original

    unrelated = tmp_path / "crates" / "demo" / "tests" / "test_demo.rs"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("ignored\n", encoding="utf-8")
    subprocess.run([git, "add", "crates/demo/tests/test_demo.rs"], cwd=tmp_path, check=True)
    assert python_diagnostic.native_source_digest(repo_root=tmp_path) == changed


def test_citry_profile_selects_the_root_owner_of_its_policy_test_dependencies() -> None:
    assert python_diagnostic._SYNC_ARGUMENTS["citry"] == (
        "--package",
        "citry-monorepo",
        "--package",
        "citry",
    )
    root_pyproject = (python_diagnostic._REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"pyyaml>=6.0"' in root_pyproject


def test_cache_identity_is_scoped_by_runner_python_compiler_and_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rustc_identity = ["rustc one", "rust-one"]
    source_digest = ["source-one"]
    python_version = ["3.14.0"]
    monkeypatch.setattr(python_diagnostic, "_rustc_identity", lambda: tuple(rustc_identity))
    monkeypatch.setattr(python_diagnostic, "_uv_identity", lambda: "uv 1")
    monkeypatch.setattr(python_diagnostic, "native_source_digest", lambda **_kwargs: source_digest[0])
    monkeypatch.setattr(python_diagnostic.platform, "python_version", lambda: python_version[0])
    monkeypatch.setattr(python_diagnostic.sysconfig, "get_config_var", lambda _name: "cpython-314-linux")

    base = python_diagnostic.cache_identity("Linux", "X64", "ubuntu24/one", repo_root=tmp_path)["cache_key"]
    assert python_diagnostic.cache_identity("macOS", "X64", "macos-15/one", repo_root=tmp_path)["cache_key"] != base
    assert python_diagnostic.cache_identity("Linux", "ARM64", "ubuntu24/one", repo_root=tmp_path)["cache_key"] != base
    assert python_diagnostic.cache_identity("Linux", "X64", "ubuntu24/two", repo_root=tmp_path)["cache_key"] != base

    python_version[0] = "3.14.1"
    assert python_diagnostic.cache_identity("Linux", "X64", "ubuntu24/one", repo_root=tmp_path)["cache_key"] != base
    python_version[0] = "3.14.0"

    rustc_identity[:] = ["rustc two", "rust-two"]
    assert python_diagnostic.cache_identity("Linux", "X64", "ubuntu24/one", repo_root=tmp_path)["cache_key"] != base
    rustc_identity[:] = ["rustc one", "rust-one"]

    source_digest[0] = "source-two"
    assert python_diagnostic.cache_identity("Linux", "X64", "ubuntu24/one", repo_root=tmp_path)["cache_key"] != base

    source_digest[0] = "source-one"
    monkeypatch.setattr(python_diagnostic, "_uv_identity", lambda: "uv 2")
    assert python_diagnostic.cache_identity("Linux", "X64", "ubuntu24/one", repo_root=tmp_path)["cache_key"] != base


def test_verified_wheel_requires_matching_key_name_and_bytes(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.2.3-cp314-cp314-any.whl"
    wheel.write_bytes(b"wheel bytes")
    python_diagnostic.record_wheel(tmp_path, "exact-key")

    assert python_diagnostic.verified_wheel(tmp_path, "exact-key") == wheel

    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["sha256"] == hashlib.sha256(b"wheel bytes").hexdigest()

    with pytest.raises(RuntimeError, match="does not match"):
        python_diagnostic.verified_wheel(tmp_path, "wrong-key")

    wheel.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="does not match"):
        python_diagnostic.verified_wheel(tmp_path, "exact-key")


@pytest.mark.parametrize(
    ("profile", "expected_profile_arguments", "needs_core"),
    [
        ("citry", ["--package", "citry-monorepo", "--package", "citry"], True),
        ("citry-core", ["--package", "citry-core"], True),
        ("citry-lsp", ["--package", "citry-lsp"], True),
        ("citry-ui", ["--package", "citry-ui"], True),
        ("pygments-citry", ["--package", "pygments-citry"], False),
        ("full-workspace", ["--all-packages"], True),
    ],
)
def test_install_profile_narrows_sync_and_substitutes_verified_core_wheel(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    profile: str,
    expected_profile_arguments: list[str],
    needs_core: bool,
) -> None:
    commands: list[list[str]] = []
    monkeypatch.setattr(python_diagnostic, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(python_diagnostic, "_executable", lambda name: name)
    monkeypatch.setattr(
        python_diagnostic.subprocess,
        "run",
        lambda command, **_kwargs: commands.append(command),
    )
    if needs_core:
        wheel = tmp_path / "citry_core.whl"
        wheel.write_bytes(b"wheel")
        python_diagnostic.record_wheel(tmp_path, "cache-key")

    python_diagnostic.install_profile(profile, tmp_path, "cache-key")

    expected_sync = ["uv", "sync", "--locked", *expected_profile_arguments]
    if needs_core:
        expected_sync.extend(["--no-install-package", "citry-core"])
    assert commands[0] == expected_sync
    if needs_core:
        assert commands[1][:8] == [
            "uv",
            "pip",
            "install",
            "--python",
            ".venv",
            "--no-deps",
            "--reinstall",
            str(tmp_path / "citry_core.whl"),
        ]
        assert commands[2] == [
            "uv",
            "run",
            "--no-sync",
            "python",
            "-c",
            "import citry_core._rust as rust; print(rust.__file__)",
        ]
    else:
        assert len(commands) == 1
