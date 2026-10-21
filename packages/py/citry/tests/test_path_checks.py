"""
Tests for asking the host app whether it serves a link path (``citry/_path_checks.py``).

The first part tests ``check_paths()`` with hand-written checkers. The rest
builds a small real Flask, Starlette/FastAPI and Django app, and checks that
each integration's path checker agrees with the framework's own test client
on which paths the app serves.
"""

import json
import os
import subprocess
import sys
import time
import types
from dataclasses import dataclass

import pytest

from citry import Citry
from citry._path_checks import PathLookup, check_paths, has_path_checkers, register_path_checker


@dataclass(frozen=True)
class Case:
    """One link path, whether the host app serves it, and the suggestion for it when it does not."""

    path: str
    found: bool
    suggestion: str | None = None


try:
    from django.middleware.common import CommonMiddleware
except ImportError:  # pragma: no cover - the Django tests skip without django
    CommonMiddleware = object


class SlashAddingMiddleware(CommonMiddleware):
    """A project's own CommonMiddleware subclass, which redirects to the trailing slash the same way."""


def _served(status: int) -> bool:
    # A 405 means the path exists for another method, such as a POST-only
    # form target, so a link or form action to it is not a typo.
    return status < 400 or status == 405


def _mismatches(engine, cases, status_of):
    """Return each case where the checker's verdict, the client's answer and the expected answer disagree."""
    results = check_paths(engine, [case.path for case in cases])
    assert results.failures == ()
    mismatches = []
    for case in cases:
        verdict = results.verdicts[case.path]
        served = _served(status_of(case.path))
        if (verdict.found, served, verdict.suggestion) != (case.found, case.found, case.suggestion):
            mismatches.append((case.path, {"checker": verdict, "client_serves": served, "expected": case}))
    return mismatches


def _static_files(root):
    """Write a static folder with one file, a sub-folder, and a file outside it that ".." would reach."""
    static = root / "static"
    (static / "img").mkdir(parents=True)
    (static / "avatar.svg").write_text("<svg/>")
    (static / "img" / "logo.svg").write_text("<svg/>")
    (root / "secret.txt").write_text("not public")
    return static


class TestCheckPaths:
    def test_paths_under_the_mounted_prefix_are_found_without_asking(self):
        engine = Citry()
        engine.set_mounted_prefix("/citry")
        asked = []

        def checker(path):
            asked.append(path)
            return PathLookup(found=False)

        register_path_checker(engine, checker)
        results = check_paths(engine, ["/citry", "/citry/citry.js", "/citryx"])
        assert results.verdicts["/citry"].found
        assert results.verdicts["/citry/citry.js"].found
        # A path that only starts with the same letters is the host's.
        assert not results.verdicts["/citryx"].found
        assert asked == ["/citryx"]

    def test_a_path_is_found_when_any_checker_finds_it(self):
        engine = Citry()
        register_path_checker(engine, lambda _path: PathLookup(found=False, nearby=("/about",)))
        register_path_checker(engine, lambda path: PathLookup(found=path == "/abuot"))
        results = check_paths(engine, ["/abuot", "/missing"])
        assert results.verdicts["/abuot"].found
        assert results.verdicts["/abuot"].suggestion is None
        assert not results.verdicts["/missing"].found
        assert has_path_checkers(engine)

    def test_a_raising_checker_leaves_the_path_without_a_verdict(self):
        engine = Citry()

        def broken(path):
            raise RuntimeError("routing table not loaded")

        register_path_checker(engine, broken)
        register_path_checker(engine, lambda path: PathLookup(found=path == "/about"))
        results = check_paths(engine, ["/contact", "/about"])
        # The broken checker may serve /contact, so it is not reported.
        assert "/contact" not in results.verdicts
        assert results.failures == (("/contact", "RuntimeError: routing table not loaded"),)
        # Another checker that finds the path settles it despite the failure.
        assert results.verdicts["/about"].found

    def test_the_suggestion_is_a_served_path_one_slip_away(self):
        engine = Citry()
        register_path_checker(engine, lambda _path: PathLookup(found=False, nearby=("/contact", "/about")))
        results = check_paths(engine, ["/abuot", "/elsewhere"])
        assert results.verdicts["/abuot"].suggestion == "/about"
        # No served path is one slip from this one.
        assert results.verdicts["/elsewhere"].suggestion is None

    def test_results_do_not_depend_on_the_order_paths_or_suggestions_arrive_in(self):
        def run(paths, nearby):
            engine = Citry()
            register_path_checker(engine, lambda _path: PathLookup(found=False, nearby=nearby))
            return check_paths(engine, paths)

        # The paths and the served paths arrive in a different order in each
        # run; the verdicts and the suggestions picked must not change.
        first = run(["/abb", "/x", "/abuot"], ("/ab", "/about", "/abot"))
        second = run(["/abuot", "/abb", "/x"], ("/abot", "/about", "/ab"))
        assert first == second
        assert first.verdicts["/abuot"].suggestion == "/about"
        assert first.verdicts["/abb"].suggestion == "/ab"


