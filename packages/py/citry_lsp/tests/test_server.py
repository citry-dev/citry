"""End-to-end stdio protocol test for the Citry language server."""

from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_lsp
from lsprotocol import types
from pygls.exceptions import JsonRpcInvalidParams
from pytest_lsp import ClientServerConfig, LanguageClient

import citry_lsp.server as server_module
from citry_lsp.engine import BrowserProjection, CompletionResult, DocumentState, HtmlProjection, TemplateVariableHover
from citry_lsp.formatting import PreparedComponentAssets, prepare_component_assets
from citry_lsp.project import ProjectState
from citry_lsp.protocol import (
    BROWSER_PROJECTION_METHOD,
    EMBEDDED_FORMATTING_VERSION,
    FORMAT_COMPONENT_ASSETS_METHOD,
    FORMAT_EMBEDDED_METHOD,
    HTML_PROJECTION_METHOD,
    PROTOCOL_VERSION,
    EmbeddedFormattingCapability,
    ProjectStatus,
)
from citry_lsp.server import (
    CitryLanguageServer,
    _embedded_formatting_capability,
    _embedded_request_failure,
    _embedded_results,
    _format_component_assets,
    _formatting_registration_params,
    _parse_embedded_response,
    _project_reload_change,
    _register_formatting_capability,
    _snippet_plain_text,
    _workspace_path,
    _workspace_uri,
    browser_projection_request,
    html_projection_request,
)


def test_formatting_registration_uses_only_the_portable_language_filter(tmp_path):
    first_workspace = tmp_path / "first"
    second_workspace = tmp_path / "second"

    first = _formatting_registration_params(first_workspace.as_uri())
    second = _formatting_registration_params(second_workspace.as_uri())

    first_options = first.registrations[0].register_options
    second_options = second.registrations[0].register_options
    assert isinstance(first_options, types.DocumentFormattingRegistrationOptions)
    assert isinstance(second_options, types.DocumentFormattingRegistrationOptions)
    first_selector = first_options.document_selector[0]
    second_selector = second_options.document_selector[0]
    assert isinstance(first_selector, types.TextDocumentFilterLanguage)
    assert isinstance(second_selector, types.TextDocumentFilterLanguage)
    assert first_selector.language == second_selector.language == "citry-html"
    assert first_selector.scheme is second_selector.scheme is None
    assert first_selector.pattern is second_selector.pattern is None


@pytest.mark.asyncio
async def test_declined_formatting_registration_does_not_abort_initialization(tmp_path, caplog):
    register = AsyncMock(side_effect=JsonRpcInvalidParams("declined"))
    language_server = SimpleNamespace(
        workspace_uri=tmp_path.as_uri(),
        client_register_capability_async=register,
    )

    await _register_formatting_capability(language_server)

    register.assert_awaited_once()
    assert "declined dynamic formatting registration" in caplog.text


def test_workspace_uri_preserves_a_symlink_root(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "linked-workspace"
    link.symlink_to(target, target_is_directory=True)
    params = types.InitializeParams(
        capabilities=types.ClientCapabilities(),
        root_uri=link.as_uri(),
    )

    assert _workspace_uri(params) == link.as_uri()
    assert _workspace_path(params) == target.resolve()


def test_client_can_keep_standard_formatting_on_the_custom_route(tmp_path):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    formatting=types.DocumentFormattingClientCapabilities(dynamic_registration=True),
                ),
            ),
            root_uri=tmp_path.as_uri(),
            initialization_options={
                "protocolVersion": PROTOCOL_VERSION,
                "app": None,
                "standardFormatting": False,
            },
        )
    )

    assert language_server.dynamic_formatting is False


def test_environment_file_initialization_resolves_relative_to_workspace(tmp_path):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={
                "protocolVersion": PROTOCOL_VERSION,
                "app": None,
                "envFile": ".config/citry.env",
            },
        )
    )

    assert language_server.environment_file == tmp_path / ".config" / "citry.env"


@pytest.mark.parametrize("environment_file", ["", "   ", 7, False, []])
def test_environment_file_initialization_rejects_invalid_values(tmp_path, environment_file):
    language_server = CitryLanguageServer()

    with pytest.raises(JsonRpcInvalidParams, match="envFile"):
        language_server.configure(
            types.InitializeParams(
                capabilities=types.ClientCapabilities(),
                root_uri=tmp_path.as_uri(),
                initialization_options={
                    "protocolVersion": PROTOCOL_VERSION,
                    "app": None,
                    "envFile": environment_file,
                },
            )
        )


def test_project_reload_changes_include_only_python_and_the_configured_environment_file(tmp_path):
    language_server = CitryLanguageServer()
    language_server.environment_file = (tmp_path / ".env").resolve()

    assert _project_reload_change(language_server, (tmp_path / "app.py").as_uri())
    assert _project_reload_change(language_server, (tmp_path / ".env").as_uri())
    assert not _project_reload_change(language_server, (tmp_path / ".env.local").as_uri())
    assert not _project_reload_change(language_server, "untitled:settings")


def test_browser_projection_request_requires_exact_current_document_identity(monkeypatch):
    uri = "file:///card.html"
    document = DocumentState(uri, "citry-html", '<p x-text="title"></p>', 4)
    projection = BrowserProjection(
        "var title;\nvoid (title);",
        types.Position(1, 11),
        types.Range(types.Position(0, 11), types.Position(0, 16)),
        types.Range(types.Position(1, 6), types.Position(1, 11)),
        owned_root_names=("title",),
        citry_owns_position=True,
    )
    project = object()
    language_server = SimpleNamespace(documents={uri: document}, project=project)
    projected = Mock(return_value=projection)
    monkeypatch.setattr(server_module, "browser_projection", projected)

    response = browser_projection_request(
        language_server,
        {
            "textDocument": {"uri": uri, "version": 4},
            "position": {"line": 0, "character": 13},
        },
    )

    assert response == projection.to_dict()
    projected.assert_called_once_with(document, types.Position(0, 13), project, {uri: document})
    assert (
        browser_projection_request(
            language_server,
            {
                "textDocument": {"uri": uri, "version": 3},
                "position": {"line": 0, "character": 13},
            },
        )
        is None
    )
    with pytest.raises(JsonRpcInvalidParams, match="parameters"):
        browser_projection_request(language_server, {"textDocument": {"uri": uri, "version": 4}})


def test_html_projection_request_requires_exact_current_document_identity(monkeypatch):
    uri = "file:///card.html"
    document = DocumentState(uri, "citry-html", '<c-card c-body="<><input /></>" />', 4)
    projection = HtmlProjection(
        "<input />",
        types.Position(0, 3),
        types.Range(types.Position(0, 17), types.Position(0, 26)),
        types.Range(types.Position(0, 0), types.Position(0, 9)),
    )
    project = object()
    language_server = SimpleNamespace(documents={uri: document}, project=project)
    projected = Mock(return_value=projection)
    monkeypatch.setattr(server_module, "html_projection", projected)

    response = html_projection_request(
        language_server,
        {
            "textDocument": {"uri": uri, "version": 4},
            "position": {"line": 0, "character": 20},
        },
    )

    assert response == projection.to_dict()
    projected.assert_called_once_with(document, types.Position(0, 20), project)
    assert (
        html_projection_request(
            language_server,
            {
                "textDocument": {"uri": uri, "version": 3},
                "position": {"line": 0, "character": 20},
            },
        )
        is None
    )
    with pytest.raises(JsonRpcInvalidParams, match="parameters"):
        html_projection_request(language_server, {"textDocument": {"uri": uri, "version": 4}})


