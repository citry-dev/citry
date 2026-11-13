"""
The user-facing error of the ``events`` extension, and its wire shape.

A handler or guard raises :class:`EventError` to answer a call with a
structured error instead of actions: the client receives
``{status, code, message, fieldErrors?}`` and surfaces ``message`` as the human
summary and ``fieldErrors`` as the per-field map next to inputs (design
``docs/design/events.md`` 3.7 and 4.3). One class with a ``status`` argument
covers forbidden, not-found, and conflict without an exception zoo.

This module also maps a failed schema validation (the structured
``ValidationResult`` of the sibling ``schemas`` module) onto the same wire
shape: the 422 ``invalid_args`` error object, with the validator's per-field
messages as ``fieldErrors``.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import TYPE_CHECKING, Any, NamedTuple

from citry._protocol.events import build_error

if TYPE_CHECKING:
    from citry.ext.events.schemas import ValidationResult

# The wire code of each user-raisable status. Every row is protocol
# vocabulary (packages/protocol/events/v1, spec.md section 4.5): 403 ->
# "forbidden" (also pinned by design events.md 3.7), 404 -> "not_found",
# 409 -> "conflict", and 422 -> "invalid_args" (shared with schema
# validation). A status outside this map ships the protocol's catch-all
# code "error" together with the raised status, unchanged.
_STATUS_CODES = {
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "invalid_args",
}
_FALLBACK_CODE = "error"

# A request alone decides how many fields it sends that the data class
# does not declare (or State fields the browser may not write), and how
# many items one list or dict field holds. Listing a message for each
# could make the response many times the size of the request, so an error
# lists at most this many of each kind. Messages about other fields, and
# fields an author passes to EventError, are always listed.
MAX_UNEXPECTED_FIELDS = 20
MAX_ITEM_ERRORS = 20

# Pydantic's error types for a key a model does not declare: v2, then v1.
PYDANTIC_EXTRA_TYPES = frozenset({"extra_forbidden", "value_error.extra"})

# What schema-validation failures say as the human summary; the real content
# is the per-field map (design events.md 3.7).
_INVALID_ARGS_MESSAGE = "Invalid event arguments."


class EventError(Exception):
    """
    A structured error an event handler or guard raises to answer a call.

    The client receives the ``status``, a stable string ``code`` derived from
    it, the ``message`` as the human summary (a toast or banner), and
    ``fieldErrors`` as the per-field error map surfaced next to inputs
    (for example, ``$error('submit')?.fieldErrors``). Raising it anywhere in a
    handler, a guard, or the
    ``_context`` hook turns the call into that error response; it never
    becomes a host 500.

    Attributes:
        message: The human summary of the error.
        fields: Per-field error messages, keyed by data-schema field name
            (e.g. ``{"email": "Enter a valid email address."}``). Empty when
            the error is not about specific fields.
        status: The HTTP status of the error (400 to 599). ``422`` (the
            default) is a validation failure; ``403``, ``404``, and ``409``
            cover forbidden, not found, and conflict.

    Example:
        ```python
        from citry.ext.events import EventError

        class DocumentEditor(Component):
            class State:
                document_id: int

            class Events:
                def _guard(self):
                    user = user_from_request(self.request)
                    if can_edit(user, self.state.document_id):
                        return
                    raise EventError(
                        "You cannot edit this document.",
                        status=403,
                    )

                def subscribe(self, data: SubscribeIn):
                    if is_taken(data.email):
                        raise EventError(
                            "Please fix the errors below.",
                            fields={"email": "Already subscribed."},
                        )
        ```

    """

    def __init__(self, message: str, fields: Mapping[str, str] | None = None, status: int = 422) -> None:
        if not isinstance(message, str) or not message:
            msg = f"EventError: message must be a non-empty string; got {message!r}."
            raise ValueError(msg)
        if isinstance(status, bool) or not isinstance(status, int) or not 400 <= status <= 599:
            msg = f"EventError: status must be an HTTP error status (400 to 599); got {status!r}."
            raise ValueError(msg)
        if fields is not None and (
            not isinstance(fields, Mapping)
            or not all(isinstance(key, str) and isinstance(value, str) for key, value in fields.items())
        ):
            msg = (
                f"EventError: fields must map field names to messages,"
                f' e.g. {{"email": "Enter a valid email address."}}; got {fields!r}.'
            )
            raise ValueError(msg)
        super().__init__(message)
        self.message = message
        self.fields: dict[str, str] = dict(fields) if fields else {}
        self.status = status

    @property
    def code(self) -> str:
        """The stable wire code for the error's status (e.g. ``"forbidden"`` for 403)."""
        return _STATUS_CODES.get(self.status, _FALLBACK_CODE)


