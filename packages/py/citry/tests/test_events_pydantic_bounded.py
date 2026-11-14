"""
Pydantic event data and State writes, checked by Citry's copy of the class's validator.

Citry builds, once per Pydantic class, a second validator from the class's
own core schema. It stops each list or dict at its first bad item, counts
the errors of the whole validation and stops past a limit, and spends from
one work budget per request when a recursive value may be checked again.
These tests cover what a caller sees: the same values for valid data, the
stop messages, the registration errors, the State paths, and the fallback
when the copy cannot be built. ``_pydantic_bounded.py`` explains the design.
"""

from __future__ import annotations

import asyncio
import collections
import dataclasses
import datetime
import decimal
import enum
import ipaddress  # noqa: TC003 - Pydantic reads the test classes' annotations at run time
import json
import logging
import random
import re
import subprocess
import sys
import threading
import time
import tracemalloc
import uuid
from collections.abc import Mapping, Sequence
from typing import Annotated, Any, Literal, cast, get_args
from weakref import WeakKeyDictionary

import pydantic
import pydantic.dataclasses
import pydantic_core
import pytest
import typing_extensions
from pydantic_core import SchemaValidator
from pydantic_core import core_schema as pydantic_core_schema
from typing_extensions import TypeAliasType, TypedDict

from citry import Citry, Component
from citry.ext.events import _pydantic_bounded as bounded
from citry.ext.events.dispatcher import EventsDispatcher, TransportContext
from citry.ext.events.errors import MAX_FIELD_ERRORS_TEXT, FieldErrors
from citry.ext.events.schemas import validate_args
from citry.ext.events.state import restore_state
from citry.ext.events.tokens import StateUpdateError, apply_state_updates, mint_state_token

SIGNING_KEY = "test-secret-key"


@pytest.fixture(autouse=True)
def _steady_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    # A test that expects the step budget to stop a check would see the CPU
    # limit stop it first on a slow or busy machine, so the CPU limit is out
    # of reach here; the tests of the CPU limit set their own. Each test gets
    # its own record of the once-per-class warnings, so a test that looks
    # for a warning does not depend on which tests ran before it.
    monkeypatch.setattr(bounded, "WORK_SECONDS", 60.0)
    monkeypatch.setattr(bounded, "_WARNED_WORK", WeakKeyDictionary())


class _HandClock:
    """A CPU clock that moves only when a test moves it, so a test of the CPU limit does not depend on the machine."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def deep_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    # A test of the work budget needs data deep enough for the budget to run
    # out, which is past the nesting limit. pytest runs tests on the main
    # thread, which has 8 MiB of stack on Linux and macOS. On Windows a
    # check uses far less stack per level: CI measured more than 150 levels
    # of these shapes in 512 KiB. So a limit of 100 still fits.
    monkeypatch.setattr(bounded, "MAX_CHECK_DEPTH", 100)


@pytest.fixture
def hand_clock(monkeypatch: pytest.MonkeyPatch) -> _HandClock:
    # A real CPU clock moves in steps of about 15.6 ms on Windows, so a test
    # that spins for a few milliseconds can read no time, or a whole step.
    clock = _HandClock()
    monkeypatch.setattr(bounded, "cpu_clock", clock)
    return clock


def _spend_cpu(seconds: float) -> None:
    """Use ``seconds`` of CPU time on the hand clock that the test installed."""
    clock = bounded.cpu_clock
    assert isinstance(clock, _HandClock)
    clock.now += seconds


def _citry() -> Citry:
    app = Citry(secret=SIGNING_KEY, autodiscover=False)
    app.set_mounted_prefix("/citry")
    return app


# --- schemas shared by several tests ------------------------------------------


class Row(pydantic.BaseModel):
    a: int
    b: int


class Rows(pydantic.BaseModel):
    rows: list[Row]


Row20 = pydantic.create_model("Row20", **{f"f{i}": (int, ...) for i in range(20)})  # type: ignore[call-overload]


class And(pydantic.BaseModel):
    type: Literal["and"]
    items: list[And | Or | Leaf]


class Or(pydantic.BaseModel):
    type: Literal["or"]
    items: list[And | Or | Leaf]


class Leaf(pydantic.BaseModel):
    type: Literal["leaf"]
    v: int


And.model_rebuild()
Or.model_rebuild()


class Query(pydantic.BaseModel):
    q: And | Or | Leaf


# A named type that the copy wraps as a whole, used in two places.
WrappedInts = typing_extensions.TypeAliasType(  # type: ignore[misc]
    "WrappedInts", Annotated[list[int], pydantic.WrapValidator(lambda value, handler: handler(value))]
)

# A recursive type whose members are a list and a tuple, not classes.
Nested = typing_extensions.TypeAliasType("Nested", "list[Nested] | tuple[Nested, ...] | int")  # type: ignore[misc]
# The same with a dict of itself next to a class, where only the class could carry a tag.
Keyed = typing_extensions.TypeAliasType("Keyed", "dict[str, Keyed] | KeyedGroup | int")  # type: ignore[misc]


class KeyedGroup(pydantic.BaseModel):
    items: list[Keyed]


class _Calls:
    """Count the values Pydantic checked, to tell how far a validation ran before it stopped."""

    def __init__(self) -> None:
        self.count = 0

    def __call__(self, value: Any) -> Any:
        self.count += 1
        return value


def _passthrough(value: Any, handler: Any) -> Any:
    return handler(value)


# A stop comes once the errors pass the limit, so a stopped validation
# checks about that many values, however many the request sent.
STOPPED = bounded.MAX_ERRORS + 10


def _chain(depth: int, leaf: Any) -> dict[str, Any]:
    """Return a filter chain ``depth`` levels deep, one child per level, ending in ``leaf``."""
    value: dict[str, Any] = {"type": "leaf", "v": leaf}
    for _ in range(depth):
        value = {"type": "and", "items": [value]}
    return value


# --- what the copy changes -------------------------------------------------------


def test_every_pydantic_core_collection_stops_at_its_first_bad_item() -> None:
    # The set is read from pydantic-core, so a collection type added later
    # is picked up; these are the ones every supported release has. Older
    # releases build a deque or Counter as a wrap validator around a list or
    # dict, whose items the copy counts one by one instead.
    assert {"list", "set", "frozenset", "dict", "tuple"} <= bounded._FAIL_FAST_TYPES


def test_a_pydantic_list_reports_only_its_first_bad_item() -> None:
    result = validate_args(Rows, {"rows": [{}] * 50})

    assert result.fields == {"rows.0.a": "Field required", "rows.0.b": "Field required"}
    assert result.unlisted_fields == 0


def test_valid_data_gives_the_value_the_class_gives() -> None:
    payload = {"rows": [{"a": 1, "b": "2"}, {"a": 3.0, "b": 4}]}

    result = validate_args(Rows, payload)

    assert result.ok
    assert result.value == Rows.model_validate(payload)
    assert result.value.model_fields_set == {"rows"}


def test_pydantic_models_inside_a_plain_dataclass_share_one_error_total() -> None:
    # Citry calls Pydantic once per field here, and every call adds to one
    # total: 60 models of 20 missing fields each pass the limit together.
    data = dataclasses.make_dataclass("Data", [(f"r{index}", Row20) for index in range(60)])

    result = validate_args(data, {f"r{index}": {} for index in range(60)})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}


def test_typed_extras_with_many_bad_values_are_stopped() -> None:
    # Pydantic checks every extra key of an object before the object
    # returns, so each one is counted as it fails, and the check stops there.
    calls = _Calls()
    counted = Annotated[int, pydantic.BeforeValidator(calls)]

    class Extras(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="allow")
        __pydantic_extra__: dict[str, counted] = pydantic.Field(init=False)  # type: ignore[valid-type]

    result = validate_args(Extras, {f"k{index}": "x" for index in range(20_000)})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert calls.count < STOPPED


def test_typed_dict_extra_items_with_many_bad_values_are_stopped() -> None:
    calls = _Calls()

    class Open(TypedDict, extra_items=Annotated[int, pydantic.BeforeValidator(calls)]):  # type: ignore[call-arg]
        a: int

    data = pydantic.create_model("Data", f=(Open, ...))
    result = validate_args(data, {"f": {"a": 1, **{f"k{index}": "x" for index in range(20_000)}}})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert calls.count < STOPPED


def test_valid_typed_extras_give_the_value_the_class_gives() -> None:
    payload = {f"k{index}": index for index in range(3000)}

    result = validate_args(Extras, payload)

    assert result.ok
    assert result.value == Extras.model_validate(payload)


def test_many_undeclared_keys_get_one_message_for_their_object() -> None:
    class Strict(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        a: int = 0

    class Outer(pydantic.BaseModel):
        inner: Strict

    result = validate_args(Outer, {"inner": {f"k{index}": 1 for index in range(200)}})

    assert result.fields == {"inner": "This object has 200 fields that are not declared; at most 100 are allowed."}


def test_a_few_undeclared_keys_still_get_a_message_each() -> None:
    class Strict(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        a: int = 0

    result = validate_args(Strict, {"x": 1, "y": 2})

    assert result.fields == {"x": "Extra inputs are not permitted", "y": "Extra inputs are not permitted"}


def test_a_chain_of_nested_models_deeper_than_the_nesting_limit_is_refused(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Building the copy walks the schema with its own stack, so a chain of
    # 300 different models still gets a copy. Valid data 300 levels deep is
    # past the nesting limit and gets the 422 for deep data, while a missing
    # field near the top is reported before the check goes deeper.
    model: Any = pydantic.create_model("Level0", v=(int, ...))
    for index in range(1, 300):
        model = pydantic.create_model(f"Level{index}", c=(model, ...))
    payload: dict[str, Any] = {"v": 1}
    for _ in range(299):
        payload = {"c": payload}

    with caplog.at_level(logging.ERROR, logger="citry"):
        deep = validate_args(model, payload)
        missing = validate_args(model, {"c": {}})

    assert deep.fields == {"_args": bounded.TOO_DEEP_MESSAGE}
    assert missing.fields == {"c.c": "Field required"}
    # Deep data is the sender's problem, not a fault in the app, so nothing
    # is logged as an error.
    assert caplog.text == ""


_CHAIN_BUILT_ON_A_SMALL_STACK = """
import json
import threading

import pydantic

from citry.ext.events import _pydantic_bounded as bounded

model = pydantic.create_model("Level0", v=(int, ...))
for index in range(1, 300):
    model = pydantic.create_model(f"Level{index}", c=(model, ...))

built = []


def build():
    built.append(bounded.checker_for(model).validator is not None)


threading.stack_size(1024 * 1024)
thread = threading.Thread(target=build)
thread.start()
thread.join()
print(json.dumps(built))
"""


def test_the_copy_of_a_chain_of_nested_models_is_built_on_a_thread_with_a_small_stack() -> None:
    # The first call to a class builds Citry's copy of its validator on the
    # thread that serves the request, and that thread's stack can be small
    # (1 MB on Windows). Building the copy of this chain on such a stack
    # overflows it and ends the process, so the test runs it in a process
    # of its own.
    done = subprocess.run(
        [sys.executable, "-c", _CHAIN_BUILT_ON_A_SMALL_STACK],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    assert done.returncode == 0, done.stderr[-2000:]
    assert json.loads(done.stdout) == [True]


_CHECKED_AT_THE_LIMIT_ON_A_SMALL_STACK = r"""
from __future__ import annotations

import dataclasses
import json
import sys
import threading
from typing import Annotated, Literal, Optional, Union

import pydantic
import pydantic.dataclasses

from citry.ext.events import _pydantic_bounded as bounded
from citry.ext.events.schemas import validate_args

# Only the nesting limit may stop these checks, so data reaches it in every
# shape, including unions the work budget would stop sooner (see `check`).
bounded.WORK_SECONDS = 600.0


class WNode(pydantic.BaseModel):
    c: Annotated[Optional[WNode], pydantic.WrapValidator(lambda v, h: h(v))] = None
    v: int = 0


# A wrap validator on the model and another on its field: the heaviest
# shape per level measured, so it sets MAX_CHECK_DEPTH.
class MWNode(pydantic.BaseModel):
    c: Annotated[Optional[MWNode], pydantic.WrapValidator(lambda v, h: h(v))] = None
    v: int = 0

    @pydantic.model_validator(mode="wrap")
    @classmethod
    def around(cls, value, handler):
        return handler(value)


class UAnd(pydantic.BaseModel):
    type: Literal["and"]
    items: list[Union[UAnd, UOr, ULeaf]]


class UOr(pydantic.BaseModel):
    type: Literal["or"]
    any: list[Union[UAnd, UOr, ULeaf]]


class ULeaf(pydantic.BaseModel):
    type: Literal["leaf"]
    v: int


@pydantic.dataclasses.dataclass
class DAnd:
    type: Literal["and"]
    items: list[Union[DAnd, DOr, DLeaf]]


@pydantic.dataclasses.dataclass
class DOr:
    type: Literal["or"]
    any: list[Union[DAnd, DOr, DLeaf]]


@pydantic.dataclasses.dataclass
class DLeaf:
    type: Literal["leaf"]
    v: int


@dataclasses.dataclass
class PNode:
    c: Optional[Union[PNode, int]] = None


class LTree(pydantic.BaseModel):
    c: list[LTree] = []
    v: int = 0


class TAnd(pydantic.BaseModel):
    type: Literal["and"]
    items: list[Annotated[Union[TAnd, TLeaf], pydantic.Field(discriminator="type")]]


class TLeaf(pydantic.BaseModel):
    type: Literal["leaf"]
    v: int


