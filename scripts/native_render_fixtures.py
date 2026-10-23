"""
Write the test fixtures of ``crates/citry_native_render`` from Citry's own Python code.

The Rust crate evaluates ``simple = "vue"`` row templates, hashes call-run
ids and writes call-run manifest items without any Python, so its tests
compare it with answers observed from Python. This script produces those
answers:

- ``board_rows.json`` and ``shapes.json``: a template's plan (the tuples
  ``native_row_plan_tuples`` passes to Rust), and for each row its variables
  (with each value's Python type spelled out), the root ``c-bind`` layout
  Python gives its key set, and the prepared-data JSON Citry's Python
  evaluator and assembly write;
- ``run_digests.json``: call-run row ids computed by Python's ``_DigestPrefix``;
- ``walk_rows.json``: loops over JSON data, as a template writes them (the
  loop clause, the call's inputs and its ``#c-key``), with the paths
  ``citry._vue.native_walk`` lowers them to, and the values Python's
  sandboxed evaluator reads for each row (or the error it raises), and, for
  a case where the Rust walk must decline, the reason it gives;
- ``run_items.json``: whole call runs (the rows one ``c-for`` places), with
  each row's ids from ``_DigestPrefix``, each row's manifest item as
  ``_script_json`` writes a dict with the keys ``prepared_manifest`` and
  ``_prepare_holding_assets`` give a run row, and the first repeated key.
  The item's key set is copied here by hand; the page tests in
  ``test_native_render_runs.py`` check its whole shape.

The expected bytes always come from Python, never from Rust, so the cargo
tests lock observed behavior. Run from the repository root:

    uv run --no-sync python scripts/native_render_fixtures.py          # write
    uv run --no-sync python scripts/native_render_fixtures.py --check  # compare

``--check`` exits with status 1 and names each file that differs from what
the current Python code writes; a Python test runs it, so a fixture cannot
drift from Python's output.
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import math
import random
import struct
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from citry import Citry, Component
from citry._vue.direct_capture import _DIGEST_JSON, _DigestPrefix
from citry._vue.json_data import _copy_evaluated_json
from citry._vue.leaf_program import LeafProgramNode, native_row_plan_tuples
from citry._vue.native_walk import lower_loop, lower_path
from citry._vue.serialization import _script_json
from citry.component_render import _simple_vue_admission
from citry.constness import _ConstMapping, _overlay_const_mapping, const_value
from citry_core.safe_eval import compile_expr

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "crates" / "citry_native_render" / "tests" / "fixtures"

# The row template of the benchmark's project-board page (`ProjectOutput` in
# benchmarks/web/apps/citry), copied here so the fixtures do not change when
# the benchmark app does.
BOARD_ROW_TEMPLATE = """
<article c-bind="row_attrs" data-output-expanded="true">
<header>
<span class="row-title">{{ row['title'] }}</span>
<span class="row-status">{{ row['status'] }}</span>
<span c-data-output-badge="row['status']">{{ row['badge'] }}</span>
</header>
<form class="output-form">
<input type="hidden" name="row_id" c-value="row['id']">
<label>Description <textarea data-output-description>{{ row['description'] }}</textarea>
</label>
<label>
<input type="checkbox" data-output-completed c-checked="row['completed']"> Completed</label>
<button c-data-bench-action="row['select_action']">Select</button>
</form>
<section>
<c-if cond="row['dependencies']">
<article
  c-for="dep in row['dependencies']"
  c-data-dependency-id="dep['id']"
  c-data-dependency-title="dep['title']"
  c-data-dependency-completed="'true' if dep['completed'] else 'false'"
>
<span class="dependency-title">{{ dep['title'] }}</span>
</article>
</c-if>
<c-else>
<p>No dependencies</p>
</c-else>
</section>
<section>
<c-if cond="row['attachments']">
<article
  c-for="attachment in row['attachments']"
  c-data-attachment-id="attachment['id']"
  c-data-attachment-name="attachment['name']"
