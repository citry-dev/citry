"""
Rules for an attribute name that is chosen while the page renders.

A name that comes from data (a `c-bind` mapping key, or a name an
`on_attrs_resolved` hook adds) must be a plain HTML attribute name, and it
may not be one the browser reads as code or markup. A name the author writes
in the template is not data, so it keeps working on a plain or static element.
(A `<c-element>` with `c-is` or `c-bind` cannot tell a written name from one
passed in as data, so it refuses a template-written handler too.)
"""

from __future__ import annotations

from collections import UserDict
from typing import Any

import pytest

from citry import Citry, Component, Extension
from citry._vue.capture import render_prepared

_TEMPLATE_SHAPES = {
    "plain": '<div c-bind="attrs">x</div>',
    "c-element": '<c-element is="div" c-bind="attrs">x</c-element>',
    # A page with browser code goes through the Vue renderer.
    "vue": '<div c-bind="attrs">x</div>',
    "vue-prepared": '<div c-bind="attrs">x</div>',
}


def _render_spread(shape: str, key: str) -> str:
    """Render a page whose `c-bind` mapping holds the single key `key`."""
    app = Citry(autodiscover=False, extensions=[])
    uses_vue = shape.startswith("vue")

    class Page(Component):
        citry = app
        template = _TEMPLATE_SHAPES[shape]
        if uses_vue:
            js = """
                $component({});
            """

        def template_data(self, kwargs, slots):
            return {"attrs": {key: "x"}}

    if shape == "vue-prepared":
        # This is the render the Vue compiler reads, so it needs the same refusal.
        return str(render_prepared(Page()))
    return str(Page())


@pytest.mark.parametrize("shape", list(_TEMPLATE_SHAPES))
@pytest.mark.parametrize("key", ["onclick", "ONMOUSEOVER", "innerHTML", "outerHTML", "SrcDoc"])
def test_spread_keys_may_not_name_code_reading_attributes(shape: str, key: str) -> None:
    # The browser reads these values as code or markup, in any letter case.
    with pytest.raises(ValueError, match="start with 'on'"):
        _render_spread(shape, key)


def test_spread_key_error_says_how_to_fix_it() -> None:
    # The mapping may belong to a component's `attrs` input, so the message tells the
    # author to remove the key rather than to rewrite a template they may not own.
    with pytest.raises(ValueError, match="Remove the key from the mapping"):
        _render_spread("plain", "onclick")


@pytest.mark.parametrize("shape", ["plain", "vue"])
@pytest.mark.parametrize("key", ["title", "data-x", "aria-label"])
def test_spread_keys_that_read_no_code_still_render(shape: str, key: str) -> None:
    # Control: the same spread with an ordinary name renders, so the refusals above
    # come from the name and not from the spread itself.
    assert f'{key}="x"' in _render_spread(shape, key)


@pytest.mark.parametrize("key", ["onclick", "innerHTML", "SrcDoc"])
def test_spread_keys_may_not_name_code_reading_attributes_beside_a_translation_binding(key: str) -> None:
    # An element with a `$c-tr` binding reads its `c-bind` mapping on its own path,
    # so that path needs the same refusal.
    app = Citry(autodiscover=False, extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}})

    class Page(Component):
        citry = app
        messages = "save = Save"
        template = """
            <div
              c-bind="attrs"
              c-aria-label="tr('save')"
              $c-tr:save[aria-label]
            >x</div>
        """

        def template_data(self, kwargs, slots):
            return {"attrs": {key: "x"}}

    with pytest.raises(ValueError, match="start with 'on'"):
        str(Page())


