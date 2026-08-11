"""Tests for diagnostics and narrow editor intelligence."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pytest
from lsprotocol import types

import citry_lsp.engine as engine_module
from citry import Citry, Component, ComponentLibrary, LibraryComponent, SlotInput, TemplateAnalysis
from citry_core.template_parser import CITRY_DIRECTIVE_NAMES, RESERVED_TAG_NAMES, STRUCTURAL_TAG_ATTRIBUTE_NAMES
from citry_lsp.catalog import CatalogIndex, FieldRecord
from citry_lsp.engine import (
    _CITRY_SYNTAX,
    _STRUCTURAL_ATTRIBUTES,
    _STRUCTURAL_TAG_SPECS,
    DocumentState,
    HtmlProjection,
    TemplateVariableHover,
    _field_definition_location,
    _open_document_source,
    _template_data_fields,
    all_expression_shadows,
    browser_diagnostics,
    browser_projection,
    completion_items,
    completion_result,
    declaration,
    definition,
    document_symbols,
    expression_shadows,
    hover,
    html_projection,
    references,
    render_template_variable_hover,
    semantic_dependencies,
    template_lint_diagnostics,
)
from citry_lsp.project import ProjectState, load_project
from citry_lsp.protocol import ProjectStatus

_DEFINITION_ENGINE = Citry(autodiscover=False)


class DefinitionCard(Component):
    citry = _DEFINITION_ENGINE
    template = """
    <article>Definition target</article>
    """

    class Kwargs:
        title: str

    class Slots:
        body: SlotInput[dict[str, object]]


class TemplateDataCard(Component):
    citry = _DEFINITION_ENGINE
    template = """
    <article c-title="template_user" #c-key="template_user">
      {{ template_user }}
      <div c-for="row in items">{{ row }} {{ row.upper }} {{ shared_count }}</div>
      {{ template_user.upper }} {{ café }}
    </article>
    """

    class TemplateData:
        template_user: str
        items: list[str]
        shared_count: int
        café: str  # noqa: PLC2401 - intentional NFKC identifier coverage


class TemplateDataChild(TemplateDataCard):
    class TemplateData:
        child_only: bool


class ExpressionCompletionForm(Component):
    """Exercise a complete form-shaped schema through ordinary typing states."""

    citry = _DEFINITION_ENGINE

    class TemplateData:
        form_id: str
        action: str | None
        method: str | None
        enctype: str | None
        target: str | None
        autocomplete: str | None
        disabled: bool
        readonly: bool
        submitting: bool
        novalidate: bool
        aria_busy: str | None
        attrs: dict[str, object]

    template = """
    <form data-label="😀" c-action="action">
      {{ action }}
    </form>
    """


class TemplateDataLibraryBase(LibraryComponent):
    template = "{{ library_title }}"

    class TemplateData:
        library_title: str


class TemplateDataLibraryCard(TemplateDataLibraryBase):
    pass


_DEFINITION_ENGINE.register_library(
    ComponentLibrary("lsp-template-data", (TemplateDataLibraryCard,)),
)


class Title(Component):
    citry = _DEFINITION_ENGINE
    template = "<span>Title component</span>"


class _CardBodySlotData:
    row: str
    index: int


@lru_cache(maxsize=1)
def _registry_state() -> ProjectState:
    """Build the immutable registry fixture once for this test process."""
    engine = Citry(autodiscover=False)

    class Card(Component):
        """Render a documented card."""

        citry = engine
        template = '<article><c-slot name="body" /></article>'

        class Kwargs:
            title: str
            count: int = 0
            required: bool = False

        class Slots:
            body: SlotInput[_CardBodySlotData]

    catalog = CatalogIndex(engine.inspect_components(include_builtins=True).to_dict())
    return ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="app:engine",
            mode="registry",
            registry_ready=True,
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
        ),
        engine.template_analysis(),
        catalog,
    )


@lru_cache(maxsize=1)
def _component_matching_state() -> ProjectState:
    """Reuse the small component-name catalog across matching cases."""
    engine = Citry(autodiscover=False)

    class CForm(Component):
        citry = engine
        template = "<form></form>"

    catalog = CatalogIndex(engine.inspect_components(include_builtins=False).to_dict())
    return ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="app:engine",
            mode="registry",
            registry_ready=True,
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
        ),
        engine.template_analysis(),
        catalog,
    )


def _syntax_state() -> ProjectState:
    return ProjectState(ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="syntax-only"))


@lru_cache(maxsize=1)
def _definition_catalog() -> CatalogIndex:
    """Inspect the module-owned definition registry once for all navigation cases."""
    return CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())


@lru_cache(maxsize=1)
def _definition_analysis() -> TemplateAnalysis:
    """Build parser rules once because ProjectState treats the analysis as immutable."""
    return _DEFINITION_ENGINE.template_analysis()


def _document(source: str, project: ProjectState, *, language_id: str = "citry-html") -> DocumentState:
    document = DocumentState("file:///template.html", language_id, source, 1)
    document.update(source, 1, project)
    return document


def _position(source: str, marker: str, offset: int = 0) -> types.Position:
    index = source.index(marker) + offset
    before = source[:index]
    return types.Position(before.count("\n"), len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2)


def test_html_projection_extracts_parser_proven_nested_templates_with_exact_ranges():
    project = _syntax_state()
    source = "<c-card c-body=\"<>😀<label for='email'>Email</label></>\" />"
    document = _document(source, project)

    projection = html_projection(document, _position(source, "email", 2), project)

    assert isinstance(projection, HtmlProjection)
    assert projection.source == "😀<label for='email'>Email</label>"
    assert projection.position == _position(projection.source, "email", 2)
    assert projection.source_range == types.Range(
        _position(source, "😀"),
        _position(source, "</>"),
    )
    assert projection.virtual_range == types.Range(
        types.Position(0, 0),
        _position(projection.source, projection.source, len(projection.source)),
    )


def test_html_projection_extracts_a_rooted_nested_template_without_a_fragment_envelope():
    project = _syntax_state()
    source = "<c-card c-body=\"<section><input type='email' /></section>\" />"

    projection = html_projection(_document(source, project), _position(source, "email", 2), project)

    assert projection is not None
    assert projection.source == "<section><input type='email' /></section>"
    assert projection.source_range == types.Range(
        _position(source, "<section>"),
        _position(source, "</section>", len("</section>")),
    )


def test_html_projection_maps_nested_templates_inside_indented_python_literals():
    project = _syntax_state()
    source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template = """\n'
        '      <c-card c-body="<>\n'
        "        <input type='email' />\n"
        '      </>" />\n'
        '    """\n'
    )
    document = _document(source, project, language_id="python")

    projection = html_projection(document, _position(source, "email", 2), project)

    assert projection is not None
    assert projection.source == "\n        <input type='email' />\n"
    assert projection.source_range == types.Range(
        _position(source, '<c-card c-body="<>', len('<c-card c-body="<>')),
        _position(source, "      </>"),
    )


def test_html_projection_preserves_crlf_and_utf16_inside_nested_templates():
    project = _syntax_state()
    source = "<c-card\r\n  c-body=\"<>\r\n    😀<input type='email' />\r\n  </>\"\r\n/>"
    document = _document(source, project)

    projection = html_projection(document, _position(source, "email", 2), project)

    assert projection is not None
    assert projection.source == "\r\n    😀<input type='email' />\r\n  "
    assert projection.position == _position(projection.source, "email", 2)
    assert projection.source_range == types.Range(
        _position(source, "<>\r\n", 2),
        _position(source, "</>"),
    )


@pytest.mark.parametrize(
    ("source", "marker", "expected_tag", "expected_attribute"),
    [
        (
            '<c-element is="form" c-action="submit" class="card"></c-element>',
            "c-action",
            "form",
            'c-action="submit" class="card"',
        ),
        (
            '<c-Element IS="FORM" c-action="submit" class="card"></c-Element>',
            "c-action",
            "form",
            'c-action="submit" class="card"',
        ),
        (
            '<c-element c-is="tag" c-class="card"></c-element>',
            "c-class",
            "x-element",
            'c-class="card"',
        ),
        (
            '<c-element c-IS="tag" c-class="card"></c-element>',
            "c-class",
            "x-element",
            'c-class="card"',
        ),
        (
            '<c-element is="form" c-bind="attrs" class="card"></c-element>',
            "class",
            "x-element",
            'class="card"',
        ),
        (
            '<c-element is="blockquote" class="quote"></c-element>',
            "class",
            "x-element",
            'class="quote"',
        ),
    ],
)
def test_html_projection_uses_static_c_element_targets_only_when_same_length_mapping_is_proven(
    source: str,
    marker: str,
    expected_tag: str,
    expected_attribute: str,
):
    project = _syntax_state()
    projection = html_projection(_document(source, project), _position(source, marker, 2), project)

    assert projection is not None
    assert projection.source.startswith(f"<{expected_tag}")
    assert projection.source.rstrip().endswith(f"{expected_attribute}>")
    assert 'is="' not in projection.source
    assert "c-is=" not in projection.source
    assert "c-bind=" not in projection.source
    assert len(projection.source) == len(source[: source.index(">") + 1])


def test_html_projection_leaves_c_element_selection_attributes_to_citry():
    project = _syntax_state()
    source = '<c-element is="form" c-action="submit"></c-element>'
    document = _document(source, project)

    assert html_projection(document, _position(source, 'is="form"', 1), project) is None
    assert html_projection(document, _position(source, "c-element", 2), project) is None


def test_html_projection_prefers_a_nested_c_element_start_tag():
    project = _syntax_state()
    source = "<c-card c-body=\"<>😀<c-element is='button' c-disabled='busy'>Go</c-element></>\" />"
    document = _document(source, project)

    projection = html_projection(document, _position(source, "c-disabled", 3), project)

    assert projection is not None
    assert projection.source.startswith("<button")
    assert projection.source.rstrip().endswith("c-disabled='busy'>")
    assert " is=" not in projection.source
    assert projection.source_range == types.Range(
        _position(source, "<c-element"),
        _position(source, ">Go", 1),
    )


def test_html_projection_prefers_nested_html_over_its_c_element_host():
    project = _syntax_state()
    source = '<c-element is="div" c-body="<><input type=\'email\' /></>"></c-element>'

    projection = html_projection(_document(source, project), _position(source, "email", 2), project)

    assert projection is not None
    assert projection.source == "<input type='email' />"


def test_html_projection_refuses_a_non_linear_python_escape_map():
    project = _syntax_state()
    source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template = """<c-card c-body=\'<>'
        '<input title=\\"example\\" />'
        '</>\' />"""\n'
    )
    document = _document(source, project, language_id="python")

    assert html_projection(document, _position(source, "example", 2), project) is None


def test_html_projection_requires_the_current_parser_tree():
    project = _syntax_state()
    valid = "<c-card c-body=\"<><input type='email' /></>\" />"
    document = _document(valid, project)
    invalid = "<c-card c-body=\"<><input type='email' /></>\""
    document.update(invalid, 2, project)

    assert html_projection(document, _position(invalid, "email", 2), project) is None


