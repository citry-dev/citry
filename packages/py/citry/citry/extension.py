"""
The extension (plugin) system.

Extensions let third-party code (and citry's own subsystems, such as the
built-in JS/CSS dependency handling) hook into the component lifecycle without
touching the core. An extension is a subclass of :class:`Extension` that
implements one or more ``on_*`` hook methods and, optionally, exposes a
per-component nested config class (the ``Component.View`` / ``Component.Cache``
mechanism), HTTP routes (``Extension.urls``), and CLI commands.

Extensions are scoped to a :class:`~citry.citry.Citry` instance (per DJC #1413,
all engine state lives on the ``Citry`` instance). Pass them at construction::

    from citry import Citry, Component, Extension

    class TimingExtension(Extension):
        name = "timing"

        def on_component_rendered(self, ctx):
            print(f"{type(ctx.component).__name__} rendered")

    app = Citry(extensions=[TimingExtension])

The full design, the hook catalog, and the divergences from django-components
are in ``docs/design/extensions.md``. It wires the lifecycle, registration,
render, template, slot, JS/CSS, merge (``on_render_context_merge``), and
serialize hooks, plus the ``emit`` mechanism for extension-owned custom hooks
(the dependencies extension's ``on_dependencies`` and the cache extension's
``on_component_cache_hit``).
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass, replace
from importlib import import_module
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast
from weakref import ReferenceType, WeakSet, ref

from citry._nested_declarations import (
    NestedClassDeclaration,
    _compose_nested_declaration_class,
    _get_nested_class_declarations,
)
from citry.introspection import (
    ComponentExtensionInfo,
    ComponentInfo,
    ComponentIntrospectionError,
    ExtensionVersion,
    _freeze_extension_publication,
)
from citry.settings import LintSettings
from citry.util.misc import snake_to_pascal

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from citry._javascript_policy import _JavascriptPolicy
    from citry._serialization_security import _ScriptSecurityMaterializer
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.citry_render import CitryRender, RenderPart
    from citry.command import CommandArg, CommandArgGroup, CommandHandler, CommandSubcommand
    from citry.component import Component
    from citry.nodes import BodyItem, SlotNode
    from citry.ownership_manifest import OwnershipManifestArtifact
    from citry.settings import SecurityCspMode, SecurityJavascriptMode
    from citry.slots import Slot
    from citry.util.routing import URLRoute


################################################
# HOOK CONTEXTS
#
# Frozen dataclasses, consistent with citry's metaclass (which
# converts inner Kwargs/Slots to dataclasses); threaded across extensions with
# ``dataclasses.replace``. The surface is minimal: contexts carry ``citry`` plus,
# when a component instance exists, ``component``. Fields trivially derivable
# from those (component class, component id, registry) are not duplicated.
# See docs/design/extensions.md section 3.
################################################


@dataclass(frozen=True, slots=True)
class OnExtensionCreatedContext:
    citry: Citry
    """The ``Citry`` instance the extension belongs to."""
    extension: Extension
    """The created extension instance."""


@dataclass(frozen=True, slots=True)
class ComponentIntrospectionContext:
    """
    Give one extension the inputs for an explicitly requested metadata query.

    The component class is temporary live runtime state. Inspectors publish
    copied JSON metadata and must not retain this context or the class.

    Attributes:
        citry: The owning Citry instance.
        component_class: The live class from the query's copied registry
            snapshot.
        info: The complete core metadata record, with no extension entries.

    """

    citry: Citry
    """The ``Citry`` instance being inspected."""
    component_class: type[Component]
    """The temporary live component class from the copied registry snapshot."""
    info: ComponentInfo
    """The already-built core metadata record, with no extension entries."""


@dataclass(frozen=True, slots=True)
class TemplateNamespaceContext:
    """Give an extension one component whose template namespace it can describe."""

    citry: Citry
    """The owning Citry instance."""
    component_class: type[Component]
    """The temporary live component class from the registry snapshot."""


@dataclass(frozen=True, slots=True)
class TemplateNamespaceContribution:
    """
    Publish analysis-only variables added by one installed extension.

    Attributes:
        template_variables: Variable names mapped to annotations, using the
            same format as [`LintSettings.template_variables`][citry.LintSettings.template_variables].
        allows_extra_variables: Whether this extension intentionally preserves
            additional names that it cannot enumerate. Such unknown names are
            linted as warnings, never silently accepted.

    """

    template_variables: Mapping[str, object]
    allows_extra_variables: bool = False

    def __post_init__(self) -> None:
        validated = LintSettings(template_variables=self.template_variables)
        object.__setattr__(self, "template_variables", validated.template_variables)
        if type(self.allows_extra_variables) is not bool:
            msg = "TemplateNamespaceContribution.allows_extra_variables must be a bool"
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class OnComponentClassCreatedContext:
    citry: Citry
    """The ``Citry`` instance the component class belongs to."""
    component_class: type[Component]
    """The created Component class."""

    def nested_declarations(self, name: str) -> tuple[NestedClassDeclaration, ...]:
        """
        Return the exact authored bindings for ``name`` in component C3 order.

        A record whose value is ``None`` is an explicit reset, distinct from
        the name being absent. The classes are the original source objects,
        even after Citry replaces the component attribute with an effective
        runtime config class.

        Args:
            name: The nested declaration name, usually the extension's
                [`class_name`][citry.Extension.class_name].

        Returns:
            The declarations from the component through its bases in C3 order.

        """
        return _get_nested_class_declarations(self.component_class, name)


@dataclass(frozen=True, slots=True)
class OnComponentRegisteredContext:
    citry: Citry
    """The ``Citry`` instance the component was registered with."""
    name: str
    """The name the component was registered under."""
    component_class: type[Component]
    """The registered Component class."""


@dataclass(frozen=True, slots=True)
class OnComponentUnregisteredContext:
    citry: Citry
    """The ``Citry`` instance the component was unregistered from."""
    name: str
    """The name the component was registered under."""
    component_class: type[Component]
    """The unregistered Component class."""


@dataclass(frozen=True, slots=True)
class OnComponentInputContext:
    citry: Citry
    """The ``Citry`` instance the component belongs to."""
    component: Component
    """The Component instance being rendered."""
    kwargs: dict[str, Any]
    """The keyword arguments passed to the component (mutable plain dict)."""
    slots: dict[str, Any]
    """The slot fills passed to the component (mutable plain dict)."""


@dataclass(frozen=True, slots=True)
class OnComponentDataContext:
    citry: Citry
    """The ``Citry`` instance the component belongs to."""
    component: Component
    """The Component instance being rendered."""
    context: CitryContext
    """The render-scoped ``CitryContext`` for this component's render.
    Extensions stash tree-wide state in ``context.extra`` (for example the
    dependencies extension's render records); it bubbles up through
    ``on_render_context_merge`` as nested renders are consumed. ``context.provides``
    is not yet populated when this hook fires."""
    template_data: dict[str, Any]
    """The template variables from ``Component.template_data()`` (mutable)."""
    js_data: dict[str, Any]
    """The JS variables from ``Component.js_data()`` (mutable). Consumed by
    the built-in ``dependencies`` extension."""
    css_data: dict[str, Any]
    """The CSS variables from ``Component.css_data()`` (mutable). Consumed by
    the built-in ``dependencies`` extension."""


@dataclass(frozen=True, slots=True)
class OnComponentRenderedContext:
    citry: Citry
    """The ``Citry`` instance the component belongs to."""
    component: Component
    """The Component instance that was rendered."""
    render: CitryRender | str | None
    """The rendered output, or ``None`` if rendering failed."""
    error: Exception | None
    """The error raised during rendering, or ``None`` if it succeeded."""


@dataclass(frozen=True, slots=True)
class OnSlotRenderedContext:
    citry: Citry
    """The ``Citry`` instance the component belongs to."""
    component: Component
    """The component whose template holds the ``<c-slot>`` that was rendered."""
    slot: Slot
    """The Slot that was rendered: the fill, or the fallback when no fill was given."""
    slot_name: str
    """The resolved slot name (``"default"`` for an unnamed slot)."""
    slot_node: SlotNode
    """The runtime ``SlotNode`` at whose site the slot rendered."""
    slot_is_required: bool
    """Whether the slot resolved as required."""
    result: RenderPart
    """The rendered output (a ``str`` or a ``CitryRender``)."""


@dataclass(frozen=True, slots=True)
class OnAttrsResolvedContext:
    citry: Citry
    """The ``Citry`` instance the component belongs to."""
    component: Component
    """The component whose template holds the element. For ``<c-element>``,
    this is the lexical owner, not the transparent built-in renderer."""
    tag_name: str
    """The HTML tag the attributes belong to (e.g. ``"div"``)."""
    attrs: dict[str, Any]
    """The resolved attribute dict: ``class``/``style`` already normalized to
    strings, booleans still ``True``, omitted attributes already absent."""


@dataclass(frozen=True, slots=True)
class RenderCacheInstance:
    """One selected artifact-local component identity exposed to payload extensions."""

    index: int
    render_id: str
    class_id: str


@dataclass(frozen=True, slots=True)
class OnRenderCacheExportContext:
    """Read-only selected subtree passed to a payload extension exporter."""

    citry: Citry
    root_context: CitryContext
    instances: tuple[RenderCacheInstance, ...]
    selected_render_ids: frozenset[str]


@dataclass(frozen=True, slots=True)
class OnRenderCacheStageContext:
    """Validated detached payload and fresh IDs passed to a replay stager."""

    citry: Citry
    payload: dict[str, object]
    instance_ids: tuple[str, ...]
    instance_class_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RenderCacheWrite:
    """One exact backend repair prepared without mutating the cache."""

    key: str
    value: str
    ttl: float | None = None
    rollback_delete: bool = False
    """Delete a newly created exact key if a later replay step fails."""


@dataclass(frozen=True, slots=True)
class StagedRenderCacheContribution:
    """Immutable extension contribution that core alone applies on replay."""

    extra_items: tuple[tuple[str, object], ...] = ()
    cache_writes: tuple[RenderCacheWrite, ...] = ()
    frame_markers: tuple[tuple[int, tuple[str, ...]], ...] = ()
    text_replacements: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class OnTemplateLoadedContext:
    citry: Citry
    """The ``Citry`` instance the component class belongs to."""
    component_class: type[Component]
    """The Component class whose template was loaded."""
    content: str
    """The template string (before parsing)."""


@dataclass(frozen=True, slots=True)
class OnMessagesLoadedContext:
    citry: Citry
    """The ``Citry`` instance the component class belongs to."""
    component_class: type[Component]
    """The Component class whose source messages were loaded."""
    declaration_owner: type
    """The class that authored the inherited messages/messages_file pair."""
    content: str
    """The source-locale Fluent text before compilation."""
    origin: str
    """A file path or inline ``module::Class.messages`` label for diagnostics."""


@dataclass(frozen=True, slots=True)
class OnCitryClearedContext:
    citry: Citry
    """The ``Citry`` instance whose registry and engine caches were cleared."""


@dataclass(frozen=True, slots=True)
class OnTemplateCompiledContext:
    citry: Citry
    """The ``Citry`` instance the component class belongs to."""
    component_class: type[Component]
    """The Component class whose template was compiled."""
    nodes: list[BodyItem]
    """The generated body node list."""


@dataclass(frozen=True, slots=True)
class OnJsLoadedContext:
    citry: Citry
    """The ``Citry`` instance the component class belongs to."""
    component_class: type[Component]
    """The Component class whose JS was loaded."""
    content: str
    """The JS content (inline or read from ``js_file``)."""


@dataclass(frozen=True, slots=True)
class OnCssLoadedContext:
    citry: Citry
    """The ``Citry`` instance the component class belongs to."""
    component_class: type[Component]
    """The Component class whose CSS was loaded."""
    content: str
    """The CSS content (inline or read from ``css_file``)."""


@dataclass(frozen=True, slots=True)
class OnFilesResetContext:
    citry: Citry
    """The ``Citry`` instance the component class belongs to."""
    component_class: type[Component]
    """The Component class whose loaded asset files were reset."""


@dataclass(frozen=True, slots=True)
class OnTemplateResetContext:
    citry: Citry
    """The ``Citry`` instance the component class belongs to."""
    component_class: type[Component]
    """The Component class whose loaded template was reset."""


@dataclass(frozen=True, slots=True)
class OnRenderContextMergeContext:
    citry: Citry
    """The ``Citry`` instance the render belongs to."""
    parent_context: CitryContext
    """The context of the render that consumed the nested one."""
    child_context: CitryContext
    """The context of the consumed nested render."""


@dataclass(frozen=True, slots=True)
class OnSerializeContext:
    citry: Citry
    """The ``Citry`` instance the render belongs to."""
    context: CitryContext
    """The root render's ``CitryContext`` (its ``extra`` carries everything
    that bubbled up during the render)."""
    html: str
    """The joined HTML (threaded: return a new string to replace it)."""
    placeholders: dict[str, str]
    """The placeholder parts found during serialization: unique placeholder id
    (the ``Placeholder.key`` plus a counter and a private serialization
    identity) to the exact text standing in for it in ``html``. Match the key
    prefix rather than relying on the private suffix."""
    deps_strategy: str
    """The ``serialize(deps_strategy=...)`` argument."""
    deps_position: str
    """The ``serialize(deps_position=...)`` argument."""


################################################
# COMMANDS
################################################


class ExtensionCommand:
    """
    Base class for an extension's CLI command.

    Subclass this, set ``name`` (and usually ``help``), declare any ``arguments``,
    and define ``handle`` to do the work. A command that only groups
    ``subcommands`` leaves ``handle`` unset, and the runner prints its help
    instead of running anything. The declarations are turned into an ``argparse``
    parser and dispatched by :mod:`citry.command`; an extension lists its command
    classes in ``Extension.commands`` and a user reaches one as
    ``citry ext run <extension> <command>``. (Extension HTTP routes are a
    separate surface, ``Extension.urls``.)
    """

    name: ClassVar[str]
    """The command name (``citry ext run <extension> <name>``)."""

    help: ClassVar[str] = ""
    """One-line description of the command, shown in ``--help`` output."""

    arguments: ClassVar[Sequence[CommandArg | CommandArgGroup]] = ()
    """Positional arguments and options, declared with :class:`~citry.command.CommandArg`."""

    subcommands: ClassVar[Sequence[type[ExtensionCommand]]] = ()
    """Nested commands. A command with subcommands usually has no ``handle`` of its own."""

    subparser_input: ClassVar[CommandSubcommand | None] = None
    """Optional customization of how this command appears when nested under a parent."""

    handle: CommandHandler | None = None
    """Runs the command, called with the parsed options as keyword arguments.
    ``None`` (the default) marks a command that only groups subcommands; a real
    command overrides this with ``def handle(self, **kwargs)``."""

    citry: Citry | None = None
    """The engine the command runs against, bound by the runner before ``handle``
    is called (mirrors :attr:`Extension.citry`). A command's ``handle`` reads it
    to reach the component registry and the installed extensions."""


################################################
# PER-COMPONENT CONFIG
################################################


class ExtensionConfig:
    """
    Base for the per-component nested config class (reached as ``Extension.Config``).

    An extension named ``"view"`` (``class_name == "View"``) lets a user define a
    nested ``class View:`` on a component. The manager rebuilds that nested class
    as a subclass of this base (binding ``component_class``), then instantiates it
    per render and attaches it as ``component.view``.

    The component back-reference is a weakref, and the component may be ``None``
    for extensions that run outside a component lifecycle (for example a future
    Storybook extension).
    """

    component_class: ClassVar[type[Component]]
    """The Component class this config is defined on (bound by the manager)."""

    def __init__(self, component: Component | None) -> None:
        # Weak ref to avoid a component <-> config reference cycle. ``None`` when
        # the extension runs outside a component lifecycle.
        self._component_ref: ReferenceType[Component] | None = ref(component) if component is not None else None

    @property
    def component(self) -> Component:
        """
        The owning Component instance.

        Raises ``RuntimeError`` if this config runs outside a component lifecycle
        (no component), or if the component has been garbage-collected.
        """
        if self._component_ref is None:
            msg = f"{type(self).__name__} runs outside a component lifecycle (no component)"
            raise RuntimeError(msg)
        component = self._component_ref()
        if component is None:
            msg = "Component has been garbage collected"
            raise RuntimeError(msg)
        return component


################################################
# EXTENSION BASE
################################################


class Extension:
    """
    Base class for all extensions.

    Subclass this, set ``name`` (a lowercase Python identifier), and implement the
    ``on_*`` hooks you care about. Every hook has an empty default, so an
    extension only overrides what it needs (the manager calls only the hooks an
    extension actually overrides). The ``on_*`` methods below are the full hook
    catalog.
    """

    name: ClassVar[str]
    """Name of the extension. Lowercase, a valid Python identifier. Determines
    the attribute the per-component config is reachable under
    (``component.<name>``) and, via :attr:`class_name`, the nested class name."""

    class_name: ClassVar[str]
    """PascalCase name of the per-component nested config class, derived from
    :attr:`name` at subclass creation (``my_extension`` -> ``MyExtension``)."""

    Config: ClassVar[type[ExtensionConfig]] = ExtensionConfig
    """Base class the per-component nested config inherits from."""

    commands: ClassVar[list[type[ExtensionCommand]]] = []
    """CLI commands this extension provides (see :class:`ExtensionCommand`)."""

    introspection_version: ClassVar[int | None] = None
    """Positive schema version when this extension publishes component metadata."""

    render_cache_mode: ClassVar[Literal["deny", "stateless", "payload"]] = "deny"
    """Whether settled render state from this extension can be replayed."""

    render_cache_version: ClassVar[int | None] = None
    """Positive compatibility version for stateless or payload replay."""

    _component_config_enabled: ClassVar[bool] = True
    """Internal gate for extensions whose nested config surface is not ready."""

    citry: Citry
    """The ``Citry`` instance this extension instance belongs to. Set by the
    manager when the extension is attached (extensions are per-instance, so
    the back-reference is unambiguous)."""

    @property
    def urls(self) -> list[URLRoute]:
        """
        HTTP routes this extension provides (see ``citry/util/routing.py``).

        Mounted by the web-integration adapters as part of ``Citry.urls``: a
        user extension's routes live under ``ext/<extension name>/``;
        built-in extensions own their paths directly. Override as an
        attribute or property; handlers can reach engine state through
        ``self.citry``.
        """
        return []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "name", None):
            msg = f"Extension {cls.__name__} must define a 'name'"
            raise ValueError(msg)
        if not cls.name.isidentifier():
            msg = f"Extension name must be a valid Python identifier, got {cls.name!r}"
            raise ValueError(msg)
        if not cls.name.islower():
            msg = f"Extension name must be lowercase, got {cls.name!r}"
            raise ValueError(msg)
        if not getattr(cls, "class_name", None):
            cls.class_name = snake_to_pascal(cls.name)
        if not isinstance(cls.class_name, str) or not cls.class_name.isidentifier():
            msg = f"Extension class_name must be a valid Python identifier, got {cls.class_name!r}"
            raise ValueError(msg)

    # ----- Config field validation -----

    def validate_config_fields(self, fields: Mapping[str, Any], *, component: type[Component] | None = None) -> None:
        """
        Check the config fields declared for this extension, at declaration time.

        Users configure an extension in two places: a component's nested config
        class (``class View:`` for an extension named ``"view"``), and the
        engine-wide
        [`extensions_defaults`][citry.CitrySettings.extensions_defaults]
        setting. Citry calls this method once per declaration:

        - At engine construction, with the extension's entry in the
          ``extensions_defaults`` setting (``component`` is ``None``).
        - At component class definition, with the fields declared on the
          component's nested config class, including fields from its
          user-written base classes (``component`` is the component class).

        The base implementation accepts everything: by default an extension's
        config may hold any fields, even methods. Override it to reject bad
        fields early, so a typo in a field name fails at startup or at class
        definition instead of surfacing later as a confusing downstream error.
        Because both declaration sites are checked, the fields are known-valid
        by the time the config class is instantiated.

        Args:
            fields: The declared fields, mapping field name to declared value.
                For a nested config class, dunder names, the ``Config`` base's
                members, and citry's own bookkeeping attributes are already
                filtered out.
            component: The component class the fields were declared on, or
                ``None`` when the fields come from the ``extensions_defaults``
                setting.

        Raises:
            ValueError: When a field is not valid for this extension. Raise it
                with a message naming the offending field and what is valid;
                citry prefixes the declaration site (the component and its
                nested class, or the setting).

        Example:
            An extension whose config accepts exactly one field:

            ```python
            from citry import Extension

            class CacheExtension(Extension):
                name = "cache"

                def validate_config_fields(self, fields, *, component=None):
                    for name in fields:
                        if name != "ttl":
                            msg = f"unknown config field {name!r}; the only field is 'ttl'"
                            raise ValueError(msg)
            ```

        """

    def _component_config_defaults(self, fields: Mapping[str, Any]) -> Mapping[str, Any]:
        """Select engine defaults inherited by per-component config instances."""
        return fields

    def inspect_component(self, ctx: ComponentIntrospectionContext) -> dict[str, object] | None:
        """
        Publish this extension's allowlisted metadata for one component.

        Citry calls this direct query method only when a caller explicitly
        requests the extension by name. Override it together with a positive
        :attr:`introspection_version`. Return an exact built-in ``dict`` made
        only from strict JSON values, or ``None`` when this component has no
        entry. The method must be observational, deterministic, reentrant, and
        thread-safe; it must not render, load assets, mutate registration, or
        depend on request state.

        Args:
            ctx: The owning engine, temporary live component class, and its
                already-built core metadata record. ``ctx.info.extensions`` is
                always empty.

        Returns:
            An extension-owned JSON object, or ``None``.

        """

    def inspect_template_namespace(
        self,
        ctx: TemplateNamespaceContext,
    ) -> TemplateNamespaceContribution | None:
        """
        Describe template variables supplied by this extension.

        Citry calls this observational hook while it captures tooling analysis.
        Return detached annotations only. Do not render, mutate the component,
        or depend on request state. The contribution can add known names or
        report that the extension preserves unenumerated extras, but it cannot
        change lint severity.

        Args:
            ctx: The owning engine and temporary component class.

        Returns:
            Portable namespace metadata, or ``None`` for no contribution.

        """

    # ----- Extension lifecycle -----

    def on_extension_created(self, ctx: OnExtensionCreatedContext) -> None:
        """Called once when this extension instance is created."""

    # ----- Component class lifecycle -----

    def on_component_class_created(self, ctx: OnComponentClassCreatedContext) -> None:
        """Called after a Component class is defined, before it is registered."""

    def on_component_registered(self, ctx: OnComponentRegisteredContext) -> None:
        """Called after a Component class is registered."""

    def on_component_unregistered(self, ctx: OnComponentUnregisteredContext) -> None:
        """Called after a Component class is unregistered."""

    def on_citry_cleared(self, ctx: OnCitryClearedContext) -> None:
        """Called during ``Citry.clear()`` after its registry is empty."""

    # ----- Component render -----

    def on_component_input(self, ctx: OnComponentInputContext) -> None:
        """
        Called when a component starts rendering, before ``template_data``.

        Inspect or mutate ``ctx.kwargs`` / ``ctx.slots`` in place. These are
        the authoritative raw mappings. Citry normalizes Slots and constructs
        the component's final typed ``kwargs`` and ``slots`` once all input
        hooks finish.
        """

    def on_component_data(self, ctx: OnComponentDataContext) -> None:
        """
        Called after ``template_data``; mutate ``ctx.template_data`` to add or
        change template variables.
        """

    def on_component_rendered(self, ctx: OnComponentRenderedContext) -> CitryRender | str | None:
        """
        Called after a component (and its children) rendered. Return a new
        ``CitryRender`` / ``str`` to replace the output, raise to replace the
        error, or return ``None`` to keep the original.
        """

    def on_slot_rendered(self, ctx: OnSlotRenderedContext) -> RenderPart | None:
        """
        Called after a ``<c-slot>`` site rendered (a fill, or the fallback).

        Return a new render part (``str`` or ``CitryRender``) to replace the
        output, or ``None`` to keep the original. Raising propagates.
        """

    def on_attrs_resolved(self, ctx: OnAttrsResolvedContext) -> dict[str, Any] | None:
        """
        Called after an HTML element's dynamic attributes resolved to their
        final dict, before it is formatted into the output. Return a new dict
        to replace the attributes, or ``None`` to keep them.

        Fires per element per render, only for elements with at least one
        dynamic attribute (a ``c-*`` value or a ``c-bind`` spread).
        """

    def on_render_context_merge(self, ctx: OnRenderContextMergeContext) -> None:
        """
        Called when a nested render's output is consumed by an enclosing
        render (a child component settling into its parent, or an
        already-rendered value embedded via an expression or slot).

        Merge your extension's slice of ``ctx.child_context.extra`` into
        ``ctx.parent_context.extra``, with your own policy (the dependencies
        extension, for example, appends records preserving order). The core
        does not merge anything itself.
        """

    def export_render_cache(self, ctx: OnRenderCacheExportContext) -> dict[str, object]:
        """Export this payload extension's selected strict-JSON contribution."""
        msg = f"Payload extension {self.name!r} does not implement export_render_cache()."
        raise NotImplementedError(msg)

    def stage_render_cache(self, ctx: OnRenderCacheStageContext) -> StagedRenderCacheContribution:
        """Validate a detached payload and return a mutation-free replay contribution."""
        msg = f"Payload extension {self.name!r} does not implement stage_render_cache()."
        raise NotImplementedError(msg)

    def _render_cache_participates(self, ctx: OnRenderCacheExportContext) -> bool:  # noqa: ARG002
        """Whether this deny-mode extension affected the selected render."""
        render_hooks = (
            "on_component_input",
            "on_component_data",
            "on_component_rendered",
            "on_slot_rendered",
            "on_attrs_resolved",
            "on_render_context_merge",
            "on_serialize",
            "on_template_loaded",
            "on_messages_loaded",
            "on_template_compiled",
            "on_js_loaded",
            "on_css_loaded",
        )
        return any(getattr(type(self), name) is not getattr(Extension, name) for name in render_hooks)

    def render_cache_bypass_reason(self) -> str | None:
        """Return a stable reason when this extension requires live rendering."""
        return None

    def on_serialize(self, ctx: OnSerializeContext) -> str | None:
        """
        Called at the end of ``CitryRender.serialize()`` with the joined HTML.

        Return a new string to replace the output (threaded across
        extensions), or ``None`` to keep it. This is where serialize-time
        work that needs the whole page happens; the dependencies extension
        places the collected JS/CSS here, using ``ctx.placeholders`` for the
        ``<c-js>``/``<c-css>`` positions.
        """

    def _on_serialize_internal(
        self,
        ctx: OnSerializeContext,
        _script_security: _ScriptSecurityMaterializer | None,
        _security_csp: SecurityCspMode,
        _javascript_policy: _JavascriptPolicy | None,
        _security_javascript: SecurityJavascriptMode,
        _ownership_artifact: OwnershipManifestArtifact | None,
    ) -> str | None:
        """Internal dispatch carrying call-local structured-script authority."""
        return self.on_serialize(ctx)

    # ----- Template -----

    def on_template_loaded(self, ctx: OnTemplateLoadedContext) -> str | None:
        """
        Called once per class with the template string before it is parsed.
        Return a new string to modify it.
        """

    def on_messages_loaded(self, ctx: OnMessagesLoadedContext) -> str | None:
        """
        Called once per source declaration with source-locale Fluent text
        before compilation. A parent and children that inherit the same
        messages share this one call.

        Return a new string to replace the source. User extensions run in
        installation order. The built-in i18n extension always runs after
        those transformations, so it compiles the same final string the asset
        loader caches.
        """

    def on_template_compiled(self, ctx: OnTemplateCompiledContext) -> list[BodyItem] | None:
        """
        Called once per compiled body, with the generated node list. Mutate it
        in place or return a new list.
        """

    def on_template_reset(self, ctx: OnTemplateResetContext) -> None:
        """Called after a component class's loaded template is reset."""

    # ----- JS / CSS -----

    def on_js_loaded(self, ctx: OnJsLoadedContext) -> str | None:
        """
        Called once per class with the component's primary JS content (inline
        or read from ``js_file``). Return a new string to modify it.
        """

    def on_css_loaded(self, ctx: OnCssLoadedContext) -> str | None:
        """
        Called once per class with the component's primary CSS content (inline
        or read from ``css_file``). Return a new string to modify it.
        """


