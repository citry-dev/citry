"""Parser-backed diagnostics and narrow editor intelligence."""

from __future__ import annotations

import ast
import io
import re
import tokenize
import unicodedata
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlparse

from lsprotocol import types

from citry import LspPosition, LspRange
from citry_core.template_parser import (
    HTML_VOID_ELEMENTS,
    RESERVED_TAG_NAMES,
    HtmlAttrKind,
    TemplateElement,
    parse_diagnostic,
    parse_template,
)
from citry_lsp.regions import (
    TemplateRegion,
    discover_python_regions,
    document_offset_at,
    parser_char_index,
    region_at_position,
    standalone_region,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry_lsp.catalog import CatalogIndex, ComponentRecord, FieldRecord
    from citry_lsp.project import ProjectState


@dataclass(frozen=True, slots=True)
class ParsedRegion:
    """One successfully parsed template region."""

    region: TemplateRegion
    template: Any


@dataclass(frozen=True, slots=True)
class CompletionResult:
    """Completion items plus whether the client should query again while typing."""

    items: tuple[types.CompletionItem, ...]
    is_incomplete: bool = False


@dataclass(frozen=True, slots=True)
class _AttributeCompletionContext:
    """The exact authored attribute name that one completion should replace."""

    edit_range: types.Range
    authored_attrs: frozenset[str]
    preserve_value: bool


@dataclass(frozen=True, slots=True)
class _LexicalBinding:
    """One parser-proven template-local name and its authored definition."""

    name: str
    start_index: int
    end_index: int
    kind: str
    source_name: str | None = None


@dataclass(frozen=True, slots=True)
class _LexicalReference:
    """A lexical binding together with the exact queried token span."""

    binding: _LexicalBinding
    start_index: int
    end_index: int


@dataclass(slots=True)
class DocumentState:
    """Current analysis and last valid parse for one open document."""

    uri: str
    language_id: str
    source: str
    version: int | None
    regions: tuple[TemplateRegion, ...] = ()
    parsed: dict[str, ParsedRegion] = field(default_factory=dict)
    last_good: dict[str, ParsedRegion] = field(default_factory=dict)
    diagnostics: tuple[types.Diagnostic, ...] = ()

    def update(self, source: str, version: int | None, project: ProjectState) -> None:
        """Replace source, analyze definite regions, and retain valid trees."""
        self.source = source
        self.version = version
        discovery: tuple[TemplateRegion, ...]
        if self.language_id == "citry-html" or (
            self.language_id == "html" and project.catalog is not None and project.catalog.owns_template_uri(self.uri)
        ):
            discovery = (standalone_region(source),)
        elif self.language_id == "python":
            discovery = discover_python_regions(source).regions
        else:
            discovery = ()
        self.regions = discovery
        diagnostics: list[types.Diagnostic] = []
        parsed: dict[str, ParsedRegion] = {}
        for region in discovery:
            result, findings = _parse_region(region, project)
            diagnostics.extend(findings)
            if result is not None:
                parsed[region.key] = result
                self.last_good[region.key] = result
        self.parsed = parsed
        self.diagnostics = tuple(diagnostics)

    def region_at(self, position: types.Position) -> TemplateRegion | None:
        """Return the current region containing an LSP position."""
        return region_at_position(self.regions, _citry_position(position))

    def parsed_at(self, position: types.Position) -> ParsedRegion | None:
        """Return a current parse, falling back only for the same region key."""
        region = self.region_at(position)
        if region is None:
            return None
        return self.parsed.get(region.key) or self.last_good.get(region.key)


def completion_items(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
) -> list[types.CompletionItem]:
    """Return completion items without the surrounding LSP list metadata."""
    return list(completion_result(document, position, project).items)


def completion_result(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
) -> CompletionResult:
    """Return schema-free and optional registry-backed completions."""
    catalog = project.catalog
    region = document.region_at(position)
    if region is None:
        return CompletionResult(())
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return CompletionResult(())
    cursor = parser_char_index(region.source_map.template_source, parser_index)
    source = region.source_map.template_source
    before = source[:cursor]

    template_fields = _template_data_fields(document, region, catalog) if catalog is not None else ()
    parsed = document.parsed.get(region.key)
    if parsed is not None:
        lexical = _lexical_bindings_at(parsed.template, parser_index, ())
        if lexical is not None:
            if not _root_completion_context(source, cursor):
                return CompletionResult((), is_incomplete=True)
            insert_range, replace_range = _expression_completion_ranges(region, source, cursor)
            return CompletionResult(
                tuple(
                    _expression_completions(
                        lexical,
                        template_fields,
                        insert_range=insert_range,
                        replace_range=replace_range,
                    )
                ),
                is_incomplete=True,
            )
    # Empty dynamic attributes and unfinished expressions do not have a valid
    # tree, so recover only those broken buffers from the current text.
    if parsed is None and _inside_unfinished_python_expression(source, cursor):
        if not _root_completion_context(source, cursor):
            return CompletionResult((), is_incomplete=True)
        insert_range, replace_range = _expression_completion_ranges(region, source, cursor)
        return CompletionResult(
            tuple(
                _expression_completions(
                    _current_text_lexical_bindings(source, cursor),
                    template_fields,
                    insert_range=insert_range,
                    replace_range=replace_range,
                )
            ),
            is_incomplete=True,
        )

    tag_match = re.search(r"<(/?)(c-[A-Za-z0-9_.-]*)$", before)
    tag_context = None
    if tag_match is not None:
        tag_context = _open_end_tag(before) if tag_match.group(1) else _open_start_tag(before)
    if tag_match is not None and tag_context is not None and tag_context[0] == tag_match.group(2):
        tag_range = _tag_completion_range(
            document,
            region,
            source,
            tag_match.start(2),
            cursor,
        )
        if tag_range is None:
            return CompletionResult((), is_incomplete=True)
        closing = bool(tag_match.group(1))
        authored_attrs, close_start_tag = _tag_completion_tail(source, cursor)
        structural = _structural_tag_completions(
            closing=closing,
            edit_range=tag_range,
            close_start_tag=not closing and close_start_tag,
            authored_attrs=authored_attrs,
        )
        registered = (
            _component_completions(
                catalog,
                tag_match.group(2),
                edit_range=tag_range,
            )
            if catalog is not None
            else []
        )
        return CompletionResult((*structural, *registered), is_incomplete=True)

    open_tags = _unfinished_start_tag_chain(before)
    if not open_tags:
        return CompletionResult(())
    tag_start, tag_name, tag_text = open_tags[-1]
    component = catalog.get_tag(tag_name) if catalog is not None else None
    if tag_name == "c-fill" and _inside_static_name_value(tag_text):
        parent = _parent_component(source, cursor, catalog) if catalog is not None else None
        return CompletionResult(
            tuple(_field_completions(parent.slots if parent is not None else (), types.CompletionItemKind.Property))
        )
    if tag_name == "c-fill":
        slot_name = _static_attr_value(tag_text, "name")
        parent = _parent_component(source, cursor, catalog) if catalog is not None else None
        data_context = _slot_data_source_context(tag_text)
        if slot_name is not None and parent is not None and data_context is not None:
            available = project.component_slot_data_fields(parent, slot_name)
            if available is None:
                return CompletionResult(())
            return CompletionResult(
                tuple(
                    types.CompletionItem(
                        label=name,
                        kind=types.CompletionItemKind.Variable,
                        detail=f"data exposed by the {slot_name!r} slot",
                    )
                    for name in available
                    if name not in data_context
                )
            )
    attribute_context, attribute_position = _attribute_completion_context(
        document,
        region,
        source,
        tag_start,
        cursor,
    )
    if not attribute_position:
        return CompletionResult(())
    if attribute_context is None:
        return CompletionResult((), is_incomplete=True)
    authored_attrs = set(attribute_context.authored_attrs)
    items = _directive_attribute_completions(
        tag_name,
        component is not None,
        authored_attrs,
        edit_range=attribute_context.edit_range,
        preserve_value=attribute_context.preserve_value,
    )
    if component is None:
        return CompletionResult(tuple(items), is_incomplete=True)
    existing = {name.removeprefix("c-") for name in authored_attrs}
    for schema_field in component.kwargs:
        if schema_field.name in existing:
            continue
        new_text = schema_field.name if attribute_context.preserve_value else f'{schema_field.name}="$1"'
        items.append(
            types.CompletionItem(
                label=schema_field.name,
                kind=types.CompletionItemKind.Field,
                detail=_field_detail(schema_field),
                documentation=_markdown(schema_field.description),
                insert_text=new_text,
                insert_text_format=types.InsertTextFormat.Snippet,
                filter_text=schema_field.name,
                text_edit=types.InsertReplaceEdit(
                    new_text=new_text,
                    insert=attribute_context.edit_range,
                    replace=attribute_context.edit_range,
                ),
            )
        )
    return CompletionResult(tuple(items), is_incomplete=True)


def hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
) -> types.Hover | None:
    """Return lexical or catalog documentation for the token under cursor."""
    catalog = project.catalog
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    cursor = parser_char_index(region.source_map.template_source, parser_index)
    source = region.source_map.template_source
    parsed = document.parsed.get(region.key)
    if parsed is not None:
        reference = _lexical_reference_at(parsed.template, parser_index)
        if reference is not None:
            return types.Hover(
                types.MarkupContent(
                    types.MarkupKind.Markdown,
                    _lexical_binding_markdown(reference.binding),
                ),
                range=_range(region.source_map.map_range(reference.start_index, reference.end_index)),
            )
        if catalog is not None:
            field_reference = _template_data_reference_at(
                parsed.template,
                parser_index,
                _template_data_fields(document, region, catalog),
            )
            if field_reference is not None:
                template_field, use = field_reference
                return types.Hover(
                    types.MarkupContent(
                        types.MarkupKind.Markdown,
                        _template_data_field_markdown(template_field),
                    ),
                    range=_range(region.source_map.map_range(use.start_index, use.end_index)),
                )
    token = _token_at(source, cursor)
    if token is None:
        return None
    token_text, start, end = token
    if catalog is None:
        return None
    component = catalog.get_tag(token_text) if _tag_name_is_token(source, start, end) else None
    if component is not None:
        content = _component_markdown(component, project)
    else:
        open_tag = _open_start_tag(source[:cursor])
        if open_tag is not None and open_tag[0] == "c-fill":
            parent = _parent_component(source, cursor, catalog)
            if parent is None:
                return None
            slot_name = _static_attr_value(open_tag[1], "name")
            if slot_name is None and _inside_static_name_value(open_tag[1]):
                slot_name = token_text
            slot = _find_field(parent.slots, slot_name or "")
            if slot is None:
                return None
            data_fields = project.component_slot_data_fields(parent, slot.name)
            if token_text == slot.name:
                content = _slot_markdown(slot, data_fields)
            elif data_fields is not None and token_text in data_fields:
                content = _slot_data_field_markdown(token_text, slot.name, parent)
            else:
                return None
        else:
            field = _catalog_field_at(document, source, cursor, catalog)
            if field is None:
                return None
            content = _field_markdown(field)
    return types.Hover(
        types.MarkupContent(types.MarkupKind.Markdown, content),
        range=_range(region.source_map.map_range(_char_to_byte(source, start), _char_to_byte(source, end))),
    )


