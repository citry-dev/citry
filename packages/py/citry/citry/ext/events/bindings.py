r"""
Compile Citry Events template attributes into typed binding metadata.

Authored ``@c-*`` event/poll bindings and ``:c-*`` State controls are
validated after template compilation and retained only on typed prepared
element nodes and travel in the prepared browser configuration. Runtime State
controls contributed by ``c-bind`` use a private, producer-authenticated Python
carrier until typed capture consumes them. The ``data-cev-*`` namespace is
reserved, so an authored or extension-forged ``data-cev-*`` attribute fails closed.

Design: ``docs/design/events.md`` section 5.1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, NoReturn, cast

from citry._state_binding_targets import (
    _custom_update_event_error,
    _Element,
    _input_type,
)
from citry._state_binding_targets import (
    _element_of as _state_binding_element,
)
from citry._state_binding_targets import (
    _validate_binding_target as _classify_state_binding_target,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.ext.events.extension import EventsInfo

RUNTIME_CONTROL_ATTR: Final = "data-citry-runtime-control"
RUNTIME_EVENTS_ATTR: Final = "data-citry-runtime-events"
_CHANNEL_EVENT: Final = "event"
_CHANNEL_POLL: Final = "poll"
_CHANNEL_CONTROL: Final = "control"

_RUNTIME_CONTROL_TOKEN = object()
_RUNTIME_EVENTS_TOKEN = object()


@dataclass(frozen=True, slots=True)
class _RuntimeControlBindings:
    specs: tuple[MappingProxyType[str, object], ...]
    _producer_token: object

    def __str__(self) -> str:
        raise TypeError("runtime State control metadata cannot be serialized as an HTML attribute")


@dataclass(frozen=True, slots=True)
class _RuntimeEventBindings:
    event_specs: tuple[MappingProxyType[str, object], ...]
    poll_specs: tuple[MappingProxyType[str, object], ...]
    _producer_token: object

    def __str__(self) -> str:
        raise TypeError("runtime event metadata cannot be serialized as an HTML attribute")


def _runtime_control_bindings(value: object) -> tuple[dict[str, object], ...]:
    """Consume native control metadata only when this module produced it."""
    if type(value) is not _RuntimeControlBindings or value._producer_token is not _RUNTIME_CONTROL_TOKEN:
        raise TypeError("runtime State control metadata lacks Events producer provenance")
    return tuple(dict(spec) for spec in value.specs)


def _runtime_event_bindings(
    value: object,
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    """Consume runtime event and poll metadata only when this module produced it."""
    if type(value) is not _RuntimeEventBindings or value._producer_token is not _RUNTIME_EVENTS_TOKEN:
        raise TypeError("runtime event metadata lacks Events producer provenance")
    return (
        tuple(dict(spec) for spec in value.event_specs),
        tuple(dict(spec) for spec in value.poll_specs),
    )


# ----- Vocabulary constants (design 5.1) -----

# What a bare `.debounce` / `.throttle` (no time segment) means. Design 5.1
# pins both bare forms at 250 ms.
DEFAULT_DEBOUNCE_MS: Final = 250
DEFAULT_THROTTLE_MS: Final = 250

# `<input>` types whose committed value already updates on `change`, so `.lazy`
# (which asks for the committed-value event) is redundant and rejected.
_COMMITTED_INPUT_TYPES: Final = frozenset({"checkbox", "radio"})

# The 22 input-type keywords in the HTML Standard, partitioned by the State
# binding directions Citry can faithfully support. Matching is ASCII-case
# insensitive but deliberately does not strip whitespace: a present nonempty
# value outside this table is invalid authoring, even though browsers normalize
# every unknown value to the Text state.
# Event-binding boolean modifiers (design 5.1 modifier table).
_EVENT_FLAGS: Final = frozenset({"prevent", "stop", "self", "once"})
_KEY_FILTERS: Final = frozenset({"enter", "escape"})
# The only event names whose events carry a `key`, matched exactly. The
# template parser applies the same rule to Vue listeners such as `@click.enter`.
_KEYBOARD_EVENTS: Final = frozenset({"keydown", "keyup", "keypress"})

_PREFIX_EVENT: Final = "@c-"
_PREFIX_STATE: Final = ":c-"

# The base marker (after the `c-` in `@c-poll`) that means "interval", not a
# DOM event.
_POLL: Final = "poll"


# A modifier time segment: a whole number of milliseconds or seconds.
_TIME_RE: Final = re.compile(r"^(?P<n>\d+)(?P<unit>ms|s)$")


def _citry_tag_identity(tag_name: str) -> str | None:
    """Return folded Citry identity only for the exact lowercase prefix."""
    if not tag_name.startswith("c-"):
        return None
    return f"c-{tag_name[2:].lower()}"


def _time_to_ms(segment: str) -> int:
    """Convert a matched time segment (``"30s"``, ``"300ms"``) to milliseconds."""
    match = _TIME_RE.match(segment)
    if match is None:  # pragma: no cover - callers pre-check with _TIME_RE
        msg = f"not a time segment: {segment!r}"
        raise ValueError(msg)
    value = int(match.group("n"))
    return value if match.group("unit") == "ms" else value * 1000


# ----- Parsed-attribute plumbing -----


@dataclass(frozen=True, slots=True)
class _Attr:
    """One parsed attribute of a start tag: its name, and its value if written."""

    name: str
    value: str | None  # None when the attribute was written with no `=value`
    source: str  # the exact source text, re-emitted verbatim for non-bindings


def _split_name(attr_name: str, prefix: str) -> tuple[str, list[str]]:
    """
    Split a binding attribute name into its base name and modifier segments.

    ``:c-query.debounce.300ms`` with prefix ``:c-`` yields ``("query",
    ["debounce", "300ms"])``; the ``.on:<event>`` segment keeps its ``:`` (only
    ``.`` splits). The base name is the DOM event for ``@c-*`` or the State
    field for ``:c-*``.
    """
    rest = attr_name[len(prefix) :]
    segments = rest.split(".")
    return segments[0], segments[1:]


def _split_handler_args(
    info: EventsInfo,
    value: str,
    attr_name: str,
    location: _Location,
) -> tuple[str, str | None]:
    """
    Split a binding value into its handler name and raw arg expression.

    ``rate({stars: 5})`` yields ``("rate", "{stars: 5}")``; a bare ``save``
    yields ``("save", None)``. The arg expression is whatever the author wrote
    between the outermost parentheses, carried verbatim (citry never parses
    it); ``()`` with nothing inside is treated as no args. The JavaScript
    interior is deliberately opaque: only the outer server-handler call shell
    is recognized, so parentheses in strings, template literals, regexes, and
    nested expressions cannot terminate the binding early.

    A complete declared handler name wins before shell recognition. This is
    important because an explicit ``@event(name=...)`` wire name may itself
    contain parentheses. Otherwise, a call shell starts at the first ``(`` and
    must end at the final non-whitespace ``)``. Consuming the complete winning
    string here is the shared strictness rule for literal element bindings,
    spread-contributed element bindings, and component-tag client bindings.
    """
    text = value.strip()
    if text in info.handlers:
        return text, None
    open_index = text.find("(")
    if open_index == -1:
        return text, None
    handler = text[:open_index].strip()
    if not text.endswith(")"):
        message = f"{attr_name!r}: a server-handler call must end at its final ')' with no trailing text"
        raise ValueError(message + location.suffix())
    args = text[open_index + 1 : -1]
    return handler, (None if not args.strip() else args)


# ----- Modifier tokenizing -----


@dataclass(frozen=True, slots=True)
class _ModToken:
    """
    One tokenized modifier: a ``kind`` and an optional value.

    ``kind`` is one of ``"flag"`` (``value`` is the flag name), ``"debounce"``
    / ``"throttle"`` (``value`` is milliseconds or ``None`` for the bare form),
    ``"on"`` (``value`` is the override event), ``"time"`` (``value`` is a
    standalone interval in milliseconds), or ``"unknown"`` (``value`` is the
    raw segment).
    """

    kind: str
    value: str | int | None


def _tokenize_modifiers(segments: list[str]) -> list[_ModToken]:
    """Tokenize a binding's modifier segments, folding a time segment into the debounce/throttle before it."""
    tokens: list[_ModToken] = []
    index = 0
    count = len(segments)
    while index < count:
        segment = segments[index]
        if segment in _EVENT_FLAGS or segment in _KEY_FILTERS or segment == "lazy":
            tokens.append(_ModToken("flag", segment))
        elif segment in ("debounce", "throttle"):
            time_ms: int | None = None
            # A time segment directly after `.debounce`/`.throttle` is its value.
            if index + 1 < count and _TIME_RE.match(segments[index + 1]):
                time_ms = _time_to_ms(segments[index + 1])
                index += 1
            tokens.append(_ModToken(segment, time_ms))
        elif segment.startswith("on:"):
            tokens.append(_ModToken("on", segment[len("on:") :]))
        elif _TIME_RE.match(segment):
            tokens.append(_ModToken("time", _time_to_ms(segment)))
        else:
            tokens.append(_ModToken("unknown", segment))
        index += 1
    return tokens


