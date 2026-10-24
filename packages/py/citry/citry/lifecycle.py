"""Thread coordination for component discovery and registry state."""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import FrameType


class CitryLifecycleInProgress(RuntimeError):
    """
    Raised when another thread is changing Citry's component lifecycle state.

    Component discovery, registration, built-in creation, and clearing
    publish related state together. A competing thread receives this error
    rather than observing an incomplete registry or waiting in a way that can
    deadlock with Python's module-import locks.

    One case waits instead: when a render or component lookup needs the
    ``Citry`` instance's one-time setup (discovery and built-in creation)
    while another thread runs it, it waits for that setup to finish. A thread
    that is importing a module, or running a reset, still receives this error,
    because the setup may be waiting for that import or for the locks the
    reset holds; so does a wait that lasts over a minute. Finish
    [`Citry.initialize()`][citry.Citry.initialize] before starting request
    threads to avoid both this error and that wait during normal server
    operation. An operation that encounters it may also be retried after the
    active lifecycle operation finishes.
    """


# The files Python's import system runs a module import from.
_IMPORT_FRAMES = frozenset({"<frozen importlib._bootstrap>", "<frozen importlib._bootstrap_external>"})


# How long a thread waits for another thread's one-time setup before it
# gives up with CitryLifecycleInProgress. Discovery that takes longer, or a
# setup that waits for the waiting thread, then fails instead of hanging.
_SETUP_WAIT_SECONDS = 60.0

# Per-thread depth of code that must not wait for the setup, such as a
# reset that holds Citry's asset locks (see `no_setup_wait`).
_NO_SETUP_WAIT = threading.local()


@contextmanager
def no_setup_wait() -> Iterator[None]:
    """
    Make this thread raise instead of waiting for another thread's one-time setup.

    A reset holds locks that the setup may need (its registration hooks can
    read loaded messages), so a render from a reset hook that waited for the
    setup could hang both threads.
    """
    _NO_SETUP_WAIT.depth = getattr(_NO_SETUP_WAIT, "depth", 0) + 1
    try:
        yield
    finally:
        _NO_SETUP_WAIT.depth -= 1


def _may_wait_for_setup() -> bool:
    """Whether this thread may wait for another thread's one-time setup."""
    return not getattr(_NO_SETUP_WAIT, "depth", 0) and not _inside_module_import()


def _inside_module_import() -> bool:
    """Whether this thread is running a module's import, for example a module that renders at import time."""
    frame: FrameType | None = sys._getframe(1)
    while frame is not None:
        if frame.f_code.co_filename in _IMPORT_FRAMES:
            return True
        frame = frame.f_back
    return False


@dataclass(frozen=True, slots=True)
class _LifecycleState:
    """One atomically published logical-ownership record."""

    owner_thread_id: int
    root_operation: str
    root_blocks_nested: bool
    entries: tuple[object, ...]
    # Set for the engine's one-time setup (discovery and built-ins), which
    # other threads wait for instead of failing; the owner sets it when the
    # setup ends, whether it succeeded or failed.
    setup_finished: threading.Event | None = None