def definition(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> types.Location | None:
    """Navigate to an exact catalog or lexical declaration when provable."""
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    source = region.source_map.template_source
    cursor = parser_char_index(source, parser_index)
    token = _token_at(source, cursor)
    if token is not None and project.catalog is not None:
        component = project.catalog.get_tag(token[0])
        if (
            component is not None
            and _tag_name_is_token(source, token[1], token[2])
            and component.python_file is not None
        ):
            return types.Location(
                component.python_file.resolve().as_uri(),
                _component_definition_range(component),
            )

    parsed = document.parsed.get(region.key)
    if parsed is not None:
        reference = _lexical_definition(parsed.template, parser_index, ())
        if reference is not None:
            return types.Location(
                document.uri,
                _range(
                    region.source_map.map_range(
                        reference.binding.start_index,
                        reference.binding.end_index,
                    )
                ),
            )
        if project.catalog is not None:
            field_reference = _template_data_reference_at(
                parsed.template,
                parser_index,
                _template_data_fields(document, region, project.catalog),
            )
            if field_reference is not None:
                template_field, _use = field_reference
                template_field_source: str | None = None
                if template_field.source_file is not None and open_documents is not None:
                    template_field_source = _open_document_source(template_field.source_file, open_documents)
                return _field_definition_location(template_field, source=template_field_source)

    if token is None or project.catalog is None:
        return None
    field = _catalog_field_at(document, source, cursor, project.catalog)
    if field is None:
        return None
    synchronized_source: str | None = None
    if field.source_file is not None and open_documents is not None:
        synchronized_source = _open_document_source(field.source_file, open_documents)
    return _field_definition_location(field, source=synchronized_source)


def document_symbols(document: DocumentState) -> list[types.DocumentSymbol]:
    """Return a hierarchy of parsed component and structural tags."""
    symbols: list[types.DocumentSymbol] = []
    for parsed in document.parsed.values():
        symbols.extend(_template_symbols(parsed.template, parsed.region))
    return symbols


def _parse_region(
    region: TemplateRegion,
    project: ProjectState,
) -> tuple[ParsedRegion | None, list[types.Diagnostic]]:
    source = region.source_map.template_source
    try:
        template = project.analysis.parse_template(source) if project.analysis is not None else parse_template(source)
    except (SyntaxError, ValueError) as exc:
        diagnostic = parse_diagnostic(exc)
        if diagnostic is not None and diagnostic.start_index is not None and diagnostic.end_index is not None:
            mapped = region.source_map.map_range(diagnostic.start_index, diagnostic.end_index)
            code = diagnostic.code
        else:
            mapped = region.source_map.map_range(0, 0)
            code = "citry.parse.configuration"
        return None, [
            types.Diagnostic(
                _range(mapped),
                str(exc),
                severity=types.DiagnosticSeverity.Error,
                code=code,
                source="citry",
            )
        ]

    parsed = ParsedRegion(region, template)
    if project.analysis is None:
        return parsed, []
    return parsed, _unknown_component_diagnostics(template, region, project.analysis.component_names)


def _unknown_component_diagnostics(
    template: Any,
    region: TemplateRegion,
    known_names: frozenset[str],
    *,
    base_index: int = 0,
) -> list[types.Diagnostic]:
    findings: list[types.Diagnostic] = []
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        tag = node.start_tag.name
        normalized = f"c-{tag.content[2:].lower()}" if tag.content.startswith("c-") else None
        if normalized is not None and normalized not in RESERVED_TAG_NAMES:
            name = normalized.removeprefix("c-")
            if name not in known_names:
                findings.append(
                    types.Diagnostic(
                        _range(
                            region.source_map.map_range(
                                base_index + tag.start_index,
                                base_index + tag.end_index,
                            )
                        ),
                        f"Unknown registered component <{tag.content}>.",
                        severity=types.DiagnosticSeverity.Error,
                        code="citry.component.unknown",
                        source="citry",
                    )
                )
        body = getattr(node, "body", None)
        if body is not None:
            findings.extend(_unknown_component_diagnostics(body, region, known_names, base_index=base_index))
        for attr in node.start_tag.attrs:
            if attr.kind != HtmlAttrKind.Template or attr.inner_value is None:
                continue
            parsed_nested = _parse_nested_template(attr.inner_value.content)
            if parsed_nested is None:
                continue
            nested, nested_start = parsed_nested
            findings.extend(
                _unknown_component_diagnostics(
                    nested,
                    region,
                    known_names,
                    base_index=base_index + attr.inner_value.start_index + nested_start,
                )
            )
    return findings


def _lexical_definition(
    template: Any,
    index: int,
    environment: tuple[_LexicalBinding, ...],
    *,
    base_index: int = 0,
) -> _LexicalReference | None:
    for element in template.elements:
        value: Any = element._0
        if isinstance(element, TemplateElement.Expr):
            target = _definition_for_uses(value.used_variables, index, environment, base_index=base_index)
            if target is not None:
                return target
            continue
        if not isinstance(element, TemplateElement.Node):
            continue
        node = value
        introduced = _node_bindings(node, base_index=base_index)
        for attr in node.start_tag.attrs:
            attr_environment = _attribute_environment(node, attr, environment, introduced)
            if attr.kind == HtmlAttrKind.Template and attr.inner_value is not None:
                parsed_nested = _parse_nested_template(attr.inner_value.content)
                if parsed_nested is not None:
                    nested, nested_start = parsed_nested
                    target = _lexical_definition(
                        nested,
                        index,
                        attr_environment,
                        base_index=base_index + attr.inner_value.start_index + nested_start,
                    )
                    if target is not None:
                        return target
                    continue
            target = _definition_for_uses(
                attr.used_variables,
                index,
                attr_environment,
                base_index=base_index,
            )
            if target is not None:
                return target
        body = getattr(node, "body", None)
        if body is not None:
            target = _lexical_definition(
                body,
                index,
                (*environment, *introduced),
                base_index=base_index,
            )
            if target is not None:
                return target
    return None


def _definition_for_uses(
    uses: list[Any],
    index: int,
    environment: tuple[_LexicalBinding, ...],
    *,
    base_index: int,
) -> _LexicalReference | None:
    for use in uses:
        if base_index + use.start_index <= index < base_index + use.end_index:
            for introduced in reversed(environment):
                if _identifier_key(introduced.name) == _identifier_key(use.content):
                    return _LexicalReference(
                        introduced,
                        base_index + use.start_index,
                        base_index + use.end_index,
                    )
    return None


def _lexical_reference_at(template: Any, index: int) -> _LexicalReference | None:
    declared = _introduced_binding_at(template, index, base_index=0)
    if declared is not None:
        return _LexicalReference(declared, declared.start_index, declared.end_index)
    return _lexical_definition(template, index, ())


def _introduced_binding_at(template: Any, index: int, *, base_index: int) -> _LexicalBinding | None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        introduced = _node_bindings(node, base_index=base_index)
        for binding in introduced:
            if binding.start_index <= index < binding.end_index:
                return binding
        for attr in node.start_tag.attrs:
            if attr.kind != HtmlAttrKind.Template or attr.inner_value is None:
                continue
            parsed_nested = _parse_nested_template(attr.inner_value.content)
            if parsed_nested is None:
                continue
            nested, nested_start = parsed_nested
            target = _introduced_binding_at(
                nested,
                index,
                base_index=base_index + attr.inner_value.start_index + nested_start,
            )
            if target is not None:
                return target
        body = getattr(node, "body", None)
        if body is not None:
            target = _introduced_binding_at(body, index, base_index=base_index)
            if target is not None:
                return target
    return None


def _lexical_bindings_at(
    template: Any,
    index: int,
    environment: tuple[_LexicalBinding, ...],
    *,
    base_index: int = 0,
) -> tuple[_LexicalBinding, ...] | None:
    """Return the active environment only when ``index`` is in Python source."""
    for element in template.elements:
        value: Any = element._0
        if isinstance(element, TemplateElement.Expr):
            expression_start = base_index + value.token.start_index + len("{{")
            expression_end = base_index + value.token.end_index - len("}}")
            if expression_start <= index <= expression_end:
                return environment
            continue
        if not isinstance(element, TemplateElement.Node):
            continue
        node = value
        introduced = _node_bindings(node, base_index=base_index)
        for attr in node.start_tag.attrs:
            inner = attr.inner_value
            if inner is None or not (base_index + inner.start_index <= index <= base_index + inner.end_index):
                continue
            attr_environment = _attribute_environment(node, attr, environment, introduced)
            # PyO3 exposes HtmlAttrKind as unhashable, so a set membership test
            # is not available here.
            if attr.kind == HtmlAttrKind.Expression or attr.kind == HtmlAttrKind.Meta:  # noqa: PLR1714
                return attr_environment
            if attr.kind == HtmlAttrKind.Template:
                parsed_nested = _parse_nested_template(inner.content)
                if parsed_nested is not None:
                    nested, nested_start = parsed_nested
                    return _lexical_bindings_at(
                        nested,
                        index,
                        attr_environment,
                        base_index=base_index + inner.start_index + nested_start,
                    )
            return None
        body = getattr(node, "body", None)
        if body is not None and _node_body_contains(node, index, base_index=base_index):
            resolved = _lexical_bindings_at(
                body,
                index,
                (*environment, *introduced),
                base_index=base_index,
            )
            if resolved is not None:
                return resolved
    return None


def _node_bindings(node: Any, *, base_index: int) -> tuple[_LexicalBinding, ...]:
    tag_name = node.start_tag.name.content
    bindings: list[_LexicalBinding] = []
    for token in node.introduced_variables:
        kind = "loop" if tag_name != "c-fill" else "slot-data"
        source_name: str | None = None
        if tag_name == "c-fill":
            kind, source_name = _fill_binding_detail(node, token)
        bindings.append(
            _LexicalBinding(
                token.content,
                base_index + token.start_index,
                base_index + token.end_index,
                kind,
                source_name,
            )
        )
    return tuple(bindings)


def _fill_binding_detail(node: Any, token: Any) -> tuple[str, str | None]:
    for attr in node.start_tag.attrs:
        pattern = attr.fill_data_pattern
        if pattern is not None:
            if pattern.whole is not None and _same_token(pattern.whole, token):
                return "slot-data", None
            for field in pattern.fields:
                if _same_token(field.target, token):
                    return "slot-data", field.source.content
            if pattern.rest is not None and _same_token(pattern.rest, token):
                return "slot-data-rest", None
        if attr.key.content == "fallback" and attr.inner_value is not None and _same_token(attr.inner_value, token):
            return "fallback", None
    return "slot-data", None


def _same_token(left: Any, right: Any) -> bool:
    return left.start_index == right.start_index and left.end_index == right.end_index


_CONTROL_FLOW_ATTRIBUTES = frozenset({"c-if", "c-elif", "c-else", "c-for", "c-empty"})


def _attribute_environment(
    node: Any,
    attr: Any,
    environment: tuple[_LexicalBinding, ...],
    introduced: tuple[_LexicalBinding, ...],
) -> tuple[_LexicalBinding, ...]:
    tag_name = node.start_tag.name.content
    shorthand_for = tag_name not in {"c-for", "c-fill"} and any(
        candidate.key.content == "c-for" for candidate in node.start_tag.attrs
    )
    if shorthand_for and attr.key.content not in _CONTROL_FLOW_ATTRIBUTES:
        return (*environment, *introduced)
    return environment


def _node_body_contains(node: Any, index: int, *, base_index: int) -> bool:
    body = getattr(node, "body", None)
    if body is None:
        return False
    return base_index + node.start_tag.token.end_index <= index <= base_index + node.end_tag.token.start_index


def _parse_nested_template(source: str) -> tuple[Any, int] | None:
    """Reparse a nested value and retain its byte offset inside the attribute."""
    nested_source = source
    nested_start = 0
    trimmed = source.strip()
    if trimmed.startswith("<>") and trimmed.endswith("</>"):
        nested_source = trimmed[2:-3]
        leading = source[: len(source) - len(source.lstrip())]
        nested_start = len(leading.encode("utf-8")) + 2
    try:
        return parse_template(nested_source), nested_start
    except (SyntaxError, ValueError):
        return None


def _identifier_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _template_symbols(template: Any, region: TemplateRegion) -> list[types.DocumentSymbol]:
    symbols: list[types.DocumentSymbol] = []
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        tag = node.start_tag.name
        body = getattr(node, "body", None)
        full_token = node.start_tag.token if body is None else node.end_tag.token
        end_index = full_token.end_index
        symbol_range = _range(region.source_map.map_range(node.start_tag.token.start_index, end_index))
        selection = _range(region.source_map.map_range(tag.start_index, tag.end_index))
        symbols.append(
            types.DocumentSymbol(
                name=f"<{tag.content}>",
                kind=types.SymbolKind.Class if tag.content.startswith("c-") else types.SymbolKind.Object,
                range=symbol_range,
                selection_range=selection,
                children=_template_symbols(body, region) if body is not None else None,
            )
        )
    return symbols


_ATTR_RE = re.compile(r"(?:^|\s)([#$@:A-Za-z_][\w:.$@#-]*)\s*(?:=|\s|$)")
_TOKEN_RE = re.compile(r"[#$@:A-Za-z_][\w:.$@#-]*")
_UNICODE_IDENTIFIER_RE = re.compile(r"(?:[^\W\d]|_)\w*")
_RAW_TEXT_TAG_NAMES = frozenset({"script", "style", "textarea", "title", "c-raw"})


@dataclass(frozen=True, slots=True)
class _CompletionSpec:
    label: str
    detail: str
    insert_text: str
    repeatable: bool = False


_STRUCTURAL_TAG_DETAILS = {
    "c-if": "Conditional branch",
    "c-elif": "Else-if branch",
    "c-else": "Else branch",
    "c-for": "Loop over an iterable",
    "c-empty": "Empty branch for a loop",
    "c-raw": "Render its body as literal text",
    "c-fill": "Fill a component slot",
    "c-slot": "Declare a component slot outlet",
}

_STRUCTURAL_TAG_REQUIRED_ATTRIBUTES = {
    "c-if": "cond",
    "c-elif": "cond",
    "c-for": "each",
    "c-fill": "name",
}

_GENERAL_DIRECTIVES = (
    _CompletionSpec("c-if", "Citry conditional directive", 'c-if="${1:condition}"'),
    _CompletionSpec("c-elif", "Citry else-if directive", 'c-elif="${1:condition}"'),
    _CompletionSpec("c-else", "Citry else directive", "c-else"),
    _CompletionSpec("c-for", "Citry loop directive", 'c-for="${1:item} in ${2:items}"'),
    _CompletionSpec("c-empty", "Citry empty-loop directive", "c-empty"),
    _CompletionSpec("c-bind", "Spread a Python attribute mapping", 'c-bind="${1:attributes}"', repeatable=True),
    _CompletionSpec("#c-key", "Stable Citry morph key", '#c-key="${1:key}"'),
    _CompletionSpec("#c-ignore", "Exclude this subtree from Citry morphing", "#c-ignore"),
)

_CLIENT_PROP_DIRECTIVES = (
    _CompletionSpec("$c-props", "Supply client-side component props", '\\$c-props="${1:{}}"'),
    _CompletionSpec(
        "c-$c-props",
        "Compute the complete client props expression in Python",
        'c-\\$c-props="${1:expression}"',
    ),
)

_STRUCTURAL_ATTRIBUTES: dict[str, tuple[_CompletionSpec, ...]] = {
    "c-if": (_CompletionSpec("cond", "Conditional expression", 'cond="${1:condition}"'),),
    "c-elif": (_CompletionSpec("cond", "Conditional expression", 'cond="${1:condition}"'),),
    "c-else": (),
    "c-for": (_CompletionSpec("each", "Loop clause", 'each="${1:item} in ${2:items}"'),),
    "c-empty": (),
    "c-raw": (),
    "c-fill": (
        _CompletionSpec("name", "Static slot name", 'name="${1:default}"'),
        _CompletionSpec("c-name", "Dynamic slot name", 'c-name="${1:name}"'),
        _CompletionSpec("data", "Bind data exposed by this slot", 'data="${1:data}"'),
        _CompletionSpec("fallback", "Bind fallback-content state", 'fallback="${1:fallback}"'),
        _CompletionSpec("c-bind", "Spread fill attributes", 'c-bind="${1:attributes}"', repeatable=True),
    ),
    "c-slot": (
        _CompletionSpec("name", "Static slot name", 'name="${1:default}"'),
        _CompletionSpec("c-name", "Dynamic slot name", 'c-name="${1:name}"'),
        _CompletionSpec("required", "Require a fill for this slot", "required"),
        _CompletionSpec("c-required", "Compute whether this slot is required", 'c-required="${1:condition}"'),
        _CompletionSpec("c-bind", "Spread slot attributes and data", 'c-bind="${1:attributes}"', repeatable=True),
        *_GENERAL_DIRECTIVES[:5],
    ),
}

_DYNAMIC_TARGET_ATTRIBUTES = (
    _CompletionSpec("is", "Static dynamic target", 'is="${1:target}"'),
    _CompletionSpec("c-is", "Computed dynamic target", 'c-is="${1:target}"'),
    _CompletionSpec("c-bind", "Spread target attributes", 'c-bind="${1:attributes}"', repeatable=True),
)


def _structural_tag_completions(
    *,
    closing: bool,
    edit_range: types.Range,
    close_start_tag: bool,
    authored_attrs: set[str],
) -> list[types.CompletionItem]:
    """Offer parser-owned structural tags even without an application catalog."""
    items: list[types.CompletionItem] = []
    for name in sorted(RESERVED_TAG_NAMES):
        if closing:
            new_text = name
            insert_text_format = types.InsertTextFormat.PlainText
        else:
            attribute = _STRUCTURAL_TAG_REQUIRED_ATTRIBUTES.get(name)
            if (attribute == "name" and authored_attrs & {"name", "c-name", "c-bind"}) or attribute in authored_attrs:
                attribute = None
            new_text = f'{name} {attribute}="${{1}}"' if attribute is not None else name
            if close_start_tag:
                new_text += ">"
            insert_text_format = types.InsertTextFormat.Snippet
        items.append(
            types.CompletionItem(
                label=name,
                kind=types.CompletionItemKind.Keyword,
                detail=_STRUCTURAL_TAG_DETAILS[name],
                insert_text=new_text,
                insert_text_format=insert_text_format,
                filter_text=name,
                sort_text=f"0:{name}",
                text_edit=types.InsertReplaceEdit(
                    new_text=new_text,
                    insert=edit_range,
                    replace=edit_range,
                ),
            )
        )
    return items


def _directive_attribute_completions(
    tag_name: str,
    registered_component: bool,
    authored_attrs: set[str],
    *,
    edit_range: types.Range,
    preserve_value: bool,
) -> list[types.CompletionItem]:
    normalized_tag = tag_name.lower()
    if normalized_tag in _STRUCTURAL_ATTRIBUTES:
        specs = _STRUCTURAL_ATTRIBUTES[normalized_tag]
    elif normalized_tag == "c-component":
        specs = (*_DYNAMIC_TARGET_ATTRIBUTES, *_GENERAL_DIRECTIVES, *_CLIENT_PROP_DIRECTIVES)
    elif normalized_tag == "c-element":
        specs = (*_DYNAMIC_TARGET_ATTRIBUTES, *_GENERAL_DIRECTIVES)
    else:
        is_component = registered_component or (tag_name.startswith("c-") and normalized_tag not in RESERVED_TAG_NAMES)
        specs = (*_GENERAL_DIRECTIVES, *(_CLIENT_PROP_DIRECTIVES if is_component else ()))

    control_if_present = bool(authored_attrs & {"c-if", "c-elif", "c-else"})
    control_for_present = bool(authored_attrs & {"c-for", "c-empty"})
    empty_present = "c-empty" in authored_attrs
    exclusive_pairs = (
        frozenset({"is", "c-is"}),
        frozenset({"name", "c-name"}),
        frozenset({"required", "c-required"}),
    )
    seen_labels: set[str] = set()
    items: list[types.CompletionItem] = []
    for spec in specs:
        if spec.label in seen_labels:
            continue
        seen_labels.add(spec.label)
        if not spec.repeatable and spec.label in authored_attrs:
            continue
        if spec.label in {"c-if", "c-elif", "c-else"} and control_if_present:
            continue
        if spec.label in {"c-if", "c-elif", "c-else"} and empty_present:
            continue
        if spec.label in {"c-for", "c-empty"} and control_for_present:
            continue
        if spec.label == "c-empty" and control_if_present:
            continue
        if any(spec.label in pair and authored_attrs & pair for pair in exclusive_pairs):
            continue
        new_text = spec.label if preserve_value else spec.insert_text
        items.append(
            types.CompletionItem(
                label=spec.label,
                kind=types.CompletionItemKind.Keyword,
                detail=spec.detail,
                insert_text=new_text,
                insert_text_format=types.InsertTextFormat.Snippet,
                filter_text=spec.label,
                text_edit=types.InsertReplaceEdit(
                    new_text=new_text,
                    insert=edit_range,
                    replace=edit_range,
                ),
            )
        )
    return items


def _lexical_completions(
    bindings: tuple[_LexicalBinding, ...],
    *,
    insert_range: types.Range,
    replace_range: types.Range,
) -> list[types.CompletionItem]:
    seen: set[str] = set()
    items: list[types.CompletionItem] = []
    for binding in reversed(bindings):
        key = _identifier_key(binding.name)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            types.CompletionItem(
                label=binding.name,
                kind=types.CompletionItemKind.Variable,
                detail=_lexical_binding_detail(binding),
                filter_text=binding.name,
                text_edit=types.InsertReplaceEdit(
                    new_text=binding.name,
                    insert=insert_range,
                    replace=replace_range,
                ),
            )
        )
    items.reverse()
    return items


