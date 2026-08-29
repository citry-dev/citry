"""pygls transport adapter for the Citry analysis engine."""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import suppress
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar, cast

from lsprotocol import types
from pygls.exceptions import JsonRpcException, JsonRpcInvalidParams
from pygls.lsp.server import LanguageServer

from citry._diagnostic_catalog import FORMAT_PROVIDER_INVALID, FORMAT_STALE_DOCUMENT
from citry_core.template_formatter import EmbeddedFormatResult
from citry_lsp.engine import (
    DocumentState,
    ParsedRegion,
    browser_diagnostics,
    browser_projection,
    completion_result,
    declaration,
    definition,
    document_symbols,
    hover,
    html_projection,
    i18n_diagnostics,
    references,
    semantic_dependencies,
    template_lint_diagnostics,
    template_variable_hover,
)
from citry_lsp.environment import EnvironmentFileError, resolve_environment_file
from citry_lsp.formatting import (
    EmbeddedProviderRequest,
    FormatScope,
    PreparedComponentAssets,
    finish_component_assets,
    format_templates,
    prepare_component_assets,
)
from citry_lsp.project import ProjectState, load_project_async
from citry_lsp.protocol import (
    BROWSER_PROJECTION_METHOD,
    EMBEDDED_FORMATTING_VERSION,
    FORMAT_COMPONENT_ASSETS_METHOD,
    FORMAT_EMBEDDED_METHOD,
    FORMAT_TEMPLATES_METHOD,
    HTML_PROJECTION_METHOD,
    PROTOCOL_VERSION,
    SERVER_VERSION,
    EmbeddedFormattingCapability,
    ProjectStatus,
)
from citry_lsp.semantic import (
    semantic_completions,
    semantic_definition,
    semantic_diagnostics,
    semantic_hover,
    semantic_signature_help,
    semantic_type_definition,
    semantic_variable_hover,
)
from citry_lsp.type_analysis import TyAnalyzer
from citry_lsp.uri import file_uri_path

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Coroutine, Sequence

_InteractiveResult = TypeVar("_InteractiveResult")

STATUS_METHOD = "citry/status"
RELOAD_METHOD = "citry/reload"
_MISSING = object()
_EMBEDDED_REQUEST_TIMEOUT_SECONDS = 30.0
_RELOAD_DEBOUNCE_SECONDS = 0.15
_SEMANTIC_DIAGNOSTIC_DEBOUNCE_SECONDS = 0.15
logger = logging.getLogger(__name__)


