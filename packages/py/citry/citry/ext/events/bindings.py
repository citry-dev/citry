r"""
The template binding rewrite for the ``events`` extension.

Templates opt into interactivity with two attribute prefixes: ``@c-*`` names a
DOM event and the handler it sends (``@c-click="save"``), and ``:c-*`` names a
State field a control is bound to (``:c-query.debounce.300ms="refresh"``). Both
are citry-owned and dissolve before the HTML reaches the browser: this module
rewrites each one into a ``data-cev-*`` attribute carrying a compact,
base64-encoded JSON spec that the client runtime (WP17) reads at event time.

The rewrite runs in two stages, because bindings can appear two ways:

- **Stage one, after template compilation** (:func:`compile_template_bindings`,
  structured-node level): attributes the parser proved were authored on real
  elements. The source template remains unchanged for diagnostics and
  introspection.
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

Additional boundary rules:

- A binding that reaches a component tag through a render-time spread never
  enters the element rewrite. A1's source-ordered component-input split
  captures `@c-*` as a component-tag client binding and keeps `:c-*` as an ordinary
  invalid component input. Later Alpine batches own client-binding validation and
  delivery.
- Control-type validation runs at template load when possible, against final
  server-rendered attributes after ``c-type`` / ``c-bind`` resolution, and in
  the browser for Alpine-mutated ``:type`` values. The final two use the same
  complete input-type matrix and fail closed while the live type is invalid.
- ``<c-element>`` is classified by the element its ``is`` attribute names. A
  literal ``is`` permits early target validation; for computed ``is``
  (``c-is``, or ``is`` through a spread), target-dependent checks are deferred
  until the selected tag and its final attributes resolve at render time.
- Binding-shaped text inside ``<c-raw>``, HTML comments, and native
  ``script``/``style``/``textarea``/``title`` bodies is text, not an
  attribute, and is therefore never validated or rewritten.

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
    - ``key``: an ``event.key`` filter (``"enter"`` / ``"escape"``) or ``null``
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
    - ``binding_mode``: ``"one-way"`` for a State-to-control binding (no
      value), ``"two-way"`` for a binding whose value names the handler and
      which also writes control changes back to State
    - ``handler``: the handler wire name for a two-way binding, or ``null``
    - ``lazy``: whether ``.lazy`` was set (use the control's committed-value
      event instead of its active event; the client resolves the concrete
      event from the live control)
    - ``on``: an explicit ``.on:<event>`` update-event override, or ``null``
    - ``key``: an ``event.key`` filter or ``null``
    - ``debounce`` / ``throttle``: milliseconds, or ``null``

The importable contract mirrors this prose: :data:`DATA_CEV_ATTRS` enumerates
the attribute names and their payload keys, and :data:`BINDING_SPEC_ENCODING`
names the encoding. These attributes are compiler-owned: authoring a
``data-cev-*`` attribute directly is a template-load error.

Design: ``docs/design/events.md`` section 5.1; ``docs/design/events_plan.md``
WP12.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, NoReturn

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
            payload_keys=(
                "cid",
                "field",
                "binding_mode",
                "handler",
                "lazy",
                "on",
                "key",
                "debounce",
                "throttle",
            ),
            summary="State bindings from :c-<field>: bind a control to a public State field.",
        ),
    }
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
_TWO_WAY_INPUT_TYPES: Final = frozenset(
    {
        "text",
        "search",
        "tel",
        "url",
        "email",
        "password",
        "date",
        "month",
        "week",
        "time",
        "datetime-local",
        "number",
        "range",
        "color",
        "checkbox",
        "radio",
    }
)
_ONE_WAY_INPUT_TYPES: Final = frozenset({"hidden"})
_UNSUPPORTED_INPUT_TYPES: Final = frozenset({"file", "submit", "image", "reset", "button"})
_HTML_INPUT_TYPES: Final = _TWO_WAY_INPUT_TYPES | _ONE_WAY_INPUT_TYPES | _UNSUPPORTED_INPUT_TYPES

# The HTML elements the client can read a value from and write a value back to
# (`readControlValue` / `applyValueToControl` in the client runtime). A
# `<select multiple>` is included and carries a list of selected option values;
# the live element's `multiple` property decides that shape, so direct and
# dynamic/spread forms share the same path. A state binding on any other plain
# element has nothing to bind, so it is rejected.
# Widening this set is the single place a future "bind anything" feature hooks
# in; the client must learn the element's value shape in the same change.
_KNOWN_FORM_CONTROLS: Final = frozenset({"input", "textarea", "select"})

# Hyphenated names HTML reserves for SVG and MathML elements, so they are not
# custom element names however much they look like one. None of them holds a
# value, so a state binding on one is rejected with everything else.
_RESERVED_HYPHENATED_TAGS: Final = frozenset(
    {
        "annotation-xml",
        "color-profile",
        "font-face",
        "font-face-format",
        "font-face-name",
        "font-face-src",
        "font-face-uri",
        "missing-glyph",
    }
)

# Event-binding boolean modifiers (design 5.1 modifier table).
_EVENT_FLAGS: Final = frozenset({"prevent", "stop", "self", "once"})
_KEY_FILTERS: Final = frozenset({"enter", "escape"})

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


def _is_custom_element(tag_name: str) -> bool:
    """
    Whether a tag names a custom element, by HTML's own rule for the name.

    A custom element may expose a value the way a form control does, so a state
    binding is allowed on one. After the browser upgrades the element, the
    client reads and writes that typed property without native-control
    coercion, and the element names its own update event with ``.on:<event>``.

    Pass a lowercased name: HTML tag names are case insensitive, so ``<My-Box>``
    in markup is the custom element ``my-box``.

    A hyphen alone is not enough. HTML reserves a handful of hyphenated names
    for SVG and MathML elements that hold no value, a name must start with an
    ASCII letter, and Citry's own ``c-`` tags are components rather than
    elements (reachable here through ``<c-element is="c-foo">``).
    """
    if not tag_name or tag_name in _RESERVED_HYPHENATED_TAGS or tag_name.startswith("c-"):
        return False
    if not tag_name[0].isascii() or not tag_name[0].isalpha():
        return False
    return "-" in tag_name


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


@dataclass(frozen=True, slots=True)
class _Element:
    """The element a binding sits on, for the control-type validations."""

    tag_name: str
    input_type: str | None  # the static `type` value, when statically known
    type_static_known: bool  # False when the type is dynamic (e.g. via c-type / c-bind)
    tag_static_known: bool = True  # False for <c-element> whose `is` is dynamic


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
            "cid": class_id,
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

    debounce, throttle = _merged_timing(info, handler or "", debounce, throttle)
    return {
        "cid": class_id,
        "field": field,
        "binding_mode": "two-way",
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


def _validate_binding_target(element: _Element, *, binding_mode: str, attr_name: str, location: _Location) -> str:
    """
    Classify the element a ``:c-*`` binding sits on, or reject it.

    Returns ``"control"`` for a form control the client reads and writes
    directly, ``"custom"`` for a custom element (which must name its own
    update event), and ``"deferred"`` for a computed ``<c-element>`` target.

    Every other plain HTML element is rejected: the client has no value to read
    from it or write to it, so the binding would silently do nothing on the way
    down and write an undefined value on the way up.

    A ``<c-element>`` whose element name is computed cannot be classified while
    its template is loaded. Its compiled spec is re-checked by the final-attrs
    hook against the selected tag before any HTML reaches the browser, so only
    target-dependent checks defer; State and handler ownership still validate
    immediately.
    """
    if not element.tag_static_known:
        return "deferred"
    tag = element.tag_name.lower()
    if tag in _KNOWN_FORM_CONTROLS:
        if tag == "input":
            _validate_input_binding_mode(
                element,
                binding_mode=binding_mode,
                attr_name=attr_name,
                location=location,
            )
        return "control"
    if _is_custom_element(tag):
        return "custom"
    controls = ", ".join(f"<{name}>" for name in sorted(_KNOWN_FORM_CONTROLS))
    _fail(
        location,
        f"{attr_name!r}: <{element.tag_name}> holds no value, so a State binding has nothing to bind."
        f" State bindings go on {controls}, or on a custom element that exposes a value."
        f" To react to events on <{element.tag_name}>, use an '@c-*' event binding instead",
    )
    return "control"  # pragma: no cover - _fail always raises


def _input_type(element: _Element) -> str | None:
    """Return a known static input keyword, ``""`` for unknown, or ``None`` while dynamic."""
    if not element.type_static_known:
        return None
    raw = element.input_type
    if raw is None or raw == "":
        return "text"
    normalized = raw.lower()
    return normalized if normalized in _HTML_INPUT_TYPES else ""


def _validate_input_binding_mode(element: _Element, *, binding_mode: str, attr_name: str, location: _Location) -> None:
    """
    Enforce the complete HTML input-type/binding-direction matrix.

    A dynamic type is deferred to the final-attrs hook or browser classifier.
    Missing and empty types are Text; a present unknown keyword is rejected
    distinctly from a standard type that Citry deliberately does not bind.
    """
    input_type = _input_type(element)
    if input_type is None:
        return
    if input_type in _TWO_WAY_INPUT_TYPES:
        return
    if input_type == "hidden":
        if binding_mode == "one-way":
            return
        _fail(
            location,
            f'{attr_name!r}: <input type="hidden"> supports one-way State bindings only;'
            " it has no user update event. Remove the handler value to make this binding one-way",
        )
    if input_type == "file":
        _fail(
            location,
            f'{attr_name!r}: <input type="file"> cannot be bound to State (files cannot live in State);'
            " use an ordinary upload endpoint or a custom transport instead;"
            " Citry's JSON events transport does not carry files",
        )
    if input_type in _UNSUPPORTED_INPUT_TYPES:
        _fail(
            location,
            f'{attr_name!r}: <input type="{input_type}"> cannot be bound to State; {input_type} inputs are'
            " action controls, not editable value controls. Use an '@c-*' event binding instead",
        )
    raw = element.input_type or ""
    _fail(
        location,
        f'{attr_name!r}: <input type="{raw}"> is not a recognized input type in this Citry version,'
        " so its value and update behavior are unknown. Use a supported standard type",
    )


def _validate_two_way_control(
    element: _Element, *, lazy: bool, on_event: str | None, attr_name: str, location: _Location
) -> None:
    """Run the control-type validations for a two-way binding (design 5.1's update-event table)."""
    tag = element.tag_name.lower()
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
                f"{attr_name!r}: <{element.tag_name}> is a custom element, so it has no default update event."
                f" Name the event the element fires when its value changes, via '.on:<event>'",
            )
    elif on_event is None:
        _control_event(element, tag, lazy=lazy, attr_name=attr_name, location=location)


