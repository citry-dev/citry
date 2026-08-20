"""Inspect, stage, and promote the exact Citry VS Code extension artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import struct
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Final
from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from collections.abc import Sequence

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
PACKAGE_ROOT: Final = REPO_ROOT / "packages" / "editors" / "vscode"
MAX_VSIX_BYTES: Final = 1024 * 1024
MAX_UNCOMPRESSED_BYTES: Final = 2 * 1024 * 1024
EXPECTED_ID: Final = "citry-dev.citry"
EXPECTED_ENGINE: Final = "^1.101.0"


class DistributionVerificationError(RuntimeError):
    """The VSIX differs from the checked source or release contract."""


def sha256_bytes(value: bytes) -> str:
    """Return one lowercase SHA-256 digest."""
    return hashlib.sha256(value).hexdigest()


def package_manifest() -> dict[str, Any]:
    """Read the checked extension manifest."""
    try:
        payload: Any = json.loads((PACKAGE_ROOT / "package.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DistributionVerificationError(f"cannot read extension package.json: {error}") from error
    if not isinstance(payload, dict):
        raise DistributionVerificationError("extension package.json must contain one object")
    return payload


def package_version() -> str:
    """Return the release version declared by package.json."""
    version = package_manifest().get("version")
    if not isinstance(version, str) or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        raise DistributionVerificationError(f"extension package.json has invalid version {version!r}")
    return version


def expected_vsix_name(version: str) -> str:
    """Return the one accepted release filename."""
    return f"citry-dev.citry-{version}.vsix"


def source_members() -> dict[str, Path]:
    """Map every source-owned VSIX member to its checked repository file."""
    relative = {
        "extension/package.json": "package.json",
        "extension/language-configuration.json": "language-configuration.json",
        "extension/fluent-language-configuration.json": "fluent-language-configuration.json",
        "extension/readme.md": "README.md",
        "extension/LICENSE.txt": "LICENSE",
        "extension/changelog.md": "CHANGELOG.md",
        "extension/SUPPORT.md": "SUPPORT.md",
        "extension/syntaxes/fluent.tmLanguage.json": "syntaxes/fluent.tmLanguage.json",
        "extension/syntaxes/citry-python.injection.tmLanguage.json": "syntaxes/citry-python.injection.tmLanguage.json",
        "extension/syntaxes/citry-html.tmLanguage.json": "syntaxes/citry-html.tmLanguage.json",
        "extension/syntaxes/citry-html.injection.tmLanguage.json": "syntaxes/citry-html.injection.tmLanguage.json",
        "extension/syntaxes/citry-html-attributes.injection.tmLanguage.json": (
            "syntaxes/citry-html-attributes.injection.tmLanguage.json"
        ),
        "extension/images/icon.png": "images/icon.png",
        "extension/out/extension.js": "out/extension.js",
    }
    return {member: PACKAGE_ROOT / path for member, path in relative.items()}


def expected_members() -> set[str]:
    """Return the complete closed VSIX member set."""
    return {"extension.vsixmanifest", "[Content_Types].xml", *source_members()}


def _safe_archive_name(name: str, *, artifact: Path) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        raise DistributionVerificationError(f"{artifact.name} contains unsafe member {name!r}")
    return path


def _require_regular_members(archive: zipfile.ZipFile, *, artifact: Path) -> list[zipfile.ZipInfo]:
    bad_member = archive.testzip()
    if bad_member is not None:
        raise DistributionVerificationError(f"{artifact.name} has corrupt member {bad_member!r}")
    entries = [entry for entry in archive.infolist() if not entry.is_dir()]
    names = [entry.filename for entry in entries]
    if len(names) != len(set(names)):
        raise DistributionVerificationError(f"{artifact.name} contains duplicate member names")
    for entry in entries:
        _safe_archive_name(entry.filename, artifact=artifact)
        if stat.S_ISLNK(entry.external_attr >> 16):
            raise DistributionVerificationError(f"{artifact.name} contains a symbolic link")
    return entries


def _require_package_json(payload: bytes, *, version: str) -> None:
    try:
        manifest: Any = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DistributionVerificationError(f"VSIX package.json is invalid: {error}") from error
    expected = package_manifest()
    if manifest != expected:
        raise DistributionVerificationError("VSIX package.json differs from the checked release manifest")
    if manifest.get("publisher") != "citry-dev" or manifest.get("name") != "citry":
        raise DistributionVerificationError("VSIX package.json has an unexpected extension identity")
    if manifest.get("version") != version:
        raise DistributionVerificationError("VSIX package.json has an unexpected version")
    if manifest.get("engines", {}).get("vscode") != EXPECTED_ENGINE:
        raise DistributionVerificationError("VSIX package.json has an unexpected VS Code floor")
    if manifest.get("main") != "./out/extension.js" or manifest.get("browser") is not None:
        raise DistributionVerificationError("VSIX must be a desktop/remote workspace extension")
    if manifest.get("extensionKind") != ["workspace"]:
        raise DistributionVerificationError("VSIX extensionKind must remain workspace-only")
    if set(manifest.get("categories", [])) != {"Programming Languages", "Formatters", "Linters"}:
        raise DistributionVerificationError("VSIX marketplace categories differ from the release contract")
    if manifest.get("pricing") != "Free":
        raise DistributionVerificationError("VSIX marketplace pricing must be explicit and free")
    expected_listing = {
        "icon": "images/icon.png",
        "repository": {
            "type": "git",
            "url": "https://github.com/citry-dev/citry.git",
            "directory": "packages/editors/vscode",
        },
        "homepage": "https://citry.dev/ide/vscode/",
        "bugs": {"url": "https://github.com/citry-dev/citry/issues"},
        "qna": "https://github.com/citry-dev/citry/discussions",
        "sponsor": {"url": "https://github.com/sponsors/JuroOravec"},
    }
    for field, expected_value in expected_listing.items():
        if manifest.get(field) != expected_value:
            raise DistributionVerificationError(f"VSIX package.json has an unexpected {field!r} listing value")


def _require_vsix_manifest(payload: bytes, *, version: str) -> None:
    try:
        # The closed archive contract caps the complete expanded VSIX at 2 MiB,
        # and this generated member is compared structurally below. Stdlib XML
        # keeps the release verifier dependency-free on clean GitHub runners.
        root = ET.fromstring(payload)  # noqa: S314
    except ET.ParseError as error:
        raise DistributionVerificationError(f"extension.vsixmanifest is invalid XML: {error}") from error
    namespace = {"v": "http://schemas.microsoft.com/developer/vsx-schema/2011"}
    identity = root.find("v:Metadata/v:Identity", namespace)
    if identity is None:
        raise DistributionVerificationError("extension.vsixmanifest has no Identity")
    expected_identity = {"Id": "citry", "Version": version, "Publisher": "citry-dev", "Language": "en-US"}
    if any(identity.get(name) != value for name, value in expected_identity.items()):
        raise DistributionVerificationError("extension.vsixmanifest identity differs from package.json")
    target = root.find("v:Installation/v:InstallationTarget", namespace)
    if target is None or target.get("Id") != "Microsoft.VisualStudio.Code":
        raise DistributionVerificationError("extension.vsixmanifest has an unexpected installation target")
    properties = {
        node.get("Id"): node.get("Value") for node in root.findall("v:Metadata/v:Properties/v:Property", namespace)
    }
    if properties.get("Microsoft.VisualStudio.Code.Engine") != EXPECTED_ENGINE:
        raise DistributionVerificationError("extension.vsixmanifest has an unexpected VS Code floor")
    if properties.get("Microsoft.VisualStudio.Code.ExtensionKind") != "workspace":
        raise DistributionVerificationError("extension.vsixmanifest is not workspace-only")
    if properties.get("Microsoft.VisualStudio.Code.ExecutesCode") != "true":
        raise DistributionVerificationError("extension.vsixmanifest does not declare executable code")
    if properties.get("Microsoft.VisualStudio.Services.Content.Pricing") != "Free":
        raise DistributionVerificationError("extension.vsixmanifest does not declare free pricing")
    expected_listing = {
        "Microsoft.VisualStudio.Code.SponsorLink": "https://github.com/sponsors/JuroOravec",
        "Microsoft.VisualStudio.Services.Links.Source": "https://github.com/citry-dev/citry.git",
        "Microsoft.VisualStudio.Services.Links.Support": "https://github.com/citry-dev/citry/issues",
        "Microsoft.VisualStudio.Services.Links.Learn": "https://citry.dev/ide/vscode/",
        "Microsoft.VisualStudio.Services.CustomerQnALink": "https://github.com/citry-dev/citry/discussions",
    }
    for field, expected_value in expected_listing.items():
        if properties.get(field) != expected_value:
            raise DistributionVerificationError(f"extension.vsixmanifest has an unexpected {field!r} value")
    metadata = root.find("v:Metadata", namespace)
    if metadata is None:
        raise DistributionVerificationError("extension.vsixmanifest has no Metadata")
    icon = metadata.find("v:Icon", namespace)
    if icon is None or icon.text != "extension/images/icon.png":
        raise DistributionVerificationError("extension.vsixmanifest does not expose the packaged PNG icon")


def _require_icon(payload: bytes) -> None:
    if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise DistributionVerificationError("extension icon is not a valid PNG header")
    width, height = struct.unpack(">II", payload[16:24])
    if width < 128 or height < 128:
        raise DistributionVerificationError(f"extension icon is only {width}x{height}; registries require 128x128+")


def _require_no_local_paths(member: str, payload: bytes) -> None:
    if Path(member).suffix.lower() not in {".js", ".json", ".md", ".txt", ".xml", ".vsixmanifest"}:
        return
    forbidden = (b"/Users/", b"/home/runner/work/", b"file:///", b"C:\\\\")
    if any(value in payload for value in forbidden):
        raise DistributionVerificationError(f"{member} contains an absolute build-machine path")


def verify_vsix(path: Path, *, version: str | None = None) -> dict[str, Any]:
    """Verify one closed, source-matched universal VSIX."""
    version = package_version() if version is None else version
    if path.name != expected_vsix_name(version):
        raise DistributionVerificationError(f"expected VSIX {expected_vsix_name(version)!r}, found {path.name!r}")
    payload = path.read_bytes()
    if len(payload) > MAX_VSIX_BYTES:
        raise DistributionVerificationError(
            f"{path.name} is {len(payload)} bytes; the release cap is {MAX_VSIX_BYTES} bytes"
        )
    try:
        with zipfile.ZipFile(path) as archive:
            entries = _require_regular_members(archive, artifact=path)
            names = {entry.filename for entry in entries}
            expected = expected_members()
            if names != expected:
                raise DistributionVerificationError(
                    f"VSIX inventory mismatch; missing={sorted(expected - names)!r}; "
                    f"unexpected={sorted(names - expected)!r}"
                )
            uncompressed = sum(entry.file_size for entry in entries)
            if uncompressed > MAX_UNCOMPRESSED_BYTES:
                raise DistributionVerificationError(
                    f"{path.name} expands to {uncompressed} bytes; cap is {MAX_UNCOMPRESSED_BYTES} bytes"
                )
            by_name = {entry.filename: archive.read(entry) for entry in entries}
    except zipfile.BadZipFile as error:
        raise DistributionVerificationError(f"{path.name} is not a valid VSIX: {error}") from error

    for member, source in source_members().items():
        if not source.is_file():
            raise DistributionVerificationError(f"checked VSIX source is missing: {source.relative_to(REPO_ROOT)}")
        if by_name[member] != source.read_bytes():
            raise DistributionVerificationError(f"{member} differs from {source.relative_to(REPO_ROOT).as_posix()}")
    _require_package_json(by_name["extension/package.json"], version=version)
    _require_vsix_manifest(by_name["extension.vsixmanifest"], version=version)
    _require_icon(by_name["extension/images/icon.png"])
    for member, member_payload in by_name.items():
        _require_no_local_paths(member, member_payload)
    if b"0.1.0 - Unreleased" in by_name["extension/changelog.md"]:
        raise DistributionVerificationError("release changelog is still marked Unreleased")

    return {
        "name": path.name,
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "uncompressed_bytes": sum(len(value) for value in by_name.values()),
        "members": sorted(by_name),
    }


def _release_report(path: Path) -> dict[str, Any]:
    return {"version": package_version(), "artifacts": [verify_vsix(path)]}


def _require_empty_output(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise DistributionVerificationError(f"output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def stage_qualification(path: Path, output_dir: Path) -> dict[str, Any]:
    """Copy only the verified VSIX and its exact-byte inventory."""
    report = _release_report(path)
    _require_empty_output(output_dir)
    shutil.copy2(path, output_dir / path.name)
    (output_dir / "release-inventory.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_staged_bundle(bundle_dir: Path) -> dict[str, Any]:
    """Re-verify a flat qualification bundle against the tagged checkout."""
    if not bundle_dir.is_dir():
        raise DistributionVerificationError(f"qualification bundle is not a directory: {bundle_dir}")
    entries = sorted(bundle_dir.iterdir())
    if any(entry.is_symlink() or not entry.is_file() for entry in entries):
        raise DistributionVerificationError("qualification bundle must contain only regular root files")
    version = package_version()
    expected_names = {expected_vsix_name(version), "release-inventory.json"}
    by_name = {entry.name: entry for entry in entries}
    if set(by_name) != expected_names:
        raise DistributionVerificationError(
            f"qualification bundle mismatch; missing={sorted(expected_names - set(by_name))!r}; "
            f"unexpected={sorted(set(by_name) - expected_names)!r}"
        )
    report = _release_report(by_name[expected_vsix_name(version)])
    try:
        recorded: Any = json.loads(by_name["release-inventory.json"].read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DistributionVerificationError(f"cannot read release-inventory.json: {error}") from error
    if recorded != report:
        raise DistributionVerificationError("release-inventory.json does not match the qualified VSIX bytes")
    return report


def promote_qualification_archive(
    archive_path: Path,
    *,
    expected_digest: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Check GitHub's artifact digest, safely extract, and verify the bundle."""
    match = re.fullmatch(r"sha256:([0-9a-f]{64})", expected_digest)
    if match is None:
        raise DistributionVerificationError(f"invalid qualification artifact digest: {expected_digest!r}")
    if sha256_bytes(archive_path.read_bytes()) != match.group(1):
        raise DistributionVerificationError("qualification archive SHA-256 differs from GitHub's digest")
    _require_empty_output(output_dir)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = _require_regular_members(archive, artifact=archive_path)
            for entry in entries:
                member = _safe_archive_name(entry.filename, artifact=archive_path)
                if len(member.parts) != 1:
                    raise DistributionVerificationError(
                        f"qualification archive member must be a root file: {entry.filename!r}"
                    )
                (output_dir / entry.filename).write_bytes(archive.read(entry))
    except zipfile.BadZipFile as error:
        raise DistributionVerificationError(f"qualification artifact is not a valid zip: {error}") from error
    return verify_staged_bundle(output_dir)


