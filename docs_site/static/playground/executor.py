"""Execute one visitor-authored module inside the disposable Pyodide Worker."""

# The Worker intentionally executes visitor code and catches control-flow
# exceptions at its boundary.
# ruff: noqa: BLE001, S102

from __future__ import annotations

import ast
import contextlib
import dataclasses
import inspect
import io
import json
import linecache
import logging
import secrets
import sys
import traceback
from types import ModuleType
from typing import Any

import citry_ui
from citry import Citry, CitryElement, CitryRender, Component, ComponentLike, citry
from citry.component_like import _resolve_component_like
from citry.ext.events import EventRequest, EventsDispatcher, TransportContext
from citry.util.routing import RouteHeaders, RouteRequest, RouteResponse, match_route

PLAYGROUND_FILENAME = "<playground>"
PLAYGROUND_MODULE_NAME = "__playground__"
MAX_STREAM_CHARS = 65_536
MAX_TRACEBACK_CHARS = 16_384
MAX_MESSAGE_CHARS = 4_096
MAX_ASSET_PATHS = 32
MAX_ASSET_PATH_BYTES = 512
MAX_ASSET_BYTES = 1024 * 1024
MAX_ASSET_BATCH_BYTES = 4 * 1024 * 1024
MAX_CATALOG_BYTES = 256 * 1024
PLAYGROUND_EVENT_PATH = "/playground/events"
PLAYGROUND_ASSET_PREFIX = "/__citry_playground__"
SUPPORTED_EVENT_ACTIONS = frozenset({"data", "event", "render", "state"})
_ALLOWED_ASSET_ROUTES = frozenset(
    {
        ("cache/{class_id}.{vars_hash}.{script_type}", "citry_cached_script_vars"),
        ("cache/{class_id}.{script_type}", "citry_cached_script"),
        ("asset/{file_name}", "citry_asset"),
        ("citry.js", "citry_client_runtime"),
        ("ext/events/runtime.js", "citry_events_runtime"),
    }
)
_ALLOWED_ASSET_CONTENT_TYPES = frozenset({"text/css", "text/javascript"})


@dataclasses.dataclass
class _RuntimeState:
    namespace: dict[str, Any] | None = None
    run_id: int | None = None


_runtime_state = _RuntimeState()
_dispatcher = EventsDispatcher()

# The default Citry engine belongs only to this disposable Worker. Give it a
# per-Worker secret so visitor components can use ordinary signed State without
# adding playground-only setup to their module.
citry.settings = dataclasses.replace(
    citry.settings,
    secret=[secrets.token_urlsafe(32)],
    autodiscover=False,
)
citry.set_mounted_prefix(PLAYGROUND_ASSET_PREFIX)

# Event exceptions are teaching feedback in this local-only runtime. Debug
# mode includes the exception type and message in the structured handler error;
# Citry still never sends a traceback over the Events protocol.
logging.getLogger("citry").setLevel(logging.DEBUG)


class PreviewContractError(Exception):
    kind = "preview_contract"

    def __init__(
        self,
        message: str,
        *,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message)
        self.line = line
        self.column = column


class MissingPreviewError(PreviewContractError):
    kind = "missing_preview"


class NonePreviewError(PreviewContractError):
    kind = "none_preview"


class UnsupportedPreviewTypeError(PreviewContractError):
    kind = "unsupported_preview_type"


class TopLevelAwaitError(PreviewContractError):
    kind = "top_level_await"


def _bounded(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit] + "\n[output truncated]", True


def _normalize_preview(value: object) -> str:
    # Visitor code may change the default engine. The host prefix remains a
    # playground contract so every document and event fragment names assets alike.
    citry.set_mounted_prefix(PLAYGROUND_ASSET_PREFIX)
    if isinstance(value, str):
        return str(value)
    if isinstance(value, CitryElement):
        return str(value)
    if isinstance(value, CitryRender):
        return value.serialize()
    if isinstance(value, ComponentLike):
        return str(_resolve_component_like(value, citry))
    if value is None:
        raise NonePreviewError(
            "The preview expression returned None. End the module with HTML, a CitryElement, a ComponentLike, "
            "or a CitryRender."
        )
    raise UnsupportedPreviewTypeError(
        f"Cannot preview {type(value).__name__}. End the module with HTML, a CitryElement, a ComponentLike, "
        "or a CitryRender."
    )


