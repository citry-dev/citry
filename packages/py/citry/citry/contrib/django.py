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

Reusing Django's ``SECRET_KEY`` as citry's signing secret (so values citry
signs are covered by the key the project already manages)::

    from citry.contrib.django import secret

    app = Citry(secret=secret())

Citry owns this adapter (rather than leaving it to django-components) so
plain citry works with Django regardless of how django-components ends up
relating to citry. Django is imported lazily, only when these functions are
called.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from citry.util.routing import RouteHeaders, RouteRequest, flatten_routes, normalize_mount_prefix

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Literal

    from citry.citry import Citry
    from citry.util.routing import RouteResponse, URLRoute

__all__ = ["DjangoCache", "enable_hot_reload", "secret", "urlpatterns"]

_PARAM_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _to_django_path(path: str) -> str:
    """Convert citry's ``{param}`` placeholders to Django's ``<str:param>``."""
    return _PARAM_RE.sub(r"<str:\1>", path)


def _build_request(request: Any) -> RouteRequest:
    """Read Django's ``HttpRequest`` into a framework-neutral request."""
    headers = RouteHeaders(request.headers.items())
    return RouteRequest(
        method=request.method,
        path=request.path,
        query={key: tuple(values) for key, values in request.GET.lists()},
        headers=headers,
        body=request.body,
        content_type=headers.get("content-type", ""),
        native=request,
    )


def _make_view(route: URLRoute) -> Any:
    """
    Wrap one citry route as a Django view.

    The view is the standard adapter shape: translate the ``HttpRequest``
    into a ``RouteRequest`` (``_build_request``), call the route's
    handler, and translate the returned ``RouteResponse`` into an
    ``HttpResponse``.
    """
    # Imported here, not at module load: this module must be importable
    # without Django on the path (citry.contrib hosts several integrations).
    from django.http import HttpResponse, HttpResponseNotAllowed  # noqa: PLC0415

    def view(request: Any, **kwargs: Any) -> Any:
        if request.method not in route.methods and request.method != "HEAD":
            return HttpResponseNotAllowed(route.methods)
        handler = route.handler
        assert handler is not None  # noqa: S101 - flatten_routes only yields handler routes
        # urlpatterns() rejected async handlers up front, so the call returns
        # a concrete RouteResponse.
        response = cast("RouteResponse", handler(_build_request(request), **kwargs))
        http_response = HttpResponse(content=response.body, content_type=response.content_type, status=response.status)
        # Django's response object holds one value per header name, so a
        # repeated name (e.g. two Set-Cookie lines) cannot be represented.
        # Reject it loudly instead of silently keeping only the last value;
        # the ASGI and WSGI adapters send every pair.
        seen_names: set[str] = set()
        for name, value in response.headers:
            lowered = name.lower()
            if lowered in seen_names:
                msg = (
                    f"RouteResponse repeats the response header {name!r}, which the Django adapter "
                    "cannot send: Django's response object holds one value per header name. Send one "
                    "value per name, or serve citry through the ASGI or WSGI adapter, which send "
                    "every pair."
                )
                raise ValueError(msg)
            seen_names.add(lowered)
            http_response[name] = value
        return http_response

    return view


def urlpatterns(citry_instance: Citry, prefix: str | None = None) -> list[Any]:
    """
    ``Citry.urls`` as Django URL patterns, for ``include()``-ing.

    Pass ``prefix`` (where you include the patterns, e.g. ``"/citry"``) to
    also record it on the instance, so URL building (fragment manifests, the
    runtime ``src``) points at the right place; leaving it ``None`` means you
    call ``set_mounted_prefix`` yourself.

    The generated views are synchronous, so every route handler must be a
    plain function; an ``async def`` handler raises ``TypeError`` here,
    pointing at the ASGI adapter as the fix.
    """
    from django.urls import path as django_path  # noqa: PLC0415

    # Check the prefix up front, but record it only after every route has
    # been accepted, so a rejected async handler leaves the instance untouched.
    if prefix is not None:
        normalize_mount_prefix(prefix)

    patterns = []
    for full_path, route in flatten_routes(citry_instance.urls):
        # Reject async handlers at URL-configuration time (startup), so the
        # error points at the fix instead of surfacing as a request-time 500.
        if inspect.iscoroutinefunction(route.handler):
            msg = (
                f"citry route {route.name or full_path!r} has an 'async def' handler, which the "
                "synchronous Django view adapter cannot run. Serve citry's routes through the ASGI "
                "adapter instead (mount citry.contrib.asgi.asgi_app in your ASGI application), or "
                "make the handler a plain 'def'."
            )
            raise TypeError(msg)
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

    if prefix is not None:
        citry_instance.set_mounted_prefix(prefix)
    return patterns


