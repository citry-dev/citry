"""Parser-backed diagnostics and narrow editor intelligence."""

from __future__ import annotations

import ast
import io
import re
import tokenize
import unicodedata
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Literal, cast

from lsprotocol import types

from citry import LspPosition, LspRange
from citry._diagnostic_catalog import (
    BROWSER_INCOMPATIBLE_COMPONENT_PROP,
    BROWSER_MISSING_COMPONENT_PROP,
    BROWSER_UNKNOWN_COMPONENT_PROP,
    BROWSER_UNKNOWN_SERVER_EVENT,
    JS_DATA_UNSUPPORTED_TYPE,
    PARSE_CONFIGURATION,
    TEMPLATE_UNKNOWN_COMPONENT,
)
from citry._diagnostics import diagnostic_documentation_url, render_diagnostic
from citry.analysis import (
    SERVER_EVENT_CALL_NAMES,
    AlpineLintConsumer,
    BrowserBinding,
    BrowserComponentPropsUse,
    BrowserExpression,
    BrowserObjectProperty,
    ComponentJsLintConsumer,
    JsonWireType,
    ShadowPythonDocument,
    TemplateLintConsumer,
    TemplatePythonControl,
    TemplatePythonQuery,
    TemplatePythonRoot,
    analyze_browser_component_source,
    analyze_css_data_source,
    analyze_js_data_source,
    analyze_template_data_source,
    browser_bindings,
    browser_client_prop_accepts,
    browser_completion_at,
    browser_component_prop_uses,
    browser_component_props,
    browser_component_scope_writes,
    browser_declarative_events,
    browser_expression_at,
    browser_expressions,
    browser_identifier_at,
    browser_identifiers,
    browser_literal_calls,
    browser_literal_wire_type,
    browser_member_at,
    build_inferred_template_shadow,
    build_schema_template_shadow,
    css_data_completion_at,
    css_data_reference_at,
    css_data_references,
    json_wire_type_from_annotation,
    json_wire_type_from_expression,
    lint_unknown_alpine_variables,
    lint_unknown_component_js_variables,
    lint_unknown_template_variables,
    merge_json_wire_types,
    python_application_lint_variable_range,
    python_class_asset_resolution_signature,
    python_class_defines_direct_method,
    python_class_resolution_signature,
    python_component_lint_variable_range,
    python_event_handler_range,
    template_python_queries,
    template_python_query_at,
)
from citry_core.template_parser import (
    CITRY_DIRECTIVE_NAMES,
    HTML_VOID_ELEMENTS,
    RESERVED_TAG_NAMES,
    STRUCTURAL_TAG_ATTRIBUTE_NAMES,
    HtmlAttrKind,
    TemplateElement,
    parse_diagnostic,
    parse_template,
)
from citry_lsp.regions import (
    CssRegion,
    JsRegion,
    TemplateRegion,
    css_region_at_position,
    discover_python_css_regions,
    discover_python_js_regions,
    discover_python_regions,
    document_offset_at,
    document_range_for_offsets,
    js_region_at_position,
    parser_char_index,
    region_at_position,
    standalone_css_region,
    standalone_js_region,
    standalone_region,
)
from citry_lsp.uri import file_uri_path

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from citry._linting import TemplateVariableInfo
    from citry._template_data_source import TemplateDataSourceShape
    from citry_lsp.catalog import CatalogIndex, ComponentRecord, FieldRecord, SchemaRecord
    from citry_lsp.project import ProjectState, SourceEventRecord, SourceLintRecord, SourceStateFieldRecord


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
class TemplateVariableHover:
    """One exact template variable plus the Citry facts shown beside its type."""

    name: str
    range: types.Range
    provenance: str
    description: str | None = None
    fallback_types: tuple[str, ...] = ()
    binding_kind: str | None = None
    is_declaration: bool = False


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


@dataclass(frozen=True, slots=True)
class _TemplateRoot:
    """One template root joined across every proven asset consumer."""

    name: str
    presence: Literal["always", "conditional"]
    origins: frozenset[str]
    fields: tuple[FieldRecord, ...] = ()
    type_field: FieldRecord | None = None
    fallback_types: tuple[str, ...] | None = None
    description: str | None = None
    shadow_type_display: str | None = None
    locations: tuple[types.Location, ...] = ()
    lint_definitions: tuple[SourceLintRecord, ...] = ()
    access: Literal["mapping", "attribute", "mixed", "analysis"] = "mapping"


@dataclass(frozen=True, slots=True)
class _TemplateContext:
    """One consumer's roots and optional current Python source owner."""

    roots: tuple[_TemplateRoot, ...]
    source_file: Path | None = None
    source: str | None = None
    source_kind: str | None = None
    source_module: str | None = None
    source_qualname: str | None = None
    kwargs_type: tuple[str, str] | None = None
    namespace_policy: Literal["closed", "allow-extra", "unknown"] = "unknown"


@dataclass(frozen=True, slots=True)
class _CssDataProducer:
    """One Python declaration or method that can emit a custom property."""

    origin: str
    type_display: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class _CssDataRoot:
    """One CSS-data name joined across every proven stylesheet consumer."""

    name: str
    presence: Literal["always", "conditional"]
    producers: tuple[_CssDataProducer, ...]
    fields: tuple[FieldRecord, ...] = ()
    locations: tuple[types.Location, ...] = ()


@dataclass(frozen=True, slots=True)
class _JsDataProducer:
    """One Python declaration or method that can seed a browser variable."""

    origin: str
    wire_type: JsonWireType
    description: str | None = None


@dataclass(frozen=True, slots=True)
class _JsDataRoot:
    """One JS-data name joined across every proven template consumer."""

    name: str
    presence: Literal["always", "conditional"]
    wire_type: JsonWireType
    producers: tuple[_JsDataProducer, ...]
    fields: tuple[FieldRecord, ...] = ()
    locations: tuple[types.Location, ...] = ()


@dataclass(frozen=True, slots=True)
class _ClientProp:
    """One current static child prop and its exact JavaScript declaration."""

    name: str
    javascript: str
    required: bool
    location: types.Location


@dataclass(frozen=True, slots=True)
class ExpressionShadow:
    """One analyzer document for one proven template consumer."""

    identity: str
    source_file: Path
    source: str
    document: ShadowPythonDocument
    query: TemplatePythonQuery
    cursor_offset: int


@dataclass(frozen=True, slots=True)
class ExpressionShadowGroup:
    """All consumer documents for one authored Python expression."""

    position: types.Position
    shadows: tuple[ExpressionShadow, ...]


@dataclass(frozen=True, slots=True)
class SemanticDependencies:
    """Python sources known to affect one document's template semantics."""

    source_uris: frozenset[str]
    complete: bool


@dataclass(frozen=True, slots=True)
class _ExpressionShadowConsumer:
    """One consumer's validated source facts reused across expression queries."""

    identity: str
    source_file: Path
    source: str
    source_kind: Literal["schema", "inferred"]
    source_module: str | None
    source_qualname: str
    kwargs_type: tuple[str, str] | None
    roots: tuple[TemplatePythonRoot, ...]


@dataclass(frozen=True, slots=True)
class BrowserProjection:
    """One virtual JavaScript document plus its exact authored source copy."""

    source: str
    position: types.Position
    source_range: types.Range
    virtual_range: types.Range
    owned_root_names: tuple[str, ...] = ()
    citry_owns_position: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return the private client payload without changing LSP protocol v1."""
        return {
            "source": self.source,
            "position": _position_dict(self.position),
            "sourceRange": _range_dict(self.source_range),
            "virtualRange": _range_dict(self.virtual_range),
            "ownedRootNames": list(self.owned_root_names),
            "citryOwnsPosition": self.citry_owns_position,
        }


@dataclass(frozen=True, slots=True)
class HtmlProjection:
    """One parser-proven HTML fragment plus its authored source range."""

    source: str
    position: types.Position
    source_range: types.Range
    virtual_range: types.Range

    def to_dict(self) -> dict[str, object]:
        """Return the private client payload without changing LSP protocol v1."""
        return {
            "source": self.source,
            "position": _position_dict(self.position),
            "sourceRange": _range_dict(self.source_range),
            "virtualRange": _range_dict(self.virtual_range),
        }


@dataclass(frozen=True, slots=True)
class _HtmlProjectionSlice:
    """A projection in parser byte coordinates before host-source mapping."""

    source: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class _SyntaxReference:
    """One parser-owned tag or attribute together with its authored span."""

    spec: _SyntaxSpec
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
    css_regions: tuple[CssRegion, ...] = ()
    js_regions: tuple[JsRegion, ...] = ()
    parsed: dict[str, ParsedRegion] = field(default_factory=dict)
    last_good: dict[str, ParsedRegion] = field(default_factory=dict)
    diagnostics: tuple[types.Diagnostic, ...] = ()
    _analysis_revision: int = field(default=0, init=False, repr=False, compare=False)
    _expression_shadow_project: object | None = field(default=None, init=False, repr=False, compare=False)
    _expression_shadow_documents: tuple[tuple[str, int, int, str], ...] | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )
    _expression_shadow_groups: tuple[ExpressionShadowGroup, ...] = field(
        default=(),
        init=False,
        repr=False,
        compare=False,
    )

    def update(self, source: str, version: int | None, project: ProjectState) -> None:
        """Replace source, analyze definite regions, and retain valid trees."""
        # Semantic inputs include exact template text, so no answer survives an edit.
        self._expression_shadow_project = None
        self._expression_shadow_documents = None
        self._expression_shadow_groups = ()
        self._analysis_revision += 1
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
        if self.language_id == "css" and project.catalog is not None and project.catalog.asset_owners(self.uri, "css"):
            self.css_regions = (standalone_css_region(source),)
        elif self.language_id == "python":
            self.css_regions = discover_python_css_regions(source)
        else:
            self.css_regions = ()
        if (
            self.language_id == "javascript"
            and project.catalog is not None
            and project.catalog.asset_owners(self.uri, "js")
        ):
            self.js_regions = (standalone_js_region(source),)
        elif self.language_id == "python":
            self.js_regions = discover_python_js_regions(source)
        else:
            self.js_regions = ()
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

    def css_region_at(self, position: types.Position) -> CssRegion | None:
        """Return the current authored CSS region containing a position."""
        return css_region_at_position(self.css_regions, _citry_position(position))

    def js_region_at(self, position: types.Position) -> JsRegion | None:
        """Return the current authored JavaScript region containing a position."""
        return js_region_at_position(self.js_regions, _citry_position(position))


def template_lint_diagnostics(
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> tuple[types.Diagnostic, ...]:
    """Apply portable root linting only where current component ownership is proven."""
    if project.catalog is None or project.analysis is None:
        return ()
    diagnostics: list[types.Diagnostic] = []
    for region in document.regions:
        parsed = document.parsed.get(region.key)
        if parsed is None:
            continue
        owners = _template_consumers(document, region, project, open_documents)
        if not owners:
            continue
        consumers: list[TemplateLintConsumer] = []
        for owner in owners:
            context = _component_template_context(owner, project, document, open_documents)
            lint = project.analysis.component_lint.get(owner.definition_id)
            if (
                context is None
                or lint is None
                or any(not _template_root_fields_are_current(root, open_documents) for root in context.roots)
            ):
                # One stale or unprovable consumer makes the physical
                # template's joined namespace unsafe to diagnose.
                consumers = []
                break
            known_names = {root.name for root in context.roots}
            current_schema_names = _current_template_schema_names(owner, project, open_documents)
            if current_schema_names is None:
                consumers = []
                break
            known_names.update(current_schema_names)
            known_names.update(variable.name for variable in lint.template_variables)
            consumers.append(
                TemplateLintConsumer(
                    known_names=frozenset(known_names),
                    namespace_policy=("allow-extra" if lint.allows_extra_variables else context.namespace_policy),
                    rule_unknown_template_variable=lint.rule_unknown_template_variable,
                )
            )
        if not consumers:
            continue
        for finding in lint_unknown_template_variables(parsed.template, consumers):
            mapped = region.source_map.map_range(finding.start_index, finding.end_index)
            diagnostics.append(
                types.Diagnostic(
                    range=_range(mapped),
                    message=finding.message,
                    severity=(
                        types.DiagnosticSeverity.Error
                        if finding.severity == "error"
                        else types.DiagnosticSeverity.Warning
                    ),
                    code=finding.code,
                    code_description=types.CodeDescription(diagnostic_documentation_url(finding.code)),
                    source="citry",
                )
            )
    return tuple(diagnostics)


def browser_diagnostics(
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> tuple[types.Diagnostic, ...]:
    """Report Citry-owned JsData and literal server-event problems."""
    diagnostics = list(_js_data_type_diagnostics(document, project, open_documents))
    if project.catalog is None or project.source_analysis is None:
        return tuple(diagnostics)
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    for region in document.regions:
        parsed = document.parsed.get(region.key)
        if parsed is None:
            continue
        consumers = _template_consumers(document, region, project, open_documents)
        if not consumers:
            continue
        expressions = browser_expressions(parsed.template, parse_nested=parser)
        alpine_consumers = _alpine_lint_consumers(
            consumers,
            document,
            project,
            open_documents,
        )
        if alpine_consumers is not None:
            for finding in lint_unknown_alpine_variables(expressions, alpine_consumers):
                diagnostics.append(
                    types.Diagnostic(
                        range=_range(region.source_map.map_range(finding.start_index, finding.end_index)),
                        message=finding.message,
                        severity=(
                            types.DiagnosticSeverity.Error
                            if finding.severity == "error"
                            else types.DiagnosticSeverity.Warning
                        ),
                        code=finding.code,
                        code_description=types.CodeDescription(diagnostic_documentation_url(finding.code)),
                        source="citry",
                    )
                )
        event_contract = _event_contract(consumers, document, project, open_documents)
        if event_contract is not None:
            for expression in expressions:
                for call in browser_literal_calls(expression, SERVER_EVENT_CALL_NAMES):
                    if call.value in event_contract:
                        continue
                    diagnostics.append(
                        _browser_event_diagnostic(
                            region,
                            call.value,
                            call.start_index,
                            call.end_index,
                        )
                    )
            for event in browser_declarative_events(
                parsed.template,
                frozenset(event_contract),
                parse_nested=parser,
            ):
                if event.name in event_contract:
                    continue
                diagnostics.append(
                    _browser_event_diagnostic(
                        region,
                        event.name,
                        event.start_index,
                        event.end_index,
                    )
                )
        roots = _template_js_data_roots(document, region, project, open_documents)
        for props_use in browser_component_prop_uses(parsed.template, parse_nested=parser):
            child = project.catalog.get_tag(props_use.tag_name)
            if child is None:
                continue
            contract = _component_client_props(child, project, document, open_documents)
            if contract is None:
                continue
            diagnostics.extend(
                _component_props_diagnostics(
                    region,
                    props_use,
                    contract,
                    roots,
                    expressions,
                )
            )
    for js_region in document.js_regions:
        js_consumers = _js_consumers(document, js_region, project, open_documents)
        js_lint_consumers = _component_js_lint_consumers(js_consumers, project)
        if js_lint_consumers is not None:
            for component_finding in lint_unknown_component_js_variables(
                js_region.source_map.template_source,
                js_lint_consumers,
            ):
                diagnostics.append(
                    types.Diagnostic(
                        range=_range(
                            js_region.source_map.map_range(
                                component_finding.start_index,
                                component_finding.end_index,
                            )
                        ),
                        message=component_finding.message,
                        severity=(
                            types.DiagnosticSeverity.Error
                            if component_finding.severity == "error"
                            else types.DiagnosticSeverity.Warning
                        ),
                        code=component_finding.code,
                        code_description=types.CodeDescription(diagnostic_documentation_url(component_finding.code)),
                        source="citry",
                    )
                )
        js_event_contract = _event_contract(js_consumers, document, project, open_documents)
        if not js_consumers or js_event_contract is None:
            continue
        js_expression = _component_js_expression(js_region)
        for call in browser_literal_calls(js_expression, SERVER_EVENT_CALL_NAMES):
            if call.value in js_event_contract:
                continue
            diagnostics.append(
                types.Diagnostic(
                    range=_range(js_region.source_map.map_range(call.start_index, call.end_index)),
                    message=render_diagnostic(BROWSER_UNKNOWN_SERVER_EVENT, name=call.value),
                    severity=types.DiagnosticSeverity.Error,
                    code=BROWSER_UNKNOWN_SERVER_EVENT,
                    code_description=types.CodeDescription(diagnostic_documentation_url(BROWSER_UNKNOWN_SERVER_EVENT)),
                    source="citry",
                )
            )
    return tuple(diagnostics)


def _component_js_lint_consumers(
    consumers: tuple[ComponentRecord, ...],
    project: ProjectState,
) -> tuple[ComponentJsLintConsumer, ...] | None:
    """Build each proven component-JavaScript global namespace."""
    if project.analysis is None or not consumers:
        return None
    resolved: list[ComponentJsLintConsumer] = []
    for component in consumers:
        lint = project.analysis.component_lint.get(component.definition_id)
        if lint is None:
            return None
        resolved.append(
            ComponentJsLintConsumer(
                known_names=frozenset(variable.name for variable in lint.component_js_globals),
                rule_unknown_component_js_variable=lint.rule_unknown_component_js_variable,
            )
        )
    return tuple(resolved)


def _component_js_global_types(
    consumers: tuple[ComponentRecord, ...],
    project: ProjectState,
) -> dict[str, JsonWireType] | None:
    """Join configured component-JavaScript globals across every asset owner."""
    if project.analysis is None or not consumers:
        return None
    resolved: list[dict[str, JsonWireType]] = []
    for component in consumers:
        lint = project.analysis.component_lint.get(component.definition_id)
        if lint is None:
            return None
        resolved.append(
            {
                variable.name: (
                    json_wire_type_from_annotation(variable.type_display)
                    if variable.type_display is not None
                    else JsonWireType("unknown")
                )
                for variable in lint.component_js_globals
            }
        )
    common = dict(resolved[0])
    for candidate in resolved[1:]:
        common = {
            name: merge_json_wire_types((wire_type, candidate[name]))
            for name, wire_type in common.items()
            if name in candidate
        }
    return common


def _alpine_lint_consumers(
    consumers: tuple[ComponentRecord, ...],
    current_document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[AlpineLintConsumer, ...] | None:
    """Build every source-proven browser namespace for one physical template."""
    if project.analysis is None:
        return None
    resolved: list[AlpineLintConsumer] = []
    for component in consumers:
        roots = _component_js_data_roots(component, project, current_document, open_documents)
        scope_roots = _component_scope_roots(component, project, current_document, open_documents)
        lint = project.analysis.component_lint.get(component.definition_id)
        if roots is None or scope_roots is None or lint is None:
            return None
        resolved.append(
            AlpineLintConsumer(
                known_names=frozenset(
                    (
                        *[root.name for root in roots],
                        *[root.name for root in scope_roots],
                        *[variable.name for variable in lint.alpine_variables],
                    )
                ),
                rule_unknown_alpine_variable=lint.rule_unknown_alpine_variable,
            )
        )
    return tuple(resolved)


def _browser_event_diagnostic(
    region: TemplateRegion | JsRegion,
    name: str,
    start_index: int,
    end_index: int,
) -> types.Diagnostic:
    return types.Diagnostic(
        range=_range(region.source_map.map_range(start_index, end_index)),
        message=render_diagnostic(BROWSER_UNKNOWN_SERVER_EVENT, name=name),
        severity=types.DiagnosticSeverity.Error,
        code=BROWSER_UNKNOWN_SERVER_EVENT,
        code_description=types.CodeDescription(diagnostic_documentation_url(BROWSER_UNKNOWN_SERVER_EVENT)),
        source="citry",
    )


def browser_projection(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> BrowserProjection | None:
    """Build JavaScript-provider input for Alpine or component JS source."""
    expression_context = _browser_expression_context(document, position, project)
    if expression_context is not None:
        region, expression, parser_index = expression_context
        roots = _template_js_data_roots(document, region, project, open_documents)
        consumers = _template_consumers(document, region, project, open_documents)
        events = _event_contract(consumers, document, project, open_documents)
        if not consumers or events is None:
            return None
        state_roots = _shared_state_roots(consumers, document, project, open_documents)
        if state_roots is None:
            return None
        binding_types = {
            binding.name: _browser_binding_wire_type(binding, roots) for binding in expression.binding_details
        }
        preamble = _browser_preamble(
            roots,
            expression.bindings,
            (),
            tuple(events),
            state_roots,
            binding_types=binding_types,
        )
        if expression.mode == "statement":
            prefix = f"{preamble}\n(function () {{\n"
            suffix = "\n})();\n"
        elif expression.mode == "loop":
            prefix = f"{preamble}\nfor ("
            suffix = ") {}\n"
        else:
            prefix = f"{preamble}\nvoid (\n"
            suffix = "\n);\n"
        source = f"{prefix}{expression.source}{suffix}"
        relative_byte = parser_index - expression.start_index
        try:
            relative_char = parser_char_index(expression.source, relative_byte)
        except ValueError:
            return None
        virtual_start = len(prefix)
        virtual_end = virtual_start + len(expression.source)
        source_range = _range(region.source_map.map_range(expression.start_index, expression.end_index))
        owned_names = tuple(root.name for root in roots)
        owns_position = _browser_projection_owns_position(
            expression,
            parser_index,
            roots,
            state_roots,
            component_js=False,
        )
        return BrowserProjection(
            source,
            _position(
                document_range_for_offsets(
                    source,
                    virtual_start + relative_char,
                    virtual_start + relative_char,
                ).start
            ),
            source_range,
            _range(document_range_for_offsets(source, virtual_start, virtual_end)),
            owned_names,
            owns_position,
        )

    js_region = document.js_region_at(position)
    if js_region is None:
        return None
    js_parser_index = js_region.source_map.parser_index_at(_citry_position(position))
    if js_parser_index is None:
        return None
    consumers = _js_consumers(document, js_region, project, open_documents)
    if not consumers:
        return None
    js_roots = _js_asset_data_roots(document, js_region, project, open_documents)
    if js_roots is None:
        return None
    scope_roots = _js_asset_scope_roots(document, js_region, project, open_documents)
    if scope_roots is None:
        return None
    events = _event_contract(consumers, document, project, open_documents)
    if events is None:
        return None
    state_roots = _shared_state_roots(consumers, document, project, open_documents)
    if state_roots is None:
        return None
    props = browser_component_props(js_region.source_map.template_source)
    component_globals = _component_js_global_types(consumers, project)
    if component_globals is None:
        return None
    preamble = _browser_preamble(
        js_roots,
        tuple(component_globals),
        props,
        tuple(events),
        state_roots,
        binding_types=component_globals,
        scope_roots=scope_roots,
        include_root_variables=False,
        component_js=True,
    )
    prefix = f"{preamble}\n"
    authored = js_region.source_map.template_source
    source = f"{prefix}{authored}"
    try:
        relative_char = parser_char_index(authored, js_parser_index)
    except ValueError:
        return None
    virtual_start = len(prefix)
    source_range = _range(js_region.source_map.map_range(0, len(authored.encode("utf-8"))))
    return BrowserProjection(
        source,
        _position(
            document_range_for_offsets(
                source,
                virtual_start + relative_char,
                virtual_start + relative_char,
            ).start
        ),
        source_range,
        _range(document_range_for_offsets(source, virtual_start, virtual_start + len(authored))),
        (),
        _browser_projection_owns_position(
            _component_js_expression(js_region),
            js_parser_index,
            js_roots,
            state_roots,
            component_js=True,
        ),
    )


def html_projection(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
) -> HtmlProjection | None:
    """Extract nested HTML or one source-proven ``<c-element>`` start tag."""
    region = document.region_at(position)
    if region is None:
        return None
    parsed = document.parsed.get(region.key)
    if parsed is None:
        # Provider edits and navigation must never use a recovered old tree.
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    projected = _html_projection_slice(
        parsed.template,
        region.source_map.template_source,
        parser_index,
        parser,
    )
    if projected is None:
        return None
    try:
        if not region.source_map.range_is_unambiguous(projected.start_index, projected.end_index):
            return None
        mapped_source_range = region.source_map.map_range(projected.start_index, projected.end_index)
        host_start = document_offset_at(document.source, mapped_source_range.start)
        host_end = document_offset_at(document.source, mapped_source_range.end)
        authored_source = _parser_source_slice(
            region.source_map.template_source,
            projected.start_index,
            projected.end_index,
        )
        provider_source = _linearly_mapped_html_source(
            authored_source,
            projected.source,
            document.source[host_start:host_end],
        )
        if provider_source is None:
            # Escapes and literal joins need a richer future source map.
            return None
        cursor_char = document_offset_at(document.source, _citry_position(position)) - host_start
        if not 0 <= cursor_char <= len(provider_source):
            return None
        source_range = _range(mapped_source_range)
    except ValueError:
        return None
    virtual_range = _range(document_range_for_offsets(provider_source, 0, len(provider_source)))
    virtual_position = _position(document_range_for_offsets(provider_source, cursor_char, cursor_char).start)
    return HtmlProjection(provider_source, virtual_position, source_range, virtual_range)


def _html_projection_slice(
    template: Any,
    template_source: str,
    index: int,
    parser: Any,
    *,
    base_index: int = 0,
) -> _HtmlProjectionSlice | None:
    """Prefer the smallest parser-proven HTML context containing ``index``."""
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        for attr in node.start_tag.attrs:
            if attr.kind != HtmlAttrKind.Template or attr.inner_value is None:
                continue
            nested = _parse_nested_template_source(attr.inner_value.content, parser)
            if nested is None:
                continue
            nested_template, nested_start, nested_source = nested
            absolute_start = base_index + attr.inner_value.start_index + nested_start
            absolute_end = absolute_start + len(nested_source.encode("utf-8"))
            if not (absolute_start <= index <= absolute_end):
                continue
            deeper = _html_projection_slice(
                nested_template,
                template_source,
                index,
                parser,
                base_index=absolute_start,
            )
            if deeper is not None:
                return deeper
            return _HtmlProjectionSlice(
                nested_source,
                absolute_start,
                absolute_end,
            )
        c_element = _c_element_projection_slice(node, template_source, index, base_index=base_index)
        if c_element is not None:
            return c_element
        body = getattr(node, "body", None)
        if body is not None and _node_body_contains(node, index, base_index=base_index):
            body_projection = _html_projection_slice(body, template_source, index, parser, base_index=base_index)
            if body_projection is not None:
                return body_projection
    return None


def _c_element_projection_slice(
    node: Any,
    template_source: str,
    index: int,
    *,
    base_index: int,
) -> _HtmlProjectionSlice | None:
    """Project a dynamic-element start tag to a same-length ordinary tag."""
    if not _is_c_element_tag(node.start_tag.name.content):
        return None
    start_tag = node.start_tag
    start = base_index + start_tag.token.start_index
    end = base_index + start_tag.token.end_index
    name_end = base_index + start_tag.name.end_index
    if not (name_end <= index <= end):
        return None

    private_attrs = [attr for attr in start_tag.attrs if _is_c_element_private_attr(attr.key.content)]
    if any(
        base_index + attr.token.start_index <= index <= base_index + attr.token.end_index for attr in private_attrs
    ):
        # These attributes describe Citry's selection mechanism, not the
        # selected HTML element, so the HTML provider must not claim them.
        return None

    authored = _parser_source_slice(template_source, start, end)
    projected = list(authored)
    relative_name_start = parser_char_index(authored, start_tag.name.start_index - start_tag.token.start_index)
    relative_name_end = parser_char_index(authored, start_tag.name.end_index - start_tag.token.start_index)
    target = _static_c_element_target(start_tag.attrs)
    provider_tag = (
        target if target is not None and len(target) <= relative_name_end - relative_name_start else "x-element"
    )
    replacement = provider_tag + " " * (relative_name_end - relative_name_start - len(provider_tag))
    projected[relative_name_start:relative_name_end] = replacement
    for attr in private_attrs:
        attr_start = parser_char_index(authored, attr.token.start_index - start_tag.token.start_index)
        attr_end = parser_char_index(authored, attr.token.end_index - start_tag.token.start_index)
        projected[attr_start:attr_end] = " " * (attr_end - attr_start)
    return _HtmlProjectionSlice(
        "".join(projected),
        start,
        end,
    )


def _static_c_element_target(attrs: list[Any]) -> str | None:
    """Return a literal effective tag only when no dynamic source can replace it."""
    if any(
        attr.key.content == "c-bind" or (attr.key.content.startswith("c-") and attr.key.content[2:].lower() == "is")
        for attr in attrs
    ):
        return None
    candidates = [attr for attr in attrs if attr.key.content.lower() == "is"]
    if len(candidates) != 1:
        return None
    candidate = candidates[0]
    if candidate.kind != HtmlAttrKind.Static or candidate.inner_value is None:
        return None
    value = candidate.inner_value.content
    return value.lower() if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", value) else None


def _is_c_element_private_attr(name: str) -> bool:
    """Recognize target channels without lowercasing Citry's prefix."""
    return name.lower() == "is" or name == "c-bind" or (name.startswith("c-") and name[2:].lower() == "is")


