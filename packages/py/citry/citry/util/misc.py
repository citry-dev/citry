"""Small, dependency-free helpers shared across the citry engine."""

from __future__ import annotations

import re
import sys
from dataclasses import fields, is_dataclass
from importlib import import_module
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib import parse

from typing_extensions import TypeIs

from citry._schema_introspection import _inspect_schema_class

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import ModuleType


# TypeIs (not TypeGuard) so type checkers also narrow the negative branch:
# "not a generator" rules the generator type out of a union.
def is_generator(obj: Any) -> TypeIs[Generator[Any, Any, Any]]:
    """Check if an object is a generator (anything with a ``send`` method)."""
    return hasattr(obj, "send")


def to_dict(data: Any) -> dict[str, Any]:
    """
    Convert an object to a plain dict.

    Handles ``dict``, ``NamedTuple``, ``dataclass``, and Pydantic model
    instances. This lets callers accept a typed ``Kwargs``/``Slots``/
    ``TemplateData`` instance interchangeably with a plain mapping. Pydantic
    is recognized by its attribute protocol (``model_fields`` for v2,
    ``__fields__`` for v1), not imported, so it stays out of citry's
    dependencies.

    The conversion is shallow on purpose: it does not recurse into nested
    dataclasses/models (unlike ``dataclasses.asdict`` or ``model_dump``),
    since the values are kept as-is for rendering.
    """
    if isinstance(data, dict):
        return data
    if hasattr(data, "_asdict"):  # NamedTuple
        return data._asdict()
    if is_dataclass(data) and not isinstance(data, type):  # dataclass instance
        return {f.name: getattr(data, f.name) for f in fields(data)}

    # Pydantic model instance (v2 `model_fields` first; v1 `__fields__`).
    model_fields = getattr(type(data), "model_fields", None)
    pydantic_v2 = isinstance(model_fields, dict)
    if not pydantic_v2:
        model_fields = getattr(type(data), "__fields__", None)
    if isinstance(model_fields, dict):
        normalized = {name: getattr(data, name) for name in model_fields}

        # Pydantic v2 keeps explicitly allowed extras in a dedicated mapping;
        # v1 keeps them beside declared fields in the instance dictionary.
        # They are part of the validated result and must not disappear when a
        # component data schema opts into accepting them.
        pydantic_extras = getattr(data, "__pydantic_extra__", None)
        if isinstance(pydantic_extras, dict):
            normalized.update(pydantic_extras)
        elif not pydantic_v2:
            instance_values = getattr(data, "__dict__", None)
            fields_set = getattr(data, "__fields_set__", None)
            if isinstance(instance_values, dict) and isinstance(fields_set, set):
                normalized.update(
                    (name, instance_values[name])
                    for name in fields_set
                    if name not in model_fields and name in instance_values
                )
        return normalized

    return dict(data)


class FieldSpec(NamedTuple):
    """One declared input field: its name, and whether a value must be given."""

    name: str
    required: bool


def get_fields(cls: Any) -> list[FieldSpec] | None:
    """
    Read the declared fields of a typed-input class (``Kwargs``/``Slots``).

    Returns one ``FieldSpec`` per field, or ``None`` when ``cls`` is not a
    recognized declaration style. Recognized styles, in the order checked:

    - dataclasses (what the Component metaclass produces from plain inner
      classes): required when the field has neither a default nor a default
      factory.
    - Pydantic v2 models, recognized by ``model_fields`` mapping field names
      to infos with ``is_required()``.
    - Pydantic v1 models, recognized by ``__fields__`` mapping field names to
      infos with a ``required`` flag.
    - NamedTuples (``_fields`` / ``_field_defaults``): required when the
      field has no default.

    Pydantic is recognized by its attribute protocol without being imported,
    so it stays out of citry's dependencies; any class following the same
    protocol works.
    """
    rich_fields = _inspect_schema_class(cls)
    if rich_fields is None:
        return None
    return [FieldSpec(field.name, field.required) for field in rich_fields]


def get_import_path(cls_or_fn: type | Any) -> str:
    """
    Return the full import path of a class or function, e.g. ``"path.to.MyClass"``.

    Built-ins return just the qualified name (``"str"``, not ``"builtins.str"``).
    """
    module: str | None = getattr(cls_or_fn, "__module__", None)
    qualname: str = cls_or_fn.__qualname__
    if not module or module == "builtins":
        return qualname
    return module + "." + qualname


def get_module_info(cls_or_fn: type | Any) -> tuple[ModuleType | None, str | None, str | None]:
    """
    Return the module, module name, and module file path where a class or
    function is defined.

    Any of the three may be ``None``: a class defined in the REPL or via
    ``exec`` has no module file, and a synthetic class may have no module at
    all. Callers treat a missing file path as "no module directory" and skip
    module-relative file resolution.
    """
    module_name: str | None = getattr(cls_or_fn, "__module__", None)

    module: ModuleType | None = None
    if module_name:
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            try:
                module = import_module(module_name)
            except Exception:  # noqa: BLE001 - any import failure means "no module info"
                module = None

    module_file_path: str | None = getattr(module, "__file__", None) if module else None

    return module, module_name, module_file_path


# A string is a glob if it contains at least one of `?`, `*`, or `[`.
_GLOB_RE = re.compile(r"[?*[]")


def is_glob(filepath: str) -> bool:
    """Return whether ``filepath`` contains glob characters (``?``, ``*``, ``[``)."""
    return _GLOB_RE.search(filepath) is not None


def snake_to_pascal(name: str) -> str:
    """
    Convert a snake_case name to PascalCase.

    ``my_extension`` -> ``MyExtension``. Used to derive an extension's
    ``class_name`` (the nested config class users define on a component) from
    its ``name``.
    """
    return "".join(part[:1].upper() + part[1:] for part in name.split("_"))


# Kept internal (not in citry's public __all__): generic URL plumbing, not citry-specific.
# Promote beside URLRoute/RouteResponse (util/routing.py) if a consumer like Component.Events needs it.
def format_url(url: str, query: dict[str, Any] | None = None, fragment: str | None = None) -> str:
    """
    Add query parameters and a fragment to a URL, returning the updated URL.

    ``query`` and ``fragment`` are optional and leave the URL untouched when
    ``None``. Any query parameters already on ``url`` are kept, with ``query``
    merged on top. A query value of ``True`` becomes a flag parameter with no
    value; ``False`` and ``None`` values are dropped.

    ```py
    format_url("https://example.com", query={"foo": "bar"}, fragment="baz")
    # "https://example.com?foo=bar#baz"

    format_url(
        "https://example.com",
        query={"foo": "bar", "baz": None, "enabled": True, "debug": False},
    )
    # "https://example.com?foo=bar&enabled"
    ```
    """
    parts = parse.urlsplit(url)
    fragment_enc = parse.quote(fragment or parts.fragment, safe="")
    base_query = dict(parse.parse_qsl(parts.query))
    # Drop None and False before merging; keep everything already on the URL.
    supplied = {key: value for key, value in (query or {}).items() if value is not None and value is not False}
    merged = {**base_query, **supplied}

    query_parts = []
    for key, value in merged.items():
        if value is True:
            # A True value is a flag parameter: emit the key alone, no "=value".
            query_parts.append(parse.quote_plus(str(key)))
        else:
            query_parts.append(f"{parse.quote_plus(str(key))}={parse.quote_plus(str(value))}")
    encoded_query = "&".join(query_parts)

    return parse.urlunsplit(parts._replace(query=encoded_query, fragment=fragment_enc))
