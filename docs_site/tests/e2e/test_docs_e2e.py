"""
Browser e2e for the built docs site.

These are the checks the isolated unit tests could not make: they load the real
rendered pages in a browser and assert the whole thing works end to end - no
broken assets, a populated table of contents on reference pages, working search,
theme switching, active nav, and the responsive chrome. Each is a regression
guard for a class of bug that shipped because it was only ever tested in
isolation.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e


def _failed_requests(page: Any, url: str) -> list[str]:
    """Navigate to ``url`` and return any request that came back 4xx/5xx."""
    bad: list[str] = []
    page.on("response", lambda r: bad.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    page.goto(url, wait_until="networkidle")
    return bad


def test_pages_load_with_no_broken_assets(page: Any, docs_site_url: str) -> None:
    # The "missing files" class of bug: a dropped /static, /pagefind, or /citry
    # asset shows up as a 404 here.
    for path in ("/", "/getting-started/installation/", "/reference/component/", "/reference/"):
        bad = _failed_requests(page, docs_site_url + path)
        assert bad == [], f"{path} loaded with failed requests: {bad}"


def test_reference_page_has_a_populated_toc(page: Any, docs_site_url: str) -> None:
    # The exact regression: reference-symbol headings are injected as raw HTML, so
    # without toc.py's merge pass the right rail was empty.
    page.goto(docs_site_url + "/reference/component/")
    toc_links = page.locator(".djc-toc .djc-toc__link")
    assert toc_links.count() > 5, "reference right-rail TOC should list the class and its members"
    # A member of the class is present in the rail.
    assert page.locator('.djc-toc a[href="#citry-component-template-data"]').count() >= 1


def test_home_page_toc_renders(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/")
    assert page.locator(".djc-toc .djc-toc__link").count() >= 1


def test_both_resize_handles_present(page: Any, docs_site_url: str) -> None:
    # Left sidebar handle + right TOC handle (the right one was the dropped hook).
    page.goto(docs_site_url + "/reference/component/")
    assert page.locator('.djc-resize-handle[data-target="djc-sidebar"]').count() == 1
    assert page.locator('.djc-resize-handle[data-target="djc-toc"]').count() == 1


def test_search_returns_results(page: Any, docs_site_url: str) -> None:
    # Exercises the whole search path: the trigger opens the modal, Pagefind loads
    # its index from /pagefind/, and a query yields results.
    page.goto(docs_site_url + "/getting-started/installation/")
    page.locator("[data-search-open]").first.click()
    page.locator(".djc-search__input").fill("component")
    page.wait_for_selector(".djc-search__result", timeout=15000)
    assert page.locator(".djc-search__result").count() >= 1


def test_theme_toggle_sets_data_theme(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/")
    page.locator('.djc-header__actions [data-theme-value="dark"]').first.click()
    page.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'")


def test_active_nav_item_is_marked(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/reference/component/")
    # The current page's sidebar link carries the active class.
    assert page.locator(".djc-sidebar__link.is-active").count() >= 1


def test_events_and_guides_are_separate_ordered_docs_sections(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/guides/server-events/")
    labels = page.locator(".djc-sidebar__label").all_inner_texts()
    assert "EVENTS" in labels, labels
    assert "GUIDES" in labels, labels
    assert labels.index("EVENTS") + 1 == labels.index("GUIDES")
    assert page.locator('.djc-sidebar__link.is-active[href="/guides/server-events/"]').count() == 1

    page.goto(docs_site_url + "/web-frameworks/")
    assert page.locator('.djc-sidebar__link.is-active[href="/web-frameworks/"]').count() == 1
    assert page.locator(".djc-breadcrumbs").inner_text().split() == ["Guides", "/", "Web", "frameworks"]


def test_desktop_primary_navigation_does_not_overlap_actions(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/community/help/")
    for width in (769, 800, 900, 1024):
        page.set_viewport_size({"width": width, "height": 800})
        nav = page.locator(".djc-header__nav")
        actions = page.locator(".djc-header__actions")
        assert nav.is_visible()
        nav_box = nav.bounding_box()
        actions_box = actions.bounding_box()
        assert nav_box is not None
        assert actions_box is not None
        assert nav_box["x"] + nav_box["width"] <= actions_box["x"]


def test_mobile_shows_overflow_menu(page: Any, docs_site_url: str) -> None:
    # Below 768px the desktop header controls are hidden and the overflow menu
    # button takes over. The drawer carries the same primary navigation as the
    # desktop header, in the same order.
    page.set_viewport_size({"width": 375, "height": 800})
    page.goto(docs_site_url + "/reference/component/")
    assert page.locator(".djc-overflow__btn").is_visible()
    page.locator(".djc-hamburger").click()
    links = page.locator(".djc-sidebar__topnav a")
    assert links.all_inner_texts() == ["Docs", "Examples", "Reference", "Community"]
    assert links.evaluate_all("els => els.map(el => el.getAttribute('href'))") == [
        "/getting-started/installation/",
        "/examples/",
        "/reference/",
        "/community/people/",
    ]
    assert page.locator('.djc-sidebar__topnav a[aria-current="true"]').inner_text() == "Reference"


def test_examples_gallery_renders_live_demos(page: Any, docs_site_url: str) -> None:
    # The gallery shows a card per example, each with a live-demo iframe pointing
    # at that example's pre-rendered standalone page.
    page.goto(docs_site_url + "/examples/")
    assert page.locator(".example-card").count() >= 5
    assert page.locator('.example-demo-frame[src="/examples/tabs/"]').count() == 1


def test_example_standalone_demo_page_loads(page: Any, docs_site_url: str) -> None:
    # The iframe target (a pre-rendered example page) loads with no failed requests.
    bad = _failed_requests(page, docs_site_url + "/examples/tabs/")
    assert bad == [], f"example page loaded with failed requests: {bad}"


def test_tabs_example_supports_keyboard_navigation(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/examples/tabs/")
    tabs = page.locator('[role="tab"]')
    panels = page.locator('[role="tabpanel"]')

    tabs.first.focus()
    page.keyboard.press("ArrowRight")

    assert tabs.nth(1).get_attribute("aria-selected") == "true"
    assert tabs.nth(1).evaluate("element => element === document.activeElement")
    assert panels.nth(0).is_hidden()
    assert panels.nth(1).is_visible()

    page.keyboard.press("End")
    assert tabs.nth(2).get_attribute("aria-selected") == "true"
    page.keyboard.press("Home")
    assert tabs.first.get_attribute("aria-selected") == "true"


def test_fragment_loads_its_deps_on_demand(page: Any, docs_site_url: str) -> None:
    # The whole static-fragment path: the page loads the runtime from /citry/,
    # a click fetches the pre-rendered fragment, the runtime loads the component's
    # JS/CSS from the static /citry/cache/ files, and the fragment's own JS runs.
    page.goto(docs_site_url + "/examples/fragments/")
    page.locator("#frag-load").click()
    page.wait_for_function("document.querySelector('.frag-widget')?.dataset.ready === '1'")
    assert "(JS ran)" in page.locator(".frag-widget__title").inner_text()
    # The component's CSS loaded too (the widget got its purple border).
    border = page.eval_on_selector(".frag-widget", "el => getComputedStyle(el).borderTopColor")
    assert border == "rgb(130, 80, 223)"  # #8250df


def test_content_page_has_an_edit_on_github_link(page: Any, docs_site_url: str) -> None:
    # A content page's footer links to its source file on GitHub (from git_metadata).
    page.goto(docs_site_url + "/concepts/components/")
    link = page.locator(".djc-footer__edit a")
    assert link.count() == 1
    href = link.get_attribute("href")
    assert href.startswith("https://github.com/citry-dev/citry/edit/main/docs_site/content/")
