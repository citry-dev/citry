import pytest
from scripts.verify_playground_release import PlaygroundReleaseError, verify_runtime_pin


def _runtime(*, version: str = "0.4.7", digest: str = "a" * 64) -> dict:
    return {
        "citry": {"version": version},
        "packages": [
            {
                "name": "citry",
                "version": version,
                "source": "pypi",
                "filename": f"citry-{version}-py3-none-any.whl",
                "sha256": digest,
            }
        ],
    }


def _inventory(*, version: str = "0.4.7", digest: str = "a" * 64) -> dict:
    return {
        "version": version,
        "artifacts": [
            {"name": f"citry-{version}-py3-none-any.whl", "sha256": digest},
            {"name": f"citry-{version}.tar.gz", "sha256": "b" * 64},
        ],
    }


def test_matching_runtime_pin_accepts_the_qualified_wheel() -> None:
    assert verify_runtime_pin(
        runtime=_runtime(),
        inventory=_inventory(),
        package_name="citry",
        wheel_pattern="*.whl",
    )


def test_compatible_older_runtime_does_not_force_an_update() -> None:
    assert not verify_runtime_pin(
        runtime=_runtime(version="0.4.6"),
        inventory=_inventory(),
        package_name="citry",
        wheel_pattern="*.whl",
    )


def test_matching_version_rejects_a_different_qualified_hash() -> None:
    with pytest.raises(PlaygroundReleaseError, match="differs from the qualified wheel"):
        verify_runtime_pin(
            runtime=_runtime(),
            inventory=_inventory(digest="c" * 64),
            package_name="citry",
            wheel_pattern="*.whl",
        )