# ----- The rewrite context (shared by both stages) -----


@dataclass(frozen=True, slots=True)
class _Location:
    """Where a binding lives, for error messages: the component and a place in it."""

    comp_name: str
    where: str  # e.g. "line 4" (compiled stage) or "<button> after dynamic attributes resolved"

    def suffix(self) -> str:
        return f" (in {self.comp_name} template, {self.where})"


def _input_type_is_browser_dynamic(attr_names: list[str], *, include_python_attrs: bool) -> bool:
    """Whether Vue/browser attribute syntax may replace an input's static type."""
    for name in attr_names:
        folded = name.lower()
        if include_python_attrs and folded in {"c-type", "c-bind"}:
            return True
        if folded == "v-bind" or folded.startswith(("v-bind.", ":[", ".[", "v-bind:[")):
            return True
        if folded in {".type", ":type"} or folded.startswith((".type.", ":type.")):
            return True
        if folded == "v-bind:type" or folded.startswith("v-bind:type."):
            return True
    return False


def _fail(location: _Location, message: str) -> NoReturn:
    msg = message + location.suffix()
    raise ValueError(msg)


# ----- Spec building per channel -----


def _resolve_handler(info: EventsInfo, handler: str, attr_name: str, location: _Location) -> None:
    """Reject a handler name the owning component did not declare."""
    if handler and handler in info.handlers:
        return
    declared = ", ".join(sorted(info.handlers)) or "(none)"
    _fail(
        location,
        f"{attr_name!r} names event handler {handler!r}, which is not a declared handler of"
        f" {location.comp_name}. Declared handlers: {declared}",
    )


def _merged_timing(
    info: EventsInfo, handler: str, debounce: int | None, throttle: int | None
) -> tuple[int | None, int | None]:
    """Fold a binding's own timing over the handler's configured defaults (the binding wins)."""
    resolved = info.handlers[handler]
    return (
        debounce if debounce is not None else resolved.debounce,
        throttle if throttle is not None else resolved.throttle,
    )


def _validate_timing_pair(debounce: int | None, throttle: int | None, attr_name: str, location: _Location) -> None:
    for name, value in (("debounce", debounce), ("throttle", throttle)):
        if value is not None and value > 2**53 - 1:
            _fail(location, f"{attr_name!r}: .{name} timing exceeds the JavaScript safe-integer limit")


def _reject_second_key_filter(
    attr_name: str, key: str | None, second: str, location: _Location, *, handler: str | None = None
) -> None:
    """Fail when one binding carries a second key filter, naming both so the author picks."""
    if key is None:
        return
    # A binding sends for one key, and a second filter would silently replace
    # the first. Vue reads `@keydown.enter.escape` as "either key", so say
    # plainly that these bindings do not, and how to get that from Vue.
    message = (
        f"{attr_name!r} has two key filters, '.{key}' and '.{second}'. A Citry Events binding"
        f" reacts to one key, so it cannot read them as either key the way a Vue listener does."
        f" Keep one key filter"
    )
    if handler is None:
        _fail(location, message + ".")
    event = _split_name(attr_name, _PREFIX_EVENT)[0]
    _fail(
        location,
        f"{message}, or call the handler from a Vue listener, which accepts several keys:"
        f" @{event}.{key}.{second}=\"$sendEvent('{handler}')\".",
    )


