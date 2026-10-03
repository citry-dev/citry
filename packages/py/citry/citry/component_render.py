"""
Component render pipeline.

This module contains the core rendering logic. When a CitryElement is
rendered (via ``.render()``), it calls ``render_impl`` which:

1. Creates a real Component instance (via ``_create_instance``), which
   normalizes inputs and sets instance state (id, kwargs, slots, parent, root)
2. Calls ``template_data()`` and validates it against ``TemplateData``
3. Builds a ``CitryContext`` (the render-scoped state) and the template body
   (a node list), walks the body into a parts list, and returns a
   ``CitryRender`` wrapping the parts plus the context

``render_impl`` returns a ``CitryRender`` (not a string). Serialization to HTML
happens later, via ``CitryRender.serialize()`` (or ``str()``). See
docs/design/component_rendering.md for the three-phase model.

The slow step, compiling the template (parse + compile + exec) into a
body-generating function, runs once per **component class** and is cached on
the class, since it is the same for a given template. On top of that sits the
``Const`` optimization: parts of the template that depend only on inputs
marked ``Const()`` ("same value on every render") are computed once and the
result is cached per component class and per set of ``Const`` values, so
repeat renders skip that work. See docs/design/component_constness.md and
citry/constness.py.

Rendering is deferred and stack-driven, so nesting depth is not tied to
Python's recursion limit; ``CitrySettings.max_component_depth`` bounds it
instead, so a component that renders itself forever fails fast. Rendering also
collects each component's JS/CSS dependencies, and drives the ``on_render``
hook; see docs/design/component_rendering_defer.md and component_on_render.md. Django's
context snapshotting is deliberately not ported: a component receives only
its own props and slots, never an inherited context.
"""

from __future__ import annotations

import abc
from contextlib import nullcontext
from contextvars import ContextVar
from dataclasses import dataclass, replace
from difflib import get_close_matches
from inspect import getattr_static
from typing import TYPE_CHECKING, Any, NamedTuple, NoReturn, cast

from citry._class_introspection import _component_declaration_generation, _static_class_dict, _static_class_mro
from citry._pure import (
    PureBodyPlan,
    PureInteriorBody,
    PureLiveBodyItem,
    PurePreparedPart,
    pure_body_cache_scope,
    pure_body_lookup,
    store_pure_body,
)
from citry._vue.capture import (
    PreparedTextValue,
    PreparedTrustedHtmlValue,
    coalesce_prepared_static_nodes,
    prepared_render_active,
    typed_render_scope,
    vue_render_active,
)
from citry._vue.direct import direct_render_scope
from citry.assets import _TEMPLATE_CACHE, load_template
from citry.citry_context import CitryContext
from citry.citry_element import CitryElement, _PreparedCallMetadata
from citry.citry_render import (
    _VALUE_CONTEXT,
    CitryRender,
    DeferredComponent,
    RenderFrame,
    SimpleVueRecord,
    _after_render_hooks_scope,
    _render_slot_value,
)
from citry.citry_template import CitryTemplate, DeclaredSlot
from citry.client_directives import CLIENT_PROPS_ATTR, validate_client_props_target
from citry.component_like import ComponentLike, _component_like_render_scope, _resolve_component_like
from citry.components.mark import reject_repeated_mark_names
from citry.constness import (
    _const_mapping,
    _ConstMapping,
    _construct_data_schema,
    _merge_const_mappings,
    _normalize_data_schema_instance,
    _refresh_const_mapping,
    _restore_const_identities,
    const_value,
    extract_const_vars,
    precompute_const_parts,
)
from citry.nodes import (
    ComponentNode,
    ElementAttrsNode,
    ElementKeyNode,
    ExprHtmlAttr,
    ExprNode,
    FillDataBinding,
    FillNode,
    ForeignHtmlAttr,
    ForeignNode,
    ForNode,
    IfNode,
    SlotNode,
    StaticHtmlAttr,
    TemplateHtmlAttr,
)
from citry.slots import Slot
from citry.util.exception import (
    set_component_error_message,
    set_template_origin_error_message,
    set_template_position_error_message,
)
from citry.util.html import Markup, escape
from citry.util.id import gen_render_id, validate_render_id
from citry.util.logger import is_tracing, trace_component_msg, trace_node_msg
from citry.util.misc import get_fields, is_generator, to_dict
from citry_core.template_parser import ForeignSpan, ParseOptions, compile_template, parse_template

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence
    from contextlib import AbstractContextManager

    from citry._vue.direct import DirectExecutionFrame
    from citry._vue.leaf_program import LeafCallChildren, LeafProgramNode, PreparedLeafProgram
    from citry.assets import HasHtml
    from citry.citry_render import OnRenderGenerator, RenderPart, RenderReplacement
    from citry.component import Component
    from citry.nodes import BodyItem, Node
    from citry_core.template_parser import TagRules


# Per-render template globals: the variables passed to a single render through
# Component.render(template_globals=...). Held in a context variable because the
# value is the same for the whole render and must reach every nested render
# (deferred children, embedded {{ element }} values, slot content) without being
# threaded through each node and slot; a concurrent render on another thread or
# task keeps its own value. None means no per-render override was given.
_render_globals: ContextVar[dict[str, Any] | None] = ContextVar("citry_render_globals", default=None)


@dataclass(frozen=True, slots=True)
class _SimpleVueAdmission:
    """
    The per-class answer to "can a ``simple='vue'`` call skip the Component instance".

    Every call of the same class would otherwise repeat the same checks: the
    scan of the class and its bases, the nested declarations, the dependency lists, the extension
    hooks, and the template plan. ``_simple_vue_admission`` computes this record
    once and reuses it while every input it read is unchanged; see
    ``_simple_vue_admission_key`` for that list.
    """

    # The engine and class state this record was computed from.
    key: tuple[object, ...]
    # The loaded template the plan was built from; compared by identity.
    template: CitryTemplate | None
    # A reason the class itself is incompatible with simple='vue', or None.
    rejection: str | None
    # The engine (not the class) needs the ordinary render path for this class.
    renders_ordinarily: bool
    # The static data callbacks to call, or None where the class keeps the
    # base default (kwargs as template data, no js_data or css_data).
    template_data_callback: Callable[[Any, dict[str, Any]], Any] | None
    js_data_callback: Callable[[Any, dict[str, Any]], Any] | None
    css_data_callback: Callable[[Any, dict[str, Any]], Any] | None
    # The admitted evaluator for the class template; None when not admitted.
    leaf_node: LeafProgramNode | None
    # Whether the class declares any secondary Dependencies at all.
    has_dependencies: bool
    # Each plain (non-component) base between the class and Component, with
    # its namespace values at computation time. Writes to these classes do
    # not move the component declaration count, so each call compares them.
    plain_bases: tuple[tuple[type, tuple[tuple[str, object], ...]], ...] = ()


# The class attribute that holds a class's admission record. Keeping the
# record on the class (instead of a module-level table) lets the class and the
# callbacks the record holds be collected together. It is written with
# type.__setattr__, so storing it does not count as a declaration change.
_SIMPLE_VUE_ADMISSION_ATTR = "_citry_simple_vue_admission"


def _reject_simple_vue(component_class: type[Any], reason: str) -> NoReturn:
    """Raise the named error for a class or call that cannot use ``simple='vue'``."""
    raise TypeError(f"Component {component_class.__name__} simple='vue' is unsupported: {reason}.")


def _simple_vue_admission_key(component_class: type[Component]) -> tuple[object, ...]:
    """
    Snapshot everything outside the template that an admission record depends on.

    A record is reused only while this tuple compares equal, so each entry
    names one way the answer can change:

    - the component declaration count moves when any component class assigns
      or deletes an authored attribute after definition;
    - the extension manager and its extension tuple identify the installed
      extensions and, through them, the hook dispatch cache;
    - the Cache extension revision moves on ``reset_template()``,
      ``reset_files()``, ``Citry.clear()`` and alias removal;
    - the i18n registry generation moves when a component registers or
      unregisters, when message sources load or reload, and on clear;
    - ``abc.get_cache_token()`` moves when any class is registered as
      ``ComponentLike`` (or with any other ABC), which changes value dispatch.

    The loaded template is compared separately, by identity.
    """
    extensions = component_class.citry.extensions
    by_name = extensions._extensions_by_name
    i18n = by_name.get("i18n")
    return (
        _component_declaration_generation(),
        extensions,
        extensions._extensions,
        cast("Any", by_name["cache"])._revision,
        None if i18n is None else cast("Any", i18n)._registry_generation,
        abc.get_cache_token(),
    )


def _simple_vue_admission(component_class: type[Component]) -> _SimpleVueAdmission:
    """Return the current admission record for a ``simple='vue'`` class, rebuilding it when stale."""
    key = _simple_vue_admission_key(component_class)
    namespace = vars(component_class)
    admission = cast("_SimpleVueAdmission | None", namespace.get(_SIMPLE_VUE_ADMISSION_ATTR))
    # A reset or reload replaces the class's loaded template object, so the
    # identity check catches template changes the key tuple does not cover.
    if (
        admission is not None
        and admission.key == key
        and admission.template is namespace.get(_TEMPLATE_CACHE)
        and _plain_bases_unchanged(admission.plain_bases)
    ):
        return admission
    admission = _compute_simple_vue_admission(component_class, key)
    type.__setattr__(component_class, _SIMPLE_VUE_ADMISSION_ATTR, admission)
    return admission


def _plain_base_snapshot(base: type) -> tuple[tuple[str, object], ...]:
    """Record a plain base's namespace so a later write to it can be detected."""
    return tuple(_static_class_dict(base).items())


def _plain_bases_unchanged(plain_bases: tuple[tuple[type, tuple[tuple[str, object], ...]], ...]) -> bool:
    """Whether every recorded plain base still has the same names bound to the same objects."""
    # Most components have no plain bases, so this loop usually does nothing.
    for base, snapshot in plain_bases:
        current = _static_class_dict(base)
        if len(current) != len(snapshot):
            return False
        for name, value in snapshot:
            if current.get(name, _MISSING_MEMBER) is not value:
                return False
    return True


# Distinguishes a deleted member from one bound to None.
_MISSING_MEMBER = object()


