"""
Tests for the size check on a ``Decimal`` that a request supplies.

A short text such as ``"1e999999999"`` holds a number with a billion digits,
which a fixed-point format (``f"{amount:.2f}"``), ``"%d" % amount`` or
``int(amount)`` writes out in full. Citry refuses such a value from a
request with the same 422 ``invalid_args`` answer as any other bad
argument, on every route that turns request text into a ``Decimal``: an
Events argument checked by Citry or by Pydantic, sent as JSON or as a no-JS
form, and a browser write to a Pydantic State. The accepted range is the
one a float accepts: a size below ``1e309``, ignoring the sign, and at most
308 decimal places.

No test formats or converts a value above ``1e400``, so a run on a
release without the check stays cheap, while still failing the assertions.
"""

import dataclasses
import json
from collections.abc import Generator, Iterable
from decimal import Decimal
from typing import Annotated, Any

import pydantic
import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared_direct
from citry.ext.cache.errors import CacheArtifactError
from citry.ext.events.cache import stage_events_cache
from citry.ext.events.emission import EXTRA_KEY as EVENTS_EXTRA_KEY
from citry.ext.events.schemas import validate_args
from citry.ext.events.tokens import StateUpdateError, apply_state_updates, mint_state_token
from citry.extension import OnRenderCacheStageContext
from citry.util import decimals as decimals_module
from citry.util.decimals import (
    REQUEST_DECIMAL_MESSAGE,
    decimal_in_range,
    find_oversized_decimal,
    request_decimal_in_range,
)

pytest.importorskip("fastapi", reason="the HTTP route tests need fastapi + httpx2")
pytest.importorskip("httpx2", reason="Starlette's TestClient needs httpx2")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from citry.contrib.fastapi import mount

SIGNING_KEY = "decimal-size-test-secret-key"
ENVELOPE_HEADERS = {"Content-Type": "application/citry-events+json", "X-Citry-Events": "1"}


################################################
# THE SHARED CHECK
################################################


class TestRange:
    @pytest.mark.parametrize(
        "text",
        ["1e308", "9.999e308", "-1e308", "1e-308", "0.01", "19.99", "-1234567.89", "0", "1E+2"],
    )
    def test_accepts_values_inside_the_float_range(self, text):
        assert request_decimal_in_range(Decimal(text))

    @pytest.mark.parametrize(
        "text",
        # Too large; too many decimal places; a zero with a far exponent,
        # which `:f` also writes out digit by digit.
        ["1e309", "-1e309", "1e999999999", "1e-309", "1.5e-308", "0e-309", "0e309"],
    )
    def test_refuses_values_outside_the_float_range(self, text):
        assert not request_decimal_in_range(Decimal(text))

    def test_non_finite_values_have_no_digits_to_write(self):
        # Callers refuse NaN and infinity themselves, by `is_finite()`.
        assert request_decimal_in_range(Decimal("NaN"))
        assert request_decimal_in_range(Decimal("-Infinity"))

    def test_the_range_is_a_parameter(self):
        assert decimal_in_range(Decimal("1e32767"), largest=32767, smallest=-32768)
        assert not decimal_in_range(Decimal("1e32768"), largest=32767, smallest=-32768)


@dataclasses.dataclass(slots=True)
class _Slotted:
    note: str
    amount: Decimal


class _Extra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")
    name: str = "x"


class TestFindOversizedDecimal:
    def test_reports_the_first_path_in_field_and_item_order(self):
        value = {"a": [Decimal(1), Decimal("1e309"), Decimal("1e400")], "b": Decimal("1e400")}
        assert find_oversized_decimal(value) == ("a", 1)

    def test_reads_dataclass_fields_with_slots(self):
        assert find_oversized_decimal(_Slotted(note="n", amount=Decimal("1e-309"))) == ("amount",)

    def test_reads_pydantic_extra_values(self):
        model = _Extra.model_validate({"price": Decimal("1e309")})
        assert find_oversized_decimal(model) == ("price",)

    def test_a_dict_key_and_a_set_item_report_their_container(self):
        assert find_oversized_decimal({"m": {Decimal("1e309"): 1}}) == ("m", None)
        assert find_oversized_decimal({"m": {(Decimal(1), Decimal("1e309")): 1}}) == ("m", None, 1)
        assert find_oversized_decimal({"s": frozenset({Decimal("1e309")})}) == ("s", None)

    def test_reads_the_value_inside_a_pydantic_secret(self):
        assert find_oversized_decimal({"s": pydantic.Secret[Decimal](Decimal("1e309"))}) == ("s", None)

    def test_does_not_use_up_an_iterator(self):
        items = iter([Decimal("1e309")])
        assert find_oversized_decimal({"i": items}) is None
        assert next(items) == Decimal("1e309")

    def test_values_in_range_pass(self):
        assert find_oversized_decimal({"a": [Decimal("19.99"), "1e999999999", 10**400]}) is None