def test_js_data_alpine_and_component_js_intelligence_share_exact_python_origins(tmp_path):
    template_source = (
        '<button @c-click="save" @c-blur="missing" '
        'x-text="title.toUpperCase() + notice.toUpperCase() + ready.valueOf() + disabled1 + '
        '$state.progress.toFixed()" '
        "@click=\"sendEvent('save'); $sendEvent('save'); sendEvent('missing'); "
        "$loading('missing'); $error()\"></button>"
        '<template x-for="color in colors"><span x-text="color.toUpperCase()"></span></template>'
    )
    js_source = (
        "$component({\n"
        "  props: { label: { type: String, required: true }, page: { type: Number, default: null } },\n"
        "  init({ data, scope, props, state, sendEvent, loading, error }) {\n"
        "    scope.notice = data.title; Object.assign(scope, { ready: true });\n"
        "    data.title.toUpperCase(); scope.count.toFixed(); scope.notice.toUpperCase();\n"
        "    props.label.toUpperCase(); state.progress.toFixed();\n"
        "    sendEvent('save'); sendEvent('missing'); loading('missing'); error();\n"
        "  },\n"
        "});\n"
    )
    template_file = tmp_path / "card.html"
    js_file = tmp_path / "card.js"
    app_file = tmp_path / "app.py"
    template_file.write_text(template_source, encoding="utf-8")
    js_file.write_text(js_source, encoding="utf-8")
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    js_file = 'card.js'\n"
        "    class JsData:\n"
        "        title: str\n"
        "        count: int\n"
        "        invalid: set[str]\n"
        "        colors: list[str]\n"
        "    class State:\n"
        "        progress: int\n"
        "        secret: str\n"
        "        _public = ('progress',)\n"
        "    class Events:\n"
        "        def save(self):\n"
        "            pass\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    template = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    javascript = DocumentState(js_file.as_uri(), "javascript", js_source, 1)
    python = DocumentState(app_file.as_uri(), "python", app_source, 1)
    for document in (template, javascript, python):
        document.update(document.source, document.version, project)
    documents = {document.uri: document for document in (template, javascript, python)}

    root_items = completion_items(template, _position(template_source, "title", 2), project, documents)
    assert [item.label for item in root_items] == ["title"]
    root_hover = hover(template, _position(template_source, "title", 2), project, documents)
    assert root_hover is not None
    assert "(variable) title: string" in root_hover.contents.value
    title_target = definition(template, _position(template_source, "title", 2), project, documents)
    assert isinstance(title_target, types.Location)
    assert title_target.uri == app_file.as_uri()
    assert title_target.range.start.line == 8

    state_hover = hover(
        template,
        _position(template_source, "$state.progress", len("$state.pro")),
        project,
        documents,
    )
    assert state_hover is not None
    assert "(property) progress: number" in state_hover.contents.value
    state_target = definition(
        template,
        _position(template_source, "$state.progress", len("$state.pro")),
        project,
        documents,
    )
    assert isinstance(state_target, types.Location)
    assert state_target.uri == app_file.as_uri()
    assert state_target.range.start.line == 13

    loop_declaration = _position(template_source, 'x-for="color', len('x-for="co'))
    loop_use = _position(template_source, "color.to", len("color"))
    loop_hover = hover(template, loop_use, project, documents)
    assert loop_hover is not None
    assert "(variable) color: string" in loop_hover.contents.value
    declaration_hover = hover(template, loop_declaration, project, documents)
    assert declaration_hover is not None
    assert "(variable) color: string" in declaration_hover.contents.value
    loop_target = definition(template, loop_use, project, documents)
    assert isinstance(loop_target, types.Location)
    assert loop_target.uri == template_file.as_uri()
    assert loop_target.range == declaration_hover.range
    loop_references = references(
        template,
        loop_use,
        project,
        documents,
        include_declaration=True,
    )
    assert loop_references is not None
    assert len(loop_references) == 2

    js_title_target = definition(javascript, _position(js_source, "data.title", len("data.ti")), project, documents)
    assert js_title_target == title_target
    scope_target = definition(
        template,
        _position(template_source, "notice.to", len("notice")),
        project,
        documents,
    )
    assert isinstance(scope_target, types.Location)
    assert scope_target.uri == js_file.as_uri()
    assert scope_target.range.start.line == 3
    scope_hover = hover(
        template,
        _position(template_source, "notice.to", len("notice")),
        project,
        documents,
    )
    assert scope_hover is not None
    assert "notice: string" in scope_hover.contents.value
    js_references = references(
        javascript,
        _position(js_source, "data.title", len("data.ti")),
        project,
        documents,
        include_declaration=True,
    )
    assert js_references is not None
    assert {location.uri for location in js_references} == {js_file.as_uri(), app_file.as_uri()}

    template_projection = browser_projection(
        template,
        _position(template_source, "title.to", len("title.to")),
        project,
        documents,
    )
    assert template_projection is not None
    assert "var title;" in template_projection.source
    assert "function $provide(key, value)" in template_projection.source
    assert template_projection.owned_root_names == (
        "title",
        "count",
        "invalid",
        "colors",
        "notice",
        "ready",
    )
    loop_projection = browser_projection(template, loop_use, project, documents)
    assert loop_projection is not None
    assert "/** @type {string} */\nvar color;" in loop_projection.source
    js_projection = browser_projection(
        javascript,
        _position(js_source, "data.title", len("data.title")),
        project,
        documents,
    )
    assert js_projection is not None
    assert "var title;" not in js_projection.source
    assert "label: string" in js_projection.source
    assert "page: number | null" in js_projection.source
    assert "notice?: string" in js_projection.source
    assert "ready?: boolean" in js_projection.source
    assert "@typedef {{progress: number}} CitryEventsState" in js_projection.source
    assert "function((" not in js_projection.source
    assert "/** @typedef {Object} CitryEventError" in js_projection.source
    assert "function $component(definition)" in js_projection.source
    assert "function $provide(key, value)" not in js_projection.source
    assert "secret" not in js_projection.source
    assert js_projection.citry_owns_position

    template_state_projection = browser_projection(
        template,
        _position(template_source, "$state.progress", len("$state.pro")),
        project,
        documents,
    )
    assert template_state_projection is not None
    assert template_state_projection.citry_owns_position
    callback_state_target = definition(
        javascript,
        _position(
            js_source,
            "props.label.toUpperCase(); state.progress",
            len("props.label.toUpperCase(); state.pro"),
        ),
        project,
        documents,
    )
    assert callback_state_target == state_target

    magic_hover = hover(
        template,
        _position(template_source, "$loading", len("$load")),
        project,
        documents,
    )
    assert magic_hover is not None
    assert "(function) $loading" in magic_hover.contents.value
    assert "https://citry.dev/reference/browser-apis/#loading" in magic_hover.contents.value
    send_event_magic_hover = hover(
        template,
        _position(template_source, "$sendEvent", len("$send")),
        project,
        documents,
    )
    assert send_event_magic_hover is not None
    assert "(function) $sendEvent" in send_event_magic_hover.contents.value
    assert "https://citry.dev/reference/browser-apis/#send-event" in send_event_magic_hover.contents.value
    component_hover = hover(
        javascript,
        _position(js_source, "$component", len("$comp")),
        project,
        documents,
    )
    assert component_hover is not None
    assert "(function) $component" in component_hover.contents.value
    assert "https://citry.dev/reference/browser-apis/#component" in component_hover.contents.value
    context_hover = hover(
        javascript,
        _position(js_source, "props.label", len("pro")),
        project,
        documents,
    )
    assert context_hover is not None
    assert "(parameter) props: Readonly<CitryClientProps>" in context_hover.contents.value
    assert "https://citry.dev/reference/browser-apis/#component" in context_hover.contents.value
    send_event_context_hover = hover(
        javascript,
        _position(js_source, "sendEvent('save", len("send")),
        project,
        documents,
    )
    assert send_event_context_hover is not None
    assert "(function) sendEvent" in send_event_context_hover.contents.value
    assert "https://citry.dev/reference/browser-apis/#component" in send_event_context_hover.contents.value
    props_projection = browser_projection(
        javascript,
        _position(js_source, "props.label", len("pro")),
        project,
        documents,
    )
    assert props_projection is not None
    assert props_projection.citry_owns_position

    loading_items = completion_items(
        template,
        _position(template_source, "$loading('missing", len("$loading('")),
        project,
        documents,
    )
    assert [item.label for item in loading_items] == ["save"]
    assert loading_items[0].text_edit is not None
    assert loading_items[0].text_edit.new_text == "save"
    callback_loading_items = completion_items(
        javascript,
        _position(js_source, "loading('missing", len("loading('")),
        project,
        documents,
    )
    assert [item.label for item in callback_loading_items] == ["save"]

    dynamic_props_source = js_source.replace(
        "{ label: { type: String, required: true }, page: { type: Number, default: null } }",
        "makeProps()",
    )
    dynamic_javascript = DocumentState(js_file.as_uri(), "javascript", dynamic_props_source, 2)
    dynamic_javascript.update(dynamic_props_source, 2, project)
    dynamic_documents = {**documents, dynamic_javascript.uri: dynamic_javascript}
    dynamic_projection = browser_projection(
        dynamic_javascript,
        _position(dynamic_props_source, "makeProps", 2),
        project,
        dynamic_documents,
    )
    assert dynamic_projection is not None
    assert "@typedef {Record<string, unknown>} CitryClientProps" in dynamic_projection.source

    template_codes = [finding.code for finding in browser_diagnostics(template, project, documents)]
    js_codes = [finding.code for finding in browser_diagnostics(javascript, project, documents)]
    python_codes = [finding.code for finding in browser_diagnostics(python, project, documents)]
    assert template_codes == [
        "citry.alpine.unknown-variable",
        "citry.browser.unknown-server-event",
        "citry.browser.unknown-server-event",
        "citry.browser.unknown-server-event",
    ]
    assert js_codes == [
        "citry.browser.unknown-server-event",
        "citry.browser.unknown-server-event",
    ]
    assert python_codes == ["citry.js-data.unsupported-type"]
    event_target = definition(
        javascript,
        _position(js_source, "'save'", 2),
        project,
        documents,
    )
    assert isinstance(event_target, types.Location)
    assert event_target.uri == app_file.as_uri()
    assert event_target.range.start.line == 17
    declarative_target = definition(
        template,
        _position(template_source, '@c-click="save', len('@c-click="sa')),
        project,
        documents,
    )
    assert declarative_target == event_target
    declarative_items = completion_items(
        template,
        _position(template_source, '@c-click="save', len('@c-click="sa')),
        project,
        documents,
    )
    assert [item.label for item in declarative_items] == ["save"]
    assert declarative_items[0].text_edit is not None
    assert declarative_items[0].text_edit.new_text == "save"
    declarative_hover = hover(
        template,
        _position(template_source, '@c-click="save', len('@c-click="sa')),
        project,
        documents,
    )
    assert declarative_hover is not None
    assert "(server event) save" in declarative_hover.contents.value


def test_static_component_props_report_contract_errors_and_navigate_to_child_js(tmp_path):
    template_source = (
        '<c-child $c-props="{ title: title, count: \'many\', extra: true }" /><c-child $c-props="{ title, ...{} }" />'
    )
    child_js = (
        "$component({\n"
        "  props: {\n"
        "    title: { type: String, required: true },\n"
        "    count: { type: Number, required: true },\n"
        "    enabled: { type: Boolean, required: true },\n"
        "  },\n"
        "  init() {},\n"
        "});\n"
    )
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Child(Component):\n"
        "    citry = engine\n"
        "    js_file = 'child.js'\n"
        "    template = '<span></span>'\n"
        "class Parent(Component):\n"
        "    citry = engine\n"
        "    template_file = 'parent.html'\n"
        "    class JsData:\n"
        "        title: str\n"
    )
    template_file = tmp_path / "parent.html"
    child_js_file = tmp_path / "child.js"
    app_file = tmp_path / "app.py"
    template_file.write_text(template_source, encoding="utf-8")
    child_js_file.write_text(child_js, encoding="utf-8")
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    template = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    javascript = DocumentState(child_js_file.as_uri(), "javascript", child_js, 1)
    python = DocumentState(app_file.as_uri(), "python", app_source, 1)
    for document in (template, javascript, python):
        document.update(document.source, document.version, project)
    documents = {document.uri: document for document in (template, javascript, python)}

    prop_findings = [
        finding
        for finding in browser_diagnostics(template, project, documents)
        if str(finding.code).startswith("citry.browser.")
    ]
    assert [finding.code for finding in prop_findings] == [
        "citry.browser.incompatible-component-prop",
        "citry.browser.unknown-component-prop",
        "citry.browser.missing-component-prop",
    ]
    assert "expects number" in prop_findings[0].message
    assert "extra" in prop_findings[1].message
    assert "enabled" in prop_findings[2].message

    key_position = _position(template_source, "title: title", 2)
    target = definition(template, key_position, project, documents)
    assert isinstance(target, types.Location)
    assert target.uri == child_js_file.as_uri()
    assert target.range.start.line == 2
    prop_hover = hover(template, key_position, project, documents)
    assert prop_hover is not None
    assert "(property) title: string" in prop_hover.contents.value


def test_component_js_unknown_variables_use_lint_globals_and_default_to_error(tmp_path):
    js_source = """
$component(({ data }) => {
  console.log(data.ready, configuredClient);
  scope.ready = data.ready;
});
"""
    js_file = tmp_path / "card.js"
    app_file = tmp_path / "app.py"
    js_file.write_text(js_source, encoding="utf-8")
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component, LintSettings\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False, "
        "lint=LintSettings(component_js_globals={'configuredClient': str}))\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    js_file = 'card.js'\n"
        "    class JsData:\n"
        "        ready: bool\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    javascript = DocumentState(js_file.as_uri(), "javascript", js_source, 1)
    python = DocumentState(app_file.as_uri(), "python", app_source, 1)
    for document in (javascript, python):
        document.update(document.source, document.version, project)
    documents = {document.uri: document for document in (javascript, python)}

    findings = browser_diagnostics(javascript, project, documents)
    projection = browser_projection(
        javascript,
        _position(js_source, "configuredClient", len("configured")),
        project,
        documents,
    )

    assert [(finding.code, finding.message, finding.severity) for finding in findings] == [
        (
            "citry.component-js.unknown-variable",
            "Component JavaScript variable 'scope' is not defined.",
            types.DiagnosticSeverity.Error,
        )
    ]
    assert findings[0].range == types.Range(
        start=_position(js_source, "scope.ready"),
        end=_position(js_source, "scope.ready", len("scope")),
    )
    assert projection is not None
    assert "/** @type {string} */\nvar configuredClient;" in projection.source


def test_inferred_js_data_tracks_kwargs_types_synchronized_source_and_invalid_literals(tmp_path):
    template_source = "<p x-text=\"submitting.valueOf() ? title.toUpperCase() : ''\"></p>"
    template_file = tmp_path / "card.html"
    app_file = tmp_path / "app.py"
    template_file.write_text(template_source, encoding="utf-8")
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class Kwargs:\n"
        "        submitting: bool = False\n"
        "    def js_data(self, kwargs: Kwargs, slots):\n"
        "        return {'title': 'Card', 'submitting': kwargs.submitting, 'invalid': {1, 2}}\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    template = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    python = DocumentState(app_file.as_uri(), "python", app_source, 1)
    for document in (template, python):
        document.update(document.source, document.version, project)
    documents = {template.uri: template, python.uri: python}

    items = completion_items(template, _position(template_source, "title", 2), project, documents)
    assert [item.label for item in items] == ["title"]
    submitting_hover = hover(template, _position(template_source, "submitting", 2), project, documents)
    assert submitting_hover is not None
    assert "(variable) submitting: boolean" in submitting_hover.contents.value
    projection = browser_projection(
        template,
        _position(template_source, "submitting.valueOf", len("submitting.value")),
        project,
        documents,
    )
    assert projection is not None
    assert "/** @type {boolean} */\nvar submitting;" in projection.source
    target = definition(template, _position(template_source, "title", 2), project, documents)
    assert isinstance(target, types.Location)
    assert target.uri == app_file.as_uri()
    assert target.range.start.line == 9
    diagnostics = browser_diagnostics(python, project, documents)
    assert [diagnostic.code for diagnostic in diagnostics] == ["citry.js-data.unsupported-type"]

    edited_source = app_source.replace("'title': 'Card'", "'renamed': 'Card'")
    edited_python = DocumentState(app_file.as_uri(), "python", edited_source, 2)
    edited_python.update(edited_source, 2, project)
    edited_documents = {template.uri: template, edited_python.uri: edited_python}

    assert completion_items(template, _position(template_source, "title", 2), project, edited_documents) == []
    assert definition(template, _position(template_source, "title", 2), project, edited_documents) is None


def test_css_file_completes_hovers_and_navigates_declared_css_data(tmp_path):
    css_source = ".card { height: var(--chart_height); width: var(--chart_height); }"
    css_file = tmp_path / "card.css"
    css_file.write_text(css_source, encoding="utf-8")
    app_source = (
        "from pathlib import Path\n"
        "from typing import Annotated\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    class CssData:\n"
        "        chart_height: Annotated[str, 'Rendered chart height.']\n"
        "    template = '<div class=\"card\"></div>'\n"
        "    css_file = 'card.css'\n"
    )
    app_file = tmp_path / "app.py"
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(css_file.as_uri(), "css", css_source, 1)
    document.update(css_source, 1, project)
    documents = {document.uri: document}

    partial = css_source.replace("--chart_height", "--cha", 1)
    partial_document = DocumentState(css_file.as_uri(), "css", partial, 2)
    partial_document.update(partial, 2, project)
    completions = completion_items(partial_document, _position(partial, "--cha", len("--cha")), project)
    assert [item.label for item in completions] == ["--chart_height"]
    assert completions[0].detail == "Citry CSS data · Python producer type: str"
    assert completions[0].text_edit == types.TextEdit(
        types.Range(_position(partial, "--cha"), _position(partial, "--cha", len("--cha"))),
        "--chart_height",
    )

    position = _position(css_source, "chart_height", 2)
    found_hover = hover(document, position, project, documents)
    assert found_hover is not None
    assert "--chart_height" in found_hover.contents.value
    assert "`Card.CssData.chart_height`: `str`" in found_hover.contents.value

    target = definition(document, position, project, documents)
    assert isinstance(target, types.Location)
    assert target.uri == app_file.as_uri()
    assert target.range.start.line == 7
    assert declaration(document, position, project, documents) == target
    found_references = references(document, position, project, documents, include_declaration=True)
    assert found_references is not None
    assert len(found_references) == 3


