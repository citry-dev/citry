"""
FastAPI / Starlette convenience for mounting citry's routes.

One call mounts the route table and records the prefix on the instance, so
URL building (script URLs in fragments, the runtime ``src``) works::

    from fastapi import FastAPI
    from citry.contrib.fastapi import mount

    app = FastAPI()
    mount(app, citry_instance)            # serves /citry/... ; default prefix
    mount(app, citry_instance, prefix="/assets/citry")

Works with any application exposing Starlette's ``.mount(path, app)``
(FastAPI and Starlette both do); the routes themselves are served by the
dependency-free ``citry.contrib.asgi`` app, so this module needs no FastAPI
import of its own.

``mount()`` also registers a path checker: a function ``citry check`` and
the editor call to ask whether the app's routes or static files serve a
link path written in a template, so a link to a page or file the app does
not serve is reported before anyone clicks it.
"""

from __future__ import annotations

import stat
from pathlib import PurePath
from typing import TYPE_CHECKING, Any

from citry._path_checks import PathLookup, register_path_checker
from citry.contrib._path_lookup import files_beside
from citry.contrib.asgi import asgi_app
from citry.util.routing import normalize_mount_prefix

if TYPE_CHECKING:
    import os
    from collections.abc import Sequence

    from citry._path_checks import PathChecker
    from citry.citry import Citry

__all__ = ["mount"]


def mount(app: Any, citry_instance: Citry, prefix: str = "/citry") -> None:
    """
    Mount ``citry_instance``'s routes into a FastAPI/Starlette ``app`` at
    ``prefix``, and record the prefix on the instance.

    A trailing ``/`` on ``prefix`` is dropped. When ``app`` lists its routes,
    as FastAPI and Starlette apps do, ``citry check`` and the editor can also
    ask it whether it serves each link path written in your templates.

    Raises:
        ValueError: If ``prefix`` does not start with ``/``.

    """
    # Check the prefix before handing it to Starlette, whose own check fails
    # with a bare AssertionError that does not name the Citry setting.
    # set_mounted_prefix() checks the caller's prefix again, so it gets the
    # original: the normalized root prefix "" would fail that check.
    mount_path = normalize_mount_prefix(prefix)
    app.mount(mount_path, asgi_app(citry_instance))
    citry_instance.set_mounted_prefix(prefix)
    # Only an app that lists its routes can be asked about a path. Any other
    # host gets the mount without a checker, so `citry check` skips its
    # links rather than failing on every one.
    if hasattr(app, "routes"):
        register_path_checker(citry_instance, _starlette_path_checker(app), host=app)


def _starlette_path_checker(app: Any) -> PathChecker:
    """
    Build a path checker that answers from a Starlette or FastAPI ``app``'s routes.

    The checker walks ``app.routes`` each time it is called, so it sees the
    routes the app adds after ``mount()``. It asks each route the same
    question Starlette's router asks for a GET request, and follows the
    router's rules:

    - The first route that matches the path and the method decides.
    - A route that matches the path for another method (a POST-only form
      target) counts as served.
    - A ``StaticFiles`` mount serves the path only when the file exists.
    - A mount of an app that does not list its routes counts as served,
      because the checker cannot look inside it.
    - When nothing matches, the router redirects to the path with its
      trailing slash added or removed, so that path decides.
    """

    def check(path: str) -> PathLookup:
        found = _serves(app, path, follow_slash_redirect=True)
        if found:
            return PathLookup(found=True)
        return PathLookup(found=False, nearby=_nearby(app.routes, path, prefix=""))

    return check


def _serves(app: Any, path: str, *, follow_slash_redirect: bool) -> bool:
    """Return whether a GET request for ``path`` reaches a route or file of ``app``."""
    # The keys Starlette's route matching reads from a request's scope.
    scope: dict[str, Any] = {"type": "http", "method": "GET", "path": path, "root_path": "", "headers": []}
    verdict = _match_routes(app.routes, scope, redirect_slashes=_redirects_slashes(app))
    if verdict == "redirect":
        # The redirect goes back to the top of the app with the other spelling
        # of the trailing slash. One step is enough: a second redirect could
        # only toggle the slash back, a loop the browser gives up on.
        toggled = path.rstrip("/") if path.endswith("/") else f"{path}/"
        return follow_slash_redirect and _serves(app, toggled, follow_slash_redirect=False)
    return verdict == "found"


def _match_routes(routes: Sequence[Any], scope: dict[str, Any], *, redirect_slashes: bool) -> str:
    """
    Return ``"found"``, ``"missing"`` or ``"redirect"`` for ``scope`` under one router's ``routes``.

    This mirrors ``starlette.routing.Router.app``: the first route that matches
    fully handles the request, a route that matches only the path answers
    when no route matches fully, and the trailing-slash redirect comes last.
    """
    # Imported here, not at module load: this module must import without
    # Starlette installed, and only a Starlette app ever registers this checker.
    from starlette.routing import Host, Match  # noqa: PLC0415

    matched_other_method = False
    host_redirects = False
    for route in routes:
        if isinstance(route, Host):
            # A root-relative link goes to the page's own host, which the
            # checker does not know, so a Host route serves the path when any
            # of its routes does, and otherwise the next route is asked. A
            # Host app that does not list its routes cannot be asked, and
            # counting it as serving every path would hide every typo.
            inner = getattr(route.app, "routes", None)
            if inner is None:
                continue
            verdict = _match_routes(inner, scope, redirect_slashes=_redirects_slashes(route.app))
            if verdict == "found":
                return "found"
            host_redirects = host_redirects or verdict == "redirect"
            continue
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            return _route_verdict(route, {**scope, **child_scope})
        if match == Match.PARTIAL:
            matched_other_method = True
    if matched_other_method:
        return "found"
    # The host's own router would redirect to the other trailing-slash
    # spelling, which the caller then checks from the top.
    if host_redirects:
        return "redirect"
    if redirect_slashes and scope["path"] != "/":
        toggled = dict(scope)
        toggled["path"] = scope["path"].rstrip("/") if scope["path"].endswith("/") else f"{scope['path']}/"
        if any(route.matches(toggled)[0] != Match.NONE for route in routes):
            return "redirect"
    return "missing"


