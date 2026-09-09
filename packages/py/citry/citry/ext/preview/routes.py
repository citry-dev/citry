"""HTTP handlers registered exclusively by preview commands."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from citry.ext.preview.rendering import PreviewNotFound
from citry.util.routing import RouteRequest, RouteResponse, URLRoute

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry.ext.preview.rendering import PreviewRenderer

_LOG = logging.getLogger(__name__)


def preview_routes(renderer: PreviewRenderer) -> tuple[URLRoute, ...]:
    """Build a fresh route table for a command host, never for Citry.urls."""

    def respond(
        request: RouteRequest, callback: Callable[[], str], allowed: set[str], required: set[str], mime: str
    ) -> RouteResponse:
        status = 200
        content = ""
        if request.method not in {"GET", "HEAD"}:
            return RouteResponse("Method Not Allowed", status=405, headers=(("Allow", "GET, HEAD"),))
        if (
            set(request.query) - allowed
            or required - set(request.query)
            or any(len(values) != 1 or not values[0] for values in request.query.values())
        ):
            status, content, mime = 400, "Invalid preview query.", "text/plain; charset=utf-8"
        else:
            try:
                content = callback()
            except PreviewNotFound:
                status, content, mime = 404, "Preview not found.", "text/plain; charset=utf-8"
            except Exception:  # noqa: BLE001 - HTTP failures must not expose Python internals
                _LOG.exception("Preview request failed: %s", request.path)
                status, content, mime = 500, "Preview rendering failed; see server logs.", "text/plain; charset=utf-8"
        return RouteResponse(
            "" if request.method == "HEAD" else content,
            status=status,
            content_type=mime,
            headers=(("Cache-Control", "no-store"),),
        )

    def catalog(request: RouteRequest) -> RouteResponse:
        return respond(request, lambda: json.dumps(renderer.catalog()), set(), set(), "application/json")

    def render(request: RouteRequest, *, component_id: str) -> RouteResponse:
        return respond(
            request,
            lambda: renderer.render_page(component_id, request.query["variant"][0]).serialize(
                deps_strategy="document"
            ),
            {"variant"},
            {"variant"},
            "text/html; charset=utf-8",
        )

    def gallery(request: RouteRequest) -> RouteResponse:
        return respond(
            request,
            lambda: renderer.render_gallery(request.query.get("component", (None,))[0]).serialize(
                deps_strategy="document"
            ),
            {"component"},
            set(),
            "text/html; charset=utf-8",
        )

    return (
        URLRoute("catalog", handler=catalog, methods=("GET", "HEAD")),
        URLRoute("render/{component_id}", handler=render, methods=("GET", "HEAD")),
        URLRoute("gallery", handler=gallery, methods=("GET", "HEAD")),
    )
