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
    dist_info: str = "citry_core-1.7.0.dist-info",
    root_is_purelib: str = "false",
    extension: str = "citry_core/_rust.cpython-314-wasm32-emscripten.so",
    tag: str = "cp314-cp314-pyemscripten_2026_0_wasm32",
    extra_members: dict[str, bytes] | None = None,
) -> None:
    members = {name: (ROOT / "packages" / "py" / "citry_core" / name).read_bytes() for name in source_inventory()}
    members[extension] = b"native-extension"
    members[f"{dist_info}/METADATA"] = (
        b"Metadata-Version: 2.4\nName: citry_core\nVersion: 1.7.0\nRequires-Python: >=3.11, <4.0\n"
        b"License-File: LICENSE\nLicense-File: LICENSE-vize\nLicense-File: LICENSE-html5gum\n"
    )
    members[f"{dist_info}/WHEEL"] = (f"Wheel-Version: 1.0\nRoot-Is-Purelib: {root_is_purelib}\nTag: {tag}\n").encode()
    members[f"{dist_info}/licenses/LICENSE"] = (ROOT / "packages" / "py" / "citry_core" / "LICENSE").read_bytes()
    members[f"{dist_info}/licenses/LICENSE-vize"] = (
        ROOT / "packages" / "py" / "citry_core" / "LICENSE-vize"
    ).read_bytes()
    members[f"{dist_info}/licenses/LICENSE-html5gum"] = (
        ROOT / "packages" / "py" / "citry_core" / "LICENSE-html5gum"
    ).read_bytes()
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
    names = expected_release_filenames("1.7.0")

    assert len(names) == 46
    assert "citry_core-1.7.0.tar.gz" in names
    assert "citry_core-1.7.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl" in names
    assert sum(name.endswith(".whl") for name in names) == 45
    assert sum("cp311-abi3" in name for name in names) == 14
    assert sum("pypy311_pp73" in name for name in names) == 10
    assert sum("cp314t" in name for name in names) == 10
    assert sum("cp315t" in name for name in names) == 10
    assert "citry_core-1.7.0-cp311-abi3-manylinux_2_5_i686.manylinux1_i686.whl" in names
    assert not any("cp311-cp311" in name for name in names)
    assert not any("manylinux_2_17_i686" in name for name in names)


def test_pyodide_build_config_owns_the_exact_wheel_name() -> None:
    config = load_build_config()

    assert config["rust"] == "1.97.0"
    assert expected_wheel_name("1.7.0", config) == ("citry_core-1.7.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl")


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
    wheel = tmp_path / "citry_core-1.7.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel)

    report = verify_wheel(wheel, version="1.7.0")

    assert report["name"] == wheel.name
    assert report["sha256"] == hex_sha256(wheel.read_bytes())
    assert report["extension"] == "citry_core/_rust.cpython-314-wasm32-emscripten.so"


