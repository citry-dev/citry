"""Serve the shared board through Tetra's HTTP component protocol."""

# Configure Django before importing component routes and views.
# ruff: noqa: E402

import mimetypes
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

import django
from django.conf import settings

settings.configure(
    DEBUG=False,
    SECRET_KEY="project-board-local-benchmark-only",  # noqa: S106 - isolated synthetic data
    ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"],
    ROOT_URLCONF="app",
    INSTALLED_APPS=[
        "tetra",
        "django.contrib.staticfiles",
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.sessions",
        "board_app",
    ],
    MIDDLEWARE=[
        "django_host.ResponseTiming",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "tetra.middleware.TetraMiddleware",
    ],
    SESSION_ENGINE="django.contrib.sessions.backends.cache",
    USE_TZ=True,
    STATIC_URL="/static/",
    TETRA_ESBUILD_PATH=str(HERE / "generated" / "esbuild"),
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "DIRS": [str(HERE)],
        }
    ],
)
django.setup()

from django.contrib.staticfiles import finders
from django.core.asgi import get_asgi_application
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.template import Template
from django.urls import include, path
from django_host import asset_view, health
from model import reset
from render_timing import RenderTimingMiddleware, instrument
from tetra import Component


def index(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponse(status=405)
    try:
        session = request.GET.get("session", "manual")
        reset(session, int(request.GET.get("count", "14")))
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    return render(request, "page.html", {"session": session})


def static_asset(_request: HttpRequest, name: str) -> HttpResponse:
    """Serve installed and prebuilt assets without a development static server."""
    if ".." in Path(name).parts or Path(name).is_absolute():
        return HttpResponse(status=404)
    found = finders.find(name)
    if not found:
        return HttpResponse(status=404)
    return HttpResponse(
        Path(found).read_bytes(), content_type=mimetypes.guess_type(name)[0] or "application/octet-stream"
    )


urlpatterns = [
    path("", index),
    path("health", health),
    path("assets/<str:name>", asset_view(HERE / "assets", SCENARIO)),
    path("static/<path:name>", static_asset),
    path("__tetra__/", include("tetra.urls")),
]
application = get_asgi_application()


instrument(Template, "render")

instrument(Component, "render")

application = RenderTimingMiddleware(application)
