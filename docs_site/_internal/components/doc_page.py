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
from urllib.parse import urlparse

from markupsafe import Markup

from citry import Component

# Imported for their registration side effect: the DocPage template renders
# <c-search-modal> and <c-version-picker>, which citry resolves from the registry.
from docs_site._internal.components.search_modal import SearchModal  # noqa: F401
from docs_site._internal.components.version_picker import VersionPicker  # noqa: F401

if TYPE_CHECKING:
    from datetime import datetime

    from docs_site._internal.nav import NavSection, NavTree

# Site-level social-card image used when a page sets no og_image of its own.
_DEFAULT_OG_IMAGE_PATH = "/static/img/favicon.png"

# The project's social channels: header icon links (GitHub / PyPI / Discord)
# and text links in the mobile overflow menu.
_REPO_URL = "https://github.com/citry-dev/citry"
_PYPI_URL = "https://pypi.org/project/citry/"
_DISCORD_URL = "https://discord.gg/NaQ8QPyHtD"


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

    def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        title = kwargs.title
        site_name = kwargs.site_name
        page_title = f"{title} - {site_name}" if title and title != site_name else site_name

        nav_sections: list[SimpleNamespace] = []
        breadcrumbs: list[SimpleNamespace] = []
        prev_page = next_page = None
        nav_tree: NavTree | None = kwargs.nav_tree
        if nav_tree is not None:
            nav_tree.set_active(kwargs.current_path)
            nav_sections = _build_nav_view(nav_tree.sections, kwargs.current_path)
            breadcrumbs = _build_breadcrumbs(nav_tree, kwargs.current_path)
            prev_page, next_page = nav_tree.find_prev_next(kwargs.current_path)

        toc_items = _flatten_toc(kwargs.toc_items or [])
        last_updated = kwargs.last_updated.strftime("%-d %b %Y") if kwargs.last_updated else ""

        # Structured data (JSON-LD): a breadcrumb trail on any page with a
        # canonical URL, plus an article description on content pages (the home
        # page has no path segments, so it gets neither).
        breadcrumb_jsonld = ""
        if kwargs.canonical and title:
            breadcrumb_jsonld = _build_breadcrumb_jsonld(kwargs.canonical, title, kwargs.site_url)
        article_jsonld = ""
        if kwargs.current_path.strip("/") and kwargs.canonical and title:
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
            "og_image": _resolve_og_image(kwargs.og_image, kwargs.site_url),
            "breadcrumb_jsonld": Markup(breadcrumb_jsonld) if breadcrumb_jsonld else "",  # noqa: S704 - escaped for <script>
            "article_jsonld": Markup(article_jsonld) if article_jsonld else "",  # noqa: S704 - escaped for <script>
            "edit_url": kwargs.edit_url,
            "repo_url": _REPO_URL,
            "pypi_url": _PYPI_URL,
            "discord_url": _DISCORD_URL,
            "google_site_verification": kwargs.google_site_verification,
            "nav_sections": nav_sections,
            "breadcrumbs": breadcrumbs,
            "prev_page": prev_page,
            "next_page": next_page,
            "toc_items": toc_items,
            # Add an <h1> from the title only when the content brings none.
            "inject_title": bool(title) and not kwargs.content_has_h1,
            "content_html": Markup(kwargs.content_html),  # noqa: S704 - trusted pipeline output
            "last_updated": last_updated,
            "authors": ", ".join(kwargs.authors) if kwargs.authors else "",
        }

    template = """
      <!DOCTYPE html>
      <html c-lang="lang">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{{ page_title }}</title>
        <c-if cond="description"><meta name="description" c-content="description"></c-if>
        <c-if cond="canonical"><link rel="canonical" c-href="canonical"></c-if>
        <meta name="robots" c-content="robots">
        <meta name="generator" content="citry docs builder">
        <c-if cond="google_site_verification"><meta name="google-site-verification" c-content="google_site_verification"></c-if>
        <link rel="alternate" type="text/markdown" href="/llms.txt" title="llms.txt">

        <meta property="og:type" content="article">
        <meta property="og:site_name" c-content="site_name">
        <meta property="og:title" c-content="title or site_name">
        <c-if cond="description"><meta property="og:description" c-content="description"></c-if>
        <c-if cond="canonical"><meta property="og:url" c-content="canonical"></c-if>
        <meta property="og:image" c-content="og_image">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" c-content="title or site_name">
        <c-if cond="description"><meta name="twitter:description" c-content="description"></c-if>
        <meta name="twitter:image" c-content="og_image">

        <c-if cond="breadcrumb_jsonld"><script type="application/ld+json">{{ breadcrumb_jsonld }}</script></c-if>
        <c-if cond="article_jsonld"><script type="application/ld+json">{{ article_jsonld }}</script></c-if>

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

        <link rel="icon" type="image/svg+xml" href="/static/img/favicon.svg">
        <link rel="icon" type="image/png" href="/static/img/favicon.png">
        <link rel="stylesheet" href="/static/css/tokens.css">
        <link rel="stylesheet" href="/static/css/site.css">
        <link rel="stylesheet" href="/static/css/pygments-light.css">
        <link rel="stylesheet" href="/static/css/pygments-dark.css">
        <link rel="stylesheet" href="/static/css/reference.css">
        <link rel="stylesheet" href="/static/css/search.css">
        <meta name="djc-base-path" c-content="base_path">
        <c-css />
      </head>
      <body>
        <header class="djc-header">
          <div class="djc-header__inner">
            <button class="djc-hamburger" aria-label="Open navigation" aria-controls="djc-sidebar" aria-expanded="false">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
            </button>
            <a class="djc-logo" href="/"><span class="djc-logo__wordmark">Citry</span></a>
            <nav class="djc-header__nav">
              <a href="/getting-started/installation/">Docs</a>
            </nav>
            <div class="djc-header__actions">
              <button class="djc-search-trigger" type="button" data-search-open aria-label="Search" aria-haspopup="dialog" aria-controls="djc-search-dialog" aria-expanded="false">
                <svg class="djc-search-trigger__icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <span class="djc-search-trigger__label">Search</span>
                <kbd class="djc-search-trigger__key">/</kbd>
              </button>
              <c-version-picker c-current_version="version" />
              <div class="djc-theme-picker" role="radiogroup" aria-label="Color theme">
                <button class="djc-theme-picker__btn" data-theme-value="light" aria-label="Light theme" title="Light">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                </button>
                <button class="djc-theme-picker__btn" data-theme-value="auto" aria-label="System theme" title="System">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                </button>
                <button class="djc-theme-picker__btn" data-theme-value="dark" aria-label="Dark theme" title="Dark">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                </button>
              </div>
              <a class="djc-gh-link" c-href="repo_url" aria-label="GitHub" target="_blank" rel="noopener">
                <svg viewBox="0 0 16 16" width="20" height="20" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
              </a>
              <a class="djc-social-link" c-href="pypi_url" aria-label="PyPI" target="_blank" rel="noopener">
                <svg viewBox="0 0 448 512" width="20" height="20" fill="currentColor"><path d="M439.8 200.5c-7.7-30.9-22.3-54.2-53.4-54.2h-40.1v47.4c0 36.8-31.2 67.8-66.8 67.8H172.7c-29.2 0-53.4 25-53.4 54.3v101.8c0 29 25.2 46 53.4 54.3 33.8 9.9 66.3 11.7 106.8 0 26.9-7.8 53.4-23.5 53.4-54.3v-40.7H226.2v-13.6h160.2c31.1 0 42.6-21.7 53.4-54.2 11.2-33.5 10.7-65.7 0-108.6M286.2 444.7a20.4 20.4 0 1 1 0-40.7 20.4 20.4 0 1 1 0 40.7M167.8 248.1h106.8c29.7 0 53.4-24.5 53.4-54.3V91.9c0-29-24.4-50.7-53.4-55.6-35.8-5.9-74.7-5.6-106.8.1-45.2 8-53.4 24.7-53.4 55.6v40.7h106.9v13.6h-147c-31.1 0-58.3 18.7-66.8 54.2-9.8 40.7-10.2 66.1 0 108.6 7.6 31.6 25.7 54.2 56.8 54.2H101v-48.8c0-35.3 30.5-66.4 66.8-66.4m-6.6-183.4a20.4 20.4 0 1 1 0 40.8 20.4 20.4 0 1 1 0-40.8"/></svg>
              </a>
              <a class="djc-social-link" c-href="discord_url" aria-label="Discord" target="_blank" rel="noopener">
                <svg viewBox="0 0 576 512" width="20" height="20" fill="currentColor"><path d="M492.5 69.8c-.2-.3-.4-.6-.8-.7-38.1-17.5-78.4-30-119.7-37.1-.4-.1-.8 0-1.1.1s-.6.4-.8.8c-5.5 9.9-10.5 20.2-14.9 30.6-44.6-6.8-89.9-6.8-134.4 0-4.5-10.5-9.5-20.7-15.1-30.6-.2-.3-.5-.6-.8-.8s-.7-.2-1.1-.2C162.5 39 122.2 51.5 84.1 69c-.3.1-.6.4-.8.7C7.1 183.5-13.8 294.6-3.6 404.2c0 .3.1.5.2.8s.3.4.5.6c44.4 32.9 94 58 146.8 74.2.4.1.8.1 1.1 0s.7-.4.9-.7c11.3-15.4 21.4-31.8 30-48.8.1-.2.2-.5.2-.8s0-.5-.1-.8-.2-.5-.4-.6-.4-.3-.7-.4c-15.8-6.1-31.2-13.4-45.9-21.9-.3-.2-.5-.4-.7-.6s-.3-.6-.3-.9 0-.6.2-.9.3-.5.6-.7c3.1-2.3 6.2-4.7 9.1-7.1.3-.2.6-.4.9-.4s.7 0 1 .1c96.2 43.9 200.4 43.9 295.5 0 .3-.1.7-.2 1-.2s.7.2.9.4c2.9 2.4 6 4.9 9.1 7.2.2.2.4.4.6.7s.2.6.2.9-.1.6-.3.9-.4.5-.6.6c-14.7 8.6-30 15.9-45.9 21.8-.2.1-.5.2-.7.4s-.3.4-.4.7-.1.5-.1.8.1.5.2.8c8.8 17 18.8 33.3 30 48.8.2.3.6.6.9.7s.8.1 1.1 0c52.9-16.2 102.6-41.3 147.1-74.2.2-.2.4-.4.5-.6s.2-.5.2-.8c12.3-126.8-20.5-236.9-86.9-334.5zm-302 267.7c-29 0-52.8-26.6-52.8-59.2s23.4-59.2 52.8-59.2c29.7 0 53.3 26.8 52.8 59.2 0 32.7-23.4 59.2-52.8 59.2m195.4 0c-29 0-52.8-26.6-52.8-59.2s23.4-59.2 52.8-59.2c29.7 0 53.3 26.8 52.8 59.2 0 32.7-23.2 59.2-52.8 59.2"/></svg>
              </a>
              <div class="djc-overflow">
                <button class="djc-overflow__btn" aria-label="More options" aria-haspopup="true" aria-expanded="false">
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><circle cx="12" cy="5" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="12" cy="19" r="2"/></svg>
                </button>
                <div class="djc-overflow__menu">
                  <div class="djc-overflow__row">
                    <span class="djc-overflow__label">Theme</span>
                    <div class="djc-theme-picker" role="radiogroup" aria-label="Color theme">
                      <button class="djc-theme-picker__btn djc-theme-picker__btn--text" data-theme-value="light">Light</button>
                      <button class="djc-theme-picker__btn djc-theme-picker__btn--text" data-theme-value="auto">Auto</button>
                      <button class="djc-theme-picker__btn djc-theme-picker__btn--text" data-theme-value="dark">Dark</button>
                    </div>
                  </div>
                  <c-if cond="version">
                    <div class="djc-overflow__row">
                      <span class="djc-overflow__label">Version</span>
                      <c-version-picker c-current_version="version" />
                    </div>
                  </c-if>
                  <a class="djc-overflow__link" c-href="repo_url" target="_blank" rel="noopener">GitHub</a>
                  <a class="djc-overflow__link" c-href="pypi_url" target="_blank" rel="noopener">PyPI</a>
                  <a class="djc-overflow__link" c-href="discord_url" target="_blank" rel="noopener">Discord</a>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div class="djc-layout">
          <aside class="djc-sidebar" id="djc-sidebar">
            <nav class="djc-sidebar__topnav">
              <a href="/getting-started/installation/">Docs</a>
              <a href="/examples/">Examples</a>
            </nav>
            <nav class="djc-sidebar__nav">
              <div c-for="section in nav_sections" c-class="['djc-sidebar__section', {'djc-sidebar__section--standalone': section.is_standalone}]">
                <c-if cond="section.is_standalone">
                  <a c-class="['djc-sidebar__link', 'djc-sidebar__link--top', {'is-active': section.active}]" c-href="section.path">{{ section.label }}</a>
                </c-if>
                <c-else>
                  <c-if cond="section.collapsible">
                    <div class="djc-sidebar__group djc-sidebar__group--top" c-data-open="'true' if section.expanded else 'false'">
                      <button class="djc-sidebar__group-label" c-aria-expanded="'true' if section.expanded else 'false'"><span>{{ section.label }}</span><span class="djc-sidebar__caret">&#9662;</span></button>
                      <ul class="djc-sidebar__items" c-hidden="not section.expanded">
                        <c-if cond="section.index_path">
                          <li><a c-class="['djc-sidebar__link', {'is-active': section.index_active}]" c-href="section.index_path">Overview</a></li>
                        </c-if>
                        <li c-for="item in section.child_items"><a c-class="['djc-sidebar__link', {'is-active': item.active}]" c-href="item.path">{{ item.title }}</a></li>
                      </ul>
                    </div>
                  </c-if>
                  <c-else>
                    <div class="djc-sidebar__label">{{ section.label }}</div>
                    <c-if cond="section.index_path or section.child_items">
                      <ul class="djc-sidebar__items">
                        <c-if cond="section.index_path">
                          <li><a c-class="['djc-sidebar__link', {'is-active': section.index_active}]" c-href="section.index_path">Overview</a></li>
                        </c-if>
                        <li c-for="item in section.child_items"><a c-class="['djc-sidebar__link', {'is-active': item.active}]" c-href="item.path">{{ item.title }}</a></li>
                      </ul>
                    </c-if>
                    <c-if cond="section.child_groups">
                      <div c-for="group in section.child_groups" class="djc-sidebar__group" c-data-open="'true' if group.expanded else 'false'">
                        <button class="djc-sidebar__group-label" c-aria-expanded="'true' if group.expanded else 'false'"><span>{{ group.label }}</span><span class="djc-sidebar__caret">&#9662;</span></button>
                        <ul class="djc-sidebar__items" c-hidden="not group.expanded">
                          <li c-for="item in group.items"><a c-class="['djc-sidebar__link', {'is-active': item.active}]" c-href="item.path">{{ item.title }}</a></li>
                        </ul>
                      </div>
                    </c-if>
                  </c-else>
                </c-else>
              </div>
            </nav>
          </aside>

          <div class="djc-drawer-overlay"></div>
          <div class="djc-resize-handle" data-target="djc-sidebar" data-direction="left"></div>

          <main class="djc-content">
            <nav class="djc-breadcrumbs" c-if="breadcrumbs" aria-label="Breadcrumb">
              <span c-for="crumb in breadcrumbs" class="djc-breadcrumbs__crumb">
                <c-if cond="crumb.is_last"><span class="djc-breadcrumbs__current">{{ crumb.label }}</span></c-if>
                <c-else><c-if cond="crumb.path"><a c-href="crumb.path">{{ crumb.label }}</a></c-if><c-else><span>{{ crumb.label }}</span></c-else><span class="djc-breadcrumbs__sep">/</span></c-else>
              </span>
            </nav>

            <details class="djc-toc-mobile" c-if="toc_items">
              <summary>On this page</summary>
              <ul class="djc-toc__list">
                <li c-for="item in toc_items" class="djc-toc__item">
                  <span class="djc-toc__row">
                    <c-if cond="item.kind"><span c-class="'doc-symbol doc-symbol-' + item.kind"></span></c-if>
                    <a class="djc-toc__link" c-href="'#' + item.id">{{ item.name }}</a>
                  </span>
                  <ul class="djc-toc__sublist" c-if="item.children">
                    <li c-for="child in item.children" class="djc-toc__subitem">
                      <c-if cond="child.kind"><span c-class="'doc-symbol doc-symbol-' + child.kind"></span></c-if>
                      <a class="djc-toc__link" c-href="'#' + child.id">{{ child.name }}</a>
                    </li>
                  </ul>
                </li>
              </ul>
            </details>

            <article class="prose" c-data-pagefind-body="searchable" c-data-pagefind-weight="pagefind_weight">
              <c-if cond="inject_title"><h1>{{ title }}</h1></c-if>
              {{ content_html }}
            </article>

            <nav class="djc-page-nav" c-if="prev_page or next_page">
              <c-if cond="prev_page">
                <a class="djc-page-nav__card djc-page-nav__prev" c-href="prev_page.path">
                  <span class="djc-page-nav__direction">&larr; Previous</span><strong>{{ prev_page.title }}</strong>
                </a>
              </c-if>
              <c-else><div class="djc-page-nav__card djc-page-nav__placeholder"></div></c-else>
              <c-if cond="next_page">
                <a class="djc-page-nav__card djc-page-nav__next" c-href="next_page.path">
                  <span class="djc-page-nav__direction">Next &rarr;</span><strong>{{ next_page.title }}</strong>
                </a>
              </c-if>
              <c-else><div class="djc-page-nav__card djc-page-nav__placeholder"></div></c-else>
            </nav>

            <footer class="djc-footer" c-if="version or last_updated or edit_url">
              <c-if cond="edit_url"><div class="djc-footer__edit"><a c-href="edit_url" target="_blank" rel="noopener">Edit this page on GitHub</a></div></c-if>
              <c-if cond="last_updated"><div class="djc-footer__meta">Last updated {{ last_updated }}<c-if cond="authors"> by {{ authors }}</c-if></div></c-if>
              <c-if cond="version"><div>Citry version: {{ version }}</div></c-if>
            </footer>
          </main>

          <div class="djc-resize-handle" data-target="djc-toc" data-direction="right" c-if="toc_items"></div>
          <aside class="djc-toc" id="djc-toc" c-if="toc_items">
            <div class="djc-toc__label">On this page</div>
            <ul class="djc-toc__list">
              <li c-for="item in toc_items" c-class="['djc-toc__item', {'djc-toc__item--collapsible': item.collapsible}]">
                <span class="djc-toc__row">
                  <c-if cond="item.collapsible"><button type="button" class="djc-toc__toggle" aria-expanded="false" c-aria-label="'Toggle members of ' + item.name"></button></c-if>
                  <c-if cond="item.kind"><span c-class="'doc-symbol doc-symbol-' + item.kind"></span></c-if>
                  <a class="djc-toc__link" c-href="'#' + item.id">{{ item.name }}</a>
                </span>
                <ul class="djc-toc__sublist" c-if="item.children">
                  <li c-for="child in item.children" class="djc-toc__subitem">
                    <c-if cond="child.kind"><span c-class="'doc-symbol doc-symbol-' + child.kind"></span></c-if>
                    <a class="djc-toc__link" c-href="'#' + child.id">{{ child.name }}</a>
                  </li>
                </ul>
              </li>
            </ul>
          </aside>
        </div>

        <button class="djc-back-to-top" type="button" aria-label="Back to top" hidden>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
        </button>

        <c-search-modal />

        <c-js />
        <script src="/static/js/site.js"></script>
        <script src="/static/js/search.js"></script>
      </body>
      </html>
    """


