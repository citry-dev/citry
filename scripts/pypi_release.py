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


def compare_public(expected: Mapping[str, str], public: Mapping[str, str]) -> str:
    """
    Classify the public files as "absent", "partial", or "complete" against the qualified ones.

    Raises:
        PyPIReleaseError: A public file is not in the qualified set, or has a
            different SHA-256 than the qualified file of the same name.

    """
    unexpected = sorted(set(public) - set(expected))
    changed = sorted(name for name in expected.keys() & public.keys() if expected[name] != public[name])
    # A file that differs from the qualified bytes can never be fixed by
    # uploading more files, because a registry never replaces a file. Stop and
    # name it, so a person decides what to do.
    if unexpected or changed:
        missing = sorted(set(expected) - set(public))
        raise PyPIReleaseError(
            "public registry bytes differ from qualification; "
            f"missing={missing}, unexpected={unexpected}, changed={changed}"
        )
    if not public:
        return "absent"
    return "complete" if public.keys() == expected.keys() else "partial"


def public_state(*, status: int, inventory: Mapping[str, Any], payload: Mapping[str, Any] | None) -> str:
    """Read PyPI's answer for one version and classify it with `compare_public`."""
    expected = _inventory_artifacts(inventory)
    if status == 404:
        if payload is not None:
            raise PyPIReleaseError("a 404 PyPI response must not include release metadata")
        return "absent"
    if status != 200 or payload is None:
        raise PyPIReleaseError(f"could not prove the PyPI release state; HTTP {status}")
    return compare_public(expected, _public_artifacts(payload))


def upload_required(
    *,
    status: int,
    inventory: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
    allow_partial: bool = False,
) -> bool:
    """Return whether to upload, accepting only absent, partial (when allowed), or byte-identical releases."""
    state = public_state(status=status, inventory=inventory, payload=payload)
    # The check after an upload must see every file, so when PyPI answers for
    # the version, anything short of the complete set (some files, or an empty
    # file list) is a failure there. Only the check before an upload lets a
    # partial set through.
    if status == 200 and state != "complete" and not allow_partial:
        missing = sorted(set(_inventory_artifacts(inventory)) - set(_public_artifacts(payload or {})))
        raise PyPIReleaseError(f"public PyPI release is missing qualified files: missing={missing}")
    return state != "complete"


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
    # Only the check before an upload passes this flag. A partial upload left by
    # an earlier attempt is then finished with skip-existing, and the strict
    # check after the upload proves every file.
    parser.add_argument("--allow-partial", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Check the public release and optionally expose the upload decision."""
    args = _parser().parse_args(argv)
    try:
        inventory = _load(args.inventory)
        payload = None if args.pypi_json is None else _load(args.pypi_json)
        state = public_state(status=args.status, inventory=inventory, payload=payload)
        publish = upload_required(
            status=args.status,
            inventory=inventory,
            payload=payload,
            allow_partial=args.allow_partial,
        )
    except PyPIReleaseError as error:
        sys.stderr.write(f"PyPI release error: {error}\n")
        return 1
    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as stream:
            stream.write(f"publish={'true' if publish else 'false'}\n")
            # The publish action skips files PyPI already holds only when an
            # earlier attempt left some there; a first upload sends every file.
            stream.write(f"skip_existing={'true' if state == 'partial' else 'false'}\n")
    messages = {
        "absent": "upload required\n",
        "partial": "upload required for the missing files; the files already public match\n",
        "complete": "public bytes already match\n",
    }
    sys.stdout.write(messages[state])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
