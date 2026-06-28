"""
Hot reload: watch component files and invalidate their caches in place.

When a component's ``template_file`` / ``js_file`` / ``css_file`` changes on
disk, the next render should show the new content without restarting the
process. The engine already knows how to drop a file's cached work
(``Citry.invalidate_file``); this module supplies the missing half, a watcher
that notices the change and calls it.

The watcher is pluggable behind the :class:`FileWatcher` protocol. The default
is :class:`WatchfilesWatcher` (Rust-backed, native OS events) when the
``watcher-watchfiles`` extra is installed, falling back to the dependency-free
:class:`PollingWatcher` (a periodic mtime scan) otherwise. A host that already
runs its own watcher (Django's autoreloader, an editor) does not need any of
this: it can feed change events straight into ``Citry.invalidate_file``.

Typical use is through the ``citry watch`` command; the design and the host
entry points are in ``docs/design/hot_reload.md``.
"""

from __future__ import annotations

import importlib.util
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from citry.citry import Citry
    from citry.component import Component


# How often the dependency-free poller re-scans, and how long stop() waits for
# the watcher thread to exit, both in seconds.
_DEFAULT_POLL_INTERVAL = 0.5
_DEFAULT_STOP_TIMEOUT = 5.0


class FileWatcher(Protocol):
    """
    A source of file-change events.

    ``run`` blocks, calling ``on_change`` with a set of changed paths for each
    batch of events, until another thread calls ``stop``. Implementations should
    coalesce the burst of events a single editor save produces into as few
    ``on_change`` calls as they can, and must return from ``run`` promptly once
    ``stop`` is called. Bring your own by passing one to :func:`watch`.
    """

    def run(self, roots: Sequence[Path], on_change: Callable[[set[Path]], None]) -> None:
        """Watch ``roots`` and call ``on_change`` per batch until stopped."""
        ...

    def stop(self) -> None:
        """Ask ``run`` to return. Safe to call from another thread."""
        ...


class WatchfilesWatcher:
    """
    A :class:`FileWatcher` backed by ``watchfiles`` (native inotify/FSEvents/
    ReadDirectoryChangesW, with a polling fallback for network mounts).

    Needs the ``watcher-watchfiles`` extra (``pip install
    citry[watcher-watchfiles]``); the import is deferred to ``run`` so this
    class can be referenced without the extra installed.
    """

    def __init__(self, *, force_polling: bool = False) -> None:
        self._force_polling = force_polling
        self._stop = threading.Event()

    def run(self, roots: Sequence[Path], on_change: Callable[[set[Path]], None]) -> None:
        """Stream ``watchfiles`` change batches into ``on_change``."""
        from watchfiles import watch as watchfiles_watch  # noqa: PLC0415

        for changes in watchfiles_watch(
            *roots,
            stop_event=self._stop,
            force_polling=self._force_polling,
        ):
            # watchfiles yields a set of (Change, path-string) pairs per batch.
            on_change({Path(raw_path) for _change, raw_path in changes})

    def stop(self) -> None:
        """Signal the ``watchfiles`` loop (it watches ``self._stop``)."""
        self._stop.set()


class PollingWatcher:
    """
    A dependency-free :class:`FileWatcher` that re-scans ``roots`` on a timer.

    Portable and needs no extra, but slower and less efficient than
    :class:`WatchfilesWatcher`; it is the fallback when no native watcher is
    installed. ``interval`` is the seconds between scans.
    """

    def __init__(self, *, interval: float = _DEFAULT_POLL_INTERVAL) -> None:
        self._interval = interval
        self._stop = threading.Event()

    def run(self, roots: Sequence[Path], on_change: Callable[[set[Path]], None]) -> None:
        """Re-scan ``roots`` every ``interval`` seconds and report mtime changes."""
        previous = self._snapshot(roots)
        # wait() returns True once stopped, so the loop ends promptly on stop().
        while not self._stop.wait(self._interval):
            current = self._snapshot(roots)
            changed = self._diff(previous, current)
            previous = current
            if changed:
                on_change(changed)

    def stop(self) -> None:
        """Break the scan loop after the current wait."""
        self._stop.set()

    @staticmethod
    def _snapshot(roots: Sequence[Path]) -> dict[Path, float]:
        """Map every existing file under ``roots`` to its modification time."""
        seen: dict[Path, float] = {}
        for root in roots:
            for file_path in root.rglob("*"):
                try:
                    stat = file_path.stat()
                except OSError:
                    # Vanished between listing and stat, or unreadable: treat as
                    # absent so a later appearance reads as a change.
                    continue
                if Path.is_file(file_path):
                    seen[file_path] = stat.st_mtime
        return seen

    @staticmethod
    def _diff(before: dict[Path, float], after: dict[Path, float]) -> set[Path]:
        """The paths that were added, removed, or whose mtime moved."""
        changed = {path for path, mtime in after.items() if before.get(path) != mtime}
        changed |= before.keys() - after.keys()
        return changed