def _compute_simple_vue_admission(
    component_class: type[Component],
    key: tuple[object, ...],
) -> _SimpleVueAdmission:
    """
    Run every class-level ``simple='vue'`` check once.

    Checks run in two groups. The first group looks only at what the class
    declares (members, nested declarations, messages, dependencies, data
    callbacks, template); a failure there is recorded as a rejection so each
    call raises the same named error. The second group looks at engine state
    the class does not control (extension hooks and i18n settings); a failure
    there makes the calls render as ordinary components instead.
    """
    from types import FunctionType  # noqa: PLC0415

    from citry._nested_declarations import _get_nested_class_declarations  # noqa: PLC0415
    from citry._vue.leaf_program import compile_leaf_program  # noqa: PLC0415
    from citry.assets import _find_pair_declaration  # noqa: PLC0415
    from citry.component import Component as ComponentBase  # noqa: PLC0415
    from citry.ext.dependencies.extension import DependenciesExtension  # noqa: PLC0415
    from citry.ext.events.extension import EventsExtension  # noqa: PLC0415
    from citry.ext.i18n.extension import I18nExtension  # noqa: PLC0415

    # Component subclasses report their own writes through the declaration
    # count; plain bases do not, so the namespaces of the plain bases the scan
    # below reads (those before Component in the MRO) are recorded instead.
    mro = _static_class_mro(component_class)
    scanned_bases = mro[: mro.index(ComponentBase)] if ComponentBase in mro else mro
    plain_bases = tuple(
        (base, _plain_base_snapshot(base)) for base in scanned_bases if not isinstance(base, type(ComponentBase))
    )

    def rejected(reason: str, template: CitryTemplate | None = None) -> _SimpleVueAdmission:
        return _SimpleVueAdmission(
            key=key,
            template=template,
            rejection=reason,
            renders_ordinarily=False,
            template_data_callback=None,
            js_data_callback=None,
            css_data_callback=None,
            leaf_node=None,
            has_dependencies=False,
            plain_bases=plain_bases,
        )

    class_metadata = {
        _SIMPLE_VUE_ADMISSION_ATTR,
        "__module__",
        "__doc__",
        "__qualname__",
        "__dict__",
        "__weakref__",
        "__annotations__",
        "__classcell__",
        "__slots__",
        "__firstlineno__",
        "__static_attributes__",
        "__type_params__",
    }
    static_data_callbacks = {"template_data", "js_data", "css_data"}
    unsupported_instance_members = {
        "on_render",
        "on_component_input",
        "on_component_rendered",
        "on_dependencies",
        "provide",
        "unprovide",
        "inject",
    }
    # Every authored member between the class and Component must be data,
    # a nested class, or a plain static function; anything that needs an
    # instance cannot run without one.
    for base in _static_class_mro(component_class):
        if base is ComponentBase:
            break
        for member, value in _static_class_dict(base).items():
            if member in class_metadata:
                continue
            if member in unsupported_instance_members or member.startswith("on_"):
                return rejected(f"instance member {member} is not supported")
            if member in static_data_callbacks:
                continue
            if type(value) is staticmethod:
                if type(value.__func__) is FunctionType:
                    continue
                return rejected(f"static member {member} must wrap a Python function")
            if isinstance(value, type):
                continue
            if type(value) in (FunctionType, classmethod, property):
                return rejected(f"instance member {member} is not supported")
            if any("__get__" in _static_class_dict(value_type) for value_type in _static_class_mro(type(value))):
                return rejected(f"descriptor {member} is not supported")

    for declaration_name in ("Events", "Cache", "I18n", "State"):
        if _get_nested_class_declarations(component_class, declaration_name):
            return rejected(f"{declaration_name} configuration is not supported")
    if _get_nested_class_declarations(component_class, "Slots"):
        slots_fields = get_fields(component_class.Slots) if component_class.Slots is not None else []
        if slots_fields is None or slots_fields:
            return rejected("nonempty Slots configuration is not supported")
    # Messages on this class (or a base) would need the per-instance i18n
    # collector. Messages on some other registered class are engine state and
    # are handled with the extension hooks below.
    _messages_owner, inline_messages, messages_file = _find_pair_declaration(
        component_class, "messages", "messages_file"
    )
    if inline_messages is not None or messages_file is not None:
        return rejected("component messages are not supported")
    dependencies = component_class.get_dependencies()
    # A media type with no entries declares no stylesheet, so check the
    # entries rather than the mapping itself.
    if any(dependencies.css.values()):
        return rejected("secondary CSS dependencies are unsupported for simple='vue'")
    if dependencies.js:
        return rejected("secondary JavaScript dependencies are unsupported for simple='vue'")

    template_data_member: object | None = None
    js_data_member: object | None = None
    css_data_member: object | None = None
    for base in _static_class_mro(component_class):
        base_namespace = _static_class_dict(base)
        if template_data_member is None and "template_data" in base_namespace:
            template_data_member = base_namespace["template_data"]
        if js_data_member is None and "js_data" in base_namespace:
            js_data_member = base_namespace["js_data"]
        if css_data_member is None and "css_data" in base_namespace:
            css_data_member = base_namespace["css_data"]
        if template_data_member is not None and js_data_member is not None and css_data_member is not None:
            break
    if template_data_member is not ComponentBase.template_data and type(template_data_member) is not staticmethod:
        return rejected("template_data must use the base default or be declared as a static method")
    for callback_name, callback_member, base_callback in (
        ("js_data", js_data_member, ComponentBase.js_data),
        ("css_data", css_data_member, ComponentBase.css_data),
    ):
        if callback_member is not base_callback and type(callback_member) is not staticmethod:
            return rejected(f"{callback_name} must use the base default or be declared as a static method")

    compiled = _get_compiled_template(component_class, prepared=True)
    if compiled is None or compiled.prepared_generate is None:
        return rejected("a prepared template is required", compiled)
    extensions = component_class.citry.extensions
    # The plan depends on how extensions transform the compiled template, so
    # its cache key names each extension's template hooks.
    extension_key = tuple(
        (
            id(extension),
            getattr(type(extension), "on_template_foreign_compiled", None),
            getattr(type(extension), "on_template_compiled", None),
            getattr(type(extension), "on_attrs_resolved", None),
        )
        for extension in extensions._extensions
    )
    plan_key = (
        "simple-vue-leaf-calls",
        compiled.template_id,
        compiled.origin,
        compiled.kind,
        extension_key,
    )
    # The plan is stored on the loaded template, so a rebuilt admission for an
    # unchanged template and extension set reuses it and on_template_compiled
    # runs once per plan.
    with compiled.compile_lock:
        cached_plan = compiled.prepared_standalone_bodies.get(plan_key)
        if cached_plan is None:
            generated = compiled.prepared_generate()
            foreign_resolved = extensions.on_template_foreign_compiled(
                component_class,
                generated,
                provider_metadata=compiled.foreign_provider_metadata,
                template_id=compiled.template_id,
                origin=compiled.origin,
                template_kind=compiled.kind,
            )
            transformed = extensions.on_template_compiled(
                component_class,
                foreign_resolved,
                template_id=compiled.template_id,
                origin=compiled.origin,
                template_kind=compiled.kind,
            )
            typed = coalesce_prepared_static_nodes(transformed)
            compiled_leaf = compile_leaf_program(typed, allow_static_only=True, allow_calls=True)
            cached_plan = (
                [compiled_leaf]
                if compiled_leaf is not None and compiled_leaf.static_instance_free_template_supported()
                else []
            )
            compiled.prepared_standalone_bodies[plan_key] = cached_plan
            compiled.prepared_standalone_bodies.move_to_end(plan_key)
            while len(compiled.prepared_standalone_bodies) > 64:
                compiled.prepared_standalone_bodies.popitem(last=False)
        else:
            compiled.prepared_standalone_bodies.move_to_end(plan_key)
    if len(cached_plan) != 1:
        # `#c-ignore` keeps its contents through the component's own Vue
        # instance, which a simple component does not have. Name it, because
        # the generic reason below does not mention it.
        if "#c-ignore" in compiled.source:
            return rejected(
                "`#c-ignore` needs a component instance to keep its contents; "
                'remove `simple = "vue"` from this component, or remove `#c-ignore`',
                compiled,
            )
        return rejected(
            "the template uses slots, a child call that passes content, c-bind or Vue bindings, "
            "or an expression the instance-free renderer cannot evaluate",
            compiled,
        )
    leaf_node = cast("LeafProgramNode", cached_plan[0])

    # Engine state from here on. Only the built-in extensions are known to
    # leave an instance-free render unchanged; the i18n extension qualifies
    # only while no catalog can apply to this render.
    def known_lifecycle_hook(extension: object, hook_name: str) -> bool:
        extension_type = type(extension)
        implementation = getattr(extension_type, hook_name, None)
        if extension_type is DependenciesExtension:
            return implementation is getattr(DependenciesExtension, hook_name, None)
        if extension_type is EventsExtension:
            return implementation is getattr(EventsExtension, hook_name, None)
        if extension_type is I18nExtension:
            i18n = cast("I18nExtension", extension)
            return (
                implementation is getattr(I18nExtension, hook_name, None)
                and not i18n.configured
                and not i18n._has_registered_message_source()
            )
        return False

    renders_ordinarily = any(
        not known_lifecycle_hook(extension, hook_name)
        for hook_name in (
            "on_component_input",
            "on_component_data",
            "on_component_rendered",
            "on_render_context_merge",
        )
        for extension in extensions._extensions_with_hook(hook_name)
    ) or not leaf_node.static_instance_free_hooks_supported(extensions)

    return _SimpleVueAdmission(
        key=key,
        template=compiled,
        rejection=None,
        renders_ordinarily=renders_ordinarily,
        template_data_callback=_static_data_callback(template_data_member),
        js_data_callback=_static_data_callback(js_data_member),
        css_data_callback=_static_data_callback(css_data_member),
        leaf_node=leaf_node,
        has_dependencies=bool(dependencies),
        plain_bases=plain_bases,
    )


def _static_data_callback(member: object) -> Callable[[Any, dict[str, Any]], Any] | None:
    """Unwrap an admitted staticmethod; the base default method maps to None."""
    if type(member) is staticmethod:
        return cast("Callable[[Any, dict[str, Any]], Any]", member.__func__)
    return None


def _simple_vue_renders_ordinarily(component_class: type[Component]) -> bool:
    """Whether engine state sends this admitted ``simple='vue'`` class through ordinary rendering."""
    admission = _simple_vue_admission(component_class)
    return admission.rejection is None and admission.renders_ordinarily


def _render_simple_vue_leaf(
    element: CitryElement,
    parent_context: CitryContext,
) -> SimpleVueRecord | None:
    """
    Render one admitted ``simple='vue'`` occurrence without a Python Component.

    Returns None for a class that is not ``simple='vue'``, and also when
    engine state (an extension hook, configured i18n, or messages on another
    registered component) requires the ordinary path. That decision is made
    before the render ID or any data callback, so the ordinary render that
    follows runs each callback exactly once.
    """
    component_class = element.comp_cls
    if component_class.simple != "vue":
        return None

    from citry.ext.dependencies.emission import EXTRA_KEY  # noqa: PLC0415
    from citry.ext.dependencies.extension import _DependencyCacheCapture  # noqa: PLC0415
    from citry.ext.dependencies.scripts import has_component_asset  # noqa: PLC0415
    from citry.ext.dependencies.types import DependencyRecord  # noqa: PLC0415

    try:
        # The call shape belongs to this invocation, so it is checked every time.
        if (
            type(element) is not CitryElement
            or component_class.transparent
            or component_class.pure
            or component_class._citry_dynamic_selector
            or element.slots
            or element.component_tag_client_bindings
            or element.element_morph_metadata is not None
        ):
            _reject_simple_vue(
                component_class,
                "calls must be registered, nontransparent leaf components without slots, component-tag bindings, "
                "or instance effects",
            )
        # Registration can change between calls without touching any key the
        # admission record watches, so identity is checked every time.
        if component_class.citry.get_component_by_class_id(component_class.class_id) is not component_class:
            _reject_simple_vue(component_class, "the component must remain registered in its owning Citry instance")

        admission = _simple_vue_admission(component_class)
        if admission.rejection is not None:
            _reject_simple_vue(component_class, admission.rejection)

        metadata = element.prepared_call_metadata
        if metadata is None:
            # Only a direct root call carries no call metadata.
            if parent_context.component is not None:
                _reject_simple_vue(component_class, "a template-authored, slot-free component call is required")
        elif type(metadata) is not _PreparedCallMetadata or metadata.slot_free_body is not True:
            _reject_simple_vue(component_class, "a template-authored, slot-free component call is required")
        elif parent_context.component is None and not metadata.simple_vue_callers:
            # With no component around it, a template call can only come
            # from a simple='vue' template, which names its callers.
            _reject_simple_vue(component_class, "a direct root call cannot carry child-call metadata")

        # Engine state needs the ordinary path. Nothing observable has run
        # yet, so the caller renders this call as a regular component.
        if admission.renders_ordinarily:
            return None
        leaf_node = cast("LeafProgramNode", admission.leaf_node)

        # Match Component.__init__: allocate and validate the render ID before
        # the typed schema can reject this occurrence.
        render_id = (
            component_class.citry.id_generator() if component_class.citry.id_generator is not None else gen_render_id()
        )
        render_id = validate_render_id(render_id)
        kwargs, _kwargs_const = _construct_data_schema(
            element.kwargs,
            component_class.Kwargs,
            provenance_only=True,
        )
        # Callbacks run in the ordinary order: template_data, js_data, css_data.
        template_data_callback = admission.template_data_callback
        template_data = kwargs if template_data_callback is None else template_data_callback(kwargs, {})
        template_data = _normalize_data(template_data, component_class.TemplateData)
        js_data_callback = admission.js_data_callback
        js_data = _normalize_data(
            None if js_data_callback is None else js_data_callback(kwargs, {}),
            component_class.JsData,
        )
        # This path skips on_component_data, so the callback's own keys are
        # the final ones the browser will receive.
        _check_js_data_keys(component_class, js_data)
        css_data_callback = admission.css_data_callback
        css_data = _normalize_data(
            None if css_data_callback is None else css_data_callback(kwargs, {}),
            component_class.CssData,
        )
        instance_globals = component_class.citry.template_globals
        render_globals = _render_globals.get()
        if instance_globals or render_globals:
            template_data = _merge_const_mappings(
                _const_mapping(instance_globals),
                _const_mapping(render_globals or {}),
                template_data,
            )
        variables = dict(template_data)
        calls: dict[tuple[int, str], tuple[Any, dict[str, object], str | None]] | None = (
            {} if leaf_node.fragment.calls else None
        )
        leaf = leaf_node.render_static_instance_free(
            variables,
            component_name=component_class.__name__,
            calls=calls,
        )
        if calls is not None:
            _defer_simple_vue_calls(
                component_class,
                leaf,
                calls,
                parent_context,
                metadata,
                admission,
            )

        css_capture = None
        if css_data:
            from citry.ext.dependencies.scripts import _cache_component_css_vars_capture  # noqa: PLC0415

            css_capture = _cache_component_css_vars_capture(component_class, css_data)
        css_vars_hash = None if css_capture is None else css_capture.variables_hash
        has_js_asset = has_component_asset("js", component_class)
        has_css_asset = has_component_asset("css", component_class)
        # The parent owns the dependency set, so this record goes in at the
        # position where an ordinary child render would have merged it.
        if has_js_asset or has_css_asset or admission.has_dependencies:
            records = parent_context.extra.setdefault(EXTRA_KEY, {})
            if type(records) is not dict:
                _reject_simple_vue(component_class, "dependency records changed type during instance-free rendering")
            records[
                DependencyRecord(
                    class_id=component_class.class_id,
                    component_id=render_id,
                    css_vars_hash=css_vars_hash,
                    component_class=component_class,
                )
            ] = _DependencyCacheCapture(css=css_capture)

        return SimpleVueRecord(
            component_class=component_class,
            class_id=component_class.class_id,
            render_id=render_id,
            call_metadata=metadata,
            js_data=dict(js_data),
            leaf=leaf,
            prepared_data=leaf.prepared_data,
            css_vars_hash=css_vars_hash,
            root_markers=() if css_vars_hash is None else (f"data-ccss-{css_vars_hash}",),
        )
    except Exception as error:
        call_metadata = element.prepared_call_metadata
        callers = call_metadata.simple_vue_callers if type(call_metadata) is _PreparedCallMetadata else ()
        set_component_error_message(
            error, [*_component_path(parent_context.component), *callers, component_class.__name__]
        )
        raise