@pytest.mark.asyncio
async def test_catalog_reload_preserves_the_incremental_type_analyzer(tmp_path):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    previous = language_server.type_analyzer
    previous.close = AsyncMock()
    language_server.protocol.notify = Mock()

    for _ in range(5):
        await language_server.reload_project()

    previous.close.assert_not_awaited()
    assert language_server.type_analyzer is previous
    assert language_server.protocol.notify.call_count == 5


@pytest.mark.asyncio
async def test_overlapping_reloads_apply_only_the_latest_generation(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    language_server.protocol.notify = Mock()
    first_started = asyncio.Event()
    first_cancelled = asyncio.Event()
    never = asyncio.Event()
    loads = 0

    async def load(_workspace, _app, *, environment_file=None):
        assert environment_file is None
        nonlocal loads
        loads += 1
        current = loads
        if current == 1:
            first_started.set()
            try:
                await never.wait()
            except asyncio.CancelledError:
                first_cancelled.set()
                raise
        return ProjectState(
            ProjectStatus(
                interpreter=sys.executable,
                workspace=str(tmp_path),
                mode="syntax-only",
                message=f"generation {current}",
            )
        )

    monkeypatch.setattr(server_module, "load_project_async", load)
    first = asyncio.create_task(language_server.reload_project())
    await first_started.wait()
    second = asyncio.create_task(language_server.reload_project())

    first_result, second_result = await asyncio.gather(first, second)

    assert loads == 2
    assert first_cancelled.is_set()
    assert first_result["message"] == "generation 2"
    assert second_result["message"] == "generation 2"
    assert language_server.project.status.message == "generation 2"
    language_server.protocol.notify.assert_called_once()


@pytest.mark.asyncio
async def test_watched_reload_burst_coalesces_to_one_worker_load(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": "app:app"},
        )
    )
    language_server.protocol.notify = Mock()
    loads = 0

    async def load(_workspace, _app, *, environment_file=None):
        assert environment_file is None
        nonlocal loads
        loads += 1
        return ProjectState(
            ProjectStatus(
                interpreter=sys.executable,
                workspace=str(tmp_path),
                mode="syntax-only",
                message="coalesced",
            )
        )

    monkeypatch.setattr(server_module, "load_project_async", load)
    requests = [asyncio.create_task(language_server.reload_project(debounce=0.01)) for _ in range(3)]

    results = await asyncio.gather(*requests)

    assert loads == 1
    assert {result["message"] for result in results} == {"coalesced"}


@pytest.mark.asyncio
@pytest.mark.parametrize("race", ["unchanged", "edit", "open", "close"])
async def test_project_snapshot_apply_never_overwrites_or_resurrects_concurrent_documents(tmp_path, race):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    language_server.protocol.notify = Mock()
    language_server.text_document_publish_diagnostics = Mock()
    uri = (tmp_path / "card.citry-html").as_uri()
    original = DocumentState(uri, "citry-html", "{{ old }}", 1)
    original.update(original.source, original.version, language_server.project)
    language_server.documents[uri] = original
    project = ProjectState(
        ProjectStatus(
            interpreter=sys.executable,
            workspace=str(tmp_path),
            mode="syntax-only",
            message="replacement",
        )
    )
    prepared = await language_server._prepare_project_documents(project)
    opened_uri = (tmp_path / "opened.citry-html").as_uri()

    if race == "edit":
        language_server.update_document(uri, "citry-html", "{{ new }}", 2)
    elif race == "open":
        language_server.update_document(opened_uri, "citry-html", "{{ opened }}", 1)
    elif race == "close":
        language_server.documents.pop(uri)

    language_server._apply_project(project, 1, prepared)

    if race == "unchanged":
        assert language_server.documents[uri] is not original
        assert language_server.documents[uri].source == "{{ old }}"
    elif race == "edit":
        assert language_server.documents[uri] is original
        assert language_server.documents[uri].source == "{{ new }}"
        assert language_server.documents[uri].version == 2
    elif race == "open":
        assert language_server.documents[uri] is not original
        assert language_server.documents[opened_uri].source == "{{ opened }}"
    else:
        assert uri not in language_server.documents
    await language_server.close()


