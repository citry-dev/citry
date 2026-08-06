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

from pathlib import Path
from typing import Any

import pytest

from docs_site._internal.config import config
from docs_site._internal.site_nav import load_site_nav

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e


def _failed_requests(page: Any, url: str) -> list[str]:
    """Navigate to ``url`` and return any request that came back 4xx/5xx."""
    bad: list[str] = []
    page.on("response", lambda r: bad.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    page.goto(url, wait_until="networkidle")
    return bad


def _wait_for_attribute(locator: Any, name: str, value: str | None) -> None:
    locator.evaluate(
        """(element, expected) => new Promise((resolve, reject) => {
          const deadline = Date.now() + 2_000;
          const check = () => {
            if (element.getAttribute(expected.name) === expected.value) {
              resolve();
            } else if (Date.now() >= deadline) {
              reject(new Error(
                `${expected.name} did not become ${JSON.stringify(expected.value)}`
              ));
            } else {
              requestAnimationFrame(check);
            }
          };
          check();
        })""",
        {"name": name, "value": value},
    )


def _wait_for_style_property(locator: Any, name: str, value: str) -> None:
    locator.evaluate(
        """(element, expected) => new Promise((resolve, reject) => {
          const deadline = Date.now() + 2_000;
          const check = () => {
            const actual = element.style.getPropertyValue(expected.name);
            if (actual.includes(expected.value)) {
              resolve();
            } else if (Date.now() >= deadline) {
              reject(new Error(
                `${expected.name} did not include ${JSON.stringify(expected.value)}`
              ));
            } else {
              requestAnimationFrame(check);
            }
          };
          check();
        })""",
        {"name": name, "value": value},
    )


def _wait_for_text(locator: Any, value: str) -> None:
    locator.evaluate(
        """(element, expected) => new Promise((resolve, reject) => {
          const deadline = Date.now() + 2_000;
          const check = () => {
            if (element.textContent.includes(expected)) {
              resolve();
            } else if (Date.now() >= deadline) {
              reject(new Error(`Text did not include ${JSON.stringify(expected)}`));
            } else {
              requestAnimationFrame(check);
            }
          };
          check();
        })""",
        value,
    )


def test_pages_load_with_no_broken_assets(page: Any, docs_site_url: str) -> None:
    # The "missing files" class of bug: a dropped /static, /pagefind, or /citry
    # asset shows up as a 404 here.
    for path in (
        "/",
        "/getting-started/installation/",
        "/reference/component/",
        "/reference/",
        "/blog/",
        "/blog/language-agnostic-tools/",
    ):
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


def test_right_rail_toc_offsets_links_by_heading_level(page: Any, docs_site_url: str) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(docs_site_url + "/ui-library/components/combobox/")

    h2 = page.locator('.djc-toc a[href="#api-reference"]')
    h3 = page.locator('.djc-toc a[href="#inputs"]')
    h4 = page.locator('.djc-toc a[href="#ccombobox-server-inputs"]')
    assert h2.count() == h3.count() == h4.count() == 1

    h2_box = h2.bounding_box()
    h3_box = h3.bounding_box()
    h4_box = h4.bounding_box()
    assert h2_box is not None
    assert h3_box is not None
    assert h4_box is not None
    assert h3_box["x"] >= h2_box["x"] + 8
    assert h4_box["x"] >= h3_box["x"] + 8


def test_right_rail_toc_follows_back_and_forward_between_anchors(
    page: Any,
    docs_site_url: str,
) -> None:
    def wait_for_active_toc_link(href: str) -> None:
        page.wait_for_function(
            """href => {
                const active = Array.from(
                    document.querySelectorAll('.djc-toc__link.is-active')
                );
                return active.length === 2
                    && active.every(link => link.getAttribute('href') === href);
            }""",
            arg=href,
            timeout=1000,
        )

    def wait_for_no_active_toc_link() -> None:
        page.wait_for_function(
            "document.querySelectorAll('.djc-toc__link.is-active').length === 0",
            timeout=1000,
        )

    page.set_viewport_size({"width": 1280, "height": 600})
    page.add_init_script(
        """window.IntersectionObserver = class {
            observe() {}
            unobserve() {}
            disconnect() {}
        };"""
    )
    page.goto(docs_site_url + "/__tests__/toc-history/")
    first_href = "#first-target"
    second_href = "#second-target"

    page.evaluate("href => { window.location.hash = href; }", first_href)
    page.wait_for_function("href => window.location.hash === href", arg=first_href)
    wait_for_active_toc_link(first_href)
    page.evaluate("href => { window.location.hash = href; }", second_href)
    page.wait_for_function("href => window.location.hash === href", arg=second_href)
    wait_for_active_toc_link(second_href)

    page.go_back()
    page.wait_for_function("href => window.location.hash === href", arg=first_href)
    wait_for_active_toc_link(first_href)

    page.go_forward()
    page.wait_for_function("href => window.location.hash === href", arg=second_href)
    wait_for_active_toc_link(second_href)

    page.go_back()
    page.wait_for_function("href => window.location.hash === href", arg=first_href)
    page.go_back()
    page.wait_for_function("window.location.hash === ''")
    wait_for_no_active_toc_link()


def test_toc_anchor_click_activates_desktop_and_mobile_copies(
    page: Any,
    docs_site_url: str,
) -> None:
    def wait_for_rendering() -> None:
        page.evaluate(
            """() => new Promise(resolve => requestAnimationFrame(
                () => requestAnimationFrame(resolve)
            ))"""
        )

    def assert_active_href(href: str) -> None:
        active_hrefs = page.locator(".djc-toc__link.is-active").evaluate_all(
            "links => links.map(link => link.getAttribute('href'))"
        )
        assert active_hrefs == [href, href]

    page.set_viewport_size({"width": 1280, "height": 600})
    second_href = "#second-target"
    third_href = "#third-target"
    page.goto(docs_site_url + "/__tests__/toc-history/" + second_href)

    wait_for_rendering()
    assert_active_href(second_href)

    page.locator(f'#djc-toc .djc-toc__link[href="{third_href}"]').click()
    page.wait_for_function("href => window.location.hash === href", arg=third_href)
    wait_for_rendering()
    assert_active_href(third_href)

    page.locator(f'#djc-toc .djc-toc__link[href="{second_href}"]').click()
    page.wait_for_function("href => window.location.hash === href", arg=second_href)
    wait_for_rendering()
    assert_active_href(second_href)

    page.evaluate(
        """href => {
            const heading = document.getElementById(href.slice(1));
            window.scrollTo(0, heading.offsetTop - 70);
        }""",
        "#first-target",
    )
    page.wait_for_function(
        """href => {
            const active = Array.from(
                document.querySelectorAll('.djc-toc__link.is-active')
            );
            return active.length === 2
                && active.every(link => link.getAttribute('href') === href);
        }""",
        arg="#first-target",
    )
    page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }))")
    wait_for_rendering()
    assert_active_href("#first-target")

    page.locator(f'#djc-toc .djc-toc__link[href="{second_href}"]').click()
    wait_for_rendering()
    assert_active_href(second_href)