def _preview_expression(tree: ast.Module) -> ast.Expr | None:
    if not tree.body or not isinstance(tree.body[-1], ast.Expr):
        return None
    last = tree.body[-1]
    if len(tree.body) == 1 and isinstance(last.value, ast.Constant) and isinstance(last.value.value, str):
        return None
    return last


def _fresh_private_name(
    base: str,
    source: str,
    *,
    reserved: set[str] | None = None,
) -> str:
    reserved = reserved or set()
    candidate = base
    suffix = 0
    while candidate in source or candidate in reserved:
        suffix += 1
        candidate = f"{base}_{suffix}"
    return candidate


def _rewrite_final_expression(
    tree: ast.Module,
    expression: ast.Expr,
    *,
    result_name: str,
    normalizer_name: str,
) -> None:
    normalizer = ast.Name(id=normalizer_name, ctx=ast.Load())
    ast.copy_location(normalizer, expression.value)
    call = ast.Call(func=normalizer, args=[expression.value], keywords=[])
    ast.copy_location(call, expression.value)
    target = ast.Name(id=result_name, ctx=ast.Store())
    ast.copy_location(target, expression.value)
    replacement = ast.Assign(targets=[target], value=call)
    ast.copy_location(replacement, expression)
    tree.body[-1] = replacement
    ast.fix_missing_locations(tree)


def _reject_top_level_async(tree: ast.Module) -> None:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Await, ast.AsyncFor, ast.AsyncWith)):
            continue
        parent = parents.get(node)
        while parent is not None and not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent = parents.get(parent)
        if parent is None:
            raise TopLevelAwaitError(
                "Top-level await and top-level async statements are not supported. "
                "The playground executes a normal Python module.",
                line=getattr(node, "lineno", None),
                column=getattr(node, "col_offset", None),
            )


def _last_statement_line(tree: ast.Module) -> int:
    if not tree.body:
        return 1
    return getattr(tree.body[-1], "end_lineno", tree.body[-1].lineno)


def _format_user_traceback(error: BaseException, seen: set[int] | None = None) -> str:
    seen = seen or set()
    if id(error) in seen:
        return f"{type(error).__name__}: {error}\n[exception chain cycle omitted]\n"
    seen.add(id(error))
    if isinstance(error, SyntaxError):
        return "".join(traceback.format_exception_only(type(error), error))

    parts: list[str] = []
    if error.__cause__ is not None:
        parts.append(_format_user_traceback(error.__cause__, seen))
        parts.append("\nThe above exception was the direct cause of the following exception:\n\n")
    elif error.__context__ is not None and not error.__suppress_context__:
        parts.append(_format_user_traceback(error.__context__, seen))
        parts.append("\nDuring handling of the above exception, another exception occurred:\n\n")

    frames = [frame for frame in traceback.extract_tb(error.__traceback__) if frame.filename == PLAYGROUND_FILENAME]
    if frames:
        parts.append("Traceback (most recent call last):\n")
        for frame in frames:
            parts.append(f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}\n')
            if frame.line:
                parts.append(f"    {frame.line.strip()}\n")
    parts.extend(traceback.format_exception_only(type(error), error))
    return "".join(parts)


def _diagnostic(error: BaseException) -> dict[str, object]:
    frames = [frame for frame in traceback.extract_tb(error.__traceback__) if frame.filename == PLAYGROUND_FILENAME]
    frame = frames[-1] if frames else None
    if isinstance(error, SyntaxError):
        line = error.lineno
        column = error.offset - 1 if error.offset is not None else None
        filename = error.filename or PLAYGROUND_FILENAME
        kind = "syntax_error"
    elif isinstance(error, PreviewContractError):
        line = error.line if error.line is not None else getattr(frame, "lineno", None)
        column = error.column
        filename = PLAYGROUND_FILENAME
        kind = error.kind
    else:
        line = frame.lineno if frame is not None else None
        column = None
        filename = PLAYGROUND_FILENAME if frame is not None else "<runner>"
        kind = "execution_stopped" if isinstance(error, (SystemExit, KeyboardInterrupt)) else "python_error"

    traceback_text = (
        f'  File "{PLAYGROUND_FILENAME}", line {line or 1}\n{type(error).__name__}: {error}\n'
        if isinstance(error, PreviewContractError) and not frames
        else _format_user_traceback(error)
    )
    message, message_truncated = _bounded(str(error), MAX_MESSAGE_CHARS)
    traceback_text, traceback_truncated = _bounded(traceback_text, MAX_TRACEBACK_CHARS)
    return {
        "kind": kind,
        "message": message,
        "filename": filename,
        "line": line,
        "column": column,
        "traceback": traceback_text,
        "truncated": message_truncated or traceback_truncated,
    }


