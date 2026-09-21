"""Tests for ``Component.js_data()`` / ``css_data()``, their typed schemas, and the hook wiring."""

from dataclasses import is_dataclass

import pytest

from citry import Citry, Component, Extension
from citry._vue.capture import render_prepared
from citry._vue.direct_capture import assemble_typed_render


def _data_probe(captured: list) -> type[Extension]:
    """An extension whose ``on_component_data`` records the hook context."""

    class Probe(Extension):
        name = "probe"

        def on_component_data(self, ctx):
            captured.append(ctx)

    return Probe


def _assemble(component):
    rendered = render_prepared(component)
    return assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"x-{type_key.lower().replace('_', '-')}",
    )


class TestJsCssDataMethods:
    def test_defaults_to_empty_dicts(self):
        captured: list = []
        c = Citry(extensions=[_data_probe(captured)])

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        str(Card())
        assert captured[-1].js_data == {}
        assert captured[-1].css_data == {}

    def test_data_reaches_the_hook(self):
        captured: list = []
        c = Citry(extensions=[_data_probe(captured)])

        class Card(Component):
            citry = c
            template = "<p>{{ rows }}</p>"

            def template_data(self, kwargs, slots):
                return {"rows": kwargs["rows"]}

            def js_data(self, kwargs, slots):
                return {"rows": kwargs["rows"]}

            def css_data(self, kwargs, slots):
                return {"row-color": "red"}

        assembly = _assemble(Card(rows=3))
        [occurrence] = assembly.view.occurrences
        definition = assembly.compile_inputs[occurrence.definition_id]
        assert definition.template.startswith("<p>{{ preparedData.")
        assert "3" in occurrence.prepared_data.values()
        assert occurrence.server_data == {"rows": 3}
        assert captured[-1].js_data == {"rows": 3}
        assert captured[-1].css_data == {"row-color": "red"}

    def test_hook_still_carries_template_data(self):
        captured: list = []
        c = Citry(extensions=[_data_probe(captured)])

        class Card(Component):
            citry = c
            template = "<p>{{ title }}</p>"

            def template_data(self, kwargs, slots):
                return {"title": "hi"}

        str(Card())
        assert captured[-1].template_data == {"title": "hi"}


class TestJsCssDataSchemas:
    def test_schemas_auto_convert_to_dataclasses(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class JsData:
                rows: int

            class CssData:
                color: str = "red"

        assert is_dataclass(Card.JsData)
        assert is_dataclass(Card.CssData)

    def test_missing_field_raises(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class JsData:
                rows: int

            def js_data(self, kwargs, slots):
                return {}

        with pytest.raises(TypeError, match="rows"):
            str(Card())

    def test_unexpected_field_raises(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class CssData:
                color: str = "red"

            def css_data(self, kwargs, slots):
                return {"colour": "red"}

        with pytest.raises(TypeError, match="colour"):
            str(Card())

    def test_schema_instance_is_accepted(self):
        captured: list = []
        c = Citry(extensions=[_data_probe(captured)])

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class JsData:
                rows: int

            def js_data(self, kwargs, slots):
                return Card.JsData(rows=5)

        str(Card())
        assert captured[-1].js_data == {"rows": 5}

    def test_validated_schema_defaults_become_the_normalized_data(self):
        captured: list = []
        c = Citry(extensions=[_data_probe(captured)])

        class Card(Component):
            citry = c
            template = "<p>{{ title }}</p>"

            class TemplateData:
                title: str = "default title"

            class JsData:
                rows: int = 3

            class CssData:
                color: str = "red"

            def template_data(self, kwargs, slots):
                return {}

            def js_data(self, kwargs, slots):
                return {}

            def css_data(self, kwargs, slots):
                return {}

        assembly = _assemble(Card())
        [occurrence] = assembly.view.occurrences
        definition = assembly.compile_inputs[occurrence.definition_id]
        assert definition.template.startswith("<p>{{ preparedData.")
        assert "default title" in occurrence.prepared_data.values()
        assert occurrence.server_data == {"rows": 3}
        assert captured[-1].template_data == {"title": "default title"}
        assert captured[-1].js_data == {"rows": 3}
        assert captured[-1].css_data == {"color": "red"}

    def test_declared_schema_requires_the_method_to_supply_it(self):
        # A schema with required fields makes the default js_data() (which
        # returns None, normalized to {}) fail validation: declaring the
        # schema is a promise the method must keep.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class JsData:
                rows: int

        with pytest.raises(TypeError, match="rows"):
            str(Card())
