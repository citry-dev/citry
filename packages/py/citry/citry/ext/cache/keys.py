"""Canonical render-cache key encoding and public exact-key helpers."""

from __future__ import annotations

import base64
import hashlib
import json
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

from citry.constness import const_value, is_const

from .errors import CacheKeyError
from .limits import _MAX_KEY_BYTES, _MAX_KEY_DEPTH, _MAX_KEY_NODES

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.citry import Citry
    from citry.component import Component

_KEY_SCHEMA_VERSION = 1
_JSON_ENCODER = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class _ExtensionCacheCompatibility:
    """One installed extension's ordered render-cache compatibility stamp."""

    name: str
    mode: str
    version: int | None


@dataclass(frozen=True, slots=True)
class _CacheKeyContext:
    """Engine state sampled for one physical key calculation."""

    scope_kind: Literal["local", "shared"]
    namespace: str | None
    generation: str | None
    engine_id: str | None
    revision: int
    extensions: tuple[_ExtensionCacheCompatibility, ...]


@dataclass(slots=True)
class _EncodingState:
    nodes: int
    active: set[int]
    content_bytes: int


def component_cache_key(
    component: type[Component],
    *,
    vary: object,
    version: int | str = 1,
) -> str:
    """
    Build the exact physical key for one component variation.

    This helper does not construct the component, run input hooks, or call a
    component's ``Cache.vary()`` method. Callers supply the already-computed semantic
    variation value.

    Args:
        component: Component class whose stable class ID identifies the entry.
        vary: Semantic variation accepted by Citry's canonical key encoder.
        version: Author-controlled exact integer or non-empty string version.

    Returns:
        A short ASCII key suitable for deleting one exact backend entry.

    Raises:
        TypeError: If ``component`` is not a Component class.
        ValueError: If ``version`` is invalid.
        CacheKeyError: If ``vary`` cannot be encoded safely.

    """
    from citry.component import Component  # noqa: PLC0415

    if not isinstance(component, type) or not issubclass(component, Component):
        msg = f"component_cache_key() requires a Component class; got {component!r}."
        raise TypeError(msg)
    return _build_component_cache_key(
        cast("Any", component.citry.extensions.get_extension("cache"))._key_context(),
        component.class_id,
        vary=vary,
        version=version,
    )


def fragment_cache_key(
    citry: Citry,
    key: str,
    *,
    vary: object = (),
    version: int | str = 1,
) -> str:
    """
    Build the exact physical key for one named fragment variation.

    Like ``<c-cache>``, this unwraps an outer ``Const`` marker from ``key``,
    ``vary``, and ``version`` before validation and encoding.

    Args:
        citry: Engine whose cache scope and local revision apply.
        key: Exact non-empty semantic fragment name.
        vary: Semantic variation accepted by Citry's canonical key encoder.
        version: Author-controlled exact integer or non-empty string version.

    Returns:
        A short ASCII key suitable for deleting one exact backend entry.

    Raises:
        TypeError: If ``citry`` is not a Citry instance.
        ValueError: If ``key`` or ``version`` is invalid.
        CacheKeyError: If ``vary`` cannot be encoded safely.

    """
    from citry.citry import Citry  # noqa: PLC0415

    if not isinstance(citry, Citry):
        msg = f"fragment_cache_key() requires a Citry instance; got {citry!r}."
        raise TypeError(msg)
    normalized_key = const_value(key)
    normalized_vary = const_value(vary)
    normalized_version = const_value(version)
    if type(normalized_key) is not str or not normalized_key:
        msg = f"fragment cache key must be an exact non-empty string; got {normalized_key!r}."
        raise ValueError(msg)
    _validate_utf8_text(normalized_key, source="fragment cache key")
    return _build_fragment_cache_key(
        cast("Any", citry.extensions.get_extension("cache"))._key_context(),
        normalized_key,
        vary=normalized_vary,
        version=normalized_version,
    )


def _build_component_cache_key(
    context: _CacheKeyContext,
    class_id: str,
    *,
    vary: object,
    version: int | str,
) -> str:
    """Shared runtime/helper builder for a component physical key."""
    return _build_physical_key(context, "c", class_id, vary=vary, version=version)


def _build_fragment_cache_key(
    context: _CacheKeyContext,
    key: str,
    *,
    vary: object,
    version: int | str,
) -> str:
    """Shared runtime/helper builder for a named-fragment physical key."""
    return _build_physical_key(context, "f", key, vary=vary, version=version)


