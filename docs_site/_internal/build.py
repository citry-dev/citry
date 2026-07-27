"""
Build the static site: render every markdown page to HTML on disk.

Walks the content directory, renders each ``*.md`` through the pipeline, and
writes the result to ``<output>/<slug>/index.html`` (clean URLs). Non-markdown
files (images, etc.) are copied across verbatim so relative references keep
working.

A content page that fails to render is recorded on the outcome rather than
aborting the whole build, so one broken page does not hide the others. The
generated pages (the API reference and the 404 page) are not guarded that way: a
failure there is a bug in this builder, not bad page content, so it stops the
build loudly.

After the pages are written the build runs its finishing steps in a fixed
order: the API reference and example demos, the ``objects.inv`` index, the
custom 404 page, Citry's client runtime (so component JavaScript works from
flat files), and finally an HTML-shrinking pass. Each page that the layout
produces is also recorded in ``BuildOutcome.records`` so later steps (sitemap,
robots, llms files) can be built from that list without re-reading the output.
"""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from pathlib import Path
from typing import TYPE_CHECKING

from citry import citry as default_citry
from docs_site._internal.base_path import apply_base_path
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.crossrefs import build_objects_inv
from docs_site._internal.examples import get_example_registry
from docs_site._internal.llms import generate_llms_files
from docs_site._internal.minify import minify_site
from docs_site._internal.nav import load_nav
from docs_site._internal.pagefind import run_pagefind
from docs_site._internal.paths import md_companion_path, md_to_html_path, md_to_url
from docs_site._internal.pipeline import RenderResult, render_page
from docs_site._internal.redirects import emit_redirects
from docs_site._internal.reference_pages import (
    CATEGORIES,
    reference_index_markdown,
    reference_nav_section,
    reference_page_markdown,
)
from docs_site._internal.release_notes import (
    parse_changelog,
    release_index_markdown,
    release_page_markdown,
    releases_nav_section,
)
from docs_site._internal.seo import generate_seo_files
from docs_site._internal.social_cards import generate_social_cards
from docs_site._internal.static_deps import CITRY_MOUNT_PREFIX, export_fragment_deps, export_runtime
from docs_site._internal.versioning import git_head_sha, materialize_alias, update_manifest, write_build_info

if TYPE_CHECKING:
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
    # The markdown source for a content page, or None for a generated page.
    source_md: Path | None
    # The page body as expanded markdown, for the llms full-text export.
    markdown_body: str


