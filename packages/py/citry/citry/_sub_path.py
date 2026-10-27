"""
The sub-path a host app is served below, as the current request sees it.

An app served below a sub-path, such as ``/shop``, receives requests whose
paths start with ``/shop``, while its routes are declared without it.
Citry's own URLs (the client runtime, the Events endpoints, compiled
definitions) must start with it too, or the browser asks the site root for
them. Where the sub-path comes from depends on the framework and on the
deployment: a server such as gunicorn or uvicorn can set it per request,
and the framework's own setting gives it outside a request. Each web integration's ``mount()`` registers a
function that answers with the current sub-path (see
``Citry._set_sub_path_reader``), and the FastAPI and Flask integrations
record the request's value here while the request runs.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from collections.abc import Iterator

# The sub-path of the request being handled, set by the integration that
# received it, or None outside a request. A context variable, so threads
# and tasks that serve different requests each see their own value, and a
# worker thread that Starlette starts for a sync view inherits it. A thread
# started with `loop.run_in_executor()` or `threading.Thread` does not.
_REQUEST_SUB_PATH: ContextVar[str | None] = ContextVar("citry_request_sub_path", default=None)


def normalize_sub_path(value: object) -> str:
    """
    Return the sub-path in the form URLs start with it: ``/shop``, or ``""`` for the site root.

    The framework settings and server values that hold it may end in ``/``
    (Django's script prefix always does) or be ``/`` for the site root.
    Characters a URL path cannot hold, such as a space, are percent-encoded;
    a ``%`` is kept, so a value that is already encoded stays as it is. A
    value that is not a string, does not start with one ``/``, or starts
    with ``//`` counts as the site root. Such a value can come from a proxy
    header, and ``//host`` would point the page's scripts at another site.
    """
    if not isinstance(value, str) or not value.startswith("/") or value.startswith("//"):
        return ""
    # The characters RFC 3986 allows in a path, plus "%".
    return quote(value.rstrip("/"), safe="/:@!$&'()*+,;=%")


def request_sub_path() -> str | None:
    """Return the sub-path the current request recorded, or ``None`` outside a request."""
    return _REQUEST_SUB_PATH.get()


@contextmanager
def recording_sub_path(value: object) -> Iterator[None]:
    """Make ``value`` the current request's sub-path while the block runs."""
    token = _REQUEST_SUB_PATH.set(normalize_sub_path(value))
    try:
        yield
    finally:
        _REQUEST_SUB_PATH.reset(token)
