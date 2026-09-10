"""Release jobs accept only the exact files verified by the publication job."""

from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from scripts.release_closeout import ReleaseCloseoutError, extract_closeout, main

COMMIT = "a" * 40
PAYLOAD = b"qualified wheel bytes"


def _files() -> dict[str, bytes]:
    return {
        "release-inventory.json": json.dumps(
            {
                "version": "0.5.0",
                "artifacts": [
                    {"name": "citry.whl", "bytes": len(PAYLOAD), "sha256": hashlib.sha256(PAYLOAD).hexdigest()}
                ],
            }
        ).encode(),
        "qualification-provenance.json": json.dumps({"head_sha": COMMIT}).encode(),
        "citry.whl": PAYLOAD,
    }


def _archive(tmp_path: Path, files: dict[str, bytes], extra: zipfile.ZipInfo | None = None) -> Path:
    path = tmp_path / "closeout.zip"
    with zipfile.ZipFile(path, "w") as target:
        for name, payload in files.items():
            target.writestr(name, payload)
        if extra is not None:
            target.writestr(extra, b"untrusted")
    return path


def _extract(path: Path, output: Path, digest: str | None = None) -> None:
    extract_closeout(
        archive=path,
        artifact_digest=digest or hashlib.sha256(path.read_bytes()).hexdigest(),
        release_commit=COMMIT,
        expected_version="0.5.0",
        output_dir=output,
    )


def test_extracts_exact_approved_files(tmp_path: Path) -> None:
    files = _files()
    archive = _archive(tmp_path, files)
    output = tmp_path / "assets"
    output.mkdir()
    _extract(archive, output, "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest())
    assert {path.name: path.read_bytes() for path in output.iterdir()} == files


@pytest.mark.parametrize("change", ["hash", "size", "commit", "version", "extra", "missing", "duplicate", "invalid"])
def test_rejects_changed_inventory_or_members(tmp_path: Path, change: str) -> None:
    files = _files()
    inventory = json.loads(files["release-inventory.json"])
    if change == "hash":
        files["citry.whl"] = b"x" * len(PAYLOAD)
    elif change == "size":
        inventory["artifacts"][0]["bytes"] += 1
    elif change == "commit":
        files["qualification-provenance.json"] = json.dumps({"head_sha": "b" * 40}).encode()
    elif change == "version":
        inventory["version"] = "0.6.0"
    elif change == "extra":
        files["unapproved.whl"] = b"extra"
    elif change == "missing":
        del files["citry.whl"]
    elif change == "duplicate":
        inventory["artifacts"] *= 2
    else:
        inventory["artifacts"][0]["bytes"] = True
    files["release-inventory.json"] = json.dumps(inventory).encode()
    archive = _archive(tmp_path, files)
    with pytest.raises(ReleaseCloseoutError):
        _extract(archive, tmp_path / "assets")
    assert not (tmp_path / "assets").exists()


@pytest.mark.parametrize("name", ["../outside", "/absolute", "nested/file", "back\\slash", "folder/", "-option.whl"])
def test_rejects_unsafe_names(tmp_path: Path, name: str) -> None:
    archive = _archive(tmp_path, _files(), zipfile.ZipInfo(name))
    with pytest.raises(ReleaseCloseoutError, match="unsafe"):
        _extract(archive, tmp_path / "assets")


@pytest.mark.parametrize("mode", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFDIR])
def test_rejects_nonregular_members(tmp_path: Path, mode: int) -> None:
    member = zipfile.ZipInfo("special.whl")
    member.create_system = 3
    member.external_attr = (mode | 0o600) << 16
    archive = _archive(tmp_path, _files(), member)
    with pytest.raises(ReleaseCloseoutError, match="unsafe"):
        _extract(archive, tmp_path / "assets")


def test_rejects_duplicate_zip_names(tmp_path: Path) -> None:
    with pytest.warns(UserWarning, match="Duplicate name"):
        archive = _archive(tmp_path, _files(), zipfile.ZipInfo("citry.whl"))
    with pytest.raises(ReleaseCloseoutError, match="duplicate"):
        _extract(archive, tmp_path / "assets")


def test_rejects_wrong_archive_digest(tmp_path: Path) -> None:
    archive = _archive(tmp_path, _files())
    with pytest.raises(ReleaseCloseoutError, match="archive digest"):
        _extract(archive, tmp_path / "assets", "0" * 64)


def test_corrupt_zip_fails_cli_without_creating_output(tmp_path: Path) -> None:
    archive = tmp_path / "broken.zip"
    archive.write_bytes(b"not a zip")
    output = tmp_path / "assets"
    assert (
        main(
            [
                "--archive",
                str(archive),
                "--artifact-digest",
                hashlib.sha256(archive.read_bytes()).hexdigest(),
                "--release-commit",
                COMMIT,
                "--version",
                "0.5.0",
                "--output-dir",
                str(output),
            ]
        )
        == 1
    )
    assert not output.exists()


def test_preserves_existing_output(tmp_path: Path) -> None:
    archive = _archive(tmp_path, _files())
    output = tmp_path / "assets"
    output.mkdir()
    marker = output / "existing"
    marker.write_text("keep")
    with pytest.raises(ReleaseCloseoutError, match="new or empty"):
        _extract(archive, output)
    assert marker.read_text() == "keep"


@pytest.mark.parametrize("verified", [False, True])
def test_vsix_requires_registry_verification(tmp_path: Path, verified: bool) -> None:
    files = _files()
    files["extension.vsix"] = files.pop("citry.whl")
    inventory = json.loads(files["release-inventory.json"])
    inventory["artifacts"][0]["name"] = "extension.vsix"
    files["release-inventory.json"] = json.dumps(inventory).encode()
    if verified:
        files["registry-verification.json"] = b'{"verified": true}'
    archive = _archive(tmp_path, files)
    output = tmp_path / "assets"
    if verified:
        _extract(archive, output)
        assert (output / "extension.vsix").read_bytes() == PAYLOAD
    else:
        with pytest.raises(ReleaseCloseoutError, match="require registry verification"):
            _extract(archive, output)
        assert not output.exists()
