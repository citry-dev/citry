"""
Tests for the Const optimization (citry/constness.py): the Const marker, the
cache key built from marked values, the precomputing step that pre-computes the
constant parts of a template, and the cache that stores the results.
"""

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
from citry._vue.capture import PreparedConstantNode, PreparedExprNode, PreparedTextValue
from citry._vue.leaf_program import LeafProgramNode
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
from citry.nodes import ComponentNode, ExprHtmlAttr, ExprNode, FillNode, ForNode, IfNode, StaticHtmlAttr


def _track_prepared_expression(monkeypatch, expression):
    original = PreparedExprNode.evaluate
    calls = []

    def evaluate(self, variables, *, sandboxed=True):
        if self.expr.strip() == expression:
            calls.append(tuple(const_value(variables[name]) for name in self.used_vars))
        return original(self, variables, sandboxed=sandboxed)

    monkeypatch.setattr(PreparedExprNode, "evaluate", evaluate)
    return calls


def _cache_has_prepared_text(cache, expected):
    """Return whether the prepared cache contains one constant text value."""
    return any(
        any(
            isinstance(item, PreparedConstantNode)
            and isinstance(item.value, PreparedTextValue)
            and item.value.value == expected
            for item in body
        )
        for body in cache.values()
    )


def _cache_has_leaf_program(cache):
    """Return whether the prepared cache retains a live leaf program."""
    return any(any(isinstance(item, LeafProgramNode) for item in body) for body in cache.values())


def _track_if_selection(monkeypatch, condition):
    original = IfNode.active_branch_body
    calls = []

    def active_branch_body(self, context):
        matches = any(
            isinstance(attr, ExprHtmlAttr)
            and attr.key == "cond"
            and isinstance(attr.expr, str)
            and attr.expr.strip() == condition
            for branch in self.branches
            for attr in branch[1]
        )
        if matches:
            calls.append(tuple(const_value(context.variables[name]) for name in self.used_vars))
        return original(self, context)

    monkeypatch.setattr(IfNode, "active_branch_body", active_branch_body)
    return calls


