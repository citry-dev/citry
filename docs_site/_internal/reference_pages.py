"""
The API-reference categories: which public symbols go on which page.

Re-derived from ``citry.__all__`` (not DJC's Django-shaped pages). Each category
becomes one ``/reference/<slug>/`` page whose markdown is a heading plus a
``<c-docstring />`` per symbol (or ``<c-builtin />`` for the dynamically created
built-in tags). The build renders these pages through the normal pipeline, and
``reference_nav_section`` adds them to the sidebar.
"""

from __future__ import annotations

from dataclasses import dataclass

from docs_site._internal.nav import NavItem, NavSection


@dataclass
class Category:
    slug: str
    title: str
    intro: str
    symbols: list[str]
    # "griffe" symbols are dotted paths resolved by <c-docstring>; "builtin"
    # symbols are tag names introspected from the registry by <c-builtin>.
    source: str = "griffe"


# The 17 root-exported extension hook-context objects all live on the one
# Extensions page. The dependencies extension's own hook context
# (OnDependenciesContext) lives on the Dependencies page with its extension.
_HOOK_CONTEXTS = [
    "citry.OnAttrsResolvedContext",
    "citry.OnComponentClassCreatedContext",
    "citry.OnComponentDataContext",
    "citry.OnComponentInputContext",
    "citry.OnComponentRegisteredContext",
    "citry.OnComponentRenderedContext",
    "citry.OnComponentUnregisteredContext",
    "citry.OnCssLoadedContext",
    "citry.OnExtensionCreatedContext",
    "citry.OnFilesResetContext",
    "citry.OnJsLoadedContext",
    "citry.OnRenderContextMergeContext",
    "citry.OnSerializeContext",
    "citry.OnSlotRenderedContext",
    "citry.OnTemplateCompiledContext",
    "citry.OnTemplateLoadedContext",
    "citry.OnTemplateResetContext",
]

