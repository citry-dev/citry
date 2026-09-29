"""Vue Options members are typed and navigable from component JavaScript and templates."""

from __future__ import annotations

import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest
from lsprotocol import types

from citry_lsp.engine import DocumentState, browser_projection, declaration, definition, hover, references
from citry_lsp.project import load_project

# Each Options member kind the instance carries: props, inject, data(),
# setup(), computed, methods, a js_data() key, and a Citry helper.
_JS = """$component({
  props: { label: { type: String, required: true } },
  inject: ['theme'],
  data() { return { count: 1, open: false, seen: this.label.length + this.title.length }; },
  setup() { return { query: "" }; },
  computed: {
    double() { return this.count * 2; },
  },
  watch: { count() { this.toggle(); } },
  methods: {
    toggle() { this.open = !this.open; return this.open; },
    startDrag(/** @type {Event} */ event) { this.toggle(); this.label; this.theme; this.title; },
  },
  mounted() { this.startDrag(new Event('x')); },
  provide() { return { shared: this.count }; },
  onServerRender({ component }) { component.title; component.toggle(); },
});
"""

_TEMPLATE = (
    '<button @click="startDrag($event)" :title="label" v-if="open" '
    'v-text="count + double + query + theme + amount"></button>'
    '<template v-for="count in [1]"><span v-text="count"></span></template>'
)

_APP = """from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
class Card(Component):
    citry = engine
    template_file = 'card.html'
    js_file = 'card.js'
    class JsData:
        title: str
        amount: int
"""


def _position(source: str, marker: str, offset: int = 0) -> types.Position:
    before = source[: source.index(marker) + offset]
    return types.Position(before.count("\n"), len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2)


def _range_of(source: str, marker: str, offset: int, length: int) -> types.Range:
    return types.Range(_position(source, marker, offset), _position(source, marker, offset + length))


@lru_cache(maxsize=1)
def _repository_tsc() -> Path | None:
    """Find the repo-local TypeScript compiler when the Node workspace is installed."""
    repository = Path(__file__).resolve().parents[4]
    bin_dir = repository / "packages" / "js" / "citry-client" / "node_modules" / ".bin"
    names = ("tsc.cmd", "tsc.exe", "tsc") if os.name == "nt" else ("tsc",)
    return next((bin_dir / name for name in names if (bin_dir / name).is_file()), None)


# TypeScript reports the inferred type of each `__probe(read)` argument, which
# proves what hover and completion will show for that read.
_PROBE = "\n/** @param {null} value */\nfunction __probe(value) {}\n"


def _probe_message(expected: str) -> str:
    return f"Argument of type '{expected}' is not assignable to parameter of type 'null'."


def _type_errors(tmp_path: Path, source: str) -> list[str]:
    """Type-check one projection and return each error message."""
    tsc = _repository_tsc()
    if tsc is None:
        pytest.skip("repo-local tsc is unavailable; install the Node workspace for this integration check")
    checked = tmp_path / "projection.js"
    checked.write_text(source + _PROBE, encoding="utf-8")
    result = subprocess.run(
        [
            str(tsc),
            "--ignoreConfig",
            "--noEmit",
            "--strict",
            "--allowJs",
            "--checkJs",
            "--moduleResolution",
            "bundler",
            "--module",
            "preserve",
            "--target",
            "es2022",
            "--pretty",
            "false",
            str(checked),
        ],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
    )
    return re.findall(r"projection\.js\(\d+,\d+\): error TS\d+: (.*)", result.stdout + result.stderr)