@dataclass
class BuildOutcome:
    """Result of a build: where it wrote, how many pages, and any failures."""

    output_dir: Path
    built: int = 0
    failed: int = 0
    # Per-page `.md` companion files written beside content pages (the raw
    # expanded markdown, for LLMs and tools that want the source not the HTML).
    companions: int = 0
    examples: int = 0
    reference: int = 0
    releases: int = 0
    elapsed: float = 0.0
    # (page path relative to content dir, error message) for pages that raised.
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
    config = config or default_config
    content_dir = config.content_dir
    if output_dir is None:
        output_dir = (config.versions_dir / docs_version) if docs_version else config.site_dir
    output_dir = output_dir.resolve()

    if _is_unsafe_output(output_dir, content_dir, config):
        msg = f"Refusing to clear unsafe output dir: {output_dir}"
        raise ValueError(msg)

    # Record where the runtime is served so a component's JS gets a URL pointing
    # at the file the build writes, instead of being inlined into every page.
    default_citry.set_mounted_prefix(CITRY_MOUNT_PREFIX)

    site_base = config.site_url.rstrip("/")
    # A version snapshot canonicals to its own /v/<version>/ tree.
    canonical_base = f"{site_base}/v/{docs_version}" if docs_version else site_base
    md_files = sorted(p for p in content_dir.rglob("*.md") if p.name != "_nav.yml")
    nav_tree = load_nav(content_dir / "_nav.yml")
    # The "Release notes" section lists one item per version, so it needs the
    # parsed changelog; skip it entirely when there is no CHANGELOG (the pages
    # are skipped in _build_releases on the same check, so the link is never dead).
    changelog_file = config.repo_root / "CHANGELOG.md"
    if changelog_file.is_file():
        nav_tree.sections.append(releases_nav_section(parse_changelog(changelog_file.read_text(encoding="utf-8"))))
    nav_tree.sections.append(reference_nav_section())
    version = configure_docs_globals(config)

    if output_dir.exists():
        shutil.rmtree(output_dir)

    outcome = BuildOutcome(output_dir=output_dir, docs_version=docs_version)
    start = time.monotonic()

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

    _copy_non_markdown_assets(content_dir, output_dir)
    # A version snapshot is mounted under /v/ and its pages emit root-absolute
    # /static URLs, so it shares the root build's /static rather than copying it.
    if not docs_version:
        _copy_static_assets(config, output_dir)
    outcome.examples = _pre_render_examples(output_dir)
    ref_records = _build_reference(output_dir, config, nav_tree, version, canonical_base)
    outcome.reference = len(ref_records)
    outcome.records.extend(ref_records)
    rel_records = _build_releases(output_dir, config, nav_tree, version, canonical_base)
    outcome.releases = len(rel_records)
    outcome.records.extend(rel_records)
    # objects.inv lets other docs sites cross-link into citry's reference.
    (output_dir / "objects.inv").write_bytes(build_objects_inv(version))

    # The custom 404 GitHub Pages serves on any unmatched path.
    outcome.not_found = _build_not_found(output_dir, config, nav_tree, version)

    # The site-wide crawl / index / card files belong to the root build only; a
    # version snapshot is mounted under /v/ and shares the root's robots+sitemap.
    if not docs_version:
        outcome.redirects = emit_redirects(output_dir, site_url=config.site_url)
        seo = generate_seo_files(
            outcome.records,
            output_dir,
            site_url=config.site_url,
            version=version,
            generated_at=datetime.now(tz=UTC),
            repo_root=config.repo_root,
            # robots.txt disallows old /v/<version>/ trees; read the committed
            # versions/ manifest, whose disallow paths are stable whether or not
            # /v/ is mounted in this particular build.
            versions_root=config.versions_dir,
        )
        outcome.sitemap_urls = seo.sitemap_urls
        outcome.llms_links, outcome.llms_pages = generate_llms_files(
            outcome.records, output_dir, nav_tree, site_url=config.site_url, site_name=config.site_name
        )
        if social_cards:
            card_outcome = generate_social_cards(
                output_dir,
                outcome.records,
                nav_tree,
                site_url=config.site_url,
                cache_dir=config.base_dir / ".cache" / "og",
            )
            outcome.social_cards_placed = card_outcome.placed
            outcome.social_cards_skipped = card_outcome.skipped_reason

    # The client runtime and the search index are also shared from the root: a
    # snapshot's pages reference /citry/citry.js and /pagefind/ at the site root.
    if not docs_version:
        # The client runtime, so a component's JavaScript loads from flat files.
        outcome.runtime = export_runtime(output_dir, default_citry)

        # The search index, built by scanning the written HTML. A failure here is
        # recorded but does not fail the build (the pages are already on disk).
        if search:
            search_result = run_pagefind(output_dir)
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
    if docs_version:
        write_build_info(output_dir, version=docs_version, source_sha=git_head_sha(config.repo_root))
        if update_versions_manifest:
            update_manifest(config.versions_dir, docs_version, aliases=(alias,) if alias else ())
        if alias:
            outcome.alias_redirects = materialize_alias(config.versions_dir, alias, docs_version)

    outcome.elapsed = time.monotonic() - start
    return outcome


def _record_for(page_url: str, canonical: str, result: RenderResult, *, source_md: Path | None) -> PageRecord:
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
    )


def _write_companion(path: Path, meta: PageMeta | None, markdown_body: str, canonical: str) -> None:
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
        header_lines.append(f"title: {title}")
    if canonical:
        header_lines.append(f"url: {canonical}")
    if description:
        # Quote the description so a colon or a leading special char stays valid YAML.
        desc = description.replace('"', '\\"')
        header_lines.append(f'description: "{desc}"')
    header_lines.append("---")
    header_lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(header_lines) + markdown_body, encoding="utf-8")


