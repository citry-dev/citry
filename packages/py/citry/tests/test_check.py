"""Focused behavior tests for the conservative ``citry check`` command."""

from __future__ import annotations

import json
import os
import sys
import textwrap
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from citry import Citry, Component, Extension, ForeignSpan, ForeignSpanSet, LintSettings
from citry.__main__ import main
from citry._app_selection import CheckAppSelection
from citry._checker import (
    TRANSFORM_NOTE,
    CheckFinding,
    CheckReport,
    _byte_offset_coordinates,
    _lsp_range_coordinates,
    check_project,
)
from citry._diagnostic_catalog import I18N_CATALOG_INVALID, I18N_MISSING_PARAM_TYPE, TEMPLATE_MARKER_NAME_INVALID
from citry._symbol_table import CHECK_NOTE, symtable
from citry.ext.i18n import DateFormat, FormatRegistry, NumberFormat
from citry.ext.i18n.extension import I18nExtension

if TYPE_CHECKING:
    from pathlib import Path


requires_symtable = pytest.mark.skipif(symtable is None, reason="PyPy has no _symtable; see #434")


@pytest.fixture(autouse=True)
def _isolate_import_state(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "path", list(sys.path))
    before = set(sys.modules)
    yield
    for module_name in set(sys.modules) - before:
        if module_name.startswith("check_project_"):
            sys.modules.pop(module_name, None)


def _run_main(args: list[str]) -> int:
    try:
        return main(args)
    except SystemExit as exc:
        return cast("int", exc.code)


def _write_app(tmp_path: Path, source: str, *, name: str = "check_project_app") -> str:
    (tmp_path / f"{name}.py").write_text(source, encoding="utf-8")
    return f"{name}:engine"


class TestModeSelection:
    def test_bare_check_requires_an_explicit_mode(self, monkeypatch, capsys):
        def forbidden(*args, **kwargs):
            raise AssertionError("a mode error must not start analysis")

        monkeypatch.setattr("citry.commands.check.check_project", forbidden)

        assert _run_main(["check"]) == 2
        error = capsys.readouterr().err
        assert "citry --app module:engine check" in error
        assert "citry check --static" in error

    @pytest.mark.parametrize("app_option", ["split", "equals"])
    def test_app_and_static_conflict_before_import_or_analysis(self, app_option, monkeypatch, capsys):
        def forbidden(*args, **kwargs):
            raise AssertionError("a mode conflict must not import or analyze")

        monkeypatch.setattr("citry.commands.check.load_app", forbidden)
        monkeypatch.setattr("citry.commands.check.check_project", forbidden)
        args = (
            ["--app", "invalid:engine", "check", "--static"]
            if app_option == "split"
            else ["--app=invalid:engine", "check", "--static"]
        )

        assert _run_main(args) == 2
        assert "--static cannot be combined with an app selection" in capsys.readouterr().err

    def test_types_needs_the_registry_mode(self, monkeypatch, capsys):
        def forbidden(*args, **kwargs):
            raise AssertionError("a mode error must not start analysis")

        monkeypatch.setattr("citry.commands.check.check_project", forbidden)

        assert _run_main(["check", "--static", "--types"]) == 2
        assert "--types needs the app's registry" in capsys.readouterr().err

    @pytest.mark.parametrize(
        "args",
        [
            ["check", "--help"],
            ["check", "--static", "--help"],
            ["--app", "invalid:engine", "check", "--help"],
        ],
    )
    def test_help_never_imports_or_analyzes(self, args, monkeypatch, capsys):
        def forbidden(*call_args, **kwargs):
            raise AssertionError("help must not import or analyze")

        monkeypatch.setattr("citry.commands.check.load_app", forbidden)
        monkeypatch.setattr("citry.commands.check.check_project", forbidden)

        assert _run_main(args) == 0
        output = capsys.readouterr().out
        assert "--static" in output
        assert "limited inline template candidates" in output


