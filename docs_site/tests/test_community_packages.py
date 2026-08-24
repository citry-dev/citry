"""Tests for the validated Community package catalog and page projection."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from lxml import html as lxml_html
from starlette.testclient import TestClient

from docs_site._internal.build import build_site
from docs_site._internal.community_packages import (
    CommunityPackageCatalogError,
    community_package_list_markdown,
    current_community_package_catalog,
    load_community_package_catalog,
    use_community_package_catalog,
)
from docs_site._internal.config import DocsConfig
from docs_site._internal.guards import community_packages as community_packages_guard
from docs_site._internal.guards.base import GuardContext
from docs_site._internal.pipeline import render_page
from docs_site._internal.serve import create_app


def _write_catalog(path: Path, packages: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    package_block = f"packages:\n{packages}" if packages else "packages: []\n"
    path.write_text(f"schema_version: 1\n{package_block}", encoding="utf-8")
    return path


def _package(
    distribution: str,
    *,
    name: str,
    categories: str = "      - extension\n",
    published: str = "true",
    source_url: str = "https://example.test/source",
    extra: str = "",
) -> str:
    return (
        f"  - distribution: {distribution}\n"
        f"    name: {name}\n"
        "    categories:\n"
        f"{categories}"
        f"    summary: What {name} provides.\n"
        "    ownership: community\n"
        f"    published: {published}\n"
        '    citry_requirement: ">=1.0.0"\n'
        f"    source_url: {source_url}\n"
        f"    maintainer: {name} maintainers\n"
        f"{extra}"
    )


def test_catalog_loads_immutable_packages_in_name_order_and_projects_categories(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path / "community_packages.yml",
        _package(
            "two-tools",
            name="Zulu tools",
            categories="      - extension\n      - ui_library\n",
        )
        + _package("alpha-ui", name="Alpha UI", categories="      - ui_library\n"),
    )

    catalog = load_community_package_catalog(path)

    assert [package.name for package in catalog.packages] == ["Alpha UI", "Zulu tools"]
    assert [package.distribution for package in catalog.packages_for("extension")] == ["two-tools"]
    assert [package.distribution for package in catalog.packages_for("ui_library")] == [
        "alpha-ui",
        "two-tools",
    ]
    with pytest.raises(FrozenInstanceError):
        catalog.packages[0].name = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("packages", "message", "expected_line"),
    [
        (
            _package("same-name", name="One") + _package("same_name", name="Two"),
            r"duplicates packages\[0\]",
            13,
        ),
        (
            _package("unsafe", name="Unsafe", source_url="http://example.test"),
            "absolute HTTPS",
            3,
        ),
        (
            _package("unknown", name="Unknown", categories="      - something_else\n"),
            "unknown value",
            3,
        ),
        (
            _package("bad-spec", name="Bad spec").replace('">=1.0.0"', '"not a spec"'),
            "valid version specifier",
            3,
        ),
    ],
)
def test_catalog_rejects_invalid_entries_with_the_package_line(
    tmp_path: Path,
    packages: str,
    message: str,
    expected_line: int,
) -> None:
    path = _write_catalog(tmp_path / "community_packages.yml", packages)

    with pytest.raises(CommunityPackageCatalogError, match=message) as caught:
        load_community_package_catalog(path)

    assert caught.value.line == expected_line


def test_catalog_context_is_nested_and_restored(tmp_path: Path) -> None:
    first = load_community_package_catalog(_write_catalog(tmp_path / "first.yml", _package("first", name="First")))
    second = load_community_package_catalog(_write_catalog(tmp_path / "second.yml", _package("second", name="Second")))

    with pytest.raises(RuntimeError, match="No Community package catalog"):
        current_community_package_catalog()
    with use_community_package_catalog(first):
        assert current_community_package_catalog() is first
        with use_community_package_catalog(second):
            assert current_community_package_catalog() is second
        assert current_community_package_catalog() is first
    with pytest.raises(RuntimeError, match="No Community package catalog"):
        current_community_package_catalog()


def test_package_component_renders_cards_and_a_concise_markdown_projection(tmp_path: Path) -> None:
    catalog = load_community_package_catalog(
        _write_catalog(
            tmp_path / "community_packages.yml",
            _package(
                "preview-tool",
                name="Preview tool",
                published="false",
                extra=(
                    "    docs_url: /guide/\n"
                    "    maintainer_url: https://example.test/team\n"
                    "    notice: Preview with a licensing disclosure.\n"
                ),
            ),
        )
    )

    result = render_page(
        '# Packages\n\n<c-community-packages category="extension" />\n',
        community_package_catalog=catalog,
        wrap_in_layout=False,
    )

    assert 'class="community-package-card"' in result.html
    assert 'aria-labelledby="package-preview-tool"' in result.html
    assert "Not yet on PyPI" in result.html
    assert "Preview with a licensing disclosure." in result.html
    assert "pip install preview-tool" not in result.html
    assert "docs-community-packages:start" not in result.markdown_body
    assert "[Preview tool](</guide/>)" in result.markdown_body
    assert "not yet published on PyPI" in result.markdown_body
    assert "Notice: Preview with a licensing disclosure." in result.markdown_body
    assert community_package_list_markdown(catalog, "extension") in result.markdown_body

    document = lxml_html.fragment_fromstring(result.html, create_parent="div")
    external_links = document.xpath('.//a[starts-with(@href, "https://")]')
    assert external_links
    assert all(link.get("target") == "_blank" for link in external_links)
    assert all(link.get("rel") == "noopener" for link in external_links)
    internal_link = document.xpath('.//a[@href="/guide/"]')[0]
    assert internal_link.get("target") is None
    assert internal_link.get("rel") is None


@pytest.mark.parametrize(
    ("source_url", "message"),
    [
        ("/not-a-public-repository/", "absolute HTTPS"),
        (r"https://example.test\escaped", "backslashes"),
        ("https://:443", "absolute HTTPS"),
        ("https://[broken", "valid HTTPS"),
    ],
)
def test_catalog_rejects_ambiguous_or_malformed_source_urls(
    tmp_path: Path,
    source_url: str,
    message: str,
) -> None:
    path = _write_catalog(
        tmp_path / "community_packages.yml",
        _package("unsafe-url", name="Unsafe URL", source_url=source_url),
    )

    with pytest.raises(CommunityPackageCatalogError, match=message):
        load_community_package_catalog(path)


def test_catalog_rejects_browser_origin_escaping_internal_urls(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path / "community_packages.yml",
        _package(
            "unsafe-docs",
            name="Unsafe docs",
            extra="    docs_url: /\\evil.example/path\n",
        ),
    )

    with pytest.raises(CommunityPackageCatalogError, match="backslashes"):
        load_community_package_catalog(path)


def test_catalog_rejects_nonprinting_plain_text(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path / "community_packages.yml",
        _package("hidden-text", name="Hidden\u200btext"),
    )

    with pytest.raises(CommunityPackageCatalogError, match="control characters"):
        load_community_package_catalog(path)


def test_pypi_url_uses_the_normalized_distribution_name(tmp_path: Path) -> None:
    catalog = load_community_package_catalog(
        _write_catalog(
            tmp_path / "community_packages.yml",
            _package("Demo_Pkg", name="Demo package"),
        )
    )

    assert catalog.packages[0].pypi_url == "https://pypi.org/project/demo-pkg/"


def test_markdown_projection_escapes_catalog_text(tmp_path: Path) -> None:
    package = _package("literal-tool", name="A [literal] tool").replace(
        "What A [literal] tool provides.",
        "Show <tags> and *literal stars*.",
    )
    catalog = load_community_package_catalog(_write_catalog(tmp_path / "community_packages.yml", package))

    projected = community_package_list_markdown(catalog, "extension")

    assert "A \\[literal\\] tool" in projected
    assert "&lt;tags&gt;" in projected
    assert r"\*literal stars\*" in projected


def test_empty_category_renders_an_honest_empty_state(tmp_path: Path) -> None:
    catalog = load_community_package_catalog(_write_catalog(tmp_path / "community_packages.yml", ""))

    result = render_page(
        '<c-community-packages category="ui_library" />',
        community_package_catalog=catalog,
        wrap_in_layout=False,
    )

    assert "No packages are listed in this category yet." in result.html
    assert "No packages are listed under Community UI libraries yet." in result.markdown_body


def _build_config(tmp_path: Path) -> tuple[DocsConfig, Path, Path]:
    content = tmp_path / "content"
    content.mkdir()
    output = tmp_path / "site"
    redirects = tmp_path / "redirects.yml"
    redirects.write_text("redirects: []\n", encoding="utf-8")
    return (
        DocsConfig(
            content_dir=content,
            site_dir=output,
            repo_root=tmp_path,
            redirects_config=redirects,
        ),
        content,
        output,
    )


def test_root_build_renders_package_page_and_plain_markdown_companion(tmp_path: Path) -> None:
    config, content, output = _build_config(tmp_path)
    catalog_path = _write_catalog(
        tmp_path / "community_packages.yml",
        _package("example-extension", name="Example extension"),
    )
    config.community_packages_data = catalog_path
    page = content / "community" / "extensions.md"
    page.parent.mkdir()
    page.write_text(
        "---\ntitle: Extensions\ndescription: Extension directory.\n---\n\n"
        '# Extensions\n\n<c-community-packages category="extension" />\n',
        encoding="utf-8",
    )
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Community\n"
        "    scope: site\n"
        "    items: [{ title: Extensions, path: /community/extensions/ }]\n",
        encoding="utf-8",
    )

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 0
    html = (output / "community" / "extensions" / "index.html").read_text(encoding="utf-8")
    companion = (output / "community" / "extensions" / "index.md").read_text(encoding="utf-8")
    assert 'class="community-package-card"' in html
    assert "[Example extension](<https://pypi.org/project/example-extension/>)" in companion
    assert "docs-community-packages:start" not in companion


def test_invalid_root_catalog_preserves_the_previous_output(tmp_path: Path) -> None:
    config, content, output = _build_config(tmp_path)
    invalid_catalog = tmp_path / "invalid-community-packages.yml"
    invalid_catalog.write_text("not: the catalog\n", encoding="utf-8")
    config.community_packages_data = invalid_catalog
    page = content / "community" / "extensions.md"
    page.parent.mkdir()
    page.write_text('<c-community-packages category="extension" />\n', encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Community\n"
        "    scope: site\n"
        "    items: [{ title: Extensions, path: /community/extensions/ }]\n",
        encoding="utf-8",
    )
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("known good output", encoding="utf-8")

    with pytest.raises(CommunityPackageCatalogError, match="missing required key"):
        build_site(config=config, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "known good output"


def test_snapshot_omits_package_pages_without_loading_current_catalog(tmp_path: Path) -> None:
    config, content, output = _build_config(tmp_path)
    invalid_catalog = tmp_path / "invalid-community-packages.yml"
    invalid_catalog.write_text("not: the catalog\n", encoding="utf-8")
    config.community_packages_data = invalid_catalog
    (content / "index.md").write_text("# Versioned home\n", encoding="utf-8")
    package_page = content / "community" / "extensions.md"
    package_page.parent.mkdir()
    package_page.write_text("<c-this-must-not-render />\n", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    scope: versioned\n"
        "    items: [{ title: Home, path: / }]\n"
        "  - label: Community\n"
        "    scope: site\n"
        "    items: [{ title: Extensions, path: /community/extensions/ }]\n",
        encoding="utf-8",
    )

    outcome = build_site(
        config=config,
        output_dir=output,
        docs_version="1.0.0",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert outcome.failed == 0
    assert (output / "index.html").is_file()
    assert not (output / "community").exists()


def test_source_guard_reports_a_mismatched_page_directive(tmp_path: Path) -> None:
    content = tmp_path / "content"
    page = content / "community" / "extensions.md"
    page.parent.mkdir(parents=True)
    page.write_text('<c-community-packages category="ui_library" />\n', encoding="utf-8")
    _write_catalog(
        tmp_path / "data" / "community_packages.yml",
        _package("example-extension", name="Example extension"),
    )
    ctx = GuardContext(
        content_dir=content,
        examples_dir=tmp_path / "examples",
        nav_path=content / "_nav.yml",
        static_dir=tmp_path / "static",
        repo_root=tmp_path,
    )

    results = list(community_packages_guard.check(ctx))

    assert len(results) == 1
    assert results[0].source == "community/extensions.md"
    assert "category 'extension'" in results[0].message


def test_source_guard_ignores_a_directive_inside_fenced_code(tmp_path: Path) -> None:
    content = tmp_path / "content"
    page = content / "community" / "extensions.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        '```html\n<c-community-packages category="extension" />\n```\n',
        encoding="utf-8",
    )
    _write_catalog(
        tmp_path / "data" / "community_packages.yml",
        _package("example-extension", name="Example extension"),
    )
    ctx = GuardContext(
        content_dir=content,
        examples_dir=tmp_path / "examples",
        nav_path=content / "_nav.yml",
        static_dir=tmp_path / "static",
        repo_root=tmp_path,
    )

    results = list(community_packages_guard.check(ctx))

    assert len(results) == 1
    assert "exactly one" in results[0].message


def test_source_guard_requires_package_routes_to_remain_site_scoped(tmp_path: Path) -> None:
    content = tmp_path / "content"
    extension_page = content / "community" / "extensions.md"
    extension_page.parent.mkdir(parents=True)
    extension_page.write_text('<c-community-packages category="extension" />\n', encoding="utf-8")
    ui_page = content / "community" / "ui-libraries.md"
    ui_page.write_text('<c-community-packages category="ui_library" />\n', encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Community\n"
        "    scope: versioned\n"
        "    items:\n"
        "      - { title: Extensions, path: /community/extensions/ }\n"
        "      - { title: UI libraries, path: /community/ui-libraries/ }\n",
        encoding="utf-8",
    )
    _write_catalog(
        tmp_path / "data" / "community_packages.yml",
        _package("example-extension", name="Example extension"),
    )
    ctx = GuardContext(
        content_dir=content,
        examples_dir=tmp_path / "examples",
        nav_path=content / "_nav.yml",
        static_dir=tmp_path / "static",
        repo_root=tmp_path,
    )

    results = list(community_packages_guard.check(ctx))

    assert len(results) == 1
    assert "site-scoped" in results[0].message


def test_dev_server_reloads_package_data_for_each_directory_request(tmp_path: Path) -> None:
    config, content, _output = _build_config(tmp_path)
    catalog_path = _write_catalog(
        tmp_path / "community_packages.yml",
        _package("example-extension", name="Example extension"),
    )
    config.community_packages_data = catalog_path
    page = content / "community" / "extensions.md"
    page.parent.mkdir()
    page.write_text('<c-community-packages category="extension" />\n', encoding="utf-8")
    client = TestClient(create_app(config=config))

    first = client.get("/community/extensions/")
    catalog_path.write_text(
        catalog_path.read_text(encoding="utf-8").replace(
            "What Example extension provides.",
            "Updated package summary.",
        ),
        encoding="utf-8",
    )
    second = client.get("/community/extensions/")

    assert first.status_code == 200
    assert "What Example extension provides." in first.text
    assert second.status_code == 200
    assert "Updated package summary." in second.text