################################################
# EVENTS ARGUMENTS, CHECKED WITHOUT HTTP
################################################


class PlainArgs:
    amount: Decimal


class ListArgs:
    amounts: list[Decimal]
    prices: dict[str, Decimal]


class Inner:
    amount: Decimal


class NestedArgs:
    inner: Inner


class PydanticArgs(pydantic.BaseModel):
    amount: Decimal


class PydanticPlaces(pydantic.BaseModel):
    # `decimal_places` alone does not bound the exponent.
    amount: Annotated[Decimal, pydantic.Field(decimal_places=2)]


class PydanticMaxDigits(pydantic.BaseModel):
    amount: Annotated[Decimal, pydantic.Field(max_digits=12, decimal_places=2)]


class PydanticList(pydantic.BaseModel):
    amounts: list[Decimal]
    by_name: dict[str, Decimal]


class PlainHoldingPydantic:
    line: PydanticArgs


@pydantic.dataclasses.dataclass
class PydanticDataclassArgs:
    amount: Decimal


class PydanticIterable(pydantic.BaseModel):
    # Citry checks the items before the handler runs and hands it an
    # iterator over them, which the check after Pydantic cannot read.
    amounts: Iterable[Decimal]


class PydanticGenerator(pydantic.BaseModel):
    amounts: Generator[Decimal, None, None]


class PydanticAliased(pydantic.BaseModel):
    amount: Decimal = pydantic.Field(alias="Amount")


class PydanticTupleKeys(pydantic.BaseModel):
    # A JSON key is text, but `Json[...]` lets Pydantic parse it into a tuple.
    totals: dict[pydantic.Json[tuple[Decimal, ...]], int]


@pydantic.dataclasses.dataclass
class Filled:
    raw: str
    amount: Decimal = Decimal(0)


@pydantic.dataclasses.dataclass
class FillsInner:
    inner: Filled

    def __post_init__(self) -> None:
        # App code fills a field of an inner object that Citry already
        # walked when Pydantic built it.
        self.inner.amount = Decimal(self.inner.raw)


@dataclasses.dataclass
class PlainFillsInner:
    inner: Filled
    raw: str

    def __post_init__(self) -> None:
        self.inner.amount = Decimal(self.raw)


@pydantic.dataclasses.dataclass
class Chain:
    # Each level is a Pydantic dataclass, which Citry checks as it is built.
    amount: Decimal
    next: "Chain | None" = None


