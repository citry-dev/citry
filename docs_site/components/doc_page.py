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

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from markupsafe import Markup

from citry import Component

if TYPE_CHECKING:
    from docs_site.nav import NavSection, NavTree

# The project's repository, shown in the header GitHub link.
_REPO_URL = "https://github.com/JuroOravec/citry"


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
        # The navigation tree (docs_site.nav.NavTree) or None for a bare render.
        nav_tree: Any = None
        # This page's clean URL, e.g. "concepts/components/" (drives active state).
        current_path: str = ""
        # python-markdown's raw toc tokens; flattened into the right-rail TOC.
        toc_items: list | None = None
        # Footer "last updated" date (a datetime) and author names.
        last_updated: Any = None
        authors: list | None = None
        og_image: str = ""
        edit_url: str = ""

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

        <meta property="og:type" content="article">
        <meta property="og:site_name" c-content="site_name">
        <meta property="og:title" c-content="title or site_name">
        <c-if cond="description"><meta property="og:description" c-content="description"></c-if>
        <c-if cond="canonical"><meta property="og:url" c-content="canonical"></c-if>
        <c-if cond="og_image"><meta property="og:image" c-content="og_image"></c-if>
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" c-content="title or site_name">

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
              <a href="/getting-started/">Docs</a>
            </nav>
            <div class="djc-header__actions">
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
            </div>
          </div>
        </header>

        <div class="djc-layout">
          <aside class="djc-sidebar" id="djc-sidebar">
            <nav class="djc-sidebar__nav">
              <div c-for="section in nav_sections" c-class="['djc-sidebar__section', {'djc-sidebar__section--standalone': section.is_standalone}]">
                <c-if cond="section.is_standalone">
                  <a c-class="['djc-sidebar__link', 'djc-sidebar__link--top', {'is-active': section.active}]" c-href="section.path">{{ section.label }}</a>
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

            <article class="prose">
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

          <aside class="djc-toc" id="djc-toc" c-if="toc_items">
            <div class="djc-toc__label">On this page</div>
            <ul class="djc-toc__list">
              <li c-for="item in toc_items" class="djc-toc__item">
                <span class="djc-toc__row"><a class="djc-toc__link" c-href="'#' + item.id">{{ item.name }}</a></span>
                <ul class="djc-toc__sublist" c-if="item.children">
                  <li c-for="child in item.children" class="djc-toc__subitem"><a class="djc-toc__link" c-href="'#' + child.id">{{ child.name }}</a></li>
                </ul>
              </li>
            </ul>
          </aside>
        </div>

        <button class="djc-back-to-top" type="button" aria-label="Back to top" hidden>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
        </button>

        <c-js />
        <script src="/static/js/site.js"></script>
      </body>
      </html>
    """

    def template_data(self, kwargs: Any, slots: Any | None = None) -> dict[str, Any]:  # noqa: ARG002
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

        return {
            "lang": kwargs.lang,
            "page_title": page_title,
            "title": title,
            "description": kwargs.description,
            "canonical": kwargs.canonical,
            "robots": "noindex,follow" if kwargs.noindex else "index,follow",
            "version": kwargs.version,
            "site_name": site_name,
            "og_image": kwargs.og_image,
            "edit_url": kwargs.edit_url,
            "repo_url": _REPO_URL,
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
        view.append(
            SimpleNamespace(
                label=section.label,
                path=section.path,
                is_standalone=is_standalone,
                active=is_standalone and section_norm == current,
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
        children = [SimpleNamespace(id=c["id"], name=c["name"]) for c in token.get("children", [])]
        items.append(SimpleNamespace(id=token["id"], name=token["name"], children=children))
    return items
