"""
Check event data and State writes against a Pydantic class with a copy of its validator.

Before a handler runs, Citry checks the call's data against the handler's
``data`` class, and a browser write to a Pydantic State is checked against the
State class. Citry limits the work it spends on data that fails: each list and
dict stops at its first bad item, and a validation stops once it holds too
many errors or has spent its request's work budget.

This module builds, once per Pydantic class, a second validator from the
class's own core schema (the dict that tells pydantic-core how to check the
class). The result is an instance of the same class, built by the same schema,
so values, validators and ``model_fields_set`` behave as with the class's own
validator. The copy differs in these ways:

1. Every collection that has Pydantic's ``fail_fast`` setting stops at its
   first bad item. Inside a wrap validator, which may read every error and
   retry, collections keep reading every item, and each item is counted
   instead. Inside ``Json[...]`` below a wrap validator, only items that
   JSON and Python read alike (numbers, strings, booleans, nulls) can be
   counted one by one, and the text as a whole is counted as it fails,
   before the wrap validator sees its errors. Each extra key of an object
   whose class gives extra keys a type is counted the same way, since
   Pydantic checks them all before the object returns.
2. Every object (model, dataclass, TypedDict) is wrapped in a small Python
   function. When the object fails, the function adds its error count to a
   total for the whole validation, and stops the validation once the total
   passes a limit (1,000 errors, lower when keys or messages are long).
3. Every place where Pydantic can throw errors away and still succeed (a
   union and its members, a default used on error, a custom error, the
   strict attempt of a lax-or-strict pair) is wrapped too, so the errors it
   threw away leave the total again. When such a part passes the limit
   while it runs, only that part fails, with one error, and the node above
   goes on (a union tries its next member). This keeps a valid request
   from being stopped.
4. An object whose class forbids extra keys refuses more than 100 undeclared
   keys with one error, before Pydantic writes an error for each.
5. Where a recursive definition (a named schema that can lead back to
   itself, such as a model that holds a list of itself) may be checked more
   than once for the same value, by the members of a union, a wrap
   validator, or a lax-or-strict pair, each check spends from the request's
   work budget (see ``WorkBudget``), and a check that parses text inside
   one spends for its characters each time it runs (see
   ``_text_spending``). Citry's own check of a plain class or dataclass
   spends the same way for a union inside another union, and a Pydantic
   class it checks there uses a copy whose text checks spend (see
   ``repeated_checks``). The validation stops once the budget, or the
   request's CPU time for checks, is spent. The budget belongs to the
   whole request.

When a schema cannot produce many errors at all (no recursion, no extra keys,
a fixed and small worst case), the copy gets only the ``fail_fast`` change and
no wrappers, so a valid request costs what it costs with the class's own
validator.

A ``json`` node (``Json[...]``) hands the schema below it JSON values, and a
strict model there refuses Python objects, so below it the copy keeps
Pydantic's own nodes until a wrap validator, below which pydantic-core passes
Python objects anyway. A State that Citry reads as JSON is read with a copy
built the same way. A definition reached from both kinds of place gets one
copy for each. When a part there could still make many errors (see
``_Schema.unbounded_reason``), Citry refuses the class: when the component
class is defined if it can, and otherwise at the first call.

Pydantic's ``PydanticOmit`` and ``PydanticUseDefault`` signals reach the node
that handles them through every wrapper unchanged (see ``_signal``).

The copy needs ``SchemaValidator(..., _use_prebuilt=False)``, from Pydantic
2.13.0, so that nested models are rebuilt inside the copy instead of reusing
their own validators.
"""

from __future__ import annotations

import contextlib
import contextvars
import functools
import inspect
import os
import re
import sys
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NamedTuple, cast
from weakref import WeakKeyDictionary

from citry.util.logger import logger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# Pydantic is optional: without it no class reaches this module.
try:
    import pydantic_core
    from pydantic_core import core_schema as _core_schema
except ImportError:  # pragma: no cover - exercised only without Pydantic installed
    pydantic_core = None  # type: ignore[assignment]
    _core_schema = None  # type: ignore[assignment]


################################################
# LIMITS
################################################

# The most errors one validation may keep before Citry stops it. An ordinary
# form never comes near this.
MAX_ERRORS = 1000
# The limit never drops below this, however long the keys are, so a bad
# request with one long key and a few errors still gets its field messages
# instead of the single message.
MIN_ERRORS = 8
# An object that forbids extra keys refuses more undeclared keys than this
# with one error instead of one each.
MAX_EXTRA_KEYS = 100
# The work one request may spend checking values again, in steps (see
# `WorkBudget.spend_on`). Valid recursive data of ordinary depth fits.
WORK_BUDGET = 60_000_000
# The CPU time one request may spend inside Citry's checks, in seconds,
# read before each check that may run again. The steps above are the main
# limit; this one stops a request once its checks that may run again have
# used a fixed amount of CPU time, whatever the steps say.
WORK_SECONDS = 1.0
# The clock behind WORK_SECONDS: the CPU time of the calling thread. On
# Windows it moves in steps of about 15.6 ms, so a check that runs for less
# than one step can read no time at all, and the time counted for each check
# can be off by up to one step. It is a module-level name so that a test can
# replace it with a clock it moves by hand.
cpu_clock = time.thread_time
# What one more check of a list or object costs besides the values inside it,
# in steps: the Python wrappers around it run on every check.
ENTRY_STEPS = 32
# What each list or dict inside a value costs to check again, in steps:
# pydantic-core builds a new one each time. A member that fails at once is
# charged for the whole value too, so this stays low enough that a large
# valid leaf still fits a few levels.
CONTAINER_STEPS = 2
# Steps are charged for text in steps per this many characters, so a plain
# string costs one step per 64 characters.
_TEXT_PER_STEP = 64
# How many steps per 64 characters one check of a string costs, by the kind
# of schema that reads it (see `_Schema.text_steps`).
TEXT_STEPS = {
    "plain": 1,
    "decimal": 16,
    "decimal-digits": 32,
    "fraction": 128,
    "url": 256,
    "python-re": 128,
    "function": 128,
    "json": 192,
}
# Each check of JSON text at least this long costs `_LONG_JSON_TEXT_STEPS`
# per 64 characters instead.
_LONG_JSON_TEXT = 64 * 1024
_LONG_JSON_TEXT_STEPS = 1536
# What one call of a Citry wrapper costs, in steps, when it runs inside a
# check that may run again.
PYTHON_CALL_STEPS = 64
# Citry's own check of a plain class or dataclass runs in Python, so each
# value it checks again costs this many steps.
CITRY_CHECK_STEPS = 16
# What the kept errors may cost in text. Each path character counts four
# times: pydantic-core keeps a UTF-8 copy, Python makes a string for each
# error, Citry writes the path text, and the response repeats it.
ERROR_TEXT_BUDGET = 16 * 1024 * 1024
_PATH_COPIES = 4
# About what one error costs besides its path and message text.
_ERROR_OVERHEAD = 400
# The most path parts the kept errors may hold in all, so that a deep
# payload keeps fewer errors.
_PATH_PARTS_BUDGET = 50_000
# A schema whose worst case is at most this many errors needs no wrappers,
# as long as no key the payload chooses lands in an error's path.
_FIXED_ERRORS_WITHOUT_WRAPPERS = MAX_ERRORS // 4

TOO_MANY_ERRORS_MESSAGE = "This data has too many errors to check. Correct it and send it again."
TOO_DEEP_MESSAGE = "This data is nested too deeply to check. Send it with fewer levels of nesting."
TOO_MUCH_WORK_MESSAGE = (
    "This data is too large or nested too deeply to check. Send less data, or data with fewer levels of nesting."
)
TOO_SLOW_MESSAGE = "This data took too long to check. Send less data, or data with fewer levels of nesting."
NOT_CHECKABLE_MESSAGE = "The value could not be checked."
REQUIRED_PYDANTIC = "2.13.0"
# What the log says when Citry refuses every call to a class, with the fix.
_OLD_PYDANTIC_REFUSAL = f"Events needs Pydantic {REQUIRED_PYDANTIC} or newer for Pydantic classes. Upgrade Pydantic."
_NOT_COPIED_REFUSAL = (
    "Citry could not copy the class's validator; the traceback logged before this names the cause. Check that"
    " the class builds with the installed Pydantic, and report the traceback as a bug."
)


class ValidationTooCostly(Exception):
    """
    Stop a validation from inside Pydantic.

    It is not a ``ValueError``, so pydantic-core does not record it as a
    field error: it stops at once and drops every error it holds, and the
    exception reaches the caller of the validation.

    Attributes:
        reason: ``"errors"`` when the validation kept too many errors,
            ``"work"`` when the request spent its work budget, ``"time"``
            when the request's checks used up their CPU time, ``"depth"``
            when the data nests deeper than Python can follow.

    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason

    @property
    def message(self) -> str:
        """The field message for the call that was stopped."""
        if self.reason == "errors":
            return TOO_MANY_ERRORS_MESSAGE
        # Running out of time can happen on a busy server to data that is
        # large rather than deep, so it says so instead of blaming nesting.
        if self.reason == "time":
            return TOO_SLOW_MESSAGE
        # The work budget runs out for a wide value too, not only a deep one.
        return TOO_MUCH_WORK_MESSAGE if self.reason == "work" else TOO_DEEP_MESSAGE


################################################
# THE REQUEST'S WORK BUDGET
################################################


class WorkBudget:
    """The work one request may spend checking values again, and the results it keeps so it does not repeat work."""

    __slots__ = (
        "_clocks",
        "_recent",
        "_seconds_left",
        "_sizes",
        "active",
        "left",
        "restores",
        "union_depth",
        "v1_parses",
    )

    def __init__(self, amount: int = WORK_BUDGET, seconds: float | None = None) -> None:
        self.left = amount
        # How many of Citry's own union checks are running inside each other.
        # Only a union inside another union's attempt can repeat work.
        self.union_depth = 0
        # An asyncio task or a thread started during the request copies the
        # request's context, and so this budget. Once the request ends the
        # budget is closed, so later work in that task gets a budget of its own.
        self.active = True
        # The measure of each large list and dict, by id (see `measure`). The
        # value is kept too, so that its id cannot pass to another object
        # while the request runs.
        self._sizes: dict[int, tuple[Any, Measure]] = {}
        # The measures of the last values measured that were not kept, read
        # again by the members of a union and by the levels of a chain (see
        # `measure`). The value read longest ago is dropped first.
        self._recent: OrderedDict[int, tuple[Any, Measure]] = OrderedDict()
        # The States the request restored, by class and the hash of their
        # values' JSON text, so its calls can reuse a restore (see
        # `restore_state` in `state.py`).
        self.restores: OrderedDict[tuple[type, bytes], Any] = OrderedDict()
        # The Pydantic v1 States the request parsed from JSON text, by class
        # and the hash of the text, so the reads of one written State after
        # its write check reuse one parse (see `_parse_v1` in `state.py`).
        self.v1_parses: OrderedDict[tuple[type, bytes], Any] = OrderedDict()
        # The CPU time left, and for each thread running a check, when the
        # outermost check started on that thread's clock and how many checks
        # run inside each other. Only time inside checks counts: between
        # them an async server runs other requests on the same thread. Each
        # thread keeps its own start, because each thread has its own clock.
        self._seconds_left = WORK_SECONDS if seconds is None else seconds
        self._clocks: dict[int, list[Any]] = {}

    def spend(self, steps: int = 1) -> None:
        """Spend ``steps`` steps, and stop the validation once they are gone."""
        self.left -= steps
        if self.left < 0:
            raise ValidationTooCostly("work")

    def spend_time(self, steps: int) -> None:
        """Spend ``steps`` steps before a check that may run long, and stop once the steps or CPU time are gone."""
        self.spend(steps)
        # Read the clock only here, before each check that may run again,
        # not at every wrapper call: reading it costs about a tenth of a call.
        clock = self._clocks.get(threading.get_ident())
        if clock is not None and cpu_clock() - clock[0] > self._seconds_left:
            raise ValidationTooCostly("time")

    def spend_on(self, value: Any, times: int = 1, container_values: int = CONTAINER_STEPS) -> None:
        """
        Spend for checking ``value`` ``times`` more times: ``ENTRY_STEPS`` plus one step per value inside it.

        Each list or dict inside counts as ``container_values`` values, since
        a check builds a new one. Text costs one step per 64 characters; a
        check that parses it spends more where it runs (see
        ``_text_spending``). A number, a boolean or ``None`` costs nothing
        here: checking it again repeats no work below it, and the check of
        the list or object that holds it is charged for it already.
        """
        if isinstance(value, (str, bytes)):
            self.spend_time(times * (len(value) // _TEXT_PER_STEP))
        elif isinstance(value, _CONTAINERS):
            found = self.measure(value)
            steps = found.values + found.containers * container_values + found.characters // _TEXT_PER_STEP
            self.spend_time(times * (ENTRY_STEPS + steps))
        else:
            self.spend_time(0)

    def measure(self, value: Any) -> Measure:
        """
        Return how many values, lists and dicts, and characters of text ``value`` holds, itself and keys included.

        A check runs at every level of a tree, so measures are kept for the
        rest of the request, and a later walk reads a kept measure instead
        of walking that part again. A list or dict keeps its measure when
        it holds at least ``_MEASURED_SIZE`` items, or when the values,
        lists and dicts it holds outside its largest direct child add up
        to at least ``_BRANCH_SIZE``. So a list that splits into two large
        parts (a fork) is kept, and so is each level of a comb, where every
        level holds the next level and many small lists beside it. A chain
        of one-item lists is not kept, since each list holds only one more
        container than the list inside it.

        A kept list or dict either has a kept measure somewhere inside two
        or more of its direct children, or holds at least
        ``_BRANCH_SIZE`` values, lists and dicts that no kept measure below
        it covers. Lists of the second kind cover separate parts of the
        data, and there are no more lists of the first kind than lists of
        the second kind below them, so the request keeps at most one
        measure per ``_BRANCH_SIZE / 2`` values, lists and dicts it
        measures, whatever their shape.

        A value that is not kept goes into a store of the last
        ``_RECENT_SIZE`` such values instead, when it is the value measured
        at the top or holds at least ``_BRANCH_SIZE`` values, lists and
        dicts. The members of a union check the same value one after
        another, a union inside a union checks the levels below it again
        on each attempt, and the check of each list in a chain of one-item
        lists measures the rest of the chain, so those values are read from
        the store. The store has a fixed size, so a payload of many small
        values or long chains does not grow it.
        """
        if not isinstance(value, _CONTAINERS):
            return Measure(1, 0, len(value) if isinstance(value, (str, bytes)) else 0)
        sizes = self._sizes
        recent = self._recent
        known = sizes.get(id(value))
        if known is None:
            known = recent.get(id(value))
            if known is not None:
                # The store drops the value read longest ago first, so a
                # value read again moves to the end. A thread that shares
                # the request may have dropped it since the read above.
                with suppress(KeyError):
                    recent.move_to_end(id(value))
        if known is not None and known[0] is value:
            return known[1]
        # Each open list or dict is a frame: the value, its items still to
        # read, the values, lists and dicts, and characters counted so far,
        # whether it is a dict, and the values, lists and dicts of its
        # largest direct child (see below). An explicit stack, because a
        # value can nest deeper than Python's recursion limit.
        open_ids = {id(value)}
        stack: list[list[Any]] = [_frame(value)]
        while True:
            frame = stack[-1]
            child = None
            for entry in frame[1]:
                if frame[5]:
                    # A dict entry: its key counts as a value, with its text.
                    key, item = entry
                    frame[2] += 1
                    if isinstance(key, (str, bytes)):
                        frame[4] += len(key)
                else:
                    item = entry
                if not isinstance(item, _CONTAINERS):
                    frame[2] += 1
                    if isinstance(item, (str, bytes)):
                        frame[4] += len(item)
                    continue
                known = sizes.get(id(item)) or recent.get(id(item))
                if known is not None and known[0] is item:
                    found = known[1]
                    frame[2] += found.values
                    frame[3] += found.containers
                    frame[4] += found.characters
                    frame[6] = max(frame[6], found.values + found.containers)
                elif id(item) in open_ids:
                    # A value a validator built can hold itself; the inner
                    # copy then counts as one value.
                    frame[2] += 1
                else:
                    child = item
                    break
            if child is not None:
                # Read the child first; this frame's loop resumes after it.
                open_ids.add(id(child))
                stack.append(_frame(child))
                continue
            node, _, values, containers, characters, _, largest = stack.pop()
            open_ids.discard(id(node))
            found = Measure(values, containers, characters)
            # Keep a list or dict that holds many items, or enough beside
            # its largest child: a later walk then stops here. A chain of
            # one-item lists is not kept, because it would add one entry
            # per list however little each holds. The store of fixed size
            # takes the top value, which a union's members measure again,
            # and the large lists of a chain, which the checks of the lists
            # above them measure again. A small list inside costs about as
            # much to walk again as to look up.
            if len(node) >= _MEASURED_SIZE or values + containers - largest >= _BRANCH_SIZE:
                sizes[id(node)] = (node, found)
            elif not stack or values + containers >= _BRANCH_SIZE:
                recent[id(node)] = (node, found)
                # Another thread may empty the store between the two steps.
                with suppress(KeyError):
                    while len(recent) > _RECENT_SIZE:
                        recent.popitem(last=False)
            if not stack:
                return found
            parent = stack[-1]
            parent[2] += values
            parent[3] += containers
            parent[4] += characters
            parent[6] = max(parent[6], values + containers)

    def clock_on(self) -> None:
        """Start counting this thread's CPU time against the budget, unless a check is already counting it."""
        thread = threading.get_ident()
        clock = self._clocks.get(thread)
        if clock is None:
            self._clocks[thread] = [cpu_clock(), 1]
        else:
            clock[1] += 1

    def clock_off(self) -> None:
        """Stop counting CPU time once the outermost check ends, and keep what is left for the request's next check."""
        thread = threading.get_ident()
        clock = self._clocks.get(thread)
        if clock is None:
            return
        clock[1] -= 1
        if clock[1] == 0:
            self._seconds_left -= cpu_clock() - clock[0]
            del self._clocks[thread]

    def out_of_time(self) -> bool:
        """Return whether the request's CPU time is used up, counting what the check on this thread has used so far."""
        clock = self._clocks.get(threading.get_ident())
        used = cpu_clock() - clock[0] if clock is not None else 0.0
        return used > self._seconds_left

    def skip_time(self, seconds: float) -> None:
        """Leave ``seconds`` of CPU time just spent on this thread off the running check's clock."""
        clock = self._clocks.get(threading.get_ident())
        if clock is not None:
            # Moving the start forward is the same as pausing the clock.
            clock[0] += seconds

    def close(self) -> None:
        """Drop the measures, restored States and parsed States kept for the request once it ends."""
        self._sizes = {}
        self._recent = OrderedDict()
        self.restores = OrderedDict()
        self.v1_parses = OrderedDict()


