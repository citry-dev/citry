"""
Build the static site: render every markdown page to HTML on disk.

Walks the content directory, renders each ``*.md`` through the pipeline, and
writes the result to ``<output>/<slug>/index.html`` (clean URLs). Non-markdown
files (images, etc.) are copied across verbatim so relative references keep
working.

A content page that fails to render is recorded on the outcome rather than
aborting the whole build, so one broken page does not hide the others. The
generated Reference pages and the 404 page are not guarded that way: a failure
there is a bug in this builder, not bad page content, so it stops the build
loudly. Authored non-Python Reference pages follow the content path.

After the pages are written the build runs its finishing steps in a fixed
order: generated API Reference pages and example demos, the ``objects.inv``
index, the custom 404 page, Citry's client runtime (so component JavaScript
works from flat files), and finally an HTML-shrinking pass. Each page that the
layout produces is also recorded in ``BuildOutcome.records`` so later steps
(sitemap, robots, llms files) can be built from that list without re-reading
the output.
"""

from __future__ import annotations

import shutil
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from pathlib import Path
from typing import TYPE_CHECKING
from unicodedata import normalize

from citry import citry as default_citry
from docs_site._internal.base_path import apply_base_path
from docs_site._internal.blog import (
    BlogCatalog,
    BlogPost,
    blog_source_routes,
    load_blog_catalog,
    serialize_atom_feed,
)
from docs_site._internal.config import DocsConfig
from docs_site._internal.config_loading import DocsConfigError
from docs_site._internal.crossrefs import build_objects_inv
from docs_site._internal.examples import get_example_registry
from docs_site._internal.llms import generate_llms_files
from docs_site._internal.minify import minify_site
from docs_site._internal.nav import SCOPE_SITE, load_nav
from docs_site._internal.pagefind import run_pagefind
from docs_site._internal.paths import (
    clean_url_to_companion_path,
    clean_url_to_html_path,
    md_companion_path,
    md_to_html_path,
    md_to_url,
)
from docs_site._internal.pipeline import RenderResult, render_page
from docs_site._internal.project import DocsProject, current_docs_project, docs_project_scope
from docs_site._internal.redirects import emit_redirects, validate_redirect_routes
from docs_site._internal.reference_pages import (
    reference_index_markdown,
    reference_page_markdown,
    validate_authored_reference_sources,
)
from docs_site._internal.release_notes import (
    parse_changelog,
    release_index_markdown,
    release_page_markdown,
)
from docs_site._internal.seo import generate_seo_files
from docs_site._internal.site_nav import load_site_nav
from docs_site._internal.social_cards import generate_social_cards
from docs_site._internal.static_deps import CITRY_MOUNT_PREFIX, export_fragment_deps, export_runtime
from docs_site._internal.ui_library_projection import (
    UiLibraryCatalog,
    ui_library_source_path,
    ui_library_source_routes,
    validate_ui_library_sources,
)
from docs_site._internal.ui_library_reference import compose_ui_library_source
from docs_site._internal.ui_previews import (
    UiPreview,
    discover_ui_previews,
    render_ui_preview_document,
)
from docs_site._internal.versioning import (
    git_head_sha,
    materialize_alias,
    update_manifest,
    validate_alias_target,
    validate_tree_identifier,
    validate_version_target,
    write_build_info,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from docs_site._internal.frontmatter import PageMeta
    from docs_site._internal.nav import NavTree


@dataclass
class PageRecord:
    """One layout-wrapped page, captured so later steps can index the site."""

    url: str  # clean URL, e.g. "concepts/components/" ("" for the home page)
    canonical: str  # resolved canonical URL (may be empty when no site URL is set)
    title: str
    description: str
    noindex: bool
    # True for pages the DocPage layout produced (content + reference). Example
    # demo pages are standalone and are not recorded here.
    is_doc_page: bool
    # The authored markdown source, which may live outside content_dir, or None
    # for a generated page.
    source_md: Path | None
    # The page body as expanded markdown, for the llms full-text export.
    markdown_body: str
    # Authored editorial timestamp for dated content. Sitemap generation uses
    # this instead of git history when present.
    editorial_updated: datetime | None = None


@dataclass
class BuildOutcome:
    """Result of a build: where it wrote, how many pages, and any failures."""

    output_dir: Path
    built: int = 0
    failed: int = 0
    # Per-page `.md` companion files written beside content pages (the raw
    # expanded markdown, for LLMs and tools that want the source not the HTML).
    companions: int = 0
    # Private rendered documents referenced by Citry UI component pages.
    ui_previews: int = 0
    examples: int = 0
    reference: int = 0
    releases: int = 0
    blog_posts: int = 0
    ui_library: int = 0
    blog_feed: bool = False
    elapsed: float = 0.0
    # (authored source label, error message) for pages that raised.
    errors: list[tuple[str, str]] = field(default_factory=list)
    # Every layout-wrapped page, for sitemap / robots / llms generation.
    records: list[PageRecord] = field(default_factory=list)
    not_found: bool = False  # whether the 404 page was written
    runtime: Path | None = None  # where the client runtime was written, if any
    minified: int = 0  # number of HTML files the minify pass shrank
    sitemap_urls: int = 0  # URLs listed in sitemap.xml
    redirects: int = 0  # redirect stubs written
    llms_links: int = 0  # link entries in llms.txt
    llms_pages: int = 0  # pages concatenated into llms-full.txt
    search_ok: bool = False  # whether the search index built
    search_message: str = ""  # the search-index result message
    base_path_files: int = 0  # HTML files rewritten for a subpath deploy
    social_cards_placed: int = 0  # per-page social cards generated and placed
    social_cards_skipped: str = ""  # why card generation was skipped, if it was
    docs_version: str = ""  # the version this snapshot was built as (version mode)
    alias_redirects: int = 0  # redirect stubs written for a materialized alias


@docs_project_scope
def build_site(
    *,
    config: DocsConfig | None = None,
    output_dir: Path | None = None,
    minify: bool = True,
    search: bool = True,
    social_cards: bool = True,
    docs_version: str = "",
    alias: str = "",
    update_versions_manifest: bool = True,
    project: DocsProject | None = None,
) -> BuildOutcome:
    """Build the root site directly, or publish a version snapshot after staging it."""
    if project is None:  # pragma: no cover - supplied by @docs_project_scope
        raise RuntimeError("docs project scope was not initialized")
    if not docs_version:
        return _build_site_to_output(
            config=config,
            output_dir=output_dir,
            minify=minify,
            search=search,
            social_cards=social_cards,
            docs_version=docs_version,
            alias=alias,
            update_versions_manifest=update_versions_manifest,
            project=project,
        )

    if not update_versions_manifest and alias:
        raise DocsConfigError("a detached docs-version build cannot materialize an alias")
    validate_version_target(config.versions_dir, docs_version)
    if alias:
        validate_tree_identifier(alias, "alias")
        validate_alias_target(config.versions_dir, alias, docs_version)

    canonical_version_dir = (config.versions_dir / docs_version).resolve()
    requested_target = output_dir or (config.versions_dir / docs_version)
    if requested_target.is_symlink():
        raise ValueError(f"Refusing to replace symlink output dir: {requested_target}")
    target_dir = requested_target.resolve()
    if target_dir != canonical_version_dir and (update_versions_manifest or alias):
        raise DocsConfigError("a custom docs-version output requires update_versions_manifest=False and no alias")
    if _is_unsafe_output(target_dir, config.content_dir, config, docs_version=docs_version):
        raise ValueError(f"Refusing to clear unsafe output dir: {target_dir}")

    # A failed page render is a normal BuildOutcome, not an exception. Build the
    # complete candidate away from the published tree so either kind of failure
    # leaves the last known-good snapshot, manifest, and alias untouched.
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{target_dir.name}.build-", dir=target_dir.parent) as temporary:
        staged_dir = Path(temporary)
        outcome = _build_site_to_output(
            config=config,
            output_dir=staged_dir,
            minify=minify,
            search=search,
            social_cards=social_cards,
            docs_version=docs_version,
            alias="",
            update_versions_manifest=False,
            project=project,
            staging_output=True,
        )
        outcome.output_dir = target_dir
        if outcome.failed:
            return outcome
        _replace_output_directory(staged_dir, target_dir)

    if update_versions_manifest:
        update_manifest(config.versions_dir, docs_version, aliases=(alias,) if alias else ())
    if alias:
        outcome.alias_redirects = materialize_alias(config.versions_dir, alias, docs_version)
    return outcome


def _build_site_to_output(
    *,
    config: DocsConfig,
    output_dir: Path | None = None,
    minify: bool = True,
    search: bool = True,
    social_cards: bool = True,
    docs_version: str = "",
    alias: str = "",
    update_versions_manifest: bool = True,
    project: DocsProject,
    staging_output: bool = False,
) -> BuildOutcome:
    """
    Build every page in ``config.content_dir`` into ``output_dir``.

    ``output_dir`` defaults to ``config.site_dir``. The target is cleared first,
    so it must not be the repo root, the content dir, or a filesystem root (that
    raises ``ValueError``). Set ``minify=False`` to skip the HTML-shrinking pass,
    ``search=False`` to skip building the search index, or ``social_cards=False``
    to skip per-page card generation (which otherwise runs when a browser is
    available and is a no-op when one is not).

    Pass ``docs_version`` to build a version snapshot instead of the current site:
    the output goes under ``config.versions_dir/<version>/``, pages canonical to
    ``/v/<version>/...``, the site-wide crawl files (sitemap, robots, llms,
    redirects, social cards) are left to the root build, and the version is
    stamped and added to ``versions.json`` (unless ``update_versions_manifest`` is
    False). ``alias`` (e.g. ``"latest"``) materializes that alias as redirects.
    """
    if project is None:  # pragma: no cover - supplied by @docs_project_scope
        raise RuntimeError("docs project scope was not initialized")
    if not update_versions_manifest and not docs_version:
        raise DocsConfigError("update_versions_manifest=False requires docs_version")
    if not update_versions_manifest and alias:
        raise DocsConfigError("a detached docs-version build cannot materialize an alias")
    if docs_version:
        validate_version_target(config.versions_dir, docs_version)
    if alias:
        validate_tree_identifier(alias, "alias")
        if not docs_version:
            raise DocsConfigError("alias requires docs_version")
        validate_alias_target(config.versions_dir, alias, docs_version)
    content_dir = config.content_dir
    if output_dir is None:
        output_dir = (config.versions_dir / docs_version) if docs_version else config.site_dir
    if output_dir.is_symlink():
        raise ValueError(f"Refusing to clear symlink output dir: {output_dir}")
    output_dir = output_dir.resolve()
    if docs_version:
        canonical_version_dir = (config.versions_dir / docs_version).resolve()
        if output_dir != canonical_version_dir and (update_versions_manifest or alias):
            raise DocsConfigError("a custom docs-version output requires update_versions_manifest=False and no alias")

    if not staging_output and _is_unsafe_output(output_dir, content_dir, config, docs_version=docs_version):
        msg = f"Refusing to clear unsafe output dir: {output_dir}"
        raise ValueError(msg)

    # Record where the runtime is served so a component's JS gets a URL pointing
    # at the file the build writes, instead of being inlined into every page.
    default_citry.set_mounted_prefix(CITRY_MOUNT_PREFIX)

    site_base = project.site_url.rstrip("/")
    # A version snapshot canonicals to its own /v/<version>/ tree.
    canonical_base = f"{site_base}/v/{docs_version}" if docs_version else site_base
    authored_nav = load_nav(content_dir / "_nav.yml")
    if authored_nav.has_source("reference"):
        validate_authored_reference_sources(project.reference, content_dir)
    include_site_content = not bool(docs_version)
    include_ui_source = include_site_content or authored_nav.scope_for_source("ui_library") != SCOPE_SITE
    if authored_nav.has_source("ui_library") and include_ui_source:
        validate_ui_library_sources(
            project.ui_library,
            repo_root=config.repo_root,
        )
        ui_previews = discover_ui_previews(
            project.ui_library,
            repo_root=config.repo_root,
        )
    else:
        ui_previews = ()
    include_blog_source = include_site_content or authored_nav.scope_for_source("blog") != SCOPE_SITE
    # Validate generated content before clearing the output directory whenever
    # it belongs to this build. Snapshot builds never inspect site-scoped input.
    blog_catalog = load_blog_catalog(content_dir) if authored_nav.has_source("blog") and include_blog_source else None
    nav_tree = load_site_nav(
        config,
        project=project,
        blog_catalog=blog_catalog,
        include_site_content=include_site_content,
    )
    md_files = sorted(
        path
        for path in content_dir.rglob("*.md")
        if path.name != "_nav.yml"
        and _generic_loop_owns_authored_page(path, content_dir)
        and (include_site_content or nav_tree.scope_for_url(md_to_url(path.relative_to(content_dir))) != SCOPE_SITE)
    )
    source_routes = {
        **(blog_catalog.source_to_public_path if blog_catalog is not None else blog_source_routes(content_dir)),
        **ui_library_source_routes(project.ui_library, repo_root=config.repo_root),
    }
    if include_site_content:
        published_paths = {item.path for item in nav_tree.flat_pages()} | (
            {nav_tree.home.path} if nav_tree.home else set()
        )
        occupied_paths = set(published_paths)
        occupied_paths.update(md_to_url(path.relative_to(content_dir)) for path in md_files)
        occupied_paths.update(source_routes.values())
        occupied_paths.update(preview.public_path for preview in ui_previews)
        for info in get_example_registry().values():
            demo = f"/examples/{info.public_slug}/demo/"
            occupied_paths.add(demo)
            occupied_paths.update(f"{demo}{variant}/" for variant in info.fragments)
        validate_redirect_routes(
            project.redirects,
            published_paths,
            occupied_paths=occupied_paths,
        )
        _validate_blog_feed_output(
            project.settings.blog.feed_path,
            pagefind_path=project.settings.pagefind_path,
            content_dir=content_dir,
            occupied_paths=occupied_paths | set(project.redirects.as_dict()),
        )
        _validate_pagefind_output(
            project.settings.pagefind_path,
            feed_path=project.settings.blog.feed_path,
            content_dir=content_dir,
            occupied_paths=occupied_paths | set(project.redirects.as_dict()),
        )
    version = configure_docs_globals(project)
    version_prefix = f"/v/{docs_version}" if docs_version else ""

    if output_dir.exists():
        shutil.rmtree(output_dir)

    outcome = BuildOutcome(output_dir=output_dir, docs_version=docs_version)
    start = time.monotonic()
    blog_feed_url = (
        nav_tree.project_path(project.settings.blog.feed_path, version_prefix)
        if blog_catalog and blog_catalog.posts
        else ""
    )

    for md_path in md_files:
        rel = md_path.relative_to(content_dir)
        out_path = md_to_html_path(output_dir, rel)
        page_url = md_to_url(rel)
        canonical = f"{canonical_base}/{page_url}" if canonical_base else ""

        try:
            source = md_path.read_text(encoding="utf-8")
            result = render_page(
                source,
                config=config,
                canonical=canonical,
                nav_tree=nav_tree,
                current_path=page_url,
                version=version,
                source_path=md_path,
                blog_catalog=blog_catalog,
                is_blog_index=rel == Path("blog/index.md"),
                blog_feed_url=blog_feed_url,
                version_prefix=version_prefix,
                source_to_public_path=source_routes,
            )
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(result.html, encoding="utf-8")
            record = _record_for(page_url, canonical, result, source_md=md_path)
            # Also emit the expanded markdown as a `.md` companion beside the page,
            # so LLMs and tools can fetch the raw markdown. Its `url:` is the page's
            # resolved canonical, matching the record and the page's canonical link.
            _write_companion(md_companion_path(output_dir, rel), result.meta, result.markdown_body, record.canonical)
            outcome.built += 1
            outcome.companions += 1
            outcome.records.append(record)
        except Exception as exc:  # noqa: BLE001 - one bad page must not abort the build
            outcome.failed += 1
            outcome.errors.append((str(rel), f"{type(exc).__name__}: {exc}"))

    if include_ui_source and authored_nav.has_source("ui_library"):
        ui_records, ui_errors = _build_ui_library_pages(
            output_dir,
            config,
            nav_tree,
            version,
            canonical_base,
            project.ui_library,
            source_routes=source_routes,
            blog_catalog=blog_catalog,
            blog_feed_url=blog_feed_url,
            version_prefix=version_prefix,
        )
        outcome.ui_library = len(ui_records)
        outcome.built += len(ui_records)
        outcome.companions += len(ui_records)
        outcome.records.extend(ui_records)
        outcome.failed += len(ui_errors)
        outcome.errors.extend(ui_errors)
        preview_count, preview_errors = _build_ui_previews(
            output_dir,
            ui_previews,
            repo_root=config.repo_root,
        )
        outcome.ui_previews = preview_count
        outcome.failed += len(preview_errors)
        outcome.errors.extend(preview_errors)

    if blog_catalog is not None:
        blog_records, blog_errors = _build_blog_posts(
            output_dir,
            config,
            nav_tree,
            version,
            canonical_base,
            blog_catalog,
            blog_feed_url,
            version_prefix,
        )
        outcome.blog_posts = len(blog_records)
        outcome.built += len(blog_records)
        outcome.companions += len(blog_records)
        outcome.records.extend(blog_records)
        outcome.failed += len(blog_errors)
        outcome.errors.extend(blog_errors)
        outcome.blog_feed = _write_blog_feed(output_dir, config, blog_catalog)

    _copy_non_markdown_assets(
        content_dir,
        output_dir,
        nav_tree=nav_tree,
        include_site_content=include_site_content,
    )
    # A version snapshot is mounted under /v/ and its pages emit root-absolute
    # /static URLs, so it shares the root build's /static rather than copying it.
    if not docs_version:
        _copy_static_assets(config, output_dir)
    outcome.examples = _pre_render_examples(
        output_dir,
        nav_tree=nav_tree,
        include_site_content=include_site_content,
    )
    ref_records = []
    build_reference = include_site_content or (
        nav_tree.has_source("reference") and nav_tree.scope_for_source("reference") != SCOPE_SITE
    )
    if build_reference:
        ref_records = _build_reference(
            output_dir,
            config,
            nav_tree,
            version,
            canonical_base,
            blog_catalog=blog_catalog,
            blog_feed_url=blog_feed_url,
            version_prefix=version_prefix,
        )
    outcome.reference = len(ref_records)
    outcome.records.extend(ref_records)
    rel_records = []
    build_releases = include_site_content or (
        nav_tree.has_source("releases") and nav_tree.scope_for_source("releases") != SCOPE_SITE
    )
    if build_releases:
        rel_records = _build_releases(
            output_dir,
            config,
            nav_tree,
            version,
            canonical_base,
            blog_catalog=blog_catalog,
            blog_feed_url=blog_feed_url,
            version_prefix=version_prefix,
        )
    outcome.releases = len(rel_records)
    outcome.records.extend(rel_records)
    if docs_version and not (output_dir / "index.html").is_file():
        _write_snapshot_home_redirect(output_dir, nav_tree, canonical_base)
    # objects.inv lets other docs sites cross-link into citry's reference.
    if build_reference:
        (output_dir / "objects.inv").write_bytes(build_objects_inv(version))

    # The custom 404 GitHub Pages serves on any unmatched path.
    outcome.not_found = _build_not_found(
        output_dir,
        config,
        nav_tree,
        version,
        blog_catalog=blog_catalog,
        blog_feed_url=blog_feed_url,
        version_prefix=version_prefix,
    )

    # The site-wide crawl / index / card files belong to the root build only; a
    # version snapshot is mounted under /v/ and shares the root's robots+sitemap.
    if not docs_version:
        outcome.redirects = emit_redirects(
            output_dir,
            site_url=project.site_url,
            redirects=project.redirects.as_dict(),
        )
        seo = generate_seo_files(
            outcome.records,
            output_dir,
            site_url=project.site_url,
            version=version,
            generated_at=datetime.now(tz=timezone.utc),
            repo_root=config.repo_root,
            # robots.txt disallows old /v/<version>/ trees; read the committed
            # versions/ manifest, whose disallow paths are stable whether or not
            # /v/ is mounted in this particular build.
            versions_root=config.versions_dir,
        )
        outcome.sitemap_urls = seo.sitemap_urls
        outcome.llms_links, outcome.llms_pages = generate_llms_files(
            outcome.records,
            output_dir,
            nav_tree,
            site_url=project.site_url,
            site_name=project.settings.name,
        )
        if social_cards:
            card_outcome = generate_social_cards(
                output_dir,
                outcome.records,
                nav_tree,
                site_url=project.site_url,
                site_name=project.settings.name,
                cache_dir=config.base_dir / ".cache" / "og",
            )
            outcome.social_cards_placed = card_outcome.placed
            outcome.social_cards_skipped = card_outcome.skipped_reason

    # The client runtime and the search index are also shared from the root: a
    # snapshot's pages reference the client and configured search assets at the
    # site root.
    if not docs_version:
        # The client runtime, so a component's JavaScript loads from flat files.
        outcome.runtime = export_runtime(output_dir, default_citry)

        # The search index, built by scanning the written HTML. A failure here is
        # recorded but does not fail the build (the pages are already on disk).
        if search:
            pagefind_subdir = project.settings.pagefind_path.removeprefix("/").rsplit("/", 1)[0]
            search_result = run_pagefind(output_dir, pagefind_subdir)
            outcome.search_ok = search_result.ok
            outcome.search_message = search_result.message

    # Minify last among the content writers: it is the final step that produces
    # HTML, so every other writer has already run.
    if minify:
        outcome.minified = minify_site(output_dir).files

    # Base-path rewriting is truly last: it edits the finished HTML in place for a
    # subpath deploy. A no-op when no base path is configured.
    outcome.base_path_files = apply_base_path(output_dir, config.base_path)

    # Version mode: stamp the snapshot, record it in the manifest, and write any
    # alias redirects, so the committed versions tree stays consistent.
    if docs_version and not outcome.failed:
        write_build_info(
            output_dir,
            version=docs_version,
            source_sha=git_head_sha(config.repo_root),
            site_routes=nav_tree.site_route_patterns(),
        )
        if update_versions_manifest:
            update_manifest(config.versions_dir, docs_version, aliases=(alias,) if alias else ())
        if alias:
            outcome.alias_redirects = materialize_alias(config.versions_dir, alias, docs_version)

    outcome.elapsed = time.monotonic() - start
    return outcome


def _replace_output_directory(staged_dir: Path, target_dir: Path) -> None:
    """Replace ``target_dir`` with a completed staged build, restoring it on error."""
    if staged_dir.is_symlink() or not staged_dir.is_dir():
        raise ValueError(f"Staged output must be a directory: {staged_dir}")
    if target_dir.is_symlink() or (target_dir.exists() and not target_dir.is_dir()):
        raise ValueError(f"Existing output target must be a directory: {target_dir}")
    backup_dir: Path | None = None
    if target_dir.exists():
        backup_dir = Path(tempfile.mkdtemp(prefix=f".{target_dir.name}.backup-", dir=target_dir.parent))
        backup_dir.rmdir()
        target_dir.replace(backup_dir)
    try:
        staged_dir.replace(target_dir)
    except Exception:
        if backup_dir is not None:
            backup_dir.replace(target_dir)
        raise
    if backup_dir is not None:
        shutil.rmtree(backup_dir)


def _record_for(
    page_url: str,
    canonical: str,
    result: RenderResult,
    *,
    source_md: Path | None,
    blog_post: BlogPost | None = None,
) -> PageRecord:
    """Build a ``PageRecord`` from a render result (front matter wins for canonical)."""
    meta = result.meta
    return PageRecord(
        url=page_url,
        canonical=(meta.canonical if meta and meta.canonical else canonical),
        title=meta.title if meta else "",
        description=meta.description if meta else "",
        noindex=bool(meta and meta.noindex),
        is_doc_page=True,
        source_md=source_md,
        markdown_body=result.markdown_body,
        editorial_updated=blog_post.effective_updated if blog_post else None,
    )


def _write_companion(
    path: Path,
    meta: PageMeta | None,
    markdown_body: str,
    canonical: str,
    *,
    blog_post: BlogPost | None = None,
) -> None:
    """
    Write a ``.md`` companion (front matter + expanded markdown) beside a page.

    LLMs and tools that want the raw markdown fetch this instead of scraping the
    HTML. The front matter carries just enough to identify the page (title,
    canonical URL, description); the body is the page's markdown after the custom
    ``<c-*>`` tags and ``--8<--`` snippet includes were expanded
    (``RenderResult.markdown_body``).
    """
    header_lines = ["---"]
    title = meta.title if meta else ""
    description = meta.description if meta else ""
    if title:
        if blog_post is not None:
            header_lines.append(f'title: "{_escape_yaml_double_quoted(title)}"')
        else:
            header_lines.append(f"title: {title}")
    if canonical:
        header_lines.append(f"url: {canonical}")
    if description:
        # Quote the description so a colon or a leading special char stays valid YAML.
        desc = _escape_yaml_double_quoted(description)
        header_lines.append(f'description: "{desc}"')
    if blog_post is not None:
        header_lines.extend(
            [
                f'date: "{blog_post.published.isoformat()}"',
                f'author: "{_escape_yaml_double_quoted(blog_post.author)}"',
            ]
        )
        if blog_post.updated is not None:
            header_lines.append(f'updated: "{blog_post.updated.isoformat()}"')
        if blog_post.author_url:
            header_lines.append(f'author_url: "{_escape_yaml_double_quoted(blog_post.author_url)}"')
        if blog_post.tags:
            header_lines.append("tags:")
            header_lines.extend(f'  - "{_escape_yaml_double_quoted(tag)}"' for tag in blog_post.tags)
    header_lines.append("---")
    header_lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(header_lines) + markdown_body, encoding="utf-8")


