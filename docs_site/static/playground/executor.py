"""Execute one visitor-authored module inside the disposable Pyodide Worker."""

# The Worker intentionally executes visitor code and catches control-flow
# exceptions at its boundary.
# ruff: noqa: BLE001, S102

from __future__ import annotations

import ast
import contextlib
import dataclasses
import io
import json
import linecache
import logging
import secrets
import sys
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any

from citry import CitryElement, CitryRender, citry
from citry.ext.events import EventRequest, EventsDispatcher, TransportContext, emission
from citry.util.routing import RouteHeaders, RouteResponse

PLAYGROUND_FILENAME = "<playground>"
PLAYGROUND_MODULE_NAME = "__playground__"
MAX_STREAM_CHARS = 65_536
MAX_TRACEBACK_CHARS = 16_384
MAX_MESSAGE_CHARS = 4_096
PLAYGROUND_EVENT_PATH = "/playground/events"
SUPPORTED_EVENT_ACTIONS = frozenset({"data", "event", "state"})


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
    if isinstance(value, str):
        return str(value)
    if isinstance(value, CitryElement):
        return str(value)
    if isinstance(value, CitryRender):
        return value.serialize()
    if value is None:
        raise NonePreviewError(
            "The preview expression returned None. End the module with HTML, a CitryElement, or a CitryRender."
        )
    raise UnsupportedPreviewTypeError(
        f"Cannot preview {type(value).__name__}. End the module with HTML, a CitryElement, or a CitryRender."
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


def install_events_client_runtime(source: str) -> str:
    """Install the generated Events runtime omitted from the Citry 0.3.0 wheel."""
    target = Path(emission.__file__).parent / "client" / "citry-events.js"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    emission._client_runtime_js.cache_clear()
    return str(target)


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
                    "The playground currently supports Data, Dispatch, and State actions."
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

    # Render actions need Citry's fragment asset routes. Give serialization a
    # syntactically valid prefix so the dispatcher can finish, then reject the
    # unsupported action with a pointed playground error below.
    previous_prefix = citry.mounted_prefix
    citry.set_mounted_prefix("/__citry_playground__")
    try:
        response = _dispatcher.dispatch(envelope, context, request=request)
    finally:
        citry._mounted_prefix = previous_prefix
    return json.dumps(_apply_playground_event_policy(envelope, response), allow_nan=False)


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
                "No preview value was found. End the module with HTML, a CitryElement, or a CitryRender.",
                line=_last_statement_line(tree),
                column=0,
            )
        html = namespace[result_name]
        _runtime_state.namespace = namespace
        _runtime_state.run_id = run_id
        diagnostic = None
    except BaseException as error:
        html = None
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
            "truncated": stdout_truncated or stderr_truncated,
        }
    )
