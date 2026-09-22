from __future__ import annotations

import gc
import json
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from citry import Citry, Component, Extension, InMemoryCache
from citry._vue.capture import (
    PreparedAttribute,
    PreparedBrowserBinding,
    PreparedDynamicElementOpen,
    PreparedElementOpen,
    PreparedStaticRun,
    PreparedTextValue,
    PreparedVerbatimHtml,
    StaticRunOpening,
    StaticRunStructure,
    is_authenticated_browser_binding,
    is_authenticated_dynamic_element_open,
    prepared_browser_binding,
    prepared_dynamic_element_open,
    render_prepared,
    render_prepared_direct,
)
from citry._vue.direct_capture import (
    UnsupportedPreparedView,
    _issue_cache_replay_identity,
    _matches_cache_replay_identity,
    assemble_typed_render,
)
from citry._vue.leaf_program import static_leaf_parts, typed_leaf_parts
from citry.citry_context import CitryContext
from citry.citry_render import CitryRender
from citry.component_registry import NotRegistered
from citry.ext.cache import component_cache_key
from citry.ext.cache.artifact import (
    ArtifactAttribute,
    ArtifactDirectPythonComponentPart,
    ArtifactDirectSlotPart,
    ArtifactElementOpenPart,
    ArtifactExtension,
    ArtifactFrame,
    ArtifactFramePart,
    ArtifactPreparedBinding,
    ArtifactPreparedCall,
    ArtifactSourceTextPart,
    ArtifactStaticRunOpening,
    ArtifactStaticRunPart,
    ArtifactStaticRunStructure,
    ArtifactTextValuePart,
    ArtifactVerbatimHtmlPart,
    CachedRenderArtifact,
    FrozenJsonObject,
    _decode_artifact,
    _encode_artifact,
)
from citry.ext.cache.errors import CacheArtifactError, _CacheArtifactCompatibilityError
from citry.ext.cache.replay import (
    _export_typed_leaf,
    _replay_typed_leaf,
    _source_fingerprint,
    _UnsupportedTypedCachePart,
)
from citry.ext.events.emission import EXTRA_KEY as EVENTS_EXTRA_KEY
from citry.extension import RenderCacheWrite, StagedRenderCacheContribution


def _artifact(*parts: object) -> CachedRenderArtifact:
    return CachedRenderArtifact(
        root_frame=0,
        frames=(
            ArtifactFrame(
                instance=0,
                class_id="tests.Card",
                class_name="Card",
                is_component_root=True,
                root_markers=(),
                parts=parts,
            ),
        ),
        extensions=(),
    )


def test_typed_codec_is_version_one_and_keeps_source_separate_from_values() -> None:
    artifact = _artifact(
        ArtifactSourceTextPart("<p>{{ value }}</p>", (0, 3), "<p>"),
        ArtifactVerbatimHtmlPart("<c-raw>{{ value }}</c-raw>", (7, 18), "{{ value }}"),
        ArtifactTextValuePart("<p>{{ value }}</p>", (3, 14), "<script>{{ unsafe }}</script>"),
        ArtifactElementOpenPart(
            source="<button :title='title'>",
            span=(0, 23),
            tag="button",
            attrs=(ArtifactAttribute("title", "data", (8, 22), "{{ still-data }}"),),
            is_void=False,
            is_self_closing=False,
            element_metadata=None,
            event_bindings=(),
        ),
    )

    encoded = _encode_artifact(artifact)
    wire = json.loads(encoded)

    assert wire["artifact_version"] == 1
    assert wire["frames"][0]["parts"][1] == [
        "verbatim_html",
        "<c-raw>{{ value }}</c-raw>",
        [7, 18],
        "{{ value }}",
    ]
    assert wire["frames"][0]["parts"][2][0] == "text_value"
    assert wire["frames"][0]["parts"][2][3] == "<script>{{ unsafe }}</script>"
    assert _decode_artifact(encoded) == artifact


def test_verbatim_html_cache_replay_keeps_origin_and_opaque_bytes() -> None:
    value = PreparedVerbatimHtml("<c-raw>a < b {{ x }}</c-raw>", (7, 20), "a < b {{ x }}")
    assert _replay_typed_leaf(_export_typed_leaf(value)) == value


def test_typed_codec_rejects_unknown_parts_and_cross_frame_references() -> None:
    wire = json.loads(_encode_artifact(_artifact(ArtifactSourceTextPart("x", (0, 1), "x"))))
    wire["frames"][0]["parts"] = [["future_part", "x"]]
    with pytest.raises(CacheArtifactError, match="unknown or malformed"):
        _decode_artifact(json.dumps(wire))

    invalid = _artifact(
        ArtifactDirectSlotPart(
            frame=1,
            execution=1,
            parent_execution=None,
            external_parent_execution=False,
            lexical_instance=0,
            lexical_parent_depth=None,
            receiver_instance=0,
            receiver_parent_depth=None,
            kind="fallback",
            public_name="content",
            fill_source="fill",
            source="x",
            span=(0, 1),
            origin=None,
        )
    )
    with pytest.raises(CacheArtifactError, match="missing frame"):
        _encode_artifact(invalid)