def _escape_yaml_double_quoted(value: str) -> str:
    """Escape a scalar embedded in a YAML double-quoted string."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _generic_loop_owns_authored_page(path: Path, content_dir: Path) -> bool:
    """Return whether the generic authored-page loop owns ``path``."""
    rel = path.relative_to(content_dir)
    # Citry UI component routes read their authoritative api.md files through
    # the catalog. Reserve this old copy location so a stale derived file can
    # never create a second page record for the same public route.
    if rel.parts[:2] == ("ui-library", "components"):
        return False
    if not rel.parts or rel.parts[0] != "blog":
        return True
    # The Blog index follows the ordinary clean-URL path. Dated posts are built
    # separately from the catalog so their filenames never leak into URLs.
    return rel == Path("blog/index.md")


def _validate_blog_feed_output(
    feed_path: str,
    *,
    pagefind_path: str,
    content_dir: Path,
    occupied_paths: set[str],
) -> None:
    """Require the feed to own a file path outside every other output tree."""
    feed_relative = feed_path.lstrip("/")
    pagefind_subdir = pagefind_path.lstrip("/").rsplit("/", 1)[0]
    planned_files = _planned_output_files(content_dir, occupied_paths)
    if _file_collides_with_files(feed_relative, planned_files) or _file_collides_with_directory(
        feed_relative, pagefind_subdir
    ):
        raise DocsConfigError(f"blog.feed_path collides with another output: {feed_path}")


def _validate_pagefind_output(
    pagefind_path: str,
    *,
    feed_path: str,
    content_dir: Path,
    occupied_paths: set[str],
) -> None:
    """Require Pagefind to own a previously unused output directory."""
    output_subdir = pagefind_path.removeprefix("/").rsplit("/", 1)[0]
    reserved_root = output_subdir.split("/", 1)[0].casefold() in {"citry", "meta", "og", "static", "v"}
    planned_files = _planned_output_files(content_dir, occupied_paths)
    planned_files.add(feed_path.lstrip("/"))
    if reserved_root or _directory_collides_with_files(output_subdir, planned_files):
        raise DocsConfigError(f"search.pagefind_path collides with another output: {pagefind_path}")


def _normalize_output_routes(paths: set[str]) -> set[str]:
    return {f"/{path.strip('/')}/" if path.strip("/") else "/" for path in paths}


def _route_output_files(routes: set[str]) -> set[str]:
    files: set[str] = set()
    for path in routes:
        route = path.strip("/")
        prefix = f"{route}/" if route else ""
        files.update({f"{prefix}index.html", f"{prefix}index.md"})
    return files


def _planned_output_files(content_dir: Path, occupied_paths: set[str]) -> set[str]:
    """Return file paths that are known before the output directory is cleared."""
    files = _route_output_files(_normalize_output_routes(occupied_paths))
    files.update(
        {
            "404.html",
            "llms-full.txt",
            "llms.txt",
            "meta/indexing.json",
            "objects.inv",
            "robots.txt",
            "sitemap.xml",
        }
    )
    files.update(
        path.relative_to(content_dir).as_posix()
        for path in content_dir.rglob("*")
        if path.is_file() and path.suffix != ".md" and path.name != "_nav.yml"
    )
    return files


def _file_collides_with_files(path: str, files: set[str]) -> bool:
    """Return whether either file path would require treating the other as a directory."""
    comparable = _portable_path_key(path)
    return any(
        comparable == (other := _portable_path_key(candidate))
        or comparable.startswith(f"{other}/")
        or other.startswith(f"{comparable}/")
        for candidate in files
    )


def _file_collides_with_directory(file_path: str, directory: str) -> bool:
    """Return whether a file is the directory, contains it, or lives below it."""
    comparable_file = _portable_path_key(file_path)
    comparable_directory = _portable_path_key(directory)
    return (
        comparable_file == comparable_directory
        or comparable_file.startswith(f"{comparable_directory}/")
        or comparable_directory.startswith(f"{comparable_file}/")
    )


def _directory_collides_with_files(directory: str, files: set[str]) -> bool:
    """Return whether a generated directory overlaps any planned output file."""
    return any(_file_collides_with_directory(file_path, directory) for file_path in files)


def _portable_path_key(path: str) -> str:
    """Compare output paths as case- and normalization-insensitive filesystems do."""
    return normalize("NFC", path).casefold()


def _build_ui_library_pages(
    output_dir: Path,
    config: DocsConfig,
    nav_tree: NavTree,
    version: str,
    canonical_base: str,
    catalog: UiLibraryCatalog,
    *,
    source_routes: Mapping[Path, str],
    blog_catalog: BlogCatalog | None = None,
    blog_feed_url: str = "",
    version_prefix: str = "",
) -> tuple[list[PageRecord], list[tuple[str, str]]]:
    """Render component-owned API sources directly to their catalog routes."""
    records: list[PageRecord] = []
    errors: list[tuple[str, str]] = []
    for projection in catalog.projections:
        source_path = ui_library_source_path(projection, repo_root=config.repo_root)
        page_url = projection.public_path.lstrip("/")
        canonical = f"{canonical_base}{projection.public_path}" if canonical_base else ""
        try:
            result = render_page(
                compose_ui_library_source(source_path, family=projection.family),
                config=config,
                canonical=canonical,
                nav_tree=nav_tree,
                current_path=page_url,
                version=version,
                source_path=source_path,
                blog_catalog=blog_catalog,
                blog_feed_url=blog_feed_url,
                version_prefix=version_prefix,
                source_to_public_path=source_routes,
            )
            html_path = clean_url_to_html_path(output_dir, projection.public_path)
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text(result.html, encoding="utf-8")
            record = _record_for(page_url, canonical, result, source_md=source_path)
            _write_companion(
                clean_url_to_companion_path(output_dir, projection.public_path),
                result.meta,
                result.markdown_body,
                record.canonical,
            )
            records.append(record)
        except Exception as exc:  # noqa: BLE001 - match ordinary authored-page failure isolation
            errors.append((projection.source.as_posix(), f"{type(exc).__name__}: {exc}"))
    return records, errors


def _build_ui_previews(
    output_dir: Path,
    previews: tuple[UiPreview, ...],
    *,
    repo_root: Path,
) -> tuple[int, list[tuple[str, str]]]:
    """Render private component previews without publishing page records."""
    built = 0
    errors: list[tuple[str, str]] = []
    for preview in previews:
        try:
            html = render_ui_preview_document(preview, repo_root=repo_root)
            target = clean_url_to_html_path(output_dir, preview.public_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            built += 1
        except Exception as exc:  # noqa: BLE001 - preserve per-page build isolation
            label = f"{preview.source.as_posix()} ({preview.public_path})"
            errors.append((label, f"{type(exc).__name__}: {exc}"))
    return built, errors


def _build_blog_posts(
    output_dir: Path,
    config: DocsConfig,
    nav_tree: NavTree,
    version: str,
    canonical_base: str,
    catalog: BlogCatalog,
    blog_feed_url: str,
    version_prefix: str,
) -> tuple[list[PageRecord], list[tuple[str, str]]]:
    """Render catalog posts to stable slug routes and Markdown companions."""
    records: list[PageRecord] = []
    errors: list[tuple[str, str]] = []
    for post in catalog.posts:
        page_url = post.public_path.lstrip("/")
        canonical = f"{canonical_base}{post.public_path}" if canonical_base else ""
        try:
            result = render_page(
                post.source,
                config=config,
                canonical=canonical,
                nav_tree=nav_tree,
                current_path=page_url,
                version=version,
                source_path=post.source_path,
                blog_catalog=catalog,
                blog_post=post,
                blog_feed_url=blog_feed_url,
                version_prefix=version_prefix,
            )
            html_path = clean_url_to_html_path(output_dir, post.public_path)
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text(result.html, encoding="utf-8")
            record = _record_for(
                page_url,
                canonical,
                result,
                source_md=post.source_path,
                blog_post=post,
            )
            _write_companion(
                clean_url_to_companion_path(output_dir, post.public_path),
                result.meta,
                result.markdown_body,
                record.canonical,
                blog_post=post,
            )
            records.append(record)
        except Exception as exc:  # noqa: BLE001 - match ordinary authored-page failure isolation
            errors.append((post.source_rel.as_posix(), f"{type(exc).__name__}: {exc}"))
    return records, errors


def _write_blog_feed(output_dir: Path, config: DocsConfig, catalog: BlogCatalog) -> bool:
    """Write the Atom feed when at least one published post exists."""
    project = current_docs_project()
    xml = serialize_atom_feed(
        catalog,
        site_url=project.site_url,
        base_path=config.base_path,
        feed_path=project.settings.blog.feed_path,
        feed_limit=project.settings.blog.feed_limit,
    )
    if not xml:
        return False
    feed_path = output_dir / project.settings.blog.feed_path.lstrip("/")
    feed_path.parent.mkdir(parents=True, exist_ok=True)
    feed_path.write_text(xml, encoding="utf-8")
    return True


def _citry_version() -> str:
    """The installed citry version (shown in the footer), or ``""`` if unknown."""
    try:
        return get_version("citry")
    except PackageNotFoundError:
        return ""


def configure_docs_globals(project: DocsProject | DocsConfig) -> str:
    """
    Expose shared values to every template, and return the citry version.

    Sets ``version`` and ``site_name`` as Citry template globals, so a page can
    write ``{{ version }}`` or ``{{ site_name }}`` directly (the docs site
    dogfoods Citry's global-variables feature instead of a dedicated tag).
    """
    if isinstance(project, DocsConfig):
        from docs_site._internal.project import load_docs_project  # noqa: PLC0415

        project = load_docs_project(project)
    version = _citry_version()
    default_citry.template_globals.update(
        {
            "version": version,
            "site_name": project.settings.name,
            "repo_url": project.settings.repository.url,
            "repo_full_name": project.settings.repository.full_name,
            "repo_edit_branch": project.settings.repository.edit_branch,
            "repo_issues_url": project.settings.repository.issues_url,
            "repo_sponsors_url": project.settings.repository.sponsors_url,
            "pypi_url": project.settings.pypi_url,
            "discord_url": project.settings.discord_url,
        }
    )
    return version


def _is_unsafe_output(
    output_dir: Path,
    content_dir: Path,
    config: DocsConfig,
    *,
    docs_version: str = "",
) -> bool:
    """Reject any clear target that overlaps source, config, or version inputs."""
    resolved = output_dir.resolve()
    if resolved == Path(resolved.anchor):
        return True

    repo_root = config.repo_root.resolve()
    if resolved == repo_root or repo_root.is_relative_to(resolved):
        return True

    base_dir = config.base_dir.resolve()
    protected_dirs = {
        content_dir.resolve(),
        config.examples_dir.resolve(),
        *(base_dir / name for name in ("_internal", "data", "scripts", "static")),
    }
    if any(
        resolved == protected or resolved.is_relative_to(protected) or protected.is_relative_to(resolved)
        for protected in protected_dirs
    ):
        return True

    versions_dir = config.versions_dir.resolve()
    allowed_version_output = bool(docs_version) and resolved == (versions_dir / docs_version).resolve()
    declared_site_output = not docs_version and resolved == config.site_dir.resolve() and resolved != base_dir
    if not (allowed_version_output or declared_site_output) and (
        resolved == base_dir or resolved.is_relative_to(base_dir) or base_dir.is_relative_to(resolved)
    ):
        return True
    if not allowed_version_output and (
        resolved == versions_dir or resolved.is_relative_to(versions_dir) or versions_dir.is_relative_to(resolved)
    ):
        return True

    config_paths = {
        config.settings_config,
        config.reference_config,
        config.ui_library_config,
        config.redirects_config,
        config.versions_config,
        config.people_sources_config,
    }
    return any(path.resolve() == resolved or path.resolve().is_relative_to(resolved) for path in config_paths)


def _copy_non_markdown_assets(
    content_dir: Path,
    output_dir: Path,
    *,
    nav_tree: NavTree,
    include_site_content: bool,
) -> None:
    """Copy images and other non-``.md`` content files into the output tree verbatim."""
    for asset in content_dir.rglob("*"):
        if asset.is_dir() or asset.suffix == ".md" or asset.name == "_nav.yml":
            continue
        rel = asset.relative_to(content_dir)
        if not include_site_content and nav_tree.scope_for_content_asset(rel) == SCOPE_SITE:
            continue
        dest = output_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, dest)


def _copy_static_assets(config: DocsConfig, output_dir: Path) -> None:
    """Copy the site's static assets (CSS, JS, fonts, images) into ``<output>/static``."""
    static_dir = config.base_dir / "static"
    if static_dir.is_dir():
        shutil.copytree(static_dir, output_dir / "static", dirs_exist_ok=True)


def _write_snapshot_home_redirect(output_dir: Path, nav_tree: NavTree, canonical_base: str) -> None:
    """Give a snapshot a stable home when the root landing page is site-scoped."""
    for item in nav_tree.flat_pages():
        if item.scope == SCOPE_SITE or item.path == "/":
            continue
        target = output_dir / item.path.strip("/") / "index.html"
        if not target.is_file():
            continue
        emit_redirects(
            output_dir,
            site_url=canonical_base,
            redirects={"/": item.path},
        )
        return
    raise RuntimeError("Version snapshot has no built versioned page for its homepage")


def _build_reference(
    output_dir: Path,
    config: DocsConfig,
    nav_tree: NavTree,
    version: str,
    canonical_base: str,
    *,
    blog_catalog: BlogCatalog | None = None,
    blog_feed_url: str = "",
    version_prefix: str = "",
) -> list[PageRecord]:
    """Render the generated API-reference index and category pages."""
    records: list[PageRecord] = []

    def write(page_url: str, source: str) -> None:
        canonical = f"{canonical_base}/{page_url}" if canonical_base else ""
        result = render_page(
            source,
            config=config,
            canonical=canonical,
            nav_tree=nav_tree,
            current_path=page_url,
            version=version,
            blog_catalog=blog_catalog,
            blog_feed_url=blog_feed_url,
            version_prefix=version_prefix,
        )
        out_path = output_dir / page_url / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result.html, encoding="utf-8")
        records.append(_record_for(page_url, canonical, result, source_md=None))

    project = current_docs_project()
    write("reference/", reference_index_markdown(project.reference))
    for cat in project.reference.categories:
        # Authored categories were rendered with the normal content pages. Do
        # not overwrite their HTML or create a duplicate PageRecord here.
        if cat.authored:
            continue
        write(f"reference/{cat.slug}/", reference_page_markdown(cat))
    return records


