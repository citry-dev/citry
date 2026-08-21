"""
The page-rendering pipeline: markdown source in, full HTML page out.

The upstream django-components site renders each page in three passes:

    Pass 1: expand the custom ``<c-*>`` tags (``<c-example>``, ``<c-image>``,
            ``<c-docstring>``, ...) and bare ``{{ ... }}`` expressions
    Pass 2: convert markdown to HTML (python-markdown + pymdownx extensions)
    Pass 3: wrap the content HTML in the page layout

This module runs all three. Pass 1 is ``render_content`` (below): it renders the
markdown body as a Citry template so the custom tags (each a small component under
``components/``) turn into HTML, after fence protection. Passes 2 and 3 are the
Markdown conversion and the ``DocPage`` layout wrap (a Citry component).

Maintainers select and configure ordinary Python-Markdown extensions in
``settings.yml``. The pipeline adds its capture and table wrappers, and supplies
checkout-specific snippet and repository options at runtime.
"""

from __future__ import annotations

import itertools
from contextlib import nullcontext
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree as ET

import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor

import pygments_citry  # noqa: F401  (registers the `citry` fence lexer at build startup; migration item 1.5)
from citry import Component
from citry import citry as default_citry
from docs_site._internal.blog import (
    BlogCatalog,
    BlogPost,
    project_blog_list_for_text,
    use_blog_catalog,
)

