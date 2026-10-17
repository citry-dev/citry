"""Tests for ``Component.js_data()`` / ``css_data()``, their typed schemas, and the hook wiring."""

from dataclasses import is_dataclass

import pytest

from citry import Citry, Component, Extension, component_render
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
        assert definition.template.startswith("<p>{{ $citryPrepared.")
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
        assert definition.template.startswith("<p>{{ $citryPrepared.")
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


class TestJsDataReservedKeys:
    """js_data() keys the browser runtime refuses are rejected when Python renders."""

    @pytest.mark.parametrize(
        ("key", "message"),
        [
            ("$count", r"component Card .*contains the key '\$count'.*'\$'.*Rename the key, for example to 'count'"),
            ("_count", r"component Card .*contains the key '_count'.*'_'.*Rename the key, for example to 'count'"),
            ("$", r"contains the key '\$'.*Rename the key to a name that starts with a letter"),
            ("__", r"contains the key '__'.*Rename the key to a name that starts with a letter"),
            ("_1x", r"contains the key '_1x'.*Rename the key to a name that starts with a letter"),
            ("citryId", r"contains the key 'citryId'.*prop on every component.*starts with a letter"),
        ],
    )
    def test_reserved_key_raises_before_output(self, key, message):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            def js_data(self, kwargs, slots):
                return {"ok": 1, key: 2}

        with pytest.raises(ValueError, match=message):
            Card().render()

    def test_str_subclass_key_is_checked(self):
        class Name(str):
            __slots__ = ()

        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            def js_data(self, kwargs, slots):
                return {Name("$x"): 1}

        with pytest.raises(ValueError, match=r"contains the key '\$x'"):
            Card().render()

    def test_typed_schema_field_with_underscore_raises(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class JsData:
                _secret: int = 1

            def js_data(self, kwargs, slots):
                return self.JsData()

        with pytest.raises(ValueError, match=r"contains the key '_secret'"):
            Card().render()

    def test_key_added_by_extension_raises(self):
        class AddKey(Extension):
            name = "add_reserved_key"

            def on_component_data(self, ctx):
                ctx.js_data["$added"] = 1

        c = Citry(extensions=[AddKey])

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        with pytest.raises(ValueError, match=r"component Card \(from js_data\(\) or an extension's.*'\$added'"):
            Card().render()

    def test_ordinary_keys_render_every_time(self, monkeypatch):
        # Start with no remembered keys, so the first render runs the prefix
        # test and the second takes the remembered-key path.
        monkeypatch.setattr(component_render, "_ACCEPTED_JS_DATA_KEYS", set())
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            def js_data(self, kwargs, slots):
                return {"count": 1, "count_": 2, "a$b": 3, "a_b": 4, "citryid": 5}

        for _ in range(2):
            html = Card().render().serialize()
            assert '"count":1' in html
            assert '"a$b":3' in html
        assert {"count", "a$b"} <= component_render._ACCEPTED_JS_DATA_KEYS