def _fresh_module(source: str, extra: dict[str, Any]) -> ModuleType:
    citry.clear()
    citry.register_library(citry_ui)
    module = ModuleType(PLAYGROUND_MODULE_NAME)
    module.__file__ = PLAYGROUND_FILENAME
    module.__package__ = None
    module.__dict__.update(extra)

    # Python 3.14 keeps ordinary annotations deferred. Citry reads their source
    # without evaluating visitor expressions, which requires the dynamic module
    # to follow the same sys.modules and linecache contracts as an imported file.
    linecache.cache[PLAYGROUND_FILENAME] = (
        len(source),
        None,
        source.splitlines(keepends=True),
        PLAYGROUND_FILENAME,
    )
    sys.modules[PLAYGROUND_MODULE_NAME] = module
    return module


def _catalog_field(field: object) -> dict[str, object]:
    """Copy the small field contract used by browser completion and hover."""
    return {
        "name": field.name,
        "required": field.required,
        "typeDisplay": field.type_display,
        "description": field.description,
    }


def _catalog_component(component: object) -> dict[str, object]:
    """Project one stable component record without exposing runtime objects."""
    return {
        "definitionId": component.definition_id,
        "name": component.name,
        "aliases": list(component.aliases),
        "className": component.class_name,
        "importPath": component.import_path,
        "description": component.description,
        "builtin": component.builtin,
        "kwargs": [_catalog_field(field) for field in component.schemas.kwargs.fields],
        "slots": [_catalog_field(field) for field in component.schemas.slots.fields],
    }


def _catalog_snapshot(namespace: dict[str, Any]) -> dict[str, object] | None:
    """Copy every registry reachable from the successful playground module."""
    engines: dict[int, Citry] = {id(citry): citry}
    try:
        for value in namespace.values():
            if isinstance(value, Citry):
                engines[id(value)] = value
            elif isinstance(value, type) and issubclass(value, Component):
                owner = value.citry
                if isinstance(owner, Citry):
                    engines[id(owner)] = owner
        registries = []
        for engine in engines.values():
            catalog = engine.inspect_components(include_builtins=True)
            registries.append(
                {
                    "engineId": catalog.engine_id,
                    "components": [_catalog_component(component) for component in catalog.components],
                }
            )
        snapshot: dict[str, object] = {"schemaVersion": 1, "registries": registries}
        if len(json.dumps(snapshot, ensure_ascii=False, allow_nan=False).encode()) > MAX_CATALOG_BYTES:
            return None
        return snapshot
    except Exception:
        # Introspection enriches the editor but must never turn a successful
        # render into a failed playground run.
        return None


def _unsupported_event_result(envelope: object, message: str) -> dict[str, object]:
    if not isinstance(envelope, dict):
        request_id = None
        calls: list[object] = [None]
    else:
        request_id = envelope.get("requestId")
        raw_calls = envelope.get("calls")
        calls = raw_calls if isinstance(raw_calls, list) and raw_calls else [None]

    results: list[dict[str, object]] = []
    for call in calls:
        result: dict[str, object] = {
            "ok": False,
            "error": {
                "status": 500,
                "code": "handler_error",
                "message": message,
            },
        }
        if isinstance(call, dict) and isinstance(call.get("sendSequence"), int):
            result["sendSequence"] = call["sendSequence"]
        results.append(result)
    return {
        "protocol": "citry-events/1",
        "requestId": request_id,
        "results": results,
    }


