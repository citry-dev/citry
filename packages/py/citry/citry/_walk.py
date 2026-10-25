"""
Run a recursive walk without one Python call per level.

A walker that would call itself once per nested level is written as a
generator. Where it would call itself, it yields
``Call(function, *args, **kwargs)`` instead, naming the walker to run and
its arguments, and the yield expression gives back what the call
returned::

    def depth(node):
        best = 0
        for child in node.children:
            best = max(best, (yield Call(depth, child)))
        return best + 1

    run(depth(root))

`run` keeps the running generators on a list, so the number of Python
frames stays the same however deep the walk goes. A walker can also yield
values that are not a `Call`. `walk` passes each one to whoever reads it and
sends that reader's reply back to the walker; `run` raises `TypeError` for
them.

The driver keeps the behavior of the recursive version:

- An exception raised in a child is thrown into its caller at the
  ``yield Call(...)``, so a ``try``/``except`` around the call still sees it.
  So is an exception raised while starting the child.
- An exception the reader of `walk` throws into it reaches the walker that
  yielded the value, as it would through a ``yield from`` chain.
- When the reader of `walk` stops early, the walkers still running are
  closed from the innermost out, so their ``finally`` blocks run in the
  order nested calls would run them. An exception raised while one closes
  is thrown into the next walker out, which can catch it and should then
  end. A walker that ignores the close runs its cleanup later than in a
  ``yield from`` chain. A walker that yields while being closed gets a
  ``RuntimeError``, and a ``Call`` it yields then never starts. `walk`'s
  ``close`` returns nothing.

The driver costs a few hundred nanoseconds per `Call`, so a walker that runs
on every render and visits many nodes is better written with a hand-written
stack.
"""

from __future__ import annotations

from types import GeneratorType
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

_T = TypeVar("_T")


class Call:
    """
    Ask the driver to run ``function(*args, **kwargs)``, a generator function, as a nested walk.

    The ``yield`` that gives the driver a `Call` gives back the nested walk's
    return value.
    """

    __slots__ = ("args", "function", "kwargs")

    def __init__(self, function: Callable[..., Generator[Any, Any, Any]], *args: object, **kwargs: object) -> None:
        self.function = function
        self.args = args
        self.kwargs = kwargs


def run(generator: Generator[Any, Any, _T]) -> _T:
    """
    Run a walker generator to its end and return its result.

    Raises:
        TypeError: when a walker yields anything other than a `Call`. The
            error is raised at that walker's ``yield``.

    """
    stack: list[Generator[Any, Any, Any]] = [generator]
    sent: Any = None
    raised: BaseException | None = None
    try:
        while True:
            current = stack[-1]
            try:
                if raised is not None:
                    error, raised = raised, None
                    request = current.throw(error)
                else:
                    request = current.send(sent)
            except StopIteration as stop:
                # The walker returned: hand the value to its caller, or end.
                stack.pop()
                if not stack:
                    return cast("_T", stop.value)
                sent = stop.value
                continue
            except BaseException as error:
                # The walker raised: throw the exception into its caller at
                # the `yield Call(...)`, as a nested call would raise there.
                stack.pop()
                if not stack:
                    raise
                raised = error
                sent = None
                continue
            sent = None
            if type(request) is Call:
                raised = _start(request, stack)
            else:
                raised = TypeError(f"a walker run with run() yielded {type(request).__name__}, not a Call")
    finally:
        _close(stack)


def walk(generator: Generator[Any, Any, _T]) -> Generator[Any, Any, _T]:
    """Run a walker generator as one generator: yield its non-`Call` values, then return its result."""
    stack: list[Generator[Any, Any, Any]] = [generator]
    sent: Any = None
    raised: BaseException | None = None
    try:
        while True:
            current = stack[-1]
            try:
                if raised is not None:
                    error, raised = raised, None
                    request = current.throw(error)
                else:
                    request = current.send(sent)
            except StopIteration as stop:
                stack.pop()
                if not stack:
                    return cast("_T", stop.value)
                sent = stop.value
                continue
            except BaseException as error:
                stack.pop()
                if not stack:
                    raise
                raised = error
                sent = None
                continue
            sent = None
            if type(request) is Call:
                raised = _start(request, stack)
                continue
            # An ordinary yielded value goes to this walk's reader. What the
            # reader sends back, or throws in, goes to the walker that
            # yielded it.
            try:
                sent = yield request
            except GeneratorExit:
                # The reader is closing the walk: the `finally` block closes
                # each walker, innermost first.
                raise
            except BaseException as error:  # noqa: BLE001 - thrown into the walker that yielded
                raised = error
    finally:
        _close(stack)


def _start(request: Call, stack: list[Generator[Any, Any, Any]]) -> BaseException | None:
    """Start a nested walk on the stack, or return the error to throw into its caller."""
    try:
        child = request.function(*request.args, **request.kwargs)
    except BaseException as error:  # noqa: BLE001 - thrown into the caller
        # Starting the nested walk failed (for example a wrong argument):
        # the caller sees it at its `yield Call(...)`.
        return error
    if type(child) is not GeneratorType:
        name = getattr(request.function, "__qualname__", repr(request.function))
        return TypeError(f"Call({name}) returned {type(child).__name__}, not a generator: the function needs a yield")
    stack.append(child)
    return None


def _close(stack: list[Generator[Any, Any, Any]]) -> None:
    """Close the walkers still running from the innermost out, as nested calls would unwind."""
    error: BaseException | None = None
    while stack:
        current = stack.pop()
        try:
            if error is None:
                current.close()
            else:
                # The walker inside this one raised while closing, so this
                # one gets the exception at its `yield`, where it can catch
                # it. A walker that catches it should end: yielding again
                # while being closed is a bug, reported outward, as a
                # `yield from` chain reports it.
                current.throw(error)
                current.close()
                error = RuntimeError("a walker yielded again while it was being closed")
        except StopIteration:
            # The walker caught the exception and returned.
            error = None
        except BaseException as close_error:  # noqa: BLE001 - raised after the rest are closed
            error = close_error
    if error is not None:
        raise error
