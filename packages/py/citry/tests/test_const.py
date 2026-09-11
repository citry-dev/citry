"""
Tests for the Const optimization (citry/constness.py): the Const marker, the
cache key built from marked values, the precomputing step that pre-computes the
constant parts of a template, and the cache that stores the results.
"""

# ruff: noqa: ANN

import gc
import json
import re
import subprocess
import sys
import textwrap
from collections import namedtuple
from dataclasses import InitVar, dataclass, field
from pathlib import Path
from typing import NamedTuple
from weakref import ref

import pytest

from citry import Citry, Component, Const, Extension, const_value, constness, is_const
from citry.constness import (
    _MAX_UNROLL_ITERATIONS,
    _UNFREEZABLE,
    ConstBodyCache,
    _ConstMapping,
    _overlay_const_mapping,
    extract_const_vars,
    freeze_const,
    precompute_const_parts,
)
from citry.nodes import ComponentNode, ExprHtmlAttr, ExprNode, FillNode, ForNode, IfNode, SlotNode, StaticHtmlAttr


class _Unhashable:
    """Equality without hashability: no stable, value-based cache key."""

    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return isinstance(other, _Unhashable) and self.x == other.x

    __hash__ = None


class TestConstMarker:
    def test_is_const(self):
        assert is_const(Const(3))
        assert not is_const(3)
        assert not is_const("x")

    def test_const_value_unwraps(self):
        assert const_value(Const(3)) == 3
        assert const_value(Const("hi")) == "hi"

    def test_const_value_unwraps_nested_markers_without_copying(self):
        for value in ("span", 3, False, None, [Const("child")]):
            assert const_value(Const(Const(Const(value)))) is value

    def test_const_value_rejects_cycles_without_hanging(self):
        source = """
from citry import Const, const_value
first = Const(1)
second = Const(first)
try:
    first.__wrapped__ = second
except RecursionError:
    pass
try:
    const_value(first)
except ValueError as error:
    assert "cycle" in str(error)
else:
    raise AssertionError("cyclic markers were accepted")
finally:
    first.__wrapped__ = 1
"""
        subprocess.run([sys.executable, "-c", source], check=True, timeout=5)

    def test_const_value_passthrough_for_plain(self):
        assert const_value(3) == 3
        assert const_value("hi") == "hi"