class TestReducedAnalysisNote:
    """On an interpreter without the `symtable` module a loaded app's report says it checks less."""

    @staticmethod
    def _write_clean_app(tmp_path: Path) -> str:
        # A loaded app is what runs the analyses that read the symbol table.
        return _write_app(
            tmp_path,
            "from citry import Citry, Component\n"
            "engine = Citry(autodiscover=False)\n"
            "class Fine(Component):\n"
            "    citry = engine\n"
            "    template = '<div></div>'\n",
        )

    @staticmethod
    def _hide_symtable(monkeypatch: pytest.MonkeyPatch) -> None:
        # Each module imported the name, so each holds its own binding.
        for module in ("citry._symbol_table", "citry._checker", "citry._template_python"):
            monkeypatch.setattr(f"{module}.symtable", None)

    def test_text_output_carries_the_note_when_symtable_is_missing(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = self._write_clean_app(tmp_path)
        self._hide_symtable(monkeypatch)

        assert _run_main(["--app", spec, "check"]) == 0
        assert f"citry check: note: {CHECK_NOTE}\n" in capsys.readouterr().err

    def test_json_notes_carry_the_note_when_symtable_is_missing(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = self._write_clean_app(tmp_path)
        self._hide_symtable(monkeypatch)

        assert _run_main(["--app", spec, "check", "--format", "json"]) == 0
        assert CHECK_NOTE in json.loads(capsys.readouterr().out)["notes"]

    def test_static_output_has_no_note_when_symtable_is_missing(self, tmp_path, monkeypatch, capsys):
        # Static mode loads no app, so neither symbol-table analysis runs.
        monkeypatch.chdir(tmp_path)
        self._write_clean_app(tmp_path)
        self._hide_symtable(monkeypatch)

        assert _run_main(["check", "--static", "--format", "json"]) == 0
        captured = capsys.readouterr()
        assert CHECK_NOTE not in json.loads(captured.out)["notes"]
        assert "_symtable" not in captured.err

    @requires_symtable
    def test_no_note_when_symtable_is_present(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = self._write_clean_app(tmp_path)

        assert _run_main(["--app", spec, "check", "--format", "json"]) == 0
        captured = capsys.readouterr()
        assert CHECK_NOTE not in json.loads(captured.out)["notes"]
        assert "_symtable" not in captured.err


class TestStaticMode:
    def test_static_mode_never_initializes_the_default_engine(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "component.py").write_text(
            "from citry import Component\nclass Broken(Component):\n    template = '<div>'\n",
            encoding="utf-8",
        )

        def fail() -> None:
            raise AssertionError("default engine must stay isolated")

        monkeypatch.setattr("citry.__main__.default_engine.initialize", fail)

        assert _run_main(["check", "--static"]) == 1
        assert "component.py" in capsys.readouterr().err

    @pytest.mark.parametrize(
        ("source", "expected_code"),
        [
            ("from citry import Component\nclass Card(Component):\n template = '<div>'\n", 1),
            ("from citry import Component as Base\nclass Card(Base):\n template: str = r'<div>'\n", 1),
            ("import citry as c\nclass Card(c.Component):\n template = u'<div>'\n", 1),
            ("from citry import LibraryComponent\nclass Card(LibraryComponent):\n template = '<' 'div>'\n", 1),
            (
                "from citry import Component\nclass Base(Component):\n pass\nclass Card(Base):\n template = '<div>'\n",
                1,
            ),
            ("class Card:\n template = '<div>'\n", 0),
            ("from other import Component\nclass Card(Component):\n template = '<div>'\n", 0),
            ("from citry import Component\nclass Card(Component):\n template = f'<{name}>'\n", 0),
            ("from citry import Component\nclass Card(Component):\n template = make_template()\n", 0),
            ("from citry import Component\nclass Card(Component):\n template = '<' + 'div>'\n", 0),
            (
                "from citry import Component\nclass Card(Component):\n if enabled:\n  template = '<div>'\n",
                0,
            ),
            (
                "from citry import Component\nclass Card(Component):\n template = '<div>'\n template = '<p></p>'\n",
                0,
            ),
            (
                "from citry import Component\nclass Card(Component):\n template = '<div>'\n template: str\n",
                1,
            ),
            (
                "from citry import Component\nclass Card(Component):\n template = '<div>'\n del template\n",
                0,
            ),
            (
                "from citry import Component\nclass Card(Component):\n template = '<div>'\n template += '</div>'\n",
                0,
            ),
            (
                "from citry import Component\nclass Card(Component):\n template = '<div>'\n"
                " def template(self):\n  pass\n",
                0,
            ),
            (
                "from citry import Component\nclass Card(Component):\n template = '<div>'\n"
                " x = (template := computed)\n",
                0,
            ),
            (
                "from citry import Component\n@decorate\nclass Card(Component):\n template = '<div>'\n",
                0,
            ),
            (
                "from citry import Component\nclass Card(Component):\n"
                " template_lang = choose_language()\n template = '<div>'\n",
                0,
            ),
            (
                "from citry import Component\nclass Mixin:\n template_lang = 'pug'\n"
                "class Card(Component, Mixin):\n template_lang = None\n template = '<div>'\n",
                1,
            ),
            (
                "from citry import Component\nclass Mixin:\n template_lang = 'pug'\n"
                "class Card(Component, Mixin):\n template = '<div>'\n",
                0,
            ),
            (
                "from citry import Component\nclass Parent(Component):\n template = '<p></p>'\n"
                "class Child(Parent):\n pass\n",
                0,
            ),
            (
                "from citry import Component\nclass Card(Component):\n template_file = 'card.html'\n",
                0,
            ),
            (
                "from citry import Component\nclass Card(Component):\n template = '<div>'\n template_lang = ''\n",
                1,
            ),
        ],
    )
    def test_only_provable_direct_component_literals_are_checked(
        self,
        source,
        expected_code,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "components.py").write_text(source, encoding="utf-8")

        assert _run_main(["check", "--static"]) == expected_code
        captured = capsys.readouterr()
        assert captured.out == ""
        assert ("components.py" in captured.err) is (expected_code == 1)

    def test_inherited_non_base_language_is_not_parsed_as_base_citry(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "components.py").write_text(
            "from citry import Component\n"
            "class Base(Component):\n template_lang = 'pug'\n"
            "class Card(Base):\n template = '<div>'\n",
            encoding="utf-8",
        )

        assert _run_main(["check", "--static"]) == 1
        error = capsys.readouterr().err
        assert "Citry cannot check template_lang with a str value" in error
        assert "Parse error" not in error

    def test_source_errors_are_findings_and_scan_continues(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "a_broken.py").write_text("def unfinished(\n", encoding="utf-8")
        (tmp_path / "b_component.py").write_text(
            "from citry import Component\nclass Broken(Component):\n template = '<span>'\n",
            encoding="utf-8",
        )

        assert _run_main(["check", "--static"]) == 1
        error = capsys.readouterr().err
        assert error.index("a_broken.py") < error.index("b_component.py")

    def test_uses_the_existing_autodiscovery_file_policy(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "_private.py").write_text(
            "from citry import Component\nclass Hidden(Component):\n template = '<div>'\n",
            encoding="utf-8",
        )
        visible = tmp_path / "visible.py"
        visible.write_text("class Unrelated:\n template = '<div>'\n", encoding="utf-8")

        assert main(["check", "--static"]) == 0
        assert capsys.readouterr().err == ""


class TestRegistryMode:
    def test_app_check_treats_foreign_spans_as_unknown_syntax(self, tmp_path):
        class HostSyntax(Extension):
            name = "host_syntax"

            def on_template_foreign_spans(self, ctx):
                source = ctx.content.encode()
                spans = []
                cursor = 0
                while (start := source.find(b"{%", cursor)) >= 0:
                    end = source.find(b"%}", start + 2)
                    if end < 0:
                        break
                    end += 2
                    spans.append(ForeignSpan(start, end, may_control_body=True))
                    cursor = end
                return ForeignSpanSet(tuple(spans))

            def on_template_foreign_compiled(self, ctx):
                ctx.mark_resolved(*ctx.claims)
                return ctx.nodes

        engine = Citry(extensions=[HostSyntax], autodiscover=False)

        class Host(Component):
            citry = engine
            template = "é{% for item in items %}<span>{{ item }}</span>{% endfor %}"

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 0
        assert report.findings == ()

    def test_valid_app_checks_inline_syntax_and_reports_the_transform_limit_once(self, tmp_path):
        engine = Citry(autodiscover=False)

        class Broken(Component):
            citry = engine
            template = "<div>"

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 1
        assert report.notes == (TRANSFORM_NOTE,)
        assert len(report.findings) == 1
        assert "Broken.template" in report.findings[0].origin

    def test_complete_tag_rules_validate_registered_aliases(self, tmp_path):
        engine = Citry(autodiscover=False)

        class Button(Component):
            citry = engine
            template = "<button></button>"

            class Kwargs:
                label: str

        engine.register(Button, "action")

        class Host(Component):
            citry = engine
            template = '<c-action unknown="x" />'

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 1
        assert "unknown" in report.findings[0].message.lower()

    def test_schema_less_registered_and_builtin_tags_are_known(self, tmp_path):
        engine = Citry(autodiscover=False)

        class FreeForm(Component):
            citry = engine
            template = "<p></p>"

        class Host(Component):
            citry = engine
            template = '<c-FreeForm anything="yes" /><c-provide />'

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 0

    def test_registered_name_matching_is_case_insensitive(self, tmp_path):
        engine = Citry(autodiscover=False)

        class KnownCard(Component):
            citry = engine
            template = "<p></p>"

        class Host(Component):
            citry = engine
            template = "<c-KNOWNCARD />"

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 0

    def test_unknown_checks_cover_ordinary_nested_bodies(self, tmp_path):
        engine = Citry(autodiscover=False)

        class Host(Component):
            citry = engine
            template = "<main><c-Ghost /></main>"

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 1
        assert report.findings[0].message == "Component <c-Ghost> is not registered."
        assert report.findings[0].code == "citry.template.unknown-component"

    def test_literal_tr_uses_complete_cross_component_i18n_index(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Messages(Component):
            citry = engine
            messages = "known-message = Known"

        class Host(Component):
            citry = engine
            template = '{{ tr("known-message") }} {{ tr("missing-message") }}'

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == ["citry.i18n.unknown-message"]
        assert "missing-message" in report.findings[0].message

    def test_literal_trans_message_uses_complete_i18n_index(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = "known-message = Known"
            template = '<c-trans message="missing-message" c-values="{}" />'

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == ["citry.i18n.unknown-message"]

    def test_literal_trans_checks_attribute_values_and_fills(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = """
                # @param {str} $name
                # @param {Slot} $link
                rich = Hello { $name }, { $link }
                    .aria-label = Hello { $name }
            """
            template = """
                <c-trans message="rich" attr="missing" c-values="{'name': 'Ada'}" />
                <c-trans message="rich" c-values="{'extra': 'Ada'}">
                    <c-fill name="wrong">Wrong</c-fill>
                </c-trans>
            """

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == [
            "citry.i18n.unknown-message",
            "citry.i18n.argument-invalid",
        ]
        assert "rich.missing" in report.findings[0].message
        assert "unknown values: extra" in report.findings[1].message
        assert "missing values: name" in report.findings[1].message
        assert "unknown fills: wrong" in report.findings[1].message
        assert "missing fills: link" in report.findings[1].message

    def test_literal_trans_values_on_an_indented_line_are_checked(self, tmp_path):
        # A multi-line `c-values` starts on an indented line, which Citry
        # accepts. The check must read it, not skip the `<c-trans>`.
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = """
                # @param {str} $name
                greeting = Hello { $name }
            """
            template = """
                <c-trans
                  message="greeting"
                  c-values="
                    {'extra': 'Ada'}
                  "
                />
            """

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == ["citry.i18n.argument-invalid"]
        assert "unknown values: extra" in report.findings[0].message
        assert "missing values: name" in report.findings[0].message

    def test_missing_i18n_param_type_is_a_configurable_warning(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Broken(Component):
            citry = engine
            messages = "broken = Hello, { $name }."

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        # The Rust compiler spells this code itself, so the generated constant
        # proves the reported code is the catalogued one.
        assert report.findings[0].code == I18N_MISSING_PARAM_TYPE
        assert report.findings[0].severity == "warning"
        assert "without an @param" in report.findings[0].message
        assert report.exit_code == 0

    def test_invalid_inline_messages_report_a_located_catalog_finding(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        # A selector variable without an @param type is a compile error, so
        # check must report it instead of raising out of the run.
        class Picker(Component):
            citry = engine
            messages = """
                items = { $count ->
                    [one] One item
                   *[other] Many items
                }
            """

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert len(report.findings) == 1
        finding = report.findings[0]
        assert finding.code == I18N_CATALOG_INVALID
        assert "selector $count must have type int or Decimal" in finding.message
        assert finding.origin.endswith("::Picker.messages")
        # Lines and columns count from 0 in the dedented messages string.
        assert (finding.line, finding.column, finding.end_line, finding.end_column) == (1, 10, 1, 16)
        assert finding.source_kind == "inline"
        assert report.exit_code == 1

    def test_catalog_failure_without_a_source_position_names_the_catalog(self, tmp_path, monkeypatch):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = "known = Known"

        def fail_to_load(_extension: object) -> None:
            raise RuntimeError("catalog package unreadable")

        # A failure that is not a compile error has no position to report.
        monkeypatch.setattr(I18nExtension, "_load_project_sources", fail_to_load)

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [(finding.origin, finding.code, finding.line) for finding in report.findings] == [
            ("i18n catalog", I18N_CATALOG_INVALID, None),
        ]
        assert "RuntimeError: catalog package unreadable" in report.findings[0].message

    def test_literal_tr_checks_attributes_arguments_and_literal_types(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = """
                # @param {str} $name - User name.
                greeting = Hello, { $name }.
                    .aria-label = Greeting for { $name }
            """
            template = """
                {{ tr("greeting", attr="missing", name="Ada") }}
                {{ tr("greeting", extra="Ada") }}
                {{ tr("greeting", name=3) }}
            """

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == [
            "citry.i18n.unknown-message",
            "citry.i18n.argument-invalid",
            "citry.i18n.argument-invalid",
        ]
        assert "greeting.missing" in report.findings[0].message
        assert "unknown argument(s): extra" in report.findings[1].message
        assert "missing argument(s): name" in report.findings[1].message
        assert "must be str" in report.findings[2].message

    def test_template_variable_types_are_checked_against_message_parameters(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = "# @param {str} $name\ngreeting = Hello, { $name }."
            template = '{{ tr("greeting", name=count) }}'

            class TemplateData:
                count: int

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == ["citry.i18n.argument-invalid"]
        assert "must be str, not int" in report.findings[0].message

    def test_c_tr_checks_message_output_named_values_and_literal_types(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = """
                # @param {str} $name
                greeting = Hello, { $name }.
                    .aria-label = Greeting for { $name }
            """
            template = """
                <span $c-tr:missing></span>
                <span $c-tr:greeting.missing></span>
                <span $c-tr:greeting.aria-label[aria-label]="{ name: 1, extra: true }"></span>
            """

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == [
            "citry.i18n.unknown-message",
            "citry.i18n.unknown-message",
            "citry.i18n.argument-invalid",
        ]
        assert "unknown argument(s): extra" in report.findings[2].message
        assert "must be str, not number" in report.findings[2].message

    @pytest.mark.parametrize("attribute", ["$c-tr:", "$c-tr[]", "$c-tr:known[]", "$c-tr:known."])
    def test_c_tr_malformed_owned_names_are_check_errors(self, tmp_path, attribute):
        engine = Citry(autodiscover=False)

        class Host(Component):
            citry = engine
            template = f"<span {attribute}></span>"

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == ["citry.i18n.argument-invalid"]

    def test_dynamic_trans_values_spread_defers_argument_checks_to_runtime(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = "# @param {str} $name\ngreeting = Hello, { $name }."
            template = '<c-trans message="greeting" c-values="{**values}" />'

            class TemplateData:
                values: dict[str, object]

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.findings == ()

    def test_python_self_i18n_tr_literal_ids_are_checked(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = "known = Known"

            def translated_label(self) -> str:
                return self.i18n.tr("missing")

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == ["citry.i18n.unknown-message"]
        assert "missing" in report.findings[0].message

    def test_template_fmt_literal_profile_is_checked(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "formats": FormatRegistry(number={"measurement": NumberFormat()}),
                }
            },
        )

        class Host(Component):
            citry = engine
            template = "{{ fmt.number(total, format='measurement') }} {{ fmt.number(total, format='missing') }}"
            messages = "unused = Present"

            class TemplateData:
                total: int

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        profile_findings = [finding for finding in report.findings if finding.code == "citry.i18n.argument-invalid"]
        assert len(profile_findings) == 1
        assert "Unknown i18n format profile 'missing' for number" in profile_findings[0].message

    def test_python_formatter_and_parser_literal_profiles_are_checked(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "formats": FormatRegistry(
                        number={"measurement": NumberFormat()},
                        date={"display": DateFormat()},
                    ),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = "unused = Present"

            def labels(self) -> tuple[str, object]:
                return (
                    self.i18n.format.number(3, format="missing"),
                    self.i18n.parse.date("1/2/2026", format="display"),
                )

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == [
            "citry.i18n.argument-invalid",
            "citry.i18n.argument-invalid",
        ]
        assert "Unknown i18n format profile 'missing' for number" in report.findings[0].message
        assert "Unknown i18n parse profile 'display' for date" in report.findings[1].message

    def test_browser_i18n_literal_profiles_are_checked(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "formats": FormatRegistry(number={"measurement": NumberFormat()}),
                }
            },
        )

        class Host(Component):
            citry = engine
            template = """
            <c-i18n c-client="True" tag="main">
              <span v-text="$i18n.format.number(total, {format: 'missing'})"></span>
            </c-i18n>
            """
            messages = "unused = Present"

            class TemplateData:
                total: int

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        profile_findings = [finding for finding in report.findings if finding.code == "citry.i18n.argument-invalid"]
        assert len(profile_findings) == 1
        assert "Unknown i18n format profile 'missing' for number" in profile_findings[0].message

    def test_guarded_formatter_profiles_are_unchecked_without_i18n_settings(self, tmp_path):
        # Component messages make i18n available, but only configured i18n
        # has profiles and gives the browser `$i18n`, so guarded calls pass
        # while an unguarded call, which fails when it runs, is reported.
        engine = Citry(autodiscover=False)

        class Host(Component):
            citry = engine

            class I18n:
                messages_locale = "en-US"

            def label(self) -> str:
                return self.i18n.format.number(3, format="missing") if self.i18n.configured else "3"

            def guarded_block(self) -> str:
                if not self.i18n.configured:
                    return "4"
                return self.i18n.format.number(4, format="missing")

            def unguarded(self) -> str:
                return self.i18n.format.number(5, format="unguarded")

            js = """
            const i18n = component.$i18n;
            const label = i18n ? i18n.format.number(3, { format: 'missing' }) : '3';
            """
            messages = """
            unused = Present
            """

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.message for finding in report.findings if finding.code.startswith("citry.i18n.")] == [
            "Unknown i18n format profile 'unguarded' for number; configured profiles: none.",
        ]

    @pytest.mark.parametrize("attr", ["which", "None"])
    def test_literal_missing_id_is_checked_when_attr_is_not_a_string(self, tmp_path, attr):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = "known = Known"
            template = f'{{{{ tr("missing", attr={attr}) }}}}'

            class TemplateData:
                which: str

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == ["citry.i18n.unknown-message"]

    def test_python_i18n_scan_stops_at_nested_helper_classes(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = "known = Known"

            class Helper:
                def translated_label(self) -> str:
                    return self.i18n.tr("missing")

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.findings == ()

    def test_client_message_ids_are_checked_and_plain_fallback_is_a_warning(self, tmp_path):
        # A missing translation still renders through the fallback chain, so
        # plain tr() text that falls back is a warning that keeps the exit
        # code at 0; an unknown client message ID stays an error.
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US", "cs-CZ"),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = """
            known-message = Known
            """
            template = """
            {{ tr("known-message") }}
            """

            class I18n:
                client_messages = ("missing-client-message",)

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [(finding.code, finding.severity) for finding in report.findings] == [
            ("citry.i18n.client-message-invalid", "error"),
            ("citry.i18n.cross-language-fallback", "warning"),
        ]
        assert "no translation for: cs-CZ" in report.findings[1].message

    def test_partial_translations_pass_check_by_default(self, tmp_path):
        engine = Citry(
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US", "cs-CZ"),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = """
            greeting = Hello
            """
            template = """
            {{ tr("greeting") }}
            """

            def label(self) -> str:
                return self.i18n.tr("greeting")

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [(finding.code, finding.severity) for finding in report.findings] == [
            ("citry.i18n.cross-language-fallback", "warning"),
            ("citry.i18n.cross-language-fallback", "warning"),
        ]
        assert report.exit_code == 0

    @pytest.mark.parametrize(
        ("app_rule", "component_rule", "expected"),
        [
            ("error", None, ["error", "error", "error"]),
            ("ignore", None, []),
            ("ignore", "error", ["error", "error", "error"]),
            ("error", "ignore", []),
        ],
    )
    def test_cross_language_fallback_severity_follows_lint_settings(
        self,
        tmp_path,
        app_rule,
        component_rule,
        expected,
    ):
        engine = Citry(
            autodiscover=False,
            lint=LintSettings(rule_i18n_cross_language_fallback=app_rule),
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US", "cs-CZ"),
                }
            },
        )
        lint = {} if component_rule is None else {"rule_i18n_cross_language_fallback": component_rule}

        class Host(Component):
            citry = engine
            messages = """
            greeting = Hello
            """
            template = """
            {{ tr("greeting") }}
            """
            Lint = type("Lint", (), lint)

            class I18n:
                client_messages = ("greeting",)

            def label(self) -> str:
                return self.i18n.tr("greeting")

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        # One finding each for the client message, the Python call, and the
        # template call.
        assert [finding.code for finding in report.findings] == ["citry.i18n.cross-language-fallback"] * len(expected)
        assert [finding.severity for finding in report.findings] == expected
        assert report.exit_code == (1 if expected else 0)

    def test_shared_template_reports_fallback_at_the_strictest_consumer_severity(self, tmp_path):
        shared = tmp_path / "shared.html"
        shared.write_text('{{ tr("greeting") }}', encoding="utf-8")
        engine = Citry(
            dirs=[tmp_path],
            autodiscover=False,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US", "cs-CZ"),
                }
            },
        )

        class Lenient(Component):
            citry = engine
            template_file = "shared.html"
            messages = """
            greeting = Hello
            """

            class Lint:
                rule_i18n_cross_language_fallback = "ignore"

        class Strict(Component):
            citry = engine
            template_file = "shared.html"

            class Lint:
                rule_i18n_cross_language_fallback = "error"

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [(finding.code, finding.severity) for finding in report.findings] == [
            ("citry.i18n.cross-language-fallback", "error"),
        ]

        # Once every component that shares the template ignores the rule,
        # nothing is reported.
        Strict.Lint.rule_i18n_cross_language_fallback = "ignore"
        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.findings == ()

    def test_rich_message_fallback_stays_an_error_when_plain_fallback_is_ignored(self, tmp_path):
        # Rendering <c-trans> in a locale without its translation raises, so
        # the fallback setting cannot turn this finding off.
        engine = Citry(
            autodiscover=False,
            lint=LintSettings(rule_i18n_cross_language_fallback="ignore"),
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US", "cs-CZ"),
                }
            },
        )

        class Host(Component):
            citry = engine
            messages = """
            # @param {Slot} $link
            terms = Read { $link }.
                .title = Terms
            """
            template = """
            <c-trans message="terms" c-values="{}">
              <c-fill name="link"><a href="/terms">terms</a></c-fill>
            </c-trans>
            <c-trans message="terms" attr="title" c-values="{}" />
            """

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [(finding.code, finding.severity) for finding in report.findings] == [
            ("citry.i18n.rich-message-fallback", "error"),
            ("citry.i18n.rich-message-fallback", "error"),
        ]
        assert "'terms.title'" in report.findings[1].message
        assert "no translation for: cs-CZ" in report.findings[0].message
        assert report.exit_code == 1

    def test_expression_strings_that_look_like_templates_do_not_create_unknowns(self, tmp_path):
        engine = Citry(autodiscover=False)

        class Outer(Component):
            citry = engine
            template = "<div></div>"

        class Host(Component):
            citry = engine
            template = """<c-Outer c-title="'<c-Ghost />'" />"""

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 0

    def test_inherited_file_assets_and_aliases_are_checked_once(self, tmp_path):
        (tmp_path / "shared.pug").write_text("<section>", encoding="utf-8")
        engine = Citry(dirs=[tmp_path], autodiscover=False)

        class Parent(Component):
            citry = engine
            template_file = "shared.pug"

        class Child(Parent):
            pass

        engine.register(Child, "child-alias")

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 1
        assert len(report.findings) == 1
        assert report.findings[0].origin == str(tmp_path / "shared.pug")

    def test_unrelated_components_sharing_one_file_are_checked_once(self, tmp_path):
        shared = tmp_path / "shared.html"
        shared.write_text("<section>", encoding="utf-8")
        engine = Citry(dirs=[tmp_path], autodiscover=False)

        class First(Component):
            citry = engine
            template_file = "shared.html"

        class Second(Component):
            citry = engine
            template_file = shared

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 1
        assert len(report.findings) == 1
        assert report.findings[0].origin == str(shared)

    @pytest.mark.parametrize(
        ("base_name", "child_name"),
        [("ABase", "ZChild"), ("ZBase", "AChild")],
    )
    def test_inherited_source_and_language_override_are_order_independent(
        self,
        base_name,
        child_name,
        tmp_path,
    ):
        engine = Citry(autodiscover=False)
        base = type(base_name, (Component,), {"citry": engine, "template": "<div>"})
        type(child_name, (base,), {"template_lang": "pug"})

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 1
        assert len(report.findings) == 2
        assert any("template_lang" in finding.message for finding in report.findings)
        assert any("Parse error" in finding.message for finding in report.findings)

    def test_explicit_none_and_unsupported_language_are_handled_without_loading(self, tmp_path):
        engine = Citry(autodiscover=False)

        class NoTemplate(Component):
            citry = engine
            template = None

        class Alternate(Component):
            citry = engine
            template = "<div>"
            template_lang = ""

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 1
        assert len(report.findings) == 1
        assert "template_lang" in report.findings[0].message

    def test_bad_utf8_asset_does_not_stop_later_templates(self, tmp_path):
        (tmp_path / "a.html").write_bytes(b"\xff")
        (tmp_path / "b.html").write_text("<article>", encoding="utf-8")
        engine = Citry(dirs=[tmp_path], autodiscover=False)

        class First(Component):
            citry = engine
            template_file = "a.html"

        class Second(Component):
            citry = engine
            template_file = "b.html"

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 1
        assert len(report.findings) == 2
        assert "could not read this template file" in report.findings[0].message
        assert report.findings[1].origin.endswith("b.html")

    def test_never_calls_template_load_or_transform_hooks(self, tmp_path, monkeypatch):
        engine = Citry(autodiscover=False)

        class Safe(Component):
            citry = engine
            template = "<p></p>"

        def forbidden(*args, **kwargs):
            raise AssertionError("runtime template loading is forbidden")

        monkeypatch.setattr(Safe, "get_template", forbidden)
        monkeypatch.setattr(engine.extensions, "on_template_loaded", forbidden)

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 0


class TestAppFallback:
    @pytest.mark.parametrize("app_option", ["split", "equals"])
    def test_valid_app_forms_run_registry_mode_cleanly(self, app_option, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = _write_app(
            tmp_path,
            "from citry import Citry, Component\nengine = Citry(autodiscover=False)\n"
            "class Safe(Component):\n citry = engine\n template = '<p></p>'\n",
        )
        args = ["--app", spec, "check"] if app_option == "split" else [f"--app={spec}", "check"]

        assert main(args) == 0
        assert capsys.readouterr().err.count("extension-transformed") == 1

    def test_unknown_template_roots_use_app_policy_and_runtime_globals(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = _write_app(
            tmp_path,
            "from citry import Citry, Component\n"
            "engine = Citry(autodiscover=False, template_globals={'site_name': 'Citry'})\n"
            "class Card(Component):\n"
            " citry = engine\n"
            " class TemplateData:\n"
            "  title: str\n"
            " template = '''\n<p>{{ title }} {{ site_name }} {{ typo }}</p>\n'''\n",
        )

        assert _run_main(["--app", spec, "check", "--format", "json"]) == 1
        payload = json.loads(capsys.readouterr().out)
        assert [item["code"] for item in payload["findings"]] == ["citry.template.unknown-variable"]
        assert payload["findings"][0]["severity"] == "error"
        assert "typo" in payload["findings"][0]["message"]

    def test_warning_policy_reports_without_failing_check(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = _write_app(
            tmp_path,
            "from citry import Citry, Component, LintSettings\n"
            "engine = Citry(autodiscover=False, lint=LintSettings("
            "rule_unknown_template_variable='warning'))\n"
            "class Card(Component):\n"
            " citry = engine\n"
            " class TemplateData:\n"
            "  title: str\n"
            " template = '''\n<p>{{ typo }}</p>\n'''\n",
        )

        assert main(["--app", spec, "check", "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["exit_code"] == 0
        assert payload["findings"][0]["severity"] == "warning"

    def test_extra_allowing_schema_caps_default_error_at_warning(self, tmp_path, monkeypatch, capsys):
        pytest.importorskip("pydantic")
        monkeypatch.chdir(tmp_path)
        spec = _write_app(
            tmp_path,
            "from pydantic import BaseModel, ConfigDict\n"
            "from citry import Citry, Component\n"
            "engine = Citry(autodiscover=False)\n"
            "class Card(Component):\n"
            " citry = engine\n"
            " class TemplateData(BaseModel):\n"
            "  model_config = ConfigDict(extra='allow')\n"
            "  title: str\n"
            " template = '''\n<p>{{ undeclared }}</p>\n'''\n",
        )

        assert main(["--app", spec, "check", "--format", "json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["exit_code"] == 0
        assert payload["findings"][0]["severity"] == "warning"
        assert payload["findings"][0]["message"] == (
            "Template variable 'undeclared' is not declared. It may be supplied dynamically."
        )

    def test_absent_schema_stays_strict_by_default(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = _write_app(
            tmp_path,
            "from citry import Citry, Component\n"
            "engine = Citry(autodiscover=False)\n"
            "class Card(Component):\n"
            " citry = engine\n"
            " template = '{{ undeclared }}'\n",
        )

        assert _run_main(["--app", spec, "check", "--format", "json"]) == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["findings"][0]["severity"] == "error"
        assert payload["findings"][0]["message"] == (
            "Template variable 'undeclared' is not declared. "
            "Citry could not determine whether it is supplied dynamically."
        )

    def test_shared_template_uses_the_strictest_consumer_policy(self, tmp_path, monkeypatch, capsys):
        pytest.importorskip("pydantic")
        monkeypatch.chdir(tmp_path)
        (tmp_path / "shared.html").write_text("{{ undeclared }}", encoding="utf-8")
        spec = _write_app(
            tmp_path,
            "from pathlib import Path\n"
            "from pydantic import BaseModel, ConfigDict\n"
            "from citry import Citry, Component\n"
            "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
            "class Open(Component):\n"
            " citry = engine\n"
            " template_file = 'shared.html'\n"
            " class TemplateData(BaseModel):\n"
            "  model_config = ConfigDict(extra='allow')\n"
            "  title: str\n"
            "class Closed(Component):\n"
            " citry = engine\n"
            " template_file = 'shared.html'\n"
            " class TemplateData:\n"
            "  title: str\n",
        )

        assert _run_main(["--app", spec, "check", "--format", "json"]) == 1
        payload = json.loads(capsys.readouterr().out)
        root_findings = [item for item in payload["findings"] if item["code"] == "citry.template.unknown-variable"]
        assert [(item["severity"], item["message"]) for item in root_findings] == [
            ("error", "Template variable 'undeclared' is not available in this template.")
        ]

    @pytest.mark.parametrize(
        "spec",
        [
            "invalid",
            ":engine",
            "check_project_missing:engine",
        ],
    )
    def test_invalid_app_specs_fall_back_once_and_exit_two(self, spec, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "component.py").write_text(
            "from citry import Component\nclass Broken(Component):\n template = '<div>'\n",
            encoding="utf-8",
        )

        assert _run_main([f"--app={spec}", "check"]) == 2
        error = capsys.readouterr().err
        assert error.count("citry check: app unavailable:") == 1
        assert "component.py" in error
        assert "is not registered" not in error

    @pytest.mark.parametrize(
        "body",
        [
            "engine = object()\n",
            (
                "from citry import ComponentLibrary, LibraryComponent\n"
                "class CCard(LibraryComponent):\n"
                " template = '''\n<article></article>\n'''\n"
                "engine = ComponentLibrary('test-ui', (CCard,))\n"
            ),
            "raise RuntimeError('boom')\n",
            "raise SystemExit(7)\n",
        ],
    )
    def test_wrong_object_and_project_import_failures_fall_back(self, body, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = _write_app(tmp_path, body)

        assert _run_main(["--app", spec, "check"]) == 2
        assert capsys.readouterr().err.count("citry check: app unavailable:") == 1

    def test_discovery_failure_discards_partial_registry_facts(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        spec = _write_app(
            tmp_path,
            "from pathlib import Path\nfrom citry import Citry\nengine = Citry(dirs=[Path.cwd()])\n",
        )
        (tmp_path / "a_component.py").write_text(
            "from check_project_app import engine\nfrom citry import Component\n"
            "class Known(Component):\n citry = engine\n template = '<p></p>'\n",
            encoding="utf-8",
        )
        (tmp_path / "b_failure.py").write_text("raise RuntimeError('discovery boom')\n", encoding="utf-8")
        (tmp_path / "c_host.py").write_text(
            "from citry import Component\nclass Host(Component):\n template = '<c-Missing />'\n",
            encoding="utf-8",
        )

        assert _run_main(["--app", spec, "check"]) == 2
        error = capsys.readouterr().err
        assert error.count("citry check: app unavailable:") == 1
        assert "discovery boom" in error
        assert "is not registered" not in error

    @pytest.mark.parametrize(
        ("statement", "error_type"),
        [("raise KeyboardInterrupt", KeyboardInterrupt), ("raise GeneratorExit", GeneratorExit)],
    )
    def test_process_control_exceptions_are_not_degraded(self, statement, error_type, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        spec = _write_app(tmp_path, f"{statement}\n")

        with pytest.raises(error_type):
            main(["--app", spec, "check"])

    def test_tag_rule_failure_discards_registry_facts(self, tmp_path, monkeypatch):
        engine = Citry(autodiscover=False)

        class Known(Component):
            citry = engine
            template = "<p></p>"

        (tmp_path / "host.py").write_text(
            "from citry import Component\nclass Host(Component):\n template = '<c-Missing />'\n",
            encoding="utf-8",
        )

        def fail(_engine):
            raise RuntimeError("tag rule boom")

        monkeypatch.setattr("citry._checker.build_tag_rules", fail)

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert report.exit_code == 2
        assert report.app_failure == "RuntimeError: tag rule boom"
        assert all("is not registered" not in finding.message for finding in report.findings)

    def test_other_commands_keep_project_import_failures_fail_fast(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        spec = _write_app(tmp_path, "raise RuntimeError('inspect boom')\n")

        with pytest.raises(RuntimeError, match="inspect boom"):
            main(["--app", spec, "inspect", "--json"])


def test_check_has_no_positional_path_or_legacy_json_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert _run_main(["check", "--static", "."]) == 2
    assert _run_main(["check", "--static", "--json"]) == 2


def test_json_format_has_versioned_structured_parser_diagnostic(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "component.py").write_text(
        "from citry import Component\nclass Broken(Component):\n template = '<div>'\n",
        encoding="utf-8",
    )

    assert _run_main(["check", "--static", "--format", "json"]) == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert captured.err == ""
    assert payload["schema_version"] == 1
    assert payload["mode"] == "static"
    assert payload["exit_code"] == 1
    assert payload["findings"][0]["code"] == "citry.parse.syntax"
    assert payload["findings"][0]["range"]["start_index"] is not None
    # Static mode reads the template string from the class, so its range
    # counts inside that string.
    assert payload["findings"][0]["range"]["source_kind"] == "inline"


_RANGES_APP = """\
from citry import Citry, Component

engine = Citry(
    autodiscover=False,
    extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
)


class Greeting(Component):
    citry = engine
    messages = \"\"\"
        known = Known
    \"\"\"
    template = \"\"\"
      <p>é {{ missing }} <c-nope /> <span v-text="nope"></span></p>
    \"\"\"
    js = \"\"\"
      sendEvent("missing");
    \"\"\"

    class JsData:
        note: str = "é"; tags: set[str]

    class Events:
        def save(self):
            pass

    def subtitle(self):
        return self.i18n.tr("missing-id")


class Broken(Component):
    citry = engine
    template = \"\"\"
      <p>x</p>
      <c-if cond="x">
    \"\"\"


class Styled(Component):
    citry = engine
    template = \"\"\"
      <p>Styled</p>
    \"\"\"
    css = \"\"\"
      .note { color: var(--acent); }
    \"\"\"

    class CssData:
        accent: str


class FromFile(Component):
    citry = engine
    template_file = "from_file.html"
    js_file = "from_file.js"
    css_file = "from_file.css"

    class CssData:
        accent: str
"""


def test_json_ranges_of_every_rule_family_count_from_zero(tmp_path, monkeypatch, capsys):
    # Every rule family numbers its range the same way (#203). Each template,
    # JavaScript, and CSS mistake below sits on line 1 or 2 of its source,
    # counted from 0, and the `é` before some of them makes a byte offset
    # differ from a column.
    monkeypatch.chdir(tmp_path)
    spec = _write_app(tmp_path, _RANGES_APP, name="check_project_ranges")
    (tmp_path / "from_file.html").write_text("<p>\n  é {{ gone }}\n</p>\n", encoding="utf-8")
    (tmp_path / "from_file.js").write_text('\nsendEvent("missing");\n', encoding="utf-8")
    (tmp_path / "from_file.css").write_text("\n.note { color: var(--acent); }\n", encoding="utf-8")
    app_file = str(tmp_path / "check_project_ranges.py")

    assert _run_main(["--app", spec, "check", "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)

    ranges = {
        (finding["code"], finding["origin"].removeprefix(f"{tmp_path}{os.sep}")): (
            finding["range"]["source_kind"],
            finding["range"]["start"]["line"],
            finding["range"]["start"]["column"],
            finding["range"]["end"]["line"],
            finding["range"]["end"]["column"],
        )
        for finding in payload["findings"]
    }
    assert ranges == {
        # Inline template: the parser, Citry's own rules, and the Vue rules.
        ("citry.parse.syntax", "check_project_ranges.Broken.template"): ("inline", 2, 0, 2, 15),
        ("citry.template.unknown-variable", "check_project_ranges.Greeting.template"): ("inline", 1, 8, 1, 15),
        ("citry.template.unknown-component", "check_project_ranges.Greeting.template"): ("inline", 1, 20, 1, 26),
        ("citry.vue.unknown-variable", "check_project_ranges.Greeting.template"): ("inline", 1, 44, 1, 48),
        # Inline JavaScript and CSS count in their own string.
        ("citry.browser.unknown-server-event", "check_project_ranges.Greeting.js"): ("inline", 1, 11, 1, 18),
        ("citry.css.misspelled-variable", "check_project_ranges.Styled.css"): ("inline", 1, 19, 1, 26),
        # Template, JavaScript, and CSS files count in the file.
        ("citry.template.unknown-variable", "from_file.html"): ("file", 1, 7, 1, 11),
        ("citry.browser.unknown-server-event", "from_file.js"): ("file", 1, 11, 1, 18),
        ("citry.css.misspelled-variable", "from_file.css"): ("file", 1, 19, 1, 26),
        # Python code counts in the component's file, which the origin names.
        (
            "citry.js-data.unsupported-type",
            "check_project_ranges.py (check_project_ranges.Greeting.JsData.tags)",
        ): ("file", 21, 25, 21, 29),
        ("citry.i18n.unknown-message", "check_project_ranges.py (check_project_ranges.Greeting)"): (
            "file",
            28,
            15,
            28,
            41,
        ),
    }
    # The byte offsets count in the same text as the lines and columns.
    by_code = {finding["code"]: finding["range"] for finding in payload["findings"]}
    source = (tmp_path / "check_project_ranges.py").read_text(encoding="utf-8")
    js_data = by_code["citry.js-data.unsupported-type"]
    assert source.encode()[js_data["start_index"] : js_data["end_index"]] == b"tags"
    assert app_file in {finding["origin"].split(" (", 1)[0] for finding in payload["findings"]}


def test_json_ranges_count_crlf_files_as_python_reads_them(tmp_path, monkeypatch, capsys):
    # A file with CR LF line endings counts lines the same way, and its byte
    # offsets count each line break as one "\n", as Python reads the file.
    monkeypatch.chdir(tmp_path)
    app = (
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class JsData:\n"
        "        tags: set[str]\n"
    )
    (tmp_path / "check_project_crlf.py").write_bytes(app.replace("\n", "\r\n").encode())
    (tmp_path / "card.html").write_bytes(b"<p>\r\n  {{ gone }}\r\n</p>\r\n")

    assert _run_main(["--app", "check_project_crlf:engine", "check", "--format", "json"]) == 1
    ranges = {finding["code"]: finding["range"] for finding in json.loads(capsys.readouterr().out)["findings"]}

    template = ranges["citry.template.unknown-variable"]
    assert (template["source_kind"], template["start"], template["end"]) == (
        "file",
        {"line": 1, "column": 5},
        {"line": 1, "column": 9},
    )
    text = (tmp_path / "card.html").read_text(encoding="utf-8").encode()
    assert text[template["start_index"] : template["end_index"]] == b"gone"
    js_data = ranges["citry.js-data.unsupported-type"]
    assert (js_data["start"], js_data["end"]) == ({"line": 6, "column": 8}, {"line": 6, "column": 12})
    text = (tmp_path / "check_project_crlf.py").read_text(encoding="utf-8").encode()
    assert text[js_data["start_index"] : js_data["end_index"]] == b"tags"


def test_messages_file_catalog_error_counts_in_the_file(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    spec = _write_app(
        tmp_path,
        "from citry import Citry, Component\n"
        "engine = Citry(\n"
        "    autodiscover=False,\n"
        "    extensions_defaults={'i18n': {'source_locale': 'en-US', 'locales': ('en-US',)}},\n"
        ")\n"
        "class Picker(Component):\n"
        "    citry = engine\n"
        "    messages_file = 'picker.ftl'\n",
    )
    # A selector variable without an @param type is a compile error.
    (tmp_path / "picker.ftl").write_text(
        "ok = Fine\nitems = { $count ->\n    [one] One item\n   *[other] Many items\n}\n",
        encoding="utf-8",
    )

    assert _run_main(["--app", spec, "check", "--format", "json"]) == 1
    [finding] = json.loads(capsys.readouterr().out)["findings"]

    assert finding["origin"] == str(tmp_path / "picker.ftl")
    assert (finding["range"]["source_kind"], finding["range"]["start"], finding["range"]["end"]) == (
        "file",
        {"line": 1, "column": 10},
        {"line": 1, "column": 16},
    )


def test_byte_offsets_map_to_lines_and_columns_as_editors_count_them():
    # Lines end at CR LF, CR, and LF only, as in Python and the Language
    # Server Protocol; a form feed or U+2028 stays inside its line. Columns
    # count UTF-16 code units, so an emoji takes two.
    source = "a\r\nb\rc\x0cd\u2028e\n😀f"

    def at(text: str) -> tuple[int, int]:
        return _byte_offset_coordinates(source, len(source[: source.index(text)].encode("utf-8")))

    assert at("b") == (1, 0)
    assert at("c") == (2, 0)
    assert at("d") == (2, 2)
    assert at("e") == (2, 4)
    assert at("f") == (3, 2)


def test_type_checker_ranges_count_bytes_as_python_reads_the_file():
    # ty and TypeScript read a file's raw text, CR LF included. Their range
    # keeps its lines and columns, and its byte offsets count each line
    # break as one "\n", as the checker's own rules do.
    def position(line: int, character: int) -> SimpleNamespace:
        return SimpleNamespace(line=line, character=character)

    value_range = SimpleNamespace(start=position(1, 2), end=position(1, 6))

    assert _lsp_range_coordinates("a\r\né tags\r\n", value_range) == (5, 9, 1, 2, 1, 6)


def test_a_report_rejects_a_range_without_the_text_it_counts_in():
    finding = CheckFinding("app.Card.template", "x", "citry.parse.syntax", "error", 0, 1, 0, 0, 0, 1)

    with pytest.raises(ValueError, match="has a range but no source_kind"):
        CheckReport((finding,))


def test_json_degraded_mode_reports_app_failure_once(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    assert _run_main(["--app", "missing:engine", "check", "--format", "json"]) == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert captured.err == ""
    assert payload["mode"] == "degraded"
    assert "could not import" in payload["app_failure"]


def test_environment_and_project_metadata_do_not_select_an_app(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CITRY_APP", "no.such.module:engine")
    (tmp_path / "pyproject.toml").write_text(
        "[tool.citry]\napp = 'no.such.module:engine'\n",
        encoding="utf-8",
    )

    assert main(["check", "--static"]) == 0
    assert capsys.readouterr().err == ""


def test_registry_check_reports_js_data_wire_and_literal_server_event_problems(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = (
            "<button @c-click=\"missing\" @click=\"sendEvent('missing'); $loading('missing'); $error()\"></button>"
            '<input :c-title="missing">'
        )
        js = 'sendEvent("missing"); loading("missing"); error(); sendEvent(dynamicName); onEvent("anything", () => {})'

        class JsData:
            title: str
            invalid: set[str]

        class State:
            title: str = ""

        class Events:
            def save(self):
                pass

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    assert [finding.code for finding in report.findings].count("citry.js-data.unsupported-type") == 1
    assert [finding.code for finding in report.findings].count("citry.browser.unknown-server-event") == 6
    assert {finding.severity for finding in report.findings if "unsupported-type" in finding.code} == {"warning"}


# Each method form Citry can call as component.method(kwargs, slots): the
# decorator line (if any) and the receiver parameter that precedes kwargs.
_METHOD_FORMS = pytest.mark.parametrize(
    ("decorator", "receiver"),
    [("", "self, "), ("    @staticmethod\n", ""), ("    @classmethod\n", "cls, ")],
    ids=["instance", "staticmethod", "classmethod"],
)


@_METHOD_FORMS
def test_registry_check_infers_template_data_for_every_method_form(tmp_path, monkeypatch, capsys, decorator, receiver):
    monkeypatch.chdir(tmp_path)
    spec = _write_app(
        tmp_path,
        "from typing import NamedTuple\n"
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Badge(Component):\n"
        "    citry = engine\n"
        "    class Kwargs(NamedTuple):\n"
        "        high: bool\n"
        f"{decorator}"
        f"    def template_data({receiver}kwargs, slots):\n"
        "        return {'label': 'Hot', 'high': kwargs.high}\n"
        "    template = '<span c-class=\"{\\'hot\\': high}\">{{ label }}</span>'\n",
    )

    assert _run_main(["--app", spec, "check", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["findings"] == []


@_METHOD_FORMS
def test_registry_check_joins_inferred_js_data_values_to_kwargs_types(
    tmp_path, monkeypatch, capsys, decorator, receiver
):
    monkeypatch.chdir(tmp_path)
    spec = _write_app(
        tmp_path,
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template = '<div></div>'\n"
        "    class Kwargs:\n"
        "        invalid: set[str]\n"
        "        submitting: bool = False\n"
        f"{decorator}"
        f"    def js_data({receiver}options: Kwargs, slots):\n"
        "        return {'submitting': options.submitting, 'invalid': options.invalid}\n",
    )

    assert _run_main(["--app", spec, "check", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    findings = [item for item in payload["findings"] if item["code"] == "citry.js-data.unsupported-type"]

    assert len(findings) == 1
    assert "'invalid'" in findings[0]["message"]


def test_registry_check_accepts_known_send_event_and_keeps_dynamic_and_on_event_open(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = (
            '<button @c-click="save" '
            "@click=\"sendEvent('save'); $loading('save'); $error(); "
            "sendEvent(name); onEvent('open', fn)\"></button>"
            '<input :c-title="save">'
        )
        js = 'sendEvent("save"); loading("save"); error(); $sendEvent(name); $onEvent("anything", fn)'

        class State:
            title: str = ""

        class Events:
            def save(self):
                pass

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    assert not [finding for finding in report.findings if finding.code == "citry.browser.unknown-server-event"]


def test_registry_check_reads_no_vue_variables_under_v_pre_but_reports_its_duplicate_id(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
        <div v-pre>
          <p v-if="a" id="same"></p>
          <p v-else id="same"></p>
        </div>
        """
        js = """
        $component({});
        """

    class Plain(Component):
        citry = engine
        template = """
        <div>
          <p v-if="a"></p>
        </div>
        """
        js = """
        $component({});
        """

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # Vue leaves `v-if` under `v-pre` as written, so only the component
    # without `v-pre` reads `a`. Both `<p>` elements are on the page, so the
    # repeated id is real.
    assert sorted((item.origin.rsplit(".", 2)[-2], item.code) for item in report.findings) == [
        ("Card", "citry.template.duplicate-id"),
        ("Plain", "citry.vue.unknown-variable"),
    ]
    messages = {item.code: item.message for item in report.findings}
    assert messages == {
        "citry.template.duplicate-id": (
            "Another element in this template already has id 'same'. An id must be unique in the page."
        ),
        "citry.vue.unknown-variable": "Vue variable 'a' is not available in this component.",
    }


def test_registry_check_reports_unknown_alpine_roots_and_respects_component_policy(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = (
            '<main :class="disabled1">'
            '<template x-for="color in colors"><span x-text="color + customGlobal"></span></template>'
            "</main>"
        )

        class JsData:
            disabled: bool
            colors: list[str]

        class Lint:
            rule_unknown_vue_variable = "warning"
            vue_variables = {"customGlobal": str}

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [item for item in report.findings if item.code == "citry.vue.unknown-variable"]

    assert [(item.message, item.severity) for item in findings] == [
        ("Vue variable 'disabled1' is not available in this component.", "warning")
    ]


def test_registry_check_reports_a_vue_read_of_a_python_loop_variable_once(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
          <ul>
            <li c-for="item in items" :title="item" v-text="label"></li>
            <li c-for="label in items" :title="label"></li>
          </ul>
        """

        class JsData:
            label: str

    class Relaxed(Component):
        citry = engine
        template = '<p c-for="entry in items" :title="entry"></p>'

        class Lint:
            rule_unknown_vue_variable = "ignore"

    class Quiet(Component):
        citry = engine
        template = '<p c-for="row in items" :title="row"></p>'

        class Lint:
            rule_unknown_vue_variable = "ignore"
            rule_vue_python_variable = "ignore"

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [
        (item.code, item.severity, item.message)
        for item in report.findings
        if item.code in {"citry.vue.python-variable", "citry.vue.unknown-variable"}
    ]

    # `label` is also a js_data key, so Vue silently shows that browser value
    # instead of the loop value, and the warning names both meanings.
    assert findings == [
        (
            "citry.vue.unknown-variable",
            "error",
            "Vue variable 'item' is not available in this component. 'item' is a Python variable here, "
            "which the browser never sees; pass its value with a c- attribute or loop with Vue's v-for.",
        ),
        (
            "citry.vue.python-variable",
            "warning",
            "Vue reads the component's browser value 'label' here, not the Python loop or slot variable "
            "'label'. Use c-title=\"label\" for the Python value, or rename one of them.",
        ),
        (
            "citry.vue.python-variable",
            "warning",
            "Vue reads 'entry' from browser state, but 'entry' is a Python variable here. "
            'Use c-title="entry" to pass the Python value.',
        ),
    ]


_TABLE_SLOT_TEMPLATE = """
  <ul>
    <li v-for="row in rows"><c-slot name="item" :row="row" /></li>
  </ul>
"""
_PAGE_SCOPED_FILL_TEMPLATE = """
  <c-Table>
    <c-fill name="item" v-slot="{ row, missing }"><b>cell</b></c-fill>
  </c-Table>
"""


def _unknown_slot_prop_findings(tmp_path: Path, engine: Citry) -> list[CheckFinding]:
    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    return [item for item in report.findings if item.code == "citry.vue.unknown-slot-prop"]


def test_registry_check_reports_a_v_slot_key_the_receiving_slot_does_not_pass(tmp_path):
    engine = Citry(autodiscover=False)

    class Table(Component):
        citry = engine
        template = _TABLE_SLOT_TEMPLATE

        class JsData:
            rows: list[str]

    class Page(Component):
        citry = engine
        template = _PAGE_SCOPED_FILL_TEMPLATE

    (finding,) = _unknown_slot_prop_findings(tmp_path, engine)

    assert finding.severity == "warning"
    assert finding.message == (
        "Slot 'item' on <c-Table> passes no Vue prop named 'missing', so it is undefined in this fill. "
        "The slot passes: row."
    )
    assert "Page" in finding.origin
    # The range is the key `missing` itself, in the Page template after its shared indentation is removed.
    assert (finding.line, finding.column, finding.end_line, finding.end_column) == (2, 37, 2, 44)
    assert finding.source_kind == "inline"
    assert finding.start_index is not None
    assert finding.end_index is not None
    text = textwrap.dedent(_PAGE_SCOPED_FILL_TEMPLATE).encode()
    assert text[finding.start_index : finding.end_index] == b"missing"


def test_registry_check_reports_a_key_the_slot_cannot_pass_because_it_passes_no_props(tmp_path):
    engine = Citry(autodiscover=False)

    class Table(Component):
        citry = engine
        template = '<ul><c-slot name="item" /></ul>'

    class Page(Component):
        citry = engine
        template = '<c-Table><c-fill name="item" v-slot="{ x }"><b>cell</b></c-fill></c-Table>'

    (finding,) = _unknown_slot_prop_findings(tmp_path, engine)

    assert finding.severity == "warning"
    assert finding.message == (
        "Slot 'item' on <c-Table> passes no Vue props, so 'x' is undefined in this fill. "
        "If the slot passes Python data, read it with data= instead. Otherwise add it to its "
        '<c-slot> as a Vue prop, such as :row="row".'
    )
    assert (finding.line, finding.column, finding.end_line, finding.end_column) == (0, 39, 0, 40)


def test_registry_check_skips_the_v_slot_check_when_the_receiving_template_has_a_dynamic_slot_name(tmp_path):
    engine = Citry(autodiscover=False)

    class Table(Component):
        citry = engine
        template = """
          <ul>
            <li v-for="row in rows"><c-slot name="item" :row="row" /></li>
            <c-slot c-name="other" />
          </ul>
        """

        class JsData:
            rows: list[str]

    class Page(Component):
        citry = engine
        template = _PAGE_SCOPED_FILL_TEMPLATE

    # A slot with a computed name may be the one `item` targets, so nothing
    # proves which props the fill receives.
    assert _unknown_slot_prop_findings(tmp_path, engine) == []


def test_registry_check_counts_a_slot_prop_passed_from_inside_a_forwarded_fill(tmp_path):
    engine = Citry(autodiscover=False)

    class Inner(Component):
        citry = engine
        template = '<div><c-slot name="x" /></div>'

    class Table(Component):
        citry = engine
        # The `<c-slot name="item">` sits in a fill of `Inner`, so it is nested
        # in a `<c-fill>` body, and it still decides what `item` passes.
        template = """
          <ul>
            <li v-for="row in rows">
              <c-Inner><c-fill name="x"><c-slot name="item" :row="row" /></c-fill></c-Inner>
            </li>
          </ul>
        """

        class JsData:
            rows: list[str]

    class Page(Component):
        citry = engine
        template = _PAGE_SCOPED_FILL_TEMPLATE

    (finding,) = _unknown_slot_prop_findings(tmp_path, engine)

    # `row` is found inside the forwarded fill, so only `missing` is unknown.
    # Had the walk skipped the fill body, the slot would look absent and
    # nothing would be reported.
    assert finding.message == (
        "Slot 'item' on <c-Table> passes no Vue prop named 'missing', so it is undefined in this fill. "
        "The slot passes: row."
    )


def test_registry_check_reads_the_template_a_receiving_subclass_inherits(tmp_path):
    engine = Citry(autodiscover=False)

    class Base(Component):
        citry = engine
        template = _TABLE_SLOT_TEMPLATE

        class JsData:
            rows: list[str]

    class Child(Base):
        pass

    class Page(Component):
        citry = engine
        template = _PAGE_SCOPED_FILL_TEMPLATE.replace("Table", "Child")

    (finding,) = _unknown_slot_prop_findings(tmp_path, engine)

    # `Child` declares no template of its own, so it is checked against the
    # `item` slot it inherits from `Base`.
    assert finding.message == (
        "Slot 'item' on <c-Child> passes no Vue prop named 'missing', so it is undefined in this fill. "
        "The slot passes: row."
    )


def test_registry_check_skips_the_v_slot_check_for_an_unregistered_tag(tmp_path):
    engine = Citry(autodiscover=False)

    class Table(Component):
        citry = engine
        template = _TABLE_SLOT_TEMPLATE

        class JsData:
            rows: list[str]

    class Page(Component):
        citry = engine
        template = _PAGE_SCOPED_FILL_TEMPLATE.replace("Table", "Missing")

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # The unknown tag is reported by its own rule; the slot check adds nothing on top.
    assert any(item.code == "citry.template.unknown-component" for item in report.findings)
    assert not any(item.code == "citry.vue.unknown-slot-prop" for item in report.findings)


def test_registry_check_skips_the_v_slot_check_when_every_key_is_passed_or_the_pattern_is_one_name(tmp_path):
    engine = Citry(autodiscover=False)

    class Table(Component):
        citry = engine
        template = """
          <ul>
            <li v-for="row in rows"><c-slot name="item" :row-data="row" /></li>
          </ul>
        """

        class JsData:
            rows: list[str]

    class Page(Component):
        citry = engine
        template = """
          <c-Table>
            <c-fill name="item" v-slot="{ rowData }"><b>cell</b></c-fill>
          </c-Table>
          <c-Table>
            <c-fill name="item" v-slot="props"><b>cell</b></c-fill>
          </c-Table>
        """

    # `:row-data` reaches the fill as `rowData`, and a single name reads no key by name.
    assert _unknown_slot_prop_findings(tmp_path, engine) == []


def test_registry_check_defaults_unknown_alpine_roots_to_error(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = '<button :disabled="disabled1"></button>'

        class JsData:
            disabled: bool

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [item for item in report.findings if item.code == "citry.vue.unknown-variable"]

    assert len(findings) == 1
    assert findings[0].severity == "error"


def test_registry_check_consumes_native_vue_options_namespace(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = '<button @click="save()" :title="label"></button>'
        js = "$component({ methods: { save() {} }, computed: { label() { return 'ready' } } })"

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    assert not [item for item in report.findings if item.code == "citry.vue.unknown-variable"]


def test_registry_check_declines_unknown_vue_namespace_after_options_spread(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = '<button @click="dynamicName()"></button>'
        js = "$component({ methods: { save() {} }, ...dynamicOptions })"

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    assert not [item for item in report.findings if item.code == "citry.vue.unknown-variable"]


def test_registry_check_reports_unknown_component_js_variables_and_missing_context_binding(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        js = """
        const outside = notCheckedHere;
        $component({
          onServerRender({ component }) {
            console.log(component.ready, configuredClient);
            scope.ready = component.ready;
          }
        });
        """

        class Lint:
            component_js_globals = {"configuredClient": object}

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [item for item in report.findings if item.code == "citry.component-js.unknown-variable"]

    assert [(item.message, item.severity) for item in findings] == [
        ("Component JavaScript variable 'scope' is not defined.", "error")
    ]


def test_registry_check_respects_component_js_rule_severity(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        js = """
        $component(() => {
          missingClient();
        });
        """

        class Lint:
            rule_unknown_component_js_variable = "warning"

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [item for item in report.findings if item.code == "citry.component-js.unknown-variable"]

    assert [(item.message, item.severity) for item in findings] == [
        ("Component JavaScript variable 'missingClient' is not defined.", "warning")
    ]


_VUE_COMPONENT_PROP_JS = """
$component({ props: {
  requiredTitle: { type: String, required: true },
  requiredCount: { type: Number, required: true },
  requiredRows: { type: Array, required: true },
  requiredDefault: { type: Boolean, required: true, default: false },
  optionalText: { type: String },
  optionalMixed: { type: [String, Number] },
  defaultedCount: { type: Number, default: 1 },
} });
"""
_VUE_COMPONENT_PROP_CODES = {
    "citry.browser.missing-component-prop",
    "citry.browser.incompatible-component-prop",
}


def _check_vue_component_prop_template(
    tmp_path: Path,
    template_source: str,
    *,
    dynamic_props: bool = False,
):
    engine = Citry(autodiscover=False)
    type(
        "Card",
        (Component,),
        {
            "citry": engine,
            "template": "<div></div>",
            "js": _VUE_COMPONENT_PROP_JS,
            "__module__": __name__,
        },
    )
    page_namespace: dict[str, object] = {
        "citry": engine,
        "template": template_source,
        "__module__": __name__,
    }
    if dynamic_props:

        class PageJsData:
            dynamic_props: dict[str, str]

        page_namespace["JsData"] = PageJsData
    type("Page", (Component,), page_namespace)
    return check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)


def _vue_component_prop_findings(report):
    return [finding for finding in report.findings if finding.code in _VUE_COMPONENT_PROP_CODES]


def _check_mark_template(tmp_path: Path, template_source: str):
    engine = Citry(autodiscover=False)
    type(
        "Page",
        (Component,),
        {"citry": engine, "template": template_source, "__module__": __name__},
    )
    return check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)


def test_registry_check_reports_native_vue_component_prop_presence_and_literal_types(tmp_path):
    valid = (
        '<c-card :required-title="\'ready\'" :requiredCount="2" v-bind:required-rows="[]" '
        ':requiredDefault="false" :optional-text="null" :optional-mixed="null" '
        ':defaultedCount="null" ordinary="fall-through attribute" />'
    )
    assert _vue_component_prop_findings(_check_vue_component_prop_template(tmp_path, valid)) == []

    missing = _vue_component_prop_findings(_check_vue_component_prop_template(tmp_path, "<c-card />"))
    assert [finding.code for finding in missing] == ["citry.browser.missing-component-prop"] * 4
    assert [finding.message for finding in missing] == [
        "Required Vue prop 'requiredTitle' is missing for <c-card>.",
        "Required Vue prop 'requiredCount' is missing for <c-card>.",
        "Required Vue prop 'requiredRows' is missing for <c-card>.",
        "Required Vue prop 'requiredDefault' is missing for <c-card>.",
    ]
    assert all(finding.start_index == 1 and finding.end_index == 7 for finding in missing)

    incompatible_source = (
        '<c-card :required-title="1" :requiredCount="\'many\'" :requiredRows="1" :requiredDefault="false" />'
    )
    incompatible = _vue_component_prop_findings(_check_vue_component_prop_template(tmp_path, incompatible_source))
    assert [finding.code for finding in incompatible] == ["citry.browser.incompatible-component-prop"] * 3
    assert [finding.message for finding in incompatible] == [
        "Vue prop 'required-title' expects string, but this binding is number.",
        "Vue prop 'requiredCount' expects number, but this binding is \"many\".",
        "Vue prop 'requiredRows' expects unknown[], but this binding is number.",
    ]
    expected_ranges = (
        (incompatible_source.index(':required-title="') + len(':required-title="'), 1),
        (incompatible_source.index(':requiredCount="') + len(':requiredCount="'), len("'many'")),
        (incompatible_source.index(':requiredRows="') + len(':requiredRows="'), 1),
    )
    assert [(finding.start_index, finding.end_index) for finding in incompatible] == [
        (start, start + width) for start, width in expected_ranges
    ]


def test_registry_check_reports_a_boolean_prop_given_a_string_other_than_its_own_name(tmp_path):
    # Vue turns '' and the prop's own name, hyphenated, into true for a
    # Boolean prop; any other string arrives as that string.
    value = "open ? 'required-default' : 'closed'"
    template = f'<c-card :requiredTitle="\'x\'" :requiredCount="1" :requiredRows="[]" :requiredDefault="{value}" />'
    findings = _vue_component_prop_findings(_check_vue_component_prop_template(tmp_path, template))

    # Only the result the prop rejects is named; the span covers the whole value.
    assert [finding.message for finding in findings] == [
        "Vue prop 'requiredDefault' expects boolean, but this binding is \"closed\".",
    ]
    assert (findings[0].start_index, findings[0].end_index) == (
        template.index(value),
        template.index(value) + len(value),
    )


@pytest.mark.parametrize(
    "value",
    [
        "''",
        "'required-default'",
        "flag ? '' : false",
        "flag ? true : 'required-default'",
        # A string whose text Citry does not read may be one of the two.
        "`${name}`",
        "cond ? label : 'x'",
    ],
)
def test_registry_check_accepts_the_strings_vue_turns_into_true_for_a_boolean_prop(tmp_path, value):
    template = f'<c-card :requiredTitle="\'x\'" :requiredCount="1" :requiredRows="[]" :requiredDefault="{value}" />'
    assert _vue_component_prop_findings(_check_vue_component_prop_template(tmp_path, template)) == []


def test_registry_check_tracks_vue_component_prop_spread_order_and_dynamic_uncertainty(tmp_path):
    check = lambda source: _vue_component_prop_findings(  # noqa: E731 - keep scenario inputs compact
        _check_vue_component_prop_template(tmp_path, source, dynamic_props=True)
    )
    static_object = (
        "<c-card v-bind=\"{ requiredTitle: 'ready', requiredCount: 2, requiredRows: [], requiredDefault: false }\" />"
    )
    assert check(static_object) == []

    assert check('<c-card v-bind="dynamic_props" />') == []

    explicit_after_dynamic = '<c-card v-bind="dynamic_props" :required-title="1" />'
    after = check(explicit_after_dynamic)
    assert [finding.code for finding in after] == ["citry.browser.incompatible-component-prop"]
    assert after[0].message == "Vue prop 'required-title' expects string, but this binding is number."
    assert after[0].start_index == explicit_after_dynamic.index(':required-title="') + len(':required-title="')
    assert after[0].end_index == after[0].start_index + 1

    explicit_before_dynamic = '<c-card :required-title="1" v-bind="dynamic_props" />'
    assert check(explicit_before_dynamic) == []


def test_registry_check_maps_vue_prop_ranges_after_utf8_text(tmp_path):
    source = 'é<c-card :required-title="1" :requiredCount="2" :requiredRows="[]" :requiredDefault="false" />'

    findings = _vue_component_prop_findings(_check_vue_component_prop_template(tmp_path, source))

    assert len(findings) == 1
    finding = findings[0]
    value_start = len(source[: source.index(':required-title="') + len(':required-title="')].encode("utf-8"))
    utf16_column = len(source[: source.index(':required-title="') + len(':required-title="')].encode("utf-16-le")) // 2
    assert finding.code == "citry.browser.incompatible-component-prop"
    assert (finding.start_index, finding.end_index) == (value_start, value_start + 1)
    assert (finding.line, finding.column, finding.end_line, finding.end_column) == (
        0,
        utf16_column,
        0,
        utf16_column + 1,
    )


@pytest.mark.parametrize("asset_kind", ["inline", "file"])
def test_registry_check_precollects_shared_vue_props_without_loading_js(tmp_path, monkeypatch, asset_kind):
    import citry.component as component_module

    def fail_load_js(*args, **kwargs):
        pytest.fail("the registry check must inspect authored JavaScript without loading the component asset")

    monkeypatch.setattr(component_module, "load_js", fail_load_js)
    engine = Citry(autodiscover=False)
    browser_source: dict[str, object] = {}
    if asset_kind == "inline":
        browser_source["js"] = _VUE_COMPONENT_PROP_JS
    else:
        javascript_file = tmp_path / "props.js"
        javascript_file.write_text(_VUE_COMPONENT_PROP_JS, encoding="utf-8")
        browser_source["js_file"] = javascript_file

    card_namespace = {
        "citry": engine,
        "template": "<div></div>",
        "__module__": __name__,
        **browser_source,
    }
    Card = type("Card", (Component,), card_namespace)
    type("AliasCard", (Card,), {"name": "alias-card", "__module__": __name__})

    shared_template = tmp_path / "shared.html"
    shared_template.write_text("<c-card /><c-alias-card />", encoding="utf-8")
    for page_name in ("PageOne", "PageTwo"):
        type(
            page_name,
            (Component,),
            {"citry": engine, "template_file": shared_template, "__module__": __name__},
        )

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    findings = _vue_component_prop_findings(report)
    expected = [
        f"Required Vue prop '{name}' is missing for <c-card>."
        for name in ("requiredTitle", "requiredCount", "requiredRows", "requiredDefault")
    ] + [
        f"Required Vue prop '{name}' is missing for <c-alias-card>."
        for name in ("requiredTitle", "requiredCount", "requiredRows", "requiredDefault")
    ]
    assert [finding.message for finding in findings] == expected
    assert len([finding for finding in report.findings if finding.origin == str(shared_template)]) == 8


def test_registry_check_keeps_unknown_child_diagnostics_and_known_vue_props(tmp_path):
    source = (
        '<c-card :required-title="\'ready\'" :requiredCount="2" :requiredRows="[]" '
        ':requiredDefault="false" ordinary="fall-through" /><c-ghost />'
    )

    report = _check_vue_component_prop_template(tmp_path, source)

    assert _vue_component_prop_findings(report) == []
    assert [(finding.code, finding.message) for finding in report.findings] == [
        ("citry.template.unknown-component", "Component <c-ghost> is not registered.")
    ]


@pytest.mark.parametrize(
    ("source", "message", "start_marker", "end_marker"),
    [
        (
            '<c-component is="mark" />',
            "Marker requires a literal name attribute.",
            "c-component",
            "c-component",
        ),
        (
            '<c-component is="mark" :name="dynamic" />',
            "Marker name must be a static literal.",
            ":name",
            "dynamic",
        ),
        (
            '<c-component is="mark" name="9bad" />',
            "Marker name must match [A-Za-z][A-Za-z0-9_-]*.",
            "9bad",
            "9bad",
        ),
        (
            '<c-component is="mark" name="valid" title="extra" />',
            "Marker accepts only its name attribute.",
            "title",
            "title",
        ),
        (
            '<c-component is="mark" name="valid" NAME="other" />',
            "Marker accepts only its name attribute.",
            "NAME",
            "NAME",
        ),
        (
            '<c-component is="mark" name="valid"><c-fill name="Default">x</c-fill></c-component>',
            "Marker accepts only its default slot.",
            "Default",
            "Default",
        ),
        (
            '<c-component is="mark" name="valid"><c-fill c-name="fillName">x</c-fill></c-component>',
            "Marker accepts only its default slot.",
            "fillName",
            "fillName",
        ),
        (
            '<c-mark name="9bad" />',
            "Marker name must match [A-Za-z][A-Za-z0-9_-]*.",
            "9bad",
            "9bad",
        ),
    ],
)
def test_registry_check_reports_invalid_literal_marker_authoring(
    tmp_path: Path,
    source: str,
    message: str,
    start_marker: str,
    end_marker: str,
):
    report = _check_mark_template(tmp_path, source)

    findings = [finding for finding in report.findings if finding.code == TEMPLATE_MARKER_NAME_INVALID]

    assert len(findings) == 1
    finding = findings[0]
    expected_start = len(source[: source.index(start_marker)].encode("utf-8"))
    expected_end = len(source[: source.index(end_marker) + len(end_marker)].encode("utf-8"))
    assert finding.message == message
    assert (finding.start_index, finding.end_index) == (expected_start, expected_end)


@pytest.mark.parametrize(
    "source",
    [
        '<c-component c-is="selector" name="valid" />',
        '<c-component is="card" />',
    ],
)
def test_registry_check_leaves_dynamic_and_nonmark_component_selectors_alone(tmp_path: Path, source: str):
    report = _check_mark_template(tmp_path, source)

    assert not [finding for finding in report.findings if finding.code == TEMPLATE_MARKER_NAME_INVALID]


@pytest.mark.parametrize(
    ("source", "message_fragment"),
    [
        ('<c-mark :name="dynamic" />', "must have one of the following attributes: 'name', 'c-name'"),
        ('<c-mark NAME="other" />', "Found invalid attributes: NAME"),
        ('<c-component is="mark" name="one" name="two" />', "Duplicate attribute 'name' found."),
    ],
)
def test_registry_check_keeps_parser_owned_mark_syntax_rejections(tmp_path: Path, source: str, message_fragment: str):
    report = _check_mark_template(tmp_path, source)

    assert [finding.code for finding in report.findings] == ["citry.parse.syntax"]
    assert message_fragment in report.findings[0].message


def test_registry_check_reports_leftover_alpine_attributes_with_component_severities(tmp_path):
    engine = Citry(autodiscover=False, lint=LintSettings(rule_alpine_cloak="warning"))

    class Card(Component):
        citry = engine
        template = """
          <div x-data="{ open: false }" x-cloak>
            <c-inner x-label="'kwarg'" />
          </div>
        """

    # No Kwargs schema, so the tag accepts `x-label` as a keyword argument.
    class Inner(Component):
        citry = engine
        template = "<p>inner</p>"

    class Picker(Component):
        citry = engine
        template = '<input x-mask="99/99">'

        class Lint:
            rule_alpine_attribute = "ignore"

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [
        (item.code, item.severity, item.line)
        for item in report.findings
        if item.code.startswith("citry.template.alpine-")
    ]

    # The component tag's `x-label` is a kwarg, the application lowered
    # x-cloak to a warning, and Picker ignores the attribute rule.
    assert findings == [
        ("citry.template.alpine-attribute", "warning", 1),
        ("citry.template.alpine-cloak", "warning", 1),
    ]


def test_static_check_reports_leftover_alpine_attributes_with_default_severities(tmp_path):
    (tmp_path / "card.py").write_text(
        "from citry import Component\nclass Card(Component):\n    template = '<div x-show=\"open\" x-cloak></div>'\n",
        encoding="utf-8",
    )

    report = check_project(CheckAppSelection(), tmp_path)

    assert [(item.code, item.severity) for item in report.findings] == [
        ("citry.template.alpine-attribute", "warning"),
        ("citry.template.alpine-cloak", "error"),
    ]


def test_registry_check_reports_invalid_attribute_values_with_component_severities(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
          <div draggable="treu">
            <input type="datetime">
          </div>
        """

    class Legacy(Component):
        citry = engine
        template = '<div dir="sideways"></div>'

        class Lint:
            rule_invalid_attribute_value = "ignore"

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [
        (item.severity, item.line, item.column, item.end_column)
        for item in report.findings
        if item.code == "citry.template.invalid-attribute-value"
    ]

    # A known component gets the default error, and Legacy ignores the rule.
    # Each finding spans the value inside its quotes.
    assert findings == [("error", 1, 16, 20), ("error", 2, 15, 23)]


def test_static_check_reports_invalid_attribute_values_as_warnings(tmp_path):
    (tmp_path / "card.py").write_text(
        "from citry import Component\nclass Card(Component):\n    template = '<a target=\"_new\">a</a>'\n",
        encoding="utf-8",
    )

    report = check_project(CheckAppSelection(), tmp_path)

    # Static mode cannot read LintSettings, which might turn the rule off, so
    # with no Lint class the finding stays a warning and the check exits 0.
    assert [(item.code, item.severity) for item in report.findings] == [
        ("citry.template.invalid-attribute-value", "warning"),
    ]


def test_registry_check_reports_misspelled_directives_with_component_severities(tmp_path):
    engine = Citry(autodiscover=False)

    class Panel(Component):
        citry = engine
        template = """
          <div c-iff="True">a</div>
          <input c-form="'f'">
        """

    class Widget(Component):
        citry = engine
        template = '<div c-show="True"></div>'

        class Lint:
            rule_misspelled_directive = "ignore"

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [
        (item.severity, item.line, item.column, item.end_column, item.message)
        for item in report.findings
        if item.code == "citry.template.misspelled-directive"
    ]

    # `c-form` binds a real attribute of <input>; Widget ignores the rule.
    # The finding spans the attribute name.
    assert findings == [
        (
            "error",
            1,
            5,
            10,
            "'c-iff' is not a Citry directive, so it renders an HTML attribute named 'iff'. Did you mean 'c-if'?",
        ),
    ]


def test_static_check_reports_misspelled_directives_as_errors(tmp_path):
    (tmp_path / "card.py").write_text(
        "from citry import Component\nclass Card(Component):\n    template = '<p c-elseif=\"x\">a</p>'\n",
        encoding="utf-8",
    )

    report = check_project(CheckAppSelection(), tmp_path)

    assert [(item.code, item.severity) for item in report.findings] == [
        ("citry.template.misspelled-directive", "error"),
    ]


def _static_lint_findings(tmp_path, source: str) -> list[tuple[str, str]]:
    """Run static mode over one component module and return (code, severity) per finding."""
    (tmp_path / "card.py").write_text("from citry import Component\n" + source, encoding="utf-8")
    report = check_project(CheckAppSelection(), tmp_path)
    return [(item.code, item.severity) for item in report.findings]


_STATIC_LINT_TEMPLATE = '    template = \'<p c-iff="x" dir="sideways" x-cloak>a</p>\'\n'


def test_static_check_applies_the_component_lint_class(tmp_path):
    findings = _static_lint_findings(
        tmp_path,
        "class Card(Component):\n" + _STATIC_LINT_TEMPLATE + "    class Lint:\n"
        "        rule_misspelled_directive = 'ignore'\n"
        "        rule_invalid_attribute_value = 'error'\n"
        "        rule_alpine_cloak = 'warning'\n",
    )

    # Each rule takes the component's own literal value.
    assert sorted(findings) == [
        ("citry.template.alpine-cloak", "warning"),
        ("citry.template.invalid-attribute-value", "error"),
    ]


def test_static_check_uses_no_application_severities_for_unreadable_lint(tmp_path):
    findings = _static_lint_findings(
        tmp_path,
        "from myapp.lint import IGNORE\n"
        "class Card(Component):\n" + _STATIC_LINT_TEMPLATE + "    class Lint:\n"
        "        rule_misspelled_directive = IGNORE\n",
    )

    # The imported name cannot be read without running the code, so each
    # rule keeps the severity it has without an application.
    assert sorted(findings) == [
        ("citry.template.alpine-cloak", "error"),
        ("citry.template.invalid-attribute-value", "warning"),
        ("citry.template.misspelled-directive", "error"),
    ]


def test_static_check_reads_inherited_lint_and_reports_the_strictest_owner(tmp_path):
    base = (
        "class Base(Component):\n"
        "    class Lint:\n"
        "        rule_misspelled_directive = 'ignore'\n"
        "class Card(Base):\n"
        "    template = '<p c-iff=\"x\">a</p>'\n"
    )

    # Card inherits Base's "ignore".
    assert _static_lint_findings(tmp_path, base) == []
    # Shop renders Card's template and sets "warning", the stricter choice.
    shop = "class Shop(Card):\n    class Lint:\n        rule_misspelled_directive = 'warning'\n"
    assert _static_lint_findings(tmp_path, base + shop) == [("citry.template.misspelled-directive", "warning")]
    # Plain drops the inherited Lint, so its default error applies.
    plain = "class Plain(Card):\n    Lint = None\n"
    assert _static_lint_findings(tmp_path, base + plain) == [("citry.template.misspelled-directive", "error")]


def test_registry_check_reports_undeclared_emits_and_child_listeners(tmp_path):
    engine = Citry(autodiscover=False)

    class Lane(Component):
        citry = engine
        template = """
          <section></section>
        """
        js = """
          $component({
            emits: ['drop-task'],
            methods: {
              drop() {
                this.$emit('drop-task');
                this.$emit('drop-tsak');
              },
            },
          });
        """

    class Board(Component):
        citry = engine
        template = """
          <c-Lane
            @drop-task="move($event)"
            @drop-tsak="move($event)"
            @click="move($event)"
          ></c-Lane>
          <button @click="$emit('moved')"></button>
        """
        js = """
          $component({
            emits: ['changed'],
            methods: { move() {} },
          });
        """

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = sorted(
        (item.code, item.severity, item.message)
        for item in report.findings
        if item.code.startswith("citry.browser.undeclared-")
    )

    # `@click` may be a native event, so only the hyphenated typo is reported.
    assert findings == [
        (
            "citry.browser.undeclared-component-event",
            "warning",
            "Component 'c-lane' does not declare event 'drop-tsak' in its emits option. Did you mean 'drop-task'?",
        ),
        (
            "citry.browser.undeclared-emit",
            "error",
            "Event 'drop-tsak' is not declared in this component's emits option.",
        ),
        ("citry.browser.undeclared-emit", "error", "Event 'moved' is not declared in this component's emits option."),
    ]


# The benchmark mistakes the template-only rules catch, one per line.
_MARKUP_MISTAKES = """
  <div class="board" id="board" titel="Board">
    <dvi class="row"></dvi>
    <h1 id="board">Board</h1>
    <p>Owner: <div>Ann</div></p>
    <img src="/static/avatar.svg" width="32">
    <button :aria-expandd="open" @clik="toggle()" disabled="false">Menu</button>
    <form v-model="query"><input name="q"></form>
    <p v-iff="open">Details</p>
    <p v-if="open &&">More</p>
    <table><div>Row</div></table>
  </div>
"""
_MARKUP_FINDINGS = [
    ("citry.template.misspelled-attribute", "error", 1),
    ("citry.template.misspelled-element", "error", 2),
    ("citry.template.duplicate-id", "error", 3),
    ("citry.template.invalid-nesting", "error", 4),
    ("citry.template.missing-image-alt", "warning", 5),
    ("citry.template.invalid-attribute-value", "warning", 6),
    ("citry.template.unknown-aria-attribute", "error", 6),
    ("citry.vue.misspelled-event", "warning", 6),
    ("citry.browser.invalid-model-target", "error", 7),
    ("citry.template.misspelled-directive", "error", 8),
    ("citry.vue.invalid-expression", "error", 9),
    ("citry.vue.compile-error", "error", 10),
]


def _sorted_findings(report) -> list[tuple[str, str, int | None]]:
    return sorted(
        ((item.code, item.severity, item.line) for item in report.findings),
        key=lambda item: (item[2] or 0, item[0]),
    )


def test_static_check_reports_the_template_only_rules_with_each_default_severity(tmp_path):
    (tmp_path / "card.py").write_text(
        f'from citry import Component\nclass Card(Component):\n    template = """{_MARKUP_MISTAKES}"""\n',
        encoding="utf-8",
    )

    report = check_project(CheckAppSelection(), tmp_path)

    # The finding lines count from the first line of the template string.
    # Without the application an invalid attribute value is a warning.
    assert _sorted_findings(report) == sorted(_MARKUP_FINDINGS, key=lambda item: (item[2], item[0]))


def test_static_check_applies_the_component_lint_class_to_the_template_only_rules(tmp_path):
    (tmp_path / "card.py").write_text(
        "from citry import Component\n"
        f'class Card(Component):\n    template = """{_MARKUP_MISTAKES}"""\n'
        "    class Lint:\n"
        "        rule_missing_image_alt = 'error'\n"
        "        rule_duplicate_id = 'ignore'\n"
        "        rule_invalid_vue_expression = 'warning'\n"
        "        rule_vue_compile_error = 'warning'\n",
        encoding="utf-8",
    )

    findings = {
        (code, severity) for code, severity, _line in _sorted_findings(check_project(CheckAppSelection(), tmp_path))
    }

    assert ("citry.template.missing-image-alt", "error") in findings
    assert ("citry.vue.invalid-expression", "warning") in findings
    assert ("citry.vue.compile-error", "warning") in findings
    assert not any(code == "citry.template.duplicate-id" for code, _severity in findings)


def test_registry_check_reports_the_template_only_rules_with_the_application_settings(tmp_path):
    engine = Citry(
        autodiscover=False,
        lint=LintSettings(rule_misspelled_event="error", rule_invalid_nesting="ignore"),
    )

    class Card(Component):
        citry = engine
        template = _MARKUP_MISTAKES

    class Quiet(Component):
        citry = engine
        template = '<p titel="x"></p>'

        class Lint:
            rule_misspelled_attribute = "ignore"

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    # The component sends no browser data, so its Vue names are unknown too.
    findings = [item for item in _sorted_findings(report) if item[0] != "citry.vue.unknown-variable"]

    # With the application, an invalid attribute value is an error, and
    # each setting applies; Quiet turns its rule off for itself.
    expected = [
        (
            code,
            "error" if code in {"citry.template.invalid-attribute-value", "citry.vue.misspelled-event"} else severity,
            line,
        )
        for code, severity, line in _MARKUP_FINDINGS
        if code != "citry.template.invalid-nesting"
    ]
    assert findings == sorted(expected, key=lambda item: (item[2], item[0]))


def _csp_findings(report) -> list[tuple[str, int | None, int | None, int | None, int | None]]:
    return sorted(
        (item.severity, item.line, item.column, item.end_line, item.end_column)
        for item in report.findings
        if item.code == "citry.template.csp-incompatible"
    )


def _csp_engine_components(engine: Citry) -> None:
    """Define the two components whose templates the CSP tests check."""

    class Card(Component):
        citry = engine
        template = """
          <button onclick="save()">Save</button>
          <a href="javascript:go()">Go</a>
          <script>run()</script>
          <c-raw><b onclick="x">c</b></c-raw>
        """

    class Plain(Component):
        citry = engine
        # The non-ASCII letter shows that columns count characters, not bytes.
        template = '<p>é <i onclick="y"></i></p>'


@pytest.mark.parametrize(
    ("mode", "severity"),
    [("warn", "warning"), ("strict", "error")],
)
def test_registry_check_reports_strict_csp_problems_with_the_engines_severity(tmp_path, mode, severity):
    engine = Citry(autodiscover=False, security_csp=mode)
    _csp_engine_components(engine)

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # Each finding spans the attribute name, the javascript: value, or the tag
    # name; <c-raw> content is read as the HTML that comes out.
    assert _csp_findings(report) == [
        (severity, 0, 8, 0, 15),
        (severity, 1, 8, 1, 15),
        (severity, 2, 9, 2, 24),
        (severity, 3, 1, 3, 7),
        (severity, 4, 10, 4, 17),
    ]


def test_registry_check_reports_nothing_about_csp_while_the_engine_has_it_off(tmp_path):
    engine = Citry(autodiscover=False)
    _csp_engine_components(engine)

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    assert _csp_findings(report) == []


def test_registry_check_leaves_a_registered_components_attributes_out_of_the_csp_check(tmp_path):
    engine = Citry(autodiscover=False, security_csp="strict")

    class Inner(Component):
        citry = engine
        template = "<b>inner</b>"

    class Outer(Component):
        citry = engine
        template = '<c-inner onclick="x" href="javascript:y" /><c-unknown onclick="x" />'

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    assert _csp_findings(report) == []


def test_static_check_reports_nothing_about_csp_because_it_has_no_engine_settings(tmp_path):
    (tmp_path / "card.py").write_text(
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template = \'<div titel="x" onclick="y"></div><script>z()</script>\'\n',
        encoding="utf-8",
    )

    report = check_project(CheckAppSelection(), tmp_path)

    # The misspelled attribute shows that the template was read.
    assert [item.code for item in report.findings] == ["citry.template.misspelled-attribute"]


def test_registry_check_reports_only_an_ordinary_component_inside_a_vue_v_for(tmp_path):
    engine = Citry(autodiscover=False)

    class Row(Component):
        citry = engine
        template = "<li>row</li>"

    class Label(Component):
        citry = engine
        transparent = True
        template = "<b>label</b>"

    class Table(Component):
        citry = engine
        template = '<ul><template v-for="item in items"><c-row /><c-label /></template></ul>'

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # A transparent component is copied into the caller's template, so a
    # Vue `v-for` may repeat it.
    findings = [item for item in report.findings if item.code == "citry.vue.compile-error"]
    assert [(item.line, item.column) for item in findings] == [(0, 37)]
    assert "Repeat it with '<c-for>'" in findings[0].message


def test_registry_check_reports_a_root_image_only_without_browser_code(tmp_path):
    engine = Citry(autodiscover=False)

    class Avatar(Component):
        citry = engine
        template = '<img src="/static/avatar.svg">'

    class BrowserAvatar(Component):
        citry = engine
        template = '<img :src="src">'
        js = """
          $component({ props: ['src'] });
        """

    class StateAvatar(Component):
        citry = engine
        template = '<img src="/static/avatar.svg">'

        class State:
            loaded: bool = False

    class DataAvatar(Component):
        citry = engine
        template = '<img src="/static/avatar.svg">'

        def js_data(self, kwargs, slots):
            return {"src": "/static/avatar.svg"}

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # Vue passes the alt a parent writes on <c-BrowserAvatar> to its root
    # <img>, and browser data or State may make Vue render a component
    # too; a server-only component has no such path.
    (finding,) = report.findings
    assert finding.code == "citry.template.missing-image-alt"
    assert "Avatar" in finding.origin
    assert "BrowserAvatar" not in finding.origin


@pytest.mark.parametrize(
    ("options", "reported"),
    [
        # Vue does not pass a parent's attributes on, so nothing adds alt.
        ("inheritAttrs: false", True),
        ("inheritAttrs: true", False),
        # Vue's default passes them on.
        ("props: ['src']", False),
        # A value the check cannot read may be true.
        ("inheritAttrs: window.flag", False),
        ("inheritAttrs: false, ...shared", False),
    ],
)
def test_registry_check_reports_a_root_image_whose_component_sets_inherit_attrs_false(tmp_path, options, reported):
    engine = Citry(autodiscover=False)

    class Avatar(Component):
        citry = engine
        template = '<img :src="src">'
        js = f"""
          $component({{ {options} }});
        """

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    codes = [item.code for item in report.findings if item.code == "citry.template.missing-image-alt"]
    assert codes == (["citry.template.missing-image-alt"] if reported else [])


@pytest.mark.parametrize(
    ("directives", "reported"),
    [
        ("directives: { iff: { mounted() {} } }", False),
        ("directives: { Iff: { mounted() {} } }", False),
        # A directive the check cannot list may be any name.
        ("directives: shared", True),
        ("directives: { focus: {} }", True),
        ("props: ['open']", True),
    ],
)
def test_registry_check_accepts_a_custom_directive_the_component_registers(tmp_path, directives, reported):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = '<p v-iff="open">Details</p>'
        js = f"""
          $component({{ props: ['open'], {directives} }});
        """

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    codes = [item.code for item in report.findings if item.code == "citry.template.misspelled-directive"]
    assert codes == (["citry.template.misspelled-directive"] if reported else [])


def test_registry_check_reports_a_shared_template_one_owner_does_not_register(tmp_path):
    (tmp_path / "details.html").write_text('<p v-iff="open">Details</p>', encoding="utf-8")
    engine = Citry(autodiscover=False)

    class Registers(Component):
        citry = engine
        template_file = str(tmp_path / "details.html")
        js = """
          $component({ props: ['open'], directives: { iff: {} } });
        """

    class Plain(Component):
        citry = engine
        template_file = str(tmp_path / "details.html")
        js = """
          $component({ props: ['open'] });
        """

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # The template fails in the component that does not register `iff`.
    assert [item.code for item in report.findings if item.code == "citry.template.misspelled-directive"] == [
        "citry.template.misspelled-directive"
    ]


def test_registry_check_reports_lowercase_child_listener_typos_with_the_configured_severity(tmp_path):
    engine = Citry(autodiscover=False, lint=LintSettings(rule_undeclared_component_event="error"))

    class Card(Component):
        citry = engine
        template = "<section></section>"
        js = """
          $component({ emits: ['hide'] });
        """

    class Board(Component):
        citry = engine
        template = '<c-Card @hdie="hideCard" @click="hideCard"></c-Card>'
        js = """
          $component({ methods: { hideCard() {} } });
        """

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    # `@click` is a DOM event the child's root may fire; `@hdie` is not.
    assert [
        (item.code, item.severity, item.message)
        for item in report.findings
        if item.code == "citry.browser.undeclared-component-event"
    ] == [
        (
            "citry.browser.undeclared-component-event",
            "error",
            "Component 'c-card' does not declare event 'hdie' in its emits option. Did you mean 'hide'?",
        ),
    ]
