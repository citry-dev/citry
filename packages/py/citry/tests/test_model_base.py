"""
`CitrySettings.model_base`: the kind of class Citry generates from plain schema declarations.

Without the setting a plain ``class Kwargs:`` becomes a generated slotted
dataclass. With it, the class is a dataclass with the base's options, a
Pydantic v2 or v1 model that subclasses the base, or a named tuple. These
tests check each kind for the schemas it serves, the errors for the ones it
cannot serve, and that the generated classes keep what Citry relies on.
"""

from __future__ import annotations

import functools
import sys
import types
import typing
from dataclasses import dataclass, field, is_dataclass
from decimal import Decimal
from enum import Enum

import pytest

from citry import Citry, CitrySettings, Component, ComponentLibrary, Const, LibraryComponent, is_const
from citry.ext.events.extension import _component_events_info
from citry.ext.events.schemas import validate_args

pydantic = pytest.importorskip("pydantic")
pydantic_v1 = pytest.importorskip("pydantic.v1")


class StrictModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", strict=True)


class ModelV1(pydantic_v1.BaseModel):
    class Config:
        extra = pydantic_v1.Extra.forbid


@dataclass
class PlainBase:
    pass


@dataclass(frozen=True)
class FrozenBase:
    pass


class Bump:
    by: int = 1


class Opaque:
    """A type Pydantic cannot build a validator for."""


def _card(base: object) -> type[Component]:
    app = Citry(autodiscover=False, model_base=base)

    class Card(Component):
        citry = app
        template = """
          <p>{{ title }} {{ count }} {{ loud }}</p>
        """

        class Kwargs:
            title: str
            count: int = 0

            def shout(self) -> str:
                return self.title.upper()

        def template_data(self, kwargs, slots):
            return {"title": kwargs.title, "count": kwargs.count, "loud": kwargs.shout()}

    return Card


# --- the setting ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "error", "message"),
    [
        (object(), TypeError, "must be a class or an import string"),
        (int, TypeError, "int, which is not a kind Citry can generate"),
        (typing.NamedTuple("Point", [("x", int)]), TypeError, "a named tuple cannot be extended"),
    ],
)
def test_a_value_of_no_kind_fails_when_the_settings_are_built(value: object, error: type, message: str) -> None:
    with pytest.raises(error, match=message):
        CitrySettings(model_base=value)


def test_a_typed_dict_is_not_a_kind() -> None:
    class Movie(typing.TypedDict):
        title: str

    with pytest.raises(TypeError, match=r"which is not a kind Citry can generate\. model_base accepts"):
        CitrySettings(model_base=Movie)


def test_a_dataclass_base_with_its_own_init_fails() -> None:
    @dataclass(init=False)
    class Custom:
        def __init__(self) -> None:
            pass

    with pytest.raises(TypeError, match="defines `__init__`, but Citry generates the constructor"):
        CitrySettings(model_base=Custom)


def test_an_import_string_is_resolved_when_citry_is_built() -> None:
    # The settings keep the string, so a settings module need not import it.
    settings = CitrySettings(model_base="pydantic.BaseModel")
    assert settings.model_base == "pydantic.BaseModel"

    card = _card("pydantic.BaseModel")

    assert issubclass(card.Kwargs, pydantic.BaseModel)


def test_an_import_string_for_a_missing_package_fails_when_citry_is_built() -> None:
    with pytest.raises(
        ImportError, match=r"'no_such_package' could not be imported .*Check the spelling, or install the package"
    ):
        Citry(autodiscover=False, model_base="no_such_package.BaseModel")


# --- each kind -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        (None, "dataclass"),
        (PlainBase, "dataclass"),
        (StrictModel, "pydantic"),
        (ModelV1, "pydantic"),
        (typing.NamedTuple, "namedtuple"),
    ],
)
def test_each_kind_renders_a_plain_kwargs_declaration(base: object, expected: str) -> None:
    card = _card(base)
    kwargs = card.Kwargs

    if expected == "dataclass":
        assert is_dataclass(kwargs)
    elif expected == "pydantic":
        assert issubclass(kwargs, base)  # type: ignore[arg-type]
    else:
        assert issubclass(kwargs, tuple)
    # Schema tools find the generated class by its marker, which a Pydantic
    # class body would have turned into a private attribute.
    assert kwargs.__dict__["_citry_synthesized_declaration"] is True
    # The authored method is there in every kind.
    assert "<p" in card(title="hi", count=2).render().serialize()
    assert "hi 2 HI" in card(title="hi", count=2).render().serialize()


