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

import re
import shutil
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from docs_site._internal._vendor.mike_versions import Versions
from docs_site._internal.build import build_site
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.versioning import (
    load_manifest,
    select_indexed_versions,
    select_published_versions,
    write_manifest,
)

if TYPE_CHECKING:
    from pathlib import Path


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
    # Old-version HTML pages rewritten to noindex + a canonical to the current release.
    noindexed_pages: int = 0


def assemble_site(
    *, config: DocsConfig | None = None, output_dir: Path | None = None, build: bool = True
) -> AssembleOutcome:
    """Build the current version into the site root and mount the committed versions under ``/v/``."""
    config = config or default_config
    site_dir = (output_dir or config.site_dir).resolve()
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
    if (config.versions_dir / "versions.json").is_file():
        outcome.published = _publish_versions(config.versions_dir, dest_v, config.publish_window)

    if (dest_v / "versions.json").is_file():
        # Hide the old mounted versions from search (noindex + canonical to the
        # current release), then point the root pages' picker at the manifest.
        outcome.noindexed_pages = _noindex_old_versions(site_dir, dest_v, site_url=config.site_url)
        outcome.picker_pages = _enable_root_version_picker(site_dir, config.base_path)
    return outcome


def _publish_versions(versions_root: Path, dest_v: Path, window: int) -> list[str]:
    """Copy the published subset of committed versions into ``dest_v`` and write a trimmed manifest."""
    manifest = load_manifest(versions_root)
    published = select_published_versions(manifest, window)
    published_set = set(published)

    trimmed = Versions()
    for info in manifest:
        version = str(info.version)
        if version not in published_set:
            continue
        shutil.copytree(versions_root / version, dest_v / version, dirs_exist_ok=True)
        trimmed.add(version, title=info.title, aliases=list(info.aliases))
        # Copy each alias dir (e.g. latest/) whose target version is published.
        for alias in info.aliases:
            alias_dir = versions_root / alias
            if alias_dir.is_dir():
                shutil.copytree(alias_dir, dest_v / alias, dirs_exist_ok=True)
    write_manifest(dest_v, trimmed)
    return published


def _enable_root_version_picker(site_dir: Path, base: str) -> int:
    """Add ``data-versions-root`` to the root pages' picker so site.js fetches the manifest there."""
    needle = "data-version-picker"
    replacement = f'data-version-picker data-versions-root="{base}/v/"'
    v_dir = site_dir / "v"
    changed = 0
    for html in site_dir.rglob("*.html"):
        if v_dir in html.parents:
            continue  # /v/<version>/ pages derive the manifest path from their own URL
        text = html.read_text(encoding="utf-8")
        if needle in text and "data-versions-root" not in text:
            html.write_text(text.replace(needle, replacement), encoding="utf-8")
            changed += 1
    return changed


# A whole <meta ...> / <link ...> start tag, so an attribute can be rewritten
# without assuming any particular attribute order.
_META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.IGNORECASE)

# One attribute's value, matching a double-quoted, single-quoted, or bare value.
# Both forms occur because the minify pass drops quotes and reorders attributes
# (``name="robots" content="index,follow"`` -> ``content=index,follow name=robots``).
_ATTR_RE = {
    name: re.compile(rf'\b{name}=("[^"]*"|\'[^\']*\'|[^\s>]*)', re.IGNORECASE)
    for name in ("name", "rel", "content", "href")
}


def _attr_value(tag: str, name: str) -> str:
    """The (unquoted) value of the first ``name=...`` attribute in ``tag``, or "" if absent."""
    match = _ATTR_RE[name].search(tag)
    return match.group(1).strip("\"'") if match else ""


def _set_attr(tag: str, name: str, value: str) -> str:
    """Replace the first ``name=...`` attribute's value with ``name="value"`` (unchanged if absent)."""
    # A function replacement inserts the value verbatim, so a URL with backslashes
    # or ``\1``-looking text is not read as a regex replacement template.
    return _ATTR_RE[name].sub(lambda _match: f'{name}="{value}"', tag, count=1)


def _rewrite_meta_robots(html: str) -> str:
    """Force every ``<meta name="robots">`` in ``html`` to ``noindex,follow``."""

    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if _attr_value(tag, "name").lower() != "robots":
            return tag
        return _set_attr(tag, "content", "noindex,follow")

    return _META_TAG_RE.sub(repl, html)


def _rewrite_canonical(html: str, target: str) -> str:
    """Point every ``<link rel="canonical">`` in ``html`` at ``target``."""

    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if _attr_value(tag, "rel").lower() != "canonical":
            return tag
        return _set_attr(tag, "href", target)

    return _LINK_TAG_RE.sub(repl, html)


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
    kept = set(select_indexed_versions(manifest))
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
