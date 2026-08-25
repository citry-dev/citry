import json
from pathlib import Path

from examples.tools.release_gate import validate_release_surfaces


def _write_fixture(root: Path, *, example_version: str = "0.4.4") -> dict:
    (root / "packages/py/citry").mkdir(parents=True)
    (root / "examples/starters/fastapi").mkdir(parents=True)
    (root / "docs_site/static/playground").mkdir(parents=True)
    (root / "packages/py/citry/pyproject.toml").write_text(
        '[project]\nname = "citry"\nversion = "0.4.4"\n', encoding="utf-8"
    )
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
        "citry": {"version": example_version},
        "packages": [{"name": "citry", "version": example_version, "url": wheel_url}],
    }
    root.joinpath("docs_site/static/playground/runtime.json").write_text(json.dumps(runtime), encoding="utf-8")
    return {
        "urls": [
            {
                "filename": "citry-0.4.4-py3-none-any.whl",
                "url": wheel_url,
                "digests": {"sha256": wheel_hash},
            }
        ]
    }


def test_release_surfaces_match_public_citry(tmp_path: Path) -> None:
    payload = _write_fixture(tmp_path)

    assert validate_release_surfaces(tmp_path, pypi_payload=payload) == []


def test_release_surfaces_reject_stale_examples_and_playground(tmp_path: Path) -> None:
    payload = _write_fixture(tmp_path, example_version="0.4.3")

    problems = validate_release_surfaces(tmp_path, pypi_payload=payload)

    assert any("manifest must set its minimum Citry version to 0.4.4" in item for item in problems)
    assert any("README must name Citry 0.4.4" in item for item in problems)
    assert any("lock must resolve Citry 0.4.4" in item for item in problems)
    assert any("playground: citry.version must be 0.4.4" in item for item in problems)
