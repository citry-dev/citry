"""Tests for the bounded project-import worker."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from textwrap import dedent

import pytest

from citry import Citry
from citry_lsp import app_worker
from citry_lsp import project as project_module
from citry_lsp.catalog import CatalogIndex
from citry_lsp.project import SourceAnalysisIndex, load_project, load_project_async


@pytest.mark.asyncio
async def test_cancelled_async_project_load_kills_and_reaps_its_worker(tmp_path, monkeypatch):
    communicate_started = asyncio.Event()
    reaped = asyncio.Event()
    never = asyncio.Event()

    class Process:
        returncode = None
        calls = 0
        killed = False

        async def communicate(self):
            self.calls += 1
            if self.calls == 1:
                communicate_started.set()
                await never.wait()
            self.returncode = -9
            reaped.set()
            return b"", b""

        def kill(self):
            self.killed = True
            self.returncode = -9

        async def wait(self):
            reaped.set()
            return self.returncode

    process = Process()

    async def create_process(*_args, **_kwargs):
        return process

    monkeypatch.setattr(project_module.asyncio, "create_subprocess_exec", create_process)
    loading = asyncio.create_task(load_project_async(tmp_path, "app:app"))
    await communicate_started.wait()

    loading.cancel()

    with pytest.raises(asyncio.CancelledError):
        await loading
    assert process.killed
    assert reaped.is_set()


@pytest.mark.asyncio
async def test_async_project_load_uses_the_injected_short_timeout(tmp_path):
    (tmp_path / "slow.py").write_text("import time\ntime.sleep(60)\napp = object()\n", encoding="utf-8")

    state = await load_project_async(tmp_path, "slow:app", timeout=0.05)

    assert state.status.mode == "syntax-only"
    assert state.status.message is not None
    assert "0.05s startup limit" in state.status.message


def test_project_worker_captures_output_and_returns_copied_registry(tmp_path):
    (tmp_path / "app.py").write_text(
        "from citry import Citry, Component, LintSettings\n"
        "print('project says hello')\n"
        "engine = Citry(\n"
        "    autodiscover=False,\n"
        "    security_csp='warn',\n"
        "    lint=LintSettings(template_variables={'request': str}),\n"
        ")\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template = '<article></article>'\n"
        "    class Kwargs:\n"
        "        title: str\n"
        "    class Lint:\n"
        "        template_variables = {'local_context': int}\n"
        "    def css_data(self, kwargs, slots):\n"
        "        return {'accent': 'red'}\n"
        "    css = '.card { color: var(--accent); }'\n",
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:engine")

    assert state.status.mode == "registry"
    assert state.status.registry_ready is True
    assert state.security_csp == "warn"
    assert state.status.message is not None
    assert "project says hello" in state.status.message
    assert state.analysis is not None
    assert "card" in state.analysis.component_names
    assert state.catalog is not None
    card = state.catalog.get("c-card")
    assert card is not None
    assert state.source_analysis is not None
    chain = state.source_analysis.template_data_chain(card)
    assert chain is not None
    assert chain[0].qualname == "Card"
    assert chain[-1].qualname == "Component"
    asset_chain = state.source_analysis.template_asset_chain(card)
    assert asset_chain is not None
    assert [candidate.qualname for candidate in asset_chain] == ["Card"]
    css_data_chain = state.source_analysis.css_data_chain(card)
    assert css_data_chain is not None
    assert [candidate.qualname for candidate in css_data_chain] == ["Card"]
    css_asset_chain = state.source_analysis.css_asset_chain(card)
    assert css_asset_chain is not None
    assert [candidate.qualname for candidate in css_asset_chain] == ["Card"]
    request = state.source_analysis.template_lint_definition(card, "request")
    assert request is not None
    assert (request.kind, request.owner, request.source_file) == ("application", "engine", tmp_path / "app.py")
    local_context = state.source_analysis.template_lint_definition(card, "local_context")
    assert local_context is not None
    assert (local_context.kind, local_context.owner, local_context.source_file) == (
        "component",
        "Card.Lint",
        tmp_path / "app.py",
    )


def test_project_worker_receives_only_the_configured_discovery_environment(tmp_path, monkeypatch):
    environment_file = tmp_path / ".env"
    environment_file.write_text("CITRY_LSP_ENV_TEST=from-file\n", encoding="utf-8")
    monkeypatch.setenv("CITRY_LSP_ENV_TEST", "from-parent")
    (tmp_path / "app.py").write_text(
        "import os\n"
        "from citry import Citry\n"
        "if os.environ.get('CITRY_LSP_ENV_TEST') != 'from-file':\n"
        "    raise RuntimeError('worker did not receive configured environment')\n"
        "engine = Citry(autodiscover=False)\n",
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:engine", environment_file=environment_file)

    assert state.status.registry_ready is True
    assert state.status.environment_file == str(environment_file)
    assert os.environ["CITRY_LSP_ENV_TEST"] == "from-parent"


@pytest.mark.asyncio
async def test_async_project_worker_receives_the_configured_discovery_environment(tmp_path):
    environment_file = tmp_path / ".env"
    environment_file.write_text("CITRY_LSP_ASYNC_ENV_TEST=available\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "import os\n"
        "from citry import Citry\n"
        "if os.environ.get('CITRY_LSP_ASYNC_ENV_TEST') != 'available':\n"
        "    raise RuntimeError('async worker did not receive configured environment')\n"
        "engine = Citry(autodiscover=False)\n",
        encoding="utf-8",
    )

    state = await load_project_async(tmp_path, "app:engine", environment_file=environment_file)

    assert state.status.registry_ready is True
    assert state.status.environment_file == str(environment_file)


def test_invalid_environment_file_degrades_without_starting_worker(tmp_path, monkeypatch):
    environment_file = tmp_path / "missing.env"
    monkeypatch.setattr("citry_lsp.project.subprocess.run", lambda *_args, **_kwargs: pytest.fail("started"))

    state = load_project(tmp_path, "app:engine", environment_file=environment_file)

    assert state.status.mode == "syntax-only"
    assert state.status.environment_file == str(environment_file)
    assert "Environment file" in (state.status.message or "")
    assert "does not exist" in (state.status.message or "")


def test_syntax_only_project_does_not_guess_a_csp_mode(tmp_path):
    state = load_project(tmp_path, None)

    assert state.status.mode == "syntax-only"
    assert state.security_csp is None


@pytest.mark.parametrize(
    "engine_settings",
    [
        None,
        {"version": 2, "security_csp": "strict"},
        {"version": 1, "security_csp": "future"},
        {"version": 1, "security_csp": "strict", "extra": True},
    ],
)
def test_engine_settings_worker_envelope_fails_closed(tmp_path, monkeypatch, engine_settings):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "settings_app.py").write_text(
        "from citry import Citry\nengine = Citry(autodiscover=False)\n",
        encoding="utf-8",
    )
    payload = app_worker._run("settings_app:engine", tmp_path)
    if engine_settings is None:
        payload.pop("engine_settings")
    else:
        payload["engine_settings"] = engine_settings

    state = project_module._project_from_worker_output(
        tmp_path,
        "settings_app:engine",
        0,
        json.dumps(payload),
        "",
    )

    assert state.status.mode == "syntax-only"
    assert "engine" in (state.status.message or "")


def test_project_worker_copies_the_checked_i18n_index(tmp_path):
    app_file = tmp_path / "app.py"
    app_file.write_text(
        dedent(
            '''
            from citry import Citry, Component
            from citry.ext.i18n import FormatRegistry, NumberFormat

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

            class Page(Component):
                citry = engine
                template = '{{ tr("account-greeting", name="Ada") }}'
                messages = """
                # @param {str} $name - User name.
                account-greeting = Welcome, { $name }.
                account-wrapper = { account-greeting }
                """
            ''',
        ),
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:engine")

    assert state.i18n is not None
    assert state.i18n.configured
    assert state.i18n.message_ids() == ("account-greeting", "account-wrapper")
    greeting = state.i18n.output("account-greeting")
    assert greeting is not None
    assert greeting.definition.path == f"{app_file}::Page.messages"
    assert [(item.name, item.type_name, item.descriptions) for item in greeting.parameters] == [
        ("name", "str", ("User name.",))
    ]
    assert state.i18n.profile_names("format", "number") == ("measurement",)
    assert state.i18n.references[0].token == "account-greeting"  # noqa: S105 - Fluent key, not a secret


def test_project_worker_indexes_component_messages_in_zero_configuration_source_mode(tmp_path):
    app_file = tmp_path / "app.py"
    app_file.write_text(
        dedent(
            """
            from citry import Citry, Component

            engine = Citry(autodiscover=False)

            class Messages(Component):
                citry = engine

                class I18n:
                    messages_locale = "en-US"

                messages = "account-title = Account"

            class Page(Component):
                citry = engine
                template = '{{ tr("account-title") }}'
            """,
        ),
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:engine")

    assert state.i18n is not None
    assert state.i18n.available
    assert not state.i18n.configured
    title = state.i18n.output("account-title")
    assert title is not None
    assert title.definition.path == f"{app_file}::Messages.messages"


def test_worker_memoizes_class_fingerprints_across_data_and_asset_channels(tmp_path, monkeypatch):
    class Card:
        pass

    source_file = tmp_path / "app.py"
    source_file.write_text("class Card:\n    pass\n", encoding="utf-8")
    calls: list[str | None] = []

    monkeypatch.setattr(app_worker, "_loaded_python_file", lambda _candidate: source_file)
    monkeypatch.setattr(app_worker, "_python_source", lambda _source_file: source_file.read_text())

    def resolution(_source: str, _qualname: str) -> str:
        calls.append(None)
        return "data-resolution"

    def asset_resolution(_source: str, _qualname: str, kind: str) -> str:
        calls.append(kind)
        return f"{kind}-resolution"

    monkeypatch.setattr(app_worker, "python_class_resolution_signature", resolution)
    monkeypatch.setattr(app_worker, "python_class_asset_resolution_signature", asset_resolution)
    app_worker._source_class_record.cache_clear()
    try:
        assert app_worker._source_class_record(Card) == app_worker._source_class_record(Card)
        assert app_worker._source_class_record(Card, asset_kind="template") == app_worker._source_class_record(
            Card,
            asset_kind="template",
        )
    finally:
        app_worker._source_class_record.cache_clear()

    assert calls == [None, "template"]


def test_project_worker_withholds_unproven_imported_asset_provenance(tmp_path):
    (tmp_path / "settings.py").write_text("CARD_TEMPLATE = 'card.html'\n", encoding="utf-8")
    (tmp_path / "card.html").write_text("{{ user }}", encoding="utf-8")
    (tmp_path / "app.py").write_text(
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

    state = load_project(tmp_path, "app:engine")

    assert state.catalog is not None
    card = state.catalog.get("c-card")
    assert card is not None
    assert state.source_analysis is not None
    assert state.source_analysis.template_asset_chain(card) is None


def test_project_worker_materializes_component_library_without_host_app_state(tmp_path):
    (tmp_path / "app.py").write_text(
        dedent(
            '''
            from citry import Citry, Component, ComponentLibrary, LibraryComponent

            print("library import output")

            host_app = Citry(autodiscover=False)

            class HostOnly(Component):
                citry = host_app
                template = """
                <aside></aside>
                """

            class DefaultOnly(Component):
                template = """
                <footer></footer>
                """

            class CCard(LibraryComponent):
                class Kwargs:
                    title: str

                class Lint:
                    template_variables = {"library_context": str}

                def template_data(self, kwargs, slots):
                    return {"title": kwargs.title}

                template = """
                <article>{{ title }}</article>
                """

            library = ComponentLibrary(
                "test-ui",
                (CCard,),
                required_extensions=("events",),
            )
            ''',
        ),
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:library")

    assert state.status.mode == "registry"
    assert state.status.registry_ready is True
    assert "library-only registry" in (state.status.message or "")
    assert "library import output" in (state.status.message or "")
    assert "host-app components, configuration, and host-provided extensions are not included" in (
        state.status.message or ""
    )
    assert state.analysis is not None
    assert "c-card" in state.analysis.component_names
    assert "provide" in state.analysis.component_names
    assert "host-only" not in state.analysis.component_names
    assert "c-host-only" not in state.analysis.component_names
    assert "default-only" not in state.analysis.component_names
    assert state.catalog is not None
    card = state.catalog.get("c-card")
    assert card is not None
    assert state.catalog.get("c-provide") is not None
    assert state.catalog.get("c-host-only") is None
    assert state.catalog.get("c-default-only") is None
    assert state.source_analysis is not None
    chain = state.source_analysis.template_data_chain(card)
    assert chain is not None
    assert [candidate.qualname for candidate in chain] == ["CCard"]
    asset_chain = state.source_analysis.template_asset_chain(card)
    assert asset_chain is not None
    assert [candidate.qualname for candidate in asset_chain] == ["CCard"]
    library_context = state.source_analysis.template_lint_definition(card, "library_context")
    assert library_context is not None
    assert (library_context.kind, library_context.owner) == ("component", "CCard.Lint")


def test_project_worker_explains_library_extensions_that_need_a_host_app(tmp_path):
    (tmp_path / "app.py").write_text(
        dedent(
            '''
            from citry import ComponentLibrary, LibraryComponent
            from citry import Citry, Extension

            class Theme(Extension):
                name = "theme"

            class CCard(LibraryComponent):
                template = """
                <article></article>
                """

            library = ComponentLibrary(
                "test-ui",
                (CCard,),
                required_extensions=("theme",),
            )

            engine = Citry(extensions=(Theme,), autodiscover=False)
            engine.register_library(library)
            ''',
        ),
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:library")

    assert state.status.mode == "syntax-only"
    assert state.status.registry_ready is False
    assert "required extension 'theme'" in (state.status.message or "")
    assert "expose a configured Citry instance" in (state.status.message or "")

    configured_state = load_project(tmp_path, "app:engine")

    assert configured_state.status.mode == "registry"
    assert configured_state.status.message is None
    assert configured_state.catalog is not None
    assert configured_state.catalog.get("c-card") is not None


def test_project_worker_rejects_targets_other_than_apps_or_libraries(tmp_path):
    (tmp_path / "app.py").write_text("target = object()\n", encoding="utf-8")

    state = load_project(tmp_path, "app:target")

    assert state.status.mode == "syntax-only"
    assert state.status.registry_ready is False
    assert "not a Citry instance or ComponentLibrary" in (state.status.message or "")


def test_project_worker_preserves_non_requirement_library_errors(tmp_path):
    (tmp_path / "app.py").write_text(
        dedent(
            '''
            from citry import ComponentLibrary, LibraryComponent

            class CBroken(LibraryComponent):
                class Cache:
                    enabled = "yes"

                template = """
                <article></article>
                """

            library = ComponentLibrary(
                "broken-ui",
                (CBroken,),
                required_extensions=("events",),
            )
            ''',
        ),
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:library")

    assert state.status.mode == "syntax-only"
    assert "component Cache enabled must be an exact bool" in (state.status.message or "")
    assert "expose a configured Citry instance" not in (state.status.message or "")


def test_project_worker_turns_system_exit_into_syntax_only_degradation(tmp_path):
    (tmp_path / "app.py").write_text("raise SystemExit(7)\n", encoding="utf-8")

    state = load_project(tmp_path, "app:engine")

    assert state.status.mode == "syntax-only"
    assert state.status.registry_ready is False
    assert state.status.message is not None
    assert "SystemExit" in state.status.message


def test_project_worker_timeout_degrades_without_hanging_server(tmp_path):
    (tmp_path / "app.py").write_text(
        "import time\ntime.sleep(10)\n",
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:engine", timeout=0.05)

    assert state.status.mode == "syntax-only"
    assert state.status.message is not None
    assert "startup limit" in state.status.message


def test_no_app_selects_reported_syntax_only_mode(tmp_path):
    state = load_project(tmp_path, None)

    assert state.status.mode == "syntax-only"
    assert state.status.app is None
    assert "No Citry app configured" in (state.status.message or "")
    assert state.status.to_dict()["mode"] == "syntax-only"
    assert state.status.python_expression_provider == "ruff@0.16.2+5b48a04097"


def test_worker_process_and_json_failures_degrade(tmp_path, monkeypatch):
    responses = [
        subprocess.CompletedProcess([], 9, stdout="", stderr="worker crashed"),
        subprocess.CompletedProcess([], 0, stdout="not json", stderr=""),
        subprocess.CompletedProcess([], 2, stdout='{"ok": false, "error": "bad app"}', stderr=""),
        subprocess.CompletedProcess([], 2, stdout="[]", stderr=""),
    ]

    def run(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr("citry_lsp.project.subprocess.run", run)

    messages = [(load_project(tmp_path, "app:engine").status.message or "") for _ in range(4)]

    assert "without a response" in messages[0]
    assert "worker crashed" in messages[0]
    assert "invalid JSON" in messages[1]
    assert "bad app" in messages[2]
    assert "status 2" in messages[3]


def test_worker_protocol_and_version_mismatches_degrade(tmp_path, monkeypatch):
    engine = Citry(autodiscover=False)
    base = {
        "ok": True,
        "target": {"kind": "citry"},
        "analysis": engine.template_analysis().to_dict(),
        "catalog": engine.inspect_components(include_builtins=True, resolve_assets=True).to_dict(),
    }
    payloads = [
        {key: value for key, value in base.items() if key != "target"},
        {**base, "target": {"kind": "future"}},
        {**base, "target": {"kind": "component-library"}},
        {**base, "target": {"kind": "component-library", "name": 7}},
        {**base, "target": {"kind": "citry", "extra": True}},
        {**base, "analysis": None},
        {**base, "analysis": {**base["analysis"], "component_lint": {}}},
        {**base, "catalog": {**base["catalog"], "citry_version": "development"}},
        {**base, "catalog": {**base["catalog"], "schema_version": 999}},
    ]

    def run(*_args, **_kwargs):
        payload = payloads.pop(0)
        return subprocess.CompletedProcess([], 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr("citry_lsp.project.subprocess.run", run)

    messages = [(load_project(tmp_path, "app:engine").status.message or "") for _ in range(9)]

    assert "target metadata must be an object" in messages[0]
    assert "target kind 'future' is unsupported" in messages[1]
    assert "name must be a non-empty string" in messages[2]
    assert "name must be a non-empty string" in messages[3]
    assert "contains unsupported fields" in messages[4]
    assert "protocol mismatch" in messages[5]
    assert "template lint component ids do not match" in messages[6]
    assert "outside this server's supported" in messages[7]
    assert "schema 999 is unsupported" in messages[8]


def test_private_source_analysis_requires_exact_catalog_coverage(tmp_path, monkeypatch):
    engine = Citry(autodiscover=False)
    raw_catalog = engine.inspect_components(include_builtins=True, resolve_assets=True).to_dict()
    catalog = CatalogIndex(raw_catalog)
    components = [
        {
            "definition_id": component.definition_id,
            "css_data": {"resolution_chain": None},
            "css_asset": {"resolution_chain": None},
            "js_data": {"resolution_chain": None},
            "js_asset": {"resolution_chain": None},
            "events": {"handlers": [], "state": []},
            "template_data": {"resolution_chain": None},
            "template_asset": {"resolution_chain": None},
            "template_lint": {"variables": []},
        }
        for component in catalog.components
    ]
    valid = {"version": 1, "components": components}

    index = SourceAnalysisIndex(valid, catalog)
    assert all(index.template_data_chain(component) is None for component in catalog.components)
    assert all(index.template_asset_chain(component) is None for component in catalog.components)
    assert all(index.state_fields(component) == () for component in catalog.components)
    with pytest.raises(ValueError, match="do not match"):
        SourceAnalysisIndex({"version": 1, "components": components[:-1]}, catalog)
    with pytest.raises(ValueError, match="duplicate"):
        SourceAnalysisIndex({"version": 1, "components": [*components, components[0]]}, catalog)
    with pytest.raises(ValueError, match="unsupported"):
        SourceAnalysisIndex({"version": 2, "components": components}, catalog)

    invalid_state = json.loads(json.dumps(valid))
    invalid_state["components"][0]["events"]["state"] = [
        {
            "name": "count",
            "type_display": "int",
            "description": None,
            "module": "app",
            "qualname": "Card.State",
            "file": "relative.py",
        }
    ]
    with pytest.raises(ValueError, match="relative State source"):
        SourceAnalysisIndex(invalid_state, catalog)

    payload = {
        "ok": True,
        "target": {"kind": "citry"},
        "analysis": engine.template_analysis().to_dict(),
        "catalog": raw_catalog,
    }
    monkeypatch.setattr(
        "citry_lsp.project.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, stdout=json.dumps(payload), stderr=""),
    )

    state = load_project(tmp_path, "app:engine")

    assert state.status.mode == "syntax-only"
    assert "source analysis envelope is invalid" in (state.status.message or "")


def test_source_analysis_declines_non_function_template_data_without_invoking_it(tmp_path):
    (tmp_path / "app.py").write_text(
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template = '{{ unknown }}'\n"
        "    template_data = property(lambda self: (_ for _ in ()).throw(RuntimeError('invoked')))\n",
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:engine")

    assert state.status.registry_ready is True
    assert state.catalog is not None
    assert state.source_analysis is not None
    card = state.catalog.get("c-card")
    assert card is not None
    assert state.source_analysis.template_data_chain(card) is None