def _build_event_spec(info: EventsInfo, event: str, attr: _Attr, location: _Location) -> dict[str, Any]:
    """Validate and build one typed event spec from an ``@c-<event>`` attribute."""
    if not event:
        # `@c-="save"` (or `@c-.prevent=...`): the `@c-` names no DOM event, so
        # there is nothing to listen for. Reject it rather than ship event="".
        _fail(location, f"{attr.name!r} needs a DOM event name, e.g. '@c-click'")
    if attr.value is None or not attr.value.strip():
        _fail(location, f'{attr.name!r} needs a handler name as its value, e.g. {attr.name}="save"')
    handler, args = _split_handler_args(info, attr.value or "", attr.name, location)
    _resolve_handler(info, handler, attr.name, location)

    _, segments = _split_name(attr.name, _PREFIX_EVENT)
    prevent = stop = self_flag = once = False
    key: str | None = None
    debounce: int | None = None
    throttle: int | None = None
    for token in _tokenize_modifiers(segments):
        if token.kind == "flag" and token.value in _EVENT_FLAGS:
            prevent = prevent or token.value == "prevent"
            stop = stop or token.value == "stop"
            self_flag = self_flag or token.value == "self"
            once = once or token.value == "once"
        elif token.kind == "flag" and token.value in _KEY_FILTERS:
            _reject_second_key_filter(attr.name, key, str(token.value), location, handler=handler)
            key = str(token.value)
        elif token.kind == "flag":  # lazy
            _fail(location, f"{attr.name!r}: '.lazy' only applies to a two-way state binding (:c-...), not an event")
        elif token.kind == "debounce":
            debounce = _debounce_ms(token)
        elif token.kind == "throttle":
            throttle = _throttle_ms(token)
        elif token.kind == "on":
            _fail(location, f"{attr.name!r}: '.on:' only applies to a two-way state binding (:c-...), not an event")
        elif token.kind == "time":
            _fail(location, f"{attr.name!r}: a time segment only applies to @c-poll; use '.debounce'/'.throttle' here")
        else:  # unknown
            _fail(location, f"{attr.name!r} has an unknown modifier '.{token.value}'")

    # A native event by any other name has no key, so the binding would
    # silently never send. Reject it when the template loads, as the template
    # parser does for a Vue listener such as `@click.enter`.
    if key is not None and event not in _KEYBOARD_EVENTS:
        _fail(
            location,
            f"{attr.name!r} uses '.{key}' on the {event!r} event. '.enter' and '.escape' work only on"
            f" keyboard events ('keydown', 'keyup', 'keypress'), which carry the pressed key. Remove"
            f" '.{key}', or listen to 'keydown' or 'keyup' to react to a key.",
        )

    debounce, throttle = _merged_timing(info, handler, debounce, throttle)
    _validate_timing_pair(debounce, throttle, attr.name, location)
    return {
        "event": event,
        "handler": handler,
        "args": args,
        "prevent": prevent,
        "stop": stop,
        "self": self_flag,
        "once": once,
        "key": key,
        "debounce": debounce,
        "throttle": throttle,
    }


def _debounce_ms(token: _ModToken) -> int:
    """The milliseconds a ``.debounce`` token carries: its time segment, or the bare 250 ms default."""
    if isinstance(token.value, int):
        return token.value
    return DEFAULT_DEBOUNCE_MS


def _throttle_ms(token: _ModToken) -> int:
    """The milliseconds a ``.throttle`` token carries: its time segment, or the bare 250 ms default."""
    if isinstance(token.value, int):
        return token.value
    return DEFAULT_THROTTLE_MS


def _build_poll_spec(info: EventsInfo, attr: _Attr, location: _Location) -> dict[str, Any]:
    """Validate and build one typed poll spec from an ``@c-poll.<N>s`` attribute."""
    if attr.value is None or not attr.value.strip():
        _fail(location, f'{attr.name!r} needs a handler name as its value, e.g. {attr.name}="refresh"')
    handler, args = _split_handler_args(info, attr.value or "", attr.name, location)
    _resolve_handler(info, handler, attr.name, location)

    # The poll interval is one time segment in seconds (design 5.1): a
    # millisecond segment, a second interval, or any other modifier is a load
    # error rather than a guess. Read the raw segments so the unit is visible
    # here (the tokenizer has already folded a time segment to milliseconds).
    _, segments = _split_name(attr.name, _PREFIX_EVENT)
    interval: int | None = None
    for segment in segments:
        match = _TIME_RE.match(segment)
        if match is None:
            _fail(location, f"{attr.name!r}: @c-poll takes only an interval like '.30s', not '.{segment}'")
        elif match.group("unit") != "s":
            _fail(location, f"{attr.name!r}: the @c-poll interval is in seconds, e.g. '.30s', not '.{segment}'")
        elif interval is not None:
            _fail(location, f"{attr.name!r}: @c-poll takes exactly one interval; found a second time segment")
        else:
            interval = _time_to_ms(segment)
    if interval is None:
        _fail(location, f"{attr.name!r}: @c-poll needs an interval, e.g. @c-poll.30s")
    if interval <= 0:
        _fail(location, f"{attr.name!r}: @c-poll interval must be positive")
    if interval > 2**53 - 1:
        _fail(location, f"{attr.name!r}: @c-poll interval exceeds the JavaScript safe-integer limit")
    return {"handler": handler, "args": args, "interval": interval}


