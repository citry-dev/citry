"""Tests for diagnostics and narrow editor intelligence."""

from __future__ import annotations

from pathlib import Path

import pytest
from lsprotocol import types

from citry import Citry, Component, ComponentLibrary, LibraryComponent, SlotInput
from citry_core.template_parser import RESERVED_TAG_NAMES
from citry_lsp.catalog import CatalogIndex, FieldRecord
from citry_lsp.engine import (
    DocumentState,
    _field_definition_location,
    _open_document_source,
    _template_data_fields,
    completion_items,
    completion_result,
    definition,
    document_symbols,
    hover,
)
from citry_lsp.project import ProjectState
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


def _registry_state() -> ProjectState:
    engine = Citry(autodiscover=False)

    class Card(Component):
        """Render a documented card."""

        citry = engine
        template = '<article><c-slot name="body" /></article>'

        class Kwargs:
            title: str
            count: int = 0

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


def _component_matching_state() -> ProjectState:
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


def _document(source: str, project: ProjectState, *, language_id: str = "citry-html") -> DocumentState:
    document = DocumentState("file:///template.html", language_id, source, 1)
    document.update(source, 1, project)
    return document


def _position(source: str, marker: str, offset: int = 0) -> types.Position:
    index = source.index(marker) + offset
    before = source[:index]
    return types.Position(before.count("\n"), len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2)


def test_syntax_diagnostic_uses_parser_code_and_exact_range():
    source = "😀<div>"
    document = _document(source, _syntax_state())

    assert len(document.diagnostics) == 1
    diagnostic = document.diagnostics[0]
    assert diagnostic.code == "citry.parse.syntax"
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

    assert [item.code for item in registry.diagnostics] == ["citry.component.unknown"]
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


def test_component_definition_uses_exact_top_level_class_name_range():
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _DEFINITION_ENGINE.template_analysis(),
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
    assert "TemplateData field" in hint.contents.value
    assert "str (required)" in hint.contents.value
    assert target is not None
    field_line = next(index for index, line in enumerate(source.splitlines()) if line.strip() == "template_user: str")
    assert target.uri == source_file.as_uri()
    assert target.range == types.Range(
        types.Position(field_line, len("        ")),
        types.Position(field_line, len("        template_user")),
    )


def test_inline_template_data_uses_asset_owner_provenance_for_an_unregistered_library_base():
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
        catalog,
    )
    source_file = Path(__file__).resolve()
    source = source_file.read_text(encoding="utf-8")
    document = DocumentState(source_file.as_uri(), "python", source, 1)
    document.update(source, 1, project)

    items = completion_items(document, _position(source, marker, offset), project)

    assert {"template_user", "items", "shared_count", "café"} <= {item.label for item in items}


def test_template_data_hover_joins_only_the_exact_free_root_token():
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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


def test_template_data_completion_replaces_the_complete_identifier_around_cursor():
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(interpreter="python", workspace=str(Path.cwd()), mode="registry", registry_ready=True),
        _DEFINITION_ENGINE.template_analysis(),
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
    catalog = CatalogIndex(_DEFINITION_ENGINE.inspect_components(include_builtins=True).to_dict())
    project = ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="tests.test_engine:_DEFINITION_ENGINE",
            mode="registry",
            registry_ready=True,
        ),
        _DEFINITION_ENGINE.template_analysis(),
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
    assert "Loop variable introduced by c-for" in hint.contents.value


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
    assert "from 'source'" in alias_hint.contents.value
    assert fallback_hint is not None
    assert isinstance(fallback_hint.contents, types.MarkupContent)
    assert "Fallback variable" in fallback_hint.contents.value


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

    assert [diagnostic.code for diagnostic in nested.diagnostics] == ["citry.component.unknown"]
    assert nested.diagnostics[0].range.start.character == nested_source.index("c-ghost")
    assert symbols[0].name == "<br>"
    assert symbols[0].children is None

    fragment_source = '<div c-body="<><c-ghost /></>"></div>'
    fragment = _document(fragment_source, project)
    assert [diagnostic.code for diagnostic in fragment.diagnostics] == ["citry.component.unknown"]
    assert fragment.diagnostics[0].range.start.character == fragment_source.index("c-ghost")


def test_configuration_parse_error_uses_zero_width_fallback(monkeypatch):
    def fail(_source):
        raise ValueError("configuration failed")

    monkeypatch.setattr("citry_lsp.engine.parse_template", fail)
    document = _document("<div />", _syntax_state())

    assert document.diagnostics[0].code == "citry.parse.configuration"
    assert document.diagnostics[0].range.start == types.Position(0, 0)
