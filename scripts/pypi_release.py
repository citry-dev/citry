"""Decide whether PyPI needs an upload and reject different public bytes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class PyPIReleaseError(ValueError):
    """The public PyPI state cannot be recovered safely."""


def _inventory_artifacts(inventory: Mapping[str, Any]) -> dict[str, str]:
    artifacts = inventory.get("artifacts")
    if not isinstance(artifacts, list):
        raise PyPIReleaseError("release inventory has no artifacts list")
    result: dict[str, str] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise PyPIReleaseError("release inventory contains a non-object artifact")
        name = artifact.get("name")
        digest = artifact.get("sha256")
        if not isinstance(name, str) or not isinstance(digest, str) or len(digest) != 64:
            raise PyPIReleaseError("release inventory contains an invalid artifact identity")
        result[name] = digest
    if len(result) != len(artifacts):
        raise PyPIReleaseError("release inventory contains duplicate artifact names")
    return result


def _public_artifacts(payload: Mapping[str, Any]) -> dict[str, str]:
    urls = payload.get("urls")
    if not isinstance(urls, list):
        raise PyPIReleaseError("PyPI response has no urls list")
    result: dict[str, str] = {}
    for artifact in urls:
        if not isinstance(artifact, dict):
            continue
        name = artifact.get("filename")
        digests = artifact.get("digests")
        digest = digests.get("sha256") if isinstance(digests, dict) else None
        if isinstance(name, str) and isinstance(digest, str):
            result[name] = digest
    return result


def upload_required(*, status: int, inventory: Mapping[str, Any], payload: Mapping[str, Any] | None) -> bool:
    """Return whether to upload, accepting only absent or byte-identical releases."""
    expected = _inventory_artifacts(inventory)
    if status == 404:
        if payload is not None:
            raise PyPIReleaseError("a 404 PyPI response must not include release metadata")
        return True
    if status != 200 or payload is None:
        raise PyPIReleaseError(f"could not prove the PyPI release state; HTTP {status}")
    public = _public_artifacts(payload)
    if public != expected:
        missing = sorted(set(expected) - set(public))
        unexpected = sorted(set(public) - set(expected))
        changed = sorted(name for name in expected.keys() & public.keys() if expected[name] != public[name])
        raise PyPIReleaseError(
            "public PyPI bytes differ from qualification; "
            f"missing={missing}, unexpected={unexpected}, changed={changed}"
        )
    return False


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PyPIReleaseError(f"could not read {path}: {error}") from error
    if not isinstance(value, dict):
        raise PyPIReleaseError(f"{path} must contain an object")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", type=int, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--pypi-json", type=Path)
    parser.add_argument("--github-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Check the public release and optionally expose the upload decision."""
    args = _parser().parse_args(argv)
    try:
        publish = upload_required(
            status=args.status,
            inventory=_load(args.inventory),
            payload=None if args.pypi_json is None else _load(args.pypi_json),
        )
    except PyPIReleaseError as error:
        sys.stderr.write(f"PyPI release error: {error}\n")
        return 1
    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as stream:
            stream.write(f"publish={'true' if publish else 'false'}\n")
    sys.stdout.write("upload required\n" if publish else "public bytes already match\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
