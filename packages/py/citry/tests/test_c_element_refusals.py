"""
Tests for what `<c-element>` refuses while a page renders.

The tag name and the attribute names of `<c-element>` can come from data
(`c-is`, `c-bind`, `<c-component c-is>`, or a direct Python call), so the
element checks each one itself. The ordinary server render and the Vue
render (a component with `js`) must refuse the same names.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

import citry.components.dynamic as dynamic_element
import citry.util.html as html_util
from citry import Citry, Component
from citry._vue.capture import (
    PreparedDynamicElementClose,
    PreparedDynamicElementOpen,
    UnsupportedPreparedView,
    render_prepared_direct,
)
from citry._vue.direct_capture import assemble_typed_render
from citry.citry_render import CitryRender

# An independent copy of the contract: tags that the browser handles in a
# special way (it runs or loads them, reads their contents as raw text, or
# changes how it reads the rest of the page). It is written out here, not
# imported, so a change to the library's list has to change this one too.
REFUSED_TAGS = frozenset(
    {
        "applet",
        "base",
        "embed",
        "frame",
        "frameset",
        "iframe",
        "link",
        "meta",
        "noembed",
        "noframes",
        "noscript",
        "object",
        "plaintext",
        "script",
        "style",
        "template",
        "textarea",
        "title",
        "xmp",
    }
)

# "server" renders the page as HTML text. "vue" renders a component that has
# `js`, through the prepared capture the Vue page is built from.
RENDER_PATHS = ("server", "vue")


def _mixed_case(tag: str) -> str:
    """Return the tag with every second letter in upper case, such as `sCrIpT`."""
    return "".join(char.upper() if index % 2 else char for index, char in enumerate(tag))


def _render_page(template: str, data: dict[str, Any], *, path: str) -> str:
    """Render a one-component page on the chosen render path and return its HTML."""
    registry = Citry(autodiscover=False)
    source = template
    values = data

    if path == "vue":

        class VuePage(Component):
            citry = registry

            def template_data(self, kwargs, slots):
                return values

            template = source

            # The `js` makes the component a Vue component, so it takes the Vue render.
            js = """
                export default { data() { return { count: 1 } } }
            """

        return str(render_prepared_direct(VuePage()))

    class ServerPage(Component):
        citry = registry

        def template_data(self, kwargs, slots):
            return values

        template = source

    return str(ServerPage())


def test_refused_dynamic_element_tags_match_the_contract() -> None:
    """The library's list of refused tags is exactly the contract above."""
    assert html_util._REFUSED_DYNAMIC_ELEMENT_TAGS == REFUSED_TAGS


@pytest.mark.parametrize("path", RENDER_PATHS)
@pytest.mark.parametrize(
    "spelling",
    [str.lower, str.upper, _mixed_case],
    ids=["lower", "upper", "mixed"],
)
@pytest.mark.parametrize("tag", sorted(REFUSED_TAGS))
def test_c_element_refuses_special_tags(tag: str, spelling: Any, path: str) -> None:
    """
    `<c-element>` refuses a tag the browser handles in a special way, in any letter case.

    Citry escapes an element's body as HTML text, which does not fit these
    tags, so a `<c-element>` with `c-is` or `c-bind` may not name one.
    """
    template = """
        <c-element c-is="tag">x</c-element>
    """

    with pytest.raises(ValueError, match="cannot render a <"):
        _render_page(template, {"tag": spelling(tag)}, path=path)


@pytest.mark.parametrize("path", RENDER_PATHS)
@pytest.mark.parametrize("tag", ["div", "my-widget", "clipPath"])
def test_c_element_still_renders_ordinary_tags(tag: str, path: str) -> None:
    """A plain tag, a custom element name, and a camel-case SVG name are not refused."""
    template = """
        <c-element c-is="tag">x</c-element>
    """

    html = _render_page(template, {"tag": tag}, path=path)

    assert f"<{tag}" in html
    assert f"</{tag}>" in html


@pytest.mark.parametrize("path", RENDER_PATHS)
@pytest.mark.parametrize(
    "attrs",
    [
        {"IS": "section", "onclick": "x"},
        {"IS": "section", "OnClick": "x"},
        {"IS": "section", "srcdoc": "x"},
    ],
    ids=["onclick", "mixed-case-onclick", "srcdoc"],
)
def test_c_element_checks_every_attribute_name(attrs: dict[str, str], path: str) -> None:
    """
    `<c-component c-is="'element'" c-bind>` passes its mapping on to `<c-element>`, which checks each name.

    The `IS` key picks the tag, so the same mapping also shows the check
    applies to a name that is not the first or the only one.
    """
    template = """
        <c-component
            c-is="'element'"
            c-bind="attrs"
        >x</c-component>
    """

    with pytest.raises(ValueError, match="start with 'on'"):
        _render_page(template, {"attrs": attrs}, path=path)


