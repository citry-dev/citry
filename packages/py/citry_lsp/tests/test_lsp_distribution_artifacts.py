"""Focused tests for the citry-lsp distribution verifier."""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts import verify_citry_lsp_distribution as distribution_verifier  # noqa: E402
from scripts.select_citry_core_qualification import select_artifact  # noqa: E402
from scripts.verify_citry_lsp_distribution import (  # noqa: E402
    DistributionVerificationError,
    expected_release_filenames,
    promote_qualification_archive,
    verify_staged_bundle,
    verify_wheel,
)


def _write_wheel(path: Path, *, extra: str | None = None) -> None:
    dist_info = "citry_lsp-0.1.0.dist-info"
    metadata = (
        "Metadata-Version: 2.4\nName: citry-lsp\nVersion: 0.1.0\nRequires-Python: <4.0,>=3.10\n"
        + "".join(
            f"Requires-Dist: {requirement}\n" for requirement in sorted(distribution_verifier.EXPECTED_REQUIRES_DIST)
        )
        + "\n"
    ).encode()
    members = {
        "citry_lsp/__init__.py": b"value = 1\n",
        f"{dist_info}/METADATA": metadata,
        f"{dist_info}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{dist_info}/entry_points.txt": b"[console_scripts]\ncitry-lsp = citry_lsp.__main__:main\n",
        f"{dist_info}/top_level.txt": b"citry_lsp\n",
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


def test_release_inventory_is_one_universal_wheel_and_one_sdist() -> None:
    assert expected_release_filenames("0.1.0") == {
        "citry_lsp-0.1.0-py3-none-any.whl",
        "citry_lsp-0.1.0.tar.gz",
    }


def test_wheel_verifier_rejects_payload_outside_the_closed_package(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        distribution_verifier,
        "source_inventory",
        lambda: {"__init__.py": distribution_verifier.sha256_bytes(b"value = 1\n")},
    )
    valid = tmp_path / "citry_lsp-0.1.0-py3-none-any.whl"
    _write_wheel(valid)
    assert verify_wheel(valid, version="0.1.0")["name"] == valid.name

    invalid = tmp_path / "invalid" / valid.name
    invalid.parent.mkdir()
    _write_wheel(invalid, extra="installer_hook.py")
    with pytest.raises(DistributionVerificationError, match=r"unexpected=.*installer_hook\.py"):
        verify_wheel(invalid, version="0.1.0")


def test_staged_bundle_requires_the_recorded_bytes(monkeypatch, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    wheel = bundle / "citry_lsp-0.1.0-py3-none-any.whl"
    sdist = bundle / "citry_lsp-0.1.0.tar.gz"
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
    expected = {"version": "0.1.0", "artifacts": []}
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


def test_selector_accepts_the_lsp_qualification_name() -> None:
    commit = "a" * 40
    artifact = {
        "id": 42,
        "name": "verified-citry-lsp-distributions",
        "expired": False,
        "digest": f"sha256:{'b' * 64}",
        "workflow_run": {"head_sha": commit, "id": 7},
    }

    assert (
        select_artifact(
            {"artifacts": [artifact]},
            commit=commit,
            run_id=7,
            artifact_name="verified-citry-lsp-distributions",
        )
        == artifact
    )
