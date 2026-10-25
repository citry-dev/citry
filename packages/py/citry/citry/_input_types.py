"""
Check the outer type of each value a component receives against its annotation.

When a component renders, Citry builds its ``Kwargs`` (and ``TemplateData``,
``JsData``, ``CssData``, and ``State``) from plain values. This module checks
each field of the built object against the field's annotation and raises
``TypeError`` for a value of the wrong type, so ``Card(title=123)`` against
``title: str`` fails with a message that names the component and the field.

Only the outer type is checked: ``list[str]`` accepts any ``list`` and does not
look at the items, because checking every item would cost time in proportion
to the data on every render.

The first check of a schema class reads its annotations once and stores a
tuple of prepared field checks on the class. Each later check first compares
the value's exact type with a set of accepted types, which is much cheaper
than ``isinstance``, and runs the slower test only when that fails.
"""

from __future__ import annotations

import numbers
import re
import sys
import types
import typing
from abc import ABCMeta
from collections.abc import Callable as AbcCallable
from dataclasses import is_dataclass
from typing import TYPE_CHECKING, Any, ForwardRef, cast, get_args, get_origin
from weakref import WeakKeyDictionary

import typing_extensions

from citry._class_introspection import _static_class_dict, _static_class_namespace_copy
from citry._schema_introspection import _read_schema_fields
from citry.constness import (
    _is_const_marker,
    _schema_has_generated_dataclass_init,
    const_value,
)
from citry.secret import Secret

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry.component import Component

# The prepared checks live on the schema class itself.
_CHECKS_ATTR = "_citry_input_type_checks"

# A schema class that refuses a new class attribute keeps its checks here
# instead. Weak keys let a class defined inside a test or request go away.
_FALLBACK_CHECKS: WeakKeyDictionary[type, tuple[_FieldCheck, ...]] = WeakKeyDictionary()

# Remembering every passing type would keep classes alive and grow without
# bound for values such as ``Mock`` objects, which get a new class each.
_MAX_REMEMBERED_TYPES = 32

# A value shown in an error message is cut to this many characters, so a large
# list or a long string does not bury the message.
_MAX_VALUE_REPR = 80

_NONE_TYPE = type(None)

# Stands for an annotation that could not be evaluated. ``None`` cannot play
# this part, because ``x: None`` is a real annotation that accepts only None.
_UNRESOLVED = object()

# Annotation wrappers that only add metadata around the type to check.
_WRAPPER_ORIGINS: frozenset[object] = frozenset(
    {
        typing.Annotated,
        typing.ClassVar,
        typing.Final,
        typing_extensions.Annotated,
        typing_extensions.Final,
        typing_extensions.Required,
        typing_extensions.NotRequired,
        typing_extensions.ReadOnly,
    },
)

_UNION_ORIGINS: frozenset[object] = frozenset({typing.Union, types.UnionType})
_LITERAL_ORIGINS: frozenset[object] = frozenset({typing.Literal, typing_extensions.Literal})
_ANY_FORMS: frozenset[object] = frozenset({typing.Any, typing_extensions.Any, object})

# ``isinstance`` on a class whose metaclass uses one of these answers from the
# value's type alone, so a type that passed once can be accepted by the fast
# exact-type test from then on.
_TYPE_ONLY_INSTANCE_CHECKS = (type.__instancecheck__, ABCMeta.__instancecheck__)


class _Matcher:
    """
    The prepared test for one annotation.

    ``accepted`` holds exact types that pass without further work. It starts
    with the annotation's own classes and grows with each type that passed a
    ``type_tests`` entry, so a subclass such as ``Markup`` for ``str`` or a
    ``list`` for ``Sequence`` takes the fast path from its second use.
    ``value_tests`` depend on the value itself (``Literal``, ``type[X]``) and
    are never remembered by type.
    """

    __slots__ = ("accepted", "type_tests", "value_tests")

    def __init__(
        self,
        accepted: set[type],
        type_tests: tuple[Callable[[object], bool], ...] = (),
        value_tests: tuple[Callable[[object], bool], ...] = (),
    ) -> None:
        self.accepted = accepted
        self.type_tests = type_tests
        self.value_tests = value_tests

    def slow_match(self, value: object) -> bool:
        """Run the full tests for a value whose exact type is not yet accepted."""
        for test in self.type_tests:
            if test(value):
                value_type = type(value)
                # A proxy that reports another class through ``__class__``
                # passed because of what it wraps, not its own type, so only
                # an honest type is remembered.
                if len(self.accepted) < _MAX_REMEMBERED_TYPES and value.__class__ is value_type:
                    self.accepted.add(value_type)
                return True
        return any(test(value) for test in self.value_tests)

    def accepts_now(self, value: object) -> bool:
        """Whether ``value`` passes, without remembering its type."""
        if type(value) in self.accepted:
            return True
        return any(test(value) for test in (*self.type_tests, *self.value_tests))