def _expression_completions(
    bindings: tuple[_LexicalBinding, ...],
    template_fields: tuple[FieldRecord, ...],
    *,
    insert_range: types.Range,
    replace_range: types.Range,
) -> list[types.CompletionItem]:
    """Combine lexical names with conservative TemplateData root fields."""
    items = _lexical_completions(
        bindings,
        insert_range=insert_range,
        replace_range=replace_range,
    )
    seen = {_identifier_key(item.label) for item in items}
    for schema_field in template_fields:
        key = _identifier_key(schema_field.name)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            types.CompletionItem(
                label=schema_field.name,
                kind=types.CompletionItemKind.Variable,
                detail=f"TemplateData · {_field_detail(schema_field)}",
                documentation=_markdown(schema_field.description),
                filter_text=schema_field.name,
                text_edit=types.InsertReplaceEdit(
                    new_text=schema_field.name,
                    insert=insert_range,
                    replace=replace_range,
                ),
            )
        )
    return items


def _lexical_binding_detail(binding: _LexicalBinding) -> str:
    if binding.kind == "loop":
        return "loop variable introduced by c-for"
    if binding.kind == "fallback":
        return "fallback variable introduced by c-fill"
    if binding.kind == "slot-data-rest":
        return "remaining slot data introduced by c-fill"
    if binding.source_name is not None and binding.source_name != binding.name:
        return f"slot-data variable introduced from {binding.source_name!r} by c-fill"
    return "slot-data variable introduced by c-fill"


