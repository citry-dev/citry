"""
Assemble the full multi-version deploy artifact.

The everyday build writes only the current version. A deploy also mounts every
committed snapshot alongside it. This assembles the tree the host serves:

    site/
        index.html, concepts/, static/, sitemap.xml, ...   <- current version
        v/
            versions.json                                  <- the manifest
            <version>/ ...                                 <- each committed version
            latest/ ...                                    <- the latest alias redirects

It builds the current version into the site root, copies the published subset of
``versions/*`` into ``site/v/`` with a trimmed manifest, and marks the root
pages' version picker so its script fetches that manifest (the root pages have no
``/v/`` segment to derive it from, so they need the hint; ``/v/<version>/`` pages
derive it from their own URL and are left alone).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from docs_site._internal._vendor.mike_versions import Versions
from docs_site._internal.base_path import apply_base_path
from docs_site._internal.build import _is_unsafe_output, _replace_output_directory, build_site
from docs_site._internal.html_rewrite import (
    StartTag,
    append_attribute,
    parse_start_tags,
    rewrite_attribute_values,
    rewrite_start_tags,
)
from docs_site._internal.project import DocsProject, current_docs_project, docs_project_scope
from docs_site._internal.versioning import (
    load_manifest,
    select_indexed_versions,
    select_published_versions,
    write_manifest,
)

if TYPE_CHECKING:
    from docs_site._internal.config import DocsConfig


@dataclass
class AssembleOutcome:
    """Where the artifact was assembled, which versions it mounted, pickers wired, old pages hidden."""

    output_dir: Path
    # A current-version render failure or search-index failure makes the
    # artifact undeployable. The CLI reports these and exits nonzero.
    failed: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)
    search_ok: bool | None = None
    search_message: str = ""
    published: list[str] = field(default_factory=list)
    picker_pages: int = 0
    # Mounted snapshot pages pointed at the root build's configured Pagefind bundle.
    pagefind_pages: int = 0
    # Mounted snapshot pages rewritten for a project-Pages deployment prefix.
    mounted_base_path_pages: int = 0
    # Mounted snapshot pages whose legacy URL-less breadcrumb items were removed.
    breadcrumb_pages: int = 0
    # Old-version HTML pages rewritten to noindex + a canonical to the current release.
    noindexed_pages: int = 0


@docs_project_scope
def assemble_site(
    *,
    config: DocsConfig | None = None,
    output_dir: Path | None = None,
    build: bool = True,
    project: DocsProject | None = None,
) -> AssembleOutcome:
    """Build the current version into the site root and mount the committed versions under ``/v/``."""
    if project is None:  # pragma: no cover - supplied by @docs_project_scope
        raise RuntimeError("docs project scope was not initialized")
    requested_site_dir = output_dir or config.site_dir
    if requested_site_dir.is_symlink():
        raise ValueError(f"Refusing to use symlink assembly output dir: {requested_site_dir}")
    site_dir = requested_site_dir.resolve()
    if _is_unsafe_output(site_dir, config.content_dir, config):
        raise ValueError(f"Refusing to use unsafe assembly output dir: {site_dir}")
    outcome = AssembleOutcome(output_dir=site_dir)

    if build:
        # The current version is the root of the deploy artifact. Do not mount
        # versions onto it when any page or the shipped search index failed:
        # callers must be able to reject a partial artifact before upload.
        build_outcome = build_site(config=config, output_dir=site_dir)
        outcome.failed = build_outcome.failed
        outcome.errors = list(build_outcome.errors)
        outcome.search_ok = build_outcome.search_ok
        outcome.search_message = build_outcome.search_message
        if outcome.failed or not outcome.search_ok:
            return outcome

    dest_v = site_dir / "v"
    outcome.published = _publish_versions(config.versions_dir, dest_v, project.versions.publish_window)

    if (dest_v / "versions.json").is_file():
        # Hide the old mounted versions from search (noindex + canonical to the
        # current release), point their search UI at the root build's configured
        # index, then point the root pages' picker at the manifest.
        if config.base_path:
            outcome.mounted_base_path_pages = apply_base_path(dest_v, config.base_path)
        outcome.breadcrumb_pages = _rewrite_mounted_breadcrumbs(dest_v)
        outcome.noindexed_pages = _noindex_old_versions(site_dir, dest_v, site_url=project.site_url)
        outcome.pagefind_pages = _rewrite_mounted_pagefind_path(
            dest_v,
            f"{config.base_path}{project.settings.pagefind_path}",
        )
        outcome.picker_pages = _enable_root_version_picker(site_dir, config.base_path)
    return outcome


def _publish_versions(versions_root: Path, dest_v: Path, window: int) -> list[str]:
    """Replace ``dest_v`` with the exact published subset and its trimmed manifest."""
    has_manifest = (versions_root / "versions.json").is_file()
    manifest = load_manifest(versions_root) if has_manifest else Versions()
    published = select_published_versions(manifest, window)
    published_set = set(published)

    dest_v.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".v.publish-", dir=dest_v.parent) as temporary:
        staged_v = Path(temporary)
        trimmed = Versions()
        for info in manifest:
            version = str(info.version)
            if version not in published_set:
                continue
            shutil.copytree(versions_root / version, staged_v / version)
            trimmed.add(version, title=info.title, aliases=list(info.aliases))
            # Copy each alias dir (e.g. latest/) whose target version is published.
            for alias in info.aliases:
                alias_dir = versions_root / alias
                if alias_dir.is_dir():
                    shutil.copytree(alias_dir, staged_v / alias)
        if has_manifest:
            write_manifest(staged_v, trimmed)
        _replace_output_directory(staged_v, dest_v)
    return published


def _enable_root_version_picker(site_dir: Path, base: str) -> int:
    """
    Add ``data-versions-root`` to the root pages' picker so site.js fetches the manifest there.

    A page without a picker is skipped rather than treated as a problem: the
    project home uses the landing layout, which carries no docs chrome, so
    versions are switched from the documentation pages instead.
    """

    def add_versions_root(tag: StartTag) -> str:
        attrs = dict(tag.attrs)
        if "data-version-picker" not in attrs or "data-versions-root" in attrs:
            return tag.source
        return append_attribute(tag.source, f'data-versions-root="{base}/v/"')

    v_dir = site_dir / "v"
    changed = 0
    for html in site_dir.rglob("*.html"):
        if v_dir in html.parents:
            continue  # /v/<version>/ pages derive the manifest path from their own URL
        text = html.read_text(encoding="utf-8")
        rewritten = rewrite_start_tags(text, add_versions_root)
        if rewritten == text:
            continue
        html.write_text(rewritten, encoding="utf-8")
        changed += 1
    return changed


def _rewrite_mounted_pagefind_path(root: Path, pagefind_path: str) -> int:
    """Point copied snapshots at the Pagefind bundle emitted by the root build."""

    def rewrite_overlay(tag: StartTag) -> str:
        attrs = dict(tag.attrs)
        classes = (attrs.get("class") or "").split()
        if tag.name != "div" or "djc-search__overlay" not in classes or "data-pagefind-path" not in attrs:
            return tag.source
        return rewrite_attribute_values(
            tag.source,
            lambda name, value: pagefind_path if name == "data-pagefind-path" else value,
        )

    changed = 0
    for html_path in root.rglob("*.html"):
        source = html_path.read_text(encoding="utf-8")
        rewritten = rewrite_start_tags(source, rewrite_overlay)
        if rewritten == source:
            continue
        html_path.write_text(rewritten, encoding="utf-8")
        changed += 1
    return changed


def _rewrite_mounted_breadcrumbs(root: Path) -> int:
    """Remove URL-less ListItems from copied snapshots' BreadcrumbList data."""
    changed = 0
    for html_path in root.rglob("*.html"):
        source = html_path.read_text(encoding="utf-8")
        rewritten = _rewrite_breadcrumb_jsonld(source)
        if rewritten == source:
            continue
        html_path.write_text(rewritten, encoding="utf-8")
        changed += 1
    return changed