def limit_unexpected_fields(fields: Mapping[str, str], unexpected: Collection[str]) -> tuple[dict[str, str], int]:
    """
    Keep the first ``MAX_UNEXPECTED_FIELDS`` unexpected-field messages and drop the rest.

    Every other message is kept. "First" follows the order of ``fields``,
    so a caller that sorts its messages keeps the same names on every call.

    Args:
        fields: The per-field messages.
        unexpected: The names in ``fields`` that the request sent but the
            schema or State does not declare.

    Returns:
        The kept messages, and how many unexpected-field messages were
        dropped.

    """
    if len(unexpected) <= MAX_UNEXPECTED_FIELDS:
        return dict(fields), 0
    kept: dict[str, str] = {}
    listed = 0
    for name, message in fields.items():
        if name in unexpected:
            # Past the limit an unexpected name is only counted.
            if listed >= MAX_UNEXPECTED_FIELDS:
                continue
            listed += 1
        kept[name] = message
    return kept, len(unexpected) - listed


class FieldErrors:
    """
    Collect the per-field messages of one validation, and limit them when it fails.

    A validator walks the payload and calls this for each part that does
    not fit. It names a part by a field path: a pair of the parent's path
    and one more key or list index, with ``None`` above the top level, so
    ``(((None, "scores"), "alice"), 3)`` written out as text is
    ``scores.alice.3``. A pair shares its parent with its siblings, so a
    long dict key over many list items is held once. Writing the text for
    each item would copy that key once per item, which takes time and
    memory growing with the square of the request's size.

    The text is written in :meth:`limited`, only for the messages it keeps.
    """

    __slots__ = ("_containers", "_records", "pydantic_total")

    def __init__(self, *, shares_total_with: FieldErrors | None = None) -> None:
        self._records: list[tuple[Any, str, int]] = []
        self._containers: list[Any] = []
        # A validation can call Pydantic once per nested object, and only a
        # running total bounds the cost. A scratch collector for one attempt
        # at a union shares its parent's.
        self.pydantic_total: PydanticTotal = (
            PydanticTotal() if shares_total_with is None else shares_total_with.pydantic_total
        )

    def __bool__(self) -> bool:
        return bool(self._records)

    def add(self, path: Any, message: str) -> None:
        """Record ``message``, unless an earlier message has the same path text."""
        self._records.append((path, message, _KEEP_FIRST))

    def add_unexpected(self, path: Any, message: str) -> None:
        """Record a message for a field the request should not have sent, which counts toward the limit on those."""
        self._records.append((path, message, _KEEP_FIRST_UNEXPECTED))

    def set_unexpected(self, path: Any, message: str) -> None:
        """Record a message for a field the request should not have sent, over any earlier one with the same text."""
        self._records.append((path, message, _REPLACE_UNEXPECTED))

    def add_container(self, path: Any) -> None:
        """Mark the path of a list or dict field whose items the request decides the number of."""
        self._containers.append(path)

    def first_message(self) -> str | None:
        """Return the first message recorded, or ``None``."""
        return self._records[0][1] if self._records else None

    def limited(self) -> tuple[dict[str, str], int]:
        """
        Return the messages to send, and how many were left out.

        The messages are sorted by path, with list indexes in number order.
        At most ``MAX_UNEXPECTED_FIELDS`` messages for unexpected fields are
        kept, and at most ``MAX_ITEM_ERRORS`` inside each list or dict
        field. A message is inside a container when its path text starts
        with the container's path text and a dot (``tags.3`` is inside
        ``tags``), and in a nested container it counts toward every
        container it is inside. "First" follows the sorted order.

        Returns:
            The kept messages by path text, and how many were dropped.

        """
        root, unexpected_count = self._build_tree()
        return _walk_path_tree(root, limit_unexpected=unexpected_count > MAX_UNEXPECTED_FIELDS)

    def _build_tree(self) -> tuple[_PathNode, int]:
        """Place every record in one tree, and return its root and the number of unexpected fields."""
        tree = _PathTree()
        unexpected_count = 0
        for path, message, kind in self._records:
            node = tree.place(path)
            # Two paths with the same text reach the same node, however a
            # dotted key split them, so the first of them keeps its message.
            is_first = node.message is None
            if is_first or kind == _REPLACE_UNEXPECTED:
                node.message = message
                if kind != _KEEP_FIRST and not node.unexpected:
                    node.unexpected = True
                    unexpected_count += 1
        for path in self._containers:
            tree.place(path).container = True
        return tree.root, unexpected_count


