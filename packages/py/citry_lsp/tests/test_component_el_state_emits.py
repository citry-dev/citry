"""`$el`, `$state` and `emits` are typed and checked from the component's own sources."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from lsprotocol import types
from test_component_instance_types import _position, _probe_message, _type_errors

from citry_lsp.engine import DocumentState, browser_diagnostics, browser_projection, hover
from citry_lsp.project import load_project

if TYPE_CHECKING:
    from pathlib import Path

# Lane is a child component with a typed `emits` object, rendered by Card.
_APP = """from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
class Lane(Component):
    citry = engine
    template_file = 'lane.html'
    js_file = 'lane.js'
class Card(Component):
    citry = engine
    template_file = 'card.html'
    js_file = 'card.js'
{extra}
"""

_LANE_JS = """$component({
  emits: {
    'drop-task'(/** @type {{taskId: number}} */ payload) { return true; },
    closed: null,
    emptied: () => true,
  },
});
"""


def _project(
    tmp_path: Path,
    template: str,
    javascript: str,
    *,
    extra: str = "",
    lane_template: str = "<section/>",
    lane_js: str = _LANE_JS,
):
    (tmp_path / "app.py").write_text(_APP.format(extra=extra), encoding="utf-8")
    (tmp_path / "card.html").write_text(template, encoding="utf-8")
    (tmp_path / "card.js").write_text(javascript, encoding="utf-8")
    (tmp_path / "lane.html").write_text(lane_template, encoding="utf-8")
    (tmp_path / "lane.js").write_text(lane_js, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready, project.status
    javascript_document = DocumentState((tmp_path / "card.js").as_uri(), "javascript", javascript, 1)
    template_document = DocumentState((tmp_path / "card.html").as_uri(), "citry-html", template, 1)
    for document in (javascript_document, template_document):
        document.update(document.source, 1, project)
    documents = {javascript_document.uri: javascript_document, template_document.uri: template_document}
    return project, javascript_document, template_document, documents


def _probed(tmp_path: Path, projection_source: str, marker: str, replacement: str) -> list[str]:
    source = projection_source.replace(marker, replacement, 1)
    assert source != projection_source, marker
    return _type_errors(tmp_path, source)


# `mounted()` reads `$el`; the editor works out its type only when a source reads it.
_EL_JS = """$component({
  data() { return { count: 1 }; },
  mounted() { this.$el; },
  methods: { read() { return this.count; } },
  onServerRender({ component }) { component.count; },
});
"""


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("<button>Go</button>", "HTMLButtonElement"),
        ("<section></section>", "HTMLElement"),
        # Comments and whitespace around the root are not rendered.
        ("\n  <!-- icon -->\n  <svg></svg>\n", "SVGSVGElement"),
        ("<my-widget></my-widget>", "HTMLElement"),
        # A v-if chain without v-else may render Vue's comment placeholder.
        ('<p v-if="count"></p><span v-else-if="count"></span>', "Comment | HTMLParagraphElement | HTMLSpanElement"),
        ('<p v-if="count"></p><div v-else></div>', "HTMLDivElement | HTMLParagraphElement"),
        ('<c-if cond="x"><ul></ul></c-if><c-else><ol></ol></c-else>', "HTMLOListElement | HTMLUListElement"),
        ('<template v-if="count"><table></table></template>', "Comment | HTMLTableElement"),
        # The attribute forms of the server's control flow.
        ('<p c-if="x"></p>', "Comment | HTMLParagraphElement"),
        (
            '<p c-if="x"></p><span c-elif="y"></span><div c-else></div>',
            "HTMLDivElement | HTMLParagraphElement | HTMLSpanElement",
        ),
        ('<li c-for="item in items"></li>', "Node"),
        # The root is a child component: its own root decides.
        ("<c-Lane></c-Lane>", "HTMLElement"),
        # Fragments and text.
        ("<p></p><p></p>", "Node"),
        ('<li v-for="item in [1]"></li>', "Node"),
        ("Plain text", "Text"),
        ("<c-slot />", "Node"),
    ],
)
def test_el_is_typed_from_the_template_root(tmp_path, template, expected):
    project, javascript, _template, documents = _project(tmp_path, template, _EL_JS)
    projection = browser_projection(javascript, _position(_EL_JS, "this.count", 1), project, documents)
    assert projection is not None
    errors = _probed(tmp_path, projection.source, "return this.count;", "__probe(this.$el);")
    assert _probe_message(expected) in errors, errors
    # An initializer's `component` is the same instance.
    errors = _probed(tmp_path, projection.source, "component.count;", "__probe(component.$el);")
    assert _probe_message(expected) in errors, errors


def test_el_in_template_expressions_and_unknown_roots(tmp_path):
    template = '<button @click="count" :title="$el"></button>'
    project, _javascript, template_document, documents = _project(tmp_path, template, _EL_JS)
    projection = browser_projection(template_document, _position(template, '$el"', 1), project, documents)
    assert projection is not None
    errors = _probed(tmp_path, projection.source, "\n$el\n", "\n__probe($el)\n")
    assert _probe_message("HTMLButtonElement") in errors, errors

    # A component that renders itself has no root to finish, so `$el` is a
    # plain Node rather than `any`.
    project, javascript, _template, documents = _project(tmp_path, "<c-Card></c-Card>", _EL_JS)
    projection = browser_projection(javascript, _position(_EL_JS, "this.count", 1), project, documents)
    assert projection is not None
    errors = _probed(tmp_path, projection.source, "return this.count;", "__probe(this.$el);")
    assert _probe_message("Node") in errors, errors


_STATE_JS = """$component({
  methods: { m() { this.$state; } },
});
"""


def test_state_is_typed_from_the_state_class(tmp_path):
    extra = """    class State:
        progress: int = 0
        note: str = ""
        _model = ('note',)
    class Events:
        def save(self):
            pass
