"""
Tests for Kwargs/Slots declared as Pydantic models.

Citry does not depend on Pydantic; ``util.misc.get_fields`` recognizes
Pydantic v2 models by their attribute protocol. Citry constructs the typed
view from the final post-input-hook raw values, which runs Pydantic validation.
These tests pin that end-user path:
declaration, validation, defaults, parse-time tag rules, slots, and how the
``Const`` marker behaves through Pydantic validation.

Pydantic is a dev/test dependency only; the suite skips cleanly without it.
"""

# ruff: noqa: ANN

import pytest

from citry import Citry, Component, Const, Extension
from citry.constness import is_const
from citry.nodes import ExprNode
from citry.slots import Slot
from citry.util.misc import to_dict

pydantic = pytest.importorskip("pydantic")
BaseModel = pydantic.BaseModel
ConfigDict = pydantic.ConfigDict
BaseModelV1 = pytest.importorskip("pydantic.v1").BaseModel


class TestPydanticKwargs:
    @pytest.mark.parametrize("model_base", [BaseModel, BaseModelV1])
    def test_same_generation_models_merge_across_c3_branches(self, model_base):
        c = Citry()

        class LeftSchema(model_base):
            left: str = "left"

        class RightSchema(model_base):
            right: str = "right"

        class Left(Component):
            citry = c
            Kwargs = LeftSchema

        class Right(Component):
            citry = c
            Kwargs = RightSchema

        class Combined(Left, Right):
            pass

        value = Combined.Kwargs()
        assert (value.left, value.right) == ("left", "right")

    def test_typed_view_is_validated_model(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ title }} x{{ cols }}</p>"

            class Kwargs(BaseModel):
                title: str
                cols: int = 2

            def template_data(self, kwargs, slots):
                assert isinstance(kwargs, Card.Kwargs)
                return {"title": kwargs.title, "cols": kwargs.cols}

        assert Card(title="hi").render().serialize() == '<p data-cid-c1="">hi x2</p>'
        assert Card(title="hi", cols=5).render().serialize() == '<p data-cid-c2="">hi x5</p>'

    def test_validation_error_surfaces(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>hi</p>"

            class Kwargs(BaseModel):
                cols: int

        with pytest.raises(pydantic.ValidationError):
            Card(cols="not an int").render()

    def test_input_hook_mutation_is_coerced_and_validated(self):
        class Coerce(Extension):
            name = "coerce"

            def on_component_input(self, ctx):
                ctx.kwargs["cols"] = "7"

        c = Citry(extensions=[Coerce])

        class Card(Component):
            citry = c
            template = """
            <p>{{ cols }}</p>
            """

            class Kwargs(BaseModel):
                cols: int

            def template_data(self, kwargs, slots):
                assert kwargs.cols == 7
                assert type(kwargs.cols) is int
                return {"cols": kwargs.cols}

        assert Card(cols=1).render().serialize().strip() == '<p data-cid-c1="">7</p>'

    def test_missing_required_kwarg_raises(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>hi</p>"

            class Kwargs(BaseModel):
                title: str

        with pytest.raises(pydantic.ValidationError):
            Card().render()

    def test_parse_time_tag_rules_from_pydantic_model(self):
        # get_fields reads the model's fields, so a template using the
        # component is validated at parse time: unknown attrs and missing
        # required attrs fail before any render.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>hi</p>"

            class Kwargs(BaseModel):
                title: str
                cols: int = 2

        class BadUnknown(Component):
            citry = c
            template = '<c-Card title="x" wrong="y" />'

        with pytest.raises(SyntaxError, match="wrong"):
            BadUnknown().render()

        class BadMissing(Component):
            citry = c
            template = '<c-Card cols="3" />'

        with pytest.raises(SyntaxError, match="title"):
            BadMissing().render()


class TestPydanticSlots:
    def test_slots_model_with_slot_values(self):
        c = Citry()

        class Box(Component):
            citry = c
            template = '<div><c-slot name="header">fb</c-slot></div>'

            class Slots(BaseModel):
                model_config = ConfigDict(arbitrary_types_allowed=True)

                header: Slot | None = None

            def template_data(self, kwargs, slots):
                assert isinstance(slots, Box.Slots)

        assert "HEAD" in Box(slots={"header": "HEAD"}).render().serialize()
        assert "fb" in Box().render().serialize()

    def test_parse_time_fill_rules_from_pydantic_model(self):
        c = Citry()

        class Box(Component):
            citry = c
            template = '<div><c-slot name="header">fb</c-slot></div>'

            class Slots(BaseModel):
                model_config = ConfigDict(arbitrary_types_allowed=True)

                header: Slot | None = None

        class BadFill(Component):
            citry = c
            template = '<c-Box><c-fill name="wrong">x</c-fill></c-Box>'

        with pytest.raises(SyntaxError, match="wrong"):
            BadFill().render()


class TestPydanticComponentData:
    def test_template_data_uses_validated_coercions_and_defaults(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ count + 1 }} {{ label }}</p>"

            class TemplateData(BaseModel):
                count: int
                label: str = "rows"

            def template_data(self, kwargs, slots):
                return {"count": "7"}

        assert Card().render().serialize() == '<p data-cid-c1="">8 rows</p>'

    @pytest.mark.parametrize("model_base", [BaseModel, BaseModelV1])
    def test_data_schemas_preserve_extras_the_model_explicitly_allows(self, model_base):
        class OpenData(model_base):
            if model_base is BaseModel:
                model_config = ConfigDict(extra="allow")
            else:

                class Config:
                    extra = "allow"

            known: int

        captured: list = []

        class Probe(Extension):
            name = "probe"

            def on_component_data(self, ctx):
                captured.append(ctx)

        c = Citry(extensions=[Probe])

        class Card(Component):
            citry = c
            template = "<p>{{ plugin_value }}</p>"
            TemplateData = OpenData

            def template_data(self, kwargs, slots):
                data = OpenData(known=7, plugin_value="kept")
                data.__dict__["cached_value"] = "must not leak"
                return data

        assert Card().render().serialize() == '<p data-cid-c1="">kept</p>'
        assert captured[-1].template_data == {"known": 7, "plugin_value": "kept"}

    def test_pydantic_v1_allowed_underscore_extra_is_preserved(self):
        class OpenData(BaseModelV1):
            class Config:
                extra = "allow"

            known: int

        data = OpenData(known=7, _plugin_value="kept")

        assert to_dict(data) == {"known": 7, "_plugin_value": "kept"}


class TestPydanticConstInterplay:
    def test_validation_strips_the_marker_from_the_typed_view(self):
        # Pydantic validation produces new (coerced) values, so the typed
        # view loses the Const marker: the value safely renders as dynamic.
        # Validation itself accepts the transparent proxy.
        c = Citry()

        seen: dict = {}

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

            class Kwargs(BaseModel):
                cols: int

            def template_data(self, kwargs, slots):
                seen["typed_is_const"] = is_const(kwargs.cols)
                return {"cols": kwargs.cols}

        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c1="">3</p>'
        assert seen["typed_is_const"] is False
        (body,) = c._const_body_cache.values()
        assert any(isinstance(item, ExprNode) for item in body)

    def test_raw_kwargs_keep_the_marker(self):
        # The documented pattern for const-ness with a validating Kwargs
        # model: read the marked value from raw_kwargs.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

            class Kwargs(BaseModel):
                cols: int

            def template_data(self, kwargs, slots):
                return {"cols": self.raw_kwargs["cols"]}

        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c1="">3</p>'
        (body,) = c._const_body_cache.values()
        assert body == ["<p>3</p>"]
