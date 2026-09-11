"""State binding keys use the owning component's public schema in every template host."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest
from lsprotocol import types

from citry import Citry, Component
from citry._checker import _check_template, _TemplateSource
from citry.analysis import browser_state_bindings
from citry_core.template_parser import parse_template
from citry_lsp.engine import DocumentState, browser_diagnostics, completion_items, definition, hover
from citry_lsp.project import ProjectState, load_project

if TYPE_CHECKING:
    from pathlib import Path


def _position(source: str, marker: str, offset: int = 0) -> types.Position:
    before = source[: source.index(marker) + offset]
    return types.Position(before.count("\n"), len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2)


def _owned_document(tmp_path: Path, mode: str, template: str) -> tuple[ProjectState, DocumentState]:
    if mode == "nested":
        template = f"<div c-title='<>{template}</>'></div>"
    app_source = """from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
class Card(Component):
    citry = engine
    class State:
        query: str
        time: int
        secret: str
        _public = ('query', 'time')
    class Events:
        def refresh(self):
            pass
"""
    if mode == "inline":
        app_source += f'    template = """\n{template}\n    """\n'
    else:
        app_source += "    template_file = 'card.html'\n"
        (tmp_path / "card.html").write_text(template, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready
    path = app_file if mode == "inline" else tmp_path / "card.html"
    source = app_source if mode == "inline" else template
    document = DocumentState(path.as_uri(), "python" if mode == "inline" else "citry-html", source, 1)
    document.update(source, 1, project)
    return project, document


@pytest.mark.parametrize("mode", ["standalone", "inline", "nested"])
@pytest.mark.parametrize("template", ["<input :c->", "<input :c-"])
def test_state_completion_uses_public_fields_in_every_template_host(tmp_path, mode, template):
    project, document = _owned_document(tmp_path, mode, template)

    items = completion_items(document, _position(document.source, ":c-", 3), project)

    assert [item.label for item in items] == [":c-query", ":c-time"]
    assert all(item.text_edit.new_text == item.label for item in items)


@pytest.mark.parametrize("mode", ["standalone", "inline", "nested"])
def test_state_key_diagnostic_has_only_the_field_range(tmp_path, mode):
    project, document = _owned_document(tmp_path, mode, '😀<input :c-querylol.debounce="refresh">')

    findings = browser_diagnostics(document, project)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.code == "citry.browser.unknown-state-field"
    assert finding.severity == types.DiagnosticSeverity.Error
    assert finding.range == types.Range(
        _position(document.source, "querylol"), _position(document.source, "querylol", len("querylol"))
    )


def test_state_completion_replaces_the_base_without_changing_modifiers_or_handler(tmp_path):
    project, document = _owned_document(tmp_path, "standalone", '<input :c-querylol.debounce.300ms="refresh">')
    items = completion_items(document, _position(document.source, ":c-qu", 5), project)

    assert [item.label for item in items] == [":c-query"]
    edit = items[0].text_edit
    assert edit.new_text == ":c-query"
    assert edit.range == types.Range(_position(document.source, ":c-"), _position(document.source, ".debounce"))


def test_valid_state_keeps_modifier_and_handler_intelligence(tmp_path):
    project, document = _owned_document(tmp_path, "standalone", '<input :c-query.debounce.300ms="refresh">')
    assert browser_diagnostics(document, project) == ()
    state_position = _position(document.source, "query", 2)
    assert "(field) query: str" in hover(document, state_position, project).contents.value
    assert definition(document, state_position, project).uri == (tmp_path / "app.py").as_uri()
    modifiers = completion_items(document, _position(document.source, ".debounce", 1), project)
    assert ".debounce" in {item.label for item in modifiers}
    handlers = completion_items(document, _position(document.source, "refresh", 2), project)
    assert [item.label for item in handlers] == ["refresh"]


def test_private_state_fields_are_rejected_and_unknown_schemas_remain_open(tmp_path):
    project, document = _owned_document(tmp_path, "standalone", '<input :c-secret="refresh"><input :c->')
    assert [finding.code for finding in browser_diagnostics(document, project)] == [
        "citry.browser.unknown-state-field"
    ]
    # Missing schema evidence is distinct from a proven empty public schema.
    project = replace(project, source_analysis=None)
    assert browser_diagnostics(document, project) == ()
    assert completion_items(document, _position(document.source, ":c->", 3), project) == []


def test_state_completion_and_diagnostics_do_not_claim_an_unowned_template(tmp_path):
    project, document = _owned_document(tmp_path, "standalone", "<input :c-querylol><input :c->")
    document.uri = (tmp_path / "unowned.html").as_uri()
    assert browser_diagnostics(document, project) == ()
    assert completion_items(document, _position(document.source, ":c->", 3), project) == []


def test_shared_template_uses_only_fields_accepted_by_every_owner(tmp_path):
    _project, document = _owned_document(tmp_path, "standalone", "<input :c-time><input :c->")
    app_file = tmp_path / "app.py"
    app_file.write_text(
        app_file.read_text(encoding="utf-8")
        + """
class Other(Component):
    citry = engine
    class State:
        query: str
    template_file = 'card.html'
