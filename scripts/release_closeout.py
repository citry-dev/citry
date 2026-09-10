"""Verify publisher files before attaching them to a GitHub Release."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import stat
import sys
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


class ReleaseCloseoutError(ValueError):
    """The downloaded files do not match the publication job's verified archive."""


def _object(data: bytes, name: str) -> dict[str, Any]:
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ReleaseCloseoutError(f"{name} must contain an object")
    return value


def extract_closeout(
    *, archive: Path, artifact_digest: str, release_commit: str, expected_version: str, output_dir: Path
) -> None:
    """Check the complete archive, then write its files to an empty directory."""
    digest = artifact_digest.removeprefix("sha256:")
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ReleaseCloseoutError("artifact digest must be a SHA256 hash")
    if re.fullmatch(r"[0-9a-f]{40}", release_commit) is None:
        raise ReleaseCloseoutError("release commit must be a full commit SHA")
    if not expected_version:
        raise ReleaseCloseoutError("expected version must not be empty")
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ReleaseCloseoutError("archive digest does not match the publisher output")
    files: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as source:
        for member in source.infolist():
            name = member.filename
            kind = stat.S_IFMT(member.external_attr >> 16)
            if (
                re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.+-]*", name) is None
                or name != member.orig_filename
                or name in files
                or member.is_dir()
                or kind not in (0, stat.S_IFREG)
            ):
                raise ReleaseCloseoutError(f"archive contains an unsafe or duplicate member: {name!r}")
            files[name] = source.read(member)
    metadata = {"release-inventory.json", "qualification-provenance.json"}
    if not metadata <= files.keys():
        raise ReleaseCloseoutError("archive is missing release metadata")
    inventory = _object(files["release-inventory.json"], "release inventory")
    provenance = _object(files["qualification-provenance.json"], "qualification provenance")
    if inventory.get("version") != expected_version:
        raise ReleaseCloseoutError("inventory version does not match the requested release")
    if provenance.get("head_sha") != release_commit:
        raise ReleaseCloseoutError("qualification commit does not match the requested release")
    artifacts = inventory.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ReleaseCloseoutError("inventory must contain a nonempty artifacts list")
    expected: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ReleaseCloseoutError("inventory artifact must be an object")
        artifact_name = artifact.get("name")
        size = artifact.get("bytes")
        checksum = artifact.get("sha256")
        if (
            not isinstance(artifact_name, str)
            or not artifact_name.endswith((".whl", ".tar.gz", ".vsix"))
            or artifact_name in expected
            or artifact_name not in files
            or type(size) is not int
            or size < 0
            or not isinstance(checksum, str)
            or re.fullmatch(r"[0-9a-f]{64}", checksum) is None
        ):
            raise ReleaseCloseoutError("inventory contains an invalid or duplicate artifact")
        payload = files[artifact_name]
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != checksum:
            raise ReleaseCloseoutError(f"artifact bytes do not match the inventory: {artifact_name}")
        expected.add(artifact_name)
    if any(name.endswith(".vsix") for name in expected) and "registry-verification.json" not in files:
        raise ReleaseCloseoutError("VSIX releases require registry verification")
    if "registry-verification.json" in files:
        if not all(name.endswith(".vsix") for name in expected):
            raise ReleaseCloseoutError("registry verification is only supported for VSIX releases")
        _object(files["registry-verification.json"], "registry verification")
        metadata.add("registry-verification.json")
    if files.keys() != expected | metadata:
        raise ReleaseCloseoutError("archive contains files outside the release inventory")
    if output_dir.is_symlink() or (output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir()))):
        raise ReleaseCloseoutError("output directory must be new or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in files.items():
        with (output_dir / name).open("xb") as destination:
            destination.write(payload)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the archive supplied by the publisher job."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--release-commit", required=True)
    parser.add_argument("--version", dest="expected_version", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        extract_closeout(**vars(args))
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        sys.stderr.write(f"Release closeout error: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