class TestFlaskPathChecker:
    @pytest.fixture
    def app(self, tmp_path):
        flask = pytest.importorskip("flask", reason="the Flask path checker tests need flask")
        _static_files(tmp_path)
        brand_static = tmp_path / "brand"
        brand_static.mkdir()
        (brand_static / "logo.svg").write_text("<svg/>")

        app = flask.Flask("path_checks_flask_app", root_path=str(tmp_path))
        app.add_url_rule("/about", "about", lambda: "about")
        app.add_url_rule("/projects/<int:project_id>", "project", lambda project_id: str(project_id))
        app.add_url_rule("/subscribe", "subscribe", lambda: "ok", methods=["POST"])
        app.add_url_rule("/docs/", "docs", lambda: "docs")
        blueprint = flask.Blueprint(
            "brand", __name__, static_folder=str(brand_static), static_url_path="/brand-static"
        )
        app.register_blueprint(blueprint)
        return app

    def test_the_checker_agrees_with_the_test_client(self, app):
        from citry.contrib.flask import mount

        engine = Citry()
        mount(app, engine)
        # Routes added after mount() are still seen, because the checker
        # reads the URL map each time it is asked.
        app.add_url_rule("/late", "late", lambda: "late")
        client = app.test_client()
        cases = [
            Case("/about", found=True),
            Case("/abuot", found=False, suggestion="/about"),
            Case("/late", found=True),
            Case("/projects/7", found=True),
            Case("/projects/alpha", found=False),
            Case("/static/avatar.svg", found=True),
            Case("/static/avtar.svg", found=False, suggestion="/static/avatar.svg"),
            Case("/static/img/logo.svg", found=True),
            Case("/static/img/lgo.svg", found=False, suggestion="/static/img/logo.svg"),
            Case("/static/img", found=False),
            Case("/static/../secret.txt", found=False),
            Case("/brand-static/logo.svg", found=True),
            Case("/brand-static/lgo.svg", found=False, suggestion="/brand-static/logo.svg"),
            Case("/subscribe", found=True),
            Case("/docs/", found=True),
            # Werkzeug redirects to the rule's trailing slash, but not the reverse.
            Case("/docs", found=True),
            Case("/about/", found=False),
        ]
        assert _mismatches(engine, cases, lambda path: client.get(path, follow_redirects=True).status_code) == []

    def test_mount_registers_one_checker(self, app):
        from citry.contrib.flask import mount

        engine = Citry()
        mount(app, engine)
        assert len(engine._path_checkers) == 1

    def test_a_rejected_mount_registers_no_checker(self, app):
        from citry.contrib.flask import mount

        engine = Citry()
        with pytest.raises(ValueError, match="needs a prefix below the root"):
            mount(app, engine, prefix="/")
        assert engine._path_checkers == []

    def test_a_redirect_counts_only_when_its_target_is_served(self, app):
        from citry.contrib.flask import mount

        engine = Citry()
        mount(app, engine)
        app.add_url_rule("/old-about", "old_about", redirect_to="/about")
        app.add_url_rule("/old-team", "old_team", redirect_to="/team")
        client = app.test_client()
        cases = [
            Case("/old-about", found=True),
            Case("/old-team", found=False),
            # Werkzeug merges doubled slashes with a redirect.
            Case("/static//avatar.svg", found=True),
            Case("/static//missing.css", found=False),
        ]
        assert _mismatches(engine, cases, lambda path: client.get(path, follow_redirects=True).status_code) == []

    def test_a_rule_for_a_subdomain_is_found(self, tmp_path):
        flask = pytest.importorskip("flask", reason="the Flask path checker tests need flask")
        from citry.contrib.flask import mount

        app = flask.Flask(
            "path_checks_subdomain_app", root_path=str(tmp_path), static_folder=None, subdomain_matching=True
        )
        app.config["SERVER_NAME"] = "example.com"
        app.add_url_rule("/dashboard", "dashboard", lambda: "dash", subdomain="api")
        engine = Citry()
        mount(app, engine)
        check = engine._path_checkers[0][1]
        # The page holding the link may be on the api subdomain, which the
        # checker cannot know, so a rule for any subdomain serves the path.
        assert check("/dashboard").found
        assert app.test_client().get("/dashboard", base_url="http://api.example.com").status_code == 200
        assert not check("/dashbaord").found

    def test_a_null_character_in_a_static_path_is_not_found(self, app):
        from citry.contrib.flask import mount

        engine = Citry()
        mount(app, engine)
        # A decoded "%00" must give a verdict, not an error.
        assert not engine._path_checkers[0][1]("/static/img\x00/logo.svg").found

    def test_a_host_without_a_url_map_registers_no_checker(self):
        from citry.contrib.flask import mount

        class PlainWsgiHost:
            def wsgi_app(self, environ, start_response):
                start_response("200 OK", [])
                return [b""]

        engine = Citry()
        mount(PlainWsgiHost(), engine)
        assert engine.mounted_prefix == "/citry"
        assert not has_path_checkers(engine)


