"""
Pydantic v1 classes and Events.

Events checks a call's data with dataclasses, annotated classes and Pydantic
v2 models. Citry refuses a ``data`` class that is, or reaches, a
``pydantic.v1`` model or dataclass when the component is defined, and a v1
class it meets only at a call (behind a forward reference) gets the
"could not be checked" 422 without running.

A browser write to a ``pydantic.v1`` State is still checked by the model
itself. While Citry runs one of its validations, it hooks two functions of
``pydantic.v1``, so it can count the errors any v1 check builds there and
read the clock. Outside its validations, ``pydantic.v1`` runs its own
functions.
"""

import functools
import json
import logging
import sys
import threading
import time
import types
import warnings
from dataclasses import dataclass, field
from typing import Annotated, Any, Dict, List, NamedTuple, Optional, Union  # noqa: UP035 - shapes of their own

import pytest
from pydantic_core import core_schema

from citry import Citry, Component
from citry.ext.events import _pydantic_bounded as bounded
from citry.ext.events import tokens as tokens_module
from citry.ext.events.dispatcher import EventsDispatcher, TransportContext
from citry.ext.events.openapi import build_openapi_document
from citry.ext.events.schemas import validate_args
from citry.ext.events.state import state_wire_values
from citry.ext.events.tokens import StateUpdateError, apply_state_updates, mint_state_token

pydantic = pytest.importorskip("pydantic")
v1 = pytest.importorskip("pydantic.v1")
v1_error_wrappers = pytest.importorskip("pydantic.v1.error_wrappers")
v1_fields = pytest.importorskip("pydantic.v1.fields")
v1_main = pytest.importorskip("pydantic.v1.main")

SIGNING_KEY = "test-secret-key"
NOT_CHECKABLE = "The value could not be checked."
# What `pydantic.v1` itself has in place, read before any test runs a Citry check.
ORIGINAL_INIT = v1_error_wrappers.ErrorWrapper.__dict__["__init__"]
ORIGINAL_SINGLETON = v1_fields.ModelField.__dict__["_validate_singleton"]


class Tag(v1.BaseModel):
    x: int


@v1.dataclasses.dataclass
class TagDataclass:
    x: int


@dataclass
class InField:
    d: Tag


@dataclass
class InList:
    ds: list[Tag]


@dataclass
class InDict:
    ds: dict[str, Tag]


@dataclass
class InOptional:
    d: Optional[Tag] = None  # noqa: UP045 - the typing spelling is a shape of its own


@dataclass
class InPipeOptional:
    d: Tag | None = None


@dataclass
class InUnion:
    d: Union[int, Tag]  # noqa: UP007 - the typing spelling is a shape of its own


@dataclass
class InNestedDataclass:
    inner: InList


class InPlainClass:
    d: Tag


@dataclass
class V1DataclassField:
    d: TagDataclass


@dataclass
class V1DataclassInList:
    ds: list[TagDataclass]


# Pydantic warns that it does not support a v1 model inside a v2 class.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Mixing V1 models and V2 models", category=UserWarning)

    class V2Field(pydantic.BaseModel):
        d: Tag

    class V2List(pydantic.BaseModel):
        d: list[Tag] | None = None

    class V2V1Dataclass(pydantic.BaseModel):
        d: TagDataclass

    class V2InJson(pydantic.BaseModel):
        d: pydantic.Json[pydantic.InstanceOf[Tag]]

    class V2PlainValidator(pydantic.BaseModel):
        d: Annotated[dict, pydantic.PlainValidator(Tag.parse_obj)]

    class V2BeforeValidator(pydantic.BaseModel):
        d: Annotated[Any, pydantic.BeforeValidator(Tag.parse_obj)]

    @pydantic.dataclasses.dataclass
    class PydanticDataclassField:
        d: Tag

    @pydantic.dataclasses.dataclass
    class PydanticDataclassInstanceOf:
        # Pydantic tests the type only, but Citry checks a Pydantic
        # dataclass's fields itself first, which would build the v1 model.
        d: pydantic.InstanceOf[Tag]

    class V2InstanceOf(pydantic.BaseModel):
        # Only tests that the value is an instance, so no v1 check runs.
        d: pydantic.InstanceOf[Tag] | None = None


class _OwnSchemaTag(v1.BaseModel):
    """A v1 model that gives Pydantic v2 a schema calling one of its own methods."""

    x: int = 0

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> Any:
        return core_schema.no_info_plain_validator_function(cls.parse_obj)


with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Mixing V1 models and V2 models", category=UserWarning)

    class V2OwnSchema(pydantic.BaseModel):
        d: _OwnSchemaTag


@dataclass
class V2InsidePlain:
    inner: V2Field


@dataclass
class InTuple:
    ds: tuple[Tag, ...]


