"""
Browser e2e: a `css_data()` value that the check accepts adds no rule once Citry escapes it.

The check reads each value as written, and Citry then writes control and
non-ASCII characters as CSS hex escapes. The browser reads an escape as part
of a name, so an escaped character must not change where the browser thinks a
name, URL or string starts. Each value below puts such a character right
before `url(`, followed by text that would add a page-wide rule if the
browser read it differently from the check. The test loads Citry's own
stylesheet route and checks that the page keeps its color and the sheet keeps
one rule.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.util.css import _escape_beyond_printable_ascii

pytestmark = pytest.mark.e2e

# Text that would end the declaration and its rule, then color the page,
# if the browser read the `url(` before it as a function call.
_TAIL = 'url(/*)"*/)}html{background:green}.z{"'

# Values the check accepts. In each, the character before `url(` is written
# as an escape, and the browser must read the same tokens the check read.
_ACCEPTED = {
    "control_character_in_a_string": f'"\x01"{_TAIL}',
    "delete_in_a_string": f'"\x7f"{_TAIL}',
    "non_ascii_letter_before_a_function": 'éurl("*/)}html{background:green}.z{")',
}

_READ_PAGE = """
() => ({
  background: getComputedStyle(document.documentElement).backgroundColor,
  selectors: [...document.styleSheets[0].cssRules].map((rule) => rule.selectorText),
  y: document.styleSheets[0].cssRules[0].style.getPropertyValue('--y').trim(),
})
"""

_GREEN = "rgb(0, 128, 0)"


@pytest.mark.parametrize("value", _ACCEPTED.values(), ids=list(_ACCEPTED))
def test_an_accepted_css_data_value_adds_no_rule_once_escaped(page: Any, serve_live: Any, value: str) -> None:
    app = Citry()
    app.set_mounted_prefix("/citry")

    class Themed(Component):
        citry = app
        template = """
            <div class="themed">themed</div>
        """
        css = """
            .themed { color: var(--x); }
        """

        def css_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            # `y` follows `x`, so a value that ended its declaration early would lose it.
            return {"x": value, "y": "1"}

    rendered = Themed().render()
    fragment_html = rendered.serialize(deps_strategy="fragment")
    record = next(item for item in rendered.context.extra["dependencies"] if item.class_id == Themed.class_id)
    assert record.css_vars_hash is not None

    base = serve_live(app, "<html></html>", fragment_html)
    sheet_url = f"/citry/cache/{Themed.class_id}.{record.css_vars_hash}.css"
    page.route(
        base + "/page",
        lambda route: route.fulfill(
            body=f'<!doctype html><link rel="stylesheet" href="{sheet_url}"><p>text</p>',
            headers={"content-type": "text/html; charset=utf-8"},
        ),
    )
    page.goto(base + "/page")
    page.wait_for_load_state("load")

    result = page.evaluate(_READ_PAGE)
    assert result["background"] != _GREEN
    assert len(result["selectors"]) == 1
    assert result["selectors"][0].startswith("[data-ccss-")
    assert result["y"] == "1"


def test_the_page_turns_green_when_an_escape_changes_the_tokens(page: Any) -> None:
    # Proves the check above can see a break: a control character before
    # `url(`, escaped without the check, makes the browser read a function
    # call where the check would read a URL, and the tail colors the page.
    # Citry refuses this value, so it is written here by hand.
    declaration = _escape_beyond_printable_ascii(f"\x01{_TAIL}")
    page.set_content(f"<!doctype html><style>.x {{\n  --x: {declaration};\n  --y: 1;\n}}</style><p>text</p>")

    result = page.evaluate(_READ_PAGE)
    assert result["background"] == _GREEN
