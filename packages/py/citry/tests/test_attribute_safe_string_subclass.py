"""
Tests for trusted HTML written into an attribute when its `str()` keeps `__html__`.

Django's `SafeString` (from `mark_safe` or `format_html`) is a `str` subclass
with `__html__`, and its `str()` returns the same object. Citry decodes such a
value to the text a browser reads and then escapes it for the attribute, so a
`"` inside it must not end the attribute, as for `Markup`.

`#c-key` on an HTML element has its own writer on the node path (the older
node classes that render a template compiled without the capture step), so
its tests reuse the routes of `test_node_path_attribute_values.py`.
"""

from __future__ import annotations

import pytest

import citry.util.html as html_util
from citry import Citry, Component, Markup, format_attrs
from citry.util.html import escape_attribute_value
from tests.test_node_path_attribute_values import _NODE_ROUTES, _target_attributes
from tests.test_node_path_attribute_values import _render as _render_route

_BREAKOUT = 'x" onmouseover="alert(1)" y="'
_ESCAPED = "x&#34; onmouseover=&#34;alert(1)&#34; y=&#34;"


class _SafeLike(str):
    """Behaves like Django's `SafeString`: `__html__` and `str()` both return the same object."""

    __slots__ = ()

    def __html__(self):
        return self

    def __str__(self):
        return self


def _render(template, value):
    app = Citry()

    class Child(Component):
        citry = app
        template = """
            <span :class="{a: true}">c</span>
        """

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {"v": value}

    Page.template = template
    return Page().render().serialize()


def test_escape_attribute_value_escapes_a_subclass_that_keeps_html():
    assert escape_attribute_value(_SafeLike(_BREAKOUT)) == _ESCAPED


def test_format_attrs_escapes_a_subclass_that_keeps_html():
    assert format_attrs({"title": _SafeLike(_BREAKOUT)}) == f'title="{_ESCAPED}"'


@pytest.mark.parametrize(
    "template",
    [
        pytest.param('<div c-title="v">x</div>', id="c-attribute"),
        pytest.param("""<div c-bind="{'title': v}">x</div>""", id="c-bind"),
        pytest.param('<c-element is="div" c-title="v">x</c-element>', id="c-element"),
    ],
)
def test_rendered_attribute_escapes_a_subclass_that_keeps_html(template):
    html = _render(template, _SafeLike(_BREAKOUT))

    assert f'title="{_ESCAPED}"' in html
    assert ' onmouseover="' not in html


def test_django_safestring_is_escaped_in_an_attribute():
    safestring = pytest.importorskip("django.utils.safestring")

    html = _render('<div c-title="v">x</div>', safestring.mark_safe(_BREAKOUT))

    assert f'title="{_ESCAPED}"' in html


def test_vue_attribute_takes_a_subclass_that_keeps_html():
    # A component with a Vue binding sends the value to the browser as JSON,
    # which accepts only an exact str.
    html = _render('<div c-title="v" :class="{a: true}">x</div>', _SafeLike(_BREAKOUT))

    assert ' onmouseover="' not in html


class _TextGivesSafeLike:
    """Like a lazy `mark_safe(...)` value: no `__html__` itself, but its `str()` returns a `SafeString`."""

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return _SafeLike(self.text)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(_SafeLike(_BREAKOUT), id="keeps-html"),
        pytest.param(_TextGivesSafeLike(_BREAKOUT), id="str-gives-keeps-html"),
        pytest.param(Markup(_BREAKOUT), id="markup"),  # noqa: S704 - a fixed test value
    ],
)
def test_exact_str_of_str_drops_the_subclass(value):
    text = html_util.exact_str(str(value))

    assert type(text) is str
    assert text == _BREAKOUT


class TestElementKey:
    """`#c-key` writes the key as escaped text on the node path, whatever the value's class."""

    @pytest.mark.parametrize("route", _NODE_ROUTES)
    def test_key_escapes_a_subclass_that_keeps_html(self, route):
        html = _render_route(route, '<div id="t" #c-key="v">x</div>', {"v": _SafeLike(_BREAKOUT)})
        attrs = _target_attributes(html)

        assert "onmouseover" not in attrs
        assert attrs["data-citry-key"] == ":" + _BREAKOUT

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param(
                """<ul><c-for each="i in [1]"><li id="t" #c-key="v">x</li></c-for></ul>""",
                id="loop",
            ),
            pytest.param('<c-element is="div" id="t" #c-key="v">x</c-element>', id="c-element"),
        ],
    )
    def test_key_in_a_loop_or_dynamic_element_escapes_a_subclass_that_keeps_html(self, template):
        html = _render_route("kept-slot", template, {"v": _SafeLike(_BREAKOUT)})
        attrs = _target_attributes(html)

        assert "onmouseover" not in attrs
        assert attrs["data-citry-key"] == ":" + _BREAKOUT

    def test_django_template_extension_escapes_a_django_key(self):
        # The shape of an app that uses an extension for Django template
        # syntax: its templates render on the node path on every request.
        safestring = pytest.importorskip("django.utils.safestring")

        html = _render_route(
            "foreign-span",
            '<div id="t" #c-key="v">x</div>',
            {"v": safestring.mark_safe(_BREAKOUT)},
        )
        attrs = _target_attributes(html)

        assert "onmouseover" not in attrs
        assert attrs["data-citry-key"] == ":" + _BREAKOUT

    def test_vue_key_takes_a_subclass_that_keeps_html(self):
        # A page with Vue sends the key to the browser as JSON, which accepts
        # only an exact str.
        html = _render('<div id="t" #c-key="v" :class="{a: true}">x</div>', _SafeLike(_BREAKOUT))

        assert ' onmouseover="' not in html

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param('<c-Child #c-key="v" />', id="component"),
            pytest.param(
                """<div :class="{b: true}"><c-for each="i in [v]"><c-Child #c-key="i" /></c-for></div>""",
                id="component-in-loop",
            ),
        ],
    )
    def test_vue_component_key_takes_a_subclass_that_keeps_html(self, template):
        # A component's key on a page with Vue must be an exact str; it is
        # identity text and is never written as an attribute.
        html = _render(template, _SafeLike(_BREAKOUT))

        assert ' onmouseover="' not in html