for model in (WNode, MWNode, UAnd, UOr, LTree, TAnd):
    model.model_rebuild()
for data_class in (DAnd, DOr):
    pydantic.dataclasses.rebuild_dataclass(
        data_class, _types_namespace={"DAnd": DAnd, "DOr": DOr, "DLeaf": DLeaf}
    )


def holder(annotation):
    return pydantic.create_model("Holder", x=(annotation, ...))


# The "or" nodes hold their children under another name, so a member that
# does not match a node fails at once. With one name the check would try
# every member at every level and take seconds, while each level takes the
# same stack either way.
FIELDS = {"and": "items", "or": "any"}


def tagged(depth, leaf, tags):
    value = {"type": "leaf", "v": leaf}
    for level in range(depth):
        tag = tags[level % len(tags)]
        value = {"type": tag, FIELDS[tag]: [value]}
    return value


def chained(depth, leaf, wrap):
    value = leaf
    for _ in range(depth):
        value = wrap(value)
    return value


SHAPES = {
    "wrap validator": (holder(WNode), lambda n, leaf: chained(n, {"v": leaf}, lambda c: {"c": c})),
    "model and field wrap validators": (
        holder(MWNode),
        lambda n, leaf: chained(n, {"v": leaf}, lambda c: {"c": c}),
    ),
    "union of models": (holder(Union[UAnd, UOr, ULeaf]), lambda n, leaf: tagged(n, leaf, ("and", "or"))),
    "union of Pydantic dataclasses": (
        holder(Union[DAnd, DOr, DLeaf]),
        lambda n, leaf: tagged(n, leaf, ("and", "or")),
    ),
    "plain dataclass union": (holder(PNode), lambda n, leaf: chained(n, {"c": leaf}, lambda c: {"c": c})),
    "list of models": (holder(LTree), lambda n, leaf: chained(n, {"v": leaf}, lambda c: {"c": [c]})),
    "discriminated union": (holder(TAnd), lambda n, leaf: tagged(n, leaf, ("and",))),
}


def check(cls, payload):
    with bounded.request_work() as budget:
        budget.left = 10**12
        return validate_args(cls, payload)


def answer(cls, payload):
    return json.dumps(check(cls, payload).fields, sort_keys=True)


too_deep = json.dumps({"_args": bounded.TOO_DEEP_MESSAGE})
cases = []
for name, (cls, build) in SHAPES.items():
    # On the main thread's large stack, find the deepest data the limit
    # accepts. The next level must be refused by the limit itself.
    depth = 1
    while check(cls, {"x": build(depth + 1, 1)}).ok:
        depth += 1
    assert answer(cls, {"x": build(depth + 1, 1)}) == too_deep, name
    for payload in ({"x": build(depth, 1)}, {"x": build(depth, "bad")}, {"x": build(depth + 1, 1)}):
        cases.append((name, depth, cls, payload, answer(cls, payload)))

results = []


def check_all():
    for name, depth, cls, payload, expected in cases:
        # Name the case first, so a run that does not finish shows the last
        # case it reached.
        print(f"checking {name} at {depth} levels", file=sys.stderr, flush=True)
        results.append([name, depth, answer(cls, payload) == expected])


