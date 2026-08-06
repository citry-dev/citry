"""Focused tests for the citry distribution verifier."""

from __future__ import annotations

import io
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.verify_citry_distribution import (  # noqa: E402
    DistributionVerificationError,
    inventory_fingerprint,
    package_payload,
    require_equal,
    sdist_inventory,
    wheel_inventory,
)


def test_archive_inventories_hash_payloads_without_extracting(tmp_path: Path) -> None:
    wheel = tmp_path / "citry.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("citry/__init__.py", b"value = 1\n")
        archive.writestr("citry-1.0.0.dist-info/METADATA", b"Name: citry\n")

    sdist = tmp_path / "citry.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        content = b"value = 1\n"
        member = tarfile.TarInfo("citry-1.0.0/citry/__init__.py")
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))

    wheel_files = wheel_inventory(wheel)
    sdist_files = sdist_inventory(sdist)

    assert package_payload(wheel_files, "citry") == package_payload(sdist_files, "citry-1.0.0/citry")
    assert inventory_fingerprint(wheel_files) == inventory_fingerprint(dict(reversed(wheel_files.items())))


def test_inventory_comparison_names_changed_and_missing_files() -> None:
    with pytest.raises(DistributionVerificationError, match=r"a\.py, b\.py"):
        require_equal("payload", {"a.py": "old"}, {"a.py": "new", "b.py": "new"})