def _unique_vsix(dist_dir: Path) -> Path:
    expected = expected_vsix_name(package_version())
    matches = sorted(path for path in dist_dir.glob("*.vsix") if path.is_file())
    if [path.name for path in matches] != [expected]:
        raise DistributionVerificationError(
            f"expected only {expected!r} in {dist_dir}; found {[path.name for path in matches]!r}"
        )
    return matches[0]


def main(argv: Sequence[str] | None = None) -> int:
    """Run qualification, stage a bundle, or promote one exact bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path)
    parser.add_argument("--stage-output-dir", type=Path)
    parser.add_argument("--promote-archive", type=Path)
    parser.add_argument("--artifact-digest")
    parser.add_argument("--promotion-output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.promote_archive is not None:
            if not args.artifact_digest or args.promotion_output_dir is None:
                parser.error("promotion requires --artifact-digest and --promotion-output-dir")
            report = promote_qualification_archive(
                args.promote_archive,
                expected_digest=args.artifact_digest,
                output_dir=args.promotion_output_dir,
            )
        else:
            if args.dist_dir is None:
                parser.error("qualification requires --dist-dir")
            path = _unique_vsix(args.dist_dir.resolve())
            report = _release_report(path)
            if args.stage_output_dir is not None:
                report = stage_qualification(path, args.stage_output_dir)
    except DistributionVerificationError as error:
        parser.exit(1, f"VS Code extension verification failed: {error}\n")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