@pytest.mark.parametrize("shape", list(_TEMPLATE_SHAPES))
@pytest.mark.parametrize(
    "key",
    [
        pytest.param("x\x0cy", id="form-feed"),
        pytest.param("a\x00b", id="nul"),
        pytest.param("a\ufeffb", id="byte-order-mark"),
        pytest.param("a\x7fb", id="delete"),
        pytest.param("a\x85b", id="c1-control"),
        pytest.param('a"b', id="double-quote"),
        pytest.param("a'b", id="single-quote"),
        pytest.param("a\ufdd0b", id="noncharacter-fdd0"),
        pytest.param("a\ufdefb", id="noncharacter-fdef"),
        pytest.param("a\ufffeb", id="noncharacter-fffe"),
        pytest.param("a\U0001fffeb", id="noncharacter-plane-1"),
        pytest.param("a\U0010ffffb", id="noncharacter-last-plane"),
        pytest.param("a\ud800b", id="lone-surrogate"),
        pytest.param("a<b", id="less-than"),
        pytest.param("a>b", id="greater-than"),
        pytest.param("a=b", id="equals"),
        pytest.param("a/b", id="slash"),
        pytest.param("a b", id="space"),
    ],
)
def test_spread_keys_may_only_use_html_attribute_name_characters(shape: str, key: str) -> None:
    # These characters are not allowed in an attribute name.
    with pytest.raises(ValueError, match="invalid HTML attribute name"):
        _render_spread(shape, key)


class _HiddenKeysDict(dict):
    """A dict whose iteration and `keys()` leave out some items; the check must cover every item."""

    def __iter__(self):
        return iter(["data-x"])

    def keys(self):
        return ["data-x"]


class _UserDictMapping(UserDict):
    """A mapping that is not a dict, which Citry copies into a plain dict."""


_HOOK_TEMPLATES = {
    "plain": '<div c-onclick="handler">x</div>',
    "i18n-binding": """
        <div
          c-onclick="handler"
          c-aria-label="tr('save')"
          $c-tr:save[aria-label]
        >x</div>
    """,
    "c-element": '<c-element is="div" c-onclick="handler">x</c-element>',
}


def _render_with_hook(template: str, mode: str, calls: list[str]) -> str:
    """Render `template` with an extension whose `on_attrs_resolved` hook runs `mode`."""

    class Hook(Extension):
        name = "hook"

        def on_attrs_resolved(self, ctx):
            attrs = dict(ctx.attrs)
            if mode == "add":
                attrs["onmouseover"] = "x"
            elif mode == "rename":
                attrs["onmouseover"] = attrs.pop("onclick")
            elif mode == "add-harmless":
                attrs["data-x"] = "1"
            elif mode == "hidden-keys":
                attrs = _HiddenKeysDict({**attrs, "data-x": "1", "onmouseover": "x"})
            elif mode == "mapping-subclass":
                attrs = _UserDictMapping({**attrs, "onmouseover": "x"})
            # The hook returns normally, so a refusal can only come from Citry's own check.
            calls.append(mode)
            return attrs

    app = Citry(
        autodiscover=False,
        extensions=[Hook],
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )

    class Page(Component):
        citry = app
        messages = "save = Save"

        def template_data(self, kwargs, slots):
            return {"handler": "h", "tag": "div"}

    Page.template = template
    return str(Page())


@pytest.mark.parametrize("shape", list(_HOOK_TEMPLATES))
@pytest.mark.parametrize("mode", ["add", "rename", "hidden-keys", "mapping-subclass"])
def test_attrs_hooks_may_not_add_code_reading_names(shape: str, mode: str) -> None:
    # A hook is extension code, not the template author, so a name it adds (or a
    # written one it renames) is data. The browser would read its value as code.
    calls: list[str] = []
    with pytest.raises(ValueError, match="start with 'on'") as excinfo:
        _render_with_hook(_HOOK_TEMPLATES[shape], mode, calls)
    assert calls == [mode]
    # The message tells the extension author the fix for a hook.
    assert "may change the value of an attribute the template wrote" in str(excinfo.value)


def test_attrs_hooks_may_not_add_code_reading_names_to_a_dynamic_element() -> None:
    # A `<c-element c-is>` takes the tag from data and formats its attributes on another path.
    calls: list[str] = []
    template = '<c-element c-is="tag">x</c-element>'
    with pytest.raises(ValueError, match="start with 'on'") as excinfo:
        _render_with_hook(template, "add", calls)
    assert calls == ["add"]
    assert "may change the value of an attribute the template wrote" in str(excinfo.value)


