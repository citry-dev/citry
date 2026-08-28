"""Run the supported ``ty`` language server behind a small Citry adapter."""

from __future__ import annotations

import ast
import asyncio
import importlib.metadata
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from contextlib import suppress
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, NoReturn

from lsprotocol import types
from pygls.client import JsonRPCClient

from citry_lsp.uri import canonical_document_uri, file_uri_path

TY_VERSION = "0.0.73"
_REQUEST_TIMEOUT_SECONDS = 5.0
# VS Code gives the language server 1.5s to stop before terminating it. Keep
# the complete graceful -> client stop -> terminate -> kill escalation below
# that outer bound so Citry reaps ty itself rather than orphaning the child.
_CLIENT_STOP_TIMEOUT_SECONDS = 0.35
_PROCESS_STOP_TIMEOUT_SECONDS = 0.2


class TyUnavailableError(RuntimeError):
    """The pinned analyzer cannot safely answer requests in this environment."""


@dataclass(frozen=True, slots=True)
class TyDocument:
    """One current Python document forwarded from the editor or shadow builder."""

    uri: str
    source: str


@dataclass(frozen=True, slots=True)
class TyCompletion:
    """One completion candidate with only stable LSP presentation fields."""

    label: str
    detail: str | None
    documentation: types.MarkupContent | None
    kind: types.CompletionItemKind | None
    sort_text: str | None


@dataclass(frozen=True, slots=True)
class TyHover:
    """Analyzer hover content and its exact virtual-document range."""

    contents: types.MarkupContent
    range: types.Range | None


@dataclass(frozen=True, slots=True)
class TyDiagnostic:
    """One pull diagnostic before Citry validates its authored range."""

    range: types.Range
    message: str
    severity: types.DiagnosticSeverity | None
    code: str | int | None
    source: str | None
    href: str | None


