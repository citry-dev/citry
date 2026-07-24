"""Tests for the DocPage chrome (sidebar nav, active state, breadcrumbs, prev/next)."""

from __future__ import annotations

import json

from lxml import html as lxml_html

from docs_site._internal.components.doc_page import DocPage
from docs_site._internal.config import DocsConfig
from docs_site._internal.nav import NavItem, NavSection, NavTree
from docs_site._internal.pipeline import render_page


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
    document = lxml_html.document_fromstring(html)
    # A section with children renders as an inert category label.
    assert '<div class="djc-sidebar__label">Concepts</div>' in html
    # The current page's item is marked active; its sibling is not.
    components = document.xpath('//a[@href="/concepts/components/"]')[0]
    slots = document.xpath('//a[@href="/concepts/slots/"]')[0]
    assert components.text_content().strip() == "Components"
    assert "is-active" in components.classes
    assert slots.text_content().strip() == "Slots"
    assert "is-active" not in slots.classes
    # A childless section renders as a standalone link.
    home = document.xpath('//a[@href="/" and contains(@class, "djc-sidebar__link")]')[0]
    assert home.text_content().strip() == "Home"
    assert {"djc-sidebar__link", "djc-sidebar__link--top"} <= set(home.classes)


def test_breadcrumbs_trail() -> None:
    html = _render_components_page()
    document = lxml_html.document_fromstring(html)
    current = document.xpath('//span[contains(@class, "djc-breadcrumbs__current")]')[0]
    assert current.text_content().strip() == "Components"
    # The parent category is a non-link span (it has no page of its own).
    assert "<span>Concepts</span>" in html


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
    # BreadcrumbList JSON-LD, with the "/citry/" base path stripped (the trail
    # starts at the first content segment, not the project name).
    assert '"@type": "BreadcrumbList"' in html
    # The first crumb is the first content segment, proving "citry" was stripped.
    assert '"position": 1, "name": "Concepts"' in html
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