def _build_releases(
    output_dir: Path,
    config: DocsConfig,
    nav_tree: NavTree,
    version: str,
    canonical_base: str,
    *,
    blog_catalog: BlogCatalog | None = None,
    blog_feed_url: str = "",
    version_prefix: str = "",
) -> list[PageRecord]:
    """Generate and render the release-notes pages (the index plus one per version)."""
    records: list[PageRecord] = []

    def write(page_url: str, source: str) -> None:
        canonical = f"{canonical_base}/{page_url}" if canonical_base else ""
        # run_citry_pass=False: release prose shows citry syntax as text, not as
        # tags to execute (a `<c-raw>` in the notes would otherwise break Pass 1).
        result = render_page(
            source,
            config=config,
            canonical=canonical,
            nav_tree=nav_tree,
            current_path=page_url,
            version=version,
            run_citry_pass=False,
            blog_catalog=blog_catalog,
            blog_feed_url=blog_feed_url,
            version_prefix=version_prefix,
        )
        out_path = output_dir / page_url / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result.html, encoding="utf-8")
        records.append(_record_for(page_url, canonical, result, source_md=None))

    # A missing CHANGELOG.md (some embed/test configs point repo_root at a bare
    # dir) yields no release pages. The "Release notes" nav entry is gated on the
    # same check in build_site, so the sidebar link and the pages stay in step.
    changelog = config.repo_root / "CHANGELOG.md"
    if not changelog.is_file():
        return records
    releases = parse_changelog(
        changelog.read_text(encoding="utf-8"),
        exclude=current_docs_project().settings.excluded_releases,
    )
    write("releases/", release_index_markdown(releases))
    for release in releases:
        write(f"releases/{release.slug}/", release_page_markdown(release))
    return records