class TestEventArguments:
    @pytest.mark.parametrize("text", ["1e309", "1e-309", "1e999999999"])
    def test_citry_coercion_refuses_an_oversized_decimal(self, text):
        result = validate_args(PlainArgs, {"amount": text})
        assert result.fields == {"amount": REQUEST_DECIMAL_MESSAGE}

    @pytest.mark.parametrize("text", ["1e308", "1e-308", "19.99"])
    def test_citry_coercion_accepts_the_boundary(self, text):
        result = validate_args(PlainArgs, {"amount": text})
        assert result.ok
        assert result.value.amount == Decimal(text)

    def test_list_and_dict_items_name_their_path(self):
        result = validate_args(ListArgs, {"amounts": ["1", "1e309"], "prices": {"tea": "1e-400"}})
        assert result.fields == {"amounts.1": REQUEST_DECIMAL_MESSAGE, "prices.tea": REQUEST_DECIMAL_MESSAGE}

    def test_nested_object(self):
        result = validate_args(NestedArgs, {"inner": {"amount": "1e309"}})
        assert result.fields == {"inner.amount": REQUEST_DECIMAL_MESSAGE}

    @pytest.mark.parametrize("schema", [PydanticArgs, PydanticPlaces, PydanticDataclassArgs])
    def test_pydantic_refuses_an_oversized_decimal(self, schema):
        result = validate_args(schema, {"amount": "1e309"})
        assert result.fields == {"amount": REQUEST_DECIMAL_MESSAGE}

    def test_pydantic_accepts_the_boundary(self):
        assert validate_args(PydanticArgs, {"amount": "1e308"}).ok
        assert validate_args(PydanticArgs, {"amount": "1e-308"}).ok

    def test_pydantic_lists_and_dicts(self):
        result = validate_args(PydanticList, {"amounts": ["2", "1e309"], "by_name": {}})
        assert result.fields == {"amounts.1": REQUEST_DECIMAL_MESSAGE}
        result = validate_args(PydanticList, {"amounts": [], "by_name": {"tea": "1e-309"}})
        assert result.fields == {"by_name.tea": REQUEST_DECIMAL_MESSAGE}

    def test_pydantic_model_inside_a_plain_class(self):
        result = validate_args(PlainHoldingPydantic, {"line": {"amount": "1e309"}})
        assert result.fields == {"line.amount": REQUEST_DECIMAL_MESSAGE}

    def test_max_digits_keeps_its_own_pydantic_message(self):
        # Pydantic already refuses this value for having too many digits.
        result = validate_args(PydanticMaxDigits, {"amount": "1e309"})
        assert not result.ok
        assert result.fields["amount"] != REQUEST_DECIMAL_MESSAGE
        assert validate_args(PydanticMaxDigits, {"amount": "1234567890.12"}).ok

    def test_max_digits_does_not_bound_a_zero_and_the_check_still_runs(self):
        # Pydantic counts no digits in `0E-400`, so `max_digits` and
        # `decimal_places` accept it, while `f"{amount:f}"` writes 400 zeros.
        result = validate_args(PydanticMaxDigits, {"amount": "0E-400"})
        assert result.fields == {"amount": REQUEST_DECIMAL_MESSAGE}

    def test_a_decimal_a_codec_built_gets_the_same_check(self):
        assert validate_args(PlainArgs, {"amount": Decimal("1e400")}).fields == {"amount": REQUEST_DECIMAL_MESSAGE}

    @pytest.mark.parametrize("schema", [PydanticIterable, PydanticGenerator])
    def test_iterable_and_generator_items(self, schema):
        result = validate_args(schema, {"amounts": ["1", "1e309"]})
        assert result.fields == {"amounts": REQUEST_DECIMAL_MESSAGE}
        checked = validate_args(schema, {"amounts": ["1", "2.5"]})
        assert list(checked.value.amounts) == [Decimal(1), Decimal("2.5")]

    def test_an_aliased_field_is_named_as_the_request_names_it(self):
        result = validate_args(PydanticAliased, {"Amount": "1e309"})
        assert result.fields == {"Amount": REQUEST_DECIMAL_MESSAGE}

    def test_nested_pydantic_dataclasses_are_walked_once(self, monkeypatch):
        # Citry checks each level as it is built; the walks share what they
        # read, so the work stays in step with the size of the data.
        calls = []
        original = decimals_module._children
        monkeypatch.setattr(decimals_module, "_children", lambda item: calls.append(1) or original(item))
        payload: dict[str, Any] = {"amount": "1"}
        for _ in range(30):
            payload = {"amount": "1", "next": payload}
        assert validate_args(Chain, payload).ok
        # 31 objects, each read twice: once by the walks of the levels and
        # once by the walk of the finished value.
        assert len(calls) == 31 * 2
        payload["next"]["next"]["amount"] = "1e309"
        assert validate_args(Chain, payload).fields == {"next.next.amount": REQUEST_DECIMAL_MESSAGE}

    def test_a_dict_key_pydantic_parsed_into_a_tuple(self):
        result = validate_args(PydanticTupleKeys, {"totals": {'["1", "1e309"]': 1}})
        assert result.fields == {"totals": REQUEST_DECIMAL_MESSAGE}

    @pytest.mark.parametrize(
        ("schema", "payload"),
        [
            (FillsInner, {"inner": {"raw": "1e309"}}),
            (PlainFillsInner, {"inner": {"raw": "1"}, "raw": "1e309"}),
        ],
    )
    def test_a_decimal_written_into_an_object_already_walked(self, schema, payload):
        # The walks of one validation skip what an inner level read, so the
        # finished value is walked once more before the handler sees it.
        assert validate_args(schema, payload).fields == {"inner.amount": REQUEST_DECIMAL_MESSAGE}

    def test_the_message_does_not_echo_the_value(self):
        result = validate_args(PlainArgs, {"amount": "1e999999999"})
        assert "999999999" not in result.fields["amount"]


