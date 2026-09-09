"""Execute the fixed Button template in its caller's ownership scope."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from benchmarks.leaf_contract_probe.adapter import plain

from citry import component_render as runtime
from citry.citry_context import CitryContext
from citry.citry_render import CitryRender
from citry.nodes import ComponentNode, SlotNode


@contextmanager
def installed(module: Any, enabled: bool, counts: dict[str, int] | None = None) -> Any:
    """Select direct Button tags and restore both entry points after the experiment."""
    original_node = ComponentNode.render
    original_slot = SlotNode.render
    selected = module.Button
    outlet: ContextVar[Any] = ContextVar("wrapper_function_outlet", default=None)
    compiled = None
    body = None

    def slot_render(node: Any, context: CitryContext) -> Any:
        content = outlet.get()
        if content is None:
            return original_slot(node, context)
        if node.attrs or node.body or node.introduced_vars:
            raise TypeError("Wrapper function supports only its empty default outlet")
        if counts is not None:
            counts["outlets"] = counts.get("outlets", 0) + 1
        # Caller content can itself contain ordinary slots or nested wrappers.
        token = outlet.set(None)
        try:
            return content()
        finally:
            outlet.reset(token)

    def node_render(node: Any, caller: CitryContext) -> Any:
        nonlocal compiled, body
        owner = caller.component
        if node.name != selected.name.lower() or owner is None or owner.citry.get(node.name) is not selected:
            return original_node(node, caller)
        if node.contains_fills or node.metadata is not None:
            raise TypeError("Wrapper function requires implicit default content and no range directives")
        if selected.citry.template_globals or runtime._render_globals.get():
            raise TypeError("Wrapper function does not support template globals")
        resolved = node._resolve_inputs(caller)
        if resolved.client_bindings:
            raise TypeError("Wrapper function does not support component client bindings")
        try:
            values = plain(resolved.kwargs)
        except (TypeError, ValueError) as error:
            raise type(error)(str(error).replace("Icon function", "Wrapper function")) from error
        kwargs = selected.Kwargs(**values)
        data = selected.template_data(None, kwargs, {})
        if counts is not None:
            counts["callbacks"] = counts.get("callbacks", 0) + 1
        if body is None:
            compiled = runtime._get_compiled_template(selected)
            body = compiled.generate()
        context = CitryContext(
            variables=data,
            component=owner,
            provides=caller.provides,
            ownership=caller.ownership,
            sandboxed=caller.sandboxed,
            template_record=compiled,
        )

        def content() -> CitryRender:
            return CitryRender(runtime._render_body(node.body, caller), caller)

        token = outlet.set(content)
        try:
            return CitryRender(runtime._render_body(body, context), context)
        finally:
            outlet.reset(token)

    try:
        if enabled:
            ComponentNode.render = node_render
            SlotNode.render = slot_render
        yield
    finally:
        ComponentNode.render = original_node
        SlotNode.render = original_slot
