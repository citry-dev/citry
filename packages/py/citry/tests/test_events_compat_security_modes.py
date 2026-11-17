"""
The no-JavaScript answer of an Events handler keeps the app's security checks.

When a plain form posts to a handler, or a link opens a ``GET`` handler,
Citry answers with an HTML page instead of the JSON the browser runtime
reads. These tests check that this answer applies the app's
``security_javascript="forbid"`` and ``security_csp`` as the app's own page
render does: on the WSGI, ASGI and Django adapters, for a component element,
a bare element, an already-rendered value, a standalone template and a
component that belongs to another engine.
"""

from __future__ import annotations

import sys
import types
import warnings
from collections.abc import Callable, Iterator
from typing import Any
from urllib.parse import urlencode

import pytest

django = pytest.importorskip("django", reason="the Django half of these tests needs Django")
httpx2 = pytest.importorskip("httpx2", reason="Starlette's TestClient needs httpx2")

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(ALLOWED_HOSTS=["*"])
    django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import override_settings  # noqa: E402
from django.urls import clear_url_caches, include, path  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from citry import Citry, Component  # noqa: E402
from citry.contrib.asgi import asgi_app  # noqa: E402
from citry.contrib.django import urlpatterns  # noqa: E402
from citry.contrib.wsgi import wsgi_app  # noqa: E402
from citry.ext.events import actions, event  # noqa: E402

SIGNING_KEY = "compat-security-modes-secret"
# A harmless value whose effect a browser would show; the tests only look for it in the body.
PAYLOAD = "javascript:void(document.body.dataset.compat='ran')"
HANDLER_ERROR = "The event handler raised an unexpected error."
_URLCONF_NAME = "citry_compat_security_modes_urlconf"


class _UrlIn:
    url: str = ""


def _app(**settings_kwargs: Any) -> Citry:
    c = Citry(secret=SIGNING_KEY, **settings_kwargs)
    c.set_mounted_prefix("/citry")
    return c


def _components(c: Citry) -> type[Component]:
    """Build a handler component whose handlers return the value under test in each supported shape."""

    class Out(Component):
        citry = c

        class Kwargs:
            url: str

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"url": kwargs.url}

        template = """
            <p><a c-href="url">continue</a></p>
        """

    class AuthorScript(Component):
        citry = c

        template = """
            <button onclick="document.body.dataset.compat = 'ran'">go</button>
            <script>document.body.dataset.compat = "ran";</script>
        """

    class Scripted(Component):
        citry = c

        template = """
            <p>saved</p>
        """

        js = """
            document.body.dataset.compat = "ran";
        """

    # A component that forgot its ``citry = c`` line belongs to another engine
    # with the default settings.
    other_engine = _app()

    class Foreign(Component):
        citry = other_engine

        class Kwargs:
            url: str

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"url": kwargs.url}

        template = """
            <p><a c-href="url">continue</a></p>
        """

    class Box(Component):
        citry = c

        class Events:
            def element(self, data: _UrlIn) -> Any:
                return actions.Render(Out(url=data.url))

            def bare(self, data: _UrlIn) -> Any:
                # A bare element is the shorthand for Render(element).
                return Out(url=data.url)

            def rendered(self, data: _UrlIn) -> Any:
                return actions.Render(Out(url=data.url).render())

            def template(self, data: _UrlIn) -> Any:
                return actions.Render(
                    c.render_template('<a c-href="url">continue</a>', {"url": data.url}),
                )

            def author(self) -> Any:
                return AuthorScript()

            def scripted(self) -> Any:
                return Scripted()

            def foreign(self, data: _UrlIn) -> Any:
                return Foreign(url=data.url)

            @event(methods=("GET",))
            def nav(self, data: _UrlIn) -> Any:
                return Out(url=data.url)

        template = """
            <p>box</p>
        """

    # Kept on the class so a test can render the same component as a page.
    Box.out_component = Out  # type: ignore[attr-defined]
    return Box