@dataclass
class InSet:
    ds: frozenset[Tag]


@dataclass
class InTypingList:
    ds: List[Tag]  # noqa: UP006 - the typing spelling is a shape of its own


@dataclass
class InTypingDict:
    ds: Dict[str, Tag]  # noqa: UP006 - the typing spelling is a shape of its own


@dataclass
class InAnnotated:
    d: Annotated[Tag, "a note"]


@dataclass
class InheritsField(InField):
    other: int = 0


class TagPair(NamedTuple):
    first: Tag


@dataclass
class InNamedTuple:
    pair: TagPair


with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Mixing V1 models and V2 models", category=UserWarning)

    class V2Partial(pydantic.BaseModel):
        d: Annotated[dict, pydantic.PlainValidator(functools.partial(Tag.parse_obj))]


# A module that defers its annotations, so each resolved hint is a new
# object, which Python can free and give the same id to the next one.
_DEFERRED_SOURCE = """
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Inner:
    c: list[Tag]


@dataclass
class Deferred:
    x: Inner
    y0: list[int]
    y1: int | None
    y2: int | None
"""
_deferred = types.ModuleType("_citry_test_v1_deferred")
_deferred.Tag = Tag  # type: ignore[attr-defined]
sys.modules[_deferred.__name__] = _deferred
exec(compile(_DEFERRED_SOURCE, _deferred.__name__, "exec"), _deferred.__dict__)  # noqa: S102 - a fixed test module
Deferred = _deferred.Deferred


# Each shape that holds a v1 class, with the class the error names.
REFUSED = {
    "the data class itself": (Tag, "Tag"),
    "a v1 dataclass as the data class": (TagDataclass, "TagDataclass"),
    "field": (InField, "Tag"),
    "list": (InList, "Tag"),
    "dict": (InDict, "Tag"),
    "optional": (InOptional, "Tag"),
    "pipe optional": (InPipeOptional, "Tag"),
    "union": (InUnion, "Tag"),
    "nested dataclass": (InNestedDataclass, "Tag"),
    "plain class": (InPlainClass, "Tag"),
    "v1 dataclass field": (V1DataclassField, "TagDataclass"),
    "v1 dataclass in a list": (V1DataclassInList, "TagDataclass"),
    "v2 model field": (V2Field, "Tag"),
    "v2 model list": (V2List, "Tag"),
    "v1 dataclass in a v2 model": (V2V1Dataclass, "TagDataclass"),
    "json in a v2 model": (V2InJson, "Tag"),
    "plain validator": (V2PlainValidator, "Tag"),
    "before validator": (V2BeforeValidator, "Tag"),
    "own core schema": (V2OwnSchema, "_OwnSchemaTag"),
    "pydantic dataclass field": (PydanticDataclassField, "Tag"),
    "pydantic dataclass instance-of": (PydanticDataclassInstanceOf, "Tag"),
    "v2 model inside a plain dataclass": (V2InsidePlain, "Tag"),
    "tuple": (InTuple, "Tag"),
    "frozenset": (InSet, "Tag"),
    "typing list": (InTypingList, "Tag"),
    "typing dict": (InTypingDict, "Tag"),
    "annotated": (InAnnotated, "Tag"),
    "inherited field": (InheritsField, "Tag"),
    "named tuple": (InNamedTuple, "Tag"),
    "partial validator": (V2Partial, "Tag"),
    "deferred annotations": (Deferred, "Tag"),
}


def _app() -> Citry:
    app = Citry(secret=SIGNING_KEY, autodiscover=False)
    app.set_mounted_prefix("/citry")
    return app


def _component(app: Citry, data_class: Any, ran: list[str] | None = None) -> type[Component]:
    ran = [] if ran is None else ran

    class Form(Component):
        citry = app
        template = """
          <form></form>
        """

        class Events:
            def submit(self, data: data_class) -> dict[str, str]:  # type: ignore[valid-type]
                ran.append("submit")
                return {"got": type(data).__name__}

            def other(self) -> dict[str, str]:
                ran.append("other")
                return {"other": "done"}

    return Form


def _dispatch(app: Citry, *calls: dict[str, Any]) -> dict[str, Any]:
    envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": list(calls)}
    return EventsDispatcher().dispatch(envelope, TransportContext(transport="http", citry=app))


def _call(component: type[Component], handler: str, args: dict[str, Any]) -> dict[str, Any]:
    return {"componentClassId": component.class_id, "handlerName": handler, "args": args}


def _hooks_in_place() -> bool:
    return (
        v1_error_wrappers.ErrorWrapper.__dict__["__init__"] is not ORIGINAL_INIT
        or v1_fields.ModelField.__dict__["_validate_singleton"] is not ORIGINAL_SINGLETON
    )


