"""A2 versioned ownership manifest, typed client bindings, and physical caps."""

from __future__ import annotations

import json
import re

import pytest

from citry import Citry, Component
from citry._protocol import client_graph
from citry.ownership_manifest import COMMENT_PREFIX, PROTOCOL, OwnershipManifestArtifact

_GRAPH_RE = re.compile(
    r'<script type="application/json" data-citry-graph>(.*?)</script>',
    re.DOTALL,
)
_EVENTS_RE = re.compile(
    r'<script type="application/json" data-citry-events>(.*?)</script>',
    re.DOTALL,
)
_DEPS_RE = re.compile(
    r'<script type="application/json" data-citry>(.*?)</script>',
    re.DOTALL,
)


def _manifest(html: str) -> dict:
    match = _GRAPH_RE.search(html)
    assert match is not None
    return json.loads(match.group(1))


def test_document_manifest_is_deterministic_discriminated_and_ordered():
    c = Citry()

    class Child(Component):
        citry = c
        js = """
          $component(() => {});
        """
        template = "<span>child</span>"

    class Page(Component):
        citry = c

        class Events:
            def save(self):
                return None

        template = """
          <c-child
            $c-props="{count: localCount}"
            @click="selected = true"
            @c-click.prevent="save({value: `closed )`})"
          />
        """

    render = Page().render()
    first = render.serialize()
    second = render.serialize()
    manifest = _manifest(first)

    assert first == second
    assert manifest["protocol"] == PROTOCOL
    assert manifest["mode"] == "production"
    assert manifest["delimiters"] == {"format": COMMENT_PREFIX}
    assert len(manifest["revision"]) == 64
    client_bindings = manifest["graphs"][0]["nestedComponents"][0]["clientBindings"]
    assert [client_binding["payload"]["type"] for client_binding in client_bindings] == [
        "props",
        "alpine-handler",
        "citry-dom-event",
    ]
    citry_payload = client_bindings[-1]["payload"]
    assert citry_payload["prevent"] is True
    assert citry_payload["handler"] == "save"
    assert citry_payload["args"] == "{value: `closed )`}"

    graph_pos = first.index("data-citry-graph")
    events_pos = first.index("data-citry-events")
    deps_pos = first.index("data-citry>")
    assert graph_pos < events_pos < deps_pos
    events_match = _EVENTS_RE.search(first)
    deps_match = _DEPS_RE.search(first)
    assert events_match is not None
    assert deps_match is not None
    events = json.loads(events_match.group(1))
    deps = json.loads(deps_match.group(1))
    assert events["clientGraphRevision"] == deps["graph"] == manifest["revision"]


def test_single_multi_rootless_adjacent_and_nested_ranges_have_balanced_caps():
    c = Citry()

    class Shell(Component):
        citry = c
        template = "before<c-slot />middle<c-slot />after"

    class Page(Component):
        citry = c
        js = "$component(() => {})"
        template = "<c-shell><i>a</i><b>b</b></c-shell>"

    html = Page().render().serialize()
    manifest = _manifest(html)
    revision = manifest["revision"]
    prefix = manifest["delimiters"]["format"]
    caps = re.findall(rf"<!--{re.escape(prefix)}:{revision}:(\d+):([ir]):(\d+):([se])-->", html)

    expected = {
        (str(graph["graphId"]), kind, str(record[id_key]))
        for graph in manifest["graphs"]
        for kind, records, id_key in (
            ("i", graph["componentInstances"], "instanceId"),
            ("r", graph["slotRegions"], "regionId"),
        )
        for record in records
    }
    assert {(graph, kind, record) for graph, kind, record, _ in caps} == expected
    for graph, kind, record in expected:
        assert caps.count((graph, kind, record, "s")) == 1
        assert caps.count((graph, kind, record, "e")) == 1
    assert "before<!--citry:" in html
    assert re.search(r"<i [^>]*>a</i>", html)
    assert re.search(r"<b [^>]*>b</b>", html)


def test_template_fill_alone_emits_graph_and_activates_both_scope_endpoints():
    c = Citry()

    class Card(Component):
        citry = c
        template = '<section><c-slot name="body"><i>fallback</i></c-slot></section>'

    class Page(Component):
        citry = c
        template = '<main><c-card><c-fill name="body"><button x-text="label"></button></c-fill></c-card></main>'

    html = Page().render().serialize()
    manifest = _manifest(html)
    graph = manifest["graphs"][0]

    assert len(graph["fills"]) == 1
    assert graph["fills"][0]["policy"] == "template"
    assert len(graph["slotRegions"]) == 1
    assert html.count('data-citry-root=""') == 2
    assert "Citry events client runtime. GENERATED FILE" in html