def test_typed_codec_rejects_post_migration_version_two() -> None:
    wire = json.loads(_encode_artifact(_artifact()))
    wire["artifact_version"] = 2
    with pytest.raises(_CacheArtifactCompatibilityError, match="supported integer value 1"):
        _decode_artifact(json.dumps(wire))


def test_typed_codec_rejects_duplicate_json_fields() -> None:
    with pytest.raises(CacheArtifactError, match="duplicate"):
        _decode_artifact('{"artifact_version":1,"artifact_version":1}')


def test_typed_codec_rejects_bool_cycle_shared_and_unreachable_frame_references() -> None:
    child = ArtifactFrame(
        instance=1,
        class_id="tests.Child",
        class_name="Child",
        is_component_root=True,
        root_markers=(),
        parts=(),
    )
    artifact = CachedRenderArtifact(
        root_frame=0,
        frames=(_artifact(ArtifactFramePart(1)).frames[0], child),
        extensions=(),
    )
    wire = json.loads(_encode_artifact(artifact))

    invalid_bool = json.loads(json.dumps(wire))
    invalid_bool["root_frame"] = True
    with pytest.raises(CacheArtifactError, match="root_frame"):
        _decode_artifact(json.dumps(invalid_bool))

    cycle = json.loads(json.dumps(wire))
    cycle["frames"][1]["parts"] = [["frame", 0]]
    with pytest.raises(CacheArtifactError, match="cycle"):
        _decode_artifact(json.dumps(cycle))

    shared = json.loads(json.dumps(wire))
    shared["frames"][0]["parts"].append(["frame", 1])
    with pytest.raises(CacheArtifactError, match="more than once"):
        _decode_artifact(json.dumps(shared))

    unreachable = json.loads(json.dumps(wire))
    unreachable["frames"][0]["parts"] = []
    with pytest.raises(CacheArtifactError, match="unreachable"):
        _decode_artifact(json.dumps(unreachable))


def test_typed_codec_rejects_duplicate_frozen_keys_and_reserved_root_markers() -> None:
    malformed = replace(
        _artifact(),
        extensions=(ArtifactExtension("probe", 1, FrozenJsonObject((("x", 1), ("x", 2)))),),
    )
    with pytest.raises(CacheArtifactError, match="unique"):
        _encode_artifact(malformed)

    for marker in ('data-cid="archived-id"', "data-cid-archived-id", 'data-probe="unterminated'):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["frames"][0]["root_markers"] = [marker]
        with pytest.raises(CacheArtifactError, match=r"marker|attribute"):
            _decode_artifact(json.dumps(wire))


def test_typed_codec_validates_prepared_binding_span_against_its_own_source() -> None:
    artifact = CachedRenderArtifact(
        root_frame=0,
        frames=(
            ArtifactFrame(
                instance=0,
                class_id="tests.Card",
                class_name="Card",
                is_component_root=True,
                root_markers=(),
                parts=(),
                prepared_call=ArtifactPreparedCall(
                    source="a much longer parent source",
                    span=(0, 1),
                    explicit_key=None,
                    origin=None,
                    slot_free_body=True,
                    raw_slots_present=False,
                    bindings=(ArtifactPreparedBinding("prop", "label", "x", "x", (0, 2)),),
                ),
            ),
        ),
        extensions=(),
    )

    with pytest.raises(CacheArtifactError, match="exceeds its source UTF-8 length"):
        _decode_artifact(_encode_artifact(artifact))


def test_typed_codec_rejects_invalid_static_run_offsets() -> None:
    artifact = _artifact(
        ArtifactStaticRunPart(
            "<p>",
            ArtifactStaticRunStructure((ArtifactStaticRunOpening(999, 500, 1000, 0, ()),), 0),
        )
    )

    with pytest.raises(CacheArtifactError, match="offsets must be ordered within"):
        _decode_artifact(_encode_artifact(artifact))


def test_static_run_tag_transitions_survive_cache_codec_and_replay() -> None:
    value = PreparedStaticRun(
        "<section><textarea>x</textarea></section>",
        StaticRunStructure(
            (StaticRunOpening(0, 8, 9, 0, frozenset({"data-probe"})),),
            0,
            (("open", "section"), ("open", "textarea"), ("close", "textarea"), ("close", "section")),
        ),
    )
    exported = _export_typed_leaf(value)
    artifact = _artifact(exported)

    decoded = _decode_artifact(_encode_artifact(artifact))

    assert decoded == artifact
    assert _replay_typed_leaf(decoded.frames[0].parts[0]) == value


def test_typed_codec_rejects_malformed_static_run_tag_transitions() -> None:
    artifact = _artifact(
        ArtifactStaticRunPart(
            "<section></section>",
            ArtifactStaticRunStructure((), 0, (("open", "section"), ("close", "section"))),
        )
    )
    wire = json.loads(_encode_artifact(artifact))
    wire["frames"][0]["parts"][0][2][2][0] = ["push", "section"]

    with pytest.raises(CacheArtifactError, match="open/close tag transition"):
        _decode_artifact(json.dumps(wire))


def test_typed_codec_rejects_source_spans_inside_a_utf8_code_point() -> None:
    artifact = _artifact(ArtifactSourceTextPart("é", (1, 2), "é"))

    with pytest.raises(CacheArtifactError, match="UTF-8 byte boundaries"):
        _decode_artifact(_encode_artifact(artifact))