def _track_loop_iterations(monkeypatch, clause):
    original = ForNode.iter_bodies
    calls = []

    def iter_bodies(self, context):
        each_attrs = [attr for attr in self.branches[0][1] if isinstance(attr, ExprHtmlAttr) and attr.key == "each"]
        matches = len(each_attrs) == 1 and each_attrs[0].expr.strip() == clause
        for body, body_context in original(self, context):
            if matches:
                calls.append(
                    tuple(
                        body_context.variables[name] for name in self.branches[0][3] if name in body_context.variables
                    )
                )
            yield body, body_context

    monkeypatch.setattr(ForNode, "iter_bodies", iter_bodies)
    return calls


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
        assert _cache_has_prepared_text(c._const_body_cache, "same")

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
        assert _cache_has_leaf_program(c._const_body_cache)

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
        assert _cache_has_leaf_program(c._const_body_cache)

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
        assert _cache_has_prepared_text(c._const_body_cache, "same")
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
        assert _cache_has_prepared_text(c._const_body_cache, "same")

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
        assert _cache_has_prepared_text(c._const_body_cache, "constant")

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
        # Generated Vue declarations consume the marker in the prepared input
        # path before template evaluation; post-init observes plain values.
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
        assert _cache_has_prepared_text(app._const_body_cache, "fixed")

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
        assert _cache_has_prepared_text(app._const_body_cache, "fixed")

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

        rendered = Probe().render()
        assert rendered.render_target == "prepared"
        assert [part.value if hasattr(part, "value") else part.html for part in rendered.parts] == [
            "template",
            ":",
            "global",
        ]
        serialized = rendered.serialize()
        assert serialized.startswith('<div id="citry-vue-')
        assert '"serverData":{"js":["js"]}' in serialized
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
        assert _cache_has_prepared_text(app._const_body_cache, original)

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
        assert _cache_has_leaf_program(c._const_body_cache)

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
        assert _cache_has_prepared_text(c._const_body_cache, "original value")

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
        assert _cache_has_prepared_text(app._const_body_cache, "fixed")

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
        assert _cache_has_prepared_text(app._const_body_cache, "fixed")

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
    def test_const_expr_is_evaluated_once_for_a_reused_signature(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "cols")

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c1="">3</p>'
        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c2="">3</p>'
        assert calls == [(3,)]

    def test_dynamic_expr_stays_dynamic_in_shared_body(self, monkeypatch):
        c = Citry()
        const_calls = _track_prepared_expression(monkeypatch, "cols")
        dynamic_calls = _track_prepared_expression(monkeypatch, "other")

        class Card(Component):
            citry = c
            template = "<p>{{ cols }} and {{ other }}</p>"

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        # Two renders share the const signature but differ in the dynamic input.
        assert Card(cols=Const(3), other="x").render().serialize() == '<p data-cid-c1="">3 and x</p>'
        assert Card(cols=Const(3), other="y").render().serialize() == '<p data-cid-c2="">3 and y</p>'
        assert len(c._const_body_cache) == 1
        assert const_calls == [(3,)]
        assert dynamic_calls == [("x",), ("y",)]

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

    def test_const_if_branch_is_pruned(self, monkeypatch):
        c = Citry()
        calls = _track_if_selection(monkeypatch, "cols > 2")

        class Card(Component):
            citry = c
            template = '<c-if cond="cols > 2">big</c-if><c-else>small</c-else>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        assert Card(cols=Const(3)).render().serialize() == "big"
        assert Card(cols=Const(3)).render().serialize() == "big"
        assert Card(cols=Const(1)).render().serialize() == "small"
        assert calls == [(3,), (1,)]

    def test_const_if_with_no_match_precomputes_to_nothing(self, monkeypatch):
        c = Citry()
        calls = _track_if_selection(monkeypatch, "cols > 2")

        class Card(Component):
            citry = c
            template = '<c-if cond="cols > 2">big</c-if>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        assert Card(cols=Const(1)).render().serialize() == ""
        assert Card(cols=Const(1)).render().serialize() == ""
        assert calls == [(1,)]

    def test_dynamic_if_uses_each_render_input(self, monkeypatch):
        c = Citry()
        calls = _track_if_selection(monkeypatch, "cols > 2")

        class Card(Component):
            citry = c
            template = '<c-if cond="cols > 2">big</c-if><c-else>small</c-else>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        assert Card(cols=3).render().serialize() == "big"
        assert Card(cols=1).render().serialize() == "small"
        assert calls == [(3,), (1,)]

    def test_pruned_branch_is_precomputed_recursively(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "label")

        class Card(Component):
            citry = c
            template = '<c-if cond="show">{{ label }}: {{ count }}</c-if>'

            def template_data(self, kwargs, slots):
                return {
                    "show": kwargs["show"],
                    "label": kwargs["label"],
                    "count": kwargs["count"],
                }

        assert Card(show=Const(True), label=Const("n"), count=7).render().serialize() == "n: 7"  # noqa: FBT003
        assert Card(show=Const(True), label=Const("n"), count=8).render().serialize() == "n: 8"  # noqa: FBT003
        assert calls == [("n",)]

    def test_zero_variable_expr_renders_without_const_inputs(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ 1 + 1 }}</p>"

        assert Card().render().serialize() == '<p data-cid-c1="">2</p>'
        assert Card().render().serialize() == '<p data-cid-c2="">2</p>'

    def test_fill_content_updates_across_const_renders(self):
        c = Citry()

        class Box(Component):
            citry = c
            template = '<div><c-slot name="s">fb</c-slot></div>'

        class Page(Component):
            citry = c
            template = '<c-Box><c-fill name="s">{{ msg }}</c-fill></c-Box>'

            def template_data(self, kwargs, slots):
                return {"msg": kwargs["msg"], "k": kwargs["k"]}

        # Same const signature, different fills: both renders use their own fill.
        first = Page(msg="one", k=Const(1)).render().serialize()
        second = Page(msg="two", k=Const(1)).render().serialize()
        assert "one" in first
        assert "two" in second
        assert first != second

    def test_const_element_value_renders_fresh_each_time(self):
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
        assert first != second


