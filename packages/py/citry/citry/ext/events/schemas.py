"""
Data schemas of the ``events`` extension: conversion, validation, coercion.

A handler's ``data`` parameter is annotated with a schema class, and the
whole wire ``args`` payload is validated against it before the handler runs.
This module owns that machinery: the class-side conversion (a plain annotated
class gets the same dataclass treatment as ``State``; a dataclass is used
as-is; a Pydantic class is checked by a copy of its own validator that
stops each list and dict at its first bad item, see ``_pydantic_bounded``),
and the payload validation with its deliberately small coercion table.
Validation returns a structured :class:`ValidationResult` rather than
raising, so the dispatcher can map failures onto the per-field 422 error
object. Design:
``docs/design/events.md`` section 3.3.

The coercion table, exactly (anything else is a per-field error):

- ``int`` / ``float`` cross-coercion (a whole ``float`` for an ``int`` field,
  any ``int`` for a ``float`` field; ``bool`` counts as neither),
- ``str`` to ``UUID`` / ``datetime`` / ``date`` / ``time`` / ``Decimal`` /
  ``Enum`` (ISO strings, by enum value),
- ``list`` to ``tuple`` / ``set``,
- nested annotated classes from objects,
- a ``Literal[...]`` field accepts a value equal to one of its listed
  values after that value's own rule above (an Enum member by its value),
  so ``"2"`` from a form post binds to ``Literal[1, 2]`` and ``true`` never
  matches ``1``.

The binding is source-aware (design 3.3). A JSON payload stays strict for
``int`` / ``float`` / ``bool`` fields: JSON expresses those types natively,
so a string there is a client bug worth surfacing. Form posts and GET query
strings cannot express them (every value arrives as a string), so for
payloads from those codecs strings additionally bind to declared ``int`` /
``float`` / ``bool`` fields (``"5"`` binds to ``int``; ``bool`` accepts the
HTML form vocabulary ``"true"`` / ``"false"`` / ``"1"`` / ``"0"`` / ``"on"``).
A form submitted through the browser runtime gets the same rule: the browser
sends the form's text and marks the call with ``argsSource: "form"``. The
codecs and the dispatcher mark such payloads by building them as
[`StringArgs`][citry.ext.events.schemas.StringArgs]; see ``validate_args``.

Deliberately absent: ORM-model-by-primary-key coercion (an argument must
never turn into an unauthorized database fetch; handlers fetch and authorize
their own models).
"""

from __future__ import annotations

import contextlib
import json
import math
import re
import sys
import threading
from array import array
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import MISSING, dataclass, fields, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import GenericAlias, UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
    NamedTuple,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)
from uuid import UUID
from weakref import WeakKeyDictionary, WeakSet

import typing_extensions

from citry._nested_declarations import _is_plain_field_family, convert_plain_declaration
from citry.ext.events import _pydantic_bounded as bounded
from citry.ext.events.errors import PYDANTIC_EXTRA_TYPES, FieldErrors, PydanticTotal, trimmed_path
from citry.ext.events.files import UploadedFile
from citry.ext.events.handlers import _is_schema_class
from citry.ext.events.state import convert_state_class
from citry.util.logger import logger

if TYPE_CHECKING:
    from citry._model_base import ModelBase

# Pydantic is optional: when installed, Pydantic-model schemas are delegated
# to it wholesale; without it, schemas are plain annotated classes or
# dataclasses and this module needs nothing else.
try:
    import pydantic
except ImportError:  # pragma: no cover - exercised via the tests' None patch
    pydantic = None  # type: ignore[assignment]

# Internal marker for "this value failed": lets the coercion recursion record
# an error and keep validating the remaining fields, so one bad field never
# hides the others.
_INVALID: Any = object()

_REQUIRED_MESSAGE = "This field is required."
_EXTRA_MESSAGE = "Unexpected field: not declared on the schema."
# File parts only exist once the multipart payload codec produces them; any
# plain wire value on a file-typed field is a validation error until then.
_FILE_MESSAGE = "Expected an uploaded file: file fields arrive as multipart form data, not as JSON values."

