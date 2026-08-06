"""pygls transport adapter for the Citry analysis engine."""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import suppress
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.parse import unquote, urlparse

from lsprotocol import types
from pygls.exceptions import JsonRpcException, JsonRpcInvalidParams
from pygls.lsp.server import LanguageServer

from citry_core.template_formatter import EmbeddedFormatResult
from citry_lsp.engine import DocumentState, completion_result, definition, document_symbols, hover
from citry_lsp.formatting import (
    EmbeddedProviderRequest,
    FormatScope,
    PreparedComponentAssets,
    finish_component_assets,
    format_templates,
    prepare_component_assets,
)
from citry_lsp.project import ProjectState, load_project
from citry_lsp.protocol import (
    EMBEDDED_FORMATTING_VERSION,
    FORMAT_COMPONENT_ASSETS_METHOD,
    FORMAT_EMBEDDED_METHOD,
    FORMAT_TEMPLATES_METHOD,
    PROTOCOL_VERSION,
    SERVER_VERSION,
    EmbeddedFormattingCapability,
    ProjectStatus,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

STATUS_METHOD = "citry/status"
RELOAD_METHOD = "citry/reload"
_MISSING = object()
_EMBEDDED_REQUEST_TIMEOUT_SECONDS = 30.0
logger = logging.getLogger(__name__)


class CitryLanguageServer(LanguageServer):
    """Language server with one independent workspace and project registry."""

    def __init__(self) -> None:
        super().__init__("citry-lsp", SERVER_VERSION, text_document_sync_kind=types.TextDocumentSyncKind.Full)
        self.app: str | None = None
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

    def configure(self, params: types.InitializeParams) -> None:
        """Validate the client protocol and load the selected project generation."""
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
        self.project = _project_with_embedded_capability(
            load_project(self.workspace_path, self.app),
            self.embedded_formatting,
        )

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
        document = self.documents.get(uri)
        if document is None:
            document = DocumentState(uri, language_id, source, version)
            self.documents[uri] = document
        document.language_id = language_id
        document.update(source, version, self.project)
        self.publish(document)

    def reload_project(self) -> dict[str, object]:
        """Replace project state through a fresh worker and reanalyze documents."""
        self.project = _project_with_embedded_capability(
            load_project(self.workspace_path, self.app),
            self.embedded_formatting,
        )
        for document in self.documents.values():
            document.update(document.source, document.version, self.project)
            self.publish(document)
        self.protocol.notify(STATUS_METHOD, self.project.status.to_dict())
        return self.project.status.to_dict()


server = CitryLanguageServer()


@server.feature(types.INITIALIZE)
def initialize(ls: CitryLanguageServer, params: types.InitializeParams) -> None:
    """Capture initialization options before pygls builds capabilities."""
    ls.configure(params)


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
    selector = types.TextDocumentFilterLanguage(
        language="citry-html",
        scheme="file",
        pattern=types.RelativePattern(workspace_uri, "**/*"),
    )
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
def did_open(ls: CitryLanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    """Analyze a newly opened Citry or Python document."""
    document = params.text_document
    ls.update_document(document.uri, document.language_id, document.text, document.version)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: CitryLanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    """Analyze the full synchronized document content."""
    if not params.content_changes:
        return
    change = params.content_changes[-1]
    source = change.text
    previous = ls.documents.get(params.text_document.uri)
    language_id = previous.language_id if previous is not None else "python"
    ls.update_document(params.text_document.uri, language_id, source, params.text_document.version)


@server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
def did_close(ls: CitryLanguageServer, params: types.DidCloseTextDocumentParams) -> None:
    """Drop document state and clear its diagnostics."""
    ls.documents.pop(params.text_document.uri, None)
    ls.text_document_publish_diagnostics(types.PublishDiagnosticsParams(params.text_document.uri, ()))


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["<", "-", ".", " ", '"', "'", "{", ",", "#", "$"]),
)
def completion(ls: CitryLanguageServer, params: types.CompletionParams) -> types.CompletionList:
    """Complete Citry syntax, lexical bindings, and registry contracts."""
    document = ls.documents.get(params.text_document.uri)
    if document is None:
        return types.CompletionList(is_incomplete=False, items=())
    result = completion_result(document, params.position, ls.project)
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
def hover_feature(ls: CitryLanguageServer, params: types.HoverParams) -> types.Hover | None:
    """Show lexical bindings or catalog-backed component and input documentation."""
    document = ls.documents.get(params.text_document.uri)
    return hover(document, params.position, ls.project) if document is not None else None


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def definition_feature(ls: CitryLanguageServer, params: types.DefinitionParams) -> types.Location | None:
    """Navigate to exact lexical, component, and component-input declarations."""
    document = ls.documents.get(params.text_document.uri)
    return definition(document, params.position, ls.project, ls.documents) if document is not None else None


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
def watched_files(ls: CitryLanguageServer, params: types.DidChangeWatchedFilesParams) -> None:
    """Reload registry facts when project Python files change."""
    if ls.app is not None and any(change.uri.lower().endswith(".py") for change in params.changes):
        ls.reload_project()


@server.feature(STATUS_METHOD)
def status_request(ls: CitryLanguageServer, _params: object | None = None) -> dict[str, object]:
    """Return the current interpreter, app, protocol, and confidence mode."""
    return ls.project.status.to_dict()


@server.feature(RELOAD_METHOD)
def reload_request(ls: CitryLanguageServer, _params: object | None = None) -> dict[str, object]:
    """Reload the configured app through a fresh worker."""
    return ls.reload_project()


@server.feature(FORMAT_TEMPLATES_METHOD)
def format_templates_request(ls: CitryLanguageServer, params: object) -> dict[str, object]:
    """Format current Citry template text through the versioned custom request."""
    uri, version, scope, position = _format_templates_params(params)
    document = ls.documents.get(uri)
    if document is None:
        return {
            "kind": "refused",
            "code": "citry.format.stale-document",
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
                "code": "citry.format.stale-document",
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
            "code": "citry.format.provider-invalid",
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
        "code": "citry.format.stale-document",
        "message": "document changed while embedded formatting was in progress",
        "range": None,
    }


def _embedded_request_failure(error: Exception) -> dict[str, object]:
    detail = f"{type(error).__name__}: {error}"
    if "citry.format.stale-document" in str(error):
        return {
            "kind": "refused",
            "code": "citry.format.stale-document",
            "message": detail,
            "range": None,
        }
    return {
        "kind": "refused",
        "code": "citry.format.provider-invalid",
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


def _is_wire_object(value: object) -> bool:
    value_type = type(value)
    return value_type is dict or (value_type.__module__ == "pygls.protocol" and value_type.__name__ == "Object")


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
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        msg = f"Citry requires a file workspace URI, got {uri!r}"
        raise JsonRpcInvalidParams(msg)
    path = unquote(parsed.path)
    if parsed.netloc:
        path = f"//{parsed.netloc}{path}"
    return Path(path).resolve()


__all__ = [
    "RELOAD_METHOD",
    "STATUS_METHOD",
    "CitryLanguageServer",
    "format_component_assets_request",
    "format_document",
    "format_templates_request",
    "server",
]