def test_python_component_wrapper_round_trips_with_its_local_ordinal() -> None:
    child = ArtifactFrame(
        instance=1,
        class_id="tests.Child",
        class_name="Child",
        is_component_root=True,
        root_markers=(),
        parts=(ArtifactSourceTextPart("child", (0, 5), "child"),),
    )
    artifact = CachedRenderArtifact(
        root_frame=0,
        frames=(
            ArtifactFrame(
                instance=0,
                class_id="tests.Root",
                class_name="Root",
                is_component_root=True,
                root_markers=(),
                parts=(ArtifactDirectPythonComponentPart(1, 2),),
            ),
            child,
        ),
        extensions=(),
    )

    assert _decode_artifact(_encode_artifact(artifact)) == artifact


def test_cached_python_slot_component_replays_explicit_composition_wrapper() -> None:
    app = Citry(autodiscover=False)
    calls: list[str] = []

    class Child(Component):
        citry = app
        template = "<b>child</b>"

    class Outlet(Component):
        citry = app
        template = "<section>{{ content }}</section>"

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "stable"

        def template_data(self, kwargs, slots):
            calls.append("data")
            return {"content": slots["default"]()}

    def child(_ctx):
        calls.append("slot")
        return Child()

    tag_for_type = lambda value: "x-" + value.lower().replace("_", "-")  # noqa: E731
    first_render = render_prepared_direct(Outlet(slots={"default": child}))
    second_render = render_prepared_direct(Outlet(slots={"default": child}))
    first = assemble_typed_render(first_render, revision=0, tag_for_type=tag_for_type)
    second = assemble_typed_render(second_render, revision=0, tag_for_type=tag_for_type)

    assert calls == ["data", "slot"]
    assert first_render.frame.render_id != second_render.frame.render_id
    assert [item.type_key for item in first.view.occurrences] == [item.type_key for item in second.view.occurrences]


def test_cache_replay_identity_requires_issued_current_engine_class(monkeypatch) -> None:
    app = Citry(autodiscover=False)
    foreign = Citry(autodiscover=False)

    class Card(Component):
        citry = app

    context = CitryContext(component=None)
    assert not _matches_cache_replay_identity(context, app, Card)

    _issue_cache_replay_identity(context, app, Card)
    assert _matches_cache_replay_identity(context, app, Card)
    assert not _matches_cache_replay_identity(context, foreign, Card)

    original_lookup = type(app).get_component_by_class_id

    class Replacement:
        pass

    def stale_lookup(self, class_id):
        if self is app and class_id == Card.class_id:
            return Replacement
        return original_lookup(self, class_id)

    monkeypatch.setattr(type(app), "get_component_by_class_id", stale_lookup)
    assert not _matches_cache_replay_identity(context, app, Card)


def test_cache_replay_identity_rejects_a_live_or_foreign_class_context() -> None:
    app = Citry(autodiscover=False)
    foreign = Citry(autodiscover=False)

    class Card(Component):
        citry = app

    with pytest.raises(TypeError, match="componentless"):
        _issue_cache_replay_identity(CitryContext(component=Card()), app, Card)
    with pytest.raises((KeyError, TypeError), match=r"registry class|registered"):
        _issue_cache_replay_identity(CitryContext(component=None), foreign, Card)


def test_componentless_prepared_frame_without_decoder_identity_is_rejected() -> None:
    app = Citry(autodiscover=False)

    class Child(Component):
        citry = app
        template = "<b>child</b>"

    class Parent(Component):
        citry = app
        template = "<main><c-Child /></main>"

    rendered = render_prepared_direct(Parent())
    nested = next(part for part in rendered.parts if isinstance(part, CitryRender))
    nested.context.component = None

    with pytest.raises(UnsupportedPreparedView, match="engine registry identity"):
        assemble_typed_render(
            rendered,
            revision=0,
            tag_for_type=lambda value: "x-" + value.lower().replace("_", "-"),
        )


def test_typed_codec_rejects_invalid_spans_and_nonfinite_values() -> None:
    wire = json.loads(_encode_artifact(_artifact()))
    wire["frames"][0]["parts"] = [["source_text", "x", [2, 1], "x"]]
    with pytest.raises(CacheArtifactError, match="must not precede"):
        _decode_artifact(json.dumps(wire))

    wire["frames"][0]["parts"] = [["text_value", "x", [0, 1], float("nan")]]
    with pytest.raises(CacheArtifactError, match=r"finite JSON|non-finite|valid JSON"):
        _decode_artifact(json.dumps(wire))

    wire = json.loads(_encode_artifact(_artifact()))
    wire["frames"][0]["parts"] = [["source_text", "x", [0, 999], "x"]]
    with pytest.raises(CacheArtifactError, match="source UTF-8 length"):
        _decode_artifact(json.dumps(wire))


def test_typed_leaf_replay_keeps_template_shaped_values_in_the_data_channel() -> None:
    value = PreparedTextValue("{{ value }}", (0, 11), "{{ x }} <script>alert(1)</script>")

    replayed = _replay_typed_leaf(_export_typed_leaf(value))

    assert replayed == value
    assert replayed.value == "{{ x }} <script>alert(1)</script>"


