"""
The ``ViewEvents`` compatibility shim of the ``events`` extension.

For components ported from verb-shaped view code (django-components'
``Component.View`` and friends), where one method per HTTP verb handles the
whole request. A component's ``class Events(ViewEvents):`` keeps that shape:
the seven verb names (``get``, ``post``, ``put``, ``patch``, ``delete``,
``head``, ``options``) become event handlers that answer their own HTTP
method, and the extension serves one extra route,
``ext/events/e/{class_id}``, which picks the handler from the request
method alone. Design: ``docs/design/events.md`` section 10.

Everything else is plain ``Events`` behavior: verb handlers declare the same
parameter vocabulary (minus ``state``), validate ``data`` the same way, and
return the same actions. Only the verb-shaped route maps mechanically. A port
must adapt host-specific request parsing and response construction to typed
``data``, the neutral ``request``, and Events return values. It can later grow
named events next to its verbs and drop the shim one handler at a time.
"""

from __future__ import annotations

from dataclasses import replace
from inspect import signature
from types import FunctionType
from typing import TYPE_CHECKING, Any

from citry.ext.events.codecs import FormCodec
from citry.ext.events.config import Events
from citry.ext.events.dispatcher import EventsDispatcher
from citry.ext.events.handlers import EVENT_OPTIONS_ATTR, EventOptions, event_options

# The transport translation is the per-event route's, unchanged; only the
# event name comes from the HTTP method instead of the URL, so the verb
# route reuses the routes module's package-private request pipeline rather
# than duplicating it.
from citry.ext.events.routes import _serve_call, _serve_call_async
from citry.util.routing import RouteRequest, RouteResponse, URLRoute

if TYPE_CHECKING:
    from citry.citry import Citry

__all__ = [
    "VERB_HANDLER_NAMES",
    "VIEW_EVENT_PATH",
    "ViewEvents",
    "view_events_routes",
]

# The handler names the shim reserves, one per HTTP verb (design 10).
VERB_HANDLER_NAMES = ("get", "post", "put", "patch", "delete", "head", "options")

# The shim's extra route: the per-event path without the event segment.
# ``{class_id}`` matches a single path segment, so this route and the
# two-segment per-event route can never claim each other's requests.
VIEW_EVENT_PATH = "ext/events/e/{class_id}"

_VERB_METHODS = tuple(verb.upper() for verb in VERB_HANDLER_NAMES)


class ViewEvents(Events):
    """
    Base class for verb-shaped ``Events`` classes, for ports from view code.

    Subclass it as a component's ``class Events(ViewEvents):`` and the seven
    HTTP verb names (``get``, ``post``, ``put``, ``patch``, ``delete``,
    ``head``, ``options``) become reserved handler names: each one accepts
    exactly its own HTTP method, and the extra route
    ``ext/events/e/{class_id}`` dispatches to it from the request method
    alone, so a form can post to the component URL with no event name in it.
    Existing handler bodies still need to replace host-specific request
    parsing and responses with typed ``data``, the neutral ``request``, and
    Events return values.

    The verb compatibility route does not require a State token, and verb
    handlers cannot inject ``state``. A named runtime call to a verb on a
    State-declaring component may still carry the component token. Stateful
    work belongs in named event handlers, which can live on the same class.

    Prefer naming events after actions: once a component has more than one
    mutation, one ``post`` that inspects the payload is the multiplexing
    this extension exists to remove. Keep the verbs for the initial port,
    then split them into named handlers (``save``, ``archive``, ...) as the
    component grows.

    Example:
        ```python
        from citry import Component
        from citry.ext.events import ViewEvents

        class ContactIn:
            email: str = ""
            message: str = ""

        class ContactForm(Component):
            class Events(ViewEvents):
                def post(self, data: ContactIn, request):
                    send_message(data.email, data.message)
                    return ContactForm()

        # <form method="post"> posting to ext/events/e/{class_id}
        # reaches ContactForm.Events.post.
        ```

    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for verb in VERB_HANDLER_NAMES:
            func = cls.__dict__.get(verb)
            if not isinstance(func, FunctionType):
                continue
            parameters = tuple(signature(func).parameters)
            if "state" in parameters:
                msg = (
                    f"{cls.__name__}.{verb} declares 'state', but verb handlers omit it: they"
                    f" serve the token-optional verb compatibility route and do not expose State."
                    f" Move stateful work into a named event handler (which can live on the same class)."
                )
                raise ValueError(msg)
            options = event_options(func)
            if options is None:
                options = EventOptions(methods=(verb.upper(),))
            elif options.methods is None:
                options = replace(options, methods=(verb.upper(),))
            else:
                # An explicit @event(methods=...) is the user's call; the
                # shim only fills the verb in when nothing else did.
                continue
            setattr(func, EVENT_OPTIONS_ATTR, options)


################################################
# THE VERB ROUTE
################################################


def _as_empty_form(request: RouteRequest) -> RouteRequest:
    """
    Present a bodyless non-GET request as an empty form post.

    A ported caller's natural ``fetch(url, {method: "DELETE"})`` sends no
    body and no content type; decoding it as an empty form post gives the
    verb handler its empty args instead of a no-codec rejection. GET stays
    untouched (its args ride the query string).
    """
    if request.method != "GET" and not request.body and not request.content_type:
        return replace(request, content_type=FormCodec.content_type)
    return request


def view_events_routes(citry: Citry) -> list[URLRoute]:
    """The shim's route table: the verb-dispatch route, bound to one ``Citry`` instance."""
    dispatcher = EventsDispatcher()

    def accepts_view_events(class_id: str) -> bool:
        try:
            comp_cls = citry.get_component_by_class_id(class_id)
        except KeyError:
            # Let the shared dispatcher preserve its pointed unknown-component
            # response. Only known, non-ViewEvents classes are hidden here.
            return True
        events_cls = getattr(comp_cls, "Events", None)
        return isinstance(events_cls, type) and issubclass(events_cls, ViewEvents)

    def serve_view_event(request: RouteRequest, *, class_id: str) -> RouteResponse:
        # The HTTP method names the event; everything downstream (method
        # allowlist, codecs, CSRF, dispatch, compat mode) is the per-event
        # route's pipeline with that name as the URL-authoritative event.
        if not accepts_view_events(class_id):
            return RouteResponse(content="Not Found", status=404)
        return _serve_call(
            _as_empty_form(request),
            citry,
            dispatcher,
            url_component=class_id,
            url_event=request.method.lower(),
        )

    async def serve_view_event_async(request: RouteRequest, *, class_id: str) -> RouteResponse:
        if not accepts_view_events(class_id):
            return RouteResponse(content="Not Found", status=404)
        return await _serve_call_async(
            _as_empty_form(request),
            citry,
            dispatcher,
            url_component=class_id,
            url_event=request.method.lower(),
        )

    return [
        URLRoute(
            VIEW_EVENT_PATH,
            handler=serve_view_event,
            handler_async=serve_view_event_async,
            name="citry_events_view_dispatch",
            methods=_VERB_METHODS,
        ),
    ]
