"""Focused tests for the citry-core release artifact gates."""

from __future__ import annotations

import csv
import io
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts import build_citry_core_pyodide_wheel as pyodide_builder  # noqa: E402
from scripts import verify_citry_core_distribution as distribution_verifier  # noqa: E402
from scripts.build_citry_core_pyodide_wheel import (  # noqa: E402
    PyodideBuildError,
    expected_wheel_name,
    load_build_config,
)
from scripts.verify_citry_core_distribution import (  # noqa: E402
    DistributionVerificationError,
    expected_release_filenames,
    hex_sha256,
    source_inventory,
    stage_and_verify,
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

    assert len(names) == 92
    assert "citry_core-1.5.0.tar.gz" in names
    assert "citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl" in names
    assert sum(name.endswith(".whl") for name in names) == 91
    assert sum("pypy311_pp73" in name for name in names) == 10
    assert sum("cp314t" in name for name in names) == 10
    assert "citry_core-1.5.0-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.whl" in names
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