def _is_c_element_tag(name: str) -> bool:
    """Mirror Citry's exact prefix and case-insensitive component identity."""
    return name.startswith("c-") and name[2:].lower() == "element"


def _parser_source_slice(source: str, start_index: int, end_index: int) -> str:
    """Slice UTF-8 parser coordinates without accepting split code points."""
    encoded = source.encode("utf-8")
    return encoded[start_index:end_index].decode("utf-8")


def _linearly_mapped_html_source(authored: str, projected: str, host: str) -> str | None:
    """Carry host-only line indentation into a same-length HTML projection."""
    authored_lines = authored.splitlines(keepends=True)
    projected_lines = projected.splitlines(keepends=True)
    host_lines = host.splitlines(keepends=True)
    if len(authored_lines) != len(projected_lines) or len(authored_lines) != len(host_lines):
        return None
    mapped: list[str] = []
    for authored_line, projected_line, host_line in zip(authored_lines, projected_lines, host_lines, strict=True):
        authored_body, authored_ending = _split_line_ending(authored_line)
        projected_body, projected_ending = _split_line_ending(projected_line)
        host_body, host_ending = _split_line_ending(host_line)
        if (
            authored_ending != projected_ending
            or authored_ending != host_ending
            or not host_body.endswith(authored_body)
        ):
            return None
        prefix = host_body[: len(host_body) - len(authored_body)] if authored_body else host_body
        if prefix.strip(" \t"):
            return None
        mapped.append(f"{prefix}{projected_body}{host_ending}")
    return "".join(mapped)


def _split_line_ending(value: str) -> tuple[str, str]:
    """Separate one preserved LF or CRLF sequence from a projected line."""
    if value.endswith("\r\n"):
        return value[:-2], "\r\n"
    if value.endswith(("\n", "\r")):
        return value[:-1], value[-1]
    return value, ""


def _browser_projection_owns_position(
    expression: BrowserExpression,
    parser_index: int,
    roots: tuple[_JsDataRoot, ...],
    state_roots: tuple[_JsDataRoot, ...],
    *,
    component_js: bool,
) -> bool:
    """Prefer Citry's Python-backed hover and navigation at exact owned names."""
    identifier = browser_identifier_at(expression, parser_index)
    if identifier is not None and not component_js and identifier.root and identifier.name in _ALPINE_API_SPECS:
        return True
    if identifier is not None and component_js:
        if identifier.root and identifier.name == "$component":
            return True
        analysis = analyze_browser_component_source(expression.source)
        if analysis.valid and any(
            start <= parser_index <= end
            for binding in analysis.bindings
            for start, end in ((binding.start_index, binding.end_index), *binding.references)
        ):
            return True
    if (
        not component_js
        and identifier is not None
        and any(binding.name == identifier.name for binding in expression.binding_details)
    ):
        return True
    if not component_js and identifier is not None and identifier.root:
        return identifier.name in {root.name for root in roots}
    member = browser_member_at(expression, parser_index)
    if member is None:
        return False
    if member.owner == "$state" or (component_js and member.owner == "state"):
        return member.name in {root.name for root in state_roots}
    return component_js and member.owner in {"data", "scope"} and member.name in {root.name for root in roots}


