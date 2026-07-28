"""
Executable runner candidates for the Citry playground design research.

This is a proof, not product code. It keeps the four Stage 3 preview-value
candidates small enough to compare while exercising the current Citry API.
"""

# The proof intentionally executes visitor code and catches control-flow
# exceptions at the Worker boundary, which is exactly what S102 and BLE001 flag.
# ruff: noqa: BLE001, S102

from __future__ import annotations

import ast
import contextlib
import io
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from citry import CitryElement, CitryRender, citry

PLAYGROUND_FILENAME = "<playground>"


@dataclass(frozen=True)
class Diagnostic:
    """A source-oriented error returned by a runner candidate."""

    kind: str
    message: str
    filename: str
    line: int | None
    column: int | None
    traceback: str


@dataclass(frozen=True)
class RunResult:
    """The captured result of one candidate execution."""

    html: str | None
    stdout: str
    stderr: str
    diagnostic: Diagnostic | None = None

    @property
    def ok(self) -> bool:
        return self.diagnostic is None


class PreviewContractError(Exception):
    """Base class for runner-generated preview contract failures."""

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


class MultiplePreviewError(PreviewContractError):
    kind = "multiple_preview_calls"


class TopLevelAwaitError(PreviewContractError):
    kind = "top_level_await"


def normalize_preview(value: object) -> str:
    """Normalize only the HTML result types proposed for the playground."""
    if isinstance(value, str):
        # Markup is a str subclass, so it deliberately follows this path.
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


def run_implicit(source: str) -> RunResult:
    """Run a module and preview its final expression through one AST rewrite."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        tree = ast.parse(source, filename=PLAYGROUND_FILENAME, mode="exec")
        _reject_top_level_async(tree)
        final_expression = _preview_expression(tree)
        result_name = _fresh_private_name("__citry_playground_result", source)
        normalizer_name = _fresh_private_name(
            "__citry_playground_normalize",
            source,
            reserved={result_name},
        )

        if final_expression is not None:
            _rewrite_final_expression(
                tree,
                final_expression,
                result_name=result_name,
                normalizer_name=normalizer_name,
            )

        code = compile(
            tree,
            PLAYGROUND_FILENAME,
            "exec",
            dont_inherit=True,
        )
        namespace = _fresh_namespace({normalizer_name: normalize_preview})
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code, namespace, namespace)

        if final_expression is None:
            line = _last_statement_line(tree)
            raise MissingPreviewError(
                "No preview value was found. End the module with HTML, a CitryElement, or a CitryRender.",
                line=line,
                column=0 if line is not None else None,
            )
        return RunResult(
            html=namespace[result_name],
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )
    except BaseException as error:
        return RunResult(
            html=None,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            diagnostic=_diagnostic(error),
        )


def run_explicit_render(source: str) -> RunResult:
    """Run a module with a playground-only ``render(value)`` helper."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    previews: list[str] = []

    def render(value: object) -> None:
        if previews:
            raise MultiplePreviewError("render(value) may be called only once per run.")
        previews.append(normalize_preview(value))

    try:
        tree = ast.parse(source, filename=PLAYGROUND_FILENAME, mode="exec")
        _reject_top_level_async(tree)
        code = compile(tree, PLAYGROUND_FILENAME, "exec", dont_inherit=True)
        namespace = _fresh_namespace({"render": render})
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code, namespace, namespace)
        if not previews:
            raise MissingPreviewError(
                "No preview value was found. Call render(value) once.",
                line=_last_statement_line(tree),
                column=0,
            )
        return RunResult(
            html=previews[0],
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )
    except BaseException as error:
        return RunResult(
            html=None,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            diagnostic=_diagnostic(error),
        )


def run_print_as_html(source: str) -> RunResult:
    """Run the rejected candidate where all stdout becomes preview HTML."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        tree = ast.parse(source, filename=PLAYGROUND_FILENAME, mode="exec")
        _reject_top_level_async(tree)
        code = compile(tree, PLAYGROUND_FILENAME, "exec", dont_inherit=True)
        namespace = _fresh_namespace()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code, namespace, namespace)
        html = stdout.getvalue()
        if not html:
            raise MissingPreviewError(
                "No preview value was printed. Call print(value).",
                line=_last_statement_line(tree),
                column=0,
            )
        return RunResult(html=html, stdout=html, stderr=stderr.getvalue())
    except BaseException as error:
        return RunResult(
            html=None,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            diagnostic=_diagnostic(error),
        )


def run_named_preview(source: str) -> RunResult:
    """Run the candidate that reserves a module global named ``preview``."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        tree = ast.parse(source, filename=PLAYGROUND_FILENAME, mode="exec")
        _reject_top_level_async(tree)
        code = compile(tree, PLAYGROUND_FILENAME, "exec", dont_inherit=True)
        namespace = _fresh_namespace()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code, namespace, namespace)
            if "preview" not in namespace:
                raise MissingPreviewError(
                    "No preview value was found. Assign a value to preview.",
                    line=_last_statement_line(tree),
                    column=0,
                )
            html = normalize_preview(namespace["preview"])
        return RunResult(
            html=html,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )
    except BaseException as error:
        return RunResult(
            html=None,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            diagnostic=_diagnostic(error),
        )