################################################
# EXTENSION MANAGER
################################################

_Result = Literal["none", "map", "first"]

# Stamped as a class attribute on the classes the manager itself synthesizes
# while rebuilding a component's nested config class (the rebuilt class and the
# holder of the ``extensions_defaults`` fields), so that config-field
# enumeration can tell them apart from classes the user wrote.
_SYNTHESIZED_CONFIG_ATTR = "_citry_synthesized_config"


@dataclass(frozen=True, slots=True)
class _ComponentInspector:
    """One preflighted installed extension metadata capability."""

    extension: Extension
    version: int


# Temporarily off. The debug extension is meant to be a development-only
# built-in (dev_prod_mode.md section 4), but its render-cache participation
# turns a cached (`<c-cache>`) component's ownership graph into an invalid
# manifest, an uninvoked instance that still names a parent, even with both
# highlight flags off. Set this True again once that bug is fixed; the
# development-mode test in test_extension.py is marked xfail until then.
_AUTO_DEBUG_IN_DEVELOPMENT = False


def _builtin_extensions(mode: str) -> tuple[type[Extension], ...]:
    """
    The built-in extensions a ``Citry`` instance carries in the given ``mode``.

    Prepended to the user's extension spec by ``ExtensionManager._build``, so
    their names are effectively reserved (a user extension reusing one fails
    the duplicate-name validation). Built-ins cannot be disabled or replaced
    (docs/design/asset_loading.md section 7.2).

    Cache, Dependencies, Events, and i18n are always present. The ``debug`` extension
    draws visual component boundaries, which is developer-only output, so it is
    meant to be a built-in only when ``mode`` is ``"development"``
    (dev_prod_mode.md section 4). That auto-registration is temporarily gated
    off by ``_AUTO_DEBUG_IN_DEVELOPMENT`` (see the note there).
    """
    # Imported here, not at module load: the built-in extension modules
    # subclass Extension from this module, so a top-level import would be
    # circular.
    from citry.ext.cache import CacheExtension  # noqa: PLC0415
    from citry.ext.dependencies import DependenciesExtension  # noqa: PLC0415
    from citry.ext.events import EventsExtension  # noqa: PLC0415
    from citry.ext.i18n import I18nExtension  # noqa: PLC0415

    builtins: tuple[type[Extension], ...] = (
        CacheExtension,
        DependenciesExtension,
        EventsExtension,
        I18nExtension,
    )
    if mode == "development" and _AUTO_DEBUG_IN_DEVELOPMENT:
        from citry.ext.debug import Debug  # noqa: PLC0415

        builtins = (*builtins, Debug)
    return builtins


