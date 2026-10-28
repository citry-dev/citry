"""
Flask convenience for mounting citry's routes.

One call wraps the app's WSGI entry point so requests under ``prefix`` go to
citry's routes, and records the prefix on the instance::

    from flask import Flask
    from citry.contrib.flask import mount

    app = Flask(__name__)
    mount(app, citry_instance)            # serves /citry/... ; default prefix
    mount(app, citry_instance, prefix="/assets/citry")

Works with any application exposing a ``wsgi_app`` attribute holding its
WSGI callable (Flask does); the routes themselves are served by the
dependency-free ``citry.contrib.wsgi`` app, so this module needs no Flask
import of its own.

For a Flask app, ``mount()`` also registers a path checker: a function
``citry check`` and the editor call to ask whether the app's routes or
static files serve a link path written in a template, so a link to a page
or file the app does not serve is reported before anyone clicks it.
"""

from __future__ import annotations

import posixpath
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import unquote, urlsplit

from citry._path_checks import PathLookup, register_path_checker
from citry._sub_path import normalize_sub_path, recording_sub_path, request_sub_path
from citry.contrib._path_lookup import files_beside
from citry.contrib.wsgi import wsgi_app
from citry.util.routing import normalize_mount_prefix

if TYPE_CHECKING:
    from collections.abc import Iterable

    from citry._path_checks import PathChecker
    from citry.citry import Citry
    from citry.contrib.wsgi import StartResponse

__all__ = ["mount"]