class TestStarlettePathChecker:
    @pytest.fixture
    def app(self, tmp_path):
        fastapi = pytest.importorskip("fastapi", reason="the Starlette path checker tests need fastapi")
        pytest.importorskip("httpx2", reason="Starlette's TestClient needs httpx2")
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.middleware.gzip import GZipMiddleware
        from starlette.responses import PlainTextResponse
        from starlette.routing import Mount, Route
        from starlette.staticfiles import StaticFiles

        static = _static_files(tmp_path)
        site = tmp_path / "site"
        site.mkdir()
        (site / "index.html").write_text("<p>home</p>")

        def text(request):
            return PlainTextResponse("ok")

        app = fastapi.FastAPI()
        app.get("/about")(lambda: "about")
        # A typed path parameter in the route itself, so Starlette's routing
        # rejects a non-number before FastAPI's validation runs.
        app.get("/projects/{project_id:int}")(lambda project_id: project_id)
        app.post("/subscribe")(lambda: "ok")
        app.get("/guides/")(lambda: "guides")
        app.mount("/static", StaticFiles(directory=static), name="static")
        app.mount("/site", StaticFiles(directory=site, html=True), name="site")
        app.mount("/company", Starlette(routes=[Route("/team", text)]))
        app.router.routes.append(Mount("/api", routes=[Route("/status", text)]))
        # Middleware wraps the StaticFiles app, which the checker must still find.
        app.router.routes.append(
            Mount("/assets", app=StaticFiles(directory=static), middleware=[Middleware(GZipMiddleware)])
        )
        return app

    def test_the_checker_agrees_with_the_test_client(self, app):
        from fastapi.testclient import TestClient

        from citry.contrib.fastapi import mount

        engine = Citry()
        mount(app, engine)
        app.get("/late")(lambda: "late")
        client = TestClient(app)
        cases = [
            Case("/about", found=True),
            Case("/abuot", found=False, suggestion="/about"),
            Case("/late", found=True),
            Case("/projects/7", found=True),
            Case("/projects/alpha", found=False),
            Case("/static/avatar.svg", found=True),
            Case("/static/avtar.svg", found=False, suggestion="/static/avatar.svg"),
            Case("/static/img/logo.svg", found=True),
            Case("/static/img/lgo.svg", found=False, suggestion="/static/img/logo.svg"),
            Case("/static/img", found=False),
            # httpx sends this as "/secret.txt", so the client half only shows
            # the browser would not reach a file; the checker gets the raw path.
            Case("/static/../secret.txt", found=False),
            Case("/assets/avatar.svg", found=True),
            Case("/assets/avtar.svg", found=False, suggestion="/assets/avatar.svg"),
            Case("/site/", found=True),
            Case("/site", found=True),
            Case("/company/team", found=True),
            Case("/company/taem", found=False, suggestion="/company/team"),
            Case("/api/status", found=True),
            Case("/api/stauts", found=False, suggestion="/api/status"),
            Case("/subscribe", found=True),
            Case("/guides/", found=True),
            # The router redirects a missing or extra trailing slash.
            Case("/guides", found=True),
            Case("/about/", found=True),
        ]
        assert _mismatches(engine, cases, lambda path: client.get(path).status_code) == []

    def test_a_host_route_is_asked_with_its_own_slash_redirect(self, app):
        from starlette.responses import PlainTextResponse
        from starlette.routing import Host, Route, Router

        from citry.contrib.fastapi import mount

        def text(request):
            return PlainTextResponse("ok")

        async def opaque(scope, receive, send):
            await PlainTextResponse("anything")(scope, receive, send)

        app.router.routes.insert(0, Host("api.example.com", Router(routes=[Route("/guide/", text)])))
        # A Host app that does not list its routes must not make every path served.
        app.router.routes.insert(0, Host("cdn.example.com", opaque))
        engine = Citry()
        mount(app, engine)
        check = engine._path_checkers[0][1]
        assert check("/guide/").found
        assert check("/guide").found
        assert not check("/giude/").found

    def test_a_path_under_an_opaque_mount_is_found(self, app):
        from citry.contrib.fastapi import mount

        engine = Citry()
        mount(app, engine)
        # Citry's own routes are an ASGI app the checker cannot look into.
        assert engine._path_checkers[0][1]("/citry/anything").found

    def test_mount_registers_one_checker(self, app):
        from citry.contrib.fastapi import mount

        engine = Citry()
        mount(app, engine)
        assert len(engine._path_checkers) == 1

    def test_a_rejected_mount_registers_no_checker(self, app):
        from citry.contrib.fastapi import mount

        engine = Citry()
        routes_before = list(app.routes)
        with pytest.raises(ValueError, match="must start with"):
            mount(app, engine, prefix="citry")
        assert engine._path_checkers == []
        assert app.routes == routes_before


