"""
Citry checks the outer type of each value a component receives.

A wrong value raises ``TypeError`` naming the component, the field, the
expected type and the value. Only the outer type is checked (``list[str]``
accepts any list), annotations that ``isinstance`` cannot test are skipped,
and ``Citry(lint=LintSettings(check_input_types=False))`` or a nested
``class Lint:`` with ``check_input_types = False`` turns the check off.
"""

from __future__ import annotations

import collections.abc
import numbers
import sys
import types
import typing
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Annotated, Any, Literal, NamedTuple, NewType, Optional, Protocol, TypeVar, Union
from unittest.mock import Mock

import pytest
import typing_extensions
import wrapt
from pydantic import BaseModel

import citry._input_types as input_types
from citry import Citry, Component, ComponentLibrary, Const, LibraryComponent, LintSettings, Markup
from citry.ext.events.dispatcher import EventsDispatcher, TransportContext
from citry.ext.events.tokens import mint_state_token

if TYPE_CHECKING:
    from decimal import Context as CheckerOnlyName


SIGNING_KEY = "input-types-secret"
UserId = NewType("UserId", int)
T = TypeVar("T")


class Row:
    pass


class SubRow(Row):
    pass


class Movie(typing.TypedDict):
    title: str


@typing.runtime_checkable
class HasClose(Protocol):
    def close(self) -> None: ...


class PlainProtocol(Protocol):
    def close(self) -> None: ...


class Closer:
    def close(self) -> None:
        pass


class CountedInt:
    """An integer type that registers itself, as numpy integers do."""


numbers.Integral.register(CountedInt)


def _card(app: Citry, annotation: object, *, default: object = dataclass) -> type[Component]:
    """Build a component whose one input ``value`` has the given annotation."""
    namespace: dict[str, Any] = {"__annotations__": {"value": annotation}}
    if default is not dataclass:
        namespace["value"] = default
    kwargs_class = type("Kwargs", (), namespace)

    class Card(Component):
        citry = app
        Kwargs = kwargs_class

        template = """
          <span>{{ value }}</span>
        """

    return Card


def _renders(component: type[Component], **kwargs: object) -> bool:
    """Whether the component renders, or ``False`` when the type check rejects a value."""
    try:
        str(component(**kwargs))
    except TypeError as error:
        if "expects" not in str(error):
            raise
        return False
    return True


class TestErrorMessage:
    def test_names_the_component_field_expected_type_and_value(self):
        app = Citry()
        card = _card(app, str)

        with pytest.raises(TypeError) as error:
            str(card(value=123))

        message = str(error.value)
        assert "Card.Kwargs.value expects str, got int (123)." in message
        assert "change the annotation to accept int" in message
        # The render error wrapper still adds where the component was used.
        assert message.startswith("An error occurred while rendering components Card:")

    def test_long_value_is_shortened(self):
        app = Citry()
        card = _card(app, str)

        with pytest.raises(TypeError) as error:
            str(card(value=list(range(200))))

        assert "got list ([0, 1, 2," in str(error.value)
        assert "...)." in str(error.value)

    def test_value_whose_repr_fails_still_reports_the_type(self):
        class Broken:
            def __repr__(self) -> str:
                raise RuntimeError

        app = Citry()
        card = _card(app, str)

        with pytest.raises(TypeError, match=r"got Broken \(<unprintable value>\)"):
            str(card(value=Broken()))

    def test_union_is_written_as_in_source(self):
        app = Citry()
        card = _card(app, Optional[int])  # noqa: UP045 - the typing spelling under test

        with pytest.raises(TypeError, match=r"Card\.Kwargs\.value expects int \| None, got str"):
            str(card(value="1"))


