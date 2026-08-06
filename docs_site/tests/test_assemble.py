"""Tests for the version-mode build and the multi-version deploy assembly."""

from __future__ import annotations

import json
from pathlib import Path

from docs_site._internal._vendor.mike_versions import Versions
from docs_site._internal.assemble import (
    _enable_root_version_picker,
    _noindex_old_versions,
    _rewrite_canonical,
    _rewrite_meta_robots,
    _rewrite_mounted_pagefind_path,
    assemble_site,
)
from docs_site._internal.build import BuildOutcome, build_site
from docs_site._internal.config import DocsConfig
from docs_site._internal.versioning import (
    BUILD_INFO_NAME,
    MANIFEST_NAME,
    materialize_alias,
    update_manifest,
    write_manifest,
)


def _config(tmp_path: Path) -> DocsConfig:
    # Keeps the real content_dir; only the output trees are redirected to tmp.
    return DocsConfig(site_dir=tmp_path / "site", versions_dir=tmp_path / "versions")


def test_version_mode_writes_a_committed_snapshot(tmp_path: Path) -> None:
    config = _config(tmp_path)

    outcome = build_site(config=config, docs_version="1.0.0", alias="latest", search=False, minify=False)

    versions = config.versions_dir
    assert outcome.docs_version == "1.0.0"
    assert (versions / "1.0.0" / "index.html").is_file()
    # Stamped and recorded in the manifest.
    build_info = json.loads((versions / "1.0.0" / BUILD_INFO_NAME).read_text(encoding="utf-8"))
    assert build_info["version"] == "1.0.0"
    assert "/blog/*" in build_info["site_routes"]
    assert "/community/*" in build_info["site_routes"]
    assert [v["version"] for v in json.loads((versions / MANIFEST_NAME).read_text(encoding="utf-8"))] == ["1.0.0"]
    # The alias is materialized, and the snapshot canonicals to its own /v/ tree.
    assert outcome.alias_redirects > 0
    assert (versions / "latest" / "index.html").is_file()
    page = (versions / "1.0.0" / "concepts" / "components" / "index.html").read_text(encoding="utf-8")
    assert "/v/1.0.0/concepts/components/" in page
    assert 'href="/v/1.0.0/getting-started/installation/"' in page
    assert 'href="/community/people/"' in page
    assert 'href="/blog/"' in page
    assert not (versions / "1.0.0" / "community").exists()
    assert not (versions / "1.0.0" / "blog").exists()
    # Site-wide crawl files belong to the root build, not the snapshot.
    assert not (versions / "1.0.0" / "sitemap.xml").exists()


def test_assemble_mounts_versions_and_enables_picker(tmp_path: Path) -> None:
    config = _config(tmp_path)
    build_site(config=config, docs_version="1.0.0", alias="latest", search=False, minify=False)
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        config.settings_config.read_text(encoding="utf-8").replace(
            "/pagefind/pagefind.js",
            "/custom-search/pagefind.js",
            1,
        ),
        encoding="utf-8",
    )
    config.settings_config = settings_path
    config.base_path = "/preview"

    outcome = assemble_site(config=config)

    site = config.site_dir
    assert outcome.published == ["1.0.0"]
    assert (site / "v" / "versions.json").is_file()
    assert (site / "v" / "1.0.0" / "index.html").is_file()
    assert (site / "v" / "latest" / "index.html").is_file()
    # The current build is at the root (with its sitemap), and its picker now
    # points at the manifest; the /v/ pages derive that path themselves.
    assert (site / "sitemap.xml").is_file()
    assert (site / "custom-search" / "pagefind.js").is_file()
    assert outcome.picker_pages > 0
    assert outcome.pagefind_pages > 0
    assert outcome.mounted_base_path_pages > 0
    assert 'data-versions-root="/preview/v/"' in (site / "docs" / "index.html").read_text(encoding="utf-8")
    # The project home is the landing page, which carries no docs chrome and so
    # has no picker to point anywhere. Versions are switched from the docs.
    assert "data-version-picker" not in (site / "index.html").read_text(encoding="utf-8")
    assert "data-version-picker" not in (site / "blog" / "index.html").read_text(encoding="utf-8")
    assert "data-versions-root" not in (site / "community" / "people" / "index.html").read_text(encoding="utf-8")
    mounted = (site / "v" / "1.0.0" / "docs" / "index.html").read_text(encoding="utf-8")
    assert "data-versions-root" not in mounted
    assert 'data-pagefind-path="/preview/custom-search/pagefind.js"' in mounted
    assert 'href="/preview/v/1.0.0/' in mounted