def _build_bind_spec(
    info: EventsInfo, field: str, attr: _Attr, element: _Element, location: _Location
) -> dict[str, Any]:
    """Validate and build one typed control spec from a ``:c-<field>`` attribute."""
    _resolve_state_field(info, field, attr.name, location)

    value = attr.value.strip() if attr.value is not None else ""
    two_way = value != ""
    handler = value if two_way else None

    _, segments = _split_name(attr.name, _PREFIX_STATE)
    lazy = False
    on_event: str | None = None
    key: str | None = None
    debounce: int | None = None
    throttle: int | None = None
    for token in _tokenize_modifiers(segments):
        if token.kind == "flag" and token.value == "lazy":
            lazy = True
        elif token.kind == "flag" and token.value in _KEY_FILTERS:
            _reject_second_key_filter(attr.name, key, str(token.value), location)
            key = str(token.value)
        elif token.kind == "flag":  # prevent/stop/self/once: event-only
            _fail(
                location, f"{attr.name!r}: '.{token.value}' is an event modifier and does not apply to a state binding"
            )
        elif token.kind == "debounce":
            debounce = _debounce_ms(token)
        elif token.kind == "throttle":
            throttle = _throttle_ms(token)
        elif token.kind == "on":
            # A binding sends on exactly one update event, so a second `.on:`
            # would silently replace the first. Name both so the author picks.
            if on_event is not None:
                _fail(
                    location,
                    f"{attr.name!r} names two update events, '.on:{on_event}' and '.on:{token.value}';"
                    f" a state binding sends on one event, so keep one '.on:'",
                )
            on_event = str(token.value)
            # `.on:` must name the update event; an empty name (`.on:=`) is a
            # malformed shape, so reject it rather than ship on="" to the client.
            if not on_event:
                _fail(location, f"{attr.name!r}: '.on:' needs an event name, e.g. '.on:keyup'")
        elif token.kind == "time":
            _fail(location, f"{attr.name!r}: a bare time segment is not a valid state-binding modifier")
        else:  # unknown
            _fail(location, f"{attr.name!r} has an unknown modifier '.{token.value}'")

    if not two_way:
        # A one-way binding writes the field into the control, so it needs an
        # element that can hold a value just as much as a two-way one does.
        _validate_binding_target(
            element,
            binding_mode="one-way",
            attr_name=attr.name,
            location=location,
        )
        # It only reads state onto the control; it takes no update-timing or
        # key modifiers (there is no update to time).
        if lazy or on_event is not None or debounce is not None or throttle is not None or key is not None:
            _fail(
                location,
                f"{attr.name!r} is a one-way binding (no handler value), so it cannot carry an update-timing modifier"
                f" (.lazy, .debounce, .throttle, .on:) or a key filter; give it a handler value to make it two-way",
            )
        return {
            "field": field,
            "binding_mode": "one-way",
            "handler": None,
            "lazy": False,
            "on": None,
            "key": None,
            "debounce": None,
            "throttle": None,
        }

    _resolve_handler(info, handler or "", attr.name, location)
    _require_writable(info, field, attr.name, location)
    if lazy and on_event is not None:
        _fail(location, f"{attr.name!r}: '.lazy' and '.on:' cannot be combined; choose one update event")
    _validate_two_way_control(element, lazy=lazy, on_event=on_event, attr_name=attr.name, location=location)
    # The update event is the one whose `key` the browser checks. The default
    # update events (`input`, `change`) and every other `.on:` name carry no
    # key, so the binding would silently never send. Reject it when the
    # template loads, as `_build_event_spec` does for `@c-click.enter`.
    if key is not None and on_event not in _KEYBOARD_EVENTS:
        _fail(location, _keyless_update_event_error(attr.name, key, on_event, element, lazy=lazy))

    debounce, throttle = _merged_timing(info, handler or "", debounce, throttle)
    _validate_timing_pair(debounce, throttle, attr.name, location)
    return {
        "field": field,
        "binding_mode": "two-way",
        "handler": handler,
        "lazy": lazy,
        "on": on_event,
        "key": key,
        "debounce": debounce,
        "throttle": throttle,
    }


def _keyless_update_event_error(
    attr_name: str, key: str, on_event: str | None, element: _Element, *, lazy: bool
) -> str:
    """Explain a ``:c-*`` key filter whose update event carries no key, naming that event and both fixes."""
    # The fix names the modifier the author has to change, because adding
    # `.on:` next to `.lazy` or a second `.on:` is not the right repair.
    if on_event is not None:
        where = f"on the {on_event!r} update event"
        fix = f"Change '.on:{on_event}' to '.on:keydown' or '.on:keyup'"
    else:
        # Name the default the browser would use, so the author sees which
        # event `.on:` replaces. When the tag or input type is resolved
        # later (by `c-is`, `c-type`, `c-bind`, or Vue's `:type`), the default
        # could be either keyless event.
        default = _default_update_event(element, lazy=lazy)
        where = (
            f"on the control's default update event {default!r}"
            if default is not None
            else "on the control's default update event ('input' or 'change')"
        )
        fix = "Replace '.lazy' with '.on:keydown' or '.on:keyup'" if lazy else "Add '.on:keydown' or '.on:keyup'"
    return (
        f"{attr_name!r} uses '.{key}' {where}. '.enter' and '.escape' work only on keyboard events"
        f" ('keydown', 'keyup', 'keypress'), which carry the pressed key. {fix} to send on a key,"
        f" or remove '.{key}'."
    )


def _default_update_event(element: _Element, *, lazy: bool) -> str | None:
    """The default update event of a known native control, or ``None`` when the tag or type is resolved later."""
    # A control whose value commits as a whole (a choice, a checkbox) always
    # sends on `change`; a text control sends on every keystroke unless `.lazy`.
    if _committed_control(element) is not None:
        return "change"
    tag = element.tag_name.lower()
    if tag == "textarea" or (tag == "input" and element.type_static_known):
        return "change" if lazy else "input"
    return None


def _committed_control(element: _Element) -> str | None:
    """
    Describe a known native control whose value already commits on ``change``, such as ``<select>``.

    Returns ``None`` for any other element, and for an ``<input>`` whose type
    is resolved later, because its default update event is not known yet.
    """
    tag = element.tag_name.lower()
    if tag == "select":
        return "<select>"
    if tag == "input" and element.type_static_known:
        input_type = _input_type(element)
        if input_type in _COMMITTED_INPUT_TYPES:
            return f'<input type="{input_type}">'
    return None


def _resolve_state_field(info: EventsInfo, field: str, attr_name: str, location: _Location) -> None:
    """Reject a ``:c-*`` field that is not a public State field of the owning component."""
    if info.state_cls is None or info.state_meta is None:
        _fail(
            location,
            f"{attr_name!r} binds State field {field!r}, but {location.comp_name} declares no State class."
            f" Declare a State class with that field",
        )
        return
    state_fields = {member.name for member in fields(info.state_cls)}
    if field not in state_fields:
        declared = ", ".join(sorted(state_fields)) or "(none)"
        _fail(
            location, f"{attr_name!r} binds {field!r}, which is not a State field. Declared State fields: {declared}"
        )
    if field not in info.state_meta.public:
        public = ", ".join(info.state_meta.public) or "(none)"
        _fail(
            location,
            f"{attr_name!r} binds {field!r}, which is not a public State field (not in _public), so bindings cannot"
            f" touch it. Public fields: {public}",
        )