@pytest.mark.parametrize("base", [None, PlainBase, typing.NamedTuple])
def test_citry_checks_the_values_of_a_dataclass_or_named_tuple(base: object) -> None:
    card = _card(base)

    with pytest.raises(TypeError, match="count"):
        card(title="hi", count="2").render()


@pytest.mark.parametrize("base", [StrictModel, ModelV1])
def test_pydantic_checks_the_values_of_a_model(base: object) -> None:
    card = _card(base)

    with pytest.raises(Exception, match="count") as raised:
        card(title="hi", count="many").render()
    assert "validation error" in str(raised.value)


def test_the_base_model_config_applies_to_every_generated_model() -> None:
    card = _card(StrictModel)

    # `strict=True` on the base refuses the coercion Pydantic would make.
    with pytest.raises(Exception, match="Input should be a valid integer"):
        card(title="hi", count="2").render()


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.11 does not record kw_only on a dataclass")
def test_a_dataclass_base_gives_its_options_to_the_generated_class() -> None:
    @dataclass(kw_only=True, order=True)
    class Ordered:
        pass

    kwargs = _card(Ordered).Kwargs

    params = kwargs.__dataclass_params__  # type: ignore[attr-defined]
    assert params.order is True
    assert issubclass(kwargs, Ordered)
    with pytest.raises(TypeError):
        kwargs("hi")


def test_a_dataclass_base_post_init_runs_after_citrys_check() -> None:
    seen: list[str] = []

    @dataclass
    class Recording:
        def __post_init__(self) -> None:
            seen.append(type(self).__name__)

    _card(Recording)(title="hi").render()

    assert seen == ["Kwargs"]