def _route_verdict(route: Any, scope: dict[str, Any]) -> str:
    """Return what the route that fully matched ``scope`` does with it."""
    # Imported here for the same reason as in _match_routes.
    from starlette.routing import Mount  # noqa: PLC0415
    from starlette.staticfiles import StaticFiles  # noqa: PLC0415

    if not isinstance(route, Mount):
        # A plain route matched the path and the method.
        return "found"
    # A mount may wrap its app in middleware; the app it was given is kept
    # underneath, and that is the one that decides what is served.
    mounted = getattr(route, "_base_app", route.app)
    if isinstance(mounted, StaticFiles):
        return "found" if _static_file_exists(mounted, scope) else "missing"
    inner = getattr(mounted, "routes", None)
    if inner is None:
        # An ASGI app that does not list its routes (such as Citry's own)
        # cannot be asked, so the mount's prefix is taken as its answer.
        return "found"
    return _match_routes(inner, scope, redirect_slashes=_redirects_slashes(mounted))


def _redirects_slashes(app: Any) -> bool:
    """Return whether a router, or an app's router, redirects a path that differs only by a trailing slash."""
    router = getattr(app, "router", app)
    # Starlette's Router redirects by default; an unknown router is assumed to
    # behave the same, so a missing slash is not reported against it.
    return bool(getattr(router, "redirect_slashes", True))


def _static_file_exists(files: Any, scope: dict[str, Any]) -> bool:
    """Return whether a ``StaticFiles`` app answers a GET for ``scope`` with a file."""
    relative = files.get_path(scope)
    _, status = _lookup(files, relative)
    if status is None:
        return False
    if stat.S_ISREG(status.st_mode):
        return True
    # In html mode a folder is served through its index.html, after a redirect
    # that adds the trailing slash.
    if stat.S_ISDIR(status.st_mode) and files.html:
        _, index_status = _lookup(files, str(PurePath(relative, "index.html")))
        return index_status is not None and stat.S_ISREG(index_status.st_mode)
    return False


def _lookup(files: Any, relative: str) -> tuple[str, os.stat_result | None]:
    """Run ``StaticFiles.lookup_path``, reading the errors it raises for bad names as "no file"."""
    try:
        full_path, status = files.lookup_path(relative)
    except (OSError, ValueError):
        # StaticFiles answers a name that is too long, holds a null byte, or
        # cannot be read with an error status, never with the file.
        return "", None
    return full_path, status


def _nearby(routes: Sequence[Any], path: str, *, prefix: str) -> tuple[str, ...]:
    """Return the served paths a reader may have meant by the missing ``path``."""
    # Imported here for the same reason as in _match_routes.
    from starlette.routing import Host, Mount, Route  # noqa: PLC0415
    from starlette.staticfiles import StaticFiles  # noqa: PLC0415

    found: set[str] = set()
    for route in routes:
        if isinstance(route, Host):
            found.update(_nearby(getattr(route.app, "routes", ()), path, prefix=prefix))
            continue
        # A route or mount with a parameter in its own path has no single URL
        # a link could spell exactly. Starlette gives every mount a trailing
        # "path" parameter for the part below it, which does not count.
        parameters = set(getattr(route, "param_convertors", ()))
        if isinstance(route, Mount):
            parameters.discard("path")
        if parameters:
            continue
        if isinstance(route, Mount):
            mount_path = prefix + route.path
            mounted = getattr(route, "_base_app", route.app)
            if isinstance(mounted, StaticFiles):
                found.update(_static_neighbours(mounted, path, mount_path))
            else:
                found.update(_nearby(getattr(mounted, "routes", ()), path, prefix=mount_path))
        elif isinstance(route, Route):
            # Only an HTTP route is a page a link opens; a websocket route is not.
            found.add(prefix + route.path)
    return tuple(sorted(found))


def _static_neighbours(files: Any, path: str, mount_path: str) -> tuple[str, ...]:
    """Return the files beside ``path`` when it falls under a ``StaticFiles`` mount at ``mount_path``."""
    if not path.startswith(f"{mount_path}/"):
        return ()
    # StaticFiles builds the file name from the part of the path below the mount.
    relative = files.get_path({"type": "http", "path": path[len(mount_path) :], "root_path": ""})
    # lookup_path keeps the name inside the mounted folder, so a folder
    # reached through ".." offers no suggestions.
    folder, status = _lookup(files, str(PurePath(relative).parent))
    if status is None or not stat.S_ISDIR(status.st_mode):
        return ()
    return files_beside(path, [folder])