def test_wheel_verifier_accepts_the_canonical_abi3_extension(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.7.0-cp311-abi3-macosx_11_0_arm64.whl"
    _write_wheel(
        wheel,
        extension="citry_core/_rust.abi3.so",
        tag="cp311-abi3-macosx_11_0_arm64",
    )

    report = verify_wheel(wheel, version="1.7.0")

    assert report["extension"] == "citry_core/_rust.abi3.so"

    windows_wheel = tmp_path / "citry_core-1.7.0-cp311-abi3-win_amd64.whl"
    _write_wheel(
        windows_wheel,
        extension="citry_core/_rust.pyd",
        tag="cp311-abi3-win_amd64",
    )

    windows_report = verify_wheel(windows_wheel, version="1.7.0")

    assert windows_report["extension"] == "citry_core/_rust.pyd"


def test_wheel_verifier_rejects_an_unchecked_python_payload(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.7.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel)
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("citry_core/extra.py", "surprise = True\n")

    with pytest.raises(DistributionVerificationError, match="Python payload differs"):
        verify_wheel(wheel, version="1.7.0")


def test_wheel_verifier_requires_exact_upstream_license_attribution(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.7.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(
        wheel,
        extra_members={"citry_core-1.7.0.dist-info/licenses/LICENSE-vize": b"changed\n"},
    )

    with pytest.raises(DistributionVerificationError, match="checked license inventory"):
        verify_wheel(wheel, version="1.7.0")


def test_patched_crate_inventory_closes_source_and_attribution() -> None:
    inventory = distribution_verifier.patched_crate_inventory()

    assert "third_party/rust/vize_atelier_core/Cargo.toml" in inventory
    assert "third_party/rust/vize_atelier_core/LICENSE" in inventory
    assert "third_party/rust/vize_atelier_core/README.citry.md" in inventory
    assert "third_party/rust/vize_atelier_core/src/codegen/v_for/generate.rs" in inventory
    assert "third_party/rust/vize_s1_to_s2/Cargo.toml" in inventory
    assert "third_party/rust/vize_s1_to_s2/LICENSE" in inventory
    assert "third_party/rust/vize_s1_to_s2/README.citry.md" in inventory
    assert "third_party/rust/vize_s1_to_s2/src/emit/directive.rs" in inventory
    assert all(
        name.startswith(
            (
                "third_party/rust/vize_atelier_core/",
                "third_party/rust/vize_s1_to_s2/",
            )
        )
        for name in inventory
    )


# The SHA-256 of the LICENSE file inside each html5gum release whose notice
# has been compared with packages/py/citry_core/LICENSE-html5gum. To add a
# release, read the LICENSE in its crates.io archive (in the cargo registry
# source folder, or `tar -xzOf html5gum-X.Y.Z.crate html5gum-X.Y.Z/LICENSE`),
# update LICENSE-html5gum if the text changed, and add the digest here.
HTML5GUM_LICENSE_SHA256 = {
    "0.9.1": "d8c0537cc294880316b3a28a7fd4eeccf1254fa955851582cac46fd048f9e8db",
}


def test_wheel_html5gum_license_is_the_locked_crate_license() -> None:
    # The wheel ships compiled html5gum code but not its source, so the
    # license file next to the package must carry the notice of the html5gum
    # release that Cargo.lock builds.
    lock = distribution_verifier._loads_toml((ROOT / "Cargo.lock").read_text(encoding="utf-8"))
    locked = {package["version"] for package in lock["package"] if package["name"] == "html5gum"}
    package_license = ROOT / "packages" / "py" / "citry_core" / "LICENSE-html5gum"

    assert locked, "Cargo.lock does not lock html5gum"
    unchecked = sorted(locked - HTML5GUM_LICENSE_SHA256.keys())
    assert not unchecked, f"html5gum {unchecked} is locked but its LICENSE is not in HTML5GUM_LICENSE_SHA256"
    assert {hex_sha256(package_license.read_bytes())} == {HTML5GUM_LICENSE_SHA256[version] for version in locked}


def test_pyproject_declares_attribution_and_tracks_patch_build_inputs() -> None:
    manifest = distribution_verifier._loads_toml(
        (ROOT / "packages" / "py" / "citry_core" / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert manifest["project"]["license-files"] == ["LICENSE", "LICENSE-vize", "LICENSE-html5gum"]
    assert "include" not in manifest["tool"]["maturin"]
    cache_files = {entry["file"] for entry in manifest["tool"]["uv"]["cache-keys"]}
    assert "../../../third_party/rust/vize_atelier_core/**/*.rs" in cache_files
    assert "../../../third_party/rust/vize_atelier_core/Cargo.toml" in cache_files
    assert "../../../third_party/rust/vize_s1_to_s2/**/*.rs" in cache_files
    assert "../../../third_party/rust/vize_s1_to_s2/Cargo.toml" in cache_files


def test_wheel_verifier_rejects_a_recorded_installer_script(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.7.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel, extra_members={"citry_core-1.7.0.data/scripts/surprise": b"#!/bin/sh\n"})

    with pytest.raises(DistributionVerificationError, match="member inventory mismatch"):
        verify_wheel(wheel, version="1.7.0")


def test_wheel_verifier_accepts_only_the_reviewed_musllinux_repair_library(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wheel = tmp_path / "citry_core-1.7.0-cp314-cp314-musllinux_1_2_aarch64.whl"
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

    verify_wheel(wheel, version="1.7.0")

    _write_wheel(
        wheel,
        extension="citry_core/_rust.cpython-314-aarch64-linux-musl.so",
        tag="cp314-cp314-musllinux_1_2_aarch64",
        extra_members={library_name: b"\x7fELF-tampered-libgcc"},
    )
    with pytest.raises(DistributionVerificationError, match=r"reviewed .* repair payload"):
        verify_wheel(wheel, version="1.7.0")


def test_wheel_verifier_requires_the_canonical_metadata_directory(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.7.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel, dist_info="other-1.7.0.dist-info")

    with pytest.raises(DistributionVerificationError, match=r"canonical .* metadata directory"):
        verify_wheel(wheel, version="1.7.0")


def test_wheel_verifier_rejects_a_purelib_native_wheel(tmp_path: Path) -> None:
    wheel = tmp_path / "citry_core-1.7.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
    _write_wheel(wheel, root_is_purelib="true")

    with pytest.raises(DistributionVerificationError, match="must be a platform wheel"):
        verify_wheel(wheel, version="1.7.0")


def _reverse_joined_tags(name: str) -> str:
    """Write each dot-joined group of tags in a wheel name in the opposite order, as another builder may."""
    if not name.endswith(".whl"):
        return name
    *leading, python, abi, platform = name.removesuffix(".whl").split("-")
    reversed_sets = (".".join(reversed(tags.split("."))) for tags in (python, abi, platform))
    return "-".join([*leading, *reversed_sets]) + ".whl"


def test_release_inventory_accepts_every_wheel_with_its_tags_in_the_other_order() -> None:
    expected = expected_release_filenames("1.7.0")
    built = {_reverse_joined_tags(name) for name in expected}

    # Reversing really changes the names that carry dot-joined tags, so the
    # comparison below is not trivially passing on identical strings.
    assert built != expected
    assert "citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl" in built
    assert "citry_core-1.7.0-cp311-abi3-manylinux1_i686.manylinux_2_5_i686.whl" in built
    assert distribution_verifier._inventory_difference(expected, built) == ([], [])
    assert distribution_verifier._inventory_difference(expected, expected) == ([], [])


@pytest.mark.parametrize(
    "tag_order",
    ["manylinux_2_17_x86_64.manylinux2014_x86_64", "manylinux2014_x86_64.manylinux_2_17_x86_64"],
)
def test_wheel_verifier_reads_dot_joined_filename_tags_as_a_set(tmp_path: Path, tag_order: str) -> None:
    wheel = tmp_path / f"citry_core-1.7.0-cp311-abi3-{tag_order}.whl"
    # maturin lists each tag of the set on its own line.
    _write_wheel(
        wheel,
        extension="citry_core/_rust.abi3.so",
        tag="cp311-abi3-manylinux2014_x86_64\nTag: cp311-abi3-manylinux_2_17_x86_64",
    )

    report = verify_wheel(wheel, version="1.7.0")

    assert report["name"] == wheel.name
    assert report["tags"] == [
        "cp311-abi3-manylinux2014_x86_64",
        "cp311-abi3-manylinux_2_17_x86_64",
    ]


def test_release_inventory_still_rejects_a_different_set_of_tags() -> None:
    expected = {"citry_core-1.7.0-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"}
    # A wheel that drops one tag of the set is a different file, not a respelling.
    built = {"citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.whl"}

    assert distribution_verifier._inventory_difference(expected, built) == (sorted(expected), sorted(built))


def test_release_inventory_does_not_collapse_a_repeated_tag() -> None:
    expected = {"citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.whl"}
    # A name that lists a tag twice is not a respelling of the expected file.
    built = {"citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.manylinux2014_x86_64.whl"}

    assert distribution_verifier._inventory_difference(expected, built) == (sorted(expected), sorted(built))


def test_release_inventory_refuses_two_spellings_of_one_wheel() -> None:
    names = {
        "citry_core-1.7.0-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
    }

    with pytest.raises(DistributionVerificationError, match="differ only in the order of their tags"):
        distribution_verifier._inventory_difference(names, names)


@pytest.mark.parametrize(
    "built_name",
    [
        "citry_core-1.7.0-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
    ],
)
def test_stage_and_verify_keeps_the_built_name_of_a_wheel_matched_by_tag_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    built_name: str,
) -> None:
    raw = tmp_path / "raw" / "wheels-linux"
    raw.mkdir(parents=True)
    wheel = raw / built_name
    wheel.write_bytes(b"built-wheel")
    # The closed release set always spells the tags one way, whatever order the builder used.
    expected = "citry_core-1.7.0-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
    report = {"name": built_name, "bytes": len(b"built-wheel"), "sha256": hex_sha256(b"built-wheel")}
    monkeypatch.setattr(distribution_verifier, "expected_release_filenames", lambda _version: {expected})
    monkeypatch.setattr(distribution_verifier, "package_version", lambda: "1.7.0")
    monkeypatch.setattr(distribution_verifier, "verify_wheel", lambda _path, **_kwargs: report)

    staged = stage_and_verify(tmp_path / "raw", tmp_path / "verified")

    assert staged["artifacts"] == [report]
    assert sorted(path.name for path in (tmp_path / "verified").iterdir()) == [built_name, "release-inventory.json"]
    assert json.loads((tmp_path / "verified" / "release-inventory.json").read_text()) == staged

    # The qualification bundle is re-checked later against the same closed set, so it must agree.
    assert verify_staged_bundle(tmp_path / "verified") == staged


@pytest.mark.parametrize("problem", ["short_tag_set", "missing_inventory", "stray_file"])
def test_staged_bundle_rejects_a_changed_file_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    problem: str,
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    expected = "citry_core-1.7.0-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
    built = "citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.whl" if problem == "short_tag_set" else expected
    (bundle / built).write_bytes(b"wheel")
    if problem != "missing_inventory":
        (bundle / "release-inventory.json").write_text("{}", encoding="utf-8")
    if problem == "stray_file":
        (bundle / "notes.txt").write_text("extra", encoding="utf-8")
    monkeypatch.setattr(distribution_verifier, "expected_release_filenames", lambda _version: {expected})
    monkeypatch.setattr(distribution_verifier, "package_version", lambda: "1.7.0")

    with pytest.raises(DistributionVerificationError, match="qualification bundle mismatch"):
        verify_staged_bundle(bundle)


def test_stage_and_verify_names_the_files_of_a_real_inventory_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.whl").write_bytes(b"short-tag-set")
    expected = "citry_core-1.7.0-cp311-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
    monkeypatch.setattr(distribution_verifier, "expected_release_filenames", lambda _version: {expected})
    monkeypatch.setattr(distribution_verifier, "package_version", lambda: "1.7.0")

    with pytest.raises(DistributionVerificationError, match="release inventory mismatch") as error:
        stage_and_verify(raw, tmp_path / "verified")

    assert expected in str(error.value)
    assert "citry_core-1.7.0-cp311-abi3-manylinux2014_x86_64.whl" in str(error.value)


def test_inventory_rejects_duplicate_basenames_before_staging(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    (raw / "first").mkdir(parents=True)
    (raw / "second").mkdir()
    for directory in (raw / "first", raw / "second"):
        (directory / "citry_core-1.7.0.tar.gz").write_bytes(b"duplicate")

    with pytest.raises(DistributionVerificationError, match="duplicate artifact basenames"):
        stage_and_verify(raw, tmp_path / "verified")


def test_staged_bundle_requires_the_recorded_artifact_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    wheel = bundle / "citry_core-1.7.0-cp311-abi3-test.whl"
    wheel.write_bytes(b"qualified-wheel")
    artifact_report = {"name": wheel.name, "bytes": len(wheel.read_bytes()), "sha256": hex_sha256(wheel.read_bytes())}
    (bundle / "release-inventory.json").write_text(
        json.dumps({"version": "1.7.0", "artifacts": [artifact_report]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(distribution_verifier, "expected_release_filenames", lambda _version: {wheel.name})
    monkeypatch.setattr(distribution_verifier, "package_version", lambda: "1.7.0")
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
    expected_report = {"version": "1.7.0", "artifacts": []}
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


def _assert_hashed_build_pins(command: list[str]) -> None:
    # --no-config hides the root build pins, so the rebuild must get them as a hashed file.
    index = command.index("--build-constraints")
    assert command[index + 2] == "--require-hashes"
    assert "--hash=sha256:" in Path(command[index + 1]).read_text(encoding="utf-8")


def test_sdist_smoke_rebuild_gets_the_hashed_build_pins(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], *, cwd: Path, env: object = None) -> str:
        del env
        _assert_hashed_build_pins(command)
        output = Path(command[command.index("--out-dir") + 1])
        output.mkdir(parents=True)
        (output / "rebuilt.whl").write_bytes(b"wheel")
        return ""

    monkeypatch.setattr(distribution_verifier, "verify_sdist", lambda *args, **kwargs: None)  # noqa: ARG005
    monkeypatch.setattr(distribution_verifier, "verify_wheel", lambda *args, **kwargs: {})  # noqa: ARG005
    monkeypatch.setattr(distribution_verifier, "smoke_wheel", lambda *args, **kwargs: {})  # noqa: ARG005
    monkeypatch.setattr(distribution_verifier, "_run", fake_run)
    report = distribution_verifier.smoke_sdist(Path("citry_core.tar.gz"), rust_toolchain="1.97.0")
    assert report["sdist"] == "citry_core.tar.gz"


def _pyodide_tree(tmp_path: Path) -> tuple[Path, Path, dict[str, str | int]]:
    # The smallest workspace and cross-build environment that build_wheel accepts.
    workspace = tmp_path / "workspace"
    source = workspace / "packages" / "py" / "citry_core"
    (source / "citry_core").mkdir(parents=True)
    (source / "pyproject.toml").write_text("[project]\nversion = '1.0.0'\n", encoding="utf-8")
    (source / "pyodide-build.json").write_text((ROOT / "packages/py/citry_core/pyodide-build.json").read_text())
    (workspace / "Cargo.toml").write_text("", encoding="utf-8")
    (workspace / "pyproject.toml").write_text((ROOT / "pyproject.toml").read_text(), encoding="utf-8")
    config = load_build_config(source / "pyodide-build.json")
    xbuildenv = tmp_path / "xbuildenv"
    pyodide_root = xbuildenv / str(config["pyodide"])
    for relative in (
        "xbuildenv/pyodide-root/dist/pyodide.mjs",
        "emsdk/upstream/bin/wasm-opt",
        "emsdk/upstream/emscripten/emcc",
    ):
        (pyodide_root / relative).parent.mkdir(parents=True, exist_ok=True)
        (pyodide_root / relative).write_bytes(b"")
    (tmp_path / "cargo-home").mkdir()
    return source, xbuildenv, config


def _build_pyodide(tmp_path: Path, source: Path, xbuildenv: Path) -> None:
    pyodide_builder.build_wheel(
        source=source,
        out_dir=tmp_path / "out",
        xbuildenv_path=xbuildenv,
        cargo_target_dir=tmp_path / "target",
        source_date_epoch=1,
        cargo_home=tmp_path / "cargo-home",
    )


def test_pyodide_build_checks_the_maturin_hash_through_uv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source, xbuildenv, config = _pyodide_tree(tmp_path)
    seen: dict[str, str] = {}

    def fake_run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
        del command, cwd
        assert env is not None
        # pyodide-build's `uv pip install` reads the pins from this file and checks their hashes.
        seen["constraints"] = Path(env["UV_CONSTRAINT"]).read_text(encoding="utf-8")
        wheel = tmp_path / "out" / expected_wheel_name("1.0.0", config)
        wheel.write_bytes(b"wheel")

    monkeypatch.setattr(pyodide_builder, "_verify_emscripten_version", lambda *args, **kwargs: None)  # noqa: ARG005
    monkeypatch.setattr(pyodide_builder, "_normalize_wheel", lambda *args, **kwargs: None)  # noqa: ARG005
    monkeypatch.setattr(pyodide_builder.shutil, "which", lambda name, path=None: f"/bin/{name}")  # noqa: ARG005
    monkeypatch.setattr(pyodide_builder, "_run", fake_run)
    _build_pyodide(tmp_path, source, xbuildenv)
    assert f"maturin=={config['maturin']} \\\n    --hash=sha256:" in seen["constraints"]


def test_pyodide_build_refuses_to_run_without_uv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source, xbuildenv, _ = _pyodide_tree(tmp_path)
    monkeypatch.setattr(pyodide_builder, "_verify_emscripten_version", lambda *args, **kwargs: None)  # noqa: ARG005
    # Without uv, pyodide-build would install maturin with pip and skip the hash check.
    monkeypatch.setattr(pyodide_builder.shutil, "which", lambda name, path=None: None)  # noqa: ARG005
    with pytest.raises(PyodideBuildError, match="uv must be on PATH"):
        _build_pyodide(tmp_path, source, xbuildenv)