class _LifecycleCoordinator:
    """Give one thread temporary ownership of related component state."""

    def __init__(self) -> None:
        self._state_lock = threading.Lock()
        self._state: _LifecycleState | None = None

    @contextmanager
    def operation(
        self,
        operation: str,
        *,
        reentrant: bool = True,
        blocks_nested: bool = False,
        setup: bool = False,
    ) -> Iterator[None]:
        """
        Claim logical ownership without holding the state lock over user code.

        ``setup=True`` marks the engine's one-time setup that a render or
        lookup needs before it can read the registry. Another thread that
        needs the same setup waits for this one to finish, with no lock
        held, and then checks again; any other competing operation still
        raises ``CitryLifecycleInProgress``. So does a thread that is
        importing a module or running a reset: the setup imports component
        modules and reads loaded messages, and may be waiting for that
        import or for the locks the reset holds. A wait that lasts longer
        than ``_SETUP_WAIT_SECONDS`` raises too.
        """
        thread_id = threading.get_ident()
        entry = object()
        claimed = False
        try:
            while not claimed:
                waiter: threading.Event | None = None
                with self._state_lock:
                    state = self._state
                    if state is None:
                        self._state = _LifecycleState(
                            owner_thread_id=thread_id,
                            root_operation=operation,
                            root_blocks_nested=blocks_nested,
                            entries=(entry,),
                            setup_finished=threading.Event() if setup else None,
                        )
                        claimed = True
                    elif state.owner_thread_id != thread_id:
                        if not (setup and state.setup_finished is not None) or not _may_wait_for_setup():
                            self._raise_competing_thread(operation, state.root_operation)
                        waiter = state.setup_finished
                    elif not reentrant or state.root_blocks_nested:
                        msg = (
                            f"{operation} cannot run recursively; "
                            f"{state.root_operation} is already running on this thread."
                        )
                        raise RuntimeError(msg)
                    else:
                        self._state = replace(state, entries=(*state.entries, entry))
                        claimed = True
                if waiter is not None:
                    # The other thread's setup may be what this one needs;
                    # once it ends, check the state again.
                    self.wait_for_setup(waiter, operation)
            yield
        finally:
            finished: threading.Event | None = None
            with self._state_lock:
                state = self._state
                if state is not None and entry in state.entries:
                    remaining = tuple(item for item in state.entries if item is not entry)
                    if remaining:
                        self._state = replace(state, entries=remaining)
                    else:
                        self._state = None
                        finished = state.setup_finished
            # Wake the threads waiting for this setup, after the state is
            # cleared so they can claim it if it failed.
            if finished is not None:
                finished.set()

    @contextmanager
    def read(self, operation: str) -> Iterator[None]:
        """
        Hold the short state lock across one readiness check and raw read.

        While another thread runs the one-time setup, this waits for it with
        no lock held, then checks again.
        """
        while True:
            with self._state_lock:
                waiter = self.check_read(operation)
                if waiter is None:
                    yield
                    return
            self.wait_for_setup(waiter, operation)

    def wait_for_setup(self, waiter: threading.Event, operation: str) -> None:
        """
        Wait, with no lock held, for another thread's one-time setup to end.

        Raises ``CitryLifecycleInProgress`` after ``_SETUP_WAIT_SECONDS``, so
        a setup that is itself waiting for this thread fails instead of
        hanging both.
        """
        if not waiter.wait(_SETUP_WAIT_SECONDS):
            msg = (
                f"Cannot {operation}: waited {_SETUP_WAIT_SECONDS:g} s for component discovery on another "
                "thread. Call initialize() before starting worker threads, and do not make code that runs "
                "during discovery wait for a thread that renders."
            )
            raise CitryLifecycleInProgress(msg)

    def check_read(self, operation: str) -> threading.Event | None:
        """
        Raise unless this thread may read lifecycle state now.

        The caller must hold ``_state_lock``. ``read()`` does both steps; the
        component lookups that run several times per rendered row write
        ``with coordinator._state_lock: coordinator.check_read(...)`` inline,
        because entering a generator-based context manager costs several
        times as much as a plain ``with`` on the lock.

        Returns ``None`` when the read may go ahead. While another thread
        runs the one-time setup, returns the event that thread sets when it
        ends: the caller releases ``_state_lock``, waits on it, and checks
        again. A thread that is importing a module, or running a reset,
        raises instead, because the setup may be waiting for that import or
        for the locks the reset holds.
        """
        state = self._state
        if state is not None and state.owner_thread_id != threading.get_ident():
            if state.setup_finished is not None and _may_wait_for_setup():
                return state.setup_finished
            self._raise_competing_thread(operation, state.root_operation)
        if state is not None and state.root_blocks_nested:
            msg = f"{operation} cannot run while {state.root_operation} is active on this thread."
            raise RuntimeError(msg)
        return None

    @staticmethod
    def _raise_competing_thread(operation: str, active: str) -> None:
        msg = (
            f"Cannot {operation} while {active} is running on another thread. "
            "Call initialize() before starting worker threads, or retry after the active operation finishes."
        )
        raise CitryLifecycleInProgress(msg)