def test_dynamic_open_replay_runs_the_current_validating_factory() -> None:
    opening = prepared_dynamic_element_open("section", {"title": "{{ data }}"})

    replayed = _replay_typed_leaf(_export_typed_leaf(opening))

    assert replayed.tag == "section"
    assert dict(replayed.attrs) == {"title": "{{ data }}"}


def test_dynamic_open_cache_keeps_authored_vue_source_and_key_separate_from_data() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Card(Component):
        citry = app
        template = '<c-element c-is="tag" @click="count++" :title="label" #c-key="key" c-class="klass" />'

        def template_data(self, kwargs, slots):
            return {"tag": "button", "key": "row", "klass": "data"}

        def js_data(self, kwargs, slots):
            return {"count": 0, "label": "label"}

    rendered = render_prepared_direct(Card())
    pending = [rendered]
    opening = None
    while pending and opening is None:
        current = pending.pop()
        for part in current.parts:
            if type(part) is PreparedDynamicElementOpen:
                opening = part
                break
            if hasattr(part, "parts"):
                pending.append(part)
    assert opening is not None

    exported = _export_typed_leaf(opening)
    decoded = _decode_artifact(_encode_artifact(_artifact(exported)))
    replayed = _replay_typed_leaf(decoded.frames[0].parts[0])

    assert replayed.key == "row"
    assert is_authenticated_dynamic_element_open(replayed)
    assert dict(replayed.attrs) == {"class": "data", "data-citry-key": ":row"}
    assert [attr.value for attr in replayed.authored_attrs] == ['@click="count++"', ':title="label"']


def test_common_leaf_component_cache_hit_skips_data_and_keeps_fresh_boundary() -> None:
    app = Citry()
    calls: list[str] = []

    class Card(Component):
        citry = app
        template = "<p>{{ value }}</p>"

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            calls.append("data")
            return {"value": "{{ remains data }}"}

    first = render_prepared(Card())
    second = render_prepared(Card())

    assert calls == ["data"]
    assert first.frame.render_id != second.frame.render_id
    assert first.parts[0].fragment == second.parts[0].fragment
    assert first.parts[0].prepared_data == second.parts[0].prepared_data
    assert typed_leaf_parts(first.parts[0]) == typed_leaf_parts(second.parts[0])
    assert static_leaf_parts(first.parts[0]) == static_leaf_parts(second.parts[0])


def test_source_fingerprint_mismatch_is_a_diagnosed_miss_and_fresh_store() -> None:
    app = Citry()
    calls: list[str] = []

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            calls.append("data")
            return {}

    render_prepared_direct(Card())
    key, entry = next(iter(app.cache._data.items()))
    wire = json.loads(entry[0])
    wire["frames"][0]["source_fingerprint"] = "0" * 64
    app.cache._data[key] = (json.dumps(wire), entry[1])

    render_prepared_direct(Card())
    repaired = json.loads(app.cache._data[key][0])

    assert calls == ["data", "data"]
    assert repaired["frames"][0]["source_fingerprint"] != "0" * 64


def test_archived_class_name_mismatch_rejects_replay_and_rebuilds() -> None:
    app = Citry()
    calls = 0

    class Card(Component):
        citry = app

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return {}

        template = """
        <p>card</p>
        """

    render_prepared_direct(Card())
    key, entry = next(iter(app.cache._data.items()))
    wire = json.loads(entry[0])
    wire["frames"][0]["class_name"] = "ArchivedCard"
    app.cache._data[key] = (json.dumps(wire), entry[1])

    render_prepared_direct(Card())

    assert calls == 2
    refreshed = json.loads(app.cache._data[key][0])
    assert refreshed["frames"][0]["class_name"] == "Card"


def test_duplicate_custom_generator_ids_reject_replay_and_rebuild() -> None:
    app = Citry()
    calls: list[str] = []

    class Child(Component):
        citry = app

        def template_data(self, kwargs, slots):
            calls.append("child")
            return {}

        template = """
        <span>child</span>
        """

    class Parent(Component):
        citry = app

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            calls.append("parent")
            return {}

        template = """
        <div><c-Child /></div>
        """

    render_prepared_direct(Parent())
    app.id_generator = lambda: "duplicate"

    render_prepared_direct(Parent())

    assert calls == ["parent", "child", "parent", "child"]


def test_missing_descendant_registration_never_serves_stale_cached_output() -> None:
    app = Citry()
    child_calls = 0

    class Child(Component):
        citry = app

        def template_data(self, kwargs, slots):
            nonlocal child_calls
            child_calls += 1
            return {}

        template = """
        <span>child</span>
        """

    class Parent(Component):
        citry = app

        class Cache:
            enabled = True

        template = """
        <div><c-Child /></div>
        """

    render_prepared_direct(Parent())
    app.unregister(Child)

    with pytest.raises(NotRegistered, match="child"):
        render_prepared_direct(Parent())

    assert child_calls == 1


def test_alias_remap_invalidates_cached_native_prop_call() -> None:
    app = Citry()
    calls: list[str] = []

    class Old(Component):
        citry = app
        template = "<span>old</span>"

        def template_data(self, kwargs, slots):
            calls.append("old")
            return kwargs

    app.register(Old, "target")

    class Parent(Component):
        citry = app
        template = '<c-target :title="label" />'
        js = "$component({data(){return {label:'native'}}});"

        class Cache:
            enabled = True

    render_prepared_direct(Parent())
    app.unregister("target")

    class New(Component):
        citry = app
        template = "<strong>new</strong>"

        def template_data(self, kwargs, slots):
            calls.append("new")
            return kwargs

    app.register(New, "target")
    render_prepared_direct(Parent())

    assert app.get("old") is Old
    assert app.get("target") is New
    assert calls == ["old", "new"]


