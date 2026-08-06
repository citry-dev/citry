"""
The handler vocabulary of the ``events`` extension.

What counts as an event handler on a component's ``class Events:`` (public
``def`` means handler, underscore ``def`` means private helper, underscore
attributes mean configuration), the fixed parameter vocabulary a handler may
declare, and the per-handler ``@event`` decorator. Everything here validates
at class definition, so typos die loudly and every signature is fully
classifiable before any call arrives. Design: ``docs/design/events.md``
sections 3.1, 3.3, and 3.5.
"""

from __future__ import annotations
import __future__

import ast
import inspect
import re
import sys
import textwrap
from collections.abc import Callable
from dataclasses import dataclass, is_dataclass
from string import Formatter
from types import FunctionType
from typing import Any, TypeVar, get_type_hints, overload

from citry.ext.events.config import Events

# The fixed name vocabulary handler parameters come from (design 3.3). A
# handler declares only what it needs; any other name is a class-definition
# error.
INJECTABLE_PARAMS = ("data", "state", "context", "request", "event")

# The config attributes recognized on ``class Events:`` and in
# ``extensions_defaults["events"]``. Any other underscore attribute that is
# not a ``def`` fails at declaration time (``EventsExtension.
# validate_config_fields``), which is what makes config typos loud.
# ``_max_envelope_bytes`` (the transport byte cap, design 3.5) is the one
# engine-wide name: the cap is checked before any component resolves, so it
# is settings-only and a component declaring it fails at class definition.
CONFIG_NAMES = (
    "_guard",
    "_context",
    "_csrf",
    "_methods",
    "_debounce",
    "_throttle",
    "_topics",
    "_max_envelope_bytes",
)

_HTTP_METHOD_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_MAX_TIMING_MILLISECONDS = 2**53 - 1

# Where ``@event`` stores its values, as an attribute on the handler function.
EVENT_OPTIONS_ATTR = "_citry_event_options"

_INJECTABLE_SET = frozenset(INJECTABLE_PARAMS)

# Classes the extension system itself contributes to a woven Events class.
# Handler enumeration and config resolution stop at these, so config-base
# members are never mistaken for user declarations.
_FRAMEWORK_CLASSES = frozenset(Events.__mro__)

# Descriptor-shaped values allowed under underscore names (private helpers).
_DEF_LIKE = (staticmethod, classmethod, property)

_F = TypeVar("_F", bound=Callable[..., Any])


@dataclass(frozen=True, slots=True)
class EventOptions:
    """
    The values one ``@event(...)`` call stored on a handler.

    ``None`` means the key was not given, so the component-level config (and
    below it, the engine and factory defaults) applies. The queue knobs
    ``latest_wins`` and ``bundle`` have no component level (they are
    per-handler on purpose, design 3.5), so they hold plain booleans whose
    defaults match an undecorated handler.
    """

    name: str | None = None
    methods: tuple[str, ...] | None = None
    guard: Callable[..., Any] | None = None
    csrf: str | bool | Callable[..., Any] | None = None
    debounce: int | None = None
    throttle: int | None = None
    latest_wins: bool = False
    bundle: bool = True


def event_options(func: Callable[..., Any]) -> EventOptions | None:
    """The ``@event`` values stored on ``func``, or ``None`` for a bare handler."""
    options = getattr(func, EVENT_OPTIONS_ATTR, None)
    return options if isinstance(options, EventOptions) else None


def is_def_like(value: Any) -> bool:
    """
    Whether a class member's value is a ``def`` or a def-shaped descriptor
    (``staticmethod``, ``classmethod``, ``property``).

    On an ``Events`` class this is what makes an underscore name a private
    helper rather than a config attribute.
    """
    return inspect.isfunction(value) or isinstance(value, _DEF_LIKE)


################################################
# CONFIG VALUE VALIDATION
#
# Shared between the ``@event`` decorator and the component-level underscore
# attributes, so both levels reject the same shapes with the same wording.
# ``source`` names the offending site (e.g. "@event(methods=...)" or
# "Component Doc: Events._methods").
################################################


def validate_methods_value(source: str, value: Any) -> tuple[str, ...]:
    """Check a ``methods`` value: a non-empty tuple of HTTP method names, normalized uppercase."""
    if isinstance(value, str) or not isinstance(value, (tuple, list)) or not all(isinstance(m, str) for m in value):
        msg = f'{source} must be a tuple of HTTP method names, e.g. ("POST",); got {value!r}.'
        raise ValueError(msg)
    if not value:
        msg = f"{source} must name at least one HTTP method; got an empty {type(value).__name__}."
        raise ValueError(msg)
    invalid = next((method for method in value if _HTTP_METHOD_RE.fullmatch(method) is None), None)
    if invalid is not None:
        msg = f"{source} contains an invalid HTTP method name: {invalid!r}."
        raise ValueError(msg)
    return tuple(m.upper() for m in value)


