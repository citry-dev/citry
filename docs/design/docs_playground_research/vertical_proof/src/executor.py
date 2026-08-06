"""Browser-side execution contract for the Stage 6 vertical proof."""

# The Worker is disposable and intentionally executes visitor code.
# ruff: noqa: BLE001, S102

from __future__ import annotations

import ast
import contextlib
import io
import json
import traceback

from citry import CitryElement, CitryRender, citry

PLAYGROUND_FILENAME = "<playground>"
MAX_STREAM_CHARS = 65_536
MAX_TRACEBACK_CHARS = 16_384
MAX_MESSAGE_CHARS = 4_096


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


def _is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _preview_expression(tree: ast.Module) -> ast.Expr | None:
    if not tree.body or not isinstance(tree.body[-1], ast.Expr):
        return None
    if len(tree.body) == 1 and _is_docstring(tree.body[-1]):
        return None
    return tree.body[-1]


def _fresh_private_name(
    base: str,
    source: str,
    reserved: set[str] | None = None,
) -> str:
    reserved = reserved or set()
    candidate = base
    suffix = 0
    while candidate in source or candidate in reserved:
        suffix += 1
        candidate = f"{base}_{suffix}"
    return candidate


def _reject_top_level_async(tree: ast.Module) -> None:
    parents = {}
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
                "Top-level await and top-level async statements are not supported.",
                line=getattr(node, "lineno", None),
                column=getattr(node, "col_offset", None),
            )


def _rewrite_final_expression(
    tree: ast.Module,
    expression: ast.Expr,
    result_name: str,
    normalizer_name: str,
) -> None:
    call = ast.Call(
        func=ast.Name(id=normalizer_name, ctx=ast.Load()),
        args=[expression.value],
        keywords=[],
    )
    ast.copy_location(call, expression.value)
    replacement = ast.Assign(targets=[ast.Name(id=result_name, ctx=ast.Store())], value=call)
    ast.copy_location(replacement, expression)
    tree.body[-1] = replacement
    ast.fix_missing_locations(tree)


def _format_traceback(error: BaseException) -> str:
    if isinstance(error, SyntaxError):
        return "".join(traceback.format_exception_only(type(error), error))
    frames = [
        frame
        for frame in traceback.extract_tb(error.__traceback__)
        if frame.filename == PLAYGROUND_FILENAME or (frame.filename.startswith("<") and frame.filename.endswith(">"))
    ]
    parts = []
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
        kind = "syntax_error"
    elif isinstance(error, PreviewContractError):
        line = error.line if error.line is not None else getattr(frame, "lineno", None)
        column = error.column
        kind = error.kind
    else:
        line = frame.lineno if frame is not None else None
        column = None
        kind = "execution_stopped" if isinstance(error, (SystemExit, KeyboardInterrupt)) else "python_error"
    message, message_truncated = _bounded(str(error), MAX_MESSAGE_CHARS)
    traceback_text, traceback_truncated = _bounded(_format_traceback(error), MAX_TRACEBACK_CHARS)
    return {
        "kind": kind,
        "message": message,
        "filename": (
            PLAYGROUND_FILENAME if frame or isinstance(error, (SyntaxError, PreviewContractError)) else "<runner>"
        ),
        "line": line,
        "column": column,
        "traceback": traceback_text,
        "truncated": message_truncated or traceback_truncated,
    }


def run_source_json(source: str) -> str:
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        tree = ast.parse(source, filename=PLAYGROUND_FILENAME, mode="exec")
        _reject_top_level_async(tree)
        expression = _preview_expression(tree)
        if expression is None:
            line = getattr(tree.body[-1], "end_lineno", 1) if tree.body else 1
            raise MissingPreviewError(
                "No preview value was found. End the module with HTML, a CitryElement, or a CitryRender.",
                line=line,
                column=0,
            )
        result_name = _fresh_private_name("__citry_playground_result", source)
        normalizer_name = _fresh_private_name("__citry_playground_normalize", source, {result_name})
        _rewrite_final_expression(tree, expression, result_name, normalizer_name)
        namespace = {
            "__file__": PLAYGROUND_FILENAME,
            "__name__": "__playground__",
            "__package__": None,
            normalizer_name: _normalize_preview,
        }
        citry.clear()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(compile(tree, PLAYGROUND_FILENAME, "exec", dont_inherit=True), namespace, namespace)
        stdout_text, stdout_truncated = _bounded(stdout.getvalue(), MAX_STREAM_CHARS)
        stderr_text, stderr_truncated = _bounded(stderr.getvalue(), MAX_STREAM_CHARS)
        return json.dumps(
            {
                "ok": True,
                "html": namespace[result_name],
                "stdout": stdout_text,
                "stderr": stderr_text,
                "truncated": stdout_truncated or stderr_truncated,
            }
        )
    except BaseException as error:
        stdout_text, stdout_truncated = _bounded(stdout.getvalue(), MAX_STREAM_CHARS)
        stderr_text, stderr_truncated = _bounded(stderr.getvalue(), MAX_STREAM_CHARS)
        return json.dumps(
            {
                "ok": False,
                "html": None,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "diagnostic": _diagnostic(error),
                "truncated": stdout_truncated or stderr_truncated,
            }
        )
