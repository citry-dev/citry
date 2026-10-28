"""
State handling for the ``events`` extension.

A component's ``class State:`` declares exactly what round-trips between the
browser and the event handlers. This module owns its class-side treatment:
the dataclass conversion (the same treatment the core gives ``Kwargs``,
applied here so the core stays unaware of State), the underscore meta
(``_public``, ``_model``, ``_storage``, ``_max_bytes``, ``_max_age``), and
the render-time derivation that builds the State instance from a component's
kwargs. Design: ``docs/design/events.md`` sections 3.2 and 7.2.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import MISSING, dataclass, fields
from datetime import timedelta
from typing import Any, cast, get_args
from weakref import WeakKeyDictionary

from citry._annotation_introspection import _own_annotations
from citry._class_introspection import _safe_class_text, _static_class_namespace_copy
from citry._input_types import _CHECKS_ATTR
from citry._model_base import ModelBase, dataclass_options
from citry._nested_declarations import (
    _CONST_SCHEMA_DEFAULTS_ATTR,
    _SYNTHESIZED_DECLARATION_ATTR,
    _SYNTHESIZED_FIELD_OWNERS_ATTR,
    NestedClassDeclaration,
    _dropped_field_names,
    _dropped_fields_sentence,
    _replaced_parent_schema,
    _warn_nested_schema_replaced,
    convert_plain_declaration,
)

# A setting read with this default was not set.
_UNSET = object()


def _pydantic_supports(method: str, parameter: str) -> bool:
    """Whether the installed Pydantic v2 ``BaseModel.<method>`` takes ``parameter``."""
    try:
        from pydantic import BaseModel  # noqa: PLC0415 - Pydantic is optional
    except ImportError:
        return False
    return parameter in inspect.signature(getattr(BaseModel, method)).parameters


# Pydantic 2.11 reads keys by field name only, and 2.12 leaves computed
# fields out of a dump; older releases get the closest equivalent.
_VALIDATES_BY_NAME = _pydantic_supports("model_validate_json", "by_name")
_DUMP_EXCLUDES_COMPUTED = _pydantic_supports("model_dump", "exclude_computed_fields")


# Names Python's ABC machinery writes on a model class itself.
_MODEL_CLASS_NAMES = frozenset({"_abc_impl"})
# The full State meta surface. Every other underscore attribute on a State
# class is a class-definition error, which is what makes typos loud
# (``_pubic = (...)`` fails instead of silently doing nothing).
STATE_META_NAMES = ("_public", "_model", "_storage", "_max_bytes", "_max_age")

_STORAGE_VALUES = ("signed", "server")
_DEFAULT_MAX_BYTES = 8192

# Descriptor-shaped values (methods and friends) are allowed under any
# underscore name: State may carry private helpers just like it carries the
# recommended ``render()`` method. Plain values are what must be meta names.
_DEF_LIKE = (staticmethod, classmethod, property)
# Names Citry writes on a State class itself: the generated schema's
# construction metadata, and the input type checks a render stores on it the
# first time it checks a State value.
_SYNTHESIZED_STATE_NAMES = frozenset(
    {_SYNTHESIZED_DECLARATION_ATTR, _SYNTHESIZED_FIELD_OWNERS_ATTR, _CONST_SCHEMA_DEFAULTS_ATTR, _CHECKS_ATTR}
)


@dataclass(frozen=True, slots=True)
class StateMeta:
    """
    The resolved State meta of one component: visibility, writability, storage.

    Attributes:
        public: The fields templates and client bindings may touch; the only
            fields whose plain values ship client-side. Defaults to all
            fields.
        model: The public fields the client may write (two-way bindings);
            always a subset of ``public``. Defaults to the same fields as
            ``public``.
        storage: Where the round-trip State lives: ``"signed"`` (in the
            client token) or ``"server"``.
        max_bytes: Mint-time cap on the serialized State, in bytes.
        max_age: Optional token expiry; ``None`` means tokens do not expire.

    """

    public: tuple[str, ...]
    model: tuple[str, ...]
    storage: str
    max_bytes: int
    max_age: timedelta | None


# The field names of each State class, read once: a dataclass's fields, or a
# Pydantic model's. Every function that reads State fields calls these, so
# dataclass and model State share one code path.
_FIELD_NAMES: WeakKeyDictionary[type, tuple[str, ...]] = WeakKeyDictionary()
_REQUIRED_NAMES: WeakKeyDictionary[type, frozenset[str]] = WeakKeyDictionary()


def state_model_kind(state_cls: type) -> str | None:
    """Return ``"v2"`` or ``"v1"`` for a Pydantic model State, or ``None`` for a dataclass."""
    if isinstance(getattr(state_cls, "model_fields", None), dict) and hasattr(state_cls, "__pydantic_validator__"):
        return "v2"
    if isinstance(getattr(state_cls, "__fields__", None), dict) and hasattr(state_cls, "__config__"):
        return "v1"
    return None


def _model_fields(state_cls: type) -> dict[str, Any]:
    kind = state_model_kind(state_cls)
    if kind == "v2":
        return cast("dict[str, Any]", state_cls.model_fields)  # type: ignore[attr-defined]
    return cast("dict[str, Any]", state_cls.__fields__)  # type: ignore[attr-defined]


def state_field_names(state_cls: type) -> tuple[str, ...]:
    """Return a State class's field names, in declaration order."""
    names = _FIELD_NAMES.get(state_cls)
    if names is None:
        names = (
            tuple(_model_fields(state_cls))
            if state_model_kind(state_cls)
            else tuple(f.name for f in fields(state_cls))
        )
        _FIELD_NAMES[state_cls] = names
    return names


