"""Inspect one built citry-ui wheel without importing the source checkout."""

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

EXPECTED_RUNTIME_FILES = {
    "citry_ui/__init__.py",
    "citry_ui/py.typed",
    "citry_ui/components/__init__.py",
    "citry_ui/components/_anchored_layer.py",
    "citry_ui/components/_active_descendant.py",
    "citry_ui/components/_aria.py",
    "citry_ui/components/_attrs.py",
    "citry_ui/components/_context.py",
    "citry_ui/components/_dialog_controller.py",
    "citry_ui/components/_form_control_runtime.py",
    "citry_ui/components/_i18n.py",
    "citry_ui/components/_scroll_geometry.py",
    "citry_ui/components/_shared_component_assets.py",
    "citry_ui/components/_validation.py",
    "citry_ui/components/caccordion/__init__.py",
    "citry_ui/components/caccordion/caccordion.py",
    "citry_ui/components/calert/__init__.py",
    "citry_ui/components/calert/calert.py",
    "citry_ui/components/calert_dialog/__init__.py",
    "citry_ui/components/calert_dialog/calert_dialog.py",
    "citry_ui/components/cavatar/__init__.py",
    "citry_ui/components/cavatar/cavatar.py",
    "citry_ui/components/cbadge/__init__.py",
    "citry_ui/components/cbadge/cbadge.py",
    "citry_ui/components/cbreadcrumbs/__init__.py",
    "citry_ui/components/cbreadcrumbs/cbreadcrumbs.py",
    "citry_ui/components/cbutton/__init__.py",
    "citry_ui/components/cbutton/cbutton.py",
    "citry_ui/components/cbutton_group/__init__.py",
    "citry_ui/components/cbutton_group/cbutton_group.py",
    "citry_ui/components/ccard/__init__.py",
    "citry_ui/components/ccard/ccard.py",
    "citry_ui/components/ccarousel/__init__.py",
    "citry_ui/components/ccarousel/ccarousel.py",
    "citry_ui/components/ccheckbox/__init__.py",
    "citry_ui/components/ccheckbox/ccheckbox.py",
    "citry_ui/components/ccombobox/__init__.py",
    "citry_ui/components/ccombobox/ccombobox.py",
    "citry_ui/components/ccommand_palette/__init__.py",
    "citry_ui/components/ccommand_palette/ccommand_palette.py",
    "citry_ui/components/ccontext_menu/__init__.py",
    "citry_ui/components/ccontext_menu/ccontext_menu.py",
    "citry_ui/components/cdialog/__init__.py",
    "citry_ui/components/cdialog/cdialog.py",
    "citry_ui/components/cdisclosure/__init__.py",
    "citry_ui/components/cdisclosure/cdisclosure.py",
    "citry_ui/components/cdrawer/__init__.py",
    "citry_ui/components/cdrawer/cdrawer.py",
    "citry_ui/components/cdivider/__init__.py",
    "citry_ui/components/cdivider/cdivider.py",
    "citry_ui/components/ceditable/__init__.py",
    "citry_ui/components/ceditable/ceditable.py",
    "citry_ui/components/cfield/__init__.py",
    "citry_ui/components/cfield/cfield.py",
    "citry_ui/components/cfile_input/__init__.py",
    "citry_ui/components/cfile_input/cfile_input.py",
    "citry_ui/components/cflow/__init__.py",
    "citry_ui/components/cflow/cflow.py",
    "citry_ui/components/cgrid/__init__.py",
    "citry_ui/components/cgrid/cgrid.py",
    "citry_ui/components/cform/__init__.py",
    "citry_ui/components/cform/cform.py",
    "citry_ui/components/chover_card/__init__.py",
    "citry_ui/components/chover_card/chover_card.py",
    "citry_ui/components/cicon/__init__.py",
    "citry_ui/components/cicon/_catalog.py",
    "citry_ui/components/cicon/cicon.py",
    "citry_ui/components/cimage/__init__.py",
    "citry_ui/components/cimage/cimage.py",
    "citry_ui/components/clist/__init__.py",
    "citry_ui/components/clist/clist.py",
    "citry_ui/components/clistbox/__init__.py",
    "citry_ui/components/clistbox/clistbox.py",
    "citry_ui/components/cmenu/__init__.py",
    "citry_ui/components/cmenu/cmenu.py",
    "citry_ui/components/cmulti_select/__init__.py",
    "citry_ui/components/cmulti_select/cmulti_select.py",
    "citry_ui/components/cnative_select/__init__.py",
    "citry_ui/components/cnative_select/cnative_select.py",
    "citry_ui/components/cnavigation_menu/__init__.py",
    "citry_ui/components/cnavigation_menu/cnavigation_menu.py",
    "citry_ui/components/cnumber_input/__init__.py",
    "citry_ui/components/cnumber_input/cnumber_input.py",
    "citry_ui/components/cpagination/__init__.py",
    "citry_ui/components/cpagination/cpagination.py",
    "citry_ui/components/cpopover/__init__.py",
    "citry_ui/components/cpopover/cpopover.py",
    "citry_ui/components/ctooltip/__init__.py",
    "citry_ui/components/ctooltip/ctooltip.py",
    "citry_ui/components/cprogress/__init__.py",
    "citry_ui/components/cprogress/cprogress.py",
    "citry_ui/components/cradio/__init__.py",
    "citry_ui/components/cradio/cradio.py",
    "citry_ui/components/cscroll_area/__init__.py",
    "citry_ui/components/cscroll_area/cscroll_area.py",
    "citry_ui/components/cselect/__init__.py",
    "citry_ui/components/cselect/cselect.py",
    "citry_ui/components/cspinner/__init__.py",
    "citry_ui/components/cspinner/cspinner.py",
    "citry_ui/components/cskeleton/__init__.py",
    "citry_ui/components/cskeleton/cskeleton.py",
    "citry_ui/components/csplitbutton/__init__.py",
    "citry_ui/components/csplitbutton/_submit_registry.py",
    "citry_ui/components/csplitbutton/csplitbutton.py",
    "citry_ui/components/csplitter/__init__.py",
    "citry_ui/components/csplitter/csplitter.py",
    "citry_ui/components/cstepper/__init__.py",
    "citry_ui/components/cstepper/cstepper.py",
    "citry_ui/components/cswitch/__init__.py",
    "citry_ui/components/cswitch/cswitch.py",
    "citry_ui/components/ctable/__init__.py",
    "citry_ui/components/ctable/ctable.py",
    "citry_ui/components/ctabs/__init__.py",
    "citry_ui/components/ctabs/ctabs.py",
    "citry_ui/components/ctag/__init__.py",
    "citry_ui/components/ctag/ctag.py",
    "citry_ui/components/ctags_input/__init__.py",
    "citry_ui/components/ctags_input/ctags_input.py",
    "citry_ui/components/ctextarea/__init__.py",
    "citry_ui/components/ctextarea/ctextarea.py",
    "citry_ui/components/ctoggle/__init__.py",
    "citry_ui/components/ctoggle/ctoggle.py",
    "citry_ui/components/ctoast/__init__.py",
    "citry_ui/components/ctoast/ctoast.py",
    "citry_ui/components/ctoolbar/__init__.py",
    "citry_ui/components/ctoolbar/ctoolbar.py",
    "citry_ui/components/ctree/__init__.py",
    "citry_ui/components/ctree/ctree.py",
}
EXPECTED_I18N_FILES = {
    "citry_ui_i18n/__init__.py",
    "citry_ui_i18n/_generate_catalog.py",
    "citry_ui_i18n/citry-i18n.toml",
    "citry_ui_i18n/formats.json",
    "citry_ui_i18n/_compiled/__init__.py",
    "citry_ui_i18n/_compiled/link.json",
    "citry_ui_i18n/_compiled/manifest.json",
    "citry_ui_i18n/_compiled/server.json",
    "citry_ui_i18n/locales/en-US/citry-ui.ftl",
}
_FORBIDDEN_SUFFIXES = {".html", ".json", ".md", ".png", ".svg"}
_THIRD_PARTY_NOTICE_SHA256 = "0f1b152923fc9ff1181a9e6c87aa5877e258efe6d7dbc4c3198ab25e9dd3e8ad"
MAX_WHEEL_BYTES = 700 * 1024
MAX_I18N_COMPRESSED_BYTES = 20 * 1024
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
        msg = f"Wheel is missing required runtime files: {', '.join(missing)}."
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
        msg = f"Wheel contains repository-only or stale runtime files: {', '.join(forbidden)}."
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

    package_root = Path(__file__).parents[2]
    if contents[license_name] != (package_root / "LICENSE").read_bytes():
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
    if metadata.get("Requires-Python") not in {">=3.10, <4.0", "<4.0,>=3.10"}:
        raise WheelQualificationError("Wheel METADATA has an unexpected Python requirement.")
    if metadata.get_all("Requires-Dist", []) != ["citry<0.5.0,>=0.4.0"]:
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
