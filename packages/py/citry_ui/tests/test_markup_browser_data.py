"""Trusted HTML strings reach the browser data of `CButton` and `CAvatar` as the text the server writes."""

from __future__ import annotations

import json
import re
from html import unescape

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component


class _SelfReturningSafeString(str):
    """Stands in for Django's `SafeString`: `__html__` and `str()` both return the object itself."""

    __slots__ = ()

    def __html__(self) -> str:
        return self

    def __str__(self) -> str:
        return self


# Each kind of value an app can hand over for an attribute. The trusted ones
# hold HTML, so the browser reads `&amp;` in them as `&`.
_KINDS = {
    "str": str,
    "Markup": Markup,
    "SafeString": _SelfReturningSafeString,
}


def _render(source: str, **data: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data

    return str(Page())


def _json_string(html: str, key: str) -> str:
    """Return the first JSON string value under `key` in the page's browser data."""
    match = re.search(rf'"{key}":("(?:[^"\\]|\\.)*")', html)
    assert match is not None, f"no {key!r} in the browser data"
    return json.loads(match.group(1))


def _attribute(html: str, tag: str, name: str) -> str:
    """Return the value of `name` on the first `tag` element, as the browser reads it."""
    match = re.search(rf'<{tag}\b[^>]*\s{name}="([^"]*)"', html)
    assert match is not None, f"no {name!r} on <{tag}>"
    return unescape(match.group(1))


@pytest.mark.parametrize("kind", list(_KINDS))
def test_cbutton_href_reaches_the_browser_as_the_server_writes_it(kind: str) -> None:
    href = _KINDS[kind]("/search?q=a&amp;page=2")
    html = _render('<c-CButton c-href="href">Search</c-CButton>', href=href)
    # The server reads trusted HTML's `&amp;` as `&`; a plain `str` is text,
    # so its `&amp;` stays as typed. The browser data must agree either way.
    expected = "/search?q=a&amp;page=2" if kind == "str" else "/search?q=a&page=2"
    assert _attribute(html, "a", "href") == expected
    assert _json_string(html, "href") == expected


@pytest.mark.parametrize("kind", list(_KINDS))
def test_cbutton_tabindex_reaches_the_browser_as_text(kind: str) -> None:
    html = _render(
        '<c-CButton href="/a" c-attrs="attrs">Go</c-CButton>',
        attrs={"tabindex": _KINDS[kind]("3")},
    )
    assert _json_string(html, "tabIndex") == "3"


@pytest.mark.parametrize("kind", list(_KINDS))
@pytest.mark.parametrize("src", [None, "/avatar.png"], ids=["browser-image", "server-image"])
def test_cavatar_img_attrs_reach_the_browser_as_the_server_writes_them(kind: str, src: str | None) -> None:
    title = _KINDS[kind]("Tom &amp; &quot;Jerry&quot;")
    html = _render('<c-CAvatar alt="Tom" c-src="src" c-img_attrs="attrs" />', src=src, attrs={"title": title})
    expected = "Tom &amp; &quot;Jerry&quot;" if kind == "str" else 'Tom & "Jerry"'
    data = json.loads(re.search(r'"imgAttrs":(\{[^}]*\})', html).group(1))  # type: ignore[union-attr]
    assert data == {"title": expected}
    # With `src`, the server writes the image itself; without it, the
    # browser code creates the image from the data above.
    if src is not None:
        assert _attribute(html, "img", "title") == expected


def test_cbutton_tabindex_true_reaches_the_browser_as_the_server_writes_it() -> None:
    html = _render('<c-CButton href="/a" c-attrs="attrs">Go</c-CButton>', attrs={"tabindex": True})
    assert _attribute(html, "a", "tabindex") == "true"
    assert _json_string(html, "tabIndex") == "true"