# Each row: annotation, values that pass, values that fail.
ANNOTATION_CASES: list[tuple[str, object, list[object], list[object]]] = [
    ("str", str, ["a", Markup("<b>")], [1, None, b"a"]),
    ("int accepts bool and registered integers", int, [1, True, CountedInt()], [1.0, "1", Decimal(1)]),
    ("float accepts int and real numbers", float, [1.0, 1, Fraction(1, 2)], [Decimal("1.5"), "1.0"]),
    ("complex accepts real numbers", complex, [1j, 1.0, 1], ["1j"]),
    ("bool rejects int", bool, [True, False], [0, 1, None]),
    ("None", None, [None], [0, ""]),
    ("class and subclass", Row, [Row(), SubRow()], [object(), Mock()]),
    ("Optional", Optional[int], [1, None], ["1"]),  # noqa: UP045 - the typing spelling under test
    ("pipe union", int | str, [1, "a"], [1.5, None]),
    ("typing Union", Union[int, str], [1, "a"], [None]),  # noqa: UP007 - the typing spelling under test
    ("Annotated", Annotated[int, "meta"], [1], ["1"]),
    ("Literal", Literal["a", 1], ["a", 1], ["b", 2, True]),
    ("Literal with None", Literal["a", None], ["a", None], ["b"]),  # noqa: PYI061 - None inside Literal under test
    ("list outer type only", list[str], [[], [1, 2]], [(), "ab", {1}]),
    ("dict outer type only", dict[str, int], [{}, {"a": "b"}], [[("a", 1)]]),
    ("tuple outer type only", tuple[int, ...], [(), ("a",)], [[1]]),
    ("Sequence", collections.abc.Sequence[str], [[], (), "ab"], [{1}, 1]),
    ("Mapping", collections.abc.Mapping[str, int], [{}, types.MappingProxyType({})], [[]]),
    ("type[X]", type[Row], [Row, SubRow], [Row(), int]),
    ("bare type", type, [int, Row], [1]),
    ("NewType is its base type", UserId, [UserId(1), 2], ["1"]),
    ("TypedDict is a dict", Movie, [{"title": "x"}, {}], [[]]),
    ("Callable", collections.abc.Callable[[int], str], [len, Row], [1, "a"]),
    ("runtime Protocol", HasClose, [Closer()], [object()]),
    ("type alias", typing_extensions.TypeAliasType("IntAlias", int), [1], ["1"]),
]


@pytest.mark.parametrize(
    ("annotation", "accepted", "rejected"),
    [case[1:] for case in ANNOTATION_CASES],
    ids=[case[0] for case in ANNOTATION_CASES],
)
def test_annotation_forms(annotation: object, accepted: list[object], rejected: list[object]):
    app = Citry()
    card = _card(app, annotation)

    for value in accepted:
        assert _renders(card, value=value), value
        # A second render takes the exact-type fast path for a remembered
        # type; it must give the same answer.
        assert _renders(card, value=value), value
    for value in rejected:
        assert not _renders(card, value=value), value


UNCHECKED_ANNOTATIONS: list[tuple[str, object]] = [
    ("Any", Any),
    ("object", object),
    ("TypeVar", T),
    ("Protocol without runtime_checkable", PlainProtocol),
    ("LiteralString", typing_extensions.LiteralString),
    ("union with Any", int | Any),
    ("name that cannot be evaluated", "MissingName"),
    ("forward reference that cannot be evaluated", typing.ForwardRef("MissingName")),
]


@pytest.mark.parametrize(
    "annotation",
    [case[1] for case in UNCHECKED_ANNOTATIONS],
    ids=[case[0] for case in UNCHECKED_ANNOTATIONS],
)
def test_annotations_that_cannot_be_tested_are_skipped(annotation: object):
    app = Citry()
    card = _card(app, annotation)

    assert _renders(card, value=object())
    assert _renders(card, value=1)


