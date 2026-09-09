"""Deep interior content must survive scheduling scans and final serialization."""

from __future__ import annotations

from itertools import pairwise

from citry import Citry, CitryContext, CitryRender, Component
from citry.citry_render import DeferredComponent
from citry.component_render import _ContextMergeTask, _RenderTask, _scan_deferred


def test_deep_interior_scan_merges_contexts_after_their_children() -> None:
    app = Citry()

    class Leaf(Component):
        citry = app
        template = """
            leaf
        """

    leaf_context = CitryContext()
    pending = DeferredComponent(Leaf(), parent=None)
    leaf_parts = [pending]
    render = CitryRender(leaf_parts, leaf_context)
    contexts = [leaf_context]
    for _ in range(1100):
        context = CitryContext()
        contexts.append(context)
        render = CitryRender(["before", render, "after"], context)

    tasks = _scan_deferred(render)
    assert len(tasks) == len(contexts)
    assert isinstance(tasks[0], _RenderTask)
    assert tasks[0].deferred is pending
    assert tasks[0].position.parts is leaf_parts
    assert tasks[0].position.parent_context is leaf_context
    assert tasks[1:] == [_ContextMergeTask(parent, child) for child, parent in pairwise(contexts)]


def test_deep_completed_interiors_serialize_in_source_order() -> None:
    context = CitryContext()
    render = CitryRender(["end"], context)
    for index in range(1100):
        render = CitryRender([f"<div>{index}:", render, "</div>"], context)

    assert _scan_deferred(render) == []
    assert render.serialize() == (
        "".join(f"<div>{index}:" for index in reversed(range(1100))) + "end" + "</div>" * 1100
    )