class CitryLanguageServer(LanguageServer):
    """Language server with one independent workspace and project registry."""

    def __init__(self) -> None:
        super().__init__("citry-lsp", SERVER_VERSION, text_document_sync_kind=types.TextDocumentSyncKind.Full)
        self.app: str | None = None
        self.environment_file: Path | None = None
        self.completion_insert_replace = False
        self.completion_snippets = False
        self.dynamic_formatting = False
        self.embedded_formatting: EmbeddedFormattingCapability | None = None
        self.workspace_path = Path.cwd().resolve()
        self.workspace_uri = self.workspace_path.as_uri()
        self.project = ProjectState(
            ProjectStatus(
                interpreter="",
                workspace=str(self.workspace_path),
                mode="unavailable",
                message="The language server has not initialized.",
            )
        )
        self.documents: dict[str, DocumentState] = {}
        self.analysis_generation = 0
        self.type_analyzer = TyAnalyzer(self.workspace_path)
        self.type_analysis_warning_sent = False
        self._reload_requested_generation = 0
        self._reload_applied_generation = 0
        self._reload_delay = _RELOAD_DEBOUNCE_SECONDS
        self._reload_event = asyncio.Event()
        self._reload_task: asyncio.Task[None] | None = None
        self._reload_load_task: asyncio.Task[ProjectState] | None = None
        self._reload_waiters: list[tuple[int, asyncio.Future[dict[str, object]]]] = []
        self._semantic_task: asyncio.Task[None] | None = None
        self._interactive_requests = 0
        self._semantic_refresh_deferred = False
        self._close_task: asyncio.Task[None] | None = None
        self._closing = False

    def configure(self, params: types.InitializeParams) -> None:
        """Validate initialization options before asynchronous project loading."""
        options = params.initialization_options
        if options is None:
            options = {}
        if type(options) is not dict:
            msg = "Citry initializationOptions must be an object"
            raise JsonRpcInvalidParams(msg)
        client_protocol = options.get("protocolVersion")
        if type(client_protocol) is not int or client_protocol != PROTOCOL_VERSION:
            msg = f"Citry client protocol {client_protocol!r} is incompatible with server protocol {PROTOCOL_VERSION}."
            raise JsonRpcInvalidParams(msg)
        app = options.get("app")
        if app is not None and (type(app) is not str or not app):
            msg = "Citry initializationOptions.app must be a non-empty module:attribute string or null"
            raise JsonRpcInvalidParams(msg)
        self.app = app
        standard_formatting = options.get("standardFormatting", True)
        if type(standard_formatting) is not bool:
            msg = "Citry initializationOptions.standardFormatting must be a boolean"
            raise JsonRpcInvalidParams(msg)
        text_document = params.capabilities.text_document
        formatting = text_document.formatting if text_document else None
        self.dynamic_formatting = bool(
            standard_formatting and formatting is not None and formatting.dynamic_registration is True
        )
        completion = text_document.completion if text_document else None
        completion_item = completion.completion_item if completion else None
        self.completion_insert_replace = bool(
            completion_item is not None and completion_item.insert_replace_support is True
        )
        self.completion_snippets = bool(completion_item is not None and completion_item.snippet_support is True)
        self.embedded_formatting = _embedded_formatting_capability(options)
        self.workspace_uri = _workspace_uri(params)
        self.workspace_path = _workspace_path(params)
        environment_file = options.get("envFile")
        if environment_file is not None and (type(environment_file) is not str or not environment_file.strip()):
            msg = "Citry initializationOptions.envFile must be a non-empty path string or null"
            raise JsonRpcInvalidParams(msg)
        try:
            self.environment_file = (
                resolve_environment_file(self.workspace_path, environment_file)
                if environment_file is not None
                else None
            )
        except EnvironmentFileError as exc:
            msg = f"Citry initializationOptions.envFile {exc}"
            raise JsonRpcInvalidParams(msg) from exc
        # The child starts lazily, so configuration can replace this owner
        # without importing or starting project code in the stdio process.
        self.type_analyzer = TyAnalyzer(self.workspace_path)
        self.type_analysis_warning_sent = False
        self.project = _project_with_embedded_capability(
            ProjectState(
                ProjectStatus(
                    interpreter="",
                    workspace=str(self.workspace_path),
                    app=self.app,
                    mode="unavailable",
                    message="The configured Citry project is still loading.",
                )
            ),
            self.embedded_formatting,
        )

    async def load_initial_project(self) -> None:
        """Load registry facts without blocking initialization's event loop."""
        project = await load_project_async(
            self.workspace_path,
            self.app,
            environment_file=self.environment_file,
        )
        self.project = _project_with_embedded_capability(project, self.embedded_formatting)

    def publish(self, document: DocumentState) -> None:
        """Publish the current diagnostics for one document."""
        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                document.uri,
                document.diagnostics,
                version=document.version,
            )
        )

    def update_document(self, uri: str, language_id: str, source: str, version: int | None) -> None:
        """Analyze and publish one open document generation."""
        self.analysis_generation += 1
        document = self.documents.get(uri)
        if document is None:
            document = DocumentState(uri, language_id, source, version)
            self.documents[uri] = document
        document.language_id = language_id
        document.update(source, version, self.project)
        self.publish(document)

    async def publish_semantic_diagnostics(self, uri: str, version: int | None) -> None:
        """Publish mapped type findings only for the generation that requested them."""
        document = self.documents.get(uri)
        if document is None:
            return
        generation = self.analysis_generation
        findings = await semantic_diagnostics(
            self.type_analyzer,
            document,
            self.project,
            self.documents,
        )
        lint_findings = template_lint_diagnostics(document, self.project, self.documents)
        browser_findings = browser_diagnostics(document, self.project, self.documents)
        i18n_findings = i18n_diagnostics(document, self.project, self.documents)
        current = self.documents.get(uri)
        if current is not document or current.version != version or self.analysis_generation != generation:
            return
        _report_type_analysis_failure(self)
        self.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri,
                (*document.diagnostics, *lint_findings, *browser_findings, *i18n_findings, *findings),
                version=version,
            )
        )

    async def publish_semantic_dependents(self, changed: DocumentState) -> None:
        """Refresh the changed document and templates that depend on Python source."""
        await self.publish_semantic_diagnostics(changed.uri, changed.version)
        if changed.language_id != "python":
            return
        try:
            changed_path = file_uri_path(changed.uri)
            changed_uri = changed_path.resolve().as_uri() if changed_path is not None else changed.uri
        except (TypeError, ValueError):
            changed_uri = changed.uri
        direct: list[DocumentState] = []
        fallback: list[DocumentState] = []
        for document in tuple(self.documents.values()):
            if document is changed:
                continue
            dependencies = semantic_dependencies(document, self.project, self.documents)
            if changed_uri in dependencies.source_uris:
                direct.append(document)
            elif not dependencies.complete:
                fallback.append(document)
        for document in (*direct, *fallback):
            await self.publish_semantic_diagnostics(document.uri, document.version)

    def schedule_semantic_dependents(self, changed: DocumentState) -> None:
        """Debounce semantic diagnostics so interactive requests get priority."""
        if self._interactive_requests:
            self._semantic_refresh_deferred = True
            return
        self._replace_semantic_task(self._delayed_semantic_dependents(changed))

    def schedule_all_semantic_diagnostics(self) -> None:
        """Refresh every open document after one applied project generation."""
        if self._interactive_requests:
            self._semantic_refresh_deferred = True
            return
        self._replace_semantic_task(self._delayed_all_semantic_diagnostics())

    async def run_interactive(
        self,
        operation: Callable[[], Awaitable[_InteractiveResult]],
    ) -> _InteractiveResult:
        """Preempt background diagnostics while one interactive Ty query runs."""
        self._interactive_requests += 1
        try:
            semantic = self._semantic_task
            if semantic is not None and semantic is not asyncio.current_task() and not semantic.done():
                self._semantic_refresh_deferred = True
                semantic.cancel()
                await asyncio.gather(semantic, return_exceptions=True)
            return await operation()
        finally:
            self._interactive_requests -= 1
            if (
                self._interactive_requests == 0
                and self._semantic_refresh_deferred
                and self.documents
                and not self._closing
            ):
                self._semantic_refresh_deferred = False
                self.schedule_all_semantic_diagnostics()

    def _replace_semantic_task(self, refresh: Coroutine[object, object, None]) -> None:
        previous = self._semantic_task
        if previous is not None and not previous.done():
            previous.cancel()
        task = asyncio.create_task(refresh)
        self._semantic_task = task
        task.add_done_callback(_consume_background_task)

    async def _delayed_semantic_dependents(self, changed: DocumentState) -> None:
        await asyncio.sleep(_SEMANTIC_DIAGNOSTIC_DEBOUNCE_SECONDS)
        current = self.documents.get(changed.uri)
        if current is not changed:
            return
        await self.publish_semantic_dependents(changed)

    async def _delayed_all_semantic_diagnostics(self) -> None:
        await asyncio.sleep(_SEMANTIC_DIAGNOSTIC_DEBOUNCE_SECONDS)
        for document in tuple(self.documents.values()):
            await self.publish_semantic_diagnostics(document.uri, document.version)

    async def wait_for_semantic_refresh(self) -> None:
        """Await the currently scheduled refresh, primarily for focused tests."""
        task = self._semantic_task
        if task is not None:
            await asyncio.shield(task)

    async def reload_project(self, *, debounce: float = 0.0) -> dict[str, object]:
        """Request one coalesced, latest-wins project reload generation."""
        if self._closing:
            return self.project.status.to_dict()
        self._reload_requested_generation += 1
        requested = self._reload_requested_generation
        self._reload_delay = min(self._reload_delay, max(debounce, 0.0))
        waiter: asyncio.Future[dict[str, object]] = asyncio.get_running_loop().create_future()
        self._reload_waiters.append((requested, waiter))
        self._reload_event.set()
        active_load = self._reload_load_task
        if active_load is not None and not active_load.done():
            active_load.cancel()
        if self._reload_task is None or self._reload_task.done():
            self._reload_task = asyncio.create_task(self._reload_worker())
            self._reload_task.add_done_callback(_consume_background_task)
        try:
            return await asyncio.shield(waiter)
        except asyncio.CancelledError:
            waiter.cancel()
            raise

    async def _reload_worker(self) -> None:
        """Serialize app discovery and discard every superseded result."""
        try:
            while not self._closing:
                self._reload_event.clear()
                delay = self._reload_delay
                self._reload_delay = _RELOAD_DEBOUNCE_SECONDS
                if delay:
                    try:
                        await asyncio.wait_for(self._reload_event.wait(), delay)
                    except asyncio.TimeoutError:
                        pass
                    else:
                        continue
                target = self._reload_requested_generation
                loading = asyncio.create_task(
                    load_project_async(
                        self.workspace_path,
                        self.app,
                        environment_file=self.environment_file,
                    )
                )
                self._reload_load_task = loading
                try:
                    project = await loading
                except asyncio.CancelledError:
                    if not self._closing and target != self._reload_requested_generation:
                        continue
                    raise
                finally:
                    if self._reload_load_task is loading:
                        self._reload_load_task = None
                if target != self._reload_requested_generation:
                    continue
                prepared = await self._prepare_project_documents(project)
                if target != self._reload_requested_generation:
                    continue
                self._apply_project(project, target, prepared)
                self._finish_reload_waiters(target)
                if not self._reload_event.is_set() and target == self._reload_requested_generation:
                    return
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Citry project reload failed")
            self._fail_reload_waiters(exc)
        finally:
            if self._closing:
                self._fail_reload_waiters(asyncio.CancelledError())

    async def _prepare_project_documents(
        self,
        project: ProjectState,
    ) -> dict[str, tuple[DocumentState, int, DocumentState]]:
        """Parse stable document snapshots away from the LSP event loop."""
        snapshots = tuple(
            (
                document,
                document.uri,
                document.language_id,
                document.source,
                document.version,
                document._analysis_revision,
                dict(document.last_good),
            )
            for document in self.documents.values()
        )
        return await asyncio.to_thread(_reanalyze_document_snapshots, snapshots, project)

    def _apply_project(
        self,
        project: ProjectState,
        generation: int,
        prepared: dict[str, tuple[DocumentState, int, DocumentState]],
    ) -> None:
        """Publish one completed project generation atomically on the event loop."""
        self.analysis_generation += 1
        semantic = self._semantic_task
        if semantic is not None and not semantic.done():
            semantic.cancel()
        self.project = _project_with_embedded_capability(project, self.embedded_formatting)
        self._reload_applied_generation = generation
        for uri, document in tuple(self.documents.items()):
            snapshot = prepared.get(uri)
            if snapshot is not None and snapshot[0] is document and snapshot[1] == document._analysis_revision:
                analyzed = snapshot[2]
                self.documents[uri] = analyzed
            else:
                # A document opened or changed while snapshots were parsing.
                # Reanalyze only that race on the event loop before publishing.
                document.update(document.source, document.version, self.project)
                analyzed = document
            self.publish(analyzed)
        self.protocol.notify(STATUS_METHOD, self.project.status.to_dict())
        if self.documents:
            self.schedule_all_semantic_diagnostics()

    def _finish_reload_waiters(self, generation: int) -> None:
        status = self.project.status.to_dict()
        remaining: list[tuple[int, asyncio.Future[dict[str, object]]]] = []
        for target, waiter in self._reload_waiters:
            if target <= generation:
                if not waiter.done():
                    waiter.set_result(status)
            else:
                remaining.append((target, waiter))
        self._reload_waiters = remaining

    def _fail_reload_waiters(self, error: BaseException) -> None:
        for _target, waiter in self._reload_waiters:
            if not waiter.done():
                if isinstance(error, asyncio.CancelledError):
                    waiter.cancel()
                else:
                    waiter.set_exception(error)
        self._reload_waiters.clear()

    async def close(self) -> None:
        """Cancel background generations and reap the one owned analyzer."""
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._close_owned_resources())
        await _await_cancellation_safe(self._close_task)

    async def _close_owned_resources(self) -> None:
        """Perform terminal cleanup exactly once for all shutdown callers."""
        self._closing = True
        tasks = [task for task in (self._semantic_task, self._reload_task) if task is not None and not task.done()]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._fail_reload_waiters(asyncio.CancelledError())
        await self.type_analyzer.close()


