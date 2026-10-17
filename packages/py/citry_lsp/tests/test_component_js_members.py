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
    tmp_path: Path,
    javascript: str,
    *,
    standalone: bool = False,
    declared: bool = False,
    open_data: bool = False,
    member_rule: str | None = None,
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
    if member_rule is not None:
        app_source += f"    class Lint:\n        rule_unknown_component_js_member = {member_rule!r}\n"
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
        f"$component({{ onServerRender({{ component: payload }}) {{{body}}} }});"
        if configuration
        else f"$component(({{ component: payload }}) => {{{body}}});"
    )
    project, document = _project_document(tmp_path, javascript, standalone=standalone)
    source = document.source
    use = _position(source, "payload.b", 3)
    target = types.Location(
        document.uri,
        types.Range(_position(source, "component: payload", 11), _position(source, "component: payload", 18)),
    )

    assert definition(document, use, project) == target
    assert declaration(document, use, project) == target
    found = references(document, use, project, include_declaration=True)
    assert found is not None
    assert len(found) == 3
    assert target in found
    assert definition(document, _position(source, "payload.other", 3), project) is None


def test_callback_navigation_does_not_guess_when_javascript_is_invalid(tmp_path):
    project, document = _project_document(tmp_path, "$component(({ component }) => { component.; });")
    assert definition(document, _position(document.source, "component.;", 2), project) is None


@pytest.mark.parametrize("standalone", [False, True])
@pytest.mark.parametrize("declared", [False, True])
def test_unknown_member_has_exact_name_range_and_clears_after_edit(tmp_path, standalone, declared):
    javascript = '$component(({ component: payload }) => { console.log("😀", payload.c, payload.b); });'
    project, document = _project_document(tmp_path, javascript, standalone=standalone, declared=declared)
    diagnostics = browser_diagnostics(document, project, {document.uri: document})

    assert len(diagnostics) == 1
    finding = diagnostics[0]
    assert finding.code == "citry.component-js.unknown-member"
    assert finding.message == "Component instance member 'c' is not defined by this component."
    assert finding.severity == types.DiagnosticSeverity.Error
    assert finding.range == types.Range(
        _position(document.source, "payload.c", 8), _position(document.source, "payload.c", 9)
    )
    document.update(document.source.replace("payload.c", "payload.a"), 2, project)
    assert browser_diagnostics(document, project, {document.uri: document}) == ()


def test_open_inferred_data_does_not_create_a_closed_namespace(tmp_path):
    project, document = _project_document(
        tmp_path, "$component(({ component }) => { console.log(component.dynamic); });", open_data=True
    )
    assert browser_diagnostics(document, project, {document.uri: document}) == ()


def test_unsaved_js_data_declaration_supplies_a_new_field(tmp_path):
    project, document = _project_document(
        tmp_path, "$component(({ component }) => { console.log(component.c); });", declared=True
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
        $component(({ component }) => { console.log(component.extra); });
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
        # Text inside a string is not a member read.
        '$component(({ component }) => { console.log(component.b, "component.c"); });',
        # Vue's instance API, Citry's helpers, and the runtime-added prop.
        "$component(({ component }) => { component.$el; component._uid; component.citryId; });",
        "$component(({ component }) => { component.toString(); component.hasOwnProperty('b'); });",
        # A shadowing parameter is a different object.
        "$component(({ component }) => { function read(component) { return component.c; } });",
        # A reassigned or defaulted parameter may no longer hold the instance.
        "$component(({ component }) => { component = {}; console.log(component.c); });",
        "$component(({ component = {} }) => { console.log(component.c); });",
        "$component(({ component }) => { console.log(component[dynamicKey]); });",
        "$component(({ component }) => { component.; });",
        # Vue lets code add plain instance properties, so a written name is known.
        "$component(({ component }) => { component.timer = 1; console.log(component.timer); });",
        "$component({ created() { this.count += 1; }, methods: { m() { return this.count; } } });",
        "$component(({ component }) => { Object.assign(component, extra); console.log(component.c); });",
        # Options the analyzer cannot read make every name possible.
        "$component(options);",
        "$component({ ...shared, methods: { m() { return this.c; } } });",
        "$component({ setup() { return make(); }, methods: { m() { return this.c; } } });",
        "$component({ inject: names, methods: { m() { return this.c; } } });",
        # Destructuring and `for` targets may write the member they name.
        "$component({ methods: { m(o) { [this.x] = o; ({ a: this.y } = o); return this.x + this.y; } } });",
        "$component({ methods: { m(xs) { for (this.k of xs); return this.k; } } });",
        # Writes the text cannot name, and `this` inside a class body.
        "$component({ methods: { m(k) { this[k] = 1; return this.c; } } });",
        "$component({ methods: { m() { const self = this; Object.assign(self, x); return this.c; } } });",
        "$component(({ component }) => { ({ component } = next); console.log(component.c); });",
        "$component({ methods: { m() { class A { x = this.c; } return A; } } });",
        # Merged options can declare any name; an option Vue never calls has no proven `this`.
        "$component({ mixins: [shared], methods: { m() { return this.c; } } });",
        "$component({ extends: base, mounted() { return this.c; } });",
        "$component({ asyncData() { return this.c; } });",
    ],
)
def test_member_analysis_excludes_unproven_receivers_and_open_namespaces(javascript):
    assert lint_unknown_component_js_members(javascript, frozenset({"a", "b"})) == ()


