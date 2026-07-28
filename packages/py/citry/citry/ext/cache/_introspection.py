"""Version 1 public metadata projection for the Cache extension."""

from __future__ import annotations

from types import FunctionType
from typing import TYPE_CHECKING, Literal, cast

from citry._class_introspection import _static_class_dict, _static_class_mro
from citry.cache import _normalize_ttl

from .keys import _validate_version

if TYPE_CHECKING:
    from citry.introspection import ComponentInfo


_MISSING = object()


def inspect_cache(component_class: type, info: ComponentInfo) -> dict[str, object] | None:
    """Build one allowlisted Cache v1 entry without executing component code."""
    if info.builtin and info.name == "cache":
        return None

    config_class = _static_class_dict(component_class).get("Cache")
    if not isinstance(config_class, type):
        raise TypeError("The component has no statically readable effective Cache config class.")

    enabled = _config_value(config_class, "enabled")
    ttl = _config_value(config_class, "ttl")
    version = _config_value(config_class, "version")
    vary = _config_value(config_class, "vary", default=None)

    if type(enabled) is not bool:
        raise RuntimeError("The effective component Cache enabled value is not an exact bool.")
    normalized_ttl = _normalize_ttl(ttl, source="component Cache ttl")
    encoded_version = _encode_version(version)
    variation: Literal["default", "custom"] = "custom" if type(vary) is FunctionType else "default"
    if variation == "custom":
        slot_source = "not-applicable"
    elif info.schemas.slots.kind == "fields" and not info.schemas.slots.fields:
        slot_source = "none"
    else:
        slot_source = "possible"

    return {
        "enabled": cast("bool", enabled),
        "ttl": normalized_ttl,
        "version": encoded_version,
        "variation": variation,
        "default_variation_slot_source": slot_source,
    }


def _config_value(config_class: type, name: str, *, default: object = _MISSING) -> object:
    """Read one effective config value without invoking descriptors or metaclasses."""
    for candidate in _static_class_mro(config_class):
        namespace = _static_class_dict(candidate)
        if name in namespace:
            return namespace[name]
    if default is not _MISSING:
        return default
    raise RuntimeError(f"The effective component Cache config has no {name!r} value.")


def _encode_version(value: object) -> dict[str, str]:
    """Preserve every valid Cache version in strict portable JSON."""
    try:
        _validate_version(value)
    except ValueError as error:
        raise RuntimeError("The effective component Cache version is invalid.") from error
    if type(value) is int:
        return {"kind": "integer", "value": hex(cast("int", value))}
    if type(value) is str:
        return {"kind": "string", "value": cast("str", value)}
    raise AssertionError("Validated Cache versions are exact integers or strings.")


__all__: list[str] = []
