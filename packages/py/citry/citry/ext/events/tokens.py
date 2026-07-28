"""
State tokens for the ``events`` extension: mint, verify, apply updates.

A component's ``State`` (section 3.2) is the only thing that round-trips
between the browser and the event handlers. At render time the extension
turns the State into a token delivered with the HTML; on each call the client
echoes the token back, the server rebuilds the State from it, applies any
pending two-way binding writes, and runs the handler. This module owns those
three steps and nothing else (no HTTP, no dispatch): the pure functions
``mint_state_token``, ``verify_state_token``, and ``apply_state_updates``.

There are two ways the round-trip State can be stored, chosen per component by
the ``_storage`` State meta, and the token stays opaque to the client either
way (it only stores and echoes the string):

- ``"signed"`` (the default): the State travels inside the token itself. The
  token is ``cev1.<base64url(payload)>.<base64url(hmac_sha256)>``, where the
  payload is the canonical JSON
  ``{"v": 1, "c": class_id, "s": {state}, "t": mint_epoch, "x": expiry|null}``.
  The HMAC binds the payload to the class id and the protocol version, so a
  token cannot be tampered with or moved to another component. Nothing lives
  on the server between calls.
- ``"server"``: the State lives in ``Citry.cache`` under a random, unguessable
  key, and the token is just ``ces1.<key>`` (a distinct prefix from the signed
  form so verification can tell them apart). This is the opt-in mode for State
  too large to ship on every call, State that must not be readable in the page
  source, and step one of the livecomponents migration (design section 10).
  It needs a shared cache backend across workers, the same constraint the
  fragments feature already documents: one worker mints the key, another may
  serve the next call and must find the entry. Expiry rides the cache's own
  time-to-live, set from ``_max_age`` at mint.

The per-call order the dispatcher (a later work package) drives is: verify the
token, rebuild ``cls.State(**verified.state_kwargs)``, apply ``stateUpdates`` to
the writable (``_model``) fields, run the handler, then mint a fresh token from
the possibly-mutated State for the response. This module provides the first,
third, and last of those steps. Design: ``docs/design/events.md`` sections 7.1
and 7.2.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import math
import secrets as secrets_module
import sys
import time
from dataclasses import dataclass, fields
from types import UnionType
from typing import TYPE_CHECKING, Any, Union, cast, get_args, get_origin, get_type_hints
from weakref import WeakKeyDictionary

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from datetime import timedelta

    from citry.cache import CitryCache

__all__ = [
    "InvalidStateError",
    "SigningSecretError",
    "StaleStateError",
    "StateTokenError",
    "StateUpdateError",
    "VerifiedState",
    "apply_state_updates",
    "mint_state_token",
    "verify_state_token",
]

# The two token prefixes. The signed prefix is the design-pinned wire format
# (7.1); the server prefix is this binding's own choice, distinct so that
# verification dispatches on it without ever having to guess the storage mode.
_SIGNED_PREFIX = "cev1"
_SERVER_PREFIX = "ces1"

_PROTOCOL_VERSION = 1

# Resolved field types per State class, so a hot dispatch path does not re-run
# ``get_type_hints`` on every call. Weak keys let a retired State class be
# collected.
_HINT_CACHE: WeakKeyDictionary[type, dict[str, Any]] = WeakKeyDictionary()

_MALFORMED_MSG = (
    "The state token is malformed and could not be read. It may have been truncated or"
    " altered in transit; reload the page to get a fresh token."
)
_NO_SIGNING_KEY_MSG = (
    "No signing secret is configured, but this component's State must be signed into a"
    " token. Set one on your Citry instance, e.g. Citry(secret='<a long random string>')."
    " Django projects can reuse their existing key with"
    " Citry(secret=citry.contrib.django.secret())."
)


def _now() -> float:
    """The current wall-clock epoch, in seconds. Indirected so tests can pin it."""
    return time.time()


@dataclass(frozen=True, slots=True)
class VerifiedState:
    """
    The trustworthy result of verifying a state token.

    Attributes:
        state_kwargs: The State fields as a plain dict, ready to rebuild the
            typed State with ``cls.State(**state_kwargs)``.
        class_id: The class id the token was minted for; already checked to
            match the component the call is dispatching to.

    """

    state_kwargs: dict[str, Any]
    class_id: str


@dataclass(frozen=True, slots=True)
class PreparedStateToken:
    """Pure token result plus an optional exact server-cache write."""

    token: str
    cache_key: str | None = None
    cache_value: str | None = None
    ttl: float | None = None


class StateTokenError(Exception):
    """
    Base for state-token failures the dispatcher maps onto wire error codes.

    Attributes:
        code: The protocol error code (``"invalid_state"``, ``"stale_state"``,
            or ``"invalid_args"``).
        status: The HTTP status that code maps to.
        message: The human-readable summary.

    """

    code: str = "invalid_state"
    status: int = 403

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidStateError(StateTokenError):
    """
    The token is malformed, or was minted for another component (403).

    Malformed means the payload cannot be read as a well-formed token: bad
    base64, bad JSON, a wrong protocol version, or missing fields. A token that
    is well-formed but fails signature verification answers
    [`StaleStateError`][citry.ext.events.tokens.StaleStateError] instead; the
    split is the error-codes rule in design section 4.3.
    """

    code = "invalid_state"
    status = 403


class StaleStateError(StateTokenError):
    """
    The token is stale: expired, rotated out, or its server-side entry is gone (409).

    A well-formed token whose signature matches no configured secret answers
    this code (the error-codes rule in design section 4.3): a token signed by a
    rotated-out secret looks exactly like that, and a signature-only tamper is
    indistinguishable from it. Re-rendering the page refreshes the token.
    """

    code = "stale_state"
    status = 409


class StateUpdateError(StateTokenError):
    """
    One or more two-way binding updates failed the writable-field gate or a type check (422).

    Attributes:
        fields: Per-field messages keyed by the offending State field name, the
            same ``fields`` shape schema validation and ``EventError`` use, so
            the client can show them next to the inputs.

    """

    code = "invalid_args"
    status = 422

    def __init__(self, message: str, fields: dict[str, str]) -> None:
        super().__init__(message)
        self.fields = fields


class SigningSecretError(Exception):
    """
    A signed token was requested but no usable signing secret is configured.

    Raised the first time a signed-storage component is minted without a
    ``CitrySettings.secret``. It is a deployment-configuration error (the fix is
    one line, named in the message), not a per-call client failure, so it stays
    outside the [`StateTokenError`][citry.ext.events.tokens.StateTokenError]
    hierarchy the dispatcher maps to wire codes.
    """


# ----- Minting -----


def mint_state_token(
    state: Any,
    *,
    class_id: str,
    secret: str | list[str] | None,
    max_age: timedelta | None,
    max_bytes: int,
    storage: str = "signed",
    cache: CitryCache | None = None,
) -> str:
    """
    Turn a State instance into the opaque token delivered with the HTML.

    The same call also runs at the end of a dispatch to re-mint the token from
    the possibly-mutated State, so the client's stored token always reflects the
    latest server state.

    Args:
        state: The State instance to serialize. Must be a dataclass instance
            (the extension converts every ``State`` class to one); a stateless
            component carries no token and must not reach here.
        class_id: The component's stable class id, bound into the token so it
            can only be replayed against the same component.
        secret: The signing secret, a single string or a rotation list whose
            first entry signs. Ignored in server storage. ``None`` (no secret
            configured) raises
            [`SigningSecretError`][citry.ext.events.tokens.SigningSecretError]
            for signed storage.
        max_age: Optional token lifetime; ``None`` never expires. In signed
            storage it becomes the payload's expiry field; in server storage it
            becomes the cache entry's time-to-live.
        max_bytes: The mint-time size canary for signed storage: State whose
            serialized form exceeds it raises, with guidance to keep an id and
            reload the rest. Not applied in server storage, whose whole purpose
            is State too large to round-trip.
        storage: ``"signed"`` (default) or ``"server"``.
        cache: The cache backend for server storage; required when
            ``storage="server"``.

    Returns:
        The token string: ``cev1.<payload>.<sig>`` for signed storage, or
        ``ces1.<key>`` for server storage.

    Raises:
        ValueError: When ``state`` is not a State instance, a State field is not
            JSON-serializable, holds a dict with non-string keys (naming the
            field), or contains a circular reference, the signed serialized
            State is over ``max_bytes``, ``storage`` is unknown, or server
            storage was asked for without a cache.
        SigningSecretError: When signed storage is minted without a secret.

    """
    if state is None:
        msg = "mint_state_token requires a State instance; a stateless component carries no token."
        raise ValueError(msg)
    if storage not in ("signed", "server"):
        msg = f"Unknown storage mode {storage!r}; expected 'signed' or 'server'."
        raise ValueError(msg)

    state_dict = _state_dict(state, class_id)
    prepared = _prepare_state_token_values(
        state_dict,
        class_id=class_id,
        secret=secret,
        max_age=max_age,
        max_bytes=max_bytes,
        storage=storage,
    )
    _commit_prepared_state_token(prepared, cache)
    return prepared.token


def _prepare_state_token_values(
    state_dict: dict[str, Any],
    *,
    class_id: str,
    secret: str | list[str] | None,
    max_age: timedelta | None,
    max_bytes: int,
    storage: str,
) -> PreparedStateToken:
    """Validate plain State values and prepare a token without cache mutation."""
    if storage not in ("signed", "server"):
        msg = f"Unknown storage mode {storage!r}; expected 'signed' or 'server'."
        raise ValueError(msg)
    _validate_state_values(state_dict, class_id)
    payload = _build_payload(class_id, state_dict, max_age)
    if storage == "server":
        key = secrets_module.token_urlsafe(32)
        ttl = max_age.total_seconds() if max_age is not None else None
        return PreparedStateToken(
            token=f"{_SERVER_PREFIX}.{key}",
            cache_key=key,
            cache_value=_canonical_json(payload),
            ttl=ttl,
        )
    _enforce_max_bytes(class_id, state_dict, max_bytes)
    signing_secret = _normalize_secrets(secret)[0]
    return PreparedStateToken(token=_sign(payload, signing_secret))


def _commit_prepared_state_token(prepared: PreparedStateToken, cache: CitryCache | None) -> None:
    """Commit one prepared server token, if any."""
    if prepared.cache_key is None:
        return
    if cache is None:
        msg = (
            "State._storage='server' needs a cache backend, but none was provided to"
            " mint_state_token. Pass cache=citry.cache (use a shared backend across workers)."
        )
        raise ValueError(msg)
    cache.set(prepared.cache_key, cast("str", prepared.cache_value), ttl=prepared.ttl)


def _validate_state_values(state_dict: dict[str, Any], class_id: str) -> None:
    """Apply the strict State JSON contract to an exact plain field mapping."""
    if type(state_dict) is not dict or any(type(name) is not str for name in state_dict):
        raise ValueError(f"Component {class_id}: State values must be an exact dict with string keys.")
    for field_name, value in state_dict.items():
        _reject_non_string_dict_keys(value, class_id, field_name)
        try:
            _canonical_json(value)
        except (TypeError, ValueError) as err:
            raise ValueError(f"Component {class_id}: State field {field_name!r} is not strict JSON.") from err


def _state_dict(state: Any, class_id: str) -> dict[str, Any]:
    """The State fields as a plain dict, rejecting any field that is not JSON-safe."""
    result: dict[str, Any] = {}
    for state_field in fields(state):
        value = getattr(state, state_field.name)
        # JSON object keys are always strings, so a non-string dict key (at any
        # depth) is silently rewritten to a string on the round-trip (1 comes back
        # as "1") instead of round-tripping. json.dumps does that coercion without
        # complaint, so catch it here, named to the field, before it corrupts the
        # state or the mixed-key case fails unattributed while the payload is signed.
        _reject_non_string_dict_keys(value, class_id, state_field.name)
        try:
            # Probe with the same serializer the payload uses, so a value that
            # cannot be serialized to JSON at all (for example a custom object) is
            # named here rather than raised unattributed later during signing.
            _canonical_json(value)
        except (TypeError, ValueError) as err:
            if isinstance(err, ValueError) and "Circular reference" in str(err):
                raise
            msg = (
                f"Component {class_id}: State field {state_field.name!r} holds a value"
                f" ({_state_value_description(value)}) which is not JSON-serializable under strict rules."
                f" State round-trips as JSON"
                f" on every event call: store ids and plain values (str, int, float, bool, None,"
                f" lists, and dicts with string keys) and rebuild richer objects in the handler."
            )
            raise ValueError(msg) from err
        result[state_field.name] = value
    return result


def _reject_non_string_dict_keys(value: Any, class_id: str, field_name: str, seen: set[int] | None = None) -> None:
    """
    Reject a dict at any depth whose keys are not all strings, naming the field.

    ``seen`` holds the ids of the containers already visited on this walk, so a
    self-referential container cannot recurse forever here. The circular value
    itself is still rejected: the canonical-JSON probe that runs right after
    this check raises json's circular-reference ValueError for it, the same
    error a circular value gets on every other serialization path.
    """
    if not isinstance(value, (dict, list, tuple)):
        return
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                msg = (
                    f"Component {class_id}: State field {field_name!r} holds a dict with a non-string"
                    f" key ({key!r}, of type {type(key).__name__}). State round-trips as JSON on every event"
                    f" call, and JSON object keys are always strings, so a non-string key is rewritten"
                    f" to a string and does not round-trip. Use string keys (store a list of entries if"
                    f" the keys are not strings) and rebuild richer objects in the handler."
                )
                # A non-JSON-safe State field is the mint contract's ValueError (the
                # sibling unserializable-value path raises ValueError too), even
                # though this particular guard happens to test the key's type.
                raise ValueError(msg)  # noqa: TRY004
        for sub_value in value.values():
            _reject_non_string_dict_keys(sub_value, class_id, field_name, seen)
    else:
        for item in value:
            _reject_non_string_dict_keys(item, class_id, field_name, seen)


def _build_payload(class_id: str, state_dict: dict[str, Any], max_age: timedelta | None) -> dict[str, Any]:
    """The canonical payload dict shared by both storage modes."""
    minted_at = int(_now())
    expiry = minted_at + int(max_age.total_seconds()) if max_age is not None else None
    return {"v": _PROTOCOL_VERSION, "c": class_id, "s": state_dict, "t": minted_at, "x": expiry}


def _enforce_max_bytes(class_id: str, state_dict: dict[str, Any], max_bytes: int) -> None:
    """Reject signed State whose serialized size trips the design-smell canary."""
    size = len(_canonical_json(state_dict).encode("utf-8"))
    if size > max_bytes:
        msg = (
            f"Component {class_id}: the serialized State is {size} bytes, over the _max_bytes cap of"
            f" {max_bytes}. State round-trips on every event call, so it should stay small (the audit"
            f" measured 150 to 300 bytes). Keep an id in State and reload the rest in the handler, or"
            f" raise _max_bytes if the size is genuinely needed."
        )
        raise ValueError(msg)


def _sign(payload: dict[str, Any], signing_secret: str) -> str:
    """Serialize, HMAC-sign, and armor the payload into a signed token string."""
    payload_bytes = _canonical_json(payload).encode("utf-8")
    signature = hmac.new(signing_secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"{_SIGNED_PREFIX}.{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}"


def _normalize_secrets(secret: str | list[str] | None) -> list[str]:
    """The secret(s) as a non-empty list of non-empty strings, or raise the pointed error."""
    if secret is None:
        raise SigningSecretError(_NO_SIGNING_KEY_MSG)
    secrets_list = [secret] if isinstance(secret, str) else list(secret)
    if not secrets_list or not all(isinstance(entry, str) and entry for entry in secrets_list):
        raise SigningSecretError(_NO_SIGNING_KEY_MSG)
    return secrets_list


# ----- Verifying -----


def verify_state_token(token: str, *, cls: Any, secrets: list[str], cache: CitryCache | None = None) -> VerifiedState:
    """
    Verify an echoed token and return the State fields to rebuild it from.

    Dispatches on the token's prefix, so the caller does not have to know the
    component's storage mode. For a signed token it checks the HMAC against
    every rotation secret in constant time and the expiry; for a server token it
    loads the entry from the cache. Either way it then confirms the token was
    minted for ``cls`` (the class-id binding), so a token for one component
    cannot be replayed against another.

    Args:
        token: The opaque token the client echoed back.
        cls: The component class the call dispatches to. Its ``class_id`` is the
            expected binding; the State is rebuilt from the result as
            ``cls.State(**verified.state_kwargs)`` by the caller.
        secrets: All valid signing secrets (the rotation list); every one is
            tried so tokens signed by a still-listed key keep verifying. Unused
            for server-storage tokens.
        cache: The cache backend, required to load a server-storage token.

    Returns:
        A [`VerifiedState`][citry.ext.events.tokens.VerifiedState] carrying the
        State fields and the bound class id.

    Raises:
        InvalidStateError: The token is malformed (its payload cannot be read
            as a well-formed token: bad base64, bad JSON, a wrong protocol
            version, or missing fields), or it was minted for another
            component (403).
        StaleStateError: The token is stale (409): it expired, its signature
            matches no current secret while the payload is still well-formed
            (a rotated-out signing secret, or a tampered signature, which is
            indistinguishable from one), or a server token's cache entry is
            gone. The 403/409 split is the error-codes rule in design
            section 4.3.

    """
    if not isinstance(token, str) or not token:
        # A missing or non-string token (for example a stateful call that arrived
        # with no state field) is malformed, not a crash: map it like any other
        # unreadable token instead of letting an AttributeError reach the caller.
        raise InvalidStateError(_MALFORMED_MSG)
    if token.startswith(_SERVER_PREFIX + "."):
        payload = _load_server_payload(token[len(_SERVER_PREFIX) + 1 :], cache)
    elif token.startswith(_SIGNED_PREFIX + "."):
        payload = _verify_signed(token, secrets)
    else:
        raise InvalidStateError(_MALFORMED_MSG)

    expected = cls.class_id
    if payload.get("c") != expected:
        msg = (
            f"The state token was minted for a different component (token class id"
            f" {payload.get('c')!r}, expected {expected!r}). Reload the page to get a token for this"
            f" component."
        )
        raise InvalidStateError(msg)

    return VerifiedState(state_kwargs=payload["s"], class_id=payload["c"])


def _verify_signed(token: str, secrets: list[str]) -> dict[str, Any]:
    """
    Check a signed token's structure, HMAC, and expiry, returning its payload.

    A signature that matches no secret is classified by payload well-formedness
    (the error-codes rule in design 4.3): a well-formed payload answers the
    stale-state 409, anything less the invalid-state 403.
    """
    parts = token.split(".")
    # A signed token is exactly three segments: prefix, payload, signature.
    if len(parts) != 3:
        raise InvalidStateError(_MALFORMED_MSG)
    _prefix, b64_payload, b64_sig = parts
    try:
        payload_bytes = _b64url_decode(b64_payload)
        signature = _b64url_decode(b64_sig)
    except (binascii.Error, ValueError) as err:
        raise InvalidStateError(_MALFORMED_MSG) from err

    secrets_list = [secrets] if isinstance(secrets, str) else list(secrets) if secrets else []
    matched = False
    for candidate in secrets_list:
        expected_sig = hmac.new(candidate.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
        # No early break: comparing against every rotation secret keeps the time
        # taken from revealing which key (if any) matched.
        if hmac.compare_digest(signature, expected_sig):
            matched = True
    if not matched:
        # The signature verifies against no current secret. Per the error-codes
        # rule in design 4.3 the payload decides the error code: a payload that
        # still parses as a well-formed token (valid JSON with the version,
        # component class, and state fields; base64 validity was checked above)
        # is exactly what a token signed by a rotated-out secret looks like, so
        # it answers stale_state (409). Anything less is malformed and answers
        # invalid_state (403). A signature-only tamper is indistinguishable
        # from a rotated-out secret, so it takes the stale path too. The
        # payload is parsed here only to pick the error code; nothing from it
        # is trusted or returned.
        _decode_payload(payload_bytes)  # raises the malformed 403 unless the payload is well-formed
        msg = (
            "The state token is stale: its signature matches no currently configured signing secret"
            " (for example the signing secret was rotated, or the token expired). Re-rendering the"
            " page refreshes the token. If you rotated secrets, keep the previous one in the secret"
            " list so already-issued tokens keep verifying."
        )
        raise StaleStateError(msg)

    payload = _decode_payload(payload_bytes)
    _check_expiry(payload)
    return payload


def _decode_payload(payload_bytes: bytes) -> dict[str, Any]:
    """Parse and shape-check a signed token's payload JSON."""
    try:
        payload = json.loads(
            payload_bytes,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError, ValueError) as err:
        # Payload bytes that are not UTF-8 raise UnicodeDecodeError, and JSON
        # nested too deep to parse raises RecursionError. Both are just as
        # malformed as bad JSON, and no minted token can produce either (mint
        # writes UTF-8 and would hit the same recursion limit first), so both
        # map to the 403 here instead of escaping verify as a crash.
        raise InvalidStateError(_MALFORMED_MSG) from err
    if not _valid_payload_shape(payload):
        raise InvalidStateError(_MALFORMED_MSG)
    return cast("dict[str, Any]", payload)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate field {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-finite number {value}")


def _valid_payload_shape(payload: object) -> bool:
    if type(payload) is not dict:
        return False
    value = cast("dict[str, Any]", payload)
    if set(value) != {"c", "s", "t", "v", "x"}:
        return False
    if type(value["v"]) is not int or value["v"] != _PROTOCOL_VERSION:
        return False
    if type(value["c"]) is not str or not value["c"] or type(value["s"]) is not dict:
        return False
    if type(value["t"]) is not int:
        return False
    expiry = value["x"]
    return expiry is None or (type(expiry) in (int, float) and math.isfinite(expiry))


def _check_expiry(payload: dict[str, Any]) -> None:
    """Reject a signed token past its expiry field as stale."""
    expiry = payload.get("x")
    if expiry is None:
        return
    if isinstance(expiry, bool) or not isinstance(expiry, (int, float)):
        raise InvalidStateError(_MALFORMED_MSG)
    if _now() >= expiry:
        msg = (
            "The state token has expired. Reload the page to get a fresh token; the component will"
            " pick up the latest server state."
        )
        raise StaleStateError(msg)


def _load_server_payload(key: str, cache: CitryCache | None) -> dict[str, Any]:
    """Load a server-storage token's payload from the cache, or map the miss to stale."""
    if cache is None:
        # A server-style token reached a component with no cache to load it from
        # (for example a signed-storage component being sent a token it never
        # minted). Treat it as invalid rather than crash.
        raise InvalidStateError(_MALFORMED_MSG)
    raw = cache.get(key)
    if raw is None:
        msg = (
            "The server-side state for this component is no longer available (it expired or was"
            " evicted from the cache). Reload the page to continue; keep an id in State and reload the"
            " rest so a lost cache entry is recoverable."
        )
        raise StaleStateError(msg)
    try:
        payload = json.loads(
            raw,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as err:
        raise InvalidStateError(_MALFORMED_MSG) from err
    # Same shape and protocol-version guard as the signed path (_decode_payload):
    # during a rolling deploy a v1 worker must reject a payload a future v2 worker
    # wrote, rather than read it under the wrong protocol.
    if not _valid_payload_shape(payload):
        raise InvalidStateError(_MALFORMED_MSG)
    return cast("dict[str, Any]", payload)


# ----- Applying two-way binding updates -----


def apply_state_updates(
    state: Any,
    updates: Mapping[str, Any] | None,
    *,
    model_fields: Iterable[str],
) -> tuple[str, ...]:
    """
    Apply the client's two-way binding writes to the writable State fields.

    Only fields in ``model_fields`` (the State ``_model`` set) may be written,
    and each value must match its field's declared type. All updates are checked
    first and the batch is rejected as a whole on any failure, so a State is
    never left half-mutated; a successful call mutates ``state`` in place.

    Args:
        state: The rebuilt State instance to mutate.
        updates: The two-way binding writes from the call envelope, or ``None``.
        model_fields: The writable field names (the State ``_model`` set).

    Returns:
        The applied field names, sorted, so the caller can tell whether the
        State changed and needs re-minting.

    Raises:
        StateUpdateError: When any update names a non-writable field or carries a
            value of the wrong type; ``fields`` holds the per-field messages
            (422).

    """
    if not updates:
        return ()
    writable = frozenset(model_fields)
    hints = _resolve_hints(type(state))
    errors: dict[str, str] = {}
    to_apply: list[tuple[str, Any]] = []
    # Sorted iteration keeps the per-field error order (and the applied list)
    # deterministic regardless of the wire dict's key order.
    for name in sorted(updates):
        value = updates[name]
        if name not in writable:
            errors[name] = "This field cannot be written from the client (it is not in the State _model set)."
            continue
        hint = hints.get(name)
        if not _value_matches(value, hint):
            errors[name] = f"Expected {_type_label(hint)}, got {type(value).__name__}."
            continue
        to_apply.append((name, value))
    if errors:
        raise StateUpdateError("Some state updates were rejected; see the field messages.", fields=errors)
    for name, value in to_apply:
        setattr(state, name, value)
    return tuple(name for name, _ in to_apply)


def _resolve_hints(state_cls: type) -> dict[str, Any]:
    """The State class's field types, resolved once and cached."""
    cached = _HINT_CACHE.get(state_cls)
    if cached is None:
        try:
            cached = get_type_hints(state_cls)
        except (NameError, TypeError):
            # Resolving the whole class at once failed because one field's
            # annotation will not resolve (for example a type imported only under
            # TYPE_CHECKING). Resolve the rest field by field so only that one
            # field falls back to a lenient check, not every field on the State.
            cached = _resolve_hints_per_field(state_cls)
        _HINT_CACHE[state_cls] = cached
    return cached


def _resolve_hints_per_field(state_cls: type) -> dict[str, Any]:
    """
    Resolve each field's annotation on its own, isolating an unresolvable one.

    Used only when resolving the whole class at once fails. A field whose
    annotation still will not resolve is left out of the result, so its check
    falls back to lenient (``hints.get(name)`` is then ``None``) while every
    field that did resolve keeps a real type check.
    """
    resolved: dict[str, Any] = {}
    # Walk the inheritance chain base-first so a subclass annotation overrides a
    # base one, and read each class's own annotations (not the inherited view) so
    # a base's fields are not counted twice.
    for klass in reversed(state_cls.__mro__):
        module = sys.modules.get(klass.__module__)
        global_ns = getattr(module, "__dict__", {})
        local_ns = dict(vars(klass))
        for name, annotation in klass.__dict__.get("__annotations__", {}).items():
            try:
                resolved[name] = _resolve_annotation(annotation, global_ns, local_ns)
            except Exception:  # noqa: BLE001
                # Any resolution failure leaves just this field lenient; the other
                # fields keep their real type checks.
                resolved.pop(name, None)
    return resolved


def _resolve_annotation(annotation: Any, global_ns: dict[str, Any], local_ns: dict[str, Any]) -> Any:
    """Resolve one possibly-stringized annotation to a type in the State's namespace."""
    if not isinstance(annotation, str):
        return annotation

    def _carrier() -> None: ...

    # A throwaway function carrying just this annotation, so get_type_hints
    # evaluates it exactly the way the whole-class path does, but for one field.
    _carrier.__annotations__ = {"field": annotation}
    return get_type_hints(_carrier, globalns=global_ns, localns=local_ns)["field"]


def _value_matches(value: Any, hint: Any) -> bool:
    """Whether a JSON value satisfies a field's declared type (a check, not a coercion)."""
    # No usable hint: cannot type-check reliably, so accept and rely on the
    # handler to authorize what it does with the value (7.2).
    if hint is None or isinstance(hint, str):
        return True
    origin = get_origin(hint)
    if origin is Union or origin is UnionType:
        return any(_value_matches(value, arm) for arm in get_args(hint))
    if hint is type(None):
        return value is None
    if hint is bool:
        return type(value) is bool
    if hint is int:
        # bool is a subclass of int, but a JSON true is not an integer input.
        return type(value) is int
    if hint is float:
        # JSON does not distinguish 1 from 1.0, so an int is a valid float value.
        return type(value) in (int, float)
    if hint is str:
        return isinstance(value, str)
    if hint is list or origin is list:
        return isinstance(value, list)
    if hint is dict or origin is dict:
        return isinstance(value, dict)
    if isinstance(hint, type):
        return isinstance(value, hint)
    # A parameterized or exotic annotation we do not special-case: accept.
    return True


def _type_label(hint: Any) -> str:
    """A short, readable name for a field's type, for the rejection message."""
    if hint is None or isinstance(hint, str):
        return "the declared type"
    if hint is type(None):
        return "null"
    origin = get_origin(hint)
    if origin is Union or origin is UnionType:
        return " or ".join(_type_label(arm) for arm in get_args(hint))
    name = getattr(hint, "__name__", None)
    return name if isinstance(name, str) else str(hint)


def _b64url_encode(data: bytes) -> str:
    """URL-safe base64 without padding, the token's armoring."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    """Reverse :func:`_b64url_encode`, restoring the stripped padding."""
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys and compact separators, so a token is byte-stable."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _state_value_description(value: Any) -> str:
    """A concise reason-bearing description for a State value rejected by strict JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return f"non-finite float {value!r}"
    return f"type {type(value).__name__}"
