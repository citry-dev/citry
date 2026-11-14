"""
Check that an operation takes time in step with the size of its input.

A test that compares a wall-clock time with a fixed bound fails on a slow
machine and passes on a fast one. These helpers time the same operation on
a small input and on one several times larger, on the same machine in the
same run, and compare the two. An operation that reads its input once takes
about ``factor`` times longer on the larger input. One that reads it again
for every character takes about ``factor`` squared times longer, which the
bound rejects once the smaller run takes longer than the floor below. The
speed of the machine cancels out of the comparison.

When the smaller run is faster than the floor, the comparison works as a
bound of ``3 * factor`` milliseconds on the larger run. That still refuses
the slow code these tests guard against, which took seconds, but it does
not notice a small slowdown on such short inputs.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

# The smaller time is never taken as less than this, so timing noise on a
# run of a few microseconds cannot turn into a large ratio. An input for
# which the smaller run takes several times this long gets a true growth
# comparison; a faster one gets the fixed bound the docstring describes.
_FLOOR_SECONDS = 0.001
# How far above the linear ratio the larger run may go. Timing noise on a
# busy machine stays well under this multiple, while an operation that grows
# with the square of the input is about `factor` times over the linear ratio.
_ALLOWANCE = 3


def best_time(run: Callable[[Any], object], argument: Any, *, repeats: int = 5) -> float:
    """Return the shortest time, in seconds, of ``repeats`` calls to ``run(argument)``."""
    # The first call fills lazily built caches (compiled patterns, cached
    # route splits), so the timed calls measure only the work itself.
    run(argument)
    best = float("inf")
    for _repeat in range(repeats):
        start = time.perf_counter()
        run(argument)
        # The shortest of several runs leaves out the ones a busy machine slowed down.
        best = min(best, time.perf_counter() - start)
    return best


def growth_ratio(run: Callable[[Any], object], small: Any, large: Any, *, repeats: int = 5) -> float:
    """Return how many times longer ``run`` takes on ``large`` than on ``small``."""
    return best_time(run, large, repeats=repeats) / max(best_time(run, small, repeats=repeats), _FLOOR_SECONDS)


def assert_grows_in_step(
    run: Callable[[Any], object], small: Any, large: Any, *, factor: int, repeats: int = 5
) -> float:
    """
    Fail unless ``run`` takes about ``factor`` times longer on ``large`` than on ``small``.

    ``large`` must be ``factor`` times the size of ``small``. ``run`` also
    checks the answer, so a call that returns the wrong result fails here
    too. Returns the ratio, so a caller can report it.
    """
    ratio = growth_ratio(run, small, large, repeats=repeats)
    limit = _ALLOWANCE * factor
    assert ratio < limit, f"{factor} times the input took {ratio:.1f} times as long (limit {limit})"
    return ratio