CATEGORIES: list[Category] = [
    Category("component", "Component", "The base class every component subclasses.", ["citry.Component"]),
    Category(
        "component-introspection",
        "Component introspection",
        "Frozen metadata records for component catalogs, schemas, assets, and extensions.",
        [
            "citry.ComponentCatalog",
            "citry.ComponentInfo",
            "citry.ComponentIntrospectionContext",
            "citry.ComponentIntrospectionError",
            "citry.ComponentSchemas",
            "citry.SchemaInfo",
            "citry.FieldInfo",
            "citry.FrozenJsonObject",
            "citry.FrozenJsonValue",
            "citry.ComponentAssets",
            "citry.AssetInfo",
            "citry.ExtensionVersion",
            "citry.ComponentExtensionInfo",
            "citry.NestedClassDeclaration",
        ],
    ),
    Category(
        "component-libraries",
        "Component libraries",
        "Engine-neutral component definitions, explicit manifests, and per-Citry installations.",
        [
            "citry.ComponentLibrary",
            "citry.LibraryComponent",
            "citry.LibraryComponentInvocation",
            "citry.LibraryInstallation",
            "citry.ComponentLike",
            "citry.LibraryComponentContextError",
            "citry.LibraryInstallationStale",
            "citry.LibraryManifestChanged",
            "citry.LibraryNotInstalled",
        ],
    ),
    Category(
        "citry",
        "Citry instance and config",
        "The `Citry` instance that scopes components, settings, and caches.",
        [
            "citry.Citry",
            "citry.citry",
            "citry.AlreadyRegistered",
            "citry.NotRegistered",
            "citry.CitryLifecycleInProgress",
            "citry.CitrySettings",
            "citry.CitryCache",
            "citry.InMemoryCache",
        ],
    ),
    Category(
        "rendering",
        "Rendering",
        "The three-phase render pipeline and its output structs.",
        [
            "citry.CitryElement",
            "citry.CitryRender",
            "citry.CitryContext",
            "citry.CitryTemplate",
            "citry.Placeholder",
            "citry.RenderReplacement",
            "citry.RenderFrame",
            "citry.OnRenderGenerator",
            "citry.DepsStrategy",
            "citry.DepsPosition",
            "citry.Const",
        ],
    ),
    Category(
        "slots",
        "Slots",
        "The slot value and fill types.",
        [
            "citry.Slot",
            "citry.SlotContext",
            "citry.SlotData",
            "citry.SlotFunc",
            "citry.SlotInput",
            "citry.SlotResult",
        ],
    ),
    Category(
        "nodes",
        "Nodes",
        "The runtime node classes the compiled template instantiates.",
        [
            "citry.Node",
            "citry.ComponentNode",
            "citry.ElementAttrsNode",
            "citry.ExprNode",
            "citry.ForNode",
            "citry.IfNode",
            "citry.SlotNode",
            "citry.FillNode",
            "citry.TemplateNode",
            "citry.HtmlAttr",
            "citry.ExprHtmlAttr",
            "citry.StaticHtmlAttr",
            "citry.TemplateHtmlAttr",
        ],
    ),
    Category(
        "extensions",
        "Extensions",
        "The plugin system: the extension base, its commands, and the hook context objects.",
        [
            "citry.Extension",
            "citry.ExtensionConfig",
            "citry.ExtensionManager",
            "citry.ExtensionCommand",
            "citry.ext.debug.Debug",
            "citry.CommandArg",
            "citry.CommandArgGroup",
            "citry.CommandSubcommand",
            *_HOOK_CONTEXTS,
        ],
    ),
    Category(
        "dependencies",
        "Dependencies",
        "The JS/CSS dependency types collected and placed at serialize time, "
        "and the built-in `citry.ext.dependencies` extension that owns them.",
        [
            "citry.ext.dependencies.CitryDependencies",
            "citry.ext.dependencies.Dependency",
            "citry.ext.dependencies.DependencyRecord",
            "citry.ext.dependencies.Script",
            "citry.ext.dependencies.Style",
            "citry.ext.dependencies.DependenciesExtension",
            "citry.ext.dependencies.OnDependenciesContext",
            "citry.ext.dependencies.get_dependencies",
        ],
    ),
    Category(
        "cache-keys",
        "Render cache keys",
        "Exact key helpers and errors for component and named-fragment render caches.",
        [
            "citry.ext.cache.CacheKeyError",
            "citry.ext.cache.OnComponentCacheHitContext",
            "citry.ext.cache.component_cache_key",
            "citry.ext.cache.fragment_cache_key",
        ],
    ),
    Category(
        "events",
        "Events",
        "Event handlers declared on components: the `class Events:` contract, "
        "the typed base for it, and the built-in `citry.ext.events` extension that owns it.",
        [
            "citry.Events",
            "citry.ext.events.X_CITRY_EVENTS_HEADER",
            "citry.ext.events.CallEvent",
            "citry.ext.events.EventError",
            "citry.ext.events.EventRequest",
            "citry.ext.events.EventsDispatcher",
            "citry.ext.events.EventsExtension",
            "citry.ext.events.TransportContext",
            "citry.ext.events.UploadedFile",
            "citry.ext.events.ViewEvents",
            "citry.ext.events.actions",
            "citry.ext.events.actions.Action",
            "citry.ext.events.actions.Render",
            "citry.ext.events.actions.Data",
            "citry.ext.events.actions.Dispatch",
            "citry.ext.events.actions.Redirect",
            "citry.ext.events.actions.PushUrl",
            "citry.ext.events.actions.ReplaceUrl",
            "citry.ext.events.actions.Download",
            "citry.ext.events.event",
            "citry.ext.events.get_event_url",
        ],
    ),
    Category(
        "attributes",
        "HTML attributes",
        "Helpers for Vue-like class/style merging on HTML elements.",
        [
            "citry.format_attrs",
            "citry.merge_attrs",
            "citry.normalize_class",
            "citry.normalize_style",
            "citry.parse_string_style",
        ],
    ),
    Category(
        "web",
        "Web integration",
        "The route table a web framework mounts, and the request/response types handlers use (see `citry.contrib`).",
        ["citry.URLRoute", "citry.RouteRequest", "citry.RouteResponse", "citry.RouteHeaders"],
    ),
    Category(
        "contrib",
        "Contrib integrations",
        "Adapters mounting citry into web frameworks, and cache adapters for shared stores "
        "(the `citry.contrib.<name>` modules).",
        [
            "citry.contrib.fastapi.mount",
            "citry.contrib.flask.mount",
            "citry.contrib.django.urlpatterns",
            "citry.contrib.django.enable_hot_reload",
            "citry.contrib.django.secret",
            "citry.contrib.django.DjangoCache",
            "citry.contrib.asgi.asgi_app",
            "citry.contrib.asgi.reload_lifespan",
            "citry.contrib.wsgi.wsgi_app",
            "citry.contrib.caches.RedisCache",
            "citry.contrib.caches.DiskCache",
        ],
    ),
    Category(
        "builtins",
        "Built-in components",
        "The built-in `<c-*>` tags every component can use.",
        ["component", "element", "provide", "cache", "js", "css", "error-fallback"],
        source="builtin",
    ),
]

_BY_SLUG = {c.slug: c for c in CATEGORIES}


def category(slug: str) -> Category | None:
    """The category with this slug, or ``None``."""
    return _BY_SLUG.get(slug)


def reference_page_markdown(cat: Category) -> str:
    """Markdown for one category page: a heading and a directive per symbol."""
    directive = "c-builtin tag" if cat.source == "builtin" else "c-docstring path"
    lines = [f"# {cat.title}", "", cat.intro, ""]
    for symbol in cat.symbols:
        lines.append(f'<{directive}="{symbol}" />')
        lines.append("")
    return "\n".join(lines) + "\n"


def reference_index_markdown() -> str:
    """Markdown for the ``/reference/`` landing page (a list of the categories)."""
    lines = ["# API reference", "", "The citry public API, by area.", ""]
    lines.extend(f"- [{c.title}](/reference/{c.slug}/) - {c.intro}" for c in CATEGORIES)
    return "\n".join(lines) + "\n"


def reference_nav_section() -> NavSection:
    """The sidebar section linking every reference category page."""
    items = [NavItem(title="Overview", path="/reference/")]
    items += [NavItem(title=c.title, path=f"/reference/{c.slug}/") for c in CATEGORIES]
    return NavSection(label="Reference", items=items)