def _url(comp_cls: type[Component], name: str) -> str:
    return f"/citry/ext/events/e/{comp_cls.class_id}/{name}"


# What a browser sends for a plain <form method="post"> on the same site.
_FORM_HEADERS = {
    "content-type": "application/x-www-form-urlencoded",
    "origin": "http://testserver",
    "sec-fetch-site": "same-origin",
}
# What a browser sends when a link on another site opens a GET handler.
_LINK_HEADERS = {
    "accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "navigate",
}


class _Answer:
    """The parts of an HTTP answer these tests compare, from any adapter."""

    def __init__(self, status: int, content_type: str, body: str) -> None:
        self.status = status
        self.content_type = content_type
        self.body = body


Send = Callable[[str, str, dict[str, str], bytes], _Answer]


def _wsgi_sender(c: Citry) -> Send:
    inner = wsgi_app(c)

    def app(environ: dict[str, Any], start_response: Any) -> Any:
        # Mount Citry under /citry as a dispatching parent app would.
        environ = {**environ, "SCRIPT_NAME": "/citry", "PATH_INFO": environ["PATH_INFO"][len("/citry") :]}
        return inner(environ, start_response)

    client = httpx2.Client(transport=httpx2.WSGITransport(app=app), base_url="http://testserver")

    def send(method: str, url: str, headers: dict[str, str], body: bytes) -> _Answer:
        response = client.request(method, url, headers=headers, content=body)
        return _Answer(response.status_code, response.headers.get("content-type", ""), response.text)

    return send


def _asgi_sender(c: Citry) -> Send:
    inner = asgi_app(c)

    async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        await inner({**scope, "root_path": "/citry"}, receive, send)

    client = TestClient(app)

    def send(method: str, url: str, headers: dict[str, str], body: bytes) -> _Answer:
        response = client.request(method, url, headers=headers, content=body)
        return _Answer(response.status_code, response.headers.get("content-type", ""), response.text)

    return send


@pytest.fixture
def senders() -> Iterator[dict[str, Callable[[Citry], Send]]]:
    """One factory per adapter; the Django one mounts the app in a throwaway URLconf."""
    cleanups: list[Callable[[], None]] = []

    def django_sender(c: Citry) -> Send:
        module = types.ModuleType(_URLCONF_NAME)
        module.urlpatterns = [path("citry/", include(urlpatterns(c, prefix="/citry")))]  # type: ignore[attr-defined]
        sys.modules[_URLCONF_NAME] = module
        clear_url_caches()
        override = override_settings(ROOT_URLCONF=_URLCONF_NAME, ALLOWED_HOSTS=["*"], MIDDLEWARE=[])
        override.enable()
        cleanups.append(override.disable)
        client = Client(HTTP_HOST="testserver")

        def send(method: str, url: str, headers: dict[str, str], body: bytes) -> _Answer:
            extra = {k: v for k, v in headers.items() if k != "content-type"}
            if method == "POST":
                response = client.post(url, data=body, content_type=headers["content-type"], headers=extra)
            else:
                response = client.get(url, headers=extra)
            return _Answer(response.status_code, response.get("Content-Type", ""), response.content.decode())

        return send

    yield {"wsgi": _wsgi_sender, "asgi": _asgi_sender, "django": django_sender}
    for cleanup in cleanups:
        cleanup()
    sys.modules.pop(_URLCONF_NAME, None)
    clear_url_caches()


def _form_post(send: Send, box: type[Component], name: str, fields: dict[str, str]) -> _Answer:
    return send("POST", _url(box, name), _FORM_HEADERS, urlencode(fields).encode())


def _link_get(send: Send, box: type[Component], name: str, fields: dict[str, str]) -> _Answer:
    return send("GET", f"{_url(box, name)}?{urlencode(fields)}", _LINK_HEADERS, b"")


def _assert_refused(answer: _Answer) -> None:
    # The same plain-text 500 a no-JavaScript answer gives for any handler error.
    assert answer.status == 500
    assert answer.content_type.startswith("text/plain")
    assert answer.body == HANDLER_ERROR