@pytest.mark.asyncio
async def test_shutdown_cancels_reload_and_reaps_the_existing_analyzer(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": "app:app"},
        )
    )
    load_started = asyncio.Event()
    load_cancelled = asyncio.Event()
    never = asyncio.Event()

    async def load(_workspace, _app, *, environment_file=None):
        assert environment_file is None
        load_started.set()
        try:
            await never.wait()
        except asyncio.CancelledError:
            load_cancelled.set()
            raise

    monkeypatch.setattr(server_module, "load_project_async", load)
    language_server.type_analyzer.close = AsyncMock()
    reloading = asyncio.create_task(language_server.reload_project())
    await load_started.wait()

    await language_server.close()

    with pytest.raises(asyncio.CancelledError):
        await reloading
    assert load_cancelled.is_set()
    language_server.type_analyzer.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancelled_shutdown_finishes_analyzer_cleanup_before_propagating(tmp_path):
    language_server = CitryLanguageServer()
    close_started = asyncio.Event()
    release_close = asyncio.Event()

    async def close_analyzer():
        close_started.set()
        await release_close.wait()

    language_server.type_analyzer.close = AsyncMock(side_effect=close_analyzer)
    closing = asyncio.create_task(language_server.close())
    await close_started.wait()

    closing.cancel()
    await asyncio.sleep(0)
    assert not closing.done()
    release_close.set()

    with pytest.raises(asyncio.CancelledError):
        await closing
    language_server.type_analyzer.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_python_change_refreshes_semantic_diagnostics_for_open_templates(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    python_uri = (tmp_path / "app.py").as_uri()
    template_uri = (tmp_path / "card.citry-html").as_uri()
    language_server.update_document(python_uri, "python", "value = 1\n", 1)
    language_server.update_document(template_uri, "citry-html", "<div></div>", 1)
    semantic = AsyncMock(return_value=())
    monkeypatch.setattr(server_module, "semantic_diagnostics", semantic)
    language_server.text_document_publish_diagnostics = Mock()

    await server_module.did_change(
        language_server,
        types.DidChangeTextDocumentParams(
            types.VersionedTextDocumentIdentifier(2, python_uri),
            [types.TextDocumentContentChangeWholeDocument("value = 2\n")],
        ),
    )
    await language_server.wait_for_semantic_refresh()

    assert semantic.await_count == 2
    assert {call.args[1].uri for call in semantic.await_args_list} == {python_uri, template_uri}


@pytest.mark.asyncio
async def test_new_document_generation_cancels_stale_semantic_diagnostics(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    uri = (tmp_path / "card.citry-html").as_uri()
    language_server.update_document(uri, "citry-html", "{{ first }}", 1)
    language_server.text_document_publish_diagnostics = Mock()
    first_started = asyncio.Event()
    first_cancelled = asyncio.Event()
    release_first = asyncio.Event()
    calls = 0

    async def semantic(*_args):
        nonlocal calls
        calls += 1
        if calls == 1:
            first_started.set()
            try:
                await release_first.wait()
            except asyncio.CancelledError:
                first_cancelled.set()
                raise
        return ()

    monkeypatch.setattr(server_module, "semantic_diagnostics", semantic)
    monkeypatch.setattr(server_module, "_SEMANTIC_DIAGNOSTIC_DEBOUNCE_SECONDS", 0.01)
    language_server.schedule_semantic_dependents(language_server.documents[uri])
    await first_started.wait()

    language_server.update_document(uri, "citry-html", "{{ second }}", 2)
    language_server.schedule_semantic_dependents(language_server.documents[uri])
    await language_server.wait_for_semantic_refresh()

    assert first_cancelled.is_set()
    assert calls == 2


@pytest.mark.asyncio
async def test_interactive_completion_preempts_and_reschedules_background_diagnostics(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    uri = (tmp_path / "card.citry-html").as_uri()
    language_server.update_document(uri, "citry-html", "{{ value }}", 1)
    language_server.text_document_publish_diagnostics = Mock()
    diagnostic_started = asyncio.Event()
    diagnostic_cancelled = asyncio.Event()
    never = asyncio.Event()
    diagnostic_calls = 0

    async def diagnostics(*_args):
        nonlocal diagnostic_calls
        diagnostic_calls += 1
        if diagnostic_calls == 1:
            diagnostic_started.set()
            try:
                await never.wait()
            except asyncio.CancelledError:
                diagnostic_cancelled.set()
                raise
        return ()

    async def complete(*_args):
        assert diagnostic_cancelled.is_set()
        return (types.CompletionItem("value"),)

    monkeypatch.setattr(server_module, "semantic_diagnostics", diagnostics)
    monkeypatch.setattr(server_module, "semantic_completions", complete)
    monkeypatch.setattr(
        server_module,
        "completion_result",
        lambda *_args: CompletionResult(()),
    )
    monkeypatch.setattr(server_module, "_SEMANTIC_DIAGNOSTIC_DEBOUNCE_SECONDS", 0.01)
    language_server.schedule_semantic_dependents(language_server.documents[uri])
    await diagnostic_started.wait()

    result = await server_module.completion(
        language_server,
        types.CompletionParams(types.TextDocumentIdentifier(uri), types.Position(0, 5)),
    )
    await language_server.wait_for_semantic_refresh()

    assert [item.label for item in result.items] == ["value"]
    assert diagnostic_cancelled.is_set()
    assert diagnostic_calls == 2


@pytest.mark.asyncio
async def test_cancelled_interactive_drain_does_not_create_or_leak_the_operation() -> None:
    language_server = CitryLanguageServer()
    background_started = asyncio.Event()
    cleanup_started = asyncio.Event()
    release_cleanup = asyncio.Event()
    never = asyncio.Event()
    operations_created = 0

    async def background():
        background_started.set()
        try:
            await never.wait()
        finally:
            cleanup_started.set()
            await asyncio.shield(release_cleanup.wait())

    async def operation():
        return "unreachable"

    def operation_factory():
        nonlocal operations_created
        operations_created += 1
        return operation()

    semantic = asyncio.create_task(background())
    language_server._semantic_task = semantic
    await background_started.wait()
    interactive = asyncio.create_task(language_server.run_interactive(operation_factory))
    await cleanup_started.wait()

    interactive.cancel()
    with pytest.raises(asyncio.CancelledError):
        await interactive
    release_cleanup.set()
    await asyncio.gather(semantic, return_exceptions=True)

    assert operations_created == 0
    assert language_server._interactive_requests == 0


@pytest.mark.asyncio
async def test_python_change_prioritizes_direct_semantic_dependents_and_skips_proven_unrelated(
    tmp_path,
    monkeypatch,
):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    python_uri = (tmp_path / "models.py").as_uri()
    fallback_uri = (tmp_path / "fallback.citry-html").as_uri()
    direct_uri = (tmp_path / "direct.citry-html").as_uri()
    unrelated_uri = (tmp_path / "unrelated.citry-html").as_uri()
    for uri, language_id, source in (
        (python_uri, "python", "value = 1\n"),
        (fallback_uri, "citry-html", "{{ fallback }}"),
        (direct_uri, "citry-html", "{{ direct }}"),
        (unrelated_uri, "citry-html", "{{ unrelated }}"),
    ):
        language_server.update_document(uri, language_id, source, 1)
    language_server.text_document_publish_diagnostics = Mock()
    order: list[str] = []

    async def diagnostics(_analyzer, document, *_args):
        order.append(document.uri)
        return ()

    def dependencies(document, *_args):
        if document.uri == direct_uri:
            return SimpleNamespace(source_uris=frozenset({python_uri}), complete=True)
        if document.uri == fallback_uri:
            return SimpleNamespace(source_uris=frozenset(), complete=False)
        return SimpleNamespace(source_uris=frozenset(), complete=True)

    monkeypatch.setattr(server_module, "semantic_diagnostics", diagnostics)
    monkeypatch.setattr(server_module, "semantic_dependencies", dependencies)

    await language_server.publish_semantic_dependents(language_server.documents[python_uri])

    assert order == [python_uri, direct_uri, fallback_uri]


@pytest.mark.asyncio
async def test_semantic_handlers_drop_results_after_any_document_change(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    source = "{{ value }}"
    uri = (tmp_path / "card.citry-html").as_uri()
    language_server.text_document_publish_diagnostics = Mock()
    language_server.update_document(uri, "citry-html", source, 1)
    position = types.Position(0, 5)
    version = 1

    async def stale(value):
        nonlocal version
        version += 1
        language_server.update_document(uri, "citry-html", source, version)
        return value

    monkeypatch.setattr(
        server_module,
        "completion_result",
        lambda *_args: SimpleNamespace(items=(), is_incomplete=False),
    )
    monkeypatch.setattr(
        server_module,
        "semantic_completions",
        lambda *_args: stale((types.CompletionItem("value"),)),
    )
    completed = await server_module.completion(
        language_server,
        types.CompletionParams(types.TextDocumentIdentifier(uri), position),
    )

    monkeypatch.setattr(server_module, "hover", lambda *_args: None)
    monkeypatch.setattr(
        server_module,
        "semantic_hover",
        lambda *_args: stale(types.Hover(types.MarkupContent(types.MarkupKind.Markdown, "value"))),
    )
    hovered = await server_module.hover_feature(
        language_server,
        types.HoverParams(types.TextDocumentIdentifier(uri), position),
    )

    monkeypatch.setattr(server_module, "definition", lambda *_args: None)
    monkeypatch.setattr(
        server_module,
        "semantic_definition",
        lambda *_args: stale((types.Location(uri, types.Range(position, position)),)),
    )
    defined = await server_module.definition_feature(
        language_server,
        types.DefinitionParams(types.TextDocumentIdentifier(uri), position),
    )

    monkeypatch.setattr(
        server_module,
        "semantic_type_definition",
        lambda *_args: stale((types.Location(uri, types.Range(position, position)),)),
    )
    typed = await server_module.type_definition_feature(
        language_server,
        types.TypeDefinitionParams(types.TextDocumentIdentifier(uri), position),
    )

    monkeypatch.setattr(
        server_module,
        "semantic_signature_help",
        lambda *_args: stale(types.SignatureHelp([types.SignatureInformation("value()")])),
    )
    signed = await server_module.signature_help_feature(
        language_server,
        types.SignatureHelpParams(types.TextDocumentIdentifier(uri), position),
    )

    assert not completed.items
    assert hovered is None
    assert defined is None
    assert typed is None
    assert signed is None


@pytest.mark.asyncio
async def test_reference_and_declaration_handlers_forward_variable_context(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    source = "{{ value }}"
    uri = (tmp_path / "card.citry-html").as_uri()
    language_server.text_document_publish_diagnostics = Mock()
    language_server.update_document(uri, "citry-html", source, 1)
    position = types.Position(0, 5)
    location = types.Location(uri, types.Range(position, position))
    reference = Mock(return_value=[location])
    declared = Mock(return_value=location)
    monkeypatch.setattr(server_module, "references", reference)
    monkeypatch.setattr(server_module, "declaration", declared)

    found = await server_module.references_feature(
        language_server,
        types.ReferenceParams(
            text_document=types.TextDocumentIdentifier(uri),
            position=position,
            context=types.ReferenceContext(include_declaration=True),
        ),
    )
    target = await server_module.declaration_feature(
        language_server,
        types.DeclarationParams(types.TextDocumentIdentifier(uri), position),
    )

    assert found == [location]
    assert target == location
    assert reference.call_args.kwargs == {"include_declaration": True}
    declared.assert_called_once()


@pytest.mark.asyncio
async def test_variable_hover_composes_semantics_before_the_engine_fallback(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    source = "{{ value }}"
    uri = (tmp_path / "card.citry-html").as_uri()
    language_server.text_document_publish_diagnostics = Mock()
    language_server.update_document(uri, "citry-html", source, 1)
    position = types.Position(0, 5)
    token_range = types.Range(types.Position(0, 3), types.Position(0, 8))
    variable = TemplateVariableHover("value", token_range, "TemplateData field · required", fallback_types=("str",))
    expected = types.Hover(
        types.MarkupContent(
            types.MarkupKind.Markdown,
            "```python\n(variable) value: Literal['ready']\n```\n\nTemplateData field · required",
        ),
        token_range,
    )
    semantic = AsyncMock(return_value=expected)
    monkeypatch.setattr(server_module, "template_variable_hover", lambda *_args: variable)
    monkeypatch.setattr(server_module, "semantic_variable_hover", semantic)
    base_hover = Mock(side_effect=AssertionError("variable hover must use semantics before its fallback"))
    monkeypatch.setattr(server_module, "hover", base_hover)

    result = await server_module.hover_feature(
        language_server,
        types.HoverParams(types.TextDocumentIdentifier(uri), position),
    )

    assert result == expected
    semantic.assert_awaited_once()
    base_hover.assert_not_called()


@pytest.mark.asyncio
async def test_variable_hover_drops_a_fallback_built_before_a_document_change(tmp_path, monkeypatch):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    source = "{{ value }}"
    uri = (tmp_path / "card.citry-html").as_uri()
    language_server.text_document_publish_diagnostics = Mock()
    language_server.update_document(uri, "citry-html", source, 1)
    position = types.Position(0, 5)
    variable = TemplateVariableHover(
        "value",
        types.Range(types.Position(0, 3), types.Position(0, 8)),
        "TemplateData field · required",
        fallback_types=("str",),
    )

    async def stale(*_args):
        language_server.update_document(uri, "citry-html", source, 2)
        return types.Hover(types.MarkupContent(types.MarkupKind.Markdown, "fallback"))

    monkeypatch.setattr(server_module, "template_variable_hover", lambda *_args: variable)
    monkeypatch.setattr(server_module, "semantic_variable_hover", stale)

    result = await server_module.hover_feature(
        language_server,
        types.HoverParams(types.TextDocumentIdentifier(uri), position),
    )

    assert result is None


@pytest.mark.asyncio
async def test_expression_completion_downgrades_edits_for_older_clients(tmp_path):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    source = '<div c-for="item in items">{{ item }}</div>'
    uri = (tmp_path / "card.citry-html").as_uri()
    document = DocumentState(uri, "citry-html", source, 1)
    document.update(source, 1, language_server.project)
    language_server.documents[uri] = document
    item_start = source.rindex("item")
    cursor = types.Position(0, item_start + len("it"))

    result = await server_module.completion(
        language_server,
        types.CompletionParams(types.TextDocumentIdentifier(uri), cursor),
    )

    assert language_server.completion_insert_replace is False
    assert result.is_incomplete is True
    item = next(candidate for candidate in result.items if candidate.label == "item")
    assert item.text_edit == types.TextEdit(
        types.Range(types.Position(0, item_start), types.Position(0, item_start + len("item"))),
        "item",
    )


@pytest.mark.asyncio
async def test_structural_tag_completion_downgrades_snippets_for_older_clients(tmp_path):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    source = "<c-"
    uri = (tmp_path / "card.citry-html").as_uri()
    document = DocumentState(uri, "citry-html", source, 1)
    document.update(source, 1, language_server.project)
    language_server.documents[uri] = document

    result = await server_module.completion(
        language_server,
        types.CompletionParams(types.TextDocumentIdentifier(uri), types.Position(0, len(source))),
    )

    item = next(candidate for candidate in result.items if candidate.label == "c-for")
    assert item.insert_text_format == types.InsertTextFormat.PlainText
    assert item.insert_text == 'c-for each="">'
    assert item.text_edit == types.TextEdit(
        types.Range(types.Position(0, 1), types.Position(0, len(source))),
        'c-for each="">',
    )


@pytest.mark.asyncio
async def test_attribute_completion_downgrades_atomic_edits_for_older_clients(tmp_path):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None},
        )
    )
    source = "<div c-ioops>"
    uri = (tmp_path / "card.citry-html").as_uri()
    document = DocumentState(uri, "citry-html", source, 1)
    document.update(source, 1, language_server.project)
    language_server.documents[uri] = document
    cursor = types.Position(0, source.index("c-ioops") + len("c-i"))

    result = await server_module.completion(
        language_server,
        types.CompletionParams(types.TextDocumentIdentifier(uri), cursor),
    )

    assert result.is_incomplete is True
    item = next(candidate for candidate in result.items if candidate.label == "c-if")
    assert item.insert_text_format == types.InsertTextFormat.PlainText
    assert item.insert_text == 'c-if="condition"'
    assert item.text_edit == types.TextEdit(
        types.Range(
            types.Position(0, source.index("c-ioops")),
            types.Position(0, source.index("c-ioops") + len("c-ioops")),
        ),
        'c-if="condition"',
    )


@pytest.mark.parametrize(
    ("snippet", "expected"),
    [
        ('c-for="${1:item} in ${2:items}"', 'c-for="item in items"'),
        ('\\$c-props="${1:{}}"', '$c-props="{}"'),
        ('c-if="${1}"', 'c-if=""'),
    ],
)
def test_plain_completion_text_resolves_supported_snippet_forms(snippet, expected):
    assert _snippet_plain_text(snippet) == expected


def test_embedded_capability_is_additive_to_protocol_v1(tmp_path):
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={
                "protocolVersion": 1,
                "embeddedFormatting": {
                    "version": EMBEDDED_FORMATTING_VERSION,
                    "languages": ["javascript", "css"],
                    "providerSelection": "vscode-first-result",
                },
            },
        )
    )

    assert PROTOCOL_VERSION == 1
    assert language_server.embedded_formatting is not None
    assert language_server.embedded_formatting.languages == ("javascript", "css")
    status = language_server.project.status.to_dict()
    assert status["embedded_formatting"] == {
        "version": 1,
        "languages": ("javascript", "css"),
        "provider_selection": "vscode-first-result",
        "provider_identity": None,
        "provider_version": None,
    }


def test_boolean_protocol_version_is_rejected(tmp_path) -> None:
    language_server = CitryLanguageServer()

    with pytest.raises(JsonRpcInvalidParams, match="protocol"):
        language_server.configure(
            types.InitializeParams(
                capabilities=types.ClientCapabilities(),
                root_uri=tmp_path.as_uri(),
                initialization_options={"protocolVersion": True},
            )
        )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ({"version": 2, "languages": [], "providerSelection": "vscode-first-result"}, "version"),
        ({"version": 1, "languages": "javascript", "providerSelection": "vscode-first-result"}, "languages"),
        ({"version": 1, "languages": ["html"], "providerSelection": "vscode-first-result"}, "languages"),
        ({"version": 1, "languages": [], "providerSelection": "default-formatter"}, "providerSelection"),
    ],
)
def test_invalid_embedded_capability_is_rejected(value, message):
    with pytest.raises(JsonRpcInvalidParams, match=message):
        _embedded_formatting_capability({"embeddedFormatting": value})