class TyAnalyzer:
    """Own one incremental analyzer child for a Citry workspace."""

    def __init__(
        self,
        workspace: Path,
        *,
        executable: Path | None = None,
        python_prefix: Path | None = None,
    ) -> None:
        self.workspace = workspace.resolve()
        self._executable = executable
        # citry-lsp itself is launched by the selected interpreter. Passing
        # that interpreter's prefix explicitly keeps ty from rediscovering a
        # different ambient or workspace environment.
        self._python_prefix = (python_prefix or Path(sys.prefix)).resolve()
        self._client: JsonRPCClient | None = None
        self._documents: dict[str, tuple[str, int]] = {}
        self._lock = asyncio.Lock()
        self._active_requests: set[asyncio.Task[Any]] = set()
        self._failed: str | None = None
        self._closed = False

    @property
    def failure(self) -> str | None:
        """Return the stable degradation reason after startup or a child failure."""
        return self._failed

    async def completion(
        self,
        document: TyDocument,
        position: types.Position,
        *,
        synchronized: tuple[TyDocument, ...] = (),
    ) -> tuple[TyCompletion, ...]:
        """Return safe member candidates from one exact virtual position."""
        async with self._lock:
            client = await self._ready_client()
            await self._sync_documents(client, (*synchronized, document))
            raw = await self._request(
                client,
                types.TEXT_DOCUMENT_COMPLETION,
                types.CompletionParams(types.TextDocumentIdentifier(document.uri), position),
            )
        if raw is None:
            return ()
        items = raw if isinstance(raw, list) else _field(raw, "items")
        if not isinstance(items, (list, tuple)):
            await self._invalid_response("completion")
        candidates: list[tuple[object, str, str | None]] = []
        for item in items:
            label = _field(item, "label")
            detail = _optional_string(_field(item, "detail"))
            if not isinstance(label, str):
                await self._invalid_response("completion item")
            if label.startswith("_"):
                continue
            candidates.append((item, label, detail))
        if not candidates:
            return ()

        # Attribute definitions identify the runtime owner even when the
        # receiver is a call, cast, subscript, or conditional expression.
        special_labels = {
            "mro",
            "format",
            "format_map",
            "gi_code",
            "gi_frame",
            "cr_code",
            "cr_frame",
            "ag_code",
            "ag_frame",
        }
        probe_labels = {candidates[0][1], *(label for _, label, _ in candidates if label in special_labels)}
        if "mro" in probe_labels:
            probe_labels.add("__mro__")
        definition_results: dict[str, object] = {}
        async with self._lock:
            client = await self._ready_client()
            try:
                for label in probe_labels:
                    probe = _completion_member_probe(document, position, label)
                    if probe is None:
                        continue
                    probe_document, probe_position = probe
                    await self._sync_documents(client, (*synchronized, probe_document))
                    definition_results[label] = await self._request(
                        client,
                        types.TEXT_DOCUMENT_DEFINITION,
                        types.DefinitionParams(types.TextDocumentIdentifier(probe_document.uri), probe_position),
                    )
            finally:
                if self._client is client:
                    await self._sync_documents(client, (*synchronized, document))

        owners: dict[str, str | None] = {}
        for label, result in definition_results.items():
            valid, owner = _definition_owner(result)
            if not valid:
                await self._invalid_response("completion member definition")
            owners[label] = owner
        receiver_owner = owners.get(candidates[0][1])
        retained: list[TyCompletion] = []
        for item, label, detail in candidates:
            if not _safe_completion_item(
                label,
                detail,
                receiver_is_type=owners.get("__mro__") == "type",
                receiver_owner=receiver_owner,
                member_owner=owners.get(label),
            ):
                continue
            retained.append(
                TyCompletion(
                    label=label,
                    detail=detail,
                    documentation=_markup(_field(item, "documentation")),
                    kind=_completion_kind(_field(item, "kind")),
                    sort_text=_optional_string(_field(item, "sortText", _field(item, "sort_text"))),
                )
            )
        return tuple(retained)

    async def hover(
        self,
        document: TyDocument,
        position: types.Position,
        *,
        synchronized: tuple[TyDocument, ...] = (),
    ) -> TyHover | None:
        """Return structured type information at one virtual position."""
        async with self._lock:
            client = await self._ready_client()
            await self._sync_documents(client, (*synchronized, document))
            raw = await self._request(
                client,
                types.TEXT_DOCUMENT_HOVER,
                types.HoverParams(types.TextDocumentIdentifier(document.uri), position),
            )
        if raw is None:
            return None
        contents = _markup(_field(raw, "contents"))
        if contents is None:
            await self._invalid_response("hover")
        raw_range = _field(raw, "range")
        hover_range = _range(raw_range)
        if raw_range is not None and hover_range is None:
            await self._invalid_response("hover range")
        return TyHover(contents, hover_range)

    async def definition(
        self,
        document: TyDocument,
        position: types.Position,
        *,
        synchronized: tuple[TyDocument, ...] = (),
    ) -> tuple[types.Location, ...]:
        """Return analyzer definitions without accepting location links or edits."""
        async with self._lock:
            client = await self._ready_client()
            await self._sync_documents(client, (*synchronized, document))
            raw = await self._request(
                client,
                types.TEXT_DOCUMENT_DEFINITION,
                types.DefinitionParams(types.TextDocumentIdentifier(document.uri), position),
            )
        values = raw if isinstance(raw, list) else [raw] if raw is not None else []
        locations: list[types.Location] = []
        for value in values:
            if _field(value, "targetUri", _field(value, "target_uri")) is not None:
                # LocationLink is valid LSP, but Citry intentionally accepts
                # only exact Location records for conservative source mapping.
                continue
            uri = _field(value, "uri")
            location_range = _range(_field(value, "range"))
            if not isinstance(uri, str) or location_range is None:
                await self._invalid_response("definition")
            locations.append(types.Location(uri, location_range))
        return tuple(locations)

    async def type_definition(
        self,
        document: TyDocument,
        position: types.Position,
        *,
        synchronized: tuple[TyDocument, ...] = (),
    ) -> tuple[types.Location, ...]:
        """Return analyzer type definitions as exact Location records."""
        async with self._lock:
            client = await self._ready_client()
            await self._sync_documents(client, (*synchronized, document))
            raw = await self._request(
                client,
                types.TEXT_DOCUMENT_TYPE_DEFINITION,
                types.TypeDefinitionParams(types.TextDocumentIdentifier(document.uri), position),
            )
        values = raw if isinstance(raw, list) else [raw] if raw is not None else []
        locations: list[types.Location] = []
        for value in values:
            if _field(value, "targetUri", _field(value, "target_uri")) is not None:
                # Generated-source mapping requires exact Location ranges, so
                # a LocationLink cannot be accepted partially.
                return ()
            uri = _field(value, "uri")
            location_range = _range(_field(value, "range"))
            if not isinstance(uri, str) or location_range is None:
                await self._invalid_response("type definition")
            locations.append(types.Location(uri, location_range))
        return tuple(locations)

    async def diagnostics(
        self,
        document: TyDocument,
        *,
        synchronized: tuple[TyDocument, ...] = (),
    ) -> tuple[TyDiagnostic, ...]:
        """Pull current diagnostics so Citry can retain only authored expressions."""
        async with self._lock:
            client = await self._ready_client()
            await self._sync_documents(client, (*synchronized, document))
            raw = await self._request(
                client,
                types.TEXT_DOCUMENT_DIAGNOSTIC,
                types.DocumentDiagnosticParams(types.TextDocumentIdentifier(document.uri)),
            )
        items = _field(raw, "items")
        if not isinstance(items, (list, tuple)):
            await self._invalid_response("diagnostic report")
        retained: list[TyDiagnostic] = []
        for item in items:
            diagnostic_range = _range(_field(item, "range"))
            message = _field(item, "message")
            if diagnostic_range is None or not isinstance(message, str):
                await self._invalid_response("diagnostic")
            code = _field(item, "code")
            description = _field(item, "codeDescription", _field(item, "code_description"))
            href = _field(description, "href")
            retained.append(
                TyDiagnostic(
                    diagnostic_range,
                    message,
                    _diagnostic_severity(_field(item, "severity")),
                    code if isinstance(code, (str, int)) else None,
                    _optional_string(_field(item, "source")),
                    href if isinstance(href, str) else None,
                )
            )
        return tuple(retained)

    async def signature_help(
        self,
        document: TyDocument,
        position: types.Position,
        *,
        synchronized: tuple[TyDocument, ...] = (),
    ) -> types.SignatureHelp | None:
        """Return structured call signatures at one virtual position."""
        async with self._lock:
            client = await self._ready_client()
            await self._sync_documents(client, (*synchronized, document))
            raw = await self._request(
                client,
                types.TEXT_DOCUMENT_SIGNATURE_HELP,
                types.SignatureHelpParams(types.TextDocumentIdentifier(document.uri), position),
            )
        if raw is None:
            return None
        raw_signatures = _field(raw, "signatures", ())
        if not isinstance(raw_signatures, (list, tuple)):
            await self._invalid_response("signature help")
        signatures: list[types.SignatureInformation] = []
        for raw_signature in raw_signatures:
            label = _field(raw_signature, "label")
            if not isinstance(label, str):
                await self._invalid_response("signature")
            raw_parameters = _field(raw_signature, "parameters")
            parameters: list[types.ParameterInformation] | None = None
            if raw_parameters is not None and not isinstance(raw_parameters, (list, tuple)):
                await self._invalid_response("signature parameters")
            if isinstance(raw_parameters, (list, tuple)):
                parameters = []
                for raw_parameter in raw_parameters:
                    parameter_label = _parameter_label(_field(raw_parameter, "label"))
                    if parameter_label is None:
                        await self._invalid_response("signature parameter")
                    parameters.append(
                        types.ParameterInformation(
                            parameter_label,
                            _markup_or_string(_field(raw_parameter, "documentation")),
                        )
                    )
            signatures.append(
                types.SignatureInformation(
                    label,
                    _markup_or_string(_field(raw_signature, "documentation")),
                    parameters,
                    _optional_int(_field(raw_signature, "activeParameter")),
                )
            )
        if not signatures:
            return None
        return types.SignatureHelp(
            signatures,
            _optional_int(_field(raw, "activeSignature")),
            _optional_int(_field(raw, "activeParameter")),
        )

    async def close(self) -> None:
        """Shut down the child without leaving a process behind on editor exit."""
        self._closed = True
        current = asyncio.current_task()
        for request in tuple(self._active_requests):
            if request is not current:
                request.cancel()
        async with self._lock:
            client = self._client
            self._client = None
            self._documents.clear()
            if client is None:
                return
            await _stop_client_cancellation_safe(client, graceful=True)

    async def close_document(self, uri: str) -> None:
        """Let the analyzer return to disk state after an editor buffer closes."""
        uri = canonical_document_uri(uri)
        async with self._lock:
            client = self._client
            if client is None or uri not in self._documents:
                return
            client.protocol.notify(
                types.TEXT_DOCUMENT_DID_CLOSE,
                types.DidCloseTextDocumentParams(types.TextDocumentIdentifier(uri)),
            )
            self._documents.pop(uri, None)

    async def _ready_client(self) -> JsonRPCClient:
        if self._closed:
            raise TyUnavailableError("this Python expression analyzer generation is closed")
        if self._failed is not None:
            raise TyUnavailableError(self._failed)
        if self._client is not None and not self._client.stopped:
            return self._client
        client: JsonRPCClient | None = None
        operation = asyncio.current_task()
        if operation is not None:
            self._active_requests.add(operation)
        try:
            executable = await asyncio.to_thread(self._validated_executable)
            client = _configured_client(self._python_prefix)
            await client.start_io(str(executable), "server", cwd=self.workspace)
            params = _initialize_params(self.workspace, self._python_prefix)
            await _bounded_client_request(client, types.INITIALIZE, params, _REQUEST_TIMEOUT_SECONDS)
            client.protocol.notify(types.INITIALIZED, types.InitializedParams())
        except asyncio.CancelledError:
            if client is not None:
                await _stop_client_cancellation_safe(client, graceful=False)
            raise
        except Exception as exc:
            if client is not None:
                await _stop_client_cancellation_safe(client, graceful=False)
            self._failed = f"Python expression analysis is unavailable: {exc}"
            raise TyUnavailableError(self._failed) from exc
        finally:
            if operation is not None:
                self._active_requests.discard(operation)
        self._client = client
        return client

    def _validated_executable(self) -> Path:
        executable = self._executable or _installed_ty_executable()
        return _validated_ty_executable(executable)

    async def _sync_documents(self, client: JsonRPCClient, documents: tuple[TyDocument, ...]) -> None:
        # Full document changes keep this adapter independent of ty's chosen
        # incremental synchronization granularity.
        for document in documents:
            current = self._documents.get(document.uri)
            if current is None:
                version = 1
                client.protocol.notify(
                    types.TEXT_DOCUMENT_DID_OPEN,
                    types.DidOpenTextDocumentParams(
                        types.TextDocumentItem(document.uri, "python", version, document.source)
                    ),
                )
            elif current[0] != document.source:
                version = current[1] + 1
                client.protocol.notify(
                    types.TEXT_DOCUMENT_DID_CHANGE,
                    types.DidChangeTextDocumentParams(
                        types.VersionedTextDocumentIdentifier(version=version, uri=document.uri),
                        [types.TextDocumentContentChangeWholeDocument(document.source)],
                    ),
                )
            else:
                continue
            self._documents[document.uri] = (document.source, version)

    async def _request(self, client: JsonRPCClient, method: str, params: object) -> Any:
        if self._closed:
            raise TyUnavailableError("this Python expression analyzer generation is closed")
        operation = asyncio.current_task()
        if operation is not None:
            self._active_requests.add(operation)
        try:
            return await _bounded_client_request(client, method, params, _REQUEST_TIMEOUT_SECONDS)
        except asyncio.CancelledError:
            # Cancellation belongs to this editor request, not to the shared
            # analyzer generation. The bounded request leaves its pygls
            # future alive to consume a possible late response safely.
            raise
        except Exception as exc:
            self._client = None
            self._documents.clear()
            await _stop_client_cancellation_safe(client, graceful=False)
            self._failed = f"Python expression analysis stopped responding: {exc}"
            raise TyUnavailableError(self._failed) from exc
        finally:
            if operation is not None:
                self._active_requests.discard(operation)

    async def _invalid_response(self, response_kind: str) -> NoReturn:
        """Disable one analyzer generation after a malformed protocol result."""
        async with self._lock:
            client = self._client
            self._client = None
            self._documents.clear()
            self._failed = f"Python expression analysis received an invalid {response_kind} response"
            if client is not None:
                await _stop_client_cancellation_safe(client, graceful=False)
        raise TyUnavailableError(self._failed)


