from __future__ import annotations

import hashlib

import pytest

from citry import Citry, Component
from citry._vue import events as vue_events
from citry._vue.capture import render_prepared_direct
from citry._vue.compiler import NativeCompiler
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.events import (
    DirectVueEventsProducer,
    default_events_producer,
    definition_bundle,
    native_compile_view,
    style_asset,
)
from citry._vue.serialization import _component_tags_for_manifest, _prepare_initial_result
from citry.browser_render import BrowserPluginDescriptor, BrowserRenderContribution
from citry.component import ComponentMeta
from citry.ext.dependencies.types import Script, Style
from citry.ext.events import actions
from citry.ext.events.emission import EXTRA_KEY, EventInstanceEntry
from citry.ext.events.renderers import VuePreparedRenderEncoder, dispatcher_for
from citry.ext.events.results import RenderEncodingContext
from citry.extension import Extension
from citry.serialize import _can_defer_vue_body_children
from citry.slots import Slot


def test_default_producer_reuses_ordinary_component_metadata_per_preparation(monkeypatch) -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Root(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Child #c-key="value" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"values": ["a", "b", "c"]}

    calls: list[str] = []
    original = vue_events._format_default_component_tag

    def counted(type_key, component):
        calls.append(type_key)
        return original(type_key, component)

    monkeypatch.setattr(vue_events, "_format_default_component_tag", counted)
    producer = default_events_producer(registry)
    result = producer._prepare_from_render_result(
        render_prepared_direct(Root()), citry=registry, app_id="metadata", revision=0
    )
    tags = result.tags
    assert tags is not None
    assert set(tags) == {Root.class_id, Child.class_id}
    assert calls.count(Root.class_id) == 2
    assert calls.count(Child.class_id) == 2


def test_default_producer_rejects_name_change_during_preparation() -> None:
    registry = Citry(autodiscover=False)

    class Root(Component):
        citry = registry
        template = "<p>root</p>"

    producer = default_events_producer(registry)
    compile_view = producer._compile_view

    def mutate_name(assembly):
        compiled = compile_view(assembly)
        Root.__name__ = "ChangedRoot"
        return compiled

    producer._compile_view = mutate_name
    try:
        with pytest.raises(ValueError, match="registry metadata changed during Vue preparation"):
            producer.prepare_from_render(render_prepared_direct(Root()), citry=registry, app_id="metadata", revision=0)
    finally:
        Root.__name__ = "Root"
        producer._compile_view = compile_view


def test_default_producer_validates_metadata_after_bundle_publication() -> None:
    registry = Citry(autodiscover=False)

    class Root(Component):
        citry = registry
        template = "<p>root</p>"

    producer = default_events_producer(registry)
    publish_bundle = producer._publish_bundle

    def mutate_name(digest, content):
        publish_bundle(digest, content)
        Root.__name__ = "ChangedAfterPublish"

    producer._publish_bundle = mutate_name
    try:
        with pytest.raises(ValueError, match="registry metadata changed during Vue preparation"):
            producer.prepare_from_render(render_prepared_direct(Root()), citry=registry, app_id="metadata", revision=0)
    finally:
        Root.__name__ = "Root"
        producer._publish_bundle = publish_bundle


def test_default_producer_rejects_mapper_override_during_compilation() -> None:
    registry = Citry(autodiscover=False)

    class Root(Component):
        citry = registry
        template = "<p>root</p>"

    producer = default_events_producer(registry)
    compile_view = producer._compile_view

    def replace_mapper(assembly):
        compiled = compile_view(assembly)
        producer.component_tag = lambda _type_key: "x-replaced"
        return compiled

    producer._compile_view = replace_mapper
    try:
        with pytest.raises(ValueError, match="metadata configuration changed during preparation"):
            producer.prepare_from_render(render_prepared_direct(Root()), citry=registry, app_id="metadata", revision=0)
    finally:
        del producer.component_tag
        producer._compile_view = compile_view


def test_default_producer_rejects_paired_mapper_replacement_during_compilation() -> None:
    registry = Citry(autodiscover=False)

    class Root(Component):
        citry = registry
        template = "<p>root</p>"

    producer = default_events_producer(registry)
    compile_view = producer._compile_view
    original_tag = producer._tag_for_type
    original_builtin_tag = producer._builtin_tag_callback

    def replace_mapper_pair(assembly):
        compiled = compile_view(assembly)

        def replacement(_type_key):
            return "x-replaced"

        producer._tag_for_type = replacement
        producer._builtin_tag_callback = replacement
        return compiled

    producer._compile_view = replace_mapper_pair
    try:
        with pytest.raises(ValueError, match="metadata configuration changed during preparation"):
            producer.prepare_from_render(render_prepared_direct(Root()), citry=registry, app_id="metadata", revision=0)
    finally:
        producer._tag_for_type = original_tag
        producer._builtin_tag_callback = original_builtin_tag
        producer._compile_view = compile_view


def test_default_producer_rejects_render_from_replaced_registered_class() -> None:
    registry = Citry(autodiscover=False)

    class Root(Component):
        citry = registry
        template = "<p>old</p>"

    rendered = render_prepared_direct(Root())
    old_class_id = Root.class_id

    class Replacement(Component):
        citry = registry
        template = "<p>new</p>"

    type.__setattr__(Replacement, "_class_id", old_class_id)
    registry._classes_by_id[old_class_id] = Replacement
    producer = default_events_producer(registry)
    with pytest.raises(ValueError, match="component class changed before Vue metadata preparation"):
        producer.prepare_from_render(rendered, citry=registry, app_id="metadata", revision=0)


def test_default_producer_second_preparation_observes_new_component_name() -> None:
    registry = Citry(autodiscover=False)

    class Root(Component):
        citry = registry
        template = "<p>root</p>"

    producer = default_events_producer(registry)
    first_result = producer._prepare_from_render_result(
        render_prepared_direct(Root()), citry=registry, app_id="first", revision=0
    )
    Root.__name__ = "RenamedRoot"
    try:
        second_result = producer._prepare_from_render_result(
            render_prepared_direct(Root()), citry=registry, app_id="second", revision=0
        )
    finally:
        Root.__name__ = "Root"
    first_tags = first_result.tags
    second_tags = second_result.tags
    assert first_tags is not None
    assert second_tags is not None
    assert first_tags[Root.class_id] != second_tags[Root.class_id]


def test_default_producer_keeps_custom_metaclass_tag_path_uncached(monkeypatch) -> None:
    registry = Citry(autodiscover=False)

    class CustomMeta(ComponentMeta):
        pass

    class Root(Component, metaclass=CustomMeta):
        citry = registry
        template = "<p>root</p>"

    calls: list[str] = []
    original = vue_events._format_default_component_tag

    def counted(type_key, component):
        calls.append(type_key)
        return original(type_key, component)

    monkeypatch.setattr(vue_events, "_format_default_component_tag", counted)
    producer = default_events_producer(registry)
    result = producer._prepare_from_render_result(
        render_prepared_direct(Root()), citry=registry, app_id="metadata", revision=0
    )
    tags = result.tags
    assert tags == {}
    assert calls == [Root.class_id]


def test_default_producer_falls_back_for_overridden_engine_lookup() -> None:
    class CustomCitry(Citry):
        lookup_calls = 0

        def get_component_by_class_id(self, class_id):
            self.lookup_calls += 1
            return super().get_component_by_class_id(class_id)

    registry = CustomCitry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Root(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Child #c-key="value" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"values": ["a", "b"]}

    producer = default_events_producer(registry)
    registry.lookup_calls = 0
    result = producer._prepare_from_render_result(
        render_prepared_direct(Root()), citry=registry, app_id="metadata", revision=0
    )
    assert result.tags is None
    assert registry.lookup_calls >= 7


def test_initial_tag_collection_preserves_repeated_custom_callback_calls() -> None:
    calls: list[str] = []

    class Producer:
        def component_tag(self, type_key):
            calls.append(type_key)
            return f"x-{type_key.lower()}-{len(calls)}"

    tags = _component_tags_for_manifest(
        Producer(),
        {"occurrences": [{"typeKey": "A"}, {"typeKey": "A"}, {"typeKey": "B"}]},
        {},
    )
    assert calls == ["A", "A", "B"]
    assert tags == {"A": "x-a-2", "B": "x-b-3"}


def test_custom_tag_collection_cannot_stale_cached_ordinary_metadata(monkeypatch) -> None:
    registry = Citry(autodiscover=False)

    class CustomMeta(ComponentMeta):
        pass

    class Custom(Component, metaclass=CustomMeta):
        citry = registry
        template = "<i>custom</i>"

    class Root(Component):
        citry = registry
        template = "<c-Custom />"

    mutate = False
    original = vue_events._format_default_component_tag

    def mutating(type_key, component):
        if mutate and component is Custom:
            Root.__name__ = "ChangedByCustomMapper"
        return original(type_key, component)

    monkeypatch.setattr(vue_events, "_format_default_component_tag", mutating)
    producer = default_events_producer(registry)
    result = producer._prepare_from_render_result(
        render_prepared_direct(Root()), citry=registry, app_id="metadata", revision=0
    )
    mutate = True
    try:
        _component_tags_for_manifest(producer, result.payload, result.tags)
        with pytest.raises(ValueError, match="registry metadata changed during Vue preparation"):
            result.validate()
    finally:
        Root.__name__ = "Root"


def test_initial_preparation_honors_instance_override() -> None:
    class Producer:
        def prepare_from_render(self, render, **kwargs):
            return {"source": "class"}

        def _prepare_from_render_result(self, render, **kwargs):
            raise AssertionError("private built-in preparation path was used")

    producer = Producer()

    def instance_prepare(_render, **_kwargs):
        return {"source": "instance"}

    producer.prepare_from_render = instance_prepare
    manifest, tags, validate = _prepare_initial_result(producer, object(), object(), "app")
    assert manifest == {"source": "instance"}
    assert tags is None
    validate()


def test_direct_events_producer_uses_selected_credentials_and_one_bundle() -> None:
    registry = Citry(
        secret="vue-events-producer-test-secret",  # noqa: S106
        autodiscover=False,
    )
    registry.set_mounted_prefix("/citry")

    class Board(Component):
        citry = registry
        template = '<button @c-click="save">{{ label }}</button>'

        class Events:
            def save(self):
                return None

        def template_data(self, kwargs, slots):
            return {"label": "Save"}

    published: dict[str, bytes] = {}

    producer = DirectVueEventsProducer(
        tag_for_type=lambda _value: "citry-board-root",
        compile_view=native_compile_view(NativeCompiler()),
        request_scope=lambda _element, _context: ("board", 1, 0, initial["rootId"]),
        publish_bundle=published.__setitem__,
    )
    info = registry.extensions.get_extension("events").resolve(Board)
    initial = producer.prepare_from_render(render_prepared_direct(Board()), citry=registry, app_id="board", revision=0)
    assert "baseRevision" not in initial
    context = RenderEncodingContext(registry, None, next(iter(info.handlers.values())), "http", "vue-prepared/1")
    encoded = VuePreparedRenderEncoder(producer).encode(actions.Render(Board()), "render:old", context)
    payload = encoded["prepared"]
    assert encoded["renderer"] == "vue-prepared/1"
    assert encoded["target"] == "render:old"

    root = next(item for item in payload["occurrences"] if item["id"] == payload["rootId"])
    event_context = root["eventContext"]
    assert set(event_context) == {
        "serverRenderId",
        "stateToken",
        "publicState",
        "componentClassId",
        "descriptor",
    }
    assert event_context["serverRenderId"]
    assert event_context["descriptor"]["eventHandlers"]["save"]["httpMethod"] == "POST"
    assert len(published) == 1
    digest, javascript = next(iter(published.items()))
    assert payload["definitions"][0]["url"] == f"/definitions/{digest}.js"
    assert b"CitryStableDefinitions" in javascript

    prepared_render = render_prepared_direct(Board())
    encoded_render = VuePreparedRenderEncoder(producer).encode(actions.Render(prepared_render), "render:old", context)
    assert encoded_render["prepared"]["rootId"] == initial["rootId"]


def test_direct_events_producer_supports_zero_and_nested_event_owners() -> None:
    registry = Citry(secret="vue-events-owner-test-secret", autodiscover=False)  # noqa: S106

    class Passive(Component):
        citry = registry
        template = "<p>passive</p>"

    class Child(Component):
        citry = registry
        template = "<span>child</span>"

        class Events:
            def ping(self):
                return None

    registry.register(Child)

    class Parent(Component):
        citry = registry
        template = "<main><c-child /></main>"

        class Events:
            def ping(self):
                return None

    registry.register(Parent)
    producer = DirectVueEventsProducer(
        tag_for_type=lambda value: f"citry-{value.lower().replace('_', '-')}",
        compile_view=native_compile_view(NativeCompiler()),
        request_scope=lambda _element, _context: ("page", 1, 0, "citryOccurrenceRoot"),
        publish_bundle=lambda _digest, _content: None,
    )

    passive = producer.prepare_from_render(
        render_prepared_direct(Passive()), citry=registry, app_id="passive", revision=0
    )
    assert all(type(item["renderId"]) is str and item["renderId"] for item in passive["occurrences"])
    assert all("eventContext" not in item for item in passive["occurrences"])

    nested = producer.prepare_from_render(
        render_prepared_direct(Parent()), citry=registry, app_id="nested", revision=0
    )
    contexts = [item["eventContext"] for item in nested["occurrences"] if "eventContext" in item]
    assert len(contexts) == 2
    assert {item["componentClassId"] for item in contexts} == {Parent.class_id, Child.class_id}
    assert all(
        item.get("eventContext", {}).get("serverRenderId") == item["renderId"] for item in nested["occurrences"]
    )
    child_id = next(item["id"] for item in nested["occurrences"] if item["typeKey"] == Child.class_id)
    anchored = producer.prepare_from_render(
        render_prepared_direct(Child()),
        citry=registry,
        app_id="nested",
        revision=1,
        base_revision=0,
        root_occurrence_id=child_id,
    )
    assert anchored["rootId"] == child_id
    assert anchored["baseRevision"] == 0


def test_direct_events_producer_addresses_selected_transparent_root_without_event_context() -> None:
    registry = Citry(autodiscover=False)

    class Transparent(Component):
        citry = registry
        transparent = True
        template = "<p>transparent</p>"

    payload = default_events_producer(registry).prepare_from_render(
        render_prepared_direct(Transparent()), citry=registry, app_id="transparent", revision=0
    )
    [root] = payload["occurrences"]

    assert root["id"] == payload["rootId"]
    assert root["renderId"]
    assert "eventContext" not in root


def test_direct_events_producer_rejects_selected_transparent_render_alias_context() -> None:
    registry = Citry(secret="vue-events-alias-test-secret", autodiscover=False)  # noqa: S106

    class Transparent(Component):
        citry = registry
        transparent = True
        template = "<em>transparent</em>"

    class Root(Component):
        citry = registry
        template = "<main>{{ child }}</main>"

        class Events:
            def ping(self):
                return None

        def template_data(self, kwargs, slots):
            return {"child": Transparent()}

    rendered = render_prepared_direct(Root())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda value: f"citry-{value.lower().replace('_', '-')}",
    )
    aliases = set(assembly.render_to_occurrence) - set(assembly.occurrence_to_render.values())
    [alias] = aliases
    rendered.context.extra[EXTRA_KEY] = {EventInstanceEntry(alias, Root.class_id, None, "{}"): None}

    with pytest.raises(ValueError, match="Events instance does not match its canonical prepared occurrence render ID"):
        default_events_producer(registry).prepare_from_render(rendered, citry=registry, app_id="alias", revision=0)


def test_direct_events_producer_rejects_forged_transparent_events_manifest(monkeypatch) -> None:
    registry = Citry(autodiscover=False)

    class Transparent(Component):
        citry = registry
        transparent = True
        template = "<p>transparent</p>"

    rendered = render_prepared_direct(Transparent())
    render_id = rendered.frame.render_id

    def forged(*_args, **_kwargs):
        return {
            "componentInstances": [
                {
                    "renderId": render_id,
                    "componentClassId": Transparent.class_id,
                    "stateToken": None,
                    "publicState": {},
                }
            ],
            "componentClasses": [{"componentClassId": Transparent.class_id, "eventHandlers": {}}],
        }

    monkeypatch.setattr(vue_events, "build_events_manifest", forged)
    with pytest.raises(ValueError, match="component type without an Events declaration"):
        default_events_producer(registry).prepare_from_render(rendered, citry=registry, app_id="forged", revision=0)


@pytest.mark.parametrize(
    ("corrupt", "message"),
    [
        (
            lambda manifest: manifest["componentInstances"].append(dict(manifest["componentInstances"][0])),
            "multiple Events instances matched one prepared occurrence",
        ),
        (
            lambda manifest: manifest["componentInstances"][0].__setitem__("componentClassId", "wrong"),
            "Events instance class does not match its prepared occurrence type",
        ),
    ],
)
def test_direct_events_producer_rejects_malformed_occurrence_context_attachment(monkeypatch, corrupt, message) -> None:
    registry = Citry(secret="vue-events-address-test-secret", autodiscover=False)  # noqa: S106

    class Root(Component):
        citry = registry
        template = '<button @c-click="ping">ping</button>'

        class Events:
            def ping(self):
                return None

    original = vue_events.build_events_manifest

    def malformed(*args, **kwargs):
        manifest = original(*args, **kwargs)
        corrupt(manifest)
        return manifest

    monkeypatch.setattr(vue_events, "build_events_manifest", malformed)
    with pytest.raises(ValueError, match=message):
        default_events_producer(registry).prepare_from_render(
            render_prepared_direct(Root()), citry=registry, app_id="malformed", revision=0
        )


def test_direct_events_producer_preserves_object_prototype_handler_names() -> None:
    registry = Citry(secret="vue-events-handler-name-test-secret", autodiscover=False)  # noqa: S106

    class App(Component):
        citry = registry
        template = "<p>handlers</p>"

        class Events:
            def constructor(self):
                return None

            def toString(self):  # noqa: N802
                return None

    producer = DirectVueEventsProducer(
        tag_for_type=lambda _value: "citry-handler-root",
        compile_view=native_compile_view(NativeCompiler()),
        request_scope=lambda _element, _context: ("handlers", 1, 0, "citryOccurrenceRoot"),
        publish_bundle=lambda _digest, _content: None,
    )
    manifest = producer.prepare_from_render(
        render_prepared_direct(App()), citry=registry, app_id="handlers", revision=0
    )
    root = next(item for item in manifest["occurrences"] if item["id"] == manifest["rootId"])
    assert set(root["eventContext"]["descriptor"]["eventHandlers"]) == {"constructor", "toString"}


def test_default_events_renderer_bootstraps_selected_render_without_rendering_twice() -> None:
    registry = Citry(secret="vue-events-default-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class App(Component):
        citry = registry
        template = '<button @c-click="save">{{ label }}</button>'

        class Events:
            def save(self):
                return None

        def template_data(self, kwargs, slots):
            return {"label": "Save"}

    dispatcher_for(registry)
    rendered = App().render()
    assert rendered.render_target == "prepared"
    html = rendered.serialize()
    assert 'id="citry-vue-' in html
    assert "></div>" in html
    assert "CitryStable.startPrepared" in html
    assert '"endpoint":"/citry/ext/events/call"' in html
    assert '"eventBaseUrl":"/citry/ext/events/e/"' in html
    assert 'src="/citry/citry.js"' in html


def test_mounted_renderer_without_initial_events_keeps_lazy_events_endpoint_available() -> None:
    registry = Citry(secret="vue-events-lazy-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class App(Component):
        citry = registry
        template = '<button :disabled="False">Ready</button>'

    html = App().render().serialize()
    assert '"endpoint":"/citry/ext/events/call"' in html
    assert '"eventBaseUrl":"/citry/ext/events/e/"' in html
    assert html.count('src="/citry/citry.js"') == 1


def test_unconfigured_engine_keeps_static_serialization() -> None:
    registry = Citry(autodiscover=False)

    class Static(Component):
        citry = registry
        template = "<p>plain</p>"

    rendered = Static().render()
    assert rendered.render_target == "prepared"
    html = rendered.serialize()
    assert html.startswith("<p ")
    assert html.endswith(">plain</p>")
    assert "CitryStable" not in html


def test_vue_document_preserves_physical_shell_and_replaces_logical_body() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = (
            '<!doctype html><html lang="en"><head><title>Example</title></head>'
            '<body class="page"><button id="dynamic" :title="\'ready\'">ready</button></body></html>'
        )

    html = Page().render().serialize()
    assert html.startswith("<!doctype html><html ")
    assert 'lang="en"' in html.split("<head>", 1)[0]
    assert "data-cid-" in html.split("<head>", 1)[0]
    assert '<head><title>Example</title></head><body class="page">' in html
    assert '<div id="citry-vue-' in html
    assert '<button id="dynamic"' not in html
    assert "CitryStable.startPrepared" in html
    assert "</body></html>" in html


def test_vue_document_append_dependencies_execute_before_bootstrap() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = "<!doctype html><html><head></head><body><button :title=\"'ready'\">ready</button></body></html>"

    html = Page().render().serialize(deps_position="append")
    assert html.index("Citry interactive runtime") < html.index("CitryStable.startPrepared")
    assert html.count('id="citry-vue-') == 1


def test_vue_document_javascript_omit_keeps_static_body() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = (
            '<!doctype html><html><head></head><body><button id="kept" :title="\'ready\'">ready</button></body></html>'
        )

    html = Page().render().serialize(security_javascript="omit")
    assert '<button id="kept"' in html
    assert "CitryStable.startPrepared" not in html
    assert 'id="citry-vue-' not in html


def test_vue_document_rejects_binding_in_physical_head_of_mixed_root() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = (
            "<!doctype html><html><head><title :class=\"'active'\">Example</title></head>"
            "<body><button :title=\"'ready'\">ready</button></body></html>"
        )

    with pytest.raises(ValueError, match="physical document head"):
        Page().render().serialize()


def test_vue_document_does_not_defer_a_component_in_the_physical_head() -> None:
    registry = Citry(autodiscover=False)

    class HeadContent(Component):
        citry = registry
        template = "<title>Selected child title</title>"

    class Page(Component):
        citry = registry
        template = (
            "<!doctype html><html><head><c-HeadContent /></head>"
            "<body><button :title=\"'ready'\">ready</button></body></html>"
        )

    html = Page().render().serialize()
    assert "<title" in html
    assert "Selected child title</title>" in html
    assert "CitryStable.startPrepared" in html


def test_vue_document_allows_dependency_placeholders_around_prepared_body() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = (
            "<!doctype html><html><head><c-css /></head>"
            "<body><button :title=\"'ready'\">ready</button><c-js /></body></html>"
        )

    html = Page().render().serialize()
    assert "CitryStable.startPrepared" in html
    assert html.count('id="citry-vue-') == 1


def test_vue_document_rejects_head_only_js_data_before_prepared_assembly() -> None:
    registry = Citry(autodiscover=False)

    class HeadData(Component):
        citry = registry
        template = "<meta name=head-data>"

        def js_data(self, kwargs, slots):
            return {"active": True}

    class Page(Component):
        citry = registry
        template = (
            "<!doctype html><html><head><c-HeadData /></head>"
            "<body><button :title=\"'ready'\">ready</button></body></html>"
        )

    with pytest.raises(ValueError, match=r"js_data.*physical document head"):
        Page().render().serialize()


def test_vue_document_rejects_head_only_component_javascript_before_prepared_assembly() -> None:
    registry = Citry(autodiscover=False)

    class HeadScript(Component):
        citry = registry
        template = "<meta name=head-script>"
        js = "$component({created(){}});"

    class Page(Component):
        citry = registry
        template = (
            "<!doctype html><html><head><c-HeadScript /></head>"
            "<body><button :title=\"'ready'\">ready</button></body></html>"
        )

    with pytest.raises(ValueError, match=r"Component JavaScript.*physical document head"):
        Page().render().serialize()


def test_vue_body_deferral_is_limited_to_the_builtin_default_document_contract() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "<p>body child</p>"

    class Page(Component):
        citry = registry
        template = (
            "<!doctype html><html><head></head><body>"
            "<c-Child /><button :title=\"'ready'\">ready</button></body></html>"
        )

    rendered = Page().render()

    def eligible(candidate=rendered, **overrides):
        options = {
            "deps_strategy": "document",
            "deps_position": "smart",
            "security_csp": "off",
            "security_javascript": "allow",
            "security_script_integrity": "off",
            "csp_nonce": None,
            **overrides,
        }
        return _can_defer_vue_body_children(candidate, **options)

    assert eligible()
    assert not eligible(deps_position="append")
    assert not eligible(security_csp="warn")
    assert not eligible(security_javascript="warn")
    assert not eligible(security_script_integrity="citry")
    assert not eligible(csp_nonce="bm9uY2U")

    class PlaceholderPage(Component):
        citry = registry
        template = (
            "<!doctype html><html><head><c-css /></head>"
            "<body><c-Child /><button :title=\"'ready'\">ready</button><c-js /></body></html>"
        )

    assert not eligible(PlaceholderPage().render())

    class CssChild(Component):
        citry = registry
        template = "<p>styled child</p>"
        css = "p { color: var(--accent); }"

        def css_data(self, kwargs, slots):
            return {"accent": "red"}

    class CssPage(Component):
        citry = registry
        template = (
            "<!doctype html><html><head></head><body>"
            "<c-CssChild /><button :title=\"'ready'\">ready</button></body></html>"
        )

    assert not eligible(CssPage().render())

    class SafeLeaf(Component):
        citry = registry
        template = "<p>{{ label }}</p>"

        def template_data(self, kwargs, slots):
            return {"label": "safe leaf"}

    class SafeLeafPage(Component):
        citry = registry
        template = (
            "<!doctype html><html><head></head><body>"
            "<c-SafeLeaf /><button :title=\"'ready'\">ready</button></body></html>"
        )

    assert eligible(SafeLeafPage().render())

    class NestedDocumentLeaf(Component):
        citry = registry
        template = "<html><head></head><body>{{ label }}</body></html>"

        def template_data(self, kwargs, slots):
            return {"label": "nested"}

    class NestedDocumentPage(Component):
        citry = registry
        template = (
            "<!doctype html><html><head></head><body>"
            "<c-NestedDocumentLeaf /><button :title=\"'ready'\">ready</button></body></html>"
        )

    assert not eligible(NestedDocumentPage().render())


def test_vue_document_hook_cannot_remove_mount_host() -> None:
    class RemoveHost(Extension):
        name = "remove_host"

        def on_serialize(self, ctx):
            return ctx.html.replace('<div id="citry-vue-', '<div data-removed="true" id="citry-vue-')

    registry = Citry(autodiscover=False, extensions=[RemoveHost])

    class Page(Component):
        citry = registry
        template = "<!doctype html><html><head></head><body><button :title=\"'ready'\">ready</button></body></html>"

    with pytest.raises(ValueError, match="preserve exactly one empty Citry mount host"):
        Page().render().serialize()


def test_same_compiled_slots_render_static_then_prepared() -> None:
    registry = Citry(secret="vue-target-switch-test-secret", autodiscover=False)  # noqa: S106

    class Receiver(Component):
        citry = registry
        template = '<article><c-slot name="body">fallback</c-slot></article>'

    class App(Component):
        citry = registry
        template = '<main><c-receiver><c-fill name="body">supplied</c-fill></c-receiver></main>'

    static = App().render()
    assert static.render_target == "prepared"
    assert "supplied" in static.serialize()

    registry.set_mounted_prefix("/citry")
    dispatcher_for(registry)
    prepared = App().render()
    assert prepared.render_target == "prepared"
    html = prepared.serialize()
    assert "supplied" in html
    assert "CitryStable.startPrepared" not in html


def test_default_events_producer_publishes_engine_owned_route_asset() -> None:
    registry = Citry(secret="vue-default-producer-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class Root(Component):
        citry = registry
        template = "<main>root</main>"

    payload = default_events_producer(registry).prepare_from_render(
        render_prepared_direct(Root()), citry=registry, app_id="app", revision=0
    )
    asset = payload["definitions"][0]
    assert asset["url"] == f"/citry/ext/events/definitions/{asset['sha256']}.js"
    assert definition_bundle(registry, asset["sha256"]) is not None


def test_default_events_producer_retains_selected_css_variables_stylesheet() -> None:
    registry = Citry(secret="vue-css-vars-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class Root(Component):
        citry = registry
        template = '<main :data-ready="true">root</main>'
        css = "main { color: var(--accent); }"

        def css_data(self, kwargs, slots):
            return {"accent": "teal"}

    payload = default_events_producer(registry).prepare_from_render(
        render_prepared_direct(Root()), citry=registry, app_id="app", revision=0
    )
    styles = payload["styles"]
    assert len(styles) == 2
    variables = next(item for item in styles if b"--accent" in style_asset(registry, item["source"]["sha256"]))
    assert variables["owner"]["typeKey"] == Root.class_id
    assert variables["source"]["url"].endswith(".css")
    assert len(variables["source"]["sha256"]) == 64
    assert variables["owner"]["occurrenceIds"] == [payload["rootId"]]
    assert all(item["owner"]["occurrenceIds"] == [payload["rootId"]] for item in styles)


def test_extension_assets_use_app_lifetime_owner_and_exact_sources() -> None:
    integrity = "sha384-" + "A" * 64

    class Assets(Extension):
        name = "assets"

        def browser_plugin(self):
            return BrowserPluginDescriptor(1, Script(content="window.plugin=true"))

        def prepare_browser_render(self, ctx):
            return BrowserRenderContribution(
                1,
                {},
                scripts=(
                    Script(url="https://cdn.test/app.js", attrs={"integrity": integrity, "crossorigin": "anonymous"}),
                ),
                styles=(Style(content=".asset{color:red}"),),
            )

    registry = Citry(autodiscover=False, extensions=[Assets])
    registry.set_mounted_prefix("/citry")

    class Root(Component):
        citry = registry
        template = '<main :data-ready="true">root</main>'

    payload = default_events_producer(registry).prepare_from_render(
        render_prepared_direct(Root()), citry=registry, app_id="app", revision=0
    )
    script = payload["scripts"][0]
    assert script["owner"] == {"kind": "extension", "extensionName": "assets"}
    assert script["source"] == {
        "kind": "external",
        "url": "https://cdn.test/app.js",
        "attrs": {"integrity": integrity, "crossorigin": "anonymous"},
    }
    style = payload["styles"][0]
    assert style["owner"] == {"kind": "extension", "extensionName": "assets"}
    assert style["source"]["kind"] == "owned"
    assert len(style["source"]["sha256"]) == 64


def test_default_events_producer_groups_shared_stylesheet_occurrence_references() -> None:
    registry = Citry(secret="vue-css-shared-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class Styled(Component):
        citry = registry
        template = '<span style="color:var(--accent)">styled</span>'
        css = ".unused { color: var(--accent); }"

        def css_data(self, kwargs, slots):
            return {"accent": kwargs["color"]}

    class Root(Component):
        citry = registry
        template = '<c-Styled color="red" #c-key="\'a\'" /><c-Styled color="red" #c-key="\'b\'" />'

    payload = default_events_producer(registry).prepare_from_render(
        render_prepared_direct(Root()), citry=registry, app_id="app", revision=0
    )
    styled_ids = sorted(item["id"] for item in payload["occurrences"] if item["typeKey"] == Styled.class_id)
    variables = next(
        item for item in payload["styles"] if b"--accent" in style_asset(registry, item["source"]["sha256"])
    )
    assert variables["owner"]["occurrenceIds"] == styled_ids


def test_prepared_vue_merges_identical_component_css_without_legacy_markers() -> None:
    registry = Citry(secret="vue-css-component-shared-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")
    shared_css = ".shared-component-style { color: currentColor; }"

    class First(Component):
        citry = registry
        template = "<p>first</p>"
        css = shared_css

    class Second(Component):
        citry = registry
        template = "<p>second</p>"
        css = shared_css

    class Root(Component):
        citry = registry
        template = '<main :data-ready="true"><c-First #c-key="\'first\'"/><c-Second #c-key="\'second\'"/></main>'

    payload = default_events_producer(registry).prepare_from_render(
        render_prepared_direct(Root()), citry=registry, app_id="shared-component-css", revision=0
    )
    shared = [
        item
        for item in payload["styles"]
        if item["source"].get("sha256") == hashlib.sha256(shared_css.encode()).hexdigest()
    ]

    assert {item["owner"]["typeKey"] for item in shared} == {First.class_id, Second.class_id}
    assert all(item["source"]["attrs"] == {"rel": "stylesheet"} for item in shared)


def test_prepared_type_script_identity_hashes_exact_wrapped_served_bytes() -> None:
    registry = Citry(secret="vue-type-asset-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class Root(Component):
        citry = registry
        template = (
            "<!doctype html><html><head><title>test</title></head>"
            '<body><main :data-ready="true">root</main></body></html>'
        )
        js = "const scopedName = 3; $component({data(){return {value: scopedName};}});"

    payload = default_events_producer(registry).prepare_from_render(
        render_prepared_direct(Root()), citry=registry, app_id="app", revision=0
    )
    script = payload["scripts"][0]
    content = definition_bundle(registry, script["source"]["sha256"])
    assert content is not None
    assert hashlib.sha256(content).hexdigest() == script["source"]["sha256"]
    assert script["source"]["url"].endswith(f"/{script['source']['sha256']}.js")
    assert content.startswith(b"(function() {\nconst scopedName = 3;")
    assert content.endswith(b"\n})();")


def test_custom_dependency_hook_disables_later_lazy_type_assets() -> None:
    class DependencyPolicy(Extension):
        name = "dependency_policy"

        def on_dependencies(self, ctx):
            return None

    registry = Citry(autodiscover=False, extensions=[DependencyPolicy])

    class Root(Component):
        citry = registry
        template = (
            "<!doctype html><html><head><title>test</title></head>"
            '<body><main :data-ready="true">root</main></body></html>'
        )

    html = Root().render().serialize()
    assert '"allowLazyTypeAssets":false' in html


def test_type_policy_rejects_custom_or_unresolved_lazy_dependencies() -> None:
    registry = Citry(secret="vue-type-policy-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class CustomHook(Component):
        citry = registry
        template = "<p>custom</p>"

        @classmethod
        def on_dependencies(cls, scripts, styles):
            return None

    class ExtraAsset(Component):
        citry = registry
        template = "<p>extra</p>"

        class Dependencies:
            js = ["https://example.test/required.js"]

    for component in (CustomHook, ExtraAsset):
        payload = default_events_producer(registry).prepare_from_render(
            render_prepared_direct(component()), citry=registry, app_id="app", revision=0
        )
        assert payload["typePolicies"] == [{"typeKey": component.class_id, "lazyAllowed": False}]


def test_shared_stylesheet_is_owned_by_each_actual_occurrence_type() -> None:
    registry = Citry(autodiscover=False)

    class First(Component):
        citry = registry
        template = "<p>first</p>"

        class Dependencies:
            css = ["/shared.css"]

    class Second(Component):
        citry = registry
        template = "<p>second</p>"

        class Dependencies:
            css = ["/shared.css"]

    class Root(Component):
        citry = registry
        template = "<main><c-First/><c-Second/></main>"

    payload = default_events_producer(registry).prepare_from_render(
        render_prepared_direct(Root()), citry=registry, app_id="app", revision=0
    )
    shared = [item for item in payload["styles"] if item["source"]["url"] == "/shared.css"]
    assert len(shared) == 2
    assert {item["owner"]["typeKey"] for item in shared} == {First.class_id, Second.class_id}
    occurrence_types = {item["id"]: item["typeKey"] for item in payload["occurrences"]}
    for item in shared:
        assert {occurrence_types[value] for value in item["owner"]["occurrenceIds"]} == {item["owner"]["typeKey"]}


def test_standalone_shared_assets_keep_each_owner_and_emit_one_physical_tag() -> None:
    registry = Citry(autodiscover=False)
    shared_script = Script(content="globalThis.__citrySharedAsset = true;", wrap=False)
    shared_style = Style(content=".citry-shared-asset { color: currentColor; }")

    class First(Component):
        citry = registry
        template = '<p class="citry-shared-asset">first</p>'

        class Dependencies:
            js = [shared_script]
            css = [shared_style]

    class Second(Component):
        citry = registry
        template = '<p class="citry-shared-asset">second</p>'

        class Dependencies:
            js = [shared_script]
            css = [shared_style]

    class Root(Component):
        citry = registry
        template = '<main :data-ready="true"><c-First/><c-Second/></main>'

    rendered = render_prepared_direct(Root())
    payload = default_events_producer(registry).prepare_from_render(
        rendered,
        citry=registry,
        app_id="shared-assets",
        revision=0,
    )
    script_owners = {
        item["owner"]["typeKey"]
        for item in payload["scripts"]
        if item["source"].get("sha256") == hashlib.sha256(shared_script.content.encode()).hexdigest()
    }
    style_owners = {
        item["owner"]["typeKey"]
        for item in payload["styles"]
        if item["source"].get("sha256") == hashlib.sha256(shared_style.content.encode()).hexdigest()
    }
    assert script_owners == {First.class_id, Second.class_id}
    assert style_owners == {First.class_id, Second.class_id}

    html = rendered.serialize()
    assert html.count(shared_script.content) == 1
    assert html.count(shared_style.content) == 1


def test_transparent_render_helper_styles_use_the_mapped_vue_owner() -> None:
    registry = Citry(autodiscover=False)

    class Widget(Component):
        citry = registry
        template = '<p :data-ready="true">widget</p>'

        class Dependencies:
            css = ["/widget.css"]

    rendered = registry.render_template(
        '<c-slot name="content"/>',
        slots={"content": Slot(lambda ctx: Widget().render(provides=ctx.provides))},
    )
    payload = default_events_producer(registry).prepare_from_render(rendered, citry=registry, app_id="app", revision=0)
    style = next(item for item in payload["styles"] if item["source"]["url"] == "/widget.css")
    assert style["owner"]["typeKey"] == Widget.class_id
    occurrence_types = {item["id"]: item["typeKey"] for item in payload["occurrences"]}
    assert {occurrence_types[value] for value in style["owner"]["occurrenceIds"]} == {Widget.class_id}