def mount(app: Any, citry_instance: Citry, prefix: str = "/citry") -> None:
    """
    Mount ``citry_instance``'s routes into a Flask ``app`` at ``prefix``, and
    record the prefix on the instance.

    A trailing ``/`` on ``prefix`` is dropped, so ``"/citry/"`` serves the
    same paths as ``"/citry"``. For a Flask app, ``citry check`` and the
    editor can also ask the app whether it serves each link path written in
    your templates.

    Raises:
        ValueError: If ``prefix`` does not start with ``/``, or is the root
            ``"/"``. The app is left unchanged.

    """
    # Validate before touching the app: a failure after the wsgi_app swap
    # would leave the app routing to a Citry instance that never recorded
    # its prefix. Normalizing also keeps "/citry/" from matching only
    # "/citry//..." paths below.
    mount_path = normalize_mount_prefix(prefix)
    # Every request matches a root mount, so the Flask app's own routes
    # would never run.
    if not mount_path:
        msg = (
            f"Flask mount() needs a prefix below the root, such as '/citry', got {prefix!r}. "
            "A root prefix would send every request to Citry and none to the Flask app."
        )
        raise ValueError(msg)
    citry_wsgi = wsgi_app(citry_instance)
    host_wsgi = app.wsgi_app

    def dispatch(environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
        path = environ.get("PATH_INFO", "")
        # SCRIPT_NAME is the sub-path the server mounted the app at. Record
        # it while the request is handled, so URLs built in Citry's own
        # routes, which run outside Flask, start with it.
        with recording_sub_path(environ.get("SCRIPT_NAME", "")):
            if path == mount_path or path.startswith(mount_path + "/"):
                # The WSGI convention for sub-mounting: the prefix moves into
                # SCRIPT_NAME, PATH_INFO keeps the remainder.
                forwarded = dict(environ)
                forwarded["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + mount_path
                forwarded["PATH_INFO"] = path[len(mount_path) :]
                return citry_wsgi(forwarded, start_response)
            return host_wsgi(environ, start_response)

    app.wsgi_app = dispatch
    citry_instance.set_mounted_prefix(prefix)

    def sub_path() -> str:
        script_root = _flask_script_root(app)
        if script_root is not None:
            return normalize_sub_path(script_root)
        # A request to Citry's own routes runs outside Flask, so dispatch
        # recorded its SCRIPT_NAME.
        recorded = request_sub_path()
        if recorded is not None:
            return recorded
        # Outside a request, Flask builds URLs below APPLICATION_ROOT, so
        # Citry's URLs follow it too.
        return normalize_sub_path(app.config.get("APPLICATION_ROOT"))

    citry_instance._set_sub_path_reader(sub_path)
    # Only a Flask app has a route table to ask. Any other WSGI host gets the
    # mount without a checker, so `citry check` skips its links rather than
    # failing on every one.
    if hasattr(app, "url_map"):
        register_path_checker(citry_instance, _flask_path_checker(app), host=app)


def _flask_script_root(app: Any) -> str | None:
    """
    Return the current request's ``script_root`` when ``app`` is handling it, or ``None``.

    Inside one of the app's requests, Flask's ``script_root`` is the
    sub-path, after any WSGI middleware such as ``ProxyFix`` set it, and a
    streamed response that keeps the request context still sees it.
    """
    try:
        # Imported here, not at module load: mount() also accepts a WSGI
        # app that is not Flask, in an environment without Flask.
        from flask import current_app, has_request_context, request  # noqa: PLC0415
    except ImportError:
        return None
    # Another Flask app's request says nothing about this app's sub-path.
    # current_app is a proxy, so compare the app object it stands for.
    if not has_request_context() or cast("Any", current_app)._get_current_object() is not app:
        return None
    return request.script_root


def _flask_path_checker(app: Any) -> PathChecker:
    """
    Build a path checker that answers from the Flask ``app``'s URL map and static folders.

    The checker reads the URL map each time it is called, so it sees the
    routes the app adds after ``mount()``. A path that one of the app's rules
    accepts for another method counts as served, because a form can still
    post to it. A path the app redirects (to add a trailing slash, to merge
    doubled slashes, or through a rule's ``redirect_to``) counts when the
    redirect target is served. A path the app's ``static`` endpoint (or a
    blueprint's) accepts counts only when the file exists in that static
    folder.
    """

    def check(path: str) -> PathLookup:
        return _flask_lookup(app, path, follow_redirect=True)

    return check


def _flask_lookup(app: Any, path: str, *, follow_redirect: bool) -> PathLookup:
    """Answer for one path under every host the app's rules are bound to."""
    # Imported here, not at module load: this module must import without
    # Flask installed, and only a Flask app ever registers this checker.
    from werkzeug.exceptions import HTTPException, MethodNotAllowed, NotFound  # noqa: PLC0415
    from werkzeug.routing import RequestRedirect  # noqa: PLC0415

    nearby: set[str] = set(_literal_rules(app))
    for host, adapter in _adapters(app):
        try:
            endpoint, arguments = adapter.match(path, method="GET")
        except MethodNotAllowed:
            # The path exists for another method, such as a POST-only form target.
            return PathLookup(found=True)
        except RequestRedirect as redirect:
            target = urlsplit(redirect.new_url)
            # A redirect to another host cannot be checked here, and the
            # browser follows a second redirect too, so both count as served.
            if not follow_redirect or target.netloc != host:
                return PathLookup(found=True)
            return _flask_lookup(app, unquote(target.path), follow_redirect=False)
        except NotFound:
            # Another host the app routes for may still serve the path.
            continue
        except HTTPException:
            # Any other refusal (a websocket-only rule) still names a route the
            # app owns, so the link is not a typo of a missing route.
            return PathLookup(found=True)
        folder = _static_folder(app, endpoint)
        if folder is None:
            return PathLookup(found=True)
        lookup = _static_file_lookup(path, folder, str(arguments.get("filename", "")))
        if lookup.found:
            return lookup
        nearby.update(lookup.nearby)
    return PathLookup(found=False, nearby=tuple(sorted(nearby)))


def _adapters(app: Any) -> list[tuple[str, Any]]:
    """
    Bind the app's URL map once for each host its rules are written for, paired with that host.

    A root-relative link goes to the host of the page that holds it, which
    the checker does not know. So a path counts as served when a rule for any
    of the app's hosts serves it, the same way the Starlette checker treats a
    ``Host`` route.
    """
    url_map = app.url_map
    server_name = app.config.get("SERVER_NAME") or "localhost"
    rules = list(url_map.iter_rules())
    # A host or subdomain with a variable in it has no single name to bind
    # to, so its rules are left out rather than guessed at.
    if url_map.host_matching:
        hosts = sorted({rule.host for rule in rules if rule.host and "<" not in rule.host} | {server_name})
        return [(host, url_map.bind(host)) for host in hosts]
    adapters = [(server_name, url_map.bind(server_name))]
    for subdomain in sorted({rule.subdomain for rule in rules if rule.subdomain and "<" not in rule.subdomain}):
        adapters.append((f"{subdomain}.{server_name}", url_map.bind(server_name, subdomain=subdomain)))
    return adapters


def _literal_rules(app: Any) -> tuple[str, ...]:
    """Return the app's page rules that take no arguments, the only ones a link can name exactly."""
    # A websocket rule is not a page a link opens, so it is no suggestion.
    return tuple(sorted({rule.rule for rule in app.url_map.iter_rules() if not rule.arguments and not rule.websocket}))


def _static_folder(app: Any, endpoint: str) -> str | None:
    """
    Return the folder a static endpoint serves files from, or ``None`` for any other endpoint.

    The answer is an empty string when the endpoint's owner has no static folder.
    """
    # Flask names the app's static route "static", and each blueprint's
    # "<blueprint>.static", where a nested blueprint's name is dotted.
    if endpoint == "static":
        owner = app
    elif endpoint.endswith(".static"):
        owner = app.blueprints.get(endpoint.removesuffix(".static"))
    else:
        return None
    folder = getattr(owner, "static_folder", None)
    # The endpoint exists only when the owner had a static folder, but an app
    # may clear it later; a missing folder serves nothing.
    return folder if isinstance(folder, str) else ""


def _static_file_lookup(path: str, folder: str, filename: str) -> PathLookup:
    """Answer for a path the static route accepted: found only when the file exists inside ``folder``."""
    # Imported here for the same reason as in the checker above.
    from werkzeug.security import safe_join  # noqa: PLC0415

    # Flask serves the file through werkzeug's safe_join and refuses anything
    # that is not a regular file, so the checker applies the same two tests.
    # safe_join returns None for a name that leaves the folder through "..".
    full_path = safe_join(folder, filename) if folder else None
    if full_path is not None and Path(full_path).is_file():
        return PathLookup(found=True)
    # Suggest only from the requested file's own folder, and only when that
    # folder is itself inside the static folder.
    parent = safe_join(folder, posixpath.dirname(filename)) if folder else None
    return PathLookup(found=False, nearby=files_beside(path, [parent] if parent is not None else []))
