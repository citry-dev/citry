"""Tests for the DocPage chrome (sidebar nav, active state, breadcrumbs, prev/next)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from lxml import html as lxml_html

from docs_site._internal.blog import load_blog_catalog
from docs_site._internal.components.doc_page import DocPage
from docs_site._internal.config import DocsConfig
from docs_site._internal.nav import SCOPE_SITE, NavArea, NavGroup, NavItem, NavTree
from docs_site._internal.pipeline import render_page


def _nav() -> NavTree:
    return NavTree(
        areas=[
            NavArea(
                label="Docs",
                items=[NavItem(title="Home", path="/")],
                groups=[
                    NavGroup(
                        label="Concepts",
                        items=[
                            NavItem(
                                title="Components",
                                path="/concepts/components/",
                            ),
                            NavItem(
                                title="Slots",
                                path="/concepts/slots/",
                            ),
                        ],
                    ),
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


def _site_nav() -> NavTree:
    return NavTree(
        areas=[
            NavArea(
                label="Docs",
                items=[NavItem(title="Home", path="/")],
                groups=[
                    NavGroup(
                        label="Guide",
                        items=[
                            NavItem(
                                title="Install",
                                path="/guide/install/",
                            ),
                            NavItem(
                                title="Setup",
                                path="/guide/setup/",
                            ),
                        ],
                    ),
                ],
            ),
            NavArea(
                label="Examples",
                items=[
                    NavItem(title="Overview", path="/examples/"),
                ],
            ),
            NavArea(
                label="Reference",
                items=[
                    NavItem(title="Overview", path="/reference/"),
                    NavItem(title="Widget", path="/reference/widget/"),
                ],
            ),
            NavArea(
                label="Community",
                items=[
                    NavItem(title="People", path="/community/people/"),
                    NavItem(title="Help", path="/community/help/"),
                ],
            ),
        ]
    )


def _render_site_nav(current_path: str) -> str:
    return render_page(
        "# Page\n\nText.",
        nav_tree=_site_nav(),
        current_path=current_path,
    ).html


def test_playground_layout_keeps_header_and_owns_the_viewport() -> None:
    tree = _site_nav()
    tree.areas.insert(
        3,
        NavArea(
            label="Try it",
            scope=SCOPE_SITE,
            items=[NavItem(title="Playground", path="/playground/", scope=SCOPE_SITE)],
        ),
    )
    source = """\
---
title: Try Citry
description: Run Citry in the browser.
layout: playground
---

