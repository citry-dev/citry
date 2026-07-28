"""
Cross-host acceptance tests for the Events HTTP contract (WP18).

The same representative calls run through mounted Django and FastAPI hosts.
Each scenario first locks its protocol and HTTP outcome, then the final
assertion compares normalized responses so host-adapter drift cannot hide
behind two separate suites.
"""

from __future__ import annotations

import json
import sys
import types
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Protocol
from unittest.mock import patch
from urllib.parse import urlencode

import pytest

django = pytest.importorskip("django", reason="the Events host-parity tests need Django")
fastapi = pytest.importorskip("fastapi", reason="the Events host-parity tests need FastAPI")
pytest.importorskip("httpx", reason="Starlette's TestClient needs httpx")

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(ALLOWED_HOSTS=["*"])
    django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import override_settings  # noqa: E402
from django.urls import clear_url_caches, include, path  # noqa: E402
from django.utils.decorators import decorator_from_middleware  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from citry import Citry, Component  # noqa: E402
from citry.contrib.django import urlpatterns as django_urlpatterns  # noqa: E402
from citry.contrib.fastapi import mount as mount_fastapi  # noqa: E402
from citry.ext.events import event  # noqa: E402
from citry.ext.events.tokens import mint_state_token  # noqa: E402

SIGNING_KEY = "wp18-host-parity-secret"
FIXED_NOW = 1_700_000_000.0
RUNTIME_HEADERS = {"X-Citry-Events": "1"}
ENVELOPE_CONTENT_TYPE = "application/citry-events+json"
FIXED_RENDER_ID = "wp18_parity"

_urlconf_serial = 0


class _TextIn:
    text: str


class _CountIn:
    count: int


@pytest.fixture(autouse=True)
def _pinned_token_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: FIXED_NOW)


def _fixture_component(c: Citry) -> type[Component]:
    """Build the one component shared by every host-parity scenario."""

    class ParityState:
        text: str = ""

        def render(self) -> Any:
            return HostParity(text=self.text)

    class HostParity(Component):
        citry = c

        class Kwargs:
            text: str = ""

        State = ParityState

        class Events:
            def save(self, data: _TextIn, state: ParityState) -> Any:
                state.text = data.text
                return state.render()

            def quiet(self, state: ParityState) -> None:
                return None

            @event(methods=("GET",))
            def echo(self, data: _TextIn) -> dict[str, str]:
                return {"echo": data.text}

            def add(self, data: _CountIn) -> dict[str, int]:
                return {"total": data.count + 1}

        def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, str]:
            return {"text": kwargs.text}

        template = """
            <p>{{ text }}</p>
        """

    return HostParity


def _token(component: type[Component], *, text: str = "") -> str:
    return mint_state_token(
        component.State(text=text),
        class_id=component.class_id,
        secret=SIGNING_KEY,
        max_age=None,
        max_bytes=8192,
    )


class _Response(Protocol):
    status_code: int
    headers: Mapping[str, str]
    content: bytes

    def json(self) -> Any: ...


@dataclass(frozen=True)
class _Snapshot:
    status: int
    content_type: str
    body: Any
    cache_control: str | None = None


@dataclass
class _MountedHost:
    name: str
    client: Any
    component: type[Component]

    def event_url(self, event_name: str) -> str:
        return f"/citry/ext/events/e/{self.component.class_id}/{event_name}"

    def post_envelope(self, event_name: str, call: dict[str, Any]) -> _Response:
        envelope = {"protocol": "citry-events/1", "requestId": "parity", "calls": [{"args": {}, **call}]}
        return self.post_raw_envelope(self.event_url(event_name), envelope)

    def post_raw_envelope(self, url: str, envelope: dict[str, Any]) -> _Response:
        if "/ext/events/e/" in url:
            component_class_id, handler_name = url.rsplit("/", 2)[-2:]
            envelope = {
                **envelope,
                "calls": [
                    {
                        "componentClassId": component_class_id,
                        "handlerName": handler_name,
                        "args": {},
                        **call,
                    }
                    if isinstance(call, dict)
                    else call
                    for call in envelope.get("calls", [])
                ],
            }
        headers = {"Content-Type": ENVELOPE_CONTENT_TYPE, **RUNTIME_HEADERS}
        if self.name == "django":
            return self.client.post(
                url,
                data=json.dumps(envelope),
                content_type=ENVELOPE_CONTENT_TYPE,
                headers=RUNTIME_HEADERS,
            )
        return self.client.post(url, content=json.dumps(envelope), headers=headers)

    def get(self, event_name: str, query: dict[str, str]) -> _Response:
        if self.name == "django":
            return self.client.get(self.event_url(event_name), data=query)
        return self.client.get(self.event_url(event_name), params=query)

    def post_form(self, event_name: str, fields: dict[str, str]) -> _Response:
        if self.name == "django":
            return self.client.post(
                self.event_url(event_name),
                data=urlencode(fields),
                content_type="application/x-www-form-urlencoded",
            )
        return self.client.post(self.event_url(event_name), data=fields)

    def post_raw_form(self, event_name: str, body: bytes) -> _Response:
        if self.name == "django":
            return self.client.post(
                self.event_url(event_name),
                data=body,
                content_type="application/x-www-form-urlencoded",
            )
        return self.client.post(
            self.event_url(event_name),
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )


def _response_text(response: _Response) -> str:
    return response.content.decode()


def _json_snapshot(response: _Response) -> _Snapshot:
    return _Snapshot(
        status=response.status_code,
        content_type=response.headers["content-type"].split(";", 1)[0],
        body=response.json(),
        cache_control=response.headers.get("cache-control"),
    )


def _checked_fragment(html: str, expected_text: str) -> str:
    """Check the fixture's identity facts, then retain every response byte."""
    assert expected_text in html
    assert f'data-cid="{FIXED_RENDER_ID}"' in html
    assert "data-citry-graph" in html
    assert "data-citry-events" in html
    return html


def _checked_render_html(snapshot: _Snapshot, expected_text: str) -> _Snapshot:
    """Retain the complete render body after checking its expected fixture facts."""
    body = json.loads(json.dumps(snapshot.body))
    action = body["results"][0]["actions"][0]
    assert action["action"] == "render"
    action["html"] = _checked_fragment(action["html"], expected_text)
    return _Snapshot(snapshot.status, snapshot.content_type, body, snapshot.cache_control)


def _happy_stateful_render(host: _MountedHost) -> _Snapshot:
    response = host.post_envelope(
        "save",
        {
            "callerRenderId": "parity_i1",
            "args": {"text": "Hello from parity"},
            "stateToken": _token(host.component),
            "sendSequence": 7,
        },
    )
    snapshot = _checked_render_html(_json_snapshot(response), "Hello from parity")
    assert snapshot.status == 200
    assert snapshot.body["results"][0]["sendSequence"] == 7
    assert snapshot.body["results"][0]["actions"][0]["target"] == "render:parity_i1"
    return snapshot


def _stateless_get(host: _MountedHost) -> _Snapshot:
    snapshot = _json_snapshot(host.get("echo", {"text": "hello"}))
    assert snapshot.status == 200
    assert snapshot.cache_control == "no-store"
    assert snapshot.body["results"] == [
        {"ok": True, "actions": [{"action": "data", "value": {"echo": "hello"}}]},
    ]
    return snapshot


def _validation_and_unknown_errors(host: _MountedHost) -> tuple[_Snapshot, _Snapshot]:
    invalid = _json_snapshot(host.post_envelope("add", {"args": {"count": "three"}}))
    unknown = _json_snapshot(host.post_envelope("missing", {"args": {}}))
    assert invalid.status == 422
    assert invalid.body["results"][0]["error"] == {
        "status": 422,
        "code": "invalid_args",
        "message": "The args for event 'add' on component 'HostParity' did not validate.",
        "fieldErrors": {"count": "Expected int, got str."},
    }
    assert unknown.status == 404
    assert unknown.body["results"][0]["error"]["code"] == "unknown_event"
    return invalid, unknown


def _unknown_component(host: _MountedHost) -> _Snapshot:
    response = host.post_raw_envelope(
        "/citry/ext/events/e/NotRegistered_deadbeef/echo",
        {"protocol": "citry-events/1", "requestId": "unknown-component", "calls": [{"args": {}}]},
    )
    snapshot = _json_snapshot(response)
    assert snapshot.status == 404
    assert snapshot.body == {
        "protocol": "citry-events/1",
        "requestId": "unknown-component",
        "results": [
            {
                "ok": False,
                "error": {
                    "status": 404,
                    "code": "unknown_component",
                    "message": "No component with class id 'NotRegistered_deadbeef' is registered.",
                },
            },
        ],
    }
    return snapshot


def _mixed_batch(host: _MountedHost) -> _Snapshot:
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "mixed",
        "calls": [
            {"componentClassId": host.component.class_id, "handlerName": "echo", "args": {"text": "one"}},
            {"componentClassId": host.component.class_id, "handlerName": "missing", "args": {}},
        ],
    }
    snapshot = _json_snapshot(host.post_raw_envelope("/citry/ext/events/call", envelope))
    assert snapshot.status == 200
    first, second = snapshot.body["results"]
    assert first == {"ok": True, "actions": [{"action": "data", "value": {"echo": "one"}}]}
    assert second["ok"] is False
    assert second["error"]["status"] == 404
    assert second["error"]["code"] == "unknown_event"
    return snapshot


def _compatibility_form(host: _MountedHost) -> _Snapshot:
    response = host.post_form(
        "save",
        {
            "text": "No-JS parity",
            "_citry_state_token": _token(host.component),
            "_citry_caller_render_id": "parity_form",
        },
    )
    text = _response_text(response)
    assert response.status_code == 200
    return _Snapshot(
        status=response.status_code,
        content_type=response.headers["content-type"].split(";", 1)[0],
        body=_checked_fragment(text, "No-JS parity"),
    )