def _rewrite_breadcrumb_jsonld(html: str) -> str:
    """Remove non-page crumbs while preserving every other part of the HTML."""
    rewritten = html
    folded = html.casefold()
    for tag in reversed(parse_start_tags(html)):
        attrs = dict(tag.attrs)
        if tag.name != "script" or (attrs.get("type") or "").casefold() != "application/ld+json":
            continue
        close_start = folded.find("</script", tag.end)
        if close_start < 0:
            continue
        block = html[tag.end : close_start]
        try:
            data = json.loads(block)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("@type") != "BreadcrumbList":
            continue
        items = data.get("itemListElement")
        if not isinstance(items, list):
            continue
        last = len(items) - 1
        linked = [
            item for index, item in enumerate(items) if isinstance(item, dict) and (item.get("item") or index == last)
        ]
        if len(linked) == len(items) and len(linked) >= 2:
            continue
        if len(linked) < 2:
            close_end = folded.find(">", close_start)
            if close_end >= 0:
                rewritten = rewritten[: tag.start] + rewritten[close_end + 1 :]
            continue
        for position, item in enumerate(linked, start=1):
            item["position"] = position
        data["itemListElement"] = linked
        leading = block[: len(block) - len(block.lstrip())]
        trailing = block[len(block.rstrip()) :]
        replacement = f"{leading}{json.dumps(data, ensure_ascii=True)}{trailing}"
        rewritten = rewritten[: tag.end] + replacement + rewritten[close_start:]
    return rewritten