def _require_writable(info: EventsInfo, field: str, attr_name: str, location: _Location) -> None:
    """Reject a two-way binding to a public-but-read-only field (not in ``_model``)."""
    assert info.state_meta is not None  # a two-way binding reached here only past _resolve_state_field  # noqa: S101
    if field not in info.state_meta.model:
        writable = ", ".join(info.state_meta.model) or "(none)"
        _fail(
            location,
            f"{attr_name!r} is a two-way binding to {field!r}, which is public but not writable (not in _model)."
            f" Writable fields: {writable}",
        )


def _validate_binding_target(element: _Element, *, binding_mode: str, attr_name: str, location: _Location) -> str:
    """Apply shared target rules with the runtime template location."""
    try:
        return _classify_state_binding_target(element, binding_mode=binding_mode, attr_name=attr_name)
    except ValueError as exc:
        _fail(location, str(exc))


def _validate_two_way_control(
    element: _Element, *, lazy: bool, on_event: str | None, attr_name: str, location: _Location
) -> None:
    """Run the control-type validations for a two-way binding (design 5.1's update-event table)."""
    kind = _validate_binding_target(
        element,
        binding_mode="two-way",
        attr_name=attr_name,
        location=location,
    )
    if kind == "deferred":
        # The final selected tag determines both whether it is bindable and
        # which default update event/modifier combinations it supports.
        return
    if kind != "control":
        # A custom element has no default update event, so it must name one.
        if on_event is None:
            _fail(
                location,
                _custom_update_event_error(element.tag_name, attr_name),
            )
    elif on_event is None and lazy:
        # `.lazy` moves a text control's update to `change`; on a control that
        # already sends on `change` it would do nothing, so reject it.
        committed = _committed_control(element)
        if committed is not None:
            _fail(
                location, f"{attr_name!r}: '.lazy' has no effect on {committed}; its value already commits on 'change'"
            )


def _classify_binding(attr_name: str) -> str | None:
    """Which channel an attribute name feeds, or ``None`` when it is not a binding."""
    if attr_name.startswith(_PREFIX_EVENT):
        base, _ = _split_name(attr_name, _PREFIX_EVENT)
        return _CHANNEL_POLL if base == _POLL else _CHANNEL_EVENT
    if attr_name.startswith(_PREFIX_STATE):
        return _CHANNEL_CONTROL
    return None


def _build_spec(channel: str, info: EventsInfo, attr: _Attr, element: _Element, location: _Location) -> dict[str, Any]:
    if channel == _CHANNEL_EVENT:
        event, _ = _split_name(attr.name, _PREFIX_EVENT)
        return _build_event_spec(info, event, attr, location)
    if channel == _CHANNEL_POLL:
        return _build_poll_spec(info, attr, location)
    field, _ = _split_name(attr.name, _PREFIX_STATE)
    return _build_bind_spec(info, field, attr, element, location)


@dataclass(frozen=True, slots=True)
class CompiledCitryBoundaryBinding:
    """One validated component-boundary ``@c-*`` server binding."""

    channel: str
    spec: Mapping[str, Any]


def compile_citry_boundary_binding(
    info: EventsInfo,
    comp_name: str,
    tag_name: str,
    attr_name: str,
    value: str,
    *,
    line: int,
    column: int,
) -> CompiledCitryBoundaryBinding:
    """
    Validate and compile a winning ``@c-*`` component-tag client binding in its source parent.

    Component bindings use the same name, modifier, handler, timing, and
    opaque-call-shell parser as element bindings. The compiled spec is retained
    as prepared component-call data for native Vue listener generation.
    """
    channel = _classify_binding(attr_name)
    if channel not in (_CHANNEL_EVENT, _CHANNEL_POLL):
        msg = f"Expected a Citry event binding on <{tag_name}>, got {attr_name!r}."
        raise ValueError(msg)
    location = _Location(
        comp_name=comp_name,
        where=f"line {line}, column {column}, on <{tag_name}> component boundary",
    )
    spec = _build_spec(
        channel,
        info,
        _Attr(name=attr_name, value=value, source=attr_name),
        _Element(tag_name=tag_name, input_type=None, type_static_known=False),
        location,
    )
    return CompiledCitryBoundaryBinding(channel=channel, spec=MappingProxyType(spec))


# ----- Stage one: compiled-node rewrite -----


@dataclass(frozen=True, slots=True)
class CompiledTemplateBindings:
    """
    The result of transforming one compiled template body.

    Attributes:
        nodes: The compiled body with real element bindings retained as typed
            metadata. Literal text is untouched.
        two_way_fields: The State fields bound two-way anywhere in the template.
            Each binding has already been checked against ``_model``; this
            aggregate remains available for diagnostics and introspection.

    """

    nodes: list[Any]
    two_way_fields: frozenset[str]


def compile_template_bindings(
    info: EventsInfo,
    comp_name: str,
    nodes: list[Any],
) -> CompiledTemplateBindings:
    """
    Validate and transform parser-proven bindings in a compiled template body.

    Ordinary static HTML usually compiles straight to strings. The template
    compiler deliberately preserves regions containing ``@c-*`` or ``:c-*``
    as :class:`ElementAttrsNode` objects, so this pass can
    distinguish real attributes from binding-shaped text. Otherwise-static
    regions collapse back to a string after transformation.

    Args:
        info: The owning component's resolved events info (handlers, State).
        comp_name: The owning component's name, for error messages.
        nodes: The compiled body nodes.

    Returns:
        The transformed nodes and two-way field diagnostics.

    Raises:
        ValueError: On any invalid binding (undeclared handler, non-public
            field, illegal modifier combination, invalid placement, or
            authored compiler output), with the template location.

    """
    two_way_fields: set[str] = set()
    transformed = _transform_compiled_body(
        nodes,
        info=info,
        comp_name=comp_name,
        two_way_fields=two_way_fields,
    )
    return CompiledTemplateBindings(nodes=transformed, two_way_fields=frozenset(two_way_fields))