def test_inline_css_uses_inferred_hyphenated_css_data_key(tmp_path):
    source = (
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    def css_data(self, kwargs, slots):\n"
        "        return {'row-color': 'red'}\n"
        "    template = '<div class=\"card\"></div>'\n"
        '    css = """\n'
        "    .card { color: var(--row-color); }\n"
        '    """\n'
    )
    app_file = tmp_path / "app.py"
    app_file.write_text(source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(app_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    documents = {document.uri: document}
    position = _position(source, "--row-color", 3)

    found_hover = hover(document, position, project, documents)
    target = definition(document, position, project, documents)

    assert found_hover is not None
    assert "Card.css_data()" in found_hover.contents.value
    assert isinstance(target, types.Location)
    assert target.uri == app_file.as_uri()
    assert target.range.start.line == 5


def test_shared_css_intersects_producers_and_unknown_custom_properties_remain_open(tmp_path):
    css_source = ".shared { color: var(--common); background: var(--only_a); border: var(--theme); }"
    css_file = tmp_path / "shared.css"
    css_file.write_text(css_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class A(Component):\n"
        "    citry = engine\n"
        "    class CssData:\n"
        "        common: str\n"
        "        only_a: str\n"
        "    template = '<div></div>'\n"
        "    css_file = 'shared.css'\n"
        "class B(Component):\n"
        "    citry = engine\n"
        "    class CssData:\n"
        "        common: int\n"
        "    template = '<div></div>'\n"
        "    css_file = 'shared.css'\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(css_file.as_uri(), "css", css_source, 1)
    document.update(css_source, 1, project)

    common = hover(document, _position(css_source, "common", 2), project)

    assert common is not None
    assert "`A.CssData.common`: `str`" in common.contents.value
    assert "`B.CssData.common`: `int`" in common.contents.value
    assert hover(document, _position(css_source, "only_a", 2), project) is None
    assert hover(document, _position(css_source, "theme", 2), project) is None


def test_css_data_uses_synchronized_schema_and_asset_ownership(tmp_path):
    css_source = ".card { color: var(--accent); background: var(--fresh); }"
    css_file = tmp_path / "card.css"
    css_file.write_text(css_source, encoding="utf-8")
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    class CssData:\n"
        "        accent: str\n"
        "    template = '<div></div>'\n"
        "    css_file = 'card.css'\n"
    )
    app_file = tmp_path / "app.py"
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    css_document = DocumentState(css_file.as_uri(), "css", css_source, 1)
    css_document.update(css_source, 1, project)
    edited = app_source.replace("accent: str", "fresh: int")
    python_document = DocumentState(app_file.as_uri(), "python", edited, 2)
    python_document.update(edited, 2, project)
    documents = {css_document.uri: css_document, python_document.uri: python_document}

    assert hover(css_document, _position(css_source, "accent", 2), project, documents) is None
    fresh = hover(css_document, _position(css_source, "fresh", 2), project, documents)
    assert fresh is not None
    assert "`Card.CssData.fresh`: `int`" in fresh.contents.value
    target = definition(css_document, _position(css_source, "fresh", 2), project, documents)
    assert isinstance(target, types.Location)
    assert target.range.start.line == 6

    moved = edited.replace("css_file = 'card.css'", "css_file = 'other.css'")
    moved_document = DocumentState(app_file.as_uri(), "python", moved, 3)
    moved_document.update(moved, 3, project)
    moved_documents = {css_document.uri: css_document, moved_document.uri: moved_document}
    assert hover(css_document, _position(css_source, "fresh", 2), project, moved_documents) is None


def test_template_lint_diagnostics_join_declared_roots_globals_and_component_metadata(tmp_path):
    template_file = tmp_path / "card.html"
    template_source = '<div c-title="title + framework_value">{{ site_name }} {{ typo }}</div>'
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False, "
        "template_globals={'site_name': 'Citry'})\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        title: str\n"
        "    class Lint:\n"
        "        template_variables = {'framework_value': str}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    diagnostics = template_lint_diagnostics(document, project, {document.uri: document})

    assert [(item.code, item.severity) for item in diagnostics] == [
        ("citry.template.unknown-variable", types.DiagnosticSeverity.Error)
    ]
    assert diagnostics[0].range == types.Range(
        _position(template_source, "typo"),
        _position(template_source, "typo", len("typo")),
    )


def test_runtime_globals_and_lint_metadata_complete_and_hover(tmp_path):
    template_file = tmp_path / "card.html"
    template_source = "{{ site_name }} {{ request }} {{ component_value }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_source = (
        "from pathlib import Path\n"
        "from typing import Annotated\n"
        "from citry import Citry, Component, LintSettings\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False, "
        "template_globals={'site_name': 'Citry'}, "
        "lint=LintSettings(template_variables={'request': Annotated[str, 'Current request.']}))\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class Lint:\n"
        "        template_variables = {'component_value': int}\n"
    )
    app_file = tmp_path / "app.py"
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}

    items = completion_items(
        document,
        _position(template_source, "site_name", len("site")),
        project,
        documents,
    )
    request_hint = hover(document, _position(template_source, "request", 2), project, documents)
    request_definition = definition(document, _position(template_source, "request", 2), project, documents)
    component_definition = definition(
        document,
        _position(template_source, "component_value", 2),
        project,
        documents,
    )

    assert {"site_name", "request", "component_value"} <= {item.label for item in items}
    assert request_hint is not None
    assert isinstance(request_hint.contents, types.MarkupContent)
    assert request_hint.contents.value == (
        "```python\n(variable) request: str\n```\n\nApplication lint metadata.\n\nCurrent request."
    )
    assert request_definition == types.Location(
        app_file.as_uri(),
        types.Range(
            _position(app_source, "'request'"),
            _position(app_source, "'request'", len("'request'")),
        ),
    )
    assert component_definition == types.Location(
        app_file.as_uri(),
        types.Range(
            _position(app_source, "'component_value'"),
            _position(app_source, "'component_value'", len("'component_value'")),
        ),
    )

    edited_app = app_source.replace("'component_value': int", "'other_value': int")
    open_app = DocumentState(app_file.as_uri(), "python", edited_app, 2)
    open_app.update(edited_app, 2, project)
    synchronized = {**documents, open_app.uri: open_app}
    assert (
        definition(
            document,
            _position(template_source, "component_value", 2),
            project,
            synchronized,
        )
        is None
    )


def test_template_lint_diagnostics_use_inferred_roots_and_warning_policy(tmp_path):
    template_file = tmp_path / "card.html"
    template_source = "{{ inferred }} {{ missing }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component, LintSettings\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False, "
        "lint=LintSettings(rule_unknown_template_variable='warning'))\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs, slots):\n"
        "        return {'inferred': 'yes'}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    diagnostics = template_lint_diagnostics(document, project, {document.uri: document})

    assert [(item.message, item.severity) for item in diagnostics] == [
        (
            "Template variable 'missing' is not available in this template.",
            types.DiagnosticSeverity.Warning,
        )
    ]
    assert diagnostics[0].code_description == types.CodeDescription(
        "https://citry.dev/ide/diagnostics/#citry.template.unknown-variable"
    )


def test_template_lint_diagnostics_do_not_run_without_registry_ownership():
    source = "{{ unknown }}"
    project = _syntax_state()
    document = _document(source, project)

    assert template_lint_diagnostics(document, project, {document.uri: document}) == ()


@pytest.mark.parametrize(
    "edited_source",
    [
        (
            "from pathlib import Path\n"
            "from citry import Citry, Component\n"
            "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
            "class Card(Component):\n"
            "    citry = engine\n"
            "    template_file = 'card.html'\n"
            "    class TemplateData:\n"
            "        title: str\n"
            "        added: str\n"
        ),
        "def invalid(\n",
    ],
)
def test_template_lint_diagnostics_decline_or_refresh_synchronized_schema_source(tmp_path, edited_source):
    template_file = tmp_path / "card.html"
    template_source = "{{ added }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        title: str\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    template_document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    template_document.update(template_source, 1, project)
    python_document = DocumentState(app_file.as_uri(), "python", edited_source, 2)
    python_document.update(edited_source, 2, project)
    documents = {
        template_document.uri: template_document,
        python_document.uri: python_document,
    }

    assert template_lint_diagnostics(template_document, project, documents) == ()


def test_syntax_diagnostic_uses_parser_code_and_exact_range():
    source = "😀<div>"
    document = _document(source, _syntax_state())

    assert len(document.diagnostics) == 1
    diagnostic = document.diagnostics[0]
    assert diagnostic.code == "citry.parse.syntax"
    assert diagnostic.code_description == types.CodeDescription(
        "https://citry.dev/ide/diagnostics/#citry.parse.syntax"
    )
    assert diagnostic.range.start.character >= 2


def test_python_comment_text_does_not_create_lsp_diagnostics():
    project = _syntax_state()

    for source in (
        "{{ user.name # show the person's name }}",
        "{{ x # } note }}",
        "{{ x # { note }}",
        '{{ x # say "}}" then stop }}',
    ):
        document = _document(source, project)

        assert document.diagnostics == (), source


def test_unknown_component_only_fires_in_registry_mode():
    source = "<c-ghost />"

    registry = _document(source, _registry_state())
    static = _document(source, _syntax_state())

    assert [item.code for item in registry.diagnostics] == ["citry.template.unknown-component"]
    assert registry.diagnostics[0].message == "Component <c-ghost> is not registered."
    assert registry.diagnostics[0].code_description == types.CodeDescription(
        "https://citry.dev/ide/diagnostics/#citry.template.unknown-component"
    )
    assert static.diagnostics == ()


def test_component_attribute_and_slot_completion():
    project = _registry_state()
    tag_source = "<c-ca"
    attr_source = "<c-card "
    slot_source = '<c-card><div></div><c-fill name="bo'

    tags = completion_items(_document(tag_source, project), _position(tag_source, "ca", 2), project)
    attrs = completion_items(_document(attr_source, project), _position(attr_source, " ", 1), project)
    slots = completion_items(_document(slot_source, project), _position(slot_source, "bo", 2), project)

    assert "c-card" in {item.label for item in tags}
    assert {"title", "count"} <= {item.label for item in attrs}
    assert "body" in {item.label for item in slots}

    card = next(item for item in tags if item.label == "c-card")
    assert card.filter_text == "c-card"
    assert isinstance(card.text_edit, types.InsertReplaceEdit)
    assert card.text_edit.insert == types.Range(types.Position(0, 1), types.Position(0, len(tag_source)))
    assert card.text_edit.replace == card.text_edit.insert


def test_fill_parent_ignores_component_text_in_comments_and_interpolations():
    project = _registry_state()
    sources = (
        '<c-card>{# <c-title> #}<c-fill name="bo',
        '<c-card><!-- <c-title> --><c-fill name="bo',
        '<c-card>{{ "<c-title>" }}<c-fill name="bo',
    )

    for source in sources:
        items = completion_items(_document(source, project), types.Position(0, len(source)), project)
        assert "body" in {item.label for item in items}


def test_nested_template_fill_keeps_its_inner_component_parent():
    project = _registry_state()
    source = "<c-unknown c-body=\"<><c-card><c-fill name='bo"

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert "body" in {item.label for item in items}


def test_syntax_only_completion_offers_authoritative_structural_tags():
    project = _syntax_state()
    source = "<c-"

    result = completion_result(_document(source, project), types.Position(0, len(source)), project)
    items = result.items

    assert {item.label for item in items} == set(RESERVED_TAG_NAMES)
    assert result.is_incomplete is True
    by_label = {item.label: item for item in items}
    expected_snippets = {
        "c-if": 'c-if cond="${1}">',
        "c-elif": 'c-elif cond="${1}">',
        "c-for": 'c-for each="${1}">',
        "c-fill": 'c-fill name="${1}">',
    }
    for label, item in by_label.items():
        expected = expected_snippets.get(label, f"{label}>")
        assert item.filter_text == label
        assert item.insert_text == expected
        assert item.insert_text_format == types.InsertTextFormat.Snippet
        assert isinstance(item.text_edit, types.InsertReplaceEdit)
        assert item.text_edit.new_text == expected
        assert item.text_edit.insert == types.Range(types.Position(0, 1), types.Position(0, len(source)))
        assert item.text_edit.replace == item.text_edit.insert


def test_structural_tag_completion_replaces_the_complete_token_around_cursor():
    project = _syntax_state()
    source = "<c-fooo>"
    cursor = types.Position(0, len("<c-fo"))

    result = completion_result(_document(source, project), cursor, project)

    item = next(candidate for candidate in result.items if candidate.label == "c-for")
    assert result.is_incomplete is True
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    token_range = types.Range(types.Position(0, 1), types.Position(0, len("<c-fooo")))
    assert item.text_edit.insert == token_range
    assert item.text_edit.replace == token_range
    assert item.text_edit.new_text == 'c-for each="${1}"'


def test_closing_structural_tag_completion_keeps_a_bare_name():
    project = _syntax_state()
    source = "<c-for></c-fooo>"
    cursor = types.Position(0, len("<c-for></c-fo"))

    result = completion_result(_document(source, project), cursor, project)

    item = next(candidate for candidate in result.items if candidate.label == "c-for")
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.insert_text == "c-for"
    assert item.insert_text_format == types.InsertTextFormat.PlainText
    assert item.text_edit.new_text == "c-for"
    token_range = types.Range(
        types.Position(0, len("<c-for></")),
        types.Position(0, len("<c-for></c-fooo")),
    )
    assert item.text_edit.insert == token_range
    assert item.text_edit.replace == token_range


def test_inline_python_tag_completion_maps_utf16_insert_and_replace_ranges():
    project = _syntax_state()
    source = 'from citry import Component\nclass Card(Component):\n    template = """😀<c-fooo>"""\n'
    cursor = _position(source, "<c-fo", len("<c-fo"))
    document = _document(source, project, language_id="python")

    result = completion_result(document, cursor, project)

    item = next(candidate for candidate in result.items if candidate.label == "c-for")
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    token_range = types.Range(
        _position(source, "<c-", 1),
        _position(source, "<c-fooo", len("<c-fooo")),
    )
    assert item.text_edit.insert == token_range
    assert item.text_edit.replace == token_range


@pytest.mark.parametrize(
    ("source", "label", "expected"),
    [
        ('<c-fooo each="item in items">', "c-for", "c-for"),
        ('<c-iff cond="ready">', "c-if", "c-if"),
        ('<c-filll c-name="slot">', "c-fill", "c-fill"),
        ('<c-filll c-bind="attrs">', "c-fill", "c-fill"),
    ],
)
def test_structural_tag_completion_preserves_existing_primary_attributes(source, label, expected):
    project = _syntax_state()
    cursor = types.Position(0, source.index(" "))

    result = completion_result(_document(source, project), cursor, project)

    item = next(candidate for candidate in result.items if candidate.label == label)
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.text_edit.new_text == expected


@pytest.mark.parametrize(
    "source",
    [
        '<c-filll {# name="fake" #}>',
        "<c-filll title='name=\"fake\"'>",
    ],
)
def test_structural_tag_completion_ignores_attribute_text_in_comments_and_values(source):
    project = _syntax_state()
    cursor = types.Position(0, len("<c-filll"))

    result = completion_result(_document(source, project), cursor, project)

    item = next(candidate for candidate in result.items if candidate.label == "c-fill")
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.text_edit.new_text == 'c-fill name="${1}"'


@pytest.mark.parametrize(
    "source",
    [
        "<c- {# body #}<div></div>",
        "<c- {# body #}{{ value }}",
        "<c- {# body #}",
    ],
)
def test_structural_tag_completion_closes_before_a_body_comment(source):
    project = _syntax_state()
    cursor = types.Position(0, len("<c-"))

    result = completion_result(_document(source, project), cursor, project)

    item = next(candidate for candidate in result.items if candidate.label == "c-fill")
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.text_edit.new_text == 'c-fill name="${1}">'


def test_registered_dotted_alias_completion_remains_live_after_the_dot():
    engine = Citry(autodiscover=False)

    class DottedAliasCard(Component):
        citry = engine
        template = """
        <article></article>
        """

    engine.register(DottedAliasCard, name="ui.card")
    catalog = CatalogIndex(engine.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        engine.template_analysis(),
        catalog,
    )
    source = "<c-ui.c"

    result = completion_result(_document(source, project), types.Position(0, len(source)), project)

    item = next(candidate for candidate in result.items if candidate.label == "c-ui.card")
    assert result.is_incomplete is True
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    expected_range = types.Range(types.Position(0, 1), types.Position(0, len(source)))
    assert item.text_edit.insert == expected_range
    assert item.text_edit.replace == expected_range


def test_structural_tag_completion_closes_before_a_trailing_template_newline():
    project = _syntax_state()
    source = "<c-\n"
    cursor = types.Position(0, len("<c-"))

    result = completion_result(_document(source, project), cursor, project)

    item = next(candidate for candidate in result.items if candidate.label == "c-for")
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.text_edit.new_text == 'c-for each="${1}">'


def test_nested_tag_completion_uses_the_current_dynamic_attribute():
    project = _syntax_state()
    source = '<c-card c-one="abc" c-body="<><c-'

    result = completion_result(_document(source, project), types.Position(0, len(source)), project)

    assert "c-for" in {item.label for item in result.items}


def test_tag_completion_declines_an_edit_across_implicit_python_literals():
    project = _syntax_state()
    source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        "    template = (\n"
        '        "<c-"  # keep split\n'
        '        "fooo>"\n'
        "    )\n"
    )
    cursor = _position(source, '"fo', len('"fo'))
    document = _document(source, project, language_id="python")

    result = completion_result(document, cursor, project)

    assert result.items == ()


def test_tag_completion_requires_a_real_template_tag_name_context():
    project = _registry_state()
    sources = (
        "{# <c- #}",
        "<!-- <c- -->",
        '<div title="<c-">x</div>',
        '<script>const x="<c-";</script>',
    )

    for source in sources:
        cursor = source.index("<c-") + len("<c-")
        items = completion_items(_document(source, project), types.Position(0, cursor), project)
        assert items == []


def test_closing_tag_completion_keeps_real_markup_context():
    project = _registry_state()
    source = "<c-if></c-"

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert set(RESERVED_TAG_NAMES) <= {item.label for item in items}


def test_registry_completion_unions_structural_and_registered_tags():
    project = _registry_state()
    source = "<c-"

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)
    labels = [item.label for item in items]

    assert set(RESERVED_TAG_NAMES) <= set(labels)
    assert {"c-card", "c-Card"} <= set(labels)
    assert len(labels) == len(set(labels))