def _rewrite_meta_robots(html: str) -> str:
    """Force every ``<meta name="robots">`` in ``html`` to ``noindex,follow``."""

    def rewrite_meta(tag: StartTag) -> str:
        attrs = dict(tag.attrs)
        if tag.name != "meta" or (attrs.get("name") or "").casefold() != "robots":
            return tag.source
        return rewrite_attribute_values(
            tag.source,
            lambda name, value: "noindex,follow" if name == "content" else value,
        )

    return rewrite_start_tags(html, rewrite_meta)


def _rewrite_canonical(html: str, target: str) -> str:
    """Point every ``<link rel="canonical">`` in ``html`` at ``target``."""

    def rewrite_link(tag: StartTag) -> str:
        attrs = dict(tag.attrs)
        if tag.name != "link" or (attrs.get("rel") or "").casefold() != "canonical":
            return tag.source
        return rewrite_attribute_values(
            tag.source,
            lambda name, value: target if name == "href" else value,
        )

    return rewrite_start_tags(html, rewrite_link)


def _clean_url(rel: Path) -> str:
    """
    The clean URL path of a built page file, mirroring the URLs the build assigns.

    A page lives at ``<clean-path>/index.html`` and its clean URL is that directory
    (empty for the home page). Any other ``.html`` keeps its own name.
    """
    if rel.name == "index.html":
        parent = rel.parent.as_posix()  # "." for a top-level index.html
        return "" if parent == "." else f"{parent}/"
    return rel.as_posix()


def _noindex_old_versions(site_dir: Path, dest_v: Path, *, site_url: str) -> int:
    """
    Rewrite each old mounted version's pages to noindex + a canonical to the
    current release, and return the number of HTML files changed.

    Net-new in citry: django-components deferred this (its feature 6.12b), so it is
    built here as an assemble-time pass rather than ported. "Old" is every mounted
    version outside the kept-indexed set (the newest few plus the ``latest`` alias),
    read from the mounted ``/v/versions.json`` so only versions actually present are
    touched. Citry serves the current version at the site root, so a page at
    ``/v/<old>/concepts/slots/`` canonicals to ``<site>/concepts/slots/``; when no
    such current page exists it canonicals to the root home and still gets noindex,
    so an old-only page is never left indexable.
    """
    base = site_url.rstrip("/")
    manifest = load_manifest(dest_v)
    kept = set(
        select_indexed_versions(
            manifest,
            keep_recent=current_docs_project().versions.index_keep_recent,
        )
    )
    old_versions = [str(info.version) for info in manifest if str(info.version) not in kept]

    changed = 0
    for version in old_versions:
        version_dir = dest_v / version
        for html in sorted(version_dir.rglob("*.html")):
            rel = html.relative_to(version_dir)
            # The current-version page that supersedes this old one, if it exists.
            has_current_page = (site_dir / rel).is_file()
            canonical = f"{base}/{_clean_url(rel)}" if has_current_page else f"{base}/"
            text = html.read_text(encoding="utf-8")
            rewritten = _rewrite_canonical(_rewrite_meta_robots(text), canonical)
            if rewritten != text:
                html.write_text(rewritten, encoding="utf-8")
                changed += 1
    return changed
