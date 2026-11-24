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
import functools
import inspect
import re
import sys
import textwrap
from collections.abc import Callable
from dataclasses import dataclass, is_dataclass
from types import FunctionType
from typing import Any, TypeVar, get_type_hints, overload

from citry._class_introspection import _static_class_namespace_copy
from citry.ext.events.config import Events

# The fixed name vocabulary handler parameters come from (design 3.3). A
# handler declares only what it needs; any other name is a class-definition
# error.
INJECTABLE_PARAMS = ("data", "state", "context", "request", "event")

# The config attributes recognized on ``class Events:`` and in
# ``extensions_defaults["events"]``. Any other underscore attribute that is
# not a ``def`` fails at declaration time (``EventsExtension.
# validate_config_fields``), which is what makes config typos loud.
# ``_max_body_bytes`` (the largest request body, design 3.5),
# ``_max_form_fields`` (the most fields in one form post), and
# ``_csrf_field_names`` (the host CSRF fields the server drops from an event
# call's arguments, design 3.5 and security_csrf.md 4.4) are engine-wide
# names: they apply before any component's config is read, so they are
# settings-only and a component declaring one fails at class definition.
# ``_csp_nonce`` (a function that returns the CSP nonce of the page that sent
# a call) is engine-wide too, because a page's nonce is one fact for every
# component on it. ``_csrf_cookie`` and ``_csrf_header`` (the names of the
# host's CSRF cookie and header, which the browser runtime reads from each
# app's configuration block) are engine-wide for the same reason: a site has
# one CSRF scheme. ``_render_inputs`` (a function that returns the keyword
# arguments Citry passes to ``render()`` for every Render a call performs) is
# an ordinary per-component name: the calling component's value wins over
# ``extensions_defaults["events"]``.
CONFIG_NAMES = (
    "_guard",
    "_context",
    "_csrf",
    "_methods",
    "_debounce",
    "_throttle",
    "_max_body_bytes",
    "_max_form_fields",
    "_csrf_field_names",
    "_csp_nonce",
    "_csrf_cookie",
    "_csrf_header",
    "_render_inputs",
)

# The engine-wide config names, which only ``extensions_defaults["events"]``
# may set.
ENGINE_CONFIG_NAMES = frozenset(
    {"_max_body_bytes", "_max_form_fields", "_csrf_field_names", "_csp_nonce", "_csrf_cookie", "_csrf_header"}
)

# The hidden field Django's ``{% csrf_token %}`` and its own forms write. A
# page that keeps it inside a form sending a server event would otherwise
# fail every call with an unknown field (design 3.5, security_csrf.md 4.4).
DEFAULT_CSRF_FIELD_NAMES = ("csrfmiddlewaretoken",)

_HTTP_METHOD_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")

# The methods the per-event route (``ext/events/e/{class_id}/{event}``)
# admits at the host adapter. Handlers can register after the routes are
# mounted (Django snapshots its URL set once), so the route cannot list only
# the methods current handlers declare; it admits this fixed set, and the
# resolved handler answers 405 with its own ``Allow`` list. A handler may
# declare only methods from this set, because on its own URL a request with
# any other method stops at the adapter, so the declared method could never
# be served there. It lives here rather than in
# ``routes.py`` because ``routes.py`` imports the dispatcher, which imports
# this module.
EVENT_ROUTE_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
_MAX_TIMING_MILLISECONDS = 2**53 - 1

# Where ``@event`` stores its values, as an attribute on the handler function.
EVENT_OPTIONS_ATTR = "_citry_event_options"

_INJECTABLE_SET = frozenset(INJECTABLE_PARAMS)

# Classes the extension system itself contributes to a woven Events class.
# Handler enumeration and config resolution stop at these, so config-base
# members are never mistaken for user declarations. Base classes Citry ships
# for users to subclass join through ``framework_base``.
_FRAMEWORK_CLASSES: set[type] = set(Events.__mro__)

# Descriptor-shaped values allowed under underscore names (private helpers).
_DEF_LIKE = (staticmethod, classmethod, property)