################################################
# STATE WRITES, CHECKED WITHOUT HTTP
################################################


class ModelState(pydantic.BaseModel):
    amount: Decimal = Decimal(0)
    history: list[Decimal] = pydantic.Field(default_factory=list)


# A Pydantic dataclass State takes only JSON values from the browser, so a
# `Decimal` field refuses the text form before Pydantic runs. A field typed
# `Any` whose validator builds a Decimal from the text still reaches Pydantic,
# and gets the same size check.
_DecimalFromText = Annotated[Any, pydantic.BeforeValidator(lambda value: Decimal(value))]


@pydantic.dataclasses.dataclass
class DataclassState:
    amount: _DecimalFromText = Decimal(0)


@pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(validate_assignment=True))
class AssigningState:
    amount: _DecimalFromText = Decimal(0)


@pydantic.dataclasses.dataclass
class StrictDataclassState:
    amount: Decimal = Decimal(0)


class DerivingState(pydantic.BaseModel):
    raw: str = "0"
    total: Decimal = Decimal(0)

    @pydantic.model_validator(mode="after")
    def _total_from_raw(self) -> "DerivingState":
        # The validator builds a Decimal from the browser's text.
        object.__setattr__(self, "total", Decimal(self.raw))
        return self


class TextDerivedState(pydantic.BaseModel):
    amount_text: str = "0"
    amount: Decimal = Decimal(0)

    @pydantic.model_validator(mode="before")
    @classmethod
    def _amount_from_text(cls, data: Any) -> Any:
        # A common "form text to number" pattern: the field is derived from
        # the text field the browser writes.
        if isinstance(data, dict):
            data = {**data, "amount": str(data.get("amount_text", "0")).replace(",", "")}
        return data


@pydantic.dataclasses.dataclass
class PostInitState:
    raw: str = ""
    # Unset until the browser writes `raw`, since a token holds JSON only.
    total: Any = None

    def __post_init__(self) -> None:
        self.total = Decimal(self.raw) if self.raw else None


class TestStateWrites:
    def test_a_derived_field_equal_to_its_old_value_is_checked(self):
        # `Decimal("0E-1000000") == Decimal(0)`, but `f"{amount:f}"` writes
        # a million zeros, so every field is checked, not only changed ones.
        state = TextDerivedState()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"amount_text": "0E-1000000"}, model_fields={"amount_text"})
        assert caught.value.fields == {"amount": REQUEST_DECIMAL_MESSAGE}
        assert state.amount_text == "0"

    def test_a_field_post_init_derives_in_a_pydantic_dataclass_state(self):
        state = PostInitState()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"raw": "1e309"}, model_fields={"raw"})
        assert caught.value.fields == {"total": REQUEST_DECIMAL_MESSAGE}
        assert state.raw == ""

    def test_a_field_a_validator_derives_from_a_write_is_checked(self):
        state = DerivingState()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"raw": "1e309"}, model_fields={"raw"})
        assert caught.value.fields == {"total": REQUEST_DECIMAL_MESSAGE}
        assert state.total == Decimal(0)
        apply_state_updates(state, {"raw": "19.99"}, model_fields={"raw"})
        assert state.total == Decimal("19.99")

    def test_a_nested_pydantic_v1_model_in_a_v1_state(self):
        v1 = pytest.importorskip("pydantic.v1")

        class Line(v1.BaseModel):
            price: Decimal

        class V1State(v1.BaseModel):
            lines: list[Line] = []

        state = V1State()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"lines": [{"price": "1"}, {"price": "1e309"}]}, model_fields={"lines"})
        assert caught.value.fields == {"lines.1.price": REQUEST_DECIMAL_MESSAGE}
        assert state.lines == []

    @pytest.mark.parametrize("state_cls", [ModelState, DataclassState, AssigningState])
    @pytest.mark.parametrize("text", ["1e309", "1e-309"])
    def test_refuses_an_oversized_decimal_and_keeps_the_state(self, state_cls, text):
        state = state_cls()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"amount": text}, model_fields={"amount"})
        assert caught.value.fields == {"amount": REQUEST_DECIMAL_MESSAGE}
        assert state.amount == Decimal(0)

    # Without `validate_assignment` a Pydantic dataclass keeps the browser's
    # text until the next restore, so only the two that convert are compared.
    @pytest.mark.parametrize("state_cls", [ModelState, AssigningState])
    def test_accepts_money(self, state_cls):
        state = state_cls()
        apply_state_updates(state, {"amount": "19.99"}, model_fields={"amount"})
        assert state.amount == Decimal("19.99")

    def test_a_decimal_field_of_a_pydantic_dataclass_refuses_text(self):
        state = StrictDataclassState()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"amount": "1e309"}, model_fields={"amount"})
        assert caught.value.fields == {"amount": "Expected Decimal, got str."}

    def test_list_item_in_a_model_state(self):
        state = ModelState()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"history": ["1", "1e400"]}, model_fields={"history"})
        assert caught.value.fields == {"history.1": REQUEST_DECIMAL_MESSAGE}