class TestDjangoPathChecker:
    @pytest.fixture
    def serving(self, tmp_path):
        """Yield ``(engine, client)`` for a Django project whose URLconf includes Citry's routes."""
        django = pytest.importorskip("django", reason="the Django path checker tests need django")
        from django.conf import settings

        # Settings are process-wide; configure them only when no other test
        # did, and change everything this test needs through override_settings.
        if not settings.configured:
            settings.configure(ALLOWED_HOSTS=["*"])
            django.setup()
        from django.contrib.staticfiles import views as static_views
        from django.http import HttpResponse
        from django.test import Client
        from django.test.utils import override_settings
        from django.urls import include, path, re_path
        from django.views.decorators.http import require_POST

        from citry.contrib.django import urlpatterns

        static = _static_files(tmp_path)

        def text(request, **kwargs):
            return HttpResponse("ok")

        engine = Citry()
        urlconf = types.ModuleType("citry_path_checks_urlconf")
        urlconf.urlpatterns = [
            path("about", text),
            path("projects/<int:pk>", text),
            path("subscribe", require_POST(text)),
            path("guides/", text),
            path("blog/", include([path("archive", text), path("<slug:slug>/edit", text)])),
            re_path(r"^legacy/\d+$", text),
            # What a development server serves under STATIC_URL; it accepts any
            # name, so only the finders can say whether the file exists.
            re_path(r"^static/(?P<path>.*)$", static_views.serve, {"insecure": True}),
            path("citry/", include(urlpatterns(engine, prefix="/citry"))),
        ]
        with override_settings(
            ROOT_URLCONF=urlconf,
            ALLOWED_HOSTS=["*"],
            INSTALLED_APPS=["django.contrib.staticfiles"],
            MIDDLEWARE=["django.middleware.common.CommonMiddleware"],
            APPEND_SLASH=True,
            DEBUG=False,
            STATIC_URL="/static/",
            STATICFILES_DIRS=[str(static)],
            STATICFILES_FINDERS=["django.contrib.staticfiles.finders.FileSystemFinder"],
            MEDIA_URL="/media/",
        ):
            yield engine, Client(raise_request_exception=False)

    def test_the_checker_agrees_with_the_test_client(self, serving):
        engine, client = serving
        cases = [
            Case("/about", found=True),
            Case("/abuot", found=False, suggestion="/about"),
            Case("/projects/7", found=True),
            Case("/projects/alpha", found=False),
            Case("/blog/archive", found=True),
            Case("/blog/archvie", found=False, suggestion="/blog/archive"),
            Case("/blog/first-post/edit", found=True),
            Case("/legacy/12", found=True),
            Case("/static/avatar.svg", found=True),
            Case("/static/avtar.svg", found=False, suggestion="/static/avatar.svg"),
            Case("/static/img/logo.svg", found=True),
            Case("/static/img/lgo.svg", found=False, suggestion="/static/img/logo.svg"),
            Case("/static/img", found=False),
            Case("/static/../secret.txt", found=False),
            Case("/subscribe", found=True),
            Case("/guides/", found=True),
            # CommonMiddleware adds a missing trailing slash, never removes one.
            Case("/guides", found=True),
            Case("/about/", found=False),
        ]
        assert _mismatches(engine, cases, lambda path: client.get(path, follow=True).status_code) == []

    def test_an_unset_media_url_does_not_cover_the_site(self, serving):
        from django.test.utils import override_settings

        engine, _client = serving
        # Django reads an empty MEDIA_URL as "/", which would otherwise match
        # every path.
        with override_settings(MEDIA_URL="", STATIC_URL=None):
            assert not engine._path_checkers[0][1]("/abuot").found
            assert engine._path_checkers[0][1]("/about").found

    def test_a_language_prefixed_page_is_found_for_every_language(self, serving):
        from django.conf.urls.i18n import i18n_patterns
        from django.http import HttpResponse
        from django.test.utils import override_settings
        from django.urls import path

        engine, _client = serving
        urlconf = types.ModuleType("citry_path_checks_i18n_urlconf")
        urlconf.urlpatterns = i18n_patterns(path("pricing", lambda _request: HttpResponse("ok")))
        with override_settings(
            ROOT_URLCONF=urlconf, USE_I18N=True, LANGUAGE_CODE="en", LANGUAGES=[("en", "English"), ("de", "German")]
        ):
            check = engine._path_checkers[0][1]
            assert check("/en/pricing").found
            # Not the active language, but a link may point at the German page.
            assert check("/de/pricing").found
            assert not check("/fr/pricing").found

    def test_a_sub_path_deployment_resolves_links_below_the_sub_path(self, serving):
        from django.urls import set_script_prefix

        engine, _client = serving
        check = engine._path_checkers[0][1]
        set_script_prefix("/app/")
        try:
            assert check("/app/about").found
            # The project is not served outside its sub-path.
            assert not check("/about").found
            assert check("/app/abuot").nearby
            assert "/app/about" in check("/app/abuot").nearby
        finally:
            set_script_prefix("/")

    def test_a_common_middleware_subclass_still_adds_the_slash(self, serving):
        from django.test.utils import override_settings

        engine, _client = serving
        with override_settings(MIDDLEWARE=[f"{__name__}.SlashAddingMiddleware", "no.such.Middleware"]):
            assert engine._path_checkers[0][1]("/guides").found

    def test_a_path_under_media_url_is_found(self, serving):
        engine, _client = serving
        # Uploaded files are not listed anywhere the checker can read.
        assert engine._path_checkers[0][1]("/media/uploads/photo.png").found

    def test_without_common_middleware_a_missing_slash_is_not_found(self, serving):
        from django.test.utils import override_settings

        engine, _client = serving
        with override_settings(MIDDLEWARE=[]):
            assert not engine._path_checkers[0][1]("/guides").found

    def test_without_staticfiles_installed_static_paths_go_through_the_urlconf(self, serving):
        from django.test.utils import override_settings

        engine, _client = serving
        # The development pattern under /static/ accepts any name, and with no
        # finders to ask, the checker can only follow the URLconf.
        with override_settings(INSTALLED_APPS=[]):
            assert engine._path_checkers[0][1]("/static/avtar.svg").found

    def test_urlpatterns_registers_one_checker(self, serving):
        engine, _client = serving
        assert len(engine._path_checkers) == 1

    def test_a_rejected_urlpatterns_call_registers_no_checker(self, serving):
        from citry.contrib.django import urlpatterns

        engine = Citry()
        with pytest.raises(ValueError, match="must start with"):
            urlpatterns(engine, prefix="citry")
        assert engine._path_checkers == []


