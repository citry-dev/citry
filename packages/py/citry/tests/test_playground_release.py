import pytest
from scripts.verify_playground_release import (
    PlaygroundReleaseError,
    validate_published_runtime,
    verify_runtime_pin,
)


def _runtime(*, version: str = "0.4.7", digest: str = "a" * 64) -> dict:
    return {
        "schema_version": 1,
        "protocol_version": 1,
        "source": "published",
        "pyodide": {
            "version": "314.0.3",
            "python": "3.14.2",
            "index_url": "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/",
            "module_url": "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/pyodide.mjs",
        },
        "citry": {"version": version, "core_version": version, "ui_version": version},
        "packages": [
            {
                "name": "citry-core",
                "version": version,
                "source": "pypi",
                "filename": f"citry_core-{version}-cp314-cp314-pyemscripten_2026_0_wasm32.whl",
                "sha256": digest,
            },
            {
                "name": "citry",
                "version": version,
                "source": "pypi",
                "filename": f"citry-{version}-py3-none-any.whl",
                "sha256": digest,
            },
            {
                "name": "citry-ui",
                "version": version,
                "source": "pypi",
                "filename": f"citry_ui-{version}-py3-none-any.whl",
                "sha256": digest,
            },
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


def test_workspace_runtime_is_not_accepted_at_the_published_release_boundary() -> None:
    runtime = _runtime()
    runtime["source"] = "workspace"

    with pytest.raises(PlaygroundReleaseError, match="source 'published'"):
        verify_runtime_pin(
            runtime=runtime,
            inventory=_inventory(),
            package_name="citry",
            wheel_pattern="*.whl",
        )


@pytest.mark.parametrize("url", ["./local/citry.whl", "local/citry.whl"])
def test_relative_package_url_is_not_accepted_at_the_published_release_boundary(url: str) -> None:
    runtime = _runtime()
    package = next(package for package in runtime["packages"] if package["name"] == "citry")
    package["source"] = "url"
    package.pop("filename")
    package.pop("sha256")
    package["url"] = url

    with pytest.raises(PlaygroundReleaseError, match=r"approved .*HTTPS URL"):
        verify_runtime_pin(
            runtime=runtime,
            inventory=_inventory(),
            package_name="citry",
            wheel_pattern="*.whl",
        )


@pytest.mark.parametrize(
    "package",
    [
        {"version": "1.0.0", "source": "pypi", "filename": "x.whl", "sha256": "a" * 64},
        {"name": "x", "source": "pypi", "filename": "x.whl", "sha256": "a" * 64},
        {
            "name": "x",
            "version": "1.0.0",
            "source": "pypi",
            "filename": "x.whl",
            "sha256": "A" * 64,
        },
        {
            "name": "x",
            "version": "1.0.0",
            "source": "pypi",
            "filename": "x.whl",
            "sha256": "a" * 63,
        },
    ],
)
def test_published_runtime_rejects_missing_identity_or_unqualified_pypi_digest(package: dict) -> None:
    runtime = _runtime()
    runtime["packages"].append(package)

    with pytest.raises(PlaygroundReleaseError, match=r"(?:name and version|filename or SHA-256)"):
        validate_published_runtime(runtime)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/package.whl",
        "https://user:password@cdn.jsdelivr.net/package.whl",
        "https://cdn.jsdelivr.net:444/package.whl",
        "https://cdn.jsdelivr.net/package.whl?redirect=elsewhere",
        "https://[broken/package.whl",
    ],
)
def test_published_runtime_rejects_unapproved_direct_package_urls(url: str) -> None:
    runtime = _runtime()
    runtime["packages"].append({"name": "x", "version": "1.0.0", "source": "url", "url": url})

    with pytest.raises(PlaygroundReleaseError, match=r"approved .*HTTPS URL"):
        validate_published_runtime(runtime)


def test_published_runtime_accepts_the_pyodide_cdn_origin_for_direct_packages() -> None:
    runtime = _runtime()
    runtime["packages"].append(
        {
            "name": "MarkupSafe",
            "version": "3.0.3",
            "source": "url",
            "url": "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/markupsafe-3.0.3.whl",
        }
    )

    validate_published_runtime(runtime)


def test_published_runtime_rejects_duplicate_normalized_package_names() -> None:
    runtime = _runtime()
    citry = next(package for package in runtime["packages"] if package["name"] == "citry")
    runtime["packages"].append(dict(citry, name="CITRY"))

    with pytest.raises(PlaygroundReleaseError, match="duplicate package"):
        validate_published_runtime(runtime)


def test_published_runtime_requires_the_complete_citry_tuple() -> None:
    runtime = _runtime()
    runtime["packages"] = []

    with pytest.raises(PlaygroundReleaseError, match="missing package"):
        validate_published_runtime(runtime)


def test_published_runtime_requires_consistent_citry_versions() -> None:
    runtime = _runtime()
    runtime["citry"]["ui_version"] = "9.9.9"

    with pytest.raises(PlaygroundReleaseError, match="disagrees with citry config"):
        validate_published_runtime(runtime)


@pytest.mark.parametrize("field", ["index_url", "module_url"])
def test_published_runtime_rejects_unpinned_pyodide_urls(field: str) -> None:
    runtime = _runtime()
    runtime["pyodide"][field] = "https://example.com/pyodide.mjs"

    with pytest.raises(PlaygroundReleaseError, match="Pyodide CDN URLs"):
        validate_published_runtime(runtime)