def test_member_analysis_handles_aliases_and_closure_captures():
    source = """$component({ onServerRender({ component: payload }) {
        const read = () => `${payload.missing}`;
        console.log(payload?.other, payload["third"]);
    } });"""
    findings = lint_unknown_component_js_members(source, frozenset({"a", "b"}))
    assert [finding.name for finding in findings] == ["missing", "other"]
    encoded = source.encode("utf-8")
    assert [encoded[finding.start_index : finding.end_index].decode() for finding in findings] == [
        "missing",
        "other",
    ]
    assert lint_unknown_component_js_members(source, None) == ()


def test_member_analysis_accepts_every_declared_options_name():
    source = """$component({
      props: ["label"],
      inject: ["theme"],
      data() { return { open: false }; },
      setup() { return { query: "" }; },
      computed: {
        shown() { return this.open && this.label && this.theme && this.query && this.a && this.typoComputed; },
      },
      methods: {
        toggle() {
          const later = () => this.typoArrow;
          function detached() { return this.notChecked; }
          return this.shown + this.toggle + this.$state + later + detached;
        },
      },
      mounted() {
        const { open } = this;
        return open && this.typoHook;
      },
      watch: { open: { handler() { return this.typoWatch; } } },
    });"""
    findings = lint_unknown_component_js_members(source, frozenset({"a", "b"}))
    assert [finding.name for finding in findings] == ["typoComputed", "typoArrow", "typoHook", "typoWatch"]


def test_checker_and_lsp_share_unknown_member_diagnostics(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine

        class JsData:
            a: str
            b: int

    javascript = "$component(({ component }) => { console.log(component.c); });"
    findings = _check_browser_source(engine, _BrowserSource("card.js", javascript, [Card]), {})
    project, document = _project_document(tmp_path, javascript, standalone=True, declared=True)
    diagnostics = browser_diagnostics(document, project)
    assert len(findings) == len(diagnostics) == 1
    assert findings[0].code == diagnostics[0].code
    assert findings[0].message == diagnostics[0].message
    assert findings[0].column == diagnostics[0].range.start.character


def test_member_analysis_reports_at_the_requested_severity():
    source = "$component(({ component }) => { console.log(component.c); });"
    [warning] = lint_unknown_component_js_members(source, frozenset({"a"}), severity="warning")
    assert (warning.name, warning.severity) == ("c", "warning")
    assert lint_unknown_component_js_members(source, frozenset({"a"}), severity="ignore") == ()
    with pytest.raises(ValueError, match="member rule severity"):
        lint_unknown_component_js_members(source, frozenset({"a"}), severity="warn")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("rule", "expected"),
    [("warning", types.DiagnosticSeverity.Warning), ("ignore", None), ("error", types.DiagnosticSeverity.Error)],
)
def test_checker_and_lsp_apply_the_component_member_rule_severity(tmp_path, rule, expected):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine

        class JsData:
            a: str
            b: int

        class Lint:
            rule_unknown_component_js_member = rule

    javascript = "$component(({ component }) => { console.log(component.c); });"
    findings = _check_browser_source(engine, _BrowserSource("card.js", javascript, [Card]), {})
    project, document = _project_document(tmp_path, javascript, standalone=True, declared=True, member_rule=rule)
    diagnostics = [
        diagnostic
        for diagnostic in browser_diagnostics(document, project)
        if diagnostic.code == "citry.component-js.unknown-member"
    ]
    if expected is None:
        assert findings == []
        assert diagnostics == []
        return
    [finding] = findings
    [diagnostic] = diagnostics
    assert finding.severity == rule
    assert diagnostic.severity == expected


def test_shared_javascript_uses_the_strictest_owner_member_severity():
    engine = Citry(autodiscover=False)

    class Quiet(Component):
        citry = engine

        class JsData:
            a: str

        class Lint:
            rule_unknown_component_js_member = "ignore"

    class Loud(Component):
        citry = engine

        class JsData:
            a: str

        class Lint:
            rule_unknown_component_js_member = "warning"

    javascript = "$component(({ component }) => { console.log(component.c); });"
    both = _check_browser_source(engine, _BrowserSource("shared.js", javascript, [Quiet, Loud]), {})
    quiet_only = _check_browser_source(engine, _BrowserSource("shared.js", javascript, [Quiet]), {})
    assert [(finding.code, finding.severity) for finding in both] == [
        ("citry.component-js.unknown-member", "warning"),
    ]
    assert quiet_only == []