################################################
# OVER HTTP
################################################


class PayIn:
    amount: Decimal


class WalletState(pydantic.BaseModel):
    amount: Decimal = Decimal(0)


class StoredWalletState(pydantic.BaseModel):
    amount: Decimal = Decimal(0)
    _storage = "server"


def _app():
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Pay(Component):
        citry = c
        template = """
<p>ok</p>
"""

        class Events:
            def pay(self, data: PayIn):
                return None

            def pay_model(self, data: PydanticPlaces):
                return None

    class Wallet(Component):
        citry = c
        State = WalletState
        template = """
<p>ok</p>
"""

        class Events:
            def show(self, state: WalletState):
                return None

    class StoredWallet(Component):
        citry = c
        State = StoredWalletState
        template = """
<p>ok</p>
"""

        class Events:
            def show(self, state: StoredWalletState):
                return None

    app = FastAPI()
    mount(app, c)
    return TestClient(app), Pay, Wallet, StoredWallet, c


def _url(comp_cls, name):
    return f"/citry/ext/events/e/{comp_cls.class_id}/{name}"


def _post_call(client, comp_cls, name, **call):
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "calls": [{"componentClassId": comp_cls.class_id, "handlerName": name, "args": {}, **call}],
    }
    return client.post(_url(comp_cls, name), content=json.dumps(envelope), headers=ENVELOPE_HEADERS)


def _call_error(response):
    [result] = response.json()["results"]
    assert result["ok"] is False
    return result["error"]


class TestHttpRoutes:
    @pytest.mark.parametrize("handler", ["pay", "pay_model"])
    def test_events_envelope_refuses_with_invalid_args(self, handler):
        client, pay, _wallet, *_ = _app()
        response = _post_call(client, pay, handler, args={"amount": "1e309"})
        error = _call_error(response)
        assert error["status"] == 422
        assert error["code"] == "invalid_args"
        assert error["fieldErrors"] == {"amount": REQUEST_DECIMAL_MESSAGE}

    def test_events_envelope_accepts_money(self):
        client, pay, _wallet, *_ = _app()
        [result] = _post_call(client, pay, "pay", args={"amount": "19.99"}).json()["results"]
        assert result["ok"] is True

    def test_no_js_form_post_refuses_with_a_422(self):
        client, pay, _wallet, *_ = _app()
        response = client.post(_url(pay, "pay"), data={"amount": "1e309"})
        assert response.status_code == 422
        assert response.text.split("\n")[1] == f"amount: {REQUEST_DECIMAL_MESSAGE}"

    def test_pydantic_state_write_refuses_with_invalid_args(self):
        client, _pay, wallet, *_ = _app()
        token = mint_state_token(
            WalletState(), class_id=wallet.class_id, secret=SIGNING_KEY, max_age=None, max_bytes=8192
        )
        response = _post_call(
            client,
            wallet,
            "show",
            callerRenderId="c1",
            stateToken=token,
            stateUpdates={"amount": "1e-309"},
        )
        error = _call_error(response)
        assert error["status"] == 422
        assert error["code"] == "invalid_args"
        assert error["fieldErrors"] == {"amount": REQUEST_DECIMAL_MESSAGE}