def _required_field_names(state_cls: type) -> frozenset[str]:
    """Return the State fields that have no default, which a build must pass."""
    required = _REQUIRED_NAMES.get(state_cls)
    if required is None:
        kind = state_model_kind(state_cls)
        if kind == "v2":
            required = frozenset(name for name, info in _model_fields(state_cls).items() if info.is_required())
        elif kind == "v1":
            required = frozenset(name for name, info in _model_fields(state_cls).items() if info.required)
        else:
            required = frozenset(
                f.name for f in fields(state_cls) if f.default is MISSING and f.default_factory is MISSING
            )
        _REQUIRED_NAMES[state_cls] = required
    return required


def state_values(state: Any) -> dict[str, Any]:
    """Return a State instance's field values by name, for any State kind."""
    return {name: getattr(state, name) for name in state_field_names(type(state))}


def state_wire_values(state: Any) -> dict[str, Any]:
    """
    Return the State field values as the token stores them.

    A model State can hold nested models, dates and other values Pydantic
    writes as JSON, so Pydantic writes them as JSON here, by field name and
    in the form it reads back (``round_trip``), and `restore_state` reads
    that JSON back into their types. Computed fields are left out. A
    dataclass State's values are used as they are, and the token checks they
    are plain JSON.
    """
    kind = state_model_kind(type(state))
    if kind == "v2":
        options: dict[str, Any] = {"mode": "json", "by_alias": False, "round_trip": True, "warnings": False}
        if _DUMP_EXCLUDES_COMPUTED:
            options["exclude_computed_fields"] = True
        else:
            options["include"] = set(state_field_names(type(state)))
        return cast("dict[str, Any]", state.model_dump(**options))
    if kind == "v1":
        # Pydantic v1 writes a nested model with the fields of its runtime
        # class, which may be a subclass State does not declare. Reading the
        # JSON back through the State class keeps only declared fields.
        declared = type(state).parse_raw(state.json())
        return cast("dict[str, Any]", json.loads(declared.json()))
    return state_values(state)


def state_setting(state_cls: type, name: str, default: Any = None) -> Any:
    """
    Read a State setting such as ``_storage``, also from a Pydantic model.

    Pydantic v2 (and v1 with ``underscore_attrs_are_private``) keeps an
    underscore name in a model's body as a private attribute, so reading it
    as a class attribute returns Pydantic's wrapper, not the value.
    """
    private = getattr(state_cls, "__private_attributes__", None)
    if isinstance(private, dict) and name in private:
        value = getattr(private[name], "default", default)
        # Pydantic marks a private attribute without a default with its own
        # undefined object, which is not a setting value.
        return default if type(value).__name__ in {"PydanticUndefinedType", "UndefinedType"} else value
    return getattr(state_cls, name, default)


