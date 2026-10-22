"""
Level A of the native render path: Rust reads ``simple = "vue"`` rows and hashes call-run ids.

Most cases render one page on the Rust path and on the Python path in this
process (``render_both`` in ``tests/_render_paths.py``) and compare the
bytes or the error, the callbacks' calls, and how many rows Rust read and
how many of those an output rebuilt in Python. The rest check the pieces
directly: the decision of when the Rust path runs, the record properties,
the Rust classes' error modes, and the fixture generator.

A few cases change process-wide state that cannot be undone
(``ComponentLike.register``), so they run in their own interpreter, once
per path.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import math
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

import fastapi
import pytest
from fastapi.testclient import TestClient
from scripts import native_render_fixtures

from citry import Citry, Component
from citry._protocol.events import build_call, build_call_envelope
from citry._vue import leaf_program, native_render
from citry._vue.json_data import _copy_evaluated_json
from citry._vue.leaf_program import LeafProgramNode, native_row_plan_tuples
from citry._vue.serialization import _script_json
from citry.citry_render import SimpleVueRecord
from citry.component_render import _simple_vue_admission
from citry.contrib.fastapi import mount
from citry.secret import Secret
from citry.util.html import Markup

from ._render_paths import NONCE, render_both, run_on_path

# The project board's row, trimmed to the shapes level A reads: a root
# c-bind, texts, attributes, a c-if and nested loops.
ROW_TEMPLATE = """
<article c-bind="row_attrs" data-output-expanded="true">
<h3>{{ row['title'] }}</h3>
<span c-data-status="row['status']">{{ row['status'] }}</span>
<input type="checkbox" c-checked="row['completed']">
<c-if cond="row['dependencies']">
<p
  c-for="dep in row['dependencies']"
  c-data-dependency-id="dep['id']"
  c-data-done="'true' if dep['done'] else 'false'"