def _fresh_namespace(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Clear Citry-owned global state and return a new module namespace."""
    citry.clear()
    namespace: dict[str, Any] = {
        "__file__": PLAYGROUND_FILENAME,
        "__name__": "__playground__",
        "__package__": None,
    }
    if extra:
        namespace.update(extra)
    return namespace


def _preview_expression(tree: ast.Module) -> ast.Expr | None:
    if not tree.body or not isinstance(tree.body[-1], ast.Expr):
        return None
    last = tree.body[-1]
    if len(tree.body) == 1 and _is_docstring(last):
        # Rewriting the sole docstring would change __doc__ and display prose
        # which ordinary module execution treats as metadata.
        return None
    return last


def _is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _rewrite_final_expression(
    tree: ast.Module,
    final_expression: ast.Expr,
    *,
    result_name: str,
    normalizer_name: str,
) -> None:
    normalizer = ast.Name(id=normalizer_name, ctx=ast.Load())
    ast.copy_location(normalizer, final_expression.value)
    normalized = ast.Call(
        func=normalizer,
        args=[final_expression.value],
        keywords=[],
    )
    ast.copy_location(normalized, final_expression.value)
    target = ast.Name(id=result_name, ctx=ast.Store())
    ast.copy_location(target, final_expression.value)
    replacement = ast.Assign(targets=[target], value=normalized)
    ast.copy_location(replacement, final_expression)
    tree.body[-1] = replacement
    ast.fix_missing_locations(tree)


def _fresh_private_name(
    base: str,
    source: str,
    *,
    reserved: set[str] | None = None,
) -> str:
    """Choose a deterministic name absent even as source text."""
    reserved = reserved or set()
    candidate = base
    suffix = 0
    while candidate in source or candidate in reserved:
        suffix += 1
        candidate = f"{base}_{suffix}"
    return candidate


def _reject_top_level_async(tree: ast.Module) -> None:
    """Reject async constructs that ordinary module compilation rejects."""
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    async_nodes = (ast.Await, ast.AsyncFor, ast.AsyncWith)
    for node in ast.walk(tree):
        if not isinstance(node, async_nodes):
            continue
        parent = parents.get(node)
        inside_function = False
        while parent is not None:
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inside_function = True
                break
            parent = parents.get(parent)
        if not inside_function:
            raise TopLevelAwaitError(
                "Top-level await and top-level async statements are not "
                "supported. The playground executes a normal Python module.",
                line=getattr(node, "lineno", None),
                column=getattr(node, "col_offset", None),
            )


def _last_statement_line(tree: ast.Module) -> int | None:
    if not tree.body:
        return 1
    return getattr(tree.body[-1], "end_lineno", tree.body[-1].lineno)


def _diagnostic(error: BaseException) -> Diagnostic:
    playground_frames = [
        frame for frame in traceback.extract_tb(error.__traceback__) if frame.filename == PLAYGROUND_FILENAME
    ]
    playground_frame = playground_frames[-1] if playground_frames else None
    if isinstance(error, SyntaxError):
        line = error.lineno
        column = error.offset - 1 if error.offset is not None else None
        filename = error.filename or PLAYGROUND_FILENAME
    elif isinstance(error, PreviewContractError):
        line = error.line if error.line is not None else getattr(playground_frame, "lineno", None)
        column = error.column
        filename = PLAYGROUND_FILENAME
    else:
        line = playground_frame.lineno if playground_frame is not None else None
        column = None
        filename = PLAYGROUND_FILENAME if playground_frame is not None else "<runner>"

    if isinstance(error, PreviewContractError) and not playground_frames:
        traceback_text = f'  File "{PLAYGROUND_FILENAME}", line {line or 1}\n{type(error).__name__}: {error}\n'
    else:
        traceback_text = _format_user_traceback(error)

    return Diagnostic(
        kind=getattr(error, "kind", _error_kind(error)),
        message=str(error),
        filename=filename,
        line=line,
        column=column,
        traceback=traceback_text,
    )


def _format_user_traceback(
    error: BaseException,
    seen: set[int] | None = None,
) -> str:
    """Keep visitor frames and exception messages, but hide runner internals."""
    if seen is None:
        seen = set()
    error_id = id(error)
    if error_id in seen:
        return f"{type(error).__name__}: {error}\n[exception chain cycle omitted]\n"
    seen.add(error_id)

    if isinstance(error, SyntaxError):
        return "".join(traceback.format_exception_only(type(error), error))

    parts: list[str] = []
    if error.__cause__ is not None:
        parts.append(_format_user_traceback(error.__cause__, seen))
        parts.append("\nThe above exception was the direct cause of the following exception:\n\n")
    elif error.__context__ is not None and not error.__suppress_context__:
        parts.append(_format_user_traceback(error.__context__, seen))
        parts.append("\nDuring handling of the above exception, another exception occurred:\n\n")

    frames = [
        frame
        for frame in traceback.extract_tb(error.__traceback__)
        if frame.filename == PLAYGROUND_FILENAME or (frame.filename.startswith("<") and frame.filename.endswith(">"))
    ]
    if frames:
        parts.append("Traceback (most recent call last):\n")
        for frame in frames:
            parts.append(f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}\n')
            if frame.line:
                parts.append(f"    {frame.line.strip()}\n")
    parts.extend(traceback.format_exception_only(type(error), error))
    return "".join(parts)


def _error_kind(error: BaseException) -> str:
    if isinstance(error, SyntaxError):
        return "syntax_error"
    if isinstance(error, (SystemExit, KeyboardInterrupt)):
        return "execution_stopped"
    return "python_error"


Runner = Callable[[str], RunResult]
