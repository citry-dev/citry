"""Read the classes a data method can reach through its kwargs, so tooling can type ``kwargs.task.lane``."""

from __future__ import annotations

import enum
import math
import sys
import typing
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, ForwardRef, TypeVar, get_origin

import typing_extensions

from citry._annotation_introspection import _own_annotations
from citry._class_introspection import _safe_class_text, _static_class_mro
from citry._json_wire import WireClass, WireClassKind
from citry._schema_introspection import _effective_schema_binding, _format_annotation
from citry.introspection import _is_utf8_string

if TYPE_CHECKING:
    from collections.abc import Mapping

# A project's model graph can be large; this many classes covers ordinary
# attribute chains without letting one component copy a whole domain model.
_MAX_CLASSES = 64

# Standard-library value and container classes have no attributes worth following.
_LEAF_MODULES = frozenset({"builtins", "typing", "types", "collections.abc", "datetime", "decimal", "uuid"})

# An annotation that could not be resolved; its attribute stays untyped.
_UNRESOLVED = object()

# Wrappers around an attribute's value type: TypedDict key markers and
# `Annotated` metadata. Each takes the value type as its first argument.
_VALUE_WRAPPERS = frozenset(
    {
        typing_extensions.Annotated,
        typing_extensions.NotRequired,
        typing_extensions.ReadOnly,
        typing_extensions.Required,
    }
)


@dataclass(frozen=True, slots=True)
class KwargsWireClasses:
    """
    The annotations a data method reads when it follows attributes of its kwargs.

    Attributes:
        members: Each Kwargs field's annotation, resolved and written the way
            Citry formats schema types, so a class is its import path.
        classes: The classes those annotations reach, by import path.
        class_modules: The module of each class named anywhere in
            ``members``, by import path. An import path such as
            ``app.store.Board.Row`` does not say where the module ends and
            the nested class begins, so a tool that imports the class reads
            the module here.

    """

    members: Mapping[str, str | None] = field(default_factory=dict)
    classes: Mapping[str, WireClass] = field(default_factory=dict)
    class_modules: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready copy for the language server's worker payload."""
        return {
            "members": dict(self.members),
            "classes": {name: item.to_dict() for name, item in self.classes.items()},
            "class_modules": dict(self.class_modules),
        }

    @classmethod
    def from_dict(cls, value: object) -> KwargsWireClasses:
        """Validate and restore one copied record."""
        if type(value) is not dict or set(value) != {"members", "classes", "class_modules"}:
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
        class_modules = value["class_modules"]
        if type(class_modules) is not dict or any(
            type(path) is not str or type(module) is not str for path, module in class_modules.items()
        ):
            msg = "kwargs wire class modules must map import paths to module names"
            raise ValueError(msg)
        return cls(
            members=dict(members),
            classes={name: WireClass.from_dict(item) for name, item in classes.items()},
            class_modules=dict(class_modules),
        )


def kwargs_wire_classes(component_class: type) -> KwargsWireClasses:
    """
    Describe the classes reachable from one component's effective Kwargs fields.

    ``citry check`` and the language server's app worker both call this, so
    they type ``kwargs.task.lane`` in ``js_data()`` the same way. Annotations
    are resolved in their own module, as ``typing.get_type_hints()`` does,
    so ``from __future__ import annotations`` still yields import paths. An
    annotation that cannot be resolved, such as a name imported only under
    ``TYPE_CHECKING``, leaves that attribute untyped. A class whose metadata
    raises is left out, so this function never raises.
    """
    try:
        _owner, schema = _effective_schema_binding(component_class, "Kwargs")
        members = _attribute_hints(schema) if isinstance(schema, type) else None
    except Exception:  # noqa: BLE001 - project classes may raise anywhere; their chains then stay unknown
        return KwargsWireClasses()
    if members is None:
        return KwargsWireClasses()
    members = {name: _alias_value(hint) for name, hint in members.items()}
    classes: dict[str, WireClass] = {}
    pending: list[object] = list(members.values())
    while pending and len(classes) < _MAX_CLASSES:
        hint = pending.pop(0)
        try:
            name = _followed_class_name(hint)
            if name is None or name in classes:
                continue
            described = _describe_class(typing.cast("type", hint))
        except Exception:  # noqa: BLE001, S112 - one class with raising metadata is left out
            continue
        if described is None:
            continue
        wire_class, hints = described
        classes[name] = wire_class
        pending.extend(hints.values())
    class_modules: dict[str, str] = {}
    for hint in members.values():
        _collect_class_modules(hint, class_modules, depth=0)
    return KwargsWireClasses(
        members={name: _hint_display(hint) for name, hint in members.items()},
        classes=classes,
        class_modules=class_modules,
    )