def test_plain_server_only_template_fill_does_not_load_the_client_runtime():
    c = Citry()

    class Card(Component):
        citry = c
        template = '<section><c-slot name="body" /></section>'

    class Page(Component):
        citry = c
        template = '<main><c-card><c-fill name="body">plain</c-fill></c-card></main>'

    html = Page().render().serialize()

    assert "plain" in html
    assert "data-citry-graph" not in html
    assert "Citry events client runtime. GENERATED FILE" not in html


def test_client_context_magic_alone_emits_the_graph_and_alpine_runtime():
    c = Citry()

    class MagicTree(Component):
        citry = c
        template = """
          <section x-init="$provide('theme', { name: 'blue' })">
            <output x-text="$inject('theme').name"></output>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <c-magic-tree />
        """

    html = Page().render().serialize()

    assert "data-citry-graph" in html
    assert html.count('data-citry-root=""') == 1
    assert "Citry events client runtime. GENERATED FILE" in html


def test_context_magic_text_outside_an_alpine_attribute_does_not_activate_the_client():
    c = Citry()

    class Page(Component):
        citry = c
        template = """
          <code>$inject('theme')</code>
        """

    html = Page().render().serialize()

    assert "data-citry-graph" not in html
    assert "Citry events client runtime. GENERATED FILE" not in html


def test_context_magic_in_a_data_attribute_does_not_activate_the_client():
    c = Citry()

    class Page(Component):
        citry = c
        template = """
          <main data-x-init="$inject('theme')"></main>
        """

    html = Page().render().serialize()

    assert "data-citry-graph" not in html
    assert "Citry events client runtime. GENERATED FILE" not in html


@pytest.mark.parametrize(
    "expression",
    [
        "($inject)('theme')",
        "$inject?.('theme')",
        "consume($inject)",
    ],
)
def test_context_magic_reference_in_an_alpine_attribute_activates_the_client(expression: str):
    c = Citry()

    class Page(Component):
        citry = c
        template = f"""
          <main x-init="{expression}"></main>
        """

    html = Page().render().serialize()

    assert "data-citry-graph" in html
    assert "Citry events client runtime. GENERATED FILE" in html


def test_detached_python_fill_does_not_create_a_client_graph_by_itself():
    c = Citry()

    class Card(Component):
        citry = c
        template = """
          <section>
            <c-slot />
          </section>
        """

    html = Card(slots={"default": "plain Python content"}).render().serialize()

    assert "data-citry-graph" not in html
    assert "data-citry-root" not in html
    assert "Citry events client runtime. GENERATED FILE" not in html


def test_source_ranges_use_utf8_bytes_in_post_hook_runtime_source():
    c = Citry(mode="development")

    class Child(Component):
        citry = c
        template = "<button>child</button>"

    class Page(Component):
        citry = c
        template = 'π<c-child @click="selected = true" />'

    html = Page().render().serialize()
    manifest = _manifest(html)
    graph = manifest["graphs"][0]
    client_binding = graph["nestedComponents"][0]["clientBindings"][0]
    location = next(
        record for record in graph["sourceLocations"] if record["locationId"] == client_binding["locationId"]
    )
    source_bytes = Page.template.encode("utf8")
    start = location["sourceOffset"]["start"]
    end = location["sourceOffset"]["end"]

    assert source_bytes[start:end].decode("utf8") == '@click="selected = true"'


def test_same_citry_foreign_render_graphs_aggregate_in_physical_order():
    c = Citry()

    class Foreign(Component):
        citry = c
        js = "$component(() => {})"
        template = "<aside>foreign</aside>"

    foreign = Foreign().render()

    class Page(Component):
        citry = c
        template = "before{{ foreign }}after"

        def template_data(self, kwargs, slots):
            return {"foreign": foreign}

    manifest = _manifest(Page().render().serialize())
    graph_classes = [[record["className"] for record in graph["componentClasses"]] for graph in manifest["graphs"]]

    assert len(manifest["graphs"]) == 2
    assert graph_classes == [["Page"], ["Foreign"]]


def test_runtime_dynamic_selector_is_transparent_in_the_wire_graph():
    c = Citry()

    class Target(Component):
        citry = c
        js = """
          $component(() => {});
        """
        template = "<button>target</button>"

    class Page(Component):
        citry = c
        js = "$component(() => {})"
        template = '<c-component c-is="target" $c-props="{value: 1}" />'

        def template_data(self, kwargs, slots):
            return {"target": Target}

    manifest = _manifest(Page().render().serialize())
    graph = manifest["graphs"][0]
    class_names = [record["className"] for record in graph["componentClasses"]]
    invocation = graph["nestedComponents"][0]

    assert class_names == ["Page", "Target"]
    assert len(graph["componentInstances"]) == 2
    assert invocation["targetClassId"] == Target.class_id
    assert invocation["targetRenderId"] == graph["componentInstances"][1]["renderId"]
    assert invocation["clientBindings"][0]["payload"]["type"] == "props"


