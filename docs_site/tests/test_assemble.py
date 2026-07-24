"""Tests for the version-mode build and the multi-version deploy assembly."""

from __future__ import annotations

import json
from pathlib import Path

from docs_site._internal.assemble import _noindex_old_versions, assemble_site
from docs_site._internal.build import BuildOutcome, build_site
from docs_site._internal.config import DocsConfig
from docs_site._internal.versioning import BUILD_INFO_NAME, MANIFEST_NAME, update_manifest


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
    assert json.loads((versions / "1.0.0" / BUILD_INFO_NAME).read_text(encoding="utf-8"))["version"] == "1.0.0"
    assert [v["version"] for v in json.loads((versions / MANIFEST_NAME).read_text(encoding="utf-8"))] == ["1.0.0"]
    # The alias is materialized, and the snapshot canonicals to its own /v/ tree.
    assert outcome.alias_redirects > 0
    assert (versions / "latest" / "index.html").is_file()
    page = (versions / "1.0.0" / "concepts" / "components" / "index.html").read_text(encoding="utf-8")
    assert "/v/1.0.0/concepts/components/" in page
    # Site-wide crawl files belong to the root build, not the snapshot.
    assert not (versions / "1.0.0" / "sitemap.xml").exists()


def test_assemble_mounts_versions_and_enables_picker(tmp_path: Path) -> None:
    config = _config(tmp_path)
    build_site(config=config, docs_version="1.0.0", alias="latest", search=False, minify=False)

    outcome = assemble_site(config=config)

    site = config.site_dir
    assert outcome.published == ["1.0.0"]
    assert (site / "v" / "versions.json").is_file()
    assert (site / "v" / "1.0.0" / "index.html").is_file()
    assert (site / "v" / "latest" / "index.html").is_file()
    # The current build is at the root (with its sitemap), and its picker now
    # points at the manifest; the /v/ pages derive that path themselves.
    assert (site / "sitemap.xml").is_file()
    assert outcome.picker_pages > 0
    assert 'data-versions-root="/v/"' in (site / "index.html").read_text(encoding="utf-8")
    assert "data-versions-root" not in (site / "v" / "1.0.0" / "index.html").read_text(encoding="utf-8")


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
        '<meta content="noindex,follow" name=robots><link href="https://x.test/concepts/slots/" rel=canonical>'
    )
    # No current counterpart: canonical to the root home, still noindex.
    assert (dest_v / "1.0.0" / "gone" / "index.html").read_text(encoding="utf-8") == (
        '<meta name="robots" content="noindex,follow"/><link rel="canonical" href="https://x.test/"/>'
    )
    # The version home page canonicals to the site home.
    assert 'href="https://x.test/"' in (dest_v / "1.1.0" / "index.html").read_text(encoding="utf-8")
    # The kept version is untouched.
    assert kept_page.read_text(encoding="utf-8") == kept_original