class PydanticTotal:
    """What one validation has handed to Pydantic so far."""

    __slots__ = ("measured", "path_text", "size", "sized")

    def __init__(self) -> None:
        self.path_text = 0
        self.size = 0
        # Each container's id with each model that measured it, and the ids
        # of the containers already in `size`.
        self.measured: set[tuple[int, type]] = set()
        self.sized: set[int] = set()


# How FieldErrors treats a record whose path text already has a message.
_KEEP_FIRST = 0
_KEEP_FIRST_UNEXPECTED = 1
_REPLACE_UNEXPECTED = 2


class _TrimmedPath(NamedTuple):
    """A field path with the dots at the end of its text removed; see :func:`trimmed_path`."""

    path: Any
    empty_name: str | None


def trimmed_path(path: Any, empty_name: str | None = None) -> _TrimmedPath:
    """
    Name the part at ``path`` when its text may end in dots.

    A model-level message from Pydantic has no field of its own, so it goes
    on the path of the object it describes, with any dots at the end of that
    path's text removed. ``empty_name`` is used when no text is left.
    """
    return _TrimmedPath(path, empty_name)


class _PathNode:
    """One dot-separated segment of a path's text, with what was recorded for the path that ends here."""

    __slots__ = (
        "children",
        "container",
        "listed",
        "message",
        "only_child",
        "segment",
        "trimmed",
        "unexpected",
    )

    def __init__(self, segment: str, trimmed: _PathNode | None) -> None:
        self.segment = segment
        # The node of this path's text without the dots at its end, or None
        # when the text does not end in a dot.
        self.trimmed = trimmed
        # A key full of dots makes a long chain of nodes with one child each,
        # so one child is held directly and a dict is made for the second.
        self.only_child: _PathNode | None = None
        self.children: dict[str, _PathNode] | None = None
        self.message: str | None = None
        self.unexpected = False
        self.container = False
        self.listed = 0

    def child(self, segment: str, *, root: _PathNode) -> _PathNode:
        """Return the node for one more segment, created on first use."""
        only_child = self.only_child
        if only_child is not None and only_child.segment == segment:
            return only_child
        node = None if self.children is None else self.children.get(segment)
        if node is None:
            # Only an empty segment below the first means the text ends in a dot.
            node = _PathNode(segment, (self.trimmed or self) if segment == "" and self is not root else None)
            if only_child is None and self.children is None:
                self.only_child = node
            else:
                if self.children is None:
                    assert only_child is not None  # noqa: S101 - the branch above holds the first child
                    self.children = {only_child.segment: only_child}
                    self.only_child = None
                self.children[segment] = node
        return node

    def ordered_children(self) -> list[_PathNode]:
        """Return the children in path order."""
        if self.children is None:
            return [] if self.only_child is None else [self.only_child]
        return sorted(self.children.values(), key=_segment_order)


class _PathTree:
    """
    The tree that gives each path text one node, read one dot-separated segment at a time.

    A dict key may itself hold dots, so ``a.b`` as one key and ``b`` nested
    inside ``a`` have the same text and must share one message. Splitting
    every key at its dots makes them reach the same node. Each field path
    pair is placed once and shares its parent's node, so a long key is
    split once however many items sit under it.
    """

    __slots__ = ("_placed", "root")

    def __init__(self) -> None:
        self.root = _PathNode("", None)
        # By identity: FieldErrors keeps every pair alive, and hashing a pair
        # would walk all its parents.
        self._placed: dict[int, _PathNode] = {}

    def place(self, path: Any) -> _PathNode:
        """Return the node of a field path, or of a path from :func:`trimmed_path`."""
        if isinstance(path, _TrimmedPath):
            return self._place_trimmed(path)
        root = self.root
        if path is None:
            return root.child("", root=root)
        placed = self._placed
        waiting = []
        pair = path
        # Climb to the nearest parent already placed, so that a shared parent
        # is read once.
        while pair is not None and id(pair) not in placed:
            waiting.append(pair)
            pair = pair[0]
        node = root if pair is None else placed[id(pair)]
        for pair in reversed(waiting):
            for segment in f"{pair[1]}".split("."):
                node = node.child(segment, root=root)
            placed[id(pair)] = node
        return node

    def _place_trimmed(self, path: _TrimmedPath) -> _PathNode:
        node = self.place(path.path)
        node = node.trimmed or node
        root = self.root
        if path.empty_name is not None and node is root.child("", root=root):
            return root.child(path.empty_name, root=root)
        return node


