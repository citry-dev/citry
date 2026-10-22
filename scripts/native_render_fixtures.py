"""
Write the test fixtures of ``crates/citry_native_render`` from Citry's own Python code.

The Rust crate evaluates ``simple = "vue"`` row templates and hashes call-run
ids without any Python, so its tests compare it with answers observed from
Python. This script produces those answers:

- ``board_rows.json`` and ``shapes.json``: a template's plan (the tuples
  ``native_row_plan_tuples`` passes to Rust), and for each row its variables
  (with each value's Python type spelled out), the root ``c-bind`` layout
  Python gives its key set, and the prepared-data JSON Citry's Python
  evaluator and assembly write;
- ``run_digests.json``: call-run row ids computed by Python's ``_DigestPrefix``.

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
from citry._vue.serialization import _script_json
from citry.component_render import _simple_vue_admission

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "crates" / "citry_native_render" / "tests" / "fixtures"

# The project board's row template (the benchmark page's `ProjectOutput`),
# copied here so the fixtures do not change when the benchmark app does.
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

# A template for the shapes the board does not use: literal texts, a
# conditional expression, c-if/c-elif with no match, literal and boolean
# attributes, nested loops reading the outer loop's item, and truth tests on
# dicts and strings. Every piece is admitted by simple='vue' (c-empty is not).
SHAPE_TEMPLATE = """
<div class="shape">
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

BOARD_ROWS = 20
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


def fixture_for(node: LeafProgramNode, cases: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    """Describe the node's plan and, for each row Python accepts, the JSON Python writes for it."""
    tuples = native_row_plan_tuples(node)
    if tuples is None:
        msg = "the fixture template has no Rust plan"
        raise TypeError(msg)
    ops, roots, loop_targets, _spread_limit = tuples
    # The layout callbacks and the variable each spread reads, in spread order.
    spreads = [
        (cast("Callable[[tuple[str, ...]], Any]", op[3]), cast("tuple[str, ...]", op[2])[1])
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
        entries = [layout(tuple(variables[root] or ())) for layout, root in spreads]
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
        "plan": {"ops": described(ops), "roots": described(roots), "loop_targets": list(loop_targets)},
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
    floats += [finite_float(rng) for _ in range(6)]
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
    base = {"id": "1", "a": "A", "b": "B", "flag": True, "n": 3, "x": 0, "y": "", "outer": [], "d": {}}
    cases: list[tuple[str, dict[str, Any]]] = []
    values: list[object] = [None, True, False, 0, 7, -1, 2**53, 1.5, -0.0, "", "x", "\u00e9\u2028<"]
    for index, value in enumerate(values):
        for flag in (True, None, "s", 2.5):
            cases.append(
                (f"value[{index}] flag={flag!r}", {"v": dict(base, a=value, b=f"b{index}", flag=flag, n=value)})
            )
    for x, y in itertools.product((0, 1, "", "x", [], [0], {}, {"k": 1}, None), repeat=2):
        cases.append((f"x={x!r} y={y!r}", {"v": dict(base, x=x, y=y)}))
    for d in ({}, {"a": 1}, "", "s", [], [1], 0.0, 3):
        cases.append((f"d={d!r}", {"v": dict(base, d=d)}))
    outer = [
        [],
        [{"k": "k1", "inner": []}],
        [{"k": "k1", "inner": [1, "two", None, 3.25, True]}, {"k": 2**60, "inner": [False]}],
        [{"k": None, "inner": ["a<b"]}, {"k": False, "inner": []}, {"k": "", "inner": [""]}],
    ]
    for index, item in enumerate(outer):
        cases.append((f"outer[{index}]", {"v": dict(base, outer=item)}))
    return cases


def digest_cases() -> dict[str, Any]:
    """Call-run row ids observed from Python's ``_DigestPrefix``, for the Rust digest test."""
    sites = [
        ((BOARD_ROW_TEMPLATE, 120, 260, "app.ProjectOutput_1a2b3c"), ("citryRoute", 3)),
        (('<c-Row c-for="r in rows" />\n\u00e9 \U0001f600 <b>', 0, 9, "x"), ()),
    ]
    occurrence = "citryOccurrence0123456789abcdef01234567"
    keys = ["", "output-1", 'q"uote\\back', "tags <b>&", "ctl \x00\x1f\x7f", "caf\u00e9", "\u2028", "\U0001f600"]
    cases = []
    child = _DigestPrefix(occurrence)
    for member_base, route in sites:
        placement = _DigestPrefix(member_base, route)
        for key in keys:
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
