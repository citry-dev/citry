import base64
import csv
import hashlib
import io
from pathlib import Path
from zipfile import ZipFile

import pytest

from citry_ui.quality.qualify_wheel import (
    EXPECTED_I18N_FILES,
    EXPECTED_RUNTIME_FILES,
    MAX_I18N_COMPRESSED_BYTES,
    WheelQualificationError,
    qualify_wheel,
)

_THIRD_PARTY_NOTICE = (Path(__file__).parents[3] / "THIRD_PARTY_LICENSES.md").read_bytes()
_LICENSE = (Path(__file__).parents[3] / "LICENSE").read_bytes()
_RUNTIME_PACKAGE = Path(__file__).parents[2]


def _wheel(tmp_path, *, extra=()):
    path = tmp_path / "citry_ui-0.1.0-py3-none-any.whl"
    dist = "citry_ui-0.1.0.dist-info"
    files = {
        **dict.fromkeys(EXPECTED_RUNTIME_FILES, b""),
        **dict.fromkeys(EXPECTED_I18N_FILES, b""),
        f"{dist}/METADATA": (
            b"Name: citry-ui\nVersion: 0.1.0\nRequires-Python: >=3.10, <4.0\nRequires-Dist: citry<0.5.0,>=0.4.2\n"
        ),
        f"{dist}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{dist}/licenses/LICENSE": _LICENSE,
        f"{dist}/licenses/THIRD_PARTY_LICENSES.md": _THIRD_PARTY_NOTICE,
        f"{dist}/top_level.txt": b"citry_ui\ncitry_ui_i18n\n",
    }
    files.update(dict(extra))
    record_name = f"{dist}/RECORD"
    rows = []
    for name, payload in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")
        rows.append([name, f"sha256={digest}", str(len(payload))])
    rows.append([record_name, "", ""])
    output = io.StringIO()
    csv.writer(output, lineterminator="\n").writerows(rows)
    files[record_name] = output.getvalue().encode()
    with ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return path


def test_qualify_wheel_accepts_the_runtime_boundary(tmp_path):
    report = qualify_wheel(_wheel(tmp_path))

    assert report.distribution == "citry_ui-0.1.0"
    assert report.pure_python is True
    assert report.runtime_files == len(EXPECTED_RUNTIME_FILES | EXPECTED_I18N_FILES)
    assert report.wheel_bytes > 0
    assert report.i18n_compressed_bytes >= 0


def test_runtime_boundary_matches_every_shipped_python_module():
    excluded_parts = {"quality", "snippets", "tests", "tools"}
    shipped_python = {
        path.relative_to(_RUNTIME_PACKAGE.parent).as_posix()
        for path in _RUNTIME_PACKAGE.rglob("*.py")
        if excluded_parts.isdisjoint(path.relative_to(_RUNTIME_PACKAGE).parts)
    }
    shipped_assets = {
        path.relative_to(_RUNTIME_PACKAGE.parent).as_posix()
        for suffix in ("*.min.css", "*.min.js")
        for path in _RUNTIME_PACKAGE.rglob(suffix)
    }

    assert shipped_python | shipped_assets | {"citry_ui/py.typed"} == EXPECTED_RUNTIME_FILES


def test_runtime_boundary_includes_split_button_private_dependencies():
    assert {
        "citry_ui/components/_shared_component_assets.py",
        "citry_ui/components/csplitbutton/_submit_registry.py",
        "citry_ui/components/csplitbutton/csplitbutton.py",
    } <= EXPECTED_RUNTIME_FILES


def test_runtime_boundary_includes_tags_input_public_runtime():
    assert {
        "citry_ui/components/_form_control_runtime.py",
        "citry_ui/components/ctags_input/__init__.py",
        "citry_ui/components/ctags_input/ctags_input.py",
    } <= EXPECTED_RUNTIME_FILES


def test_runtime_boundary_includes_scroll_area_and_shared_geometry():
    assert {
        "citry_ui/components/_scroll_geometry.py",
        "citry_ui/components/cscroll_area/__init__.py",
        "citry_ui/components/cscroll_area/cscroll_area.py",
    } <= EXPECTED_RUNTIME_FILES


def test_runtime_boundary_includes_context_menu_public_runtime():
    assert {
        "citry_ui/components/ccontext_menu/__init__.py",
        "citry_ui/components/ccontext_menu/ccontext_menu.py",
    } <= EXPECTED_RUNTIME_FILES


def test_runtime_boundary_includes_image_public_runtime():
    assert {
        "citry_ui/components/cimage/__init__.py",
        "citry_ui/components/cimage/cimage.py",
    } <= EXPECTED_RUNTIME_FILES


def test_runtime_boundary_includes_command_palette_and_private_controllers():
    assert {
        "citry_ui/components/_active_descendant.py",
        "citry_ui/components/_dialog_controller.py",
        "citry_ui/components/ccommand_palette/__init__.py",
        "citry_ui/components/ccommand_palette/ccommand_palette.py",
    } <= EXPECTED_RUNTIME_FILES


def test_runtime_boundary_includes_the_side_effect_free_i18n_catalog_package():
    assert {
        "citry_ui_i18n/citry-i18n.toml",
        "citry_ui_i18n/formats.json",
        "citry_ui_i18n/locales/en-US/citry-ui.ftl",
        "citry_ui_i18n/_compiled/manifest.json",
        "citry_ui_i18n/_compiled/server.json",
        "citry_ui_i18n/_compiled/link.json",
        "citry_ui_i18n/_generate_catalog.py",
    } <= EXPECTED_I18N_FILES


def test_qualify_wheel_rejects_an_incomplete_third_party_notice(tmp_path):
    dist = "citry_ui-0.1.0.dist-info"
    path = _wheel(
        tmp_path,
        extra=((f"{dist}/licenses/THIRD_PARTY_LICENSES.md", b"Lucide 1.30.0\nISC License\n"),),
    )

    with pytest.raises(WheelQualificationError, match="third-party notice differs"):
        qualify_wheel(path)


def test_qualify_wheel_rejects_a_marker_only_third_party_notice(tmp_path):
    dist = "citry_ui-0.1.0.dist-info"
    path = _wheel(
        tmp_path,
        extra=(
            (
                f"{dist}/licenses/THIRD_PARTY_LICENSES.md",
                b"Lucide 1.30.0\nISC License\nThe MIT License (MIT)\ncircle-help circle-x triangle-alert\n",
            ),
        ),
    )

    with pytest.raises(WheelQualificationError, match="third-party notice differs"):
        qualify_wheel(path)


def test_qualify_wheel_rejects_an_oversized_i18n_package(tmp_path):
    path = _wheel(
        tmp_path,
        extra=(("citry_ui_i18n/_compiled/server.json", b"x" * (MAX_I18N_COMPRESSED_BYTES + 1)),),
    )

    with pytest.raises(WheelQualificationError, match="Compressed Citry UI i18n package"):
        qualify_wheel(path)


@pytest.mark.parametrize(
    "name",
    [
        "citry_ui/components/cbutton/api.md",
        "citry_ui/components/cbutton/README.md",
        "citry_ui/components/cbutton/snippets/basic.py",
        "citry_ui/components/cbutton/tests/test_button.py",
        "citry_ui/quality/scenarios.py",
        "citry_ui/components/cbutton/stale.py",
    ],
)
def test_qualify_wheel_rejects_repository_only_files(tmp_path, name):
    path = _wheel(tmp_path, extra=((name, b"support"),))

    with pytest.raises(WheelQualificationError, match="repository-only or stale"):
        qualify_wheel(path)