>
<a class="attachment-name" c-href="attachment['url']">{{ attachment['name'] }}</a>
<span c-for="tag in attachment['tags']" c-data-attachment-tag="tag">{{ tag }}</span>
</article>
</c-if>
<c-else>
<p>No attachments</p>
</c-else>
</section>
</article>
"""

# A template for the shapes the board does not use: a root c-bind that
# spreads a dict inside a variable, literal texts, a conditional expression,
# c-if/c-elif with no match, literal and boolean attributes, nested loops
# reading the outer loop's item, and truth tests on dicts and strings. Every
# piece is one simple='vue' accepts (c-empty is not).
SHAPE_TEMPLATE = """
<div data-kind="shape" c-bind="v['attrs']">
<p>{{ 'lit' }}|{{ None }}|{{ True }}|{{ v['a'] if v['flag'] else v['b'] }}|{{ v['n'] }}</p>
<p c-if="v['x']">x</p>
<p c-elif="v['y']">y</p>
<input
  type="checkbox"
  c-checked="v['flag']"
  c-disabled="True"
  c-data-n="v['n']"
  c-data-lit="'k'"
  c-data-none="None"
>
<ul>
<li c-for="o in v['outer']" c-data-k="o['k']">
<b c-for="i in o['inner']" c-data-pair="o['k']">{{ i }}{{ o['k'] }}</b>
</li>
</ul>
<span c-if="v['d']">dict truthy</span>
<span c-else>dict falsy</span>
</div>
"""

BOARD_ROWS = 10
# A fixed seed, so --check sees the same rows every run.
SEED = 20261023


def typed(value: object) -> object:
    """Spell out a value's exact Python type, which JSON alone loses."""
    if value is None:
        return {"none": None}
    if type(value) is bool:
        return {"bool": value}
    if type(value) is int:
        return {"int": str(value)}
    if type(value) is float:
        return {"float": [repr(value)]}
    if type(value) is str:
        return {"str": value}
    if type(value) is dict:
        return {"dict": [[key, typed(item)] for key, item in value.items()]}
    if type(value) is list:
        return {"list": [typed(item) for item in value]}
    msg = f"fixture rows hold only plain values, got {type(value).__name__}"
    raise TypeError(msg)


def described(value: object) -> object:
    """Turn the plan tuples into JSON, replacing each layout callback with a marker."""
    if callable(value):
        return "<layout>"
    if isinstance(value, tuple):
        return [described(item) for item in value]
    return value


def row_node(template: str) -> LeafProgramNode:
    """Return the compiled template node Citry uses for a ``simple='vue'`` component with this template."""
    engine = Citry(autodiscover=False)
    component = type("FixtureRow", (Component,), {"citry": engine, "simple": "vue", "template": template})
    node = _simple_vue_admission(component).leaf_node
    if not isinstance(node, LeafProgramNode):
        msg = "the fixture template is not admitted as simple='vue'"
        raise TypeError(msg)
    return node


def spread_dict(variables: dict[str, Any], path: tuple[str, str, tuple[str, ...]]) -> Any:
    """Follow a spread's path (``("p", root, keys)``) to the dict whose keys it spreads."""
    _tag, root, keys = path
    value = variables[root]
    for key in keys:
        value = value[key]
    return value


