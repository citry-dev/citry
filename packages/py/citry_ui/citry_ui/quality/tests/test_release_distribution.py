import importlib.util
import io
import sys
import tarfile
from email.message import Message
from pathlib import Path

import pytest
import tomllib

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


def test_sdist_rebuild_gets_the_hashed_build_pins(monkeypatch, tmp_path):
    output = tmp_path / "wheel"

    def fake_run(command, *, cwd, env=None):
        del cwd, env
        # --no-config hides the root build pins, so the rebuild must get them as a hashed file.
        assert command[-3] == "--build-constraints"
        assert command[-1] == "--require-hashes"
        assert "--hash=sha256:" in Path(command[-2]).read_text(encoding="utf-8")
        (output / "rebuilt.whl").write_bytes(b"wheel")
        return ""

    monkeypatch.setattr(_MODULE, "_run", fake_run)
    assert _MODULE._build_sdist_wheel(tmp_path / "citry_ui.tar.gz", output, cwd=tmp_path) == output / "rebuilt.whl"


def _release_metadata(classifiers):
    metadata = Message()
    metadata["Name"] = "citry-ui"
    metadata["Version"] = "0.1.0"
    metadata["Requires-Python"] = ">=3.11, <4.0"
    for requirement in sorted(_MODULE.EXPECTED_REQUIRES_DIST):
        metadata["Requires-Dist"] = requirement
    for classifier in classifiers:
        metadata["Classifier"] = classifier
    return metadata


def test_metadata_requires_the_classifier_the_package_declares():
    # The verifier pins the development status, so a pyproject edit that leaves it behind would
    # fail the publish only after the wheel is built.
    pyproject = Path(__file__).parents[3] / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["classifiers"]

    _MODULE._require_metadata(_release_metadata(declared), artifact=Path("citry_ui.whl"), version="0.1.0")


def test_metadata_rejects_a_wheel_without_the_declared_status():
    metadata = _release_metadata(["Development Status :: 3 - Alpha"])

    with pytest.raises(_MODULE.DistributionVerificationError, match="Production/Stable classifier"):
        _MODULE._require_metadata(metadata, artifact=Path("citry_ui.whl"), version="0.1.0")
