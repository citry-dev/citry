"""
``DocPage`` - the document page layout, as a Citry component.

Wraps rendered content HTML in a complete page: a ``<head>`` with title and SEO
metadata, a sticky header (logo, nav, theme picker), a left sidebar built from
the navigation tree, the content article (with breadcrumbs, an injected title
when the page has no H1, and prev/next links), a right-rail table of contents,
and a footer. ``<c-css>`` / ``<c-js>`` mark where Citry places the CSS and JS
collected from the components used on the page.

The chrome keeps the upstream ``djc-*`` class names so the ported ``site.css``
and ``site.js`` (theme picker, sidebar drawer, resize handles, scroll-spy TOC,
back-to-top) work unchanged. Still to port: the search modal, the version
picker, JSON-LD structured data, and the mobile overflow menu.

Django template filters from the original have moved into ``template_data``:
loop-position flags (the breadcrumb tail), date formatting, and joins are
computed in Python, since Citry expressions read plain values.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit

from markupsafe import Markup

from citry import Component
from docs_site._internal.components.brand import CitryMark  # noqa: F401
from docs_site._internal.components.landing import LandingPage  # noqa: F401
from docs_site._internal.components.playground_workspace import PlaygroundWorkspace  # noqa: F401
from docs_site._internal.nav import SCOPE_VERSIONED
from docs_site._internal.project import current_docs_project
from docs_site._internal.settings import google_search_site_target

if TYPE_CHECKING:
    from datetime import datetime

    from docs_site._internal.blog import BlogPost
    from docs_site._internal.nav import NavArea, NavTree

# Site-level social-card image used when a page sets no og_image of its own.
_DEFAULT_OG_IMAGE_PATH = "/static/img/favicon.png"

_REVIEW_HINT = "This page has not completed final human review. May contain minor inaccuracies."


class TocItems(Component):
    """Recursive, level-aware list used by the desktop and mobile page TOCs."""

    transparent = True

    class Kwargs:
        items: list
        mobile: bool = False
        nested: bool = False

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "items": kwargs.items,
            "mobile": kwargs.mobile,
            "list_class": "djc-toc__sublist" if kwargs.nested else "djc-toc__list",
            "item_class": "djc-toc__subitem" if kwargs.nested else "djc-toc__item",
        }

    template = """
      <ul c-class="list_class">
        <li
          c-for="item in items"
          c-class="[item_class, {'djc-toc__item--collapsible': item.collapsible and not mobile}]"
        >
          <span c-class="['djc-toc__row', item.level_class]">
            <c-if cond="item.collapsible and not mobile">
              <button
                type="button"
                class="djc-toc__toggle"
                aria-expanded="false"
                c-aria-label="'Toggle members of ' + item.name"
              ></button>
            </c-if>
            <c-if cond="item.kind">
              <span c-class="'doc-symbol doc-symbol-' + item.kind"></span>
            </c-if>
            <a
              class="djc-toc__link"
              c-href="'#' + item.id"
            >
              {{ item.name }}
            </a>
          </span>
          <c-TocItems
            c-if="item.children"
            c-items="item.children"
            c-mobile="mobile"
            c-nested="True"
          />
        </li>
      </ul>
    """


class SidebarNavLink(Component):
    """One page link with optional review state and publication date."""

    transparent = True

    class Kwargs:
        item: Any
        top: bool = False

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        needs_review = bool(kwargs.item.needs_review)
        return {
            "item": kwargs.item,
            "top": kwargs.top,
            "needs_review": needs_review,
            "review_hint": _REVIEW_HINT,
            "aria_label": f"{kwargs.item.title}. {_REVIEW_HINT}" if needs_review else None,
        }

    template = """
      <a
        c-class="[
          'djc-sidebar__link',
          {
            'djc-sidebar__link--top': top,
            'is-active': item.active,
          },
        ]"
        c-href="item.path"
        c-aria-label="aria_label"
      >
        <span
          c-if="needs_review"
          class="djc-sidebar__review-icon"
          aria-hidden="true"
        >🚧</span>
        <span>{{ item.title }}</span>
        <time
          c-if="item.date_iso"
          class="djc-sidebar__date"
          c-datetime="item.date_iso"
        >
          {{ item.date_label }}
        </time>
        <span
          c-if="needs_review"
          class="djc-sidebar__review-hint"
          aria-hidden="true"
        >
          {{ review_hint }}
        </span>
      </a>
    """


class DocPage(Component):
    """Full-document layout: head, header, sidebar, content, TOC, footer."""

    class Kwargs:
        # Already-rendered content HTML (trusted: our own pipeline output).
        content_html: str
        title: str = ""
        description: str = ""
        canonical: str = ""
        noindex: bool = False
        # Whether the content already has an <h1> (else the title becomes one).
        content_has_h1: bool = False
        version: str = ""
        lang: str = "en"
        site_name: str = "Citry"
        # The navigation tree (docs_site._internal.nav.NavTree) or None for a bare render.
        nav_tree: Any = None
        # This page's clean URL, e.g. "concepts/components/" (drives active state).
        current_path: str = ""
        # python-markdown's raw toc tokens; flattened into the right-rail TOC.
        toc_items: list | None = None
        # Footer "last updated" date and first-commit date (both datetimes), plus
        # author names. The dates also feed the article structured data.
        last_updated: Any = None
        created: Any = None
        authors: list | None = None
        # Front-matter social-card image (resolved to a URL with the site default).
        og_image: str = ""
        # The public site URL, used to build absolute structured-data links and
        # to strip the site's base path from the breadcrumb trail.
        site_url: str = ""
        # A subpath prefix for a project-Pages deploy (e.g. "/citry"), emitted as
        # a meta tag so the search script can prefix result links. Usually empty.
        base_path: str = ""
        # Google Search Console ownership token; when set, rendered as a
        # <meta name="google-site-verification"> in the head.
        google_site_verification: str = ""
        # Whether this page is indexed for search (the 404 page opts out) and an
        # optional search-ranking boost (1.0 is the neutral default).
        searchable: bool = True
        boost: float = 1.0
        edit_url: str = ""
        # Blog pages reuse the document shell but replace git-derived article
        # metadata and generic previous/next navigation with editorial data.
        blog_post: Any = None
        blog_newer: Any = None
        blog_older: Any = None
        is_blog_index: bool = False
        blog_feed_url: str = ""
        # Declarative build scope and the mount prefix used by frozen snapshots.
        page_scope: str = SCOPE_VERSIONED
        version_prefix: str = ""
        # Narrative docs pages use the complete three-column chrome. The
        # playground keeps only the shared header and owns the viewport below.
        layout: str = "docs"
        # Set by the render-scoped live-code collector, never inferred from prose.
        has_live_code: bool = False
        has_interactive_live_code: bool = False
        repo_url: str = ""
        pypi_url: str = ""
        discord_url: str = ""
        search_quick_links: list | None = None
        pagefind_path: str = "/pagefind/pagefind.js"
        search_site_target: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        settings = current_docs_project().settings
        title = kwargs.title
        is_playground = kwargs.layout == "playground"
        is_landing = kwargs.layout == "landing"
        has_live_code = kwargs.has_live_code
        has_interactive_live_code = kwargs.has_interactive_live_code
        site_name = kwargs.site_name
        page_title = f"{title} - {site_name}" if title and title != site_name else site_name

        nav_sections: list[SimpleNamespace] = []
        breadcrumbs: list[SimpleNamespace] = []
        prev_page = next_page = None
        nav_tree: NavTree | None = kwargs.nav_tree
        top_nav_items: list[SimpleNamespace] = []
        if nav_tree is not None:
            nav_tree.set_active(kwargs.current_path)
            active_area = nav_tree.find_area(kwargs.current_path)
            top_nav_items = _build_top_nav_view(
                nav_tree,
                kwargs.current_path,
                kwargs.version_prefix,
            )
            nav_sections = _build_nav_view(active_area, nav_tree, kwargs.version_prefix)
            breadcrumbs = _build_breadcrumbs(nav_tree, kwargs.current_path, kwargs.version_prefix)
            if not (kwargs.blog_post or kwargs.is_blog_index):
                prev_page, next_page = nav_tree.find_prev_next(kwargs.current_path)
                prev_page = _project_nav_item(prev_page, nav_tree, kwargs.version_prefix)
                next_page = _project_nav_item(next_page, nav_tree, kwargs.version_prefix)

        toc_items = _flatten_toc(kwargs.toc_items or [])
        last_updated = kwargs.last_updated.strftime("%-d %b %Y") if kwargs.last_updated else ""

        # Structured data (JSON-LD): a breadcrumb trail on any page with a
        # canonical URL, plus an article description on content pages (the home
        # page has no path segments, so it gets neither).
        breadcrumb_jsonld = ""
        if not is_playground and kwargs.current_path.strip("/") and kwargs.canonical and breadcrumbs:
            breadcrumb_jsonld = _build_breadcrumb_jsonld(
                kwargs.canonical,
                breadcrumbs,
                kwargs.site_url,
            )
        article_jsonld = ""
        og_image = _resolve_og_image(kwargs.og_image, kwargs.site_url)
        blog_author_meta = (
            _resolve_blog_author_url(
                kwargs.blog_post.author_url,
                kwargs.canonical,
                kwargs.blog_post.public_path,
            )
            if kwargs.blog_post and kwargs.blog_post.author_url
            else (kwargs.blog_post.author if kwargs.blog_post else "")
        )
        if not is_playground and kwargs.current_path.strip("/") and kwargs.canonical and title:
            if kwargs.blog_post:
                article_jsonld = _build_blog_posting_jsonld(
                    canonical=kwargs.canonical,
                    post=kwargs.blog_post,
                    image=og_image,
                    site_name=site_name,
                )
            else:
                article_jsonld = _build_article_jsonld(
                    canonical=kwargs.canonical,
                    title=title,
                    description=kwargs.description,
                    created=kwargs.created,
                    last_updated=kwargs.last_updated,
                    site_name=site_name,
                )

        # Emit data-pagefind-weight only when the page is boosted; the neutral
        # default (1.0) leaves it off so Pagefind uses its own default. None omits
        # the attribute entirely.
        pagefind_weight = str(kwargs.boost) if kwargs.boost != 1.0 else None

        return {
            "lang": kwargs.lang,
            "is_playground": is_playground,
            "is_landing": is_landing,
            "has_live_code": has_live_code,
            "has_interactive_live_code": has_interactive_live_code,
            "page_title": page_title,
            "base_path": kwargs.base_path,
            "searchable": kwargs.searchable,
            "pagefind_weight": pagefind_weight,
            "title": title,
            "description": kwargs.description,
            "canonical": kwargs.canonical,
            "robots": "noindex,follow" if kwargs.noindex else "index,follow",
            "version": kwargs.version,
            "site_name": site_name,
            "og_type": "website" if is_playground else "article",
            "og_image": og_image,
            "breadcrumb_jsonld": Markup(breadcrumb_jsonld) if breadcrumb_jsonld else "",  # noqa: S704 - escaped for <script>
            "article_jsonld": Markup(article_jsonld) if article_jsonld else "",  # noqa: S704 - escaped for <script>
            "edit_url": kwargs.edit_url,
            "repo_url": kwargs.repo_url or settings.repository.url,
            "pypi_url": kwargs.pypi_url or settings.pypi_url,
            "discord_url": kwargs.discord_url or settings.discord_url,
            "google_site_verification": kwargs.google_site_verification,
            "top_nav_items": top_nav_items,
            "nav_sections": nav_sections,
            "breadcrumbs": breadcrumbs,
            "prev_page": prev_page,
            "next_page": next_page,
            "toc_items": toc_items,
            # Add an <h1> from the title only when the content brings none.
            "inject_title": bool(title) and not kwargs.content_has_h1 and not kwargs.blog_post,
            "content_html": Markup(kwargs.content_html),  # noqa: S704 - trusted pipeline output
            "last_updated": last_updated,
            "authors": ", ".join(kwargs.authors) if kwargs.authors else "",
            "show_version_picker": kwargs.page_scope == SCOPE_VERSIONED and not is_playground,
            "blog_feed_url": kwargs.blog_feed_url,
            "blog_post": kwargs.blog_post,
            "blog_author": kwargs.blog_post.author if kwargs.blog_post else "",
            "blog_author_url": kwargs.blog_post.author_url if kwargs.blog_post else "",
            "blog_author_meta": blog_author_meta,
            "blog_published_iso": kwargs.blog_post.published.isoformat() if kwargs.blog_post else "",
            "blog_published_label": _format_blog_date(kwargs.blog_post.published) if kwargs.blog_post else "",
            "blog_updated_iso": kwargs.blog_post.updated.isoformat()
            if kwargs.blog_post and kwargs.blog_post.updated
            else "",
            "blog_updated_label": _format_blog_date(kwargs.blog_post.updated)
            if kwargs.blog_post and kwargs.blog_post.updated
            else "",
            "blog_reading_minutes": kwargs.blog_post.reading_minutes if kwargs.blog_post else 0,
            "blog_tags": kwargs.blog_post.tags if kwargs.blog_post else (),
            "blog_newer": _project_blog_neighbor(kwargs.blog_newer, nav_tree, kwargs.version_prefix),
            "blog_older": _project_blog_neighbor(kwargs.blog_older, nav_tree, kwargs.version_prefix),
            "blog_all_posts_path": nav_tree.project_path("/blog/", kwargs.version_prefix)
            if nav_tree is not None
            else "/blog/",
            # The header logo and the search overlay's popular-page links are
            # chrome, so DocPage projects them the same way it projects the nav:
            # inside a version snapshot they must stay in that snapshot instead
            # of jumping to the current docs.
            "home_path": nav_tree.project_path("/", kwargs.version_prefix) if nav_tree is not None else "/",
            "search_quick_links": [
                SimpleNamespace(label=link.label, path=nav_tree.project_path(link.path, kwargs.version_prefix))
                for link in (kwargs.search_quick_links or settings.quick_links)
            ]
            if nav_tree is not None
            else (kwargs.search_quick_links or settings.quick_links),
            "pagefind_path": kwargs.pagefind_path or settings.pagefind_path,
            "search_site_target": kwargs.search_site_target
            or google_search_site_target(kwargs.site_url or settings.public_url),
        }

    template = """
      <!DOCTYPE html>
      <html c-lang="lang">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>{{ page_title }}</title>
          <c-if cond="description">
            <meta name="description" c-content="description">
          </c-if>
          <c-if cond="canonical">
            <link rel="canonical" c-href="canonical">
          </c-if>
          <meta name="robots" c-content="robots">
          <meta name="generator" content="citry docs builder">
          <c-if cond="google_site_verification">
            <meta
              name="google-site-verification"
              c-content="google_site_verification"
            >
          </c-if>
          <link
            rel="alternate"
            type="text/markdown"
            href="/llms.txt"
            title="llms.txt"
          >
          <c-if cond="blog_feed_url">
            <link
              rel="alternate"
              type="application/atom+xml"
              title="Citry blog"
              c-href="blog_feed_url"
            >
          </c-if>

          <meta property="og:type" c-content="og_type">
          <meta property="og:site_name" c-content="site_name">
          <meta property="og:title" c-content="title or site_name">
          <c-if cond="description">
            <meta property="og:description" c-content="description">
          </c-if>
          <c-if cond="canonical">
            <meta property="og:url" c-content="canonical">
          </c-if>
          <meta property="og:image" c-content="og_image">
          <c-if cond="blog_post">
            <meta
              property="article:published_time"
              c-content="blog_published_iso"
            >
            <c-if cond="blog_updated_iso">
              <meta
                property="article:modified_time"
                c-content="blog_updated_iso"
              >
            </c-if>
            <meta
              property="article:author"
              c-content="blog_author_meta"
            >
            <meta
              c-for="tag in blog_tags"
              property="article:tag"
              c-content="tag"
            >
          </c-if>
          <meta name="twitter:card" content="summary_large_image">
          <meta name="twitter:title" c-content="title or site_name">
          <c-if cond="description">
            <meta name="twitter:description" c-content="description">
          </c-if>
          <meta name="twitter:image" c-content="og_image">

          <c-if cond="breadcrumb_jsonld">
            <script type="application/ld+json">
              {{ breadcrumb_jsonld }}
            </script>
          </c-if>
          <c-if cond="article_jsonld">
            <script type="application/ld+json">
              {{ article_jsonld }}
            </script>
          </c-if>

          <script>
            (function () {
              // Key matches the vendored site.js theme picker; rebranded together
              // with the rest of the djc-* hooks later.
              var t = localStorage.getItem('djc-theme');
              if (t === 'dark' || t === 'light') {
                document.documentElement.setAttribute('data-theme', t);
              }
            })();
          </script>

          <link
            rel="icon"
            type="image/svg+xml"
            href="/static/img/favicon.svg"
          >
          <link
            rel="icon"
            type="image/png"
            sizes="32x32"
            href="/static/img/favicon-32.png"
          >
          <link
            rel="icon"
            type="image/png"
            sizes="16x16"
            href="/static/img/favicon-16.png"
          >
          <link
            rel="apple-touch-icon"
            sizes="180x180"
            href="/static/img/apple-touch-icon.png"
          >
          <link rel="stylesheet" href="/static/css/tokens.css">
          <link rel="stylesheet" href="/static/css/site.css">
          <link rel="stylesheet" href="/static/css/pygments-light.css">
          <link rel="stylesheet" href="/static/css/pygments-dark.css">
          <link rel="stylesheet" href="/static/css/reference.css">
          <link rel="stylesheet" href="/static/css/search.css">
          <c-if cond="is_playground">
            <link rel="stylesheet" href="/static/playground/playground.css">
          </c-if>
          <c-if cond="has_live_code">
            <link rel="stylesheet" href="/static/playground/live_code.css">
          </c-if>
          <meta name="djc-base-path" c-content="base_path">
          <c-css />
        </head>
        <body
          c-class="{
            'citry-playground-page': is_playground,
            'citry-landing-page': is_landing,
          }"
        >
          <header class="djc-header">
            <div class="djc-header__inner">
              <button
                class="djc-hamburger"
                aria-label="Open navigation"
                aria-controls="djc-sidebar"
                aria-expanded="false"
              >
                <svg
                  viewBox="0 0 24 24"
                  width="20"
                  height="20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <line
                    x1="3"
                    y1="6"
                    x2="21"
                    y2="6"
                  />
                  <line
                    x1="3"
                    y1="12"
                    x2="21"
                    y2="12"
                  />
                  <line
                    x1="3"
                    y1="18"
                    x2="21"
                    y2="18"
                  />
                </svg>
              </button>
              <a class="djc-logo" c-href="home_path">
                <c-citry-mark css_class="djc-logo__mark" />
                <span class="djc-logo__wordmark">Citry</span>
                <span class="djc-badge">Beta</span>
              </a>
              <nav class="djc-header__nav" aria-label="Primary navigation">
                <a
                  c-for="item in top_nav_items"
                  c-class="{'is-active': item.active}"
                  c-href="item.path"
                  c-aria-current="item.aria_current"
                >
                  <span class="djc-header__nav-label">{{ item.label }}</span>
                  <span
                    c-if="item.badge"
                    class="djc-nav-badge"
                  >
                    {{ item.badge }}
                  </span>
                </a>
              </nav>
              <div class="djc-header__actions">
                <button
                  class="djc-search-trigger"
                  type="button"
                  data-search-open
                  aria-label="Search"
                  aria-haspopup="dialog"
                  aria-controls="djc-search-dialog"
                  aria-expanded="false"
                >
                  <svg
                    class="djc-search-trigger__icon"
                    viewBox="0 0 24 24"
                    width="16"
                    height="16"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    aria-hidden="true"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <line
                      x1="21"
                      y1="21"
                      x2="16.65"
                      y2="16.65"
                    />
                  </svg>
                  <span class="djc-search-trigger__label">Search</span>
                  <kbd class="djc-search-trigger__key">/</kbd>
                </button>
                <c-if cond="show_version_picker">
                  <c-version-picker c-current_version="version" />
                </c-if>
                <div
                  class="djc-theme-picker"
                  role="radiogroup"
                  aria-label="Color theme"
                >
                  <button
                    class="djc-theme-picker__btn"
                    data-theme-value="light"
                    aria-label="Light theme"
                    title="Light"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      width="16"
                      height="16"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <circle cx="12" cy="12" r="5" />
                      <line
                        x1="12"
                        y1="1"
                        x2="12"
                        y2="3"
                      />
                      <line
                        x1="12"
                        y1="21"
                        x2="12"
                        y2="23"
                      />
                      <line
                        x1="4.22"
                        y1="4.22"
                        x2="5.64"
                        y2="5.64"
                      />
                      <line
                        x1="18.36"
                        y1="18.36"
                        x2="19.78"
                        y2="19.78"
                      />
                      <line x1="1" y1="12" x2="3" y2="12" />
                      <line x1="21" y1="12" x2="23" y2="12" />
                      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                    </svg>
                  </button>
                  <button
                    class="djc-theme-picker__btn"
                    data-theme-value="auto"
                    aria-label="System theme"
                    title="System"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      width="16"
                      height="16"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <rect x="2" y="3" width="20" height="14" rx="2" />
                      <line x1="8" y1="21" x2="16" y2="21" />
                      <line x1="12" y1="17" x2="12" y2="21" />
                    </svg>
                  </button>
                  <button
                    class="djc-theme-picker__btn"
                    data-theme-value="dark"
                    aria-label="Dark theme"
                    title="Dark"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      width="16"
                      height="16"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path
                        d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
                      />
                    </svg>
                  </button>
                </div>
                <a
                  class="djc-gh-link"
                  c-href="repo_url"
                  aria-label="GitHub"
                  target="_blank"
                  rel="noopener"
                >
                  <svg
                    viewBox="0 0 16 16"
                    width="20"
                    height="20"
                    fill="currentColor"
                  >
                    <path
                      d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
                    />
                  </svg>
                </a>
                <a
                  class="djc-social-link"
                  c-href="pypi_url"
                  aria-label="PyPI"
                  target="_blank"
                  rel="noopener"
                >
                  <svg
                    viewBox="0 0 448 512"
                    width="20"
                    height="20"
                    fill="currentColor"
                  >
                    <path
                      d="M439.8 200.5c-7.7-30.9-22.3-54.2-53.4-54.2h-40.1v47.4c0 36.8-31.2 67.8-66.8 67.8H172.7c-29.2 0-53.4 25-53.4 54.3v101.8c0 29 25.2 46 53.4 54.3 33.8 9.9 66.3 11.7 106.8 0 26.9-7.8 53.4-23.5 53.4-54.3v-40.7H226.2v-13.6h160.2c31.1 0 42.6-21.7 53.4-54.2 11.2-33.5 10.7-65.7 0-108.6M286.2 444.7a20.4 20.4 0 1 1 0-40.7 20.4 20.4 0 1 1 0 40.7M167.8 248.1h106.8c29.7 0 53.4-24.5 53.4-54.3V91.9c0-29-24.4-50.7-53.4-55.6-35.8-5.9-74.7-5.6-106.8.1-45.2 8-53.4 24.7-53.4 55.6v40.7h106.9v13.6h-147c-31.1 0-58.3 18.7-66.8 54.2-9.8 40.7-10.2 66.1 0 108.6 7.6 31.6 25.7 54.2 56.8 54.2H101v-48.8c0-35.3 30.5-66.4 66.8-66.4m-6.6-183.4a20.4 20.4 0 1 1 0 40.8 20.4 20.4 0 1 1 0-40.8"
                    />
                  </svg>
                </a>
                <a
                  class="djc-social-link"
                  c-href="discord_url"
                  aria-label="Discord"
                  target="_blank"
                  rel="noopener"
                >
                  <svg
                    viewBox="0 0 576 512"
                    width="20"
                    height="20"
                    fill="currentColor"
                  >
                    <path
                      d="M492.5 69.8c-.2-.3-.4-.6-.8-.7-38.1-17.5-78.4-30-119.7-37.1-.4-.1-.8 0-1.1.1s-.6.4-.8.8c-5.5 9.9-10.5 20.2-14.9 30.6-44.6-6.8-89.9-6.8-134.4 0-4.5-10.5-9.5-20.7-15.1-30.6-.2-.3-.5-.6-.8-.8s-.7-.2-1.1-.2C162.5 39 122.2 51.5 84.1 69c-.3.1-.6.4-.8.7C7.1 183.5-13.8 294.6-3.6 404.2c0 .3.1.5.2.8s.3.4.5.6c44.4 32.9 94 58 146.8 74.2.4.1.8.1 1.1 0s.7-.4.9-.7c11.3-15.4 21.4-31.8 30-48.8.1-.2.2-.5.2-.8s0-.5-.1-.8-.2-.5-.4-.6-.4-.3-.7-.4c-15.8-6.1-31.2-13.4-45.9-21.9-.3-.2-.5-.4-.7-.6s-.3-.6-.3-.9 0-.6.2-.9.3-.5.6-.7c3.1-2.3 6.2-4.7 9.1-7.1.3-.2.6-.4.9-.4s.7 0 1 .1c96.2 43.9 200.4 43.9 295.5 0 .3-.1.7-.2 1-.2s.7.2.9.4c2.9 2.4 6 4.9 9.1 7.2.2.2.4.4.6.7s.2.6.2.9-.1.6-.3.9-.4.5-.6.6c-14.7 8.6-30 15.9-45.9 21.8-.2.1-.5.2-.7.4s-.3.4-.4.7-.1.5-.1.8.1.5.2.8c8.8 17 18.8 33.3 30 48.8.2.3.6.6.9.7s.8.1 1.1 0c52.9-16.2 102.6-41.3 147.1-74.2.2-.2.4-.4.5-.6s.2-.5.2-.8c12.3-126.8-20.5-236.9-86.9-334.5zm-302 267.7c-29 0-52.8-26.6-52.8-59.2s23.4-59.2 52.8-59.2c29.7 0 53.3 26.8 52.8 59.2 0 32.7-23.4 59.2-52.8 59.2m195.4 0c-29 0-52.8-26.6-52.8-59.2s23.4-59.2 52.8-59.2c29.7 0 53.3 26.8 52.8 59.2 0 32.7-23.2 59.2-52.8 59.2"
                    />
                  </svg>
                </a>
                <div class="djc-overflow">
                  <button
                    class="djc-overflow__btn"
                    aria-label="More options"
                    aria-haspopup="true"
                    aria-expanded="false"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      width="20"
                      height="20"
                      fill="currentColor"
                    >
                      <circle
                        cx="12"
                        cy="5"
                        r="2"
                      />
                      <circle
                        cx="12"
                        cy="12"
                        r="2"
                      />
                      <circle
                        cx="12"
                        cy="19"
                        r="2"
                      />
                    </svg>
                  </button>
                  <div class="djc-overflow__menu">
                    <div class="djc-overflow__row">
                      <span class="djc-overflow__label">Theme</span>
                      <div
                        class="djc-theme-picker"
                        role="radiogroup"
                        aria-label="Color theme"
                      >
                        <button
                          class="djc-theme-picker__btn djc-theme-picker__btn--text"
                          data-theme-value="light"
                        >
                          Light
                        </button>
                        <button
                          class="djc-theme-picker__btn djc-theme-picker__btn--text"
                          data-theme-value="auto"
                        >
                          Auto
                        </button>
                        <button
                          class="djc-theme-picker__btn djc-theme-picker__btn--text"
                          data-theme-value="dark"
                        >
                          Dark
                        </button>
                      </div>
                    </div>
                    <c-if cond="version and show_version_picker">
                      <div class="djc-overflow__row">
                        <span class="djc-overflow__label">Version</span>
                        <c-version-picker c-current_version="version" />
                      </div>
                    </c-if>
                    <a
                      class="djc-overflow__link"
                      c-href="repo_url"
                      target="_blank"
                      rel="noopener"
                    >
                      GitHub
                    </a>
                    <a
                      class="djc-overflow__link"
                      c-href="pypi_url"
                      target="_blank"
                      rel="noopener"
                    >
                      PyPI
                    </a>
                    <a
                      class="djc-overflow__link"
                      c-href="discord_url"
                      target="_blank"
                      rel="noopener"
                    >
                      Discord
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </header>

          <c-if cond="is_playground">
            <aside class="djc-sidebar citry-playground__nav-drawer" id="djc-sidebar">
              <nav class="djc-sidebar__topnav" aria-label="Primary drawer navigation">
                <a
                  c-for="item in top_nav_items"
                  c-class="{'is-active': item.active}"
                  c-href="item.path"
                  c-aria-current="item.aria_current"
                >
                  <span>{{ item.label }}</span>
                  <span
                    c-if="item.badge"
                    class="djc-nav-badge"
                  >
                    {{ item.badge }}
                  </span>
                </a>
              </nav>
            </aside>
            <div class="djc-drawer-overlay"></div>
            <c-playground-workspace c-help_html="content_html" />
          </c-if>

          <c-if cond="is_landing">
            <aside class="djc-sidebar citry-landing__nav-drawer" id="djc-sidebar">
              <nav class="djc-sidebar__topnav" aria-label="Primary drawer navigation">
                <a
                  c-for="item in top_nav_items"
                  c-class="{'is-active': item.active}"
                  c-href="item.path"
                  c-aria-current="item.aria_current"
                >
                  <span>{{ item.label }}</span>
                  <span
                    c-if="item.badge"
                    class="djc-nav-badge"
                  >
                    {{ item.badge }}
                  </span>
                </a>
              </nav>
            </aside>
            <div class="djc-drawer-overlay"></div>
            <c-landing-page
              c-content_html="content_html"
              c-searchable="searchable"
              c-pagefind_weight="pagefind_weight"
              c-repo_url="repo_url"
            />
          </c-if>

          <div c-if="not is_playground and not is_landing" class="djc-layout">
            <aside class="djc-sidebar" id="djc-sidebar">
              <nav class="djc-sidebar__topnav" aria-label="Primary drawer navigation">
                <a
                  c-for="item in top_nav_items"
                  c-class="{'is-active': item.active}"
                  c-href="item.path"
                  c-aria-current="item.aria_current"
                >
                  <span>{{ item.label }}</span>
                  <span
                    c-if="item.badge"
                    class="djc-nav-badge"
                  >
                    {{ item.badge }}
                  </span>
                </a>
              </nav>
              <nav class="djc-sidebar__nav" aria-label="Section navigation">
                <div
                  c-for="section in nav_sections"
                  c-class="['djc-sidebar__section', {'djc-sidebar__section--standalone': section.is_standalone}]"
                  c-data-area="section.key"
                >
                  <c-if cond="section.is_standalone">
                    <a
                      c-class="['djc-sidebar__link', 'djc-sidebar__link--top', {'is-active': section.active}]"
                      c-href="section.path"
                    >
                      <span>{{ section.label }}</span>
                      <span
                        c-if="section.badge"
                        class="djc-nav-badge"
                      >
                        {{ section.badge }}
                      </span>
                    </a>
                  </c-if>
                  <c-else>
                    <c-if cond="section.collapsible">
                      <div
                        class="djc-sidebar__group djc-sidebar__group--top"
                        c-data-open="'true' if section.expanded else 'false'"
                      >
                        <button
                          class="djc-sidebar__group-label"
                          c-aria-expanded="'true' if section.expanded else 'false'"
                        >
                          <span>{{ section.label }}</span>
                          <span
                            c-if="section.badge"
                            class="djc-nav-badge"
                          >
                            {{ section.badge }}
                          </span>
                          <span class="djc-sidebar__caret">&#9662;</span>
                        </button>
                        <ul class="djc-sidebar__items" c-hidden="not section.expanded">
                          <c-if cond="section.index_path">
                            <li>
                              <a
                                c-class="['djc-sidebar__link', {'is-active': section.index_active}]"
                                c-href="section.index_path"
                              >
                                Overview
                              </a>
                            </li>
                          </c-if>
                          <li c-for="item in section.child_items">
                            <c-SidebarNavLink c-item="item" />
                          </li>
                        </ul>
                      </div>
                    </c-if>
                    <c-else>
                      <div class="djc-sidebar__label">
                        <span>{{ section.label }}</span>
                        <span
                          c-if="section.badge"
                          class="djc-nav-badge"
                        >
                          {{ section.badge }}
                        </span>
                      </div>
                      <c-if cond="section.index_path or section.child_items">
                        <ul class="djc-sidebar__items">
                          <c-if cond="section.index_path">
                            <li>
                              <a
                                c-class="['djc-sidebar__link', {'is-active': section.index_active}]"
                                c-href="section.index_path"
                              >
                                Overview
                              </a>
                            </li>
                          </c-if>
                          <li c-for="item in section.child_items">
                            <c-SidebarNavLink c-item="item" />
                          </li>
                        </ul>
                      </c-if>
                      <c-if cond="section.child_groups">
                        <div
                          c-for="group in section.child_groups"
                          c-class="['djc-sidebar__subsection', {'djc-sidebar__group': group.collapsible, 'djc-sidebar__group--top': group.section_style}]"
                          c-data-open="'true' if group.expanded else 'false'"
                        >
                          <c-if cond="group.collapsible">
                            <button
                              class="djc-sidebar__group-label"
                              c-aria-expanded="'true' if group.expanded else 'false'"
                            >
                              <span>{{ group.label }}</span>
                              <span class="djc-sidebar__caret">&#9662;</span>
                            </button>
                            <ul class="djc-sidebar__items" c-hidden="not group.expanded">
                              <li c-for="item in group.items">
                                <c-SidebarNavLink c-item="item" />
                              </li>
                            </ul>
                          </c-if>
                          <c-else>
                            <div class="djc-sidebar__label">{{ group.label }}</div>
                            <ul class="djc-sidebar__items">
                              <li c-for="item in group.items">
                                <c-SidebarNavLink c-item="item" />
                              </li>
                            </ul>
                          </c-else>
                        </div>
                      </c-if>
                    </c-else>
                  </c-else>
                </div>
              </nav>
            </aside>

            <div class="djc-drawer-overlay"></div>
            <div
              class="djc-resize-handle"
              data-target="djc-sidebar"
              data-direction="left"
            ></div>

            <main class="djc-content">
              <nav
                c-if="breadcrumbs"
                class="djc-breadcrumbs"
                aria-label="Breadcrumb"
              >
                <span c-for="crumb in breadcrumbs" class="djc-breadcrumbs__crumb">
                  <c-if cond="crumb.is_last">
                    <span class="djc-breadcrumbs__current">
                      {{ crumb.label }}
                    </span>
                  </c-if>
                  <c-else>
                    <c-if cond="crumb.path">
                      <a c-href="crumb.path">{{ crumb.label }}</a>
                    </c-if>
                    <c-else>
                      <span>{{ crumb.label }}</span>
                    </c-else>
                    <span class="djc-breadcrumbs__sep">/</span>
                  </c-else>
                </span>
              </nav>

              <details c-if="toc_items" class="djc-toc-mobile">
                <summary>On this page</summary>
                <c-TocItems c-items="toc_items" c-mobile="True" />
              </details>

              <article
                class="prose"
                c-data-pagefind-body="searchable"
                c-data-pagefind-weight="pagefind_weight"
              >
                <c-if cond="blog_post">
                  <header class="blog-post-header">
                    <h1>{{ title }}</h1>
                    <p class="blog-post-header__subtitle">{{ description }}</p>
                    <div class="blog-post-header__meta">
                      <span class="blog-post-header__author">
                        By
                        <c-if cond="blog_author_url">
                          <a c-href="blog_author_url">{{ blog_author }}</a>
                        </c-if>
                        <c-else>
                          <span>{{ blog_author }}</span>
                        </c-else>
                      </span>
                      <span aria-hidden="true">&middot;</span>
                      <time c-datetime="blog_published_iso">
                        {{ blog_published_label }}
                      </time>
                      <span aria-hidden="true">&middot;</span>
                      <span>About {{ blog_reading_minutes }} min read</span>
                    </div>
                    <div
                      c-if="blog_updated_iso"
                      class="blog-post-header__updated"
                    >
                      Updated
                      <time c-datetime="blog_updated_iso">
                        {{ blog_updated_label }}
                      </time>
                    </div>
                    <ul
                      c-if="blog_tags"
                      class="blog-tags"
                      aria-label="Tags"
                    >
                      <li c-for="tag in blog_tags">{{ tag }}</li>
                    </ul>
                  </header>
                </c-if>
                <c-else>
                  <c-if cond="inject_title">
                    <h1>{{ title }}</h1>
                  </c-if>
                </c-else>
                {{ content_html }}
              </article>

              <nav
                c-if="blog_post"
                class="blog-post-nav"
                aria-label="Blog post navigation"
              >
                <a class="blog-post-nav__all" c-href="blog_all_posts_path">
                  All posts
                </a>
                <div c-if="blog_newer or blog_older" class="djc-page-nav">
                  <c-if cond="blog_newer">
                    <a
                      class="djc-page-nav__card djc-page-nav__prev"
                      c-href="blog_newer.public_path"
                    >
                      <span class="djc-page-nav__direction">
                        &larr; Newer post
                      </span>
                      <strong>{{ blog_newer.title }}</strong>
                    </a>
                  </c-if>
                  <c-else>
                    <div class="djc-page-nav__card djc-page-nav__placeholder"></div>
                  </c-else>
                  <c-if cond="blog_older">
                    <a
                      class="djc-page-nav__card djc-page-nav__next"
                      c-href="blog_older.public_path"
                    >
                      <span class="djc-page-nav__direction">
                        Older post &rarr;
                      </span>
                      <strong>{{ blog_older.title }}</strong>
                    </a>
                  </c-if>
                  <c-else>
                    <div class="djc-page-nav__card djc-page-nav__placeholder"></div>
                  </c-else>
                </div>
              </nav>

              <nav
                c-if="not blog_post and (prev_page or next_page)"
                class="djc-page-nav"
              >
                <c-if cond="prev_page">
                  <a
                    class="djc-page-nav__card djc-page-nav__prev"
                    c-href="prev_page.path"
                  >
                    <span class="djc-page-nav__direction">
                      &larr; Previous
                    </span>
                    <strong>{{ prev_page.title }}</strong>
                  </a>
                </c-if>
                <c-else>
                  <div class="djc-page-nav__card djc-page-nav__placeholder"></div>
                </c-else>
                <c-if cond="next_page">
                  <a
                    class="djc-page-nav__card djc-page-nav__next"
                    c-href="next_page.path"
                  >
                    <span class="djc-page-nav__direction">
                      Next &rarr;
                    </span>
                    <strong>{{ next_page.title }}</strong>
                  </a>
                </c-if>
                <c-else>
                  <div class="djc-page-nav__card djc-page-nav__placeholder"></div>
                </c-else>
              </nav>

              <footer
                c-if="version or last_updated or edit_url"
                class="djc-footer"
              >
                <c-if cond="edit_url">
                  <div class="djc-footer__edit">
                    <a
                      c-href="edit_url"
                      target="_blank"
                      rel="noopener"
                    >
                      Edit this page on GitHub
                    </a>
                  </div>
                </c-if>
                <c-if cond="last_updated">
                  <div class="djc-footer__meta">
                    Last updated {{ last_updated }}
                    <c-if cond="authors">
                      by {{ authors }}
                    </c-if>
                  </div>
                </c-if>
                <c-if cond="version">
                  <div>Citry version: {{ version }}</div>
                </c-if>
              </footer>
            </main>

            <div
              c-if="toc_items"
              class="djc-resize-handle"
              data-target="djc-toc"
              data-direction="right"
            ></div>
            <aside
              c-if="toc_items"
              id="djc-toc"
              class="djc-toc"
            >
              <div class="djc-toc__label">On this page</div>
              <c-TocItems c-items="toc_items" />
            </aside>
          </div>

          <button
            c-if="not is_playground"
            class="djc-back-to-top"
            type="button"
            aria-label="Back to top"
            hidden
          >
            <svg
              viewBox="0 0 24 24"
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <line
                x1="12"
                y1="19"
                x2="12"
                y2="5"
              />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </button>

          <c-search-modal
            c-quick_links="search_quick_links"
            c-pagefind_path="pagefind_path"
            c-site_target="search_site_target"
          />

          <c-js />
          <script src="/static/js/site.js"></script>
          <script src="/static/js/search.js"></script>
          <c-if cond="is_playground">
            <script type="module" src="/static/playground/playground.js"></script>
          </c-if>
          <c-if cond="has_interactive_live_code">
            <script type="module" src="/static/playground/live_code.js"></script>
          </c-if>
          <c-if cond="is_landing">
            <script type="module" src="/static/playground/landing_composer.js"></script>
          </c-if>
        </body>
      </html>
    """


def _build_top_nav_view(
    nav_tree: NavTree,
    current_path: str,
    version_prefix: str = "",
) -> list[SimpleNamespace]:
    """Build primary navigation directly from the declared area order."""
    active_area = nav_tree.find_area(current_path)
    return [
        SimpleNamespace(
            key=area.label,
            label=area.label,
            badge=area.badge,
            path=nav_tree.project_path(area.entry_path, version_prefix),
            active=area is active_area,
            aria_current="true" if area is active_area else None,
        )
        for area in nav_tree.areas
    ]


def _build_nav_view(
    area: NavArea | None,
    nav_tree: NavTree,
    version_prefix: str = "",
) -> list[SimpleNamespace]:
    """Build the active area's sidebar model."""
    if area is None:
        return []
    return [
        SimpleNamespace(
            key=area.label,
            label=area.label,
            badge=area.badge,
            path="",
            is_standalone=False,
            active=False,
            collapsible=False,
            expanded=True,
            index_path="",
            index_active=False,
            child_items=[_project_nav_item(item, nav_tree, version_prefix) for item in area.items],
            child_groups=[_project_nav_group(group, nav_tree, version_prefix) for group in area.groups],
        )
    ]


