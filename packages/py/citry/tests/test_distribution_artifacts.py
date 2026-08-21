"""Focused tests for the citry distribution verifier."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts import verify_citry_distribution as distribution_verifier  # noqa: E402
from scripts.select_citry_core_qualification import select_artifact  # noqa: E402
from scripts.verify_citry_distribution import (  # noqa: E402
    DistributionVerificationError,
    inventory_fingerprint,
    package_payload,
    promote_qualification_archive,
    require_equal,
    sdist_inventory,
    verify_staged_bundle,
    verify_wheel,
    wheel_inventory,
)
from scripts.verify_wheel_size import verify as verify_wheel_sizes  # noqa: E402


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


def test_wheel_size_gate_reports_and_rejects_the_exact_compressed_size(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.0.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel")

    assert verify_wheel_sizes([wheel], max_bytes=5) == [
        {
            "wheel": wheel.name,
            "bytes": 5,
            "maxBytes": 5,
        }
    ]
    with pytest.raises(ValueError, match="release cap is 4 bytes"):
        verify_wheel_sizes([wheel], max_bytes=4)


def _write_wheel(path: Path, *, extra: str | None = None) -> None:
    dist_info = "citry-0.4.2.dist-info"
    metadata = (
        "Metadata-Version: 2.4\nName: citry\nVersion: 0.4.2\nRequires-Python: <4.0,>=3.10\n"
        + "".join(
            f"Requires-Dist: {requirement}\n" for requirement in sorted(distribution_verifier.EXPECTED_REQUIRES_DIST)
        )
        + "".join(f"Provides-Extra: {name}\n" for name in sorted(distribution_verifier.EXPECTED_EXTRAS))
        + "\n"
    ).encode()
    members = {
        "citry/__init__.py": b"value = 1\n",
        f"{dist_info}/METADATA": metadata,
        f"{dist_info}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{dist_info}/entry_points.txt": b"[console_scripts]\ncitry = citry.__main__:main\n",
        f"{dist_info}/top_level.txt": b"citry\n",
        f"{dist_info}/licenses/LICENSE": (distribution_verifier.PACKAGE_ROOT / "LICENSE").read_bytes(),
    }
    if extra is not None:
        members[extra] = b"unexpected\n"
    record_name = f"{dist_info}/RECORD"
    record = (
        "".join(
            f"{name},sha256={distribution_verifier.record_sha256(payload)},{len(payload)}\n"
            for name, payload in members.items()
        )
        + f"{record_name},,\n"
    )
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
        archive.writestr(record_name, record.encode())


def test_wheel_verifier_rejects_payload_outside_the_closed_package(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        distribution_verifier,
        "source_inventory",
        lambda: {"__init__.py": distribution_verifier.sha256_bytes(b"value = 1\n")},
    )
    valid = tmp_path / "citry-0.4.2-py3-none-any.whl"
    _write_wheel(valid)
    assert verify_wheel(valid, version="0.4.2")["name"] == valid.name

    invalid = tmp_path / "invalid" / valid.name
    invalid.parent.mkdir()
    _write_wheel(invalid, extra="installer_hook.py")
    with pytest.raises(DistributionVerificationError, match=r"unexpected=.*installer_hook\.py"):
        verify_wheel(invalid, version="0.4.2")


def test_staged_bundle_requires_the_recorded_bytes(monkeypatch, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    wheel = bundle / "citry-0.4.2-py3-none-any.whl"
    sdist = bundle / "citry-0.4.2.tar.gz"
    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
    report = distribution_verifier._release_report(wheel, sdist)
    (bundle / "release-inventory.json").write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(distribution_verifier, "verify_wheel", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(distribution_verifier, "verify_sdist", lambda *_args, **_kwargs: {})

    assert verify_staged_bundle(bundle) == report
    wheel.write_bytes(b"changed")
    with pytest.raises(DistributionVerificationError, match="does not match"):
        verify_staged_bundle(bundle)


def test_promotion_checks_github_digest_before_safe_extraction(monkeypatch, tmp_path: Path) -> None:
    archive = tmp_path / "qualification.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("release-inventory.json", "{}\n")
    digest = f"sha256:{hashlib.sha256(archive.read_bytes()).hexdigest()}"
    expected = {"version": "0.4.2", "artifacts": []}
    monkeypatch.setattr(distribution_verifier, "verify_staged_bundle", lambda _directory: expected)

    assert (
        promote_qualification_archive(
            archive,
            expected_digest=digest,
            output_dir=tmp_path / "out",
        )
        == expected
    )
    with pytest.raises(DistributionVerificationError, match="does not match GitHub"):
        promote_qualification_archive(
            archive,
            expected_digest=f"sha256:{'0' * 64}",
            output_dir=tmp_path / "wrong",
        )


def test_selector_accepts_the_citry_specific_qualification_name() -> None:
    commit = "a" * 40
    artifact = {
        "id": 42,
        "name": "verified-citry-distributions",
        "expired": False,
        "digest": f"sha256:{'b' * 64}",
        "workflow_run": {"head_sha": commit, "id": 7},
    }

    assert (
        select_artifact(
            {"artifacts": [artifact]},
            commit=commit,
            run_id=7,
            artifact_name="verified-citry-distributions",
        )
        == artifact
    )
