"""
Check how many digits a ``Decimal`` would take to write out, before anything writes it.

A ``Decimal`` keeps its exponent apart from its digits, so a few characters
such as ``"1e999999999"`` hold a number with a billion digits. Nothing is
spent while the number is only stored. The cost comes when something writes
every digit: a fixed-point format such as ``f"{amount:.2f}"``, ``"%d" % amount``,
or ``int(amount)``. Those take memory or CPU time that grows with the
exponent, so one short request value can cost gigabytes.

Citry checks a ``Decimal`` that a request supplies (an Events argument, a
State write, or the State a token restores) against about the range a
``float`` accepts: its size, ignoring the sign, must be below ``1e309``, and
it may have at most 308 decimal places. A zero with more than 308 decimal
places is refused too, since ``f"{amount:f}"`` writes every one of them.
Written out in full, an accepted number has at most 617 digits, and money or
measurement values sit far inside that range. The i18n
number formatter uses the same check with the wider range its Rust formatter
supports.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import fields, is_dataclass
from decimal import Decimal
from typing import Any

# The power of ten of the first digit (`Decimal.adjusted()`) may be at most
# this, so a request number's size stays below 1e309, as a float's does.
REQUEST_DECIMAL_LARGEST = 308
# The power of ten of the last digit (the exponent of `Decimal.as_tuple()`)
# may be at least this, so a request number has at most 308 decimal places.
REQUEST_DECIMAL_SMALLEST = -308
# The message names the limit and never the value, so a refused number cannot
# become a huge response or log line.
REQUEST_DECIMAL_MESSAGE = (
    "Not a valid Decimal: the number is too large or has too many decimal places. "
    "Enter a number between -1e309 and 1e309 with at most 308 decimal places."
)


# Values that hold nothing for the walk to read, checked by exact type
# because that test is the cheapest and these are most of a request's values.
_PLAIN_TYPES = frozenset({str, bytes, int, float, bool, type(None)})


class SharedWalk:
    """What the walks of one validation have read in full (see ``shared_walk``)."""

    __slots__ = ("last_root", "objects", "walks")

    def __init__(self) -> None:
        # The objects read, by id, each held so its id stays its own.
        self.objects: dict[int, Any] = {}
        # How many walks finished, and the value the latest one started from.
        self.walks = 0
        self.last_root: Any = None

    def needs_final_walk(self, result: Any) -> bool:
        """
        Whether ``result`` must be walked again, with nothing skipped, before a handler sees it.

        Code that runs after a walk, such as an outer ``__post_init__`` or
        validator, can write a new ``Decimal`` into an object the walk read,
        and a later walk skips that object. Only when the one walk was of
        ``result`` itself, as the last step, did no code run after it.
        """
        return self.walks > 1 or (self.walks == 1 and self.last_root is not result)


# The record of the `shared_walk` running in this context, or None outside one.
_WALKED: ContextVar[SharedWalk | None] = ContextVar("citry_decimal_walked", default=None)


def decimal_in_range(value: Decimal, *, largest: int, smallest: int) -> bool:
    """
    Return whether every digit of ``value`` lies between ``10**smallest`` and ``10**largest``.

    The check reads only the exponents, so it costs the same for any value.
    NaN and infinity have no digits to write, so they pass; callers that
    must refuse them check ``is_finite()`` themselves.

    Args:
        value: The number to check.
        largest: The highest power of ten the first digit may have.
        smallest: The lowest power of ten the last digit may have.

    Returns:
        ``True`` when writing ``value`` out in full stays within the range.

    """
    last = value.as_tuple().exponent
    # NaN and infinity carry a letter here instead of a number.
    if not isinstance(last, int):
        return True
    # Zero is checked too: `format(Decimal("0e-1000000"), "f")` writes a
    # million zeros, so a zero with a far exponent costs as much as any value.
    return value.adjusted() <= largest and last >= smallest


def request_decimal_in_range(value: Decimal) -> bool:
    """Return whether ``value`` fits the range Citry accepts for a ``Decimal`` from a request."""
    return decimal_in_range(value, largest=REQUEST_DECIMAL_LARGEST, smallest=REQUEST_DECIMAL_SMALLEST)


@contextmanager
def shared_walk() -> Iterator[SharedWalk]:
    """
    Let the walks of one validation skip the objects an earlier walk read in full.

    Citry checks a Pydantic result as soon as Pydantic returns, at every
    level of nested data, so without this an outer level would walk again
    everything its inner levels already walked, and data nested ``n``
    levels deep would cost ``n`` times its size. The objects are held until
    the scope ends, so a freed object's id cannot be reused by a new one.

    A skipped object may have changed after its walk: an outer
    ``__post_init__`` or validator can write a new ``Decimal`` into it. So
    when ``SharedWalk.needs_final_walk`` says so, the caller walks the
    finished result once more after the scope ends, with nothing skipped,
    before any handler sees it.

    Yields:
        The record of the walks, which the caller asks about the final walk.

    """
    record = SharedWalk()
    token = _WALKED.set(record)
    try:
        yield record
    finally:
        _WALKED.reset(token)


def find_oversized_decimal(value: Any) -> tuple[Any, ...] | None:
    """
    Find a ``Decimal`` inside a checked value that is outside the request range.

    Pydantic builds its own ``Decimal`` values from request text, and a
    validator may build more, so Citry walks the result after Pydantic has
    checked it. The walk reads lists, tuples, deques, sets, dict keys
    (the items of a tuple key too) and values, dataclass fields, the fields
    and extra values of a Pydantic model (v1 or v2), and the value inside a
    ``pydantic.Secret``. It ignores
    other objects, such as an app's own classes, so a type of yours that
    holds a ``Decimal`` needs its own check. It never reads an iterator,
    which would use it up.

    The walk keeps its own list of what is left to read, so data nested as
    deeply as a request allows takes no extra Python frames. It reads each
    object once, and inside ``shared_walk`` it skips the objects an earlier
    walk of the same validation read in full.

    Args:
        value: A value built from request data.

    Returns:
        The keys and list indexes that lead from ``value`` to the first
        such ``Decimal``, in field and item order, or ``None`` when there
        is none. A key is ``None`` for a set item or a dict key, which
        have no key of their own; any keys after it lead inside that item,
        such as a tuple key. An empty tuple means ``value`` itself.

    """
    if isinstance(value, Decimal):
        return None if request_decimal_in_range(value) else ()
    record = _WALKED.get()
    shared = record.objects if record is not None else None
    walked: dict[int, Any] = {}
    # Each entry holds a value and the link to it: a pair of the parent's
    # link and the key, so the path is built only for a value it reports.
    pending: list[tuple[Any, Any]] = [(value, None)]
    while pending:
        item, link = pending.pop()
        if isinstance(item, Decimal):
            if not request_decimal_in_range(item):
                return _path(link)
            continue
        # A value held in several places is read once. Only objects the
        # walk read into are recorded, and each is held until the walk (or
        # the shared scope) ends, so no other value can have its id.
        key = id(item)
        if key in walked or (shared is not None and key in shared):
            continue
        children = _children(item)
        if children is None:
            continue
        walked[key] = item
        # Pushed in reverse, so the first field or item is read first and
        # the reported path is the first in order. Text and numbers, the
        # most common values, hold nothing to read and are not pushed.
        pending.extend((child, (link, name)) for name, child in reversed(children) if type(child) not in _PLAIN_TYPES)
    # Only a walk that read everything may let later walks skip its objects.
    if record is not None:
        record.objects.update(walked)
        record.walks += 1
        record.last_root = value
    return None


def _path(link: Any) -> tuple[Any, ...]:
    """Turn the chain of ``(parent_link, key)`` pairs into the keys from the walk's start."""
    parts: list[Any] = []
    while link is not None:
        link, name = link
        # A list index stays a number; any other dict key is reported as text.
        parts.append(name if name is None or type(name) is int else str(name))
    parts.reverse()
    return tuple(parts)