def _invalid_utf8_compatibility_form(host: _MountedHost) -> _Snapshot:
    response = host.post_raw_form("save", b"text=ok&broken=\xff")
    snapshot = _Snapshot(
        status=response.status_code,
        content_type=response.headers["content-type"].split(";", 1)[0],
        body=_response_text(response),
    )
    assert snapshot == _Snapshot(
        status=400,
        content_type="text/plain",
        body="The form body is not valid UTF-8.",
    )
    return snapshot


_Scenario = Callable[[_MountedHost], Any]

SCENARIOS: tuple[Any, ...] = (
    pytest.param(_happy_stateful_render, id="happy-stateful-render"),
    pytest.param(_stateless_get, id="stateless-get"),
    pytest.param(_validation_and_unknown_errors, id="validation-and-unknown-errors"),
    pytest.param(_unknown_component, id="unknown-component"),
    pytest.param(_mixed_batch, id="mixed-batch-always-200"),
    pytest.param(_compatibility_form, id="compatibility-form"),
    pytest.param(_invalid_utf8_compatibility_form, id="invalid-utf8-compatibility-form"),
)


@contextmanager
def _mounted_fastapi_host() -> Iterator[_MountedHost]:
    citry = Citry(secret=SIGNING_KEY)
    component = _fixture_component(citry)
    app = fastapi.FastAPI()
    mount_fastapi(app, citry)
    client = TestClient(app)
    try:
        yield _MountedHost("fastapi", client, component)
    finally:
        client.close()


def _install_django_urlconf(citry: Citry, extra_patterns: list[Any] | None = None) -> tuple[str, Any]:
    global _urlconf_serial  # noqa: PLW0603 - Django requires an importable module name
    _urlconf_serial += 1
    module_name = f"citry_wp18_host_parity_urls_{_urlconf_serial}"
    module = types.ModuleType(module_name)
    routes = django_urlpatterns(citry, prefix="/citry")
    module.urlpatterns = [*(extra_patterns or []), path("citry/", include(routes))]
    sys.modules[module_name] = module
    clear_url_caches()
    override = override_settings(ROOT_URLCONF=module_name, ALLOWED_HOSTS=["*"], MIDDLEWARE=[])
    override.enable()
    return module_name, override


@contextmanager
def _mounted_django_host() -> Iterator[_MountedHost]:
    citry = Citry(secret=SIGNING_KEY)
    component = _fixture_component(citry)
    module_name, override = _install_django_urlconf(citry)
    try:
        yield _MountedHost("django", Client(), component)
    finally:
        override.disable()
        sys.modules.pop(module_name, None)
        clear_url_caches()


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_django_and_fastapi_have_the_same_events_http_contract(scenario: _Scenario) -> None:
    snapshots: dict[str, Any] = {}
    for mounted_host in (_mounted_django_host, _mounted_fastapi_host):
        with mounted_host() as host, patch("citry.component.gen_render_id", return_value=FIXED_RENDER_ID):
            snapshots[host.name] = scenario(host)

    assert snapshots["django"] == snapshots["fastapi"]


class _ExactSaveMiddleware:
    """A Django view middleware used only by the exact save URL below."""

    paths: list[str] = []

    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        return self.get_response(request)

    def process_view(self, request: Any, _view_func: Any, _view_args: Any, _view_kwargs: Any) -> None:
        type(self).paths.append(request.path)

    def process_response(self, _request: Any, response: Any) -> Any:
        response["X-WP18-Policy"] = "save-only"
        return response


def test_django_can_attach_host_middleware_to_one_exact_event_url() -> None:
    citry = Citry(secret=SIGNING_KEY)
    component = _fixture_component(citry)
    routes = django_urlpatterns(citry, prefix="/citry")
    dispatch = next(route for route in routes if route.name == "citry_events_dispatch")
    save_url = f"/citry/ext/events/e/{component.class_id}/save"
    decorated_save = decorator_from_middleware(_ExactSaveMiddleware)(dispatch.callback)
    exact_save_pattern = path(
        save_url.removeprefix("/"),
        decorated_save,
        {"class_id": component.class_id, "event": "save"},
        name="wp18_exact_save",
    )
    _ExactSaveMiddleware.paths.clear()
    module_name, override = _install_django_urlconf(citry, [exact_save_pattern])
    host = _MountedHost("django", Client(), component)
    try:
        save = host.post_envelope(
            "save",
            {"args": {"text": "guarded"}, "stateToken": _token(component), "callerRenderId": "policy_i1"},
        )
        sibling = host.post_envelope("quiet", {"args": {}, "stateToken": _token(component)})
    finally:
        override.disable()
        sys.modules.pop(module_name, None)
        clear_url_caches()

    assert save.status_code == 200
    assert save.headers["X-WP18-Policy"] == "save-only"
    assert sibling.status_code == 200
    assert "X-WP18-Policy" not in sibling.headers
    assert _ExactSaveMiddleware.paths == [save_url]
