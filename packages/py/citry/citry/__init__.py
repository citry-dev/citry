# citry - Fast, simple, and smart frontend framework for Python
#
# This package provides the rendering runtime for Citry templates:
# component lifecycle, slots, rendering pipeline, and the node classes
# that the V3 compiler output instantiates.
#
# For the Rust-powered parser and compiler, see citry_core.
#
# API stability: the names exported HERE (listed in __all__) are the public
# API, and only these are promised not to break between releases. Submodules
# (citry.slots, citry.nodes, ...) may be imported from, but their contents
# are internal and free to change between releases.

from citry.attrs import (
    format_attrs,
    merge_attrs,
    normalize_class,
    normalize_style,
    parse_string_style,
)
from citry.cache import CitryCache, InMemoryCache
from citry.citry import (
    Citry,
    citry,
)
from citry.citry_context import CitryContext
from citry.citry_element import CitryElement
from citry.citry_render import (
    CitryRender,
    DepsPosition,
    DepsStrategy,
    OnRenderGenerator,
    Placeholder,
    RenderFrame,
    RenderReplacement,
)
from citry.citry_template import CitryTemplate
from citry.command import CommandArg, CommandArgGroup, CommandSubcommand
from citry.component import Component
from citry.component_like import ComponentLike
from citry.component_registry import AlreadyRegistered, NotRegistered
from citry.constness import Const
from citry.ext.events.config import Events
from citry.extension import (
    ComponentIntrospectionContext,
    Extension,
    ExtensionCommand,
    ExtensionConfig,
    ExtensionManager,
    NestedClassDeclaration,
    OnAttrsResolvedContext,
    OnComponentClassCreatedContext,
    OnComponentDataContext,
    OnComponentInputContext,
    OnComponentRegisteredContext,
    OnComponentRenderedContext,
    OnComponentUnregisteredContext,
    OnCssLoadedContext,
    OnExtensionCreatedContext,
    OnFilesResetContext,
    OnJsLoadedContext,
    OnRenderContextMergeContext,
    OnSerializeContext,
    OnSlotRenderedContext,
    OnTemplateCompiledContext,
    OnTemplateLoadedContext,
    OnTemplateResetContext,
)
from citry.introspection import (
    AssetInfo,
    ComponentAssets,
    ComponentCatalog,
    ComponentExtensionInfo,
    ComponentInfo,
    ComponentIntrospectionError,
    ComponentSchemas,
    ExtensionVersion,
    FieldInfo,
    FrozenJsonObject,
    FrozenJsonValue,
    SchemaInfo,
)
from citry.library_component import (
    ComponentLibrary,
    LibraryComponent,
    LibraryComponentContextError,
    LibraryComponentInvocation,
    LibraryInstallation,
    LibraryInstallationStale,
    LibraryManifestChanged,
    LibraryNotInstalled,
)
from citry.lifecycle import CitryLifecycleInProgress
from citry.nodes import (
    ComponentNode,
    ElementAttrsNode,
    ExprHtmlAttr,
    ExprNode,
    FillNode,
    ForNode,
    HtmlAttr,
    IfNode,
    Node,
    SlotNode,
    StaticHtmlAttr,
    TemplateHtmlAttr,
    TemplateNode,
)
from citry.settings import CitrySettings
from citry.slots import (
    Slot,
    SlotContext,
    SlotData,
    SlotFunc,
    SlotInput,
    SlotResult,
)
from citry.util.routing import RouteHeaders, RouteRequest, RouteResponse, URLRoute

__all__ = [
    "AlreadyRegistered",
    "AssetInfo",
    "Citry",
    "CitryCache",
    "CitryContext",
    "CitryElement",
    "CitryLifecycleInProgress",
    "CitryRender",
    "CitrySettings",
    "CitryTemplate",
    "CommandArg",
    "CommandArgGroup",
    "CommandSubcommand",
    "Component",
    "ComponentAssets",
    "ComponentCatalog",
    "ComponentExtensionInfo",
    "ComponentInfo",
    "ComponentIntrospectionContext",
    "ComponentIntrospectionError",
    "ComponentLibrary",
    "ComponentLike",
    "ComponentNode",
    "ComponentSchemas",
    "Const",
    "DepsPosition",
    "DepsStrategy",
    "ElementAttrsNode",
    "Events",
    "ExprHtmlAttr",
    "ExprNode",
    "Extension",
    "ExtensionCommand",
    "ExtensionConfig",
    "ExtensionManager",
    "ExtensionVersion",
    "FieldInfo",
    "FillNode",
    "ForNode",
    "FrozenJsonObject",
    "FrozenJsonValue",
    "HtmlAttr",
    "IfNode",
    "InMemoryCache",
    "LibraryComponent",
    "LibraryComponentContextError",
    "LibraryComponentInvocation",
    "LibraryInstallation",
    "LibraryInstallationStale",
    "LibraryManifestChanged",
    "LibraryNotInstalled",
    "NestedClassDeclaration",
    "Node",
    "NotRegistered",
    "OnAttrsResolvedContext",
    "OnComponentClassCreatedContext",
    "OnComponentDataContext",
    "OnComponentInputContext",
    "OnComponentRegisteredContext",
    "OnComponentRenderedContext",
    "OnComponentUnregisteredContext",
    "OnCssLoadedContext",
    "OnExtensionCreatedContext",
    "OnFilesResetContext",
    "OnJsLoadedContext",
    "OnRenderContextMergeContext",
    "OnRenderGenerator",
    "OnSerializeContext",
    "OnSlotRenderedContext",
    "OnTemplateCompiledContext",
    "OnTemplateLoadedContext",
    "OnTemplateResetContext",
    "Placeholder",
    "RenderFrame",
    "RenderReplacement",
    "RouteHeaders",
    "RouteRequest",
    "RouteResponse",
    "SchemaInfo",
    "Slot",
    "SlotContext",
    "SlotData",
    "SlotFunc",
    "SlotInput",
    "SlotNode",
    "SlotResult",
    "StaticHtmlAttr",
    "TemplateHtmlAttr",
    "TemplateNode",
    "URLRoute",
    "citry",
    "format_attrs",
    "merge_attrs",
    "normalize_class",
    "normalize_style",
    "parse_string_style",
]