def _build_physical_key(
    context: _CacheKeyContext,
    kind: Literal["c", "f"],
    identity: str,
    *,
    vary: object,
    version: int | str,
) -> str:
    _validate_version(version)
    record_content_bytes = 0
    identity_path = "component class_id" if kind == "c" else "fragment key"
    record_content_bytes = _add_record_content(
        record_content_bytes,
        _precheck_text_size(identity, identity_path),
        identity_path,
    )
    for path, value in (
        ("cache namespace", context.namespace),
        ("cache generation", context.generation),
        ("cache engine_id", context.engine_id),
    ):
        if value is not None:
            record_content_bytes = _add_record_content(
                record_content_bytes,
                _precheck_text_size(value, path),
                path,
            )
    if len(context.extensions) > _MAX_KEY_NODES:
        raise CacheKeyError("extensions", f"compatibility list exceeds {_MAX_KEY_NODES:,} entries")
    for index, item in enumerate(context.extensions):
        name_path = f"extensions[{index}].name"
        mode_path = f"extensions[{index}].mode"
        record_content_bytes = _add_record_content(
            record_content_bytes,
            _precheck_text_size(item.name, name_path),
            name_path,
        )
        record_content_bytes = _add_record_content(
            record_content_bytes,
            _precheck_text_size(item.mode, mode_path),
            mode_path,
        )
        if item.version is not None:
            version_path = f"extensions[{index}].render_cache_version"
            record_content_bytes = _add_record_content(
                record_content_bytes,
                _hex_size(item.version),
                version_path,
            )
    variation_state = _EncodingState(nodes=0, active=set(), content_bytes=0)
    variation_tree = _canonical_cache_tree(
        vary,
        path="vary",
        state=variation_state,
        depth=0,
    )
    record_content_bytes = _add_record_content(
        record_content_bytes,
        variation_state.content_bytes,
        "vary",
    )
    if type(version) is int:
        if version.bit_length() > _MAX_KEY_BYTES * 4:
            raise CacheKeyError("version", "integer is too large for the 64 KiB canonical format")
        record_content_bytes = _add_record_content(record_content_bytes, _hex_size(version), "version")
        version_tree: list[Any] = ["i", hex(version)]
    else:
        version_string = cast("str", version)
        record_content_bytes = _add_record_content(
            record_content_bytes,
            _precheck_text_size(version_string, "version"),
            "version",
        )
        version_tree = ["s", version_string]
    extension_records: list[list[Any]] = []
    for index, item in enumerate(context.extensions):
        if item.version is not None and item.version.bit_length() > _MAX_KEY_BYTES * 4:
            raise CacheKeyError(
                f"extensions[{index}].render_cache_version",
                "integer is too large for the 64 KiB canonical format",
            )
        encoded_version = None if item.version is None else ["i", hex(item.version)]
        extension_records.append([item.name, item.mode, encoded_version])
    if context.revision.bit_length() > _MAX_KEY_BYTES * 4:
        raise CacheKeyError("revision", "integer is too large for the 64 KiB canonical format")
    _add_record_content(record_content_bytes, _hex_size(context.revision), "revision")
    record: list[Any] = [
        "citry-render-key",
        _KEY_SCHEMA_VERSION,
        [context.scope_kind, context.namespace, context.generation, context.engine_id],
        ["i", hex(context.revision)],
        kind,
        identity,
        version_tree,
        extension_records,
        variation_tree,
    ]
    digest = _hash_canonical_json(record, path="key")
    return f"citry:render:v1:{kind}:{digest}"


def _hash_canonical_json(value: object, *, path: str) -> str:
    """Hash canonical JSON incrementally while enforcing its byte budget."""
    digest = hashlib.sha256()
    for chunk in _iter_canonical_json(value, path=path):
        digest.update(chunk)
    return digest.hexdigest()


def _iter_canonical_json(value: object, *, path: str) -> Iterator[bytes]:
    """Yield UTF-8 JSON chunks and stop at the aggregate format limit."""
    total = 0
    for text in _JSON_ENCODER.iterencode(value):
        chunk = _encode_utf8(text)
        if chunk is None:
            raise CacheKeyError(path, "canonical data must be valid UTF-8 text; Unicode surrogates are unsupported")
        total += len(chunk)
        if total > _MAX_KEY_BYTES:
            raise CacheKeyError(path, "canonical encoded data exceeds the 64 KiB format limit")
        yield chunk


