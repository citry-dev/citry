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


def test_both_resize_handles_present(page: Any, docs_site_url: str) -> None:
    # Left sidebar handle + right TOC handle (the right one was the dropped hook).
    page.goto(docs_site_url + "/reference/component/")
    assert page.locator('.djc-resize-handle[data-target="djc-sidebar"]').count() == 1
    assert page.locator('.djc-resize-handle[data-target="djc-toc"]').count() == 1


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


def test_theme_toggle_sets_data_theme(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/")
    page.locator('.djc-header__actions [data-theme-value="dark"]').first.click()
    page.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'")


def test_active_nav_item_is_marked(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/reference/component/")
    # The current page's sidebar link carries the active class.
    assert page.locator(".djc-sidebar__link.is-active").count() >= 1


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
    collapsible_area, collapsible_group, static_group = next(
        (
            collapsible_area,
            collapsible_group,
            static_group,
        )
        for collapsible_area in tree.areas
        for collapsible_group in collapsible_area.groups
        if collapsible_group.collapsible
        for static_area in tree.areas
        if static_area is not collapsible_area
        for static_group in static_area.groups
        if not static_group.collapsible and static_group.label == collapsible_group.label
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