>{{ dep['title'] }}</p>
</c-if>
<c-else>
<p>No dependencies</p>
</c-else>
<ul><li c-for="tag in row['tags']">{{ tag }}</li></ul>
</article>
"""

# Every output kind serialize() offers; each one reads the rows differently.
OUTPUTS: dict[str, dict[str, Any]] = {
    "hydrated": {},
    "ssr_false": {"ssr": False},
    "static": {"deps_strategy": "simple"},
    "fragment": {"deps_strategy": "fragment"},
    "hydration_declined": {"deps_position": "append"},
    "csp": {"security_csp": "strict", "csp_nonce": NONCE},
}
# The outputs that write each row's HTML, so they rebuild every Rust-read row.
HTML_OUTPUTS = {"static", "fragment", "hydration_declined", "csp"}


def make_rows(count: int, *, seed: int = 7) -> list[dict[str, Any]]:
    """Board-shaped rows with a fixed seed, so both paths see the same data."""
    rng = random.Random(seed)  # noqa: S311 - reproducible test data
    return [
        {
            "id": f"output-{index}",
            "key": f"k{index}",
            "title": f"Output {index} <caf\u00e9>",
            "status": rng.choice(["todo", "doing", "done"]),
            "completed": rng.random() < 0.3,
            "dependencies": [
                {"id": index * 10 + n, "title": f"Dep {n}", "done": rng.random() < 0.5}
                for n in range(rng.randrange(3))
            ],
            "tags": [f"t{n}" for n in range(rng.randrange(3))],
        }
        for index in range(count)
    ]


@dataclasses.dataclass
class Board:
    """One page and the things a case changes on it."""

    engine: Citry
    page: type[Component]
    row: type[Component]
    rows: list[dict[str, Any]]
    calls: dict[str, int]

    def render(self) -> Any:
        return self.page(rows=self.rows).render()


def build_board(
    rows: list[dict[str, Any]],
    *,
    in_root: bool = False,
    template_data: Any = None,
    template: str = ROW_TEMPLATE,
    **engine_options: Any,
) -> Board:
    """
    Build the page: rows inside child components (``Phase``), or written in the page's own template.

    ``template_data(row, index)``, when given, returns the row's variables,
    so a case can hand one row a value Rust declines.
    """
    engine = Citry(autodiscover=False, secret="native-render-test-secret", **engine_options)  # noqa: S106
    # The hydrated document links the page's scripts under the engine's URL prefix.
    engine.set_mounted_prefix("/citry")
    calls = {"template_data": 0}

    def row_template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
        calls["template_data"] += 1
        row = kwargs.row
        if template_data is not None:
            return template_data(row, calls["template_data"] - 1)
        return {"row": row, "row_attrs": {"id": f"row-{row['id']}", "data-row-id": row["id"]}}

    row_class = type(
        "Output",
        (Component,),
        {
            "citry": engine,
            "simple": "vue",
            "Kwargs": type("Kwargs", (), {"__annotations__": {"row": dict}}),
            "template_data": staticmethod(row_template_data),
            "template": template,
            "js": "$component({data(){return {open: true};}});",
        },
    )

    class Phase(Component):
        citry = engine

        class Kwargs:
            phase: dict

        template = """
            <section c-data-phase-id="phase['id']">
              <c-Output
                c-for="row in phase['rows']"
                #c-key="row['key']"
                c-row="row"
              />
            </section>
        """
        js = """
            $component({data(){return {open: true};}});
        """

    if in_root:
        body = """
            <c-Output
              c-for="row in rows"
              #c-key="row['key']"
              c-row="row"
            />
        """
    else:
        body = """
            <c-Phase
              c-for="phase in phases"
              #c-key="phase['id']"
              c-phase="phase"
            />
        """

    class Page(Component):
        citry = engine

        class Kwargs:
            rows: list

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            # Rows go to phases of up to ten, so one page has several call runs.
            phases = [
                {"id": f"phase-{start}", "rows": kwargs.rows[start : start + 10]}
                for start in range(0, len(kwargs.rows), 10)
            ]
            return {"rows": kwargs.rows, "phases": phases}

        template = f"""
            <html><head></head><body><main>{body}</main></body></html>
        """

    return Board(engine, Page, row_class, rows, calls)


def serialize_all(board: Board, outputs: dict[str, dict[str, Any]]) -> dict[str, object]:
    """Render once per output and serialize; an output that raises records its error."""
    result: dict[str, object] = {}
    for label, options in outputs.items():
        try:
            if options.get("security_csp") == "strict":
                # Strict CSP must be the engine's own policy too.
                board.engine.settings = dataclasses.replace(board.engine.settings, security_csp="strict")
            result[label] = board.render().serialize(**options)
        except Exception as error:  # noqa: BLE001 - compared between the paths
            result[label] = f"{type(error).__name__}: {error}"
    result["template_data calls"] = board.calls["template_data"]
    return result


# ---------------------------------------------------------------------------
# Byte identity on every output
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("in_root", [False, True], ids=["child_rows", "root_rows"])
@pytest.mark.parametrize("size", [14, 40])
@pytest.mark.parametrize("output", list(OUTPUTS))
def test_every_output_writes_the_same_bytes_on_both_paths(
    output: str, size: int, *, in_root: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    # On a full HTML document Vue mounts or hydrates, the serializer leaves
    # out the body, so no row needs its HTML, in a child component or in
    # the root template. The HTML outputs and strict CSP with a nonce keep
    # the body, so every row is rebuilt.
    rebuilt = size if output in HTML_OUTPUTS else 0
    render_both(
        lambda: serialize_all(build_board(make_rows(size), in_root=in_root), {output: OUTPUTS[output]}),
        monkeypatch,
        rows_read=size,
        rows_rebuilt=rebuilt,
    )


@pytest.mark.qualification
def test_a_board_of_1400_rows_writes_the_same_bytes_on_both_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    # The size the benchmark page measures; only the full profile runs it.
    outputs = {label: OUTPUTS[label] for label in ("hydrated", "static")}
    render_both(
        lambda: serialize_all(build_board(make_rows(1400)), outputs),
        monkeypatch,
        rows_read=2800,
        rows_rebuilt=1400,
    )


def test_one_render_serialized_twice_and_as_mixed_outputs(monkeypatch: pytest.MonkeyPatch) -> None:
    def run() -> object:
        board = build_board(make_rows(14))
        rendered = board.render()
        # A static output builds each row's leaf once and keeps it; the
        # hydrated page written after it must not change.
        return [
            rendered.serialize(),
            rendered.serialize(),
            rendered.serialize(deps_strategy="simple"),
            rendered.serialize(deps_strategy="fragment"),
            rendered.serialize(),
        ]

    rust, _python = render_both(run, monkeypatch, rows_read=14, rows_rebuilt=14)
    outputs = rust.result
    assert isinstance(outputs, list)
    assert outputs[0] == outputs[1] == outputs[4]


@pytest.mark.parametrize("in_root", [False, True], ids=["child_rows", "root_rows"])
def test_development_mode_keeps_rows_on_the_python_path(*, in_root: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    # Development mode checks every element id the page writes, so the
    # serializer needs every row's HTML even on a hydrated page. Reading
    # the rows in Rust would only add work, so a development engine skips it.
    render_both(
        lambda: serialize_all(build_board(make_rows(14), in_root=in_root, mode="development"), {"hydrated": {}}),
        monkeypatch,
        rows_read=0,
        rows_rebuilt=0,
    )


def test_a_custom_tag_callback_keeps_rows_off_the_precompile_path(monkeypatch: pytest.MonkeyPatch) -> None:
    # Only the precompile path writes Rust's JSON; with a tag callback of the
    # page's own, every row's leaf is rebuilt for the manifest instead.
    def run() -> object:
        board = build_board(make_rows(14))
        producer = native_render_producer(board.engine)
        builtin = producer._tag_for_type
        producer._tag_for_type = lambda type_key: builtin(type_key)
        return serialize_all(board, {"hydrated": {}})

    render_both(run, monkeypatch, rows_read=14, rows_rebuilt=14)


def native_render_producer(engine: Citry) -> Any:
    """Return the engine's Vue Events producer, the object that owns the component tag callback."""
    from citry._vue.events import default_events_producer

    return default_events_producer(engine)


