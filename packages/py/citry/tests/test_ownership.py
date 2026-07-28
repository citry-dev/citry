"""A1 server ownership records, captured before rendering flattens them."""

from __future__ import annotations

import gc
import re

import pytest

from citry import Citry, CitryRender, Component, Extension, Slot
from citry.constness import const_value
from citry.ownership import (
    CitryDomEventClientBindingPayload,
    ComponentTagClientBindingKind,
    ComponentTagClientBindingSource,
    LogicalFillKind,
    QueueState,
    SourcePolicy,
)
from citry.util.html import SafeString


def _snapshot(render):
    graph = render.context.ownership
    assert graph is not None
    return graph.snapshot()


class TestComponentTagClientBindingOwnership:
    def test_typed_target_receives_only_kwargs_while_invocation_keeps_client_bindings(self):
        c = Citry()
        captured = []

        class Child(Component):
            citry = c

            class Kwargs:
                title: str

            template = """
              <button>{{ title }}</button>
            """

            def template_data(self, kwargs, slots):
                captured.append({key: const_value(value) for key, value in self.raw_kwargs.items()})
                return {"title": kwargs.title}

        class Page(Component):
            citry = c

            class Events:
                def save_it(self):
                    return None

            template = """
              <c-child
                title="ok"
                $c-props="{ count: localCount }"
                @click="select()"
                x-on:focus="focusIt()"
                @c-save="save_it"
              />
            """

        render = Page().render()
        snapshot = _snapshot(render)
        child_call = next(call for call in snapshot.component_invocations if call.authored_tag == "child")

        assert captured == [{"title": "ok"}]
        assert child_call.target_render_id is not None
        assert [client_binding.key for client_binding in child_call.client_bindings] == [
            "$c-props",
            "@click",
            "x-on:focus",
            "@c-save",
        ]
        assert [client_binding.kind for client_binding in child_call.client_bindings] == [
            ComponentTagClientBindingKind.PROPS,
            ComponentTagClientBindingKind.ALPINE_HANDLER,
            ComponentTagClientBindingKind.ALPINE_HANDLER,
            ComponentTagClientBindingKind.CITRY_HANDLER,
        ]
        assert all(
            client_binding.source == ComponentTagClientBindingSource.DIRECT
            for client_binding in child_call.client_bindings
        )
        citry_payload = child_call.client_bindings[-1].payload
        assert isinstance(citry_payload, CitryDomEventClientBindingPayload)
        assert (citry_payload.class_id, citry_payload.event, citry_payload.handler, citry_payload.args) == (
            Page.class_id,
            "save",
            "save_it",
            None,
        )
        locations = {location.id: location for location in snapshot.source_locations}
        snippets = [
            locations[client_binding.source_location_id].snippet for client_binding in child_call.client_bindings
        ]
        assert snippets == [
            '$c-props="{ count: localCount }"',
            '@click="select()"',
            'x-on:focus="focusIt()"',
            '@c-save="save_it"',
        ]

    def test_winning_contributions_keep_replacement_order_and_spread_location(self):
        c = Citry()

        class Child(Component):
            citry = c
            template = """
              <button>child</button>
            """

        class Page(Component):
            citry = c
            template = """
              <c-child
                @click="first"
                x-on:focus="focus"
                c-bind="replace"
                c-bind="remove"
                c-bind="add"
              />
            """

            def template_data(self, kwargs, slots):
                return {
                    "replace": {"@click": "second"},
                    "remove": {"@click": None},
                    "add": {"$c-props": "{ value: spreadValue }", "@click": "last"},
                }

        snapshot = _snapshot(Page().render())
        call = next(call for call in snapshot.component_invocations if call.authored_tag == "child")
        locations = {location.id: location for location in snapshot.source_locations}

        assert [client_binding.key for client_binding in call.client_bindings] == ["x-on:focus", "$c-props", "@click"]
        assert [client_binding.payload.expression for client_binding in call.client_bindings] == [
            "focus",
            "{ value: spreadValue }",
            "last",
        ]
        assert [client_binding.source for client_binding in call.client_bindings] == [
            ComponentTagClientBindingSource.DIRECT,
            ComponentTagClientBindingSource.SPREAD,
            ComponentTagClientBindingSource.SPREAD,
        ]
        assert [
            locations[client_binding.source_location_id].mapping_key for client_binding in call.client_bindings
        ] == [
            None,
            "$c-props",
            "@click",
        ]
        assert locations[call.client_bindings[1].source_location_id].snippet == 'c-bind="add"'

    @pytest.mark.parametrize(
        ("attribute", "data", "source"),
        [
            ('@c-click.prevent="save({value: `closed )`})"', {}, ComponentTagClientBindingSource.DIRECT),
            (
                'c-@c-click.prevent="binding"',
                {"binding": "save({value: `closed )`})"},
                ComponentTagClientBindingSource.SERVER_DYNAMIC,
            ),
            (
                'c-bind="bindings"',
                {"bindings": {"@c-click.prevent": "save({value: `closed )`})"}},
                ComponentTagClientBindingSource.SPREAD,
            ),
        ],
    )
    def test_every_citry_boundary_source_compiles_against_the_parent(self, attribute, data, source):
        c = Citry()

        class Child(Component):
            citry = c

            class Events:
                def child_only(self):
                    return None

            template = "<button>child</button>"

        class Page(Component):
            citry = c

            class Events:
                def save(self):
                    return None

            def template_data(self, kwargs, slots):
                return data

        Page.template = f"<c-child {attribute} />"
        snapshot = _snapshot(Page().render())
        client_binding = snapshot.component_invocations[0].client_bindings[0]
        payload = client_binding.payload

        assert isinstance(payload, CitryDomEventClientBindingPayload)
        assert client_binding.source == source
        assert payload.class_id == Page.class_id
        assert payload.handler == "save"
        assert payload.args == "{value: `closed )`}"
        assert payload.prevent is True

    def test_child_handler_cannot_satisfy_a_parent_authored_boundary_binding(self):
        c = Citry()

        class Child(Component):
            citry = c

            class Events:
                def child_only(self):
                    return None

            template = "child"

        class Page(Component):
            citry = c
            template = '<c-child @c-click="child_only" />'

        with pytest.raises(ValueError, match=r"not a declared handler of Page"):
            Page().render()

    @pytest.mark.parametrize(
        "expression",
        [
            '{value: "closed )"}',
            r'{value: "escaped \\" and )"}',
            "{value: `closed ) and ${nested(1)}`}",
            r"{value: /\)/.test(text)}",
            "{value: outer(inner(1), () => (2))}",
        ],
    )
    def test_component_boundary_handler_preserves_opaque_javascript_interior(self, expression):
        c = Citry()

        class Child(Component):
            citry = c
            template = "<button>child</button>"

        class Page(Component):
            citry = c

            class Events:
                def save(self):
                    return None

        Page.template = f"<c-child @c-click='save({expression})' />"
        snapshot = _snapshot(Page().render())
        payload = snapshot.component_invocations[0].client_bindings[0].payload

        assert isinstance(payload, CitryDomEventClientBindingPayload)
        assert payload.handler == "save"
        assert payload.args == expression

    def test_component_boundary_handler_rejects_trailing_binding_text(self):
        c = Citry()

        class Child(Component):
            citry = c
            template = "<button>child</button>"

        class Page(Component):
            citry = c
            template = '<c-child @c-click="save({ok: true}); selected = false" />'

            class Events:
                def save(self):
                    return None

        with pytest.raises(ValueError, match=r"must end at its final '\)' with no trailing text"):
            Page().render()

    def test_one_compiled_location_executed_in_loop_gets_fresh_records(self):
        c = Citry()

        class Child(Component):
            citry = c
            template = """
              <i>child</i>
            """

        class Page(Component):
            citry = c
            template = """
              <c-for each="item in items">
                <c-child c-$c-props="item" />
              </c-for>
            """

            def template_data(self, kwargs, slots):
                return {"items": ["{ n: 1 }", "{ n: 2 }"]}

        snapshot = _snapshot(Page().render())
        calls = [call for call in snapshot.component_invocations if call.authored_tag == "child"]
        locations = {location.id: location for location in snapshot.source_locations}

        assert len(calls) == 2
        assert calls[0].id != calls[1].id
        assert calls[0].source_location_id != calls[1].source_location_id
        assert locations[calls[0].source_location_id].span == locations[calls[1].source_location_id].span
        assert calls[0].client_bindings[0].payload.expression == "{ n: 1 }"
        assert calls[1].client_bindings[0].payload.expression == "{ n: 2 }"

    def test_source_spans_convert_utf8_bytes_to_exact_character_offsets(self):
        c = Citry()

        class Child(Component):
            citry = c
            template = "child"

        class Page(Component):
            citry = c
            template = "é🙂\n  <c-child $c-props=\"{ label: 'ž' }\" />"

        snapshot = _snapshot(Page().render())
        call = next(call for call in snapshot.component_invocations if call.authored_tag == "child")
        locations = {location.id: location for location in snapshot.source_locations}
        call_location = locations[call.source_location_id]
        client_binding_location = locations[call.client_bindings[0].source_location_id]

        assert call_location.snippet == "<c-child $c-props=\"{ label: 'ž' }\" />"
        assert client_binding_location.snippet == "$c-props=\"{ label: 'ž' }\""
        assert (call_location.line, call_location.column) == (2, 3)
        assert call_location.byte_span != call_location.span
        assert client_binding_location.byte_span != client_binding_location.span

    def test_dynamic_state_binding_remains_invalid_on_component_boundary(self):
        c = Citry()

        class Child(Component):
            citry = c
            template = "child"

        class Page(Component):
            citry = c
            template = '<c-child c-bind="attrs" />'

            def template_data(self, kwargs, slots):
                return {"attrs": {":c-count": "refresh"}}

        with pytest.raises(RuntimeError, match=r"State binding ':c-count'.*component boundary"):
            Page().render()