server = CitryLanguageServer()


def _consume_background_task(task: asyncio.Task[object]) -> None:
    """Observe a background result without reporting normal cancellation."""
    with suppress(asyncio.CancelledError):
        error = task.exception()
        if error is not None:
            logger.error(
                "Citry background task failed",
                exc_info=(type(error), error, error.__traceback__),
            )


def _reanalyze_document_snapshots(
    snapshots: tuple[
        tuple[DocumentState, str, str, str, int | None, int, dict[str, ParsedRegion]],
        ...,
    ],
    project: ProjectState,
) -> dict[str, tuple[DocumentState, int, DocumentState]]:
    """Build replacement document generations in one worker thread."""
    prepared: dict[str, tuple[DocumentState, int, DocumentState]] = {}
    for original, uri, language_id, source, version, revision, last_good in snapshots:
        replacement = DocumentState(uri, language_id, source, version)
        replacement.last_good = last_good
        replacement.update(source, version, project)
        prepared[uri] = (original, revision, replacement)
    return prepared


async def _await_cancellation_safe(task: asyncio.Task[None]) -> None:
    """Finish terminal ownership cleanup before propagating cancellation."""
    cancellation: asyncio.CancelledError | None = None
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError as exc:
            cancellation = exc
    await task
    if cancellation is not None:
        raise cancellation


@server.feature(types.SHUTDOWN)
async def shutdown_feature(ls: CitryLanguageServer, *_args: object) -> None:
    """Stop the analyzer child while the client still awaits a response."""
    await ls.close()


@server.feature(types.INITIALIZE)
async def initialize(ls: CitryLanguageServer, params: types.InitializeParams) -> None:
    """Capture initialization options before pygls builds capabilities."""
    ls.configure(params)
    await ls.load_initial_project()