# ---------------------------------------------------------------------------
# Events: the update responses
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ActionIn:
    action: str = ""


def events_chain() -> object:
    """Load the page, then run four Events actions in turn, each with the previous response's token."""
    rows = make_rows(14)
    board = build_board(rows)
    engine = board.engine
    page_class = board.page

    class Live(Component):
        citry = engine

        class Kwargs:
            rows: list

        class State(Kwargs):
            pass

        class Events:
            def act(self, data: ActionIn, state: Any) -> Any:
                current = list(state.rows)
                if data.action == "insert":
                    current.insert(3, {**current[0], "id": "inserted", "key": "inserted", "title": "New"})
                elif data.action == "reorder":
                    current.reverse()
                elif data.action == "remove":
                    current = [row for row in current if row["id"] != "inserted"]
                return Live(rows=current)

        template = """
            <form @c-submit.prevent="act">
              <c-Phase
                c-for="phase in phases"
                #c-key="phase['id']"
                c-phase="phase"
              />
            </form>
        """

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return page_class.template_data(self, kwargs, slots)

    class LivePage(Component):
        citry = engine

        class Kwargs:
            rows: list

        template = """
            <html><head></head><body><main><c-Live c-rows="rows" /></main></body></html>
        """

    app = fastapi.FastAPI()
    mount(app, engine)
    client = TestClient(app)
    page = LivePage(rows=rows).render().serialize()
    match = page.split('data-citry-vue-document="', 1)[1].split(">", 1)[1].split("</script>", 1)[0]
    manifest = json.loads(match)["manifest"]
    owner = next(item for item in manifest["occurrences"] if "eventContext" in item)
    responses: list[object] = [page]
    revision = 0
    for sequence, action in enumerate(("probe", "insert", "reorder", "remove"), start=1):
        context = owner["eventContext"]
        call = build_call(
            context["componentClassId"],
            "act",
            {"action": action},
            caller_render_id=context["serverRenderId"],
            state_token=context["stateToken"],
            send_sequence=sequence,
        )
        envelope = build_call_envelope(
            f"chain-{sequence}",
            [call],
            capabilities={"actions": ["render"], "swaps": ["morph"], "renderers": ["vue-prepared/1"]},
        )
        response = client.post(
            "/citry/ext/events/call",
            content=json.dumps(envelope),
            headers={
                "content-type": "application/citry-events+json",
                "x-citry-events": "1",
                "x-citry-vue-app": manifest["appId"],
                "x-citry-vue-occurrence": owner["id"],
                "x-citry-vue-revision": str(revision),
            },
        )
        responses.append(response.text)
        result = response.json()["results"][0]
        assert result["ok"], result
        prepared = next(item for item in result["actions"] if item["action"] == "render")["prepared"]
        revision = prepared["revision"]
        owner = next(item for item in prepared["occurrences"] if "eventContext" in item)
    return responses