def _build_breadcrumbs(
    nav_tree: NavTree,
    current_path: str,
    version_prefix: str = "",
) -> list[SimpleNamespace]:
    """The breadcrumb trail with an ``is_last`` flag on the final (current) crumb."""
    crumbs = nav_tree.find_breadcrumbs(current_path)
    last = len(crumbs) - 1
    return [
        SimpleNamespace(
            label=label,
            path=nav_tree.project_path(path, version_prefix),
            is_last=i == last,
        )
        for i, (label, path) in enumerate(crumbs)
    ]


def _project_nav_item(item: Any, nav_tree: NavTree, version_prefix: str) -> SimpleNamespace | None:
    if item is None:
        return None
    return SimpleNamespace(
        title=item.title,
        path=nav_tree.project_path(item.path, version_prefix),
        active=item.active,
        needs_review=item.needs_review,
        date_iso=item.date_iso,
        date_label=item.date_label,
    )


def _project_nav_group(group: Any, nav_tree: NavTree, version_prefix: str) -> SimpleNamespace:
    return SimpleNamespace(
        label=group.label,
        items=[_project_nav_item(item, nav_tree, version_prefix) for item in group.items],
        collapsible=group.collapsible,
        section_style=group.section_style,
        expanded=group.expanded,
    )


def _project_blog_neighbor(post: Any, nav_tree: NavTree | None, version_prefix: str) -> SimpleNamespace | None:
    if post is None:
        return None
    path = nav_tree.project_path(post.public_path, version_prefix) if nav_tree is not None else post.public_path
    return SimpleNamespace(title=post.title, public_path=path)


