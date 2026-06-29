"""
The page-rendering pipeline: markdown source in, full HTML page out.

The upstream django-components site renders each page in three passes:

    Pass 1: expand authoring directives in the markdown ({% example %}, ...)
    Pass 2: convert markdown to HTML (python-markdown + pymdownx extensions)
    Pass 3: wrap the content HTML in the page layout

This module ports passes 2 and 3, which are the core of a working page: the
markdown conversion (Django-independent, copied as-is from upstream) and the
``DocPage`` layout wrap (a Citry component). Pass 1 - the Citry rewrite of the
authoring directives, including the live ``<c-example>`` widget - is added in
the next step, alongside fence protection.

The markdown extension set and its config are copied verbatim from the upstream
site: they plug into python-markdown directly and never depended on Django.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import markdown

from docs_site.components.doc_page import DocPage
from docs_site.config import DocsConfig
from docs_site.config import config as default_config
from docs_site.directives import expand_directives
from docs_site.fence_protection import protect_fences
from docs_site.frontmatter import parse_page

if TYPE_CHECKING:
    from docs_site.nav import NavTree

# Markdown extension set, copied verbatim from the upstream docs site. These
# plug into python-markdown directly and do not depend on Django or mkdocs.
MD_EXTENSIONS = [
    "abbr",
    "admonition",
    "attr_list",
    "def_list",
    "tables",
    "md_in_html",  # lets block-level HTML from Pass 1 pass through Pass 2 untouched
    "toc",
    "pymdownx.details",
    "pymdownx.highlight",
    "pymdownx.inlinehilite",
    "pymdownx.magiclink",  # bare-URL autolinking + #123 / user/repo issue shorthand
    "pymdownx.snippets",  # --8<-- "path" file inclusion
    "pymdownx.superfences",
    "pymdownx.tabbed",
    "pymdownx.tasklist",
]

MD_EXTENSION_CONFIGS: dict[str, dict[str, Any]] = {
    # Line-number anchors stay off: they would emit an empty <a> per code line
    # (no visible benefit, and a Lighthouse a11y failure for unnamed links).
    "pymdownx.highlight": {"anchor_linenums": False},
    "pymdownx.magiclink": {
        "repo_url_shorthand": True,
        "user": "JuroOravec",
        "repo": "citry",
    },
    "pymdownx.tabbed": {"alternate_style": True},
    "pymdownx.tasklist": {"custom_checkbox": True},
    "toc": {"permalink": "¤"},
}


@dataclass
class RenderResult:
    """The output of rendering one page."""

    html: str
    toc_tokens: list


def render_page(
    source: str,
    *,
    config: DocsConfig | None = None,
    canonical: str = "",
    nav_tree: NavTree | None = None,
    current_path: str = "",
    version: str = "",
    wrap_in_layout: bool = True,
) -> RenderResult:
    """
    Render markdown ``source`` to a full HTML page (front matter + passes 2-3).

    ``canonical`` is the page's canonical URL and ``current_path`` its clean URL
    (front matter's canonical wins when set). ``nav_tree`` drives the sidebar,
    breadcrumbs, and prev/next; without it the chrome renders with an empty nav.
    With ``wrap_in_layout=False`` only the content HTML is returned, without the
    surrounding ``DocPage`` document.
    """
    config = config or default_config

    meta = parse_page(source)
    # Pass 0: protect code so the citry render leaves it literal.
    protected = protect_fences(meta.body)
    # Pass 1: render the body as a citry template, expanding authoring directives.
    expanded = expand_directives(protected, context={"current_path": current_path})
    # Pass 2: convert the expanded markdown to HTML.
    content_html, toc_tokens = _pass2_markdown(expanded, config=config)

    if not wrap_in_layout:
        return RenderResult(html=content_html, toc_tokens=toc_tokens)

    # The layout adds an <h1> from the title only when the content lacks one.
    content_has_h1 = any(token.get("level") == 1 for token in toc_tokens)

    page_html = str(
        DocPage(
            content_html=content_html,
            title=meta.title,
            description=meta.description,
            canonical=meta.canonical or canonical,
            noindex=meta.noindex,
            content_has_h1=content_has_h1,
            site_name=config.site_name,
            version=version,
            nav_tree=nav_tree,
            current_path=current_path,
            toc_items=toc_tokens,
        )
    )
    return RenderResult(html=page_html, toc_tokens=toc_tokens)


def _pass2_markdown(source: str, *, config: DocsConfig) -> tuple[str, list]:
    """Convert markdown to HTML; also return python-markdown's TOC tokens."""
    configs = {
        **MD_EXTENSION_CONFIGS,
        # `--8<-- "path"` includes resolve against the repo root ONLY (matching
        # upstream). Adding the source file's own dir would, on a
        # case-insensitive filesystem, let a root-relative include resolve to
        # the including page itself and silently produce an empty page.
        "pymdownx.snippets": {"check_paths": True, "base_path": [str(config.repo_root)]},
    }
    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=configs)
    html = md.convert(source)
    toc_tokens = getattr(md, "toc_tokens", [])
    return html, toc_tokens
