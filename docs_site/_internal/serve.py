"""
Development server: render docs pages live, on each request.

A Starlette app with a catch-all route that maps the request URL to a markdown
file under the content dir and renders it through the pipeline. Citry's own
asset routes (component JS/CSS, the client runtime) are mounted under
``/citry`` so a page that embeds live component examples gets its assets served;
a ``static/`` dir, if present, is served at ``/static``.

The asset mounts are registered before the catch-all so they win for their own
prefixes. Run it with the ``serve`` CLI command (uvicorn with auto-reload), or
point any ASGI server at ``docs_site._internal.serve:app``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from citry import citry as default_citry
from citry.contrib.asgi import asgi_app
from docs_site._internal.build import configure_docs_globals
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.examples import get_example_registry
from docs_site._internal.nav import load_nav
from docs_site._internal.paths import md_to_url, url_to_md
from docs_site._internal.pipeline import render_page
from docs_site._internal.reference_pages import (
    category,
    reference_index_markdown,
    reference_nav_section,
    reference_page_markdown,
)
from docs_site._internal.release_notes import (
    Release,
    parse_changelog,
    release_index_markdown,
    release_page_markdown,
    releases_nav_section,
)

if TYPE_CHECKING:
    from starlette.requests import Request

    from citry import Citry
    from docs_site._internal.nav import NavTree

# Where citry's component-asset routes are mounted (and recorded on the instance
# so any emitted asset URLs point at the right place).
_CITRY_PREFIX = "/citry"


def _load_nav(config: DocsConfig) -> NavTree:
    """Load the content nav and append the generated reference section."""
    nav_tree = load_nav(config.content_dir / "_nav.yml")
    changelog_file = config.repo_root / "CHANGELOG.md"
    if changelog_file.is_file():
        nav_tree.sections.append(releases_nav_section(parse_changelog(changelog_file.read_text(encoding="utf-8"))))
    nav_tree.sections.append(reference_nav_section())
    return nav_tree


def create_app(*, config: DocsConfig | None = None, citry_instance: Citry | None = None) -> Starlette:
    """Build the docs dev-server app for ``config`` (defaults to the module config)."""
    config = config or default_config
    citry_instance = citry_instance or default_citry
    # Set the version / site-name template globals once so {{ version }} resolves
    # in live-rendered pages, the same as the static build does.
    version = configure_docs_globals(config)

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
        result = render_page(
            md_path.read_text(encoding="utf-8"),
            config=config,
            canonical=canonical,
            nav_tree=_load_nav(config),
            current_path=page_url,
            version=version,
            source_path=md_path,
        )
        return HTMLResponse(result.html)

    async def serve_example(request: Request) -> HTMLResponse | PlainTextResponse:
        # The standalone live-demo page an example card's iframe loads.
        info = get_example_registry().get(request.path_params["name"])
        if info is None:
            return PlainTextResponse("Not Found", status_code=404)
        return HTMLResponse(str(info.page_cls()))

    async def serve_example_variant(request: Request) -> HTMLResponse | PlainTextResponse:
        # A fragment example serves each variant on its own endpoint, the way the
        # static build pre-renders it to examples/<name>/<variant>/. Rendering the
        # fragment here also caches its script, so the /citry mount then serves the
        # fragment's JS/CSS (the dev-server counterpart to export_fragment_deps).
        info = get_example_registry().get(request.path_params["name"])
        if info is None:
            return PlainTextResponse("Not Found", status_code=404)
        variant = info.fragments.get(request.path_params["variant"])
        if variant is None:
            return PlainTextResponse("Not Found", status_code=404)
        return HTMLResponse(variant().render().serialize(deps_strategy="fragment"))

    def _render_reference(page_url: str, source: str) -> HTMLResponse:
        site_base = config.site_url.rstrip("/")
        canonical = f"{site_base}/{page_url}" if site_base else ""
        html = render_page(
            source,
            config=config,
            canonical=canonical,
            nav_tree=_load_nav(config),
            current_path=page_url,
            version=version,
        ).html
        return HTMLResponse(html)

    async def serve_reference_index(request: Request) -> HTMLResponse:  # noqa: ARG001
        return _render_reference("reference/", reference_index_markdown())

    async def serve_reference(request: Request) -> HTMLResponse | PlainTextResponse:
        cat = category(request.path_params["slug"])
        if cat is None:
            return PlainTextResponse("Not Found", status_code=404)
        return _render_reference(f"reference/{cat.slug}/", reference_page_markdown(cat))

    def _changelog_releases() -> list[Release]:
        changelog = config.repo_root / "CHANGELOG.md"
        if not changelog.is_file():
            return []
        return parse_changelog(changelog.read_text(encoding="utf-8"))

    def _render_release(page_url: str, source: str) -> HTMLResponse:
        site_base = config.site_url.rstrip("/")
        canonical = f"{site_base}/{page_url}" if site_base else ""
        # run_citry_pass=False: release prose shows citry syntax as text (see build).
        html = render_page(
            source,
            config=config,
            canonical=canonical,
            nav_tree=_load_nav(config),
            current_path=page_url,
            version=version,
            run_citry_pass=False,
        ).html
        return HTMLResponse(html)

    async def serve_release_index(request: Request) -> HTMLResponse:  # noqa: ARG001
        return _render_release("releases/", release_index_markdown(_changelog_releases()))

    async def serve_release(request: Request) -> HTMLResponse | PlainTextResponse:
        slug = request.path_params["slug"]
        release = next((r for r in _changelog_releases() if r.slug == slug), None)
        if release is None:
            return PlainTextResponse("Not Found", status_code=404)
        return _render_release(f"releases/{release.slug}/", release_page_markdown(release))

    routes: list[Route | Mount] = [
        Mount(_CITRY_PREFIX, app=asgi_app(citry_instance)),
        # Before the catch-all: example demos and generated reference pages live
        # outside the content tree.
        Route("/examples/{name}/", serve_example),
        Route("/examples/{name}/{variant}/", serve_example_variant),
        Route("/reference/", serve_reference_index),
        Route("/reference/{slug}/", serve_reference),
        Route("/releases/", serve_release_index),
        Route("/releases/{slug}/", serve_release),
    ]
    static_dir = config.base_dir / "static"
    if static_dir.is_dir():
        routes.append(Mount("/static", app=StaticFiles(directory=static_dir)))
    # Catch-all LAST so the routes above win for their own prefixes.
    routes.append(Route("/{url_path:path}", serve_page))

    app = Starlette(routes=routes)
    citry_instance.set_mounted_prefix(_CITRY_PREFIX)
    return app


# Module-level app for ``uvicorn docs_site._internal.serve:app`` (and the serve command).
app = create_app()
