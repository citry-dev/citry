"""Run the benchmark's cases on several worker threads, with a limit on how many of one framework run at once."""

from __future__ import annotations

import threading
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence


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
    with Ctrl-C, `stop` is set first, so the running tasks can tell that
    their child processes may have been killed by the same signal, and the
    function waits for them before raising KeyboardInterrupt.
    """
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
                    name = group(tasks[index])
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
            except BaseException as error:  # noqa: BLE001 - raised again by the caller's thread
                with changed:
                    errors.append(error)
            finally:
                with changed:
                    running[group(tasks[index])] -= 1
                    changed.notify_all()

    threads = [threading.Thread(target=worker, name=f"case-worker-{number}") for number in range(max(1, jobs))]
    for thread in threads:
        thread.start()
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        # Ctrl-C reaches only this thread. The workers finish the case they
        # are on, which stops its development server, and start no other.
        stop.set()
        with changed:
            changed.notify_all()
        for thread in threads:
            thread.join()
        raise
    if errors:
        raise errors[0]
    return results  # type: ignore[return-value]  # every slot was filled by a finished task