def _identity_test(default: object) -> Callable[[object], bool]:
    def is_default(value: object) -> bool:
        return value is default

    return is_default


class _FieldCheck(typing.NamedTuple):
    """One field's prepared check, unpacked in the render loop."""

    name: str
    accepted: set[type]
    matcher: _Matcher
    expected: str


def _check_input_types(
    instance: object,
    schema: type,
    component_class: type[Component],
    role: str,
) -> None:
    """
    Raise ``TypeError`` when a field of ``instance`` has the wrong outer type.

    ``instance`` is the final object built from ``schema``, after Citry has
    removed every ``Const`` marker, so the check sees the values the
    component's code will read. ``role`` names the schema in the error
    (``"Kwargs"``, ``"TemplateData"``, ...).
    """
    # The component's own Lint.check_input_types wins; None defers to its
    # Citry engine's LintSettings.
    enabled = component_class._citry_input_types
    if enabled is None:
        enabled = component_class.citry.settings.lint.check_input_types
    if not enabled:
        return

    for name, accepted, matcher, expected in _schema_checks_for(schema):
        value = getattr(instance, name, _MISSING)
        # The exact-type test answers almost every render; the rest only runs
        # for a subclass, an abstract annotation, or a wrong value.
        if type(value) in accepted or value is _MISSING:
            continue
        # State from state_data() can still hold a Const marker at this
        # point; the Events extension removes it later, so test the value
        # the marker stands for.
        if _is_const_marker(value):
            value = const_value(value)
            if type(value) in accepted:
                continue
        if not matcher.slow_match(value):
            _raise_type_error(component_class, role, _FieldCheck(name, accepted, matcher, expected), value)


class _MissingValue:
    """Marks a field that a schema's own code left unset."""


_MISSING = _MissingValue()


# How an expected-type label names Secret, such as `list[citry.secret.Secret[str]]`.
_SECRET_IN_LABEL = re.compile(r"\bSecret\b")


def _raise_type_error(
    component_class: type[Component],
    role: str,
    check: _FieldCheck,
    value: object,
) -> typing.NoReturn:
    """Raise the error that names the component, field, expected type, and value, and says what to do."""
    name, _accepted, matcher, expected = check
    type_name = _class_label(type(value))
    # Two different classes with the same name would read "expects Row, got
    # Row", so the module tells them apart.
    if type_name in expected.replace("|", " ").replace("[", " ").replace("]", " ").split():
        type_name = f"{type(value).__module__}.{type_name}"
    # The app's author cannot edit a library's annotations, so the advice
    # for a library component is about the value. This lookup runs only on
    # the error path.
    library = component_class.citry._library_name_of(component_class)
    library_note = ""
    if library is not None and role != "Kwargs":
        # A library data method usually built this value, but the default
        # template_data() and State built from Kwargs pass the app's input
        # through, so the message cannot tell whose value it is.
        library_note = (
            f" {component_class.__name__} comes from the component library {library!r}. If you passed this "
            "value as an input, pass one of the expected type; otherwise report it to that library."
        )
    if not matcher.type_tests and matcher.accepted <= {_NONE_TYPE} and matcher.value_tests:
        # Literal and type[...] fail on the value itself, so a wider type
        # would not help.
        fix = f"Use one of the values that {expected} allows."
    else:
        if library is None:
            verb = "Pass" if role == "Kwargs" else "Use"
            fix = f"{verb} a value of the expected type, or change the annotation to accept {type_name}."
        elif role == "Kwargs":
            fix = (
                f"{component_class.__name__} comes from the component library {library!r}, "
                "so pass a value of the expected type."
            )
        else:
            fix = ""
        if role == "Kwargs" and isinstance(value, str):
            # A plain template attribute always passes text.
            fix += f' In a template, write c-{name}="..." to pass a Python value instead of text.'
    shown = _short_repr(value)
    if Secret in matcher.accepted or _SECRET_IN_LABEL.search(expected):
        # The field expects a Secret, alone or inside a container such as
        # list[Secret[str]], but got a bare value, which is most likely the
        # secret itself. Error messages end up in logs and error pages, so
        # the message must not print it.
        shown = "value hidden"
    if Secret in matcher.accepted:
        type_name = _class_label(type(value))
        if role in {"Kwargs", "TemplateData"}:
            fix = (
                "Wrap the value where it is created, as Secret(value), so it shows as *** in templates, "
                "logs, and error messages."
            )
        else:
            # JsData, CssData, and State go to the browser, which never
            # receives a Secret, so wrapping the value would only move the error.
            fix = (
                f"Citry never sends a Secret to the browser, so a {role} field cannot hold one. Remove the "
                "field, and read the value on the server where you need it."
            )
    msg = f"{component_class.__name__}.{role}.{name} expects {expected}, got {type_name} ({shown})."
    if fix:
        msg += f" {fix.strip()}"
    msg += library_note
    raise TypeError(msg)