def test_embedded_response_requires_exact_echoed_identity():
    with pytest.raises(ValueError, match="document version"):
        _parse_embedded_response(
            {
                "version": 1,
                "textDocument": {"uri": "file:///card.py", "version": 8},
                "planId": "plan",
                "providerSelection": "vscode-first-result",
                "results": [],
            },
            uri="file:///card.py",
            document_version=7,
            plan_id="plan",
            expected_region_ids=(),
            provider_selection="vscode-first-result",
        )


def test_embedded_response_validates_result_cardinality_and_payloads():
    base = {
        "version": 1,
        "textDocument": {"uri": "file:///card.py", "version": 7},
        "planId": "plan",
        "providerSelection": "vscode-first-result",
    }
    cases = [
        ({**base, "results": []}, "result count"),
        (
            {
                **base,
                "results": [
                    {"planId": "wrong", "regionId": "region", "status": "unchanged"},
                ],
            },
            "unknown plan or region",
        ),
        (
            {
                **base,
                "results": [
                    {"planId": "plan", "regionId": "region", "status": "mystery"},
                ],
            },
            "unknown status",
        ),
        (
            {
                **base,
                "version": True,
                "results": [
                    {"planId": "plan", "regionId": "region", "status": "unchanged"},
                ],
            },
            "unsupported version",
        ),
        (
            {
                **base,
                "textDocument": {"uri": "file:///card.py", "version": True},
                "results": [
                    {"planId": "plan", "regionId": "region", "status": "unchanged"},
                ],
            },
            "document version",
        ),
        (
            {
                **base,
                "results": [
                    {
                        "planId": "plan",
                        "regionId": "region",
                        "status": "formatted",
                        "text": "const answer = 42;\n",
                        "message": "contradiction",
                    },
                ],
            },
            "require text",
        ),
        (
            {
                **base,
                "results": [
                    {
                        "planId": "plan",
                        "regionId": "region",
                        "status": "formatted",
                        "text": "const answer = 42;\n",
                        "provider": "forged@1",
                    },
                ],
            },
            "cannot claim a provider identity",
        ),
    ]
    for response, message in cases:
        with pytest.raises(ValueError, match=message):
            _parse_embedded_response(
                response,
                uri="file:///card.py",
                document_version=7,
                plan_id="plan",
                expected_region_ids=("region",),
                provider_selection="vscode-first-result",
            )