def _defer_simple_vue_calls(
    component_class: type[Component],
    leaf: PreparedLeafProgram,
    calls: dict[tuple[int, str], tuple[Any, dict[str, object], str | None]],
    parent_context: CitryContext,
    metadata: _PreparedCallMetadata | None,
    admission: _SimpleVueAdmission,
) -> None:
    """
    Turn the calls a ``simple='vue'`` template made into deferred children.

    Each child gets the same element, call metadata and provided values that
    ``ComponentNode.render`` would give it inside an ordinary parent. The
    render loop then renders it as usual, so the child's own mode decides
    how it renders. A ``simple='vue'`` parent has no Python instance, so the
    child's ``parent`` is the nearest ordinary component above it (None at
    the root); ``simple_vue_callers`` keeps the skipped names for error
    messages.
    """
    from citry._vue.direct import active_execution  # noqa: PLC0415

    children = cast("LeafCallChildren", leaf.call_children)
    registered = component_class.citry._registry._name_to_cls
    for call in leaf.fragment.calls:
        # Recorded even when the loop is empty; a name that resolves to no
        # registered class, or to a class that cannot be called here, gets
        # no loop, like ForNode.render.
        run_class = registered.get(call.node.name) if call.node.key is not None else None
        if run_class is not None and run_class.simple is not True and not run_class.transparent:
            children.run_types[call.key] = run_class.class_id
    callers = (*(() if metadata is None else metadata.simple_vue_callers), component_class.__name__)
    origin = admission.template.origin if admission.template is not None else None
    parent_component = parent_context.component
    direct_parent_execution = active_execution()
    for site, (call, kwargs, key) in calls.items():
        node = call.node
        child_class = component_class.citry.get(node.name)
        # These children do not render as a component of their own: they
        # write their HTML into their caller's template, which a simple='vue'
        # template compiled once cannot take in.
        if child_class.simple is True or child_class.transparent or child_class._citry_dynamic_selector:
            kind = "simple=True" if child_class.simple is True else "transparent or dynamic"
            _reject_simple_vue(
                component_class,
                f"its template calls {child_class.__name__}, a {kind} component that renders into its "
                "caller's template; wrap that call in an ordinary component or use an ordinary parent",
            )
        element = CitryElement(
            child_class,
            kwargs,
            {},
            prepared_call_metadata=_PreparedCallMetadata(
                node.source,
                node.position,
                key,
                origin,
                slot_free_body=True,
                simple_vue_callers=callers,
            ),
        )
        children.index[site] = len(children.parts)
        children.parts.append(
            DeferredComponent(
                element,
                cast("Component", parent_component),
                parent_context.provides,
                direct_parent_execution=direct_parent_execution,
            )
        )


def _simple_vue_child_tasks(
    record: SimpleVueRecord,
    parent_context: CitryContext,
    depth: int,
) -> list[_RenderTask]:
    """Queue the children a ``simple='vue'`` occurrence called, in template order, at ``depth``."""
    children = record.leaf.call_children
    if children is None:
        return []
    # The children's dependencies go where the record's own dependency
    # record went: the context of the nearest enclosing render.
    return [
        _RenderTask(part, _DeferredComponentPosition(children.parts, index, parent_context), depth)
        for index, part in enumerate(children.parts)
        if isinstance(part, DeferredComponent)
    ]


def render_impl(
    element: CitryElement,
    parent: Component | None = None,
    provides: dict[str, Any] | None = None,
    *,
    render_globals: dict[str, Any] | None = None,
) -> CitryRender:
    """
    Render a component and everything inside it into a finished ``CitryRender``.

    The public render entry: ``CitryElement.render`` calls it, and a composed
    element found in a ``{{ ... }}`` expression renders through it too.

    ``render_globals`` are the per-render template variables from
    ``Component.render(template_globals=...)``. They are merged into every
    component in this render, on top of the instance's ``citry.template_globals``
    and under a component's own ``template_data``. They are kept in a context
    variable for the duration of the render, so every nested render sees them
    without being passed the value. ``None`` (the default) adds no override and
    leaves any enclosing render's globals in place, so a nested ``render_impl``
    call does not disturb the render it runs inside.
    """
    value_token = _VALUE_CONTEXT.set(None)
    try:
        if element.comp_cls.simple == "vue" and parent is None:
            owner = element.comp_cls.citry
            root_context = CitryContext(
                component=None,
                provides=provides,
                sandboxed=owner.settings.sandbox_expressions,
            )
            render_token = _render_globals.set(render_globals) if render_globals is not None else None
            try:
                with _component_like_render_scope(owner):
                    record = _render_simple_vue_leaf(element, root_context)
            finally:
                if render_token is not None:
                    _render_globals.reset(render_token)
            # None means engine state needs the ordinary path; nothing ran
            # yet, so the ordinary root render below is the only render.
            if record is not None:
                root_render = CitryRender(
                    parts=[record],
                    context=root_context,
                    owner_citry=owner,
                    render_target="prepared",
                )
                if record.leaf.call_children is None:
                    return root_render
                # The children render through the ordinary render loop, in
                # the same scopes an ordinary root render sets up.
                with (
                    nullcontext() if prepared_render_active() else typed_render_scope(direct=True, vue=False),
                    direct_render_scope(),
                    _component_like_render_scope(owner),
                    pure_body_cache_scope(),
                ):
                    render_token = _render_globals.set(render_globals) if render_globals is not None else None
                    try:
                        return _settle_render(root_render, finalize_root=False)
                    finally:
                        if render_token is not None:
                            _render_globals.reset(render_token)
        if element.comp_cls.simple is True and parent is None:
            # A standalone template supplies an explicit owner for a root simple
            # call. Embedded calls already carry their actual insertion context.
            return element.comp_cls.citry.render_template(
                "{{ simple_root_value }}",
                {"simple_root_value": element},
                provides=provides,
                template_globals=render_globals,
                origin=f"<simple root {element.comp_cls.__name__}>",
            )
        target_scope: AbstractContextManager[None]
        if prepared_render_active():
            target_scope = nullcontext()
        else:
            # Rendering always captures one typed representation. Whether it is
            # consumed as static HTML or compiled for Vue is decided later by
            # serialization, without changing Python expression semantics.
            target_scope = typed_render_scope(direct=True, vue=False)
        with (
            target_scope,
            direct_render_scope(),
            _component_like_render_scope(element.comp_cls.citry),
            pure_body_cache_scope(),
        ):
            if render_globals is None:
                return _render_tree(element, parent, provides)
            token = _render_globals.set(render_globals)
            try:
                return _render_tree(element, parent, provides)
            finally:
                _render_globals.reset(token)
    finally:
        _VALUE_CONTEXT.reset(value_token)


def _render_tree(
    element: CitryElement,
    parent: Component | None = None,
    provides: dict[str, Any] | None = None,
) -> CitryRender:
    """
    Render a component and everything inside it, returning a finished CitryRender.

    Called by ``CitryElement.render()``. It renders the top component with
    ``_render_one``, which leaves each nested ``<c-child>`` as an unrendered
    ``DeferredComponent``. This function then renders those children one at a
    time, working through a list instead of calling itself, so a deeply nested
    page never hits Python's recursion limit (see
    docs/design/component_rendering_defer.md). The list has no natural end
    when a component renders itself forever, so each task carries its nesting
    depth and the loop raises ``RecursionError`` past
    ``CitrySettings.max_component_depth``.

    A component's after-render hooks run once everything inside that component
    has been rendered (so children run before their parents): first its own
    ``on_render`` generator is resumed with the settled result (it may replace
    the output, any number of times), then extensions' ``on_component_rendered``
    runs, and the child's collected dependencies are copied into its parent.

    When a component's render fails, the error travels up the component tree:
    each enclosing component's ``on_render`` generator, then extensions'
    ``on_component_rendered``, runs with the error and may swallow it by
    producing replacement output. An error nothing handles is raised from
    here, carrying the component path in its message
    (docs/design/component_on_render.md sections 5-6).

    Args:
        element: The component to render (its class, kwargs, slots, and cached
            template body).
        parent: The parent Component instance when rendering inside another
            component's template. Sets the parent/root links.
        provides: The provide/inject entries the rendered component inherits
            (see docs/design/component_provide.md). Empty for a plain user call; set
            when an element is rendered from inside another render (an
            embedded ``{{ element }}`` or slot content), so the subtree keeps
            the provides active at its render site.

    Returns:
        A finished ``CitryRender`` with every child rendered (no
        ``DeferredComponent`` parts left). Call ``.serialize()`` (or ``str()``)
        on it to get the HTML.

    """
    root = _render_one_traced(element, parent, provides)
    if root.cache_hit:
        return root.render
    return _settle_render(root.render, root.generator)


def _settle_render(
    root_render: CitryRender,
    root_generator: OnRenderGenerator | None = None,
    *,
    finalize_root: bool = True,
) -> CitryRender:
    """
    Resolve deferred components inside an existing render tree.

    ``_render_tree`` uses the normal ``finalize_root=True`` path after
    rendering the root component once. ``Slot.__str__`` uses
    ``finalize_root=False`` for a template-defined fill body: that body is an
    interior render owned by an already-rendered component, so only deferred
    descendants need rendering and finalization. The shared stack keeps both
    paths non-recursive and preserves child hooks, error boundaries, and
    dependency merging.
    """
    # We keep a stack of two kinds of work:
    #   - _RenderTask: render one deferred child, and put its result where the
    #     DeferredComponent was.
    #   - _FinalizeTask: run that child's after-render hooks and copy its
    #     dependencies into the parent.
    # When we render a child we add its _FinalizeTask first, then its own
    # children on top. We always take from the top of the stack, so a child and
    # everything inside it finish before we run the parent's _FinalizeTask. (This
    # is the approach django-components uses, but on objects instead of HTML
    # strings.)
    #
    # Each task also carries its component's nesting depth (the root is 1), so
    # data that contains itself, which would nest forever, stops at
    # max_component_depth. The depth is relative to this loop: a nested
    # _settle_render (slot text, an element in an expression, the target of a
    # <c-component>) runs inside a Python call, so Python's own recursion
    # limit already bounds that nesting. A cache hit places a stored subtree
    # without counting its levels; it was rendered once already, so it cannot
    # nest forever. Without a root component here, the components directly
    # inside root_render start at depth 1.
    child_depth = 2 if finalize_root else 1
    stack: list[_RenderTask | _FinalizeTask | _ContextMergeTask] = []
    if finalize_root:
        stack.append(
            _FinalizeTask(
                root_render,
                None,
                root_generator,
            )
        )
    stack.extend(reversed(_scan_deferred(root_render, child_depth)))

    root_result = root_render

    def commit(old: CitryRender, final: CitryRender, position: _DeferredComponentPosition | None) -> None:
        # Put a component's settled output where it belongs: at its recorded
        # position in the parent's parts (copying its collected dependencies
        # up), or as the new root result.
        nonlocal root_result
        if position is None:
            root_result = final
        else:
            from citry._vue.direct import wrap_python_composition_result  # noqa: PLC0415

            placed = wrap_python_composition_result(final)
            _replace_in_parts(position.parts, position.idx, old, placed)
            _merge_dependencies(position.parent_context, final.context)

    def requeue(
        task: _FinalizeTask,
        content: RenderReplacement,
        generator: OnRenderGenerator | None,
        *,
        hook_checkpoint: int,  # noqa: ARG001
        hook_through_order: int,  # noqa: ARG001
    ) -> None:
        # The component's on_render generator replaced its output. Render the
        # new content in its place (children deferred as usual) and finalize
        # the component again once the new content settles; the generator (if
        # still live) is then resumed with that result.
        old = task.render
        component = old.context.component
        if component is None:
            msg = "an on_render generator settled on a render that has no component."
            raise RuntimeError(msg)
        new_render = CitryRender(
            parts=_replacement_parts(content, old.context, component),
            context=old.context,
            is_component_root=old.is_component_root,
            is_transparent_root=old.frame.is_transparent_root,
        )
        if task.position is not None:
            _replace_in_parts(task.position.parts, task.position.idx, old, new_render)
        # The replacement is still this component's output, so it keeps the
        # component's depth and its children sit one level below it.
        stack.append(
            _FinalizeTask(
                new_render,
                task.position,
                generator,
                direct_parent_execution=task.direct_parent_execution,
                depth=task.depth,
            )
        )
        stack.extend(reversed(_scan_deferred(new_render, task.depth + 1)))

    def settle(task: _FinalizeTask, error: Exception | None) -> CitryRender | None:
        # Settle a component whose subtree has finished rendering (or, when
        # ``error`` is set, whose subtree failed): drive its on_render
        # generator, then run the extension hook via _finalize.
        #
        # Returns the final render to commit, or None when the generator
        # produced new content that was queued for re-processing (this task's
        # replacement finalize is then on the stack). Raises when the error,
        # incoming or raised here, was not handled, so the caller bubbles it.
        render: CitryRender | None = task.render if error is None else None
        generator = task.generator
        if error is not None:
            task.render.context._error_tainted = True
        while generator is not None:
            try:
                yielded = _send_on_render_generator(generator, (render, error), task.render.context)
            except StopIteration as stop:
                if stop.value is not None:
                    # `return <content>`: the final output; the generator is
                    # done, so the re-queued finalize carries no generator.
                    requeue(
                        task,
                        stop.value,
                        None,
                        hook_checkpoint=0,
                        hook_through_order=0,
                    )
                    return None
                # Plain `return`: keep the current result (and error).
                break
            except Exception as gen_error:  # noqa: BLE001
                # The generator raised: that becomes the component's error.
                # A fresh error gets this component's path; re-raising the
                # error it was sent keeps the original frames.
                if gen_error is not error:
                    set_component_error_message(gen_error, _component_path(task.render.context.component))
                task.render.context._error_tainted = True
                render, error = None, gen_error
                break
            if yielded is None:
                # Bare yield after the first: answer immediately with the
                # unchanged result.
                continue
            try:
                requeue(
                    task,
                    yielded,
                    generator,
                    hook_checkpoint=0,
                    hook_through_order=0,
                )
            except TypeError as bad_yield:
                # The yielded value was not renderable; deliver the failure
                # back to this generator, like any error in its content.
                set_component_error_message(bad_yield, _component_path(task.render.context.component))
                task.render.context._error_tainted = True
                render, error = None, bad_yield
                continue
            return None
        finalized = _finalize(task.render, error)
        owner = finalized.context.component
        if owner is not None and owner._citry_mark_name_repeated:
            # Two <c-mark> tags with one name rendered for this component. Every
            # fill and branch it wrote has settled by now, so check the output it
            # kept: an on_render hook or error boundary may have dropped one.
            reject_repeated_mark_names(owner, finalized)
        if finalized.frame.is_component_root and finalized.context.component is not None:
            root_markers = tuple(dict.fromkeys(finalized.context._get_root_markers()))
            # Most roots have no extra markers. Keep their immutable frame;
            # custom frame constructors and marker changes still run replacement.
            frame = finalized.frame
            if (
                root_markers
                or type(frame) is not RenderFrame
                or type(frame.root_markers) is not tuple
                or frame.root_markers
            ):
                finalized.frame = replace(finalized.frame, root_markers=root_markers)
        cache_plan = finalized.context.extra.pop("citry_cache_miss_plan", None)
        if cache_plan is not None:
            from citry.ext.cache.extension import CacheExtension  # noqa: PLC0415

            # Only the cache extension can publish the plan it staged on the miss,
            # so a foreign extension under the "cache" name must fail here rather
            # than silently drop the finished render.
            publishing_component = finalized.context.component
            if publishing_component is None:
                raise TypeError("a staged cache miss must finalize on a live component")
            cache_extension = publishing_component.citry.extensions.get_extension("cache")
            if not isinstance(cache_extension, CacheExtension):
                raise TypeError("the 'cache' extension slot must hold a CacheExtension")
            cache_extension._publish_component(cache_plan, finalized)
        return finalized

    def settle_in_invocation_region(task: _FinalizeTask, error: Exception | None) -> CitryRender | None:
        """Finalize under the direct placement captured for deferred work."""
        from citry._vue.direct import direct_execution_scope  # noqa: PLC0415

        with direct_execution_scope(task.direct_parent_execution):
            return settle(task, error)

    def bubble(error: Exception) -> None:
        # A component's render failed; give its ancestors a chance to handle
        # the error (docs/design/component_on_render.md section 5).
        #
        # The stack is pushed depth-first, so everything above an ancestor's
        # _FinalizeTask is exactly that ancestor's pending subtree work.
        # Popping to the nearest _FinalizeTask therefore discards the dead
        # output's remaining work and lands on the nearest enclosing
        # component. That component's on_render generator, then extensions,
        # may swallow the error by producing replacement output, which ends
        # the unwind. Otherwise the error continues to the next ancestor, and
        # out of render_impl at the root.
        #
        # The nesting-depth error skips this: an error boundary inside the
        # recursion would swallow it and let the next sibling recurse again,
        # so data that contains itself twice would still render exponentially
        # many components. Ending the whole render is the only bounded answer.
        if getattr(error, "_citry_nesting_limit", False):
            raise error
        while stack:
            task = stack.pop()
            if isinstance(task, _ContextMergeTask):
                continue
            if not isinstance(task, _FinalizeTask):
                continue
            try:
                final = settle_in_invocation_region(task, error)
            except Exception as unhandled:  # noqa: BLE001
                error = unhandled
                continue
            if final is not None:
                commit(task.render, final, task.position)
            # final is None: the generator queued replacement output, which
            # also ends the unwind (the component is re-processing).
            return
        raise error

    while stack:
        task = stack.pop()
        # Case: A foreign-context interior render has now had every deferred
        # descendant settled. Merge its completed extension state into the
        # enclosing context before that enclosing component finalizes.
        if isinstance(task, _ContextMergeTask):
            _merge_dependencies(task.parent_context, task.child_context)
            continue
        # Case: Render nested component
        if isinstance(task, _RenderTask):
            try:
                # Checked before any work for the child, so a runaway recursion
                # stops after max_component_depth renders instead of growing
                # memory until the process dies. bubble() raises it straight
                # out of the render; no ancestor hook can swallow it.
                if task.depth > task.deferred.element.comp_cls.citry.settings.max_component_depth:
                    raise _nesting_depth_error(task)
                from citry._vue.direct import direct_execution_scope  # noqa: PLC0415

                with direct_execution_scope(task.deferred.direct_parent_execution):
                    simple_record = _render_simple_vue_leaf(
                        task.deferred.element,
                        task.position.parent_context,
                    )
                    child = (
                        None
                        if simple_record is not None
                        else _render_one_traced(
                            task.deferred.element,
                            task.deferred.parent,
                            task.deferred.provides,
                        )
                    )
            except Exception as error:  # noqa: BLE001
                bubble(error)
                continue
            if simple_record is not None:
                _replace_in_parts(task.position.parts, task.position.idx, task.deferred, simple_record)
                # Render the children it called next, before its later
                # siblings, as an ordinary parent's children would be.
                if simple_record.leaf.call_children is not None:
                    stack.extend(
                        reversed(_simple_vue_child_tasks(simple_record, task.position.parent_context, task.depth + 1))
                    )
                continue
            if child is None:
                raise AssertionError("ordinary deferred rendering did not produce a result")
            if child.cache_hit:
                # A stored subtree is finished; its depth is not counted
                # (see the comment at the top of this function).
                _replace_in_parts(task.position.parts, task.position.idx, task.deferred, child.render)
                _merge_dependencies(task.position.parent_context, child.render.context)
                continue
            _replace_in_parts(task.position.parts, task.position.idx, task.deferred, child.render)
            stack.append(
                _FinalizeTask(
                    child.render,
                    task.position,
                    child.generator,
                    direct_parent_execution=task.deferred.direct_parent_execution,
                    depth=task.depth,
                )
            )
            stack.extend(reversed(_scan_deferred(child.render, task.depth + 1)))
        # Case: Finalize nested component
        else:
            try:
                final = settle_in_invocation_region(task, None)
            except Exception as error:  # noqa: BLE001
                bubble(error)
                continue
            if final is not None:
                commit(task.render, final, task.position)

    return root_result