def has_state_setting(state_cls: type, name: str) -> bool:
    """Whether a State class sets a State setting, also as a Pydantic private attribute."""
    private = getattr(state_cls, "__private_attributes__", None)
    return (isinstance(private, dict) and name in private) or hasattr(state_cls, name)


def _model_frozen(state_cls: type) -> str | None:
    """Return the setting that freezes a Pydantic model State, or ``None``."""
    kind = state_model_kind(state_cls)
    if kind == "v2":
        config = getattr(state_cls, "model_config", {})
        return "model_config['frozen']" if config.get("frozen") else None
    if kind == "v1":
        config = state_cls.__config__  # type: ignore[attr-defined]
        if getattr(config, "frozen", False):
            return "Config.frozen"
        if getattr(config, "allow_mutation", True) is False:
            return "Config.allow_mutation = False"
    return None


def restore_state(state_cls: type, values: dict[str, Any]) -> Any:
    """
    Build State from the values a verified token carried.

    A model State reads them as JSON, the form the token stores, so a date,
    an enum, or a tuple that JSON wrote as a list is checked back into its
    type even under ``strict=True``. Keys are read as field names only, so
    an alias, which another field could share, never fills a field.

    Raises:
        TypeError: The values no longer fit a dataclass State.
        ValueError: The values no longer validate for a model State
            (Pydantic's ``ValidationError`` is a ``ValueError``).

    """
    kind = state_model_kind(state_cls)
    if kind is None:
        return state_cls(**values)
    text = json.dumps(values, allow_nan=False)
    if kind == "v2":
        if _VALIDATES_BY_NAME:
            return state_cls.model_validate_json(text, by_alias=False, by_name=True)  # type: ignore[attr-defined]
        return state_cls.model_validate_json(text)  # type: ignore[attr-defined]
    return state_cls.parse_raw(text)  # type: ignore[attr-defined]


def check_changed_state(state: Any) -> tuple[str | None, str] | None:
    """
    Check that a changed model State can be signed and restored again, and adopt Pydantic's values.

    A handler's ``state.count = ...`` or ``state.items.append(...)`` is not
    validated by Pydantic unless the model sets ``validate_assignment=True``,
    and an in-place change never is. So the values the token will carry are
    restored here, and the State takes the restored values, so a value
    Pydantic converts (``"2"`` for an ``int``) is signed converted. The
    restored values must then survive a second round trip unchanged.
    Returns ``(field, message)`` for the first problem, or ``None`` when the
    State can be signed or is a dataclass.
    """
    state_cls = type(state)
    if state_model_kind(state_cls) is None:
        return None
    try:
        restored = restore_state(state_cls, state_wire_values(state))
        again = restore_state(state_cls, state_wire_values(restored))
    except ValueError as error:
        return _first_error(error)
    except (TypeError, UnicodeDecodeError) as error:
        return None, f"a value could not be written as JSON ({type(error).__name__})"
    # Models compare their field values, so a set in another order is the
    # same value; a value Pydantic writes as JSON that reads back as another
    # value is not.
    changed = next(
        (name for name in state_field_names(state_cls) if getattr(restored, name) != getattr(again, name)), None
    )
    if changed is not None:
        return changed, "the value Pydantic writes as JSON does not read back as the same value"
    _adopt(state, restored)
    return None


def _adopt(state: Any, source: Any) -> None:
    """Give a model State another instance's field values, without assignment validation, which already ran."""
    state.__dict__.update({name: source.__dict__[name] for name in state_field_names(type(state))})


def _first_error(error: ValueError) -> tuple[str | None, str]:
    """Return the field and message of a Pydantic error, without the input value, which may be private."""
    errors = getattr(error, "errors", None)
    found: list[Any] = []
    if callable(errors):
        try:
            found = list(errors(include_input=False))
        except TypeError:
            found = list(errors())
    if not found:
        return None, type(error).__name__
    first = found[0]
    location = tuple(first.get("loc", ()))
    path = ".".join(str(part) for part in location)
    return (str(location[0]) if location else None), f"{path}: {first.get('msg', 'invalid value')}"