def test_events_updates_send_the_same_responses_on_both_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    # Updates read rows in Rust but rebuild each one for their manifest, so
    # the four updates rebuild 14, 15, 15 and 14 rows; the page itself none.
    render_both(events_chain, monkeypatch, rows_read=14 + 14 + 15 + 15 + 14, rows_rebuilt=14 + 15 + 15 + 14)


# ---------------------------------------------------------------------------
# Faults: rows Rust declines, and errors raised on both paths
# ---------------------------------------------------------------------------

FAULT_ROW = 5


class DictSubclass(dict):  # type: ignore[type-arg]
    pass


class RenderId(str):
    __slots__ = ()


def _fault_data(name: str) -> Any:
    """Return a ``template_data`` that gives row FAULT_ROW (or every row) the fault ``name``."""
    reused: dict[str, Any] = {}

    def data(row: dict[str, Any], index: int) -> dict[str, Any]:
        attrs: dict[str, Any] = {"id": f"row-{row['id']}", "data-row-id": row["id"]}
        if name == "spread_limit":
            # A new c-bind key set on every row, past Rust's layout cache.
            attrs[f"data-k{index}"] = "v"
        if name == "reused_dict":
            # One dict object, changed for every row.
            reused.clear()
            reused.update(attrs)
            attrs = reused
        if index != FAULT_ROW:
            return {"row": row, "row_attrs": attrs}
        row = dict(row)
        faults: dict[str, Any] = {
            "missing_key": lambda: row.pop("title"),
            "markup": lambda: row.update(title=Markup("<b>trusted</b>")),
            "nan": lambda: row.update(title=math.nan),
            "secret": lambda: row.update(title=Secret("hidden")),
            "tuple": lambda: row.update(dependencies=tuple(row["dependencies"])),
            "lone_surrogate": lambda: row.update(title="bad \ud800 text"),
            "int_beyond_i64": lambda: row.update(title=-(2**66), status=2**70),
            "int_past_digit_limit": lambda: row.update(title=10 ** (sys.get_int_max_str_digits() + 1)),
            "float_registered": lambda: row.update(title=1.5),
            "onclick": lambda: attrs.update(onclick="alert(1)"),
            "style": lambda: attrs.update(style="color:red"),
            "case_collision": lambda: attrs.update(ID="upper"),
        }
        if name == "dict_subclass":
            return {"row": DictSubclass(row), "row_attrs": attrs}
        if name in faults:
            faults[name]()
        return {"row": row, "row_attrs": attrs}

    return data


def fault_result(name: str) -> object:
    """Render the fault page, change what the case changes, and serialize it as hydrated and static."""
    rows = make_rows(40)
    if name == "surrogate_key":
        rows[FAULT_ROW]["key"] = "bad \ud800 key"
    options: dict[str, Any] = {}
    if name == "str_subclass_render_id":
        counter = iter(range(10_000))
        options["id_generator"] = lambda: RenderId(f"r{next(counter)}")
    board = build_board(rows, template_data=_fault_data(name), **options)
    if name == "shadowing_global":
        # A template global named like a loop target sends every row to Python,
        # which raises its shadowing error.
        board.engine.template_globals = {"dep": 1}
    rendered = board.render()
    if name == "mutated_after_render":
        # The output must keep the values each row had when it rendered.
        for row in rows:
            row["title"] = "changed after render"
            row["dependencies"].append({"id": -1, "title": "late", "done": False})
    result: dict[str, object] = {"template_data calls": board.calls["template_data"]}
    for label, output in (("hydrated", {}), ("static", {"deps_strategy": "simple"})):
        try:
            result[label] = rendered.serialize(**output)
        except Exception as error:  # noqa: BLE001 - compared between the paths
            result[label] = f"{type(error).__name__}: {error}"
    return result


def fault_or_error(name: str) -> object:
    """The fault case's result, or the error its render raised (with the component path in the message)."""
    try:
        return fault_result(name)
    except Exception as error:  # noqa: BLE001 - compared between the paths
        return f"{type(error).__name__}: {error}"


