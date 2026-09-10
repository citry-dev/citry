"""Probe dynamic HTML rendering without an independent component or slot outlet."""

from __future__ import annotations

# ruff: noqa: S101 - qualification refuses optimized Python through presentation.
import json
from types import MethodType, SimpleNamespace
from typing import Any

from benchmarks.performance_followups.presentation import baseline, callback_counts, load

from citry.citry_render import CitryRender
from citry.component_render import _render_body
from citry.components.dynamic import _format_element_attrs, _pop_html_attr, _validate_tag_name
from citry.constness import const_value
from citry.nodes import ComponentNode
from citry.util.html import Markup
from citry_core.template_parser import HTML_VOID_ELEMENTS

ORIGINAL_INIT = ComponentNode.__init__


def direct_render(node: ComponentNode, context: Any) -> CitryRender:
    """Use the caller for attributes and children under an experimental contract."""
    resolved = node._resolve_inputs(context)
    assert not resolved.client_bindings
    attrs = dict(resolved.kwargs)
    tag = const_value(_pop_html_attr(attrs, "is"))
    _validate_tag_name(tag)
    # The shared formatter needs only these renderer fields in this restricted case.
    renderer = SimpleNamespace(parent=context.component, citry=context.component.citry, _element_morph_metadata=None)
    formatted = _format_element_attrs(renderer, tag, attrs)
    if tag.lower() in HTML_VOID_ELEMENTS:
        if any(not isinstance(item, str) or item.strip() for item in node.body):
            raise ValueError(f"<c-element>: void element '{tag}' cannot have children.")
        return CitryRender([Markup("<{}{}/>").format(tag, formatted)], context)
    parts = [Markup("<{}{}>").format(tag, formatted), *_render_body(node.body, context), Markup("</{}>").format(tag)]
    return CitryRender(parts, context)


def specialized_init(node: ComponentNode, *args: Any, **kwargs: Any) -> None:
    """Select eligible built-in calls once when compiled nodes are constructed."""
    ORIGINAL_INIT(node, *args, **kwargs)
    if node.name == "element" and not node.contains_fills and node.metadata is None:
        node.render = MethodType(direct_render, node)


def install() -> None:
    """Enable this process-local research candidate before templates compile."""
    ComponentNode.__init__ = specialized_init


def qualify() -> dict[str, Any]:
    """Compare the released simple configuration under the proposed identity change."""
    baseline.ids._id_base = 123456
    control, tree_hash = load()
    before, _ = baseline.observe(control, control.gen_render_data())
    callbacks = callback_counts(control)
    install()
    candidate, _ = load()
    after, _ = baseline.observe(candidate, candidate.gen_render_data())
    assert before["projected_sha256"] == after["projected_sha256"]
    assert callback_counts(candidate) == callbacks
    expected = dict(before["component_calls"])
    removed = expected.pop("DynamicElement")
    assert after["component_calls"] == expected
    assert before["generated_ids"] - after["generated_ids"] == removed
    return {
        "control": before,
        "candidate": after,
        "callbacks": callbacks,
        "removed_dynamic_calls": removed,
        "scenario_sha256": tree_hash,
    }


if __name__ == "__main__":
    print(json.dumps(qualify()))