def _build_not_found(
    output_dir: Path,
    config: DocsConfig,
    nav_tree: NavTree,
    version: str,
    *,
    blog_catalog: BlogCatalog | None = None,
    blog_feed_url: str = "",
    version_prefix: str = "",
) -> bool:
    """
    Write ``404.html`` - the page GitHub Pages serves for any path that does not exist.

    The page gives a lost visitor three ways forward: a button that opens the
    same search modal as the header (the DocPage layout renders that modal on
    every page), a short list of popular destinations, and a link to report a
    page that has moved. The destination links are absolute because a 404 is
    served at arbitrary deep paths, so a relative link would resolve against the
    wrong base; the build-check ``internal_link`` guard confirms they still point
    at built pages.
    """
    source = (
        "---\n"
        "title: Page not found\n"
        "noindex: true\n"
        "searchable: false\n"
        "---\n\n"
        "# Page not found\n\n"
        "The page you are looking for does not exist or may have moved.\n\n"
        # A button, not a link: search.js opens the search modal for every element
        # tagged data-search-open, the same hook the header search trigger uses.
        '<button class="djc-notfound__search" type="button" data-search-open>'
        "Search the documentation</button>\n\n"
        "## Popular destinations\n\n"
        "- [Installation](/getting-started/installation/)\n"
        "- [Your first component](/getting-started/your-first-component/)\n"
        "- [Components](/concepts/components/)\n"
        "- [API reference](/reference/)\n\n"
        "If a page that recently existed is now missing, "
        # Raw anchor so the report link opens in a new tab (the site's convention
        # for offsite links), which a plain markdown link would not carry.
        f'<a href="{escape(current_docs_project().settings.repository.issues_url, quote=True)}" '
        'target="_blank" rel="noopener">'
        "open an issue</a> and we will fix the link.\n"
    )
    html = render_page(
        source,
        config=config,
        canonical="",
        nav_tree=nav_tree,
        current_path="404",
        version=version,
        blog_catalog=blog_catalog,
        blog_feed_url=blog_feed_url,
        version_prefix=version_prefix,
    ).html
    (output_dir / "404.html").write_text(html, encoding="utf-8")
    return True


def _pre_render_examples(
    output_dir: Path,
    *,
    nav_tree: NavTree,
    include_site_content: bool,
) -> int:
    """Render each example's standalone page (and any fragment variants) to static files."""
    count = 0
    for info in get_example_registry().values():
        route = f"/examples/{info.public_slug}/"
        if not include_site_content and nav_tree.scope_for_url(route) == SCOPE_SITE:
            continue
        out_path = output_dir / "examples" / info.public_slug / "demo" / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(str(info.page_cls()), encoding="utf-8")
        count += 1
        # A fragment demo: pre-render each variant as an HTML fragment to its own
        # endpoint, and write the fragment component's dep files so the client
        # runtime can load its JS/CSS on the static site (see export_fragment_deps).
        for variant, comp_cls in info.fragments.items():
            variant_path = output_dir / "examples" / info.public_slug / "demo" / variant / "index.html"
            variant_path.parent.mkdir(parents=True, exist_ok=True)
            variant_path.write_text(comp_cls().render().serialize(deps_strategy="fragment"), encoding="utf-8")
            export_fragment_deps(output_dir, comp_cls)
            count += 1
    return count