def validate_timing_value(source: str, value: Any) -> int | None:
    """Check a ``debounce`` / ``throttle`` value in portable milliseconds."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        msg = f"{source} must be a non-negative int (milliseconds) or None; got {value!r}."
        raise ValueError(msg)
    if value > _MAX_TIMING_MILLISECONDS:
        msg = (
            f"{source} must be a non-negative int no greater than {_MAX_TIMING_MILLISECONDS}"
            f" (milliseconds), or None; got {value!r}."
        )
        raise ValueError(msg)
    return value


def validate_bool_value(source: str, value: Any) -> bool:
    """
    Check a ``latest_wins`` / ``bundle`` value: a plain bool.

    The queue knobs exist at the handler level only (design 3.5), so unlike
    the validators above, only the ``@event`` decorator calls this.
    """
    if not isinstance(value, bool):
        msg = f"{source} must be True or False; got {value!r}."
        # ValueError, not TypeError: one exception type for the whole
        # class-definition error matrix.
        raise ValueError(msg)  # noqa: TRY004
    return value


def validate_csrf_value(source: str, value: Any) -> str | bool | Callable[..., Any]:
    """Check a ``csrf`` value: ``"auto"``, ``False``, or a callable."""
    if value == "auto" or value is False or callable(value):
        return value
    msg = f'{source} must be "auto", False, or a callable; got {value!r}.'
    raise ValueError(msg)


def validate_callable_value(source: str, value: Any) -> Callable[..., Any] | None:
    """Check a ``guard`` / ``context`` value: a callable (or None)."""
    if value is None or callable(value):
        return value
    msg = f"{source} must be a callable or None; got {value!r}."
    raise ValueError(msg)


def validate_topics_value(source: str, value: Any, state_fields: tuple[str, ...] | None) -> tuple[str, ...]:
    """
    Check a ``_topics`` value: topic-name templates formatted from State fields.

    Stored and validated here, consumed by server push later; every
    ``{placeholder}`` must name a State field of the component.
    """
    if isinstance(value, str) or not isinstance(value, (tuple, list)) or not all(isinstance(t, str) for t in value):
        msg = f'{source} must be a tuple of topic-name templates, e.g. ("project:{{project_id}}",); got {value!r}.'
        raise ValueError(msg)
    for template in value:
        for _, placeholder, _, _ in Formatter().parse(template):
            if placeholder is None:
                continue
            if placeholder == "" or placeholder.isdigit():
                msg = (
                    f"{source} template {template!r} uses a positional placeholder;"
                    f' name a State field instead, e.g. "{{project_id}}".'
                )
                raise ValueError(msg)
            if state_fields is None:
                msg = (
                    f"{source} template {template!r} names {placeholder!r}, but the component"
                    f" declares no State class (topic templates format State fields)."
                )
                raise ValueError(msg)
            if placeholder not in state_fields:
                msg = (
                    f"{source} template {template!r} names {placeholder!r}, which is not a State"
                    f" field. Declared fields: {', '.join(state_fields) or '(none)'}."
                )
                raise ValueError(msg)
    return tuple(value)


################################################
# THE @event DECORATOR
################################################


@overload
def event(func: _F, /) -> _F: ...


@overload
def event(
    *,
    name: str | None = None,
    methods: tuple[str, ...] | list[str] | None = None,
    guard: Callable[..., Any] | None = None,
    csrf: str | bool | Callable[..., Any] | None = None,
    debounce: int | None = None,
    throttle: int | None = None,
    latest_wins: bool = False,
    bundle: bool = True,
) -> Callable[[_F], _F]: ...


def event(
    func: _F | None = None,
    /,
    *,
    name: str | None = None,
    methods: tuple[str, ...] | list[str] | None = None,
    guard: Callable[..., Any] | None = None,
    csrf: str | bool | Callable[..., Any] | None = None,
    debounce: int | None = None,
    throttle: int | None = None,
    latest_wins: bool = False,
    bundle: bool = True,
) -> _F | Callable[[_F], _F]:
    """
    Per-handler configuration for one event handler.

    Bare handlers need no decorator; use ``@event(...)`` only to override the
    component-level defaults for one handler. Every key not given falls back
    to the component's underscore config
    (``_methods``, ``_guard``, ``_csrf``, ``_debounce``, ``_throttle``),
    which itself falls back to ``extensions_defaults["events"]`` and then the
    built-in defaults. The queue knobs ``latest_wins`` and ``bundle`` are the
    exception: they exist per handler only, so a call site that needs
    different queue semantics names a different handler.

    Args:
        func: The handler, when used as a bare ``@event`` (no arguments).
        name: Wire name override: rename the Python method without touching
            templates.
        methods: The allowed HTTP methods for this handler, e.g. ``("GET",)``.
        guard: Per-handler authorization callable; replaces (does not stack
            on) the component's ``_guard``.
        csrf: Per-handler CSRF policy: ``"auto"``, ``False``, or a callable.
        debounce: Client-side debounce, in milliseconds.
        throttle: Client-side throttle, in milliseconds.
        latest_wins: Opt this handler into newest-wins queueing on the
            client. When a newer call to the handler is queued for the same
            component instance, calls still waiting to be sent are dropped,
            and an in-flight one is abandoned (its response is ignored when
            it arrives). The server still executes every call it received,
            so opt in only when overlapping runs are safe, e.g. an
            idempotent autosave. Off by default, because dropping a call is
            data loss unless the handler is written for it.
        bundle: Whether the client may send this handler's calls in a shared
            batch request alongside other calls that become ready at the
            same moment. Pass ``False`` for a handler that should always
            travel alone, e.g. a slow export that fast toggles should not
            wait on.

    Returns:
        The handler itself (the decorator only attaches the configuration).

    Example:
        ```python
        from citry.ext.events import event

        class Document(Component):
            class Events:
                @event(debounce=400)
                def autosave(self, state: DocState):
                    save_draft(state.doc_id, state.title)

                @event(methods=("GET",))
                def word_count(self, data: WordCountIn) -> dict:
                    return {"words": count_words(data.doc_id)}
        ```

    Raises:
        ValueError: When a value has the wrong shape (e.g. a ``methods``
            string instead of a tuple), at decoration time.

    """
    if name is not None and (not isinstance(name, str) or not name):
        msg = f"@event(name=...) must be a non-empty string; got {name!r}."
        raise ValueError(msg)
    options = EventOptions(
        name=name,
        methods=validate_methods_value("@event(methods=...)", methods) if methods is not None else None,
        guard=validate_callable_value("@event(guard=...)", guard),
        csrf=validate_csrf_value("@event(csrf=...)", csrf) if csrf is not None else None,
        debounce=validate_timing_value("@event(debounce=...)", debounce),
        throttle=validate_timing_value("@event(throttle=...)", throttle),
        latest_wins=validate_bool_value("@event(latest_wins=...)", latest_wins),
        bundle=validate_bool_value("@event(bundle=...)", bundle),
    )

    def wrap(handler: _F) -> _F:
        setattr(handler, EVENT_OPTIONS_ATTR, options)
        return handler

    return wrap(func) if func is not None else wrap


################################################
# HANDLER ENUMERATION AND SIGNATURE VALIDATION
################################################


def user_level_classes(raw_events_cls: type) -> list[type]:
    """
    The classes of a raw ``Events`` MRO that the user wrote.

    Stops at the framework classes (the woven config base and above), so
    config-base members are never mistaken for user declarations.
    """
    return [
        klass
        for klass in raw_events_cls.__mro__
        if klass not in _FRAMEWORK_CLASSES
        and not vars(klass).get("_citry_synthesized_config", False)
        and not vars(klass).get("_citry_synthesized_declaration", False)
    ]


def collect_event_handlers(comp_name: str, raw_events_cls: type) -> dict[str, FunctionType]:
    """
    Enumerate the event handlers a raw ``Events`` class declares.

    Public ``def``s are handlers; underscore ``def``s are private helpers
    (with ``_context`` and ``_guard`` doubling as config); underscore
    attributes that are not ``def``s are config, their names already checked
    at declaration time by ``EventsExtension.validate_config_fields``.
    Handlers merge across the user's own base classes, base-first, so a
    subclass redefinition wins while keeping the base's position.

    Returns:
        The handlers in definition order, keyed by method name.

    Raises:
        ValueError: For an ``@event`` on a private helper, or a public
            staticmethod/classmethod.

    """
    handlers: dict[str, FunctionType] = {}
    for klass in reversed(user_level_classes(raw_events_cls)):
        for member_name, value in vars(klass).items():
            if member_name.startswith("__") and member_name.endswith("__"):
                continue
            if member_name.startswith("_"):
                if is_def_like(value):
                    if inspect.isfunction(value) and event_options(value) is not None:
                        msg = (
                            f"Component {comp_name}: @event cannot decorate {member_name!r}:"
                            f" underscore defs are private helpers, not handlers. Rename it"
                            f" without the leading underscore to expose it as an event."
                        )
                        raise ValueError(msg)
                    continue  # a private helper, or a config def like _guard / _context
                # A non-def underscore attribute is config; its name was
                # already checked at declaration time by
                # ``EventsExtension.validate_config_fields``.
                continue
            if isinstance(value, (staticmethod, classmethod)):
                msg = (
                    f"Component {comp_name}: event handler {member_name!r} cannot be a"
                    f" staticmethod or classmethod; handlers are plain methods and receive"
                    f" 'self' (the per-call Events instance)."
                )
                # ValueError, not TypeError: one exception type for the whole
                # class-definition error matrix.
                raise ValueError(msg)  # noqa: TRY004
            if isinstance(value, FunctionType):
                handlers[member_name] = value
    return handlers


def validate_handler_signature(
    comp_name: str,
    method_name: str,
    func: FunctionType,
    has_state: bool,
) -> tuple[str, ...]:
    """
    Check one handler's parameters against the fixed vocabulary.

    Parameters must come from ``data``, ``state``, ``context``, ``request``,
    ``event``; ``*args`` / ``**kwargs`` are rejected; declaring ``state`` on
    a component with no State class is rejected.

    Returns:
        The declared parameter names (without ``self``), in signature order.

    Raises:
        ValueError: With a message naming what was declared and what is
            valid, at class definition.

    """
    # A fresh function with the same code has the same parameters and no
    # annotations. This prevents Python 3.14's deferred return annotations
    # from running while Citry validates only parameter names and kinds.
    signature_probe = FunctionType(func.__code__, func.__globals__, func.__name__, func.__defaults__, func.__closure__)
    signature_probe.__kwdefaults__ = func.__kwdefaults__
    parameters = list(inspect.signature(signature_probe).parameters.values())
    if not parameters or parameters[0].name != "self":
        msg = (
            f"Component {comp_name}: event handler {method_name!r} must declare 'self' as its"
            f" first parameter (handlers are instance methods on the Events class)."
        )
        raise ValueError(msg)
    names: list[str] = []
    for parameter in parameters[1:]:
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            star = "*" if parameter.kind is inspect.Parameter.VAR_POSITIONAL else "**"
            msg = (
                f"Component {comp_name}: event handler {method_name!r} declares"
                f" '{star}{parameter.name}'; event handlers cannot take '*args' or '**kwargs'"
                f" (the signature is the schema). Declare only the parameters you need from:"
                f" {', '.join(INJECTABLE_PARAMS)}."
            )
            raise ValueError(msg)
        if parameter.name not in _INJECTABLE_SET:
            msg = (
                f"Component {comp_name}: event handler {method_name!r} declares parameter"
                f" {parameter.name!r}, which is not in the handler vocabulary. Handler"
                f" parameters come from: {', '.join(INJECTABLE_PARAMS)}."
            )
            raise ValueError(msg)
        names.append(parameter.name)
    if "state" in names and not has_state:
        msg = (
            f"Component {comp_name}: event handler {method_name!r} declares 'state', but"
            f" {comp_name} declares no State class. Declare a State class on the component,"
            f" or drop the 'state' parameter."
        )
        raise ValueError(msg)
    return tuple(names)


def resolve_data_schema(comp_cls: type, method_name: str, func: FunctionType) -> type:
    """
    Resolve a handler's ``data`` annotation to its schema class, eagerly.

    ``data`` is the one annotation the dispatcher must resolve (it is the
    validator), so it is resolved at class definition: with the handler's
    module globals, rescued by a local namespace seeded with the component
    and its nested classes (so a schema class declared on the component
    resolves too). The other injectables' annotations are advisory and never
    resolved.

    Raises:
        ValueError: When ``data`` has no annotation, the annotation does not
            resolve, or it is not a class with annotated fields.

    """
    comp_name = comp_cls.__name__
    annotations = _get_annotations_as_text(func)
    if "data" not in annotations:
        msg = (
            f"Component {comp_name}: event handler {method_name!r} declares 'data' without a"
            f" type annotation. Annotate it with the input schema class (an annotated class,"
            f" a dataclass, or a Pydantic model), e.g. 'data: SearchIn'."
        )
        raise ValueError(msg)
    raw = annotations["data"]

    # The rescue namespace: the component's own (and inherited) nested
    # classes plus every class name on its MRO, nearest last so it wins.
    localns: dict[str, Any] = {}
    for klass in reversed(comp_cls.__mro__):
        localns[klass.__name__] = klass
        localns.update({name: nested for name, nested in vars(klass).items() if isinstance(nested, type)})
    localns.update(_annotation_closure_locals(func))

    # A throwaway function carrying only the ``data`` annotation, so
    # ``get_type_hints`` cannot trip over a bogus annotation on another
    # parameter (those are advisory by design).
    def probe() -> None: ...

    probe.__annotations__ = {"data": raw}
    try:
        resolved = get_type_hints(probe, globalns=getattr(func, "__globals__", None), localns=localns)["data"]
    except (NameError, TypeError) as err:
        msg = (
            f"Component {comp_name}: cannot resolve the 'data' annotation {raw!r} on event"
            f" handler {method_name!r} ({err}). Define the schema class at module level, or"
            f" as a class on the component, so the name resolves at class definition."
        )
        raise ValueError(msg) from err

    if not _is_schema_class(resolved):
        msg = (
            f"Component {comp_name}: the 'data' annotation on event handler {method_name!r}"
            f" must be a class with annotated fields (an annotated class, a dataclass, or a"
            f" Pydantic model); got {resolved!r}."
        )
        raise ValueError(msg)
    return resolved


def _get_annotations_as_text(
    obj: Callable[..., Any] | type,
    *,
    require_exact_storage: bool = True,
) -> dict[str, Any]:
    """Copy annotations without running Python 3.14 deferred expressions."""
    if require_exact_storage and isinstance(obj, type):
        namespace = type.__dict__["__dict__"].__get__(obj)
        stored = namespace.get("__annotations__")
        if stored is not None and type(stored) is not dict:
            return {}
    if sys.version_info < (3, 14):
        return inspect.get_annotations(obj, eval_str=False)

    try:
        source = textwrap.dedent(inspect.getsource(obj))
        parsed = ast.parse(source)
    except (IndentationError, OSError, SyntaxError, TypeError):
        if isinstance(obj, FunctionType) and obj.__code__.co_flags & __future__.annotations.compiler_flag:
            return inspect.get_annotations(obj, eval_str=False)
        return {}
    object_name = obj.__name__
    for node in ast.walk(parsed):
        if isinstance(obj, FunctionType) and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == object_name:
                return _function_source_annotations(node)
        elif isinstance(obj, type) and isinstance(node, ast.ClassDef) and node.name == object_name:
            return _class_source_annotations(node)
    return {}


def _function_source_annotations(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
    """Return parameter and return annotation text from one parsed function."""
    result: dict[str, str] = {}
    arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    if node.args.vararg is not None:
        arguments.append(node.args.vararg)
    if node.args.kwarg is not None:
        arguments.append(node.args.kwarg)
    for argument in arguments:
        if argument.annotation is not None:
            result[argument.arg] = _annotation_source_text(argument.annotation)
    if node.returns is not None:
        result["return"] = _annotation_source_text(node.returns)
    return result


def _class_source_annotations(node: ast.ClassDef) -> dict[str, str]:
    """Return directly declared field annotation text from one parsed class."""
    return {
        statement.target.id: _annotation_source_text(statement.annotation)
        for statement in node.body
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
    }


def _annotation_source_text(node: ast.expr) -> str:
    """Normalize one annotation AST without evaluating the expression."""
    if isinstance(node, ast.Constant) and type(node.value) is str:
        return node.value
    return ast.unparse(node)


def _annotation_closure_locals(func: FunctionType) -> dict[str, Any]:
    """Copy names captured by Python 3.14's generated annotation function."""
    if sys.version_info < (3, 14):
        return {}
    annotate = func.__annotate__
    if type(annotate) is not FunctionType or annotate.__closure__ is None:
        return {}
    return {
        name: cell.cell_contents
        for name, cell in zip(annotate.__code__.co_freevars, annotate.__closure__, strict=True)
        if name != "__classdict__"
    }


def _is_schema_class(candidate: Any) -> bool:
    """Whether a resolved ``data`` annotation can become an input schema."""
    if not isinstance(candidate, type):
        return False
    if is_dataclass(candidate):
        return True
    # Any class with annotated fields, own or inherited; Pydantic models
    # (annotated classes themselves) pass here without a Pydantic import.
    for klass in candidate.__mro__:
        namespace = type.__dict__["__dict__"].__get__(klass)
        stored = namespace.get("__annotations__")
        if isinstance(stored, dict) and dict.__len__(stored) > 0:
            return True
        if _get_annotations_as_text(klass, require_exact_storage=False):
            return True
    return False
