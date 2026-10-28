"""
The native render path leaves a template nested past its depth limits to Python.

Rust builds a plan for a ``simple = "vue"`` template, then evaluates it and
writes each row's data, with code that calls itself once per nesting level.
That work reads Python objects, so it cannot move to a stack taken from the
heap. Rust therefore refuses a template nested past two limits
(``NATIVE_RENDER_MAX_BODY_DEPTH`` for the ``c-if`` and ``c-for`` bodies and
conditional expressions, and ``NATIVE_RENDER_MAX_READ_DEPTH`` for the paths a
template reads), and Python's evaluator renders it. Each build has its own
limits, because a debug build's stack frames are several times larger, so
every test reads the active limit from ``citry_core._rust`` rather than
copying it.

The first tests check the refusal and the rendering in this process. The last
ones render on a fresh 128 KiB thread (the default thread stack on musl
Linux) in a separate interpreter, so a crash fails one test rather than the
run. Those cost an interpreter start each, so CI runs them in one Linux cell
(``CITRY_NATIVE_DEPTH_PROBES=1``), while a local run always does, which checks
a developer's debug build too.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import textwrap
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue import native_render
from citry_core import _rust

from ._render_paths import render_both

BODY_LIMIT: int = _rust.NATIVE_RENDER_MAX_BODY_DEPTH
READ_LIMIT: int = _rust.NATIVE_RENDER_MAX_READ_DEPTH

# A top-level `{{ n }}` is level 2 (the top level, then its expression), and
# each loop or `c-if` around it adds one, so the deepest chain is two short.
DEEPEST_CHAIN = BODY_LIMIT - 2
# The variable is level 1 and each subscript adds one.
DEEPEST_PATH = READ_LIMIT - 1

needs_native = pytest.mark.skipif(not native_render.SUPPORTED, reason="this interpreter takes the Python render path")


# ---------------------------------------------------------------------------
# The plan refuses past the limits.
# ---------------------------------------------------------------------------

_JS_SAFE_INTEGER = 2**53 - 1


def _row_plan(ops: tuple[object, ...], roots: tuple[object, ...], loop_targets: tuple[str, ...]) -> object:
    # The same five arguments `native_row_plan_tuples` passes.
    return native_render.native._RowPlan(ops, roots, loop_targets, 16, _JS_SAFE_INTEGER)


def _loop_chain_plan(loops: int) -> object:
    ops: tuple[object, ...] = (("text", "t", ("p", "n", ())),)
    items: tuple[object, ...] = ((), (), None)
    targets = []
    for level in reversed(range(loops)):
        iterable = ("p", "rows", ()) if level == 0 else ("p", f"r{level - 1}", ())
        ops = (("for", f"f{level}", f"r{level}", iterable, ops, ()),)
        items = (("list",), (), items)
        targets.append(f"r{level}")
    return _row_plan(ops, (("n", (("scalar",), (), None)), ("rows", items)), tuple(targets))


def _if_chain_plan(levels: int) -> object:
    ops: tuple[object, ...] = (("text", "t", ("p", "n", ())),)
    for level in range(levels):
        ops = (("if", f"i{level}", ((("p", "flag", ()), ops),)),)
    return _row_plan(ops, (("flag", (("truth",), (), None)), ("n", (("scalar",), (), None))), ())


def _conditional_plan(levels: int) -> object:
    expr: tuple[object, ...] = ("p", "n", ())
    for _ in range(levels):
        expr = ("i", ("p", "flag", ()), ("p", "n", ()), expr)
    ops = (("text", "t", expr),)
    return _row_plan(ops, (("flag", (("truth",), (), None)), ("n", (("scalar",), (), None))), ())


def _path_plan(keys: int) -> object:
    node: tuple[object, ...] = (("scalar",), (), None)
    for _ in range(keys):
        node = ((), (("k", node),), None)
    ops = (("text", "t", ("p", "a", ("k",) * keys)),)
    return _row_plan(ops, (("a", node),), ())


def _loops_with_path_plan(loops: int, keys: int) -> object:
    """`{{ rN['k']... }}` with `keys` subscripts inside `loops` nested loops."""
    leaf: tuple[object, ...] = (("scalar",), (), None)
    for _ in range(keys):
        leaf = ((), (("k", leaf),), None)
    innermost = f"r{loops - 1}"
    ops: tuple[object, ...] = (("text", "t", ("p", innermost, ("k",) * keys)),)
    items = leaf
    targets = []
    for level in reversed(range(loops)):
        iterable = ("p", "rows", ()) if level == 0 else ("p", f"r{level - 1}", ())
        ops = (("for", f"f{level}", f"r{level}", iterable, ops, ()),)
        items = (("list",), (), items)
        targets.append(f"r{level}")
    return _row_plan(ops, (("rows", items),), tuple(targets))


# Loop items and subscripts both add a read level: the list `rows` is level 1,
# each loop's item one more, and each subscript one more.
_LOOPS_WITH_PATH = min(3, DEEPEST_CHAIN)


def _loops_with_path(keys: int) -> object:
    return _loops_with_path_plan(_LOOPS_WITH_PATH, keys)


@needs_native
@pytest.mark.parametrize(
    ("build", "deepest"),
    [
        (_loop_chain_plan, DEEPEST_CHAIN),
        (_if_chain_plan, DEEPEST_CHAIN),
        (_conditional_plan, DEEPEST_CHAIN),
        (_path_plan, DEEPEST_PATH),
        (_loops_with_path, READ_LIMIT - 1 - _LOOPS_WITH_PATH),
    ],
    ids=["loops", "ifs", "conditionals", "path", "loops-and-path"],
)
def test_rust_plans_up_to_each_limit_and_refuses_one_past_it(build: Any, deepest: int) -> None:
    build(deepest)
    with pytest.raises(ValueError, match=r"^too_deep: ") as raised:
        build(deepest + 1)
    # The message names the limit, which the debug log repeats.
    limit = READ_LIMIT if build in {_path_plan, _loops_with_path} else BODY_LIMIT
    assert f"more than {limit} levels deep" in str(raised.value)


# ---------------------------------------------------------------------------
# Rendering at and past the limits, in this process.
# ---------------------------------------------------------------------------


def _loop_chain(loops: int) -> tuple[str, dict[str, object]]:
    """`{{ n }}` inside `loops` nested loops, each over the item of the loop around it."""
    names = ["rows"] + [f"r{level}" for level in range(loops)]
    opening = "".join(f'<div c-for="{names[level + 1]} in {names[level]}">' for level in range(loops))
    data: object = [1]
    for _ in range(loops - 1):
        data = [data]
    return opening + "{{ n }}" + "</div>" * loops, {"n": 7, "rows": data}


def _deep_component(template: str, data: dict[str, object]) -> type[Component]:
    engine = Citry(autodiscover=False)

    def template_data(_kwargs: object, _slots: object) -> dict[str, object]:
        return data

    return type(
        "Deep",
        (Component,),
        {
            "citry": engine,
            "simple": "vue",
            "template": template,
            "template_data": staticmethod(template_data),
            "js": "$component({});",
        },
    )


@needs_native
def test_a_template_at_the_limit_renders_natively(monkeypatch: pytest.MonkeyPatch) -> None:
    deep = _deep_component(*_loop_chain(DEEPEST_CHAIN))
    render_both(lambda: deep().render().serialize(), monkeypatch, rows_read=1)


@needs_native
def test_a_template_past_the_limit_renders_in_python_with_the_same_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deep = _deep_component(*_loop_chain(DEEPEST_CHAIN + 1))
    render_both(lambda: deep().render().serialize(), monkeypatch, rows_read=0)


@needs_native
def test_a_template_past_the_limit_is_logged_once_at_debug_level(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The plan is only built on the native path, which a run with
    # `--python-render-path` turns off.
    monkeypatch.setattr(native_render, "ACTIVE", True)
    deep = _deep_component(*_loop_chain(DEEPEST_CHAIN + 1))
    with caplog.at_level(logging.DEBUG, logger="citry"):
        deep().render().serialize()
        deep().render().serialize()
    messages = [record.getMessage() for record in caplog.records if "with its Python path" in record.getMessage()]
    assert len(messages) == 1
    # The message names the component, so its author can find it.
    assert "component Deep " in messages[0]
    assert f"more than {BODY_LIMIT} levels deep" in messages[0]


# ---------------------------------------------------------------------------
# Rendering on a small thread, in a separate interpreter.
# ---------------------------------------------------------------------------

_ON_CI = os.environ.get("GITHUB_ACTIONS") == "true"
needs_probe_cell = pytest.mark.skipif(
    _ON_CI and os.environ.get("CITRY_NATIVE_DEPTH_PROBES") != "1",
    reason="CI renders on small threads in one Linux cell only",
)

# Renders one deep template twice: on the main thread through Python's
# evaluator, which also compiles it, and then on a fresh 128 KiB thread on the
# native path, where Rust builds the row plan for the first time. Render ids
# are pinned, so the two outputs compare byte for byte. Each render writes the
# hydrated and the static output, and both rebuild the Rust-read row in Python
# (`NativeRow.snapshot()`); the thread then collects garbage.
_HARNESS = """
import gc
import itertools
import json
import sys
import threading

