"""
Django parity tests for the events HTTP layer (WP13): the same pipeline the
FastAPI suite drives (test_events_routes.py), served through
``citry.contrib.django.urlpatterns`` and Django's test client, plus the
host-token CSRF proof: the events routes run under Django's CSRF middleware
untouched, and no view is ``csrf_exempt`` (docs/design/events.md 7.4 and its
section 15 falsifier).

Like the other Django suites, this file skips without Django installed (it
ships in the ``benchmark`` dependency group).
"""

import json
import logging
import sys
import types
from urllib.parse import urlencode

import pytest

django = pytest.importorskip("django", reason="the Django events tests need django")

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(ALLOWED_HOSTS=["*"])
    django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import override_settings  # noqa: E402
from django.urls import clear_url_caches, include, path  # noqa: E402

from citry import Citry, Component  # noqa: E402
from citry.contrib.django import urlpatterns  # noqa: E402
from citry.ext.events import ViewEvents, event  # noqa: E402
from citry.ext.events.tokens import mint_state_token  # noqa: E402

SIGNING_KEY = "test-secret-key"
FIXED_NOW = 1_700_000_000.0
RUNTIME_HEADERS = {"X-Citry-Events": "1"}

# A well-formed Django CSRF secret: 32 characters from the allowed alphabet.
CSRF_SECRET = "a" * 32

_URLCONF_NAME = "citry_events_test_urlconf"


@pytest.fixture(autouse=True)
def _pinned_token_clock(monkeypatch):
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: FIXED_NOW)


def _citry():
    return Citry(secret=SIGNING_KEY)


def _greeter(c):
    """The same fixture component shape the FastAPI suite drives (parity)."""

    class GreetIn:
        text: str = ""

    class GreeterState:
        text: str = ""

        def render(self):
            return Greeter(text=self.text)

    class Greeter(Component):
        citry = c

        class Kwargs:
            text: str = ""

        State = GreeterState

        class Events:
            def save(self, data: GreetIn, state):
                state.text = data.text
                return state.render()

            def quiet(self, state):
                return None

            @event(methods=("GET",))
            def echo(self, data: GreetIn):
                return {"echo": data.text}

        def template_data(self, kwargs, slots):
            return {"text": kwargs.text}

        template = """
            <p>{{ text }}</p>
        """

    return Greeter


def _token(comp_cls, **state_kwargs):
    return mint_state_token(
        comp_cls.State(**state_kwargs),
        class_id=comp_cls.class_id,
        secret=SIGNING_KEY,
        max_age=None,
        max_bytes=8192,
    )


@pytest.fixture
def mounted():
    """Mount one Citry instance's routes at /citry/ in a throwaway URLconf."""

    def mount(c, middleware=()):
        patterns = urlpatterns(c, prefix="/citry")
        module = types.ModuleType(_URLCONF_NAME)
        module.urlpatterns = [path("citry/", include(patterns))]
        sys.modules[_URLCONF_NAME] = module
        clear_url_caches()
        override = override_settings(
            ROOT_URLCONF=_URLCONF_NAME,
            ALLOWED_HOSTS=["*"],
            MIDDLEWARE=list(middleware),
        )
        override.enable()
        cleanups.append(override.disable)
        return patterns

    cleanups = []
    yield mount
    for cleanup in cleanups:
        cleanup()
    sys.modules.pop(_URLCONF_NAME, None)
    clear_url_caches()


def _event_url(comp_cls, name):
    return f"/citry/ext/events/e/{comp_cls.class_id}/{name}"


def _post_envelope(client, url, call, **kwargs):
    component_class_id, handler_name = url.rsplit("/", 2)[-2:]
    call = {
        "componentClassId": component_class_id,
        "handlerName": handler_name,
        "args": {},
        **call,
    }
    envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": [call]}
    headers = {**RUNTIME_HEADERS, **kwargs.pop("headers", {})}
    # The vendor media type is what marks the body as an envelope (design
    # 6.2); plain application/json on the per-event route is the flat shape.
    return client.post(
        url,
        data=json.dumps(envelope),
        content_type="application/citry-events+json",
        headers=headers,
        **kwargs,
    )