threading.stack_size(512 * 1024)
thread = threading.Thread(target=check_all)
thread.start()
thread.join()
print(json.dumps(results))
"""


def test_data_at_the_nesting_limit_gets_the_same_answer_on_a_thread_with_half_a_windows_stack() -> None:
    # A server thread has 1 MiB of stack on Windows and in the official
    # Python images for Alpine Linux. The nesting limit must leave half of
    # that free, so data at the limit, in shapes that take a lot of stack
    # per level, must get the same answer on a 512 KiB thread as on the
    # main thread. Valid data, data with a bad leaf, and data one level too
    # deep are each checked. The check runs in a process of its own, so a
    # thread that runs out of stack cannot affect the other tests.
    done = subprocess.run(
        [sys.executable, "-c", _CHECKED_AT_THE_LIMIT_ON_A_SMALL_STACK],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    assert done.returncode == 0, done.stderr[-2000:]
    results = json.loads(done.stdout)
    assert len(results) == 21
    assert [result for result in results if not result[2]] == []


def test_data_past_the_nesting_limit_is_refused_and_logged_once(caplog: pytest.LogCaptureFixture) -> None:
    class Node(pydantic.BaseModel):
        c: Node | None = None

    payload: dict[str, Any] = {}
    for _ in range(bounded.MAX_CHECK_DEPTH):
        payload = {"c": payload}

    with caplog.at_level(logging.WARNING, logger="citry"):
        first = validate_args(Node, payload)
        second = validate_args(Node, payload)

    assert first.fields == second.fields == {"_args": bounded.TOO_DEEP_MESSAGE}
    # Any client can send deep data again, so the warning comes once per class.
    assert caplog.text.count(f"nests more than {bounded.MAX_CHECK_DEPTH} objects") == 1


def test_a_part_that_drops_bad_items_does_not_swallow_the_nesting_limit() -> None:
    # `OnErrorOmit` drops an item on any error, Citry's stops included.
    # Without the stop kept on the tally, the data would be accepted with
    # its deep part cut off.
    class ONode(pydantic.BaseModel):
        c: list[pydantic.OnErrorOmit[ONode]] = []

    payload: dict[str, Any] = {}
    for _ in range(bounded.MAX_CHECK_DEPTH + 10):
        payload = {"c": [payload]}

    assert validate_args(ONode, payload).fields == {"_args": bounded.TOO_DEEP_MESSAGE}


@pydantic.dataclasses.dataclass
class DeepNode:
    c: DeepNode | None = None


@pydantic.dataclasses.dataclass
class DeepTreeState:
    tree: DeepNode | None = None


def test_a_dataclass_state_the_app_built_deeper_than_the_nesting_limit_restores() -> None:
    # A restore reads values the server wrote, or Citry checked when the
    # browser wrote them, so the nesting limit does not apply to it.
    value: dict[str, Any] = {}
    for _ in range(bounded.MAX_CHECK_DEPTH + 10):
        value = {"c": value}

    state = restore_state(DeepTreeState, {"tree": value})

    depth = 0
    node = state.tree
    while node is not None:
        depth += 1
        node = node.c
    assert depth == bounded.MAX_CHECK_DEPTH + 11


def test_a_copy_is_built_on_the_calling_thread_where_the_stack_size_cannot_be_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(size: int = 0) -> int:
        # What Pyodide and other platforms without settable stacks do.
        msg = "setting stack size not supported"
        raise ValueError(msg)

    monkeypatch.setattr(threading, "stack_size", refuse)
    built_on: list[int] = []

    def build() -> str:
        built_on.append(threading.get_ident())
        return "built"

    assert bounded._on_large_stack(build) == "built"
    assert built_on == [threading.get_ident()]


def test_a_forked_child_gets_a_new_build_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    # A thread of the parent may hold the lock at the fork, and the child has
    # no thread that would release it.
    held = threading.Lock()
    held.acquire()
    monkeypatch.setattr(bounded, "_BUILD_STACK_LOCK", held)

    bounded._new_build_stack_lock()

    assert bounded._BUILD_STACK_LOCK is not held
    assert bounded._on_large_stack(lambda: "built") == "built"


def test_an_error_while_building_a_copy_reaches_the_caller() -> None:
    def build() -> None:
        msg = "cannot build"
        raise TypeError(msg)

    with pytest.raises(TypeError, match="cannot build"):
        bounded._on_large_stack(build)


# --- recursive unions and the work budget -------------------------------------------


def test_a_valid_filter_chain_fourteen_levels_deep_is_accepted() -> None:
    result = validate_args(Query, {"q": _chain(14, 1)})

    assert result.ok
    assert result.value == Query.model_validate({"q": _chain(14, 1)})


@pytest.mark.usefixtures("deep_checks")
def test_a_valid_filter_chain_too_deep_to_check_is_refused_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="citry"):
        result = validate_args(Query, {"q": _chain(20, 1)})

    assert result.fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}
    assert "Query" in caplog.text
    assert "discriminator" in caplog.text


@pytest.mark.usefixtures("deep_checks")
def test_a_bad_deep_filter_chain_stops_without_walking_every_member() -> None:
    def elapsed(depth: int) -> float:
        # The best of three runs keeps one slow run of a busy machine out of
        # the comparison.
        best = float("inf")
        for _run in range(3):
            start = time.perf_counter()
            result = validate_args(Query, {"q": _chain(depth, "x")})
            best = min(best, time.perf_counter() - start)
            assert result.fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}
        return best

    # The request's work budget stops a bad chain, so 25 more levels cost
    # about the same. Past 45 levels the nesting limit refuses it first.
    assert elapsed(45) < 3 * elapsed(20) + 0.05


def test_a_discriminated_recursive_union_is_limited_only_by_the_nesting_limit() -> None:
    class TAnd(pydantic.BaseModel):
        type: Literal["and"]
        items: list[Annotated[TAnd | TLeaf, pydantic.Field(discriminator="type")]]

    class TLeaf(pydantic.BaseModel):
        type: Literal["leaf"]
        v: int

    TAnd.model_rebuild()

    class TQuery(pydantic.BaseModel):
        q: TAnd

    def chain(depth: int) -> dict[str, Any]:
        value: dict[str, Any] = {"type": "leaf", "v": 1}
        for _ in range(depth):
            value = {"type": "and", "items": [value]}
        return {"q": value}

    # Each level of a discriminated union counts once toward the nesting
    # limit, so 28 levels pass, twice the depth at which a union without a
    # discriminator stops (see the filter chain tests above). A chain past
    # the limit gets the 422 for deep data.
    assert validate_args(TQuery, chain(28)).ok
    assert validate_args(TQuery, chain(bounded.MAX_CHECK_DEPTH)).fields == {"_args": bounded.TOO_DEEP_MESSAGE}


Tree = TypeAliasType("Tree", "dict[str, Tree] | list[Tree] | int")


class Blob(pydantic.BaseModel):
    v: Tree


def test_a_recursive_union_that_reads_each_value_with_one_member_spends_nothing() -> None:
    # A JSON-like union: a dict member and a list member never read the same
    # value, so its cost grows with the data and it is not refused for size.
    payload = {"v": [[1, {"a": [2]}]] * 60_000}

    result = validate_args(Blob, payload)

    assert result.ok
    assert result.value == Blob.model_validate(payload)


def test_the_calls_of_one_request_share_one_work_budget() -> None:
    payload = {"q": _chain(14, 1)}
    results = []
    with bounded.request_work():
        results = [validate_args(Query, payload) for _ in range(16)]

    assert results[0].ok
    assert results[-1].fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}


def test_a_plain_dataclass_recursive_union_too_deep_to_check_is_refused() -> None:
    @dataclasses.dataclass
    class DAnd:
        items: list[DAnd | DOr | int]

    @dataclasses.dataclass
    class DOr:
        items: list[DAnd | DOr | int]

    @dataclasses.dataclass
    class DQuery:
        q: DAnd | DOr

    # The classes are local, so their string annotations are resolved here.
    DAnd.__annotations__ = {"items": list[DAnd | DOr | int]}
    DOr.__annotations__ = {"items": list[DAnd | DOr | int]}
    DQuery.__annotations__ = {"q": DAnd | DOr}

    value: dict[str, Any] = {"items": ["x"]}
    for _ in range(60):
        value = {"items": [value]}

    assert validate_args(DQuery, {"q": value}).fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}


@dataclasses.dataclass
class First:
    x: int


@dataclasses.dataclass
class Second:
    y: int


@dataclasses.dataclass
class FirstOrSecond:
    items: list[First | Second]


def test_a_plain_dataclass_list_of_unions_spends_nothing() -> None:
    # A union outside any other union checks each item once per member, which
    # grows only with the data, so a long list is not refused.
    result = validate_args(FirstOrSecond, {"items": [{"y": 1}] * 150_000})

    assert result.ok


class JsonCond(pydantic.BaseModel):
    value: pydantic.Json[list[int]]


@dataclasses.dataclass
class PAnd:
    op: Literal["and"]
    children: list[JsonCond | PAnd | POr]


@dataclasses.dataclass
class POr:
    op: Literal["or"]
    children: list[JsonCond | PAnd | POr]


@dataclasses.dataclass
class PFilter:
    where: JsonCond | PAnd | POr


def _plain_tree(depth: int, leaf: str) -> dict[str, Any]:
    value: dict[str, Any] = {"op": "and", "children": [{"value": leaf}]}
    for level in range(depth):
        value = {"op": "or" if level % 2 else "and", "children": [value]}
    return {"where": value}


def test_a_plain_dataclass_tree_spends_for_json_text_its_pydantic_leaf_parses() -> None:
    # A leaf deep in the tree spends for its JSON text each time Citry's
    # own check reads it.
    leaf = "[" + ",".join(["1"] * 50_000) + "]"

    assert validate_args(PFilter, _plain_tree(4, leaf)).ok
    assert validate_args(PFilter, _plain_tree(12, leaf)).fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}


def test_a_pydantic_class_outside_a_repeated_union_uses_the_ordinary_copy() -> None:
    class Cond(pydantic.BaseModel):
        value: pydantic.Json[list[int]]

    @dataclasses.dataclass
    class Holder:
        where: Cond | int

    Holder.__annotations__ = {"where": Cond | int}

    assert validate_args(Holder, {"where": {"value": "[1]"}}).ok
    # Only a check inside a union that Citry may run again needs the copy
    # whose text checks spend.
    assert Cond in bounded._CHECKERS[(False, False, False)]
    assert Cond not in bounded._CHECKERS[(False, False, True)]


@pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(strict=True))
class StrictData:
    a: int = 0
    name: str = ""


def test_a_strict_pydantic_dataclass_as_event_data_accepts_valid_data() -> None:
    result = validate_args(StrictData, {"a": 1, "name": "x"})

    assert result.value == StrictData(a=1, name="x")
    assert not validate_args(StrictData, {"a": "1"}).ok


# --- registration -----------------------------------------------------------------


def test_an_old_pydantic_is_refused_when_a_component_registers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bounded, "SUPPORTED", False)
    app = _citry()

    with pytest.raises(RuntimeError, match=r"needs Pydantic 2\.13\.0 or newer"):

        class Form(Component):
            citry = app
            template = """
              <p></p>
            """

            class Events:
                def save(self, data: Rows) -> None:
                    pass


def test_an_old_pydantic_is_refused_for_a_pydantic_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bounded, "SUPPORTED", False)
    app = _citry()

    class Counter(pydantic.BaseModel):
        count: int = 0

    with pytest.raises(RuntimeError, match=r"the State class \S*Counter is a Pydantic class"):

        class Widget(Component):
            citry = app
            State = Counter
            template = """
              <p></p>
            """


class Wrapped(pydantic.BaseModel):
    q: pydantic.Json[And | Or]


def test_a_json_field_holding_a_recursive_union_is_refused_at_registration() -> None:
    app = _citry()

    with pytest.raises(
        ValueError, match=r"the field 'q' of the event data class Wrapped holds a Json\[\.\.\.\] value with a union"
    ):

        class Search(Component):
            citry = app
            template = """
              <p></p>
            """

            class Events:
                def run(self, data: Wrapped) -> None:
                    pass


def _strict_filter_state(model: tuple[str, ...]) -> type:
    class StrictFilters(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)
        filters: list[And | Or | Leaf] = []
        _model = model

    return StrictFilters


def test_a_strict_state_whose_writable_field_holds_a_recursive_union_is_refused() -> None:
    state = _strict_filter_state(("filters",))
    app = _citry()

    with pytest.raises(ValueError, match=r"writable field 'filters' holds a union without a discriminator"):

        class Filters(Component):
            citry = app
            State = state
            template = """
              <p></p>
            """


def test_a_strict_state_whose_recursive_union_the_browser_cannot_write_is_accepted() -> None:
    state = _strict_filter_state(())
    app = _citry()

    class Filters(Component):
        citry = app
        State = state
        template = """
          <p></p>
        """

    assert Filters.State is not None


def test_a_lax_state_is_checked_in_python_mode_and_a_strict_one_as_json() -> None:
    class Lax(pydantic.BaseModel):
        filters: list[And | Or | Leaf] = []

    assert bounded.state_write_mode(Lax) == "python"
    assert bounded.state_write_mode(_strict_filter_state(())) == "json"


# --- State writes -------------------------------------------------------------------


class Settings(pydantic.BaseModel):
    tags: list[Annotated[int, pydantic.Field(gt=0)]] = []
    rows: list[Row] = []
    _model = ("tags", "rows")


def _settings_component() -> type[Component]:
    class Panel(Component):
        citry = _citry()
        State = Settings
        template = """
          <p></p>
        """

        class Events:
            def read(self, state: Any) -> dict[str, Any]:
                return {"tags": state.tags}

    return Panel


def _dispatch(comp_cls: type[Component], **call: Any) -> dict[str, Any]:
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "calls": [{"componentClassId": comp_cls.class_id, "handlerName": "read", "args": {}, **call}],
    }
    result = EventsDispatcher().dispatch(envelope, TransportContext(transport="http", citry=comp_cls.citry))
    assert isinstance(result, dict)
    [item] = result["results"]
    return cast("dict[str, Any]", item)


def _settings_token(comp_cls: type[Component]) -> str:
    state_cls = comp_cls.State
    assert state_cls is not None
    return mint_state_token(state_cls(), class_id=comp_cls.class_id, secret=SIGNING_KEY, max_age=None, max_bytes=8192)


def test_a_model_state_write_reports_the_first_bad_item() -> None:
    panel = _settings_component()

    item = _dispatch(panel, callerRenderId="i1", stateToken=_settings_token(panel), stateUpdates={"tags": [0] * 500})

    assert item["error"]["status"] == 422
    assert item["error"]["fieldErrors"] == {"tags.0": "Input should be greater than 0"}


class Extras(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, int] = pydantic.Field(init=False)


class Tagged(pydantic.BaseModel):
    meta: Extras = Extras()
    _model = ("meta",)


def test_a_model_state_write_with_too_many_errors_gets_one_message() -> None:
    state = Tagged()

    with bounded.request_work(), pytest.raises(StateUpdateError) as caught:
        apply_state_updates(state, {"meta": {f"k{index}": "x" for index in range(5000)}}, model_fields=("meta",))

    assert caught.value.fields == {"_state": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert state.meta == Extras()


def test_a_valid_model_state_write_gives_the_value_the_class_gives() -> None:
    state = Settings()

    applied = apply_state_updates(state, {"tags": [1, "2"], "rows": [{"a": 1, "b": 2}]}, model_fields=("tags", "rows"))

    assert applied == ("rows", "tags")
    assert state.tags == [1, 2]
    assert state.rows == [Row(a=1, b=2)]


def test_a_strict_state_write_reads_dates_and_tuples_from_json() -> None:
    class Strict(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)
        day: datetime.date = datetime.date(2020, 1, 1)
        pair: tuple[int, int] = (0, 0)
        _model = ("day", "pair")

    state = Strict()

    apply_state_updates(state, {"day": "2021-02-03", "pair": [1, 2]}, model_fields=("day", "pair"))

    assert state.day == datetime.date(2021, 2, 3)
    assert state.pair == (1, 2)


class Mixed(pydantic.BaseModel):
    when: datetime.date | str = "later"
    span: datetime.timedelta = datetime.timedelta(0)
    _model = ("when", "span")


def test_a_lax_state_write_takes_the_value_json_gives() -> None:
    # Python mode would keep "2021-02-03" as a str here; the token is read
    # back as JSON, which makes it a date, so the write does too.
    state = Mixed()

    apply_state_updates(state, {"when": "2021-02-03"}, model_fields=("when", "span"))

    assert state.when == datetime.date(2021, 2, 3)


def test_a_lax_state_write_refuses_what_json_refuses() -> None:
    # Python mode reads a boolean as a timedelta of one second; JSON does not.
    state = Mixed()

    with bounded.request_work(), pytest.raises(StateUpdateError) as caught:
        apply_state_updates(state, {"span": True}, model_fields=("when", "span"))

    assert caught.value.fields == {"span": "Input should be a valid duration"}


def test_a_lax_state_with_a_writable_recursive_union_is_refused() -> None:
    class Lax(pydantic.BaseModel):
        tree: And | Or | Leaf | None = None
        _model = ("tree",)

    app = _citry()

    with pytest.raises(ValueError, match=r"writable field 'tree' of the Pydantic model State .*Lax holds a union"):

        class Schedule(Component):
            citry = app
            State = Lax
            template = """
              <p></p>
            """


@pytest.mark.parametrize("tree", [Nested, Keyed], ids=["lists", "dicts"])
def test_a_state_whose_recursive_union_holds_lists_is_refused_with_a_fix_that_applies(tree: Any) -> None:
    board = pydantic.create_model("Board", tree=(tree | None, None))

    app = _citry()

    with pytest.raises(ValueError, match="callable Discriminator with a Tag") as raised:

        class Tree(Component):
            citry = app
            State = board
            template = """
              <p></p>
            """

    # A list or a tuple cannot carry a Literal tag field.
    assert "Literal" not in str(raised.value)


def test_a_lax_state_with_a_discriminated_writable_recursive_union_is_accepted() -> None:
    class TAnd(pydantic.BaseModel):
        type: Literal["and"]
        items: list[Annotated[TAnd | TLeaf, pydantic.Field(discriminator="type")]]

    class TLeaf(pydantic.BaseModel):
        type: Literal["leaf"]
        v: int

    TAnd.model_rebuild()

    class Lax(pydantic.BaseModel):
        tree: TAnd | None = None
        _model = ("tree",)

    app = _citry()

    class Schedule(Component):
        citry = app
        State = Lax
        template = """
          <p></p>
        """

    assert Schedule.State is not None


def test_a_pydantic_dataclass_state_with_validate_assignment_reports_the_first_bad_item() -> None:
    @pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(validate_assignment=True))
    class Checked:
        tags: list[Annotated[int, pydantic.Field(gt=0)]] = dataclasses.field(default_factory=list)

    state = Checked()

    with bounded.request_work(), pytest.raises(StateUpdateError) as caught:
        apply_state_updates(state, {"tags": [0] * 500}, model_fields=("tags",))

    assert caught.value.fields == {"tags.0": "Input should be greater than 0"}
    assert state.tags == []


# --- the fallback when the copy cannot be built ---------------------------------------


def test_a_copy_that_cannot_be_built_falls_back_to_the_path_limit(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    real_build = bounded._build

    def build(schema: Any, *, wrapped: bool) -> Any:
        if wrapped:
            raise RuntimeError("cannot copy")
        return real_build(schema, wrapped=wrapped)

    monkeypatch.setattr(bounded, "_build", build)

    class Forbid(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        rows: list[Row]

    with caplog.at_level(logging.ERROR, logger="citry"):
        checker = bounded.checker_for(Forbid)

    assert checker is not None
    assert checker.needs_path_limit
    assert not checker.wrapped
    assert "could not build" in caplog.text
    assert validate_args(Forbid, {"rows": [{}] * 50}).fields == {
        "rows.0.a": "Field required",
        "rows.0.b": "Field required",
    }


def test_a_recursive_union_is_refused_when_its_copy_cannot_be_built(monkeypatch: pytest.MonkeyPatch) -> None:
    def build(schema: Any, *, wrapped: bool) -> Any:
        raise RuntimeError("cannot copy")

    monkeypatch.setattr(bounded, "_build", build)

    class Again(pydantic.BaseModel):
        q: And | Or

    assert validate_args(Again, {"q": _chain(3, 1)}).fields == {"_args": bounded.NOT_CHECKABLE_MESSAGE}


# --- the size of one 422 ------------------------------------------------------------


def test_one_422_stops_listing_messages_past_its_text_limit() -> None:
    errors = FieldErrors()
    message = "x" * 5000
    for index in range(100):
        errors.add((None, f"field{index:03d}"), message)

    fields, unlisted = errors.limited()

    assert sum(len(name) + len(text) for name, text in fields.items()) <= MAX_FIELD_ERRORS_TEXT
    assert "field000" in fields
    assert len(fields) + unlisted == 100


def test_the_first_message_is_listed_however_long() -> None:
    errors = FieldErrors()
    errors.add((None, "k" * (MAX_FIELD_ERRORS_TEXT + 10)), "bad")
    errors.add((None, "z"), "also bad")

    fields, unlisted = errors.limited()

    assert list(fields.values()) == ["bad"]
    assert unlisted == 1


# --- same results as the class ----------------------------------------------------------


def _mutated(value: Any, rng: random.Random) -> Any:
    """Return ``value`` with a few parts changed at random to plausible wrong values."""
    if isinstance(value, dict):
        out = {key: _mutated(item, rng) if rng.random() < 0.3 else item for key, item in value.items()}
        if rng.random() < 0.1 and out:
            out.pop(rng.choice(sorted(out)))
        return out
    if isinstance(value, list):
        return [_mutated(item, rng) if rng.random() < 0.3 else item for item in value]
    return rng.choice([value, "x", None, -1, 1.5, [], {}, "2", True])


def test_the_copy_gives_the_class_answer_on_changed_payloads() -> None:
    class Kitchen(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        name: str
        size: Annotated[int, pydantic.Field(ge=0)] = 0
        rows: list[Row] = []
        query: And | Or | Leaf | None = None
        scores: dict[str, float] = {}
        pair: tuple[int, str] = (0, "")

        @pydantic.field_validator("name")
        @classmethod
        def _strip(cls, value: str) -> str:
            return value.strip()

    valid = {
        "name": " n ",
        "size": 3,
        "rows": [{"a": 1, "b": 2}],
        "query": _chain(2, 4),
        "scores": {"a": 1.0},
        "pair": [1, "a"],
    }
    rng = random.Random(7)  # noqa: S311 - a fixed seed makes the test repeatable
    for _ in range(600):
        payload = json.loads(json.dumps(_mutated(valid, rng)))
        try:
            expected: Any = Kitchen.model_validate(payload)
            expected_errors = None
        except pydantic.ValidationError as error:
            expected, expected_errors = None, {(tuple(e["loc"]), e["msg"]) for e in error.errors()}
        result = validate_args(Kitchen, payload)
        if expected_errors is None:
            assert result.ok, payload
            assert result.value == expected
            assert result.value.model_fields_set == expected.model_fields_set
        else:
            assert not result.ok, payload
            listed = {".".join(map(str, loc)) for loc, _ in expected_errors}
            assert set(result.fields) <= listed | {""}, payload


# --- parts that only a wrap validator lets Citry count -----------------------------------


def test_a_json_field_with_a_wrap_validator_over_a_list_is_stopped() -> None:
    # Below a wrap validator pydantic-core checks Python objects even inside
    # Json[...], so Citry counts each item there.
    calls = _Calls()
    item = Annotated[int, pydantic.BeforeValidator(calls)]
    data = pydantic.create_model(
        "Data", f=(pydantic.Json[Annotated[list[item], pydantic.WrapValidator(_passthrough)]], ...)
    )

    result = validate_args(data, {"f": json.dumps(["x"] * 20_000)})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert calls.count < STOPPED


def test_a_strict_state_write_with_a_wrap_validator_over_a_list_is_stopped() -> None:
    calls = _Calls()
    item = Annotated[int, pydantic.BeforeValidator(calls)]

    class Strict(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)
        v: Annotated[list[item], pydantic.WrapValidator(_passthrough)] = []  # type: ignore[valid-type]
        _model = ("v",)

    state = Strict()

    with bounded.request_work(), pytest.raises(StateUpdateError) as caught:
        apply_state_updates(state, {"v": ["x"] * 20_000}, model_fields=("v",))

    assert caught.value.fields == {"_state": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert calls.count < STOPPED
    assert state.v == []


def test_a_fallback_copy_counts_a_list_under_a_wrap_validator(monkeypatch: pytest.MonkeyPatch) -> None:
    real_build = bounded._build

    def build(schema: Any, *, wrapped: bool) -> Any:
        if wrapped:
            raise RuntimeError("cannot copy")
        return real_build(schema, wrapped=wrapped)

    monkeypatch.setattr(bounded, "_build", build)
    calls = _Calls()
    item = Annotated[int, pydantic.BeforeValidator(calls)]
    data = pydantic.create_model("Data", f=(Annotated[list[item], pydantic.WrapValidator(_passthrough)], ...))

    result = validate_args(data, {"f": ["x"] * 20_000})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert calls.count < STOPPED


class Ring(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True)
    day: datetime.date
    kids: list[Ring] = []


Ring.model_rebuild()


def test_a_strict_recursive_model_inside_a_json_field_reads_its_json() -> None:
    # A recursive model is a definition the copy reaches from inside and from
    # outside Json[...]; inside, it must get no wrappers, or the strict model
    # would see a Python string where JSON gives a date.
    data = pydantic.create_model("Data", f=(pydantic.Json[Ring], ...))
    payload = {"f": json.dumps({"day": "2020-01-02", "kids": [{"day": "2020-01-03"}]})}

    result = validate_args(data, payload)

    assert result.ok
    assert result.value == data.model_validate(payload)


def _drop_bad_tags(value: Any, handler: Any) -> Any:
    """Drop each tag the errors name, then check again, as a lenient app might."""
    try:
        return handler(value)
    except pydantic.ValidationError as error:
        bad = {(entry["loc"][0], entry["loc"][2]) for entry in error.errors() if entry["loc"][1:2] == ("tags",)}
        kept = [
            {**kid, "tags": [tag for index, tag in enumerate(kid["tags"]) if (number, index) not in bad]}
            for number, kid in enumerate(value)
        ]
        return handler(kept)


class TagTree(pydantic.BaseModel):
    tags: list[int] = []
    kids: Annotated[list[TagTree], pydantic.WrapValidator(_drop_bad_tags)] = []


TagTree.model_rebuild()


def test_a_wrap_validator_over_a_recursive_type_sees_every_error_below_it() -> None:
    # The recursive type is reached below the wrap validator, so its lists
    # keep reading every item there, as the class's own validator does.
    payload = {"kids": [{"tags": [1, "x", 2, "y", 3]}]}

    result = validate_args(TagTree, payload)

    assert result.ok
    assert result.value == TagTree.model_validate(payload)


ZONES = Literal[tuple(f"Zone/Number{index:03d}" for index in range(100))]  # type: ignore[valid-type]


class ZoneExtras(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, ZONES] = pydantic.Field(init=False)  # type: ignore[valid-type]


ZoneData = pydantic.create_model("ZoneData", f=(pydantic.Json[ZoneExtras], ...))


def test_a_json_field_with_typed_extras_of_a_long_literal_is_refused_at_registration() -> None:
    app = _citry()

    with pytest.raises(ValueError, match=r"holds a Json\[\.\.\.\] value with extra keys that the class allows"):

        class Zones(Component):
            citry = app
            template = """
              <p></p>
            """

            class Events:
                def save(self, data: ZoneData) -> None:  # type: ignore[valid-type]
                    pass


def test_a_strict_state_with_writable_typed_extras_of_a_long_literal_is_refused() -> None:
    class Strict(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)
        zones: ZoneExtras = ZoneExtras()
        _model = ("zones",)

    app = _citry()

    with pytest.raises(ValueError, match=r"writable field 'zones' holds extra keys that the class allows") as raised:

        class Zones(Component):
            citry = app
            State = Strict
            template = """
              <p></p>
            """

    # The message names the setting to remove as a phrase that reads on its own.
    assert "You can also remove a strict model setting, or set _model to the fields" in str(raised.value)


# --- JSON mode and Python mode ------------------------------------------------------------------

# The core schema types that hold other schemas or check no value of their
# own. Every other type pydantic-core has checks one scalar value.
_STRUCTURE_TYPES = frozenset({
    "invalid", "list", "deque", "tuple", "set", "frozenset", "generator", "dict", "frozendict", "ordered-dict",
    "counter", "function-after", "function-before", "function-wrap", "function-plain", "default", "nullable",
    "union", "tagged-union", "chain", "lax-or-strict", "json-or-python", "typed-dict", "model-fields", "model",
    "dataclass-args", "dataclass", "named-tuple", "arguments", "arguments-v3", "call", "custom-error", "json",
    "definitions", "definition-ref",
})  # fmt: skip


class _Colour(enum.Enum):
    RED = "red"


class _Size(enum.IntEnum):
    ONE = 1


def _scalar_schema(kind: str) -> Any:
    """Return a small schema of one scalar core type; a type added to pydantic-core later fails here."""
    if kind == "literal":
        return pydantic_core_schema.literal_schema(["a", 1, 1.5, True, None])
    if kind == "enum":
        return pydantic_core_schema.enum_schema(_Colour, list(_Colour), sub_type="str")
    if kind in ("is-instance", "is-subclass"):
        return {"type": kind, "cls": int}
    return {"type": kind}


# JSON-decoded values a browser can send. A lone surrogate is left out: JSON
# mode refuses the whole text at once, one error that cannot repeat.
_BROWSER_VALUES = [
    True, False, 0, 1, -1, 10**20, 1.0, 1.5, 1e300, "", "1", "a", "1.0", " 1 ", "0x10", "inf", "NaN", "1+2j",
    "2020-01-01", "2020-01-01T12:00:00", "12:00", "P1D", "https://example.com", str(uuid.UUID(int=1)), "red",
    None, [], [1], {}, {"a": 1},
]  # fmt: skip


def test_every_scalar_core_type_is_known_to_the_copy() -> None:
    scalars = set(get_args(pydantic_core_schema.CoreSchemaType)) - _STRUCTURE_TYPES

    assert scalars <= bounded._SCALAR_TYPES


def test_python_mode_accepts_more_than_json_mode_only_for_the_known_types() -> None:
    # A lax State is checked in Python mode first and read as JSON after. JSON
    # refuses a few values Python accepts, one error per value, which
    # registration's checks for the JSON read must cover. A new difference
    # shows here, so those checks can be compared with it.
    scalars = set(get_args(pydantic_core_schema.CoreSchemaType)) - _STRUCTURE_TYPES
    found = set()
    for kind in sorted(scalars):
        validator = SchemaValidator(_scalar_schema(kind))
        for value in _BROWSER_VALUES:
            try:
                validator.validate_python(value)
            except pydantic.ValidationError:
                continue
            try:
                validator.validate_json(json.dumps(value))
            except pydantic.ValidationError:
                found.add(kind)

    # An older pydantic-core may lack a type, or check it with a Python
    # function that reads both modes alike.
    assert found == {"timedelta", "fraction", "complex", "is-instance"} & scalars


class Aliased(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    first: int = pydantic.Field(0, alias="f")


class AliasState(pydantic.BaseModel):
    inner: Aliased = Aliased.model_validate({})
    _model = ("inner",)


def test_a_state_with_a_forbidding_model_and_an_alias_is_checked_as_json() -> None:
    # Reading by field name, JSON mode drops an alias key that Python mode
    # refuses as extra, so such a State is read only as JSON.
    assert bounded.state_write_mode(AliasState) == "json"


def test_a_state_write_with_an_alias_key_under_a_forbidding_model_takes_the_json_answer() -> None:
    state = AliasState()
    write = {"inner": {"f": 5}}

    with bounded.request_work():
        apply_state_updates(state, write, model_fields=("inner",))

    assert state.inner == AliasState.model_validate_json(json.dumps(write), by_alias=False, by_name=True).inner


# --- valid data with errors thrown away -------------------------------------------------------------


class IntExtras(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, int] = pydantic.Field(init=False)
    kind: Literal["ints"] = "ints"


class StrExtras(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, str] = pydantic.Field(init=False)


class EitherExtras(pydantic.BaseModel):
    u: IntExtras | StrExtras


def test_a_union_member_with_many_errors_does_not_refuse_a_value_another_member_accepts() -> None:
    payload = {"u": {f"k{index}": "x" for index in range(3000)}}

    result = validate_args(EitherExtras, payload)

    assert result.ok
    assert result.value == EitherExtras.model_validate(payload)


Wide = pydantic.create_model("Wide", **{f"f{i}": (int, ...) for i in range(20)})  # type: ignore[call-overload]
Narrow = pydantic.create_model("Narrow", b=(int, ...))


def test_a_long_key_elsewhere_does_not_refuse_a_union_another_member_accepts() -> None:
    # A long key lowers the error limit below the first member's 20 errors,
    # which the union throws away when the second member accepts.
    data = pydantic.create_model("Data", u=(Wide | Narrow, ...), notes=(dict[str, str], {}))
    payload = {"u": {"b": 1}, "notes": {"k" * 300_000: "x"}}

    result = validate_args(data, payload)

    assert result.ok
    assert result.value == data.model_validate(payload)


def test_a_plain_dataclass_union_of_pydantic_models_throws_failed_members_errors_away() -> None:
    @dataclasses.dataclass
    class Data:
        u: Wide | Narrow  # type: ignore[valid-type]
        notes: dict[str, str]

    result = validate_args(Data, {"u": {"b": 1}, "notes": {"k" * 300_000: "x"}})

    assert result.ok
    assert result.value.u == Narrow(b=1)


def _keep_or_empty(value: Any, handler: Any) -> Any:
    try:
        return handler(value)
    except pydantic.ValidationError:
        return []


def test_a_wrap_validator_that_recovers_from_too_many_errors_is_refused() -> None:
    # The errors below a wrap validator count while it runs, since Pydantic
    # holds them all; past the limit the call stops, even if the validator
    # would have caught them.
    data = pydantic.create_model("Data", f=(Annotated[list[int], pydantic.WrapValidator(_keep_or_empty)], ...))

    assert validate_args(data, {"f": ["x"] * 900}).ok
    assert validate_args(data, {"f": ["x"] * 2000}).fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}


# --- Citry's own validator ----------------------------------------------------------------------------


@dataclasses.dataclass
class PlainRow:
    a: int
    b: int


@dataclasses.dataclass
class PlainRows:
    rows: list[PlainRow]


def test_a_plain_dataclass_list_reports_only_its_first_bad_item() -> None:
    result = validate_args(PlainRows, {"rows": [{}] * 50_000})

    assert result.fields == {"rows.0.a": "This field is required.", "rows.0.b": "This field is required."}


@pydantic.dataclasses.dataclass
class PydanticRow:
    a: int
    b: int


@pydantic.dataclasses.dataclass
class PydanticRows:
    v: list[PydanticRow]


@pydantic.dataclasses.dataclass
class PositiveRow:
    a: Annotated[int, pydantic.Field(gt=0)]
    b: Annotated[int, pydantic.Field(gt=0)]


@pydantic.dataclasses.dataclass
class PositiveRows:
    v: list[PositiveRow]


def test_a_pydantic_dataclass_list_reports_only_its_first_bad_item() -> None:
    # Each item is its own object, as a decoded request's items are.
    result = validate_args(PydanticRows, {"v": [{} for _ in range(50_000)]})

    assert result.fields == {"v.0.a": "This field is required.", "v.0.b": "This field is required."}


def test_a_pydantic_dataclass_list_whose_items_fail_pydantics_own_checks_answers_422() -> None:
    # Citry's own check accepts every item, so Pydantic's checks fail them
    # one by one. The call answers with the first bad item, and no
    # `ValidationError` escapes.
    result = validate_args(PositiveRows, {"v": [{"a": 0, "b": 0} for _ in range(50_000)]})

    assert not result.ok
    assert result.fields == {"v.0.a": "Input should be greater than 0", "v.0.b": "Input should be greater than 0"}


def test_citry_own_messages_count_toward_the_error_limit() -> None:
    result = validate_args(PlainRow, {"a": 1, "b": 2, **{f"k{index}": 1 for index in range(5000)}})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}


# --- the request's work budget -------------------------------------------------------------------------


def test_a_task_started_during_a_request_gets_its_own_budget_after_the_request_ends() -> None:
    async def later() -> bool:
        await asyncio.sleep(0)
        return validate_args(Query, {"q": _chain(14, 1)}).ok

    loop = asyncio.new_event_loop()
    try:
        with bounded.request_work() as budget:
            budget.left = 0
            task = loop.create_task(later())
        assert loop.run_until_complete(task)
    finally:
        loop.close()


class Twice(pydantic.BaseModel):
    """A recursive model whose wrap validator checks each value twice."""

    kid: Twice | None = None

    @pydantic.model_validator(mode="wrap")
    @classmethod
    def twice(cls, value: Any, handler: Any) -> Any:
        handler(value)
        return handler(value)


def _twice_chain(depth: int) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for _ in range(depth):
        value = {"kid": value}
    return value


@pytest.mark.usefixtures("deep_checks")
def test_a_state_write_too_deep_to_check_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    # Below a wrap validator Citry's wrappers run in the JSON read too, so
    # such a State registers and its writes run on the work budget.
    class Lax(pydantic.BaseModel):
        q: Twice | None = None
        _model = ("q",)

    state = Lax()

    with caplog.at_level(logging.WARNING, logger="citry"), bounded.request_work() as budget:
        # A small step budget, so the steps run out long before the CPU
        # limit on any machine, and the test checks the step budget.
        budget.left = 200_000
        with pytest.raises(StateUpdateError):
            apply_state_updates(state, {"q": _twice_chain(30)}, model_fields=("q",))

    assert "Lax was refused because checking it took more work" in caplog.text
    assert "discriminator" in caplog.text


# --- registration on an older Pydantic -------------------------------------------------------------------


@dataclasses.dataclass
class Holder:
    rows: list[Row]


def test_an_old_pydantic_is_refused_for_a_pydantic_class_inside_a_plain_dataclass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bounded, "SUPPORTED", False)
    app = _citry()

    with pytest.raises(RuntimeError, match=r"holds Row, which is a Pydantic class"):

        class Form(Component):
            citry = app
            template = """
              <p></p>
            """

            class Events:
                def save(self, data: Holder) -> None:
                    pass


# --- Pydantic's signals through Citry's wrappers ---------------------------------------------------


class OmitUnderWrap(pydantic.BaseModel):
    items: list[pydantic.OnErrorOmit[int]]

    @pydantic.model_validator(mode="wrap")
    @classmethod
    def around(cls, value: Any, handler: Any) -> Any:
        return handler(value)


def _default_if_negative(value: Any, handler: Any) -> Any:
    if isinstance(value, int) and value < 0:
        raise pydantic_core.PydanticUseDefault
    return handler(value)


class DefaultOnNegative(pydantic.BaseModel):
    x: Annotated[int, pydantic.WrapValidator(_default_if_negative)] = 5
    # A recursive field gives the copy its counting wrappers.
    kid: DefaultOnNegative | None = None


def test_an_item_dropped_on_error_under_a_wrap_validator_is_dropped() -> None:
    data = pydantic.create_model("Data", m=(OmitUnderWrap, ...))

    result = validate_args(data, {"m": {"items": [1, "x", 3]}})

    assert result.ok
    assert result.value.m.items == [1, 3]


def test_a_wrap_validator_that_asks_for_the_default_gets_it() -> None:
    data = pydantic.create_model("Data", m=(DefaultOnNegative, ...))

    result = validate_args(data, {"m": {"x": -1, "kid": {"x": -2}}})

    assert result.ok
    assert result.value.m == DefaultOnNegative.model_validate({"x": -1, "kid": {"x": -2}})


def test_an_item_dropped_on_error_in_a_state_read_as_json_is_dropped() -> None:
    class Strict(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)
        m: OmitUnderWrap = OmitUnderWrap(items=[])
        _model = ("m",)

    state = Strict()

    with bounded.request_work():
        apply_state_updates(state, {"m": {"items": [1, "x", 3]}}, model_fields=("m",))

    assert state.m.items == [1, 3]


def test_a_signal_that_escapes_the_authors_own_wrap_validator_fails_as_in_the_class() -> None:
    # The class raises pydantic-core's SchemaError when the drop signal leaves
    # the author's own handler, and the copy must not turn it into a drop.
    class Odd(pydantic.BaseModel):
        items: list[Annotated[pydantic.OnErrorOmit[int], pydantic.WrapValidator(_passthrough)]]
        kid: Odd | None = None

    payload = {"items": [1, "x"]}
    with pytest.raises(pydantic_core.SchemaError):
        Odd.model_validate(payload)
    checker = bounded.checker_for(Odd)
    assert checker is not None

    with pytest.raises(pydantic_core.SchemaError):
        bounded.validate_python(checker, payload)


# --- every collection under a wrap validator is counted ----------------------------------------------

# Schema keys that hold one schema per item the payload sends. Every other
# key that holds a schema holds one per position or one in all.
_PER_ITEM_KEYS = frozenset({
    "items_schema", "keys_schema", "values_schema", "extras_schema", "extras_keys_schema", "var_args_schema",
    "var_kwargs_schema", "arguments_schema",
})  # fmt: skip
_ONE_SCHEMA_KEYS = frozenset({
    "schema", "steps", "choices", "lax_schema", "strict_schema", "json_schema", "python_schema", "fields",
    "return_schema", "definitions", "json_schema_input_schema", "computed_fields",
})  # fmt: skip


def _schema_valued_keys() -> dict[str, set[str]]:
    """Return, for each core schema type, the keys of its TypedDict that hold schemas."""
    found: dict[str, set[str]] = {}
    for value in vars(pydantic_core_schema).copy().values():
        annotations = getattr(value, "__annotations__", None)
        if not (isinstance(value, type) and annotations and "type" in annotations):
            continue
        kind = re.search(r"Literal\[['\"]([a-z0-9-]+)['\"]\]", str(annotations["type"]))
        if kind is None:
            continue
        keys = {
            key
            for key, hint in annotations.items()
            if "CoreSchema" in str(hint) or "Field]" in str(hint) or "Parameter]" in str(hint)
        }
        found[kind.group(1)] = keys - {"serialization", "metadata"}
    return found


def test_every_core_schema_key_that_holds_a_schema_per_item_is_counted() -> None:
    # A new collection type or key in pydantic-core shows here, so the copy
    # can be taught to count its items under a wrap validator.
    unknown = {
        f"{kind}.{key}"
        for kind, keys in _schema_valued_keys().items()
        for key in keys
        if key not in _PER_ITEM_KEYS | _ONE_SCHEMA_KEYS
    }
    assert unknown == set()
    for kind, keys in _schema_valued_keys().items():
        per_item = keys & _PER_ITEM_KEYS
        if not per_item:
            continue
        if per_item <= {"items_schema", "keys_schema", "values_schema"}:
            # A generator reads its items only when the handler iterates it,
            # after the validation, one error at a time.
            assert kind in bounded._FAIL_FAST_TYPES or kind == "generator", kind
            assert per_item <= set(bounded._ITEM_KEYS), kind
        elif kind == "arguments-v3":
            assert "arguments_schema" in per_item
        elif kind in ("arguments", "call"):
            # `arguments_schema` of `arguments` lists fixed parameters;
            # `call` holds an `arguments` schema.
            assert per_item - {"arguments_schema"} <= set(bounded._EXTRAS_KEYS), kind
        else:
            assert per_item <= set(bounded._EXTRAS_KEYS), kind


def test_every_collection_type_counts_each_item_schema_under_a_wrap_validator() -> None:
    # Built from the raw schema of each collection type pydantic-core has, so
    # a type whose item schemas sit in another shape (a tuple holds a list of
    # them) shows here.
    for kind in sorted(bounded._FAIL_FAST_TYPES):
        keys = _schema_valued_keys()[kind] & {"items_schema", "keys_schema", "values_schema"}
        node: dict[str, Any] = {"type": kind}
        for key in keys:
            node[key] = pydantic_core_schema.int_schema()
        if kind == "tuple":
            node["items_schema"] = [pydantic_core_schema.str_schema(), pydantic_core_schema.int_schema()]
            node["variadic_item_index"] = 1
        raw = pydantic_core_schema.no_info_wrap_validator_function(_passthrough, node)

        copied = bounded._Rewriter(bounded._Schema(raw), wrapped=True).rewrite(raw)["schema"]["schema"]

        for key in keys:
            items = copied[key] if type(copied[key]) is list else [copied[key]]
            assert [item["function"]["function"] for item in items] == [bounded._counted] * len(items), (kind, key)


def _counted_item(calls: _Calls) -> Any:
    return Annotated[int, pydantic.BeforeValidator(calls)]


def _counted_key(calls: _Calls) -> Any:
    return Annotated[int, pydantic.BeforeValidator(calls)]


_COLLECTIONS: list[tuple[str, Any, Any]] = [
    ("list", lambda item: list[item], lambda n: ["x"] * n),
    ("variadic tuple", lambda item: tuple[item, ...], lambda n: ["x"] * n),
    ("set", lambda item: set[item], lambda n: [f"x{i}" for i in range(n)]),
    ("frozenset", lambda item: frozenset[item], lambda n: [f"x{i}" for i in range(n)]),
    ("deque", lambda item: collections.deque[item], lambda n: ["x"] * n),
    ("sequence", lambda item: Sequence[item], lambda n: ["x"] * n),
    ("dict values", lambda item: dict[str, item], lambda n: {f"k{i}": "x" for i in range(n)}),
    ("dict keys", lambda item: dict[item, int], lambda n: {f"k{i}": 0 for i in range(n)}),
    ("mapping values", lambda item: Mapping[str, item], lambda n: {f"k{i}": "x" for i in range(n)}),
    ("counter keys", lambda item: collections.Counter[item], lambda n: {f"k{i}": 1 for i in range(n)}),
    (
        "ordered dict values",
        lambda item: collections.OrderedDict[str, item],
        lambda n: {f"k{i}": "x" for i in range(n)},
    ),
    ("optional list", lambda item: list[item] | None, lambda n: ["x"] * n),
    ("list in a list", lambda item: list[list[item]], lambda n: [["x"] * n]),
]


@pytest.mark.parametrize(("label", "shape", "payload"), _COLLECTIONS, ids=[row[0] for row in _COLLECTIONS])
def test_every_collection_under_a_wrap_validator_stops_at_the_error_limit(
    label: str, shape: Any, payload: Any
) -> None:
    calls = _Calls()
    data = pydantic.create_model(
        "Data", f=(Annotated[shape(_counted_item(calls)), pydantic.WrapValidator(_passthrough)], ...)
    )

    result = validate_args(data, {"f": payload(5_000)})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}, label
    assert calls.count < STOPPED, label


def test_a_variadic_tuple_under_a_wrap_validator_inside_json_is_stopped() -> None:
    # The copy for JSON text holds wrappers below a wrap validator too.
    calls = _Calls()
    shape = Annotated[tuple[_counted_item(calls), ...], pydantic.WrapValidator(_passthrough)]  # type: ignore[misc]
    data = pydantic.create_model("Data", f=(pydantic.Json[shape], ...))

    result = validate_args(data, {"f": json.dumps(["x"] * 5_000)})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert calls.count < STOPPED


def test_a_variadic_tuple_under_a_wrap_validator_in_a_state_write_is_stopped() -> None:
    calls = _Calls()

    class Lax(pydantic.BaseModel):
        v: Annotated[tuple[_counted_item(calls), ...], pydantic.WrapValidator(_passthrough)] = ()  # type: ignore[valid-type]
        _model = ("v",)

    with bounded.request_work(), pytest.raises(StateUpdateError) as caught:
        apply_state_updates(Lax(), {"v": ["x"] * 5_000}, model_fields=("v",))

    assert caught.value.fields == {"_state": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert calls.count < STOPPED


def test_a_tuple_with_fixed_positions_and_a_variadic_tail_counts_each_item_schema() -> None:
    # Pydantic writes `tuple[str, *tuple[int, ...]]` this way; the class
    # syntax for it differs between Python versions, so the schema is built here.
    raw = pydantic_core_schema.no_info_wrap_validator_function(
        _passthrough,
        pydantic_core_schema.tuple_schema(
            [pydantic_core_schema.str_schema(), pydantic_core_schema.int_schema()], variadic_item_index=1
        ),
    )
    copied = bounded._Rewriter(bounded._Schema(raw), wrapped=True).rewrite(raw)

    items = copied["schema"]["schema"]["items_schema"]
    assert [item["type"] for item in items] == ["function-wrap", "function-wrap"]
    assert [item["schema"]["type"] for item in items] == ["str", "int"]


def _drop_bad(value: Any, handler: Any) -> Any:
    """Keep the items of a JSON list that pass, as an app's wrap validator might."""
    try:
        return handler(value)
    except pydantic.ValidationError as err:
        bad = {error["loc"][0] for error in err.errors() if error["loc"]}
        return [item for index, item in enumerate(json.loads(value)) if index not in bad]