def test_the_django_checker_starts_django_like_citry_check_does(tmp_path):
    # `citry check` imports the URL configuration without calling
    # django.setup(), so the checker must load the apps itself, or static
    # files and FORCE_SCRIPT_NAME are never read. A fresh process shows that.
    pytest.importorskip("django", reason="the Django path checker tests need django")
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "site.css").write_text("", encoding="utf-8")
    (tmp_path / "proj_settings.py").write_text(
        "from pathlib import Path\n"
        "SECRET_KEY = 'x'\n"
        "ROOT_URLCONF = 'proj_urls'\n"
        "FORCE_SCRIPT_NAME = '/app'\n"
        "STATIC_URL = 'static/'\n"
        "STATICFILES_DIRS = [Path(__file__).parent / 'static']\n"
        "INSTALLED_APPS = ['django.contrib.staticfiles']\n",
        encoding="utf-8",
    )
    (tmp_path / "proj_urls.py").write_text(
        "from django.http import HttpResponse\n"
        "from django.urls import include, path\n"
        "from citry import Citry\n"
        "from citry.contrib.django import urlpatterns as citry_urlpatterns\n"
        "engine = Citry()\n"
        "urlpatterns = [\n"
        "    path('', lambda request: HttpResponse('')),\n"
        "    path('citry/', include(citry_urlpatterns(engine, prefix='/app/citry'))),\n"
        "]\n",
        encoding="utf-8",
    )
    script = (
        "import json\n"
        "from citry._path_checks import check_paths\n"
        "from proj_urls import engine\n"
        "paths = ['/app/', '/app/static/site.css', '/app/static/sit.css', '/app/nope']\n"
        "results = check_paths(engine, paths)\n"
        "print(json.dumps({path: verdict.found for path, verdict in results.verdicts.items()}))\n"
        "print(json.dumps(list(results.failures)))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "DJANGO_SETTINGS_MODULE": "proj_settings", "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        check=True,
    )
    verdicts_line, failures_line = completed.stdout.strip().splitlines()

    assert json.loads(failures_line) == []
    assert json.loads(verdicts_line) == {
        "/app/": True,
        "/app/nope": False,
        "/app/static/sit.css": False,
        "/app/static/site.css": True,
    }


def test_mounting_into_the_same_app_again_replaces_its_checker():
    from citry.contrib.fastapi import mount

    starlette = pytest.importorskip("starlette.applications", reason="needs starlette")
    engine = Citry()
    first = starlette.Starlette()
    mount(first, engine)
    mount(first, engine, prefix="/assets")
    second = starlette.Starlette()
    mount(second, engine)

    assert [host for host, _checker in engine._path_checkers] == [first, second]


def test_a_deadline_leaves_the_remaining_paths_without_a_verdict():
    engine = Citry()
    register_path_checker(engine, lambda _path: PathLookup(found=True))

    results = check_paths(engine, ["/a", "/b"], deadline=time.monotonic() - 1)

    assert results.verdicts == {}
    assert results.failures == ()
