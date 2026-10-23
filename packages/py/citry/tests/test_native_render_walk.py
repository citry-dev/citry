"""
Level C2 of the native render path: Rust walks a call run's loop and reads each row's inputs.

A call run is the rows one ``<c-for>`` places at one component call site.
When the loop's iterable, the call's inputs and its ``#c-key`` are plain
paths (a name and constant subscripts), ``ForNode._walk_call_run`` asks Rust
to read every row and build each row's kwargs dict and call metadata, in
place of Python's walk (``ForNode._render_call_run``). Anything Rust cannot
read exactly as Python does makes it decline, and Python's walk then runs the
loop from the start and raises its own errors.

This file checks:

- page cases on both paths in this process (``render_both`` in
  ``tests/_render_paths.py``), comparing the bytes or the error and the
  callbacks' calls, with the loops Rust walked and the reason of each loop
  it left to Python, so a silent decline cannot pass. There is one case for
  each decline reason a page can reach;
- that on the 140-row board Rust walks all five loops and records exactly
  what Python's walk records, object for object;
- the lowering (``citry._vue.native_walk``), which needs no Rust;
- the binding directly, for the reads and failures no page reaches.
"""

from __future__ import annotations

import gc
import logging
import sys
import weakref
from contextlib import contextmanager
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import pytest

from citry import Citry, Component, Const
from citry._vue import native_render
from citry._vue.native_walk import lower_loop, lower_path
from citry.citry_element import _PreparedCallMetadata
from citry.citry_render import _DeferredRunRow
from citry.constness import _ConstMapping, _ConstProxy
from citry.extension import Extension
from citry.nodes import ForNode
from citry.util.logger import _ensure_trace_level, logger
from citry_core.safe_eval import compile_expr

from . import test_call_run_order as order
from ._render_paths import render_both, run_on_path
from .test_native_render_rows import build_board, make_rows

if TYPE_CHECKING:
    from collections.abc import Iterator

# ---------------------------------------------------------------------------
# Page cases
# ---------------------------------------------------------------------------

_RUN_LINE = """<c-Row c-for="row in rows" #c-key="row['key']" c-row="row" />"""

# The list component's template for the cases that change the loop; every
# other case renders _RUN_LINE.
_LIST_TEMPLATES = {
    "filtered": """<c-for each="row in rows if row['key']"><c-Row #c-key="row['key']" c-row="row" /></c-for>""",
    "multi_target": """<c-Row c-for="index, row in rows" #c-key="row['key']" c-row="row" />""",
    "slice_iterable": """<c-Row c-for="row in rows[1:]" #c-key="row['key']" c-row="row" />""",
    "private_key": """<c-Row c-for="row in rows" #c-key="row['_key']" c-row="row" />""",
    "surrogate_key": """<c-Row c-for="row in rows" #c-key="row['\\ud800']" c-row="row" />""",
    "static_input": """<c-Row c-for="row in rows" #c-key="row['key']" c-row="row" label="fixed" />""",
    "call_input": """<c-Row c-for="row in rows" #c-key="row['key']" c-row="row" c-label="row['key'].upper()" />""",
    "scope_input": """<c-Row c-for="row in rows" #c-key="row['key']" c-row="row" c-label="title" />""",
    "const_input": """<c-Row c-for="row in rows" #c-key="row['key']" c-row="row" c-label="title" />""",
    "missing_scope_input": """<c-Row c-for="row in rows" #c-key="row['key']" c-row="row" c-label="page" />""",
    "int_keys": """<c-Row c-for="row in rows" #c-key="row['n']" c-row="row" />""",
    "extreme_int_keys": """<c-Row c-for="row in rows" #c-key="row['n']" c-row="row" />""",
    "int_beyond_i64": """<c-Row c-for="row in rows" #c-key="row['n']" c-row="row" />""",
    "bool_keys": """<c-Row c-for="row in rows" #c-key="row['n']" c-row="row" />""",
    "none_key": """<c-Row c-for="row in rows" #c-key="row['n']" c-row="row" />""",
    "list_rows": """<c-Row c-for="row in rows" #c-key="row[0]" c-row="row[1]" />""",
    "mixed_rows": """<c-Row c-for="row in rows" #c-key="row[0]" c-row="row[1]" />""",
    "bool_keyed_rows": """<c-Row c-for="row in rows" #c-key="row[1]" c-row="row['row']" />""",
    "list_by_str": """<c-Row c-for="row in rows" #c-key="row['key']" c-row="row" />""",
    "nested_path": """<c-Row c-for="row in rows['groups'][0]" #c-key="row['key']" c-row="row" />""",
}


def _rows(count: int) -> list[dict[str, Any]]:
    return [{"key": f"a{index}", "title": f"row {index}"} for index in range(count)]


class _Text(dict):  # type: ignore[type-arg]
    """A dict subclass, which the walk does not read as plain data."""