def _control_event(element: _Element, tag: str, *, lazy: bool, attr_name: str, location: _Location) -> str | None:
    """
    The update event for a statically-known form control, or ``None`` when the type is not statically known.

    Raises for ``.lazy`` on a control whose committed value already updates on
    ``change`` (checkbox, radio, select). The complete direction check runs
    earlier in :func:`_validate_input_binding_mode`.
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
    input_type = _input_type(element)
    assert input_type in _TWO_WAY_INPUT_TYPES  # validated by _validate_binding_target  # noqa: S101
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


# ----- Stage one: compiled-node rewrite -----


@dataclass(frozen=True, slots=True)
class CompiledTemplateBindings:
    """
    The result of transforming one compiled template body.

    Attributes:
        nodes: The compiled body with real element bindings replaced by their
            ``data-cev-*`` form. Literal text is untouched.
        two_way_fields: The State fields bound two-way anywhere in the template.
            Each binding has already been checked against ``_model``; this
            aggregate remains available for diagnostics and introspection.

    """

    nodes: list[Any]
    two_way_fields: frozenset[str]


def compile_template_bindings(
    info: EventsInfo,
    class_id: str,
    comp_name: str,
    nodes: list[Any],
) -> CompiledTemplateBindings:
    """
    Validate and transform parser-proven bindings in a compiled template body.

    Ordinary static HTML usually compiles straight to strings. The template
    compiler deliberately preserves regions containing ``@c-*``, ``:c-*``, or
    ``data-cev-*`` as :class:`ElementAttrsNode` objects, so this pass can
    distinguish real attributes from binding-shaped text. Otherwise-static
    regions collapse back to a string after transformation.

    Args:
        info: The owning component's resolved events info (handlers, State).
        class_id: The owning component's class id (the spec's ``cid``).
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
        class_id=class_id,
        comp_name=comp_name,
        two_way_fields=two_way_fields,
    )
    return CompiledTemplateBindings(nodes=transformed, two_way_fields=frozenset(two_way_fields))