@server.feature(types.INITIALIZED)
async def initialized(ls: CitryLanguageServer, _params: types.InitializedParams) -> None:
    """Publish project status once the client can receive notifications."""
    if ls.dynamic_formatting:
        ls.feature(types.TEXT_DOCUMENT_FORMATTING)(format_document)
        await _register_formatting_capability(ls)
    status = ls.project.status
    ls.protocol.notify(STATUS_METHOD, status.to_dict())
    if status.message is not None and status.mode != "registry":
        message_type = types.MessageType.Warning if status.mode == "syntax-only" else types.MessageType.Error
        ls.window_show_message(types.ShowMessageParams(message_type, status.message))


def _formatting_registration_params(workspace_uri: str) -> types.RegistrationParams:
    # The registration itself belongs to this initialized workspace client.
    # Keep the selector language-only: PyCharm's native client rejects the LSP
    # 3.17 RelativePattern wire shape, while LSP4IJ 0.20.1 incorrectly ORs the
    # language, scheme, and pattern fields of one document filter. Adding a
    # file scheme would therefore expose Citry formatting on ordinary Python.
    _ = workspace_uri
    selector = types.TextDocumentFilterLanguage(language="citry-html")
    options = types.DocumentFormattingRegistrationOptions(document_selector=[selector])
    registration = types.Registration(
        "citry-html-formatting",
        types.TEXT_DOCUMENT_FORMATTING,
        options,
    )
    return types.RegistrationParams([registration])


async def _register_formatting_capability(ls: CitryLanguageServer) -> None:
    try:
        await ls.client_register_capability_async(_formatting_registration_params(ls.workspace_uri))
    except JsonRpcException as error:
        logger.warning("Client declined dynamic formatting registration: %s", error)


def _embedded_formatting_capability(options: dict[str, object]) -> EmbeddedFormattingCapability | None:
    raw = options.get("embeddedFormatting", _MISSING)
    if raw is _MISSING:
        return None
    if type(raw) is not dict:
        msg = "Citry initializationOptions.embeddedFormatting must be an object"
        raise JsonRpcInvalidParams(msg)
    version = raw.get("version", _MISSING)
    languages = raw.get("languages", _MISSING)
    provider_selection = raw.get("providerSelection", _MISSING)
    if type(version) is not int or version != EMBEDDED_FORMATTING_VERSION:
        msg = f"Citry embeddedFormatting.version must be {EMBEDDED_FORMATTING_VERSION}"
        raise JsonRpcInvalidParams(msg)
    if type(languages) is not list or any(
        type(language) is not str or language not in {"javascript", "css"} for language in languages
    ):
        msg = "Citry embeddedFormatting.languages must contain only javascript and css"
        raise JsonRpcInvalidParams(msg)
    if len(set(languages)) != len(languages):
        msg = "Citry embeddedFormatting.languages must not contain duplicates"
        raise JsonRpcInvalidParams(msg)
    if provider_selection != "vscode-first-result":
        msg = "Citry embeddedFormatting.providerSelection must be vscode-first-result"
        raise JsonRpcInvalidParams(msg)
    return EmbeddedFormattingCapability(
        languages=tuple(cast("list[str]", languages)),
        provider_selection=provider_selection,
    )


def _project_with_embedded_capability(
    project: ProjectState,
    capability: EmbeddedFormattingCapability | None,
) -> ProjectState:
    status = replace(project.status, embedded_formatting=capability)
    return replace(project, status=status)


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: CitryLanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    """Analyze a newly opened Citry or Python document."""
    document = params.text_document
    ls.update_document(document.uri, document.language_id, document.text, document.version)
    ls.schedule_semantic_dependents(ls.documents[document.uri])


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: CitryLanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    """Analyze the full synchronized document content."""
    if not params.content_changes:
        return
    change = params.content_changes[-1]
    source = change.text
    previous = ls.documents.get(params.text_document.uri)
    language_id = previous.language_id if previous is not None else "python"
    ls.update_document(params.text_document.uri, language_id, source, params.text_document.version)
    ls.schedule_semantic_dependents(ls.documents[params.text_document.uri])


