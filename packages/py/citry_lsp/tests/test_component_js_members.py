"""Component JavaScript names retain their types and authored binding targets."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from lsprotocol import types

from citry import Citry, Component
from citry._checker import _BrowserSource, _check_browser_source
from citry.analysis import lint_unknown_component_js_members
from citry_lsp.engine import DocumentState, browser_diagnostics, declaration, definition, references
from citry_lsp.project import load_project

if TYPE_CHECKING:
    from pathlib import Path


def _position(source: str, marker: str, offset: int = 0) -> types.Position:
    before = source[: source.index(marker) + offset]
    return types.Position(before.count("\n"), len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2)


def _project_document(
    tmp_path: Path, javascript: str, *, standalone: bool = False, declared: bool = False, open_data: bool = False
):
    app_source = """from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
class Card(Component):
    citry = engine
    def js_data(self, kwargs, slots):
        return {"a": "str", "b": 1}
"""
    if declared:
        app_source += "    class JsData:\n        a: str\n        b: int\n"
    if open_data:
        app_source = app_source.replace('return {"a": "str", "b": 1}', 'return {"a": "str", **kwargs.extra}')
    if standalone:
        app_source += "    js_file = 'card.js'\n"
        (tmp_path / "card.js").write_text(javascript, encoding="utf-8")
    else:
        app_source += f'    js = """\n{javascript}\n    """\n'
    app_path = tmp_path / "app.py"
    app_path.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready
    path = tmp_path / "card.js" if standalone else app_path
    source = javascript if standalone else app_source
    document = DocumentState(path.as_uri(), "javascript" if standalone else "python", source, 1)
    document.update(source, 1, project)
    return project, document


@pytest.mark.parametrize("standalone", [False, True])
@pytest.mark.parametrize("configuration", [False, True])
def test_callback_alias_navigation_follows_its_binding_and_excludes_shadowed_names(
    tmp_path, standalone, configuration
):
    body = """
        // 😀 keeps source ranges honest across UTF-8 and UTF-16.
        console.log(payload.b);
        function nested(payload) { return payload.other; }
        const read = () => payload.a;
    """
    javascript = (
        f"$component({{ init({{ data: payload }}) {{{body}}} }});"
        if configuration
        else f"$component(({{ data: payload }}) => {{{body}}});"
    )
    project, document = _project_document(tmp_path, javascript, standalone=standalone)
    source = document.source
    use = _position(source, "payload.b", 3)
    target = types.Location(
        document.uri,
        types.Range(_position(source, "data: payload", 6), _position(source, "data: payload", 13)),
    )

    assert definition(document, use, project) == target
    assert declaration(document, use, project) == target
    found = references(document, use, project, include_declaration=True)
    assert found is not None
    assert len(found) == 3
    assert target in found
    assert definition(document, _position(source, "payload.other", 3), project) is None


def test_callback_navigation_does_not_guess_when_javascript_is_invalid(tmp_path):
    project, document = _project_document(tmp_path, "$component(({ data }) => { data.; });")
    assert definition(document, _position(document.source, "data.;", 2), project) is None


@pytest.mark.parametrize("standalone", [False, True])
@pytest.mark.parametrize("declared", [False, True])
def test_unknown_data_member_has_exact_field_range_and_clears_after_edit(tmp_path, standalone, declared):
    javascript = '$component(({ data: payload }) => { console.log("😀", payload.c, payload.b); });'
    project, document = _project_document(tmp_path, javascript, standalone=standalone, declared=declared)
    diagnostics = browser_diagnostics(document, project, {document.uri: document})

    assert len(diagnostics) == 1
    finding = diagnostics[0]
    assert finding.code == "citry.component-js.unknown-data-member"
    assert finding.severity == types.DiagnosticSeverity.Error
    assert finding.range == types.Range(
        _position(document.source, "payload.c", 8), _position(document.source, "payload.c", 9)
    )
    document.update(document.source.replace("payload.c", "payload.a"), 2, project)
    assert browser_diagnostics(document, project, {document.uri: document}) == ()


def test_open_inferred_data_does_not_create_a_closed_namespace(tmp_path):
    project, document = _project_document(
        tmp_path, "$component(({ data }) => { console.log(data.dynamic); });", open_data=True
    )
    assert browser_diagnostics(document, project, {document.uri: document}) == ()


def test_unsaved_js_data_declaration_supplies_a_new_field(tmp_path):
    project, document = _project_document(
        tmp_path, "$component(({ data }) => { console.log(data.c); });", declared=True
    )
    assert len(browser_diagnostics(document, project, {document.uri: document})) == 1
    document.update(document.source.replace("        b: int", "        b: int\n        c: bool"), 2, project)
    assert browser_diagnostics(document, project, {document.uri: document}) == ()


def test_changed_js_data_extra_policy_defers_diagnostics_until_registry_reload(tmp_path):
    source = '''from citry import Citry, Component
from pydantic import BaseModel, ConfigDict
engine = Citry(autodiscover=False)
class Card(Component):
    citry = engine
    class JsData(BaseModel):
        model_config = ConfigDict(extra="forbid")
        a: str
    js = """
        $component(({ data }) => { console.log(data.extra); });
    """
'''
    path = tmp_path / "app.py"
    path.write_text(source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready
    document = DocumentState(path.as_uri(), "python", source, 1)
    document.update(source, 1, project)
    assert len(browser_diagnostics(document, project, {document.uri: document})) == 1

    document.update(source.replace('extra="forbid"', 'extra="allow"'), 2, project)
    assert browser_diagnostics(document, project, {document.uri: document}) == ()


@pytest.mark.parametrize(
    "javascript",
    [
        '$component(({ data }) => { console.log(data.b, "data.c"); });',
        "$component(({ data }) => { data.toString(); data.hasOwnProperty('b'); });",
        "$component(({ data }) => { function read(data) { return data.c; } });",
        "$component(({ data }) => { data = {}; console.log(data.c); });",
        "$component(({ data }) => { console.log(data[dynamicKey]); });",
        "$component(({ data = {} }) => { console.log(data.c); });",
        "$component(({ data }) => { data.; });",
    ],
)
def test_data_member_analysis_excludes_unproven_objects_and_dynamic_keys(javascript):
    assert lint_unknown_component_js_members(javascript, frozenset({"a", "b"})) == ()


def test_data_member_analysis_handles_aliases_bracket_keys_and_closure_captures():
    source = """$component({ init({ data: payload }) {
        const read = () => `${payload.missing}`;
        console.log(payload?.other, payload["third"]);
    } });"""
    findings = lint_unknown_component_js_members(source, frozenset({"a", "b"}))
    assert [finding.name for finding in findings] == ["missing", "other", "third"]
    encoded = source.encode("utf-8")
    assert [encoded[finding.start_index : finding.end_index].decode() for finding in findings] == [
        "missing",
        "other",
        "third",
    ]
    assert lint_unknown_component_js_members(source, None) == ()


def test_checker_and_lsp_share_unknown_data_member_diagnostics(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine

        class JsData:
            a: str
            b: int

    javascript = "$component(({ data }) => { console.log(data.c); });"
    findings = _check_browser_source(engine, _BrowserSource("card.js", javascript, [Card]), {})
    project, document = _project_document(tmp_path, javascript, standalone=True, declared=True)
    diagnostics = browser_diagnostics(document, project)
    assert len(findings) == len(diagnostics) == 1
    assert findings[0].code == diagnostics[0].code
    assert findings[0].message == diagnostics[0].message
    assert findings[0].column == diagnostics[0].range.start.character