def _lexical_binding_markdown(binding: _LexicalBinding) -> str:
    return f"### `{binding.name}`\n\n{_lexical_binding_detail(binding).capitalize()}."


def _inside_unfinished_python_expression(source: str, cursor: int) -> bool:
    before = source[:cursor]
    open_tag = _open_start_tag(before)
    if open_tag is not None:
        _tag_name, tag_text = open_tag
        current_value = _unfinished_attribute_value(tag_text)
        if current_value is None:
            return False
        attr_name, value, _value_start = current_value
        if value.lstrip().startswith("<"):
            return _has_unfinished_template_expression(value)
        if attr_name in {"#c-key", "cond", "each"}:
            return True
        return attr_name.startswith("c-")
    return _has_unfinished_template_expression(before)


def _unfinished_attribute_value(tag_text: str) -> tuple[str, str, int] | None:
    """Return the value whose opening quote is still active at the cursor."""
    quote: str | None = None
    quote_start: int | None = None
    escaped = False
    index = 0
    while index < len(tag_text):
        if quote is None and tag_text.startswith("{#", index):
            comment_end = tag_text.find("#}", index + 2)
            if comment_end < 0:
                return None
            index = comment_end + 2
            continue
        char = tag_text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif quote is None and char in {'"', "'"}:
            quote = char
            quote_start = index
        elif char == quote:
            quote = None
            quote_start = None
        index += 1
    if quote_start is None:
        return None
    assignment = re.search(
        r"([#$@:A-Za-z_][\w:.$@#-]*)\s*=\s*$",
        tag_text[:quote_start],
    )
    if assignment is None:
        return None
    value_start = quote_start + 1
    return assignment.group(1), tag_text[value_start:], value_start


def _expression_completion_ranges(
    region: TemplateRegion,
    source: str,
    cursor: int,
) -> tuple[types.Range, types.Range]:
    """Map the current Python identifier to insertion and replacement ranges."""
    start = cursor
    while start > 0 and _python_identifier_continue(source[start - 1]):
        start -= 1
    end = cursor
    while end < len(source) and _python_identifier_continue(source[end]):
        end += 1
    insert_range = _range(
        region.source_map.map_range(
            _char_to_byte(source, start),
            _char_to_byte(source, cursor),
        )
    )
    replace_range = _range(
        region.source_map.map_range(
            _char_to_byte(source, start),
            _char_to_byte(source, end),
        )
    )
    return insert_range, replace_range


def _tag_completion_range(
    document: DocumentState,
    region: TemplateRegion,
    source: str,
    start: int,
    cursor: int,
) -> types.Range | None:
    """Map the complete Citry tag-name token around the cursor."""
    end = cursor
    while end < len(source) and _tag_name_continue(source[end]):
        end += 1
    mapped = _range(region.source_map.map_range(_char_to_byte(source, start), _char_to_byte(source, end)))
    host_start = document_offset_at(document.source, _citry_position(mapped.start))
    host_end = document_offset_at(document.source, _citry_position(mapped.end))
    if document.source[host_start:host_end] != source[start:end]:
        return None
    return mapped


def _tag_completion_tail(source: str, cursor: int) -> tuple[set[str], bool]:
    """Read authored attributes and whether a new start tag needs its closing delimiter."""
    end = cursor
    while end < len(source) and _tag_name_continue(source[end]):
        end += 1
    authored_attrs: set[str] = set()
    authored_tail = False
    index = end
    while index < len(source):
        if source[index].isspace():
            index += 1
            continue
        if source.startswith("{#", index):
            comment_end = source.find("#}", index + 2)
            if comment_end < 0:
                return authored_attrs, not authored_tail
            index = comment_end + 2
            continue
        if source.startswith("{{", index):
            return authored_attrs, not authored_tail
        if source[index] in {">", "/"}:
            return authored_attrs, False
        if source[index] in {"<", '"', "'"}:
            return authored_attrs, not authored_tail
        attr_match = _TOKEN_RE.match(source, index)
        if attr_match is None:
            authored_tail = True
            index += 1
            continue
        authored_tail = True
        authored_attrs.add(attr_match.group())
        index = attr_match.end()
        while index < len(source) and source[index].isspace():
            index += 1
        if index >= len(source) or source[index] != "=":
            continue
        index += 1
        while index < len(source) and source[index].isspace():
            index += 1
        if index < len(source) and source[index] in {'"', "'"}:
            value_end = _matching_quote(source, index + 1, source[index])
            if value_end is None:
                return authored_attrs, False
            index = value_end + 1
            continue
        while index < len(source) and not source[index].isspace() and source[index] not in {">", "/"}:
            index += 1
    return authored_attrs, not authored_tail