def test_alias_removal_invalidates_cached_call_before_missing_tag_error() -> None:
    app = Citry()

    class Retained(Component):
        citry = app
        template = "<span>target</span>"

    app.register(Retained, "target")

    class Parent(Component):
        citry = app
        template = '<c-target :title="label" />'
        js = "$component({data(){return {label:'native'}}});"

        class Cache:
            enabled = True

    render_prepared_direct(Parent())
    app.unregister("target")

    assert app.get("retained") is Retained
    with pytest.raises(NotRegistered, match="target"):
        render_prepared_direct(Parent())


def test_source_fingerprint_ignores_checkout_specific_template_origin(monkeypatch) -> None:
    class Card:
        pass

    template = type("Template", (), {"source": "<p>card</p>", "origin": "/worker-a/app/card.html"})()
    monkeypatch.setattr("citry.ext.cache.replay.load_template", lambda _component_class: template)
    first = _source_fingerprint(Card)
    template.origin = "/worker-b/app/card.html"

    assert _source_fingerprint(Card) == first


def test_revision_change_inside_backend_set_removes_old_publication() -> None:
    app = Citry()
    extension = app.extensions.get_extension("cache")
    original_set = app.cache.set

    def invalidating_set(key, value, ttl=None):
        original_set(key, value, ttl=ttl)
        extension._advance_revision()

    app.cache.set = invalidating_set

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

    old_key = component_cache_key(Card, vary={})
    render_prepared_direct(Card())

    assert app.cache.get(old_key) is None


def test_revision_change_during_lookup_rebuilds_the_physical_key(monkeypatch) -> None:
    app = Citry()
    extension = app.extensions.get_extension("cache")
    first_get = True
    original_get = app.cache.get

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

    def racing_get(key):
        nonlocal first_get
        value = original_get(key)
        if first_get:
            first_get = False
            extension._advance_revision()
        return value

    monkeypatch.setattr(app.cache, "get", racing_get)
    render_prepared_direct(Card())

    assert app.cache.get(component_cache_key(Card, vary={})) is not None


def test_revision_change_during_replay_rolls_back_new_staged_write(monkeypatch) -> None:
    app = Citry()
    extension = app.extensions.get_extension("cache")
    calls = 0

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return {}

    render_prepared_direct(Card())
    original_set = app.cache.set

    def invalidating_set(key, value, ttl=None):
        original_set(key, value, ttl=ttl)
        if key == "repair:key":
            extension._advance_revision()

    monkeypatch.setattr(app.cache, "set", invalidating_set)

    def stage_repair(*_args, **_kwargs):
        return (
            StagedRenderCacheContribution(
                cache_writes=(RenderCacheWrite("repair:key", "repair", rollback_delete=True),),
            ),
        )

    monkeypatch.setattr(app.extensions, "_stage_render_cache", stage_repair)

    render_prepared_direct(Card())

    assert calls == 2
    assert app.cache.get("repair:key") is None


def test_public_component_cache_honors_ttl_expiry(monkeypatch) -> None:
    now = [100.0]
    monkeypatch.setattr("citry.cache.time.monotonic", lambda: now[0])
    app = Citry()
    calls = 0

    class Card(Component):
        citry = app
        template = "<p>{{ generation }}</p>"

        class Cache:
            enabled = True
            ttl = 5

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return {"generation": calls}

    render_prepared_direct(Card())
    now[0] = 104.99
    render_prepared_direct(Card())
    assert calls == 1
    now[0] = 105.0
    render_prepared_direct(Card())
    assert calls == 2


def test_hit_observer_runs_after_replay_while_data_and_render_hooks_are_skipped() -> None:
    calls: list[str] = []

    class Probe(Extension):
        name = "cache_probe"
        render_cache_mode = "stateless"
        render_cache_version = 1

        def on_component_input(self, ctx):
            if type(ctx.component).__name__ == "Card":
                calls.append("input")

        def on_component_data(self, ctx):
            if type(ctx.component).__name__ == "Card":
                calls.append("data-hook")

        def on_component_rendered(self, ctx):
            if type(ctx.component).__name__ == "Card":
                calls.append("rendered-hook")

        def on_component_cache_hit(self, ctx):
            calls.append(f"hit:{ctx.kind}:{ctx.frame_count}")

    app = Citry(extensions=[Probe])

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            calls.append("data")
            return {}

        def on_render(self):
            calls.append("render")

    render_prepared_direct(Card())
    render_prepared_direct(Card())

    assert calls == ["input", "data", "data-hook", "render", "rendered-hook", "input", "hit:component:1"]


def test_recovered_render_error_is_tainted_and_never_published() -> None:
    app = Citry()

    class Fallback(Component):
        citry = app
        template = "<p>fallback</p>"

    class Card(Component):
        citry = app
        template = "<p>unused</p>"

        class Cache:
            enabled = True

        def on_render(self):
            _result, error = yield 42
            assert isinstance(error, TypeError)
            return render_prepared_direct(Fallback())

    rendered = render_prepared_direct(Card())

    assert rendered.context._error_tainted
    assert app.cache.get(component_cache_key(Card, vary={})) is None


