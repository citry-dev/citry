"""
Data schemas of the ``events`` extension: conversion, validation, coercion.

A handler's ``data`` parameter is annotated with a schema class, and the
whole wire ``args`` payload is validated against it before the handler runs.
This module owns that machinery: the class-side conversion (a plain annotated
class gets the same dataclass treatment as ``State``; a dataclass is used
as-is; a Pydantic model is delegated wholesale to Pydantic), and the payload
validation with its deliberately small coercion table. Validation returns a
structured :class:`ValidationResult` rather than raising, so the dispatcher
can map failures onto the per-field 422 error object. Design:
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

import math
import threading
from collections.abc import Mapping
from dataclasses import MISSING, dataclass, fields
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import UnionType
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Union, get_args, get_origin, get_type_hints
from uuid import UUID

from citry._nested_declarations import _is_plain_field_family, convert_plain_declaration
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
            elements ``"tags.1"``). Sorted by field path, so the error
            object is deterministic. Empty when validation succeeded.

    """

    value: Any
    fields: dict[str, str]

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
            " Pydantic v1 model, because Events validation reads Pydantic v2 models only. Decorate it with"
            " @dataclass to keep it a dataclass, or set model_base to a Pydantic v2 model."
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
    a Pydantic-model schema is validated by Pydantic wholesale (its own
    rules, its own messages).

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
        field path. A schema ``__post_init__`` (or Pydantic validator) that
        raises something other than a validation error propagates to the
        caller.

    """
    if bind_strings is None:
        bind_strings = isinstance(args, StringArgs)
    errors: dict[str, str] = {}
    if not isinstance(args, Mapping):
        errors[""] = f"Expected an object, got {_value_type_name(args)}."
        return ValidationResult(value=None, fields=errors)
    instance = _validate_object(schema_cls, args, "", errors, bind_strings=bind_strings)
    if instance is _INVALID:
        return ValidationResult(value=None, fields=dict(sorted(errors.items())))
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


def declared_field_names(schema_cls: type) -> frozenset[str]:
    """
    Return the field names a ``data`` class takes from the wire, without resolving its annotations.

    The dispatcher reads this before it drops the host's CSRF fields from a
    call, so a class that declares such a field still receives it. A
    Pydantic model's field aliases count too, because Pydantic reads a
    payload key by its alias.
    """
    if _is_pydantic_model(schema_cls):
        # ``model_fields`` is Pydantic v2; ``__fields__`` the v1 spelling.
        model_fields = getattr(schema_cls, "model_fields", None) or getattr(schema_cls, "__fields__", {})
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
    errors: dict[str, str] = {}
    if _coerce(value, annotation, "", errors, bind_strings=bind_strings) is not _INVALID:
        return None
    return next(iter(errors.values()), None)


def _validate_object(
    schema_cls: type,
    mapping: Mapping[str, Any],
    prefix: str,
    errors: dict[str, str],
    *,
    bind_strings: bool,
) -> Any:
    """
    Validate one payload object against one schema class.

    Records failures in ``errors`` under ``prefix``-ed field paths and
    returns the schema instance, or ``_INVALID`` when anything in this
    object's subtree failed.
    """
    if _is_pydantic_model(schema_cls):
        return _validate_pydantic(schema_cls, mapping, prefix, errors)

    converted, specs = _schema_info(schema_cls)
    accepted = {spec.name for spec in specs}
    ok = True

    for key in mapping:
        if key not in accepted:
            errors.setdefault(prefix + str(key), _EXTRA_MESSAGE)
            ok = False

    values: dict[str, Any] = {}
    for spec in specs:
        if spec.name in mapping:
            coerced = _coerce(
                mapping[spec.name], spec.annotation, prefix + spec.name, errors, bind_strings=bind_strings
            )
            if coerced is _INVALID:
                ok = False
            else:
                values[spec.name] = coerced
        elif spec.required:
            errors.setdefault(prefix + spec.name, _REQUIRED_MESSAGE)
            ok = False

    if not ok:
        return _INVALID
    return converted(**values)


def _validate_pydantic(schema_cls: type, mapping: Mapping[str, Any], prefix: str, errors: dict[str, str]) -> Any:
    """Delegate one payload object to Pydantic, mapping its errors onto field paths."""
    # ``model_validate`` is Pydantic v2; ``parse_obj`` the v1 spelling.
    validate = getattr(schema_cls, "model_validate", None) or schema_cls.parse_obj  # type: ignore[attr-defined]
    try:
        return validate(dict(mapping))
    except pydantic.ValidationError as err:
        for entry in err.errors():
            location = ".".join(str(part) for part in entry["loc"])
            key = prefix + location if location else prefix.rstrip(".")
            errors.setdefault(key, str(entry["msg"]))
        return _INVALID
    except Exception:  # noqa: BLE001 - a validator's own bug must not escape the dispatcher
        # Pydantic turns only ValueError and AssertionError in a validator
        # into a ValidationError; another exception is the author's bug, and
        # answers this one call 422 rather than failing the whole envelope.
        logger.exception(f"A validator raised while checking event data for {schema_cls.__qualname__}.")
        errors.setdefault(prefix.rstrip(".") or "_args", "The value could not be checked.")
        return _INVALID


def _is_pydantic_model(schema_cls: type) -> bool:
    """Whether ``schema_cls`` is a Pydantic model (always ``False`` without Pydantic installed)."""
    return pydantic is not None and isinstance(schema_cls, type) and issubclass(schema_cls, pydantic.BaseModel)


################################################
# VALUE COERCION
################################################


def _coerce(value: Any, annotation: Any, path: str, errors: dict[str, str], *, bind_strings: bool) -> Any:
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
    if origin in (list, tuple, set):
        return _coerce_container(value, annotation, origin, path, errors, bind_strings=bind_strings)
    if origin is dict or origin is Mapping:
        # Object fields pass as-is; per-key coercion is not in the table.
        expected = dict if origin is dict else Mapping
        if isinstance(value, expected):
            return value
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

    # A nested annotated class validates recursively from an object.
    if _is_schema_class(annotation):
        if isinstance(value, annotation):
            return value
        if isinstance(value, Mapping):
            return _validate_object(annotation, value, path + ".", errors, bind_strings=bind_strings)
        return _fail(errors, path, f"Expected an object, got {_value_type_name(value)}.")

    # Any other class: accept an instance (values constructed server-side),
    # coerce nothing.
    if isinstance(value, annotation):
        return value
    return _fail(errors, path, _mismatch(_type_name(annotation), value))


def _coerce_isoformat(value: Any, annotation: type, path: str, errors: dict[str, str]) -> Any:
    """Coerce a ``datetime`` / ``date`` / ``time`` field from an ISO-format string."""
    if isinstance(value, annotation):
        return value
    if isinstance(value, str):
        try:
            return annotation.fromisoformat(value)  # type: ignore[attr-defined]
        except ValueError:
            return _fail(errors, path, f"Not a valid {annotation.__name__}: {_short_repr(value)}.")
    return _fail(errors, path, _mismatch(annotation.__name__, value))


def _coerce_union(value: Any, annotation: Any, path: str, errors: dict[str, str], *, bind_strings: bool) -> Any:
    """Coerce a union-annotated value: ``None`` when allowed, else the first member that fits."""
    members = get_args(annotation)
    non_none = [member for member in members if member is not type(None)]
    if value is None and len(non_none) < len(members):
        return None
    if len(non_none) == 1:
        # Optional[X]: the member's own message (and nested paths) apply directly.
        return _coerce(value, non_none[0], path, errors, bind_strings=bind_strings)
    for member in non_none:
        scratch: dict[str, str] = {}
        coerced = _coerce(value, member, path, scratch, bind_strings=bind_strings)
        if coerced is not _INVALID:
            return coerced
    names = " or ".join(_type_name(member) for member in non_none)
    return _fail(errors, path, f"Expected {names}, got {_value_type_name(value)}.")


def _coerce_literal(value: Any, annotation: Any, path: str, errors: dict[str, str], *, bind_strings: bool) -> Any:
    """Coerce a ``Literal[...]`` value: it must equal one of the listed values, with that value's type."""
    members = get_args(annotation)
    for member in members:
        # The wire carries an Enum member as its value, so the value is what
        # the payload must match, read by the value's own type.
        expected = member.value if isinstance(member, Enum) else member
        # Each listed value is read by its own type's rule, so a form post's
        # "2" still binds to `Literal[1, 2]`, as for a plain field of that type.
        scratch: dict[str, str] = {}
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
    value: Any, annotation: Any, origin: type, path: str, errors: dict[str, str], *, bind_strings: bool
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

    items = []
    ok = True
    for index, (item, element_annotation) in enumerate(zip(value, element_annotations, strict=True)):
        coerced = _coerce(item, element_annotation, f"{path}.{index}", errors, bind_strings=bind_strings)
        if coerced is _INVALID:
            ok = False
        else:
            items.append(coerced)
    if not ok:
        return _INVALID
    if origin is tuple:
        return tuple(items)
    if origin is set:
        try:
            return set(items)
        except TypeError:
            return _fail(errors, path, "Set items must be hashable.")
    return items


################################################
# MESSAGE HELPERS
################################################


def _fail(errors: dict[str, str], path: str, message: str) -> Any:
    """Record the first message for ``path`` and return the invalid marker."""
    errors.setdefault(path, message)
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
        return str(annotation).replace("typing.", "")
    return getattr(annotation, "__name__", str(annotation))


def _short_repr(value: str) -> str:
    """The value's repr, truncated so a huge payload string cannot flood the message."""
    return repr(value if len(value) <= 60 else value[:57] + "...")