def _class_label(cls: type) -> str:
    """Name a class as its source does: ``None`` for NoneType, ``Card.Kwargs`` for a nested class."""
    if cls is _NONE_TYPE:
        return "None"
    qualname = getattr(cls, "__qualname__", None)
    # A class defined inside a function has "<locals>" in its qualified name,
    # which means nothing to the reader, so its plain name is used.
    if isinstance(qualname, str) and "<locals>" not in qualname:
        return qualname
    return cls.__name__


def _restore_json_tuples(instance: object, schema: type) -> None:
    """
    Turn a list back into a tuple for each field whose annotation accepts a tuple but not a list.

    Events State travels to the browser and back as JSON, which has no
    tuple, so a ``tuple[str, ...]`` field comes back as a list. Restoring the
    declared outer type keeps the handler, and any component it renders
    from the State, working with the type the field names.
    """
    for check in _schema_checks_for(schema):
        value = getattr(instance, check.name, _MISSING)
        if type(value) is list and check.matcher.accepts_now(()) and not check.matcher.accepts_now([]):
            object.__setattr__(instance, check.name, tuple(value))


def _short_repr(value: object) -> str:
    """Return a bounded ``repr`` that cannot itself fail the error message."""
    try:
        text = repr(value)
    except Exception:  # noqa: BLE001 - a broken __repr__ must not hide the type error
        return "<unprintable value>"
    if len(text) > _MAX_VALUE_REPR:
        return text[: _MAX_VALUE_REPR - 3] + "..."
    return text


def _schema_checks_for(schema: type) -> tuple[_FieldCheck, ...]:
    """Return the prepared checks for a schema class, preparing them on first use."""
    # Read the class's own namespace, so a subclass schema never reuses its
    # parent's list, which lacks the subclass's own fields.
    checks = schema.__dict__.get(_CHECKS_ATTR)
    if checks is None:
        return _schema_checks(schema)
    return cast("tuple[_FieldCheck, ...]", checks)


def _schema_checks(schema: type) -> tuple[_FieldCheck, ...]:
    """Prepare and store the field checks for one schema class."""
    fallback = _FALLBACK_CHECKS.get(schema)
    if fallback is not None:
        return fallback
    checks = _build_schema_checks(schema)
    try:
        type.__setattr__(schema, _CHECKS_ATTR, checks)
    except (AttributeError, TypeError):
        # A built-in or a class with a locked namespace keeps its checks
        # beside it instead.
        _FALLBACK_CHECKS[schema] = checks
    return checks


