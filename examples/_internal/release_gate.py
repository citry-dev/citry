"""Validate example compatibility and portable playground release coordinates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import InvalidVersion, Version

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by the Python 3.10 CI leg
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPI_REGISTRY = "https://pypi.org/simple"
PYPI_FILES_HOST = "files.pythonhosted.org"


def _project_version(repo_root: Path) -> str:
    manifest = tomllib.loads((repo_root / "packages/py/citry/pyproject.toml").read_text(encoding="utf-8"))
    version = manifest.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("Citry's package manifest has no project.version")
    return version


def _public_artifacts(payload: dict[str, Any]) -> dict[str, tuple[str, str]]:
    artifacts: dict[str, tuple[str, str]] = {}
    for item in payload.get("urls", []):
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        url = item.get("url")
        digests = item.get("digests")
        sha256 = digests.get("sha256") if isinstance(digests, dict) else None
        if isinstance(filename, str) and isinstance(url, str) and isinstance(sha256, str):
            artifacts[filename] = (url, sha256)
    return artifacts


def _artifact_problem(
    artifact: dict[str, Any],
    *,
    owner: str,
    public_artifacts: dict[str, tuple[str, str]] | None,
    require_digest: bool = True,
) -> str | None:
    url = artifact.get("url")
    digest = artifact.get("hash")
    if not isinstance(url, str) or urlparse(url).hostname != PYPI_FILES_HOST:
        return f"{owner} does not use an immutable files.pythonhosted.org URL"
    if public_artifacts is None:
        return None
    filename = url.rsplit("/", 1)[-1]
    public = public_artifacts.get(filename)
    if public is None:
        return f"{owner} names {filename!r}, which is absent from the public PyPI release"
    if public[0] != url or (require_digest and digest != f"sha256:{public[1]}"):
        return f"{owner} URL or SHA-256 differs from the public PyPI artifact"
    return None


def _runtime_artifact_problem(
    artifact: dict[str, Any],
    *,
    owner: str,
    public_artifacts: dict[str, tuple[str, str]] | None,
) -> str | None:
    filename = artifact.get("filename")
    digest = artifact.get("sha256")
    if artifact.get("source") != "pypi":
        return f"{owner} must resolve an exact PyPI artifact"
    if not isinstance(filename, str) or not filename or "/" in filename:
        return f"{owner} has an invalid filename"
    if not isinstance(digest, str) or len(digest) != 64:
        return f"{owner} has an invalid SHA-256 digest"
    try:
        int(digest, 16)
    except ValueError:
        return f"{owner} has an invalid SHA-256 digest"
    if public_artifacts is None:
        return None
    public = public_artifacts.get(filename)
    if public is None:
        return f"{owner} names {filename!r}, which is absent from the public PyPI release"
    if public[1] != digest:
        return f"{owner} SHA-256 differs from the public PyPI artifact"
    return None


def _citry_requirement(dependencies: Any) -> tuple[Requirement | None, str | None]:
    requirements: list[Requirement] = []
    for raw in dependencies if isinstance(dependencies, list) else []:
        if not isinstance(raw, str):
            continue
        try:
            requirement = Requirement(raw)
        except InvalidRequirement:
            continue
        if requirement.name.lower().replace("_", "-") == "citry":
            requirements.append(requirement)
    if len(requirements) != 1:
        return None, "manifest must declare exactly one Citry dependency"
    return requirements[0], None


def validate_release_surfaces(
    repo_root: Path = REPO_ROOT,
    *,
    pypi_payload: dict[str, Any] | None = None,
    core_pypi_payload: dict[str, Any] | None = None,
) -> list[str]:
    """Return every example compatibility or playground coordinate mismatch."""
    problems: list[str] = []
    version = _project_version(repo_root)
    public_artifacts = None if pypi_payload is None else _public_artifacts(pypi_payload)
    core_public_artifacts = None if core_pypi_payload is None else _public_artifacts(core_pypi_payload)
    catalog = tomllib.loads((repo_root / "examples/catalog.toml").read_text(encoding="utf-8"))

    for entry in catalog.get("projects", []):
        project_id = entry.get("id", "<unknown>")
        project_root = repo_root / "examples" / entry["path"]
        manifest = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
        requirement, requirement_problem = _citry_requirement(manifest.get("project", {}).get("dependencies"))
        if requirement_problem is not None:
            problems.append(f"{project_id}: {requirement_problem}")

        lock = tomllib.loads((project_root / "uv.lock").read_text(encoding="utf-8"))
        locked = [package for package in lock.get("package", []) if package.get("name") == "citry"]
        if len(locked) != 1:
            problems.append(f"{project_id}: lock must contain exactly one Citry package")
            continue
        citry = locked[0]
        locked_version = citry.get("version")
        if citry.get("source") != {"registry": PYPI_REGISTRY}:
            problems.append(f"{project_id}: lock must resolve Citry from {PYPI_REGISTRY}")
        if requirement is not None:
            try:
                compatible = isinstance(locked_version, str) and Version(locked_version) in requirement.specifier
            except InvalidVersion:
                compatible = False
            if not compatible:
                problems.append(f"{project_id}: locked Citry {locked_version!r} does not satisfy {requirement}")
        artifacts = [citry.get("sdist"), *citry.get("wheels", [])]
        artifacts = [artifact for artifact in artifacts if isinstance(artifact, dict)]
        if not artifacts:
            problems.append(f"{project_id}: lock contains no immutable Citry artifacts")
        for artifact in artifacts:
            problem = _artifact_problem(
                artifact,
                owner=f"{project_id}: locked Citry artifact",
                # An example lock may deliberately remain on an older compatible
                # Citry release, so its own immutable PyPI coordinates are enough.
                public_artifacts=None,
            )
            if problem is not None:
                problems.append(problem)

    runtime = json.loads((repo_root / "docs_site/static/playground/runtime.json").read_text(encoding="utf-8"))
    runtime_citry = runtime.get("citry", {})
    runtime_packages = runtime.get("packages", [])
    if runtime_citry.get("version") != version:
        problems.append(f"playground: citry.version must be {version}")
    packages = [package for package in runtime_packages if package.get("name") == "citry"]
    if len(packages) != 1 or packages[0].get("version") != version:
        problems.append(f"playground: packages must contain Citry {version} exactly once")
    elif (
        problem := _runtime_artifact_problem(
            packages[0],
            owner="playground: Citry wheel",
            public_artifacts=public_artifacts,
        )
    ) is not None:
        problems.append(problem)

    build = json.loads((repo_root / "packages/py/citry_core/pyodide-build.json").read_text(encoding="utf-8"))
    pyodide = runtime.get("pyodide", {})
    if pyodide.get("version") != build.get("pyodide") or pyodide.get("python") != build.get("python"):
        problems.append("playground: Pyodide and Python versions must match citry-core's browser build tuple")

    core_version = runtime_citry.get("core_version")
    core_packages = [package for package in runtime_packages if package.get("name") == "citry-core"]
    if not isinstance(core_version, str) or len(core_packages) != 1 or core_packages[0].get("version") != core_version:
        problems.append("playground: citry.core_version must match exactly one citry-core package")
    else:
        expected_core_wheel = (
            f"citry_core-{core_version}-{build['python_tag']}-{build['abi_tag']}-{build['platform_tag']}.whl"
        )
        if core_packages[0].get("filename") != expected_core_wheel:
            problems.append("playground: citry-core wheel must match the pinned Python and PyEmscripten ABI")
        elif (
            problem := _runtime_artifact_problem(
                core_packages[0],
                owner="playground: Citry Core wheel",
                public_artifacts=core_public_artifacts,
            )
        ) is not None:
            problems.append(problem)

    ui_version = runtime_citry.get("ui_version")
    ui_packages = [package for package in runtime_packages if package.get("name") == "citry-ui"]
    if not isinstance(ui_version, str) or len(ui_packages) != 1 or ui_packages[0].get("version") != ui_version:
        problems.append("playground: citry.ui_version must match exactly one citry-ui package")
    elif (
        problem := _runtime_artifact_problem(
            ui_packages[0],
            owner="playground: Citry UI wheel",
            public_artifacts=None,
        )
    ) is not None:
        problems.append(problem)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pypi-json", type=Path)
    parser.add_argument("--core-pypi-json", type=Path)
    args = parser.parse_args()
    payload = None
    core_payload = None
    if args.pypi_json is not None:
        payload = json.loads(args.pypi_json.read_text(encoding="utf-8"))
    if args.core_pypi_json is not None:
        core_payload = json.loads(args.core_pypi_json.read_text(encoding="utf-8"))
    problems = validate_release_surfaces(pypi_payload=payload, core_pypi_payload=core_payload)
    if problems:
        for problem in problems:
            print(f"release surface error: {problem}")
        return 1
    print("Citry examples remain compatible and the playground uses exact package coordinates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
