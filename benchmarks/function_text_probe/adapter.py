"""Emit fixed caller-owned function bodies into one buffer, retaining structured children."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from benchmarks.composed_function_probe.adapter import FunctionRender
from benchmarks.composed_function_probe.adapter import installed as composed_installed
from benchmarks.leaf_contract_probe.adapter import ATTRS, plain

from citry import component_render as runtime
from citry._pure import pure_body_lookup, store_pure_body
from citry.citry_context import CitryContext
from citry.citry_render import CitryRender, DeferredComponent, unwrap_physical_region
from citry.nodes import ComponentNode, ForNode, IfNode, SlotNode


@contextmanager
def installed(module: Any, enabled: bool, counts: dict[str, int] | None = None) -> Any:
    """Compare direct emission with the unchanged immediate composed implementation."""
    with composed_installed(module, "immediate", counts):
        if not enabled:
            yield
            return
        reference_node = ComponentNode.render
        selected = {cls.name.lower(): cls for cls in (module.Button, module.Icon, module.HeroIcon)}
        prepared: dict[type, tuple[Any, Any]] = {}

        def selected_class(node: Any, context: CitryContext) -> type | None:
            cls = selected.get(node.name)
            owner = context.component
            # Serialization may surround a transparent component's interior output with identity markers.
            if cls is None or owner is None or type(owner).transparent or owner.citry.get(node.name) is not cls:
                return None
            return cls

        def append_part(part: Any, context: CitryContext, out: list[Any]) -> bool:
            if isinstance(part, str):
                out.append(part)
                return False
            value = unwrap_physical_region(part)
            deferred = isinstance(value, DeferredComponent) or (
                isinstance(value, CitryRender) and runtime._contains_deferred(value)
            )
            if isinstance(value, CitryRender) and value.context is not context and not deferred:
                runtime._merge_dependencies(context, value.context)
            out.append(part)
            return deferred

        def emit(body: Any, context: CitryContext, out: list[Any], outlet: Any = None) -> bool:
            deferred = False
            for item in body:
                if isinstance(item, str):
                    out.append(item)
                    continue
                try:
                    if type(item) is IfNode:
                        branch = item.active_branch_body(context)
                        if branch is not None:
                            deferred = emit(branch, context, out, outlet) or deferred
                    elif type(item) is ForNode and item._precomputed_text is None:
                        for branch, child_context in item.iter_bodies(context):
                            deferred = emit(branch, child_context, out, outlet) or deferred
                    elif type(item) is SlotNode and outlet is not None:
                        if item.attrs or item.body or item.introduced_vars:
                            raise TypeError("Template function supports only its empty default outlet")
                        if counts is not None:
                            counts["outlets"] = counts.get("outlets", 0) + 1
                        deferred = outlet(out) or deferred
                    elif type(item) is ComponentNode and (cls := selected_class(item, context)) is not None:
                        function_context, nested_deferred = execute(cls, item, context, out)
                        if not nested_deferred:
                            runtime._merge_dependencies(context, function_context)
                        deferred = nested_deferred or deferred
                    else:
                        deferred = append_part(item.render(context), context, out) or deferred
                except Exception as error:
                    runtime._attach_template_position(error, item, context)
                    raise
            return deferred

        def execute(cls: type, node: Any, caller: CitryContext, out: list[Any]) -> tuple[CitryContext, bool]:
            if node.contains_fills or node.metadata is not None or (cls is module.HeroIcon and node.body):
                raise TypeError("Template function requires implicit default content and no range directives")
            if cls.citry.template_globals or runtime._render_globals.get():
                raise TypeError("Template function does not support template globals")
            resolved = node._resolve_inputs(caller)
            if resolved.client_bindings:
                raise TypeError("Template function does not support component client bindings")
            try:
                values = plain(resolved.kwargs)
            except (TypeError, ValueError) as error:
                raise type(error)(str(error).replace("Icon function", "Template function")) from error
            if cls is module.HeroIcon:
                attrs = values.get("attrs")
                if attrs is not None and (type(attrs) is not dict or any(name not in ATTRS for name in attrs)):
                    raise TypeError("SVG function supports only declared ordinary SVG attributes")
            kwargs = cls.Kwargs(**values)
            data = cls.template_data(None, kwargs, {})
            if counts is not None:
                counts[cls.__name__] = counts.get(cls.__name__, 0) + 1
            entry = prepared.get(cls)
            if entry is None:
                compiled = runtime._get_compiled_template(cls)
                entry = prepared[cls] = (compiled, compiled.generate())
            compiled, body = entry
            context = CitryContext(
                variables=data,
                component=caller.component,
                extra=None if cls is module.HeroIcon else caller.extra,
                provides=caller.provides,
                ownership=caller.ownership,
                sandboxed=caller.sandboxed,
                template_record=compiled,
            )

            def content(target: list[Any]) -> bool:
                if all(isinstance(item, str) and not item.strip() for item in node.body):
                    return False
                # The caller's own slot nodes must not select this function's outlet.
                return emit(node.body, caller, target)

            if cls is not module.HeroIcon:
                return context, emit(body, context, out, content)
            lookup = pure_body_lookup(cls, body, data, compiled.used_vars)
            if lookup is not None and lookup[1] is not None:
                out.extend(runtime._replay_pure_body(lookup[1], context))
                if counts is not None:
                    counts["svg_replays"] = counts.get("svg_replays", 0) + 1
                return context, False
            checkpoint = caller.ownership.checkpoint()
            svg: list[Any] = []
            has_deferred = emit(body, context, svg)
            if (
                has_deferred
                or not all(isinstance(part, str) for part in svg)
                or caller.ownership.checkpoint() != checkpoint
                or context.extra
                or context._error_tainted
            ):
                raise TypeError("SVG function produced unsupported render effects")
            text = "".join(svg)
            if lookup is not None:
                store_pure_body(lookup[0], (text,))
            out.append(text)
            return context, False

        def node_render(node: Any, caller: CitryContext) -> Any:
            cls = selected_class(node, caller)
            if cls is None:
                return reference_node(node, caller)
            parts: list[Any] = []
            context, deferred = execute(cls, node, caller, parts)
            if not deferred and all(isinstance(part, str) for part in parts):
                text = "".join(parts)
                # A pure caller must retain this live call rather than caching its output string.
                if type(caller.component).pure:
                    return FunctionRender([text], context)
                runtime._merge_dependencies(caller, context)
                return text
            # The scheduler still needs positions for ordinary deferred children.
            return FunctionRender(parts, context)

        ComponentNode.render = node_render
        try:
            yield
        finally:
            ComponentNode.render = reference_node