def _check_model_state(comp_name: str, state_cls: type) -> None:
    """
    Reject a Pydantic model State that Citry could not store and restore.

    Citry assigns to State, writes its declared fields as JSON into the
    token by field name, and reads them back the same way. A frozen model or
    field, a field the dump leaves out or reshapes (``exclude``,
    ``exclude_if``, a serializer), or a secret type (which Pydantic writes
    masked) would lose or break State, at any depth of nested models.

    Raises:
        ValueError: The model has one of these, naming the field or setting.

    """
    prefix = f"Component {comp_name}: State"
    frozen = _model_frozen(state_cls)
    if frozen is not None:
        msg = (
            f"{prefix} is a frozen Pydantic model ({frozen}). State must stay mutable (handlers change it and"
            " the changes travel back to the browser); remove that setting."
        )
        raise ValueError(msg)
    for model, path in _models_in(state_cls, "State"):
        problem = _model_problem(model, top=model is state_cls)
        if problem is not None:
            msg = f"Component {comp_name}: {path}{problem}"
            raise ValueError(msg)


def _models_in(model: type, path: str, seen: set[type] | None = None) -> list[tuple[type, str]]:
    """Return a model and every model its fields hold, at any depth, with the path to each."""
    seen = set() if seen is None else seen
    if model in seen:
        return []
    seen.add(model)
    found: list[tuple[type, str]] = [(model, path)]
    for name, info in _model_fields(model).items():
        annotation = getattr(info, "annotation", None) or getattr(info, "outer_type_", None)
        for nested in _annotation_types(annotation):
            if state_model_kind(nested) is not None:
                found.extend(_models_in(nested, f"{path}.{name}", seen))
    return found


def _annotation_types(annotation: Any) -> list[Any]:
    """Return every type an annotation names, through unions, containers and ``Annotated``."""
    found = [annotation]
    for argument in get_args(annotation):
        found.extend(_annotation_types(argument))
    return found


def _model_problem(model: type, *, top: bool) -> str | None:
    """Return what makes one model unusable in State, or ``None``; the message starts after its path."""
    kind = state_model_kind(model)
    decorators = getattr(model, "__pydantic_decorators__", None)
    if kind == "v2" and (
        getattr(decorators, "model_serializers", None) or getattr(decorators, "field_serializers", None)
    ):
        return (
            " defines a serializer, which changes the JSON Citry stores in the page so it may not read back."
            " Remove it, or keep State to plain fields."
        )
    # Restoring by field name ignores aliases on recent Pydantic; older v2
    # releases and v1 need the model to accept field names.
    by_name = kind == "v2" and _VALIDATES_BY_NAME
    by_name = by_name or _populates_by_name(model)
    for name, info in _model_fields(model).items():
        problem = _field_problem(kind, name, info, by_name=by_name)
        if problem is not None:
            return f".{name} {problem}"
    del top
    return None


def _populates_by_name(model: type) -> bool:
    """Whether a model accepts an aliased field by its own name."""
    if state_model_kind(model) == "v2":
        config = getattr(model, "model_config", {})
        return bool(config.get("populate_by_name") or config.get("validate_by_name"))
    return bool(getattr(model.__config__, "allow_population_by_field_name", False))  # type: ignore[attr-defined]