def _tag_name_continue(char: str) -> bool:
    """Recognize characters Citry permits in registered component names."""
    return char.isascii() and (char.isalnum() or char in {"-", "_", "."})


def _root_completion_context(source: str, cursor: int) -> bool:
    """Reject root suggestions while the cursor is completing a member."""
    start = cursor
    while start > 0 and _python_identifier_continue(source[start - 1]):
        start -= 1
    return not source[:start].rstrip().endswith(".")


def _python_identifier_continue(char: str) -> bool:
    """Recognize Unicode characters that can continue a Python identifier."""
    return char == "_" or char.isalnum() or f"a{char}".isidentifier()


def _has_unfinished_template_expression(source: str) -> bool:
    """Recognize an open interpolation in template, not static-attribute, text."""
    index = 0
    while index < len(source):
        next_marker = _next_template_marker(source, index)
        if next_marker is None:
            return False
        marker, start = next_marker
        if marker == "{#":
            end = source.find("#}", start + 2)
            if end < 0:
                return False
            index = end + 2
        elif marker == "{{":
            expression_end = _template_expression_end(source, start)
            if expression_end is None:
                return True
            index = expression_end
        elif source.startswith("<!--", start):
            end = source.find("-->", start + 4)
            if end < 0:
                return False
            index = end + 3
        else:
            tag_end = _tag_end(source, start)
            if tag_end is None:
                return False
            tag_text = source[start : tag_end + 1]
            tag_match = re.match(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)", tag_text)
            fragment = re.match(r"<\s*/?\s*>", tag_text)
            if tag_match is None and fragment is None:
                index = start + 1
                continue
            if _tag_has_unfinished_nested_expression(tag_text):
                return True
            if tag_match is None or tag_match.group(1) or tag_match.group(2) != "c-raw":
                index = tag_end + 1
                continue
            raw_end = _raw_end_start(source, tag_end + 1, "c-raw")
            if raw_end is None:
                return False
            close_end = _tag_end(source, raw_end)
            if close_end is None:
                return False
            index = close_end + 1
    return False


def _tag_has_unfinished_nested_expression(tag_text: str) -> bool:
    """Inspect only template-valued dynamic attributes inside a complete tag."""
    pattern = re.compile(r"(?:^|\s)c-[\w$-]+\s*=\s*(['\"])(.*?)\1", re.DOTALL)
    return any(
        value.lstrip().startswith("<") and _has_unfinished_template_expression(value)
        for value in (match.group(2) for match in pattern.finditer(tag_text))
    )


def _current_text_lexical_bindings(source: str, cursor: int) -> tuple[_LexicalBinding, ...]:
    """Recover active bindings from complete start tags before broken source."""
    stack: list[tuple[str, tuple[_LexicalBinding, ...]]] = []
    current = source[:cursor]
    tags = [
        *_complete_tags(current),
        *_unfinished_nested_template_tags(current),
        *_unfinished_start_tag_events(current),
    ]
    tags.sort(key=lambda item: item[0])
    seen: set[tuple[int, str]] = set()
    for start, tag_text, closing, tag_name, self_closing in tags:
        event_key = (start, tag_name)
        if event_key in seen:
            continue
        seen.add(event_key)
        normalized = tag_name.lower()
        if closing:
            for index in range(len(stack) - 1, -1, -1):
                if stack[index][0].lower() == normalized:
                    del stack[index:]
                    break
            continue
        bindings = _bindings_from_start_tag(tag_text, start, tag_name)
        if not self_closing and normalized not in HTML_VOID_ELEMENTS:
            stack.append((tag_name, bindings))
    return tuple(binding for _tag_name, bindings in stack for binding in bindings)


def _unfinished_nested_template_tags(source: str) -> list[tuple[int, str, bool, str, bool]]:
    """Find complete inner tags in a template-valued attribute open at EOF."""
    tags: list[tuple[int, str, bool, str, bool]] = []
    for match in re.finditer(r"(?:^|\s)c-[\w$-]+\s*=\s*(['\"])", source):
        quote = match.group(1)
        value_start = match.end()
        value_end = _matching_quote(source, value_start, quote)
        if value_end is not None:
            continue
        value = source[value_start:]
        leading_chars = len(value) - len(value.lstrip())
        nested = value[leading_chars:]
        if not (nested.startswith("<>") or re.match(r"<[A-Za-z]", nested)):
            continue
        nested_start = value_start + leading_chars
        tags.extend(
            (nested_start + start, tag_text, closing, tag_name, self_closing)
            for start, tag_text, closing, tag_name, self_closing in _complete_tags(nested)
        )
    return tags


def _unfinished_start_tag_events(source: str, *, base_index: int = 0) -> list[tuple[int, str, bool, str, bool]]:
    """Recover parseable prefixes from each unfinished nested start tag."""
    opened = _outer_open_start_tag(source)
    if opened is None:
        return []
    start, tag_name, tag_text = opened
    events: list[tuple[int, str, bool, str, bool]] = []
    synthetic = _parseable_start_tag_prefix(tag_text)
    if synthetic is not None:
        events.append((base_index + start, synthetic, False, tag_name, False))

    # A template-valued attribute creates a nested template grammar. Recurse
    # only after that authored marker, so Python comparison operators in other
    # quoted attributes cannot masquerade as tags.
    nested = _unfinished_nested_attribute(tag_text)
    if nested is not None:
        nested_start, nested_source = nested
        events.extend(
            _unfinished_start_tag_events(
                nested_source,
                base_index=base_index + start + nested_start,
            )
        )
    return events


def _parseable_start_tag_prefix(tag_text: str) -> str | None:
    """Close the fully authored attribute prefix of an unfinished tag."""
    quote: str | None = None
    escaped = False
    quote_start: int | None = None
    for index, char in enumerate(tag_text):
        if escaped:
            escaped = False
        elif char == "\\" and quote is not None:
            escaped = True
        elif char in {"'", '"'}:
            if quote is None:
                quote = char
                quote_start = index
            elif quote == char:
                quote = None
                quote_start = None
    prefix = tag_text if quote_start is None else tag_text[:quote_start]
    # Drop the incomplete attribute name and equals sign that precede an open
    # value, retaining earlier complete attributes at their authored offsets.
    if quote_start is not None:
        prefix = re.sub(r"(?:^|\s)[#$A-Za-z_][\w.$#-]*\s*=\s*$", "", prefix)
    if "c-for" not in prefix and not re.match(r"<\s*c-(?:for|fill)\b", prefix, re.IGNORECASE):
        return None
    return f"{prefix.rstrip()} />"


def _unfinished_nested_attribute(tag_text: str) -> tuple[int, str] | None:
    current_value = _unfinished_attribute_value(tag_text)
    if current_value is None:
        return None
    attr_name, value, value_start = current_value
    if not attr_name.startswith("c-"):
        return None
    leading = len(value) - len(value.lstrip())
    nested = value[leading:]
    if not (nested.startswith("<>") or re.match(r"<[A-Za-z]", nested)):
        return None
    return value_start + leading, nested


def _matching_quote(source: str, start: int, quote: str) -> int | None:
    for index in range(start, len(source)):
        if source[index] == quote:
            return index
    return None


def _tag_end(source: str, start: int) -> int | None:
    """Find a tag close while respecting quoted values and Citry comments."""
    quote: str | None = None
    index = start + 1
    while index < len(source):
        if quote is None and source.startswith("{#", index):
            comment_end = source.find("#}", index + 2)
            if comment_end < 0:
                return None
            index = comment_end + 2
            continue
        char = source[index]
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
        elif char == ">" and quote is None:
            return index
        index += 1
    return None


def _template_expression_end(source: str, start: int) -> int | None:
    """Find ``}}`` outside Python strings, comments, and nested delimiters."""
    index = start + 2
    quote: str | None = None
    triple = False
    escaped = False
    comment = False
    round_depth = square_depth = curly_depth = 0
    while index < len(source):
        if comment:
            # Citry expression comments end at the template delimiter even
            # without a physical newline, matching the compiler grammar.
            if source.startswith("}}", index):
                return index + 2
            if source[index] in {"\r", "\n"}:
                comment = False
            index += 1
            continue
        if quote is not None:
            marker = quote * (3 if triple else 1)
            if not escaped and source.startswith(marker, index):
                index += len(marker)
                quote = None
                triple = False
                continue
            if escaped:
                escaped = False
            elif source[index] == "\\":
                escaped = True
            index += 1
            continue
        if source.startswith("}}", index) and round_depth == square_depth == curly_depth == 0:
            return index + 2
        char = source[index]
        if char == "#":
            comment = True
        elif char in {"'", '"'}:
            quote = char
            triple = source.startswith(char * 3, index)
            if triple:
                index += 2
        elif char == "(":
            round_depth += 1
        elif char == ")" and round_depth:
            round_depth -= 1
        elif char == "[":
            square_depth += 1
        elif char == "]" and square_depth:
            square_depth -= 1
        elif char == "{":
            curly_depth += 1
        elif char == "}" and curly_depth:
            curly_depth -= 1
        index += 1
    return None