def test_backend_get_and_set_failures_propagate() -> None:
    class BrokenGet(InMemoryCache):
        def get(self, key):
            raise RuntimeError("get failed")

    class BrokenSet(InMemoryCache):
        def set(self, key, value, ttl=None):
            raise RuntimeError("set failed")

    for backend, message in ((BrokenGet(), "get failed"), (BrokenSet(), "set failed")):
        app = Citry(cache=backend)

        class Card(Component):
            citry = app
            template = "<p>card</p>"

            class Cache:
                enabled = True

        with pytest.raises(RuntimeError, match=message):
            render_prepared_direct(Card())


def test_cached_artifact_is_concurrently_reusable() -> None:
    app = Citry()

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

    render_prepared_direct(Card())
    with ThreadPoolExecutor(max_workers=8) as executor:
        renders = list(executor.map(lambda _index: render_prepared_direct(Card()), range(32)))
    ids = [render.frame.render_id for render in renders]
    assert len(ids) == len(set(ids))


def test_cached_artifact_does_not_retain_unregistered_class() -> None:
    app = Citry()

    def render_and_release():
        class Temporary(Component):
            citry = app
            template = "<p>temporary</p>"

            class Cache:
                enabled = True

        render_prepared_direct(Temporary())
        class_ref = weakref.ref(Temporary)
        app.unregister(Temporary)
        return class_ref

    class_ref = render_and_release()
    gc.collect()
    assert class_ref() is None


def test_corrupt_entry_is_a_miss_and_successful_render_replaces_it() -> None:
    app = Citry()

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

    key = component_cache_key(Card, vary={})
    app.cache.set(key, "not an artifact")
    render_prepared_direct(Card())

    assert json.loads(app.cache.get(key))["artifact_version"] == 1


def test_configured_entry_limit_skips_oversized_publication() -> None:
    app = Citry(extensions_defaults={"cache": {"max_entry_bytes": 100}})

    class Card(Component):
        citry = app
        template = f"<p>{'large' * 100}</p>"

        class Cache:
            enabled = True

    render_prepared_direct(Card())

    assert app.cache.get(component_cache_key(Card, vary={})) is None


def test_failing_hit_observer_is_isolated_from_later_observers() -> None:
    seen: list[str] = []

    class Failing(Extension):
        name = "failing_cache_observer"
        render_cache_mode = "stateless"
        render_cache_version = 1

        def on_component_cache_hit(self, ctx):
            seen.append("failing")
            raise RuntimeError("observer failure")

    class Later(Extension):
        name = "later_cache_observer"
        render_cache_mode = "stateless"
        render_cache_version = 1

        def on_component_cache_hit(self, ctx):
            seen.append("later")

    app = Citry(extensions=[Failing, Later])

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

    render_prepared_direct(Card())
    render_prepared_direct(Card())

    assert seen == ["failing", "later"]


def test_revision_change_during_finalize_skips_publication() -> None:
    class ResetRevision(Extension):
        name = "reset_cache_revision"
        render_cache_mode = "stateless"
        render_cache_version = 1

        def on_component_rendered(self, ctx):
            if type(ctx.component).__name__ == "Card":
                ctx.citry.extensions._advance_render_cache_revision()

    app = Citry(extensions=[ResetRevision])

    class Card(Component):
        citry = app
        template = "<p>card</p>"

        class Cache:
            enabled = True

    old_key = component_cache_key(Card, vary={})
    render_prepared_direct(Card())

    assert app.cache.get(old_key) is None


def test_server_state_cache_hit_mints_fresh_storage_key_without_rebuilding_state() -> None:
    app = Citry(secret="cache-state-test-secret")  # noqa: S106
    state_builds = 0

    class Card(Component):
        citry = app
        template = '<button @c-click="update">{{ value }}</button>'

        class Cache:
            enabled = True

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

        def template_data(self, kwargs, slots):
            return {"value": 5}

    first = render_prepared_direct(Card())
    second = render_prepared_direct(Card())
    first_entry = next(iter(first.context.extra[EVENTS_EXTRA_KEY]))
    second_entry = next(iter(second.context.extra[EVENTS_EXTRA_KEY]))

    assert state_builds == 1
    assert first_entry.state_token.startswith("ces1.")
    assert second_entry.state_token.startswith("ces1.")
    assert first_entry.state_token != second_entry.state_token
    assert app.cache.has(second_entry.state_token.removeprefix("ces1."))


def test_missing_server_state_rejects_replay_before_context_contribution() -> None:
    app = Citry(secret="cache-state-test-secret")  # noqa: S106
    state_builds = 0

    class Card(Component):
        citry = app

        class Cache:
            enabled = True

        class State:
            value: int = 5
            _storage = "server"

            def __post_init__(self):
                nonlocal state_builds
                state_builds += 1

        class Events:
            def update(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"value": 5}

        template = """
        <button @c-click="update">{{ value }}</button>
        """

    first = render_prepared_direct(Card())
    first_entry = next(iter(first.context.extra[EVENTS_EXTRA_KEY]))
    app.cache.delete(first_entry.state_token.removeprefix("ces1."))

    second = render_prepared_direct(Card())
    second_entries = tuple(second.context.extra[EVENTS_EXTRA_KEY])

    assert state_builds == 2
    assert len(second_entries) == 1
    assert second_entries[0].state_token != first_entry.state_token
    assert app.cache.has(second_entries[0].state_token.removeprefix("ces1."))


