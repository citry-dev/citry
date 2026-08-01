"""Shared authoring contract for opt-in live documentation snippets."""

from __future__ import annotations

import ast
import base64
import json
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.config import DocsConfig

UI_COMPONENTS_ROOT = PurePosixPath("packages/py/citry_ui/citry_ui/components")
MAX_LIVE_SOURCE_BYTES = 64 * 1024
_ALLOWED_PACKAGE_ROOTS = {
    "__future__",
    "citry",
    "citry_core",
    "markupsafe",
    "typing_extensions",
    "wrapt",
}


class LiveCodeValidationError(ValueError):
    """An authored live-code directive or source does not meet the contract."""


@dataclass
class LiveCodeContext:
    """Per-page inputs needed while a ``<c-live-code>`` component renders."""

    config: DocsConfig
    source_path: Path | None
    interactive: bool
    allow_citry_ui: bool = False
    has_live_code: bool = False
    has_interactive: bool = False


_context: ContextVar[LiveCodeContext | None] = ContextVar("docs_live_code_context", default=None)


@contextmanager
def use_live_code_context(context: LiveCodeContext) -> Iterator[None]:
    """Expose one page's live-code build context to nested components."""
    token = _context.set(context)
    try:
        yield
    finally:
        _context.reset(token)


def get_live_code_context() -> LiveCodeContext | None:
    """Return the current page's live-code context, if one is active."""
    return _context.get()


def _component_snippet_root(authored: PurePosixPath) -> PurePosixPath | None:
    """Return the narrow component-owned snippets root for an allowed path."""
    prefix_length = len(UI_COMPONENTS_ROOT.parts)
    if (
        len(authored.parts) == prefix_length + 3
        and authored.parts[:prefix_length] == UI_COMPONENTS_ROOT.parts
        and authored.parts[prefix_length + 1] == "snippets"
    ):
        return UI_COMPONENTS_ROOT / authored.parts[prefix_length] / "snippets"
    return None


def _validate_path(path: str, repo_root: Path, *, static: bool) -> tuple[Path, bool]:
    if not path or "\\" in path or "\0" in path or "://" in path:
        raise LiveCodeValidationError("path must be a non-empty POSIX repository path")
    if any(part in {"", ".", ".."} for part in path.split("/")):
        raise LiveCodeValidationError("path must not contain empty, current, or parent segments")
    authored = PurePosixPath(path)
    if authored.is_absolute() or ".." in authored.parts:
        raise LiveCodeValidationError("path traversal and absolute paths are not allowed")
    if authored.suffix != ".py":
        raise LiveCodeValidationError("path must name a Python module ending in .py")
    component_root = _component_snippet_root(authored)
    is_component_snippet = component_root is not None
    if static and component_root is not None:
        allowlist_root = component_root
    elif not static:
        allowlist_root = PurePosixPath()
    else:
        raise LiveCodeValidationError(
            "static live code must be inside a Citry UI components/<family>/snippets/ directory"
        )

    root = repo_root.resolve()
    allowed_root = (root / Path(*allowlist_root.parts)).resolve()
    try:
        allowed_root.relative_to(root)
    except ValueError as error:
        raise LiveCodeValidationError("live-code allowlist resolves outside the repository") from error
    candidate = (root / Path(*authored.parts)).resolve()
    try:
        candidate.relative_to(allowed_root)
    except ValueError as error:
        raise LiveCodeValidationError("path resolves outside the live-code allowlist") from error
    if not candidate.is_file():
        raise LiveCodeValidationError(f"source file does not exist: {path}")
    return candidate, is_component_snippet


class _TopLevelAsyncVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.function_depth = 0
        self.offender: ast.AST | None = None

    def _visit_function(self, node: ast.AST) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_function(node)

    def _reject_at_module_scope(self, node: ast.AST) -> None:
        if self.function_depth == 0 and self.offender is None:
            self.offender = node
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        self._reject_at_module_scope(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._reject_at_module_scope(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._reject_at_module_scope(node)


def _validate_module(source: str, path: str, *, allow_citry_ui: bool) -> None:
    try:
        tree = ast.parse(source, filename=path, feature_version=(3, 10))
    except SyntaxError as error:
        location = f" at line {error.lineno}" if error.lineno else ""
        raise LiveCodeValidationError(f"source has invalid Python syntax{location}: {error.msg}") from error

    async_visitor = _TopLevelAsyncVisitor()
    async_visitor.visit(tree)
    if async_visitor.offender is not None:
        raise LiveCodeValidationError("top-level await, async for, and async with are not supported")

    try:
        compile(tree, path, "exec")
    except SyntaxError as error:
        location = f" at line {error.lineno}" if error.lineno else ""
        raise LiveCodeValidationError(f"source has invalid Python syntax{location}: {error.msg}") from error

    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                raise LiveCodeValidationError("relative imports are not supported")
            if node.module:
                names = [node.module]
        for name in names:
            package_root = name.partition(".")[0]
            allowed_roots = _ALLOWED_PACKAGE_ROOTS | ({"citry_ui"} if allow_citry_ui else set())
            if package_root not in sys.stdlib_module_names and package_root not in allowed_roots:
                raise LiveCodeValidationError(f"unsupported import: {name}")


def load_live_source(
    path: str,
    *,
    repo_root: Path,
    title: str = "",
    static: bool = False,
    allow_citry_ui: bool = False,
) -> str:
    """Read and validate one canonical live-code source file."""
    if title is not None and not title.strip():
        raise LiveCodeValidationError("title must not be blank")
    source_path, is_component_snippet = _validate_path(path, repo_root, static=static)
    raw = source_path.read_bytes()
    if len(raw) > MAX_LIVE_SOURCE_BYTES:
        raise LiveCodeValidationError(f"source exceeds the {MAX_LIVE_SOURCE_BYTES // 1024} KiB limit")
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise LiveCodeValidationError("source is not valid UTF-8") from error
    if "\r" in source:
        raise LiveCodeValidationError("source must use LF line endings")
    _validate_module(source, path, allow_citry_ui=(static and is_component_snippet) or allow_citry_ui)
    return source


def encode_live_projection(path: str, title: str, *, static: bool = False) -> str:
    """Encode marker metadata without embedding executable source in the page."""
    payload = json.dumps(
        {"path": path, "title": title, "static": static},
        separators=(",", ":"),
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_live_projection(payload: str) -> tuple[str, str, bool]:
    """Decode marker metadata emitted by the live-code component."""
    padded = payload + "=" * (-len(payload) % 4)
    try:
        value = json.loads(base64.urlsafe_b64decode(padded).decode())
        path = value["path"]
        title = value["title"]
        static = value.get("static", False)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as error:
        raise LiveCodeValidationError("live-code projection marker is invalid") from error
    if not isinstance(path, str) or not isinstance(title, str) or not isinstance(static, bool):
        raise LiveCodeValidationError("live-code projection marker is invalid")
    return path, title, static
