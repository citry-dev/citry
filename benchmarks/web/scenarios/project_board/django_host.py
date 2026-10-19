"""Provide shared Django configuration and response timing for compatible adapters."""

import os
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

import django
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from model import response_identity


def configure() -> None:
    settings.configure(
        DEBUG=False,
        SECRET_KEY="project-board-local-benchmark-only",  # noqa: S106 - isolated synthetic data
        ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"],
        ROOT_URLCONF="app",
        MIDDLEWARE=["django_host.ResponseTiming", "django.middleware.csrf.CsrfViewMiddleware"],
        INSTALLED_APPS=[],
        USE_TZ=True,
        TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": False}],
    )
    django.setup()


class ResponseTiming:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = perf_counter()
        identity_token = response_identity.set(None)
        response = self.get_response(request)
        response["Server-Timing"] = f"application;dur={(perf_counter() - start) * 1000:.3f}"
        response["Cache-Control"] = "no-store"
        identity = response_identity.get()
        if identity:
            response["X-Bench-Operation"] = identity[0]
            response["X-Bench-Revision"] = str(identity[1])
        response_identity.reset(identity_token)
        return response


def health(_request: HttpRequest) -> HttpResponse:
    return HttpResponse(os.environ.get("CITRY_BENCH_SERVER_NONCE", "ok"), content_type="text/plain")


def asset_view(directory: Path, shared: Path) -> Callable[[HttpRequest, str], HttpResponse]:
    def asset(_request: HttpRequest, name: str) -> HttpResponse:
        path = shared / name if name == "board.css" else directory / name
        if not path.is_file() or path.parent not in (shared, directory):
            return HttpResponse(status=404)
        return HttpResponse(path.read_bytes(), content_type="text/css" if name.endswith(".css") else "text/javascript")

    return asset
