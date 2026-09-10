import copy
import hashlib
import io
import json
import zipfile

import pytest
from scripts import update_playground_runtime as updater
from scripts.verify_playground_release import PlaygroundReleaseError


def _wheel(name, version, requires=()):
    content = io.BytesIO()
    metadata = f"Name: {name}\nVersion: {version}\nRequires-Python: >=3.12\n"
    metadata += "".join(f"Requires-Dist: {requirement}\n" for requirement in requires)
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr(f"{name}-{version}.dist-info/METADATA", metadata)
    return content.getvalue()


@pytest.fixture
def release(monkeypatch):
    baseline = {"citry-core": "1.6.0", "citry": "0.4.0", "citry-ui": "0.2.0"}
    runtime = {
        "schema_version": 1,
        "protocol_version": 1,
        "pyodide": {"version": "314.0.3", "python": "3.14.2"},
        "citry": {
            "version": baseline["citry"],
            "core_version": baseline["citry-core"],
            "ui_version": baseline["citry-ui"],
        },
        "packages": [
            {
                "name": name,
                "version": version,
                "source": "pypi",
                "filename": f"{name.replace('-', '_')}-{version}-"
                + ("cp314-cp314-pyemscripten_2026_0_wasm32.whl" if name == "citry-core" else "py3-none-any.whl"),
                "sha256": "a" * 64,
            }
            for name, version in baseline.items()
        ]
        + [
            {"name": "wrapt", "version": "2.1.0", "source": "url", "url": "https://example.com/wrapt.whl"},
            {
                "name": "typing-extensions",
                "version": "4.15.0",
                "source": "url",
                "url": "https://example.com/typing.whl",
            },
        ],
    }
    versions = {"citry-core": "1.7.0", "citry": "0.5.0", "citry-ui": "0.2.1"}
    inventories, wheels = {}, {}
    for package in runtime["packages"]:
        name = package["name"]
        if name not in versions:
            continue
        version = versions[name]
        requirements = ["citry-core==1.7.0", "wrapt>=2", "typing-extensions>=4"] if name == "citry" else []
        wheel = _wheel(name, version, requirements)
        filename = package["filename"].replace(package["version"], version)
        inventories[name] = {
            "version": version,
            "artifacts": [{"name": filename, "sha256": hashlib.sha256(wheel).hexdigest(), "bytes": len(wheel)}],
        }
        wheels[name] = wheel
    monkeypatch.setattr(updater, "release_inventory", lambda name, _version: inventories[name])
    monkeypatch.setattr(updater, "public_wheel", lambda name, _version, _artifact: wheels[name])
    return runtime, versions, inventories, wheels


def test_updates_exact_versions_preserves_dependencies_and_is_idempotent(release):
    runtime, versions, _, _ = release
    original = copy.deepcopy(runtime)
    result = updater.update_runtime(runtime, versions)
    assert runtime == original
    assert result["pyodide"] == original["pyodide"]
    assert [item for item in result["packages"] if item["name"] not in versions] == [
        item for item in original["packages"] if item["name"] not in versions
    ]
    assert result["citry"] == {"version": "0.5.0", "core_version": "1.7.0", "ui_version": "0.2.1"}
    assert updater.update_runtime(result, versions) == result


def test_rejects_downgrade(release):
    runtime, versions, _, _ = release
    versions["citry-core"] = "1.0.0"
    with pytest.raises(PlaygroundReleaseError, match="downgrade"):
        updater.update_runtime(runtime, versions)


def test_rejects_abi_change(release):
    runtime, versions, inventories, _ = release
    artifact = inventories["citry-core"]["artifacts"][0]
    artifact["name"] = artifact["name"].replace("cp314", "cp313")
    with pytest.raises(PlaygroundReleaseError, match="current browser ABI"):
        updater.update_runtime(runtime, versions)


def test_rejects_unsatisfied_dependencies_without_mutating_input(release):
    runtime, versions, _, wheels = release
    original = copy.deepcopy(runtime)
    wheels["citry"] = _wheel("citry", "0.5.0", ["citry-core==2.0"])
    with pytest.raises(PlaygroundReleaseError, match="not satisfied"):
        updater.update_runtime(runtime, versions)
    assert runtime == original


def test_public_wheel_checks_actual_bytes(monkeypatch):
    artifact = {"name": "citry-0.5.0-py3-none-any.whl", "sha256": "a" * 64, "bytes": 3}
    metadata = {
        "urls": [
            {
                "filename": artifact["name"],
                "digests": {"sha256": artifact["sha256"]},
                "size": 3,
                "url": "https://files.pythonhosted.org/wheel.whl",
                "yanked": False,
            }
        ]
    }
    monkeypatch.setattr(
        updater, "_download", lambda url: json.dumps(metadata).encode() if url.endswith("json") else b"bad"
    )
    with pytest.raises(PlaygroundReleaseError, match="public bytes"):
        updater.public_wheel("citry", "0.5.0", artifact)


def test_dependency_markers_use_browser_environment(release):
    runtime, _, _, _ = release
    version = runtime["citry"]["version"]
    updater.verify_dependencies(runtime, {"citry": _wheel("citry", version, ['missing; sys_platform == "win32"'])})
    with pytest.raises(PlaygroundReleaseError, match="not satisfied"):
        updater.verify_dependencies(
            runtime, {"citry": _wheel("citry", version, ['missing; sys_platform == "emscripten"'])}
        )


def test_source_versions_rejects_branch_before_running_git(monkeypatch):
    def unexpected(*_args):
        pytest.fail("invalid source ref reached git")

    monkeypatch.setattr(updater, "_run", unexpected)
    with pytest.raises(PlaygroundReleaseError, match="canonical"):
        updater.source_versions("main")


def test_rejects_yanked_public_wheel(monkeypatch):
    artifact = {"name": "citry-0.5.0-py3-none-any.whl"}
    monkeypatch.setattr(
        updater,
        "_download",
        lambda _url: json.dumps({"urls": [{"filename": artifact["name"], "yanked": True}]}).encode(),
    )
    with pytest.raises(PlaygroundReleaseError, match="non-yanked"):
        updater.public_wheel("citry", "0.5.0", artifact)


def test_failed_update_leaves_runtime_file_unchanged(release, monkeypatch, tmp_path):
    runtime, versions, _, wheels = release
    path = tmp_path / "runtime.json"
    original = json.dumps(runtime)
    path.write_text(original)
    wheels["citry"] = _wheel("citry", "0.5.0", ["missing-runtime-dependency>=1"])
    monkeypatch.setattr(updater, "source_versions", lambda _ref: versions)
    monkeypatch.setattr(updater.sys, "argv", ["update", "--source-ref", "citry@0.5.0", "--runtime", str(path)])
    assert updater.main() == 1
    assert path.read_text() == original