@server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
async def did_close(ls: CitryLanguageServer, params: types.DidCloseTextDocumentParams) -> None:
    """Drop document state and clear its diagnostics."""
    ls.analysis_generation += 1
    closed = ls.documents.pop(params.text_document.uri, None)
    await ls.type_analyzer.close_document(params.text_document.uri)
    ls.text_document_publish_diagnostics(types.PublishDiagnosticsParams(params.text_document.uri, ()))
    if closed is not None and closed.language_id == "python":
        ls.schedule_all_semantic_diagnostics()


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["<", "-", ".", " ", '"', "'", "{", ",", "#", "$"]),
)
async def completion(ls: CitryLanguageServer, params: types.CompletionParams) -> types.CompletionList:
    """Complete Citry syntax, lexical bindings, and registry contracts."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        return types.CompletionList(is_incomplete=False, items=())
    result = completion_result(document, params.position, ls.project, ls.documents)
    if not result.items:
        generation = ls.analysis_generation
        semantic = await ls.run_interactive(
            lambda: semantic_completions(
                ls.type_analyzer,
                document,
                params.position,
                ls.project,
                ls.documents,
            )
        )
        if generation != ls.analysis_generation:
            return types.CompletionList(is_incomplete=False, items=())
        if semantic:
            result = replace(result, items=semantic, is_incomplete=True)
        _report_type_analysis_failure(ls)
    for item in result.items:
        if not ls.completion_snippets and item.insert_text_format == types.InsertTextFormat.Snippet:
            if item.insert_text is not None:
                item.insert_text = _snippet_plain_text(item.insert_text)
            edit = item.text_edit
            if isinstance(edit, (types.TextEdit, types.InsertReplaceEdit)):
                edit.new_text = _snippet_plain_text(edit.new_text)
            item.insert_text_format = types.InsertTextFormat.PlainText
        if not ls.completion_insert_replace:
            edit = item.text_edit
            if isinstance(edit, types.InsertReplaceEdit):
                item.text_edit = types.TextEdit(range=edit.replace, new_text=edit.new_text)
    return types.CompletionList(is_incomplete=result.is_incomplete, items=result.items)


def _snippet_plain_text(value: str) -> str:
    """Resolve tab stops to their defaults for clients without snippet support."""
    result: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value):
            result.append(value[index + 1])
            index += 2
            continue
        if char != "$" or index + 1 >= len(value):
            result.append(char)
            index += 1
            continue
        if value[index + 1].isdigit():
            index += 2
            while index < len(value) and value[index].isdigit():
                index += 1
            continue
        if value[index + 1] != "{":
            result.append(char)
            index += 1
            continue
        end = index + 2
        depth = 1
        while end < len(value) and depth:
            if value[end] == "\\":
                end += 2
                continue
            if value[end] == "{":
                depth += 1
            elif value[end] == "}":
                depth -= 1
            end += 1
        if depth:
            result.append(char)
            index += 1
            continue
        placeholder = value[index + 2 : end - 1]
        tab_stop, separator, default = placeholder.partition(":")
        if tab_stop.isdigit() and separator:
            result.append(_snippet_plain_text(default))
        elif not tab_stop.isdigit():
            result.append(value[index:end])
        index = end
    return "".join(result)


@server.feature(types.TEXT_DOCUMENT_HOVER)
async def hover_feature(ls: CitryLanguageServer, params: types.HoverParams) -> types.Hover | None:
    """Show Python-style variables, Citry syntax, or catalog documentation."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        return None
    variable = template_variable_hover(document, params.position, ls.project, ls.documents)
    if variable is not None:
        # The parser owns identity and provenance; ty contributes only the current Python type.
        generation = ls.analysis_generation
        variable_result = await ls.run_interactive(
            lambda: semantic_variable_hover(
                ls.type_analyzer,
                document,
                params.position,
                ls.project,
                ls.documents,
                variable,
            )
        )
        if generation != ls.analysis_generation:
            return None
        _report_type_analysis_failure(ls)
        return variable_result
    result = hover(document, params.position, ls.project, ls.documents)
    if result is None:
        generation = ls.analysis_generation
        result = await ls.run_interactive(
            lambda: semantic_hover(
                ls.type_analyzer,
                document,
                params.position,
                ls.project,
                ls.documents,
            )
        )
        if generation != ls.analysis_generation:
            return None
        _report_type_analysis_failure(ls)
    return result


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
async def definition_feature(
    ls: CitryLanguageServer,
    params: types.DefinitionParams,
) -> types.Location | list[types.Location] | None:
    """Navigate to exact lexical, component, and component-input declarations."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        return None
    result = definition(document, params.position, ls.project, ls.documents)
    if result is not None:
        return result
    generation = ls.analysis_generation
    semantic = await ls.run_interactive(
        lambda: semantic_definition(
            ls.type_analyzer,
            document,
            params.position,
            ls.project,
            ls.documents,
        )
    )
    if generation != ls.analysis_generation:
        return None
    _report_type_analysis_failure(ls)
    if len(semantic) == 1:
        return semantic[0]
    return list(semantic) if semantic else None


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
async def references_feature(
    ls: CitryLanguageServer,
    params: types.ReferenceParams,
) -> list[types.Location] | None:
    """List exact uses of one Citry-owned template variable."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        return None
    return references(
        document,
        params.position,
        ls.project,
        ls.documents,
        include_declaration=params.context.include_declaration,
    )


@server.feature(types.TEXT_DOCUMENT_DECLARATION)
async def declaration_feature(
    ls: CitryLanguageServer,
    params: types.DeclarationParams,
) -> types.Location | list[types.Location] | None:
    """Navigate from one template variable to its authored declaration."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        return None
    return declaration(document, params.position, ls.project, ls.documents)


@server.feature(types.TEXT_DOCUMENT_TYPE_DEFINITION)
async def type_definition_feature(
    ls: CitryLanguageServer,
    params: types.TypeDefinitionParams,
) -> types.Location | list[types.Location] | None:
    """Navigate to Python types proven for one template variable."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        return None
    generation = ls.analysis_generation
    locations = await ls.run_interactive(
        lambda: semantic_type_definition(
            ls.type_analyzer,
            document,
            params.position,
            ls.project,
            ls.documents,
        )
    )
    if generation != ls.analysis_generation:
        return None
    _report_type_analysis_failure(ls)
    if len(locations) == 1:
        return locations[0]
    return list(locations) if locations else None


@server.feature(
    types.TEXT_DOCUMENT_SIGNATURE_HELP,
    types.SignatureHelpOptions(trigger_characters=["(", ","], retrigger_characters=[","]),
)
async def signature_help_feature(
    ls: CitryLanguageServer,
    params: types.SignatureHelpParams,
) -> types.SignatureHelp | None:
    """Show Python call signatures for a proven template expression."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        return None
    generation = ls.analysis_generation
    result = await ls.run_interactive(
        lambda: semantic_signature_help(
            ls.type_analyzer,
            document,
            params.position,
            ls.project,
            ls.documents,
        )
    )
    if generation != ls.analysis_generation:
        return None
    _report_type_analysis_failure(ls)
    return result


def _report_type_analysis_failure(ls: CitryLanguageServer) -> None:
    """Show one degradation notice while parser-backed features stay active."""
    message = ls.type_analyzer.failure
    if message is None or ls.type_analysis_warning_sent:
        return
    ls.type_analysis_warning_sent = True
    ls.window_show_message(types.ShowMessageParams(types.MessageType.Warning, message))


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def symbols_feature(
    ls: CitryLanguageServer,
    params: types.DocumentSymbolParams,
) -> list[types.DocumentSymbol]:
    """Return parsed tag hierarchy for the current document."""
    document = ls.documents.get(params.text_document.uri)
    return document_symbols(document) if document is not None else []


async def format_document(
    ls: CitryLanguageServer,
    params: types.DocumentFormattingParams,
) -> Sequence[dict[str, object]]:
    """Format one dynamically selected standalone Citry document."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        msg = "Citry cannot format a document that is not open"
        raise JsonRpcInvalidParams(msg)
    if document.version is None:
        msg = "Citry cannot format a document without a synchronized version"
        raise JsonRpcInvalidParams(msg)
    if document.language_id != "citry-html":
        msg = "Standard Citry formatting is available only for citry-html documents"
        raise JsonRpcInvalidParams(msg)
    result = await _format_component_assets(
        ls,
        document.uri,
        document.version,
        "document",
        None,
    )
    if result["kind"] == "refused":
        raise JsonRpcInvalidParams(f"{result['code']}: {result['message']}")
    _log_format_notices(ls, result)
    if result["kind"] == "unchanged":
        return []
    edit = cast("dict[str, object]", result["edit"])
    document_changes = cast("list[dict[str, object]]", edit["documentChanges"])
    return cast("list[dict[str, object]]", document_changes[0]["edits"])