def test_schema_free_directive_completion_uses_host_specific_snippets():
    project = _syntax_state()

    plain = completion_items(_document("<div ", project), types.Position(0, len("<div ")), project)
    component = completion_items(
        _document("<c-unknown ", project),
        types.Position(0, len("<c-unknown ")),
        project,
    )
    conditional = completion_items(
        _document("<c-if ", project),
        types.Position(0, len("<c-if ")),
        project,
    )
    fill = completion_items(
        _document("<c-card><c-fill ", project),
        types.Position(0, len("<c-card><c-fill ")),
        project,
    )
    slot = completion_items(
        _document("<c-slot ", project),
        types.Position(0, len("<c-slot ")),
        project,
    )
    dynamic_component = completion_items(
        _document("<c-component ", project),
        types.Position(0, len("<c-component ")),
        project,
    )

    plain_by_label = {item.label: item for item in plain}
    component_labels = {item.label for item in component}
    assert set(plain_by_label) == {
        "c-if",
        "c-elif",
        "c-else",
        "c-for",
        "c-empty",
        "c-bind",
        "#c-key",
        "#c-ignore",
    }
    assert plain_by_label["c-for"].insert_text == 'c-for="${1:item} in ${2:items}"'
    assert plain_by_label["#c-key"].insert_text == '#c-key="${1:key}"'
    assert {"$c-props", "c-$c-props"} <= component_labels
    component_by_label = {item.label: item for item in component}
    assert component_by_label["$c-props"].insert_text == '\\$c-props="${1:{}}"'
    assert component_by_label["c-$c-props"].insert_text == 'c-\\$c-props="${1:expression}"'
    assert {item.label for item in conditional} == {"cond"}
    assert {item.label for item in fill} == {"name", "c-name", "data", "fallback", "c-bind"}
    assert {"c-if", "c-elif", "c-else", "c-for", "c-empty"} <= {item.label for item in slot}
    assert not {"#c-key", "#c-ignore", "$c-props", "c-$c-props"} & {item.label for item in slot}
    assert len(dynamic_component) == len({item.label for item in dynamic_component})


@pytest.mark.parametrize(
    ("source", "label", "expected_new_text"),
    [
        ("<div c-ioops>", "c-if", 'c-if="${1:condition}"'),
        ('<div c-ioops = "ready">', "c-if", "c-if"),
        ("<c-card tiiitle>", "title", 'title="$1"'),
    ],
)
def test_attribute_completion_replaces_the_complete_token(source, label, expected_new_text):
    project = _registry_state()
    attribute_name = "c-ioops" if "c-ioops" in source else "tiiitle"
    cursor = _position(
        source,
        attribute_name,
        2 if attribute_name == "tiiitle" else len("c-i"),
    )

    result = completion_result(_document(source, project), cursor, project)

    assert result.is_incomplete is True
    item = next(candidate for candidate in result.items if candidate.label == label)
    token_range = types.Range(
        _position(source, attribute_name),
        _position(source, attribute_name, len(attribute_name)),
    )
    assert item.filter_text == label
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.text_edit.insert == token_range
    assert item.text_edit.replace == token_range
    assert item.text_edit.new_text == expected_new_text
    start = source.index(attribute_name)
    assert source[:start] + item.text_edit.new_text + source[start + len(attribute_name) :] == source.replace(
        attribute_name,
        expected_new_text,
        1,
    )


def test_attribute_completion_uses_a_zero_width_edit_after_whitespace():
    project = _syntax_state()
    source = "<div "
    cursor = types.Position(0, len(source))

    result = completion_result(_document(source, project), cursor, project)

    assert result.is_incomplete is True
    item = next(candidate for candidate in result.items if candidate.label == "c-if")
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.text_edit.insert == types.Range(cursor, cursor)
    assert item.text_edit.replace == types.Range(cursor, cursor)


@pytest.mark.parametrize(
    ("source", "partial", "label", "expected_new_text"),
    [
        ("<div #c-kooops>", "#c-kooops", "#c-key", '#c-key="${1:key}"'),
        ("<c-card $c-prooops>", "$c-prooops", "$c-props", '\\$c-props="${1:{}}"'),
        ("<c-slot requiired>", "requiired", "required", "required"),
        (
            '<c-card c-body="<div c-ioops></div>">',
            "c-ioops",
            "c-if",
            'c-if="${1:condition}"',
        ),
    ],
)
def test_attribute_completion_uses_atomic_edits_for_every_attribute_shape(
    source,
    partial,
    label,
    expected_new_text,
):
    project = _registry_state()
    cursor = _position(source, partial, max(1, len(partial) // 2))

    result = completion_result(_document(source, project), cursor, project)

    item = next(candidate for candidate in result.items if candidate.label == label)
    assert item.filter_text == label
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.text_edit.replace == types.Range(
        _position(source, partial),
        _position(source, partial, len(partial)),
    )
    assert item.text_edit.new_text == expected_new_text


def test_attribute_completion_excludes_only_the_active_attribute_token():
    project = _syntax_state()
    active = "c-if"

    current = completion_items(
        _document(f"<div {active}>", project),
        types.Position(0, len("<div c-i")),
        project,
    )
    duplicate = completion_items(
        _document(f'<div {active} c-if="ready">', project),
        types.Position(0, len("<div c-i")),
        project,
    )

    assert "c-if" in {item.label for item in current}
    assert "c-if" not in {item.label for item in duplicate}


@pytest.mark.parametrize(
    "source",
    [
        '<div title=" c-if " ',
        "<div title=c-if ",
        "<div {# c-if #} ",
        '<div {# " #} ',
    ],
)
def test_attribute_completion_ignores_names_and_quotes_in_values_and_comments(source):
    project = _syntax_state()

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert "c-if" in {item.label for item in items}


@pytest.mark.parametrize(
    "source",
    [
        '<div title="x\\" c-ioops></div>',
        "<div title='x\\' c-ioops></div>",
    ],
)
def test_attribute_completion_treats_backslashes_as_plain_html_value_text(source):
    project = _syntax_state()
    cursor = _position(source, "c-ioops", len("c-i"))

    result = completion_result(_document(source, project), cursor, project)

    c_if = next(item for item in result.items if item.label == "c-if")
    assert isinstance(c_if.text_edit, types.InsertReplaceEdit)
    assert c_if.text_edit.replace == types.Range(
        _position(source, "c-ioops"),
        _position(source, "c-ioops", len("c-ioops")),
    )


@pytest.mark.parametrize(
    ("source", "marker"),
    [
        ('<div title=" c-if ">', "c-if"),
        ("<div {# c-if #}>", "c-if"),
        ('<div title="x">', ">"),
    ],
)
def test_attribute_completion_stays_out_of_values_comments_and_tag_close(source, marker):
    project = _syntax_state()

    items = completion_items(_document(source, project), _position(source, marker), project)

    assert items == []


@pytest.mark.parametrize(
    ("source", "cursor"),
    [
        ('<div  title="x"></div>', len("<div")),
        ('<div title=x c-for="x in xs"></div>', len("<div title=x")),
    ],
)
def test_attribute_completion_does_not_insert_before_separator_whitespace(source, cursor):
    project = _syntax_state()

    result = completion_result(_document(source, project), types.Position(0, cursor), project)

    assert result.items == ()


def test_attribute_completion_maps_utf16_python_hosts_and_declines_split_literals():
    project = _syntax_state()
    direct = 'from citry import Component\nclass Card(Component):\n    template = """😀<div c-ioops>"""\n'
    direct_cursor = _position(direct, "c-ioops", len("c-i"))
    direct_document = DocumentState("file:///card.py", "python", direct, 1)
    direct_document.update(direct, 1, project)

    direct_result = completion_result(direct_document, direct_cursor, project)

    direct_item = next(candidate for candidate in direct_result.items if candidate.label == "c-if")
    assert isinstance(direct_item.text_edit, types.InsertReplaceEdit)
    assert direct_item.text_edit.replace == types.Range(
        _position(direct, "c-ioops"),
        _position(direct, "c-ioops", len("c-ioops")),
    )

    split = 'from citry import Component\nclass Card(Component):\n    template = "<div c-" "ioops>"\n'
    split_cursor = _position(split, "ioops", 1)
    split_document = DocumentState("file:///split.py", "python", split, 1)
    split_document.update(split, 1, project)

    split_result = completion_result(split_document, split_cursor, project)

    assert split_result.is_incomplete is True
    assert split_result.items == ()


def test_directive_completion_suppresses_existing_and_conflicting_controls():
    project = _syntax_state()
    source = '<div c-if="ready" #c-key="row.id" '

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)
    labels = {item.label for item in items}

    assert not {"c-if", "c-elif", "c-else"} & labels
    assert "#c-key" not in labels
    assert "c-for" in labels
    assert "c-bind" in labels


@pytest.mark.parametrize(
    ("source", "excluded"),
    [
        ('<c-component is="card" ', {"is", "c-is"}),
        ('<c-fill name="body" ', {"name", "c-name"}),
        ('<c-slot name="body" required ', {"name", "c-name", "required", "c-required"}),
        ('<div c-if="ready" ', {"c-if", "c-elif", "c-else", "c-empty"}),
        ("<div c-empty ", {"c-if", "c-elif", "c-else", "c-for", "c-empty"}),
    ],
)
def test_directive_completion_suppresses_parser_conflicts(source, excluded):
    project = _syntax_state()

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert not excluded & {item.label for item in items}


def test_component_completion_offers_and_ranks_class_spelling():
    project = _registry_state()
    lowercase_source = "<c-c"
    class_source = "<c-C"

    lowercase = completion_items(
        _document(lowercase_source, project),
        types.Position(0, len(lowercase_source)),
        project,
    )
    class_names = completion_items(
        _document(class_source, project),
        types.Position(0, len(class_source)),
        project,
    )

    lowercase_by_label = {item.label: item for item in lowercase}
    class_by_label = {item.label: item for item in class_names}
    assert {"c-card", "c-Card"} <= lowercase_by_label.keys()
    assert lowercase_by_label["c-card"].sort_text < lowercase_by_label["c-Card"].sort_text
    assert class_by_label["c-Card"].sort_text < class_by_label["c-card"].sort_text


@pytest.mark.parametrize(
    ("source", "expected_first", "expected_filter"),
    [
        ("<c-", "c-c-form", "c-c-form"),
        ("<c-c", "c-c-form", "c-c-form"),
        ("<c-C", "c-CForm", "c-CForm"),
        ("<c-c-f", "c-c-form", "c-c-form"),
        ("<c-form", "c-CForm", "c-form"),
        ("<c-cfo", "c-CForm", "c-cform"),
        ("<c-cform", "c-cform", "c-cform"),
    ],
)
def test_component_completion_server_filters_and_ranks_authored_spelling(
    source,
    expected_first,
    expected_filter,
):
    project = _component_matching_state()

    result = completion_result(_document(source, project), types.Position(0, len(source)), project)

    component_items = [item for item in result.items if item.kind == types.CompletionItemKind.Class]
    by_label = {item.label: item for item in component_items}
    assert "c-CForm" in by_label
    assert min(component_items, key=lambda item: item.sort_text or "").label == expected_first
    assert by_label[expected_first].filter_text == expected_filter
    assert isinstance(by_label[expected_first].text_edit, types.InsertReplaceEdit)
    assert by_label[expected_first].text_edit.replace == types.Range(
        types.Position(0, 1),
        types.Position(0, len(source)),
    )


def test_uppercase_citry_prefix_is_not_treated_as_component_syntax():
    project = _registry_state()
    source = "<C-C"

    assert completion_items(_document(source, project), types.Position(0, len(source)), project) == []

    invalid = _document("<C-Card />", project)
    assert [diagnostic.code for diagnostic in invalid.diagnostics] == ["citry.parse.syntax"]
    assert "prefixes are lowercase" in invalid.diagnostics[0].message


def test_syntax_hover_covers_every_parser_owned_structural_tag_without_a_registry():
    project = _syntax_state()
    sources = {
        "c-if": '<c-if cond="ready"></c-if>',
        "c-elif": '<c-if cond="first"></c-if><c-elif cond="second"></c-elif>',
        "c-else": '<c-if cond="ready"></c-if><c-else></c-else>',
        "c-for": '<c-for each="item in items"></c-for>',
        "c-empty": '<c-for each="item in items"></c-for><c-empty></c-empty>',
        "c-raw": "<c-raw>{{ untouched }}</c-raw>",
        "c-fill": '<c-card><c-fill name="body"></c-fill></c-card>',
        "c-slot": '<c-slot name="body"></c-slot>',
    }

    # The exported parser set makes this corpus fail when Citry adds syntax
    # without adding the corresponding editor documentation.
    assert frozenset(sources) == RESERVED_TAG_NAMES
    for tag_name, source in sources.items():
        result = hover(_document(source, project), _position(source, tag_name, 2), project)

        assert result is not None, tag_name
        assert isinstance(result.contents, types.MarkupContent)
        assert result.range == types.Range(
            _position(source, tag_name),
            _position(source, tag_name, len(tag_name)),
        )
        assert f"`<{tag_name}>`" in result.contents.value
        assert f"https://citry.dev/reference/builtins/#{tag_name}" in result.contents.value


def test_syntax_hover_metadata_is_exhaustive_unique_and_parser_owned():
    keys = [(spec.kind, spec.context, spec.label) for spec in _CITRY_SYNTAX]
    documented_directives = {
        spec.label for spec in _CITRY_SYNTAX if spec.kind == "attribute" and spec.context in {"general", "component"}
    }
    documented_structural_attributes = {
        tag_name: frozenset(spec.label for spec in specs) for tag_name, specs in _STRUCTURAL_ATTRIBUTES.items()
    }

    assert len(keys) == len(set(keys))
    assert frozenset(_STRUCTURAL_TAG_SPECS) == RESERVED_TAG_NAMES
    assert documented_directives == CITRY_DIRECTIVE_NAMES
    assert documented_structural_attributes == STRUCTURAL_TAG_ATTRIBUTE_NAMES
    assert all(spec.documentation_url.startswith("https://citry.dev/") for spec in _CITRY_SYNTAX)


@pytest.mark.parametrize(
    ("source", "attribute", "documentation_path"),
    [
        ('<div c-if="ready"></div>', "c-if", "/syntax/control-flow/"),
        (
            '<div c-if="first"></div><div c-elif="second"></div>',
            "c-elif",
            "/syntax/control-flow/",
        ),
        ('<div c-if="ready"></div><div c-else></div>', "c-else", "/syntax/control-flow/"),
        ('<div c-for="item in items"></div>', "c-for", "/syntax/control-flow/"),
        (
            '<div c-for="item in items"></div><div c-empty></div>',
            "c-empty",
            "/syntax/control-flow/",
        ),
        ('<div c-bind="attrs"></div>', "c-bind", "/syntax/dynamic-attributes/#c-bind-spread"),
        ('<div #c-key="row.id"></div>', "#c-key", "/syntax/dynamic-attributes/#c-key"),
        ("<div #c-ignore></div>", "#c-ignore", "/syntax/dynamic-attributes/#c-ignore"),
        ('<c-card $c-props="{ open }" />', "$c-props", "/concepts/client-interactivity/#pass-client-props-down"),
        (
            '<c-card c-$c-props="props"></c-card>',
            "c-$c-props",
            "/concepts/client-interactivity/#pass-client-props-down",
        ),
        ('<c-if cond="ready"></c-if>', "cond", "/syntax/control-flow/"),
        ('<c-for each="item in items"></c-for>', "each", "/syntax/control-flow/"),
        ('<c-slot name="body"></c-slot>', "name", "/concepts/slots/"),
        ('<c-slot c-name="slot_name"></c-slot>', "c-name", "/concepts/slots/#dynamic-slot-names"),
        (
            '<c-card><c-fill name="body" data="{ item }"></c-fill></c-card>',
            "data",
            "/concepts/slots/#scoped-slots-passing-data-to-the-fill",
        ),
        (
            '<c-card><c-fill name="body" fallback="has_fallback"></c-fill></c-card>',
            "fallback",
            "/concepts/slots/#wrapping-the-fallback",
        ),
        ('<c-slot name="body" required></c-slot>', "required", "/concepts/slots/#supply-fallback-content"),
        (
            '<c-slot name="body" c-required="required"></c-slot>',
            "c-required",
            "/concepts/slots/#require-a-slot-conditionally",
        ),
        (
            '<c-card><c-fill c-bind="fill_attrs"></c-fill></c-card>',
            "c-bind",
            "/concepts/slots/#spread-slot-and-fill-settings",
        ),
        (
            '<c-slot c-bind="slot_attrs"></c-slot>',
            "c-bind",
            "/concepts/slots/#spread-slot-and-fill-settings",
        ),
        ('<c-component is="card"></c-component>', "is", "/advanced/dynamic-components/"),
        ('<c-element c-is="tag"></c-element>', "c-is", "/advanced/dynamic-components/"),
    ],
)
def test_syntax_hover_documents_directives_and_structural_attributes_without_a_registry(
    source,
    attribute,
    documentation_path,
):
    project = _syntax_state()

    result = hover(_document(source, project), _position(source, attribute, 1), project)

    assert result is not None
    assert isinstance(result.contents, types.MarkupContent)
    assert result.range == types.Range(
        _position(source, attribute),
        _position(source, attribute, len(attribute)),
    )
    assert f"`{attribute}`" in result.contents.value
    assert f"https://citry.dev{documentation_path}" in result.contents.value


@pytest.mark.parametrize(
    ("source", "marker"),
    [
        ('<div c-class="classes"></div>', "c-class"),
        ('<div title="c-bind"></div>', "c-bind"),
        ('<c-if c-bind="attrs"></c-if>', "c-bind"),
        ('<c-fill #c-key="row.id"></c-fill>', "#c-key"),
        ("<c-slot #c-ignore></c-slot>", "#c-ignore"),
        ('<c-raw c-if="ready"></c-raw>', "c-if"),
        ("<div>{# <c-slot required> #}</div>", "c-slot"),
        ("<div><!-- <c-slot required> --></div>", "c-slot"),
        ("<c-raw><c-slot required></c-raw>", "c-slot"),
        ('<script>const sample = "<c-slot required>";</script>', "c-slot"),
        ('<div name="body" required></div>', "required"),
    ],
)
def test_syntax_hover_ignores_dynamic_attributes_values_and_comments(source, marker):
    project = _syntax_state()

    assert hover(_document(source, project), _position(source, marker, 1), project) is None


def test_syntax_hover_covers_closing_tags_and_invalid_structural_placement():
    project = _syntax_state()
    closing_source = '<c-if cond="ready"></c-if>'
    invalid_source = "<c-fill></c-fill>"
    closing_start = closing_source.rindex("c-if")

    closing = hover(
        _document(closing_source, project),
        types.Position(0, closing_start + 2),
        project,
    )
    invalid = hover(_document(invalid_source, project), _position(invalid_source, "c-fill", 2), project)

    assert closing is not None
    assert closing.range == types.Range(
        types.Position(0, closing_start),
        types.Position(0, closing_start + len("c-if")),
    )
    assert invalid is not None
    assert isinstance(invalid.contents, types.MarkupContent)
    assert "`<c-fill>`" in invalid.contents.value


def test_syntax_hover_maps_nested_and_inline_python_ranges_with_astral_text():
    project = _syntax_state()
    nested_source = '<c-card c-body="<>😀<c-slot required /></>" />'
    python_source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template = """\n'
        "      😀<c-slot required />\n"
        '    """\n'
    )

    nested = hover(_document(nested_source, project), _position(nested_source, "required", 2), project)
    inline = hover(
        _document(python_source, project, language_id="python"),
        _position(python_source, "required", 2),
        project,
    )

    assert nested is not None
    assert nested.range == types.Range(
        _position(nested_source, "required"),
        _position(nested_source, "required", len("required")),
    )
    assert inline is not None
    assert inline.range == types.Range(
        _position(python_source, "required"),
        _position(python_source, "required", len("required")),
    )


