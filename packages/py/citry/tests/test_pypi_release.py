import json
from pathlib import Path

import pytest
from scripts.pypi_release import PyPIReleaseError, main, upload_required


def _inventory() -> dict:
    return {
        "version": "0.4.7",
        "artifacts": [
            {"name": "citry-0.4.7-py3-none-any.whl", "sha256": "a" * 64},
            {"name": "citry-0.4.7.tar.gz", "sha256": "b" * 64},
        ],
    }


def _payload(*, wheel_digest: str = "a" * 64) -> dict:
    return {
        "urls": [
            {"filename": "citry-0.4.7.tar.gz", "digests": {"sha256": "b" * 64}},
            {"filename": "citry-0.4.7-py3-none-any.whl", "digests": {"sha256": wheel_digest}},
        ]
    }


def test_absent_release_requires_an_upload() -> None:
    assert upload_required(status=404, inventory=_inventory(), payload=None) is True


def test_exact_public_release_is_a_safe_retry() -> None:
    assert upload_required(status=200, inventory=_inventory(), payload=_payload()) is False


def test_different_public_bytes_stop_recovery() -> None:
    with pytest.raises(PyPIReleaseError, match=r"changed=\['citry-0\.4\.7-py3-none-any\.whl'\]"):
        upload_required(status=200, inventory=_inventory(), payload=_payload(wheel_digest="c" * 64))


def _partial_payload() -> dict:
    # An upload that stopped after the sdist: PyPI lists one of the two files.
    return {"urls": [{"filename": "citry-0.4.7.tar.gz", "digests": {"sha256": "b" * 64}}]}


def test_partial_release_resumes_only_before_an_upload() -> None:
    # The check before an upload lets the rest be sent with skip-existing.
    assert upload_required(status=200, inventory=_inventory(), payload=_partial_payload(), allow_partial=True) is True


def test_partial_release_fails_the_check_after_an_upload() -> None:
    # Without the flag the check demands every file, so a verify step cannot
    # pass while a wheel is still missing.
    with pytest.raises(PyPIReleaseError, match=r"missing=\['citry-0\.4\.7-py3-none-any\.whl'\]"):
        upload_required(status=200, inventory=_inventory(), payload=_partial_payload())


def test_partial_release_with_a_changed_file_still_stops() -> None:
    payload = {"urls": [{"filename": "citry-0.4.7.tar.gz", "digests": {"sha256": "c" * 64}}]}

    with pytest.raises(PyPIReleaseError, match=r"changed=\['citry-0\.4\.7\.tar\.gz'\]"):
        upload_required(status=200, inventory=_inventory(), payload=payload, allow_partial=True)


def test_a_public_file_qualification_never_made_stops() -> None:
    payload = _payload()
    payload["urls"].append({"filename": "citry-0.4.7-py2-none-any.whl", "digests": {"sha256": "d" * 64}})

    with pytest.raises(PyPIReleaseError, match=r"unexpected=\['citry-0\.4\.7-py2-none-any\.whl'\]"):
        upload_required(status=200, inventory=_inventory(), payload=payload, allow_partial=True)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (None, ["publish=true", "skip_existing=false"]),
        (_partial_payload(), ["publish=true", "skip_existing=true"]),
        (_payload(), ["publish=false", "skip_existing=false"]),
    ],
)
def test_the_workflow_output_turns_on_skip_existing_only_for_a_partial_release(
    tmp_path: Path, payload: dict | None, expected: list[str]
) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps(_inventory()), encoding="utf-8")
    output = tmp_path / "github-output"
    argv = ["--status", "404" if payload is None else "200", "--inventory", str(inventory)]
    if payload is not None:
        (tmp_path / "pypi.json").write_text(json.dumps(payload), encoding="utf-8")
        argv += ["--pypi-json", str(tmp_path / "pypi.json")]

    assert main([*argv, "--github-output", str(output), "--allow-partial"]) == 0
    assert output.read_text(encoding="utf-8").splitlines() == expected