class _DeferredComponentPosition(NamedTuple):
    """Where a ``DeferredComponent`` sits, so we can put its rendered result there."""

    parts: list[RenderPart]  # the list the DeferredComponent is in
    idx: int  # its position in that list (named `idx`, not `index`, so it doesn't hide tuple.index)
    parent_context: CitryContext  # the parent component's context; where this child's dependencies go


class _RenderTask(NamedTuple):
    """Render one deferred child component."""

    deferred: DeferredComponent
    position: _DeferredComponentPosition
    # How many components deep the child sits (the root component is 1);
    # checked against CitrySettings.max_component_depth before it renders.
    depth: int


class _FinalizeTask(NamedTuple):
    """Run a rendered component's after-render hooks and copy its dependencies up."""

    render: CitryRender
    position: _DeferredComponentPosition | None  # None for the top (root) component
    # The component's live on_render generator when the hook yielded; resumed
    # with the settled result when this task runs (None for most components).
    generator: OnRenderGenerator | None = None
    direct_parent_execution: DirectExecutionFrame | None = None
    # The component's nesting depth, so when its on_render replaces the
    # output, the new children queue one level below it.
    depth: int = 1


class _ContextMergeTask(NamedTuple):
    """Merge an interior render only after all of its deferred children settle."""

    parent_context: CitryContext
    child_context: CitryContext


class _InitialRender(NamedTuple):
    """The first render result plus its render-local cache decision."""

    render: CitryRender
    generator: OnRenderGenerator | None
    cache_hit: bool = False


def _scan_deferred_parts(
    parts: list[RenderPart],
    parent_context: CitryContext,
    tasks: list[_RenderTask | _ContextMergeTask],
    depth: int,
) -> bool:
    """Append child work in source order at ``depth``, merging contexts after their children."""
    initial_count = len(tasks)
    stack: list[tuple[Iterator[tuple[int, RenderPart]], list[RenderPart], CitryContext, int]] = [
        (iter(enumerate(parts)), parts, parent_context, initial_count)
    ]
    while stack:
        entries, current_parts, context, task_count = stack[-1]
        try:
            i, part = next(entries)
        except StopIteration:
            stack.pop()
            if stack and len(tasks) > task_count:
                enclosing_context = stack[-1][2]
                if context is not enclosing_context:
                    tasks.append(_ContextMergeTask(enclosing_context, context))
            continue
        if type(part) is str:
            continue
        if isinstance(part, DeferredComponent):
            tasks.append(_RenderTask(part, _DeferredComponentPosition(current_parts, i, context), depth))
        elif type(part) is SimpleVueRecord:
            # A root simple='vue' render holds its called children in its
            # leaf; they share the enclosing context. The record is already
            # rendered at this level, so its children are one level below.
            if part.leaf.call_children is not None:
                tasks.extend(_simple_vue_child_tasks(part, context, depth + 1))
        else:
            unwrapped = part
            if isinstance(unwrapped, CitryRender):
                stack.append((iter(enumerate(unwrapped.parts)), unwrapped.parts, unwrapped.context, len(tasks)))
    return len(tasks) > initial_count


def _scan_deferred(render: CitryRender, depth: int) -> list[_RenderTask | _ContextMergeTask]:
    """
    Find the child components inside ``render`` that still need rendering.

    ``depth`` is the nesting depth the found children render at, one more
    than the depth of the component that owns ``render``.

    Returns one ``_RenderTask`` per ``DeferredComponent``, descending into
    every nested ``CitryRender``. Most nested renders share this component's
    context (``<c-if>``/``<c-for>`` blocks, nested templates), but slot-fill
    content invoked during this render carries the context of the component
    that *wrote* the fill, and components inside it defer like any other, so
    cross-context renders are searched too. Descending into an embedded,
    already-completed subtree is harmless: ``render_impl`` finished its queue,
    so it contains no ``DeferredComponent`` parts.

    Each task's ``parent_context`` is the context of the nested render the
    deferred sits in: that is the lexical owner (for fill content, the
    component whose template wrote it), which is where the child's
    dependencies belong (see docs/design/component_slots.md section 8).
    """
    tasks: list[_RenderTask | _ContextMergeTask] = []
    _scan_deferred_parts(render.parts, render.context, tasks, depth)
    return tasks


def _contains_deferred(render: CitryRender) -> bool:
    """Whether a nested render still has any deferred component work."""
    pending = [render]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in seen:
            continue
        seen.add(object_id)
        for part in current.parts:
            if type(part) is str:
                continue
            if isinstance(part, DeferredComponent):
                return True
            unwrapped = part
            if isinstance(unwrapped, CitryRender):
                pending.append(unwrapped)
    return False


def _render_ids(render: CitryRender, *, exclude_render_id: str | None = None) -> set[str]:
    """Collect component render IDs reachable through one render tree."""
    render_ids: set[str] = set()
    pending: list[CitryRender] = [render]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in seen:
            continue
        seen.add(object_id)
        render_id = current.frame.render_id
        if render_id is not None and render_id != exclude_render_id:
            render_ids.add(render_id)
        for part in current.parts:
            if type(part) is str:
                continue
            nested_part = part
            if isinstance(nested_part, CitryRender):
                pending.append(nested_part)
    return render_ids


def _render_selection(render: CitryRender) -> tuple[set[str], set[int]]:
    """Collect selected render IDs and object identities in one tree walk."""
    render_ids: set[str] = set()
    object_ids: set[int] = set()
    pending: list[RenderPart] = [render]
    while pending:
        current = pending.pop()
        # Text identity cannot select an occurrence: equal or interned text
        # can appear in unrelated slots. Keep only structural identities.
        if not isinstance(current, CitryRender):
            continue
        object_id = id(current)
        if object_id in object_ids:
            continue
        object_ids.add(object_id)
        if isinstance(current, CitryRender):
            render_id = current.frame.render_id
            if render_id is not None:
                render_ids.add(render_id)
            pending.extend(current.parts)
    return render_ids, object_ids


def _render_ids_from_parts(parts: list[RenderPart]) -> set[str]:
    """Collect component render IDs reachable from a selected parts list."""
    render_ids: set[str] = set()
    for part in parts:
        nested_part = part
        if isinstance(nested_part, CitryRender):
            render_ids.update(_render_ids(nested_part))
    return render_ids


def _render_objects(render: RenderPart) -> set[int]:
    """Collect transient part identities reachable through a render tree."""
    object_ids: set[int] = set()
    pending: list[RenderPart] = [render]
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in object_ids:
            continue
        object_ids.add(object_id)
        if isinstance(current, CitryRender):
            pending.extend(current.parts)
    return object_ids


def _render_objects_from_parts(parts: list[RenderPart]) -> set[int]:
    """Collect transient part identities reachable from selected parts."""
    object_ids: set[int] = set()
    for part in parts:
        if isinstance(part, CitryRender):
            object_ids.update(_render_objects(part))
        else:
            object_ids.add(id(part))
    return object_ids


def _contains_render(container: CitryRender, target: CitryRender) -> bool:
    """Return whether ``target`` remains reachable inside ``container``."""
    pending: list[CitryRender] = [container]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if current is target:
            return True
        object_id = id(current)
        if object_id in seen:
            continue
        seen.add(object_id)
        for part in current.parts:
            if type(part) is str:
                continue
            nested_part = part
            if isinstance(nested_part, CitryRender):
                pending.append(nested_part)
    return False


def _replace_in_parts(parts: list[RenderPart], index: int, target: object, new: RenderPart) -> None:
    """
    Put ``new`` where ``target`` currently is in ``parts``.

    ``index`` is where ``target`` was last seen, so we check that spot first. If
    the list has changed (for example user code or an extension edited
    ``parts``), we scan the whole list for ``target`` instead. Each render step
    swaps one item for one item, so positions normally stay put.
    """
    if 0 <= index < len(parts) and parts[index] is target:
        parts[index] = new
        return
    for i, part in enumerate(parts):
        if part is target:
            parts[i] = new
            return
    msg = "deferred part vanished from its .parts list before resolution"
    raise RuntimeError(msg)


