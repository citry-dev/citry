"""
Implementation of the ``events`` extension class.

The package ``__init__`` re-exports the public names; this module holds the
extension itself: the raw-class capture of each component's ``Events`` and
``State`` declarations, the class-definition validation of both, the
three-level config resolution, and the per-class :class:`EventsInfo` record
everything else reads. Design: ``docs/design/events.md`` section 3.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from difflib import get_close_matches
from types import FunctionType
from typing import TYPE_CHECKING, Any, Literal, cast
from weakref import WeakKeyDictionary

from citry._nested_declarations import (
    _active_nested_class_declarations,
    _compose_nested_declaration_class,
)
from citry.ext.events._introspection import capture_handler_introspection, inspect_events
from citry.ext.events.bindings import compile_template_bindings, rewrite_resolved_attrs
from citry.ext.events.cache import export_events_cache, stage_events_cache
from citry.ext.events.config import Events
from citry.ext.events.emission import capture_instance, emit_events_dependencies, merge_instance_entries
from citry.ext.events.handlers import (
    CONFIG_NAMES,
    collect_event_handlers,
    event_options,
    is_def_like,
    resolve_data_schema,
    user_level_classes,
    validate_callable_value,
    validate_csrf_value,
    validate_handler_signature,
    validate_methods_value,
    validate_timing_value,
    validate_topics_value,
)
from citry.ext.events.openapi import OpenApiCommand
from citry.ext.events.routes import events_config_url, events_routes
from citry.ext.events.state import (
    StateMeta,
    build_state_instance,
    convert_state_class,
    resolve_state_meta,
    validate_state_class,
)
from citry.ext.events.view_events import view_events_routes
from citry.extension import Extension

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from citry.component import Component
    from citry.ext.dependencies.emission import OnDependenciesContext
    from citry.extension import (
        ComponentIntrospectionContext,
        OnAttrsResolvedContext,
        OnComponentClassCreatedContext,
        OnComponentDataContext,
        OnRenderCacheExportContext,
        OnRenderCacheStageContext,
        OnRenderContextMergeContext,
        OnTemplateCompiledContext,
        OnTemplateResetContext,
        StagedRenderCacheContribution,
    )
    from citry.util.routing import URLRoute


def _config_name_hint(name: str) -> str:
    """A " Did you mean ...?" suffix pointing at the closest recognized config name, or empty."""
    close = get_close_matches(name, CONFIG_NAMES, n=1, cutoff=0.7)
    return f" Did you mean {close[0]!r}?" if close else ""


# The URL builder rides the one class every component's Events config is
# woven on (design events.md 3.8: component.events.url(...) during render).
# The implementation lives with the routes it points at; attaching it here,
# where the weaving is set up, keeps the config module a pure typing surface
# and the woven class identical to the typed base.
Events.url = events_config_url  # type: ignore[attr-defined]

# The built-in defaults, the lowest of the three config levels (component
# beats extensions_defaults["events"] beats these).
_FACTORY_DEFAULTS: dict[str, Any] = {
    "_guard": None,
    "_context": None,
    "_csrf": "auto",
    "_methods": ("POST",),
    "_debounce": None,
    "_throttle": None,
    "_topics": (),
}


@dataclass(frozen=True, slots=True)
class EventHandler:
    """
    One event handler of a component, with its per-handler config resolved.

    Attributes:
        name: The wire name calls address the handler by: the method name,
            unless ``@event(name=...)`` renamed it.
        method_name: The Python method name on the ``Events`` class.
        func: The handler function as the user wrote it (unbound).
        params: The parameter names the handler declares (without ``self``),
            in signature order; each is one of the injectables.
        data_schema: The resolved ``data`` schema class, or ``None`` for a
            handler that declares no ``data``.
        methods: The allowed HTTP methods, uppercase.
        guard: The authorization callable guarding this handler, or ``None``.
        csrf: The CSRF policy: ``"auto"``, ``False``, or a callable.
        debounce: Client-side debounce in milliseconds, or ``None``.
        throttle: Client-side throttle in milliseconds, or ``None``.
        return_type_display: Safe copied return annotation text, or ``None``.
        return_type_fidelity: Whether ``return_type_display`` is normalized.
        description: The handler's cleaned docstring, or ``None``.

    """

    name: str
    method_name: str
    func: Callable[..., Any]
    params: tuple[str, ...]
    data_schema: type | None
    methods: tuple[str, ...]
    guard: Callable[..., Any] | None
    csrf: str | bool | Callable[..., Any]
    debounce: int | None
    throttle: int | None
    return_type_display: str | None
    return_type_fidelity: Literal["normalized", "unavailable"]
    description: str | None


@dataclass(frozen=True, slots=True)
class EventsInfo:
    """
    Everything the ``events`` extension knows about one component class.

    Computed once at class definition (which is also when all the
    class-definition validation runs) and read back through
    ``EventsExtension.resolve``.

    Attributes:
        events_cls: The raw ``Events`` class as the user declared it (own or
            inherited); ``None`` when the component declares no events.
        state_cls: The State class after the dataclass conversion; ``None``
            when the component declares no State.
        state_meta: The resolved State meta, or ``None`` without a State.
        handlers: The event handlers in definition order, keyed by wire name.
        guard: The component-level ``_guard``, resolved through the three
            config levels; ``None`` when nothing configures one.
        context: The component-level ``_context`` hook, resolved the same
            way; ``None`` when nothing configures one.
        csrf: The component-level CSRF policy (``"auto"`` unless configured).
        methods: The component-level allowed HTTP methods, uppercase.
        debounce: The component-level debounce in milliseconds, or ``None``.
        throttle: The component-level throttle in milliseconds, or ``None``.
        topics: The v2 server-push topic templates; stored and validated,
            not yet consumed.

    """

    events_cls: type | None
    state_cls: type | None
    state_meta: StateMeta | None
    handlers: dict[str, EventHandler]
    guard: Callable[..., Any] | None
    context: Callable[..., Any] | None
    csrf: str | bool | Callable[..., Any]
    methods: tuple[str, ...]
    debounce: int | None
    throttle: int | None
    topics: tuple[str, ...]


_EVENTS_INFO_ATTR = "_citry_events_info"


def _component_events_info(component_class: type) -> EventsInfo | None:
    """Return metadata stored directly on one concrete component class."""
    value = vars(component_class).get(_EVENTS_INFO_ATTR)
    return value if isinstance(value, EventsInfo) else None


class EventsExtension(Extension):
    """
    Built-in extension that validates, serves, and renders component Events.

    Every [`Citry`][citry.Citry] instance installs this extension. It validates
    a component's ``Events`` and ``State`` declarations when the component
    class is created, contributes the Events HTTP routes, prepares declarative
    bindings, and emits the browser runtime data needed by rendered instances.

    Most applications use the nested ``class Events`` API described in
    [Server events](/events/) and never instantiate this class
    directly. Extension and tooling authors can retrieve it from the instance's
    [`ExtensionManager`][citry.ExtensionManager] to inspect resolved handler or
    State metadata.
    """

    name = "events"

    introspection_version = 1
    render_cache_mode = "payload"
    # Pre-1.0 payload corrections update version 1 in place.
    render_cache_version = 1

    Config = Events

    # The extension's CLI commands (``citry ext run events <name>``).
    commands = [OpenApiCommand]  # noqa: RUF012 - matches the Extension.commands ClassVar

    @property
    def urls(self) -> list[URLRoute]:
        """
        Return the Events routes bound to this extension's Citry instance.

        Returns:
            Routes for the client runtime, batched calls, named handlers, and
            [`ViewEvents`][citry.ext.events.ViewEvents] compatibility calls.

        """
        return [*events_routes(self.citry), *view_events_routes(self.citry)]

    def __init__(self) -> None:
        # Per-class results live on each concrete component. Metadata may hold
        # handler functions whose closures refer back to that component; a
        # class-owned cycle remains collectible after registry removal, while
        # a WeakKeyDictionary value referring to its key would not.
        # The two-way binding target fields per class, filled by the compiled-
        # node binding transform after each target is validated against _model.
        # The aggregate remains available for diagnostics and introspection.
        self._two_way_targets: WeakKeyDictionary[type, frozenset[str]] = WeakKeyDictionary()

    def validate_config_fields(self, fields: Mapping[str, Any], *, component: type[Component] | None = None) -> None:
        """
        Check declared Events config fields against the two-tier rule.

        Underscore names are configuration and must be one of the recognized
        config attributes (``_guard``, ``_context``, ``_csrf``, ``_methods``,
        ``_debounce``, ``_throttle``, ``_topics``, plus the engine-wide
        ``_max_envelope_bytes``, which only ``extensions_defaults`` may set);
        on a component's ``Events`` class an underscore ``def`` is a private
        helper and is exempt.
        Unprefixed names are event handlers: they belong on a component's
        nested ``Events`` class, so they are rejected in
        ``extensions_defaults`` (an event handler cannot be defaulted
        globally), and on the component they must be plain methods defined
        with ``def``, which is exactly what handler enumeration collects
        (design ``events.md`` 3.1). A ``staticmethod`` or ``classmethod``
        passes here so enumeration can reject it with its own pointed error;
        anything else (a ``property``, a ``functools.partial``, a plain
        value) fails here rather than sit on Events as silently neither
        handler nor config. Citry calls this at engine construction (for the
        setting) and at component class definition; see
        [`Extension.validate_config_fields`][citry.Extension.validate_config_fields].

        Args:
            fields: The declared fields, mapping field name to declared value.
            component: The component class the fields were declared on, or
                ``None`` when they come from the ``extensions_defaults``
                setting.

        Raises:
            ValueError: For an unrecognized underscore name (with a "did you
                mean" hint), an event handler in ``extensions_defaults``, or a
                handler value that is not a plain function.

        """
        for name, value in fields.items():
            if name.startswith("_"):
                # On a component's Events class, underscore defs are private
                # helpers (and _guard / _context may be written as defs).
                if component is not None and is_def_like(value):
                    continue
                if name == "_max_envelope_bytes":
                    # The envelope byte cap guards the transport before any
                    # component resolves (and a batch spans components), so
                    # it is engine-wide, never per component.
                    if component is not None:
                        msg = (
                            f"{name!r} is engine-wide configuration; set it in"
                            f" extensions_defaults['events'], not on a component's Events class."
                        )
                        raise ValueError(msg)
                    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                        msg = f"'_max_envelope_bytes' must be a positive int (a byte count); got {value!r}."
                        raise ValueError(msg)
                    continue
                if name in CONFIG_NAMES:
                    continue
                msg = (
                    f"{name!r} is not a recognized Events config attribute; the recognized"
                    f" names are: {', '.join(CONFIG_NAMES)}.{_config_name_hint(name)}"
                )
                raise ValueError(msg)
            if component is None:
                msg = (
                    f"{name!r} cannot be a global default: unprefixed names on Events are"
                    f" event handlers, and event handlers are defined on each component's"
                    f" nested Events class. Only the underscore config can be defaulted"
                    f" globally: {', '.join(CONFIG_NAMES)}.{_config_name_hint(name)}"
                )
                raise ValueError(msg)
            # Accept exactly what handler enumeration collects: plain functions
            # (public defs, design events.md 3.1). staticmethod / classmethod
            # pass through so enumeration can reject them with its own pointed
            # error; anything else (a property, a functools.partial, a plain
            # value) would be silently neither handler nor config.
            if not isinstance(value, (FunctionType, staticmethod, classmethod)):
                msg = (
                    f"{name!r} must be an event handler (unprefixed names on Events are"
                    f" handlers, and a handler is a plain method defined with 'def');"
                    f" got {value!r}. Configuration uses the underscore names:"
                    f" {', '.join(CONFIG_NAMES)}."
                )
                # ValueError, not TypeError: one exception type for the whole
                # class-definition error matrix (and what the framework's
                # wrapping call sites catch).
                raise ValueError(msg)  # noqa: TRY004

    def on_component_class_created(self, ctx: OnComponentClassCreatedContext) -> None:
        """Validate and record one component's Events and State declarations."""
        cls = ctx.component_class
        self._validate_direct_declarations(ctx)
        info = self._compute_info(cls)
        if cls.transparent and (info.events_cls is not None or info.state_cls is not None):
            msg = (
                f"Component {cls.__name__} is transparent and cannot declare Events or State:"
                " client-active instances require a component root carrying their identity marker."
            )
            raise ValueError(msg)
        type.__setattr__(cls, _EVENTS_INFO_ATTR, info)

    def inspect_component(self, ctx: ComponentIntrospectionContext) -> dict[str, object] | None:
        """
        Return public, JSON-safe Events metadata for component introspection.

        Args:
            ctx: The component-introspection request.

        Returns:
            Versioned handler metadata, or ``None`` when the component has no
            Events metadata to publish.

        Raises:
            RuntimeError: When the component was not recorded at class
                creation.

        """
        info = _component_events_info(ctx.component_class)
        if info is None:
            msg = "Events metadata was not captured when the component class was created."
            raise RuntimeError(msg)
        return inspect_events(info)

    def on_template_compiled(self, ctx: OnTemplateCompiledContext) -> list[Any]:
        """
        Validate and compile literal ``@c-*`` and ``:c-*`` bindings.

        Args:
            ctx: The compiled template body and its owning component.

        Returns:
            The body with parser-proven element bindings compiled.

        Raises:
            ValueError: When a binding names an unknown handler or State field,
                or uses an invalid modifier combination.

        """
        comp_cls = ctx.component_class
        compiled = compile_template_bindings(
            self.resolve(comp_cls),
            comp_cls.class_id,
            comp_cls.__name__,
            ctx.nodes,
        )
        self._two_way_targets[comp_cls] = self._two_way_targets.get(comp_cls, frozenset()).union(
            compiled.two_way_fields
        )
        return compiled.nodes

    def on_template_reset(self, ctx: OnTemplateResetContext) -> None:
        """Discard binding diagnostics derived from the previous compiled body."""
        self._two_way_targets.pop(ctx.component_class, None)

    def on_attrs_resolved(self, ctx: OnAttrsResolvedContext) -> dict[str, Any] | None:
        """
        Validate and compile ``@c-*`` and ``:c-*`` bindings from dynamic attrs.

        Args:
            ctx: The resolved-attribute context for one HTML element.

        Returns:
            Updated attributes, or ``None`` when the element has no Events
            binding.

        """
        # Defining this hook makes the core treat every app as having an
        # attrs-resolved subscriber, so it stops pre-computing constant element
        # attributes at compile time (component_render.py `precompute_attrs`)
        # even for apps that use no bindings. The two-stage rewrite needs this
        # render-time hook, so v1 accepts the cost; a later change could gate the
        # deopt on a component that actually carries bindings.
        comp_cls = type(ctx.component)
        return rewrite_resolved_attrs(
            self.resolve(comp_cls), comp_cls.class_id, comp_cls.__name__, ctx.tag_name, ctx.attrs
        )

    def on_component_data(self, ctx: OnComponentDataContext) -> None:
        """
        Prepare one rendered Events instance for browser activation.

        Args:
            ctx: The component-data context for the instance being rendered.

        """
        capture_instance(self, ctx)

    def on_render_context_merge(self, ctx: OnRenderContextMergeContext) -> None:
        """Merge child Events records into their parent render context."""
        # Captured instance entries bubble up exactly like the dependencies
        # extension's records, so the root context sees every instance.
        merge_instance_entries(ctx.parent_context, ctx.child_context)

    def export_render_cache(self, ctx: OnRenderCacheExportContext) -> dict[str, object]:
        return export_events_cache(self, ctx)

    def stage_render_cache(self, ctx: OnRenderCacheStageContext) -> StagedRenderCacheContribution:
        return stage_events_cache(self, ctx)

    def on_dependencies(self, ctx: OnDependenciesContext) -> None:
        """
        Add the Events runtime and instance data to serialized dependencies.

        Args:
            ctx: The dependencies context for the render being serialized.

        """
        emit_events_dependencies(self, ctx)

    def two_way_binding_targets(self, comp_cls: type[Component]) -> frozenset[str]:
        """
        The State fields bound two-way in a component's template.

        Populated when the template first compiles, so it is empty for a
        component whose template has not been compiled yet or that has no
        two-way bindings. Each individual target was already validated against
        ``_model`` during compilation; this aggregate is exposed for
        diagnostics and introspection.

        Args:
            comp_cls: The component class to look up.

        Returns:
            The two-way bound State field names (empty when none).

        """
        return self._two_way_targets.get(comp_cls, frozenset())

    def resolve(self, comp_cls: type[Component]) -> EventsInfo:
        """
        The events info of a component class: handlers, State, resolved config.

        Args:
            comp_cls: The component class to look up.

        Returns:
            The resolved handler, State, and configuration record computed
            when the class was defined.

        """
        info = _component_events_info(comp_cls)
        if info is None:
            # Defensive: normally computed at class creation; recompute for a
            # class that predates this extension instance.
            info = self._compute_info(comp_cls)
            type.__setattr__(comp_cls, _EVENTS_INFO_ATTR, info)
        return info

    def build_state(self, component: Component) -> Any:
        """
        Build the State instance for the component instance being rendered.

        Uses the component's own ``state_data(kwargs, slots)`` when it
        defines one (returning the State instance or a dict for it);
        otherwise derives the State from same-named kwargs, with State-field
        defaults filling the gaps.

        Args:
            component: The component instance being rendered.

        Returns:
            The State instance, or ``None`` when the component declares no
            State class.

        Raises:
            ValueError: When a State field has neither a matching kwarg nor
                a default, or when ``state_data()`` returns something other
                than the State or a dict.

        """
        comp_cls = type(component)
        info = self.resolve(comp_cls)
        if info.state_cls is None:
            return None
        comp_name = comp_cls.__name__
        state_data = getattr(component, "state_data", None)
        if callable(state_data):
            result = state_data(component.kwargs, component.slots)
            if result is None:
                msg = (
                    f"Component {comp_name}: state_data() returned None; return the State"
                    f" instance ({comp_name}.State(...)) or a dict of its fields."
                )
                raise ValueError(msg)
            if isinstance(result, dict):
                return info.state_cls(**result)
            if isinstance(result, info.state_cls):
                return result
            msg = (
                f"Component {comp_name}: state_data() must return the State instance"
                f" ({comp_name}.State(...)) or a dict of its fields; got {type(result).__name__}."
            )
            raise ValueError(msg)
        return build_state_instance(comp_name, info.state_cls, component.raw_kwargs)

    # ----- Capture and validation (class definition time) -----

    def _validate_direct_declarations(self, ctx: OnComponentClassCreatedContext) -> None:
        """Validate non-class values written directly on this component."""
        cls = ctx.component_class
        comp_name = cls.__name__
        events_declaration = next(
            (item for item in ctx.nested_declarations("Events") if item.declaring_class is cls),
            None,
        )
        if events_declaration is not None:
            declared = events_declaration.value
            if declared is not None and not isinstance(declared, type):
                msg = (
                    f"Component {comp_name}: 'Events' must be a class (or None to declare"
                    f" no events); got {declared!r}."
                )
                raise ValueError(msg)
        state_declaration = next(
            (item for item in ctx.nested_declarations("State") if item.declaring_class is cls),
            None,
        )
        if state_declaration is not None:
            declared_state = state_declaration.value
            if declared_state is not None and not isinstance(declared_state, type):
                msg = (
                    f"Component {comp_name}: 'State' must be a class (or None to declare"
                    f" no state); got {declared_state!r}."
                )
                raise ValueError(msg)

    def _effective_events_class(self, cls: type[Component]) -> type | None:
        """Build the user-authored Events class with automatic C3 inheritance."""
        declarations = _active_nested_class_declarations(cls, "Events")
        if not declarations:
            return None
        first_owner = declarations[0].declaring_class
        inherited = _component_events_info(first_owner)
        if (
            first_owner is not cls
            and inherited is not None
            and declarations == _active_nested_class_declarations(first_owner, "Events")
        ):
            return inherited.events_cls
        return _compose_nested_declaration_class(cls, "Events")

    def _effective_state(self, cls: type[Component]) -> tuple[type, StateMeta] | None:
        """Build and convert the effective State declaration for this component."""
        declarations = _active_nested_class_declarations(cls, "State")
        if not declarations:
            return None
        first_owner = declarations[0].declaring_class
        inherited = _component_events_info(first_owner)
        if (
            first_owner is not cls
            and inherited is not None
            and inherited.state_cls is not None
            and inherited.state_meta is not None
            and declarations == _active_nested_class_declarations(first_owner, "State")
        ):
            return inherited.state_cls, inherited.state_meta

        declaration = _compose_nested_declaration_class(cls, "State")
        declaration = cast("type", declaration)
        comp_name = cls.__name__
        validate_state_class(comp_name, declaration)
        converted = convert_state_class(comp_name, declaration)
        meta = resolve_state_meta(comp_name, declaration, converted)
        type.__setattr__(cls, "State", converted)
        return converted, meta

    def _compute_info(self, cls: type[Component]) -> EventsInfo:
        comp_name = cls.__name__
        raw_events = self._effective_events_class(cls)
        state_entry = self._effective_state(cls)
        state_cls, state_meta = state_entry if state_entry is not None else (None, None)

        # state_data with nothing to build is a latent bug; fail at class
        # definition rather than silently never calling it. Only the class's
        # own def counts: a subclass that opts out with ``State = None`` keeps
        # its parent's inherited state_data, which is simply never called.
        if state_cls is None and callable(cls.__dict__.get("state_data")):
            msg = (
                f"Component {comp_name} defines state_data() but declares no State class."
                f" Declare a State class on the component (or remove state_data)."
            )
            raise ValueError(msg)

        defaults = self.citry.settings.extensions_defaults.get("events", {})
        guard = validate_callable_value(
            f"Component {comp_name}: Events._guard",
            self._resolve_config_value(raw_events, "_guard", defaults),
        )
        context = validate_callable_value(
            f"Component {comp_name}: Events._context",
            self._resolve_config_value(raw_events, "_context", defaults),
        )
        csrf = validate_csrf_value(
            f"Component {comp_name}: Events._csrf",
            self._resolve_config_value(raw_events, "_csrf", defaults),
        )
        methods = validate_methods_value(
            f"Component {comp_name}: Events._methods",
            self._resolve_config_value(raw_events, "_methods", defaults),
        )
        debounce = validate_timing_value(
            f"Component {comp_name}: Events._debounce",
            self._resolve_config_value(raw_events, "_debounce", defaults),
        )
        throttle = validate_timing_value(
            f"Component {comp_name}: Events._throttle",
            self._resolve_config_value(raw_events, "_throttle", defaults),
        )
        state_fields = tuple(f.name for f in fields(state_cls)) if state_cls is not None else None
        topics = validate_topics_value(
            f"Component {comp_name}: Events._topics",
            self._resolve_config_value(raw_events, "_topics", defaults),
            state_fields,
        )

        handlers: dict[str, EventHandler] = {}
        if raw_events is not None:
            for method_name, func in collect_event_handlers(comp_name, raw_events).items():
                params = validate_handler_signature(comp_name, method_name, func, has_state=state_cls is not None)
                data_schema = resolve_data_schema(cls, method_name, func) if "data" in params else None
                options = event_options(func)
                wire_name = options.name if options is not None and options.name is not None else method_name
                if wire_name in handlers:
                    msg = (
                        f"Component {comp_name}: two event handlers share the wire name"
                        f" {wire_name!r} ({handlers[wire_name].method_name!r} and {method_name!r})."
                        f" Wire names must be unique per component; change the @event(name=...)"
                        f" override."
                    )
                    raise ValueError(msg)
                return_type_display, return_type_fidelity, description = capture_handler_introspection(func)
                handlers[wire_name] = EventHandler(
                    name=wire_name,
                    method_name=method_name,
                    func=func,
                    params=params,
                    data_schema=data_schema,
                    methods=options.methods if options is not None and options.methods is not None else methods,
                    guard=options.guard if options is not None and options.guard is not None else guard,
                    csrf=options.csrf if options is not None and options.csrf is not None else csrf,
                    debounce=options.debounce if options is not None and options.debounce is not None else debounce,
                    throttle=options.throttle if options is not None and options.throttle is not None else throttle,
                    return_type_display=return_type_display,
                    return_type_fidelity=return_type_fidelity,
                    description=description,
                )

        return EventsInfo(
            events_cls=raw_events,
            state_cls=state_cls,
            state_meta=state_meta,
            handlers=handlers,
            guard=guard,
            context=context,
            csrf=csrf,
            methods=methods,
            debounce=debounce,
            throttle=throttle,
            topics=topics,
        )

    def _resolve_config_value(self, raw_events_cls: type | None, name: str, defaults: Mapping[str, Any]) -> Any:
        """
        One config attribute through the three levels.

        The component level is what the user's own Events classes declare
        (framework base classes never count, so precedence cannot be skewed
        by subclassing the typed base); below that,
        ``extensions_defaults["events"]``, then the built-in default.
        """
        if raw_events_cls is not None:
            for klass in user_level_classes(raw_events_cls):
                if name in vars(klass):
                    return vars(klass)[name]
        if name in defaults:
            return defaults[name]
        return _FACTORY_DEFAULTS[name]
