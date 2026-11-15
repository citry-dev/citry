"""
The application both releases run during the rolling-deploy check.

`check.py` installs the previous citry release in one virtual environment and
the candidate in another, then runs this file once in each. It imports only
what an application imports from citry, because the same file has to run on
both releases, just as one application's code runs on both sides of a deploy.

Two commands:

- `render` (old release): renders a page and a cached component into the
  shared store, and writes the HTML to a JSON file.
- `serve` (new release): answers the requests in a JSON file through Citry's
  WSGI app, renders the cached component again, and writes what it got.

Both processes use one `DiskCache` directory, the store the docs recommend
for workers on one host, so the new process sees what the old one wrote, as
workers sharing a cache do during a deploy.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from typing import Any

import diskcache

from citry import Citry, Component
from citry.contrib.caches import DiskCache
from citry.contrib.wsgi import wsgi_app

# Every process signs and checks State with the same secret, as the workers
# of one application do.
SECRET = "rolling-deploy-check-secret-0123456789"  # noqa: S105
PREFIX = "/citry"
# The render cache keeps entries apart only by namespace and generation. Using
# the same values on both releases is the case that could go wrong: a new
# release reading an entry an old release wrote.
CACHE_SETTINGS = {"namespace": "rolling-deploy", "generation": "same-on-both-releases", "ttl": 600}


def build_app(store: Path, *, cache_generation: str | None = None) -> tuple[Citry, dict[str, type[Component]]]:
    """Build the application: one engine and the components the check uses."""
    cache_settings = dict(CACHE_SETTINGS)
    # `serve` builds a second engine with another generation to render the
    # cached component without reading the old entry.
    if cache_generation is not None:
        cache_settings["generation"] = cache_generation
    engine = Citry(
        secret=SECRET,
        autodiscover=False,
        cache=DiskCache(diskcache.Cache(str(store))),
        extensions_defaults={"cache": cache_settings},
    )
    engine.set_mounted_prefix(PREFIX)

    class SignedState:
        count: int = 0

        def render(self) -> Any:
            return SignedCounter(count=self.count)

    class SignedCounter(Component):
        citry = engine
        State = SignedState

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002 - citry passes both
            return kwargs

        class Events:
            def bump(self, state: SignedState) -> Any:
                state.count += 1
                return state.render()

        template = """
            <button id="signed" @c-click="bump">{{ count }}</button>
        """

    class StoredState:
        # The State lives in the shared store, and the page holds only a
        # pointer to it.
        _storage = "server"
        count: int = 0

        def render(self) -> Any:
            return StoredCounter(count=self.count)

    class StoredCounter(Component):
        citry = engine
        State = StoredState

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002 - citry passes both
            return kwargs

        class Events:
            def bump(self, state: StoredState) -> Any:
                state.count += 1
                return state.render()

        template = """
            <button id="stored" @c-click="bump">{{ count }}</button>
        """

    class CachedCard(Component):
        citry = engine

        class Kwargs:
            name: str

        class Cache:
            enabled = True
            ttl = 600
            version = 1

        def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG002 - citry passes both
            return {"name": kwargs.name}

        template = """
            <article class="card">{{ name }}</article>
        """

    return engine, {"SignedCounter": SignedCounter, "StoredCounter": StoredCounter, "CachedCard": CachedCard}


def render(store: Path, out: Path) -> None:
    """Render what an open page from the old release holds."""
    _engine, components = build_app(store)
    pages = {
        "signed": components["SignedCounter"](count=0).render().serialize(),
        "stored": components["StoredCounter"](count=0).render().serialize(),
        "cached": components["CachedCard"](name="Travel mug").render().serialize(),
    }
    out.write_text(json.dumps(pages), encoding="utf-8")


def _call_wsgi(app: Any, request: dict[str, Any]) -> dict[str, Any]:
    """Run one request through the WSGI app, as a server mounted at PREFIX would."""
    body = request.get("body", "").encode()
    environ: dict[str, Any] = {
        "REQUEST_METHOD": request["method"],
        "SCRIPT_NAME": PREFIX,
        "PATH_INFO": request["path"].removeprefix(PREFIX),
        "QUERY_STRING": "",
        "SERVER_NAME": "app.test",
        "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": sys.stderr,
        "wsgi.version": (1, 0),
        "wsgi.multithread": False,
        "wsgi.multiprocess": True,
        "wsgi.run_once": False,
        "CONTENT_LENGTH": str(len(body)),
        "HTTP_HOST": "app.test",
    }
    for name, value in request.get("headers", {}).items():
        key = name.upper().replace("-", "_")
        environ[key if key in {"CONTENT_TYPE", "CONTENT_LENGTH"} else f"HTTP_{key}"] = value
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]], _exc_info: Any = None) -> None:
        captured["status"] = int(status.split(" ", 1)[0])
        captured["headers"] = {name.lower(): value for name, value in headers}

    chunks = app(environ, start_response)
    try:
        content = b"".join(chunks)
    finally:
        close = getattr(chunks, "close", None)
        if close is not None:
            close()
    return {**captured, "body": content.decode("utf-8", errors="replace")}


def serve(store: Path, requests_file: Path, out: Path) -> None:
    """Answer the old page's requests and render the cached component on the new release."""
    engine, components = build_app(store)
    app = wsgi_app(engine)
    requests = json.loads(requests_file.read_text(encoding="utf-8"))
    answers = {name: _call_wsgi(app, request) for name, request in requests.items()}
    # The cached component, once through the shared entry the old release may
    # have written and once from an engine that cannot see that entry.
    shared = components["CachedCard"](name="Travel mug").render().serialize()
    _fresh_engine, fresh_components = build_app(store, cache_generation="fresh-render")
    fresh = fresh_components["CachedCard"](name="Travel mug").render().serialize()
    out.write_text(json.dumps({"answers": answers, "cached": {"shared": shared, "fresh": fresh}}), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 2)[1])
    commands = parser.add_subparsers(dest="command", required=True)
    render_parser = commands.add_parser("render")
    render_parser.add_argument("--store", type=Path, required=True)
    render_parser.add_argument("--out", type=Path, required=True)
    serve_parser = commands.add_parser("serve")
    serve_parser.add_argument("--store", type=Path, required=True)
    serve_parser.add_argument("--requests", type=Path, required=True)
    serve_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "render":
        render(args.store, args.out)
    else:
        serve(args.store, args.requests, args.out)


if __name__ == "__main__":
    main()