def _citry_version() -> str:
    """The installed citry version (shown in the footer), or ``""`` if unknown."""
    try:
        return get_version("citry")
    except PackageNotFoundError:
        return ""


def configure_docs_globals(config: DocsConfig) -> str:
    """
    Expose shared values to every template, and return the citry version.

    Sets ``version`` and ``site_name`` as Citry template globals, so a page can
    write ``{{ version }}`` or ``{{ site_name }}`` directly (the docs site
    dogfoods Citry's global-variables feature instead of a dedicated tag).
    """
    version = _citry_version()
    default_citry.template_globals.update({
        "version": version,
        "site_name": config.site_name,
    })
    return version


def _is_unsafe_output(output_dir: Path, content_dir: Path, config: DocsConfig) -> bool:
    """The output dir is cleared, so refuse the repo root, content dir, or a filesystem root."""
    resolved = output_dir.resolve()
    unsafe = {config.repo_root.resolve(), content_dir.resolve(), Path(resolved.anchor)}
    return resolved in unsafe


def _copy_non_markdown_assets(content_dir: Path, output_dir: Path) -> None:
    """Copy images and other non-``.md`` content files into the output tree verbatim."""
    for asset in content_dir.rglob("*"):
        if asset.is_dir() or asset.suffix == ".md" or asset.name == "_nav.yml":
            continue
        dest = output_dir / asset.relative_to(content_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, dest)


def _copy_static_assets(config: DocsConfig, output_dir: Path) -> None:
    """Copy the site's static assets (CSS, JS, fonts, images) into ``<output>/static``."""
    static_dir = config.base_dir / "static"
    if static_dir.is_dir():
        shutil.copytree(static_dir, output_dir / "static", dirs_exist_ok=True)


def _build_reference(
    output_dir: Path, config: DocsConfig, nav_tree: NavTree, version: str, canonical_base: str
) -> list[PageRecord]:
    """Generate and render the API-reference pages (the index plus one per category)."""
    records: list[PageRecord] = []

    def write(page_url: str, source: str) -> None:
        canonical = f"{canonical_base}/{page_url}" if canonical_base else ""
        result = render_page(
            source, config=config, canonical=canonical, nav_tree=nav_tree, current_path=page_url, version=version
        )
        out_path = output_dir / page_url / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result.html, encoding="utf-8")
        records.append(_record_for(page_url, canonical, result, source_md=None))

    write("reference/", reference_index_markdown())
    for cat in CATEGORIES:
        write(f"reference/{cat.slug}/", reference_page_markdown(cat))
    return records


def _build_releases(
    output_dir: Path, config: DocsConfig, nav_tree: NavTree, version: str, canonical_base: str
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
    releases = parse_changelog(changelog.read_text(encoding="utf-8"))
    write("releases/", release_index_markdown(releases))
    for release in releases:
        write(f"releases/{release.slug}/", release_page_markdown(release))
    return records


def _build_not_found(output_dir: Path, config: DocsConfig, nav_tree: NavTree, version: str) -> bool:
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
        '<a href="https://github.com/citry-dev/citry/issues" target="_blank" rel="noopener">'
        "open an issue</a> and we will fix the link.\n"
    )
    html = render_page(
        source, config=config, canonical="", nav_tree=nav_tree, current_path="404", version=version
    ).html
    (output_dir / "404.html").write_text(html, encoding="utf-8")
    return True


def _pre_render_examples(output_dir: Path) -> int:
    """Render each example's standalone page (and any fragment variants) to static files."""
    count = 0
    for name, info in get_example_registry().items():
        out_path = output_dir / "examples" / name / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(str(info.page_cls()), encoding="utf-8")
        count += 1
        # A fragment demo: pre-render each variant as an HTML fragment to its own
        # endpoint, and write the fragment component's dep files so the client
        # runtime can load its JS/CSS on the static site (see export_fragment_deps).
        for variant, comp_cls in info.fragments.items():
            variant_path = output_dir / "examples" / name / variant / "index.html"
            variant_path.parent.mkdir(parents=True, exist_ok=True)
            variant_path.write_text(comp_cls().render().serialize(deps_strategy="fragment"), encoding="utf-8")
            export_fragment_deps(output_dir, comp_cls)
            count += 1
    return count