def _build_schema_checks(schema: type) -> tuple[_FieldCheck, ...]:
    """Read each field's annotation and prepare its check, skipping what cannot be checked."""
    if not _schema_is_checked(schema):
        return ()
    raw_fields = _read_schema_fields(schema)
    if raw_fields is None:
        return ()

    hints_by_owner: dict[type, dict[str, object] | None] = {}
    checks: list[_FieldCheck] = []
    for raw_field in raw_fields:
        owner = raw_field.declaring_class if raw_field.declaring_class is not None else schema
        annotation = _resolve_annotation(raw_field.name, raw_field.annotation, owner, hints_by_owner)
        matcher = _matcher_for(annotation)
        if matcher is None:
            continue
        # The author wrote the default, so it always passes. This keeps
        # ``x: str = None`` (common in code ported from django-components)
        # and ``tags: list[str] = ()`` working instead of failing every
        # render that leaves the field out. Only the default object itself
        # passes: another tuple for ``list[str]`` still fails.
        if raw_field.default_kind == "value":
            default = const_value(raw_field.default_value)
            if default is None:
                matcher.accepted.add(_NONE_TYPE)
            elif not matcher.accepts_now(default):
                matcher.value_tests = (*matcher.value_tests, _identity_test(default))
        checks.append(_FieldCheck(raw_field.name, matcher.accepted, matcher, _annotation_label(annotation)))
    return tuple(checks)


def _schema_is_checked(schema: type) -> bool:
    """Whether Citry, rather than the schema's own code, decides the field values."""
    # Pydantic models and Pydantic dataclasses check values themselves.
    if hasattr(schema, "__pydantic_validator__") or hasattr(schema, "__pydantic_fields__"):
        return False
    if isinstance(getattr(schema, "model_fields", None), dict) or isinstance(
        getattr(schema, "__fields__", None), dict
    ):
        return False
    if is_dataclass(schema):
        # A hand-written constructor takes over how values become fields.
        return _schema_has_generated_dataclass_init(schema)
    if issubclass(schema, tuple) and isinstance(getattr(schema, "_fields", None), tuple):
        return _has_generated_namedtuple_constructor(schema)
    return False


def _has_generated_namedtuple_constructor(schema: type) -> bool:
    """Whether ``collections.namedtuple`` wrote the constructor, rather than the schema's author."""
    constructor = _static_class_dict(schema).get("__new__")
    # The generated constructor is a staticmethod around a lambda compiled
    # from a string; a hand-written ``__new__`` is an ordinary function.
    function = constructor.__func__ if isinstance(constructor, staticmethod) else constructor
    code = getattr(function, "__code__", None)
    return code is not None and code.co_filename == "<string>" and code.co_name == "<lambda>"


def _resolve_annotation(
    name: str,
    annotation: object,
    owner: type,
    hints_by_owner: dict[type, dict[str, object] | None],
) -> object:
    """
    Evaluate one stored annotation in the module of the class that declares it.

    A field inherited from a base in another module must resolve its names
    there, not in the module of the component that uses it.
    """
    if type(annotation) is not str and not isinstance(annotation, ForwardRef):
        return annotation
    if owner not in hints_by_owner:
        try:
            # Resolves string annotations in the owner's module and namespace,
            # the same way type checkers read them.
            hints_by_owner[owner] = typing_extensions.get_type_hints(owner, include_extras=True)
        except Exception:  # noqa: BLE001 - one unresolvable name falls back to resolving fields alone
            hints_by_owner[owner] = None
    hints = hints_by_owner[owner]
    if hints is not None and name in hints:
        return hints[name]
    return _evaluate_alone(annotation, owner)


def _evaluate_alone(annotation: object, owner: type) -> object:
    """Evaluate one annotation by itself, or return ``_UNRESOLVED`` (unchecked) when it fails."""
    evaluate = getattr(annotation, "evaluate", None)
    if isinstance(annotation, ForwardRef) and callable(evaluate):
        # Python 3.14 forward references remember where they were written.
        try:
            return evaluate()
        except Exception:  # noqa: BLE001, S110 - fall through to the module lookup
            pass
    source = annotation if type(annotation) is str else cast("ForwardRef", annotation).__forward_arg__
    module = sys.modules.get(owner.__module__)
    # Copies, because an import or another thread may change these namespaces
    # while eval reads them.
    namespace = vars(module).copy() if module is not None else {}
    try:
        return eval(source, namespace, _static_class_namespace_copy(owner))  # noqa: S307 - the app's own annotation
    except Exception:  # noqa: BLE001 - a name only imported for type checkers leaves the field unchecked
        return _UNRESOLVED


