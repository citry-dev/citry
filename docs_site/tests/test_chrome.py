"""Tests for the DocPage chrome (sidebar nav, active state, breadcrumbs, prev/next)."""

from __future__ import annotations

from docs_site.nav import NavItem, NavSection, NavTree
from docs_site.pipeline import render_page


def _nav() -> NavTree:
    return NavTree(
        sections=[
            NavSection(label="Home", path="/"),
            NavSection(
                label="Concepts",
                items=[
                    NavItem(title="Components", path="/concepts/components/"),
                    NavItem(title="Slots", path="/concepts/slots/"),
                ],
            ),
        ]
    )


def _render_components_page() -> str:
    return render_page(
        "# Components\n\n## Basics\n\nText.",
        nav_tree=_nav(),
        current_path="concepts/components/",
    ).html


def test_sidebar_shows_sections_and_active_item() -> None:
    html = _render_components_page()
    # A section with children renders as an inert category label.
    assert '<div class="djc-sidebar__label">Concepts</div>' in html
    # The current page's item is marked active; its sibling is not.
    assert '<a class="djc-sidebar__link is-active" href="/concepts/components/">Components</a>' in html
    assert '<a class="djc-sidebar__link" href="/concepts/slots/">Slots</a>' in html
    # A childless section renders as a standalone link.
    assert '<a class="djc-sidebar__link djc-sidebar__link--top" href="/">Home</a>' in html


def test_breadcrumbs_trail() -> None:
    html = _render_components_page()
    assert '<span class="djc-breadcrumbs__current">Components</span>' in html
    # The parent category is a non-link span (it has no page of its own).
    assert "<span>Concepts</span>" in html


def test_prev_next_links() -> None:
    html = _render_components_page()
    # In document order Home -> Components -> Slots, so prev=Home, next=Slots.
    assert 'djc-page-nav__prev" href="/"' in html
    assert 'djc-page-nav__next" href="/concepts/slots/"' in html


def test_right_rail_toc_lists_h2_sections() -> None:
    html = _render_components_page()
    # The H1 is unwrapped; its h2 ("Basics") becomes a TOC entry.
    assert '<a class="djc-toc__link" href="#basics">Basics</a>' in html


def test_chrome_header_and_footer() -> None:
    html = _render_components_page()
    assert '<span class="djc-logo__wordmark">Citry</span>' in html
    assert 'data-theme-value="dark"' in html
    assert "/static/css/site.css" in html
    assert "/static/js/site.js" in html


def test_render_without_nav_still_works() -> None:
    # A bare render (no nav) must not error; the sidebar is just empty.
    html = render_page("# Solo\n\nText.").html
    assert "<!DOCTYPE html>" in html
    assert '<article class="prose">' in html
    assert "djc-breadcrumbs" not in html  # no nav -> no breadcrumbs
