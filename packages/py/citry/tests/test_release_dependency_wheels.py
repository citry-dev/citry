"""Contracts for native candidate dependencies used by release smoke matrices."""

from pathlib import Path

import yaml  # type: ignore[import-untyped]

_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKFLOWS = _REPO_ROOT / ".github" / "workflows"


def test_multi_version_cpython_smokes_build_selected_core_as_abi3() -> None:
    checked: set[str] = set()

    for path in _WORKFLOWS.glob("py--*-publish.yml"):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        jobs = workflow["jobs"]
        smoke = jobs.get("smoke-python")
        if smoke is None:
            continue
        versions = smoke.get("strategy", {}).get("matrix", {}).get("python-version", [])
        if len(versions) < 2:
            continue

        core_builds = [
            step["run"]
            for step in jobs["build"]["steps"]
            if "uv build --package citry-core --wheel" in step.get("run", "")
        ]
        if not core_builds:
            continue

        build_pythons = [
            step["with"]["python-version"]
            for step in jobs["build"]["steps"]
            if step.get("uses") == "actions/setup-python@v7"
        ]
        assert versions == ["3.10", "3.11", "3.12", "3.13", "3.14"], path.name
        assert build_pythons == ["3.14"], path.name
        assert len(core_builds) == 1, path.name
        assert "--config-setting 'maturin.build-args=--features abi3-py310'" in core_builds[0], path.name
        checked.add(path.name)

    assert checked == {
        "py--citry--publish.yml",
        "py--citry-lsp--publish.yml",
        "py--citry-ui--publish.yml",
    }