_MISSING_EXTENSION_OWNER = object()

# Public nested Component declarations owned by built-in extensions. They are
# real base-class API slots, so the owning extension may use its class name;
# every other collision remains an error.
_COMPONENT_CONFIG_API_OWNERS = {
    "Cache": "cache",
    "Dependencies": "dependencies",
    "Events": "events",
    "I18n": "i18n",
}


class ExtensionManager:
    """
    Fans each lifecycle hook out across a ``Citry`` instance's extensions.

    Owned by :class:`~citry.citry.Citry` and built once in its ``__init__``.
    Unlike DJC's module-level singleton, there is no deferred-event machinery: a
    component class is bound to its ``Citry`` (and thus these extensions) at
    definition time, so the extensions are always present when a hook fires.

    Dispatch is *smart*: for each hook name, only the extensions that actually
    override that hook are called (an extension that does not implement a hook
    costs nothing). The same name-keyed dispatch underlies :meth:`emit`, which
    extensions use for their own custom hooks (e.g. ``on_dependencies``).
    """

    def __init__(
        self,
        citry: Citry,
        extensions: Sequence[type[Extension] | Extension | str] = (),
    ) -> None:
        self.citry = citry
        # Name -> instance map, populated by ``_build`` for O(1) ``get_extension``.
        self._extensions_by_name: dict[str, Extension] = {}
        self._ownership_snapshot: list[tuple[Extension, object]] = []
        try:
            self._extensions: tuple[Extension, ...] = self._build(extensions)
            self._hook_extensions_cache: dict[str, tuple[Extension, ...]] = {}
            self._validated_component_declarations: dict[str, WeakSet[type]] = {}
            self._validate_names()
            self._validate_render_cache_compatibility()
            self._validate_extensions_defaults()
        except BaseException:
            self._rollback_extension_ownership()
            raise

    def _build(
        self,
        extensions: Sequence[type[Extension] | Extension | str],
    ) -> tuple[Extension, ...]:
        instances: list[Extension] = [builtin() for builtin in _builtin_extensions(self.citry.mode)]
        for extension in extensions:
            resolved: type[Extension] | Extension
            # Case: Import path like `my_package.my_module.MyExtension`.
            if isinstance(extension, str):
                module_path, class_name = extension.rsplit(".", 1)
                resolved = getattr(import_module(module_path), class_name)
            # Case: class object or instance.
            else:
                resolved = extension
            if isinstance(resolved, type):
                instance = resolved()
            else:
                instance = resolved
                current_owner = getattr(instance, "citry", None)
                if current_owner is not None and current_owner is not self.citry:
                    msg = (
                        f"Extension instance {instance.name!r} is already installed on another Citry instance. "
                        "Pass the extension class or create a fresh extension instance."
                    )
                    raise ValueError(msg)
            instances.append(instance)
        # Attach the Citry back-reference (extensions are per-instance, so
        # each instance belongs to exactly one Citry).
        self._ownership_snapshot = [
            (instance, getattr(instance, "citry", _MISSING_EXTENSION_OWNER)) for instance in instances
        ]
        for instance in instances:
            instance.citry = self.citry
        # Name -> instance map for O(1) ``get_extension``. A duplicate name
        # collapses here, but ``_validate_names`` scans the full tuple and raises
        # on duplicates, so an ambiguous map can never be used.
        self._extensions_by_name = {inst.name: inst for inst in instances}
        # Make extensions list immutable
        return tuple(instances)

    def _commit_extension_ownership(self) -> None:
        """Forget rollback state after construction hooks have succeeded."""
        self._ownership_snapshot.clear()

    def _rollback_extension_ownership(self) -> None:
        """Restore extension owners after engine construction fails."""
        for instance, owner in reversed(self._ownership_snapshot):
            if owner is _MISSING_EXTENSION_OWNER:
                if hasattr(instance, "citry"):
                    del instance.citry
            else:
                instance.citry = cast("Citry", owner)
        self._ownership_snapshot.clear()

    def _validate_names(self) -> None:
        # The Component-API conflict check needs the Component class, which is
        # not importable while the default ``citry = Citry()`` is constructed
        # (citry.py is still mid-import and component.py imports it back). The
        # default instance carries only the built-in extensions, whose names
        # are known not to conflict, so skipping the API check there is safe;
        # any user-constructed Citry runs the full validation.
        try:
            from citry.component import Component  # noqa: PLC0415
        except ImportError:
            component: type | None = None
        else:
            component = Component

        seen: set[str] = set()
        class_name_owners: dict[str, str] = {}
        reserved_class_names = {"Kwargs", "Slots", "TemplateData", "JsData", "CssData", "Lint", "State"}
        for extension in self._extensions:
            # Built-in names are reserved: the built-ins come first in the
            # tuple, so a user extension reusing one fails here as a duplicate.
            if extension.name in seen:
                msg = f"Multiple extensions cannot share the name {extension.name!r}"
                raise ValueError(msg)
            seen.add(extension.name)
            if extension.class_name in reserved_class_names:
                msg = (
                    f"Extension {extension.name!r} cannot use reserved component declaration"
                    f" name {extension.class_name!r} as its class_name"
                )
                raise ValueError(msg)
            previous_owner = class_name_owners.get(extension.class_name)
            if previous_owner is not None:
                msg = (
                    f"Extensions {previous_owner!r} and {extension.name!r} cannot share"
                    f" class_name {extension.class_name!r}"
                )
                raise ValueError(msg)
            class_name_owners[extension.class_name] = extension.name
            instance_name_conflicts = component is not None and hasattr(component, extension.name)
            class_name_conflicts = (
                component is not None
                and hasattr(component, extension.class_name)
                and _COMPONENT_CONFIG_API_OWNERS.get(extension.class_name) != extension.name
            )
            if instance_name_conflicts or class_name_conflicts:
                msg = f"Extension name {extension.name!r} conflicts with existing Component API"
                raise ValueError(msg)

    def _validate_extensions_defaults(self) -> None:
        """
        Run each extension's config-field validation over its entry in the
        ``extensions_defaults`` setting, so a bad key in the setting fails at
        engine construction instead of surfacing later as a downstream error.
        """
        defaults_all = self.citry.settings.extensions_defaults
        for extension in self._extensions:
            fields = defaults_all.get(extension.name)
            if fields is None:
                continue
            # A non-mapping entry (say a bare string) would otherwise surface
            # as a confusing error from inside the extension's own validation.
            if not isinstance(fields, Mapping):
                msg = (
                    f"Extension {extension.name!r}: the entry in the 'extensions_defaults' setting must be"
                    f" a mapping of config field names to values; got {fields!r}."
                )
                # ValueError, not TypeError: every engine-construction error
                # raises ValueError, one type for the whole matrix.
                raise ValueError(msg)  # noqa: TRY004
            try:
                extension.validate_config_fields(fields, component=None)
            except ValueError as err:
                msg = f"Extension {extension.name!r}: invalid config field in the 'extensions_defaults' setting. {err}"
                raise ValueError(msg) from err

    def _validate_render_cache_compatibility(self) -> None:
        """Validate every extension's declarative replay compatibility stamp."""
        valid_modes = {"deny", "stateless", "payload"}
        for extension in self._extensions:
            mode = extension.render_cache_mode
            version = extension.render_cache_version
            if type(mode) is not str or mode not in valid_modes:
                msg = (
                    f"Extension {extension.name!r}: render_cache_mode must be one of"
                    f" {', '.join(sorted(valid_modes))}; got {mode!r}."
                )
                raise ValueError(msg)
            if version is not None and (type(version) is not int or version <= 0):
                msg = f"Extension {extension.name!r}: render_cache_version must be a positive exact int or None."
                raise ValueError(msg)
            if mode != "deny" and version is None:
                msg = (
                    f"Extension {extension.name!r}: render_cache_mode={mode!r} requires a positive"
                    " render_cache_version."
                )
                raise ValueError(msg)

    def get_extension(self, name: str) -> Extension:
        extension = self._extensions_by_name.get(name)
        if extension is None:
            msg = f"Extension {name!r} not found"
            raise ValueError(msg)
        return extension

    def _template_namespace_contributions(
        self,
        component_class: type[Component],
    ) -> tuple[tuple[str, TemplateNamespaceContribution], ...]:
        """Collect validated extension facts without allowing a severity override."""
        ctx = TemplateNamespaceContext(self.citry, component_class)
        contributions: list[tuple[str, TemplateNamespaceContribution]] = []
        for extension in self._extensions_with_hook("inspect_template_namespace"):
            try:
                contribution = extension.inspect_template_namespace(ctx)
            except Exception as err:
                msg = (
                    f"Extension {extension.name!r} failed while inspecting the template namespace "
                    f"for {component_class.__name__}."
                )
                raise RuntimeError(msg) from err
            if contribution is None:
                continue
            if type(contribution) is not TemplateNamespaceContribution:
                msg = (
                    f"Extension {extension.name!r} must return TemplateNamespaceContribution or None "
                    "from inspect_template_namespace()."
                )
                raise TypeError(msg)
            contributions.append((extension.name, contribution))
        return tuple(contributions)

    def _advance_render_cache_revision(self) -> int:
        """Advance the built-in Cache extension's local invalidation state."""
        cache_extension = self._extensions_by_name["cache"]
        return cast("Any", cache_extension)._advance_revision()

    @contextmanager
    def _render_cache_invalidation(self) -> Iterator[None]:
        """Hold the cache revision guard until derived-state reset commits."""
        cache_extension = self._extensions_by_name["cache"]
        with cast("Any", cache_extension)._invalidation():
            yield

    def _export_render_cache(self, ctx: OnRenderCacheExportContext) -> tuple[Any, ...]:
        """Enforce compatibility and detach every participating payload extension."""
        from citry.ext.cache.artifact import ArtifactExtension, _freeze_object  # noqa: PLC0415
        from citry.ext.cache.errors import CacheArtifactError, _CacheUncacheableError  # noqa: PLC0415

        exported: list[ArtifactExtension] = []
        for extension in self._extensions:
            mode = extension.render_cache_mode
            if mode == "deny":
                if extension._render_cache_participates(ctx):
                    raise _CacheUncacheableError(extension.name)
                continue
            if mode == "stateless":
                continue
            version = extension.render_cache_version
            if type(version) is not int or version <= 0:  # validated at construction; defensive here
                raise CacheArtifactError(f"Extension {extension.name!r} has no valid render-cache version.")
            payload = extension.export_render_cache(ctx)
            if type(payload) is not dict:
                raise CacheArtifactError(f"Extension {extension.name!r} cache exporter must return an exact dict.")
            exported.append(
                ArtifactExtension(
                    name=extension.name,
                    version=version,
                    payload=_freeze_object(payload, f"extension {extension.name!r} payload"),
                )
            )
        return tuple(exported)

    def _stage_render_cache(
        self,
        payloads: tuple[Any, ...],
        *,
        instance_ids: tuple[str, ...],
        instance_class_ids: tuple[str, ...],
    ) -> tuple[StagedRenderCacheContribution, ...]:
        """Validate every payload and stage immutable contributions without mutation."""
        from citry.ext.cache.artifact import ArtifactExtension, _thaw_json  # noqa: PLC0415
        from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

        expected = [extension for extension in self._extensions if extension.render_cache_mode == "payload"]
        if len(payloads) != len(expected):
            raise CacheArtifactError("Cached render artifact has incomplete extension payload coverage.")
        staged: list[StagedRenderCacheContribution] = []
        for index, (payload, extension) in enumerate(zip(payloads, expected, strict=True)):
            if type(payload) is not ArtifactExtension:
                raise CacheArtifactError(f"Artifact extension payload {index} has an invalid type.")
            if payload.name != extension.name or payload.version != extension.render_cache_version:
                raise CacheArtifactError(
                    f"Artifact extension payload {index} is incompatible with extension {extension.name!r}."
                )
            thawed = _thaw_json(payload.payload)
            if type(thawed) is not dict:
                raise CacheArtifactError(f"Extension {extension.name!r} payload must be a JSON object.")
            contribution = extension.stage_render_cache(
                OnRenderCacheStageContext(
                    citry=self.citry,
                    payload=cast("dict[str, object]", thawed),
                    instance_ids=instance_ids,
                    instance_class_ids=instance_class_ids,
                )
            )
            if type(contribution) is not StagedRenderCacheContribution:
                raise CacheArtifactError(
                    f"Extension {extension.name!r} cache stager returned an invalid contribution."
                )
            if any(type(item) is not tuple or len(item) != 2 for item in contribution.extra_items):
                raise CacheArtifactError(f"Extension {extension.name!r} staged invalid context entries.")
            for write in contribution.cache_writes:
                if (
                    type(write) is not RenderCacheWrite
                    or type(write.key) is not str
                    or not write.key
                    or type(write.value) is not str
                    or type(write.rollback_delete) is not bool
                ):
                    raise CacheArtifactError(f"Extension {extension.name!r} staged an invalid cache write.")
            for instance, markers in contribution.frame_markers:
                if type(instance) is not int or type(markers) is not tuple:
                    raise CacheArtifactError(f"Extension {extension.name!r} staged invalid frame markers.")
                if any(type(marker) is not str or not marker for marker in markers):
                    raise CacheArtifactError(f"Extension {extension.name!r} staged invalid frame markers.")
            for old, new in contribution.text_replacements:
                if type(old) is not str or not old or type(new) is not str or not new:
                    raise CacheArtifactError(f"Extension {extension.name!r} staged invalid text replacements.")
            staged.append(contribution)
        return tuple(staged)

    def _prepare_component_inspectors(self, requested: object) -> tuple[_ComponentInspector, ...]:
        """Normalize and preflight every explicitly requested inspector."""
        if isinstance(requested, str):
            msg = "Citry introspection include_extensions must be an iterable of names, not a string."
            raise TypeError(msg)
        try:
            raw_names: tuple[object, ...] = tuple(cast("Any", requested))
        except TypeError as err:
            msg = "Citry introspection include_extensions must be an iterable of names."
            raise TypeError(msg) from err
        if any(type(name) is not str or not name for name in raw_names):
            msg = "Citry introspection extension names must be exact non-empty strings."
            raise TypeError(msg)

        inspectors: list[_ComponentInspector] = []
        for name in sorted(set(cast("tuple[str, ...]", raw_names))):
            extension = self._extensions_by_name.get(name)
            if extension is None:
                raise ComponentIntrospectionError(name, None, "the extension is not installed.")
            method = getattr(type(extension), "inspect_component", None)
            if method is Extension.inspect_component or not callable(method):
                raise ComponentIntrospectionError(name, None, "the extension does not implement an inspector.")
            version = getattr(type(extension), "introspection_version", None)
            if type(version) is not int or version <= 0:
                raise ComponentIntrospectionError(
                    name,
                    None,
                    "introspection_version must be a positive integer.",
                )
            inspectors.append(_ComponentInspector(extension=extension, version=version))
        return tuple(inspectors)

    @staticmethod
    def _component_introspection_versions(
        inspectors: tuple[_ComponentInspector, ...],
    ) -> tuple[ExtensionVersion, ...]:
        """Return the catalog envelope entries for a preflighted selection."""
        return tuple(
            ExtensionVersion(name=inspector.extension.name, introspection_version=inspector.version)
            for inspector in inspectors
        )

    def _inspect_component_extensions(
        self,
        component_class: type[Component],
        info: ComponentInfo,
        inspectors: tuple[_ComponentInspector, ...],
    ) -> ComponentInfo:
        """Run selected inspectors against one complete core metadata record."""
        if not inspectors:
            return info
        if info.extensions:
            msg = "Extension inspectors require a core ComponentInfo with no existing extension entries."
            raise RuntimeError(msg)
        ctx = ComponentIntrospectionContext(citry=self.citry, component_class=component_class, info=info)
        entries: list[ComponentExtensionInfo] = []
        for inspector in inspectors:
            extension = inspector.extension
            try:
                published = extension.inspect_component(ctx)
                if published is None:
                    continue
                frozen = _freeze_extension_publication(published)
                entries.append(
                    ComponentExtensionInfo(
                        name=extension.name,
                        introspection_version=inspector.version,
                        data=frozen,
                    )
                )
            except Exception as err:
                component_name = info.name
                error_type = type.__dict__["__name__"].__get__(type(err))
                detail = f"its inspector or publication validation raised {error_type}."
                raise ComponentIntrospectionError(extension.name, component_name, detail) from err
        return replace(info, extensions=tuple(entries))

    def get_extension_command(self, name: str, command_name: str) -> type[ExtensionCommand]:
        for command in self.get_extension(name).commands:
            if command.name == command_name:
                return command
        msg = f"Command {command_name!r} not found in extension {name!r}"
        raise ValueError(msg)

    @property
    def commands(self) -> dict[str, tuple[type[ExtensionCommand], ...]]:
        """
        Every extension's CLI commands, keyed by extension name (read as ``Citry.commands``).

        Built-in extensions come first (they are prepended at construction), then
        the user's extensions in spec order; only extensions that declare commands
        appear. Extension names are unique (enforced at construction), so the keys
        never collide. The CLI reaches a command as
        ``citry ext run <extension name> <command name>``.
        """
        return {extension.name: tuple(extension.commands) for extension in self._extensions if extension.commands}

    @property
    def urls(self) -> tuple[URLRoute, ...]:
        """
        The combined route table of every extension (read as ``Citry.urls``).

        Built-in extensions own their paths directly (e.g. the dependencies
        extension's ``cache/...`` and ``citry.js``); a user extension's
        routes are namespaced under ``ext/<extension name>/`` so they cannot
        collide with citry's own or each other's.
        """
        # Imported here, not at module load: routing is only needed when a
        # web integration asks for the table.
        from citry.util.routing import URLRoute  # noqa: PLC0415

        builtin_types = _builtin_extensions(self.citry.mode)
        routes: list[URLRoute] = []
        namespaced: list[URLRoute] = []
        for extension in self._extensions:
            extension_urls = tuple(extension.urls)
            if not extension_urls:
                continue
            if isinstance(extension, builtin_types):
                routes.extend(extension_urls)
            else:
                namespaced.append(URLRoute(f"ext/{extension.name}/", children=extension_urls))
        return (*routes, *namespaced)

    # ----- Smart dispatch -----

    def _extensions_with_hook(self, name: str) -> tuple[Extension, ...]:
        """
        Filter for extensions that implement a hook named ``name``. Cached per-name
        for efficiency since this is called on every hook emit.

        For a hook declared on :class:`Extension`, an extension defines it when
        its method differs from the base (i.e. it is overridden). For a custom
        hook not on the base (a future ``emit``-only hook), any extension that
        defines a method of that name qualifies.
        """
        # Remember which extensions define which hooks, so we don't have to
        # iterate all extensions on every hook call.
        cached = self._hook_extensions_cache.get(name)
        if cached is not None:
            return cached

        base_method = getattr(Extension, name, None)
        matching: list[Extension] = []
        for extension in self._extensions:
            method = getattr(type(extension), name, None)
            if not callable(method):
                continue
            if base_method is not None and method is base_method:
                continue  # inherited, not overridden
            matching.append(extension)
        result = tuple(matching)

        self._hook_extensions_cache[name] = result
        return result

    def emit(self, name: str, ctx: Any, result: _Result = "none", field: str | None = None) -> Any:
        """
        Dispatch hook ``name`` to the extensions that define it, combining the
        hooks' returned values per ``result``:

        - ``"none"``: call every extension, ignore returns; return ``None``.
        - ``"first"``: return the first non-``None`` return (short-circuit).
        - ``"map"``: thread ``ctx.<field>`` - each non-``None`` return replaces it
          (via ``dataclasses.replace``) and is passed to the next extension; the
          final field value is returned.

        An extension defines ``name`` by overriding it (see
        ``_extensions_with_hook``). ``name`` need not be a hook declared on
        :class:`Extension`, so an extension can fire its own custom hook for
        others to implement.

        Examples:
            Most named hooks delegate here. ``on_component_data`` notifies every
            extension that defines it (``"none"``)::

                manager.emit("on_component_data", ctx)

            ``on_template_loaded`` threads ``ctx.content`` through the extensions
            (``"map"``) and returns the final string::

                manager.emit("on_template_loaded", ctx, result="map", field="content")

            A custom hook can let an extension short-circuit (``"first"`` returns
            the first non-``None`` value)::

                manager.emit("on_my_event", ctx, result="first")

        """
        extensions = self._extensions_with_hook(name)
        if result == "none":
            for extension in extensions:
                getattr(extension, name)(ctx)
            return None
        if result == "first":
            for extension in extensions:
                out = getattr(extension, name)(ctx)
                if out is not None:
                    return out
            return None
        if result == "map":
            if field is None:
                msg = "emit(result='map') requires a field name"
                raise ValueError(msg)
            for extension in extensions:
                out = getattr(extension, name)(ctx)
                if out is not None:
                    ctx = replace(ctx, **{field: out})
            return getattr(ctx, field)
        msg = f"Unknown result policy {result!r}"
        raise ValueError(msg)

    # ----- Per-component config classes -----

    def _declared_config_fields(self, extension: Extension, user_cls: type) -> dict[str, Any]:
        """
        The config fields a user-declared nested config class carries: the own
        attributes of every user-written class in its MRO, merged base-first so
        the nearest declaration's value wins (mirroring attribute lookup).

        Excluded, so only what the user wrote counts as a field: dunder names,
        the extension's ``Config`` base and everything above it, and the
        classes ``_init_component_class`` itself synthesizes (recognized by the
        ``_SYNTHESIZED_CONFIG_ATTR`` stamp), which subclassing a parent
        component's rebuilt config pulls into the MRO.
        """
        framework_classes = set(extension.Config.__mro__)
        fields: dict[str, Any] = {}
        for klass in reversed(user_cls.__mro__):
            if klass in framework_classes or _SYNTHESIZED_CONFIG_ATTR in vars(klass):
                continue
            for name, value in vars(klass).items():
                if name.startswith("__") and name.endswith("__"):
                    continue
                fields[name] = value
        return fields

    def _validate_component_config_fields(self, component_class: type[Component]) -> None:
        """
        Validate each newly encountered authored config declaration.

        Called at class definition, before ``on_component_class_created``
        reaches any extension, so hooks and effective config classes only see
        validated fields. The manager validates a declaration once for this
        Citry instance, including a declaration inherited from a reusable
        definition base that did not itself pass through ``ComponentMeta``.
        """
        for extension in self._extensions:
            for declaration in _get_nested_class_declarations(component_class, extension.class_name):
                if declaration.value is None:
                    break
                if not isinstance(declaration.value, type):
                    continue
                validated = self._validated_component_declarations.setdefault(extension.name, WeakSet())
                if declaration.declaring_class in validated:
                    continue
                fields = self._declared_config_fields(extension, declaration.value)
                try:
                    extension.validate_config_fields(fields, component=component_class)
                except ValueError as err:
                    msg = (
                        f"Component {component_class.__name__}: invalid config field on its nested"
                        f" {extension.class_name!r} class (the {extension.name!r} extension). {err}"
                    )
                    raise ValueError(msg) from err
                validated.add(declaration.declaring_class)

    def _init_component_class(self, component_class: type[Component]) -> None:
        """
        Rebuild each extension's nested config class as a subclass of its ``Config`` base.

        For an extension named ``"view"`` (``class_name == "View"``): synthesize a
        new ``View`` whose bases are ``(user View, GlobalDefaults, ext.Config)`` -
        so attribute precedence is component-level > global defaults > factory -
        with ``component_class`` bound, and assign it back. If the component
        defines no nested class, the synthesized class is just ``ext.Config``.
        """
        defaults_all = self.citry.settings.extensions_defaults
        for extension in self._extensions:
            if not extension._component_config_enabled:
                continue
            class_name = extension.class_name
            user_cls = _compose_nested_declaration_class(component_class, class_name)

            bases: list[type] = [extension.Config]

            ext_defaults = extension._component_config_defaults(defaults_all.get(extension.name, {}))
            if ext_defaults:
                defaults_cls = type(
                    f"{class_name}Defaults",
                    (),
                    {**dict(ext_defaults), _SYNTHESIZED_CONFIG_ATTR: True},
                )
                bases.insert(0, defaults_cls)

            if isinstance(user_cls, type):
                bases.insert(0, user_cls)

            config_cls = type(
                class_name,
                tuple(bases),
                {
                    "__module__": component_class.__module__,
                    "__qualname__": f"{component_class.__qualname__}.{class_name}",
                    "component_class": component_class,
                    _SYNTHESIZED_CONFIG_ATTR: True,
                },
            )
            # Nested declarations are immutable after class creation. This is
            # the framework's one-time materialization of the captured source,
            # so bypass the public component metaclass guard deliberately.
            type.__setattr__(component_class, class_name, config_cls)

    def _init_component_instance(self, component: Component) -> None:
        """
        Instantiate each extension's config class with the component and attach
        it as ``component.<extension.name>``.
        """
        component_class = type(component)
        for extension in self._extensions:
            if not extension._component_config_enabled:
                continue
            config_cls = getattr(component_class, extension.class_name, None)
            if not (isinstance(config_cls, type) and issubclass(config_cls, extension.Config)):
                # The class was defined before this extension's config was set up.
                # Should not happen in normal flow (the metaclass runs
                # _init_component_class), but recover defensively.
                self._init_component_class(component_class)
                config_cls = getattr(component_class, extension.class_name)
            setattr(component, extension.name, config_cls(component))

    # ----- Lifecycle hooks -----

    def on_extension_created(self) -> None:
        # Each extension receives a context naming itself, so this cannot go
        # through the shared-ctx ``emit``.
        for extension in self._extensions_with_hook("on_extension_created"):
            extension.on_extension_created(OnExtensionCreatedContext(citry=self.citry, extension=extension))

    def on_component_class_created(self, component_class: type[Component]) -> None:
        # Validate newly declared config fields before the hook reaches any
        # extension, so extensions (and the config weaving that follows) only
        # ever see validated fields.
        self._validate_component_config_fields(component_class)
        self.emit(
            "on_component_class_created",
            OnComponentClassCreatedContext(citry=self.citry, component_class=component_class),
        )

    def on_component_registered(self, name: str, component_class: type[Component]) -> None:
        self.emit(
            "on_component_registered",
            OnComponentRegisteredContext(citry=self.citry, name=name, component_class=component_class),
        )

    def on_component_unregistered(self, name: str, component_class: type[Component]) -> None:
        self.emit(
            "on_component_unregistered",
            OnComponentUnregisteredContext(citry=self.citry, name=name, component_class=component_class),
        )

    def on_citry_cleared(self) -> None:
        self.emit("on_citry_cleared", OnCitryClearedContext(citry=self.citry))

    # ----- Render hooks -----

    def on_component_input(self, component: Component) -> None:
        # Skip building the context dataclass when no extension subscribes, the
        # same short-circuit the per-element/per-slot hooks use. This runs per
        # component, so the allocation is worth avoiding on the construction path.
        if not self.has_hook("on_component_input"):
            return
        self.emit(
            "on_component_input",
            OnComponentInputContext(
                citry=self.citry,
                component=component,
                kwargs=component.raw_kwargs,
                slots=component.raw_slots,
            ),
        )

    def on_component_data(
        self,
        component: Component,
        context: CitryContext,
        template_data: dict[str, Any],
        js_data: dict[str, Any],
        css_data: dict[str, Any],
    ) -> None:
        if not self.has_hook("on_component_data"):
            return
        ctx = OnComponentDataContext(
            citry=self.citry,
            component=component,
            context=context,
            template_data=template_data,
            js_data=js_data,
            css_data=css_data,
        )
        extensions = self._extensions_with_hook("on_component_data")
        i18n = self._extensions_by_name["i18n"]
        # Configured i18n owns the reserved tr/fmt names. Run it after every
        # user extension so a later hook cannot replace the checked facades.
        ordered = [extension for extension in extensions if extension is not i18n]
        if i18n in extensions:
            ordered.append(i18n)
        for extension in ordered:
            extension.on_component_data(ctx)

    def on_render_context_merge(self, parent_context: CitryContext, child_context: CitryContext) -> None:
        self.emit(
            "on_render_context_merge",
            OnRenderContextMergeContext(citry=self.citry, parent_context=parent_context, child_context=child_context),
        )

    def on_serialize(
        self,
        context: CitryContext,
        html: str,
        placeholders: dict[str, str],
        deps_strategy: str,
        deps_position: str,
        *,
        _script_security: _ScriptSecurityMaterializer | None = None,
        _security_csp: SecurityCspMode = "off",
        _javascript_policy: _JavascriptPolicy | None = None,
        _security_javascript: SecurityJavascriptMode = "allow",
        _ownership_artifact: OwnershipManifestArtifact | None = None,
    ) -> str:
        ctx = OnSerializeContext(
            citry=self.citry,
            context=context,
            html=html,
            placeholders=placeholders,
            deps_strategy=deps_strategy,
            deps_position=deps_position,
        )
        for extension in self._extensions_with_hook("on_serialize"):
            out = extension._on_serialize_internal(
                ctx,
                _script_security,
                _security_csp,
                _javascript_policy,
                _security_javascript,
                _ownership_artifact,
            )
            if out is not None:
                ctx = replace(ctx, html=out)
        return ctx.html

    def on_component_rendered(
        self,
        component: Component,
        render: CitryRender | str | None,
        error: Exception | None,
    ) -> tuple[CitryRender | str | None, Exception | None, bool]:
        """
        Thread the rendered output through the extensions; a return replaces the
        render, a raise replaces the error.
        """
        # Fires for every component; skip the context build when unsubscribed.
        had_error = error is not None
        if not self.has_hook("on_component_rendered"):
            return render, error, had_error
        ctx = OnComponentRenderedContext(citry=self.citry, component=component, render=render, error=error)
        for extension in self._extensions_with_hook("on_component_rendered"):
            try:
                out = extension.on_component_rendered(ctx)
            except Exception as err:  # noqa: BLE001
                had_error = True
                ctx = replace(ctx, render=None, error=err)
            else:
                if out is not None:
                    ctx = replace(ctx, render=out, error=None)
        return ctx.render, ctx.error, had_error

    def on_slot_rendered(
        self,
        component: Component,
        slot: Slot,
        slot_name: str,
        slot_node: SlotNode,
        slot_is_required: bool,
        result: RenderPart,
    ) -> RenderPart:
        """
        Thread a slot's rendered output through the extensions; a return
        replaces the result, a raise propagates.
        """
        # Skip building the context when nothing subscribes: this fires for
        # every slot of every component, so the dataclass would otherwise be
        # built and thrown away on a hot path.
        if not self.has_hook("on_slot_rendered"):
            return result
        return self.emit(
            "on_slot_rendered",
            OnSlotRenderedContext(
                citry=self.citry,
                component=component,
                slot=slot,
                slot_name=slot_name,
                slot_node=slot_node,
                slot_is_required=slot_is_required,
                result=result,
            ),
            result="map",
            field="result",
        )

    def has_hook(self, name: str) -> bool:
        """Whether any installed extension implements the hook ``name``."""
        return bool(self._extensions_with_hook(name))

    def on_attrs_resolved(
        self,
        component: Component,
        tag_name: str,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Thread an element's resolved attribute dict through the extensions; a
        return replaces the dict, a raise propagates.

        This sits on a per-element per-render hot path, so when no extension
        implements the hook the dict is returned without building a context.
        """
        if not self._extensions_with_hook("on_attrs_resolved"):
            return attrs
        return self.emit(
            "on_attrs_resolved",
            OnAttrsResolvedContext(
                citry=self.citry,
                component=component,
                tag_name=tag_name,
                attrs=attrs,
            ),
            result="map",
            field="attrs",
        )

    # ----- Template hooks -----

    def on_template_loaded(self, component_class: type[Component], content: str) -> str:
        return self.emit(
            "on_template_loaded",
            OnTemplateLoadedContext(citry=self.citry, component_class=component_class, content=content),
            result="map",
            field="content",
        )

    def on_messages_loaded(
        self,
        component_class: type[Component],
        declaration_owner: type,
        content: str,
        origin: str,
    ) -> str:
        ctx = OnMessagesLoadedContext(
            citry=self.citry,
            component_class=component_class,
            declaration_owner=declaration_owner,
            content=content,
            origin=origin,
        )
        extensions = self._extensions_with_hook("on_messages_loaded")
        i18n = self._extensions_by_name["i18n"]
        # User extensions may normalize or replace authored source. The
        # built-in runtime must compile the final value, and it must not retain
        # a catalog when an earlier transformer raises. Keep i18n last for this
        # one mapping hook regardless of extension installation order.
        ordered = [extension for extension in extensions if extension is not i18n]
        if i18n in extensions:
            ordered.append(i18n)
        for extension in ordered:
            result = extension.on_messages_loaded(ctx)
            if result is not None:
                ctx = replace(ctx, content=result)
        return ctx.content

    def on_template_compiled(self, component_class: type[Component], nodes: list[BodyItem]) -> list[BodyItem]:
        return self.emit(
            "on_template_compiled",
            OnTemplateCompiledContext(citry=self.citry, component_class=component_class, nodes=nodes),
            result="map",
            field="nodes",
        )

    def on_template_reset(self, component_class: type[Component]) -> None:
        """Notify extensions after a component class's template is reset."""
        self.emit(
            "on_template_reset",
            OnTemplateResetContext(citry=self.citry, component_class=component_class),
        )

    # ----- JS / CSS hooks -----

    def on_js_loaded(self, component_class: type[Component], content: str) -> str:
        return self.emit(
            "on_js_loaded",
            OnJsLoadedContext(citry=self.citry, component_class=component_class, content=content),
            result="map",
            field="content",
        )

    def on_css_loaded(self, component_class: type[Component], content: str) -> str:
        return self.emit(
            "on_css_loaded",
            OnCssLoadedContext(citry=self.citry, component_class=component_class, content=content),
            result="map",
            field="content",
        )

    def on_files_reset(self, component_class: type[Component]) -> None:
        """
        Notify extensions that a component class's loaded asset files were
        reset, so each drops its own per-class state (the ``dependencies``
        built-in drops its merged result here).

        Deliberately not declared on the :class:`Extension` base: this is the
        first consumer of the duck-typed custom-hook dispatch (an extension
        subscribes by defining a method named ``on_files_reset``).
        """
        self.emit(
            "on_files_reset",
            OnFilesResetContext(citry=self.citry, component_class=component_class),
        )