# The bool spellings a string transport may send (design 3.3): the HTML form
# vocabulary, exactly. "on" is what a value-less checked checkbox submits.
# Anything else (including "off", which an unchecked checkbox never submits,
# and any casing variant) is a per-field error.
_BOOL_STRINGS = {"true": True, "1": True, "on": True, "false": False, "0": False}
_BOOL_STRINGS_MESSAGE = "accepted spellings: true, false, 1, 0, on"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    The outcome of validating a wire args payload against a schema.

    Validation never raises for bad user input; it returns this result, and
    the dispatcher maps a failed one onto the per-field 422 error object
    (``{fields: {name: message}}``).

    Attributes:
        value: The validated schema instance, or ``None`` when validation
            failed.
        fields: One message per failed field, keyed by the field's path
            (nested fields use dotted paths like ``"address.city"``, list
            elements ``"tags.1"``). Sorted by field path, with list indexes
            in number order, so the error object is deterministic. Empty
            when validation succeeded. Each list or dict field reports only
            its first bad item. It lists at most 20 messages for fields the
            payload sent and the schema does not declare, and stops listing
            once the messages reach ``MAX_FIELD_ERRORS_TEXT``. A message
            longer than ``MAX_FIELD_MESSAGE`` (1,000) characters is cut to
            that length and ends with "…". Data with
            too many errors, data too large or nested too deeply to
            check, or a check that took too long gets one message under
            ``_args``.
        unlisted_fields: How many messages those two limits left out of
            ``fields``. ``0`` when none were.

    """

    value: Any
    fields: dict[str, str]
    unlisted_fields: int = 0

    @property
    def ok(self) -> bool:
        """Whether the payload validated (no per-field errors)."""
        return not self.fields


class StringArgs(dict[str, Any]):
    """
    An args payload whose values arrived as strings (a form post, a GET
    query string, or a form the browser runtime collected).

    The string transports cannot express numbers or booleans natively, so
    the form and query codecs (``codecs.py``) build the args they decode as
    this class, and [`validate_args`][citry.ext.events.schemas.validate_args]
    then additionally binds strings to declared ``int`` / ``float`` /
    ``bool`` fields (the source-aware rule of design 3.3). The dispatcher
    also builds it for a JSON call marked ``argsSource: "form"``, which the
    browser sends when it collected the args from a form, so both ways of
    submitting a form bind the same. Any other JSON payload is decoded into
    plain dicts, so its validation stays strict.
    """


# The results of `convert_schema_class` and `_schema_info`, one per schema
# class. Two threads may compute one at the same time; the lock makes both
# return the result stored first, so a schema keeps one converted class.
_CONVERTED_SCHEMAS: dict[type, type] = {}
_SCHEMA_INFOS: dict[type, tuple[type, tuple[_FieldSpec, ...]]] = {}
_SCHEMA_CACHE_LOCK = threading.Lock()


def convert_schema_class(schema_cls: type) -> type:
    """
    Resolve a ``data`` schema class to the class payloads are validated into.

    A Pydantic model is returned as-is (validation delegates to Pydantic
    wholesale). A class the user decorated with ``@dataclass`` is used as-is
    (frozen is fine here: schemas are inputs, nothing mutates them). Any
    other annotated class gets the same dataclass treatment as ``State``
    (via [`convert_state_class`][citry.ext.events.state.convert_state_class]):
    the class the user wrote is never modified, and inherited annotations
    count as fields.

    The conversion is computed once per class and reused, so nested schema
    instances keep a stable class identity across calls.

    Args:
        schema_cls: The resolved ``data`` annotation.

    Returns:
        The class validated payloads are constructed with.

    """
    cached = _CONVERTED_SCHEMAS.get(schema_cls)
    if cached is not None:
        return cached
    if _is_pydantic_model(schema_cls) or "__dataclass_fields__" in schema_cls.__dict__:
        converted = schema_cls
    else:
        converted = convert_state_class(schema_cls.__name__, schema_cls)
    with _SCHEMA_CACHE_LOCK:
        return _CONVERTED_SCHEMAS.setdefault(schema_cls, converted)


# Events `data` classes generated under `model_base`, by authored class and
# setting. One authored class may serve components of several Citry
# instances with different settings, so the setting is part of the key.
_GENERATED_DATA_SCHEMAS: dict[tuple[type, ModelBase], type] = {}


def generated_data_schema(comp_name: str, schema_cls: type, model_base: ModelBase) -> type:
    """
    Return the class a handler's plain ``data`` declaration becomes under ``model_base``.

    A Pydantic model, a class decorated with ``@dataclass``, or another class
    that brings its own construction is kept as written, as without the
    setting.

    Raises:
        ValueError: ``model_base`` is ``typing.NamedTuple`` or a Pydantic v1
            model, which Events validation cannot build.

    """
    # A class that is, or inherits, a dataclass is kept as written, as
    # without the setting: a child keeps its parent's kind.
    if (
        _is_pydantic_model(schema_cls)
        or any("__dataclass_fields__" in klass.__dict__ for klass in schema_cls.__mro__)
        or not _is_plain_field_family(schema_cls)
    ):
        return schema_cls
    key = (schema_cls, model_base)
    cached = _GENERATED_DATA_SCHEMAS.get(key)
    if cached is not None:
        return cached
    if model_base.kind == "namedtuple":
        msg = (
            f"Component {comp_name}: the event data class {schema_cls.__qualname__} cannot be generated as a"
            " NamedTuple, because Events validation builds dataclass or Pydantic instances only. Decorate it with"
            " @dataclass to keep it a dataclass, or set model_base to another kind."
        )
        raise ValueError(msg)
    if model_base.kind == "pydantic-v1":
        msg = (
            f"Component {comp_name}: the event data class {schema_cls.__qualname__} cannot be generated as a"
            " Pydantic v1 model, because Events validation reads dataclasses, annotated classes and Pydantic v2"
            " models only. Decorate it with @dataclass to keep it a dataclass, or set model_base to a Pydantic v2"
            " model."
        )
        raise ValueError(msg)
    generated = convert_plain_declaration(schema_cls, model_base=model_base, component_name=comp_name)
    with _SCHEMA_CACHE_LOCK:
        return _GENERATED_DATA_SCHEMAS.setdefault(key, generated)


def validate_args(
    schema_cls: type,
    args: Mapping[str, Any],
    *,
    bind_strings: bool | None = None,
) -> ValidationResult:
    """
    Validate a wire ``args`` payload against a handler's ``data`` schema.

    Checks the payload's keys against the schema's fields (a missing required
    field and an unexpected key are each a per-field error), coerces the
    values per the module's coercion table, and constructs the schema
    instance. Nested annotated classes validate recursively from objects;
    a Pydantic v2 model schema is validated by Pydantic's rules and messages,
    through a copy of its validator that stops at the first bad item of
    each list or dict and stops the whole validation past an error limit.

    Args:
        schema_cls: The schema class (converted or not;
            [`convert_schema_class`][citry.ext.events.schemas.convert_schema_class]
            is applied internally).
        args: The wire args payload, one JSON-decoded object.
        bind_strings: Whether strings additionally bind to declared ``int``
            / ``float`` / ``bool`` fields, the string-transport rule of
            design 3.3 (``"5"`` binds to ``int``; ``bool`` accepts exactly
            ``"true"`` / ``"false"`` / ``"1"`` / ``"0"`` / ``"on"``).
            ``None`` (the default) reads the answer off the payload itself:
            ``True`` when a codec or the dispatcher built it as
            [`StringArgs`][citry.ext.events.schemas.StringArgs], else the
            strict JSON behavior. A Pydantic-model schema is unaffected
            either way: Pydantic applies its own coercion rules.

    Returns:
        A [`ValidationResult`][citry.ext.events.schemas.ValidationResult]:
        either the schema instance, or the per-field messages sorted by
        field path, with list indexes in number order. A schema
        ``__post_init__`` that raises propagates to the caller. A Pydantic
        validator that raises ``ValueError`` or ``AssertionError`` gives a
        field error with its message. One that raises another exception
        gives a field error saying the value could not be checked. Data
        nested deeper than Python can follow gives the "nested too deeply"
        message under ``_args``.

    The check runs on a thread of Citry's own with a large stack, and the
    calling thread waits for it. Validators and ``__post_init__`` see the
    caller's context variables there, but not ``threading.local`` values,
    and a context variable they set does not reach the caller.

    """
    if bind_strings is None:
        bind_strings = isinstance(args, StringArgs)
    if not isinstance(args, Mapping):
        return ValidationResult(value=None, fields={"": f"Expected an object, got {_value_type_name(args)}."})
    # The whole check runs on a check thread, whose large stack fits data at
    # the nesting limit, whatever stack the server gives the calling thread.
    return bounded.run_on_check_thread(_validate_payload, schema_cls, args, bind_strings=bind_strings)


def _validate_payload(schema_cls: type, args: Mapping[str, Any], *, bind_strings: bool) -> ValidationResult:
    """Check ``args`` against ``schema_cls`` as ``validate_args`` describes, on the running thread."""
    errors = FieldErrors()
    # One error total for the whole payload, so every Pydantic call inside it
    # (a nested model in a plain dataclass, one per list item) shares it, and
    # one work budget for the request, which a direct caller gets too.
    with bounded.request_work(), bounded.validation_scope(args):
        try:
            instance = _validate_object(schema_cls, args, None, errors, bind_strings=bind_strings)
        except bounded.ValidationTooCostly as stop:
            # Stopping drops the errors Pydantic held, so the call gets one
            # message for the whole payload.
            bounded.warn_if_stopped(schema_cls, stop)
            return ValidationResult(value=None, fields={"_args": stop.message})
        except RecursionError:
            # The data nests deeper than Python can follow inside one of the
            # checks. Answer that it is nested too deeply. The log has no
            # traceback, which would list every frame, and comes once per class.
            bounded.warn_work_spent(schema_cls, "depth")
            return ValidationResult(value=None, fields={"_args": bounded.TOO_DEEP_MESSAGE})
    if instance is _INVALID:
        # The payload alone decides how many undeclared keys and how many
        # list or dict items it sends, so only those messages are limited,
        # in path order so the same names are listed on every call.
        fields, unlisted = errors.limited()
        return ValidationResult(value=None, fields=fields, unlisted_fields=unlisted)
    return ValidationResult(value=instance, fields={})


################################################
# SCHEMA-OBJECT VALIDATION
################################################


class _FieldSpec(NamedTuple):
    """One schema field: its name, resolved annotation, and required-ness."""

    name: str
    annotation: Any
    required: bool


def _field_hints(converted: type) -> dict[str, Any]:
    """Resolve the annotations of the dataclass fields, and nothing else."""
    wanted = {field.name for field in fields(converted)}
    # Base-first so a subclass annotation wins, matching how `get_type_hints`
    # walks the MRO.
    collected: dict[str, Any] = {
        name: annotation
        for base in reversed(converted.__mro__)
        for name, annotation in getattr(base, "__annotations__", {}).items()
        if name in wanted
    }
    # A throwaway carrier so the strings resolve against the same module
    # namespace the real class would have used.
    carrier = type(converted.__name__, (), {"__annotations__": collected, "__module__": converted.__module__})
    return get_type_hints(carrier)


def _schema_info(schema_cls: type) -> tuple[type, tuple[_FieldSpec, ...]]:
    """The converted class and field specs of a non-Pydantic schema, computed once."""
    cached = _SCHEMA_INFOS.get(schema_cls)
    if cached is not None:
        return cached
    converted = convert_schema_class(schema_cls)
    # Resolved annotation objects, not strings: user modules may use
    # ``from __future__ import annotations``.
    try:
        hints = get_type_hints(converted)
    except TypeError:
        # Python 3.10 refuses to resolve a bare, unsubscripted `ClassVar` written
        # as a deferred annotation, and one bad entry fails the whole class. Such
        # an attribute is not a dataclass field, so its annotation was never
        # wanted here; resolve the fields on their own and let a field whose own
        # annotation is genuinely broken still raise.
        hints = _field_hints(converted)
    specs = tuple(
        _FieldSpec(
            name=field.name,
            annotation=hints.get(field.name, Any),
            required=field.default is MISSING and field.default_factory is MISSING,
        )
        for field in fields(converted)
        # Fields the constructor does not take (``field(init=False)``) cannot
        # come from the wire; they are neither accepted nor required.
        if field.init
    )
    with _SCHEMA_CACHE_LOCK:
        return _SCHEMA_INFOS.setdefault(schema_cls, (converted, specs))


def payload_fields(schema_cls: type) -> tuple[_FieldSpec, ...] | None:
    """
    Return the fields a ``data`` class accepts from the wire, for ``citry check``.

    Returns None for a Pydantic model, whose own rules decide what it
    accepts, and for a class whose annotations cannot be resolved, which
    fails at the first call anyway.
    """
    if _is_pydantic_model(schema_cls):
        return None
    try:
        return _schema_info(schema_cls)[1]
    except Exception:  # noqa: BLE001 - an unresolvable annotation is reported when the handler runs
        return None


def nested_pydantic_classes(schema_cls: type) -> tuple[type, ...]:
    """
    Return the Pydantic classes a plain ``data`` class reaches through its fields, at any depth.

    Citry checks those with the copy of their validator too, so registration
    refuses them on a Pydantic too old to build one. A class whose
    annotations cannot be resolved is skipped; it fails at its first call.
    """
    found: list[type] = []
    seen: set[int] = set()
    # Visited hints stay alive, so a freed hint's id cannot name the next one.
    visited: list[Any] = []
    todo: list[Any] = [schema_cls]
    while todo:
        hint = todo.pop()
        if id(hint) in seen:
            continue
        seen.add(id(hint))
        visited.append(hint)
        todo.extend(get_args(hint))
        if not isinstance(hint, type):
            continue
        if bounded.is_pydantic_v2_class(hint) and hint is not schema_cls:
            found.append(hint)
        if _is_pydantic_model(hint) or not _is_schema_class(hint):
            continue
        specs = payload_fields(hint)
        todo.extend(spec.annotation for spec in specs or ())
    return tuple(found)


def check_no_pydantic_v1(comp_name: str, schema_cls: type) -> None:
    """
    Refuse a ``data`` class that is, or holds, a ``pydantic.v1`` model or dataclass.

    Events checks data with dataclasses, annotated classes and Pydantic v2
    models. A v1 check cannot be stopped or counted the way those are, so
    registration refuses it wherever it sits: as the class itself, in a
    field, a list, a dict, an optional or a union, in a nested plain class,
    or inside a Pydantic v2 class (see ``pydantic_v1_model_in``). A class
    whose annotations cannot be resolved yet is skipped; a v1 class found
    behind it at a call is refused there.

    Raises:
        ValueError: The class is or holds a ``pydantic.v1`` class, named in
            the message with the fix.

    """
    # A v1 class can exist only once the app loaded `pydantic.v1`, so other
    # apps skip resolving the annotations. Citry's own import fails under
    # Pydantic 1 (`state.py` reads Pydantic 2 methods), so that install
    # never reaches here.
    if "pydantic.v1" not in sys.modules:
        return
    found = pydantic_v1_class_in(schema_cls)
    if found is None:
        return
    where = "is" if found is schema_cls else f"holds {found.__qualname__}, which is"
    msg = (
        f"Component {comp_name}: the event data class {schema_cls.__qualname__} {where} a pydantic.v1 model or"
        " dataclass. Events checks event data with dataclasses, annotated classes and Pydantic v2 models only."
        f" Make {found.__qualname__} a Pydantic v2 model."
    )
    raise ValueError(msg)


def pydantic_v1_class_in(schema_cls: type) -> type | None:
    """Return the first ``pydantic.v1`` model or dataclass that a ``data`` class is or reaches, or ``None``."""
    seen: set[int] = set()
    # Each resolved annotation is a new object, such as `list[Tag]`, that
    # Python may free and give the same id to the next one. Keeping every
    # visited hint alive keeps an id from naming two different hints.
    visited: list[Any] = []
    todo: list[Any] = [schema_cls]
    while todo:
        hint = todo.pop()
        if id(hint) in seen:
            continue
        seen.add(id(hint))
        visited.append(hint)
        # The arguments of a list, dict, optional or union hold the classes.
        todo.extend(get_args(hint))
        if not isinstance(hint, type):
            continue
        if bounded.is_pydantic_v1_class(hint) or bounded.is_pydantic_v1_dataclass(hint):
            return hint
        if bounded.is_pydantic_v2_class(hint):
            # Pydantic reads its own fields, so Citry reads its core schema.
            root = bounded.core_schema_of(hint)
            found = None if root is None else bounded.pydantic_v1_model_in(root)
            if found is not None:
                return found
            # Citry checks a Pydantic dataclass's fields itself before
            # Pydantic builds it, so those fields are read below too.
            if _is_pydantic_model(hint):
                continue
        if not _is_schema_class(hint):
            continue
        todo.extend(_annotations_without_converting(hint))
    return None


def _annotations_without_converting(cls: type) -> list[Any]:
    """
    Return the resolved annotations of a class's fields, or none when they do not resolve yet.

    Registration reads these without building Citry's dataclass of the
    class, because building it formats the defaults with ``repr()``, which
    must not run before a call needs it.
    """
    try:
        hints = get_type_hints(cls)
    except Exception:  # noqa: BLE001 - an unresolvable annotation is reported when the handler runs
        return []
    # A dataclass field that `__init__` does not take never comes from the browser.
    skipped = {item.name for item in fields(cls) if not item.init} if is_dataclass(cls) else set()
    # A ClassVar is not a field, so the browser never sends a value for it.
    return [hint for name, hint in hints.items() if name not in skipped and get_origin(hint) is not ClassVar]


def declared_field_names(schema_cls: type) -> frozenset[str]:
    """
    Return the field names a ``data`` class takes from the wire, without resolving its annotations.

    The dispatcher reads this before it drops the host's CSRF fields from a
    call, so a class that declares such a field still receives it. A
    Pydantic model's field aliases count too, because Pydantic reads a
    payload key by its alias.
    """
    if _is_pydantic_model(schema_cls):
        model_fields = schema_cls.model_fields  # type: ignore[attr-defined]
        names = set(model_fields)
        for info in model_fields.values():
            names.update(_pydantic_input_names(info))
        return frozenset(names)
    converted = convert_schema_class(schema_cls)
    return frozenset(field.name for field in fields(converted) if field.init)


def _pydantic_input_names(info: Any) -> set[str]:
    """Return every top-level payload key a Pydantic field reads: its alias and its validation aliases."""
    names: set[str] = set()
    alias = getattr(info, "alias", None)
    if isinstance(alias, str):
        names.add(alias)
    # Pydantic v2's `validation_alias` is a string, an `AliasChoices` of
    # several, or an `AliasPath` whose first step is the top-level key.
    validation_alias = getattr(info, "validation_alias", None)
    choices = getattr(validation_alias, "choices", None)
    for choice in choices if isinstance(choices, list) else [validation_alias]:
        path = getattr(choice, "path", None)
        first = path[0] if isinstance(path, list) and path else choice
        if isinstance(first, str):
            names.add(first)
    return names


def json_value_error(annotation: Any, value: Any, *, bind_strings: bool = False) -> str | None:
    """
    Return the message the server gives for ``value`` in a field annotated ``annotation``, or None when it fits.

    By default ``value`` is checked as a JSON payload is, without the string
    rules of a form post, because the browser sends ``@c-*`` arguments as
    JSON. ``bind_strings`` applies those rules, as for a GET query string.
    """
    # On a check thread, for its large stack, as in `validate_args`.
    return bounded.run_on_check_thread(_value_error, annotation, value, bind_strings=bind_strings)


def _value_error(annotation: Any, value: Any, *, bind_strings: bool) -> str | None:
    """Return the message for ``value`` as ``json_value_error`` describes, checking on the running thread."""
    errors = FieldErrors()
    with bounded.request_work(), bounded.validation_scope(value):
        try:
            if _coerce(value, annotation, (None, ""), errors, bind_strings=bind_strings) is not _INVALID:
                return None
        except bounded.ValidationTooCostly as stop:
            return stop.message
        except RecursionError:
            # Data nested deeper than Python can follow in the check, as in `validate_args`.
            return bounded.TOO_DEEP_MESSAGE
    return errors.first_message()


def _validate_object(
    schema_cls: type,
    mapping: Mapping[str, Any],
    parent: Any,
    errors: FieldErrors,
    *,
    bind_strings: bool,
) -> Any:
    """
    Validate one payload object against one schema class.

    Records failures in ``errors`` under field paths that start at
    ``parent`` (``None`` for the top level) and returns the schema instance,
    or ``_INVALID`` when anything in this object's subtree failed.
    """
    if bounded.is_pydantic_v1_class(schema_cls) or bounded.is_pydantic_v1_dataclass(schema_cls):
        return _refuse_pydantic_v1(schema_cls, parent, errors)
    if _is_pydantic_model(schema_cls):
        return _validate_pydantic(schema_cls, mapping, parent, errors)

    converted, specs = _schema_info(schema_cls)
    accepted = {spec.name for spec in specs}
    ok = True

    for key in mapping:
        if key not in accepted:
            errors.add_unexpected((parent, str(key)), _EXTRA_MESSAGE)
            # The payload decides how many keys it sends, so each one counts
            # toward the validation's error limit.
            bounded.count_errors()
            ok = False

    values: dict[str, Any] = {}
    for spec in specs:
        if spec.name in mapping:
            coerced = _coerce(
                mapping[spec.name], spec.annotation, (parent, spec.name), errors, bind_strings=bind_strings
            )
            if coerced is _INVALID:
                ok = False
            else:
                values[spec.name] = coerced
        elif spec.required:
            errors.add((parent, spec.name), _REQUIRED_MESSAGE)
            bounded.count_errors()
            ok = False

    if not ok:
        return _INVALID
    if not _is_pydantic_dataclass(converted):
        return converted(**values)
    # A Pydantic dataclass checks its fields when it is built, so this call
    # costs what a Pydantic model's does, and can fail the way one does. The
    # copy of its validator builds it as its `__init__` would, and stops early.
    checker = _pydantic_checker(converted, mapping, parent, errors)
    if checker is _INVALID:
        return _INVALID
    try:
        if checker is None:
            return converted(**values)
        return bounded.validate_init(checker, converted, values)
    except pydantic.ValidationError as err:
        _record_pydantic_errors(err, converted, parent, errors)
        return _INVALID
    except bounded.ValidationTooCostly:
        raise
    except Exception:  # noqa: BLE001 - a validator's own bug must not escape the dispatcher
        logger.exception(f"A validator raised while checking event data for {schema_cls.__qualname__}.")
        errors.add(trimmed_path(parent, "_args"), bounded.NOT_CHECKABLE_MESSAGE)
        return _INVALID


def _validate_pydantic(schema_cls: type, mapping: Mapping[str, Any], parent: Any, errors: FieldErrors) -> Any:
    """Delegate one payload object to Pydantic, mapping its errors onto field paths."""
    checker = _pydantic_checker(schema_cls, mapping, parent, errors)
    if checker is _INVALID:
        return _INVALID
    try:
        if checker is None:
            return schema_cls.model_validate(dict(mapping))  # type: ignore[attr-defined]
        # A stop raised inside goes up to validate_args, which ends the whole validation.
        return bounded.validate_python(checker, dict(mapping))
    except pydantic.ValidationError as err:
        _record_pydantic_errors(err, schema_cls, parent, errors)
        return _INVALID
    except bounded.ValidationTooCostly:
        raise
    except RecursionError:
        # The data nests deeper than Python can follow inside a check that
        # Citry does not control, such as a validator of the author.
        # `validate_args` answers that the data is nested too deeply and logs it once.
        raise bounded.ValidationTooCostly("depth") from None
    except Exception:  # noqa: BLE001 - a validator's own bug must not escape the dispatcher
        # Pydantic turns only ValueError and AssertionError in a validator
        # into a ValidationError; another exception is the author's bug, and
        # answers this one call 422 rather than failing the whole envelope.
        logger.exception(f"A validator raised while checking event data for {schema_cls.__qualname__}.")
        errors.add(trimmed_path(parent, "_args"), bounded.NOT_CHECKABLE_MESSAGE)
        return _INVALID


def _refuse_pydantic_v1(schema_cls: type, parent: Any, errors: FieldErrors) -> Any:
    """
    Refuse data for a ``pydantic.v1`` class that registration did not see, and log why once.

    Registration refuses a ``data`` class that holds a v1 model, but it
    cannot see one behind a forward reference resolved only later. The
    call then gets the "could not be checked" 422, and the v1 model never
    runs on the browser's data.
    """
    if schema_cls not in _LOGGED_V1:
        _LOGGED_V1.add(schema_cls)
        logger.error(
            f"Citry refuses event data for {schema_cls.__qualname__}, a pydantic.v1 class, because Events checks"
            " data with dataclasses, annotated classes and Pydantic v2 models only. Make"
            f" {schema_cls.__qualname__} a Pydantic v2 model."
        )
    errors.add(trimmed_path(parent, "_args"), bounded.NOT_CHECKABLE_MESSAGE)
    return _INVALID


# The v1 classes already logged by `_refuse_pydantic_v1`, so each is logged once, not on every call.
_LOGGED_V1: WeakSet[type] = WeakSet()


def _pydantic_checker(schema_cls: type, mapping: Mapping[str, Any], parent: Any, errors: FieldErrors) -> Any:
    """
    Return Citry's copy of a Pydantic class's validator, ``None`` to use its own, or ``_INVALID``.

    A class whose forward references are still unresolved has no core
    schema to copy, so it keeps its own validator with the path limit. A
    v2 class gets the copy, plus the path limit when the copy could only be
    built without its counting wrappers.
    ``_INVALID`` means the call was refused, with the message recorded.
    """
    checker = None
    if bounded.is_pydantic_v2_class(schema_cls):
        # Inside a union that Citry's own check may run again, the class's
        # checks that parse text spend for it each time they run.
        checker = bounded.checker_for(schema_cls, repeated=bounded.in_repeated_check())
    if checker is not None and checker.validator is None:
        bounded.log_refusal(schema_cls, checker)
        errors.add(trimmed_path(parent, "_args"), bounded.NOT_CHECKABLE_MESSAGE)
        return _INVALID
    if (checker is None or checker.needs_path_limit) and not pydantic_can_report(mapping, schema_cls, errors):
        errors.add(trimmed_path(parent, "_args"), PATHS_TOO_LONG_MESSAGE)
        return _INVALID
    return checker


def _record_pydantic_errors(err: Any, schema_cls: type, parent: Any, errors: FieldErrors) -> None:
    """Record each error of a Pydantic ``ValidationError`` under ``parent``."""
    # Citry reads only each error's location, message and type, so the URL,
    # context and input value are not built.
    entries = err.errors(include_url=False, include_context=False, include_input=False)
    shared: dict[tuple[int, Any], Any] = {}
    for container in pydantic_container_paths(schema_cls, (entry["loc"] for entry in entries), parent, shared):
        errors.add_container(container)
    for entry in entries:
        location = entry["loc"]
        # Only a location with no text has no field of its own.
        has_text = location not in ((), ("",))
        path = shared_location_path(parent, location, shared) if has_text else trimmed_path(parent)
        if entry.get("type") in PYDANTIC_EXTRA_TYPES:
            errors.add_unexpected(path, str(entry["msg"]))
        else:
            errors.add(path, str(entry["msg"]))


def shared_location_path(parent: Any, location: Sequence[Any], shared: dict[tuple[int, Any], Any]) -> Any:
    """
    Return the field path of a Pydantic error location, reusing the pairs of earlier errors.

    Pydantic gives every error its own copy of each key, so errors under one
    long key would otherwise be split at the key's dots once each. ``shared``
    holds the pairs made for one Pydantic call.
    """
    path = parent
    for part in location:
        slot = (id(path), part)
        pair = shared.get(slot)
        if pair is None:
            pair = shared[slot] = (path, str(part))
        path = pair
    return path


# Pydantic writes the whole path of a field into each error it reports,
# before Citry sees any of them. Where Citry cannot use its copy of the
# validator with the wrappers that count errors (a Pydantic v1 model, a State
# checked as JSON, or a copy built without those wrappers), Citry adds up the
# paths before Pydantic runs. These limit the total text of the paths in one
# validation's payloads: the larger of a fixed amount, which is about 335,000
# paths of 50 characters, and a multiple of the payloads' own size, so a
# large request with short keys still reaches Pydantic. A union counts once
# per member, because each member reports its own errors.
MAX_PYDANTIC_PATH_TEXT = 16 * 1024 * 1024
MAX_PYDANTIC_PATH_TEXT_PER_CHARACTER = 32
PATHS_TOO_LONG_MESSAGE = (
    "The field paths in this data are too long in total to check. Send shorter keys or fewer items."
)
_NESTED_JSON_TYPES = frozenset({dict, list, tuple})
# The tokens that matter in the text a `Json` field reads. An unclosed string
# runs to the end of the text, so a bad text takes one pass like a good one.
_JSON_TOKEN = re.compile(r""""(?:[^"\\]|\\.)*+(?:"|\\?\Z)|[\[\]{},]""", re.DOTALL)