class TestConstUserBoundaries:
    def test_component_methods_receive_ordinary_values(self):
        sentinel = object()

        def function():
            return "called"

        seen = []
        c = Citry()

        class Probe(Component):
            citry = c

            class Kwargs:
                true: bool
                false: bool
                none: None
                sentinel: object
                name: str
                function: object

            def template_data(self, kwargs, slots):
                seen.append(
                    (
                        kwargs.true is True,
                        kwargs.false is False,
                        kwargs.none is None,
                        kwargs.sentinel is sentinel,
                        type(kwargs.name) is str,
                        re.fullmatch(r"[a-z]+", kwargs.name).group(),
                        Path("root") / kwargs.name,
                        ",".join((kwargs.name, "tail")),  # noqa: FLY002 - exact-type API regression
                        json.dumps({"name": kwargs.name}),
                        callable(kwargs.function),
                        kwargs.function(),
                    )
                )
                return {}

            template = """
                ok
            """.strip()

        Probe(
            true=Const(True),  # noqa: FBT003
            false=Const(False),  # noqa: FBT003
            none=Const(None),
            sentinel=Const(sentinel),
            name=Const("leaf"),
            function=Const(function),
        ).render()

        assert seen == [
            (True, True, True, True, True, "leaf", Path("root/leaf"), "leaf,tail", '{"name": "leaf"}', True, "called")
        ]

    def test_template_literal_and_const_variable_reach_child_callback_plain(self):
        seen = []
        c = Citry()

        class Child(Component):
            citry = c

            def template_data(self, kwargs, slots):
                seen.append((kwargs["literal"] is True, kwargs["variable"] is True))
                return {"literal": Const(kwargs["literal"]), "variable": Const(kwargs["variable"])}

            template = """
                {{ literal }}:{{ variable }}
            """.strip()

        class Page(Component):
            citry = c
            template = """
                <c-Child c-literal="True" c-variable="value" />
            """.strip()

        assert Page(value=Const(True)).render().serialize() == "True:True"  # noqa: FBT003
        assert seen == [(True, True)]

    def test_callback_returning_original_same_name_input_restores_constness(self):
        source = {"value": "same"}
        c = Citry()

        class Card(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return kwargs

            template = """
                {{ value }}
            """.strip()

        assert Card(value=Const(source["value"])).render().serialize() == "same"
        assert ["same"] in c._const_body_cache.values()

    def test_callback_renaming_an_original_input_does_not_restore_constness(self):
        c = Citry()

        class Card(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"renamed": kwargs["value"]}

            template = """
                {{ renamed }}
            """.strip()

        assert Card(value=Const("same")).render().serialize() == "same"
        (body,) = c._const_body_cache.values()
        assert any(isinstance(item, ExprNode) for item in body)

    def test_callback_returning_equal_distinct_value_does_not_restore_constness(self):
        c = Citry()

        class Card(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"value": list(kwargs["value"])}

            template = """
                {{ value }}
            """.strip()

        assert Card(value=Const([1, 2])).render().serialize() == "[1, 2]"
        (body,) = c._const_body_cache.values()
        assert any(isinstance(item, ExprNode) for item in body)

    def test_nested_marker_added_to_ordinary_container_remains_for_next_data_callback(self):
        seen = []
        c = Citry()

        class Card(Component):
            citry = c

            def template_data(self, kwargs, slots):
                kwargs["items"].append(Const("added"))
                return kwargs

            def js_data(self, kwargs, slots):
                seen.append((kwargs["items"][-1], is_const(kwargs["items"][-1])))

            template = """
                ok
            """.strip()

        Card(items=[]).render()
        assert seen == [("added", True)]

    def test_same_interned_custom_output_uses_the_accepted_identity_rule(self):
        source = {"value": "same"}
        c = Citry()

        class Card(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"value": source["value"]}

            template = """
                {{ value }}
            """.strip()

        assert Card(value=Const("same")).render().serialize() == "same"
        assert ["same"] in c._const_body_cache.values()
        source["value"] = "changed"
        assert Card(value=Const("same")).render().serialize() == "changed"

    def test_explicit_const_on_custom_output_preserves_precomputation(self):
        c = Citry()

        class Card(Component):
            citry = c

            def template_data(self, kwargs, slots):
                return {"value": Const(kwargs["value"])}

            template = """
                {{ value }}
            """.strip()

        assert Card(value=Const("same")).render().serialize() == "same"
        assert ["same"] in c._const_body_cache.values()

    def test_explicit_const_added_to_returned_kwargs_preserves_precomputation(self):
        c = Citry()

        class Card(Component):
            citry = c

            def template_data(self, kwargs, slots):
                kwargs["added"] = Const("constant")
                return kwargs

            template = """
                {{ added }}
            """.strip()

        assert Card().render().serialize() == "constant"
        assert ["constant"] in c._const_body_cache.values()

    def test_expression_evaluate_unwraps_direct_marked_mapping(self):
        sentinel = object()
        node = ExprNode(None, (0, 0), "value is sentinel", ("value", "sentinel"))

        assert node.evaluate({"value": Const(sentinel), "sentinel": sentinel}) is True

    def test_marked_roots_preserve_aliases_and_cycles_without_converting_an_unmarked_alias(self):
        shared = [Const("leaf")]
        cyclic = [shared]
        cyclic.append(cyclic)
        seen = []
        c = Citry()

        class Probe(Component):
            citry = c

            def template_data(self, kwargs, slots):
                seen.append(
                    (
                        kwargs["first"] is kwargs["second"],
                        kwargs["first"] is not kwargs["ordinary"],
                        kwargs["first"][0] == "leaf",
                        not is_const(kwargs["first"][0]),
                        is_const(kwargs["ordinary"][0]),
                        kwargs["cycle"][1] is kwargs["cycle"],
                    )
                )
                return {}

            template = """
                ok
            """.strip()

        Probe(first=Const(shared), second=Const(shared), ordinary=shared, cycle=Const(cyclic)).render()
        assert seen == [(True, True, True, True, True, True)]

    def test_marker_unwrapping_does_not_consult_an_opaque_target_class(self):
        class Opaque:
            @property
            def __class__(self):
                raise RuntimeError("opaque class consulted")

        class UnhashableMeta(type):
            __hash__ = None

        class UnhashableOpaque(metaclass=UnhashableMeta):
            pass

        target = Opaque()
        unhashable_target = UnhashableOpaque()

        values = _ConstMapping({"value": Const(target), "nested": [unhashable_target]})

        assert values["value"] is target
        assert values["nested"][0] is unhashable_target

    def test_plain_cycle_is_not_copied(self):
        cyclic = []
        cyclic.append(cyclic)
        seen = []
        c = Citry()

        class Probe(Component):
            citry = c

            def template_data(self, kwargs, slots):
                seen.append(kwargs["cycle"] is cyclic)
                return {}

            template = """
                ok
            """.strip()

        Probe(cycle=cyclic).render()
        assert seen == [True]

    def test_ordinary_builtin_graph_skips_the_alias_converter_even_with_a_nested_marker(self, monkeypatch):
        original_scanner = constness._ConstGraphScanner
        scanner_calls = 0

        def tracking_scanner():
            nonlocal scanner_calls
            scanner_calls += 1
            return original_scanner()

        monkeypatch.setattr(constness, "_ConstGraphScanner", tracking_scanner)
        cyclic = []
        cyclic.append(cyclic)

        nested = [{"value": Const("manual")}]
        plain = _ConstMapping({"cycle": cyclic, "nested": nested})

        assert plain["cycle"] is cyclic
        assert plain["nested"] is nested
        assert is_const(plain["nested"][0]["value"])
        assert scanner_calls == 0

        shared = [Const("marked")]
        marked = _ConstMapping({"first": Const(shared), "second": Const(shared)})

        assert marked["first"] is marked["second"]
        assert marked["first"] == ["marked"]
        assert scanner_calls == 1

    def test_marked_immutable_cycle_fails_deterministically(self):
        mutable = []
        cyclic = (mutable, Const("leaf"))
        mutable.append(cyclic)
        c = Citry()

        class Probe(Component):
            citry = c
            template = """
                ok
            """.strip()

        with pytest.raises(ValueError, match="cyclic tuple or frozenset"):
            Probe(value=Const(cyclic)).render()

    def test_bulk_mapping_update_preserves_aliases(self):
        shared = [Const(True)]  # noqa: FBT003
        values = _ConstMapping()

        values.update({"first": Const(shared), "second": Const(shared)})

        assert values["first"] is values["second"]
        assert values["first"] == [True]

    def test_mapping_update_preserves_duplicate_and_caller_list_semantics(self):
        marked = Const(1)
        pairs = [("value", marked), ("value", 2)]
        values = _ConstMapping({"old": Const(0)})

        values.update(pairs, extra=Const(3))

        assert pairs == [("value", marked), ("value", 2)]
        assert values == {"old": 0, "value": 2, "extra": 3}
        assert extract_const_vars(values)[0] == {"old": 0, "extra": 3}

        values.update([("value", 2), ("value", Const(1))])
        assert extract_const_vars(values)[0] == {"old": 0, "value": 1, "extra": 3}

    def test_mapping_update_normalizes_all_marked_roots_before_publishing(self):
        mutable = []
        cyclic = (mutable, Const("leaf"))
        mutable.append(cyclic)
        values = _ConstMapping({"stable": Const(1)})

        with pytest.raises(ValueError, match="cyclic tuple or frozenset"):
            values.update({"new": Const(cyclic), "stable": 2})

        assert values == {"stable": 1}
        assert extract_const_vars(values)[0] == {"stable": 1}

    def test_mapping_update_snapshots_an_exact_dict_before_marked_conversion(self):
        updates = {}

        class MutatingKey:
            active = False

            def __hash__(self):
                if self.active:
                    updates["later"] = Const("changed")
                    updates["injected"] = Const("extra")
                return 1

        key = MutatingKey()
        graph = {Const(key): Const("leaf")}
        updates.update({"graph": Const(graph), "later": Const("old")})
        key.active = True
        values = _ConstMapping()

        values.update(updates)

        assert set(values) == {"graph", "later"}
        assert list(values["graph"].values()) == ["leaf"]
        assert values["later"] == "old"
        assert extract_const_vars(values)[0]["later"] == "old"

    def test_marked_overlay_is_normalized_before_copying_its_parent_scope(self):
        parent = _ConstMapping({"keep": Const("before")})

        class MutatingKey:
            active = False

            def __hash__(self):
                if self.active:
                    parent["keep"] = "after"
                return 1

        key = MutatingKey()
        graph = {Const(key): Const("leaf")}
        key.active = True

        overlaid = _overlay_const_mapping(parent, {"graph": Const(graph)})

        assert overlaid["keep"] == "after"
        assert list(overlaid["graph"].values()) == ["leaf"]
        assert extract_const_vars(overlaid)[0] == {}

    def test_overlay_subclass_uses_the_generic_merge_path(self):
        class CustomCopyMapping(_ConstMapping):
            def copy(self):
                return {"custom": 1}

        parent = CustomCopyMapping({"keep": Const("before")})

        overlaid = _overlay_const_mapping(parent, {"new": 2})

        assert overlaid == {"keep": "before", "new": 2}
        assert extract_const_vars(overlaid)[0] == {"keep": "before"}

    def test_mapping_copy_is_isolated_and_self_update_clears_provenance(self):
        source = _ConstMapping({"value": Const(1)})

        copied = source.copy()
        copied["value"] = 2

        assert extract_const_vars(source)[0] == {"value": 1}
        assert extract_const_vars(copied)[0] == {}

        source.update(source)
        assert source == {"value": 1}
        assert extract_const_vars(source)[0] == {}

    def test_mapping_mutators_keep_const_metadata_in_sync(self):
        values = _ConstMapping({"value": Const(1)})

        values["value"] = 2
        assert extract_const_vars(values)[0] == {}

        values.setdefault("default", Const(3))
        assert extract_const_vars(values)[0] == {"default": 3}
        values.update({"default": 4})
        assert extract_const_vars(values)[0] == {}

        values |= {"merged": Const(5)}
        assert extract_const_vars(values)[0] == {"merged": 5}
        assert values.pop("merged") == 5
        assert extract_const_vars(values)[0] == {}

        values["deleted"] = Const(6)
        del values["deleted"]
        assert extract_const_vars(values)[0] == {}

        values["last"] = Const(6)
        assert values.popitem() == ("last", 6)
        values["clear"] = Const(7)
        values.clear()
        assert extract_const_vars(values)[0] == {}

    def test_marked_default_and_factory_are_plain_before_post_init(self):
        seen = []
        c = Citry()

        def make_false():
            return Const(False)  # noqa: FBT003

        class Probe(Component):
            citry = c

            class Kwargs:
                flag: bool = Const(True)  # noqa: FBT003
                made: bool = field(default_factory=make_false)

                def __post_init__(self):
                    seen.append((self.flag is True, self.made is False))

            template = """
                {{ flag }}:{{ made }}
            """

        assert Probe().render().serialize().strip() == "True:False"
        assert seen == [(True, True)]

    def test_default_factory_mutation_keeps_supplied_alias_and_nested_marker(self):
        shared = []
        seen = []
        c = Citry()

        def make_default():
            shared.append(Const("leaf"))
            return shared

        class Probe(Component):
            citry = c

            class Kwargs:
                supplied: list
                defaulted: list = field(default_factory=make_default)

                def __post_init__(self):
                    seen.append((self.supplied is self.defaulted, is_const(self.supplied[-1])))

            template = """
                ok
            """.strip()

        Probe(supplied=shared).render()
        assert seen == [(True, True)]

    def test_inert_marked_default_factory_recursively_unwraps_its_marked_root(self):
        seen = []
        c = Citry()

        def make_items():
            return Const([Const("leaf")])

        class Probe(Component):
            citry = c

            class Kwargs:
                items: list = field(default_factory=make_items)

            def template_data(self, kwargs, slots):
                seen.append((type(kwargs.items) is list, type(kwargs.items[0]) is str))
                return {"items": kwargs.items}

            template = """
                {{ items[0] }}
            """

        Probe().render()
        Probe().render()
        assert seen == [(True, True), (True, True)]
        (body,) = c._const_body_cache.values()
        assert all(not isinstance(item, ExprNode) for item in body)

    def test_init_false_defaults_are_plain_before_post_init_and_rendered(self):
        seen = []
        calls = 0
        c = Citry()

        def make_label():
            nonlocal calls
            calls += 1
            return Const("factory")

        class Probe(Component):
            citry = c

            class Kwargs:
                fixed: str = field(init=False, default=Const("default"))
                made: str = field(init=False, default_factory=make_label)

                def __post_init__(self):
                    seen.append((type(self.fixed) is str, type(self.made) is str))

            template = """
                {{ fixed }}:{{ made }}
            """

        assert Probe().render().serialize().strip() == "default:factory"
        assert seen == [(True, True)]
        assert calls == 1

    def test_init_var_marked_default_is_plain_and_not_template_data(self):
        seen = []
        c = Citry()

        class Probe(Component):
            citry = c

            class Kwargs:
                value: str = "visible"
                transient: InitVar[bool] = Const(True)  # noqa: FBT003

                def __post_init__(self, transient):
                    seen.append(transient is True)

            template = """
                {{ value }}
            """

        assert Probe().render().serialize().strip() == "visible"
        assert seen == [True]

    def test_custom_dataclass_constructor_keeps_its_own_default_semantics(self):
        c = Citry()

        @dataclass(init=False)
        class Inputs:
            value: str = "declared"

            def __init__(self):
                self.value = "custom"

        class Probe(Component):
            citry = c
            Kwargs = Inputs

            template = """
                {{ value }}
            """

        assert Probe().render().serialize().strip() == "custom"

    def test_transforming_schema_renders_the_actual_constructed_fields(self):
        c = Citry()

        class UpperTuple(namedtuple("InputBase", "value")):  # noqa: PYI024
            __slots__ = ()

            def __new__(cls, value):
                return super().__new__(cls, value.upper())

        class UpperDescriptor:
            def __get__(self, obj, owner=None):
                return "default" if obj is None else obj.__dict__["_value"]

            def __set__(self, obj, value):
                obj.__dict__["_value"] = value.upper()

        @dataclass
        class UpperFields:
            value: str = UpperDescriptor()

        class TupleProbe(Component):
            citry = c
            Kwargs = UpperTuple

            template = """
                {{ value }}
            """

        class FieldsProbe(Component):
            citry = c
            Kwargs = UpperFields

            template = """
                {{ value }}
            """

        for probe in (TupleProbe, FieldsProbe):
            instance = probe._create_instance(kwargs={"value": "lower"})
            assert instance.kwargs.value == "LOWER"
            assert probe(value="lower").render().serialize().strip() == "LOWER"

    def test_custom_namedtuple_constructor_cannot_expose_a_marker(self):
        seen = []
        c = Citry()

        class MarkerTuple(namedtuple("TupleBase", "flag")):  # noqa: PYI024
            __slots__ = ()

            def __new__(cls, flag):
                return super().__new__(cls, Const(flag))

        class Probe(Component):
            citry = c
            Kwargs = MarkerTuple

            def template_data(self, kwargs, slots):
                seen.append(kwargs.flag is True)
                return {"flag": kwargs.flag}

            template = """
                {{ flag }}
            """

        assert Probe(flag=True).render().serialize().strip() == "True"
        assert seen == [True]

    def test_read_only_schema_field_cannot_expose_a_marker(self):
        c = Citry()

        @dataclass(init=False)
        class Inputs:
            flag: bool

            def __init__(self, flag):
                self._flag = Const(flag)

            @property
            def flag(self):
                return self._flag

        class Probe(Component):
            citry = c
            Kwargs = Inputs

            template = """
                {{ flag }}
            """

        with pytest.raises(TypeError, match="produced a Const value in a read-only field"):
            Probe(flag=True).render()

    def test_template_data_schema_uses_actual_fields_and_excludes_init_vars(self):
        c = Citry()

        class Probe(Component):
            citry = c

            class TemplateData:
                label: str = field(init=False, default="extra")
                transient: InitVar[str] = "not-a-field"

            def template_data(self, kwargs, slots):
                return {}

            template = """
                {{ label }}
            """

        assert Probe().render().serialize().strip() == "extra"

    def test_typed_default_mapping_snapshots_current_schema_fields(self):
        c = Citry()

        class Probe(Component):
            citry = c

            class Kwargs:
                value: str

            class Cache:
                enabled = True

                def vary(self, kwargs, slots):
                    self.component.kwargs.value = "changed"

            template = """
                {{ value }}
            """

        assert Probe(value=Const("initial")).render().serialize().strip() == "changed"

    def test_namedtuple_marked_default_is_plain_in_callback(self):
        seen = []
        c = Citry()

        class Inputs(NamedTuple):
            flag: bool = Const(True)  # noqa: FBT003

        class Probe(Component):
            citry = c
            Kwargs = Inputs

            def template_data(self, kwargs, slots):
                seen.append(kwargs.flag is True)
                return {"flag": Const(kwargs.flag)}

            template = """
                {{ flag }}
            """

        assert Probe().render().serialize().strip() == "True"
        assert seen == [True]

    def test_input_hooks_pass_plain_values_and_explicit_writes_reestablish_constness(self):
        seen = []

        class First(Extension):
            name = "first"

            def on_component_input(self, ctx):
                seen.append(ctx.kwargs["flag"] is True)
                ctx.kwargs["label"] = Const("fixed")

        class Second(Extension):
            name = "second"

            def on_component_input(self, ctx):
                seen.append(type(ctx.kwargs["label"]) is str)

        app = Citry(extensions=[First, Second])

        class Probe(Component):
            citry = app
            template = """
                {{ label }}
            """.strip()

        assert Probe(flag=Const(True)).render().serialize() == "fixed"  # noqa: FBT003
        assert seen == [True, True]
        assert ["fixed"] in app._const_body_cache.values()

    def test_nested_marker_inserted_by_input_hook_remains_for_next_hook(self):
        seen = []

        class First(Extension):
            name = "first"

            def on_component_input(self, ctx):
                ctx.kwargs["items"].append(Const("added"))

        class Second(Extension):
            name = "second"

            def on_component_input(self, ctx):
                seen.append((ctx.kwargs["items"][-1], is_const(ctx.kwargs["items"][-1])))

        app = Citry(extensions=[First, Second])

        class Probe(Component):
            citry = app
            template = """
                ok
            """.strip()

        Probe(items=[]).render()
        assert seen == [("added", True)]

    def test_root_marker_inserted_through_dict_bypass_is_consumed_before_next_hook(self):
        seen = []

        class First(Extension):
            name = "first"

            def on_component_input(self, ctx):
                dict.__setitem__(ctx.kwargs, "items", Const([Const("added")]))

        class Second(Extension):
            name = "second"

            def on_component_input(self, ctx):
                seen.append((type(ctx.kwargs["items"]) is list, type(ctx.kwargs["items"][0]) is str))

        app = Citry(extensions=[First, Second])

        class Probe(Component):
            citry = app
            template = """
                {{ items[0] }}
            """.strip()

        assert Probe().render().serialize() == "added"
        assert seen == [(True, True)]

    def test_input_hook_const_candidate_survives_a_later_ordinary_write(self):
        candidate = []

        class First(Extension):
            name = "first"

            def on_component_input(self, ctx):
                ctx.kwargs["value"] = Const(candidate)

        class Second(Extension):
            name = "second"

            def on_component_input(self, ctx):
                ctx.kwargs["value"] = []

        app = Citry(extensions=[First, Second])

        class Probe(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"value": candidate}

            template = """
                {{ value }}
            """.strip()

        assert Probe().render().serialize() == "[]"
        (body,) = app._const_body_cache.values()
        assert all(not isinstance(item, ExprNode) for item in body)

    def test_data_hooks_pass_plain_values_and_explicit_write_marks_output(self):
        seen = []

        class First(Extension):
            name = "first"

            def on_component_data(self, ctx):
                ctx.template_data["label"] = Const("fixed")

        class Second(Extension):
            name = "second"

            def on_component_data(self, ctx):
                seen.append(type(ctx.template_data["label"]) is str)

        app = Citry(extensions=[First, Second])

        class Probe(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {}

            template = """
                {{ label }}
            """.strip()

        assert Probe().render().serialize() == "fixed"
        assert seen == [True]
        assert ["fixed"] in app._const_body_cache.values()

    def test_marked_data_and_global_roots_are_plain_before_data_hooks(self):
        seen = []

        class Observe(Extension):
            name = "observe"

            def on_component_data(self, ctx):
                seen.append(
                    tuple(
                        (type(values[name]) is list, type(values[name][0]) is str)
                        for values, name in (
                            (ctx.template_data, "template"),
                            (ctx.template_data, "global_items"),
                            (ctx.js_data, "js"),
                            (ctx.css_data, "css"),
                        )
                    )
                )

        app = Citry(
            extensions=[Observe],
            template_globals={"global_items": Const([Const("global")])},
        )

        class Probe(Component):
            citry = app

            class TemplateData:
                template: list

            def template_data(self, kwargs, slots):
                return {"template": Const([Const("template")])}

            def js_data(self, kwargs, slots):
                return {"js": Const([Const("js")])}

            def css_data(self, kwargs, slots):
                return {"css": Const([Const("css")])}

            template = """
                {{ template[0] }}:{{ global_items[0] }}
            """.strip()

        assert Probe().render().serialize() == "template:global"
        assert seen == [((True, True), (True, True), (True, True), (True, True))]

    def test_ordinary_data_hook_write_clears_const_metadata(self):
        values = iter(("first", "second"))

        class Replace(Extension):
            name = "replace"

            def on_component_data(self, ctx):
                ctx.template_data["label"] = next(values)

        app = Citry(extensions=[Replace])

        class Probe(Component):
            citry = app
            template = """
                {{ label }}
            """.strip()

        assert Probe(label=Const("original")).render().serialize() == "first"
        assert Probe(label=Const("original")).render().serialize() == "second"

    def test_data_hook_returning_original_same_name_input_restores_constness(self):
        original = "original value that is kept by identity"

        class Restore(Extension):
            name = "restore"

            def on_component_data(self, ctx):
                ctx.template_data["label"] = ctx.component.raw_kwargs["label"]

        app = Citry(extensions=[Restore])

        class Probe(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {}

            template = """
                {{ label }}
            """.strip()

        assert Probe(label=Const(original)).render().serialize() == original
        assert [original] in app._const_body_cache.values()

    def test_custom_schema_transformation_discards_input_metadata(self):
        seen = []
        c = Citry()

        class Probe(Component):
            citry = c

            class Kwargs:
                label: str

                def __post_init__(self):
                    seen.append(type(self.label) is str)
                    self.label = self.label.upper()

            template = """
                {{ label }}
            """.strip()

        assert Probe(label=Const("value")).render().serialize() == "VALUE"
        assert seen == [True]
        (body,) = c._const_body_cache.values()
        assert any(isinstance(item, ExprNode) for item in body)

    def test_original_input_returned_after_schema_transformation_restores_constness(self):
        c = Citry()

        class Probe(Component):
            citry = c

            class Kwargs:
                label: str

                def __post_init__(self):
                    self.label = self.label.upper()

            def template_data(self, kwargs, slots):
                return {"label": self.raw_kwargs["label"]}

            template = """
                {{ label }}
            """.strip()

        assert Probe(label=Const("original value")).render().serialize() == "original value"
        assert ["original value"] in c._const_body_cache.values()

    def test_const_global_overridden_by_dynamic_data_stays_dynamic(self):
        calls = []
        app = Citry(template_globals={"value": Const(lambda: "global")})

        class Probe(Component):
            citry = app

            def template_data(self, kwargs, slots):
                def value():
                    calls.append(None)
                    return len(calls)

                return {"value": value}

            template = """
                {{ value() }}
            """.strip()

        assert Probe().render().serialize() == "1"
        assert Probe().render().serialize() == "2"

    def test_default_mapping_preserves_constness_through_child_chain(self):
        app = Citry()

        class Leaf(Component):
            citry = app
            template = """
                {{ value }}
            """.strip()

        class Middle(Component):
            citry = app
            template = """
                <c-Leaf c-value="value" />
            """.strip()

        class Page(Component):
            citry = app
            template = """
                <c-Middle c-value="value" />
            """.strip()

        assert Page(value=Const("fixed")).render().serialize() == "fixed"
        assert ["fixed"] in app._const_body_cache.values()

    def test_dynamic_selector_preserves_known_literal_input_metadata(self):
        app = Citry()

        class Target(Component):
            citry = app
            template = """
                {{ value }}
            """.strip()

        class Page(Component):
            citry = app
            template = """
                <c-component is="Target" value="fixed" />
            """.strip()

        assert Page().render().serialize() == "fixed"
        assert ["fixed"] in app._const_body_cache.values()

    def test_simple_callback_receives_recursively_plain_marked_root_and_restores_same_input(self):
        seen = []
        c = Citry()

        class Probe(Component):
            citry = c
            simple = True

            @staticmethod
            def template_data(kwargs, _slots):
                seen.append((type(kwargs["items"]) is list, type(kwargs["items"][0]) is str))
                return {"items": kwargs["items"]}

            template = """
                {{ items[0] }}
            """.strip()

        assert Probe(items=Const([Const("leaf")])).render().serialize() == "leaf"
        assert seen == [(True, True)]

    def test_simple_default_mapping_exposes_plain_values(self):
        c = Citry()

        class Probe(Component):
            citry = c
            simple = True
            template = """
                {{ flag is True }}
            """.strip()

        assert Probe(flag=Const(True)).render().serialize() == "True"  # noqa: FBT003

    def test_repr_is_transparent(self):
        # repr forwards to the wrapped value: the engine marks template
        # literals without the user opting in, so a marked value inside a
        # container must repr exactly like the plain value.
        assert repr(Const(3)) == "3"
        assert repr(Const("hi")) == "'hi'"
        assert repr({"text": Const("hi")}) == "{'text': 'hi'}"


class TestFreezeConst:
    def test_equal_values_freeze_equal(self):
        assert freeze_const([1, 2]) == freeze_const([1, 2])
        assert freeze_const({"a": 1, "b": 2}) == freeze_const({"b": 2, "a": 1})
        assert freeze_const({1, 2}) == freeze_const({2, 1})
        assert freeze_const("hi") == freeze_const("hi")

    def test_distinct_values_freeze_distinct(self):
        assert freeze_const([1, 2]) != freeze_const([1, 3])
        assert freeze_const([1, 2]) != freeze_const((1, 2))
        assert freeze_const({"a": 1}) != freeze_const({"a": 2})

    def test_type_distinguishes_equal_values(self):
        # True == 1 and 1 == 1.0, but they render differently, so they must
        # not share a cache key.
        assert freeze_const(True) != freeze_const(1)  # noqa: FBT003
        assert freeze_const(1) != freeze_const(1.0)

    def test_nested_const_is_unwrapped(self):
        assert freeze_const(Const([Const(1), 2])) == freeze_const([1, 2])

    def test_frozen_form_is_hashable(self):
        hash(freeze_const([1, {"a": {2, 3}}, ("b",)]))

    def test_freeze_is_memoized_on_the_marker(self):
        # Const is a promise the value does not change, so the frozen key is
        # computed once per marker and reused; mutating the wrapped value
        # afterwards breaks the promise and does NOT change the key.
        marked = Const([1, 2])
        first = freeze_const(marked)
        assert freeze_const(marked) is first
        marked.append(3)
        assert freeze_const(marked) is first

    def test_unhashable_non_container_is_unfreezable(self):
        assert freeze_const(_Unhashable(1)) is _UNFREEZABLE
        # An unfreezable leaf poisons its containers.
        assert freeze_const([_Unhashable(1)]) is _UNFREEZABLE
        assert freeze_const({"k": _Unhashable(1)}) is _UNFREEZABLE


class TestExtractConstVars:
    def test_splits_const_from_dynamic(self):
        const_vars, signature = extract_const_vars({"a": Const(1), "b": 2})
        assert list(const_vars) == ["a"]
        assert const_vars["a"] == 1
        assert signature == frozenset({("a", freeze_const(1))})

    def test_unfreezable_const_is_demoted_everywhere(self):
        # The variable must drop out of BOTH the const set and the signature,
        # so precomputing and the cache key always agree.
        const_vars, signature = extract_const_vars({"a": Const(_Unhashable(1))})
        assert const_vars == {}
        assert signature == frozenset()


class TestConstFlow:
    def test_const_input_renders(self):
        # A Const input passed through template_data must not break rendering.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>hi</p>"

        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_const_signature_keys_the_cache(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

        # Different const values -> different signatures -> two cache entries.
        Card(cols=Const(3)).render()
        Card(cols=Const(5)).render()
        assert len(c._const_body_cache) == 2

        # Same signature again -> cache hit, no new entry.
        Card(cols=Const(3)).render()
        assert len(c._const_body_cache) == 2

    def test_unused_const_var_does_not_split_the_cache(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>hi</p>"  # uses no variables

        # The template never reads `cols`, so its const values cannot affect
        # the body: both renders share one cache entry (the empty signature).
        Card(cols=Const(3)).render()
        Card(cols=Const(5)).render()
        assert len(c._const_body_cache) == 1

    def test_non_const_var_not_in_signature(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>hi</p>"

        # Plain (non-Const) values do not enter the signature, so both renders
        # share the empty signature and a single cache entry.
        Card(cols=3).render()
        Card(cols=5).render()
        assert len(c._const_body_cache) == 1

    def test_container_const_value_keys_by_value(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ rows }}</p>"

        # Equal lists (distinct objects) share one canonical key.
        Card(rows=Const([1, 2, 3])).render()
        Card(rows=Const([1, 2, 3])).render()
        assert len(c._const_body_cache) == 1
        Card(rows=Const([1, 2, 4])).render()
        assert len(c._const_body_cache) == 2

    def test_unfreezable_const_value_renders_as_dynamic(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ obj.x }}</p>"

        # The value cannot be keyed, so it is demoted to dynamic: both renders
        # share the empty signature, and the expression re-evaluates each time.
        assert Card(obj=Const(_Unhashable(1))).render().serialize() == '<p data-cid-c1="">1</p>'
        assert Card(obj=Const(_Unhashable(2))).render().serialize() == '<p data-cid-c2="">2</p>'
        assert len(c._const_body_cache) == 1

    def test_bool_and_int_const_do_not_share_a_body(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ v }}</p>"

        assert Card(v=Const(True)).render().serialize() == '<p data-cid-c1="">True</p>'  # noqa: FBT003
        assert Card(v=Const(1)).render().serialize() == '<p data-cid-c2="">1</p>'
        assert len(c._const_body_cache) == 2

    def test_clear_empties_the_cache(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>hi</p>"

        Card().render()
        assert len(c._const_body_cache) >= 1
        c.clear()
        assert len(c._const_body_cache) == 0


class TestConstPrecompute:
    def test_const_expr_precomputes_to_static_text(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c1="">3</p>'
        (body,) = c._const_body_cache.values()
        assert body == ["<p>3</p>"]

    def test_dynamic_expr_stays_dynamic_in_shared_body(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ cols }} and {{ other }}</p>"

        # Two renders share the const signature but differ in the dynamic input.
        assert Card(cols=Const(3), other="x").render().serialize() == '<p data-cid-c1="">3 and x</p>'
        assert Card(cols=Const(3), other="y").render().serialize() == '<p data-cid-c2="">3 and y</p>'
        assert len(c._const_body_cache) == 1

        (body,) = c._const_body_cache.values()
        first, node, last = body
        assert first == "<p>3 and "
        assert isinstance(node, ExprNode)
        assert last == "</p>"

    def test_precomputed_value_is_escaped(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ v }}</p>"

        assert Card(v=Const("<b>")).render().serialize() == '<p data-cid-c1="">&lt;b&gt;</p>'

    def test_const_none_precomputes_to_empty(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ v }}</p>"

        assert Card(v=Const(None)).render().serialize() == '<p data-cid-c1=""></p>'
        assert Card(v=None).render().serialize() == '<p data-cid-c2=""></p>'

    def test_const_if_branch_is_pruned(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="cols > 2">big</c-if><c-else>small</c-else>'

        assert Card(cols=Const(3)).render().serialize() == "big"
        assert Card(cols=Const(1)).render().serialize() == "small"
        big_body, small_body = c._const_body_cache.values()
        assert big_body == ["big"]
        assert small_body == ["small"]

    def test_const_if_with_no_match_precomputes_to_nothing(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="cols > 2">big</c-if>'

        assert Card(cols=Const(1)).render().serialize() == ""
        (body,) = c._const_body_cache.values()
        assert body == []

    def test_dynamic_if_keeps_the_node(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="cols > 2">big</c-if><c-else>small</c-else>'

        assert Card(cols=3).render().serialize() == "big"
        assert Card(cols=1).render().serialize() == "small"
        (body,) = c._const_body_cache.values()
        (node,) = body
        assert isinstance(node, IfNode)

    def test_pruned_branch_is_precomputed_recursively(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="show">{{ label }}: {{ count }}</c-if>'

        out = Card(show=Const(True), label=Const("n"), count=7).render().serialize()  # noqa: FBT003
        assert out == "n: 7"
        (body,) = c._const_body_cache.values()
        first, node = body
        assert first == "n: "
        assert isinstance(node, ExprNode)

    def test_zero_variable_expr_precomputes_without_const_inputs(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ 1 + 1 }}</p>"

        assert Card().render().serialize() == '<p data-cid-c1="">2</p>'
        (body,) = c._const_body_cache.values()
        assert body == ["<p>2</p>"]

    def test_slot_node_never_precomputes(self):
        c = Citry()

        class Box(Component):
            citry = c
            template = '<div><c-slot name="s">fb</c-slot></div>'

        class Page(Component):
            citry = c
            template = '<c-Box><c-fill name="s">{{ msg }}</c-fill></c-Box>'

        # Same const signature, different fills: the cached Box body must keep
        # the SlotNode so each render picks up its own fill.
        assert "one" in Page(msg="one", k=Const(1)).render().serialize()
        assert "two" in Page(msg="two", k=Const(1)).render().serialize()

        box_bodies = [
            body
            for body in c._const_body_cache.values()
            if any(isinstance(item, SlotNode) for item in body if not isinstance(item, str))
        ]
        assert len(box_bodies) == 1

    def test_const_element_value_is_not_precomputed(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<span>inner</span>"

        class Holder(Component):
            citry = c
            template = "<div>{{ content }}</div>"

        # Rendering an element mints per-render state (a fresh component id),
        # so the expression must stay dynamic even though its input is const.
        element = Inner()
        first = Holder(content=Const(element)).render().serialize()
        second = Holder(content=Const(element)).render().serialize()
        assert "inner" in first
        assert "inner" in second

        # Two entries: Inner's own body, and Holder's body for the const
        # signature. Holder's must have kept the expression dynamic.
        holder_bodies = [
            body for body in c._const_body_cache.values() if any(isinstance(item, ExprNode) for item in body)
        ]
        assert len(holder_bodies) == 1


class TestTemplateLiteralConst:
    """
    A literal attribute in a template is implicitly const: it is written in
    the template, so it cannot change between renders of that template.
    """

    def test_static_attr_is_const_in_the_child(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ age }}</p>"

        class Page(Component):
            citry = c
            template = '<c-Card age="30" />'

        assert Page().render().serialize() == '<p data-cid-c2="" data-cid-c1="">30</p>'
        card_bodies = [b for b in c._const_body_cache.values() if b == ["<p>30</p>"]]
        assert len(card_bodies) == 1

    def test_unquoted_static_attr_is_const(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ age }}</p>"

        class Page(Component):
            citry = c
            template = "<c-Card age=30 />"

        Page().render()
        assert ["<p>30</p>"] in c._const_body_cache.values()

    def test_boolean_attr_is_const_true(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ compact }}</p>"

        class Page(Component):
            citry = c
            template = '<c-Card compact="" />'

        Page().render()
        assert ["<p>True</p>"] in c._const_body_cache.values()

    def test_zero_variable_expression_attr_is_typed_const(self):
        # c-age="30" evaluates to the int 30 (not the string "30") and is a
        # template literal, so it is marked const and the child precomputes on it.
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="age > 18">adult</c-if><c-else>minor</c-else>'

        class Page(Component):
            citry = c
            template = '<c-Card c-age="30" />'

        assert Page().render().serialize() == "adult"
        assert ["adult"] in c._const_body_cache.values()

    def test_template_expression_wraps_only_its_result_after_plain_arguments_are_evaluated(self):
        seen = []

        def add(left, right):
            seen.append((type(left) is int, type(right) is int))
            return left + right

        c = Citry(template_globals={"add": Const(add)})

        class Card(Component):
            citry = c

            def template_data(self, kwargs, slots):
                seen.append(
                    (
                        type(kwargs["items"]) is list,
                        all(type(item) is int for item in kwargs["items"]),
                        type(kwargs["total"]) is int,
                    )
                )
                return kwargs

            template = """
                {{ items }}:{{ total }}
            """.strip()

        class Page(Component):
            citry = c
            template = """
                <c-Card c-items="[1, 2]" c-total="add(1, 2)" />
            """.strip()

        assert Page().render().serialize() == "[1, 2]:3"
        assert seen == [(True, True), (True, True, True)]

    def test_zero_variable_container_literal_unrolls_child_loop(self):
        c = Citry()

        class Items(Component):
            citry = c
            template = '<c-for each="i in items">[{{ i * mult }}]</c-for>'

        class Page(Component):
            citry = c
            template = '<c-Items c-items="[1, 2, 3]" c-mult="10" />'

        assert Page().render().serialize() == "[10][20][30]"
        assert any(
            len(body) == 1 and isinstance(body[0], ForNode) and body[0]._precomputed_text == "[10][20][30]"
            for body in c._const_body_cache.values()
        )

        # Repeated renders hit the same signature: the per-render marker wraps
        # a fresh equal list, and the canonical key makes it the same entry.
        Page().render()
        Page().render()
        assert len(c._const_body_cache) == 2  # Page's body + Items' precomputed body

    def test_dynamic_expression_attr_is_not_marked(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ age }}</p>"

        class Page(Component):
            citry = c
            template = '<c-Card c-age="n" />'

            def template_data(self, kwargs, slots):
                return {"n": kwargs["n"]}

        assert Page(n=1).render().serialize() == '<p data-cid-c2="" data-cid-c1="">1</p>'
        assert Page(n=2).render().serialize() == '<p data-cid-c4="" data-cid-c3="">2</p>'
        # The child renders dynamic: one shared (empty-signature) entry whose
        # body keeps the expression node.
        card_bodies = [b for b in c._const_body_cache.values() if any(isinstance(item, ExprNode) for item in b)]
        assert len(card_bodies) == 1


class TestExpressionConstPropagation:
    """
    An expression attribute whose variables are all const at render time
    produces a const result (``c-age="base + 1"`` when ``base`` is const), so
    the child reuses its pre-computed work for that input as well. A single
    non-const variable in the expression breaks it, exactly like a dynamic
    attribute.
    """

    def test_all_const_expression_attr_is_const_in_the_child(self):
        # base is const, so base + 1 (= 30) is const, so the child's c-if
        # precomputes on `age`. If propagation failed, `age` would be plain and the
        # IfNode would stay live.
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="age > 18">adult</c-if><c-else>minor</c-else>'

        class Page(Component):
            citry = c
            template = '<c-Card c-age="base + 1" />'

            def template_data(self, kwargs, slots):
                return {"base": Const(29)}

        assert Page().render().serialize() == "adult"
        assert ["adult"] in c._const_body_cache.values()

    def test_expression_mixing_const_and_dynamic_is_not_marked(self):
        # base is const but n is not, so base + n is not const: the child must
        # stay dynamic (one shared empty-signature entry keeping the IfNode).
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="age > 18">adult</c-if><c-else>minor</c-else>'

        class Page(Component):
            citry = c
            template = '<c-Card c-age="base + n" />'

            def template_data(self, kwargs, slots):
                return {"base": Const(29), "n": kwargs["n"]}

        assert Page(n=1).render().serialize() == "adult"
        assert Page(n=-100).render().serialize() == "minor"
        assert ["adult"] not in c._const_body_cache.values()
        live = [b for b in c._const_body_cache.values() if any(isinstance(item, IfNode) for item in b)]
        assert len(live) == 1

    def test_propagated_const_dedups_across_a_loop(self):
        # The win: a loop hands every child an all-const computed label, so all
        # the children share ONE precomputed cache entry (the loop var `i` is not in
        # the kwarg, so the kwarg is const every iteration and equal-valued).
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>{{ label }}</span>"

        class Page(Component):
            citry = c
            template = '<c-for each="i in items"><c-Card c-label="prefix + \'!\'" /></c-for>'

            def template_data(self, kwargs, slots):
                return {"items": Const([1, 2, 3]), "prefix": Const("hi")}

        out = Page().render().serialize()
        assert out.count("<span") == 3
        assert "hi!" in out
        card_bodies = [b for b in c._const_body_cache.values() if b == ["<span>hi!</span>"]]
        assert len(card_bodies) == 1


class TestConstThroughTypedKwargs:
    def test_default_typed_kwargs_mapping_preserves_const_metadata(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

            class Kwargs:
                cols: int

        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c1="">3</p>'
        (body,) = c._const_body_cache.values()
        assert body == ["<p>3</p>"]

    def test_const_default_on_typed_kwargs_field(self):
        # A `Const(...)` default is the explicit way to mark a default value
        # constant: when the kwarg is omitted, the marked default flows
        # through template_data and precomputes; when it is passed, the live value
        # renders as usual (dynamic unless the caller marked it).
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

            class Kwargs:
                cols: int = Const(3)

        assert Card().render().serialize() == '<p data-cid-c1="">3</p>'
        assert Card(cols=5).render().serialize() == '<p data-cid-c2="">5</p>'

        precomputed = [body for body in c._const_body_cache.values() if body == ["<p>3</p>"]]
        dynamic = [body for body in c._const_body_cache.values() if any(isinstance(i, ExprNode) for i in body)]
        assert len(precomputed) == 1
        assert len(dynamic) == 1


class TestConstPrecomputeInsideKeptNodes:
    def test_component_clone_preserves_the_original_metadata_tuple(self):
        key = ExprHtmlAttr("", (0, 0), "#c-key", "item", ("item",))
        metadata = ("range", ("key", key), ("morph", "ignore"))
        node = ComponentNode(
            "",
            (0, 0),
            (),
            [ExprNode("", (0, 0), "label", ("label",))],
            ("label", "item"),
            "card",
            False,  # noqa: FBT003
            metadata,
        )

        (precomputed,) = precompute_const_parts([node], {"label": Const("fixed")})

        assert precomputed is not node
        assert precomputed.body == ["fixed"]
        assert precomputed.metadata is metadata

    def test_precomputes_inside_dynamic_if_branches(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="show">{{ label }}: {{ n }}</c-if><c-else>{{ label }} off</c-else>'

        # `show` and `n` are dynamic, `label` is const: the IfNode stays, but
        # the const expression inside each branch precomputes to text.
        assert Card(show=True, label=Const("x"), n=7).render().serialize() == "x: 7"
        assert Card(show=False, label=Const("x"), n=7).render().serialize() == "x off"
        assert len(c._const_body_cache) == 1

        (body,) = c._const_body_cache.values()
        (node,) = body
        assert isinstance(node, IfNode)
        if_body = node.branches[0][2]
        assert if_body[0] == "x: "
        assert isinstance(if_body[1], ExprNode)
        else_body = node.branches[1][2]
        assert else_body == ["x off"]

    def test_const_if_nested_in_dynamic_branch_is_pruned(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-if cond="show"><c-if cond="big">L</c-if><c-else>S</c-else>{{ n }}</c-if>'

        # The outer condition is dynamic; the inner one is const, so inside
        # the rebuilt outer branch the inner if is decided and inlined.
        assert Card(show=True, big=Const(True), n=1).render().serialize() == "L1"  # noqa: FBT003
        (body,) = c._const_body_cache.values()
        (node,) = body
        branch_body = node.branches[0][2]
        assert branch_body[0] == "L"
        assert isinstance(branch_body[1], ExprNode)

    def test_precomputes_inside_kept_for_body(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-for each="i in items">[{{ prefix }}{{ i }}]</c-for>'

        # `items` is dynamic, so the loop stays; the const `prefix` inside the
        # body precomputes (it is the same on every iteration), while the loop
        # variable expression stays dynamic.
        assert Card(items=[1, 2], prefix=Const("p")).render().serialize() == "[p1][p2]"
        (body,) = c._const_body_cache.values()
        (node,) = body
        loop_body = node.branches[0][2]
        assert loop_body[0] == "[p"
        assert isinstance(loop_body[1], ExprNode)
        assert loop_body[1].used_vars == ("i",)
        assert loop_body[2] == "]"

    def test_kept_for_masks_target_but_empty_branch_keeps_outer_scope(self):
        each_attr = ExprHtmlAttr(None, (0, 0), "each", "i in items", ("items",))
        loop_expr = ExprNode(None, (0, 0), "i", ("i",))
        empty_expr = ExprNode(None, (0, 0), "i", ("i",))
        node = ForNode(
            None,
            (
                ((0, 0), (each_attr,), [loop_expr], ("i",)),
                ((0, 0), (), [empty_expr], ()),
            ),
            ("items",),
        )

        (precomputed,) = precompute_const_parts([node], {"i": Const("outer")})

        assert isinstance(precomputed.branches[0][2][0], ExprNode)
        assert precomputed.branches[1][2] == ["outer"]

    def test_nested_loop_cannot_unroll_over_enclosing_loop_binding(self):
        inner_each = ExprHtmlAttr(None, (0, 0), "each", "i in inner_items", ("inner_items",))
        inner = ForNode(
            None,
            (((0, 0), (inner_each,), [ExprNode(None, (0, 0), "i", ("i",))], ("i",)),),
            ("inner_items",),
        )
        outer_each = ExprHtmlAttr(None, (0, 0), "each", "i in outer_items", ("outer_items",))
        outer = ForNode(
            None,
            (((0, 0), (outer_each,), [inner], ("i",)),),
            ("outer_items", "inner_items"),
        )

        (precomputed,) = precompute_const_parts(
            [outer],
            {"inner_items": Const([1])},
            visible_names={"outer_items", "inner_items"},
        )

        nested = precomputed.branches[0][2][0]
        assert isinstance(nested, ForNode)
        assert isinstance(nested.branches[0][2][0], ExprNode)


class TestConstPrecomputeInsideSlotContent:
    """
    Precomputing descends into slot content: fill bodies, the implicit default
    slot body, and slot fallback bodies all render against the variables of
    the component whose template wrote them, so const expressions inside
    them precompute like any other.
    """

    def test_const_expr_in_fill_body_precomputes(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="title" /><c-slot name="body" /></div>'

        class Page(Component):
            citry = c
            template = (
                "<c-Card>"
                '<c-fill name="title">{{ heading }}!</c-fill>'
                '<c-fill name="body"><p>{{ greeting }}</p></c-fill>'
                "</c-Card>"
            )

        out1 = Page(heading=Const("Dash"), greeting="hi").render().serialize()
        out2 = Page(heading=Const("Dash"), greeting="yo").render().serialize()
        assert "<p>hi</p>" in out1
        assert "<p>yo</p>" in out2
        assert "Dash!" in out1

        # In Page's cached body, the title fill precomputed to text while the
        # body fill kept its dynamic expression.
        (page_body,) = [b for b in c._const_body_cache.values() if not isinstance(b[0], str)]
        (component_node,) = page_body
        title_fill, body_fill = component_node.body
        assert title_fill.body == ["Dash!"]
        assert body_fill.body[0] == "<p>"
        assert isinstance(body_fill.body[1], ExprNode)

    def test_const_if_inside_fill_body_prunes(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="body" />'

        class Page(Component):
            citry = c
            template = '<c-Card><c-fill name="body">x<c-if cond="wide">WIDE</c-if></c-fill></c-Card>'

        assert Page(wide=Const(True)).render().serialize() == "xWIDE"  # noqa: FBT003
        (page_body,) = [b for b in c._const_body_cache.values() if isinstance(b[0], ComponentNode)]
        (fill,) = page_body[0].body
        assert fill.body == ["xWIDE"]

    def test_fill_data_var_stays_dynamic(self):
        c = Citry()

        class Box(Component):
            citry = c
            template = '<c-slot name="s" c-x="1" />'

        class Page(Component):
            citry = c
            template = '<c-Box><c-fill name="s" data="d">{{ d.x }}-{{ k }}</c-fill></c-Box>'

        # The fill's own `d` variable is per-invocation slot data, so the
        # expression using it stays live; the const `k` precomputes and merges.
        assert Page(k=Const("K")).render().serialize() == "1-K"
        (page_body,) = [b for b in c._const_body_cache.values() if isinstance(b[0], ComponentNode)]
        (fill,) = page_body[0].body
        assert isinstance(fill.body[0], ExprNode)
        assert fill.body[0].used_vars == ("d",)
        assert fill.body[1] == "-K"

    def test_dynamic_fill_binding_allows_only_variable_free_precomputation(self):
        attrs = (
            StaticHtmlAttr(None, (0, 0), "name", "s", ()),
            ExprHtmlAttr(None, (0, 0), "c-bind", "props", ("props",)),
        )
        fill = FillNode(
            None,
            (0, 0),
            attrs,
            [
                ExprNode(None, (0, 0), "d", ("d",)),
                ":",
                ExprNode(None, (0, 0), "k", ("k",)),
                ":",
                ExprNode(None, (0, 0), "1 + 1", ()),
            ],
            ("props",),
            (),
        )

        (precomputed,) = precompute_const_parts(
            [fill],
            {"d": Const("outer d"), "k": Const("outer k"), "props": Const(None)},
        )

        assert isinstance(precomputed.body[0], ExprNode)
        assert isinstance(precomputed.body[2], ExprNode)
        assert precomputed.body[3] == ":2"

    def test_static_fill_binding_masks_same_named_outer_const(self):
        fill = FillNode(
            None,
            (0, 0),
            (
                StaticHtmlAttr(None, (0, 0), "name", "s", ()),
                StaticHtmlAttr(None, (0, 0), "data", "d", ()),
            ),
            [ExprNode(None, (0, 0), "d", ("d",))],
            (),
            ("d",),
        )

        (precomputed,) = precompute_const_parts([fill], {"d": Const("outer")})

        assert isinstance(precomputed.body[0], ExprNode)

    def test_default_slot_body_precomputes(self):
        c = Citry()

        class Box(Component):
            citry = c
            template = '<b><c-slot name="default" /></b>'

        class Page(Component):
            citry = c
            template = "<c-Box>{{ k }}</c-Box>"

        assert Page(k=Const("K")).render().serialize() == '<b data-cid-c2="" data-cid-c1="">K</b>'
        (page_body,) = [b for b in c._const_body_cache.values() if not isinstance(b[0], str)]
        assert page_body[0].body == ["K"]

    def test_slot_fallback_body_precomputes(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="title">{{ label }}</c-slot>'

        # Unfilled: the fallback renders, and with `label` const its
        # expression precomputed inside the kept SlotNode.
        assert Card(label=Const("untitled")).render().serialize() == "untitled"
        (body,) = c._const_body_cache.values()
        (slot_node,) = body
        assert isinstance(slot_node, SlotNode)
        assert slot_node.body == ["untitled"]

        # Filled: the fill wins over the precomputed fallback, same as ever.
        assert Card(label=Const("untitled"), slots={"title": "Hello"}).render().serialize() == "Hello"


class TestConstPrecomputeUnroll:
    def test_const_loop_unrolls_to_text(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<ul><c-for each="i in items">{{ i }},</c-for></ul>'

        assert Card(items=Const([1, 2, 3])).render().serialize() == '<ul data-cid-c1="">1,2,3,</ul>'
        (body,) = c._const_body_cache.values()
        assert len(body) == 3
        assert body[0] == "<ul>"
        assert isinstance(body[1], ForNode)
        assert body[1]._precomputed_text == "1,2,3,"
        assert body[2] == "</ul>"

    def test_unrolled_loop_cache_does_not_hide_later_context_collision(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-for each="i in items">{{ i }}</c-for>'

        assert Card(items=Const([1])).render().serialize() == "1"
        with pytest.raises(RuntimeError, match=r"Cannot define variable 'i'.*Variable shadowing is not allowed"):
            Card(items=Const([1]), i="outer").render().serialize()

        assert len(c._const_body_cache) == 2

    def test_unrolled_loop_checks_context_mutated_earlier_in_same_render(self):
        class MutatingExtension(Extension):
            name = "mutating"

            def on_component_data(self, ctx):
                def mutate():
                    ctx.template_data["i"] = "late"
                    return ""

                ctx.template_data["mutate"] = mutate

        c = Citry(extensions=[MutatingExtension])

        class Card(Component):
            citry = c
            template = '{{ mutate() }}<c-for each="i in items">{{ i }}</c-for>'

        with pytest.raises(RuntimeError, match=r"Cannot define variable 'i'.*Variable shadowing is not allowed"):
            Card(items=Const([1, 2])).render().serialize()

        (body,) = c._const_body_cache.values()
        assert isinstance(body[0], ExprNode)
        assert isinstance(body[1], ForNode)
        assert body[1]._precomputed_text == "12"

    def test_unroll_precomputes_ifs_and_uses_empty_branch(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-for each="i in items"><c-if cond="i > 1">{{ i }}!</c-if></c-for><c-empty>none</c-empty>'

        assert Card(items=Const([1, 2, 3])).render().serialize() == "2!3!"
        assert Card(items=Const([])).render().serialize() == "none"
        bodies = c._const_body_cache.values()
        assert sorted(node._precomputed_text for (node,) in bodies) == ["2!3!", "none"]

    def test_unroll_backs_out_past_the_iteration_cap(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-for each="i in items">.</c-for>'

        n = _MAX_UNROLL_ITERATIONS + 1
        out = Card(items=Const(range(n))).render().serialize()
        assert out == "." * n
        (body,) = c._const_body_cache.values()
        (node,) = body
        assert not isinstance(node, str)  # the loop stayed dynamic

    def test_unroll_backs_out_on_element_value(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<i>x</i>"

        class Card(Component):
            citry = c
            template = '<c-for each="i in items">{{ i }}</c-for>'

        # The loop body is statically precomputable, but the value is an element,
        # which must render fresh per render: the unroll backs out and the
        # loop stays dynamic.
        element = Inner()
        first = Card(items=Const([element])).render().serialize()
        second = Card(items=Const([element])).render().serialize()
        assert "<i" in first
        assert "<i" in second
        card_body = next(b for b in c._const_body_cache.values() if b and not isinstance(b[0], str))
        assert len(card_body) == 1

    def test_dynamic_loop_does_not_unroll(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-for each="i in items">{{ i }}</c-for>'

        assert Card(items=[1, 2]).render().serialize() == "12"
        (body,) = c._const_body_cache.values()
        assert not isinstance(body[0], str)


class TestConstPrecomputeErrors:
    def test_failing_const_expr_stays_dynamic_and_raises_at_render(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<p>{{ cfg["missing"] }}</p>'

        # Precomputing must not raise: the failing expression stays a dynamic node
        # and the error surfaces through the normal render path, every render.
        with pytest.raises(KeyError):
            Card(cfg=Const({"a": 1})).render().serialize()
        (body,) = c._const_body_cache.values()
        assert any(isinstance(item, ExprNode) for item in body)
        with pytest.raises(KeyError):
            Card(cfg=Const({"a": 1})).render().serialize()

    def test_failing_const_cond_keeps_the_if_dynamic(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<c-if cond=\"cfg['missing']\">a</c-if>"

        with pytest.raises(KeyError):
            Card(cfg=Const({"a": 1})).render().serialize()
        (body,) = c._const_body_cache.values()
        (node,) = body
        assert isinstance(node, IfNode)


class TestConstBodyCache:
    def test_builds_once_per_key(self):
        cache = ConstBodyCache()
        calls = []

        def build():
            calls.append(1)
            return ["body"]

        assert cache.get_or_build(int, frozenset(), build) == ["body"]
        assert cache.get_or_build(int, frozenset(), build) == ["body"]
        assert len(calls) == 1

    def test_distinct_keys_build_separately(self):
        cache = ConstBodyCache()
        cache.get_or_build(int, frozenset(), lambda: ["a"])
        assert cache.get_or_build(int, frozenset({("x", 1)}), lambda: ["b"]) == ["b"]
        assert cache.get_or_build(str, frozenset(), lambda: ["c"]) == ["c"]
        assert len(cache) == 3

    def test_distinct_visible_name_sets_build_separately(self):
        cache = ConstBodyCache()
        assert cache.get_or_build(int, frozenset(), lambda: ["a"], visible_names={"items"}) == ["a"]
        assert cache.get_or_build(int, frozenset(), lambda: ["b"], visible_names={"i", "items"}) == ["b"]
        assert len(cache) == 2

    def test_lru_evicts_oldest(self):
        cache = ConstBodyCache(max_entries=2)
        cache.get_or_build(int, frozenset({("x", 1)}), lambda: ["a"])
        cache.get_or_build(int, frozenset({("x", 2)}), lambda: ["b"])
        cache.get_or_build(int, frozenset({("x", 3)}), lambda: ["c"])
        assert len(cache) == 2
        # The oldest entry ("a") was evicted, so it rebuilds.
        rebuilt = []
        cache.get_or_build(int, frozenset({("x", 1)}), lambda: rebuilt.append(1) or ["a"])
        assert rebuilt == [1]

    def test_hit_refreshes_recency(self):
        cache = ConstBodyCache(max_entries=2)
        cache.get_or_build(int, frozenset({("x", 1)}), lambda: ["a"])
        cache.get_or_build(int, frozenset({("x", 2)}), lambda: ["b"])
        # Touch "a" so "b" is now the least recently used.
        cache.get_or_build(int, frozenset({("x", 1)}), lambda: ["a2"])
        cache.get_or_build(int, frozenset({("x", 3)}), lambda: ["c"])
        # "a" survived the eviction; "b" did not.
        survived = []
        cache.get_or_build(int, frozenset({("x", 1)}), lambda: survived.append(1) or ["a3"])
        assert survived == []

    def test_failed_build_caches_nothing(self):
        cache = ConstBodyCache()

        def boom():
            msg = "build failed"
            raise RuntimeError(msg)

        with pytest.raises(RuntimeError, match="build failed"):
            cache.get_or_build(int, frozenset(), boom)
        assert len(cache) == 0
        # The next attempt retries and can succeed.
        assert cache.get_or_build(int, frozenset(), lambda: ["ok"]) == ["ok"]

    def test_evict_component(self):
        cache = ConstBodyCache()
        cache.get_or_build(int, frozenset(), lambda: ["a"])
        cache.get_or_build(int, frozenset({("x", 1)}), lambda: ["b"])
        cache.get_or_build(str, frozenset(), lambda: ["c"])
        cache.evict_component(int)
        assert len(cache) == 1

    def test_collected_component_removes_all_weakly_owned_entries(self):
        cache = ConstBodyCache()

        class Temporary:
            pass

        cache.get_or_build(Temporary, frozenset(), lambda: ["a"])
        cache.get_or_build(Temporary, frozenset({("x", 1)}), lambda: ["b"])
        temporary_ref = ref(Temporary)

        del Temporary
        gc.collect()

        assert temporary_ref() is None
        assert len(cache) == 0

    def test_collected_component_is_pruned_only_during_an_ordinary_cache_operation(self):
        cache = ConstBodyCache()

        class Temporary:
            pass

        cache.get_or_build(Temporary, frozenset(), lambda: ["a"])
        temporary_ref = ref(Temporary)

        # Collection can occur while this thread already holds the cache lock.
        # The callback only sets a flag; it does not mutate entries or release
        # a cached body from the interrupted GC call.
        with cache._lock:
            del Temporary
            gc.collect()
            assert temporary_ref() is None
            assert len(cache._entries) == 1

        # The next ordinary cache operation prunes the dead weak entry.
        assert len(cache) == 0

    def test_component_collection_does_not_release_cached_bodies_from_gc(self):
        # A weakref callback that popped the entry here would release Bomb
        # while the interrupted thread holds ``blocker`` and deadlock in its
        # destructor. Keep the reproducer in a child so regressions time out
        # instead of wedging pytest.
        script = textwrap.dedent(
            """
            import gc
            import threading

            from citry.constness import ConstBodyCache

            blocker = threading.Lock()

            class Bomb:
                def __del__(self):
                    blocker.acquire()

            class Temporary:
                pass

            cache = ConstBodyCache()
            cache.get_or_build(Temporary, frozenset(), lambda: [Bomb()])
            blocker.acquire()
            del Temporary
            gc.collect()
            blocker.release()
            cache.clear()
            print("CLASS-GC-DID-NOT-RELEASE-CACHED-BODY")
            """
        )
        try:
            completed = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            pytest.fail("component collection released a cached body from GC and deadlocked")

        assert completed.returncode == 0, completed.stderr
        assert "CLASS-GC-DID-NOT-RELEASE-CACHED-BODY" in completed.stdout

    def test_clear(self):
        cache = ConstBodyCache()
        cache.get_or_build(int, frozenset(), lambda: ["a"])
        cache.clear()
        assert len(cache) == 0
