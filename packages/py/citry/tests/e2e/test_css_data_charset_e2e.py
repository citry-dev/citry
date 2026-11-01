"""
Browser e2e: a `css_data()` stylesheet keeps its rules on a page in each listed encoding.

Citry serves the stylesheet as UTF-8 bytes. A browser that is not told the
charset decodes it with the encoding of the page that links it. On a page in
GBK or Big5, the last byte of a non-ASCII character pairs with the next ASCII
byte and can swallow the backslash of an escaped quote, so a value that the
`css_data()` check accepts would end its string early and add a rule of its own.
The first test loads the real route into a page in each encoding and counts the
rules. The second puts the same values inline in a page whose bytes are UTF-8
but whose label names another encoding, so the browser reads the `<style>`
element with the wrong one.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

# Each value is one quoted string that the `css_data()` check accepts. If the
# browser read the backslash as half of another character, the quote after it
# would end the string and `.evil` would become a rule.
_VALUES = {
    "chinese_character": '"表\\";}.evil{--evil:1}"',
    "kana": '"あ\\";}.evil{--evil:1}"',
    # ESC switches an ISO-2022-JP decoder to a two-byte mode for the bytes after it.
    "escape_character": '"\x1b$B\\";}.evil{--evil:1}"',
}

# The encoding the page declares, and the name the browser reports for it.
_ENCODINGS = {
    "utf-8": "utf-8",
    "gbk": "gbk",
    "big5": "big5",
    "shift_jis": "shift_jis",
    "euc-kr": "euc-kr",
    "iso-2022-jp": "iso-2022-jp",
}

_READ_SHEET = """
() => {
  const sheet = document.styleSheets[0];
  const rules = [...sheet.cssRules];
  return {
    characterSet: document.characterSet.toLowerCase(),
    selectors: rules.map((rule) => rule.selectorText),
    y: rules[0].style.getPropertyValue('--y').trim(),
  };
}
"""


@pytest.mark.parametrize("encoding", _ENCODINGS)
@pytest.mark.parametrize("value", _VALUES.values(), ids=list(_VALUES))
def test_a_linked_css_data_stylesheet_keeps_its_rules_on_a_page_in_each_encoding(
    page: Any, serve_live: Any, encoding: str, value: str
) -> None:
    app = Citry()
    app.set_mounted_prefix("/citry")

    class Themed(Component):
        citry = app
        template = '<div class="themed">themed</div>'
        css = ".themed { color: var(--x); }"

        def css_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            # `y` follows `x`, so a string that ended early would lose it.
            return {"x": value, "y": "1"}

    rendered = Themed().render()
    fragment_html = rendered.serialize(deps_strategy="fragment")
    record = next(item for item in rendered.context.extra["dependencies"] if item.class_id == Themed.class_id)
    assert record.css_vars_hash is not None

    base = serve_live(app, "<html></html>", fragment_html)
    sheet_url = f"/citry/cache/{Themed.class_id}.{record.css_vars_hash}.css"
    page_html = f'<!doctype html><link rel="stylesheet" href="{sheet_url}"><p>text</p>'
    # Only the page is answered here, in the encoding under test; the stylesheet
    # comes from Citry's own route on the live server.
    page.route(
        base + "/page",
        lambda route: route.fulfill(
            body=page_html.encode(encoding), headers={"content-type": f"text/html; charset={encoding}"}
        ),
    )
    page.goto(base + "/page")
    page.wait_for_load_state("load")

    result = page.evaluate(_READ_SHEET)
    # The browser really read the page in that encoding, so the test tried it.
    assert result["characterSet"] == _ENCODINGS[encoding]
    # One rule holds the variables; no rule appeared, and `y` was not lost.
    assert len(result["selectors"]) == 1
    assert result["selectors"][0].startswith("[data-ccss-")
    assert result["y"] == "1"
    # The header and the escape each keep the rules on their own, so this test
    # passes with either one; the unit tests check each layer.


_MISLABELLED = ("gbk", "big5", "shift_jis")


@pytest.mark.parametrize("label", _MISLABELLED)
@pytest.mark.parametrize("value", _VALUES.values(), ids=list(_VALUES))
def test_an_inline_css_data_stylesheet_keeps_its_rules_when_the_page_label_is_wrong(
    page: Any, serve_document: Any, label: str, value: str
) -> None:
    app = Citry()

    class Themed(Component):
        citry = app
        template = '<div class="themed">themed</div>'
        css = ".themed { color: var(--x); }"

        def css_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"x": value, "y": "1"}

    class Page(Component):
        citry = app
        template = """
          <html>
            <head><c-css /></head>
            <body><c-themed /></body>
          </html>
        """

    html = Page().render().serialize(deps_strategy="document")
    base = serve_document("<html></html>")
    # The bytes are UTF-8 but the label says otherwise, as when a server or a proxy
    # mislabels a page, so the browser decodes the inline <style> with the wrong encoding.
    page.route(
        base + "/page",
        lambda route: route.fulfill(
            body=html.encode("utf-8"), headers={"content-type": f"text/html; charset={label}"}
        ),
    )
    page.goto(base + "/page")

    result = page.evaluate(
        """
        () => {
          const rules = [...document.styleSheets].flatMap((sheet) => [...sheet.cssRules]);
          const vars = rules.find((rule) => (rule.selectorText || '').startsWith('[data-ccss-'));
          return {
            selectors: rules.map((rule) => rule.selectorText),
            y: vars ? vars.style.getPropertyValue('--y').trim() : null,
          };
        }
        """
    )
    assert ".evil" not in result["selectors"]
    assert result["y"] == "1"
