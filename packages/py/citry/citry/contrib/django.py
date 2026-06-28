"""
Django integration: URL patterns over ``Citry.urls`` and a cache wrapper.

Mounting the routes (record the prefix so URL building matches where you
include them)::

    # urls.py
    from citry.contrib.django import urlpatterns as citry_urlpatterns

    urlpatterns = [
        ...,
        path("citry/", include(citry_urlpatterns(citry_instance, prefix="/citry"))),
    ]

Pointing citry at a Django cache (so multi-worker fragment setups share one
store through the cache framework you already configured)::

    from django.core.cache import caches
    from citry.contrib.django import DjangoCache

    app = Citry(cache=DjangoCache(caches["default"]))

Hot reload in development (clear a component's caches when its template/JS/CSS
file changes, so the next render reads fresh content), driven by Django's own
autoreloader::

    # apps.py
    from django.apps import AppConfig
    from citry.contrib.django import enable_hot_reload

    class MyAppConfig(AppConfig):
        def ready(self):
            enable_hot_reload(citry_instance)  # mode="hot" by default

Citry owns this adapter (rather than leaving it to django-components) so
plain citry works with Django regardless of how django-components ends up
relating to citry. Django is imported lazily, only when these functions are
called.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from citry.util.routing import flatten_routes

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing import Literal

    from citry.citry import Citry
    from citry.util.routing import URLRoute

_PARAM_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _to_django_path(path: str) -> str:
    """Convert citry's ``{param}`` placeholders to Django's ``<str:param>``."""
    return _PARAM_RE.sub(r"<str:\1>", path)


def _make_view(route: URLRoute) -> Any:
    # Imported here, not at module load: this module must be importable
    # without Django on the path (citry.contrib hosts several integrations).
    from django.http import HttpResponse, HttpResponseNotAllowed  # noqa: PLC0415

    def view(request: Any, **kwargs: Any) -> Any:
        if request.method not in route.methods and request.method != "HEAD":
            return HttpResponseNotAllowed(route.methods)
        handler = route.handler
        assert handler is not None  # noqa: S101 - flatten_routes only yields handler routes
        response = handler(request, **kwargs)
        return HttpResponse(content=response.body, content_type=response.content_type, status=response.status)

    return view


def urlpatterns(citry_instance: Citry, prefix: str | None = None) -> list[Any]:
    """
    ``Citry.urls`` as Django URL patterns, for ``include()``-ing.

    Pass ``prefix`` (where you include the patterns, e.g. ``"/citry"``) to
    also record it on the instance, so URL building (fragment manifests, the
    runtime ``src``) points at the right place; leaving it ``None`` means you
    call ``set_mounted_prefix`` yourself.
    """
    from django.urls import path as django_path  # noqa: PLC0415

    if prefix is not None:
        citry_instance.set_mounted_prefix(prefix)

    patterns = []
    for full_path, route in flatten_routes(citry_instance.urls):
        # Django route syntax cannot express two parameters in one path
        # segment (the cache routes separate them with dots), so use re_path
        # via the compiled citry pattern when the segment-wise conversion
        # would be ambiguous. Plain `path()` covers parameter-free routes.
        if "{" in full_path:
            from django.urls import re_path  # noqa: PLC0415

            from citry.util.routing import compile_route_pattern  # noqa: PLC0415

            pattern = compile_route_pattern(full_path).pattern
            patterns.append(re_path(pattern, _make_view(route), name=route.name))
        else:
            patterns.append(django_path(full_path, _make_view(route), name=route.name))
    return patterns


def enable_hot_reload(
    citry_instance: Citry,
    *,
    mode: Literal["hot", "restart"] = "hot",
) -> Callable[..., bool | None]:
    """
    Reload changed component files in development, using Django's autoreloader.

    Connects a receiver to Django's ``file_changed`` autoreload signal. When a
    watched file changes, the receiver clears the caches of the components that
    loaded it (``Citry.invalidate_file``). With ``mode="hot"`` (the default) the
    change is handled in place and the server keeps running; with
    ``mode="restart"`` the process restart is left to Django (the same thing
    Django does for a Python edit). Files that back no loaded component fall
    through to Django's normal handling either way.

    Call once at startup, e.g. from your ``AppConfig.ready()``. Django watches
    its template and static directories, so this needs no watcher of its own.
    Returns the connected receiver (disconnect it via ``file_changed.disconnect``
    if you ever need to).
    """
    if mode not in ("hot", "restart"):
        msg = f"mode must be 'hot' or 'restart', got {mode!r}"
        raise ValueError(msg)

    from django.utils.autoreload import file_changed  # noqa: PLC0415

    def on_component_file_changed(sender: Any, file_path: Path, **kwargs: Any) -> bool | None:  # noqa: ARG001
        reset = citry_instance.invalidate_file(file_path)
        if not reset:
            # The file backs no loaded component: let Django's autoreloader
            # decide (it restarts the dev server on a Python edit, for example).
            return None
        # A truthy return tells Django's notify_file_changed the change was
        # handled, suppressing the restart; returning None lets Django restart.
        return True if mode == "hot" else None

    # weak=False: the receiver is a local closure, so a weak connection (Django's
    # default) would let it be garbage-collected right away.
    file_changed.connect(on_component_file_changed, weak=False)
    return on_component_file_changed


class DjangoCache:
    """
    Adapt a Django cache (``django.core.cache.caches[...]``) to citry's
    ``CitryCache`` protocol, so citry's stored scripts live in whatever cache
    backend the Django project already runs (Redis, Memcached, database, ...).
    """

    def __init__(self, cache: Any) -> None:
        self._cache = cache

    def get(self, key: str) -> str | None:
        value = self._cache.get(key)
        return value if isinstance(value, str) else None

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        # Django: timeout=None means "never expire", matching citry's ttl.
        self._cache.set(key, value, timeout=ttl)

    def delete(self, key: str) -> None:
        self._cache.delete(key)

    def has(self, key: str) -> bool:
        return bool(self._cache.has_key(key))
