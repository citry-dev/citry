"""
The action constructors of the ``events`` extension: what a handler returns.

An event handler's return value is its whole response, and what flows back to
the browser is **actions**: self-addressed instructions the client runtime
applies in order (design ``docs/design/events.md`` 3.4). The capitalized
constructors here build those action values; calling one performs nothing.
Import the namespace once and return what you build::

    from citry.ext.events import actions

    class Events:
        def save(self, state):
            order = create_order(state.draft_id)
            return [
                actions.Dispatch("order-saved", {"id": order.id}),
                actions.Redirect(f"/orders/{order.id}"),
            ]

Every envelope action accepts ``delay`` (seconds before the client applies the
action). Most also accept ``wait`` (whether later actions hold for it). A
``Data`` action always waits because applying it resolves the caller's
promise. ``Download`` is not an envelope action; it constructs a raw HTTP
response result.

Turning return values into these actions (dicts, elements, resolver-claimed
values) and encoding them for the wire lives in the sibling ``results``
module; this module is only the vocabulary.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any
from unicodedata import category, normalize
from urllib.parse import quote

from citry._protocol.events import SWAPS, is_finite_json_number
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender
from citry.util.id import validate_render_id

__all__ = [
    "Action",
    "Data",
    "Dispatch",
    "Download",
    "PushUrl",
    "Redirect",
    "Render",
    "ReplaceUrl",
]

# Debug-mode construction tracking: while a handler call is being dispatched
# in debug mode, this holds the per-call list every constructed action or
# download result is appended to, so a value that is constructed but never
# returned can be warned about after encoding (construction alone does nothing,
# design events.md 14.1.3). Activated by ``results.track_constructed_actions``;
# ``None`` means no tracking, the production state.
_CONSTRUCTED_ACTIONS: ContextVar[list[Any] | None] = ContextVar(
    "citry_events_constructed_actions",
    default=None,
)


# The action dataclasses are frozen (an action is a value) and deliberately
# not slotted: dataclass slots rebuild the class object, which breaks the
# zero-argument super() call the subclasses' __post_init__ validation chains
# through.
@dataclass(frozen=True)
class Action:
    """
    Base class of the action values an event handler returns.

    The concrete constructors are [`Render`][citry.ext.events.actions.Render],
    [`Data`][citry.ext.events.actions.Data],
    [`Dispatch`][citry.ext.events.actions.Dispatch], and
    [`Redirect`][citry.ext.events.actions.Redirect], plus the history actions
    [`PushUrl`][citry.ext.events.actions.PushUrl] and
    [`ReplaceUrl`][citry.ext.events.actions.ReplaceUrl]. An action is a plain
    value: constructing one performs nothing, and it only takes effect when
    the handler returns it (alone or in a list).

    Attributes:
        delay: Seconds the client waits before applying the action. ``0``
            (the default) applies it immediately.
        wait: Whether later actions in the same result hold until this one
            (and its ``delay``) has applied. ``True`` (the default) keeps the
            list strictly sequential; ``False`` schedules this action and
            lets the rest proceed immediately. Concrete actions may require
            ``True`` when their effect cannot run independently.

    """

    delay: float = field(default=0, kw_only=True)
    wait: bool = field(default=True, kw_only=True)

    def __post_init__(self) -> None:
        # Subclasses validate their own fields first and call this last, so a
        # rejected constructor call never lands in the debug tracker.
        if not is_finite_json_number(self.delay) or self.delay < 0:
            msg = (
                f"actions.{type(self).__name__}: delay must be a finite, non-negative number of seconds;"
                f" got {self.delay!r}."
            )
            raise ValueError(msg)
        if not isinstance(self.wait, bool):
            msg = f"actions.{type(self).__name__}: wait must be True or False; got {self.wait!r}."
            # ValueError, not TypeError: one exception type for every rejected
            # constructor argument (matching the extension's other validation).
            raise ValueError(msg)  # noqa: TRY004
        constructed = _CONSTRUCTED_ACTIONS.get()
        if constructed is not None:
            constructed.append(self)


@dataclass(frozen=True)
class Render(Action):
    """
    Render a component element server-side and morph it into the page.

    The element renders as a citry fragment (markup plus its dependency and
    events manifests), and the client swaps it into ``target``. A handler
    builds a fresh tree to render; nothing of the instance's original render
    is replayed (design ``events.md`` 7.5).

    Attributes:
        element: What to render: a component element (``MyComponent(...)``)
            or an already-rendered
            [`CitryRender`][citry.CitryRender].
        target: Where the rendered HTML goes: a CSS selector string (applied
            to every match), or ``None`` (the default) for the component
            instance whose event was called.
        swap: How the HTML is applied: ``"morph"`` (the default, a minimal
            in-place diff), ``"replace"``, ``"inner"``, ``"append"``,
            ``"prepend"``, ``"remove"``, or ``"none"``.
        delay: Seconds the client waits before applying the action.
        wait: Whether later actions hold until this one has applied.

    Example:
        ```python
        def add_to_cart(self, data: CartIn, context):
            cart = add_item(context.user, data.product_id)
            return actions.Render(
                CartBadge(count=cart.count),
                target="#cart-badge",
            )
        ```

    """

    element: CitryElement | CitryRender
    target: str | None = None
    swap: str = "morph"

    def __post_init__(self) -> None:
        if not isinstance(self.element, (CitryElement, CitryRender)):
            if isinstance(self.element, type):
                msg = (
                    f"actions.Render: element must be a component element, but got the class"
                    f" {self.element.__name__}; call it to build the element first:"
                    f" {self.element.__name__}(...)."
                )
            else:
                msg = (
                    f"actions.Render: element must be a component element (MyComponent(...)) or an"
                    f" already-rendered CitryRender; got {type(self.element).__name__!r}."
                )
            # ValueError, not TypeError: one exception type for every rejected
            # constructor argument (matching the extension's other validation).
            raise ValueError(msg)  # noqa: TRY004
        if self.target is not None and (not isinstance(self.target, str) or not self.target):
            msg = (
                f"actions.Render: target must be a CSS selector string, or None for the calling"
                f" instance; got {self.target!r}."
            )
            raise ValueError(msg)
        if self.target is not None and self.target.startswith("render:"):
            try:
                validate_render_id(self.target[7:])
            except (TypeError, ValueError) as error:
                msg = (
                    "actions.Render: a target beginning with 'render:' must carry an HTML-case-safe"
                    f" render ID; got {self.target!r}."
                )
                raise ValueError(msg) from error
        if self.swap not in SWAPS:
            msg = f"actions.Render: swap must be one of {', '.join(repr(s) for s in SWAPS)}; got {self.swap!r}."
            raise ValueError(msg)
        super().__post_init__()


@dataclass(frozen=True)
class Data(Action):
    """
    Resolve the client caller's promise with a JSON value.

    The value becomes the resolution of the ``$sendEvent``,
    ``$component`` ``sendEvent``, or ``Citry.events.send`` promise on the
    client. Declarative ``@c-*`` bindings discard that promise, so they do
    not expose the Data value; return ``Dispatch`` when browser code must
    observe their result. At most one ``Data`` may appear in one handler
    result (two would contradict: which value resolves the promise?);
    returning a bare ``dict`` from a handler builds this action implicitly.

    Attributes:
        value: The JSON-serializable value the caller receives.
        delay: Seconds the client waits before applying the action.
        wait: Always ``True`` because applying this action resolves the
            caller's promise.

    Raises:
        ValueError: If ``wait`` is ``False``, or another timing value is
            invalid.

    """

    value: Any

    def __post_init__(self) -> None:
        if self.wait is False:
            msg = "actions.Data: wait must be True because Data resolves the caller's promise; got False."
            raise ValueError(msg)
        super().__post_init__()


@dataclass(frozen=True)
class Dispatch(Action):
    """
    Dispatch a named browser event (a DOM ``CustomEvent``).

    The event fires under the exact given name on the calling instance's first
    live root (or on ``document`` when the call carries no instance), bubbles,
    and reaches ``onEvent`` listeners and plain ``addEventListener`` alike. A
    multi-root or mirrored instance deliberately uses one canonical root so a
    logical dispatch reaches document-level listeners only once.
    Names starting with ``citry:`` are reserved for the runtime's own events;
    the documented convention is prefixing with the component name
    (``"MyCard:submit"``).

    Attributes:
        name: The event name, dispatched verbatim.
        detail: The ``CustomEvent`` ``detail`` payload, a JSON-serializable
            value; ``None`` (the default) sends no detail.
        delay: Seconds the client waits before applying the action.
        wait: Whether later actions hold until this one has applied.

    """

    name: str
    detail: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            msg = f"actions.Dispatch: name must be a non-empty string; got {self.name!r}."
            raise ValueError(msg)
        if self.name.startswith("citry:"):
            msg = (
                f"actions.Dispatch: event names starting with 'citry:' are reserved for the citry"
                f" runtime; got {self.name!r}. Pick another name (the convention is prefixing with"
                f" the component name, e.g. 'MyCard:submit')."
            )
            raise ValueError(msg)
        super().__post_init__()


@dataclass(frozen=True)
class Redirect(Action):
    """
    Navigate the page to a URL.

    A redirect is an ordinary action, not an HTTP 30x: it applies in list
    order like everything else. Actions listed after it race the navigation,
    so put it last, or give it ``delay`` / ``wait`` timing when something
    (say a farewell toast) must be seen first:
    ``actions.Redirect(url, delay=5, wait=False)``.

    Attributes:
        url: The URL to navigate to.
        delay: Seconds the client waits before applying the action.
        wait: Whether later actions hold until this one has applied.

    """

    url: str

    def __post_init__(self) -> None:
        if not isinstance(self.url, str) or not self.url:
            msg = f"actions.Redirect: url must be a non-empty string; got {self.url!r}."
            raise ValueError(msg)
        super().__post_init__()


@dataclass(frozen=True)
class PushUrl(Action):
    """
    Push a URL onto the browser's history stack without navigating.

    The browser changes the address and adds one history entry, but Citry does
    not fetch the URL or replace the page. Back and Forward therefore change
    the address without restoring component HTML or State; use a client router
    when that restoration is required.

    Attributes:
        url: The same-origin URL to place in browser history. Relative URLs,
            query strings, and fragments are accepted; the browser resolves
            them against the current document.
        delay: Seconds the client waits before applying the action.
        wait: Whether later actions hold until this one has applied.

    """

    url: str

    def __post_init__(self) -> None:
        if not isinstance(self.url, str) or not self.url:
            msg = f"actions.PushUrl: url must be a non-empty string; got {self.url!r}."
            raise ValueError(msg)
        super().__post_init__()


@dataclass(frozen=True)
class ReplaceUrl(Action):
    """
    Replace the browser's current history URL without navigating.

    The browser changes the address in place, but Citry does not fetch the URL
    or replace the page. Back and Forward therefore change the address without
    restoring component HTML or State; use a client router when that
    restoration is required.

    Attributes:
        url: The same-origin URL to place in browser history. Relative URLs,
            query strings, and fragments are accepted; the browser resolves
            them against the current document.
        delay: Seconds the client waits before applying the action.
        wait: Whether later actions hold until this one has applied.

    """

    url: str

    def __post_init__(self) -> None:
        if not isinstance(self.url, str) or not self.url:
            msg = f"actions.ReplaceUrl: url must be a non-empty string; got {self.url!r}."
            raise ValueError(msg)
        super().__post_init__()


################################################
# DOWNLOAD RESPONSE
################################################


_BIDI_CONTROLS = frozenset(
    {
        "\u061c",
        "\u200e",
        "\u200f",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
        "\u2066",
        "\u2067",
        "\u2068",
        "\u2069",
    }
)


@dataclass(frozen=True)
class Download:
    """
    Return a file download from a per-event HTTP handler.

    A download is an HTTP response result, not an envelope action. Its handler
    must use ``@event(bundle=False)`` and be called through its per-event HTTP
    route. It may be returned bare or as the only item in a list or tuple.

    Attributes:
        content: The response body, as text or raw bytes.
        filename: The filename offered to the browser. It may contain Unicode,
            but cannot be a path or contain control characters.
        content_type: The response's media type. The default is
            ``"application/octet-stream"``.

    Example:
        ```python
        from citry.ext.events import actions, event

        @event(bundle=False)
        def export(self):
            return actions.Download(
                make_csv(),
                "orders.csv",
                content_type="text/csv; charset=utf-8",
            )
        ```

    """

    content: str | bytes
    filename: str
    content_type: str = "application/octet-stream"

    def __post_init__(self) -> None:
        if not isinstance(self.content, (str, bytes)):
            msg = f"actions.Download: content must be str or bytes; got {type(self.content).__name__!r}."
            raise ValueError(msg)  # noqa: TRY004 - one exception type for constructor validation
        if not isinstance(self.filename, str) or not self.filename:
            msg = f"actions.Download: filename must be a non-empty string; got {self.filename!r}."
            raise ValueError(msg)
        if self.filename != self.filename.strip():
            msg = "actions.Download: filename cannot start or end with whitespace."
            raise ValueError(msg)
        if self.filename in {".", ".."}:
            msg = "actions.Download: filename must name a file, not '.' or '..'."
            raise ValueError(msg)
        if "/" in self.filename or "\\" in self.filename:
            msg = "actions.Download: filename cannot contain path separators."
            raise ValueError(msg)
        if any(category(char) in {"Cc", "Cs"} or char in _BIDI_CONTROLS for char in self.filename):
            msg = (
                "actions.Download: filename cannot contain control or bidirectional formatting"
                " characters, or surrogate code points."
            )
            raise ValueError(msg)
        if not isinstance(self.content_type, str) or not self.content_type:
            msg = f"actions.Download: content_type must be a non-empty string; got {self.content_type!r}."
            raise ValueError(msg)
        if any(ord(char) < 32 or ord(char) > 126 for char in self.content_type):
            msg = "actions.Download: content_type must contain printable ASCII characters only."
            raise ValueError(msg)
        constructed = _CONSTRUCTED_ACTIONS.get()
        if constructed is not None:
            constructed.append(self)


def _download_content_disposition(filename: str) -> str:
    """Build an attachment header with ASCII fallback and UTF-8 filename."""
    decomposed = normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    fallback = "".join(char if char.isalnum() or char in " ._-" else "_" for char in decomposed)
    fallback = fallback.strip()
    leading_dots = len(filename) - len(filename.lstrip("."))
    fallback_body = fallback[leading_dots:].lstrip().rstrip(" .")
    if not fallback_body or fallback_body.startswith("."):
        # Preserve an intentional dotfile prefix while replacing a stem lost during ASCII conversion.
        fallback_body = f"download{fallback_body}"
    fallback = f"{'.' * leading_dots}{fallback_body}"
    encoded = quote(filename, safe="!#$&+-.^_`|~")
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"