def test_syntax_hover_declines_implicit_python_literal_concatenation():
    project = _syntax_state()
    source = 'from citry import Component\nclass Card(Component):\n    template = ("<c-slot requ" "ired />")\n'

    assert (
        hover(
            _document(source, project, language_id="python"),
            _position(source, "ired", 2),
            project,
        )
        is None
    )


def test_hover_and_component_definition_use_catalog_precision():
    project = _registry_state()
    source = '<c-card title="Hi" />'
    document = _document(source, project)

    tag_hover = hover(document, _position(source, "card", 2), project)
    attr_hover = hover(document, _position(source, "title", 2), project)
    target = definition(document, _position(source, "card", 2), project)

    assert tag_hover is not None
    assert isinstance(tag_hover.contents, types.MarkupContent)
    assert "documented card" in tag_hover.contents.value
    assert attr_hover is not None
    assert isinstance(attr_hover.contents, types.MarkupContent)
    assert "required" in attr_hover.contents.value
    assert target is not None
    assert target.uri.startswith("file:")
    assert target.range.start == types.Position(0, 0)


def test_syntax_hover_yields_to_catalog_inputs_and_static_slot_values():
    project = _registry_state()
    input_source = "<c-card required />"
    fill_source = '<c-card><c-fill name="body"></c-fill></c-card>'

    component_input = hover(
        _document(input_source, project),
        _position(input_source, "required", 2),
        project,
    )
    fill_key = hover(_document(fill_source, project), _position(fill_source, "name", 2), project)
    fill_value = hover(_document(fill_source, project), _position(fill_source, "body", 2), project)

    assert component_input is not None
    assert isinstance(component_input.contents, types.MarkupContent)
    assert "optional" in component_input.contents.value
    assert "citry.dev" not in component_input.contents.value
    assert fill_key is not None
    assert isinstance(fill_key.contents, types.MarkupContent)
    assert "Select this slot by its literal name" in fill_key.contents.value
    assert fill_value is not None
    assert isinstance(fill_value.contents, types.MarkupContent)
    assert "Slot `body`" in fill_value.contents.value


def test_component_definition_uses_exact_top_level_class_name_range():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _definition_analysis(),
        catalog,
    )
    source = "<c-definition-card />"

    target = definition(_document(source, project), _position(source, "definition", 2), project)

    assert target is not None
    assert target.uri == Path(__file__).resolve().as_uri()
    source_lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    class_line = next(index for index, line in enumerate(source_lines) if line.startswith("class DefinitionCard"))
    assert target.range == types.Range(
        types.Position(class_line, len("class ")),
        types.Position(class_line, len("class DefinitionCard")),
    )


def test_component_input_definition_uses_exact_nested_field_range():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _definition_analysis(),
        catalog,
    )
    source = '<c-definition-card title="title" />'

    target = definition(_document(source, project), _position(source, "title", 2), project)

    assert target is not None
    assert target.uri == Path(__file__).resolve().as_uri()
    source_lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    field_line = next(index for index, line in enumerate(source_lines) if line.strip() == "title: str")
    assert target.range == types.Range(
        types.Position(field_line, len("        ")),
        types.Position(field_line, len("        title")),
    )

    value_target = definition(
        _document(source, project),
        _position(source, 'title"', 2),
        project,
    )
    assert value_target is None

    dynamic_source = '<c-definition-card c-title="value" />'
    dynamic_target = definition(
        _document(dynamic_source, project),
        _position(dynamic_source, "c-title", len("c-ti")),
        project,
    )
    assert dynamic_target == target
    dynamic_hint = hover(
        _document(dynamic_source, project),
        _position(dynamic_source, "c-title", len("c-ti")),
        project,
    )
    assert dynamic_hint is not None
    assert isinstance(dynamic_hint.contents, types.MarkupContent)
    assert "required" in dynamic_hint.contents.value
    assert "Title component" not in dynamic_hint.contents.value


def test_inline_template_data_roots_complete_hover_and_define_exact_fields():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    outer_marker = "{{ template_user }}\n      <div"
    position = _position(source, outer_marker, len("{{ template_"))

    items = completion_items(document, position, project)
    hint = hover(document, _position(source, outer_marker, len("{{ template_")), project)
    target = definition(document, _position(source, outer_marker, len("{{ template_")), project)

    by_label = {item.label: item for item in items}
    assert {"template_user", "items", "shared_count"} <= by_label.keys()
    assert "child_only" not in by_label
    assert by_label["template_user"].detail == "TemplateData · str (required)"
    assert hint is not None
    assert isinstance(hint.contents, types.MarkupContent)
    assert hint.contents.value == ("```python\n(variable) template_user: str\n```\n\nTemplateData field · required")
    assert target is not None
    field_line = next(index for index, line in enumerate(source.splitlines()) if line.strip() == "template_user: str")
    assert target.uri == source_file.as_uri()
    assert target.range == types.Range(
        types.Position(field_line, len("        ")),
        types.Position(field_line, len("        template_user")),
    )


def test_variable_hover_uses_catalog_type_for_unusable_analyzer_text() -> None:
    variable = TemplateVariableHover(
        "callback",
        types.Range(types.Position(0, 3), types.Position(0, 11)),
        "TemplateData field · required",
        fallback_types=("Callable[[str], int]",),
    )

    hint = render_template_variable_hover(variable, ("def callback(value: str) -> int",))
    nested_declaration_hint = render_template_variable_hover(variable, ("(variable) callback: int",))
    async_declaration_hint = render_template_variable_hover(variable, ("async def callback() -> int",))
    unknown_hint = render_template_variable_hover(variable, ("Unknown",))
    literal_unknown_hint = render_template_variable_hover(variable, ('Literal["Unknown"]',))

    assert hint.contents.value == (
        "```python\n(variable) callback: Callable[[str], int]\n```\n\nTemplateData field · required"
    )
    assert nested_declaration_hint == hint
    assert async_declaration_hint == hint
    assert unknown_hint == hint
    assert literal_unknown_hint.contents.value == (
        '```python\n(variable) callback: Literal["Unknown"]\n```\n\nTemplateData field · required'
    )


def test_inline_template_data_uses_asset_owner_provenance_for_an_unregistered_library_base():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(
        document,
        _position(source, '{{ library_title }}"', len("{{ library_")),
        project,
    )

    assert "library_title" in {item.label for item in items}


def test_template_data_completion_unions_lexical_names_and_schema_roots():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    marker = "{{ row }} {{ row.upper }} {{ shared_count }}"
    position = _position(source, marker, len("{{ ro"))

    items = completion_items(document, position, project)
    matching = [item for item in items if item.label == "row"]
    lexical_hint = hover(document, _position(source, marker, len("{{ ro")), project)

    assert len(matching) == 1
    assert matching[0].detail == "loop variable introduced by c-for"
    assert {"template_user", "shared_count"} <= {item.label for item in items}
    assert lexical_hint is not None
    assert isinstance(lexical_hint.contents, types.MarkupContent)
    assert "Loop variable" in lexical_hint.contents.value


def test_lexical_roots_do_not_complete_or_resolve_at_member_boundaries():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    marker = "{{ row.upper }}"
    member_position = _position(source, marker, len("{{ row.up"))
    boundary_position = _position(source, marker, len("{{ row"))

    assert completion_items(document, member_position, project) == []
    assert hover(document, member_position, project) is None
    assert definition(document, member_position, project) is None
    assert hover(document, boundary_position, project) is None
    assert definition(document, boundary_position, project) is None


@pytest.mark.parametrize(
    ("marker", "offset"),
    [
        ('c-title="template_user"', len('c-title="template_')),
        ('#c-key="template_user"', len('#c-key="template_')),
        ('c-for="row in items"', len('c-for="row in it')),
    ],
)
def test_template_data_completion_covers_expression_valued_attributes(marker, offset):
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(document, _position(source, marker, offset), project)

    assert {"template_user", "items", "shared_count", "café"} <= {item.label for item in items}


def test_template_data_hover_joins_only_the_exact_free_root_token():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    marker = "{{ template_user.upper }}"

    root_hint = hover(document, _position(source, marker, len("{{ template_")), project)
    boundary_hint = hover(document, _position(source, marker, len("{{ template_user")), project)
    member_hint = hover(document, _position(source, marker, len("{{ template_user.up")), project)
    member_items = completion_items(
        document,
        _position(source, marker, len("{{ template_user.up")),
        project,
    )

    assert root_hint is not None
    assert boundary_hint is None
    assert member_hint is None
    assert not {"template_user", "items", "shared_count", "café"} & {item.label for item in member_items}


def test_template_data_root_join_uses_python_nfkc_identity():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    marker = "{{ café }}"

    hint = hover(document, _position(source, marker, len("{{ cafe")), project)
    target = definition(document, _position(source, marker, len("{{ cafe")), project)

    assert hint is not None
    assert target is not None
    field_line = next(index for index, line in enumerate(source.splitlines()) if line.strip().startswith("café: str"))
    assert target.range.start == types.Position(field_line, len("        "))


def test_template_data_completion_survives_an_incomplete_template_expression():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8").replace(
        "{{ template_user }}\n      <div",
        "{{ template_\n      <div",
        1,
    )
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(document, _position(source, "{{ template_", len("{{ template_")), project)

    assert "template_user" in {item.label for item in items}


@pytest.mark.parametrize("prefix", ["", "a", "aut"])
def test_template_data_completion_covers_empty_and_partial_attribute_values(prefix):
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    original = source_file.read_text(encoding="utf-8")
    replacement = f'c-action="{prefix}"'
    source = original.replace('c-action="action"', replacement, 1)
    cursor = _position(source, replacement, len(replacement) - 1)
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(document, cursor, project)

    expected = {
        "form_id",
        "action",
        "method",
        "enctype",
        "target",
        "autocomplete",
        "disabled",
        "readonly",
        "submitting",
        "novalidate",
        "aria_busy",
        "attrs",
    }
    assert {item.label for item in items} == expected
    for item in items:
        assert item.filter_text == item.label
        assert isinstance(item.text_edit, types.InsertReplaceEdit)
        assert item.text_edit.new_text == item.label
        assert item.text_edit.insert.end == cursor
        assert item.text_edit.replace.end == cursor
        assert item.text_edit.insert.start == item.text_edit.replace.start
        assert item.text_edit.insert.start.character == cursor.character - len(prefix)


@pytest.mark.parametrize(
    ("authored", "replacement", "cursor_offset"),
    [
        ('c-action="action"', 'c-autocomplete="a"', len('c-autocomplete="a')),
        (
            'c-action="action"',
            'c-autocomplete="autocomplete+a"',
            len('c-autocomplete="autocomplete+a'),
        ),
        (
            'c-action="action"',
            'c-autocomplete="autocomplete +a"',
            len('c-autocomplete="autocomplete +a'),
        ),
        ("{{ action }}", "{{a }}", len("{{a")),
        ("{{ action }}", "{{ f'{a}' }}", len("{{ f'{a")),
        ('c-action="action"', "c-action=\"f'{a}'\"", len("c-action=\"f'{a")),
        (
            'c-action="action"',
            "c-for=\"item in [f'{a}']\"",
            len("c-for=\"item in [f'{a"),
        ),
    ],
)
def test_template_data_completion_does_not_require_whitespace_before_a_root(
    authored,
    replacement,
    cursor_offset,
):
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    original = source_file.read_text(encoding="utf-8")
    source = original.replace(authored, replacement, 1)
    cursor = _position(source, replacement, cursor_offset)
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(document, cursor, project)

    autocomplete = next(item for item in items if item.label == "autocomplete")
    assert isinstance(autocomplete.text_edit, types.InsertReplaceEdit)
    assert autocomplete.text_edit.insert == types.Range(
        types.Position(cursor.line, cursor.character - 1),
        cursor,
    )
    assert autocomplete.text_edit.replace == autocomplete.text_edit.insert


@pytest.mark.parametrize(
    ("authored", "replacement", "cursor_offset"),
    [
        ("{{ action }}", "{{ 'a' }}", len("{{ 'a")),
        ("{{ action }}", "{{ 'a }}", len("{{ 'a")),
        ("{{ action }}", "{{ action # a }}", len("{{ action # a")),
        ("{{ action }}", "{{ {'a }}", len("{{ {'a")),
        ("{{ action }}", "{{ f'prefix a suffix' }}", len("{{ f'prefix a")),
        ('c-action="action"', "c-action=\"'a'\"", len("c-action=\"'a")),
        ('c-action="action"', "c-action=\"{'a': action}\"", len("c-action=\"{'a")),
    ],
)
def test_template_data_roots_do_not_complete_in_python_strings_comments_or_keys(
    authored,
    replacement,
    cursor_offset,
):
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    original = source_file.read_text(encoding="utf-8")
    source = original.replace(authored, replacement, 1)
    cursor = _position(source, replacement, cursor_offset)
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    assert completion_items(document, cursor, project) == []


