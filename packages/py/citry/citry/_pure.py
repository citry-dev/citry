"""Render-local memoization primitives for explicitly pure component bodies."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, fields, is_dataclass
from typing import TYPE_CHECKING, Any, TypeAlias

from citry.constness import const_value

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.nodes import BodyItem, Node


@dataclass(frozen=True, slots=True)
class PureInteriorBody:
    """One transparent same-context render nested inside a reusable body."""

    parts: PureBodyPlan


@dataclass(frozen=True, slots=True)
class PureLiveBodyItem:
    """One ownership/i18n/dynamic hole that must execute on every replay."""

    item: Node


PureBodyPart: TypeAlias = "str | PureInteriorBody | PureLiveBodyItem"
PureBodyPlan: TypeAlias = tuple[PureBodyPart, ...]
_PureBodyKey = tuple[type[Any], int, object]
_PureBodyCache = dict[_PureBodyKey, PureBodyPlan]
_CURRENT_PURE_BODY_CACHE: ContextVar[_PureBodyCache | None] = ContextVar(
    "citry_pure_body_cache",
    default=None,
)


class _IdentityKey:
    """A hashable identity token that keeps its referenced object alive."""

    __slots__ = ("_hash", "value")

    def __init__(self, value: Any) -> None:
        self.value = value
        self._hash = id(value)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _IdentityKey) and self.value is other.value


@contextmanager
def pure_body_cache_scope() -> Iterator[None]:
    """Reuse an enclosing root-render memo or create one for this render."""
    if _CURRENT_PURE_BODY_CACHE.get() is not None:
        yield
        return
    token = _CURRENT_PURE_BODY_CACHE.set({})
    try:
        yield
    finally:
        _CURRENT_PURE_BODY_CACHE.reset(token)


def pure_body_lookup(
    component_class: type[Any],
    body: list[BodyItem],
    variables: Mapping[str, Any],
    used_vars: Iterable[str],
) -> tuple[_PureBodyKey, PureBodyPlan | None] | None:
    """Build one safe render-local key and return its memoized body, if any."""
    cache = _CURRENT_PURE_BODY_CACHE.get()
    if cache is None:
        return None
    try:
        frozen = (
            frozenset(variables),
            tuple((name, _freeze_local(variables[name], set())) for name in used_vars if name in variables),
        )
    except Exception:  # noqa: BLE001 - memoization must not add a render failure
        return None
    key = (component_class, id(body), frozen)
    return key, cache.get(key)


def store_pure_body(key: _PureBodyKey, plan: PureBodyPlan) -> None:
    """Store a qualified body plan for the rest of this root render."""
    cache = _CURRENT_PURE_BODY_CACHE.get()
    if cache is not None:
        cache[key] = plan


def _freeze_local(value: Any, active: set[int]) -> object:
    """Freeze common values by value and unknown live objects by identity."""
    value = const_value(value)
    value_type = type(value)
    if value is None or value_type in {bool, int, str, bytes}:
        return value_type, value
    if value_type is float:
        return value_type, value.hex()

    object_id = id(value)
    if object_id in active:
        return "identity", value_type, _IdentityKey(value)

    if isinstance(value, Mapping):
        active.add(object_id)
        try:
            return (
                "mapping",
                value_type,
                tuple((_freeze_local(key, active), _freeze_local(item, active)) for key, item in value.items()),
            )
        finally:
            active.remove(object_id)

    if isinstance(value, (list, tuple)):
        active.add(object_id)
        try:
            return "sequence", value_type, tuple(_freeze_local(item, active) for item in value)
        finally:
            active.remove(object_id)

    if isinstance(value, (set, frozenset)):
        active.add(object_id)
        try:
            return "set", value_type, frozenset(_freeze_local(item, active) for item in value)
        finally:
            active.remove(object_id)

    if not isinstance(value, type) and is_dataclass(value):
        active.add(object_id)
        try:
            return (
                "dataclass",
                value_type,
                tuple((field.name, _freeze_local(getattr(value, field.name), active)) for field in fields(value)),
            )
        finally:
            active.remove(object_id)

    # Unknown application objects are safe to reuse only when the exact same
    # live object appears again inside this one synchronous root render. The
    # public purity promise forbids mutating it between those occurrences.
    return "identity", value_type, _IdentityKey(value)
