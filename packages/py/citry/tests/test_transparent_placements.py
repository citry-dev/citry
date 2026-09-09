"""Transparent instances have one physical boundary across their interior renders."""

from __future__ import annotations

import json
import re
from dataclasses import replace

import pytest

from citry import Citry, CitryContext, CitryRender, Component, Extension
from citry.citry_render import RenderFrame
from citry.ownership import OwnershipGraph
from citry.ownership_manifest import _transparent_instance_placements


def test_transparent_caller_control_flow_and_fills_share_one_instance_boundary() -> None:
    app = Citry()

    class Receiver(Component):
        citry = app
        template = """
            <section><c-slot /></section>
        """
        js = """
            $component(() => {});
        """

    class Page(Component):
        citry = app
        transparent = True
        template = """
            <c-if cond="visible">
                <div><c-receiver><b x-data="{name: 'hello'}" x-text="name"></b></c-receiver></div>
            </c-if>
        """

    rendered = Page(visible=True).render()
    html = rendered.serialize()
    match = re.search(r'<script type="application/json" data-citry-graph>(.*?)</script>', html, re.DOTALL)
    assert match is not None
    manifest = json.loads(match.group(1))
    assert any(record["transparent"] for graph in manifest["graphs"] for record in graph["componentInstances"])
    for graph in manifest["graphs"]:
        for kind, records, id_field in (
            ("i", graph["componentInstances"], "instanceId"),
            ("r", graph["slotRegions"], "regionId"),
        ):
            for record in records:
                for side in ("s", "e"):
                    cap = (
                        f"<!--citry:g1:{manifest['revision'][:8]}:{graph['graphId']}:"
                        f"{kind}:{record[id_field]}:{side}-->"
                    )
                    assert html.count(cap) == 1
    assert rendered.serialize() == html


def test_disconnected_transparent_occurrences_are_rejected() -> None:
    graph = OwnershipGraph()
    context = CitryContext(ownership=graph)
    frame = RenderFrame(
        render_id="owner",
        class_id="class",
        class_name="Owner",
        is_component_root=False,
        root_markers=(),
        is_transparent_root=True,
    )
    left = CitryRender(["left"], context, frame=frame)
    right = CitryRender(["right"], context, frame=frame)
    root = CitryRender([left, right], context)

    with pytest.raises(RuntimeError, match="transparent component occurrence has disconnected output"):
        _transparent_instance_placements(root, frozenset({(id(graph), "owner")}))


def test_missing_transparent_placement_is_rejected() -> None:
    graph = OwnershipGraph()
    root = CitryRender([], CitryContext(ownership=graph))
    with pytest.raises(RuntimeError, match="no physical output placement"):
        _transparent_instance_placements(root, frozenset({(id(graph), "missing")}))


@pytest.mark.parametrize("root_first", [False, True])
def test_remote_caller_interiors_do_not_select_the_instance_boundary(root_first: bool) -> None:
    graph = OwnershipGraph()
    context = CitryContext(ownership=graph)
    frame = RenderFrame(
        render_id="owner",
        class_id="class",
        class_name="Owner",
        is_component_root=False,
        root_markers=(),
        is_transparent_root=True,
    )
    declaration = CitryRender(["declarations"], context, frame=frame)
    interior = CitryRender(["remote fill"], context, frame=replace(frame, is_transparent_root=False))
    parts = [declaration, interior] if root_first else [interior, declaration]
    root = CitryRender(parts, context)
    included = frozenset({(id(graph), "owner")})
    assert _transparent_instance_placements(root, included) == frozenset({id(declaration)})
    with pytest.raises(RuntimeError, match="no physical output placement"):
        _transparent_instance_placements(interior, included)
    with pytest.raises(RuntimeError, match="disconnected output"):
        _transparent_instance_placements(CitryRender([declaration, declaration], context), included)


@pytest.mark.parametrize("replacement", ["text", "same-context", "foreign-context", "generator"])
def test_transparent_output_marker_survives_hook_replacements(replacement: str) -> None:
    class Replace(Extension):
        name = "replace_transparent_test"

        def on_component_rendered(self, ctx):
            if ctx.render is None or type(ctx.component).__name__ != "Wrapper":
                return None
            if replacement == "text":
                return "replacement"
            if replacement == "same-context":
                return CitryRender(["replacement"], ctx.render.context)
            if replacement == "foreign-context":
                return CitryRender(["replacement"], CitryContext())
            return None

    app = Citry(extensions=[Replace])

    class Wrapper(Component):
        citry = app
        transparent = True

        def on_render(self):
            yield
            if replacement == "generator":
                yield "replacement"

        template = """
            original
        """

    rendered = Wrapper().render()
    assert rendered.frame.is_transparent_root
    graph = rendered.context.ownership
    assert graph is not None
    included = frozenset({(id(graph), rendered.frame.render_id)})
    assert _transparent_instance_placements(rendered, included) == frozenset({id(rendered)})
    assert "replacement" in rendered.serialize()