def test_embedded_response_accepts_unknown_provider_identity() -> None:
    results = _parse_embedded_response(
        {
            "version": 1,
            "textDocument": {"uri": "file:///card.py", "version": 7},
            "planId": "plan",
            "providerSelection": "vscode-first-result",
            "results": [
                {
                    "planId": "plan",
                    "regionId": "region",
                    "status": "formatted",
                    "text": "const answer = 42;\n",
                    "provider": None,
                }
            ],
        },
        uri="file:///card.py",
        document_version=7,
        plan_id="plan",
        expected_region_ids=("region",),
        provider_selection="vscode-first-result",
    )

    assert len(results) == 1
    assert results[0].provider is None


def test_client_stale_error_stays_a_stale_document_refusal() -> None:
    response = _embedded_request_failure(RuntimeError("citry.format.stale-document: changed"))

    assert response["kind"] == "refused"
    assert response["code"] == "citry.format.stale-document"


@pytest.mark.asyncio
async def test_embedded_client_request_times_out_as_structured_failure(tmp_path, monkeypatch) -> None:
    source = "<script>const value = 1;</script>"
    uri = (tmp_path / "card.citry-html").as_uri()
    document = DocumentState(uri, "citry-html", source, 3)
    prepared = prepare_component_assets(document, requested_version=3, scope="document")
    assert isinstance(prepared, PreparedComponentAssets)

    pending: asyncio.Future[object] = asyncio.get_running_loop().create_future()
    requests: list[tuple[str, object, str]] = []
    notifications: list[tuple[str, object]] = []

    class Protocol:
        def send_request_async(self, method: str, params: object, *, msg_id: str) -> asyncio.Future[object]:
            requests.append((method, params, msg_id))
            return pending

        def notify(self, method: str, params: object) -> None:
            notifications.append((method, params))

    language_server = SimpleNamespace(
        embedded_formatting=EmbeddedFormattingCapability(
            version=1,
            languages=("javascript", "css"),
            provider_selection="vscode-first-result",
        ),
        documents={uri: document},
        protocol=Protocol(),
    )
    monkeypatch.setattr(server_module, "_EMBEDDED_REQUEST_TIMEOUT_SECONDS", 0.01)

    response = await _embedded_results(language_server, prepared)

    assert response["kind"] == "refused"
    assert response["code"] == "citry.format.provider-invalid"
    assert "TimeoutError" in response["message"]
    assert len(requests) == 1
    assert notifications == [
        (types.CANCEL_REQUEST, types.CancelParams(id=requests[0][2])),
    ]
    pending.cancel()


@pytest.mark.asyncio
async def test_synchronous_embedded_client_send_failure_is_structured(tmp_path) -> None:
    source = "<script>const value = 1;</script>"
    uri = (tmp_path / "card.citry-html").as_uri()
    document = DocumentState(uri, "citry-html", source, 3)
    prepared = prepare_component_assets(document, requested_version=3, scope="document")
    assert isinstance(prepared, PreparedComponentAssets)

    class Protocol:
        def send_request_async(self, method: str, params: object, *, msg_id: str) -> object:
            raise RuntimeError(f"send failed for {method} {msg_id}")

    language_server = SimpleNamespace(
        embedded_formatting=EmbeddedFormattingCapability(
            version=1,
            languages=("javascript", "css"),
            provider_selection="vscode-first-result",
        ),
        documents={uri: document},
        protocol=Protocol(),
    )

    response = await _embedded_results(language_server, prepared)

    assert response["kind"] == "refused"
    assert response["code"] == "citry.format.provider-invalid"
    assert "send failed" in response["message"]


