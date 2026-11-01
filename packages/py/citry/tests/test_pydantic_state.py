"""
Pydantic State: a component's ``State`` written as a Pydantic v2 or v1 model, or generated as one under ``model_base``.

The first part runs the State behaviours every kind shares (signing a
changed State, browser writes, restoring from a token, the render-time
token) against four kinds: a generated dataclass, a hand-written v2 model,
a hand-written v1 model, and a v2 model generated under ``model_base``. The
second part covers what only a model State does: Pydantic validates it when
it is restored, Citry validates a changed one before signing it, and its
settings live in Pydantic's private attributes.
"""

from __future__ import annotations

import asyncio
import dataclasses
import datetime
import decimal
import enum
import logging
import re
import typing
import uuid
from typing import Any

import pytest

from citry import Citry, Component, ComponentLibrary, LibraryComponent
from citry._vue.capture import render_prepared_direct
from citry.ext.events.dispatcher import EventsDispatcher, TransportContext
from citry.ext.events.extension import _component_events_info
from citry.ext.events.tokens import mint_state_token, verify_state_token

pydantic = pytest.importorskip("pydantic")
pydantic_v1 = pytest.importorskip("pydantic.v1")

SIGNING_KEY = "test-secret-key"
KINDS = ("dataclass", "v2", "v1", "generated")


@pytest.fixture(autouse=True)
def _pinned_token_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: 1_700_000_000.0)


def _citry(**settings: Any) -> Citry:
    app = Citry(secret=SIGNING_KEY, autodiscover=False, **settings)
    app.set_mounted_prefix("/citry")
    return app


def _state_and_app(kind: str) -> tuple[type, Citry]:
    """Build one State class of ``kind`` with the same fields, and the app it belongs to."""
    if kind == "v2":

        class ModelState(pydantic.BaseModel):
            count: int = 0
            name: str = "Counter"
            _model = ("count", "name")

        return ModelState, _citry()
    if kind == "v1":

        class ModelStateV1(pydantic_v1.BaseModel):
            count: int = 0
            name: str = "Counter"
            _model = ("count", "name")

        return ModelStateV1, _citry()

    class PlainState:
        count: int = 0
        name: str = "Counter"
        _model = ("count", "name")

    return PlainState, _citry(model_base=pydantic.BaseModel) if kind == "generated" else _citry()


def _counter(kind: str) -> type[Component]:
    state, app = _state_and_app(kind)

    class Counter(Component):
        citry = app
        State = state
        template = """
          <p>{{ count }}</p>
        """

        class Events:
            def bump(self, state: Any) -> dict[str, int]:
                state.count += 10
                return {"count": state.count}

            def read(self, state: Any) -> dict[str, Any]:
                return {"count": state.count, "name": state.name}

            def break_it(self, state: Any) -> None:
                state.count = "not a number"

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, int]:
            return {"count": 1}

    return Counter


def _token(comp_cls: type[Component], **values: Any) -> str:
    return mint_state_token(
        comp_cls.State(**values), class_id=comp_cls.class_id, secret=SIGNING_KEY, max_age=None, max_bytes=8192
    )


def _dispatch(comp_cls: type[Component], handler: str, **call: Any) -> dict[str, Any]:
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "calls": [{"componentClassId": comp_cls.class_id, "handlerName": handler, "args": {}, **call}],
    }
    result = EventsDispatcher().dispatch(envelope, TransportContext(transport="http", citry=comp_cls.citry))
    [item] = result["results"]
    return item


# --- every kind ----------------------------------------------------------------


@pytest.mark.parametrize("kind", KINDS)
def test_the_state_class_has_the_kind(kind: str) -> None:
    counter = _counter(kind)

    is_model = isinstance(getattr(counter.State, "model_fields", None), dict) or kind == "v1"
    assert is_model is (kind != "dataclass")


@pytest.mark.parametrize("kind", KINDS)
def test_a_changed_state_is_signed_into_the_state_action(kind: str) -> None:
    counter = _counter(kind)

    item = _dispatch(counter, "bump", callerRenderId="i1", stateToken=_token(counter, count=1))

    assert [action["action"] for action in item["actions"]] == ["state", "data"]
    verified = verify_state_token(item["actions"][0]["stateToken"], cls=counter, secrets=[SIGNING_KEY])
    assert verified.state_kwargs == {"count": 11, "name": "Counter"}
    assert item["actions"][0]["publicState"] == {"count": 11, "name": "Counter"}