def test_inner_cache_hit_can_be_exported_by_an_outer_cache_miss() -> None:
    app = Citry()
    calls: list[str] = []

    class Child(Component):
        citry = app
        template = "<strong>child</strong>"

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            calls.append("child")
            return {}

    class Parent(Component):
        citry = app
        template = "<main><c-Child /></main>"

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return kwargs["variant"]

        def template_data(self, kwargs, slots):
            calls.append(f"parent:{kwargs['variant']}")
            return {}

    first = render_prepared_direct(Parent(variant="one"))
    second = render_prepared_direct(Parent(variant="two"))
    third = render_prepared_direct(Parent(variant="two"))
    tag_for_type = lambda value: "x-" + value.lower().replace("_", "-")  # noqa: E731

    for rendered in (first, second, third):
        assemble_typed_render(rendered, revision=0, tag_for_type=tag_for_type)

    assert calls == ["parent:one", "child", "parent:two"]
    assert len({first.frame.render_id, second.frame.render_id, third.frame.render_id}) == 3


def test_fragment_hit_does_not_invoke_its_supplied_body_again() -> None:
    app = Citry()
    calls: list[str] = []

    def body() -> str:
        calls.append("body")
        return "cached"

    class Page(Component):
        citry = app
        template = '<main><c-cache key="fragment">{{ body() }}</c-cache></main>'

        def template_data(self, kwargs, slots):
            return {"body": body}

    render_prepared_direct(Page())
    render_prepared_direct(Page())

    assert calls == ["body"]


def test_supplied_slot_hit_rebinds_to_current_parent_without_calling_fill() -> None:
    app = Citry()
    receiver_calls: list[str] = []

    class Receiver(Component):
        citry = app
        template = "<article><c-slot /></article>"

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "stable"

        def template_data(self, kwargs, slots):
            receiver_calls.append("data")
            return {}

    class Caller(Component):
        citry = app
        template = "<c-Receiver><b>fill</b></c-Receiver>"

    tag_for_type = lambda value: "x-" + value.lower().replace("_", "-")  # noqa: E731
    first = render_prepared_direct(Caller())
    second = render_prepared_direct(Caller())
    assemble_typed_render(first, revision=0, tag_for_type=tag_for_type)
    assemble_typed_render(second, revision=0, tag_for_type=tag_for_type)

    assert receiver_calls == ["data"]
    assert first.frame.render_id != second.frame.render_id


def test_two_supplied_slots_replay_as_separate_executions() -> None:
    app = Citry()
    receiver_calls: list[str] = []

    class Receiver(Component):
        citry = app

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "stable"

        class Slots:
            header: object
            body: object

        def template_data(self, kwargs, slots):
            receiver_calls.append("data")
            return {}

        template = """
        <article><c-slot name="header" /><c-slot name="body" /></article>
        """

    class Caller(Component):
        citry = app
        template = """
        <c-Receiver>
          <c-fill name="header"><b>head</b></c-fill>
          <c-fill name="body"><i>body</i></c-fill>
        </c-Receiver>
        """

    first = str(Caller())
    second = str(Caller())

    assert "<b>head</b>" in first
    assert "<i>body</i>" in first
    assert "<b>head</b>" in second
    assert "<i>body</i>" in second
    assert receiver_calls == ["data"]


def test_cached_inner_receiver_preserves_three_component_slot_forwarding() -> None:
    app = Citry(autodiscover=False)
    inner_calls: list[str] = []

    class Inner(Component):
        citry = app
        name = "inner"
        template = '<article><c-slot name="body" /></article>'

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "stable"

        def template_data(self, kwargs, slots):
            inner_calls.append("data")
            return {}

    class Wrapper(Component):
        citry = app
        name = "wrapper"
        template = '<c-inner #c-key="\'inner\'"><c-fill name="body"><c-slot name="body" /></c-fill></c-inner>'

    class Root(Component):
        citry = app
        template = (
            '<c-wrapper #c-key="\'wrapper\'"><c-fill name="body"><strong>{{ label }}</strong></c-fill></c-wrapper>'
        )

        def template_data(self, kwargs, slots):
            return {"label": "root lexical"}

    tag_for_type = lambda value: "x-" + value.lower().replace("_", "-")  # noqa: E731
    first = assemble_typed_render(render_prepared_direct(Root()), revision=0, tag_for_type=tag_for_type)
    second = assemble_typed_render(render_prepared_direct(Root()), revision=0, tag_for_type=tag_for_type)

    for assembly in (first, second):
        root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
        root_input = assembly.compile_inputs[root.definition_id]
        assert root.prepared_data["citryText0"] == "root lexical"
        wrapper_id = root.prepared_data["calls"][root_input.local_calls[0]["localId"]]["id"]
        wrapper = next(item for item in assembly.view.occurrences if item.id == wrapper_id)
        wrapper_template = assembly.compile_inputs[wrapper.definition_id].template
        root_sites = set(__import__("re").findall(r"v-slot:\['(citrySlot[^']+)'\]", root_input.template))
        forwarded_sites = set(__import__("re").findall(r'<slot name="(citrySlot[^"]+)"', wrapper_template))
        assert root_sites & forwarded_sites

    assert inner_calls == ["data"]


