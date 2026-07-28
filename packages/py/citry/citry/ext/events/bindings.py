r"""
The template binding rewrite for the ``events`` extension.

Templates opt into interactivity with two attribute prefixes: ``@c-*`` names a
DOM event and the handler it sends (``@c-click="save"``), and ``:c-*`` names a
State field a control is bound to (``:c-query.debounce.300ms="refresh"``). Both
are citry-owned and dissolve before the HTML reaches the browser: this module
rewrites each one into a ``data-cev-*`` attribute carrying a compact,
base64-encoded JSON spec that the client runtime (WP17) reads at event time.

The rewrite runs in two stages, because bindings can appear two ways:

- **Stage one, at template load** (:func:`rewrite_template`, string level,
  before the template is parsed and cached): everything an author writes
  literally in a template.
- **Stage two, at render time** (:func:`rewrite_resolved_attrs`, through the
  ``on_attrs_resolved`` hook): bindings contributed by a spread, e.g. a parent
  passing ``attrs="{'@c-click': 'select'}"`` that a child applies with the
  ``c-bind`` attribute spread. These are validated the moment they resolve,
  server-side, with the same wording as stage one.

Validation is a hard error (design ``events.md`` 5.1): every element-level
``@c-*`` value must name a declared handler; every element-level ``:c-*`` key
must name a public State field (and a writable ``_model`` field when two-way);
and modifier combinations must parse. On a component boundary, ``@c-*`` is
left intact for component-tag client binding capture while ``:c-*`` remains invalid.
``<c-element>`` follows the element path.

Known v1 caveats (each keeps the authored syntax and the emitted contract
unchanged, so lifting it later is transparent):

- The stage-one rewrite is textual, so it also matches binding-shaped text
  inside ``<c-raw>`` blocks (the same caveat class as the shipped
  ``$component`` substring rewrite). The refinement is a node-level
  transform in a later version.
- A binding that reaches a component tag through a render-time spread never
  enters this element rewrite. A1's source-ordered component-input split
  captures `@c-*` as a component-tag client binding and keeps `:c-*` as an ordinary
  invalid component input. Later Alpine batches own client-binding validation and
  delivery.
- The control-type validations (a two-way ``<input type="file">``, ``.lazy``
  on a control whose value already commits on ``change``, a key filter on a
  non-keyboard update event) run only when the control type is written
  literally on the element. A type contributed dynamically (``c-type``,
  ``:type``, or a ``c-bind`` spread) is not known at load, so these checks are
  skipped for that element, and a literal binding that stage one already
  rewrote is not re-validated at render time. This matches design 5.1's
  update-event table, which scopes both the ``<input type="file">`` row and
  the ``.lazy`` column to "where the type is statically known". A test pins
  this behavior so it is explicit.

The compiled ``data-cev-*`` contract (WP17 reads this, never the test
fixtures)
------------------------------------------------------------------------------

Each emitted attribute's value is base64-encoded UTF-8 JSON (standard base64,
matching the sibling dependencies manifest's armoring). The decoded value is
always a JSON array of spec objects, so one element can carry several bindings
of the same channel (design 5.1: "One element may carry several event bindings
for different DOM events"). JSON object keys are sorted, so the output is
deterministic. The three attributes and their per-spec keys:

``data-cev-on`` (DOM-event bindings, from ``@c-<event>``)
    - ``cid``: owner component class id (which class's handlers this addresses)
    - ``event``: the DOM event type, e.g. ``"click"``, ``"submit"``, ``"keyup"``
    - ``handler``: the handler wire name to send
    - ``args``: the raw Alpine arg expression the author wrote between the
      parentheses (``rate({stars: 5})`` -> ``"{stars: 5}"``), or ``null`` for a
      bare handler name. Carried verbatim; citry never parses it.
    - ``prevent`` / ``stop`` / ``self`` / ``once``: booleans, the event modifiers
    - ``key``: a keyboard key filter (``"enter"`` / ``"escape"``) or ``null``
    - ``debounce`` / ``throttle``: milliseconds, or ``null`` (the merged value:
      an ``.debounce`` modifier wins over the handler's configured default)

``data-cev-poll`` (interval bindings, from ``@c-poll.<N>s``)
    - ``cid``: owner component class id
    - ``handler``: the handler wire name to send on each tick
    - ``args``: the raw arg expression, or ``null``
    - ``interval``: the poll interval in milliseconds (``.30s`` -> ``30000``)

``data-cev-bind`` (state bindings, from ``:c-<field>``)
    - ``cid``: owner component class id
    - ``field``: the State field name (case preserved; the rewrite is
      server-side, so browser attribute-name lowercasing never sees it)
    - ``mode``: ``"one"`` for a one-way binding (no value), ``"two"`` for a
      two-way binding (the value names the handler)
    - ``handler``: the handler wire name for a two-way binding, or ``null``
    - ``lazy``: whether ``.lazy`` was set (use the control's committed-value
      event instead of its active event; the client resolves the concrete
      event from the live control)
    - ``on``: an explicit ``.on:<event>`` update-event override, or ``null``
    - ``key``: a keyboard key filter or ``null``
    - ``debounce`` / ``throttle``: milliseconds, or ``null``

The importable contract mirrors this prose: :data:`DATA_CEV_ATTRS` enumerates
the attribute names and their payload keys, and :data:`BINDING_SPEC_ENCODING`
names the encoding.

Design: ``docs/design/events.md`` section 5.1; ``docs/design/events_plan.md``
WP12.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.ext.events.extension import EventsInfo

# ----- The published data-cev-* contract -----

DATA_CEV_ON: Final = "data-cev-on"
DATA_CEV_POLL: Final = "data-cev-poll"
DATA_CEV_BIND: Final = "data-cev-bind"

BINDING_SPEC_ENCODING: Final = (
    "Each attribute value is standard base64 of UTF-8 JSON; the decoded value is a JSON array of"
    " spec objects with sorted keys."
)


@dataclass(frozen=True, slots=True)
class CevAttr:
    """
    One emitted ``data-cev-*`` attribute in the compiled binding contract.

    Attributes:
        name: The emitted attribute name (e.g. ``"data-cev-on"``).
        payload_keys: The keys every spec object in the attribute's JSON array
            carries, in a stable order for documentation (the wire uses sorted
            keys).
        summary: A one-line description of what the attribute drives.

    """

    name: str
    payload_keys: tuple[str, ...]
    summary: str


# The compiled contract, frozen so WP17 can read the emitted attribute names
# and payload shapes from here rather than from the test examples. Keep this in
# step with the spec builders below.
DATA_CEV_ATTRS: Final[Mapping[str, CevAttr]] = MappingProxyType(
    {
        DATA_CEV_ON: CevAttr(
            name=DATA_CEV_ON,
            payload_keys=(
                "cid",
                "event",
                "handler",
                "args",
                "prevent",
                "stop",
                "self",
                "once",
                "key",
                "debounce",
                "throttle",
            ),
            summary="DOM-event bindings from @c-<event>: send a handler on a DOM event.",
        ),
        DATA_CEV_POLL: CevAttr(
            name=DATA_CEV_POLL,
            payload_keys=("cid", "handler", "args", "interval"),
            summary="Interval bindings from @c-poll.<N>s: send a handler on a timer.",
        ),
        DATA_CEV_BIND: CevAttr(
            name=DATA_CEV_BIND,
            payload_keys=("cid", "field", "mode", "handler", "lazy", "on", "key", "debounce", "throttle"),
            summary="State bindings from :c-<field>: bind a control to a public State field.",
        ),
    }
)

# ----- Vocabulary constants (design 5.1) -----

# What a bare `.debounce` / `.throttle` (no time segment) means. Design 5.1
# pins both bare forms at 250 ms.
DEFAULT_DEBOUNCE_MS: Final = 250
DEFAULT_THROTTLE_MS: Final = 250

# Key filters (`.enter` / `.escape`) only make sense on a keyboard event.
KEYBOARD_EVENTS: Final = frozenset({"keydown", "keyup", "keypress"})

# `<input>` types whose committed value already updates on `change`, so `.lazy`
# (which asks for the committed-value event) is redundant and rejected.
_COMMITTED_INPUT_TYPES: Final = frozenset({"checkbox", "radio"})

# Event-binding boolean modifiers (design 5.1 modifier table).
_EVENT_FLAGS: Final = frozenset({"prevent", "stop", "self", "once"})
_KEY_FILTERS: Final = frozenset({"enter", "escape"})

_PREFIX_EVENT: Final = "@c-"
_PREFIX_STATE: Final = ":c-"

# The base marker (after the `c-` in `@c-poll`) that means "interval", not a
# DOM event.
_POLL: Final = "poll"


# ----- Textual scanning (stage one) -----

# An HTML start tag: the tag name, then an attribute region where quoted values
# protect any `>` inside them, up to the closing `>`. A trailing `/` (self
# closing) is part of the attribute region and handled during reconstruction.
_TAG_RE: Final = re.compile(
    r"""<
        (?P<tag>[A-Za-z][A-Za-z0-9._:-]*)
        (?P<attrs>(?:"[^"]*"|'[^']*'|[^"'>])*)
        >""",
    re.VERBOSE | re.DOTALL,
)

# One attribute inside a start tag: a name (any run of non-space, non-`=`,
# non-`/`, non-`>` characters, which captures `@c-submit.prevent` whole), then
# an optional `= value` where the value is quoted or an unquoted run.
_ATTR_RE: Final = re.compile(
    r"""(?P<name>[^\s=/>]+)
        (?:\s*=\s*(?P<value>"[^"]*"|'[^']*'|[^\s>]+))?""",
    re.VERBOSE,
)

# A modifier time segment: a whole number of milliseconds or seconds.
_TIME_RE: Final = re.compile(r"^(?P<n>\d+)(?P<unit>ms|s)$")


def _looks_like_binding(text: str) -> bool:
    """Whether ``text`` contains any authored binding prefix (a cheap pre-filter)."""
    return _PREFIX_EVENT in text or _PREFIX_STATE in text


_NON_BOUNDARY_CITRY_TAGS: Final = {
    "c-element",
    "c-if",
    "c-elif",
    "c-else",
    "c-for",
    "c-empty",
    "c-raw",
    "c-fill",
    "c-slot",
}


def _is_component_boundary_tag(tag_name: str) -> bool:
    """Whether ``tag_name`` is a semantic component boundary."""
    normalized = tag_name.lower()
    return normalized.startswith("c-") and normalized not in _NON_BOUNDARY_CITRY_TAGS


def _is_reserved_citry_tag(tag_name: str) -> bool:
    """Whether bindings have no meaningful element or component target."""
    normalized = tag_name.lower()
    return normalized.startswith("c-") and normalized != "c-element" and not _is_component_boundary_tag(tag_name)


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


def _parse_attrs(region: str) -> list[_Attr]:
    """Parse a start tag's attribute region into ordered :class:`_Attr` records."""
    parsed: list[_Attr] = []
    for match in _ATTR_RE.finditer(region):
        raw_value = match.group("value")
        value = raw_value[1:-1] if raw_value is not None and raw_value[:1] in "\"'" else raw_value
        parsed.append(_Attr(name=match.group("name"), value=value, source=match.group(0)))
    return parsed


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
    where: str  # e.g. "line 4" (stage one) or "<button> via a render-time spread" (stage two)

    def suffix(self) -> str:
        return f" (in {self.comp_name} template, {self.where})"


@dataclass(frozen=True, slots=True)
class _Element:
    """The element a binding sits on, for the control-type validations."""

    tag_name: str
    input_type: str | None  # the static `type` value, when statically known
    type_static_known: bool  # False when the type is dynamic (e.g. via c-type / c-bind)


def _fail(location: _Location, message: str) -> None:
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


def _build_event_spec(info: EventsInfo, class_id: str, event: str, attr: _Attr, location: _Location) -> dict[str, Any]:
    """Validate and build one ``data-cev-on`` spec from an ``@c-<event>`` attribute."""
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

    if key is not None and event not in KEYBOARD_EVENTS:
        _fail(location, f"{attr.name!r}: the key filter '.{key}' only applies to keyboard events, not {event!r}")

    debounce, throttle = _merged_timing(info, handler, debounce, throttle)
    return {
        "cid": class_id,
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


def _build_poll_spec(info: EventsInfo, class_id: str, attr: _Attr, location: _Location) -> dict[str, Any]:
    """Validate and build one ``data-cev-poll`` spec from an ``@c-poll.<N>s`` attribute."""
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
    return {"cid": class_id, "handler": handler, "args": args, "interval": interval}


def _build_bind_spec(
    info: EventsInfo, class_id: str, field: str, attr: _Attr, element: _Element, location: _Location
) -> dict[str, Any]:
    """Validate and build one ``data-cev-bind`` spec from a ``:c-<field>`` attribute."""
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
        # A one-way binding only reads state onto the control; it takes no
        # update-timing or key modifiers (there is no update to time).
        if lazy or on_event is not None or debounce is not None or throttle is not None or key is not None:
            _fail(
                location,
                f"{attr.name!r} is a one-way binding (no handler value), so it cannot carry an update-timing modifier"
                f" (.lazy, .debounce, .throttle, .on:) or a key filter; give it a handler value to make it two-way",
            )
        return {
            "cid": class_id,
            "field": field,
            "mode": "one",
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
    _validate_two_way_control(element, lazy=lazy, on_event=on_event, key=key, attr_name=attr.name, location=location)

    debounce, throttle = _merged_timing(info, handler or "", debounce, throttle)
    return {
        "cid": class_id,
        "field": field,
        "mode": "two",
        "handler": handler,
        "lazy": lazy,
        "on": on_event,
        "key": key,
        "debounce": debounce,
        "throttle": throttle,
    }


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


def _validate_two_way_control(
    element: _Element, *, lazy: bool, on_event: str | None, key: str | None, attr_name: str, location: _Location
) -> None:
    """Run the control-type validations for a two-way binding (design 5.1's update-event table)."""
    tag = element.tag_name.lower()
    known_control = tag in ("input", "textarea", "select")
    if not known_control:
        # A custom element has no default update event, so it must name one.
        if on_event is None:
            _fail(
                location,
                f"{attr_name!r}: <{element.tag_name}> is not a known form control, so a two-way binding needs an"
                f" explicit update event via '.on:<event>'",
            )
        effective_event: str | None = on_event
    elif on_event is not None:
        effective_event = on_event
    else:
        effective_event = _control_event(element, tag, lazy=lazy, attr_name=attr_name, location=location)

    # A key filter only makes sense once the update event is known to be a
    # keyboard event; when the control type is dynamic the event is unknown, so
    # the check is left to the runtime rather than guessed at load time.
    if key is not None and effective_event is not None and effective_event not in KEYBOARD_EVENTS:
        _fail(
            location,
            f"{attr_name!r}: the key filter '.{key}' only applies to keyboard events, but this binding updates on"
            f" {effective_event!r}; set the event with '.on:keyup'/'.on:keydown'",
        )


def _control_event(element: _Element, tag: str, *, lazy: bool, attr_name: str, location: _Location) -> str | None:
    """
    The update event for a statically-known form control, or ``None`` when the type is not statically known.

    Raises for the control-type load errors: a two-way ``<input type=file>``,
    and ``.lazy`` on a control whose committed value already updates on
    ``change`` (checkbox, radio, select).
    """
    if tag == "select":
        if lazy:
            _fail(location, f"{attr_name!r}: '.lazy' has no effect on <select>; its value already commits on 'change'")
        return "change"
    if tag == "textarea":
        return "change" if lazy else "input"
    # tag == "input"
    if not element.type_static_known:
        return None
    input_type = (element.input_type or "text").strip().lower()
    if input_type == "file":
        _fail(
            location,
            f'{attr_name!r}: <input type="file"> cannot be two-way bound (files cannot live in State);'
            f" collect the file through event args instead",
        )
    if input_type in _COMMITTED_INPUT_TYPES:
        if lazy:
            _fail(
                location,
                f"{attr_name!r}: '.lazy' has no effect on <input type=\"{input_type}\">;"
                f" its value already commits on 'change'",
            )
        return "change"
    return "change" if lazy else "input"


# ----- Encoding and merging -----


def _encode(specs: list[dict[str, Any]]) -> str:
    """Encode a channel's spec list as base64 UTF-8 JSON (sorted keys, deterministic)."""
    payload = json.dumps(specs, separators=(",", ":"), sort_keys=True)
    return base64.b64encode(payload.encode()).decode("ascii")


def _channels() -> dict[str, list[dict[str, Any]]]:
    return {DATA_CEV_ON: [], DATA_CEV_POLL: [], DATA_CEV_BIND: []}


def _classify_binding(attr_name: str) -> str | None:
    """Which channel an attribute name feeds, or ``None`` when it is not a binding."""
    if attr_name.startswith(_PREFIX_EVENT):
        base, _ = _split_name(attr_name, _PREFIX_EVENT)
        return DATA_CEV_POLL if base == _POLL else DATA_CEV_ON
    if attr_name.startswith(_PREFIX_STATE):
        return DATA_CEV_BIND
    return None


def _build_spec(
    channel: str, info: EventsInfo, class_id: str, attr: _Attr, element: _Element, location: _Location
) -> dict[str, Any]:
    if channel == DATA_CEV_ON:
        event, _ = _split_name(attr.name, _PREFIX_EVENT)
        return _build_event_spec(info, class_id, event, attr, location)
    if channel == DATA_CEV_POLL:
        return _build_poll_spec(info, class_id, attr, location)
    field, _ = _split_name(attr.name, _PREFIX_STATE)
    return _build_bind_spec(info, class_id, field, attr, element, location)


@dataclass(frozen=True, slots=True)
class CompiledCitryBoundaryBinding:
    """One validated component-boundary ``@c-*`` server binding."""

    channel: str
    spec: Mapping[str, Any]


def compile_citry_boundary_binding(
    info: EventsInfo,
    class_id: str,
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
    opaque-call-shell parser as element bindings. The only difference is that
    the compiled spec is retained in the ownership graph instead of becoming a
    ``data-cev-*`` attribute immediately.
    """
    channel = _classify_binding(attr_name)
    if channel not in (DATA_CEV_ON, DATA_CEV_POLL):
        msg = f"Expected a Citry event binding on <{tag_name}>, got {attr_name!r}."
        raise ValueError(msg)
    location = _Location(
        comp_name=comp_name,
        where=f"line {line}, column {column}, on <{tag_name}> component boundary",
    )
    spec = _build_spec(
        channel,
        info,
        class_id,
        _Attr(name=attr_name, value=value, source=attr_name),
        _Element(tag_name=tag_name, input_type=None, type_static_known=False),
        location,
    )
    return CompiledCitryBoundaryBinding(channel=channel, spec=MappingProxyType(spec))


# ----- Stage one: template-load rewrite -----


@dataclass(frozen=True, slots=True)
class TemplateRewrite:
    """
    The result of the stage-one template rewrite.

    Attributes:
        content: The template string with every ``@c-*`` / ``:c-*`` attribute
            replaced by its ``data-cev-*`` form.
        two_way_fields: The State fields bound two-way anywhere in the template.
            Each binding has already been checked against ``_model``; this
            aggregate remains available for diagnostics and introspection.

    """

    content: str
    two_way_fields: frozenset[str]


def rewrite_template(info: EventsInfo, class_id: str, comp_name: str, content: str) -> TemplateRewrite:
    """
    Stage one: rewrite the authored bindings in a template string at load time.

    Scans start tags for ``@c-*`` / ``:c-*`` attributes, validates each against
    the owning component's handlers and State (design 5.1), and replaces them
    with the ``data-cev-*`` attributes the client runtime reads. Non-binding
    attributes and the rest of the template are left untouched; only tags that
    actually carry a binding are reconstructed.

    Args:
        info: The owning component's resolved events info (handlers, State).
        class_id: The owning component's class id (the spec's ``cid``).
        comp_name: The owning component's name, for error messages.
        content: The template string, before parsing.

    Returns:
        A [`TemplateRewrite`][citry.ext.events.bindings.TemplateRewrite] with
        the rewritten content and the two-way field diagnostics.

    Raises:
        ValueError: On any invalid binding (undeclared handler, non-public
            field, illegal modifier combination, a binding on a component tag),
            with the template location.

    """
    if not _looks_like_binding(content):
        return TemplateRewrite(content=content, two_way_fields=frozenset())

    two_way_fields: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        tag_name = match.group("tag")
        region = match.group("attrs")
        attrs = _parse_attrs(region)
        bindings = [attr for attr in attrs if _classify_binding(attr.name) is not None]
        if not bindings:
            return match.group(0)

        line = content.count("\n", 0, match.start()) + 1
        location = _Location(comp_name=comp_name, where=f"line {line}")
        if _is_component_boundary_tag(tag_name):
            state_binding = next(
                (attr for attr in bindings if _classify_binding(attr.name) == DATA_CEV_BIND),
                None,
            )
            if state_binding is None:
                # @c-* on a component is a component-tag client binding. Leave the authored
                # source and exact span intact for ComponentNode to capture.
                return match.group(0)
            _fail(
                location,
                f"<{tag_name}> is a component tag, but {state_binding.name!r} binds State on it."
                f" State bindings go on HTML elements only: a child component binds its own State in its own"
                f" template; pass data down through $c-props or Python kwargs.",
            )
        if _is_reserved_citry_tag(tag_name):
            _fail(
                location,
                f"<{tag_name}> is a Citry structural tag, so {bindings[0].name!r} has no HTML element target.",
            )

        element = _element_of(tag_name, attrs)
        channels = _channels()
        for attr in bindings:
            channel = _classify_binding(attr.name)
            assert channel is not None  # bindings were filtered on this  # noqa: S101
            spec = _build_spec(channel, info, class_id, attr, element, location)
            channels[channel].append(spec)
            if channel == DATA_CEV_BIND and spec["mode"] == "two":
                two_way_fields.add(spec["field"])
        return _reconstruct_tag(tag_name, region, attrs, channels)

    rewritten = _TAG_RE.sub(replace, content)
    return TemplateRewrite(content=rewritten, two_way_fields=frozenset(two_way_fields))


def _element_of(tag_name: str, attrs: list[_Attr]) -> _Element:
    """Read the control type off a parsed tag: a static ``type``, or a dynamic marker."""
    static_type: str | None = None
    dynamic = False
    for attr in attrs:
        if attr.name == "type":
            static_type = attr.value
        elif attr.name in ("c-type", ":type", "c-bind"):
            # The type is contributed dynamically (a c-* expression, an Alpine
            # bind, or a spread), so it is not statically known at load. The
            # control-type checks (file two-way, `.lazy` on a committed control,
            # a key filter on a non-keyboard update event) run only for a
            # statically-known type; design 5.1's update-event table scopes both
            # the file-input row and the `.lazy` column to "where the type is
            # statically known". They are not re-run for this element's literal
            # binding, which stage one has already rewritten by render time. A
            # documented v1 caveat covers the gap; see the module docstring.
            dynamic = True
    return _Element(tag_name=tag_name, input_type=static_type, type_static_known=not dynamic)


def _reconstruct_tag(tag_name: str, region: str, attrs: list[_Attr], channels: dict[str, list[dict[str, Any]]]) -> str:
    """
    Rebuild a start tag with its bindings replaced by the ``data-cev-*`` attributes.

    Non-binding attributes are re-emitted verbatim in source order; the emitted
    ``data-cev-*`` attributes follow them, in a fixed channel order. A trailing
    ``/`` (self-closing tag) is preserved.
    """
    self_closing = region.rstrip().endswith("/")
    kept = [attr.source for attr in attrs if _classify_binding(attr.name) is None]
    emitted = [f'{name}="{_encode(specs)}"' for name, specs in channels.items() if specs]
    pieces = kept + emitted
    body = " ".join(pieces)
    slash = "/" if self_closing else ""
    if body:
        return f"<{tag_name} {body}{slash}>"
    return f"<{tag_name}{slash}>"


# ----- Stage two: render-time (spread) rewrite -----


def rewrite_resolved_attrs(
    info: EventsInfo, class_id: str, comp_name: str, tag_name: str, attrs: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Stage two: rewrite bindings that arrive on an element at render time.

    Fires through the ``on_attrs_resolved`` hook for every element with dynamic
    attributes, so it fast-returns when no ``@c-*`` / ``:c-*`` key is present.
    When one is, it validates and rewrites it exactly like stage one, but the
    error is raised now (render time) rather than at template load, with the
    same wording.

    Args:
        info: The owning component's resolved events info.
        class_id: The owning component's class id (the spec's ``cid``).
        comp_name: The owning component's name, for error messages.
        tag_name: The element's tag name.
        attrs: The element's resolved attribute dict.

    Returns:
        A new attribute dict with the bindings rewritten, or ``None`` when the
        element carried no binding (leave the dict untouched).

    Raises:
        ValueError: On any invalid binding, with the render-time location.

    """
    binding_keys = [key for key in attrs if _classify_binding(key) is not None]
    if not binding_keys:
        return None

    # This hook fires only for HTML elements; a `<c-*>` component tag never
    # reaches it (its two callers, the HTML-element attrs node in
    # nodes/__init__.py and the <c-element> attribute formatter in
    # components/dynamic.py, both emit plain HTML elements). So there is no
    # component-tag check here: the literal form is caught at load by stage
    # one, and a binding that a spread lands on a component tag is a documented
    # v1 caveat (see the module docstring), silently ignored until a
    # component-input check lands.
    location = _Location(comp_name=comp_name, where=f"<{tag_name}> via a render-time attribute spread")
    resolved_type = attrs.get("type")
    element = _Element(
        tag_name=tag_name,
        input_type=str(resolved_type) if isinstance(resolved_type, str) else None,
        type_static_known=True,
    )

    result = {key: value for key, value in attrs.items() if key not in binding_keys}
    channels = _channels()
    for key in binding_keys:
        channel = _classify_binding(key)
        assert channel is not None  # filtered above  # noqa: S101
        raw = attrs[key]
        # A spread value is the attribute's value; a bare boolean True means the
        # key was contributed with no value (a one-way :c-* binding).
        value = None if raw is True else _as_str(raw)
        spec = _build_spec(channel, info, class_id, _Attr(name=key, value=value, source=key), element, location)
        channels[channel].append(spec)

    for name, specs in channels.items():
        if specs:
            _merge_encoded(result, name, specs)
    return result


def _as_str(value: Any) -> str | None:
    """A spread binding value as text, or ``None`` for an empty/absent value (one-way)."""
    if value is None or value is False:
        return None
    text = str(value)
    return text if text.strip() else None


def _merge_encoded(attrs: dict[str, Any], name: str, specs: list[dict[str, Any]]) -> None:
    """
    Set (or extend) a ``data-cev-*`` attribute with new specs.

    When stage one already emitted this attribute on the same element (a literal
    binding alongside a spread), the existing specs are decoded and the new ones
    appended, so both survive in one attribute.
    """
    existing = attrs.get(name)
    if isinstance(existing, str) and existing:
        try:
            prior = json.loads(base64.b64decode(existing).decode())
        except (ValueError, json.JSONDecodeError):
            prior = []
        if isinstance(prior, list):
            specs = [*prior, *specs]
    attrs[name] = _encode(specs)