def _transform_compiled_body(
    body: list[Any],
    *,
    info: EventsInfo,
    comp_name: str,
    two_way_fields: set[str],
) -> list[Any]:
    """Recursively transform every compiled body owned by the same component."""
    from citry.nodes import (  # noqa: PLC0415
        ComponentNode,
        ElementAttrsNode,
        FillNode,
        ForNode,
        IfNode,
        SlotNode,
    )

    transformed: list[Any] = []
    for item in body:
        if isinstance(item, ElementAttrsNode):
            needs_emitted_tag_inference = not hasattr(item, "tag")
            tag_name = item.tag_name
            if needs_emitted_tag_inference and transformed and isinstance(transformed[-1], str):
                # The compiler places the emitted ``<tag`` chunk immediately
                # before its attribute-region node. This matters for the
                # zero-cost static `<c-element is="...">` path: its source
                # position still names c-element, while the emitted chunk
                # names the actual target element.
                emitted_prefix = transformed[-1].rsplit("<", 1)[-1]
                if emitted_prefix and not any(char.isspace() or char in "/>" for char in emitted_prefix):
                    tag_name = emitted_prefix
            transformed.append(
                _transform_element_attrs_node(
                    item,
                    tag_name=tag_name,
                    info=info,
                    comp_name=comp_name,
                    two_way_fields=two_way_fields,
                )
            )
            continue

        if isinstance(item, ComponentNode):
            if item.name == "element":
                transformed_element = _transform_element_attrs(
                    tag_name="c-element",
                    source=item.source,
                    attrs=item.attrs,
                    info=info,
                    comp_name=comp_name,
                    two_way_fields=two_way_fields,
                )
                item.attrs = transformed_element[0]
                item._element_event_bindings = transformed_element[1]
                item._element_poll_bindings = transformed_element[2]
                item._element_control_bindings = transformed_element[3]
                item._element_runtime_events_candidate = info.events_cls is not None and any(
                    attr.key == "c-bind" for attr in item.attrs
                )
            else:
                _validate_component_boundary_attrs(
                    item,
                    info=info,
                    comp_name=comp_name,
                )
            item.body = _transform_compiled_body(
                item.body,
                info=info,
                comp_name=comp_name,
                two_way_fields=two_way_fields,
            )
            transformed.append(item)
            continue

        if isinstance(item, (SlotNode, FillNode)):
            _reject_structural_attrs(item, comp_name=comp_name)
            item.body = _transform_compiled_body(
                item.body,
                info=info,
                comp_name=comp_name,
                two_way_fields=two_way_fields,
            )
            transformed.append(item)
            continue

        if isinstance(item, (IfNode, ForNode)):
            branches = []
            for branch in item.branches:
                _reject_attrs_without_element(
                    branch[1],
                    tag_name="c-if/c-for control-flow branch",
                    source=item.source,
                    comp_name=comp_name,
                )
                branches.append(
                    (
                        branch[0],
                        branch[1],
                        _transform_compiled_body(
                            branch[2],
                            info=info,
                            comp_name=comp_name,
                            two_way_fields=two_way_fields,
                        ),
                        branch[3],
                    )
                )
            item.branches = tuple(branches)

        transformed.append(item)
    return transformed


def _transform_element_attrs_node(
    node: Any,
    *,
    tag_name: str,
    info: EventsInfo,
    comp_name: str,
    two_way_fields: set[str],
) -> Any:
    """Transform one ordinary HTML element's structured attribute region."""
    if hasattr(node, "_runtime_control_candidate") and node._has_spread and info.state_cls is not None:
        node._runtime_control_candidate = True
    if hasattr(node, "_runtime_events_candidate") and node._has_spread and info.events_cls is not None:
        node._runtime_events_candidate = True
    attrs, event_bindings, poll_bindings, control_bindings = _transform_element_attrs(
        tag_name=tag_name,
        source=node.source,
        attrs=node.attrs,
        info=info,
        comp_name=comp_name,
        two_way_fields=two_way_fields,
    )
    if not (event_bindings or poll_bindings or control_bindings):
        return node
    if not hasattr(node, "_with_attrs"):
        _fail(
            _compiled_location(comp_name, node.source, node.position),
            "Events bindings are unsupported in non-prepared foreign template regions",
        )
    return node._with_attrs(
        attrs,
        event_bindings=event_bindings,
        poll_bindings=poll_bindings,
        control_bindings=control_bindings,
    )


