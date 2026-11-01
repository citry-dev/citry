"""
Inspect one built citry-ui wheel against the checkout it was built from.

The check reads files from the checkout (the list of files that should ship,
and the license) but never runs citry_ui code, so it tests the wheel and not
the source.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import re
import sys
from dataclasses import asdict, dataclass
from email.parser import BytesParser
from pathlib import Path
from zipfile import BadZipFile, ZipFile

# The packaging rules in packages/py/citry_ui/pyproject.toml, restated a little
# more strictly: the walk skips quality/, snippets/, tests/ and tools/ at any
# depth, while pyproject.toml excludes them only at the top and inside each
# component. Package data adds the typing marker and minified assets, plus the
# i18n data files listed below. A file only one side accepts fails the check.
_EXCLUDED_SOURCE_PARTS = frozenset({"quality", "snippets", "tests", "tools"})
_RUNTIME_ASSET_PATTERNS = ("*.min.css", "*.min.js")
_I18N_DATA_PATTERNS = ("citry-i18n.toml", "formats.json", "locales/**/*.ftl", "_compiled/*.json")


def source_runtime_files(package_root: Path) -> frozenset[str]:
    """
    Return the wheel paths of every ``citry_ui`` file the source tree says should ship.

    The list is read from the checkout rather than kept by hand, so a new
    module needs no edit here. The built wheel is then compared with it, which
    still catches a packaging rule that drops a file or adds an unexpected one.
    """
    runtime = package_root / "citry_ui"
    if not runtime.is_dir():
        msg = (
            f"Cannot find the citry_ui source tree at {runtime}. The check compares a wheel "
            "with the checkout it was built from, so run it from a Citry checkout."
        )
        raise FileNotFoundError(msg)
    found = {"citry_ui/py.typed"}
    for pattern in ("*.py", *_RUNTIME_ASSET_PATTERNS):
        for path in runtime.rglob(pattern):
            relative = path.relative_to(runtime)
            if _EXCLUDED_SOURCE_PARTS.isdisjoint(relative.parts) and "__pycache__" not in relative.parts:
                found.add(path.relative_to(package_root).as_posix())
    return frozenset(found)


def source_i18n_files(package_root: Path) -> frozenset[str]:
    """Return the wheel paths of every ``citry_ui_i18n`` module and data file in the source tree."""
    i18n = package_root / "citry_ui_i18n"
    if not i18n.is_dir():
        msg = (
            f"Cannot find the citry_ui_i18n source tree at {i18n}. The check compares a wheel "
            "with the checkout it was built from, so run it from a Citry checkout."
        )
        raise FileNotFoundError(msg)
    found: set[str] = set()
    for pattern in ("**/*.py", *_I18N_DATA_PATTERNS):
        for path in i18n.glob(pattern):
            if path.is_file() and "__pycache__" not in path.relative_to(i18n).parts:
                found.add(path.relative_to(package_root).as_posix())
    return frozenset(found)


# This file never ships (quality/ is excluded), so it always sits in the checkout
# it belongs to; the package root is two levels up, as the license check below
# also relies on.
_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
# A mismatch can come from pyproject.toml or from the stricter walk above, so
# the error names both.
_RULES_HINT = (
    " The expected list comes from the source walk in citry_ui/quality/qualify_wheel.py"
    " (_EXCLUDED_SOURCE_PARTS and the patterns beside it); check it and pyproject.toml."
)
EXPECTED_RUNTIME_FILES = source_runtime_files(_PACKAGE_ROOT)
EXPECTED_I18N_FILES = source_i18n_files(_PACKAGE_ROOT)
_FORBIDDEN_SUFFIXES = {".html", ".json", ".md", ".png", ".svg"}
_THIRD_PARTY_NOTICE_SHA256 = "0f1b152923fc9ff1181a9e6c87aa5877e258efe6d7dbc4c3198ab25e9dd3e8ad"
MAX_WHEEL_BYTES = 800 * 1024
MAX_I18N_COMPRESSED_BYTES = 28 * 1024
_WHEEL_NAME = re.compile(r"citry_ui-(?P<version>[0-9A-Za-z.!+_]+)-py3-none-any\.whl")


class WheelQualificationError(ValueError):
    """A built wheel crossed the Citry UI runtime package boundary."""


@dataclass(frozen=True, slots=True)
class WheelReport:
    """Compact inventory emitted for CI and release records."""

    wheel: str
    files: int
    runtime_files: int
    distribution: str
    pure_python: bool
    wheel_bytes: int
    i18n_compressed_bytes: int


def qualify_wheel(path: Path) -> WheelReport:
    """Validate runtime contents, metadata, license, typing marker, and RECORD."""
    wheel_match = _WHEEL_NAME.fullmatch(path.name)
    if not path.is_file() or wheel_match is None:
        msg = f"Expected a built .whl file, got {path}."
        raise WheelQualificationError(msg)
    version = wheel_match.group("version").replace("_", "-")
    try:
        with ZipFile(path) as archive:
            names = archive.namelist()
            contents = {name: archive.read(name) for name in names}
            compressed_sizes = {entry.filename: entry.compress_size for entry in archive.infolist()}
    except BadZipFile as error:
        msg = f"Wheel is not a readable ZIP archive: {path}."
        raise WheelQualificationError(msg) from error

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        msg = f"Wheel contains duplicate paths: {', '.join(duplicates)}."
        raise WheelQualificationError(msg)

    wheel_bytes = path.stat().st_size
    if wheel_bytes > MAX_WHEEL_BYTES:
        raise WheelQualificationError(f"Wheel is {wheel_bytes} bytes; the release cap is {MAX_WHEEL_BYTES} bytes.")
    i18n_compressed_bytes = sum(size for name, size in compressed_sizes.items() if name.startswith("citry_ui_i18n/"))
    if i18n_compressed_bytes > MAX_I18N_COMPRESSED_BYTES:
        raise WheelQualificationError(
            "Compressed Citry UI i18n package is "
            f"{i18n_compressed_bytes} bytes; the release cap is {MAX_I18N_COMPRESSED_BYTES} bytes."
        )

    name_set = set(names)
    runtime_names = {name for name in names if name.startswith(("citry_ui/", "citry_ui_i18n/"))}
    expected_runtime = EXPECTED_RUNTIME_FILES | EXPECTED_I18N_FILES
    missing = sorted(expected_runtime - runtime_names)
    if missing:
        msg = f"Wheel is missing required runtime files: {', '.join(missing)}.{_RULES_HINT}"
        raise WheelQualificationError(msg)

    dist_info_roots = sorted({name.split("/", 1)[0] for name in names if ".dist-info/" in name})
    expected_dist_info = f"citry_ui-{version}.dist-info"
    if dist_info_roots != [expected_dist_info]:
        msg = f"Wheel must contain {expected_dist_info}, found {dist_info_roots}."
        raise WheelQualificationError(msg)
    dist_info = expected_dist_info

    foreign = sorted(name for name in names if not name.startswith(("citry_ui/", "citry_ui_i18n/", f"{dist_info}/")))
    if foreign:
        msg = f"Wheel contains files outside Citry UI runtime packages and metadata: {', '.join(foreign)}."
        raise WheelQualificationError(msg)

    forbidden = sorted(
        (runtime_names - expected_runtime)
        | {
            name
            for name in runtime_names
            if name.startswith("citry_ui/") and Path(name).suffix.lower() in _FORBIDDEN_SUFFIXES
        }
    )
    if forbidden:
        msg = f"Wheel contains repository-only or stale runtime files: {', '.join(forbidden)}.{_RULES_HINT}"
        raise WheelQualificationError(msg)

    metadata_name = f"{dist_info}/METADATA"
    wheel_name = f"{dist_info}/WHEEL"
    record_name = f"{dist_info}/RECORD"
    license_name = f"{dist_info}/licenses/LICENSE"
    third_party_license_name = f"{dist_info}/licenses/THIRD_PARTY_LICENSES.md"
    top_level_name = f"{dist_info}/top_level.txt"
    expected_metadata = {
        metadata_name,
        wheel_name,
        record_name,
        license_name,
        third_party_license_name,
        top_level_name,
    }
    actual_metadata = {name for name in names if name.startswith(f"{dist_info}/")}
    if actual_metadata != expected_metadata:
        missing_metadata = sorted(expected_metadata - actual_metadata)
        unexpected_metadata = sorted(actual_metadata - expected_metadata)
        msg = (
            "Wheel distribution metadata differs from the release boundary; "
            f"missing={missing_metadata}, unexpected={unexpected_metadata}."
        )
        raise WheelQualificationError(msg)

    if contents[license_name] != (_PACKAGE_ROOT / "LICENSE").read_bytes():
        raise WheelQualificationError("Wheel MIT license differs from the package license.")

    third_party_notice_digest = hashlib.sha256(contents[third_party_license_name]).hexdigest()
    if third_party_notice_digest != _THIRD_PARTY_NOTICE_SHA256:
        raise WheelQualificationError(
            "Wheel third-party notice differs from the reviewed Lucide and Feather license notice."
        )

    metadata = BytesParser().parsebytes(contents[metadata_name])
    if metadata.get("Name") != "citry-ui":
        raise WheelQualificationError("Wheel METADATA does not identify the citry-ui distribution.")
    if metadata.get("Version") != version:
        raise WheelQualificationError("Wheel METADATA version does not match its filename.")
    if metadata.get("Requires-Python") not in {">=3.11, <4.0", "<4.0,>=3.11"}:
        raise WheelQualificationError("Wheel METADATA has an unexpected Python requirement.")
    if metadata.get_all("Requires-Dist", []) != ["citry>=0.7.0"]:
        raise WheelQualificationError("Wheel METADATA has unexpected runtime dependencies.")
    if metadata.get_all("Provides-Extra", []):
        raise WheelQualificationError("Wheel METADATA has unexpected optional extras.")

    wheel_metadata = contents[wheel_name].decode("utf-8")
    pure_python = "Root-Is-Purelib: true\n" in wheel_metadata
    if not pure_python or "Tag: py3-none-any\n" not in wheel_metadata:
        raise WheelQualificationError("Citry UI wheel does not have pure-Python py3-none-any compatibility.")
    if contents[top_level_name] != b"citry_ui\ncitry_ui_i18n\n":
        raise WheelQualificationError("Wheel has unexpected top-level import packages.")

    record_rows = list(csv.reader(io.StringIO(contents[record_name].decode("utf-8"))))
    if any(len(row) != 3 for row in record_rows):
        raise WheelQualificationError("Wheel RECORD contains a malformed row.")
    recorded = {row[0] for row in record_rows}
    if len(record_rows) != len(recorded):
        raise WheelQualificationError("Wheel RECORD contains duplicate paths.")
    unrecorded = sorted(name_set - recorded)
    stale = sorted(recorded - name_set)
    if unrecorded or stale:
        msg = f"Wheel RECORD differs from the archive; unrecorded={unrecorded}, stale={stale}."
        raise WheelQualificationError(msg)
    for name, digest, size in record_rows:
        if name == record_name:
            if digest or size:
                raise WheelQualificationError("Wheel RECORD must leave its own hash and size empty.")
            continue
        payload = contents[name]
        expected_digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")
        if digest != f"sha256={expected_digest}" or size != str(len(payload)):
            raise WheelQualificationError(f"Wheel RECORD has an invalid hash or size for {name}.")

    runtime_files = len(runtime_names)
    return WheelReport(
        wheel=path.name,
        files=len(names),
        runtime_files=runtime_files,
        distribution=dist_info.removesuffix(".dist-info"),
        pure_python=pure_python,
        wheel_bytes=wheel_bytes,
        i18n_compressed_bytes=i18n_compressed_bytes,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect one built citry-ui wheel.")
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    try:
        report = qualify_wheel(args.wheel)
    except WheelQualificationError as error:
        parser.exit(1, f"citry-ui wheel qualification failed: {error}\n")
    sys.stdout.write(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