def enable_hot_reload(
    citry_instance: Citry,
    *,
    mode: Literal["hot", "restart"] = "hot",
) -> Callable[..., bool | None]:
    """
    Pick up edits to component files in development, using Django's autoreloader.

    Call it once at startup, for example from your ``AppConfig.ready()``. When
    ``runserver`` starts its reloader, this asks the reloader to also watch
    every file under the engine's ``dirs`` (``Citry(dirs=[...])``). Django
    already watches Python files and its own template directories. When a
    watched file that a component has loaded changes, Citry clears that
    component's stored template, JS, and CSS (see
    [`invalidate_file()`][citry.Citry.invalidate_file]), so the next render
    reads the file again.

    Other changed files are handled like this:

    - A Python file goes to Django, which restarts the server.
    - Any other file under the engine's ``dirs`` needs no action, because no
      component has read it yet, so the server keeps running.
    - Any other file outside the engine's ``dirs`` goes to Django's normal
      handling.

    Calling it again for the same engine replaces the earlier call, so the
    last ``mode`` wins. Point the engine's ``dirs`` at your component
    folders, not the project root: the reloader checks every file under
    them, so a large folder makes it slow.

    Args:
        citry_instance: The engine whose components should pick up edits.
        mode: What happens after Citry clears a changed component file.
            ``"hot"`` (the default) keeps the server running, and the next
            render reads the new file. ``"restart"`` restarts the server
            process, the same way Django restarts it after a Python edit.

    Returns:
        The receiver connected to Django's ``file_changed`` signal.

    Raises:
        ValueError: When ``mode`` is not ``"hot"`` or ``"restart"``.

    Example:
        ::

            # apps.py
            from django.apps import AppConfig

            from citry.contrib.django import enable_hot_reload
            from myapp import engine


            class MyAppConfig(AppConfig):
                name = "myapp"

                def ready(self):
                    enable_hot_reload(engine)

    """
    if mode not in ("hot", "restart"):
        msg = (
            f"mode must be 'hot' or 'restart', got {mode!r}. Pass mode='hot' to reload component files "
            "in place, or mode='restart' to restart the server."
        )
        raise ValueError(msg)

    # Imported here, not at module load: this module must be importable
    # without Django on the path (citry.contrib hosts several integrations).
    from django.utils import autoreload  # noqa: PLC0415

    def component_dirs() -> list[Path]:
        # Read the dirs on each call, so the watch and the claim check always
        # agree with the engine's current settings. Resolved so they compare
        # equal to the resolved changed-file paths.
        return [Path(directory).resolve() for directory in citry_instance.settings.dirs]

    def watch_component_dirs(sender: Any, **kwargs: Any) -> None:  # noqa: ARG001
        # Django's reloader reports Python files, files under its template
        # directories, and translation .mo files, so a component file
        # elsewhere under the engine's dirs would never reach
        # on_component_file_changed.
        for directory in component_dirs():
            sender.watch_dir(directory, "**/*")

    def on_component_file_changed(sender: Any, file_path: Path, **kwargs: Any) -> bool | None:  # noqa: ARG001
        reset = citry_instance.invalidate_file(file_path)
        if reset:
            if mode == "restart":
                # Django restarts only when no receiver returns a truthy value,
                # and its own template receiver returns True for every file in
                # a template directory. Returning None here would therefore not
                # restart for those files, so restart the same way Django does.
                autoreload.trigger_reload(file_path)
            # A truthy return tells Django the change was handled, so the
            # server keeps running and the next render reads the new file.
            return True
        # A Python edit needs a restart, so leave it to Django.
        if file_path.suffix == ".py":
            return None
        # watch_component_dirs made the reloader report every file under the
        # engine's dirs, including compiled bytecode and files no component
        # has loaded. None of them has anything stored to clear, so claim them
        # instead of letting Django restart the server for each one.
        resolved = Path(file_path).resolve()
        if any(directory == resolved or directory in resolved.parents for directory in component_dirs()):
            return True
        # The file is outside Citry's dirs: Django's other receivers decide.
        return None

    # Django ignores a second connect with the same dispatch_uid. Drop the
    # receivers from an earlier call for this engine first, so that call's
    # mode cannot claim a change before this call's mode sees it.
    dispatch_uid = _hot_reload_dispatch_uid(citry_instance)
    autoreload.autoreload_started.disconnect(dispatch_uid=dispatch_uid)
    autoreload.file_changed.disconnect(dispatch_uid=dispatch_uid)
    # weak=False: both receivers are local closures, so a weak connection
    # (Django's default) would let them be garbage-collected right away.
    autoreload.autoreload_started.connect(watch_component_dirs, weak=False, dispatch_uid=dispatch_uid)
    autoreload.file_changed.connect(on_component_file_changed, weak=False, dispatch_uid=dispatch_uid)
    return on_component_file_changed


