"""Map analyzer answers between virtual Python and authored Citry source."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from lsprotocol import types

from citry_lsp.engine import (
    _I18N_CALL_SIGNATURES,
    _I18N_OPERATION_SIGNATURES,
    DocumentState,
    ExpressionShadow,
    ExpressionShadowGroup,
    TemplateVariableHover,
    all_expression_shadows,
    expression_completion_ranges,
    expression_shadows,
    map_expression_shadow_range,
    render_template_variable_hover,
    template_variable_hover,
)
from citry_lsp.type_analysis import (
    TyAnalyzer,
    TyCompletion,
    TyDocument,
    TyUnavailableError,
    offset_at_position,
    position_at_offset,
    virtual_document_uri,
)
from citry_lsp.uri import file_uri_path

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from citry_lsp.project import ProjectState


async def semantic_completions(
    analyzer: TyAnalyzer,
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState],
) -> tuple[types.CompletionItem, ...]:
    """Return members accepted by every proven consumer and return path."""
    shadows = expression_shadows(
        document,
        position,
        project,
        open_documents,
        repair_completion=True,
    )
    ranges = expression_completion_ranges(document, position)
    if not shadows or ranges is None:
        return ()
    direct = _i18n_formatter_completions(shadows[0], ranges)
    if direct is not None:
        return direct
    if _has_external_unsaved_python(shadows, open_documents):
        return ()
    insert_range, replace_range = ranges
    synchronized = _python_documents(open_documents)
    if synchronized is None:
        return ()
    answers: list[dict[str, TyCompletion]] = []
    try:
        for shadow in shadows:
            virtual = _virtual_document(shadow, Path(project.status.workspace))
            for copied in shadow.document.copies:
                cursor = copied.shadow_start + shadow.cursor_offset
                response_items = await analyzer.completion(
                    virtual,
                    position_at_offset(virtual.source, cursor),
                    synchronized=synchronized,
                )
                answers.append({item.label: item for item in response_items})
    except TyUnavailableError:
        return ()
    if not answers:
        return ()
    labels = set(answers[0])
    for answer in answers[1:]:
        labels.intersection_update(answer)

    result_items: list[types.CompletionItem] = []
    for label in sorted(labels, key=lambda item: (_shared_sort_text(item, answers), item.casefold(), item)):
        candidates = tuple(answer[label] for answer in answers)
        detail = _shared_or_distinct(candidate.detail for candidate in candidates)
        documentation = _shared_markup(candidate.documentation for candidate in candidates)
        kind = candidates[0].kind if all(candidate.kind == candidates[0].kind for candidate in candidates) else None
        result_items.append(
            types.CompletionItem(
                label=label,
                kind=kind,
                detail=detail,
                documentation=documentation,
                filter_text=label,
                sort_text=_shared_sort_text(label, answers),
                text_edit=types.InsertReplaceEdit(label, insert_range, replace_range),
            )
        )
    return tuple(result_items)


async def semantic_hover(
    analyzer: TyAnalyzer,
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState],
) -> types.Hover | None:
    """Return every distinct proven type for the member under the cursor."""
    shadows = expression_shadows(document, position, project, open_documents)
    if not shadows:
        return None
    if _has_external_unsaved_python(shadows, open_documents):
        return None
    synchronized = _python_documents(open_documents)
    if synchronized is None:
        return None
    values: list[str] = []
    mapped_ranges: list[types.Range] = []
    try:
        for shadow in shadows:
            virtual = _virtual_document(shadow, Path(project.status.workspace))
            for copied in shadow.document.copies:
                cursor = copied.shadow_start + shadow.cursor_offset
                hint = await analyzer.hover(
                    virtual,
                    position_at_offset(virtual.source, cursor),
                    synchronized=synchronized,
                )
                if hint is None:
                    return None
                if hint.contents.value not in values:
                    values.append(hint.contents.value)
                if hint.range is not None:
                    mapped = map_expression_shadow_range(document, position, shadow, hint.range)
                    if mapped is None:
                        return None
                    mapped_ranges.append(mapped)
    except TyUnavailableError:
        return None
    if not values:
        return None
    content = "\n\n---\n\n".join(values)
    hover_range = (
        mapped_ranges[0] if mapped_ranges and all(item == mapped_ranges[0] for item in mapped_ranges) else None
    )
    return types.Hover(types.MarkupContent(types.MarkupKind.Markdown, content), range=hover_range)


async def semantic_variable_hover(
    analyzer: TyAnalyzer,
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState],
    variable: TemplateVariableHover,
) -> types.Hover:
    """Add every proven analyzer type to one parser-proven variable hover."""
    fallback = render_template_variable_hover(variable)
    shadows = expression_shadows(document, position, project, open_documents)
    if not shadows or _has_external_unsaved_python(shadows, open_documents):
        return fallback
    synchronized = _python_documents(open_documents)
    if synchronized is None:
        return fallback

    semantic_types: list[str] = []
    try:
        for shadow in shadows:
            virtual = _virtual_document(shadow, Path(project.status.workspace))
            for copied in shadow.document.copies:
                cursor = copied.shadow_start + shadow.cursor_offset
                hint = await analyzer.hover(
                    virtual,
                    position_at_offset(virtual.source, cursor),
                    synchronized=synchronized,
                )
                if hint is None or hint.range is None:
                    return fallback
                display_type = _python_hover_type(hint.contents)
                if display_type is None:
                    return fallback
                # The type belongs to this variable only when ty maps back to its exact token.
                mapped = map_expression_shadow_range(document, position, shadow, hint.range)
                if mapped != variable.range:
                    return fallback
                if display_type not in semantic_types:
                    semantic_types.append(display_type)
    except TyUnavailableError:
        return fallback
    if not semantic_types:
        return fallback
    return render_template_variable_hover(variable, tuple(semantic_types))


async def semantic_definition(
    analyzer: TyAnalyzer,
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState],
) -> tuple[types.Location, ...]:
    """Return exact real-source definitions and reject generated-file targets."""
    shadows = expression_shadows(document, position, project, open_documents)
    if not shadows:
        return ()
    if _has_external_unsaved_python(shadows, open_documents):
        return ()
    synchronized = _python_documents(open_documents)
    if synchronized is None:
        return ()
    generated_uris = {
        virtual_document_uri(shadow.source_file, shadow.identity, workspace=Path(project.status.workspace))
        for shadow in shadows
    }
    retained: list[types.Location] = []
    try:
        for shadow in shadows:
            virtual = _virtual_document(shadow, Path(project.status.workspace))
            for copied in shadow.document.copies:
                cursor = copied.shadow_start + shadow.cursor_offset
                locations = await analyzer.definition(
                    virtual,
                    position_at_offset(virtual.source, cursor),
                    synchronized=synchronized,
                )
                for location in locations:
                    if location.uri == virtual.uri:
                        mapped = _source_definition(shadow, location)
                        if mapped is not None:
                            retained.append(mapped)
                    elif location.uri not in generated_uris:
                        retained.append(location)
    except TyUnavailableError:
        return ()
    return _dedupe_locations(retained)


async def _fill_binding_type_definition(analyzer: TyAnalyzer) -> tuple[types.Location, ...]:
    """Resolve the current untyped fill-binding contract without choosing a use."""
    source = "from typing import Any\n__citry_fill_value: Any = None\n__citry_fill_value\n"
    document = TyDocument("citry-template-type://fill-binding.py", source)
    cursor = source.rindex("__citry_fill_value") + len("__citry_fill")
    try:
        locations = await analyzer.type_definition(document, position_at_offset(source, cursor))
    except TyUnavailableError:
        return ()
    return _dedupe_locations(list(locations))


async def semantic_type_definition(
    analyzer: TyAnalyzer,
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState],
) -> tuple[types.Location, ...]:
    """Return type declarations only when every proven expression copy agrees."""
    # This first slice belongs only to Citry-owned variables. Member and
    # Python-local identities need their own analyzer-backed reference model.
    variable = template_variable_hover(document, position, project, open_documents)
    if variable is None:
        return ()
    if variable.binding_kind in {"slot-data", "slot-data-rest", "fallback"}:
        # Fill bindings currently have the deliberate analyzer type Any. Probe
        # that neutral contract directly, so an unused declaration works and a
        # later narrowed use cannot change the declaration's answer.
        return await _fill_binding_type_definition(analyzer)
    shadows = expression_shadows(document, position, project, open_documents)
    if not shadows or _has_external_unsaved_python(shadows, open_documents):
        return ()
    synchronized = _python_documents(open_documents)
    if synchronized is None:
        return ()
    generated_uris = {
        virtual_document_uri(shadow.source_file, shadow.identity, workspace=Path(project.status.workspace))
        for shadow in shadows
    }
    retained: list[types.Location] = []
    try:
        for shadow in shadows:
            virtual = _virtual_document(shadow, Path(project.status.workspace))
            for copied in shadow.document.copies:
                cursor = copied.shadow_start + shadow.cursor_offset
                locations = await analyzer.type_definition(
                    virtual,
                    position_at_offset(virtual.source, cursor),
                    synchronized=synchronized,
                )
                # One missing consumer or return path means the shared answer
                # is not proven for the authored variable.
                if not locations:
                    return ()
                mapped_locations: list[types.Location] = []
                for location in locations:
                    if location.uri == virtual.uri:
                        mapped = _source_definition(shadow, location)
                        if mapped is None:
                            return ()
                        mapped_locations.append(mapped)
                    elif location.uri in generated_uris:
                        return ()
                    else:
                        mapped_locations.append(location)
                if not mapped_locations:
                    return ()
                retained.extend(mapped_locations)
    except TyUnavailableError:
        return ()
    return _dedupe_locations(retained)


async def semantic_signature_help(
    analyzer: TyAnalyzer,
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState],
) -> types.SignatureHelp | None:
    """Keep only call signatures that apply to every proven expression copy."""
    shadows = expression_shadows(
        document,
        position,
        project,
        open_documents,
        repair_signature=True,
    )
    if not shadows:
        return None
    direct = _i18n_formatter_signature_help(shadows[0])
    if direct is not None:
        return direct
    if _has_external_unsaved_python(shadows, open_documents):
        return None
    synchronized = _python_documents(open_documents)
    if synchronized is None:
        return None
    answers: list[types.SignatureHelp] = []
    try:
        for shadow in shadows:
            virtual = _virtual_document(shadow, Path(project.status.workspace))
            for copied in shadow.document.copies:
                cursor = copied.shadow_start + shadow.cursor_offset
                answer = await analyzer.signature_help(
                    virtual,
                    position_at_offset(virtual.source, cursor),
                    synchronized=synchronized,
                )
                if answer is None:
                    return None
                answers.append(answer)
    except TyUnavailableError:
        return None
    if not answers:
        return None
    shared_labels = {signature.label for signature in answers[0].signatures}
    for answer in answers[1:]:
        shared_labels.intersection_update(signature.label for signature in answer.signatures)
    signatures = tuple(signature for signature in answers[0].signatures if signature.label in shared_labels)
    if not signatures:
        return None
    active_label = None
    if answers[0].active_signature is not None and answers[0].active_signature < len(answers[0].signatures):
        active_label = answers[0].signatures[answers[0].active_signature].label
    active_signature = next(
        (index for index, signature in enumerate(signatures) if signature.label == active_label),
        None,
    )
    active_parameters = {answer.active_parameter for answer in answers}
    active_parameter = active_parameters.pop() if len(active_parameters) == 1 else None
    return types.SignatureHelp(signatures, active_signature, active_parameter)


def _i18n_formatter_completions(
    shadow: ExpressionShadow,
    ranges: tuple[types.Range, types.Range],
) -> tuple[types.CompletionItem, ...] | None:
    """Complete Citry's finite formatter API without querying user-code analysis."""
    if "fmt" not in shadow.query.free_names:
        return None
    match = re.search(
        r"(?<![\w.])fmt\.(?P<prefix>[^\W\d]\w*)?\Z",
        shadow.query.source[: shadow.cursor_offset],
    )
    if match is None:
        return None
    prefix = match.group("prefix") or ""
    insert_range, replace_range = ranges
    return tuple(
        types.CompletionItem(
            label=operation,
            kind=types.CompletionItemKind.Method,
            detail=signature,
            documentation=types.MarkupContent(
                types.MarkupKind.Markdown,
                "Locale-aware Citry i18n format operation.",
            ),
            filter_text=operation,
            text_edit=types.InsertReplaceEdit(operation, insert_range, replace_range),
        )
        for (namespace, operation), signature in sorted(_I18N_OPERATION_SIGNATURES.items())
        if namespace == "format" and operation.startswith(prefix)
    )