def _field_problem(kind: str | None, name: str, info: Any, *, by_name: bool) -> str | None:
    """Return what makes one model field unusable in State, or ``None``."""
    field_info = info if kind == "v2" else getattr(info, "field_info", info)
    aliases = {getattr(info, "alias", None), getattr(field_info, "validation_alias", None)}
    if any(alias not in (None, name) for alias in aliases) and not by_name:
        return (
            "has an alias, but Citry stores State by field name. Set populate_by_name=True"
            " (allow_population_by_field_name in Pydantic v1), or remove the alias."
        )
    if getattr(field_info, "frozen", None) or getattr(field_info, "allow_mutation", True) is False:
        return "is frozen, but handlers change State. Remove frozen=True from the field."
    if getattr(field_info, "exclude", None) or getattr(field_info, "exclude_if", None):
        return "is left out of the model's dump (exclude), so it would be lost between calls. Remove it."
    annotation = getattr(info, "annotation", None) or getattr(info, "outer_type_", None)
    metadata = list(getattr(field_info, "metadata", None) or ())
    for argument in _annotation_types(annotation):
        metadata.extend(getattr(argument, "__metadata__", ()))
    if any(type(item).__name__ in {"PlainSerializer", "WrapSerializer"} for item in metadata):
        return "has a serializer, so its JSON may not read back as the same value. Remove the serializer."
    if any(_is_secret_type(argument) for argument in _annotation_types(annotation)):
        return (
            "holds a secret type, which Pydantic writes masked, so its value would be lost between calls. Keep"
            " secrets out of State; store an id and load the secret in the handler."
        )
    return None


def _is_secret_type(value: Any) -> bool:
    """Whether a type is one of Pydantic's secret types (v2 or v1), which dump masked."""
    if not isinstance(value, type):
        return False
    return any(
        klass.__name__ in {"SecretStr", "SecretBytes", "Secret"} and (klass.__module__ or "").startswith("pydantic")
        for klass in value.__mro__
    )


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _merged_annotations(user_cls: type) -> dict[str, Any]:
    """
    The annotated names of ``user_cls`` including inherited declarations.

    Walks the MRO base-first so a redeclared name keeps its base position
    (the same ordering ``dataclass`` inheritance produces). Classes that were
    decorated as dataclasses themselves are skipped: their fields reach the
    conversion through ``__dataclass_fields__``, and re-collecting their
    annotations here would drop ``field(default_factory=...)`` defaults.
    """
    merged: dict[str, Any] = {}
    for klass in reversed(user_cls.__mro__):
        if "__dataclass_fields__" not in klass.__dict__:
            merged.update(_own_annotations(klass))
    return merged


def validate_state_class(comp_name: str, user_cls: type) -> None:
    """
    Reject State declarations that break the wire contract, at class definition.

    Two rules: fields cannot start with an underscore, and an underscore
    attribute that is not a method must be one of the recognized meta names.
    Field names come from the annotations across the MRO plus any
    dataclass-declared fields, so a State the user decorated with
    ``@dataclass`` (or based on one), which the conversion keeps as-is,
    obeys the same wire contract as a plain declaration.
    """
    dataclass_fields: dict[str, Any] = getattr(user_cls, "__dataclass_fields__", {})
    # `BaseModel` annotates Pydantic's internal names, so a model State's
    # fields are read from Pydantic, not from the class annotations.
    declared = (
        state_field_names(user_cls)
        if state_model_kind(user_cls) is not None
        else (*dataclass_fields, *_merged_annotations(user_cls))
    )
    for field_name in declared:
        if field_name.startswith("_"):
            msg = (
                f"Component {comp_name}: State declares field {field_name!r}. State fields cannot"
                f" start with an underscore (fields are the wire contract); underscore names are"
                f" reserved for the State meta: {', '.join(STATE_META_NAMES)}."
            )
            raise ValueError(msg)
    # Pydantic removes a private attribute from the class body, so a typo
    # such as `_strorage` is found only in its private attributes.
    private = getattr(user_cls, "__private_attributes__", None)
    for name in private if isinstance(private, dict) else ():
        if name in STATE_META_NAMES and state_setting(user_cls, name, _UNSET) is _UNSET:
            msg = (
                f"Component {comp_name}: State declares the setting {name!r} without a value. Give it one,"
                f" such as {name} = ..., or remove it."
            )
            raise ValueError(msg)
        if name not in STATE_META_NAMES:
            msg = (
                f"Component {comp_name}: {name!r} is not a recognized State meta attribute."
                f" Underscore names on State are reserved for the meta:"
                f" {', '.join(STATE_META_NAMES)}."
            )
            raise ValueError(msg)
    # Pydantic v1 keeps a setting that is only annotated, such as
    # `_storage: str`, out of the class, so it would silently be unset.
    if state_model_kind(user_cls) is not None:
        for name in _merged_annotations(user_cls):
            if name in STATE_META_NAMES and not has_state_setting(user_cls, name):
                msg = (
                    f"Component {comp_name}: State declares the setting {name!r} without a value. Give it one,"
                    f" such as {name} = ..., or remove it."
                )
                raise ValueError(msg)
    for klass in user_cls.__mro__:
        # Pydantic's own base classes carry its private helpers.
        module = getattr(klass, "__module__", "") or ""
        if klass is object or module == "pydantic" or module.startswith("pydantic."):
            continue
        # A render on another thread can be checking a value of a parent's
        # State and store its input checks on that class while this loop
        # runs, so the loop walks a copy. The stored checks are skipped by
        # name below.
        for name, value in _static_class_namespace_copy(klass).items():
            if _is_dunder(name) or not name.startswith("_"):
                continue
            # Citry's generated schema carries private construction metadata,
            # and a render stores its input checks on the class; only
            # author-written underscore values belong to the State meta.
            if name in _SYNTHESIZED_STATE_NAMES or name in _MODEL_CLASS_NAMES:
                continue
            if inspect.isfunction(value) or isinstance(value, _DEF_LIKE):
                continue  # a private helper method; State may carry methods
            if name not in STATE_META_NAMES:
                msg = (
                    f"Component {comp_name}: {name!r} is not a recognized State meta attribute."
                    f" Underscore names on State are reserved for the meta:"
                    f" {', '.join(STATE_META_NAMES)}."
                )
                raise ValueError(msg)


