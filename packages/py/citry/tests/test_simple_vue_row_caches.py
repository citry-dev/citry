"""
Per-row work that ``simple="vue"`` rows compute once and reuse.

A page of ``simple="vue"`` rows computes some results that depend only on
the template or on attribute names. These tests check that three such results
are computed once per compiled template or once per serialization, and that
each matches the per-row result:

1. Serialize copies the data the generated evaluator wrote instead of
   checking and converting it again; other leaf data is still converted.
2. The root ``c-bind`` resolves its attribute names, order, and source
   positions once per key set (up to ``_ROOT_SPREAD_PLAN_LIMIT`` key sets);
   each row only places its values.
3. The check that confirms, before the evaluator runs, that every variable the
   template reads holds plain JSON is written out once per compiled template
   as straight-line code.

Each cached result lives with the object it describes (the serialization pass
or the compiled template), so a template reload builds a fresh one.
"""

from __future__ import annotations

import itertools
import json
import math
import re
import subprocess
import sys
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue import direct_capture, events, leaf_program
from citry._vue.json_data import _copy_evaluated_json, _json_plain
from citry.citry_render import CitryRender, SimpleVueRecord
from citry.component_render import _simple_vue_admission

ROW_TEMPLATE = """
<article c-bind="row_attrs" data-fixed="source" hidden>
<h3>{{ row['title'] }}</h3>
<p c-data-count="row['count']">text \n  with authored spacing</p>
<ul>
<li c-for="item in row['items']" c-data-item="item['id']">{{ item['label'] }}</li>
</ul>
</article>
"""

PAGE_TEMPLATE = """<main><c-Row c-for="row in rows" #c-key="row['id']" c-row="row" c-attrs="row['attrs']" /></main>"""


def _rows(attrs: list[dict[str, object] | None]) -> list[dict[str, Any]]:
    return [
        {
            "id": f"r{index}",
            "title": f"<b>Row {index}</b> & more",
            "count": index,
            "items": [{"id": f"r{index}-i{item}", "label": f"item {item}"} for item in range(index % 3)],
            "attrs": row_attrs,
        }
        for index, row_attrs in enumerate(attrs)
    ]


def _build(*, simple: object, row_template: str = ROW_TEMPLATE) -> tuple[type[Component], type[Component]]:
    """Build Page -> rows of Row on a fresh engine with fixed render IDs."""
    counter = itertools.count()
    app = Citry(autodiscover=False, id_generator=lambda: f"r{next(counter)}")
    app.set_mounted_prefix("/citry")
    simple_mode = simple

    class Row(Component):
        citry = app
        simple = simple_mode
        template = row_template
        js = """
            $component({data(){return {open: true};}});
        """

        class Kwargs:
            row: dict
            attrs: dict | None

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"row": kwargs.row, "row_attrs": kwargs.attrs}

    class Page(Component):
        citry = app
        template = PAGE_TEMPLATE

    return Row, Page


def _simple_records(render: CitryRender) -> list[SimpleVueRecord]:
    records: list[SimpleVueRecord] = []
    pending: list[CitryRender] = [render]
    while pending:
        current = pending.pop()
        for part in current.parts:
            if type(part) is SimpleVueRecord:
                records.append(part)
            elif isinstance(part, CitryRender):
                pending.append(part)
    return records