def _i18n_formatter_signature_help(shadow: ExpressionShadow) -> types.SignatureHelp | None:
    """Describe a simple open ``fmt`` call from Citry's canonical API table."""
    if "fmt" not in shadow.query.free_names:
        return None
    prefix = shadow.query.source[: shadow.cursor_offset].rstrip()
    matches = list(
        re.finditer(
            r"(?<![\w.])fmt\.(?P<operation>[^\W\d]\w*)\((?P<arguments>[^()]*)\Z",
            prefix,
            flags=re.DOTALL,
        )
    )
    if not matches:
        return None
    match = matches[-1]
    operation = match.group("operation")
    key = ("format", operation)
    signature = _I18N_OPERATION_SIGNATURES.get(key)
    call_shape = _I18N_CALL_SIGNATURES.get(key)
    if signature is None or call_shape is None:
        return None
    arguments = match.group("arguments")
    parameters = (*call_shape[0], *call_shape[1], *call_shape[2])
    active_parameter: int | None = None
    if parameters:
        current_argument = arguments.rsplit(",", 1)[-1].strip()
        keyword = re.match(r"(?P<name>[^\W\d]\w*)\s*=", current_argument)
        if keyword is not None and keyword.group("name") in parameters:
            active_parameter = parameters.index(keyword.group("name"))
        else:
            active_parameter = min(arguments.count(","), len(parameters) - 1)
    return types.SignatureHelp(
        signatures=(
            types.SignatureInformation(
                label=signature,
                documentation=types.MarkupContent(
                    types.MarkupKind.Markdown,
                    "Locale-aware Citry i18n format operation.",
                ),
                parameters=tuple(types.ParameterInformation(label=name) for name in parameters),
            ),
        ),
        active_signature=0,
        active_parameter=active_parameter,
    )


