"""Copy a generated release artifact into its two permitted repository paths."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from scripts.verify_playground_release import PlaygroundReleaseError, validate_published_runtime


def apply_update(source: Path, repository: Path) -> None:
    """Reject unexpected paths before replacing the snapshot tree and runtime."""
    if source.is_symlink() or not source.is_dir():
        raise ValueError("release site artifact must be a directory")
    runtime = Path("static/playground/runtime.json")
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"release site artifact contains a non-regular path: {relative}")
        allowed = (
            relative.parts[0] == "versions" or relative == runtime or (path.is_dir() and relative in runtime.parents)
        )
        if not allowed:
            raise ValueError(f"release site artifact contains an unexpected path: {relative}")
    if not (source / "versions/versions.json").is_file() or not (source / runtime).is_file():
        raise ValueError("release site artifact must contain versions.json and runtime.json")
    try:
        runtime_manifest = json.loads((source / runtime).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"release site runtime.json is invalid: {error}") from error
    try:
        validate_published_runtime(runtime_manifest)
    except PlaygroundReleaseError as error:
        raise ValueError(f"release site runtime.json is not publishable: {error}") from error
    destination = repository / "docs_site"
    # The checkout is fresh and its SHA must match the generation job's base.
    # Replacing this directory also preserves deletions made by build-tag.
    shutil.rmtree(destination / "versions")
    shutil.copytree(source / "versions", destination / "versions")
    shutil.copyfile(source / runtime, destination / runtime)


def main() -> None:
    """Apply files downloaded from this workflow's successful generation job."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    apply_update(args.source, Path.cwd())


if __name__ == "__main__":
    main()
