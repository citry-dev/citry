"""
The HTTP CSRF layers of the ``events`` extension (design
``docs/design/events.md`` 7.4).

Three layers protect the events routes, stacked:

- **The always-on floor**, applied here to every non-GET call: a request
  carrying a JSON body (the envelope's ``application/citry-events+json``
  vendor type, any other ``+json`` suffix type, and flat
  ``application/json`` alike) must send the ``X-Citry-Events`` header
  (HTML forms cannot attach custom headers, and cross-origin JS attempting
  it hits a CORS preflight the browser blocks), and when the browser
  supplied ``Origin`` or ``Sec-Fetch-Site`` headers, they must say
  same-origin. The floor never turns off.
- **The host token layer**: under Django the events routes are plain views,
  so Django's CSRF middleware applies to them untouched; nothing in citry
  reimplements or bypasses it (no ``csrf_exempt`` anywhere), and no
  per-handler policy turns it off (the middleware answers before the view
  ever resolves a handler). Hosts without a token scheme (plain ASGI/WSGI,
  FastAPI, Flask) have no token layer.
- **The per-handler policy** governs the citry-side check that runs after
  the floor: ``"auto"`` and ``False`` add no citry-side token check, and a
  callable adds one (it receives the request and raises to reject). The
  host's own token check, where the host has one, applies on top of
  whatever the policy says.

GET handlers are read-only by contract and exempt from all of it (design
7.4): their CSRF story is "GET must not mutate", which the method allowlist
already enforces.

The dispatcher runs the check per call (so a batch can mix outcomes) and
answers any rejection as the wire error ``csrf_failed`` (403).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from citry.ext.events.errors import EventError
from citry.util.logger import logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry.ext.events.extension import EventHandler
    from citry.util.routing import RouteRequest

__all__ = ["X_CITRY_EVENTS_HEADER", "build_csrf_check", "enforce_floor"]

# The custom header the client runtime sends on every call. Its presence is
# the floor's proof that the request came from same-origin JS (or a caller
# like curl that deliberately added it), never from a bare HTML form.
X_CITRY_EVENTS_HEADER = "X-Citry-Events"
"""Header required on JSON Events calls as part of the same-origin CSRF check."""

# The rejection message is contract (the protocol examples lock it); the
# specific reason goes to the debug log for operators.
_MSG_CSRF_FAILED = "The call failed the CSRF check; reload the page and try again."

# Sec-Fetch-Site values the floor accepts: the page's own origin, and
# browser-initiated navigation ("none"). "same-site" (a sibling subdomain)
# and "cross-site" are rejected, matching the strict same-origin stance.
_ACCEPTED_FETCH_SITES = ("same-origin", "none")


def _reject(reason: str) -> None:
    logger.debug(f"Events CSRF floor rejected the request: {reason}")
    raise EventError(_MSG_CSRF_FAILED, status=403)


def enforce_floor(request: RouteRequest) -> None:
    """
    The always-on CSRF floor for one non-GET events request.

    Raises:
        EventError: With status 403 when the request fails a floor check;
            the dispatcher answers it as the ``csrf_failed`` wire error.

    """
    # Every JSON-bodied call must present the header, whatever the exact
    # content type: the envelope's application/citry-events+json vendor
    # type, any other +json suffix type, and flat application/json alike
    # (design 7.4), so an API client sends one static header. A urlencoded
    # form post is the compatibility path and is covered by the same-origin
    # checks plus the host token.
    base_type = request.content_type.split(";")[0].strip().lower()
    json_bodied = base_type == "application/json" or base_type.endswith("+json")
    if json_bodied and X_CITRY_EVENTS_HEADER.lower() not in request.headers:
        _reject(f"a JSON call without the {X_CITRY_EVENTS_HEADER} header")

    origin = request.headers.get("origin")
    if origin is not None:
        # The Origin header is browser-set and unforgeable by page JS;
        # compare its authority against the request's own Host.
        origin_host = urlsplit(origin).netloc.lower()
        host = (request.headers.get("host") or "").lower()
        if not origin_host or origin_host != host:
            _reject(f"Origin {origin!r} does not match the request host {host!r}")

    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site is not None and fetch_site.lower() not in _ACCEPTED_FETCH_SITES:
        _reject(f"Sec-Fetch-Site is {fetch_site!r}")


def build_csrf_check(request: RouteRequest) -> Callable[[EventHandler], None]:
    """
    The per-call CSRF check the HTTP routes hand the dispatcher.

    The returned callable receives the resolved handler and applies the
    layers in order: nothing for GET, then the floor, then the handler's
    own policy (``"auto"`` and ``False`` add no citry-side token check; a
    callable is called with the request and raises to reject). A host
    framework's own CSRF protection (Django's middleware) runs before any
    of this and is not governed by the policy.

    Args:
        request: The incoming HTTP request the check closes over.

    Returns:
        The check the dispatcher calls once per call.

    """

    def check(handler: EventHandler) -> None:
        if request.method == "GET":
            return
        enforce_floor(request)
        policy = handler.csrf
        if callable(policy):
            policy(request)

    return check