################################################
# DATA CLASSES ARE REFUSED
################################################


@pytest.mark.parametrize("shape", REFUSED)
def test_a_data_class_that_reaches_a_v1_class_is_refused_when_the_component_is_defined(shape: str) -> None:
    data_class, named = REFUSED[shape]

    with pytest.raises(ValueError, match=r"pydantic\.v1 model or dataclass") as caught:
        _component(_app(), data_class)

    message = str(caught.value)
    assert f"the event data class {data_class.__qualname__}" in message
    assert f"Make {named} a Pydantic v2 model." in message


def test_a_v2_model_that_only_tests_for_a_v1_instance_is_not_refused() -> None:
    # Pydantic only runs `isinstance`, so no v1 check runs on the data.
    _component(_app(), V2InstanceOf)

    assert validate_args(V2InstanceOf, {"d": {"x": 1}}).fields == {"d": "Input should be an instance of Tag"}


def test_a_v1_field_that_the_browser_never_sends_is_not_refused() -> None:
    @dataclass
    class Computed:
        x: int
        tag: Tag = field(init=False, default_factory=lambda: Tag(x=0))

    _component(_app(), Computed)


def test_a_v1_model_behind_a_forward_reference_is_refused_at_the_call_without_running(
    caplog: pytest.LogCaptureFixture,
) -> None:
    ran: list[int] = []

    @dataclass
    class Later:
        # The name does not exist yet when the component is defined, so
        # registration cannot read this field.
        d: "LateTag"  # type: ignore[name-defined]

    app = _app()
    handled: list[str] = []
    form = _component(app, Later, handled)

    class LateTag(v1.BaseModel):
        x: int

        @v1.validator("x", pre=True, allow_reuse=True)
        def note(cls, value: Any) -> Any:  # noqa: N805 - Pydantic v1 passes the class
            ran.append(1)
            return value

    globals()["LateTag"] = LateTag
    try:
        with caplog.at_level(logging.ERROR, logger="citry"):
            results = [
                _dispatch(app, _call(form, "submit", {"d": {"x": 1}}), _call(form, "other", {}))["results"]
                for _ in range(2)
            ]
    finally:
        del globals()["LateTag"]

    for refused, accepted in results:
        assert refused["error"]["status"] == 422
        assert refused["error"]["fieldErrors"] == {"d": NOT_CHECKABLE}
        assert accepted["ok"] is True
    # The v1 model never ran on the browser's data, and the log names it once.
    assert ran == []
    assert handled == ["other", "other"]
    assert caplog.text.count("Citry refuses event data for") == 1
    assert "Make" in caplog.text
    assert "LateTag a Pydantic v2 model" in caplog.text


def test_a_v2_class_that_holds_a_v1_model_met_only_at_a_call_is_refused(caplog: pytest.LogCaptureFixture) -> None:
    @dataclass
    class Wrapper:
        inner: "LateHolder"  # type: ignore[name-defined]

    app = _app()
    form = _component(app, Wrapper)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Mixing V1 models and V2 models", category=UserWarning)

        class LateHolder(pydantic.BaseModel):
            d: Annotated[dict, pydantic.PlainValidator(Tag.parse_obj)]

    globals()["LateHolder"] = LateHolder
    try:
        with caplog.at_level(logging.ERROR, logger="citry"):
            [item] = _dispatch(app, _call(form, "submit", {"inner": {"d": {"x": 1}}}))["results"]
    finally:
        del globals()["LateHolder"]

    assert item["error"]["status"] == 422
    assert item["error"]["fieldErrors"] == {"inner": NOT_CHECKABLE}
    assert "holds the pydantic.v1 class Tag" in caplog.text


def test_a_refused_call_runs_no_v1_check_and_leaves_the_hooks_out() -> None:
    @dataclass
    class Later:
        d: "LateTag2"  # type: ignore[name-defined]

    class LateTag2(v1.BaseModel):
        x: int

    globals()["LateTag2"] = LateTag2
    try:
        result = validate_args(Later, {"d": {"x": "a"}})
    finally:
        del globals()["LateTag2"]

    assert result.fields == {"d": NOT_CHECKABLE}
    assert not _hooks_in_place()


################################################
# THE HOOKS ARE IN PLACE ONLY WHILE CITRY CHECKS A V1 STATE WRITE
################################################


class Board(v1.BaseModel):
    rows: list[Tag] = []
    note: str = ""


class _Seen(v1.BaseModel):
    x: int

    @v1.validator("x", allow_reuse=True)
    def look(cls, value: int) -> int:  # noqa: N805 - Pydantic v1 passes the class
        _SEEN_HOOKS.append((value, _hooks_in_place()))
        return value


_SEEN_HOOKS: list[tuple[int, bool]] = []