def _children(item: Any) -> list[tuple[Any, Any]] | None:
    """Return the ``(key, value)`` pairs inside ``item``, or ``None`` when the walk does not read into it."""
    if type(item) in _PLAIN_TYPES:
        return None
    if isinstance(item, Mapping):
        # A key can hold a Decimal too (`dict[Decimal, int]`, or a tuple key
        # Pydantic parsed from JSON text), so keys are read like values and
        # reported at the dict's own path. Text keys are skipped here.
        pairs: list[tuple[Any, Any]] = [(None, key) for key in item if type(key) not in _PLAIN_TYPES]
        pairs.extend(item.items())
        return pairs
    if isinstance(item, (list, tuple, deque)):
        return list(enumerate(item))
    if isinstance(item, (set, frozenset)):
        # A set has no order and no index to report, so every item is
        # reported at the set's own path.
        return [(None, child) for child in item]
    if is_dataclass(item) and not isinstance(item, type):
        # By field, since a dataclass with `slots=True` has no `__dict__`;
        # an `init=False` field may still be unset.
        return [(field.name, getattr(item, field.name)) for field in fields(item) if hasattr(item, field.name)]
    item_type = type(item)
    model_fields = getattr(item_type, "__pydantic_fields__", None)
    if isinstance(model_fields, Mapping):
        # A Pydantic v2 model: its fields under the names the request used,
        # then any extra values the model allows (`extra="allow"`), which
        # come from the request too. A RootModel's one field has no name
        # in the request.
        is_root = bool(getattr(item_type, "__pydantic_root_model__", False))
        pairs = [
            (None if is_root else _request_name(name, info), getattr(item, name))
            for name, info in model_fields.items()
            if hasattr(item, name)
        ]
        extra = getattr(item, "__pydantic_extra__", None)
        if isinstance(extra, Mapping):
            pairs.extend(extra.items())
        return pairs
    v1_fields = getattr(item_type, "__fields__", None)
    if isinstance(v1_fields, Mapping) and any(base.__module__.startswith("pydantic") for base in item_type.__mro__):
        # A Pydantic v1 model, which a v1 State may hold, keeps its fields
        # in `__fields__`, each with the name the request used as `alias`.
        return [
            (getattr(info, "alias", None) or name, getattr(item, name))
            for name, info in v1_fields.items()
            if hasattr(item, name)
        ]
    if item_type.__module__.startswith("pydantic") and callable(getattr(item, "get_secret_value", None)):
        # `pydantic.Secret[Decimal]` hides its value from printing, not from
        # a template that unwraps it.
        return [(None, item.get_secret_value())]
    return None


def _request_name(name: str, info: Any) -> str:
    """Return the name a request uses for a Pydantic v2 field, so the error sits where the form shows it."""
    for candidate in (getattr(info, "validation_alias", None), getattr(info, "alias", None)):
        if isinstance(candidate, str):
            return candidate
    return name