# The values a check can descend into, and so the ones whose size is measured.
_CONTAINERS = (dict, list, tuple, set, frozenset)
# A list or dict that holds at least this many items keeps its measure for
# the rest of the request (see `WorkBudget.measure`).
_MEASURED_SIZE = 64
# A list or dict whose values, lists and dicts outside its largest direct
# child add up to at least this many keeps its measure too. A lower value
# means fewer levels of a tree are walked again and more entries are kept.
_BRANCH_SIZE = 16
# How many measures that are not kept the request still holds, dropping the
# one read longest ago. It covers the levels a union inside a union checks
# again on each attempt, and has a fixed size, so it costs the same memory
# for any payload.
_RECENT_SIZE = 256


class Measure(NamedTuple):
    """What one value holds, as ``WorkBudget.measure`` counts it."""

    # Numbers, strings, booleans, ``None`` and dict keys.
    values: int
    # Lists, dicts and other containers, the value itself included.
    containers: int
    # Characters of text in strings and keys.
    characters: int


def _frame(value: Any) -> list[Any]:
    """Return a new frame for ``WorkBudget.measure``, which counts the container itself."""
    # The last slot holds the size of the largest list or dict the value
    # holds directly.
    if isinstance(value, dict):
        return [value, iter(value.items()), 0, 1, 0, True, 0]
    return [value, iter(value), 0, 1, 0, False, 0]


_REQUEST_WORK: contextvars.ContextVar[WorkBudget | None] = contextvars.ContextVar("citry_events_work", default=None)


@contextmanager
def request_work() -> Iterator[WorkBudget]:
    """
    Give the code inside one work budget, unless an outer request already has one.

    The dispatcher opens it around every call of a request, so 16 calls in
    one request share one budget. ``validate_args`` opens it too, so a direct
    caller is bounded as well.
    """
    current = current_work()
    if current is not None:
        yield current
        return
    budget = WorkBudget()
    token = _REQUEST_WORK.set(budget)
    try:
        yield budget
    finally:
        budget.active = False
        # A task or thread that copied the request's context keeps the budget
        # object alive, so the measures it holds are dropped now.
        budget.close()
        _REQUEST_WORK.reset(token)


@contextmanager
def unbudgeted() -> Iterator[None]:
    """
    Run the code inside with no work budget and its own error count, for values the server wrote.

    A State restore reads the values of a signed (or server-stored) token,
    which the app built or Citry checked when the browser wrote them, so a
    deep tree the app built must restore. The copy still stops each list at
    its first bad item and counts errors, which bounds what a failing
    restore keeps, but no work budget or CPU limit applies.

    A check of the request's data may already be running when this
    starts, as when a write to a dataclass State with a model validator
    builds the whole State after checking its fields. The time spent
    inside does not count toward that check's CPU limit, so later calls in
    the request keep the CPU time that the browser's data had left.
    """
    outer = current_work()
    started = cpu_clock()
    work = _REQUEST_WORK.set(None)
    tally = _TALLY.set(None)
    try:
        yield
    finally:
        _TALLY.reset(tally)
        _REQUEST_WORK.reset(work)
        if outer is not None:
            outer.skip_time(cpu_clock() - started)


def current_work() -> WorkBudget | None:
    """Return the running request's work budget, or ``None`` outside one or after its request ended."""
    budget = _REQUEST_WORK.get()
    return budget if budget is not None and budget.active else None


################################################
# THE VALIDATION'S ERROR TALLY
################################################


class _Tally:
    """The errors one validation still keeps, and its limit, shared by every Pydantic call inside it."""

    __slots__ = (
        "_limit",
        "active",
        "budget",
        "errors",
        "longest_message",
        "member_floor",
        "payload",
        "repeating",
        "strings_hold_keys",
        "values_read",
    )

    def __init__(self, payload: Any) -> None:
        self.errors = 0
        # How many values a Pydantic v1 check has read, so it reads the
        # clock once for every few hundred (see `guarding_pydantic_v1`).
        self.values_read = 0
        # The request's work budget, read once here because every wrapper
        # needs it and a context variable costs a lookup each time.
        self.budget = current_work()
        # How many checks that may run again for the same value (a member of
        # a repeating union, that is, a union whose members may check the same
        # recursive value more than once, or a wrap validator's handler) are
        # running inside each other. Inside one, each Citry wrapper call
        # spends too.
        self.repeating = 0
        # Closed when its validation ends, for the same reason as a work budget.
        self.active = True
        self.payload = payload
        # Whether a schema in this validation reads JSON out of a string, so
        # that a string's whole text can hide keys.
        self.strings_hold_keys = False
        self.longest_message = 0
        self._limit: int | None = None
        # The total when the innermost running member of a repeating union
        # started, or None outside one; see `_discarded_spending`.
        self.member_floor: int | None = None

    def limit(self) -> int:
        """Return the error limit, lowered by long paths and long messages."""
        # Measured on the first failure only, so a valid request never walks
        # its payload for this.
        if self._limit is None:
            length, depth = longest_path(self.payload, strings_hold_keys=self.strings_hold_keys)
            per_error = _PATH_COPIES * length + self.longest_message + _ERROR_OVERHEAD
            by_text = ERROR_TEXT_BUDGET // per_error
            by_depth = _PATH_PARTS_BUDGET // max(depth, 1)
            self._limit = min(MAX_ERRORS, max(MIN_ERRORS, min(by_text, by_depth)))
        return self._limit

    def check(self) -> None:
        """Stop the validation, or the running member of a repeating union, when it keeps too many errors."""
        if self.errors > self.limit() or (
            self.member_floor is not None and self.errors - self.member_floor > _MEMBER_ERRORS
        ):
            raise ValidationTooCostly("errors")


_TALLY: contextvars.ContextVar[_Tally | None] = contextvars.ContextVar("citry_events_tally", default=None)


@contextmanager
def validation_scope(payload: Any) -> Iterator[None]:
    """
    Count errors over everything inside as one validation, unless an outer one is already counting.

    ``validate_args`` opens it around the whole payload, so a Pydantic model
    inside a plain dataclass, called once per list item, shares one total.
    Once the app has loaded ``pydantic.v1``, the validation also has the
    ``pydantic.v1`` hooks in place (see ``guarding_pydantic_v1``), so a v1
    check that runs inside it, even one that a validator of the author
    calls, is counted and stopped.
    """
    if _current_tally() is not None:
        yield
        return
    tally = _Tally(payload)
    token = _TALLY.set(tally)
    # The request's CPU time runs while its checks do.
    budget = tally.budget
    if budget is not None:
        budget.clock_on()
    # A v1 class can exist only once `pydantic.v1` is loaded, so other apps
    # never put the hooks in.
    guard = guarding_pydantic_v1() if "pydantic.v1" in sys.modules else contextlib.nullcontext()
    try:
        with guard:
            yield
    finally:
        if budget is not None:
            budget.clock_off()
        tally.active = False
        _TALLY.reset(token)


def _current_tally() -> _Tally | None:
    tally = _TALLY.get()
    return tally if tally is not None and tally.active else None


def count_errors(count: int = 1) -> None:
    """
    Add errors Citry's own validator recorded to the validation's total, and stop past its limit.

    Citry checks a plain dataclass itself, and a Pydantic dataclass field by
    field before Pydantic builds it, so those messages share the total with
    every Pydantic call in the same validation.
    """
    tally = _current_tally()
    if tally is not None:
        tally.errors += count
        tally.check()


@contextmanager
def repeated_checks() -> Iterator[None]:
    """
    Run checks that may run again for the same value, so the wrappers inside spend from the work budget.

    Citry's own union check runs a union inside another union's attempt in
    this, since each member of the outer union may check that value again.
    A Pydantic class checked there uses the copy that spends for text its
    checks parse (see ``checker_for``).
    """
    tally = _current_tally()
    if tally is None:
        yield
        return
    tally.repeating += 1
    try:
        yield
    finally:
        tally.repeating -= 1


def in_repeated_check() -> bool:
    """Whether the running check may run again for the same value (see ``repeated_checks``)."""
    tally = _current_tally()
    return tally is not None and tally.repeating > 0


@contextmanager
def discarded_errors() -> Iterator[None]:
    """
    Run one attempt whose errors the caller throws away, so they leave the total again.

    Citry's own union check runs each member inside this. A stop for too
    many errors still goes up to the caller, which treats the attempt as a
    failure: the attempt is dropped with all it held, and the next member runs.
    """
    tally = _current_tally()
    before = tally.errors if tally is not None else 0
    try:
        yield
    finally:
        if tally is not None:
            tally.errors = before


def longest_path(payload: Any, *, strings_hold_keys: bool) -> tuple[int, int]:
    """
    Return the longest chain of keys and list indexes in ``payload``, in characters, and its deepest depth.

    With ``strings_hold_keys`` (a schema reads JSON out of strings), a string
    can hide keys, so its whole length counts too. The walk uses its own
    stack, because a payload can be deeper than Python's recursion limit.
    """
    longest = 0
    deepest = 0

    def reach(value: Any, length: int, depth: int) -> Iterator[tuple[Any, int]] | None:
        # Count one value's own text, and return its items with their path
        # lengths when it has any.
        nonlocal longest, deepest
        if isinstance(value, dict):
            deepest = max(deepest, depth + 1)
            # A key that is not text costs about what a long number does.
            return ((item, length + (len(key) if type(key) is str else 20) + 1) for key, item in value.items())
        if isinstance(value, (list, tuple)):
            deepest = max(deepest, depth + 1)
            item_length = length + len(str(len(value))) + 1
            longest = max(longest, item_length)
            return ((item, item_length) for item in value)
        if strings_hold_keys and type(value) is str:
            longest = max(longest, length + len(value))
            # Text read as JSON can nest as deep as it has brackets.
            deepest = max(deepest, depth + value.count("[") + value.count("{"))
        return None

    # One frame per open list or dict, so the walk holds no more than the
    # current path, however many items the payload has.
    stack: list[tuple[Iterator[tuple[Any, int]], int]] = []
    items = reach(payload, 0, 0)
    if items is not None:
        stack.append((items, 1))
    while stack:
        items, depth = stack[-1]
        entry = next(items, None)
        if entry is None:
            stack.pop()
            continue
        item, length = entry
        longest = max(longest, length)
        inner = reach(item, length, depth)
        if inner is not None:
            stack.append((inner, depth + 1))
    return longest, deepest


################################################
# THE WRAPPERS PUT INTO THE COPY
################################################


# The texts pydantic-core gives the SchemaError it raises when a
# PydanticOmit or PydanticUseDefault signal leaves a wrap validator's handler.
_OMIT_TEXT = "Uncaught Omit error"
_USE_DEFAULT_TEXT = "Uncaught `PydanticUseDefault` exception"


def _signal(err: Exception) -> Exception:
    """
    Return the signal a Citry wrapper must raise for a ``SchemaError`` from its handler, or ``err`` itself.

    A node below may drop a value (``PydanticOmit``, from a default with
    ``on_error="omit"`` or a validator) or ask for the field's default
    (``PydanticUseDefault``). pydantic-core turns either into a
    ``SchemaError`` when it leaves a wrap validator's handler, so a Citry
    wrapper between the node and the list or default that handles it would
    refuse valid data. The wrapper raises the signal again instead.

    Only a ``SchemaError`` raised by the handler call itself is such a
    signal. One that passed through the author's own wrap validator first
    has that function's frame in its traceback, and the class's own
    validator raises it to the caller too, so it is left as it is.
    """
    traceback = err.__traceback__
    if traceback is None or traceback.tb_next is not None:
        return err
    text = str(err)
    if text.startswith(_OMIT_TEXT):
        return pydantic_core.PydanticOmit()
    if text.startswith(_USE_DEFAULT_TEXT):
        return pydantic_core.PydanticUseDefault()
    return err


def _counted(value: Any, handler: Any) -> Any:
    """Check one object, and keep the validation's error total in step with what it keeps."""
    tally = _current_tally()
    if tally is None:
        try:
            return handler(value)
        except pydantic_core.SchemaError as err:
            raise _signal(err) from None
    if tally.repeating and tally.budget is not None:
        tally.budget.spend(PYTHON_CALL_STEPS)
    before = tally.errors
    try:
        result = handler(value)
    except pydantic_core.ValidationError as err:
        # The object's own error count replaces whatever wrappers inside it
        # added, so each error Pydantic still keeps counts once.
        tally.errors = before + err.error_count()
        tally.check()
        raise
    except pydantic_core.SchemaError as err:
        # The node chose to drop the value or use its default: nothing is kept.
        tally.errors = before
        raise _signal(err) from None
    # A success throws away any errors made below it, for example by a union.
    tally.errors = before
    return result


def _discarded(value: Any, handler: Any) -> Any:
    """
    Check a part whose errors the node above may throw away, so they leave the total.

    The part's errors still count while it runs. When they pass the limit,
    only this part stops: it fails with one error, and the node above goes
    on as it would after any failure (a union tries its next member, a
    default is used). So a union whose first member fails on many keys
    still accepts the value through another member, as the class does.
    """
    tally = _current_tally()
    if tally is None:
        try:
            return handler(value)
        except pydantic_core.SchemaError as err:
            raise _signal(err) from None
    if tally.repeating and tally.budget is not None:
        tally.budget.spend(PYTHON_CALL_STEPS)
    before = tally.errors
    try:
        return handler(value)
    except ValidationTooCostly as stop:
        # A spent work budget stops the whole request: trying the next member
        # would only spend more.
        if stop.reason != "errors":
            raise
        raise pydantic_core.PydanticCustomError("too_many_errors", TOO_MANY_ERRORS_MESSAGE) from None
    except pydantic_core.SchemaError as err:
        raise _signal(err) from None
    finally:
        tally.errors = before