class TestDynamicTargetOwnership:
    def test_runtime_selector_forwards_one_invocation_and_client_bindings_to_actual_target(self):
        c = Citry()
        target_raw_kwargs = []

        class Card(Component):
            citry = c
            template = """
              <article><c-slot /></article>
            """

            def template_data(self, kwargs, slots):
                target_raw_kwargs.append(dict(self.raw_kwargs))
                return {}

        class Page(Component):
            citry = c
            template = """
              <c-component c-is="target" $c-props="{ chosen: true }">body</c-component>
            """

            def template_data(self, kwargs, slots):
                return {"target": "card"}

        snapshot = _snapshot(Page().render())
        invocation = next(call for call in snapshot.component_invocations if call.authored_tag == "component")
        target = next(instance for instance in snapshot.logical_instances if instance.class_id == Card.class_id)
        wrapper = next(
            instance for instance in snapshot.logical_instances if instance.class_name == "DynamicComponent"
        )

        assert target_raw_kwargs == [{}]
        assert invocation.target_render_id == target.render_id
        assert invocation.target_class_id == Card.class_id
        assert [client_binding.key for client_binding in invocation.client_bindings] == ["$c-props"]
        assert target.invocation_id == invocation.id
        assert wrapper.invocation_id is None
        assert wrapper.render_id in invocation.selector_render_ids
        assert any(
            edge.parent_render_id == invocation.source_render_id
            and edge.child_render_id == target.render_id
            and edge.invocation_id == invocation.id
            for edge in snapshot.init_ancestry
        )

    def test_failing_runtime_selector_retires_its_transparent_wrapper(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<c-component c-is="target" />'

            def template_data(self, kwargs, slots):
                return {"target": "missing"}

            def on_render(self):
                result, error = yield
                if error is not None:
                    return "recovered"
                return result

        render = Page().render()
        snapshot = _snapshot(render)
        selector = next(
            instance for instance in snapshot.logical_instances if instance.class_name == "DynamicComponent"
        )

        assert render.serialize(deps_strategy="ignore") == "recovered"
        assert selector.state.value == "retired"
        assert snapshot.component_invocations[0].state.value == "retired"
        assert snapshot.render_queue[0].state == QueueState.FAILED

    def test_c_element_keeps_handlers_on_plain_html_path(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = """
              <c-element c-is="tag" @click="local()">body</c-element>
            """

            def template_data(self, kwargs, slots):
                return {"tag": "button"}

        render = Page().render()
        snapshot = _snapshot(render)

        assert '@click="local()"' in render.serialize(deps_strategy="ignore")
        assert all(not call.client_bindings for call in snapshot.component_invocations)


class TestSlotOwnership:
    @pytest.mark.parametrize(
        ("fill_body", "expected_html"),
        [
            ("", ""),
            ("text only", "text only"),
            ("<b>one</b>", "<b>one</b>"),
            ("<i>one</i><i>two</i>", "<i>one</i><i>two</i>"),
        ],
        ids=["empty", "text-only", "single-root", "multi-root"],
    )
    def test_physical_region_capture_is_independent_of_fill_output_shape(self, fill_body, expected_html):
        c = Citry()

        class Child(Component):
            citry = c
            template = '<c-slot name="body" />'

        class Page(Component):
            citry = c
            template = f'<c-child><c-fill name="body">{fill_body}</c-fill></c-child>'

        render = Page().render()
        snapshot = _snapshot(render)
        fill = next(fill for fill in snapshot.logical_fills if fill.kind == LogicalFillKind.NAMED)
        regions = [region for region in snapshot.physical_regions if region.logical_fill_id == fill.id]

        html = re.sub(r' data-cid-[^=]+=""', "", render.serialize(deps_strategy="ignore"))
        assert html == expected_html
        assert len(regions) == 1
        assert regions[0].state.value == "captured"

    def test_supplied_fill_nested_fallback_and_component_call_keep_inverse_ownership(self):
        c = Citry()

        class Leaf(Component):
            citry = c
            template = """
              <strong>leaf</strong>
            """

        class Card(Component):
            citry = c
            template = """
              <c-slot name="body"><i>fallback</i></c-slot>
            """

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill name="body" fallback="fallback">
                  <b><c-leaf />{{ fallback }}</b>
                </c-fill>
              </c-card>
            """

        snapshot = _snapshot(Page().render())
        fills = {fill.id: fill for fill in snapshot.logical_fills}
        supplied = next(fill for fill in fills.values() if fill.kind == LogicalFillKind.NAMED)
        fallback = next(fill for fill in fills.values() if fill.kind == LogicalFillKind.FALLBACK)
        supplied_region = next(region for region in snapshot.physical_regions if region.logical_fill_id == supplied.id)
        fallback_region = next(region for region in snapshot.physical_regions if region.logical_fill_id == fallback.id)
        leaf_call = next(call for call in snapshot.component_invocations if call.authored_tag == "leaf")

        assert fallback_region.containing_region_id == supplied_region.id
        assert fallback_region.transition_from_render_id == supplied_region.lexical_owner_render_id
        assert fallback_region.lexical_owner_render_id == supplied_region.receiver_render_id
        assert leaf_call.physical_parent_region_id == supplied_region.id

    def test_mirrored_rootless_fill_has_one_logical_fill_and_two_region_requests(self):
        c = Citry()

        class Mirror(Component):
            citry = c
            template = """
              <c-slot name="body" /><c-slot name="body" />
            """

        class Page(Component):
            citry = c
            template = """
              <c-mirror><c-fill name="body" /></c-mirror>
            """

        render = Page().render()
        snapshot = _snapshot(render)
        fill = next(fill for fill in snapshot.logical_fills if fill.kind == LogicalFillKind.NAMED)
        regions = [region for region in snapshot.physical_regions if region.logical_fill_id == fill.id]

        assert render.serialize(deps_strategy="ignore").strip() == ""
        assert len(regions) == 2
        assert regions[0].id != regions[1].id

    def test_typed_default_fill_is_detached_and_gets_a_region(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="side" required />'

            class Slots:
                side: str = "DEFAULT"

        render = Card().render()
        snapshot = _snapshot(render)
        fill = next(fill for fill in snapshot.logical_fills if fill.kind == LogicalFillKind.TYPED_DEFAULT)
        regions = [region for region in snapshot.physical_regions if region.logical_fill_id == fill.id]

        assert render.serialize(deps_strategy="ignore") == "DEFAULT"
        assert fill.source_policy == SourcePolicy.TYPED_DEFAULT
        assert fill.lexical_owner_render_id is None
        assert fill.source_location_id is None
        assert len(regions) == 1

    def test_collected_template_slot_identity_cannot_alias_a_new_python_slot(self):
        observed = {}

        class ProbeIdentity(Extension):
            name = "probe_slot_identity"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ != "Page":
                    return
                assert isinstance(ctx.render, CitryRender)
                graph = ctx.render.context.ownership
                assert graph is not None
                template_keys = tuple(graph._template_fill_by_slot_object)
                old_ids = {key if isinstance(key, int) else id(key) for key in template_keys}
                del template_keys
                gc.collect()
                candidates = [Slot(f"python-{index}") for index in range(64)]
                collisions = [slot for slot in candidates if id(slot) in old_ids]
                selected = collisions[0] if collisions else candidates[0]
                nested = Outlet(slots={"default": selected}).render()
                assert nested.context.component is not None
                observed["collision_count"] = len(collisions)
                observed["outlet_id"] = nested.context.component.id

        c = Citry(extensions=[ProbeIdentity])

        class Outlet(Component):
            citry = c
            template = "<c-slot />"

        class Page(Component):
            citry = c
            template = "<c-slot>fallback</c-slot>"

        render = Page().render()
        snapshot = _snapshot(render)
        outlet_fill = next(fill for fill in snapshot.logical_fills if fill.receiver_render_id == observed["outlet_id"])

        assert observed["collision_count"] == 0
        assert outlet_fill.kind == LogicalFillKind.PYTHON
        assert outlet_fill.source_policy == SourcePolicy.PYTHON

    def test_reused_python_slot_creates_one_logical_supply_per_receiver(self):
        c = Citry()
        reusable = Slot(SafeString("<small>python</small>"), component_name="Outlet", slot_name="default")

        class Outlet(Component):
            citry = c
            template = """
              <div><c-slot /></div>
            """

        class Page(Component):
            citry = c
            template = """
              <section>{{ left }}{{ right }}</section>
            """

            def template_data(self, kwargs, slots):
                return {
                    "left": Outlet(slots={"default": reusable}),
                    "right": Outlet(slots={"default": reusable}),
                }

        snapshot = _snapshot(Page().render())
        python_fills = [fill for fill in snapshot.logical_fills if fill.source_policy == SourcePolicy.PYTHON]

        assert len(python_fills) == 2
        assert python_fills[0].id != python_fills[1].id
        assert all(fill.lexical_owner_render_id is None for fill in python_fills)
        assert all(fill.source_location_id is None for fill in python_fills)
        assert all(
            sum(region.logical_fill_id == fill.id for region in snapshot.physical_regions) == 1
            for fill in python_fills
        )

    def test_delayed_template_fill_resumes_its_graph_for_each_physical_call(self):
        c = Citry()
        captured = []

        class Inner(Component):
            citry = c
            template = "<span>inner</span>"

        class Capture(Component):
            citry = c
            template = "CAP"

            def template_data(self, kwargs, slots):
                captured.append(slots["body"])
                return {}

        class Page(Component):
            citry = c
            template = '<c-capture><c-fill name="body"><c-inner /></c-fill></c-capture>'

        render = Page().render()
        assert render.serialize(deps_strategy="ignore") == "CAP"
        assert _snapshot(render).physical_regions == ()

        assert str(captured[0]) == '<span data-cid-c3="">inner</span>'
        assert str(captured[0]) == '<span data-cid-c4="">inner</span>'

        snapshot = _snapshot(render)
        fill = next(fill for fill in snapshot.logical_fills if fill.kind == LogicalFillKind.NAMED)
        regions = [region for region in snapshot.physical_regions if region.logical_fill_id == fill.id]
        calls = [call for call in snapshot.component_invocations if call.authored_tag == "inner"]

        assert len(regions) == 2
        assert len(calls) == 2
        assert [call.physical_parent_region_id for call in calls] == [region.id for region in regions]

    def test_one_live_template_slot_gets_one_logical_attachment_per_receiver(self):
        c = Citry()
        captured = []

        class Capture(Component):
            citry = c
            template = "captured"

            def template_data(self, kwargs, slots):
                captured.append(slots["default"])
                return {}

        class Page(Component):
            citry = c
            template = "<c-capture><span>fill</span></c-capture>"

        render = Page().render()
        graph = render.context.ownership
        assert graph is not None
        slot = captured[0]
        original_receiver = next(
            fill.receiver_render_id for fill in graph.snapshot().logical_fills if fill.kind == LogicalFillKind.IMPLICIT
        )

        class Receiver:
            class_id = "Receiver_test"

            def __init__(self, render_id):
                self.id = render_id
                self.raw_slots = {"default": slot}

        first = Receiver("receiver-1")
        second = Receiver("receiver-2")
        graph.bind_supplied_slots(first)  # type: ignore[arg-type]
        graph.bind_supplied_slots(second)  # type: ignore[arg-type]

        snapshot = graph.snapshot()
        supplied = [fill for fill in snapshot.logical_fills if fill.kind == LogicalFillKind.IMPLICIT]
        by_receiver = {fill.receiver_render_id: fill for fill in supplied}
        source_invocations = {fill.source_invocation_id for fill in supplied}

        assert set(by_receiver) == {original_receiver, "receiver-1", "receiver-2"}
        assert len({fill.id for fill in supplied}) == 3
        assert len(source_invocations) == 1
        assert None not in source_invocations

    def test_template_fill_reused_in_later_render_keeps_graph_local_ids_isolated(self):
        c = Citry()
        captured = []

        class Inner(Component):
            citry = c
            template = "<i>inner</i>"

        class Capture(Component):
            citry = c
            template = "CAP"

            def template_data(self, kwargs, slots):
                captured.append(slots["default"])
                return {}

        class Page(Component):
            citry = c
            template = "<c-capture><c-inner /></c-capture>"

        class Outlet(Component):
            citry = c
            template = "<section><c-slot /></section>"

        first = Page().render()
        second = Outlet(slots={"default": captured[0]}).render()

        assert first.serialize(deps_strategy="ignore") == "CAP"
        assert (
            second.serialize(deps_strategy="ignore") == '<section data-cid-c3=""><i data-cid-c4="">inner</i></section>'
        )

        first_snapshot = _snapshot(first)
        second_snapshot = _snapshot(second)
        inner_call = next(call for call in first_snapshot.component_invocations if call.authored_tag == "inner")
        detached_fill = next(
            fill for fill in second_snapshot.logical_fills if fill.source_policy == SourcePolicy.PYTHON
        )
        detached_region = next(
            region for region in second_snapshot.physical_regions if region.logical_fill_id == detached_fill.id
        )

        assert inner_call.target_render_id is not None
        assert inner_call.physical_parent_region_id is None
        assert detached_region.result_owner_render_id is None
        assert all(call.authored_tag != "inner" for call in second_snapshot.component_invocations)


class TestDeferredOwnership:
    def test_queue_records_bind_and_settle_in_capture_order(self):
        c = Citry()

        class Leaf(Component):
            citry = c
            template = """
              done
            """

        class Branch(Component):
            citry = c
            template = """
              <c-leaf />
            """

        class Page(Component):
            citry = c
            template = """
              <c-branch />
            """

        snapshot = _snapshot(Page().render())

        assert [record.state for record in snapshot.render_queue] == [QueueState.SETTLED, QueueState.SETTLED]
        assert all(record.target_render_id is not None for record in snapshot.render_queue)
        assert [record.enqueued_order for record in snapshot.render_queue] == sorted(
            record.enqueued_order for record in snapshot.render_queue
        )

    @pytest.mark.parametrize("generator_hook", [False, True], ids=["direct", "generator-before"])
    def test_initial_on_render_side_effect_is_retired_when_not_selected(self, generator_hook):
        c = Citry()

        class Other(Component):
            citry = c
            template = "other"

        if generator_hook:

            class Page(Component):
                citry = c
                template = "template"

                def on_render(self):
                    Other().render()
                    yield
        else:

            class Page(Component):
                citry = c
                template = "template"

                def on_render(self):
                    Other().render()
                    return "replacement"

        render = Page().render()
        snapshot = _snapshot(render)
        states = {instance.class_name: instance.state.value for instance in snapshot.logical_instances}

        expected = "template" if generator_hook else "replacement"
        assert render.serialize(deps_strategy="ignore") == expected
        assert states == {"Page": "active", "Other": "retired"}

    def test_initial_on_render_created_result_stays_active_when_selected(self):
        c = Citry()

        class Other(Component):
            citry = c
            template = "other"

        class Page(Component):
            citry = c
            template = "template"

            def on_render(self):
                return Other().render()

        render = Page().render()
        snapshot = _snapshot(render)
        states = {instance.class_name: instance.state.value for instance in snapshot.logical_instances}

        assert render.serialize(deps_strategy="ignore") == "other"
        assert states == {"Page": "active", "Other": "active"}

    @pytest.mark.parametrize("select_side_effect", [False, True], ids=["discarded", "selected"])
    def test_on_render_after_phase_reconciles_side_effect_reachability(self, select_side_effect):
        c = Citry()

        class Other(Component):
            citry = c
            template = "other"

        class Page(Component):
            citry = c
            template = "template"

            def on_render(self):
                yield
                other = Other().render()
                return other if select_side_effect else "replacement"

        render = Page().render()
        snapshot = _snapshot(render)
        states = {instance.class_name: instance.state.value for instance in snapshot.logical_instances}

        expected = "other" if select_side_effect else "replacement"
        assert render.serialize(deps_strategy="ignore") == expected
        assert states == {
            "Page": "active",
            "Other": "active" if select_side_effect else "retired",
        }

    def test_swallowed_child_failure_marks_the_failed_invocation(self):
        c = Citry()

        class Boom(Component):
            citry = c
            template = """
              never
            """

            def template_data(self, kwargs, slots):
                raise ValueError("boom")

        class Guard(Component):
            citry = c
            template = """
              <c-boom />
            """

            def on_render(self):
                result, error = yield
                if error is not None:
                    return "recovered"
                return result

        class Page(Component):
            citry = c
            template = """
              <c-guard />
            """

        render = Page().render()
        snapshot = _snapshot(render)
        invocations = {call.id: call for call in snapshot.component_invocations}
        failed = [record for record in snapshot.render_queue if record.state == QueueState.FAILED]

        assert render.serialize(deps_strategy="ignore").strip() == "recovered"
        assert len(failed) == 1
        assert invocations[failed[0].invocation_id].authored_tag == "boom"

    def test_generator_replacement_retires_the_settled_output_graph(self):
        c = Citry()

        class Leaf(Component):
            citry = c
            template = "<b>leaf</b>"

        class Child(Component):
            citry = c
            template = "<c-slot /><c-leaf />"

        class Page(Component):
            citry = c
            template = "<c-child>fill</c-child>"

            def on_render(self):
                yield
                return "replacement"

        render = Page().render()
        snapshot = _snapshot(render)

        assert render.serialize(deps_strategy="ignore") == "replacement"
        assert {record.state.value for record in snapshot.render_queue} == {"retired"}
        assert [instance.state.value for instance in snapshot.logical_instances] == [
            "active",
            "retired",
            "retired",
        ]
        assert {fill.state.value for fill in snapshot.logical_fills} == {"retired"}
        assert {region.state.value for region in snapshot.physical_regions} == {"retired"}

    def test_generator_returning_settled_result_preserves_its_regions(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = "<c-slot />"

            def on_render(self):
                result, error = yield
                assert error is None
                return result

        render = Page(slots={"default": "kept"}).render()
        snapshot = _snapshot(render)

        assert render.serialize(deps_strategy="ignore") == "kept"
        assert {fill.state.value for fill in snapshot.logical_fills} == {"active"}
        assert {region.state.value for region in snapshot.physical_regions} == {"captured"}

    def test_extension_replacement_retires_the_settled_output_graph(self):
        class ReplacePage(Extension):
            name = "replace_page"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Page":
                    return "replacement"
                return None

        c = Citry(extensions=[ReplacePage])

        class Child(Component):
            citry = c
            template = "child"

        class Page(Component):
            citry = c
            template = "<c-child />"

        render = Page().render()
        snapshot = _snapshot(render)

        assert render.serialize(deps_strategy="ignore") == "replacement"
        assert [record.state.value for record in snapshot.render_queue] == ["retired"]
        assert [instance.state.value for instance in snapshot.logical_instances] == ["active", "retired"]

    def test_replacement_reusing_retired_slot_creates_active_fill_occurrence(self):
        c = Citry()
        saved = []

        class Child(Component):
            citry = c
            template = "<c-slot />"

            def template_data(self, kwargs, slots):
                saved.append(slots["default"])
                return {}

        class Page(Component):
            citry = c
            template = "<c-child>kept</c-child>"

            def on_render(self):
                yield
                return saved[0]

        render = Page().render()
        snapshot = _snapshot(render)
        active_fills = [fill for fill in snapshot.logical_fills if fill.state.value == "active"]
        active_regions = [region for region in snapshot.physical_regions if region.state.value == "captured"]

        assert render.serialize(deps_strategy="ignore") == "kept"
        assert len(active_fills) == 1
        assert len(active_regions) == 1
        assert active_regions[0].logical_fill_id == active_fills[0].id
        assert active_fills[0].lexical_owner_render_id == render.context.component.id
        active_instance_ids = {
            instance.render_id for instance in snapshot.logical_instances if instance.state.value == "active"
        }
        assert active_fills[0].receiver_render_id in active_instance_ids
        assert active_regions[0].receiver_render_id in active_instance_ids

    def test_extension_wrapper_preserves_reachable_old_output_records(self):
        class WrapPage(Extension):
            name = "wrap_page"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Page":
                    return CitryRender(parts=["[", ctx.render, "]"], context=ctx.render.context)
                return None

        c = Citry(extensions=[WrapPage])

        class Child(Component):
            citry = c
            template = "<b>child</b>"

        class Page(Component):
            citry = c
            template = "<c-child />"

        render = Page().render()
        snapshot = _snapshot(render)

        assert "[" in render.serialize(deps_strategy="ignore")
        assert "]" in render.serialize(deps_strategy="ignore")
        assert [record.state for record in snapshot.render_queue] == [QueueState.SETTLED]
        assert all(instance.state.value == "active" for instance in snapshot.logical_instances)

    def test_foreign_render_replacement_keeps_replaced_root_graph_authority(self):
        replacement = []

        class ReplacePage(Extension):
            name = "replace_page"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Page":
                    return replacement[0]
                return None

        c = Citry(extensions=[ReplacePage])

        class Other(Component):
            citry = c
            template = "<em>other</em>"

        class Child(Component):
            citry = c
            template = "child"

        class Page(Component):
            citry = c
            template = "<c-child />"

        foreign = Other().render()
        replacement.append(foreign)
        render = Page().render()
        snapshot = _snapshot(render)

        assert type(render.context.component).__name__ == "Page"
        assert render.context.ownership is not foreign.context.ownership
        assert "other" in render.serialize(deps_strategy="ignore")
        assert [record.state.value for record in snapshot.render_queue] == ["retired"]

    def test_extension_side_effect_render_is_retired_when_not_selected(self):
        side_effects = []

        class ReplacePage(Extension):
            name = "replace_page"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Page":
                    side_effects.append(Other().render())
                    return "replacement"
                return None

        c = Citry(extensions=[ReplacePage])

        class Other(Component):
            citry = c
            template = "other"

        class Child(Component):
            citry = c
            template = "child"

        class Page(Component):
            citry = c
            template = "<c-child />"

        render = Page().render()
        snapshot = _snapshot(render)

        assert render.serialize(deps_strategy="ignore") == "replacement"
        assert side_effects[0].context.ownership is render.context.ownership
        assert [instance.state.value for instance in snapshot.logical_instances] == [
            "active",
            "retired",
            "retired",
        ]

    def test_extension_side_effect_render_stays_active_when_selected(self):
        class ReplacePage(Extension):
            name = "replace_page"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Page":
                    return Other().render()
                return None

        c = Citry(extensions=[ReplacePage])

        class Other(Component):
            citry = c
            template = "other"

        class Child(Component):
            citry = c
            template = "child"

        class Page(Component):
            citry = c
            template = "<c-child />"

        render = Page().render()
        snapshot = _snapshot(render)
        states = {instance.class_name: instance.state.value for instance in snapshot.logical_instances}

        assert render.serialize(deps_strategy="ignore") == "other"
        assert states == {"Page": "active", "Child": "retired", "Other": "active"}

    def test_selected_descendant_preserves_its_hook_created_logical_ancestor(self):
        class SelectLeaf(Extension):
            name = "select_leaf"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Page":
                    side = Side().render()
                    return next(part for part in side.parts if isinstance(part, CitryRender))
                return None

        c = Citry(extensions=[SelectLeaf])

        class Leaf(Component):
            citry = c
            template = "leaf"

        class Side(Component):
            citry = c
            template = "<c-leaf />"

        class Page(Component):
            citry = c
            template = "page"

        render = Page().render()
        snapshot = _snapshot(render)
        states = {instance.class_name: instance.state.value for instance in snapshot.logical_instances}
        leaf = next(instance for instance in snapshot.logical_instances if instance.class_name == "Leaf")
        side = next(instance for instance in snapshot.logical_instances if instance.class_name == "Side")

        assert render.serialize(deps_strategy="ignore") == "leaf"
        assert states == {"Page": "active", "Side": "active", "Leaf": "active"}
        assert leaf.logical_parent_render_id == side.render_id
        assert all(edge.state.value == "active" for edge in snapshot.init_ancestry)

    def test_selecting_one_nested_region_retires_its_same_owner_sibling(self):
        class SelectFirstLeaf(Extension):
            name = "select_first_leaf"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ != "Page":
                    return None
                side = Side().render()
                pending = [side]
                while pending:
                    current = pending.pop(0)
                    if type(current.context.component).__name__ == "Leaf":
                        return current
                    pending.extend(part for part in current.parts if isinstance(part, CitryRender))
                raise AssertionError("Leaf render not found")

        c = Citry(extensions=[SelectFirstLeaf])

        class Leaf(Component):
            citry = c
            template = "{{ label }}"

        class Outlet(Component):
            citry = c
            template = "<c-slot />"

        class Side(Component):
            citry = c
            template = '<c-outlet><c-leaf label="a" /></c-outlet><c-outlet><c-leaf label="b" /></c-outlet>'

        class Page(Component):
            citry = c
            template = "page"

        render = Page().render()
        snapshot = _snapshot(render)
        outlets = [instance for instance in snapshot.logical_instances if instance.class_name == "Outlet"]
        leaves = [instance for instance in snapshot.logical_instances if instance.class_name == "Leaf"]

        assert render.serialize(deps_strategy="ignore") == "a"
        assert sorted(instance.state.value for instance in outlets) == ["active", "retired"]
        assert sorted(instance.state.value for instance in leaves) == ["active", "retired"]
        assert sorted(region.state.value for region in snapshot.physical_regions) == ["captured", "retired"]

    def test_selecting_one_rootless_text_region_retires_its_same_owner_sibling(self):
        class SelectFirstText(Extension):
            name = "select_first_text"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ != "Page":
                    return None
                side = Side(slots={"a": "A", "b": "B"}).render()
                return CitryRender(parts=[side.parts[0]], context=side.context)

        c = Citry(extensions=[SelectFirstText])

        class Side(Component):
            citry = c
            template = '<c-slot name="a" /><c-slot name="b" />'

        class Page(Component):
            citry = c
            template = "page"

        render = Page().render()
        snapshot = _snapshot(render)

        assert render.serialize(deps_strategy="ignore") == "A"
        supplied = [fill for fill in snapshot.logical_fills if fill.kind == LogicalFillKind.PYTHON]
        assert sorted(fill.state.value for fill in supplied) == ["active", "retired"]
        assert sorted(region.state.value for region in snapshot.physical_regions) == ["captured", "retired"]

    def test_error_unwind_retires_deferred_siblings_that_never_render(self):
        c = Citry()

        class Boom(Component):
            citry = c
            template = "boom"

            def template_data(self, kwargs, slots):
                raise ValueError("boom")

        class Never(Component):
            citry = c
            template = "never"

        class Page(Component):
            citry = c
            template = "<c-boom /><c-never />"

            def on_render(self):
                result, error = yield
                if error is not None:
                    return "recovered"
                return result

        render = Page().render()
        snapshot = _snapshot(render)
        queues = {
            next(
                call.authored_tag for call in snapshot.component_invocations if call.id == record.invocation_id
            ): record
            for record in snapshot.render_queue
        }

        assert render.serialize(deps_strategy="ignore") == "recovered"
        assert queues["boom"].state == QueueState.FAILED
        assert queues["never"].state.value == "retired"
        assert queues["never"].target_render_id is None

    def test_slot_rendered_replacement_retires_orphaned_fill_work(self):
        class ReplaceSlot(Extension):
            name = "replace_slot"

            def on_slot_rendered(self, ctx):
                return "replacement"

        c = Citry(extensions=[ReplaceSlot])

        class Leaf(Component):
            citry = c
            template = "leaf"

        class Child(Component):
            citry = c
            template = "<c-slot />"

        class Page(Component):
            citry = c
            template = "<c-child><c-leaf /></c-child>"

        render = Page().render()
        snapshot = _snapshot(render)
        leaf_call = next(call for call in snapshot.component_invocations if call.authored_tag == "leaf")
        leaf_queue = next(record for record in snapshot.render_queue if record.invocation_id == leaf_call.id)

        assert render.serialize(deps_strategy="ignore") == "replacement"
        assert leaf_call.state.value == "retired"
        assert leaf_queue.state == QueueState.RETIRED
        assert {region.state.value for region in snapshot.physical_regions} == {"captured"}

    def test_slot_rendered_rebinds_region_to_selected_active_output(self):
        class ReplaceSlot(Extension):
            name = "replace_slot_with_render"

            def on_slot_rendered(self, ctx):
                return Other().render()

        c = Citry(extensions=[ReplaceSlot])

        class Other(Component):
            citry = c
            template = "other"

        class Child(Component):
            citry = c
            template = "<c-slot />"

        class Page(Component):
            citry = c
            template = "<c-child>original</c-child>"

        render = Page().render()
        snapshot = _snapshot(render)
        other = next(instance for instance in snapshot.logical_instances if instance.class_name == "Other")
        region = next(region for region in snapshot.physical_regions if region.state.value == "captured")

        assert render.serialize(deps_strategy="ignore") == "other"
        assert other.state.value == "active"
        assert region.result_owner_render_id == other.render_id

    @pytest.mark.parametrize("replace_output", [False, True], ids=["keep", "replace"])
    def test_slot_rendered_rebind_handles_nested_fallback_regions(self, replace_output):
        class MapSlot(Extension):
            name = "map_nested_fallback"

            def on_slot_rendered(self, ctx):
                return "replacement" if replace_output else None

        c = Citry(extensions=[MapSlot])

        class Child(Component):
            citry = c
            template = "<c-slot>fallback</c-slot>"

        class Page(Component):
            citry = c
            template = '<c-child><c-fill name="default" fallback="fallback">{{ fallback }}</c-fill></c-child>'

        render = Page().render()
        snapshot = _snapshot(render)

        assert render.serialize(deps_strategy="ignore") == ("replacement" if replace_output else "fallback")
        expected_states = ["captured", "retired"] if replace_output else ["captured", "captured"]
        assert sorted(region.state.value for region in snapshot.physical_regions) == expected_states

    @pytest.mark.parametrize("select_repeat", [False, True], ids=["discard-repeat", "select-repeat"])
    def test_slot_rendered_repeat_call_is_nested_under_known_outlet(self, select_repeat):
        class RepeatSlot(Extension):
            name = "repeat_slot"

            def on_slot_rendered(self, ctx):
                repeated = ctx.slot()
                return repeated if select_repeat else None

        c = Citry(extensions=[RepeatSlot])

        class Page(Component):
            citry = c
            template = "<c-slot>fallback</c-slot>"

        render = Page().render()
        snapshot = _snapshot(render)
        outer, repeated = snapshot.physical_regions

        assert render.serialize(deps_strategy="ignore") == "fallback"
        assert outer.state.value == "captured"
        assert repeated.containing_region_id == outer.id
        assert repeated.state.value == ("captured" if select_repeat else "retired")

    def test_component_error_recovery_retires_partial_template_output(self):
        class BreakSlot(Extension):
            name = "break_slot"

            def on_slot_rendered(self, ctx):
                raise ValueError("slot failed")

        c = Citry(extensions=[BreakSlot])

        class Leaf(Component):
            citry = c
            template = "leaf"

        class Page(Component):
            citry = c
            template = "<c-slot />"

            def on_render(self):
                result, error = yield
                if error is not None:
                    return "recovered"
                return result

        render = Page(slots={"default": Slot(Leaf())}).render()
        snapshot = _snapshot(render)

        assert render.serialize(deps_strategy="ignore") == "recovered"
        assert all(
            instance.class_name != "Leaf" or instance.state.value == "retired"
            for instance in snapshot.logical_instances
        )
        assert {region.state.value for region in snapshot.physical_regions} == {"retired"}

    @pytest.mark.parametrize("generator_hook", [False, True], ids=["direct", "generator-prime"])
    def test_initial_on_render_exception_retires_hook_side_effects(self, generator_hook):
        c = Citry()

        class Other(Component):
            citry = c
            template = "other"

        if generator_hook:

            class Child(Component):
                citry = c
                template = "child"

                def on_render(self):
                    Other().render()
                    raise ValueError("hook failed")
                    yield

        else:

            class Child(Component):
                citry = c
                template = "child"

                def on_render(self):
                    Other().render()
                    raise ValueError("hook failed")

        class Page(Component):
            citry = c
            template = "<c-child />"

            def on_render(self):
                result, error = yield
                if error is not None:
                    return "recovered"
                return result

        render = Page().render()
        snapshot = _snapshot(render)
        other = next(instance for instance in snapshot.logical_instances if instance.class_name == "Other")

        assert render.serialize(deps_strategy="ignore") == "recovered"
        assert other.state.value == "retired"

    def test_slot_rendered_exception_retires_hook_side_effects(self):
        class BreakSlot(Extension):
            name = "break_slot_side_effect"

            def on_slot_rendered(self, ctx):
                Other().render()
                raise ValueError("slot failed")

        c = Citry(extensions=[BreakSlot])

        class Other(Component):
            citry = c
            template = "other"

        class Child(Component):
            citry = c
            template = "<c-slot />"

        class Page(Component):
            citry = c
            template = "<c-child>fill</c-child>"

            def on_render(self):
                result, error = yield
                if error is not None:
                    return "recovered"
                return result

        render = Page().render()
        snapshot = _snapshot(render)
        other = next(instance for instance in snapshot.logical_instances if instance.class_name == "Other")

        assert render.serialize(deps_strategy="ignore") == "recovered"
        assert other.state.value == "retired"
