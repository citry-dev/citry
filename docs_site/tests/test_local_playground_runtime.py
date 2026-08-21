"""Workspace Citry UI wheel used by the docs authoring server."""

from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from docs_site._internal import local_playground_runtime


def test_workspace_wheel_build_uses_a_temporary_source_copy(
    monkeypatch,
    tmp_path: Path,
) -> None:
    package_dir = tmp_path / "repo" / "packages" / "py" / "citry"
    (package_dir / "citry").mkdir(parents=True)
    (package_dir / "citry" / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "pyproject.toml").write_text("[build-system]\n", encoding="utf-8")
    (package_dir / "build" / "lib").mkdir(parents=True)
    (package_dir / "build" / "lib" / "generated.py").write_text("", encoding="utf-8")
    output_dir = tmp_path / "runtime" / "local"
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(local_playground_runtime.shutil, "which", lambda executable: f"/usr/bin/{executable}")

    def fake_run(command, **_kwargs):
        source_dir = Path(command[3])
        assert source_dir != package_dir
        assert source_dir.is_relative_to(output_dir.parent)
        assert (source_dir / "citry" / "__init__.py").is_file()
        assert not (source_dir / "build").exists()
        (output_dir / "citry-0.4.2-py3-none-any.whl").write_bytes(b"wheel")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(local_playground_runtime.subprocess, "run", fake_run)

    wheel = local_playground_runtime._build_workspace_wheel(package_dir, output_dir)

    assert wheel == output_dir / "citry-0.4.2-py3-none-any.whl"


def _write_wheel(
    output_dir: Path,
    *,
    distribution: str,
    import_name: str,
    version: str,
    requirements: tuple[str, ...] = (),
) -> Path:
    filename = f"{distribution.replace('-', '_')}-{version}-py3-none-any.whl"
    path = output_dir / filename
    dist_info = f"{distribution.replace('-', '_')}-{version}.dist-info"
    metadata = [f"Name: {distribution}", f"Version: {version}"]
    metadata.extend(f"Requires-Dist: {requirement}" for requirement in requirements)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{import_name}/__init__.py", "")
        archive.writestr(f"{dist_info}/METADATA", "\n".join(metadata) + "\n")
        archive.writestr(f"{dist_info}/WHEEL", "Wheel-Version: 1.0\nTag: py3-none-any\n")
    return path


