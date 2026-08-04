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

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import FileResponse, HTMLResponse, PlainTextResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from citry import citry as default_citry
from citry.contrib.asgi import asgi_app
from docs_site._internal.blog import BlogCatalog, BlogPost, load_blog_catalog, serialize_atom_feed
from docs_site._internal.build import configure_docs_globals
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.examples import get_example_by_slug
from docs_site._internal.local_playground_runtime import (
    LocalPlaygroundRuntime,
    build_local_playground_runtime,
)
from docs_site._internal.paths import md_to_url, url_to_md
from docs_site._internal.pipeline import render_page
from docs_site._internal.project import load_docs_project, use_docs_project
from docs_site._internal.reference_pages import (
    reference_index_markdown,
    reference_page_markdown,
    validate_authored_reference_sources,
)
from docs_site._internal.release_notes import (
    Release,
    parse_changelog,
    release_index_markdown,
    release_page_markdown,
)
from docs_site._internal.site_nav import load_site_nav

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.types import ASGIApp, Receive, Scope, Send

    from citry import Citry
    from docs_site._internal.project import DocsProject

# Where citry's component-asset routes are mounted (and recorded on the instance
# so any emitted asset URLs point at the right place).
_CITRY_PREFIX = "/citry"


class _DocsProjectMiddleware:
    """Keep the app's validated project active for every request handler."""

    def __init__(self, app: ASGIApp, *, project: DocsProject) -> None:
        self.app = app
        self.project = project

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        with use_docs_project(self.project):
            await self.app(scope, receive, send)