def _flatten_toc(toc_tokens: list) -> list[SimpleNamespace]:
    """
    Turn python-markdown's toc tokens into the right-rail model.

    The page H1 is unwrapped so its sections become the top level (the rail
    lists sections, not the redundant page title). Descendants retain their
    hierarchy and heading level so ``TocItems`` can render every H2-H6 with
    both semantic nesting and a level-based visual offset.
    """

    def view(token: dict, *, allow_collapse: bool = False) -> SimpleNamespace:
        level = int(token.get("level", 2))
        children = [view(child) for child in token.get("children", [])]
        return SimpleNamespace(
            id=token["id"],
            name=token["name"],
            kind=token.get("kind", ""),
            level=level,
            level_class=f"djc-toc__level-{level}",
            children=children,
            # Preserve the existing reference-page behavior: a top-level
            # symbol groups all of its recursively rendered members under one
            # toggle. Narrative subsection trees remain fully visible.
            collapsible=allow_collapse and any(child.kind for child in children),
        )

    top: list = []
    for token in toc_tokens:
        if token.get("level") == 1:
            top.extend(token.get("children", []))
        else:
            top.append(token)

    items: list[SimpleNamespace] = []
    for token in top:
        items.append(view(token, allow_collapse=True))
    return items


def _resolve_og_image(og_image: str, site_url: str) -> str:
    """The page's social-card image as a URL: its own ``og_image``, or the site default."""
    base = site_url.rstrip("/")
    if not og_image:
        return f"{base}{_DEFAULT_OG_IMAGE_PATH}" if base else _DEFAULT_OG_IMAGE_PATH
    if og_image.startswith(("http://", "https://")):
        return og_image
    return f"{base}/{og_image.lstrip('/')}" if base else f"/{og_image.lstrip('/')}"