def _spending(inner: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
    """Return a wrapper that spends from the work budget for the value it checks, then calls ``inner``."""

    def spend(value: Any, handler: Any) -> Any:
        tally = _current_tally()
        if tally is None or tally.budget is None:
            return inner(value, handler)
        tally.budget.spend_on(value)
        tally.repeating += 1
        try:
            return inner(value, handler)
        except pydantic_core.ValidationError as err:
            # Each wrapper above copies the errors handed up, as for a union member.
            tally.budget.spend(err.error_count() * _STEPS_PER_ERROR)
            raise
        finally:
            tally.repeating -= 1

    return spend


# A failed member of a union that can check a recursive value more than once
# stops once it holds more errors than this, and spends this many steps for
# each error it hands up, which every wrapper above copies. A valid tree's
# members fail on a few fields each, so the limit does not apply to them.
_MEMBER_ERRORS = 64
_STEPS_PER_ERROR = 64


def _discarded_spending(value: Any, handler: Any) -> Any:
    """
    Check a member of a repeating union like ``_discarded``, spending for the value and its errors.

    A repeating union is one whose members may check the same recursive
    value more than once (see ``_Schema.repeats_recursion``).
    """
    # The same steps as `_discarded`, written out: this runs at every level
    # of a recursive tree, where one more Python call per member shows.
    tally = _current_tally()
    if tally is None:
        try:
            return handler(value)
        except pydantic_core.SchemaError as err:
            raise _signal(err) from None
    budget = tally.budget
    if budget is not None:
        budget.spend_on(value)
    before = tally.errors
    outer_floor = tally.member_floor
    tally.member_floor = before
    tally.repeating += 1
    try:
        return handler(value)
    except pydantic_core.ValidationError as err:
        if budget is not None:
            budget.spend(err.error_count() * _STEPS_PER_ERROR)
        raise
    except ValidationTooCostly as stop:
        if stop.reason != "errors":
            raise
        raise pydantic_core.PydanticCustomError("too_many_errors", TOO_MANY_ERRORS_MESSAGE) from None
    except pydantic_core.SchemaError as err:
        raise _signal(err) from None
    finally:
        tally.errors = before
        tally.member_floor = outer_floor
        tally.repeating -= 1


def _text_spending(text_steps: int, long_text_steps: int = 0) -> Callable[[Any, Any], Any]:
    """
    Return a wrapper for a check that parses text, spending ``text_steps`` per 64 characters it reads.

    With ``long_text_steps``, a string of at least ``_LONG_JSON_TEXT``
    characters spends at that rate instead.

    It spends only inside a check that may run again (``_Tally.repeating``),
    as the wrappers above it do: for its own call, and for the text, since
    they charged the values already. Elsewhere the check costs what it
    costs with the class's own validator.
    """

    def charge(value: Any, handler: Any) -> Any:
        tally = _current_tally()
        if tally is not None and tally.repeating and tally.budget is not None:
            # This wrapper is a Python call too, as `_counted` charges.
            tally.budget.spend(PYTHON_CALL_STEPS)
            if isinstance(value, (str, bytes)):
                rate = long_text_steps if long_text_steps and len(value) >= _LONG_JSON_TEXT else text_steps
                tally.budget.spend_time(len(value) * rate // _TEXT_PER_STEP)
            elif isinstance(value, _CONTAINERS):
                # An author's function may read every string inside.
                tally.budget.spend_time(tally.budget.measure(value).characters * text_steps // _TEXT_PER_STEP)
        try:
            return handler(value)
        except pydantic_core.SchemaError as err:
            raise _signal(err) from None

    return charge


def _passed_through(value: Any, handler: Any) -> Any:
    try:
        return handler(value)
    except pydantic_core.SchemaError as err:
        raise _signal(err) from None


def _extras_guard(names: frozenset[str], inner: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
    """Return a wrapper that refuses an object with many keys its class forbids, before Pydantic reports each."""
    allowed = len(names) + MAX_EXTRA_KEYS

    def guard(value: Any, handler: Any) -> Any:
        # Only a dict this large can hold more undeclared keys than the limit.
        if type(value) is dict and len(value) > allowed:
            extra = sum(1 for key in value if key not in names)
            if extra > MAX_EXTRA_KEYS:
                raise pydantic_core.PydanticCustomError(
                    "too_many_extra_fields",
                    "This object has {count} fields that are not declared; at most {limit} are allowed.",
                    {"count": extra, "limit": MAX_EXTRA_KEYS},
                )
        return inner(value, handler)

    return guard


################################################
# READING THE SCHEMA
################################################


def _fail_fast_types() -> frozenset[str]:
    """Read from pydantic-core which schema types accept ``fail_fast``, so a new collection type is picked up."""
    found = set()
    for value in vars(_core_schema).copy().values():
        annotations = getattr(value, "__annotations__", None)
        if isinstance(value, type) and annotations and "fail_fast" in annotations and "type" in annotations:
            match = re.search(r"Literal\[['\"]([a-z-]+)['\"]\]", str(annotations["type"]))
            if match:
                found.add(match.group(1))
    return frozenset(found)


def _mapping_types() -> frozenset[str]:
    """Read which schema types hold keys the payload chooses, which land in error paths."""
    found = set()
    for value in vars(_core_schema).copy().values():
        annotations = getattr(value, "__annotations__", None)
        if isinstance(value, type) and annotations and "keys_schema" in annotations and "type" in annotations:
            match = re.search(r"Literal\[['\"]([a-z-]+)['\"]\]", str(annotations["type"]))
            if match:
                found.add(match.group(1))
    return frozenset(found)


_FAIL_FAST_TYPES = _fail_fast_types() if _core_schema is not None else frozenset()
_MAPPING_TYPES = _mapping_types() if _core_schema is not None else frozenset()
# The keys of a collection schema that hold the schema of each item.
_ITEM_KEYS = ("items_schema", "keys_schema", "values_schema")
# Schemas that check one value and report at most one error for it.
_SCALAR_TYPES = frozenset({
    "none", "bool", "int", "float", "decimal", "str", "bytes", "date", "time", "datetime", "timedelta",
    "literal", "enum", "uuid", "url", "multi-host-url", "complex", "is-instance", "is-subclass", "callable", "any",
    "missing-sentinel", "fraction", "ellipsis",
})  # fmt: skip
# Which rate of `TEXT_STEPS` each scalar check reads a string at. A string
# with a pattern can also read at the "python-re" rate (see `_Schema.text_steps`).
_SCALAR_TEXT = {
    "none": "plain", "bool": "plain", "int": "plain", "float": "plain", "decimal": "decimal", "str": "plain",
    "bytes": "plain", "date": "plain", "time": "plain", "datetime": "plain", "timedelta": "plain",
    "literal": "plain", "enum": "plain", "uuid": "plain", "url": "url", "multi-host-url": "url",
    "complex": "plain", "is-instance": "plain", "is-subclass": "plain", "callable": "plain", "any": "plain",
    "missing-sentinel": "plain", "fraction": "fraction", "ellipsis": "plain",
}  # fmt: skip
# The schema types that run a function on the value, which may be the author's.
_FUNCTION_TYPES = frozenset({"function-before", "function-after", "function-plain", "function-wrap"})
# Scalar schema types whose checked value holds no text.
_TEXTLESS_TYPES = frozenset({
    "none", "bool", "int", "float", "decimal", "date", "time", "datetime", "timedelta", "uuid", "complex",
    "fraction",
})  # fmt: skip
# Schema types a ``strict`` flag does not change for a value that came from
# JSON: JSON writes these natively, so strict Python and JSON read them alike.
_JSON_NATIVE_TYPES = frozenset({"str", "int", "float", "bool", "none", "list", "dict", "literal", "any"})
# What kind of JSON value a schema can descend into, to tell which union
# members can read the same value.
_OBJECT = frozenset({"object"})
_ARRAY = frozenset({"array"})
_LEAF = frozenset({"leaf"})
_ANY = _OBJECT | _ARRAY | _LEAF
_OBJECT_TYPES = frozenset({"model", "dataclass", "typed-dict", "model-fields", "dataclass-args"})
_ARRAY_TYPES = frozenset({"list", "tuple", "set", "frozenset", "deque", "generator"})


def _overlap(kinds: list[frozenset[str]]) -> bool:
    """Whether two of these sets share a kind of value other than a leaf, which no member descends into."""
    seen: set[str] = set()
    for found in kinds:
        descending = found - _LEAF
        if seen & descending:
            return True
        seen |= descending
    return False


# Keys of a schema node whose values are not schemas to check: the author's
# metadata, dumping, default values, functions, classes, and the schema used
# only to write a JSON Schema.
_NOT_SCHEMA_KEYS = frozenset({
    "metadata", "serialization", "default", "default_factory", "function", "cls", "config", "expected",
    "members", "custom_error_context", "json_schema_input_schema", "computed_fields", "discriminator",
    "post_init", "ref",
})  # fmt: skip


def _kind(node: Any) -> str | None:
    # A `fields` mapping can hold a field named "type" whose value is a dict.
    if type(node) is not dict:
        return None
    kind = node.get("type")
    return kind if isinstance(kind, str) else None


def _children(node: Any) -> list[Any]:
    if type(node) is dict:
        return [value for key, value in node.items() if key not in _NOT_SCHEMA_KEYS]
    if type(node) in (list, tuple):
        return list(node)
    return []


def _definitions(root: Any) -> dict[str, Any]:
    """Return every schema node that carries a ``ref``, by that ref."""
    found: dict[str, Any] = {}
    stack: list[Any] = [root]
    seen: set[int] = set()
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        ref = node.get("ref") if type(node) is dict else None
        if isinstance(ref, str) and _kind(node) not in (None, "definition-ref"):
            found[ref] = node
        stack.extend(_children(node))
    return found


def _refs_used(node: Any) -> set[str]:
    """Return the refs a node's subtree points to, without following them."""
    found: set[str] = set()
    todo = [node]
    visited: set[int] = set()
    while todo:
        item = todo.pop()
        if id(item) in visited:
            continue
        visited.add(id(item))
        if _kind(item) == "definition-ref":
            found.add(str(item.get("schema_ref", "")))
        todo.extend(_children(item))
    return found


def _reachable(start: set[str], direct: dict[str, set[str]]) -> set[str]:
    """Return every ref reachable from ``start`` through the definitions."""
    reached: set[str] = set()
    todo = list(start)
    while todo:
        ref = todo.pop()
        if ref in reached:
            continue
        reached.add(ref)
        todo.extend(direct.get(ref, ()))
    return reached


def _top_config(root: dict[str, Any]) -> Any:
    node = root
    if node.get("type") == "definitions":
        node = node.get("schema", {})
    config = node.get("config") if type(node) is dict else None
    return config if type(config) is dict else None


def _object_names(node: dict[str, Any]) -> frozenset[str] | None:
    """Return the keys an object schema that forbids extra keys can read, or ``None`` when it allows them."""
    inner: Any = node
    if _kind(node) in ("model", "dataclass"):
        inner = node.get("schema")
        # A model or dataclass validator in "before", "after" or "wrap" mode
        # sits between the object and its fields.
        while _kind(inner) in ("function-before", "function-after", "function-wrap", "chain"):
            inner = inner.get("schema") if _kind(inner) != "chain" else (inner.get("steps") or [None])[0]
    if _kind(inner) not in ("model-fields", "typed-dict", "dataclass-args"):
        return None
    config: dict[str, Any] = node["config"] if type(node.get("config")) is dict else {}
    if inner.get("extra_behavior", config.get("extra_fields_behavior")) != "forbid":
        return None
    fields = inner.get("fields")
    entries = fields.items() if type(fields) is dict else ((f.get("name"), f) for f in fields or ())
    names: set[str] = set()
    for name, entry in entries:
        if isinstance(name, str):
            names.add(name)
        alias = entry.get("validation_alias") if type(entry) is dict else None
        # An alias is a name, a path (a list starting with a name), or a list of such paths.
        for item in alias if type(alias) is list else [alias]:
            if isinstance(item, str):
                names.add(item)
            elif type(item) is list and item and isinstance(item[0], str):
                names.add(item[0])
            elif type(item) is list and item and type(item[0]) is list and item[0] and isinstance(item[0][0], str):
                names.add(item[0][0])
    return frozenset(names)


# Schema nodes whose most errors are their own one plus those of what they
# hold, once collections stop at their first bad item.
_BOUND_FOLLOWS_CHILDREN = frozenset({
    "model", "dataclass", "model-fields", "typed-dict", "dataclass-args", "arguments", "named-tuple",
    "model-field", "typed-dict-field", "dataclass-field", "arguments-parameter", "union", "chain",
    "lax-or-strict", "json-or-python", "json", "nullable", "default", "function-before", "function-after",
    "function-plain", "definitions",
})  # fmt: skip


def _has_fixed_count(node: dict[str, Any]) -> bool:
    """Whether a node's own error count is fixed by the schema, not by how many extra keys the payload sends."""
    config: dict[str, Any] = node["config"] if type(node.get("config")) is dict else {}
    return not (
        node.get("extra_behavior") == "forbid"
        or config.get("extra_fields_behavior") == "forbid"
        or node.get("extras_schema") is not None
        or node.get("var_args_schema") is not None
        or node.get("var_kwargs_schema") is not None
    )


def _is_fixed_tuple(node: dict[str, Any]) -> bool:
    return _kind(node) == "tuple" and node.get("variadic_item_index") is None


class _Schema:
    """What one class's core schema can do, read once by walking it."""

    def __init__(self, root: dict[str, Any]) -> None:
        self.root = root
        self.definitions = _definitions(root)
        self.definitions_list = list(self.definitions.values())
        direct = {ref: _refs_used(node) for ref, node in self.definitions.items()}
        # A definition is recursive when it can reach itself.
        self.recursive_refs = frozenset(ref for ref in direct if ref in _reachable(direct[ref], direct))
        # A definition reaches recursion when it is recursive or leads to one that is.
        self._ref_reaches = {ref: bool(_reachable({ref}, direct) & self.recursive_refs) for ref in self.definitions}
        self._reaches: dict[int, bool] = {}
        self._repeats: dict[int, bool] = {}
        # A model setting can make every pattern below it use Python's `re`.
        configs = [node["config"] for node in self.nodes(root, follow_refs=False) if type(node.get("config")) is dict]
        self._python_re = any(config.get("regex_engine") == "python-re" for config in configs)
        # Settings that make some scalars read a JSON value and its decoded
        # Python value differently, read for the whole schema because a
        # nested node inherits them from any class above it.
        self._strict = any(config.get("strict") for config in configs)
        self._coerce_numbers_to_str = any(config.get("coerce_numbers_to_str") for config in configs)
        self._repeats_anywhere: bool | None = None

    def reaches_recursion(self, node: Any) -> bool:
        """Whether checking ``node`` can lead into a recursive definition."""
        known = self._reaches.get(id(node))
        if known is None:
            ref = node.get("ref") if type(node) is dict else None
            known = (isinstance(ref, str) and ref in self.recursive_refs) or any(
                self._ref_reaches.get(used, False) for used in _refs_used(node)
            )
            self._reaches[id(node)] = known
        return known

    def repeats_recursion(self, node: Any) -> bool:
        """
        Whether ``node`` can check a part of the data that reaches a recursive definition more than once.

        A union repeats work only when two of its members both lead into
        recursion and can both read the same kind of value (two models read
        the same object). A union of a recursive dict and a recursive list
        reads each value with one member, so its cost grows with the data,
        and it spends nothing. A wrap validator may call the schema below it
        any number of times.
        """
        known = self._repeats.get(id(node))
        if known is not None:
            return known
        kind = _kind(node)
        if kind == "chain":
            # Each step checks the output of the one before, so two steps
            # that both reach recursion check that part twice.
            known = sum(1 for step in node.get("steps", ()) if self.reaches_recursion(step)) >= 2
        elif kind == "union":
            members = [choice[0] if type(choice) is tuple else choice for choice in node.get("choices", ())]
            known = _overlap([self.input_kinds(member) for member in members if self.reaches_recursion(member)])
        elif kind == "lax-or-strict":
            branches = [node.get("strict_schema"), node.get("lax_schema")]
            known = _overlap([self.input_kinds(branch) for branch in branches if self.reaches_recursion(branch)])
        elif _is_authors_wrap(node):
            known = self.reaches_recursion(node)
        else:
            known = False
        self._repeats[id(node)] = known
        return known

    def repeats_anywhere(self) -> bool:
        """Whether any part of the schema may check the same recursive value more than once."""
        if self._repeats_anywhere is None:
            self._repeats_anywhere = any(
                self.repeats_recursion(node) for node in self.nodes(self.root, follow_refs=False)
            )
        return self._repeats_anywhere

    def text_steps(self, node: dict[str, Any]) -> int:
        """Return the steps per 64 characters one schema node's own check of a string costs (see ``TEXT_STEPS``)."""
        kind = _kind(node)
        if kind == "json":
            return TEXT_STEPS["json"]
        if kind == "str" and node.get("pattern") is not None:
            engine = node.get("regex_engine")
            if engine == "python-re" or (engine is None and self._python_re):
                return TEXT_STEPS["python-re"]
        if kind == "decimal" and (node.get("max_digits") is not None or node.get("decimal_places") is not None):
            # Counting the digits takes longer than reading the number.
            return TEXT_STEPS["decimal-digits"]
        if kind in _SCALAR_TEXT:
            return TEXT_STEPS[_SCALAR_TEXT[kind]]
        if (kind in _FUNCTION_TYPES or kind == "json-or-python") and not _is_pydantic_own(node, follow=False):
            # An after validator gets the checked value, which holds no text
            # when its schema checks a number, a date or another such value.
            if kind == "function-after" and _kind(node.get("schema")) in _TEXTLESS_TYPES:
                return TEXT_STEPS["plain"]
            # The author's own function may parse the string.
            return TEXT_STEPS["function"]
        return TEXT_STEPS["plain"]

    def input_kinds(self, node: Any, entered: frozenset[str] = frozenset()) -> frozenset[str]:
        """Return which kinds of JSON value a schema node can descend into: ``"object"``, ``"array"``, ``"leaf"``."""
        kind = _kind(node)
        if kind == "definition-ref":
            ref = str(node.get("schema_ref", ""))
            target = self.definitions.get(ref)
            # A reference back into a definition being read adds nothing new.
            return frozenset() if target is None or ref in entered else self.input_kinds(target, entered | {ref})
        if isinstance(node, dict) and isinstance(node.get("ref"), str):
            entered |= {node["ref"]}
        if kind in _OBJECT_TYPES or kind in _MAPPING_TYPES:
            return _OBJECT
        if kind in _ARRAY_TYPES:
            return _ARRAY
        if kind == "named-tuple":
            return _OBJECT | _ARRAY
        if kind in _SCALAR_TYPES or kind == "json":
            return _LEAF
        if kind in ("union", "tagged-union"):
            choices = node.get("choices", ())
            members = choices.values() if type(choices) is dict else choices
            found: frozenset[str] = frozenset()
            for member in members:
                found |= self.input_kinds(member[0] if type(member) is tuple else member, entered)
            return found
        if kind == "lax-or-strict":
            return self.input_kinds(node.get("strict_schema"), entered) | self.input_kinds(
                node.get("lax_schema"), entered
            )
        if kind == "json-or-python":
            return self.input_kinds(node.get("python_schema"), entered)
        if kind == "chain":
            steps = node.get("steps") or [None]
            return self.input_kinds(steps[0], entered)
        if kind == "nullable":
            return _LEAF | self.input_kinds(node.get("schema"), entered)
        if kind in ("default", "function-after", "custom-error", "definitions"):
            return self.input_kinds(node.get("schema"), entered)
        # A function that sees the raw value first, or a node this module
        # does not know, may read any kind.
        return _ANY

    def nodes(self, start: Any, *, follow_refs: bool) -> Iterator[Any]:
        """Yield every schema node below ``start``, following refs into definitions when asked, each once."""
        stack = [start]
        seen: set[int] = set()
        while stack:
            node = stack.pop()
            if id(node) in seen:
                continue
            seen.add(id(node))
            if type(node) is dict:
                yield node
                if follow_refs and _kind(node) == "definition-ref":
                    target = self.definitions.get(str(node.get("schema_ref", "")))
                    if target is not None:
                        stack.append(target)
            stack.extend(_children(node))

    def unbounded_reason(self, start: Any, context: _Context, *, discarded_only: bool = False) -> str | None:
        """
        Return why a part of the copy that no wrapper can reach could make too many errors or work, or ``None``.

        The walk follows the same contexts as the copy (see ``_Rewriter``),
        from ``start`` reached in ``context``. Where no wrapper may go
        (inside ``Json[...]``, in the copy for JSON text, in the fallback),
        the copy keeps Pydantic's own nodes, so these parts are refused:

        - a part that may check the same recursive value more than once
          (``_Schema.repeats_recursion``: a union with two or more members
          that hold more of the tree, a chain, a lax-or-strict pair);
        - typed extra keys whose value can fail with more than one error, or
          with a long message;
        - a list or dict inside ``Json[...]`` below a wrap validator, which
          reads every item, whose items can fail with more than one error or
          a long message.

        A wrap validator lets wrappers back in below it, so the walk treats
        everything below one as counted, as the copy does.

        With ``discarded_only``, typed extra keys count only below a part
        whose errors the node above may throw away (a union member, a
        default used on error, a custom error, a strict attempt). This is
        the rule for the JSON read of a lax model State, which follows a
        Python check that accepted the writes.
        """
        # Each entry also says whether a key the payload chooses sits above
        # the node where no wrapper counts: pydantic-core copies that key into
        # the location of every error below it before anything can count them.
        stack: list[tuple[Any, _Context, bool, bool]] = [(start, context, False, False)]
        seen: set[tuple[int, _Context, bool, bool]] = set()
        while stack:
            node, reached, discarded, keyed = stack.pop()
            if (id(node), reached, discarded, keyed) in seen:
                continue
            seen.add((id(node), reached, discarded, keyed))
            if type(node) in (list, tuple):
                stack.extend((item, reached, discarded, keyed) for item in node)
                continue
            if type(node) is not dict:
                continue
            kind = _kind(node)
            if kind == "definition-ref":
                target = self.definitions.get(str(node.get("schema_ref", "")))
                if target is not None:
                    stack.append((target, reached, discarded, keyed))
                continue
            wrappable, under_wrap = _node_context(node, reached)
            if not wrappable:
                if self.repeats_recursion(node):
                    return _REPEAT_REASONS.get(kind or "") or self._union_reason(node)
                if (discarded or not discarded_only) and self._extras_unbounded(node):
                    return _DISCARDED_EXTRAS_REASON if discarded_only else _EXTRAS_REASON
                if under_wrap and kind in _FAIL_FAST_TYPES and not self._items_fail_once(node, counted_only=keyed):
                    # Below a dict's values the rule is narrower, and its fix differs.
                    if keyed and self._items_fail_once(node):
                        return _KEYED_ITEMS_REASON
                    return _WRAPPED_ITEMS_REASON
            below = _child_context(node, reached)
            # Below a dict's values the key is in every error's location.
            keyed_below = keyed or (not wrappable and under_wrap and kind in _MAPPING_TYPES)
            for name, value in node.items():
                if name not in _NOT_SCHEMA_KEYS:
                    stack.append((value, below, discarded or _discards(kind, name, node), keyed_below))
        return None

    def _union_reason(self, node: dict[str, Any]) -> str:
        """Return the reason for a repeating union: whether every member that holds more of the tree is a class."""
        for choice in node.get("choices", ()):
            member = choice[0] if type(choice) is tuple else choice
            if self.reaches_recursion(member) and not self._is_class(member):
                # Only a class can carry a Literal tag field.
                return _MIXED_UNION_REASON
        return _UNION_REASON

    def _is_class(self, node: Any) -> bool:
        """Whether a schema node checks a model, a dataclass or a TypedDict, below references and validators."""
        seen: set[str] = set()
        while True:
            kind = _kind(node)
            if kind == "definition-ref":
                ref = str(node.get("schema_ref", ""))
                if ref in seen:
                    return False
                seen.add(ref)
                node = self.definitions.get(ref)
            elif kind in _FUNCTION_TYPES - {"function-plain"} or kind in ("nullable", "default"):
                node = node.get("schema")
            else:
                return kind in ("model", "dataclass", "typed-dict")

    def _items_fail_once(self, node: dict[str, Any], *, counted_only: bool = False) -> bool:
        """
        Whether each item of a collection that Citry cannot count as a whole is still kept in check.

        Each item, and each key of a dict, must be one the copy counts as it
        fails (``reads_json_alike``), a list or dict whose own items this
        walk reads in turn, or a check that fails with at most one error with
        a short message, so the errors grow no faster than the JSON values
        the text holds. With ``counted_only`` (a key the payload chooses sits
        above, and lands in each error's location), only counted items and
        lists or dicts pass.
        """
        if _is_fixed_tuple(node):
            # A fixed tuple has as many positions as its schema.
            return True
        for key in _ITEM_KEYS:
            schemas = node.get(key)
            for schema in schemas if type(schemas) is list else [schemas]:
                if type(schema) is not dict or self.reads_json_alike(schema):
                    continue
                inner = self._unwrap_one_value(schema)
                if _kind(inner) in _FAIL_FAST_TYPES and not _is_fixed_tuple(inner):
                    continue
                if counted_only:
                    return False
                if not self._fails_with_few_short_errors(schema):
                    return False
        return True

    def _fails_with_few_short_errors(self, node: dict[str, Any]) -> bool:
        """Whether a value fails with at most one error, whose message is short."""
        message = self.one_error_message(node)
        return message is not None and message <= _LONG_EXTRA_MESSAGE

    def _unwrap_one_value(self, node: Any) -> Any:
        """Return the schema below nodes that add at most one error of their own for the same value."""
        while True:
            kind = _kind(node)
            if kind == "definition-ref":
                ref = str(node.get("schema_ref", ""))
                if ref in self.recursive_refs:
                    return node
                node = self.definitions.get(ref)
            elif kind in ("nullable", "default") or (kind == "function-wrap" and not _is_authors_wrap(node)):
                node = node.get("schema")
            else:
                return node

    def reads_json_alike(self, node: dict[str, Any]) -> bool:
        """
        Whether a schema node reads a JSON value and its decoded Python value alike, so a wrapper may sit above it.

        Inside ``Json[...]`` a Python wrapper hands the schema below it the
        decoded Python value, so the copy may count an item there only when
        the result is the same: the same value, or the same errors.
        """
        kind = _kind(node)
        if kind == "literal":
            return all(type(value) in _JSON_SCALARS for value in node.get("expected", ()))
        if kind == "str" and (self._coerce_numbers_to_str or node.get("coerce_numbers_to_str")):
            # JSON mode writes a number from its text ("1E2" gives "100"),
            # Python mode from the float it decodes to ("100.0").
            return False
        if kind in _JSON_ALIKE_TYPES:
            return True
        if kind in _LAX_JSON_ALIKE_TYPES:
            # A strict check of these accepts a JSON string but not a Python one.
            return not (self._strict or node.get("strict"))
        if kind == "nullable":
            inner = node.get("schema")
            return type(inner) is dict and self.reads_json_alike(inner)
        if kind == "union" and node.get("mode", "smart") == "smart":
            # A smart union ranks a JSON string and a Python string differently
            # against a time or a UUID, so only members JSON writes natively
            # pick the same member in both modes.
            members = [choice[0] if type(choice) is tuple else choice for choice in node.get("choices", ())]
            return bool(members) and all(
                type(member) is dict
                and _kind(member) in _JSON_ALIKE_TYPES | {"literal"}
                and self.reads_json_alike(member)
                for member in members
            )
        return False

    def _extras_unbounded(self, node: dict[str, Any]) -> bool:
        """Whether one of the node's extra keys, extra arguments or variadic parameters can fail with many errors."""
        schemas = [node.get(key) for key in _EXTRAS_KEYS]
        if _kind(node) == "arguments-v3":
            schemas += [
                entry.get("schema")
                for entry in node.get("arguments_schema") or ()
                if type(entry) is dict and entry.get("mode") in _VARIADIC_MODES
            ]
        for schema in schemas:
            if type(schema) is not dict:
                continue
            message = self.one_error_message(schema)
            if message is None or message > _LONG_EXTRA_MESSAGE:
                return True
        return False

    def one_error_message(self, node: Any, entered: frozenset[str] = frozenset()) -> int | None:
        """
        Return the longest message ``node`` can fail with, when it can fail with at most one error; else ``None``.

        A message the author's own function raises counts as short: its
        length is the author's choice.
        """
        kind = _kind(node)
        if kind == "definition-ref":
            ref = str(node.get("schema_ref", ""))
            target = self.definitions.get(ref)
            if target is None or ref in entered:
                return None
            return self.one_error_message(target, entered | {ref})
        if kind in _SCALAR_TYPES:
            return _own_message_length(node)
        if kind in ("function-plain", "any"):
            return 0
        if kind == "custom-error" or (kind in ("union", "tagged-union") and node.get("custom_error_type")):
            # One error with the schema's own message replaces those below.
            return len(str(node.get("custom_error_message") or ""))
        parts: list[Any]
        if kind in ("nullable", "default", "function-before", "function-after", "json") or (
            kind == "function-wrap" and not _is_authors_wrap(node)
        ):
            parts = [node.get("schema")]
        elif kind == "lax-or-strict":
            parts = [node.get("strict_schema"), node.get("lax_schema")]
        elif kind == "json-or-python":
            parts = [node.get("json_schema"), node.get("python_schema")]
        elif kind == "chain":
            # Each step checks the output of the one before, and the first
            # that fails ends the chain.
            parts = list(node.get("steps") or ())
        elif kind == "tagged-union" and type(node.get("choices")) is dict:
            # A tag that matches no member gives one error listing the tags.
            parts = list(node["choices"].values())
            longest = _own_message_length(node)
            for part in parts:
                found = self.one_error_message(part, entered)
                if found is None:
                    return None
                longest = max(longest, found)
            return longest
        elif kind == "union" and len(node.get("choices") or ()) == 1:
            choice = node["choices"][0]
            parts = [choice[0] if type(choice) is tuple else choice]
        else:
            # An object, a collection, a union of several members (one error
            # per member), or a node this module does not know.
            return None
        longest = 0
        for part in parts:
            if type(part) is not dict:
                continue
            found = self.one_error_message(part, entered)
            if found is None:
                return None
            longest = max(longest, found)
        return longest

    def message_length(self, start: Any) -> int:
        """Return the longest message any check below ``start`` can give, as far as the schema sets it."""
        if type(start) is not dict:
            return 0
        return max((_own_message_length(node) for node in self.nodes(start, follow_refs=True)), default=0)

    def json_mode_differs(self) -> str | None:
        """
        Return why pydantic-core could check JSON text differently from the same values decoded, or ``None``.

        A browser write to a model State is JSON, which Citry reads back the
        way the token is read. Checking the decoded values in Python mode
        gives the same answer only when nothing in the schema depends on the
        mode: no strict check of a type JSON has no native form for (a date,
        a tuple, a model), no strict model setting or ``val_json_bytes``
        setting, no schema with separate JSON
        and Python parts that is not Pydantic's own, and no model that forbids
        extra keys and has a field with an alias.
        """
        for node in self.nodes(self.root, follow_refs=False):
            kind = _kind(node)
            config = node.get("config")
            if type(config) is dict:
                if config.get("strict"):
                    return "a strict model setting"
                if config.get("val_json_bytes") not in (None, "utf8"):
                    return "the val_json_bytes setting"
            if node.get("strict") and kind not in _JSON_NATIVE_TYPES:
                return f"a strict {kind} field"
            if kind == "json-or-python" and not _is_pydantic_own(node):
                return "a custom type that checks JSON input differently from Python input"
            if kind == "model" and _forbids_with_alias(node):
                # Reading by field name, JSON mode drops such an alias key
                # while Python mode refuses it as an extra key.
                return "a model that forbids extra keys and has a field with an alias"
        return None

    def error_bound(self) -> int | None:
        """
        Return the most errors one check can keep once every collection stops at its first bad item.

        ``None`` means the payload decides: a recursive schema, extra keys,
        a wrap validator (which may read every item), or a node this does
        not know.
        """
        return self._bound(self.root, {}, frozenset())

    def _bound(self, node: Any, known: dict[int, int | None], entered: frozenset[str]) -> int | None:
        if type(node) is not dict:
            return 0
        if id(node) in known:
            return known[id(node)]
        kind = _kind(node)
        result: int | None
        if kind == "definition-ref":
            ref = str(node.get("schema_ref", ""))
            target = self.definitions.get(ref)
            # Recursion lets the payload choose the depth.
            if target is None or ref in self.recursive_refs or ref in entered:
                return None
            result = self._bound(target, known, entered | {ref})
        elif kind is None:
            # A field entry of a model or dataclass, or a tuple of a union member and its label.
            result = self._sum(_children(node), known, entered, own=0)
        elif kind in _SCALAR_TYPES or kind == "custom-error":
            result = 1
        elif _is_authors_wrap(node) or not _has_fixed_count(node):
            # The author's wrap validator may read every error below it and
            # retry, and extra keys are as many as the payload sends.
            result = None
        elif kind == "function-wrap":
            # Pydantic's own wrap validators call their handler once.
            result = self._sum(_children(node), known, entered, own=1)
        elif kind == "tagged-union":
            parts = [self._bound(choice, known, entered) for choice in (node.get("choices") or {}).values()]
            result = None if None in parts else max((part or 0 for part in parts), default=0) + 1
        elif kind in _BOUND_FOLLOWS_CHILDREN or kind in _FAIL_FAST_TYPES:
            # A collection stops at its first bad item, so it keeps the errors
            # of one item; a fixed tuple keeps those of each position.
            result = self._sum(_children(node), known, entered, own=1)
        else:
            # A node this module does not know may report any number of errors.
            result = None
        known[id(node)] = result
        return result

    def _sum(self, children: list[Any], known: dict[int, int | None], entered: frozenset[str], own: int) -> int | None:
        """Add up the bounds of the schemas among ``children``, which may be field mappings and lists of them."""
        total = own
        stack = list(children)
        while stack:
            child = stack.pop()
            if type(child) in (list, tuple):
                stack.extend(child)
            elif type(child) is dict and _kind(child) is None and "schema" not in child:
                # A mapping of field names to field schemas.
                stack.extend(child.values())
            elif type(child) is dict:
                bound = self._bound(child, known, entered)
                if bound is None:
                    return None
                total += bound
        return total

    def keys_from_payload(self) -> bool:
        """Whether a key the payload chooses can land in an error's path: a dict, extra keys, or ``Json`` text."""
        for node in self.nodes(self.root, follow_refs=False):
            kind = _kind(node)
            if kind in _MAPPING_TYPES or kind == "json" or node.get("extras_schema") is not None:
                return True
        return False

    def longest_message(self) -> int:
        """Return the length of the longest message the schema sets: a list of allowed values, or a pattern."""
        return max((_own_message_length(node) for node in self.nodes(self.root, follow_refs=False)), default=0)

    def reads_json(self) -> bool:
        return any(_kind(node) == "json" for node in self.nodes(self.root, follow_refs=False))


def _forbids_with_alias(node: dict[str, Any]) -> bool:
    """Whether a model schema forbids extra keys and gives a field a validation alias."""
    names = _object_names(node)
    if names is None:
        return False
    fields = _top_fields(node)
    return any(type(entry) is dict and entry.get("validation_alias") is not None for entry in fields.values())


def _own_message_length(node: dict[str, Any]) -> int:
    """Return how long a message one schema node writes into each of its errors can get, from the schema alone."""
    kind = _kind(node)
    if kind == "literal":
        return sum(len(repr(value)) + 2 for value in node.get("expected", ()))
    if kind == "enum":
        return sum(len(repr(value)) + 2 for value in node.get("members", ()))
    if kind == "tagged-union" and type(node.get("choices")) is dict:
        # A tag that matches no member lists every expected tag.
        return sum(len(repr(tag)) + 2 for tag in node["choices"])
    pattern = node.get("pattern")
    # A string pattern is repeated in its error message.
    return len(pattern) if isinstance(pattern, str) else 0


def _top_fields(root: dict[str, Any]) -> dict[str, Any]:
    """Return the field schemas of a model or dataclass core schema, by field name."""
    definitions = _definitions(root)
    node: Any = root
    # A class that refers to itself is a reference to its own definition.
    while _kind(node) in (
        "definitions",
        "definition-ref",
        "model",
        "dataclass",
        "function-before",
        "function-after",
        "function-wrap",
    ):
        node = definitions.get(str(node.get("schema_ref"))) if _kind(node) == "definition-ref" else node.get("schema")
    if _kind(node) == "model-fields" and type(node.get("fields")) is dict:
        return dict(node["fields"])
    if _kind(node) == "dataclass-args":
        return {str(entry.get("name")): entry for entry in node.get("fields", ()) if type(entry) is dict}
    return {}


# The packages whose functions and classes a json-or-python schema may use
# and still count as Pydantic's own: Pydantic and the standard library types
# it writes such schemas for.
_OWN_PACKAGES = frozenset({
    "pydantic", "pydantic_core", "ipaddress", "pathlib", "collections", "decimal", "uuid", "datetime", "re",
    "typing", "builtins", "fractions", "enum", "functools",
})  # fmt: skip


def _is_pydantic_own(node: dict[str, Any], *, follow: bool = True) -> bool:
    """
    Whether a json-or-python schema was written by Pydantic for a standard type, whose two parts read JSON alike.

    Pydantic writes such schemas for paths, IP addresses and similar types,
    with a lax part that reads the JSON text as well. An app's own type can
    give its Python part a check that refuses what its JSON part accepts, so
    any function or class from another package makes the schema the app's.
    Without ``follow``, only the node's own function is read.
    """
    inners = [node, *_Schema(node).nodes(node, follow_refs=False)] if follow else [node]
    for inner in inners:
        function = inner.get("function")
        targets = [function.get("function") if type(function) is dict else None, inner.get("cls")]
        for target in targets:
            if target is None:
                continue
            module = getattr(getattr(target, "func", target), "__module__", "") or ""
            if module.split(".")[0] not in _OWN_PACKAGES:
                return False
    return True


################################################
# BUILDING THE COPY
################################################


# Where a schema node sits in the copy: whether a Python wrapper may go there,
# and whether it is below a wrap validator, which may read every error below
# it and retry, so its collections keep reading every item.
_Context = tuple[bool, bool]
# The keys of an object schema that hold the schema of each extra key or
# value, one check per key the payload sends.
_EXTRAS_KEYS = ("extras_schema", "extras_keys_schema", "var_args_schema", "var_kwargs_schema")
# The schema types of one field of an object, which may carry a validation alias.
_FIELD_KINDS = frozenset({"model-field", "dataclass-field", "typed-dict-field"})
# The modes of an ``arguments-v3`` parameter that checks any number of values.
_VARIADIC_MODES = frozenset({"var_args", "var_kwargs_uniform"})


def _node_context(node: Any, context: _Context) -> _Context:
    """Return the context a node itself sits in, given the context it was reached in."""
    wrappable, under_wrap = context
    # pydantic-core hands a wrap validator a Python object even in JSON mode,
    # so a wrapper above it changes nothing the wrap validator sees.
    return (True, under_wrap) if _is_authors_wrap(node) else (wrappable, under_wrap)


def _child_context(node: Any, context: _Context) -> _Context:
    """Return the context of a node's children."""
    _, under_wrap = context
    kind = _kind(node)
    if kind == "json":
        # Below `Json[...]` the schema reads JSON values again, which a Python
        # wrapper would turn into Python objects; a strict model would then
        # refuse valid data.
        return (False, under_wrap)
    if _is_authors_wrap(node):
        # Below a wrap validator pydantic-core checks the Python object the
        # validator passes on, in JSON mode too, so wrappers are safe there.
        # Pydantic's own wrap validators are left as they are: wrapping one
        # would change the label Pydantic gives it inside a union.
        return (True, True)
    return context


def _discards(kind: str | None, key: str, node: dict[str, Any]) -> bool:
    """Whether the node above may throw away the errors of the schema it holds under ``key``."""
    if kind == "union":
        return key == "choices"
    if kind == "lax-or-strict":
        return key == "strict_schema"
    if kind == "default":
        return key == "schema" and node.get("on_error") in ("default", "omit")
    return kind == "custom-error" and key == "schema"


class _Rewriter:
    """
    Copy a core schema with the changes this module describes.

    ``wrapped=False`` starts the copy where wrappers may not go (the copy for
    JSON text, and the fallback), so it gets ``fail_fast`` and nothing else,
    except at and below a wrap validator.

    A definition (a schema that ``definition-ref`` nodes point to) can be
    reached from places with different contexts, such as from inside and
    outside ``Json[...]``. Each context it is reached in gets its own copy
    under its own name, so a definition used inside ``Json[...]`` gets no
    wrappers and one used below a wrap validator keeps reading every item.

    ``text_wrappers=True`` puts a wrapper that spends for text on every check
    that parses it, even when the schema itself never checks a value twice,
    for a class that Citry's own union check may check again.

    ``by_name=True`` builds the copy that checks browser writes to a model
    State, whose keys are field names. pydantic-core 2.46 (Pydantic 2.13.0)
    forgets the call's ``by_name`` setting below a wrap validator's handler,
    and every Citry wrapper is one, so this copy drops each field's
    validation alias instead: the field is then found by its name whatever
    the setting. On that version the class also forgets the setting below
    the author's own wrap validator, so there the aliases stay, and the copy
    reads keys as the class does.
    """

    def __init__(self, schema: _Schema, *, wrapped: bool, by_name: bool = False, text_wrappers: bool = False) -> None:
        self.schema = schema
        self.wrapped = wrapped
        self.by_name = by_name
        self.text_wrappers = text_wrappers
        self._names: dict[tuple[str, _Context], str] = {}

    def label(self, choice: Any) -> str | None:
        """Return the label Pydantic gives a union member in the class's own validator."""
        standalone: Any = choice
        if self.schema.definitions_list:
            standalone = {"type": "definitions", "schema": choice, "definitions": self.schema.definitions_list}
        try:
            return str(pydantic_core.SchemaValidator(standalone).title)
        except Exception:  # noqa: BLE001 - a member that cannot stand alone keeps Pydantic's default label
            return None

    def is_scalar_union(self, node: dict[str, Any]) -> bool:
        for choice in node.get("choices", ()):
            member = choice[0] if type(choice) is tuple else choice
            if _kind(member) == "definition-ref":
                member = self.schema.definitions.get(str(member.get("schema_ref", "")))
            if _kind(member) not in _SCALAR_TYPES:
                return False
        return True

    def rewrite(self, root: Any) -> Any:
        """
        Return a copy of ``root`` with this module's changes; functions and classes stay the same objects.

        The walk uses its own stack, because a schema of nested models can be
        deeper than Python's recursion limit, and a failure here would refuse
        every call to the class. Each task fills one slot (``target[key]``).
        A dict schedules its own "finish" task before its children, so the
        finish runs once every child is copied. Definitions are copied when a
        reference reaches them, once per context, into one list at the top.
        """
        result: list[Any] = [None]
        definitions: list[Any] = []
        start: _Context = (self.wrapped, False)
        stack: list[tuple[str, Any, _Context, Any, Any]] = [("enter", root, start, result, 0)]

        def reference(ref: str, context: _Context) -> str:
            # The first reference in a context schedules that context's copy.
            known = self._names.get((ref, context))
            if known is not None:
                return known
            name = f"{ref}:citry-{int(context[0])}{int(context[1])}"
            self._names[(ref, context)] = name
            target = self.schema.definitions.get(ref)
            if target is not None:
                definitions.append(None)
                index = len(definitions) - 1
                # The name goes on the finished copy, which may be a wrapper.
                stack.append(("name", name, context, definitions, index))
                stack.append(("enter", target, context, definitions, index))
            return name

        while stack:
            step, node, context, target, key = stack.pop()
            if step == "finish":
                original, copied = node
                target[key] = self.finish(original, copied, context)
                continue
            if step == "name":
                target[key]["ref"] = node
                continue
            if step == "tuple":
                target[key] = tuple(node)
                continue
            if type(node) in (list, tuple):
                items: list[Any] = [None] * len(node)
                if type(node) is tuple:
                    stack.append(("tuple", items, context, target, key))
                else:
                    target[key] = items
                stack.extend(("enter", item, context, items, index) for index, item in enumerate(node))
                continue
            if type(node) is not dict:
                target[key] = node
                continue
            kind = _kind(node)
            if kind == "definitions":
                # Its definitions are copied when a reference reaches them.
                stack.append(("enter", node.get("schema"), context, target, key))
                continue
            copied = dict(node)
            # Each copy of a definition gets its name when it is finished.
            copied.pop("ref", None)
            if kind == "definition-ref":
                copied["schema_ref"] = reference(str(node.get("schema_ref", "")), context)
                target[key] = copied
                continue
            stack.append(("finish", (node, copied), _node_context(node, context), target, key))
            below = _child_context(node, context)
            # The keys keep their order; the children fill their values in.
            stack.extend(
                ("enter", value, below, copied, name) for name, value in node.items() if name not in _NOT_SCHEMA_KEYS
            )
        if not definitions:
            return result[0]
        return {"type": "definitions", "schema": result[0], "definitions": definitions}

    def finish(self, node: dict[str, Any], copied: dict[str, Any], context: _Context) -> Any:
        """Apply this module's change to one schema node whose children are already copied."""
        result = self._change(node, copied, context)
        if context[0] and (self.text_wrappers or self.schema.repeats_anywhere()):
            text_steps = self.schema.text_steps(node)
            if text_steps > TEXT_STEPS["plain"]:
                # Inside a recursive value that may be checked again, a check
                # that parses text spends each time it runs.
                long_steps = _LONG_JSON_TEXT_STEPS if _kind(node) == "json" else 0
                return _wrap(result, _text_spending(text_steps, long_steps))
        return result

    def _change(self, node: dict[str, Any], copied: dict[str, Any], context: _Context) -> Any:
        wrappable, under_wrap = context
        kind = _kind(node)
        if self.by_name and not under_wrap and kind in _FIELD_KINDS:
            copied.pop("validation_alias", None)
        if kind in _FAIL_FAST_TYPES:
            return self.collection(copied, wrappable=wrappable, under_wrap=under_wrap)
        if kind == "union":
            # A wrapper anywhere inside a member changes the label Pydantic
            # gives it, also where no wrapper may sit above the union itself.
            self.keep_labels(node, copied)
        if not wrappable:
            # Here a Python wrapper would turn JSON values into Python objects.
            return copied
        if kind == "json" and under_wrap:
            # Below a wrap validator the text's items may each keep an error
            # that no wrapper inside can count, so the errors are counted as
            # the text fails, before the author's function sees them.
            return _wrap(copied, _counted)
        for key in _EXTRAS_KEYS:
            # Pydantic checks every extra key before the object returns, so
            # each one is counted as it fails, as an item of a collection is.
            if type(copied.get(key)) is dict:
                copied[key] = _wrap(copied[key], _counted)
        if kind == "arguments-v3" and type(copied.get("arguments_schema")) is list:
            # A parameter that takes any number of arguments checks each one.
            copied["arguments_schema"] = [
                {**entry, "schema": _wrap(entry["schema"], _counted)}
                if type(entry) is dict and entry.get("mode") in _VARIADIC_MODES and type(entry.get("schema")) is dict
                else entry
                for entry in copied["arguments_schema"]
            ]
        repeats = self.schema.repeats_recursion(node)
        if kind == "union":
            return self.union(node, copied, repeats=repeats)
        if kind in ("model", "dataclass") and type(copied.get("schema")) is dict:
            # The inner schema is wrapped, not the object, so the object keeps its name.
            names = _object_names(node)
            copied["schema"] = _wrap(
                copied["schema"], _extras_guard(names, _counted) if names is not None else _counted
            )
            return copied
        if kind == "typed-dict":
            names = _object_names(node)
            return _wrap(copied, _extras_guard(names, _counted) if names is not None else _counted)
        if _is_authors_wrap(node):
            if repeats and type(copied.get("schema")) is dict:
                # The author's function may call its handler any number of
                # times, so each call spends for the value it checks.
                copied["schema"] = _wrap(copied["schema"], _spending(_passed_through))
            # The author's wrap validator may catch the errors below it and succeed.
            return _wrap(copied, _counted)
        if kind == "lax-or-strict" and type(copied.get("strict_schema")) is dict:
            # Inside a union, the strict attempt's errors are thrown away
            # when the lax attempt follows.
            copied["strict_schema"] = _wrap(copied["strict_schema"], _discarded_spending if repeats else _discarded)
            if repeats and type(copied.get("lax_schema")) is dict:
                copied["lax_schema"] = _wrap(copied["lax_schema"], _spending(_passed_through))
            return copied
        if kind == "chain" and repeats:
            # Each step checks the output of the one before, so each step
            # that leads into recursion spends for the value it checks.
            copied["steps"] = [
                _wrap(step, _spending(_passed_through)) if self.schema.reaches_recursion(original) else step
                for original, step in zip(node.get("steps", ()), copied.get("steps", ()), strict=True)
            ]
            return copied
        # These nodes always throw away the errors of the schema they hold:
        # a default used on error and a custom error that replaces them.
        if (
            kind == "default" and node.get("on_error") in ("default", "omit") and type(copied.get("schema")) is dict
        ) or (kind == "custom-error" and type(copied.get("schema")) is dict):
            copied["schema"] = _wrap(copied["schema"], _discarded)
        return copied

    def collection(self, copied: dict[str, Any], *, wrappable: bool, under_wrap: bool) -> dict[str, Any]:
        if _is_fixed_tuple(copied):
            # A fixed tuple has as many positions as its schema and checks its
            # length before its items, so stopping early would change its message.
            return copied
        if under_wrap and wrappable:
            # A wrap validator may read every error and retry, so its
            # collections keep reading every item, and each item is counted
            # instead. A tuple holds a list of item schemas, one per position.
            for key in _ITEM_KEYS:
                item = copied.get(key)
                if type(item) is dict:
                    copied[key] = _wrap(item, _counted)
                elif type(item) is list:
                    copied[key] = [_wrap(entry, _counted) if type(entry) is dict else entry for entry in item]
            return copied
        if under_wrap:
            # Inside `Json[...]` below a wrap validator the author's function
            # may read every error, so the collection reads every item, as the
            # class does. Registration accepts this only when each item fails
            # with at most one short error (see `_Schema.unbounded_reason`).
            # An item that JSON and Python read alike (a number, a string, a
            # boolean, a null, a time or UUID in lax mode) can still be
            # counted as it fails; see `_Schema.reads_json_alike`.
            for key in _ITEM_KEYS:
                item = copied.get(key)
                if type(item) is dict and self.schema.reads_json_alike(item):
                    copied[key] = _wrap(item, _counted)
                elif type(item) is list:
                    alike = self.schema.reads_json_alike
                    copied[key] = [
                        _wrap(entry, _counted) if type(entry) is dict and alike(entry) else entry for entry in item
                    ]
            return copied
        copied["fail_fast"] = True
        return copied

    def keep_labels(self, node: dict[str, Any], copied: dict[str, Any]) -> None:
        """
        Give each member that holds a wrapper of the copy the label the class gives it.

        Pydantic builds a member's label from its schema, nested parts too
        (``json[union[int,function-wrap[wrap_val()]]]``), and puts it in each
        error's location, so a wrapper anywhere inside would show its own
        name there.
        """
        copied["choices"] = [
            (rewritten, label)
            if type(original) is not tuple
            # A reference's copy is built later and may be a wrapper too,
            # and the label names what the reference points to.
            and _holds_citry_wrapper(rewritten, references=True)
            and (label := self.label(original))
            else rewritten
            for original, rewritten in zip(node.get("choices", ()), copied.get("choices", ()), strict=True)
        ]

    def union(self, node: dict[str, Any], copied: dict[str, Any], *, repeats: bool) -> dict[str, Any]:
        # `keep_labels` already labelled each member that holds a wrapper.
        if self.is_scalar_union(node) and not repeats:
            # Each member reports at most one error, so a union of scalars
            # adds no more than its member count.
            return copied
        members = [choice[0] if type(choice) is tuple else choice for choice in node.get("choices", ())]
        if not repeats and not _overlap([self.schema.input_kinds(member) for member in members]):
            # At most one member can descend into any value (a dict and a
            # list, say); the others fail on its type with one error each and
            # run no wrapper. So the members need no wrapper of their own,
            # and the union's wrapper still checks the total at each level.
            return _wrap(copied, _counted)
        # Wrapping a member would change the label Pydantic puts in each error's
        # location, so every member keeps the label the class's validator gives it.
        labelled: list[Any] = []
        discard = _discarded_spending if repeats else _discarded
        for original, rewritten in zip(node.get("choices", ()), copied.get("choices", ()), strict=True):
            if type(rewritten) is tuple:
                labelled.append((_wrap(rewritten[0], discard), rewritten[1]))
                continue
            label = self.label(original)
            member = _wrap(rewritten, discard)
            labelled.append((member, label) if label is not None else member)
        copied["choices"] = labelled
        # Each member spends for its own attempt, so the union itself only counts.
        return _wrap(copied, _counted)


# Schema types that read a value the same way from JSON and from the Python
# value JSON decodes to, strict or not, and so may sit below a Python wrapper
# inside `Json[...]` (a wrapper hands the schema below it the Python value).
# See `_Schema.reads_json_alike` for the settings that change this.
_JSON_ALIKE_TYPES = frozenset({"int", "float", "str", "bool", "none"})
# Schema types that read them alike only when not strict.
_LAX_JSON_ALIKE_TYPES = frozenset({"time", "uuid"})
_JSON_SCALARS = (str, int, float, bool, type(None))


def _is_authors_wrap(node: Any) -> bool:
    """
    Whether a schema node is a wrap validator that may read every error below it and retry.

    Pydantic writes wrap validators of its own (for URLs, secrets and
    sequences), which call their handler once and keep no errors, so only
    another function counts.
    """
    return _kind(node) == "function-wrap" and not _is_pydantic_own(node, follow=False)


def _wrap(schema: Any, function: Callable[[Any, Any], Any]) -> dict[str, Any]:
    wrapper: dict[str, Any] = {
        "type": "function-wrap",
        "function": {"type": "no-info", "function": function},
        "schema": schema,
        # Marks the wrapper as Citry's, for `_is_citry_wrapper`.
        "metadata": {_WRAPPER_MARK: True},
    }
    # References to the wrapped schema must reach the wrapper.
    if type(schema) is dict and "ref" in schema:
        wrapper["ref"] = schema.pop("ref")
    return wrapper


_WRAPPER_MARK = "citry_wrapper"


def _is_citry_wrapper(node: Any) -> bool:
    """Whether a schema node is a wrapper the copy added (see ``_wrap``)."""
    metadata = node.get("metadata") if type(node) is dict else None
    return type(metadata) is dict and metadata.get(_WRAPPER_MARK) is True


def _holds_citry_wrapper(start: Any, *, references: bool = False) -> bool:
    """
    Whether a copied schema node, or a node below it, is a wrapper the copy added; references are not followed.

    With ``references``, a reference counts too, since the copy it points to
    may be a wrapper.
    """
    stack = [start]
    while stack:
        node = stack.pop()
        if _is_citry_wrapper(node) or (references and _kind(node) == "definition-ref"):
            return True
        stack.extend(_children(node))
    return False


def _rebuild_supported() -> bool:
    if pydantic_core is None:
        return False
    try:
        parameters = inspect.signature(pydantic_core.SchemaValidator).parameters
    except (TypeError, ValueError):
        return False
    return "_use_prebuilt" in parameters


# Without `_use_prebuilt` a nested model keeps its own validator, which reads
# every item, so the copy would stop early only at the top level.
SUPPORTED = _rebuild_supported()


@dataclass(eq=False)
class Checker:
    """
    The copy of one class's validator, and what Citry must do around it.

    Attributes:
        validator: The copy, or ``None`` when calls must be refused.
        wrapped: Whether the copy holds counting wrappers. Without them, it
            stops collections early and nothing else.
        needs_path_limit: Whether the caller must also apply the path limit
            (``pydantic_can_report``), because the copy has no wrappers and
            its schema can make errors in step with the payload.
        refusal: Why calls are refused (``validator`` is ``None``), for the log.
        reads_json: Whether the schema reads JSON out of strings.
        longest_message: The longest ``Literal`` or ``Enum`` message.

    """

    validator: Any
    wrapped: bool
    needs_path_limit: bool = False
    refusal: str | None = None
    reads_json: bool = False
    longest_message: int = 0
    logged: bool = field(default=False, repr=False)


# One store per kind of copy: (State, by field name, checked again), see `checker_for`.
_CHECKERS: dict[tuple[bool, bool, bool], WeakKeyDictionary[type, Checker]] = {
    (False, False, False): WeakKeyDictionary(),
    (False, False, True): WeakKeyDictionary(),
    (True, False, False): WeakKeyDictionary(),
    (True, True, False): WeakKeyDictionary(),
}
_JSON_CHECKERS: WeakKeyDictionary[type, Checker] = WeakKeyDictionary()
_LOCK = threading.Lock()


def core_schema_of(cls: type) -> dict[str, Any] | None:
    """Return a Pydantic v2 class's core schema, rebuilt first when its forward references were unresolved."""
    if not getattr(cls, "__pydantic_complete__", True):
        # A model rebuilds itself; a Pydantic dataclass through a function of
        # its module. Either may still fail, and Pydantic then refuses the
        # call itself, as it would without Citry.
        rebuild = getattr(cls, "model_rebuild", None)
        if rebuild is None:
            rebuild = getattr(sys.modules.get("pydantic.dataclasses"), "rebuild_dataclass", None)
            rebuild = (
                None if rebuild is None else (lambda raise_errors, _f=rebuild: _f(cls, raise_errors=raise_errors))
            )
        if rebuild is not None:
            try:
                rebuild(raise_errors=False)
            except Exception:  # noqa: BLE001 - an unresolved class is refused by Pydantic itself at the call
                return None
    root = getattr(cls, "__pydantic_core_schema__", None)
    # The stand-in schema of an unfinished class is a Mapping but not a dict.
    return root if type(root) is dict else None


# The stack of the thread that builds a copy of a validator, in bytes: 16
# times the 1 MB of a Windows thread, on which a chain of about 250 nested
# models overflowed. On Windows the system sets this memory aside for the
# thread, which ends with the build.
_BUILD_STACK_BYTES = 16 * 1024 * 1024
# Keeps Citry's own builds from setting the process-wide stack size at once.
_BUILD_STACK_LOCK = threading.Lock()


def _new_build_stack_lock() -> None:
    """Give a forked child a new lock, since a thread of the parent may have held the old one at the fork."""
    global _BUILD_STACK_LOCK  # noqa: PLW0603 - the module's one lock is replaced, not shared
    _BUILD_STACK_LOCK = threading.Lock()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_new_build_stack_lock)


def _on_large_stack(build: Callable[[], Any]) -> Any:
    """
    Run ``build`` on a new thread with a large stack, and return its result or raise its exception.

    pydantic-core builds a validator by walking the schema through nested
    calls on the C stack, and the copy nests deeper than the class's own
    schema because of its wrappers. A chain of a few hundred nested models
    overflows a small stack and ends the process, with no Python exception
    to catch. The first call to a class builds its copy, so the build runs
    on whatever thread serves that request, and that thread's stack can be
    small: Windows gives a thread 1 MB, and a thread that Python did not
    start keeps the size its creator chose. Running the build on a thread
    with a fixed large stack makes the depth of class it handles the same
    everywhere. The build runs once per class, so the extra thread costs
    little; checking a value with the copy runs on the caller's thread.
    """
    outcome: list[Any] = []

    def run() -> None:
        try:
            outcome.append((True, build()))
        except BaseException as error:  # noqa: BLE001 - handed to the calling thread, which raises it
            outcome.append((False, error))

    # The same context as the caller, so the build sees what it would see there.
    context = contextvars.copy_context()
    try:
        # The stack size applies to every thread the process starts while it
        # is set, so it is put back right after this start. Another thread
        # started in this short window also gets the large stack.
        with _BUILD_STACK_LOCK:
            previous = threading.stack_size(_BUILD_STACK_BYTES)
            try:
                worker = threading.Thread(target=context.run, args=(run,), name="citry-validator-build", daemon=True)
                worker.start()
            finally:
                threading.stack_size(previous)
    except (RuntimeError, ValueError):
        # A platform without threads, or without a settable stack size (such
        # as Pyodide), builds on the calling thread, as Pydantic itself does.
        return build()
    worker.join()
    succeeded, value = outcome[0]
    if not succeeded:
        raise value
    return value


def _build(schema: _Schema, *, wrapped: bool, by_name: bool = False, text_wrappers: bool = False) -> Any:
    def build() -> Any:
        rewriter = _Rewriter(schema, wrapped=wrapped, by_name=by_name, text_wrappers=text_wrappers)
        copied = rewriter.rewrite(schema.root)
        return pydantic_core.SchemaValidator(copied, _top_config(schema.root), _use_prebuilt=False)

    # The rewrite builds validators too, for the labels of union members.
    return _on_large_stack(build)


def checker_for(cls: type, *, state: bool = False, by_name: bool = False, repeated: bool = False) -> Checker | None:
    """
    Return the checker for a Pydantic v2 class's data, built on first use, or ``None`` when it has no core schema.

    ``None`` means an unfinished class: the caller keeps its own validator
    with the path limit (``pydantic_can_report``).

    Args:
        cls: The class.
        state: The class is a State. Only the fields the browser may write
            are checked at registration, so a part outside them that Citry
            could not check does not refuse calls.
        by_name: Build the copy that reads keys by field name only, for
            browser writes to a model State (see ``_Rewriter``).
        repeated: Build the copy for a check that may run again for the
            same value (see ``repeated_checks``). It always has the
            wrappers, and each check that parses text spends for it.

    """
    store = _CHECKERS[(state, by_name, repeated)]
    cached = store.get(cls)
    if cached is not None:
        return cached
    if not SUPPORTED:
        checker = Checker(None, wrapped=False, refusal=_OLD_PYDANTIC_REFUSAL)
        return _remember(store, cls, checker, complete=True)
    root = core_schema_of(cls)
    if root is None:
        return None
    schema = _Schema(root)
    common: dict[str, Any] = {"reads_json": schema.reads_json(), "longest_message": schema.longest_message()}
    complete = getattr(cls, "__pydantic_complete__", True)
    v1_class = None if state else pydantic_v1_model_in(root)
    if v1_class is not None:
        # Registration refuses this in a `data` class it can read; this
        # catches one completed later, or met inside a plain `data` class
        # behind a forward reference. The v1 check never runs on the data.
        refusal = (
            f"It holds the pydantic.v1 class {v1_class.__qualname__}, and Events checks event data with"
            f" dataclasses, annotated classes and Pydantic v2 models only. Make {v1_class.__qualname__} a Pydantic"
            " v2 model."
        )
        checker = Checker(None, wrapped=False, refusal=refusal, **common)
        return _remember(store, cls, checker, complete=complete)
    found = None if state else _unbounded_field(schema, root, _WRAPPED)
    if found is not None:
        # Registration refuses such a class when its schema is complete then;
        # this catches one that was completed later, or one that registration
        # does not see, such as a Pydantic class inside a plain `data` class.
        name, reason = found
        where = f"Its field {name!r}" if name else "It"
        refusal = f"{where} holds a Json[...] value with {reason}. {_fix_for(reason)} You can also {_PLAIN_TYPE_FIX}."
        checker = Checker(None, wrapped=False, refusal=refusal, **common)
        return _remember(store, cls, checker, complete=complete)
    try:
        # Without wrappers nothing forgets the by-name setting, so that copy keeps its aliases.
        if repeated:
            validator = _build(schema, wrapped=True, by_name=by_name, text_wrappers=True)
            checker = Checker(validator, wrapped=True, **common)
        elif _needs_no_wrappers(schema, common["longest_message"]):
            checker = Checker(_build(schema, wrapped=False), wrapped=False, **common)
        else:
            checker = Checker(_build(schema, wrapped=True, by_name=by_name), wrapped=True, **common)
    except Exception:  # noqa: BLE001 - a call must never fail because the copy could not be built
        logger.exception(
            f"Citry could not build its copy of the validator for {cls.__qualname__}. It falls back to a simpler"
            " copy that stops each list and dict at its first bad item and limits the total length of field"
            " paths, or refuses the calls when that copy cannot check the class. Check that"
            f" {cls.__qualname__} builds with the installed Pydantic, and report the traceback below as a bug."
        )
        checker = _fallback(cls, schema, common)
    return _remember(store, cls, checker, complete=complete)


class FieldsCheck(NamedTuple):
    """The copy of a Pydantic dataclass's field checks, and two facts that decide how a write is checked."""

    # The copied validator of the class's fields, with the counting wrappers.
    validator: Any
    # Whether some validator of the class takes `info`, and so may read the
    # fields declared before its own as `info.data`, or some
    # `default_factory` takes the fields checked so far.
    reads_other_fields: bool
    # Whether building the class does more than check each field on its
    # own: a model validator, `__post_init__`, or a check that reads other
    # fields. Only then can the whole State refuse values that each
    # passed its field check.
    checks_across_fields: bool


# The copy of each Pydantic dataclass's field checks, or ``None`` when Citry
# could not build one (see `fields_checker_for`).
_FIELDS_CHECKERS: WeakKeyDictionary[type, FieldsCheck | None] = WeakKeyDictionary()


def fields_checker_for(cls: type) -> FieldsCheck | None:
    """
    Return a copy of a Pydantic dataclass's field checks, or ``None`` when Citry cannot build one.

    It is the class's validator without its model validators and
    ``__post_init__``: the part that checks each field, with the counting
    wrappers. ``validate_field`` assigns one browser write through it, so a
    write is checked within the request's limits on its own, while a field
    validator still sees the fields declared before its own
    (``info.data``) and its own name (``info.field_name``), as it does
    when the class is built.

    The copy does not refuse a write to a field marked
    ``Field(frozen=True)``: the class takes that assignment too, since it
    applies ``frozen=True`` only with ``validate_assignment``.
    """
    if cls in _FIELDS_CHECKERS:
        return _FIELDS_CHECKERS[cls]
    root = core_schema_of(cls)
    found = None if root is None else _dataclass_fields_schema(root)
    check = None
    if found is not None:
        node, config, wrapped = found
        # Every field is copied without `frozen=True` (see above).
        unfrozen = {
            **node,
            "fields": [
                {key: item for key, item in entry.items() if key != "frozen"} if type(entry) is dict else entry
                for entry in node.get("fields", ())
            ],
        }

        def build() -> Any:
            copied = _Rewriter(_Schema(root), wrapped=True).rewrite(unfrozen)  # type: ignore[arg-type]
            return pydantic_core.SchemaValidator(copied, config, _use_prebuilt=False)

        try:
            # A large stack, as for the copy of a whole class (see `_on_large_stack`).
            validator = _on_large_stack(build)
        except Exception:  # noqa: BLE001 - the caller then refuses the write, as for a class it cannot copy
            logger.exception(f"Citry could not build its copy of the field checks of {cls.__qualname__}.")
        else:
            reads = _reads_other_fields(root)  # type: ignore[arg-type]
            check = FieldsCheck(validator, reads, checks_across_fields=reads or wrapped)
    with _LOCK:
        _FIELDS_CHECKERS.setdefault(cls, check)
    return _FIELDS_CHECKERS[cls]


def _dataclass_fields_schema(root: dict[str, Any]) -> tuple[dict[str, Any], Any, bool] | None:
    """
    Return the schema that checks a Pydantic dataclass's fields, its config, and one more fact, or ``None``.

    The third item is true when a model validator (before, after or wrap)
    or ``__post_init__`` runs when the class is built.
    """
    definitions = _definitions(root)
    node: Any = root
    config = _top_config(root)
    wrapped = False
    # Model validators wrap the dataclass schema, and a class that refers to
    # itself is a reference to its own definition.
    while _kind(node) in (
        "definitions",
        "definition-ref",
        "dataclass",
        "function-before",
        "function-after",
        "function-wrap",
    ):
        if _kind(node) == "dataclass":
            wrapped = wrapped or bool(node.get("post_init"))
            if type(node.get("config")) is dict:
                config = node["config"]
        elif _kind(node) in ("function-before", "function-after", "function-wrap"):
            wrapped = True
        node = definitions.get(str(node.get("schema_ref"))) if _kind(node) == "definition-ref" else node.get("schema")
    if _kind(node) != "dataclass-args":
        return None
    return node, config, wrapped


def _reads_other_fields(root: dict[str, Any]) -> bool:
    """
    Return whether any check in ``root`` may read fields other than its own.

    That is a validator that takes Pydantic's ``info`` argument, which reads
    the earlier fields as ``info.data``, or a ``default_factory`` that takes
    the fields checked so far as its argument.
    """
    # A check inside a nested class reads that class's fields, not the
    # State's, but telling them apart is not worth the risk: a State with
    # one is treated as reading other fields.
    stack: list[Any] = [root]
    while stack:
        node = stack.pop()
        if type(node) is dict:
            function = node.get("function")
            if type(function) is dict and function.get("type") == "with-info":
                return True
            if node.get("default_factory_takes_data") is True:
                return True
            stack.extend(node.values())
        elif type(node) in (list, tuple):
            stack.extend(node)
    return False


def validate_field(validator: Any, earlier: dict[str, Any], name: str, value: Any) -> Any:
    """
    Check one write to a Pydantic dataclass field with a copy from ``fields_checker_for``, and return its value.

    ``earlier`` holds the fields declared before ``name``, which a field
    validator reads as ``info.data``, as when the class is built. The check
    runs inside the running validation's limits and returns the checked
    value, which a later write of the batch then sees in ``info.data``.
    """
    with _counting(Checker(validator, wrapped=True), value):
        result = validator.validate_assignment(dict(earlier), name, value)
    # pydantic-core hands back the fields given with the checked value in
    # them, and the extra values.
    return result[0][name]


def json_checker_for(cls: type) -> Checker | None:
    """
    Return the checker for JSON text against a Pydantic v2 class: the copy for JSON text.

    It stops collections early, and holds wrappers only at and below a wrap
    validator. The caller applies the path limit too (``needs_path_limit``)
    when no Python check ran first, and Citry refuses at registration a
    class whose writable fields reach a part this copy cannot check within
    its limits (see ``_Schema.unbounded_reason``).
    """
    cached = _JSON_CHECKERS.get(cls)
    if cached is not None:
        return cached
    if not SUPPORTED:
        checker = Checker(None, wrapped=False, refusal=_OLD_PYDANTIC_REFUSAL)
        return _remember(_JSON_CHECKERS, cls, checker, complete=True)
    root = core_schema_of(cls)
    if root is None:
        return None
    schema = _Schema(root)
    common: dict[str, Any] = {"reads_json": schema.reads_json(), "longest_message": schema.longest_message()}
    try:
        checker = Checker(_build(schema, wrapped=False), wrapped=False, needs_path_limit=True, **common)
    except Exception:  # noqa: BLE001 - a call must never fail because the copy could not be built
        logger.exception(
            f"Citry could not build its copy of the validator for {cls.__qualname__}, so it refuses browser"
            f" writes to it. Check that {cls.__qualname__} builds with the installed Pydantic, and report the"
            " traceback below as a bug."
        )
        checker = Checker(None, wrapped=False, refusal=_NOT_COPIED_REFUSAL, **common)
    return _remember(_JSON_CHECKERS, cls, checker, complete=getattr(cls, "__pydantic_complete__", True))


# The context the whole copy starts in, for a Python-mode check and for JSON text.
_WRAPPED: _Context = (True, False)
_UNWRAPPED: _Context = (False, False)
# Where no wrapper can count them, typed extra keys are accepted only when
# their value fails with at most one error, whose message is at most this long.
_LONG_EXTRA_MESSAGE = 256
# Why a part cannot be checked where no wrapper can count it, for the
# messages at registration. Each reason has its fix in `_fix_for`.
_UNION_REASON = (
    "a union without a discriminator inside a recursive type, where two or more members hold more of the tree"
    " (as in And | Or | Cond, where And and Or hold more nodes)"
)
# The same union, when some members are not classes (a list or a tuple), so
# a Literal tag field cannot be added to every member.
_MIXED_UNION_REASON = (
    "a union without a discriminator inside a recursive type, where two or more members hold more of the tree"
    " (as in Node = list[Node] | tuple[Node, ...] | int)"
)
_CHAIN_REASON = "a chain of validators inside a recursive type, where two or more of them check the tree"
_LAX_OR_STRICT_REASON = "a recursive type with separate strict and lax checks, both of which check the tree"
_REPEAT_REASONS = {"chain": _CHAIN_REASON, "lax-or-strict": _LAX_OR_STRICT_REASON}
_EXTRAS_REASON = (
    "extra keys that the class allows and gives a type, whose values can fail with more than one error or with"
    " a message that lists many values (a model, a list or dict, a union of several types, or a Literal or"
    " Enum with many or long values)"
)
_DISCARDED_EXTRAS_REASON = (
    "extra keys that the class allows and gives a type, whose values can fail with more than one error or with"
    " a message that lists many values (a model, a list or dict, a union of several types, or a Literal or"
    " Enum with many or long values), inside a union member, an OnErrorOmit item or another default used"
    " when the value fails, or a custom error"
)
_KEYED_ITEMS_REASON = (
    "a wrap validator around it, and a list or dict inside a dict in that text whose items are not plain JSON values"
)
_WRAPPED_ITEMS_REASON = (
    "a wrap validator around it, and inside it a list or dict whose items can each fail with several errors"
    " or with a message that lists many values (such as a model, a union of several types, or a Literal or"
    " Enum with many or long values)"
)


def _needs_no_wrappers(schema: _Schema, longest_message: int) -> bool:
    """Whether the schema's worst case is small and fixed, so the copy needs ``fail_fast`` and nothing else."""
    try:
        bound = schema.error_bound()
    except RecursionError:
        # A schema deeper than Python's recursion limit gets the wrappers,
        # which work without a fixed error count.
        return False
    if bound is None:
        return False
    # A key the payload chooses lands in each error's path, and can be as
    # long as the request, so the bound must stay at the limit's floor.
    if schema.keys_from_payload():
        return bound <= MIN_ERRORS
    return (
        bound <= _FIXED_ERRORS_WITHOUT_WRAPPERS
        and bound * (longest_message + _ERROR_OVERHEAD) <= ERROR_TEXT_BUDGET // 4
    )


def _fallback(cls: type, schema: _Schema, common: dict[str, Any]) -> Checker:
    """Return the checker used when the wrapped copy cannot be built: ``fail_fast`` and the path limit."""
    # This rare path does not know which fields of a State the browser may
    # write, so any part of the class that it cannot check refuses calls.
    if schema.unbounded_reason(schema.root, _UNWRAPPED) is not None:
        # This copy has wrappers only below wrap validators, so nothing else
        # would count errors or work for such a part.
        return Checker(None, wrapped=False, refusal=_NOT_COPIED_REFUSAL, **common)
    try:
        return Checker(_build(schema, wrapped=False), wrapped=False, needs_path_limit=True, **common)
    except Exception:  # noqa: BLE001 - the last resort refuses rather than runs unchecked
        logger.exception(
            f"Citry could not build the simpler copy of the validator for {cls.__qualname__} either, so it"
            " refuses calls to it. Report the traceback below as a bug."
        )
        return Checker(None, wrapped=False, refusal=_NOT_COPIED_REFUSAL, **common)


def _remember(store: WeakKeyDictionary[type, Checker], cls: type, checker: Checker, *, complete: bool) -> Checker:
    # An unfinished class may still change, so its checker is not kept.
    if not complete:
        return checker
    with _LOCK:
        return store.setdefault(cls, checker)


def log_refusal(cls: type, checker: Checker) -> None:
    """Log once per class why its calls are refused, so the app author can tell this from bad data."""
    if checker.logged:
        return
    checker.logged = True
    logger.error(f"Citry refuses data for {cls.__qualname__}. {checker.refusal}")


# The reasons already logged for each class, so each is logged once.
_WARNED_WORK: WeakKeyDictionary[type, frozenset[str]] = WeakKeyDictionary()


def warn_if_stopped(cls: type, stop: ValidationTooCostly) -> None:
    """
    Warn once per class when a check stopped for work, CPU time or call depth.

    Stay quiet when it stopped for too many errors, because the client sent
    bad data. Every place that catches a stop calls this one function, so
    each applies the same rule.
    """
    if stop.reason != "errors":
        warn_work_spent(cls, stop.reason)


def warn_work_spent(cls: type, reason: str = "work", *, refused: bool = True) -> None:
    """
    Warn once per class and kind that a call ran out of work, CPU time or call depth (``reason``), naming the fix.

    Pass ``refused=False`` for a browser write to a Pydantic v1 State whose
    check finished before Citry could stop it. Citry reads the clock once
    for every few hundred values a v1 model checks (see
    ``guarding_pydantic_v1``), so a check that spends its time inside one
    validator function ends with the time gone. The warning then says the
    request's later checks may be refused.

    With ``refused=True``, a v1 model gets its own advice, because Citry
    checks it with Pydantic's own validator.
    """
    # A refused check and one that finished past the time give different
    # advice, so each gets its own once-per-class key.
    key = reason if refused else f"{reason}-finished"
    with _LOCK:
        warned = _WARNED_WORK.get(cls, frozenset())
        if key in warned:
            return
        _WARNED_WORK[cls] = warned | {key}
    if reason == "depth":
        # No traceback: it would list every frame, and any client can send
        # such data again.
        logger.warning(
            f"Data for {cls.__qualname__} was refused because checking it needs more levels of Python calls than"
            " Python allows. This usually means the browser sent deeply nested data. If the data is not deeply"
            " nested, a validator or __post_init__ of the class may be calling itself without end."
        )
        return
    if not refused:
        logger.warning(
            f"A browser write to the State {cls.__qualname__} used up the CPU time Citry allows one request"
            f" (about {WORK_SECONDS:g} second), and the check ended before Citry could stop it, so the request's"
            " later checks may be refused. Citry reads the clock once for every"
            f" {_V1_VALUES_PER_CLOCK_READ} values a Pydantic v1 model checks, so a slow validator function of the"
            " model is the likely cause. Make that validator cheaper, or use a Pydantic v2 model when the browser"
            " sends large or nested data."
        )
        return
    if is_pydantic_v1_class(cls):
        # Citry checks a v1 model with Pydantic's own validator, so the advice
        # is a discriminator on a union that holds a tree, or a Pydantic v2
        # model, which Citry checks faster.
        logger.warning(
            f"Data for {cls.__qualname__} was refused because checking it, with the checks before it in the"
            " request, used up the work or CPU time Citry allows one request (about"
            f" {WORK_SECONDS:g} second of CPU time). If valid data nests deeply, give the union that holds the tree"
            ' a discriminator, as in Field(..., discriminator="type") with a Literal "type" field on each member.'
            " Otherwise use a Pydantic v2 model when the browser sends large or nested data, or send less data per"
            " call."
        )
        return
    # Citry's own check of a plain class or dataclass does not read
    # discriminators, so the advice depends on what the class is.
    if is_pydantic_v2_class(cls):
        advice = (
            "put the discriminator on the recursive type, such as Node = Annotated[And | Or | Cond,"
            ' Field(discriminator="type")] with a Literal "type" field on each member, or use a callable'
            " Discriminator with a Tag on each member"
        )
    else:
        advice = (
            "make the recursive classes Pydantic models and put the discriminator on the recursive type, such as"
            ' Node = Annotated[And | Or | Cond, Field(discriminator="type")] with a Literal "type" field on each'
            " member, because Citry checks a plain class or dataclass itself, without reading discriminators"
        )
    if reason == "time":
        # Time runs out on a slow or busy server too, so the log names the
        # cause, and the advice applies only when the data is deep.
        logger.warning(
            f"Data for {cls.__qualname__} was refused because checking it used more CPU time than Citry allows"
            f" one request (about {WORK_SECONDS:g} s). If valid data nests deeply, {advice}. Otherwise send less"
            " data per call."
        )
        return
    logger.warning(
        f"Data for {cls.__qualname__} was refused because checking it took more work than Citry allows one"
        f" request: the data is large, or nests deeply. If valid data nests this deeply, {advice}. Otherwise"
        " send less data per call."
    )


################################################
# RUNNING THE COPY
################################################


@contextmanager
def _counting(checker: Checker, payload: Any) -> Iterator[_Tally]:
    """Run inside the validation's tally, and add each failed call's errors to it."""
    with validation_scope(payload):
        tally = _current_tally()
        assert tally is not None  # noqa: S101 - validation_scope just set it
        tally.strings_hold_keys = tally.strings_hold_keys or checker.reads_json
        tally.longest_message = max(tally.longest_message, checker.longest_message)
        before = tally.errors
        try:
            yield tally
        except pydantic_core.ValidationError as err:
            # A copy without wrappers counts here, after the call. A wrapped
            # copy's outer object already set the same total.
            tally.errors = before + err.error_count()
            tally.check()
            raise
        except RecursionError:
            # Very deep data can run out of Python frames inside the copy. It
            # gets the same answer as data nested too deeply to check.
            raise ValidationTooCostly("depth") from None


def validate_python(checker: Checker, payload: Any, **options: Any) -> Any:
    """Check ``payload`` (JSON-decoded values) with the copy, in Python mode."""
    with _counting(checker, payload):
        return checker.validator.validate_python(payload, **options)


def validate_init(checker: Checker, cls: type, values: dict[str, Any]) -> Any:
    """Build a Pydantic dataclass from keyword values with the copy, as its ``__init__`` would."""
    # The class's own `__init__` fills an instance Python already made. A
    # strict dataclass accepts only that form: given the keyword values
    # alone, it asks for an instance of the class.
    # `cls.__new__`, as Python itself calls it, so a class's own `__new__` runs too.
    instance = cast("Any", cls).__new__(cls)
    with _counting(checker, values):
        checker.validator.validate_python(pydantic_core.ArgsKwargs((), values), self_instance=instance)
    return instance


def validate_assignment(checker: Checker, instance: Any, name: str, value: Any) -> None:
    """Check and set one field of a Pydantic dataclass with the copy, as its ``validate_assignment`` would."""
    with _counting(checker, value):
        checker.validator.validate_assignment(instance, name, value)


def validate_json(checker: Checker, text: str, payload: Any, **options: Any) -> Any:
    """
    Check JSON text with the copy for JSON text, in JSON mode.

    ``payload`` is the same data decoded, which sets the error limit when a
    wrapper below a wrap validator counts a failure.
    """
    with _counting(checker, payload):
        return checker.validator.validate_json(text, **options)


################################################
# REGISTRATION CHECKS
################################################


def is_pydantic_v2_class(cls: Any) -> bool:
    """Whether ``cls`` is a Pydantic v2 model or Pydantic dataclass, which has a core schema."""
    return isinstance(cls, type) and hasattr(cls, "__pydantic_validator__") and hasattr(cls, "__pydantic_fields__")


def is_pydantic_v1_class(cls: Any) -> bool:
    """Whether ``cls`` is a Pydantic v1 model, such as a subclass of ``pydantic.v1.BaseModel``."""
    # A v2 model also has a `__fields__` attribute (deprecated, and reading it
    # warns), so the v2 test comes first.
    return (
        isinstance(cls, type)
        and not is_pydantic_v2_class(cls)
        and isinstance(getattr(cls, "__fields__", None), dict)
        and hasattr(cls, "__config__")
    )


def is_pydantic_v1_dataclass(cls: Any) -> bool:
    """Whether ``cls`` is a ``pydantic.v1`` dataclass, which keeps a v1 model in ``__pydantic_model__``."""
    return isinstance(cls, type) and is_pydantic_v1_class(cls.__dict__.get("__pydantic_model__"))


# How many values a Pydantic v1 check reads between two reads of the clock.
# A read for every value would slow each check, and this many values take
# well under a millisecond.
_V1_VALUES_PER_CLOCK_READ = 256

# How many Citry checks have the `pydantic.v1` hooks in place right now, and
# the functions the hooks replaced. The hooks stay in place only while at
# least one check needs them (see `guarding_pydantic_v1`).
_v1_hook_users = 0
_v1_originals: tuple[Any, Any, Any, Any] | None = None
_V1_HOOK_LOCK = threading.Lock()


@contextmanager
def guarding_pydantic_v1() -> Iterator[None]:
    """
    Make the Pydantic v1 checks inside this block count their errors, and stop when the request's CPU time is gone.

    Citry cannot give a Pydantic v1 model a copy of its validator the way it
    does for a v2 class, so while one of its validations runs (see
    ``validation_scope``), it hooks two places in ``pydantic.v1`` that
    every v1 check passes through. This covers a browser write to a v1
    State, and a v1 check that a validator of the author calls, which
    Citry cannot see:

    - The error wrapper's constructor, which every error goes through. A v1
      model can build many errors from a small payload, so Citry counts
      them as they are built. Each error adds to the validation's error
      total, and the check ends once the total passes the error limit. A wrapper around a nested
      model's whole ``ValidationError`` is not counted, since the errors
      inside it were counted when they were built.
    - The check of one value. Once a value passes, any errors counted while
      checking it were thrown away: a union tries its members in turn and
      drops the errors of the ones that fail when a later one accepts the
      value, and a validator of the author that runs for each item may
      build an error and catch it. So those errors leave the total again.
      The check also reads the clock once for every
      ``_V1_VALUES_PER_CLOCK_READ`` values, so a check that runs long, such
      as a union that checks the same large list again at each level of a
      tree, ends with the request's other checks when the CPU time is gone.

    Both stop the check with an error that is not a ``ValueError``, so v1
    does not catch it.

    The hooks go in when the first such block starts and come out when the
    last one ends, so outside these blocks ``pydantic.v1`` runs its own
    functions, at its own speed and with its own call depth. While a block
    runs, v1 code in another thread passes through the hooks too. Code
    outside any Citry validation finds no error total there (one context
    variable read) and calls the original function, which costs one more
    Python call per value and per error, for that time only. A Citry
    validation in that thread has its own block, so it is counted the same
    way whether or not another thread holds the hooks.

    The hooks read the error total and the clock of the ``validation_scope``
    that the current thread runs in.
    """
    installed = _add_pydantic_v1_hooks()
    try:
        yield
    finally:
        if installed:
            _remove_pydantic_v1_hooks()


def _add_pydantic_v1_hooks() -> bool:
    """Put the hooks in, or count one more user of hooks already in place; return whether they are in place."""
    global _v1_hook_users, _v1_originals  # noqa: PLW0603 - the one place that puts the hooks in
    errors_module = sys.modules.get("pydantic.v1.error_wrappers")
    fields_module = sys.modules.get("pydantic.v1.fields")
    # Only a loaded v1 model can be checked, and it loaded both modules.
    if errors_module is None or fields_module is None or not hasattr(fields_module, "ModelField"):
        return False
    with _V1_HOOK_LOCK:
        if _v1_hook_users == 0:
            wrapper, container = errors_module.ErrorWrapper, errors_module.ValidationError
            field = fields_module.ModelField
            original_init = wrapper.__dict__["__init__"]
            original_singleton = field.__dict__["_validate_singleton"]

            def counted_init(self: Any, exc: Exception, loc: Any) -> None:
                original_init(self, exc, loc)
                tally = _TALLY.get()
                if tally is not None and not isinstance(exc, container):
                    tally.errors += 1
                    tally.check()

            def guarded_singleton(self: Any, v: Any, values: Any, loc: Any, cls: Any) -> Any:
                tally = _TALLY.get()
                if tally is None:
                    # Another thread's check, or one that Citry did not start: run it as v1 would.
                    return original_singleton(self, v, values, loc, cls)
                tally.values_read += 1
                if tally.values_read % _V1_VALUES_PER_CLOCK_READ == 0 and tally.budget is not None:
                    tally.budget.spend_time(0)
                before = tally.errors
                result = original_singleton(self, v, values, loc, cls)
                if result[1] is None:
                    # The value passed, so every error counted while checking it
                    # was thrown away, and the errors leave the total.
                    tally.errors = before
                return result

            wrapper.__init__ = counted_init
            field._validate_singleton = guarded_singleton
            _v1_originals = (wrapper, original_init, field, original_singleton)
        _v1_hook_users += 1
    return True


def _remove_pydantic_v1_hooks() -> None:
    """Count one user less, and put ``pydantic.v1``'s own functions back once no check needs the hooks."""
    global _v1_hook_users, _v1_originals  # noqa: PLW0603 - the one place that takes the hooks out
    with _V1_HOOK_LOCK:
        _v1_hook_users -= 1
        if _v1_hook_users or _v1_originals is None:
            return
        wrapper, original_init, field, original_singleton = _v1_originals
        wrapper.__init__ = original_init
        field._validate_singleton = original_singleton
        _v1_originals = None


def pydantic_v1_model_in(root: dict[str, Any]) -> type | None:
    """
    Return the first ``pydantic.v1`` class that a Pydantic v2 core schema runs on its data, or ``None``.

    Pydantic v2 checks a field typed as a v1 model or v1 dataclass by
    calling that class's v1 ``validate`` method with an argument it does
    not take, so the field always fails with a ``TypeError``. A field may
    also name a method of a v1 class as its own validator, as in
    ``PlainValidator(Model.parse_obj)``, which runs a v1 check on the data.
    Both are found here. A validator that calls a v1 class from inside its
    own code, such as a lambda, cannot be seen here. A field written
    ``InstanceOf[Model]`` calls ``validate`` only in the branch that reads
    JSON. Citry checks event data as Python values, so that branch never
    runs, except inside a ``Json[...]`` field, which reads what it parsed as
    JSON.
    """
    definitions = _definitions(root)
    # Each node comes with whether a ``Json`` field reads it, because that
    # field validates what it parsed in JSON mode.
    stack: list[tuple[Any, bool]] = [(root, False)]
    seen: set[tuple[int, bool]] = set()
    while stack:
        node, reads_json = stack.pop()
        if (id(node), reads_json) in seen:
            continue
        seen.add((id(node), reads_json))
        if type(node) is dict:
            kind = _kind(node)
            if kind is not None and kind.startswith("function-"):
                owner = _v1_function_owner(node.get("function"))
                if owner is not None:
                    return owner
            elif kind == "definition-ref":
                target = definitions.get(str(node.get("schema_ref", "")))
                if target is not None:
                    stack.append((target, reads_json))
            elif kind == "json-or-python":
                stack.append((node.get("json_schema" if reads_json else "python_schema"), reads_json))
                continue
            elif kind == "json":
                stack.extend((child, True) for child in _children(node))
                continue
        stack.extend((child, reads_json) for child in _children(node))
    return None


def _v1_function_owner(function: Any) -> type | None:
    """Return the ``pydantic.v1`` class that a core schema's validator function is, or is a method of, or ``None``."""
    if type(function) is not dict:
        return None
    method = function.get("function")
    # `functools.partial(Model.parse_obj)` calls the same method.
    while isinstance(method, functools.partial):
        method = method.func
    for candidate in (method, getattr(method, "__self__", None)):
        if is_pydantic_v1_class(candidate) or is_pydantic_v1_dataclass(candidate):
            return cast("type", candidate)
    return None


def check_supported(comp_name: str, cls: Any, role: str, nested: tuple[type, ...] = ()) -> None:
    """
    Refuse a ``data`` or State class that reaches a Pydantic v2 class the installed Pydantic cannot copy.

    ``nested`` holds the Pydantic classes a plain dataclass reaches through
    its fields, which Citry checks with the copy as well, so an older
    Pydantic would refuse every call to them.

    Raises:
        RuntimeError: Pydantic is older than 2.13.0.

    """
    if SUPPORTED:
        return
    found = cls if is_pydantic_v2_class(cls) else next((item for item in nested if is_pydantic_v2_class(item)), None)
    if found is None:
        return
    version = getattr(sys.modules.get("pydantic"), "VERSION", "unknown")
    where = (
        f"the {role} {cls.__qualname__}"
        if found is cls
        else f"the {role} {cls.__qualname__} holds {found.__qualname__}, which"
    )
    msg = (
        f"Component {comp_name}: {where} is a Pydantic class, and Events needs Pydantic"
        f" {REQUIRED_PYDANTIC} or newer for Pydantic classes (installed: {version}). Upgrade Pydantic."
    )
    raise RuntimeError(msg)


def _unbounded_field(
    schema: _Schema,
    root: dict[str, Any],
    context: _Context,
    names: frozenset[str] | None = None,
    *,
    discarded_only: bool = False,
) -> tuple[str | None, str] | None:
    """
    Return the first field (in name order) that holds a part Citry cannot check, and why.

    ``names`` limits the walk to those top-level fields; without it every
    field is read, and then the rest of the class, which gives a ``None``
    name when the part sits outside any field.
    """
    fields = _top_fields(root)
    for name in sorted(fields if names is None else names):
        entry = fields.get(name)
        if entry is None:
            continue
        reason = schema.unbounded_reason(entry, context, discarded_only=discarded_only)
        if reason is not None:
            return name, reason
    if names is None:
        reason = schema.unbounded_reason(root, context, discarded_only=discarded_only)
        if reason is not None:
            return None, reason
    return None


def check_data_class(comp_name: str, cls: Any) -> None:
    """
    Refuse a Pydantic ``data`` class with a part Citry cannot check, when its schema is complete then.

    Raises:
        ValueError: A ``Json[...]`` field holds a part that no wrapper can
            reach and that Citry cannot count (see
            ``_Schema.unbounded_reason``), naming the field and the fix.

    """
    if not is_pydantic_v2_class(cls):
        return
    root = core_schema_of(cls)
    found = None if root is None else _unbounded_field(_Schema(root), root, _WRAPPED)
    if found is None:
        return
    name, reason = found
    where = f"the field {name!r} of the event data class" if name else "the event data class"
    # Outside `Json[...]` the copy counts the same part, so the plain type is a fix too.
    msg = (
        f"Component {comp_name}: {where} {cls.__qualname__} holds a Json[...] value with {reason}."
        f" {_fix_for(reason)} You can also {_PLAIN_TYPE_FIX}."
    )
    raise ValueError(msg)


def _fix_for(reason: str) -> str:
    """Return the usual change that removes a part Citry cannot check, as whole sentences."""
    if reason == _UNION_REASON:
        return (
            "Put the discriminator on the recursive type, such as"
            ' Node = Annotated[And | Or | Cond, Field(discriminator="type")], and give each member a Literal'
            ' "type" field; each node then carries that field, so update browser code that builds nodes. A'
            " callable Discriminator with a Tag on each member works too and needs no new field, when each"
            " member has a field the others lack."
        )
    if reason == _MIXED_UNION_REASON:
        return (
            "Give the recursive type a callable Discriminator with a Tag on each member, which picks the member"
            " from the value, such as Discriminator(lambda v: 'list' if isinstance(v, list) else ...)."
        )
    if reason == _CHAIN_REASON:
        return "Apply only one validator that checks the recursive type."
    if reason == _LAX_OR_STRICT_REASON:
        return "Give the recursive type one check for both strict and lax mode."
    if reason == _DISCARDED_EXTRAS_REASON:
        return (
            "Give the extra keys a type that fails with one short message, such as int or str, or move them out"
            " of that union member, OnErrorOmit item or custom error."
        )
    if reason == _WRAPPED_ITEMS_REASON:
        return (
            "Use one type for the items (and a dict's keys and values) that fails with one short message, such"
            " as int, str, date or a short Literal, not a union of several types. A union with None is fine, and"
            " so is a union of int, float, str and bool. Or put the wrap validator inside the Json[...], as in"
            " Json[Annotated[list[Item], WrapValidator(...)]]; your validator then does not run when the text"
            " is not valid JSON."
        )
    if reason == _KEYED_ITEMS_REASON:
        return (
            "Give those items a plain JSON type, such as int, float, str, bool or a Literal of those, or put the"
            " wrap validator inside the Json[...]; your validator then does not run when the text is not valid"
            " JSON."
        )
    return "Give the extra keys a type that fails with one short message, such as int or str."


# The other fixes the messages offer, after the one for the reason.
_PLAIN_TYPE_FIX = "declare the field as the type itself instead of Json[...]"
_LEAVE_OUT_FIX = "set _model to the fields the browser may change, without {name!r}"


_WRITE_MODES: WeakKeyDictionary[type, str] = WeakKeyDictionary()


def state_write_mode(cls: type) -> str:
    """Return ``"python"`` when browser writes to a model State can be checked in Python mode, else ``"json"``."""
    cached = _WRITE_MODES.get(cls)
    if cached is not None:
        return cached
    root = core_schema_of(cls)
    if root is None:
        return "json"
    mode = "json" if _Schema(root).json_mode_differs() is not None else "python"
    with _LOCK:
        return _WRITE_MODES.setdefault(cls, mode)


def check_state_class(comp_name: str, cls: Any, writable: frozenset[str]) -> None:
    """
    Refuse a Pydantic v2 State class that runs a ``pydantic.v1`` check, or has a writable part Citry cannot check.

    A field anywhere in the State that is typed as a ``pydantic.v1`` class,
    or checked with a method of one (see ``pydantic_v1_model_in``), is
    refused, as in a ``data`` class: Citry restores every field from the
    token without the ``pydantic.v1`` hooks, and the token can hold values
    the browser wrote. A State that is itself a ``pydantic.v1`` model is
    not a v2 class, so it passes here.

    For the rest, only the fields the browser may write (``_model``) are
    read: the server writes the others. The walk reads three kinds of part,
    each with the rules of ``_Schema.unbounded_reason``:

    - A ``Json[...]`` field, in any Pydantic State.
    - Every field of a model State that pydantic-core reads differently from
      JSON and from Python (see ``_Schema.json_mode_differs``), which Citry
      checks only by reading the writes as JSON.
    - The JSON read of any other model State, which runs after Citry's
      Python check has accepted the writes. Here extra keys with a type
      count only below a union member or another part whose errors are
      thrown away.

    Raises:
        ValueError: The State holds a ``pydantic.v1`` class, or has a
            writable field Citry cannot check; the message names it and the
            fix.

    """
    if not is_pydantic_v2_class(cls):
        return
    root = core_schema_of(cls)
    if root is None:
        # The class is not finished yet; the first browser write checks it
        # once it is (see `state_refusal`). With no writable field, every
        # token holds only values the server wrote.
        if writable:
            with _LOCK:
                _PENDING_STATES[cls] = (comp_name, writable)
        return
    v1_class = pydantic_v1_model_in(root)
    if v1_class is not None:
        msg = (
            f"Component {comp_name}: the State class {cls.__qualname__} holds {v1_class.__qualname__}, which is a"
            " pydantic.v1 model or dataclass. Events checks the fields of a Pydantic v2 State with dataclasses,"
            f" annotated classes and Pydantic v2 models only. Make {v1_class.__qualname__} a Pydantic v2 model."
        )
        raise ValueError(msg)
    if not writable:
        return
    schema = _Schema(root)
    found = _unbounded_field(schema, root, _WRAPPED, writable)
    if found is not None:
        name, reason = found
        # The plain type is not offered: a model State refuses some of these
        # parts outside `Json[...]` too, and the browser cannot write a class
        # to a dataclass State field. The `_model` fix also works for a State
        # that never set it: then every public field is writable.
        msg = (
            f"Component {comp_name}: the writable field {name!r} of the State {cls.__qualname__} holds a"
            f" Json[...] value with {reason}. {_fix_for(reason)} You can also {_LEAVE_OUT_FIX.format(name=name)}."
        )
        raise ValueError(msg)
    if not hasattr(cls, "model_fields"):
        # A Pydantic dataclass State is checked in Python mode only.
        return
    why = schema.json_mode_differs()
    found = _unbounded_field(schema, root, _UNWRAPPED, writable, discarded_only=why is None)
    if found is None:
        return
    name, reason = found
    if why is None:
        msg = (
            f"Component {comp_name}: the writable field {name!r} of the Pydantic model State {cls.__qualname__}"
            f" holds {reason}. {_fix_for(reason)} You can also {_LEAVE_OUT_FIX.format(name=name)}."
        )
    else:
        # Reading the State as Python values instead fixes only the extra
        # keys: a lax State refuses such a union too.
        mode = f"remove {why}, or " if reason == _EXTRAS_REASON else ""
        msg = (
            f"Component {comp_name}: Citry reads browser writes to the State {cls.__qualname__} only as JSON,"
            f" because it has {why}, and its writable field {name!r} holds {reason}. {_fix_for(reason)} You"
            f" can also {mode}{_LEAVE_OUT_FIX.format(name=name)}."
        )
    raise ValueError(msg)


# State classes whose schema was unfinished at registration, with the
# component name and writable fields to check them against later, and the
# refusals found once they were finished.
_PENDING_STATES: WeakKeyDictionary[type, tuple[str, frozenset[str]]] = WeakKeyDictionary()
_STATE_REFUSALS: WeakKeyDictionary[type, str] = WeakKeyDictionary()


def state_refusal(cls: type) -> str | None:
    """
    Return why browser writes to a State are refused, for a State whose schema was unfinished at registration.

    Registration could not read such a class, so the first write after the
    class is finished runs the registration check, logs a refusal once, and
    keeps it for later writes. ``None`` means the writes may go on.
    """
    pending = _PENDING_STATES.get(cls)
    if pending is None:
        return _STATE_REFUSALS.get(cls)
    if core_schema_of(cls) is None:
        # Still unfinished: Pydantic itself refuses to check the write.
        return None
    comp_name, writable = pending
    try:
        check_state_class(comp_name, cls, writable)
    except ValueError as err:
        reason: str | None = str(err)
    else:
        reason = None
    with _LOCK:
        _PENDING_STATES.pop(cls, None)
        if reason is not None and cls not in _STATE_REFUSALS:
            _STATE_REFUSALS[cls] = reason
            logger.error(f"Citry refuses browser writes to {cls.__qualname__}. {reason}")
    return _STATE_REFUSALS.get(cls)
