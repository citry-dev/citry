"""Read the classes a data method can reach through its kwargs, so tooling can type ``kwargs.task.lane``."""

from __future__ import annotations

import enum
import sys
import typing
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, get_origin

from citry._class_introspection import _static_class_mro
from citry._json_wire import WireClass
from citry._schema_introspection import _effective_schema_binding, _format_annotation

if TYPE_CHECKING:
    from collections.abc import Mapping

# A project's model graph can be large; this many classes covers ordinary
# attribute chains without letting one component copy a whole domain model.
_MAX_CLASSES = 64

# Builtin and container classes have no attributes worth following.
_LEAF_MODULES = frozenset({"builtins", "typing", "types", "collections.abc", "datetime", "decimal", "uuid"})


@dataclass(frozen=True, slots=True)
class KwargsWireClasses:
    """
    The annotations a data method reads when it follows attributes of its kwargs.

    Attributes:
        members: Each Kwargs field's annotation, resolved and written the way
            Citry formats schema types, so a class is its import path.
        classes: The classes those annotations reach, by import path.

    """

    members: Mapping[str, str | None] = field(default_factory=dict)
    classes: Mapping[str, WireClass] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready copy for the language server's worker payload."""
        return {
            "members": dict(self.members),
            "classes": {name: item.to_dict() for name, item in self.classes.items()},
        }

    @classmethod
    def from_dict(cls, value: object) -> KwargsWireClasses:
        """Validate and restore one copied record."""
        if type(value) is not dict or set(value) != {"members", "classes"}:
            msg = "kwargs wire class data must contain the exact supported fields"
            raise ValueError(msg)
        members = value["members"]
        classes = value["classes"]
        if type(members) is not dict or any(
            type(name) is not str or (annotation is not None and type(annotation) is not str)
            for name, annotation in members.items()
        ):
            msg = "kwargs wire class members must map names to annotations"
            raise ValueError(msg)
        if type(classes) is not dict or any(type(name) is not str for name in classes):
            msg = "kwargs wire classes must be keyed by import path"
            raise ValueError(msg)
        return cls(
            members=dict(members),
            classes={name: WireClass.from_dict(item) for name, item in classes.items()},
        )


def kwargs_wire_classes(component_class: type) -> KwargsWireClasses:
    """
    Describe the classes reachable from one component's effective Kwargs fields.

    ``citry check`` and the language server's app worker both call this, so
    they type ``kwargs.task.lane`` in ``js_data()`` the same way. Annotations
    are resolved in their own module, as ``typing.get_type_hints()`` does,
    so ``from __future__ import annotations`` still yields import paths. A
    name imported only under ``TYPE_CHECKING`` cannot be resolved at run
    time, and its chain stays unknown.
    """
    _owner, schema = _effective_schema_binding(component_class, "Kwargs")
    if not isinstance(schema, type):
        return KwargsWireClasses()
    members = _attribute_hints(schema)
    if members is None:
        return KwargsWireClasses()
    classes: dict[str, WireClass] = {}
    pending: list[object] = list(members.values())
    while pending and len(classes) < _MAX_CLASSES:
        hint = pending.pop(0)
        name = _followed_class_name(hint)
        if name is None or name in classes:
            continue
        described = _describe_class(typing.cast("type", hint))
        if described is None:
            continue
        wire_class, hints = described
        classes[name] = wire_class
        pending.extend(hints.values())
    return KwargsWireClasses(
        members={name: _format_annotation(hint) for name, hint in members.items()},
        classes=classes,
    )


def _followed_class_name(hint: object) -> str | None:
    """Return the import path of a user class whose attributes can be read, or ``None``."""
    # Only a plain class is followed. `Owner | None` or `list[Owner]` is not
    # a value whose attributes `js_data()` can read directly.
    if not isinstance(hint, type) or get_origin(hint) is not None:
        return None
    if hint.__module__ in _LEAF_MODULES:
        return None
    return _format_annotation(hint)


def _describe_class(cls: type) -> tuple[WireClass, dict[str, object]] | None:
    """Return one class's attribute annotations and the hints to follow from it."""
    if issubclass(cls, enum.Enum):
        members = tuple(cls)
        values = tuple(member.value for member in members)
        # `.value` is typed only when every value can be written as a JSON scalar.
        scalar = all(value is None or type(value) in {bool, int, float, str} for value in values)
        return (
            WireClass(
                attributes={},
                enum_values=values if scalar else None,
                enum_names=tuple(member.name for member in members),
            ),
            {},
        )
    hints = _attribute_hints(cls)
    if hints is None:
        return None
    return WireClass(attributes={name: _format_annotation(hint) for name, hint in hints.items()}), hints


def _attribute_hints(cls: type) -> dict[str, object] | None:
    """Return each public annotated attribute's resolved annotation, or ``None`` when the class has none."""
    try:
        # Resolves string annotations in the class's own module, including
        # every base class, and works for dataclasses, NamedTuple, TypedDict,
        # Pydantic models, and plain annotated classes alike.
        hints: dict[str, object] = typing.get_type_hints(cls)
    except Exception:  # noqa: BLE001 - an unresolvable annotation falls back to its raw form
        hints = _raw_annotations(cls)
    public = {name: hint for name, hint in hints.items() if not name.startswith("_") and not _is_class_var(hint)}
    return public or None


def _raw_annotations(cls: type) -> dict[str, object]:
    """Merge each base class's own annotations, nearest last, without evaluating strings."""
    merged: dict[str, object] = {}
    for candidate in reversed(_static_class_mro(cls)):
        own = candidate.__dict__.get("__annotations__")
        if isinstance(own, dict):
            merged.update(own)
    module = sys.modules.get(cls.__module__)
    namespace = vars(module) if module is not None else {}
    # A string annotation that names one importable object still resolves.
    return {
        name: namespace.get(hint, hint) if type(hint) is str and hint.isidentifier() else hint
        for name, hint in merged.items()
    }


def _is_class_var(hint: object) -> bool:
    return hint is ClassVar or get_origin(hint) is ClassVar or (type(hint) is str and hint.startswith("ClassVar"))


__all__: list[str] = []