class _ModelCosts(NamedTuple):
    """What a Pydantic model can add to a payload's error paths."""

    # Whether a `Json` field reads a payload out of a string.
    parses_json: bool
    # The most required fields of any one model: an empty object reports each
    # of them as missing, with the object's own path.
    object_fields: int
    # The most required positions of a fixed tuple or NamedTuple, which an
    # empty list reports the same way.
    list_items: int
    # How many times one bad value can be reported: each member of a union
    # that has no discriminator tries the value and reports its own errors.
    reports_per_value: int


_MODEL_COSTS: WeakKeyDictionary[type, _ModelCosts] = WeakKeyDictionary()


def pydantic_can_report(payload: Any, schema_cls: type, errors: FieldErrors) -> bool:
    """
    Add the path text of ``payload`` to this validation's total and return whether Pydantic may check it.

    Args:
        payload: The JSON-decoded value about to go to Pydantic.
        schema_cls: The Pydantic model that will check it.
        errors: The validation's collector, which keeps the running total.

    Returns:
        ``False`` when this validation's paths are too long to pass to Pydantic.

    """
    costs = _model_costs(schema_cls)
    total = errors.pydantic_total
    path_text, size = _measure_paths(payload, costs, schema_cls, total)
    total.path_text += path_text * costs.reports_per_value
    total.size += size
    return total.path_text <= max(MAX_PYDANTIC_PATH_TEXT, MAX_PYDANTIC_PATH_TEXT_PER_CHARACTER * total.size)