def test_a_list_inside_json_below_a_wrap_validator_hands_it_every_bad_item() -> None:
    data = pydantic.create_model(
        "Data", f=(Annotated[pydantic.Json[list[int]], pydantic.WrapValidator(_drop_bad)], ...)
    )
    payload = {"f": '[1, "x", 2, "y", 3]'}

    _register_data(data)
    result = validate_args(data, payload)

    assert result.ok
    assert result.value == data.model_validate(payload)
    assert result.value.f == [1, 2, 3]  # type: ignore[attr-defined]


def test_a_wrap_validator_that_recovers_from_too_many_bad_items_inside_json_is_refused() -> None:
    data = pydantic.create_model(
        "Data", f=(Annotated[pydantic.Json[list[int]], pydantic.WrapValidator(_drop_bad)], ...)
    )

    _register_data(data)
    tracemalloc.start()
    try:
        result = validate_args(data, {"f": json.dumps(["x"] * 200_000)})
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert peak < 16_000_000


BigEnum = enum.Enum("BigEnum", {f"v{i}": f"v{i}" for i in range(500)})  # type: ignore[misc]


@pytest.mark.parametrize(
    "items", [list[Row], dict[str, Row], list[BigEnum]], ids=["models", "model-values", "long-enum"]
)
def test_a_list_or_dict_inside_json_below_a_wrap_validator_whose_items_fail_more_than_once_is_refused(
    items: Any,
) -> None:
    data = pydantic.create_model("Data", f=(Annotated[pydantic.Json[items], pydantic.WrapValidator(_drop_bad)], ...))

    with pytest.raises(ValueError, match=r"holds a Json\[\.\.\.\] value with a wrap validator around it"):
        _register_data(data)


