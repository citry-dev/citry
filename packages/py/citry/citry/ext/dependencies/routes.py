"""
The dependencies extension's HTTP routes and URL builders.

Four endpoints, mounted at the root of the citry prefix (built-in
extensions own their paths directly; see ``ExtensionManager.urls``)::

    <prefix>/cache/{class_id}.{script_type}                  legacy/current class JS or CSS
    <prefix>/cache/{class_id}.{hash}.{script_type}           a class version or variables script
    <prefix>/asset/{file_name}                               a served Dependencies file (local_files="serve")
    <prefix>/citry.js                                        Citry's Vue browser runtime

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

from citry._owned_resource import _OwnedResource
from citry.cache import _forget_stored_key
from citry.ext.dependencies.scripts import (
    component_script_hash,
    gen_asset_cache_key,
    get_cached_component_script,
    get_component_script,
    get_script,
)
from citry.util.routing import RouteResponse, URLRoute

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.component import Component
    from citry.ext.dependencies.types import ScriptType
    from citry.util.routing import RouteRequest

_CONTENT_TYPES = {"js": "text/javascript", "css": "text/css"}
# The script spellings a local file may use. The browser checks the type
# (responses carry X-Content-Type-Options: nosniff), so each must be exact.
_ASSET_CONTENT_TYPES = {"js": "text/javascript", "mjs": "text/javascript", "cjs": "text/javascript", "css": "text/css"}


def asset_content_type(extension: str) -> str:
    """Return the Content-Type for a served local file, from its extension in any case."""
    return _ASSET_CONTENT_TYPES.get(extension.lower(), "application/octet-stream")


# A miss may succeed later, once a worker stores the file, so it is never kept.
_NO_STORE = (("Cache-Control", "no-store"),)

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
    content_hash = component_script_hash(script_type, comp_cls)
    if content_hash is not None:
        return comp_cls.citry.build_url(f"cache/{comp_cls.class_id}.{content_hash}.{script_type}")
    return comp_cls.citry.build_url(f"cache/{comp_cls.class_id}.{script_type}")


def runtime_url(citry: Citry) -> str:
    """The URL the client runtime is served at. Requires a mounted web integration."""
    return citry.build_url(RUNTIME_PATH)


def dependency_routes(citry: Citry) -> list[URLRoute]:
    """The extension's route table, with handlers bound to one ``Citry`` instance."""

    def serve_cached_script(
        request: RouteRequest | None,
        *,
        class_id: str,
        script_type: str,
        vars_hash: str | None = None,
    ) -> RouteResponse:
        content_type = _CONTENT_TYPES.get(script_type)
        if content_type is None:
            return RouteResponse(status=404, headers=_NO_STORE)

        try:
            comp_cls = citry.get_component_by_class_id(class_id)
        except KeyError:
            return RouteResponse(status=404, headers=_NO_STORE)

        # Only a class version's hash is a hash of the bytes served. A
        # variables hash covers the `css_data()` values, while the stylesheet
        # text around them comes from Citry's code and can change on upgrade.
        content_addressed = False
        if vars_hash is None:
            # Class-level scripts repopulate the cache on a miss.
            script = get_component_script(script_type, comp_cls)  # type: ignore[arg-type]
        else:
            # Hashed URLs cover immutable class versions and per-render
            # variables. Check the class-version namespace first; variables
            # retain their existing key scheme and fallback.
            script = get_cached_component_script(citry, class_id, script_type, vars_hash)  # type: ignore[arg-type]
            content_addressed = script is not None
            if script is None:
                current_hash = component_script_hash(script_type, comp_cls)  # type: ignore[arg-type]
                if current_hash == vars_hash:
                    script = get_cached_component_script(citry, class_id, script_type, vars_hash)  # type: ignore[arg-type]
                    content_addressed = script is not None
                else:
                    script = get_script(script_type, comp_cls, vars_hash)  # type: ignore[arg-type]
        if script is None or script.content is None:
            # A later request may find the file (another worker stores it),
            # so neither the browser nor a CDN may keep this answer.
            return RouteResponse(status=404, headers=_NO_STORE)
        resource = _OwnedResource(url="", content=script.content, content_type=content_type)
        if content_addressed:
            # The bytes at this URL never change.
            return resource.immutable_response()
        # `cache/<class_id>.js` serves whatever the class holds now, and a
        # variables stylesheet's text can change with Citry, so the browser
        # must check either one is current before each use.
        return resource.revalidated_response(request)

    def serve_asset(request: RouteRequest | None, *, file_name: str) -> RouteResponse:  # noqa: ARG001 - unused
        key = gen_asset_cache_key(file_name)
        content = citry.cache.get(key)
        if content is None:
            # This process's next render that links this file writes it again
            # instead of trusting its record that it is stored.
            _forget_stored_key(citry, key)
            return RouteResponse(status=404, headers=_NO_STORE)
        extension = file_name.rpartition(".")[2]
        # The file name is the hash of its content (see `cache_asset`).
        return _OwnedResource(
            url="",
            content=content,
            content_type=asset_content_type(extension),
        ).immutable_response()

    def serve_runtime(request: RouteRequest | None) -> RouteResponse:
        # Imported here, not at module load: emission imports this module's
        # sibling helpers, so a top-level import back into it would be
        # circular.
        from citry.ext.dependencies.emission import _runtime_resource  # noqa: PLC0415

        # `citry.js` keeps its URL across Citry upgrades, so the browser
        # must check it is current before each use.
        return _runtime_resource(citry).revalidated_response(request)

    return [
        # Content-addressed Component.js/css and the variables stylesheet
        # from `Component.css_data()`, e.g. `cache/abc123.def456.js`.
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