def _matcher_for(annotation: object) -> _Matcher | None:
    """Return the prepared test for an annotation, or ``None`` when it cannot be checked at runtime."""
    try:
        return _matcher_for_inner(annotation)
    except Exception:  # noqa: BLE001 - an annotation Citry does not understand is left unchecked
        return None


def _matcher_for_inner(annotation: object) -> _Matcher | None:
    if annotation is None or annotation is _NONE_TYPE:
        return _Matcher({_NONE_TYPE})
    if annotation is _UNRESOLVED or annotation in _ANY_FORMS or type(annotation) is str:
        return None
    if isinstance(annotation, ForwardRef):
        return None

    origin = get_origin(annotation)
    if origin in _WRAPPER_ORIGINS:
        arguments = get_args(annotation)
        return _matcher_for_inner(arguments[0]) if arguments else None
    if origin in _UNION_ORIGINS:
        return _union_matcher(get_args(annotation))
    if origin in _LITERAL_ORIGINS:
        return _literal_matcher(get_args(annotation))
    if origin is type:
        return _class_object_matcher(get_args(annotation))
    if origin is AbcCallable:
        return _Matcher(set(), type_tests=(callable,))
    if origin is not None:
        # A generic alias such as ``type Pair[T] = tuple[T, T]`` used as
        # ``Pair[int]``: check the outer type the alias stands for.
        alias_value = _type_alias_value(origin)
        if alias_value is not None:
            return _matcher_for_inner(alias_value)
    if isinstance(origin, type):
        # ``list[str]``, ``dict[str, int]``, ``Sequence[Row]``: only the
        # outer class is checked, never the items.
        return _class_matcher(origin, promote_numbers=False)

    supertype = getattr(annotation, "__supertype__", None)
    if supertype is not None:
        # A NewType is its base type at runtime.
        return _matcher_for_inner(supertype)
    alias_value = _type_alias_value(annotation)
    if alias_value is not None:
        return _matcher_for_inner(alias_value)
    if isinstance(annotation, type):
        if typing_extensions.is_typeddict(annotation):
            return _Matcher({dict}, type_tests=(_isinstance_test(dict),))
        return _class_matcher(annotation, promote_numbers=True)
    # TypeVar, ParamSpec, Self, Never, LiteralString, Unpack, and other forms
    # that ``isinstance`` cannot take stay unchecked.
    return None


def _type_alias_value(annotation: object) -> object | None:
    """Return the aliased annotation of a ``type X = ...`` statement, or ``None``."""
    alias_types = tuple(
        alias_type
        for alias_type in (getattr(typing, "TypeAliasType", None), getattr(typing_extensions, "TypeAliasType", None))
        if isinstance(alias_type, type)
    )
    if alias_types and isinstance(annotation, alias_types):
        return cast("Any", annotation).__value__
    return None


def _union_matcher(members: tuple[object, ...]) -> _Matcher | None:
    """Accept a value that any member accepts; an unchecked member leaves the union unchecked."""
    accepted: set[type] = set()
    type_tests: list[Callable[[object], bool]] = []
    value_tests: list[Callable[[object], bool]] = []
    for member in members:
        matcher = _matcher_for_inner(member)
        if matcher is None:
            return None
        accepted.update(matcher.accepted)
        type_tests.extend(matcher.type_tests)
        value_tests.extend(matcher.value_tests)
    return _Matcher(accepted, tuple(type_tests), tuple(value_tests))


def _literal_matcher(members: tuple[object, ...]) -> _Matcher | None:
    """
    Accept a value equal to a member, of the member's type or a subclass of it.

    A ``StrEnum`` member or ``Markup("sm")`` passes for ``Literal["sm"]``, as
    a ``str`` subclass passes for ``str``, although a type checker rejects
    both. ``True`` never passes for ``Literal[1]``, and ``1`` never passes
    for ``Literal[True]``.
    """
    if not members:
        return None
    accepted: set[type] = {_NONE_TYPE} if None in members else set()
    values = tuple(member for member in members if member is not None)

    def equals_member(value: object) -> bool:
        for member in values:
            member_type = type(member)
            if type(value) is member_type:
                if value == member:
                    return True
                continue
            # bool is a subclass of int, but Literal keeps them apart both ways.
            if isinstance(value, bool) or member_type is bool:
                continue
            # Compare with the member type's own __eq__, so a subclass that
            # overrides __eq__ cannot pass for a member it does not equal.
            # `is True` also rejects NotImplemented, which str.__eq__ returns
            # for a proxy that only claims to be a str.
            if isinstance(value, member_type) and member_type.__eq__(member, value) is True:
                return True
        return False

    return _Matcher(accepted, value_tests=(equals_member,) if values else ())


