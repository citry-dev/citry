"""Phase 2 tests for detached render export and replay."""

from __future__ import annotations

import base64
import gc
import json
import re
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from typing import TYPE_CHECKING

import pytest

from citry import Citry, CitryContext, CitryRender, Component, Extension
from citry.ext.cache.artifact import _decode_artifact, _encode_artifact, _thaw_json
from citry.ext.cache.errors import CacheArtifactError
from citry.ext.cache.extension import CacheExtension
from citry.ext.cache.replay import _export_component_artifact, _replay_component_artifact
from citry.ext.dependencies.extension import EXTRA_KEY as DEPENDENCIES_EXTRA_KEY
from citry.ext.dependencies.scripts import gen_cache_key
from citry.ext.dependencies.types import Script
from citry.ext.events.emission import EXTRA_KEY as EVENTS_EXTRA_KEY
from citry.ext.events.tokens import verify_state_token
from citry.extension import RenderCacheWrite, StagedRenderCacheContribution
from citry.ownership import (
    AlpineHandlerClientBindingPayload,
    CitryDomEventClientBindingPayload,
    CitryPollClientBindingPayload,
    LogicalFillKind,
    OwnershipGraph,
    OwnershipState,
    PropsClientBindingPayload,
    RegionState,
)

if TYPE_CHECKING:
    from citry.citry_element import CitryElement


_ID_MARKER = re.compile(r"data-cid-[a-z0-9_-]+")
_SIGNING_KEY = "phase-2-test-secret"


def _boundary(element: CitryElement):
    comp_cls = element.comp_cls
    component = comp_cls._create_instance(kwargs=element.kwargs, slots=element.slots)
    component._component_tag_client_bindings = element.component_tag_client_bindings
    component._ownership_invocation_id = element.ownership_invocation_id
    graph = OwnershipGraph()
    graph.bind_instance(component, element)
    graph.bind_supplied_slots(component)
    component._ownership_graph = graph
    context = CitryContext(
        component=component,
        ownership=graph,
        sandboxed=component.citry.settings.sandbox_expressions,
    )
    return component, context, graph


def _normalize_ids(html: str) -> str:
    return _ID_MARKER.sub("data-cid-ID", html)


def _enable_test_component_cache(monkeypatch, app: Citry, component_class: type[Component], key: str):
    extension = app.extensions.get_extension("cache")
    assert isinstance(extension, CacheExtension)

    def lookup(component, _context):
        if type(component) is component_class:
            return extension._lookup_physical_key(key, ttl=None, max_entry_bytes=None)
        return None

    monkeypatch.setattr(extension, "_lookup_component", lookup)
    return extension