def _component_path(component: Component | None) -> list[str]:
    """
    The class names from the root component down to ``component``, inclusive.

    Walks the ``parent`` links upward and reverses, so the root comes first.
    These names are the path frames put into error messages ("MyPage > Card >
    Avatar"; see docs/design/component_on_render.md section 6). An embedded element
    rendered from an expression has no parent link; its chain starts at
    itself, and the path of the component it is embedded in is prepended when
    the error passes through that component's render (``_render_one_traced``).
    """
    names: list[str] = []
    while component is not None:
        names.append(type(component).__name__)
        # simple='vue' components between this one and its parent have no
        # instance to walk through, so their names come from the call.
        metadata = getattr(component, "_prepared_call_metadata", None)
        if type(metadata) is _PreparedCallMetadata:
            names.extend(reversed(metadata.simple_vue_callers))
        component = component.parent
    names.reverse()
    return names


def _nesting_depth_error(task: _RenderTask) -> RecursionError:
    """
    Build the error for a child that would sit deeper than ``max_component_depth``.

    Only called once, on failure, so walking the whole parent chain here costs
    nothing on ordinary renders. The chain is shortened to its two outermost
    and three innermost names: the innermost ones show which components
    repeat, and the full chain can be thousands of names long.
    """
    element = task.deferred.element
    limit = element.comp_cls.citry.settings.max_component_depth
    metadata = element.prepared_call_metadata
    callers = metadata.simple_vue_callers if type(metadata) is _PreparedCallMetadata else ()
    names = [*_component_path(task.deferred.parent), *callers, element.comp_cls.__name__]
    if len(names) > 6:
        names = [*names[:2], "...", *names[-3:]]
    chain = " > ".join(names)
    msg = (
        f"Component {element.comp_cls.__name__} is nested more than {limit} components deep "
        f"({chain}). This usually means a component keeps rendering itself, for example a tree "
        "node whose data lists the node among its own children. Make sure the recursion ends, "
        "or pass a larger max_component_depth to Citry() if the page really nests this deep."
    )
    error = RecursionError(msg)
    # Users see a plain RecursionError; the flag lets bubble() tell this one
    # apart so no error boundary can swallow it.
    error._citry_nesting_limit = True  # type: ignore[attr-defined]
    return error


def _render_one_traced(
    element: CitryElement,
    parent: Component | None = None,
    provides: dict[str, Any] | None = None,
) -> _InitialRender:
    """
    ``_render_one``, with the component path added to any error raised.

    The path is the parent chain plus this component's class name, which is
    the same chain the created instance would report (its ``parent`` is set
    from this ``parent`` argument), and is available even when the failure
    happens before the instance exists (e.g. kwargs validation).
    """
    return _render_one_with_error_path(element, parent, provides)


def _render_one_with_error_path(
    element: CitryElement,
    parent: Component | None,
    provides: dict[str, Any] | None,
) -> _InitialRender:
    """Record a rendering failure while its owning graph is still active."""
    try:
        return _render_one(element, parent, provides)
    except Exception as err:
        metadata = element.prepared_call_metadata
        callers = metadata.simple_vue_callers if type(metadata) is _PreparedCallMetadata else ()
        set_component_error_message(err, [*_component_path(parent), *callers, element.comp_cls.__name__])
        raise


def _finalize(render: CitryRender, error: Exception | None) -> CitryRender:
    """
    Settle a rendered component: run ``on_component_rendered`` and apply the result.

    Runs once the component and everything inside it have been rendered, or,
    when ``error`` is set, when a component inside it failed and the error is
    bubbling up (docs/design/component_on_render.md section 5). The extension hook
    receives the rendered output, or ``None`` together with the error when
    rendering failed. An extension may replace the output with a new
    ``CitryRender`` or ``str`` (which also swallows the error), or raise to
    replace the error. An error that is not swallowed is raised here, to
    continue bubbling.
    """
    from citry._simple_runtime import SimpleRender  # noqa: PLC0415

    if isinstance(render, SimpleRender):
        if error is not None:
            raise error
        return render
    component = render.context.component
    if component is None:
        if error is not None:
            raise error
        return render
    if error is not None:
        render.context._error_tainted = True
    try:
        # An extension may also serialize the result and return the HTML, so
        # its hook gets the same marker rule as the component's on_render.
        with _after_render_hooks_scope(component.id):
            new_render, out_error, had_error = component.citry.extensions.on_component_rendered(
                component,
                None if error is not None else render,
                error,
            )
    except Exception:  # noqa: TRY203
        raise
    if had_error:
        render.context._error_tainted = True
    if out_error is not None:
        # A fresh error (raised by an extension just now) gets this
        # component's path; a bubbling error passing through unchanged
        # already carries the frames from where it happened.
        if out_error is not error:
            set_component_error_message(out_error, _component_path(component))
        raise out_error
    if isinstance(new_render, str):
        return CitryRender(
            parts=[new_render],
            context=render.context,
            is_component_root=render.is_component_root,
            is_transparent_root=render.frame.is_transparent_root,
        )
    if isinstance(new_render, CitryRender) and new_render is not render:
        from citry.citry_render import RenderDecoration  # noqa: PLC0415

        if isinstance(new_render, RenderDecoration) and (
            new_render.context is render.context or new_render.context.component is None
        ):
            if new_render.context is not render.context:
                _merge_dependencies(render.context, new_render.context)
            return new_render._with_frame(render.context, render.frame)
        if new_render.context is render.context:
            return CitryRender(
                parts=new_render.parts,
                context=render.context,
                is_component_root=render.is_component_root,
                is_transparent_root=render.frame.is_transparent_root,
            )
        _merge_dependencies(render.context, new_render.context)
        from citry._vue.direct import wrap_python_composition_result  # noqa: PLC0415

        return CitryRender(
            parts=[wrap_python_composition_result(new_render)],
            context=render.context,
            is_component_root=render.is_component_root,
            is_transparent_root=render.frame.is_transparent_root,
        )
    if new_render is not None:
        return new_render
    return render


def _validate_client_props_target(element: CitryElement) -> None:
    """Validate the final dynamic target and retain the authored call-site diagnostic."""
    binding_keys = tuple(binding.key for binding in element.component_tag_client_bindings)
    if CLIENT_PROPS_ATTR not in binding_keys:
        return

    comp_cls = element.comp_cls
    tag_name = f"c-{getattr(comp_cls, 'name', None) or comp_cls.__name__}"
    validate_client_props_target(comp_cls, binding_keys, tag_name=tag_name)