def test_cache_includes_transparent_slot_boundary_and_parent_region_caps():
    c = Citry()

    class ActiveChild(Component):
        citry = c
        js = "$component(() => {})"
        template = """\
<button>child</button>\
"""

    class Page(Component):
        citry = c
        template = """\
<c-cache key="example"><c-active-child /></c-cache>\
"""

    html = Page().render().serialize()
    manifest = _manifest(html)
    graph = manifest["graphs"][0]
    region_ids = {record["regionId"] for record in graph["slotRegions"]}
    nested_invocation = next(record for record in graph["nestedComponents"] if record["parentRegionId"] is not None)
    transparent_instance = next(record for record in graph["componentInstances"] if record["transparent"])

    assert len(graph["componentInstances"]) == 3
    assert len(region_ids) == 1
    assert nested_invocation["parentRegionId"] in region_ids
    revision = manifest["revision"]
    prefix = manifest["delimiters"]["format"]
    instance_id = transparent_instance["instanceId"]
    assert html.count(f"<!--{prefix}:{revision}:0:i:{instance_id}:s-->") == 1
    assert html.count(f"<!--{prefix}:{revision}:0:i:{instance_id}:e-->") == 1


def test_nested_caches_retain_region_ancestry_matching_physical_caps():
    c = Citry()

    class Page(Component):
        citry = c
        template = """\
<c-cache key="outer"><c-cache key="inner"><button x-data="{ n: 9 }">child</button></c-cache></c-cache>\
"""

    html = Page().render().serialize()
    manifest = _manifest(html)
    graph = manifest["graphs"][0]
    outer_region, inner_region = graph["slotRegions"]
    revision = manifest["revision"]
    prefix = manifest["delimiters"]["format"]
    outer_start = f"<!--{prefix}:{revision}:0:r:{outer_region['regionId']}:s-->"
    outer_end = f"<!--{prefix}:{revision}:0:r:{outer_region['regionId']}:e-->"
    inner_start = f"<!--{prefix}:{revision}:0:r:{inner_region['regionId']}:s-->"
    inner_end = f"<!--{prefix}:{revision}:0:r:{inner_region['regionId']}:e-->"

    assert outer_region["parentRegionId"] is None
    assert inner_region["parentRegionId"] == outer_region["regionId"]
    assert html.index(outer_start) < html.index(inner_start) < html.index(inner_end) < html.index(outer_end)


def test_deferred_on_render_replacement_keeps_its_physical_parent_region():
    c = Citry()

    class Active(Component):
        citry = c
        js = "$component(() => {})"
        template = """\
<button>active</button>\
"""

    class Outlet(Component):
        citry = c
        template = """\
<c-slot />\
"""

    class Replace(Component):
        citry = c
        template = """\
initial\
"""

        def on_render(self):
            yield
            return Outlet(slots={"default": Active()})

    class Page(Component):
        citry = c
        template = """\
<c-cache key="outer"><c-replace /></c-cache>\
"""

    html = Page().render().serialize()
    graph = _manifest(html)["graphs"][0]
    outer_region, replacement_region = graph["slotRegions"]

    assert outer_region["parentRegionId"] is None
    assert replacement_region["parentRegionId"] == outer_region["regionId"]


def test_render_tree_owned_by_another_citry_instance_is_rejected():
    outer = Citry()
    foreign_citry = Citry()

    class Foreign(Component):
        citry = foreign_citry
        js = "$component(() => {})"
        template = "<aside>foreign</aside>"

    foreign = Foreign().render()

    class Page(Component):
        citry = outer
        js = "$component(() => {})"
        template = "{{ foreign }}"

        def template_data(self, kwargs, slots):
            return {"foreign": foreign}

    with pytest.raises(RuntimeError, match="different Citry instances"):
        Page().render().serialize()


def test_delayed_cross_graph_template_result_is_rejected_when_v1_cannot_qualify_its_parent():
    c = Citry()
    captured = []

    class Inner(Component):
        citry = c
        template = "<i>inner</i>"

    class Capture(Component):
        citry = c
        template = "captured"

        def template_data(self, kwargs, slots):
            captured.append(slots["default"])
            return {}

    class Page(Component):
        citry = c
        template = "<c-capture><c-inner /></c-capture>"

    class Outlet(Component):
        citry = c
        js = "$component(() => {})"
        template = "<section><c-slot /></section>"

    Page().render()
    delayed = Outlet(slots={"default": captured[0]}).render()

    with pytest.raises(RuntimeError, match="cross-graph relation"):
        delayed.serialize()


