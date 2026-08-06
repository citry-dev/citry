"""Preserve and compose nested classes authored on component definitions."""

from __future__ import annotations

import inspect
from copy import copy
from dataclasses import MISSING, Field, dataclass
from types import new_class
from typing import TYPE_CHECKING, Any, cast

from citry._class_introspection import (
    _safe_class_text,
    _static_class_attribute,
    _static_class_dict,
    _static_class_mro,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

_RAW_NESTED_DECLARATIONS_ATTR = "_citry_raw_nested_declarations"
_SYNTHESIZED_DECLARATION_ATTR = "_citry_synthesized_declaration"


@dataclass(frozen=True, slots=True)
class NestedClassDeclaration:
    """
    One nested class binding written on a component or definition base.

    Attributes:
        declaring_class: The class whose body contains the binding.
        name: The nested declaration name, such as ``"Events"``.
        value: The exact authored value. Supported declarations use a class,
            while ``None`` explicitly resets inherited declarations.

    """

    declaring_class: type
    name: str
    value: object


def _capture_nested_declarations(cls: type, namespace: Mapping[str, object], names: Iterable[str]) -> None:
    """Snapshot relevant authored bindings before Citry replaces them with effective classes."""
    captured = {name: namespace[name] for name in names if name in namespace}
    type.__setattr__(cls, _RAW_NESTED_DECLARATIONS_ATTR, captured)


def _get_nested_class_declarations(cls: type, name: str) -> tuple[NestedClassDeclaration, ...]:
    """Return every authored binding in component C3 order, including resets."""
    declarations: list[NestedClassDeclaration] = []
    for declaring_class in _static_class_mro(cls):
        namespace = _static_class_dict(declaring_class)
        captured = namespace.get(_RAW_NESTED_DECLARATIONS_ATTR)
        if isinstance(captured, dict):
            if name in captured:
                declarations.append(NestedClassDeclaration(declaring_class, name, captured[name]))
            continue

        # Plain definition bases have not passed through ComponentMeta, so
        # their class namespace is already the immutable authored source.
        if namespace.get("_citry_component_root", False) is True:
            continue
        if name in namespace:
            declarations.append(NestedClassDeclaration(declaring_class, name, namespace[name]))
    return tuple(declarations)


def _active_nested_class_declarations(cls: type, name: str) -> tuple[NestedClassDeclaration, ...]:
    """Return class-valued declarations through the first explicit reset."""
    active: list[NestedClassDeclaration] = []
    component_name = _safe_class_text(cls, "__name__") or "Component"
    for declaration in _get_nested_class_declarations(cls, name):
        if declaration.value is None:
            break
        if not isinstance(declaration.value, type):
            msg = (
                f"Component {component_name}: {name!r} must be a class (or None to reset"
                f" inherited {name}); got {declaration.value!r}."
            )
            raise ValueError(msg)  # noqa: TRY004 - one declaration-time error family
        active.append(declaration)
    return tuple(active)


def _compose_nested_declaration_class(cls: type, name: str) -> type | None:
    """Compose active raw declarations as bases in component C3 order."""
    declarations = _active_nested_class_declarations(cls, name)
    if not declarations:
        return None

    bases = _nested_declaration_bases(declarations)

    if len(bases) == 1:
        return bases[0]

    module = _safe_class_text(cls, "__module__") or "citry.component"
    component_qualname = _safe_class_text(cls, "__qualname__") or _safe_class_text(cls, "__name__") or "Component"
    qualname = f"{component_qualname}.{name}"

    def populate(namespace: dict[str, Any]) -> None:
        namespace.update(
            {
                "__module__": module,
                "__qualname__": qualname,
                _SYNTHESIZED_DECLARATION_ATTR: True,
            }
        )

    try:
        return new_class(name, bases, exec_body=populate)
    except TypeError as err:
        owners = ", ".join(
            _safe_class_text(declaration.declaring_class, "__name__") or "<class>" for declaration in declarations
        )
        component_name = _safe_class_text(cls, "__name__") or "Component"
        msg = (
            f"Component {component_name}: could not compose nested {name} declarations"
            f" from the C3 chain {owners}: {err}"
        )
        raise ValueError(msg) from err


def _nested_declaration_bases(declarations: Iterable[NestedClassDeclaration]) -> tuple[type, ...]:
    """Return the non-redundant declaration classes in C3 precedence order."""
    bases: list[type] = []
    for declaration in declarations:
        candidate = declaration.value
        candidate = cast("type", candidate)
        if any(candidate in _static_class_mro(existing) for existing in bases):
            continue
        bases.append(candidate)
    return tuple(bases)


def _convert_to_slotted_dataclass(
    user_cls: type,
    *,
    owner: type | None = None,
    name: str | None = None,
    frozen: bool = False,
) -> type:
    """Create one slotted dataclass over a composed raw declaration class."""
    annotations: dict[str, Any] = {}
    for klass in reversed(_static_class_mro(user_cls)):
        source_namespace = _static_class_dict(klass)
        if "__dataclass_fields__" in source_namespace:
            continue
        annotations.update(inspect.get_annotations(klass))

    provenance_class = user_cls if owner is None else owner
    module = _static_class_attribute(provenance_class, "__module__")
    qualname = _static_class_attribute(provenance_class, "__qualname__")
    if owner is not None and isinstance(qualname, str):
        qualname = f"{qualname}.{name or _safe_class_text(user_cls, '__name__') or 'Schema'}"
    shell_namespace: dict[str, Any] = {
        "__annotations__": annotations,
        "__module__": module if isinstance(module, str) else "citry.component",
        "__qualname__": qualname if isinstance(qualname, str) else _safe_class_text(user_cls, "__name__"),
        # Tooling must attribute effective fields to their authored bases, not
        # to this implementation-only class that copies the merged annotations.
        _SYNTHESIZED_DECLARATION_ATTR: True,
    }
    for field_name in annotations:
        default = inspect.getattr_static(user_cls, field_name, MISSING)
        if isinstance(default, Field):
            # dataclass() deletes an authored ``field(...)`` marker after it
            # consumes it, so the generated shell needs its own reference.
            shell_namespace[field_name] = copy(default)

    shell = new_class(
        _safe_class_text(user_cls, "__name__") or "Schema",
        (user_cls,),
        exec_body=lambda attrs: attrs.update(shell_namespace),
    )
    # ``types.new_class`` may leave ``__qualname__`` inherited when its value
    # matches a base. Dataclass's slots rebuild copies only own attributes.
    type.__setattr__(shell, "__qualname__", shell_namespace["__qualname__"])
    return dataclass(slots=True, frozen=frozen)(shell)


def _is_dataclass_family(declaration: type) -> bool:
    """Whether Citry can safely combine this declaration through dataclass fields."""
    namespace = _static_class_dict(declaration)
    if "__dataclass_fields__" in namespace:
        return True
    bases = _static_class_mro(declaration)[1:]
    return bases == (object,) or any("__dataclass_fields__" in _static_class_dict(base) for base in bases)


__all__: list[str] = []
