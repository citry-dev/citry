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
        assert "unsupported non-None template_lang" in error
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
        assert report.findings[0].message == "1:8: unknown registered component <c-Ghost>"

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
        assert "cannot read" in report.findings[0].message
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
        assert "unknown registered component" not in error

    @pytest.mark.parametrize(
        "body",
        [
            "engine = object()\n",
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
        assert "unknown registered component" not in error

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
        assert all("unknown registered component" not in finding.message for finding in report.findings)

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