# The custom <c-*> tags each register on import; importing them lets
# render_content resolve <c-example>, <c-image>, <c-docstring>, <c-builtin>,
# <c-include-file>, <c-people>, <c-search-modal>, and <c-version-picker> by name.
from docs_site._internal.components import (  # noqa: F401
    blog,
    builtin,
    diagnostic_catalog,
    docstring,
    example_card,
    image,
    include_file,
    landing,
    landing_composer,
    live_code,
    people,
    search_modal,
    social_links,
    ui_demo,
    ui_library,
    version_picker,
)
from docs_site._internal.components.doc_page import DocPage
from docs_site._internal.crossrefs import resolve_crossrefs_in_prose
from docs_site._internal.examples import project_examples_for_text
from docs_site._internal.fence_protection import protect_fences, restore_protected_code
from docs_site._internal.frontmatter import PageMeta, parse_page
from docs_site._internal.git_metadata import edit_url_for, get_page_git_meta, is_excluded
from docs_site._internal.links import (
    linkify_headings,
    project_internal_html_urls,
    project_internal_markdown_urls,
    project_markdown_base_path,
    rewrite_internal_md_links,
    rewrite_internal_md_links_in_markdown,
)
from docs_site._internal.live_code import LiveCodeContext, use_live_code_context
from docs_site._internal.live_code_projection import project_live_code_for_text
from docs_site._internal.project import (
    DocsProject,
    docs_project_scope,
    load_docs_project,
    materialize_markdown_configs,
)
from docs_site._internal.settings import google_search_site_target
from docs_site._internal.toc import merge_html_headings_into_toc
from docs_site._internal.ui_previews import (
    UiPreviewRenderContext,
    project_ui_previews_for_text,
    use_ui_preview_context,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from citry import Citry
    from docs_site._internal.config import DocsConfig
    from docs_site._internal.nav import NavTree


@dataclass
class RenderResult:
    """The output of rendering one page."""

    html: str
    toc_tokens: list
    # The parsed front matter (title, description, canonical, noindex). The
    # build reads these to assemble the sitemap, robots, and llms files without
    # re-parsing the page.
    meta: PageMeta | None = None
    # The page body as markdown after custom <c-*> tags and --8<-- snippet
    # includes were expanded. This is the plain-text form the llms-full.txt
    # full-text export concatenates.
    markdown_body: str = ""


class _CaptureExpandedMarkdown(Preprocessor):
    """Capture Markdown immediately after the snippets preprocessor runs."""

    def __init__(self, captured: list[str]) -> None:
        super().__init__()
        self._captured = captured

    def run(self, lines: list[str]) -> list[str]:
        """Save the snippet-expanded lines without changing the HTML pass."""
        self._captured[:] = ["\n".join(lines)]
        return lines


class _CaptureExpandedMarkdownExtension(Extension):
    """Install the capture between snippets and Markdown normalization."""

    def __init__(self, captured: list[str]) -> None:
        super().__init__()
        self._captured = captured

    def extendMarkdown(self, md: markdown.Markdown) -> None:  # noqa: N802 - Python-Markdown API
        """Register the capture at the required preprocessor priority."""
        md.registerExtension(self)
        # pymdownx.snippets runs at 32 and normalize_whitespace at 30. Capturing
        # at 31 records exactly the Markdown the snippets pass produced, while
        # the same preprocessor run continues into HTML conversion. This avoids
        # a second snippets pass, which would incorrectly expand escaped markers.
        md.preprocessors.register(_CaptureExpandedMarkdown(self._captured), "capture_expanded_markdown", 31)


class _WrapTables(Treeprocessor):
    """Give Markdown tables a bounded horizontal-scroll container."""

    def run(self, root: ET.Element) -> ET.Element:
        self._wrap_children(root)
        return root

    def _wrap_children(self, parent: ET.Element) -> None:
        for index, child in enumerate(list(parent)):
            if child.tag == "table":
                wrapper = ET.Element(
                    "div",
                    {
                        "class": "table-wrapper",
                        "tabindex": "0",
                    },
                )
                parent.remove(child)
                wrapper.append(child)
                parent.insert(index, wrapper)
                continue

            self._wrap_children(child)


class _WrapTablesExtension(Extension):
    """Install the table wrapper after Markdown has built its element tree."""

    def extendMarkdown(self, md: markdown.Markdown) -> None:  # noqa: N802 - Python-Markdown API
        md.registerExtension(self)
        md.treeprocessors.register(_WrapTables(md), "wrap_tables", 1)


# A fresh content-component class per render gets a unique registered name, so
# concurrent or repeated renders never collide; it is unregistered right after.
_content_counter = itertools.count()


def render_content(
    body: str,
    *,
    citry_instance: Citry | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    """
    Render ``body`` as a Citry template, expanding the custom ``<c-*>`` tags.

    This is Pass 1: the ``<c-example>`` / ``<c-image>`` / ``<c-docstring>`` tags
    and bare ``{{ ... }}`` expressions turn into HTML before the markdown pass.
    ``body`` should already have its code protected (see
    ``fence_protection.protect_fences``); ``context`` supplies any bare
    ``{{ ... }}`` values the page uses (for example ``{{ version }}``).
    """
    citry_instance = citry_instance or default_citry
    page_context = context or {}

    class DocsContent(Component):
        citry = citry_instance
        name = f"docs-content-{next(_content_counter)}"
        transparent = True
        template = body

        class Kwargs:
            pass

        class Slots:
            pass

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, Any]:
            return page_context

    try:
        return str(DocsContent())
    finally:
        citry_instance.unregister(DocsContent)


def _content_rel(source_path: Path, config: DocsConfig) -> Path | None:
    """The source file's path relative to the content dir, or None if it is outside."""
    try:
        return source_path.relative_to(config.content_dir)
    except ValueError:
        return None


@docs_project_scope
def render_page(
    source: str,
    *,
    config: DocsConfig | None = None,
    canonical: str = "",
    nav_tree: NavTree | None = None,
    current_path: str = "",
    version: str = "",
    wrap_in_layout: bool = True,
    source_path: Path | None = None,
    run_citry_pass: bool = True,
    blog_catalog: BlogCatalog | None = None,
    blog_post: BlogPost | None = None,
    is_blog_index: bool = False,
    blog_feed_url: str = "",
    version_prefix: str = "",
    source_to_public_path: Mapping[Path, str] | None = None,
    allow_citry_ui: bool = True,
    project: DocsProject | None = None,
) -> RenderResult:
    """
    Render markdown ``source`` to a full HTML page (front matter + passes 2-3).

    ``canonical`` is the page's canonical URL and ``current_path`` its clean URL
    (front matter's canonical wins when set). ``nav_tree`` drives the sidebar,
    breadcrumbs, and prev/next; without it the chrome renders with an empty nav.
    With ``wrap_in_layout=False`` only the content HTML is returned, without the
    surrounding ``DocPage`` document. ``source_path`` is the page's source file;
    when given, its git history supplies the footer's created/last-updated dates,
    the recent authors, and the "edit on GitHub" link (generated pages pass none).
    With ``run_citry_pass=False`` the citry template pass is skipped, so a page
    whose prose *shows* citry syntax in code spans (the release notes, built from
    CHANGELOG.md) renders it as literal code instead of executing it. Such a page
    relies on its source backticking tags and expressions (the changelog does):
    a bare, unbackticked ``<tag>`` would reach the markdown pass as raw HTML.
    """
    if project is None:  # pragma: no cover - supplied by @docs_project_scope
        raise RuntimeError("docs project scope was not initialized")
    settings = project.settings
    has_live_code = False
    has_interactive_live_code = False

    meta = parse_page(source)
    if blog_post is not None:
        # Blog metadata has already passed the catalog's strict YAML-scalar
        # parser. Keep that canonical model authoritative through rendering and
        # output records; the generic docs parser intentionally supports a much
        # smaller front-matter dialect and would otherwise preserve YAML escape
        # characters in quoted titles and descriptions.
        meta = PageMeta(
            title=blog_post.title,
            description=blog_post.description,
            noindex=blog_post.noindex,
            og_image=blog_post.og_image,
            searchable=blog_post.searchable,
            boost=blog_post.boost,
            body=blog_post.body,
        )
    if run_citry_pass:
        # Pass 0: protect code so the citry render leaves it literal.
        protected = protect_fences(meta.body)
        # Pass 1: render the body as a citry template, expanding the custom <c-*> tags.
        catalog_context = use_blog_catalog(blog_catalog) if blog_catalog is not None else nullcontext()
        live_state = LiveCodeContext(
            config=config,
            source_path=source_path,
            interactive=not bool(version_prefix),
            allow_citry_ui=allow_citry_ui,
        )
        live_context = use_live_code_context(live_state)
        ui_preview_state = UiPreviewRenderContext(
            config=config,
            catalog=project.ui_library,
            source_path=source_path,
            current_path=current_path,
            version_prefix=version_prefix,
        )
        ui_preview_context = use_ui_preview_context(ui_preview_state)
        repository = settings.repository
        render_context = {
            "current_path": current_path,
            "site_name": settings.name,
            "repo_url": repository.url,
            "repo_full_name": repository.full_name,
            "repo_edit_branch": repository.edit_branch,
            "repo_issues_url": repository.issues_url,
            "repo_sponsors_url": repository.sponsors_url,
            "pypi_url": settings.pypi_url,
            "discord_url": settings.discord_url,
        }
        if version:
            render_context["version"] = version
        with catalog_context, live_context, ui_preview_context:
            expanded = restore_protected_code(render_content(protected, context=render_context))
        has_live_code = live_state.has_live_code
        has_interactive_live_code = live_state.has_interactive
    else:
        # A page that shows citry syntax as text (release notes) skips the citry
        # pass; its `<c-raw>`/`{{ ... }}` are then rendered as literal code by the
        # markdown pass rather than being parsed and executed as a template.
        expanded = meta.body
    # Resolve [text][symbol] cross-refs to reference links (skips fenced code).
    expanded, _unresolved = resolve_crossrefs_in_prose(expanded)
    # Pass 2: expand --8<-- snippets and convert the Markdown to HTML. Capture
    # the post-snippet Markdown from that same preprocessor run for companions
    # and llms-full.txt; running snippets twice would break escaped markers.
    content_html, toc_tokens, expanded = _pass2_markdown_with_expanded_source(
        expanded,
        config=config,
        project=project,
    )
    # Keep the interactive card in browser HTML, but give Markdown companions
    # and llms-full a concise source-first view derived from the same files.
    expanded = project_examples_for_text(expanded)
    expanded = project_live_code_for_text(
        expanded,
        repo_root=config.repo_root,
        allow_citry_ui=allow_citry_ui,
    )
    expanded = project_ui_previews_for_text(expanded, repo_root=config.repo_root)
    if blog_catalog is not None:
        expanded = project_blog_list_for_text(expanded, blog_catalog)
    # Rewrite internal `.md` links (e.g. ./other.md -> ../other/) so they resolve
    # under the clean-URL scheme. Generated pages (source_path=None) have no source
    # file to resolve against and pass through untouched. Runs before the branch
    # below so both the wrapped and the content-only return are rewritten.
    if source_path is not None:
        routes = source_to_public_path
        if routes is None and blog_catalog is not None:
            routes = blog_catalog.source_to_public_path
        content_html = rewrite_internal_md_links(
            content_html,
            source_path=source_path,
            content_dir=config.content_dir,
            current_public_path=current_path,
            source_to_public_path=routes,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )
        expanded = rewrite_internal_md_links_in_markdown(
            expanded,
            source_path=source_path,
            content_dir=config.content_dir,
            current_public_path=current_path,
            source_to_public_path=routes,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )
    elif version_prefix:
        content_html = project_internal_html_urls(
            content_html,
            current_public_path=current_path,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )
        expanded = project_internal_markdown_urls(
            expanded,
            current_public_path=current_path,
            nav_tree=nav_tree,
            version_prefix=version_prefix,
        )
    # Markdown companions and llms-full.txt are deployed beneath the same base
    # path as HTML. Root-relative destinations therefore need the prefix too.
    expanded = project_markdown_base_path(expanded, config.base_path)
    # The API-reference symbol headings are injected as raw HTML, so the markdown
    # TOC pass never saw them; fold them in from the rendered HTML.
    toc_tokens = merge_html_headings_into_toc(content_html, toc_tokens)
    # Make each heading's text a permalink to itself (the ¤ icon stays). The TOC
    # pass above already read the original headings, so this only affects display.
    content_html = linkify_headings(content_html)

    if not wrap_in_layout:
        return RenderResult(html=content_html, toc_tokens=toc_tokens, meta=meta, markdown_body=expanded)

    # The layout adds an <h1> from the title only when the content lacks one.
    content_has_h1 = any(token.get("level") == 1 for token in toc_tokens)

    # Git-derived footer dates + the "edit on GitHub" link, for pages that come
    # from a committed source file. Generated pages (source_path=None) get none.
    created = last_updated = None
    authors: list[str] = []
    edit_url = ""
    if source_path is not None:
        edit_url = edit_url_for(
            config.repo_root,
            source_path,
            repo_url=settings.repository.url,
            edit_branch=settings.repository.edit_branch,
        )
        content_rel = _content_rel(source_path, config)
        if blog_post is None and (content_rel is None or not is_excluded(content_rel, settings.git.exclude_patterns)):
            git_meta = get_page_git_meta(config.repo_root, source_path)
            created, last_updated, authors = git_meta.created, git_meta.last_updated, list(git_meta.authors)

    blog_newer = blog_older = None
    if blog_catalog is not None and blog_post is not None:
        blog_newer, blog_older = blog_catalog.neighbors(blog_post)

    page_html = str(
        DocPage(
            content_html=content_html,
            title=meta.title,
            # Third fallback tier: a page with no front-matter description and no
            # usable first paragraph still gets the site-level default here (the
            # earlier tiers are resolved in parse_page, which has no config).
            description=meta.description or settings.default_description,
            canonical=meta.canonical or canonical,
            noindex=meta.noindex,
            content_has_h1=content_has_h1,
            site_name=settings.name,
            site_url=project.site_url,
            base_path=config.base_path,
            google_site_verification=config.google_site_verification,
            og_image=meta.og_image,
            searchable=meta.searchable,
            boost=meta.boost,
            version=version,
            nav_tree=nav_tree,
            current_path=current_path,
            toc_items=toc_tokens,
            created=created,
            last_updated=last_updated,
            authors=authors,
            edit_url=edit_url,
            blog_post=blog_post,
            blog_newer=blog_newer,
            blog_older=blog_older,
            is_blog_index=is_blog_index,
            blog_feed_url=blog_feed_url,
            page_scope=nav_tree.scope_for_url(current_path) if nav_tree is not None else "versioned",
            version_prefix=version_prefix,
            layout=meta.layout,
            has_live_code=has_live_code,
            has_interactive_live_code=has_interactive_live_code,
            lang=settings.language,
            repo_url=settings.repository.url,
            pypi_url=settings.pypi_url,
            discord_url=settings.discord_url,
            search_quick_links=list(settings.quick_links),
            pagefind_path=settings.pagefind_path,
            search_site_target=google_search_site_target(project.site_url),
        )
    )
    return RenderResult(html=page_html, toc_tokens=toc_tokens, meta=meta, markdown_body=expanded)


def _pass2_markdown(source: str, *, config: DocsConfig, project: DocsProject | None = None) -> tuple[str, list]:
    """Convert Markdown to HTML; also return Python-Markdown's TOC tokens."""
    project = project or load_docs_project(config)
    html, toc_tokens, _expanded = _pass2_markdown_with_expanded_source(source, config=config, project=project)
    return html, toc_tokens


def _pass2_markdown_with_expanded_source(
    source: str,
    *,
    config: DocsConfig,
    project: DocsProject | None = None,
) -> tuple[str, list, str]:
    """Convert Markdown and return HTML, TOC tokens, and snippet-expanded source."""
    project = project or load_docs_project(config)
    settings = project.settings
    configs = materialize_markdown_configs(settings.markdown_pages, settings=settings)
    # `--8<-- "path"` includes resolve against the repo root ONLY (matching
    # upstream). Adding the source file's own dir would, on a case-insensitive
    # filesystem, let a root-relative include resolve to the including page
    # itself and silently produce an empty page. Preserve all ordinary
    # maintainer-owned options and override only these runtime-owned values.
    configs.setdefault("pymdownx.snippets", {}).update(
        check_paths=True,
        base_path=[str(config.repo_root)],
    )
    captured: list[str] = []
    md = markdown.Markdown(
        extensions=[
            *settings.markdown_pages.extensions,
            _CaptureExpandedMarkdownExtension(captured),
            _WrapTablesExtension(),
        ],
        extension_configs=configs,
    )
    # A component can render a <button> that wraps block content, which is valid
    # HTML. Markdown otherwise treats the tag as span-level, ends the raw HTML
    # block there, and wraps everything after it in stray paragraph tags.
    md.block_level_elements.append("button")
    html = md.convert(source)
    toc_tokens = getattr(md, "toc_tokens", [])
    # Markdown.convert returns early for blank input, before preprocessors run.
    expanded_source = captured[0] if captured else source
    return html, toc_tokens, expanded_source
