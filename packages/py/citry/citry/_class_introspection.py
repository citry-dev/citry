"""Static class metadata access that bypasses custom metaclass hooks."""

from __future__ import annotations

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