class TestTemplateLiteralConst:
    """
    A literal attribute in a template is implicitly const: it is written in
    the template, so it cannot change between renders of that template.
    """

    def test_static_attr_is_const_in_the_child(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "age")

        class Card(Component):
            citry = c
            template = "<p>{{ age }}</p>"

        class Page(Component):
            citry = c
            template = '<c-Card age="30" />'

        assert Page().render().serialize() == '<p data-cid-c2="" data-cid-c1="">30</p>'
        assert Page().render().serialize() == '<p data-cid-c4="" data-cid-c3="">30</p>'
        assert calls == [("30",)]

    def test_unquoted_static_attr_is_const(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "age")

        class Card(Component):
            citry = c
            template = "<p>{{ age }}</p>"

        class Page(Component):
            citry = c
            template = "<c-Card age=30 />"

        assert "30" in Page().render().serialize()
        assert "30" in Page().render().serialize()
        assert calls == [("30",)]

    def test_boolean_attr_is_const_true(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "compact")

        class Card(Component):
            citry = c
            template = "<p>{{ compact }}</p>"

        class Page(Component):
            citry = c
            template = '<c-Card compact="" />'

        assert "True" in Page().render().serialize()
        assert "True" in Page().render().serialize()
        assert calls == [(True,)]

    def test_zero_variable_expression_attr_is_typed_const(self, monkeypatch):
        # c-age="30" evaluates to the int 30 (not the string "30") and is a
        # template literal, so it is marked const and the child precomputes on it.
        c = Citry()
        calls = _track_if_selection(monkeypatch, "age > 18")

        class Card(Component):
            citry = c
            template = '<c-if cond="age > 18">adult</c-if><c-else>minor</c-else>'

        class Page(Component):
            citry = c
            template = '<c-Card c-age="30" />'

        assert Page().render().serialize() == "adult"
        assert Page().render().serialize() == "adult"
        assert calls == [(30,)]

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

    def test_zero_variable_container_literal_unrolls_child_loop(self, monkeypatch):
        c = Citry()
        calls = _track_loop_iterations(monkeypatch, "i in items")

        class Items(Component):
            citry = c
            template = '<c-for each="i in items">[{{ i * mult }}]</c-for>'

        class Page(Component):
            citry = c
            template = '<c-Items c-items="[1, 2, 3]" c-mult="10" />'

        assert Page().render().serialize() == "[10][20][30]"
        assert calls == [(1,), (2,), (3,)]

        # Repeated renders hit the same signature: the per-render marker wraps
        # a fresh equal list, and the canonical key makes it the same entry.
        Page().render()
        Page().render()
        assert len(c._const_body_cache) == 2  # Page's body + Items' precomputed body
        assert calls == [(1,), (2,), (3,)]

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


class TestExpressionConstPropagation:
    """
    An expression attribute whose variables are all const at render time
    produces a const result (``c-age="base + 1"`` when ``base`` is const), so
    the child reuses its pre-computed work for that input as well. A single
    non-const variable in the expression breaks it, exactly like a dynamic
    attribute.
    """

    def test_all_const_expression_attr_is_const_in_the_child(self, monkeypatch):
        # base is const, so base + 1 (= 30) is const, so the child can resolve
        # its condition once for this input.
        c = Citry()
        calls = _track_if_selection(monkeypatch, "age > 18")

        class Card(Component):
            citry = c
            template = '<c-if cond="age > 18">adult</c-if><c-else>minor</c-else>'

        class Page(Component):
            citry = c
            template = '<c-Card c-age="base + 1" />'

            def template_data(self, kwargs, slots):
                return {"base": Const(29)}

        assert Page().render().serialize() == "adult"
        assert Page().render().serialize() == "adult"
        assert calls == [(30,)]

    def test_expression_mixing_const_and_dynamic_is_not_marked(self, monkeypatch):
        # base is const but n is not, so base + n is not const: the child must
        # reevaluate the condition as n changes.
        c = Citry()
        calls = _track_if_selection(monkeypatch, "age > 18")

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
        assert calls == [(30,), (-71,)]

    def test_propagated_const_dedups_across_a_loop(self, monkeypatch):
        # The win: a loop hands every child an all-const computed label, so all
        # the children share ONE precomputed cache entry (the loop var `i` is not in
        # the kwarg, so the kwarg is const every iteration and equal-valued).
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "label")

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
        assert calls == [("hi!",)]