# Annotations nest only a few levels in practice; this bounds a pathological one.
_MAX_ANNOTATION_DEPTH = 16


def _collect_class_modules(hint: object, found: dict[str, str], *, depth: int) -> None:
    """Record the module of each class named in one resolved annotation, such as both classes in `A | list[B]`."""
    if depth > _MAX_ANNOTATION_DEPTH:
        return
    if isinstance(hint, type) and get_origin(hint) is None:
        path = _format_annotation(hint)
        module = _safe_class_text(hint, "__module__")
        if path is not None and module is not None and path.startswith(f"{module}."):
            found.setdefault(path, module)
        return
    try:
        arguments = typing.get_args(hint)
    except Exception:  # noqa: BLE001 - an unusual typing object names no class to record
        return
    for argument in arguments if type(arguments) is tuple else ():
        _collect_class_modules(argument, found, depth=depth + 1)


def _alias_value(hint: object) -> object:
    """Return what a `type Name = ...` alias (Python 3.12+) stands for, or `hint` itself."""
    # An alias can name another alias; a few steps cover real code and stop a cycle.
    for _ in range(_MAX_ANNOTATION_DEPTH):
        if type(hint).__name__ != "TypeAliasType":
            return hint
        try:
            hint = hint.__value__  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - an alias whose value fails to evaluate names nothing
            return _UNRESOLVED
    return _UNRESOLVED


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
    if issubclass(cls, enum.Flag):
        # A combined flag such as `Perm.R | Perm.W` is not one of the listed
        # members, so its `.value` and `.name` cannot be listed.
        return None
    if issubclass(cls, enum.Enum):
        members = tuple(cls)
        values = tuple(member.value for member in members)
        names = tuple(member.name for member in members)
        return (
            WireClass(
                attributes={},
                kind="enum",
                enum_values=values if all(_is_json_scalar(value) for value in values) else None,
                enum_names=names if all(_is_utf8_string(name) for name in names) else None,
            ),
            {},
        )
    hints = _attribute_hints(cls)
    if hints is None:
        return None
    kind: WireClassKind = "object"
    required: tuple[str, ...] | None = None
    if typing_extensions.is_typeddict(cls):
        kind = "typed-dict"
        required = tuple(name for name in hints if _typed_dict_key_required(cls, name))
    elif issubclass(cls, tuple) and hasattr(cls, "_fields"):
        kind = "named-tuple"
    return (
        WireClass(
            attributes={name: _hint_display(hint) for name, hint in hints.items()},
            kind=kind,
            required=required,
        ),
        hints,
    )


def _typed_dict_key_required(cls: type, name: str) -> bool:
    """Return whether a TypedDict value always has key ``name``."""
    try:
        # `__required_keys__` misses a `NotRequired[...]` written as a string
        # under postponed annotations, so read the resolved markers instead.
        marked = typing_extensions.get_type_hints(cls, include_extras=True).get(name)
    except Exception:  # noqa: BLE001 - fall back to the class's own record
        return name in getattr(cls, "__required_keys__", ())
    # A key can carry several markers, such as `ReadOnly[NotRequired[str]]`,
    # so look through each of them for the one that decides presence.
    for _ in range(_MAX_ANNOTATION_DEPTH):
        # typing_extensions spells the markers the same way on every supported Python.
        origin = typing_extensions.get_origin(marked)
        if origin is typing_extensions.NotRequired:
            return False
        if origin is typing_extensions.Required:
            return True
        if origin not in _VALUE_WRAPPERS:
            break
        marked = typing_extensions.get_args(marked)[0]
    return bool(getattr(cls, "__total__", True))