def _measure_paths(payload: Any, costs: _ModelCosts, schema_cls: type, total: PydanticTotal) -> tuple[int, int]:
    """
    Return the total length of the paths in ``payload``, and about how many characters it takes to write it.

    A container's paths count once per model that checks it, so each member
    of a union in Citry's own validators counts, and a nested Pydantic dataclass
    of one class counts once at any depth. Its size counts once whatever
    checks it, because a payload read twice is no larger, and only the size
    can raise the limit. The ids stay valid because the payload lives until
    the validation ends.
    """
    path_text = 0
    size = 0
    # Each value counts, valid or not: a payload's values could all fail.
    stack: list[tuple[Any, int]] = [(payload, 0)]

    def measure_item(item: Any, length: int) -> None:
        nonlocal path_text, size
        # Exact types first: this runs on every value of every Pydantic
        # request, and JSON only makes these types. The extra 1 is its comma.
        item_type = type(item)
        if item_type is str:
            size += len(item) + 1
            if costs.parses_json:
                path_text += _json_text_paths(item, length, costs)
        elif item_type in _NESTED_JSON_TYPES or isinstance(item, Mapping):
            size += 1
            stack.append((item, length))
        elif item_type is int:
            # About 0.3 digits per bit, without writing a number that can
            # be longer than Python agrees to write.
            size += (item.bit_length() * 77 >> 8) + 2
        else:
            # A flat guess for a float or a literal: `repr` is no measure of
            # the request's text, which can write 1e15 in four characters.
            size += 5

    while stack:
        value, length = stack.pop()
        place = (id(value), schema_cls)
        if place in total.measured:
            continue
        total.measured.add(place)
        size_before = size
        if isinstance(value, Mapping):
            path_text += costs.object_fields * length
            for key, item in value.items():
                key_length = len(key) if type(key) is str else len(str(key))
                size += key_length
                item_length = length + key_length + 1
                path_text += item_length
                if costs.parses_json and type(key) is str:
                    path_text += _json_text_paths(key, item_length, costs)
                measure_item(item, item_length)
        elif isinstance(value, (list, tuple)):
            path_text += costs.list_items * length
            # Every index in a list counts at the width of the largest.
            item_length = length + len(str(len(value))) + 1
            path_text += item_length * len(value)
            for item in value:
                measure_item(item, item_length)
        if id(value) in total.sized:
            size = size_before
        total.sized.add(id(value))
    return path_text, size