@pytest.mark.asyncio
async def test_client_without_embedded_capability_gets_outer_formatting_and_notices(tmp_path) -> None:
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": 1},
        )
    )
    source = "<main  ><script>const  answer=1;</script></main>"
    uri = (tmp_path / "card.citry-html").as_uri()
    document = DocumentState(uri, "citry-html", source, 3)
    document.update(source, 3, language_server.project)
    language_server.documents[uri] = document

    response = await _format_component_assets(language_server, uri, 3, "document", None)

    assert response["kind"] == "edit"
    assert response["providers"] == []
    assert response["notices"] == [
        {
            "code": "citry.format.provider-unavailable",
            "message": "the client does not offer javascript embedded formatting",
            "regionId": "script-body-0",
            "language": "javascript",
        }
    ]
    assert response["embeddedFormatting"] == {
        "version": 1,
        "languages": [],
        "providerSelection": None,
        "providerIdentity": None,
        "providerVersion": None,
    }


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "-m", "citry_lsp"]),
)
async def lsp_client(client: LanguageClient, tmp_path):
    (tmp_path / "app.py").write_text(
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        '    template = \'<article class="card" c-title="title"></article>\'\n'
        "    class Kwargs:\n"
        "        title: str\n"
        "    class TemplateData:\n"
        "        title: str\n"
        "        subtitle: str\n"
        'engine.register(Card, name="ui.card")\n',
        encoding="utf-8",
    )
    statuses: list[object] = []

    @client.feature("citry/status")
    def receive_status(_client: LanguageClient, params: object) -> None:
        statuses.append(params)

    @client.feature(types.CLIENT_REGISTER_CAPABILITY)
    def register_capability(_client: LanguageClient, _params: types.RegistrationParams) -> None:
        return None

    @client.feature(FORMAT_EMBEDDED_METHOD)
    def format_embedded(_client: LanguageClient, params: object) -> dict[str, object]:
        regions = params.regions
        results = []
        for region in regions:
            text = region.virtualSource
            if region.language == "javascript":
                text = text.replace("const  ", "const ").replace("=1", " = 1")
            else:
                text = text.replace(".card{color:red}", ".card {\n  color: red;\n}")
            results.append(
                {
                    "planId": params.planId,
                    "regionId": region.id,
                    "status": "formatted",
                    "text": text,
                    "provider": None,
                }
            )
        return {
            "version": 1,
            "textDocument": {
                "uri": params.textDocument.uri,
                "version": params.textDocument.version,
            },
            "planId": params.planId,
            "providerSelection": "vscode-first-result",
            "results": results,
        }

    initialize_result = await client.initialize_session(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    formatting=types.DocumentFormattingClientCapabilities(dynamic_registration=True),
                    completion=types.CompletionClientCapabilities(
                        completion_item=types.ClientCompletionItemOptions(
                            insert_replace_support=True,
                            documentation_format=[types.MarkupKind.Markdown],
                        ),
                    ),
                ),
            ),
            root_uri=tmp_path.as_uri(),
            initialization_options={
                "protocolVersion": PROTOCOL_VERSION,
                "app": "app:engine",
                "embeddedFormatting": {
                    "version": 1,
                    "languages": ["javascript", "css"],
                    "providerSelection": "vscode-first-result",
                },
            },
        )
    )
    assert initialize_result.capabilities.document_formatting_provider is None
    assert initialize_result.capabilities.completion_provider is not None
    completion_triggers = set(initialize_result.capabilities.completion_provider.trigger_characters or ())
    assert {"-", "."} <= completion_triggers
    assert not completion_triggers.intersection("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
    assert initialize_result.capabilities.signature_help_provider is not None
    assert set(initialize_result.capabilities.signature_help_provider.trigger_characters or ()) == {"(", ","}
    assert initialize_result.capabilities.references_provider is not None
    assert initialize_result.capabilities.declaration_provider is not None
    assert initialize_result.capabilities.type_definition_provider is not None
    yield
    await client.shutdown_session()


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "-m", "citry_lsp"]),
)
async def syntax_lsp_client(client: LanguageClient, tmp_path):
    @client.feature("citry/status")
    def receive_status(_client: LanguageClient, _params: object) -> None:
        return None

    await client.initialize_session(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(
                text_document=types.TextDocumentClientCapabilities(
                    completion=types.CompletionClientCapabilities(
                        completion_item=types.ClientCompletionItemOptions(
                            snippet_support=True,
                            insert_replace_support=True,
                        ),
                    ),
                ),
            ),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": 1, "app": None},
        )
    )
    yield
    await client.shutdown_session()


@pytest.mark.asyncio
async def test_stdio_diagnostics_and_completion(lsp_client: LanguageClient, tmp_path):
    source = '<c-card title="Hi"><div></c-card>'
    uri = (tmp_path / "template.html").as_uri()
    notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )

    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "citry-html", 1, source))
    )
    await notification

    assert uri in lsp_client.diagnostics
    assert lsp_client.diagnostics[uri][0].code == "citry.parse.syntax"
    status = await lsp_client.protocol.send_request_async("citry/status")
    assert status.mode == "registry", status.message
    assert status.protocol_version == PROTOCOL_VERSION
    completion = await lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(uri),
            types.Position(0, len(source.encode("utf-16-le")) // 2),
        )
    )
    assert isinstance(completion, types.CompletionList)


@pytest.mark.asyncio
async def test_stdio_expression_completion_is_incremental_and_carries_edit_ranges(
    lsp_client: LanguageClient,
    tmp_path,
):
    source_path = tmp_path / "app.py"
    original = source_path.read_text(encoding="utf-8")
    source = original.replace('c-title="title"', 'c-title=""')
    uri = source_path.as_uri()
    notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "python", 1, source))
    )
    await notification
    cursor_offset = source.index('c-title=""') + len('c-title="')
    before = source[:cursor_offset]
    cursor = types.Position(
        before.count("\n"),
        len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2,
    )

    completion = await lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(uri),
            cursor,
            context=types.CompletionContext(
                types.CompletionTriggerKind.TriggerCharacter,
                '"',
            ),
        )
    )

    assert isinstance(completion, types.CompletionList)
    assert completion.is_incomplete is True
    assert {item.label for item in completion.items} == {"title", "subtitle"}
    for item in completion.items:
        assert item.filter_text == item.label
        assert isinstance(item.text_edit, types.InsertReplaceEdit)
        assert item.text_edit.insert == types.Range(cursor, cursor)
        assert item.text_edit.replace == types.Range(cursor, cursor)

    updated_source = source.replace('c-title=""', 'c-title="t"')
    updated_notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    lsp_client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            types.VersionedTextDocumentIdentifier(2, uri),
            [types.TextDocumentContentChangeWholeDocument(updated_source)],
        )
    )
    await updated_notification
    updated_cursor = types.Position(cursor.line, cursor.character + 1)

    updated_completion = await lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(uri),
            updated_cursor,
            context=types.CompletionContext(
                types.CompletionTriggerKind.TriggerForIncompleteCompletions,
            ),
        )
    )

    assert isinstance(updated_completion, types.CompletionList)
    assert updated_completion.is_incomplete is True
    assert {item.label for item in updated_completion.items} == {"title", "subtitle"}
    for item in updated_completion.items:
        assert isinstance(item.text_edit, types.InsertReplaceEdit)
        assert item.text_edit.insert == types.Range(cursor, updated_cursor)
        assert item.text_edit.replace == types.Range(cursor, updated_cursor)