def test_assemble_without_build_replaces_stale_version_mounts(tmp_path: Path) -> None:
    config = _config(tmp_path)
    site = config.site_dir
    versions = config.versions_dir
    site.mkdir(parents=True)
    (site / "index.html").write_text("current", encoding="utf-8")
    for version in ("1.0.0", "2.0.0"):
        snapshot = versions / version
        snapshot.mkdir(parents=True)
        (snapshot / "index.html").write_text(version, encoding="utf-8")
        update_manifest(versions, version, aliases=("latest",) if version == "2.0.0" else ())
    materialize_alias(versions, "latest", "2.0.0")

    first = assemble_site(config=config, build=False)

    assert first.published == ["2.0.0", "1.0.0"]
    assert {path.name for path in (site / "v").iterdir()} == {
        "1.0.0",
        "2.0.0",
        "latest",
        "versions.json",
    }

    trimmed = Versions()
    trimmed.add("2.0.0")
    write_manifest(versions, trimmed)
    second = assemble_site(config=config, build=False)

    assert second.published == ["2.0.0"]
    assert {path.name for path in (site / "v").iterdir()} == {"2.0.0", "versions.json"}

    (versions / MANIFEST_NAME).unlink()
    third = assemble_site(config=config, build=False)

    assert third.published == []
    assert list((site / "v").iterdir()) == []


def test_assemble_rejects_partial_current_build(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)

    def partial_build(**_kwargs) -> BuildOutcome:
        return BuildOutcome(
            output_dir=config.site_dir,
            failed=1,
            errors=[("broken.md", "RuntimeError: broken")],
            search_ok=True,
        )

    monkeypatch.setattr("docs_site._internal.assemble.build_site", partial_build)

    outcome = assemble_site(config=config)

    assert outcome.failed == 1
    assert outcome.errors == [("broken.md", "RuntimeError: broken")]
    assert not (config.site_dir / "v").exists()


def test_assemble_rejects_missing_search_index(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path)

    def build_without_search(**_kwargs) -> BuildOutcome:
        return BuildOutcome(
            output_dir=config.site_dir,
            search_ok=False,
            search_message="pagefind failed",
        )

    monkeypatch.setattr("docs_site._internal.assemble.build_site", build_without_search)

    outcome = assemble_site(config=config)

    assert outcome.failed == 0
    assert outcome.search_ok is False
    assert outcome.search_message == "pagefind failed"
    assert not (config.site_dir / "v").exists()