from citry import Citry, Component
from citry._vue import native_render
from citry._vue.leaf_program import LeafProgramNode

template, data = json.loads(sys.argv[1])
engine = Citry(autodiscover=False)

def template_data(_kwargs, _slots):
    return data

Deep = type(
    "Deep",
    (Component,),
    {
        "citry": engine,
        "simple": "vue",
        "template": template,
        "template_data": staticmethod(template_data),
        "js": "$component({});",
    },
)

def pin():
    import citry.component
    import citry.component_render
    import citry._vue.serialization
    ids = itertools.count(1)
    citry.component.gen_render_id = lambda: f"c{next(ids)}"
    citry.component_render.gen_render_id = lambda: f"c{next(ids)}"
    app_ids = itertools.count()
    citry._vue.serialization.token_hex = lambda _size: f"{next(app_ids):032x}"

rows_read = 0
read_native_row = LeafProgramNode.read_native_row

def counting_read(self, variables):
    global rows_read
    row = read_native_row(self, variables)
    rows_read += row is not None
    return row

LeafProgramNode.read_native_row = counting_read

def render_all():
    pin()
    hydrated = Deep().render().serialize()
    pin()
    static = Deep().render().serialize(deps_strategy="simple")
    return hydrated, static

native_render.ACTIVE = False
python_outputs = render_all()