def _transform_element_attrs(
    *,
    tag_name: str,
    source: Any,
    attrs: tuple[Any, ...],
    info: EventsInfo,
    comp_name: str,
    two_way_fields: set[str],
) -> tuple[
    tuple[Any, ...],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
]:
    """Compile literal bindings in one parser-proven element attribute tuple."""
    from citry.nodes import StaticHtmlAttr  # noqa: PLC0415

    literal_attrs = [attr for attr in attrs if isinstance(attr, StaticHtmlAttr)]
    reserved = next((attr for attr in literal_attrs if attr.key.lower().startswith("data-cev-")), None)
    if reserved is not None:
        _fail(
            _compiled_location(comp_name, source, reserved.position),
            f"{reserved.key!r} is reserved compiler output;"
            " author State bindings with ':c-*' and event bindings with '@c-*' instead",
        )

    bindings = [attr for attr in literal_attrs if _classify_binding(attr.key) is not None]
    if not bindings:
        return attrs, (), (), ()
    state_bindings = [attr for attr in bindings if _classify_binding(attr.key) == _CHANNEL_CONTROL]
    if len(state_bindings) > 1:
        names = [attr.key for attr in state_bindings]
        _fail(
            _compiled_location(comp_name, source, state_bindings[1].position),
            f"one element supports exactly one :c-* State binding; found {names!r}",
        )
    # The browser keeps one Citry Events listener per DOM event on an element,
    # so a second `@c-keydown` would only fail later, when the page renders.
    # Catch it here, with the template line, naming both attributes.
    events_seen: dict[str, str] = {}
    for attr in bindings:
        if _classify_binding(attr.key) != _CHANNEL_EVENT:
            continue
        event, _ = _split_name(attr.key, _PREFIX_EVENT)
        first = events_seen.setdefault(event, attr.key)
        if first != attr.key:
            _fail(
                _compiled_location(comp_name, source, attr.position),
                f"<{tag_name}> has two bindings for the {event!r} event, {first!r} and {attr.key!r}. An element"
                f" sends one Citry Events call per event, so keep one '@c-{event}' binding on it.",
            )

    element_attrs = [_compiled_attr(attr) for attr in attrs]
    element = _element_of(tag_name, element_attrs)
    event_bindings: list[dict[str, object]] = []
    poll_bindings: list[dict[str, object]] = []
    control_bindings: list[dict[str, object]] = []
    for attr in bindings:
        channel = _classify_binding(attr.key)
        assert channel is not None  # filtered above  # noqa: S101
        spec = _build_spec(
            channel,
            info,
            _compiled_attr(attr),
            element,
            _compiled_location(comp_name, source, attr.position),
        )
        if channel == _CHANNEL_EVENT:
            event_bindings.append(
                {
                    "id": f"citryEvent{attr.position[0]:x}",
                    **spec,
                }
            )
        if channel == _CHANNEL_POLL:
            poll_bindings.append(
                {
                    "id": f"citryPoll{attr.position[0]:x}",
                    **spec,
                }
            )
        if channel == _CHANNEL_CONTROL and spec["binding_mode"] == "two-way":
            two_way_fields.add(spec["field"])
        if channel == _CHANNEL_CONTROL:
            control_bindings.append(
                {
                    "id": f"citryControl{attr.position[0]:x}",
                    **spec,
                }
            )

    kept = tuple(attr for attr in attrs if attr not in bindings)
    return kept, tuple(event_bindings), tuple(poll_bindings), tuple(control_bindings)


def _validate_component_boundary_attrs(
    node: Any,
    *,
    info: EventsInfo,
    comp_name: str,
) -> None:
    """Validate literal component-boundary bindings without consuming them."""
    from citry.nodes import StaticHtmlAttr  # noqa: PLC0415

    tag_name = f"c-{node.name}"
    for attr in node.attrs:
        if not isinstance(attr, StaticHtmlAttr):
            continue
        location = _compiled_location(comp_name, node.source, attr.position)
        if attr.key.lower().startswith("data-cev-"):
            _fail(
                location,
                f"{attr.key!r} is reserved compiler output; author event bindings with '@c-*' instead",
            )
        channel = _classify_binding(attr.key)
        if channel is None:
            continue
        if channel == _CHANNEL_CONTROL:
            _fail(
                location,
                f"<{tag_name}> is a component tag, but {attr.key!r} binds State on it."
                " State bindings go on HTML controls: a child component binds its own State in its template."
                " Pass data down with a native Vue prop binding (`:prop` or `v-bind:prop`) or Python kwargs.",
            )
        line, column = _line_column(node.source, attr.position[0])
        compile_citry_boundary_binding(
            info,
            comp_name,
            tag_name,
            attr.key,
            "" if attr.value is True else str(attr.value),
            line=line,
            column=column,
        )


def _reject_structural_attrs(node: Any, *, comp_name: str) -> None:
    _reject_attrs_without_element(
        node.attrs,
        tag_name=type(node).__name__.removesuffix("Node").lower(),
        source=node.source,
        comp_name=comp_name,
    )


def _reject_attrs_without_element(
    attrs: tuple[Any, ...],
    *,
    tag_name: str,
    source: Any,
    comp_name: str,
) -> None:
    """Reject Events-owned attributes on a structural node with no DOM target."""
    from citry.nodes import StaticHtmlAttr  # noqa: PLC0415

    for attr in attrs:
        if not isinstance(attr, StaticHtmlAttr):
            continue
        if attr.key.lower().startswith("data-cev-"):
            _fail(
                _compiled_location(comp_name, source, attr.position),
                f"{attr.key!r} is reserved compiler output;"
                " author State bindings with ':c-*' and event bindings with '@c-*' instead",
            )
        if _classify_binding(attr.key) is not None:
            _fail(
                _compiled_location(comp_name, source, attr.position),
                f"<{tag_name}> is a Citry structural tag, so {attr.key!r} has no HTML element target.",
            )


def _compiled_attr(attr: Any) -> _Attr:
    """Adapt one compiled HtmlAttr to the existing binding validators."""
    from citry.nodes import ExprHtmlAttr, StaticHtmlAttr, TemplateHtmlAttr  # noqa: PLC0415

    if isinstance(attr, StaticHtmlAttr):
        value = None if attr.value is True else str(attr.value)
    elif isinstance(attr, ExprHtmlAttr):
        value = None if attr.expr is True else str(attr.expr)
    elif isinstance(attr, TemplateHtmlAttr):
        value = attr.template
    else:  # pragma: no cover - compiler output is a closed HtmlAttr family
        msg = f"Unsupported compiled HTML attribute {type(attr).__name__}."
        raise TypeError(msg)
    return _Attr(name=attr.key, value=value, source=_source_slice(attr.source, attr.position))


def _source_slice(source: Any, position: tuple[int, int]) -> str:
    """Slice parser byte offsets without confusing them for Python code points."""
    encoded = str(source).encode("utf-8")
    return encoded[position[0] : position[1]].decode("utf-8")


def _line_column(source: Any, byte_index: int) -> tuple[int, int]:
    prefix = str(source).encode("utf-8")[:byte_index].decode("utf-8")
    line = prefix.count("\n") + 1
    column = len(prefix.rsplit("\n", 1)[-1]) + 1
    return line, column


def _compiled_location(
    comp_name: str,
    source: Any,
    position: tuple[int, int],
) -> _Location:
    line, _ = _line_column(source, position[0])
    return _Location(
        comp_name=comp_name,
        where=f"line {line}",
    )


def _element_of(tag_name: str, attrs: list[_Attr]) -> _Element:
    """Adapt compiled attributes to the shared static target classifier."""
    element = _state_binding_element(tag_name, [(attr.name, attr.value) for attr in attrs])
    # Vue browser-side bindings can replace a literal input type after
    # server compilation; keep that uncertainty in the shared descriptor.
    names = [attr.name for attr in attrs]
    if _input_type_is_browser_dynamic(names, include_python_attrs=True):
        return _Element(
            tag_name=element.tag_name,
            input_type=element.input_type,
            type_static_known=False,
            tag_static_known=element.tag_static_known,
        )
    return element