@server.feature(types.WORKSPACE_DID_CHANGE_WATCHED_FILES)
async def watched_files(ls: CitryLanguageServer, params: types.DidChangeWatchedFilesParams) -> None:
    """Reload registry facts when project Python or environment files change."""
    # The copied catalog proves component origins, but it is not a complete
    # transitive import graph for registrations and app configuration. Keep
    # the conservative workspace-wide Python watch and make it cheap through
    # burst coalescing rather than guessing that an unlisted module is inert.
    if ls.app is not None and any(_project_reload_change(ls, change.uri) for change in params.changes):
        await ls.reload_project(debounce=_RELOAD_DEBOUNCE_SECONDS)


def _project_reload_change(ls: CitryLanguageServer, uri: str) -> bool:
    if uri.lower().endswith(".py"):
        return True
    if ls.environment_file is None:
        return False
    changed = file_uri_path(uri)
    if changed is None:
        return False
    try:
        return changed.resolve() == ls.environment_file
    except (OSError, RuntimeError, ValueError):
        return False


@server.feature(BROWSER_PROJECTION_METHOD)
def browser_projection_request(ls: CitryLanguageServer, params: object) -> dict[str, object] | None:
    """Return one version-bound JavaScript-provider projection."""
    uri, version, position = _projection_request_params(params, label="browser projection")
    document = ls.documents.get(uri)
    if document is None or document.version != version:
        return None
    projection = browser_projection(
        document,
        position,
        ls.project,
        ls.documents,
    )
    return projection.to_dict() if projection is not None else None


@server.feature(HTML_PROJECTION_METHOD)
def html_projection_request(ls: CitryLanguageServer, params: object) -> dict[str, object] | None:
    """Return one version-bound parser-proven HTML-provider projection."""
    uri, version, position = _projection_request_params(params, label="HTML projection")
    document = ls.documents.get(uri)
    if document is None or document.version != version:
        return None
    projection = html_projection(document, position, ls.project)
    return projection.to_dict() if projection is not None else None


@server.feature(STATUS_METHOD)
def status_request(ls: CitryLanguageServer, _params: object | None = None) -> dict[str, object]:
    """Return the current interpreter, registry target, protocol, and confidence mode."""
    return ls.project.status.to_dict()


@server.feature(RELOAD_METHOD)
async def reload_request(ls: CitryLanguageServer, _params: object | None = None) -> dict[str, object]:
    """Reload the configured registry target through a fresh worker."""
    return await ls.reload_project()


@server.feature(FORMAT_TEMPLATES_METHOD)
def format_templates_request(ls: CitryLanguageServer, params: object) -> dict[str, object]:
    """Format current Citry template text through the versioned custom request."""
    uri, version, scope, position = _format_templates_params(params)
    document = ls.documents.get(uri)
    if document is None:
        return {
            "kind": "refused",
            "code": FORMAT_STALE_DOCUMENT,
            "message": "document is not open in the Citry language server",
            "range": None,
        }
    return format_templates(
        document,
        requested_version=version,
        scope=scope,
        position=position,
    )


@server.feature(FORMAT_COMPONENT_ASSETS_METHOD)
async def format_component_assets_request(ls: CitryLanguageServer, params: object) -> dict[str, object]:
    """Format current template, JavaScript, and CSS component assets atomically."""
    uri, version, scope, position = _format_component_assets_params(params)
    return await _format_component_assets(ls, uri, version, scope, position)


async def _format_component_assets(
    ls: CitryLanguageServer,
    uri: str,
    version: int,
    scope: FormatScope,
    position: types.Position | None,
) -> dict[str, object]:
    document = ls.documents.get(uri)
    if document is None:
        return _with_embedded_capability(
            {
                "kind": "refused",
                "code": FORMAT_STALE_DOCUMENT,
                "message": "document is not open in the Citry language server",
                "range": None,
            },
            ls.embedded_formatting,
        )
    prepared = prepare_component_assets(
        document,
        requested_version=version,
        scope=scope,
        position=position,
    )
    if not isinstance(prepared, PreparedComponentAssets):
        return _with_embedded_capability(prepared, ls.embedded_formatting)
    results_or_refusal = await _embedded_results(ls, prepared)
    if isinstance(results_or_refusal, dict):
        return _with_embedded_capability(results_or_refusal, ls.embedded_formatting)
    current = ls.documents.get(uri)
    if current is None or not _prepared_document_is_current(current, prepared):
        return _with_embedded_capability(
            _stale_embedded_response(),
            ls.embedded_formatting,
        )
    result = finish_component_assets(current, prepared, results_or_refusal)
    if not _prepared_document_is_current(ls.documents.get(uri), prepared):
        return _with_embedded_capability(
            _stale_embedded_response(),
            ls.embedded_formatting,
        )
    return _with_embedded_capability(result, ls.embedded_formatting)