def convert_state_class(comp_name: str, user_cls: type, model_base: ModelBase | None = None) -> type:
    """
    Return the mutable State class Citry uses: a dataclass, or a Pydantic model.

    Mirrors the treatment the core gives ``Kwargs``: a plain class converts
    to a slotted dataclass, a class the user already decorated with
    ``@dataclass`` is kept as-is (but must not be frozen, because handlers
    mutate state). A State with base classes, such as
    ``class State(Parent.State):`` or ``class State(Kwargs):``, keeps the
    fields and defaults of those bases.

    The class the user wrote is never modified. The generated dataclass
    inherits the authored declaration, preserving methods, descriptors,
    zero-argument ``super()``, and source identity in its MRO.

    A Pydantic v2 or v1 model State written by hand is kept too. With
    ``model_base`` (the setting), a plain State becomes a dataclass with a
    dataclass base's options, or a model that subclasses a Pydantic base. A
    NamedTuple base, a frozen dataclass base, and a frozen model are errors,
    because Citry assigns to State.

    Raises:
        ValueError: State is frozen, or ``model_base`` names a kind Citry
            cannot assign to.

    """
    frozen_msg = (
        f"Component {comp_name}: State is a frozen dataclass. State must stay mutable"
        f" (handlers mutate it and the changes travel back to the client);"
        f" declare it without frozen=True."
    )
    if "__dataclass_fields__" in user_cls.__dict__:
        # The user decorated the class explicitly; respect their choices,
        # except immutability, which contradicts the State contract.
        if user_cls.__dataclass_params__.frozen:  # type: ignore[attr-defined]
            raise ValueError(frozen_msg)
        return user_cls
    # A Pydantic model State written by hand is kept, as long as Citry can
    # assign to it.
    if state_model_kind(user_cls) is not None:
        _check_model_state(comp_name, user_cls)
        return user_cls
    # `class State(Parent.State):` keeps its parent's dataclass, as any child
    # schema keeps its parent's kind, so the setting's kind does not apply.
    if any("__dataclass_fields__" in klass.__dict__ for klass in user_cls.__mro__):
        model_base = model_base if model_base is not None and model_base.kind == "dataclass" else None
        if model_base is not None and dataclass_options(model_base).get("frozen"):
            model_base = None
    if model_base is not None and model_base.kind == "namedtuple":
        msg = (
            f"Component {comp_name}: State cannot be generated as a NamedTuple, because Citry assigns to State."
            " Decorate State with @dataclass to keep it a dataclass, or set model_base to a Pydantic model or a"
            " dataclass that is not frozen."
        )
        raise ValueError(msg)
    if model_base is not None and model_base.kind == "dataclass" and dataclass_options(model_base).get("frozen"):
        msg = (
            f"Component {comp_name}: State cannot be generated from the frozen dataclass model_base"
            f" {model_base.base.__qualname__}, because Citry assigns to State. Decorate State with @dataclass to"
            " keep it a mutable dataclass, or set model_base to a Pydantic model or a dataclass that is not frozen."
        )
        raise ValueError(msg)
    converted = convert_plain_declaration(user_cls, model_base=model_base, component_name=comp_name, name="State")
    if state_model_kind(converted) is not None:
        # The setting's model may itself be frozen.
        _check_model_state(comp_name, converted)
        return converted
    # A plain State based on a frozen dataclass inherits the frozen flag.
    if converted.__dataclass_params__.frozen:  # type: ignore[attr-defined]
        raise ValueError(frozen_msg)
    return converted