Playground help text.
"""

    rendered = render_page(source, nav_tree=tree, current_path="playground/").html
    document = lxml_html.document_fromstring(rendered)

    assert len(document.xpath('//main[contains(@class, "citry-playground")]')) == 1
    assert len(document.xpath("//h1")) == 1
    assert document.xpath('//h1[text()="Try Citry"]')
    assert not document.xpath('//div[contains(@class, "djc-layout")]')
    assert not document.xpath('//nav[contains(@class, "djc-breadcrumbs")]')
    assert not document.xpath('//aside[@id="djc-toc"]')
    assert not document.xpath('//nav[contains(@class, "djc-page-nav")]')
    assert not document.xpath('//footer[contains(@class, "djc-footer")]')
    assert not document.xpath('//button[contains(@class, "djc-back-to-top")]')
    assert not document.xpath('//div[contains(@class, "djc-version-picker")]')
    assert document.xpath('//link[@href="/static/playground/playground.css"]')
    assert document.xpath('//script[@src="/static/playground/playground.js"]')
    assert document.xpath('//iframe[@sandbox="allow-forms allow-scripts" and @src="/static/playground/preview.html"]')
    for button_id, label in (
        ("citry-playground-run", "Run Python"),
        ("citry-playground-stop", "Stop Python"),
        ("citry-playground-copy-code", "Copy code"),
        ("citry-playground-download-code", "Download code"),
        ("citry-playground-reset", "Reset code"),
        ("citry-playground-help", "Playground help"),
        ("citry-playground-copy-python-error", "Copy Python diagnostic"),
        ("citry-playground-dismiss-python", "Close Python diagnostic"),
        ("citry-playground-copy-preview-error", "Copy Result diagnostic"),
        ("citry-playground-dismiss-preview", "Close Result diagnostic"),
    ):
        buttons = document.xpath(f'//button[@id="{button_id}" and @aria-label="{label}"]')
        assert len(buttons) == 1
        assert buttons[0].xpath("./svg")
        assert not buttons[0].text_content().strip()
    stop = document.xpath('//button[@id="citry-playground-stop"]')[0]
    assert "disabled" in stop.attrib
    assert "hidden" not in stop.attrib
    help_dialog = document.xpath('//dialog[@id="citry-playground-help-dialog"]')[0]
    assert help_dialog.attrib["aria-labelledby"] == "citry-playground-help-title"
    help_close = document.xpath('//button[@id="citry-playground-close-help"]')[0]
    assert help_close.attrib["aria-label"] == "Close playground help"
    assert help_close.xpath("./svg")
    assert not help_close.text_content().strip()
    help_footer_close = document.xpath('//button[@id="citry-playground-close-help-footer"]')[0]
    assert help_footer_close.text_content().strip() == "Close"
    assert document.xpath(
        '//dialog[@id="citry-playground-help-dialog"]'
        '//article[contains(concat(" ", normalize-space(@class), " "), " prose ")]'
    )
    assert (
        "from citry import Component" in document.xpath('//textarea[@id="citry-playground-editor-fallback"]')[0].text
    )
    active = document.xpath('//nav[@aria-label="Primary navigation"]/a[@aria-current="true"]')
    assert [link.text_content().strip() for link in active] == ["Try it"]
    assert 'content="website"' in rendered


def test_sidebar_shows_sections_and_active_item() -> None:
    html = _render_components_page()
    document = lxml_html.document_fromstring(html)
    # The active area and its groups are the only sidebar hierarchy.
    labels = document.xpath('//div[contains(@class, "djc-sidebar__label")]')
    assert [label.text_content().strip() for label in labels] == ["Docs", "Concepts"]
    assert not document.xpath('//button[contains(@class, "djc-sidebar__group-label")]')
    # The current page's item is marked active; its sibling is not.
    components = document.xpath('//a[@href="/concepts/components/"]')[0]
    slots = document.xpath('//a[@href="/concepts/slots/"]')[0]
    assert components.text_content().strip() == "Components"
    assert "is-active" in components.classes
    assert slots.text_content().strip() == "Slots"
    assert "is-active" not in slots.classes
    # Direct area items render before its groups.
    home = document.xpath('//a[@href="/" and contains(@class, "djc-sidebar__link")]')[0]
    assert home.text_content().strip() == "Home"
    assert "djc-sidebar__link" in home.classes
    assert "djc-sidebar__link--top" not in home.classes
    section = document.xpath('//div[contains(@class, "djc-sidebar__section")]')[0]
    assert section.get("data-area") == "Docs"


def test_navigation_renders_review_hint_and_area_badge_without_changing_titles() -> None:
    tree = NavTree(
        areas=[
            NavArea(
                label="Citry UI",
                badge="alpha",
                items=[
                    NavItem(
                        title="Overview",
                        path="/ui-library/",
                        needs_review=True,
                    ),
                ],
            ),
        ],
    )
    rendered = render_page(
        "# Citry UI\n",
        nav_tree=tree,
        current_path="ui-library/",
    ).html
    document = lxml_html.document_fromstring(rendered)

    header = document.xpath('//nav[@aria-label="Primary navigation"]/a')[0]
    assert header.xpath('.//span[contains(@class, "djc-nav-badge")]/text()')[0].strip() == "alpha"

    sidebar = document.xpath(
        '//a[@href="/ui-library/" and contains(@class, "djc-sidebar__link")]',
    )[0]
    assert sidebar.get("aria-label") == (
        "Overview. This page has not completed final human review. May contain minor inaccuracies."
    )
    assert sidebar.xpath('.//span[contains(@class, "djc-sidebar__review-icon")]/text()') == ["🚧"]
    assert (
        "has not completed final human review"
        in sidebar.xpath(
            './/span[contains(@class, "djc-sidebar__review-hint")]',
        )[0].text_content()
    )

    current = document.xpath('//span[contains(@class, "djc-breadcrumbs__current")]')[0]
    assert current.text_content().strip() == "Citry UI"
    assert tree.find_title("/ui-library/") == "Overview"

    css = Path("docs_site/static/css/site.css").read_text(encoding="utf-8")
    assert ".djc-sidebar__link:hover .djc-sidebar__review-hint" in css
    assert ".djc-sidebar__link:focus-visible .djc-sidebar__review-hint" in css


def test_collapsible_group_uses_toggle_markup_and_starts_closed() -> None:
    tree = NavTree(
        areas=[
            NavArea(
                label="Examples",
                items=[
                    NavItem(title="Overview", path="/examples/"),
                ],
                groups=[
                    NavGroup(
                        label="Components",
                        collapsible=True,
                        section_style=True,
                        items=[
                            NavItem(
                                title="Card",
                                path="/examples/card/",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
    result = render_page(
        "# Examples\n",
        nav_tree=tree,
        current_path="examples/",
    )
    document = lxml_html.document_fromstring(result.html)
    group = document.xpath('//div[contains(@class, "djc-sidebar__group")]')[0]
    assert group.get("data-open") == "false"
    assert "djc-sidebar__group--top" in group.classes
    button = group.xpath('.//button[contains(@class, "djc-sidebar__group-label")]')[0]
    assert button.get("aria-expanded") == "false"
    assert group.xpath(".//ul[@hidden]")


def test_primary_navigation_order_and_active_state() -> None:
    expected = [
        ("Docs", "/"),
        ("Examples", "/examples/"),
        ("Reference", "/reference/"),
        ("Community", "/community/people/"),
    ]
    cases = {
        "guide/setup/": "Docs",
        "examples/": "Examples",
        "reference/widget/": "Reference",
        "community/help/": "Community",
    }

    for current_path, active_label in cases.items():
        document = lxml_html.document_fromstring(_render_site_nav(current_path))
        for nav_class in ("djc-header__nav", "djc-sidebar__topnav"):
            links = document.xpath(f'//nav[contains(@class, "{nav_class}")]/a')
            assert [(link.text_content().strip(), link.get("href")) for link in links] == expected
            active = [link for link in links if "is-active" in link.classes]
            assert [link.text_content().strip() for link in active] == [active_label]
            assert active[0].get("aria-current") == "true"

        assert document.xpath('//nav[@aria-label="Primary navigation"]')
        assert document.xpath('//nav[@aria-label="Primary drawer navigation"]')
        assert document.xpath('//nav[@aria-label="Section navigation"]')


def test_primary_navigation_renders_blog_last_with_sidebar_dates() -> None:
    tree = _site_nav()
    tree.areas.append(
        NavArea(
            label="Blog",
            items=[
                NavItem(title="All posts", path="/blog/"),
                NavItem(
                    title="First post",
                    path="/blog/first/",
                    date_iso="2026-07-28",
                    date_label="28 Jul 2026",
                ),
            ],
        ),
    )
    result = render_page(
        "# First post\n",
        nav_tree=tree,
        current_path="blog/first/",
    )
    document = lxml_html.document_fromstring(result.html)
    links = document.xpath('//nav[@aria-label="Primary navigation"]/a')
    assert [link.text_content().strip() for link in links] == [
        "Docs",
        "Examples",
        "Reference",
        "Community",
        "Blog",
    ]
    active = [link for link in links if "is-active" in link.classes]
    assert len(active) == 1
    assert active[0].text_content().strip() == "Blog"
    sidebar_date = document.xpath('//time[contains(@class, "djc-sidebar__date")]')[0]
    assert sidebar_date.get("datetime") == "2026-07-28"
    assert sidebar_date.text_content().strip() == "28 Jul 2026"


def test_unknown_path_has_primary_nav_but_no_active_area() -> None:
    document = lxml_html.document_fromstring(
        _render_site_nav("not-in-navigation/"),
    )
    header_links = document.xpath('//nav[@aria-label="Primary navigation"]/a')
    assert len(header_links) == 4
    assert not [link for link in header_links if "is-active" in link.classes]
    assert not document.xpath('//nav[@aria-label="Section navigation"]/div[contains(@class, "djc-sidebar__section")]')


def test_primary_areas_have_scoped_sidebars_and_page_navigation() -> None:
    community = lxml_html.document_fromstring(_render_site_nav("community/people/"))
    community_sidebar = community.xpath('//nav[contains(@class, "djc-sidebar__nav")]')[0]
    community_hrefs = community_sidebar.xpath(".//a/@href")
    assert community_hrefs
    assert all(href.startswith("/community/") for href in community_hrefs)
    page_nav_hrefs = community.xpath('//nav[contains(@class, "djc-page-nav")]//a/@href')
    assert page_nav_hrefs
    assert all(href.startswith("/community/") for href in page_nav_hrefs)

    reference = lxml_html.document_fromstring(_render_site_nav("reference/widget/"))
    reference_hrefs = reference.xpath('//nav[contains(@class, "djc-sidebar__nav")]//a/@href')
    assert reference_hrefs
    assert all(href.startswith("/reference/") for href in reference_hrefs)

    docs = lxml_html.document_fromstring(_render_site_nav("guide/setup/"))
    docs_hrefs = docs.xpath('//nav[contains(@class, "djc-sidebar__nav")]//a/@href')
    assert docs_hrefs
    assert not any(href.startswith(("/community/", "/examples/", "/reference/")) for href in docs_hrefs)


def test_breadcrumbs_trail() -> None:
    html = _render_components_page()
    document = lxml_html.document_fromstring(html)
    current = document.xpath('//span[contains(@class, "djc-breadcrumbs__current")]')[0]
    assert current.text_content().strip() == "Components"
    # The parent category is a non-link span (it has no page of its own).
    assert "<span>Concepts</span>" in html
    docs = document.xpath('//nav[contains(@class, "djc-breadcrumbs")]//a[@href="/"]')[0]
    assert docs.text_content().strip() == "Docs"


def _render_with_seo(current_path: str) -> str:
    # A site URL with a base path ("/citry/") so the breadcrumb base-path
    # stripping is exercised.
    config = DocsConfig(site_url="https://x.test/citry/")
    return render_page(
        "# Components\n\n## Basics\n\nText.",
        config=config,
        canonical=f"https://x.test/citry/{current_path}",
        nav_tree=_nav(),
        current_path=current_path,
    ).html


def test_head_has_structured_data_and_card_meta() -> None:
    html = _render_with_seo("concepts/components/")
    # BreadcrumbList JSON-LD follows the same declared hierarchy as the UI.
    assert '"@type": "BreadcrumbList"' in html
    assert '"position": 1, "name": "Docs"' in html
    assert '"position": 2, "name": "Concepts"' in html
    assert '"item": "https://x.test/citry/"' in html
    # TechArticle JSON-LD on the content page.
    assert '"@type": "TechArticle"' in html
    assert '"headline": "Components"' in html
    # The default social-card image (absolute) on both og and twitter.
    assert 'property="og:image" content="https://x.test/citry/static/img/favicon.png"' in html
    assert 'name="twitter:image" content="https://x.test/citry/static/img/favicon.png"' in html
    # The llms.txt alternate link.
    assert 'rel="alternate" type="text/markdown" href="/llms.txt"' in html


def test_home_page_has_no_breadcrumb_structured_data() -> None:
    # The home page has no path segments, so it gets neither JSON-LD block.
    html = _render_with_seo("")
    assert "BreadcrumbList" not in html
    assert "TechArticle" not in html


def test_structured_data_escapes_hostile_title() -> None:
    # A title with </script>, <, >, & and quotes must not break out of the
    # JSON-LD <script> element: the dangerous characters are unicode-escaped and
    # the quotes survive (so the JSON stays valid). Rendered through DocPage
    # directly because the small front-matter parser cannot carry quotes.
    hostile = '</script><script>alert(1)</script> & "quotes"'
    html = str(
        DocPage(
            content_html="<p>body</p>",
            title=hostile,
            canonical="https://x.test/p/",
            current_path="p/",
            site_url="https://x.test/",
        )
    )
    # No raw breakout sequence survives anywhere in the document.
    assert "</script><script>alert(1)" not in html
    # The article JSON-LD is still valid JSON with the title intact.
    marker = '<script type="application/ld+json">'
    block = html.split(marker)[-1].split("</script>")[0]
    assert json.loads(block)["headline"] == hostile


def test_chrome_has_the_responsive_markup_hooks() -> None:
    # The vendored site.js/site.css bind to these; the page must emit them or the
    # behaviors are dead. The components page has an H2, so the TOC-guarded hooks
    # (right resize handle, mobile TOC) render too.
    html = _render_components_page()
    assert 'class="djc-sidebar__topnav"' in html  # drawer top-nav (mobile)
    assert 'class="djc-overflow"' in html  # header overflow menu (mobile)
    assert 'data-target="djc-toc" data-direction="right"' in html  # right-panel resize handle
    assert 'class="djc-toc-mobile"' in html  # mobile "On this page" disclosure


def test_reference_page_right_rail_toc_is_populated() -> None:
    from docs_site._internal.reference_pages import category, reference_page_markdown

    html = render_page(reference_page_markdown(category("component")), current_path="reference/component/").html
    # The reference symbol and its members reach the right-rail TOC via toc.py's
    # HTML-heading merge, each with a kind badge; a class with members is collapsible.
    assert 'href="#citry-component"' in html  # the class itself
    assert 'href="#citry-component-template-data"' in html  # a member
    assert "doc-symbol doc-symbol-class" in html  # the symbol-kind badge
    assert 'class="djc-toc__toggle"' in html  # collapsible members toggle


def test_version_picker_seeded_when_version_set() -> None:
    html = render_page("# X\n\ntext.", nav_tree=_nav(), current_path="concepts/slots/", version="9.9.9").html
    assert 'class="djc-version-picker"' in html
    assert 'data-current="9.9.9"' in html
    assert '<option value="9.9.9" selected>9.9.9</option>' in html


def test_version_picker_omitted_without_version() -> None:
    # No version (the default) renders no picker, so the header stays clean.
    html = render_page("# X\n\ntext.", nav_tree=_nav(), current_path="concepts/slots/").html
    assert "djc-version-picker" not in html


def test_prev_next_links() -> None:
    html = _render_components_page()
    document = lxml_html.document_fromstring(html)
    # In document order Home -> Components -> Slots, so prev=Home, next=Slots.
    previous = document.xpath('//a[contains(@class, "djc-page-nav__prev")]')[0]
    following = document.xpath('//a[contains(@class, "djc-page-nav__next")]')[0]
    assert previous.get("href") == "/"
    assert following.get("href") == "/concepts/slots/"


def test_right_rail_toc_lists_h2_sections() -> None:
    html = _render_components_page()
    # The H1 is unwrapped; its h2 ("Basics") becomes a TOC entry.
    document = lxml_html.document_fromstring(html)
    basics = document.xpath('//a[@href="#basics"]')[0]
    assert "djc-toc__link" in basics.classes
    assert basics.text_content().strip() == "Basics"


def test_toc_preserves_and_marks_every_heading_depth() -> None:
    rendered = render_page("# Page\n\n## Two\n\n### Three\n\n#### Four\n\n##### Five\n\n###### Six\n").html
    document = lxml_html.document_fromstring(rendered)

    for container in ('//aside[@id="djc-toc"]', '//details[contains(@class, "djc-toc-mobile")]'):
        for heading_id, level in (("two", 2), ("three", 3), ("four", 4), ("five", 5), ("six", 6)):
            links = document.xpath(f'{container}//a[@href="#{heading_id}"]')
            assert len(links) == 1
            level_owner = links[0].xpath(
                f'ancestor::*[contains(concat(" ", normalize-space(@class), " "), " djc-toc__level-{level} ")][1]'
            )[0]
            assert f"djc-toc__level-{level}" in level_owner.classes
        three_item = document.xpath(f'{container}//a[@href="#three"]/ancestor::li[1]')[0]
        four_item = document.xpath(f'{container}//a[@href="#four"]/ancestor::li[1]')[0]
        assert three_item.xpath('.//a[@href="#four"]')
        assert four_item.xpath('.//a[@href="#five"]')


def test_chrome_header_and_footer() -> None:
    html = _render_components_page()
    assert '<span class="djc-logo__wordmark">Citry</span>' in html
    assert 'data-theme-value="dark"' in html
    assert "/static/css/site.css" in html
    assert "/static/js/site.js" in html


def test_header_shows_github_pypi_discord() -> None:
    # DJC parity: GitHub / PyPI / Discord render as header icon links (GitHub
    # keeps the djc-gh-link hook, PyPI and Discord use djc-social-link) and as
    # text links in the mobile overflow menu.
    html = _render_components_page()
    document = lxml_html.document_fromstring(html)
    # Icon links in the header.
    github = document.xpath('//a[@aria-label="GitHub"]')[0]
    pypi = document.xpath('//a[@aria-label="PyPI"]')[0]
    discord = document.xpath('//a[@aria-label="Discord"]')[0]
    assert (github.get("href"), set(github.classes)) == (
        "https://github.com/citry-dev/citry",
        {"djc-gh-link"},
    )
    assert (pypi.get("href"), set(pypi.classes)) == (
        "https://pypi.org/project/citry/",
        {"djc-social-link"},
    )
    assert (discord.get("href"), set(discord.classes)) == (
        "https://discord.gg/NaQ8QPyHtD",
        {"djc-social-link"},
    )
    # Text links in the overflow menu.
    overflow_hrefs = {link.get("href") for link in document.xpath('//a[contains(@class, "djc-overflow__link")]')}
    assert overflow_hrefs == {
        "https://github.com/citry-dev/citry",
        "https://pypi.org/project/citry/",
        "https://discord.gg/NaQ8QPyHtD",
    }


def test_google_site_verification_meta() -> None:
    # The verification meta is emitted in the head only when the config token is
    # set; it stays out by default so pages don't carry an empty tag.
    present = render_page(
        "# X\n\ntext.",
        config=DocsConfig(google_site_verification="tok-ABC123"),
        current_path="x/",
    ).html
    assert '<meta name="google-site-verification" content="tok-ABC123"/>' in present

    absent = render_page(
        "# X\n\ntext.",
        config=DocsConfig(google_site_verification=""),
        current_path="x/",
    ).html
    assert "google-site-verification" not in absent


def test_render_without_nav_still_works() -> None:
    # A bare render (no nav) must not error; the sidebar is just empty.
    html = render_page("# Solo\n\nText.").html
    assert "<!DOCTYPE html>" in html
    assert '<article class="prose"' in html
    assert "djc-breadcrumbs" not in html  # no nav -> no breadcrumbs


def test_unnavved_page_in_site_scoped_namespace_hides_version_picker() -> None:
    tree = NavTree(
        areas=[
            NavArea(
                label="News",
                items=[NavItem(title="News", path="/news/", scope=SCOPE_SITE)],
                scope=SCOPE_SITE,
            )
        ]
    )

    html = render_page(
        "# Draft\n",
        nav_tree=tree,
        current_path="news/draft/",
        version="1.2.3",
    ).html

    assert "djc-version-picker" not in html


def test_blog_post_uses_editorial_header_metadata_and_navigation(tmp_path: Path) -> None:
    content = tmp_path / "content"
    blog = content / "blog"
    blog.mkdir(parents=True)
    (blog / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    post_path = blog / "2026-07-28-first-post.md"
    post_path.write_text(
        """---
