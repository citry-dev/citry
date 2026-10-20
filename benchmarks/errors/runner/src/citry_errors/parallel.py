"""Run the benchmark's cases on several worker threads, with a limit on how many of one framework run at once."""

from __future__ import annotations

import threading
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence


class Stopped(Exception):  # noqa: N818 - it names what happened, as KeyboardInterrupt does
    """Raised by a task that saw `stop` set and gave up its case; the run is already ending."""


def run_all[T, R](
    tasks: Sequence[T],
    work: Callable[[T], R],
    *,
    jobs: int,
    group: Callable[[T], str],
    limits: Mapping[str, int],
    stop: threading.Event,
) -> list[R]:
    """
    Call `work` on every task, at most `jobs` at once, and return the results in the order of `tasks`.

    A task waits while `limits[group(task)]` tasks of its group are running,
    and a later task of another group goes first, so a framework that must
    run its cases one at a time does not hold up the others.

    When `work` raises, no new task starts, the tasks already running finish,
    and the first error is raised again here. When the run is interrupted
    with Ctrl-C, `stop` is set first: the running tasks can then tell that
    their child processes may have been killed by the same signal, and give
    up their case early by raising `Stopped`. The function waits for them
    before raising KeyboardInterrupt.
    """
    # A zero would leave every task waiting for a slot that never opens.
    if jobs < 1 or any(limit < 1 for limit in limits.values()):
        raise ValueError(f"jobs ({jobs}) and every limit ({dict(limits)}) must be 1 or more")
    # Worked out once, here, so an error in `group` reaches the caller
    # instead of ending a worker thread without a word.
    groups = [group(task) for task in tasks]
    results: list[R | None] = [None] * len(tasks)
    # Positions of the tasks not started yet, in the caller's order.
    pending = list(range(len(tasks)))
    running: Counter[str] = Counter()
    errors: list[BaseException] = []
    changed = threading.Condition()

    def take() -> int | None:
        with changed:
            while True:
                if errors or stop.is_set() or not pending:
                    return None
                for position, index in enumerate(pending):
                    name = groups[index]
                    if running[name] < limits.get(name, jobs):
                        del pending[position]
                        running[name] += 1
                        return index
                # Every waiting task's group is full: wait for a task to end.
                changed.wait()

    def worker() -> None:
        while (index := take()) is not None:
            try:
                results[index] = work(tasks[index])
            except Stopped:
                # The run is ending on Ctrl-C, which the caller's thread raises.
                pass
            except BaseException as error:  # noqa: BLE001 - raised again by the caller's thread
                with changed:
                    errors.append(error)
            finally:
                with changed:
                    running[groups[index]] -= 1
                    changed.notify_all()

    threads = [threading.Thread(target=worker, name=f"case-worker-{number}") for number in range(jobs)]
    try:
        # Started inside the `try`, so Ctrl-C while they start still stops them.
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        # Ctrl-C reaches only this thread. Each worker gives up its case
        # before the case's next tool or browser check, or finishes it; a
        # running browser check stops its development server. No new case
        # starts.
        stop.set()
        with changed:
            changed.notify_all()
        for thread in threads:
            if thread.is_alive():
                thread.join()
        raise
    if errors:
        raise errors[0]
    return results  # type: ignore[return-value]  # every slot was filled by a finished task
