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
    source_i18n_files,
    source_runtime_files,
)

_THIRD_PARTY_NOTICE = (Path(__file__).parents[3] / "THIRD_PARTY_LICENSES.md").read_bytes()
_LICENSE = (Path(__file__).parents[3] / "LICENSE").read_bytes()


def _wheel(tmp_path, *, extra=()):
    path = tmp_path / "citry_ui-0.1.0-py3-none-any.whl"
    dist = "citry_ui-0.1.0.dist-info"
    files = {
        **dict.fromkeys(EXPECTED_RUNTIME_FILES, b""),
        **dict.fromkeys(EXPECTED_I18N_FILES, b""),
        f"{dist}/METADATA": (
            b"Name: citry-ui\nVersion: 0.1.0\nRequires-Python: >=3.11, <4.0\nRequires-Dist: citry>=0.7.0\n"
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


def _touch(root, *names):
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")


def test_source_runtime_files_follow_the_packaging_rules(tmp_path):
    # A synthetic package tree with one file of each kind the rules decide on.
    _touch(
        tmp_path,
        "citry_ui/__init__.py",
        "citry_ui/py.typed",
        "citry_ui/components/cnew/__init__.py",
        "citry_ui/components/cnew/cnew.py",
        "citry_ui/components/cnew/runtime.min.js",
        "citry_ui/components/cnew/runtime.min.css",
        "citry_ui/components/cnew/runtime.js",
        "citry_ui/components/cnew/api.md",
        "citry_ui/components/cnew/tests/test_cnew.py",
        "citry_ui/components/cnew/snippets/basic.py",
        "citry_ui/components/cnew/quality/scenario.py",
        "citry_ui/components/cnew/tools/build.py",
        "citry_ui/components/cnew/__pycache__/cnew.cpython-314.pyc",
        "citry_ui/quality/report.py",
    )

    # A new component's module and minified assets are expected without any
    # edit to the qualifier; unminified JS, docs, tests, snippets, quality code
    # and bytecode are not.
    assert source_runtime_files(tmp_path) == {
        "citry_ui/__init__.py",
        "citry_ui/py.typed",
        "citry_ui/components/cnew/__init__.py",
        "citry_ui/components/cnew/cnew.py",
        "citry_ui/components/cnew/runtime.min.css",
        "citry_ui/components/cnew/runtime.min.js",
    }


def test_source_i18n_files_follow_the_package_data_rules(tmp_path):
    _touch(
        tmp_path,
        "citry_ui_i18n/__init__.py",
        "citry_ui_i18n/citry-i18n.toml",
        "citry_ui_i18n/formats.json",
        "citry_ui_i18n/_compiled/__init__.py",
        "citry_ui_i18n/_compiled/server.json",
        "citry_ui_i18n/locales/en-US/citry-ui.ftl",
        "citry_ui_i18n/locales/sk/citry-ui.ftl",
        "citry_ui_i18n/notes.md",
        "citry_ui_i18n/__pycache__/x.pyc",
    )

    # A new locale's catalog ships without an edit here.
    assert source_i18n_files(tmp_path) == {
        "citry_ui_i18n/__init__.py",
        "citry_ui_i18n/citry-i18n.toml",
        "citry_ui_i18n/formats.json",
        "citry_ui_i18n/_compiled/__init__.py",
        "citry_ui_i18n/_compiled/server.json",
        "citry_ui_i18n/locales/en-US/citry-ui.ftl",
        "citry_ui_i18n/locales/sk/citry-ui.ftl",
    }


def test_source_files_need_the_checkout(tmp_path):
    # Without the source tree there is nothing to compare a wheel with, so the
    # check says where it looked instead of passing on an empty list.
    with pytest.raises(FileNotFoundError, match="run it from a Citry checkout"):
        source_runtime_files(tmp_path)
    with pytest.raises(FileNotFoundError, match="citry_ui_i18n"):
        source_i18n_files(tmp_path)


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