@pytest.fixture
def card(tmp_path):
    (tmp_path / "card.js").write_text(_JS, encoding="utf-8")
    (tmp_path / "card.html").write_text(_TEMPLATE, encoding="utf-8")
    (tmp_path / "app.py").write_text(_APP, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready
    javascript = DocumentState((tmp_path / "card.js").as_uri(), "javascript", _JS, 1)
    template = DocumentState((tmp_path / "card.html").as_uri(), "citry-html", _TEMPLATE, 1)
    for document in (javascript, template):
        document.update(document.source, 1, project)
    documents = {javascript.uri: javascript, template.uri: template}
    return tmp_path, project, javascript, template, documents


_ALL_MEMBERS = {
    "data": ("this.count", "number"),
    "setup": ("this.query", "string"),
    "computed": ("this.double", "number"),
    "method": ("this.toggle()", "boolean"),
    "prop": ("this.label", "string"),
    "inject": ("this.theme", "unknown"),
    "js_data": ("this.title", "string"),
    "helper": ("this.$loading()", "boolean"),
}


@pytest.mark.parametrize(
    ("body_start", "probes"),
    [
        # Methods, hooks, watch handlers and provide() see every member kind,
        # including js_data() keys and Citry's helpers.
        ("startDrag(/** @type {Event} */ event) {", _ALL_MEMBERS),
        ("mounted() {", _ALL_MEMBERS),
        ("watch: { count() {", _ALL_MEMBERS),
        ("provide() {", _ALL_MEMBERS),
        ("double() {", {"data": ("this.count", "number"), "js_data": ("this.title", "string")}),
        # data() sees what exists before it runs: props, injections, js_data()
        # keys and helpers.
        (
            "data() {",
            {
                "prop": ("this.label", "string"),
                "inject": ("this.theme", "unknown"),
                "js_data": ("this.title", "string"),
                "helper": ("this.$loading()", "boolean"),
            },
        ),
        # The Options form types the initializer's `component` as the same instance.
        (
            "onServerRender({ component }) {",
            {
                name: (read.replace("this.", "component.", 1), expected)
                for name, (read, expected) in _ALL_MEMBERS.items()
            },
        ),
    ],
)
def test_options_functions_see_the_full_instance(card, body_start, probes):
    tmp_path, project, javascript, _template, documents = card
    projection = browser_projection(javascript, _position(_JS, body_start, 1), project, documents)
    assert projection is not None
    reads = "".join(f"__probe({read});" for read, _expected in probes.values())
    source = projection.source.replace(body_start, body_start + reads, 1)
    errors = _type_errors(tmp_path, source)
    for name, (_read, expected) in probes.items():
        assert _probe_message(expected) in errors, (name, errors)
    # Nothing the component declares reads as missing.
    assert not [message for message in errors if "does not exist on type" in message], errors


def test_template_names_take_the_instance_types(card):
    tmp_path, project, _javascript, template, documents = card
    authored = "count + double + query + theme + amount"
    projection = browser_projection(template, _position(_TEMPLATE, "count + double", 2), project, documents)
    assert projection is not None
    expected = {
        "count": "number",
        "double": "number",
        "query": "string",
        "theme": "unknown",
        "startDrag": "(event: Event) => void",
        "label": "string",
        # `open` is also a browser global; the component's name must win.
        "open": "boolean",
    }
    reads = ", ".join(f"__probe({name})" for name in expected)
    source = projection.source.replace(authored, reads, 1)
    assert source != projection.source
    errors = _type_errors(tmp_path, source)
    for name, type_source in expected.items():
        assert _probe_message(type_source) in errors, (name, errors)
    assert not [message for message in errors if "Cannot find name" in message], errors
    # The generated helper is never offered as a template name.
    assert "__citryComponentSource" in projection.owned_root_names


def test_options_member_navigation(card):
    tmp_path, project, javascript, template, documents = card
    js_uri = javascript.uri
    app_uri = (tmp_path / "app.py").as_uri()
    title_field = types.Location(app_uri, _range_of(_APP, "title: str", 0, 5))
    prop_declaration = types.Location(js_uri, _range_of(_JS, "label: {", 0, 5))
    inject_declaration = types.Location(js_uri, _range_of(_JS, "'theme'", 0, 7))

    # Props and injections: the JavaScript provider only reaches Citry's
    # generated declaration, so Citry maps the read to the authored entry.
    for marker, target in (
        ("this.label; this.theme", prop_declaration),
        ("this.theme; this.title", inject_declaration),
    ):
        position = _position(_JS, marker, len("this.") + 1)
        assert definition(javascript, position, project, documents) == target, marker
        assert declaration(javascript, position, project, documents) == target, marker

    # A js_data() key read through `this` or `component` opens the Python field
    # and gets Citry's hover, so the JavaScript provider does not also answer.
    for marker in ("this.title; }", "component.title;"):
        position = _position(_JS, marker, marker.index(".") + 2)
        assert definition(javascript, position, project, documents) == title_field, marker
        found = hover(javascript, position, project, documents)
        assert found is not None
        assert "(property) title: string" in found.contents.value
        assert "Citry JsData" in found.contents.value
        projection = browser_projection(javascript, position, project, documents)
        assert projection is not None
        assert projection.citry_owns_position
    title_references = references(
        javascript, _position(_JS, "this.title; }", 6), project, documents, include_declaration=True
    )
    assert title_references is not None
    assert title_field in title_references
    assert types.Location(js_uri, _range_of(_JS, "this.title; }", 5, 5)) in title_references
    assert types.Location(js_uri, _range_of(_JS, "component.title;", 10, 5)) in title_references

    # data(), setup(), computed and methods resolve inside the authored Options
    # object, where the JavaScript provider answers them itself.
    count_read = _position(_JS, "this.count * 2", 6)
    assert definition(javascript, count_read, project, documents) is None
    projection = browser_projection(javascript, count_read, project, documents)
    assert projection is not None
    assert not projection.citry_owns_position

    # A template name opens the Options entry that declares it.
    for marker, target_marker, length in (
        ("startDrag($event)", "startDrag(/**", len("startDrag")),
        ('label" v-if', "label: {", len("label")),
        ('open" v-text', "open: false", len("open")),
        ("count + double", "count: 1", len("count")),
        ("double + query", "double() {", len("double")),
        ("query + theme", 'query: ""', len("query")),
        ("theme + amount", "'theme'", len("'theme'")),
    ):
        target = types.Location(js_uri, _range_of(_JS, target_marker, 0, length))
        assert definition(template, _position(_TEMPLATE, marker, 1), project, documents) == target, marker
    # A js_data() key keeps its Python origin, and a loop binding shadows the member.
    amount = definition(template, _position(_TEMPLATE, "amount", 1), project, documents)
    assert amount == types.Location(app_uri, _range_of(_APP, "amount: int", 0, 6))
    loop_use = definition(template, _position(_TEMPLATE, 'v-text="count"', len('v-text="c')), project, documents)
    assert isinstance(loop_use, types.Location)
    assert loop_use.uri == template.uri


def test_shared_template_keeps_unknown_names(tmp_path):
    (tmp_path / "card.html").write_text('<p v-text="count"></p>', encoding="utf-8")
    (tmp_path / "card.js").write_text("$component({ data() { return { count: 1 }; } });\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        """from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
class First(Component):
    citry = engine
    template_file = 'card.html'
    js_file = 'card.js'
class Second(Component):
    citry = engine
    template_file = 'card.html'
    js_file = 'card.js'
""",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    template_source = '<p v-text="count"></p>'
    template = DocumentState((tmp_path / "card.html").as_uri(), "citry-html", template_source, 1)
    template.update(template_source, 1, project)
    projection = browser_projection(template, _position(template_source, "count", 1), project)
    assert projection is not None
    # Two components may infer different types, so no single instance is claimed.
    assert "CitryTemplateInstance" not in projection.source
    assert "/** @type {unknown} */\nvar count;" in projection.source
    # Navigation still reaches the one shared declaration.
    target = definition(template, _position(template_source, "count", 1), project)
    declared = types.Range(types.Position(0, 31), types.Position(0, 36))
    assert target == types.Location((tmp_path / "card.js").as_uri(), declared)


def test_inline_python_component_navigates_like_standalone_files(tmp_path):
    source = '''from citry import Citry, Component
engine = Citry(autodiscover=False)

class Options(Component):
    citry = engine
    class JsData:
        title: str
    template = """
      <button @click="toggle()" v-text="count + label"></button>
    """
    js = """
      $component({
        props: { label: String },
        data() { return { count: 1 }; },
        methods: {
          toggle() {
            this.count += this.label.length;
            return this.title;
          },
        },
      });
    """
'''
    path = tmp_path / "app.py"
    path.write_text(source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready
    document = DocumentState(path.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    def target(marker: str) -> types.Location:
        return types.Location(document.uri, _range_of(source, marker, 0, len(marker.split(":")[0].split("(")[0])))

    assert definition(document, _position(source, "this.title", 6), project) == target("title: str")
    assert definition(document, _position(source, "this.label", 6), project) == target("label: String")
    assert definition(document, _position(source, "count + label", 1), project) == target("count: 1")
    assert definition(document, _position(source, 'toggle()"', 1), project) == target("toggle() {")
    assert definition(document, _position(source, 'label"', 1), project) == target("label: String")
