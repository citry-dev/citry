"""Validate the version-locked example and playground surfaces for a Citry tag."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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


def validate_release_surfaces(
    repo_root: Path = REPO_ROOT,
    *,
    pypi_payload: dict[str, Any] | None = None,
) -> list[str]:
    """Return every release-coupled version or public-artifact mismatch."""
    problems: list[str] = []
    version = _project_version(repo_root)
    public_artifacts = None if pypi_payload is None else _public_artifacts(pypi_payload)
    catalog = tomllib.loads((repo_root / "examples/catalog.toml").read_text(encoding="utf-8"))

    for entry in catalog.get("projects", []):
        project_id = entry.get("id", "<unknown>")
        project_root = repo_root / "examples" / entry["path"]
        manifest = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
        citry_requirements = [
            dependency
            for dependency in manifest.get("project", {}).get("dependencies", [])
            if isinstance(dependency, str) and dependency.startswith("citry")
        ]
        if len(citry_requirements) != 1 or not citry_requirements[0].startswith(f"citry>={version},"):
            problems.append(f"{project_id}: manifest must set its minimum Citry version to {version}")

        readme = (project_root / "README.md").read_text(encoding="utf-8")
        if f"Citry {version}" not in readme:
            problems.append(f"{project_id}: README must name Citry {version}")

        lock = tomllib.loads((project_root / "uv.lock").read_text(encoding="utf-8"))
        locked = [package for package in lock.get("package", []) if package.get("name") == "citry"]
        if len(locked) != 1:
            problems.append(f"{project_id}: lock must contain exactly one Citry package")
            continue
        citry = locked[0]
        if citry.get("version") != version or citry.get("source") != {"registry": PYPI_REGISTRY}:
            problems.append(f"{project_id}: lock must resolve Citry {version} from {PYPI_REGISTRY}")
        artifacts = [citry.get("sdist"), *citry.get("wheels", [])]
        artifacts = [artifact for artifact in artifacts if isinstance(artifact, dict)]
        if not artifacts:
            problems.append(f"{project_id}: lock contains no immutable Citry artifacts")
        for artifact in artifacts:
            problem = _artifact_problem(
                artifact,
                owner=f"{project_id}: locked Citry artifact",
                public_artifacts=public_artifacts,
            )
            if problem is not None:
                problems.append(problem)

    runtime = json.loads((repo_root / "docs_site/static/playground/runtime.json").read_text(encoding="utf-8"))
    if runtime.get("citry", {}).get("version") != version:
        problems.append(f"playground: citry.version must be {version}")
    packages = [package for package in runtime.get("packages", []) if package.get("name") == "citry"]
    if len(packages) != 1 or packages[0].get("version") != version:
        problems.append(f"playground: packages must contain Citry {version} exactly once")
    elif (
        problem := _artifact_problem(
            packages[0],
            owner="playground: Citry wheel",
            public_artifacts=public_artifacts,
            require_digest=False,
        )
    ) is not None:
        problems.append(problem)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pypi-json", type=Path)
    args = parser.parse_args()
    payload = None
    if args.pypi_json is not None:
        payload = json.loads(args.pypi_json.read_text(encoding="utf-8"))
    problems = validate_release_surfaces(pypi_payload=payload)
    if problems:
        for problem in problems:
            print(f"release surface error: {problem}")
        return 1
    print("Citry release examples and playground match the public package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