def _next_template_marker(source: str, index: int) -> tuple[str, int] | None:
    candidates = ((marker, source.find(marker, index)) for marker in ("{#", "{{", "<"))
    present = ((marker, start) for marker, start in candidates if start >= 0)
    return min(present, key=lambda item: item[1], default=None)


def _raw_end_start(source: str, start: int, tag_name: str) -> int | None:
    flags = re.IGNORECASE if tag_name != "c-raw" else 0
    match = re.search(rf"</\s*{re.escape(tag_name)}(?:\s|>)", source[start:], flags)
    return None if match is None else start + match.start()


def _complete_tags(source: str) -> list[tuple[int, str, bool, str, bool]]:
    tags: list[tuple[int, str, bool, str, bool]] = []
    index = 0
    while index < len(source):
        marker = _next_template_marker(source, index)
        if marker is None:
            break
        marker_kind, start = marker
        if marker_kind == "{#":
            comment_end = source.find("#}", start + 2)
            if comment_end < 0:
                break
            index = comment_end + 2
            continue
        if marker_kind == "{{":
            expression_end = _template_expression_end(source, start)
            if expression_end is None:
                break
            index = expression_end
            continue
        if source.startswith("<!--", start):
            end = source.find("-->", start + 4)
            if end < 0:
                break
            index = end + 3
            continue
        tag_end = _tag_end(source, start)
        if tag_end is None:
            break
        tag_text = source[start : tag_end + 1]
        match = re.match(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)", tag_text)
        if match is not None:
            closing = bool(match.group(1))
            tag_name = match.group(2)
            tags.append((start, tag_text, closing, tag_name, tag_text[:-1].rstrip().endswith("/")))
            if not closing and tag_name.lower() in _RAW_TEXT_TAG_NAMES:
                raw_end = _raw_end_start(source, tag_end + 1, tag_name.lower())
                if raw_end is None:
                    break
                index = raw_end
                continue
        index = tag_end + 1
    return tags


def _bindings_from_start_tag(tag_text: str, source_start: int, tag_name: str) -> tuple[_LexicalBinding, ...]:
    if "c-for" not in tag_text and tag_name.lower() != "c-for" and tag_name.lower() != "c-fill":
        return ()
    body = tag_text[:-1].rstrip()
    if body.endswith("/"):
        body = body[:-1].rstrip()
    synthetic = f"{body} />"
    prefix = ""
    suffix = ""
    if tag_name.lower() == "c-fill":
        prefix = '<c-component is="placeholder">'
        suffix = "</c-component>"
    try:
        parsed = parse_template(f"{prefix}{synthetic}{suffix}")
    except (SyntaxError, ValueError):
        return ()
    node = _first_node_named(parsed, tag_name)
    if node is None:
        return ()
    return _node_bindings(node, base_index=source_start - len(prefix))


def _first_node_named(template: Any, tag_name: str) -> Any | None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        if node.start_tag.name.content.lower() == tag_name.lower():
            return node
        body = getattr(node, "body", None)
        if body is not None:
            nested = _first_node_named(body, tag_name)
            if nested is not None:
                return nested
    return None


def _open_start_tag(before: str) -> tuple[str, str] | None:
    chain = _unfinished_start_tag_chain(before)
    if not chain:
        return None
    _start, tag_name, tag_text = chain[-1]
    return tag_name, tag_text


def _open_end_tag(before: str) -> tuple[str, str] | None:
    """Return an unfinished closing tag in the current nested template."""
    unfinished = _outer_unfinished_tag(before)
    if unfinished is None:
        return None
    _start, closing, tag_name, tag_text = unfinished
    if closing:
        return tag_name, tag_text
    nested = _unfinished_nested_attribute(tag_text)
    if nested is None:
        return None
    _nested_start, nested_source = nested
    return _open_end_tag(nested_source)


def _unfinished_start_tag_chain(source: str, *, base_index: int = 0) -> list[tuple[int, str, str]]:
    opened = _outer_open_start_tag(source)
    if opened is None:
        return []
    start, tag_name, tag_text = opened
    chain = [(base_index + start, tag_name, tag_text)]
    nested = _unfinished_nested_attribute(tag_text)
    if nested is not None:
        nested_start, nested_source = nested
        chain.extend(
            _unfinished_start_tag_chain(
                nested_source,
                base_index=base_index + start + nested_start,
            )
        )
    return chain


def _outer_open_start_tag(source: str) -> tuple[int, str, str] | None:
    """Find the unfinished outer tag without trusting ``<``/``>`` in values."""
    unfinished = _outer_unfinished_tag(source)
    if unfinished is None:
        return None
    start, closing, tag_name, tag_text = unfinished
    return None if closing else (start, tag_name, tag_text)


def _outer_unfinished_tag(source: str) -> tuple[int, bool, str, str] | None:
    """Find an unfinished outer start or end tag in real markup context."""
    index = 0
    while index < len(source):
        marker = _next_template_marker(source, index)
        if marker is None:
            return None
        marker_kind, start = marker
        if marker_kind == "{#":
            comment_end = source.find("#}", start + 2)
            if comment_end < 0:
                return None
            index = comment_end + 2
            continue
        if marker_kind == "{{":
            expression_end = _template_expression_end(source, start)
            if expression_end is None:
                return None
            index = expression_end
            continue
        if source.startswith("<!--", start):
            comment_end = source.find("-->", start + 4)
            if comment_end < 0:
                return None
            index = comment_end + 3
            continue
        end = _tag_end(source, start)
        if end is None:
            tag_text = source[start:]
            match = re.match(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)", tag_text)
            if match is not None:
                return start, bool(match.group(1)), match.group(2), tag_text
            index = start + 1
            continue
        tag_text = source[start : end + 1]
        match = re.match(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)", tag_text)
        if match is not None and not match.group(1) and match.group(2).lower() in _RAW_TEXT_TAG_NAMES:
            raw_end = _raw_end_start(source, end + 1, match.group(2).lower())
            if raw_end is None:
                return None
            index = raw_end
            continue
        index = end + 1
    return None


def _attribute_completion_context(
    document: DocumentState,
    region: TemplateRegion,
    source: str,
    tag_start: int,
    cursor: int,
) -> tuple[_AttributeCompletionContext | None, bool]:
    """
    Scan one start tag and map the complete active attribute name.

    The boolean distinguishes a valid-but-unmappable attribute position from a
    cursor in a value or comment. The former stays incomplete so clients can
    safely ask again without receiving a partial source-map edit.
    """
    tag_match = re.match(r"<\s*[A-Za-z][\w:.-]*", source[tag_start:])
    if tag_match is None:
        return None, False
    attributes_start = tag_start + tag_match.end()
    if attributes_start >= len(source) or not source[attributes_start].isspace():
        return None, False
    tag_end = _tag_end(source, tag_start)
    limit = tag_end if tag_end is not None else len(source)
    if not attributes_start <= cursor <= limit:
        return None, False

    attributes: list[tuple[str, int, int, int | None]] = []
    blocked: list[tuple[int, int, bool]] = []
    index = attributes_start
    while index < limit:
        if source[index].isspace():
            index += 1
            continue
        if source.startswith("{#", index):
            comment_end = source.find("#}", index + 2, limit)
            if comment_end < 0:
                blocked.append((index, limit, True))
                break
            blocked.append((index, comment_end + 2, False))
            index = comment_end + 2
            continue
        if source[index] in {"/", ">", "<"}:
            break

        name_start = index
        while index < limit and _attribute_name_continues(source, index):
            index += 1
        if index == name_start:
            index += 1
            continue
        name_end = index
        assignment = None
        after_name = index
        while after_name < limit and source[after_name].isspace():
            after_name += 1
        if after_name < limit and source[after_name] == "=":
            assignment = after_name
            value_start = after_name
            after_name += 1
            while after_name < limit and source[after_name].isspace():
                after_name += 1
            if after_name >= limit:
                blocked.append((value_start, limit, True))
                index = limit
            elif source[after_name] in {'"', "'"}:
                quote = source[after_name]
                value_end = _matching_quote(source[:limit], after_name + 1, quote)
                if value_end is None:
                    blocked.append((value_start, limit, True))
                    index = limit
                else:
                    blocked.append((value_start, value_end + 1, False))
                    index = value_end + 1
            else:
                value_end = after_name
                while value_end < limit and not source[value_end].isspace() and source[value_end] not in {">", "<"}:
                    value_end += 1
                blocked.append((value_start, value_end, value_end == limit))
                index = value_end
        attributes.append((source[name_start:name_end], name_start, name_end, assignment))

    if any(start <= cursor < end or (include_end and cursor == end) for start, end, include_end in blocked):
        return None, False

    active: tuple[str, int, int, int | None] | None = None
    for attribute in attributes:
        _name, start, end, assignment = attribute
        if start <= cursor <= end or (assignment is not None and end < cursor < assignment):
            active = attribute
            break

    if active is None:
        if cursor == 0 or not source[cursor - 1].isspace():
            return None, False
        edit_start = edit_end = cursor
        preserve_value = False
    else:
        _name, edit_start, edit_end, assignment = active
        preserve_value = assignment is not None

    authored_attrs = frozenset(
        name
        for name, start, end, _assignment in attributes
        if active is None or (start, end) != (active[1], active[2])
    )
    mapped = _range(
        region.source_map.map_range(
            _char_to_byte(source, edit_start),
            _char_to_byte(source, edit_end),
        )
    )
    try:
        host_start = document_offset_at(document.source, _citry_position(mapped.start))
        host_end = document_offset_at(document.source, _citry_position(mapped.end))
    except ValueError:
        return None, True
    if document.source[host_start:host_end] != source[edit_start:edit_end]:
        return None, True
    return _AttributeCompletionContext(mapped, authored_attrs, preserve_value), True