@pytest.mark.parametrize("shape", list(_HOOK_TEMPLATES))
def test_attrs_hooks_may_not_add_code_reading_names_but_keep_written_handlers(shape: str) -> None:
    # Control: a hook that adds a harmless name leaves the author's `c-onclick` in place.
    calls: list[str] = []
    html = _render_with_hook(_HOOK_TEMPLATES[shape], "add-harmless", calls)
    assert calls == ["add-harmless"]
    assert 'onclick="h"' in html
    assert 'data-x="1"' in html


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        pytest.param('<div onclick="x">y</div>', 'onclick="x"', id="literal"),
        pytest.param('<div c-onclick="handler">y</div>', 'onclick="h"', id="dynamic-value"),
        pytest.param('<c-element is="div" onclick="x">y</c-element>', 'onclick="x"', id="c-element-literal"),
        pytest.param(
            '<c-element is="div" c-onclick="handler">y</c-element>', 'onclick="h"', id="c-element-dynamic-value"
        ),
    ],
)
def test_template_written_handlers_still_render(template: str, expected: str) -> None:
    # The template author wrote the name, so it is not data. Only a name chosen
    # at render time is refused.
    app = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots) -> dict[str, Any]:
            return {"handler": "h"}

    Page.template = template
    html = str(Page())
    assert expected in html
    assert ">y</div>" in html


def test_template_written_handler_renders_on_a_page_with_browser_code() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = app
        template = '<div onclick="x">y</div>'
        js = """
            $component({});
        """

    html = str(Page())
    assert 'onclick="x"' in html
    assert ">y</div>" in html


# Names Citry uses to find its own placeholders and elements, in the server, the
# render cache, and the browser code. A name from data must not be able to write one.
_CITRY_MARKER_NAMES = [
    "c-render-id",
    "C-Render-Id",
    "data-cid",
    "DATA-CID-abc",
    "data-ccss-x",
    "data-citry",
    "data-citry-vue-document",
    "data-citry-vue-fragment",
    "data-citry-css-url",
    "data-citry-key",
    "data-citry-morph",
    "data-citry-i18n-binding",
    "data-citry-opaque-root",
    "data-citry-security-x",
    "data-citry-omit-handler-x",
]

_MARKER_SHAPES = {
    **_TEMPLATE_SHAPES,
    "c-element-dynamic": '<c-element c-is="tag" c-bind="attrs">x</c-element>',
    "vue-prepared-c-element": '<c-element c-is="tag" c-bind="attrs">x</c-element>',
}


def _render_marker_spread(shape: str, key: str) -> str:
    """Render a page whose `c-bind` mapping holds the single key `key`, on any marker shape."""
    app = Citry(autodiscover=False, extensions=[])
    uses_vue = shape.startswith("vue")

    class Page(Component):
        citry = app
        template = _MARKER_SHAPES[shape]
        if uses_vue:
            js = """
                $component({});
            """

        def template_data(self, kwargs, slots):
            return {"attrs": {key: "x"}, "tag": "div"}

    if shape.startswith("vue-prepared"):
        return str(render_prepared(Page()))
    return str(Page())


@pytest.mark.parametrize("shape", list(_MARKER_SHAPES))
@pytest.mark.parametrize("key", _CITRY_MARKER_NAMES)
def test_spread_keys_may_not_name_citry_markers(shape: str, key: str) -> None:
    # A data-chosen `c-render-id` on an empty `<template>` would make the server copy
    # another component's HTML there; the other names steer Citry's browser code.
    with pytest.raises(ValueError, match=r"Citry reserves") as excinfo:
        _render_marker_spread(shape, key)
    assert repr(key) in str(excinfo.value)


@pytest.mark.parametrize("shape", list(_MARKER_SHAPES))
@pytest.mark.parametrize(
    "key",
    [
        "data-x",
        "data-cidr",
        "data-ccssx",
        "data-citryx",
        # Citry UI writes names under `data-citry-` through `c-bind`, so only the
        # names core Citry reads are refused.
        "data-citry-ui-part",
        # The browser lowercases only ASCII letters, so these are different names.
        pytest.param("data-cİd-x", id="dotted-capital-i"),
        pytest.param("c-render-İd", id="render-id-dotted-capital-i"),
    ],
)
def test_spread_keys_close_to_citry_markers_still_render(shape: str, key: str) -> None:
    # Control: these names only look like reserved ones and still render, so the
    # check above refuses exact reserved names, not look-alikes.
    assert f'{key}="x"' in _render_marker_spread(shape, key)