@lru_cache(maxsize=4)
def _validated_ty_executable(executable: Path) -> Path:
    """Validate each installed analyzer binary once per language-server process."""
    # The environment cannot safely replace this distribution underneath a
    # running server, so every workspace analyzer can share the same probe.
    try:
        installed = importlib.metadata.version("ty")
    except importlib.metadata.PackageNotFoundError as exc:
        raise TyUnavailableError(f"ty {TY_VERSION} is not installed") from exc
    if installed != TY_VERSION:
        raise TyUnavailableError(f"ty {TY_VERSION} is required, but {installed} is installed")
    if not executable.is_file():
        raise TyUnavailableError(f"the ty executable is missing at {executable}")
    completed = subprocess.run(
        [str(executable), "version", "--output-format", "json"],
        capture_output=True,
        check=False,
        text=True,
        timeout=2.0,
    )
    try:
        reported = json.loads(completed.stdout).get("version")
    except (AttributeError, json.JSONDecodeError) as exc:
        raise TyUnavailableError("ty returned an invalid version response") from exc
    if completed.returncode != 0 or reported != TY_VERSION:
        raise TyUnavailableError(f"the ty executable reports unsupported version {reported!r}")
    return executable


async def _stop_client(client: JsonRPCClient, *, graceful: bool) -> None:
    """Bound child shutdown for normal exit and partially started failures."""
    if graceful:
        with suppress(Exception):
            await _bounded_client_request(client, types.SHUTDOWN, None, _CLIENT_STOP_TIMEOUT_SECONDS)
    with suppress(Exception):
        client.protocol.notify(types.EXIT)
    try:
        await asyncio.wait_for(client.stop(), _CLIENT_STOP_TIMEOUT_SECONDS)
        return
    except asyncio.TimeoutError:
        pass
    except (AttributeError, OSError, RuntimeError):
        pass

    # pygls waits for its stdio child but does not terminate it. Escalate only
    # after the protocol shutdown bound so reloads cannot orphan a hung ty.
    process = getattr(client, "_server", None)
    if process is None or getattr(process, "returncode", None) is not None:
        return
    with suppress(ProcessLookupError, PermissionError):
        process.terminate()
    try:
        await asyncio.wait_for(process.wait(), _PROCESS_STOP_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        with suppress(ProcessLookupError, PermissionError):
            process.kill()
        with suppress(Exception):
            await asyncio.wait_for(process.wait(), _PROCESS_STOP_TIMEOUT_SECONDS)


async def _stop_client_cancellation_safe(client: JsonRPCClient, *, graceful: bool) -> None:
    """Finish child cleanup before propagating cancellation to the caller."""
    stopping = asyncio.create_task(_stop_client(client, graceful=graceful))
    cancellation: asyncio.CancelledError | None = None
    while not stopping.done():
        try:
            await asyncio.shield(stopping)
        except asyncio.CancelledError as exc:
            cancellation = exc
    await stopping
    if cancellation is not None:
        raise cancellation


async def _bounded_client_request(
    client: JsonRPCClient,
    method: str,
    params: object | None,
    timeout: float,
) -> Any:
    """
    Await one child request without cancelling pygls's response future.

    Pygls dispatches a late response by completing the original future. If
    ``asyncio.wait_for`` cancels that future first, the protocol later raises
    ``InvalidStateError`` and can strand reader cleanup. Shielding preserves
    the future, while the explicit cancellation notification lets ty stop
    obsolete work promptly.
    """
    request_id = str(uuid.uuid4())
    pending = asyncio.ensure_future(client.protocol.send_request_async(method, params, msg_id=request_id))
    try:
        return await asyncio.wait_for(asyncio.shield(pending), timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        with suppress(Exception):
            client.protocol.notify(types.CANCEL_REQUEST, types.CancelParams(id=request_id))
        pending.add_done_callback(_consume_late_response)
        raise


def _consume_late_response(future: asyncio.Future[Any]) -> None:
    """Observe a response that arrived after its Citry request ended."""
    with suppress(asyncio.CancelledError, Exception):
        future.result()


def virtual_document_uri(source_file: Path, identity: str) -> str:
    """Return a deterministic unsaved sibling URI for one component consumer."""
    safe_identity = "".join(char if char.isalnum() else "_" for char in identity)[:48]
    # A valid module stem lets ty assign the sibling to the source package, so
    # copied relative imports retain their ordinary package context.
    name = f"__citry_{source_file.stem}_{safe_identity}.py"
    return source_file.resolve().with_name(name).as_uri()


def position_at_offset(source: str, offset: int) -> types.Position:
    """Convert a Python string index to an LSP UTF-16 position."""
    bounded = min(max(offset, 0), len(source))
    before = source[:bounded]
    line = before.count("\n")
    line_text = before.rsplit("\n", 1)[-1]
    return types.Position(line, len(line_text.encode("utf-16-le")) // 2)


def offset_at_position(source: str, position: types.Position) -> int | None:
    """Convert an LSP UTF-16 position to a Python string index exactly."""
    if position.line < 0 or position.character < 0:
        return None
    lines = source.splitlines(keepends=True)
    if position.line >= len(lines):
        if position.line == 0 and not lines and position.character == 0:
            return 0
        return None
    prefix = sum(len(line) for line in lines[: position.line])
    line = lines[position.line].removesuffix("\n").removesuffix("\r")
    units = 0
    for index, char in enumerate(line):
        if units == position.character:
            return prefix + index
        units += len(char.encode("utf-16-le")) // 2
        if units > position.character:
            return None
    return prefix + len(line) if units == position.character else None


def _configured_client(python_prefix: Path) -> JsonRPCClient:
    client = JsonRPCClient()
    workspace_options = _ty_workspace_options(python_prefix)

    @client.feature("workspace/configuration")
    def configuration(*args: object) -> list[dict[str, object]]:
        params = args[-1] if args else None
        items = _field(params, "items", ())
        return [workspace_options for _ in items] if isinstance(items, (list, tuple)) else []

    @client.feature("client/registerCapability")
    def register_capability(*_args: object) -> None:
        return None

    @client.feature("window/workDoneProgress/create")
    def create_progress(*_args: object) -> None:
        return None

    @client.feature("workspace/workspaceFolders")
    def workspace_folders(*_args: object) -> list[object]:
        return []

    @client.feature(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    def ignore_push_diagnostics(*_args: object) -> None:
        # Citry uses pull diagnostics so a shadow update cannot publish a
        # generated-file diagnostic directly to the user's editor.
        return None

    @client.feature(types.WINDOW_LOG_MESSAGE)
    def ignore_log(*_args: object) -> None:
        return None

    @client.feature(types.WINDOW_SHOW_MESSAGE)
    def ignore_message(*_args: object) -> None:
        return None

    return client


def _initialize_params(workspace: Path, python_prefix: Path) -> types.InitializeParams:
    workspace_uri = workspace.as_uri()
    return types.InitializeParams(
        capabilities=types.ClientCapabilities(
            workspace=types.WorkspaceClientCapabilities(configuration=True, workspace_folders=True),
            text_document=types.TextDocumentClientCapabilities(
                completion=types.CompletionClientCapabilities(
                    completion_item=types.ClientCompletionItemOptions(
                        documentation_format=[types.MarkupKind.Markdown, types.MarkupKind.PlainText]
                    )
                ),
                definition=types.DefinitionClientCapabilities(),
                type_definition=types.TypeDefinitionClientCapabilities(),
                diagnostic=types.DiagnosticClientCapabilities(dynamic_registration=False),
                hover=types.HoverClientCapabilities(
                    content_format=[types.MarkupKind.Markdown, types.MarkupKind.PlainText]
                ),
                signature_help=types.SignatureHelpClientCapabilities(),
            ),
        ),
        process_id=os.getpid(),
        root_uri=workspace_uri,
        workspace_folders=[types.WorkspaceFolder(workspace_uri, workspace.name or "workspace")],
        initialization_options=_ty_workspace_options(python_prefix),
    )


def _ty_workspace_options(python_prefix: Path) -> dict[str, object]:
    """Pin ty module resolution to the interpreter running citry-lsp."""
    return {
        "configuration": {
            "environment": {
                "python": str(python_prefix),
            }
        }
    }


def _installed_ty_executable() -> Path:
    scripts = Path(sysconfig.get_path("scripts"))
    suffix = ".exe" if sys.platform == "win32" else ""
    return scripts / f"ty{suffix}"


def _safe_completion_item(
    label: str,
    detail: str | None = None,
    *,
    receiver_is_type: bool = False,
    receiver_owner: str | None = None,
    member_owner: str | None = None,
) -> bool:
    if label.startswith("_"):
        return False
    if label == "mro" and receiver_is_type:
        return False
    if (
        label == "mro"
        and detail is not None
        and ("bound method <class '" in detail or detail.startswith("bound method type["))
    ):
        return False
    if receiver_owner in {"CodeType", "FrameType", "TracebackType"}:
        return False
    unsafe_by_receiver = {
        "type": {"mro"},
        "str": {"format", "format_map"},
        "GeneratorType": {"gi_code", "gi_frame"},
        "CoroutineType": {"cr_code", "cr_frame"},
        "AsyncGeneratorType": {"ag_code", "ag_frame"},
    }
    return label not in unsafe_by_receiver.get(member_owner or "", ())


def _completion_member_probe(
    document: TyDocument,
    position: types.Position,
    label: str,
) -> tuple[TyDocument, types.Position] | None:
    """Insert one candidate so ty can resolve the exact attribute definition."""
    if not label.isidentifier():
        return None
    cursor = offset_at_position(document.source, position)
    if cursor is None:
        return None
    start = cursor
    while start > 0 and (document.source[start - 1].isalnum() or document.source[start - 1] == "_"):
        start -= 1
    end = cursor
    while end < len(document.source) and (document.source[end].isalnum() or document.source[end] == "_"):
        end += 1
    probe_source = f"{document.source[:start]}{label}{document.source[end:]}"
    probe_position = position_at_offset(probe_source, start + len(label) - 1)
    return TyDocument(document.uri, probe_source), probe_position


def _definition_owner(raw: object) -> tuple[bool, str | None]:
    """Return the enclosing typeshed class for exact definition locations."""
    values = raw if isinstance(raw, list) else [raw] if raw is not None else []
    owners: set[str] = set()
    for value in values:
        uri = _field(value, "targetUri", _field(value, "target_uri", _field(value, "uri")))
        range_value = _field(value, "targetRange", _field(value, "target_range", _field(value, "range")))
        location_range = _range(range_value)
        if not isinstance(uri, str) or location_range is None:
            return False, None
        owner = _typeshed_class_at(uri, location_range.start.line + 1)
        if owner is not None:
            owners.add(owner)
    return True, next(iter(owners)) if len(owners) == 1 else None


@lru_cache(maxsize=16)
def _typeshed_classes(path: str) -> tuple[tuple[int, int, str], ...]:
    """Index class line spans from one pinned typeshed source file."""
    try:
        module = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return ()
    classes = [
        (node.lineno, node.end_lineno, node.name)
        for node in ast.walk(module)
        if isinstance(node, ast.ClassDef) and node.end_lineno is not None
    ]
    return tuple(classes)


def _typeshed_class_at(uri: str, line: int) -> str | None:
    """Resolve a ty-vendored typeshed location to its enclosing class."""
    if "/ty/vendored/typeshed/" not in uri or "/stdlib/" not in uri:
        return None
    path = file_uri_path(uri)
    if path is None:
        return None
    candidates = [item for item in _typeshed_classes(str(path)) if item[0] <= line <= item[1]]
    return min(candidates, key=lambda item: item[1] - item[0])[2] if candidates else None


def _field(value: object, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None


def _markup_or_string(value: object) -> str | types.MarkupContent | None:
    return value if isinstance(value, str) else _markup(value)


def _parameter_label(value: object) -> str | tuple[int, int] | None:
    if isinstance(value, str):
        return value
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(isinstance(item, int) and item >= 0 for item in value)
    ):
        return value[0], value[1]
    return None


def _markup(value: object) -> types.MarkupContent | None:
    if isinstance(value, str):
        return types.MarkupContent(types.MarkupKind.PlainText, value)
    kind = _field(value, "kind")
    content = _field(value, "value")
    if kind in {types.MarkupKind.Markdown, types.MarkupKind.PlainText} and isinstance(content, str):
        return types.MarkupContent(kind, content)
    return None


def _position(value: object) -> types.Position | None:
    line = _field(value, "line")
    character = _field(value, "character")
    if isinstance(line, int) and isinstance(character, int) and line >= 0 and character >= 0:
        return types.Position(line, character)
    return None


def _range(value: object) -> types.Range | None:
    start = _position(_field(value, "start"))
    end = _position(_field(value, "end"))
    return types.Range(start, end) if start is not None and end is not None else None


def _completion_kind(value: object) -> types.CompletionItemKind | None:
    try:
        return types.CompletionItemKind(value) if isinstance(value, int) else None
    except ValueError:
        return None


def _diagnostic_severity(value: object) -> types.DiagnosticSeverity | None:
    try:
        return types.DiagnosticSeverity(value) if isinstance(value, int) else None
    except ValueError:
        return None


__all__ = [
    "TY_VERSION",
    "TyAnalyzer",
    "TyCompletion",
    "TyDiagnostic",
    "TyDocument",
    "TyHover",
    "TyUnavailableError",
    "offset_at_position",
    "position_at_offset",
    "virtual_document_uri",
]