def _attribute_name_continues(source: str, index: int) -> bool:
    """Mirror the parser's delimiter-based HTML attribute-name grammar."""
    return (
        not source[index].isspace()
        and source[index] not in {"=", "/", ">", "<"}
        and not source.startswith("{#", index)
    )


def _inside_static_name_value(tag_text: str) -> bool:
    return re.search(r"(?:^|\s)name\s*=\s*(['\"])[^'\"]*$", tag_text) is not None


def _static_attr_value(tag_text: str, name: str) -> str | None:
    match = re.search(rf"(?:^|\s){re.escape(name)}\s*=\s*(['\"])([^'\"]*)\1", tag_text)
    return match.group(2) if match is not None else None


def _slot_data_source_context(tag_text: str) -> frozenset[str] | None:
    match = re.search(r"(?:^|\s)data\s*=\s*(['\"])([^'\"]*)$", tag_text)
    if match is None:
        return None
    value = match.group(2)
    opening = value.rfind("{")
    if opening < 0 or "}" in value[opening:]:
        return None
    body = value[opening + 1 :]
    current = body.rsplit(",", 1)[-1].strip()
    if current.startswith("**") or re.search(r"\bas(?:\s+\w*)?$", current) is not None:
        return None
    existing: set[str] = set()
    for item in body.split(","):
        source = item.strip().split(maxsplit=1)[0] if item.strip() else ""
        if source.isidentifier():
            existing.add(source)
    return frozenset(existing)


def _parent_component(source: str, cursor: int, catalog: CatalogIndex) -> ComponentRecord | None:
    stack: list[str] = []
    current = source[:cursor]
    tags = [
        *_complete_tags(current),
        *_unfinished_nested_template_tags(current),
        *_unfinished_start_tag_events(current),
    ]
    tags.sort(key=lambda item: item[0])
    seen: set[tuple[int, str]] = set()
    for start, _tag_text, closing, name, self_closing in tags:
        event_key = (start, name)
        if event_key in seen:
            continue
        seen.add(event_key)
        if closing:
            for index in range(len(stack) - 1, -1, -1):
                if stack[index].lower() == name.lower():
                    del stack[index:]
                    break
        elif not self_closing and name.lower() not in HTML_VOID_ELEMENTS:
            stack.append(name)
    for name in reversed(stack):
        component = catalog.get_tag(name)
        if component is not None:
            return component
    return None


def _token_at(source: str, cursor: int) -> tuple[str, int, int] | None:
    for match in _TOKEN_RE.finditer(source):
        if match.start() <= cursor <= match.end():
            return match.group(), match.start(), match.end()
    for match in _UNICODE_IDENTIFIER_RE.finditer(source):
        if match.start() <= cursor <= match.end() and match.group().isidentifier():
            return match.group(), match.start(), match.end()
    return None


def _field_completions(fields: tuple[FieldRecord, ...], kind: types.CompletionItemKind) -> list[types.CompletionItem]:
    return [
        types.CompletionItem(
            label=field.name,
            kind=kind,
            detail=_field_detail(field),
            documentation=_markdown(field.description),
        )
        for field in fields
    ]


def _template_data_fields(
    document: DocumentState,
    region: TemplateRegion,
    catalog: CatalogIndex,
) -> tuple[FieldRecord, ...]:
    """Return only schema fields shared by every proven template consumer."""
    if document.language_id == "python":
        if not region.ast_proven or region.component_name is None:
            return ()
        owners = catalog.inline_asset_consumers(document.uri, "template", region.component_name)
    elif document.language_id in {"citry-html", "html"}:
        owners = catalog.asset_owners(document.uri, "template")
    else:
        return ()
    if not owners:
        return ()

    schemas = tuple(owner.schemas.template_data for owner in owners)
    if any(schema.kind != "fields" for schema in schemas):
        return ()
    common = list(schemas[0].fields)
    if len({_identifier_key(schema_field.name) for schema_field in common}) != len(common):
        return ()
    for schema in schemas[1:]:
        fields = {_identifier_key(schema_field.name): schema_field for schema_field in schema.fields}
        if len(fields) != len(schema.fields):
            return ()
        retained: list[FieldRecord] = []
        for schema_field in common:
            candidate = fields.get(_identifier_key(schema_field.name))
            if candidate is None or not _same_field_contract(schema_field, candidate):
                continue
            retained_field = schema_field
            if _field_provenance(schema_field) != _field_provenance(candidate):
                retained_field = replace(
                    schema_field,
                    source_module=None,
                    source_qualname=None,
                    source_file=None,
                )
            retained.append(retained_field)
        common = retained
    return tuple(common)


def _same_field_contract(left: FieldRecord, right: FieldRecord) -> bool:
    """Compare schema semantics while leaving navigation provenance separate."""
    return (
        _identifier_key(left.name) == _identifier_key(right.name)
        and left.required == right.required
        and left.type_display == right.type_display
        and left.type_fidelity == right.type_fidelity
        and left.default_kind == right.default_kind
        and left.default_value_state == right.default_value_state
        and left.default_value == right.default_value
        and left.description == right.description
    )


def _field_provenance(field: FieldRecord) -> tuple[str | None, str | None, Path | None]:
    return field.source_module, field.source_qualname, field.source_file


def _template_data_reference_at(
    template: Any,
    index: int,
    fields: tuple[FieldRecord, ...],
) -> tuple[FieldRecord, Any] | None:
    """Join an exact parser-reported free root token to TemplateData."""
    by_name = {_identifier_key(schema_field.name): schema_field for schema_field in fields}
    for use in template.used_variables:
        if use.start_index <= index < use.end_index:
            schema_field = by_name.get(_identifier_key(use.content))
            if schema_field is not None:
                return schema_field, use
    return None


def _component_completions(
    catalog: CatalogIndex,
    prefix: str,
    *,
    edit_range: types.Range,
) -> list[types.CompletionItem]:
    items: list[types.CompletionItem] = []
    seen: set[str] = set()
    for component in catalog.components:
        variants: list[tuple[str, bool, int]] = []
        if component.class_name is not None:
            class_spelling = f"c-{component.class_name}"
            if catalog.get_tag(class_spelling) is component:
                variants.append((class_spelling, True, 1))
        variants.extend(
            (f"c-{name}", False, 0 if variant_index == 0 else variant_index + 1)
            for variant_index, name in enumerate(component.registered_names)
        )
        for label, is_class_name, variant_index in variants:
            if label in seen:
                continue
            seen.add(label)
            match = _component_completion_match(
                prefix,
                label,
                is_class_name=is_class_name,
                variant_index=variant_index,
            )
            if match is None:
                continue
            sort_text, filter_text = match
            items.append(
                types.CompletionItem(
                    label=label,
                    kind=types.CompletionItemKind.Class,
                    detail=_component_detail(component),
                    documentation=_markdown(component.description),
                    insert_text=label,
                    filter_text=filter_text,
                    sort_text=sort_text,
                    text_edit=types.InsertReplaceEdit(
                        new_text=label,
                        insert=edit_range,
                        replace=edit_range,
                    ),
                )
            )
    return items


def _component_completion_match(
    prefix: str,
    label: str,
    *,
    is_class_name: bool,
    variant_index: int,
) -> tuple[str, str] | None:
    """Match one component spelling while preserving the user's typed shape."""
    query = prefix.removeprefix("c-")
    suffix = label.removeprefix("c-")
    surfaces = [(suffix, False)]
    if is_class_name and len(suffix) > 1 and suffix[0] == "C" and suffix[1].isupper():
        surfaces.append((suffix[1:], True))

    matches: list[tuple[tuple[int, int, int, int], str]] = []
    for surface, elided in surfaces:
        result = _component_surface_match(query, surface, is_class_name=is_class_name)
        if result is None:
            continue
        tier, matched_surface, consumed_query = result
        comparison_query = query if consumed_query == len(query) else _compact_component_name(query)
        case_mismatches = sum(
            left != right
            for left, right in zip(comparison_query, matched_surface, strict=False)
            if left.casefold() == right.casefold()
        )
        score = (
            tier + (2 if elided else 0),
            variant_index,
            case_mismatches,
            len(matched_surface) - consumed_query,
        )
        filter_text = prefix + matched_surface[consumed_query:]
        matches.append((score, filter_text))
    if not matches:
        return None
    score, filter_text = min(matches)
    tier, variant, case_mismatches, remaining = score
    return (
        f"1:{tier:03}:{variant:03}:{case_mismatches:03}:{remaining:04}:{label.casefold()}:{label}",
        filter_text,
    )


def _component_surface_match(
    query: str,
    surface: str,
    *,
    is_class_name: bool,
) -> tuple[int, str, int] | None:
    """Return a match tier and the surface used for client-side filtering."""
    if query == surface:
        return 0, surface, len(query)
    if not query:
        return 20, surface, 0
    compact_query = _compact_component_name(query)
    compact_surface = _compact_component_name(surface)
    if (
        is_class_name
        and len(compact_query) >= 2
        and query == compact_query
        and len(compact_query) < len(compact_surface)
        and compact_surface.casefold().startswith(compact_query.casefold())
    ):
        return 10, compact_surface, len(compact_query)
    if surface.startswith(query):
        return 20, surface, len(query)
    if surface.casefold().startswith(query.casefold()):
        return 30, surface, len(query)
    if compact_surface.startswith(compact_query):
        return 40, compact_surface, len(compact_query)
    if compact_surface.casefold().startswith(compact_query.casefold()):
        return 50, compact_surface, len(compact_query)
    return None


def _compact_component_name(value: str) -> str:
    """Remove separators that distinguish equivalent component spellings."""
    return re.sub(r"[-_.]", "", value)


def _component_detail(component: ComponentRecord) -> str:
    return component.import_path or component.class_name or "Citry component"


