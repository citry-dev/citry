"""
The application both releases run during the rolling-deploy check.

`check.py` installs the previous citry release in one virtual environment and
the candidate in another, then runs this file once in each. It imports only
what an application imports from citry, because the same file has to run on
both releases, just as one application's code runs on both sides of a deploy.

Three commands:

- `render`: renders pages and a cached component into the shared store, and
  writes the HTML to a JSON file.
- `serve` (the other release): answers the requests in a JSON file through
  Citry's WSGI app, renders the cached component again, and writes what it
  got.
- `answer` (the same release as `serve`): only answers requests. `check.py`
  uses it for the second event call, which needs the State the first answer
  returned.

`check.py` runs `render` with one release and `serve` and `answer` with the
other, in both directions: old release renders and new release serves, then
the other way round. Both processes use one
`DiskCache` directory, the store the docs recommend for workers on one host,
so the serving process sees what the rendering one wrote, as workers sharing
a cache do during a deploy.
"""

from __future__ import annotations

import argparse
import hashlib
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
CACHED_CARD_RENDERS: list[str] = []
# Two releases share a render cache entry when the namespace, generation,
# component and inputs match (unless a release adds more to the key). Using the
# same namespace and generation on both releases is the case that could go
# wrong: one release reading an entry the other wrote.
CACHE_SETTINGS = {"namespace": "rolling-deploy", "generation": "same-on-both-releases", "ttl": 600}


def count_label(count: int) -> str:
    """
    The text a counter shows, which `check.py` looks for in an answer's render.

    The whole text is one value, so it reaches the render as one string
    whatever form the release uses (HTML, or the data of a Vue render), and
    the template itself holds none of the text, so the template alone
    cannot match.
    """
    return f"rolling-count-{count}"


def build_app(store: Path, *, cache_generation: str | None = None) -> tuple[Citry, dict[str, Any]]:
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
    # Each State renders the component defined after it, so it finds the
    # class through this table, filled in once every class exists.
    components: dict[str, Any] = {}

    class SignedState:
        count: int = 0

        def render(self) -> Any:
            return components["SignedCounter"](count=self.count)

    class SignedCounter(Component):
        citry = engine
        State = SignedState

        class Kwargs:
            count: int = 0

        def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG002 - citry passes both
            return {"label": count_label(kwargs.count)}

        class Events:
            def bump(self, state: SignedState) -> Any:
                state.count += 1
                return state.render()

        template = """
            <button id="signed" @c-click="bump">{{ label }}</button>
        """

    class StoredState:
        # The State lives in the shared store, and the page holds only a
        # pointer to it.
        _storage = "server"
        count: int = 0

        def render(self) -> Any:
            return components["StoredCounter"](count=self.count)

    class StoredCounter(Component):
        citry = engine
        State = StoredState

        class Kwargs:
            count: int = 0

        def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG002 - citry passes both
            return {"label": count_label(kwargs.count)}

        class Events:
            def bump(self, state: StoredState) -> Any:
                state.count += 1
                return state.render()

        template = """
            <button id="stored" @c-click="bump">{{ label }}</button>
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
            # Counted so `serve` can say whether it reused the other release's entry.
            CACHED_CARD_RENDERS.append(kwargs.name)
            return {"name": kwargs.name}

        template = """
            <article class="card">{{ name }}</article>
        """

    components.update(SignedCounter=SignedCounter, StoredCounter=StoredCounter, CachedCard=CachedCard)
    return engine, components


def render(store: Path, out: Path, start_count: int) -> None:
    """Render what an open page from this release holds."""
    _engine, components = build_app(store)
    # The counters start away from State's default of 0, so a server that
    # ignored the page's State and built a fresh one would show another count.
    pages = {
        "signed": components["SignedCounter"](count=start_count).render().serialize(),
        "stored": components["StoredCounter"](count=start_count).render().serialize(),
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
    # The digest lets the check compare a served file with the one the page expects.
    return {
        **captured,
        "body": content.decode("utf-8", errors="replace"),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _answer_all(engine: Citry, requests_file: Path) -> dict[str, dict[str, Any]]:
    """Answer every request in the file, in order, through one WSGI app."""
    app = wsgi_app(engine)
    requests = json.loads(requests_file.read_text(encoding="utf-8"))
    return {name: _call_wsgi(app, request) for name, request in requests.items()}


def serve(store: Path, requests_file: Path, out: Path) -> None:
    """Answer the other release's page requests, and render the cached component again."""
    engine, components = build_app(store)
    answers = _answer_all(engine, requests_file)
    # The cached component, once through the shared entry the old release may
    # have written and once from an engine that cannot see that entry.
    shared = components["CachedCard"](name="Travel mug").render().serialize()
    reused = not CACHED_CARD_RENDERS
    _fresh_engine, fresh_components = build_app(store, cache_generation="fresh-render")
    fresh = fresh_components["CachedCard"](name="Travel mug").render().serialize()
    out.write_text(
        json.dumps({"answers": answers, "cached": {"shared": shared, "fresh": fresh, "reused": reused}}),
        encoding="utf-8",
    )


def answer(store: Path, requests_file: Path, out: Path) -> None:
    """Answer requests through Citry's WSGI app, without rendering anything else."""
    engine, _components = build_app(store)
    out.write_text(json.dumps({"answers": _answer_all(engine, requests_file)}), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 2)[1])
    commands = parser.add_subparsers(dest="command", required=True)
    render_parser = commands.add_parser("render")
    render_parser.add_argument("--store", type=Path, required=True)
    render_parser.add_argument("--out", type=Path, required=True)
    render_parser.add_argument("--start-count", type=int, required=True)
    serve_parser = commands.add_parser("serve")
    serve_parser.add_argument("--store", type=Path, required=True)
    serve_parser.add_argument("--requests", type=Path, required=True)
    serve_parser.add_argument("--out", type=Path, required=True)
    answer_parser = commands.add_parser("answer")
    answer_parser.add_argument("--store", type=Path, required=True)
    answer_parser.add_argument("--requests", type=Path, required=True)
    answer_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "render":
        render(args.store, args.out, args.start_count)
    elif args.command == "serve":
        serve(args.store, args.requests, args.out)
    else:
        answer(args.store, args.requests, args.out)


if __name__ == "__main__":
    main()
