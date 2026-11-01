"""Static class metadata access that bypasses custom metaclass hooks."""

from __future__ import annotations

from _py_abc import ABCMeta as _PyABCMeta
from abc import ABCMeta
from types import MappingProxyType
from typing import TYPE_CHECKING

from citry.introspection import _is_utf8_string

if TYPE_CHECKING:
    from collections.abc import Mapping


# Counts authored attribute writes and deletions on component classes (those
# built by ComponentMeta; plain mixin bases are not counted) after they are
# defined. A cache derived from class declarations stores the count
# it was built with, and rebuilds once the count moves, so an assignment such
# as ``Card.on_render = ...`` after the first render is still seen.
_component_declaration_writes = [0]


def _component_declaration_generation() -> int:
    """Return the current count of post-definition component class writes."""
    return _component_declaration_writes[0]


def _advance_component_declaration_generation() -> None:
    """Record that some component class changed an authored declaration."""
    _component_declaration_writes[0] += 1


def _static_class_attribute(cls: type, name: str) -> object:
    """Read one type-owned descriptor without calling ``type(cls)`` hooks."""
    descriptor = type.__dict__.get(name)
    if descriptor is None:
        return None
    try:
        return descriptor.__get__(cls)
    except (AttributeError, TypeError):
        return None


def _static_class_dict(cls: type) -> Mapping[str, object]:
    """Return a class namespace without invoking its metaclass."""
    value = _static_class_attribute(cls, "__dict__")
    if type(value) is MappingProxyType:
        return value
    return {}


def _static_class_namespace_copy(cls: type) -> dict[str, object]:
    """
    Return a copy of a class namespace without invoking its metaclass.

    Citry stores computed results on component and State classes the first
    time they are needed (the loaded template, resolved assets, the record of
    whether a ``simple='vue'`` class can render without an instance), and any
    render thread can store one at any moment. Python raises
    ``RuntimeError`` when a dict gains or loses a key while a loop is walking
    it, so a caller that loops over the members of such a class loops over
    this copy rather than over ``_static_class_dict``.
    """
    value = _static_class_attribute(cls, "__dict__")
    if type(value) is MappingProxyType:
        # The proxy forwards copy() to the class's own dict, whose copy() runs
        # in C without stopping partway, so another thread cannot change the
        # dict mid-copy, with or without the GIL.
        return value.copy()
    return {}


def _names_abc_meta_writes(meta: type) -> frozenset[str]:
    """Return the non-dunder names ``meta`` writes into a class it builds with an empty body."""
    empty = meta("_EmptyABC", (), {})
    namespace = _static_class_namespace_copy(empty)
    return frozenset(name for name in namespace if not (name.startswith("__") and name.endswith("__")))


# ABCMeta stores, on every class it builds, the caches it keeps to answer
# `isinstance()` and `issubclass()` quickly. The names differ by
# implementation: CPython's `abc.ABCMeta` writes `_abc_impl`, while PyPy's
# `abc.ABCMeta` writes `_abc_registry`, `_abc_cache`, `_abc_negative_cache`
# and `_abc_negative_cache_version`, the same names as the stdlib's
# pure-Python `_py_abc`. `_py_abc` is listed too, so a test on CPython can
# build a class the way PyPy does. Each set is read from an empty class on the
# running interpreter, so it matches whatever that interpreter writes.
_ABC_BOOKKEEPING: tuple[tuple[type, frozenset[str]], ...] = tuple(
    (meta, _names_abc_meta_writes(meta)) for meta in dict.fromkeys((ABCMeta, _PyABCMeta))
)


def _is_abc_bookkeeping(cls: type, name: str) -> bool:
    """
    Return whether ``name`` on ``cls`` is a cache that an ABCMeta wrote, not an authored attribute.

    A check that rejects unknown underscore names on a class uses this to
    leave the metaclass's own entries alone. Every Pydantic model's metaclass
    extends ABCMeta, so this covers model classes too.
    """
    # `type(cls)` rather than `isinstance`, which could read `cls.__class__`
    # through a metaclass hook; this module reads classes without running one.
    metaclass = type(cls)
    return any(name in names and issubclass(metaclass, meta) for meta, names in _ABC_BOOKKEEPING)


def _static_class_mro(cls: type) -> tuple[type, ...]:
    """Return a class MRO without invoking its metaclass."""
    value = _static_class_attribute(cls, "__mro__")
    if type(value) is not tuple or not all(isinstance(candidate, type) for candidate in value):
        return ()
    return value


def _safe_class_text(cls: type, name: str) -> str | None:
    """Return a valid text field owned by ``type``, or ``None``."""
    value = _static_class_attribute(cls, name)
    if type(value) is not str or not value or not _is_utf8_string(value):
        return None
    return value


def _safe_class_import_path(cls: type) -> str | None:
    """Read a class path without invoking its metaclass's representation."""
    module = _safe_class_text(cls, "__module__")
    qualname = _safe_class_text(cls, "__qualname__")
    if qualname is None or module is None:
        return None
    if module == "builtins":
        return qualname
    return f"{module}.{qualname}"


__all__: list[str] = []