def _field_detail(field: FieldRecord) -> str:
    required = "required" if field.required else "optional"
    return f"{field.type_display or 'value'} ({required})"


def _component_markdown(component: ComponentRecord, project: ProjectState) -> str:
    lines = [f"### `c-{component.name}`", "", component.description or _component_detail(component)]
    if component.kwargs:
        lines.extend(("", "**Inputs:** " + ", ".join(f"`{field.name}`" for field in component.kwargs)))
    if component.slots:
        lines.extend(("", "**Slots:**"))
        for slot in component.slots:
            data_fields = project.component_slot_data_fields(component, slot.name)
            data = ""
            if data_fields is not None:
                shape = ", ".join(data_fields) if data_fields else "no fields"
                data = f"; data: {{ {shape} }}"
            lines.append(f"- `{slot.name}` ({'required' if slot.required else 'optional'}{data})")
    return "\n".join(lines)


def _field_markdown(field: FieldRecord) -> str:
    return f"### `{field.name}`\n\n{_field_detail(field)}\n\n{field.description or ''}".rstrip()


def _template_data_field_markdown(field: FieldRecord) -> str:
    lines = [f"### `{field.name}`", "", f"TemplateData field · {_field_detail(field)}"]
    if field.description:
        lines.extend(("", field.description))
    return "\n".join(lines)


def _slot_markdown(field: FieldRecord, data_fields: tuple[str, ...] | None) -> str:
    lines = [f"### Slot `{field.name}`", "", _field_detail(field)]
    if field.description:
        lines.extend(("", field.description))
    if data_fields is not None:
        shape = ", ".join(f"`{name}`" for name in data_fields) if data_fields else "No fields."
        lines.extend(("", f"**Exposed data:** {shape}"))
    return "\n".join(lines)


def _slot_data_field_markdown(name: str, slot_name: str, component: ComponentRecord) -> str:
    return f"### `{name}`\n\nData exposed by slot `{slot_name}` on `c-{component.name}`."


def _find_field(fields: tuple[FieldRecord, ...], name: str) -> FieldRecord | None:
    resolved = name.removeprefix("c-")
    return next((field for field in fields if field.name == resolved), None)


def _catalog_field_at(
    document: DocumentState,
    source: str,
    cursor: int,
    catalog: CatalogIndex,
) -> FieldRecord | None:
    """Resolve only catalog fields with an unambiguous authored reference."""
    token = _token_at(source, cursor)
    if token is None:
        return None
    token_text, token_start, token_end = token
    start_tag = _start_tag_at(source, cursor)
    if start_tag is None:
        return None
    tag_name, tag_text, tag_start = start_tag

    # Component input declarations are referenced by the attribute key, never
    # by an equal-looking word inside its value.
    key_is_token = any(
        tag_start + match.start(1) == token_start and tag_start + match.end(1) == token_end
        for match in _ATTR_RE.finditer(tag_text)
    )
    component = catalog.get_tag(tag_name)
    if component is not None and key_is_token:
        field = _find_field(component.kwargs, token_text)
        if field is not None:
            return field

    # Slot names are static string values. A fill points at its lexical parent;
    # a slot declaration in a standalone asset points at its sole catalog owner.
    if tag_name not in {"c-fill", "c-slot"} or not _static_attr_value_is_token(
        tag_text,
        "name",
        token_start - tag_start,
        token_end - tag_start,
    ):
        return None
    if tag_name == "c-fill":
        owner = _parent_component(source, cursor, catalog)
    else:
        owners = catalog.asset_owners(document.uri, "template")
        owner = owners[0] if len(owners) == 1 else None
    return _find_field(owner.slots if owner is not None else (), token_text)


def _tag_name_is_token(source: str, token_start: int, token_end: int) -> bool:
    tag_start = source.rfind("<", 0, token_start + 1)
    if tag_start < 0:
        return False
    match = re.match(r"<\s*/?\s*([A-Za-z][\w:.-]*)", source[tag_start:])
    return bool(
        match is not None and tag_start + match.start(1) == token_start and tag_start + match.end(1) == token_end
    )


def _start_tag_at(source: str, cursor: int) -> tuple[str, str, int] | None:
    search_end = cursor + 1
    while search_end > 0:
        start = source.rfind("<", 0, search_end)
        if start < 0:
            return None
        search_end = start
        if source.startswith(("</", "<!", "<?"), start):
            continue
        end = _start_tag_end(source, start)
        if end is None or cursor > end:
            continue
        tag_text = source[start : end + 1]
        match = re.match(r"<\s*([A-Za-z][\w:.-]*)", tag_text)
        if match is not None:
            return match.group(1), tag_text, start
    return None


def _start_tag_end(source: str, start: int) -> int | None:
    quote: str | None = None
    for index in range(start + 1, len(source)):
        char = source[index]
        if char in {'"', "'"}:
            quote = None if quote == char else char if quote is None else quote
        elif char == ">" and quote is None:
            return index
    return None


def _static_attr_value_is_token(tag_text: str, name: str, start: int, end: int) -> bool:
    for match in re.finditer(rf"(?:^|\s){re.escape(name)}\s*=\s*(['\"])([^'\"]*)\1", tag_text):
        if match.start(2) == start and match.end(2) == end:
            return True
    return False


def _field_definition_location(field: FieldRecord, *, source: str | None = None) -> types.Location | None:
    if field.source_file is None or field.source_qualname is None or "<locals>" in field.source_qualname:
        return None
    try:
        source_file = field.source_file.resolve()
        if source is None:
            source = source_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(source_file))
        class_node = _class_node_for_qualname(tree, field.source_qualname)
        token = _annotated_field_token(source, class_node, field.name) if class_node is not None else None
    except (OSError, SyntaxError, UnicodeError, tokenize.TokenError):
        return None
    if token is None:
        return None
    line, start, end = token
    source_line = source.splitlines()[line]
    return types.Location(
        source_file.as_uri(),
        types.Range(
            types.Position(line, _utf16_units(source_line[:start])),
            types.Position(line, _utf16_units(source_line[:end])),
        ),
    )


def _open_document_source(source_file: Path, open_documents: Mapping[str, DocumentState]) -> str | None:
    """Find synchronized text even when the editor opened a symlinked path."""
    canonical = source_file.resolve()
    direct = open_documents.get(canonical.as_uri())
    if direct is not None:
        return direct.source
    for document in open_documents.values():
        parsed = urlparse(document.uri)
        if parsed.scheme != "file" or parsed.netloc:
            continue
        try:
            document_path = Path(unquote(parsed.path)).resolve()
        except (OSError, ValueError):
            continue
        if document_path == canonical:
            return document.source
    return None


def _annotated_field_token(
    source: str,
    class_node: ast.ClassDef,
    field_name: str,
) -> tuple[int, int, int] | None:
    declarations = [
        statement.target
        for statement in class_node.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == field_name
    ]
    if len(declarations) != 1:
        return None
    target = declarations[0]
    source_line = source.splitlines()[target.lineno - 1]
    target_column = _utf8_byte_column_to_char(source_line, target.col_offset)
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if (
            token.start == (target.lineno, target_column)
            and token.type == tokenize.NAME
            and token.string == field_name
        ):
            return token.start[0] - 1, token.start[1], token.end[1]
    return None


def _utf8_byte_column_to_char(source_line: str, byte_column: int) -> int:
    return len(source_line.encode("utf-8")[:byte_column].decode("utf-8"))


def _component_definition_range(component: ComponentRecord) -> types.Range:
    if component.python_file is None or component.qualname is None:
        return _zero_range()
    try:
        source = component.python_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(component.python_file))
        class_node = _class_node_for_qualname(tree, component.qualname)
        if class_node is None:
            return _zero_range()
        token = _class_name_token(source, class_node)
    except (OSError, SyntaxError, UnicodeError, tokenize.TokenError):
        return _zero_range()
    if token is None:
        return _zero_range()
    line, start, end = token
    source_line = source.splitlines()[line]
    return types.Range(
        types.Position(line, _utf16_units(source_line[:start])),
        types.Position(line, _utf16_units(source_line[:end])),
    )


def _class_node_for_qualname(tree: ast.Module, qualname: str) -> ast.ClassDef | None:
    parts = qualname.split(".")
    if not parts or "<locals>" in parts:
        return None
    body: list[ast.stmt] = tree.body
    target: ast.ClassDef | None = None
    for part in parts:
        matches = [node for node in body if isinstance(node, ast.ClassDef) and node.name == part]
        if len(matches) != 1:
            return None
        target = matches[0]
        body = target.body
    return target


def _class_name_token(source: str, node: ast.ClassDef) -> tuple[int, int, int] | None:
    saw_class = False
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.start[0] < node.lineno:
            continue
        if token.start[0] > node.lineno:
            break
        if token.type != tokenize.NAME:
            continue
        if not saw_class:
            saw_class = token.string == "class"
            continue
        if token.string != node.name:
            return None
        return token.start[0] - 1, token.start[1], token.end[1]
    return None


def _utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def _markdown(value: str | None) -> types.MarkupContent | None:
    return types.MarkupContent(types.MarkupKind.Markdown, value) if value else None


def _char_to_byte(source: str, index: int) -> int:
    return len(source[:index].encode("utf-8"))


def _citry_position(position: types.Position) -> LspPosition:
    return LspPosition(position.line, position.character)


def _range(value: LspRange) -> types.Range:
    return types.Range(
        types.Position(value.start.line, value.start.character),
        types.Position(value.end.line, value.end.character),
    )


def _zero_range() -> types.Range:
    return types.Range(types.Position(0, 0), types.Position(0, 0))


__all__ = [
    "CompletionResult",
    "DocumentState",
    "ParsedRegion",
    "completion_items",
    "completion_result",
    "definition",
    "document_symbols",
    "hover",
]
