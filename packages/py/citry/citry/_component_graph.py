"""Build authored component-template dependency graphs from registry snapshots."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from citry._class_introspection import (
    _safe_class_import_path,
    _safe_class_text,
    _static_class_dict,
    _static_class_mro,
)
from citry._component_introspection import (
    _group_registrations,
    _installed_citry_version,
    _loaded_python_file,
    _primary_name,
)
from citry._inline_assets import normalize_inline_asset
from citry.analysis import LspPosition, LspRange
from citry.assets import _find_pair_declaration, _inspect_asset_path
from citry.component_graph import (
    ComponentGraph,
    ComponentGraphLocation,
    ComponentGraphNode,
    ComponentGraphProblem,
    ComponentGraphReference,
    UnresolvedComponentReference,
)
from citry_core.template_parser import (
    RESERVED_TAG_NAMES,
    HtmlAttrKind,
    ParseOptions,
    TemplateElement,
    parse_diagnostic,
    parse_template,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry
    from citry.component import Component
    from citry_core.template_parser import ForeignSpan as CoreForeignSpan


@dataclass(frozen=True, slots=True)
class _Consumer:
    """One selected graph node consuming an effective template declaration."""

    component_class: type[Component]
    node: ComponentGraphNode
    declared_on: str | None
    declaration_file: Path | None


@dataclass(slots=True)
class _Source:
    """One physical authored template and every selected registry consumer."""

    origin: str
    source_kind: Literal["inline", "file"]
    content: str | None
    template_file: Path | None
    consumers: list[_Consumer] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _Occurrence:
    """One source-relative component invocation before consumer projection."""

    authored_name: str | None
    syntax: Literal["tag", "static-selector", "dynamic-selector"]
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class _SourceProblem:
    """One source-level failure before consumer definition IDs are attached."""

    code: str
    message: str
    start_index: int | None = None
    end_index: int | None = None


def _effective_class_value(comp_cls: type[Component], name: str) -> object:
    """Read one effective class value without invoking metaclass hooks."""
    for candidate in _static_class_mro(comp_cls):
        namespace = _static_class_dict(candidate)
        if name in namespace:
            return namespace[name]
    return None


def _class_label(comp_cls: type[Component]) -> str:
    """Return a stable readable class label without calling user code."""
    return _safe_class_import_path(comp_cls) or _safe_class_text(comp_cls, "__name__") or "Component"


def _error_detail(exc: BaseException) -> str:
    """Return compact text for one isolated graph-source failure."""
    detail = str(exc).strip()
    return detail or type(exc).__name__


def _build_node(
    engine: Citry,
    comp_cls: type[Component],
    names: tuple[str, ...],
    *,
    builtin: bool,
) -> ComponentGraphNode:
    """Copy graph identity fields from one registered class generation."""
    namespace = _static_class_dict(comp_cls)
    primary_name = _primary_name(comp_cls, names)
    return ComponentGraphNode(
        class_id=cast("str", namespace.get("_class_id")),
        engine_id=engine.engine_id,
        definition_id=cast("str", namespace.get("_definition_id")),
        name=primary_name,
        aliases=tuple(name for name in names if name != primary_name),
        builtin=builtin,
    )


def _problem_for_nodes(
    nodes: tuple[ComponentGraphNode, ...],
    code: str,
    message: str,
    origin: str,
    location: ComponentGraphLocation | None = None,
) -> ComponentGraphProblem:
    """Build one canonical public problem for selected nodes."""
    return ComponentGraphProblem(
        component_definition_ids=tuple(sorted(node.definition_id for node in nodes)),
        code=code,
        message=message,
        origin=origin,
        location=location,
    )


def _coalesce_problems(problems: list[ComponentGraphProblem]) -> list[ComponentGraphProblem]:
    """Combine identical physical-source failures across inherited consumers."""
    grouped: dict[tuple[object, ...], set[str]] = {}
    examples: dict[tuple[object, ...], ComponentGraphProblem] = {}
    for problem in problems:
        key = (problem.code, problem.message, problem.origin, problem.location)
        examples.setdefault(key, problem)
        grouped.setdefault(key, set()).update(problem.component_definition_ids)
    return [
        ComponentGraphProblem(
            component_definition_ids=tuple(sorted(grouped[key])),
            code=problem.code,
            message=problem.message,
            origin=problem.origin,
            location=problem.location,
        )
        for key, problem in examples.items()
    ]


def _collect_sources(
    engine: Citry,
    selected: tuple[tuple[type[Component], ComponentGraphNode], ...],
) -> tuple[dict[tuple[object, ...], _Source], list[ComponentGraphProblem]]:
    """Resolve effective authored primary templates without loading them."""
    sources: dict[tuple[object, ...], _Source] = {}
    problems: list[ComponentGraphProblem] = []
    for comp_cls, node in selected:
        class_label = _class_label(comp_cls)
        try:
            owner, inline, filepath = _find_pair_declaration(comp_cls, "template", "template_file")
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - isolate one declaration
            problems.append(
                _problem_for_nodes(
                    (node,),
                    "template-declaration",
                    f"Could not inspect the primary template declaration: {_error_detail(exc)}",
                    class_label,
                )
            )
            continue

        if inline is None and filepath is None:
            continue
        language = _effective_class_value(comp_cls, "template_lang")
        if language is not None:
            problems.append(
                _problem_for_nodes(
                    (node,),
                    "template-language-unsupported",
                    f"Static component graphs support the default template language, not {language!r}.",
                    class_label,
                )
            )
            continue

        declared_on = _safe_class_import_path(owner)
        declaration_file = _loaded_python_file(owner)
        consumer = _Consumer(comp_cls, node, declared_on, declaration_file)
        declaration_origin = declared_on or _class_label(owner)
        if inline is not None:
            if type(inline) is not str:
                problems.append(
                    _problem_for_nodes(
                        (node,),
                        "template-value-invalid",
                        "The inline primary template must be a string.",
                        f"{declaration_origin}.template",
                    )
                )
                continue
            inline_key = ("inline", id(owner))
            source = sources.get(inline_key)
            if source is None:
                source = _Source(
                    origin=f"{declaration_origin}.template",
                    source_kind="inline",
                    content=normalize_inline_asset(inline),
                    template_file=None,
                )
                sources[inline_key] = source
            source.consumers.append(consumer)
            continue

        if not isinstance(filepath, (str, Path)):
            problems.append(
                _problem_for_nodes(
                    (node,),
                    "template-value-invalid",
                    "The primary template file must be a string or pathlib.Path.",
                    f"{declaration_origin}.template_file",
                )
            )
            continue
        try:
            inspection = _inspect_asset_path(
                filepath,
                owner_dir=declaration_file.parent if declaration_file is not None else None,
                search_dirs=engine.settings.dirs,
            )
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - isolate one path declaration
            problems.append(
                _problem_for_nodes(
                    (node,),
                    "template-file-unreadable",
                    f"Could not inspect primary template path {str(filepath)!r}: {_error_detail(exc)}",
                    f"{declaration_origin}.template_file",
                )
            )
            continue
        resolved = inspection.resolved_path
        if resolved is None:
            searched = ", ".join(path.as_posix() for path in inspection.searched_paths)
            locations = searched or "no searchable locations"
            problems.append(
                _problem_for_nodes(
                    (node,),
                    "template-file-not-found",
                    f"Could not find primary template file {str(filepath)!r}; searched {locations}.",
                    f"{declaration_origin}.template_file",
                )
            )
            continue
        resolved_identity = resolved.resolve()
        file_key = ("file", resolved_identity)
        source = sources.get(file_key)
        if source is None:
            source = _Source(
                origin=resolved_identity.as_posix(),
                source_kind="file",
                content=None,
                template_file=resolved_identity,
            )
            sources[file_key] = source
        source.consumers.append(consumer)

    for source in sources.values():
        if source.content is not None:
            continue
        template_file = source.template_file
        if template_file is None:  # pragma: no cover - private invariant
            continue
        try:
            source.content = template_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            problems.append(
                _problem_for_nodes(
                    tuple(consumer.node for consumer in source.consumers),
                    "template-file-unreadable",
                    f"Could not read primary template file: {_error_detail(exc)}",
                    source.origin,
                )
            )
    return sources, _coalesce_problems(problems)


def _foreign_options(
    engine: Citry,
    source: _Source,
    content: str,
    *,
    template_kind: Literal["primary", "nested"],
) -> tuple[ParseOptions | None, _SourceProblem | None]:
    """Collect one consumer-independent provider-span view for graph parsing."""
    digest = hashlib.sha256()
    digest.update(source.origin.encode())
    digest.update(b"\0")
    digest.update(template_kind.encode())
    digest.update(b"\0")
    digest.update(content.encode())
    template_id = f"component-graph:{digest.hexdigest()}"

    agreed_spans: tuple[CoreForeignSpan, ...] | None = None
    agreed_descriptor: tuple[tuple[object, ...], ...] | None = None
    try:
        for consumer in source.consumers:
            spans, _metadata = engine.extensions.on_template_foreign_spans(
                consumer.component_class,
                content,
                template_id=template_id,
                origin=source.origin,
                template_kind=template_kind,
            )
            typed_spans = cast("tuple[CoreForeignSpan, ...]", spans)
            descriptor = tuple(
                (span.start_byte, span.end_byte, span.provider, span.ordinal, span.may_control_body)
                for span in typed_spans
            )
            if agreed_descriptor is None:
                agreed_spans = typed_spans
                agreed_descriptor = descriptor
            elif descriptor != agreed_descriptor:
                msg = "Components sharing this template disagree about its foreign source spans."
                return None, _SourceProblem("template-namespace-unavailable", msg)
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - isolate one provider namespace
        return None, _SourceProblem(
            "template-namespace-unavailable",
            f"Could not inspect foreign template spans: {_error_detail(exc)}",
        )

    if not agreed_spans:
        return None, None
    validation_error = _foreign_span_error(content, agreed_spans)
    if validation_error is not None:
        return None, _SourceProblem(
            "template-namespace-unavailable",
            f"Could not inspect foreign template spans: {validation_error}",
        )
    controlling = next((span for span in agreed_spans if span.may_control_body), None)
    problem = None
    if controlling is not None:
        problem = _SourceProblem(
            "foreign-source-controls-body",
            "A host-template provider controls this source body, so authored Citry dependencies may be hidden.",
            controlling.start_byte,
            controlling.end_byte,
        )
    return ParseOptions(list(agreed_spans)), problem


def _foreign_span_error(content: str, spans: tuple[CoreForeignSpan, ...]) -> str | None:
    """Validate provider ranges before using them as authored locations."""
    content_bytes = content.encode()
    ordered = sorted(spans, key=lambda span: (span.start_byte, span.end_byte, span.provider, span.ordinal))
    claim_ids: set[tuple[str, int]] = set()
    previous_end = 0
    for index, span in enumerate(ordered):
        start = span.start_byte
        end = span.end_byte
        if start < 0 or start >= end:
            return f"span {start}..{end} must have a non-empty forward range"
        if end > len(content_bytes):
            return f"span {start}..{end} exceeds the {len(content_bytes)}-byte template"
        try:
            content_bytes[:start].decode()
            content_bytes[:end].decode()
        except UnicodeDecodeError:
            return f"span {start}..{end} does not begin and end on UTF-8 boundaries"
        if index and start < previous_end:
            return f"span {start}..{end} overlaps an earlier provider span"
        claim_id = (span.provider, span.ordinal)
        if claim_id in claim_ids:
            return f"provider claim {span.provider!r}/{span.ordinal} is duplicated"
        claim_ids.add(claim_id)
        previous_end = end
    return None


def _nested_content(source: str) -> tuple[str, int]:
    """Remove one fragment wrapper and return content plus its UTF-8 byte base."""
    stripped = source.lstrip()
    leading_chars = len(source) - len(stripped)
    trailing = stripped.rstrip()
    if stripped.startswith("<>") and trailing.endswith("</>"):
        content_start = leading_chars + len("<>")
        content_end = leading_chars + len(trailing) - len("</>")
    else:
        content_start = leading_chars
        content_end = len(source.rstrip())
    content_end = max(content_start, content_end)
    byte_base = len(source[:content_start].encode())
    return source[content_start:content_end], byte_base


def _diagnostic_problem(
    exc: BaseException,
    *,
    code: Literal["template-syntax", "nested-template-syntax"],
    base_index: int,
) -> _SourceProblem:
    """Convert one parser failure to a root-source-relative graph problem."""
    diagnostic = parse_diagnostic(exc)
    start_index = getattr(diagnostic, "start_index", None) if diagnostic is not None else None
    end_index = getattr(diagnostic, "end_index", None) if diagnostic is not None else None
    return _SourceProblem(
        code,
        _error_detail(exc),
        base_index + start_index if type(start_index) is int else None,
        base_index + end_index if type(end_index) is int else None,
    )


def _selector_occurrence(node: Any, *, base_index: int) -> _Occurrence | None:
    """Classify one opening tag as a static or dynamic component reference."""
    tag_token = node.start_tag.name
    tag = tag_token.content
    if not tag.startswith("c-"):
        return None
    normalized_tag = tag.casefold()
    if normalized_tag == "c-element" or normalized_tag in RESERVED_TAG_NAMES:
        return None
    if normalized_tag != "c-component":
        return _Occurrence(
            authored_name=tag[len("c-") :],
            syntax="tag",
            start_index=base_index + tag_token.start_index,
            end_index=base_index + tag_token.end_index,
        )

    attrs = node.start_tag.attrs
    spread = next((attr for attr in attrs if attr.key.content == "c-bind"), None)
    static_is = next((attr for attr in attrs if attr.key.content == "is"), None)
    if spread is None and static_is is not None and static_is.inner_value is not None:
        token = static_is.inner_value
        return _Occurrence(
            authored_name=token.content,
            syntax="static-selector",
            start_index=base_index + token.start_index,
            end_index=base_index + token.end_index,
        )

    dynamic_is = next((attr for attr in attrs if attr.key.content == "c-is"), None)
    locus = dynamic_is or spread
    token = locus.inner_value if locus is not None and locus.inner_value is not None else tag_token
    return _Occurrence(
        authored_name=None,
        syntax="dynamic-selector",
        start_index=base_index + token.start_index,
        end_index=base_index + token.end_index,
    )


def _walk_template(
    engine: Citry,
    source: _Source,
    template: object,
    occurrences: list[_Occurrence],
    problems: list[_SourceProblem],
    *,
    base_index: int,
) -> None:
    """Collect opening component tags, including recursively nested templates."""
    elements = getattr(template, "elements", None)
    if type(elements) is not list:  # pragma: no cover - parser contract guard
        problems.append(_SourceProblem("template-syntax", "The parser returned an invalid template AST."))
        return
    for element in elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        occurrence = _selector_occurrence(node, base_index=base_index)
        if occurrence is not None:
            occurrences.append(occurrence)
        body = getattr(node, "body", None)
        if body is not None:
            _walk_template(engine, source, body, occurrences, problems, base_index=base_index)
        for attr in node.start_tag.attrs:
            if attr.inner_value is None or attr.kind != HtmlAttrKind.Template:
                continue
            nested_source, nested_value_base = _nested_content(attr.inner_value.content)
            nested_base = base_index + attr.inner_value.start_index + nested_value_base
            options, namespace_problem = _foreign_options(
                engine,
                source,
                nested_source,
                template_kind="nested",
            )
            if namespace_problem is not None:
                problems.append(
                    _SourceProblem(
                        namespace_problem.code,
                        namespace_problem.message,
                        nested_base + namespace_problem.start_index
                        if namespace_problem.start_index is not None
                        else None,
                        nested_base + namespace_problem.end_index if namespace_problem.end_index is not None else None,
                    )
                )
                if namespace_problem.code == "template-namespace-unavailable":
                    continue
            try:
                nested = parse_template(nested_source, options=options)
            except (SyntaxError, ValueError) as exc:
                problems.append(_diagnostic_problem(exc, code="nested-template-syntax", base_index=nested_base))
                continue
            _walk_template(
                engine,
                source,
                nested,
                occurrences,
                problems,
                base_index=nested_base,
            )


def _inspect_source(
    engine: Citry,
    source: _Source,
) -> tuple[list[_Occurrence], list[_SourceProblem]]:
    """Parse one physical source and collect source-relative graph facts."""
    content = source.content
    if content is None:
        return [], []
    try:
        content.encode("utf-8")
    except UnicodeEncodeError:
        return [], [
            _SourceProblem(
                "template-value-invalid",
                "The inline primary template must not contain unpaired Unicode surrogate code points.",
            )
        ]
    options, namespace_problem = _foreign_options(engine, source, content, template_kind="primary")
    problems = [namespace_problem] if namespace_problem is not None else []
    if namespace_problem is not None and namespace_problem.code == "template-namespace-unavailable":
        return [], problems
    try:
        template = parse_template(content, options=options)
    except (SyntaxError, ValueError) as exc:
        problems.append(_diagnostic_problem(exc, code="template-syntax", base_index=0))
        return [], problems
    occurrences: list[_Occurrence] = []
    _walk_template(engine, source, template, occurrences, problems, base_index=0)
    occurrences.sort(key=lambda item: (item.start_index, item.end_index, item.syntax, item.authored_name or ""))
    return occurrences, problems


def _utf16_position(source: str, byte_index: int) -> LspPosition:
    """Convert one root-template UTF-8 byte boundary to an LSP position."""
    prefix = source.encode()[:byte_index].decode()
    line = prefix.count("\n")
    current_line = prefix.rsplit("\n", 1)[-1]
    return LspPosition(line, len(current_line.encode("utf-16-le")) // 2)


def _location(
    source: _Source,
    consumer: _Consumer | None,
    start_index: int,
    end_index: int,
) -> ComponentGraphLocation:
    """Build one public location in the normalized root template."""
    content = source.content or ""
    return ComponentGraphLocation(
        origin=source.origin,
        source_kind=source.source_kind,
        declared_on=consumer.declared_on if consumer is not None else None,
        declaration_file=consumer.declaration_file if consumer is not None else None,
        template_file=source.template_file,
        start_index=start_index,
        end_index=end_index,
        source_range=LspRange(
            _utf16_position(content, start_index),
            _utf16_position(content, end_index),
        ),
    )


def _problem_location(
    source: _Source,
    problem: _SourceProblem,
) -> ComponentGraphLocation | None:
    """Build a shared-source location without inventing ambiguous provenance."""
    if problem.start_index is None or problem.end_index is None:
        return None
    first = source.consumers[0] if source.consumers else None
    provenance = first
    if first is not None and any(
        consumer.declared_on != first.declared_on or consumer.declaration_file != first.declaration_file
        for consumer in source.consumers[1:]
    ):
        provenance = None
    return _location(source, provenance, problem.start_index, problem.end_index)


def _location_sort_key(location: ComponentGraphLocation) -> tuple[object, ...]:
    return (
        location.origin,
        location.source_kind,
        location.declared_on or "",
        location.declaration_file.as_posix() if location.declaration_file is not None else "",
        location.template_file.as_posix() if location.template_file is not None else "",
        location.start_index,
        location.end_index,
        location.source_range.start.line,
        location.source_range.start.character,
        location.source_range.end.line,
        location.source_range.end.character,
    )


def _reference_sort_key(reference: ComponentGraphReference) -> tuple[object, ...]:
    location = reference.location
    return (
        reference.source_definition_id,
        *_location_sort_key(location),
        reference.target_definition_id,
        reference.registered_name,
        reference.authored_name,
        reference.syntax,
    )


def _unresolved_sort_key(reference: UnresolvedComponentReference) -> tuple[object, ...]:
    location = reference.location
    return (
        reference.source_definition_id,
        *_location_sort_key(location),
        reference.reason,
        reference.authored_name or "",
        reference.syntax,
    )


def _problem_sort_key(problem: ComponentGraphProblem) -> tuple[object, ...]:
    return (
        problem.component_definition_ids,
        problem.origin,
        problem.code,
        problem.message,
        *((0,) if problem.location is None else (1, *_location_sort_key(problem.location))),
    )


def _build_component_graph(
    engine: Citry,
    registrations: Mapping[str, type[Component]],
    *,
    include_builtins: bool,
) -> ComponentGraph:
    """Build one graph from an already-copied registry snapshot."""
    groups = _group_registrations(registrations)
    all_records = [
        (
            comp_cls,
            _build_node(
                engine,
                comp_cls,
                names,
                builtin=engine._is_builtin_component(comp_cls),
            ),
        )
        for comp_cls, names in groups
    ]
    all_by_class_identity = {id(comp_cls): node for comp_cls, node in all_records}
    selected = tuple((comp_cls, node) for comp_cls, node in all_records if include_builtins or not node.builtin)
    selected_node_ids = {node.definition_id for _comp_cls, node in selected}
    nodes = tuple(sorted((node for _comp_cls, node in selected), key=lambda item: (item.name, item.class_id)))
    registry_targets = {
        name.lower(): (comp_cls, all_by_class_identity[id(comp_cls)]) for name, comp_cls in registrations.items()
    }

    sources, problems = _collect_sources(engine, selected)
    references: list[ComponentGraphReference] = []
    unresolved: list[UnresolvedComponentReference] = []
    for source in sorted(sources.values(), key=lambda item: (item.origin, item.source_kind)):
        if source.content is None:
            continue
        occurrences, source_problems = _inspect_source(engine, source)
        affected_nodes = tuple(consumer.node for consumer in source.consumers)
        problems.extend(
            _problem_for_nodes(
                affected_nodes,
                problem.code,
                problem.message,
                source.origin,
                _problem_location(source, problem),
            )
            for problem in source_problems
        )
        for consumer in source.consumers:
            for occurrence in occurrences:
                location = _location(source, consumer, occurrence.start_index, occurrence.end_index)
                if occurrence.authored_name is None:
                    unresolved.append(
                        UnresolvedComponentReference(
                            source_definition_id=consumer.node.definition_id,
                            authored_name=None,
                            reason="dynamic-target",
                            syntax="dynamic-selector",
                            location=location,
                        )
                    )
                    continue
                normalized = occurrence.authored_name.lower()
                target = registry_targets.get(normalized)
                if target is None:
                    unresolved.append(
                        UnresolvedComponentReference(
                            source_definition_id=consumer.node.definition_id,
                            authored_name=occurrence.authored_name,
                            reason="unknown-component",
                            syntax=occurrence.syntax,
                            location=location,
                        )
                    )
                    continue
                _target_class, target_node = target
                if target_node.definition_id not in selected_node_ids:
                    continue
                references.append(
                    ComponentGraphReference(
                        source_definition_id=consumer.node.definition_id,
                        target_definition_id=target_node.definition_id,
                        registered_name=normalized,
                        authored_name=occurrence.authored_name,
                        syntax=cast("Literal['tag', 'static-selector']", occurrence.syntax),
                        location=location,
                    )
                )

    references.sort(key=_reference_sort_key)
    unresolved.sort(key=_unresolved_sort_key)
    problems.sort(key=_problem_sort_key)
    return ComponentGraph(
        schema_version=1,
        citry_version=_installed_citry_version(),
        engine_id=engine.engine_id,
        nodes=nodes,
        references=tuple(references),
        unresolved=tuple(unresolved),
        problems=tuple(problems),
    )


__all__: list[str] = []