@pytest.mark.parametrize(
    ("items", "text"),
    [
        (dict[Annotated[str, pydantic.Field(max_length=3)], int], '{"a": 1, "long": 2, "b": "x"}'),
        (list[list[int]], '[[1, "x"], "y", [2]]'),
        (list[int | str], '[1, "a", [], {}]'),
        (dict[int, int], '{"1": 1, "x": 2, "3": "y"}'),
        (list[pydantic.AnyUrl], '["http://a.com", "nope", 3]'),
        (list[datetime.date], '["2020-01-01", "x", 1e20]'),
    ],
    ids=["limited-keys", "nested-lists", "scalar-union", "int-keys", "urls", "dates"],
)
def test_a_list_or_dict_inside_json_below_a_wrap_validator_whose_items_fail_once_matches_the_class(
    items: Any, text: str
) -> None:
    data = pydantic.create_model("Data", f=(Annotated[pydantic.Json[items], pydantic.WrapValidator(_view)], ...))

    _register_data(data)

    # The wrap validator sees every error the class gives it, item by item.
    assert validate_args(data, {"f": text}).value == data.model_validate({"f": text})


@pytest.mark.parametrize(
    "items",
    [dict[str, list[datetime.date]], dict[str, dict[str, decimal.Decimal]], list[dict[str, list[pydantic.AnyUrl]]]],
    ids=["dates-below-a-key", "decimals-below-a-key", "urls-below-a-key"],
)
def test_items_that_are_not_counted_below_a_key_inside_json_below_a_wrap_validator_are_refused(items: Any) -> None:
    data = pydantic.create_model("Data", f=(Annotated[pydantic.Json[items], pydantic.WrapValidator(_view)], ...))

    # Each error below a key carries that key, which the text can make long.
    with pytest.raises(ValueError, match=r"a list or dict inside a dict in that text whose items are not plain"):
        _register_data(data)