class SeenBoard(v1.BaseModel):
    item: _Seen = _Seen(x=0)


def test_pydantic_v1_runs_its_own_functions_before_and_after_a_citry_validation() -> None:
    assert not _hooks_in_place()
    state = SeenBoard()
    _SEEN_HOOKS.clear()

    apply_state_updates(state, {"item": {"x": 1}}, model_fields={"item"})

    # Reading the State's current value (0) back from JSON runs v1's own
    # functions. The hooks were there only while the write (1) was checked,
    # and while the written State was read back as JSON in the same check.
    assert _SEEN_HOOKS == [(0, False), (1, True), (1, True)]
    assert not _hooks_in_place()


@pytest.mark.parametrize(
    "rows",
    [[{"x": "a"}], json.loads("[" + ",".join(["[]"] * 5000) + "]")],
    ids=["a few errors", "too many errors"],
)
def test_the_hooks_come_out_after_a_v1_state_write_that_is_refused(rows: list[Any]) -> None:
    with pytest.raises(StateUpdateError):
        apply_state_updates(Board(), {"rows": rows}, model_fields={"rows"})

    assert not _hooks_in_place()


def test_the_hooks_come_out_after_a_v1_state_write_that_runs_out_of_time() -> None:
    with bounded.request_work() as budget:
        budget._seconds_left = -1.0
        with pytest.raises(StateUpdateError):
            apply_state_updates(Board(), {"note": "late"}, model_fields={"note"})

    assert not _hooks_in_place()


def test_the_hooks_are_in_only_while_citry_checks_event_data() -> None:
    seen: list[bool] = []

    @dataclass
    class Probe:
        x: int

        def __post_init__(self) -> None:
            seen.append(_hooks_in_place())

    assert validate_args(Probe, {"x": 1}).ok
    assert seen == [True]
    assert not _hooks_in_place()


def test_overlapping_citry_validations_in_two_threads_keep_the_hooks_until_both_end() -> None:
    inside = threading.Event()
    release = threading.Event()
    seen: list[bool] = []

    def slow_write() -> None:
        with bounded.validation_scope({}):
            inside.set()
            release.wait(5)

    worker = threading.Thread(target=slow_write)
    worker.start()
    inside.wait(5)
    # This validation starts and ends while the other thread's is still inside.
    with bounded.validation_scope({}):
        seen.append(_hooks_in_place())
    seen.append(_hooks_in_place())
    release.set()
    worker.join()

    assert seen == [True, True]
    assert not _hooks_in_place()


def test_nested_guarded_blocks_keep_the_hooks_until_the_last_one_ends() -> None:
    with bounded.guarding_pydantic_v1():
        with bounded.guarding_pydantic_v1():
            assert _hooks_in_place()
        assert _hooks_in_place()
    assert not _hooks_in_place()


def test_the_hooks_come_out_when_the_guarded_block_raises() -> None:
    with pytest.raises(RuntimeError), bounded.guarding_pydantic_v1():
        raise RuntimeError

    assert not _hooks_in_place()


def test_another_threads_v1_check_while_the_hooks_are_in_gets_every_error() -> None:
    # The hooks find no Citry validation in that thread and call the
    # originals, so the check keeps all its errors and the same messages.
    rows = [[]] * 3000
    expected = None
    try:
        Board(rows=rows)
    except v1.ValidationError as err:
        expected = err.errors()

    got: list[Any] = []

    def other_thread() -> None:
        try:
            Board(rows=rows)
        except v1.ValidationError as err:
            got.append(err.errors())

    with bounded.validation_scope({}), bounded.guarding_pydantic_v1():
        assert _hooks_in_place()
        worker = threading.Thread(target=other_thread)
        worker.start()
        worker.join()

    assert expected is not None
    assert got == [expected]
    assert len(expected) == 3000


def test_a_v1_check_outside_a_citry_validation_while_the_hooks_are_in_keeps_every_error() -> None:
    with bounded.guarding_pydantic_v1(), pytest.raises(v1.ValidationError) as caught:
        Board(rows=[[]] * 3000)

    assert len(caught.value.errors()) == 3000


################################################
# WHAT THE HOOKS DO INSIDE A CITRY CHECK
################################################


def test_each_error_a_v1_model_builds_is_counted_once() -> None:
    class Pair(v1.BaseModel):
        a: int
        b: int

    class Holder(v1.BaseModel):
        pair: Pair

    with bounded.validation_scope({}), bounded.guarding_pydantic_v1():
        tally = bounded._current_tally()
        assert tally is not None
        with pytest.raises(v1.ValidationError):
            Holder.parse_obj({"pair": {}})
        # Two missing fields, and the wrapper around the nested model's
        # whole error is not counted again.
        assert tally.errors == 2