# How many of the 40 rows Rust reads in each fault case. A fault Python
# refuses fails the render at row FAULT_ROW, after Rust read the rows before it.
FAULT_ROWS_READ = {
    "missing_key": FAULT_ROW,
    "dict_subclass": FAULT_ROW,
    "markup": FAULT_ROW,
    "nan": FAULT_ROW,
    "secret": FAULT_ROW,
    "tuple": FAULT_ROW,
    "int_past_digit_limit": FAULT_ROW,
    "onclick": FAULT_ROW,
    # Values Python renders but Rust declines: the row renders in Python.
    "lone_surrogate": 39,
    "int_beyond_i64": 39,
    "style": 39,
    "case_collision": 39,
    # Rust keeps 32 key sets; the rest of the rows go to Python.
    "spread_limit": 32,
    "reused_dict": 40,
    "mutated_after_render": 40,
    # Python hashes that one row's ids; Rust still reads every row.
    "surrogate_key": 40,
    "str_subclass_render_id": 40,
    "shadowing_global": 0,
}


@pytest.mark.parametrize("name", sorted(FAULT_ROWS_READ))
def test_faults_raise_or_render_the_same_on_both_paths(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    render_both(lambda: fault_or_error(name), monkeypatch, rows_read=FAULT_ROWS_READ[name])


def test_a_lowered_digit_limit_after_render_changes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Rust declines every int outside i64, so a row's copy never depends on
    # the digit limit in force when a later output rebuilds it.
    def run() -> object:
        limit = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(6000)
        try:
            board = build_board(
                make_rows(14),
                template_data=lambda row, index: {
                    "row": {**row, "title": 10**5000} if index == FAULT_ROW else row,
                    "row_attrs": {"id": f"row-{row['id']}"},
                },
            )
            rendered = board.render()
        finally:
            sys.set_int_max_str_digits(limit)
        return [rendered.serialize(), rendered.serialize(deps_strategy="simple")]

    render_both(run, monkeypatch, rows_read=13, rows_rebuilt=13)


def test_a_lone_surrogate_in_a_template_key_is_handed_back(monkeypatch: pytest.MonkeyPatch) -> None:
    template = """
        <p>{{ row['\\ud800'] }}</p>
    """
    rows = [{"id": "a", "key": "a", "\ud800": "x"}, {"id": "b", "key": "b", "\ud800": "y"}]
    render_both(
        lambda: serialize_all(build_board(rows, template=template), {"static": OUTPUTS["static"]}), monkeypatch
    )


# The cases that register a type with ComponentLike, which lasts for the
# rest of the process, so each runs in a fresh interpreter.
_OWN_PROCESS_FAULTS = {"component_like_str": "str", "component_like_float": "float"}


def _fault_in_own_process(name: str, *, rust: bool) -> object:
    script = """
import json, sys
sys.path.insert(0, sys.argv[4])
import pytest
from citry.component_like import ComponentLike
from tests._render_paths import run_on_path
from tests.test_native_render_rows import fault_or_error

ComponentLike.register({"str": str, "float": float}[sys.argv[2]])
with pytest.MonkeyPatch.context() as patch:
    run = run_on_path(lambda: fault_or_error(sys.argv[1]), patch, rust=sys.argv[3] == "rust")
print(json.dumps([run.result, run.rows_read]))
"""
    kind = _OWN_PROCESS_FAULTS[name]
    fault = "float_registered" if kind == "float" else "plain"
    result = subprocess.run(
        # The last argument puts the repository root on the path, for `scripts`.
        [sys.executable, "-c", script, fault, kind, "rust" if rust else "python", str(Path(__file__).parents[4])],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.splitlines()[-1])


@pytest.mark.parametrize("name", sorted(_OWN_PROCESS_FAULTS))
def test_component_like_registration_gives_the_same_result_on_both_paths(name: str) -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    rust_result, rust_rows = _fault_in_own_process(name, rust=True)
    python_result, python_rows = _fault_in_own_process(name, rust=False)
    assert rust_result == python_result
    assert python_rows == 0
    # A registered float makes row FAULT_ROW's float a component value:
    # Rust declines the row and Python's check fails the render there. A
    # registered str breaks the page before any row renders.
    assert rust_rows == (FAULT_ROW if name == "component_like_float" else 0)


# ---------------------------------------------------------------------------
# The record, the flag and the decision
# ---------------------------------------------------------------------------


def _first_record(rendered: Any) -> SimpleVueRecord:
    """Return the first ``simple='vue'`` record a render holds, searching its child renders."""
    pending = [rendered]
    while pending:
        current = pending.pop()
        for part in current.parts:
            if type(part) is SimpleVueRecord:
                return part
            if hasattr(part, "parts"):
                pending.append(part)
    msg = "the render holds no simple='vue' record"
    raise AssertionError(msg)


def test_copying_a_rust_record_keeps_its_row_and_its_lazy_leaf(monkeypatch: pytest.MonkeyPatch) -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    monkeypatch.setattr(native_render, "ACTIVE", True)
    record = _first_record(build_board(make_rows(3), in_root=True).render())
    assert record.native is not None
    # A Python composition site copies the record this way
    # (`_mark_python_simple_vue` in citry/_vue/direct.py).
    copied = dataclasses.replace(record, python_composition=True)
    assert type(copied) is SimpleVueRecord
    assert copied.python_composition is True
    assert copied.native is record.native
    assert copied._leaf is None
    assert copied.call_children is None
    assert copied.vue_errors == ()
    assert copied.fragment is record.fragment
    assert copied.prepared_data == record.prepared_data


def test_the_rust_path_is_on_where_it_is_supported(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    # Without this, a stale build or a broken import would fall back to the
    # Python path silently and every other test would still pass.
    import sysconfig

    standard_cpython = (
        sys.implementation.name == "cpython"
        and sys.platform != "emscripten"
        and not sysconfig.get_config_var("Py_GIL_DISABLED")
    )
    assert native_render.SUPPORTED is standard_cpython
    if not standard_cpython:
        return
    if not request.config.getoption("--python-render-path"):
        assert native_render.ACTIVE is native_render._decision.active
    evaluated: list[str] = []
    original = LeafProgramNode.render_static_instance_free

    def spy(self: LeafProgramNode, variables: dict[str, object], **kwargs: Any) -> Any:
        evaluated.append(kwargs["component_name"])
        return original(self, variables, **kwargs)

    monkeypatch.setattr(LeafProgramNode, "render_static_instance_free", spy)
    run = run_on_path(lambda: build_board(make_rows(14)).render().serialize(), monkeypatch, rust=True)
    assert run.rows_read == 14
    assert run.rows_rebuilt == 0
    assert evaluated == []


@pytest.mark.parametrize("serialize_on_rust", [True, False])
def test_switching_the_flag_between_render_and_serialize_keeps_the_bytes(
    serialize_on_rust: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")

    def run() -> object:
        rendered = build_board(make_rows(14)).render()
        native_render.ACTIVE = serialize_on_rust
        return [rendered.serialize(), rendered.serialize(deps_strategy="simple")]

    render_on_rust = not serialize_on_rust
    switched = run_on_path(run, monkeypatch, rust=render_on_rust)
    reference = run_on_path(run, monkeypatch, rust=False)
    assert switched.result == reference.result
    assert switched.rows_read == (14 if render_on_rust else 0)


_RUST_NAMES = ("_RowPlan", "_NativeRow", "_RunDigests", "_encode_occurrences")


class _FullModule:
    """Stands for a native module that has every name the native path calls."""

    _RowPlan = _NativeRow = _RunDigests = _encode_occurrences = None


class _OlderModule:
    """Stands for a native module from before ``_RunDigests`` existed."""

    _RowPlan = _NativeRow = _encode_occurrences = None


@pytest.mark.parametrize(
    ("implementation", "platform", "gil_disabled", "module", "env_value", "supported", "active", "warns"),
    [
        ("cpython", "linux", 0, _FullModule, None, True, True, None),
        ("cpython", "linux", None, _FullModule, "1", True, True, None),
        ("cpython", "linux", 0, _FullModule, "0", True, False, None),
        ("cpython", "linux", 0, _FullModule, "yes", True, True, "is not '0' or '1'"),
        ("pypy", "linux", 0, _FullModule, None, False, False, None),
        ("cpython", "emscripten", 0, _FullModule, None, False, False, None),
        ("cpython", "linux", 1, _FullModule, None, False, False, None),
        ("pypy", "linux", 0, None, "off", False, False, "is not '0' or '1'"),
        ("cpython", "linux", 0, None, None, False, False, "native_render is missing"),
        ("cpython", "darwin", 0, _OlderModule, None, False, False, "native_render._RunDigests is missing"),
        ("cpython", "win32", 0, None, "0", False, False, "native_render is missing"),
    ],
)
def test_the_decision_covers_each_interpreter_and_setting(
    implementation: str,
    platform: str,
    gil_disabled: object,
    module: object,
    env_value: str | None,
    *,
    supported: bool,
    active: bool,
    warns: str | None,
) -> None:
    decision = native_render._decide(
        implementation=implementation,
        platform=platform,
        gil_disabled=gil_disabled,
        module=module,
        env_value=env_value,
    )
    assert (decision.supported, decision.active) == (supported, active)
    if warns is None:
        assert decision.warnings == ()
    else:
        assert len(decision.warnings) == 1
        assert warns in decision.warnings[0]


def test_each_decision_warning_is_shown_once() -> None:
    decision = native_render._Decision(supported=False, active=False, warnings=("first", "second"))
    with pytest.warns(RuntimeWarning) as caught:
        native_render._warn(decision)
    assert [str(item.message) for item in caught] == ["first", "second"]


def test_a_description_rust_refuses_keeps_the_template_in_python(monkeypatch: pytest.MonkeyPatch) -> None:
    # A data key named "calls" would clash with the key assembly adds, so
    # Rust refuses the plan and every row of the template stays in Python.
    def refused(_node: LeafProgramNode) -> object:
        return ((("text", "calls", ("c", "x")),), (), (), 32)

    monkeypatch.setattr("citry._vue.leaf_program.native_row_plan_tuples", refused)
    run = run_on_path(lambda: build_board(make_rows(3)).render().serialize(), monkeypatch, rust=True)
    assert run.rows_read == 0
    assert isinstance(run.result, str)


def test_the_shipped_module_has_every_name_the_decision_checks() -> None:
    assert native_render._REQUIRED_NAMES == _RUST_NAMES
    if native_render.SUPPORTED:
        assert all(hasattr(native_render.native, name) for name in _RUST_NAMES)


# ---------------------------------------------------------------------------
# The Rust classes directly
# ---------------------------------------------------------------------------


def _node(template: str) -> LeafProgramNode:
    engine = Citry(autodiscover=False)
    component = type("Probe", (Component,), {"citry": engine, "simple": "vue", "template": template})
    node = _simple_vue_admission(component).leaf_node
    assert isinstance(node, LeafProgramNode)
    return node


def _python_json(node: LeafProgramNode, variables: dict[str, object]) -> str:
    leaf = node.render_static_instance_free(variables, component_name="Probe")
    return _script_json(
        {"calls": {}, **{key: _copy_evaluated_json(value) for key, value in leaf.prepared_data.items()}}
    )


def test_rust_writes_floats_and_ints_as_python_does() -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    node = _node("""
        <p c-data-v="v">{{ v }}</p>
    """)
    rng = random.Random(11)  # noqa: S311 - reproducible test data
    values: list[object] = [0.1, -0.0, 1e16, 1e-5, 5e-324, 2**53, -(2**53), 2**63 - 1, -(2**63)]
    values += [rng.uniform(-1e9, 1e9) for _ in range(300)] + [
        rng.random() * 10 ** rng.randrange(-300, 300) for _ in range(300)
    ]
    for value in values:
        row = node.read_native_row({"v": value})
        assert row is not None, value
        assert row.prepared_json == _python_json(node, {"v": value}), value


def test_a_row_rust_read_rebuilds_from_its_snapshot() -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    node = _node(ROW_TEMPLATE)
    [row] = make_rows(1)
    variables = {"row": row, "row_attrs": {"id": "x", "data-n": 3, "data-f": 2.5, "data-off": False}}
    native = node.read_native_row(variables)
    assert native is not None
    snapshot = native.snapshot()
    # A fresh dict each time, which a later change to the row cannot reach.
    assert snapshot is not native.snapshot()
    row["title"] = "changed"
    leaf = node.render_native_snapshot(snapshot, component_name="Probe")
    assert _script_json({"calls": {}, **leaf.prepared_data}) == native.prepared_json


def test_rust_declines_what_python_must_check() -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    node = _node(ROW_TEMPLATE)
    [row] = make_rows(1)
    attrs = {"id": "x"}
    declined = [
        DictSubclass({"row": row, "row_attrs": attrs}),
        {"row": {**row, "title": "\udc00"}, "row_attrs": attrs},
        {"row": {**row, "title": 2**64}, "row_attrs": attrs},
        {"row": {**row, "title": math.inf}, "row_attrs": attrs},
        {"row": {**row, "tags": ("a",)}, "row_attrs": attrs},
        {"row": row, "row_attrs": {1: "x"}},
        {"row": row, "row_attrs": {"\udc00": "x"}},
        {"row": row, "row_attrs": {"onclick": "x"}},
        {"row": row},
        # A variable named like a loop target.
        {"row": row, "row_attrs": attrs, "dep": 1},
    ]
    for variables in declined:
        assert node.read_native_row(variables) is None, variables


def test_the_occurrence_encoder_refuses_items_assembly_never_makes() -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    native = native_render.native
    assert native is not None
    row = _node("""
        <p>{{ v }}</p>
    """).read_native_row({"v": "x"})
    good = {
        "definitionId": "d",
        "id": "o",
        "parentId": None,
        "placementKey": None,
        "preparedData": {"calls": {}},
        "renderId": "r",
        "serverData": {},
        "typeKey": "t",
    }
    assert (
        native._encode_occurrences([good], {"o": row}, _script_json)
        == "[" + _script_json({**good, "preparedData": json.loads(row.prepared_json)}) + "]"
    )
    for bad in (
        {**good, "extra": 1},
        {**good, "preparedData": {"calls": {}, "x": 1}},
        {**good, "serverData": {"x": 1}},
        {**good, "renderId": 5},
    ):
        with pytest.raises(ValueError, match="native occurrence item"):
            native._encode_occurrences([bad], {"o": row}, _script_json)
    with pytest.raises(ValueError, match="is not a dict"):
        native._encode_occurrences([("o",)], {"o": row}, _script_json)
    with pytest.raises(ValueError, match="not a _NativeRow"):
        native._encode_occurrences([good], {"o": "text"}, _script_json)
    with pytest.raises(ValueError, match="fallback result is not a str"):
        native._encode_occurrences([good], {}, lambda _item: 5)


def test_run_ids_fall_back_for_a_key_with_no_utf8_form() -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    native = native_render.native
    assert native is not None
    digests = native._RunDigests('["site"', '["parent"')
    assert digests.member_ids("bad \ud800") is None
    placement, child = digests.member_ids("k")
    assert placement.startswith("citryPlacement")
    assert child.startswith("citryOccurrence")


def test_a_dropped_template_frees_its_row_plan() -> None:
    if not native_render.SUPPORTED:
        pytest.skip("this interpreter takes the Python render path")
    native = native_render.native
    assert native is not None

    def plans() -> int:
        return sum(1 for item in gc.get_objects() if type(item) is native._RowPlan)

    gc.collect()
    before = plans()
    node = _node(ROW_TEMPLATE)
    # The plan holds a callback that holds the node, which holds the plan.
    assert node.native_row_plan is not None
    row = node.read_native_row({"row": make_rows(1)[0], "row_attrs": {"id": "x"}})
    assert plans() == before + 1
    # A row holds only strings and Rust data, so the collector skips it.
    assert gc.is_tracked(row) is False
    del node, row
    gc.collect()
    assert plans() == before


def test_the_cargo_fixtures_match_what_python_writes() -> None:
    # The Rust crate's tests compare against these files; they must be the
    # current Python code's own output.
    assert native_render_fixtures.check() == []


def test_templates_rust_does_not_run_have_no_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    # The expression subset admits only None, bool and str literals; any
    # other literal means the subset grew, and Rust must not guess its text.
    assert leaf_program._native_row_expr(leaf_program._SimpleJsonExpr(kind="constant", value=5)) is None
    assert leaf_program._native_row_expr(leaf_program._SimpleJsonExpr(kind="call")) is None
    # A template the Python evaluator cannot run has no Rust plan either.
    plain = _node(ROW_TEMPLATE)
    monkeypatch.setattr(plain, "static_instance_free_template_supported", lambda: False)
    assert native_row_plan_tuples(plain) is None