def _render_one(
    element: CitryElement,
    parent: Component | None = None,
    provides: dict[str, Any] | None = None,
) -> _InitialRender:
    """
    Render one component, without rendering the components inside it.

    Creates the Component instance, runs the data methods, calls the
    ``on_render`` hook, builds (or reuses) the template body, and turns it
    into a ``CitryRender``. Any ``<c-child>`` tags in the template become
    unrendered ``DeferredComponent`` parts; rendering those, and running
    ``on_component_rendered``, is done by ``render_impl``.

    Args:
        element: The CitryElement to render. Carries the component class,
            kwargs, slots, and the cached body (node list).
        parent: The parent Component instance if rendering inside another
            component's template. Used to set parent/root references.
        provides: The provide/inject entries this component inherits (captured
            where its tag sits, or passed by the caller). Readable via
            ``Component.inject`` and passed on to its own descendants.

    Returns:
        The initial render whose parts may contain unresolved
        ``DeferredComponent`` values, plus its generator and render-local cache
        decision. ``render_impl`` settles all three together.

    """
    comp_cls = element.comp_cls
    from citry._vue.capture import prepared_render_active  # noqa: PLC0415

    # A simple='vue' class reaches this path only when engine state (not the
    # class) needs ordinary rendering; any other arrival skipped the checks.
    if comp_cls.simple == "vue" and not _simple_vue_renders_ordinarily(comp_cls):
        raise TypeError(
            "simple='vue' calls must pass through the instance-free leaf renderer; "
            "this invocation reached the ordinary component-instance path"
        )
    if comp_cls.simple is True:
        from citry._simple_runtime import SimpleElement, prepare_simple_element, render_simple  # noqa: PLC0415

        if not isinstance(element, SimpleElement):
            element = prepare_simple_element(
                element,
                CitryContext(
                    component=parent,
                    provides=provides,
                    sandboxed=comp_cls.citry.settings.sandbox_expressions,
                ),
            )
        return _InitialRender(render_simple(element), None)
    _validate_client_props_target(element)
    citry_instance = comp_cls.citry
    extensions = citry_instance.extensions

    # 1. Create component instance with all state.
    #    Uses _create_instance() which bypasses ComponentMeta.__call__
    #    (that returns a CitryElement) and calls Component.__init__.
    #    __init__ handles input normalization (dict/NamedTuple/dataclass ->
    #    dict, copied), id generation, typed kwargs/slots, raw_ variants,
    #    inherited provides, and parent/root references.
    component = comp_cls._create_instance(
        kwargs=element.kwargs,
        slots=element.slots,
        parent=parent,
        provides=provides,
        _defer_input_finalization=True,
    )
    if type(element) is not CitryElement:
        from citry.components.dynamic import _DynamicSelectorElement  # noqa: PLC0415
        from citry.components.mark import _SyntheticMarkElement  # noqa: PLC0415

        if isinstance(element, _DynamicSelectorElement):
            component._selector_call_shape = (element.contains_fills, element.has_range_directives)
        elif type(element) is _SyntheticMarkElement:
            component._citry_mark_replacement = True
    if element.component_tag_client_bindings and comp_cls.transparent and not comp_cls._citry_dynamic_selector:
        # A transparent component renders no Vue component of its own, so a
        # prop, listener, or `v-show` on its tag would have nothing to reach.
        # `<c-component>` is the exception: it forwards them to its target.
        names = ", ".join(repr(binding.key) for binding in element.component_tag_client_bindings)
        msg = (
            f"{names} cannot be used on the tag of the transparent component {comp_cls.__name__!r}: "
            "it renders its content in place and has no Vue component to receive props, listeners, or 'v-show'. "
            "Put the binding on an element inside it."
        )
        raise TypeError(msg)
    component._component_tag_client_bindings = element.component_tag_client_bindings
    # Private dynamic-element directives must be visible to input hooks, but
    # never enter the user kwargs those hooks can replace.
    component._element_morph_metadata = element.element_morph_metadata
    component._prepared_call_metadata = element.prepared_call_metadata
    # 2. Attach the per-component extension configs (eg `component.view`,
    #    AKA `component.<ext.name>`), then run on_component_input.
    #    Typed construction is deliberately deferred until every input hook
    #    finishes, so hook mutations and the values used to render cannot drift.
    #    Defaults, factories, coercion, and validation run exactly once.
    extensions._init_component_instance(component)
    extensions.on_component_input(component)
    component._finalize_inputs()

    # Trace the authoritative post-hook inputs. The ancestor path is O(depth),
    # so build it only when TRACE is enabled.
    if is_tracing():
        trace_component_msg(
            "RENDER",
            type(component).__name__,
            component.id,
            component_path=_component_path(component),
            slot_fills=component.raw_slots,
        )

    # 3. Build the current-call component context before component data executes.
    active_provides = component._provides_inherited
    if component._provides_own:
        active_provides = {**active_provides, **component._provides_own}
    context = CitryContext(
        component=component,
        provides=active_provides,
        sandboxed=citry_instance.settings.sandbox_expressions,
    )

    from citry._vue.capture import direct_prepared_render_active  # noqa: PLC0415

    if direct_prepared_render_active():
        from citry.ext.cache.errors import CacheArtifactError, _CacheRevisionChanged  # noqa: PLC0415
        from citry.ext.cache.extension import CacheExtension, _CacheHit, _CacheMissPlan  # noqa: PLC0415
        from citry.ext.cache.replay import _replay_component_artifact, _replay_fragment_artifact  # noqa: PLC0415

        # The registry is keyed by name and hands back the base Extension, while the
        # replay decisions below are the cache extension's own. Narrow once here so a
        # different extension registered under "cache" fails on this line rather than
        # part-way through a replay.
        cache_extension = citry_instance.extensions.get_extension("cache")
        if not isinstance(cache_extension, CacheExtension):
            raise TypeError("the 'cache' extension slot must hold a CacheExtension")
        while True:
            try:
                decision = cache_extension._lookup_component(component, context)
            except _CacheRevisionChanged:
                continue
            if isinstance(decision, _CacheHit):
                try:
                    replayed = (
                        _replay_fragment_artifact(
                            decision.artifact,
                            boundary=component,
                            context=context,
                            revision=decision.miss.revision,
                        )
                        if decision.miss.kind == "fragment"
                        else _replay_component_artifact(
                            decision.artifact,
                            boundary=component,
                            context=context,
                            revision=decision.miss.revision,
                        )
                    )
                except CacheArtifactError as error:
                    if cache_extension._revision_snapshot() != decision.miss.revision:
                        continue
                    cache_extension._record_replay_rejection(decision, component, error)
                    decision = decision.miss
                else:
                    cache_extension._notify_component_hit(decision, component)
                    return _InitialRender(render=replayed, generator=None, cache_hit=True)
            break
        if isinstance(decision, _CacheMissPlan):
            context.extra["citry_cache_miss_plan"] = decision

    # 4. Call the data methods on a miss or bypass.
    #    template_data() feeds the template variables; js_data() / css_data()
    #    feed the component's JS/CSS variables, consumed by the built-in
    #    `dependencies` extension (docs/design/dependencies.md section 5).
    #    Each may return a dict, a NamedTuple, or the component's typed
    #    dataclass; `_normalize_data` validates it and converts the validated
    #    instance to a plain dict, so schema defaults and coercions become the
    #    values consumers see. No defensive copy is needed here: an override
    #    produces its result fresh each render, and the default returns the
    #    component's own kwargs, which __init__ already copied per render
    #    (raw_kwargs), so the result is never shared across renders.
    from citry._vue.direct import direct_receiver_scope  # noqa: PLC0415

    with direct_receiver_scope(context):
        # Component imports this render module lazily, so the cycle is settled here.
        from citry.component import Component as ComponentBase  # noqa: PLC0415

        template_data_callback = component.template_data
        default_template_data = (
            getattr(template_data_callback, "__func__", None) is ComponentBase.template_data
            and getattr(template_data_callback, "__self__", None) is component
        )
        tpl_data = _normalize_data(
            template_data_callback(component.kwargs, component.slots),
            comp_cls.TemplateData,
            preserve=component._kwargs_const if default_template_data else None,
        )
        js_data = _normalize_data(component.js_data(component.kwargs, component.slots), comp_cls.JsData)
        css_data = _normalize_data(component.css_data(component.kwargs, component.slots), comp_cls.CssData)

    # 3.5 Overlay template globals: variables exposed to every component's
    #     template without being returned from each template_data(). Two layers,
    #     lowest precedence first: this instance's citry.template_globals, then
    #     any per-render globals from Component.render(template_globals=...). The
    #     component's own data wins over both, so all globals go under tpl_data.
    #     Merged after the schema check above, so a global need not appear in a
    #     component's declared TemplateData. Skipped when there are none, so a
    #     render with no globals pays nothing here.
    instance_globals = citry_instance.template_globals
    render_globals = _render_globals.get()
    if instance_globals or render_globals:
        tpl_data = _merge_const_mappings(
            _const_mapping(instance_globals),
            _const_mapping(render_globals or {}),
            tpl_data,
        )

    context.variables = tpl_data

    # 4.5 on_component_data: extensions may add/modify the data, and stash
    #     tree-wide state into ``context.extra`` (e.g. the dependencies
    #     extension's render records).
    with direct_receiver_scope(context):
        extensions.on_component_data(component, context, tpl_data, js_data, css_data)
        _restore_const_identities(tpl_data, component._const_candidates)
    # Checked after the extensions ran, because an extension may add keys, and
    # before the template renders, so the error comes before any browser output.
    _check_js_data_keys(comp_cls, js_data)
    context.js_data = js_data

    # 5. ``provides`` are the entries this component inherited plus any
    #    provide or block changes it registered during template_data; a new
    #    mapping is built only when outgoing state changed (see
    #    docs/design/component_provide.md section 4.1).
    active_provides = component._provides_inherited
    if component._provides_own:
        active_provides = {**active_provides, **component._provides_own}
    context.provides = active_provides

    # 5.5 The per-component render hook (docs/design/component_on_render.md section 3).
    #     Returning None (the default) renders the template as usual.
    #     Returning content makes it the component's whole output, and the
    #     template body below is never built or walked. A generator runs up
    #     to its first yield here (the "before" phase), and what it yielded
    #     picks the output the same way; the live generator then travels with
    #     the component's finalize task and is resumed with the settled
    #     result once the whole subtree has rendered (``settle`` in
    #     ``render_impl``).
    generator: OnRenderGenerator | None = None
    parts: list[RenderPart] | None = None
    try:
        with direct_receiver_scope(context):
            hook_result = component.on_render()
        if is_generator(hook_result):
            # Prime the generator (runs the before-phase, up to the first
            # yield). A bare first yield means "render the template as usual";
            # yielded or returned content becomes the output instead.
            generator = hook_result
            parts, generator = _send_into_generator(generator, None, context, component, default_on_none=True)
        elif hook_result is not None:
            parts = _replacement_parts(hook_result, context, component)
    except Exception:  # noqa: TRY203
        raise

    if parts is not None:
        return _InitialRender(
            render=CitryRender(
                parts=parts,
                context=context,
                is_component_root=not comp_cls.transparent,
                is_transparent_root=comp_cls.transparent,
            ),
            generator=generator,
        )

    # 6. Build the body (the list of static strings and node objects the
    #    template compiles to). Parsing and compiling the template runs once
    #    per component class (cached on the class).
    #
    #    Then the Const optimization kicks in. extract_const_vars() collects
    #    the template variables whose names retain a Const promise in the
    #    renderer's side metadata and turns them into a cache key. The values
    #    themselves are ordinary Python objects. The first render with a
    #    given set of Const values builds the node list and runs precompute_const_parts()
    #    on it, which does the work that depends only on those values right
    #    away: e.g. "{{ cols }}" with cols=Const(3) becomes the text "3", and
    #    a <c-if> whose condition uses only Const values keeps just the
    #    branch that matches. The result is cached, so later renders with the
    #    same Const values reuse it and skip all of that work. See
    #    docs/design/component_constness.md and citry/constness.py.
    #
    #    on_template_compiled fires here (per built node list, before the
    #    optimization and caching), so an extension can transform the node
    #    list once and have the transform cached. See
    #    docs/design/extensions.md section 7.4.
    #
    #    Only Const values the template actually uses (``compiled.used_vars``)
    #    go into the value part of the cache key; a Const value the template
    #    never reads cannot change the output. The presence of every variable
    #    name is keyed separately because c-for/c-fill reject binding a name
    #    already in scope, including one the template otherwise never reads.
    #    A node injected by an extension may use a value outside the compiled
    #    set; that value stays un-optimized and re-evaluates each render.
    try:
        template_override = getattr(element, "_template_override", None)
        from citry._vue.capture import prepared_render_active  # noqa: PLC0415

        prepared = prepared_render_active()
        compiled = _get_compiled_template(
            comp_cls,
            template_override=template_override,
            prepared=prepared,
        )
        context.template_record = compiled
        generate = (
            compiled.prepared_generate
            if prepared and compiled is not None
            else compiled.generate
            if compiled
            else None
        )
        if compiled is None or generate is None:
            body: list[BodyItem] = []
        else:
            visible_names = frozenset(tpl_data)

            const_vars, signature = extract_const_vars(tpl_data, used_vars=compiled.used_vars)

            def build() -> list[BodyItem]:
                foreign_resolved = extensions.on_template_foreign_compiled(
                    comp_cls,
                    generate(),
                    provider_metadata=compiled.foreign_provider_metadata,
                    template_id=compiled.template_id,
                    origin=compiled.origin,
                    template_kind=compiled.kind,
                )
                transformed = extensions.on_template_compiled(
                    comp_cls,
                    foreign_resolved,
                    template_id=compiled.template_id,
                    origin=compiled.origin,
                    template_kind=compiled.kind,
                )
                if prepared:
                    from citry._vue.capture import (  # noqa: PLC0415
                        PREPARED_CONST_PRECOMPUTE_ADAPTER,
                        coalesce_prepared_static_nodes,
                    )
                    from citry._vue.leaf_program import (  # noqa: PLC0415
                        compile_leaf_program,
                    )

                    specialized = precompute_const_parts(
                        transformed,
                        const_vars,
                        precompute_attrs=not extensions.has_hook("on_attrs_resolved"),
                        sandboxed=citry_instance.settings.sandbox_expressions,
                        visible_names=visible_names,
                        adapter=PREPARED_CONST_PRECOMPUTE_ADAPTER,
                    )
                    typed = coalesce_prepared_static_nodes(specialized)
                    i18n = getattr(component, "i18n", None)
                    allow_i18n_passthrough = i18n is not None and i18n._extension._compiled_catalog is None
                    attrs_hooks = extensions._extensions_with_hook("on_attrs_resolved")
                    from citry.ext.events.extension import EventsExtension  # noqa: PLC0415

                    supported_attrs_hooks = all(
                        type(extension) is EventsExtension
                        and getattr(extension.on_attrs_resolved, "__func__", None) is EventsExtension.on_attrs_resolved
                        for extension in attrs_hooks
                    )
                    program = (
                        compile_leaf_program(
                            typed,
                            allow_i18n_passthrough=allow_i18n_passthrough,
                        )
                        if template_override is None
                        and comp_cls.simple is False
                        and not comp_cls.pure
                        and not comp_cls.transparent
                        and not is_tracing()
                        and supported_attrs_hooks
                        else None
                    )
                    return [program] if program is not None else typed
                return precompute_const_parts(
                    transformed,
                    const_vars,
                    # Precomputing an attribute region bakes its dict before extensions
                    # see it, so keep the regions live when anyone subscribes.
                    precompute_attrs=not extensions.has_hook("on_attrs_resolved"),
                    sandboxed=citry_instance.settings.sandbox_expressions,
                    visible_names=visible_names,
                )

            if prepared:
                if template_override is None:
                    body = citry_instance._const_body_cache.get_or_build(
                        comp_cls,
                        signature,
                        build,
                        visible_names=visible_names,
                        format_key=("vue-prepared", is_tracing()),
                    )
                else:
                    # The ABC token keeps a later ComponentLike registration
                    # from reusing text a constant value was written as.
                    prepared_key = (signature, visible_names, is_tracing(), abc.get_cache_token())
                    with compiled.compile_lock:
                        cached_body = compiled.prepared_standalone_bodies.get(prepared_key)
                        if cached_body is None:
                            cached_body = build()
                            compiled.prepared_standalone_bodies[prepared_key] = cached_body
                            while len(compiled.prepared_standalone_bodies) > 64:
                                compiled.prepared_standalone_bodies.popitem(last=False)
                        compiled.prepared_standalone_bodies.move_to_end(prepared_key)
                        body = cached_body
            elif template_override is not None:
                # One transparent class serves every standalone source. Its
                # body cache must therefore include the immutable template
                # record rather than using the class-keyed shared cache.
                standalone_key = (signature, visible_names, abc.get_cache_token())
                with compiled.compile_lock:
                    cached_body = compiled.standalone_bodies.get(standalone_key)
                    if cached_body is None:
                        cached_body = build()
                        compiled.standalone_bodies[standalone_key] = cached_body
                        compiled.standalone_bodies.move_to_end(standalone_key)
                        while len(compiled.standalone_bodies) > 64:
                            compiled.standalone_bodies.popitem(last=False)
                    body = cached_body
            else:
                body = citry_instance._const_body_cache.get_or_build(
                    comp_cls,
                    signature,
                    build,
                    visible_names=visible_names,
                )

        # 7. Walk the body into a parts list and wrap it in a CitryRender. Any nested
        #    components are left as unrendered DeferredComponent parts; render_impl
        #    renders them and runs on_component_rendered for each one once everything
        #    inside it has been rendered. This render is the component's whole
        #    output, so it is marked as the component's root render (serialization
        #    relies on the flag to find component frame boundaries). A transparent
        #    component opts out: its output joins the surrounding frame and gets no
        #    data-cid marker (e.g. the <c-provide> built-in).
        if comp_cls.pure:
            pure_lookup = pure_body_lookup(
                comp_cls,
                body,
                context.variables,
                compiled.used_vars if compiled is not None else (),
            )
        else:
            pure_lookup = None
        if pure_lookup is not None and pure_lookup[1] is not None:
            parts = _replay_pure_body(pure_lookup[1], context)
        elif pure_lookup is not None:
            parts, pure_plan, cached_node_count = _render_and_capture_pure_body(body, context, component)
            if cached_node_count:
                store_pure_body(pure_lookup[0], pure_plan)
        else:
            parts = _render_body(body, context)
    except Exception as render_error:
        context._error_tainted = True
        if generator is None:
            raise
        # The component's own template failed; deliver the error to its live
        # on_render generator, the same ``(None, error)`` it would receive
        # for a failing child. This is what lets an error boundary guard its
        # own slot content, which renders right here in its body walk. The
        # generator may produce replacement output; if it does not (plain
        # return), the error continues out as usual.
        parts, generator = _send_into_generator(
            generator,
            (None, render_error),
            context,
            component,
            default_on_none=False,
        )
        if parts is None:
            raise

    return _InitialRender(
        render=CitryRender(
            parts=parts,
            context=context,
            is_component_root=not comp_cls.transparent,
            is_transparent_root=comp_cls.transparent,
        ),
        generator=generator,
    )


def _i18n_body_capture_is_empty(component: Component) -> bool:
    """Whether skipping this component's body would omit no i18n metadata."""
    usage = component.i18n._usage_state
    if usage is not None and not usage.empty:
        return False
    bindings = component.i18n._bindings_state
    return bindings is None or not (bindings.records or bindings.markers or bindings._pending_text)


def _capture_pure_part(part: RenderPart, context: CitryContext) -> str | PureInteriorBody | PurePreparedPart | None:
    """Detach one ownership-free output part for a render-local pure plan."""
    if isinstance(part, str):
        return part
    from citry._vue.capture import (  # noqa: PLC0415
        PreparedElementClose,
        PreparedSourceText,
        PreparedStaticRun,
        PreparedTextValue,
    )

    if type(part) in {PreparedSourceText, PreparedStaticRun, PreparedElementClose}:
        return PurePreparedPart(part)
    if (
        type(part) is PreparedTextValue
        and part.browser_binding is None
        and type(part.value) in {type(None), bool, int, float, str}
    ):
        return PurePreparedPart(part)
    if (
        type(part) is not CitryRender
        or part.context is not context
        or part.is_component_root
        or part.frame.is_transparent_root
    ):
        return None
    plan: list[str | PureInteriorBody | PurePreparedPart] = []
    for nested_part in part.parts:
        captured = _capture_pure_part(nested_part, context)
        if captured is None:
            return None
        plan.append(captured)
    return PureInteriorBody(tuple(plan))


