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

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from citry.cache import InMemoryCache
from citry.ext.events import tokens
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
GOLDEN_NO_EXPIRY = "cev1.eyJjIjoiQ291bnRlcl9hYjEyY2QiLCJzIjp7ImNvdW50IjozLCJsYWJlbCI6ImhpIn0sInQiOjE3MDAwMDAwMDAsInYiOjEsIngiOm51bGx9.v8DpZJ62veLSs3oHRgNwWWKlXnY1xdpLzCIFrE_tVAk"  # noqa: E501
GOLDEN_WITH_EXPIRY = "cev1.eyJjIjoiQ291bnRlcl9hYjEyY2QiLCJzIjp7ImNvdW50IjozLCJsYWJlbCI6ImhpIn0sInQiOjE3MDAwMDAwMDAsInYiOjEsIngiOjE3MDAwMDM2MDB9.HOmVEm0AuLGjvAurlzdhVh9Q8ZD-2WLFXInzjHXk9EM"  # noqa: E501


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
        signature = hmac.new(SIGNING_KEY.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
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

    def test_no_max_age_no_ttl(self):
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
        assert ttl is None

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
            key,
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