def test_same_graph_render_hook_fragment_rebases_an_inert_outer_fill_boundary():
    c = Citry()
    captured: list[str] = []

    class ActiveChild(Component):
        citry = c
        js = "$component(() => {})"
        template = '<button x-data="{ local: true }">child</button>'

    class Capture(Component):
        citry = c
        template = "<c-slot />"

        def on_render(self):
            result, error = yield
            if error is not None:
                return None
            assert result is not None
            captured.append(str(result))
            return None

    class Page(Component):
        citry = c
        template = "<c-capture><c-active-child /></c-capture>"

    Page().render().serialize()
    manifest = _manifest(captured[0])
    graph = manifest["graphs"][0]

    assert len(graph["componentInstances"]) == 2
    assert graph["componentInstances"][0]["parentRenderId"] is None
    assert graph["componentInstances"][0]["invocationId"] is None
    assert graph["slotRegions"] == []


def test_same_graph_render_hook_fragment_rejects_an_outer_fill_that_needs_projection():
    c = Citry()

    class Capture(Component):
        citry = c
        template = "<c-slot />"

        def on_render(self):
            result, error = yield
            if error is not None:
                return None
            assert result is not None
            str(result)
            return None

    class Page(Component):
        citry = c
        template = '<c-capture><button x-data="{ caller: true }">child</button></c-capture>'

    with pytest.raises(RuntimeError, match="cross-graph relation"):
        Page().render()


def test_simple_and_ignore_keep_the_server_only_output_free_of_graph_artifacts():
    c = Citry()

    class Page(Component):
        citry = c
        js = "$component(() => {})"
        template = "alpha<span>beta</span>"

    render = Page().render()
    for strategy in ("simple", "ignore"):
        html = render.serialize(deps_strategy=strategy)
        assert f"{COMMENT_PREFIX}:" not in html
        assert "data-citry-graph" not in html


def test_reusing_one_concrete_component_render_in_two_positions_fails_closed():
    c = Citry()

    class Child(Component):
        citry = c
        js = "$component(() => {})"
        template = "<span>child</span>"

    child = Child().render()

    class Page(Component):
        citry = c
        template = "{{ child }}{{ child }}"

        def template_data(self, kwargs, slots):
            return {"child": child}

    with pytest.raises(RuntimeError, match="same rendered component occurrence"):
        Page().render().serialize()


def test_realistic_manifest_stays_within_the_large_graph_regression_budget():
    c = Citry()

    class Item(Component):
        citry = c
        js = """
          $component(() => {});
        """
        template = "<button><c-slot /></button>"

    class Page(Component):
        citry = c

        class Events:
            def choose(self):
                return None

        template = """
          <ul>
            <c-for each="item in items">
              <li><c-item c-$c-props="item['props']" c-bind="item['handlers']">{{ item['label'] }}</c-item></li>
            </c-for>
          </ul>
        """

        def template_data(self, kwargs, slots):
            return {
                "items": [
                    {
                        "label": f"row-{index}",
                        "props": f"{{index: {index}}}",
                        "handlers": {"@click": "selected = true", "@c-click": "choose"},
                    }
                    for index in range(100)
                ]
            }

    html = Page().render().serialize()
    encoded = json.dumps(_manifest(html), separators=(",", ":"), sort_keys=True).encode()
    assert len(encoded) < 250_000


def test_manifest_artifact_does_not_impose_a_protocol_size_limit():
    graph = client_graph.build_graph(
        graph_id=0,
        component_classes=[client_graph.build_component_class("Page_1", "x" * 1_100_000)],
        component_instances=[
            client_graph.build_component_instance(
                instance_id=1,
                render_id="page_1",
                class_id="Page_1",
                invocation_id=None,
                parent_render_id=None,
                transparent=False,
            )
        ],
        source_locations=[],
        nested_components=[],
        component_execution_order_constraints=[],
        fills=[],
        slot_regions=[],
    )
    manifest = client_graph.build_manifest("production", [graph])
    artifact = OwnershipManifestArtifact(
        revision=manifest["revision"],
        manifest=manifest,
        captures=(),
        graph_indexes={},
        instance_ids={},
        transparent_instance_ids=frozenset(),
        region_ids=frozenset(),
        client_active_instances=frozenset(),
    )

    assert len(artifact.json().encode("utf8")) > 1_000_000