def _render_and_capture_pure_body(
    body: list[BodyItem],
    context: CitryContext,
    component: Component,
) -> tuple[list[RenderPart], PureBodyPlan, int]:
    """Render once while compiling safe values around live transaction holes."""
    parts: list[RenderPart] = []
    plan: list[str | PureInteriorBody | PureLiveBodyItem | PurePreparedPart] = []
    cached_node_count = 0
    tracing = is_tracing()
    for item in body:
        if isinstance(item, str):
            parts.append(item)
            plan.append(item)
            continue
        i18n_empty_before = _i18n_body_capture_is_empty(component)
        part = _render_pure_live_item(item, context, tracing=tracing)
        parts.append(part)
        if i18n_empty_before and _i18n_body_capture_is_empty(component):
            captured = _capture_pure_part(part, context)
            if captured is not None:
                plan.append(captured)
                cached_node_count += 1
                continue
        plan.append(PureLiveBodyItem(item))
    return parts, tuple(plan), cached_node_count


def _render_pure_live_item(item: Node, context: CitryContext, *, tracing: bool) -> RenderPart:
    """Execute one live plan hole with the ordinary body-walker contract."""
    if tracing:
        trace_node_msg("RENDER", type(item).__name__, getattr(item, "position", None))
    value_token = _VALUE_CONTEXT.set(context)
    try:
        part = item.render(context)
    except Exception as err:
        _attach_template_position(err, item, context)
        raise
    finally:
        _VALUE_CONTEXT.reset(value_token)
    unwrapped = part
    if isinstance(unwrapped, CitryRender) and unwrapped.context is not context and not _contains_deferred(unwrapped):
        _merge_dependencies(context, unwrapped.context)
    return part


def _replay_pure_body(plan: PureBodyPlan, context: CitryContext) -> list[RenderPart]:
    """Recreate transparent render wrappers against the current component context."""
    parts: list[RenderPart] = []
    for item in plan:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, PurePreparedPart):
            parts.append(item.part)
        elif isinstance(item, PureInteriorBody):
            parts.append(CitryRender(parts=_replay_pure_body(item.parts, context), context=context))
        else:
            parts.append(_render_pure_live_item(item.item, context, tracing=is_tracing()))
    return parts


def _send_into_generator(
    generator: OnRenderGenerator,
    send_arg: Any,
    context: CitryContext,
    component: Component,
    *,
    default_on_none: bool,
) -> tuple[list[RenderPart] | None, OnRenderGenerator | None]:
    """
    Send into an ``on_render`` generator until it produces an outcome.

    Used inside ``_render_one``, at priming time (``send_arg`` is ``None``)
    and when the component's own template render failed (``send_arg`` is
    ``(None, error)``). Returns ``(parts, generator)``: the replacement parts
    (``None`` for "no replacement") and the generator if it is still live
    (``None`` once it finished).

    An unrenderable yielded value (the ``TypeError`` from the coercion) is
    delivered back into the generator as ``(None, error)``, so every yield
    uniformly receives the settled result or failure of what it yielded.

    A bare yield (``yield`` / ``yield None``) means "render the template as
    usual" while priming (``default_on_none=True``). After an error was
    delivered (``default_on_none=False``) it means "answer again with the
    unchanged result", so the same value is re-sent, mirroring the settle
    loop in ``render_impl``.
    """
    while True:
        try:
            yielded = _send_on_render_generator(generator, send_arg, context)
        except StopIteration as stop:
            if stop.value is None:
                # Plain return: no replacement, generator done.
                return None, None
            return _replacement_parts(stop.value, context, component), None
        if yielded is None:
            if default_on_none:
                return None, generator
            continue
        try:
            return _replacement_parts(yielded, context, component), generator
        except TypeError as bad_yield:
            context._error_tainted = True
            set_component_error_message(bad_yield, _component_path(component))
            send_arg = (None, bad_yield)


def _send_on_render_generator(
    generator: OnRenderGenerator,
    send_arg: Any,
    context: CitryContext,
) -> Any:
    """Execute one generator phase with its component as the active Slot receiver."""
    from citry._vue.direct import direct_receiver_scope  # noqa: PLC0415

    # The generator may serialize its own result and return the HTML; see
    # _AFTER_RENDER_HOOKS_RENDER_ID for why that serialization skips this
    # component's root markers.
    render_id = context.component.id if context.component is not None else None
    with direct_receiver_scope(context), _after_render_hooks_scope(render_id):
        return generator.send(send_arg)


# The source label on the text part a prepared (Vue) render gets when
# on_render returns a plain str. That text has no template position, so the
# part points into this label instead, the way Python slot text does.
_ON_RENDER_TEXT_SOURCE = "on-render-text"


def _replacement_parts(value: RenderReplacement, context: CitryContext, component: Component) -> list[RenderPart]:
    """
    Convert an ``on_render`` replacement value into the component's parts list.

    The accepted values mirror what a ``{{ ... }}`` expression accepts
    (``_render_value`` in citry_render.py): a plain ``str`` is text and is
    escaped, while ``Markup`` (or any object with ``__html__``) is trusted
    HTML and is inserted as-is. The one difference is that an unsupported
    type is an error rather than being escaped to text
    (docs/design/component_on_render.md section 3.1).
    """
    # A Const marker is unwrapped first (a replacement built from a literal
    # template attribute arrives Const-wrapped); the value becomes output
    # here, so the marker has no further role, and the proxy must not leak
    # into the parts.
    value = const_value(value)
    if isinstance(value, ComponentLike):
        value = _resolve_component_like(value, component.citry)
    if type(value) is str and value == "":
        # "" is the public way to render nothing. Every serializer, the Vue
        # one included, treats this exact empty string as zero output.
        return [""]
    if getattr_static(value, "__html__", None) is not None:
        # Trusted HTML, as in a {{ ... }} expression. The Vue target used by
        # server events accepts HTML only as a typed part, the same one a
        # {{ ... }} Markup value becomes there.
        if vue_render_active():
            return [PreparedTrustedHtmlValue(str(cast("HasHtml", value).__html__()))]
        # Markup is already a render part; escape() turns another __html__
        # object into Markup without escaping it.
        return [value if isinstance(value, Markup) else escape(value)]
    if isinstance(value, str):
        # Plain text. A typed render needs a text part, which the serializer
        # escapes and the browser renders as the same text node, so a
        # returned "<script>" stays visible text. Renders outside a typed
        # render scope escape it here instead.
        if prepared_render_active():
            return [PreparedTextValue(_ON_RENDER_TEXT_SOURCE, (0, len(_ON_RENDER_TEXT_SOURCE)), str(value))]
        return [escape(value)]
    if isinstance(value, Slot):
        # Invoked with no data, like {{ my_slot }}. Slot content renders with
        # the scope of the component that wrote it, so its collected data is
        # copied into this render (the same merge as _render_body does).
        part = _render_slot_value(value, None, None, context)
        if type(part) is str:
            return [part]
        unwrapped = part
        if (
            isinstance(unwrapped, CitryRender)
            and unwrapped.context is not context
            and not _contains_deferred(unwrapped)
        ):
            _merge_dependencies(context, unwrapped.context)
        return [part]
    if isinstance(value, CitryElement):
        # Deferred like a <c-child> tag in the template: the render_impl loop
        # renders it, so a replacement chain can never exhaust the Python
        # call stack.
        if value.comp_cls.simple is True:
            from citry._simple_runtime import simple_deferred  # noqa: PLC0415

            return [simple_deferred(value, context)]
        return [
            DeferredComponent(
                value,
                parent=component,
                provides=context.provides,
            )
        ]
    if isinstance(value, CitryRender):
        # An already-rendered subtree is inlined; its collected data is
        # copied into this render.
        if value.context is not context:
            _merge_dependencies(context, value.context)
        from citry._vue.direct import wrap_python_composition_result  # noqa: PLC0415

        return [wrap_python_composition_result(value)]
    msg = (
        f"{type(component).__name__}.on_render() returned {type(value).__name__!r}; "
        "expected a str, a composed element, a CitryRender, a Slot, or None."
    )
    raise TypeError(msg)


def _get_compiled_template(
    comp_cls: type[Component],
    *,
    template_override: CitryTemplate | None = None,
    prepared: bool = False,
) -> CitryTemplate | None:
    """
    Return the component's template with its compiled form filled in.

    The template is loaded via ``assets.load_template``, which resolves
    ``template`` / ``template_file``, reads the file when needed, fires
    ``on_template_loaded``, and caches the ``CitryTemplate`` on the class (see
    docs/design/asset_loading.md). On the first render in each mode this function
    compiles the source and fills the selected generator and ``used_vars`` in place,
    so the loaded and compiled halves share one cache and one invalidation
    (``Component.reset_template()``). Each call to ``generate`` produces a
    fresh node list. Returns ``None`` when the component has no template.

    A parse or compile error is re-raised with the template's origin (the file
    path, or ``module::Class`` for inline) prefixed to its message, so a
    syntax error names where the template came from.
    """
    template = template_override if template_override is not None else load_template(comp_cls)
    if template is None:
        return None
    current_generate = template.prepared_generate if prepared else template.generate
    if current_generate is None:
        with template.compile_lock:
            current_generate = template.prepared_generate if prepared else template.generate
            if current_generate is not None:
                return template
            try:
                if not template.foreign_prepared:
                    spans, metadata = comp_cls.citry.extensions.on_template_foreign_spans(
                        comp_cls,
                        template.source,
                        template_id=template.template_id,
                        origin=template.origin,
                        template_kind=template.kind,
                        foreign_compile_contexts=template.foreign_compile_contexts,
                    )
                    template.foreign_spans = spans
                    template.foreign_provider_metadata = metadata
                    template.foreign_prepared = True
                compile_prepared = prepared
                if prepared and template.foreign_spans:
                    from citry._vue.capture import vue_render_active  # noqa: PLC0415

                    if vue_render_active():
                        raise TypeError("prepared Vue rendering does not yet support foreign template spans")
                    # Static serialization still preserves the established
                    # foreign-provider hook contract. Its selected output is
                    # ordinary trusted HTML and never enters the Vue compiler.
                    compile_prepared = False
                generate = _compile_template(
                    template,
                    comp_cls.citry._tag_rules(),
                    prepared=compile_prepared,
                )
                _check_declared_slots(comp_cls, template)
                if prepared:
                    template.prepared_generate = generate
                    # Typed nodes are now the normal compiled representation;
                    # keep the established public compiled-template accessor
                    # pointed at that same immutable generator.
                    template.generate = generate
                else:
                    template.generate = generate
            except Exception as err:
                set_template_origin_error_message(err, template.origin)
                raise
    return template


def _check_declared_slots(comp_cls: type[Component], template: CitryTemplate) -> None:
    """
    Check a component's own ``<c-slot>`` tags against its ``Slots`` schema.

    Runs once, at first compile, and only when the component declares a closed
    ``Slots`` schema (an omitted ``Slots`` accepts any fills, so there is nothing
    to check; see docs/design/component_slots.md section 9.5). It catches a *dead slot*: a
    ``<c-slot name="X">`` whose ``X`` is not a declared slot, so no caller can
    ever fill it. Dynamic-name slots (``<c-slot c-name="...">``) are not in
    ``declared_slots``, so they are never flagged.

    A slot's ``required`` flag and a default on the matching ``Slots`` field are
    orthogonal (the fill may be passed from outside, or omitted), so that
    combination is deliberately not flagged.
    """
    slot_specs = get_fields(comp_cls.Slots)
    if slot_specs is None:
        return
    declared = {spec.name for spec in slot_specs}
    for slot in template.declared_slots:
        if slot.name not in declared:
            close = get_close_matches(slot.name, sorted(declared), n=1, cutoff=0.7)
            hint = f" Did you mean {close[0]!r}?" if close else ""
            msg = (
                f"Component {comp_cls.__name__!r} renders <c-slot name={slot.name!r}> "
                f"(line {slot.line}) but its Slots class does not declare {slot.name!r}, so no "
                f"caller can fill it.{hint} Add {slot.name!r} to Slots, or remove the slot."
            )
            raise RuntimeError(msg)


def _compile_template(
    template: CitryTemplate,
    user_rules: dict[str, TagRules] | None = None,
    *,
    prepared: bool = False,
) -> Callable[[], list[BodyItem]]:
    """
    Parse, compile, and exec a template's source.

    Uses the citry_core pipeline: parse -> compile -> exec. The
    ``generate_template`` function from the exec'd namespace is returned;
    calling it returns a fresh list of runtime node objects. HTML mode also
    emits static strings; prepared mode emits typed source, value, and element nodes.
    The component-template caller publishes it only after its class-level slot
    validation succeeds. The parsed AST's root ``used_variables`` (which are
    transitive) become ``template.used_vars``.

    ``user_rules`` are the parse-time validation rules derived from the
    registered components' declarations (``Citry._tag_rules()``), so a
    template using a declared component fails here, at parse time, on unknown
    or missing kwargs/fills.

    The compiled code creates node objects (ExprNode, ComponentNode, etc.) by
    name. Those names are supplied through the ``ns`` namespace below, so the
    generated code can find them.
    """
    options = (
        ParseOptions(
            list(template.foreign_spans),
            source_offset=template.source_offset,
            root_source=template.root_source,
        )
        if template.foreign_spans or template.source_offset or template.root_source is not None
        else None
    )
    ast = parse_template(template.source, user_rules=user_rules, options=options)
    template.used_vars = frozenset(token.content for token in ast.used_variables)
    # The static <c-slot> declarations, kept for `_check_declared_slots` (the
    # caller runs it, since it has the component class and thus its Slots).
    template.declared_slots = tuple(
        DeclaredSlot(slot.token.content, slot.token.line_col[0], slot.token.line_col[1]) for slot in ast.slots
    )
    if prepared:
        from citry._vue.capture import (  # noqa: PLC0415
            PreparedElementCloseNode,
            PreparedElementOpenNode,
            PreparedExprNode,
            PreparedSourceTextNode,
            PreparedVerbatimHtmlNode,
        )
        from citry_core.template_parser.compile import _compile_prepared_template  # noqa: PLC0415

        code = _compile_prepared_template(ast)
    else:
        code = compile_template(ast)

    # Build the namespace for exec. "source" is the original template string,
    # passed to nodes for error reporting and diagnostics. This namespace
    # becomes the returned function's globals, so the node classes and source
    # stay bound to it.
    ns: dict[str, Any] = {
        # Projected nested parses keep root-absolute node positions, so their
        # runtime nodes must carry the matching root source as well.
        "source": template.root_source or template.source,
        "ExprNode": ExprNode,
        "ForeignNode": ForeignNode,
        "ComponentNode": ComponentNode,
        "ElementAttrsNode": ElementAttrsNode,
        "ElementKeyNode": ElementKeyNode,
        "IfNode": IfNode,
        "ForNode": ForNode,
        "SlotNode": SlotNode,
        "FillDataBinding": FillDataBinding,
        "FillNode": FillNode,
        "StaticHtmlAttr": StaticHtmlAttr,
        "ExprHtmlAttr": ExprHtmlAttr,
        "TemplateHtmlAttr": TemplateHtmlAttr,
        "ForeignHtmlAttr": ForeignHtmlAttr,
    }
    if prepared:
        ns.update(
            PreparedSourceTextNode=PreparedSourceTextNode,
            PreparedVerbatimHtmlNode=PreparedVerbatimHtmlNode,
            PreparedExprNode=PreparedExprNode,
            PreparedElementOpenNode=PreparedElementOpenNode,
            PreparedElementCloseNode=PreparedElementCloseNode,
        )
    exec(code, ns)  # noqa: S102
    generate: Callable[[], list[BodyItem]] = ns["generate_template"]
    return generate