async def semantic_diagnostics(
    analyzer: TyAnalyzer,
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState],
) -> tuple[types.Diagnostic, ...]:
    """Return only analyzer findings wholly inside authored expressions."""
    groups = all_expression_shadows(document, project, open_documents)
    if not groups:
        return ()
    if _has_external_unsaved_python(
        tuple(shadow for group in groups for shadow in group.shadows),
        open_documents,
    ):
        return ()
    synchronized = _python_documents(open_documents)
    if synchronized is None:
        return ()
    retained: list[types.Diagnostic] = []
    try:
        for diagnostic_document in _diagnostic_documents(groups, Path(project.status.workspace)):
            findings = await analyzer.diagnostics(
                diagnostic_document.virtual,
                synchronized=synchronized,
            )
            for finding in findings:
                if finding.code is None or finding.code == "unresolved-reference":
                    # Step 17 owns unknown-root policy and project globals.
                    continue
                mapped = _map_diagnostic_range(document, diagnostic_document, finding.range)
                if mapped is None:
                    continue
                code = f"citry.python.{finding.code}"
                retained.append(
                    types.Diagnostic(
                        mapped,
                        finding.message,
                        severity=finding.severity,
                        code=code,
                        code_description=(types.CodeDescription(finding.href) if finding.href is not None else None),
                        source="Citry (ty)",
                    )
                )
    except TyUnavailableError:
        return ()
    return _dedupe_diagnostics(retained)