def check_replaced_state(component_class: type, nearest: NestedClassDeclaration, state_cls: type) -> None:
    """
    Check a State that replaces its parent's State instead of extending it.

    A replacing State starts from the default settings, not the parent's.
    Moving server-kept values into the page is a security change, so it
    fails at class definition unless the new State sets ``_storage`` itself.
    Losing the parent's fields, ``_public``, ``_model``, or ``_max_age`` is
    less severe, so it only warns, once per declaring class.

    Raises:
        ValueError: The parent's State sets ``_storage = "server"`` and the
            new State does not set ``_storage``.

    """
    replaced = _replaced_parent_schema(component_class, "State", nearest)
    if replaced is None:
        return
    parent, parent_schema = replaced
    declared = cast("type", nearest.value)
    owner = _safe_class_text(nearest.declaring_class, "__name__") or "Component"
    parent_name = f"{_safe_class_text(parent.declaring_class, '__name__') or '<class>'}.State"

    if state_setting(parent_schema, "_storage", "signed") == "server" and not has_state_setting(declared, "_storage"):
        msg = (
            f"Component {owner}: State replaces {parent_name}, which keeps its values on the server"
            f' (_storage = "server"). The new State does not set _storage, so its values would be'
            f" stored in the page, where anyone who opens the page can read them. Write"
            f" `class State({parent_name}):` to keep the parent's fields and settings, or set"
            f' _storage in the new State ("server", or "signed" to store the values in the page'
            f" on purpose)."
        )
        raise ValueError(msg)

    sentences: list[str] = []
    dropped = _dropped_field_names(parent_schema, state_cls)
    if dropped:
        sentences.append(_dropped_fields_sentence(nearest, parent, dropped))
    else:
        sentences.append(f"Component {owner}: State replaces {parent_name}.")
    consequences = {
        "_public": "browser code can now read every field",
        "_model": "browser code can now change every field it can read",
        "_max_age": "its values never expire",
    }
    for setting, consequence in consequences.items():
        if state_setting(parent_schema, setting) is not None and not has_state_setting(declared, setting):
            sentences.append(f"It does not set {setting}, which {parent_name} sets, so {consequence}.")
    if len(sentences) == 1 and not dropped:
        return
    sentences.append(
        f"To keep the parent's fields and settings, write `class State({parent_name}):`"
        " or copy them into the new State."
    )
    _warn_nested_schema_replaced(nearest, " ".join(sentences))


def _validate_field_tuple(comp_name: str, attr_name: str, value: Any, field_names: tuple[str, ...]) -> tuple[str, ...]:
    """Check a ``_public`` / ``_model`` value: a tuple of declared field names."""
    if isinstance(value, str) or not isinstance(value, (tuple, list)) or not all(isinstance(f, str) for f in value):
        msg = f"Component {comp_name}: State.{attr_name} must be a tuple of State field names; got {value!r}."
        raise ValueError(msg)
    for entry in value:
        if entry not in field_names:
            msg = (
                f"Component {comp_name}: State.{attr_name} lists {entry!r}, which is not a State"
                f" field. Declared fields: {', '.join(field_names) or '(none)'}."
            )
            raise ValueError(msg)
    return tuple(value)


