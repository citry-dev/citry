"""Inspect one built citry-ui wheel without importing the source checkout."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from zipfile import BadZipFile, ZipFile

EXPECTED_RUNTIME_FILES = {
    "citry_ui/__init__.py",
    "citry_ui/py.typed",
    "citry_ui/components/__init__.py",
    "citry_ui/components/_aria.py",
    "citry_ui/components/_context.py",
    "citry_ui/components/_validation.py",
    "citry_ui/components/cbutton/__init__.py",
    "citry_ui/components/cbutton/cbutton.py",
    "citry_ui/components/ccombobox/__init__.py",
    "citry_ui/components/ccombobox/ccombobox.py",
    "citry_ui/components/cdialog/__init__.py",
    "citry_ui/components/cdialog/cdialog.py",
    "citry_ui/components/cfield/__init__.py",
    "citry_ui/components/cfield/cfield.py",
    "citry_ui/components/cform/__init__.py",
    "citry_ui/components/cform/cform.py",
    "citry_ui/components/ctable/__init__.py",
    "citry_ui/components/ctable/ctable.py",
    "citry_ui/components/ctabs/__init__.py",
    "citry_ui/components/ctabs/ctabs.py",
}
_FORBIDDEN_SUFFIXES = {".html", ".json", ".md", ".png", ".svg"}


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


def qualify_wheel(path: Path) -> WheelReport:
    """Validate runtime contents, metadata, license, typing marker, and RECORD."""
    if not path.is_file() or path.suffix != ".whl":
        msg = f"Expected a built .whl file, got {path}."
        raise WheelQualificationError(msg)
    try:
        with ZipFile(path) as archive:
            names = archive.namelist()
            contents = {name: archive.read(name) for name in names}
    except BadZipFile as error:
        msg = f"Wheel is not a readable ZIP archive: {path}."
        raise WheelQualificationError(msg) from error

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        msg = f"Wheel contains duplicate paths: {', '.join(duplicates)}."
        raise WheelQualificationError(msg)

    name_set = set(names)
    runtime_names = {name for name in names if name.startswith("citry_ui/")}
    missing = sorted(EXPECTED_RUNTIME_FILES - runtime_names)
    if missing:
        msg = f"Wheel is missing required runtime files: {', '.join(missing)}."
        raise WheelQualificationError(msg)

    dist_info_roots = sorted({name.split("/", 1)[0] for name in names if ".dist-info/" in name})
    if len(dist_info_roots) != 1:
        msg = f"Wheel must contain one .dist-info directory, found {dist_info_roots}."
        raise WheelQualificationError(msg)
    dist_info = dist_info_roots[0]

    foreign = sorted(
        name for name in names if not name.startswith("citry_ui/") and not name.startswith(f"{dist_info}/")
    )
    if foreign:
        msg = f"Wheel contains files outside citry_ui and its metadata: {', '.join(foreign)}."
        raise WheelQualificationError(msg)

    forbidden = sorted(
        (runtime_names - EXPECTED_RUNTIME_FILES)
        | {name for name in runtime_names if Path(name).suffix.lower() in _FORBIDDEN_SUFFIXES}
    )
    if forbidden:
        msg = f"Wheel contains repository-only or stale runtime files: {', '.join(forbidden)}."
        raise WheelQualificationError(msg)

    metadata_name = f"{dist_info}/METADATA"
    wheel_name = f"{dist_info}/WHEEL"
    record_name = f"{dist_info}/RECORD"
    license_name = f"{dist_info}/licenses/LICENSE"
    missing_metadata = [
        name for name in (metadata_name, wheel_name, record_name, license_name) if name not in name_set
    ]
    if missing_metadata:
        msg = f"Wheel is missing distribution metadata: {', '.join(missing_metadata)}."
        raise WheelQualificationError(msg)

    metadata = contents[metadata_name].decode("utf-8")
    if "Name: citry-ui\n" not in metadata:
        raise WheelQualificationError("Wheel METADATA does not identify the citry-ui distribution.")
    if "Requires-Dist: citry" not in metadata:
        raise WheelQualificationError("Wheel METADATA does not declare the citry runtime dependency.")

    wheel_metadata = contents[wheel_name].decode("utf-8")
    pure_python = "Root-Is-Purelib: true\n" in wheel_metadata
    if not pure_python:
        raise WheelQualificationError("Citry UI wheel is not marked as a pure-Python wheel.")

    record_rows = list(csv.reader(io.StringIO(contents[record_name].decode("utf-8"))))
    recorded = {row[0] for row in record_rows if row}
    unrecorded = sorted(name_set - recorded)
    stale = sorted(recorded - name_set)
    if unrecorded or stale:
        msg = f"Wheel RECORD differs from the archive; unrecorded={unrecorded}, stale={stale}."
        raise WheelQualificationError(msg)

    runtime_files = len(runtime_names)
    return WheelReport(
        wheel=path.name,
        files=len(names),
        runtime_files=runtime_files,
        distribution=dist_info.removesuffix(".dist-info"),
        pure_python=pure_python,
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
