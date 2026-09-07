import pytest
from scripts.pypi_release import PyPIReleaseError, upload_required


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