def test_mounted_pagefind_rewrite_accepts_minified_and_quoted_attributes(tmp_path: Path) -> None:
    quoted = tmp_path / "1.0.0" / "index.html"
    minified = tmp_path / "1.0.0" / "guide" / "index.html"
    untouched = tmp_path / "latest" / "index.html"
    for path, source in (
        (
            quoted,
            '<div class="djc-search__overlay" data-pagefind-path="/pagefind/pagefind.js"></div>',
        ),
        (
            minified,
            "<div data-pagefind-path=/pagefind/pagefind.js class=djc-search__overlay></div>",
        ),
        (
            untouched,
            '<code>data-pagefind-path="/documented/pagefind.js"</code>'
            '<div data-pagefind-path="/unrelated/pagefind.js"></div>'
            '<script>const sample = \'<div class="djc-search__overlay" '
            'data-pagefind-path="/script/pagefind.js">\';</script>',
        ),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    assert _rewrite_mounted_pagefind_path(tmp_path, "/preview/custom-search/pagefind.js") == 2
    assert 'data-pagefind-path="/preview/custom-search/pagefind.js"' in quoted.read_text(encoding="utf-8")
    assert "data-pagefind-path=/preview/custom-search/pagefind.js" in minified.read_text(encoding="utf-8")
    untouched_source = untouched.read_text(encoding="utf-8")
    assert "/documented/pagefind.js" in untouched_source
    assert "/unrelated/pagefind.js" in untouched_source
    assert "/script/pagefind.js" in untouched_source


def test_noindex_rewrites_only_real_meta_and_link_tags() -> None:
    source = (
        '<meta name="robots" content="index,follow"><link rel="canonical" href="https://old.test/">'
        '<code>content="index,follow" href="https://documented.test/"</code>'
        '<script>const tags = \'<meta name="robots" content="script">'
        '<link rel="canonical" href="https://script.test/">\';</script>'
    )

    rewritten = _rewrite_canonical(_rewrite_meta_robots(source), "https://new.test/")

    assert '<meta name="robots" content="noindex,follow">' in rewritten
    assert '<link rel="canonical" href="https://new.test/">' in rewritten
    assert 'content="index,follow" href="https://documented.test/"' in rewritten
    assert 'content="script"' in rewritten
    assert 'href="https://script.test/"' in rewritten


def test_version_picker_rewrite_only_touches_picker_elements(tmp_path: Path) -> None:
    page = tmp_path / "docs" / "index.html"
    version_page = tmp_path / "v" / "1.0.0" / "index.html"
    source = (
        "<div data-version-picker></div>"
        "<code>data-version-picker</code>"
        "<script>const token = 'data-version-picker';</script>"
    )
    for path in (page, version_page):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    assert _enable_root_version_picker(tmp_path, "/preview") == 1
    rewritten = page.read_text(encoding="utf-8")
    assert 'data-versions-root="/preview/v/"' in rewritten
    assert "<code>data-version-picker</code>" in rewritten
    assert "const token = 'data-version-picker'" in rewritten
    assert version_page.read_text(encoding="utf-8") == source


def _snapshot_page(page: Path, canonical: str, *, mini: bool) -> None:
    """Write a minimal built page (robots meta + self-canonical), minified or not."""
    page.parent.mkdir(parents=True, exist_ok=True)
    if mini:
        # The shape the minify pass leaves: bare values, attributes reordered.
        text = f"<meta content=index,follow name=robots><link href={canonical} rel=canonical>"
    else:
        text = f'<meta name="robots" content="index,follow"/><link rel="canonical" href="{canonical}"/>'
    page.write_text(text, encoding="utf-8")


def test_noindex_old_versions_rewrites_old_and_leaves_kept(tmp_path: Path) -> None:
    site = tmp_path / "site"
    dest_v = site / "v"
    # Four mounted versions, latest on the newest: kept {1.3.0, 1.2.0}, old {1.1.0, 1.0.0}.
    update_manifest(dest_v, "1.0.0")
    update_manifest(dest_v, "1.1.0")
    update_manifest(dest_v, "1.2.0")
    update_manifest(dest_v, "1.3.0", aliases=("latest",))

    # Current (root) pages that some old pages have a counterpart for.
    (site / "concepts" / "slots").mkdir(parents=True)
    (site / "concepts" / "slots" / "index.html").write_text("<h1>current slots</h1>", encoding="utf-8")
    (site / "index.html").write_text("<h1>home</h1>", encoding="utf-8")

    # 1.0.0 in the un-minified markup, 1.1.0 in the minified markup, so both forms
    # are exercised. Each version has a page with a root counterpart, a page with
    # none, and its home page.
    for version, mini in (("1.0.0", False), ("1.1.0", True)):
        for sub, url in (("concepts/slots", "concepts/slots/"), ("gone", "gone/"), ("", "")):
            page = dest_v / version / sub / "index.html" if sub else dest_v / version / "index.html"
            _snapshot_page(page, f"https://x.test/v/{version}/{url}", mini=mini)
    # A kept version whose page must stay byte-for-byte as built.
    kept_page = dest_v / "1.2.0" / "concepts" / "slots" / "index.html"
    _snapshot_page(kept_page, "https://x.test/v/1.2.0/concepts/slots/", mini=False)
    kept_original = kept_page.read_text(encoding="utf-8")

    changed = _noindex_old_versions(site, dest_v, site_url="https://x.test/")

    assert changed == 6  # 2 old versions x 3 pages each
    # Old page with a current counterpart: noindex + canonical to the root page.
    assert (dest_v / "1.0.0" / "concepts" / "slots" / "index.html").read_text(encoding="utf-8") == (
        '<meta name="robots" content="noindex,follow"/><link rel="canonical" href="https://x.test/concepts/slots/"/>'
    )
    # The same page in minified markup: attribute order/quoting kept, values swapped.
    assert (dest_v / "1.1.0" / "concepts" / "slots" / "index.html").read_text(encoding="utf-8") == (
        "<meta content=noindex,follow name=robots><link href=https://x.test/concepts/slots/ rel=canonical>"
    )
    # No current counterpart: canonical to the root home, still noindex.
    assert (dest_v / "1.0.0" / "gone" / "index.html").read_text(encoding="utf-8") == (
        '<meta name="robots" content="noindex,follow"/><link rel="canonical" href="https://x.test/"/>'
    )
    # The version home page canonicals to the site home.
    assert "href=https://x.test/" in (dest_v / "1.1.0" / "index.html").read_text(encoding="utf-8")
    # The kept version is untouched.
    assert kept_page.read_text(encoding="utf-8") == kept_original