@dataclass(frozen=True, slots=True)
class _DiagnosticExpressionCopy:
    """One authored expression copy inside a batched analyzer document."""

    position: types.Position
    shadow: ExpressionShadow
    combined_start: int
    combined_end: int
    original_start: int


@dataclass(frozen=True, slots=True)
class _DiagnosticDocument:
    """One analyzer request plus every exact expression range it contains."""

    virtual: TyDocument
    copies: tuple[_DiagnosticExpressionCopy, ...]


def _diagnostic_documents(
    groups: tuple[ExpressionShadowGroup, ...],
    workspace: Path,
) -> tuple[_DiagnosticDocument, ...]:
    """Combine independent queries for one consumer into one analyzer request."""
    by_consumer: dict[tuple[str, Path, str], list[tuple[types.Position, ExpressionShadow]]] = {}
    for group in groups:
        for shadow in group.shadows:
            key = shadow.identity, shadow.source_file.resolve(), shadow.source
            by_consumer.setdefault(key, []).append((group.position, shadow))

    documents: list[_DiagnosticDocument] = []
    for entries in by_consumer.values():
        combined = _combined_diagnostic_document(entries, workspace)
        if combined is not None:
            documents.append(combined)
            continue
        # Any unexpected generated shape keeps the exact per-query behavior.
        documents.extend(_single_diagnostic_document(position, shadow, workspace) for position, shadow in entries)
    return tuple(documents)