class TestRestoredState:
    # A token signed by an earlier release holds whatever the browser wrote
    # then. `mint_state_token` signs any value, as the release did.

    @pytest.mark.parametrize("storage", ["signed", "server"])
    @pytest.mark.parametrize("updates", [None, {"amount": "1"}])
    def test_a_token_holding_an_oversized_decimal_is_refused(self, storage, updates):
        client, _pay, wallet, stored_wallet, c = _app()
        state_cls = WalletState
        if storage == "server":
            wallet, state_cls = stored_wallet, StoredWalletState
        token = mint_state_token(
            state_cls(amount=Decimal("1e400")),
            class_id=wallet.class_id,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
            storage=storage,
            cache=c.cache,
        )
        call: dict[str, Any] = {"callerRenderId": "c1", "stateToken": token}
        if updates is not None:
            call["stateUpdates"] = updates
        error = _call_error(_post_call(client, wallet, "show", **call))
        assert error["status"] == 422
        assert error["code"] == "invalid_args"
        assert error["fieldErrors"] == {"amount": REQUEST_DECIMAL_MESSAGE}

    def test_a_token_holding_money_still_works(self):
        client, _pay, wallet, *_ = _app()
        token = mint_state_token(
            WalletState(amount=Decimal("19.99")),
            class_id=wallet.class_id,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        [result] = _post_call(client, wallet, "show", callerRenderId="c1", stateToken=token).json()["results"]
        assert result["ok"] is True


# A State the server made before this release, holding a value a browser
# wrote then. Neither kind is checked when the server builds it.
class CachedModelState(pydantic.BaseModel):
    amount: Decimal = Decimal("1e400")


# A Pydantic dataclass State keeps text in its token and builds the
# Decimal when it is restored.
@pydantic.dataclasses.dataclass
class CachedTextState:
    amount: _DecimalFromText = "1e400"


def _stage_cached_render(c, entry):
    """Stage the Events part of a cached render of ``entry``, as a cache hit does."""
    payload = {
        "instances": [
            {
                "class_id": entry.component_class_id,
                "instance": 0,
                "state": {
                    "storage": "signed",
                    "token": entry.state_token,
                    "values": json.loads(entry.public_state_json),
                },
            }
        ]
    }
    context = OnRenderCacheStageContext(
        citry=c,
        payload=payload,
        instance_ids=("c1abcdef",),
        instance_class_ids=(entry.component_class_id,),
        parent_ids=(),
        provided_render_ids={},
    )
    return stage_events_cache(c.extensions.get_extension("events"), context)


@pytest.mark.parametrize("state_cls", [CachedModelState, CachedTextState])
def test_a_cached_render_with_an_oversized_state_decimal_is_not_replayed(state_cls):
    # Replaying a cached render signs its State token again with a new
    # expiry, so a token holding such a value makes the render start afresh.
    c = Citry(secret=SIGNING_KEY)

    class Card(Component):
        citry = c
        State = state_cls
        template = """
<button @c-click="show">go</button>
"""

        class Cache:
            enabled = True

        class Events:
            def show(self, state):
                return None

    entry = next(iter(render_prepared_direct(Card()).context.extra[EVENTS_EXTRA_KEY]))
    with pytest.raises(CacheArtifactError, match="holds a Decimal outside the request range"):
        _stage_cached_render(c, entry)


def test_a_cached_render_with_money_in_its_state_is_replayed():
    c = Citry(secret=SIGNING_KEY)

    class Card(Component):
        citry = c
        State = WalletState
        template = """
<button @c-click="show">go</button>
"""

        class Cache:
            enabled = True

        class Events:
            def show(self, state):
                return None

    entry = next(iter(render_prepared_direct(Card()).context.extra[EVENTS_EXTRA_KEY]))
    assert _stage_cached_render(c, entry).frame_markers == ((0, ('data-cid="c1abcdef"',)),)


################################################
# THE SINKS AT THE BOUNDARY
################################################


class TestSinksAtTheBoundary:
    def test_the_largest_accepted_value_formats_quickly(self):
        # At the boundary, a fixed-point format and `%d` write 309 digits,
        # which is cheap, so the bound leaves the sinks harmless.
        amount = validate_args(PlainArgs, {"amount": "1e308"}).value.amount
        c = Citry()
        html = str(
            c.render_template(
                """
<p>{{ f"{amount:.2f}" }}|{{ "%d" % amount }}</p>
""",
                {"amount": amount},
            )
        )
        fixed, integer = html.strip().removeprefix("<p>").removesuffix("</p>").split("|")
        assert fixed == "1" + "0" * 308 + ".00"
        assert integer == "1" + "0" * 308

    def test_money_still_formats(self):
        amount = validate_args(PlainArgs, {"amount": "1234.5"}).value.amount
        html = str(
            Citry().render_template(
                """
<p>{{ f"{amount:,.2f}" }}</p>
""",
                {"amount": amount},
            )
        )
        assert html.strip() == "<p>1,234.50</p>"