def test_both_resize_handles_present(page: Any, docs_site_url: str) -> None:
    # Left sidebar handle + right TOC handle (the right one was the dropped hook).
    page.goto(docs_site_url + "/reference/component/")
    assert page.locator('.djc-resize-handle[data-target="djc-sidebar"]').count() == 1
    assert page.locator('.djc-resize-handle[data-target="djc-toc"]').count() == 1


def test_ui_preview_frame_resizes_only_from_its_own_window(
    page: Any,
    docs_site_url: str,
) -> None:
    page.goto(docs_site_url + "/")
    page.locator("body").evaluate(
        """body => {
            body.innerHTML = '<iframe title="Preview" data-ui-preview-frame '
                + 'sandbox="allow-scripts" srcdoc="<p>Preview</p>"></iframe>';
        }"""
    )
    page.add_script_tag(path=str(Path("docs_site/static/js/site.js").resolve()))
    frame = page.locator("[data-ui-preview-frame]")
    frame_element = frame.element_handle()
    assert frame_element is not None
    content = frame_element.content_frame()
    assert content is not None

    content.evaluate("parent.postMessage({ type: 'citry-ui-preview-height', height: 321 }, '*')")
    page.wait_for_function("document.querySelector('[data-ui-preview-frame]').style.height === '321px'")

    page.evaluate("window.postMessage({ type: 'citry-ui-preview-height', height: 777 }, '*')")
    page.wait_for_timeout(50)
    assert frame.evaluate("element => element.style.height") == "321px"


def test_ui_api_table_scrolls_without_covering_the_toc(page: Any, docs_site_url: str) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(docs_site_url + "/ui-library/components/button/")

    marker = page.locator("#button-input-cbutton-server-inputs-type")
    wrapper = marker.locator("xpath=ancestor::div[contains(@class, 'table-wrapper')]")
    toc = page.locator(".djc-toc")

    assert wrapper.count() == 1
    assert wrapper.evaluate("element => element.scrollWidth > element.clientWidth")
    wrapper_box = wrapper.bounding_box()
    toc_box = toc.bounding_box()
    assert wrapper_box is not None
    assert toc_box is not None
    assert wrapper_box["x"] + wrapper_box["width"] <= toc_box["x"]

    wrapper.evaluate("element => { element.scrollLeft = element.scrollWidth }")
    assert wrapper.evaluate("element => element.scrollLeft > 0")


def test_search_returns_results(page: Any, docs_site_url: str) -> None:
    # Exercises the whole search path: the trigger opens the modal, Pagefind loads
    # its index from /pagefind/, and a query yields results.
    page.goto(docs_site_url + "/getting-started/installation/")
    page.locator("[data-search-open]").first.click()
    page.locator(".djc-search__input").fill("component")
    page.wait_for_selector(".djc-search__result", timeout=15000)
    assert page.locator(".djc-search__result").count() >= 1


