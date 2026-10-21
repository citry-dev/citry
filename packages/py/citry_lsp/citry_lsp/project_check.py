"""Check a whole project's components from the command line the way the editor checks open files."""

from __future__ import annotations

import asyncio
import io
import tokenize
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from citry_lsp.engine import DocumentState, _js_data_type_diagnostics
from citry_lsp.semantic import infer_js_data_value_types, semantic_diagnostics
from citry_lsp.type_analysis import TyAnalyzer, TyUnavailableError, is_project_source_file
from citry_lsp.uri import file_uri_path

if TYPE_CHECKING:
    from pathlib import Path

    from lsprotocol import types

    from citry_lsp.project import ProjectState


# A batch check waits this long for one ty answer. A cold start on a busy CI
# machine is far slower than the editor's interactive bound.
_BATCH_REQUEST_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True, slots=True)
class ProjectTypeFinding:
    """One TypeScript or ty finding, mapped back to the authored file it belongs to."""

    path: Path
    source: str
    diagnostic: types.Diagnostic


def project_documents(project: ProjectState, workspace: Path) -> dict[str, DocumentState]:
    """
    Read every authored file in `workspace` that holds a component's template or JavaScript.

    Components installed from another package are skipped, because their
    authors check them; that includes a package in a virtual environment
    inside `workspace`. Each file is read from disk and prepared the way the
    editor prepares an open file.
    """
    catalog = project.catalog
    if catalog is None:
        return {}
    languages: dict[Path, str] = {}
    for component in catalog.components:
        for kind, language in (("template", "citry-html"), ("js", "javascript")):
            asset = getattr(component.assets, kind)
            if asset.kind == "inline" and asset.owner_file is not None:
                languages.setdefault(asset.owner_file.resolve(), "python")
            elif asset.resolved_path is not None:
                languages.setdefault(asset.resolved_path.resolve(), language)
    documents: dict[str, DocumentState] = {}
    for path, language in sorted(languages.items()):
        if not is_project_source_file(path, workspace):
            continue
        try:
            raw = path.read_bytes()
            # Decode as Python and the editor do, keeping CRLF line endings
            # and dropping a byte order mark, so the text matches the file
            # that ty reads from disk.
            encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline) if language == "python" else ("utf-8", [])
            source = raw.decode(encoding)
        except (OSError, SyntaxError, UnicodeError, LookupError):
            continue
        document = DocumentState(path.as_uri(), language, source, 0)
        document.update(source, 0, project)
        documents[document.uri] = document
    return documents


def check_project_python_types(
    project: ProjectState,
    workspace: Path,
    documents: dict[str, DocumentState] | None = None,
) -> tuple[ProjectTypeFinding, ...]:
    """
    Run ty over the Python expressions of every component template in `workspace`.

    Each template expression is checked in the same generated Python file the
    editor gives ty, and the findings pass the same filter, so `citry check
    --types` reports a `citry.python.*` finding exactly when the editor would.
    The result also holds the editor's `citry.js-data.unsupported-type`
    warnings, which can depend on the types ty gives `js_data()` values.

    ty also types the `js_data()` values Citry's own rules leave unknown, and
    `project` keeps those types, so run this before the TypeScript check that
    reads them.

    Pass the ``documents`` that ``project_documents()`` returned to reuse
    them; otherwise the files are read again.

    Raises:
        TyUnavailableError: When ty cannot start or stops answering.

    """
    workspace = workspace.resolve()
    if documents is None:
        documents = project_documents(project, workspace)
    return asyncio.run(_check_project_python_types(project, workspace, documents))


async def _check_project_python_types(
    project: ProjectState,
    workspace: Path,
    documents: dict[str, DocumentState],
) -> tuple[ProjectTypeFinding, ...]:
    analyzer = TyAnalyzer(workspace, request_timeout=_BATCH_REQUEST_TIMEOUT_SECONDS)
    results: list[ProjectTypeFinding] = []
    try:
        # A copy of the project starts without ty's answers, so comparing
        # the two shows which warnings need them.
        untyped = replace(project)
        await infer_js_data_value_types(analyzer, project, documents)
        if analyzer.failure is not None:
            raise TyUnavailableError(analyzer.failure)
        for uri, document in sorted(documents.items()):
            findings = await semantic_diagnostics(analyzer, document, project, documents)
            # The editor shows nothing when ty fails, but a command must say so.
            if analyzer.failure is not None:
                raise TyUnavailableError(analyzer.failure)
            path = file_uri_path(uri)
            if path is None:
                continue
            # The editor warns about a js_data() value that JSON cannot carry
            # once ty has typed it, such as a module constant holding a path,
            # so the command reports those warnings too. Warnings Citry's own
            # rules give without ty are left to the registry check, which
            # already reports them.
            reported = [*findings, *_ty_js_data_type_diagnostics(document, project, untyped, documents)]
            results.extend(
                ProjectTypeFinding(path, document.source, diagnostic)
                for diagnostic in sorted(
                    reported,
                    key=lambda item: (item.range.start.line, item.range.start.character),
                )
            )
    finally:
        await analyzer.close()
    return tuple(results)


def _ty_js_data_type_diagnostics(
    document: DocumentState,
    project: ProjectState,
    untyped: ProjectState,
    documents: dict[str, DocumentState],
) -> list[types.Diagnostic]:
    """Return the editor's js-data warnings for one file that appear only once ty has typed the values."""
    without_ty = {
        (item.range.start.line, item.range.start.character, item.message)
        for item in _js_data_type_diagnostics(document, untyped, documents)
    }
    return [
        item
        for item in _js_data_type_diagnostics(document, project, documents)
        if (item.range.start.line, item.range.start.character, item.message) not in without_ty
    ]


__all__ = ["ProjectTypeFinding", "check_project_python_types", "project_documents"]