# ----- Stage two: render-time (spread) rewrite -----


def rewrite_resolved_attrs(
    info: EventsInfo, comp_name: str, tag_name: str, attrs: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Stage two: rewrite bindings that arrive on an element at render time.

    Fires through the ``on_attrs_resolved`` hook for every element with dynamic
    attributes. Raw ``@c-*`` / ``:c-*`` keys are compiled exactly like stage
    one. Runtime State controls use producer-authenticated metadata and are
    validated against the final resolved input type before HTML reaches the browser.

    Args:
        info: The owning component's resolved events info.
        comp_name: The owning component's name, for error messages.
        tag_name: The element's tag name.
        attrs: The element's resolved attribute dict.

    Returns:
        A new attribute dict with the bindings rewritten, or ``None`` when the
        element carried no binding (leave the dict untouched).

    Raises:
        ValueError: On any invalid binding, with the render-time location.

    """
    forged_private = next(
        (key for key in attrs if isinstance(key, str) and key.lower() in {RUNTIME_CONTROL_ATTR, RUNTIME_EVENTS_ATTR}),
        None,
    )
    if forged_private is not None:
        raise TypeError(f"{forged_private!r} is reserved internal Events metadata")
    binding_keys = [key for key in attrs if isinstance(key, str) and _classify_binding(key) is not None]
    if not binding_keys:
        return None

    # The hook is invoked only for final HTML element attributes. Component
    # boundary bindings are captured and validated through their typed
    # relationship path before this stage.
    location = _Location(comp_name=comp_name, where=f"<{tag_name}> after dynamic attributes resolved")
    state_binding_keys = [key for key in binding_keys if _classify_binding(key) == _CHANNEL_CONTROL]
    if len(state_binding_keys) > 1:
        _fail(location, f"one element supports exactly one :c-* State binding; found {state_binding_keys!r}")
    element = _resolved_element(tag_name, attrs, location)

    result = {key: value for key, value in attrs.items() if key not in binding_keys}
    event_specs: list[dict[str, Any]] = []
    runtime_poll_specs: list[dict[str, Any]] = []
    bind_specs: list[dict[str, Any]] = []
    for key in binding_keys:
        channel = _classify_binding(key)
        assert channel is not None  # filtered above  # noqa: S101
        raw = attrs[key]
        # A spread value is the attribute's value; a bare boolean True means the
        # key was contributed with no value (a one-way :c-* binding).
        value = None if raw is True else _as_str(raw)
        spec = _build_spec(channel, info, _Attr(name=key, value=value, source=key), element, location)
        if channel == _CHANNEL_EVENT:
            event_specs.append(spec)
        elif channel == _CHANNEL_POLL:
            runtime_poll_specs.append(spec)
        else:
            bind_specs.append(spec)

    if event_specs and any(spec["args"] is not None for spec in event_specs):
        _fail(location, "runtime-resolved @c-* event bindings support handler names without argument expressions")
    if runtime_poll_specs and any(spec["args"] is not None for spec in runtime_poll_specs):
        _fail(location, "runtime-resolved @c-poll bindings support handler names without argument expressions")
    if event_specs or runtime_poll_specs:
        normalized_events = tuple(MappingProxyType(dict(spec)) for spec in event_specs)
        normalized_polls = tuple(MappingProxyType(dict(spec)) for spec in runtime_poll_specs)
        result[RUNTIME_EVENTS_ATTR] = _RuntimeEventBindings(
            normalized_events,
            normalized_polls,
            _RUNTIME_EVENTS_TOKEN,
        )
    if bind_specs:
        if len(bind_specs) != 1:
            _fail(location, f"one element supports exactly one :c-* State binding; found {len(bind_specs)}")
        normalized = tuple(MappingProxyType(dict(spec)) for spec in bind_specs)
        result[RUNTIME_CONTROL_ATTR] = _RuntimeControlBindings(normalized, _RUNTIME_CONTROL_TOKEN)
    return result


def _resolved_element(tag_name: str, attrs: dict[str, Any], location: _Location) -> _Element:
    """Describe the final rendered element, preserving browser-only ``:type`` uncertainty."""
    type_keys = [key for key in attrs if isinstance(key, str) and key.lower() == "type"]
    if len(type_keys) > 1:
        _fail(
            location,
            "the resolved element contains more than one case-variant of the HTML 'type' attribute;"
            " keep exactly one spelling",
        )
    attr_names = [key for key in attrs if isinstance(key, str)]
    client_dynamic = _input_type_is_browser_dynamic(attr_names, include_python_attrs=False)
    raw_type: str | None = None
    if type_keys:
        value = attrs[type_keys[0]]
        if value is True:
            raw_type = ""
        elif value is not None and value is not False:
            raw_type = str(value)
    return _Element(
        tag_name=tag_name,
        input_type=raw_type,
        type_static_known=not client_dynamic,
    )


def _as_str(value: Any) -> str | None:
    """A spread binding value as text, or ``None`` for an empty/absent value (one-way)."""
    if value is None or value is False:
        return None
    text = str(value)
    return text if text.strip() else None


def _validate_final_control_bindings(
    tag_name: str,
    attrs: dict[str, Any],
    specs: tuple[Mapping[str, object], ...],
    *,
    comp_name: str,
) -> None:
    """Recheck trusted typed State controls against the final post-hook element shape."""
    if not specs:
        return
    location = _Location(comp_name=comp_name, where=f"<{tag_name}> after all attribute hooks resolved")
    element = _resolved_element(tag_name, attrs, location)
    for spec in specs:
        field = spec["field"]
        attr_name = f":c-{field}"
        if spec["binding_mode"] == "one-way":
            _validate_binding_target(
                element,
                binding_mode="one-way",
                attr_name=attr_name,
                location=location,
            )
        else:
            _validate_two_way_control(
                element,
                lazy=cast("bool", spec["lazy"]),
                on_event=cast("str | None", spec["on"]),
                attr_name=attr_name,
                location=location,
            )