def _segment_order(node: _PathNode) -> tuple[int, int, str, str]:
    """
    Sort a path segment, with list indexes in number order.

    Only the first 20 item messages of a list are kept, so ``tags.2`` must
    come before ``tags.10`` for the earliest items to be the ones kept.
    """
    part = node.segment
    # An all-digit segment sorts by its length without leading zeros, then
    # by its digits, which is number order without converting it: a key
    # the request sends can be thousands of digits long. Text segments sort
    # after numbers, so the two kinds are never compared directly.
    if part.isascii() and part.isdigit():
        digits = part.lstrip("0")
        return (0, len(digits), digits, part)
    return (1, 0, part, part)


def _walk_path_tree(root: _PathNode, *, limit_unexpected: bool) -> tuple[dict[str, str], int]:
    """
    Visit the tree in path order and return the kept messages and how many were dropped.

    A path sorts before the longer paths that start with it, so a node's
    message comes before its children, and the children go in segment
    order. The walk uses its own stack because a key full of dots makes a
    tree far deeper than Python's recursion limit.
    """
    kept: dict[str, str] = {}
    dropped = 0
    unexpected_listed = 0
    # The text of the current path, one segment each. Written out only for a
    # kept message, and the limits keep few of those.
    segments: list[str] = []
    # The containers the walk is inside, and how many of them are full. A
    # message under a full container is dropped without looking at the rest.
    open_containers: list[_PathNode] = []
    full_containers = 0

    # False to enter a node, True to leave it after its children.
    stack: list[tuple[_PathNode, bool]] = []

    stack.extend((child, False) for child in reversed(root.ordered_children()))
    while stack:
        node, leaving = stack.pop()
        if leaving:
            segments.pop()
            if node.container:
                open_containers.pop()
                if node.listed >= MAX_ITEM_ERRORS:
                    full_containers -= 1
            continue
        # A trimmed link points back up the tree, so clearing it lets the tree
        # be freed at once, without waiting for the garbage collector.
        node.trimmed = None
        segments.append(node.segment)
        message = node.message
        if message is not None:
            if node.unexpected and limit_unexpected and unexpected_listed >= MAX_UNEXPECTED_FIELDS:
                dropped += 1
            else:
                unexpected_listed += node.unexpected
                if full_containers:
                    dropped += 1
                else:
                    kept[".".join(segments)] = message
                    for container in open_containers:
                        container.listed += 1
                        if container.listed == MAX_ITEM_ERRORS:
                            full_containers += 1
        # A message counts toward the containers around it, not its own.
        if node.container:
            open_containers.append(node)
        stack.append((node, True))
        stack.extend((child, False) for child in reversed(node.ordered_children()))
    return kept, dropped


def unlisted_fields_note(count: int) -> str:
    """
    Return the sentence that ends an error message when field messages were left out.

    Returns an empty string for a count of 0, so a caller can append it
    unconditionally. The text starts with a space.
    """
    if count <= 0:
        return ""
    noun = "field error is" if count == 1 else "field errors are"
    return f" {count:,} more {noun} not shown."


def invalid_args_error(result: ValidationResult) -> EventError:
    """
    The ``EventError`` for a failed schema validation.

    Wraps the validator's per-field messages as the 422 ``invalid_args``
    error, the same shape a handler raises by hand, so the client handles
    both identically.

    Args:
        result: A failed ``ValidationResult`` from
            [`validate_args`][citry.ext.events.schemas.validate_args].

    Returns:
        The 422 error carrying the result's field messages.

    Raises:
        ValueError: When the result did not fail (there is no error to build).

    """
    if result.ok:
        msg = "invalid_args_error() takes a failed ValidationResult; this one succeeded."
        raise ValueError(msg)
    message = _INVALID_ARGS_MESSAGE + unlisted_fields_note(result.unlisted_fields)
    return EventError(message, fields=result.fields, status=422)


def wire_error(error: EventError) -> dict[str, Any]:
    """
    The wire object of an ``EventError``: what a failed call's result carries.

    The shape is ``{status, code, message}`` plus ``fieldErrors`` when the error
    has per-field messages (design ``events.md`` 4.3).

    Args:
        error: The error to encode.

    Returns:
        The JSON-ready error object.

    """
    return build_error(error.status, error.code, error.message, error.fields)