def test_search_finds_the_card_color_journey(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/examples/")
    page.locator("[data-search-open]").first.click()
    page.locator(".djc-search__input").fill("accent color")
    page.wait_for_selector(".djc-search__result", timeout=15000)
    paths = page.locator(".djc-search__result").evaluate_all("links => links.map(link => new URL(link.href).pathname)")

    assert "/getting-started/your-first-component/" in paths or "/examples/card/" in paths


def test_search_prefixes_a_result_route_that_matches_the_deployment_base(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/")
    page.route(
        "**/__pagefind_base_path_test__.js",
        lambda route: route.fulfill(
            content_type="text/javascript",
            body=(
                "export function debouncedSearch() {"
                "return Promise.resolve({results: [{data: () => Promise.resolve({"
                "url: '/docs/', meta: {title: 'Docs'}, excerpt: 'Docs'"
                "})}]});}"
            ),
        ),
    )
    page.set_content(
        '<head><meta name="djc-base-path" content="/docs"></head><body>'
        "<button data-search-open>Search</button>"
        '<div class="djc-search__overlay" data-pagefind-path="/__pagefind_base_path_test__.js" hidden>'
        '<div class="djc-search__dialog">'
        '<button data-search-close>Close</button><input class="djc-search__input">'
        '<div class="djc-search__results"><div data-search-list></div>'
        "<div data-search-empty></div><div data-search-noresults hidden></div>"
        "<div data-search-error hidden></div></div></div></div></body>"
    )
    page.add_script_tag(path=str(Path("docs_site/static/js/search.js").resolve()))

    page.locator("[data-search-open]").click()
    page.locator(".djc-search__input").fill("docs")
    result = page.locator(".djc-search__result")
    result.wait_for()

    assert result.get_attribute("href").startswith("/docs/docs/?h=docs")


def test_google_search_fallback_scopes_to_the_public_site_path(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/")
    page.route("**/__missing_pagefind__.js", lambda route: route.abort())
    page.set_content(
        "<body><button data-search-open>Search</button>"
        '<div class="djc-search__overlay" data-pagefind-path="/__missing_pagefind__.js" '
        'data-search-site-target="owner.github.io/citry" hidden>'
        '<div class="djc-search__dialog"><button data-search-close>Close</button>'
        '<input class="djc-search__input"><div class="djc-search__results">'
        "<div data-search-list></div><div data-search-empty></div>"
        "<div data-search-noresults hidden></div><div data-search-error hidden></div>"
        "</div></div></div></body>"
    )
    page.add_script_tag(path=str(Path("docs_site/static/js/search.js").resolve()))

    page.locator("[data-search-open]").click()
    page.locator(".djc-search__input").fill("components")
    fallback = page.locator("[data-search-error] a")
    fallback.wait_for()

    assert fallback.get_attribute("href") == (
        "https://www.google.com/search?q=site:owner.github.io%2Fcitry+components"
    )


def test_theme_toggle_sets_data_theme(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/")
    page.locator('.djc-header__actions [data-theme-value="dark"]').first.click()
    page.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'")


def test_active_nav_item_is_marked(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/reference/component/")
    # The current page's sidebar link carries the active class.
    assert page.locator(".djc-sidebar__link.is-active").count() >= 1


@pytest.mark.parametrize(
    ("viewport_width", "open_drawer"),
    [(1280, False), (375, True)],
    ids=("desktop", "mobile-drawer"),
)
def test_internal_page_link_brings_active_sidebar_item_clearly_into_view(
    page: Any,
    docs_site_url: str,
    viewport_width: int,
    open_drawer: bool,
) -> None:
    def assert_active_link_is_clear(target_path: str) -> None:
        active = page.locator(f'.djc-sidebar__link.is-active[href="{target_path}"]')
        gaps = active.evaluate(
            """link => {
                const sidebar = link.closest('#djc-sidebar');
                const sidebarRect = sidebar.getBoundingClientRect();
                const linkRect = link.getBoundingClientRect();
                const viewportTop = sidebarRect.top + sidebar.clientTop;
                const viewportBottom = viewportTop + sidebar.clientHeight;
                return {
                    top: linkRect.top - viewportTop,
                    bottom: viewportBottom - linkRect.bottom,
                };
            }"""
        )
        assert gaps["top"] >= 24
        assert gaps["bottom"] >= 24

    def follow_content_link(target_path: str) -> None:
        page.locator("main").evaluate(
            """(main, path) => {
                const link = document.createElement('a');
                link.id = 'sidebar-scroll-test-link';
                link.href = path;
                link.textContent = 'Open another documentation page';
                main.prepend(link);
            }""",
            target_path,
        )
        page.locator("#sidebar-scroll-test-link").click()
        page.wait_for_url(docs_site_url + target_path)

    page.set_viewport_size({"width": viewport_width, "height": 480})
    page.goto(docs_site_url + "/docs/")
    sidebar = page.locator("#djc-sidebar")
    sidebar.evaluate("element => { element.scrollTop = 0; }")
    first_path = sidebar.locator(".djc-sidebar__link").first.get_attribute("href")
    assert first_path is not None
    target_path = sidebar.locator(".djc-sidebar__link").evaluate_all(
        """links => links
            .filter(link => !link.closest('[hidden]'))
            .sort((left, right) => (
                left.getBoundingClientRect().top - right.getBoundingClientRect().top
            ))
            .at(-1)
            .getAttribute('href')"""
    )
    assert target_path is not None
    target_is_below_viewport = sidebar.locator(f'.djc-sidebar__link[href="{target_path}"]').evaluate(
        """link => {
            const sidebar = link.closest('#djc-sidebar');
            const sidebarRect = sidebar.getBoundingClientRect();
            return link.getBoundingClientRect().top
                >= sidebarRect.top + sidebar.clientTop + sidebar.clientHeight;
        }"""
    )
    assert target_is_below_viewport

    follow_content_link(target_path)

    if open_drawer:
        page.locator(".djc-hamburger").click()
    assert_active_link_is_clear(target_path)

    if open_drawer:
        page.locator(".djc-drawer-overlay").click()
    sidebar.evaluate("element => { element.scrollTop = element.scrollHeight; }")
    first_is_above_viewport = sidebar.locator(f'.djc-sidebar__link[href="{first_path}"]').evaluate(
        """link => {
            const sidebar = link.closest('#djc-sidebar');
            const sidebarRect = sidebar.getBoundingClientRect();
            return link.getBoundingClientRect().bottom
                <= sidebarRect.top + sidebar.clientTop;
        }"""
    )
    assert first_is_above_viewport
    follow_content_link(first_path)
    if open_drawer:
        page.locator(".djc-hamburger").click()
    assert_active_link_is_clear(first_path)


def test_navigation_status_badges_and_review_hint_render(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/docs/")

    alpha_badge = page.locator('.djc-header__nav a[href="/ui-library/"] .djc-nav-badge')
    assert alpha_badge.inner_text() == "ALPHA"

    review_link = page.locator('.djc-sidebar__link[aria-label*="final human review"]').first
    assert review_link.locator(".djc-sidebar__review-icon").inner_text() == "🚧"
    hint = review_link.locator(".djc-sidebar__review-hint")
    assert hint.evaluate("el => getComputedStyle(el).opacity") == "0"
    review_link.hover()
    page.wait_for_function(
        "el => getComputedStyle(el).opacity === '1'",
        arg=hint.element_handle(),
    )


def test_active_header_underline_excludes_status_badge(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/ui-library/")

    active = page.locator('.djc-header__nav a[href="/ui-library/"]')
    label = active.locator(".djc-header__nav-label")
    badge = active.locator(".djc-nav-badge")

    assert "is-active" in (active.get_attribute("class") or "")
    assert active.evaluate("el => getComputedStyle(el).textDecorationLine") == "none"
    assert label.evaluate("el => getComputedStyle(el).textDecorationLine") == "underline"
    assert badge.evaluate("el => getComputedStyle(el).textDecorationLine") == "none"


def test_navigation_review_hint_stays_inside_resized_sidebar(page: Any, docs_site_url: str) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(docs_site_url + "/docs/")

    sidebar = page.locator("#djc-sidebar")
    sidebar.evaluate("el => { el.style.width = '160px'; }")
    review_link = page.locator('.djc-sidebar__link[aria-label*="final human review"]').first
    hint = review_link.locator(".djc-sidebar__review-hint")
    review_link.hover()
    sidebar_scrollport = sidebar.evaluate(
        """el => {
            const rect = el.getBoundingClientRect();
            el.scrollTop = 1;
            return {
                left: rect.left + el.clientLeft,
                right: rect.left + el.clientLeft + el.clientWidth,
                overflowY: getComputedStyle(el).overflowY,
                scrollable: el.scrollHeight > el.clientHeight,
                scrollTop: el.scrollTop,
            };
        }"""
    )
    hint_box = hint.bounding_box()
    assert hint_box is not None
    assert sidebar_scrollport["overflowY"] == "auto"
    assert sidebar_scrollport["scrollable"]
    assert sidebar_scrollport["scrollTop"] > 0
    assert hint_box["x"] >= sidebar_scrollport["left"]
    assert hint_box["x"] + hint_box["width"] <= sidebar_scrollport["right"]


def test_sidebar_groups_follow_declared_order_and_active_page(
    page: Any,
    docs_site_url: str,
) -> None:
    tree = load_site_nav(config)
    docs = tree.areas[0]
    expected_labels = [group.label for group in docs.groups]
    target = docs.groups[-2].items[0]
    page.goto(docs_site_url + target.path)
    labels = page.locator(
        ".djc-sidebar__subsection > .djc-sidebar__label, "
        ".djc-sidebar__subsection > "
        ".djc-sidebar__group-label span:first-child"
    ).all_text_contents()
    labels = [label.strip() for label in labels]
    assert labels == expected_labels
    assert page.locator(f'.djc-sidebar__link.is-active[href="{target.path}"]').count() == 1


def test_desktop_primary_navigation_does_not_overlap_actions(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/community/help/")
    for extra_labels in ((), ("Try it", "Citry UI")):
        page.locator(".djc-header__nav").evaluate(
            """(nav, labels) => {
                for (const label of labels) {
                    const link = document.createElement('a');
                    link.href = '#';
                    link.textContent = label;
                    nav.insertBefore(link, nav.lastElementChild);
                }
            }""",
            list(extra_labels),
        )
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
    tree = load_site_nav(config)
    labels = links.locator(":scope > span:first-child").all_inner_texts()
    assert labels == [area.label for area in tree.areas]
    badges = links.locator(":scope > .djc-nav-badge").all_inner_texts()
    assert badges == [area.badge.upper() for area in tree.areas if area.badge]
    assert links.evaluate_all("els => els.map(el => el.getAttribute('href'))") == [
        area.entry_path for area in tree.areas
    ]
    assert page.locator('.djc-sidebar__topnav a[aria-current="true"]').inner_text() == "Reference"


def test_blog_post_has_scoped_navigation_toc_and_feed(page: Any, docs_site_url: str) -> None:
    tree = load_site_nav(config)
    blog_area = tree.areas[-1]
    assert blog_area.label == "Blog"
    post = blog_area.items[1]

    page.goto(docs_site_url + post.path)

    primary = page.locator(".djc-header__nav a")
    assert primary.last.inner_text() == "Blog"
    assert primary.last.get_attribute("href") == "/blog/"
    assert page.locator(".djc-header__nav a.is-active").inner_text() == "Blog"
    assert page.locator("article.prose h1").count() == 1
    assert page.locator(".djc-toc .djc-toc__link").count() >= 1
    assert page.locator(f'.djc-sidebar__link.is-active[href="{post.path}"] time').count() == 1
    assert page.locator(".djc-header__actions > .djc-version-picker").count() == 0

    feed = page.request.get(docs_site_url + "/blog/feed.xml")
    assert feed.ok
    assert feed.headers["content-type"].startswith(("application/atom+xml", "application/xml"))

    page.set_viewport_size({"width": 375, "height": 800})
    page.locator(".djc-hamburger").click()
    assert page.locator('.djc-sidebar__topnav a[aria-current="true"]').inner_text() == "Blog"


def test_collapsible_state_does_not_hide_a_static_group_in_another_area(
    page: Any,
    docs_site_url: str,
) -> None:
    tree = load_site_nav(config)
    collapsible_area, collapsible_group = next(
        (area, group) for area in tree.areas for group in area.groups if group.collapsible
    )
    static_group = next(
        group
        for area in tree.areas
        if area is not collapsible_area
        for group in area.groups
        if not group.collapsible and group.items
    )

    page.goto(docs_site_url + collapsible_area.entry_path)
    toggle = page.locator(
        ".djc-sidebar__group-label",
        has_text=collapsible_group.label,
    )
    assert toggle.get_attribute("aria-expanded") == "false"
    toggle.click()
    assert toggle.get_attribute("aria-expanded") == "true"

    page.goto(docs_site_url + static_group.items[0].path)
    label = page.locator(
        ".djc-sidebar__subsection > .djc-sidebar__label",
        has_text=static_group.label,
    )
    assert label.all_text_contents() == [static_group.label]
    items = label.locator("xpath=following-sibling::ul[1]")
    assert items.is_visible()
    assert items.get_attribute("hidden") is None


def test_example_recipe_renders_its_live_demo(
    page: Any,
    docs_site_url: str,
) -> None:
    page.goto(docs_site_url + "/examples/tabs/")
    assert page.locator(".example-card").count() == 1
    tabs_frame = page.locator('.example-demo-frame[src="/examples/tabs/demo/"]')
    assert tabs_frame.count() == 1
    assert tabs_frame.get_attribute("title") == "Tabs example live demo"
    assert "example-demo-frame--theme-sync" not in (tabs_frame.get_attribute("class") or "")


def test_tabs_ui_preview_is_keyboard_operable_at_a_narrow_viewport(
    page: Any,
    docs_site_url: str,
) -> None:
    page.set_viewport_size({"width": 360, "height": 760})
    page.goto(docs_site_url + "/ui-library/components/tabs/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")
    demo = demos.nth(1)
    frame_element = demo.locator("[data-ui-preview-frame]")
    preview = demo.frame_locator("[data-ui-preview-frame]")
    tabs = preview.locator('[role="tab"]')

    demo.wait_for()
    frame_element.wait_for()
    assert demo.locator(".citry-ui-demo__source").get_attribute("open") is None
    assert tabs.count() == 3
    assert demo.locator("[data-live-activate]").count() == 0

    tabs.first.focus()
    page.keyboard.press("ArrowRight")

    assert tabs.nth(1).evaluate("element => element === document.activeElement")
    assert tabs.nth(1).get_attribute("aria-selected") == "true"
    assert "Finding nebulae" in preview.locator('[role="tabpanel"]:not([hidden])').inner_text()
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert preview.locator("html").evaluate("node => node.scrollWidth <= node.clientWidth")


def test_tabs_ui_sampler_and_configurator_are_result_first_and_reactive(
    page: Any,
    docs_site_url: str,
) -> None:
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(docs_site_url + "/ui-library/components/tabs/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")

    assert demos.count() == 13
    assert all(demos.nth(index).locator(".citry-ui-demo__source").get_attribute("open") is None for index in range(13))

    sampler = demos.nth(0).frame_locator("[data-ui-preview-frame]")
    sampler_roots = sampler.locator("[data-citry-tabs-root]")
    assert sampler_roots.count() == 2
    assert sampler_roots.nth(0).get_attribute("data-variant") == "underline"
    assert sampler_roots.nth(1).get_attribute("data-variant") == "pill"
    assert sampler.locator("button:disabled").count() == 1
    sampler.locator('[role="tab"]', has_text="Broadcast").click()
    assert "mixtape" in sampler.locator('[role="tabpanel"]:not([hidden])').first.inner_text()

    configurator_demo = demos.nth(2)
    controls_panel = configurator_demo.locator("[data-ui-preview-controls]")
    controls = controls_panel.locator("form")
    configurator = configurator_demo.frame_locator("[data-ui-preview-frame]")
    configurator_root = configurator.locator(".tabs-configurator")
    configured_root = configurator.locator("[data-citry-tabs-root]")
    assert controls_panel.get_attribute("open") == ""
    assert configurator.locator("form").count() == 0
    controls_panel.locator("summary").click()
    assert controls_panel.get_attribute("open") is None
    controls_panel.locator("summary").click()
    assert controls_panel.get_attribute("open") == ""
    controls.get_by_label("Accent").select_option("coral")
    _wait_for_style_property(configurator_root, "--cui-tabs-accent", "#c2410c")
    controls.get_by_label("Variant").select_option("pill")
    _wait_for_attribute(configured_root, "data-variant", "pill")
    controls.get_by_label("Density").select_option("compact")
    _wait_for_attribute(configured_root, "data-density", "compact")
    controls.get_by_label("Orientation").select_option("vertical")
    _wait_for_attribute(configured_root, "data-orientation", "vertical")
    controls.get_by_label("Alignment").select_option("end")
    _wait_for_attribute(configured_root, "data-align", "end")
    controls.get_by_label("Grow to fill space").check()
    _wait_for_attribute(configured_root, "data-grow", "")
    controls.get_by_label("Loop keyboard focus").uncheck()
    _wait_for_attribute(configured_root, "data-loop", None)
    controls.get_by_label("Disable all Tabs").check()
    _wait_for_attribute(configured_root, "data-disabled", "")
    assert configurator.locator('[role="tab"]:disabled').count() == 3
    controls.get_by_label("Disable all Tabs").uncheck()
    _wait_for_attribute(configured_root, "data-disabled", None)
    configurator.locator('[role="tab"]', has_text="Europa").click()
    assert configurator.locator(".tabs-configurator__status strong").inner_text() == "europa"

    page.locator('.djc-header__actions [data-theme-value="light"]').first.click()
    page.wait_for_function("document.documentElement.getAttribute('data-theme') === 'light'")
    page.wait_for_timeout(50)
    code_background = page.locator(".prose pre").first.evaluate("element => getComputedStyle(element).backgroundColor")
    preview_background = (
        demos.nth(0)
        .locator(".citry-ui-demo__preview")
        .evaluate("element => getComputedStyle(element).backgroundColor")
    )
    frame_background = sampler.locator("body").evaluate("element => getComputedStyle(element).backgroundColor")
    assert preview_background == code_background
    assert frame_background == code_background

    page.locator('.djc-header__actions [data-theme-value="dark"]').first.click()
    page.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'")
    page.wait_for_timeout(50)
    dark_code_background = page.locator(".prose pre").first.evaluate(
        "element => getComputedStyle(element).backgroundColor"
    )
    dark_frame_background = sampler.locator("body").evaluate("element => getComputedStyle(element).backgroundColor")
    assert dark_code_background != code_background
    assert dark_frame_background == dark_code_background

    page_font_size = float(page.locator("body").evaluate("element => parseFloat(getComputedStyle(element).fontSize)"))
    preview_font_size = float(
        sampler.locator("html").evaluate("element => parseFloat(getComputedStyle(element).fontSize)")
    )
    assert preview_font_size < page_font_size


def test_tabs_ui_focused_examples_cover_remaining_public_behaviors(
    page: Any,
    docs_site_url: str,
) -> None:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(docs_site_url + "/ui-library/components/tabs/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")

    density_demo = demos.nth(4)
    density_demo.scroll_into_view_if_needed()
    density = density_demo.frame_locator("[data-ui-preview-frame]")
    density_roots = density.locator("[data-citry-tabs-root]")
    assert density_roots.count() == 3
    density_demo.get_by_label("Make Tabs equal width").check()
    for index in range(3):
        _wait_for_attribute(density_roots.nth(index), "data-grow", "")

    layout_demo = demos.nth(5)
    layout_demo.scroll_into_view_if_needed()
    layout = layout_demo.frame_locator("[data-ui-preview-frame]")
    layout_root = layout.locator("[data-citry-tabs-root]")
    layout_demo.get_by_label("Orientation").select_option("vertical")
    _wait_for_attribute(layout_root, "data-orientation", "vertical")
    layout_demo.get_by_label("Alignment").select_option("end")
    _wait_for_attribute(layout_root, "data-align", "end")

    controlled_demo = demos.nth(6)
    controlled_demo.scroll_into_view_if_needed()
    controlled = controlled_demo.frame_locator("[data-ui-preview-frame]")
    controlled.get_by_label("Apply requests from Tabs").uncheck()
    controlled.get_by_role("tab", name="Europa").click()
    assert controlled.get_by_role("tab", name="Mercury").get_attribute("aria-selected") == "true"
    assert "europa" in controlled.locator(".tabs-controlled__status").inner_text()
    controlled.get_by_label("Apply requests from Tabs").check()
    controlled.get_by_role("tab", name="Titan").click()
    assert controlled.get_by_role("tab", name="Titan").get_attribute("aria-selected") == "true"

    disabled_demo = demos.nth(7)
    disabled_demo.scroll_into_view_if_needed()
    disabled = disabled_demo.frame_locator("[data-ui-preview-frame]")
    assert disabled.locator('[role="tab"]:disabled').count() == 1
    disabled_demo.get_by_label("Disable the whole group").check()
    _wait_for_attribute(disabled.locator("[data-citry-tabs-root]"), "data-disabled", "")
    assert disabled.locator('[role="tab"]:disabled').count() == 3

    activation_demo = demos.nth(8)
    activation_demo.scroll_into_view_if_needed()
    activation = activation_demo.frame_locator("[data-ui-preview-frame]")
    manual_list = activation.get_by_role("tablist", name="Manual probe data")
    manual_tabs = manual_list.get_by_role("tab")
    manual_tabs.first.focus()
    page.keyboard.press("ArrowRight")
    assert manual_tabs.nth(1).evaluate("element => element === document.activeElement")
    assert manual_tabs.first.get_attribute("aria-selected") == "true"
    page.keyboard.press("Enter")
    assert manual_tabs.nth(1).get_attribute("aria-selected") == "true"

    overflow_demo = demos.nth(9)
    overflow_demo.scroll_into_view_if_needed()
    overflow = overflow_demo.frame_locator("[data-ui-preview-frame]")
    overflow_list = overflow.get_by_role("tablist", name="Planetary observation programs")
    assert overflow_list.evaluate("element => element.scrollWidth > element.clientWidth")
    overflow.get_by_role("tab", name="Outer-system objects").click()
    assert overflow.get_by_role("tab", name="Outer-system objects").get_attribute("aria-selected") == "true"

    nested_demo = demos.nth(10)
    nested_demo.scroll_into_view_if_needed()
    nested = nested_demo.frame_locator("[data-ui-preview-frame]")
    nested.get_by_role("tab", name="Atmosphere").click()
    assert nested.get_by_role("tab", name="Jupiter").get_attribute("aria-selected") == "true"
    assert nested.get_by_role("tab", name="Atmosphere").get_attribute("aria-selected") == "true"

    direction_demo = demos.nth(11)
    direction_demo.scroll_into_view_if_needed()
    direction = direction_demo.frame_locator("[data-ui-preview-frame]")
    rtl_list = direction.get_by_role("tablist", name="الكواكب الداخلية بالعربية")
    rtl_tabs = rtl_list.get_by_role("tab")
    rtl_tabs.first.focus()
    page.keyboard.press("ArrowRight")
    assert rtl_tabs.nth(2).evaluate("element => element === document.activeElement")
    assert rtl_tabs.nth(2).get_attribute("aria-selected") == "true"

    theme_demo = demos.nth(12)
    theme_demo.scroll_into_view_if_needed()
    theme = theme_demo.frame_locator("[data-ui-preview-frame]")
    light_card = theme.locator(".tabs-theme__card--light")
    dark_card = theme.locator(".tabs-theme__card--dark")
    assert light_card.evaluate("element => getComputedStyle(element).colorScheme") == "light"
    assert dark_card.evaluate("element => getComputedStyle(element).colorScheme") == "dark"
    assert light_card.evaluate("element => getComputedStyle(element).backgroundColor") != (
        dark_card.evaluate("element => getComputedStyle(element).backgroundColor")
    )

    assert console_errors == []


def test_dialog_ui_examples_are_result_first_reactive_and_operable(
    page: Any,
    docs_site_url: str,
) -> None:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.goto(docs_site_url + "/ui-library/components/dialog/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")

    assert demos.count() == 11
    assert all(demos.nth(index).locator(".citry-ui-demo__source").get_attribute("open") is None for index in range(11))

    sampler = demos.nth(0).frame_locator("[data-ui-preview-frame]")
    sampler.get_by_role("button", name="Open field note").click()
    sampler_dialog = sampler.locator('[data-citry-ui-part="dialog"]').first
    assert sampler_dialog.evaluate("element => element.open") is True
    sampler_dialog.get_by_role("button", name="Close").click()
    assert sampler_dialog.evaluate("element => element.open") is False

    configurator_demo = demos.nth(2)
    controls = configurator_demo.locator("[data-ui-preview-controls] form")
    configurator = configurator_demo.frame_locator("[data-ui-preview-frame]")
    configured_dialog = configurator.locator('[data-citry-ui-part="dialog"]')
    controls.get_by_label("Size").select_option("lg")
    controls.get_by_label("Scroll").select_option("dialog")
    controls.get_by_label("Allow passive dismissal").uncheck()
    _wait_for_attribute(configured_dialog, "data-size", "lg")
    _wait_for_attribute(configured_dialog, "data-scroll", "dialog")
    configurator.get_by_role("button", name="Preview configuration").click()
    assert configured_dialog.evaluate("element => element.open") is True
    assert configured_dialog.get_by_role("button", name="Close").is_hidden()
    configured_dialog.get_by_role("button", name="Finish preview").click()
    assert configured_dialog.evaluate("element => element.open") is False

    assert console_errors == []


def test_dialog_ui_focused_examples_cover_control_focus_forms_and_nesting(
    page: Any,
    docs_site_url: str,
) -> None:
    page.goto(docs_site_url + "/ui-library/components/dialog/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")

    controlled = demos.nth(3).frame_locator("[data-ui-preview-frame]")
    controlled_trigger = controlled.get_by_role("button", name="Request flight plan")
    controlled_trigger.click()
    controlled_dialog = controlled.locator('[data-citry-ui-part="dialog"]')
    assert controlled_dialog.evaluate("element => element.open") is False
    controlled.get_by_label("Accept Dialog requests").check()
    controlled_trigger.click()
    assert controlled_dialog.evaluate("element => element.open") is True
    controlled_dialog.get_by_role("button", name="Request close").click()
    assert controlled_dialog.evaluate("element => element.open") is False

    focus = demos.nth(5).frame_locator("[data-ui-preview-frame]")
    focus.get_by_role("button", name="Name a comet").click()
    assert focus.locator("#comet-name").evaluate("element => element === document.activeElement") is True
    focus.get_by_role("dialog", name="Name a comet").get_by_role("button", name="Close").click()
    focus.get_by_role("button", name="Read eclipse report").click()
    assert (
        focus.get_by_role("heading", name="Total eclipse report").evaluate(
            "element => element === document.activeElement"
        )
        is True
    )

    dialog_form = demos.nth(7).frame_locator("[data-ui-preview-frame]")
    dialog_form.get_by_role("button", name="Choose constellation").click()
    dialog_form.get_by_role("dialog", name="Choose a constellation").get_by_role("button", name="Orion").click()
    _wait_for_text(dialog_form.locator(".dialog-form-demo__result"), "Orion")

    nested = demos.nth(8).frame_locator("[data-ui-preview-frame]")
    nested.get_by_role("button", name="Open transit report").click()
    outer = nested.get_by_role("dialog", name="Europa transit report")
    outer.get_by_role("button", name="Open transit chart").click()
    inner = nested.locator('[data-citry-ui-part="dialog"]').nth(1)
    assert inner.evaluate("element => element.open") is True
    inner.get_by_role("button", name="Return to report").click()
    assert inner.evaluate("element => element.open") is False
    assert outer.evaluate("element => element.open") is True


def test_combobox_ui_examples_are_result_first_reactive_and_operable(
    page: Any,
    docs_site_url: str,
) -> None:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.goto(docs_site_url + "/ui-library/components/combobox/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")

    assert demos.count() == 9
    assert all(demos.nth(index).locator(".citry-ui-demo__source").get_attribute("open") is None for index in range(9))

    sampler = demos.nth(0).frame_locator("[data-ui-preview-frame]")
    sampler_inputs = sampler.get_by_role("combobox")
    assert sampler_inputs.count() == 3
    assert sampler_inputs.nth(0).input_value() == "Saturn"
    assert sampler_inputs.nth(2).is_disabled()

    configurator_demo = demos.nth(2)
    controls = configurator_demo.locator("[data-ui-preview-controls] form")
    configurator = configurator_demo.frame_locator("[data-ui-preview-frame]")
    configured = configurator.locator("[data-citry-combobox-root]")
    controls.get_by_label("Variant").select_option("filled")
    controls.get_by_label("Size").select_option("lg")
    controls.get_by_label("Local filter").select_option("starts_with")
    controls.get_by_label("Open on focus").check()
    controls.get_by_label("Highlight first match").check()
    _wait_for_attribute(configured, "data-variant", "filled")
    _wait_for_attribute(configured, "data-size", "lg")
    configured.get_by_role("combobox").focus()
    _wait_for_attribute(configured, "data-open", "")
    assert configured.locator('[data-citry-ui-part="option"][data-highlighted]').count() == 1

    remote_demo = demos.nth(3)
    remote_demo.scroll_into_view_if_needed()
    remote = remote_demo.frame_locator("[data-ui-preview-frame]")
    remote.get_by_role("combobox").fill("ve")
    remote.get_by_role("option", name="Vega Blue-white star in Lyra").wait_for(state="visible")
    remote.get_by_role("combobox").fill("offline")
    remote.get_by_text("The catalog could not be read.").wait_for(state="visible")
    remote.get_by_role("combobox").fill("rig")
    remote.get_by_role("option", name="Rigel Blue supergiant in Orion").wait_for(state="visible")

    controlled_demo = demos.nth(4)
    controlled_demo.scroll_into_view_if_needed()
    controlled = controlled_demo.frame_locator("[data-ui-preview-frame]")
    controlled.get_by_role("combobox").fill("cer")
    controlled.get_by_role("option", name="Ceres Dwarf planet in the asteroid belt").click()
    assert "ceres" in controlled.locator(".controlled-target dl").inner_text()

    form_demo = demos.nth(5)
    form_demo.scroll_into_view_if_needed()
    form = form_demo.frame_locator("[data-ui-preview-frame]")
    form.get_by_role("button", name="Submit route").click()
    assert form.locator(".launch-form__result").inner_text() == "Route: luna"

    assert console_errors == []


def test_table_ui_examples_cover_semantics_footer_overflow_theme_and_environment(
    page: Any,
    docs_site_url: str,
) -> None:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.goto(docs_site_url + "/ui-library/components/table/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")

    assert demos.count() == 9
    assert all(demos.nth(index).locator(".citry-ui-demo__source").get_attribute("open") is None for index in range(9))

    basic = demos.nth(1).frame_locator("[data-ui-preview-frame]")
    table = basic.get_by_role("table", name="Galilean moons")
    assert table.locator('th[scope="col"]').count() == 3
    assert table.locator('th[scope="row"]').count() == 4
    assert table.locator('[data-column-key="diameter"]').first.get_attribute("data-align") == "end"

    totals = demos.nth(3).frame_locator("[data-ui-preview-frame]")
    footer = totals.locator('[data-citry-ui-part="footer"]')
    assert footer.locator('[data-citry-ui-part="footer-cell"]').count() == 3
    assert footer.get_by_text("84.5").count() == 1

    states = demos.nth(5).frame_locator("[data-ui-preview-frame]")
    assert states.locator('table[aria-busy="true"]').count() == 1
    assert states.locator('[data-citry-ui-part="empty"]').get_by_text("No signals match this wavelength.").count() == 1
    assert (
        states.locator('[data-citry-ui-part="error"]').get_by_text("The telescope feed is unavailable.").count() == 1
    )

    demos.nth(6).scroll_into_view_if_needed()
    sticky = demos.nth(6).frame_locator("[data-ui-preview-frame]")
    bounded = sticky.locator(".sticky-tables article").first.locator('[data-citry-ui-part="root"]')
    assert bounded.get_attribute("role") == "region"
    assert bounded.get_attribute("aria-labelledby") == bounded.locator("caption").get_attribute("id")
    assert bounded.evaluate("element => element.scrollWidth > element.clientWidth") is True
    assert bounded.evaluate("element => element.scrollHeight > element.clientHeight") is True
    assert (
        bounded.locator('[data-citry-ui-part="header-cell"]').first.evaluate(
            "element => getComputedStyle(element).position"
        )
        == "sticky"
    )

    demos.nth(7).scroll_into_view_if_needed()
    theme = demos.nth(7).frame_locator("[data-ui-preview-frame]")
    night = theme.locator(".observatory-tables__night")
    day = theme.locator(".observatory-tables__day")
    assert night.evaluate("element => getComputedStyle(element).colorScheme") == "dark"
    assert day.evaluate("element => getComputedStyle(element).colorScheme") == "light"

    demos.nth(8).scroll_into_view_if_needed()
    environment = demos.nth(8).frame_locator("[data-ui-preview-frame]")
    assert environment.locator(".table-environment").get_attribute("dir") == "rtl"
    assert environment.get_by_role("table", name="نظام نجمي").count() == 1

    assert console_errors == []


def test_button_ui_sampler_and_configurator_are_result_first_and_reactive(
    page: Any,
    docs_site_url: str,
) -> None:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.set_viewport_size({"width": 360, "height": 760})
    page.goto(docs_site_url + "/ui-library/components/button/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")

    assert demos.count() == 10
    assert all(demos.nth(index).locator(".citry-ui-demo__source").get_attribute("open") is None for index in range(10))

    sampler = demos.nth(0).frame_locator("[data-ui-preview-frame]")
    sampler_buttons = sampler.locator('[data-citry-ui-part="button"]')
    assert sampler_buttons.count() == 5
    assert sampler.locator("[data-loading]").count() == 1
    assert sampler.locator("button:disabled").count() == 1
    assert sampler.locator("html").evaluate("node => node.scrollWidth <= node.clientWidth")

    configurator_demo = demos.nth(2)
    configurator_demo.scroll_into_view_if_needed()
    controls = configurator_demo.locator("[data-ui-preview-controls] form")
    configurator = configurator_demo.frame_locator("[data-ui-preview-frame]")
    configured_button = configurator.locator('[data-citry-ui-part="button"]')

    controls.get_by_label("Variant").select_option("outline")
    _wait_for_attribute(configured_button, "data-variant", "outline")
    controls.get_by_label("Intent").select_option("positive")
    _wait_for_attribute(configured_button, "data-intent", "positive")
    controls.get_by_label("Size").select_option("large")
    _wait_for_attribute(configured_button, "data-size", "large")
    controls.get_by_label("Loading position").select_option("start")
    _wait_for_attribute(configured_button, "data-loading-position", "start")
    controls.get_by_label("Show loading state").check()
    _wait_for_attribute(configured_button, "data-loading", "")
    assert (
        configured_button.locator('[data-citry-ui-part="start"]').evaluate(
            "element => getComputedStyle(element).opacity"
        )
        == "0"
    )
    assert (
        configured_button.locator('[data-citry-ui-part="content"]').evaluate(
            "element => getComputedStyle(element).opacity"
        )
        == "1"
    )
    controls.get_by_label("Show loading state").uncheck()
    controls.get_by_label("Fill available width").check()
    _wait_for_attribute(configured_button, "data-block", "")
    controls.get_by_label("Disable Button").check()
    _wait_for_attribute(configured_button, "data-disabled", "")
    assert configured_button.is_disabled()

    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert console_errors == []


def test_button_ui_native_form_and_theme_examples_exercise_public_contracts(
    page: Any,
    docs_site_url: str,
) -> None:
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(docs_site_url + "/ui-library/components/button/", wait_until="networkidle")
    demos = page.locator("[data-citry-ui-demo]")

    form_demo = demos.nth(8)
    form_demo.scroll_into_view_if_needed()
    form = form_demo.frame_locator("[data-ui-preview-frame]")
    species = form.get_by_label("Species")
    species.fill("Scarlet tiger moth")
    form.get_by_role("button", name="Record sighting").click()
    assert form.locator(".button-form__result").inner_text() == "Recorded with field journal."
    form.get_by_role("button", name="Reset journal").click()
    assert species.input_value() == "Silver-washed fritillary"
    assert form.locator(".button-form__result").inner_text() == "Journal reset."

    theme_demo = demos.nth(9)
    theme_demo.scroll_into_view_if_needed()
    theme = theme_demo.frame_locator("[data-ui-preview-frame]")
    day = theme.locator(".button-theme__card--day")
    night = theme.locator(".button-theme__card--night")
    rounded = day.get_by_role("button", name="Open plant index")
    night_content = night.locator('[data-citry-ui-part="content"]').first

    assert day.evaluate("element => getComputedStyle(element).colorScheme") == "light"
    assert night.evaluate("element => getComputedStyle(element).colorScheme") == "dark"
    assert rounded.evaluate("element => getComputedStyle(element).borderRadius") == "999px"
    assert night_content.evaluate("element => getComputedStyle(element).letterSpacing") != "normal"


def test_form_submission_example_receives_the_native_submit_event(
    page: Any,
    docs_site_url: str,
) -> None:
    page.goto(docs_site_url + "/examples/form-submission/")
    card = page.locator(".example-card").first
    card.get_by_role("tab", name="Live demo").click()
    frame_element = card.locator('iframe[src="/examples/form-submission/demo/"]')
    assert set(frame_element.get_attribute("sandbox").split()) == {
        "allow-forms",
        "allow-same-origin",
        "allow-scripts",
    }
    frame = card.frame_locator('iframe[src="/examples/form-submission/demo/"]')
    frame.locator('input[name="name"]').fill("Ada Lovelace")
    frame.get_by_role("button", name="Submit").click()
    thanks = frame.locator(".contact-form__thanks")
    thanks.wait_for()
    assert thanks.inner_text() == "Thank you for your submission, Ada Lovelace!"


def test_example_card_is_source_first_and_keyboard_operable(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/examples/card/")
    card = page.locator(".example-card").first
    tabs = card.get_by_role("tab")
    panels = card.locator('.tabbed-content > [role="tabpanel"]')

    assert tabs.first.inner_text().strip() == "Component"
    assert tabs.first.get_attribute("aria-selected") == "true"
    tabs.first.focus()
    page.keyboard.press("End")

    assert tabs.nth(2).inner_text().strip() == "Live demo"
    assert tabs.nth(2).get_attribute("aria-selected") == "true"
    assert tabs.nth(2).evaluate("element => element === document.activeElement")
    assert panels.nth(0).is_hidden()
    assert panels.nth(2).is_visible()


def test_card_example_adapts_to_light_and_dark_color_schemes(page: Any, docs_site_url: str) -> None:
    def wait_for_card_colors(expected: dict[str, str]) -> None:
        page.wait_for_function(
            """expected => {
              const frame = document.querySelector('iframe[src="/examples/card/demo/"]');
              const card = frame && frame.contentDocument && frame.contentDocument.querySelector('.demo-card');
              if (!card) return false;
              const style = getComputedStyle(card);
              return style.backgroundColor === expected.background && style.color === expected.color;
            }""",
            arg=expected,
        )

    page.emulate_media(color_scheme="light")
    page.goto(docs_site_url + "/examples/card/")
    card = page.locator(".example-card").first
    card.get_by_role("tab", name="Live demo").click()
    frame = page.frame_locator('iframe[src="/examples/card/demo/"]')
    frame.locator(".demo-card").wait_for()
    light = frame.locator(".demo-card").evaluate(
        "element => ({background: getComputedStyle(element).backgroundColor, color: getComputedStyle(element).color})"
    )

    page.locator('.djc-header__actions [data-theme-value="dark"]').first.click()
    page.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'")
    dark = frame.locator(".demo-card").evaluate(
        "element => ({background: getComputedStyle(element).backgroundColor, color: getComputedStyle(element).color})"
    )

    assert light["background"] != dark["background"]
    assert light["color"] != dark["color"]

    page.emulate_media(color_scheme="dark")
    page.locator('.djc-header__actions [data-theme-value="auto"]').first.click()
    page.wait_for_function("!document.documentElement.hasAttribute('data-theme')")
    wait_for_card_colors(dark)
    auto_dark = frame.locator(".demo-card").evaluate(
        "element => ({background: getComputedStyle(element).backgroundColor, color: getComputedStyle(element).color})"
    )
    assert auto_dark == dark

    page.emulate_media(color_scheme="light")
    wait_for_card_colors(light)
    auto_light = frame.locator(".demo-card").evaluate(
        "element => ({background: getComputedStyle(element).backgroundColor, color: getComputedStyle(element).color})"
    )
    assert auto_light == light


def test_example_standalone_demo_page_loads(page: Any, docs_site_url: str) -> None:
    # The iframe target (a pre-rendered example page) loads with no failed requests.
    bad = _failed_requests(page, docs_site_url + "/examples/tabs/demo/")
    assert bad == [], f"example page loaded with failed requests: {bad}"


def test_tabs_example_supports_keyboard_navigation(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/examples/tabs/demo/")
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
    page.goto(docs_site_url + "/examples/fragments/demo/")
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
