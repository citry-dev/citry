"""Focused tests for the citry-core release artifact gates."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts import build_citry_core_pyodide_wheel as pyodide_builder  # noqa: E402
from scripts import select_citry_core_qualification as qualification_selector  # noqa: E402
from scripts import verify_citry_core_distribution as distribution_verifier  # noqa: E402
from scripts.build_citry_core_pyodide_wheel import (  # noqa: E402
    PyodideBuildError,
    expected_wheel_name,
    load_build_config,
)
from scripts.select_citry_core_qualification import (  # noqa: E402
    QualificationSelectionError,
    select_artifact,
    select_run,
)
from scripts.verify_citry_core_distribution import (  # noqa: E402
    DistributionVerificationError,
    expected_release_filenames,
    hex_sha256,
    promote_qualification_archive,
    source_inventory,
    stage_and_verify,
    verify_staged_bundle,
    verify_wheel,
)


def _write_wheel(
    path: Path,
    *,
    dist_info: str = "citry_core-1.5.0.dist-info",
    root_is_purelib: str = "false",
    extension: str = "citry_core/_rust.cpython-314-wasm32-emscripten.so",
    tag: str = "cp314-cp314-pyemscripten_2026_0_wasm32",
    extra_members: dict[str, bytes] | None = None,
) -> None:
    members = {name: (ROOT / "packages" / "py" / "citry_core" / name).read_bytes() for name in source_inventory()}
    members[extension] = b"native-extension"
    members[f"{dist_info}/METADATA"] = (
        b"Metadata-Version: 2.4\nName: citry_core\nVersion: 1.5.0\nRequires-Python: >=3.10, <4.0\n"
    )
    members[f"{dist_info}/WHEEL"] = (f"Wheel-Version: 1.0\nRoot-Is-Purelib: {root_is_purelib}\nTag: {tag}\n").encode()
    members[f"{dist_info}/licenses/LICENSE"] = (ROOT / "packages" / "py" / "citry_core" / "LICENSE").read_bytes()
    members[f"{dist_info}/sboms/citry_core_py.cyclonedx.json"] = b'{"bomFormat":"CycloneDX"}\n'
    members.update(extra_members or {})
    record = io.StringIO()
    rows = csv.writer(record, lineterminator="\n")
    for name, payload in sorted(members.items()):
        rows.writerow((name, f"sha256={_record_digest(payload)}", len(payload)))
    rows.writerow((f"{dist_info}/RECORD", "", ""))
    members[f"{dist_info}/RECORD"] = record.getvalue().encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def _record_digest(payload: bytes) -> str:
    import base64
    import hashlib

    return base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()


def test_expected_release_inventory_is_closed_and_includes_the_browser_wheel() -> None:
    names = expected_release_filenames("1.5.0")

    assert len(names) == 36
    assert "citry_core-1.5.0.tar.gz" in names
    assert "citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl" in names
    assert sum(name.endswith(".whl") for name in names) == 35
    assert sum("cp310-abi3" in name for name in names) == 14
    assert sum("pypy311_pp73" in name for name in names) == 10
    assert sum("cp314t" in name for name in names) == 10
    assert "citry_core-1.5.0-cp310-abi3-manylinux_2_5_i686.manylinux1_i686.whl" in names
    assert not any("cp311-cp311" in name for name in names)
    assert not any("manylinux_2_17_i686" in name for name in names)


def test_package_version_falls_back_without_python_311_tomllib(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(distribution_verifier, "_tomllib", None)

    assert distribution_verifier.package_version() == "1.5.0"


def test_pyodide_build_config_owns_the_exact_wheel_name() -> None:
    config = load_build_config()

    assert config["rust"] == "1.95.0"
    assert expected_wheel_name("1.5.0", config) == ("citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl")


def test_pyodide_builder_checks_the_installed_emscripten_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pyodide_builder,
        "_capture",
        lambda *args, **kwargs: "emcc (Emscripten gcc/clang-like replacement) 5.0.3 (commit)",  # noqa: ARG005
    )
    pyodide_builder._verify_emscripten_version(Path("emcc"), cwd=ROOT, expected="5.0.3")

    with pytest.raises(PyodideBuildError, match=r"expected Emscripten 5\.0\.4, found '5\.0\.3'"):
        pyodide_builder._verify_emscripten_version(Path("emcc"), cwd=ROOT, expected="5.0.4")


def test_wheel_verifier_checks_payload_metadata_extension_license_and_record(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel)

    report = verify_wheel(wheel, version="1.5.0")

    assert report["name"] == wheel.name
    assert report["sha256"] == hex_sha256(wheel.read_bytes())
    assert report["extension"] == "citry_core/_rust.cpython-314-wasm32-emscripten.so"


def test_wheel_verifier_accepts_the_canonical_abi3_extension(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.5.0-cp310-abi3-macosx_11_0_arm64.whl"
    _write_wheel(
        wheel,
        extension="citry_core/_rust.abi3.so",
        tag="cp310-abi3-macosx_11_0_arm64",
    )

    report = verify_wheel(wheel, version="1.5.0")

    assert report["extension"] == "citry_core/_rust.abi3.so"

    windows_wheel = tmp_path / "citry_core-1.5.0-cp310-abi3-win_amd64.whl"
    _write_wheel(
        windows_wheel,
        extension="citry_core/_rust.pyd",
        tag="cp310-abi3-win_amd64",
    )

    windows_report = verify_wheel(windows_wheel, version="1.5.0")

    assert windows_report["extension"] == "citry_core/_rust.pyd"


def test_wheel_verifier_rejects_an_unchecked_python_payload(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel)
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("citry_core/extra.py", "surprise = True\n")

    with pytest.raises(DistributionVerificationError, match="Python payload differs"):
        verify_wheel(wheel, version="1.5.0")


def test_wheel_verifier_rejects_a_recorded_installer_script(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel, extra_members={"citry_core-1.5.0.data/scripts/surprise": b"#!/bin/sh\n"})

    with pytest.raises(DistributionVerificationError, match="member inventory mismatch"):
        verify_wheel(wheel, version="1.5.0")


def test_wheel_verifier_accepts_only_the_reviewed_musllinux_repair_library(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wheel = tmp_path / "citry_core-1.5.0-cp314-cp314-musllinux_1_2_aarch64.whl"
    library_name = "citry_core.libs/libgcc_s-reviewed.so.1"
    library = b"\x7fELF-reviewed-libgcc"
    monkeypatch.setitem(
        distribution_verifier.MUSLLINUX_LIBGCC,
        "musllinux_1_2_aarch64",
        (library_name, len(library), hex_sha256(library)),
    )
    _write_wheel(
        wheel,
        extension="citry_core/_rust.cpython-314-aarch64-linux-musl.so",
        tag="cp314-cp314-musllinux_1_2_aarch64",
        extra_members={library_name: library},
    )

    verify_wheel(wheel, version="1.5.0")

    _write_wheel(
        wheel,
        extension="citry_core/_rust.cpython-314-aarch64-linux-musl.so",
        tag="cp314-cp314-musllinux_1_2_aarch64",
        extra_members={library_name: b"\x7fELF-tampered-libgcc"},
    )
    with pytest.raises(DistributionVerificationError, match=r"reviewed .* repair payload"):
        verify_wheel(wheel, version="1.5.0")


def test_wheel_verifier_requires_the_canonical_metadata_directory(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel, dist_info="other-1.5.0.dist-info")

    with pytest.raises(DistributionVerificationError, match=r"canonical .* metadata directory"):
        verify_wheel(wheel, version="1.5.0")


def test_wheel_verifier_rejects_a_purelib_native_wheel(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel, root_is_purelib="true")

    with pytest.raises(DistributionVerificationError, match="must be a platform wheel"):
        verify_wheel(wheel, version="1.5.0")


def test_inventory_rejects_duplicate_basenames_before_staging(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "first").mkdir(parents=True)
    (raw / "second").mkdir()
    for directory in (raw / "first", raw / "second"):
        (directory / "citry_core-1.5.0.tar.gz").write_bytes(b"duplicate")

    with pytest.raises(DistributionVerificationError, match="duplicate artifact basenames"):
        stage_and_verify(raw, tmp_path / "verified")


def test_staged_bundle_requires_the_recorded_artifact_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    wheel = bundle / "citry_core-1.5.0-cp310-abi3-test.whl"
    wheel.write_bytes(b"qualified-wheel")
    artifact_report = {"name": wheel.name, "bytes": len(wheel.read_bytes()), "sha256": hex_sha256(wheel.read_bytes())}
    (bundle / "release-inventory.json").write_text(
        json.dumps({"version": "1.5.0", "artifacts": [artifact_report]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(distribution_verifier, "expected_release_filenames", lambda _version: {wheel.name})
    monkeypatch.setattr(distribution_verifier, "verify_wheel", lambda _path, **_kwargs: artifact_report)

    assert verify_staged_bundle(bundle)["artifacts"] == [artifact_report]

    wheel.write_bytes(b"different-wheel")
    changed_report = {**artifact_report, "bytes": len(wheel.read_bytes()), "sha256": hex_sha256(wheel.read_bytes())}
    monkeypatch.setattr(distribution_verifier, "verify_wheel", lambda _path, **_kwargs: changed_report)
    with pytest.raises(DistributionVerificationError, match="does not match the qualified artifact bytes"):
        verify_staged_bundle(bundle)


def test_promotion_checks_github_digest_before_safe_extraction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "qualification.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("release-inventory.json", "{}\n")
    digest = f"sha256:{hashlib.sha256(archive.read_bytes()).hexdigest()}"
    expected_report = {"version": "1.5.0", "artifacts": []}
    monkeypatch.setattr(distribution_verifier, "verify_staged_bundle", lambda _directory: expected_report)

    assert (
        promote_qualification_archive(archive, expected_digest=digest, output_dir=tmp_path / "out") == expected_report
    )

    with pytest.raises(DistributionVerificationError, match="does not match GitHub"):
        promote_qualification_archive(
            archive,
            expected_digest=f"sha256:{'0' * 64}",
            output_dir=tmp_path / "wrong",
        )


def test_qualification_selector_requires_the_exact_successful_main_commit() -> None:
    commit = "a" * 40
    run = {
        "id": 42,
        "run_number": 7,
        "run_attempt": 1,
        "html_url": "https://github.com/citry-dev/citry/actions/runs/42",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": commit,
        "head_branch": "main",
        "head_repository": {"full_name": "citry-dev/citry"},
    }

    assert select_run({"workflow_runs": [run]}, repository="citry-dev/citry", commit=commit) == run

    with pytest.raises(QualificationSelectionError, match="no successful manual qualification"):
        select_run(
            {"workflow_runs": [{**run, "head_branch": "review"}]},
            repository="citry-dev/citry",
            commit=commit,
        )


def test_qualification_selector_requires_one_live_artifact_for_the_commit() -> None:
    commit = "b" * 40
    artifact = {
        "id": 99,
        "name": qualification_selector.ARTIFACT_NAME,
        "expired": False,
        "digest": f"sha256:{'c' * 64}",
        "workflow_run": {"head_sha": commit, "id": 42},
    }

    assert select_artifact({"artifacts": [artifact]}, commit=commit, run_id=42) == artifact

    with pytest.raises(QualificationSelectionError, match="one live"):
        select_artifact({"artifacts": [{**artifact, "expired": True}]}, commit=commit)
