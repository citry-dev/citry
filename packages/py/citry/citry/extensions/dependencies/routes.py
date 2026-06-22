"""
The dependencies extension's HTTP routes and URL builders.

Four endpoints, mounted at the root of the citry prefix (built-in
extensions own their paths directly; see ``ExtensionManager.urls``)::

    <prefix>/cache/{class_id}.{script_type}                  a class's Component.js / .css
    <prefix>/cache/{class_id}.{vars_hash}.{script_type}      a variables script
    <prefix>/asset/{file_name}                               a served Dependencies file (local_files="serve")
    <prefix>/citry.js                                        the client-side dependency manager

These are what HTML fragments fetch: a fragment carries URLs instead of
inlined tags, so the same component used by many fragments is downloaded
once. Class-level scripts repopulate the cache on a miss (they can always be
rebuilt from the class); variables scripts cannot, which is why multi-worker
deployments that use fragments need a shared cache backend
(docs/design/dependencies.md sections 4.3 and 8.3).

Handlers are framework-neutral (they return ``RouteResponse``); the
``citry.contrib`` adapters translate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from citry.extensions.dependencies.scripts import gen_asset_cache_key, get_component_script, get_script
from citry.util.routing import RouteResponse, URLRoute

if TYPE_CHECKING:
    from typing import Any

    from citry.citry import Citry
    from citry.component import Component
    from citry.extensions.dependencies.types import ScriptType

_CONTENT_TYPES = {"js": "text/javascript", "css": "text/css"}

RUNTIME_PATH = "citry.js"
"""Route path of the client runtime (under the mounted prefix)."""


def script_url(comp_cls: type[Component], script_type: ScriptType, vars_hash: str | None = None) -> str:
    """
    The URL one cached component script is served at.

    Requires a mounted web integration (the URL must point somewhere);
    ``Citry.build_url`` raises with guidance otherwise.
    """
    if vars_hash:
        return comp_cls.citry.build_url(f"cache/{comp_cls.class_id}.{vars_hash}.{script_type}")
    return comp_cls.citry.build_url(f"cache/{comp_cls.class_id}.{script_type}")


def runtime_url(citry: Citry) -> str:
    """The URL the client runtime is served at. Requires a mounted web integration."""
    return citry.build_url(RUNTIME_PATH)


def dependency_routes(citry: Citry) -> list[URLRoute]:
    """The extension's route table, with handlers bound to one ``Citry`` instance."""

    def serve_cached_script(
        request: Any,  # noqa: ARG001 - the adapter's request object; unused
        *,
        class_id: str,
        script_type: str,
        vars_hash: str | None = None,
    ) -> RouteResponse:
        content_type = _CONTENT_TYPES.get(script_type)
        if content_type is None:
            return RouteResponse(status=404)

        try:
            comp_cls = citry.get_component_by_class_id(class_id)
        except KeyError:
            return RouteResponse(status=404)

        if vars_hash is None:
            # Class-level scripts repopulate the cache on a miss.
            script = get_component_script(script_type, comp_cls)  # type: ignore[arg-type]
        else:
            # Variables scripts exist only if the render that produced them
            # wrote to a cache this process can read.
            script = get_script(script_type, comp_cls, vars_hash)  # type: ignore[arg-type]
        if script is None or script.content is None:
            return RouteResponse(status=404)
        return RouteResponse(content=script.content, content_type=content_type)

    def serve_asset(request: Any, *, file_name: str) -> RouteResponse:  # noqa: ARG001 - unused, see above
        content = citry.cache.get(gen_asset_cache_key(file_name))
        if content is None:
            return RouteResponse(status=404)
        extension = file_name.rpartition(".")[2]
        return RouteResponse(content=content, content_type=_CONTENT_TYPES.get(extension, "application/octet-stream"))

    def serve_runtime(request: Any) -> RouteResponse:  # noqa: ARG001 - unused, see above
        # Imported here, not at module load: emission imports this module's
        # sibling helpers, so a top-level import back into it would be
        # circular.
        from citry.extensions.dependencies.emission import _runtime_js  # noqa: PLC0415

        return RouteResponse(content=_runtime_js(), content_type=_CONTENT_TYPES["js"])

    return [
        # Component JS/CSS variables from `Component.js_data()`/`Component.css_data()`,
        # e.g. `cache/abc123.def456.js`.
        # NOTE: The more specific (two-parameter) pattern first: matching is
        # first-wins, and `{class_id}.{script_type}` would also match a
        # vars-script path.
        URLRoute(
            "cache/{class_id}.{vars_hash}.{script_type}",
            handler=serve_cached_script,
            name="citry_cached_script_vars",
        ),
        # Component JS/CSS scripts from `Component.js`/`Component.css`, e.g. `cache/abc123.js`
        URLRoute("cache/{class_id}.{script_type}", handler=serve_cached_script, name="citry_cached_script"),
        # Dependencies extension assets from `Component.dependencies.js/css`, e.g. `asset/abc123.css`
        URLRoute("asset/{file_name}", handler=serve_asset, name="citry_asset"),
        URLRoute(RUNTIME_PATH, handler=serve_runtime, name="citry_client_runtime"),
    ]


__all__ = ["RUNTIME_PATH", "dependency_routes", "runtime_url", "script_url"]