def _json_text_paths(text: str, length: int, costs: _ModelCosts) -> int:
    """
    Return about how much path text a ``Json`` field could make from ``text``.

    This counts tokens and parses nothing but each string, so it needs no
    agreement with Pydantic's parser: a repeated key counts each time, any
    depth is fine, and text no parser accepts just costs a little more. Each
    item costs the length of the path it sits at, each string adds its own
    length, and each bracket counts its path once per required field. A
    string can hold more ``Json`` text, which counts the same way. Every such
    level doubles the escapes the text needs, so a long string has few levels
    and this reads the text only a few times.
    """
    total = 0
    # The path length at each open bracket, and the last string seen, which
    # is the key when a bracket opens right after it. The lengths sit in a
    # compact array of machine ints, one per open bracket.
    lengths = array("q", [length])
    last_string = 0
    for token in _JSON_TOKEN.finditer(text):
        character = text[token.start()]
        if character == '"':
            # A string right after another is a value under that key.
            own_length = lengths[-1] + last_string + 1
            last_string = token.end() - token.start()
            total += lengths[-1] + last_string
            inner = _json_string_value(token.group())
            # A quote matters too: it can open a string that holds brackets
            # only after another level of decoding.
            if inner is not None and ("[" in inner or "{" in inner or '"' in inner):
                total += _json_text_paths(inner, own_length, costs)
        elif character == "[":
            lengths.append(lengths[-1] + last_string + 1)
            total += costs.list_items * lengths[-1]
            last_string = 0
        elif character == "{":
            lengths.append(lengths[-1] + last_string + 1)
            total += costs.object_fields * lengths[-1]
            last_string = 0
        elif character in "]}":
            if len(lengths) > 1:
                lengths.pop()
        else:
            total += lengths[-1]
            last_string = 0
    return total


def _json_string_value(token: str) -> str | None:
    """Return the text a JSON string token stands for, or ``None`` when it is not a valid string."""
    # No parser reads inside a string that is not valid, and the raw token
    # has been counted.
    if len(token) < 2 or not token.endswith('"'):
        return None
    if "\\" not in token:
        return token[1:-1]
    try:
        return cast("str", json.loads(token, strict=False))
    except ValueError:
        return None


def _model_costs(schema_cls: type) -> _ModelCosts:
    """Return what a Pydantic model can add to its error paths, read once from its core schema."""
    cached = _MODEL_COSTS.get(schema_cls)
    if cached is not None:
        return cached
    # A class with an unresolved forward reference holds a stand-in schema.
    # Pydantic would rebuild it on the first call anyway, and that first call
    # must be measured against the real schema.
    rebuild = getattr(schema_cls, "model_rebuild", None)
    if not getattr(schema_cls, "__pydantic_complete__", True) and rebuild is not None:
        rebuild(raise_errors=False)
    costs = _read_model_costs(schema_cls)
    if getattr(schema_cls, "__pydantic_complete__", True):
        _MODEL_COSTS[schema_cls] = costs
    return costs


def _read_model_costs(schema_cls: type) -> _ModelCosts:
    # A Pydantic v1 model has no core schema, and it holds each error's
    # location as a tuple of the same key objects, so its errors copy no
    # key text.
    root = getattr(schema_cls, "__pydantic_core_schema__", None)
    pending: list[Any] = [root]
    parses_json = False
    object_fields = 0
    list_items = 0
    # Maps each definition's name to its schema, so a reference can find it.
    definitions: dict[str, dict[str, Any]] = {}
    # An author's own metadata in the schema can hold itself.
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        # The stand-in schema is a Mapping but not a dict, and is not walked.
        if type(node) is dict:
            parses_json = parses_json or node.get("type") == "json"
            fields = _required_entries(node, "fields")
            object_fields = max(object_fields, fields)
            # A NamedTuple reads a list or an object, and either one reports
            # each position it lacks.
            if node.get("type") == "named-tuple":
                list_items = max(list_items, fields)
            positions = _required_entries(node, "arguments_schema")
            object_fields = max(object_fields, positions)
            list_items = max(list_items, positions)
            # A homogeneous list keeps one schema here, not a list of them.
            if type(node.get("items_schema")) is list:
                list_items = max(list_items, _required_entries(node, "items_schema"))
            if isinstance(node.get("ref"), str):
                definitions[node["ref"]] = node
            pending.extend(node.values())
        elif type(node) in (list, tuple):
            pending.extend(node)
    return _ModelCosts(parses_json, object_fields, list_items, _reports_per_value(root, definitions))


def _reports_per_value(root: Any, definitions: dict[str, dict[str, Any]]) -> int:
    """
    Return how many times one bad value can be reported under a core schema node.

    A union without a discriminator reports once per member, so its members
    add up, and nested unions add up inside that. A tagged union reports one
    member. The walk stops at a definition it has already entered, which ends
    the walk on a recursive schema. The walk uses its own stack, because a
    schema of nested models can be deeper than Python's recursion limit, and
    a failure here would fail every call to the model.
    """
    # A node on the way down holds 1, so a reference back to it counts once.
    known: dict[int, int] = {}
    # False to enter a node, True to add up its children.
    stack: list[tuple[Any, bool]] = [(root, False)]
    while stack:
        node, leaving = stack.pop()
        if leaving:
            reports = [known.get(id(child), 1) for child in _schema_children(node, definitions)]
            is_union = type(node) is dict and node.get("type") == "union"
            known[id(node)] = sum(reports) if is_union else max(reports, default=1)
        elif type(node) in (dict, list, tuple) and id(node) not in known:
            known[id(node)] = 1
            stack.append((node, True))
            stack.extend((child, False) for child in _schema_children(node, definitions))
    return known.get(id(root), 1)


