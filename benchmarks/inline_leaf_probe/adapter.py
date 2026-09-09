"""Render selected icon SVG as caller-owned output while keeping deferred evaluation."""

from __future__ import annotations

from typing import Any

from benchmarks.leaf_contract_probe.adapter import ATTRS, plain

from citry import component_render as runtime
from citry._pure import pure_body_lookup, store_pure_body
from citry.citry_context import CitryContext
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender, DeferredComponent
from citry.nodes import ComponentNode
from citry.ownership import current_ownership_graph


class InlineElement(CitryElement):
    """Identify descriptors created by the selected direct template tag."""

    __slots__ = ()


def install(module: Any, enabled: bool) -> None:
    """Select one trusted fixture class; leave the ordinary runtime installed otherwise."""
    selected = module.HeroIcon
    original_render = runtime._render_one
    original_node_render = ComponentNode.render
    body = None
    compiled = None

    def node_render(node: Any, context: CitryContext) -> Any:
        component = context.component
        if node.name != selected.name or component is None or component.citry.get(node.name) is not selected:
            return original_node_render(node, context)
        if node.body or node.metadata is not None:
            raise TypeError("Inline icons do not support slots or component range directives")
        resolved = node._resolve_inputs(context)
        if resolved.client_bindings:
            raise TypeError("Inline icons do not support component client bindings")
        # Keep evaluation deferred so this experiment changes identity rather
        # than callback order. The tag creates no invocation, source-location, or queue record.
        element = InlineElement(selected, resolved.kwargs, {}, ownership_graph=context.ownership)
        return DeferredComponent(
            element,
            component,
            context.provides,
            physical_parent_region_id=context.ownership.current_region_id(),
        )

    def render(element: Any, parent: Any = None, provides: Any = None) -> Any:
        nonlocal body, compiled
        if element.comp_cls is not selected:
            return original_render(element, parent, provides)
        if parent is None:
            raise TypeError("Icon function requires an ordinary enclosing component")
        if (
            element.slots
            or element.component_tag_client_bindings
            or element.element_morph_metadata is not None
            or element.forward_ownership_invocation
            or getattr(element, "_template_override", None) is not None
            or selected.citry.template_globals
            or runtime._render_globals.get()
        ):
            raise TypeError("Icon function does not support slots, client directives or template overrides/globals")
        if type(element.kwargs) is not dict:
            raise TypeError("Icon function inputs must be an exact dictionary")
        ownership = element.ownership_graph or current_ownership_graph()
        if ownership is None:
            raise RuntimeError("Icon function requires an enclosing ownership graph")
        if type(element) is not InlineElement or element.ownership_invocation_id is not None:
            raise TypeError("Inline icons require a direct selected template tag")
        values = plain(element.kwargs)
        attrs = values.get("attrs")
        if attrs is not None and (type(attrs) is not dict or any(name not in ATTRS for name in attrs)):
            raise TypeError("Icon function supports only declared ordinary SVG attributes")
        # Schema construction and application data still run for every occurrence.
        kwargs = selected.Kwargs(**values)
        data = selected.template_data(None, kwargs, {})
        if body is None:
            compiled = runtime._get_compiled_template(selected)
            body = compiled.generate()
        context = CitryContext(
            variables=data,
            ownership=ownership,
            sandboxed=selected.citry.settings.sandbox_expressions,
            template_record=compiled,
        )
        # Reuse keys and prepared output stored for the current root render. The selected contract
        # excludes i18n and all body effects, so capture needs no live instance.
        lookup = pure_body_lookup(selected, body, data, compiled.used_vars)
        if lookup is not None and lookup[1] is not None:
            parts = runtime._replay_pure_body(lookup[1], context)
        else:
            checkpoint = ownership.checkpoint()
            parts = runtime._render_body(body, context)
            if lookup is not None:
                plan = tuple(runtime._capture_pure_part(part, context) for part in parts)
                if any(part is None for part in plan) or ownership.checkpoint() != checkpoint or context.extra:
                    raise TypeError("Icon function body produced unsupported render effects")
                store_pure_body(lookup[0], plan)
        return runtime._InitialRender(CitryRender(parts, context), None, None, None)

    if enabled:
        runtime._render_one = render
        ComponentNode.render = node_render
