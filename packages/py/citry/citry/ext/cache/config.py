"""Strict engine and component configuration for the built-in Cache extension."""

from __future__ import annotations

from dataclasses import dataclass
from inspect import iscoroutinefunction, isfunction
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from citry.cache import _normalize_ttl
from citry.extension import ExtensionConfig

from .keys import _validate_utf8_text, _validate_version

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry

_DEFAULT_TTL = 300
_DEFAULT_MAX_ENTRY_BYTES = 1_000_000
_ENGINE_FIELDS = frozenset({"ttl", "namespace", "generation", "max_entry_bytes"})
_COMPONENT_FIELDS = frozenset({"enabled", "ttl", "vary", "version"})


class CacheConfig(ExtensionConfig):
    """
    Typed runtime view of one component's ``Cache`` declaration.

    Citry creates this value from the component's nested ``Cache`` class. Read
    it through ``component.cache`` while the component is rendering.

    Attributes:
        enabled: Whether Citry may cache this component's rendered output.
        ttl: How many seconds an entry remains valid, or ``None`` for no
            expiry.
        version: An application-controlled value included in the cache key.

    """

    enabled: ClassVar[bool] = False
    ttl: ClassVar[float | None] = _DEFAULT_TTL
    version: ClassVar[int | str] = 1


@dataclass(frozen=True, slots=True)
class _CacheEngineDefaults:
    """Validated engine defaults held independently of caller mappings."""

    ttl: float | None
    namespace: str | None
    generation: str | None
    max_entry_bytes: int | None


@dataclass(frozen=True, slots=True)
class _CacheScope:
    """The application/deployment identity included in physical cache keys."""

    kind: Literal["local", "shared"]
    namespace: str | None
    generation: str | None
    engine_id: str | None


def _validate_engine_fields(fields: Mapping[str, Any]) -> None:
    """Validate one ``extensions_defaults['cache']`` mapping."""
    unknown = set(fields) - _ENGINE_FIELDS
    if unknown:
        names = ", ".join(repr(name) for name in sorted(unknown, key=repr))
        msg = f"unknown engine Cache field(s): {names}; valid fields are {', '.join(sorted(_ENGINE_FIELDS))}."
        raise ValueError(msg)

    _normalize_ttl(fields.get("ttl", _DEFAULT_TTL), source="Cache ttl")
    namespace = fields.get("namespace")
    generation = fields.get("generation")
    _validate_optional_nonempty_string(namespace, source="Cache namespace")
    _validate_optional_nonempty_string(generation, source="Cache generation")
    if generation is not None and namespace is None:
        msg = "Cache generation requires a non-empty namespace."
        raise ValueError(msg)

    max_entry_bytes = fields.get("max_entry_bytes", _DEFAULT_MAX_ENTRY_BYTES)
    if max_entry_bytes is not None and (type(max_entry_bytes) is not int or max_entry_bytes <= 0):
        msg = f"Cache max_entry_bytes must be None or an exact positive int; got {max_entry_bytes!r}."
        raise ValueError(msg)


def _validate_component_fields(fields: Mapping[str, Any]) -> None:
    """Validate one component's nested ``Cache`` declaration."""
    unknown = set(fields) - _COMPONENT_FIELDS
    if unknown:
        names = ", ".join(repr(name) for name in sorted(unknown, key=repr))
        msg = f"unknown component Cache field(s): {names}; valid fields are {', '.join(sorted(_COMPONENT_FIELDS))}."
        raise ValueError(msg)

    enabled = fields.get("enabled", False)
    if type(enabled) is not bool:
        msg = f"component Cache enabled must be an exact bool; got {enabled!r}."
        raise ValueError(msg)

    _normalize_ttl(fields.get("ttl", _DEFAULT_TTL), source="component Cache ttl")
    _validate_version(fields.get("version", 1))

    if "vary" in fields:
        vary = fields["vary"]
        if not isfunction(vary) or iscoroutinefunction(vary):
            msg = "component Cache vary must be a synchronous instance method."
            raise ValueError(msg)


def _build_engine_defaults(fields: Mapping[str, Any]) -> _CacheEngineDefaults:
    """Copy and normalize validated engine fields."""
    _validate_engine_fields(fields)
    return _CacheEngineDefaults(
        ttl=_normalize_ttl(fields.get("ttl", _DEFAULT_TTL), source="Cache ttl"),
        namespace=fields.get("namespace"),
        generation=fields.get("generation"),
        max_entry_bytes=fields.get("max_entry_bytes", _DEFAULT_MAX_ENTRY_BYTES),
    )


def _effective_scope(citry: Citry, defaults: _CacheEngineDefaults) -> _CacheScope:
    """Resolve local versus explicitly shared key scope for one engine."""
    if defaults.namespace is not None and defaults.generation is not None:
        return _CacheScope(
            kind="shared",
            namespace=defaults.namespace,
            generation=defaults.generation,
            engine_id=None,
        )
    return _CacheScope(
        kind="local",
        namespace=defaults.namespace,
        generation=None,
        engine_id=citry.engine_id,
    )


def _validate_optional_nonempty_string(value: object, *, source: str) -> None:
    if value is not None and (type(value) is not str or not value):
        msg = f"{source} must be None or an exact non-empty string; got {value!r}."
        raise ValueError(msg)
    if type(value) is str:
        _validate_utf8_text(value, source=source)