def test_a_v1_check_inside_a_citry_validation_stops_at_the_error_limit() -> None:
    with bounded.validation_scope({}), bounded.guarding_pydantic_v1():
        with pytest.raises(bounded.ValidationTooCostly) as caught:
            Board.parse_obj({"rows": [[]] * 100_000})

    assert caught.value.reason == "errors"


def test_a_v1_check_reads_the_clock_once_for_every_few_hundred_values(monkeypatch: pytest.MonkeyPatch) -> None:
    reads: list[float] = []
    original = bounded.WorkBudget.spend_time

    def spend_time(budget: bounded.WorkBudget, seconds: float) -> None:
        reads.append(seconds)
        original(budget, seconds)

    monkeypatch.setattr(bounded.WorkBudget, "spend_time", spend_time)
    with bounded.request_work():
        with bounded.validation_scope({}), bounded.guarding_pydantic_v1():
            Board.parse_obj({"rows": [{"x": index} for index in range(2560)]})

    # v1 checks a few values for each row (the item, the model, its field),
    # so 2,560 rows make about 30 reads, not one for each value.
    assert 15 <= len(reads) <= 40


def test_a_v1_state_write_ends_when_the_cpu_time_is_gone() -> None:
    class Slow(v1.BaseModel):
        x: int

        @v1.validator("x", allow_reuse=True)
        def wait(cls, value: int) -> int:  # noqa: N805 - Pydantic v1 passes the class
            time.sleep(0)
            return value

    class SlowBoard(v1.BaseModel):
        rows: list[Slow] = []

    with bounded.request_work() as budget:
        budget._seconds_left = 1e-9
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(SlowBoard(), {"rows": [{"x": 1}] * 5000}, model_fields={"rows"})

    assert caught.value.fields == {"_state": bounded.TOO_SLOW_MESSAGE}


################################################
# A V1 STATE WRITE IS READ BACK FROM JSON ONCE PER REQUEST
################################################


class _Chunk(v1.BaseModel):
    words: List[str] = []  # noqa: UP006 - Pydantic v1 reads the typing spelling


class _Story(v1.BaseModel):
    chunks: List[_Chunk] = []  # noqa: UP006 - Pydantic v1 reads the typing spelling
    count: int = 0


def _state_component(app: Citry, state_cls: type, handler: Any) -> type[Component]:
    class Panel(Component):
        citry = app
        State = state_cls
        template = """
          <p></p>
        """

        class Events:
            def save(self, state: Any) -> None:
                handler(state)

    return Panel


def _state_call(component: type[Component], updates: dict[str, Any], caller: str = "p1") -> dict[str, Any]:
    token = mint_state_token(
        component.State(), class_id=component.class_id, secret=SIGNING_KEY, max_age=None, max_bytes=8192
    )
    return {
        "componentClassId": component.class_id,
        "handlerName": "save",
        "args": {},
        "callerRenderId": caller,
        "stateToken": token,
        "stateUpdates": updates,
    }


def _bump(state: Any) -> None:
    state.count += 1


def _keep(state: Any) -> None:
    del state


@pytest.mark.parametrize(("handler", "most"), [(_keep, 3), (_bump, 4)], ids=["kept", "changed"])
def test_a_v1_state_write_is_parsed_a_few_times_per_request(
    monkeypatch: pytest.MonkeyPatch, handler: Any, most: int
) -> None:
    # Citry reads a written v1 State for the fingerprint, the round-trip
    # check, the new token and the public values. The request reuses one
    # parse for those reads.
    app = _app()
    panel = _state_component(app, _Story, handler)
    # The browser leaves out a field with a default, so the written State's
    # JSON differs from the write and is parsed once more.
    call = _state_call(panel, {"chunks": [{}]})
    parses: list[type] = []
    original = v1_main.validate_model

    def counting(model: type, *args: Any, **kwargs: Any) -> Any:
        if model is _Story:
            parses.append(model)
        return original(model, *args, **kwargs)

    monkeypatch.setattr(v1_main, "validate_model", counting)
    result = _dispatch(app, *[dict(call, callerRenderId=f"p{index}") for index in range(16)])

    assert all(item["ok"] for item in result["results"])
    # The token's values (their fingerprint reads the same JSON), the
    # browser's write, and the written State read back as JSON, once for the
    # whole request. A handler that changes State adds one read of the
    # changed State.
    assert len(parses) == most


def test_calls_that_reuse_a_v1_parse_each_get_their_own_state() -> None:
    seen: list[list[str]] = []

    def change_in_place(state: Any) -> None:
        seen.append(list(state.chunks[0].words))
        state.chunks[0].words.append("changed")

    app = _app()
    panel = _state_component(app, _Story, change_in_place)
    call = _state_call(panel, {"chunks": [{"words": ["a"]}]})
    result = _dispatch(app, call, dict(call, callerRenderId="p2"), dict(call, callerRenderId="p3"))

    assert all(item["ok"] for item in result["results"])
    # The second and third calls read the same write, and the first call's
    # change in place reaches neither.
    assert seen == [["a"], ["a"], ["a"]]


