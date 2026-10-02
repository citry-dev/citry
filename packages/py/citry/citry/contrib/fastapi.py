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
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from citry.contrib.asgi import asgi_app
from citry.util.routing import normalize_mount_prefix

if TYPE_CHECKING:
    from citry.citry import Citry

__all__ = ["mount"]


def mount(app: Any, citry_instance: Citry, prefix: str = "/citry") -> None:
    """
    Mount ``citry_instance``'s routes into a FastAPI/Starlette ``app`` at
    ``prefix``, and record the prefix on the instance.

    A trailing ``/`` on ``prefix`` is dropped.

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
