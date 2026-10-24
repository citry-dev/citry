"""
Cache backend calls run with no Citry lock held.

The backend is the application's own code, often a network round trip, so
a slow call must not hold up renders on other threads or a hot reload. Each
test makes one backend write slow and checks what other threads can do
meanwhile, and that a reset during the write is not undone.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from citry import Citry, Component, InMemoryCache
from citry.ext.cache import component_cache_key

# How long a test waits for a thread before it reports it stuck.
_JOIN_TIMEOUT = 10.0


class _SlowWrites(InMemoryCache):
    """An in-memory backend whose writes wait on ``release`` while ``slow`` is set."""

    def __init__(self) -> None:
        super().__init__()
        self.slow = threading.Event()
        self.writing = threading.Event()
        self.release = threading.Event()

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        if self.slow.is_set():
            self.writing.set()
            self.release.wait(_JOIN_TIMEOUT)
        super().set(key, value, ttl=ttl)


def _start(target: Any) -> threading.Thread:
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread


def _finish(thread: threading.Thread, timeout: float = _JOIN_TIMEOUT) -> None:
    thread.join(timeout)
    assert not thread.is_alive(), "the thread is stuck"


def _cached_component(app: Citry, name: str, text: str) -> type[Component]:
    cls = type(
        name, (Component,), {"citry": app, "template": f"<p>{text}</p>", "Cache": type("Cache", (), {"enabled": True})}
    )
    return cls


def test_a_slow_cache_write_does_not_hold_up_a_reset_or_another_cached_render() -> None:
    backend = _SlowWrites()
    app = Citry(autodiscover=False, cache=backend)
    card = _cached_component(app, "Card", "card")
    other = _cached_component(app, "Other", "other")
    app.initialize()
    backend.slow.set()
    writer = _start(lambda: card().render().serialize())
    assert backend.writing.wait(_JOIN_TIMEOUT)
    backend.slow.clear()
    try:
        # A reset and a render that builds a cache key both take the cache
        # revision lock; neither waits for the write.
        began = time.perf_counter()
        _finish(_start(card.reset_template), timeout=2.0)
        rendered: list[str] = []
        _finish(_start(lambda: rendered.append(other().render().serialize())), timeout=2.0)
        assert time.perf_counter() - began < 2.0
        assert "other" in rendered[0]
    finally:
        backend.release.set()
    _finish(writer)


def test_a_reset_during_a_slow_cache_write_is_not_undone() -> None:
    # The write stores the render made before the reset. Citry deletes that
    # stale entry after the write returns, and the next render shows the new
    # template.
    backend = _SlowWrites()
    app = Citry(autodiscover=False, cache=backend)
    card = _cached_component(app, "Card", "old")
    app.initialize()
    old_key = component_cache_key(card, vary={})
    backend.slow.set()
    writer = _start(lambda: card().render().serialize())
    try:
        assert backend.writing.wait(_JOIN_TIMEOUT)
        backend.slow.clear()
        card.template = "<p>new</p>"
        _finish(_start(card.reset_template), timeout=2.0)
    finally:
        backend.release.set()
    _finish(writer)
    assert backend.get(old_key) is None
    assert "new" in card().render().serialize()
