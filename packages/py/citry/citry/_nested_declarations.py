"""
Preserve authored nested classes and resolve them for one component class.

A component carries two kinds of nested classes. Data shapes (``Kwargs``,
``Slots``, ``State``, ``TemplateData``, ``JsData``, ``CssData``) follow
ordinary Python inheritance: the nearest declaration in the component's
method resolution order (C3 order) applies, and a subclass extends its
parent's shape only by naming it as a base. Settings classes (``Events``,
``Lint``, ``Cache``, extension configs) are combined across every
declaration instead. This module keeps the authored bindings and provides
both resolutions.
"""

from __future__ import annotations

from copy import copy
from dataclasses import MISSING, Field, InitVar, dataclass, fields, is_dataclass
from types import new_class
from typing import TYPE_CHECKING, Any, ClassVar, cast, get_origin
from weakref import WeakKeyDictionary

from citry._annotation_introspection import _own_annotations
from citry._caller_warnings import warn_at_caller
from citry._class_introspection import (
    _safe_class_text,
    _static_class_attribute,
    _static_class_dict,
    _static_class_mro,
    _static_class_namespace_copy,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from citry._model_base import ModelBase

_RAW_NESTED_DECLARATIONS_ATTR = "_citry_raw_nested_declarations"
_SYNTHESIZED_DECLARATION_ATTR = "_citry_synthesized_declaration"
_SYNTHESIZED_FIELD_OWNERS_ATTR = "_citry_synthesized_field_owners"
_CONST_SCHEMA_DEFAULTS_ATTR = "_citry_const_schema_defaults"
# CPython marks every class created by a class statement with this type flag.
_HEAP_TYPE_FLAG = 1 << 9
# A plain class that defines one of these constructs instances its own way,
# so a generated dataclass ``__init__`` must not replace it.
_CUSTOM_CONSTRUCTION_NAMES = frozenset({"__init__", "__new__", "__slots__", "model_fields", "__fields__", "_fields"})

# The data shapes `model_base` generates. `Slots` holds render content, not
# field values, so it always stays a dataclass.
_MODEL_BASE_SCHEMA_NAMES = frozenset({"Kwargs", "TemplateData", "JsData", "CssData"})

# A library definition is materialized once per Citry instance that installs
# it, so remember which definitions already warned to warn only once each.
_WARNED_REPLACEMENTS: WeakKeyDictionary[type, set[str]] = WeakKeyDictionary()


class NestedSchemaReplacedWarning(UserWarning):
    """
    Warn that a subclass's nested data class drops fields its parent declared.

    A nested data class on a subclass, such as ``class Kwargs:``, replaces
    the parent's class of the same name, the same as any nested Python
    class. Citry emits this warning once, when the subclass is defined (or,
    for a library component, when its library is registered), if the new
    class leaves out fields that the parent's class declared. For ``State``
    it also warns when the new class stops setting ``_public``, ``_model``,
    or ``_max_age`` that the parent's ``State`` set.

    To keep the parent's fields, name the parent's class as a base. To drop
    them on purpose, silence this warning class with the standard
    [`warnings`](https://docs.python.org/3/library/warnings.html) filters.

    Example:
        ```python
        class Message(Component):
            class Kwargs:
                text: str

        # Warns: Kwargs replaces Message.Kwargs and leaves out 'text'.
        class SignedMessage(Message):
            class Kwargs:
                signature: str

        # Keeps 'text' and adds 'signature'; no warning.
        class SignedMessageFixed(Message):
            class Kwargs(Message.Kwargs):
                signature: str
        ```

    """


@dataclass(frozen=True, slots=True)
class NestedClassDeclaration:
    """
    One nested class binding written on a component or definition base.

    Attributes:
        declaring_class: The class whose body contains the binding.
        name: The nested declaration name, such as ``"Events"``.
        value: The exact authored value. Supported declarations use a class,
            while ``None`` declares that the component has no such class.

    """

    declaring_class: type
    name: str
    value: object


def _capture_nested_declarations(cls: type, namespace: Mapping[str, object], names: Iterable[str]) -> None:
    """Snapshot relevant authored bindings before Citry replaces them with effective classes."""
    captured = {name: namespace[name] for name in names if name in namespace}
    type.__setattr__(cls, _RAW_NESTED_DECLARATIONS_ATTR, captured)


def _get_nested_class_declarations(cls: type, name: str) -> tuple[NestedClassDeclaration, ...]:
    """Return every authored binding in component C3 order, including ``None`` bindings."""
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
    """Return the class-valued settings declarations through the first ``None`` binding."""
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


def _is_processed_component(cls: type) -> bool:
    """Whether ComponentMeta already resolved this class's nested declarations."""
    return isinstance(_static_class_dict(cls).get(_RAW_NESTED_DECLARATIONS_ATTR), dict)


def _resolved_binding(declaration: NestedClassDeclaration) -> object:
    """Return the class a declaring component actually uses for this binding."""
    # ComponentMeta replaces a plain declaration with its generated class on
    # the declaring component. Two bases that alias the same generated class
    # (``Kwargs = Left.Kwargs``) then compare equal, as they should.
    if isinstance(declaration.value, type) and _is_processed_component(declaration.declaring_class):
        namespace = _static_class_dict(declaration.declaring_class)
        if declaration.name in namespace:
            return namespace[declaration.name]
    return declaration.value


def _describe_binding(declaration: NestedClassDeclaration) -> str:
    owner = _safe_class_text(declaration.declaring_class, "__name__") or "<class>"
    if declaration.value is None:
        return f"{declaration.name} = None on {owner}"
    return f"{owner}.{declaration.name}"


def _same_binding(first: NestedClassDeclaration, second: NestedClassDeclaration) -> bool:
    """Whether two declarations bind the same class, authored or generated."""
    # Two bases may bind one module-level class, which each base converts to
    # its own generated class, or one may alias the other's generated class.
    if first.value is second.value:
        return True
    return _resolved_binding(first) is _resolved_binding(second)


def _require_class_or_none(cls: type, declaration: NestedClassDeclaration) -> None:
    if declaration.value is None or isinstance(declaration.value, type):
        return
    component_name = _safe_class_text(cls, "__name__") or "Component"
    owner = _safe_class_text(declaration.declaring_class, "__name__") or component_name
    name = declaration.name
    msg = (
        f"Component {component_name}: {owner}.{name} must be a class, or None for no {name};"
        f" got {declaration.value!r}. Declare it as `class {name}:` with annotated fields."
    )
    raise ValueError(msg)


def _nearest_data_shape_declaration(cls: type, name: str) -> NestedClassDeclaration | None:
    """
    Return the one data-shape declaration that applies to ``cls``.

    The nearest binding in C3 order applies, exactly like a Python attribute
    lookup. Citry never combines data shapes from separate bases, so when
    two bases that are unrelated to each other each bind a different class
    (or one binds ``None``) and ``cls`` binds none itself, the choice would
    silently depend on base order. That case is a definition-time error.
    """
    declarations = _get_nested_class_declarations(cls, name)
    if not declarations:
        return None
    nearest = declarations[0]
    component_name = _safe_class_text(cls, "__name__") or "Component"
    _require_class_or_none(cls, nearest)
    if nearest.declaring_class is cls:
        return nearest

    # A declaration whose owner is an ancestor of another declaring class is
    # already hidden by that nearer declaration. Only the nearest declaration
    # on each separate branch can compete with the one Python picked.
    declaring_classes = [declaration.declaring_class for declaration in declarations]
    competing = [
        declaration
        for declaration in declarations
        if not any(
            other is not declaration.declaring_class and declaration.declaring_class in _static_class_mro(other)
            for other in declaring_classes
        )
    ]
    for declaration in competing[1:]:
        _require_class_or_none(cls, declaration)
    conflicts = [declaration for declaration in competing[1:] if not _same_binding(declaration, nearest)]
    if conflicts:
        named = [_describe_binding(declaration) for declaration in (nearest, *conflicts)]
        listed = ", ".join(named[:-1]) + f" and {named[-1]}"
        # Every conflict involves at least one class, so suggest the first.
        first_class = next(declaration for declaration in (nearest, *conflicts) if isinstance(declaration.value, type))
        suggestion = f"`{name} = {_describe_binding(first_class)}`"
        msg = (
            f"Component {component_name}: its bases declare {name} differently ({listed}),"
            f" and Citry does not combine them. Declare {name} on {component_name}: write"
            f" {suggestion} to use one of them, or define the fields in module-level classes"
            f" and write `class {name}(FirstFields, SecondFields):`."
        )
        raise ValueError(msg)
    return nearest


def _ancestor_with_same_declaration(cls: type, name: str, nearest: NestedClassDeclaration) -> type | None:
    """
    Return a resolved ancestor that uses the same declaration as ``cls``.

    Its effective class can be reused unchanged, so a subclass that declares
    nothing keeps its parent's class by identity. The search is not limited
    to the declaring class: a library definition or a plain mixin never
    passes through ComponentMeta, while the first component built on it does.
    """
    for ancestor in _static_class_mro(cls)[1:]:
        if not _is_processed_component(ancestor) or name not in _static_class_dict(ancestor):
            continue
        ancestor_declarations = _get_nested_class_declarations(ancestor, name)
        if ancestor_declarations and ancestor_declarations[0] == nearest:
            return ancestor
    return None


def _parent_declaration(cls: type, name: str, nearest: NestedClassDeclaration) -> NestedClassDeclaration | None:
    """Return the declaration the declaring class would have inherited without its own."""
    owner_mro = _static_class_mro(nearest.declaring_class)
    # C3 keeps the owner's own MRO order inside every subclass's MRO, so the
    # first later declaration from one of the owner's bases is its parent's.
    return next(
        (
            declaration
            for declaration in _get_nested_class_declarations(cls, name)
            if declaration.declaring_class is not nearest.declaring_class and declaration.declaring_class in owner_mro
        ),
        None,
    )


def _replaced_parent_schema(
    cls: type, name: str, nearest: NestedClassDeclaration
) -> tuple[NestedClassDeclaration, type] | None:
    """
    Return the parent declaration and class that ``nearest`` replaces.

    Returns ``None`` when the parent has no class to replace, or when the new
    declaration names the parent's class as a base (or aliases it), which
    keeps every parent field.
    """
    parent = _parent_declaration(cls, name, nearest)
    if parent is None or not isinstance(parent.value, type) or not isinstance(nearest.value, type):
        return None
    # Choosing another base's class, as the error for two different base
    # declarations suggests, is a deliberate choice rather than a replacement.
    if any(
        declaration != nearest and _same_binding(declaration, nearest)
        for declaration in _get_nested_class_declarations(cls, name)
    ):
        return None
    parent_schema = _resolved_binding(parent)
    if not isinstance(parent_schema, type):
        return None
    declared_mro = _static_class_mro(nearest.value)
    if parent_schema in declared_mro or parent.value in declared_mro:
        return None
    return parent, parent_schema


def _is_classvar_annotation(annotation: object) -> bool:
    """Whether an annotation declares no instance field: a ClassVar or an InitVar."""
    if annotation is ClassVar or get_origin(annotation) is ClassVar:
        return True
    if annotation is InitVar or isinstance(annotation, InitVar):
        return True
    return isinstance(annotation, str) and annotation.startswith(
        ("ClassVar", "typing.ClassVar", "t.ClassVar", "InitVar", "dataclasses.InitVar")
    )


def _schema_field_names(schema: type) -> tuple[str, ...] | None:
    """Return the field names a schema accepts, or ``None`` for an adapter Citry cannot read."""
    if is_dataclass(schema):
        return tuple(field.name for field in fields(schema))
    model_fields = getattr(schema, "model_fields", None)
    if isinstance(model_fields, dict):
        return tuple(model_fields)
    v1_fields = getattr(schema, "__fields__", None)
    if isinstance(v1_fields, dict):
        return tuple(v1_fields)
    if issubclass(schema, tuple):
        named = getattr(schema, "_fields", None)
        return tuple(named) if isinstance(named, tuple) else None
    if not _is_plain_field_family(schema):
        return None
    # A plain class from a definition base has not been converted yet; its
    # annotations across the MRO are the fields conversion would produce.
    names: dict[str, None] = {}
    for klass in reversed(_static_class_mro(schema)):
        names.update(
            (field_name, None)
            for field_name, annotation in _own_annotations(klass).items()
            if not _is_classvar_annotation(annotation)
        )
    return tuple(names)


def _dropped_field_names(parent_schema: type, schema: object) -> tuple[str, ...]:
    """Return the parent fields that ``schema`` no longer declares, in parent order."""
    if not isinstance(schema, type):
        return ()
    parent_fields = _schema_field_names(parent_schema)
    new_fields = _schema_field_names(schema)
    if parent_fields is None or new_fields is None:
        return ()
    return tuple(field_name for field_name in parent_fields if field_name not in new_fields)


def _quoted_list(names: Iterable[str]) -> str:
    quoted = [repr(name) for name in names]
    if len(quoted) == 1:
        return quoted[0]
    return ", ".join(quoted[:-1]) + f" and {quoted[-1]}"


def _dropped_fields_sentence(
    nearest: NestedClassDeclaration, parent: NestedClassDeclaration, dropped: tuple[str, ...]
) -> str:
    owner = _safe_class_text(nearest.declaring_class, "__name__") or "Component"
    parent_owner = _safe_class_text(parent.declaring_class, "__name__") or "<class>"
    noun = "field" if len(dropped) == 1 else "fields"
    return (
        f"Component {owner}: {nearest.name} replaces {parent_owner}.{nearest.name}"
        f" and leaves out {noun} {_quoted_list(dropped)}."
    )


def _warn_nested_schema_replaced(nearest: NestedClassDeclaration, message: str) -> None:
    """Emit the migration warning once per declaring class, attributed to the user's code."""
    owner = nearest.declaring_class
    warned = _WARNED_REPLACEMENTS.setdefault(owner, set())
    if nearest.name in warned:
        return

    # Point the warning at the first frame outside Citry: the class statement
    # for a component, or the register_library() call for a library.
    warn_at_caller(message, NestedSchemaReplacedWarning)
    # Mark it only once the warning went out: under warnings-as-errors the
    # first definition fails, and a later one must fail the same way.
    warned.add(nearest.name)


def _warn_if_fields_dropped(cls: type, name: str, nearest: NestedClassDeclaration, schema: object) -> None:
    """Warn when a new data-shape declaration leaves out fields of the one it replaces."""
    replaced = _replaced_parent_schema(cls, name, nearest)
    if replaced is None:
        return
    parent, parent_schema = replaced
    dropped = _dropped_field_names(parent_schema, schema)
    if not dropped:
        return
    parent_owner = _safe_class_text(parent.declaring_class, "__name__") or "<class>"
    pronoun = "it" if len(dropped) == 1 else "them"
    message = (
        f"{_dropped_fields_sentence(nearest, parent, dropped)} To keep {pronoun},"
        f" write `class {name}({parent_owner}.{name}):`."
    )
    _warn_nested_schema_replaced(nearest, message)


def _compose_nested_declaration_class(cls: type, name: str) -> type | None:
    """Combine the active settings declarations as bases in component C3 order."""
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


def _is_plain_field_family(declaration: type) -> bool:
    """
    Whether Citry may convert this class into a generated dataclass.

    Dataclasses and plain field classes qualify, including a parent
    component's generated class and module-level field classes named as
    bases. A class that brings its own construction keeps it: classes built
    by another metaclass (Pydantic, TypedDict, ABC, Protocol), NamedTuple and
    other built-in type subclasses, and classes based on a plain class that
    defines a constructor, slots, or a schema protocol attribute such as
    ``model_fields``.
    """
    for klass in _static_class_mro(declaration):
        if klass is object:
            continue
        if type(klass) is not type:
            return False
        # Built-in types such as ``dict`` or ``tuple`` are static types; every
        # class defined in Python code is a heap type.
        flags = _static_class_attribute(klass, "__flags__")
        if type(flags) is not int or not flags & _HEAP_TYPE_FLAG:
            return False
        # A copy: the set check below loops over it, and another thread may
        # store on the class meanwhile.
        namespace = _static_class_namespace_copy(klass)
        if "__dataclass_fields__" in namespace:
            continue
        # The declared class itself is always converted, as an authored nested
        # field class. Only a base can bring its own construction.
        if klass is not declaration and not _CUSTOM_CONSTRUCTION_NAMES.isdisjoint(namespace):
            return False
    return True


def _effective_data_schema(component_class: type, name: str, declared: type, *, use_model_base: bool = True) -> type:
    """Return the runtime class for one class-valued data-shape declaration."""
    component_name = _safe_class_text(component_class, "__name__") or "Component"
    namespace = _static_class_dict(declared)

    # An explicitly decorated dataclass, including an alias of a parent's
    # generated class, keeps its authored options and identity.
    if "__dataclass_fields__" in namespace:
        return declared

    declared_mro = _static_class_mro(declared)
    if tuple in declared_mro and any("_fields" in _static_class_dict(klass) for klass in declared_mro):
        new_fields = [
            field_name
            for field_name, annotation in _own_annotations(declared).items()
            if not _is_classvar_annotation(annotation)
        ]
        if "_fields" not in namespace and new_fields:
            base = next(klass for klass in declared_mro if "_fields" in _static_class_dict(klass))
            base_name = (_safe_class_text(base, "__qualname__") or "NamedTuple").rsplit("<locals>.", 1)[-1]
            noun = "field" if len(new_fields) == 1 else "fields"
            msg = (
                f"Component {component_name}: {name} subclasses the NamedTuple {base_name} and adds"
                f" {noun} {_quoted_list(new_fields)}, but a NamedTuple subclass cannot add fields."
                f" Declare a new NamedTuple that lists every field, or declare {name} as a plain"
                " class with annotated fields."
            )
            raise ValueError(msg)
        return declared

    if not _is_plain_field_family(declared):
        return declared
    model_base = (
        _component_model_base(component_class) if use_model_base and name in _MODEL_BASE_SCHEMA_NAMES else None
    )
    return convert_plain_declaration(declared, owner=component_class, name=name, model_base=model_base)


def _component_model_base(component_class: type) -> ModelBase | None:
    """Return the resolved `model_base` of the Citry instance a component belongs to."""
    engine = _static_class_dict(component_class).get("citry")
    model_base = getattr(engine, "_model_base", None)
    from citry._model_base import ModelBase  # noqa: PLC0415 - avoids importing the settings module early

    return model_base if isinstance(model_base, ModelBase) else None


def convert_plain_declaration(
    user_cls: type,
    *,
    owner: type | None = None,
    name: str | None = None,
    model_base: ModelBase | None = None,
    component_name: str | None = None,
) -> type:
    """
    Generate the class for one plain field declaration, of the kind ``model_base`` names.

    A declaration that already inherits a dataclass, such as a parent
    component's generated class, stays a dataclass: a child follows its
    parent's kind, and the setting decides only when no parent schema exists.

    ``component_name`` names the component in messages when there is no
    ``owner`` class, as for an Events ``data`` class.

    Raises:
        ValueError: The dataclass cannot be generated (see
            `_convert_to_slotted_dataclass`).
        TypeError: The model or named tuple cannot be generated.

    """
    inherits_dataclass = any(
        "__dataclass_fields__" in _static_class_dict(klass) for klass in _static_class_mro(user_cls)
    )
    if (
        model_base is not None
        and model_base.kind == "dataclass"
        and (not inherits_dataclass or issubclass(user_cls, model_base.base))
    ):
        # A child of a class generated from the base keeps the base's options;
        # a class that inherits another dataclass keeps that one's.
        return _convert_to_slotted_dataclass(user_cls, owner=owner, name=name, model_base=model_base)
    if model_base is None or inherits_dataclass:
        return _convert_to_slotted_dataclass(user_cls, owner=owner, name=name)

    from citry._input_types import _UNRESOLVED, _resolve_annotation  # noqa: PLC0415 - imports component modules
    from citry._model_base import BuildInput, build_named_tuple, build_pydantic_model  # noqa: PLC0415
    from citry.constness import _plain_schema_default  # noqa: PLC0415 - constness imports component modules

    annotations: dict[str, Any] = {}
    field_owners: dict[str, type] = {}
    for klass in reversed(_static_class_mro(user_cls)):
        own_annotations = _own_annotations(klass)
        annotations.update(own_annotations)
        field_owners.update((field_name, klass) for field_name in own_annotations)
    # The generated class lives in the component's module, so each name is
    # read now in the module of the class that wrote it. A name that cannot
    # be read yet stays text, for the model to read when it is first used.
    hints_by_owner: dict[type, dict[str, object] | None] = {}
    for field_name, annotation in annotations.items():
        resolved = _resolve_annotation(field_name, annotation, field_owners[field_name], hints_by_owner)
        if resolved is not _UNRESOLVED:
            annotations[field_name] = resolved
    module, qualname = _generated_names(user_cls, owner, name)
    owner_name = _safe_class_text(owner, "__name__") if owner is not None else component_name
    build = BuildInput(
        user_cls=user_cls,
        component_name=owner_name,
        schema_name=name or _safe_class_text(user_cls, "__name__") or "Schema",
        annotations=annotations,
        field_owners=field_owners,
        field_names=tuple(
            field_name for field_name, annotation in annotations.items() if not _is_classvar_annotation(annotation)
        ),
        module=module,
        qualname=qualname,
        class_name=_safe_class_text(user_cls, "__name__") or "Schema",
    )
    if model_base.kind == "namedtuple":
        generated, const_defaults = build_named_tuple(build, _plain_schema_default)
        if const_defaults:
            type.__setattr__(generated, _CONST_SCHEMA_DEFAULTS_ATTR, const_defaults)
    else:
        generated = build_pydantic_model(build, model_base)
    # Set after creation: Pydantic turns an underscore name in a class body
    # into a private attribute, which would hide these markers.
    type.__setattr__(generated, _SYNTHESIZED_DECLARATION_ATTR, True)
    type.__setattr__(generated, _SYNTHESIZED_FIELD_OWNERS_ATTR, tuple(field_owners.items()))
    return generated


def _generated_names(user_cls: type, owner: type | None, name: str | None) -> tuple[str, str]:
    """Return the module and qualified name a generated class reports."""
    provenance_class = user_cls if owner is None else owner
    module = _static_class_attribute(provenance_class, "__module__")
    qualname = _static_class_attribute(provenance_class, "__qualname__")
    if owner is not None and isinstance(qualname, str):
        qualname = f"{qualname}.{name or _safe_class_text(user_cls, '__name__') or 'Schema'}"
    return (
        module if isinstance(module, str) else "citry.component",
        qualname if isinstance(qualname, str) else _safe_class_text(user_cls, "__name__") or "Schema",
    )


def _inherited_default(user_cls: type, field_name: str) -> object:
    """
    Return the authored default a field inherits, following the class MRO.

    Generated classes are skipped: their slots hide the default behind a
    slot descriptor, and the authored class they were generated from comes
    right after them in the MRO with the original value (including a
    ``Const`` marker or a ``field(...)`` specifier).
    """
    for klass in _static_class_mro(user_cls):
        namespace = _static_class_dict(klass)
        if namespace.get(_SYNTHESIZED_DECLARATION_ATTR, False) is True:
            continue
        dataclass_fields = namespace.get("__dataclass_fields__")
        if isinstance(dataclass_fields, dict) and field_name in dataclass_fields:
            declared_field = dataclass_fields[field_name]
            if declared_field.default is MISSING and declared_field.default_factory is MISSING:
                return MISSING
            return declared_field
        if field_name in namespace:
            value = namespace[field_name]
            # A user-slotted class stores a slot descriptor, not a default.
            if type(value).__name__ == "member_descriptor":
                return MISSING
            return value
    return MISSING


def _dataclass_base_frozen_flags(user_cls: type) -> dict[type, bool]:
    """Return each dataclass in the MRO with its frozen flag, in MRO order."""
    flags: dict[type, bool] = {}
    for klass in _static_class_mro(user_cls):
        params = _static_class_dict(klass).get("__dataclass_params__")
        if params is not None:
            flags[klass] = bool(getattr(params, "frozen", False))
    return flags


def _convert_to_slotted_dataclass(
    user_cls: type,
    *,
    owner: type | None = None,
    name: str | None = None,
    model_base: ModelBase | None = None,
) -> type:
    """
    Generate one slotted dataclass from an authored plain field class.

    Fields that a dataclass base already declares (such as a parent
    component's generated class named as a base) come from that base with
    their defaults. The authored class's own annotations, and those of its
    plain bases, become the new fields. The generated class is frozen when
    its dataclass bases are frozen.

    With a dataclass ``model_base``, the generated class also subclasses
    the base, and takes its dataclass options.

    Raises:
        ValueError: The dataclass bases mix frozen and non-frozen, so no
            generated class can inherit from all of them, or the dataclass
            cannot be generated for another reason.

    """
    from citry._model_base import dataclass_options  # noqa: PLC0415 - avoids importing settings early

    # The base sits after the authored class, so the authored class's own
    # members still win; the base's fields come first in field order.
    extra_bases: tuple[type, ...] = (
        (model_base.base,) if model_base is not None and not issubclass(user_cls, model_base.base) else ()
    )
    options = dataclass_options(model_base) if model_base is not None else {}
    # Plain classes that a dataclass base already covers reach the new class
    # through dataclass inheritance with their defaults intact. Collecting
    # their annotations again would redeclare those fields without defaults.
    covered: set[type] = set()
    for klass in _static_class_mro(user_cls):
        if "__dataclass_fields__" in _static_class_dict(klass):
            covered.update(_static_class_mro(klass))

    annotations: dict[str, Any] = {}
    field_owners: dict[str, type] = {}
    for klass in reversed(_static_class_mro(user_cls)):
        if klass in covered:
            continue
        own_annotations = _own_annotations(klass)
        annotations.update(own_annotations)
        # The generated dataclass owns the merged annotation mapping, so keep
        # the authored owner beside it for catalog and editor navigation.
        field_owners.update((field_name, klass) for field_name in own_annotations)

    provenance_class = user_cls if owner is None else owner
    module = _static_class_attribute(provenance_class, "__module__")
    qualname = _static_class_attribute(provenance_class, "__qualname__")
    if owner is not None and isinstance(qualname, str):
        qualname = f"{qualname}.{name or _safe_class_text(user_cls, '__name__') or 'Schema'}"

    # Const markers on inherited defaults stay declared unless this class
    # gives the field a new default.
    inherited_consts = getattr(user_cls, _CONST_SCHEMA_DEFAULTS_ATTR, None)
    const_defaults: dict[str, Any] = dict(inherited_consts) if isinstance(inherited_consts, dict) else {}
    shell_namespace: dict[str, Any] = {
        "__annotations__": annotations,
        "__module__": module if isinstance(module, str) else "citry.component",
        "__qualname__": qualname if isinstance(qualname, str) else _safe_class_text(user_cls, "__name__"),
        # Tooling must attribute effective fields to their authored bases, not
        # to this implementation-only class that copies the merged annotations.
        _SYNTHESIZED_DECLARATION_ATTR: True,
        _SYNTHESIZED_FIELD_OWNERS_ATTR: tuple(field_owners.items()),
    }
    from citry.constness import (  # noqa: PLC0415 - declaration conversion precedes component import completion
        _plain_schema_default,
        _schema_default_factory,
        is_const,
    )

    for field_name in annotations:
        const_defaults.pop(field_name, None)
        default = _inherited_default(user_cls, field_name)
        if isinstance(default, Field):
            # dataclass() deletes an authored ``field(...)`` marker after it
            # consumes it, so the generated shell needs its own reference.
            copied_default = copy(default)
            if default.default is not MISSING:
                if is_const(default.default):
                    const_defaults[field_name] = _plain_schema_default(default.default)
                copied_default.default = _plain_schema_default(default.default)
            if default.default_factory is not MISSING and not default.init:
                copied_default.default_factory = _schema_default_factory(field_name, default.default_factory)
            shell_namespace[field_name] = copied_default
        elif default is not MISSING:
            if is_const(default):
                const_defaults[field_name] = _plain_schema_default(default)
            shell_namespace[field_name] = _plain_schema_default(default)
    if const_defaults or inherited_consts:
        shell_namespace[_CONST_SCHEMA_DEFAULTS_ATTR] = const_defaults

    base_flags = _dataclass_base_frozen_flags(user_cls)
    for extra_base in extra_bases:
        base_flags.update(_dataclass_base_frozen_flags(extra_base))
    # Python 3.13 and later reject a frozen dataclass over a non-frozen
    # dataclass base, and 3.10 to 3.12 accept one, so check the bases here and
    # fail the same way on every version.
    if len(set(base_flags.values())) > 1:
        raise _mixed_frozen_error(owner, name, user_cls, base_flags)
    frozen = all(base_flags.values()) and bool(base_flags)
    class_name = _safe_class_text(user_cls, "__name__") or "Schema"

    def generate(*, kw_only: bool) -> type:
        # Field() markers are consumed by dataclass(), so each attempt starts
        # from fresh copies of them.
        namespace = {key: copy(value) if isinstance(value, Field) else value for key, value in shell_namespace.items()}
        shell = new_class(class_name, (user_cls, *extra_bases), exec_body=lambda attrs: attrs.update(namespace))
        # ``types.new_class`` may leave ``__qualname__`` inherited when its value
        # matches a base. Dataclass's slots rebuild copies only own attributes.
        type.__setattr__(shell, "__qualname__", namespace["__qualname__"])
        chosen = {**options, "frozen": frozen, "kw_only": kw_only or options.get("kw_only", False)}
        return dataclass(slots=True, **chosen)(shell)

    try:
        return generate(kw_only=False)
    except TypeError as error:
        if "follows default argument" not in str(error) and "non-default argument" not in str(error):
            raise _conversion_error(owner, name, user_cls, error) from error
    # Citry passes inputs by name, so a required field may follow one with a
    # default. Keyword-only fields express that order without changing names.
    try:
        return generate(kw_only=True)
    except TypeError as error:
        raise _conversion_error(owner, name, user_cls, error) from error


def _error_prefix(owner: type | None, name: str | None, user_cls: type) -> tuple[str, str]:
    """Name the component and declaration that an error message refers to."""
    component_name = _safe_class_text(owner, "__name__") if owner is not None else None
    declaration = name or _safe_class_text(user_cls, "__name__") or "Schema"
    prefix = f"Component {component_name}: " if component_name else ""
    return prefix, declaration


def _mixed_frozen_error(
    owner: type | None,
    name: str | None,
    user_cls: type,
    base_flags: dict[type, bool],
) -> ValueError:
    prefix, declaration = _error_prefix(owner, name, user_cls)
    # Name one base of each kind so the author knows which classes to change.
    frozen_base = next(klass for klass, frozen in base_flags.items() if frozen)
    mutable_base = next(klass for klass, frozen in base_flags.items() if not frozen)
    frozen_name = _safe_class_text(frozen_base, "__name__") or "a base"
    mutable_name = _safe_class_text(mutable_base, "__name__") or "another base"
    return ValueError(
        f"{prefix}{declaration} cannot mix frozen and non-frozen dataclass bases:"
        f" {frozen_name} is frozen and {mutable_name} is not."
        " Make every dataclass base frozen, or none of them."
    )


def _conversion_error(owner: type | None, name: str | None, user_cls: type, error: TypeError) -> ValueError:
    prefix, declaration = _error_prefix(owner, name, user_cls)
    return ValueError(f"{prefix}could not generate a dataclass for {declaration}: {error}.")


__all__ = ["NestedSchemaReplacedWarning"]
