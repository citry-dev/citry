"""Accumulate request-local rendering and output-preparation spans."""

from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from threading import get_ident
from time import perf_counter
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")
ASGIMessage = dict[str, Any]
ASGIScope = dict[str, Any]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIApplication = Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]]


@dataclass
class RenderTimings:
    duration: float = 0.0
    count: int = 0
    depth: int = 0
    thread: int | None = None


current: ContextVar[RenderTimings | None] = ContextVar("html_render_timings", default=None)


@dataclass
class PreparationTimings:
    """Accumulate disjoint output-preparation spans for one emitted payload."""

    duration: float = 0.0
    count: int = 0
    depth: int = 0


preparation_current: ContextVar[PreparationTimings | None] = ContextVar(
    "server_output_preparation_timings", default=None
)
preparation_pending: ContextVar[PreparationTimings | None] = ContextVar(
    "pending_server_output_preparation_timings", default=None
)


def pending_preparation() -> PreparationTimings:
    """Return the task-local payload accumulator, creating it when needed."""
    timing = preparation_pending.get()
    if timing is None:
        timing = PreparationTimings()
        preparation_pending.set(timing)
    return timing


def current_pending_preparation() -> PreparationTimings | None:
    """Return the task-local payload accumulator without creating one."""
    return preparation_pending.get()


def take_pending_preparation() -> PreparationTimings | None:
    """Consume the task-local payload accumulator before one emission."""
    timing = preparation_pending.get()
    preparation_pending.set(None)
    return timing


def discard_pending_preparation() -> None:
    """Discard preparation work that cannot produce a payload."""
    preparation_pending.set(None)


@contextmanager
def preparation_scope(timing: PreparationTimings) -> Iterator[None]:
    """Make one accumulator visible to selected construction and serialization spans."""
    token = preparation_current.set(timing)
    try:
        yield
    finally:
        preparation_current.reset(token)


@contextmanager
def preparation_span(timing: PreparationTimings | None = None) -> Iterator[None]:
    """Measure an outer preparation span while counting nested work once."""
    timing = timing or preparation_current.get()
    if timing is None:
        yield
        return
    outer = timing.depth == 0
    timing.depth += 1
    start = perf_counter() if outer else 0.0
    try:
        yield
    finally:
        timing.depth -= 1
        if outer:
            timing.duration += perf_counter() - start
            timing.count += 1


@contextmanager
def render_span() -> Iterator[None]:
    timing = current.get()
    if timing is None:
        yield
        return
    if timing.depth and timing.thread != get_ident():
        raise RuntimeError("Concurrent render threads within one request are unsupported")
    outer = timing.depth == 0
    if outer:
        timing.thread = get_ident()
    timing.depth += 1
    start = perf_counter() if outer else 0.0
    try:
        yield
    finally:
        timing.depth -= 1
        if outer:
            timing.duration += perf_counter() - start
            timing.count += 1
            timing.thread = None


def timed_render(function: Callable[P, R]) -> Callable[P, R]:
    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        with render_span():
            return function(*args, **kwargs)

    return wrapped


def instrument(owner: Any, name: str) -> None:
    """Wrap an adapter-selected synchronous method, preserving class binding."""
    descriptor = vars(owner).get(name)
    if isinstance(descriptor, classmethod):
        setattr(owner, name, classmethod(timed_render(descriptor.__func__)))
    else:
        setattr(owner, name, timed_render(getattr(owner, name)))


class RenderTimingMiddleware:
    """Share one mutable accumulator across ASGI and worker-thread contexts."""

    def __init__(self, application: ASGIApplication) -> None:
        self.application = application

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        if scope["type"] != "http":
            await self.application(scope, receive, send)
            return
        timing = RenderTimings()
        token = current.set(timing)

        async def observed_send(message: ASGIMessage) -> None:
            if message["type"] == "http.response.start" and timing.count and message["status"] < 400:
                headers = list(message.get("headers", []))
                value = f"render;dur={timing.duration * 1000:.3f}".encode("ascii")
                existing = [v for k, v in headers if k.lower() == b"server-timing"]
                headers = [(k, v) for k, v in headers if k.lower() != b"server-timing"]
                headers.append((b"server-timing", b", ".join([*existing, value])))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.application(scope, receive, observed_send)
        finally:
            current.reset(token)