def test_fill_data_completion_does_not_mix_in_template_roots():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    original = source_file.read_text(encoding="utf-8")
    replacement = '<c-definition-card><c-fill name="body" data="{ a"></c-fill></c-definition-card>'
    source = original.replace(
        '<form data-label="😀" c-action="action">\n      {{ action }}\n    </form>',
        replacement,
        1,
    )
    cursor = _position(source, replacement, len('<c-definition-card><c-fill name="body" data="{ a'))
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    labels = {item.label for item in completion_items(document, cursor, project)}

    assert "autocomplete" not in labels
    assert "action" not in labels


def test_template_data_completion_replaces_the_complete_identifier_around_cursor():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    marker = 'c-action="action"'
    cursor = _position(source, marker, len('c-action="act'))
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(document, cursor, project)

    action = next(item for item in items if item.label == "action")
    assert isinstance(action.text_edit, types.InsertReplaceEdit)
    assert action.text_edit.insert == types.Range(
        _position(source, marker, len('c-action="')),
        cursor,
    )
    assert action.text_edit.replace == types.Range(
        _position(source, marker, len('c-action="')),
        _position(source, marker, len('c-action="action')),
    )


def test_template_data_completion_covers_an_empty_interpolation():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    original = source_file.read_text(encoding="utf-8")
    source = original.replace("{{ action }}", "{{  }}", 1)
    cursor = _position(source, "{{  }}", len("{{ "))
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(document, cursor, project)

    assert "action" in {item.label for item in items}
    action = next(item for item in items if item.label == "action")
    assert isinstance(action.text_edit, types.InsertReplaceEdit)
    assert action.text_edit.insert == types.Range(cursor, cursor)
    assert action.text_edit.replace == types.Range(cursor, cursor)


def test_expression_completion_ignores_interpolation_text_in_a_static_attribute():
    project = _syntax_state()
    source = '<div c-for="item in items" title="{{ literal"><span class="x"></span></div>'
    document = _document(source, project)

    items = completion_items(document, _position(source, 'class="x', len('class="x')), project)

    assert items == []


def test_broken_buffer_completion_ignores_static_attribute_interpolation_text():
    project = _syntax_state()
    source = '<div c-for="item in items" title="{{ literal">text'
    document = _document(source, project)

    items = completion_items(document, _position(source, "text", len("text")), project)

    assert items == []


def test_empty_dynamic_attribute_completion_ignores_quotes_in_tag_comments():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    original = source_file.read_text(encoding="utf-8")
    source = original.replace(
        '<form data-label="😀" c-action="action">',
        '<form {# note "quoted" #} data-label="😀" c-action="">',
        1,
    )
    marker = 'c-action=""'
    cursor = _position(source, marker, len('c-action="'))
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(document, cursor, project)

    assert "action" in {item.label for item in items}


def test_template_data_is_withheld_for_regex_recovered_python_regions():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8") + "\n("
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    marker = "{{ template_user }}\n      <div"

    items = completion_items(document, _position(source, marker, len("{{ template_")), project)

    assert items == []


def test_shared_file_template_data_exposes_only_identical_common_fields(tmp_path):
    template_file = tmp_path / "shared.html"
    template_source = "{{ common }} {{ child_only }}"
    template_file.write_text(template_source, encoding="utf-8")
    engine = Citry(dirs=[tmp_path], autodiscover=False)

    class SharedBase(Component):
        citry = engine
        template_file = "shared.html"

        class TemplateData:
            common: str

    class SharedChild(SharedBase):
        class TemplateData:
            child_only: bool

    catalog = CatalogIndex(engine.inspect_components(include_builtins=True, resolve_assets=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(tmp_path), mode="registry", registry_ready=True),
        engine.template_analysis(),
        catalog,
    )
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    items = completion_items(document, _position(template_source, "common", 3), project)
    common_hint = hover(document, _position(template_source, "common", 3), project)
    child_hint = hover(document, _position(template_source, "child_only", 3), project)

    assert {item.label for item in items} == {"common"}
    assert common_hint is not None
    assert child_hint is None
    assert document.diagnostics == ()


def test_shared_file_common_contract_with_distinct_definitions_has_no_definition(tmp_path):
    template_file = tmp_path / "independent.html"
    template_source = "{{ common }}"
    template_file.write_text(template_source, encoding="utf-8")
    engine = Citry(dirs=[tmp_path], autodiscover=False)

    class First(Component):
        citry = engine
        template_file = "independent.html"

        class TemplateData:
            common: str

    class Second(Component):
        citry = engine
        template_file = "independent.html"

        class TemplateData:
            common: str

    catalog = CatalogIndex(engine.inspect_components(include_builtins=True, resolve_assets=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(tmp_path), mode="registry", registry_ready=True),
        engine.template_analysis(),
        catalog,
    )
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    region = document.regions[0]

    fields = _template_data_fields(document, region, catalog)
    items = completion_items(document, _position(template_source, "common", 3), project)

    assert {item.label for item in items} == {"common"}
    assert len(fields) == 1
    assert fields[0].source_file is None
    assert definition(document, _position(template_source, "common", 3), project) is None


def test_template_data_is_withheld_without_a_proven_template_owner():
    project = _registry_state()
    source = "{{ title }}"
    document = _document(source, project)

    assert completion_items(document, _position(source, "title", 3), project) == []
    assert hover(document, _position(source, "title", 3), project) is None
    assert definition(document, _position(source, "title", 3), project) is None
    assert document.diagnostics == ()


def test_template_data_is_withheld_when_a_shared_file_has_an_untyped_consumer(tmp_path):
    template_file = tmp_path / "mixed.html"
    template_source = "{{ common }}"
    template_file.write_text(template_source, encoding="utf-8")
    engine = Citry(dirs=[tmp_path], autodiscover=False)

    class Typed(Component):
        citry = engine
        template_file = "mixed.html"

        class TemplateData:
            common: str

    class Untyped(Component):
        citry = engine
        template_file = "mixed.html"

    catalog = CatalogIndex(engine.inspect_components(include_builtins=True, resolve_assets=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(tmp_path), mode="registry", registry_ready=True),
        engine.template_analysis(),
        catalog,
    )
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    assert completion_items(document, _position(template_source, "common", 3), project) == []
    assert hover(document, _position(template_source, "common", 3), project) is None


def test_inferred_template_data_tracks_synchronized_source_for_completion_hover_and_definition(tmp_path):
    template_file = tmp_path / "card.html"
    template_source = "{{ title }} {{ count }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    disk_source = (
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[__import__('pathlib').Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'title': 'Hello', 'count': 1}\n"
    )
    app_file.write_text(disk_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready is True
    assert project.source_analysis is not None
    template_document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    template_document.update(template_source, 1, project)

    items = completion_items(
        template_document,
        _position(template_source, "title", 3),
        project,
        {template_document.uri: template_document},
    )
    hint = hover(
        template_document,
        _position(template_source, "title", 3),
        project,
        {template_document.uri: template_document},
    )
    target = definition(
        template_document,
        _position(template_source, "title", 3),
        project,
        {template_document.uri: template_document},
    )

    assert {item.label for item in items} == {"title", "count"}
    assert {item.detail for item in items} == {"Inferred from template_data()"}
    assert hint is not None
    assert isinstance(hint.contents, types.MarkupContent)
    assert hint.contents.value == ("```python\n(variable) title\n```\n\nInferred from template_data()")
    assert isinstance(target, types.Location)
    assert target.uri == app_file.as_uri()
    assert target.range.start.line == 6

    edited_source = disk_source.replace("'title': 'Hello'", "'heading': 'Hello'")
    python_document = DocumentState(app_file.as_uri(), "python", edited_source, 2)
    python_document.update(edited_source, 2, project)
    edited_template = "{{ heading }}"
    template_document.update(edited_template, 2, project)
    open_documents = {
        template_document.uri: template_document,
        python_document.uri: python_document,
    }

    edited_items = completion_items(
        template_document,
        _position(edited_template, "heading", 3),
        project,
        open_documents,
    )
    edited_target = definition(
        template_document,
        _position(edited_template, "heading", 3),
        project,
        open_documents,
    )

    assert {item.label for item in edited_items} == {"heading", "count"}
    assert isinstance(edited_target, types.Location)
    assert edited_target.range.start.line == 6
    assert edited_source.splitlines()[6][edited_target.range.start.character :].startswith("'heading'")

    python_document.update(edited_source + "\n(", 3, project)
    assert (
        completion_items(
            template_document,
            _position(edited_template, "heading", 3),
            project,
            open_documents,
        )
        == []
    )
    assert (
        definition(
            template_document,
            _position(edited_template, "heading", 3),
            project,
            open_documents,
        )
        is None
    )


def test_expression_shadows_use_declared_schema_source_and_exact_cursor(tmp_path):
    template_file = tmp_path / "card.html"
    template_source = "{{ method.lower() }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        method: str | None\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    shadows = expression_shadows(
        document,
        _position(template_source, "lower", 2),
        project,
        {document.uri: document},
    )

    assert len(shadows) == 1
    shadow = shadows[0]
    assert shadow.cursor_offset == template_source.index("lower") + 2 - template_source.index("method")
    assert len(shadow.document.copies) == 1
    copy = shadow.document.copies[0]
    assert shadow.document.source[copy.shadow_start : copy.shadow_end] == "method.lower() "
    assert "method = __citry_cast(Card.TemplateData, __citry_data).method" in shadow.document.source


def test_all_expression_shadows_reuses_one_consumer_join_per_generation(tmp_path, monkeypatch):
    template_file = tmp_path / "card.html"
    template_source = "\n".join(f"{{{{ title.lower() }}}} {{{{ items[{index}] }}}}" for index in range(12))
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        title: str\n"
        "        items: list[str]\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    python_document = DocumentState(app_file.as_uri(), "python", app_source, 1)
    python_document.update(app_source, 1, project)
    documents = {document.uri: document, python_document.uri: python_document}

    original = engine_module._component_template_context
    calls = 0

    def counted_context(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_module, "_component_template_context", counted_context)
    first = all_expression_shadows(document, project, documents)
    second = all_expression_shadows(document, project, documents)

    assert len(first) == 24
    assert second is first
    assert calls == 1

    # Exact synchronized text, not the editor version alone, defines a new generation.
    python_document.update(f"{app_source}\n", 2, project)
    refreshed = all_expression_shadows(document, project, documents)
    assert refreshed is not first
    assert len(refreshed) == 24
    assert calls == 2


def test_semantic_dependencies_expose_direct_sources_and_stay_conservative(tmp_path):
    template_file = tmp_path / "card.html"
    template_source = "{{ title.lower() }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        title: str\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    dependencies = semantic_dependencies(document, project, {document.uri: document})

    assert app_file.resolve().as_uri() in dependencies.source_uris
    # Python annotations may import types from files absent from portable provenance.
    assert dependencies.complete is False


def test_expression_shadows_decline_a_query_split_across_python_literals(tmp_path):
    app_file = tmp_path / "app.py"
    source = (
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        '    template = "{{ title.lo" "wer() }}"\n'
        "    class TemplateData:\n"
        "        title: str\n"
    )
    app_file.write_text(source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(app_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    shadows = expression_shadows(
        document,
        _position(source, "wer", 2),
        project,
        {document.uri: document},
    )

    assert shadows == ()


def test_expression_shadows_copy_each_inferred_return_and_synchronized_source(tmp_path):
    template_file = tmp_path / "card.html"
    template_source = "{{ method.lower() }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    disk_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        if kwargs:\n"
        "            return {'method': 'get'}\n"
        "        return {'method': None}\n"
    )
    app_file.write_text(disk_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    edited_source = disk_source.replace("'get'", "'post'")
    python_document = DocumentState(app_file.as_uri(), "python", edited_source, 2)
    python_document.update(edited_source, 2, project)

    shadows = expression_shadows(
        document,
        _position(template_source, "lower", 2),
        project,
        {document.uri: document, python_document.uri: python_document},
    )

    assert len(shadows) == 1
    shadow = shadows[0]
    assert "'post'" in shadow.document.source
    assert len(shadow.document.copies) == 2


def test_inferred_template_data_survives_component_library_materialization(tmp_path):
    template_file = tmp_path / "library-card.html"
    template_source = "{{ title }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from citry import ComponentLibrary, LibraryComponent\n"
        "class CCard(LibraryComponent):\n"
        "    template_file = 'library-card.html'\n"
        "    class Kwargs:\n"
        "        title: str\n"
        "    def template_data(self, kwargs, slots):\n"
        "        return {'title': kwargs.title}\n"
        "library = ComponentLibrary('test-ui', (CCard,))\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:library")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    items = completion_items(document, _position(template_source, "title", 3), project)
    target = definition(document, _position(template_source, "title", 3), project)

    assert [(item.label, item.detail) for item in items] == [("title", "Inferred from template_data()")]
    assert isinstance(target, types.Location)
    assert target.uri == app_file.as_uri()
    assert target.range.start.line == 6


def test_library_source_inference_rejects_generated_classes_with_forged_provenance(tmp_path):
    template_file = tmp_path / "generated-card.html"
    template_source = "{{ authored_root }} {{ generated_root }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from functools import wraps\n"
        "from citry import ComponentLibrary, LibraryComponent\n"
        "class CCard(LibraryComponent):\n"
        "    template_file = 'generated-card.html'\n"
        "    def template_data(self, kwargs, slots):\n"
        "        return {'authored_root': 1}\n"
        "class GeneratedCCard(CCard):\n"
        "    @wraps(CCard.template_data)\n"
        "    def template_data(self, kwargs, slots):\n"
        "        return {'generated_root': 1}\n"
        "GeneratedCCard.__name__ = CCard.__name__\n"
        "GeneratedCCard.__module__ = CCard.__module__\n"
        "GeneratedCCard.__qualname__ = CCard.__qualname__\n"
        "library = ComponentLibrary('test-ui', (GeneratedCCard,))\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:library")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    assert completion_items(document, _position(template_source, "authored_root", 3), project) == []
    assert hover(document, _position(template_source, "generated_root", 3), project) is None


def test_library_source_inference_rejects_same_line_code_from_another_module(tmp_path):
    template_file = tmp_path / "cross-module-card.html"
    template_source = "{{ authored_root }} {{ generated_root }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "factory.py").write_text(
        "from functools import wraps\n"
        "\n"
        "def generated(base):\n"
        "    class Generated(base):\n"
        "        @wraps(base.template_data)\n"
        "        def template_data(self, kwargs, slots):\n"
        "            return {'generated_root': 1}\n"
        "    Generated.__name__ = base.__name__\n"
        "    Generated.__module__ = base.__module__\n"
        "    Generated.__qualname__ = base.__qualname__\n"
        "    return Generated\n",
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "from citry import ComponentLibrary, LibraryComponent\n"
        "from factory import generated\n"
        "class CCard(LibraryComponent):\n"
        "    template_file = 'cross-module-card.html'\n"
        "    def template_data(self, kwargs, slots):\n"
        "        return {'authored_root': 1}\n"
        "GeneratedCCard = generated(CCard)\n"
        "library = ComponentLibrary('test-ui', (GeneratedCCard,))\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:library")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    assert completion_items(document, _position(template_source, "authored_root", 3), project) == []
    assert hover(document, _position(template_source, "generated_root", 3), project) is None


def test_inherited_default_template_data_exposes_effective_kwargs_fields(tmp_path):
    template_file = tmp_path / "form.html"
    template_source = "{{ method }} {{ action }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Form(Component):\n"
        "    citry = engine\n"
        "    template_file = 'form.html'\n"
        "    class Kwargs:\n"
        "        method: str\n"
        "        action: str | None = None\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    items = completion_items(document, _position(template_source, "method", 3), project)
    hint = hover(document, _position(template_source, "method", 3), project)
    target = definition(document, _position(template_source, "method", 3), project)

    by_name = {item.label: item for item in items}
    assert set(by_name) == {"method", "action"}
    assert by_name["method"].detail == "Inferred from template_data() · str (required)"
    assert hint is not None
    assert isinstance(target, types.Location)
    assert target.uri == app_file.as_uri()
    assert target.range.start.line == 7

    # An unsaved override invalidates the copied inherited-owner chain until
    # project reload establishes a new exact component generation.
    edited_source = app_source.replace(
        "    class Kwargs:\n",
        "    def template_data(self, kwargs):\n        return {'other': 1}\n    class Kwargs:\n",
    )
    python_document = DocumentState(app_file.as_uri(), "python", edited_source, 2)
    python_document.update(edited_source, 2, project)

    assert (
        completion_items(
            document,
            _position(template_source, "method", 3),
            project,
            {document.uri: document, python_document.uri: python_document},
        )
        == []
    )