def _apply_playground_event_policy(envelope: object, response: object) -> dict[str, object]:
    if isinstance(response, RouteResponse):
        return _unsupported_event_result(
            envelope,
            "Downloads and raw route responses are not available in the browser playground.",
        )
    if not isinstance(response, dict):
        return _unsupported_event_result(envelope, "The event returned an invalid response.")

    results = response.get("results")
    if not isinstance(results, list):
        return response
    for result in results:
        if not isinstance(result, dict) or result.get("ok") is not True:
            continue
        actions = result.get("actions")
        if not isinstance(actions, list):
            continue
        unsupported = sorted(
            {
                action.get("action")
                for action in actions
                if isinstance(action, dict) and action.get("action") not in SUPPORTED_EVENT_ACTIONS
            }
        )
        if not unsupported:
            continue
        names = ", ".join(str(name) for name in unsupported)
        replacement: dict[str, object] = {
            "ok": False,
            "error": {
                "status": 500,
                "code": "handler_error",
                "message": (
                    f"This event returned unsupported playground action(s): {names}. "
                    "The playground currently supports Data, Dispatch, Render, and State actions."
                ),
            },
        }
        if isinstance(result.get("sendSequence"), int):
            replacement["sendSequence"] = result["sendSequence"]
        result.clear()
        result.update(replacement)
    return response


def dispatch_event_json(envelope_json: str, run_id: int) -> str:
    """Dispatch one browser Events envelope against the displayed module."""
    if _runtime_state.namespace is None or _runtime_state.run_id != run_id:
        raise RuntimeError("This event belongs to a preview that is no longer active. Run the module again.")

    envelope = json.loads(envelope_json)
    body = envelope_json.encode("utf-8")
    content_type = "application/citry-events+json"
    headers = RouteHeaders([("Content-Type", content_type)])
    request = EventRequest(
        method="POST",
        path=PLAYGROUND_EVENT_PATH,
        headers=headers,
        body=body,
        content_type=content_type,
    )
    context = TransportContext(
        transport="playground",
        citry=citry,
        headers=headers,
    )

    # Reassert the host-owned prefix before fragment serialization in case the
    # visitor changed the default engine while handling an earlier event.
    citry.set_mounted_prefix(PLAYGROUND_ASSET_PREFIX)
    response = _dispatcher.dispatch(envelope, context, request=request)
    return json.dumps(_apply_playground_event_policy(envelope, response), allow_nan=False)