async def _embedded_results(
    ls: CitryLanguageServer,
    prepared: PreparedComponentAssets,
) -> list[EmbeddedFormatResult] | dict[str, object]:
    capability = ls.embedded_formatting
    supported_languages = frozenset(capability.languages) if capability is not None else frozenset()
    delegated = [request for request in prepared.requests if request.language in supported_languages]
    results = [
        EmbeddedFormatResult.unavailable(
            prepared.id,
            request.id,
            f"the client does not offer {request.language} embedded formatting",
        )
        for request in prepared.requests
        if request.language not in supported_languages
    ]
    if not delegated:
        return results
    if capability is None:
        return results
    request_params = _embedded_request_params(prepared, delegated)
    request_id = str(uuid.uuid4())
    try:
        pending = ls.protocol.send_request_async(
            FORMAT_EMBEDDED_METHOD,
            request_params,
            msg_id=request_id,
        )
        response = await asyncio.wait_for(
            asyncio.shield(pending),
            timeout=_EMBEDDED_REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as error:
        ls.protocol.notify(types.CANCEL_REQUEST, types.CancelParams(id=request_id))
        pending.add_done_callback(_consume_cancelled_client_response)
        return _embedded_request_failure(error)
    except asyncio.CancelledError:
        ls.protocol.notify(types.CANCEL_REQUEST, types.CancelParams(id=request_id))
        pending.add_done_callback(_consume_cancelled_client_response)
        raise
    except Exception as error:  # noqa: BLE001 - an external client must not terminate the server request
        return _embedded_request_failure(error)
    if not _prepared_document_is_current(ls.documents.get(prepared.document_uri), prepared):
        return _stale_embedded_response()
    try:
        delegated_results = _parse_embedded_response(
            response,
            uri=prepared.document_uri,
            document_version=prepared.document_version,
            plan_id=prepared.id,
            expected_region_ids=tuple(request.id for request in delegated),
            provider_selection=capability.provider_selection,
        )
    except ValueError as error:
        return {
            "kind": "refused",
            "code": FORMAT_PROVIDER_INVALID,
            "message": str(error),
            "range": None,
        }
    results.extend(delegated_results)
    return results


def _consume_cancelled_client_response(future: asyncio.Future[object]) -> None:
    with suppress(BaseException):
        future.result()


def _embedded_request_params(
    prepared: PreparedComponentAssets,
    requests: list[EmbeddedProviderRequest],
) -> dict[str, object]:
    return {
        "version": EMBEDDED_FORMATTING_VERSION,
        "textDocument": {
            "uri": prepared.document_uri,
            "version": prepared.document_version,
        },
        "planId": prepared.id,
        "regions": [
            {
                "id": request.id,
                "language": request.language,
                "kind": request.kind,
                "source": request.source,
                "virtualSource": request.virtual_source,
                "protectedRanges": [],
                "delimiterConstraints": {
                    "forbiddenSubstrings": list(request.forbidden_substrings),
                    "caseInsensitive": True,
                },
            }
            for request in requests
        ],
    }


def _parse_embedded_response(
    response: object,
    *,
    uri: str,
    document_version: int,
    plan_id: str,
    expected_region_ids: tuple[str, ...],
    provider_selection: str,
) -> list[EmbeddedFormatResult]:
    if not _is_wire_object(response):
        msg = "citry/formatEmbedded response must be an object"
        raise ValueError(msg)
    version = _wire_field(response, "version", default=_MISSING)
    text_document = _wire_field(response, "textDocument", default=_MISSING)
    echoed_plan = _wire_field(response, "planId", default=_MISSING)
    selection = _wire_field(response, "providerSelection", default=_MISSING)
    raw_results = _wire_field(response, "results", default=_MISSING)
    if type(version) is not int or version != EMBEDDED_FORMATTING_VERSION:
        msg = "citry/formatEmbedded response has an unsupported version"
        raise ValueError(msg)
    if not _is_wire_object(text_document):
        msg = "citry/formatEmbedded response requires a textDocument object"
        raise ValueError(msg)
    if _wire_field(text_document, "uri") != uri:
        msg = "citry/formatEmbedded response belongs to a different document URI"
        raise ValueError(msg)
    echoed_document_version = _wire_field(text_document, "version")
    if type(echoed_document_version) is not int or echoed_document_version != document_version:
        msg = "citry/formatEmbedded response belongs to a different document version"
        raise ValueError(msg)
    if echoed_plan != plan_id:
        msg = "citry/formatEmbedded response belongs to a different plan"
        raise ValueError(msg)
    if selection != provider_selection:
        msg = "citry/formatEmbedded response changed the provider selection mechanism"
        raise ValueError(msg)
    if type(raw_results) is not list or len(raw_results) != len(expected_region_ids):
        msg = "citry/formatEmbedded response result count does not match the request"
        raise ValueError(msg)

    expected = frozenset(expected_region_ids)
    seen: set[str] = set()
    results: list[EmbeddedFormatResult] = []
    for raw_result in raw_results:
        if not _is_wire_object(raw_result):
            msg = "citry/formatEmbedded results must be objects"
            raise ValueError(msg)
        result_plan = _wire_field(raw_result, "planId", default=_MISSING)
        region_id = _wire_field(raw_result, "regionId", default=_MISSING)
        status = _wire_field(raw_result, "status", default=_MISSING)
        text = _wire_field(raw_result, "text", default=_MISSING)
        provider = _wire_field(raw_result, "provider", default=_MISSING)
        message = _wire_field(raw_result, "message", default=_MISSING)
        if result_plan != plan_id or type(region_id) is not str or region_id not in expected:
            msg = "citry/formatEmbedded result has an unknown plan or region identity"
            raise ValueError(msg)
        if region_id in seen:
            msg = f"citry/formatEmbedded response duplicates region {region_id!r}"
            raise ValueError(msg)
        seen.add(region_id)
        if status == "formatted":
            if type(text) is not str or message is not _MISSING:
                msg = "formatted citry/formatEmbedded results require text, no message, and an unknown provider"
                raise ValueError(msg)
            if provider is not _MISSING and provider is not None:
                msg = "vscode-first-result cannot claim a provider identity"
                raise ValueError(msg)
            results.append(
                EmbeddedFormatResult.formatted(
                    plan_id,
                    region_id,
                    text,
                    None,
                )
            )
        elif status == "unchanged":
            if text is not _MISSING or provider is not _MISSING or message is not _MISSING:
                msg = "unchanged citry/formatEmbedded results cannot carry output fields"
                raise ValueError(msg)
            results.append(EmbeddedFormatResult.unchanged(plan_id, region_id))
        elif status == "unavailable":
            if type(message) is not str or text is not _MISSING or provider is not _MISSING:
                msg = "unavailable citry/formatEmbedded results require only a message"
                raise ValueError(msg)
            results.append(EmbeddedFormatResult.unavailable(plan_id, region_id, message))
        elif status == "error":
            if type(message) is not str or text is not _MISSING or provider is not _MISSING:
                msg = "error citry/formatEmbedded results require only a message"
                raise ValueError(msg)
            results.append(EmbeddedFormatResult.error(plan_id, region_id, message))
        else:
            msg = f"citry/formatEmbedded result has unknown status {status!r}"
            raise ValueError(msg)
    return results


def _format_component_assets_params(params: object) -> tuple[str, int, FormatScope, types.Position | None]:
    return _format_scope_params(params, method=FORMAT_COMPONENT_ASSETS_METHOD)


def _prepared_document_is_current(
    document: DocumentState | None,
    prepared: PreparedComponentAssets,
) -> bool:
    return bool(
        document is not None
        and document.uri == prepared.document_uri
        and document.version == prepared.document_version
        and document.source == prepared.document_source
    )


def _stale_embedded_response() -> dict[str, object]:
    return {
        "kind": "refused",
        "code": FORMAT_STALE_DOCUMENT,
        "message": "document changed while embedded formatting was in progress",
        "range": None,
    }


def _embedded_request_failure(error: Exception) -> dict[str, object]:
    detail = f"{type(error).__name__}: {error}"
    if FORMAT_STALE_DOCUMENT in str(error):
        return {
            "kind": "refused",
            "code": FORMAT_STALE_DOCUMENT,
            "message": detail,
            "range": None,
        }
    return {
        "kind": "refused",
        "code": FORMAT_PROVIDER_INVALID,
        "message": f"embedded formatting client request failed: {detail}",
        "range": None,
    }


def _with_embedded_capability(
    response: dict[str, object],
    capability: EmbeddedFormattingCapability | None,
) -> dict[str, object]:
    result = dict(response)
    result["embeddedFormatting"] = {
        "version": EMBEDDED_FORMATTING_VERSION,
        "languages": list(capability.languages) if capability is not None else [],
        "providerSelection": capability.provider_selection if capability is not None else None,
        "providerIdentity": capability.provider_identity if capability is not None else None,
        "providerVersion": capability.provider_version if capability is not None else None,
    }
    return result


def _log_format_notices(ls: CitryLanguageServer, response: dict[str, object]) -> None:
    notices = response.get("notices")
    if type(notices) is not list:
        return
    for notice in notices:
        if type(notice) is not dict:
            continue
        code = notice.get("code")
        message = notice.get("message")
        if type(code) is str and type(message) is str:
            ls.window_log_message(types.LogMessageParams(types.MessageType.Info, f"{code}: {message}"))


def _format_templates_params(params: object) -> tuple[str, int, FormatScope, types.Position | None]:
    return _format_scope_params(params, method=FORMAT_TEMPLATES_METHOD)


def _format_scope_params(
    params: object,
    *,
    method: str,
) -> tuple[str, int, FormatScope, types.Position | None]:
    if not _is_wire_object(params):
        msg = f"{method} params must be an object"
        raise JsonRpcInvalidParams(msg)
    text_document = _wire_field(params, "textDocument")
    scope_value = _wire_field(params, "scope")
    if not _is_wire_object(text_document) or not _is_wire_object(scope_value):
        msg = f"{method} requires textDocument and scope objects"
        raise JsonRpcInvalidParams(msg)
    uri = _wire_field(text_document, "uri")
    version = _wire_field(text_document, "version")
    if type(uri) is not str or not uri or type(version) is not int or version < 0:
        msg = f"{method} textDocument requires a URI and non-negative integer version"
        raise JsonRpcInvalidParams(msg)
    kind = _wire_field(scope_value, "kind")
    raw_position = _wire_field(scope_value, "position", default=_MISSING)
    if kind == "document" and raw_position is _MISSING:
        return uri, version, "document", None
    if kind != "position" or not _is_wire_object(raw_position):
        msg = f"{method} scope must be document or position"
        raise JsonRpcInvalidParams(msg)
    line = _wire_field(raw_position, "line")
    character = _wire_field(raw_position, "character")
    if type(line) is not int or line < 0 or type(character) is not int or character < 0:
        msg = f"{method} position requires non-negative integer line and character"
        raise JsonRpcInvalidParams(msg)
    return uri, version, "position", types.Position(line, character)


def _projection_request_params(
    params: object,
    *,
    label: str,
) -> tuple[str, int, types.Position]:
    """Validate one projection request after Pygls decodes its JSON objects."""
    if not _wire_object_has_exact_fields(params, frozenset({"textDocument", "position"})):
        raise JsonRpcInvalidParams(f"{label} parameters are invalid")
    text_document = _wire_field(params, "textDocument")
    position = _wire_field(params, "position")
    if not _wire_object_has_exact_fields(text_document, frozenset({"uri", "version"})):
        raise JsonRpcInvalidParams(f"{label} textDocument is invalid")
    uri = _wire_field(text_document, "uri")
    version = _wire_field(text_document, "version")
    if type(uri) is not str or type(version) is not int:
        raise JsonRpcInvalidParams(f"{label} identity is invalid")
    if not _wire_object_has_exact_fields(position, frozenset({"line", "character"})):
        raise JsonRpcInvalidParams(f"{label} position is invalid")
    line = _wire_field(position, "line")
    character = _wire_field(position, "character")
    if type(line) is not int or type(character) is not int or line < 0 or character < 0:
        raise JsonRpcInvalidParams(f"{label} position is invalid")
    return uri, version, types.Position(line, character)


def _is_wire_object(value: object) -> bool:
    value_type = type(value)
    return value_type is dict or (
        isinstance(value, tuple) and value_type.__module__ == "pygls.protocol" and value_type.__name__ == "Object"
    )


def _wire_object_has_exact_fields(value: object, expected: frozenset[str]) -> bool:
    """Keep custom request validation strict for raw and Pygls-decoded JSON."""
    if type(value) is dict:
        return frozenset(value) == expected
    if not _is_wire_object(value):
        return False
    fields = getattr(value, "_fields", ())
    return type(fields) is tuple and frozenset(fields) == expected


def _wire_field(value: object, name: str, *, default: object | None = None) -> object | None:
    if type(value) is dict:
        return value.get(name, default)
    return getattr(value, name, default)


def _workspace_path(params: types.InitializeParams) -> Path:
    return _path_from_uri(_workspace_uri(params))


def _workspace_uri(params: types.InitializeParams) -> str:
    if params.workspace_folders:
        return params.workspace_folders[0].uri
    if params.root_uri:
        return params.root_uri
    if params.root_path:
        return Path(params.root_path).absolute().as_uri()
    return Path.cwd().resolve().as_uri()


def _path_from_uri(uri: str) -> Path:
    path = file_uri_path(uri)
    if path is None:
        msg = f"Citry requires a file workspace URI, got {uri!r}"
        raise JsonRpcInvalidParams(msg)
    return path.resolve()


__all__ = [
    "RELOAD_METHOD",
    "STATUS_METHOD",
    "CitryLanguageServer",
    "format_component_assets_request",
    "format_document",
    "format_templates_request",
    "server",
]
