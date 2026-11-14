"""
Every mount resolves a cache-script path in one pass.

The two `cache/...` routes place parameters next to each other with a `.`
between them. On each adapter, a valid path resolves to the script handler
with the right parts, and a long path that never matches is rejected
quickly rather than by searching every way to split the dots. Every mount,
Django's patterns included, matches with `match_route_pattern`. Inputs are
ordinary: a real class-id-shaped string, and a long run of `.`-separated
parts for the no-match case.
"""

from __future__ import annotations

import time

import pytest

from citry import Citry
from citry.util.routing import match_route

_BOUND_SECONDS = 0.5
# A long run of dot-separated parts ending in `/`, which no single route
# segment can hold, so every route reports no match after one scan.
_LONG_NO_MATCH = "a." * 20_000 + "/"


def _citry() -> Citry:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    return app


def _dependency_routes(app: Citry) -> list:
    from citry.ext.dependencies.routes import dependency_routes

    return dependency_routes(app)


def test_shared_matcher_resolves_a_valid_cache_path() -> None:
    app = _citry()
    routes = _dependency_routes(app)
    matched = match_route(routes, "cache/Table_a1b2c3.0f1e2d3c.js")
    assert matched is not None
    assert matched.params == {"class_id": "Table_a1b2c3", "vars_hash": "0f1e2d3c", "script_type": "js"}
    two = match_route(routes, "cache/Table_a1b2c3.css")
    assert two is not None
    assert two.params == {"class_id": "Table_a1b2c3", "script_type": "css"}


def test_shared_matcher_rejects_a_long_cache_path_quickly() -> None:
    app = _citry()
    routes = _dependency_routes(app)
    start = time.perf_counter()
    assert match_route(routes, "cache/" + _LONG_NO_MATCH) is None
    assert time.perf_counter() - start < _BOUND_SECONDS


def test_django_resolver_resolves_and_rejects_in_one_pass() -> None:
    django = pytest.importorskip("django")
    from django.conf import settings

    if not settings.configured:
        settings.configure(ALLOWED_HOSTS=["*"])
        django.setup()
    from django.urls import URLResolver, include, path

    from citry.contrib.django import urlpatterns

    patterns = [path("citry/", include(urlpatterns(_citry(), prefix="/citry")))]

    def resolve(target: str):
        for entry in patterns:
            assert isinstance(entry, URLResolver)
            try:
                return entry.resolve(target)
            except Exception:  # noqa: BLE001 - Resolver404 and friends
                return None
        return None

    valid = resolve("citry/cache/Table_a1b2c3.0f1e2d3c.js")
    assert valid is not None
    assert valid.kwargs == {"class_id": "Table_a1b2c3", "vars_hash": "0f1e2d3c", "script_type": "js"}

    start = time.perf_counter()
    assert resolve("citry/cache/" + _LONG_NO_MATCH) is None
    assert time.perf_counter() - start < _BOUND_SECONDS


def test_flask_mount_serves_a_cache_path_and_rejects_a_long_one_quickly() -> None:
    flask = pytest.importorskip("flask")
    from citry.contrib.flask import mount

    host = flask.Flask(__name__)
    app = Citry(autodiscover=False)
    mount(host, app)
    client = host.test_client()

    # A well-formed cache path reaches Citry's route, which answers 404
    # because no such script is cached, rather than falling through to Flask.
    assert client.get("/citry/cache/Table_a1b2c3.js").status_code == 404

    start = time.perf_counter()
    response = client.get("/citry/cache/" + "a." * 20_000 + "x/y")
    assert response.status_code == 404
    assert time.perf_counter() - start < _BOUND_SECONDS
