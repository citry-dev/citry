"""
Development server: render docs pages live, on each request.

A Starlette app with a catch-all route that maps the request URL to a markdown
file under the content dir and renders it through the pipeline. Citry's own
asset routes (component JS/CSS, the client runtime) are mounted under
``/citry`` so a page that embeds live component examples gets its assets served;
a ``static/`` dir, if present, is served at ``/static``.

The asset mounts are registered before the catch-all so they win for their own
prefixes. Run it with the ``serve`` CLI command (uvicorn with auto-reload), or
point any ASGI server at ``docs_site.serve:app``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from citry import citry as default_citry
from citry.contrib.asgi import asgi_app
from docs_site.config import DocsConfig
from docs_site.config import config as default_config
from docs_site.examples import get_example_registry
from docs_site.nav import load_nav
from docs_site.paths import md_to_url, url_to_md
from docs_site.pipeline import render_page

if TYPE_CHECKING:
    from starlette.requests import Request

    from citry import Citry

# Where citry's component-asset routes are mounted (and recorded on the instance
# so any emitted asset URLs point at the right place).
_CITRY_PREFIX = "/citry"


def create_app(*, config: DocsConfig | None = None, citry_instance: Citry | None = None) -> Starlette:
    """Build the docs dev-server app for ``config`` (defaults to the module config)."""
    config = config or default_config
    citry_instance = citry_instance or default_citry

    async def serve_page(request: Request) -> HTMLResponse | PlainTextResponse:
        md_path = url_to_md(config.content_dir, request.path_params.get("url_path", ""))
        if md_path is None:
            return PlainTextResponse("Not Found", status_code=404)
        # Canonical and current_path match what the build would write, so a
        # preview matches the deployed page.
        page_url = md_to_url(md_path.relative_to(config.content_dir.resolve()))
        site_base = config.site_url.rstrip("/")
        canonical = f"{site_base}/{page_url}" if site_base else ""
        # Load the nav fresh each request so edits to _nav.yml show up live.
        nav_tree = load_nav(config.content_dir / "_nav.yml")
        result = render_page(
            md_path.read_text(encoding="utf-8"),
            config=config,
            canonical=canonical,
            nav_tree=nav_tree,
            current_path=page_url,
        )
        return HTMLResponse(result.html)

    async def serve_example(request: Request) -> HTMLResponse | PlainTextResponse:
        # The standalone live-demo page an example card's iframe loads.
        info = get_example_registry().get(request.path_params["name"])
        if info is None:
            return PlainTextResponse("Not Found", status_code=404)
        return HTMLResponse(str(info.page_cls()))

    routes: list[Route | Mount] = [
        Mount(_CITRY_PREFIX, app=asgi_app(citry_instance)),
        # Before the catch-all: the example demo pages live outside the content tree.
        Route("/examples/{name}/", serve_example),
    ]
    static_dir = config.base_dir / "static"
    if static_dir.is_dir():
        routes.append(Mount("/static", app=StaticFiles(directory=static_dir)))
    # Catch-all LAST so the routes above win for their own prefixes.
    routes.append(Route("/{url_path:path}", serve_page))

    app = Starlette(routes=routes)
    citry_instance.set_mounted_prefix(_CITRY_PREFIX)
    return app


# Module-level app for ``uvicorn docs_site.serve:app`` (and the serve command).
app = create_app()