class _RaisingKey:
    """
    A dict key whose hash equals ``"key"``'s, so looking ``"key"`` up runs this ``__eq__``.

    It raises once armed; it is armed after the dict holding it is built,
    because building the dict compares the keys too.
    """

    def __init__(self) -> None:
        self.armed = False

    def __hash__(self) -> int:
        return hash("key")

    def __eq__(self, other: object) -> bool:
        if self.armed:
            raise ValueError("the key compare failed")
        return False


def _case_rows(case: str) -> Any:
    """The ``rows`` value the page passes to its list component for ``case``."""
    rows: Any = _rows(4)
    if case == "tuple_rows":
        rows = tuple(rows)
    elif case == "generator":
        rows = (row for row in _rows(4))
    elif case == "dict_iterable":
        rows = {"a": 1, "b": 2}
    elif case in {"int_keys", "extreme_int_keys", "int_beyond_i64", "bool_keys", "none_key"}:
        values = {
            "int_keys": [0, 1, 2],
            "extreme_int_keys": [-(2**63), -5, 2**63 - 1],
            "int_beyond_i64": [1, 2**63],
            "bool_keys": [True, False],
            "none_key": [1, None],
        }[case]
        rows = [{"n": value, "title": f"row {value}"} for value in values]
    elif case == "list_rows":
        rows = [[f"k{index}", {"title": f"row {index}"}] for index in range(3)]
    elif case == "mixed_rows":
        rows = [("k0", {"title": "tuple row"}), ["k1", {"title": "list row"}]]
    elif case == "bool_keyed_rows":
        rows = [{True: f"k{index}", "row": {"title": f"row {index}"}} for index in range(3)]
    elif case == "list_by_str":
        rows = [["x"], ["y"]]
    elif case == "nested_path":
        rows = {"groups": [_rows(3)]}
    elif case in {"missing_key", "unsandboxed_missing"}:
        del rows[2]["key"]
    elif case == "dict_subclass_row":
        rows[1] = _Text(rows[1])
    elif case == "marker_row":
        rows = [Const(row) for row in rows]
    elif case == "marker_inside_row":
        rows = [{**row, "extra": Const([1, 2])} for row in rows]
    elif case == "read_raised":
        raising = _RaisingKey()
        rows[1] = {raising: 1, **rows[1]}
        raising.armed = True
    elif case == "empty":
        rows = []
    return rows


@contextmanager
def _collecting_trace(log: list[str], *, enabled: bool) -> Iterator[None]:
    """Turn Citry's TRACE logging on while the block runs, adding its lines to ``log``, when ``enabled``."""
    if not enabled:
        yield
        return

    class Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            log.append(record.getMessage())

    handler = Collect(level=1)
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(_ensure_trace_level())
    try:
        yield
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


class _PlainScope(Extension):
    """Replace a component's template variables with a plain dict, which the walk does not read."""

    name = "native_walk_plain_scope"

    def on_component_data(self, ctx: Any) -> None:
        ctx.context.variables = dict(ctx.context.variables)


def _engine_class(case: str, log: list[str], page_rows: list[Any]) -> type[Citry]:
    """The ``Citry`` class for ``case``; ``custom_get`` overrides ``get`` with a lookup that logs each call."""
    if case != "custom_get":
        return Citry

    class LookupCitry(Citry):
        def get(self, name: str) -> Any:
            # An overridden lookup still only returns the class, so the
            # Rust walk calls it too; the log shows it ran once per row.
            if name == "row":
                log.append(f"get {len(page_rows)}")
            return super().get(name)

    return LookupCitry


def _patch_lookup(engine: Citry, case: str) -> None:
    """For two cases, make the registry's own read of the row's name raise or answer with another class."""
    if case not in {"get_raised", "class_changed"}:
        return
    registry = engine._registry
    read = registry._get

    def patched(name: str) -> Any:
        # The loop finds its class without this read, so every row's own
        # lookup is the first to raise or to answer with another class: a
        # stand-in for another thread changing the registry.
        if name == "row" and case == "get_raised":
            raise RuntimeError("component lookup refused while another lifecycle change runs")
        return read("other" if name == "row" else name)

    registry._get = patched  # type: ignore[method-assign]