class TestCoreArtifactReplay:
    def test_component_artifact_reuses_boundary_and_mints_descendant_ids(self):
        app = Citry()

        class Card(Component):
            citry = app
            template = """
            <p>cached card</p>
            """

        class Page(Component):
            citry = app
            template = """
            <main><c-card /></main>
            """

        original = Page().render()
        artifact = _decode_artifact(_encode_artifact(_export_component_artifact(original)))
        original_ids = {
            record.render_id
            for record in original.context.ownership.snapshot().logical_instances
            if record.state == OwnershipState.ACTIVE
        }
        for render_id in original_ids:
            assert render_id not in _encode_artifact(artifact)

        boundary, context, graph = _boundary(Page())
        replayed = _replay_component_artifact(artifact, boundary=boundary, context=context)
        replayed_ids = {
            record.render_id for record in graph.snapshot().logical_instances if record.state == OwnershipState.ACTIVE
        }
        assert replayed.frame.render_id == boundary.id
        assert boundary.id in replayed_ids
        assert len(replayed_ids) == 2
        assert replayed_ids.isdisjoint(original_ids)
        assert _normalize_ids(replayed.serialize(deps_strategy="ignore")) == _normalize_ids(
            original.serialize(deps_strategy="ignore")
        )

        inner = next(part for part in replayed.parts if isinstance(part, CitryRender))
        assert inner.context.component is None
        assert inner.frame.class_id == Card.class_id

    def test_two_replays_of_one_artifact_get_disjoint_descendant_ids(self):
        app = Citry()

        class Child(Component):
            citry = app
            template = """
            <span>child</span>
            """

        class Parent(Component):
            citry = app
            template = """
            <div><c-child /></div>
            """

        artifact = _export_component_artifact(Parent().render())

        def replay_once():
            boundary, context, graph = _boundary(Parent())
            replayed = _replay_component_artifact(artifact, boundary=boundary, context=context)
            ids = {
                record.render_id
                for record in graph.snapshot().logical_instances
                if record.state == OwnershipState.ACTIVE
            }
            return replayed, ids

        first, first_ids = replay_once()
        second, second_ids = replay_once()
        assert first_ids.isdisjoint(second_ids)
        assert _normalize_ids(first.serialize(deps_strategy="ignore")) == _normalize_ids(
            second.serialize(deps_strategy="ignore")
        )

    def test_component_tag_client_bindings_round_trip_through_replay(self):
        app = Citry()

        class Child(Component):
            citry = app
            js = """
              $component(() => {});
            """
            template = """
            <span>child</span>
            """

        class Cached(Component):
            citry = app

            class Events:
                def save(self):
                    return None

                def refresh(self):
                    return None

            template = """
            <div>
              <c-child
                #c-key="cache_key"
                $c-props="{ count: localCount }"
                @click="select()"
                @c-save.prevent.stop.once.debounce.50ms="save({value: 1})"
                @c-poll.5s="refresh"
              />
            </div>
            """

            def template_data(self, kwargs, slots):
                return {"cache_key": kwargs.get("cache_key", "")}

        encoded = _encode_artifact(_export_component_artifact(Cached(cache_key="</script>π").render()))
        wire = json.loads(encoded)
        assert wire["artifact_version"] == 1
        assert wire["ownership"]["invocations"][0]["morph_key"] == "</script>π"
        assert wire["ownership"]["invocations"][0]["morph_mode"] is None

        missing = json.loads(encoded)
        missing["ownership"]["invocations"][0].pop("morph_mode")
        missing_artifact = _decode_artifact(json.dumps(missing))
        missing_boundary, missing_context, _missing_graph = _boundary(Cached())
        with pytest.raises(CacheArtifactError, match="invalid field set"):
            _replay_component_artifact(
                missing_artifact,
                boundary=missing_boundary,
                context=missing_context,
            )

        wrong_type = json.loads(encoded)
        wrong_type["ownership"]["invocations"][0]["morph_mode"] = False
        wrong_artifact = _decode_artifact(json.dumps(wrong_type))
        wrong_boundary, wrong_context, _wrong_graph = _boundary(Cached())
        with pytest.raises(CacheArtifactError, match="morph_mode must be an exact string"):
            _replay_component_artifact(
                wrong_artifact,
                boundary=wrong_boundary,
                context=wrong_context,
            )

        unknown = json.loads(encoded)
        unknown["ownership"]["invocations"][0]["morph_mode"] = "replace"
        unknown_artifact = _decode_artifact(json.dumps(unknown))
        unknown_boundary, unknown_context, _unknown_graph = _boundary(Cached())
        with pytest.raises(CacheArtifactError, match="morph_mode contains unknown value"):
            _replay_component_artifact(
                unknown_artifact,
                boundary=unknown_boundary,
                context=unknown_context,
            )

        wire["ownership"]["invocations"][0]["morph_mode"] = "ignore"
        artifact = _decode_artifact(json.dumps(wire))
        boundary, context, graph = _boundary(Cached())
        _replay_component_artifact(artifact, boundary=boundary, context=context)
        invocation = next(
            record
            for record in graph.snapshot().component_invocations
            if record.authored_tag == "child" and record.state == OwnershipState.ACTIVE
        )
        assert invocation.morph_key == "</script>π"
        assert invocation.morph_mode == "ignore"
        props, alpine, event, poll = (client_binding.payload for client_binding in invocation.client_bindings)

        assert isinstance(props, PropsClientBindingPayload)
        assert props.expression == "{ count: localCount }"
        assert isinstance(alpine, AlpineHandlerClientBindingPayload)
        assert alpine.expression == "select()"
        assert isinstance(event, CitryDomEventClientBindingPayload)
        assert (
            event.class_id,
            event.event,
            event.handler,
            event.args,
            event.prevent,
            event.stop,
            event.once,
            event.debounce,
        ) == (Cached.class_id, "save", "save", "{value: 1}", True, True, True, 50)
        assert isinstance(poll, CitryPollClientBindingPayload)
        assert (poll.class_id, poll.handler, poll.args, poll.interval) == (
            Cached.class_id,
            "refresh",
            None,
            5000,
        )

    def test_replay_rejects_props_when_current_target_lost_its_registration(self, monkeypatch):
        app = Citry()

        class Child(Component):
            citry = app
            js = """
              $component(() => {});
            """
            template = """
              child
            """

        class Cached(Component):
            citry = app
            template = """
              <c-child $c-props="{ value: 1 }" />
            """

        artifact = _export_component_artifact(Cached().render())
        Child.js = "console.log('registration removed');"
        Child.reset_files()
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()

        def unexpected_stage(*args, **kwargs):
            pytest.fail("invalid client props reached render-cache extension staging")

        monkeypatch.setattr(app.extensions, "_stage_render_cache", unexpected_stage)
        with pytest.raises(
            CacheArtifactError,
            match=r"\$c-props.*target component 'Child'.*no \$component\(\.\.\.\) registration",
        ):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert graph.snapshot() == before

    def test_concurrent_replays_do_not_mutate_the_shared_artifact(self):
        app = Citry()

        class Leaf(Component):
            citry = app
            template = """
            <i>leaf</i>
            """

        class Root(Component):
            citry = app
            template = """
            <section><c-leaf /></section>
            """

        artifact = _decode_artifact(_encode_artifact(_export_component_artifact(Root().render())))

        def replay_once(_index):
            boundary, context, graph = _boundary(Root())
            replayed = _replay_component_artifact(artifact, boundary=boundary, context=context)
            return replayed.serialize(deps_strategy="ignore"), {
                record.render_id
                for record in graph.snapshot().logical_instances
                if record.state == OwnershipState.ACTIVE
            }

        with ThreadPoolExecutor(max_workers=8) as executor:
            outcomes = list(executor.map(replay_once, range(32)))
        all_ids = [render_id for _, ids in outcomes for render_id in ids]
        assert len(all_ids) == len(set(all_ids))
        assert len({_normalize_ids(html) for html, _ in outcomes}) == 1

    def test_missing_descendant_class_rejects_before_graph_mutation(self):
        app = Citry()

        class Child(Component):
            citry = app
            template = """
            <span>child</span>
            """

        class Parent(Component):
            citry = app
            template = """
            <div><c-child /></div>
            """

        artifact = _export_component_artifact(Parent().render())
        app.unregister(Child)
        boundary, context, graph = _boundary(Parent())
        before = graph.snapshot()
        with pytest.raises(CacheArtifactError, match="registered component"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)
        assert graph.snapshot() == before

    def test_archived_class_name_mismatch_rejects_before_graph_mutation(self):
        app = Citry()

        class Cached(Component):
            citry = app
            template = """
            <p>cached</p>
            """

        wire = json.loads(_encode_artifact(_export_component_artifact(Cached().render())))
        wire["ownership"]["instances"][0]["class_name"] = "RetiredCached"
        artifact = _decode_artifact(json.dumps(wire))
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()

        with pytest.raises(CacheArtifactError, match="class name does not match"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert graph.snapshot() == before
        assert context.extra == {}

    def test_duplicate_ids_from_custom_generator_reject_before_graph_mutation(self):
        app = Citry()

        class Child(Component):
            citry = app
            template = """
            <span>child</span>
            """

        class Cached(Component):
            citry = app
            template = """
            <div><c-child /></div>
            """

        artifact = _export_component_artifact(Cached().render())
        app.id_generator = lambda: "duplicate"
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()

        with pytest.raises(CacheArtifactError, match="duplicate replay ID"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert graph.snapshot() == before
        assert context.extra == {}

    def test_artifact_does_not_keep_unregistered_classes_alive(self):
        app = Citry()

        class Leaf(Component):
            citry = app
            template = """
            <span>leaf</span>
            """

        class Root(Component):
            citry = app
            template = """
            <div><c-leaf /></div>
            """

        original = Root().render()
        artifact = _decode_artifact(_encode_artifact(_export_component_artifact(original)))
        leaf_ref = weakref.ref(Leaf)
        app.unregister(Leaf)
        del original
        del Leaf
        gc.collect()
        assert leaf_ref() is None
        assert artifact.frames[1].class_id is not None

    def test_supplied_slot_writer_and_nested_component_are_remapped_per_hit(self, monkeypatch):
        app = Citry()
        leaf_renders = 0

        class Leaf(Component):
            citry = app
            template = """
            <strong>leaf</strong>
            """

            def template_data(self, kwargs, slots=None):
                nonlocal leaf_renders
                leaf_renders += 1
                return {}

        class Cached(Component):
            citry = app
            template = """
            <article><c-slot name="body" /></article>
            """

        class Page(Component):
            citry = app
            template = """
            <main>
              <c-cached>
                <c-fill name="body"><b>{{ first }}<c-leaf /></b></c-fill>
              </c-cached>
              <c-cached>
                <c-fill name="body"><i>{{ second }}<c-leaf /></i></c-fill>
              </c-cached>
            </main>
            """

            def template_data(self, kwargs, slots=None):
                return {"first": "one", "second": "two"}

        _enable_test_component_cache(monkeypatch, app, Cached, "phase2:slot-writer")
        rendered = Page().render()
        html = rendered.serialize(deps_strategy="ignore")
        snapshot = rendered.context.ownership.snapshot()
        active_instances = {
            record.render_id: record for record in snapshot.logical_instances if record.state == OwnershipState.ACTIVE
        }
        page_id = next(record.render_id for record in active_instances.values() if record.class_id == Page.class_id)
        cached_ids = {record.render_id for record in active_instances.values() if record.class_id == Cached.class_id}
        leaf_instances = [record for record in active_instances.values() if record.class_id == Leaf.class_id]
        supplied = [
            fill
            for fill in snapshot.logical_fills
            if fill.kind == LogicalFillKind.NAMED and fill.state == OwnershipState.ACTIVE
        ]
        regions = [region for region in snapshot.physical_regions if region.state == RegionState.CAPTURED]

        assert leaf_renders == 1
        assert html.count("one") == 2
        assert "two" not in html
        assert len(cached_ids) == 2
        assert len(leaf_instances) == 2
        assert {record.logical_parent_render_id for record in leaf_instances} == {page_id}
        assert len(supplied) == 2
        assert {fill.lexical_owner_render_id for fill in supplied} == {page_id}
        assert {fill.receiver_render_id for fill in supplied} == cached_ids
        assert len(regions) == 2
        assert len({region.id for region in regions}) == 2
        assert {region.lexical_owner_render_id for region in regions} == {page_id}
        fills_by_receiver = {fill.receiver_render_id: fill for fill in supplied}
        assert all(
            region.source_location_id == fills_by_receiver[region.receiver_render_id].source_location_id
            for region in regions
        )
        locations = {record.id: record for record in snapshot.source_locations}
        leaf_locations = [
            locations[record.source_location_id]
            for record in snapshot.component_invocations
            if record.target_class_id == Leaf.class_id and record.state == OwnershipState.ACTIVE
        ]
        page_source = leaf_locations[0].source
        expected_starts = {page_source.find("<c-leaf />"), page_source.rfind("<c-leaf />")}
        assert {record.span[0] for record in leaf_locations} == expected_starts
        assert {record.snippet for record in leaf_locations} == {"<c-leaf />"}
        assert {record.owner_class_id for record in leaf_locations} == {Page.class_id}

    def test_supplied_slot_writer_rebinds_to_a_different_parent_class(self, monkeypatch):
        app = Citry()
        leaf_renders = 0

        class Leaf(Component):
            citry = app
            template = """
            <strong>leaf</strong>
            """

            def template_data(self, kwargs, slots=None):
                nonlocal leaf_renders
                leaf_renders += 1
                return {}

        class Cached(Component):
            citry = app
            template = """
            <article><c-slot name="body" /></article>
            """

        class FirstPage(Component):
            citry = app
            template = """
            <main>
              <c-cached>
                <c-fill name="body"><b>first<c-leaf /></b></c-fill>
              </c-cached>
            </main>
            """

        class SecondPage(Component):
            citry = app
            template = """
            <aside>
              <c-cached>
                <c-fill name="body"><i>second<c-leaf /></i></c-fill>
              </c-cached>
            </aside>
            """

        _enable_test_component_cache(monkeypatch, app, Cached, "phase2:different-writer")
        FirstPage().render()
        rendered = SecondPage().render()
        snapshot = rendered.context.ownership.snapshot()
        instances = {
            record.render_id: record for record in snapshot.logical_instances if record.state == OwnershipState.ACTIVE
        }
        second_page_id = next(
            record.render_id for record in instances.values() if record.class_id == SecondPage.class_id
        )
        leaf = next(record for record in instances.values() if record.class_id == Leaf.class_id)
        invocation = next(
            record
            for record in snapshot.component_invocations
            if record.target_render_id == leaf.render_id and record.state == OwnershipState.ACTIVE
        )
        location = next(record for record in snapshot.source_locations if record.id == invocation.source_location_id)

        assert leaf_renders == 1
        assert leaf.logical_parent_render_id == second_page_id
        assert invocation.source_render_id == second_page_id
        assert invocation.source_class_id == SecondPage.class_id
        assert location.owner_render_id == second_page_id
        assert location.owner_class_id == SecondPage.class_id
        assert location.snippet == "<c-leaf />"
        assert location.span[0] == location.source.find("<c-leaf />")

    def test_two_supplied_slots_from_one_writer_remap_independently(self, monkeypatch):
        app = Citry()
        leaf_renders = 0

        class Leaf(Component):
            citry = app

            class Kwargs:
                label: str

            template = """
            <strong>{{ label }}</strong>
            """

            def template_data(self, kwargs, slots=None):
                nonlocal leaf_renders
                leaf_renders += 1
                return {"label": kwargs.label}

        class Cached(Component):
            citry = app
            template = """
            <article>
              <c-slot name="left" />
              <c-slot name="right" />
            </article>
            """

        class Page(Component):
            citry = app
            template = """
            <main>
              <c-cached>
                <c-fill name="left"><c-leaf label="left" /></c-fill>
                <c-fill name="right"><c-leaf label="right" /></c-fill>
              </c-cached>
            </main>
            """

        _enable_test_component_cache(monkeypatch, app, Cached, "phase2:two-slot-writer")
        first = Page().render()
        second = Page().render()
        html = second.serialize(deps_strategy="ignore")
        snapshot = second.context.ownership.snapshot()
        instances = {
            record.render_id: record for record in snapshot.logical_instances if record.state == OwnershipState.ACTIVE
        }
        page_id = next(record.render_id for record in instances.values() if record.class_id == Page.class_id)
        leaves = [record for record in instances.values() if record.class_id == Leaf.class_id]
        fills = [
            fill
            for fill in snapshot.logical_fills
            if fill.kind == LogicalFillKind.NAMED and fill.state == OwnershipState.ACTIVE
        ]
        captured_regions = [region for region in snapshot.physical_regions if region.state == RegionState.CAPTURED]

        assert leaf_renders == 2
        assert "left" in html
        assert "right" in html
        assert len(leaves) == 2
        assert {leaf.logical_parent_render_id for leaf in leaves} == {page_id}
        assert {fill.slot_name for fill in fills} == {"left", "right"}
        assert {fill.lexical_owner_render_id for fill in fills} == {page_id}
        fills_by_id = {fill.id: fill for fill in fills}
        assert {
            fills_by_id[region.logical_fill_id].slot_name
            for region in captured_regions
            if region.logical_fill_id in fills_by_id
        } == {"left", "right"}
        first_ids = {
            record.render_id
            for record in first.context.ownership.snapshot().logical_instances
            if record.state == OwnershipState.ACTIVE
        }
        assert first_ids.isdisjoint(instances)

    def test_transparent_descendant_dependencies_are_replayed(self, monkeypatch):
        app = Citry()
        transparent_renders = 0

        class TransparentChild(Component):
            citry = app
            transparent = True
            js = """
            console.log("transparent child");
            """
            template = """
            <span>transparent child</span>
            """

            def template_data(self, kwargs, slots=None):
                nonlocal transparent_renders
                transparent_renders += 1
                return {}

        class Cached(Component):
            citry = app
            template = """
            <section><c-transparent-child /></section>
            """

        _enable_test_component_cache(monkeypatch, app, Cached, "phase2:transparent-dependencies")
        first = Cached().render()
        artifact = _export_component_artifact(first)
        second = Cached().render()
        records = second.context.extra[DEPENDENCIES_EXTRA_KEY]
        ownership = _thaw_json(artifact.ownership)
        assert isinstance(ownership, dict)
        instances = ownership["instances"]
        assert isinstance(instances, list)

        assert transparent_renders == 1
        assert len(instances) == 2
        assert any(instance["transparent"] for instance in instances)
        assert {record.class_id for record in records} == {TransparentChild.class_id}
        assert "transparent child" in second.serialize()

    def test_dependencies_replay_repairs_evicted_variable_script(self, monkeypatch):
        app = Citry()
        data_calls = 0

        class Cached(Component):
            citry = app
            template = """
            <div>cached</div>
            """
            js = """
            $component(({ data }) => data.count);
            """

            def js_data(self, kwargs, slots=None):
                nonlocal data_calls
                data_calls += 1
                return {"count": 7}

        _enable_test_component_cache(monkeypatch, app, Cached, "phase2:dependencies")
        first = Cached().render()
        first_record = next(iter(first.context.extra["dependencies"]))
        variables_key = gen_cache_key(Cached.class_id, "js", first_record.js_vars_hash)
        expected_value = app.cache.get(variables_key)
        assert expected_value is not None
        app.cache.delete(variables_key)

        second = Cached().render()
        second_record = next(iter(second.context.extra["dependencies"]))

        assert data_calls == 1
        assert second_record.component_id == second.frame.render_id
        assert second_record.component_id != first_record.component_id
        assert app.cache.get(variables_key) == expected_value
        first_html = first.serialize()
        second_html = second.serialize()
        assert "cached" in first_html
        assert "cached" in second_html
        assert first_record.js_vars_hash in first_html
        assert second_record.js_vars_hash in second_html

    def test_dependencies_replay_rejects_stale_css_capture_when_current_css_is_whitespace(self):
        app = Citry()

        class Cached(Component):
            citry = app
            template = """
            <div>cached</div>
            """
            css = """
            .cached { color: var(--accent); }
            """

            def css_data(self, kwargs, slots=None):
                return {"accent": "red"}

        original = Cached().render()
        record = next(iter(original.context.extra[DEPENDENCIES_EXTRA_KEY]))
        assert record.css_vars_hash is not None
        variables_key = gen_cache_key(Cached.class_id, "css", record.css_vars_hash)
        artifact = _export_component_artifact(original)
        app.cache.delete(variables_key)

        Cached.css = """
        """
        Cached.reset_files()
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()

        with pytest.raises(CacheArtifactError, match="incompatible with the current component CSS"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert app.cache.get(variables_key) is None
        assert graph.snapshot() == before
        assert context.extra == {}

    def test_revision_change_during_repair_rejects_before_replay(self, monkeypatch):
        app = Citry()

        class Cached(Component):
            citry = app
            js = """
            $component(({ data }) => data.count);
            """
            template = """
            <div>cached</div>
            """

            def js_data(self, kwargs, slots=None):
                return {"count": 7}

        original = Cached().render()
        record = next(iter(original.context.extra[DEPENDENCIES_EXTRA_KEY]))
        assert record.js_vars_hash is not None
        variables_key = gen_cache_key(Cached.class_id, "js", record.js_vars_hash)
        artifact = _export_component_artifact(original)
        app.cache.delete(variables_key)
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()
        extension = app.extensions.get_extension("cache")
        assert isinstance(extension, CacheExtension)
        revision = extension._revision_snapshot()
        original_set = app.cache.set

        def racing_set(key, value, ttl=None):
            original_set(key, value, ttl=ttl)
            if key == variables_key:
                extension._advance_revision()

        monkeypatch.setattr(app.cache, "set", racing_set)

        with pytest.raises(CacheArtifactError, match="revision changed"):
            _replay_component_artifact(
                artifact,
                boundary=boundary,
                context=context,
                revision=revision,
            )

        assert app.cache.get(variables_key) is not None
        assert graph.snapshot() == before
        assert context.extra == {}

    def test_revision_change_during_extension_staging_rejects_before_mutation(self):
        class RacingPayload(Extension):
            name = "racing_payload"
            render_cache_mode = "payload"
            render_cache_version = 1

            def export_render_cache(self, ctx):
                return {}

            def stage_render_cache(self, ctx):
                ctx.citry.extensions._advance_render_cache_revision()
                return StagedRenderCacheContribution()

        app = Citry(extensions=[RacingPayload])

        class Cached(Component):
            citry = app
            template = """
            <div>cached</div>
            """

        artifact = _export_component_artifact(Cached().render())
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()
        extension = app.extensions.get_extension("cache")
        assert isinstance(extension, CacheExtension)
        revision = extension._revision_snapshot()

        with pytest.raises(CacheArtifactError, match="revision changed"):
            _replay_component_artifact(
                artifact,
                boundary=boundary,
                context=context,
                revision=revision,
            )

        assert graph.snapshot() == before
        assert context.extra == {}

    def test_failed_replay_deletes_new_extension_repair_write(self, monkeypatch):
        repair_key = "phase2:rollback-repair"

        class RepairPayload(Extension):
            name = "repair_payload"
            render_cache_mode = "payload"
            render_cache_version = 1

            def export_render_cache(self, ctx):
                return {}

            def stage_render_cache(self, ctx):
                return StagedRenderCacheContribution(
                    cache_writes=(
                        RenderCacheWrite(
                            key=repair_key,
                            value="repaired",
                            rollback_delete=True,
                        ),
                    ),
                )

        app = Citry(extensions=[RepairPayload])

        class Cached(Component):
            citry = app
            template = """
            <div>cached</div>
            """

        artifact = _export_component_artifact(Cached().render())
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()

        def fail_import(*args, **kwargs):
            raise RuntimeError("late replay failure")

        monkeypatch.setattr(graph, "import_replayed_snapshot", fail_import)

        with pytest.raises(RuntimeError, match="late replay failure"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert app.cache.get(repair_key) is None
        assert graph.snapshot() == before
        assert context.extra == {}

    def test_noncanonical_js_variables_reject_before_repair(self):
        app = Citry()

        class Cached(Component):
            citry = app
            js = """
            $component(({ data }) => data.count);
            """
            template = """
            <div>cached</div>
            """

            def js_data(self, kwargs, slots=None):
                return {"count": 7}

        wire = json.loads(_encode_artifact(_export_component_artifact(Cached().render())))
        dependencies = next(item for item in wire["extensions"] if item["name"] == "dependencies")
        capture = dependencies["payload"]["records"][0]["js"]
        source = '{ "count":7}'
        variables_hash = sha256(source.encode()).hexdigest()[:32]
        encoded = base64.b64encode(source.encode()).decode()
        content = (
            f'Citry.manager.registerComponentData("{Cached.class_id}", "{variables_hash}", '
            f'JSON.parse(atob("{encoded}")));'
        )
        capture.update(
            {
                "hash": variables_hash,
                "source": source,
                "value": json.dumps(
                    Script(kind="variables", content=content, origin_class_id=Cached.class_id).to_json()
                ),
            }
        )
        artifact = _decode_artifact(json.dumps(wire))
        variables_key = gen_cache_key(Cached.class_id, "js", variables_hash)
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()

        with pytest.raises(CacheArtifactError, match="canonical JSON"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert app.cache.get(variables_key) is None
        assert graph.snapshot() == before
        assert context.extra == {}

    def test_unsafe_css_variables_reject_before_repair(self):
        app = Citry()

        class Cached(Component):
            citry = app
            css = ".cached { color: var(--tone); }"
            template = "<div>cached</div>"

            def css_data(self, kwargs, slots=None):
                return {"tone": "red"}

        wire = json.loads(_encode_artifact(_export_component_artifact(Cached().render())))
        dependencies = next(item for item in wire["extensions"] if item["name"] == "dependencies")
        capture = dependencies["payload"]["records"][0]["css"]
        unsafe_source = json.dumps({"x; } body { color": "red"}, separators=(",", ":"))
        capture["source"] = unsafe_source

        artifact = _decode_artifact(json.dumps(wire))
        unsafe_hash = sha256(unsafe_source.encode()).hexdigest()[:32]
        variables_key = gen_cache_key(Cached.class_id, "css", unsafe_hash)
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()

        with pytest.raises(CacheArtifactError, match=r"css_data\(\) entry .* cannot be emitted"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert app.cache.get(variables_key) is None
        assert graph.snapshot() == before
        assert context.extra == {}

    def test_events_replay_mints_fresh_identity_without_rebuilding_state(self, monkeypatch):
        from citry.ext.events import tokens

        app = Citry(secret=_SIGNING_KEY)
        state_builds = 0
        mint_times = iter((1_000.0, 2_000.0))
        monkeypatch.setattr(tokens, "_now", lambda: next(mint_times))

        class Cached(Component):
            citry = app

            class State:
                count: int = 3
                _public = ("count",)

                def __post_init__(self):
                    nonlocal state_builds
                    state_builds += 1

            class Events:
                def increment(self, state):
                    return None

            template = """
            <button>increment</button>
            """

        _enable_test_component_cache(monkeypatch, app, Cached, "phase2:events")
        first = Cached().render()
        first_entry = next(iter(first.context.extra[EVENTS_EXTRA_KEY]))
        second = Cached().render()
        second_entry = next(iter(second.context.extra[EVENTS_EXTRA_KEY]))

        assert state_builds == 1
        assert first_entry.render_id == first.frame.render_id
        assert second_entry.render_id == second.frame.render_id
        assert second_entry.render_id != first_entry.render_id
        assert second_entry.state_token != first_entry.state_token
        assert second_entry.state_token is not None
        assert verify_state_token(
            second_entry.state_token,
            cls=Cached,
            secrets=[_SIGNING_KEY],
        ).state_kwargs == {"count": 3}
        assert f'data-cid="{second_entry.render_id}"' in second.frame.root_markers

    def test_server_state_replay_mints_a_fresh_token_without_state_construction(self):
        app = Citry()
        state_builds = 0

        class Cached(Component):
            citry = app

            class State:
                value: int = 5
                _public = ("value",)
                _storage = "server"

                def __post_init__(self):
                    nonlocal state_builds
                    state_builds += 1

            class Events:
                def update(self, state):
                    return None

            template = """
            <button>update</button>
            """

        original = Cached().render()
        original_entry = next(iter(original.context.extra[EVENTS_EXTRA_KEY]))
        artifact = _decode_artifact(_encode_artifact(_export_component_artifact(original)))
        boundary, context, _graph = _boundary(Cached())

        replayed = _replay_component_artifact(artifact, boundary=boundary, context=context)
        replayed_entry = next(iter(replayed.context.extra[EVENTS_EXTRA_KEY]))

        assert state_builds == 1
        assert replayed_entry.render_id == boundary.id
        assert replayed_entry.state_token is not None
        assert replayed_entry.state_token.startswith("ces1.")
        assert replayed_entry.state_token != original_entry.state_token
        assert app.cache.has(replayed_entry.state_token.removeprefix("ces1."))

    def test_missing_server_state_rejects_before_graph_or_context_mutation(self):
        app = Citry()

        class Cached(Component):
            citry = app

            class State:
                value: int = 5
                _storage = "server"

            class Events:
                def update(self, state):
                    return None

            template = """
            <button>update</button>
            """

        original = Cached().render()
        original_entry = next(iter(original.context.extra[EVENTS_EXTRA_KEY]))
        artifact = _decode_artifact(_encode_artifact(_export_component_artifact(original)))
        assert original_entry.state_token is not None
        app.cache.delete(original_entry.state_token.removeprefix("ces1."))
        boundary, context, graph = _boundary(Cached())
        before_graph = graph.snapshot()
        before_extra = dict(context.extra)

        with pytest.raises(CacheArtifactError, match="no longer replayable"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert graph.snapshot() == before_graph
        assert context.extra == before_extra

    def test_cross_section_frame_reference_rejects_before_mutation(self):
        app = Citry()

        class Child(Component):
            citry = app
            template = """
            <span>child</span>
            """

        class Cached(Component):
            citry = app
            template = """
            <div><c-child /></div>
            """

        wire = json.loads(_encode_artifact(_export_component_artifact(Cached().render())))
        wire["frames"][1]["instance"] = 99
        artifact = _decode_artifact(json.dumps(wire))
        boundary, context, graph = _boundary(Cached())
        before = graph.snapshot()

        with pytest.raises(CacheArtifactError, match="missing ownership instance"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert graph.snapshot() == before
        assert context.extra == {}

    def test_bad_region_rejects_before_dependency_repair(self):
        app = Citry()

        class Cached(Component):
            citry = app
            css = """
            .cached { color: var(--tone); }
            """
            template = """
            <div><c-slot name="body" /></div>
            """

            def css_data(self, kwargs, slots=None):
                return {"tone": "red"}

        original = Cached(slots={"body": "content"}).render()
        variables_hash = next(iter(original.context.extra[DEPENDENCIES_EXTRA_KEY])).css_vars_hash
        assert variables_hash is not None
        variables_key = gen_cache_key(Cached.class_id, "css", variables_hash)
        artifact = _export_component_artifact(original)
        app.cache.delete(variables_key)

        def corrupt_region(part):
            from citry.ext.cache.artifact import ArtifactFramePart, ArtifactRegionPart

            if isinstance(part, ArtifactRegionPart):
                return replace(part, region=99)
            if isinstance(part, ArtifactFramePart):
                return part
            return part

        frames = []
        corrupted = False
        for frame in artifact.frames:
            parts = []
            for part in frame.parts:
                changed = corrupt_region(part)
                corrupted = corrupted or changed != part
                parts.append(changed)
            frames.append(replace(frame, parts=tuple(parts)))
        assert corrupted
        artifact = replace(artifact, frames=tuple(frames))
        boundary, context, graph = _boundary(Cached(slots={"body": "content"}))
        before = graph.snapshot()

        with pytest.raises(CacheArtifactError, match="missing ownership region"):
            _replay_component_artifact(artifact, boundary=boundary, context=context)

        assert app.cache.get(variables_key) is None
        assert graph.snapshot() == before
        assert context.extra == {}


class TestCoreCacheCheckpoint:
    def test_hit_runs_input_but_skips_data_render_and_rendered_hooks(self, monkeypatch):
        calls: list[str] = []

        class Probe(Extension):
            name = "probe"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_input(self, ctx):
                if type(ctx.component).__name__ == "Cached":
                    calls.append("input")

            def on_component_data(self, ctx):
                if type(ctx.component).__name__ == "Cached":
                    calls.append("data-hook")

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Cached":
                    calls.append("rendered-hook")

        app = Citry(extensions=[Probe])

        class Child(Component):
            citry = app
            template = """
            <small>child</small>
            """

            def template_data(self, kwargs, slots):
                calls.append("child-data")
                return {}

        class Cached(Component):
            citry = app
            template = """
            <section><c-child /></section>
            """

            def template_data(self, kwargs, slots):
                calls.append("template-data")
                return {}

            def js_data(self, kwargs, slots):
                calls.append("js-data")
                return {}

            def css_data(self, kwargs, slots):
                calls.append("css-data")
                return {}

            def on_render(self):
                calls.append("on-render")

        _enable_test_component_cache(monkeypatch, app, Cached, "phase2:hit")
        first = Cached().render()
        first_calls = list(calls)
        calls.clear()
        second = Cached().render()

        assert first_calls == [
            "input",
            "template-data",
            "js-data",
            "css-data",
            "data-hook",
            "on-render",
            "child-data",
            "rendered-hook",
        ]
        assert calls == ["input"]
        assert _normalize_ids(first.serialize(deps_strategy="ignore")) == _normalize_ids(
            second.serialize(deps_strategy="ignore")
        )
        first_ids = {
            record.render_id
            for record in first.context.ownership.snapshot().logical_instances
            if record.state == OwnershipState.ACTIVE
        }
        second_ids = {
            record.render_id
            for record in second.context.ownership.snapshot().logical_instances
            if record.state == OwnershipState.ACTIVE
        }
        assert first_ids.isdisjoint(second_ids)

    def test_corrupt_entry_becomes_a_miss_and_is_overwritten(self, monkeypatch):
        app = Citry()
        calls = 0

        class Cached(Component):
            citry = app
            template = """
            <p>fresh</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        key = "phase2:corrupt"
        app.cache.set(key, "not an artifact")
        _enable_test_component_cache(monkeypatch, app, Cached, key)

        assert "fresh" in Cached().render().serialize(deps_strategy="ignore")
        assert calls == 1
        assert _decode_artifact(app.cache.get(key))

    def test_revision_change_during_lookup_rebuilds_the_physical_key(self, monkeypatch):
        app = Citry()

        class Cached(Component):
            citry = app
            template = """
            <p>fresh</p>
            """

        extension = app.extensions.get_extension("cache")
        assert isinstance(extension, CacheExtension)
        first_get = True
        original_get = app.cache.get

        def racing_get(key):
            nonlocal first_get
            value = original_get(key)
            if first_get:
                first_get = False
                extension._advance_revision()
            return value

        def lookup(_component, _context):
            key = f"phase2:revision-key:{extension._revision_snapshot()}"
            return extension._lookup_physical_key(key, ttl=None, max_entry_bytes=None)

        monkeypatch.setattr(app.cache, "get", racing_get)
        monkeypatch.setattr(extension, "_lookup_component", lookup)

        assert "fresh" in Cached().render().serialize(deps_strategy="ignore")
        assert app.cache.get("phase2:revision-key:0") is None
        assert _decode_artifact(app.cache.get("phase2:revision-key:1"))

    def test_recovered_invalid_initial_generator_yield_skips_publication(self, monkeypatch):
        app = Citry()

        class Cached(Component):
            citry = app
            template = """
            <p>unused</p>
            """

            def on_render(self):
                _result, error = yield 42
                assert isinstance(error, TypeError)
                return "<p>fallback</p>"

        key = "phase2:invalid-yield"
        _enable_test_component_cache(monkeypatch, app, Cached, key)
        rendered = Cached().render()

        assert "fallback" in rendered.serialize(deps_strategy="ignore")
        assert rendered.context._error_tainted
        assert app.cache.get(key) is None

    def test_recovered_descendant_error_taints_and_skips_publication(self, monkeypatch):
        app = Citry()

        class Failing(Component):
            citry = app
            template = """
            <i>unused</i>
            """

            def template_data(self, kwargs, slots):
                raise ValueError("temporary")

        class CachedBoundary(Component):
            citry = app
            template = """
            <div><c-failing /></div>
            """

            def on_render(self):
                _result, error = yield
                if error is not None:
                    return "<p>fallback</p>"
                return None

        key = "phase2:tainted"
        _enable_test_component_cache(monkeypatch, app, CachedBoundary, key)
        rendered = CachedBoundary().render()

        assert "fallback" in rendered.serialize(deps_strategy="ignore")
        assert rendered.context._error_tainted
        assert app.cache.get(key) is None

    def test_intermediate_extension_error_stays_tainted_after_later_recovery(self, monkeypatch):
        class RaiseOnFinalize(Extension):
            name = "raise_on_finalize"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_rendered(self, ctx):
                raise ValueError("temporary")

        class RecoverFinalize(Extension):
            name = "recover_finalize"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_rendered(self, ctx):
                if ctx.error is not None:
                    return "<p>fallback</p>"
                return None

        app = Citry(extensions=[RaiseOnFinalize, RecoverFinalize])

        class Cached(Component):
            citry = app
            template = """
            <p>normal</p>
            """

        key = "phase2:extension-taint"
        _enable_test_component_cache(monkeypatch, app, Cached, key)
        rendered = Cached().render()

        assert "fallback" in rendered.serialize(deps_strategy="ignore")
        assert rendered.context._error_tainted
        assert app.cache.get(key) is None

    def test_revision_change_during_finalize_skips_publication(self, monkeypatch):
        app: Citry

        class ResetRevision(Extension):
            name = "reset_revision"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Cached":
                    ctx.citry.extensions._advance_render_cache_revision()

        app = Citry(extensions=[ResetRevision])

        class Cached(Component):
            citry = app
            template = """
            <p>done</p>
            """

        key = "phase2:stale-publication"
        _enable_test_component_cache(monkeypatch, app, Cached, key)

        assert "done" in Cached().render().serialize(deps_strategy="ignore")
        assert app.cache.get(key) is None

    def test_participating_deny_extension_skips_publication(self, monkeypatch):
        class DenyOutputCache(Extension):
            name = "deny_output_cache"

            def on_component_data(self, ctx):
                ctx.template_data["message"] = "changed"

        app = Citry(extensions=[DenyOutputCache])

        class Cached(Component):
            citry = app
            template = """
            <p>{{ message }}</p>
            """

        key = "phase2:denied"
        _enable_test_component_cache(monkeypatch, app, Cached, key)

        assert "changed" in Cached().render().serialize(deps_strategy="ignore")
        assert app.cache.get(key) is None