class TestDjangoParity:
    def test_urlpatterns_carry_the_events_routes(self, mounted):
        c = _citry()
        patterns = mounted(c)
        names = [p.name for p in patterns]
        assert "citry_events_call" in names
        assert "citry_events_runtime" in names
        assert "citry_events_dispatch" in names
        # The per-event route resolves through the parametrized pattern.
        by_name = {p.name: p for p in patterns}
        match = by_name["citry_events_dispatch"].resolve("ext/events/e/Doc_a1b2c3/save")
        assert match is not None
        assert match.kwargs == {"class_id": "Doc_a1b2c3", "event": "save"}

    def test_full_pipeline_through_the_django_client(self, mounted):
        c = _citry()
        greeter = _greeter(c)
        mounted(c)
        client = Client()
        response = _post_envelope(
            client,
            _event_url(greeter, "save"),
            {"callerRenderId": "i1", "args": {"text": "Hello"}, "stateToken": _token(greeter), "sendSequence": 3},
        )
        assert response.status_code == 200
        [item] = response.json()["results"]
        assert item["ok"] is True
        assert item["sendSequence"] == 3
        assert ">Hello</p>" in item["actions"][0]["html"]

    def test_error_status_mirrors_and_get_is_no_store(self, mounted):
        c = _citry()
        greeter = _greeter(c)
        mounted(c)
        client = Client()

        response = _post_envelope(client, _event_url(greeter, "nope"), {"args": {}})
        assert response.status_code == 404
        assert response.json()["results"][0]["error"]["code"] == "unknown_event"

        response = client.get(_event_url(greeter, "echo"), {"text": "hi"})
        assert response.status_code == 200
        assert response["Cache-Control"] == "no-store"
        assert response.json()["results"][0]["actions"][0]["value"] == {"echo": "hi"}

    def test_compat_form_post_round_trip(self, mounted):
        c = _citry()
        greeter = _greeter(c)
        mounted(c)
        client = Client()
        # What a plain <form method="post"> sends (Django's test client
        # would otherwise default to multipart, which is a v1.x codec).
        fields = {"text": "No JS", "_citry_state_token": _token(greeter), "_citry_caller_render_id": "i1"}
        response = client.post(
            _event_url(greeter, "save"),
            data=urlencode(fields),
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/html")
        assert ">No JS</p>" in response.content.decode()

    def test_view_events_compat_post_can_return_an_unaddressed_component(self, mounted):
        c = _citry()

        class Result(Component):
            citry = c

            class Kwargs:
                text: str

            template = """
                <p>{{ text }}</p>
            """

        class FormIn:
            text: str

        class Form(Component):
            citry = c

            class Events(ViewEvents):
                def post(self, data: FormIn):
                    return Result(text=data.text)

            template = """
                <form></form>
            """

        mounted(c)
        response = Client().post(
            f"/citry/ext/events/e/{Form.class_id}",
            data=urlencode({"text": "Rendered by the view port"}),
            content_type="application/x-www-form-urlencoded",
        )

        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/html")
        assert ">Rendered by the view port</p>" in response.content.decode()

    def test_runtime_js_is_served(self, mounted):
        c = _citry()
        mounted(c)
        client = Client()
        response = client.get("/citry/ext/events/runtime.js")
        assert response.status_code == 200
        assert b"placeholder" in response.content

    def test_async_event_handler_answers_the_pointed_500(self, mounted, caplog):
        # The route table (with the ASGI-only async twins riding along)
        # mounts fine under Django, and the sync host runs the sync
        # dispatcher: an `async def` event handler is never run on a private
        # loop, it answers the 500 naming dispatch_async and the fix (the
        # exception text rides the wire in debug mode only, design 3.7).
        c = _citry()

        class Slow(Component):
            citry = c

            class Events:
                async def fetch(self):
                    return {"n": 1}

            template = """
                <div>s</div>
            """

        mounted(c)
        client = Client()
        with caplog.at_level(logging.DEBUG, logger="citry"):
            response = _post_envelope(client, _event_url(Slow, "fetch"), {"args": {}})
        assert response.status_code == 500
        error = response.json()["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "dispatch_async" in error["message"]


class TestDjangoCsrfIntegration:
    """The host-token layer: Django's middleware, untouched, no csrf_exempt."""

    MIDDLEWARE = ("django.middleware.csrf.CsrfViewMiddleware",)

    def test_no_view_is_csrf_exempt(self, mounted):
        c = _citry()
        patterns = mounted(c)
        for pattern in patterns:
            assert not getattr(pattern.callback, "csrf_exempt", False), pattern.name

    def test_post_without_the_host_token_is_rejected_by_django(self, mounted):
        c = _citry()
        greeter = _greeter(c)
        mounted(c, middleware=self.MIDDLEWARE)
        client = Client(enforce_csrf_checks=True)
        response = _post_envelope(client, _event_url(greeter, "quiet"), {"args": {}, "stateToken": _token(greeter)})
        # Django's middleware answered; the dispatcher never ran (a result
        # envelope would be JSON with a csrf_failed code).
        assert response.status_code == 403
        assert not response["Content-Type"].startswith("application/json")

    def test_post_with_the_host_token_passes_without_csrf_exempt(self, mounted):
        c = _citry()
        greeter = _greeter(c)
        mounted(c, middleware=self.MIDDLEWARE)
        client = Client(enforce_csrf_checks=True)
        client.cookies["csrftoken"] = CSRF_SECRET
        response = _post_envelope(
            client,
            _event_url(greeter, "quiet"),
            {"args": {}, "stateToken": _token(greeter)},
            headers={"X-CSRFToken": CSRF_SECRET},
        )
        assert response.status_code == 200
        assert response.json()["results"][0]["ok"] is True

    def test_get_handlers_are_exempt_from_the_token_layer(self, mounted):
        c = _citry()
        greeter = _greeter(c)
        mounted(c, middleware=self.MIDDLEWARE)
        client = Client(enforce_csrf_checks=True)
        # No cookie, no header: GET carries no token duty.
        response = client.get(_event_url(greeter, "echo"), {"text": "hi"})
        assert response.status_code == 200

    def test_csrf_false_still_requires_the_host_token(self, mounted):
        # The policy governs only the citry-side check: Django's middleware
        # runs before the view ever resolves the handler, and no view is
        # csrf_exempt, so csrf=False cannot drop the host token. Design 3.5
        # says exactly this: False drops only citry's own token layer, and
        # the host framework's token check is governed by the host.
        c = _citry()

        class Open(Component):
            citry = c
            template = "<div>o</div>"

            class Events:
                @event(csrf=False)
                def go(self):
                    return None

        mounted(c, middleware=self.MIDDLEWARE)
        client = Client(enforce_csrf_checks=True)

        # Without Django's token: Django's middleware answers; the
        # dispatcher never runs (an envelope answer would be JSON).
        response = _post_envelope(client, _event_url(Open, "go"), {"args": {}})
        assert response.status_code == 403
        assert not response["Content-Type"].startswith("application/json")

        # With the token, csrf=False adds no citry-side check on top.
        client.cookies["csrftoken"] = CSRF_SECRET
        response = _post_envelope(
            client,
            _event_url(Open, "go"),
            {"args": {}},
            headers={"X-CSRFToken": CSRF_SECRET},
        )
        assert response.status_code == 200
        assert response.json()["results"][0]["ok"] is True