def _compile_nested_template(
    template_str: str,
    user_rules: dict[str, TagRules] | None = None,
    component_class: type[Component] | None = None,
    *,
    root_source: str | None = None,
    source_offset: int = 0,
    foreign_spans: tuple[tuple[int, int, str, int, bool], ...] = (),
    provider_metadata: Mapping[str, object | None] | None = None,
    template_id: str | None = None,
    origin: str | None = None,
) -> Callable[[], list[BodyItem]]:
    """
    Compile a nested template fragment into its body-generating function.

    Used by the nodes that carry a template *inside* an attribute value (a
    ``c-body="<span>{{ x }}</span>"`` on a component). Such a fragment is not
    a component class's template, so there is no class-level ``CitryTemplate``
    to fill; a throwaway one wraps the fragment for the shared compile step.
    Position-in-the-outer-template error context is attached by the node's
    render wrapper, not here. When an owning component class is available, the
    fragment passes through the same compiled-template extension hooks as that
    class's primary body. Nested-template bindings therefore remain in the
    owner's handler/State scope without rewriting the authored source string.
    """
    core_spans = tuple(ForeignSpan(*span) for span in foreign_spans)
    template_kwargs: dict[str, Any] = {}
    if template_id is not None:
        template_kwargs["template_id"] = template_id
    template = CitryTemplate(
        source=template_str,
        origin=origin or "<nested template>",
        kind="nested",
        foreign_spans=core_spans,
        foreign_prepared=True,
        source_offset=source_offset,
        root_source=root_source,
        **template_kwargs,
    )
    from citry._vue.capture import prepared_render_active, vue_render_active  # noqa: PLC0415

    prepared = prepared_render_active()
    if prepared and core_spans and vue_render_active():
        raise TypeError("prepared Vue rendering does not yet support foreign template spans")
    generate = _compile_template(template, user_rules, prepared=prepared and not core_spans)
    if component_class is None:
        return generate
    if provider_metadata is None:
        primary = load_template(component_class)
        provider_metadata = primary.foreign_provider_metadata if primary is not None else {}
    foreign_resolved = component_class.citry.extensions.on_template_foreign_compiled(
        component_class,
        generate(),
        provider_metadata=provider_metadata,
        template_id=template.template_id,
        origin=template.origin,
        template_kind=template.kind,
    )
    compiled = component_class.citry.extensions.on_template_compiled(
        component_class,
        foreign_resolved,
        template_id=template.template_id,
        origin=template.origin,
        template_kind=template.kind,
    )
    return lambda: compiled


def _render_body(body: Sequence[BodyItem], context: CitryContext) -> list[RenderPart]:
    """
    Render a body (a list of static strings and nodes) into a list of parts.

    Static strings pass through unchanged in HTML mode and are rejected in
    prepared mode. Each node is rendered with
    ``context`` and adds a part: a ``str``, a nested ``CitryRender``, or a
    ``DeferredComponent`` (a ``<c-child>`` tag, rendered later by ``render_impl``).

    A node may return a ``CitryRender`` from a *different* render: an
    already-rendered value found in a ``{{ ... }}`` expression. When that happens
    its dependencies are copied into this render's context. A ``CitryRender`` from
    *this* render (for example a ``<c-if>`` block or a nested template, which use
    the same context) does not need copying.

    The parts are returned as a list, not joined into one string, so that an
    already-rendered value embedded in the middle can still be read later. Joining
    happens in ``CitryRender.serialize()``.
    """
    value_token = _VALUE_CONTEXT.set(context)
    try:
        from citry._vue.capture import vue_render_active  # noqa: PLC0415

        direct_prepared = vue_render_active()
        parts: list[RenderPart] = []
        tracing = is_tracing()  # hoisted: one level check per body walk, not per node
        for item in body:
            if isinstance(item, str):
                if direct_prepared:
                    raise TypeError("prepared Vue rendering received unsupported raw compiled output")
                parts.append(item)
                continue
            if tracing:
                trace_node_msg("RENDER", type(item).__name__, getattr(item, "position", None))
            try:
                part = item.render(context)
            except Exception as err:
                _attach_template_position(err, item, context)
                raise
            if type(part) is str:
                if direct_prepared:
                    raise TypeError(
                        f"prepared Vue rendering received unsupported raw output from {type(item).__name__}"
                    )
                parts.append(part)
                continue
            unwrapped = part
            if (
                isinstance(unwrapped, CitryRender)
                and unwrapped.context is not context
                and not _contains_deferred(unwrapped)
            ):
                _merge_dependencies(context, unwrapped.context)
            parts.append(part)

        return parts
    finally:
        _VALUE_CONTEXT.reset(value_token)


def _attach_template_position(err: Exception, node: BodyItem, context: CitryContext) -> None:
    """
    Add the failing node's template snippet to the error message.

    Every compiler-emitted node carries ``source`` (the whole template
    string) and ``position`` (its start/end indices in it); a node injected
    by an extension may not, in which case this does nothing. The snippet is
    added once per error, by the innermost failing node: control-flow bodies
    render through ``_render_body`` recursively, so the enclosing node's
    pass through here is a no-op (see ``set_template_position_error_message``).

    The header names the lexical template class, which can be a simple class
    rendering under another component's ownership. Slot-fill content retains
    the source context of the component that wrote it.
    """
    source = getattr(node, "source", None)
    position = getattr(node, "position", None)
    if not isinstance(source, str) or not isinstance(position, tuple) or len(position) != 2:
        return
    component = context.component
    component_name = type(component).__name__ if component is not None else None
    if context._simple_scope is not None:
        component_name = context._simple_scope.component_class.__name__
    # Prefer the exact template record that produced this body. This matters
    # for render_template() and nested templates: loading the component's
    # primary template would report the wrong origin and provider metadata.
    active_template = context.template_record
    origin = active_template.origin if active_template is not None else None
    if origin is None and component is not None:
        try:
            template = load_template(type(component))
        except Exception:  # noqa: BLE001 - error reporting must not raise
            template = None
        if template is not None:
            origin = template.origin
    set_template_position_error_message(err, source, position, component_name, origin)


# Every js_data() key becomes a member of the component's Vue instance in the
# browser. Vue and Citry already own every instance name that starts with "$"
# or "_", and Citry adds the "citryId" prop to every component, so the browser
# runtime refuses those keys when the component mounts. Python knows these
# names without seeing the component's JavaScript, so it rejects them at render
# time, before any HTML leaves the server. A key that matches a name the
# component's JavaScript defines (a prop, data(), setup(), method, computed
# value, or injection) can only be detected in the browser, which reports it
# when the component mounts.
_RESERVED_JS_DATA_PREFIXES = ("$", "_")
_RESERVED_JS_DATA_NAMES = frozenset({"citryId"})

# Names that already passed the check above. A component returns the same few
# keys on every render, so a set lookup replaces the prefix test after the
# first render. The cap keeps components that build keys from data (for
# example one key per row ID) from growing the set without limit; past it,
# new names are still checked, just not remembered.
_ACCEPTED_JS_DATA_KEYS: set[str] = set()
_ACCEPTED_JS_DATA_KEYS_LIMIT = 4096


def _check_js_data_keys(component_class: type[Any], js_data: Mapping[str, object]) -> None:
    """Reject a ``js_data()`` key that the browser runtime would refuse at mount."""
    accepted = _ACCEPTED_JS_DATA_KEYS
    for key in js_data:
        if key in accepted:
            continue
        # Only a non-string key is skipped here, because the prepared-data
        # conversion rejects it with its own error. A str subclass is still
        # checked, since it reaches the browser as an ordinary string.
        if not isinstance(key, str):
            continue
        if key.startswith(_RESERVED_JS_DATA_PREFIXES) or key in _RESERVED_JS_DATA_NAMES:
            raise ValueError(_reserved_js_data_key_message(component_class, key))
        if len(accepted) < _ACCEPTED_JS_DATA_KEYS_LIMIT:
            accepted.add(key)


def _reserved_js_data_key_message(component_class: type[Any], key: str) -> str:
    """Explain why one ``js_data()`` key is refused and suggest a usable name."""
    if key in _RESERVED_JS_DATA_NAMES:
        reason = f"Citry uses {key!r} as a prop on every component's Vue instance"
    else:
        reason = (
            f"Vue and Citry reserve names that start with {key[0]!r} on the component's Vue instance, "
            "so the browser would refuse this key when the component mounts"
        )
    # Strip the reserved prefix so the suggestion is usually the name the
    # author meant; fall back to a generic hint when nothing usable remains.
    stripped = key.lstrip("".join(_RESERVED_JS_DATA_PREFIXES))
    # A name that starts with a digit could not be read from a template
    # expression, so it is not worth suggesting.
    if stripped and stripped != key and not stripped[0].isdigit() and stripped not in _RESERVED_JS_DATA_NAMES:
        suggestion = f", for example to {stripped!r}"
    else:
        suggestion = " to a name that starts with a letter"
    return (
        f"The JavaScript data for component {component_class.__name__} (from js_data() or an extension's "
        f"on_component_data) contains the key {key!r}, but {reason}. "
        f"Rename the key{suggestion}."
    )


def _normalize_data(
    maybe_data: Any,
    schema_cls: type | None,
    *,
    preserve: _ConstMapping | None = None,
) -> _ConstMapping:
    """
    Normalize and validate one data method's result as a named mapping.

    The result of ``template_data()`` / ``js_data()`` / ``css_data()`` may be
    a dict, a NamedTuple, or the component's typed dataclass, so convert with
    ``to_dict``. When the component declares the matching schema class
    (``TemplateData``/``JsData``/``CssData``), constructing
    ``schema_cls(**data)`` raises on invalid input and materializes schema
    defaults and coercions. Convert that validated instance to a named mapping
    so every downstream consumer observes the declared schema result.
    ``preserve`` is supplied only for the renderer-owned base kwargs mapping;
    transforming schemas do not inherit const provenance. A callback that
    forwards a marked input under the same name may recover that provenance at
    the final template boundary. An exact outer ``Const`` in callback output
    establishes provenance directly and consumes nested markers inside its
    exact builtin value graph. Ordinary containers are not searched for
    manually nested markers.
    """
    if maybe_data is None:
        data = _ConstMapping()
    elif schema_cls is None and maybe_data is preserve:
        # The base untyped template_data returns the raw kwargs mapping itself.
        # Keep its historical live-sharing behavior with later data callbacks.
        shared = cast("_ConstMapping", preserve)
        _refresh_const_mapping(shared)
        return shared
    elif schema_cls is None and preserve is not None:
        # The base typed template_data returns its schema instance. Snapshot
        # its current fields now: renderer callbacks may have updated the
        # instance since input construction, while js/css callbacks that run
        # after this point must not update the template-data snapshot.
        return _const_mapping(to_dict(maybe_data), preserve=preserve)
    elif schema_cls is None and preserve is None and isinstance(maybe_data, _ConstMapping):
        # An arbitrary callback returning kwargs remains a live shared mapping,
        # and its ordinary writes have already invalidated inherited metadata.
        # Retain any still-valid same-name promise and any explicit Const the
        # callback assigned to the mapping.
        _refresh_const_mapping(maybe_data)
        return maybe_data
    else:
        data = _const_mapping(to_dict(maybe_data), preserve=preserve)

    if schema_cls is None:
        return data
    if isinstance(maybe_data, schema_cls):
        return _normalize_data_schema_instance(maybe_data, schema_cls, preserve=data)
    _validated, normalized = _construct_data_schema(data, schema_cls)
    return normalized


def _merge_dependencies(into: CitryContext, source: CitryContext) -> None:
    """
    Fire the ``on_render_context_merge`` hook: a nested render's output was consumed
    by an enclosing render, so each extension merges its own slice of
    ``source.extra`` into ``into.extra`` with its own policy (the dependencies
    extension appends its records preserving order; see
    docs/design/component_rendering.md section 6 and docs/design/extensions.md section
    9.1). The core owns only the firing, not the merge semantics.

    A render with no component on either context has no ``Citry`` instance to
    reach extensions through; there is nothing to merge for it either, since
    only component renders collect tree-wide state.
    """
    if source._error_tainted:
        into._error_tainted = True
    component = into.component if into.component is not None else source.component
    if component is None:
        return
    component.citry.extensions.on_render_context_merge(into, source)
