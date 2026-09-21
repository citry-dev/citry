# ruff: noqa: FBT003

from __future__ import annotations

import subprocess
import sys

import pytest

from citry import Citry, Component, Const, Extension, Markup
from citry._vue.capture import (
    PreparedAttribute,
    PreparedElementClose,
    PreparedElementCloseNode,
    PreparedElementOpen,
    PreparedElementOpenNode,
    PreparedExprNode,
    PreparedSourceText,
    PreparedSourceTextNode,
    PreparedTextValue,
    PreparedVerbatimHtml,
    PreparedVerbatimHtmlNode,
    render_prepared,
    typed_render_scope,
)
from citry._vue.compiler import NativeCompiler
from citry._vue.direct_capture import UnsupportedPreparedView, assemble_typed_render
from citry._vue.leaf_program import PreparedLeafProgram
from citry.citry_context import CitryContext
from citry.constness import ConstBodyCache
from citry.ext.events.bindings import RUNTIME_CONTROL_ATTR
from citry.nodes import ExprHtmlAttr, StaticHtmlAttr, TemplateNode
from citry.slots import Slot


def _assembled_view(render, **kwargs):
    return assemble_typed_render(render, **kwargs).view


def test_prepared_nodes_preserve_source_and_python_text_semantics() -> None:
    source = '<p c-title="title">{{ value }}</p>'
    context = CitryContext(variables={"title": "<heading>", "value": True})
    opened = PreparedElementOpenNode(
        source,
        (0, 19),
        "p",
        (ExprHtmlAttr(source, (3, 18), "c-title", "title", ("title",)),),
        ("title",),
        False,
        False,
        (),
    ).render(context)
    value = PreparedExprNode(source, (19, 30), "value", ("value",)).render(context)

    assert opened == PreparedElementOpen(
        source,
        (0, 19),
        "p",
        (PreparedAttribute("title", "data", (3, 18), "<heading>"),),
        False,
        False,
        (),
    )
    assert value == PreparedTextValue(source, (19, 30), "True")
    assert PreparedSourceTextNode(source, (0, 2), "é").render(context) == PreparedSourceText(source, (0, 2), "é")
    assert PreparedVerbatimHtmlNode(source, (2, 5), "{{x}}").render(context) == PreparedVerbatimHtml(
        source, (2, 5), "{{x}}"
    )
    assert PreparedElementCloseNode(source, (30, 34), "p").render(context) == PreparedElementClose(
        source, (30, 34), "p"
    )


def test_prepared_verbatim_html_is_never_compiled_as_vue_source() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class RawBlock(Component):
        citry = registry
        template = "<div><c-raw><button @click='unsafe'>{{ unsafe }}</button></c-raw></div>"

    rendered = render_prepared(RawBlock())
    assert rendered.serialize(deps_strategy="ignore") == (
        "<div data-cid-c1=\"\"><button @click='unsafe'>{{ unsafe }}</button></div>"
    )
    assembly = assemble_typed_render(rendered, revision=0, tag_for_type=lambda _key: "x-raw-block")
    occurrence = assembly.view.occurrences[0]
    compiled_input = assembly.compile_inputs[occurrence.definition_id]
    assert "unsafe" not in compiled_input.template
    assert "{{ unsafe }}" not in compiled_input.template
    assert "<citry-opaque-html" in compiled_input.template
    assert occurrence.prepared_data["opaqueHtml"] == {
        "citryOpaque0": {"html": "<button @click='unsafe'>{{ unsafe }}</button>"}
    }


def test_trusted_html_rejects_raw_text_and_rcdata_contexts() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Rcdata(Component):
        citry = registry
        template = "<div><textarea>{{ value }}</textarea></div><title>{{ value }}</title>"

        def template_data(self, kwargs, slots):
            return {"value": Markup("&lt;b&gt;x&lt;/b&gt;")}

    with pytest.raises(UnsupportedPreparedView, match="raw-text or RCDATA content"):
        assemble_typed_render(render_prepared(Rcdata()), revision=0, tag_for_type=lambda _key: "x-rcdata")

    class RawText(Component):
        citry = registry
        template = "<style>{{ value }}</style>"

        def template_data(self, kwargs, slots):
            return {"value": Markup("body { color: red }")}

    with pytest.raises(UnsupportedPreparedView, match="raw-text or RCDATA content"):
        assemble_typed_render(render_prepared(RawText()), revision=0, tag_for_type=lambda _key: "x-raw-text")

    class ForeignParent(Component):
        citry = registry
        template = "<svg><g>{{ value }}</g></svg>"

        def template_data(self, kwargs, slots):
            return {"value": Markup("<circle></circle>")}

    with pytest.raises(UnsupportedPreparedView, match="SVG or MathML parent"):
        assemble_typed_render(render_prepared(ForeignParent()), revision=0, tag_for_type=lambda _key: "x-foreign")

    class DynamicRcdataRaw(Component):
        citry = registry
        template = '<c-element c-is="tag"><c-raw><b>x</b></c-raw></c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "textarea"}

    with pytest.raises(UnsupportedPreparedView, match=r"c-raw.*raw-text or RCDATA content"):
        assemble_typed_render(
            render_prepared(DynamicRcdataRaw()),
            revision=0,
            tag_for_type=lambda _key: "x-dynamic-rcdata",
        )


def test_opaque_html_rejects_component_and_slot_placement_under_foreign_content() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class OpaqueChild(Component):
        citry = registry
        template = "{{ body }}"

        def template_data(self, kwargs, slots):
            return {"body": Markup('<title><b onclick="globalThis.example=1">x</b></title>')}

    class ComponentParent(Component):
        citry = registry
        template = "<div><c-OpaqueChild /></div><svg><c-OpaqueChild /></svg>"

    with pytest.raises(UnsupportedPreparedView, match="SVG or MathML parent"):
        assemble_typed_render(
            render_prepared(ComponentParent()),
            revision=0,
            tag_for_type=lambda key: f"x-{key.lower().replace('_', '-')}",
        )

    class ForeignSlot(Component):
        citry = registry
        template = "<svg><c-slot /></svg>"

    class SlotParent(Component):
        citry = registry
        template = '<c-ForeignSlot><c-fill name="default">{{ body }}</c-fill></c-ForeignSlot>'

        def template_data(self, kwargs, slots):
            return {"body": Markup('<title><b onclick="globalThis.example=1">x</b></title>')}

    with pytest.raises(UnsupportedPreparedView, match="SVG or MathML parent"):
        assemble_typed_render(
            render_prepared(SlotParent()),
            revision=0,
            tag_for_type=lambda key: f"x-{key.lower().replace('_', '-')}",
        )


