"""Thread coordination for component discovery and registry state."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


class CitryLifecycleInProgress(RuntimeError):
    """
    Raised when another thread is changing Citry's component lifecycle state.

    Component discovery, registration, built-in creation, clearing, and
    tag-rule construction publish related state together. A competing thread
    receives this error rather than observing an incomplete registry or waiting
    in a way that can deadlock with Python's module-import locks.

    Finish [`Citry.initialize()`][citry.Citry.initialize] before starting
    request threads to avoid this error during normal server operation. An
    operation that encounters it may also be retried after the active lifecycle
    operation finishes.
    """


@dataclass(frozen=True, slots=True)
class _LifecycleState:
    """One atomically published logical-ownership record."""

    owner_thread_id: int
    root_operation: str
    root_blocks_nested: bool
    entries: tuple[object, ...]


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
    ) -> Iterator[None]:
        """Claim logical ownership without holding the state lock over user code."""
        thread_id = threading.get_ident()
        entry = object()
        try:
            with self._state_lock:
                state = self._state
                if state is None:
                    self._state = _LifecycleState(
                        owner_thread_id=thread_id,
                        root_operation=operation,
                        root_blocks_nested=blocks_nested,
                        entries=(entry,),
                    )
                elif state.owner_thread_id != thread_id:
                    self._raise_competing_thread(operation, state.root_operation)
                elif not reentrant or state.root_blocks_nested:
                    msg = (
                        f"{operation} cannot run recursively; "
                        f"{state.root_operation} is already running on this thread."
                    )
                    raise RuntimeError(msg)
                else:
                    self._state = _LifecycleState(
                        owner_thread_id=state.owner_thread_id,
                        root_operation=state.root_operation,
                        root_blocks_nested=state.root_blocks_nested,
                        entries=(*state.entries, entry),
                    )
            yield
        finally:
            with self._state_lock:
                state = self._state
                if state is not None and entry in state.entries:
                    remaining = tuple(item for item in state.entries if item is not entry)
                    self._state = (
                        _LifecycleState(
                            owner_thread_id=state.owner_thread_id,
                            root_operation=state.root_operation,
                            root_blocks_nested=state.root_blocks_nested,
                            entries=remaining,
                        )
                        if remaining
                        else None
                    )

    @contextmanager
    def read(self, operation: str) -> Iterator[None]:
        """Hold the short state lock across one readiness check and raw read."""
        thread_id = threading.get_ident()
        with self._state_lock:
            state = self._state
            if state is not None and state.owner_thread_id != thread_id:
                self._raise_competing_thread(operation, state.root_operation)
            if state is not None and state.root_blocks_nested:
                msg = f"{operation} cannot run while {state.root_operation} is active on this thread."
                raise RuntimeError(msg)
            yield

    @staticmethod
    def _raise_competing_thread(operation: str, active: str) -> None:
        msg = (
            f"Cannot {operation} while {active} is running on another thread. "
            "Call initialize() before starting worker threads, or retry after the active operation finishes."
        )
        raise CitryLifecycleInProgress(msg)
