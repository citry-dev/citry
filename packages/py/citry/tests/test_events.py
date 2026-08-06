"""
Tests for the events extension skeleton: registration, raw-class capture,
the State contract and its meta, the handler vocabulary and its
class-definition errors, and the three-level config resolution
(docs/design/events.md sections 3.1 to 3.6 and 7.2).
"""

import functools
import gc
import json
import sys
import typing
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import timedelta
from typing import ClassVar
from weakref import ref

import pytest

import citry as citry_module
from citry import Citry as _Citry
from citry import Component
from citry.ext.events import EventsExtension, event
from citry.ext.events.handlers import EventOptions, event_options
from citry.ext.events.schemas import validate_args


def _events_ext(app):
    return app.extensions.get_extension("events")


# Root-level State classes for the `State = SomeClass` assignment form.
class TodoState:
    project_id: int
    query: str = ""

    def render(self):
        return f"todo:{self.project_id}:{self.query}"


class SearchIn:
    query: str = ""
    limit: int = 10


@dataclass
class IntrospectionEventIn:
    title: str = field(metadata={"description": "The public title."})
    count: int = 2


class _IntrospectionAnnotationDict(dict):
    pass


# Runtime Events validation accepts ordinary dict subclasses as annotation
# mappings and constructs ``value`` normally. Introspection deliberately
# refuses to walk a container subclass, so the public schema is opaque.
IntrospectionOpaqueIn = type(
    "IntrospectionOpaqueIn",
    (),
    {
        "__module__": __name__,
        "__annotations__": _IntrospectionAnnotationDict({"value": int}),
    },
)


class IntrospectionEmptyIn:
    marker: ClassVar[int] = 1


def _events_introspection_catalog(app, *, include_default_values=False):
    payload = app.inspect_components(
        include_default_values=include_default_values,
        include_extensions=("events",),
    ).to_dict()
    return payload, {component["name"]: component for component in payload["components"]}


class TestRegistration:
    def test_events_is_a_builtin(self):
        app = _Citry()
        assert [ext.name for ext in app.extensions._extensions] == ["cache", "dependencies", "events"]
        assert isinstance(_events_ext(app), EventsExtension)

    def test_config_is_the_typed_base(self):
        # The class the weaving uses and the typing base are the same class.
        assert EventsExtension.Config is citry_module.Events

    def test_render_cache_version_tracks_the_binding_schema_hard_cut(self):
        assert EventsExtension.render_cache_version == 1