def test_build_local_runtime_keeps_compatible_citry_and_adds_workspace_citry_ui(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "docs_site" / "static" / "playground"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "runtime.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "protocol_version": 1,
                "pyodide": {"version": "test", "python": "3.14.2"},
                "citry": {"version": "0.4.2", "core_version": "1.5.1", "ui_version": "0.1.0"},
                "packages": [
                    {"name": "citry-core", "version": "1.5.1", "url": "https://example.test/core.whl"},
                    {"name": "citry", "version": "0.4.2", "url": "https://example.test/citry.whl"},
                    {"name": "citry-ui", "version": "0.1.0", "url": "https://example.test/ui.whl"},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_build(package_dir: Path, output_dir: Path) -> Path:
        assert package_dir.name == "citry_ui"
        return _write_wheel(
            output_dir,
            distribution="citry-ui",
            import_name="citry_ui",
            version="0.1.0",
            requirements=("citry>=0.4.0,<0.5.0",),
        )

    monkeypatch.setattr(local_playground_runtime, "_build_workspace_wheel", fake_build)

    local = local_playground_runtime.build_local_playground_runtime(
        repo_root=tmp_path,
        output_dir=tmp_path / "runtime",
    )
    manifest = json.loads(local.manifest_path.read_text(encoding="utf-8"))
    packages = {package["name"]: package for package in manifest["packages"]}

    assert manifest["citry"] == {
        "version": "0.4.2",
        "core_version": "1.5.1",
        "ui_version": "0.1.0",
    }
    assert packages["citry-core"]["url"] == "https://example.test/core.whl"
    assert packages["citry"]["version"] == "0.4.2"
    assert packages["citry"]["url"] == "https://example.test/citry.whl"
    assert packages["citry-ui"]["version"] == "0.1.0"
    assert packages["citry-ui"]["url"] == "./local/citry_ui-0.1.0-py3-none-any.whl"
    assert [package["name"] for package in manifest["packages"]].count("citry-ui") == 1
    assert local.wheel_names == {"citry_ui-0.1.0-py3-none-any.whl"}


def test_build_local_runtime_rejects_workspace_ui_newer_than_published_citry(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "docs_site" / "static" / "playground"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "runtime.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "protocol_version": 1,
                "pyodide": {"version": "test", "python": "3.14.2"},
                "citry": {"version": "0.3.1", "core_version": "1.4.0"},
                "packages": [
                    {"name": "citry-core", "version": "1.4.0", "url": "https://example.test/core.whl"},
                    {"name": "citry", "version": "0.3.1", "url": "https://example.test/citry.whl"},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_build(_package_dir: Path, output_dir: Path) -> Path:
        return _write_wheel(
            output_dir,
            distribution="citry-ui",
            import_name="citry_ui",
            version="0.1.0",
            requirements=("citry>=0.4.0,<0.5.0",),
        )

    monkeypatch.setattr(local_playground_runtime, "_build_workspace_wheel", fake_build)

    with pytest.raises(
        local_playground_runtime.LocalPlaygroundRuntimeError,
        match=r"local Citry UI 0\.1\.0 does not accept the playground's Citry 0\.3\.1",
    ):
        local_playground_runtime.build_local_playground_runtime(
            repo_root=tmp_path,
            output_dir=tmp_path / "runtime",
        )


def test_local_runtime_can_be_loaded_from_its_generated_directory(tmp_path: Path) -> None:
    local_dir = tmp_path / "runtime"
    wheels = local_dir / "local"
    wheels.mkdir(parents=True)
    citry_wheel = _write_wheel(
        wheels,
        distribution="citry",
        import_name="citry",
        version="0.4.2",
    )
    ui_wheel = _write_wheel(
        wheels,
        distribution="citry-ui",
        import_name="citry_ui",
        version="0.1.0",
    )
    manifest = {
        "schema_version": 1,
        "protocol_version": 1,
        "citry": {"version": "0.4.2", "core_version": "1.5.1", "ui_version": "0.1.0"},
        "packages": [
            {
                "name": "citry",
                "version": "0.4.2",
                "url": f"./local/{citry_wheel.name}",
            },
            {
                "name": "citry-ui",
                "version": "0.1.0",
                "url": f"./local/{ui_wheel.name}",
            },
        ],
    }
    (local_dir / "runtime.json").write_text(json.dumps(manifest), encoding="utf-8")

    loaded = local_playground_runtime.load_local_playground_runtime(local_dir)

    assert loaded.manifest_path == local_dir / "runtime.json"
    assert loaded.wheel_names == {citry_wheel.name, ui_wheel.name}


def test_local_runtime_rejects_a_manifest_without_local_citry_ui(tmp_path: Path) -> None:
    local_dir = tmp_path / "runtime"
    wheels = local_dir / "local"
    wheels.mkdir(parents=True)
    citry_wheel = _write_wheel(
        wheels,
        distribution="citry",
        import_name="citry",
        version="0.4.2",
    )
    (local_dir / "runtime.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "protocol_version": 1,
                "citry": {"version": "0.4.2", "core_version": "1.5.1", "ui_version": "0.1.0"},
                "packages": [
                    {
                        "name": "citry",
                        "version": "0.4.2",
                        "url": f"./local/{citry_wheel.name}",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        local_playground_runtime.LocalPlaygroundRuntimeError,
        match=r"missing citry-ui 0\.1\.0",
    ):
        local_playground_runtime.load_local_playground_runtime(local_dir)


@pytest.mark.parametrize("field", ["schema_version", "protocol_version"])
@pytest.mark.parametrize("value", [True, 1.0, 2, None])
def test_local_runtime_rejects_unsupported_manifest_versions(tmp_path: Path, field: str, value: object) -> None:
    local_dir = tmp_path / "runtime"
    local_dir.mkdir()
    manifest = {
        "schema_version": 1,
        "protocol_version": 1,
        "packages": [],
        "citry": {"version": "0.4.2", "ui_version": "0.1.0"},
    }
    if value is None:
        manifest.pop(field)
    else:
        manifest[field] = value
    (local_dir / "runtime.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(local_playground_runtime.LocalPlaygroundRuntimeError, match=f"{field.split('_')[0]} version 1"):
        local_playground_runtime.load_local_playground_runtime(local_dir)