def fixture_for(node: LeafProgramNode, cases: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    """Describe the node's plan and, for each row Python accepts, the JSON Python writes for it."""
    tuples = native_row_plan_tuples(node)
    if tuples is None:
        msg = "the fixture template has no Rust plan"
        raise TypeError(msg)
    ops, roots, loop_targets, _spread_limit, js_safe_integer = tuples
    # The layout callbacks and the path each spread reads, in spread order.
    spreads = [
        (cast("Callable[[tuple[str, ...]], Any]", op[3]), cast("tuple[str, str, tuple[str, ...]]", op[2]))
        for op in ops
        if op[0] == "spread"
    ]
    program = node._simple_json_program
    if program is None:
        msg = "the fixture template has no Python evaluator"
        raise TypeError(msg)
    rows = []
    for label, variables in cases:
        if not program.readset_preflight(None, variables):
            continue
        entries = [layout(tuple(spread_dict(variables, path) or ())) for layout, path in spreads]
        # A key set Python merges per row has no layout, so Rust declines it.
        if any(entry is None for entry in entries):
            continue
        leaf = node.render_static_instance_free(variables, component_name="FixtureRow")
        data = {key: _copy_evaluated_json(value) for key, value in leaf.prepared_data.items()}
        rows.append(
            {
                "name": label,
                "variables": typed(variables),
                "spreads": [[list(item) for item in entry] for entry in entries],
                "expected": _script_json({"calls": {}, **data}),
            }
        )
    return {
        "plan": {
            "ops": described(ops),
            "roots": described(roots),
            "loop_targets": list(loop_targets),
            "js_safe_integer": js_safe_integer,
        },
        "rows": rows,
    }


def board_variables(rng: random.Random, index: int) -> dict[str, Any]:
    """One board row's variables, shaped as the benchmark page's ``template_data`` returns them."""
    dependencies = [
        {"id": f"d{index}-{n}", "title": f"Dependency {n}", "completed": rng.random() < 0.5}
        for n in range(rng.randrange(4))
    ]
    attachments = [
        {
            "id": f"a{index}-{n}",
            "name": f"file-{n}.pdf",
            "url": f"/files/{index}/{n}?v=1&x=<{n}>",
            "tags": [f"tag{m}" for m in range(rng.randrange(3))],
        }
        for n in range(rng.randrange(3))
    ]
    completed = rng.random() < 0.3
    row = {
        "id": f"output-{index}",
        "title": f"Output {index} \u2013 caf\u00e9",
        "status": rng.choice(["todo", "doing", "done"]),
        "badge": "Completed" if completed else "In progress",
        "description": f'Line one\nline "two" for {index}',
        "completed": completed,
        "select_action": f"select:{index}",
        "dependencies": dependencies,
        "attachments": attachments,
    }
    attrs: dict[str, Any] = {"id": f"row-{index}", "data-row-id": row["id"], "data-selected": "false"}
    if index % 3 == 0:
        attrs["data-source-id"] = f"source-{index}"
    return {"row": row, "row_attrs": attrs}


def finite_float(rng: random.Random) -> float:
    """A float drawn from every magnitude, including subnormals."""
    while True:
        value = struct.unpack("<d", struct.pack("<Q", rng.getrandbits(64)))[0]
        if math.isfinite(value):
            return value


def edge_rows(base: dict[str, Any], rng: random.Random) -> list[tuple[str, dict[str, Any]]]:
    """Rows that put every value rule through every text and attribute position: escapes, floats, big ints."""
    cases: list[tuple[str, dict[str, Any]]] = []
    specials = [
        "",
        'quote " backslash \\ slash /',
        "tags <script>&amp; > ' ",
        "control \x00\x01\x08\x0c\n\r\t\x1f\x7f",
        "latin caf\u00e9 \u00ff",
        "bmp \u2028\u2029\uffff \u4e2d",
        "astral \U0001f600 \U0010ffff",
    ]
    # Floats where two shortest texts are equally close, and the ends of the
    # ranges where Python switches between plain and exponent notation.
    floats = [0.0, -0.0, 0.1, 1.5, 1e16, 1e15, 123456789012345678.0, 1e-4, 1e-5, 5e-324, 1.7976931348623157e308]
    floats += [2**50 + 0.25, -(2**51 + 0.75), 1113178120592002.2, 9 * 10**15 + 0.5]
    # Many more floats run through Rust in tests/test_native_render_rows.py,
    # which compares them with Python directly.
    floats += [finite_float(rng) for _ in range(2)]
    ints = [0, -1, 2**53 - 1, 2**53, -(2**53) + 1, -(2**53), 2**63 - 1, -(2**63)]
    scalars: list[object] = [None, True, False, *ints, *floats, *specials]
    for index, value in enumerate(scalars):
        variables = copy.deepcopy(base)
        row = variables["row"]
        for key in ("title", "status", "badge", "id", "description", "completed", "select_action"):
            row[key] = value
        row["dependencies"] = [{"id": value, "title": value, "completed": value}]
        row["attachments"] = [
            {"id": value, "name": value, "url": value, "tags": [value, index, "t"]},
            {"id": index, "name": "second", "url": "/x", "tags": []},
        ]
        variables["row_attrs"] = {"id": f"row-{index}", "data-value": value, "aria-label": value}
        cases.append((f"scalar[{index}]={value!r:.40}", variables))
    for truth in (0, 1, "", "x", [], [1], {}, {"a": 1}, None, 0.0, 2.5, True, False, -0.0):
        variables = copy.deepcopy(base)
        variables["row"]["dependencies"] = [
            {"id": 1, "title": "a", "completed": truth},
            {"id": 2, "title": "b", "completed": not truth},
        ]
        cases.append((f"truth={truth!r}", variables))
    for label, attrs in (
        ("row_attrs=None", None),
        ("c-bind names that sort by code point", {"data-z": 1, "data-a": 3, "data-\u00e9": 4, "aria-x": "y"}),
        ("c-bind values that leave attributes out", {"id": "x", "data-a": None, "data-b": False, "data-c": True}),
    ):
        variables = copy.deepcopy(base)
        variables["row_attrs"] = attrs
        cases.append((label, variables))
    variables = copy.deepcopy(base)
    variables["row"]["dependencies"] = []
    variables["row"]["attachments"] = []
    cases.append(("empty lists", variables))
    return cases


def shape_cases() -> list[tuple[str, dict[str, Any]]]:
    """Rows for the shape template: every literal kind and truth value through its positions."""
    base = {
        "id": "1",
        "a": "A",
        "b": "B",
        "flag": True,
        "n": 3,
        "x": 0,
        "y": "",
        "outer": [],
        "d": {},
        "attrs": {"data-shape": "s"},
    }
    cases: list[tuple[str, dict[str, Any]]] = []
    values: list[object] = [None, True, False, 0, -1, 2**53, 1.5, "", "\u00e9\u2028<"]
    for index, value in enumerate(values):
        for flag in (True, None, "s", 2.5):
            cases.append(
                (f"value[{index}] flag={flag!r}", {"v": dict(base, a=value, b=f"b{index}", flag=flag, n=value)})
            )
    for x, y in itertools.product((0, "x", [], [0], {}, {"k": 1}, None), (0, 1, "", [0], None)):
        cases.append((f"x={x!r} y={y!r}", {"v": dict(base, x=x, y=y)}))
    for d in ({}, {"a": 1}, "", "s", [], [1], 0.0, 3):
        cases.append((f"d={d!r}", {"v": dict(base, d=d)}))
    for attrs in ({}, None, {"id": "x", "data-n": 2, "data-off": False, "data-on": True}):
        cases.append((f"attrs={attrs!r}", {"v": dict(base, attrs=attrs)}))
    outer = [
        [],
        [{"k": "k1", "inner": []}],
        [{"k": "k1", "inner": [1, "two", None, 3.25, True]}, {"k": 2**60, "inner": [False]}],
        [{"k": None, "inner": ["a<b"]}, {"k": False, "inner": []}, {"k": "", "inner": [""]}],
    ]
    for index, item in enumerate(outer):
        cases.append((f"outer[{index}]", {"v": dict(base, outer=item)}))
    return cases


# Call-run keys that stress the JSON string writer and the digests: quotes,
# backslashes, `<`, control characters, non-ASCII and astral text.
EDGE_KEYS = ["", "output-1", 'q"uote\\back', "tags <b>&", "ctl \x00\x1f\x7f", "caf\u00e9", "\u2028", "\U0001f600"]


def digest_cases() -> dict[str, Any]:
    """Call-run row ids observed from Python's ``_DigestPrefix``, for the Rust digest test."""
    sites = [
        ((BOARD_ROW_TEMPLATE, 120, 260, "app.ProjectOutput_1a2b3c"), ("citryRoute", 3)),
        (('<c-Row c-for="r in rows" />\n\u00e9 \U0001f600 <b>', 0, 9, "x"), ()),
    ]
    occurrence = "citryOccurrence0123456789abcdef01234567"
    cases = []
    child = _DigestPrefix(occurrence)
    for member_base, route in sites:
        placement = _DigestPrefix(member_base, route)
        for key in EDGE_KEYS:
            placement_key = f"citryPlacement{placement.digest(('explicit', key))[:24]}"
            cases.append(
                {
                    "placement_prefix": _DIGEST_JSON.encode((member_base, route))[:-1],
                    "child_prefix": _DIGEST_JSON.encode((occurrence,))[:-1],
                    "key": key,
                    "placement_key": placement_key,
                    "child_id": f"citryOccurrence{child.digest(placement_key)[:24]}",
                }
            )
    return {"cases": cases}


def run_case(
    member_base: tuple[object, ...],
    route: tuple[object, ...],
    type_key: str,
    definition_id: str,
    rows: list[tuple[str, str, dict[str, Any]]],
) -> dict[str, Any]:
    """One call run's rows and what Python makes of them, for the Rust run test."""
    parent_id = "citryOccurrence0123456789abcdef01234567"
    placement = _DigestPrefix(member_base, route)
    child = _DigestPrefix(parent_id)
    expected_ids = []
    expected_items = []
    first_repeat = None
    seen: set[str] = set()
    for index, (key, render_id, prepared) in enumerate(rows):
        if key in seen and first_repeat is None:
            first_repeat = index
        seen.add(key)
        placement_key = f"citryPlacement{placement.digest(('explicit', key))[:24]}"
        child_id = f"citryOccurrence{child.digest(placement_key)[:24]}"
        expected_ids.append([placement_key, child_id])
        # The item prepared_manifest builds, plus the renderId that
        # _prepare_holding_assets adds to every occurrence.
        item = {
            "id": child_id,
            "typeKey": type_key,
            "definitionId": definition_id,
            "serverData": {},
            "preparedData": prepared,
            "parentId": parent_id,
            "placementKey": placement_key,
            "renderId": render_id,
        }
        expected_items.append(_script_json(item))
    return {
        "placement_prefix": _DIGEST_JSON.encode((member_base, route))[:-1],
        "child_prefix": _DIGEST_JSON.encode((parent_id,))[:-1],
        "parent_id": parent_id,
        "type_key": type_key,
        "definition_id": definition_id,
        "keys": [key for key, _, _ in rows],
        "render_ids": [render_id for _, render_id, _ in rows],
        "prepared_json": [_script_json(prepared) for _, _, prepared in rows],
        "expected_ids": expected_ids,
        "expected_items": expected_items,
        "first_repeat": first_repeat,
    }


def run_cases() -> dict[str, Any]:
    """Whole call runs observed from Python, for the Rust run test."""
    return {
        "cases": [
            # The board's shape: one call site, ordinary keys and data.
            run_case(
                (BOARD_ROW_TEMPLATE, 120, 260, "app.ProjectOutput_1a2b3c"),
                (),
                "app.ProjectOutput_1a2b3c",
                "citryDefinitiona1b2c3",
                [
                    (f"output-{index}", f"r{index}", {"calls": {}, "row": {"id": index, "title": f"T {index}"}})
                    for index in range(6)
                ],
            ),
            # Keys, render ids, type keys and data that need escapes,
            # including non-ASCII and astral text and `<`.
            run_case(
                ('<c-Row c-for="r in rows" />\n\u00e9 \U0001f600 <b>', 0, 9, "x"),
                ("citryRoute", 3),
                "x.Row_\u00e9",
                "citryDefinition<\u2028>",
                [(key, f"id {key}", {"calls": {}, "t": key, "n": None, "b": True, "f": 1.5}) for key in EDGE_KEYS],
            ),
            # A repeated key at index 3.
            run_case(
                ("<c-Row />", 1, 2, "t"),
                (),
                "t",
                "d",
                [(key, f"r{index}", {"calls": {}}) for index, key in enumerate(["a", "b", "c", "a", "b"])],
            ),
        ]
    }


def _walk_rows(count: int) -> list[dict[str, Any]]:
    return [{"id": f"r{index}", "n": index, "title": f"row {index}", "tags": ["a", "b"]} for index in range(count)]


# Each loop case: (name, scope, loop clause, inputs as (kwarg name,
# expression), key expression, the reason Rust must decline or None).
WALK_CASES: list[tuple[str, dict[str, Any], str, list[tuple[str, str]], str, str | None]] = [
    ("board", {"phase": {"outputs": _walk_rows(4)}}, "row in phase['outputs']", [("row", "row")], "row['id']", None),
    ("int_keys", {"rows": _walk_rows(3)}, "row in rows", [("row", "row")], "row['n']", None),
    (
        "int_edges",
        {"rows": [{"n": 0}, {"n": -5}, {"n": 2**63 - 1}, {"n": -(2**63)}]},
        "row in rows",
        [("row", "row")],
        "row['n']",
        None,
    ),
    ("int_beyond_i64", {"rows": [{"n": 2**63}]}, "row in rows", [("row", "row")], "row['n']", "key_type"),
    ("bool_key", {"rows": [{"k": True}]}, "row in rows", [("row", "row")], "row['k']", "key_type"),
    ("none_key", {"rows": [{"k": None}]}, "row in rows", [("row", "row")], "row['k']", "key_type"),
    ("float_key", {"rows": [{"k": 1.5}]}, "row in rows", [("row", "row")], "row['k']", "key_type"),
    ("dict_key", {"rows": [{"k": {"x": 1}}]}, "row in rows", [("row", "row")], "row['k']", "key_type"),
    (
        "missing_key_row2",
        {"rows": [*_walk_rows(2), {"title": "no id"}, *_walk_rows(1)]},
        "row in rows",
        [("row", "row")],
        "row['id']",
        "missing",
    ),
    ("iterable_dict", {"rows": {"a": 1, "b": 2}}, "row in rows", [("row", "row")], "row", "iterable"),
    ("iterable_str", {"rows": "abc"}, "row in rows", [("row", "row")], "row", "iterable"),
    ("iterable_missing", {"other": []}, "row in rows", [("row", "row")], "row", "missing"),
    (
        "nested_index",
        {"groups": [_walk_rows(1), _walk_rows(3)]},
        "row in groups[1]",
        [("row", "row")],
        "row['id']",
        None,
    ),
    ("index_past_end", {"groups": [_walk_rows(1)]}, "row in groups[5]", [("row", "row")], "row['id']", "missing"),
    ("list_by_str", {"rows": [["x"], ["y"]]}, "row in rows", [("row", "row")], "row['id']", "not_plain"),
    ("str_by_str", {"rows": _walk_rows(2)}, "row in rows", [("v", "row['id']['x']")], "row['id']", "not_plain"),
    ("str_by_int", {"rows": _walk_rows(2)}, "row in rows", [("v", "row['id'][0]")], "row['id']", "not_plain"),
    (
        "scope_input",
        {"phase": {"name": "p", "outputs": _walk_rows(2)}},
        "row in phase['outputs']",
        [("row", "row"), ("phase", "phase"), ("label", "phase['name']")],
        "row['id']",
        None,
    ),
    ("empty", {"rows": []}, "row in rows", [("row", "row")], "row['id']", None),
    ("list_rows", {"rows": [["k0", 1], ["k1", 2]]}, "row in rows", [("count", "row[1]")], "row[0]", None),
    (
        "deep",
        {"a": {"b": [{"c": _walk_rows(2)}]}},
        "row in a['b'][0]['c']",
        [("tags", "row['tags']")],
        "row['id']",
        None,
    ),
    ("str_rows", {"rows": ["x", "y", "x2"]}, "row in rows", [("label", "row")], "row", None),
    ("missing_scope_input", {"rows": _walk_rows(2)}, "row in rows", [("p", "page")], "row['id']", "missing"),
    ("no_inputs", {"rows": _walk_rows(2)}, "row in rows", [], "row['id']", None),
]


def _walk_path(expr: str) -> dict[str, Any]:
    """Lower one expression as ``ForNode`` does, written as the fixture spells a path."""
    lowered = lower_path(expr)
    if lowered is None:
        raise SystemExit(f"the lowering refused {expr!r}")
    return _walk_path_json(lowered)


def _walk_path_json(lowered: tuple[str, tuple[str | int, ...]]) -> dict[str, Any]:
    name, steps = lowered
    return {"name": name, "steps": [{"str": step} if type(step) is str else {"int": step} for step in steps]}


def _python_walk(scope: dict[str, Any], target: str, clause: str, inputs: list[tuple[str, str]], key: str) -> Any:
    """Evaluate the loop as Python's walk does; return each row's values, or the error's type name."""
    variables = _ConstMapping(scope)
    try:
        # The iterable once, then per row each input and the key, each over
        # the row's own scope (the loop variable added to a copy).
        items = list(compile_expr(f"(({target},) for {clause})", sandboxed=True)(variables))
        rows = []
        for (item,) in items:
            row_scope = _overlay_const_mapping(variables, {target: item})
            values = [compile_expr(expr, sandboxed=True)(row_scope) for _name, expr in inputs]
            # The key as ComponentNode turns it into the call's key: None
            # stays None, anything else becomes its str().
            key_value = const_value(compile_expr(key, sandboxed=True)(row_scope))
            rows.append({"kwargs": values, "key": None if key_value is None else str(key_value)})
    except Exception as error:  # noqa: BLE001 - the failure is the recorded result
        return type(error).__name__
    return rows


def walk_cases() -> dict[str, Any]:
    """The loop cases for the Rust walk test, evaluated by Python's sandboxed evaluator."""
    cases = []
    for name, scope, clause, inputs, key, decline in WALK_CASES:
        target = clause.split(" in ", 1)[0].strip()
        loop = lower_loop((target,), clause)
        if loop is None:
            raise SystemExit(f"the lowering refused the loop {clause!r}")
        python = _python_walk(scope, target, clause, inputs, key)
        # A case that expects Rust to read the rows must be one Python reads.
        if decline is None and not isinstance(python, list):
            raise SystemExit(f"{name}: Python raised {python}, but the case expects Rust to read the rows")
        cases.append(
            {
                "name": name,
                "scope": scope,
                "spec": {
                    "target": loop[0],
                    "iterable": _walk_path_json(loop[1]),
                    "kwargs": [_walk_path(expr) for _name, expr in inputs],
                    "key": _walk_path(key),
                },
                "decline": decline,
                "python": python,
            }
        )
    return {"cases": cases}


def encoded(fixture: dict[str, Any]) -> str:
    """Write a fixture as JSON with one row or case per line, so a change reads as a short diff."""
    entries_key = "rows" if "rows" in fixture else "cases"
    head = {key: value for key, value in fixture.items() if key != entries_key}
    lines = [json.dumps(entry, ensure_ascii=True, separators=(",", ":")) for entry in fixture[entries_key]]
    head_text = json.dumps(head, ensure_ascii=True, separators=(",", ":"))[:-1]
    separator = "," if head else ""
    return head_text + f'{separator}"{entries_key}":[\n' + ",\n".join(lines) + "\n]}\n"


def fixtures() -> dict[str, str]:
    """Compute every fixture file's text from the current Python code."""
    rng = random.Random(SEED)  # noqa: S311 - reproducible test data, not security
    board = [(f"board row {index}", board_variables(rng, index)) for index in range(BOARD_ROWS)]
    # The edge rows start from a row with both loops filled.
    base = next(
        variables
        for _label, variables in board
        if variables["row"]["dependencies"] and variables["row"]["attachments"]
    )
    return {
        "board_rows.json": encoded(fixture_for(row_node(BOARD_ROW_TEMPLATE), board + edge_rows(base, rng))),
        "shapes.json": encoded(fixture_for(row_node(SHAPE_TEMPLATE), shape_cases())),
        "run_digests.json": encoded(digest_cases()),
        "run_items.json": encoded(run_cases()),
        "walk_rows.json": encoded(walk_cases()),
    }


def check() -> list[str]:
    """Return the fixture files whose committed text differs from what the current Python code writes."""
    return [
        name
        for name, text in fixtures().items()
        if not (FIXTURES / name).exists() or (FIXTURES / name).read_text(encoding="utf-8") != text
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] if __doc__ else None)
    parser.add_argument("--check", action="store_true", help="compare the committed fixtures instead of writing them")
    args = parser.parse_args(argv)
    if args.check:
        stale = check()
        for name in stale:
            path = FIXTURES.relative_to(ROOT) / name
            print(f"{path} differs from Python's output; rerun scripts/native_render_fixtures.py")  # noqa: T201
        return 1 if stale else 0
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, text in fixtures().items():
        (FIXTURES / name).write_text(text, encoding="utf-8")
        print(f"wrote {FIXTURES.relative_to(ROOT) / name}")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