def default_og_image_url(site_url: str) -> str:
    """
    The site-level fallback social-card image URL (what a page shows with no
    ``og_image``). The social-card step rewrites this to a per-page card where one
    is generated, so the two must agree on the exact string.
    """
    return _resolve_og_image("", site_url)


def _jsonld_dumps(data: dict[str, Any]) -> str:
    """
    Serialize a structured-data object for embedding in a ``<script>`` element.

    Inside a ``<script>`` the browser does not decode HTML entities, so escaping
    the quotes (as normal HTML escaping would) breaks the JSON. Instead only the
    three characters that could end the script element early are written as
    unicode escapes; the caller marks the result safe so the quotes survive.
    """
    raw = json.dumps(data, ensure_ascii=False)
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _build_article_jsonld(
    *,
    canonical: str,
    title: str,
    description: str,
    created: datetime | None,
    last_updated: datetime | None,
    site_name: str,
) -> str:
    """A ``TechArticle`` structured-data object for a content page."""
    org = {"@type": "Organization", "name": site_name}
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": title,
        "mainEntityOfPage": canonical,
        "url": canonical,
        "author": org,
        "publisher": org,
    }
    if description:
        data["description"] = description
    # Dates come from git history when available; omitted otherwise.
    if created is not None:
        data["datePublished"] = created.isoformat()
    if last_updated is not None:
        data["dateModified"] = last_updated.isoformat()
    return _jsonld_dumps(data)