def _schema_children(node: Any, definitions: dict[str, dict[str, Any]]) -> list[Any]:
    """Return what a core schema node leads to: its members for a union, the definition for a reference."""
    if type(node) is not dict:
        return list(node)
    if node.get("type") == "definition-ref":
        return [definitions.get(node.get("schema_ref", ""))]
    if node.get("type") == "union":
        return list(node.get("choices", ()))
    return list(node.values())


def _required_entries(node: dict[str, Any], name: str) -> int:
    """Return how many required entries a core schema node holds under ``name``."""
    # Model and TypedDict fields are a dict and dataclass fields a list. A
    # fixed tuple keeps its positions under `items_schema`, and a NamedTuple
    # under `fields` or `arguments_schema`.
    fields = node.get(name)
    if not isinstance(fields, (dict, list)):
        return 0
    entries = fields.values() if isinstance(fields, dict) else fields
    return sum(1 for entry in entries if _is_required_entry(entry))


def _is_required_entry(entry: Any) -> bool:
    if type(entry) is not dict or entry.get("required") is False:
        return False
    # A field with a default wraps its schema in a `default` node, and a
    # tuple position is the schema itself.
    schema = entry.get("schema", entry)
    return type(schema) is dict and schema.get("type") != "default"


def pydantic_container_paths(
    model_cls: type, locations: Iterable[Sequence[Any]], parent: Any, shared: dict[tuple[int, Any], Any]
) -> list[Any]:
    """
    Return the field paths of the list and dict fields that Pydantic error locations pass through.

    Pydantic reports a list item as ``("tags", 3)``, so a whole-number part
    always means the parts before it are a list. A dict value is
    ``("scores", "alice")``, where the location alone cannot tell a dict key
    from a field name, so those are found by walking the model's
    annotations along the location. The walk follows field names and
    aliases, ``Optional`` and ``Annotated``, and the member tag Pydantic
    adds for a union with exactly one dict member; anything else ends it.

    The paths are made under ``parent`` from the pairs in ``shared``, which
    :func:`shared_location_path` also uses, and each container is returned
    once.
    """
    containers: list[Any] = []
    returned: set[int] = set()
    # Many locations share one shape (rows.0.x, rows.1.x, ...), so the walk
    # runs once per shape, with list indexes replaced by a marker.
    walked: dict[tuple[Any, ...], tuple[int, ...]] = {}
    for location in locations:
        shape = tuple(_INDEX if isinstance(part, int) else part for part in location)
        depths = walked.get(shape)
        if depths is None:
            depths = walked[shape] = _container_depths(model_cls, shape)
        # A deep location passes through a container at many depths, so the
        # path is extended from one depth to the next. Building each
        # container's path from the start would read the location once per
        # container, which grows with the square of its depth.
        path = parent
        reached = 0
        for depth in depths:
            path = shared_location_path(path, location[reached:depth], shared)
            reached = depth
            # Depth 0 is the model itself, which is no list or dict field.
            if depth == 0:
                continue
            if id(path) not in returned:
                returned.add(id(path))
                containers.append(path)
    return containers


# Stands in for a list index in a location shape.
_INDEX = object()


def _container_depths(model_cls: type, shape: tuple[Any, ...]) -> tuple[int, ...]:
    """Return how many leading parts of ``shape`` name each list or dict it passes through."""
    depths = {depth for depth, part in enumerate(shape) if part is _INDEX}
    annotation: Any = model_cls
    for depth, part in enumerate(shape):
        annotation = _single_shape(annotation)
        origin = get_origin(annotation)
        # A Pydantic v1 State reports its errors by the same paths as a v2 class.
        is_model = _is_pydantic_model(annotation) or bounded.is_pydantic_v1_class(annotation)
        if isinstance(annotation, type) and is_model:
            annotation = _pydantic_field_annotation(annotation, part)
        elif origin in (list, tuple, set, frozenset) or origin is Sequence:
            args = get_args(annotation)
            # Only a homogeneous container holds as many items as the request sends.
            annotation = args[0] if args and (origin is not tuple or args[-1] is Ellipsis) else None
        elif origin is dict or origin is Mapping:
            depths.add(depth)
            args = get_args(annotation)
            annotation = args[1] if len(args) == 2 else None
        elif origin in (Union, UnionType) and isinstance(part, str):
            # Pydantic names the union member it tried; a single dict member
            # is the only one this walk can identify from that tag alone.
            dicts = [arg for arg in get_args(annotation) if get_origin(_single_shape(arg)) in (dict, Mapping)]
            annotation = dicts[0] if len(dicts) == 1 else None
            continue
        else:
            break
        if annotation is None:
            break
    return tuple(sorted(depths))


def _single_shape(annotation: Any) -> Any:
    """Unwrap ``Annotated`` and ``Optional``; a union of several shapes is returned as is."""
    while get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]
    if get_origin(annotation) in (Union, UnionType):
        options = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(options) == 1:
            return _single_shape(options[0])
    return annotation


def _pydantic_field_annotation(model_cls: type, name: Any) -> Any:
    """Return the annotation of the Pydantic v2 or v1 field that ``name`` or its alias names, or ``None``."""
    fields = getattr(model_cls, "model_fields", None)
    if isinstance(fields, Mapping):
        # An error location uses the key the payload sent, which may be an alias.
        field = fields.get(name) or next(
            (info for info in fields.values() if name in _pydantic_input_names(info)), None
        )
        return None if field is None else field.annotation
    # Pydantic v1 keeps the full annotation, list[int] for example, as outer_type_.
    v1_fields = getattr(model_cls, "__fields__", {})
    field = v1_fields.get(name) or next((info for info in v1_fields.values() if info.alias == name), None)
    return None if field is None else field.outer_type_


def _is_pydantic_model(schema_cls: type) -> bool:
    """Whether ``schema_cls`` is a Pydantic v2 model (always ``False`` without Pydantic installed)."""
    return pydantic is not None and isinstance(schema_cls, type) and issubclass(schema_cls, pydantic.BaseModel)


def _is_pydantic_dataclass(schema_cls: type) -> bool:
    """Whether ``schema_cls`` is a dataclass that Pydantic checks when it is built."""
    return pydantic is not None and pydantic.dataclasses.is_pydantic_dataclass(schema_cls)


################################################
# VALUE COERCION
################################################