def resolve_state_meta(comp_name: str, user_cls: type, state_cls: type) -> StateMeta:
    """
    Read and validate the State meta attributes, applying the defaults.

    ``_model`` defaults to ``_public``, which defaults to all fields;
    ``_model`` must be a subset of ``_public``. ``_storage``, ``_max_bytes``,
    and ``_max_age`` are stored with their defaults
    (``"signed"``, ``8192``, ``None``).
    """
    field_names = state_field_names(state_cls)

    raw_public = state_setting(user_cls, "_public")
    if raw_public is None:
        public = field_names
    else:
        public = _validate_field_tuple(comp_name, "_public", raw_public, field_names)

    raw_model = state_setting(user_cls, "_model")
    if raw_model is None:
        model = public
    else:
        model = _validate_field_tuple(comp_name, "_model", raw_model, field_names)
        for entry in model:
            if entry not in public:
                msg = (
                    f"Component {comp_name}: State._model lists {entry!r}, which is not in"
                    f" _public. Every _model field must also be public;"
                    f" _public fields: {', '.join(public) or '(none)'}."
                )
                raise ValueError(msg)

    storage = state_setting(user_cls, "_storage", "signed")
    if storage not in _STORAGE_VALUES:
        msg = (
            f"Component {comp_name}: State._storage must be one of"
            f" {', '.join(repr(v) for v in _STORAGE_VALUES)}; got {storage!r}."
        )
        raise ValueError(msg)

    max_bytes = state_setting(user_cls, "_max_bytes", _DEFAULT_MAX_BYTES)
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        msg = f"Component {comp_name}: State._max_bytes must be a positive int (bytes); got {max_bytes!r}."
        raise ValueError(msg)

    max_age = state_setting(user_cls, "_max_age")
    if max_age is not None and not isinstance(max_age, timedelta):
        msg = f"Component {comp_name}: State._max_age must be a datetime.timedelta or None; got {max_age!r}."
        raise ValueError(msg)
    if max_age is not None and max_age.total_seconds() < 0:
        msg = f"Component {comp_name}: State._max_age must be non-negative; got {max_age!r}."
        raise ValueError(msg)

    return StateMeta(public=public, model=model, storage=storage, max_bytes=max_bytes, max_age=max_age)


def build_state_instance(comp_name: str, state_cls: type, raw_kwargs: dict[str, Any]) -> Any:
    """
    The default ``state_data`` derivation: build State from same-named kwargs.

    Each State field takes the kwarg of the same name; a field with no kwarg
    match falls back to its State default, and a field with neither is a
    render-time error naming the field.
    """
    values: dict[str, Any] = {}
    missing: list[str] = []
    required = _required_field_names(state_cls)
    for name in state_field_names(state_cls):
        if name in raw_kwargs:
            values[name] = raw_kwargs[name]
        elif name in required:
            missing.append(name)
    if missing:
        noun = "field" if len(missing) == 1 else "fields"
        verb = "has" if len(missing) == 1 else "have"
        msg = (
            f"Component {comp_name}: cannot build State: {noun}"
            f" {', '.join(repr(f) for f in missing)} {verb} no matching kwarg and no default."
            f" Pass a kwarg of the same name, give the State field a default,"
            f" or define state_data() on the component."
        )
        raise ValueError(msg)
    return state_cls(**values)


def public_state_values(state: Any, meta: StateMeta) -> dict[str, Any]:
    """
    Return the JSON form of a State instance's public fields, sorted by name.

    Only these fields ever reach the browser: every render puts them in the
    component's Events record, and a handler that changes State without
    rendering the component sends them in its ``state`` action. Both use this
    function, so a field outside ``_public`` cannot leak through either one.
    The JSON round trip turns a tuple into a list, the same as the token
    stores it, and sorting gives both places the same key order.
    """
    wire = state_wire_values(state)
    values = {name: wire[name] for name in sorted(meta.public)}
    return json.loads(json.dumps(values, allow_nan=False))
