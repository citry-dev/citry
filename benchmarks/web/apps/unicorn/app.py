"""Serve the board through Django Unicorn's component protocol."""

# Django must be configured before importing framework views.
# ruff: noqa: E402
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

import django
import django_unicorn
from django.conf import settings

settings.configure(
    DEBUG=False,
    SECRET_KEY="project-board-local-benchmark-only",  # noqa: S106
    ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"],
    ROOT_URLCONF="app",
    MIDDLEWARE=[
        "django_host.ResponseTiming",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
    ],
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
    INSTALLED_APPS=["django.contrib.staticfiles", "django_unicorn"],
    STATIC_URL="/static/",
    USE_TZ=True,
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "DIRS": [str(HERE / "templates")],
        }
    ],
)
django.setup()

from django.core.asgi import get_asgi_application
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.template import Template
from django.urls import include, path
from django_host import asset_view, health
from django_unicorn.components import UnicornView
from model import reset
from render_timing import RenderTimingMiddleware, instrument


def index(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponse(status=405)
    try:
        session = request.GET.get("session", "manual")
        reset(session, int(request.GET.get("count", "14")))
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))
    request.session["board_session"] = session
    get_token(request)
    return render(request, "page.html", {"session": session})


def runtime(_request: HttpRequest) -> HttpResponse:
    # Serve the exact runtime from the pinned installed wheel, including morphdom.
    file = Path(django_unicorn.__file__).parent / "static/unicorn/js/unicorn.min.js"
    return HttpResponse(file.read_bytes(), content_type="text/javascript")


urlpatterns = [
    path("", index),
    path("unicorn/", include("django_unicorn.urls")),
    path("static/unicorn/js/unicorn.min.js", runtime),
    path("assets/<str:name>", asset_view(HERE / "assets", SCENARIO)),
    path("health", health),
]
application = get_asgi_application()


instrument(Template, "render")

instrument(UnicornView, "render")

application = RenderTimingMiddleware(application)