def _coerce(value: Any, annotation: Any, path: Any, errors: FieldErrors, *, bind_strings: bool) -> Any:
    """
    Coerce one payload value to its annotated type.

    Returns the coerced value, or ``_INVALID`` after recording a message for
    ``path`` in ``errors``. Only the module's coercion table applies (plus,
    with ``bind_strings``, the string-transport rule for ``int`` / ``float``
    / ``bool``); anything else is a mismatch.
    """
    if annotation is Any or annotation is object:
        return value

    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        return _coerce_union(value, annotation, path, errors, bind_strings=bind_strings)
    if origin is Literal:
        return _coerce_literal(value, annotation, path, errors, bind_strings=bind_strings)
    # A bare typing alias (``typing.List``, ``typing.Tuple``) says nothing
    # about its items, so it is checked as the plain container. Only the
    # builtin ``tuple[()]`` has no arguments and still declares a shape.
    if origin in (list, tuple, set) and not get_args(annotation) and not isinstance(annotation, GenericAlias):
        return _coerce(value, origin, path, errors, bind_strings=bind_strings)
    if origin in (list, tuple, set):
        return _coerce_container(value, annotation, origin, path, errors, bind_strings=bind_strings)
    if origin is dict or origin is Mapping:
        expected = dict if origin is dict else Mapping
        if isinstance(value, expected):
            return _coerce_mapping(value, annotation, path, errors, bind_strings=bind_strings)
        return _fail(errors, path, f"Expected an object, got {_value_type_name(value)}.")
    if origin is not None:
        return _fail(errors, path, f"Unsupported annotation for event data: {_type_name(annotation)}.")

    if annotation is type(None):
        if value is None:
            return None
        return _fail(errors, path, f"Expected null, got {_value_type_name(value)}.")
    if not isinstance(annotation, type):
        return _fail(errors, path, f"Unsupported annotation for event data: {annotation!r}.")

    # The four JSON primitives, by identity: an Enum or user subclass of one
    # of these must not match here (IntEnum subclasses int).
    if annotation is bool:
        # No 0/1 or "true" coercion from JSON: bool is its own JSON type.
        # The string transports have no bool type at all, so there the HTML
        # form vocabulary binds instead (design 3.3).
        if isinstance(value, bool):
            return value
        if bind_strings and isinstance(value, str):
            if value in _BOOL_STRINGS:
                return _BOOL_STRINGS[value]
            return _fail(errors, path, f"Not a valid bool: {_short_repr(value)}; {_BOOL_STRINGS_MESSAGE}.")
        return _fail(errors, path, _mismatch("bool", value))
    if annotation is int:
        # ``bool`` subclasses ``int`` in Python but not in JSON; reject it.
        if isinstance(value, bool):
            return _fail(errors, path, _mismatch("int", value))
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            return _fail(errors, path, "Expected int, got a float with a fractional part.")
        if bind_strings and isinstance(value, str):
            # Python's own int() grammar on purpose (signs, surrounding
            # whitespace, digit-grouping underscores): the lenient shapes a
            # typed-into-an-input value takes. The schema tests lock it.
            try:
                return int(value)
            except ValueError:
                return _fail(errors, path, f"Not a valid int: {_short_repr(value)}.")
        return _fail(errors, path, _mismatch("int", value))
    if annotation is float:
        if isinstance(value, bool):
            return _fail(errors, path, _mismatch("float", value))
        if isinstance(value, float):
            # The JSON codecs already reject non-finite numbers at parse
            # (codecs.py); this guards payloads a user codec built directly,
            # so inf / nan never reach a handler from any transport.
            if not math.isfinite(value):
                return _fail(errors, path, f"Expected a finite float, got {value!r}.")
            return value
        if isinstance(value, int):
            # JSON ints are unbounded; Python floats are not.
            try:
                return float(value)
            except OverflowError:
                return _fail(errors, path, "Expected float, got an int too large for a float.")
        if bind_strings and isinstance(value, str):
            # Python's own float() grammar (signs, whitespace, underscores,
            # exponents), minus the non-finite spellings: "inf" / "nan"
            # would bind a value the JSON result envelope cannot carry, and
            # one that strict JSON binding could never produce.
            try:
                parsed = float(value)
            except ValueError:
                return _fail(errors, path, f"Not a valid float: {_short_repr(value)}.")
            if not math.isfinite(parsed):
                return _fail(errors, path, f"Not a valid float: {_short_repr(value)}.")
            return parsed
        return _fail(errors, path, _mismatch("float", value))
    if annotation is str:
        if isinstance(value, str):
            return value
        return _fail(errors, path, _mismatch("str", value))

    # Bare (unparametrized) containers: check the shape, convert list to
    # tuple/set, take elements as-is.
    if annotation is list:
        if isinstance(value, list):
            return value
        return _fail(errors, path, f"Expected a list, got {_value_type_name(value)}.")
    if annotation is tuple:
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return _fail(errors, path, f"Expected a list, got {_value_type_name(value)}.")
    if annotation is set:
        if isinstance(value, (list, set)):
            # Wire lists may carry unhashable elements (objects, arrays).
            try:
                return set(value)
            except TypeError:
                return _fail(errors, path, "Set items must be hashable.")
        return _fail(errors, path, f"Expected a list, got {_value_type_name(value)}.")
    if annotation is dict:
        if isinstance(value, dict):
            return value
        return _fail(errors, path, f"Expected an object, got {_value_type_name(value)}.")

    if issubclass(annotation, Enum):
        if isinstance(value, annotation):
            return value
        if isinstance(value, str):
            try:
                return annotation(value)  # by enum value
            except ValueError:
                return _fail(errors, path, f"Not a valid {annotation.__name__}: {_short_repr(value)}.")
        return _fail(errors, path, _mismatch(annotation.__name__, value))
    if issubclass(annotation, UUID):
        if isinstance(value, annotation):
            return value
        if isinstance(value, str):
            try:
                return annotation(value)
            except ValueError:
                return _fail(errors, path, f"Not a valid UUID: {_short_repr(value)}.")
        return _fail(errors, path, _mismatch("UUID", value))
    # ``datetime`` before ``date``: datetime subclasses date.
    if issubclass(annotation, datetime):
        return _coerce_isoformat(value, annotation, path, errors)
    if issubclass(annotation, date):
        return _coerce_isoformat(value, annotation, path, errors)
    if issubclass(annotation, time):
        return _coerce_isoformat(value, annotation, path, errors)
    if issubclass(annotation, Decimal):
        if isinstance(value, annotation):
            if not value.is_finite():
                return _fail(errors, path, f"Not a valid Decimal: {value!r}.")
            return value
        # From strings only: JSON floats would defeat the point of Decimal.
        if isinstance(value, str):
            try:
                parsed_decimal = annotation(value)
            except InvalidOperation:
                return _fail(errors, path, f"Not a valid Decimal: {_short_repr(value)}.")
            # Decimal's own grammar also reads "Infinity" / "NaN" / "sNaN";
            # like the non-finite float spellings, they would bind a value
            # the JSON result envelope cannot carry, so they answer the
            # same per-field error.
            if not parsed_decimal.is_finite():
                return _fail(errors, path, f"Not a valid Decimal: {_short_repr(value)}.")
            return parsed_decimal
        return _fail(errors, path, _mismatch("Decimal", value))
    if issubclass(annotation, UploadedFile):
        if isinstance(value, annotation):
            return value
        return _fail(errors, path, _FILE_MESSAGE)

    # A TypedDict is a plain dict at runtime and isinstance() refuses it, so
    # an object passes as it came, with its keys unchecked. This runs before
    # the annotated-class branch below, which would also match a TypedDict.
    # typing_extensions also recognizes its own TypedDict, which Pydantic
    # asks for on Python 3.11.
    if typing_extensions.is_typeddict(annotation):
        if isinstance(value, Mapping):
            return value
        return _fail(errors, path, f"Expected an object, got {_value_type_name(value)}.")

    # Citry cannot check a browser value against a Protocol without
    # @runtime_checkable, which isinstance() refuses, so the field is
    # reported as unsupported. This runs before the annotated-class branch,
    # which would also match a Protocol that annotates attributes.
    if _is_unchecked_protocol(annotation):
        return _fail(errors, path, f"Unsupported annotation for event data: {_type_name(annotation)}.")

    # A nested annotated class validates recursively from an object.
    if _is_schema_class(annotation):
        if isinstance(value, annotation):
            return value
        if isinstance(value, Mapping):
            return _validate_object(annotation, value, path, errors, bind_strings=bind_strings)
        return _fail(errors, path, f"Expected an object, got {_value_type_name(value)}.")

    # Any other class: accept an instance (values constructed server-side),
    # coerce nothing.
    try:
        matches = isinstance(value, annotation)
    except TypeError:
        # Citry cannot check a browser value against a class whose
        # isinstance() raises (an unusual metaclass), so the field is
        # reported as unsupported.
        return _fail(errors, path, f"Unsupported annotation for event data: {_type_name(annotation)}.")
    if matches:
        return value
    return _fail(errors, path, _mismatch(_type_name(annotation), value))


def _coerce_isoformat(value: Any, annotation: type, path: Any, errors: FieldErrors) -> Any:
    """Coerce a ``datetime`` / ``date`` / ``time`` field from an ISO-format string."""
    if isinstance(value, annotation):
        return value
    if isinstance(value, str):
        try:
            return annotation.fromisoformat(value)  # type: ignore[attr-defined]
        except ValueError:
            return _fail(errors, path, f"Not a valid {annotation.__name__}: {_short_repr(value)}.")
    return _fail(errors, path, _mismatch(annotation.__name__, value))


def _coerce_union(value: Any, annotation: Any, path: Any, errors: FieldErrors, *, bind_strings: bool) -> Any:
    """Coerce a union-annotated value: ``None`` when allowed, else the first member that fits."""
    members = get_args(annotation)
    non_none = [member for member in members if member is not type(None)]
    if value is None and len(non_none) < len(members):
        return None
    if len(non_none) == 1:
        # Optional[X]: the member's own message (and nested paths) apply directly.
        return _coerce(value, non_none[0], path, errors, bind_strings=bind_strings)
    # A union inside another union's attempt is checked again for each member
    # of the outer one. Each second or later attempt at a value there spends
    # from the request's work budget for that value, twice: once for itself
    # and once for the failed attempt before it, which spent nothing. A union
    # outside any other, or a first attempt, adds work in step with the data
    # only.
    budget = bounded.current_work()
    spends = budget is not None and budget.union_depth > 0
    if budget is not None:
        budget.union_depth += 1
    # Every check inside such a union may run again, so the Pydantic classes
    # checked there spend for the text they parse, as in a Pydantic tree.
    repeated = bounded.repeated_checks() if spends else contextlib.nullcontext()
    try:
        with repeated:
            coerced = _coerce_members(
                value, non_none, path, errors, budget if spends else None, bind_strings=bind_strings
            )
        if coerced is not _INVALID:
            return coerced
    finally:
        if budget is not None:
            budget.union_depth -= 1
    names = " or ".join(_type_name(member) for member in non_none)
    return _fail(errors, path, f"Expected {names}, got {_value_type_name(value)}.")


