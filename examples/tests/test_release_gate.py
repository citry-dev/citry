import json
from pathlib import Path

from examples._internal.release_gate import validate_release_surfaces


def _write_fixture(root: Path, *, example_version: str = "0.4.4") -> tuple[dict, dict]:
    (root / "packages/py/citry").mkdir(parents=True)
    (root / "packages/py/citry_core").mkdir(parents=True)
    (root / "examples/starters/fastapi").mkdir(parents=True)
    (root / "docs_site/static/playground").mkdir(parents=True)
    (root / "packages/py/citry/pyproject.toml").write_text(
        '[project]\nname = "citry"\nversion = "0.4.4"\n', encoding="utf-8"
    )
    build = {
        "pyodide": "314.0.3",
        "python": "3.14.2",
        "python_tag": "cp314",
        "abi_tag": "cp314",
        "platform_tag": "pyemscripten_2026_0_wasm32",
    }
    (root / "packages/py/citry_core/pyodide-build.json").write_text(json.dumps(build), encoding="utf-8")
    (root / "examples/catalog.toml").write_text(
        'schema = 1\n[[projects]]\nid = "starter-fastapi"\npath = "starters/fastapi"\n',
        encoding="utf-8",
    )
    project = root / "examples/starters/fastapi"
    project.joinpath("pyproject.toml").write_text(
        f'[project]\nname = "example"\nversion = "0.1.0"\ndependencies = ["citry>={example_version},<0.5"]\n',
        encoding="utf-8",
    )
    project.joinpath("README.md").write_text(f"Requires Citry {example_version}.\n", encoding="utf-8")
    wheel_url = "https://files.pythonhosted.org/packages/aa/bb/citry-0.4.4-py3-none-any.whl"
    wheel_hash = "1" * 64
    core_version = "1.6.1"
    core_filename = f"citry_core-{core_version}-{build['python_tag']}-{build['abi_tag']}-{build['platform_tag']}.whl"
    core_url = f"https://files.pythonhosted.org/packages/cc/dd/{core_filename}"
    ui_version = "0.2.0"
    ui_url = f"https://files.pythonhosted.org/packages/ee/ff/citry_ui-{ui_version}-py3-none-any.whl"
    project.joinpath("uv.lock").write_text(
        "\n".join(
            (
                "version = 1",
                "[[package]]",
                'name = "citry"',
                f'version = "{example_version}"',
                'source = { registry = "https://pypi.org/simple" }',
                "wheels = [",
                f'  {{ url = "{wheel_url}", hash = "sha256:{wheel_hash}" }},',
                "]",
            )
        ),
        encoding="utf-8",
    )
    runtime = {
        "pyodide": {"version": build["pyodide"], "python": build["python"]},
        "citry": {"version": example_version, "core_version": core_version, "ui_version": ui_version},
        "packages": [
            {"name": "citry", "version": example_version, "url": wheel_url},
            {"name": "citry-core", "version": core_version, "url": core_url},
            {"name": "citry-ui", "version": ui_version, "url": ui_url},
        ],
    }
    root.joinpath("docs_site/static/playground/runtime.json").write_text(json.dumps(runtime), encoding="utf-8")
    citry_payload = {
        "urls": [
            {
                "filename": "citry-0.4.4-py3-none-any.whl",
                "url": wheel_url,
                "digests": {"sha256": wheel_hash},
            }
        ]
    }
    core_payload = {
        "urls": [
            {
                "filename": core_filename,
                "url": core_url,
                "digests": {"sha256": "2" * 64},
            }
        ]
    }
    return citry_payload, core_payload


def test_release_surfaces_match_public_citry(tmp_path: Path) -> None:
    payload, core_payload = _write_fixture(tmp_path)

    assert validate_release_surfaces(tmp_path, pypi_payload=payload, core_pypi_payload=core_payload) == []


def test_release_surfaces_reject_stale_examples_and_playground(tmp_path: Path) -> None:
    payload, core_payload = _write_fixture(tmp_path, example_version="0.4.3")

    problems = validate_release_surfaces(tmp_path, pypi_payload=payload, core_pypi_payload=core_payload)

    assert any("manifest must set its minimum Citry version to 0.4.4" in item for item in problems)
    assert any("README must name Citry 0.4.4" in item for item in problems)
    assert any("lock must resolve Citry 0.4.4" in item for item in problems)
    assert any("playground: citry.version must be 0.4.4" in item for item in problems)


def test_release_surfaces_reject_incompatible_core_wheel(tmp_path: Path) -> None:
    payload, _core_payload = _write_fixture(tmp_path)
    runtime_path = tmp_path / "docs_site/static/playground/runtime.json"
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    core = next(package for package in runtime["packages"] if package["name"] == "citry-core")
    core["url"] = "https://files.pythonhosted.org/packages/cc/dd/citry_core-1.6.1-py3-none-any.whl"
    runtime_path.write_text(json.dumps(runtime), encoding="utf-8")

    problems = validate_release_surfaces(tmp_path, pypi_payload=payload, core_pypi_payload={"urls": []})

    assert any("wheel must match the pinned Python and PyEmscripten ABI" in item for item in problems)


def test_release_surfaces_reject_unpublished_core_wheel(tmp_path: Path) -> None:
    payload, _core_payload = _write_fixture(tmp_path)

    problems = validate_release_surfaces(tmp_path, pypi_payload=payload, core_pypi_payload={"urls": []})

    assert any("absent from the public PyPI release" in item for item in problems)