def completion_items(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> list[types.CompletionItem]:
    """Return completion items without the surrounding LSP list metadata."""
    return list(completion_result(document, position, project, open_documents).items)


def completion_result(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> CompletionResult:
    """Return schema-free and optional registry-backed completions."""
    catalog = project.catalog
    event_result = _browser_event_completion_result(document, position, project, open_documents)
    if event_result is not None:
        return event_result
    browser_result = _browser_data_completion_result(document, position, project, open_documents)
    if browser_result is not None:
        return browser_result
    css_region = document.css_region_at(position)
    if css_region is not None:
        return _css_data_completion_result(document, css_region, position, project, open_documents)
    region = document.region_at(position)
    if region is None:
        return CompletionResult(())
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return CompletionResult(())
    cursor = parser_char_index(region.source_map.template_source, parser_index)
    source = region.source_map.template_source
    before = source[:cursor]

    template_roots = _template_data_roots(document, region, project, open_documents) if catalog is not None else ()
    parsed = document.parsed.get(region.key)
    if parsed is not None:
        lexical = _lexical_bindings_at(parsed.template, parser_index, ())
        if lexical is not None:
            nested_parser = project.analysis.parse_template if project.analysis is not None else parse_template
            query = template_python_query_at(parsed.template, parser_index, parse_nested=nested_parser)
            if query is not None or not _inside_fill_completion_value(before):
                if query is None:
                    root_context = _root_completion_context(source, cursor, token_aware=False)
                else:
                    query_start = parser_char_index(source, query.start_index)
                    root_context = _root_completion_context(
                        query.source,
                        cursor - query_start,
                        loop=query.host_kind == "loop",
                    )
                if not root_context:
                    return CompletionResult((), is_incomplete=True)
                ranges = _expression_completion_ranges(region, source, cursor)
                if ranges is None:
                    return CompletionResult((), is_incomplete=True)
                insert_range, replace_range = ranges
                return CompletionResult(
                    tuple(
                        _expression_completions(
                            lexical,
                            template_roots,
                            insert_range=insert_range,
                            replace_range=replace_range,
                        )
                    ),
                    is_incomplete=True,
                )
    # Empty dynamic attributes and unfinished expressions do not have a valid
    # tree, so recover only those broken buffers from the current text.
    unfinished = _unfinished_python_expression_context(source, cursor) if parsed is None else None
    if unfinished is not None:
        expression_source, expression_cursor, loop = unfinished
        if not _root_completion_context(expression_source, expression_cursor, loop=loop):
            return CompletionResult((), is_incomplete=True)
        ranges = _expression_completion_ranges(region, source, cursor)
        if ranges is None:
            return CompletionResult((), is_incomplete=True)
        insert_range, replace_range = ranges
        return CompletionResult(
            tuple(
                _expression_completions(
                    _current_text_lexical_bindings(source, cursor),
                    template_roots,
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
    open_documents: Mapping[str, DocumentState] | None = None,
) -> types.Hover | None:
    """Return Citry syntax, lexical, or catalog documentation under cursor."""
    browser_api_hover = _browser_api_hover(document, position, project)
    if browser_api_hover is not None:
        return browser_api_hover
    component_prop_hover = _browser_component_prop_hover(document, position, project, open_documents)
    if component_prop_hover is not None:
        return component_prop_hover
    browser_event_hover = _browser_event_hover(document, position, project, open_documents)
    if browser_event_hover is not None:
        return browser_event_hover
    browser_binding_hover = _browser_binding_hover(document, position, project, open_documents)
    if browser_binding_hover is not None:
        return browser_binding_hover
    browser_hover = _browser_data_hover(document, position, project, open_documents)
    if browser_hover is not None:
        return browser_hover
    browser_member_hover = _js_data_member_hover(document, position, project, open_documents)
    if browser_member_hover is not None:
        return browser_member_hover
    state_hover = _browser_state_hover(document, position, project, open_documents)
    if state_hover is not None:
        return state_hover
    css_hover = _css_data_hover(document, position, project, open_documents)
    if css_hover is not None:
        return css_hover
    variable = template_variable_hover(document, position, project, open_documents)
    if variable is not None:
        return render_template_variable_hover(variable)

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
        syntax_reference = _syntax_reference_at(parsed.template, parser_index)
    else:
        syntax_reference = None
    # A parser-shaped scan keeps syntax help available when a misplaced
    # structural tag makes the otherwise recognizable document invalid.
    if syntax_reference is None:
        syntax_reference = _syntax_reference_from_source(source, cursor)
    if syntax_reference is not None:
        syntax_range = _mapped_syntax_range(document, region, source, syntax_reference)
        if syntax_range is not None:
            return types.Hover(
                types.MarkupContent(
                    types.MarkupKind.Markdown,
                    _syntax_markdown(syntax_reference.spec),
                ),
                range=syntax_range,
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


def template_variable_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> TemplateVariableHover | None:
    """Describe the exact proven variable under the cursor without guessing its type."""
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    parsed = document.parsed.get(region.key)
    if parsed is None:
        return None

    # Lexical bindings shadow component roots, matching render-time name lookup.
    reference = _lexical_reference_at(parsed.template, parser_index)
    if reference is not None:
        return TemplateVariableHover(
            name=reference.binding.name,
            range=_range(region.source_map.map_range(reference.start_index, reference.end_index)),
            provenance=_lexical_binding_detail(reference.binding).capitalize() + ".",
            binding_kind=reference.binding.kind,
            is_declaration=(
                reference.start_index == reference.binding.start_index
                and reference.end_index == reference.binding.end_index
            ),
        )

    # A root is meaningful only when the registry proves which component owns this template.
    if project.catalog is None:
        return None
    field_reference = _template_data_reference_at(
        parsed.template,
        parser_index,
        _template_data_roots(document, region, project, open_documents),
    )
    if field_reference is None:
        return None
    root, use = field_reference
    if not _template_root_fields_are_current(root, open_documents):
        return None
    return TemplateVariableHover(
        name=root.name,
        range=_range(region.source_map.map_range(use.start_index, use.end_index)),
        provenance=_template_root_provenance(root),
        description=_template_root_hover_description(root),
        fallback_types=_template_root_fallback_types(root),
    )


def render_template_variable_hover(
    variable: TemplateVariableHover,
    semantic_types: tuple[str, ...] = (),
) -> types.Hover:
    """Render a Python-style variable declaration followed by Citry provenance."""
    # Analyzer answers win, while catalog text keeps declared roots readable during degradation.
    display_types = _safe_hover_types(semantic_types) or _safe_hover_types(variable.fallback_types)
    declaration = f"(variable) {variable.name}"
    if display_types:
        declaration += f": {_join_hover_types(display_types)}"
    lines = ["```python", declaration, "```", "", variable.provenance]
    if variable.description:
        lines.extend(("", variable.description))
    return types.Hover(
        types.MarkupContent(types.MarkupKind.Markdown, "\n".join(lines)),
        range=variable.range,
    )


def references(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
    *,
    include_declaration: bool = False,
) -> list[types.Location] | None:
    """Return references to one proven template root or lexical binding."""
    browser_binding_references = _browser_binding_reference_locations(
        document,
        position,
        project,
        open_documents,
        include_declaration=include_declaration,
    )
    if browser_binding_references is not None:
        return browser_binding_references
    browser_references = _browser_data_reference_locations(
        document,
        position,
        project,
        open_documents,
        include_declaration=include_declaration,
    )
    if browser_references is not None:
        return browser_references
    browser_member_references = _js_data_member_reference_locations(
        document,
        position,
        project,
        open_documents,
        include_declaration=include_declaration,
    )
    if browser_member_references is not None:
        return browser_member_references
    state_references = _browser_state_reference_locations(
        document,
        position,
        project,
        open_documents,
        include_declaration=include_declaration,
    )
    if state_references is not None:
        return state_references
    css_references = _css_data_reference_locations(
        document,
        position,
        project,
        open_documents,
        include_declaration=include_declaration,
    )
    if css_references is not None:
        return css_references
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    parsed = document.parsed.get(region.key)
    if parsed is None:
        return None

    lexical = _lexical_reference_at(parsed.template, parser_index)
    if lexical is not None:
        found = [
            types.Location(
                document.uri,
                _range(region.source_map.map_range(reference.start_index, reference.end_index)),
            )
            for reference in _lexical_references(parsed.template, lexical.binding)
        ]
        if include_declaration:
            found.append(
                types.Location(
                    document.uri,
                    _range(
                        region.source_map.map_range(
                            lexical.binding.start_index,
                            lexical.binding.end_index,
                        )
                    ),
                )
            )
        return list(_sorted_locations(found))

    # Root references require a registry because a spelling alone does not
    # prove which component contract owns the template.
    if project.catalog is None:
        return None
    field_reference = _template_data_reference_at(
        parsed.template,
        parser_index,
        _template_data_roots(document, region, project, open_documents),
    )
    if field_reference is None:
        return None
    root, _use = field_reference
    if not _template_root_fields_are_current(root, open_documents):
        return None
    found = [
        types.Location(
            document.uri,
            _range(region.source_map.map_range(use.start_index, use.end_index)),
        )
        for use in parsed.template.used_variables
        if _identifier_key(use.content) == _identifier_key(root.name)
    ]
    if include_declaration:
        found.extend(_template_root_locations(root, open_documents))
    return list(_sorted_locations(found))


def declaration(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> types.Location | list[types.Location] | None:
    """Navigate to the authored origin of one proven template variable."""
    component_prop_location = _browser_component_prop_origin(document, position, project, open_documents)
    if component_prop_location is not None:
        return component_prop_location
    browser_binding_location = _browser_binding_origin_location(document, position, project, open_documents)
    if browser_binding_location is not None:
        return browser_binding_location
    event_locations = _browser_event_origin_locations(document, position, project, open_documents)
    if event_locations:
        return event_locations[0] if len(event_locations) == 1 else list(event_locations)
    browser_locations = _browser_data_origin_locations(document, position, project, open_documents)
    if browser_locations:
        return browser_locations[0] if len(browser_locations) == 1 else list(browser_locations)
    browser_member_locations = _js_data_member_origin_locations(document, position, project, open_documents)
    if browser_member_locations:
        return browser_member_locations[0] if len(browser_member_locations) == 1 else list(browser_member_locations)
    state_locations = _browser_state_origin_locations(document, position, project, open_documents)
    if state_locations:
        return state_locations[0] if len(state_locations) == 1 else list(state_locations)
    css_locations = _css_data_origin_locations(document, position, project, open_documents)
    if css_locations:
        return css_locations[0] if len(css_locations) == 1 else list(css_locations)
    locations = _template_variable_origin_locations(document, position, project, open_documents)
    if not locations:
        return None
    if len(locations) == 1:
        return locations[0]
    return list(locations)


def definition(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> types.Location | list[types.Location] | None:
    """Navigate to an exact catalog or lexical declaration when provable."""
    component_prop_location = _browser_component_prop_origin(document, position, project, open_documents)
    if component_prop_location is not None:
        return component_prop_location
    browser_binding_location = _browser_binding_origin_location(document, position, project, open_documents)
    if browser_binding_location is not None:
        return browser_binding_location
    event_locations = _browser_event_origin_locations(document, position, project, open_documents)
    if event_locations:
        return event_locations[0] if len(event_locations) == 1 else list(event_locations)
    browser_locations = _browser_data_origin_locations(document, position, project, open_documents)
    if browser_locations:
        return browser_locations[0] if len(browser_locations) == 1 else list(browser_locations)
    browser_member_locations = _js_data_member_origin_locations(document, position, project, open_documents)
    if browser_member_locations:
        return browser_member_locations[0] if len(browser_member_locations) == 1 else list(browser_member_locations)
    state_locations = _browser_state_origin_locations(document, position, project, open_documents)
    if state_locations:
        return state_locations[0] if len(state_locations) == 1 else list(state_locations)
    css_locations = _css_data_origin_locations(document, position, project, open_documents)
    if css_locations:
        return css_locations[0] if len(css_locations) == 1 else list(css_locations)
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

    origins = _template_variable_origin_locations(document, position, project, open_documents)
    if origins:
        if len(origins) == 1:
            return origins[0]
        return list(origins)

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


def expression_shadows(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
    *,
    repair_completion: bool = False,
    repair_signature: bool = False,
) -> tuple[ExpressionShadow, ...]:
    """Build current analyzer inputs for the Python expression under the cursor."""
    catalog = project.catalog
    if catalog is None:
        return ()
    region = document.region_at(position)
    if region is None:
        return ()
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return ()
    parsed = document.parsed.get(region.key)
    query_source = region.source_map.template_source
    nested_parser = project.analysis.parse_template if project.analysis is not None else parse_template
    if parsed is not None:
        query_template = parsed.template
        query = template_python_query_at(parsed.template, parser_index, parse_nested=nested_parser)
        safety_query = query
    elif repair_completion:
        repaired = _repair_member_completion_query(query_source, parser_index, project)
        if repaired is None:
            return ()
        query_source, query, safety_query, query_template = repaired
    elif repair_signature:
        repaired = _repair_call_signature_query(query_source, parser_index, project)
        if repaired is None:
            return ()
        query_source, query, safety_query, query_template = repaired
    else:
        return ()
    if query is None or safety_query is None:
        return ()
    if safety_query.host_kind == "loop" and _query_contains_named_expression(safety_query):
        # Citry permits a walrus in the iterable, but Python forbids that
        # spelling in the comprehension used to model a c-for clause. Decline
        # semantics instead of surfacing the shadow's false syntax error.
        return ()
    if _query_contains_lambda_named_expression(safety_query):
        return ()
    query_start_char = parser_char_index(query_source, query.start_index)
    preceding_walrus = any(
        candidate.end_index <= query.start_index and _query_contains_named_expression(candidate)
        for candidate in template_python_queries(query_template, parse_nested=nested_parser)
    )
    if preceding_walrus:
        # Citry intentionally leaks walrus assignments into later render
        # context, including assignments made in lambdas. A standalone Python
        # shadow cannot model that flow soundly yet.
        return ()
    query_end_char = parser_char_index(query_source, query.end_index)
    if _mapped_template_range(region, query_source, query_start_char, query_end_char) is None:
        return ()
    query_start = query_start_char
    cursor = parser_char_index(query_source, parser_index)
    cursor_offset = cursor - query_start
    if cursor_offset < 0 or cursor_offset > len(query.source):
        return ()
    if repair_completion:
        query = _completion_query_with_none_narrowing(query, cursor_offset)

    consumers = _expression_shadow_consumers(document, region, project, open_documents)
    if consumers is None:
        return ()
    return _build_expression_shadows(consumers, query, cursor_offset)


def _expression_shadow_consumers(
    document: DocumentState,
    region: TemplateRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_ExpressionShadowConsumer, ...] | None:
    """Validate consumer joins once before building one or many query shadows."""
    owners = _template_consumers(document, region, project, open_documents)
    contexts = tuple(_component_template_context(owner, project, document, open_documents) for owner in owners)
    if not contexts or any(context is None for context in contexts):
        return None
    consumers: list[_ExpressionShadowConsumer] = []
    for owner, context in zip(owners, contexts, strict=True):
        if (
            context is None
            or context.source_file is None
            or context.source is None
            or context.source_kind not in {"schema", "inferred"}
            or context.source_qualname is None
        ):
            return None
        consumers.append(
            _ExpressionShadowConsumer(
                identity=owner.definition_id,
                source_file=context.source_file,
                source=context.source,
                source_kind=cast("Literal['schema', 'inferred']", context.source_kind),
                source_module=context.source_module,
                source_qualname=context.source_qualname,
                kwargs_type=context.kwargs_type,
                roots=tuple(
                    TemplatePythonRoot(
                        root.name,
                        root.presence,
                        root.access,
                        root.type_field.source_module if root.type_field is not None else None,
                        root.type_field.source_qualname if root.type_field is not None else None,
                        root.shadow_type_display,
                    )
                    for root in context.roots
                ),
            )
        )
    return tuple(consumers)


def _build_expression_shadows(
    consumers: tuple[_ExpressionShadowConsumer, ...],
    query: TemplatePythonQuery,
    cursor_offset: int,
) -> tuple[ExpressionShadow, ...]:
    """Build one query from source facts already proven for every consumer."""
    shadows: list[ExpressionShadow] = []
    for consumer in consumers:
        if consumer.source_kind == "schema":
            shadow = build_schema_template_shadow(
                consumer.source,
                consumer.source_qualname,
                consumer.roots,
                query,
                source_module=consumer.source_module,
                source_is_package=consumer.source_file.name == "__init__.py",
            )
        else:
            shadow = build_inferred_template_shadow(
                consumer.source,
                consumer.source_qualname,
                consumer.roots,
                query,
                source_module=consumer.source_module,
                source_is_package=consumer.source_file.name == "__init__.py",
                kwargs_type=consumer.kwargs_type,
            )
        if shadow is None:
            return ()
        shadows.append(
            ExpressionShadow(
                identity=consumer.identity,
                source_file=consumer.source_file,
                source=consumer.source,
                document=shadow,
                query=query,
                cursor_offset=cursor_offset,
            )
        )
    return tuple(shadows)


def _query_contains_named_expression(query: TemplatePythonQuery) -> bool:
    """Return whether one complete Python host mutates the render context."""
    framed = f"[\nNone for {query.source}\n]" if query.host_kind == "loop" else query.source
    try:
        tree = ast.parse(framed, mode="eval")
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return True
    return any(isinstance(node, ast.NamedExpr) for node in ast.walk(tree))


def _query_contains_lambda_named_expression(query: TemplatePythonQuery) -> bool:
    """Detect Citry's context-leaking lambda assignment special case."""
    framed = f"[\nNone for {query.source}\n]" if query.host_kind == "loop" else query.source
    try:
        tree = ast.parse(framed, mode="eval")
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return True
    return any(
        isinstance(node, ast.Lambda)
        and any(isinstance(descendant, ast.NamedExpr) for descendant in ast.walk(node.body))
        for node in ast.walk(tree)
    )


def _repair_member_completion_query(
    source: str,
    parser_index: int,
    project: ProjectState,
) -> tuple[str, TemplatePythonQuery, TemplatePythonQuery, Any] | None:
    """Insert a temporary member name after a trailing dot for analyzer context."""
    cursor = parser_char_index(source, parser_index)
    if cursor == 0 or source[cursor - 1] != ".":
        return None
    placeholder = "__citry_completion__"
    repaired = f"{source[:cursor]}{placeholder}{source[cursor:]}"
    try:
        template = (
            project.analysis.parse_template(repaired) if project.analysis is not None else parse_template(repaired)
        )
    except (SyntaxError, ValueError):
        return None
    query = template_python_query_at(
        template,
        parser_index,
        parse_nested=project.analysis.parse_template if project.analysis is not None else parse_template,
    )
    if query is None:
        return None
    query_start = parser_char_index(repaired, query.start_index)
    relative_cursor = cursor - query_start
    if query.source[relative_cursor : relative_cursor + len(placeholder)] != placeholder:
        return None
    original_query = replace(
        query,
        source=f"{query.source[:relative_cursor]}{query.source[relative_cursor + len(placeholder) :]}",
        end_index=query.end_index - len(placeholder.encode()),
    )
    # Keep the valid repaired query for AST safety checks. The authored query
    # is intentionally incomplete so ty can answer at the trailing dot.
    return source, original_query, query, template


def _repair_call_signature_query(
    source: str,
    parser_index: int,
    project: ProjectState,
) -> tuple[str, TemplatePythonQuery, TemplatePythonQuery, Any] | None:
    """Temporarily close a call whose opening syntax precedes the cursor."""
    cursor = parser_char_index(source, parser_index)
    prefix = source[:cursor].rstrip()
    if not prefix or prefix[-1] not in {"(", ","}:
        return None
    # Trying a small number of closing parentheses avoids inventing a Python
    # parser here while covering ordinary and nested unfinished calls.
    for close_count in range(1, 9):
        placeholder = f"None{')' * close_count}"
        repaired = f"{source[:cursor]}{placeholder}{source[cursor:]}"
        try:
            template = (
                project.analysis.parse_template(repaired) if project.analysis is not None else parse_template(repaired)
            )
        except (SyntaxError, ValueError):
            continue
        query = template_python_query_at(
            template,
            parser_index,
            parse_nested=project.analysis.parse_template if project.analysis is not None else parse_template,
        )
        if query is None:
            continue
        query_start = parser_char_index(repaired, query.start_index)
        relative_cursor = cursor - query_start
        if query.source[relative_cursor : relative_cursor + len(placeholder)] != placeholder:
            continue
        original_query = replace(
            query,
            source=f"{query.source[:relative_cursor]}{query.source[relative_cursor + len(placeholder) :]}",
            end_index=query.end_index - len(placeholder.encode()),
        )
        return source, original_query, query, template
    return None


def _completion_query_with_none_narrowing(
    query: TemplatePythonQuery,
    cursor_offset: int,
) -> TemplatePythonQuery:
    """Let completion expose a direct root's non-None member surface."""
    identifier = r"[^\W\d]\w*"
    match = re.search(
        rf"(?<![\w.])(?P<receiver>{identifier})\s*\.\s*(?:{identifier})?\Z",
        query.source[:cursor_offset],
    )
    if match is None:
        return query
    receiver = match.group("receiver")
    if receiver not in query.free_names:
        return query
    # ty intentionally intersects union members, so `str | None` otherwise
    # exposes no useful public completions. This synthetic control affects
    # completion only; diagnostics and hover still see the authored union.
    control = TemplatePythonControl(
        "if",
        f"{receiver} is not None",
        free_names=(receiver,),
    )
    return replace(query, controls=(*query.controls, control))


def expression_completion_ranges(
    document: DocumentState,
    position: types.Position,
) -> tuple[types.Range, types.Range] | None:
    """Return exact insert and replace ranges for a semantic completion."""
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    source = region.source_map.template_source
    cursor = parser_char_index(source, parser_index)
    return _expression_completion_ranges(region, source, cursor)


def all_expression_shadows(
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> tuple[ExpressionShadowGroup, ...]:
    """Build analyzer inputs for every currently valid Python expression."""
    synchronized = _open_document_generation(open_documents)
    if document._expression_shadow_project is project and document._expression_shadow_documents == synchronized:
        return document._expression_shadow_groups

    groups: list[ExpressionShadowGroup] = []
    nested_parser = project.analysis.parse_template if project.analysis is not None else parse_template
    for parsed in document.parsed.values():
        queries = template_python_queries(parsed.template, parse_nested=nested_parser)
        consumers = _expression_shadow_consumers(document, parsed.region, project, open_documents)
        if consumers is None:
            continue
        walrus_ends: list[int] = []
        for query in queries:
            has_walrus = _query_contains_named_expression(query)
            if (
                (query.host_kind == "loop" and has_walrus)
                or _query_contains_lambda_named_expression(query)
                or any(end_index <= query.start_index for end_index in walrus_ends)
            ):
                if has_walrus:
                    walrus_ends.append(query.end_index)
                continue
            query_start = parser_char_index(parsed.region.source_map.template_source, query.start_index)
            query_end = parser_char_index(parsed.region.source_map.template_source, query.end_index)
            if (
                _mapped_template_range(
                    parsed.region,
                    parsed.region.source_map.template_source,
                    query_start,
                    query_end,
                )
                is None
            ):
                if has_walrus:
                    walrus_ends.append(query.end_index)
                continue
            mapped = parsed.region.source_map.map_range(query.start_index, query.start_index)
            position = types.Position(mapped.start.line, mapped.start.character)
            shadows = _build_expression_shadows(consumers, query, 0)
            if shadows:
                groups.append(ExpressionShadowGroup(position, shadows))
            if has_walrus:
                walrus_ends.append(query.end_index)
    result = tuple(groups)
    # Keep only one exact generation so edits in another open document cannot leak memory.
    document._expression_shadow_project = project
    document._expression_shadow_documents = synchronized
    document._expression_shadow_groups = result
    return result


def _open_document_generation(
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[tuple[str, int, int, str], ...]:
    """Describe exact synchronized inputs without trusting version monotonicity."""
    if open_documents is None:
        return ()
    return tuple(
        sorted(
            (uri, id(candidate), candidate._analysis_revision, candidate.language_id)
            for uri, candidate in open_documents.items()
        )
    )


def semantic_dependencies(
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> SemanticDependencies:
    """Return direct Python inputs and whether they exhaust semantic dependencies."""
    source_paths: set[Path] = set()
    complete = project.source_analysis is not None
    for parsed in document.parsed.values():
        consumers = _template_consumers(document, parsed.region, project, open_documents)
        if not consumers:
            complete = False
            continue
        for component in consumers:
            if component.python_file is not None:
                source_paths.add(component.python_file.resolve())
            if project.source_analysis is None:
                complete = False
                continue
            asset_chain = project.source_analysis.template_asset_chain(component)
            data_chain = project.source_analysis.template_data_chain(component)
            if asset_chain is None or data_chain is None:
                complete = False
            for chain in (asset_chain, data_chain):
                if chain is not None:
                    source_paths.update(candidate.source_file.resolve() for candidate in chain)
            context = _component_template_context(component, project, document, open_documents)
            if context is None:
                complete = False
                continue
            if context.source_file is not None:
                source_paths.add(context.source_file.resolve())
            for root in context.roots:
                source_paths.update(
                    field.source_file.resolve() for field in root.fields if field.source_file is not None
                )
                source_paths.update(definition.source_file.resolve() for definition in root.lint_definitions)

            # Annotation imports and helper calls can cross files that the
            # portable registry does not index yet. Callers may prioritize the
            # direct set, but must retain a workspace fallback while incomplete.
            if context.source is not None:
                complete = False
    return SemanticDependencies(
        frozenset(path.as_uri() for path in source_paths),
        complete,
    )


def map_expression_shadow_range(
    document: DocumentState,
    position: types.Position,
    shadow: ExpressionShadow,
    shadow_range: types.Range,
) -> types.Range | None:
    """Map a range only when it lies wholly inside one copied expression."""
    region = document.region_at(position)
    if region is None:
        return None
    start = _source_offset_at_position(shadow.document.source, shadow_range.start)
    end = _source_offset_at_position(shadow.document.source, shadow_range.end)
    if start is None or end is None or end < start:
        return None
    for copied in shadow.document.copies:
        if copied.shadow_start <= start <= end <= copied.shadow_end:
            template_start = parser_char_index(region.source_map.template_source, copied.template_start)
            authored_start = template_start + start - copied.shadow_start
            authored_end = template_start + end - copied.shadow_start
            if authored_end > len(region.source_map.template_source):
                return None
            return _mapped_template_range(
                region,
                region.source_map.template_source,
                authored_start,
                authored_end,
            )
    return None


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
            code = PARSE_CONFIGURATION
        return None, [
            types.Diagnostic(
                _range(mapped),
                str(exc),
                severity=types.DiagnosticSeverity.Error,
                code=code,
                code_description=types.CodeDescription(diagnostic_documentation_url(code)),
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
                        render_diagnostic(TEMPLATE_UNKNOWN_COMPONENT, tag=tag.content),
                        severity=types.DiagnosticSeverity.Error,
                        code=TEMPLATE_UNKNOWN_COMPONENT,
                        code_description=types.CodeDescription(
                            diagnostic_documentation_url(TEMPLATE_UNKNOWN_COMPONENT)
                        ),
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


def _lexical_references(
    template: Any,
    target: _LexicalBinding,
    environment: tuple[_LexicalBinding, ...] = (),
    *,
    base_index: int = 0,
) -> tuple[_LexicalReference, ...]:
    """Collect uses that resolve to one exact parser-proven binding."""
    found: list[_LexicalReference] = []
    for element in template.elements:
        value: Any = element._0
        if isinstance(element, TemplateElement.Expr):
            found.extend(_references_for_uses(value.used_variables, environment, target, base_index=base_index))
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
                    found.extend(
                        _lexical_references(
                            nested,
                            target,
                            attr_environment,
                            base_index=base_index + attr.inner_value.start_index + nested_start,
                        )
                    )
                    continue
            found.extend(_references_for_uses(attr.used_variables, attr_environment, target, base_index=base_index))
        body = getattr(node, "body", None)
        if body is not None:
            found.extend(
                _lexical_references(
                    body,
                    target,
                    (*environment, *introduced),
                    base_index=base_index,
                )
            )
    return tuple(sorted(found, key=lambda reference: (reference.start_index, reference.end_index)))


def _references_for_uses(
    uses: list[Any],
    environment: tuple[_LexicalBinding, ...],
    target: _LexicalBinding,
    *,
    base_index: int,
) -> tuple[_LexicalReference, ...]:
    found: list[_LexicalReference] = []
    for use in uses:
        binding = next(
            (
                candidate
                for candidate in reversed(environment)
                if _identifier_key(candidate.name) == _identifier_key(use.content)
            ),
            None,
        )
        if binding == target:
            found.append(
                _LexicalReference(
                    binding,
                    base_index + use.start_index,
                    base_index + use.end_index,
                )
            )
    return tuple(found)


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
    parsed = _parse_nested_template_source(source, parse_template)
    return (parsed[0], parsed[1]) if parsed is not None else None


def _parse_nested_template_source(source: str, parser: Any) -> tuple[Any, int, str] | None:
    """Return a nested tree together with its exact unwrapped authored source."""
    nested_source = source
    nested_start = 0
    trimmed = source.strip()
    if trimmed.startswith("<>") and trimmed.endswith("</>"):
        nested_source = trimmed[2:-3]
        leading = source[: len(source) - len(source.lstrip())]
        nested_start = len(leading.encode("utf-8")) + 2
    try:
        return parser(nested_source), nested_start, nested_source
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
class _SyntaxSpec:
    """One parser-owned spelling shared by completion and hover."""

    label: str
    kind: str
    detail: str
    documentation: str
    documentation_url: str
    context: str | None = None
    insert_text: str | None = None
    repeatable: bool = False
    primary_attribute: str | None = None


_BUILTINS_URL = "https://citry.dev/reference/builtins/"
_CONTROL_FLOW_URL = "https://citry.dev/syntax/control-flow/"
_DYNAMIC_ATTRIBUTES_URL = "https://citry.dev/syntax/dynamic-attributes/"
_SLOTS_URL = "https://citry.dev/concepts/slots/"
_CLIENT_INTERACTIVITY_URL = "https://citry.dev/concepts/client-interactivity/"
_DYNAMIC_COMPONENTS_URL = "https://citry.dev/advanced/dynamic-components/"

# Keeping the authored spellings and their prose together makes a new parser
# feature visibly incomplete until both completion and hover can describe it.
_CITRY_SYNTAX = (
    _SyntaxSpec(
        "c-if",
        "tag",
        "Conditional branch",
        "Render this block when its `cond` Python expression is truthy.",
        f"{_BUILTINS_URL}#c-if",
        primary_attribute="cond",
    ),
    _SyntaxSpec(
        "c-elif",
        "tag",
        "Else-if branch",
        "Add another conditional block after an adjacent `<c-if>` or `<c-elif>`.",
        f"{_BUILTINS_URL}#c-elif",
        primary_attribute="cond",
    ),
    _SyntaxSpec(
        "c-else",
        "tag",
        "Else branch",
        "Add the final fallback block to an adjacent conditional chain.",
        f"{_BUILTINS_URL}#c-else",
    ),
    _SyntaxSpec(
        "c-for",
        "tag",
        "Loop over an iterable",
        "Repeat this block using the Python-style loop clause in `each`.",
        f"{_BUILTINS_URL}#c-for",
        primary_attribute="each",
    ),
    _SyntaxSpec(
        "c-empty",
        "tag",
        "Empty branch for a loop",
        "Render this block when the adjacent `<c-for>` produces no values.",
        f"{_BUILTINS_URL}#c-empty",
    ),
    _SyntaxSpec(
        "c-raw",
        "tag",
        "Render its body as literal text",
        "Keep template-looking text in this block unchanged.",
        f"{_BUILTINS_URL}#c-raw",
    ),
    _SyntaxSpec(
        "c-fill",
        "tag",
        "Fill a component slot",
        "Choose the slot that receives this block of content.",
        f"{_BUILTINS_URL}#c-fill",
        primary_attribute="name",
    ),
    _SyntaxSpec(
        "c-slot",
        "tag",
        "Declare a component slot outlet",
        "Mark where content supplied by a component caller should appear.",
        f"{_BUILTINS_URL}#c-slot",
    ),
    _SyntaxSpec(
        "c-if",
        "attribute",
        "Citry conditional directive",
        "Render this element or component when the Python expression is truthy.",
        _CONTROL_FLOW_URL,
        context="general",
        insert_text='c-if="${1:condition}"',
    ),
    _SyntaxSpec(
        "c-elif",
        "attribute",
        "Citry else-if directive",
        "Add this element as the next branch when earlier adjacent conditions are false.",
        _CONTROL_FLOW_URL,
        context="general",
        insert_text='c-elif="${1:condition}"',
    ),
    _SyntaxSpec(
        "c-else",
        "attribute",
        "Citry else directive",
        "Add this element as the final fallback in an adjacent conditional chain.",
        _CONTROL_FLOW_URL,
        context="general",
        insert_text="c-else",
    ),
    _SyntaxSpec(
        "c-for",
        "attribute",
        "Citry loop directive",
        "Repeat this element using a Python-style loop clause.",
        _CONTROL_FLOW_URL,
        context="general",
        insert_text='c-for="${1:item} in ${2:items}"',
    ),
    _SyntaxSpec(
        "c-empty",
        "attribute",
        "Citry empty-loop directive",
        "Render this element when the adjacent `c-for` produces no values.",
        _CONTROL_FLOW_URL,
        context="general",
        insert_text="c-empty",
    ),
    _SyntaxSpec(
        "c-bind",
        "attribute",
        "Spread a Python attribute mapping",
        "Evaluate a Python mapping and apply its entries as attributes or component inputs.",
        f"{_DYNAMIC_ATTRIBUTES_URL}#c-bind-spread",
        context="general",
        insert_text='c-bind="${1:attributes}"',
        repeatable=True,
    ),
    _SyntaxSpec(
        "#c-key",
        "attribute",
        "Stable Citry morph key",
        "Give this element or component a stable identity across browser updates.",
        f"{_DYNAMIC_ATTRIBUTES_URL}#c-key",
        context="general",
        insert_text='#c-key="${1:key}"',
    ),
    _SyntaxSpec(
        "#c-ignore",
        "attribute",
        "Exclude this subtree from Citry morphing",
        "Keep this browser-owned subtree unchanged during Citry updates.",
        f"{_DYNAMIC_ATTRIBUTES_URL}#c-ignore",
        context="general",
        insert_text="#c-ignore",
    ),
    _SyntaxSpec(
        "$c-props",
        "attribute",
        "Supply client-side component props",
        "Pass the result of this Alpine expression to the child component as live props.",
        f"{_CLIENT_INTERACTIVITY_URL}#pass-client-props-down",
        context="component",
        insert_text='\\$c-props="${1:{}}"',
    ),
    _SyntaxSpec(
        "c-$c-props",
        "attribute",
        "Compute the complete client props expression in Python",
        "Evaluate Python to produce the Alpine expression used for the child component's live props.",
        f"{_CLIENT_INTERACTIVITY_URL}#pass-client-props-down",
        context="component",
        insert_text='c-\\$c-props="${1:expression}"',
    ),
    _SyntaxSpec(
        "cond",
        "attribute",
        "Conditional expression",
        "Evaluate this Python expression to decide whether the branch renders.",
        _CONTROL_FLOW_URL,
        context="c-if",
        insert_text='cond="${1:condition}"',
    ),
    _SyntaxSpec(
        "cond",
        "attribute",
        "Conditional expression",
        "Evaluate this Python expression to decide whether the branch renders.",
        _CONTROL_FLOW_URL,
        context="c-elif",
        insert_text='cond="${1:condition}"',
    ),
    _SyntaxSpec(
        "each",
        "attribute",
        "Loop clause",
        "Bind loop targets and choose the Python iterable for this repeated block.",
        _CONTROL_FLOW_URL,
        context="c-for",
        insert_text='each="${1:item} in ${2:items}"',
    ),
    _SyntaxSpec(
        "name",
        "attribute",
        "Static slot name",
        "Select this slot by its literal name.",
        _SLOTS_URL,
        context="c-fill",
        insert_text='name="${1:default}"',
    ),
    _SyntaxSpec(
        "c-name",
        "attribute",
        "Dynamic slot name",
        "Evaluate Python to choose the slot name at render time.",
        f"{_SLOTS_URL}#dynamic-slot-names",
        context="c-fill",
        insert_text='c-name="${1:name}"',
    ),
    _SyntaxSpec(
        "data",
        "attribute",
        "Bind data exposed by this slot",
        "Bind fields exposed by the selected slot to names available in this fill body.",
        f"{_SLOTS_URL}#scoped-slots-passing-data-to-the-fill",
        context="c-fill",
        insert_text='data="${1:data}"',
    ),
    _SyntaxSpec(
        "fallback",
        "attribute",
        "Bind fallback content",
        "Bind the selected slot's fallback content to a local `Slot` variable inside this fill.",
        f"{_SLOTS_URL}#wrapping-the-fallback",
        context="c-fill",
        insert_text='fallback="${1:fallback}"',
    ),
    _SyntaxSpec(
        "c-bind",
        "attribute",
        "Spread fill attributes",
        "Evaluate a Python mapping that may provide the fill's slot name and bindings.",
        f"{_SLOTS_URL}#spread-slot-and-fill-settings",
        context="c-fill",
        insert_text='c-bind="${1:attributes}"',
        repeatable=True,
    ),
    _SyntaxSpec(
        "name",
        "attribute",
        "Static slot name",
        "Declare this slot under a literal name; omitting it declares the default slot.",
        _SLOTS_URL,
        context="c-slot",
        insert_text='name="${1:default}"',
    ),
    _SyntaxSpec(
        "c-name",
        "attribute",
        "Dynamic slot name",
        "Evaluate Python to choose this outlet's slot name at render time.",
        f"{_SLOTS_URL}#dynamic-slot-names",
        context="c-slot",
        insert_text='c-name="${1:name}"',
    ),
    _SyntaxSpec(
        "required",
        "attribute",
        "Require a fill for this slot",
        "Raise at render time when this outlet is reached without a supplied fill.",
        f"{_SLOTS_URL}#supply-fallback-content",
        context="c-slot",
        insert_text="required",
    ),
    _SyntaxSpec(
        "c-required",
        "attribute",
        "Compute whether this slot is required",
        "Evaluate Python to decide whether this outlet requires a supplied fill.",
        f"{_SLOTS_URL}#require-a-slot-conditionally",
        context="c-slot",
        insert_text='c-required="${1:condition}"',
    ),
    _SyntaxSpec(
        "c-bind",
        "attribute",
        "Spread slot attributes and data",
        "Evaluate a Python mapping that may provide the slot name, requirement, and exposed data.",
        f"{_SLOTS_URL}#spread-slot-and-fill-settings",
        context="c-slot",
        insert_text='c-bind="${1:attributes}"',
        repeatable=True,
    ),
    _SyntaxSpec(
        "is",
        "attribute",
        "Static dynamic target",
        "Select a component or HTML element by its literal name.",
        _DYNAMIC_COMPONENTS_URL,
        context="dynamic-target",
        insert_text='is="${1:target}"',
    ),
    _SyntaxSpec(
        "c-is",
        "attribute",
        "Computed dynamic target",
        "Evaluate Python to choose the component or HTML element rendered here.",
        _DYNAMIC_COMPONENTS_URL,
        context="dynamic-target",
        insert_text='c-is="${1:target}"',
    ),
    _SyntaxSpec(
        "c-bind",
        "attribute",
        "Spread target attributes",
        "Evaluate a Python mapping that may provide the dynamic target and its attributes.",
        f"{_DYNAMIC_ATTRIBUTES_URL}#c-bind-spread",
        context="dynamic-target",
        insert_text='c-bind="${1:attributes}"',
        repeatable=True,
    ),
)


def _syntax_specs(*, kind: str, context: str | None = None) -> tuple[_SyntaxSpec, ...]:
    """Select syntax records while preserving their intentional display order."""
    return tuple(spec for spec in _CITRY_SYNTAX if spec.kind == kind and spec.context == context)


_STRUCTURAL_TAG_SPECS = {spec.label: spec for spec in _syntax_specs(kind="tag")}
_GENERAL_DIRECTIVES = _syntax_specs(kind="attribute", context="general")
_CLIENT_PROP_DIRECTIVES = _syntax_specs(kind="attribute", context="component")
_STRUCTURAL_ATTRIBUTES: dict[str, tuple[_SyntaxSpec, ...]] = {
    name: _syntax_specs(kind="attribute", context=name) for name in RESERVED_TAG_NAMES
}
# Slots may also carry condition/loop directives, unlike the other structural
# tags, so add the parser's five control-flow forms after slot-owned fields.
_STRUCTURAL_ATTRIBUTES["c-slot"] = (*_STRUCTURAL_ATTRIBUTES["c-slot"], *_GENERAL_DIRECTIVES[:5])
_DYNAMIC_TARGET_ATTRIBUTES = _syntax_specs(kind="attribute", context="dynamic-target")


def _validate_syntax_metadata() -> None:
    """Refuse editor metadata that has drifted from the parser inventory."""
    keys = [(spec.kind, spec.context, spec.label) for spec in _CITRY_SYNTAX]
    if len(keys) != len(set(keys)):
        msg = "Citry syntax metadata contains a duplicate kind/context/name entry."
        raise RuntimeError(msg)
    if frozenset(_STRUCTURAL_TAG_SPECS) != RESERVED_TAG_NAMES:
        msg = "Citry structural-tag hover metadata does not match the parser inventory."
        raise RuntimeError(msg)
    documented_directives = {
        spec.label for spec in _CITRY_SYNTAX if spec.kind == "attribute" and spec.context in {"general", "component"}
    }
    if documented_directives != CITRY_DIRECTIVE_NAMES:
        msg = "Citry directive hover metadata does not match the parser inventory."
        raise RuntimeError(msg)
    documented_structural_attributes = {
        tag_name: frozenset(spec.label for spec in specs) for tag_name, specs in _STRUCTURAL_ATTRIBUTES.items()
    }
    if documented_structural_attributes != STRUCTURAL_TAG_ATTRIBUTE_NAMES:
        msg = "Citry structural-attribute hover metadata does not match the parser inventory."
        raise RuntimeError(msg)
    if any(not spec.documentation_url.startswith("https://citry.dev/") for spec in _CITRY_SYNTAX):
        msg = "Citry syntax hover metadata must link to canonical citry.dev documentation."
        raise RuntimeError(msg)


_validate_syntax_metadata()


def _syntax_reference_at(
    template: Any,
    index: int,
    *,
    base_index: int = 0,
) -> _SyntaxReference | None:
    """Find parser-owned syntax using AST tokens, including nested templates."""
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        tag_name = node.start_tag.name.content
        tag_spec = _STRUCTURAL_TAG_SPECS.get(tag_name)
        start_name = node.start_tag.name
        if tag_spec is not None and _token_contains(start_name, index, base_index=base_index):
            return _SyntaxReference(
                tag_spec,
                base_index + start_name.start_index,
                base_index + start_name.end_index,
            )
        end_tag = getattr(node, "end_tag", None)
        if (
            end_tag is not None
            and tag_spec is not None
            and _token_contains(end_tag.name, index, base_index=base_index)
        ):
            return _SyntaxReference(
                tag_spec,
                base_index + end_tag.name.start_index,
                base_index + end_tag.name.end_index,
            )
        for attr in node.start_tag.attrs:
            if _token_contains(attr.key, index, base_index=base_index):
                attr_spec = _syntax_attribute_spec(tag_name, attr.key.content)
                if attr_spec is not None:
                    return _SyntaxReference(
                        attr_spec,
                        base_index + attr.key.start_index,
                        base_index + attr.key.end_index,
                    )
            if attr.kind != HtmlAttrKind.Template or attr.inner_value is None:
                continue
            parsed_nested = _parse_nested_template(attr.inner_value.content)
            if parsed_nested is None:
                continue
            nested, nested_start = parsed_nested
            reference = _syntax_reference_at(
                nested,
                index,
                base_index=base_index + attr.inner_value.start_index + nested_start,
            )
            if reference is not None:
                return reference
        body = getattr(node, "body", None)
        if body is not None:
            reference = _syntax_reference_at(body, index, base_index=base_index)
            if reference is not None:
                return reference
    return None


def _token_contains(token: Any, index: int, *, base_index: int) -> bool:
    """Use the parser's byte offsets for an exact authored token lookup."""
    return base_index + token.start_index <= index < base_index + token.end_index


def _syntax_attribute_spec(tag_name: str, attr_name: str) -> _SyntaxSpec | None:
    """Resolve context-sensitive structural attributes before general directives."""
    normalized_tag = tag_name.lower()
    if normalized_tag in RESERVED_TAG_NAMES:
        # Reserved tags accept only their context-qualified fixed syntax. This
        # keeps recovery hover from documenting parser-forbidden directives.
        return next(
            (spec for spec in _STRUCTURAL_ATTRIBUTES[normalized_tag] if spec.label == attr_name),
            None,
        )
    contexts: list[str | None] = []
    if normalized_tag in {"c-component", "c-element"}:
        contexts.append("dynamic-target")
    is_component = tag_name.startswith("c-") and normalized_tag not in {
        *RESERVED_TAG_NAMES,
        "c-element",
    }
    if is_component:
        contexts.append("component")
    contexts.append("general")
    return next(
        (
            spec
            for context in contexts
            for spec in _CITRY_SYNTAX
            if spec.kind == "attribute" and spec.context == context and spec.label == attr_name
        ),
        None,
    )


def _syntax_reference_from_source(source: str, cursor: int) -> _SyntaxReference | None:
    """Recognize complete real tags when semantic validation rejected the tree."""
    for tag_start, tag_text, closing, tag_name, _self_closing in _complete_tags(source):
        tag_end = tag_start + len(tag_text)
        if not tag_start <= cursor <= tag_end:
            continue
        match = re.match(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)", tag_text)
        if match is None:
            continue
        name_start = tag_start + match.start(2)
        name_end = tag_start + match.end(2)
        tag_spec = _STRUCTURAL_TAG_SPECS.get(tag_name)
        if name_start <= cursor < name_end and tag_spec is not None:
            return _SyntaxReference(
                tag_spec,
                _char_to_byte(source, name_start),
                _char_to_byte(source, name_end),
            )
        if closing:
            continue
        attr_reference = _syntax_attribute_reference_in_tag(source, tag_text, tag_start, tag_name, cursor)
        if attr_reference is not None:
            return attr_reference
    return None


def _syntax_attribute_reference_in_tag(
    source: str,
    tag_text: str,
    tag_start: int,
    tag_name: str,
    cursor: int,
) -> _SyntaxReference | None:
    """Scan only attribute names, skipping quoted values and Citry comments."""
    tag_match = re.match(r"<\s*[A-Za-z][\w:.-]*", tag_text)
    if tag_match is None:
        return None
    index = tag_match.end()
    limit = len(tag_text)
    while index < limit:
        if tag_text[index].isspace():
            index += 1
            continue
        if tag_text.startswith("{#", index):
            comment_end = tag_text.find("#}", index + 2)
            if comment_end < 0:
                return None
            index = comment_end + 2
            continue
        if tag_text[index] in {"/", ">", "<"}:
            return None
        name_start = index
        while index < limit and _attribute_name_continues(tag_text, index):
            index += 1
        if name_start == index:
            index += 1
            continue
        name_end = index
        authored_start = tag_start + name_start
        authored_end = tag_start + name_end
        if authored_start <= cursor < authored_end:
            spec = _syntax_attribute_spec(tag_name, tag_text[name_start:name_end])
            if spec is None:
                return None
            return _SyntaxReference(
                spec,
                _char_to_byte(source, authored_start),
                _char_to_byte(source, authored_end),
            )
        while index < limit and tag_text[index].isspace():
            index += 1
        if index >= limit or tag_text[index] != "=":
            continue
        index += 1
        while index < limit and tag_text[index].isspace():
            index += 1
        if index < limit and tag_text[index] in {'"', "'"}:
            value_end = _matching_quote(tag_text, index + 1, tag_text[index])
            if value_end is None:
                return None
            index = value_end + 1
            continue
        while (
            index < limit
            and not tag_text[index].isspace()
            and tag_text[index] not in {">", "<"}
            and not tag_text.startswith("{#", index)
        ):
            index += 1
    return None


def _syntax_markdown(spec: _SyntaxSpec) -> str:
    """Render one concise first-party hover with its canonical guide link."""
    subject = f"<{spec.label}>" if spec.kind == "tag" else spec.label
    return f"### `{subject}`\n\n{spec.documentation}\n\n[Read the Citry documentation]({spec.documentation_url})"


def _mapped_syntax_range(
    document: DocumentState,
    region: TemplateRegion,
    source: str,
    reference: _SyntaxReference,
) -> types.Range | None:
    """Map only a token whose authored host slice remains exactly contiguous."""
    mapped = _range(region.source_map.map_range(reference.start_index, reference.end_index))
    try:
        host_start = document_offset_at(document.source, _citry_position(mapped.start))
        host_end = document_offset_at(document.source, _citry_position(mapped.end))
        template_start = parser_char_index(source, reference.start_index)
        template_end = parser_char_index(source, reference.end_index)
    except ValueError:
        return None
    if document.source[host_start:host_end] != source[template_start:template_end]:
        return None
    return mapped


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
        spec = _STRUCTURAL_TAG_SPECS[name]
        if closing:
            new_text = name
            insert_text_format = types.InsertTextFormat.PlainText
        else:
            attribute = spec.primary_attribute
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
                detail=spec.detail,
                documentation=_markdown(_syntax_markdown(spec)),
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
        # Attribute records used for completion always define an insertion;
        # the label remains a safe fallback if the metadata is incomplete.
        new_text = spec.label if preserve_value else spec.insert_text or spec.label
        items.append(
            types.CompletionItem(
                label=spec.label,
                kind=types.CompletionItemKind.Keyword,
                detail=spec.detail,
                documentation=_markdown(_syntax_markdown(spec)),
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
    template_roots: tuple[_TemplateRoot, ...],
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
    for root in template_roots:
        key = _identifier_key(root.name)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            types.CompletionItem(
                label=root.name,
                kind=types.CompletionItemKind.Variable,
                detail=_template_root_detail(root),
                documentation=_markdown(_template_root_description(root)),
                filter_text=root.name,
                text_edit=types.InsertReplaceEdit(
                    new_text=root.name,
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


def _inside_fill_completion_value(before: str) -> bool:
    """Keep static fill-name/data completion ahead of template roots."""
    open_tag = _open_start_tag(before)
    if open_tag is None or open_tag[0] != "c-fill":
        return False
    tag_text = open_tag[1]
    return _inside_static_name_value(tag_text) or _slot_data_source_context(tag_text) is not None


def _unfinished_python_expression_context(source: str, cursor: int) -> tuple[str, int, bool] | None:
    """Return the active broken-buffer Python slice and its local cursor."""
    before = source[:cursor]
    open_tag = _open_start_tag(before)
    if open_tag is not None:
        _tag_name, tag_text = open_tag
        current_value = _unfinished_attribute_value(tag_text)
        if current_value is None:
            return None
        attr_name, value, _value_start = current_value
        if value.lstrip().startswith("<"):
            nested = _unfinished_template_expression_context(value)
            return None if nested is None else (*nested, False)
        if attr_name in {"#c-key", "cond", "each"}:
            return value, len(value), attr_name == "each"
        if attr_name.startswith("c-"):
            return value, len(value), attr_name == "c-for"
        return None
    expression = _unfinished_template_expression_context(before)
    return None if expression is None else (*expression, False)


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
) -> tuple[types.Range, types.Range] | None:
    """Map the current Python identifier to insertion and replacement ranges."""
    start = cursor
    while start > 0 and _python_identifier_continue(source[start - 1]):
        start -= 1
    end = cursor
    while end < len(source) and _python_identifier_continue(source[end]):
        end += 1
    insert_range = _mapped_template_range(region, source, start, cursor)
    replace_range = _mapped_template_range(region, source, start, end)
    if insert_range is None or replace_range is None:
        return None
    return insert_range, replace_range


def _mapped_template_range(
    region: TemplateRegion,
    source: str,
    start: int,
    end: int,
) -> types.Range | None:
    """Map only a template slice contained by one authored literal."""
    start_index = _char_to_byte(source, start)
    end_index = _char_to_byte(source, end)
    if not region.source_map.range_is_unambiguous(start_index, end_index):
        return None
    return _range(region.source_map.map_range(start_index, end_index))


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


def _root_completion_context(
    source: str,
    cursor: int,
    *,
    loop: bool = False,
    token_aware: bool = True,
) -> bool:
    """Reject roots in member access and non-code Python tokens."""
    if cursor < 0 or cursor > len(source):
        return False
    start = cursor
    while start > 0 and _python_identifier_continue(source[start - 1]):
        start -= 1
    if source[:start].rstrip().endswith("."):
        return False
    if not token_aware:
        return True
    framed = f"[\nNone for {source}\n]" if loop else source
    framed_cursor = cursor + len("[\nNone for ") if loop else cursor
    if _python_name_at(framed, framed_cursor):
        # Python 3.10 and 3.11 tokenize a complete f-string as one STRING.
        # The AST name proves the cursor is in its replacement expression.
        return True
    # Completion can be manually triggered inside a Python string or comment.
    # Token boundaries keep those characters from masquerading as root names.
    line_offsets = [0]
    for match in re.finditer(r"\n", source):
        line_offsets.append(match.end())
    blocked_types = {tokenize.STRING, tokenize.COMMENT, tokenize.NUMBER}
    fstring_middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    if isinstance(fstring_middle, int):
        blocked_types.add(fstring_middle)
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type == tokenize.ERRORTOKEN and token.string in {'"', "'"}:
                token_start = line_offsets[token.start[0] - 1] + token.start[1]
                if token_start <= cursor:
                    return False
                continue
            if token.type not in blocked_types:
                continue
            token_start = line_offsets[token.start[0] - 1] + token.start[1]
            token_end = line_offsets[token.end[0] - 1] + token.end[1]
            if token_start <= cursor <= token_end:
                return False
    except tokenize.TokenError as exc:
        message = str(exc.args[0]).lower() if exc.args else ""
        if "string literal" in message or "multi-line string" in message:
            return False
    except (IndentationError, SyntaxError):
        # Other malformed buffers still retain the lexical member guard.
        pass
    return True


def _python_name_at(source: str, cursor: int) -> bool:
    """Return whether a complete expression has a name at the cursor."""
    try:
        tree = ast.parse(source, mode="eval")
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return False
    lines = source.splitlines(keepends=True)
    line_offsets = [0]
    for line in lines[:-1]:
        line_offsets.append(line_offsets[-1] + len(line))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Name) or node.end_lineno is None or node.end_col_offset is None:
            continue
        start_line = lines[node.lineno - 1]
        end_line = lines[node.end_lineno - 1]
        start = line_offsets[node.lineno - 1] + _utf8_byte_column_to_char(start_line, node.col_offset)
        end = line_offsets[node.end_lineno - 1] + _utf8_byte_column_to_char(end_line, node.end_col_offset)
        if start <= cursor <= end:
            return True
    return False


def _python_identifier_continue(char: str) -> bool:
    """Recognize Unicode characters that can continue a Python identifier."""
    return char == "_" or char.isalnum() or f"a{char}".isidentifier()


def _has_unfinished_template_expression(source: str) -> bool:
    """Recognize an open interpolation in template, not static-attribute, text."""
    return _unfinished_template_expression_context(source) is not None


def _unfinished_template_expression_context(source: str) -> tuple[str, int] | None:
    """Return the source of one active interpolation at the end of a template."""
    index = 0
    while index < len(source):
        next_marker = _next_template_marker(source, index)
        if next_marker is None:
            return None
        marker, start = next_marker
        if marker == "{#":
            end = source.find("#}", start + 2)
            if end < 0:
                return None
            index = end + 2
        elif marker == "{{":
            expression_end = _template_expression_end(source, start)
            if expression_end is None:
                expression = source[start + 2 :]
                return expression, len(expression)
            index = expression_end
        elif source.startswith("<!--", start):
            end = source.find("-->", start + 4)
            if end < 0:
                return None
            index = end + 3
        else:
            tag_end = _tag_end(source, start)
            if tag_end is None:
                return None
            tag_text = source[start : tag_end + 1]
            tag_match = re.match(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)", tag_text)
            fragment = re.match(r"<\s*/?\s*>", tag_text)
            if tag_match is None and fragment is None:
                index = start + 1
                continue
            nested = _tag_unfinished_nested_expression_context(tag_text)
            if nested is not None:
                return nested
            if tag_match is None or tag_match.group(1) or tag_match.group(2) != "c-raw":
                index = tag_end + 1
                continue
            raw_end = _raw_end_start(source, tag_end + 1, "c-raw")
            if raw_end is None:
                return None
            close_end = _tag_end(source, raw_end)
            if close_end is None:
                return None
            index = close_end + 1
    return None


def _tag_has_unfinished_nested_expression(tag_text: str) -> bool:
    """Inspect only template-valued dynamic attributes inside a complete tag."""
    return _tag_unfinished_nested_expression_context(tag_text) is not None


def _tag_unfinished_nested_expression_context(tag_text: str) -> tuple[str, int] | None:
    """Return an active interpolation inside one template-valued attribute."""
    pattern = re.compile(r"(?:^|\s)c-[\w$-]+\s*=\s*(['\"])(.*?)\1", re.DOTALL)
    for value in (match.group(2) for match in pattern.finditer(tag_text)):
        if not value.lstrip().startswith("<"):
            continue
        context = _unfinished_template_expression_context(value)
        if context is not None:
            return context
    return None


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


def _browser_binding_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[TemplateRegion, BrowserBinding, JsonWireType, int, int] | None:
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    parsed = document.parsed.get(region.key)
    if parser_index is None or parsed is None:
        return None
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    binding = next(
        (
            candidate
            for candidate in browser_bindings(parsed.template, parse_nested=parser)
            if candidate.start_index <= parser_index <= candidate.end_index
        ),
        None,
    )
    use_start = binding.start_index if binding is not None else 0
    use_end = binding.end_index if binding is not None else 0
    if binding is None:
        expression = browser_expression_at(parsed.template, parser_index, parse_nested=parser)
        if expression is None:
            return None
        identifier = browser_identifier_at(expression, parser_index)
        if identifier is None:
            return None
        use_start = identifier.start_index
        use_end = identifier.end_index
        binding = next(
            (candidate for candidate in reversed(expression.binding_details) if candidate.name == identifier.name),
            None,
        )
    if binding is None:
        return None
    roots = _template_js_data_roots(document, region, project, open_documents)
    return region, binding, _browser_binding_wire_type(binding, roots), use_start, use_end


def _browser_binding_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Hover | None:
    resolved = _browser_binding_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, binding, wire_type, use_start, use_end = resolved
    return types.Hover(
        types.MarkupContent(
            types.MarkupKind.Markdown,
            "\n".join(
                (
                    "```javascript",
                    f"(variable) {binding.name}: {wire_type.javascript}",
                    "```",
                    "",
                    "Alpine `x-for` binding" if binding.kind == "x-for" else "Alpine `x-data` binding",
                )
            ),
        ),
        range=_range(region.source_map.map_range(use_start, use_end)),
    )


def _browser_binding_origin_location(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Location | None:
    resolved = _browser_binding_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, binding, _wire_type, _use_start, _use_end = resolved
    return types.Location(
        document.uri,
        _range(region.source_map.map_range(binding.start_index, binding.end_index)),
    )


def _browser_binding_reference_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
    *,
    include_declaration: bool,
) -> list[types.Location] | None:
    resolved = _browser_binding_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, selected, _wire_type, _use_start, _use_end = resolved
    parsed = document.parsed.get(region.key)
    if parsed is None:
        return None
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    found: list[types.Location] = []
    for expression in browser_expressions(parsed.template, parse_nested=parser):
        for identifier in browser_identifiers(expression):
            binding = next(
                (candidate for candidate in reversed(expression.binding_details) if candidate.name == identifier.name),
                None,
            )
            if binding is None or (binding.start_index, binding.end_index) != (
                selected.start_index,
                selected.end_index,
            ):
                continue
            found.append(
                types.Location(
                    document.uri,
                    _range(region.source_map.map_range(identifier.start_index, identifier.end_index)),
                )
            )
    if include_declaration:
        found.append(
            types.Location(
                document.uri,
                _range(region.source_map.map_range(selected.start_index, selected.end_index)),
            )
        )
    return list(_sorted_locations(found))


def _browser_data_completion_result(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> CompletionResult | None:
    """Complete JsData roots in parser-proven Alpine expression hosts."""
    context = _browser_expression_context(document, position, project)
    if context is None:
        return None
    region, expression, parser_index = context
    completion = browser_completion_at(expression, parser_index)
    if completion is None:
        return CompletionResult((), is_incomplete=True)
    roots = _template_js_data_roots(document, region, project, open_documents)
    edit_range = _range(region.source_map.map_range(completion.start_index, completion.end_index))
    return CompletionResult(
        tuple(
            types.CompletionItem(
                label=root.name,
                kind=types.CompletionItemKind.Variable,
                detail=_js_data_root_detail(root),
                documentation=_markdown(_js_data_root_documentation(root)),
                filter_text=root.name,
                text_edit=types.TextEdit(edit_range, root.name),
            )
            for root in roots
            if root.name.startswith(completion.prefix) and root.name not in expression.bindings
        ),
        is_incomplete=True,
    )


def _browser_data_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Hover | None:
    resolved = _browser_data_root_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, root, identifier = resolved
    lines = ["```javascript", f"(variable) {root.name}: {root.wire_type.javascript}", "```", "", "Citry JsData"]
    for producer in sorted(root.producers, key=lambda item: item.origin):
        lines.append(f"- `{producer.origin}`")
        if producer.description:
            lines.append(f"  {producer.description}")
    if root.presence == "conditional":
        lines.extend(("", "This key is returned only on some proven `js_data()` paths."))
    return types.Hover(
        types.MarkupContent(types.MarkupKind.Markdown, "\n".join(lines)),
        range=_range(region.source_map.map_range(identifier.start_index, identifier.end_index)),
    )


def _browser_data_reference_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
    *,
    include_declaration: bool,
) -> list[types.Location] | None:
    resolved = _browser_data_root_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, root, _identifier = resolved
    parsed = document.parsed.get(region.key)
    if parsed is None:
        return None
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    found: list[types.Location] = []
    for expression in browser_expressions(parsed.template, parse_nested=parser):
        for identifier in browser_identifiers(expression):
            if identifier.root and identifier.name == root.name:
                found.append(
                    types.Location(
                        document.uri,
                        _range(region.source_map.map_range(identifier.start_index, identifier.end_index)),
                    )
                )
    if include_declaration:
        found.extend(_js_data_root_locations(root, open_documents))
    return list(_sorted_locations(found))


def _browser_data_origin_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    resolved = _browser_data_root_at(document, position, project, open_documents)
    return _js_data_root_locations(resolved[1], open_documents) if resolved is not None else ()


def _browser_expression_context(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
) -> tuple[TemplateRegion, BrowserExpression, int] | None:
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    parsed = document.parsed.get(region.key)
    if parsed is None:
        return None
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    expression = browser_expression_at(parsed.template, parser_index, parse_nested=parser)
    return (region, expression, parser_index) if expression is not None else None


def _browser_data_root_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[TemplateRegion, _JsDataRoot, Any] | None:
    context = _browser_expression_context(document, position, project)
    if context is None:
        return None
    region, expression, parser_index = context
    identifier = browser_identifier_at(expression, parser_index)
    if identifier is None or not identifier.root:
        return None
    root = next(
        (
            candidate
            for candidate in _template_js_data_roots(document, region, project, open_documents)
            if candidate.name == identifier.name
        ),
        None,
    )
    return (region, root, identifier) if root is not None else None


def _template_js_data_roots(
    document: DocumentState,
    region: TemplateRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_JsDataRoot, ...]:
    consumers = _template_consumers(document, region, project, open_documents)
    if not consumers:
        return ()
    resolved: list[tuple[_JsDataRoot, ...] | None] = []
    for component in consumers:
        data_roots = _component_js_data_roots(component, project, document, open_documents)
        scope_roots = _component_scope_roots(component, project, document, open_documents)
        if data_roots is None or scope_roots is None:
            resolved.append(None)
            continue
        by_name = {root.name: root for root in data_roots}
        for scope_root in scope_roots:
            existing = by_name.get(scope_root.name)
            by_name[scope_root.name] = (
                scope_root
                if existing is None
                else _JsDataRoot(
                    scope_root.name,
                    scope_root.presence,
                    merge_json_wire_types((existing.wire_type, scope_root.wire_type)),
                    tuple(dict.fromkeys((*existing.producers, *scope_root.producers))),
                    _dedupe_fields((*existing.fields, *scope_root.fields)),
                    _dedupe_locations((*existing.locations, *scope_root.locations)),
                )
            )
        resolved.append(tuple(by_name.values()))
    if any(roots is None for roots in resolved):
        return ()
    root_sets = [roots for roots in resolved if roots is not None]
    if not root_sets:
        return ()
    common = {root.name: root for root in root_sets[0]}
    if len(common) != len(root_sets[0]):
        return ()
    for roots in root_sets[1:]:
        candidates = {root.name: root for root in roots}
        if len(candidates) != len(roots):
            return ()
        joined: dict[str, _JsDataRoot] = {}
        for name, root in common.items():
            candidate = candidates.get(name)
            if candidate is None:
                continue
            joined[name] = _JsDataRoot(
                name,
                "conditional" if root.presence == "conditional" or candidate.presence == "conditional" else "always",
                merge_json_wire_types((root.wire_type, candidate.wire_type)),
                tuple(dict.fromkeys((*root.producers, *candidate.producers))),
                _dedupe_fields((*root.fields, *candidate.fields)),
                _dedupe_locations((*root.locations, *candidate.locations)),
            )
        common = joined
    return tuple(common.values())


def _component_scope_roots(
    component: ComponentRecord,
    project: ProjectState,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_JsDataRoot, ...] | None:
    """Resolve exact synchronous `$component` scope writes for one owner."""
    resolved = _component_js_asset_source(component, project, current_document, open_documents)
    if resolved is None:
        return None
    if resolved is False:
        return ()
    source, uri, source_map = resolved
    data_roots = _component_js_data_roots(component, project, current_document, open_documents)
    if data_roots is None:
        return None
    data_by_name = {root.name: root for root in data_roots}
    grouped: dict[str, list[Any]] = {}
    for write in browser_component_scope_writes(source):
        grouped.setdefault(write.name, []).append(write)
    roots: list[_JsDataRoot] = []
    owner_name = component.qualname or component.class_name or component.name
    for name, writes in grouped.items():
        wire_types = tuple(_scope_write_wire_type(write.value_source, data_by_name) for write in writes)
        wire_type = merge_json_wire_types(wire_types)
        locations = tuple(
            types.Location(uri, _range(source_map.map_range(write.start_index, write.end_index))) for write in writes
        )
        roots.append(
            _JsDataRoot(
                name,
                "conditional",
                wire_type,
                (_JsDataProducer(f"{owner_name}.$component scope.{name}", wire_type),),
                locations=locations,
            )
        )
    return tuple(roots)


def _component_js_asset_source(
    component: ComponentRecord,
    project: ProjectState,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[str, str, Any] | Literal[False] | None:
    """Return one current JS asset and exact source map, absent, or unproven."""
    asset = component.assets.js
    if asset.kind == "none":
        return False
    if not _js_consumer_is_current(component, project, open_documents):
        return None
    if asset.resolved_path is not None:
        source_file = asset.resolved_path.resolve()
        documents = dict(open_documents or {})
        documents[current_document.uri] = current_document
        found, source = _synchronized_document_source(source_file, documents)
        if not found:
            try:
                source = source_file.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                return None
        if source is None:
            return None
        return source, source_file.as_uri(), standalone_js_region(source).source_map
    if asset.owner_file is None or asset.owner_qualname is None or "<locals>" in asset.owner_qualname:
        return None
    source = _python_source(asset.owner_file, current_document, open_documents)
    if source is None:
        return None
    owner_name = asset.owner_qualname.rsplit(".", 1)[-1]
    matches = [region for region in discover_python_js_regions(source) if region.component_name == owner_name]
    if len(matches) != 1:
        return None
    source_map = matches[0].source_map
    return source_map.template_source, asset.owner_file.resolve().as_uri(), source_map


def _component_client_props(
    component: ComponentRecord,
    project: ProjectState,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_ClientProp, ...] | None:
    """Resolve a child's static prop contract from its current JavaScript."""
    resolved = _component_js_asset_source(component, project, current_document, open_documents)
    if resolved is None or resolved is False:
        return None
    source, uri, source_map = resolved
    props = browser_component_props(source)
    if props is None:
        return None
    return tuple(
        _ClientProp(
            prop.name,
            prop.javascript,
            prop.required,
            types.Location(uri, _range(source_map.map_range(prop.start_index, prop.end_index))),
        )
        for prop in props
    )


def _browser_component_prop_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[TemplateRegion, BrowserObjectProperty, _ClientProp] | None:
    """Join one authored `$c-props` key to its current child declaration."""
    if project.catalog is None:
        return None
    region = document.region_at(position)
    if region is None:
        return None
    parsed = document.parsed.get(region.key)
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parsed is None or parser_index is None:
        return None
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    for use in browser_component_prop_uses(parsed.template, parse_nested=parser):
        property_ = next(
            (
                candidate
                for candidate in use.properties
                if candidate.start_index <= parser_index <= candidate.end_index
            ),
            None,
        )
        if property_ is None:
            continue
        child = project.catalog.get_tag(use.tag_name)
        if child is None:
            return None
        contract = _component_client_props(child, project, document, open_documents)
        if contract is None:
            return None
        prop = next((candidate for candidate in contract if candidate.name == property_.name), None)
        return (region, property_, prop) if prop is not None else None
    return None


def _browser_component_prop_origin(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Location | None:
    resolved = _browser_component_prop_at(document, position, project, open_documents)
    return resolved[2].location if resolved is not None else None


def _browser_component_prop_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Hover | None:
    resolved = _browser_component_prop_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, property_, prop = resolved
    return types.Hover(
        types.MarkupContent(
            types.MarkupKind.Markdown,
            "\n".join(
                (
                    "```javascript",
                    f"(property) {prop.name}: {prop.javascript}",
                    "```",
                    "",
                    "Client prop declared by the child component",
                )
            ),
        ),
        range=_range(region.source_map.map_range(property_.start_index, property_.end_index)),
    )


def _component_props_diagnostics(
    region: TemplateRegion,
    use: BrowserComponentPropsUse,
    contract: tuple[_ClientProp, ...],
    roots: tuple[_JsDataRoot, ...],
    expressions: tuple[BrowserExpression, ...],
) -> tuple[types.Diagnostic, ...]:
    """Check direct keys while dynamic keys suppress only missing-prop errors."""
    by_name = {prop.name: prop for prop in contract}
    explicit = {prop.name for prop in use.properties}
    diagnostics: list[types.Diagnostic] = []
    for property_ in use.properties:
        expected = by_name.get(property_.name)
        if expected is None:
            diagnostics.append(
                _browser_diagnostic(
                    region,
                    property_.start_index,
                    property_.end_index,
                    BROWSER_UNKNOWN_COMPONENT_PROP,
                    name=property_.name,
                    tag=use.tag_name,
                )
            )
            continue
        actual = _browser_prop_value_type(property_, roots, expressions)
        if actual.kind != "unknown" and not browser_client_prop_accepts(expected.javascript, actual):
            diagnostics.append(
                _browser_diagnostic(
                    region,
                    property_.value_start_index,
                    property_.value_end_index,
                    BROWSER_INCOMPATIBLE_COMPONENT_PROP,
                    name=property_.name,
                    expected=expected.javascript,
                    actual=actual.javascript,
                )
            )
    if not use.has_dynamic_keys:
        for prop in contract:
            if prop.required and prop.name not in explicit:
                diagnostics.append(
                    _browser_diagnostic(
                        region,
                        use.start_index,
                        use.end_index,
                        BROWSER_MISSING_COMPONENT_PROP,
                        name=prop.name,
                        tag=use.tag_name,
                    )
                )
    return tuple(diagnostics)


def _browser_prop_value_type(
    property_: BrowserObjectProperty,
    roots: tuple[_JsDataRoot, ...],
    expressions: tuple[BrowserExpression, ...],
) -> JsonWireType:
    """Infer direct literals, proven roots, and active Alpine loop bindings."""
    source = property_.value_source.strip()
    if re.fullmatch(r"[A-Za-z_$][\w$]*", source):
        root = next((candidate for candidate in roots if candidate.name == source), None)
        if root is not None:
            return root.wire_type
        expression = next(
            (
                candidate
                for candidate in expressions
                if candidate.start_index <= property_.value_start_index
                and property_.value_end_index <= candidate.end_index
            ),
            None,
        )
        if expression is not None:
            binding = next(
                (candidate for candidate in reversed(expression.binding_details) if candidate.name == source),
                None,
            )
            if binding is not None:
                return _browser_binding_wire_type(binding, roots)
    return browser_literal_wire_type(source)


def _browser_diagnostic(
    region: TemplateRegion,
    start_index: int,
    end_index: int,
    code: str,
    **parameters: str,
) -> types.Diagnostic:
    """Render one catalog-backed browser diagnostic at template coordinates."""
    return types.Diagnostic(
        range=_range(region.source_map.map_range(start_index, end_index)),
        message=render_diagnostic(code, **parameters),
        severity=types.DiagnosticSeverity.Error,
        code=code,
        code_description=types.CodeDescription(diagnostic_documentation_url(code)),
        source="citry",
    )


def _scope_write_wire_type(
    value_source: str,
    data_roots: Mapping[str, _JsDataRoot],
) -> JsonWireType:
    """Infer only literal and direct JsData-backed scope assignment types."""
    value = value_source.strip()
    data_member = re.fullmatch(r"data\.([A-Za-z_$][\w$]*)", value)
    if data_member is not None and (root := data_roots.get(data_member.group(1))) is not None:
        return root.wire_type
    if value in {"true", "false"}:
        return JsonWireType("boolean")
    if value == "null":
        return JsonWireType("null")
    if re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value):
        return JsonWireType("number")
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return JsonWireType("string")
    if value.startswith("[") and value.endswith("]"):
        return JsonWireType("array", (JsonWireType("unknown"),))
    if value.startswith("{") and value.endswith("}"):
        return JsonWireType("object", additional=JsonWireType("unknown"))
    return JsonWireType("unknown")


def _browser_binding_wire_type(
    binding: BrowserBinding,
    roots: tuple[_JsDataRoot, ...],
) -> JsonWireType:
    """Infer Alpine x-for positional values from one exact iterable root."""
    if binding.kind != "x-for":
        return JsonWireType("unknown")
    source = binding.source.strip()
    root = next((candidate for candidate in roots if candidate.name == source), None)
    return _iterated_wire_type(root.wire_type, binding.position) if root is not None else JsonWireType("unknown")


def _iterated_wire_type(wire_type: JsonWireType, position: int) -> JsonWireType:
    if wire_type.kind == "union":
        return merge_json_wire_types(tuple(_iterated_wire_type(item, position) for item in wire_type.items))
    if wire_type.kind == "array":
        if position == 0:
            return merge_json_wire_types(wire_type.items)
        return JsonWireType("number") if position in {1, 2} else JsonWireType("unknown")
    if wire_type.kind == "object":
        if position == 0:
            values = tuple(field.value for field in wire_type.fields)
            if wire_type.additional is not None:
                values = (*values, wire_type.additional)
            return merge_json_wire_types(values)
        if position == 1:
            return JsonWireType("string")
        return JsonWireType("number") if position == 2 else JsonWireType("unknown")
    if wire_type.kind == "string" and position == 0:
        return JsonWireType("string")
    return JsonWireType("unknown")


def _component_js_data_roots(
    component: ComponentRecord,
    project: ProjectState,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_JsDataRoot, ...] | None:
    schema = component.schemas.js_data
    owner_name = component.qualname or component.class_name or component.name
    if schema.kind == "opaque":
        return ()
    if schema.kind == "fields":
        return _js_schema_roots(component, owner_name, open_documents)
    if project.source_analysis is None:
        return None
    chain = project.source_analysis.js_data_chain(component)
    if not chain:
        return None
    for candidate in chain[:-1]:
        source = _python_source(candidate.source_file, current_document, open_documents)
        if source is None or python_class_resolution_signature(source, candidate.qualname) != candidate.resolution:
            return None
        if python_class_defines_direct_method(source, candidate.qualname, "js_data") is not False:
            return None
    owner = chain[-1]
    source = _python_source(owner.source_file, current_document, open_documents)
    if source is None or python_class_resolution_signature(source, owner.qualname) != owner.resolution:
        return None
    shape = analyze_js_data_source(source, owner.qualname)
    if shape is None:
        return None
    member_types = _js_data_member_types(component, shape)
    roots: list[_JsDataRoot] = []
    for root in shape.roots:
        value_types = tuple(
            json_wire_type_from_expression(value_source, member_types=member_types)
            for definition in root.definitions
            if (value_source := _source_range_text(source, definition.value_range)) is not None
        )
        wire_type = merge_json_wire_types(value_types)
        roots.append(
            _JsDataRoot(
                root.name,
                root.presence,
                wire_type,
                (_JsDataProducer(f"{owner_name}.js_data()", wire_type),),
                locations=tuple(
                    types.Location(owner.source_file.resolve().as_uri(), _range(definition.key_range))
                    for definition in root.definitions
                ),
            )
        )
    return tuple(roots)


def _js_data_member_types(
    component: ComponentRecord,
    shape: TemplateDataSourceShape,
) -> dict[str, dict[str, JsonWireType]]:
    """Join the effective Kwargs schema to the js_data() kwargs parameter."""
    if len(shape.parameters) < 2 or component.schemas.kwargs.kind != "fields":
        return {}
    return {
        shape.parameters[1]: {
            field.name: (
                json_wire_type_from_annotation(field.type_display)
                if field.type_display is not None
                else JsonWireType("unknown")
            )
            for field in component.schemas.kwargs.fields
        }
    }


def _js_schema_roots(
    component: ComponentRecord,
    owner_name: str,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_JsDataRoot, ...] | None:
    schema = component.schemas.js_data
    grouped: dict[tuple[Path, str], list[FieldRecord]] = {}
    detached: list[FieldRecord] = []
    for schema_field in schema.fields:
        if schema_field.source_file is None or schema_field.source_qualname is None:
            detached.append(schema_field)
            continue
        grouped.setdefault((schema_field.source_file.resolve(), schema_field.source_qualname), []).append(schema_field)
    if component.python_file is not None and component.qualname is not None:
        grouped.setdefault((component.python_file.resolve(), f"{component.qualname}.JsData"), [])

    roots = [_catalog_js_data_root(schema_field, owner_name) for schema_field in detached]
    for (source_file, qualname), catalog_fields in grouped.items():
        found, source = (
            _synchronized_document_source(source_file, open_documents) if open_documents is not None else (False, None)
        )
        if not found:
            roots.extend(_catalog_js_data_root(schema_field, owner_name) for schema_field in catalog_fields)
            continue
        if source is None:
            return None
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
            return None
        schema_class = _class_node_for_qualname(tree, qualname)
        if schema_class is None:
            if catalog_fields:
                return None
            continue
        by_name = {schema_field.name: schema_field for schema_field in catalog_fields}
        direct_names = _direct_schema_field_names(schema_class)
        for statement in schema_class.body:
            if not isinstance(statement, ast.AnnAssign) or not isinstance(statement.target, ast.Name):
                continue
            if statement.target.id not in direct_names:
                continue
            token = _annotated_field_token(source, schema_class, statement.target.id)
            if token is None:
                return None
            line, start, end = token
            source_line = source.splitlines()[line]
            location = types.Location(
                source_file.as_uri(),
                types.Range(
                    types.Position(line, _utf16_units(source_line[:start])),
                    types.Position(line, _utf16_units(source_line[:end])),
                ),
            )
            current_field = by_name.get(statement.target.id)
            annotation = _css_data_annotation(statement.annotation)
            wire_type = json_wire_type_from_annotation(ast.unparse(annotation))
            roots.append(
                _JsDataRoot(
                    statement.target.id,
                    "always",
                    wire_type,
                    (
                        _JsDataProducer(
                            f"{qualname}.{statement.target.id}",
                            wire_type,
                            current_field.description if current_field is not None else None,
                        ),
                    ),
                    fields=(current_field,) if current_field is not None else (),
                    locations=(location,) if current_field is None else (),
                )
            )
    return tuple(roots)


def _catalog_js_data_root(schema_field: FieldRecord, owner_name: str) -> _JsDataRoot:
    wire_type = (
        json_wire_type_from_annotation(schema_field.type_display)
        if schema_field.type_display is not None
        else JsonWireType("unknown")
    )
    return _JsDataRoot(
        schema_field.name,
        "always",
        wire_type,
        (
            _JsDataProducer(
                f"{owner_name}.JsData.{schema_field.name}",
                wire_type,
                schema_field.description,
            ),
        ),
        fields=(schema_field,),
    )


def _js_data_root_locations(
    root: _JsDataRoot,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    locations = list(root.locations)
    for schema_field in root.fields:
        source = (
            _open_document_source(schema_field.source_file, open_documents)
            if schema_field.source_file and open_documents
            else None
        )
        location = _field_definition_location(schema_field, source=source)
        if location is None:
            return ()
        locations.append(location)
    return _sorted_locations(locations)


def _js_data_root_detail(root: _JsDataRoot) -> str:
    conditional = " · conditional" if root.presence == "conditional" else ""
    return f"Citry JsData · {root.wire_type.display}{conditional}"


def _js_data_root_documentation(root: _JsDataRoot) -> str:
    lines = ["Python producers:"]
    for producer in sorted(root.producers, key=lambda item: item.origin):
        lines.append(f"- `{producer.origin}` → `{producer.wire_type.display}`")
        if producer.description:
            lines.append(f"  {producer.description}")
    return "\n".join(lines)


def _source_range_text(source: str, value_range: LspRange | None) -> str | None:
    if value_range is None:
        return None
    start = _source_offset_at_position(
        source,
        types.Position(value_range.start.line, value_range.start.character),
    )
    end = _source_offset_at_position(
        source,
        types.Position(value_range.end.line, value_range.end.character),
    )
    return source[start:end] if start is not None and end is not None and start <= end else None


def _js_consumers(
    document: DocumentState,
    region: JsRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[ComponentRecord, ...]:
    catalog = project.catalog
    if catalog is None:
        return ()
    if document.language_id == "python":
        if not region.ast_proven or region.component_name is None:
            return ()
        owners = catalog.inline_asset_consumers(document.uri, "js", region.component_name)
    elif document.language_id == "javascript":
        owners = catalog.asset_owners(document.uri, "js")
    else:
        return ()
    return tuple(owner for owner in owners if _js_consumer_is_current(owner, project, open_documents))


def _js_consumer_is_current(
    component: ComponentRecord,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> bool:
    if open_documents is None or project.source_analysis is None:
        return True
    chain = project.source_analysis.js_asset_chain(component)
    if chain is None:
        return not any(document.language_id == "python" for document in open_documents.values())
    for candidate in chain:
        found, source = _synchronized_document_source(candidate.source_file, open_documents)
        if found and (
            source is None
            or python_class_asset_resolution_signature(source, candidate.qualname, "js") != candidate.resolution
        ):
            return False
    return True


def _js_asset_data_roots(
    document: DocumentState,
    region: JsRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_JsDataRoot, ...] | None:
    consumers = _js_consumers(document, region, project, open_documents)
    if not consumers:
        return None
    resolved = [_component_js_data_roots(component, project, document, open_documents) for component in consumers]
    if any(roots is None for roots in resolved):
        return None
    root_sets = [roots for roots in resolved if roots is not None]
    if not root_sets:
        return ()
    common = {root.name: root for root in root_sets[0]}
    for roots in root_sets[1:]:
        candidates = {root.name: root for root in roots}
        common = {
            name: _JsDataRoot(
                name,
                (
                    "conditional"
                    if root.presence == "conditional" or candidates[name].presence == "conditional"
                    else "always"
                ),
                merge_json_wire_types((root.wire_type, candidates[name].wire_type)),
                tuple(dict.fromkeys((*root.producers, *candidates[name].producers))),
                _dedupe_fields((*root.fields, *candidates[name].fields)),
                _dedupe_locations((*root.locations, *candidates[name].locations)),
            )
            for name, root in common.items()
            if name in candidates
        }
    return tuple(common.values())


def _js_asset_scope_roots(
    document: DocumentState,
    region: JsRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_JsDataRoot, ...] | None:
    consumers = _js_consumers(document, region, project, open_documents)
    if not consumers:
        return None
    resolved: list[tuple[_JsDataRoot, ...]] = []
    for component in consumers:
        data_roots = _component_js_data_roots(component, project, document, open_documents)
        scope_roots = _component_scope_roots(component, project, document, open_documents)
        if data_roots is None or scope_roots is None:
            return None
        by_name = {root.name: root for root in data_roots}
        for scope_root in scope_roots:
            by_name[scope_root.name] = scope_root
        resolved.append(tuple(by_name.values()))
    common = {root.name: root for root in resolved[0]}
    for roots in resolved[1:]:
        candidates = {root.name: root for root in roots}
        common = {
            name: _JsDataRoot(
                name,
                "conditional"
                if root.presence == "conditional" or candidates[name].presence == "conditional"
                else "always",
                merge_json_wire_types((root.wire_type, candidates[name].wire_type)),
                tuple(dict.fromkeys((*root.producers, *candidates[name].producers))),
                _dedupe_fields((*root.fields, *candidates[name].fields)),
                _dedupe_locations((*root.locations, *candidates[name].locations)),
            )
            for name, root in common.items()
            if name in candidates
        }
    return tuple(common.values())


@dataclass(frozen=True, slots=True)
class _BrowserApiSpec:
    """Describe one Citry browser API in hover-friendly JavaScript terms."""

    kind: str
    type_display: str
    description: str
    documentation_url: str


_BROWSER_APIS_URL = "https://citry.dev/reference/browser-apis/"
_ALPINE_API_SPECS = {
    "$state": _BrowserApiSpec(
        "magic",
        "CitryEventsState",
        "Read or update this component's public Events state.",
        f"{_BROWSER_APIS_URL}#state",
    ),
    "$loading": _BrowserApiSpec(
        "function",
        "(name?: CitryServerEventName) => boolean",
        "Check whether any server handler, or one named handler, is running.",
        f"{_BROWSER_APIS_URL}#loading",
    ),
    "$error": _BrowserApiSpec(
        "function",
        "(name?: CitryServerEventName) => CitryEventError | null",
        "Read the latest retained server-handler error.",
        f"{_BROWSER_APIS_URL}#error",
    ),
    "$sendEvent": _BrowserApiSpec(
        "function",
        "(name: CitryServerEventName, args?: Record<string, unknown>, opts?: unknown) => Promise<unknown>",
        "Call one of this component's declared server event handlers.",
        f"{_BROWSER_APIS_URL}#send-event",
    ),
    "$onEvent": _BrowserApiSpec(
        "function",
        "(name: string, callback: (detail: unknown) => void) => CitryCleanup",
        "Listen for a browser event targeting this component instance.",
        f"{_BROWSER_APIS_URL}#on-event",
    ),
    "$provide": _BrowserApiSpec(
        "function",
        "(key: string | symbol, value: unknown) => void",
        "Provide a client value to rendered descendants.",
        f"{_BROWSER_APIS_URL}#provide",
    ),
    "$inject": _BrowserApiSpec(
        "function",
        "(key: string | symbol, fallback?: unknown) => unknown",
        "Read the nearest inherited client value.",
        f"{_BROWSER_APIS_URL}#inject",
    ),
    "$unprovide": _BrowserApiSpec(
        "function",
        "(key: string | symbol) => void",
        "Hide an inherited client value for this subtree.",
        f"{_BROWSER_APIS_URL}#unprovide",
    ),
}
_COMPONENT_API_SPECS = {
    "$component": _BrowserApiSpec(
        "function",
        "(definition: CitryComponentInitializer | CitryComponentDefinition) => void",
        "Initialize each rendered instance of this component.",
        f"{_BROWSER_APIS_URL}#component",
    ),
}
_COMPONENT_CONTEXT_SPECS = {
    "id": _BrowserApiSpec("parameter", "string", "The current server render ID.", f"{_BROWSER_APIS_URL}#component"),
    "els": _BrowserApiSpec(
        "parameter",
        "Element[]",
        "The stable array of this instance's current root elements.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "data": _BrowserApiSpec(
        "parameter",
        "CitryJsData",
        "The instance-local JSON returned by `js_data()`.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "graph": _BrowserApiSpec(
        "parameter",
        "unknown",
        "Current ownership route and source metadata, when available.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "props": _BrowserApiSpec(
        "parameter",
        "Readonly<CitryClientProps>",
        "Stable reactive values declared by the `$component` configuration.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "scope": _BrowserApiSpec(
        "parameter",
        "CitryJsData & Record<string, unknown>",
        "The stable reactive object visible to this component's Alpine expressions.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "state": _BrowserApiSpec(
        "parameter",
        "CitryEventsState | null",
        "This component's public reactive Events state.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "effect": _BrowserApiSpec(
        "function",
        "(fn: () => void) => CitryCleanup",
        "Run a managed reactive effect for this component instance.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "reactive": _BrowserApiSpec(
        "function",
        "<T>(value: T) => T",
        "Create an Alpine reactive proxy.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "provide": _BrowserApiSpec(
        "function",
        "(key: string | symbol, value: unknown) => void",
        "Provide a client value to rendered descendants.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "inject": _BrowserApiSpec(
        "function",
        "(key: string | symbol, fallback?: unknown) => unknown",
        "Read the nearest inherited client value.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "unprovide": _BrowserApiSpec(
        "function",
        "(key: string | symbol) => void",
        "Hide an inherited client value for rendered descendants.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "sendEvent": _BrowserApiSpec(
        "function",
        "(name: CitryServerEventName, args?: Record<string, unknown>, opts?: unknown) => Promise<unknown>",
        "Call one of this component's declared server event handlers.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "onEvent": _BrowserApiSpec(
        "function",
        "(name: string, callback: (detail: unknown) => void) => CitryCleanup",
        "Listen for a browser event targeting this component instance.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "loading": _BrowserApiSpec(
        "function",
        "(name?: CitryServerEventName) => boolean",
        "Check whether any server handler, or one named handler, is running.",
        f"{_BROWSER_APIS_URL}#component",
    ),
    "error": _BrowserApiSpec(
        "function",
        "(name?: CitryServerEventName) => CitryEventError | null",
        "Read the latest retained server-handler error.",
        f"{_BROWSER_APIS_URL}#component",
    ),
}


def _browser_api_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
) -> types.Hover | None:
    """Describe one exact Citry magic or `$component` context binding."""
    resolved = _browser_api_at(document, position, project)
    if resolved is None:
        return None
    region, label, spec, start, end = resolved
    return types.Hover(
        types.MarkupContent(
            types.MarkupKind.Markdown,
            "\n".join(
                (
                    "```javascript",
                    f"({spec.kind}) {label}: {spec.type_display}",
                    "```",
                    "",
                    spec.description,
                    "",
                    f"[Read the Citry documentation]({spec.documentation_url})",
                )
            ),
        ),
        range=_range(region.source_map.map_range(start, end)),
    )


def _browser_api_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
) -> tuple[TemplateRegion | JsRegion, str, _BrowserApiSpec, int, int] | None:
    template_context = _browser_expression_context(document, position, project)
    if template_context is not None:
        region, expression, parser_index = template_context
        identifier = browser_identifier_at(expression, parser_index)
        if identifier is None or not identifier.root:
            return None
        spec = _ALPINE_API_SPECS.get(identifier.name)
        if spec is None:
            return None
        return region, identifier.name, spec, identifier.start_index, identifier.end_index

    js_region = document.js_region_at(position)
    if js_region is None:
        return None
    js_parser_index = js_region.source_map.parser_index_at(_citry_position(position))
    if js_parser_index is None:
        return None
    source = js_region.source_map.template_source
    expression = _component_js_expression(js_region)
    identifier = browser_identifier_at(expression, js_parser_index)
    if identifier is not None and identifier.root:
        spec = _COMPONENT_API_SPECS.get(identifier.name)
        if spec is not None:
            return js_region, identifier.name, spec, identifier.start_index, identifier.end_index
    analysis = analyze_browser_component_source(source)
    if not analysis.valid:
        return None
    for binding in analysis.bindings:
        spec = _COMPONENT_CONTEXT_SPECS.get(binding.name)
        if spec is None:
            continue
        for start, end in ((binding.start_index, binding.end_index), *binding.references):
            if start <= js_parser_index <= end:
                return js_region, binding.local_name, spec, start, end
    return None


def _browser_preamble(
    roots: tuple[_JsDataRoot, ...],
    bindings: tuple[str, ...],
    props: tuple[Any, ...] | None,
    event_names: tuple[str, ...],
    state_roots: tuple[_JsDataRoot, ...] = (),
    *,
    binding_types: Mapping[str, JsonWireType] | None = None,
    scope_roots: tuple[_JsDataRoot, ...] | None = None,
    include_root_variables: bool = True,
    component_js: bool = False,
) -> str:
    """Render collision-tolerant JSDoc facts for VS Code's JS provider."""
    lines = ["// Generated Citry browser-analysis declarations."]
    names: set[str] = set()
    if include_root_variables:
        for root in roots:
            if root.name in names:
                continue
            names.add(root.name)
            lines.extend((f"/** @type {{{root.wire_type.javascript}}} */", f"var {root.name};"))
    for binding in bindings:
        if binding in names:
            continue
        names.add(binding)
        wire_type = (binding_types or {}).get(binding, JsonWireType("unknown"))
        lines.extend((f"/** @type {{{wire_type.javascript}}} */", f"var {binding};"))
    data_shape = _js_object_shape(tuple((root.name, root.wire_type.javascript, True) for root in roots))
    effective_scope_roots = roots if scope_roots is None else scope_roots
    scope_shape = _js_object_shape(
        tuple((root.name, root.wire_type.javascript, root.presence == "always") for root in effective_scope_roots)
    )
    props_shape = (
        "Record<string, unknown>"
        if props is None
        else _js_object_shape(tuple((prop.name, prop.javascript, prop.required or prop.has_default) for prop in props))
    )
    state_shape = _js_object_shape(tuple((root.name, root.wire_type.javascript, True) for root in state_roots))
    event_type = " | ".join(_js_string_literal(name) for name in event_names) or "string"
    lines.extend(
        (
            f"/** @typedef {{{data_shape}}} CitryJsData */",
            f"/** @typedef {{{props_shape}}} CitryClientProps */",
            f"/** @typedef {{{state_shape}}} CitryEventsState */",
            f"/** @typedef {{{event_type}}} CitryServerEventName */",
            "/** @typedef {Object} CitryEventError",
            " * @property {number} status",
            " * @property {string} code",
            " * @property {string} message",
            " * @property {Record<string, string[]>} [fieldErrors]",
            " */",
            "/** @callback CitryCleanup @returns {void} */",
            "/** @callback CitryComponentInitializer",
            " * @param {CitryComponentContext} context",
            " * @returns {void | CitryCleanup}",
            " */",
            "/**",
            " * @typedef {Object} CitryComponentContext",
            " * @property {string} id",
            " * @property {Element[]} els",
            " * @property {CitryJsData} data",
            f" * @property {{{scope_shape} & Record<string, unknown>}} scope",
            " * @property {Readonly<CitryClientProps>} props",
            " * @property {CitryEventsState | null} state",
            " * @property {unknown} [graph]",
            " * @property {(key: string | symbol, value: unknown) => void} provide",
            " * @property {(key: string | symbol, fallback?: unknown) => unknown} inject",
            " * @property {(key: string | symbol) => void} unprovide",
            " * @property {<T>(value: T) => T} reactive",
            " * @property {(fn: () => void) => CitryCleanup} effect",
            " * @property {(name?: CitryServerEventName) => boolean} loading",
            " * @property {(name?: CitryServerEventName) => (CitryEventError | null)} error",
            " * @property {(name: CitryServerEventName, args?: Record<string, unknown>, opts?: unknown) => "
            "Promise<unknown>} sendEvent",
            " * @property {(name: string, callback: (detail: unknown) => void) => CitryCleanup} onEvent",
            " */",
            "/** @typedef {Object} CitryPropDefinition",
            " * @property {(Function | Function[])} [type]",
            " * @property {boolean} [required]",
            " * @property {*} [default]",
            " */",
            "/** @typedef {Object} CitryComponentDefinition",
            " * @property {Record<string, CitryPropDefinition>} [props]",
            " * @property {CitryComponentInitializer} init",
            " */",
        )
    )
    if component_js:
        lines.extend(
            (
                "/** @overload @param {CitryComponentInitializer} definition @returns {void} */",
                "/** @overload @param {CitryComponentDefinition} definition @returns {void} */",
                "function $component(definition) {}",
            )
        )
    else:
        lines.extend(
            (
                "/** @param {CitryServerEventName} name @param {Record<string, unknown>=} args "
                "@returns {Promise<unknown>} */",
                "function sendEvent(name, args) { return Promise.resolve(); }",
                "/** @param {CitryServerEventName} name @param {Record<string, unknown>=} args "
                "@returns {Promise<unknown>} */",
                "function $sendEvent(name, args) { return Promise.resolve(); }",
                "/** @param {string} name @param {(detail: unknown) => void} fn @returns {CitryCleanup} */",
                "function onEvent(name, fn) { return function () {}; }",
                "/** @param {string} name @param {(detail: unknown) => void} fn @returns {CitryCleanup} */",
                "function $onEvent(name, fn) { return function () {}; }",
                "/** @type {CitryEventsState} */ var $state;",
                "/** @param {CitryServerEventName} [name] @returns {boolean} */",
                "function $loading(name) { return false; }",
                "/** @param {CitryServerEventName} [name] @returns {CitryEventError | null} */",
                "function $error(name) { return null; }",
                "/** @param {string | symbol} key @param {unknown} value @returns {void} */",
                "function $provide(key, value) {}",
                "/** @param {string | symbol} key @param {unknown} [fallback] @returns {unknown} */",
                "function $inject(key, fallback) { return fallback; }",
                "/** @param {string | symbol} key @returns {void} */",
                "function $unprovide(key) {}",
                "/** @type {Event} */ var $event;",
                "/** @type {Element} */ var $el;",
                "/** @type {Record<string, Element>} */ var $refs;",
            )
        )
    return "\n".join(lines)


def _js_object_shape(fields: tuple[tuple[str, str, bool], ...]) -> str:
    if not fields:
        return "Record<string, never>"
    members = [f"{_js_property_name(name)}{'?' if not required else ''}: {value}" for name, value, required in fields]
    return "{" + ", ".join(members) + "}"


def _js_property_name(name: str) -> str:
    return name if name.isidentifier() else _js_string_literal(name)


def _js_string_literal(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _browser_event_origin_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    resolved = _browser_server_event_at(document, position, project, open_documents)
    if resolved is None:
        return ()
    _region, name, _start, _end, contract = resolved
    return contract.get(name, ())


def _browser_event_completion_result(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> CompletionResult | None:
    """Complete server handlers in Citry calls and declarative event values."""
    call_context = _browser_event_context(document, position, project, open_documents)
    if call_context is not None:
        call_region, expression, call_index, consumers = call_context
        call = next(
            (
                candidate
                for candidate in browser_literal_calls(expression, SERVER_EVENT_CALL_NAMES)
                if candidate.start_index <= call_index <= candidate.end_index
            ),
            None,
        )
        if call is not None:
            contract = _event_contract(consumers, document, project, open_documents)
            if contract is None:
                return CompletionResult((), is_incomplete=True)
            prefix_bytes = expression.source.encode("utf-8")[
                call.start_index - expression.start_index : call_index - expression.start_index
            ]
            try:
                prefix = prefix_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return CompletionResult((), is_incomplete=True)
            edit_range = _range(call_region.source_map.map_range(call.start_index, call.end_index))
            return CompletionResult(
                tuple(
                    types.CompletionItem(
                        label=name,
                        kind=types.CompletionItemKind.Function,
                        detail="Citry server event handler",
                        text_edit=types.TextEdit(edit_range, name),
                    )
                    for name in sorted(contract)
                    if name.startswith(prefix)
                ),
                is_incomplete=True,
            )

    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    source = region.source_map.template_source
    cursor = parser_char_index(source, parser_index)

    # Truncating at the cursor lets the existing tag scanner prove that the
    # cursor is inside an authored start tag rather than a comment or raw body.
    chain = _unfinished_start_tag_chain(source[:cursor])
    if not chain:
        return None
    tag_start, _tag_name, tag_text = chain[-1]
    match = re.search(
        r"(?:^|[ \t\r\n])@c-[^\s=/>]+\s*=\s*(['\"])([^'\"()\s]*)$",
        tag_text,
    )
    if match is None:
        return None
    prefix = match.group(2)
    prefix_start = tag_start + match.start(2)
    start_index = len(source[:prefix_start].encode("utf-8"))
    edit_range = _range(region.source_map.map_range(start_index, parser_index))

    consumers = _template_consumers(document, region, project, open_documents)
    contract = _event_contract(consumers, document, project, open_documents)
    if contract is None:
        return CompletionResult((), is_incomplete=True)
    return CompletionResult(
        tuple(
            types.CompletionItem(
                label=name,
                kind=types.CompletionItemKind.Function,
                detail="Citry server event handler",
                text_edit=types.TextEdit(edit_range, name),
            )
            for name in sorted(contract)
            if name.startswith(prefix)
        ),
        is_incomplete=True,
    )


def _browser_server_event_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[TemplateRegion | JsRegion, str, int, int, Mapping[str, tuple[types.Location, ...]]] | None:
    """Resolve one literal server-handler name across every supported spelling."""
    region = document.region_at(position)
    if region is not None:
        parsed = document.parsed.get(region.key)
        parser_index = region.source_map.parser_index_at(_citry_position(position))
        consumers = _template_consumers(document, region, project, open_documents)
        contract = _event_contract(consumers, document, project, open_documents)
        parser = project.analysis.parse_template if project.analysis is not None else parse_template
        if parsed is not None and parser_index is not None and contract is not None:
            event = next(
                (
                    candidate
                    for candidate in browser_declarative_events(
                        parsed.template,
                        frozenset(contract),
                        parse_nested=parser,
                    )
                    if candidate.start_index <= parser_index <= candidate.end_index
                ),
                None,
            )
            if event is not None:
                return region, event.name, event.start_index, event.end_index, contract
    context = _browser_event_context(document, position, project, open_documents)
    if context is None:
        return None
    expression_region, expression, parser_index, consumers = context
    call = next(
        (
            candidate
            for candidate in browser_literal_calls(expression, SERVER_EVENT_CALL_NAMES)
            if candidate.start_index <= parser_index <= candidate.end_index
        ),
        None,
    )
    if call is None:
        return None
    contract = _event_contract(consumers, document, project, open_documents)
    return (
        (expression_region, call.value, call.start_index, call.end_index, contract) if contract is not None else None
    )


def _browser_event_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Hover | None:
    resolved = _browser_server_event_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, name, start, end, contract = resolved
    if name not in contract:
        return None
    return types.Hover(
        types.MarkupContent(
            types.MarkupKind.Markdown,
            "\n".join(
                (
                    "```javascript",
                    f"(server event) {name}",
                    "```",
                    "",
                    "Citry server event handler",
                )
            ),
        ),
        range=_range(region.source_map.map_range(start, end)),
    )


def _browser_event_context(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[TemplateRegion | JsRegion, BrowserExpression, int, tuple[ComponentRecord, ...]] | None:
    template_context = _browser_expression_context(document, position, project)
    if template_context is not None:
        region, expression, parser_index = template_context
        consumers = _template_consumers(document, region, project, open_documents)
        return region, expression, parser_index, consumers
    js_region = document.js_region_at(position)
    if js_region is None:
        return None
    js_parser_index = js_region.source_map.parser_index_at(_citry_position(position))
    if js_parser_index is None:
        return None
    js_consumers = _js_consumers(document, js_region, project, open_documents)
    return js_region, _component_js_expression(js_region), js_parser_index, js_consumers


def _component_js_expression(region: JsRegion) -> BrowserExpression:
    source = region.source_map.template_source
    return BrowserExpression(source, 0, len(source.encode("utf-8")), "statement", "component-js")


def _js_data_member_root_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[JsRegion, _JsDataRoot, Any] | None:
    region = document.js_region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    member = browser_member_at(_component_js_expression(region), parser_index)
    if member is None or member.owner not in {"data", "scope"}:
        return None
    roots = (
        _js_asset_data_roots(document, region, project, open_documents)
        if member.owner == "data"
        else _js_asset_scope_roots(document, region, project, open_documents)
    )
    if roots is None:
        return None
    root = next((candidate for candidate in roots if candidate.name == member.name), None)
    return (region, root, member) if root is not None else None


def _js_data_member_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Hover | None:
    resolved = _js_data_member_root_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, root, member = resolved
    lines = [
        "```javascript",
        f"(property) {member.name}: {root.wire_type.javascript}",
        "```",
        "",
        "Citry JsData",
    ]
    for producer in sorted(root.producers, key=lambda item: item.origin):
        lines.append(f"- `{producer.origin}`")
    return types.Hover(
        types.MarkupContent(types.MarkupKind.Markdown, "\n".join(lines)),
        range=_range(region.source_map.map_range(member.start_index, member.end_index)),
    )


def _js_data_member_origin_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    resolved = _js_data_member_root_at(document, position, project, open_documents)
    return _js_data_root_locations(resolved[1], open_documents) if resolved is not None else ()


def _js_data_member_reference_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
    *,
    include_declaration: bool,
) -> list[types.Location] | None:
    resolved = _js_data_member_root_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, root, _member = resolved
    expression = _component_js_expression(region)
    found: list[types.Location] = []
    for identifier in browser_identifiers(expression):
        member = browser_member_at(expression, identifier.start_index)
        if member is None or member.owner not in {"data", "scope"} or member.name != root.name:
            continue
        found.append(
            types.Location(
                document.uri,
                _range(region.source_map.map_range(member.start_index, member.end_index)),
            )
        )
    if include_declaration:
        found.extend(_js_data_root_locations(root, open_documents))
    return list(_sorted_locations(found))


def _shared_state_roots(
    consumers: tuple[ComponentRecord, ...],
    current_document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_JsDataRoot, ...] | None:
    """Intersect public Events State fields across every physical owner."""
    if not consumers or project.source_analysis is None:
        return None
    per_consumer: list[tuple[_JsDataRoot, ...]] = []
    for component in consumers:
        fields = project.source_analysis.state_fields(component)
        if fields is None:
            return None
        consumer_roots: list[_JsDataRoot] = []
        for state_field in fields:
            root = _state_field_root(state_field, current_document, open_documents)
            if root is None:
                return None
            consumer_roots.append(root)
        per_consumer.append(tuple(consumer_roots))
    common = {root.name: root for root in per_consumer[0]}
    for roots in per_consumer[1:]:
        candidates = {root.name: root for root in roots}
        common = {
            name: _JsDataRoot(
                name,
                "always",
                merge_json_wire_types((root.wire_type, candidates[name].wire_type)),
                tuple(dict.fromkeys((*root.producers, *candidates[name].producers))),
                locations=_dedupe_locations((*root.locations, *candidates[name].locations)),
            )
            for name, root in common.items()
            if name in candidates
        }
    return tuple(common.values())


def _state_field_root(
    field: SourceStateFieldRecord,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> _JsDataRoot | None:
    source = _python_source(field.source_file, current_document, open_documents)
    if source is None:
        return None
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None
    class_node = _class_node_for_qualname(tree, field.qualname)
    if class_node is None:
        return None
    declarations = [
        statement
        for statement in class_node.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == field.name
    ]
    if len(declarations) != 1:
        return None
    token = _annotated_field_token(source, class_node, field.name)
    if token is None:
        return None
    line, start, end = token
    source_line = source.splitlines()[line]
    location = types.Location(
        field.source_file.resolve().as_uri(),
        types.Range(
            types.Position(line, _utf16_units(source_line[:start])),
            types.Position(line, _utf16_units(source_line[:end])),
        ),
    )
    wire_type = json_wire_type_from_annotation(ast.unparse(declarations[0].annotation))
    return _JsDataRoot(
        field.name,
        "always",
        wire_type,
        (_JsDataProducer(f"{field.qualname}.{field.name}", wire_type, field.description),),
        locations=(location,),
    )


def _browser_state_root_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[TemplateRegion | JsRegion, _JsDataRoot, Any] | None:
    region: TemplateRegion | JsRegion
    template_context = _browser_expression_context(document, position, project)
    if template_context is not None:
        region, expression, parser_index = template_context
        consumers = _template_consumers(document, region, project, open_documents)
    else:
        js_region = document.js_region_at(position)
        if js_region is None:
            return None
        js_parser_index = js_region.source_map.parser_index_at(_citry_position(position))
        if js_parser_index is None:
            return None
        region = js_region
        expression = _component_js_expression(js_region)
        consumers = _js_consumers(document, js_region, project, open_documents)
        parser_index = js_parser_index
    member = browser_member_at(expression, parser_index)
    state_owners = {"$state"} if isinstance(region, TemplateRegion) else {"$state", "state"}
    if member is None or member.owner not in state_owners:
        return None
    roots = _shared_state_roots(consumers, document, project, open_documents)
    if roots is None:
        return None
    root = next((candidate for candidate in roots if candidate.name == member.name), None)
    return (region, root, member) if root is not None else None


def _browser_state_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Hover | None:
    resolved = _browser_state_root_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, root, member = resolved
    return types.Hover(
        types.MarkupContent(
            types.MarkupKind.Markdown,
            f"```javascript\n(property) {root.name}: {root.wire_type.javascript}\n```\n\nCitry Events State",
        ),
        range=_range(region.source_map.map_range(member.start_index, member.end_index)),
    )


def _browser_state_origin_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    resolved = _browser_state_root_at(document, position, project, open_documents)
    return resolved[1].locations if resolved is not None else ()


def _browser_state_reference_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
    *,
    include_declaration: bool,
) -> list[types.Location] | None:
    resolved = _browser_state_root_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, root, _member = resolved
    if isinstance(region, TemplateRegion):
        parsed = document.parsed.get(region.key)
        if parsed is None:
            return None
        parser = project.analysis.parse_template if project.analysis is not None else parse_template
        expressions = browser_expressions(parsed.template, parse_nested=parser)
    else:
        expressions = (_component_js_expression(region),)
    found: list[types.Location] = []
    state_owners = {"$state"} if isinstance(region, TemplateRegion) else {"$state", "state"}
    for expression in expressions:
        for identifier in browser_identifiers(expression):
            member = browser_member_at(expression, identifier.start_index)
            if member is None or member.owner not in state_owners or member.name != root.name:
                continue
            found.append(
                types.Location(
                    document.uri,
                    _range(region.source_map.map_range(member.start_index, member.end_index)),
                )
            )
    if include_declaration:
        found.extend(root.locations)
    return list(_sorted_locations(found))


def _event_contract(
    consumers: tuple[ComponentRecord, ...],
    current_document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> dict[str, tuple[types.Location, ...]] | None:
    """Intersect exact effective event names across every physical-asset owner."""
    if not consumers or project.source_analysis is None:
        return None
    per_consumer: list[dict[str, types.Location]] = []
    for component in consumers:
        event_handlers = project.source_analysis.event_handlers(component)
        if event_handlers is None:
            return None
        resolved: dict[str, types.Location] = {}
        for handler in event_handlers:
            location = _event_handler_location(handler, current_document, open_documents)
            if location is None:
                return None
            resolved[handler.name] = location
        per_consumer.append(resolved)
    common = set(per_consumer[0])
    for consumer_handlers in per_consumer[1:]:
        common.intersection_update(consumer_handlers)
    return {
        name: _sorted_locations([consumer_handlers[name] for consumer_handlers in per_consumer])
        for name in sorted(common)
    }


def _event_handler_location(
    handler: SourceEventRecord,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Location | None:
    source = _python_source(handler.source_file, current_document, open_documents)
    if source is None:
        return None
    source_range = python_event_handler_range(
        source,
        handler.qualname,
        handler.method_name,
        handler.name,
    )
    if source_range is None:
        return None
    return types.Location(handler.source_file.resolve().as_uri(), _range(source_range))


def _js_data_type_diagnostics(
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Diagnostic, ...]:
    """Warn at current Python producers that cannot cross the strict JSON wire."""
    if document.language_id != "python" or project.catalog is None:
        return ()
    canonical = file_uri_path(document.uri)
    if canonical is None:
        return ()
    canonical = canonical.resolve()
    found: dict[tuple[int, int, int, int, str], types.Diagnostic] = {}
    for component in project.catalog.components:
        roots = _component_js_data_roots(component, project, document, open_documents)
        if roots is None:
            continue
        for root in roots:
            if not root.wire_type.unsupported:
                continue
            detail = "; ".join(root.wire_type.unsupported)
            for location in _js_data_root_locations(root, open_documents):
                path = file_uri_path(location.uri)
                if path is None or path.resolve() != canonical:
                    continue
                key = (
                    location.range.start.line,
                    location.range.start.character,
                    location.range.end.line,
                    location.range.end.character,
                    root.name,
                )
                found[key] = types.Diagnostic(
                    location.range,
                    render_diagnostic(JS_DATA_UNSUPPORTED_TYPE, name=root.name, detail=detail),
                    severity=types.DiagnosticSeverity.Warning,
                    code=JS_DATA_UNSUPPORTED_TYPE,
                    code_description=types.CodeDescription(diagnostic_documentation_url(JS_DATA_UNSUPPORTED_TYPE)),
                    source="citry",
                )
    return tuple(found[key] for key in sorted(found))


def _css_data_completion_result(
    document: DocumentState,
    region: CssRegion,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> CompletionResult:
    """Complete exact runtime custom-property names inside CSS ``var()``."""
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return CompletionResult(())
    context = css_data_completion_at(region.source_map.template_source, parser_index)
    if context is None:
        return CompletionResult(())
    roots = _css_data_roots(document, region, project, open_documents)
    edit_range = _range(region.source_map.map_range(context.start_index, context.end_index))
    items = tuple(
        types.CompletionItem(
            label=f"--{root.name}",
            kind=types.CompletionItemKind.Variable,
            detail=_css_data_root_detail(root),
            documentation=_markdown(_css_data_root_documentation(root)),
            filter_text=f"--{root.name}",
            text_edit=types.TextEdit(edit_range, f"--{root.name}"),
        )
        for root in roots
        if root.name.startswith(context.prefix)
    )
    return CompletionResult(items, is_incomplete=True)


def _css_data_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Hover | None:
    """Describe a custom property only when every stylesheet owner provides it."""
    resolved = _css_data_root_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, root, reference = resolved
    lines = ["```css", f"--{root.name}", "```", "", "Provided by Citry CSS data:"]
    for producer in sorted(root.producers, key=lambda item: item.origin):
        type_text = f": `{producer.type_display}`" if producer.type_display else ""
        lines.append(f"- `{producer.origin}`{type_text}")
        if producer.description:
            lines.append(f"  {producer.description}")
    if root.presence == "conditional":
        lines.extend(("", "This key is returned only on some proven `css_data()` paths."))
    return types.Hover(
        types.MarkupContent(types.MarkupKind.Markdown, "\n".join(lines)),
        range=_range(region.source_map.map_range(reference.start_index, reference.end_index)),
    )


def _css_data_reference_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
    *,
    include_declaration: bool,
) -> list[types.Location] | None:
    """List exact uses inside one physical CSS asset and optional Python origins."""
    resolved = _css_data_root_at(document, position, project, open_documents)
    if resolved is None:
        return None
    region, root, _reference = resolved
    found = [
        types.Location(document.uri, _range(region.source_map.map_range(item.start_index, item.end_index)))
        for item in css_data_references(region.source_map.template_source)
        if item.name == root.name
    ]
    if include_declaration:
        found.extend(_css_data_root_locations(root, open_documents))
    return list(_sorted_locations(found))


def _css_data_origin_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    """Return every exact Python producer for one proven CSS-data reference."""
    resolved = _css_data_root_at(document, position, project, open_documents)
    if resolved is None:
        return ()
    return _css_data_root_locations(resolved[1], open_documents)


def _css_data_root_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[CssRegion, _CssDataRoot, Any] | None:
    region = document.css_region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    reference = css_data_reference_at(region.source_map.template_source, parser_index)
    if reference is None:
        return None
    root = next(
        (
            candidate
            for candidate in _css_data_roots(document, region, project, open_documents)
            if candidate.name == reference.name
        ),
        None,
    )
    return (region, root, reference) if root is not None else None


def _css_data_roots(
    document: DocumentState,
    region: CssRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_CssDataRoot, ...]:
    """Intersect exact CSS-data names across every current asset consumer."""
    consumers = _css_consumers(document, region, project, open_documents)
    if not consumers:
        return ()
    resolved = [_component_css_data_roots(component, project, document, open_documents) for component in consumers]
    if any(roots is None for roots in resolved):
        return ()
    root_sets = [roots for roots in resolved if roots is not None]
    if not root_sets:
        return ()
    common = {root.name: root for root in root_sets[0]}
    if len(common) != len(root_sets[0]):
        return ()
    for roots in root_sets[1:]:
        candidates = {root.name: root for root in roots}
        if len(candidates) != len(roots):
            return ()
        joined: dict[str, _CssDataRoot] = {}
        for name, root in common.items():
            candidate = candidates.get(name)
            if candidate is None:
                continue
            joined[name] = _CssDataRoot(
                name,
                "conditional" if root.presence == "conditional" or candidate.presence == "conditional" else "always",
                tuple(dict.fromkeys((*root.producers, *candidate.producers))),
                _dedupe_fields((*root.fields, *candidate.fields)),
                _dedupe_locations((*root.locations, *candidate.locations)),
            )
        common = joined
    return tuple(common.values())


def _css_consumers(
    document: DocumentState,
    region: CssRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[ComponentRecord, ...]:
    catalog = project.catalog
    if catalog is None:
        return ()
    if document.language_id == "python":
        if not region.ast_proven or region.component_name is None:
            return ()
        owners = catalog.inline_asset_consumers(document.uri, "css", region.component_name)
    elif document.language_id == "css":
        owners = catalog.asset_owners(document.uri, "css")
    else:
        return ()
    return tuple(owner for owner in owners if _css_consumer_is_current(owner, project, open_documents))


def _css_consumer_is_current(
    component: ComponentRecord,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> bool:
    """Reject CSS ownership contradicted by synchronized component source."""
    if open_documents is None or project.source_analysis is None:
        return True
    chain = project.source_analysis.css_asset_chain(component)
    if chain is None:
        return not any(document.language_id == "python" for document in open_documents.values())
    for candidate in chain:
        found, source = _synchronized_document_source(candidate.source_file, open_documents)
        if found and (
            source is None
            or python_class_asset_resolution_signature(source, candidate.qualname, "css") != candidate.resolution
        ):
            return False
    return True


def _component_css_data_roots(
    component: ComponentRecord,
    project: ProjectState,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_CssDataRoot, ...] | None:
    """Resolve declared fields or conservative keys for one component."""
    schema = component.schemas.css_data
    owner_name = component.qualname or component.class_name or component.name
    if schema.kind == "opaque":
        return ()
    if schema.kind == "fields":
        return _css_schema_roots(component, owner_name, open_documents)
    if project.source_analysis is None:
        return None
    chain = project.source_analysis.css_data_chain(component)
    if not chain:
        return None
    for candidate in chain[:-1]:
        source = _python_source(candidate.source_file, current_document, open_documents)
        if source is None or python_class_resolution_signature(source, candidate.qualname) != candidate.resolution:
            return None
        if python_class_defines_direct_method(source, candidate.qualname, "css_data") is not False:
            return None
    owner = chain[-1]
    source = _python_source(owner.source_file, current_document, open_documents)
    if source is None or python_class_resolution_signature(source, owner.qualname) != owner.resolution:
        return None
    shape = analyze_css_data_source(source, owner.qualname)
    if shape is None:
        return None
    return tuple(
        _CssDataRoot(
            root.name,
            root.presence,
            (_CssDataProducer(f"{owner_name}.css_data()"),),
            locations=tuple(
                types.Location(owner.source_file.resolve().as_uri(), _range(definition.key_range))
                for definition in root.definitions
            ),
        )
        for root in shape.roots
    )


def _css_schema_roots(
    component: ComponentRecord,
    owner_name: str,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_CssDataRoot, ...] | None:
    """Join catalog fields with direct schema edits from synchronized source."""
    schema = component.schemas.css_data
    grouped: dict[tuple[Path, str], list[FieldRecord]] = {}
    detached: list[FieldRecord] = []
    for schema_field in schema.fields:
        if schema_field.source_file is None or schema_field.source_qualname is None:
            detached.append(schema_field)
            continue
        grouped.setdefault((schema_field.source_file.resolve(), schema_field.source_qualname), []).append(schema_field)

    # An empty or newly added direct schema still has no catalog field that can
    # point at its class, so check the component's ordinary nested owner too.
    if component.python_file is not None and component.qualname is not None:
        grouped.setdefault((component.python_file.resolve(), f"{component.qualname}.CssData"), [])

    roots = [_catalog_css_data_root(schema_field, owner_name) for schema_field in detached]
    for (source_file, qualname), catalog_fields in grouped.items():
        found, source = (
            _synchronized_document_source(source_file, open_documents) if open_documents is not None else (False, None)
        )
        if not found:
            roots.extend(_catalog_css_data_root(schema_field, owner_name) for schema_field in catalog_fields)
            continue
        if source is None:
            return None
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
            return None
        schema_class = _class_node_for_qualname(tree, qualname)
        if schema_class is None:
            # A missing direct class with no catalog fields simply means the
            # component still inherits its effective schema elsewhere.
            if catalog_fields:
                return None
            continue
        by_name = {schema_field.name: schema_field for schema_field in catalog_fields}
        for statement in schema_class.body:
            if not isinstance(statement, ast.AnnAssign) or not isinstance(statement.target, ast.Name):
                continue
            if statement.target.id not in _direct_schema_field_names(schema_class):
                continue
            token = _annotated_field_token(source, schema_class, statement.target.id)
            if token is None:
                return None
            line, start, end = token
            source_line = source.splitlines()[line]
            location = types.Location(
                source_file.as_uri(),
                types.Range(
                    types.Position(line, _utf16_units(source_line[:start])),
                    types.Position(line, _utf16_units(source_line[:end])),
                ),
            )
            current_field = by_name.get(statement.target.id)
            annotation = _css_data_annotation(statement.annotation)
            roots.append(
                _CssDataRoot(
                    statement.target.id,
                    "always",
                    (
                        _CssDataProducer(
                            f"{qualname}.{statement.target.id}",
                            ast.unparse(annotation),
                            current_field.description if current_field is not None else None,
                        ),
                    ),
                    fields=(current_field,) if current_field is not None else (),
                    locations=(location,) if current_field is None else (),
                )
            )
    return tuple(roots)


def _catalog_css_data_root(schema_field: FieldRecord, owner_name: str) -> _CssDataRoot:
    return _CssDataRoot(
        schema_field.name,
        "always",
        (
            _CssDataProducer(
                f"{owner_name}.CssData.{schema_field.name}",
                schema_field.type_display,
                schema_field.description,
            ),
        ),
        fields=(schema_field,),
    )


def _css_data_annotation(annotation: ast.expr) -> ast.expr:
    if isinstance(annotation, ast.Subscript) and (
        (isinstance(annotation.value, ast.Name) and annotation.value.id == "Annotated")
        or (isinstance(annotation.value, ast.Attribute) and annotation.value.attr == "Annotated")
    ):
        return annotation.slice.elts[0] if isinstance(annotation.slice, ast.Tuple) else annotation.slice
    return annotation


def _css_data_root_locations(
    root: _CssDataRoot,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    locations = list(root.locations)
    for schema_field in root.fields:
        source = (
            _open_document_source(schema_field.source_file, open_documents)
            if schema_field.source_file and open_documents
            else None
        )
        location = _field_definition_location(schema_field, source=source)
        if location is None:
            return ()
        locations.append(location)
    return _sorted_locations(locations)


def _css_data_root_detail(root: _CssDataRoot) -> str:
    producer_types = tuple(
        dict.fromkeys(producer.type_display for producer in root.producers if producer.type_display)
    )
    if len(producer_types) == 1:
        suffix = f" · Python producer type: {producer_types[0]}"
    elif producer_types:
        suffix = f" · Python producer types: {', '.join(producer_types)}"
    else:
        suffix = ""
    conditional = " · conditional" if root.presence == "conditional" else ""
    return f"Citry CSS data{suffix}{conditional}"


def _css_data_root_documentation(root: _CssDataRoot) -> str:
    lines = ["Python producers:"]
    for producer in sorted(root.producers, key=lambda item: item.origin):
        type_text = f": `{producer.type_display}`" if producer.type_display else ""
        lines.append(f"- `{producer.origin}`{type_text}")
        if producer.description:
            lines.append(f"  {producer.description}")
    return "\n".join(lines)


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


def _template_data_roots(
    document: DocumentState,
    region: TemplateRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_TemplateRoot, ...]:
    """Join declared or source-inferred roots across all proven consumers."""
    catalog = project.catalog
    if catalog is None:
        return ()
    owners = _template_consumers(document, region, project, open_documents)
    if not owners:
        return ()
    contexts = [_component_template_context(owner, project, document, open_documents) for owner in owners]
    if any(context is None for context in contexts):
        return ()
    resolved = [context.roots for context in contexts if context is not None]
    if not resolved:
        return ()
    common = {_identifier_key(root.name): root for root in resolved[0]}
    if len(common) != len(resolved[0]):
        return ()
    for roots in resolved[1:]:
        candidates = {_identifier_key(root.name): root for root in roots}
        if len(candidates) != len(roots):
            return ()
        joined: dict[str, _TemplateRoot] = {}
        for key, root in common.items():
            candidate = candidates.get(key)
            if candidate is None:
                continue
            fields = _dedupe_fields((*root.fields, *candidate.fields))
            # Conflicting annotations do not make the root itself disappear.
            # They only prevent type-specific hover claims.
            type_field = root.type_field
            if (
                type_field is None
                or candidate.type_field is None
                or not _same_field_contract(type_field, candidate.type_field)
            ):
                type_field = None
            joined[key] = _TemplateRoot(
                name=root.name,
                presence=(
                    "conditional"
                    if root.presence == "conditional" or candidate.presence == "conditional"
                    else "always"
                ),
                origins=root.origins | candidate.origins,
                fields=fields,
                type_field=type_field,
                fallback_types=_join_root_fallback_types(root, candidate),
                description=root.description if root.description == candidate.description else None,
                shadow_type_display=(
                    root.shadow_type_display if root.shadow_type_display == candidate.shadow_type_display else None
                ),
                locations=_dedupe_locations((*root.locations, *candidate.locations)),
                lint_definitions=_dedupe_lint_definitions((*root.lint_definitions, *candidate.lint_definitions)),
                access=root.access if root.access == candidate.access else "mixed",
            )
        common = joined
    return tuple(common.values())


def _template_consumers(
    document: DocumentState,
    region: TemplateRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[ComponentRecord, ...]:
    catalog = project.catalog
    if catalog is None:
        return ()
    if document.language_id == "python":
        if not region.ast_proven or region.component_name is None:
            return ()
        owners = catalog.inline_asset_consumers(document.uri, "template", region.component_name)
        return tuple(owner for owner in owners if _template_consumer_is_current(owner, project, open_documents))
    if document.language_id in {"citry-html", "html"}:
        return tuple(
            owner
            for owner in catalog.asset_owners(document.uri, "template")
            if _template_consumer_is_current(owner, project, open_documents)
        )
    return ()


def _template_consumer_is_current(
    component: ComponentRecord,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> bool:
    """Reject a consumer whose synchronized MRO no longer selects this asset."""
    if open_documents is None or project.source_analysis is None:
        return True
    chain = project.source_analysis.template_asset_chain(component)
    if chain is None:
        # An unsupported dynamic/imported declaration has no finite source
        # dependency set. Trust the loaded registry only while no Python
        # buffer can be newer than it.
        return not any(document.language_id == "python" for document in open_documents.values())
    for candidate in chain:
        found, source = _synchronized_document_source(candidate.source_file, open_documents)
        if not found:
            continue
        if (
            source is None
            or python_class_asset_resolution_signature(source, candidate.qualname) != candidate.resolution
        ):
            return False
    return True


def _component_template_roots(
    component: ComponentRecord,
    project: ProjectState,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[_TemplateRoot, ...] | None:
    """Return the roots from one consumer's source-analysis context."""
    context = _component_template_context(component, project, current_document, open_documents)
    return context.roots if context is not None else None


def _component_template_context(
    component: ComponentRecord,
    project: ProjectState,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> _TemplateContext | None:
    """Resolve one consumer without mixing its source scope with another."""
    schema = component.schemas.template_data
    schema_policy = cast("Literal['closed', 'allow-extra', 'unknown']", schema.namespace_policy)
    if schema.kind in {"fields", "opaque"}:
        roots = _with_component_lint_roots(
            component,
            project,
            tuple(_schema_template_root(field) for field in schema.fields),
        )
        schema_owner = _schema_source_anchor(schema, component, project)
        if schema_owner is None:
            return _TemplateContext(roots, namespace_policy=schema_policy)
        source_file, module, qualname = schema_owner
        source = _python_source(source_file, current_document, open_documents)
        if source is None:
            return _TemplateContext(roots, namespace_policy=schema_policy)
        return _TemplateContext(
            roots,
            source_file,
            source,
            "schema",
            module,
            qualname,
            namespace_policy=schema_policy,
        )
    if project.source_analysis is None:
        return None
    chain = project.source_analysis.template_data_chain(component)
    if not chain:
        return None
    for candidate in chain[:-1]:
        source = _python_source(candidate.source_file, current_document, open_documents)
        if source is None:
            return None
        if python_class_resolution_signature(source, candidate.qualname) != candidate.resolution:
            return None
        if python_class_defines_direct_method(source, candidate.qualname, "template_data") is not False:
            return None
    owner = chain[-1]
    source = _python_source(owner.source_file, current_document, open_documents)
    if source is None:
        return None
    if python_class_resolution_signature(source, owner.qualname) != owner.resolution:
        return None
    kwargs_schema = component.schemas.kwargs
    kwargs_fields = tuple(field.name for field in kwargs_schema.fields) if kwargs_schema.kind == "fields" else None
    shape = analyze_template_data_source(
        source,
        owner.qualname,
        kwargs_fields=kwargs_fields,
    )
    if shape is None:
        return None
    kwargs_by_name = {_identifier_key(field.name): field for field in kwargs_schema.fields}
    roots = _with_component_lint_roots(
        component,
        project,
        tuple(_inferred_template_root(root, shape, owner.source_file, kwargs_by_name) for root in shape.roots),
    )
    kwargs_owner = _schema_source_owner(kwargs_schema)
    kwargs_type = (kwargs_owner[1], kwargs_owner[2]) if kwargs_owner is not None else None
    return _TemplateContext(
        roots,
        owner.source_file,
        source,
        "inferred",
        owner.module,
        owner.qualname,
        kwargs_type,
        (
            "unknown"
            if shape.completeness == "open"
            else cast("Literal['closed', 'allow-extra', 'unknown']", kwargs_schema.namespace_policy)
            if shape.preserves_kwargs_extras
            else "closed"
        ),
    )


def _schema_source_owner(schema: SchemaRecord) -> tuple[Path, str, str] | None:
    """Find the field whose provenance names the effective schema class."""
    candidates = {
        (field.source_file.resolve(), field.source_module, field.source_qualname)
        for field in schema.fields
        if field.source_module is not None
        and field.source_qualname is not None
        and field.source_file is not None
        and schema.import_path == f"{field.source_module}.{field.source_qualname}"
    }
    return next(iter(candidates)) if len(candidates) == 1 else None


def _schema_source_anchor(
    schema: SchemaRecord,
    component: ComponentRecord,
    project: ProjectState,
) -> tuple[Path, str, str] | None:
    """Choose one stable virtual-document owner while roots keep their own types."""
    candidates = sorted(
        {
            (field.source_file.resolve(), field.source_module, field.source_qualname)
            for field in schema.fields
            if field.source_module is not None and field.source_qualname is not None and field.source_file is not None
        },
        key=lambda item: (str(item[0]), item[1], item[2]),
    )
    if candidates:
        return candidates[0]
    if schema.import_path is None:
        return None

    # An empty schema has no field provenance, so recover its authored class
    # from the component MRO copied by the worker.
    classes: list[tuple[Path, str]] = []
    if component.python_file is not None and component.module is not None:
        classes.append((component.python_file.resolve(), component.module))
    if project.source_analysis is not None:
        chain = project.source_analysis.template_data_chain(component)
        if chain is not None:
            classes.extend((item.source_file.resolve(), item.module) for item in chain)
    anchors = {
        (source_file, module, schema.import_path[len(module) + 1 :])
        for source_file, module in classes
        if schema.import_path.startswith(f"{module}.")
    }
    if not anchors:
        return None
    longest_module = max(len(item[1]) for item in anchors)
    narrowed = sorted(
        (item for item in anchors if len(item[1]) == longest_module),
        key=lambda item: (str(item[0]), item[1], item[2]),
    )
    return narrowed[0] if len(narrowed) == 1 else None


def _schema_template_root(field: FieldRecord) -> _TemplateRoot:
    return _TemplateRoot(
        name=field.name,
        presence="always",
        origins=frozenset({"TemplateData"}),
        fields=(field,),
        type_field=field,
        fallback_types=(field.type_display,) if field.type_display is not None else None,
        access="attribute",
    )


def _with_component_lint_roots(
    component: ComponentRecord,
    project: ProjectState,
    roots: tuple[_TemplateRoot, ...],
) -> tuple[_TemplateRoot, ...]:
    """Add effective runtime globals and analysis-only variables as roots."""
    if project.analysis is None:
        return roots
    lint = project.analysis.component_lint.get(component.definition_id)
    if lint is None:
        return roots
    by_name = {_identifier_key(root.name): root for root in roots}
    if len(by_name) != len(roots):
        return roots
    ordered = list(roots)
    for variable in lint.template_variables:
        key = _identifier_key(variable.name)
        if key in by_name:
            # Component template data wins over a global of the same name at
            # runtime, so its source and type remain authoritative here too.
            continue
        definition = (
            project.source_analysis.template_lint_definition(component, variable.name)
            if project.source_analysis is not None
            else None
        )
        root = _lint_template_root(variable, definition)
        by_name[key] = root
        ordered.append(root)
    return tuple(ordered)


def _lint_template_root(
    variable: TemplateVariableInfo,
    definition: SourceLintRecord | None,
) -> _TemplateRoot:
    """Convert detached lint metadata and optional authored provenance."""
    display = variable.type_display if variable.type_fidelity == "normalized" else None
    return _TemplateRoot(
        name=variable.name,
        presence="always",
        origins=frozenset({_lint_variable_origin(variable.source)}),
        fallback_types=(display,) if display is not None else None,
        description=variable.description,
        shadow_type_display=_safe_shadow_type_display(display),
        lint_definitions=(definition,) if definition is not None else (),
        access="analysis",
    )


def _lint_variable_origin(source: str) -> str:
    return {
        "runtime-global": "runtime global",
        "application": "application lint metadata",
        "component": "component lint metadata",
        "extension": "extension template namespace",
    }.get(source, "template namespace metadata")


def _safe_shadow_type_display(value: str | None) -> str | None:
    """Canonicalize one expression-shaped annotation before code generation."""
    if value is None:
        return None
    try:
        expression = ast.parse(value, mode="eval")
    except (SyntaxError, UnicodeEncodeError, ValueError, MemoryError, RecursionError):
        return None
    forbidden = (
        ast.Await,
        ast.Call,
        ast.DictComp,
        ast.GeneratorExp,
        ast.IfExp,
        ast.Lambda,
        ast.ListComp,
        ast.NamedExpr,
        ast.SetComp,
        ast.Yield,
        ast.YieldFrom,
    )
    if any(isinstance(node, forbidden) for node in ast.walk(expression)):
        return None
    return ast.unparse(expression.body)


def _inferred_template_root(
    root: Any,
    shape: TemplateDataSourceShape,
    source_file: Path,
    kwargs_by_name: dict[str, FieldRecord],
) -> _TemplateRoot:
    fields: tuple[FieldRecord, ...] = ()
    type_field: FieldRecord | None = None
    if "kwargs" in root.origins:
        field = kwargs_by_name.get(_identifier_key(root.name))
        if field is not None:
            fields = (field,)
            if root.origins == frozenset({"kwargs"}):
                type_field = field
    locations = tuple(
        types.Location(source_file.resolve().as_uri(), _range(definition.key_range)) for definition in root.definitions
    )
    origins = {"template_data()"}
    if "kwargs" in root.origins:
        origins.add("Kwargs")
    if shape.completeness == "open":
        origins.add("open shape")
    return _TemplateRoot(
        name=root.name,
        presence=root.presence,
        origins=frozenset(origins),
        fields=fields,
        type_field=type_field,
        fallback_types=(type_field.type_display,) if type_field is not None and type_field.type_display else None,
        locations=_dedupe_locations(locations),
        access=(
            "attribute"
            if root.origins == frozenset({"kwargs"})
            else "mixed"
            if "kwargs" in root.origins
            else "mapping"
        ),
    )


def _python_source(
    source_file: Path,
    current_document: DocumentState,
    open_documents: Mapping[str, DocumentState] | None,
) -> str | None:
    """Prefer synchronized text and refuse conflicting aliases."""
    canonical = source_file.resolve()
    candidates: list[str] = []
    documents = [current_document]
    if open_documents is not None:
        documents.extend(document for document in open_documents.values() if document is not current_document)
    for document in documents:
        path = file_uri_path(document.uri)
        if path is None:
            continue
        try:
            document_path = path.resolve()
        except (OSError, ValueError):
            continue
        if document_path == canonical:
            candidates.append(document.source)
    if candidates:
        return candidates[0] if all(source == candidates[0] for source in candidates[1:]) else None
    try:
        with tokenize.open(canonical) as source_stream:
            return source_stream.read()
    except (OSError, SyntaxError, UnicodeError):
        return None


def _dedupe_locations(locations: tuple[types.Location, ...]) -> tuple[types.Location, ...]:
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


def _sorted_locations(locations: list[types.Location]) -> tuple[types.Location, ...]:
    """Deduplicate navigation results and keep their authored source order."""
    return tuple(
        sorted(
            _dedupe_locations(tuple(locations)),
            key=lambda location: (
                location.uri,
                location.range.start.line,
                location.range.start.character,
                location.range.end.line,
                location.range.end.character,
            ),
        )
    )


def _dedupe_fields(fields: tuple[FieldRecord, ...]) -> tuple[FieldRecord, ...]:
    retained: list[FieldRecord] = []
    seen: set[tuple[str, str | None, str | None, Path | None]] = set()
    for schema_field in fields:
        key = (
            schema_field.name,
            schema_field.source_module,
            schema_field.source_qualname,
            schema_field.source_file,
        )
        if key not in seen:
            seen.add(key)
            retained.append(schema_field)
    return tuple(retained)


def _dedupe_lint_definitions(
    definitions: tuple[SourceLintRecord, ...],
) -> tuple[SourceLintRecord, ...]:
    retained: list[SourceLintRecord] = []
    seen: set[tuple[str, str, str, Path]] = set()
    for definition in definitions:
        key = (definition.name, definition.kind, definition.owner, definition.source_file)
        if key not in seen:
            seen.add(key)
            retained.append(definition)
    return tuple(retained)


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
    roots: tuple[_TemplateRoot, ...],
) -> tuple[_TemplateRoot, Any] | None:
    """Join an exact parser-reported free root token to TemplateData."""
    by_name = {_identifier_key(root.name): root for root in roots}
    for use in template.used_variables:
        if use.start_index <= index < use.end_index:
            root = by_name.get(_identifier_key(use.content))
            if root is not None:
                return root, use
    return None


def _template_variable_origin_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...] | None:
    """Resolve the authored declaration of one exact Citry-owned variable."""
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    parsed = document.parsed.get(region.key)
    if parsed is None:
        return None

    lexical = _lexical_reference_at(parsed.template, parser_index)
    if lexical is not None:
        return (
            types.Location(
                document.uri,
                _range(
                    region.source_map.map_range(
                        lexical.binding.start_index,
                        lexical.binding.end_index,
                    )
                ),
            ),
        )

    if project.catalog is None:
        return None
    field_reference = _template_data_reference_at(
        parsed.template,
        parser_index,
        _template_data_roots(document, region, project, open_documents),
    )
    if field_reference is None:
        return None
    root, _use = field_reference
    if not _template_root_fields_are_current(root, open_documents):
        return None
    return _template_root_locations(root, open_documents)


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


def _template_root_detail(root: _TemplateRoot) -> str:
    if root.access == "analysis":
        detail = _template_root_provenance(root).removesuffix(".")
    elif "TemplateData" in root.origins:
        detail = "TemplateData"
    else:
        detail = "Inferred from template_data()"
    if root.type_field is not None:
        detail += f" · {_field_detail(root.type_field)}"
    if root.presence == "conditional":
        detail += " · conditional"
    return detail


def _template_root_provenance(root: _TemplateRoot) -> str:
    if root.access == "analysis":
        if len(root.origins) == 1:
            return next(iter(root.origins)).capitalize() + "."
        return "Known template namespace variable."
    has_schema = "TemplateData" in root.origins
    has_return = "template_data()" in root.origins
    if has_schema and has_return:
        detail = "Proven by TemplateData and template_data()"
    elif has_schema:
        detail = "TemplateData field"
    elif "Kwargs" in root.origins and root.fallback_types is not None:
        detail = "Inferred from template_data() via Kwargs"
    else:
        detail = "Inferred from template_data()"
    if root.type_field is not None:
        detail += " · required" if root.type_field.required else " · optional"
    if root.presence == "conditional":
        detail += " · conditional"
    return detail


def _template_root_fallback_types(root: _TemplateRoot) -> tuple[str, ...]:
    if root.fallback_types is None:
        return ()
    return root.fallback_types


def _join_root_fallback_types(left: _TemplateRoot, right: _TemplateRoot) -> tuple[str, ...] | None:
    # A shared fallback is complete only when every consumer supplied presentation text.
    if left.fallback_types is None or right.fallback_types is None:
        return None
    return tuple(dict.fromkeys((*left.fallback_types, *right.fallback_types)))


def _safe_hover_types(values: tuple[str, ...]) -> tuple[str, ...]:
    retained: list[str] = []
    for value in values:
        candidate = value.strip()
        # One declaration line cannot safely embed Markdown fences or analyzer declarations.
        if (
            not candidate
            or "\n" in candidate
            or "\r" in candidate
            or "```" in candidate
            or _hover_type_contains_unknown(candidate)
            or re.match(r"^\([A-Za-z][A-Za-z -]*\)\s+", candidate) is not None
            or candidate.startswith(("def ", "async def ", "class ", "@", "<"))
        ):
            return ()
        if candidate not in retained:
            retained.append(candidate)
    return tuple(retained)


def _hover_type_contains_unknown(value: str) -> bool:
    # Token identity distinguishes ty's uncertainty marker from a quoted literal value.
    try:
        tokens = tokenize.generate_tokens(io.StringIO(value).readline)
        return any(token.type == tokenize.NAME and token.string == "Unknown" for token in tokens)
    except tokenize.TokenError:
        return True


def _join_hover_types(values: tuple[str, ...]) -> str:
    if len(values) == 1:
        return values[0]
    # Parentheses retain each analyzer answer when one consumer already has a union.
    return " | ".join(f"({value})" if " | " in value else value for value in values)


def _template_root_description(root: _TemplateRoot) -> str | None:
    if root.description is not None:
        return root.description
    return root.type_field.description if root.type_field is not None else None


def _template_root_hover_description(root: _TemplateRoot) -> str | None:
    paragraphs: list[str] = []
    description = _template_root_description(root)
    if description:
        paragraphs.append(description)
    if root.presence == "conditional":
        paragraphs.append("This root is returned only on some statically visible paths.")
    return "\n\n".join(paragraphs) or None


def _template_root_locations(
    root: _TemplateRoot,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    locations = list(root.locations)
    for definition in root.lint_definitions:
        location = _lint_definition_location(definition, open_documents)
        if location is not None:
            locations.append(location)
    for schema_field in root.fields:
        synchronized: str | None = None
        if schema_field.source_file is not None and open_documents is not None:
            found, synchronized = _synchronized_document_source(schema_field.source_file, open_documents)
            if found and synchronized is None:
                continue
        location = _field_definition_location(schema_field, source=synchronized)
        if location is not None:
            locations.append(location)
    return _dedupe_locations(tuple(locations))


def _lint_definition_location(
    definition: SourceLintRecord,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Location | None:
    """Revalidate one copied lint key against synchronized Python source."""
    source: str | None = None
    if open_documents is not None:
        found, source = _synchronized_document_source(definition.source_file, open_documents)
        if found and source is None:
            return None
    if source is None:
        try:
            with tokenize.open(definition.source_file) as source_stream:
                source = source_stream.read()
        except (OSError, SyntaxError, UnicodeError):
            return None
    if definition.kind == "application":
        source_range = python_application_lint_variable_range(source, definition.owner, definition.name)
    else:
        source_range = python_component_lint_variable_range(source, definition.owner, definition.name)
    if source_range is None:
        return None
    return types.Location(definition.source_file.resolve().as_uri(), _range(source_range))


def _template_root_fields_are_current(
    root: _TemplateRoot,
    open_documents: Mapping[str, DocumentState] | None,
) -> bool:
    """Reject catalog fields contradicted by synchronized Python source."""
    if open_documents is None:
        return True
    for schema_field in root.fields:
        if (
            schema_field.source_file is None
            or schema_field.source_module is None
            or schema_field.source_qualname is None
        ):
            continue
        found, synchronized = _synchronized_document_source(schema_field.source_file, open_documents)
        if found and (synchronized is None or _field_definition_location(schema_field, source=synchronized) is None):
            return False
    return True


def _current_template_schema_names(
    component: ComponentRecord,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> frozenset[str] | None:
    """Read newly authored schema names or decline invalid synchronized Python."""
    if open_documents is None:
        return frozenset()
    schema = component.schemas.template_data
    candidates: set[tuple[Path, str]] = set()
    for schema_field in schema.fields:
        if schema_field.source_file is not None and schema_field.source_qualname is not None:
            candidates.add((schema_field.source_file.resolve(), schema_field.source_qualname))
    if component.python_file is not None and component.module is not None and schema.import_path is not None:
        prefix = f"{component.module}."
        if schema.import_path.startswith(prefix):
            candidates.add((component.python_file.resolve(), schema.import_path[len(prefix) :]))
    if component.python_file is not None and component.qualname is not None:
        candidates.add((component.python_file.resolve(), f"{component.qualname}.TemplateData"))
    if project.source_analysis is not None:
        chain = project.source_analysis.template_data_chain(component)
        if chain is not None:
            for item in chain:
                if schema.import_path is not None and schema.import_path.startswith(f"{item.module}."):
                    candidates.add(
                        (
                            item.source_file.resolve(),
                            schema.import_path[len(item.module) + 1 :],
                        )
                    )
                candidates.add((item.source_file.resolve(), f"{item.qualname}.TemplateData"))

    names: set[str] = set()
    parsed_sources: dict[Path, ast.Module] = {}
    for source_file, qualname in candidates:
        found, source = _synchronized_document_source(source_file, open_documents)
        if not found:
            continue
        if source is None:
            return None
        tree = parsed_sources.get(source_file)
        if tree is None:
            try:
                tree = ast.parse(source)
            except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
                return None
            parsed_sources[source_file] = tree
        class_node = _class_node_for_qualname(tree, qualname)
        if class_node is not None:
            names.update(_direct_schema_field_names(class_node))
    return frozenset(names)


def _direct_schema_field_names(class_node: ast.ClassDef) -> set[str]:
    """Collect direct annotated fields while excluding ClassVar declarations."""
    names: set[str] = set()
    for statement in class_node.body:
        if not isinstance(statement, ast.AnnAssign) or not isinstance(statement.target, ast.Name):
            continue
        annotation = statement.annotation
        base = annotation.value if isinstance(annotation, ast.Subscript) else annotation
        if (isinstance(base, ast.Name) and base.id == "ClassVar") or (
            isinstance(base, ast.Attribute) and base.attr == "ClassVar"
        ):
            continue
        names.add(statement.target.id)
    return names


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
    _found, source = _synchronized_document_source(source_file, open_documents)
    return source


def _synchronized_document_source(
    source_file: Path,
    open_documents: Mapping[str, DocumentState],
) -> tuple[bool, str | None]:
    """Return synchronized source and decline conflicting URI aliases."""
    canonical = source_file.resolve()
    candidates: list[str] = []
    for document in open_documents.values():
        path = file_uri_path(document.uri)
        if path is None:
            continue
        try:
            document_path = path.resolve()
        except (OSError, ValueError):
            continue
        if document_path == canonical:
            candidates.append(document.source)
    if not candidates:
        return False, None
    if any(source != candidates[0] for source in candidates[1:]):
        return True, None
    return True, candidates[0]


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


def _source_offset_at_position(source: str, position: types.Position) -> int | None:
    """Translate an LSP position without accepting half of an astral character."""
    if position.line < 0 or position.character < 0:
        return None
    lines = source.splitlines(keepends=True)
    if position.line >= len(lines):
        return None
    prefix = sum(len(line) for line in lines[: position.line])
    line = lines[position.line].removesuffix("\n").removesuffix("\r")
    units = 0
    for index, char in enumerate(line):
        if units == position.character:
            return prefix + index
        units += _utf16_units(char)
        if units > position.character:
            return None
    return prefix + len(line) if units == position.character else None


def _markdown(value: str | None) -> types.MarkupContent | None:
    return types.MarkupContent(types.MarkupKind.Markdown, value) if value else None


def _char_to_byte(source: str, index: int) -> int:
    return len(source[:index].encode("utf-8"))


def _citry_position(position: types.Position) -> LspPosition:
    return LspPosition(position.line, position.character)


def _position(position: LspPosition) -> types.Position:
    return types.Position(position.line, position.character)


def _range(value: LspRange) -> types.Range:
    return types.Range(
        types.Position(value.start.line, value.start.character),
        types.Position(value.end.line, value.end.character),
    )


def _position_dict(position: types.Position) -> dict[str, int]:
    return {"line": position.line, "character": position.character}


def _range_dict(value: types.Range) -> dict[str, object]:
    return {
        "start": _position_dict(value.start),
        "end": _position_dict(value.end),
    }


def _zero_range() -> types.Range:
    return types.Range(types.Position(0, 0), types.Position(0, 0))


__all__ = [
    "BrowserProjection",
    "CompletionResult",
    "DocumentState",
    "ExpressionShadow",
    "ExpressionShadowGroup",
    "HtmlProjection",
    "ParsedRegion",
    "SemanticDependencies",
    "TemplateVariableHover",
    "all_expression_shadows",
    "browser_diagnostics",
    "browser_projection",
    "completion_items",
    "completion_result",
    "declaration",
    "definition",
    "document_symbols",
    "expression_completion_ranges",
    "expression_shadows",
    "hover",
    "html_projection",
    "map_expression_shadow_range",
    "references",
    "render_template_variable_hover",
    "semantic_dependencies",
    "template_lint_diagnostics",
    "template_variable_hover",
]