def _canonical_cache_tree(value: object, *, path: str, state: _EncodingState, depth: int) -> list[Any]:
    if depth > _MAX_KEY_DEPTH:
        raise CacheKeyError(path, f"nesting depth exceeds the {_MAX_KEY_DEPTH} level format limit")
    _count_node(state, path)

    if is_const(value):
        marker_id = id(value)
        _enter_container(state, marker_id, path)
        try:
            return [
                "c",
                _canonical_cache_tree(const_value(value), path=path, state=state, depth=depth + 1),
            ]
        finally:
            state.active.remove(marker_id)
    if value is None:
        return ["n"]
    if type(value) is bool:
        return ["b", value]
    if type(value) is int:
        if value.bit_length() > _MAX_KEY_BYTES * 4:
            raise CacheKeyError(path, "integer is too large for the 64 KiB canonical format")
        _count_content_bytes(state, _hex_size(value), path)
        return ["i", hex(value)]
    if type(value) is float:
        if not math.isfinite(value):
            raise CacheKeyError(path, "floats must be finite; NaN and infinity are unsupported")
        encoded_float = value.hex()
        _count_content_bytes(state, len(encoded_float), path)
        return ["f", encoded_float]
    if type(value) is str:
        _count_content_bytes(state, _precheck_text_size(value, path), path)
        return ["s", value]
    if type(value) is bytes:
        if len(value) > _MAX_KEY_BYTES:
            raise CacheKeyError(path, "bytes value exceeds the 64 KiB canonical format")
        base64_size = 4 * ((len(value) + 2) // 3)
        _count_content_bytes(state, base64_size, path)
        return ["y", base64.b64encode(value).decode("ascii")]
    if type(value) is list or type(value) is tuple:
        if state.nodes + len(value) > _MAX_KEY_NODES:
            raise CacheKeyError(path, f"value tree exceeds the {_MAX_KEY_NODES:,} node format limit")
        container_id = id(value)
        _enter_container(state, container_id, path)
        try:
            tag = "l" if type(value) is list else "t"
            items = [
                _canonical_cache_tree(item, path=f"{path}[{index}]", state=state, depth=depth + 1)
                for index, item in enumerate(value)
            ]
            return [tag, items]
        finally:
            state.active.remove(container_id)
    if type(value) is dict:
        if state.nodes + (2 * len(value)) > _MAX_KEY_NODES:
            raise CacheKeyError(path, f"value tree exceeds the {_MAX_KEY_NODES:,} node format limit")
        container_id = id(value)
        _enter_container(state, container_id, path)
        try:
            keys = list(value)
            for key in keys:
                if type(key) is not str:
                    raise CacheKeyError(path, f"dict keys must be exact strings; got {type(key).__name__}")
                _count_content_bytes(state, _precheck_text_size(key, path), path)
            pairs: list[list[Any]] = []
            for key in sorted(keys):
                _count_node(state, f"{path}[{key!r}]")
                pairs.append(
                    [
                        key,
                        _canonical_cache_tree(
                            value[key],
                            path=f"{path}[{key!r}]",
                            state=state,
                            depth=depth + 1,
                        ),
                    ]
                )
            return ["d", pairs]
        finally:
            state.active.remove(container_id)

    raise CacheKeyError(path, f"unsupported value type {type(value).__name__}")


def _count_node(state: _EncodingState, path: str) -> None:
    state.nodes += 1
    if state.nodes > _MAX_KEY_NODES:
        raise CacheKeyError(path, f"value tree exceeds the {_MAX_KEY_NODES:,} node format limit")


def _count_content_bytes(state: _EncodingState, size: int, path: str) -> None:
    """Reject aggregate scalar content before building a large tagged tree."""
    state.content_bytes += size
    if state.content_bytes > _MAX_KEY_BYTES:
        raise CacheKeyError(path, "canonical encoded data exceeds the 64 KiB format limit")


def _add_record_content(current: int, size: int, path: str) -> int:
    """Add a key-record scalar size before materializing its encoded form."""
    total = current + size
    if total > _MAX_KEY_BYTES:
        raise CacheKeyError(path, "canonical encoded data exceeds the 64 KiB format limit")
    return total


def _hex_size(value: int) -> int:
    """Return the exact length of ``hex(value)`` without creating the string."""
    if value == 0:
        return 3
    return ((value.bit_length() + 3) // 4) + 2 + (1 if value < 0 else 0)


def _enter_container(state: _EncodingState, container_id: int, path: str) -> None:
    if container_id in state.active:
        raise CacheKeyError(path, "value tree contains a cycle")
    state.active.add(container_id)


def _precheck_text_size(value: str, path: str) -> int:
    if len(value) > _MAX_KEY_BYTES:
        raise CacheKeyError(path, "string exceeds the 64 KiB canonical format")
    encoded = _encode_utf8(value)
    if encoded is None:
        raise CacheKeyError(path, "string must be valid UTF-8 text; Unicode surrogates are unsupported")
    size = len(encoded)
    if size > _MAX_KEY_BYTES:
        raise CacheKeyError(path, "string exceeds the 64 KiB canonical format")
    return size


def _validate_version(version: object) -> None:
    if type(version) is int:
        return
    if type(version) is str and version:
        _validate_utf8_text(version, source="cache version")
        return
    msg = f"cache version must be an exact int or a non-empty exact string; got {version!r}."
    raise ValueError(msg)


def _validate_utf8_text(value: str, *, source: str) -> None:
    """Reject Python strings that cannot be represented by the cache's UTF-8 wire format."""
    if _encode_utf8(value) is None:
        msg = f"{source} must be valid UTF-8 text; Unicode surrogates are unsupported."
        raise ValueError(msg)


def _encode_utf8(value: str) -> bytes | None:
    """Encode text strictly without leaking ``UnicodeEncodeError`` through public APIs."""
    try:
        return value.encode("utf-8")
    except UnicodeEncodeError:
        return None