@pytest.mark.parametrize("shape", ["plain", "vue"])
@pytest.mark.parametrize("key", ["data-cev-x", "DATA-CITRY-RUNTIME-EVENTS"])
def test_spread_keys_in_the_events_namespace_keep_their_own_error(shape: str, key: str) -> None:
    # The Events names are refused first, with the error that names the Events fix.
    with pytest.raises(RuntimeError, match="reserved internal Events namespace"):
        _render_spread(shape, key)


@pytest.mark.parametrize("key", ["c-render-id", "data-cid-x", "data-citry-vue-fragment"])
def test_spread_keys_may_not_name_citry_markers_beside_a_translation_binding(key: str) -> None:
    # An element with a `$c-tr` binding reads its `c-bind` mapping in separate code
    # (the i18n extension), so it needs its own test.
    app = Citry(autodiscover=False, extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}})

    class Page(Component):
        citry = app
        messages = "save = Save"
        template = """
            <div
              c-bind="attrs"
              c-aria-label="tr('save')"
              $c-tr:save[aria-label]
            >x</div>
        """

        def template_data(self, kwargs, slots):
            return {"attrs": {key: "x"}}

    with pytest.raises(ValueError, match=r"Citry reserves"):
        str(Page())


def test_spread_key_marker_error_says_how_to_fix_it() -> None:
    with pytest.raises(ValueError, match="Remove the key from the mapping, or rename it"):
        _render_marker_spread("plain", "data-cid-x")


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        pytest.param('<div data-cid-q c-c-render-id="tag">y</div>', 'data-cid-q c-render-id="div"', id="plain"),
        pytest.param('<c-element is="div" data-cid-q>y</c-element>', "data-cid-q", id="c-element-static-is"),
    ],
)
def test_template_written_marker_names_still_render(template: str, expected: str) -> None:
    # The template author wrote the name, so it is not data. These elements compile
    # to plain tags, so Citry knows the name came from the template.
    app = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots) -> dict[str, Any]:
            return {"tag": "div"}

    Page.template = template
    assert expected in str(Page())


def test_dynamic_element_refuses_a_template_written_marker_name() -> None:
    # A `<c-element c-is>` receives every name as data, so it refuses a written
    # marker name too, as it does a written handler.
    app = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = app
        template = '<c-element c-is="tag" data-cid-q>y</c-element>'

        def template_data(self, kwargs, slots) -> dict[str, Any]:
            return {"tag": "div"}

    with pytest.raises(ValueError, match="refuses both") as excinfo:
        str(Page())
    assert "Citry reserves" in str(excinfo.value)


@pytest.mark.parametrize("shape", ["plain", "vue", "vue-prepared"])
def test_attrs_hook_may_add_a_reserved_name_to_a_dynamic_element(shape: str) -> None:
    # A hook is extension code, so it may add reserved names (the Events extension
    # adds `data-cev-*`), on a page with or without Vue alike.
    class Hook(Extension):
        name = "hook"

        def on_attrs_resolved(self, ctx):
            return {**ctx.attrs, "data-ccss-hook": ""}

    app = Citry(autodiscover=False, extensions=[Hook])

    class Page(Component):
        citry = app
        template = '<c-element c-is="tag">y</c-element>'
        if shape != "plain":
            js = """
                $component({});
            """

        def template_data(self, kwargs, slots) -> dict[str, Any]:
            return {"tag": "div"}

    html = str(render_prepared(Page())) if shape == "vue-prepared" else str(Page())
    assert "data-ccss-hook" in html


def test_attrs_hook_adding_the_private_key_attribute_conflicts_with_c_key() -> None:
    # An extension hook is extension code, so it may add marker names (the Events
    # extension adds `data-cev-*`). The `#c-key` attribute is still checked after it.
    class Hook(Extension):
        name = "hook"

        def on_attrs_resolved(self, ctx):
            return {**ctx.attrs, "data-citry-key": "forged"}

    app = Citry(autodiscover=False, extensions=[Hook])

    class Page(Component):
        citry = app
        template = """<c-element c-is="tag" #c-key="'row'">y</c-element>"""

        def template_data(self, kwargs, slots) -> dict[str, Any]:
            return {"tag": "div"}

    with pytest.raises(ValueError, match=r"conflicts with its private #c-key metadata"):
        str(Page())
