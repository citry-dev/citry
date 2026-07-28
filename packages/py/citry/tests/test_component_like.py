"""Tests for contextual composition through the public ``ComponentLike`` protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, CitryElement, Component, ComponentLike, Const, Slot

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(slots=True)
class _ComponentLikeValue:
    """Configurable structural implementation used by the protocol tests."""

    factory: Callable[[Citry], Any]
    seen: list[Citry] = field(default_factory=list)

    def __citry_element__(self, citry: Citry, /) -> CitryElement:
        self.seen.append(citry)
        return self.factory(citry)


def _text_value(app: Citry, text: str = "resolved") -> _ComponentLikeValue:
    class Text(Component):
        citry = app
        template = """
          <span>{{ text }}</span>
        """

    return _ComponentLikeValue(lambda _app: Text(text=text))


def test_protocol_is_structural_and_runtime_checkable():
    app = Citry(autodiscover=False)
    value = _text_value(app)

    assert isinstance(value, ComponentLike)


def test_expression_resolves_against_the_rendering_citry_once_per_occurrence():
    app = Citry(autodiscover=False)
    value = _text_value(app)

    class Page(Component):
        citry = app
        template = """
          <main>{{ value }}{{ value }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"value": value}

    html = str(Page())

    assert html.count(">resolved</span>") == 2
    assert value.seen == [app, app]


def test_protocol_rejects_a_non_element_result_without_recursing():
    app = Citry(autodiscover=False)
    inner = _ComponentLikeValue(lambda _app: object())
    outer = _ComponentLikeValue(lambda _app: inner)

    class Page(Component):
        citry = app
        template = """
          <main>{{ value }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"value": outer}

    with pytest.raises(TypeError, match=r"returned '_ComponentLikeValue'; expected a CitryElement"):
        str(Page())

    assert outer.seen == [app]
    assert inner.seen == []


def test_protocol_rejects_an_element_bound_to_another_citry():
    app = Citry(autodiscover=False)
    other = Citry(autodiscover=False)
    value = _text_value(other)

    class Page(Component):
        citry = app
        template = """
          {{ value }}
        """

        def template_data(self, kwargs, slots):
            return {"value": value}

    with pytest.raises(ValueError, match="different Citry instance"):
        str(Page())


def test_protocol_preserves_resolver_errors_and_adds_the_component_path():
    app = Citry(autodiscover=False)

    def fail(_app: Citry) -> CitryElement:
        raise LookupError("missing package installation")

    value = _ComponentLikeValue(fail)

    class Page(Component):
        citry = app
        template = """
          <main>{{ value }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"value": value}

    with pytest.raises(LookupError, match=r"rendering components Page[\s\S]*missing package installation"):
        str(Page())


def test_resolved_element_inherits_provided_values_and_contributes_css():
    app = Citry(autodiscover=False)

    class Reader(Component):
        citry = app
        template = """
          <strong class="reader">{{ value }}</strong>
        """
        css = """
          .reader { color: teal; }
        """

        def template_data(self, kwargs, slots):
            return {"value": self.inject("theme").value}

    value = _ComponentLikeValue(lambda _app: Reader())

    class Page(Component):
        citry = app
        template = """
          <main>{{ value }}</main><c-css />
        """

        def template_data(self, kwargs, slots):
            self.provide("theme", value="inherited")
            return {"value": value}

    html = str(Page())

    assert ">inherited</strong>" in html
    assert ".reader { color: teal; }" in html


def test_static_slot_content_can_be_component_like():
    app = Citry(autodiscover=False)
    value = _text_value(app, "static slot")
    slot = Slot(value)

    class Page(Component):
        citry = app
        template = """
          <main>{{ slot }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"slot": slot}

    assert ">static slot</span>" in str(Page())
    assert value.seen == [app]


def test_callable_slot_result_can_be_component_like():
    app = Citry(autodiscover=False)
    value = _text_value(app, "callable slot")
    slot = Slot(lambda _ctx: value)

    class Page(Component):
        citry = app
        template = """
          <main>{{ slot }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"slot": slot}

    assert ">callable slot</span>" in str(Page())
    assert value.seen == [app]


def test_explicit_slot_call_resolves_component_like_inside_safe_eval():
    app = Citry(autodiscover=False)
    value = _text_value(app, "slot data")
    slot = Slot(lambda ctx: value if ctx.data.show else "hidden")

    class Page(Component):
        citry = app
        template = """
          <main>{{ slot({'show': True}) }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"slot": slot}

    assert ">slot data</span>" in str(Page())
    assert value.seen == [app]


def test_standalone_slot_has_no_implicit_global_citry_fallback():
    app = Citry(autodiscover=False)
    value = _text_value(app)

    with pytest.raises(RuntimeError, match="without a Citry render context"):
        Slot(value)()


@pytest.mark.parametrize("generator_form", [False, True], ids=["plain", "generator"])
def test_on_render_replacement_accepts_component_like_and_sets_parent(generator_form):
    app = Citry(autodiscover=False)
    parents: list[str | None] = []

    class Replacement(Component):
        citry = app
        template = """
          <mark>replacement</mark>
        """

        def template_data(self, kwargs, slots):
            parents.append(type(self.parent).__name__ if self.parent is not None else None)
            return {}

    value = _ComponentLikeValue(lambda _app: Replacement())

    if generator_form:

        class Page(Component):
            citry = app

            def on_render(self):
                yield value

    else:

        class Page(Component):
            citry = app

            def on_render(self):
                return value

    assert ">replacement</mark>" in str(Page())
    assert value.seen == [app]
    assert parents == ["Page"]


def test_const_component_like_is_never_precomputed_into_text():
    app = Citry(autodiscover=False)
    value = _text_value(app, "dynamic")

    class Page(Component):
        citry = app
        template = """
          <main>{{ value }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"value": Const(value)}

    assert ">dynamic</span>" in str(Page())
    assert ">dynamic</span>" in str(Page())
    assert value.seen == [app, app]


def test_html_attribute_values_do_not_invoke_component_like():
    app = Citry(autodiscover=False)
    value = _text_value(app)

    class Page(Component):
        citry = app
        template = """
          <main c-title="value">content</main>
        """

        def template_data(self, kwargs, slots):
            return {"value": value}

    html = str(Page())

    assert "title=" in html
    assert value.seen == []
