"""
Tests for the Events request limits: the body size and the number of form fields.

Each host adapter (ASGI, WSGI, Django) must stop reading a body just past
``_max_body_bytes``, whatever ``Content-Length`` claims and also when the body
arrives in chunks without one, so an oversized request is never held in
memory whole. The tests count the bytes each adapter pulls from the client,
on every route that dispatches an event.
"""

# ruff: noqa: ANN

import asyncio
import io
import json
import types

import pytest

from citry import Citry, Component
from citry.contrib.asgi import _read_body, asgi_app
from citry.contrib.wsgi import wsgi_app
from citry.ext.events import ViewEvents
from citry.ext.i18n.routes import _MAX_REQUEST_BYTES, i18n_routes
from citry.util.routing import URLRoute, body_read_limit, flatten_routes

_SECRET = "s" * 40
_CAP = 256
_CALL_PATH = "/ext/events/call"


def _engine(**events_defaults):
    """An engine with a small body cap and one component whose handler a request can target."""
    engine = Citry(secret=_SECRET, extensions_defaults={"events": {"_max_body_bytes": _CAP, **events_defaults}})
    engine.set_mounted_prefix("/citry")

    class Target(Component):
        citry = engine
        template = """
<p>t</p>
"""

        class Events:
            def save(self):
                return None

    class Page(Component):
        citry = engine
        template = """
<p>v</p>
"""

        # A verb-shaped component, served on the view-event route.
        class Events(ViewEvents):
            def post(self):
                return None

    engine.target = Target
    engine.view_target = Page
    return engine


def _paths(engine):
    """Every route that dispatches an event, which must all stop reading past the cap."""
    return {
        "batch": _CALL_PATH,
        "per-event": f"/ext/events/e/{engine.target.class_id}/save",
        "view-event": f"/ext/events/e/{engine.view_target.class_id}",
    }


def _rejected_as_too_large(status, body):
    """
    Return whether a response rejects the request with ``payload_too_large``.

    The batch route answers HTTP 200 with the error in the result envelope,
    as the Events protocol specifies; the other routes answer 413.
    """
    if status == 413:
        return True
    if status != 200:
        return False
    results = json.loads(body).get("results") or []
    return bool(results) and results[0].get("error", {}).get("code") == "payload_too_large"


class _CountingStream(io.RawIOBase):
    """A request body stream that records how many bytes the server read from it."""

    def __init__(self, size):
        self.remaining = size
        self.read_bytes = 0

    def readable(self):
        return True

    def read(self, size=-1):
        if size is None or size < 0:
            size = self.remaining
        chunk = b"x" * min(size, self.remaining)
        self.remaining -= len(chunk)
        self.read_bytes += len(chunk)
        return chunk


def test_every_event_route_has_the_body_cap():
    engine = _engine()
    limited = {route.name: body_read_limit(route) for _path, route in flatten_routes(engine.urls)}
    for name in ("citry_events_call", "citry_events_dispatch", "citry_events_view_dispatch"):
        assert limited[name] == _CAP + 1