class TestStateCapture:
    def test_component_exposes_the_optional_state_declaration(self):
        assert Component.State is None

        app = _Citry()

        class Plain(Component):
            citry = app

        assert Plain.State is None

    def test_nested_state_converted_to_dataclass(self):
        app = _Citry()

        class Doc(Component):
            citry = app

            class State:
                doc_id: int
                title: str = ""

        info = _events_ext(app).resolve(Doc)
        assert is_dataclass(info.state_cls)
        assert [f.name for f in fields(info.state_cls)] == ["doc_id", "title"]
        # The class attribute becomes the converted class (the Kwargs treatment).
        assert Doc.State is info.state_cls
        # slots, and mutable (non-frozen).
        assert hasattr(info.state_cls, "__slots__")
        instance = info.state_cls(doc_id=1)
        instance.title = "changed"
        assert instance.title == "changed"

    def test_assigned_root_state_converted(self):
        app = _Citry()

        class Todo(Component):
            citry = app
            State = TodoState

        info = _events_ext(app).resolve(Todo)
        assert is_dataclass(info.state_cls)
        assert [f.name for f in fields(info.state_cls)] == ["project_id", "query"]
        assert Todo.State is info.state_cls
        # The module-level class the user assigned stays untouched.
        assert not is_dataclass(TodoState)
        assert "__dataclass_fields__" not in vars(TodoState)
        # Methods survive the conversion, and `self` in them is the state.
        assert info.state_cls(project_id=7).render() == "todo:7:"

        # A second component sharing the same root class converts identically.
        class Other(Component):
            citry = app
            State = TodoState

        other_info = _events_ext(app).resolve(Other)
        assert is_dataclass(other_info.state_cls)
        assert [f.name for f in fields(other_info.state_cls)] == ["project_id", "query"]
        assert not is_dataclass(TodoState)

    def test_state_kwargs_subclass_inherits_field_declarations(self):
        app = _Citry()

        class Leaf(Component):
            citry = app

            class Kwargs:
                title: str
                count: int = 3

            class State(Kwargs):
                extra: str = "x"

        info = _events_ext(app).resolve(Leaf)
        assert [f.name for f in fields(info.state_cls)] == ["title", "count", "extra"]

    def test_explicitly_decorated_dataclass_kept(self):
        app = _Citry()

        @dataclass
        class Explicit:
            a: int = 0

        class Comp(Component):
            citry = app
            State = Explicit

        info = _events_ext(app).resolve(Comp)
        assert info.state_cls is Explicit

    def test_frozen_state_rejected(self):
        app = _Citry()

        @dataclass(frozen=True)
        class Frozen:
            a: int = 0

        with pytest.raises(ValueError, match="frozen") as err:

            class Comp(Component):
                citry = app
                State = Frozen

        assert (
            "Component Comp: State is a frozen dataclass. State must stay mutable"
            " (handlers mutate it and the changes travel back to the client);"
            " declare it without frozen=True." in str(err.value)
        )

    def test_state_none_declares_no_state(self):
        app = _Citry()

        class Parent(Component):
            citry = app

            class State:
                a: int = 1

        class Child(Parent):
            citry = app
            State = None

        ext = _events_ext(app)
        assert ext.resolve(Parent).state_cls is not None
        assert ext.resolve(Child).state_cls is None

    def test_state_inherited_by_component_subclass(self):
        app = _Citry()

        class Parent(Component):
            citry = app

            class State:
                a: int = 1

        class Child(Parent):
            citry = app

        ext = _events_ext(app)
        assert ext.resolve(Child).state_cls is ext.resolve(Parent).state_cls

    def test_child_state_declaration_automatically_extends_parent_state(self):
        app = _Citry()

        class Parent(Component):
            citry = app

            class State:
                parent: str = "parent"

                def label(self):
                    return self.parent

        class Child(Parent):
            class State:
                child: str = "child"

                def label(self):
                    return super().label() + ":" + self.child

        info = _events_ext(app).resolve(Child)
        assert [field.name for field in fields(info.state_cls)] == ["parent", "child"]
        assert info.state_cls().label() == "parent:child"

    def test_state_multiple_inheritance_follows_component_c3(self):
        app = _Citry()

        class Common(Component):
            citry = app

            class State:
                shared: str = "common"

        class Left(Common):
            class State:
                left: str = "left"
                shared: str = "left-shared"

        class Right(Common):
            class State:
                right: str = "right"
                shared: str = "right-shared"

        class Combined(Left, Right):
            pass

        state_cls = _events_ext(app).resolve(Combined).state_cls
        assert [field.name for field in fields(state_cls)] == ["shared", "right", "left"]
        assert state_cls().shared == "left-shared"

    def test_state_must_be_a_class(self):
        app = _Citry()

        with pytest.raises(ValueError, match="must be a class") as err:

            class Comp(Component):
                citry = app
                State = 5

        assert "Component Comp: 'State' must be a class (or None to declare no state); got 5." in str(err.value)

    def test_underscore_state_field_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="underscore") as err:

            class Comp(Component):
                citry = app

                class State:
                    _secret: int

        assert (
            "Component Comp: State declares field '_secret'. State fields cannot start with"
            " an underscore (fields are the wire contract); underscore names are reserved"
            " for the State meta: _public, _model, _storage, _max_bytes, _max_age." in str(err.value)
        )

    def test_underscore_field_on_explicit_dataclass_rejected(self):
        # A user-decorated dataclass is kept as-is by the conversion, but its
        # fields obey the same wire contract as a plain declaration.
        app = _Citry()

        @dataclass
        class Hidden:
            _secret: int

        with pytest.raises(ValueError, match="_secret") as err:

            class Comp(Component):
                citry = app
                State = Hidden

        assert (
            "Component Comp: State declares field '_secret'. State fields cannot start with"
            " an underscore (fields are the wire contract); underscore names are reserved"
            " for the State meta: _public, _model, _storage, _max_bytes, _max_age." in str(err.value)
        )

    def test_underscore_field_with_default_on_explicit_dataclass_rejected(self):
        # With a default the underscore name also lands in the class __dict__;
        # it still fails as a field, not as an unrecognized meta attribute.
        app = _Citry()

        @dataclass
        class Hidden:
            _secret: int = 5

        with pytest.raises(ValueError, match="_secret") as err:

            class Comp(Component):
                citry = app
                State = Hidden

        assert "Component Comp: State declares field '_secret'." in str(err.value)
        assert "not a recognized State meta attribute" not in str(err.value)

    def test_underscore_field_from_dataclass_base_rejected(self):
        app = _Citry()

        @dataclass
        class DataBase:
            _hidden: str = ""

        with pytest.raises(ValueError, match="_hidden") as err:

            class Comp(Component):
                citry = app

                class State(DataBase):
                    visible: int = 0

        assert (
            "Component Comp: State declares field '_hidden'. State fields cannot start with"
            " an underscore (fields are the wire contract); underscore names are reserved"
            " for the State meta: _public, _model, _storage, _max_bytes, _max_age." in str(err.value)
        )

    def test_unknown_underscore_state_attr_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_pubic") as err:

            class Comp(Component):
                citry = app

                class State:
                    x: int = 0
                    _pubic = ("x",)

        assert (
            "Component Comp: '_pubic' is not a recognized State meta attribute. Underscore"
            " names on State are reserved for the meta:"
            " _public, _model, _storage, _max_bytes, _max_age." in str(err.value)
        )

    def test_underscore_state_methods_are_helpers(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                n: int = 1

                def _fmt(self):
                    return f"n={self.n}"

                def render(self):
                    return self._fmt()

        info = _events_ext(app).resolve(Comp)
        assert info.state_cls(n=4).render() == "n=4"


class TestStateMeta:
    def test_meta_defaults(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                a: int
                b: str = ""

        meta = _events_ext(app).resolve(Comp).state_meta
        # _model defaults to _public defaults to all fields.
        assert meta.public == ("a", "b")
        assert meta.model == ("a", "b")
        assert meta.storage == "signed"
        assert meta.max_bytes == 8192
        assert meta.max_age is None

    def test_narrowed_public_narrows_model_too(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                a: int
                b: str = ""
                _public = ("a",)

        meta = _events_ext(app).resolve(Comp).state_meta
        assert meta.public == ("a",)
        assert meta.model == ("a",)

    def test_model_clamps_below_public(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                a: int
                b: str = ""
                _model = ("a",)

        meta = _events_ext(app).resolve(Comp).state_meta
        assert meta.public == ("a", "b")
        assert meta.model == ("a",)

    def test_model_must_be_subset_of_public(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_model") as err:

            class Comp(Component):
                citry = app

                class State:
                    a: int
                    b: str = ""
                    _public = ("a",)
                    _model = ("b",)

        assert (
            "Component Comp: State._model lists 'b', which is not in _public. Every _model"
            " field must also be public; _public fields: a." in str(err.value)
        )

    def test_public_must_name_declared_fields(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_public") as err:

            class Comp(Component):
                citry = app

                class State:
                    title: str = ""
                    _public = ("titel",)

        assert (
            "Component Comp: State._public lists 'titel', which is not a State field."
            " Declared fields: title." in str(err.value)
        )

    def test_storage_and_limits_stored(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                a: int = 0
                _storage = "server"
                _max_bytes = 1024
                _max_age = timedelta(minutes=5)

        meta = _events_ext(app).resolve(Comp).state_meta
        assert meta.storage == "server"
        assert meta.max_bytes == 1024
        assert meta.max_age == timedelta(minutes=5)

    def test_negative_max_age_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_max_age"):

            class Comp(Component):
                citry = app

                class State:
                    value: int = 0
                    _max_age = timedelta(seconds=-1)

    def test_unknown_storage_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_storage") as err:

            class Comp(Component):
                citry = app

                class State:
                    a: int = 0
                    _storage = "redis"

        assert "Component Comp: State._storage must be one of 'signed', 'server'; got 'redis'." in str(err.value)


class TestStateData:
    def test_default_derivation_from_same_named_kwargs(self):
        app = _Citry()

        class Todo(Component):
            citry = app

            class Kwargs:
                project_id: int
                query: str = ""

            State = TodoState

        component = Todo._create_instance(kwargs={"project_id": 5, "query": "q"})
        state = _events_ext(app).build_state(component)
        assert (state.project_id, state.query) == (5, "q")

    def test_state_field_defaults_fill_gaps(self):
        app = _Citry()

        class Todo(Component):
            citry = app

            class Kwargs:
                project_id: int

            State = TodoState

        component = Todo._create_instance(kwargs={"project_id": 5})
        state = _events_ext(app).build_state(component)
        assert (state.project_id, state.query) == (5, "")

    def test_field_with_no_kwarg_and_no_default_is_a_render_error(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                needed: int

        component = Comp._create_instance(kwargs={})
        with pytest.raises(ValueError, match="needed") as err:
            _events_ext(app).build_state(component)
        assert (
            "Component Comp: cannot build State: field 'needed' has no matching kwarg and"
            " no default. Pass a kwarg of the same name, give the State field a default,"
            " or define state_data() on the component." in str(err.value)
        )

    def test_state_data_override_returning_dict(self):
        app = _Citry()

        class Doc(Component):
            citry = app

            class Kwargs:
                doc: dict
                title: str = ""

            class State:
                doc_id: int
                title: str = ""

            def state_data(self, kwargs, slots):
                return {"doc_id": kwargs.doc["pk"], "title": kwargs.title}

        component = Doc._create_instance(kwargs={"doc": {"pk": 7}, "title": "T"})
        state = _events_ext(app).build_state(component)
        assert (state.doc_id, state.title) == (7, "T")

    def test_state_data_override_returning_state_instance(self):
        app = _Citry()

        class Doc(Component):
            citry = app

            class Kwargs:
                doc: dict

            class State:
                doc_id: int

            def state_data(self, kwargs, slots):
                return Doc.State(doc_id=kwargs.doc["pk"])

        component = Doc._create_instance(kwargs={"doc": {"pk": 3}})
        state = _events_ext(app).build_state(component)
        assert isinstance(state, Doc.State)
        assert state.doc_id == 3

    def test_state_data_returning_none_rejected(self):
        app = _Citry()

        class Doc(Component):
            citry = app

            class State:
                a: int = 0

            def state_data(self, kwargs, slots):
                return None

        component = Doc._create_instance(kwargs={})
        with pytest.raises(ValueError, match="state_data") as err:
            _events_ext(app).build_state(component)
        assert (
            "Component Doc: state_data() returned None; return the State instance"
            " (Doc.State(...)) or a dict of its fields." in str(err.value)
        )

    def test_state_data_returning_wrong_type_rejected(self):
        app = _Citry()

        class Doc(Component):
            citry = app

            class State:
                a: int = 0

            def state_data(self, kwargs, slots):
                return ["nope"]

        component = Doc._create_instance(kwargs={})
        with pytest.raises(ValueError, match="state_data") as err:
            _events_ext(app).build_state(component)
        assert (
            "Component Doc: state_data() must return the State instance (Doc.State(...))"
            " or a dict of its fields; got list." in str(err.value)
        )

    def test_state_data_without_state_class_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="state_data") as err:

            class Comp(Component):
                citry = app

                def state_data(self, kwargs, slots):
                    return {}

        assert (
            "Component Comp defines state_data() but declares no State class. Declare a"
            " State class on the component (or remove state_data)." in str(err.value)
        )

    def test_state_none_child_skips_inherited_state_data(self):
        # A child opting out with ``State = None`` keeps its parent's
        # inherited state_data(); it must not fail class definition, and the
        # inherited method is simply never called.
        app = _Citry()

        class Parent(Component):
            citry = app

            class State:
                a: int = 0

            def state_data(self, kwargs, slots):
                return {"a": 1}

        class Child(Parent):
            citry = app
            State = None

        ext = _events_ext(app)
        assert ext.resolve(Child).state_cls is None
        component = Child._create_instance(kwargs={})
        assert ext.build_state(component) is None

    def test_build_state_is_none_without_state(self):
        app = _Citry()

        class Comp(Component):
            citry = app

        component = Comp._create_instance(kwargs={})
        assert _events_ext(app).build_state(component) is None


class TestHandlerEnumeration:
    def test_public_defs_are_handlers_in_definition_order(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                def save(self):
                    return None

                def refresh(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        assert list(info.handlers) == ["save", "refresh"]
        assert info.handlers["save"].method_name == "save"
        assert info.handlers["save"].params == ()

    def test_underscore_defs_are_helpers_not_handlers(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                def _helper(self):
                    return 1

                def go(self):
                    return self._helper()

        info = _events_ext(app).resolve(Comp)
        assert list(info.handlers) == ["go"]

    def test_context_hook_recognized_as_config(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                def _context(self):
                    return {"user": "u"}

                def go(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        assert list(info.handlers) == ["go"]
        assert info.context is not None
        assert info.context.__name__ == "_context"

    def test_unknown_underscore_events_attr_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_guardd") as err:

            class Comp(Component):
                citry = app

                class Events:
                    _guardd = "typo"

        assert (
            "Component Comp: invalid config field on its nested 'Events' class (the"
            " 'events' extension). '_guardd' is not a recognized Events config attribute;"
            " the recognized names are:"
            " _guard, _context, _csrf, _methods, _debounce, _throttle, _topics, _max_envelope_bytes."
            " Did you mean '_guard'?" in str(err.value)
        )

    def test_handlers_inherit_through_component_subclassing(self):
        app = _Citry()

        class Parent(Component):
            citry = app

            class Events:
                def go(self):
                    return None

        class Child(Parent):
            citry = app

        info = _events_ext(app).resolve(Child)
        assert list(info.handlers) == ["go"]

    def test_subclass_events_automatically_extend_parent_events(self):
        app = _Citry()

        class Parent(Component):
            citry = app

            class Events:
                def go(self):
                    return None

        class Child(Parent):
            citry = app

            class Events:
                def extra(self):
                    return None

        info = _events_ext(app).resolve(Child)
        assert list(info.handlers) == ["go", "extra"]

    def test_events_multiple_inheritance_follows_component_c3(self):
        app = _Citry()

        class Common(Component):
            citry = app

            class Events:
                def common(self):
                    return "common"

        class Left(Common):
            class Events:
                def left(self):
                    return "left"

                def common(self):
                    return "left-common"

        class Right(Common):
            class Events:
                def right(self):
                    return "right"

                def common(self):
                    return "right-common"

        class Combined(Left, Right):
            pass

        info = _events_ext(app).resolve(Combined)
        assert set(info.handlers) == {"common", "left", "right"}
        assert info.handlers["common"].func(None) == "left-common"

    def test_events_none_on_first_c3_branch_shadows_later_branch(self):
        app = _Citry()

        class Muted(Component):
            citry = app
            Events = None

        class Kept(Component):
            citry = app

            class Events:
                def kept(self):
                    return None

        class Combined(Muted, Kept):
            pass

        assert _events_ext(app).resolve(Combined).handlers == {}

    def test_events_none_stops_inheritance(self):
        app = _Citry()

        class Parent(Component):
            citry = app

            class Events:
                def go(self):
                    return None

        class Child(Parent):
            citry = app
            Events = None

        assert _events_ext(app).resolve(Child).handlers == {}

    def test_typed_base_members_are_not_handlers(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events(citry_module.Events):
                def go(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        # The base's own members (the `component` property, `__init__`) are
        # framework members, never handlers.
        assert list(info.handlers) == ["go"]

    def test_events_must_be_a_class(self):
        app = _Citry()

        with pytest.raises(ValueError, match="must be a class") as err:

            class Comp(Component):
                citry = app
                Events = 5

        assert "Component Comp: 'Events' must be a class (or None to declare no events); got 5." in str(err.value)

    def test_staticmethod_handler_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="staticmethod") as err:

            class Comp(Component):
                citry = app

                class Events:
                    @staticmethod
                    def ping():
                        return None

        assert (
            "Component Comp: event handler 'ping' cannot be a staticmethod or classmethod;"
            " handlers are plain methods and receive 'self' (the per-call Events instance)." in str(err.value)
        )

    def test_event_decorator_on_helper_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_helper") as err:

            class Comp(Component):
                citry = app

                class Events:
                    @event(name="x")
                    def _helper(self):
                        return None

        assert (
            "Component Comp: @event cannot decorate '_helper': underscore defs are private"
            " helpers, not handlers. Rename it without the leading underscore to expose it"
            " as an event." in str(err.value)
        )


class TestSignatureValidation:
    def test_unknown_parameter_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="qery") as err:

            class Comp(Component):
                citry = app

                class Events:
                    def search(self, qery):
                        return None

        assert (
            "Component Comp: event handler 'search' declares parameter 'qery', which is not"
            " in the handler vocabulary. Handler parameters come from:"
            " data, state, context, request, event." in str(err.value)
        )

    def test_var_positional_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="args") as err:

            class Comp(Component):
                citry = app

                class Events:
                    def go(self, *args):
                        return None

        assert (
            "Component Comp: event handler 'go' declares '*args'; event handlers cannot"
            " take '*args' or '**kwargs' (the signature is the schema). Declare only the"
            " parameters you need from: data, state, context, request, event." in str(err.value)
        )

    def test_var_keyword_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="kwargs") as err:

            class Comp(Component):
                citry = app

                class Events:
                    def go(self, **kwargs):
                        return None

        assert "declares '**kwargs'" in str(err.value)

    def test_state_on_stateless_component_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="State") as err:

            class Comp(Component):
                citry = app

                class Events:
                    def go(self, state):
                        return None

        assert (
            "Component Comp: event handler 'go' declares 'state', but Comp declares no"
            " State class. Declare a State class on the component, or drop the 'state'"
            " parameter." in str(err.value)
        )

    def test_handler_must_take_self(self):
        app = _Citry()

        with pytest.raises(ValueError, match="self") as err:

            class Comp(Component):
                citry = app

                class Events:
                    def go():
                        return None

        assert (
            "Component Comp: event handler 'go' must declare 'self' as its first parameter"
            " (handlers are instance methods on the Events class)." in str(err.value)
        )

    def test_all_injectables_accepted(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                a: int = 0

            class Events:
                def go(self, data: SearchIn, state, context, request, event):
                    return None

        handler = _events_ext(app).resolve(Comp).handlers["go"]
        assert handler.params == ("data", "state", "context", "request", "event")
        assert handler.data_schema is SearchIn

    def test_injectable_annotations_are_advisory(self):
        # A bogus annotation must not raise on any injectable: only `data` is
        # ever resolved (state, context, request, event stay advisory).
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                a: int = 0

            class Events:
                def go(self, state: "Bogus1", context: "Bogus2", request: "Bogus3", event: "Bogus4"):  # noqa: F821
                    return None

        assert list(_events_ext(app).resolve(Comp).handlers) == ["go"]

    def test_data_requires_annotation(self):
        app = _Citry()

        with pytest.raises(ValueError, match="data") as err:

            class Comp(Component):
                citry = app

                class Events:
                    def go(self, data):
                        return None

        assert (
            "Component Comp: event handler 'go' declares 'data' without a type annotation."
            " Annotate it with the input schema class (an annotated class, a dataclass, or"
            " a Pydantic model), e.g. 'data: SearchIn'." in str(err.value)
        )

    def test_unresolvable_data_annotation_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="NoSuchSchema") as err:

            class Comp(Component):
                citry = app

                class Events:
                    def go(self, data: "NoSuchSchema"):  # noqa: F821
                        return None

        assert (
            "Component Comp: cannot resolve the 'data' annotation 'NoSuchSchema' on event"
            " handler 'go' (name 'NoSuchSchema' is not defined). Define the schema class at"
            " module level, or as a class on the component, so the name resolves at class"
            " definition." in str(err.value)
        )

    def test_data_annotation_must_be_schema_class(self):
        app = _Citry()

        with pytest.raises(ValueError, match="int") as err:

            class Comp(Component):
                citry = app

                class Events:
                    def go(self, data: int):
                        return None

        assert (
            "Component Comp: the 'data' annotation on event handler 'go' must be a class"
            " with annotated fields (an annotated class, a dataclass, or a Pydantic model);"
            " got <class 'int'>." in str(err.value)
        )

    def test_nested_schema_resolves_through_localns(self):
        # A schema class nested on the component is not in the handler's
        # module globals; the extension's local-namespace rescue resolves it.
        app = _Citry()

        class Comp(Component):
            citry = app

            class FilterIn:
                q: str = ""

            class Events:
                def go(self, data: "FilterIn"):  # noqa: F821
                    return None

        handler = _events_ext(app).resolve(Comp).handlers["go"]
        assert handler.data_schema is Comp.FilterIn

    def test_dataclass_data_schema_accepted(self):
        app = _Citry()

        @dataclass
        class In:
            n: int = 0

        class Comp(Component):
            citry = app

            class Events:
                def go(self, data: In):
                    return None

        assert _events_ext(app).resolve(Comp).handlers["go"].data_schema is In


class TestEventDecorator:
    def test_bare_decorator_keeps_defaults(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                @event
                def go(self):
                    return None

        handler = _events_ext(app).resolve(Comp).handlers["go"]
        assert handler.name == "go"
        assert handler.methods == ("POST",)
        assert event_options(handler.func) == EventOptions()

    def test_wire_name_override(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                @event(name="find")
                def search(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        assert list(info.handlers) == ["find"]
        assert info.handlers["find"].method_name == "search"

    def test_duplicate_wire_names_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="save") as err:

            class Comp(Component):
                citry = app

                class Events:
                    @event(name="save")
                    def save_a(self):
                        return None

                    def save(self):
                        return None

        assert (
            "Component Comp: two event handlers share the wire name 'save' ('save_a' and"
            " 'save'). Wire names must be unique per component; change the @event(name=...)"
            " override." in str(err.value)
        )

    def test_decorator_values_stored_on_handler(self):
        app = _Citry()

        def my_guard(events):
            return None

        def my_csrf(request):
            return None

        class Comp(Component):
            citry = app

            class Events:
                @event(methods=("get",), guard=my_guard, csrf=my_csrf, debounce=400, throttle=1000)
                def go(self):
                    return None

        handler = _events_ext(app).resolve(Comp).handlers["go"]
        assert handler.methods == ("GET",)
        assert handler.guard is my_guard
        assert handler.csrf is my_csrf
        assert handler.debounce == 400
        assert handler.throttle == 1000

    def test_queue_knobs_stored_on_handler_metadata(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                @event(latest_wins=True)
                def autosave(self):
                    return None

                @event(bundle=False)
                def export(self):
                    return None

                @event
                def refresh(self):
                    return None

                def plain(self):
                    return None

        handlers = _events_ext(app).resolve(Comp).handlers
        # Each knob rides independently; the one not given keeps its default.
        assert event_options(handlers["autosave"].func) == EventOptions(latest_wins=True)
        assert event_options(handlers["export"].func) == EventOptions(bundle=False)
        # Omitted knobs default to latest_wins=False, bundle=True; an
        # undecorated handler carries no options record at all.
        assert event_options(handlers["refresh"].func) == EventOptions()
        assert event_options(handlers["plain"].func) is None

    def test_decorator_value_validation(self):
        with pytest.raises(ValueError, match="name") as err:
            event(name="")
        assert "@event(name=...) must be a non-empty string; got ''." in str(err.value)

        with pytest.raises(ValueError, match="methods") as err:
            event(methods="POST")
        assert "@event(methods=...) must be a tuple of HTTP method names, e.g. (\"POST\",); got 'POST'." in str(
            err.value
        )

        with pytest.raises(ValueError, match="methods") as err:
            event(methods=("BAD METHOD",))
        assert "@event(methods=...) contains an invalid HTTP method name: 'BAD METHOD'." in str(err.value)

        with pytest.raises(ValueError, match="debounce") as err:
            event(debounce=-1)
        assert "@event(debounce=...) must be a non-negative int (milliseconds) or None; got -1." in str(err.value)

        with pytest.raises(ValueError, match="csrf") as err:
            event(csrf="nope")
        assert "@event(csrf=...) must be \"auto\", False, or a callable; got 'nope'." in str(err.value)

        with pytest.raises(ValueError, match="guard") as err:
            event(guard=5)
        assert "@event(guard=...) must be a callable or None; got 5." in str(err.value)

        # The classic 1-for-True: the queue knobs take real booleans only.
        with pytest.raises(ValueError, match="latest_wins") as err:
            event(latest_wins=1)
        assert "@event(latest_wins=...) must be True or False; got 1." in str(err.value)

        with pytest.raises(ValueError, match="bundle") as err:
            event(bundle="no")
        assert "@event(bundle=...) must be True or False; got 'no'." in str(err.value)


class TestConfigResolution:
    def test_factory_defaults(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                def go(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        assert info.guard is None
        assert info.context is None
        assert info.csrf == "auto"
        assert info.methods == ("POST",)
        assert info.debounce is None
        assert info.throttle is None
        assert info.topics == ()

    def test_extensions_defaults_level(self):
        def engine_guard(events):
            return None

        app = _Citry(extensions_defaults={"events": {"_guard": engine_guard, "_methods": ("PUT",), "_debounce": 250}})

        class Comp(Component):
            citry = app

            class Events:
                def go(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        assert info.guard is engine_guard
        assert info.methods == ("PUT",)
        assert info.debounce == 250
        # Handlers inherit the component-level resolution.
        assert info.handlers["go"].methods == ("PUT",)
        assert info.handlers["go"].guard is engine_guard

    def test_component_level_beats_extensions_defaults(self):
        def engine_guard(events):
            return None

        def comp_guard(events):
            return None

        app = _Citry(extensions_defaults={"events": {"_guard": engine_guard}})

        class Comp(Component):
            citry = app

            class Events:
                _guard = comp_guard

                def go(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        assert info.guard is comp_guard
        assert info.handlers["go"].guard is comp_guard

    def test_decorator_beats_component_level(self):
        def comp_guard(events):
            return None

        def handler_guard(events):
            return None

        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                _guard = comp_guard
                _debounce = 250

                @event(guard=handler_guard, debounce=0)
                def go(self):
                    return None

                def other(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        assert info.handlers["go"].guard is handler_guard
        assert info.handlers["go"].debounce == 0
        assert info.handlers["other"].guard is comp_guard
        assert info.handlers["other"].debounce == 250

    def test_guard_def_and_assignment_bind_identically(self):
        def external_guard(events):
            return None

        app = _Citry()

        class WithDef(Component):
            citry = app

            class Events:
                def _guard(self):
                    return None

                def go(self):
                    return None

        class WithAssignment(Component):
            citry = app

            class Events:
                _guard = external_guard

                def go(self):
                    return None

        ext = _events_ext(app)
        assert ext.resolve(WithDef).guard.__name__ == "_guard"
        assert ext.resolve(WithAssignment).guard is external_guard

    def test_methods_normalized_uppercase(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                _methods = ("get", "m-search")

                def go(self):
                    return None

        assert _events_ext(app).resolve(Comp).methods == ("GET", "M-SEARCH")

    def test_topics_stored_and_validated(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class State:
                project_id: int

            class Events:
                _topics = ("project:{project_id}", "global")

                def go(self, state):
                    return None

        assert _events_ext(app).resolve(Comp).topics == ("project:{project_id}", "global")

    def test_topics_placeholder_must_name_state_field(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_topics") as err:

            class Comp(Component):
                citry = app

                class State:
                    project_id: int

                class Events:
                    _topics = ("project:{proj_id}",)

                    def go(self, state):
                        return None

        assert (
            "Component Comp: Events._topics template 'project:{proj_id}' names 'proj_id',"
            " which is not a State field. Declared fields: project_id." in str(err.value)
        )

    def test_topics_placeholder_without_state_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="_topics") as err:

            class Comp(Component):
                citry = app

                class Events:
                    _topics = ("project:{project_id}",)

                    def go(self):
                        return None

        assert (
            "Component Comp: Events._topics template 'project:{project_id}' names"
            " 'project_id', but the component declares no State class (topic templates"
            " format State fields)." in str(err.value)
        )

    def test_topics_positional_placeholder_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="positional") as err:

            class Comp(Component):
                citry = app

                class State:
                    project_id: int

                class Events:
                    _topics = ("project:{}",)

                    def go(self, state):
                        return None

        assert (
            "Component Comp: Events._topics template 'project:{}' uses a positional"
            ' placeholder; name a State field instead, e.g. "{project_id}".' in str(err.value)
        )


class TestConfigFieldValidation:
    """The two-tier field rule (EventsExtension.validate_config_fields)."""

    def test_defaults_typo_rejected_at_engine_construction(self):
        with pytest.raises(ValueError, match="_guardd") as err:
            _Citry(extensions_defaults={"events": {"_guardd": lambda: None}})

        assert (
            "Extension 'events': invalid config field in the 'extensions_defaults'"
            " setting. '_guardd' is not a recognized Events config attribute; the"
            " recognized names are:"
            " _guard, _context, _csrf, _methods, _debounce, _throttle, _topics, _max_envelope_bytes."
            " Did you mean '_guard'?" in str(err.value)
        )

    def test_defaults_handler_rejected(self):
        # Event handlers live on each component's Events class; there is no
        # global default handler, so an unprefixed key in the setting fails.
        with pytest.raises(ValueError, match="refresh") as err:
            _Citry(extensions_defaults={"events": {"refresh": lambda: None}})

        assert (
            "Extension 'events': invalid config field in the 'extensions_defaults'"
            " setting. 'refresh' cannot be a global default: unprefixed names on Events"
            " are event handlers, and event handlers are defined on each component's"
            " nested Events class. Only the underscore config can be defaulted globally:"
            " _guard, _context, _csrf, _methods, _debounce, _throttle, _topics, _max_envelope_bytes." in str(err.value)
        )

    def test_defaults_config_name_without_underscore_gets_hint(self):
        # Forgetting the underscore on a config name is the likely cause of an
        # unprefixed key that resembles one; the rejection points at it.
        with pytest.raises(ValueError, match="guard") as err:
            _Citry(extensions_defaults={"events": {"guard": lambda: None}})

        assert "Did you mean '_guard'?" in str(err.value)

    def test_non_callable_handler_field_rejected(self):
        app = _Citry()

        with pytest.raises(ValueError, match="greeting") as err:

            class Comp(Component):
                citry = app

                class Events:
                    greeting = "hi"

                    def go(self):
                        return None

        assert (
            "Component Comp: invalid config field on its nested 'Events' class (the"
            " 'events' extension). 'greeting' must be an event handler (unprefixed names"
            " on Events are handlers, and a handler is a plain method defined with"
            " 'def'); got 'hi'. Configuration uses the underscore names:"
            " _guard, _context, _csrf, _methods, _debounce, _throttle, _topics, _max_envelope_bytes." in str(err.value)
        )

    def test_property_handler_rejected(self):
        # Handler enumeration would silently skip a public property (it is
        # neither handler nor config), so validation rejects it up front.
        app = _Citry()

        with pytest.raises(ValueError, match="greeting") as err:

            class Comp(Component):
                citry = app

                class Events:
                    @property
                    def greeting(self):
                        return "hi"

        assert (
            "Component Comp: invalid config field on its nested 'Events' class (the"
            " 'events' extension). 'greeting' must be an event handler (unprefixed names"
            " on Events are handlers, and a handler is a plain method defined with"
            " 'def'); got <property object" in str(err.value)
        )

    def test_non_function_callable_handler_rejected(self):
        # Callable but not a def: handler enumeration would silently skip a
        # functools.partial too, so validation rejects it up front.
        app = _Citry()

        with pytest.raises(ValueError, match="refresh") as err:

            class Comp(Component):
                citry = app

                class Events:
                    refresh = functools.partial(print, "hi")

        assert (
            "Component Comp: invalid config field on its nested 'Events' class (the"
            " 'events' extension). 'refresh' must be an event handler (unprefixed names"
            " on Events are handlers, and a handler is a plain method defined with"
            " 'def'); got functools.partial(<built-in function print>, 'hi')."
            " Configuration uses the underscore names:"
            " _guard, _context, _csrf, _methods, _debounce, _throttle, _topics, _max_envelope_bytes." in str(err.value)
        )

    def test_valid_two_tier_config_passes(self):
        # Underscore config in the setting and on the component, plus handlers
        # and a private helper on the component: all tiers accepted together.
        def my_guard(events):
            return None

        app = _Citry(extensions_defaults={"events": {"_methods": ("PUT",), "_debounce": 100}})

        class Comp(Component):
            citry = app

            class Events:
                _guard = my_guard

                def go(self):
                    return None

                def _helper(self):
                    return None

        info = _events_ext(app).resolve(Comp)
        assert list(info.handlers) == ["go"]
        assert info.methods == ("PUT",)
        assert info.debounce == 100
        assert info.guard is my_guard


class TestAmbientSlots:
    def test_ambient_members_declared_on_the_base(self):
        assert list(citry_module.Events.__annotations__) == ["state", "context", "request", "event"]

    def test_ambient_members_unpopulated_until_dispatch(self):
        app = _Citry()

        class Comp(Component):
            citry = app

            class Events:
                def go(self):
                    return None

        instance = Comp.Events(None)
        for member in ("state", "context", "request", "event"):
            with pytest.raises(AttributeError):
                getattr(instance, member)

    def test_woven_config_subclasses_the_typed_base(self):
        app = _Citry()

        class Bare(Component):
            citry = app

            class Events:
                def go(self):
                    return None

        class Typed(Component):
            citry = app

            class State:
                a: int = 0

            class Events(citry_module.Events):
                def go(self, state):
                    return None

        # Both weave onto the same base; subclassing it changes nothing.
        assert issubclass(Bare.Events, citry_module.Events)
        assert issubclass(Typed.Events, citry_module.Events)
        ext = _events_ext(app)
        assert list(ext.resolve(Bare).handlers) == list(ext.resolve(Typed).handlers) == ["go"]


class TestEventsIntrospection:
    def test_version_one_publication_shape_is_exact_and_canonical(self):
        app = _Citry(
            autodiscover=False,
            extensions_defaults={"events": {"_debounce": 250, "_throttle": 900}},
        )

        class Card(Component):
            citry = app

            class Events:
                @event(name="z-save", methods=("PATCH", "POST"), debounce=0)
                def save(self, data: IntrospectionEventIn) -> dict[str, int]:
                    """
                    Save one card.

                    Keeps the public description clean.
                    """
                    return {}

                def alpha(self):
                    return None

                def empty_schema(self, data: IntrospectionEmptyIn):
                    return None

                def opaque(self, data: IntrospectionOpaqueIn):
                    return None

        validated_opaque = validate_args(IntrospectionOpaqueIn, {"value": 1})
        assert validated_opaque.ok
        assert validated_opaque.value.value == 1
        assert validate_args(IntrospectionEmptyIn, {}).ok
        catalog, components = _events_introspection_catalog(app)

        assert catalog["extension_versions"] == {"events": 1}
        assert components["card"]["extensions"]["events"] == {
            "introspection_version": 1,
            "data": {
                "handlers": [
                    {
                        "name": "alpha",
                        "methods": ["POST"],
                        "request_schema": None,
                        "return_type_display": None,
                        "return_type_fidelity": "unavailable",
                        "description": None,
                        "debounce": 250,
                        "throttle": 900,
                    },
                    {
                        "name": "empty_schema",
                        "methods": ["POST"],
                        "request_schema": {
                            "kind": "fields",
                            "import_path": f"{__name__}.IntrospectionEmptyIn",
                            "fields": [],
                        },
                        "return_type_display": None,
                        "return_type_fidelity": "unavailable",
                        "description": None,
                        "debounce": 250,
                        "throttle": 900,
                    },
                    {
                        "name": "opaque",
                        "methods": ["POST"],
                        "request_schema": {
                            "kind": "opaque",
                            "import_path": f"{__name__}.IntrospectionOpaqueIn",
                            "fields": [],
                        },
                        "return_type_display": None,
                        "return_type_fidelity": "unavailable",
                        "description": None,
                        "debounce": 250,
                        "throttle": 900,
                    },
                    {
                        "name": "z-save",
                        # Resolved method order is meaningful and must not be
                        # alphabetized along with handler wire names.
                        "methods": ["PATCH", "POST"],
                        "request_schema": {
                            "kind": "fields",
                            "import_path": f"{__name__}.IntrospectionEventIn",
                            "fields": [
                                {
                                    "name": "title",
                                    "required": True,
                                    "type_display": "str",
                                    "type_fidelity": "normalized",
                                    "description": "The public title.",
                                },
                                {
                                    "name": "count",
                                    "required": False,
                                    "type_display": "int",
                                    "type_fidelity": "normalized",
                                    "description": None,
                                },
                            ],
                        },
                        "return_type_display": "dict[str, int]",
                        "return_type_fidelity": "normalized",
                        "description": "Save one card.\n\nKeeps the public description clean.",
                        "debounce": 0,
                        "throttle": 900,
                    },
                ]
            },
        }

    def test_plain_schemas_publish_inheritance_defaults_and_deferred_classvars_safely(self):
        factory_calls = 0

        def factory():
            nonlocal factory_calls
            factory_calls += 1
            return [1]

        class BasePayload:
            inherited: int
            real_override: int
            deferred_override: int

        class InheritedPayload(BasePayload):
            required: str
            real_override: ClassVar[int] = 1
            deferred_override: "typing.ClassVar[int]" = 2
            direct: int = 3

        class FieldPayload:
            required: str
            empty: int = field()
            value: int = field(default=4, metadata={"description": "Published value."})
            made: list[int] = field(default_factory=factory)
            hidden: int = field(default=5, init=False)
            unqualified: "ClassVar" = 1
            unqualified_item: "ClassVar[int]" = 2
            qualified: "typing.ClassVar" = 3
            qualified_item: "typing.ClassVar[int]" = 4

        app = _Citry(autodiscover=False)

        class Card(Component):
            citry = app

            class Events:
                def fields(self, data: FieldPayload):
                    return None

                def inherited(self, data: InheritedPayload):
                    return None

        assert validate_args(InheritedPayload, {"inherited": 1, "required": "ok"}).ok
        assert validate_args(FieldPayload, {"required": "ok", "empty": 1, "made": []}).ok
        _catalog, components = _events_introspection_catalog(app, include_default_values=True)
        handlers = {
            handler["name"]: handler for handler in components["card"]["extensions"]["events"]["data"]["handlers"]
        }

        assert handlers["inherited"]["request_schema"]["fields"] == [
            {
                "name": "inherited",
                "required": True,
                "type_display": "int",
                "type_fidelity": "normalized",
                "description": None,
            },
            {
                "name": "required",
                "required": True,
                "type_display": "str",
                "type_fidelity": "normalized",
                "description": None,
            },
            {
                "name": "direct",
                "required": False,
                "type_display": "int",
                "type_fidelity": "normalized",
                "description": None,
            },
        ]
        assert handlers["fields"]["request_schema"]["fields"] == [
            {
                "name": "required",
                "required": True,
                "type_display": "str",
                "type_fidelity": "normalized",
                "description": None,
            },
            {
                "name": "empty",
                "required": True,
                "type_display": "int",
                "type_fidelity": "normalized",
                "description": None,
            },
            {
                "name": "value",
                "required": False,
                "type_display": "int",
                "type_fidelity": "normalized",
                "description": "Published value.",
            },
            {
                "name": "made",
                "required": False,
                "type_display": "list[int]",
                "type_fidelity": "normalized",
                "description": None,
            },
        ]
        assert factory_calls == 0

    def test_absent_empty_inherited_and_explicit_none_events_stay_distinct(self):
        app = _Citry(autodiscover=False)

        class Bare(Component):
            citry = app

        class EmptyEvents(Component):
            citry = app

            class Events:
                pass

        class Parent(Component):
            citry = app

            class Events:
                @event(name="public-name")
                def python_name(self):
                    return None

        class Child(Parent):
            pass

        class OptOut(Parent):
            Events = None

        _catalog, components = _events_introspection_catalog(app)

        assert "events" not in components["bare"]["extensions"]
        assert components["empty-events"]["extensions"]["events"]["data"] == {"handlers": []}
        assert (
            components["child"]["extensions"]["events"]["data"] == components["parent"]["extensions"]["events"]["data"]
        )
        assert components["parent"]["extensions"]["events"]["data"]["handlers"][0]["name"] == "public-name"
        assert "python_name" not in json.dumps(components["parent"]["extensions"]["events"])
        assert "events" not in components["opt-out"]["extensions"]

    def test_annotations_defaults_and_hostile_objects_are_never_executed_or_represented(self):
        calls = {"annotation": 0, "factory": 0, "repr": 0, "str": 0}

        def explode_annotation():
            calls["annotation"] += 1
            raise AssertionError

        def explode_factory():
            calls["factory"] += 1
            raise AssertionError

        class Hostile:
            def __repr__(self):
                calls["repr"] += 1
                raise AssertionError

            def __str__(self):
                calls["str"] += 1
                raise AssertionError

        hostile_default = Hostile()
        hostile_annotation = Hostile()

        class Payload:
            generated: list[int] = field(default_factory=explode_factory)
            unsafe: object = hostile_default

        def hostile_handler(self) -> hostile_annotation:
            return None

        app = _Citry(autodiscover=False)

        class Card(Component):
            citry = app

            class Events:
                def string_annotation(self) -> "explode_annotation()":
                    return None

                hostile_annotation = hostile_handler

                def submit(self, data: Payload):
                    return None

        _catalog, components = _events_introspection_catalog(app, include_default_values=True)
        handlers = {
            handler["name"]: handler for handler in components["card"]["extensions"]["events"]["data"]["handlers"]
        }

        assert handlers["string_annotation"]["return_type_display"] == "explode_annotation()"
        assert handlers["string_annotation"]["return_type_fidelity"] == "normalized"
        if sys.version_info >= (3, 14):
            assert handlers["hostile_annotation"]["return_type_display"] == "hostile_annotation"
            assert handlers["hostile_annotation"]["return_type_fidelity"] == "normalized"
        else:
            assert handlers["hostile_annotation"]["return_type_display"] is None
            assert handlers["hostile_annotation"]["return_type_fidelity"] == "unavailable"
        request_schema = handlers["submit"]["request_schema"]
        assert request_schema["kind"] == "fields"
        assert [request_field["name"] for request_field in request_schema["fields"]] == ["generated", "unsafe"]
        for request_field in request_schema["fields"]:
            assert set(request_field) == {
                "name",
                "required",
                "type_display",
                "type_fidelity",
                "description",
            }
        assert calls == {"annotation": 0, "factory": 0, "repr": 0, "str": 0}

    @pytest.mark.skipif(sys.version_info < (3, 14), reason="native deferred annotations require Python 3.14")
    def test_native_deferred_return_annotation_is_not_executed(self):
        annotation_calls = 0

        def explode_annotation():
            nonlocal annotation_calls
            annotation_calls += 1
            return int

        app = _Citry(autodiscover=False)

        class DeferredCard(Component):
            citry = app

            class Events:
                def ping(self) -> explode_annotation():
                    return None

        _catalog, components = _events_introspection_catalog(app)
        handler = components["deferred-card"]["extensions"]["events"]["data"]["handlers"][0]

        assert annotation_calls == 0
        assert handler["return_type_display"] == "explode_annotation()"
        assert handler["return_type_fidelity"] == "normalized"

    def test_publication_excludes_private_events_state_and_queue_configuration(self):
        private_value = "PRIVATE_STATE_VALUE_MUST_NOT_BE_PUBLISHED"
        private_topic = "private-topic:{token}"

        def private_guard(events):
            return None

        def private_context(events):
            return None

        def private_csrf(request):
            return None

        app = _Citry(autodiscover=False)

        class Card(Component):
            citry = app

            class State:
                token: str = private_value

            class Events:
                _guard = private_guard
                _context = private_context
                _csrf = private_csrf
                _topics = (private_topic,)

                @event(guard=private_guard, csrf=private_csrf, latest_wins=True, bundle=False)
                def publish(self):
                    return None

        _catalog, components = _events_introspection_catalog(app)
        publication = components["card"]["extensions"]["events"]["data"]
        handler = publication["handlers"][0]

        assert set(publication) == {"handlers"}
        assert set(handler) == {
            "name",
            "methods",
            "request_schema",
            "return_type_display",
            "return_type_fidelity",
            "description",
            "debounce",
            "throttle",
        }
        serialized = json.dumps(publication, sort_keys=True)
        for excluded in (
            private_value,
            private_topic,
            "private_guard",
            "private_context",
            "private_csrf",
            "latest_wins",
            "bundle",
            "method_name",
            "func",
            "state",
            "topics",
            "csrf",
            "guard",
            "context",
        ):
            assert excluded not in serialized

    def test_inspection_does_not_load_or_render_the_template(self):
        template_data_calls = 0
        app = _Citry(autodiscover=False)

        class LazyCard(Component):
            citry = app
            template_file = "events-introspection-missing.html"

            def template_data(self, kwargs, slots):
                nonlocal template_data_calls
                template_data_calls += 1
                raise AssertionError

            class Events:
                def ping(self):
                    return None

        assert "_citry_template" not in LazyCard.__dict__
        info = app.inspect_component(
            LazyCard,
            resolve_assets=True,
            include_extensions=("events",),
        )

        assert info.assets.template.resolution == "missing"
        assert info.extensions[0].name == "events"
        assert "_citry_template" not in LazyCard.__dict__
        assert _events_ext(app).two_way_binding_targets(LazyCard) == frozenset()
        assert app._file_index == {}
        assert template_data_calls == 0

    def test_timing_values_stay_within_the_javascript_safe_integer_range(self):
        max_safe = 2**53 - 1
        app = _Citry(autodiscover=False)

        class SafeTiming(Component):
            citry = app

            class Events:
                _throttle = max_safe

                @event(debounce=max_safe)
                def ping(self):
                    return None

        _catalog, components = _events_introspection_catalog(app)
        handler = components["safe-timing"]["extensions"]["events"]["data"]["handlers"][0]
        assert handler["debounce"] == max_safe
        assert handler["throttle"] == max_safe

        with pytest.raises(ValueError, match="9007199254740991"):
            event(debounce=max_safe + 1)

        with pytest.raises(ValueError, match="9007199254740991"):

            class UnsafeTiming(Component):
                citry = app

                class Events:
                    _throttle = max_safe + 1

                    def ping(self):
                        return None

    def test_retained_events_catalog_does_not_keep_an_unregistered_component_alive(self):
        app = _Citry(autodiscover=False)

        def make_component():
            class RetainedCard(Component):
                citry = app

                class Events:
                    def ping(self):
                        return None

            return RetainedCard

        retained_card = make_component()
        retained_ref = ref(retained_card)
        catalog = app.inspect_components(include_extensions=("events",))
        app.unregister(retained_card)
        del retained_card
        gc.collect()

        assert catalog.to_dict()["components"][0]["extensions"]["events"]["data"] == {
            "handlers": [
                {
                    "name": "ping",
                    "methods": ["POST"],
                    "request_schema": None,
                    "return_type_display": None,
                    "return_type_fidelity": "unavailable",
                    "description": None,
                    "debounce": None,
                    "throttle": None,
                }
            ]
        }
        assert retained_ref() is None

    @pytest.mark.parametrize("removal", ["unregister", "clear"])
    def test_closure_bearing_events_metadata_does_not_retain_removed_component(self, removal):
        app = _Citry(autodiscover=False)

        def make_component():
            class RetainedCard(Component):
                citry = app

                class Events:
                    def ping(self):
                        return RetainedCard

            return RetainedCard

        retained_card = make_component()
        retained_ref = ref(retained_card)
        if removal == "unregister":
            app.unregister(retained_card)
        else:
            app.clear()
        del retained_card
        gc.collect()

        assert retained_ref() is None