@pytest.mark.parametrize("kind", KINDS)
def test_a_call_that_only_reads_state_signs_nothing(kind: str) -> None:
    counter = _counter(kind)

    item = _dispatch(counter, "read", callerRenderId="i1", stateToken=_token(counter, count=4))

    assert [action["action"] for action in item["actions"]] == ["data"]
    assert item["actions"][0]["value"] == {"count": 4, "name": "Counter"}


@pytest.mark.parametrize("kind", KINDS)
def test_a_browser_write_is_applied_before_the_handler(kind: str) -> None:
    counter = _counter(kind)

    item = _dispatch(counter, "read", callerRenderId="i1", stateToken=_token(counter), stateUpdates={"name": "Drafts"})

    assert item["actions"][1]["value"] == {"count": 0, "name": "Drafts"}


@pytest.mark.parametrize("kind", KINDS)
def test_a_browser_write_of_the_wrong_type_is_a_per_field_422(kind: str) -> None:
    counter = _counter(kind)

    item = _dispatch(counter, "read", stateToken=_token(counter), stateUpdates={"count": "many"})

    error = item["error"]
    assert error["status"] == 422
    assert error["code"] == "invalid_args"
    assert set(error["fieldErrors"]) == {"count"}


@pytest.mark.parametrize(("count", "note"), [(20, ""), (21, " 1 more unexpected field is not shown.")])
@pytest.mark.parametrize("kind", KINDS)
def test_browser_writes_to_names_outside_the_state_stop_at_twenty(kind: str, count: int, note: str) -> None:
    counter = _counter(kind)
    # Reverse order shows the listed names come from sorting, not from the wire order.
    updates = {f"u{index:03d}": 1 for index in reversed(range(count))}

    item = _dispatch(counter, "read", stateToken=_token(counter), stateUpdates=updates)

    error = item["error"]
    assert error["status"] == 422
    assert error["code"] == "invalid_args"
    assert error["message"] == "Some state updates were rejected; see the field messages." + note
    assert list(error["fieldErrors"]) == [f"u{index:03d}" for index in range(20)]
    assert all("_model" in message for message in error["fieldErrors"].values())


@pytest.mark.parametrize("kind", KINDS)
def test_a_hundred_writes_to_names_outside_the_state_are_counted(kind: str) -> None:
    counter = _counter(kind)
    updates = {f"u{index:03d}": 1 for index in range(100)}

    item = _dispatch(counter, "read", stateToken=_token(counter), stateUpdates=updates)

    error = item["error"]
    assert error["message"].endswith(" 80 more unexpected fields are not shown.")
    assert len(error["fieldErrors"]) == 20


@pytest.mark.parametrize("kind", KINDS)
def test_the_render_signs_a_state_token(kind: str) -> None:
    counter = _counter(kind)

    html = counter().render().serialize()

    assert "<p" in html
    assert "1</p>" in html


# --- a model State --------------------------------------------------------------


@pytest.mark.parametrize("kind", ["v2", "v1", "generated"])
def test_a_wrong_typed_assignment_fails_the_call_that_made_it(kind: str, caplog: pytest.LogCaptureFixture) -> None:
    counter = _counter(kind)

    with caplog.at_level(logging.ERROR, logger="citry"):
        item = _dispatch(counter, "break_it", callerRenderId="i1", stateToken=_token(counter, count=1))

    # The mistake shows up here, not as stale_state on the next call, and
    # no new token goes out.
    assert item["error"]["status"] == 500
    assert item["error"]["code"] == "handler_error"
    assert "actions" not in item
    logged = caplog.text
    assert "'break_it' on component Counter left State field 'count'" in logged