def _coerce_members(
    value: Any,
    members: list[Any],
    path: Any,
    errors: FieldErrors,
    spending: bounded.WorkBudget | None,
    *,
    bind_strings: bool,
) -> Any:
    """Return what the first union member that fits gives, or ``_INVALID``; ``spending`` charges later attempts."""
    for attempt, member in enumerate(members):
        if spending is not None and attempt:
            # Citry's own check runs in Python, so each value costs more,
            # and a list or dict about as much as a number.
            spending.spend_on(value, 2 * bounded.CITRY_CHECK_STEPS, container_values=1)
        scratch = FieldErrors(shares_total_with=errors)
        try:
            # A failed member's messages are thrown away, so they leave the
            # error total too, and a member with too many errors fails on
            # its own while the next member still runs.
            with bounded.discarded_errors():
                coerced = _coerce(value, member, path, scratch, bind_strings=bind_strings)
        except bounded.ValidationTooCostly as stop:
            if stop.reason != "errors":
                raise
            coerced = _INVALID
        if coerced is not _INVALID:
            return coerced
    return _INVALID


def _coerce_literal(value: Any, annotation: Any, path: Any, errors: FieldErrors, *, bind_strings: bool) -> Any:
    """Coerce a ``Literal[...]`` value: it must equal one of the listed values, with that value's type."""
    members = get_args(annotation)
    for member in members:
        # The wire carries an Enum member as its value, so the value is what
        # the payload must match, read by the value's own type.
        expected = member.value if isinstance(member, Enum) else member
        # Each listed value is read by its own type's rule, so a form post's
        # "2" still binds to `Literal[1, 2]`, as for a plain field of that type.
        scratch = FieldErrors()
        coerced = _coerce(value, type(expected), path, scratch, bind_strings=bind_strings)
        # Python counts True == 1, so the type is compared too: JSON keeps
        # `true` and `1` apart, and so does the field.
        if coerced is not _INVALID and type(coerced) is type(expected) and coerced == expected:
            return member
    # Values are shown as the browser writes them, an Enum member by its value.
    listed = ", ".join(_literal_value_text(member.value if isinstance(member, Enum) else member) for member in members)
    return _fail(errors, path, f"Expected one of {listed}, got {_literal_value_text(value)}.")


def _literal_value_text(value: Any) -> str:
    """Show a scalar itself, in JSON spelling, so a wrong choice reads as that choice; anything else by its type."""
    if isinstance(value, str):
        return _short_repr(value)
    if isinstance(value, bool) or value is None:
        return _value_type_name(value) if value is None else str(value).lower()
    if isinstance(value, (int, float)):
        return repr(value)
    return _value_type_name(value)


def _coerce_container(
    value: Any, annotation: Any, origin: type, path: Any, errors: FieldErrors, *, bind_strings: bool
) -> Any:
    """Coerce a parametrized ``list`` / ``tuple`` / ``set`` field, element by element."""
    args = get_args(annotation)

    # What shapes may carry the value in: lists always (the wire form), plus
    # the target's own type for values constructed server-side.
    if origin is tuple:
        shape_ok = isinstance(value, (list, tuple))
    elif origin is set:
        shape_ok = isinstance(value, (list, set))
    else:
        shape_ok = isinstance(value, list)
    if not shape_ok:
        return _fail(errors, path, f"Expected a list, got {_value_type_name(value)}.")

    # Fixed-shape tuples (``tuple[int, str]``) coerce per position; everything
    # else is homogeneous with one element type.
    if origin is tuple and len(args) == 2 and args[1] is Ellipsis:
        element_annotations: list[Any] = [args[0]] * len(value)
    elif origin is tuple:
        if len(value) != len(args):
            return _fail(errors, path, f"Expected a list of {len(args)} items, got {len(value)}.")
        element_annotations = list(args)
    else:
        element_annotations = [args[0]] * len(value)

    errors.add_container(path)
    items = []
    for index, (item, element_annotation) in enumerate(zip(value, element_annotations, strict=True)):
        coerced = _coerce(item, element_annotation, (path, index), errors, bind_strings=bind_strings)
        if coerced is _INVALID:
            # The payload decides how many items it sends, so the list stops
            # at its first bad item, as a Pydantic list does in Citry's copy.
            return _INVALID
        items.append(coerced)
    if origin is tuple:
        return tuple(items)
    if origin is set:
        try:
            return set(items)
        except TypeError:
            return _fail(errors, path, "Set items must be hashable.")
    return items


def _coerce_mapping(
    value: Mapping[Any, Any], annotation: Any, path: Any, errors: FieldErrors, *, bind_strings: bool
) -> Any:
    """Coerce a parametrized ``dict`` / ``Mapping`` field, key by key and value by value."""
    args = get_args(annotation)
    if len(args) != 2:
        return value
    key_annotation, value_annotation = args
    # A `str`, `Any`, or `object` key with an `Any` or `object` value needs
    # no conversion, so the object passes as it came.
    if key_annotation in (str, Any, object) and value_annotation in (Any, object):
        return value

    errors.add_container(path)
    items: dict[Any, Any] = {}
    for key, item in value.items():
        item_path = (path, key)
        # A JSON object key is always a string, as a form value is, so the
        # key binds by the string-transport rule: "3" fills a `dict[int, ...]`.
        # The key's own message is replaced by the "Invalid key" message
        # below, so it comes off the error total too.
        key_errors = FieldErrors()
        with bounded.discarded_errors():
            coerced_key = _coerce(key, key_annotation, item_path, key_errors, bind_strings=True)
        if coerced_key is _INVALID:
            # The dict stops at its first bad item, as a list does.
            return _fail(errors, item_path, f"Invalid key: {key_errors.first_message() or 'Invalid value.'}")
        coerced = _coerce(item, value_annotation, item_path, errors, bind_strings=bind_strings)
        if coerced is _INVALID:
            return _INVALID
        items[coerced_key] = coerced
    return items


################################################
# MESSAGE HELPERS
################################################


def _fail(errors: FieldErrors, path: Any, message: str) -> Any:
    """Record the message for ``path``, count it toward the validation's error limit, and return the invalid marker."""
    errors.add(path, message)
    bounded.count_errors()
    return _INVALID


def _mismatch(expected: str, value: Any) -> str:
    return f"Expected {expected}, got {_value_type_name(value)}."


def _value_type_name(value: Any) -> str:
    """The received value's type, in wire language (``None`` reads as ``null``)."""
    if value is None:
        return "null"
    return type(value).__name__


def _type_name(annotation: Any) -> str:
    """A readable name for an annotation, for error messages."""
    if annotation is type(None):
        return "null"
    if get_origin(annotation) is not None:
        return generic_label(annotation)
    return getattr(annotation, "__name__", str(annotation))


def generic_label(hint: Any) -> str:
    """Write a parametrized type by its short names (``dict[str, Point]``), without module paths."""
    origin = get_origin(hint)
    if origin is Union or origin is UnionType:
        return " | ".join(generic_label(arm) for arm in get_args(hint))
    if origin is None:
        if hint is type(None):
            return "None"
        if hint is Ellipsis:
            return "..."
        name = getattr(hint, "__name__", None)
        return name if isinstance(name, str) else str(hint).replace("typing.", "")
    args = get_args(hint)
    if origin is Literal:
        inner = ", ".join(repr(arg.value if isinstance(arg, Enum) else arg) for arg in args)
        return f"Literal[{inner}]"
    # Annotated metadata and other special forms read best as Python writes them.
    if not isinstance(origin, type):
        return str(hint).replace("typing.", "")
    # A bare typing alias (``typing.Tuple``) reads as its container, while
    # the builtin ``tuple[()]`` has no arguments but keeps its brackets.
    if not args and not isinstance(hint, GenericAlias):
        return origin.__name__
    inner = ", ".join(generic_label(arg) for arg in args) if args else "()"
    return f"{origin.__name__}[{inner}]"


def _is_unchecked_protocol(annotation: Any) -> bool:
    """Whether ``annotation`` is a Protocol without @runtime_checkable, which isinstance() refuses."""
    return bool(getattr(annotation, "_is_protocol", False)) and not getattr(annotation, "_is_runtime_protocol", False)


def _short_repr(value: str) -> str:
    """The value's repr, truncated so a huge payload string cannot flood the message."""
    return repr(value if len(value) <= 60 else value[:57] + "...")
