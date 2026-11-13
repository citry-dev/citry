"""
Tests for the events state tokens (docs/design/events.md sections 7.1 and 7.2):
minting and verifying the signed State token, the opt-in server-side store, and
applying two-way binding updates under the ``_model`` gate.

The golden token strings are authored observe-then-lock: they were produced by
running the real ``mint_state_token`` with a pinned clock, a fixed secret, and a
fixed State, then locked here. The clock is pinned by monkeypatching the
module-level ``_now`` so the timestamp field (the one non-deterministic input) is
fixed.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import logging
import typing
from dataclasses import dataclass, field, make_dataclass
from datetime import timedelta
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Literal, Protocol, TypedDict

import pytest
import typing_extensions

from citry.cache import InMemoryCache
from citry.ext.events import _pydantic_bounded as bounded
from citry.ext.events import tokens
from citry.ext.events.schemas import PATHS_TOO_LONG_MESSAGE
from citry.ext.events.state import check_changed_state, restore_state
from citry.ext.events.tokens import (
    InvalidStateError,
    SigningSecretError,
    StaleStateError,
    StateUpdateError,
    VerifiedState,
    apply_state_updates,
    mint_state_token,
    verify_state_token,
)

if TYPE_CHECKING:
    # Imported only for type checking, so at runtime the ``exotic`` field below
    # has an annotation that resolving the whole class's hints cannot resolve.
    from decimal import Decimal

FIXED_NOW = 1_700_000_000.0

# Signing keys held in variables (never passed as string literals to the
# ``secret=`` parameter), so the values are stable across tests.
SIGNING_KEY = "test-secret-key"
OLD_KEY = "old-signing-key"
NEW_KEY = "new-signing-key"

CLASS_ID = "Counter_ab12cd"

# The protocol package's golden exchanges, the wire contract for error statuses
# and codes (see the tests README). Conformance tests read the expected
# values from these files rather than copying them by hand.
TESTS_DIR = Path(__file__).resolve().parents[4] / "packages" / "protocol" / "events" / "v1" / "tests"

# Locked golden vectors: mint(CounterState(count=3, label="hi"),
# class_id=CLASS_ID, secret=SIGNING_KEY, _now=FIXED_NOW).
GOLDEN_NO_EXPIRY = "cev1.eyJjIjoiQ291bnRlcl9hYjEyY2QiLCJzIjp7ImNvdW50IjozLCJsYWJlbCI6ImhpIn0sInQiOjE3MDAwMDAwMDAsInYiOjEsIngiOm51bGx9.7jlis78Jj3-eReJNBQ-ZAE6g8875aNn3QdSbDutdndk"  # noqa: E501
GOLDEN_WITH_EXPIRY = "cev1.eyJjIjoiQ291bnRlcl9hYjEyY2QiLCJzIjp7ImNvdW50IjozLCJsYWJlbCI6ImhpIn0sInQiOjE3MDAwMDAwMDAsInYiOjEsIngiOjE3MDAwMDM2MDB9.Ss0KHdwx1rZqbHsgHrpxHmR8waawjODipotVIeAFzdo"  # noqa: E501


@dataclass
class CounterState:
    count: int = 0
    label: str = ""


@dataclass
class WidgetState:
    count: int = 0
    query: str = ""
    enabled: bool = False
    note: str | None = None


@dataclass
class ShapedState:
    # Fields whose types have parts the browser's value is checked against.
    choice: Literal["a", "b"] = "a"
    one: Literal[1] = 1
    tags: list[int] = field(default_factory=list)
    grid: list[list[int]] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)
    pair: tuple[int, str] = (0, "")
    runs: tuple[int, ...] = ()
    maybe_tags: list[int] | None = None


class Point(TypedDict):
    x: int


class Reader(Protocol):
    # Not @runtime_checkable, so isinstance() refuses it.
    def read(self) -> str: ...


class Color(str, Enum):
    RED = "red"
    BLUE = "blue"


class Shade(Enum):
    # No str or int mix-in, so a member is not equal to its value.
    DARK = "dark"


class ExtensionPoint(typing_extensions.TypedDict):
    x: int


@dataclass
class EnumShapeState:
    # Field types a dataclass State stores as plain JSON.
    extension_point: ExtensionPoint = field(default_factory=lambda: {"x": 0})
    colors: list[Color] = field(default_factory=list)
    color_map: dict[str, Color] = field(default_factory=dict)
    shade: Shade = Shade.DARK
    combo: typing.Tuple = ()  # noqa: UP006


@dataclass
class TypedShapeState:
    # Field types whose check has a special case of its own.
    points: list[Point] = field(default_factory=list)
    origin: Point = field(default_factory=lambda: {"x": 0})
    point_map: dict[str, Point] = field(default_factory=dict)
    readers: list[Reader] = field(default_factory=list)
    reader: Reader | None = None
    ratio: Literal[1.0, 2.5] = 1.0
    color: Literal[Color.RED, Color.BLUE] = Color.RED
    nothing: tuple[()] = ()
    anything: tuple = ()
    either: list[int] | list[str] = field(default_factory=list)
    numbers: list[int] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)


@dataclass
class PartlyResolvableState:
    # ``exotic`` is annotated with a type importable only under TYPE_CHECKING, so
    # resolving the whole class's hints at once fails; ``count`` must still be
    # type-checked and only ``exotic`` fall back to a lenient check.
    count: int = 0
    exotic: Decimal = None


# Stand-in component classes: verify only reads ``cls.class_id`` for the
# class-id binding check, so a plain attribute is enough.
class FakeCounter:
    class_id = CLASS_ID
    State = CounterState


class OtherComp:
    class_id = "Other_zz9999"
    State = CounterState


class RecordingCache:
    """A cache that records the ttl each ``set`` received."""

    def __init__(self):
        self.store = {}
        self.ttls = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ttl=None):
        self.store[key] = value
        self.ttls[key] = ttl

    def delete(self, key):
        self.store.pop(key, None)

    def has(self, key):
        return key in self.store


def _pin_now(monkeypatch, value=FIXED_NOW):
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: value)


def _forge_signed_token(payload_bytes):
    # A cev1 token signed with a key no test ever verifies against, so the HMAC
    # cannot match and verification must pick the error code from the payload
    # alone (the no-match classification of design 4.3).
    signature = hmac.new(b"key-the-verifier-does-not-know", payload_bytes, hashlib.sha256).digest()
    return f"cev1.{tokens._b64url_encode(payload_bytes)}.{tokens._b64url_encode(signature)}"


class TestMintGoldenVectors:
    def test_no_expiry_exact_token(self, monkeypatch):
        _pin_now(monkeypatch)
        token = mint_state_token(
            CounterState(count=3, label="hi"),
            class_id=CLASS_ID,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        assert token == GOLDEN_NO_EXPIRY

    def test_with_expiry_exact_token(self, monkeypatch):
        _pin_now(monkeypatch)
        token = mint_state_token(
            CounterState(count=3, label="hi"),
            class_id=CLASS_ID,
            secret=SIGNING_KEY,
            max_age=timedelta(hours=1),
            max_bytes=8192,
        )
        assert token == GOLDEN_WITH_EXPIRY

    def test_field_declaration_order_does_not_change_token(self, monkeypatch):
        _pin_now(monkeypatch)

        @dataclass
        class ReorderedState:
            label: str = ""
            count: int = 0

        token = mint_state_token(
            ReorderedState(label="hi", count=3),
            class_id=CLASS_ID,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        # Canonical JSON sorts keys, so the token is identical to the one from a
        # State that declares the same fields in the other order.
        assert token == GOLDEN_NO_EXPIRY

    def test_dict_value_key_order_does_not_change_token(self, monkeypatch):
        _pin_now(monkeypatch)

        @dataclass
        class DictState:
            data: dict = None

        first = mint_state_token(
            DictState(data={"a": 1, "b": 2}),
            class_id="X_1",
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        second = mint_state_token(
            DictState(data={"b": 2, "a": 1}),
            class_id="X_1",
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        assert first == second

    def test_unicode_state_round_trips(self, monkeypatch):
        _pin_now(monkeypatch)
        token = mint_state_token(
            CounterState(count=1, label="café ☕"),
            class_id=CLASS_ID,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        verified = verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert verified.state_kwargs["label"] == "café ☕"


class TestMintGuards:
    def test_none_state_rejected(self):
        with pytest.raises(ValueError, match="requires a State instance"):
            mint_state_token(None, class_id="X_1", secret=SIGNING_KEY, max_age=None, max_bytes=8192)

    def test_unknown_storage_rejected(self):
        with pytest.raises(ValueError, match="Unknown storage mode"):
            mint_state_token(
                CounterState(), class_id="X_1", secret=SIGNING_KEY, max_age=None, max_bytes=8192, storage="weird"
            )

    def test_json_unsafe_field_names_field_and_fix(self):
        class NotJson:
            pass

        @dataclass
        class BadState:
            obj: object = None

        with pytest.raises(ValueError, match="not JSON-serializable") as exc_info:
            mint_state_token(
                BadState(obj=NotJson()), class_id=CLASS_ID, secret=SIGNING_KEY, max_age=None, max_bytes=8192
            )
        assert "'obj'" in str(exc_info.value)  # names the offending field

    def test_over_max_bytes_names_cap_and_guidance(self):
        big = CounterState(count=1, label="x" * 10_000)
        with pytest.raises(ValueError, match="_max_bytes cap of 100") as exc_info:
            mint_state_token(big, class_id=CLASS_ID, secret=SIGNING_KEY, max_age=None, max_bytes=100)
        assert "Keep an id in State" in str(exc_info.value)  # the id-plus-reload guidance

    def test_max_bytes_not_enforced_for_server_storage(self):
        cache = InMemoryCache()
        big = CounterState(count=1, label="x" * 10_000)
        token = mint_state_token(
            big, class_id=CLASS_ID, secret=None, max_age=None, max_bytes=10, storage="server", cache=cache
        )
        assert token.startswith("ces1.")

    def test_server_state_is_stored_under_the_citry_namespace(self):
        # Citry's cache keys share the ``citry:`` namespace, so State can sit
        # in a cache shared with the host app without colliding with its keys.
        cache = InMemoryCache()
        token = mint_state_token(
            CounterState(count=1),
            class_id=CLASS_ID,
            secret=None,
            max_age=None,
            max_bytes=10,
            storage="server",
            cache=cache,
        )
        key = token.removeprefix("ces1.")
        assert cache.get(f"citry:state:{key}") is not None
        assert cache.get(key) is None

    def test_server_token_cannot_read_a_key_outside_the_state_namespace(self):
        # The key in a token is client input; it must only ever address
        # State entries, never another cache entry it happens to name.
        cache = InMemoryCache()
        cache.set(
            "user-key",
            tokens._canonical_json({"v": 1, "c": CLASS_ID, "s": {"count": 1}, "t": 0, "x": None}),
            ttl=None,
        )
        with pytest.raises(StaleStateError):
            verify_state_token("ces1.user-key", cls=FakeCounter, secrets=[], cache=cache)

    def test_missing_secret_raises_pointed_error(self):
        with pytest.raises(SigningSecretError) as exc_info:
            mint_state_token(CounterState(), class_id=CLASS_ID, secret=None, max_age=None, max_bytes=8192)
        message = str(exc_info.value)
        assert "No signing secret is configured" in message
        assert "Citry(secret=" in message
        assert "citry.contrib.django.secret()" in message

    def test_empty_secret_list_raises(self):
        with pytest.raises(SigningSecretError):
            mint_state_token(CounterState(), class_id=CLASS_ID, secret=[], max_age=None, max_bytes=8192)

    def test_dict_with_all_integer_keys_rejected(self):
        # A dict whose keys are all non-string (here integers) serializes under a
        # plain json.dumps AND sorts, so it slipped past the canonicalization probe
        # and silently round-tripped with its keys rewritten to strings (1 came back
        # as "1"). It must instead be the friendly, field-naming mint error.
        @dataclass
        class IntKeyState:
            data: dict = None

        with pytest.raises(ValueError, match="non-string key") as exc_info:
            mint_state_token(
                IntKeyState(data={1: "a", 2: "b"}),
                class_id=CLASS_ID,
                secret=SIGNING_KEY,
                max_age=None,
                max_bytes=8192,
            )
        message = str(exc_info.value)
        assert "'data'" in message  # names the offending field
        assert "of type int" in message  # names the key and its type
        assert "Use string keys" in message  # points at the fix
        # An int-keyed dict IS json.dumps-serializable, so the message must not
        # claim otherwise (that wording is reserved for genuinely unserializable
        # values, e.g. a custom object).
        assert "not JSON-serializable" not in message

    def test_various_non_string_dict_keys_rejected(self):
        # int is covered above; float, bool, and None keys also coerce to strings
        # and do not round-trip, so each is rejected the same way.
        @dataclass
        class KeyState:
            data: dict = None

        for bad in ({1.5: "a"}, {True: "a"}, {None: "a"}):
            with pytest.raises(ValueError, match="non-string key") as exc_info:
                mint_state_token(
                    KeyState(data=bad),
                    class_id=CLASS_ID,
                    secret=SIGNING_KEY,
                    max_age=None,
                    max_bytes=8192,
                )
            assert "'data'" in str(exc_info.value)

    def test_dict_with_mixed_keys_rejected(self):
        # Mixed str/int keys do not round-trip either (the int key is rewritten).
        # The first non-string key is named, deterministically (dicts keep insertion
        # order). This case is json.dumps-serializable but not sortable, so the
        # message must be the key wording, not "not JSON-serializable".
        @dataclass
        class MixedKeyState:
            data: dict = None

        with pytest.raises(ValueError, match="non-string key") as exc_info:
            mint_state_token(
                MixedKeyState(data={1: "a", "b": 2}),
                class_id=CLASS_ID,
                secret=SIGNING_KEY,
                max_age=None,
                max_bytes=8192,
            )
        message = str(exc_info.value)
        assert "'data'" in message
        assert "of type int" in message  # the int key, hit first
        assert "not JSON-serializable" not in message

    def test_non_string_dict_keys_rejected_in_server_mode(self):
        # The JSON-safe enforcement runs before the server-storage split, so server
        # mode gets the same friendly error rather than a crash in the cache write.
        @dataclass
        class IntKeyState:
            data: dict = None

        with pytest.raises(ValueError, match="non-string key") as exc_info:
            mint_state_token(
                IntKeyState(data={1: "a", 2: "b"}),
                class_id=CLASS_ID,
                secret=None,
                max_age=None,
                max_bytes=8192,
                storage="server",
                cache=InMemoryCache(),
            )
        assert "'data'" in str(exc_info.value)

    def test_nested_non_string_dict_keys_rejected(self):
        # The check is recursive: a non-string key nested inside a dict value or a
        # list is caught too, so it cannot slip through under a string-keyed outer
        # dict.
        @dataclass
        class NestedState:
            data: dict = None

        for bad in ({"outer": {1: "x"}}, {"items": [{2: "y"}]}):
            with pytest.raises(ValueError, match="non-string key") as exc_info:
                mint_state_token(
                    NestedState(data=bad),
                    class_id=CLASS_ID,
                    secret=SIGNING_KEY,
                    max_age=None,
                    max_bytes=8192,
                )
            assert "'data'" in str(exc_info.value)  # names the top-level field, not the nested one

    def test_circular_state_value_raises_circular_reference_error(self):
        # A self-referential container must fail the same way on every mint
        # path: json's circular-reference ValueError (raised by the
        # canonical-JSON probe), not a RecursionError out of the recursive
        # non-string-key walk, which runs first.
        @dataclass
        class LoopState:
            data: object = None

        loop_dict: dict = {}
        loop_dict["self"] = loop_dict
        loop_list: list = []
        loop_list.append(loop_list)
        for bad in (loop_dict, loop_list, {"items": [loop_dict]}):
            with pytest.raises(ValueError, match="Circular reference"):
                mint_state_token(
                    LoopState(data=bad),
                    class_id=CLASS_ID,
                    secret=SIGNING_KEY,
                    max_age=None,
                    max_bytes=8192,
                )

    @pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
    @pytest.mark.parametrize("storage", ["signed", "server"])
    def test_non_finite_state_value_is_rejected_with_its_field(self, value, storage):
        @dataclass
        class FloatState:
            ratio: float = 0.0

        with pytest.raises(ValueError, match=r"State field 'ratio'.*non-finite float"):
            mint_state_token(
                FloatState(ratio=value),
                class_id=CLASS_ID,
                secret=SIGNING_KEY if storage == "signed" else None,
                max_age=None,
                max_bytes=8192,
                storage=storage,
                cache=InMemoryCache() if storage == "server" else None,
            )

    def test_shared_substructure_still_mints(self):
        # The cycle guard skips only containers it has already visited; a value
        # shared twice WITHOUT a cycle is legitimate and must keep minting.
        @dataclass
        class SharedState:
            data: dict = None

        shared = {"a": 1}
        token = mint_state_token(
            SharedState(data={"x": shared, "y": shared}),
            class_id=CLASS_ID,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        assert token.startswith("cev1.")


class TestVerifyRoundTrip:
    def test_round_trip_returns_kwargs_and_class_id(self, monkeypatch):
        _pin_now(monkeypatch)
        token = mint_state_token(
            CounterState(count=7, label="x"), class_id=CLASS_ID, secret=SIGNING_KEY, max_age=None, max_bytes=8192
        )
        verified = verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert isinstance(verified, VerifiedState)
        assert verified.state_kwargs == {"count": 7, "label": "x"}
        assert verified.class_id == CLASS_ID


class TestSigningKeyLabel:
    def _signed_with(self, key: bytes) -> str:
        # The payload of a real token, so only the signature differs.
        payload_bytes = tokens._b64url_decode(GOLDEN_NO_EXPIRY.split(".")[1])
        signature = hmac.new(key, payload_bytes, hashlib.sha256).digest()
        return f"cev1.{tokens._b64url_encode(payload_bytes)}.{tokens._b64url_encode(signature)}"

    def test_a_payload_signed_with_the_raw_secret_is_refused(self):
        # Other code that signs with the same secret (an app helper that
        # signs with Django's SECRET_KEY, say) produces exactly this. It
        # matches no current key, so it is stale, like a token signed by a
        # removed secret.
        token = self._signed_with(SIGNING_KEY.encode("utf-8"))
        with pytest.raises(StaleStateError):
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])

    def test_a_payload_signed_with_the_labelled_key_verifies(self):
        # The control for the test above: the same payload, signed with the
        # key derived from the label, is accepted.
        key = hmac.new(b"citry.events.state-token", SIGNING_KEY.encode("utf-8"), hashlib.sha256).digest()
        verified = verify_state_token(self._signed_with(key), cls=FakeCounter, secrets=[SIGNING_KEY])
        assert verified.state_kwargs == {"count": 3, "label": "hi"}


class TestRotation:
    def test_old_token_still_verifies_under_rotation_list(self):
        old_token = mint_state_token(
            CounterState(count=5), class_id=CLASS_ID, secret=OLD_KEY, max_age=None, max_bytes=8192
        )
        verified = verify_state_token(old_token, cls=FakeCounter, secrets=[NEW_KEY, OLD_KEY])
        assert verified.state_kwargs["count"] == 5

    def test_rotation_list_signs_with_first_entry(self):
        token = mint_state_token(
            CounterState(count=5), class_id=CLASS_ID, secret=[NEW_KEY, OLD_KEY], max_age=None, max_bytes=8192
        )
        # Verifies under the new (first) key alone.
        verified = verify_state_token(token, cls=FakeCounter, secrets=[NEW_KEY])
        assert verified.state_kwargs["count"] == 5
        # Under only the retired key the signature matches nothing, and a
        # well-formed token that verifies against no current secret is stale
        # (409), not invalid: it looks exactly like a rotated-out token
        # (design 4.3).
        with pytest.raises(StaleStateError):
            verify_state_token(token, cls=FakeCounter, secrets=[OLD_KEY])


class TestInvalidState:
    def _mint(self):
        return mint_state_token(
            CounterState(count=1), class_id=CLASS_ID, secret=SIGNING_KEY, max_age=None, max_bytes=8192
        )

    def test_tampered_payload(self):
        # Corrupting the payload segment invalidates the signature AND breaks
        # the payload itself: the JSON always ends in "}", and swapping the
        # last base64 character for "A" (all-zero bits) always rewrites that
        # closing byte, because "}" never encodes to an all-zero final
        # character (an arbitrary flip could decode to the same bytes through
        # the discarded padding bits; see test_tampered_signature). The JSON
        # no longer parses, and an unreadable payload under a failed signature
        # is invalid_state (403) per the 4.3 split, unlike a signature-only
        # tamper, which keeps the payload well-formed and answers stale (409).
        token = self._mint()
        prefix, payload_b64, sig = token.split(".")
        tampered_payload = payload_b64[:-1] + ("A" if payload_b64[-1] != "A" else "B")
        tampered = f"{prefix}.{tampered_payload}.{sig}"
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(tampered, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403
        assert exc_info.value.code == "invalid_state"

    def test_unverified_bad_json_payload_is_invalid(self):
        # The signature matches nothing and the payload is not JSON at all:
        # less than a well-formed token, so invalid_state (403) per 4.3.
        token = _forge_signed_token(b'{"v": 1, "c": ')
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403
        assert exc_info.value.code == "invalid_state"

    def test_unverified_wrong_version_payload_is_invalid(self):
        # An unverifiable signature over a payload declaring another protocol
        # version is not a well-formed v1 token: invalid_state (403), not stale.
        payload = tokens._canonical_json({"v": 2, "c": CLASS_ID, "s": {"count": 1}, "t": 0, "x": None})
        token = _forge_signed_token(payload.encode("utf-8"))
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403
        assert exc_info.value.code == "invalid_state"

    def test_unverified_payload_missing_fields_is_invalid(self):
        # A well-formed token needs the component class ("c") and state ("s")
        # fields; a payload missing either is malformed, so the no-match split
        # answers invalid_state (403), not stale_state.
        missing_c = {"v": 1, "s": {"count": 1}, "t": 0, "x": None}
        missing_s = {"v": 1, "c": CLASS_ID, "t": 0, "x": None}
        for payload in (missing_c, missing_s):
            token = _forge_signed_token(tokens._canonical_json(payload).encode("utf-8"))
            with pytest.raises(InvalidStateError) as exc_info:
                verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
            assert exc_info.value.status == 403
            assert exc_info.value.code == "invalid_state"

    def test_unverified_non_utf8_payload_is_invalid(self):
        # The payload segment decodes to bytes that are not UTF-8, so the
        # payload cannot be read as JSON at all: less than a well-formed
        # token, so the no-match split answers invalid_state (403) rather
        # than letting the parser's UnicodeDecodeError escape verify as a
        # crash.
        token = _forge_signed_token(b"\xff\xff\xff")
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403
        assert exc_info.value.code == "invalid_state"

    def test_unverified_deeply_nested_payload_is_invalid(self):
        # A payload nested too deep for the JSON parser (an attacker can send
        # one; no minted token can be this deep) is just as unreadable as bad
        # JSON: invalid_state (403), not a RecursionError escaping verify.
        token = _forge_signed_token(("[" * 20_000 + "]" * 20_000).encode())
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403
        assert exc_info.value.code == "invalid_state"

    def test_unverified_bad_payload_base64_is_invalid(self):
        # A payload segment that cannot be base64 at all (non-ascii characters
        # raise in the decoder) is rejected before any signature check, and
        # stays invalid_state (403) per the 4.3 list. (Base64-alphabet garbage
        # like "!!!" reaches the same 403 by a different route: the lenient
        # decoder accepts it as empty bytes, which then fail the no-match
        # classification's JSON parse; see test_bad_base64_malformed.)
        sig = tokens._b64url_encode(b"not-a-real-signature")
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(f"cev1.päyload.{sig}", cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403
        assert exc_info.value.code == "invalid_state"

    def test_unknown_prefix_malformed(self):
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token("garbage-no-prefix", cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403
        assert "malformed" in exc_info.value.message.lower()

    def test_bad_base64_malformed(self):
        # The lenient base64 decoder accepts "!!!" and "###" as empty bytes,
        # so this reaches the signature check (which matches nothing) and gets
        # its 403 from the no-match classification: empty bytes are not JSON.
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token("cev1.!!!.###", cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403

    def test_wrong_protocol_version_malformed(self):
        # A validly-signed token whose payload declares v=2 is still rejected.
        payload = {"v": 2, "c": CLASS_ID, "s": {"count": 1}, "t": 0, "x": None}
        payload_bytes = tokens._canonical_json(payload).encode("utf-8")
        signature = hmac.new(tokens._state_token_key(SIGNING_KEY), payload_bytes, hashlib.sha256).digest()
        token = f"cev1.{tokens._b64url_encode(payload_bytes)}.{tokens._b64url_encode(signature)}"
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403

    def test_class_id_mismatch(self):
        token = self._mint()
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(token, cls=OtherComp, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 403
        message = exc_info.value.message
        assert "different component" in message
        assert CLASS_ID in message
        assert "Other_zz9999" in message

    def test_non_string_token_is_invalid_not_crash(self):
        # A missing token (None) or a non-string token must map to invalid_state,
        # not raise AttributeError up to the dispatcher as a handler_error (500).
        for bad in (None, 12345, b"cev1.x.y", ""):
            with pytest.raises(InvalidStateError) as exc_info:
                verify_state_token(bad, cls=FakeCounter, secrets=[SIGNING_KEY])
            assert exc_info.value.status == 403
            assert "malformed" in exc_info.value.message.lower()


class TestStaleState:
    def test_stale_checks_run_before_the_component_class_check(self, monkeypatch):
        # The spec's State tokens section fixes the order: a stale token
        # answers 409 even when it names another component class, so every
        # server gives the same answer for the same token.
        _pin_now(monkeypatch, FIXED_NOW)
        token = mint_state_token(
            CounterState(count=1), class_id=CLASS_ID, secret=SIGNING_KEY, max_age=timedelta(seconds=60), max_bytes=8192
        )
        prefix, payload_b64, sig_b64 = token.split(".")
        changed = f"{prefix}.{payload_b64}.{'A' if sig_b64[0] != 'A' else 'B'}{sig_b64[1:]}"
        with pytest.raises(StaleStateError):
            verify_state_token(changed, cls=OtherComp, secrets=[SIGNING_KEY])
        _pin_now(monkeypatch, FIXED_NOW + 61)
        with pytest.raises(StaleStateError):
            verify_state_token(token, cls=OtherComp, secrets=[SIGNING_KEY])

    def test_signed_token_expiry(self, monkeypatch):
        _pin_now(monkeypatch, FIXED_NOW)
        token = mint_state_token(
            CounterState(count=1), class_id=CLASS_ID, secret=SIGNING_KEY, max_age=timedelta(seconds=60), max_bytes=8192
        )
        # Before expiry it verifies.
        assert verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY]).state_kwargs["count"] == 1
        # After the clock passes the expiry it is stale (409), not invalid: the
        # signature is still valid, only the deadline passed.
        _pin_now(monkeypatch, FIXED_NOW + 61)
        with pytest.raises(StaleStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 409
        assert exc_info.value.code == "stale_state"
        assert "expired" in exc_info.value.message

    def test_tampered_signature(self):
        # A signature-only tamper keeps the payload well-formed, which is
        # exactly what an honest token signed by a rotated-out secret looks
        # like, so it answers stale (409), not invalid (design 4.3). The
        # corruption flips the FIRST signature character: every bit there is
        # meaningful, so the decoded bytes are guaranteed to change (the last
        # character carries discarded padding bits and a flip there can decode
        # to the same signature).
        token = mint_state_token(
            CounterState(count=1), class_id=CLASS_ID, secret=SIGNING_KEY, max_age=None, max_bytes=8192
        )
        prefix, payload_b64, sig_b64 = token.split(".")
        tampered_sig = ("A" if sig_b64[0] != "A" else "B") + sig_b64[1:]
        tampered = f"{prefix}.{payload_b64}.{tampered_sig}"
        with pytest.raises(StaleStateError) as exc_info:
            verify_state_token(tampered, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 409
        assert exc_info.value.code == "stale_state"
        assert "stale" in exc_info.value.message
        assert "Re-rendering the page" in exc_info.value.message

    def test_rotated_out_secret_is_stale_until_relisted(self):
        token = mint_state_token(
            CounterState(count=4), class_id=CLASS_ID, secret=OLD_KEY, max_age=None, max_bytes=8192
        )
        # The minting secret is gone from the rotation list: the token no
        # longer verifies, but it is a well-formed token, so it is stale (409).
        with pytest.raises(StaleStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[NEW_KEY])
        assert exc_info.value.status == 409
        assert exc_info.value.code == "stale_state"
        # Relisting the old secret makes the very same token verify again.
        verified = verify_state_token(token, cls=FakeCounter, secrets=[NEW_KEY, OLD_KEY])
        assert verified.state_kwargs["count"] == 4

    def test_unverified_well_formed_payload_is_stale(self):
        # The counterpart of the malformed cases in TestInvalidState: the
        # signature matches nothing, but the payload carries the version,
        # component class, and state fields, so the no-match split answers
        # stale (409). The payload only picks the error code; nothing from it
        # is returned.
        payload = tokens._canonical_json({"v": 1, "c": CLASS_ID, "s": {"count": 9}, "t": 0, "x": None})
        token = _forge_signed_token(payload.encode("utf-8"))
        with pytest.raises(StaleStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == 409
        assert exc_info.value.code == "stale_state"


class TestProtocolFixtureConformance:
    """
    Lock the two token-error golden vectors from the protocol package.

    The exchanges under ``packages/protocol/events/v1/tests`` are the wire
    contract (their README: an implementation that disagrees with an exchange is
    wrong). These tests read the expected status and code from the example
    files on disk, never from values copied by hand.
    """

    @staticmethod
    def _load(name):
        return json.loads((TESTS_DIR / name).read_text(encoding="utf-8"))

    def test_invalid_state_fixture_token_answers_403(self):
        call = self._load("error_invalid_state.call.json")
        result = self._load("error_invalid_state.result.json")
        # The example's token is a fixed literal (per the tests README, it
        # is not a volatile path): its payload is valid base64 and JSON but
        # misses the component class and state fields, so under the 4.3 split
        # it stays invalid_state even though the JSON parses.
        token = call["calls"][0]["stateToken"]
        expected = result["results"][0]["error"]
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == expected["status"]
        assert exc_info.value.code == expected["code"]

    def test_stale_state_fixture_arrangement_answers_409(self):
        result = self._load("error_stale_state.result.json")
        expected = result["results"][0]["error"]
        # Per the tests README, stale_state needs harness arrangement: the
        # token must be minted already stale. Arrange the rotated-out variant:
        # mint under a secret the verifier no longer lists.
        token = mint_state_token(
            CounterState(count=0), class_id=CLASS_ID, secret=OLD_KEY, max_age=None, max_bytes=8192
        )
        with pytest.raises(StaleStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[NEW_KEY])
        assert exc_info.value.status == expected["status"]
        assert exc_info.value.code == expected["code"]

    def test_changed_signature_answers_the_stale_state_fixture_error(self):
        result = self._load("error_stale_state.result.json")
        expected = result["results"][0]["error"]
        # The spec's State tokens section says a readable token whose
        # signature no current secret matches answers stale_state, because
        # the server cannot tell a changed signature from a removed secret.
        # Change only the first signature character, which always changes the
        # decoded bytes (the last one can carry ignored padding bits).
        token = mint_state_token(
            CounterState(count=0), class_id=CLASS_ID, secret=SIGNING_KEY, max_age=None, max_bytes=8192
        )
        prefix, payload_b64, sig_b64 = token.split(".")
        changed_sig = ("A" if sig_b64[0] != "A" else "B") + sig_b64[1:]
        with pytest.raises(StaleStateError) as exc_info:
            verify_state_token(f"{prefix}.{payload_b64}.{changed_sig}", cls=FakeCounter, secrets=[SIGNING_KEY])
        assert exc_info.value.status == expected["status"]
        assert exc_info.value.code == expected["code"]


class TestApplyUpdates:
    def test_writes_a_model_field_and_returns_applied(self):
        state = WidgetState(count=0, query="")
        applied = apply_state_updates(state, {"count": 5}, model_fields=("count", "query"))
        assert state.count == 5
        assert applied == ("count",)

    def test_non_model_field_rejected_422(self):
        state = WidgetState()
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"enabled": True}, model_fields=("count", "query"))
        assert exc_info.value.status == 422
        assert exc_info.value.code == "invalid_args"
        assert "enabled" in exc_info.value.fields
        assert "_model" in exc_info.value.fields["enabled"]
        assert state.enabled is False  # untouched

    def test_type_mismatch_rejected_422(self):
        state = WidgetState()
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"count": "not-an-int"}, model_fields=("count",))
        assert exc_info.value.status == 422
        assert "Expected int" in exc_info.value.fields["count"]
        assert state.count == 0

    def test_lone_surrogate_in_text_or_key_rejected_422(self):
        # JSON lets the browser send half of a UTF-16 pair, which the UTF-8
        # token cannot hold, so the whole batch is refused before any write.
        @dataclass
        class NoteState:
            text: str = ""
            tags: dict[str, int] = field(default_factory=dict)
            count: int = 0

        state = NoteState()
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(
                state,
                {"text": "a\udc00", "tags": {"\ud800": 1}, "count": 2},
                model_fields=("text", "tags", "count"),
            )
        assert exc_info.value.status == 422
        assert exc_info.value.fields == {
            "tags": tokens._LONE_SURROGATE_MESSAGE,
            "text": tokens._LONE_SURROGATE_MESSAGE,
        }
        assert (state.text, state.tags, state.count) == ("", {}, 0)
        # A pair of escapes in the request's JSON reads as one ordinary character.
        paired = json.loads('{"text": "\\ud83d\\ude00"}')
        assert apply_state_updates(state, paired, model_fields=("text",)) == ("text",)

    def test_parameterized_container_fields_accept_json_lists(self):
        # JSON has no tuple or set, and on Python 3.10 a parameterized generic
        # such as ``tuple[str, ...]`` counts as a type that isinstance() rejects.
        @dataclass
        class TagState:
            tags: tuple[str, ...] = ()
            labels: set[str] = frozenset()

        state = TagState()
        applied = apply_state_updates(state, {"tags": ["a"], "labels": ["b"]}, model_fields=("tags", "labels"))
        assert applied == ("labels", "tags")

    def test_bool_not_accepted_for_int_field(self):
        state = WidgetState()
        with pytest.raises(StateUpdateError):
            apply_state_updates(state, {"count": True}, model_fields=("count",))

    def test_optional_field(self):
        state = WidgetState()
        apply_state_updates(state, {"note": None}, model_fields=("note",))
        assert state.note is None
        apply_state_updates(state, {"note": "hi"}, model_fields=("note",))
        assert state.note == "hi"
        with pytest.raises(StateUpdateError):
            apply_state_updates(state, {"note": 5}, model_fields=("note",))

    def test_empty_updates_returns_empty_tuple(self):
        state = WidgetState(count=3)
        assert apply_state_updates(state, {}, model_fields=("count",)) == ()
        assert apply_state_updates(state, None, model_fields=("count",)) == ()
        assert state.count == 3

    def test_no_partial_mutation_on_failure(self):
        state = WidgetState(count=0, query="")
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"count": 9, "query": 123}, model_fields=("count", "query"))
        # 'count' would be valid, but the batch fails as a whole, so nothing is
        # written.
        assert state.count == 0
        assert state.query == ""
        assert set(exc_info.value.fields) == {"query"}

    def test_error_field_order_is_deterministic(self):
        state = WidgetState()
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"query": 1, "count": "x", "enabled": 2}, model_fields=("count", "query"))
        assert list(exc_info.value.fields.keys()) == ["count", "enabled", "query"]

    def test_names_outside_model_stop_at_twenty_and_the_message_counts_the_rest(self):
        state = WidgetState()
        # Reverse order shows the listed names come from sorting, not from the wire order.
        updates = {f"u{index:03d}": 1 for index in reversed(range(25))}
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, updates, model_fields=("count", "query"))
        error = exc_info.value
        assert error.status == 422
        assert error.message == (
            "Some state updates were rejected; see the field messages. 5 more field errors are not shown."
        )
        assert list(error.fields) == [f"u{index:03d}" for index in range(20)]
        assert all("_model" in message for message in error.fields.values())

    @pytest.mark.parametrize(
        ("count", "note"),
        [(20, ""), (21, " 1 more field error is not shown.")],
    )
    def test_the_limit_starts_after_twenty_names_outside_model(self, count, note):
        updates = {f"u{index:03d}": 1 for index in range(count)}
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(WidgetState(), updates, model_fields=("count",))
        assert exc_info.value.message == "Some state updates were rejected; see the field messages." + note
        assert len(exc_info.value.fields) == 20

    def test_wrong_typed_model_fields_are_kept_even_when_they_sort_after_the_dropped_names(self):
        state = WidgetState()
        updates = {f"a{index:03d}": 1 for index in range(25)} | {"count": "x", "query": 1}
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, updates, model_fields=("count", "query"))
        fields = exc_info.value.fields
        # `count` and `query` sort after every `a...` name, yet both stay.
        assert list(fields) == [f"a{index:03d}" for index in range(20)] + ["count", "query"]
        assert "Expected int" in fields["count"]
        assert "Expected str" in fields["query"]
        assert exc_info.value.message.endswith(" 5 more field errors are not shown.")
        assert state.count == 0

    def test_many_wrong_typed_model_fields_are_never_limited(self):
        # Every field here is declared in ``_model``, so the browser cannot make the list longer than the State.
        names = [f"f{index:02d}" for index in range(22)]
        wide_state = make_dataclass("WideState", [(name, int, 0) for name in names])
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(wide_state(), dict.fromkeys(names, "x"), model_fields=names)
        assert list(exc_info.value.fields) == names
        assert exc_info.value.message == "Some state updates were rejected; see the field messages."

    def test_one_unresolvable_annotation_keeps_other_fields_checked(self):
        # 'exotic' is a TYPE_CHECKING-only type, so resolving the class's hints at
        # once fails. The per-field fallback must still type-check 'count' rather
        # than making the whole State lenient.
        state = PartlyResolvableState()
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"count": "not-an-int"}, model_fields=("count", "exotic"))
        assert "Expected int" in exc_info.value.fields["count"]
        # The one unresolvable field cannot be type-checked, so any JSON value is
        # accepted and the handler re-authorizes it (7.2).
        lenient = PartlyResolvableState()
        applied = apply_state_updates(lenient, {"exotic": "anything"}, model_fields=("count", "exotic"))
        assert applied == ("exotic",)
        assert lenient.exotic == "anything"

    @pytest.mark.parametrize(
        ("name", "value", "message"),
        [
            ("choice", "c", "Expected one of 'a', 'b', got 'c'."),
            # Python counts True == 1, but JSON keeps `true` and `1` apart.
            ("one", True, "Expected one of 1, got true."),
            ("pair", [1], "Expected a list of 2 items, got 1."),
            ("pair", [1, "a", 2], "Expected a list of 2 items, got 3."),
        ],
    )
    def test_a_bad_literal_or_tuple_length_names_the_field(self, name, value, message):
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(ShapedState(), {name: value}, model_fields=(name,))
        assert exc_info.value.fields == {name: message}

    @pytest.mark.parametrize(
        ("name", "value", "path"),
        [
            ("tags", [1, "x", 3], "tags.1"),
            ("grid", [[1, 2], [3, "x"]], "grid.1.1"),
            ("scores", {"a": 1, "b": "x"}, "scores.b"),
            ("pair", ["a", "a"], "pair.0"),
            ("pair", [1, 2], "pair.1"),
            ("runs", [1, 2, "x"], "runs.2"),
            ("maybe_tags", [1, "x"], "maybe_tags.1"),
        ],
    )
    def test_a_bad_item_is_named_by_its_path_and_nothing_is_written(self, name, value, path):
        state = ShapedState()
        # `choice` is valid, but the batch fails as a whole, so it is not written either.
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {name: value, "choice": "b"}, model_fields=(name, "choice"))
        message = "Expected str, got int." if path == "pair.1" else "Expected int, got str."
        assert exc_info.value.fields == {path: message}
        assert state == ShapedState()

    def test_literal_accepts_a_listed_value(self):
        state = ShapedState()
        applied = apply_state_updates(state, {"choice": "b", "one": 1}, model_fields=("choice", "one"))
        assert applied == ("choice", "one")
        assert (state.choice, state.one) == ("b", 1)

    def test_good_items_are_written(self):
        state = ShapedState()
        updates = {
            "tags": [1, 2],
            "grid": [[1], [2, 3]],
            "scores": {"a": 1},
            "pair": [4, "x"],
            "maybe_tags": [5],
        }
        apply_state_updates(state, updates, model_fields=tuple(updates))
        assert state.tags == [1, 2]
        assert state.grid == [[1], [2, 3]]
        assert state.scores == {"a": 1}
        assert state.pair == [4, "x"]
        assert state.maybe_tags == [5]

    def test_an_optional_list_accepts_null_and_rejects_a_non_list(self):
        state = ShapedState(maybe_tags=[1])
        apply_state_updates(state, {"maybe_tags": None}, model_fields=("maybe_tags",))
        assert state.maybe_tags is None
        # A value that is no list at all is named at the field, not an item.
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"maybe_tags": 5}, model_fields=("maybe_tags",))
        assert exc_info.value.fields == {"maybe_tags": "Expected list[int], got int."}

    @pytest.mark.parametrize("count", [1, 21])
    def test_a_list_stops_at_its_first_bad_item(self, count):
        # The same early stop a Pydantic State has, so a long list of bad
        # items does not make the error response as long as the list.
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(ShapedState(), {"tags": ["x"] * count}, model_fields=("tags",))
        assert list(exc_info.value.fields) == ["tags.0"]
        assert exc_info.value.message == "Some state updates were rejected; see the field messages."

    @pytest.mark.parametrize("count", [1, 21])
    def test_a_dict_stops_at_its_first_bad_value(self, count):
        values = {f"k{index:02d}": "x" for index in range(count)}
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(ShapedState(), {"scores": values}, model_fields=("scores",))
        assert list(exc_info.value.fields) == ["scores.k00"]
        assert exc_info.value.message == "Some state updates were rejected; see the field messages."

    def test_a_scalar_message_is_listed_beside_a_stopped_list(self):
        # The early stop applies to a list's items only, so the wrong-typed
        # `choice` message is kept next to the first bad `tags` item.
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(ShapedState(), {"tags": ["x"] * 25, "choice": "z"}, model_fields=("tags", "choice"))
        fields = exc_info.value.fields
        assert list(fields) == ["choice", "tags.0"]
        assert "more field error" not in exc_info.value.message

    def test_a_typed_dict_field_or_item_accepts_an_object_and_rejects_the_rest(self):
        # isinstance() refuses a TypedDict, so it is checked as a JSON object.
        state = TypedShapeState()
        updates = {"points": [{"x": 1}, {"y": "not checked"}], "origin": {"x": 5}, "point_map": {"a": {"x": 1}}}
        applied = apply_state_updates(state, updates, model_fields=tuple(updates))
        assert applied == ("origin", "point_map", "points")
        assert state.points == [{"x": 1}, {"y": "not checked"}]
        assert state.origin == {"x": 5}
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(
                state,
                {"points": [{"x": 1}, 3], "origin": [1], "point_map": {"a": {"x": 1}, "b": "text"}},
                model_fields=("points", "origin", "point_map"),
            )
        assert exc_info.value.fields == {
            "origin": "Expected Point, got list.",
            "point_map.b": "Expected Point, got str.",
            "points.1": "Expected Point, got int.",
        }
        assert state.origin == {"x": 5}

    def test_a_class_isinstance_cannot_check_is_accepted(self):
        # A Protocol without @runtime_checkable has nothing to check a value
        # against, so the handler authorizes what it does with the value.
        state = TypedShapeState()
        updates = {"readers": [1, "x", None], "reader": {"any": "thing"}}
        applied = apply_state_updates(state, updates, model_fields=tuple(updates))
        assert applied == ("reader", "readers")
        assert state.readers == [1, "x", None]
        assert state.reader == {"any": "thing"}

    @pytest.mark.parametrize("value", [1, 2.5])
    def test_a_float_literal_accepts_the_matching_number(self, value):
        # The browser writes 1.0 as 1, so an int equal to a member matches.
        state = TypedShapeState()
        apply_state_updates(state, {"ratio": value}, model_fields=("ratio",))
        assert state.ratio == value

    @pytest.mark.parametrize("value", [True, 2, "1", 2.0, None])
    def test_a_float_literal_rejects_other_values(self, value):
        # `true` equals 1 in Python but is not a number in JSON, and 2.0 is not a listed member.
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(TypedShapeState(), {"ratio": value}, model_fields=("ratio",))
        assert list(exc_info.value.fields) == ["ratio"]
        assert exc_info.value.fields["ratio"].startswith("Expected one of 1.0, 2.5, got ")

    def test_an_enum_literal_matches_the_members_value(self):
        # The token stores a str or int Enum member as its value, as JSON.
        state = TypedShapeState()
        apply_state_updates(state, {"color": "blue"}, model_fields=("color",))
        assert state.color == "blue"
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"color": "RED"}, model_fields=("color",))
        assert exc_info.value.fields == {"color": "Expected one of 'red', 'blue', got 'RED'."}

    def test_a_typing_extensions_typed_dict_field_accepts_an_object_and_rejects_the_rest(self):
        state = EnumShapeState()
        apply_state_updates(state, {"extension_point": {"x": 5}}, model_fields=("extension_point",))
        assert state.extension_point == {"x": 5}
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"extension_point": 5}, model_fields=("extension_point",))
        assert exc_info.value.fields == {"extension_point": "Expected ExtensionPoint, got int."}

    def test_enum_items_accept_the_members_plain_value(self):
        # A dataclass State stores a str Enum member as "red", so the browser writes that.
        state = EnumShapeState()
        updates = {"colors": ["red", "blue"], "color_map": {"a": "red"}}
        apply_state_updates(state, updates, model_fields=tuple(updates))
        assert state.colors == ["red", "blue"]
        assert state.color_map == {"a": "red"}

    def test_enum_items_reject_a_value_no_member_holds(self):
        updates = {"colors": ["red", "green"], "color_map": {"a": "green", "b": "red"}}
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(EnumShapeState(), updates, model_fields=tuple(updates))
        assert exc_info.value.fields == {
            "color_map.a": "Expected Color, got str.",
            "colors.1": "Expected Color, got str.",
        }

    def test_an_enum_without_a_mix_in_accepts_a_members_plain_value_too(self):
        state = EnumShapeState()
        apply_state_updates(state, {"shade": "dark"}, model_fields=("shade",))
        assert state.shade == "dark"
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"shade": "light"}, model_fields=("shade",))
        assert exc_info.value.fields == {"shade": "Expected Shade, got str."}

    def test_a_bare_typing_tuple_accepts_any_list(self):
        state = EnumShapeState()
        apply_state_updates(state, {"combo": [1, 2]}, model_fields=("combo",))
        assert state.combo == [1, 2]
        # The rejection names the container, not the empty tuple type.
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"combo": 5}, model_fields=("combo",))
        assert exc_info.value.fields == {"combo": "Expected tuple, got int."}

    def test_an_empty_tuple_type_requires_an_empty_list_and_a_bare_tuple_accepts_any_list(self):
        state = TypedShapeState()
        apply_state_updates(state, {"nothing": [], "anything": [1, "a", None]}, model_fields=("nothing", "anything"))
        assert (state.nothing, state.anything) == ([], [1, "a", None])
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"nothing": [1]}, model_fields=("nothing",))
        assert exc_info.value.fields == {"nothing": "Expected a list of 0 items, got 1."}
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(state, {"nothing": 5, "anything": "x"}, model_fields=("nothing", "anything"))
        assert exc_info.value.fields == {
            "anything": "Expected tuple, got str.",
            "nothing": "Expected tuple[()], got int.",
        }

    @pytest.mark.parametrize(
        ("name", "value", "message"),
        [
            ("numbers", "x", "Expected list[int], got str."),
            ("numbers", {"a": 1}, "Expected list[int], got dict."),
            ("either", 5, "Expected list[int] or list[str], got int."),
            ("either", [1, "a"], "Expected list[int] or list[str], got list."),
            ("scores", [1], "Expected dict[str, int], got list."),
            # A class inside a parametrized type is named without its module path.
            ("points", 5, "Expected list[Point], got int."),
            ("point_map", 5, "Expected dict[str, Point], got int."),
        ],
    )
    def test_a_rejection_names_the_whole_declared_type(self, name, value, message):
        with pytest.raises(StateUpdateError) as exc_info:
            apply_state_updates(TypedShapeState(), {name: value}, model_fields=(name,))
        assert exc_info.value.fields == {name: message}

    def test_a_union_of_containers_accepts_either_arm(self):
        state = TypedShapeState()
        apply_state_updates(state, {"either": ["a", "b"]}, model_fields=("either",))
        assert state.either == ["a", "b"]
        apply_state_updates(state, {"either": [1, 2]}, model_fields=("either",))
        assert state.either == [1, 2]

    def test_a_dict_names_its_first_bad_value_in_the_order_sent(self):
        # The dict stops at the first bad value it reads, so which value is
        # named follows the order the browser sent the keys in.
        values = {"a": "x", "10": "x", "9": "x", "2": "x"}
        for ordered, first in ((values, "scores.a"), (dict(reversed(values.items())), "scores.2")):
            with pytest.raises(StateUpdateError) as exc_info:
                apply_state_updates(TypedShapeState(), {"scores": ordered}, model_fields=("scores",))
            assert list(exc_info.value.fields) == [first]

    def test_messages_of_different_fields_are_listed_in_path_order_whatever_the_update_order(self):
        updates = {"scores": {"b": "x", "a": "x"}, "numbers": ["x", 1, "x"], "color": "green"}
        for ordered in (updates, dict(reversed(updates.items()))):
            with pytest.raises(StateUpdateError) as exc_info:
                apply_state_updates(TypedShapeState(), ordered, model_fields=tuple(ordered))
            # Each collection names only its first bad item: `scores.b` is
            # the first one sent, and `numbers.2` is never reached.
            assert list(exc_info.value.fields) == ["color", "numbers.0", "scores.b"]


class TestServerStorage:
    def test_round_trip_mutate_remint(self):
        cache = InMemoryCache()
        first = mint_state_token(
            CounterState(count=1, label="a"),
            class_id=CLASS_ID,
            secret=None,
            max_age=None,
            max_bytes=8192,
            storage="server",
            cache=cache,
        )
        assert first.startswith("ces1.")
        verified = verify_state_token(first, cls=FakeCounter, secrets=[], cache=cache)
        assert verified.state_kwargs == {"count": 1, "label": "a"}

        rebuilt = CounterState(**verified.state_kwargs)
        rebuilt.count = 2
        second = mint_state_token(
            rebuilt,
            class_id=CLASS_ID,
            secret=None,
            max_age=None,
            max_bytes=8192,
            storage="server",
            cache=cache,
        )
        assert second != first
        assert verify_state_token(second, cls=FakeCounter, secrets=[], cache=cache).state_kwargs == {
            "count": 2,
            "label": "a",
        }

    def test_max_age_becomes_cache_ttl(self):
        cache = RecordingCache()
        mint_state_token(
            CounterState(count=1),
            class_id=CLASS_ID,
            secret=None,
            max_age=timedelta(hours=2),
            max_bytes=8192,
            storage="server",
            cache=cache,
        )
        (ttl,) = set(cache.ttls.values())
        assert ttl == 7200.0

    def test_no_max_age_gives_a_24_hour_ttl(self):
        # Each render and State change writes a new entry, so an entry with
        # no lifetime would stay in the cache for good.
        cache = RecordingCache()
        mint_state_token(
            CounterState(count=1),
            class_id=CLASS_ID,
            secret=None,
            max_age=None,
            max_bytes=8192,
            storage="server",
            cache=cache,
        )
        (ttl,) = set(cache.ttls.values())
        assert ttl == 24 * 3600.0

    def test_max_age_expiry_through_the_cache(self, monkeypatch):
        import citry.cache as cache_mod

        clock = {"t": 1000.0}
        monkeypatch.setattr(cache_mod.time, "monotonic", lambda: clock["t"])
        cache = InMemoryCache()
        token = mint_state_token(
            CounterState(count=1),
            class_id=CLASS_ID,
            secret=None,
            max_age=timedelta(seconds=30),
            max_bytes=8192,
            storage="server",
            cache=cache,
        )
        # Fresh: verifies.
        assert verify_state_token(token, cls=FakeCounter, secrets=[], cache=cache).state_kwargs == {
            "count": 1,
            "label": "",
        }
        # Past the ttl the cache evicts, and verify maps the miss to stale.
        clock["t"] = 1031.0
        with pytest.raises(StaleStateError) as exc_info:
            verify_state_token(token, cls=FakeCounter, secrets=[], cache=cache)
        assert exc_info.value.status == 409

    def test_cache_miss_stale_state_message(self):
        with pytest.raises(StaleStateError) as exc_info:
            verify_state_token("ces1.nonexistent-key", cls=FakeCounter, secrets=[], cache=InMemoryCache())
        assert exc_info.value.status == 409
        assert exc_info.value.code == "stale_state"
        message = exc_info.value.message.lower()
        assert "no longer available" in message
        assert "reload" in message

    def test_class_id_mismatch_on_server_token(self):
        cache = InMemoryCache()
        token = mint_state_token(
            CounterState(count=1),
            class_id=CLASS_ID,
            secret=None,
            max_age=None,
            max_bytes=8192,
            storage="server",
            cache=cache,
        )
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(token, cls=OtherComp, secrets=[], cache=cache)
        assert exc_info.value.status == 403

    def test_missing_server_state_is_stale_before_the_class_check(self):
        # The spec's order: State the server no longer holds answers 409
        # before the token's component class is compared.
        token = mint_state_token(
            CounterState(count=1),
            class_id=CLASS_ID,
            secret=None,
            max_age=None,
            max_bytes=8192,
            storage="server",
            cache=InMemoryCache(),
        )
        with pytest.raises(StaleStateError):
            verify_state_token(token, cls=OtherComp, secrets=[], cache=InMemoryCache())

    def test_server_token_without_cache_is_invalid(self):
        cache = InMemoryCache()
        token = mint_state_token(
            CounterState(count=1),
            class_id=CLASS_ID,
            secret=None,
            max_age=None,
            max_bytes=8192,
            storage="server",
            cache=cache,
        )
        # A signed-mode component (no cache passed) that receives a server-style
        # token treats it as invalid rather than crashing.
        with pytest.raises(InvalidStateError):
            verify_state_token(token, cls=FakeCounter, secrets=[])

    def test_server_payload_wrong_version_rejected(self):
        # A server-store entry written under a future protocol version must be
        # rejected as malformed by a worker on this version, mirroring the signed
        # path, so a rolling deploy never reads state under the wrong protocol.
        cache = InMemoryCache()
        key = "some-server-key"
        cache.set(
            f"citry:state:{key}",
            tokens._canonical_json({"v": 2, "c": CLASS_ID, "s": {"count": 1}, "t": 0, "x": None}),
            ttl=None,
        )
        with pytest.raises(InvalidStateError) as exc_info:
            verify_state_token(f"ces1.{key}", cls=FakeCounter, secrets=[], cache=cache)
        assert exc_info.value.status == 403
        assert "malformed" in exc_info.value.message.lower()


class TestResignFlow:
    def test_verify_apply_remint(self, monkeypatch):
        _pin_now(monkeypatch)
        first = mint_state_token(
            CounterState(count=1, label="a"), class_id=CLASS_ID, secret=SIGNING_KEY, max_age=None, max_bytes=8192
        )
        verified = verify_state_token(first, cls=FakeCounter, secrets=[SIGNING_KEY])
        rebuilt = CounterState(**verified.state_kwargs)
        applied = apply_state_updates(rebuilt, {"count": 9}, model_fields=("count", "label"))
        assert applied == ("count",)
        assert rebuilt.count == 9
        second = mint_state_token(rebuilt, class_id=CLASS_ID, secret=SIGNING_KEY, max_age=None, max_bytes=8192)
        assert second != first
        assert verify_state_token(second, cls=FakeCounter, secrets=[SIGNING_KEY]).state_kwargs == {
            "count": 9,
            "label": "a",
        }


class TestPydanticStateExtraKeys:
    def test_extra_keys_in_a_nested_model_are_limited(self):
        pydantic = pytest.importorskip("pydantic")

        class Inner(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(extra="forbid")
            label: str = ""

        class Board(pydantic.BaseModel):
            inner: Inner = Inner()
            count: int = 0

        # One write to a writable field carries many keys the nested model
        # does not declare, plus a wrong-typed declared field.
        updates = {"inner": {f"x{index:02d}": 1 for index in range(25)}, "count": "many"}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), updates, model_fields={"inner", "count"})

        error = caught.value
        extra = [name for name in error.fields if name.startswith("inner.x")]
        assert len(extra) == 20
        # The declared field's message is always listed.
        assert "count" in error.fields
        assert error.message.endswith(" 5 more field errors are not shown.")


class TestPydanticStateItemErrors:
    """
    A write to a Pydantic State lists the first bad item of each list or dict, where a dataclass State lists twenty.

    The count of twenty for a dataclass State is in ``TestApplyUpdates``.
    """

    NO_NOTE = "Some state updates were rejected; see the field messages."

    @pytest.mark.parametrize("count", [1, 20, 21])
    def test_a_bad_list_in_a_write_lists_only_its_first_bad_item(self, count):
        pydantic = pytest.importorskip("pydantic")

        class Board(pydantic.BaseModel):
            tags: list[int] = []

        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), {"tags": ["x"] * count}, model_fields={"tags"})
        assert list(caught.value.fields) == ["tags.0"]
        assert caught.value.message == self.NO_NOTE

    @pytest.mark.parametrize("count", [1, 20, 21])
    def test_a_bad_dict_in_a_write_lists_only_its_first_bad_value(self, count):
        pydantic = pytest.importorskip("pydantic")

        class Board(pydantic.BaseModel):
            scores: dict[str, int] = {}

        values = {f"k{index:02d}": "x" for index in range(count)}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), {"scores": values}, model_fields={"scores"})
        assert list(caught.value.fields) == ["scores.k00"]
        assert caught.value.message == self.NO_NOTE

    @pytest.mark.parametrize(("reverse", "listed"), [(False, "scores.0"), (True, "scores.24")])
    def test_the_dict_value_listed_in_a_write_is_the_first_one_sent(self, reverse, listed):
        pydantic = pytest.importorskip("pydantic")

        class Board(pydantic.BaseModel):
            scores: dict[str, int] = {}

        keys = [str(index) for index in range(25)]
        values = {key: "x" for key in (reversed(keys) if reverse else keys)}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), {"scores": values}, model_fields={"scores"})
        # Pydantic stops at the first bad value it reads, so the one listed
        # follows the order the browser sent the keys in.
        assert list(caught.value.fields) == [listed]
        assert caught.value.message == self.NO_NOTE

    def test_a_wrong_literal_choice_in_a_write_is_rejected(self):
        # The dataclass State rejects a wrong choice too (see TestApplyUpdates),
        # so both kinds of State answer a write outside the listed values.
        pydantic = pytest.importorskip("pydantic")

        class Board(pydantic.BaseModel):
            choice: Literal["a", "b"] = "a"

        board = Board()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(board, {"choice": "c"}, model_fields={"choice"})
        assert caught.value.fields == {"choice": "Input should be 'a' or 'b'"}
        assert board.choice == "a"

        apply_state_updates(board, {"choice": "b"}, model_fields={"choice"})
        assert board.choice == "b"

    def test_bad_list_items_in_a_pydantic_v1_write_stop_at_twenty(self):
        v1 = pytest.importorskip("pydantic.v1")

        class Board(v1.BaseModel):
            tags: list[int] = []
            scores: dict[str, int] = {}

        updates = {"tags": ["x"] * 21, "scores": {f"k{index:02d}": "x" for index in range(21)}}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), updates, model_fields={"tags", "scores"})
        assert len([name for name in caught.value.fields if name.startswith("tags.")]) == 20
        assert len([name for name in caught.value.fields if name.startswith("scores.")]) == 20
        assert caught.value.message.endswith(" 2 more field errors are not shown.")

    def test_a_write_nested_too_deeply_for_a_pydantic_v1_state_is_refused_without_a_traceback(self, caplog):
        v1 = pytest.importorskip("pydantic.v1")

        class Node(v1.BaseModel):
            # A string, because the class does not exist yet inside its own body.
            child: "Node | None" = None  # noqa: UP037
            value: int = 0

        # The annotations are strings (this module defers them), and v1 reads
        # a local class only when it is told where to find it.
        Node.update_forward_refs(Node=Node)

        class Board(v1.BaseModel):
            tree: Node = Node()

        Board.update_forward_refs(Node=Node)

        # The protocol's JSON depth limit allows 200 levels, which is more than Python
        # can follow inside a v1 model's own check.
        deep: dict[str, typing.Any] = {"value": 1}
        for _level in range(198):
            deep = {"child": deep, "value": 1}
        with caplog.at_level(logging.DEBUG, logger="citry"):
            with pytest.raises(StateUpdateError) as caught:
                apply_state_updates(Board(), {"tree": deep}, model_fields={"tree"})

        assert caught.value.fields == {"_state": bounded.TOO_DEEP_MESSAGE}
        # One warning for the class, and never a frame-by-frame traceback.
        assert "Traceback" not in caplog.text
        assert caplog.text.count("levels of Python calls") == 1

    def test_a_pydantic_v1_write_that_makes_too_many_errors_ends_before_it_reaches_every_row(self):
        v1 = pytest.importorskip("pydantic.v1")
        seen: list[int] = []

        class Row(v1.BaseModel):
            a: int = 0
            b: int
            c: int

            # `always` runs this for a missing field, so it counts the rows reached.
            @v1.validator("a", pre=True, always=True, allow_reuse=True)
            def note(cls, value):  # noqa: N805 - Pydantic v1 passes the class
                seen.append(1)
                return value

        class Board(v1.BaseModel):
            rows: list[Row] = []

        # The annotations are strings (this module defers them), and v1 reads
        # a local class only when it is told where to find it.
        Board.update_forward_refs(Row=Row)

        # Each row fails both required fields, so the error limit ends the
        # check before the last row.
        rows = json.loads("[" + ",".join(["[]"] * 100_000) + "]")
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), {"rows": rows}, model_fields={"rows"})

        assert caught.value.fields == {"_state": bounded.TOO_MANY_ERRORS_MESSAGE}
        assert len(seen) < 1_000

    def test_a_valid_pydantic_v1_write_to_a_union_is_not_refused_for_the_errors_of_the_members_before_it(self):
        v1 = pytest.importorskip("pydantic.v1")

        class Board(v1.BaseModel):
            xs: typing.List[typing.Union[int, str]] = []  # noqa: UP006, UP007

        # Each text fails the `int` member first, and the `str` member accepts it.
        applied = apply_state_updates(Board(), {"xs": ["a"] * 5_000}, model_fields={"xs"})

        assert applied == ("xs",)

    def test_a_pydantic_v1_write_that_the_cpu_time_stops_is_logged_as_refused(self, caplog):
        v1 = pytest.importorskip("pydantic.v1")

        class Even(v1.BaseModel):
            child: "Tree | None" = None  # noqa: UP037
            data: list[int] = []
            kind: typing.Literal["even"]

        class Odd(v1.BaseModel):
            child: "Tree | None" = None  # noqa: UP037
            data: list[int] = []
            kind: typing.Literal["odd"]

        Tree = Even | Odd
        Even.update_forward_refs(Tree=Tree)
        Odd.update_forward_refs(Tree=Tree)

        class Board(v1.BaseModel):
            root: Tree | None = None

        Board.update_forward_refs(Tree=Tree)

        # Each level checks the child more than once, so the clock is what
        # ends the check.
        node: dict[str, typing.Any] = {"data": list(range(3_000)), "kind": "odd"}
        for _level in range(14):
            node = {"child": node, "kind": "odd"}
        with caplog.at_level(logging.WARNING, logger="citry"), bounded.request_work() as budget:
            budget._seconds_left = 0.05
            with pytest.raises(StateUpdateError) as caught:
                apply_state_updates(Board(), {"root": node}, model_fields={"root"})

        assert caught.value.fields == {"_state": bounded.TOO_SLOW_MESSAGE}
        # Citry stopped the check, so the log says it refused the write, not
        # that the check finished with the time gone.
        assert caplog.text.count("Board was refused") == 1
        assert "ended before Citry could stop it" not in caplog.text

    def test_a_valid_pydantic_v1_write_checked_by_a_validator_that_catches_errors_is_not_refused(self):
        v1 = pytest.importorskip("pydantic.v1")

        class Tag(v1.BaseModel):
            labels: list[int] = []

        class Board(v1.BaseModel):
            xs: list[int] = []

            @v1.validator("xs", each_item=True)
            def keep(cls, value):  # noqa: N805 - Pydantic v1 passes the class
                # The author's own code builds a v1 error for each item and throws it away.
                with contextlib.suppress(v1.ValidationError):
                    Tag.parse_obj({"labels": ["a"]})
                return value

        applied = apply_state_updates(Board(), {"xs": list(range(1_500))}, model_fields={"xs"})

        assert applied == ("xs",)

    def test_a_pydantic_v1_write_with_a_few_errors_lists_them(self):
        v1 = pytest.importorskip("pydantic.v1")

        class Row(v1.BaseModel):
            a: int
            b: int

        class Board(v1.BaseModel):
            rows: list[Row] = []

        Board.update_forward_refs(Row=Row)

        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), {"rows": [{"a": 1}]}, model_fields={"rows"})

        assert caught.value.fields == {"rows.0.b": "field required"}

    def test_marking_the_lists_of_deep_errors_in_a_write_takes_time_in_step_with_their_depth(self):
        pydantic = pytest.importorskip("pydantic")

        # Every level holds a list of nodes, and the innermost node also has
        # thirty bad scalar fields. Each scalar field has its own error, so
        # thirty errors pass through `depth` lists, and the list of 10,000 bad
        # items beside them adds only its first.
        fields: dict[str, typing.Any] = {f"v{index:02d}": (int, 0) for index in range(30)}
        Node = pydantic.create_model("Node", c=("list[Node]", []), **fields)
        Node.model_rebuild(_types_namespace={"Node": Node})

        class Board(pydantic.BaseModel):
            tree: Node = Node()

        def best_time(depth: int) -> float:
            # The best of three runs keeps one slow run of a busy machine out
            # of the ratio.
            best = float("inf")
            for _run in range(3):
                value: dict[str, typing.Any] = {"c": [1] * 10_000, **{f"v{index:02d}": "x" for index in range(30)}}
                for _level in range(depth - 1):
                    value = {"c": [value]}
                started = perf_counter()
                with pytest.raises(StateUpdateError) as caught:
                    apply_state_updates(Board(), {"tree": value}, model_fields={"tree"})
                best = min(best, perf_counter() - started)
                # The 31 errors are inside the outer lists, which keep twenty.
                assert len(caught.value.fields) == 20
                assert caught.value.message.endswith(" 11 more field errors are not shown.")
            return best

        # Citry reads each error once, so 8 times the depth takes about 5
        # times as long, and the bound leaves room for a slow machine. The
        # deepest value here, 80 lists, is within the nesting Pydantic reads
        # back from a State's JSON.
        assert best_time(80) < 14 * best_time(10)

    def test_an_ordinary_large_write_to_a_strict_state_reaches_pydantic(self):
        pydantic = pytest.importorskip("pydantic")

        # A strict model State is checked as JSON, where the path limit still
        # runs. Thousands of short paths stay under it.
        class Board(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(strict=True)
            scores: dict[str, list[int]] = {}

        assert bounded.state_write_mode(Board) == "json"
        updates = {"scores": {f"key{index}": ["x"] for index in range(30_000)}}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), updates, model_fields={"scores"})
        assert caught.value.fields == {"scores.key0.0": "Input should be a valid integer"}
        assert caught.value.message == self.NO_NOTE

    def test_a_write_with_long_paths_to_a_strict_state_is_refused_before_pydantic_runs(self):
        pydantic = pytest.importorskip("pydantic")

        class Board(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(strict=True)
            scores: dict[str, list[int]] = {}

        assert bounded.state_write_mode(Board) == "json"
        # Small enough that a regression fails on the message, not on memory.
        updates = {"scores": {"a" * 8_000: ["x"] * 4_000}}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(Board(), updates, model_fields={"scores"})
        assert caught.value.fields == {"_state": PATHS_TOO_LONG_MESSAGE}


class TestPydanticDataclassState:
    """A Pydantic dataclass State with `validate_assignment` runs Pydantic on each write."""

    @staticmethod
    def _state_class():
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(validate_assignment=True))
        class Board:
            scores: dict[str, list[typing.Annotated[int, pydantic.Field(gt=0)]]] = pydantic.Field(default_factory=dict)
            title: str = ""

        # This file defers its annotations, and `pydantic` is local here.
        pydantic.dataclasses.rebuild_dataclass(Board, _types_namespace={"pydantic": pydantic, "typing": typing})
        return Board

    def test_a_good_write_is_applied(self):
        state = self._state_class()()
        applied = apply_state_updates(state, {"scores": {"a": [1]}}, model_fields=("scores", "title"))
        assert applied == ("scores",)
        assert state.scores == {"a": [1]}

    def test_a_refused_value_rejects_the_whole_batch_and_changes_nothing(self):
        state = self._state_class()()
        updates = {"scores": {"a": [-1]}, "title": "new"}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, updates, model_fields=("scores", "title"))
        assert list(caught.value.fields) == ["scores.a.0"]
        assert state.title == ""
        assert state.scores == {}

    def test_a_write_with_long_paths_lists_one_bad_item(self):
        state = self._state_class()()
        # Small enough that a regression fails on the message, not on memory.
        updates = {"scores": {"a" * 8_000: [-1] * 4_000}}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, updates, model_fields=("scores",))
        # The copy of the validator stops at the first bad item, so the long
        # key is written into one error and the path limit is not needed.
        assert caught.value.fields == {"scores." + "a" * 8_000 + ".0": "Input should be greater than 0"}
        assert state.scores == {}

    def test_a_write_with_long_paths_is_refused_before_pydantic_runs_when_the_copy_has_no_wrappers(self, monkeypatch):
        pydantic = pytest.importorskip("pydantic")
        build = bounded._build

        def refuse_wrappers(schema, *, wrapped):
            if wrapped:
                msg = "no wrappers"
                raise RuntimeError(msg)
            return build(schema, wrapped=wrapped)

        # Citry then builds the copy without its counting wrappers, and
        # applies the path limit as well. A class that forbids extra keys has
        # no fixed bound on its errors, so its copy is built with wrappers.
        monkeypatch.setattr(bounded, "_build", refuse_wrappers)

        @pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(validate_assignment=True, extra="forbid"))
        class Board:
            scores: dict[str, list[typing.Annotated[int, pydantic.Field(gt=0)]]] = pydantic.Field(default_factory=dict)

        pydantic.dataclasses.rebuild_dataclass(Board, _types_namespace={"pydantic": pydantic, "typing": typing})
        state = Board()
        updates = {"scores": {"a" * 8_000: [-1] * 4_000}}
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, updates, model_fields=("scores",))
        assert caught.value.fields == {"_state": PATHS_TOO_LONG_MESSAGE}
        assert state.scores == {}

    def test_a_strict_state_takes_a_good_write_and_restores(self):
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(strict=True, validate_assignment=True))
        class Board:
            count: int = 0

        state = Board()
        assert apply_state_updates(state, {"count": 5}, model_fields=("count",)) == ("count",)
        assert state.count == 5
        assert restore_state(Board, {"count": 5}) == Board(count=5)

    def test_a_write_without_validate_assignment_is_checked_and_kept_as_sent(self):
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass
        class Board:
            scores: list[typing.Annotated[int, pydantic.Field(gt=0)]] = pydantic.Field(default_factory=list)
            pair: tuple[int, ...] = ()

        pydantic.dataclasses.rebuild_dataclass(Board, _types_namespace={"pydantic": pydantic, "typing": typing})
        state = Board()
        # A value the class refuses is refused when it arrives, so it never
        # reaches the signed token.
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"scores": [1, -1]}, model_fields=("scores", "pair"))
        assert list(caught.value.fields) == ["scores.1"]
        assert state.scores == []
        # A good value is kept as the browser sent it, as the class keeps an
        # assignment without `validate_assignment`; the next restore converts it.
        apply_state_updates(state, {"pair": [1, 2]}, model_fields=("scores", "pair"))
        assert state.pair == [1, 2]

    def test_a_deep_tree_the_server_built_restores(self):
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass
        class Cond:
            type: Literal["cond"]

        @pydantic.dataclasses.dataclass
        class Or:
            type: Literal["or"]
            items: list[And | Or | Cond]

        @pydantic.dataclasses.dataclass
        class And:
            type: Literal["and"]
            items: list[And | Or | Cond]

        namespace = {"And": And, "Or": Or, "Cond": Cond, "Literal": Literal}
        pydantic.dataclasses.rebuild_dataclass(Or, _types_namespace=namespace)
        pydantic.dataclasses.rebuild_dataclass(And, _types_namespace=namespace)

        @pydantic.dataclasses.dataclass
        class Board:
            tree: And | Or | Cond | None = None

        pydantic.dataclasses.rebuild_dataclass(Board, _types_namespace=namespace)
        tree: dict[str, object] = {"type": "cond"}
        for _ in range(16):
            tree = {"type": "and", "items": [tree]}
        # Citry's copy of the validator, which checks browser writes, stops
        # at this depth.
        with bounded.request_work(), pytest.raises(bounded.ValidationTooCostly):
            bounded.validate_init(bounded.checker_for(Board, state=True), Board, {"tree": tree})
        # The token is signed, and the browser's writes were checked when they
        # arrived, so the same tree, built by the app, restores.
        restored = restore_state(Board, {"tree": tree})
        assert type(restored.tree).__name__ == "And"

    def test_a_batch_without_validate_assignment_is_checked_as_the_restore_will_build_it(self):
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass
        class Board:
            low: int = 0
            high: int = 0

            @pydantic.model_validator(mode="after")
            def ordered(self):
                if self.low > self.high:
                    msg = "low must not exceed high"
                    raise ValueError(msg)
                return self

            def __post_init__(self):
                if self.high > 100:
                    msg = "high must be at most 100"
                    raise ValueError(msg)

        # The validator sees the whole batch, not one write on the old State.
        state = Board()
        apply_state_updates(state, {"low": 5, "high": 9}, model_fields=("low", "high"))
        assert (state.low, state.high) == (5, 9)
        # `__post_init__` runs at the restore, so it runs on the write too.
        with pytest.raises(StateUpdateError):
            apply_state_updates(state, {"high": 101}, model_fields=("low", "high"))
        assert state.high == 9

    @pytest.mark.parametrize("slots", [False, True])
    def test_a_field_validator_that_reads_another_field_checks_a_write_without_validate_assignment(self, slots):
        pydantic = pytest.importorskip("pydantic")

        # Pydantic's password-confirm pattern: the second field's validator
        # reads the first through `info.data`. A class with slots has no
        # `__dict__` to read the other fields from.
        @pydantic.dataclasses.dataclass(slots=slots)
        class Board:
            password: str = "pw"  # noqa: S105 - a test value
            confirm: str = "pw"

            @pydantic.field_validator("confirm")
            @classmethod
            def matches(cls, value, info):
                if value != info.data["password"]:
                    msg = "passwords differ"
                    raise ValueError(msg)
                return value

        writable = ("password", "confirm")
        state = Board()
        apply_state_updates(state, {"confirm": "pw"}, model_fields=writable)
        # The validator of the later field sees the earlier field's write
        # from the same batch, because Citry assigns in declaration order,
        # whatever order the names sort in.
        apply_state_updates(state, {"confirm": "x", "password": "x"}, model_fields=writable)
        assert (state.password, state.confirm) == ("x", "x")
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"confirm": "zz"}, model_fields=writable)
        assert caught.value.fields == {"confirm": "Value error, passwords differ"}
        assert state.confirm == "x"

    def test_a_field_validator_that_reads_its_field_name_checks_a_write_without_validate_assignment(self):
        pydantic = pytest.importorskip("pydantic")
        longest = {"first": 5, "last": 8}

        # One validator shared by several fields looks up its own field.
        @pydantic.dataclasses.dataclass
        class Board:
            first: str = ""
            last: str = ""

            @pydantic.field_validator("first", "last")
            @classmethod
            def short(cls, value, info):
                if len(value) > longest[info.field_name]:
                    msg = f"{info.field_name} is too long"
                    raise ValueError(msg)
                return value

        writable = ("first", "last")
        state = Board()
        apply_state_updates(state, {"first": "Ada", "last": "Lovelace"}, model_fields=writable)
        assert (state.first, state.last) == ("Ada", "Lovelace")
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"last": "Lovelace!"}, model_fields=writable)
        assert caught.value.fields == {"last": "Value error, last is too long"}

    def test_a_field_validator_sees_only_the_fields_declared_before_its_own(self):
        pydantic = pytest.importorskip("pydantic")
        seen: dict[str, list[str]] = {}

        @pydantic.dataclasses.dataclass
        class Board:
            first: str = ""
            second: str = "block"
            third: str = ""

            @pydantic.field_validator("first", "second", "third")
            @classmethod
            def check(cls, value, info):
                seen[info.field_name] = sorted(info.data)
                # The class never shows `first` a later field, so this
                # never fires when the class is built.
                if info.field_name == "first" and info.data.get("second") == "block":
                    msg = "second blocks first"
                    raise ValueError(msg)
                return value

        writable = ("first", "second", "third")
        state = Board()
        # The class takes these, so the write check takes them too.
        apply_state_updates(state, {"first": "y"}, model_fields=writable)
        apply_state_updates(state, {"first": "z", "second": "ok", "third": "t"}, model_fields=writable)
        assert (state.first, state.second, state.third) == ("z", "ok", "t")
        assert seen == {"first": [], "second": ["first"], "third": ["first", "second"]}

    def test_a_write_to_a_frozen_field_is_kept_as_the_class_keeps_it(self):
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass
        class Board:
            title: str = pydantic.Field(default="", frozen=True)

        state = Board()
        # Without `validate_assignment` the class takes the assignment, so
        # a field listed in `_model` takes the browser's write.
        Board().title = "direct"
        assert apply_state_updates(state, {"title": "new"}, model_fields=("title",)) == ("title",)
        assert state.title == "new"

    @pytest.mark.parametrize("note", ["ok", "bad"])
    def test_a_validator_that_changes_info_data_leaves_the_state_as_it_was(self, note):
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass
        class Board:
            items: list[int] = field(default_factory=lambda: [1])
            note: str = ""

            @pydantic.field_validator("note")
            @classmethod
            def check(cls, value, info):
                info.data["items"].append(0)
                if value == "bad":
                    msg = "bad note"
                    raise ValueError(msg)
                return value

        state = Board()
        writable = ("items", "note")
        if note == "bad":
            with pytest.raises(StateUpdateError):
                apply_state_updates(state, {"note": note}, model_fields=writable)
        else:
            apply_state_updates(state, {"note": note}, model_fields=writable)
        # The validator changed its copy of the fields, not the State.
        assert state.items == [1]

    @pytest.mark.parametrize("validated", [False, True])
    def test_the_whole_state_is_built_again_only_when_the_class_checks_across_fields(self, validated, monkeypatch):
        pydantic = pytest.importorskip("pydantic")
        namespace: dict[str, typing.Any] = {"__annotations__": {"low": "int", "high": "int"}, "low": 0, "high": 0}
        if validated:
            namespace["ordered"] = pydantic.model_validator(mode="after")(lambda self: self)
        board = pydantic.dataclasses.dataclass(type("Board", (), namespace))
        builds = []
        real = tokens.restore_state

        def counted(state_cls, values):
            builds.append(values)
            return real(state_cls, values)

        monkeypatch.setattr(tokens, "restore_state", counted)
        apply_state_updates(board(), {"low": 1}, model_fields=("low", "high"))
        # Each field is checked on its own when the class is built, so the
        # field check already ran the check the next restore runs.
        assert len(builds) == (1 if validated else 0)

    @pytest.mark.parametrize("kind", ["model", "dataclass"])
    def test_the_calls_of_one_request_share_the_restore_of_the_same_values(self, kind):
        pydantic = pytest.importorskip("pydantic")
        runs: list[object] = []

        def counted(value):
            runs.append(value)
            return value

        annotations = {"items": typing.Annotated[list[int], pydantic.AfterValidator(counted)]}
        if kind == "model":
            board = type("Board", (pydantic.BaseModel,), {"__annotations__": annotations, "items": []})
        else:
            board = pydantic.dataclasses.dataclass(
                type("Board", (), {"__annotations__": annotations, "items": field(default_factory=list)})
            )
        values = {"items": [1, 2]}

        with bounded.request_work():
            restored = [restore_state(board, values) for _ in range(4)]
            restored[0].items.append(3)
        # The second restore keeps a copy of its result, and the later ones
        # hand out copies of it, so a call that changes its State changes
        # only its own.
        assert len(runs) == 2
        assert [state.items for state in restored] == [[1, 2, 3], [1, 2], [1, 2], [1, 2]]
        assert len({id(state.items) for state in restored}) == 4
        # Outside a request every restore checks the values again.
        restore_state(board, values)
        restore_state(board, values)
        assert len(runs) == 4

    def test_values_that_every_call_restores_stay_shared_among_other_restores(self):
        pydantic = pytest.importorskip("pydantic")
        runs: list[int] = []

        def counted(value):
            runs.append(value)
            return value

        annotations = {"count": typing.Annotated[int, pydantic.AfterValidator(counted)]}
        board = type("Board", (pydantic.BaseModel,), {"__annotations__": annotations, "count": 0})

        with bounded.request_work():
            for call in range(1, 17):
                # Each call carries the same token.
                state = restore_state(board, {"count": 0})
                # Its handler changes State to new values, which Citry
                # restores twice to check that they can be signed.
                state.count = call
                assert check_changed_state(state) is None
                # Other components of the request restore States of their own.
                for other in range(3):
                    restore_state(board, {"count": 1000 * (other + 1) + call})
        # The token's values are read on every call, so the store keeps them
        # while it drops the values each call restored only for itself.
        assert runs.count(0) == 2
        assert runs.count(16) == 2

    def test_a_default_factory_that_reads_other_fields_runs_on_the_write(self):
        pydantic = pytest.importorskip("pydantic")
        namespace: dict[str, typing.Any] = {
            "__annotations__": {"a": "int", "b": "int"},
            "a": 1,
            "b": pydantic.Field(default_factory=lambda data: 10 // data["a"], init=False),
        }
        board = pydantic.dataclasses.dataclass(type("Board", (), namespace))
        state = board()

        # The factory reads the written field, so the whole State is built
        # with the write in it, and the write fails at once, not on the next
        # call's restore.
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"a": 0}, model_fields=("a",))
        assert caught.value.fields == {"_state": "The State could not be checked."}
        assert state.a == 1
        apply_state_updates(state, {"a": 5}, model_fields=("a",))
        assert state.a == 5

    @pytest.mark.parametrize("checks_assignment", [False, True])
    @pytest.mark.parametrize("where", ["model_validator", "post_init"])
    def test_a_validator_that_raises_another_exception_refuses_the_write(self, where, checks_assignment, caplog):
        pydantic = pytest.importorskip("pydantic")
        if where == "post_init" and checks_assignment:
            pytest.skip("Pydantic does not run __post_init__ on an assignment")

        def fail(value):
            if value == "boom":
                msg = "author bug"
                raise TypeError(msg)

        namespace: dict[str, typing.Any] = {"__annotations__": {"note": "str"}, "note": "ok"}
        if where == "model_validator":
            namespace["check"] = pydantic.model_validator(mode="after")(lambda self: fail(self.note) or self)
        else:
            namespace["__post_init__"] = lambda self: fail(self.note)
        config = pydantic.ConfigDict(validate_assignment=checks_assignment)
        board = pydantic.dataclasses.dataclass(config=config)(type("Board", (), namespace))
        state = board()

        # The author's bug answers like a refused write, not a server error.
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"note": "boom"}, model_fields=("note",))
        assert caught.value.fields == {"_state": "The State could not be checked."}
        assert state.note == "ok"
        assert "A State validator raised while checking browser writes to Board." in caplog.text

    @pytest.mark.parametrize("kind", ["model", "dataclass"])
    def test_a_restore_stops_each_list_at_its_first_bad_item(self, kind):
        pydantic = pytest.importorskip("pydantic")
        zones = typing.Literal[tuple(f"zone-{i:03}" for i in range(600))]  # type: ignore[misc]
        annotations = {"tags": list[zones] | list[str]}
        if kind == "model":
            board = type("Board", (pydantic.BaseModel,), {"__annotations__": annotations, "tags": []})
        else:
            board = pydantic.dataclasses.dataclass(
                type("Board", (), {"__annotations__": annotations, "tags": field(default_factory=list)})
            )

        # A valid value restores as the class gives it.
        assert restore_state(board, {"tags": ["a"] * 5_000}).tags == ["a"] * 5_000
        # Citry's copy stops each member at its first bad item.
        with pytest.raises(pydantic.ValidationError) as raised:
            restore_state(board, {"tags": [1] * 5_000})
        assert raised.value.error_count() == 2

    def test_a_batch_check_reads_the_values_the_restore_reads(self):
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass
        class Board:
            pair: tuple[int, ...] = ()
            note: str = ""

            @pydantic.field_validator("pair", mode="before")
            @classmethod
            def copied(cls, value):
                # Takes the JSON form only (a list), as the restore hands it over.
                return value.copy()

        pydantic.dataclasses.rebuild_dataclass(Board, _types_namespace={"pydantic": pydantic})
        state = restore_state(Board, {"pair": [1, 2], "note": ""})
        assert state.pair == (1, 2)
        apply_state_updates(state, {"note": "hi"}, model_fields=("note",))
        assert state.note == "hi"

    def test_a_write_to_a_field_without_init_is_checked(self):
        pydantic = pytest.importorskip("pydantic")

        @pydantic.dataclasses.dataclass
        class Board:
            count: typing.Annotated[int, pydantic.Field(gt=0)] = field(default=1, init=False)

        pydantic.dataclasses.rebuild_dataclass(Board, _types_namespace={"pydantic": pydantic, "typing": typing})
        state = Board()
        with pytest.raises(StateUpdateError) as caught:
            apply_state_updates(state, {"count": -5}, model_fields=("count",))
        assert list(caught.value.fields) == ["count"]
        assert state.count == 1

    def test_a_large_value_the_app_built_does_not_spend_the_writes_budget(self):
        pydantic = pytest.importorskip("pydantic")
        nested = typing_extensions.TypeAliasType("nested", "list[nested] | tuple[nested, ...] | int")

        @pydantic.dataclasses.dataclass
        class Board:
            tree: nested = 0  # type: ignore[valid-type]
            note: str = ""

        pydantic.dataclasses.rebuild_dataclass(Board, _types_namespace={"nested": nested})
        tree: typing.Any = 1
        for _ in range(30):
            tree = [tree, [1, 2]]
        state = restore_state(Board, {"tree": tree, "note": ""})
        with bounded.request_work() as budget:
            # Only the browser's own value spends from the request's budget.
            budget.left = 1_000
            apply_state_updates(state, {"note": "hi"}, model_fields=("note",))
        assert state.note == "hi"