def test_inherited_template_data_is_withheld_after_unsaved_base_binding_change(tmp_path):
    template_file = tmp_path / "selected.html"
    template_source = "{{ old_root }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Base(Component):\n"
        "    citry = engine\n"
        "    def template_data(self, kwargs):\n"
        "        return {'old_root': 1}\n"
        "class Other(Component):\n"
        "    citry = engine\n"
        "    def template_data(self, kwargs):\n"
        "        return {'new_root': 1}\n"
        "Selected = Base\n"
        "class Card(Selected):\n"
        "    citry = engine\n"
        "    template_file = 'selected.html'\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    assert {item.label for item in completion_items(document, _position(template_source, "old_root", 3), project)} == {
        "old_root"
    }

    edited_source = app_source.replace("Selected = Base", "Selected = Other")
    python_document = DocumentState(app_file.as_uri(), "python", edited_source, 2)
    python_document.update(edited_source, 2, project)
    assert (
        completion_items(
            document,
            _position(template_source, "old_root", 3),
            project,
            {document.uri: document, python_document.uri: python_document},
        )
        == []
    )


def test_inherited_template_data_is_withheld_after_unsaved_import_alias_change(tmp_path):
    template_file = tmp_path / "imported.html"
    template_source = "{{ old_root }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "bases.py").write_text(
        "class Base:\n"
        "    def template_data(self, kwargs):\n"
        "        return {'old_root': 1}\n"
        "class Other:\n"
        "    def template_data(self, kwargs):\n"
        "        return {'new_root': 1}\n",
        encoding="utf-8",
    )
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from bases import Base\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Base, Component):\n"
        "    citry = engine\n"
        "    template_file = 'imported.html'\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    items = completion_items(document, _position(template_source, "old_root", 3), project)
    assert {item.label for item in items} == {"old_root"}

    edited_source = app_source.replace("from bases import Base", "from bases import Other as Base")
    python_document = DocumentState(app_file.as_uri(), "python", edited_source, 2)
    python_document.update(edited_source, 2, project)
    assert (
        completion_items(
            document,
            _position(template_source, "old_root", 3),
            project,
            {document.uri: document, python_document.uri: python_document},
        )
        == []
    )


def test_typed_kwargs_methods_are_not_modelled_as_dict_mutations(tmp_path):
    template_file = tmp_path / "authored-method.html"
    template_source = "{{ title }} {{ extra }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'authored-method.html'\n"
        "    class Kwargs:\n"
        "        title: str\n"
        "        def update(self, **values):\n"
        "            return None\n"
        "    def template_data(self, kwargs):\n"
        "        kwargs.update(extra=1)\n"
        "        return kwargs\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    assert completion_items(document, _position(template_source, "title", 3), project) == []
    assert hover(document, _position(template_source, "extra", 3), project) is None


def test_inferred_template_data_joins_an_inline_template_in_its_open_python_document(tmp_path):
    app_file = tmp_path / "app.py"
    source = (
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template = '{{ root_class }}'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'root_class': 'card'}\n"
    )
    app_file.write_text(source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(app_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    cursor = _position(source, "{{ root_class", len("{{ root_"))

    items = completion_items(document, cursor, project, {document.uri: document})
    hint = hover(document, cursor, project, {document.uri: document})
    target = definition(document, cursor, project, {document.uri: document})

    assert {item.label for item in items} == {"root_class"}
    assert hint is not None
    assert isinstance(target, types.Location)
    assert target.uri == app_file.as_uri()
    assert target.range.start.line == 6


def test_inferred_template_data_returns_every_reachable_key_definition(tmp_path):
    template_file = tmp_path / "branch.html"
    template_source = "{{ value }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Branch(Component):\n"
        "    citry = engine\n"
        "    template_file = 'branch.html'\n"
        "    def template_data(self, kwargs):\n"
        "        if condition:\n"
        "            return {'value': first}\n"
        "        return {'value': second}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    target = definition(document, _position(template_source, "value", 3), project)

    assert isinstance(target, list)
    assert [location.range.start.line for location in target] == [8, 9]


def test_declared_template_data_remains_authoritative_over_source_inference(tmp_path):
    template_file = tmp_path / "declared.html"
    template_source = "{{ declared }} {{ extra }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Declared(Component):\n"
        "    citry = engine\n"
        "    template_file = 'declared.html'\n"
        "    class TemplateData:\n"
        "        declared: str\n"
        "    def template_data(self, kwargs):\n"
        "        return {'declared': 'yes', 'extra': 'not-authoritative'}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    items = completion_items(document, _position(template_source, "declared", 3), project)

    assert {item.label for item in items} == {"declared"}
    assert hover(document, _position(template_source, "extra", 3), project) is None


def test_shared_template_intersects_inferred_roots_and_keeps_each_definition(tmp_path):
    template_file = tmp_path / "shared-inferred.html"
    template_source = "{{ common }} {{ first_only }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class First(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared-inferred.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'common': 1, 'first_only': 1}\n"
        "class Second(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared-inferred.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'common': 2, 'second_only': 2}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    items = completion_items(document, _position(template_source, "common", 3), project)
    common_target = definition(document, _position(template_source, "common", 3), project)

    assert {item.label for item in items} == {"common"}
    assert isinstance(common_target, list)
    assert [location.range.start.line for location in common_target] == [7, 12]
    assert hover(document, _position(template_source, "first_only", 3), project) is None


def test_mixed_kwargs_and_literal_returns_keep_root_but_drop_schema_type(tmp_path):
    template_file = tmp_path / "mixed-origin.html"
    template_source = "{{ title }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Mixed(Component):\n"
        "    citry = engine\n"
        "    template_file = 'mixed-origin.html'\n"
        "    class Kwargs:\n"
        "        title: str\n"
        "    def template_data(self, kwargs):\n"
        "        if flag:\n"
        "            return kwargs\n"
        "        return {'title': 42}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    items = completion_items(document, _position(template_source, "title", 3), project)
    target = definition(document, _position(template_source, "title", 3), project)

    assert [(item.label, item.detail) for item in items] == [("title", "Inferred from template_data()")]
    assert isinstance(target, list)
    assert [location.range.start.line for location in target] == [11, 7]


def test_shared_declared_and_inferred_root_keeps_both_definition_locations(tmp_path):
    template_file = tmp_path / "shared-declared-inferred.html"
    template_source = "{{ common }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Declared(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared-declared-inferred.html'\n"
        "    class TemplateData:\n"
        "        common: str\n"
        "class Inferred(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared-declared-inferred.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'common': 1}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    target = definition(document, _position(template_source, "common", 3), project)

    assert isinstance(target, list)
    assert [location.range.start.line for location in target] == [12, 7]


def test_field_definition_join_handles_utf8_columns_and_declines_ambiguity(tmp_path):
    source_file = tmp_path / "schema.py"
    source_file.write_text("class Schema:\n    café = None; title: str\n", encoding="utf-8")
    field = FieldRecord(
        name="title",
        required=True,
        type_display="str",
        type_fidelity="normalized",
        default_kind="missing",
        default_value_state="not-applicable",
        default_value=None,
        description=None,
        source_module="schema",
        source_qualname="Schema",
        source_file=source_file,
    )

    target = _field_definition_location(field)

    assert target is not None
    assert target.range == types.Range(types.Position(1, 17), types.Position(1, 22))

    synchronized = "# unsaved heading\nclass Schema:\n    title: str\n"
    synchronized_target = _field_definition_location(field, source=synchronized)
    assert synchronized_target is not None
    assert synchronized_target.range == types.Range(types.Position(2, 4), types.Position(2, 9))

    source_file.write_text("class Schema:\n    title: str\n    title: int\n", encoding="utf-8")
    assert _field_definition_location(field) is None


def test_open_field_source_join_matches_symlinked_editor_uri(tmp_path):
    source_file = tmp_path / "schema.py"
    source_file.write_text("class Schema:\n    title: str\n", encoding="utf-8")
    linked_file = tmp_path / "linked-schema.py"
    linked_file.symlink_to(source_file)
    synchronized = "# unsaved\nclass Schema:\n    title: str\n"
    document = DocumentState(linked_file.as_uri(), "python", synchronized, 2)

    assert _open_document_source(source_file, {linked_file.as_uri(): document}) == synchronized


def test_fill_slot_definition_uses_exact_nested_field_range():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _definition_analysis(),
        catalog,
    )
    source = '<c-definition-card><c-fill name="body">Body</c-fill></c-definition-card>'

    target = definition(_document(source, project), _position(source, 'name="body"', len('name="bo')), project)

    assert target is not None
    assert target.uri == Path(__file__).resolve().as_uri()
    source_lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    field_line = next(
        index for index, line in enumerate(source_lines) if line.strip() == "body: SlotInput[dict[str, object]]"
    )
    assert target.range == types.Range(
        types.Position(field_line, len("        ")),
        types.Position(field_line, len("        body")),
    )

    nested = "<c-unknown c-body=\"<><c-definition-card><c-fill name='body'>Body</c-fill></c-definition-card></>\" />"
    nested_target = definition(
        _document(nested, project),
        _position(nested, "name='body'", len("name='bo")),
        project,
    )
    assert nested_target == target


def test_slot_data_completion_and_hover_expose_known_shape():
    project = _registry_state()
    completion_source = '<c-card><c-fill name="body" data="{ ro'
    slot_hover_source = '<c-card><c-fill name="body" data="{ row }">{{ row }}</c-fill></c-card>'

    fields = completion_items(
        _document(completion_source, project),
        types.Position(0, len(completion_source)),
        project,
    )
    slot_hint = hover(
        _document(slot_hover_source, project),
        _position(slot_hover_source, 'name="body"', len('name="bo')),
        project,
    )
    data_hint = hover(
        _document(slot_hover_source, project),
        _position(slot_hover_source, "row }", 1),
        project,
    )
    component_hint = hover(
        _document(slot_hover_source, project),
        _position(slot_hover_source, "card", 2),
        project,
    )

    assert {item.label for item in fields} == {"row", "index"}
    assert slot_hint is not None
    assert isinstance(slot_hint.contents, types.MarkupContent)
    assert "Exposed data" in slot_hint.contents.value
    assert "`row`" in slot_hint.contents.value
    assert data_hint is not None
    assert isinstance(data_hint.contents, types.MarkupContent)
    assert "Data exposed by slot `body`" in data_hint.contents.value
    assert component_hint is not None
    assert isinstance(component_hint.contents, types.MarkupContent)
    assert "data: { row, index }" in component_hint.contents.value


def test_slot_data_completion_omits_bound_sources_and_declines_alias_targets():
    project = _registry_state()
    after_source = '<c-card><c-fill name="body" data="{ row, '
    alias_target = '<c-card><c-fill name="body" data="{ row as '

    after = completion_items(
        _document(after_source, project),
        types.Position(0, len(after_source)),
        project,
    )
    alias = completion_items(
        _document(alias_target, project),
        types.Position(0, len(alias_target)),
        project,
    )

    assert {item.label for item in after} == {"index"}
    assert alias == []


def test_loop_use_navigates_to_lexical_introduction_and_symbols_nest():
    project = _syntax_state()
    source = '<ul><li c-for="item in items"><span>{{ item }}</span></li></ul>'
    document = _document(source, project)

    target = definition(document, _position(source, "{{ item", 4), project)
    symbols = document_symbols(document)

    assert target is not None
    assert target.range.start == _position(source, "item in")
    assert symbols[0].name == "<ul>"
    assert symbols[0].children is not None
    assert symbols[0].children[0].name == "<li>"


def test_lexical_references_follow_one_binding_through_nested_templates():
    project = _syntax_state()
    source = (
        '<c-for each="item in outer">{{ item }}'
        '<c-card c-body="<>{{ item }}</>" />'
        "</c-for>"
        '<c-for each="item in other">{{ item }}</c-for>'
    )
    document = _document(source, project)
    position = _position(source, "{{ item", len("{{ it"))

    uses = references(document, position, project)
    with_declaration = references(document, position, project, include_declaration=True)
    declared = declaration(document, position, project)
    declaration_position = _position(source, "item in outer")
    declared_from_origin = declaration(document, declaration_position, project)

    assert uses is not None
    assert [location.range.start for location in uses] == [
        _position(source, "{{ item", len("{{ ")),
        _position(source, 'c-body="<>{{ item', len('c-body="<>{{ ')),
    ]
    assert with_declaration is not None
    assert [location.range.start for location in with_declaration] == [
        declaration_position,
        *[location.range.start for location in uses],
    ]
    assert declared is not None
    assert declared.range.start == declaration_position
    assert declared_from_origin == declared


def test_root_references_include_every_free_use_and_optional_python_origins():
    catalog = _definition_catalog()
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _definition_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    marker = "{{ template_user }}\n      <div"
    position = _position(source, marker, len("{{ template_"))

    uses = references(document, position, project, {document.uri: document})
    with_declaration = references(
        document,
        position,
        project,
        {document.uri: document},
        include_declaration=True,
    )
    declared = declaration(document, position, project, {document.uri: document})

    assert uses is not None
    assert len(uses) == 4
    assert all(location.uri == document.uri for location in uses)
    assert with_declaration is not None
    assert len(with_declaration) == 5
    field_line = next(index for index, line in enumerate(source.splitlines()) if line.strip() == "template_user: str")
    field_location = types.Location(
        source_file.as_uri(),
        types.Range(
            types.Position(field_line, len("        ")),
            types.Position(field_line, len("        template_user")),
        ),
    )
    assert field_location in with_declaration
    assert declared == field_location


@pytest.mark.parametrize("edit", ["delete-field", "invalid-source"])
def test_root_references_decline_stale_synchronized_schema_source(tmp_path: Path, edit: str):
    template_file = tmp_path / "card.html"
    template_source = "{{ user }} {{ user }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        user: str\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    synchronized_source = (
        app_source.replace("        user: str\n", "        pass\n")
        if edit == "delete-field"
        else app_source + "broken = (\n"
    )
    python_document = DocumentState(app_file.as_uri(), "python", synchronized_source, 2)
    python_document.update(synchronized_source, 2, project)
    documents = {document.uri: document, python_document.uri: python_document}
    position = _position(template_source, "user", 2)

    assert references(document, position, project, documents) is None
    assert references(document, position, project, documents, include_declaration=True) is None
    assert declaration(document, position, project, documents) is None


@pytest.mark.parametrize("edit", ["change-file", "delete-file", "invalid-source"])
def test_variable_features_decline_stale_synchronized_template_owner(tmp_path: Path, edit: str):
    template_file = tmp_path / "card.html"
    template_source = "{{ user }} {{ user }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        user: str\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    synchronized_source = {
        "change-file": app_source.replace("'card.html'", "'other.html'"),
        "delete-file": app_source.replace("template_file = 'card.html'", "template_file = None"),
        "invalid-source": app_source + "broken = (\n",
    }[edit]
    python_document = DocumentState(app_file.as_uri(), "python", synchronized_source, 2)
    python_document.update(synchronized_source, 2, project)
    documents = {document.uri: document, python_document.uri: python_document}
    position = _position(template_source, "user", 2)

    assert hover(document, position, project, documents) is None
    assert references(document, position, project, documents) is None
    assert declaration(document, position, project, documents) is None


def test_shared_template_filters_a_consumer_with_a_stale_inherited_owner(tmp_path: Path):
    template_file = tmp_path / "shared.html"
    template_source = "{{ shared }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Base(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    class TemplateData:\n"
        "        shared: str\n"
        "class Child(Base):\n"
        "    class TemplateData:\n"
        "        shared: int\n"
        "class Current(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    class TemplateData:\n"
        "        shared: str\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    synchronized_source = app_source.replace("class Child(Base):", "class Child(Component):")
    python_document = DocumentState(app_file.as_uri(), "python", synchronized_source, 2)
    python_document.update(synchronized_source, 2, project)
    documents = {document.uri: document, python_document.uri: python_document}

    targets = declaration(document, _position(template_source, "shared", 2), project, documents)

    assert isinstance(targets, list)
    assert {target.uri for target in targets} == {app_file.as_uri()}
    assert {target.range.start.line for target in targets} == {7, 15}