def _class_object_matcher(arguments: tuple[object, ...]) -> _Matcher | None:
    """Accept a class that is a subclass of the class (or classes) inside ``type[...]``."""
    bases: tuple[type, ...] = ()
    if arguments:
        inner = arguments[0]
        members = get_args(inner) if get_origin(inner) in _UNION_ORIGINS else (inner,)
        if all(isinstance(member, type) for member in members):
            bases = cast("tuple[type, ...]", members)

    def is_matching_class(value: object) -> bool:
        return isinstance(value, type) and (not bases or issubclass(value, bases))

    return _Matcher(set(), value_tests=(is_matching_class,))


def _class_matcher(annotation: type, *, promote_numbers: bool) -> _Matcher | None:
    """Accept instances of a class, with the number promotions that type checkers allow."""
    if annotation is object:
        return None
    if getattr(annotation, "_is_protocol", False):
        if not getattr(annotation, "_is_runtime_protocol", False):
            # ``isinstance`` raises for a Protocol without @runtime_checkable.
            return None
        # A runtime Protocol looks at the value's attributes, so a type that
        # passed once is not remembered.
        return _Matcher(set(), value_tests=(_isinstance_test(annotation),))
    # A class whose isinstance raises (an unusual metaclass) stays unchecked.
    isinstance(None, annotation)

    if promote_numbers and annotation is int:
        # numpy and other integer types register as numbers.Integral.
        return _Matcher({int}, type_tests=(_isinstance_test(numbers.Integral),))
    if promote_numbers and annotation is float:
        # PEP 484 lets an int stand in for a float; numbers.Real also covers
        # Fraction and numpy floats. Decimal is not a Real and is rejected.
        return _Matcher({float, int}, type_tests=(_isinstance_test(numbers.Real),))
    if promote_numbers and annotation is complex:
        return _Matcher({complex, float, int}, type_tests=(_isinstance_test(numbers.Complex),))
    if annotation is str:
        return _Matcher({str}, type_tests=(_isinstance_test(str), _is_django_lazy_text))

    test = _isinstance_test(annotation)
    if type(annotation).__instancecheck__ in _TYPE_ONLY_INSTANCE_CHECKS:
        return _Matcher({annotation}, type_tests=(test,))
    # A metaclass with its own isinstance rule may look at the value, so
    # only the annotation's own class takes the fast path.
    return _Matcher({annotation}, value_tests=(test,))


def _isinstance_test(annotation: type) -> Callable[[object], bool]:
    def test(value: object) -> bool:
        return isinstance(value, annotation)

    return test


def _is_django_lazy_text(value: object) -> bool:
    """
    Accept a Django lazy translation string, such as ``gettext_lazy("Save")``, for ``str``.

    Django passes these objects wherever it expects text, and they render as
    text, but they are not ``str`` instances. Citry looks the class up only
    when Django is already imported, so other applications never import it.
    """
    functional = sys.modules.get("django.utils.functional")
    promise = getattr(functional, "Promise", None)
    if not isinstance(promise, type) or not isinstance(value, promise):
        return False
    # Django copies the result type's methods onto each lazy class, so a lazy
    # str has str-only methods such as ``casefold`` while a lazy int does not.
    return hasattr(type(value), "casefold")


def _annotation_label(annotation: object) -> str:
    """Write an annotation the way it appears in source, for the error message."""
    if annotation is None or annotation is _NONE_TYPE:
        return "None"
    if isinstance(annotation, type) and get_origin(annotation) is None:
        return _class_label(annotation)
    if get_origin(annotation) in _UNION_ORIGINS:
        return " | ".join(_annotation_label(member) for member in get_args(annotation))
    text = repr(annotation)
    for prefix in ("typing_extensions.", "typing.", "collections.abc."):
        text = text.replace(prefix, "")
    return text


__all__: list[str] = []