def test_counted_items_below_a_key_inside_json_below_a_wrap_validator_register() -> None:
    data = pydantic.create_model(
        "Data", f=(Annotated[pydantic.Json[dict[str, list[int]]], pydantic.WrapValidator(_drop_bad)], ...)
    )

    _register_data(data)
    result = validate_args(data, {"f": json.dumps({"k" * 10_000: ["x"] * 5_000})})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}


@pytest.mark.parametrize(
    "items", [datetime.time | str | None, int | str | uuid.UUID], ids=["time-or-text", "uuid-or-text"]
)
def test_a_union_with_a_time_or_uuid_inside_json_below_a_wrap_validator_is_refused(items: Any) -> None:
    data = pydantic.create_model(
        "Data",
        f=(Annotated[pydantic.Json[list[items]], pydantic.WrapValidator(_view)], ...),  # type: ignore[valid-type]
    )

    # Such a union gives one error per member for each item, and JSON and
    # Python pick its member differently, so no wrapper can count it.
    with pytest.raises(ValueError, match=r"holds a Json\[\.\.\.\] value with a wrap validator around it"):
        _register_data(data)


def test_the_refusal_of_a_union_of_items_below_a_wrap_validator_names_the_union_and_a_fix_that_registers() -> None:
    wrap = pydantic.WrapValidator(_view)
    refused = pydantic.create_model(
        "Data", f=(Annotated[pydantic.Json[list[datetime.date | datetime.time | None]], wrap], ...)
    )
    fixed = pydantic.create_model("Data", f=(Annotated[pydantic.Json[list[datetime.date | None]], wrap], ...))

    # Each member alone fails with one short message, so the message must
    # say that the union is what Citry refuses.
    with pytest.raises(ValueError, match=r"a union of several types") as raised:
        _register_data(refused)
    assert "not a union of several types. A union with None is fine" in str(raised.value)
    _register_data(fixed)


def test_a_union_of_plain_json_types_inside_json_below_a_wrap_validator_keeps_the_class_value() -> None:
    data = pydantic.create_model(
        "Data", f=(Annotated[pydantic.Json[list[int | str | None]], pydantic.WrapValidator(_view)], ...)
    )
    payload = {"f": '["10:20:30", 1, null, 1.5, []]'}

    _register_data(data)

    assert validate_args(data, payload).value == data.model_validate(payload)


def _view(value: Any, handler: Any) -> Any:
    try:
        return handler(value)
    except pydantic.ValidationError as err:
        return [(error["type"], error["loc"], error["msg"]) for error in err.errors()]


@pytest.mark.parametrize(
    ("item", "bad"),
    [(uuid.UUID, '"x"'), (int | str, "[]"), (datetime.date, '"x"'), (decimal.Decimal, '"x"')],
    ids=["uuid", "scalar-union", "date", "decimal"],
)
def test_a_wrap_validator_that_recovers_from_too_many_bad_items_of_any_short_type_is_refused(
    item: Any, bad: str
) -> None:
    data = pydantic.create_model(
        "Data", f=(Annotated[pydantic.Json[list[item]], pydantic.WrapValidator(_drop_bad)], ...)
    )

    _register_data(data)
    result = validate_args(data, {"f": "[" + ",".join([bad] * 20_000) + "]"})

    # Items read alike from JSON and Python are counted one by one; others
    # are counted as the text fails, before the author's function sees them.
    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}


@pytest.mark.parametrize(
    "config",
    [{"coerce_numbers_to_str": True}, {}],
    ids=["model-setting", "field-setting"],
)
def test_a_json_list_of_strings_that_takes_numbers_keeps_the_class_value(config: dict[str, Any]) -> None:
    field = str if config else Annotated[str, pydantic.Field(coerce_numbers_to_str=True)]
    data = pydantic.create_model(
        "Data",
        __config__=pydantic.ConfigDict(**config),
        f=(Annotated[pydantic.Json[list[field]], pydantic.WrapValidator(_passthrough)], ...),  # type: ignore[valid-type]
    )
    payload = {"f": "[1E2, -0.0, 1e20, 5]"}

    _register_data(data)

    # JSON mode writes each number from its text, so the copy leaves these
    # items to the JSON read rather than handing them the decoded float.
    assert validate_args(data, payload).value.f == ["100", "-0", "100000000000000000000", "5"]  # type: ignore[union-attr]
    assert validate_args(data, payload).value == data.model_validate(payload)


def test_a_dict_of_short_values_inside_json_below_a_wrap_validator_registers() -> None:
    data = pydantic.create_model(
        "Data", f=(Annotated[pydantic.Json[dict[str, int]], pydantic.WrapValidator(_passthrough)], ...)
    )

    _register_data(data)
    result = validate_args(data, {"f": json.dumps({"a": "x", "b": 1, "c": "y"})})

    assert sorted(result.fields) == ["f.a", "f.c"]


def test_a_json_list_in_a_model_with_a_wrap_model_validator_registers() -> None:
    class WrapJson(pydantic.BaseModel):
        f: pydantic.Json[list[int]]

        @pydantic.model_validator(mode="wrap")
        @classmethod
        def around(cls, value: Any, handler: Any) -> Any:
            return handler(value)

    _register_data(WrapJson)

    assert validate_args(WrapJson, {"f": "[1, 2]"}).ok


# --- typed extra keys where nothing counts them ------------------------------------------------------


Wide3 = pydantic.create_model("Wide3", **{f"f{i}": (int, ...) for i in range(3)})  # type: ignore[call-overload]


class ModelExtras(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, Wide3] = pydantic.Field(init=False)  # type: ignore[valid-type]


class ScalarUnionExtras(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, int | float | datetime.date] = pydantic.Field(init=False)


class ShortExtras(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, int | None] = pydantic.Field(init=False)


def _register_data(data_cls: type) -> type[Component]:
    """Define a component whose one handler takes ``data_cls``, so registration checks it."""

    def save(self: Any, data: Payload) -> None:  # type: ignore[name-defined] # noqa: F821
        pass

    events = type("Events", (), {"save": save})
    template = """
      <p></p>
    """
    # Citry resolves a handler's `data` annotation among the component's
    # nested classes too, which is where a class local to a test can go.
    namespace = {"citry": _citry(), "Events": events, "Payload": data_cls, "template": template}
    return cast("type[Component]", type("Form", (Component,), namespace))


@pytest.mark.parametrize("extras", [ModelExtras, ScalarUnionExtras], ids=["model", "union of scalars"])
def test_json_typed_extras_that_can_fail_with_several_errors_are_refused(extras: type) -> None:
    data = pydantic.create_model("Data", f=(pydantic.Json[extras], ...))

    with pytest.raises(
        ValueError,
        match=r"the field 'f' of the event data class Data holds a Json\[\.\.\.\] value with extra keys",
    ):
        _register_data(data)


def test_json_typed_extras_that_fail_with_one_short_error_register() -> None:
    data = pydantic.create_model("Data", f=(pydantic.Json[ShortExtras], ...))

    _register_data(data)

    assert validate_args(data, {"f": json.dumps({"a": 1, "b": None})}).ok


def test_a_lax_state_with_writable_typed_extras_of_a_long_literal_registers() -> None:
    # The Python check counts them, and the JSON read meets only what it accepted.
    class Lax(pydantic.BaseModel):
        zones: ZoneExtras = ZoneExtras()
        _model = ("zones",)

    app = _citry()

    class Map(Component):
        citry = app
        State = Lax
        template = """
          <p></p>
        """

    assert Map.State is not None


def test_a_lax_state_with_long_literal_extras_inside_a_union_member_is_refused() -> None:
    class Lax(pydantic.BaseModel):
        zones: ZoneExtras | dict[str, int] = {}
        _model = ("zones",)

    app = _citry()

    with pytest.raises(
        ValueError, match=r"writable field 'zones' of .* holds extra keys that the class allows.*inside a union member"
    ):

        class Map(Component):
            citry = app
            State = Lax
            template = """
              <p></p>
            """


def test_a_state_whose_json_field_the_browser_cannot_write_registers_and_takes_writes() -> None:
    class Board(pydantic.BaseModel):
        saved: pydantic.Json[And | Or] | None = None
        title: str = ""
        _model = ("title",)

    app = _citry()

    class Panel(Component):
        citry = app
        State = Board
        template = """
          <p></p>
        """

    state = Board()
    with bounded.request_work():
        apply_state_updates(state, {"title": "new"}, model_fields=("title",))

    assert state.title == "new"


# --- State writes read keys by field name ------------------------------------------------------------


class Person(pydantic.BaseModel):
    user_name: str = pydantic.Field(alias="userName")
    # A recursive field gives the copy its counting wrappers.
    kids: list[Person] = []


def test_a_lax_state_write_to_an_aliased_nested_field_by_name_is_accepted() -> None:
    # pydantic-core 2.46 (Pydantic 2.13.0) forgets the by-name setting below
    # each Citry wrapper, so this needs the copy that drops the aliases.
    class People(pydantic.BaseModel):
        boss: Person | None = None
        _model = ("boss",)

    state = People()

    with bounded.request_work():
        apply_state_updates(state, {"boss": {"user_name": "a", "kids": [{"user_name": "k"}]}}, model_fields=("boss",))

    assert state.boss is not None
    assert state.boss.kids[0].user_name == "k"


def test_below_the_authors_wrap_validator_keys_are_read_as_the_class_reads_them() -> None:
    class Wrapped(pydantic.BaseModel):
        inner: Person

        @pydantic.model_validator(mode="wrap")
        @classmethod
        def around(cls, value: Any, handler: Any) -> Any:
            return handler(value)

    payload = {"inner": {"user_name": "a"}}
    checker = bounded.checker_for(Wrapped, state=True, by_name=True)
    assert checker is not None

    def outcome(check: Any) -> Any:
        try:
            return check().model_dump()
        except pydantic.ValidationError as err:
            return [error["loc"] for error in err.errors()]

    with bounded.request_work():
        copy = outcome(lambda: bounded.validate_python(checker, payload, by_alias=False, by_name=True))
    assert copy == outcome(lambda: Wrapped.model_validate(payload, by_alias=False, by_name=True))


# --- data nested deeper than Python can follow ------------------------------------------------------


def test_running_out_of_python_frames_gets_the_too_deep_message() -> None:
    def deep(value: Any) -> Any:
        raise RecursionError

    data = pydantic.create_model("Data", f=(Annotated[int, pydantic.AfterValidator(deep)], ...))

    assert validate_args(data, {"f": 1}).fields == {"_args": bounded.TOO_DEEP_MESSAGE}


# --- the work budget counts the size of what is checked again ----------------------------------------


class PadA(pydantic.BaseModel):
    child: PadA | PadB | None = None
    x: int
    pad: list[int] = []


class PadB(pydantic.BaseModel):
    child: PadA | PadB | None = None
    y: int
    pad: list[int] = []


PadA.model_rebuild()


def _padded_chain(depth: int, size: int) -> dict[str, Any]:
    value: dict[str, Any] = {"y": 1, "pad": [0] * size}
    for _ in range(depth):
        value = {"y": 1, "child": value}
    return value


def test_a_deep_union_over_a_large_leaf_spends_the_budget() -> None:
    data = pydantic.create_model("Data", q=(PadA | PadB, ...))

    result = validate_args(data, {"q": _padded_chain(10, 300_000)})

    assert result.fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}