def load_playground_assets_json(paths_json: str, run_id: int) -> str:
    """Serve one bounded batch of generated JS and CSS to the active preview."""
    if _runtime_state.namespace is None or _runtime_state.run_id != run_id:
        raise RuntimeError("These assets belong to a preview that is no longer active. Run the module again.")

    raw_paths = json.loads(paths_json)
    if not isinstance(raw_paths, list) or not raw_paths:
        raise ValueError("A playground asset request must contain at least one path.")
    if len(raw_paths) > MAX_ASSET_PATHS:
        raise ValueError(f"A playground asset request may contain at most {MAX_ASSET_PATHS} paths.")

    paths: list[str] = []
    seen: set[str] = set()
    prefix = f"{PLAYGROUND_ASSET_PREFIX}/"
    for path in raw_paths:
        if not isinstance(path, str) or not path or len(path.encode("utf-8")) > MAX_ASSET_PATH_BYTES:
            raise ValueError("Each playground asset path must be a short, non-empty string.")
        relative_path = path.removeprefix(prefix)
        if (
            not path.startswith(prefix)
            or not relative_path
            or any(character in path for character in ("?", "#", "%", "\\", "\0"))
            or any(segment in {".", ".."} for segment in relative_path.split("/"))
        ):
            raise ValueError(f"Unsupported playground asset path: {path!r}.")
        if path in seen:
            raise ValueError(f"Duplicate playground asset path: {path!r}.")
        seen.add(path)
        paths.append(path)

    assets: list[dict[str, str]] = []
    total_bytes = 0
    routes = citry.urls
    for path in paths:
        route_path = path.removeprefix(prefix)
        matched = match_route(routes, route_path)
        identity = None if matched is None else (matched.full_path, matched.route.name)
        if matched is None or identity not in _ALLOWED_ASSET_ROUTES:
            raise ValueError(f"Unsupported playground asset path: {path!r}.")
        if "GET" not in matched.route.methods or matched.route.handler is None:
            raise ValueError(f"The playground asset route cannot serve {path!r}.")
        handler = matched.route.handler
        if inspect.iscoroutinefunction(handler):
            raise ValueError(f"The playground asset route cannot serve {path!r} synchronously.")

        request = RouteRequest(method="GET", path=path)
        response = handler(request, **matched.params)
        if not isinstance(response, RouteResponse) or response.status != 200:
            raise ValueError(f"The playground asset was not found: {path!r}.")
        content_type = response.content_type.partition(";")[0].strip().lower()
        if content_type not in _ALLOWED_ASSET_CONTENT_TYPES:
            raise ValueError(f"The playground asset has an unsupported content type: {path!r}.")
        if isinstance(response.content, bytes):
            try:
                content = response.content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError(f"The playground asset is not valid UTF-8: {path!r}.") from error
        elif isinstance(response.content, str):
            content = response.content
        else:
            raise TypeError(f"The playground asset returned unsupported content: {path!r}.")
        content_bytes = len(content.encode("utf-8"))
        if content_bytes > MAX_ASSET_BYTES:
            raise ValueError(f"The playground asset exceeds the {MAX_ASSET_BYTES // 1024} KiB limit: {path!r}.")
        total_bytes += content_bytes
        if total_bytes > MAX_ASSET_BATCH_BYTES:
            raise ValueError(
                f"The playground asset batch exceeds the {MAX_ASSET_BATCH_BYTES // 1024 // 1024} MiB limit."
            )
        assets.append({"path": path, "contentType": content_type, "content": content})

    return json.dumps(assets, allow_nan=False)


def run_source_json(source: str, run_id: int = 1) -> str:
    """Execute ``source`` and return the bounded result as a JSON string."""
    _runtime_state.namespace = None
    _runtime_state.run_id = None
    sys.modules.pop(PLAYGROUND_MODULE_NAME, None)
    linecache.cache.pop(PLAYGROUND_FILENAME, None)
    stdout = io.StringIO()
    stderr = io.StringIO()
    module: ModuleType | None = None
    try:
        tree = ast.parse(source, filename=PLAYGROUND_FILENAME, mode="exec")
        _reject_top_level_async(tree)
        expression = _preview_expression(tree)
        result_name = _fresh_private_name("__citry_playground_result", source)
        normalizer_name = _fresh_private_name(
            "__citry_playground_normalize",
            source,
            reserved={result_name},
        )
        if expression is not None:
            _rewrite_final_expression(
                tree,
                expression,
                result_name=result_name,
                normalizer_name=normalizer_name,
            )
        module = _fresh_module(source, {normalizer_name: _normalize_preview})
        namespace = module.__dict__
        code = compile(tree, PLAYGROUND_FILENAME, "exec", dont_inherit=True)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code, namespace, namespace)
        if expression is None:
            raise MissingPreviewError(
                "No preview value was found. End the module with HTML, a CitryElement, a ComponentLike, "
                "or a CitryRender.",
                line=_last_statement_line(tree),
                column=0,
            )
        html = namespace[result_name]
        catalog = _catalog_snapshot(namespace)
        _runtime_state.namespace = namespace
        _runtime_state.run_id = run_id
        diagnostic = None
    except BaseException as error:
        html = None
        catalog = None
        diagnostic = _diagnostic(error)
        if module is not None and sys.modules.get(PLAYGROUND_MODULE_NAME) is module:
            del sys.modules[PLAYGROUND_MODULE_NAME]
        linecache.cache.pop(PLAYGROUND_FILENAME, None)

    stdout_text, stdout_truncated = _bounded(stdout.getvalue(), MAX_STREAM_CHARS)
    stderr_text, stderr_truncated = _bounded(stderr.getvalue(), MAX_STREAM_CHARS)
    return json.dumps(
        {
            "ok": diagnostic is None,
            "html": html,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "diagnostic": diagnostic,
            "catalog": catalog,
            "truncated": stdout_truncated or stderr_truncated,
        }
    )