@pytest.mark.parametrize("foreign_parent", ["svg", "math"])
@pytest.mark.parametrize("opaque_kind", ["markup", "raw"])
def test_opaque_call_run_members_reject_foreign_physical_parents(foreign_parent: str, opaque_kind: str) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = registry

        class Kwargs:
            value: int

        template = "{{ body }}" if opaque_kind == "markup" else "<c-raw><b>opaque</b></c-raw>"

        def template_data(self, kwargs, slots):
            return {"body": Markup("<b>opaque</b>")}

    class Root(Component):
        citry = registry
        template = (
            f"<{foreign_parent}>"
            '<c-for each="value in values"><c-Child #c-key="value" c-value="value" /></c-for>'
            f"</{foreign_parent}>"
        )

        def template_data(self, kwargs, slots):
            return {"values": [1, 2]}

    with pytest.raises(UnsupportedPreparedView, match="SVG or MathML parent"):
        assemble_typed_render(
            render_prepared(Root()),
            revision=0,
            tag_for_type=lambda key: f"x-{key.lower().replace('_', '-')}",
        )


@pytest.mark.parametrize("opaque_kind", ["markup", "raw"])
def test_opaque_call_run_members_keep_optimized_html_parent(opaque_kind: str) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = registry

        class Kwargs:
            value: int

        template = "{{ body }}" if opaque_kind == "markup" else "<c-raw><b>opaque</b></c-raw>"

        def template_data(self, kwargs, slots):
            return {"body": Markup("<b>opaque</b>")}

    class Root(Component):
        citry = registry
        template = '<div><c-for each="value in values"><c-Child #c-key="value" c-value="value" /></c-for></div>'

        def template_data(self, kwargs, slots):
            return {"values": [1, 2]}

    assembly = assemble_typed_render(
        render_prepared(Root()),
        revision=0,
        tag_for_type=lambda key: f"x-{key.lower().replace('_', '-')}",
    )
    root = next(item for item in assembly.view.occurrences if item.parent_id is None)
    compile_input = assembly.compile_inputs[root.definition_id]
    assert len(compile_input.local_call_runs) == 1
    assert len(root.prepared_data["callRuns"]["citryRun0"]) == 2


@pytest.mark.parametrize(
    ("python_value", "expected"),
    [(None, ""), (False, "False"), (1.0, "1.0"), ("&lt;", "&lt;"), ("<tag>", "<tag>")],
)
def test_prepared_expression_carries_text_data_without_html_escaping(python_value: object, expected: str) -> None:
    node = PreparedExprNode("{{ value }}", (0, 11), "value", ("value",))
    assert node.render(CitryContext(variables={"value": python_value})) == PreparedTextValue(
        "{{ value }}", (0, 11), expected
    )


def test_slot_scalar_operations_stay_public_strings_and_become_stable_prepared_text() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Root(Component):
        citry = registry
        template = (
            "<div>{{ value() }}|{{ value().upper() }}|{{ f'{value()}' }}</div>"
            '<svg><text><c-slot name="svg" /></text></svg>'
            "<textarea>{{ textarea() }}</textarea>"
            "<title>{{ title() }}</title>"
        )

        def template_data(self, kwargs, slots):
            return {
                "value": self.raw_slots["value"],
                "textarea": self.raw_slots["textarea"],
                "title": self.raw_slots["title"],
            }

    value = Slot("a&b")
    public = value()
    assert isinstance(public, Markup)
    assert public == "a&amp;b"
    assert len(public) == 7
    assert public.upper() == "A&AMP;B"
    assert f"<{public}>" == "<a&amp;b>"
    assert public + Markup("<b>x</b>") == Markup("a&amp;b<b>x</b>")
    assert "{}".format(public) == "a&amp;b"  # noqa: UP032 - exercise Markup.format semantics

    def assembly(text: str):
        rendered = render_prepared(
            Root(
                slots={
                    "value": Slot(text),
                    "svg": "svg&",
                    "textarea": "\nline&",
                    "title": "title&",
                }
            )
        )
        return assemble_typed_render(rendered, revision=0, tag_for_type=lambda _key: "x-root")

    first = assembly("a&b")
    second = assembly("changed&")
    assert first.view.occurrences[0].definition_id == second.view.occurrences[0].definition_id
    values = first.view.occurrences[0].prepared_data
    text_values = [value for key, value in values.items() if key.startswith("citryText")]
    assert "a&b" in text_values
    assert "A&B" in text_values
    assert "a&amp;b" in text_values
    assert "svg&" in text_values
    assert "\nline&" in text_values
    assert "title&" in text_values


def test_slot_does_not_turn_explicit_markup_into_svg_text() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Root(Component):
        citry = registry
        template = "<svg><text><c-slot /></text></svg>"

    with pytest.raises(TypeError, match="unsupported raw output: Markup"):
        render_prepared(Root(slots={"default": Markup("<b>trusted</b>")}))


@pytest.mark.parametrize(
    ("slot", "expected"),
    [
        (Slot("<>&"), "<>&"),
        (Slot("&amp;"), "&amp;"),
        (Slot("{{ literal }}"), "{{ literal }}"),
        (Slot(True), "True"),
        (Slot(None), "None"),
        (Slot(10**30), str(10**30)),
        (Slot(lambda _ctx: None), ""),
    ],
)
def test_slot_scalar_types_become_exact_prepared_text(slot: Slot, expected: str) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Root(Component):
        citry = registry
        template = "<p>{{ value() }}</p>"

        def template_data(self, kwargs, slots):
            return {"value": self.raw_slots["value"]}

    assembly = assemble_typed_render(
        render_prepared(Root(slots={"value": slot})),
        revision=0,
        tag_for_type=lambda _key: "x-root",
    )
    assert expected in assembly.view.occurrences[0].prepared_data.values()


@pytest.mark.parametrize(("value", "expected"), [(float("nan"), "nan"), (float("inf"), "inf")])
def test_prepared_exact_float_text_keeps_nonfinite_spelling(value: float, expected: str) -> None:
    node = PreparedExprNode("{{ value }}", (0, 11), "value", ("value",))
    assert node.render(CitryContext(variables={"value": value})) == PreparedTextValue("{{ value }}", (0, 11), expected)


def test_exact_scalar_text_is_escaped_only_when_static_html_is_materialized() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        template = '<p c-if="True">{{ value }}</p>'

        def template_data(self, kwargs, slots):
            return {"value": "<&"}

    rendered = Leaf().render()
    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert program.prepared_data["citryText0"] == "<&"
    assert "&lt;&amp;" in rendered.serialize(deps_strategy="ignore")