class TestAsgi:
    def _send(self, engine, chunks, *, path=_CALL_PATH, headers=()):
        """Send ``chunks`` as one body; return the status, body, and how much was pulled from the client."""
        pulled = {"bytes": 0, "messages": 0}
        pending = list(chunks)

        async def receive():
            if not pending:
                return {"type": "http.disconnect"}
            chunk = pending.pop(0)
            pulled["bytes"] += len(chunk)
            pulled["messages"] += 1
            return {"type": "http.request", "body": chunk, "more_body": bool(pending)}

        sent = []

        async def send(message):
            sent.append(message)

        scope = {
            "type": "http",
            "method": "POST",
            "path": path,
            "root_path": "",
            "query_string": b"",
            "headers": [(b"content-type", b"application/citry-events+json"), *headers],
        }
        asyncio.run(asgi_app(engine)(scope, receive, send))
        status = sent[0]["status"]
        body = b"".join(message.get("body", b"") for message in sent[1:])
        return status, body, pulled

    @pytest.mark.parametrize("route", ["batch", "per-event", "view-event"])
    def test_a_chunked_body_over_the_cap_stops_being_read(self, route):
        engine = _engine()
        # 100 chunks of 100 bytes, far past the cap, with no Content-Length.
        status, body, pulled = self._send(engine, [b"x" * 100] * 100, path=_paths(engine)[route])
        assert _rejected_as_too_large(status, body)
        # Reading stopped in the message that reached cap + 1 bytes.
        assert pulled["messages"] == 3

    def test_a_content_length_does_not_change_where_reading_stops(self):
        status, body, pulled = self._send(_engine(), [b"x" * 100] * 100, headers=[(b"content-length", b"100")])
        assert _rejected_as_too_large(status, body)
        assert pulled["messages"] == 3

    @pytest.mark.parametrize(("size", "rejected"), [(_CAP, False), (_CAP + 1, True)])
    def test_the_cap_is_the_largest_body_accepted(self, size, rejected):
        status, body, pulled = self._send(_engine(), [b"x" * (size // 2), b"x" * (size - size // 2)])
        assert _rejected_as_too_large(status, body) is rejected
        assert pulled["bytes"] == size


@pytest.mark.parametrize(
    ("chunks", "pulled"),
    [
        # Reaching the limit exactly stops reading, even with more to come.
        ([b"x" * 10, b"x" * 10, b"x" * 10], 2),
        # A message that crosses the limit is cut to it.
        ([b"x" * 15, b"x" * 15], 2),
    ],
)
def test_the_asgi_reader_returns_exactly_the_limit(chunks, pulled):
    pending = list(chunks)
    received = []

    async def receive():
        chunk = pending.pop(0)
        received.append(chunk)
        return {"type": "http.request", "body": chunk, "more_body": bool(pending)}

    assert asyncio.run(_read_body(receive, 20)) == b"x" * 20
    assert len(received) == pulled


class TestWsgi:
    def _send(self, engine, stream, environ_extra, *, path=_CALL_PATH):
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": path,
            "SCRIPT_NAME": "",
            "CONTENT_TYPE": "application/citry-events+json",
            "wsgi.input": stream,
            **environ_extra,
        }
        statuses = []
        body = b"".join(wsgi_app(engine)(environ, lambda status, _headers: statuses.append(status)))
        return int(statuses[0].split()[0]), body

    @pytest.mark.parametrize("route", ["batch", "per-event", "view-event"])
    def test_a_content_length_larger_than_the_cap_reads_only_cap_plus_one(self, route):
        engine = _engine()
        stream = _CountingStream(10_000_000)
        status, body = self._send(engine, stream, {"CONTENT_LENGTH": "10000000"}, path=_paths(engine)[route])
        assert _rejected_as_too_large(status, body)
        assert stream.read_bytes == _CAP + 1

    def test_a_chunked_body_without_content_length_reads_only_cap_plus_one(self):
        # The server marks the stream as ending with the body, as servers
        # that accept chunked uploads do.
        stream = _CountingStream(10_000_000)
        status, body = self._send(_engine(), stream, {"wsgi.input_terminated": True})
        assert _rejected_as_too_large(status, body)
        assert stream.read_bytes == _CAP + 1

    @pytest.mark.parametrize(("size", "rejected"), [(_CAP, False), (_CAP + 1, True)])
    def test_the_cap_is_the_largest_body_accepted(self, size, rejected):
        stream = _CountingStream(size)
        status, body = self._send(_engine(), stream, {"CONTENT_LENGTH": str(size)})
        assert _rejected_as_too_large(status, body) is rejected

    def test_a_content_length_smaller_than_the_body_is_respected(self):
        stream = _CountingStream(10_000)
        self._send(_engine(), stream, {"CONTENT_LENGTH": "10"})
        assert stream.read_bytes == 10


class TestDjango:
    @pytest.fixture
    def handler(self):
        """Yield a Django WSGI handler whose URL configuration includes Citry's routes, and its engine."""
        django = pytest.importorskip("django")
        from django.conf import settings

        # Settings are process-wide; configure them only when no other test
        # did, and change everything this test needs through override_settings.
        if not settings.configured:
            settings.configure(ALLOWED_HOSTS=["*"])
            django.setup()
        from django.core.handlers.wsgi import WSGIHandler
        from django.test.utils import override_settings
        from django.urls import clear_url_caches, include, path

        from citry.contrib.django import urlpatterns

        engine = _engine()
        urlconf = types.ModuleType("citry_body_limits_urlconf")
        urlconf.urlpatterns = [path("citry/", include(urlpatterns(engine, prefix="/citry")))]
        with override_settings(ROOT_URLCONF=urlconf, ALLOWED_HOSTS=["*"], MIDDLEWARE=[], DEBUG=False):
            yield WSGIHandler(), engine
        clear_url_caches()

    def _environ(self, stream, length, path=_CALL_PATH):
        # Django reads no body without a Content-Length, so a chunked body
        # cannot reach it over WSGI; the header is the case that matters.
        return {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": f"/citry{path}",
            "SCRIPT_NAME": "",
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "wsgi.url_scheme": "http",
            "CONTENT_TYPE": "application/citry-events+json",
            "CONTENT_LENGTH": str(length),
            "wsgi.input": stream,
            "wsgi.errors": io.StringIO(),
        }

    @pytest.mark.parametrize("route", ["batch", "per-event", "view-event"])
    def test_a_body_over_the_cap_reads_only_cap_plus_one(self, handler, route):
        wsgi, engine = handler
        stream = _CountingStream(10_000_000)
        statuses = []
        body = b"".join(
            wsgi(self._environ(stream, 10_000_000, _paths(engine)[route]), lambda s, _h: statuses.append(s))
        )
        assert _rejected_as_too_large(int(statuses[0].split()[0]), body)
        # request.body would read up to Django's own limit; Citry reads only
        # cap + 1 bytes.
        assert stream.read_bytes == _CAP + 1

    def test_a_guard_or_codec_can_still_read_the_django_body(self, handler):
        from django.core.handlers.wsgi import WSGIRequest

        from citry.contrib.django import _build_request

        request = WSGIRequest(self._environ(io.BytesIO(b'{"a": 1}'), 8))
        assert _build_request(request, _CAP + 1).body == b'{"a": 1}'
        # Code that reads the host request after Citry gets the same bytes.
        assert request.body == b'{"a": 1}'

    def test_a_stream_reader_gets_the_bytes_after_citry_read_them(self, handler):
        from django.core.handlers.wsgi import WSGIRequest

        from citry.contrib.django import _build_request

        request = WSGIRequest(self._environ(io.BytesIO(b'{"a": 1}'), 8))
        _build_request(request, _CAP + 1)
        assert request.read() == b'{"a": 1}'

    def test_a_body_middleware_already_read_is_taken_from_memory(self, handler):
        from django.core.handlers.wsgi import WSGIRequest

        from citry.contrib.django import _build_request

        request = WSGIRequest(self._environ(io.BytesIO(b"y" * 600), 600))
        assert len(request.body) == 600
        # Citry sees at most cap + 1 bytes; the host request keeps them all.
        assert _build_request(request, _CAP + 1).body == b"y" * (_CAP + 1)
        assert len(request.body) == 600

    def test_an_upload_middleware_parsed_first_is_still_rejected(self, handler):
        from django.core.handlers.wsgi import WSGIRequest

        from citry.contrib.django import _build_request

        boundary = "b0undary"
        payload = (
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="f"; filename="a.bin"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
            + b"z" * 5000
            + f"\r\n--{boundary}--\r\n".encode()
        )
        environ = self._environ(io.BytesIO(payload), len(payload))
        environ["CONTENT_TYPE"] = f"multipart/form-data; boundary={boundary}"
        request = WSGIRequest(environ)
        # What CsrfViewMiddleware does on a POST: parse the whole stream.
        assert request.FILES["f"].size == 5000
        # The declared size is over the cap, so the route gets a body one
        # byte past it and rejects the request.
        assert len(_build_request(request, _CAP + 1).body) == _CAP + 1


class TestFormFields:
    def _post_form(self, engine, fields):
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": _paths(engine)["per-event"],
            "SCRIPT_NAME": "",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
        }
        body = "&".join(f"f{index}=v" for index in range(fields)).encode()
        environ["CONTENT_LENGTH"] = str(len(body))
        environ["wsgi.input"] = io.BytesIO(body)
        statuses = []
        response = b"".join(wsgi_app(engine)(environ, lambda status, _headers: statuses.append(status)))
        return int(statuses[0].split()[0]), response

    def test_a_form_with_more_fields_than_the_cap_is_rejected(self):
        # A form post without the browser runtime gets the plain-text answer
        # of the per-event route.
        status, body = self._post_form(_engine(_max_body_bytes=1_000_000, _max_form_fields=10), 11)
        assert status == 413
        assert b"more than 10 fields" in body

    def test_a_form_at_the_cap_gets_past_the_limit(self):
        status, _body = self._post_form(_engine(_max_body_bytes=1_000_000, _max_form_fields=10), 10)
        assert status != 413

    def test_the_default_cap_is_one_thousand_fields(self):
        engine = _engine(_max_body_bytes=1_000_000)
        assert self._post_form(engine, 1001)[0] == 413
        assert self._post_form(engine, 1000)[0] != 413


@pytest.mark.parametrize("name", ["_max_body_bytes", "_max_form_fields"])
@pytest.mark.parametrize("value", [0, -1, True, 1.5, "big", None])
def test_a_limit_that_is_not_a_positive_int_is_rejected_at_construction(name, value):
    with pytest.raises(ValueError, match=f"'{name}' must be a positive int"):
        Citry(secret=_SECRET, extensions_defaults={"events": {name: value}})


def test_a_component_cannot_set_the_form_field_limit():
    engine = Citry(secret=_SECRET)
    with pytest.raises(ValueError, match="'_max_form_fields' is engine-wide configuration"):

        class Target(Component):
            citry = engine
            template = """
<p>t</p>
"""

            class Events:
                _max_form_fields = 5


def test_a_route_limit_must_be_a_function():
    with pytest.raises(TypeError, match="must be a function"):
        URLRoute("x", handler=lambda _request: None, max_body_bytes=64)


@pytest.mark.parametrize(("value", "error"), [(-1, ValueError), ("64", TypeError), (True, TypeError)])
def test_a_route_limit_that_returns_a_bad_value_fails(value, error):
    route = URLRoute("x", handler=lambda _request: None, max_body_bytes=lambda: value)
    with pytest.raises(error, match="must return"):
        body_read_limit(route)


def test_the_i18n_messages_route_has_a_body_cap():
    routes = {route.name: route for route in i18n_routes(Citry(secret=_SECRET))}
    assert body_read_limit(routes["citry_i18n_messages"]) == _MAX_REQUEST_BYTES + 1