def _hot_reload_dispatch_uid(citry_instance: Citry) -> str:
    """Name one engine's hot reload receivers, so a repeated call replaces them."""
    # id() stays unique while connected: the receiver closures keep the engine alive.
    return f"citry.contrib.django.enable_hot_reload:{id(citry_instance)}"


def secret() -> str:
    """
    Django's ``SECRET_KEY``, for passing as ``Citry(secret=...)``.

    Citry signs values with the engine-level
    [`secret`][citry.CitrySettings.secret] setting. In a Django project the
    natural signing key is the one the project already manages, so pass it
    through::

        from citry import Citry
        from citry.contrib.django import secret

        app = Citry(secret=secret())

    The key is read when this is called, so Django settings must be configured
    by then (in a normal Django startup they already are).

    Returns:
        The ``SECRET_KEY`` of the active Django settings.

    Raises:
        RuntimeError: When Django settings are not configured; the message
            names the fix.
        django.core.exceptions.ImproperlyConfigured: When settings are
            configured but the ``SECRET_KEY`` itself is unusable (for example
            empty); Django's own message explains the problem.

    """
    # Imported here, not at module load: this module must be importable
    # without Django on the path (citry.contrib hosts several integrations).
    from django.conf import settings as django_settings  # noqa: PLC0415
    from django.core.exceptions import ImproperlyConfigured  # noqa: PLC0415

    try:
        return cast("str", django_settings.SECRET_KEY)
    except ImproperlyConfigured as err:
        if django_settings.configured:
            # Settings are configured but unusable in some other way (for
            # example an empty SECRET_KEY); Django's own message explains
            # that better than a generic one here.
            raise
        msg = (
            "citry.contrib.django.secret() reads Django's SECRET_KEY, but Django settings are not "
            "configured. Set the DJANGO_SETTINGS_MODULE environment variable or call "
            "django.conf.settings.configure() before building the Citry instance, or pass the "
            'secret directly: Citry(secret="...").'
        )
        raise RuntimeError(msg) from err


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
        from citry.cache import _normalize_ttl  # noqa: PLC0415

        normalized_ttl = _normalize_ttl(ttl)
        if normalized_ttl == 0:
            self.delete(key)
            return
        # Django: timeout=None means "never expire", matching citry's ttl.
        self._cache.set(key, value, timeout=normalized_ttl)

    def delete(self, key: str) -> None:
        self._cache.delete(key)

    def has(self, key: str) -> bool:
        return bool(self._cache.has_key(key))