def test_open_unchanged_path_template_declaration_keeps_ownership(tmp_path: Path):
    template_file = tmp_path / "card.html"
    template_source = "{{ user }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = Path('card.html')\n"
        "    class TemplateData:\n"
        "        user: str\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    python_document = DocumentState(app_file.as_uri(), "python", app_source, 1)
    python_document.update(app_source, 1, project)
    documents = {document.uri: document, python_document.uri: python_document}
    position = _position(template_source, "user", 2)

    assert references(document, position, project, documents)
    assert declaration(document, position, project, documents) is not None


def test_dynamic_template_owner_is_withheld_when_its_source_is_synchronized(tmp_path: Path):
    template_file = tmp_path / "card.html"
    template_source = "{{ user }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    exec(\"template_file = 'card.html'\")\n"
        "    class TemplateData:\n"
        "        user: str\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    position = _position(template_source, "user", 2)
    assert references(document, position, project, {document.uri: document})

    synchronized = app_source.replace("card.html", "other.html")
    python_document = DocumentState(app_file.as_uri(), "python", synchronized, 2)
    python_document.update(synchronized, 2, project)
    documents = {document.uri: document, python_document.uri: python_document}

    assert references(document, position, project, documents) is None
    assert declaration(document, position, project, documents) is None


def test_imported_template_owner_is_withheld_for_synchronized_external_source(tmp_path: Path):
    template_file = tmp_path / "card.html"
    template_source = "{{ user }}"
    template_file.write_text(template_source, encoding="utf-8")
    settings_file = tmp_path / "settings.py"
    settings_source = "CARD_TEMPLATE = 'card.html'\n"
    settings_file.write_text(settings_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from citry import Citry, Component\n"
        "from settings import CARD_TEMPLATE\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = CARD_TEMPLATE\n"
        "    class TemplateData:\n"
        "        user: str\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    position = _position(template_source, "user", 2)
    assert references(document, position, project, {document.uri: document})

    synchronized_source = settings_source.replace("card.html", "other.html")
    python_document = DocumentState(settings_file.as_uri(), "python", synchronized_source, 2)
    python_document.update(synchronized_source, 2, project)
    documents = {document.uri: document, python_document.uri: python_document}

    assert references(document, position, project, documents) is None
    assert declaration(document, position, project, documents) is None


def test_loop_variables_complete_and_hover_without_a_registry():
    project = _syntax_state()
    source = '<c-for each="item, index in items"><span>{{ item }}</span></c-for>'
    document = _document(source, project)

    items = completion_items(document, _position(source, "{{ it", len("{{ it")), project)
    hint = hover(document, _position(source, "{{ item", len("{{ it")), project)

    assert {item.label for item in items} == {"item", "index"}
    assert all("loop variable" in (item.detail or "") for item in items)
    assert hint is not None
    assert isinstance(hint.contents, types.MarkupContent)
    assert hint.contents.value == ("```python\n(variable) item\n```\n\nLoop variable introduced by c-for.")


def test_shorthand_loop_variable_is_in_scope_for_same_element_python_attributes():
    project = _syntax_state()
    source = '<li c-for="item in items" c-title="item">{{ item }}</li>'
    document = _document(source, project)

    items = completion_items(document, _position(source, 'c-title="it', len('c-title="it')), project)
    target = definition(document, _position(source, 'c-title="item', len('c-title="it')), project)

    assert {item.label for item in items} == {"item"}
    assert target is not None
    assert target.range.start == _position(source, "item in")


def test_fill_bindings_complete_and_describe_alias_rest_and_fallback():
    project = _syntax_state()
    source = (
        '<c-card><c-fill name="body" data="{row, source as alias, **rest}" fallback="fallback">'
        "{{ alias }} {{ rest }} {{ fallback }}"
        "</c-fill></c-card>"
    )
    document = _document(source, project)

    items = completion_items(document, _position(source, "{{ al", len("{{ al")), project)
    alias_hint = hover(document, _position(source, "{{ alias", len("{{ al")), project)
    fallback_hint = hover(document, _position(source, "{{ fallback", len("{{ fall")), project)

    assert {item.label for item in items} == {"row", "alias", "rest", "fallback"}
    by_label = {item.label: item for item in items}
    assert "source" in (by_label["alias"].detail or "")
    assert "remaining slot data" in (by_label["rest"].detail or "")
    assert alias_hint is not None
    assert isinstance(alias_hint.contents, types.MarkupContent)
    assert alias_hint.contents.value == (
        "```python\n(variable) alias\n```\n\nSlot-data variable introduced from 'source' by c-fill."
    )
    assert fallback_hint is not None
    assert isinstance(fallback_hint.contents, types.MarkupContent)
    assert fallback_hint.contents.value == (
        "```python\n(variable) fallback\n```\n\nFallback variable introduced by c-fill."
    )


def test_fill_c_bind_clears_and_later_direct_attributes_restore_bindings():
    project = _syntax_state()
    cleared = '<c-card><c-fill name="body" data="{row}" fallback="empty" c-bind="attrs">{{ row }}</c-fill></c-card>'
    restored = '<c-card><c-fill name="body" c-bind="attrs" data="{row}" fallback="empty">{{ row }}</c-fill></c-card>'

    cleared_items = completion_items(
        _document(cleared, project),
        _position(cleared, "{{ row", len("{{ ro")),
        project,
    )
    restored_items = completion_items(
        _document(restored, project),
        _position(restored, "{{ row", len("{{ ro")),
        project,
    )

    assert cleared_items == []
    assert {item.label for item in restored_items} == {"row", "empty"}


def test_incomplete_interpolation_recovers_only_active_complete_bindings():
    project = _syntax_state()
    active = '<div c-for="item in items"><span>{{ it'
    sibling = '<div c-for="item in items"></div><span>{{ it'
    nested = "<c-card c-body=\"<><div c-for='item in items'>{{ it"

    active_items = completion_items(_document(active, project), types.Position(0, len(active)), project)
    sibling_items = completion_items(_document(sibling, project), types.Position(0, len(sibling)), project)
    nested_items = completion_items(_document(nested, project), types.Position(0, len(nested)), project)

    assert {item.label for item in active_items} == {"item"}
    assert sibling_items == []
    assert {item.label for item in nested_items} == {"item"}


def test_incomplete_recovery_ignores_comments_and_raw_text_that_look_like_tags():
    project = _syntax_state()
    sources = (
        '{# <div c-for="fake in xs"> #}{{ fa',
        '<script><div c-for="fake in xs">{{ fa',
        '<style><div c-for="fake in xs">{{ fa',
        '<textarea><div c-for="fake in xs">{{ fa',
        '<title><div c-for="fake in xs">{{ fa',
        '<c-raw><div c-for="fake in xs">{{ fa',
    )

    for source in sources:
        items = completion_items(_document(source, project), types.Position(0, len(source)), project)
        assert items == []


def test_comment_and_c_raw_braces_do_not_activate_expression_completion():
    project = _syntax_state()
    sources = (
        '<div c-for="item in xs">{# {{ #}',
        '<div c-for="item in xs"><!-- {{ -->',
        '<div c-for="item in xs"><c-raw>{{</c-raw>',
    )

    for source in sources:
        items = completion_items(_document(source, project), types.Position(0, len(source)), project)
        assert items == []


def test_c_raw_prefixed_component_does_not_mask_later_expression():
    project = _syntax_state()
    source = '<div c-for="item in xs"><c-rawish></c-rawish>{{ it'

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert {item.label for item in items} == {"item"}


def test_incomplete_recovery_ignores_tag_text_inside_completed_python_strings():
    project = _syntax_state()
    fake_open = "{{ \"<div c-for='fake in xs'>\" }}{{ fa"
    fake_close = '<div c-for="item in xs">{{ "</div>" }}{{ it'

    opened = completion_items(_document(fake_open, project), types.Position(0, len(fake_open)), project)
    retained = completion_items(_document(fake_close, project), types.Position(0, len(fake_close)), project)

    assert opened == []
    assert {item.label for item in retained} == {"item"}


def test_completed_same_line_python_comment_does_not_hide_later_bindings():
    project = _syntax_state()
    source = '<div c-for="outer in xs">{{ outer # comment }}<span c-for="inner in ys">{{ in'

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert {item.label for item in items} == {"outer", "inner"}


def test_incomplete_nested_template_keeps_outer_and_inner_bindings():
    project = _syntax_state()
    source = '<div c-for="outer in outers" c-body="<><span c-for=\'inner in inners\'>{{ ou'

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert {item.label for item in items} == {"outer", "inner"}


@pytest.mark.parametrize("operator", ["<", ">"])
def test_comparison_in_unfinished_expression_attribute_keeps_outer_binding(operator):
    project = _syntax_state()
    source = f'<div c-for="item in items"><span c-if="item {operator} it'

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert {item.label for item in items} == {"item"}


def test_live_shorthand_loop_binding_is_available_later_on_same_start_tag():
    project = _syntax_state()
    source = '<li c-for="item in items" c-title="it'

    items = completion_items(_document(source, project), types.Position(0, len(source)), project)

    assert {item.label for item in items} == {"item"}


def test_nested_template_lexical_navigation_keeps_host_offsets():
    project = _syntax_state()
    nested_values = (
        "<><div c-for='item in items'>{{ item }}</div></>",
        "<div c-for='item in items'>{{ item }}</div>",
        "\N{EM SPACE}<><div c-for='item in items'>{{ item }}</div></>",
    )
    for nested in nested_values:
        source = f'<c-card c-body="{nested}" />'
        document = _document(source, project)

        items = completion_items(document, _position(source, "{{ item", len("{{ it")), project)
        target = definition(document, _position(source, "{{ item", len("{{ it")), project)

        assert {item.label for item in items} == {"item"}
        assert target is not None
        assert target.range.start == _position(source, "item in")


def test_lexical_definition_matches_python_nfkc_identifier_identity():
    project = _syntax_state()
    kelvin = "\N{KELVIN SIGN}"
    source = f'<c-for each="{kelvin} in items">{{{{ K }}}}</c-for>'
    document = _document(source, project)

    target = definition(document, _position(source, "{{ K", len("{{ ")), project)

    assert target is not None
    assert target.range.start == _position(source, f"{kelvin} in")


def test_unicode_lexical_hover_and_member_hover_use_exact_parser_token_ranges():
    project = _syntax_state()
    source = '<c-for each="é in items">{{ é.name }}</c-for>'
    document = _document(source, project)

    declaration = hover(document, _position(source, "é in"), project)
    use = hover(document, _position(source, "é.name"), project)

    assert declaration is not None
    assert declaration.range == types.Range(_position(source, "é in"), _position(source, "é in", 1))
    assert use is not None
    assert use.range == types.Range(_position(source, "é.name"), _position(source, "é.name", 1))


def test_inline_python_diagnostic_maps_back_to_authored_literal():
    source = 'from citry import Component\nclass Broken(Component):\n    template = """😀<div>"""\n'
    document = _document(source, _syntax_state(), language_id="python")

    assert len(document.diagnostics) == 1
    assert document.diagnostics[0].range.start.line == 2


def test_registry_owns_only_catalog_resolved_html_assets(tmp_path):
    template_path = tmp_path / "card.html"
    template_path.write_text("<div>", encoding="utf-8")
    engine = Citry(dirs=[tmp_path], autodiscover=False)

    class FileCard(Component):
        citry = engine
        template_file = "card.html"

    catalog = CatalogIndex(engine.inspect_components(include_builtins=True, resolve_assets=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(tmp_path), mode="registry", registry_ready=True),
        engine.template_analysis(),
        catalog,
    )
    associated = DocumentState(template_path.as_uri(), "html", "<div>", 1)
    unrelated = DocumentState((tmp_path / "other.html").as_uri(), "html", "<div>", 1)

    associated.update("<div>", 1, project)
    unrelated.update("<div>", 1, project)

    assert len(associated.diagnostics) == 1
    assert unrelated.diagnostics == ()


def test_non_template_document_and_syntax_mode_expose_no_registry_features():
    project = _syntax_state()
    document = _document("plain text", project, language_id="plaintext")
    position = types.Position(0, 0)

    assert document.parsed_at(position) is None
    assert completion_items(document, position, project) == []
    assert hover(document, position, project) is None
    assert definition(document, position, project) is None
    assert document_symbols(document) == []

    registry = _registry_state()
    assert completion_items(document, position, registry) == []
    assert hover(document, position, registry) is None


def test_last_good_parse_is_retained_without_serving_stale_navigation():
    project = _syntax_state()
    document = _document("<div />", project)
    position = types.Position(0, 2)

    assert document.parsed_at(position) is not None

    document.update("<div>", 2, project)

    assert document.parsed_at(position) is not None
    assert definition(document, position, project) is None
    assert document.diagnostics


def test_completion_scanner_handles_existing_fields_values_and_orphan_fills():
    project = _registry_state()
    existing_source = '<c-card title="done" '
    quoted_source = '<c-card title="unfi'
    orphan_fill_source = '<c-fill name="bo'

    existing = completion_items(
        _document(existing_source, project),
        types.Position(0, len(existing_source)),
        project,
    )
    quoted = completion_items(
        _document(quoted_source, project),
        _position(quoted_source, "unfi", 4),
        project,
    )
    orphan_fill = completion_items(
        _document(orphan_fill_source, project),
        _position(orphan_fill_source, "bo", 2),
        project,
    )

    assert "title" not in {item.label for item in existing}
    assert "count" in {item.label for item in existing}
    assert quoted == []
    assert orphan_fill == []


def test_component_kwarg_and_slot_tooling_remains_case_sensitive():
    project = _registry_state()
    attr_source = '<c-card TITLE="wrong" '
    slot_source = '<c-card><c-fill name="BODY" />'

    attrs = completion_items(
        _document(attr_source, project),
        types.Position(0, len(attr_source)),
        project,
    )
    slot_hint = hover(
        _document(slot_source, project),
        _position(slot_source, "BODY", 2),
        project,
    )

    assert "title" in {item.label for item in attrs}
    assert slot_hint is None


def test_hover_and_definition_decline_unknown_or_unparsed_targets():
    project = _registry_state()
    source = "<section>plain</section>"
    document = _document(source, project)

    assert hover(document, _position(source, "plain", 2), project) is None
    assert definition(document, _position(source, "plain", 2), project) is None

    whitespace_source = "<section> </section>"
    whitespace = _document(whitespace_source, project)
    whitespace_position = _position(whitespace_source, " ")
    assert completion_items(whitespace, whitespace_position, project) == []
    assert hover(whitespace, whitespace_position, project) is None


def test_nested_unknown_component_and_self_closing_symbol_are_mapped():
    project = _registry_state()
    nested_source = "<section><c-ghost /></section>"
    symbol_source = "<br />"

    nested = _document(nested_source, project)
    symbols = document_symbols(_document(symbol_source, project))

    assert [diagnostic.code for diagnostic in nested.diagnostics] == ["citry.template.unknown-component"]
    assert nested.diagnostics[0].range.start.character == nested_source.index("c-ghost")
    assert symbols[0].name == "<br>"
    assert symbols[0].children is None

    fragment_source = '<div c-body="<><c-ghost /></>"></div>'
    fragment = _document(fragment_source, project)
    assert [diagnostic.code for diagnostic in fragment.diagnostics] == ["citry.template.unknown-component"]
    assert fragment.diagnostics[0].range.start.character == fragment_source.index("c-ghost")


def test_configuration_parse_error_uses_zero_width_fallback(monkeypatch):
    def fail(_source):
        raise ValueError("configuration failed")

    monkeypatch.setattr("citry_lsp.engine.parse_template", fail)
    document = _document("<div />", _syntax_state())

    assert document.diagnostics[0].code == "citry.parse.configuration"
    assert document.diagnostics[0].code_description == types.CodeDescription(
        "https://citry.dev/ide/diagnostics/#citry.parse.configuration"
    )
    assert document.diagnostics[0].range.start == types.Position(0, 0)