def create_app(
    *,
    config: DocsConfig | None = None,
    citry_instance: Citry | None = None,
    local_playground_runtime: LocalPlaygroundRuntime | None = None,
) -> Starlette:
    """Build the docs dev-server app for ``config`` (defaults to the module config)."""
    config = config or default_config
    project = load_docs_project(config)
    config = project.runtime
    settings = project.settings
    feed_path = settings.blog.feed_path
    if (config.content_dir / "_nav.yml").is_file():
        from docs_site._internal.nav import load_nav  # noqa: PLC0415

        if load_nav(config.content_dir / "_nav.yml").has_source("reference"):
            validate_authored_reference_sources(project.reference, config.content_dir)
    citry_instance = citry_instance or default_citry
    # Set the version / site-name template globals once so {{ version }} resolves
    # in live-rendered pages, the same as the static build does.
    version = configure_docs_globals(project)

    async def serve_page(request: Request) -> HTMLResponse | PlainTextResponse:
        catalog = load_blog_catalog(config.content_dir)
        md_path = url_to_md(config.content_dir, request.path_params.get("url_path", ""))
        if md_path is None:
            return PlainTextResponse("Not Found", status_code=404)
        # Dated Blog filenames are authoring identities, never public aliases.
        # The explicit slug route below is the only route that serves a post.
        if catalog.post_for_source(md_path) is not None:
            return PlainTextResponse("Not Found", status_code=404)
        requested = request.path_params.get("url_path", "").strip("/")
        if (
            catalog.index_path is not None
            and md_path.resolve() == catalog.index_path.resolve()
            and requested != "blog"
        ):
            return PlainTextResponse("Not Found", status_code=404)
        return _render_content_page(md_path, catalog=catalog)

    def _render_content_page(
        md_path: Path,
        *,
        catalog: BlogCatalog | None = None,
        blog_post: BlogPost | None = None,
    ) -> HTMLResponse:
        """Render one authored Markdown page with build-equivalent metadata."""
        catalog = catalog or load_blog_catalog(config.content_dir)
        # Canonical and current_path match what the build would write, so a
        # preview matches the deployed page.
        page_url = (
            blog_post.public_path.lstrip("/")
            if blog_post
            else md_to_url(md_path.relative_to(config.content_dir.resolve()))
        )
        site_base = project.site_url.rstrip("/")
        canonical = f"{site_base}/{page_url}" if site_base else ""
        # Load the nav fresh each request so edits to _nav.yml show up live.
        result = render_page(
            md_path.read_text(encoding="utf-8"),
            config=config,
            canonical=canonical,
            nav_tree=load_site_nav(config, project=project, blog_catalog=catalog),
            current_path=page_url,
            version=version,
            source_path=md_path,
            blog_catalog=catalog,
            blog_post=blog_post,
            is_blog_index=catalog.index_path is not None and md_path.resolve() == catalog.index_path.resolve(),
            blog_feed_url=feed_path if catalog.posts else "",
            allow_citry_ui=local_playground_runtime is not None,
            project=project,
        )
        return HTMLResponse(result.html)

    async def serve_blog_post(request: Request) -> HTMLResponse | PlainTextResponse:
        catalog = load_blog_catalog(config.content_dir)
        post = catalog.post_for_public_path(f"/blog/{request.path_params['slug']}/")
        if post is None:
            return PlainTextResponse("Not Found", status_code=404)
        return _render_content_page(post.source_path, catalog=catalog, blog_post=post)

    async def serve_blog_feed(request: Request) -> Response | PlainTextResponse:
        catalog = load_blog_catalog(config.content_dir)
        xml = serialize_atom_feed(
            catalog,
            site_url=str(request.base_url).rstrip("/"),
            base_path=config.base_path,
            feed_path=feed_path,
            feed_limit=settings.blog.feed_limit,
        )
        if not xml:
            return PlainTextResponse("Not Found", status_code=404)
        return Response(xml, media_type="application/atom+xml")

    async def serve_example(request: Request) -> HTMLResponse | PlainTextResponse:
        # The standalone live-demo page an example card's iframe loads.
        info = get_example_by_slug(request.path_params["slug"])
        if info is None:
            return PlainTextResponse("Not Found", status_code=404)
        return HTMLResponse(str(info.page_cls()))

    async def serve_example_variant(request: Request) -> HTMLResponse | PlainTextResponse:
        # A fragment example serves each variant on its own endpoint, the way the
        # static build pre-renders it below examples/<slug>/demo/. Rendering the
        # fragment here also caches its script, so the /citry mount then serves
        # the fragment's JS/CSS (the dev-server counterpart to
        # export_fragment_deps).
        info = get_example_by_slug(request.path_params["slug"])
        if info is None:
            return PlainTextResponse("Not Found", status_code=404)
        variant = info.fragments.get(request.path_params["variant"])
        if variant is None:
            return PlainTextResponse("Not Found", status_code=404)
        return HTMLResponse(variant().render().serialize(deps_strategy="fragment"))

    def _render_reference(page_url: str, source: str) -> HTMLResponse:
        catalog = load_blog_catalog(config.content_dir)
        site_base = project.site_url.rstrip("/")
        canonical = f"{site_base}/{page_url}" if site_base else ""
        html = render_page(
            source,
            config=config,
            canonical=canonical,
            nav_tree=load_site_nav(config, project=project, blog_catalog=catalog),
            current_path=page_url,
            version=version,
            blog_catalog=catalog,
            blog_feed_url=feed_path if catalog.posts else "",
            allow_citry_ui=local_playground_runtime is not None,
            project=project,
        ).html
        return HTMLResponse(html)

    async def serve_reference_index(request: Request) -> HTMLResponse:  # noqa: ARG001
        return _render_reference("reference/", reference_index_markdown(project.reference))

    async def serve_reference(request: Request) -> HTMLResponse | PlainTextResponse:
        cat = project.reference.category(request.path_params["slug"])
        if cat is None:
            return PlainTextResponse("Not Found", status_code=404)
        if cat.authored:
            md_path = url_to_md(config.content_dir, f"reference/{cat.slug}/")
            if md_path is None:
                return PlainTextResponse("Not Found", status_code=404)
            return _render_content_page(md_path)
        return _render_reference(f"reference/{cat.slug}/", reference_page_markdown(cat))

    def _changelog_releases() -> list[Release]:
        changelog = config.repo_root / "CHANGELOG.md"
        if not changelog.is_file():
            return []
        return parse_changelog(
            changelog.read_text(encoding="utf-8"),
            exclude=settings.excluded_releases,
        )

    def _render_release(page_url: str, source: str) -> HTMLResponse:
        catalog = load_blog_catalog(config.content_dir)
        site_base = project.site_url.rstrip("/")
        canonical = f"{site_base}/{page_url}" if site_base else ""
        # run_citry_pass=False: release prose shows citry syntax as text (see build).
        html = render_page(
            source,
            config=config,
            canonical=canonical,
            nav_tree=load_site_nav(config, project=project, blog_catalog=catalog),
            current_path=page_url,
            version=version,
            run_citry_pass=False,
            blog_catalog=catalog,
            blog_feed_url=feed_path if catalog.posts else "",
            project=project,
        ).html
        return HTMLResponse(html)

    async def serve_release_index(
        request: Request,  # noqa: ARG001
    ) -> HTMLResponse | PlainTextResponse:
        if not (config.repo_root / "CHANGELOG.md").is_file():
            return PlainTextResponse("Not Found", status_code=404)
        return _render_release("releases/", release_index_markdown(_changelog_releases()))

    async def serve_release(request: Request) -> HTMLResponse | PlainTextResponse:
        slug = request.path_params["slug"]
        release = next((r for r in _changelog_releases() if r.slug == slug), None)
        if release is None:
            return PlainTextResponse("Not Found", status_code=404)
        return _render_release(f"releases/{release.slug}/", release_page_markdown(release))

    routes: list[Route | Mount] = []
    if local_playground_runtime is not None:

        async def serve_local_runtime(request: Request) -> FileResponse:  # noqa: ARG001
            return FileResponse(
                local_playground_runtime.manifest_path,
                media_type="application/json",
                headers={"Cache-Control": "no-store"},
            )

        async def serve_local_events_runtime(request: Request) -> FileResponse:  # noqa: ARG001
            return FileResponse(
                local_playground_runtime.events_runtime_path,
                media_type="text/javascript",
                headers={"Cache-Control": "no-store"},
            )

        async def serve_local_wheel(request: Request) -> FileResponse | PlainTextResponse:
            filename = request.path_params["filename"]
            if filename not in local_playground_runtime.wheel_names:
                return PlainTextResponse("Not Found", status_code=404)
            return FileResponse(
                local_playground_runtime.directory / "local" / filename,
                media_type="application/zip",
                headers={"Cache-Control": "no-store"},
            )

        routes.extend(
            [
                Route("/static/playground/runtime.json", serve_local_runtime),
                Route("/static/playground/citry-events.js", serve_local_events_runtime),
                Route("/static/playground/local/{filename}", serve_local_wheel),
            ]
        )
    routes.extend(
        [
            Mount(_CITRY_PREFIX, app=asgi_app(citry_instance)),
            # Before the catch-all: example demos and Reference routes need custom
            # handling. Authored Reference categories delegate back to content.
            Route("/examples/{slug}/demo/", serve_example),
            Route("/examples/{slug}/demo/{variant}/", serve_example_variant),
            Route(feed_path, serve_blog_feed),
            Route("/blog/{slug}/", serve_blog_post),
            Route("/reference/", serve_reference_index),
            Route("/reference/{slug}/", serve_reference),
            Route("/releases/", serve_release_index),
            Route("/releases/{slug}/", serve_release),
        ]
    )
    static_dir = config.base_dir / "static"
    if static_dir.is_dir():
        routes.append(Mount("/static", app=StaticFiles(directory=static_dir)))
    # Catch-all LAST so the routes above win for their own prefixes.
    routes.append(Route("/{url_path:path}", serve_page))

    app = Starlette(
        routes=routes,
        middleware=[Middleware(_DocsProjectMiddleware, project=project)],
    )

    citry_instance.set_mounted_prefix(_CITRY_PREFIX)
    return app


def create_local_app() -> Starlette:
    """Build workspace browser wheels and create the live authoring app."""
    owner = tempfile.TemporaryDirectory(prefix="citry-docs-playground-")
    print("Building local Citry and Citry UI wheels for the browser playground...")
    local_runtime = build_local_playground_runtime(
        repo_root=default_config.repo_root,
        output_dir=Path(owner.name),
    )
    local_app = create_app(local_playground_runtime=local_runtime)
    # Keep the generated wheel directory alive for as long as the ASGI app.
    local_app.state.local_playground_runtime_owner = owner
    print("Local browser runtime ready: " + ", ".join(sorted(local_runtime.wheel_names)))
    return local_app


# Plain module-level app for ASGI imports that want the committed runtime.
app = create_app()