def test_validate_assignment_raises_inside_the_handler() -> None:
    app = _citry()

    class Strict(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(validate_assignment=True)
        count: int = 0

    class Counter(Component):
        citry = app
        State = Strict
        template = """
          <p>x</p>
        """

        class Events:
            def break_it(self, state: Any) -> None:
                state.count = "not a number"

    item = _dispatch(Counter, "break_it", stateToken=_token(Counter))

    assert item["error"]["code"] == "handler_error"


def test_an_in_place_change_to_a_nested_model_is_validated_before_signing() -> None:
    app = _citry()

    class Address(pydantic.BaseModel):
        city: str = "Bratislava"

    class Profile(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(validate_assignment=True)
        address: Address = Address()

    class Card(Component):
        citry = app
        State = Profile
        template = """
          <p>x</p>
        """

        class Events:
            def move(self, state: Any) -> None:
                # Pydantic checks neither this assignment nor the nested one.
                state.address.city = 3

    item = _dispatch(Card, "move", callerRenderId="i1", stateToken=_token(Card))

    assert item["error"]["code"] == "handler_error"


def test_an_in_place_list_change_counts_as_a_change() -> None:
    app = _citry()

    class Tags(pydantic.BaseModel):
        items: list[str] = []

    class Card(Component):
        citry = app
        State = Tags
        template = """
          <p>x</p>
        """

        class Events:
            def add(self, state: Any) -> None:
                state.items.append("new")

    item = _dispatch(Card, "add", callerRenderId="i1", stateToken=_token(Card))

    verified = verify_state_token(item["actions"][0]["stateToken"], cls=Card, secrets=[SIGNING_KEY])
    assert verified.state_kwargs == {"items": ["new"]}


def test_a_call_that_only_reads_state_validates_it_once() -> None:
    app = _citry()
    runs: list[int] = []

    class Counted(pydantic.BaseModel):
        count: int = 0

        @pydantic.field_validator("count")
        @classmethod
        def record(cls, value: int) -> int:
            runs.append(value)
            return value

    class Counter(Component):
        citry = app
        State = Counted
        template = """
          <p>x</p>
        """

        class Events:
            def read(self, state: Any) -> dict[str, int]:
                return {"count": state.count}

    token = _token(Counter, count=2)
    runs.clear()

    _dispatch(Counter, "read", callerRenderId="i1", stateToken=token)

    # One run: the restore. An unchanged State is not checked again.
    assert runs == [2]


def test_a_strict_model_restores_a_tuple_field_from_a_token() -> None:
    app = _citry()

    class Picked(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)
        ids: tuple[int, ...] = ()

    class Card(Component):
        citry = app
        State = Picked
        template = """
          <p>x</p>
        """

        class Events:
            def read(self, state: Any) -> dict[str, str]:
                return {"type": type(state.ids).__name__}

    # The token holds a list, as JSON has no tuple.
    item = _dispatch(Card, "read", stateToken=_token(Card, ids=(1, 2)))

    assert item["actions"][0]["value"] == {"type": "tuple"}


def test_a_token_that_no_longer_validates_is_stale() -> None:
    app = _citry()

    class Before(pydantic.BaseModel):
        count: str = "x"

    class After(pydantic.BaseModel):
        count: int = 0

    class Card(Component):
        citry = app
        State = Before
        template = """
          <p>x</p>
        """

        class Events:
            def read(self, state: Any) -> dict[str, int]:
                return {"ok": 1}

    token = _token(Card, count="text")
    # The class changed across a deploy, so the token's value no longer fits.
    events_info = _component_events_info(Card)
    assert events_info is not None
    object.__setattr__(events_info, "state_cls", After)

    item = _dispatch(Card, "read", stateToken=token)

    assert item["error"]["status"] == 409
    assert item["error"]["code"] == "stale_state"


def test_a_v2_private_storage_setting_is_read() -> None:
    app = _citry()

    class Stored(pydantic.BaseModel):
        count: int = 0
        _storage = "server"

    class Card(Component):
        citry = app
        State = Stored
        template = """
          <p>x</p>
        """

    info = _component_events_info(Card)
    assert info is not None
    assert info.state_meta is not None
    assert info.state_meta.storage == "server"


def test_an_unknown_underscore_name_on_a_v2_model_fails() -> None:
    app = _citry()

    class Typo(pydantic.BaseModel):
        count: int = 0
        _strorage = "server"

    with pytest.raises(ValueError, match="'_strorage' is not a recognized State meta attribute"):

        class Card(Component):
            citry = app
            State = Typo
            template = """
              <p>x</p>
            """


@pytest.mark.parametrize(
    ("base", "setting"),
    [
        ("v2", "model_config['frozen']"),
        ("v1-frozen", "Config.frozen"),
        ("v1-mutation", "Config.allow_mutation = False"),
    ],
)
def test_a_frozen_model_state_fails(base: str, setting: str) -> None:
    app = _citry()
    if base == "v2":

        class Frozen(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(frozen=True)
            count: int = 0

        state: type = Frozen
    else:

        class FrozenV1(pydantic_v1.BaseModel):
            count: int = 0

            class Config:
                frozen = base == "v1-frozen"
                allow_mutation = base != "v1-mutation"

        state = FrozenV1

    with pytest.raises(ValueError, match=re.escape(f"State is a frozen Pydantic model ({setting}")):

        class Card(Component):
            citry = app
            State = state
            template = """
              <p>x</p>
            """


def test_a_frozen_model_base_fails_for_state() -> None:
    class FrozenModel(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(frozen=True)

    app = _citry(model_base=FrozenModel)

    with pytest.raises(ValueError, match="State is a frozen Pydantic model"):

        class Card(Component):
            citry = app
            template = """
              <p>x</p>
            """

            class State:
                count: int = 0


# --- second review: the JSON form ------------------------------------------------


class Shade(enum.Enum):
    DARK = "dark"


def test_a_strict_model_round_trips_every_json_type() -> None:
    app = _citry()

    class Rich(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)
        when: datetime.date = datetime.date(2026, 1, 2)
        shade: Shade = Shade.DARK
        key: uuid.UUID = uuid.UUID(int=1)
        price: decimal.Decimal = decimal.Decimal("1.50")
        tags: set[str] = {"a"}
        maybe: tuple[int, ...] | None = (1, 2)
        pairs: list[tuple[int, int]] = [(1, 2)]
        count: int = 0

    class Card(Component):
        citry = app
        State = Rich
        template = """
          <p>x</p>
        """

        class Events:
            def bump(self, state: Any) -> dict[str, str]:
                state.count += 1
                return {"when": type(state.when).__name__, "maybe": type(state.maybe).__name__}

    # Each type travels as JSON and is read back as JSON, so strict mode
    # accepts it; a second call restores what the first one signed.
    first = _dispatch(Card, "bump", callerRenderId="i1", stateToken=_token(Card))
    assert first["actions"][1]["value"] == {"when": "date", "maybe": "tuple"}
    second = _dispatch(Card, "bump", callerRenderId="i1", stateToken=first["actions"][0]["stateToken"])
    assert second["actions"][1]["value"] == {"when": "date", "maybe": "tuple"}


def test_a_strict_model_takes_a_browser_write_for_a_date() -> None:
    app = _citry()

    class Dated(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)
        when: datetime.date = datetime.date(2026, 1, 2)

    class Card(Component):
        citry = app
        State = Dated
        template = """
          <p>x</p>
        """

        class Events:
            def read(self, state: Any) -> dict[str, str]:
                return {"when": state.when.isoformat()}

    item = _dispatch(Card, "read", callerRenderId="i1", stateToken=_token(Card), stateUpdates={"when": "2027-03-04"})

    assert item["actions"][1]["value"] == {"when": "2027-03-04"}


@pytest.mark.parametrize(
    ("field", "message"),
    [
        (pydantic.Field(default=0, frozen=True), "is frozen, but handlers change State"),
        (pydantic.Field(default=0, exclude=True), "is left out of the model's dump"),
    ],
)
def test_a_model_field_citry_cannot_store_fails_at_class_setup(field: Any, message: str) -> None:
    app = _citry()
    state = pydantic.create_model("Odd", count=(int, field))

    with pytest.raises(ValueError, match=re.escape(f"State.count {message}")):

        class Card(Component):
            citry = app
            State = state
            template = """
              <p>x</p>
            """


def test_an_alias_works_when_the_model_fills_fields_by_name() -> None:
    app = _citry()

    class Named(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(populate_by_name=True)
        count: int = pydantic.Field(default=0, alias="Count")

    class Card(Component):
        citry = app
        State = Named
        template = """
          <p>x</p>
        """

        class Events:
            def bump(self, state: Any) -> dict[str, int]:
                state.count += 1
                return {"count": state.count}

    first = _dispatch(Card, "bump", callerRenderId="i1", stateToken=_token(Card, count=4))
    second = _dispatch(Card, "bump", callerRenderId="i1", stateToken=first["actions"][0]["stateToken"])

    assert second["actions"][1]["value"] == {"count": 6}


def test_a_secret_field_fails_at_class_setup() -> None:
    app = _citry()

    class Holding(pydantic.BaseModel):
        token: pydantic.SecretStr = pydantic.SecretStr("x")

    with pytest.raises(ValueError, match=r"State\.token holds a secret type"):

        class Card(Component):
            citry = app
            State = Holding
            template = """
              <p>x</p>
            """


def test_a_model_serializer_fails_at_class_setup() -> None:
    app = _citry()

    class Shaped(pydantic.BaseModel):
        count: int = 0

        @pydantic.model_serializer
        def dump(self) -> dict[str, int]:
            return {"n": self.count}

    with pytest.raises(ValueError, match="defines a serializer"):

        class Card(Component):
            citry = app
            State = Shaped
            template = """
              <p>x</p>
            """


def test_a_setting_without_a_value_fails() -> None:
    app = _citry()

    class Unset(pydantic.BaseModel):
        count: int = 0
        _storage: str

    with pytest.raises(ValueError, match="declares the setting '_storage' without a value"):

        class Card(Component):
            citry = app
            State = Unset
            template = """
              <p>x</p>
            """


def test_a_validator_that_crashes_on_a_browser_write_answers_422() -> None:
    app = _citry()

    class Picky(pydantic.BaseModel):
        name: str = "a"

        @pydantic.field_validator("name", mode="before")
        @classmethod
        def strip(cls, value: Any) -> Any:
            return value.strip()

    class Card(Component):
        citry = app
        State = Picky
        template = """
          <p>x</p>
        """

        class Events:
            def read(self, state: Any) -> dict[str, str]:
                return {"name": state.name}

    # The integer has no .strip(), which raises AttributeError, not a
    # validation error. The call fails on its own; the envelope survives.
    item = _dispatch(Card, "read", stateToken=_token(Card), stateUpdates={"name": 5})

    assert item["error"]["status"] == 422
    assert item["error"]["fieldErrors"] == {"_state": "The State could not be checked."}


def test_a_browser_write_keeps_every_value_the_model_derives() -> None:
    app = _citry()

    class Priced(pydantic.BaseModel):
        qty: int = 1
        price: int = 5
        total: int = 5
        _model = ("qty",)

        @pydantic.model_validator(mode="after")
        def compute(self) -> Priced:
            self.total = self.qty * self.price
            return self

    class Card(Component):
        citry = app
        State = Priced
        template = """
          <p>x</p>
        """

        class Events:
            def read(self, state: Any) -> dict[str, int]:
                return {"total": state.total}

    item = _dispatch(Card, "read", callerRenderId="i1", stateToken=_token(Card), stateUpdates={"qty": 3})

    assert item["actions"][1]["value"] == {"total": 15}


def test_a_computed_field_is_not_stored_and_does_not_count_as_a_change() -> None:
    app = _citry()
    ticks = iter(range(100))

    class Clocked(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        count: int = 0

        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def tick(self) -> int:
            return next(ticks)

    class Card(Component):
        citry = app
        State = Clocked
        template = """
          <p>x</p>
        """

        class Events:
            def read(self, state: Any) -> dict[str, int]:
                return {"count": state.count}

            def bump(self, state: Any) -> None:
                state.count += 1

    token = _token(Card)

    # A value that differs on every read is not part of State.
    assert [
        action["action"] for action in _dispatch(Card, "read", callerRenderId="i1", stateToken=token)["actions"]
    ] == ["data"]
    changed = _dispatch(Card, "bump", callerRenderId="i1", stateToken=token)
    verified = verify_state_token(changed["actions"][0]["stateToken"], cls=Card, secrets=[SIGNING_KEY])
    assert verified.state_kwargs == {"count": 1}


def test_a_model_state_kept_on_the_server_round_trips() -> None:
    app = _citry()

    class Stored(pydantic.BaseModel):
        when: datetime.date = datetime.date(2026, 1, 2)
        count: int = 0
        _storage = "server"

    class Card(Component):
        citry = app
        State = Stored
        template = """
          <p>x</p>
        """

        class Events:
            def bump(self, state: Any) -> dict[str, Any]:
                state.count += 1
                return {"count": state.count, "when": state.when.isoformat()}

    first = _dispatch(Card, "bump", callerRenderId="i1", stateToken=_cached_token(Card))
    second = _dispatch(Card, "bump", callerRenderId="i1", stateToken=first["actions"][0]["stateToken"])

    assert second["actions"][1]["value"] == {"count": 2, "when": "2026-01-02"}


def _cached_token(comp_cls: type[Component]) -> str:
    return mint_state_token(
        comp_cls.State(),
        class_id=comp_cls.class_id,
        secret=SIGNING_KEY,
        max_age=None,
        max_bytes=8192,
        storage="server",
        cache=comp_cls.citry.cache,
    )


def test_an_async_dispatch_checks_a_changed_model_state() -> None:
    counter = _counter("v2")
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "calls": [
            {
                "componentClassId": counter.class_id,
                "handlerName": "break_it",
                "args": {},
                "stateToken": _token(counter),
            }
        ],
    }

    result = asyncio.run(
        EventsDispatcher().dispatch_async(envelope, TransportContext(transport="http", citry=counter.citry))
    )

    assert result["results"][0]["error"]["code"] == "handler_error"


def test_a_cached_render_replays_a_model_state_holding_a_date() -> None:
    app = _citry()
    data_calls: list[int] = []

    class Dated(pydantic.BaseModel):
        when: datetime.date = datetime.date(2026, 1, 2)

    class Card(Component):
        citry = app
        State = Dated
        template = """
          <button @c-click="update">x</button>
        """

        class Cache:
            enabled = True

        class Events:
            def update(self, state: Any) -> None:
                return None

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, int]:
            data_calls.append(1)
            return {}

    render_prepared_direct(Card())
    render_prepared_direct(Card())

    # The token holds "2026-01-02", which the model reads back as a date,
    # so the second render replays the cached entry.
    assert data_calls == [1]


# --- third review ----------------------------------------------------------------


def _model_card(state: type, **events: Any) -> type[Component]:
    app = _citry()
    events_cls = type("Events", (), events)

    class Card(Component):
        citry = app
        State = state
        Events = events_cls
        template = """
          <p>x</p>
        """

    return Card


def test_a_set_changed_in_place_signs_whatever_its_order() -> None:
    class Bag(pydantic.BaseModel):
        items: set[int] = set()

    def grow(self: Any, state: Any) -> None:
        state.items.update(range(100))
        state.items.difference_update(range(2, 64))
        state.items.difference_update(range(65, 100))

    card = _model_card(Bag, grow=grow)

    item = _dispatch(card, "grow", callerRenderId="i1", stateToken=_token(card))

    verified = verify_state_token(item["actions"][0]["stateToken"], cls=card, secrets=[SIGNING_KEY])
    assert sorted(verified.state_kwargs["items"]) == [0, 1, 64]


def test_a_value_pydantic_converts_is_signed_converted() -> None:
    class Paged(pydantic.BaseModel):
        page: int = 1

    def jump(self: Any, state: Any) -> None:
        state.page = "2"

    card = _model_card(Paged, jump=jump)

    item = _dispatch(card, "jump", callerRenderId="i1", stateToken=_token(card))

    # Browser code sees the number, not the text the handler assigned.
    assert item["actions"][0]["publicState"] == {"page": 2}


def test_an_alias_never_fills_another_field() -> None:
    class Roles(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(populate_by_name=True)
        role: str = "user"
        admin: str = pydantic.Field(default="no", alias="role")
        _model = ("role",)

    def read(self: Any, state: Any) -> dict[str, str]:
        return {"admin": state.admin}

    card = _model_card(Roles, read=read)

    # The write names `role`, which is also `admin`'s alias; State is read
    # by field name, so only `role` changes.
    item = _dispatch(card, "read", callerRenderId="i1", stateToken=_token(card), stateUpdates={"role": "yes"})

    assert item["actions"][1]["value"] == {"admin": "no"}


def test_an_alias_works_without_populate_by_name() -> None:
    class Aliased(pydantic.BaseModel):
        count: int = pydantic.Field(default=0, alias="Count")

    def bump(self: Any, state: Any) -> dict[str, int]:
        state.count += 1
        return {"count": state.count}

    card = _model_card(Aliased, bump=bump)
    first = _dispatch(card, "bump", callerRenderId="i1", stateToken=_token(card, Count=4))
    second = _dispatch(card, "bump", callerRenderId="i1", stateToken=first["actions"][0]["stateToken"])

    assert second["actions"][1]["value"] == {"count": 6}


def test_a_v1_alias_without_population_by_name_fails() -> None:
    class AliasedV1(pydantic_v1.BaseModel):
        count: int = pydantic_v1.Field(default=0, alias="Count")

    with pytest.raises(ValueError, match=r"State\.count has an alias"):
        _model_card(AliasedV1)


@pytest.mark.parametrize("kind", ["field_serializer", "plain_serializer"])
def test_a_serializer_fails_at_class_setup(kind: str) -> None:
    if kind == "field_serializer":

        class Shaped(pydantic.BaseModel):
            when: datetime.date = datetime.date(2026, 1, 2)

            @pydantic.field_serializer("when")
            def dump_when(self, value: datetime.date) -> str:
                return value.strftime("%d/%m/%Y")

        state: type = Shaped
        message = "defines a serializer"
    else:
        doubled = typing.Annotated[int, pydantic.PlainSerializer(lambda value: value * 2)]
        state = pydantic.create_model("Doubled", n=(doubled, 1))
        message = r"State\.n has a serializer"

    with pytest.raises(ValueError, match=message):
        _model_card(state)


def test_a_secret_in_a_nested_model_fails() -> None:
    class Login(pydantic.BaseModel):
        password: pydantic.SecretStr = pydantic.SecretStr("x")

    class Holder(pydantic.BaseModel):
        login: Login = Login()

    with pytest.raises(ValueError, match=r"State\.login\.password holds a secret type"):
        _model_card(Holder)


def test_a_class_named_like_a_secret_is_fine() -> None:
    class SecretSanta(pydantic.BaseModel):
        name: str = "x"

    class Party(pydantic.BaseModel):
        santa: SecretSanta = SecretSanta()
        mood: typing.Literal["Secret", "Open"] = "Open"

    assert _model_card(Party).State is Party


def test_a_nested_computed_field_is_not_stored() -> None:
    class Line(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        qty: int = 1

        @pydantic.computed_field  # type: ignore[prop-decorator]
        @property
        def double(self) -> int:
            return self.qty * 2

    class Order(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        line: Line = Line()

    def bump(self: Any, state: Any) -> None:
        state.line.qty += 1

    card = _model_card(Order, bump=bump)
    first = _dispatch(card, "bump", callerRenderId="i1", stateToken=_token(card))
    second = _dispatch(card, "bump", callerRenderId="i1", stateToken=first["actions"][0]["stateToken"])

    verified = verify_state_token(second["actions"][0]["stateToken"], cls=card, secrets=[SIGNING_KEY])
    assert verified.state_kwargs == {"line": {"qty": 3}}


def test_a_json_field_round_trips() -> None:
    class Raw(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(validate_default=True)
        data: pydantic.Json[list[int]] = "[1]"  # type: ignore[assignment]
        count: int = 0

    def bump(self: Any, state: Any) -> None:
        state.count += 1

    card = _model_card(Raw, bump=bump)
    first = _dispatch(card, "bump", callerRenderId="i1", stateToken=_token(card))
    second = _dispatch(card, "bump", callerRenderId="i1", stateToken=first["actions"][0]["stateToken"])

    assert second["actions"][0]["publicState"]["count"] == 2


class User1(pydantic_v1.BaseModel):
    name: str = "a"


class Admin1(User1):
    password: str = "pw"  # noqa: S105 - a fixture value, the field under test


class Holder1(pydantic_v1.BaseModel):
    user: User1 = User1()
    count: int = 0


def test_a_v1_nested_subclass_does_not_leak_its_extra_fields() -> None:
    def promote(self: Any, state: Any) -> None:
        state.user = Admin1()
        state.count += 1

    card = _model_card(Holder1, promote=promote)

    item = _dispatch(card, "promote", callerRenderId="i1", stateToken=_token(card))

    assert item["actions"][0]["publicState"]["user"] == {"name": "a"}


class LibraryCounter(LibraryComponent):
    template = """
      <span>{{ count }}</span>
    """

    class Kwargs:
        count: int = 0

    # A plain State the library author wrote as a dataclass.
    class State:
        count: int = 0


def test_a_library_components_state_keeps_the_kind_its_author_wrote() -> None:
    app = _citry(model_base=pydantic.BaseModel)

    installation = app.register_library(ComponentLibrary(name="pydantic-state-lib", components=(LibraryCounter,)))

    # The app's Pydantic base reaches the app's own State, not a library's.
    assert dataclasses.is_dataclass(installation.component(LibraryCounter).State)
