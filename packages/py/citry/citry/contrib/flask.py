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
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from citry.contrib.wsgi import wsgi_app
from citry.util.routing import normalize_mount_prefix

if TYPE_CHECKING:
    from collections.abc import Iterable

    from citry.citry import Citry
    from citry.contrib.wsgi import StartResponse

__all__ = ["mount"]


def mount(app: Any, citry_instance: Citry, prefix: str = "/citry") -> None:
    """
    Mount ``citry_instance``'s routes into a Flask ``app`` at ``prefix``, and
    record the prefix on the instance.

    A trailing ``/`` on ``prefix`` is dropped, so ``"/citry/"`` serves the
    same paths as ``"/citry"``.

    Raises:
        ValueError: If ``prefix`` does not start with ``/``. The app is left
            unchanged.

    """
    # Validate before touching the app: a failure after the wsgi_app swap
    # would leave the app routing to a Citry instance that never recorded
    # its prefix. Normalizing also keeps "/citry/" from matching only
    # "/citry//..." paths below.
    prefix = normalize_mount_prefix(prefix)
    citry_wsgi = wsgi_app(citry_instance)
    host_wsgi = app.wsgi_app

    def dispatch(environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
        path = environ.get("PATH_INFO", "")
        if path == prefix or path.startswith(prefix + "/"):
            # The WSGI convention for sub-mounting: the prefix moves into
            # SCRIPT_NAME, PATH_INFO keeps the remainder.
            forwarded = dict(environ)
            forwarded["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + prefix
            forwarded["PATH_INFO"] = path[len(prefix) :]
            return citry_wsgi(forwarded, start_response)
        return host_wsgi(environ, start_response)

    app.wsgi_app = dispatch
    citry_instance.set_mounted_prefix(prefix)
