"""Run the benchmark's cases on several worker threads."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class Stopped(Exception):  # noqa: N818 - it names what happened, as KeyboardInterrupt does
    """Raised by a task that saw `stop` set and gave up its case; the run is already ending."""


def run_all[T, R](
    tasks: Sequence[T],
    work: Callable[[T], R],
    *,
    jobs: int,
    stop: threading.Event,
) -> list[R]:
    """
    Call `work` on every task, at most `jobs` at once, and return the results in the order of `tasks`.

    When `work` raises, no new task starts, the tasks already running finish,
    and the first error is raised again here. When the run is interrupted
    with Ctrl-C, `stop` is set first: the running tasks can then tell that
    their child processes may have been killed by the same signal, and give
    up their case early by raising `Stopped`. The function waits for them
    before raising KeyboardInterrupt.
    """
    # A zero would start no worker, and the run would end with no results.
    if jobs < 1:
        raise ValueError(f"jobs ({jobs}) must be 1 or more")
    results: list[R | None] = [None] * len(tasks)
    # Positions of the tasks not started yet, in the caller's order.
    pending = list(range(len(tasks)))
    errors: list[BaseException] = []
    # Guards `pending` and `errors`, which every worker reads and changes.
    lock = threading.Lock()

    def take() -> int | None:
        with lock:
            if errors or stop.is_set() or not pending:
                return None
            return pending.pop(0)

    def worker() -> None:
        while (index := take()) is not None:
            try:
                results[index] = work(tasks[index])
            except Stopped:
                # The run is ending on Ctrl-C, which the caller's thread raises.
                pass
            except BaseException as error:  # noqa: BLE001 - raised again by the caller's thread
                with lock:
                    errors.append(error)

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
        for thread in threads:
            if thread.is_alive():
                thread.join()
        raise
    if errors:
        raise errors[0]
    return results  # type: ignore[return-value]  # every slot was filled by a finished task