_F = TypeVar("_F", bound=Callable[..., Any])
_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class EventOptions:
    """
    The values one ``@event(...)`` call stored on a handler.

    ``None`` means the key was not given, so the component-level config (and
    below it, the engine and factory defaults) applies. The queue knobs
    ``latest_wins``, ``bundle`` and ``detached`` have no component level (they
    are per-handler on purpose, design 3.5), so they hold plain booleans whose
    defaults match an undecorated handler. ``component_guard`` is a plain
    boolean too: ``True`` (the default) runs the component-level guard before
    ``guard``, and only an explicit ``False`` turns it off for this handler.
    """

    name: str | None = None
    methods: tuple[str, ...] | None = None
    guard: Callable[..., Any] | None = None
    component_guard: bool = True
    csrf: str | bool | Callable[..., Any] | None = None
    debounce: int | None = None
    throttle: int | None = None
    latest_wins: bool = False
    bundle: bool = True
    detached: bool = False


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


def validate_route_methods(source: str, methods: tuple[str, ...]) -> None:
    """
    Check that every declared method can reach the handler through the per-event route.

    ``methods`` is the uppercase tuple ``validate_methods_value`` returned.
    On the handler's own URL, a method outside ``EVENT_ROUTE_METHODS`` is
    answered 405 by the host adapter before Events sees the request, so a
    declared method outside that set could never be served there. (The
    batched call route ignores declared methods.) Rejecting it here makes
    that mistake fail when the class is defined instead of on the first
    request.
    """
    unreachable = next((method for method in methods if method not in EVENT_ROUTE_METHODS), None)
    if unreachable is not None:
        allowed = ", ".join(EVENT_ROUTE_METHODS)
        msg = (
            f"{source} declares HTTP method {unreachable!r}, which the per-event route does not accept,"
            f" so the handler's own URL could never serve it. Use one of: {allowed}."
        )
        raise ValueError(msg)


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
    Check a ``latest_wins`` / ``bundle`` / ``detached`` / ``component_guard`` value: a plain bool.

    These knobs exist at the handler level only (design 3.5), so unlike the
    validators above, only the ``@event`` decorator calls this. A plain bool
    matters most for ``component_guard``: a stand-in such as ``0`` or
    ``"no"`` must not decide whether an authorization check runs.
    """
    if not isinstance(value, bool):
        msg = f"{source} must be True or False; got {value!r}."
        # ValueError, not TypeError: one exception type for the whole
        # class-definition error matrix.
        raise ValueError(msg)  # noqa: TRY004
    return value


def validate_csrf_value(source: str, value: Any) -> str | bool | Callable[..., Any]:
    """Check a ``csrf`` value: ``"auto"``, ``False``, or a plain (not async) function."""
    if value == "auto" or value is False:
        return value
    if callable(value):
        # The CSRF check calls the function and treats "it did not raise" as
        # a pass, so an async one would pass every request unchecked.
        refuse_deferred_body(source, value, "that takes the request and raises EventError to refuse it")
        return value
    msg = f'{source} must be "auto", False, or a callable; got {value!r}.'
    raise ValueError(msg)


# What a guard does, for the error that refuses an async one.
GUARD_PURPOSE = "that takes the Events instance and raises EventError or returns False to refuse the call, or None"

# Calling one of these returns an object whose code has not run yet: a
# coroutine (async def), an async generator, or a generator.
_DEFERRED_BODY_CHECKS = (inspect.iscoroutinefunction, inspect.isasyncgenfunction, inspect.isgeneratorfunction)


def defers_its_body(func: Any) -> bool:
    """
    Whether calling ``func`` returns a coroutine or generator instead of running its code.

    Citry calls guards and the other Events functions without awaiting or
    iterating what they return, so the code of such a function would never
    run. ``inspect.iscoroutinefunction`` alone misses an object whose
    ``__call__`` is ``async def`` and a ``staticmethod`` or ``classmethod``
    wrapper, so this unwraps those first. It does not follow ``__wrapped__``:
    a plain wrapper such as ``asgiref.sync.async_to_sync`` sets it to the
    async function it runs, and that wrapper is a valid plain function.
    """
    # A chain of wrappers is short in practice; the bound only stops a
    # pathological self-referencing ``__call__`` from looping.
    for _ in range(32):
        if any(check(func) for check in _DEFERRED_BODY_CHECKS):
            return True
        if isinstance(func, (staticmethod, classmethod)):
            func = func.__func__
        elif isinstance(func, (functools.partial, functools.partialmethod)):
            func = func.func
        elif inspect.ismethod(func):
            func = func.__func__
        elif callable(func) and not isinstance(func, type) and not inspect.isroutine(func):
            # An instance of a class with ``__call__``: what runs is that method.
            call = type(func).__call__
            if call is func:
                return False
            func = call
        else:
            return False
    return False


def refuse_deferred_body(source: str, value: Any, purpose: str) -> None:
    """
    Raise ``ValueError`` when ``value`` is an async (or generator) function.

    Args:
        source: The setting's name, as the error message shows it.
        value: The callable the app gave.
        purpose: What the function takes and does, completing "must be a
            plain (not async) function ...".

    Raises:
        ValueError: When calling ``value`` would not run its code.

    """
    if defers_its_body(value):
        msg = (
            f"{source} must be a plain (not async) function {purpose}. Citry calls it without"
            " awaiting it, so the code of an async (or generator) function would never run;"
            f" got {value!r}."
        )
        raise ValueError(msg)


def refuse_deferred_result(source: str, result: Any, *, coroutine_only: bool = False) -> None:
    """
    Raise ``TypeError`` when a call returned a coroutine or generator.

    The class-definition check cannot see every way to build such a
    function (a plain ``def`` that returns ``some_async_function(...)``,
    for one), so the result is checked on every call too. An unrun
    coroutine or generator is closed first, so Python does not also warn
    that it was never awaited.

    Args:
        source: The function's name, as the error message shows it.
        result: What the function returned.
        coroutine_only: Refuse only a coroutine. ``_context`` passes this:
            its value is app data, which may be some other awaitable or a
            generator on purpose. A guard or CSRF function returns nothing
            useful, so any of these means its code did not run.

    Raises:
        TypeError: When ``result`` is a coroutine, or (without
            ``coroutine_only``) any other awaitable, a generator, or an
            async generator. The dispatcher answers the call with an
            error, so the check fails closed.

    """
    if coroutine_only:
        deferred = inspect.iscoroutine(result)
    else:
        deferred = inspect.isawaitable(result) or inspect.isgenerator(result) or inspect.isasyncgen(result)
    if not deferred:
        return
    # Only objects Citry knows are unrun code are closed; closing some other
    # awaitable the app returned could shut down a resource it still uses.
    if inspect.iscoroutine(result) or inspect.isgenerator(result):
        result.close()
    msg = (
        f"{source} returned a {type(result).__name__!r} object, so its code did not run. It must be"
        " a plain (not async) function: Citry calls it without awaiting it, so this call is refused."
    )
    raise TypeError(msg)


def validate_render_inputs_value(source: str, value: Any) -> Callable[..., Any] | None:
    """Check a ``_render_inputs`` value: a plain (not async) function that takes one argument, or None."""
    # The dispatcher calls the function without awaiting it, so an async
    # function would hand back a coroutine instead of the inputs.
    if value is not None and (not callable(value) or defers_its_body(value)):
        msg = (
            f"{source} must be a plain (not async) function that takes the call's EventRequest"
            " and returns a dict with the optional keys 'template_globals' and 'provides', or None;"
            f" got {value!r}."
        )
        raise ValueError(msg)
    if value is not None and not _takes_one_argument(value):
        # Citry calls it with the request alone. A `def` written inside the
        # Events class expects `self` first, so it would fail on every call;
        # refusing it here names the fix instead.
        msg = (
            f"{source} must take the call's EventRequest as its only argument; a `def` written"
            " in the Events class also expects `self`. Define the function outside the class"
            " and assign it: `_render_inputs = render_inputs`."
        )
        raise ValueError(msg)
    return value


def _takes_one_argument(func: Callable[..., Any]) -> bool:
    """Whether ``func`` can be called with exactly one positional argument."""
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        # Some callables (builtins, C extensions) have no signature to read;
        # the call itself is the only check left for them.
        return True
    try:
        signature.bind(object())
    except TypeError:
        return False
    return True


def validate_callable_value(
    source: str, value: Any, purpose: str = "that takes the Events instance, or None"
) -> Callable[..., Any] | None:
    """Check a ``guard`` / ``context`` value: a plain (not async) function, or None."""
    if value is None:
        return value
    if callable(value):
        # The dispatcher calls guards and _context without awaiting them. An
        # async guard would only create a coroutine, never raise, and so let
        # every call through; refusing it here fails at class definition.
        refuse_deferred_body(source, value, purpose)
        return value
    msg = f"{source} must be a callable or None; got {value!r}."
    raise ValueError(msg)


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
    component_guard: bool = True,
    csrf: str | bool | Callable[..., Any] | None = None,
    debounce: int | None = None,
    throttle: int | None = None,
    latest_wins: bool = False,
    bundle: bool = True,
    detached: bool = False,
) -> Callable[[_F], _F]: ...


def event(
    func: _F | None = None,
    /,
    *,
    name: str | None = None,
    methods: tuple[str, ...] | list[str] | None = None,
    guard: Callable[..., Any] | None = None,
    component_guard: bool = True,
    csrf: str | bool | Callable[..., Any] | None = None,
    debounce: int | None = None,
    throttle: int | None = None,
    latest_wins: bool = False,
    bundle: bool = True,
    detached: bool = False,
) -> _F | Callable[[_F], _F]:
    """
    Per-handler configuration for one event handler.

    Bare handlers need no decorator; use ``@event(...)`` only to override the
    component-level defaults for one handler. Every key not given falls back
    to the component's underscore config
    (``_methods``, ``_csrf``, ``_debounce``, ``_throttle``), which itself
    falls back to ``extensions_defaults["events"]`` and then the built-in
    defaults. Guards work differently: a ``guard`` given here runs after
    the component's ``_guard``, in addition to it (see ``guard`` and
    ``component_guard`` below). The queue knobs ``latest_wins``,
    ``bundle`` and ``detached`` exist per handler only, so a call
    site that needs different queue semantics names a different handler. A
    detached handler also needs the call site to pass ``wait: false``; a
    call without it waits its turn.

    Args:
        func: The handler, when used as a bare ``@event`` (no arguments).
        name: Wire name override: rename the Python method without touching
            templates.
        methods: The allowed HTTP methods for this handler, e.g. ``("GET",)``.
            Each must be one of GET, HEAD, POST, PUT, PATCH, DELETE, or
            OPTIONS, the methods the per-event route accepts.
        guard: Per-handler authorization function. It receives the
            ``Events`` instance and refuses the call by raising
            ``EventError`` or by returning ``False`` (a 403). Returning
            ``None`` lets the call go ahead; any other value also lets it
            go ahead and logs a warning. It runs after the component's
            ``_guard`` (or the app-wide ``_guard`` in
            ``extensions_defaults["events"]`` when the component defines
            none), and either one refusing refuses the call. It must be a
            plain ``def``, not ``async def``: Citry calls it without
            awaiting it.
        component_guard: Pass ``False`` to skip the component's ``_guard``
            (or the app-wide ``_guard``) for this handler only, for a
            handler that must accept callers the rest of its component
            refuses, such as a public sign-up call. ``guard`` and
            ``_context`` still run. Only ``True`` or ``False`` is
            accepted.
        csrf: Per-handler CSRF policy: ``"auto"``, ``False``, or a plain
            (not async) function that raises ``EventError`` to refuse the
            request.
        debounce: Client-side debounce, in milliseconds.
        throttle: Client-side throttle, in milliseconds.
        latest_wins: Opt this handler into newest-wins queueing on the
            client. When a newer call to the handler is queued for the same
            component instance, calls still waiting to be sent are dropped,
            an in-flight one is abandoned (its response is ignored when it
            arrives), and one whose result already arrived stops, so none
            of its actions that have not started yet will run. The server
            still executes every call it received, so opt in only when
            overlapping runs are safe, e.g. an idempotent autosave. Off by
            default, because dropping a call is data loss unless the
            handler is written for it.
        bundle: Whether the client may send this handler's calls in a shared
            batch request alongside other calls that become ready at the
            same moment. Pass ``False`` for a handler that should always
            travel alone, e.g. a slow export that fast toggles should not
            wait on.
        detached: Let browser code call this handler without waiting for
            the app's other calls, with
            ``$sendEvent(name, args, {wait: false})``. In exchange, the
            handler must not render or change State: it may return data,
            dispatch an event, redirect, update the URL, or return a
            ``Download``, and it may read State. A detached handler that
            renders or changes State fails with a ``handler_error``. It
            reads State from the token the browser sends with the call:
            browser State changes not yet sent stay in the browser for the
            next call to a handler that is not detached, so pass values the
            user is still editing as arguments. Its calls can run on
            the server at the same time as the app's other calls, so do not
            rely on what those calls write. Off by default.

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

                @event(detached=True)
                def spell_check(self, data: SpellCheckIn) -> dict:
                    return {"typos": find_typos(data.text)}

                # Runs after the component's _guard, if it has one.
                @event(guard=require_owner)
                def delete(self, state: DocState):
                    delete_document(state.doc_id)
        ```

    Raises:
        ValueError: When a value has the wrong shape (e.g. a ``methods``
            string instead of a tuple, or an ``async def`` guard), or when
            ``methods`` names a method the per-event route does not accept
            (anything other than GET, HEAD, POST, PUT, PATCH, DELETE, and
            OPTIONS), at decoration time.

    """
    if name is not None and (not isinstance(name, str) or not name):
        msg = f"@event(name=...) must be a non-empty string; got {name!r}."
        raise ValueError(msg)
    options = EventOptions(
        name=name,
        methods=validate_methods_value("@event(methods=...)", methods) if methods is not None else None,
        guard=validate_callable_value("@event(guard=...)", guard, GUARD_PURPOSE),
        component_guard=validate_bool_value("@event(component_guard=...)", component_guard),
        csrf=validate_csrf_value("@event(csrf=...)", csrf) if csrf is not None else None,
        debounce=validate_timing_value("@event(debounce=...)", debounce),
        throttle=validate_timing_value("@event(throttle=...)", throttle),
        latest_wins=validate_bool_value("@event(latest_wins=...)", latest_wins),
        bundle=validate_bool_value("@event(bundle=...)", bundle),
        detached=validate_bool_value("@event(detached=...)", detached),
    )

    def wrap(handler: _F) -> _F:
        # The shape was checked above, when ``@event(...)`` was called; the
        # route check waits for the handler so its error can name it.
        if options.methods is not None:
            handler_name = getattr(handler, "__qualname__", repr(handler))
            validate_route_methods(f"@event(methods=...) on handler {handler_name!r}", options.methods)
        setattr(handler, EVENT_OPTIONS_ATTR, options)
        return handler

    return wrap(func) if func is not None else wrap


################################################
# HANDLER ENUMERATION AND SIGNATURE VALIDATION
################################################


def framework_base(cls: type[_T]) -> type[_T]:
    """
    Mark a base class Citry ships for ``Events`` classes as part of the framework.

    Handler enumeration and config resolution skip it as they skip
    ``Events``, so a public helper added to the base later never becomes an
    event handler that a request can call on every subclass. The base lives
    in a module that imports this one, so it registers itself here rather
    than this module importing it.
    """
    _FRAMEWORK_CLASSES.add(cls)
    return cls


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
        for member_name, value in _static_class_namespace_copy(klass).items():
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
        # A parent component can be rendering on another thread, which stores
        # computed results on its class, so the loop walks a copy.
        namespace = _static_class_namespace_copy(klass)
        localns.update({name: nested for name, nested in namespace.items() if isinstance(nested, type)})
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