def _build_blog_posting_jsonld(
    *,
    canonical: str,
    post: BlogPost,
    image: str,
    site_name: str,
) -> str:
    """A ``BlogPosting`` object sourced from explicit editorial metadata."""
    # Collective project bylines are organizations; named authors remain
    # people. This keeps the simple one-author front matter readable while
    # emitting the structured identity search engines expect.
    author_type = "Organization" if post.author.casefold() == "citry maintainers" else "Person"
    author: dict[str, Any] = {
        "@type": author_type,
        "name": post.author,
    }
    if post.author_url:
        author["url"] = _resolve_blog_author_url(post.author_url, canonical, post.public_path)

    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.description,
        "mainEntityOfPage": canonical,
        "url": canonical,
        "datePublished": post.published.isoformat(),
        "dateModified": post.effective_updated.isoformat(),
        "author": author,
        "publisher": {"@type": "Organization", "name": site_name},
        "image": image,
    }
    return _jsonld_dumps(data)


def _resolve_blog_author_url(author_url: str, canonical: str, public_path: str) -> str:
    """Resolve a root-relative byline URL beneath the canonical site's base path."""
    if author_url.startswith("https://"):
        return author_url

    canonical_parts = urlsplit(canonical)
    base_path = ""
    if canonical_parts.path.endswith(public_path):
        base_path = canonical_parts.path[: -len(public_path)]
    author_parts = urlsplit(author_url)
    resolved_path = f"{base_path.rstrip('/')}{author_parts.path}"
    return urlunsplit(
        (
            canonical_parts.scheme,
            canonical_parts.netloc,
            resolved_path,
            author_parts.query,
            author_parts.fragment,
        )
    )


def _format_blog_date(value: datetime) -> str:
    """Format an authored Blog timestamp for visible page metadata."""
    return value.strftime("%-d %B %Y")


def _build_breadcrumb_jsonld(
    canonical: str,
    breadcrumbs: list[SimpleNamespace],
    site_url: str,
) -> str:
    """Build structured breadcrumbs from the same YAML hierarchy as the UI."""
    site_root = site_url.rstrip("/")
    items: list[dict[str, Any]] = []
    last = len(breadcrumbs) - 1
    for index, crumb in enumerate(breadcrumbs):
        item: dict[str, Any] = {
            "@type": "ListItem",
            "position": index + 1,
            "name": crumb.label,
        }
        if index == last:
            item["item"] = canonical
        elif crumb.path:
            path = crumb.path.strip("/")
            item["item"] = f"{site_root}/{path}/" if path else f"{site_root}/"
        items.append(item)

    return _jsonld_dumps(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": items,
        }
    )