def test_i18n_cache_hit_rebinds_typed_binding_marker_to_fresh_occurrence() -> None:
    app = Citry(extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US", "cs-CZ")}})
    calls: list[str] = []

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True" tag="main"><span $c-tr:loading>{{ tr("loading") }}</span></c-i18n>'
        messages = "loading = Loading"

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            calls.append("data")
            return {}

    markers: list[str] = []
    operands: list[str] = []
    for rendered in (render_prepared_direct(Page()), render_prepared_direct(Page())):
        pending = [rendered]
        while pending:
            value = pending.pop()
            if hasattr(value, "parts"):
                pending.extend(value.parts)
            if isinstance(value, PreparedElementOpen):
                markers.extend(
                    attr.value
                    for attr in value.attrs
                    if attr.name == "data-citry-i18n-binding" and isinstance(attr.value, str)
                )
            if isinstance(value, PreparedTextValue) and value.browser_binding is not None:
                operands.append(value.browser_binding.operand)

    assert calls == ["data"]
    assert len(markers) == 2
    assert markers[0] != markers[1]
    assert operands == markers


def test_prepared_browser_bindings_round_trip_with_data_and_provenance() -> None:
    assert is_authenticated_browser_binding(
        prepared_browser_binding(helper="$probe_helper", operand="valid", target="text")
    )
    with pytest.raises(ValueError, match="reserved template-context name"):
        prepared_browser_binding(helper="$probe-helper", operand="bad", target="text")
    with pytest.raises(ValueError, match="target is invalid"):
        prepared_browser_binding(helper="$probe", operand="bad", target="evil")  # type: ignore[arg-type]
    forged = PreparedBrowserBinding("$probe", "bad", "text")
    with pytest.raises(_UnsupportedTypedCachePart, match="not producer-authenticated"):
        _export_typed_leaf(PreparedTextValue("{{ x }}", (0, 7), "x", browser_binding=forged))
    forged_attribute = PreparedBrowserBinding("$probe", "bad", "attribute", "title")
    with pytest.raises(_UnsupportedTypedCachePart, match="not producer-authenticated"):
        _export_typed_leaf(
            PreparedElementOpen(
                "<p>",
                (0, 3),
                "p",
                (),
                is_void=False,
                is_self_closing=False,
                element_metadata=(),
                browser_bindings=(forged_attribute,),
            )
        )
    attribute = prepared_browser_binding(
        helper="$probe",
        operand={"id": "binding-1", "literal": "{{ value }} <b>"},
        target="attribute",
        name="title",
        values_expression="state.value",
    )
    text = prepared_browser_binding(helper="$probe", operand="binding-2", target="text")
    opening = PreparedElementOpen(
        "<p>",
        (0, 3),
        "p",
        (),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
        browser_bindings=(attribute,),
    )
    value = PreparedTextValue("{{ value }}", (0, 11), 'quoted " text', browser_binding=text)

    replayed_opening = _replay_typed_leaf(_export_typed_leaf(opening))
    replayed_value = _replay_typed_leaf(_export_typed_leaf(value))

    assert replayed_opening.browser_bindings[0].operand == attribute.operand
    assert replayed_value.browser_binding is not None
    assert replayed_value.browser_binding.operand == "binding-2"
    assert is_authenticated_browser_binding(replayed_opening.browser_bindings[0])
    assert is_authenticated_browser_binding(replayed_value.browser_binding)

    mixed = PreparedElementOpen(
        '<input v-model="query" c-bind="attrs">',
        (0, 42),
        "input",
        (
            PreparedAttribute("v-model", "source", (7, 22), 'v-model="query"'),
            PreparedAttribute("title", "data", (23, 37), "server"),
        ),
        is_void=True,
        is_self_closing=False,
        element_metadata=(),
    )
    replayed_mixed = _replay_typed_leaf(_export_typed_leaf(mixed))
    assert replayed_mixed.attrs == mixed.attrs

    control = {
        "id": "citryControl1a",
        "field": "query",
        "binding_mode": "two-way",
        "handler": "refresh",
        "lazy": False,
        "on": None,
        "key": None,
        "debounce": 25,
        "throttle": None,
    }
    controlled = PreparedElementOpen(
        '<input c-bind="attrs">',
        (0, 22),
        "input",
        (),
        is_void=True,
        is_self_closing=False,
        element_metadata=(),
        control_bindings=(control,),
    )
    replayed_controlled = _replay_typed_leaf(_export_typed_leaf(controlled))
    assert dict(replayed_controlled.control_bindings[0]) == control


def test_polling_prepared_element_uses_live_render_until_cache_schema_supports_it() -> None:
    opening = PreparedElementOpen(
        '<output @c-poll.5s="refresh">',
        (0, 35),
        "output",
        (),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
        poll_bindings=({"id": "citryPoll8", "handler": "refresh", "args": None, "interval": 5000},),
    )
    with pytest.raises(_UnsupportedTypedCachePart, match=r"polling bindings.*artifact version 1"):
        _export_typed_leaf(opening)