""",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document.update(document.source, 2, project)
    items = completion_items(document, _position(document.source, ":c->", 3), project)
    assert [item.label for item in items] == [":c-query"]
    assert [finding.code for finding in browser_diagnostics(document, project)] == [
        "citry.browser.unknown-state-field"
    ]


def test_stale_state_declaration_suppresses_state_key_claims(tmp_path):
    project, document = _owned_document(tmp_path, "standalone", "<input :c-querylol><input :c->")
    app_file = tmp_path / "app.py"
    # Removing a previously loaded field invalidates the public schema until
    # the app worker can refresh it from the synchronized Python source.
    source = app_file.read_text(encoding="utf-8").replace("        query: str\n", "")
    python = DocumentState(app_file.as_uri(), "python", source, 2)
    python.update(source, 2, project)
    documents = {python.uri: python, document.uri: document}
    assert browser_diagnostics(document, project, documents) == ()
    assert completion_items(document, _position(document.source, ":c->", 3), project, documents) == []


@pytest.mark.parametrize("saved", [False, True])
@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("        query: str", "        query: str\n        added: bool"),
        ("_public = ('query', 'time')", "_public = ('query', 'time', 'secret')"),
        ("    class State:", "    class State(dict):"),
    ],
)
def test_changed_state_namespace_is_open_until_worker_refresh(tmp_path, saved, old, new):
    project, document = _owned_document(tmp_path, "standalone", "<input :c-added><input :c->")
    app_file = tmp_path / "app.py"
    source = app_file.read_text(encoding="utf-8").replace(old, new)
    if saved:
        app_file.write_text(source, encoding="utf-8")
        documents = None
    else:
        python = DocumentState(app_file.as_uri(), "python", source, 2)
        python.update(source, 2, project)
        documents = {python.uri: python, document.uri: document}

    assert browser_diagnostics(document, project, documents) == ()
    assert completion_items(document, _position(document.source, ":c->", 3), project, documents) == []


def test_new_state_declaration_does_not_reuse_a_known_empty_namespace(tmp_path):
    _project, document = _owned_document(tmp_path, "standalone", "<input :c-new><input :c->")
    app_file = tmp_path / "app.py"
    original = app_file.read_text(encoding="utf-8")
    start, end = original.index("    class State:"), original.index("    class Events:")
    without_state = original[:start] + original[end:]
    app_file.write_text(without_state, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document.update(document.source, 2, project)
    assert len(browser_diagnostics(document, project)) == 1

    app_file.write_text(original, encoding="utf-8")
    assert browser_diagnostics(document, project) == ()
    assert completion_items(document, _position(document.source, ":c->", 3), project) == []


def test_editing_only_inline_template_preserves_state_key_intelligence(tmp_path):
    project, document = _owned_document(tmp_path, "inline", "<input :c-querylol><input :c->")
    document.update(document.source.replace("<input", "<br><input", 1), 2, project)
    documents = {document.uri: document}

    assert len(browser_diagnostics(document, project, documents)) == 1
    items = completion_items(document, _position(document.source, ":c->", 3), project, documents)
    assert [item.label for item in items] == [":c-query", ":c-time"]


def test_inherited_visibility_without_field_origins_is_part_of_state_snapshot(tmp_path):
    _project, document = _owned_document(tmp_path, "standalone", "<input :c-secret><input :c->")
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        """class Visibility:
    _public = ('query',)
""",
        encoding="utf-8",
    )
    app_file = tmp_path / "app.py"
    source = app_file.read_text(encoding="utf-8")
    source = "from schema import Visibility\n" + source.replace("class State:", "class State(Visibility):")
    source = source.replace("        _public = ('query', 'time')\n", "")
    app_file.write_text(source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document.update(document.source, 2, project)
    assert len(browser_diagnostics(document, project)) == 1
    items = completion_items(document, _position(document.source, ":c->", 3), project)
    assert [item.label for item in items] == [":c-query"]

    schema_file.write_text("class Visibility:\n    _public = ('query', 'secret')\n", encoding="utf-8")
    assert browser_diagnostics(document, project) == ()
    assert completion_items(document, _position(document.source, ":c->", 3), project) == []


def test_portable_state_keys_skip_comments_and_plain_attribute_values():
    source = '😀<!-- <input :c-fake> --><div title=":c-fake"><input :c-query.debounce></div>'
    bindings = browser_state_bindings(parse_template(source))

    assert len(bindings) == 1
    assert bindings[0].name == "query"
    assert source.encode("utf-8")[bindings[0].start_index : bindings[0].end_index] == b"query"


def test_batch_checker_uses_the_same_public_state_key_contract():
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine

        class State:
            query: str
            secret: str
            _public = ("query",)

        template = """
        <input :c-query><input :c-secret.debounce><input :c-querylol>
        """

    engine.initialize()
    source = _TemplateSource("test.html", Card.template, [Card])
    findings = _check_template(source)

    assert [finding.code for finding in findings] == ["citry.browser.unknown-state-field"] * 2
    assert [source.content.encode()[finding.start_index : finding.end_index] for finding in findings] == [
        b"secret",
        b"querylol",
    ]
    assert _check_template(_TemplateSource("test.html", source.content, [])) == []
