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

``urlpatterns()`` also registers a path checker: a function ``citry check``
and the editor call to ask whether the project's URL patterns or static
files serve a link path written in a template, so a link to a page or file
the project does not serve is reported before anyone clicks it.

Citry owns this adapter (rather than leaving it to django-components) so
plain citry works with Django regardless of how django-components ends up
relating to citry. Django is imported lazily, only when these functions are
called.
"""

from __future__ import annotations

import inspect
import io
import posixpath
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from citry._django_startup import start_django
from citry._path_checks import PathLookup, register_path_checker
from citry._sub_path import normalize_sub_path
from citry.contrib._path_lookup import files_beside, path_below
from citry.util.routing import RouteHeaders, RouteRequest, body_read_limit, flatten_routes, normalize_mount_prefix

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import Literal

    from citry._path_checks import PathChecker
    from citry.citry import Citry
    from citry.util.routing import RouteResponse, URLRoute

__all__ = ["DjangoCache", "enable_hot_reload", "secret", "urlpatterns"]

# Every call to urlpatterns() asks the same Django project, so a later call
# replaces the checker an earlier one registered.
_DJANGO_PROJECT = object()

_PARAM_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _to_django_path(path: str) -> str:
    """Convert citry's ``{param}`` placeholders to Django's ``<str:param>``."""
    return _PARAM_RE.sub(r"<str:\1>", path)


def _read_body(request: Any, limit: int | None) -> bytes:
    """
    Read Django's request body, at most ``limit`` bytes when a limit is set.

    ``request.body`` reads the whole body into memory, and refuses one larger
    than Django's ``DATA_UPLOAD_MAX_MEMORY_SIZE``. With a route limit, Citry
    reads from the stream instead and stops one byte past it, so the route's
    own limit governs the request in place of Django's.
    """
    if limit is None:
        return bytes(request.body)
    # Something (often middleware reading request.POST) already holds the
    # body in memory, so take it from there.
    if hasattr(request, "_body"):
        return bytes(request.body[:limit])
    if getattr(request, "_read_started", False):
        # Middleware (such as CsrfViewMiddleware on a multipart upload) has
        # already parsed the stream into POST and FILES, so no body bytes are
        # left to read. Django has no total limit for uploaded files, so check
        # the size the client declared, and hand the route a body one byte
        # past its limit when it is over, so the route rejects the request as
        # it would any oversized body.
        try:
            declared = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            declared = 0
        return bytes(limit) if declared >= limit else b""
    chunks: list[bytes] = []
    received = 0
    # read(n) may return fewer bytes than asked for; Django's stream already
    # stops at Content-Length.
    while received < limit:
        chunk = request.read(limit - received)
        if not chunk:
            break
        chunks.append(chunk)
        received += len(chunk)
    data = b"".join(chunks)
    # Leave the request as Django's own `request.body` would, so a guard, a
    # handler, or a payload codec can still read `request.native.body`,
    # `POST`, or `FILES`. For a body over the limit these hold the bytes read.
    request._body = data
    request._stream = io.BytesIO(data)
    return data


def _build_request(request: Any, body_limit: int | None = None) -> RouteRequest:
    """Read Django's ``HttpRequest`` into a framework-neutral request."""
    headers = RouteHeaders(request.headers.items())
    return RouteRequest(
        method=request.method,
        path=request.path,
        query={key: tuple(values) for key, values in request.GET.lists()},
        headers=headers,
        body=_read_body(request, body_limit),
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
        response = cast("RouteResponse", handler(_build_request(request, body_read_limit(route)), **kwargs))
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

    Calling it also lets ``citry check`` and the editor ask the project
    whether its URL patterns or static files serve each link path written in
    your templates.
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
    # Django sets the script prefix for each request (FORCE_SCRIPT_NAME when
    # set, else SCRIPT_NAME) and once at django.setup(), so Citry's URLs
    # start with the same sub-path as the project's reverse() URLs.
    citry_instance._set_sub_path_reader(_django_sub_path)
    # Registered with the patterns, after every route was accepted, so a
    # rejected call leaves the instance without a checker too.
    register_path_checker(citry_instance, _django_path_checker(), host=_DJANGO_PROJECT)
    return patterns


def _django_sub_path() -> str:
    """Return the sub-path the project is served below for the current request, such as ``/shop``."""
    from django.urls import get_script_prefix  # noqa: PLC0415

    return normalize_sub_path(get_script_prefix())


def _django_path_checker() -> PathChecker:
    """
    Build a path checker that answers from the project's URL patterns and static files.

    Django's URL lookups need no app object: the checker reads
    ``ROOT_URLCONF`` and the static file settings each time it is called, so
    it sees the patterns as the running project has them. It answers in this
    order:

    - A path under ``MEDIA_URL`` names a user upload, which no setting lists,
      so it counts as served.
    - A path under ``STATIC_URL``, with ``django.contrib.staticfiles``
      installed, counts only when the static file finders find a file. The
      finders decide even when a development pattern serves the prefix,
      because such a pattern accepts every name under it.
    - Any other path counts when ``resolve()`` finds a pattern for it, under
      any of the project's languages when it uses ``i18n_patterns()``, or when
      ``CommonMiddleware`` would redirect it to the same path with a trailing
      slash that resolves.

    A project served below a sub-path (``FORCE_SCRIPT_NAME``) writes that
    sub-path in its links, so the checker removes it before ``resolve()``.
    """

    def check(path: str) -> PathLookup:
        # Imported here, not at module load: this module must be importable
        # without Django on the path (citry.contrib hosts several integrations).
        from django.apps import apps  # noqa: PLC0415
        from django.conf import settings as django_settings  # noqa: PLC0415
        from django.urls import get_script_prefix  # noqa: PLC0415

        # `citry check` and the editor start Django before they import the app
        # when DJANGO_SETTINGS_MODULE is set. A script that imports the URL
        # configuration directly, or a project that calls settings.configure(),
        # has not loaded its apps or set the URL prefix from FORCE_SCRIPT_NAME
        # yet. The static file finders and resolve() need both, as a running
        # server has them. start_django() does nothing once the apps are loaded.
        start_django()
        script_prefix = get_script_prefix()
        media_url = _site_prefix(django_settings.MEDIA_URL, script_prefix)
        if media_url is not None and path.startswith(media_url):
            return PathLookup(found=True)
        static_url = _site_prefix(django_settings.STATIC_URL, script_prefix)
        if static_url is not None and path.startswith(static_url) and apps.is_installed("django.contrib.staticfiles"):
            return _static_file_lookup(path, path[len(static_url) :])
        # The links start with the sub-path Citry starts its own URLs with,
        # read the same way; a link to the sub-path alone, such as "/shop",
        # reaches the project's root too.
        sub_path = _django_sub_path()
        # Suggestions are written the way a link writes them, with the sub-path.
        nearby = tuple(sorted({sub_path + route for route in _literal_routes()}))
        below = path_below(path, sub_path)
        if below is None:
            # A path outside the sub-path never reaches this project.
            return PathLookup(found=False, nearby=nearby)
        # Django serves an empty path as its root.
        path_info = below or "/"
        if _resolve_match(path_info) is not None or _redirects_to_slash(path_info):
            return PathLookup(found=True)
        return PathLookup(found=False, nearby=nearby)

    return check


def _site_prefix(url: str | None, script_prefix: str) -> str | None:
    """Return a ``STATIC_URL``-style setting as a path prefix ending in ``/``, or ``None`` if unset or remote."""
    # Django adds the script prefix to a relative setting when it is read, so
    # an unset (empty) setting reads as the script prefix itself, which would
    # otherwise cover every path of the site.
    if not url or url == script_prefix:
        return None
    # A full or protocol-relative URL points at another host (a CDN), whose
    # files the project cannot list.
    if not url.startswith("/") or url.startswith("//"):
        return None
    return url if url.endswith("/") else f"{url}/"


def _resolve_match(path_info: str) -> Any:
    """Return the ``resolve()`` match for ``path_info``, or ``None`` when no pattern accepts it."""
    from django.conf import settings as django_settings  # noqa: PLC0415
    from django.urls import LocalePrefixPattern, Resolver404, get_resolver, resolve  # noqa: PLC0415
    from django.utils import translation  # noqa: PLC0415

    try:
        return resolve(path_info)
    except Resolver404:
        pass
    # i18n_patterns() accept only the active language's prefix, and the
    # checker runs outside any request, so a link to another language's page
    # is tried under that language too. Django's own helper for this test
    # caches its answer, so it would miss a URLconf changed after first use.
    uses_language_prefix = any(isinstance(entry.pattern, LocalePrefixPattern) for entry in get_resolver().url_patterns)
    if not django_settings.USE_I18N or not uses_language_prefix:
        return None
    for code, _name in django_settings.LANGUAGES:
        with translation.override(code):
            try:
                return resolve(path_info)
            except Resolver404:
                continue
    return None


def _redirects_to_slash(path_info: str) -> bool:
    """Return whether ``CommonMiddleware`` would send a request for ``path_info`` on to ``path_info + "/"``."""
    from django.conf import settings as django_settings  # noqa: PLC0415
    from django.middleware.common import CommonMiddleware  # noqa: PLC0415

    # The redirect needs both the setting and the middleware that acts on it,
    # and happens only when the slash-terminated path resolves. A view can
    # opt out with the no_append_slash decorator, which the middleware honours.
    if path_info.endswith("/") or not django_settings.APPEND_SLASH:
        return False
    if not any(_is_subclass(entry, CommonMiddleware) for entry in django_settings.MIDDLEWARE):
        return False
    match = _resolve_match(f"{path_info}/")
    return match is not None and bool(getattr(match.func, "should_append_slash", True))


def _is_subclass(dotted_path: str, base: type) -> bool:
    """Return whether the middleware at ``dotted_path`` is ``base`` or a subclass of it."""
    from django.utils.module_loading import import_string  # noqa: PLC0415

    try:
        middleware = import_string(dotted_path)
    except ImportError:
        # Django itself fails at startup on such an entry; here it just
        # cannot be the middleware that redirects.
        return False
    return isinstance(middleware, type) and issubclass(middleware, base)


def _static_file_lookup(path: str, relative: str) -> PathLookup:
    """Answer for a path under ``STATIC_URL``: found only when the finders find a file for ``relative``."""
    from django.contrib.staticfiles import finders  # noqa: PLC0415
    from django.core.exceptions import SuspiciousFileOperation  # noqa: PLC0415

    # Django's static file view normalizes the name the same way before it
    # asks the finders, and serves only a file, never a folder.
    name = posixpath.normpath(relative).lstrip("/")
    try:
        found = finders.find(name)
    except SuspiciousFileOperation:
        # A name that leaves the static folders through "..".
        found = None
    if isinstance(found, str) and Path(found).is_file():
        return PathLookup(found=True)
    try:
        # Passed by position: Django 5.2 renamed this argument from `all` to `find_all`.
        folders = finders.find(posixpath.dirname(name), True)  # noqa: FBT003
    except SuspiciousFileOperation:
        folders = []
    return PathLookup(found=False, nearby=files_beside(path, [folder for folder in folders if Path(folder).is_dir()]))


def _literal_routes(patterns: Iterable[Any] | None = None, prefix: str = "") -> Iterable[str]:
    """Yield each URL pattern that takes no parameters, as the path a link writes for it."""
    from django.urls import URLResolver, get_resolver  # noqa: PLC0415
    from django.urls.resolvers import RoutePattern  # noqa: PLC0415

    for entry in get_resolver().url_patterns if patterns is None else patterns:
        pattern = entry.pattern
        # A regular expression or a converter has no single spelling, and a
        # language prefix depends on the request, so only plain path()
        # strings name a path a link can write exactly.
        if not isinstance(pattern, RoutePattern) or pattern.converters:
            continue
        route = prefix + str(pattern)
        if isinstance(entry, URLResolver):
            yield from _literal_routes(entry.url_patterns, route)
        else:
            yield f"/{route}"


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
