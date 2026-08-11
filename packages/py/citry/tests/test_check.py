"""Focused behavior tests for the conservative ``citry check`` command."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, cast

import pytest

from citry import Citry, Component
from citry.__main__ import main
from citry._app_selection import CheckAppSelection
from citry._checker import TRANSFORM_NOTE, check_project

if TYPE_CHECKING:
    from pathlib import Path


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

    def test_static_component_props_report_unknown_and_missing_keys(self, tmp_path):
        engine = Citry(autodiscover=False)

        class Child(Component):
            citry = engine
            js = """
              $component({
                props: {
                  title: { type: String, required: true },
                  count: { type: Number, required: true },
                  enabled: { type: Boolean, required: true },
                },
                init() {},
              });
            """
            template = """
              <span></span>
            """

        class Parent(Component):
            citry = engine
            template = """
              <c-child $c-props="{ title: title, count: 'many', extra: true }" />
              <c-child $c-props="{ title, ...{} }" />
            """

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings if finding.code.startswith("citry.browser.")] == [
            "citry.browser.incompatible-component-prop",
            "citry.browser.unknown-component-prop",
            "citry.browser.missing-component-prop",
        ]

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

        assert report.findings[0].code == "citry.i18n.missing-param-type"
        assert report.findings[0].severity == "warning"
        assert "without an @param" in report.findings[0].message
        assert report.exit_code == 0

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

    def test_client_message_ids_and_cross_language_plain_fallback_are_checked(self, tmp_path):
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
            messages = "known-message = Known"
            template = '{{ tr("known-message") }}'

            class I18n:
                client_messages = ("missing-client-message",)

        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

        assert [finding.code for finding in report.findings] == [
            "citry.i18n.client-message-invalid",
            "citry.i18n.cross-language-fallback",
        ]

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
        )
        js = 'sendEvent("missing"); loading("missing"); error(); sendEvent(dynamicName); onEvent("anything", () => {})'

        class JsData:
            title: str
            invalid: set[str]

        class Events:
            def save(self):
                pass

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    assert [finding.code for finding in report.findings].count("citry.js-data.unsupported-type") == 1
    assert [finding.code for finding in report.findings].count("citry.browser.unknown-server-event") == 5
    assert {finding.severity for finding in report.findings if "unsupported-type" in finding.code} == {"warning"}


def test_registry_check_joins_inferred_js_data_values_to_kwargs_types(tmp_path, monkeypatch, capsys):
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
        "    def js_data(self, options: Kwargs, slots):\n"
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
        )
        js = 'sendEvent("save"); loading("save"); error(); $sendEvent(name); $onEvent("anything", fn)'

        class Events:
            def save(self):
                pass

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    assert not [finding for finding in report.findings if finding.code == "citry.browser.unknown-server-event"]


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
            rule_unknown_alpine_variable = "warning"
            alpine_variables = {"customGlobal": str}

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [item for item in report.findings if item.code == "citry.alpine.unknown-variable"]

    assert [(item.message, item.severity) for item in findings] == [
        ("Alpine variable 'disabled1' is not available in this component.", "warning")
    ]


def test_registry_check_defaults_unknown_alpine_roots_to_error(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = '<button :disabled="disabled1"></button>'

        class JsData:
            disabled: bool

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    findings = [item for item in report.findings if item.code == "citry.alpine.unknown-variable"]

    assert len(findings) == 1
    assert findings[0].severity == "error"


def test_registry_check_reports_unknown_component_js_variables_and_missing_context_binding(tmp_path):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        js = """
        const outside = notCheckedHere;
        $component(({ data }) => {
          console.log(data.ready, configuredClient);
          scope.ready = data.ready;
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