def _build_nav_view(sections: list[NavSection], current_path: str) -> list[SimpleNamespace]:
    """
    Build the sidebar view model: a standalone link, or a category label.

    A section that is just a page becomes a standalone link. A section with
    children becomes an inert category label; if it also has its own landing
    page, that page is surfaced as an "Overview" child so the label stays inert.
    """
    current = current_path.strip("/")
    view: list[SimpleNamespace] = []
    for section in sections:
        has_children = bool(section.items) or bool(section.groups)
        is_standalone = bool(section.path) and not has_children
        section_norm = (section.path or "").strip("/")
        collapsible = getattr(section, "collapsible", False) and has_children
        # A collapsible section starts open when the reader is on its index page
        # or one of its items, and closed otherwise (the sidebar JS then remembers
        # the reader's own toggles).
        contains_current = section_norm == current or any(item.path.strip("/") == current for item in section.items)
        view.append(
            SimpleNamespace(
                label=section.label,
                path=section.path,
                is_standalone=is_standalone,
                active=is_standalone and section_norm == current,
                collapsible=collapsible,
                expanded=collapsible and contains_current,
                index_path=section.path if (section.path and has_children) else "",
                index_active=bool(section.path) and has_children and section_norm == current,
                child_items=section.items,
                child_groups=section.groups,
            )
        )
    return view