class TestConstThroughTypedKwargs:
    def test_marker_survives_the_typed_kwargs_view(self, monkeypatch):
        # The auto-converted dataclass Kwargs stores values as-is, so the
        # marker flows whether template_data reads the typed view or the raw
        # dict. (A typed-Kwargs implementation that copies or coerces values,
        # for example a user-supplied Pydantic model, may strip the marker;
        # the value then safely renders as dynamic.)
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "cols")

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

            class Kwargs:
                cols: int

            def template_data(self, kwargs, slots):
                return {"cols": kwargs.cols}

        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c1="">3</p>'
        assert Card(cols=Const(3)).render().serialize() == '<p data-cid-c2="">3</p>'
        assert calls == [(3,)]

    def test_const_default_on_typed_kwargs_field(self, monkeypatch):
        # A `Const(...)` default is the explicit way to mark a default value
        # constant: when the kwarg is omitted, the marked default flows
        # through template_data and precomputes; when it is passed, the live value
        # renders as usual (dynamic unless the caller marked it).
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "cols")

        class Card(Component):
            citry = c
            template = "<p>{{ cols }}</p>"

            class Kwargs:
                cols: int = Const(3)

            def template_data(self, kwargs, slots):
                return {"cols": kwargs.cols}

        assert Card().render().serialize() == '<p data-cid-c1="">3</p>'
        assert Card(cols=5).render().serialize() == '<p data-cid-c2="">5</p>'
        assert Card().render().serialize() == '<p data-cid-c3="">3</p>'
        assert Card(cols=6).render().serialize() == '<p data-cid-c4="">6</p>'
        assert calls == [(3,), (5,), (6,)]


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

    def test_precomputes_inside_dynamic_if_branches(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "label")

        class Card(Component):
            citry = c
            template = '<c-if cond="show">{{ label }}: {{ n }}</c-if><c-else>{{ label }} off</c-else>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        # Both branches retain their dynamic values, while the const label is
        # evaluated once per branch when the body is prepared.
        assert Card(show=True, label=Const("x"), n=7).render().serialize() == "x: 7"
        assert Card(show=False, label=Const("x"), n=7).render().serialize() == "x off"
        assert Card(show=True, label=Const("x"), n=8).render().serialize() == "x: 8"
        assert len(c._const_body_cache) == 1
        assert calls == [("x",), ("x",)]

    def test_const_if_nested_in_dynamic_branch_is_pruned(self, monkeypatch):
        c = Citry()
        calls = _track_if_selection(monkeypatch, "big")

        class Card(Component):
            citry = c
            template = '<c-if cond="show"><c-if cond="big">L</c-if><c-else>S</c-else>{{ n }}</c-if>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        # The outer condition remains dynamic; the inner condition is decided
        # once per constant value while the neighboring value stays live.
        assert Card(show=True, big=Const(True), n=1).render().serialize() == "L1"  # noqa: FBT003
        assert Card(show=True, big=Const(True), n=2).render().serialize() == "L2"  # noqa: FBT003
        assert Card(show=True, big=Const(False), n=3).render().serialize() == "S3"  # noqa: FBT003
        assert calls == [(True,), (False,)]

    def test_precomputes_inside_kept_for_body(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "prefix")

        class Card(Component):
            citry = c
            template = '<c-for each="i in items">[{{ prefix }}{{ i }}]</c-for>'

        # `items` is dynamic, so the loop stays; the const `prefix` inside the
        # body precomputes (it is the same on every iteration), while the loop
        # variable expression stays dynamic.
        assert Card(items=[1, 2], prefix=Const("p")).render().serialize() == "[p1][p2]"
        assert Card(items=[3], prefix=Const("p")).render().serialize() == "[p3]"
        assert calls == [("p",)]

    def test_kept_for_and_empty_branch_use_their_live_scopes(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-for each="item in items">{{ outer }}:{{ item }}</c-for><c-empty>{{ outer }}</c-empty>'

            def template_data(self, kwargs, slots):
                return {"items": kwargs["items"], "outer": Const("outer")}

        assert Card(items=[1, 2]).render().serialize() == "outer:1outer:2"
        assert Card(items=[]).render().serialize() == "outer"

    def test_nested_loop_cannot_unroll_over_enclosing_loop_binding(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = (
                '<c-for each="outer in outer_items">'
                '<c-for each="inner in inner_items">{{ outer }}{{ inner }}</c-for>'
                "</c-for>"
            )

            def template_data(self, kwargs, slots):
                return {"outer_items": kwargs["outer_items"], "inner_items": Const(["a", "b"])}

        assert Card(outer_items=[1, 2]).render().serialize() == "1a1b2a2b"
        assert Card(outer_items=[3]).render().serialize() == "3a3b"


class TestConstPrecomputeInsideSlotContent:
    """
    Precomputing descends into slot content: fill bodies, the implicit default
    slot body, and slot fallback bodies all render against the variables of
    the component whose template wrote them, so const expressions inside
    them precompute like any other.
    """

    def test_const_expr_in_fill_body_precomputes(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "heading")

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
        assert calls == [("Dash",)]

    def test_const_if_inside_fill_body_prunes(self, monkeypatch):
        c = Citry()
        calls = _track_if_selection(monkeypatch, "wide")

        class Card(Component):
            citry = c
            template = '<c-slot name="body" />'

        class Page(Component):
            citry = c
            template = '<c-Card><c-fill name="body">x<c-if cond="wide">WIDE</c-if></c-fill></c-Card>'

        assert Page(wide=Const(True)).render().serialize() == "xWIDE"  # noqa: FBT003
        assert Page(wide=Const(True)).render().serialize() == "xWIDE"  # noqa: FBT003
        assert calls == [(True,)]

    def test_fill_data_var_stays_dynamic(self):
        c = Citry()

        class Box(Component):
            citry = c
            template = '<c-slot name="s" c-x="x" />'

        class Page(Component):
            citry = c
            template = '<c-Box c-x="n"><c-fill name="s" data="d">{{ d.x }}-{{ k }}</c-fill></c-Box>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        # Slot data follows each fill invocation while the const suffix stays
        # the same.
        assert Page(n=1, k=Const("K")).render().serialize() == "1-K"
        assert Page(n=2, k=Const("K")).render().serialize() == "2-K"

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

    def test_default_slot_body_precomputes(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "k")

        class Box(Component):
            citry = c
            template = '<b><c-slot name="default" /></b>'

        class Page(Component):
            citry = c
            template = "<c-Box>{{ k }}</c-Box>"

        assert Page(k=Const("K")).render().serialize() == '<b data-cid-c2="" data-cid-c1="">K</b>'
        assert Page(k=Const("K")).render().serialize() == '<b data-cid-c4="" data-cid-c3="">K</b>'
        assert calls == [("K",)]

    def test_slot_fallback_body_precomputes(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "label")

        class Card(Component):
            citry = c
            template = '<c-slot name="title">{{ label }}</c-slot>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        # Unfilled: the fallback renders and its const expression is evaluated
        # once for the shared signature.
        assert Card(label=Const("untitled")).render().serialize() == "untitled"
        assert Card(label=Const("untitled")).render().serialize() == "untitled"
        assert calls == [("untitled",)]

        # Filled: the fill wins over the precomputed fallback, same as ever.
        assert Card(label=Const("untitled"), slots={"title": "Hello"}).render().serialize() == "Hello"
        assert calls == [("untitled",)]


class TestConstPrecomputeUnroll:
    def test_const_loop_unrolls_to_text(self, monkeypatch):
        c = Citry()
        calls = _track_prepared_expression(monkeypatch, "i")
        items = Const([1, 2, 3])

        class Card(Component):
            citry = c
            template = '<ul><c-for each="i in items">{{ i }},</c-for></ul>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        assert Card(items=items).render().serialize() == '<ul data-cid-c1="">1,2,3,</ul>'
        assert Card(items=items).render().serialize() == '<ul data-cid-c2="">1,2,3,</ul>'
        assert calls == [(1,), (2,), (3,)]

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

    def test_unroll_precomputes_ifs_and_uses_empty_branch(self, monkeypatch):
        c = Citry()
        calls = _track_if_selection(monkeypatch, "i > 1")

        class Card(Component):
            citry = c
            template = '<c-for each="i in items"><c-if cond="i > 1">{{ i }}!</c-if></c-for><c-empty>none</c-empty>'

        assert Card(items=Const([1, 2, 3])).render().serialize() == "2!3!"
        assert Card(items=Const([])).render().serialize() == "none"
        assert calls == [(1,), (2,), (3,)]

    def test_long_const_loop_renders_all_items(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-for each="i in items">.</c-for>'

        n = _MAX_UNROLL_ITERATIONS + 1
        out = Card(items=Const(range(n))).render().serialize()
        assert out == "." * n

    def test_const_loop_renders_element_values_fresh_each_time(self):
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
        assert first != second

    def test_dynamic_loop_uses_new_items_each_render(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-for each="i in items">{{ i }}</c-for>'

        assert Card(items=[1, 2]).render().serialize() == "12"
        assert Card(items=[3, 4]).render().serialize() == "34"


class TestConstPrecomputeErrors:
    def test_failing_const_expr_stays_dynamic_and_raises_at_render(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<p>{{ cfg["missing"] }}</p>'

            def template_data(self, kwargs, slots):
                return dict(kwargs)

        # A failed const evaluation is deferred so the error surfaces through
        # the normal render path on every render.
        with pytest.raises(KeyError):
            Card(cfg=Const({"a": 1})).render().serialize()
        with pytest.raises(KeyError):
            Card(cfg=Const({"a": 1})).render().serialize()

    def test_failing_const_cond_keeps_the_if_dynamic(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<c-if cond=\"cfg['missing']\">a</c-if>"

        with pytest.raises(KeyError):
            Card(cfg=Const({"a": 1})).render().serialize()
        with pytest.raises(KeyError):
            Card(cfg=Const({"a": 1})).render().serialize()


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