@pytest.mark.parametrize("adapter", ["wsgi", "asgi", "django"])
class TestForbidOnEveryAdapter:
    """Each adapter and each way a browser reaches the answer without the runtime."""

    def test_a_form_post_answer_refuses_a_javascript_url(self, senders: Any, adapter: str) -> None:
        c = _app(security_javascript="forbid")
        box = _components(c)
        answer = _form_post(senders[adapter](c), box, "element", {"url": PAYLOAD})
        _assert_refused(answer)

    def test_a_get_link_answer_refuses_a_javascript_url(self, senders: Any, adapter: str) -> None:
        c = _app(security_javascript="forbid")
        box = _components(c)
        answer = _link_get(senders[adapter](c), box, "nav", {"url": PAYLOAD})
        _assert_refused(answer)

    def test_a_safe_answer_is_still_served(self, senders: Any, adapter: str) -> None:
        # forbid refuses only output that needs JavaScript, so the ordinary answer stays a page.
        c = _app(security_javascript="forbid")
        box = _components(c)
        answer = _form_post(senders[adapter](c), box, "element", {"url": "/next"})
        assert answer.status == 200
        assert answer.content_type.startswith("text/html")
        assert '<a href="/next">continue</a>' in answer.body


class TestForbidForEveryRenderedValue:
    """Every value a handler can render goes through the same check (WSGI is enough here)."""

    @pytest.mark.parametrize("handler", ["element", "bare", "rendered", "template", "foreign"])
    def test_a_javascript_url_from_data_is_refused(self, handler: str) -> None:
        c = _app(security_javascript="forbid")
        box = _components(c)
        answer = _form_post(_wsgi_sender(c), box, handler, {"url": PAYLOAD})
        _assert_refused(answer)

    def test_template_onclick_and_script_are_refused(self) -> None:
        c = _app(security_javascript="forbid")
        box = _components(c)
        answer = _form_post(_wsgi_sender(c), box, "author", {})
        _assert_refused(answer)

    def test_the_page_render_and_the_answer_agree(self) -> None:
        # The answer must not serve what the app's own page render refuses.
        c = _app(security_javascript="forbid")
        box = _components(c)
        with pytest.raises(ValueError, match="security_javascript='forbid'"):
            box.out_component(url=PAYLOAD).render().serialize()  # type: ignore[attr-defined]
        _assert_refused(_form_post(_wsgi_sender(c), box, "element", {"url": PAYLOAD}))


class TestOtherModesKeepOmit:
    """Without forbid the answer leaves out Citry's scripts and only warns."""

    @pytest.mark.parametrize("mode", ["allow", "warn", "omit"])
    def test_the_answer_is_served_with_a_warning(self, mode: str) -> None:
        c = _app(security_javascript=mode)
        box = _components(c)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            answer = _form_post(_wsgi_sender(c), box, "element", {"url": PAYLOAD})
        assert answer.status == 200
        assert answer.content_type.startswith("text/html")
        assert 'href="javascript:void(' in answer.body
        assert any("security_javascript='omit'" in str(w.message) for w in caught)

    def test_citry_scripts_stay_out_of_the_answer(self) -> None:
        # Under "allow" the component's js would be in the page; the answer has no runtime for it.
        c = _app()
        box = _components(c)
        answer = _form_post(_wsgi_sender(c), box, "scripted", {})
        assert answer.status == 200
        assert "saved</p>" in answer.body
        assert "<script" not in answer.body
        assert "dataset.compat" not in answer.body
        assert "data-citry-vue" not in answer.body


class TestCspCheckOnTheAnswer:
    def test_strict_csp_refuses_template_script_in_the_answer(self) -> None:
        # security_csp reaches this answer through the app's setting too.
        c = _app(security_csp="strict")
        box = _components(c)
        _assert_refused(_form_post(_wsgi_sender(c), box, "author", {}))
