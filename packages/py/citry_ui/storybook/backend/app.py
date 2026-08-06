"""Citry-native ASGI renderer for the Storybook adapter spike."""

from __future__ import annotations

import json
import threading
from typing import TYPE_CHECKING

import citry_ui
from backend.catalog import CATALOG_SCHEMA_VERSION, SCENARIOS, SCENARIOS_BY_ID, ScenarioArgsError, StorybookScenario
from backend.components import STORYBOOK_COMPONENTS, CStorybookFragment, CStorybookPage
from citry import Citry, Extension, RouteRequest, RouteResponse, URLRoute
from citry.contrib.asgi import asgi_app

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, MutableMapping
    from typing import Any

    Scope = MutableMapping[str, Any]
    Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
    Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]

_ALLOWED_ORIGINS = frozenset(
    f"http://{host}:{port}" for host in ("127.0.0.1", "localhost") for port in (6106, 6107, 6206, 6207)
)
_ALLOWED_HOSTS = frozenset(("127.0.0.1:8123", "localhost:8123"))
_MOUNT_PREFIX = "/citry"
_RENDER_COUNTS: dict[str, int] = {}
_RENDER_COUNTS_LOCK = threading.Lock()


def _response(
    request: RouteRequest,
    content: str,
    *,
    content_type: str = "text/plain",
    status: int = 200,
) -> RouteResponse:
    headers: tuple[tuple[str, str], ...] = (("Cache-Control", "no-store"),)
    origin = request.headers.get("origin")
    if origin in _ALLOWED_ORIGINS:
        headers = (
            *headers,
            ("Access-Control-Allow-Origin", origin),
            ("Vary", "Origin"),
        )
    return RouteResponse(
        content=content,
        content_type=content_type,
        status=status,
        headers=headers,
    )


def _request_policy_error(request: RouteRequest) -> RouteResponse | None:
    host = request.headers.get("host")
    if host not in _ALLOWED_HOSTS:
        return _response(request, "Untrusted Storybook scenario Host.", status=403)
    origin = request.headers.get("origin")
    if origin is not None and origin not in _ALLOWED_ORIGINS:
        return _response(request, "Untrusted Storybook scenario Origin.", status=403)
    return None


def _scenario(family: str, state: str) -> StorybookScenario | None:
    return SCENARIOS_BY_ID.get(f"{family}/{state}")


def _render(
    engine: Citry,
    scenario: StorybookScenario,
    request: RouteRequest,
    *,
    document: bool,
) -> RouteResponse:
    try:
        args = scenario.parse_query(request.query)
        generation = args.get("generation", "default")
        audit_key = f"{scenario.id}:{generation}"
        with _RENDER_COUNTS_LOCK:
            _RENDER_COUNTS[audit_key] = _RENDER_COUNTS.get(audit_key, 0) + 1
        content = scenario.render(args)
        if document:
            html = (
                CStorybookPage(
                    title=f"{scenario.group}: {scenario.title}",
                    scenario_id=scenario.id,
                    content=content,
                )
                .render(citry=engine)
                .serialize(deps_strategy="document")
            )
        else:
            rendered = CStorybookFragment(
                scenario_id=scenario.id,
                content=content,
            ).render(citry=engine)
            if scenario.client_interactive:
                html = rendered.serialize(deps_strategy="fragment")
            else:
                html = rendered.serialize(
                    deps_strategy="simple",
                    deps_position="prepend",
                )
    except ScenarioArgsError as error:
        return _response(request, str(error), status=400)
    return _response(request, html, content_type="text/html; charset=utf-8")


def _catalog(request: RouteRequest) -> RouteResponse:
    if (error := _request_policy_error(request)) is not None:
        return error
    manifest = {
        "schemaVersion": CATALOG_SCHEMA_VERSION,
        "scenarios": [
            {
                "id": scenario.id,
                "title": scenario.title,
                "group": scenario.group,
                "description": scenario.description,
                "usage": scenario.usage,
                "args": scenario.args,
                "argTypes": scenario.arg_types,
                "clientInteractive": scenario.client_interactive,
                "readySelector": scenario.ready_selector,
                "readyTimeoutMs": scenario.ready_timeout_ms,
                "standaloneUrl": f"{_MOUNT_PREFIX}/ext/storybook_scenarios/page/{scenario.id}",
            }
            for scenario in SCENARIOS
        ],
    }
    return _response(
        request,
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        content_type="application/json; charset=utf-8",
    )


def _audit(request: RouteRequest) -> RouteResponse:
    if (error := _request_policy_error(request)) is not None:
        return error
    with _RENDER_COUNTS_LOCK:
        counts = dict(sorted(_RENDER_COUNTS.items()))
    return _response(
        request,
        json.dumps({"renders": counts}, sort_keys=True) + "\n",
        content_type="application/json; charset=utf-8",
    )


class StorybookScenarios(Extension):
    """Expose only the private catalog's validated render routes."""

    name = "storybook_scenarios"

    @property
    def urls(self) -> list[URLRoute]:
        return [
            URLRoute("catalog", handler=_catalog, name="storybook_scenario_catalog"),
            URLRoute("audit", handler=_audit, name="storybook_scenario_audit"),
            URLRoute("render/{family}/{state}", handler=self.render, name="storybook_scenario_render"),
            URLRoute("page/{family}/{state}", handler=self.page, name="storybook_scenario_page"),
        ]

    def render(self, request: RouteRequest, *, family: str, state: str) -> RouteResponse:
        if (error := _request_policy_error(request)) is not None:
            return error
        scenario = _scenario(family, state)
        if scenario is None:
            return _response(request, "Unknown Citry UI scenario.", status=404)
        return _render(self.citry, scenario, request, document=False)

    def page(self, request: RouteRequest, *, family: str, state: str) -> RouteResponse:
        if (error := _request_policy_error(request)) is not None:
            return error
        scenario = _scenario(family, state)
        if scenario is None:
            return _response(request, "Unknown Citry UI scenario.", status=404)
        return _render(self.citry, scenario, request, document=True)


def create_engine() -> Citry:
    """Build the isolated engine used only by this contributor tool."""
    engine = Citry(autodiscover=False, extensions=[StorybookScenarios])
    engine.set_mounted_prefix(_MOUNT_PREFIX)
    engine.register_library(citry_ui)
    engine.register_library(STORYBOOK_COMPONENTS)
    engine.initialize()
    return engine


engine = create_engine()
_citry_app = asgi_app(engine)


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    """Mount the private Citry application at its advertised URL prefix."""
    if scope["type"] == "http":
        headers = {name.decode("latin-1").lower(): value.decode("latin-1") for name, value in scope.get("headers", ())}
        if headers.get("host") not in _ALLOWED_HOSTS or (
            (origin := headers.get("origin")) is not None and origin not in _ALLOWED_ORIGINS
        ):
            body = b"Untrusted Storybook scenario request."
            await send(
                {
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [
                        (b"content-type", b"text/plain; charset=utf-8"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        path = scope["path"]
        if path != _MOUNT_PREFIX and not path.startswith(f"{_MOUNT_PREFIX}/"):
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [(b"content-type", b"text/plain")],
                }
            )
            await send({"type": "http.response.body", "body": b"Not Found"})
            return
        scope = {**scope, "root_path": _MOUNT_PREFIX}
    await _citry_app(scope, receive, send)


__all__ = ["StorybookScenarios", "app", "create_engine", "engine"]