def _value_hint(hint: object) -> object:
    """Return the value type inside key markers and `Annotated`, such as `str` for `NotRequired[str]`."""
    # A marker says whether a TypedDict key is present or writable, not what
    # its value is, and Python 3.10 (3.12 and earlier for `ReadOnly`) leaves
    # the typing_extensions markers in place, so remove them here to read the
    # same type on every version.
    for _ in range(_MAX_ANNOTATION_DEPTH):
        if typing_extensions.get_origin(hint) not in _VALUE_WRAPPERS:
            return hint
        hint = typing_extensions.get_args(hint)[0]
    return _UNRESOLVED


def _is_json_scalar(value: object) -> bool:
    """Return whether ``value`` can be written as one JSON scalar, so it may be a literal type."""
    if value is None or type(value) in {bool, int}:
        return True
    if type(value) is float:
        return math.isfinite(typing.cast("float", value))
    return type(value) is str and _is_utf8_string(typing.cast("str", value))


def _hint_display(hint: object) -> str | None:
    """Format one resolved annotation, or ``None`` when it names no concrete type."""
    # A type variable, or an annotation that never resolved, would otherwise
    # be read as a class name that cannot cross the wire.
    if hint is _UNRESOLVED or isinstance(hint, (TypeVar, ForwardRef, str)):
        return None
    return _format_annotation(hint)


def _attribute_hints(cls: type) -> dict[str, object] | None:
    """Return each public annotated attribute's resolved annotation, or ``None`` when the class has none."""
    try:
        # Resolves string annotations in the class's own module, including
        # every base class, and works for dataclasses, NamedTuple, TypedDict,
        # Pydantic models, and plain annotated classes alike.
        # typing_extensions' version also removes the TypedDict key markers
        # that the standard one keeps (all of them on 3.10, `ReadOnly` through 3.12).
        hints: dict[str, object] = typing_extensions.get_type_hints(cls)
    except Exception:  # noqa: BLE001 - one unresolvable annotation falls back to resolving each alone
        hints = _resolved_one_by_one(cls)
    values = {name: _value_hint(hint) for name, hint in hints.items() if not name.startswith("_")}
    # The fallback keeps `Annotated`, so a ClassVar can sit inside one; check
    # both forms so a class attribute is never read as an instance attribute.
    public = {
        name: value for name, value in values.items() if not _is_class_var(hints[name]) and not _is_class_var(value)
    }
    return public or None


def _resolved_one_by_one(cls: type) -> dict[str, object]:
    """Resolve each annotation in its declaring class's module, marking the ones that fail."""
    merged: dict[str, object] = {}
    for candidate in reversed(_static_class_mro(cls)):
        module = sys.modules.get(candidate.__module__)
        namespace = dict(vars(module)) if module is not None else {}
        for name, hint in _own_annotations(candidate).items():
            merged[name] = _resolve_annotation(hint, namespace)
    return merged


def _resolve_annotation(hint: object, namespace: dict[str, object]) -> object:
    """Evaluate one string or forward-reference annotation, or return ``_UNRESOLVED``."""
    source = hint if type(hint) is str else hint.__forward_arg__ if isinstance(hint, ForwardRef) else None
    if source is None:
        return hint
    try:
        return eval(source, namespace)  # noqa: S307 - the app's own annotation, as get_type_hints evaluates it
    except Exception:  # noqa: BLE001 - an unresolvable name leaves the attribute untyped
        # Keep a ClassVar recognizable, so it is still dropped.
        return source if source.startswith(("ClassVar", "typing.ClassVar")) else _UNRESOLVED


def _is_class_var(hint: object) -> bool:
    if hint is ClassVar or get_origin(hint) is ClassVar:
        return True
    return type(hint) is str and hint.startswith(("ClassVar", "typing.ClassVar"))


__all__: list[str] = []