class TestAnnotationResolution:
    def test_string_annotation_resolves_in_the_declaring_module(self):
        # This module uses `from __future__ import annotations`, so every
        # annotation below is a string until Citry evaluates it.
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs:
                row: Row
                rows: list[Row]

            template = """
              <span></span>
            """

        assert _renders(Card, row=SubRow(), rows=[])
        assert not _renders(Card, row="row", rows=[])

    def test_name_imported_only_for_type_checkers_is_skipped(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs:
                context: CheckerOnlyName
                count: int

            template = """
              <span></span>
            """

        # The unresolvable field is unchecked; the other field still is.
        assert _renders(Card, context="anything", count=1)
        assert not _renders(Card, context="anything", count="1")

    def test_inherited_field_resolves_in_the_module_of_its_class(self):
        # The base declares `item: Row` in one module; the subclass lives in
        # another module whose own `Row` is a different class.
        base_module = types.ModuleType("citry_input_types_base")
        child_module = types.ModuleType("citry_input_types_child")
        sys.modules[base_module.__name__] = base_module
        sys.modules[child_module.__name__] = child_module
        try:
            exec(  # noqa: S102 - builds two real modules for the test
                "from __future__ import annotations\n"
                "from citry import Citry, Component\n"
                "app = Citry()\n"
                "class Row:\n"
                "    pass\n"
                "class Base(Component):\n"
                "    citry = app\n"
                "    class Kwargs:\n"
                "        item: Row\n"
                "    template = '<span></span>'\n",
                base_module.__dict__,
            )
            exec(  # noqa: S102 - builds two real modules for the test
                "from __future__ import annotations\n"
                "from citry_input_types_base import Base\n"
                "class Row:\n"
                "    pass\n"
                "class Child(Base):\n"
                "    class Kwargs(Base.Kwargs):\n"
                "        extra: Row = None\n",
                child_module.__dict__,
            )
            child = child_module.Child
            assert _renders(child, item=base_module.Row())
            assert not _renders(child, item=child_module.Row())
            assert _renders(child, item=base_module.Row(), extra=child_module.Row())
            assert not _renders(child, item=base_module.Row(), extra=base_module.Row())
        finally:
            del sys.modules[base_module.__name__]
            del sys.modules[child_module.__name__]


class TestDefaults:
    def test_none_default_accepts_none(self):
        # `x: str = None` is common in code ported from django-components.
        app = Citry()
        card = _card(app, str, default=None)

        assert _renders(card)
        assert _renders(card, value=None)
        assert _renders(card, value="a")
        assert not _renders(card, value=1)

    def test_default_object_passes_but_other_values_of_its_type_do_not(self):
        app = Citry()
        card = _card(app, list[str], default=())

        assert _renders(card)
        assert _renders(card, value=["a"])
        assert not _renders(card, value=("a",))

    def test_default_factory_value_is_checked(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs:
                tags: list[str] = field(default_factory=tuple)  # type: ignore[assignment]

            template = """
              <span></span>
            """

        assert not _renders(Card)
        assert _renders(Card, tags=[])


class TestConst:
    def test_const_marker_is_removed_before_the_check(self):
        app = Citry()
        card = _card(app, str)

        assert _renders(card, value=Const("a"))
        assert not _renders(card, value=Const(1))

    def test_const_default_is_checked_as_its_value(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs:
                title: str = Const("a")
                size: int = Const("large")  # type: ignore[assignment]

            template = """
              <span>{{ title }}</span>
            """

        assert _renders(Card, size=1)
        # The authored default passes, like any other default.
        assert _renders(Card)
        assert not _renders(Card, size=Const("small"))


class TestSchemaKinds:
    def test_user_dataclass_and_namedtuple_are_checked(self):
        @dataclass
        class DataclassKwargs:
            count: int

        class TupleKwargs(NamedTuple):
            count: int

        for schema in (DataclassKwargs, TupleKwargs):

            class Card(Component):
                citry = Citry()
                Kwargs = schema

                template = """
                  <span>{{ count }}</span>
                """

            assert _renders(Card, count=1)
            assert not _renders(Card, count="1")

    def test_dataclass_with_its_own_constructor_is_skipped(self):
        @dataclass(init=False)
        class OwnConstructor:
            count: int

            def __init__(self, count: object) -> None:
                self.count = count  # type: ignore[assignment]

        class Card(Component):
            citry = Citry()
            Kwargs = OwnConstructor

            template = """
              <span>{{ count }}</span>
            """

        assert _renders(Card, count="1")

    def test_pydantic_kwargs_keep_their_own_validation(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs(BaseModel):
                count: int

            template = """
              <span>{{ count }}</span>
            """

        # Pydantic converts "1" to 1 itself; Citry does not check again.
        assert "1" in str(Card(count="1"))

    def test_slots_are_not_checked(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Slots:
                body: str

            template = """
              <c-slot name="body" />
            """

        assert "text" in str(Card(slots={"body": "text"}))


class TestDataMethods:
    def _component(self, app: Citry, data_method: str, returned: object, *, schema_name: str) -> type[Component]:
        schema = type(schema_name, (), {"__annotations__": {"count": int}})

        def method(self: Component, kwargs: object, slots: object) -> object:
            return returned(type(self).__dict__[schema_name]) if callable(returned) else returned

        return type(
            "Card",
            (Component,),
            {
                "citry": app,
                schema_name: schema,
                data_method: method,
                "template": """
                  <span></span>
                """,
                "__module__": __name__,
            },
        )

    @pytest.mark.parametrize(
        ("data_method", "schema_name"),
        [("template_data", "TemplateData"), ("js_data", "JsData"), ("css_data", "CssData")],
    )
    def test_returned_dict_is_checked(self, data_method: str, schema_name: str):
        good = self._component(Citry(), data_method, {"count": 1}, schema_name=schema_name)
        bad = self._component(Citry(), data_method, {"count": "1"}, schema_name=schema_name)

        assert _renders(good)
        with pytest.raises(TypeError, match=rf"Card\.{schema_name}\.count expects int, got str"):
            str(bad())

    def test_returned_schema_instance_is_checked(self):
        app = Citry()
        bad = self._component(app, "template_data", lambda schema: schema(count="1"), schema_name="TemplateData")

        with pytest.raises(TypeError, match=r"Card\.TemplateData\.count expects int, got str"):
            str(bad())


@pytest.mark.parametrize("mode", [False, True, "vue"], ids=["ordinary", "simple", "simple-vue"])
def test_every_render_path_checks_kwargs(mode: object):
    # A simple="vue" child called from a template renders without a Python
    # instance, through its own input construction.
    app = Citry()

    class Child(Component):
        citry = app
        simple = mode  # type: ignore[assignment]

        class Kwargs:
            count: int

        template = """
          <span>{{ count }}</span>
        """

    class Parent(Component):
        citry = app

        class Kwargs:
            count: object

        template = """
          <div><c-Child c-count="count" /></div>
        """

    assert "<span" in str(Parent(count=1))
    with pytest.raises(TypeError, match=r"Child\.Kwargs\.count expects int, got str"):
        str(Parent(count="1"))


class TestState:
    def _app(self) -> Citry:
        app = Citry(secret=SIGNING_KEY)
        app.set_mounted_prefix("/citry")
        return app

    def test_state_from_kwargs_is_checked(self):
        app = self._app()

        class Counter(Component):
            citry = app

            class Kwargs:
                count: object = 0

            class State:
                count: int = 0

            # State is built only for a component with Events.
            class Events:
                def increment(self, state: object) -> None:
                    pass

            template = """
              <button @c-click="increment">{{ count }}</button>
            """

        assert _renders(Counter, count=1)
        with pytest.raises(TypeError, match=r"Counter\.State\.count expects int, got str"):
            str(Counter(count="1"))

    def test_state_from_state_data_is_checked(self):
        app = self._app()

        class Counter(Component):
            citry = app

            class State:
                count: int = 0

            class Events:
                def increment(self, state: object) -> None:
                    pass

            def state_data(self, kwargs: object, slots: object) -> dict[str, object]:
                return {"count": "1"}

            template = """
              <button @c-click="increment"></button>
            """

        with pytest.raises(TypeError, match=r"Counter\.State\.count expects int, got str"):
            str(Counter())

    def test_state_rebuilt_from_an_event_token_is_not_checked(self):
        # The signed token stores the tuple as a JSON list. A check of the
        # rebuilt State would fail every event call for this component.
        app = self._app()

        class Tags(Component):
            citry = app

            class State:
                tags: tuple[str, ...] = ("a",)

            class Events:
                def touch(self, state: object) -> None:
                    pass

            template = """
              <button @c-click="touch">tags</button>
            """

        token = mint_state_token(
            Tags.State(tags=("a", "b")),
            class_id=Tags.class_id,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        call = {
            "componentClassId": Tags.class_id,
            "handlerName": "touch",
            "callerRenderId": "r1",
            "args": {},
            "stateToken": token,
        }
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": [call]}
        result = EventsDispatcher().dispatch(envelope, TransportContext(transport="http", citry=app))

        assert result["results"][0]["ok"] is True, result

    def test_event_handler_sees_a_tuple_and_can_render_from_it(self):
        # The token and browser updates carry JSON lists. Citry turns them back
        # into tuples, so a re-render that passes the State on to Kwargs
        # declared as a tuple passes the check.
        app = self._app()
        seen: list[object] = []

        class Tags(Component):
            citry = app

            class Kwargs:
                tags: tuple[str, ...] = ()

            class State:
                tags: tuple[str, ...] = ()
                _model = ("tags",)

            class Events:
                def touch(self, state: Any) -> object:
                    seen.append(state.tags)
                    return Tags(tags=state.tags)

            template = """
              <button @c-click="touch">{{ tags }}</button>
            """

        token = mint_state_token(
            Tags.State(tags=("a", "b")),
            class_id=Tags.class_id,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        for updates in (None, {"tags": ["c"]}):
            call: dict[str, object] = {
                "componentClassId": Tags.class_id,
                "handlerName": "touch",
                "callerRenderId": "r1",
                "args": {},
                "stateToken": token,
            }
            if updates is not None:
                call["stateUpdates"] = updates
            envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": [call]}
            result = EventsDispatcher().dispatch(envelope, TransportContext(transport="http", citry=app))
            assert result["results"][0]["ok"] is True, result

        assert seen == [("a", "b"), ("c",)]


class TestSwitches:
    def test_check_runs_in_both_modes(self):
        for mode in ("development", "production"):
            app = Citry(mode=mode)
            assert not _renders(_card(app, int), value="1")

    def test_engine_setting_turns_the_check_off(self):
        app = Citry(lint=LintSettings(check_input_types=False))
        assert app.settings.lint.check_input_types is False
        assert _renders(_card(app, int), value="1")

    def test_engine_setting_defaults_to_checking(self):
        app = Citry()
        assert app.settings.lint.check_input_types is True
        assert not _renders(_card(app, int), value="1")

    def test_lint_class_turns_the_check_off(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs:
                value: int

            class Lint:
                check_input_types = False

            template = """
              <span>{{ value }}</span>
            """

        assert _renders(Card, value="1")

    def test_lint_class_turns_the_check_on_when_the_engine_turns_it_off(self):
        app = Citry(lint=LintSettings(check_input_types=False))

        class Card(Component):
            citry = app

            class Kwargs:
                value: int

            class Lint:
                check_input_types = True

            template = """
              <span>{{ value }}</span>
            """

        assert not _renders(Card, value="1")

    def test_subclass_inherits_overrides_and_resets_the_lint_class(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs:
                value: int

            class Lint:
                check_input_types = False

            template = """
              <span>{{ value }}</span>
            """

        class InheritsCard(Card):
            pass

        class StrictCard(Card):
            class Lint:
                check_input_types = True

        class OtherLintCard(Card):
            # A Lint class that sets only a rule keeps the parent's choice.
            class Lint:
                rule_unknown_template_variable = "warning"

        class ResetCard(Card):
            Lint = None

        assert _renders(InheritsCard, value="1")
        assert not _renders(StrictCard, value="1")
        assert _renders(OtherLintCard, value="1")
        # None stops inheritance and follows the engine, which checks.
        assert not _renders(ResetCard, value="1")

    def test_lint_class_on_a_separate_base_class_applies(self):
        app = Citry()

        class Base(Component):
            citry = app

            class Lint:
                check_input_types = False

        class Card(Base):
            class Kwargs:
                value: int

            template = """
              <span>{{ value }}</span>
            """

        assert _renders(Card, value="1")

    def test_engine_setting_must_be_a_bool(self):
        with pytest.raises(TypeError, match=r"LintSettings\.check_input_types must be a bool, got str"):
            LintSettings(check_input_types="false")  # type: ignore[arg-type]

    def test_lint_class_setting_must_be_a_bool(self):
        app = Citry()
        with pytest.raises(TypeError, match=r"Card\.Lint\.check_input_types must be True or False, got 'no'"):

            class Card(Component):
                citry = app

                class Lint:
                    check_input_types = "no"

    def test_lint_class_still_rejects_a_misspelled_setting(self):
        app = Citry()
        with pytest.raises(ValueError, match=r"Component Card\.Lint has unknown setting\(s\): check_input_type$"):

            class Card(Component):
                citry = app

                class Lint:
                    check_input_type = False

    def test_library_component_lint_class(self):
        class Badge(LibraryComponent):
            class Kwargs:
                count: int

            class Lint:
                check_input_types = False

            template = """
              <span>{{ count }}</span>
            """

        class Loose(LibraryComponent):
            class Lint:
                check_input_types = 1

            template = """
              <span></span>
            """

        app = Citry()
        app.register_library(ComponentLibrary(name="badges", components=(Badge,)))
        assert _renders(app.get("Badge"), count="1")

        # A library definition is checked when an engine installs it.
        with pytest.raises(TypeError, match=r"Loose\.Lint\.check_input_types must be True or False, got 1"):
            Citry().register_library(ComponentLibrary(name="loose", components=(Loose,)))


def test_django_lazy_text_is_accepted_for_str():
    # gettext_lazy() builds this same kind of object; lazy() needs no Django
    # settings, so the test does not configure Django for the whole worker.
    functional = pytest.importorskip("django.utils.functional")
    lazy_text = functional.lazy(lambda: "Save", str)()

    app = Citry()
    card = _card(app, str)
    assert not isinstance(lazy_text, str)
    assert _renders(card, value=lazy_text)
    assert not _renders(_card(Citry(), int), value=lazy_text)


class TestErrorHints:
    def test_literal_asks_for_one_of_the_allowed_values(self):
        card = _card(Citry(), Literal["a", "b"])

        with pytest.raises(TypeError, match=r"expects Literal\['a', 'b'\], got str \('c'\)\. Use one of the values"):
            str(card(value="c"))

    def test_none_is_written_as_none(self):
        card = _card(Citry(), int)

        with pytest.raises(TypeError, match=r"expects int, got None \(None\)\. .* to accept None\."):
            str(card(value=None))

    def test_same_class_name_shows_the_module(self):
        other = type("Row", (), {"__module__": "elsewhere"})
        card = _card(Citry(), Row)

        with pytest.raises(TypeError, match=r"expects Row, got elsewhere\.Row"):
            str(card(value=other()))

    def test_text_from_a_template_attribute_suggests_c_prefix(self):
        app = Citry()
        _card(app, int)

        class Page(Component):
            citry = app

            template = """
              <c-Card value="18" />
            """

        with pytest.raises(TypeError, match=r'write c-value="\.\.\." to pass a Python value'):
            str(Page())


class TestRememberedTypes:
    def test_one_check_per_schema_per_render(self, monkeypatch: pytest.MonkeyPatch):
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs:
                count: int

            class TemplateData:
                count: int

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:
                return {"count": kwargs.count}

            template = """
              <span>{{ count }}</span>
            """

        calls: list[type] = []
        original = input_types._schema_checks_for

        def count_calls(schema: type) -> object:
            calls.append(schema)
            return original(schema)

        monkeypatch.setattr(input_types, "_schema_checks_for", count_calls)
        str(Card(count=1))

        assert calls == [Card.Kwargs, Card.TemplateData]

    def test_remembered_types_are_bounded(self):
        card = _card(Citry(), Row)
        subclasses = [type(f"Row{index}", (Row,), {}) for index in range(40)]
        for subclass in subclasses:
            assert _renders(card, value=subclass())

        [check] = card.Kwargs.__dict__["_citry_input_type_checks"]
        assert len(check.accepted) <= 33

    def test_proxy_type_is_not_remembered_for_what_it_wraps(self):
        card = _card(Citry(), str)

        assert _renders(card, value=wrapt.ObjectProxy("text"))
        assert not _renders(card, value=wrapt.ObjectProxy(1))
