"""Give the benchmark's selected icon fresh identity without a live Component."""

from __future__ import annotations

from typing import Any

from benchmarks.template_function_probe.runtime import validate_values

import citry.component as component_module
from citry import component_render as runtime
from citry.citry_context import CitryContext
from citry.citry_render import CitryRender, RenderFrame
from citry.constness import _ConstProxy
from citry.ownership import current_ownership_graph

ATTRS = frozenset(
    {
        "class",
        "style",
        "viewBox",
        "aria-hidden",
        "fill",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "d",
        "title",
        "width",
        "height",
        "role",
    }
)


class IdentityRender(CitryRender):
    """Retain the normal root frame while finalization skips component hooks."""

    __slots__ = ()


def plain(value: Any, ancestors: set[int] | None = None) -> Any:
    """Read Const inputs while rejecting custom containers and conversion callbacks."""
    while type(value) is _ConstProxy:
        value = value.__wrapped__
    if type(value) not in (dict, list, tuple):
        validate_values(value)
        return value
    if ancestors is None:
        ancestors = set()
    key = id(value)
    if key in ancestors:
        raise ValueError("Icon function inputs must be acyclic")
    ancestors.add(key)
    try:
        if type(value) is dict:
            if any(type(name) is not str for name in value):
                raise TypeError("Icon function mapping keys must be exact strings")
            return {name: plain(child, ancestors) for name, child in value.items()}
        return type(value)(plain(child, ancestors) for child in value)
    finally:
        ancestors.remove(key)


def validate_attributes(values: Any) -> None:
    """Constrain dynamic names so this body cannot introduce client behavior."""
    if values is None:
        return
    if type(values) is not dict or any(type(key) is not str or key not in ATTRS for key in values):
        raise TypeError("Icon function supports only declared ordinary SVG attributes")
    validate_values(values)


def install(module: Any, enabled: bool) -> None:
    """Select one trusted fixture class; leave the ordinary runtime installed otherwise."""
    selected = module.HeroIcon
    original_render = runtime._render_one
    original_finalize = runtime._finalize
    body = None
    compiled = None
    # The existing binding function accepts class metadata through this temporary
    # object. Plain instance fields keep its ordinary native-journal path active.
    identity_type = type(selected.__name__, (), {"transparent": selected.transparent})

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
        metadata = identity_type()
        generator = selected.citry.id_generator or component_module.gen_render_id
        metadata.id = component_module.validate_render_id(generator())
        metadata._citry_class_id = selected.class_id
        ownership.bind_instance(metadata, element)
        values = plain(element.kwargs)
        validate_values(values)
        validate_attributes(values.get("attrs"))
        # Schema construction and application data still run for every occurrence.
        kwargs = selected.Kwargs(**values)
        data = selected.template_data(None, kwargs, {})
        validate_values(data)
        validate_attributes(data["default_attrs"])
        validate_attributes(data["attrs"])
        for attrs in data["icon_paths"]:
            validate_attributes(attrs)
        if body is None:
            compiled = runtime._get_compiled_template(selected)
            body = compiled.generate()
        context = CitryContext(
            variables=data,
            ownership=ownership,
            sandboxed=selected.citry.settings.sandbox_expressions,
            template_record=compiled,
        )
        result = IdentityRender(
            runtime._render_body(body, context),
            context,
            frame=RenderFrame(metadata.id, selected.class_id, selected.__name__, not selected.transparent, ()),
        )
        return runtime._InitialRender(result, None, None, None)

    def finalize(rendered: CitryRender, error: Exception | None) -> CitryRender:
        if type(rendered) is not IdentityRender:
            return original_finalize(rendered, error)
        rendered.context.ownership.settle_component(rendered.frame.render_id, failed=error is not None)
        if error is not None:
            raise error
        return rendered

    if enabled:
        runtime._render_one = render
        runtime._finalize = finalize
