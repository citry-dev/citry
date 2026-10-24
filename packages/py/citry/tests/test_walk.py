"""The generator-walk driver in `citry._walk` behaves like the recursive walk it replaces."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import pytest

from citry._walk import Call, run, walk

if TYPE_CHECKING:
    from collections.abc import Generator


def _tree(depth: int) -> list[Any]:
    # A chain `[0, [1, [2, ...]]]`, built without recursion.
    node: list[Any] = [depth - 1]
    for value in range(depth - 2, -1, -1):
        node = [value, node]
    return node


def _visit_order(node: list[Any]) -> Generator[Any, Any, list[int]]:
    order = [node[0]]
    for child in node[1:]:
        order.extend((yield Call(_visit_order, child)))
    order.append(-node[0])
    return order


def _recursive_visit_order(node: list[Any]) -> list[int]:
    order = [node[0]]
    for child in node[1:]:
        order.extend(_recursive_visit_order(child))
    order.append(-node[0])
    return order


def test_results_come_back_in_the_order_of_the_recursive_walk() -> None:
    tree = [0, [1, [2], [3]], [4, [5, [6]]]]
    assert run(_visit_order(tree)) == _recursive_visit_order(tree)


def test_an_exception_in_a_child_is_raised_at_the_callers_yield() -> None:
    def failing() -> Generator[Any, Any, None]:
        raise ValueError("deep")
        yield  # pragma: no cover - makes this a generator

    def catching() -> Generator[Any, Any, str]:
        try:
            yield Call(failing)
        except ValueError as error:
            return f"caught {error}"
        return "not raised"  # pragma: no cover

    def outer() -> Generator[Any, Any, str]:
        return (yield Call(catching))

    assert run(outer()) == "caught deep"


def test_an_uncaught_exception_leaves_run_with_its_type_and_message() -> None:
    def failing() -> Generator[Any, Any, None]:
        raise KeyError("missing")
        yield  # pragma: no cover

    def outer() -> Generator[Any, Any, None]:
        yield Call(failing)

    with pytest.raises(KeyError, match="missing"):
        run(outer())


def test_a_call_that_cannot_start_is_raised_at_the_callers_yield() -> None:
    def child(value: int) -> Generator[Any, Any, int]:
        return value
        yield  # pragma: no cover

    def outer() -> Generator[Any, Any, str]:
        try:
            yield Call(child)  # missing argument
        except TypeError:
            return "caught"
        return "not raised"  # pragma: no cover

    assert run(outer()) == "caught"


def test_finally_blocks_run_innermost_first_when_the_walk_is_abandoned() -> None:
    closed: list[str] = []

    def level(name: str, child: str | None) -> Generator[Any, Any, None]:
        try:
            if child is None:
                yield "leaf value"
            else:
                yield Call(level, child, None if child == "inner" else "inner")
        finally:
            closed.append(name)

    outer = level("outer", "middle")
    driver = walk(outer)
    assert next(driver) == "leaf value"
    driver.close()
    # The walkers are closed by the driver itself, not later by garbage
    # collection: the order holds while the driver is still referenced.
    assert closed == ["inner", "middle", "outer"]
    assert outer.gi_frame is None


def test_an_uncaught_exception_runs_each_finally_as_it_passes_out() -> None:
    closed: list[str] = []

    def failing() -> Generator[Any, Any, None]:
        try:
            raise RuntimeError("stop")
        finally:
            closed.append("failing")
        yield  # pragma: no cover

    def level(name: str) -> Generator[Any, Any, None]:
        try:
            yield Call(failing if name == "inner" else level, *([] if name == "inner" else ["inner"]))
        finally:
            closed.append(name)

    with pytest.raises(RuntimeError, match="stop"):
        run(level("outer"))
    assert closed == ["failing", "inner", "outer"]


def test_ordinary_yielded_values_reach_the_consumer_and_its_replies_return() -> None:
    def child() -> Generator[Any, Any, str]:
        reply = yield "from child"
        return f"child got {reply}"

    def outer() -> Generator[Any, Any, str]:
        first = yield "from outer"
        nested = yield Call(child)
        return f"{first} / {nested}"

    driver = walk(outer())
    assert next(driver) == "from outer"
    assert driver.send("one") == "from child"
    with pytest.raises(StopIteration) as stop:
        driver.send("two")
    assert stop.value.value == "one / child got two"


def test_run_rejects_a_walker_that_yields_an_ordinary_value_at_its_yield() -> None:
    def outer() -> Generator[Any, Any, str]:
        try:
            yield "not a call"
        except TypeError as error:
            return str(error)
        return "not raised"  # pragma: no cover

    assert run(outer()) == "a walker run with run() yielded str, not a Call"


def test_a_deep_chain_uses_as_many_python_frames_as_a_shallow_one() -> None:
    def depth_reached() -> int:
        frame = sys._getframe()
        count = 0
        while frame is not None:
            count += 1
            frame = frame.f_back
        return count

    deepest: list[int] = []

    def visit(node: list[Any]) -> Generator[Any, Any, int]:
        if len(node) == 1:
            deepest.append(depth_reached())
            return 1
        return 1 + (yield Call(visit, node[1]))

    assert run(visit(_tree(8))) == 8
    assert run(visit(_tree(100_000))) == 100_000
    assert deepest[0] == deepest[1]


def test_an_exception_thrown_into_walk_reaches_the_walker_that_yielded() -> None:
    def child() -> Generator[Any, Any, str]:
        try:
            yield "waiting"
        except ValueError:
            return "recovered"
        return "not thrown"  # pragma: no cover

    def outer() -> Generator[Any, Any, str]:
        return (yield Call(child))

    driver = walk(outer())
    assert next(driver) == "waiting"
    with pytest.raises(StopIteration) as stop:
        driver.throw(ValueError("from the reader"))
    assert stop.value.value == "recovered"


def test_an_exception_raised_while_closing_reaches_the_next_walker_out() -> None:
    events: list[str] = []

    def inner() -> Generator[Any, Any, None]:
        try:
            yield "waiting"
        finally:
            events.append("inner closed")
            raise RuntimeError("cleanup failed")

    def middle() -> Generator[Any, Any, None]:
        try:
            yield Call(inner)
        except RuntimeError as error:
            events.append(f"middle caught {error}")

    def outer() -> Generator[Any, Any, None]:
        try:
            yield Call(middle)
        finally:
            events.append("outer closed")

    driver = walk(outer())
    assert next(driver) == "waiting"
    driver.close()
    assert events == ["inner closed", "middle caught cleanup failed", "outer closed"]


def test_a_call_to_a_function_without_yield_is_a_clear_type_error() -> None:
    def plain(value: int) -> int:
        return value

    def outer() -> Generator[Any, Any, None]:
        yield Call(plain, 3)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match=r"returned int, not a generator: the function needs a yield"):
        run(outer())


def test_yield_from_inside_a_walker_works_beside_call() -> None:
    def leaf(value: int) -> Generator[Any, Any, int]:
        return value * 10
        yield  # pragma: no cover

    def helper(value: int) -> Generator[Any, Any, int]:
        # An ordinary helper generator reached with `yield from` can itself
        # ask the driver for a nested walk.
        result = yield Call(leaf, value)
        return result + 1

    def outer() -> Generator[Any, Any, int]:
        return (yield from helper(4))

    assert run(outer()) == 41


def test_an_uncaught_exception_while_closing_leaves_walk_close() -> None:
    events: list[str] = []

    def inner() -> Generator[Any, Any, None]:
        try:
            yield "waiting"
        finally:
            raise RuntimeError("cleanup failed")

    def outer() -> Generator[Any, Any, None]:
        try:
            yield Call(inner)
        finally:
            events.append("outer closed")

    driver = walk(outer())
    assert next(driver) == "waiting"
    with pytest.raises(RuntimeError, match="cleanup failed"):
        driver.close()
    assert events == ["outer closed"]


def test_a_walker_that_yields_while_being_closed_is_reported() -> None:
    def inner() -> Generator[Any, Any, None]:
        try:
            yield "waiting"
        finally:
            raise RuntimeError("cleanup failed")

    def middle() -> Generator[Any, Any, None]:
        try:
            yield Call(inner)
        except RuntimeError:
            # A walker that catches a close error should end, not yield.
            yield "again"

    driver = walk(middle())
    assert next(driver) == "waiting"
    with pytest.raises(RuntimeError, match="yielded again while it was being closed"):
        driver.close()