def test_a_frozen_dataclass_base_freezes_kwargs() -> None:
    kwargs = _card(FrozenBase).Kwargs

    assert kwargs.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_a_named_tuple_needs_its_fields_with_defaults_last() -> None:
    app = Citry(autodiscover=False, model_base=typing.NamedTuple)

    with pytest.raises(TypeError, match=r"Card.*Kwargs\.title has no default but follows a field with one"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs:
                count: int = 0
                title: str


def test_zero_argument_super_in_a_model_fails_at_class_setup() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    class Labelled:
        def label(self) -> str:
            return "base"

    # Any mention of `super` gives the method a cell that names the class
    # you wrote, so explicit `super(Kwargs, self)` cannot work either.
    with pytest.raises(TypeError, match=r"Kwargs\.label calls super\(\).*such as Labelled\.label\(self\)"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs(Labelled):
                title: str = "t"

                def label(self) -> str:
                    return super().label()


def test_a_field_pydantic_cannot_validate_is_named_at_class_setup() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    with pytest.raises(
        TypeError, match=r"Component Card: could not generate a Pydantic v2 model for Kwargs field 'item'"
    ):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs:
                count: int = 0
                item: Opaque


@pytest.mark.parametrize("base", [pydantic.BaseModel, pydantic_v1.BaseModel])
def test_a_const_default_works_as_in_a_hand_written_model(base: type) -> None:
    seen: list[tuple[bool, object]] = []

    def build(app: Citry, kwargs_cls: type) -> type[Component]:
        class Card(Component):
            citry = app
            template = """
              <p>{{ flag }}</p>
            """
            Kwargs = kwargs_cls

            def template_data(self, kwargs, slots):
                seen.append((is_const(kwargs.flag), kwargs.flag))
                return {"flag": kwargs.flag}

        return Card

    class Plain:
        flag: bool = Const(True)  # noqa: FBT003

    class Written(base):  # type: ignore[misc, valid-type]
        flag: bool = Const(True)  # noqa: FBT003

    generated = build(Citry(autodiscover=False, model_base=base), Plain)
    written = build(Citry(autodiscover=False), Written)

    # The marker stays the field's default, so Citry's authored-model path
    # carries it through validation in both cases.
    assert issubclass(generated.Kwargs, base)
    assert generated().render().serialize().endswith(">True</p>\n")
    assert written().render().serialize().endswith(">True</p>\n")
    assert seen[0] == seen[1]


def test_slots_stay_as_they_are() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    class Card(Component):
        citry = app
        template = """
          <c-slot name="title" />
        """

        class Slots:
            title: object = None

    assert not issubclass(Card.Slots, pydantic.BaseModel)


# --- inheritance ---------------------------------------------------------------


def test_a_child_schema_follows_its_parents_kind() -> None:
    plain_app = Citry(autodiscover=False)
    model_app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    class Parent(Component):
        citry = plain_app
        template = """
          <p>x</p>
        """

        class Kwargs:
            title: str = "t"

    # A dataclass parent keeps the child a dataclass under a Pydantic setting.
    class Child(Component):
        citry = model_app
        template = """
          <p>x</p>
        """

        class Kwargs(Parent.Kwargs):
            count: int = 0

    assert is_dataclass(Child.Kwargs)
    assert not issubclass(Child.Kwargs, pydantic.BaseModel)


def test_a_child_of_a_generated_model_stays_a_model() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    class Parent(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class Kwargs:
            title: str = "t"

    class Child(Parent):
        class Kwargs(Parent.Kwargs):
            count: int = 0

    assert issubclass(Child.Kwargs, Parent.Kwargs)
    assert set(Child.Kwargs.model_fields) == {"title", "count"}


# --- State and Events data -------------------------------------------------------


def _counter(base: object) -> type[Component]:
    app = Citry(autodiscover=False, model_base=base)

    class Counter(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class State:
            count: int = 0

        class Events:
            def bump(self, state, data: Bump) -> None:
                state.count += data.by

    return Counter


@pytest.mark.parametrize("base", [PlainBase, pydantic.BaseModel])
def test_state_and_event_data_follow_the_setting(base: type) -> None:
    counter = _counter(base)

    assert issubclass(counter.State, base)
    info = _component_events_info(counter)
    assert info is not None
    data = info.handlers["bump"].data_schema
    assert data is not None
    assert issubclass(data, base)
    assert data.__dict__["_citry_synthesized_declaration"] is True
    # The handler's validation reads the generated class.
    passed = validate_args(data, {"by": 3})
    assert passed.value is not None
    assert passed.value.by == 3
    failed = validate_args(data, {"by": "many"})
    assert failed.value is None
    assert "by" in failed.fields


def test_event_data_refuses_a_pydantic_v1_base() -> None:
    # Events validation reads Pydantic v2 models only, so this fails at
    # class setup rather than when the handler is called.
    with pytest.raises(ValueError, match="cannot be generated as a Pydantic v1 model"):
        _counter(pydantic_v1.BaseModel)


@dataclass
class Written:
    by: int = 1


def test_a_dataclass_event_data_class_is_kept_as_written() -> None:
    app = Citry(autodiscover=False, model_base=typing.NamedTuple)

    class Counter(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class Events:
            def bump(self, data: Written) -> None:
                pass

    info = _component_events_info(Counter)
    assert info is not None
    assert info.handlers["bump"].data_schema is Written


def test_a_dataclass_base_gives_state_its_options() -> None:
    assert issubclass(_counter(PlainBase).State, PlainBase)


@pytest.mark.parametrize(
    ("base", "message"),
    [
        (typing.NamedTuple, "State cannot be generated as a NamedTuple, because Citry assigns to State"),
        (FrozenBase, "State cannot be generated from the frozen dataclass model_base FrozenBase"),
    ],
)
def test_state_refuses_a_kind_citry_cannot_assign_to(base: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _counter(base)


def test_event_data_refuses_a_named_tuple() -> None:
    app = Citry(autodiscover=False, model_base=typing.NamedTuple)

    with pytest.raises(ValueError, match="event data class Bump cannot be generated as a NamedTuple"):

        class Counter(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Events:
                def bump(self, data: Bump) -> None:
                    pass


def test_event_data_under_a_frozen_dataclass_base_is_allowed() -> None:
    app = Citry(autodiscover=False, model_base=FrozenBase)

    class Counter(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class Events:
            def bump(self, data: Bump) -> None:
                pass

    info = _component_events_info(Counter)
    assert info is not None
    data = info.handlers["bump"].data_schema
    assert data is not None
    assert data.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


# --- review findings -------------------------------------------------------------


def test_a_field_type_resolves_in_the_module_that_wrote_it() -> None:
    # `Money` means Decimal where the mixin is written and int here, so the
    # generated model, which lives in this module, must read it there.
    other = types.ModuleType("model_base_other")
    exec(  # noqa: S102 - a module written for this test
        "from __future__ import annotations\n"
        "from decimal import Decimal\n"
        "Money = Decimal\n"
        "class Priced:\n"
        "    price: Money\n",
        other.__dict__,
    )
    sys.modules["model_base_other"] = other
    try:
        app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

        class Card(Component):
            citry = app
            template = """
              <p>{{ price }}</p>
            """

            class Kwargs(other.Priced):  # type: ignore[name-defined]
                pass

        assert Card.Kwargs.model_fields["price"].annotation is Decimal
        assert ">2.5</p>" in Card(price=Decimal("2.5")).render().serialize()
    finally:
        del sys.modules["model_base_other"]


Money = int


@pytest.mark.parametrize("base", [pydantic.BaseModel, pydantic_v1.BaseModel])
def test_a_class_constant_stays_a_class_constant(base: type) -> None:
    app = Citry(autodiscover=False, model_base=base)

    class Card(Component):
        citry = app
        template = """
          <p>{{ limit }}</p>
        """

        class Kwargs:
            LIMIT = 5
            title: str = "t"

        def template_data(self, kwargs, slots):
            return {"limit": kwargs.LIMIT}

    # A constant is not an input, under v1 as under v2.
    fields = Card.Kwargs.model_fields if base is pydantic.BaseModel else Card.Kwargs.__fields__
    assert "LIMIT" not in fields
    assert ">5</p>" in Card().render().serialize()


def test_field_init_false_fails_for_a_model() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    with pytest.raises(TypeError, match=r"Kwargs\.hidden uses field\(init=False\)"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs:
                hidden: int = field(default=1, init=False)


def test_a_field_description_reaches_the_model() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    class Card(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class Kwargs:
            title: str = field(default="t", metadata={"description": "The card's title."})

    assert Card.Kwargs.model_fields["title"].description == "The card's title."


def test_a_named_tuple_refuses_a_default_factory() -> None:
    app = Citry(autodiscover=False, model_base=typing.NamedTuple)

    with pytest.raises(TypeError, match=r"Kwargs\.tags uses field\(default_factory=\.\.\.\)"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs:
                tags: list[str] = field(default_factory=list)


def test_an_underscore_field_fails_for_a_model() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    with pytest.raises(TypeError, match=r"Kwargs\._secret starts with an underscore"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs:
                _secret: int = 0


def test_a_named_tuple_keeps_class_variables_and_special_methods() -> None:
    app = Citry(autodiscover=False, model_base=typing.NamedTuple)

    class Card(Component):
        citry = app
        template = """
          <p>{{ text }}</p>
        """

        class Kwargs:
            limit: typing.ClassVar[int] = 3
            title: str = "t"

            def __str__(self) -> str:
                return f"Card {self.title}"

        def template_data(self, kwargs, slots):
            return {"text": f"{kwargs} {kwargs.limit}"}

    assert Card.Kwargs._fields == ("title",)
    assert ">Card t 3</p>" in Card().render().serialize()


def test_a_child_of_a_dataclass_base_schema_keeps_the_base_options() -> None:
    @dataclass(order=True)
    class Ordered:
        pass

    app = Citry(autodiscover=False, model_base=Ordered)

    class Parent(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class Kwargs:
            title: str = "t"

    class Child(Parent):
        class Kwargs(Parent.Kwargs):
            count: int = 0

    assert Child.Kwargs.__dataclass_params__.order is True  # type: ignore[attr-defined]


def test_a_child_state_keeps_its_parents_dataclass() -> None:
    plain = Citry(autodiscover=False)

    class Parent(Component):
        citry = plain
        template = """
          <p>x</p>
        """

        class State:
            count: int = 0

    app = Citry(autodiscover=False, model_base=typing.NamedTuple)

    # A child State follows its parent's kind, so the NamedTuple setting,
    # which State cannot take, does not apply to it.
    class Child(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class State(Parent.State):
            step: int = 1

    assert is_dataclass(Child.State)


class CountBadge(LibraryComponent):
    template = """
      <span>{{ label }}</span>
    """

    class Kwargs:
        count: int = 0
        label: str


def test_a_library_component_keeps_the_kind_its_author_wrote() -> None:
    app = Citry(autodiscover=False, model_base=typing.NamedTuple)

    # Under the NamedTuple kind this Kwargs could not be generated, because
    # a required field follows one with a default.
    installation = app.register_library(ComponentLibrary(name="model-base-lib", components=(CountBadge,)))

    assert is_dataclass(installation.component(CountBadge).Kwargs)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (pydantic.RootModel[int], "root model"),
        (pydantic.dataclasses.dataclass(type("PD", (), {"__annotations__": {}})), "Pydantic dataclass"),
    ],
)
def test_pydantic_kinds_without_fields_are_refused(value: object, message: str) -> None:
    with pytest.raises(TypeError, match=message):
        CitrySettings(model_base=value)


def test_a_mixin_init_the_dataclass_replaced_is_fine() -> None:
    class Mixin:
        def __init__(self) -> None:
            pass

    @dataclass
    class Base(Mixin):
        pass

    assert CitrySettings(model_base=Base).model_base is Base


# --- second review --------------------------------------------------------------


def test_a_named_tuple_refuses_a_mutable_default() -> None:
    app = Citry(autodiscover=False, model_base=typing.NamedTuple)

    # Every render would share the one list.
    with pytest.raises(TypeError, match=r"Kwargs\.items has a list default, which every render would share"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs:
                items: list[str] = []


@dataclass(frozen=True)
class Coords:
    x: int = 0


def test_a_class_inheriting_its_own_dataclass_keeps_it_under_a_dataclass_base() -> None:
    app = Citry(autodiscover=False, model_base=PlainBase)

    class Card(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class Kwargs(Coords):
            y: int = 1

    # Mixing the frozen parent with the mutable base would fail, so the
    # class keeps its parent's dataclass.
    assert issubclass(Card.Kwargs, Coords)
    assert not issubclass(Card.Kwargs, PlainBase)


class Shade(Enum):
    DARK = "dark"


class Describer:
    def __get__(self, instance: object, owner: type) -> str:
        return "described"


class ShadeMixin:
    Shade = Shade
    note = Describer()
    size = len


@pytest.mark.parametrize("base", [pydantic.BaseModel, pydantic_v1.BaseModel])
def test_copied_class_members_stay_class_members(base: type) -> None:
    app = Citry(autodiscover=False, model_base=base)

    class Card(Component):
        citry = app
        template = """
          <p>{{ shade }} {{ size }}</p>
        """

        class Kwargs(ShadeMixin):
            title: str = "abc"

        def template_data(self, kwargs, slots):
            return {"shade": kwargs.Shade.DARK.value, "size": kwargs.size(kwargs.title)}

    # A nested class, a descriptor and a builtin are not inputs.
    fields = Card.Kwargs.model_fields if base is pydantic.BaseModel else Card.Kwargs.__fields__
    assert set(fields) == {"title"}
    assert ">dark 3</p>" in Card().render().serialize()


def test_a_cached_property_fails_for_a_v1_model() -> None:
    app = Citry(autodiscover=False, model_base=pydantic_v1.BaseModel)

    with pytest.raises(TypeError, match=r"Kwargs\.upper is a cached_property"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs:
                title: str = "t"

                @functools.cached_property
                def upper(self) -> str:
                    return self.title.upper()


@dataclass
class BaseData:
    by: int = 1


class ChildData(BaseData):
    extra: int = 0


@pytest.mark.parametrize("base", [pydantic_v1.BaseModel, typing.NamedTuple])
def test_event_data_that_inherits_a_dataclass_keeps_it(base: object) -> None:
    app = Citry(autodiscover=False, model_base=base)

    class Counter(Component):
        citry = app
        template = """
          <p>x</p>
        """

        class Events:
            def bump(self, data: ChildData) -> None:
                pass

    info = _component_events_info(Counter)
    assert info is not None
    assert info.handlers["bump"].data_schema is ChildData


class Greeter:
    def label(self) -> str:
        return "base"


class LoudGreeter(Greeter):
    def label(self) -> str:
        return super().label().upper()


def test_the_super_error_names_the_mixin_and_the_next_class() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)

    with pytest.raises(TypeError, match=r"LoudGreeter\.label calls super\(\).*such as Greeter\.label\(self\)"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class Kwargs(LoudGreeter):
                title: str = "t"


def test_a_pydantic_v1_dataclass_is_refused() -> None:
    v1_dataclass = pydantic_v1.dataclasses.dataclass(type("PD1", (), {"__annotations__": {}}))

    with pytest.raises(TypeError, match="Pydantic dataclass"):
        CitrySettings(model_base=v1_dataclass)


def test_an_app_subclass_of_a_library_component_follows_the_setting() -> None:
    app = Citry(autodiscover=False, model_base=pydantic.BaseModel)
    installation = app.register_library(ComponentLibrary(name="model-base-sub", components=(CountBadge,)))

    class Mine(installation.component(CountBadge)):  # type: ignore[misc]
        class Kwargs:
            label: str = "mine"

    # The app wrote this class, so the app's setting applies to it.
    assert issubclass(Mine.Kwargs, pydantic.BaseModel)
