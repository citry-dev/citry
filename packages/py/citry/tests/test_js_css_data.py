"""Tests for ``Component.js_data()`` / ``css_data()``, their typed schemas, and the hook wiring."""

from dataclasses import is_dataclass

import pytest

from citry import Citry, Component, Extension


def _data_probe(captured: list) -> type[Extension]:
    """An extension whose ``on_component_data`` records the hook context."""

    class Probe(Extension):
        name = "probe"

        def on_component_data(self, ctx):
            captured.append(ctx)

    return Probe


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

        assert str(Card(rows=3)) == '<p data-cid-c1="">3</p>'
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
