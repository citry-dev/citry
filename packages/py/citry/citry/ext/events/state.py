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
from dataclasses import MISSING, dataclass, fields
from datetime import timedelta
from typing import Any

from citry._nested_declarations import _convert_to_slotted_dataclass

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
            merged.update(inspect.get_annotations(klass))
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
    for field_name in (*dataclass_fields, *_merged_annotations(user_cls)):
        if field_name.startswith("_"):
            msg = (
                f"Component {comp_name}: State declares field {field_name!r}. State fields cannot"
                f" start with an underscore (fields are the wire contract); underscore names are"
                f" reserved for the State meta: {', '.join(STATE_META_NAMES)}."
            )
            raise ValueError(msg)
    for klass in user_cls.__mro__:
        if klass is object:
            continue
        for name, value in vars(klass).items():
            if _is_dunder(name) or not name.startswith("_"):
                continue
            if name == "_citry_synthesized_declaration":
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


def convert_state_class(comp_name: str, user_cls: type) -> type:
    """
    Rebuild a State declaration as a mutable ``dataclass(slots=True)``.

    Mirrors the treatment the core gives ``Kwargs``: a plain class converts
    to a slotted dataclass, a class the user already decorated with
    ``@dataclass`` is kept as-is (but must not be frozen, because handlers
    mutate state). A State with base classes (e.g. ``class State(Kwargs):``)
    is rebuilt with the inherited field declarations included, since plain
    bases do not feed ``dataclass()`` on their own.

    The class the user wrote is never modified. The generated dataclass
    inherits the authored declaration, preserving methods, descriptors,
    zero-argument ``super()``, and source identity in its MRO.
    """
    if "__dataclass_fields__" in user_cls.__dict__:
        # The user decorated the class explicitly; respect their choices,
        # except immutability, which contradicts the State contract.
        if user_cls.__dataclass_params__.frozen:  # type: ignore[attr-defined]
            msg = (
                f"Component {comp_name}: State is a frozen dataclass. State must stay mutable"
                f" (handlers mutate it and the changes travel back to the client);"
                f" declare it without frozen=True."
            )
            raise ValueError(msg)
        return user_cls
    return _convert_to_slotted_dataclass(user_cls)


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
    field_names = tuple(f.name for f in fields(state_cls))

    raw_public = getattr(user_cls, "_public", None)
    if raw_public is None:
        public = field_names
    else:
        public = _validate_field_tuple(comp_name, "_public", raw_public, field_names)

    raw_model = getattr(user_cls, "_model", None)
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

    storage = getattr(user_cls, "_storage", "signed")
    if storage not in _STORAGE_VALUES:
        msg = (
            f"Component {comp_name}: State._storage must be one of"
            f" {', '.join(repr(v) for v in _STORAGE_VALUES)}; got {storage!r}."
        )
        raise ValueError(msg)

    max_bytes = getattr(user_cls, "_max_bytes", _DEFAULT_MAX_BYTES)
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        msg = f"Component {comp_name}: State._max_bytes must be a positive int (bytes); got {max_bytes!r}."
        raise ValueError(msg)

    max_age = getattr(user_cls, "_max_age", None)
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
    for state_field in fields(state_cls):
        if state_field.name in raw_kwargs:
            values[state_field.name] = raw_kwargs[state_field.name]
        elif state_field.default is MISSING and state_field.default_factory is MISSING:
            missing.append(state_field.name)
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