def _transform_compiled_body(
    body: list[Any],
    *,
    info: EventsInfo,
    class_id: str,
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
            tag_name = item.tag_name
            if transformed and isinstance(transformed[-1], str):
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
                    class_id=class_id,
                    comp_name=comp_name,
                    two_way_fields=two_way_fields,
                )
            )
            continue

        if isinstance(item, ComponentNode):
            if item.name == "element":
                item.attrs = _transform_element_attrs(
                    tag_name="c-element",
                    source=item.source,
                    position=item.position,
                    attrs=item.attrs,
                    info=info,
                    class_id=class_id,
                    comp_name=comp_name,
                    two_way_fields=two_way_fields,
                )[0]
            else:
                _validate_component_boundary_attrs(
                    item,
                    info=info,
                    class_id=class_id,
                    comp_name=comp_name,
                )
            item.body = _transform_compiled_body(
                item.body,
                info=info,
                class_id=class_id,
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
                class_id=class_id,
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
                            class_id=class_id,
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
    class_id: str,
    comp_name: str,
    two_way_fields: set[str],
) -> Any:
    """Transform one ordinary HTML element's structured attribute region."""
    attrs, emitted = _transform_element_attrs(
        tag_name=tag_name,
        source=node.source,
        position=node.position,
        attrs=node.attrs,
        info=info,
        class_id=class_id,
        comp_name=comp_name,
        two_way_fields=two_way_fields,
    )
    if not emitted:
        return node

    from citry.nodes import ElementAttrsNode, StaticHtmlAttr  # noqa: PLC0415

    had_runtime_attr = any(not isinstance(attr, StaticHtmlAttr) for attr in node.attrs)
    has_later_client_directive = any(isinstance(attr, StaticHtmlAttr) and attr.key.startswith("$c-") for attr in attrs)
    if had_runtime_attr or has_later_client_directive:
        return ElementAttrsNode(node.source, node.position, attrs, node.used_vars)

    # This region was preserved only so the extension could see its literal
    # binding. Collapse it back to the static fast path, preserving the exact
    # authored spelling of every non-binding attribute.
    pieces = [
        _source_slice(attr.source, attr.position)
        for attr in node.attrs
        if isinstance(attr, StaticHtmlAttr) and _classify_binding(attr.key) is None
    ]
    pieces.extend(f'{name}="{value}"' for name, value in emitted)
    return (" " + " ".join(pieces)) if pieces else ""


