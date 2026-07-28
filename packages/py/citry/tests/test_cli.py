"""Tests for the citry CLI wiring: engine binding, the command tree, and the entry point."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from citry import Citry as _Citry
from citry import CommandArg, Component, Extension, ExtensionCommand
from citry.__main__ import main
from citry.command import format_as_ascii_table, run
from citry.commands import build_cli
from citry.commands.inspect import InspectCommand


@pytest.fixture(autouse=True)
def _sys_path_guard(monkeypatch):
    """
    Give every test a throwaway copy of sys.path.

    Calling ``main()`` in-process prepends the working directory to sys.path
    (that is its job, mirroring the console script). Running against a copy
    keeps that mutation from leaking into the rest of the pytest session.
    """
    monkeypatch.setattr(sys, "path", list(sys.path))


def _engine_with_command(captured):
    """A Citry whose 'greeter' extension provides a 'greet' command that records its inputs."""

    class Greet(ExtensionCommand):
        name = "greet"
        help = "Greet someone."
        arguments = [CommandArg("who")]

        def handle(self, **kwargs):
            captured["who"] = kwargs["who"]
            captured["citry"] = self.citry

    class Greeter(Extension):
        name = "greeter"
        commands = [Greet]

    return _Citry(extensions=[Greeter]), Greet


class TestEngineBinding:
    def test_handle_receives_bound_engine(self):
        captured: dict = {}
        engine, greet = _engine_with_command(captured)
        run(greet, ["world"], citry=engine)
        assert captured["who"] == "world"
        assert captured["citry"] is engine

    def test_engine_is_none_without_binding(self):
        seen: dict = {}

        class Cmd(ExtensionCommand):
            name = "cmd"

            def handle(self, **kwargs):
                seen["citry"] = self.citry

        run(Cmd, [])
        assert seen["citry"] is None


class TestCommandTree:
    def test_ext_run_dispatches_to_extension_command(self):
        captured: dict = {}
        engine, _ = _engine_with_command(captured)
        code = run(build_cli(engine), ["ext", "run", "greeter", "greet", "world"], citry=engine)
        assert code == 0
        assert captured["who"] == "world"
        assert captured["citry"] is engine

    def test_ext_run_unknown_extension_raises(self):
        engine, _ = _engine_with_command({})
        # 'nope' is not a routing node, so argparse rejects it.
        with pytest.raises(SystemExit):
            run(build_cli(engine), ["ext", "run", "nope", "greet"], citry=engine)

    def test_ext_run_unknown_command_under_known_extension_raises(self, capsys):
        engine, _ = _engine_with_command({})
        # 'greeter' resolves, but 'nope' is not one of its commands.
        with pytest.raises(SystemExit) as exc:
            run(build_cli(engine), ["ext", "run", "greeter", "nope"], citry=engine)
        assert exc.value.code == 2  # argparse usage error
        err = capsys.readouterr().err
        assert "usage: citry ext run greeter" in err
        assert "invalid choice: 'nope'" in err

    def test_ext_run_extension_without_command_lists_its_commands(self, capsys):
        engine, _ = _engine_with_command({})
        run(build_cli(engine), ["ext", "run", "greeter"], citry=engine)
        # The routing node has no handle, so it prints help listing its
        # commands. The braces roster is the lock: plain "greet" also appears
        # inside "greeter" in the usage line, so it proves nothing.
        assert "{greet}" in capsys.readouterr().out

    def test_ext_list_lists_extensions(self, capsys):
        engine, _ = _engine_with_command({})
        run(build_cli(engine), ["ext", "list"], citry=engine)
        out = capsys.readouterr().out
        assert "greeter" in out
        assert "dependencies" in out  # the built-in extension


class TestHelpListings:
    """Invoking a grouping node (no handle of its own) prints help listing what it offers."""

    def test_bare_citry_lists_subcommands_and_version(self, capsys):
        engine, _ = _engine_with_command({})
        code = run(build_cli(engine), [], citry=engine)
        assert code == 0
        out = capsys.readouterr().out
        assert "usage: citry" in out
        assert "{list,inspect,create,watch,ext}" in out
        assert "--version" in out
        # Each subcommand's one-line description appears in the listing
        # (watch's wraps across lines, so its roster entry above stands in).
        assert "List the registered components." in out
        assert "Emit the runtime component catalog as JSON." in out
        assert "Scaffold a new component file." in out
        assert "Inspect and run extension commands." in out

    def test_help_flag_prints_the_same_root_listing(self, capsys):
        engine, _ = _engine_with_command({})
        run(build_cli(engine), [], citry=engine)
        bare_out = capsys.readouterr().out
        # --help is handled by argparse itself, which exits 0 after printing
        # the identical help text the bare invocation printed.
        with pytest.raises(SystemExit) as exc:
            run(build_cli(engine), ["--help"], citry=engine)
        assert exc.value.code == 0
        assert capsys.readouterr().out == bare_out

    def test_ext_lists_its_subcommands(self, capsys):
        engine, _ = _engine_with_command({})
        code = run(build_cli(engine), ["ext"], citry=engine)
        assert code == 0
        out = capsys.readouterr().out
        assert "usage: citry ext" in out
        assert "{list,run}" in out
        assert "List the installed extensions." in out
        assert "Run a command provided by an extension." in out

    def test_ext_run_lists_only_extensions_with_commands(self, capsys):
        class Cmd(ExtensionCommand):
            name = "cmd"

            def handle(self, **kwargs):
                pass

        class WithCommand(Extension):
            name = "hascmd"
            commands = [Cmd]

        class Plain(Extension):
            name = "plain"

        engine = _Citry(extensions=[WithCommand, Plain])
        code = run(build_cli(engine), ["ext", "run"], citry=engine)
        assert code == 0
        out = capsys.readouterr().out
        assert "hascmd" in out
        assert "plain" not in out  # declares no commands, so 'ext run' does not offer it


class TestMain:
    def test_default_engine(self, capsys):
        # No --app: the default global engine, which carries only the built-ins.
        assert main(["ext", "list"]) == 0
        assert "dependencies" in capsys.readouterr().out

    def test_app_option_resolves_engine(self, capsys):
        assert main(["--app", "citry.citry:citry", "ext", "list"]) == 0
        assert "dependencies" in capsys.readouterr().out

    def test_app_option_must_be_module_colon_attribute(self):
        with pytest.raises(SystemExit):
            main(["--app", "no-colon-here", "ext", "list"])

    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        assert "citry" in capsys.readouterr().out


class TestListComponents:
    def test_lists_registered_components(self, capsys):
        engine = _Citry()

        class MyButton(Component):
            citry = engine
            template = """
            <button></button>
            """

        run(build_cli(engine), ["list"], citry=engine)
        out = capsys.readouterr().out
        # Both registered names share one merged row, so the class appears once.
        assert "mybutton, my-button" in out
        assert out.count("MyButton") == 1
        expected_path = str(Path(__file__).relative_to(Path.cwd()))
        my_button_lines = [line for line in out.splitlines() if line.startswith("mybutton")]
        assert my_button_lines == [f"mybutton, my-button  {'MyButton':<16}  {expected_path}"]

    def test_projects_the_complete_runtime_catalog(self, monkeypatch, capsys):
        engine = _Citry()

        class ZebraCard(Component):
            citry = engine
            template = """
            <article></article>
            """

        engine.register(ZebraCard, "extra")
        monkeypatch.setattr("citry.commands.list._source_path", lambda _: "source.py")

        run(build_cli(engine), ["list"], citry=engine)

        out = capsys.readouterr().out
        expected_rows = [
            {"name": "cache", "class": "Cache", "path": "source.py"},
            {"name": "component", "class": "DynamicComponent", "path": "source.py"},
            {"name": "css", "class": "Css", "path": "source.py"},
            {"name": "element", "class": "DynamicElement", "path": "source.py"},
            {"name": "error-fallback", "class": "ErrorFallback", "path": "source.py"},
            {"name": "js", "class": "Js", "path": "source.py"},
            {"name": "provide", "class": "Provide", "path": "source.py"},
            {"name": "zebracard, zebra-card, extra", "class": "ZebraCard", "path": "source.py"},
        ]
        assert out == f"{format_as_ascii_table(expected_rows, ('name', 'class', 'path'))}\n"

    def test_explicit_primary_name_stays_ahead_of_manual_class_name_aliases(self, capsys):
        engine = _Citry()

        class MyButton(Component):
            citry = engine
            name = "primary"
            template = """
            <button></button>
            """

        engine.register(MyButton, "mybutton")
        engine.register(MyButton, "my-button")

        run(build_cli(engine), ["list"], citry=engine)

        primary_lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith("primary")]
        assert len(primary_lines) == 1
        assert primary_lines[0].startswith("primary, my-button, mybutton  MyButton  ")

    def test_component_without_a_source_file_gets_an_empty_path_cell(self, capsys):
        # A dynamically built class has no file to point at; the listing
        # shows an empty cell instead of failing.
        engine = _Citry()
        type("Ghost", (Component,), {"citry": engine, "template": "<i></i>", "__module__": "no_such_module_xyz"})

        code = run(build_cli(engine), ["list"], citry=engine)
        out = capsys.readouterr().out
        assert code == 0
        # The ghost row carries exactly its name and class: the path cell is
        # empty, not a placeholder or the exception text.
        ghost_lines = [line for line in out.splitlines() if line.startswith("ghost")]
        assert len(ghost_lines) == 1
        assert ghost_lines[0].split() == ["ghost", "Ghost"]

    @pytest.mark.parametrize("flag", ["--all", "--columns", "--simple"])
    def test_rejects_legacy_format_flags(self, flag):
        engine = _Citry()

        with pytest.raises(SystemExit) as exc:
            run(build_cli(engine), ["list", flag], citry=engine)

        assert exc.value.code == 2


class TestInspectComponents:
    def test_handle_without_a_bound_engine_is_a_noop(self, capsys):
        InspectCommand().handle()

        assert capsys.readouterr().out == ""

    def test_json_emits_the_runtime_catalog(self, capsys):
        engine = _Citry()

        class MyButton(Component):
            citry = engine
            template = """
            <button></button>
            """

        expected = engine.inspect_components().to_json()

        code = run(build_cli(engine), ["inspect", "--json"], citry=engine)

        assert code == 0
        assert capsys.readouterr().out == f"{expected}\n"

    def test_json_uses_the_catalog_api_defaults(self, capsys):
        engine = _Citry()

        class Card(Component):
            citry = engine
            template_file = "card.html"

            class Kwargs:
                count: int = 3

        run(build_cli(engine), ["inspect", "--json"], citry=engine)

        document = json.loads(capsys.readouterr().out)
        assert document["schema_version"] == 1
        assert [component["name"] for component in document["components"]] == ["card"]
        assert document["components"][0]["builtin"] is False
        assert document["components"][0]["assets"]["template"]["resolution"] == "not-requested"
        assert document["components"][0]["schemas"]["kwargs"]["fields"][0]["default_value_state"] == "omitted"
        assert document["extension_versions"] == {}

    def test_json_flag_is_required(self, capsys):
        engine = _Citry()

        with pytest.raises(SystemExit) as exc:
            run(build_cli(engine), ["inspect"], citry=engine)

        assert exc.value.code == 2
        assert "the following arguments are required: --json" in capsys.readouterr().err


class TestCreateComponent:
    def test_writes_component_file(self, tmp_path):
        engine = _Citry()
        code = run(build_cli(engine), ["create", "MyButton", "--path", str(tmp_path)], citry=engine)
        assert code == 0
        created = tmp_path / "my_button.py"
        assert created.exists()
        text = created.read_text()
        assert "class MyButton(Component):" in text
        # The scaffold must be valid Python.
        compile(text, str(created), "exec")

    def test_reports_created_file_path(self, tmp_path, capsys):
        engine = _Citry()
        code = run(build_cli(engine), ["create", "MyButton", "--path", str(tmp_path)], citry=engine)
        assert code == 0
        assert f"Created {tmp_path / 'my_button.py'}" in capsys.readouterr().out

    def test_name_in_any_case_yields_pascal_class_and_snake_file(self, tmp_path):
        engine = _Citry()
        run(build_cli(engine), ["create", "my-fancy-card", "--path", str(tmp_path)], citry=engine)
        created = tmp_path / "my_fancy_card.py"
        assert created.exists()
        assert "class MyFancyCard(Component):" in created.read_text()

    def test_refuses_to_overwrite(self, tmp_path):
        engine = _Citry()
        existing = tmp_path / "my_button.py"
        existing.write_text("# existing\n")
        with pytest.raises(SystemExit):
            run(build_cli(engine), ["create", "MyButton", "--path", str(tmp_path)], citry=engine)
        assert existing.read_text() == "# existing\n"  # left untouched

    def test_preserves_pascalcase_acronym(self, tmp_path):
        engine = _Citry()
        run(build_cli(engine), ["create", "HTTPServer", "--path", str(tmp_path)], citry=engine)
        created = tmp_path / "http_server.py"
        assert created.exists()
        # The user's acronym casing is kept on the class; the file is snake_case.
        assert "class HTTPServer(Component):" in created.read_text()

    def test_rejects_python_keyword_name(self, tmp_path):
        engine = _Citry()
        with pytest.raises(SystemExit):
            run(build_cli(engine), ["create", "True", "--path", str(tmp_path)], citry=engine)
        assert list(tmp_path.iterdir()) == []  # nothing written

    def test_rejects_dunder_module_name(self, tmp_path):
        engine = _Citry()
        with pytest.raises(SystemExit):
            run(build_cli(engine), ["create", "__init__", "--path", str(tmp_path)], citry=engine)
        assert not (tmp_path / "__init__.py").exists()

    def test_path_that_is_a_file_fails_cleanly(self, tmp_path):
        engine = _Citry()
        blocker = tmp_path / "blocker"
        blocker.write_text("x")  # a file where the command expects a directory
        with pytest.raises(SystemExit):
            run(build_cli(engine), ["create", "MyButton", "--path", str(blocker)], citry=engine)


class TestAppHardening:
    def test_app_equals_form(self, capsys):
        assert main(["--app=citry.citry:citry", "ext", "list"]) == 0
        assert "dependencies" in capsys.readouterr().out

    def test_unresolvable_module_fails_cleanly(self, capsys):
        with pytest.raises(SystemExit):
            main(["--app", "no.such.module:engine", "ext", "list"])
        assert "could not import" in capsys.readouterr().err

    def test_inspect_does_not_fall_back_when_the_app_cannot_import(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--app", "no.such.module:engine", "inspect", "--json"])

        captured = capsys.readouterr()
        assert exc.value.code == 2
        assert captured.out == ""
        assert "could not import" in captured.err

    def test_non_citry_target_fails_cleanly(self, capsys):
        # The Citry *class*, not an instance.
        with pytest.raises(SystemExit):
            main(["--app", "citry.citry:Citry", "ext", "list"])
        assert "not a Citry instance" in capsys.readouterr().err

    def test_app_after_subcommand_is_not_hijacked(self):
        # A non-leading --app must reach the real parser (which rejects it here),
        # not be swallowed as engine selection.
        with pytest.raises(SystemExit):
            main(["ext", "list", "--app", "citry.citry:citry"])


class TestAppWorkingDirectory:
    """The CLI resolves --app against the working directory, like uvicorn/gunicorn/flask CLIs do."""

    @pytest.fixture
    def project_dir(self, tmp_path, monkeypatch):
        """A tmp project root (an app.py building a Citry) as cwd, with that dir absent from sys.path."""
        (tmp_path / "app.py").write_text(
            "from citry import Citry\n\nengine = Citry()\n",
        )
        monkeypatch.chdir(tmp_path)
        cwd = str(Path.cwd())  # the resolved path, which can differ from str(tmp_path) through symlinks
        # Console-script processes start without the working directory on
        # sys.path; strip it (pytest can add it) to reproduce those conditions.
        monkeypatch.setattr(sys, "path", [p for p in sys.path if p not in ("", str(tmp_path), cwd)])
        sys.modules.pop("app", None)  # a stale 'app' from another test would mask the import
        yield cwd
        sys.modules.pop("app", None)  # drop the module the CLI imported

    def test_app_in_working_directory_resolves(self, project_dir, capsys):
        # From a plain project root, the console entry must find 'app' the
        # same way 'python -m citry' does.
        assert main(["--app", "app:engine", "ext", "list"]) == 0
        assert "dependencies" in capsys.readouterr().out
        # The fresh insert lands at the FRONT, matching 'python -m' precedence
        # (a project-root module shadows a same-named installed one).
        assert sys.path[0] == project_dir

    def test_inspect_uses_app_in_working_directory(self, project_dir, capsys):
        assert main(["--app", "app:engine", "inspect", "--json"]) == 0
        document = json.loads(capsys.readouterr().out)
        assert document["schema_version"] == 1
        assert document["components"] == []

    def test_cwd_already_on_sys_path_is_not_duplicated(self, project_dir, capsys):
        # 'python -m citry' already puts the cwd at sys.path[0]; the entry
        # must not add a second copy.
        sys.path.insert(0, project_dir)
        assert main(["--app", "app:engine", "ext", "list"]) == 0
        capsys.readouterr()
        assert sys.path.count(project_dir) == 1
        assert sys.path[0] == project_dir

    def test_library_import_and_render_leave_sys_path_untouched(self):
        # Only the CLI entry may extend sys.path; importing citry and rendering
        # must not. Checked in a fresh interpreter, because this test process
        # imported citry long ago.
        script = textwrap.dedent(
            """
            import sys

            snapshot = list(sys.path)

            from citry import Citry, Component

            engine = Citry()

            class Hello(Component):
                citry = engine
                template = '''
                <p>hi</p>
                '''

            html = Hello().render().serialize()
            assert "hi" in html, html
            assert sys.path == snapshot, (snapshot, sys.path)
            print("SYS-PATH-UNTOUCHED")
            """
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert "SYS-PATH-UNTOUCHED" in completed.stdout