def test_prepared_scalar_specialization_observes_live_component_like_registration() -> None:
    source = """
from citry import Citry, Component
from citry.component_like import ComponentLike

app = Citry(autodiscover=False, extensions=[])
class Leaf(Component):
    citry = app
    template = '<p c-if="True">{{ value }}</p>'
    def template_data(self, kwargs, slots):
        return {'value': '<'}

assert '&lt;' in Leaf().render().serialize(deps_strategy='ignore')
ComponentLike.register(str)
try:
    Leaf().render()
except AttributeError as error:
    assert "__citry_element__" in str(error)
else:
    raise AssertionError('registered exact string bypassed live protocol dispatch')
"""
    result = subprocess.run([sys.executable, "-c", source], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_prepared_open_rejects_dynamic_vue_syntax_and_morph_metadata() -> None:
    source = '<div c-bind="attrs"></div>'
    node = PreparedElementOpenNode(
        source,
        (0, 20),
        "div",
        (ExprHtmlAttr(source, (5, 19), "c-bind", "attrs", ("attrs",)),),
        ("attrs",),
        False,
        False,
        (),
    )
    assert node.render(CitryContext(variables={"attrs": {"v-show": "danger"}}))
    with typed_render_scope(vue=True), pytest.raises(ValueError, match="cannot introduce Vue syntax"):
        node.render(CitryContext(variables={"attrs": {"v-show": "danger"}}))
    with pytest.raises(ValueError, match="morph metadata"):
        PreparedElementOpenNode(source, (0, 20), "div", (), (), False, False, (("morph", "ignore"),))


def test_typed_default_reuses_generator_and_static_serializer_consumes_parts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import citry_core.template_parser.compile as compile_module

    calls = 0

    def fake_compile(_ast: object, _lang: str | None = None) -> str:
        nonlocal calls
        calls += 1
        return """\
def generate_template():
    return [PreparedElementOpenNode(source, (0, 3), 'p', (), (), False, False, ()),
            PreparedExprNode(source, (3, 14), 'value', ('value',)),
            PreparedElementCloseNode(source, (14, 18), 'p')]
"""

    monkeypatch.setattr(compile_module, "_compile_prepared_template", fake_compile)
    registry = Citry(autodiscover=False, extensions=[])

    class Card(Component):
        citry = registry
        template = "<p>{{ value }}</p>"

        def template_data(self, kwargs, slots):
            return {"value": "<safe text>"}

    ordinary = Card().render().serialize(deps_strategy="ignore")
    first = render_prepared(Card())
    second = render_prepared(Card())

    assert "&lt;safe text&gt;" in ordinary
    assert calls == 1
    assert isinstance(first.parts[0], PreparedLeafProgram)
    assert first.parts[0].prepared_data["citryText0"] == "<safe text>"
    assert isinstance(second.parts[0], PreparedLeafProgram)
    assert "<p data-cid-" in first.serialize(deps_strategy="ignore")
    assert "&lt;safe text&gt;</p>" in first.serialize(deps_strategy="ignore")


def test_static_attribute_resolution_remains_ordinary_html() -> None:
    context = CitryContext()
    node = PreparedElementOpenNode(
        '<div class="x">',
        (0, 15),
        "div",
        (StaticHtmlAttr('<div class="x">', (5, 14), "class", "x", ()),),
        (),
        False,
        False,
        (),
    )
    opened = node.render(context)
    assert opened.attrs == (PreparedAttribute("class", "source", (5, 14), 'class="x"'),)


def test_native_prepared_compiler_executes_through_scoped_runtime() -> None:
    registry = Citry()

    class NativeCard(Component):
        citry = registry
        template = '<p class="x" c-title="title">Hi {{ value }}</p>'

        def template_data(self, kwargs, slots):
            return {"title": "heading", "value": "<body>"}

    rendered = render_prepared(NativeCard())

    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert program.prepared_data == {"citryAttrs0": {"title": "heading"}, "citryText0": "<body>"}
    assert 'class="x" v-bind="preparedData.citryAttrs0"' in program.fragment.template


def test_authored_vue_attribute_stays_source_while_spread_cannot_create_one() -> None:
    registry = Citry()

    class Authored(Component):
        citry = registry
        template = '<div v-show="shown" c-title="title">x</div>'

        def template_data(self, kwargs, slots):
            return {"shown": False, "title": "resolved"}

    program = render_prepared(Authored()).parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert 'v-show="shown"' in program.fragment.template
    assert program.prepared_data["citryAttrs0"] == {"title": "resolved"}


def test_events_rewrite_remains_resolved_data_not_compiler_source() -> None:
    registry = Citry(secret="prepared-events-test-secret")  # noqa: S106 - test-only key
    registry.set_mounted_prefix("/citry")

    class Button(Component):
        citry = registry

        class Events:
            def save(self):
                return None

        template = '<button class="x" @c-click="save">Save</button>'

    program = render_prepared(Button()).parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert "@c-click" not in program.fragment.template
    assert "v-on:click" in program.fragment.template
    assert set(program.prepared_data["eventBindings"]) == {"citryEvent12"}


def test_poll_binding_is_typed_and_omits_legacy_dom_metadata() -> None:
    registry = Citry(secret="prepared-poll-test-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class Poller(Component):
        citry = registry

        class PollArgs:
            text: str

        class Events:
            def refresh(self, data: Poller.PollArgs):
                return None

        template = """<output @c-poll.2s='refresh({text: "hello"})'>waiting</output>"""

    assembly = assemble_typed_render(
        render_prepared(Poller()),
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    occurrence = assembly.view.occurrences[0]
    definition = assembly.compile_inputs[occurrence.definition_id]
    assert "data-cev-poll" not in definition.template
    assert "$citryEvents.timings(&#x27;&#x27;,[{id:&#x27;citryPoll8&#x27;" in definition.template
    assert "{text: &quot;hello&quot;}" in definition.template
    assert occurrence.prepared_data["pollBindings"] == {
        "citryPoll8": {"id": "citryPoll8", "handler": "refresh", "args": '{text: "hello"}', "interval": 2000}
    }


def test_runtime_spread_poll_captures_handler_only_metadata() -> None:
    registry = Citry(secret="prepared-runtime-poll-secret", autodiscover=False)  # noqa: S106

    class Poller(Component):
        citry = registry

        class Events:
            def refresh(self):
                return None

        template = '<output c-bind="attrs">waiting</output>'

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-poll.2s": "refresh"}}

    assembly = assemble_typed_render(
        render_prepared(Poller()),
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    occurrence = assembly.view.occurrences[0]
    definition = assembly.compile_inputs[occurrence.definition_id]
    [binding] = occurrence.prepared_data["pollBindings"].values()
    [site] = definition.runtime_event_sites

    assert binding["id"].startswith("citryRuntimePoll")
    assert binding["handler"] == "refresh"
    assert binding["args"] is None
    assert binding["interval"] == 2000
    assert occurrence.prepared_data[site["bindingKey"]] == binding["id"]
    assert "v-citry-runtime-events" in definition.template


def test_timed_dom_event_emits_authenticated_lifecycle_directive() -> None:
    registry = Citry(secret="prepared-event-timing-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class Button(Component):
        citry = registry

        class SaveArgs:
            text: str

        class Events:
            def save(self, data: Button.SaveArgs):
                return None

        template = """<button @c-click.debounce.25ms='save({text: "hello"})'>Save</button>"""

    assembly = assemble_typed_render(
        render_prepared(Button()),
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    occurrence = assembly.view.occurrences[0]
    definition = assembly.compile_inputs[occurrence.definition_id]
    assembled_definition = next(item for item in assembly.view.definitions if item.id == occurrence.definition_id)
    assert "{text: &quot;hello&quot;}" in definition.template
    assert 'v-citry-event-timing="$citryEvents.timings(&#x27;citryEvent8&#x27;)"' in definition.template
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            definition.template,
            type_key=Button.class_id,
            directive_signature=assembled_definition.directive_signature,
            local_calls=definition.local_calls,
            element_bindings=definition.element_bindings,
            local_call_runs=definition.local_call_runs,
            dynamic_elements=definition.dynamic_elements,
        )
    assert '_resolveDirective("citry-event-timing")' in compiled.javascript
    assert '"hello"' in compiled.javascript
    assert "&quot;hello&quot;" not in compiled.javascript


@pytest.mark.parametrize(
    "directive",
    [
        'v-citry-event-timing="forged"',
        'v-citry-event-timing.foo="forged"',
        'v-citry-event-timing:arg="forged"',
        'v-citry-event-timing:[which]="forged"',
    ],
)
@pytest.mark.parametrize("timed_binding", ["", '@c-click.debounce.25ms="save"'])
def test_authored_template_cannot_impersonate_event_timing_directive(
    directive: str,
    timed_binding: str,
) -> None:
    registry = Citry()

    class Button(Component):
        citry = registry

        class Events:
            def save(self):
                return None

        template = f"<button {directive} {timed_binding}>Save</button>"

    with pytest.raises(ValueError, match="reserved compiler output"):
        render_prepared(Button())


def test_leaf_program_reuses_one_authored_event_binding_across_python_loop_items() -> None:
    registry = Citry(secret="prepared-events-loop-secret")  # noqa: S106 - test-only key
    registry.set_mounted_prefix("/citry")

    class Buttons(Component):
        citry = registry

        class Events:
            def save(self):
                return None

        template = '<button c-for="label in labels" @c-click="save">{{ label }}</button>'

        def template_data(self, kwargs, slots):
            return {"labels": ["A", "B"]}

    program = render_prepared(Buttons()).parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert program.fragment.template.count("$citryEvents.dispatch") == 1
    assert set(program.prepared_data["eventBindings"]) == {"citryEvent20"}
    assert program.prepared_data["citryLoop0"] == [
        {"citryAttrs0": {}, "citryText0": "A"},
        {"citryAttrs0": {}, "citryText0": "B"},
    ]


def test_leaf_program_rejects_duplicate_handlers_for_one_dom_event() -> None:
    registry = Citry(secret="prepared-events-duplicate-secret")  # noqa: S106 - test-only key
    registry.set_mounted_prefix("/citry")

    class Buttons(Component):
        citry = registry

        class Events:
            def save(self):
                return None

        template = '<button c-if="True" @c-click="save" @c-click.prevent="save">Save</button>'

    assert not any(isinstance(part, PreparedLeafProgram) for part in render_prepared(Buttons()).parts)


def test_plain_element_key_metadata_is_evaluated_once_as_structured_data() -> None:
    registry = Citry()

    class Keyed(Component):
        citry = registry
        template = "<div #c-key=\"item['id']\">x</div>"

        def template_data(self, kwargs, slots):
            return {"item": {"id": 7}}

    program = render_prepared(Keyed()).parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert program.prepared_data["citryKey0"] == "7"


def test_expression_string_conversion_runs_once() -> None:
    class Counted:
        calls = 0

        def __str__(self) -> str:
            self.calls += 1
            return "<once>"

    value = Counted()
    rendered = PreparedExprNode("{{ value }}", (0, 11), "value", ("value",)).render(
        CitryContext(variables={"value": value})
    )
    assert rendered == PreparedTextValue("{{ value }}", (0, 11), "<once>")
    assert type(rendered.value) is str
    assert value.calls == 1


def test_authored_vue_syntax_keeps_exact_source_with_unrelated_spread_attrs() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Mixed(Component):
        citry = registry
        template = '<div v-show="shown" c-bind="attrs">x</div>'

        def template_data(self, kwargs, slots):
            return {"shown": True, "attrs": {"title": "ok"}}

    rendered = render_prepared(Mixed())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    compiled = assembly.compile_inputs[assembly.view.occurrences[0].definition_id]
    assert 'v-show="shown"' in compiled.template
    assert 'v-bind="preparedData.citryAttrs' in compiled.template
    assert assembly.view.occurrences[0].prepared_data[
        next(key for key in assembly.view.occurrences[0].prepared_data if key.startswith("citryAttrs"))
    ] == {"title": "ok"}


def test_runtime_attr_hook_may_remove_but_not_replace_authored_vue_source() -> None:
    class RemoveVue(Extension):
        name = "remove_vue"

        def on_attrs_resolved(self, ctx):
            attrs = dict(ctx.attrs)
            attrs.pop("v-show")
            return attrs

    class ReplaceVue(Extension):
        name = "replace_vue"

        def on_attrs_resolved(self, ctx):
            return {**ctx.attrs, "v-show": "attacker", "@click": "attack()"}

    def component(registry):
        class Mixed(Component):
            citry = registry
            template = '<div v-show="shown" c-bind="attrs">x</div>'

            def template_data(self, kwargs, slots):
                return {"shown": True, "attrs": {"title": "ok"}}

        return Mixed

    removed = render_prepared(component(Citry(autodiscover=False, extensions=[RemoveVue]))())
    assembly = assemble_typed_render(
        removed,
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    compiled = assembly.compile_inputs[assembly.view.occurrences[0].definition_id]
    assert "v-show" not in compiled.template
    assert 'v-bind="preparedData.citryAttrs' in compiled.template

    with pytest.raises(ValueError, match="cannot introduce Vue syntax"):
        render_prepared(component(Citry(autodiscover=False, extensions=[ReplaceVue]))())


def test_typed_default_never_compiles_the_removed_ordinary_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import citry.component_render as render_module

    ordinary_compile = render_module.compile_template
    ordinary_calls = 0

    def counted_compile(ast: object) -> str:
        nonlocal ordinary_calls
        ordinary_calls += 1
        return ordinary_compile(ast)

    monkeypatch.setattr(render_module, "compile_template", counted_compile)
    registry = Citry()

    class PreparedFirst(Component):
        citry = registry
        template = "<p>prepared first</p>"

    render_prepared(PreparedFirst())
    assert ordinary_calls == 0
    PreparedFirst().render()
    assert ordinary_calls == 0


def test_prepared_render_rejects_raw_on_render_replacement() -> None:
    registry = Citry()

    class Replaced(Component):
        citry = registry
        template = "<p>unused</p>"

        def on_render(self):
            return "<strong>raw</strong>"

    with pytest.raises(TypeError, match="unsupported raw output"):
        render_prepared(Replaced())


def test_prepared_render_accepts_empty_on_render_replacement() -> None:
    registry = Citry()

    class Suppressed(Component):
        citry = registry
        template = "<p>unused</p>"

        def on_render(self):
            return ""

    rendered = render_prepared(Suppressed())
    assert rendered.parts == [""]
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    assert assembly.compile_inputs[root.definition_id].template == ""


def test_prepared_render_bypasses_component_output_cache_during_cutover() -> None:
    registry = Citry()

    class Cached(Component):
        citry = registry
        template = "<p>cached</p>"

        class Cache:
            enabled = True

    assert render_prepared(Cached()).render_target == "prepared"


def test_nested_template_generators_are_isolated_by_render_mode() -> None:
    from citry._vue.capture import _PREPARED_RENDER

    node = TemplateNode("outer", (0, 5), "<em>{{ value }}</em>", ("value",))
    context = CitryContext(variables={"value": "nested"})
    ordinary = node.render(context)
    token = _PREPARED_RENDER.set(True)
    try:
        prepared = node.render(context)
    finally:
        _PREPARED_RENDER.reset(token)

    assert ordinary.parts == ["<em>", "nested", "</em>"]
    assert isinstance(prepared.parts[0], PreparedElementOpen)
    assert prepared.parts[1] == PreparedTextValue("<em>{{ value }}</em>", (4, 15), "nested")


def test_nested_component_keeps_lexical_call_span_and_evaluated_key() -> None:
    registry = Citry()

    class Child(Component):
        citry = registry
        name = "child"
        template = "<i>child</i>"

    class Parent(Component):
        citry = registry
        template = '<div><c-child #c-key="key" /></div>'

        def template_data(self, kwargs, slots):
            return {"key": 7}

    rendered = render_prepared(Parent())
    child = rendered.parts[1]
    assert hasattr(child, "context")
    metadata = child.context.component._prepared_call_metadata
    assert metadata.source_span == (5, 29)
    assert metadata.explicit_key == "7"


def test_post_render_hook_raw_replacement_is_rejected() -> None:
    class RawReplacement(Extension):
        name = "raw_replacement"

        def on_component_rendered(self, ctx):
            return "<aside>raw</aside>"

    registry = Citry(extensions=[RawReplacement])

    class Card(Component):
        citry = registry
        template = "<p>card</p>"

    with pytest.raises(TypeError, match="unsupported raw output"):
        render_prepared(Card())


def test_callable_slot_plain_text_is_prepared_as_data() -> None:
    registry = Citry()

    class Receiver(Component):
        citry = registry
        template = '<article><c-slot name="default" /></article>'

    rendered = render_prepared(Receiver(slots={"default": lambda _data: "<i>raw</i>"}))
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    assert any("<i>raw</i>" in occurrence.prepared_data.values() for occurrence in assembly.view.occurrences)


def test_const_template_value_keeps_prepared_text_semantics() -> None:
    registry = Citry()

    class Card(Component):
        citry = registry
        template = "<p>{{ value }}</p>"

        def template_data(self, kwargs, slots):
            return {"value": Const("fixed")}

    rendered = render_prepared(Card())
    view = _assembled_view(rendered, revision=0, tag_for_type=lambda _key: "citry-card")
    occurrence = view.occurrences[0]
    assert "fixed" in occurrence.prepared_data.values()


def test_identical_compiled_branch_shapes_share_definition_despite_source_spans() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Item(Component):
        citry = registry
        template = '<p c-if="first">{{ label }}</p><p c-else>{{ label }}</p>'

        def template_data(self, kwargs, slots):
            return kwargs

    class Page(Component):
        citry = registry
        template = (
            '<main><c-item #c-key="\'a\'" first label="A"/><c-item #c-key="\'b\'" c-first="False" label="B"/></main>'
        )

    view = _assembled_view(
        render_prepared(Page()),
        revision=0,
        tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
    )
    items = [item for item in view.occurrences if item.type_key == Item.class_id]
    assert len(items) == 2
    assert len({item.definition_id for item in items}) == 1
    texts = {next(value for key, value in item.prepared_data.items() if key.startswith("citryText")) for item in items}
    assert texts == {"A", "B"}


def test_empty_typed_render_serializes_as_empty_html() -> None:
    registry = Citry()

    class BlankCard(Component):
        citry = registry
        template = ""

    rendered = render_prepared(BlankCard())
    assert rendered.parts == []
    assert rendered.render_target == "prepared"
    assert rendered.serialize(deps_strategy="ignore") == ""


@pytest.mark.parametrize("revision", [-1, True])
def test_direct_assembly_rejects_invalid_revision_before_traversal(revision: object) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Card(Component):
        citry = registry
        template = "<p>card</p>"

    with pytest.raises(ValueError, match="nonnegative exact integer"):
        _assembled_view(
            render_prepared(Card()),
            revision=revision,  # type: ignore[arg-type]
            tag_for_type=lambda _key: "citry-card",
        )


def test_prepared_body_cache_uses_the_bounded_per_engine_const_cache() -> None:
    compiled_bodies: list[type[Component]] = []

    class CountCompiledBodies(Extension):
        name = "count_prepared_const_bodies"

        def on_template_compiled(self, ctx):
            compiled_bodies.append(ctx.component_class)

    registry = Citry(extensions=[CountCompiledBodies])
    registry._const_body_cache = ConstBodyCache(max_entries=2)

    class Card(Component):
        citry = registry
        template = "<p>{{ value }}</p>"

        def template_data(self, kwargs, slots):
            return {"value": Const(kwargs["value"])}

    for value in ("first", "second", "third"):
        render_prepared(Card(value=value))

    assert len(compiled_bodies) == 3
    assert compiled_bodies == [Card, Card, Card]
    assert len(registry._const_body_cache) == 2

    # The first signature was evicted by the two later ones, so rendering it
    # again has to rebuild the prepared body while keeping the cache bounded.
    render_prepared(Card(value="first"))
    assert len(compiled_bodies) == 4
    assert compiled_bodies[-1] is Card
    assert len(registry._const_body_cache) == 2


def test_typed_render_converts_to_local_calls_and_occurrence_data() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = registry
        name = "child"
        template = '<p c-title="title">{{ title }}</p>'

        def template_data(self, kwargs, slots):
            return {"title": "one"}

    class Page(Component):
        citry = registry
        template = "<main><c-child #c-key=\"'child-key'\" /></main>"

    rendered = render_prepared(Page())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
    )
    view = assembly.view

    assert len(view.occurrences) == 2
    root = next(item for item in view.occurrences if item.id == view.root_id)
    child = next(item for item in view.occurrences if item.parent_id == root.id)
    root_input = assembly.compile_inputs[root.definition_id]
    call = root_input.local_calls[0]
    assert root.prepared_data["calls"][call["localId"]] == {
        "id": child.id,
        "key": child.id,
        "parentId": root.id,
    }
    child_input = assembly.compile_inputs[child.definition_id]
    assert len(child_input.element_bindings) == 1
    attrs_key = child_input.element_bindings[0]["attrsBindingKey"]
    assert child.prepared_data[attrs_key] == {"title": "one"}


def test_repeated_unkeyed_local_call_is_rejected() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = registry
        name = "child"
        template = "<i>child</i>"

    class Page(Component):
        citry = registry
        template = '<c-for each="item in items"><c-child /></c-for>'

        def template_data(self, kwargs, slots):
            return {"items": [1, 2]}

    rendered = render_prepared(Page())
    with pytest.raises(UnsupportedPreparedView, match="requires an explicit #c-key"):
        _assembled_view(
            rendered,
            revision=0,
            tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
        )


def test_keyed_repeated_calls_keep_occurrence_ids_across_reorder() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = registry
        name = "child"
        template = "<i>child</i>"

    class Page(Component):
        citry = registry
        template = '<c-for each="item in items"><c-child #c-key="item" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"items": kwargs["items"]}

    def prepare(items: list[int], revision: int):
        rendered = render_prepared(Page(items=items))
        return _assembled_view(
            rendered,
            revision=revision,
            tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
        )

    first = prepare([1, 2, 3], 0)
    second = prepare([3, 1, 4], 1)
    first_root = next(item for item in first.occurrences if item.id == first.root_id)
    second_root = next(item for item in second.occurrences if item.id == second.root_id)
    first_ids = set(first_root.prepared_data["callRuns"]["citryRun0"])
    second_ids = set(second_root.prepared_data["callRuns"]["citryRun0"])
    assert len(first_ids & second_ids) == 2
    assert len(first_ids - second_ids) == 1
    assert len(second_ids - first_ids) == 1


def test_repeated_plain_elements_allocate_distinct_text_and_attribute_bindings() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = registry
        template = '<c-for each="item in items"><p c-title="item">{{ item }}</p></c-for>'

        def template_data(self, kwargs, slots):
            return {"items": ["first", "second"]}

    rendered = render_prepared(Page())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
    )
    view = assembly.view

    root = next(item for item in view.occurrences if item.id == view.root_id)
    compiler_input = assembly.compile_inputs[root.definition_id]
    attrs_keys = [item["attrsBindingKey"] for item in compiler_input.element_bindings]
    assert attrs_keys == ["citryAttrs0"]
    records = root.prepared_data["citryLoop0"]
    assert [record["citryAttrs0"] for record in records] == [
        {"title": "first"},
        {"title": "second"},
    ]
    assert [record["citryText0"] for record in records] == ["first", "second"]


def test_supplied_fill_is_owned_by_caller_call_and_fallback_by_receiver() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Receiver(Component):
        citry = registry
        name = "receiver"
        template = '<section><c-slot name="body"><i>{{ label }}</i></c-slot></section>'

        def template_data(self, kwargs, slots):
            return {"label": "receiver"}

    class Leaf(Component):
        citry = registry
        name = "leaf"
        template = "<small>leaf</small>"

    class Caller(Component):
        citry = registry
        template = """
            <c-receiver #c-key="'supplied'">
                <c-fill name="body"><b>{{ label }}</b><c-leaf #c-key="'leaf'" /></c-fill>
            </c-receiver>
            <c-receiver #c-key="'fallback'" />
        """

        def template_data(self, kwargs, slots):
            return {"label": "caller"}

    rendered = render_prepared(Caller())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
    )
    view = assembly.view

    root = next(item for item in view.occurrences if item.id == view.root_id)
    root_input = assembly.compile_inputs[root.definition_id]
    assert len(root_input.local_calls) == 3
    assert root_input.local_call_runs == ()
    receivers = [item for item in view.occurrences if item.type_key == Receiver.class_id]
    supplied_occurrence = next(
        item for item in receivers if set(item.prepared_data["selectedSlots"].values()) == {"supplied"}
    )
    fallback_occurrence = next(
        item for item in receivers if set(item.prepared_data["selectedSlots"].values()) == {"fallback"}
    )
    supplied_id = supplied_occurrence.id
    assert set(supplied_occurrence.prepared_data["selectedSlots"].values()) == {"supplied"}
    leaf = next(item for item in view.occurrences if item.type_key == Leaf.class_id)
    assert leaf.parent_id == supplied_id
    assert set(fallback_occurrence.prepared_data["selectedSlots"].values()) == {"fallback"}
    assert "caller" in root.prepared_data.values()
    assert "receiver" in fallback_occurrence.prepared_data.values()
    assert "v-slot" in root_input.template

    compile_inputs = assembly.compile_inputs
    with NativeCompiler() as compiler:
        compiled = {
            definition.id: compiler.compile(
                compile_inputs[definition.id].template,
                type_key=definition.type_key,
                local_calls=compile_inputs[definition.id].local_calls,
                element_bindings=compile_inputs[definition.id].element_bindings,
                local_call_runs=compile_inputs[definition.id].local_call_runs,
            )
            for definition in view.definitions
        }
    assert len(compiled[root.definition_id].local_calls) == 3
    assert compiled[root.definition_id].local_call_runs == ()
    caller_js = compiled[root.definition_id].javascript
    supplied_receiver_js = compiled[
        next(item for item in view.occurrences if item.id == supplied_id).definition_id
    ].javascript
    fallback_receiver_js = compiled[fallback_occurrence.definition_id].javascript
    assert "citrySlot" in caller_js
    assert "renderSlot" in supplied_receiver_js
    assert "renderSlot" in fallback_receiver_js
    assert "selectedSlots" in compile_inputs[fallback_occurrence.definition_id].template
    assert all(
        "caller" not in value.template.lower() and ">receiver<" not in value.template.lower()
        for value in compile_inputs.values()
    )


def test_nested_slot_forwarding_keeps_root_fill_in_root_lexical_definition() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Inner(Component):
        citry = registry
        name = "inner"
        template = '<article><c-slot name="body" /></article>'

    class Wrapper(Component):
        citry = registry
        name = "wrapper"
        template = """
            <c-inner #c-key="'inner'">
                <c-fill name="body"><c-slot name="body" /></c-fill>
            </c-inner>
        """

    class Root(Component):
        citry = registry
        template = """
            <c-wrapper #c-key="'wrapper'">
                <c-fill name="body"><strong>{{ label }}</strong></c-fill>
            </c-wrapper>
        """

        def template_data(self, kwargs, slots):
            return {"label": "root lexical"}

    rendered = render_prepared(Root())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
    )
    view = assembly.view

    root = next(item for item in view.occurrences if item.id == view.root_id)
    root_input = assembly.compile_inputs[root.definition_id]
    assert "v-slot" in root_input.template
    assert "root lexical" in root.prepared_data.values()
    wrapper_call = root_input.local_calls[0]
    wrapper_id = root.prepared_data["calls"][wrapper_call["localId"]]["id"]
    wrapper = next(item for item in view.occurrences if item.id == wrapper_id)
    wrapper_input = assembly.compile_inputs[wrapper.definition_id]
    assert "v-slot" in wrapper_input.template
    assert "<slot name=" in wrapper_input.template
    assert "root lexical" not in wrapper.prepared_data.values()


def test_authored_vue_binding_cannot_conflict_with_prepared_python_attribute() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = registry
        template = '<input c-value="seed" :value="draft">'

        def template_data(self, kwargs, slots):
            return {"seed": "server", "draft": "browser"}

    rendered = render_prepared(Page())
    with pytest.raises(UnsupportedPreparedView, match="target the same HTML name"):
        _assembled_view(
            rendered,
            revision=0,
            tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
        )


@pytest.mark.parametrize(
    ("vue_attr", "python_attr"),
    [
        (':value="draft"', "c-VALUE"),
        (':VALUE="draft"', "c-value"),
        ('v-bind:TITLE="draft"', "c-title"),
    ],
)
def test_authored_and_python_attribute_targets_use_html_ascii_identity(vue_attr: str, python_attr: str) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = registry
        template = f'<input {vue_attr} {python_attr}="seed">'

        def template_data(self, kwargs, slots):
            return {"seed": "server", "draft": "browser"}

    with pytest.raises(UnsupportedPreparedView, match=r"same HTML name.*(?:VALUE|value|title)"):
        _assembled_view(
            render_prepared(Page()),
            revision=0,
            tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
        )


@pytest.mark.parametrize("vue_attr", [':[field]="draft"', 'v-bind:[field]="draft"'])
def test_dynamic_argument_binding_rejects_python_attrs_but_survives_alone(vue_attr: str) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Mixed(Component):
        citry = registry
        template = f'<input {vue_attr} c-title="seed">'

        def template_data(self, kwargs, slots):
            return {"field": "title", "draft": "browser", "seed": "server"}

    with pytest.raises(UnsupportedPreparedView, match=r"dynamic-argument.*prepared Python"):
        _assembled_view(
            render_prepared(Mixed()),
            revision=0,
            tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
        )

    class NativeOnly(Component):
        citry = registry
        template = f"<input {vue_attr}>"

        def template_data(self, kwargs, slots):
            return {"field": "title", "draft": "browser"}

    assembly = assemble_typed_render(
        render_prepared(NativeOnly()),
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    definition = assembly.compile_inputs[assembly.view.occurrences[0].definition_id]
    assert vue_attr in definition.template

    class NativeDynamicOnly(Component):
        citry = registry
        template = f'<c-element c-is="tag" {vue_attr}></c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "div", "field": "title", "draft": "browser"}

    dynamic_assembly = assemble_typed_render(
        render_prepared(NativeDynamicOnly()),
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    dynamic_definition = dynamic_assembly.compile_inputs[dynamic_assembly.view.occurrences[0].definition_id]
    assert vue_attr in dynamic_definition.template


@pytest.mark.parametrize("vue_attr", [':[field]="draft"', 'v-bind:[field]="draft"'])
def test_dynamic_element_argument_binding_still_rejects_nonempty_root_markers(vue_attr: str) -> None:
    class Marker(Extension):
        name = "marker"

        def on_component_data(self, ctx):
            ctx.context._add_root_markers(['data-probe="extension"'])

    registry = Citry(autodiscover=False, extensions=[Marker])

    class MarkedDynamic(Component):
        citry = registry
        template = f'<c-element c-is="tag" {vue_attr}></c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "div", "field": "title", "draft": "browser"}

    with pytest.raises(UnsupportedPreparedView, match="root marker conflicts"):
        assemble_typed_render(
            render_prepared(MarkedDynamic()),
            revision=0,
            tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
        )


def test_state_control_binding_is_typed_and_omits_legacy_dom_metadata() -> None:
    registry = Citry(autodiscover=False, secret="control-test-secret-control-test-secret")  # noqa: S106

    class Search(Component):
        citry = registry

        class State:
            query: str = "initial"

        class Events:
            def search(self, state):
                return None

        template = '<input :c-query.debounce.25ms="search">'

    assembly = assemble_typed_render(
        render_prepared(Search()),
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    occurrence = assembly.view.occurrences[0]
    definition = assembly.compile_inputs[occurrence.definition_id]
    assert "v-citry-control" in definition.template
    assert "data-cev-bind" not in definition.template
    controls = occurrence.prepared_data["controlBindings"]
    assert next(iter(controls.values())) == {
        "id": next(iter(controls)),
        "field": "query",
        "binding_mode": "two-way",
        "handler": "search",
        "lazy": False,
        "on": None,
        "key": None,
        "debounce": 25,
        "throttle": None,
    }


def test_multiple_state_bindings_on_one_element_are_rejected() -> None:
    registry = Citry(autodiscover=False, secret="control-list-secret-control-list-secret")  # noqa: S106

    class Pair(Component):
        citry = registry

        class State:
            first: str = "a"
            second: str = "b"

        template = "<input :c-first :c-second>"

    with pytest.raises(ValueError, match=r"exactly one :c-.*first.*second"):
        render_prepared(Pair())


def test_runtime_spread_state_binding_uses_typed_provenance() -> None:
    registry = Citry(autodiscover=False, secret="runtime-control-secret-runtime-control")  # noqa: S106

    class Search(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "refresh"}}

        template = '<input c-bind="attrs">'

    rendered = render_prepared(Search())
    assert any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    occurrence = assembly.view.occurrences[0]
    definition = assembly.compile_inputs[occurrence.definition_id]
    assert "v-citry-control" in definition.template
    assert "data-cev-bind" not in definition.template
    control = next(iter(occurrence.prepared_data["controlBindings"].values()))
    assert control["field"] == "query"
    assert control["handler"] == "refresh"


def test_runtime_spread_controls_at_one_loop_site_keep_distinct_specs() -> None:
    registry = Citry(autodiscover=False, secret="runtime-control-loop-runtime-control")  # noqa: S106

    class Fields(Component):
        citry = registry

        class State:
            first: str = ""
            second: str = ""

        class Events:
            def save_first(self, state):
                return None

            def save_second(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {
                "controls": [
                    {":c-first": "save_first"},
                    {":c-second": "save_second"},
                ]
            }

        template = '<input c-for="attrs in controls" c-bind="attrs">'

    assembly = assemble_typed_render(
        render_prepared(Fields()),
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    controls = assembly.view.occurrences[0].prepared_data["controlBindings"]
    assert len(controls) == 2
    assert {(value["field"], value["handler"]) for value in controls.values()} == {
        ("first", "save_first"),
        ("second", "save_second"),
    }


def test_runtime_spread_control_survives_the_general_direct_path() -> None:
    registry = Citry(autodiscover=False, secret="runtime-control-direct-runtime-control")  # noqa: S106

    class Direct(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"shown": True, "attrs": {":c-query": "refresh"}}

        template = '<input v-show="shown" c-bind="attrs">'

    rendered = render_prepared(Direct())
    assert not any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    occurrence = assembly.view.occurrences[0]
    definition = assembly.compile_inputs[occurrence.definition_id]
    assert 'v-show="shown"' in definition.template
    assert "v-citry-control" in definition.template
    assert next(iter(occurrence.prepared_data["controlBindings"].values()))["field"] == "query"


def test_runtime_control_candidate_keeps_one_leaf_definition_when_binding_appears() -> None:
    registry = Citry(autodiscover=False, secret="runtime-control-change-runtime-control")  # noqa: S106

    class Search(Component):
        citry = registry

        class Kwargs:
            enabled: bool = False

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "refresh"} if kwargs.enabled else {}}

        template = '<input c-bind="attrs">'

    without = assemble_typed_render(
        render_prepared(Search(enabled=False)),
        revision=0,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    with_binding = assemble_typed_render(
        render_prepared(Search(enabled=True)),
        revision=1,
        tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
    )
    first = without.view.occurrences[0]
    second = with_binding.view.occurrences[0]
    assert first.definition_id == second.definition_id
    definition = without.compile_inputs[first.definition_id]
    assert "v-citry-control" in definition.template
    assert "controlBindings" not in first.prepared_data
    assert next(iter(second.prepared_data["controlBindings"].values()))["field"] == "query"


def test_later_attribute_hook_cannot_replace_runtime_control_metadata() -> None:
    class ReplaceControl(Extension):
        name = "replace_control"

        def on_attrs_resolved(self, ctx):
            if RUNTIME_CONTROL_ATTR in ctx.attrs:
                return {**ctx.attrs, RUNTIME_CONTROL_ATTR: "forged"}
            return None

    registry = Citry(
        autodiscover=False,
        secret="runtime-control-forgery-runtime-control",  # noqa: S106
        extensions=[ReplaceControl],
    )

    class Search(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "refresh"}}

        template = '<input c-bind="attrs">'

    with pytest.raises(TypeError, match="lacks Events producer provenance"):
        render_prepared(Search())


def test_runtime_spread_event_arguments_are_rejected_before_prepared_capture() -> None:
    registry = Citry(autodiscover=False, secret="runtime-event-source-runtime-event-source")  # noqa: S106

    class Search(Component):
        citry = registry

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-click": "refresh({id: row.id})"}}

        template = '<button c-bind="attrs">search</button>'

    with pytest.raises(
        ValueError,
        match=r"runtime-resolved @c-\* event bindings support handler names without argument expressions",
    ):
        render_prepared(Search())


def test_authored_object_binding_with_python_spread_remains_rejected_until_order_is_preserved() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = registry
        template = '<input v-bind="browserAttrs" c-bind="server_attrs">'

        def template_data(self, kwargs, slots):
            return {"browserAttrs": {}, "server_attrs": {"title": "server"}}

    with pytest.raises(UnsupportedPreparedView, match="object v-bind"):
        _assembled_view(
            render_prepared(Page()),
            revision=0,
            tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
        )


def test_repeated_receiver_fills_allocate_distinct_caller_bindings() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        name = "leaf"
        template = "<small>leaf</small>"

    class Receiver(Component):
        citry = registry
        name = "receiver"
        template = '<article><c-slot name="body" /></article>'

    class Root(Component):
        citry = registry
        template = """
            <c-for each="row in rows">
                <c-receiver #c-key="row">
                    <c-fill name="body">{{ row }}<c-leaf #c-key="'leaf'" /></c-fill>
                </c-receiver>
            </c-for>
        """

        def template_data(self, kwargs, slots):
            return {"rows": ["A", "B"]}

    rendered = render_prepared(Root())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
    )
    view = assembly.view

    root = next(item for item in view.occurrences if item.id == view.root_id)
    compiler_input = assembly.compile_inputs[root.definition_id]
    receiver_calls = [item for item in compiler_input.local_calls if item["typeKey"] == Receiver.class_id]
    leaf_calls = [item for item in compiler_input.local_calls if item["typeKey"] == Leaf.class_id]
    assert len(receiver_calls) == len(leaf_calls) == 2
    assert len({item["localId"] for item in leaf_calls}) == 2
    assert len(root.prepared_data["calls"]) == 4
    assert len({root.prepared_data["calls"][item["localId"]]["id"] for item in leaf_calls}) == 2
    assert [root.prepared_data[key] for key in sorted(root.prepared_data) if key.startswith("citryText")] == ["A", "B"]


@pytest.mark.parametrize("name", ["innerHTML", "outerHTML", "textContent", "innerText", "onClick"])
def test_dynamic_dom_properties_and_listeners_are_rejected_before_compilation(name: str) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = registry
        template = '<div c-bind="attrs">safe fallback</div>'

        def template_data(self, kwargs, slots):
            return {"attrs": {name: '<img src="x" onerror="globalThis.pwned=true">'}}

    rendered = render_prepared(Page())
    with pytest.raises(UnsupportedPreparedView, match="dynamic DOM property is unsafe"):
        _assembled_view(
            rendered,
            revision=0,
            tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
        )


@pytest.mark.parametrize("authored_key", ['key="browser"', ':key="browserKey"'])
def test_prepared_element_key_rejects_another_authored_key(authored_key: str) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Page(Component):
        citry = registry
        template = f'<div {authored_key} #c-key="\'server\'" v-show="shown">value</div>'

        def template_data(self, kwargs, slots):
            return {"browserKey": "browser", "shown": True}

    rendered = render_prepared(Page())
    with pytest.raises(UnsupportedPreparedView, match="conflicts with another authored key"):
        _assembled_view(
            rendered,
            revision=0,
            tag_for_type=lambda type_key: f"citry-component-{type_key.split('_', 1)[0].lower()}",
        )