@pytest.mark.asyncio
async def test_stdio_expression_member_completion_uses_declared_python_type(
    lsp_client: LanguageClient,
    tmp_path,
) -> None:
    source_path = tmp_path / "app.py"
    source = source_path.read_text(encoding="utf-8").replace('c-title="title"', 'c-title="title."')
    uri = source_path.as_uri()
    notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "python", 1, source))
    )
    await notification
    cursor_offset = source.index('c-title="title."') + len('c-title="title.')
    before = source[:cursor_offset]
    cursor = types.Position(
        before.count("\n"),
        len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2,
    )

    completion = await lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(uri),
            cursor,
            context=types.CompletionContext(types.CompletionTriggerKind.TriggerCharacter, "."),
        )
    )

    assert isinstance(completion, types.CompletionList)
    by_label = {item.label: item for item in completion.items}
    assert "lower" in by_label
    assert by_label["lower"].detail == "bound method str.lower() -> str"
    assert "format" not in by_label
    assert not any(label.startswith("_") for label in by_label)


@pytest.mark.asyncio
async def test_stdio_expression_member_diagnostics_are_mapped_to_python_template(
    lsp_client: LanguageClient,
    tmp_path,
) -> None:
    source_path = tmp_path / "app.py"
    source = source_path.read_text(encoding="utf-8").replace(
        'c-title="title"',
        'c-title="title.missing"',
    )
    uri = source_path.as_uri()
    notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "python", 1, source))
    )
    await notification

    deadline = asyncio.get_running_loop().time() + 5
    while True:
        findings = lsp_client.diagnostics.get(uri, ())
        if any(item.code == "citry.python.unresolved-attribute" for item in findings):
            break
        if asyncio.get_running_loop().time() >= deadline:
            pytest.fail("the semantic diagnostic was not published")
        await asyncio.sleep(0.01)

    diagnostic = next(item for item in findings if item.code == "citry.python.unresolved-attribute")
    assert diagnostic.range.start.line == source[: source.index("title.missing")].count("\n")
    assert "missing" in diagnostic.message


@pytest.mark.asyncio
async def test_stdio_registered_dotted_alias_completion(lsp_client: LanguageClient, tmp_path):
    source = "<c-ui."
    uri = (tmp_path / "dotted-alias.citry-html").as_uri()
    notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "citry-html", 1, source))
    )
    await notification

    completion = await lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(uri),
            types.Position(0, len(source)),
            context=types.CompletionContext(
                types.CompletionTriggerKind.TriggerForIncompleteCompletions,
            ),
        )
    )

    assert isinstance(completion, types.CompletionList)
    item = next(candidate for candidate in completion.items if candidate.label == "c-ui.card")
    assert completion.is_incomplete is True
    assert isinstance(item.text_edit, types.InsertReplaceEdit)
    assert item.text_edit.replace == types.Range(types.Position(0, 1), types.Position(0, len(source)))


@pytest.mark.asyncio
async def test_stdio_attribute_completion_replaces_the_authored_token(
    syntax_lsp_client: LanguageClient,
    tmp_path,
):
    initial_source = "<div c-"
    uri = (tmp_path / "attribute-completion.citry-html").as_uri()
    notification = asyncio.wrap_future(
        syntax_lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    syntax_lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "citry-html", 1, initial_source))
    )
    await notification

    initial_completion = await syntax_lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(uri),
            types.Position(0, len(initial_source)),
            context=types.CompletionContext(
                types.CompletionTriggerKind.TriggerCharacter,
                "-",
            ),
        )
    )
    assert isinstance(initial_completion, types.CompletionList)
    assert initial_completion.is_incomplete is True
    initial_c_if = next(item for item in initial_completion.items if item.label == "c-if")
    assert isinstance(initial_c_if.text_edit, types.InsertReplaceEdit)
    assert initial_c_if.text_edit.replace == types.Range(
        types.Position(0, initial_source.index("c-")),
        types.Position(0, len(initial_source)),
    )

    source = "<div c-ioops>"
    notification = asyncio.wrap_future(
        syntax_lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    syntax_lsp_client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            types.VersionedTextDocumentIdentifier(2, uri),
            [types.TextDocumentContentChangeWholeDocument(source)],
        )
    )
    await notification
    token_start = source.index("c-ioops")
    cursor = types.Position(0, token_start + len("c-i"))

    completion = await syntax_lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(uri),
            cursor,
            context=types.CompletionContext(
                types.CompletionTriggerKind.TriggerForIncompleteCompletions,
            ),
        )
    )

    assert isinstance(completion, types.CompletionList)
    assert completion.is_incomplete is True
    c_if = next(item for item in completion.items if item.label == "c-if")
    assert c_if.filter_text == "c-if"
    assert isinstance(c_if.text_edit, types.InsertReplaceEdit)
    assert c_if.text_edit.replace == types.Range(
        types.Position(0, token_start),
        types.Position(0, token_start + len("c-ioops")),
    )
    assert source[:token_start] + c_if.text_edit.new_text + source[token_start + len("c-ioops") :] == (
        '<div c-if="${1:condition}">'
    )


@pytest.mark.asyncio
async def test_stdio_syntax_only_completion_and_lexical_hover(syntax_lsp_client: LanguageClient, tmp_path):
    completion_source = "<c-"
    completion_uri = (tmp_path / "completion.citry-html").as_uri()
    completion_notification = asyncio.wrap_future(
        syntax_lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    syntax_lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(completion_uri, "citry-html", 1, completion_source))
    )
    await completion_notification

    completion = await syntax_lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(completion_uri),
            types.Position(0, len(completion_source)),
            context=types.CompletionContext(
                types.CompletionTriggerKind.TriggerCharacter,
                "-",
            ),
        )
    )
    assert isinstance(completion, types.CompletionList)
    assert completion.is_incomplete is True
    c_for = next(item for item in completion.items if item.label == "c-for")
    assert c_for.insert_text_format == types.InsertTextFormat.Snippet
    assert isinstance(c_for.text_edit, types.InsertReplaceEdit)
    assert c_for.text_edit.new_text == 'c-for each="${1}">'
    assert c_for.text_edit.insert == types.Range(types.Position(0, 1), types.Position(0, len(completion_source)))

    updated_completion_source = "<c-fo"
    updated_completion_notification = asyncio.wrap_future(
        syntax_lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    syntax_lsp_client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            types.VersionedTextDocumentIdentifier(2, completion_uri),
            [types.TextDocumentContentChangeWholeDocument(updated_completion_source)],
        )
    )
    await updated_completion_notification
    updated_completion = await syntax_lsp_client.text_document_completion_async(
        types.CompletionParams(
            types.TextDocumentIdentifier(completion_uri),
            types.Position(0, len(updated_completion_source)),
            context=types.CompletionContext(
                types.CompletionTriggerKind.TriggerForIncompleteCompletions,
            ),
        )
    )
    assert isinstance(updated_completion, types.CompletionList)
    assert updated_completion.is_incomplete is True
    updated_c_for = next(item for item in updated_completion.items if item.label == "c-for")
    assert isinstance(updated_c_for.text_edit, types.InsertReplaceEdit)
    assert updated_c_for.text_edit.insert == types.Range(
        types.Position(0, 1),
        types.Position(0, len(updated_completion_source)),
    )

    hover_source = '<c-for each="item in items">{{ item }}</c-for>'
    hover_uri = (tmp_path / "hover.citry-html").as_uri()
    hover_notification = asyncio.wrap_future(
        syntax_lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    syntax_lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(hover_uri, "citry-html", 1, hover_source))
    )
    await hover_notification

    hover_result = await syntax_lsp_client.text_document_hover_async(
        types.HoverParams(
            types.TextDocumentIdentifier(hover_uri),
            types.Position(0, hover_source.index("{{ item") + len("{{ it")),
        )
    )
    assert hover_result is not None
    assert isinstance(hover_result.contents, types.MarkupContent)
    assert "Loop variable introduced by c-for" in hover_result.contents.value