class WatchdogWatcher:
    """
    A :class:`FileWatcher` backed by ``watchdog`` (its own native OS-event
    observers, with watchdog's polling observer as an internal fallback).

    Needs the ``watcher-watchdog`` extra (``pip install citry[watcher-watchdog]``);
    the import is deferred to ``run`` so the class can be referenced without it.
    Prefer :class:`WatchfilesWatcher`; this exists for projects already
    standardized on watchdog. watchdog reports one event at a time (no batching),
    so a single save can invalidate the same file more than once; each
    invalidation is a cheap cache drop, so the extra calls are harmless.
    """

    def __init__(self) -> None:
        self._stop = threading.Event()

    def run(self, roots: Sequence[Path], on_change: Callable[[set[Path]], None]) -> None:
        """Drive watchdog filesystem events into ``on_change`` until stopped."""
        from watchdog.events import FileSystemEventHandler  # noqa: PLC0415
        from watchdog.observers import Observer  # noqa: PLC0415

        class _Handler(FileSystemEventHandler):  # type: ignore[misc]  # base resolves at runtime
            def on_any_event(self, event: Any) -> None:
                if event.is_directory:
                    return
                changed = {Path(event.src_path)}
                # A rename also reports where the file moved to.
                dest = getattr(event, "dest_path", "")
                if dest:
                    changed.add(Path(dest))
                on_change(changed)

        observer = Observer()
        for root in roots:
            observer.schedule(_Handler(), str(root), recursive=True)
        observer.start()
        try:
            self._stop.wait()
        finally:
            observer.stop()
            observer.join()

    def stop(self) -> None:
        """Stop the watchdog observer loop."""
        self._stop.set()


class WatchHandle:
    """
    A running watcher. Call :meth:`stop` to tear it down, or :meth:`wait` to
    block until it stops (the ``citry watch`` command waits, then stops on
    Ctrl-C). Returned by :func:`watch`.
    """

    def __init__(self, watcher: FileWatcher, thread: threading.Thread) -> None:
        self._watcher = watcher
        self._thread = thread

    @property
    def running(self) -> bool:
        """Whether the watcher thread is still alive."""
        return self._thread.is_alive()

    def wait(self) -> None:
        """
        Block the calling thread until the watcher stops.

        Polls with a short timeout so a ``KeyboardInterrupt`` on the main thread
        is delivered promptly rather than swallowed by an un-timed join.
        """
        while self._thread.is_alive():
            self._thread.join(0.25)

    def stop(self, *, timeout: float = _DEFAULT_STOP_TIMEOUT) -> None:
        """Ask the watcher to stop and wait up to ``timeout`` for its thread."""
        self._watcher.stop()
        self._thread.join(timeout)


def _module_installed(name: str) -> bool:
    """Whether ``name`` can be imported, checked without importing it."""
    return importlib.util.find_spec(name) is not None


def default_watcher() -> FileWatcher:
    """
    The best watcher available: :class:`WatchfilesWatcher` if ``watchfiles`` is
    installed, else :class:`WatchdogWatcher` if ``watchdog`` is, else the
    dependency-free :class:`PollingWatcher`.
    """
    if _module_installed("watchfiles"):
        return WatchfilesWatcher()
    if _module_installed("watchdog"):
        return WatchdogWatcher()
    return PollingWatcher()


def _resolve_roots(engine: Citry, roots: Iterable[str | Path] | None) -> list[Path]:
    """
    The directories to watch: ``roots`` if given, else the engine's configured
    ``dirs``. Resolved to absolute paths; non-existent entries are dropped.
    """
    raw = list(roots) if roots is not None else list(engine.settings.dirs)
    resolved = [Path(entry).resolve() for entry in raw]
    existing = [path for path in resolved if path.is_dir()]
    if not existing:
        msg = (
            "citry hot reload has no directories to watch. Pass roots=... or "
            "construct the engine with Citry(dirs=[...])."
        )
        raise ValueError(msg)
    return existing


def watch(
    engine: Citry,
    *,
    roots: Iterable[str | Path] | None = None,
    watcher: FileWatcher | None = None,
    on_reload: Callable[[set[Path], list[type[Component]]], None] | None = None,
) -> WatchHandle:
    """
    Start watching ``roots`` and invalidate ``engine``'s caches in place on
    every change. Returns a :class:`WatchHandle`; call ``.stop()`` to end it.

    ``roots`` defaults to ``engine.settings.dirs``. ``watcher`` defaults to
    :func:`default_watcher`. ``on_reload(changed_paths, reset_classes)`` is
    called after each batch is invalidated, with the classes that were reset
    (the ``citry watch`` command uses it to print what reloaded).

    The watcher runs on a background daemon thread, so this returns immediately.
    Changes to files no component has loaded yet are no-ops (there is nothing
    cached to drop); a brand-new component file or a Python edit is restart-class
    and belongs to the host's own reloader. See ``docs/design/hot_reload.md``.
    """
    resolved_roots = _resolve_roots(engine, roots)
    impl = watcher if watcher is not None else default_watcher()

    def handle_change(paths: set[Path]) -> None:
        reset: list[type[Component]] = []
        for path in paths:
            reset.extend(engine.invalidate_file(path))
        if on_reload is not None:
            on_reload(paths, reset)

    thread = threading.Thread(
        target=impl.run,
        args=(resolved_roots, handle_change),
        name="citry-watch",
        daemon=True,
    )
    thread.start()
    return WatchHandle(impl, thread)
