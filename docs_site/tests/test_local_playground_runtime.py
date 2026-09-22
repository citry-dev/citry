"""Workspace Citry browser tuple used by the docs authoring server."""

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
    tag: str = "py3-none-any",
) -> Path:
    filename = f"{distribution.replace('-', '_')}-{version}-{tag}.whl"
    path = output_dir / filename
    dist_info = f"{distribution.replace('-', '_')}-{version}.dist-info"
    metadata = [f"Name: {distribution}", f"Version: {version}"]
    metadata.extend(f"Requires-Dist: {requirement}" for requirement in requirements)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{import_name}/__init__.py", "")
        archive.writestr(f"{dist_info}/METADATA", "\n".join(metadata) + "\n")
        archive.writestr(f"{dist_info}/WHEEL", f"Wheel-Version: 1.0\nTag: {tag}\n")
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
                "source": "published",
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

    core_wheel = _write_wheel(
        tmp_path,
        distribution="citry-core",
        import_name="citry_core",
        version="1.5.1",
        tag="cp314-cp314-pyemscripten_2026_0_wasm32",
    )

    def fake_build(package_dir: Path, output_dir: Path) -> Path:
        if package_dir.name == "citry":
            return _write_wheel(
                output_dir,
                distribution="citry",
                import_name="citry",
                version="0.4.2",
                requirements=("citry-core==1.5.1",),
            )
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
        core_wheel=core_wheel,
    )
    manifest = json.loads(local.manifest_path.read_text(encoding="utf-8"))
    packages = {package["name"]: package for package in manifest["packages"]}

    assert manifest["citry"] == {
        "version": "0.4.2",
        "core_version": "1.5.1",
        "ui_version": "0.1.0",
    }
    assert manifest["source"] == "workspace"
    assert packages["citry-core"]["url"] == "./local/citry_core-1.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    assert packages["citry"]["version"] == "0.4.2"
    assert packages["citry"]["url"] == "./local/citry-0.4.2-py3-none-any.whl"
    assert packages["citry-ui"]["version"] == "0.1.0"
    assert packages["citry-ui"]["url"] == "./local/citry_ui-0.1.0-py3-none-any.whl"
    assert [package["name"] for package in manifest["packages"]].count("citry-ui") == 1
    assert local.wheel_names == {
        "citry_core-1.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl",
        "citry-0.4.2-py3-none-any.whl",
        "citry_ui-0.1.0-py3-none-any.whl",
    }


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
                "source": "published",
                "pyodide": {"version": "test", "python": "3.14.2"},
                "citry": {"version": "0.3.1", "core_version": "1.4.0", "ui_version": "0.1.0"},
                "packages": [
                    {"name": "citry-core", "version": "1.4.0", "url": "https://example.test/core.whl"},
                    {"name": "citry", "version": "0.3.1", "url": "https://example.test/citry.whl"},
                    {"name": "citry-ui", "version": "0.1.0", "url": "https://example.test/ui.whl"},
                ],
            }
        ),
        encoding="utf-8",
    )

    core_wheel = _write_wheel(
        tmp_path,
        distribution="citry-core",
        import_name="citry_core",
        version="1.4.0",
        tag="cp314-cp314-pyemscripten_2026_0_wasm32",
    )

    def fake_build(package_dir: Path, output_dir: Path) -> Path:
        if package_dir.name == "citry":
            return _write_wheel(
                output_dir,
                distribution="citry",
                import_name="citry",
                version="0.3.1",
                requirements=("citry-core==1.4.0",),
            )
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
            core_wheel=core_wheel,
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
        requirements=("citry-core==1.5.1",),
    )
    core_wheel = _write_wheel(
        wheels,
        distribution="citry-core",
        import_name="citry_core",
        version="1.5.1",
        tag="cp314-cp314-pyemscripten_2026_0_wasm32",
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
        "source": "workspace",
        "citry": {"version": "0.4.2", "core_version": "1.5.1", "ui_version": "0.1.0"},
        "packages": [
            {
                "name": "citry-core",
                "version": "1.5.1",
                "url": f"./local/{core_wheel.name}",
            },
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
    assert loaded.wheel_names == {core_wheel.name, citry_wheel.name, ui_wheel.name}


def _complete_local_runtime(tmp_path: Path) -> tuple[Path, dict]:
    local_dir = tmp_path / "runtime"
    wheels = local_dir / "local"
    wheels.mkdir(parents=True)
    wheel_specs = (
        ("citry-core", "citry_core", "1.5.1", "cp314-cp314-pyemscripten_2026_0_wasm32"),
        ("citry", "citry", "0.4.2", "py3-none-any"),
        ("citry-ui", "citry_ui", "0.1.0", "py3-none-any"),
    )
    packages = []
    for name, import_name, version, tag in wheel_specs:
        wheel = _write_wheel(wheels, distribution=name, import_name=import_name, version=version, tag=tag)
        packages.append({"name": name, "version": version, "url": f"./local/{wheel.name}"})
    manifest = {
        "schema_version": 1,
        "protocol_version": 1,
        "source": "workspace",
        "citry": {"version": "0.4.2", "core_version": "1.5.1", "ui_version": "0.1.0"},
        "packages": packages,
    }
    (local_dir / "runtime.json").write_text(json.dumps(manifest), encoding="utf-8")
    return local_dir, manifest


@pytest.mark.parametrize("url", ["./local/../escape.whl", "./local/..\\escape.whl"])
def test_local_runtime_rejects_path_traversal_in_local_wheel_urls(tmp_path: Path, url: str) -> None:
    local_dir, manifest = _complete_local_runtime(tmp_path)
    manifest["packages"][0]["url"] = url
    (local_dir / "runtime.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(local_playground_runtime.LocalPlaygroundRuntimeError, match="invalid local wheel URL"):
        local_playground_runtime.load_local_playground_runtime(local_dir)


def test_local_runtime_rejects_duplicate_workspace_package_entries(tmp_path: Path) -> None:
    local_dir, manifest = _complete_local_runtime(tmp_path)
    manifest["packages"].append(dict(manifest["packages"][0]))
    (local_dir / "runtime.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(local_playground_runtime.LocalPlaygroundRuntimeError, match="duplicate citry-core"):
        local_playground_runtime.load_local_playground_runtime(local_dir)


def test_local_runtime_rejects_an_unexpected_local_package_entry(tmp_path: Path) -> None:
    local_dir, manifest = _complete_local_runtime(tmp_path)
    extra_wheel = _write_wheel(
        local_dir / "local",
        distribution="unexpected",
        import_name="unexpected",
        version="1.0.0",
    )
    manifest["packages"].append({"name": "unexpected", "version": "1.0.0", "url": f"./local/{extra_wheel.name}"})
    (local_dir / "runtime.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(local_playground_runtime.LocalPlaygroundRuntimeError, match="unexpected local package"):
        local_playground_runtime.load_local_playground_runtime(local_dir)


def test_local_runtime_rejects_a_manifest_without_local_citry_ui(tmp_path: Path) -> None:
    local_dir = tmp_path / "runtime"
    wheels = local_dir / "local"
    wheels.mkdir(parents=True)
    citry_wheel = _write_wheel(
        wheels,
        distribution="citry",
        import_name="citry",
        version="0.4.2",
        requirements=("citry-core==1.5.1",),
    )
    core_wheel = _write_wheel(
        wheels,
        distribution="citry-core",
        import_name="citry_core",
        version="1.5.1",
        tag="cp314-cp314-pyemscripten_2026_0_wasm32",
    )
    (local_dir / "runtime.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "protocol_version": 1,
                "source": "workspace",
                "citry": {"version": "0.4.2", "core_version": "1.5.1", "ui_version": "0.1.0"},
                "packages": [
                    {
                        "name": "citry-core",
                        "version": "1.5.1",
                        "url": f"./local/{core_wheel.name}",
                    },
                    {
                        "name": "citry",
                        "version": "0.4.2",
                        "url": f"./local/{citry_wheel.name}",
                    },
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
        "source": "workspace",
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