"""
    project, javascript, _template, documents = _project(tmp_path, "<p></p>", _STATE_JS, extra=extra)
    projection = browser_projection(javascript, _position(_STATE_JS, "this.$state", 1), project, documents)
    assert projection is not None
    errors = _probed(
        tmp_path,
        projection.source,
        "this.$state;",
        "__probe(this.$state.progress); this.$state.note = 'x'; this.$state.progress = 1; this.$state.typo;",
    )
    assert _probe_message("number") in errors, errors
    assert "Cannot assign to 'progress' because it is a read-only property." in errors, errors
    assert "Property 'typo' does not exist on type 'CitryEventsState'." in errors, errors
    assert not [message for message in errors if "'note'" in message], errors
    # The member's hover text says what `$state` is.
    assert "Citry Events State for this component: the public fields of its `State` class" in projection.source


def test_state_without_a_state_class_has_no_fields(tmp_path):
    project, javascript, _template, documents = _project(tmp_path, "<p></p>", _STATE_JS)
    projection = browser_projection(javascript, _position(_STATE_JS, "this.$state", 1), project, documents)
    assert projection is not None
    errors = _probed(tmp_path, projection.source, "this.$state;", "this.$state.progress;")
    assert any("Property 'progress' does not exist" in message for message in errors), errors
    assert "declares no public `State` fields" in projection.source


def test_template_state_hover_names_the_citry_facade(tmp_path):
    template = '<p v-text="$state"></p>'
    project, _javascript, template_document, documents = _project(tmp_path, template, _STATE_JS)
    found = hover(template_document, _position(template, "$state", 1), project, documents)
    assert found is not None
    assert "Citry Events State" in found.contents.value
    assert "not Vue's `data()` or a Pinia store" in found.contents.value


_EMITS_JS = """$component({
  emits: {
    'drop-task'(/** @type {number} */ id) { return true; },
    closed: null,
  },
  props: { onPing: Function },
  methods: {
    m() {
      this.$emit('drop-task', 1);
      this.$emit('closed', 'any', 2);
      this.$emit('ping');
      this.$emit('nope');
    },
  },
  onServerRender({ component }) { component.$emit('bad'); },
});
"""


def _codes(diagnostics) -> list[tuple[str, str, types.DiagnosticSeverity | None]]:
    return sorted((str(item.code), item.message, item.severity) for item in diagnostics)


def test_component_js_emit_names_are_checked(tmp_path):
    project, javascript, _template, documents = _project(tmp_path, "<p></p>", _EMITS_JS)
    found = [
        item
        for item in browser_diagnostics(javascript, project, documents)
        if item.code == "citry.browser.undeclared-emit"
    ]
    assert [(item.message, item.severity) for item in found] == [
        ("Event 'nope' is not declared in this component's emits option.", types.DiagnosticSeverity.Error),
        ("Event 'bad' is not declared in this component's emits option.", types.DiagnosticSeverity.Error),
    ]
    assert found[0].range == types.Range(_position(_EMITS_JS, "nope"), _position(_EMITS_JS, "nope", 4))

    # The JavaScript provider types `$emit` like Vue's defineComponent().
    projection = browser_projection(javascript, _position(_EMITS_JS, "this.$emit", 1), project, documents)
    assert projection is not None
    errors = _probed(
        tmp_path,
        projection.source,
        "this.$emit('drop-task', 1);",
        "this.$emit('drop-task', 1); this.$emit('drop-task', 'wrong'); __probe(this.$emit);",
    )
    assert (
        _probe_message('((event: "drop-task", id: number) => void) & ((event: "closed", ...args: any[]) => void)')
        in errors
    ), errors
    # A payload that does not match the validator's parameter is a type error.
    assert "No overload matches this call." in errors, errors


def test_component_without_emits_accepts_any_event(tmp_path):
    javascript_source = "$component({ methods: { m() { this.$emit('anything', 1); } } });\n"
    project, javascript, _template, documents = _project(tmp_path, "<p></p>", javascript_source)
    assert not [item for item in browser_diagnostics(javascript, project, documents) if "undeclared" in str(item.code)]
    projection = browser_projection(javascript, _position(javascript_source, "this.$emit", 1), project, documents)
    assert projection is not None
    errors = _probed(tmp_path, projection.source, "this.$emit('anything', 1);", "__probe(this.$emit);")
    assert _probe_message("(event: string, ...args: any[]) => void") in errors, errors


def test_array_emits_limit_the_names(tmp_path):
    javascript_source = "$component({ emits: ['open', 'close'], methods: { m() { this.$emit('open'); } } });\n"
    project, javascript, _template, documents = _project(tmp_path, "<p></p>", javascript_source)
    projection = browser_projection(javascript, _position(javascript_source, "this.$emit", 1), project, documents)
    assert projection is not None
    errors = _probed(tmp_path, projection.source, "this.$emit('open');", "__probe(this.$emit);")
    assert _probe_message('(event: "close" | "open", ...args: any[]) => void') in errors, errors


def test_template_emit_is_typed_and_checked(tmp_path):
    template = "<button @click=\"$emit('drop-task', 1)\" @dblclick=\"$emit('dropped')\"></button>"
    project, _javascript, template_document, documents = _project(tmp_path, template, _EMITS_JS)
    found = [
        item
        for item in browser_diagnostics(template_document, project, documents)
        if item.code == "citry.browser.undeclared-emit"
    ]
    assert [item.message for item in found] == ["Event 'dropped' is not declared in this component's emits option."]
    assert found[0].range == types.Range(_position(template, "dropped"), _position(template, "dropped", 7))
    projection = browser_projection(template_document, _position(template, "$emit('drop", 1), project, documents)
    assert projection is not None
    # The copied component source also emits `drop-task`; replace the template expression.
    errors = _probed(tmp_path, projection.source, "\n$emit('drop-task', 1)\n", "\n__probe($emit)\n")
    assert any(message.startswith('Argument of type \'((event: "drop-task", id: number)') for message in errors), (
        errors
    )


_PARENT_TEMPLATE = (
    '<c-Lane @drop-task="move($event)" @closed="(a, b) => move(a)" @emptied="move($event)" '
    '@dropTask.once="move($event)" @drop-tsak="move($event)" @click="move($event)"></c-Lane>'
)
_PARENT_JS = "$component({ methods: { move(/** @type {unknown} */ value) {} } });\n"


def test_child_listener_names_are_checked(tmp_path):
    project, _javascript, template_document, documents = _project(tmp_path, _PARENT_TEMPLATE, _PARENT_JS)
    found = [
        item
        for item in browser_diagnostics(template_document, project, documents)
        if item.code == "citry.browser.undeclared-component-event"
    ]
    # `@click` may be a native event, and `@dropTask` matches `drop-task`.
    assert [(item.message, item.severity) for item in found] == [
        (
            "Component 'c-lane' does not declare event 'drop-tsak' in its emits option.",
            types.DiagnosticSeverity.Warning,
        )
    ]
    assert found[0].range == types.Range(
        _position(_PARENT_TEMPLATE, "@drop-tsak"), _position(_PARENT_TEMPLATE, "@drop-tsak", len("@drop-tsak"))
    )


@pytest.mark.parametrize(
    ("marker", "authored", "probe", "expected"),
    [
        ('move($event)" @closed', "move($event)", "__probe($event)", "{ taskId: number; }"),
        # A validator without parameters emits no values.
        ('move($event)" @dropTask', "move($event)", "__probe($event)", "undefined"),
        ('move($event)" @drop-tsak', "move($event)", "__probe($event)", "{ taskId: number; }"),
        # An undeclared event reaches the child's root element as a DOM event.
        ('move($event)"></c-Lane>', "move($event)", "__probe($event)", 'CitryDomEvent<"click">'),
        # Vue calls an inline function with the emitted values.
        ("(a, b)", "(a, b) => move(a)", "(a, b) => __probe([a, b])", "any[]"),
    ],
)
def test_child_listener_payload_types(tmp_path, marker, authored, probe, expected):
    project, _javascript, template_document, documents = _project(tmp_path, _PARENT_TEMPLATE, _PARENT_JS)
    projection = browser_projection(template_document, _position(_PARENT_TEMPLATE, marker, 1), project, documents)
    assert projection is not None
    assert "__citryChildEmits" in projection.owned_root_names
    errors = _probed(tmp_path, projection.source, f"\n{authored}\n", f"\n{probe}\n")
    assert _probe_message(expected) in errors, errors


def test_array_emits_type_declared_listeners_as_any_and_others_as_events(tmp_path):
    template = '<c-Lane @drop-task="move($event)" @click="move($event)"></c-Lane>'
    lane_js = "$component({ emits: ['drop-task'] });\n"
    project, _javascript, template_document, documents = _project(tmp_path, template, _PARENT_JS, lane_js=lane_js)
    for marker, expected in (('move($event)" @click', "any"), ('move($event)"></c', 'CitryDomEvent<"click">')):
        projection = browser_projection(template_document, _position(template, marker, 1), project, documents)
        assert projection is not None
        source = projection.source.replace("\nmove($event)\n", "\n__probe($event)\n", 1)
        errors = _type_errors(tmp_path, source)
        if expected == "any":
            # `any` is assignable to the probe's `null` parameter, so no error appears.
            assert not [message for message in errors if "parameter of type 'null'" in message], errors
        else:
            assert _probe_message(expected) in errors, errors