class _SlowWord(v1.BaseModel):
    text: str

    @v1.validator("text", allow_reuse=True)
    def burn(cls, value: str) -> str:  # noqa: N805 - Pydantic v1 passes the class
        end = time.thread_time() + 0.002
        while time.thread_time() < end:
            pass
        return value


class _SlowStory(v1.BaseModel):
    words: List[_SlowWord] = []  # noqa: UP006 - Pydantic v1 reads the typing spelling
    count: int = 0


class _SlowServerStory(v1.BaseModel):
    words: List[_SlowWord] = []  # noqa: UP006 - Pydantic v1 reads the typing spelling


def test_every_v1_state_read_counts_toward_the_cpu_limit() -> None:
    with bounded.request_work() as budget:
        budget._seconds_left = 60.0
        state = _SlowStory()
        apply_state_updates(state, {"words": [{"text": "a"}] * 10}, model_fields={"words"})
        # The handler changes State, so its next read parses it again.
        state.count += 1
        before = budget._seconds_left
        state_wire_values(state)
        charged = before - budget._seconds_left
        # A second read of the same values reuses the parse.
        before_again = budget._seconds_left
        state_wire_values(state)
        charged_again = before_again - budget._seconds_left
        # A class the browser did not write in this request counts too: its
        # values may be ones the browser chose in an earlier request.
        server_state = _SlowServerStory(words=[{"text": "a"}] * 10)
        before_server = budget._seconds_left
        state_wire_values(server_state)
        charged_server = before_server - budget._seconds_left

    # Ten words at 2 ms each.
    assert charged >= 0.015
    assert charged_again == 0
    assert charged_server >= 0.015


def test_reading_the_written_v1_state_back_is_part_of_the_write_check(monkeypatch: pytest.MonkeyPatch) -> None:
    original = tokens_module.state_wire_values

    def time_runs_out_in_the_check(state: Any) -> dict[str, Any]:
        budget = bounded.current_work()
        if budget is not None and bounded._current_tally() is not None:
            budget._seconds_left = -1.0
        return original(state)

    monkeypatch.setattr(tokens_module, "state_wire_values", time_runs_out_in_the_check)
    with bounded.request_work(), pytest.raises(StateUpdateError) as caught:
        apply_state_updates(Board(), {"rows": [{"x": "1"}] * 300}, model_fields={"rows"})

    # The read-back runs inside the write check, before the handler, so its
    # time is checked and a write that runs out of time there is refused.
    assert caught.value.fields == {"_state": bounded.TOO_SLOW_MESSAGE}
    assert not _hooks_in_place()


def _slow_story_token(panel: type[Component], text: str) -> str:
    return mint_state_token(
        _SlowStory(words=[{"text": text}] * 10),
        class_id=panel.class_id,
        secret=SIGNING_KEY,
        max_age=None,
        max_bytes=8192,
    )


def test_restoring_an_earlier_v1_token_counts_toward_the_cpu_limit() -> None:
    # The first call writes to `_SlowStory`; the others only restore tokens
    # whose values an earlier request may have accepted from the browser.
    app = _app()
    panel = _state_component(app, _SlowStory, _keep)
    written = _state_call(panel, {"words": [{"text": "a"}]})
    restored = {
        "componentClassId": panel.class_id,
        "handlerName": "save",
        "args": {},
        "stateToken": _slow_story_token(panel, "b"),
    }
    left: list[float] = []
    original = tokens_module.verify_state_token

    def note_time(*args: Any, **kwargs: Any) -> Any:
        budget = bounded.current_work()
        if budget is not None:
            left.append(budget._seconds_left)
        return original(*args, **kwargs)

    dispatcher_module = sys.modules[EventsDispatcher.__module__]
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dispatcher_module, "verify_state_token", note_time)
        result = _dispatch(app, written, restored, dict(restored, stateToken=_slow_story_token(panel, "c")))

    assert all(item["ok"] for item in result["results"])
    # The second call's restore of ten slow words (20 ms) is charged.
    assert left[1] - left[2] >= 0.015