def test_the_same_shallow_tree_with_a_large_leaf_is_accepted() -> None:
    data = pydantic.create_model("Data", q=(PadA | PadB, ...))
    payload = {"q": _padded_chain(2, 300_000)}

    result = validate_args(data, payload)

    assert result.ok
    assert result.value == data.model_validate(payload)


def test_a_wrap_validator_that_calls_its_handler_twice_spends_for_each_call() -> None:
    class TwicePad(pydantic.BaseModel):
        kid: TwicePad | None = None
        pad: list[int] = []

        @pydantic.model_validator(mode="wrap")
        @classmethod
        def twice(cls, value: Any, handler: Any) -> Any:
            handler(value)
            return handler(value)

    value: dict[str, Any] = {"pad": [0] * 50_000}
    for _ in range(8):
        value = {"kid": value}
    data = pydantic.create_model("Data", q=(TwicePad, ...))

    assert validate_args(data, {"q": value}).fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}


def test_citry_own_union_check_spends_for_the_value_it_checks_again(caplog: pytest.LogCaptureFixture) -> None:
    @dataclasses.dataclass
    class DA:
        child: DA | DB | None
        x: int
        pad: list[int] = dataclasses.field(default_factory=list)

    @dataclasses.dataclass
    class DB:
        child: DA | DB | None
        y: int
        pad: list[int] = dataclasses.field(default_factory=list)

    @dataclasses.dataclass
    class DQuery:
        q: DA | DB

    # The classes are local, so their string annotations are resolved here.
    DA.__annotations__ = {"child": DA | DB | None, "x": int, "pad": list[int]}
    DB.__annotations__ = {"child": DA | DB | None, "y": int, "pad": list[int]}
    DQuery.__annotations__ = {"q": DA | DB}
    value: dict[str, Any] = {"child": None, "y": 1, "pad": [0] * 20_000}
    for _ in range(8):
        value = {"y": 1, "child": value}

    with caplog.at_level(logging.WARNING, logger="citry"):
        result = validate_args(DQuery, {"q": value})

    assert result.fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}
    # A plain dataclass cannot take a discriminator, so the advice differs.
    assert "make the recursive classes Pydantic models" in caplog.text


def test_the_measure_of_a_value_counts_every_value_inside_it_and_its_text() -> None:
    budget = bounded.WorkBudget()
    inner = [1, 2, 3]
    value = {"a": inner, "b": inner, "c": "x" * 200}

    # Numbers, strings and keys are values; lists and dicts count apart.
    # Keys and strings add their characters to the text.
    assert budget.measure(inner) == (3, 1, 0)
    assert budget.measure(value) == (3 + 2 * 3 + 1, 1 + 2, 3 + 200)


def test_the_measure_of_a_value_that_holds_itself_or_nests_deeply_is_taken() -> None:
    budget = bounded.WorkBudget()
    looped: list[Any] = [1]
    looped.append(looped)
    deep: list[Any] = []
    for _ in range(10_000):
        deep = [deep]

    # The list inside itself counts as one value.
    assert budget.measure(looped) == (2, 1, 0)
    assert budget.measure(deep) == (0, 10_001, 0)


def test_only_large_lists_and_dicts_keep_their_measure() -> None:
    budget = bounded.WorkBudget()
    small = [[] for _ in range(1_000)]
    value = {"pad": small}

    assert budget.measure(value) == (1, 1 + 1 + 1_000, 3)
    # The request keeps the measure of the long list, not of each empty list.
    # The dict around it holds little beside the list, so it goes into the
    # fixed-size store of values measured at the top.
    assert [len(entry[0]) for entry in budget._sizes.values()] == [1_000]
    assert [entry[0] for entry in budget._recent.values()] == [value]


def test_small_values_measured_on_their_own_go_into_a_store_of_fixed_size() -> None:
    budget = bounded.WorkBudget()
    values = [[index] for index in range(1_000)]

    for value in values:
        budget.measure(value)
    # Many small values cost the same memory as a few: the store keeps the
    # last ones measured, and the request keeps nothing else for them.
    assert not budget._sizes
    assert [entry[0] for entry in budget._recent.values()] == values[-bounded._RECENT_SIZE :]


def test_a_small_value_measured_again_is_read_from_the_store() -> None:
    budget = bounded.WorkBudget()
    first = [[1, 2], [3]]
    others = [[index] for index in range(bounded._RECENT_SIZE)]
    budget.measure(first)
    for value in others[:-1]:
        budget.measure(value)

    # The members of a union measure the same value one after another. A
    # value read again moves to the end, so it outlasts the values after it.
    assert budget.measure(first) == (3, 3, 0)
    budget.measure(others[-1])
    assert id(first) in budget._recent
    assert id(others[0]) not in budget._recent


def test_a_tree_keeps_the_measure_of_each_fork_into_large_subtrees() -> None:
    budget = bounded.WorkBudget()
    tree: Any = 1
    for _ in range(12):
        tree = [tree, tree]
    # Each subtree must be its own list, as in decoded JSON: the loop above
    # shares one list between both children.
    tree = json.loads(json.dumps(tree))

    assert budget.measure(tree) == (4_096, 4_095, 0)
    # A check at a lower level reads the kept measure, so it does not walk
    # the subtree again: here each list whose smaller half holds 15 or more
    # values and lists, which is each list with 16 or more leaves.
    fork = tree[0][1][0][1]
    assert budget._sizes[id(fork)][0] is fork
    assert len(budget._sizes) == 2**12 // 8 - 1


def test_each_level_of_a_comb_keeps_its_measure() -> None:
    budget = bounded.WorkBudget()
    comb: Any = 0
    for _ in range(40):
        # The next level, and beside it many short lists that are not kept.
        comb = [comb] + [[0] * 14 for _ in range(62)]

    budget.measure(comb)
    # Each level holds far more than 16 values beside the next level, so a
    # check of a level reads the kept measure of the level below it.
    assert len(budget._sizes) == 40
    assert all(len(entry[0]) == 63 for entry in budget._sizes.values())


def test_a_chain_of_one_item_lists_over_a_small_leaf_keeps_only_the_leaf() -> None:
    budget = bounded.WorkBudget()
    chains = []
    for _ in range(100):
        chain: Any = [0] * 15
        for _ in range(8):
            chain = [chain]
        chains.append(chain)

    # A check measures each list of each chain on its own, from the top.
    for chain in chains:
        level = chain
        while len(level) == 1:
            budget.measure(level)
            level = level[0]
    # One kept measure per leaf, not one per list above it, and the store
    # of values measured at the top stays at its fixed size.
    assert len(budget._sizes) == 100
    assert len(budget._recent) == bounded._RECENT_SIZE


def test_a_chain_of_small_lists_keeps_one_measure_per_large_list_only() -> None:
    budget = bounded.WorkBudget()
    chains = []
    for _ in range(50):
        chain: Any = [0] * 64
        for _ in range(100):
            chain = [chain]
        chains.append(chain)

    budget.measure({"junk": chains})

    # The list that forks into the 50 chains, and the 64-item list at the
    # end of each chain, not the 100 one-item lists above it, which would
    # keep thousands of entries for a small body.
    assert len(budget._sizes) == 1 + 50


@pytest.mark.usefixtures("hand_clock")
def test_a_restore_inside_a_check_leaves_its_time_off_the_checks_clock() -> None:
    with bounded.request_work() as budget:
        budget.clock_on()
        thread = threading.get_ident()
        start = budget._clocks[thread][0]
        with bounded.unbudgeted():
            _spend_cpu(0.02)
        # The clock starts later by the time spent inside, so a later check
        # of the request keeps that time.
        assert budget._clocks[thread][0] - start == pytest.approx(0.02)
        budget.clock_off()


@pytest.mark.usefixtures("hand_clock")
@pytest.mark.parametrize("version", ["v1", "v2"])
def test_a_restore_that_pydantic_runs_itself_counts_toward_the_checks_clock(version: str) -> None:
    def spin(value: str) -> str:
        _spend_cpu(0.02)
        return value

    if version == "v1":
        v1 = pytest.importorskip("pydantic.v1")

        class Board(v1.BaseModel):  # type: ignore[name-defined]
            note: str = ""

            @v1.validator("note")
            def slow(cls, value: str) -> str:  # noqa: N805 - Pydantic v1 passes the class
                return spin(value)

        state_cls: type = Board
    else:
        state_cls = pydantic.create_model("Board", note=(Annotated[str, pydantic.AfterValidator(spin)], ""))

    with bounded.request_work() as budget:
        budget.clock_on()
        thread = threading.get_ident()
        start = budget._clocks[thread][0]
        # The write check of a v1 State restores the browser's writes this
        # way, so a v1 class, which checks them itself, must count its time.
        restore_state(state_cls, {"note": "from the browser"})
        # How far the clock's start moved: the time taken off the clock.
        moved = budget._clocks[thread][0] - start
        budget.clock_off()
    if version == "v1":
        assert moved == 0
    else:
        # Citry's copy of a v2 class restores off the clock.
        assert moved == pytest.approx(0.02)


@pytest.mark.usefixtures("hand_clock")
def test_a_write_to_a_pydantic_v1_state_counts_toward_the_requests_cpu_limit() -> None:
    v1 = pytest.importorskip("pydantic.v1")

    class Board(v1.BaseModel):  # type: ignore[name-defined]
        note: str = ""
        _model = ("note",)

        @v1.validator("note")
        def slow(cls, value: str) -> str:  # noqa: N805 - Pydantic v1 passes the class
            _spend_cpu(0.02)
            return value

    with bounded.request_work() as budget:
        before = budget._seconds_left
        apply_state_updates(Board(), {"note": "from the browser"}, model_fields=("note",))
        # Pydantic v1 checks the write itself, so the time it took is taken
        # from what the request's later checks have left.
        assert before - budget._seconds_left >= 0.02


def _slow_v1_board(spent: float) -> Any:
    v1 = pytest.importorskip("pydantic.v1")

    class Board(v1.BaseModel):  # type: ignore[name-defined]
        note: str = ""
        _model = ("note",)

        # The helper builds this class once per test, and Pydantic v1 refuses
        # a validator function it has already seen unless it is told to allow it.
        @v1.validator("note", allow_reuse=True)
        def slow(cls, value: str) -> str:  # noqa: N805 - Pydantic v1 passes the class
            _spend_cpu(spent)
            return value

    return Board


@pytest.mark.usefixtures("hand_clock")
def test_a_pydantic_v1_state_write_that_uses_up_the_cpu_time_is_accepted_and_the_next_one_refused(
    caplog: pytest.LogCaptureFixture,
) -> None:
    board = _slow_v1_board(0.05)

    with caplog.at_level(logging.WARNING, logger="citry"), bounded.request_work() as budget:
        # Reading the State's current values runs the validator once (50 ms),
        # which counts too, and leaves 20 ms for the first write's check.
        budget._seconds_left = 0.07
        state = board()
        first = apply_state_updates(state, {"note": "first"}, model_fields=("note",))
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"note": "second"}, model_fields=("note",))
        spent = budget.out_of_time()

    # The time runs out inside one validator function, where Citry reads no
    # clock, so the first write is accepted.
    # The log names the class that used the time, once, and says the later
    # checks are what may be refused. The second write is refused before its
    # check starts, and the State keeps the first write's value.
    assert (first, state.note, spent) == (("note",), "first", True)
    assert caught.value.fields == {"_state": bounded.TOO_SLOW_MESSAGE}
    assert caplog.text.count("A browser write to the State") == 1
    assert "Board used up the CPU time" in caplog.text
    assert "Pydantic v2 model" in caplog.text


@pytest.mark.usefixtures("hand_clock")
def test_a_pydantic_v1_state_write_that_uses_up_the_cpu_time_and_fails_is_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    v1 = pytest.importorskip("pydantic.v1")

    class Board(v1.BaseModel):  # type: ignore[name-defined]
        note: str = ""
        _model = ("note",)

        @v1.validator("note")
        def slow_and_strict(cls, value: str) -> str:  # noqa: N805 - Pydantic v1 passes the class
            _spend_cpu(0.05)
            if value == "bad":
                msg = "not allowed"
                raise ValueError(msg)
            return value

    with caplog.at_level(logging.WARNING, logger="citry"), bounded.request_work() as budget:
        # Reading the State's current values runs the validator once (50 ms),
        # which counts too, and leaves 20 ms for the write's check.
        budget._seconds_left = 0.07
        with pytest.raises(StateUpdateError):
            apply_state_updates(Board(), {"note": "bad"}, model_fields=("note",))

    # The write is refused for its own reason, and the class that used the
    # time is still named, not the next class whose check finds the time gone.
    assert "Board used up the CPU time" in caplog.text


@pytest.mark.usefixtures("hand_clock")
def test_a_pydantic_v1_state_write_after_the_cpu_time_was_used_up_is_refused_before_it_runs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    board = _slow_v1_board(0.001)

    with caplog.at_level(logging.WARNING, logger="citry"), bounded.request_work() as budget:
        # An earlier check used up the time, so this quick write is not the
        # one that did. It is refused without running, and the log says so
        # instead of blaming the write for using the time up.
        budget._seconds_left = -1.0
        state = board()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"note": "quick"}, model_fields=("note",))

    assert caught.value.fields == {"_state": bounded.TOO_SLOW_MESSAGE}
    assert state.note == ""
    assert "Board was refused" in caplog.text
    assert "ended before Citry could stop it" not in caplog.text