native_render.ACTIVE = True
result = {}

def on_small_thread():
    result["outputs"] = render_all()
    gc.collect()

threading.stack_size(128 * 1024)
thread = threading.Thread(target=on_small_thread)
thread.start()
thread.join()
print(json.dumps({"same": list(result["outputs"]) == list(python_outputs), "rows_read": rows_read}))
"""


def _render_on_small_thread(template: str, data: dict[str, object]) -> dict[str, object]:
    env = {**os.environ, "CITRY_NATIVE_RENDER": "1"}
    completed = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(_HARNESS), json.dumps([template, data])],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=300,
    )
    # A stack overflow ends the interpreter: a negative code (SIGSEGV or
    # SIGBUS) on POSIX, 0xC00000FD on Windows.
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _if_chain(levels: int) -> tuple[str, dict[str, object]]:
    return '<div c-if="flag">' * levels + "{{ n }}" + "</div>" * levels, {"n": 7, "flag": True}


def _deep_path(keys: int) -> tuple[str, dict[str, object]]:
    value: object = 7
    for _ in range(keys):
        value = {"k": value}
    return "<div>{{ a" + "['k']" * keys + " }}</div>", {"a": value}


@needs_native
@needs_probe_cell
@pytest.mark.parametrize(
    ("shape", "deepest"),
    [(_loop_chain, DEEPEST_CHAIN), (_if_chain, DEEPEST_CHAIN), (_deep_path, DEEPEST_PATH)],
    ids=["loops", "ifs", "path"],
)
def test_a_small_thread_renders_at_and_one_past_the_limit(shape: Any, deepest: int) -> None:
    # The thread renders twice (the hydrated and the static output), one row
    # each, so Rust reads two rows at the limit and none past it.
    at_limit = _render_on_small_thread(*shape(deepest))
    assert at_limit == {"same": True, "rows_read": 2}
    past_limit = _render_on_small_thread(*shape(deepest + 1))
    assert past_limit == {"same": True, "rows_read": 0}


@needs_native
@needs_probe_cell
def test_the_reproduction_from_issue_422_renders_on_a_small_thread() -> None:
    # 100 nested loops crashed a debug build on a 512 KiB thread. Both
    # builds' limits are below 100, so Python renders it, here on a smaller
    # thread.
    assert _render_on_small_thread(*_loop_chain(100)) == {"same": True, "rows_read": 0}


@needs_native
@needs_probe_cell
def test_a_shallow_template_still_renders_natively_on_a_small_thread() -> None:
    assert _render_on_small_thread(*_loop_chain(2)) == {"same": True, "rows_read": 2}
