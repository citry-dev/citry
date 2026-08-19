import importlib.util
import io
import sys
import tarfile
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parents[6] / "scripts" / "verify_citry_ui_distribution.py"
_SPEC = importlib.util.spec_from_file_location("verify_citry_ui_distribution", _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)


def test_release_set_is_one_universal_wheel_and_one_sdist():
    assert _MODULE.expected_release_filenames("0.1.0") == {
        "citry_ui-0.1.0-py3-none-any.whl",
        "citry_ui-0.1.0.tar.gz",
    }


def test_sdist_rejects_parent_path_members(tmp_path):
    path = tmp_path / "citry_ui-0.1.0.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("../outside")
        member.size = 1
        archive.addfile(member, io.BytesIO(b"x"))

    with pytest.raises(_MODULE.DistributionVerificationError, match="unsafe member"):
        _MODULE.verify_sdist(path, version="0.1.0")


def test_promotion_rejects_an_untrusted_digest(tmp_path):
    archive = tmp_path / "qualification.zip"
    archive.write_bytes(b"not an artifact")

    with pytest.raises(_MODULE.DistributionVerificationError, match="invalid qualification artifact digest"):
        _MODULE.promote_qualification_archive(
            archive,
            expected_digest="sha256:not-a-digest",
            output_dir=tmp_path / "verified",
        )
