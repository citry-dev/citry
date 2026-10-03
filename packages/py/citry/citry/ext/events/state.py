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
from typing import Any, cast

from citry._annotation_introspection import _own_annotations
from citry._class_introspection import _safe_class_text
from citry._nested_declarations import (
    _CONST_SCHEMA_DEFAULTS_ATTR,
    _SYNTHESIZED_DECLARATION_ATTR,
    _SYNTHESIZED_FIELD_OWNERS_ATTR,
    NestedClassDeclaration,
    _convert_to_slotted_dataclass,
    _dropped_field_names,
    _dropped_fields_sentence,
    _replaced_parent_schema,
    _warn_nested_schema_replaced,
)

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
_SYNTHESIZED_STATE_NAMES = frozenset(
    {_SYNTHESIZED_DECLARATION_ATTR, _SYNTHESIZED_FIELD_OWNERS_ATTR, _CONST_SCHEMA_DEFAULTS_ATTR}
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
            # Citry's generated schema carries private construction metadata;
            # only author-written underscore values belong to the State meta.
            if name in _SYNTHESIZED_STATE_NAMES:
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
    mutate state). A State with base classes, such as
    ``class State(Parent.State):`` or ``class State(Kwargs):``, keeps the
    fields and defaults of those bases.

    The class the user wrote is never modified. The generated dataclass
    inherits the authored declaration, preserving methods, descriptors,
    zero-argument ``super()``, and source identity in its MRO.
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
    converted = _convert_to_slotted_dataclass(user_cls)
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

    if getattr(parent_schema, "_storage", "signed") == "server" and not hasattr(declared, "_storage"):
        msg = (
            f"Component {owner}: State replaces {parent_name}, which keeps its values on the server"
            f' (_storage = "server"). The new State does not set _storage, so it would store its'
            f" values in the page, where anyone who opens it can read them. Write"
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
        "_max_age": "its State tokens never expire",
    }
    for setting, consequence in consequences.items():
        if getattr(parent_schema, setting, None) is not None and not hasattr(declared, setting):
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
    values = {name: getattr(state, name) for name in sorted(meta.public)}
    return json.loads(json.dumps(values, allow_nan=False))