def _build_breadcrumbs(nav_tree: NavTree, current_path: str) -> list[SimpleNamespace]:
    """The breadcrumb trail with an ``is_last`` flag on the final (current) crumb."""
    crumbs = nav_tree.find_breadcrumbs(current_path)
    last = len(crumbs) - 1
    return [SimpleNamespace(label=label, path=path, is_last=i == last) for i, (label, path) in enumerate(crumbs)]


def _flatten_toc(toc_tokens: list) -> list[SimpleNamespace]:
    """
    Turn python-markdown's toc tokens into the right-rail model.

    The page H1 is unwrapped so its sections become the top level (the rail
    lists sections, not the redundant page title). Each item keeps one level of
    children.
    """
    top: list = []
    for token in toc_tokens:
        if token.get("level") == 1:
            top.extend(token.get("children", []))
        else:
            top.append(token)

    items: list[SimpleNamespace] = []
    for token in top:
        children = [
            SimpleNamespace(id=c["id"], name=c["name"], kind=c.get("kind", "")) for c in token.get("children", [])
        ]
        # A reference symbol with members (children that carry a kind) is
        # collapsible; a plain content section is not.
        collapsible = any(child.kind for child in children)
        items.append(
            SimpleNamespace(
                id=token["id"],
                name=token["name"],
                kind=token.get("kind", ""),
                children=children,
                collapsible=collapsible,
            )
        )
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


def _build_breadcrumb_jsonld(canonical: str, title: str, site_url: str) -> str:
    """A ``BreadcrumbList`` structured-data object built from the page's URL path."""
    parsed = urlparse(canonical)
    segments = [s for s in parsed.path.strip("/").split("/") if s]

    # Drop the site's own base-path prefix (e.g. a project-pages "/citry/") so the
    # trail starts at the first content segment.
    prefix: list[str] = []
    base_segs = [s for s in urlparse(site_url).path.strip("/").split("/") if s]
    if base_segs and segments[: len(base_segs)] == base_segs:
        prefix += base_segs
        segments = segments[len(base_segs) :]

    if not segments:
        return ""

    base_url = f"{parsed.scheme}://{parsed.netloc}/{'/'.join(prefix)}".rstrip("/")
    items = []
    for i, seg in enumerate(segments):
        item_url = f"{base_url}/{'/'.join(segments[: i + 1])}/"
        name = title if i == len(segments) - 1 else seg.replace("-", " ").replace("_", " ").title()
        items.append({"@type": "ListItem", "position": i + 1, "name": name, "item": item_url})

    return _jsonld_dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items})