def test_v1_restores_that_use_up_the_cpu_time_refuse_the_later_calls() -> None:
    ran: list[str] = []
    app = _app()
    panel = _state_component(app, _SlowStory, lambda state: ran.append(state.words[0].text))
    calls = [
        {
            "componentClassId": panel.class_id,
            "handlerName": "save",
            "args": {},
            "callerRenderId": f"p{index}",
            "stateToken": _slow_story_token(panel, f"w{index}"),
        }
        for index in range(4)
    ]
    with pytest.MonkeyPatch.context() as patch:
        # Each read of a token checks ten slow words (20 ms), which cannot
        # be stopped partway, so the first call or two use up the time.
        patch.setattr(bounded, "WORK_SECONDS", 0.03)
        result = _dispatch(app, *calls)

    statuses = [item.get("error", {}).get("status", 200) for item in result["results"]]
    accepted = statuses.count(200)
    # The later calls are refused before their restore, and their handlers
    # do not run.
    assert 1 <= accepted <= 2
    assert statuses == [200] * accepted + [422] * (4 - accepted)
    assert ran == [f"w{index}" for index in range(accepted)]
    assert result["results"][3]["error"]["fieldErrors"] == {"_state": bounded.TOO_SLOW_MESSAGE}


class _RawTextNote(v1.BaseModel):
    text: str = ""
    _model = ("text",)

    class Config:
        # Leaves a lone surrogate in the JSON text instead of escaping it.
        json_dumps = functools.partial(json.dumps, ensure_ascii=False)


class _Note(v1.BaseModel):
    text: str = ""
    _model = ("text",)


@pytest.mark.parametrize("state_cls", [_RawTextNote, _Note])
def test_a_v1_write_with_a_lone_surrogate_gets_a_422_before_the_handler(state_cls: type) -> None:
    ran: list[str] = []
    app = _app()
    panel = _state_component(app, state_cls, lambda state: ran.append(state.text))
    result = _dispatch(app, _state_call(panel, {"text": "a\ud800"}))

    # The token is UTF-8, which cannot hold the surrogate, so the write is
    # refused before the handler instead of failing at signing.
    error = result["results"][0]["error"]
    assert (error["status"], ran) == (422, [])
    assert error["fieldErrors"] == {"text": tokens_module._LONE_SURROGATE_MESSAGE}


class _Doubling(v1.BaseModel):
    text: str

    @v1.validator("text", allow_reuse=True)
    def double(cls, value: str) -> str:  # noqa: N805 - Pydantic v1 passes the class
        if len(value) > 5:
            msg = "too long"
            raise ValueError(msg)
        return value * 2


class _DoublingBoard(v1.BaseModel):
    item: Optional[_Doubling] = None  # noqa: UP045 - Pydantic v1 reads the typing spelling


def test_a_v1_write_that_does_not_read_back_gets_a_422_before_the_handler() -> None:
    # "abc" becomes "abcabc", which the validator refuses when Citry reads
    # the written State back, so its token could never be signed.
    ran: list[str] = []
    app = _app()
    panel = _state_component(app, _DoublingBoard, lambda _state: ran.append("save"))
    [item] = _dispatch(app, _state_call(panel, {"item": {"text": "abc"}}))["results"]

    assert item["error"]["status"] == 422
    assert "too long" in item["error"]["fieldErrors"]["item.text"]
    assert ran == []


def test_a_v1_state_whose_json_holds_a_lone_surrogate_is_parsed() -> None:
    class Loose(v1.BaseModel):
        note: str = ""

        class Config:
            json_dumps = functools.partial(json.dumps, ensure_ascii=False)

    with bounded.request_work():
        values = state_wire_values(Loose(note="\ud800"))

    assert values == {"note": "\ud800"}


class _Leaf(v1.BaseModel):
    a: int = 0
    child: Optional["_NeverDefined"] = None  # noqa: F821 - the name is never defined, on purpose


class _LeafBoard(v1.BaseModel):
    rows: List[_Leaf] = []  # noqa: UP006 - Pydantic v1 reads the typing spelling


