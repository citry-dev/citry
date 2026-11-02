"""
A locale switch in the browser passes Django's CSRF check.

A locale switch posts to ``/citry/ext/i18n/messages`` when the page does not
already hold the new locale's messages. Django's ``CsrfViewMiddleware``
checks that POST like any other view, so the request must carry the page's
CSRF token. These tests serve a real Django project with the middleware on
and switch the locale in a real browser.
"""

from __future__ import annotations

import sys
import threading
import types
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

pytest.importorskip("pytest_playwright")
django = pytest.importorskip("django", reason="the Django locale-switch tests need django")

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(ALLOWED_HOSTS=["*"])
    django.setup()

from django.core.handlers.wsgi import WSGIHandler  # noqa: E402
from django.http import HttpResponse  # noqa: E402
from django.middleware.csrf import get_token  # noqa: E402
from django.test.utils import override_settings  # noqa: E402
from django.urls import clear_url_caches, include, path  # noqa: E402

from citry import Citry, Component  # noqa: E402
from citry.contrib.django import urlpatterns  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

pytestmark = pytest.mark.e2e

_URLCONF_NAME = "citry_i18n_django_csrf_e2e_urlconf"


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietWSGIHandler(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


def _write_catalog(root: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Write a two-locale catalog package and return its import name."""
    name = "i18n_django_csrf_e2e_catalog"
    package = root / name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "i18n-django-csrf-e2e"\nsource_locale = "en-US"\n', encoding="utf8"
    )
    for locale, label in (("en-US", "Save"), ("cs-CZ", "Uložit")):
        locale_root = package / "locales" / locale
        locale_root.mkdir(parents=True)
        (locale_root / "common.ftl").write_text(f"save = {label}\n", encoding="utf8")
    monkeypatch.syspath_prepend(str(root))
    sys.modules.pop(name, None)
    return name


def _switching_page(engine: Citry) -> type[Component]:
    class Page(Component):
        citry = engine

        class Kwargs:
            csrf_token: str = ""

        def template_data(self, kwargs, slots):
            return {"csrf_token": kwargs.csrf_token}

        # The hidden input is how a page whose CSRF cookie JavaScript cannot
        # read hands the token to the browser (docs: Security, Use Django's token).
        template = """
          <c-i18n c-client="True" tag="main">
            <input
              type="hidden"
              name="csrfmiddlewaretoken"
              c-value="csrf_token"
            >
            <p id="label" $c-tr:save>{{ tr("save") }}</p>
            <button id="switch" @click="$i18n.switchLocale('cs-CZ')">switch</button>
          </c-i18n>
        """

    return Page


@pytest.fixture
def serve_django() -> Iterator[Callable[..., str]]:
    """Serve one Citry engine and one page view through a real Django WSGI handler."""
    servers: list[Any] = []
    overrides: list[Any] = []

    def factory(engine: Citry, page: Callable[[Any], str], **django_settings: Any) -> str:
        def view(request: Any) -> HttpResponse:
            return HttpResponse(page(request))

        module = types.ModuleType(_URLCONF_NAME)
        module.urlpatterns = [  # type: ignore[attr-defined]
            path("", view),
            path("citry/", include(urlpatterns(engine, prefix="/citry"))),
        ]
        sys.modules[_URLCONF_NAME] = module
        clear_url_caches()
        override = override_settings(
            ROOT_URLCONF=_URLCONF_NAME,
            MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
            **django_settings,
        )
        override.enable()
        overrides.append(override)
        server = make_server(
            "127.0.0.1", 0, WSGIHandler(), server_class=_ThreadingWSGIServer, handler_class=_QuietWSGIHandler
        )
        servers.append(server)
        threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
        return f"http://127.0.0.1:{server.server_address[1]}"

    yield factory
    for server in servers:
        server.shutdown()
    for override in reversed(overrides):
        override.disable()
    sys.modules.pop(_URLCONF_NAME, None)
    clear_url_caches()


def _engine(catalog: str) -> Citry:
    return Citry(
        secret="i18n-django-csrf-e2e-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
        # Development mode reads the catalog's .ftl files directly; production
        # needs a compiled catalog the test has no reason to build.
        mode="development",
        extensions_defaults={
            "i18n": {"source_locale": "en-US", "locales": ("en-US", "cs-CZ"), "catalogs": (catalog,)},
        },
    )


def _record_message_posts(page: Any) -> list[dict[str, Any]]:
    posts: list[dict[str, Any]] = []

    def on_response(response: Any) -> None:
        if response.url.endswith("/citry/ext/i18n/messages"):
            posts.append({"status": response.status, "headers": response.request.headers})

    page.on("response", on_response)
    return posts


def test_locale_switch_on_django_sends_the_cookie_token(
    page: Any, serve_django: Any, open_citry_page: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The default Django setup: the CSRF cookie is readable, and the page view
    # asks Django for a token so the cookie is set, as `{% csrf_token %}` or
    # `ensure_csrf_cookie` would.
    engine = _engine(_write_catalog(tmp_path, monkeypatch))
    page_cls = _switching_page(engine)

    def render(request: Any) -> str:
        get_token(request)
        return page_cls().render().serialize()

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    posts = _record_message_posts(page)
    open_citry_page(serve_django(engine, render) + "/")
    page.wait_for_function("document.querySelector('#label')?.textContent === 'Save'")
    cookie = next(item["value"] for item in page.context.cookies() if item["name"] == "csrftoken")

    page.locator("#switch").click()
    page.wait_for_function("document.querySelector('#label')?.textContent === 'Uložit'")

    assert [post["status"] for post in posts] == [200]
    assert posts[0]["headers"]["x-csrftoken"] == cookie
    assert posts[0]["headers"]["content-type"] == "application/json"
    assert faults == []


def test_locale_switch_on_django_uses_the_token_from_citry_configure(
    page: Any, serve_django: Any, open_citry_page: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # With CSRF_COOKIE_HTTPONLY the browser cannot read the cookie, so the page
    # renders Django's token into a hidden input and points Citry.configure at it.
    engine = _engine(_write_catalog(tmp_path, monkeypatch))
    page_cls = _switching_page(engine)

    def render(request: Any) -> str:
        return page_cls(csrf_token=get_token(request)).render().serialize()

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    posts = _record_message_posts(page)
    open_citry_page(serve_django(engine, render, CSRF_COOKIE_HTTPONLY=True) + "/")
    page.wait_for_function("document.querySelector('#label')?.textContent === 'Save'")
    assert page.evaluate("document.cookie") == ""

    page.evaluate(
        """() => Citry.configure({
          csrf: {token: () => document.querySelector('[name="csrfmiddlewaretoken"]').value},
        })"""
    )
    page.locator("#switch").click()
    page.wait_for_function("document.querySelector('#label')?.textContent === 'Uložit'")

    assert [post["status"] for post in posts] == [200]
    assert posts[0]["headers"]["x-csrftoken"] == page.locator("[name=csrfmiddlewaretoken]").input_value()
    assert faults == []


def test_locale_switch_on_django_without_a_token_stays_on_the_old_locale(
    page: Any, serve_django: Any, open_citry_page: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Django's middleware still decides: with no token anywhere on the page, the
    # message request is refused and the provider keeps its language.
    engine = _engine(_write_catalog(tmp_path, monkeypatch))
    page_cls = _switching_page(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    posts = _record_message_posts(page)
    open_citry_page(serve_django(engine, lambda _request: page_cls().render().serialize()) + "/")
    page.wait_for_function("document.querySelector('#label')?.textContent === 'Save'")

    # The runtime reports the refused load as a page error once it has handled
    # the response, so waiting for that error means the switch has settled.
    with page.expect_event("pageerror"):
        page.locator("#switch").click()

    assert [post["status"] for post in posts] == [403]
    assert "x-csrftoken" not in posts[0]["headers"]
    assert page.locator("#label").text_content() == "Save"
    assert faults == ["[Citry] i18n: the cs-CZ message request failed with 403."]
