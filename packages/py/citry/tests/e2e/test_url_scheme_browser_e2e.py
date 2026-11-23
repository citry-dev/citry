"""
Browser e2e: the browser reads each URL's scheme as Citry's shared reader does.

Citry's server-side URL checks (the output checks, ``Redirect``, Citry UI's
link and image checks) read a URL's scheme through one reader, tested
against the table in
``crates/citry_html_transform/tests/fixtures/url_schemes.json``. These tests
ask the real browser to read the same rows, as a script URL and as link
attribute text, and click links that spell ``javascript:`` with non-ASCII
letters to show that the browser does not run them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry._urls import url_scheme

pytestmark = pytest.mark.e2e

_TABLE = Path(__file__).resolve().parents[5] / "crates/citry_html_transform/tests/fixtures/url_schemes.json"
# A lone surrogate cannot cross into the browser as the same string.
_ROWS: list[dict[str, Any]] = [
    row for row in json.loads(_TABLE.read_text(encoding="utf-8"))["rows"] if not row.get("python_only")
]

# A relative URL takes its base's scheme. Each check runs against two bases,
# so a row the reader calls relative cannot pass by having the base's scheme.
_BASES = ["https://example.test/", "http://example.test/"]
_BASE = _BASES[0]


def _page(base: str) -> str:
    return f'<!doctype html><html><head><base href="{base}"><title>start</title></head><body></body></html>'


_PAGE = _page(_BASE)

# Returns each URL's protocol without the colon, or null when it does not parse.
_READ_URLS = """
(urls) => urls.map((url) => {
    try {
        return new URL(url, document.baseURI).protocol.slice(0, -1);
    } catch {
        return null;
    }
})
"""

# Writes each attribute text into a link's `href` through the HTML parser,
# which decodes character references, and returns the decoded value and the
# protocol the link reads from it (null when it does not parse).
_READ_LINKS = """
(texts) => texts.map((text) => {
    const holder = document.createElement("div");
    holder.innerHTML = `<a href="${text}">x</a>`;
    const link = holder.firstElementChild;
    const protocol = link.protocol;
    return [link.getAttribute("href"), protocol === ":" ? null : protocol.slice(0, -1)];
})
"""

# Attribute text the HTML parser decodes before the URL parser reads it.
_ATTRIBUTE_TEXTS = [
    "java&Tab;script:x",
    "java&NewLine;script:x",
    "java&#x09;script:x",
    "javascript&colon;x",
    "&#x6A;avascript:x",
    "java&#383;cript:x",
    "javascr&#305;pt:x",
    "javascr&#304;pt:x",
    "&#0;javascript:x",
]

# URLs Firefox refuses to parse at all, although the reader reads `data`
# from them. A URL that does not parse loads nothing, so every check that
# reads `data` is at least as strict as the browser. No other URL may fail.
_UNPARSED_IN_FIREFOX = {"da\tta:text/html,x", "da\nta:text/html,x"}


def _disagrees(url: str, scheme: str | None, protocol: str | None, base: str) -> bool:
    if protocol is None:
        return url not in _UNPARSED_IN_FIREFOX
    return protocol != (scheme or base.split(":", 1)[0])


@pytest.mark.parametrize("base", _BASES)
def test_the_browser_reads_each_table_row_as_the_table_says(page: Any, base: str) -> None:
    page.set_content(_page(base))
    urls = [row["url"] for row in _ROWS]
    read = page.evaluate(_READ_URLS, urls)
    mismatches = [
        (row["url"], protocol)
        for row, protocol in zip(_ROWS, read, strict=True)
        if _disagrees(row["url"], row["scheme"], protocol, base)
    ]
    assert mismatches == []


@pytest.mark.parametrize("base", _BASES)
def test_link_attribute_text_reads_as_the_reader_reads_the_decoded_text(page: Any, base: str) -> None:
    page.set_content(_page(base))
    # Each row, every character written as a numeric reference, plus the
    # named and numeric references a template author might write.
    texts = ["".join(f"&#{ord(char)};" for char in row["url"]) for row in _ROWS] + _ATTRIBUTE_TEXTS
    read = page.evaluate(_READ_LINKS, texts)
    # The reader, given the text the browser decoded, must read the scheme
    # the browser reads. How Citry decodes is tested where it decodes.
    mismatches = [
        (text, decoded, protocol)
        for text, (decoded, protocol) in zip(texts, read, strict=True)
        if _disagrees(decoded, url_scheme(decoded), protocol, base)
    ]
    assert mismatches == []


@pytest.mark.parametrize(
    "href",
    [
        "java\u017fcript:void(document.title='ran')",
        "javascr\u0131pt:void(document.title='ran')",
        "javascr\u0130pt:void(document.title='ran')",
    ],
    ids=["long_s", "dotless_i", "dotted_capital_i"],
)
def test_a_link_with_a_non_ascii_javascript_letter_runs_nothing(page: Any, href: str) -> None:
    # The browser reads the link as a relative URL and loads it from the
    # base, which this route answers, so a click shows where it went.
    page.route(
        f"{_BASE}**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body="<title>landed</title>"),
    )
    page.set_content(_PAGE)
    page.evaluate(
        "(href) => { const a = document.createElement('a'); a.href = href; a.id = 'go';"
        " a.textContent = 'go'; document.body.append(a); }",
        href,
    )
    with page.expect_navigation():
        page.click("#go")
    assert page.title() == "landed"


def test_an_ascii_javascript_link_runs_when_clicked(page: Any) -> None:
    # Proves the test above can see a script run: the same click on the
    # ASCII spelling changes the title.
    page.set_content(_PAGE)
    page.evaluate(
        "() => { const a = document.createElement('a'); a.href = \"javascript:void(document.title='ran')\";"
        " a.id = 'go'; a.textContent = 'go'; document.body.append(a); }"
    )
    page.click("#go")
    page.wait_for_function("() => document.title === 'ran'")