def test_a_write_to_a_v1_state_with_an_unresolved_nested_reference_gets_a_422(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Pydantic v1 cannot check `_Leaf.child`, whose type it never resolved.
    # The write itself passes, but reading the State back as JSON fails, so
    # the call answered 500 after its handler had run.
    ran: list[str] = []
    app = _app()
    panel = _state_component(app, _LeafBoard, lambda _state: ran.append("save"))
    with caplog.at_level(logging.ERROR, logger="citry"):
        [item] = _dispatch(app, _state_call(panel, {"rows": [{"a": 1}]}))["results"]

    assert item["error"]["status"] == 422
    assert item["error"]["fieldErrors"] == {"_state": "The State could not be checked."}
    assert ran == []
    assert any("update_forward_refs" in record.getMessage() for record in caplog.records)


################################################
# A V2 STATE THAT RUNS A V1 CHECK
################################################


with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Mixing V1 models and V2 models", category=UserWarning)
    # Pydantic v2 reads a v1 dataclass through its deprecated `__get_validators__`.
    warnings.filterwarnings("ignore", message="`__get_validators__` is deprecated")

    class V2StateV1Field(pydantic.BaseModel):
        tag: Tag | None = None

    class V2StateV1Dataclass(pydantic.BaseModel):
        tags: list[TagDataclass] = []

    class V2StateV1Method(pydantic.BaseModel):
        rows: Annotated[Any, pydantic.PlainValidator(Board.parse_obj)] = None

    class V2StateV1Partial(pydantic.BaseModel):
        rows: Annotated[Any, pydantic.PlainValidator(functools.partial(Board.parse_obj))] = None

    class V2StateV1ServerOnly(pydantic.BaseModel):
        # The browser may not write `rows`, but every restore checks it.
        rows: Annotated[Any, pydantic.PlainValidator(Board.parse_obj)] = None
        n: int = 0
        _model = ("n",)

    @pydantic.dataclasses.dataclass
    class V2DataclassStateV1Field:
        tag: Tag | None = None

    class V2StateWithHiddenV1Check(pydantic.BaseModel):
        # Citry cannot see the v1 model inside the lambda, so it is not refused.
        rows: Annotated[Any, pydantic.PlainValidator(lambda value: Board.parse_obj(value))] = None


V2_STATES_REFUSED = {
    "v1 model field": (V2StateV1Field, "Tag"),
    "v1 dataclass in a list": (V2StateV1Dataclass, "TagDataclass"),
    "v1 method": (V2StateV1Method, "Board"),
    "partial v1 method": (V2StateV1Partial, "Board"),
    "field the browser may not write": (V2StateV1ServerOnly, "Board"),
    "pydantic dataclass state": (V2DataclassStateV1Field, "Tag"),
}


@pytest.mark.parametrize("shape", V2_STATES_REFUSED)
def test_a_v2_state_that_runs_a_v1_check_is_refused_when_the_component_is_defined(shape: str) -> None:
    state_cls, named = V2_STATES_REFUSED[shape]

    with pytest.raises(ValueError, match=r"pydantic\.v1 model or dataclass") as caught:
        _state_component(_app(), state_cls, _keep)

    message = str(caught.value)
    assert f"the State class {state_cls.__qualname__} holds {named}" in message
    assert f"Make {named} a Pydantic v2 model." in message


def test_a_v1_state_is_not_refused() -> None:
    _state_component(_app(), _Story, _keep)


def test_a_v2_state_whose_validator_runs_a_v1_check_is_guarded(monkeypatch: pytest.MonkeyPatch) -> None:
    # The error limit is under test, so the CPU limit is out of reach: on a
    # slow machine it could stop the check first, with its own message.
    monkeypatch.setattr(bounded, "WORK_SECONDS", 60.0)
    state = V2StateWithHiddenV1Check()

    with pytest.raises(StateUpdateError) as caught:
        apply_state_updates(state, {"rows": {"rows": [[]] * 100_000}}, model_fields={"rows"})

    assert caught.value.fields == {"_state": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert not _hooks_in_place()


################################################
# A V1 CHECK THAT A VALIDATOR CALLS
################################################


with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Mixing V1 models and V2 models", category=UserWarning)

    class HiddenV1(pydantic.BaseModel):
        # Citry cannot see the v1 model inside the lambda, so it is not refused.
        board: Annotated[Any, pydantic.PlainValidator(lambda value: Board.parse_obj(value))]


def test_a_v1_check_that_a_validator_calls_is_counted_and_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    # The error limit is under test, so the CPU limit is out of reach: on a
    # slow machine it could stop the check first, with its own message.
    monkeypatch.setattr(bounded, "WORK_SECONDS", 60.0)
    _component(_app(), HiddenV1)

    result = validate_args(HiddenV1, {"board": {"rows": [[]] * 100_000}})

    assert result.fields == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}
    assert not _hooks_in_place()


def test_a_v1_check_that_a_validator_calls_gets_the_same_answer_while_another_thread_holds_the_hooks() -> None:
    payload = {"board": {"rows": [[]] * 5000}}
    alone = validate_args(HiddenV1, payload).fields
    got: list[Any] = []

    def other_thread() -> None:
        got.append(validate_args(HiddenV1, payload).fields)

    with bounded.validation_scope({}):
        worker = threading.Thread(target=other_thread)
        worker.start()
        worker.join()

    assert got == [alone]
    assert alone == {"_args": bounded.TOO_MANY_ERRORS_MESSAGE}


def test_the_openapi_document_describes_a_v1_model_that_a_handler_returns() -> None:
    app = _app()

    class Returns(Component):
        citry = app
        template = """
          <div></div>
        """

        class Events:
            def tag(self) -> Tag:
                return Tag(x=1)

    schemas = build_openapi_document(app)["components"]["schemas"]

    assert schemas["Tag"]["properties"]["x"]["type"] == "integer"