title: First post
description: A visible post subtitle.
date: 2026-07-28T09:00:00+02:00
author: Citry maintainers
tags: Project updates, Architecture
---

Opening context.

## Evidence

The result.
""",
        encoding="utf-8",
    )
    catalog = load_blog_catalog(
        content,
        now=datetime.fromisoformat("2026-07-29T12:00:00+00:00"),
    )
    post = catalog.posts[0]
    blog_items = catalog.nav_items()
    for item in blog_items:
        item.scope = SCOPE_SITE
    tree = NavTree(areas=[NavArea(label="Blog", items=blog_items, source="blog", scope=SCOPE_SITE)])

    result = render_page(
        post.source,
        config=DocsConfig(content_dir=content, repo_root=tmp_path),
        canonical="https://citry.dev/blog/first-post/",
        nav_tree=tree,
        current_path="blog/first-post/",
        version="1.0.0",
        source_path=post_path,
        blog_catalog=catalog,
        blog_post=post,
        blog_feed_url="/blog/feed.xml",
    )
    document = lxml_html.document_fromstring(result.html)

    assert len(document.xpath("//article//h1")) == 1
    assert document.xpath('//p[contains(@class, "blog-post-header__subtitle")][contains(., "visible post subtitle")]')
    assert document.xpath('//time[@datetime="2026-07-28T09:00:00+02:00"]')
    assert document.xpath('//ul[contains(@class, "blog-tags")][@aria-label="Tags"]')
    assert document.xpath('//a[@href="#evidence"]')
    assert document.xpath('//a[contains(@class, "blog-post-nav__all")][@href="/blog/"]')
    assert not document.xpath('//nav[contains(@class, "djc-page-nav")]')
    assert not document.xpath('//*[contains(@class, "djc-version-picker")]')
    assert document.xpath('//link[@type="application/atom+xml"][@href="/blog/feed.xml"]')
    assert document.xpath('//meta[@property="article:published_time"]')
    assert len(document.xpath('//meta[@property="article:tag"]')) == 2

    blocks = [json.loads(node.text) for node in document.xpath('//script[@type="application/ld+json"]')]
    article = next(block for block in blocks if block.get("@type") == "BlogPosting")
    assert article["datePublished"] == "2026-07-28T09:00:00+02:00"
    assert article["dateModified"] == article["datePublished"]
    assert article["author"]["name"] == "Citry maintainers"
    assert article["author"]["@type"] == "Organization"
    assert not [block for block in blocks if block.get("@type") == "TechArticle"]


def test_blog_render_uses_catalog_values_for_quoted_yaml_metadata(tmp_path: Path) -> None:
    content = tmp_path / "content"
    blog = content / "blog"
    blog.mkdir(parents=True)
    (blog / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    post_path = blog / "2026-07-28-quoted-post.md"
    post_path.write_text(
        "---\n"
        'title: "A \\"quoted\\" title"\n'
        "description: 'It''s catalog-backed.'\n"
        "date: 2026-07-28T09:00:00+02:00\n"
        "author: Citry maintainers\n"
        "---\n\nOpening context.\n",
        encoding="utf-8",
    )
    catalog = load_blog_catalog(content, now=datetime.fromisoformat("2026-07-29T12:00:00+00:00"))
    post = catalog.posts[0]

    result = render_page(
        post.source,
        config=DocsConfig(content_dir=content, repo_root=tmp_path),
        canonical="https://citry.dev/blog/quoted-post/",
        current_path="blog/quoted-post/",
        source_path=post_path,
        blog_catalog=catalog,
        blog_post=post,
    )
    document = lxml_html.document_fromstring(result.html)

    assert result.meta is not None
    assert result.meta.title == 'A "quoted" title'
    assert result.meta.description == "It's catalog-backed."
    assert document.xpath("string(//article//h1)").strip() == 'A "quoted" title'
    assert document.xpath('string(//meta[@name="description"]/@content)') == "It's catalog-backed."


def test_root_relative_blog_author_url_keeps_project_base_path(tmp_path: Path) -> None:
    content = tmp_path / "content"
    blog = content / "blog"
    blog.mkdir(parents=True)
    (blog / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    post_path = blog / "2026-07-28-first-post.md"
    post_path.write_text(
        "---\n"
        "title: First post\n"
        "description: A project-pages post.\n"
        "date: 2026-07-28T09:00:00+02:00\n"
        "author: Juro Oravec\n"
        "author_url: /community/people/\n"
        "---\n\nOpening context.\n",
        encoding="utf-8",
    )
    catalog = load_blog_catalog(content, now=datetime.fromisoformat("2026-07-29T12:00:00+00:00"))
    post = catalog.posts[0]

    result = render_page(
        post.source,
        config=DocsConfig(content_dir=content, repo_root=tmp_path),
        canonical="https://owner.github.io/citry/blog/first-post/",
        current_path="blog/first-post/",
        source_path=post_path,
        blog_catalog=catalog,
        blog_post=post,
    )
    document = lxml_html.document_fromstring(result.html)
    expected = "https://owner.github.io/citry/community/people/"

    assert document.xpath('string(//meta[@property="article:author"]/@content)') == expected
    blocks = [json.loads(node.text) for node in document.xpath('//script[@type="application/ld+json"]')]
    article = next(block for block in blocks if block.get("@type") == "BlogPosting")
    assert article["author"]["url"] == expected