def _single_diagnostic_document(
    position: types.Position,
    shadow: ExpressionShadow,
    workspace: Path,
) -> _DiagnosticDocument:
    copies = tuple(
        _DiagnosticExpressionCopy(
            position,
            shadow,
            copied.shadow_start,
            copied.shadow_end,
            copied.shadow_start,
        )
        for copied in shadow.document.copies
    )
    return _DiagnosticDocument(_virtual_document(shadow, workspace), copies)


def _combined_diagnostic_document(
    entries: list[tuple[types.Position, ExpressionShadow]],
    workspace: Path,
) -> _DiagnosticDocument | None:
    """Merge generated query functions only when their module context is identical."""
    if len(entries) < 2:
        position, shadow = entries[0]
        return _single_diagnostic_document(position, shadow, workspace)
    bounds = [_generated_query_function_bounds(shadow.document.source) for _, shadow in entries]
    if any(bound is None for bound in bounds):
        return None
    valid_bounds = tuple(bound for bound in bounds if bound is not None)
    first_source = entries[0][1].document.source
    first_start, first_end = valid_bounds[0]
    prefix = first_source[:first_start]
    suffix = first_source[first_end:]
    functions: list[str] = []
    copies: list[_DiagnosticExpressionCopy] = []
    combined_offset = len(prefix)
    for index, ((position, shadow), bound) in enumerate(zip(entries, valid_bounds, strict=True)):
        start, end = bound
        source = shadow.document.source
        if source[:start] != prefix or source[end:] != suffix:
            return None
        function_source = source[start:end]
        replacement = f"__citry_analyze_{index:08x}"
        if function_source.count("def __citry_analyze_template(") != 1:
            return None
        function_source = function_source.replace(
            "def __citry_analyze_template(",
            f"def {replacement}(",
            1,
        )
        if len(function_source) != end - start:
            return None
        for copied in shadow.document.copies:
            if copied.shadow_start < start or copied.shadow_end > end:
                return None
            copies.append(
                _DiagnosticExpressionCopy(
                    position,
                    shadow,
                    combined_offset + copied.shadow_start - start,
                    combined_offset + copied.shadow_end - start,
                    copied.shadow_start,
                )
            )
        functions.append(function_source)
        combined_offset += len(function_source) + 1
    functions_source = "\n".join(functions)
    combined_source = f"{prefix}{functions_source}\n{suffix}"
    first_shadow = entries[0][1]
    return _DiagnosticDocument(
        TyDocument(
            virtual_document_uri(first_shadow.source_file, first_shadow.identity, workspace=workspace),
            combined_source,
        ),
        tuple(copies),
    )