def _walk_page(case: str) -> dict[str, object]:
    """Render one small page for ``case`` as a Vue page and as a fragment; return each output and the calls."""
    log: list[str] = []
    options: dict[str, Any] = {}
    if case in {"unsandboxed", "unsandboxed_missing"}:
        options["sandbox_expressions"] = False
    if case == "plain_scope":
        options["extensions"] = [_PlainScope]
    page_rows: list[Any] = []
    engine = _engine_class(case, log, page_rows)(autodiscover=False, **options)
    engine.set_mounted_prefix("/citry")

    class Row(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            row: Any
            label: Any = None

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            log.append(f"Row {kwargs.row!r} {kwargs.label!r}")
            return {"title": repr(kwargs.row), "label": repr(kwargs.label)}

        template = """
            <article><span>{{ title }}</span><b>{{ label }}</b></article>
        """
        js = """
            $component({data(){return {open: true};}});
        """

    class Other(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            row: Any
            label: Any = None

        template = """
            <p>other</p>
        """

    class RowList(Component):
        citry = engine

        class Kwargs:
            rows: Any
            title: Any = None

        template = f"""
            <section>{_LIST_TEMPLATES.get(case, _RUN_LINE)}</section>
        """
        js = """
            $component({data(){return {open: true};}});
        """

    # const_input passes a constant title, every other case a dynamic one.
    title_input = 'title="fixed title"' if case == "const_input" else 'c-title="title"'

    class RowPage(Component):
        citry = engine

        class Kwargs:
            rows: Any
            title: Any = None

        template = f"""
            <html><head></head><body><main><c-RowList c-rows="rows" {title_input} /></main></body></html>
        """

    del Other  # registered under its name; class_changed's lookup returns it
    _patch_lookup(engine, case)
    result: dict[str, object] = {}
    for label, serialize_options in (("hydrated", {}), ("fragment", {"deps_strategy": "fragment"})):
        try:
            # A fresh value per output, so a generator is not shared.
            rows = _case_rows(case)
            if case == "custom_get":
                page_rows[:] = rows
                rows = page_rows
            with _collecting_trace(log, enabled=case == "tracing"):
                result[label] = RowPage(rows=rows, title="dynamic title").render().serialize(**serialize_options)
        except Exception as error:  # noqa: BLE001 - compared between the paths
            result[label] = f"{type(error).__name__}: {error}"
    result["log"] = log
    return result


def _walked(count: int = 2) -> tuple[int, tuple[str, ...]]:
    """Every render walked its one loop in Rust."""
    return count, ()


def _declined(reason: str) -> tuple[int, tuple[str, ...]]:
    """Both renders left the loop to Python's walk for ``reason``."""
    return 0, (reason, reason)


# For each case, over both outputs: (loops Rust walked, the reason of each
# loop it left to Python's walk), observed, then locked. Each output renders
# the page once, so a walked case walks twice.
CASE_WALKS: dict[str, tuple[int, tuple[str, ...]]] = {
    # Read in Rust.
    "plain": _walked(),
    "tuple_rows": _walked(),
    "int_keys": _walked(),
    "extreme_int_keys": _walked(),
    "list_rows": _walked(),
    "mixed_rows": _walked(),
    # `row[1]` finds the key True, as Python's dict lookup does.
    "bool_keyed_rows": _walked(),
    "nested_path": _walked(),
    "scope_input": _walked(),
    # A marker inside a row is passed on as Python's walk passes it.
    "marker_inside_row": _walked(),
    "empty": _walked(),
    "unsandboxed": _walked(),
    # No plan: the loop clause, key or an input is not a plain path.
    "filtered": _declined("no_plan_loop"),
    "multi_target": _declined("no_plan_loop"),
    "slice_iterable": _declined("no_plan_loop"),
    # The sandbox refuses the key `_key`, so Python raises SecurityError.
    "private_key": _declined("no_plan_key"),
    # The sandbox reads this key as U+FFFD, Python's parser as U+D800.
    "surrogate_key": _declined("no_plan_key"),
    "static_input": _declined("no_plan_input"),
    "call_input": _declined("no_plan_input"),
    # Declined before Rust runs.
    "tracing": _declined("tracing"),
    "plain_scope": _declined("scope"),
    "const_input": _declined("const_input"),
    # Declined by the walk; Python's walk then renders the rows or raises.
    "generator": _declined("iterable"),
    "dict_iterable": _declined("iterable"),
    "missing_key": _declined("missing"),
    "missing_scope_input": _declined("missing"),
    "unsandboxed_missing": _declined("missing"),
    "dict_subclass_row": _declined("not_plain"),
    "list_by_str": _declined("not_plain"),
    "marker_row": _declined("marker"),
    "int_beyond_i64": _declined("key_type"),
    "bool_keys": _declined("key_type"),
    "none_key": _declined("key_type"),
    "read_raised": _declined("read_raised"),
    "get_raised": _declined("get_raised"),
    "class_changed": _declined("class_changed"),
    # An overridden get is called by the Rust walk too.
    "custom_get": _walked(),
}


@pytest.mark.parametrize("case", sorted(CASE_WALKS))
def test_page_cases_render_the_same_on_both_paths(case: str, monkeypatch: pytest.MonkeyPatch) -> None:
    render_both(lambda: _walk_page(case), monkeypatch, walks=CASE_WALKS[case])


def test_a_failing_lookup_runs_the_earlier_rows_lookups_again(monkeypatch: pytest.MonkeyPatch) -> None:
    # The registry's `get` raises from its third call on, as it would while
    # another thread changes the registry. Python's walk raises at the third
    # row. The Rust walk reads every row, makes two lookups, declines at the
    # third, and Python's walk then raises at its first lookup: the same
    # error, after one more lookup. This is the one change in how many
    # times `get` runs.
    lookups: list[str] = []

    def page() -> object:
        row_page = _rows_page(Citry)
        _count_lookups(row_page.citry, lookups)
        try:
            return row_page(rows=_rows(4)).render().serialize()
        except Exception as error:  # noqa: BLE001 - compared between the paths
            return f"{type(error).__name__}: {error}"

    rust, _python = render_both(page, monkeypatch, walks=(0, ("get_raised",)))
    assert cast("str", rust.result).startswith("RuntimeError: ")
    assert lookups.count("python") == 3
    assert lookups.count("rust") == 4


def _count_lookups(engine: Citry, lookups: list[str]) -> None:
    """Count the registry's reads of ``row`` per path, and make them raise from the third on."""
    registry = engine._registry
    read = registry._get
    calls = {"count": 0}

    def counting(name: str) -> Any:
        if name == "row":
            calls["count"] += 1
            lookups.append("rust" if native_render.ACTIVE else "python")
            if calls["count"] >= 3:
                raise RuntimeError("component lookup refused while another lifecycle change runs")
        return read(name)

    registry._get = counting  # type: ignore[method-assign]


def _render_rows(engine_class: type[Citry], rows: Any) -> object:
    """Render one loop of ``simple='vue'`` rows under ``engine_class``; return the HTML or the error."""
    try:
        return _rows_page(engine_class)(rows=rows).render().serialize()
    except Exception as error:  # noqa: BLE001 - compared between the paths
        return f"{type(error).__name__}: {error}"


def _rows_page(engine_class: type[Citry]) -> Any:
    """Define a page that places one loop of ``simple='vue'`` rows, under a new ``engine_class`` engine."""
    engine = engine_class(autodiscover=False)
    engine.set_mounted_prefix("/citry")

    class Row(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            row: Any

        template = """
            <p>{{ row['key'] }}</p>
        """

    class RowPage(Component):
        citry = engine

        class Kwargs:
            rows: Any

        template = f"""
            <html><head></head><body><main>{_RUN_LINE}</main></body></html>
        """

    del Row  # found by its name
    return RowPage


# ---------------------------------------------------------------------------
# The board, and the order cases
# ---------------------------------------------------------------------------


def test_the_rust_walk_reads_every_loop_of_the_board_as_pythons_walk_does(monkeypatch: pytest.MonkeyPatch) -> None:
    # The board at 140 rows in five phases of 28: every loop must be walked
    # in Rust with no decline, or level C2 has silently switched itself off.
    # Each walk is compared with Python's walk of the same loop on the same
    # context: the same rows, kwargs dicts with the same keys in the same
    # order holding the very objects Python reads, and equal call metadata.
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    compared = {"loops": 0, "rows": 0}
    walk_call_run = ForNode._walk_call_run

    def both(self: ForNode, context: Any, run_class: Any) -> Any:
        walked = walk_call_run(self, context, run_class)
        assert type(walked) is list
        python = self._render_call_run(context, run_class)
        assert len(walked) == len(python)
        assert all(type(part) is _DeferredRunRow for part in [*walked, *python])
        assert [part.index for part in walked] == list(range(len(walked)))
        rust_run, python_run = walked[0].run, python[0].run
        assert all(part.run is rust_run for part in walked)
        for name in ("component_class", "parent", "provides", "execution"):
            assert getattr(rust_run, name) is getattr(python_run, name), name
        for rust_kwargs, python_kwargs in zip(rust_run.kwargs, python_run.kwargs, strict=True):
            assert type(rust_kwargs) is dict
            assert list(rust_kwargs) == list(python_kwargs)
            assert all(rust_kwargs[name] is value for name, value in python_kwargs.items())
        for rust_meta, python_meta in zip(rust_run.metadata, python_run.metadata, strict=True):
            assert type(rust_meta) is _PreparedCallMetadata
            assert rust_meta == python_meta
            # An exact str key is the object Python's `str()` returns.
            assert rust_meta.explicit_key is python_meta.explicit_key
        compared["loops"] += 1
        compared["rows"] += len(walked)
        return walked

    monkeypatch.setattr(ForNode, "_walk_call_run", both)
    run = run_on_path(lambda: build_board(make_rows(140), phase_size=28).render().serialize(), monkeypatch, rust=True)
    assert compared == {"loops": 5, "rows": 140}
    python = run_on_path(
        lambda: build_board(make_rows(140), phase_size=28).render().serialize(), monkeypatch, rust=False
    )
    assert python.result == run.result


def test_the_board_walks_its_five_loops_in_rust(monkeypatch: pytest.MonkeyPatch) -> None:
    # The spy of the level's own counts: five loops walked, no decline, and
    # Python's path never asks Rust.
    page = lambda: build_board(make_rows(140), phase_size=28).render().serialize()  # noqa: E731
    render_both(page, monkeypatch, walks=(5, ()))


@pytest.mark.parametrize("case", ["plain", "row_changes_next_row", "keyboard_interrupt", "row_lowers_depth_limit"])
def test_order_cases_on_plain_paths_keep_their_locked_order_through_the_rust_walk(
    case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # tests/test_call_run_order.py locks each case's callbacks on both paths;
    # these cases must reach that record through the Rust walk, including a
    # row that changes the next row's dict in place before it renders.
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    run = run_on_path(lambda: order._assert_matches(case, order._run_case(case)), monkeypatch, rust=True)
    assert run.result is None
    assert (run.walks, run.walk_declines) == (1, ())


def test_two_threads_walking_together_write_the_same_html(monkeypatch: pytest.MonkeyPatch) -> None:
    # The order file's thread case, with the Rust walk: two threads render
    # the page at once, each restarting its own id counter, and every output
    # equals one render alone. Every walk must have run in Rust.
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    walks: list[object] = []
    walk_call_run = ForNode._walk_call_run

    def counting(self: ForNode, context: Any, run_class: Any) -> Any:
        walked = walk_call_run(self, context, run_class)
        walks.append(walked if type(walked) is str else "walked")
        return walked

    monkeypatch.setattr(native_render, "ACTIVE", True)
    monkeypatch.setattr(ForNode, "_walk_call_run", counting)
    case = order._build("plain", order._Recorder())

    def render_once() -> dict[str, str]:
        case.restart_ids()
        rendered = case.page(rows=case.rows).render()
        return {label: rendered.serialize(**options) for label, options in order.LOOP_OUTPUTS.items()}

    alone = render_once()
    switch_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-5)
    try:
        for _attempt in range(5):
            outputs, overlapped = order._render_in_two_threads(render_once)
            assert all(output == alone for output in outputs)
            if overlapped:
                break
        else:
            pytest.fail("the two threads' renders never overlapped in time")
    finally:
        sys.setswitchinterval(switch_interval)
    assert set(walks) == {"walked"}


# ---------------------------------------------------------------------------
# The lowering
# ---------------------------------------------------------------------------

LOWER_PATHS: list[tuple[str, Any]] = [
    ("row", ("row", ())),
    ("row['id']", ("row", ("id",))),
    ('phase["outputs"]', ("phase", ("outputs",))),
    ("groups[0][1]", ("groups", (0, 1))),
    ("row['id']  # a comment", ("row", ("id",))),
    # Escapes both readers decode alike.
    ("row['\\N{EM DASH}x']", ("row", ("\u2014x",))),
    ("row['\\x41']", ("row", ("A",))),
    ("row['a' 'b']", ("row", ("ab",))),
    ("row[0x10]", ("row", (16,))),
    ("row[9223372036854775807]", ("row", (2**63 - 1,))),
    ("row['_id']", None),
    ("_row", None),
    ("row[-1]", None),
    ("row[True]", None),
    ("row[1.5]", None),
    ("row[b'x']", None),
    ("row[None]", None),
    ("row[2**70]", None),
    ("row[9223372036854775808]", None),
    ("row.id", None),
    ("row['a':'b']", None),
    ("row[0:2]", None),
    ("row[key]", None),
    ("f(row)", None),
    ("row + 1", None),
    ("ŕow", None),
    ("rows if x else y", None),
    ("(row := other)", None),
    ("row[", None),
    ("class", None),
    # Both evaluators read these keys as lone surrogates, which no Rust
    # string can hold.
    ("row['\\ud800']", None),
    ("row['a\\udfffb']", None),
    ("row['\\U0000d800']", None),
]

LOWER_LOOPS: list[tuple[tuple[str, ...], str, Any]] = [
    (("row",), "row in rows", ("row", ("rows", ()))),
    (("row",), "row in phase['outputs']", ("row", ("phase", ("outputs",)))),
    (("row",), "(row) in rows", ("row", ("rows", ()))),
    (("row",), "row in rows if row", None),
    (("row",), "row in rows for x in y", None),
    (("k", "v"), "k, v in pairs", None),
    (("row",), "row in rows[1:]", None),
    (("row",), "row in row", None),
    (("row",), "row in f()", None),
    (("_row",), "_row in rows", None),
    (("row",), "row in rows['\\ud800']", None),
    (("row",), "row in", None),
]


@pytest.mark.parametrize(("expr", "expected"), LOWER_PATHS)
def test_lower_path(expr: str, expected: Any) -> None:
    assert lower_path(expr) == expected


@pytest.mark.parametrize(("targets", "clause", "expected"), LOWER_LOOPS)
def test_lower_loop(targets: tuple[str, ...], clause: str, expected: Any) -> None:
    assert lower_loop(targets, clause) == expected


def test_an_expression_the_sandbox_cannot_compile_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(_source: str, *, sandboxed: bool = True) -> Any:
        raise SyntaxError("refused")

    monkeypatch.setattr("citry._vue.native_walk.compile_expr", refuse)
    assert lower_path("row") is None
    assert lower_loop(("row",), "row in rows") is None


# ---------------------------------------------------------------------------
# The plan, called directly
# ---------------------------------------------------------------------------


class _Run:
    """The run's class, as the registry's ``get`` returns it."""


class _Other:
    """Another class under the same name."""


def _get(_name: str) -> Any:
    return _Run


def _plan(key: tuple[str, tuple[Any, ...]] = ("row", ("id",)), kwargs: list[Any] | None = None) -> Any:
    native = native_render.native
    if native is None:
        pytest.skip("this interpreter takes the Python render path")
    paths = [("row", ())] if kwargs is None else kwargs
    return native._CallRunWalkPlan(
        "row",
        ("rows", ()),
        paths,
        key,
        [f"k{index}" for index in range(len(paths))],
        "row",
        "<source>",
        (0, 1),
        _PreparedCallMetadata,
        _ConstMapping,
        _ConstProxy,
    )


def test_the_walk_returns_the_objects_it_read() -> None:
    rows = [{"id": "a"}, {"id": "b"}]
    kwargs, metadata = _plan().walk(_ConstMapping({"rows": rows}), _get, _Run, "origin")
    assert [entry["k0"] for entry in kwargs] == rows
    assert all(entry["k0"] is row for entry, row in zip(kwargs, rows, strict=True))
    assert metadata[0].explicit_key is rows[0]["id"]
    assert metadata[1] == _PreparedCallMetadata("<source>", (0, 1), "b", "origin", slot_free_body=True)


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        ({"rows": [{"id": "a"}]}, 1),
        ({"rows": ({"id": "a"}, {"id": "b"})}, 2),
        ({"rows": []}, 0),
    ],
    ids=["plain_dict_scope", "tuple_iterable", "empty"],
)
def test_the_walk_reads_plain_scopes_and_sequences(variables: dict[str, Any], expected: int) -> None:
    assert len(_plan().walk(variables, _get, _Run, None)[0]) == expected


def test_the_walk_declines_what_it_cannot_read_as_python_does() -> None:
    plan = _plan()
    rows = [{"id": "a"}, {"id": "b"}]

    class Scope(dict):  # type: ignore[type-arg]
        pass

    generator = (row for row in rows)
    int_key = _plan(key=("row", ("n",)))

    class Text(str):
        __slots__ = ()

    assert plan.walk(Scope(rows=rows), _get, _Run, None) == "scope"
    assert plan.walk({"rows": generator}, _get, _Run, None) == "iterable"
    # The generator was not iterated, so Python's walk still sees every item.
    assert next(generator) is rows[0]
    assert plan.walk({"rows": [rows[0], Const(rows[1])]}, _get, _Run, None) == "marker"
    assert plan.walk({"other": rows}, _get, _Run, None) == "missing"
    assert plan.walk({"rows": [["a"]]}, _get, _Run, None) == "not_plain"
    assert plan.walk({"rows": rows}, lambda _name: _Other, _Run, None) == "class_changed"
    assert int_key.walk({"rows": [{"n": 2**63}]}, _get, _Run, None) == "key_type"
    assert int_key.walk({"rows": [{"n": True}]}, _get, _Run, None) == "key_type"
    assert int_key.walk({"rows": [{"n": Text("x")}]}, _get, _Run, None) == "key_type"


def test_int_keys_and_int_steps_read_as_python_reads_them() -> None:
    int_key = _plan(key=("row", ("n",)))
    _kwargs, metadata = int_key.walk({"rows": [{"n": 0}, {"n": -7}, {"n": 2**63 - 1}]}, _get, _Run, None)
    assert [meta.explicit_key for meta in metadata] == ["0", "-7", str(2**63 - 1)]
    by_index = _plan(key=("row", (1,)))
    assert by_index.walk({"rows": [{1: "x"}]}, _get, _Run, None)[1][0].explicit_key == "x"
    assert by_index.walk({"rows": [["a", "b"]]}, _get, _Run, None)[1][0].explicit_key == "b"
    assert by_index.walk({"rows": [["a"]]}, _get, _Run, None) == "missing"


def test_a_scope_input_is_read_for_every_row() -> None:
    page = {"title": "t"}
    plan = _plan(kwargs=[("row", ()), ("page", ("title",)), ("page", ())])
    kwargs, _metadata = plan.walk({"rows": [{"id": "a"}], "page": page}, _get, _Run, None)
    assert kwargs[0]["k1"] == "t"
    assert kwargs[0]["k2"] is page


def test_an_error_from_get_declines_and_an_interrupt_propagates() -> None:
    plan = _plan()
    rows = [{"id": "a"}]

    def raising(_name: str) -> Any:
        raise RuntimeError("lifecycle")

    def interrupted(_name: str) -> Any:
        raise KeyboardInterrupt

    assert plan.walk({"rows": rows}, raising, _Run, None) == "get_raised"
    with pytest.raises(KeyboardInterrupt):
        plan.walk({"rows": rows}, interrupted, _Run, None)


def test_an_error_while_building_a_row_declines() -> None:
    native = native_render.native
    if native is None:
        pytest.skip("this interpreter takes the Python render path")

    def failing_metadata(*_args: Any) -> Any:
        raise MemoryError

    plan = native._CallRunWalkPlan(
        "row",
        ("rows", ()),
        [("row", ())],
        ("row", ("id",)),
        ["row"],
        "row",
        "<source>",
        (0, 1),
        failing_metadata,
        _ConstMapping,
        _ConstProxy,
    )
    assert plan.walk({"rows": [{"id": "a"}]}, _get, _Run, None) == "build_raised"


def test_a_panic_exception_from_python_code_declines() -> None:
    # PyO3 turns a PanicException that Python code raises back into a Rust
    # panic, which the walk turns into a decline (nothing it built is kept).
    panic_exception = next(
        (
            cls
            for cls in BaseException.__subclasses__()
            if cls.__name__ == "PanicException" and cls.__module__ == "pyo3_runtime"
        ),
        None,
    )
    if panic_exception is None:
        pytest.skip("no PyO3 PanicException is loaded")

    def panicking(_name: str) -> Any:
        raise panic_exception("a panic in another extension")

    assert _plan().walk({"rows": [{"id": "a"}]}, panicking, _Run, None) == "panic"


class _Colliding:
    """A dict key whose hash equals ``hashed``'s, so every lookup of ``hashed`` compares it."""

    def __init__(self, hashed: str, calls: list[str], error: type[BaseException] | None = None) -> None:
        self.hashed = hashed
        self.calls = calls
        self.error = error

    def __hash__(self) -> int:
        return hash(self.hashed)

    def __eq__(self, other: object) -> bool:
        self.calls.append("eq")
        if self.error is not None:
            raise self.error("compare failed")
        return False


def test_a_colliding_row_key_is_compared_as_often_as_pythons_reads_compare_it() -> None:
    calls: list[str] = []
    rows = [{_Colliding("id", calls): 1, "id": "a"}, {_Colliding("id", calls): 1, "id": "b"}]
    # Building the dicts compared the keys already; count only the reads.
    calls.clear()
    python_keys = [compile_expr("row['id']")({"row": row}) for row in rows]
    python_compares = len(calls)
    calls.clear()
    _kwargs, metadata = _plan().walk({"rows": rows}, _get, _Run, None)
    assert [meta.explicit_key for meta in metadata] == python_keys
    assert len(calls) == python_compares > 0
    # A decline after those reads makes Python's walk read them again: the
    # stated cost of a decline.
    calls.clear()
    assert _plan().walk({"rows": [*rows, ["not a dict"]]}, _get, _Run, None) == "not_plain"
    assert len(calls) == python_compares


def test_a_colliding_scope_key_is_compared_as_often_as_pythons_reads_compare_it() -> None:
    calls: list[str] = []
    rows = [{"id": "a"}, {"id": "b"}]
    scope = {_Colliding("page", calls): 0, "rows": rows, "page": {"title": "t"}}
    calls.clear()
    # Python's evaluator over the same mapping, both scope inputs per row.
    # The key collides with a scope name, not with the loop variable, so
    # Python's per-row copy of the variables adds no compare.
    title, page = compile_expr("page['title']"), compile_expr("page")
    for _row in rows:
        title(scope)
        page(scope)
    python_compares = len(calls)
    calls.clear()
    plan = _plan(kwargs=[("row", ()), ("page", ("title",)), ("page", ())])
    plan.walk(scope, _get, _Run, None)
    assert len(calls) == python_compares > 0


def test_a_compare_that_raises_declines_and_an_interrupt_propagates() -> None:
    calls: list[str] = []
    raising = _Colliding("id", calls)
    interrupting = _Colliding("id", calls)
    rows: list[Any] = [{raising: 1, "id": "a"}]
    raising.error = ValueError
    assert _plan().walk({"rows": rows}, _get, _Run, None) == "read_raised"
    rows = [{interrupting: 1, "id": "a"}]
    interrupting.error = KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        _plan().walk({"rows": rows}, _get, _Run, None)


def test_a_list_changed_during_the_reads_is_followed_as_pythons_iterator_follows_it() -> None:
    # A colliding key's compare appends a row to the list being walked (and
    # removes one in the second loop). Python's list iterator checks the
    # length before every item, and so does the walk.
    class Growing:
        def __init__(self, target: list[Any], *, grow: bool) -> None:
            self.target = target
            self.grow = grow
            self.armed = False

        def __hash__(self) -> int:
            return hash("id")

        def __eq__(self, other: object) -> bool:
            if self.armed:
                self.armed = False
                if self.grow:
                    self.target.append({"id": "late"})
                else:
                    self.target.pop()
            return False

    for grow, expected in ((True, ["a", "b", "late"]), (False, ["a"])):
        rows: list[Any] = []
        key = Growing(rows, grow=grow)
        rows.extend([{key: 1, "id": "a"}, {"id": "b"}])
        key.armed = True
        python_rows = [row["id"] for row in rows]
        assert python_rows == expected
        # Restore the list and arm the key again for the Rust walk.
        rows[:] = [rows[0], {"id": "b"}]
        key.armed = True
        _kwargs, metadata = _plan().walk({"rows": rows}, _get, _Run, None)
        assert [meta.explicit_key for meta in metadata] == expected


@pytest.mark.parametrize(
    "args",
    [
        ("row", ("_rows", ()), [], ("row", ()), []),
        ("row", ("rows", (-1,)), [], ("row", ()), []),
        ("row", ("row", ()), [], ("row", ()), []),
        ("row", ("rows", (True,)), [], ("row", ()), []),
        ("row", ("rows", ()), [("row", ())], ("row", ()), []),
        ("", ("rows", ()), [], ("row", ()), []),
        ("row", ("rows", ()), [], ("row", ("_id",)), []),
        ("row", ("rows", ()), [], ("", ()), []),
    ],
    ids=[
        "private_name",
        "negative_index",
        "iterable_reads_target",
        "bool_step",
        "names_and_paths_differ",
        "empty_target",
        "private_key",
        "empty_name",
    ],
)
def test_the_constructor_refuses_paths_the_lowering_never_passes(args: tuple[Any, ...]) -> None:
    native = native_render.native
    if native is None:
        pytest.skip("this interpreter takes the Python render path")
    with pytest.raises(ValueError, match=r"walk plan refused|path step|kwarg name"):
        native._CallRunWalkPlan(*args, "row", "s", (0, 1), _PreparedCallMetadata, _ConstMapping, _ConstProxy)


def test_the_plan_is_tracked_by_the_collector_and_leaks_no_reference() -> None:
    plan = _plan()
    # The plan holds the call node's source, which can lead back to the loop
    # node holding the plan, so the collector must see every object it holds
    # and collect such a cycle.
    assert gc.is_tracked(plan)
    referents = gc.get_referents(plan)
    for held in ("row", "<source>", _PreparedCallMetadata, _ConstMapping, _ConstProxy):
        assert any(item is held or item == held for item in referents)

    class Source:
        """Stands for the call node's source, holding the plan as a template would."""

        plan: object = None

    native = native_render.native
    assert native is not None
    source = Source()
    cyclic = native._CallRunWalkPlan(
        "row",
        ("rows", ()),
        [],
        ("row", ()),
        [],
        "row",
        source,
        (0, 1),
        _PreparedCallMetadata,
        _ConstMapping,
        _ConstProxy,
    )
    source.plan = cyclic
    collected = weakref.ref(source)
    del source, cyclic
    gc.collect()
    assert collected() is None
    row = {"id": "a"}
    before = sys.getrefcount(row)
    for _ in range(1000):
        plan.walk({"rows": [row]}, _get, _Run, None)
    assert sys.getrefcount(row) == before


def test_an_error_while_the_plan_is_built_means_no_plan() -> None:
    def broken() -> Any:
        raise UnicodeEncodeError("utf-8", "x", 0, 1, "stand-in for a lowering failure")

    node = cast("ForNode", SimpleNamespace(_lower_walk_plan=broken))
    assert ForNode._build_walk_plan(node) == "no_plan_error"


def test_without_the_rust_module_no_plan_is_built(monkeypatch: pytest.MonkeyPatch) -> None:
    # Plans follow SUPPORTED: where the module is not used, a loop gets no
    # plan, so nothing calls Rust.
    monkeypatch.setattr(native_render, "native", None)
    node = cast("ForNode", SimpleNamespace(branches=()))
    assert ForNode._lower_walk_plan(node) == "no_plan_unsupported"


def test_the_plan_is_built_once_per_loop_node(monkeypatch: pytest.MonkeyPatch) -> None:
    # The second render reuses the plan the first one built.
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    builds: list[object] = []
    build = ForNode._build_walk_plan

    def counting(self: ForNode) -> Any:
        plan = build(self)
        builds.append(plan)
        return plan

    monkeypatch.setattr(native_render, "ACTIVE", True)
    monkeypatch.setattr(ForNode, "_build_walk_plan", counting)
    page = _rows_page(Citry)
    first = page(rows=_rows(2)).render().serialize()
    second = page(rows=_rows(2)).render().serialize()
    assert first.count("</p>") == second.count("</p>") == 2
    assert len(builds) == 1
    assert type(builds[0]) is tuple