def _capture_assemblies(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Record every Assembly the Vue serializer builds."""
    assemblies: list[Any] = []
    original = events.assemble_typed_render

    def capture(*args: Any, **kwargs: Any) -> Any:
        assembly = original(*args, **kwargs)
        assemblies.append(assembly)
        return assembly

    monkeypatch.setattr(events, "assemble_typed_render", capture)
    return assemblies


def _outcome(function: Any) -> tuple[str, str]:
    """Return ("ok", output) or the error type and message, for side-by-side comparison."""
    try:
        return ("ok", function())
    except Exception as error:  # noqa: BLE001 - the comparison covers every error type
        return (type(error).__name__, str(error))


PLAIN_ATTRS: list[dict[str, object] | None] = [
    {"id": "row-0", "data-n": 0, "data-f": 1.5, "data-t": True, "data-e": ""},
    {"id": "row-1", "data-n": 1, "data-f": -2.0, "data-t": False, "data-e": None},
    {"data-e": "x", "id": "row-2"},
    None,
    {},
    {"id": "row-5", "data-n": 5, "data-f": 0.25, "data-t": True, "data-e": "e"},
]


# 1. Evaluated prepared data is copied, not converted again.


def _assert_same_json(left: object, right: object) -> None:
    """Equal values with equal exact types at every level (True must not equal 1)."""
    assert type(left) is type(right)
    if type(left) is dict:
        assert list(left) == list(right)  # type: ignore[arg-type]
        for key in left:  # type: ignore[union-attr]
            _assert_same_json(left[key], right[key])  # type: ignore[index]
    elif type(left) is list:
        assert len(left) == len(right)  # type: ignore[arg-type]
        for item, other in zip(left, right, strict=True):  # type: ignore[call-overload]
            _assert_same_json(item, other)
    else:
        assert left == right or (type(left) is float and math.isnan(left) and math.isnan(right))  # type: ignore[arg-type]


def test_evaluated_leaf_data_is_plain_and_copied_by_assembly(monkeypatch: pytest.MonkeyPatch) -> None:
    assemblies = _capture_assemblies(monkeypatch)
    _row, page = _build(simple="vue")
    rendered = page(rows=_rows(PLAIN_ATTRS)).render()
    rendered.serialize()
    leaves = {record.render_id: record.leaf for record in _simple_records(rendered)}
    assert leaves
    assert all(leaf.prepared_data_evaluated_plain for leaf in leaves.values())

    assembly = assemblies[-1]
    occurrences = {occurrence.id: occurrence for occurrence in assembly.view.occurrences}
    for occurrence_id, render_id in assembly.occurrence_to_render.items():
        leaf = leaves.get(render_id)
        if leaf is None:
            continue
        assembled = occurrences[occurrence_id].prepared_data
        for key, value in leaf.prepared_data.items():
            # The copy equals what the checking conversion would produce.
            _assert_same_json(assembled[key], _json_plain(value))
            _assert_same_json(_copy_evaluated_json(value), _json_plain(value))
            if type(value) in {dict, list}:
                assert assembled[key] is not value
        # Changing the assembled copy leaves the evaluated leaf untouched.
        attrs_keys = [key for key, value in assembled.items() if type(value) is dict and key.startswith("citryAttrs")]
        before = json.dumps(leaf.prepared_data, sort_keys=True)
        for key in attrs_keys:
            assembled[key]["data-mutated"] = "yes"
        assert json.dumps(leaf.prepared_data, sort_keys=True) == before


def test_only_evaluated_leaf_data_skips_the_checking_conversion(monkeypatch: pytest.MonkeyPatch) -> None:
    copied: list[object] = []

    def spy(value: object) -> object:
        copied.append(value)
        return _copy_evaluated_json(value)

    monkeypatch.setattr(direct_capture, "_copy_evaluated_json", spy)
    _row, ordinary_page = _build(simple=False)
    ordinary = ordinary_page(rows=_rows(PLAIN_ATTRS)).render()
    ordinary_html = ordinary.serialize()
    assert copied == []

    _row, simple_page = _build(simple="vue")
    assert simple_page(rows=_rows(PLAIN_ATTRS)).render().serialize() == ordinary_html
    assert copied


# 2. Root c-bind names are resolved once per key set.


SPREAD_CASES: list[list[dict[str, object] | None]] = [
    PLAIN_ATTRS,
    # A spread value for a static attribute: equal (kept as authored), different, and a case variant.
    [{"data-fixed": "source"}, {"data-fixed": "other"}, {"DATA-FIXED": "x"}, {"hidden": False}],
    # Two keys with one HTML identity, and class/style contributions.
    [{"ID": "a", "id": "b"}, {"class": "a", "style": "color: red"}, {"class": None}],
    # Spread before and after key order changes, and many optional values.
    [{"a": 1, "b": 2}, {"b": 2, "a": 1}, {"a": None, "b": False}, {"a": True, "b": 0}],
]

ERROR_CASES: list[dict[str, object]] = [
    {"data-cev-x": "1"},
    {"data-citry-runtime-events": "1"},
    {"v-show": "x"},
    {":title": "x"},
    {"onclick": "x"},
    {"#c-key": "x"},
    {"$c-tr:title": "x"},
    {"bad name": "x"},
    {"$c-props": "x"},
    {"$C-PROPS": "x"},
    {"innerHTML": "x"},
]


@pytest.mark.parametrize("case", range(len(SPREAD_CASES)))
@pytest.mark.parametrize("deps_strategy", ["document", "simple"])
@pytest.mark.parametrize("ssr", [True, False])
def test_root_spread_plans_match_the_full_merge(
    monkeypatch: pytest.MonkeyPatch, case: int, deps_strategy: str, ssr: bool
) -> None:
    rows = _rows(SPREAD_CASES[case])

    def serialize(*, simple: object) -> tuple[str, str]:
        _row, page = _build(simple=simple)
        return _outcome(lambda: page(rows=rows).render().serialize(deps_strategy=deps_strategy, ssr=ssr))

    planned = serialize(simple="vue")
    ordinary = serialize(simple=False)
    # Plain key sets really took the shortcut rather than the full merge.
    if case == 0:
        row, page = _build(simple="vue")
        page(rows=rows).render()
        stored = [plan for cache in _spread_plan_caches(row) for plan in cache.plans.values()]
        assert stored
        assert all(plan is not None for plan in stored)
    # A plan limit of zero sends every row through the full per-row merge.
    monkeypatch.setattr(leaf_program, "_ROOT_SPREAD_PLAN_LIMIT", 0)
    full_merge = serialize(simple="vue")

    assert planned == full_merge
    assert planned[0] == "ok"
    assert planned == ordinary
    if deps_strategy == "simple":
        # The authored boolean `hidden` on the c-bind root keeps its authored
        # spelling in static output, on both simple='vue' paths.
        assert ' hidden=""' not in planned[1]
        assert re.search(r"<article [^>]*\bhidden\b", planned[1])


BOOLEAN_TEMPLATES = {
    "after-spread": """
        <article c-bind="row_attrs" hidden>{{ row['title'] }}</article>
    """,
    "before-spread": """
        <article hidden disabled c-bind="row_attrs">{{ row['title'] }}</article>
    """,
    "uppercase": """
        <article HIDDEN c-bind="row_attrs">{{ row['title'] }}</article>
    """,
    "nested-spread": """
        <div><p c-bind="row_attrs" hidden>{{ row['title'] }}</p></div>
    """,
    # A valueless attribute that is not an HTML boolean attribute.
    "valueless-data": """
        <article c-bind="row_attrs" data-y>{{ row['title'] }}</article>
    """,
}


@pytest.mark.parametrize("row_template", list(BOOLEAN_TEMPLATES.values()), ids=list(BOOLEAN_TEMPLATES))
def test_authored_boolean_attributes_next_to_a_spread_match_ordinary(
    monkeypatch: pytest.MonkeyPatch, row_template: str
) -> None:
    # The spread either leaves the authored boolean alone or replaces it with
    # a value of its own, which must then be written as that value.
    rows = _rows([None, {}, {"hidden": True}, {"hidden": ""}, {"hidden": "x"}, {"hidden": False}, {"id": "a"}])

    def serialize(*, simple: object) -> str:
        _row, page = _build(simple=simple, row_template=row_template)
        return page(rows=rows).render().serialize(deps_strategy="simple")

    ordinary = serialize(simple=False)
    planned = serialize(simple="vue")
    monkeypatch.setattr(leaf_program, "_ROOT_SPREAD_PLAN_LIMIT", 0)
    full_merge = serialize(simple="vue")

    assert planned == full_merge == ordinary


@pytest.mark.parametrize("attrs", ERROR_CASES, ids=[next(iter(case)) for case in ERROR_CASES])
def test_root_spread_plans_raise_the_full_merge_errors(
    monkeypatch: pytest.MonkeyPatch, attrs: dict[str, object]
) -> None:
    rows = _rows([{"id": "ok"}, attrs])

    def render() -> tuple[str, str]:
        _row, page = _build(simple="vue")
        return _outcome(lambda: page(rows=rows).render().serialize())

    planned = render()
    monkeypatch.setattr(leaf_program, "_ROOT_SPREAD_PLAN_LIMIT", 0)
    assert planned == render()
    assert planned[0] != "ok"


def _spread_plan_caches(row: type[Component]) -> list[leaf_program._RootSpreadPlans]:
    """Return the plan caches owned by the Row class's compiled evaluator."""
    # Rows run only this evaluator; the row HTML writer reads its records
    # and never resolves a spread itself.
    program = _simple_vue_admission(row).leaf_node._simple_json_program
    if program is None:
        return []
    return [
        operation
        for operation in program.evaluate.__globals__["_operations"]
        if type(operation) is leaf_program._RootSpreadPlans
    ]


def test_root_spread_plans_are_bounded_and_reset_with_the_template(monkeypatch: pytest.MonkeyPatch) -> None:
    # Every row brings its own key set, more than the plan limit.
    many = [{f"data-k{index}": index} for index in range(leaf_program._ROOT_SPREAD_PLAN_LIMIT + 8)]
    row, page = _build(simple="vue")
    planned = page(rows=_rows(many)).render().serialize(deps_strategy="simple")
    caches = _spread_plan_caches(row)
    assert caches
    assert max(len(cache.plans) for cache in caches) == leaf_program._ROOT_SPREAD_PLAN_LIMIT

    # A reloaded template compiles a new evaluator with empty plans.
    row.template = """
        <section c-bind="row_attrs" data-new="yes">{{ row['title'] }}</section>
    """
    row.reset_template()
    html = page(rows=_rows(PLAIN_ATTRS)).render().serialize(deps_strategy="simple")
    new_caches = _spread_plan_caches(row)
    assert not {id(cache) for cache in new_caches} & {id(cache) for cache in caches}
    assert html.count('data-new="yes"') == len(PLAIN_ATTRS)

    monkeypatch.setattr(leaf_program, "_ROOT_SPREAD_PLAN_LIMIT", 0)
    row_again, page_again = _build(simple="vue")
    assert page_again(rows=_rows(many)).render().serialize(deps_strategy="simple") == planned
    assert all(not cache.plans for cache in _spread_plan_caches(row_again))


def test_root_spread_plans_with_replaced_formatting(monkeypatch: pytest.MonkeyPatch) -> None:
    # A replaced escaper or formatter sends serialize to the per-row path,
    # which formats the openings the evaluator's plans produced.
    monkeypatch.setattr(leaf_program, "_default_row_formatting", lambda: False)
    rows = _rows(PLAIN_ATTRS)
    row, page = _build(simple="vue")
    planned = page(rows=rows).render().serialize(deps_strategy="simple")
    stored = [plan for cache in _spread_plan_caches(row) for plan in cache.plans.values()]
    assert stored
    assert all(plan is not None for plan in stored)

    monkeypatch.setattr(leaf_program, "_ROOT_SPREAD_PLAN_LIMIT", 0)
    _row, full_page = _build(simple="vue")
    assert full_page(rows=rows).render().serialize(deps_strategy="simple") == planned


# 3. The read-set check is written out once per template.


READSET_VARIABLES: list[object] = [
    {"row": {"title": "t", "count": 1, "items": [{"id": "a", "label": "b"}]}, "row_attrs": {"id": "x"}},
    {"row": {"title": "t", "count": 1, "items": []}, "row_attrs": None},
    {"row": {"title": None, "count": 1.5, "items": []}, "row_attrs": {"id": 1, "b": True, "f": 0.5}},
    # Missing reads, wrong containers, and values outside plain JSON.
    {"row": {"title": "t", "items": []}, "row_attrs": None},
    {"row": {"title": "t", "count": 1, "items": ()}, "row_attrs": None},
    {"row": {"title": "t", "count": 1, "items": [{"id": "a"}]}, "row_attrs": None},
    {"row": {"title": "t", "count": float("nan"), "items": []}, "row_attrs": None},
    {"row": {"title": "t", "count": 1, "items": [{"id": "a", "label": float("inf")}]}, "row_attrs": None},
    {"row": {"title": "t", "count": 1, "items": []}, "row_attrs": {"id": float("nan")}},
    {"row": {"title": "t", "count": 1, "items": []}, "row_attrs": {1: "x"}},
    {"row": {"title": "t", "count": 1, "items": []}, "row_attrs": {"id": ["x"]}},
    {"row": {"title": "t", "count": 1, "items": []}, "row_attrs": "id"},
    {"row": {"title": object(), "count": 1, "items": []}, "row_attrs": None},
    {"row": ["t"], "row_attrs": None},
    # A read name that is also a loop variable would be shadowed.
    {"row": {"title": "t", "count": 1, "items": []}, "row_attrs": None, "item": 1},
    [("row", {})],
    None,
]


def test_generated_readset_check_matches_the_shared_walker() -> None:
    row, page = _build(simple="vue")
    page(rows=_rows(PLAIN_ATTRS[:1])).render()
    program = _simple_vue_admission(row).leaf_node._simple_json_program
    preflight = program.readset_preflight
    # The check is written out, not a call into the shared walker.
    assert "_simple_json_readset_is_plain" not in preflight.__code__.co_names
    read_set = preflight.__globals__["_read_set"]

    results = [preflight(None, variables) for variables in READSET_VARIABLES]
    expected = [leaf_program._simple_json_readset_is_plain(variables, read_set) for variables in READSET_VARIABLES]
    assert results == expected
    assert results[:3] == [True, True, True]
    assert not any(results[3:])


def test_deeply_nested_readset_keeps_the_shared_walker() -> None:
    # Python rejects more than 20 nested loops in one function, so a read
    # set this deep cannot be written out and must use the shared walker.
    node = leaf_program._SimpleJsonReadNode(frozenset({"scalar"}), ())
    for _depth in range(24):
        node = leaf_program._SimpleJsonReadNode(frozenset({"list"}), (), node)
    read_set = leaf_program._SimpleJsonReadSet((("rows", node),), ())
    lines = leaf_program._simple_json_readset_check_lines(read_set, indent=4)
    with pytest.raises(SyntaxError):
        compile("\n".join(("def check(variables):", *lines)), "<test>", "exec")

    codegen = object.__new__(leaf_program._SimpleJsonCodegen)
    codegen.functions = []
    codegen.counter = 0
    codegen._read_set = read_set
    codegen._readset_preflight_function()
    assert "_simple_json_readset_is_plain(variables, _read_set)" in codegen.functions[0]


def test_generated_readset_check_sees_a_later_component_like_registration() -> None:
    source = """
from citry import Citry, Component
from citry.component_like import ComponentLike

app = Citry(autodiscover=False)

class Leaf(Component):
    citry = app
    simple = "vue"
    template = '<p c-bind="attrs">{{ value }}</p>'
    js = "$component({});"

    class Kwargs:
        value: str

    @staticmethod
    def template_data(kwargs, slots):
        return {"value": kwargs.value, "attrs": {"id": "x"}}

class Page(Component):
    citry = app
    template = '<main><c-Leaf c-for="v in values" c-value="v" /></main>'

assert "&lt;a" in Page(values=["<a", "b"]).render().serialize(deps_strategy="ignore")
ComponentLike.register(str)
try:
    Page(values=["<a", "b"]).render()
except TypeError as error:
    assert "not safe for the context-free evaluator" in str(error), error
else:
    raise AssertionError("a registered str was still treated as plain JSON")
"""
    # Registration is process-wide, so it runs in its own interpreter.
    result = subprocess.run([sys.executable, "-c", source], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