def _generated_query_function_bounds(source: str) -> tuple[int, int] | None:
    """Find the one generated query function without relying on line layout."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "__citry_analyze_template"
    ]
    if len(matches) != 1:
        return None
    node = matches[0]
    if node.end_lineno is None or node.end_col_offset is None:
        return None
    # Nested inferred-data methods need their class indentation on every copy.
    start = _ast_source_offset(source, node.lineno, 0)
    end = _ast_source_offset(source, node.end_lineno, node.end_col_offset)
    return (start, end) if start is not None and end is not None and start < end else None


def _ast_source_offset(source: str, line: int, byte_column: int) -> int | None:
    """Convert Python AST byte columns to string offsets for generated source."""
    lines = source.splitlines(keepends=True)
    if line < 1 or line > len(lines):
        return None
    raw_line = lines[line - 1].encode("utf-8")
    if byte_column < 0 or byte_column > len(raw_line):
        return None
    try:
        column = len(raw_line[:byte_column].decode("utf-8"))
    except UnicodeDecodeError:
        return None
    return sum(len(candidate) for candidate in lines[: line - 1]) + column


def _map_diagnostic_range(
    document: DocumentState,
    diagnostic_document: _DiagnosticDocument,
    finding_range: types.Range,
) -> types.Range | None:
    """Map a diagnostic only through one exact copied expression."""
    start = offset_at_position(diagnostic_document.virtual.source, finding_range.start)
    end = offset_at_position(diagnostic_document.virtual.source, finding_range.end)
    if start is None or end is None or end < start:
        return None
    for copied in diagnostic_document.copies:
        if copied.combined_start <= start <= end <= copied.combined_end:
            original_start = copied.original_start + start - copied.combined_start
            original_end = copied.original_start + end - copied.combined_start
            original_range = types.Range(
                position_at_offset(copied.shadow.document.source, original_start),
                position_at_offset(copied.shadow.document.source, original_end),
            )
            return map_expression_shadow_range(
                document,
                copied.position,
                copied.shadow,
                original_range,
            )
    return None


def _virtual_document(shadow: ExpressionShadow, workspace: Path) -> TyDocument:
    return TyDocument(
        virtual_document_uri(shadow.source_file, shadow.identity, workspace=workspace),
        shadow.document.source,
    )


def _python_documents(open_documents: Mapping[str, DocumentState]) -> tuple[TyDocument, ...] | None:
    """Forward one canonical URI per open Python file or decline aliases."""
    synchronized: dict[str, str] = {}
    for document in open_documents.values():
        if document.language_id != "python":
            continue
        path = _python_document_path(document)
        if path is None:
            return None
        uri = path.as_uri()
        previous = synchronized.get(uri)
        if previous is not None and previous != document.source:
            return None
        synchronized[uri] = document.source
    return tuple(TyDocument(uri, source) for uri, source in synchronized.items())


def _has_external_unsaved_python(
    shadows: tuple[ExpressionShadow, ...],
    open_documents: Mapping[str, DocumentState],
) -> bool:
    """Withhold results ty would otherwise resolve against stale disk imports."""
    source_files = {shadow.source_file.resolve() for shadow in shadows}
    synchronized: dict[Path, str] = {}
    for document in open_documents.values():
        if document.language_id != "python":
            continue
        path = _python_document_path(document)
        if path is None:
            return True
        previous = synchronized.get(path)
        if previous is not None and previous != document.source:
            return True
        synchronized[path] = document.source
        if path in source_files and len(source_files) == 1:
            continue
        try:
            raw_source = path.read_bytes()
            encoding, _ = tokenize.detect_encoding(io.BytesIO(raw_source).readline)
            disk_source = raw_source.decode(encoding)
        except (OSError, SyntaxError, UnicodeError):
            return True
        if path in source_files:
            # Another consumer may import this owner through its ordinary
            # module path, which ty can still resolve from disk.
            if disk_source != document.source:
                return True
            continue
        if disk_source != document.source:
            return True
    return False


def _python_document_path(document: DocumentState) -> Path | None:
    """Resolve one local editor URI to the path Python imports use."""
    path = file_uri_path(document.uri)
    if path is None:
        return None
    try:
        return path.resolve()
    except (OSError, ValueError):
        return None


def _source_definition(shadow: ExpressionShadow, location: types.Location) -> types.Location | None:
    """Map only unchanged module text back from a generated sibling."""
    start = offset_at_position(shadow.document.source, location.range.start)
    end = offset_at_position(shadow.document.source, location.range.end)
    if start is None or end is None or end < start:
        return None
    for copied in shadow.document.source_copies:
        if copied.shadow_start <= start <= end <= copied.shadow_end:
            source_start = copied.source_start + start - copied.shadow_start
            source_end = copied.source_start + end - copied.shadow_start
            if source_end > len(shadow.source):
                return None
            return types.Location(
                shadow.source_file.resolve().as_uri(),
                types.Range(
                    position_at_offset(shadow.source, source_start),
                    position_at_offset(shadow.source, source_end),
                ),
            )
    return None


def _shared_sort_text(label: str, answers: list[dict[str, TyCompletion]]) -> str:
    values: list[str] = []
    for answer in answers:
        value = answer[label].sort_text
        if value is not None:
            values.append(value)
    return min(values) if values else label


def _shared_or_distinct(values: Iterable[str | None]) -> str | None:
    distinct: list[str] = []
    for value in values:
        if isinstance(value, str) and value not in distinct:
            distinct.append(value)
    return " | ".join(distinct) if distinct else None


def _shared_markup(values: Iterable[types.MarkupContent | None]) -> types.MarkupContent | None:
    retained = [value for value in values if isinstance(value, types.MarkupContent)]
    if not retained:
        return None
    first = retained[0]
    return first if all(value == first for value in retained) else None


def _python_hover_type(content: types.MarkupContent) -> str | None:
    """Read the pinned analyzer's exact one-line Python type block."""
    if content.kind != types.MarkupKind.Markdown:
        return None
    match = re.fullmatch(r"```python\r?\n([^\r\n]+)\r?\n```", content.value.strip())
    return match.group(1).strip() if match is not None else None


def _dedupe_locations(locations: list[types.Location]) -> tuple[types.Location, ...]:
    seen: set[tuple[str, int, int, int, int]] = set()
    retained: list[types.Location] = []
    for location in locations:
        key = (
            location.uri,
            location.range.start.line,
            location.range.start.character,
            location.range.end.line,
            location.range.end.character,
        )
        if key not in seen:
            seen.add(key)
            retained.append(location)
    return tuple(retained)


def _dedupe_diagnostics(diagnostics: list[types.Diagnostic]) -> tuple[types.Diagnostic, ...]:
    seen: set[tuple[int, int, int, int, str, str | int | None]] = set()
    retained: list[types.Diagnostic] = []
    for diagnostic in diagnostics:
        key = (
            diagnostic.range.start.line,
            diagnostic.range.start.character,
            diagnostic.range.end.line,
            diagnostic.range.end.character,
            diagnostic.message,
            diagnostic.code,
        )
        if key not in seen:
            seen.add(key)
            retained.append(diagnostic)
    return tuple(retained)


__all__ = [
    "semantic_completions",
    "semantic_definition",
    "semantic_diagnostics",
    "semantic_hover",
    "semantic_signature_help",
    "semantic_type_definition",
    "semantic_variable_hover",
]
