import csv
import io
from zipfile import ZipFile

import pytest

from citry_ui.quality.qualify_wheel import EXPECTED_RUNTIME_FILES, WheelQualificationError, qualify_wheel


def _wheel(tmp_path, *, extra=()):
    path = tmp_path / "citry_ui-0.0.1-py3-none-any.whl"
    dist = "citry_ui-0.0.1.dist-info"
    files = {
        **dict.fromkeys(EXPECTED_RUNTIME_FILES, b""),
        f"{dist}/METADATA": b"Name: citry-ui\nRequires-Dist: citry>=0.3.1\n",
        f"{dist}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\n",
        f"{dist}/licenses/LICENSE": b"MIT\n",
    }
    files.update(dict(extra))
    record_name = f"{dist}/RECORD"
    rows = [[name, "", ""] for name in (*files, record_name)]
    output = io.StringIO()
    csv.writer(output, lineterminator="\n").writerows(rows)
    files[record_name] = output.getvalue().encode()
    with ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return path


def test_qualify_wheel_accepts_the_runtime_boundary(tmp_path):
    report = qualify_wheel(_wheel(tmp_path))

    assert report.distribution == "citry_ui-0.0.1"
    assert report.pure_python is True
    assert report.runtime_files == len(EXPECTED_RUNTIME_FILES)


@pytest.mark.parametrize(
    "name",
    [
        "citry_ui/components/cbutton/api.md",
        "citry_ui/components/cbutton/tests/test_button.py",
        "citry_ui/quality/scenarios.py",
    ],
)
def test_qualify_wheel_rejects_repository_only_files(tmp_path, name):
    path = _wheel(tmp_path, extra=((name, b"support"),))

    with pytest.raises(WheelQualificationError, match="repository-only or stale"):
        qualify_wheel(path)