@pytest.mark.asyncio
async def test_stdio_syntax_only_hover_serves_citry_documentation(syntax_lsp_client: LanguageClient, tmp_path):
    source = '<c-slot name="body" required></c-slot>'
    uri = (tmp_path / "syntax-hover.citry-html").as_uri()
    notification = asyncio.wrap_future(
        syntax_lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    syntax_lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "citry-html", 1, source))
    )
    await notification

    result = await syntax_lsp_client.text_document_hover_async(
        types.HoverParams(
            types.TextDocumentIdentifier(uri),
            types.Position(0, source.index("required") + 2),
        )
    )

    assert result is not None
    assert isinstance(result.contents, types.MarkupContent)
    assert "`required`" in result.contents.value
    assert "https://citry.dev/concepts/slots/#supply-fallback-content" in result.contents.value
    assert result.range == types.Range(
        types.Position(0, source.index("required")),
        types.Position(0, source.index("required") + len("required")),
    )


@pytest.mark.asyncio
async def test_stdio_projection_requests_accept_pygls_decoded_objects(
    syntax_lsp_client: LanguageClient,
    tmp_path,
) -> None:
    source = '<c-element is="form" c-action="\'lol\'"></c-element><div x-text="title"></div>'
    uri = (tmp_path / "projections.citry-html").as_uri()
    notification = asyncio.wrap_future(
        syntax_lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    syntax_lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "citry-html", 3, source))
    )
    await notification

    html = await syntax_lsp_client.protocol.send_request_async(
        HTML_PROJECTION_METHOD,
        {
            "textDocument": {"uri": uri, "version": 3},
            "position": {"line": 0, "character": source.index("c-action") + 2},
        },
    )
    browser = await syntax_lsp_client.protocol.send_request_async(
        BROWSER_PROJECTION_METHOD,
        {
            "textDocument": {"uri": uri, "version": 3},
            "position": {"line": 0, "character": source.index("title") + 2},
        },
    )

    assert html.source.startswith("<form")
    assert "c-action=\"'lol'\"" in html.source
    # Syntax-only mode has no proven browser roots, but the transport must
    # still reach that conservative result instead of rejecting its params.
    assert browser is None
    with pytest.raises(JsonRpcInvalidParams, match="parameters"):
        await syntax_lsp_client.protocol.send_request_async(
            HTML_PROJECTION_METHOD,
            {
                "textDocument": {"uri": uri, "version": 3},
                "position": {"line": 0, "character": source.index("c-action") + 2},
                "extra": True,
            },
        )


@pytest.mark.asyncio
async def test_stdio_dynamic_and_custom_formatting(lsp_client: LanguageClient, tmp_path):
    source = '😀<div  title = "hello" ></div>'
    uri = (tmp_path / "format.citry-html").as_uri()
    notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "citry-html", 7, source))
    )
    await notification

    standard = await lsp_client.text_document_formatting_async(
        types.DocumentFormattingParams(
            types.TextDocumentIdentifier(uri),
            types.FormattingOptions(tab_size=8, insert_spaces=False),
        )
    )
    custom = await lsp_client.protocol.send_request_async(
        "citry/formatTemplates",
        {
            "textDocument": {"uri": uri, "version": 7},
            "scope": {"kind": "document"},
        },
    )

    assert standard is not None
    assert len(standard) == 1
    assert standard[0].new_text == '😀<div title="hello"></div>'
    assert custom.kind == "edit"
    assert custom.edit.documentChanges[0].textDocument.version == 7
    assert custom.edit.documentChanges[0].edits[0].newText == standard[0].new_text


@pytest.mark.asyncio
async def test_stdio_python_formatting_requires_custom_request(lsp_client: LanguageClient, tmp_path):
    source = 'from citry import Component\nclass Card(Component):\n    template = """<div  id = "card" ></div>"""\n'
    uri = (tmp_path / "component.py").as_uri()
    notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "python", 9, source))
    )
    await notification

    custom = await lsp_client.protocol.send_request_async(
        "citry/formatTemplates",
        {
            "textDocument": {"uri": uri, "version": 9},
            "scope": {"kind": "position", "position": {"line": 2, "character": 20}},
        },
    )
    stale = await lsp_client.protocol.send_request_async(
        "citry/formatTemplates",
        {
            "textDocument": {"uri": uri, "version": 8},
            "scope": {"kind": "document"},
        },
    )

    assert custom.kind == "edit"
    assert '<div id="card"></div>' in custom.edit.documentChanges[0].edits[0].newText
    assert stale.kind == "refused"
    assert stale.code == "citry.format.stale-document"
    with pytest.raises(JsonRpcInvalidParams, match="scope must be document or position"):
        await lsp_client.protocol.send_request_async(
            "citry/formatTemplates",
            {
                "textDocument": {"uri": uri, "version": 9},
                "scope": {"kind": "document", "position": None},
            },
        )
    with pytest.raises(JsonRpcInvalidParams, match="only for citry-html"):
        await lsp_client.text_document_formatting_async(
            types.DocumentFormattingParams(
                types.TextDocumentIdentifier(uri),
                types.FormattingOptions(tab_size=4, insert_spaces=True),
            )
        )


@pytest.mark.asyncio
async def test_stdio_component_assets_round_trip_through_client(lsp_client: LanguageClient, tmp_path):
    source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template = """<main><script>const  nested=1;</script></main>"""\n'
        '    js = """const  direct=1;"""\n'
        '    css = """.card{color:red}"""\n'
    )
    uri = (tmp_path / "assets.py").as_uri()
    notification = asyncio.wrap_future(
        lsp_client.protocol.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    )
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "python", 11, source))
    )
    await notification

    result = await lsp_client.protocol.send_request_async(
        FORMAT_COMPONENT_ASSETS_METHOD,
        {
            "textDocument": {"uri": uri, "version": 11},
            "scope": {"kind": "document"},
        },
    )

    assert result.kind == "edit"
    new_text = result.edit.documentChanges[0].edits[0].newText
    assert "const nested = 1;" in new_text
    assert "const direct = 1;" in new_text
    assert ".card {" in new_text
    assert result.providers == []
    assert result.embeddedFormatting.providerSelection == "vscode-first-result"
    assert result.embeddedFormatting.providerIdentity is None