@pytest.mark.usefixtures("hand_clock")
def test_a_pydantic_v1_state_write_within_the_cpu_time_is_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    board = _slow_v1_board(0.001)

    with caplog.at_level(logging.WARNING, logger="citry"), bounded.request_work() as budget:
        state = board()
        apply_state_updates(state, {"note": "fine"}, model_fields=("note",))
        spent = budget.out_of_time()

    assert (state.note, spent) == ("fine", False)
    assert caplog.text == ""


def test_a_request_drops_its_measures_when_it_ends() -> None:
    with bounded.request_work() as budget:
        budget.measure([[0] * 64])
        assert budget._sizes
    # A task that copied the request's context may keep the budget alive.
    assert not budget._sizes


def test_each_thread_counts_its_own_cpu_time_against_a_shared_budget() -> None:
    budget = bounded.WorkBudget(seconds=10.0)
    budget.clock_on()
    mine = list(budget._clocks[threading.get_ident()])
    seen: list[int] = []

    def other() -> None:
        budget.clock_on()
        seen.append(len(budget._clocks))
        budget.clock_off()

    thread = threading.Thread(target=other)
    thread.start()
    thread.join()

    # Both threads had a clock of their own, and the other thread's start
    # did not replace this thread's.
    assert seen == [2]
    assert budget._clocks == {threading.get_ident(): mine}
    budget.clock_off()
    assert not budget._clocks


def test_the_longest_path_walk_holds_only_the_current_path() -> None:
    payload = {"pad": [[] for _ in range(200_000)], "deep": [[["a" * 10]]]}

    tracemalloc.start()
    try:
        found = bounded.longest_path(payload, strings_hold_keys=True)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()

    # "deep.0.0.0." and then the string itself, read as JSON text.
    assert found == (len("deep.0.0.0.") + 10, 4)
    assert peak < 1_000_000


def test_a_list_or_dict_inside_a_value_costs_more_than_a_number() -> None:
    budget = bounded.WorkBudget()
    budget.spend_on([[], [], []])
    lists = bounded.WORK_BUDGET - budget.left
    budget.spend_on([1, 2, 3])
    numbers = bounded.WORK_BUDGET - budget.left - lists

    assert lists == bounded.ENTRY_STEPS + 4 * bounded.CONTAINER_STEPS
    assert numbers == bounded.ENTRY_STEPS + 3 + bounded.CONTAINER_STEPS


def test_a_check_that_parses_text_spends_for_it_only_inside_a_check_that_may_run_again() -> None:
    budget = bounded.WorkBudget()
    text = "a" * 64_000
    charge = bounded._text_spending(bounded.TEXT_STEPS["url"])
    token = bounded._REQUEST_WORK.set(budget)
    try:
        with bounded.validation_scope(text):
            tally = bounded._current_tally()
            assert tally is not None
            charge(text, lambda value: value)
            assert budget.left == bounded.WORK_BUDGET
            tally.repeating += 1
            charge(text, lambda value: value)
    finally:
        bounded._REQUEST_WORK.reset(token)

    # The wrapper's own call, and the text at the URL rate.
    assert bounded.WORK_BUDGET - budget.left == bounded.PYTHON_CALL_STEPS + 64_000 * bounded.TEXT_STEPS["url"] // 64


def test_a_request_out_of_cpu_time_stops_at_its_next_spend_inside_a_check(hand_clock: _HandClock) -> None:
    clock = hand_clock
    budget = bounded.WorkBudget(seconds=0.5)
    # Outside a check the clock does not count, so nothing stops.
    clock.now += 1.0
    budget.spend_time(1)
    budget.clock_on()
    clock.now += 0.4
    budget.spend_time(1)
    clock.now += 0.2
    with pytest.raises(bounded.ValidationTooCostly) as stopped:
        budget.spend_time(1)
    budget.clock_off()

    assert stopped.value.reason == "time"
    # The visitor is told the check took too long, not that the data nests too deeply.
    assert stopped.value.message == bounded.TOO_SLOW_MESSAGE


def test_cpu_time_between_the_checks_of_a_request_does_not_count(hand_clock: _HandClock) -> None:
    clock = hand_clock
    budget = bounded.WorkBudget(seconds=0.5)
    budget.clock_on()
    clock.now += 0.3
    budget.clock_off()
    # Another request on the same thread (an async server) runs here.
    clock.now += 10.0
    budget.clock_on()
    clock.now += 0.1
    budget.spend_time(1)
    # The two checks together used 0.4 s of the 0.5 s, and 0.2 s more is over.
    clock.now += 0.2
    with pytest.raises(bounded.ValidationTooCostly):
        budget.spend_time(1)
    budget.clock_off()


def test_a_deep_union_that_runs_out_of_cpu_time_is_refused_with_its_own_message(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    payload = {"q": _chain(5, 1)}
    assert validate_args(Query, payload).ok

    # Every read of the clock finds a millisecond more used. A real CPU clock
    # can read the same time across a short check (on Windows it moves in
    # steps of about 15.6 ms), and then a limit of zero never fires.
    clock = _HandClock()

    def ticking() -> float:
        clock.now += 0.001
        return clock.now

    monkeypatch.setattr(bounded, "cpu_clock", ticking)
    monkeypatch.setattr(bounded, "WORK_SECONDS", 0.0)

    assert validate_args(Query, payload).fields == {"_args": bounded.TOO_SLOW_MESSAGE}
    assert "used more CPU time than Citry allows" in caplog.text


def _filter_tree(value_type: Any) -> type[pydantic.BaseModel]:
    """Return a filter tree class whose two group classes both hold more nodes, with ``value_type`` at the leaves."""

    class Cond(pydantic.BaseModel):
        field: str
        value: value_type  # type: ignore[valid-type]

    class AndG(pydantic.BaseModel):
        op: Literal["and"]
        children: list[Cond | AndG | OrG]

    class OrG(pydantic.BaseModel):
        op: Literal["or"]
        children: list[Cond | AndG | OrG]

    namespace = {"Cond": Cond, "AndG": AndG, "OrG": OrG}
    AndG.model_rebuild(_types_namespace=namespace)
    OrG.model_rebuild(_types_namespace=namespace)

    class Filter(pydantic.BaseModel):
        where: Cond | AndG | OrG

    return Filter


def _filter_payload(depth: int, leaf: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"op": "and", "children": [{"field": "a", "value": leaf}]}
    for level in range(depth):
        value = {"op": "or" if level % 2 else "and", "children": [value]}
    return {"where": value}


def test_a_shallow_tree_with_a_large_leaf_of_small_objects_is_accepted() -> None:
    # Each member of each level is charged for the whole leaf, also a member
    # that fails at once, so a list or dict inside costs only a little more
    # than a number.
    filter_class = _filter_tree(list[dict[str, int]])

    assert validate_args(filter_class, _filter_payload(4, [{"x": 1}] * 60_000)).ok


@pytest.mark.parametrize(
    ("value_type", "leaf", "depth"),
    [
        (pydantic.AnyUrl, "http://a.com/" + "a" * 102_000, 8),
        (pydantic.Json[list[int]], "[" + ",".join(["1"] * 400_000) + "]", 4),
    ],
    ids=["url", "json"],
)
def test_a_deep_union_over_text_that_its_check_parses_spends_the_budget(
    value_type: Any, leaf: str, depth: int
) -> None:
    result = validate_args(_filter_tree(value_type), _filter_payload(depth, leaf))

    assert result.fields == {"_args": bounded.TOO_MUCH_WORK_MESSAGE}


@pytest.mark.parametrize(
    ("value_type", "leaf"),
    [
        (pydantic.AnyUrl, "https://example.com/" + "a" * 200),
        (pydantic.Json[list[int]], json.dumps(list(range(1_000)))),
        (Annotated[str, pydantic.AfterValidator(str.strip)], " text " * 100),
    ],
    ids=["url", "json", "function"],
)
def test_an_ordinary_deep_union_over_text_that_its_check_parses_is_accepted(value_type: Any, leaf: str) -> None:
    cls = _filter_tree(value_type)
    payload = _filter_payload(10, leaf)

    result = validate_args(cls, payload)

    assert result.ok
    assert result.value == cls.model_validate(payload)


def test_the_text_rate_follows_the_check_that_reads_the_string() -> None:
    class Texts(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(regex_engine="python-re")
        url: pydantic.AnyUrl
        data: pydantic.Json[list[int]]
        amount: Annotated[Any, pydantic.Field()] = None
        price: Annotated[decimal.Decimal, pydantic.Field(max_digits=10)]
        code: Annotated[str, pydantic.Field(pattern=r"^[a-z]+$")]
        name: Annotated[str, pydantic.AfterValidator(str.strip)]
        count: Annotated[int, pydantic.AfterValidator(abs)]
        address: ipaddress.IPv4Address
        plain: str

    schema = bounded._Schema(Texts.__pydantic_core_schema__)
    fields = bounded._top_fields(Texts.__pydantic_core_schema__)

    def rate(name: str) -> int:
        return max(schema.text_steps(node) for node in schema.nodes(fields[name]["schema"], follow_refs=True))

    steps = bounded.TEXT_STEPS
    assert rate("url") == steps["url"]
    assert rate("data") == steps["json"]
    assert rate("price") == steps["decimal-digits"]
    assert rate("code") == steps["python-re"]
    assert rate("name") == steps["function"]
    # An after validator of a number gets the number, which holds no text.
    assert rate("count") == steps["plain"]
    # Pydantic's own checks of standard types read text as a plain string does.
    assert rate("address") == steps["plain"]
    assert rate("plain") == steps["plain"]


def _same(value: Any) -> Any:
    return value


@pytest.mark.parametrize(
    ("cls", "payload"),
    [
        (
            pydantic.create_model("Labels", u=(list[Annotated[str, pydantic.WrapValidator(_passthrough)] | int], [])),
            {"u": [None]},
        ),
        # Below a recursive union the author's function also spends for text.
        (
            _filter_tree(Annotated[str, pydantic.BeforeValidator(_same)] | int),
            _filter_payload(0, None),
        ),
        # Pydantic's own wrap validator (for a URL) is left as it is.
        (
            pydantic.create_model("UrlLabels", u=(pydantic.Json[int | pydantic.AnyUrl] | Leaf, ...)),
            {"u": "{}"},
        ),
        # A wrapper deeper inside a member changes its label too.
        (
            pydantic.create_model(
                "NestedLabels", u=(list[list[Annotated[str, pydantic.WrapValidator(_passthrough)]] | int], [])
            ),
            {"u": [[None]]},
        ),
        # A member that refers to a definition the copy wrapped as a whole.
        (
            pydantic.create_model("RefLabels", u=(WrappedInts | str, ...), v=(WrappedInts | None, None)),
            {"u": ["x"]},
        ),
    ],
    ids=["wrap", "before-in-tree", "pydantic-wrap-in-json", "nested-wrap", "reference"],
)
def test_a_union_member_the_copy_wraps_keeps_its_label_in_error_paths(cls: Any, payload: Any) -> None:
    with pytest.raises(pydantic.ValidationError) as raised:
        cls.model_validate(payload)
    expected = {".".join(str(part) for part in error["loc"]) for error in raised.value.errors()}

    assert set(validate_args(cls, payload).fields) == expected
    assert any("function-" in path for path in expected)


def test_every_scalar_core_type_has_a_text_rate() -> None:
    assert set(bounded._SCALAR_TEXT) == bounded._SCALAR_TYPES
    assert set(bounded._SCALAR_TEXT.values()) <= set(bounded.TEXT_STEPS)


# --- a class found only at the first call ------------------------------------------------------------


@dataclasses.dataclass
class PlainHolder:
    inner: Wrapped


def test_a_pydantic_class_inside_a_plain_data_class_is_refused_at_its_first_call(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Registration reads only a Pydantic `data` class itself, so a Pydantic
    # class reached through a plain dataclass is checked at the call.
    _register_data(PlainHolder)

    with caplog.at_level(logging.ERROR, logger="citry"):
        result = validate_args(PlainHolder, {"inner": {"q": "{}"}})

    assert result.fields == {"inner": bounded.NOT_CHECKABLE_MESSAGE}
    assert "Its field 'q' holds a Json[...] value with a union" in caplog.text


def test_a_state_finished_after_registration_is_checked_at_its_first_write(caplog: pytest.LogCaptureFixture) -> None:
    class Later(pydantic.BaseModel):
        saved: pydantic.Json[LaterTree] | None = None  # type: ignore[name-defined] # noqa: F821
        _model = ("saved",)

    app = _citry()

    class Panel(Component):
        citry = app
        State = Later
        template = """
          <p></p>
        """

    Later.model_rebuild(_types_namespace={"LaterTree": And | Or})

    with (
        caplog.at_level(logging.ERROR, logger="citry"),
        bounded.request_work(),
        pytest.raises(StateUpdateError) as caught,
    ):
        apply_state_updates(Later(), {"saved": "{}"}, model_fields=("saved",))

    assert caught.value.fields == {"_state": bounded.NOT_CHECKABLE_MESSAGE}
    assert "the writable field 'saved' of the State" in caplog.text


def test_a_finished_time_warning_does_not_hide_a_refused_one(caplog: pytest.LogCaptureFixture) -> None:
    class Slow:
        pass

    # Each warning gives its own advice, so the first must not silence the other.
    with caplog.at_level(logging.WARNING, logger="citry"):
        bounded.warn_work_spent(Slow, "time", refused=False)
        bounded.warn_work_spent(Slow, "time")
        bounded.warn_work_spent(Slow, "time", refused=False)

    messages = [record.getMessage() for record in caplog.records]
    assert len(messages) == 2
    assert "ended before Citry could stop it" in messages[0]
    assert "was refused" in messages[1]