@pytest.mark.parametrize("path", RENDER_PATHS)
def test_c_element_refuses_reserved_events_name_passed_on_by_c_component(path: str) -> None:
    """A `data-cev-*` name, which Citry keeps for its own Events markup, is refused the same way."""
    template = """
        <c-component
            c-is="'element'"
            c-bind="attrs"
        >x</c-component>
    """

    with pytest.raises(RuntimeError, match="reserved internal Events namespace"):
        _render_page(template, {"attrs": {"IS": "section", "data-cev-x": "x"}}, path=path)


@pytest.mark.parametrize("path", RENDER_PATHS)
def test_c_element_passed_on_by_c_component_keeps_ordinary_attributes(path: str) -> None:
    """Control: the same mapping with an ordinary attribute name renders."""
    template = """
        <c-component
            c-is="'element'"
            c-bind="attrs"
        >x</c-component>
    """

    html = _render_page(template, {"attrs": {"IS": "section", "title": "x"}}, path=path)

    assert '<section title="x"' in html


def test_c_element_checks_attribute_names_of_a_direct_python_call() -> None:
    """
    Calling the built-in element component from Python goes through the same check.

    There is no template here to vouch for the name, so the component
    cannot assume a caller already vetted it.
    """
    registry = Citry(autodiscover=False)
    element = registry.get("element")

    with pytest.raises(ValueError, match="start with 'on'"):
        str(element(**{"is": "div", "onclick": "x"}))

    # Control: an ordinary name renders.
    assert str(element(**{"is": "div", "title": "x"})) == '<div title="x"></div>'


@pytest.mark.parametrize(
    "name",
    ["a b", "a\fb", 'a"b', "a=b", "a>b", ""],
    ids=["space", "form_feed", "quote", "equals", "greater_than", "empty"],
)
def test_c_element_refuses_an_invalid_attribute_name_in_a_direct_python_call(name: str) -> None:
    """
    The built-in element checks that each name is a valid HTML attribute name, not only that it is not a handler.

    A name with a space, a quote, or a form feed would split into more than
    one attribute or end the tag when written into the page.
    """
    registry = Citry(autodiscover=False)
    element = registry.get("element")

    with pytest.raises(ValueError, match="invalid HTML attribute name") as excinfo:
        str(element(**{"is": "div", name: "x"}))

    # A later step also checks names and would refuse these too, but it names
    # "HTML attributes", not the element. This pins the element's own check.
    assert "<c-element> contains" in str(excinfo.value)


@pytest.mark.parametrize("path", RENDER_PATHS)
def test_c_element_refuses_a_template_written_handler_with_a_migration_hint(path: str) -> None:
    """
    A handler written on a `<c-element>` that has `c-is` is refused.

    The message tells the author how to migrate: use a Vue `@click` in a
    component with `js`, or write a plain tag in a `c-if` branch.
    """
    template = """
        <c-element
            c-is="tag"
            onclick="x"
        >x</c-element>
    """

    with pytest.raises(ValueError, match="start with 'on'") as excinfo:
        _render_page(template, {"tag": "div"}, path=path)

    assert "@click" in str(excinfo.value)
    # The advice names the fix that suits this element, a plain tag in a `c-if` branch.
    assert "c-if" in str(excinfo.value)


@pytest.mark.parametrize("tag", ["script", "STYLE", "iframe"])
def test_vue_assembly_refuses_a_special_tag_even_when_the_producer_check_is_skipped(
    tag: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The Vue page builder has its own list of refused tags, apart from the one `<c-element>` applies.

    A dynamic element opening is first accepted only if its tag passes
    `_validate_tag_name`, which already refuses these tags, so the builder's
    own check can never fire in normal use. The test replaces the tag of a
    real opening with a refused one and skips the first check, to show the
    second check holds on its own for any other code that produces an opening.
    """
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = """
            <c-element c-is="tag">x</c-element>
        """

        def template_data(self, kwargs, slots):
            return {"tag": "div"}

    rendered = render_prepared_direct(Page())
    pending = [rendered]
    swapped = False
    while pending:
        current = pending.pop()
        for index, part in enumerate(current.parts):
            if isinstance(part, PreparedDynamicElementOpen):
                # `replace` drops the private producer token, so copy it over.
                swapped_part = replace(part, tag=tag)
                object.__setattr__(swapped_part, "_producer_token", part._producer_token)
                current.parts[index] = swapped_part
                swapped = True
            elif isinstance(part, PreparedDynamicElementClose):
                current.parts[index] = PreparedDynamicElementClose(tag)
            elif isinstance(part, CitryRender):
                pending.append(part)
    assert swapped

    def assemble() -> object:
        return assemble_typed_render(
            rendered,
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )

    # With the first check in place, the changed opening is not accepted at all.
    with pytest.raises(UnsupportedPreparedView, match="producer provenance"):
        assemble()

    monkeypatch.setattr(dynamic_element, "_validate_tag_name", lambda _tag: None)

    with pytest.raises(UnsupportedPreparedView, match="unsupported in prepared Vue"):
        assemble()