def _transform_element_attrs(
    *,
    tag_name: str,
    source: Any,
    position: tuple[int, int],
    attrs: tuple[Any, ...],
    info: EventsInfo,
    class_id: str,
    comp_name: str,
    two_way_fields: set[str],
) -> tuple[tuple[Any, ...], list[tuple[str, str]]]:
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
        return attrs, []

    element_attrs = [_compiled_attr(attr) for attr in attrs]
    element = _element_of(tag_name, element_attrs)
    channels = _channels()
    for attr in bindings:
        channel = _classify_binding(attr.key)
        assert channel is not None  # filtered above  # noqa: S101
        spec = _build_spec(
            channel,
            info,
            class_id,
            _compiled_attr(attr),
            element,
            _compiled_location(comp_name, source, attr.position),
        )
        channels[channel].append(spec)
        if channel == DATA_CEV_BIND and spec["binding_mode"] == "two-way":
            two_way_fields.add(spec["field"])

    kept = tuple(attr for attr in attrs if attr not in bindings)
    emitted = [(name, _encode(specs)) for name, specs in channels.items() if specs]
    compiled = tuple(StaticHtmlAttr(source, position, name, value, ()) for name, value in emitted)
    return kept + compiled, emitted


def _validate_component_boundary_attrs(
    node: Any,
    *,
    info: EventsInfo,
    class_id: str,
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
        if channel == DATA_CEV_BIND:
            _fail(
                location,
                f"<{tag_name}> is a component tag, but {attr.key!r} binds State on it."
                " State bindings go on HTML elements only: a child component binds its own State in its own"
                " template; pass data down through $c-props or Python kwargs.",
            )
        line, column = _line_column(node.source, attr.position[0])
        compile_citry_boundary_binding(
            info,
            class_id,
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
    """
    Read the control type off a parsed tag: a static ``type``, or a dynamic marker.

    HTML attribute names are case insensitive, so every name read here is
    lowercased first. Matching them exactly would let ``TYPE="file"`` walk past
    the checks that ``type="file"`` fails.
    """
    static_type: str | None = None
    dynamic = False
    effective_tag = tag_name
    tag_known = True
    names = [attr.name.lower() for attr in attrs]
    if _citry_tag_identity(tag_name) == "c-element":
        # `<c-element>` renders the element its `is` attribute names, so that
        # name is what the binding actually lands on. Only a literal `is` says
        # which element that is; target-dependent checks for a computed name
        # defer to the final-attrs hook, which sees the selected HTML tag.
        static_is = next((attr.value for name, attr in zip(names, attrs, strict=True) if name == "is"), None)
        computed = any(name in ("c-is", "c-bind") for name in names)
        if static_is and not computed:
            effective_tag = static_is
        else:
            tag_known = False
    for name, attr in zip(names, attrs, strict=True):
        if name == "type":
            static_type = attr.value
        elif name in ("c-type", ":type", "c-bind"):
            # Defer a Python-resolved c-type/spread to the final-attrs hook and
            # an Alpine bind to the live browser classifier. A literal binding
            # is already compiled by then, so both later phases explicitly
            # decode and revalidate its internal spec.
            dynamic = True
    return _Element(
        tag_name=effective_tag,
        input_type=static_type,
        type_static_known=not dynamic,
        tag_static_known=tag_known,
    )


# ----- Stage two: render-time (spread) rewrite -----


def rewrite_resolved_attrs(
    info: EventsInfo, class_id: str, comp_name: str, tag_name: str, attrs: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Stage two: rewrite bindings that arrive on an element at render time.

    Fires through the ``on_attrs_resolved`` hook for every element with dynamic
    attributes. Raw ``@c-*`` / ``:c-*`` keys are compiled exactly like stage
    one. An existing ``data-cev-bind`` is also decoded and validated against
    the final resolved input type, closing the literal-binding + dynamic-type
    gap before HTML reaches the browser.

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
    binding_keys = [key for key in attrs if isinstance(key, str) and _classify_binding(key) is not None]
    if not binding_keys and DATA_CEV_BIND not in attrs:
        return None

    # This hook fires only for HTML elements; a `<c-*>` component tag never
    # reaches it (its two callers, the HTML-element attrs node in
    # nodes/__init__.py and the <c-element> attribute formatter in
    # components/dynamic.py, both emit plain HTML elements). So there is no
    # component-tag check here: the literal form is caught at load by stage
    # one, and a binding that a spread lands on a component tag is a documented
    # v1 caveat (see the module docstring), silently ignored until a
    # component-input check lands.
    location = _Location(comp_name=comp_name, where=f"<{tag_name}> after dynamic attributes resolved")
    element = _resolved_element(tag_name, attrs, location)

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
            _merge_encoded(result, name, specs, location)
    encoded_bind = result.get(DATA_CEV_BIND)
    if encoded_bind is not None:
        bind_specs = _decode_compiled_specs(DATA_CEV_BIND, encoded_bind, location)
        _validate_compiled_bind_specs(bind_specs, element, location)
        result[DATA_CEV_BIND] = _encode(bind_specs)
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
    client_dynamic = any(isinstance(key, str) and key.lower() in {":type", "x-bind:type"} for key in attrs)
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


def _decode_compiled_specs(name: str, encoded: Any, location: _Location) -> list[dict[str, Any]]:
    """Strictly decode one existing internal binding attribute at render time."""
    if not isinstance(encoded, str) or not encoded:
        _fail(location, f"{name!r} must contain nonempty base64-encoded binding specs")
    try:
        payload = base64.b64decode(encoded, validate=True).decode("utf8")
        decoded = json.loads(payload)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        _fail(location, f"{name!r} does not contain valid base64-encoded UTF-8 JSON: {exc}")
    if type(decoded) is not list:
        _fail(location, f"{name!r} must decode to a JSON array of binding spec objects")
    specs: list[dict[str, Any]] = []
    for index, spec in enumerate(decoded):
        if type(spec) is not dict:
            _fail(location, f"{name!r} spec {index} must be a JSON object")
        specs.append(spec)
    return specs


def _validate_compiled_bind_specs(specs: list[dict[str, Any]], element: _Element, location: _Location) -> None:
    """Validate compiled bind shape plus the final element/type support matrix."""
    expected_keys = frozenset(DATA_CEV_ATTRS[DATA_CEV_BIND].payload_keys)
    for index, spec in enumerate(specs):
        if frozenset(spec) != expected_keys:
            _fail(
                location,
                f"{DATA_CEV_BIND!r} spec {index} must contain exactly: {', '.join(sorted(expected_keys))}",
            )
        cid = spec["cid"]
        field = spec["field"]
        binding_mode = spec["binding_mode"]
        handler = spec["handler"]
        lazy = spec["lazy"]
        on_event = spec["on"]
        key = spec["key"]
        debounce = spec["debounce"]
        throttle = spec["throttle"]
        if not isinstance(cid, str) or not cid or not isinstance(field, str) or not field:
            _fail(location, f"{DATA_CEV_BIND!r} spec {index} needs nonempty string 'cid' and 'field' values")
        if not isinstance(binding_mode, str) or binding_mode not in {"one-way", "two-way"}:
            _fail(
                location,
                f"{DATA_CEV_BIND!r} spec {index} has invalid 'binding_mode'; expected 'one-way' or 'two-way'",
            )
        if type(lazy) is not bool:
            _fail(location, f"{DATA_CEV_BIND!r} spec {index} has non-boolean 'lazy'")
        if on_event is not None and (not isinstance(on_event, str) or not on_event):
            _fail(location, f"{DATA_CEV_BIND!r} spec {index} has invalid 'on'; expected a nonempty string or null")
        if key is not None and (not isinstance(key, str) or key not in _KEY_FILTERS):
            _fail(location, f"{DATA_CEV_BIND!r} spec {index} has invalid event-key filter 'key'")
        for timing_name, timing in (("debounce", debounce), ("throttle", throttle)):
            if timing is not None and (type(timing) is not int or timing < 0):
                _fail(
                    location,
                    f"{DATA_CEV_BIND!r} spec {index} has invalid '{timing_name}';"
                    " expected nonnegative integer or null",
                )
        attr_name = f":c-{field}"
        if binding_mode == "one-way":
            if (
                handler is not None
                or lazy
                or on_event is not None
                or key is not None
                or debounce is not None
                or throttle is not None
            ):
                _fail(location, f"{DATA_CEV_BIND!r} spec {index} has update fields on a one-way binding")
            _validate_binding_target(
                element,
                binding_mode="one-way",
                attr_name=attr_name,
                location=location,
            )
            continue
        if not isinstance(handler, str) or not handler:
            _fail(location, f"{DATA_CEV_BIND!r} spec {index} needs a nonempty two-way 'handler'")
        if lazy and on_event is not None:
            _fail(location, f"{DATA_CEV_BIND!r} spec {index} cannot combine 'lazy' with an explicit 'on' event")
        _validate_two_way_control(
            element,
            lazy=lazy,
            on_event=on_event,
            attr_name=attr_name,
            location=location,
        )


def _merge_encoded(attrs: dict[str, Any], name: str, specs: list[dict[str, Any]], location: _Location) -> None:
    """
    Set (or extend) a ``data-cev-*`` attribute with new specs.

    When stage one already emitted this attribute on the same element (a literal
    binding alongside a spread), the existing specs are decoded and the new ones
    appended, so both survive in one attribute.
    """
    existing = attrs.get(name)
    if existing is not None:
        prior = _decode_compiled_specs(name, existing, location)
        specs = [*prior, *specs]
    attrs[name] = _encode(specs)
