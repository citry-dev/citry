"""Parser-backed diagnostics and narrow editor intelligence."""

from __future__ import annotations

import ast
import io
import json
import re
import tokenize
import unicodedata
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from lsprotocol import types

from citry import LspPosition, LspRange
from citry._diagnostic_catalog import (
    BROWSER_INCOMPATIBLE_COMPONENT_PROP,
    BROWSER_MISSING_COMPONENT_PROP,
    BROWSER_UNKNOWN_COMPONENT_PROP,
    BROWSER_UNKNOWN_SERVER_EVENT,
    I18N_ARGUMENT_INVALID,
    I18N_CATALOG_INVALID,
    I18N_UNKNOWN_MESSAGE,
    JS_DATA_UNSUPPORTED_TYPE,
    PARSE_CONFIGURATION,
    TEMPLATE_UNKNOWN_COMPONENT,
)
from citry._diagnostics import diagnostic_documentation_url, render_diagnostic
from citry._i18n_directives import looks_like_i18n_binding
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
    browser_i18n_bind_calls,
    browser_i18n_binding_directives,
    browser_i18n_message_calls,
    browser_i18n_profile_calls,
    browser_identifier_at,
    browser_identifiers,
    browser_literal_calls,
    browser_literal_wire_type,
    browser_member_at,
    build_inferred_template_shadow,
    build_schema_template_shadow,
    component_name_match,
    css_data_completion_at,
    css_data_reference_at,
    css_data_references,
    json_wire_type_from_annotation,
    json_wire_type_from_expression,
    lint_csp_compatibility,
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
    unknown_component_uses,
)
from citry_core.i18n import CatalogCompiler, I18nCompileError
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
    MessagesRegion,
    TemplateRegion,
    css_region_at_position,
    discover_python_css_regions,
    discover_python_js_regions,
    discover_python_messages_regions,
    discover_python_regions,
    document_offset_at,
    document_range_for_offsets,
    js_region_at_position,
    parser_char_index,
    python_messages_source_map,
    region_at_position,
    standalone_css_region,
    standalone_js_region,
    standalone_region,
)
from citry_lsp.uri import file_uri_path

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry._linting import TemplateVariableInfo
    from citry._template_data_source import TemplateDataSourceShape
    from citry_lsp.catalog import CatalogIndex, ComponentRecord, FieldRecord, SchemaRecord
    from citry_lsp.project import (
        I18nOutputRecord,
        I18nParameterDeclarationRecord,
        ProjectState,
        SourceEventRecord,
        SourceLintRecord,
        SourceStateFieldRecord,
    )


_I18N_SOURCE_COMPILER = CatalogCompiler()

_I18N_CALL_SIGNATURES: dict[
    tuple[str, str],
    tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]],
] = {
    ("format", "number"): (("value",), ("format",), ()),
    ("format", "percent"): (("value",), ("format",), ()),
    ("format", "currency"): (("value", "currency"), ("format",), ()),
    ("format", "date"): (("value",), ("format",), ()),
    ("format", "time"): (("value",), ("format",), ()),
    ("format", "datetime"): (("value",), ("format",), ()),
    ("format", "relative_time"): (("value",), ("unit", "format"), ()),
    ("format", "list"): (("values",), ("format",), ()),
    ("format", "unit"): (("value", "unit"), ("format",), ()),
    ("parse", "number"): (("input",), ("format",), ()),
    ("parse", "percent"): (("input",), ("format",), ()),
    ("parse", "date"): (("input",), ("format",), ()),
    ("parse", "date_segments"): (("input",), ("format",), ()),
    ("parse", "time"): (("input",), ("format",), ()),
    ("parse", "time_segments"): (("input",), ("format",), ()),
    ("parse", "datetime"): (("input",), ("format",), ("fold",)),
    ("parse", "datetime_segments"): (("input",), ("format",), ("fold",)),
}
_I18N_PROFILE_OPERATION_NAMES = {
    "date_segments": "date",
    "time_segments": "time",
    "datetime_segments": "datetime",
}
_I18N_OPERATION_SIGNATURES = {
    ("format", "number"): "number(value: object, *, format: str) -> str",
    ("format", "percent"): "percent(value: object, *, format: str) -> str",
    ("format", "currency"): "currency(value: object, currency: str, *, format: str) -> str",
    ("format", "date"): "date(value: object, *, format: str) -> str",
    ("format", "time"): "time(value: object, *, format: str) -> str",
    ("format", "datetime"): "datetime(value: object, *, format: str) -> str",
    ("format", "relative_time"): "relative_time(value: object, *, unit: str, format: str) -> str",
    ("format", "list"): "list(values: object, *, format: str) -> str",
    ("format", "unit"): "unit(value: object, unit: str, *, format: str) -> str",
    ("parse", "number"): "number(input: str, *, format: str) -> NumericParseResult",
    ("parse", "percent"): "percent(input: str, *, format: str) -> NumericParseResult",
    ("parse", "date"): "date(input: str, *, format: str) -> DateParseResult",
    ("parse", "date_segments"): "date_segments(input: object, *, format: str) -> DateParseResult",
    ("parse", "time"): "time(input: str, *, format: str) -> TimeParseResult",
    ("parse", "time_segments"): "time_segments(input: object, *, format: str) -> TimeParseResult",
    ("parse", "datetime"): "datetime(input: str, *, format: str, fold: int | None = None) -> DatetimeParseResult",
    ("parse", "datetime_segments"): (
        "datetime_segments(input: object, *, format: str, fold: int | None = None) -> DatetimeParseResult"
    ),
}


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
class _I18nUse:
    """One exact message key or named profile under the cursor."""

    kind: Literal["message", "operation", "parameter", "profile", "term"]
    value: str
    range: types.Range
    attribute: str | None = None
    namespace: Literal["format", "parse"] | None = None
    operation: str | None = None
    completable: bool = True
    source_unit: str | None = None
    message: str | None = None


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
    authored_name: str
    start_index: int
    end_index: int


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
    analysis_preamble: str = ""


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
    """One recognized tag or attribute together with its authored span."""

    spec: _SyntaxSpec
    start_index: int
    end_index: int
    display_label: str | None = None


@dataclass(frozen=True, slots=True)
class _CitryBindingReference:
    """One base name or modifier segment inside a Citry-owned binding key."""

    channel: Literal["event", "state"]
    attribute_name: str
    base_name: str
    part: Literal["base", "modifier"]
    value: str
    previous_modifier: str | None
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
    messages_regions: tuple[MessagesRegion, ...] = ()
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
        self.messages_regions = discover_python_messages_regions(source) if self.language_id == "python" else ()
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


def i18n_diagnostics(
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> tuple[types.Diagnostic, ...]:
    """Report current Fluent-source and literal i18n API mistakes."""
    index = project.i18n
    if index is None or not index.available:
        return ()
    diagnostics: list[types.Diagnostic] = []
    for messages_region in document.messages_regions:
        if not _registered_messages_region(document, messages_region, project):
            continue
        try:
            _I18N_SOURCE_COMPILER.analyze_source(
                f"{file_uri_path(document.uri) or document.uri}::{messages_region.component_name}.messages",
                messages_region.source_map.template_source,
            )
        except I18nCompileError as error:
            diagnostic = _i18n_compile_diagnostic(error)
            if diagnostic is None:
                continue
            start, end, message = diagnostic
            try:
                mapped = messages_region.source_map.map_range(start, end)
            except ValueError:
                continue
            diagnostics.append(
                _i18n_diagnostic(
                    _range(mapped),
                    message,
                    I18N_CATALOG_INVALID,
                )
            )

    if document.language_id == "python":
        diagnostics.extend(_python_i18n_diagnostics(document.source, index))
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    for template_region in document.regions:
        parsed = document.parsed.get(template_region.key)
        if parsed is None:
            continue
        known_types = _i18n_template_known_types(document, template_region, project, open_documents)
        for query in template_python_queries(parsed.template, parse_nested=parser):
            for start, end, message, code in _i18n_call_findings(
                query.source,
                index,
                template=True,
                known_types=known_types,
            ):
                try:
                    mapped = template_region.source_map.map_range(query.start_index + start, query.start_index + end)
                except ValueError:
                    continue
                diagnostics.append(_i18n_diagnostic(_range(mapped), message, code))
        diagnostics.extend(_trans_i18n_diagnostics(parsed.template, template_region, index, known_types))
    return tuple(diagnostics)


def _registered_messages_region(
    document: DocumentState,
    region: MessagesRegion,
    project: ProjectState,
) -> bool:
    """Require runtime-backed ownership before treating a string as Fluent."""
    document_path = file_uri_path(document.uri)
    if document_path is None or project.catalog is None:
        return False
    try:
        expected = document_path.resolve()
    except OSError:
        return False
    return any(
        component.python_file is not None
        and component.python_file.resolve() == expected
        and component.class_name == region.component_name
        for component in project.catalog.components
    )


def _i18n_template_known_types(
    document: DocumentState,
    region: TemplateRegion,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> dict[str, str]:
    """Join only exact template-root types proven for every asset consumer."""
    consumers = _template_consumers(document, region, project, open_documents)
    if not consumers:
        return {}
    resolved: list[dict[str, str]] = []
    for component in consumers:
        context = _component_template_context(component, project, document, open_documents)
        if context is None:
            return {}
        current: dict[str, str] = {}
        for root in context.roots:
            candidates = tuple(
                dict.fromkeys(
                    value
                    for value in (
                        root.type_field.type_display if root.type_field is not None else None,
                        root.shadow_type_display,
                        *(root.fallback_types or ()),
                    )
                    if value is not None
                )
            )
            if len(candidates) == 1:
                current[root.name] = candidates[0]
        resolved.append(current)
    common = resolved[0]
    for candidate in resolved[1:]:
        common = {name: value for name, value in common.items() if candidate.get(name) == value}
    return common


def _i18n_compile_diagnostic(error: I18nCompileError) -> tuple[int, int, str] | None:
    try:
        payload = json.loads(error.diagnostic_json)
    except (AttributeError, TypeError, ValueError):
        return None
    start = payload.get("start")
    end = payload.get("end")
    message = payload.get("message")
    if type(start) is not int or type(end) is not int or end <= start or type(message) is not str:
        return None
    return start, end, message


def _python_i18n_diagnostics(source: str, index: Any) -> list[types.Diagnostic]:
    diagnostics: list[types.Diagnostic] = []
    for start, end, message, code in _i18n_call_findings(source, index, template=False):
        try:
            start_char = parser_char_index(source, start)
            end_char = parser_char_index(source, end)
        except ValueError:
            continue
        diagnostics.append(
            _i18n_diagnostic(
                _range(document_range_for_offsets(source, start_char, end_char)),
                message,
                code,
            )
        )
    return diagnostics


def _i18n_call_findings(
    source: str,
    index: Any,
    *,
    template: bool,
    known_types: Mapping[str, str] | None = None,
) -> list[tuple[int, int, str, str]]:
    # Multiline interpolation queries retain the indentation before their
    # closing delimiter. It is outside the expression and must not make an
    # otherwise valid formatter call fail Python parsing.
    parsed_source = source.rstrip() if template else source
    try:
        tree = ast.parse(parsed_source, mode="eval" if template else "exec")
    except (SyntaxError, TypeError, ValueError):
        return []
    findings: list[tuple[int, int, str, str]] = []
    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        start, end = _python_ast_byte_range(source, call)
        if _python_message_call(call.func, template=template):
            findings.extend(_literal_message_call_findings(call, index, start, end, known_types=known_types))
            continue
        target = _python_profile_call(call.func, template=template)
        if target is None:
            continue
        namespace, operation = target
        signature_issue = _i18n_profile_signature_issue(call, namespace, operation)
        if signature_issue is not None:
            findings.append((start, end, signature_issue, I18N_ARGUMENT_INVALID))
        if (namespace, operation) not in _I18N_CALL_SIGNATURES:
            continue
        profile = next((keyword.value for keyword in call.keywords if keyword.arg == "format"), None)
        if not isinstance(profile, ast.Constant) or type(profile.value) is not str:
            continue
        profile_operation = _I18N_PROFILE_OPERATION_NAMES.get(operation, operation)
        known = index.profile_names(namespace, profile_operation)
        if cast("str", profile.value) not in known:
            available = ", ".join(repr(item) for item in known) or "none"
            findings.append(
                (
                    start,
                    end,
                    f"Unknown i18n {namespace} profile {profile.value!r} for {operation}; "
                    f"configured profiles: {available}.",
                    I18N_ARGUMENT_INVALID,
                )
            )
    return findings


def _i18n_profile_signature_issue(call: ast.Call, namespace: str, operation: str) -> str | None:
    """Validate the closed Python/template formatter and parser call shape."""
    signature = _I18N_CALL_SIGNATURES.get((namespace, operation))
    if signature is None:
        return f"Unknown i18n {namespace} operation {operation!r}."
    positional_names, required_keywords, optional_keywords = signature
    spread_positionals = any(isinstance(argument, ast.Starred) for argument in call.args)
    concrete_positionals = [argument for argument in call.args if not isinstance(argument, ast.Starred)]
    spread_keywords = any(keyword.arg is None for keyword in call.keywords)
    keyword_names = [keyword.arg for keyword in call.keywords if keyword.arg is not None]
    valid_keywords = {*positional_names, *required_keywords, *optional_keywords}
    issues: list[str] = []
    if not spread_positionals and len(concrete_positionals) > len(positional_names):
        issues.append(
            f"expected at most {len(positional_names)} positional argument(s), got {len(concrete_positionals)}"
        )
    unknown = sorted(set(keyword_names) - valid_keywords)
    if unknown:
        issues.append(f"unknown argument(s): {', '.join(unknown)}")
    bound_positionals = set(positional_names[: len(concrete_positionals)])
    duplicates = sorted(bound_positionals & set(keyword_names))
    if duplicates:
        issues.append(f"argument(s) passed twice: {', '.join(duplicates)}")
    if not spread_positionals and not spread_keywords:
        supplied = bound_positionals | set(keyword_names)
        missing = [name for name in (*positional_names, *required_keywords) if name not in supplied]
        if missing:
            issues.append(f"missing argument(s): {', '.join(missing)}")
    return f"i18n {namespace}.{operation}() has {'; '.join(issues)}." if issues else None


def _python_ast_byte_range(source: str, node: ast.expr) -> tuple[int, int]:
    end_line = node.end_lineno if node.end_lineno is not None else node.lineno
    end_column = node.end_col_offset if node.end_col_offset is not None else node.col_offset
    return (
        _python_ast_byte_offset(source, node.lineno, node.col_offset),
        _python_ast_byte_offset(source, end_line, end_column),
    )


def _literal_message_call_findings(
    call: ast.Call,
    index: Any,
    start: int,
    end: int,
    *,
    known_types: Mapping[str, str] | None = None,
) -> list[tuple[int, int, str, str]]:
    if not call.args or not isinstance(call.args[0], ast.Constant) or type(call.args[0].value) is not str:
        return []
    message = cast("str", call.args[0].value)
    attribute_expression = next((keyword.value for keyword in call.keywords if keyword.arg == "attr"), None)
    attribute = None
    if attribute_expression is not None:
        if not isinstance(attribute_expression, ast.Constant):
            return []
        if attribute_expression.value is not None and type(attribute_expression.value) is not str:
            return []
        attribute = cast("str | None", attribute_expression.value)
    output = index.output(message, attribute)
    token = message if attribute is None else f"{message}.{attribute}"
    if output is None:
        return [
            (
                start,
                end,
                f"Unknown i18n message ID {token!r}; no component or configured catalog package defines it.",
                I18N_UNKNOWN_MESSAGE,
            )
        ]
    expected = {parameter.name: parameter.type_name for parameter in output.parameters}
    explicit = {
        keyword.arg: keyword.value for keyword in call.keywords if keyword.arg is not None and keyword.arg != "attr"
    }
    has_spread = any(keyword.arg is None for keyword in call.keywords)
    issues: list[str] = []
    if len(call.args) != 1:
        issues.append("tr() accepts only the message ID as a positional argument")
    unknown = sorted(set(explicit) - set(expected))
    missing = sorted(set(expected) - set(explicit)) if not has_spread else []
    if unknown:
        issues.append(f"unknown argument(s): {', '.join(unknown)}")
    if missing:
        issues.append(f"missing argument(s): {', '.join(missing)}")
    for name in sorted(set(explicit) & set(expected)):
        mismatch = _literal_i18n_expression_mismatch(expected[name], explicit[name], known_types=known_types)
        if mismatch is not None:
            issues.append(f"argument {name!r} {mismatch}")
    return [(start, end, f"i18n output {token!r} has {'; '.join(issues)}.", I18N_ARGUMENT_INVALID)] if issues else []


def _literal_i18n_expression_mismatch(
    expected: str,
    expression: ast.expr,
    *,
    known_types: Mapping[str, str] | None = None,
) -> str | None:
    if expected == "Slot":
        return "is structural and must be supplied through <c-trans>"
    if isinstance(expression, ast.Name) and known_types is not None:
        actual = known_types.get(expression.id)
        if actual is not None and not _i18n_type_accepts(expected, actual):
            return f"must be {expected}, not {actual}"
        return None
    if not isinstance(expression, ast.Constant):
        return None
    value = expression.value
    if expected == "str" and type(value) is not str:
        return f"must be str, not {type(value).__name__}"
    if expected == "scalar" and type(value) not in {str, int}:
        return f"must be str, int, or Decimal, not {type(value).__name__}"
    if expected == "int" and type(value) is not int:
        return f"must be int, not {type(value).__name__}"
    if expected in {"Decimal", "datetime"}:
        return f"must be an explicit {expected} value, not a literal {type(value).__name__}"
    return None


def _i18n_type_accepts(expected: str, actual: str) -> bool:
    short = actual.rsplit(".", maxsplit=1)[-1]
    if expected == "scalar":
        return short in {"str", "int", "Decimal"}
    return short == expected


def _trans_i18n_diagnostics(
    template: Any,
    region: TemplateRegion,
    index: Any,
    known_types: Mapping[str, str],
) -> list[types.Diagnostic]:
    diagnostics: list[types.Diagnostic] = []
    for node in _trans_nodes(template):
        attrs = {attr.key.content: attr for attr in node.start_tag.attrs}
        message_attr = attrs.get("message")
        if message_attr is None or message_attr.inner_value is None:
            continue
        message = message_attr.inner_value.content
        attribute_attr = attrs.get("attr")
        attribute = (
            attribute_attr.inner_value.content
            if attribute_attr is not None and attribute_attr.inner_value is not None
            else None
        )
        token = message if attribute is None else f"{message}.{attribute}"
        output = index.output(message, attribute)
        mapped = _range(
            region.source_map.map_range(
                message_attr.inner_value.start_index,
                message_attr.inner_value.end_index,
            )
        )
        if output is None:
            diagnostics.append(
                _i18n_diagnostic(
                    mapped,
                    f"Unknown i18n message ID {token!r}; no component or configured catalog package defines it.",
                    I18N_UNKNOWN_MESSAGE,
                )
            )
            continue
        interface = {parameter.name: parameter.type_name for parameter in output.parameters}
        scalar_names = {name for name, type_name in interface.items() if type_name != "Slot"}
        slot_names = {name for name, type_name in interface.items() if type_name == "Slot"}
        values = _literal_trans_values(attrs.get("c-values"))
        fills = _trans_fill_names(node)
        issues: list[str] = []
        if values is not None:
            unknown_values = sorted(set(values) - scalar_names)
            missing_values = sorted(scalar_names - set(values))
            if unknown_values:
                issues.append(f"unknown values: {', '.join(unknown_values)}")
            if missing_values:
                issues.append(f"missing values: {', '.join(missing_values)}")
            for name in sorted(set(values) & scalar_names):
                mismatch = _literal_i18n_expression_mismatch(
                    interface[name],
                    values[name],
                    known_types=known_types,
                )
                if mismatch is not None:
                    issues.append(f"value {name!r} {mismatch}")
        unknown_fills = sorted(fills - slot_names)
        missing_fills = sorted(slot_names - fills)
        if unknown_fills:
            issues.append(f"unknown fills: {', '.join(unknown_fills)}")
        if missing_fills:
            issues.append(f"missing fills: {', '.join(missing_fills)}")
        if values is not None:
            collisions = sorted(fills & set(values))
            if collisions:
                issues.append(f"names used by both values and fills: {', '.join(collisions)}")
        if issues:
            diagnostics.append(
                _i18n_diagnostic(
                    mapped,
                    f"<c-trans> output {token!r} has {'; '.join(issues)}.",
                    I18N_ARGUMENT_INVALID,
                )
            )
    return diagnostics


def _trans_nodes(template: Any) -> list[Any]:
    nodes: list[Any] = []
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        if node.start_tag.name.content.lower() == "c-trans":
            nodes.append(node)
        body = getattr(node, "body", None)
        if body is not None:
            nodes.extend(_trans_nodes(body))
    return nodes


def _literal_trans_values(attribute: Any | None) -> dict[str, ast.expr] | None:
    if attribute is None or attribute.inner_value is None:
        return {}
    try:
        expression = ast.parse(attribute.inner_value.content, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(expression, ast.Dict) or not all(
        key is not None and isinstance(key, ast.Constant) and type(key.value) is str for key in expression.keys
    ):
        return None
    return {
        cast("str", key.value): value
        for key, value in zip(expression.keys, expression.values, strict=True)
        if isinstance(key, ast.Constant) and type(key.value) is str
    }


def _trans_fill_names(node: Any) -> set[str]:
    fills: set[str] = set()
    body = getattr(node, "body", None)
    if body is None:
        return fills
    for element in body.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        fill = element._0
        if fill.start_tag.name.content.lower() != "c-fill":
            continue
        name = next((attr for attr in fill.start_tag.attrs if attr.key.content == "name"), None)
        if name is not None and name.inner_value is not None:
            fills.add(name.inner_value.content)
    return fills


def _i18n_diagnostic(range_: types.Range, message: str, code: str) -> types.Diagnostic:
    return types.Diagnostic(
        range=range_,
        message=message,
        severity=types.DiagnosticSeverity.Error,
        code=code,
        code_description=types.CodeDescription(diagnostic_documentation_url(code)),
        source="citry",
    )


def browser_diagnostics(
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> tuple[types.Diagnostic, ...]:
    """Report Citry-owned JsData and literal server-event problems."""
    diagnostics = list(_js_data_type_diagnostics(document, project, open_documents))
    parser = project.analysis.parse_template if project.analysis is not None else parse_template
    for region in document.regions:
        parsed = document.parsed.get(region.key)
        if parsed is None:
            continue
        for directive in browser_i18n_binding_directives(parsed.template, parse_nested=parser):
            if directive.error is None:
                continue
            start = directive.error_start_index or directive.name_start_index
            end = directive.error_end_index or directive.name_end_index
            diagnostics.append(
                _browser_diagnostic(
                    region,
                    start,
                    max(start, end),
                    I18N_ARGUMENT_INVALID,
                    detail=directive.error,
                )
            )
    if project.catalog is None or project.source_analysis is None:
        return tuple(diagnostics)
    for region in document.regions:
        parsed = document.parsed.get(region.key)
        if parsed is None:
            continue
        consumers = _template_consumers(document, region, project, open_documents)
        if not consumers:
            continue
        expressions = browser_expressions(parsed.template, parse_nested=parser)
        roots = _template_js_data_roots(document, region, project, open_documents)
        diagnostics.extend(
            _i18n_binding_diagnostics(
                region,
                parsed.template,
                project,
                roots,
                expressions,
                parser=parser,
            )
        )
        for expression in expressions:
            diagnostics.extend(
                _browser_i18n_profile_diagnostics(
                    expression,
                    region,
                    project,
                    owners=frozenset({"$i18n"}),
                )
            )
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
        for csp_finding in lint_csp_compatibility(
            expressions,
            alpine_consumers or (),
            project.security_csp,
        ):
            diagnostics.append(
                types.Diagnostic(
                    range=_range(region.source_map.map_range(csp_finding.start_index, csp_finding.end_index)),
                    message=csp_finding.message,
                    severity=(
                        types.DiagnosticSeverity.Error
                        if csp_finding.severity == "error"
                        else types.DiagnosticSeverity.Warning
                    ),
                    code=csp_finding.code,
                    code_description=types.CodeDescription(diagnostic_documentation_url(csp_finding.code)),
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
        if not js_consumers:
            continue
        js_expression = _component_js_expression(js_region)
        diagnostics.extend(
            _browser_i18n_profile_diagnostics(
                js_expression,
                js_region,
                project,
                owners=frozenset({"i18n"}),
            )
        )
        if js_event_contract is None:
            continue
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


def _browser_i18n_profile_diagnostics(
    expression: BrowserExpression,
    region: TemplateRegion | JsRegion,
    project: ProjectState,
    *,
    owners: frozenset[str],
) -> list[types.Diagnostic]:
    index = project.i18n
    if index is None or not index.configured:
        return []
    if "$i18n" in owners and "$i18n" not in expression.bindings:
        return []
    operation_names = {"relativeTime": "relative_time"}
    diagnostics: list[types.Diagnostic] = []
    for call in browser_i18n_message_calls(expression, owners):
        if call.has_dynamic_attribute:
            continue
        output = index.output(call.message, call.attribute)
        token = call.message if call.attribute is None else f"{call.message}.{call.attribute}"
        try:
            call_range = _range(region.source_map.map_range(call.message_start_index, call.message_end_index))
        except ValueError:
            continue
        if output is None:
            diagnostics.append(
                _i18n_diagnostic(
                    call_range,
                    f"Unknown i18n message ID {token!r}; no component or configured catalog package defines it.",
                    I18N_UNKNOWN_MESSAGE,
                )
            )
            continue
        expected = {parameter.name for parameter in output.parameters}
        supplied = {argument.name for argument in call.arguments}
        unknown = sorted(supplied - expected)
        missing = sorted(expected - supplied) if not call.has_dynamic_arguments else []
        if not unknown and not missing:
            continue
        details: list[str] = []
        if unknown:
            details.append(f"unknown argument(s): {', '.join(unknown)}")
        if missing:
            details.append(f"missing argument(s): {', '.join(missing)}")
        diagnostics.append(
            _i18n_diagnostic(
                call_range,
                f"i18n output {token!r} has {'; '.join(details)}.",
                I18N_ARGUMENT_INVALID,
            )
        )
    for bind_call in browser_i18n_bind_calls(expression, owners):
        if bind_call.has_dynamic_output:
            continue
        output = index.output(bind_call.message, bind_call.output)
        if output is not None:
            continue
        token = bind_call.message if bind_call.output is None else f"{bind_call.message}.{bind_call.output}"
        diagnostics.append(
            _i18n_diagnostic(
                _range(
                    region.source_map.map_range(
                        bind_call.message_start_index,
                        bind_call.message_end_index,
                    )
                ),
                f"Unknown i18n message ID {token!r}; no component or configured catalog package defines it.",
                I18N_UNKNOWN_MESSAGE,
            )
        )
    for profile_call in browser_i18n_profile_calls(expression, owners):
        operation = operation_names.get(profile_call.operation, profile_call.operation)
        known = index.profile_names(profile_call.namespace, operation)
        if profile_call.profile in known:
            continue
        available = ", ".join(repr(item) for item in known) or "none"
        diagnostics.append(
            _i18n_diagnostic(
                _range(region.source_map.map_range(profile_call.start_index, profile_call.end_index)),
                f"Unknown i18n {profile_call.namespace} profile {profile_call.profile!r} for {operation}; "
                f"configured profiles: {available}.",
                I18N_ARGUMENT_INVALID,
            )
        )
    return diagnostics


def _i18n_binding_diagnostics(
    region: TemplateRegion,
    template: Any,
    project: ProjectState,
    roots: tuple[_JsDataRoot, ...],
    expressions: tuple[BrowserExpression, ...],
    *,
    parser: Any,
) -> list[types.Diagnostic]:
    """Check static `$c-tr` outputs and named JavaScript values."""
    index = project.i18n
    if index is None or not index.available:
        return []
    diagnostics: list[types.Diagnostic] = []
    for directive in browser_i18n_binding_directives(template, parse_nested=parser):
        if directive.error is not None or directive.message is None:
            continue
        token = directive.message if directive.output is None else f"{directive.message}.{directive.output}"
        output = index.output(directive.message, directive.output)
        start = directive.message_start_index or directive.name_start_index
        end = directive.message_end_index or directive.name_end_index
        if output is None:
            diagnostics.append(
                _i18n_diagnostic(
                    _range(region.source_map.map_range(start, end)),
                    f"Unknown i18n message ID {token!r}; no component or configured catalog package defines it.",
                    I18N_UNKNOWN_MESSAGE,
                )
            )
            continue
        if directive.server_dynamic:
            continue
        expected = {parameter.name: parameter for parameter in output.parameters if parameter.type_name != "Slot"}
        supplied = {argument.name for argument in directive.arguments}
        issues: list[str] = []
        unknown = sorted(supplied - set(expected))
        missing = (
            sorted(set(expected) - supplied)
            if directive.has_values_expression and not directive.has_dynamic_arguments
            else []
        )
        if unknown:
            issues.append(f"unknown argument(s): {', '.join(unknown)}")
        if missing:
            issues.append(f"missing argument(s): {', '.join(missing)}")
        for argument in directive.arguments:
            parameter = expected.get(argument.name)
            if parameter is None:
                continue
            actual = _browser_prop_value_type(argument, roots, expressions)
            if actual.kind != "unknown" and not _browser_i18n_type_accepts(parameter.type_name, actual):
                issues.append(f"argument {argument.name!r} must be {parameter.type_name}, not {actual.javascript}")
        if issues:
            diagnostics.append(
                _i18n_diagnostic(
                    _range(region.source_map.map_range(start, end)),
                    f"$c-tr output {token!r} has {'; '.join(issues)}.",
                    I18N_ARGUMENT_INVALID,
                )
            )
    return diagnostics


def _browser_i18n_type_accepts(expected: str, actual: JsonWireType) -> bool:
    """Match a proven JavaScript value with the browser i18n argument ABI."""
    if actual.kind == "union":
        return all(_browser_i18n_type_accepts(expected, item) for item in actual.items)
    allowed = {
        "str": {"string"},
        "int": {"number", "string"},
        "Decimal": {"number", "string"},
        "scalar": {"number", "string"},
        "datetime": set(),
    }.get(expected)
    return True if allowed is None or actual.kind == "unknown" else actual.kind in allowed


def _component_js_lint_consumers(
    consumers: tuple[ComponentRecord, ...],
    project: ProjectState,
) -> tuple[ComponentJsLintConsumer, ...] | None:
    """Build each proven component-JavaScript global namespace."""
    if project.analysis is None or not consumers:
        return None
    resolved: list[ComponentJsLintConsumer] = []
    i18n_configured = project.i18n is not None and project.i18n.configured
    for component in consumers:
        lint = project.analysis.component_lint.get(component.definition_id)
        if lint is None:
            return None
        known_names = {variable.name for variable in lint.component_js_globals}
        if i18n_configured:
            known_names.add("i18n")
        resolved.append(
            ComponentJsLintConsumer(
                known_names=frozenset(known_names),
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
            i18n=project.i18n,
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
        i18n=project.i18n,
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
    if identifier is not None and not component_js and identifier.name in _ALPINE_API_SPECS:
        if identifier.name == "$i18n":
            return "$i18n" in expression.bindings
        return identifier.root
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


def _i18n_use_at(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
) -> _I18nUse | None:
    """Return one parser-backed i18n key or profile under the cursor."""
    if project.i18n is None or not project.i18n.available:
        return None
    uses: list[_I18nUse] = _catalog_i18n_uses(document, project)
    region = document.region_at(position)
    if region is not None:
        parser_index = region.source_map.parser_index_at(_citry_position(position))
        parsed = document.parsed.get(region.key)
        if parser_index is not None and parsed is not None:
            nested_parser = project.analysis.parse_template if project.analysis is not None else parse_template
            uses.extend(_mapped_i18n_binding_uses(parsed.template, region, nested_parser))
            query = template_python_query_at(
                parsed.template,
                parser_index,
                parse_nested=nested_parser,
            )
            if query is not None:
                uses.extend(_mapped_python_i18n_uses(query.source, query.start_index, region, template=True))
            expression = browser_expression_at(
                parsed.template,
                parser_index,
                parse_nested=nested_parser,
            )
            if expression is not None:
                uses.extend(_mapped_browser_i18n_uses(expression, region, owners=frozenset({"$i18n"})))
            uses.extend(_trans_i18n_uses(parsed.template, region))
    js_region = document.js_region_at(position)
    if js_region is not None:
        expression = BrowserExpression(
            js_region.source_map.template_source,
            0,
            len(js_region.source_map.template_source.encode("utf-8")),
            "statement",
            "component-js",
        )
        uses.extend(_mapped_browser_i18n_uses(expression, js_region, owners=frozenset({"i18n"})))
    if document.language_id == "python":
        uses.extend(_host_python_i18n_uses(document.source))
    matches = [use for use in uses if _position_in_range(position, use.range)]
    return min(matches, key=lambda item: _range_width(item.range)) if matches else None


def _catalog_i18n_uses(document: DocumentState, project: ProjectState) -> list[_I18nUse]:
    index = project.i18n
    if index is None:
        return []
    uses: list[_I18nUse] = []
    for output in index.outputs.values():
        range_ = _catalog_source_range(
            document,
            output.definition.path,
            output.definition.start,
            output.definition.end,
        )
        if range_ is not None:
            uses.append(_I18nUse("message", output.message, range_, output.attribute, completable=False))
    for reference in index.references:
        range_ = _catalog_source_range(document, reference.path, reference.start, reference.end)
        if range_ is None:
            continue
        message, separator, attribute = reference.token.partition(".")
        uses.append(_I18nUse("message", message, range_, attribute if separator else None))
    for region in document.messages_regions:
        if not _registered_messages_region(document, region, project):
            continue
        analysis = _analyze_messages_source(region)
        if analysis is None:
            continue
        for symbol in analysis.get("definitions", []):
            if symbol.get("kind") != "term":
                continue
            mapped = _messages_symbol_range(region, symbol)
            token = symbol.get("token")
            if mapped is not None and type(token) is str:
                uses.append(_I18nUse("term", token, mapped, completable=False, source_unit=region.key))
        for symbol in analysis.get("references", []):
            if symbol.get("kind") != "term":
                continue
            mapped = _messages_symbol_range(region, symbol)
            token = symbol.get("token")
            if mapped is not None and type(token) is str:
                uses.append(_I18nUse("term", token, mapped, completable=False, source_unit=region.key))
    return uses


def _analyze_messages_source(region: MessagesRegion) -> dict[str, Any] | None:
    try:
        payload = json.loads(
            _I18N_SOURCE_COMPILER.analyze_source(
                region.key,
                region.source_map.template_source,
            )
        )
    except (I18nCompileError, TypeError, ValueError):
        return None
    return cast("dict[str, Any]", payload) if type(payload) is dict else None


def _messages_symbol_range(region: MessagesRegion, symbol: object) -> types.Range | None:
    if type(symbol) is not dict:
        return None
    start = symbol.get("start")
    end = symbol.get("end")
    if type(start) is not int or type(end) is not int or end <= start:
        return None
    try:
        return _range(region.source_map.map_range(start, end))
    except ValueError:
        return None


def _catalog_source_range(
    document: DocumentState,
    origin: str,
    start: int,
    end: int,
) -> types.Range | None:
    document_path = file_uri_path(document.uri)
    if document_path is None:
        return None
    path_text, separator, inline = origin.rpartition("::")
    source_path = Path(path_text if separator else origin)
    try:
        if document_path.resolve() != source_path.resolve():
            return None
    except OSError:
        return None
    if separator and inline.endswith(".messages"):
        source_map = python_messages_source_map(document.source, inline.removesuffix(".messages"))
        if source_map is None:
            return None
        try:
            return _range(source_map.map_range(start, end))
        except ValueError:
            return None
    try:
        start_char = parser_char_index(document.source, start)
        end_char = parser_char_index(document.source, end)
        return _range(document_range_for_offsets(document.source, start_char, end_char))
    except ValueError:
        return None


def _mapped_python_i18n_uses(
    source: str,
    base_index: int,
    region: TemplateRegion,
    *,
    template: bool,
) -> list[_I18nUse]:
    uses: list[_I18nUse] = []
    for kind, value, attribute, namespace, operation, message, start, end in _python_i18n_uses(
        source,
        template=template,
    ):
        try:
            mapped = region.source_map.map_range(base_index + start, base_index + end)
        except ValueError:
            continue
        uses.append(
            _I18nUse(
                cast("Literal['message', 'operation', 'parameter', 'profile']", kind),
                value,
                _range(mapped),
                attribute=attribute,
                namespace=cast("Literal['format', 'parse'] | None", namespace),
                operation=operation,
                message=message,
            )
        )
    return uses


def _host_python_i18n_uses(source: str) -> list[_I18nUse]:
    uses: list[_I18nUse] = []
    for kind, value, attribute, namespace, operation, message, start, end in _python_i18n_uses(
        source,
        template=False,
    ):
        try:
            start_char = parser_char_index(source, start)
            end_char = parser_char_index(source, end)
        except ValueError:
            continue
        uses.append(
            _I18nUse(
                cast("Literal['message', 'operation', 'parameter', 'profile']", kind),
                value,
                _range(document_range_for_offsets(source, start_char, end_char)),
                attribute=attribute,
                namespace=cast("Literal['format', 'parse'] | None", namespace),
                operation=operation,
                message=message,
            )
        )
    return uses


def _python_i18n_uses(
    source: str,
    *,
    template: bool,
) -> list[tuple[str, str, str | None, str | None, str | None, str | None, int, int]]:
    """Extract direct Python/template calls with exact string-token spans."""
    # The removed suffix is only template indentation after the expression,
    # so every retained AST byte offset still maps to the authored source.
    parsed_source = source.rstrip() if template else source
    try:
        tree = ast.parse(parsed_source, mode="eval" if template else "exec")
    except (SyntaxError, TypeError, ValueError):
        return []
    uses: list[tuple[str, str, str | None, str | None, str | None, str | None, int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        message_call = _python_message_call(node.func, template=template)
        if message_call and node.args and isinstance(node.args[0], ast.Constant) and type(node.args[0].value) is str:
            message = cast("str", node.args[0].value)
            attribute = _literal_python_keyword(node, "attr")
            span = _ast_string_content_span(source, node.args[0])
            if span is not None:
                uses.append(("message", message, attribute, None, None, None, *span))
            for keyword in node.keywords:
                if keyword.arg is None or keyword.arg == "attr":
                    continue
                keyword_span = _python_keyword_name_span(source, keyword)
                if keyword_span is not None:
                    uses.append(
                        (
                            "parameter",
                            keyword.arg,
                            attribute,
                            None,
                            None,
                            message,
                            *keyword_span,
                        )
                    )
            continue
        target = _python_profile_call(node.func, template=template)
        if target is None:
            continue
        operation_span = _python_attribute_name_span(source, node.func)
        if operation_span is not None:
            uses.append(("operation", target[1], None, target[0], target[1], None, *operation_span))
        profile = next((keyword.value for keyword in node.keywords if keyword.arg == "format"), None)
        if not isinstance(profile, ast.Constant) or type(profile.value) is not str:
            continue
        span = _ast_string_content_span(source, profile)
        if span is not None:
            operation = _I18N_PROFILE_OPERATION_NAMES.get(target[1], target[1])
            uses.append(("profile", cast("str", profile.value), None, target[0], operation, None, *span))
    if not template:
        uses.extend(_client_messages_i18n_uses(source, tree))
    return uses


def _python_message_call(function: ast.expr, *, template: bool) -> bool:
    if template and isinstance(function, ast.Name) and function.id == "tr":
        return True
    return isinstance(function, ast.Attribute) and function.attr == "tr" and _python_i18n_service(function.value)


def _python_profile_call(function: ast.expr, *, template: bool) -> tuple[str, str] | None:
    if not isinstance(function, ast.Attribute):
        return None
    operation = function.attr
    owner = function.value
    if template and isinstance(owner, ast.Name) and owner.id == "fmt":
        return "format", operation
    if not isinstance(owner, ast.Attribute) or owner.attr not in {"format", "parse"}:
        return None
    if _python_i18n_service(owner.value):
        return owner.attr, operation
    return None


def _python_i18n_service(expression: ast.expr) -> bool:
    """Recognize the two explicit public ways to obtain an i18n service."""
    if (
        isinstance(expression, ast.Attribute)
        and expression.attr == "i18n"
        and isinstance(expression.value, ast.Name)
        and expression.value.id == "self"
    ):
        return True
    return (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == "for_context"
        and isinstance(expression.func.value, ast.Name)
        and expression.func.value.id == "i18n"
    )


def _literal_python_keyword(call: ast.Call, name: str) -> str | None:
    value = next((keyword.value for keyword in call.keywords if keyword.arg == name), None)
    return cast("str", value.value) if isinstance(value, ast.Constant) and type(value.value) is str else None


def _client_messages_i18n_uses(
    source: str,
    tree: ast.AST,
) -> list[tuple[str, str, str | None, str | None, str | None, str | None, int, int]]:
    uses: list[tuple[str, str, str | None, str | None, str | None, str | None, int, int]] = []
    for component in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        for nested in (item for item in component.body if isinstance(item, ast.ClassDef) and item.name == "I18n"):
            for statement in nested.body:
                value: ast.expr | None = None
                if (
                    isinstance(statement, ast.Assign)
                    and any(
                        isinstance(target, ast.Name) and target.id == "client_messages" for target in statement.targets
                    )
                ) or (
                    isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                    and statement.target.id == "client_messages"
                ):
                    value = statement.value
                if not isinstance(value, (ast.Tuple, ast.List, ast.Set)):
                    continue
                for item in value.elts:
                    if not isinstance(item, ast.Constant) or type(item.value) is not str:
                        continue
                    span = _ast_string_content_span(source, item)
                    if span is not None:
                        uses.append(("message", cast("str", item.value), None, None, None, None, *span))
    return uses


def _python_keyword_name_span(source: str, keyword: ast.keyword) -> tuple[int, int] | None:
    """Return the exact keyword name without including its value."""
    if keyword.arg is None or keyword.lineno is None or keyword.col_offset is None:
        return None
    start = _python_ast_byte_offset(source, keyword.lineno, keyword.col_offset)
    return start, start + len(keyword.arg.encode("utf-8"))


def _python_attribute_name_span(source: str, expression: ast.expr) -> tuple[int, int] | None:
    """Return the final member name in one direct attribute expression."""
    if not isinstance(expression, ast.Attribute) or expression.end_lineno is None or expression.end_col_offset is None:
        return None
    end = _python_ast_byte_offset(source, expression.end_lineno, expression.end_col_offset)
    return end - len(expression.attr.encode("utf-8")), end


def _ast_string_content_span(source: str, node: ast.Constant) -> tuple[int, int] | None:
    if any(value is None for value in (node.end_lineno, node.end_col_offset)):
        return None
    start = _python_ast_byte_offset(source, node.lineno, node.col_offset)
    end = _python_ast_byte_offset(source, cast("int", node.end_lineno), cast("int", node.end_col_offset))
    encoded = source.encode("utf-8")
    try:
        raw = encoded[start:end].decode("utf-8")
    except UnicodeDecodeError:
        return None
    match = re.fullmatch(r"(?is)(?:[rub]*)('''|\"\"\"|'|\")(.*)\1", raw)
    if match is None:
        return None
    prefix = raw[: match.start(2)]
    suffix = raw[match.end(2) :]
    return start + len(prefix.encode("utf-8")), end - len(suffix.encode("utf-8"))


def _python_ast_byte_offset(source: str, line: int, column: int) -> int:
    lines = source.splitlines(keepends=True)
    return sum(len(item.encode("utf-8")) for item in lines[: line - 1]) + column


def _mapped_browser_i18n_uses(
    expression: BrowserExpression,
    region: TemplateRegion | JsRegion,
    *,
    owners: frozenset[str],
) -> list[_I18nUse]:
    if "$i18n" in owners and "$i18n" not in expression.bindings:
        return []
    uses: list[_I18nUse] = []
    for call in browser_i18n_message_calls(expression, owners):
        try:
            mapped = region.source_map.map_range(call.message_start_index, call.message_end_index)
        except ValueError:
            continue
        uses.append(_I18nUse("message", call.message, _range(mapped), call.attribute))
        if call.has_dynamic_attribute:
            continue
        for argument in call.arguments:
            try:
                argument_range = region.source_map.map_range(argument.start_index, argument.end_index)
            except ValueError:
                continue
            uses.append(
                _I18nUse(
                    "parameter",
                    argument.name,
                    _range(argument_range),
                    attribute=call.attribute,
                    message=call.message,
                )
            )
    for bind_call in browser_i18n_bind_calls(expression, owners):
        try:
            message_range = region.source_map.map_range(
                bind_call.message_start_index,
                bind_call.message_end_index,
            )
        except ValueError:
            continue
        uses.append(
            _I18nUse(
                "message",
                bind_call.message,
                _range(message_range),
                bind_call.output,
            )
        )
        if bind_call.output is None or bind_call.output_start_index is None or bind_call.output_end_index is None:
            continue
        try:
            output_range = region.source_map.map_range(
                bind_call.output_start_index,
                bind_call.output_end_index,
            )
        except ValueError:
            continue
        uses.append(
            _I18nUse(
                "message",
                bind_call.message,
                _range(output_range),
                bind_call.output,
            )
        )
    operation_names = {"relativeTime": "relative_time"}
    for profile_call in browser_i18n_profile_calls(expression, owners):
        try:
            mapped = region.source_map.map_range(profile_call.start_index, profile_call.end_index)
        except ValueError:
            continue
        uses.append(
            _I18nUse(
                "profile",
                profile_call.profile,
                _range(mapped),
                namespace=profile_call.namespace,
                operation=operation_names.get(profile_call.operation, profile_call.operation),
            )
        )
    return uses


def _mapped_i18n_binding_uses(template: Any, region: TemplateRegion, parser: Any) -> list[_I18nUse]:
    """Map `$c-tr` message and Fluent-attribute names to catalog uses."""
    uses: list[_I18nUse] = []
    for directive in browser_i18n_binding_directives(template, parse_nested=parser):
        if directive.message is None:
            if directive.error is not None and "message ID after ':'" in directive.error:
                start = directive.error_start_index or directive.name_end_index
                end = directive.error_end_index or start
                try:
                    mapped = region.source_map.map_range(start, end)
                except ValueError:
                    continue
                uses.append(_I18nUse("message", "", _range(mapped)))
            continue
        if directive.message_start_index is None or directive.message_end_index is None:
            continue
        try:
            message_range = region.source_map.map_range(
                directive.message_start_index,
                directive.message_end_index,
            )
        except ValueError:
            continue
        uses.append(_I18nUse("message", directive.message, _range(message_range), directive.output))
        if (
            directive.output is not None
            and directive.output_start_index is not None
            and directive.output_end_index is not None
        ):
            try:
                output_range = region.source_map.map_range(
                    directive.output_start_index,
                    directive.output_end_index,
                )
            except ValueError:
                pass
            else:
                uses.append(_I18nUse("message", directive.message, _range(output_range), directive.output))
        for argument in directive.arguments:
            try:
                argument_range = region.source_map.map_range(argument.start_index, argument.end_index)
            except ValueError:
                continue
            uses.append(
                _I18nUse(
                    "parameter",
                    argument.name,
                    _range(argument_range),
                    attribute=directive.output,
                    message=directive.message,
                )
            )
    return uses


def _trans_i18n_uses(template: Any, region: TemplateRegion) -> list[_I18nUse]:
    uses: list[_I18nUse] = []
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        if node.start_tag.name.content.lower() == "c-trans":
            attrs = {attr.key.content: attr for attr in node.start_tag.attrs}
            message = attrs.get("message")
            if message is not None and message.inner_value is not None:
                attribute = attrs.get("attr")
                attribute_name = (
                    attribute.inner_value.content
                    if attribute is not None and attribute.inner_value is not None
                    else None
                )
                mapped = region.source_map.map_range(
                    message.inner_value.start_index,
                    message.inner_value.end_index,
                )
                uses.append(_I18nUse("message", message.inner_value.content, _range(mapped), attribute_name))
                values = attrs.get("c-values")
                if values is not None and values.inner_value is not None:
                    for parameter, start, end in _literal_trans_value_spans(values.inner_value.content):
                        mapped_parameter = region.source_map.map_range(
                            values.inner_value.start_index + start,
                            values.inner_value.start_index + end,
                        )
                        uses.append(
                            _I18nUse(
                                "parameter",
                                parameter,
                                _range(mapped_parameter),
                                attribute=attribute_name,
                                message=message.inner_value.content,
                            )
                        )
                body = getattr(node, "body", None)
                if body is not None:
                    for child in body.elements:
                        if not isinstance(child, TemplateElement.Node):
                            continue
                        fill = child._0
                        if fill.start_tag.name.content.lower() != "c-fill":
                            continue
                        name = next(
                            (attr for attr in fill.start_tag.attrs if attr.key.content == "name"),
                            None,
                        )
                        if name is None or name.inner_value is None:
                            continue
                        mapped_parameter = region.source_map.map_range(
                            name.inner_value.start_index,
                            name.inner_value.end_index,
                        )
                        uses.append(
                            _I18nUse(
                                "parameter",
                                name.inner_value.content,
                                _range(mapped_parameter),
                                attribute=attribute_name,
                                message=message.inner_value.content,
                            )
                        )
        body = getattr(node, "body", None)
        if body is not None:
            uses.extend(_trans_i18n_uses(body, region))
    return uses


def _literal_trans_value_spans(source: str) -> tuple[tuple[str, int, int], ...]:
    """Return literal mapping keys from one ``c-values`` expression."""
    try:
        expression = ast.parse(source, mode="eval").body
    except (SyntaxError, TypeError, ValueError):
        return ()
    if not isinstance(expression, ast.Dict):
        return ()
    found: list[tuple[str, int, int]] = []
    for key in expression.keys:
        if not isinstance(key, ast.Constant) or type(key.value) is not str:
            continue
        span = _ast_string_content_span(source, key)
        if span is not None:
            found.append((cast("str", key.value), *span))
    return tuple(found)


def _position_in_range(position: types.Position, range_: types.Range) -> bool:
    point = (position.line, position.character)
    return (range_.start.line, range_.start.character) <= point <= (range_.end.line, range_.end.character)


def _range_width(range_: types.Range) -> tuple[int, int]:
    return (range_.end.line - range_.start.line, range_.end.character - range_.start.character)


def _i18n_completion_result(use: _I18nUse, project: ProjectState) -> CompletionResult:
    index = project.i18n
    if index is None or not use.completable:
        return CompletionResult(())
    if use.kind not in {"message", "profile"}:
        return CompletionResult(())
    if use.kind == "message":
        names = index.message_ids()
        kind = types.CompletionItemKind.Value
        detail = "Fluent message"
    else:
        if use.namespace is None or use.operation is None:
            return CompletionResult(())
        names = index.profile_names(use.namespace, use.operation)
        kind = types.CompletionItemKind.EnumMember
        detail = f"i18n {use.namespace} profile for {use.operation}"
    return CompletionResult(
        tuple(
            types.CompletionItem(
                label=name,
                kind=kind,
                detail=detail,
                text_edit=types.TextEdit(use.range, name),
                filter_text=name,
            )
            for name in names
        ),
        is_incomplete=False,
    )


def _i18n_hover(use: _I18nUse, project: ProjectState) -> types.Hover | None:
    index = project.i18n
    if index is None:
        return None
    if use.kind == "term":
        return types.Hover(
            types.MarkupContent(
                types.MarkupKind.Markdown,
                f"`{use.value}`\n\nPrivate Fluent term in this component message source.",
            ),
            range=use.range,
        )
    if use.kind == "operation":
        if use.namespace is None or use.operation is None:
            return None
        signature = _I18N_OPERATION_SIGNATURES.get((use.namespace, use.operation))
        if signature is None:
            return None
        return types.Hover(
            types.MarkupContent(
                types.MarkupKind.Markdown,
                f"```python\n{signature}\n```\n\nLocale-aware i18n {use.namespace} operation.",
            ),
            range=use.range,
        )
    if use.kind == "profile":
        if use.namespace is None or use.operation is None:
            return None
        if use.value not in index.profile_names(use.namespace, use.operation):
            return None
        return types.Hover(
            types.MarkupContent(
                types.MarkupKind.Markdown,
                f"`{use.value}`\n\nNamed i18n {use.namespace} profile for `{use.operation}()`.",
            ),
            range=use.range,
        )
    if use.kind == "parameter":
        output = _i18n_parameter_output(use, index)
        if output is None:
            return None
        parameter = next((item for item in output.parameters if item.name == use.value), None)
        if parameter is None:
            return None
        description = f"\n\n{parameter.descriptions[0]}" if parameter.descriptions else ""
        inherited = "\n\nRequired through a referenced message or term." if not parameter.direct else ""
        return types.Hover(
            types.MarkupContent(
                types.MarkupKind.Markdown,
                f"`${parameter.name}`: `{parameter.type_name}`{description}{inherited}\n\nInput for `{output.token}`.",
            ),
            range=use.range,
        )
    output = index.output(use.value, use.attribute)
    if output is None and use.attribute is None:
        output = next((item for item in index.outputs.values() if item.message == use.value), None)
    if output is None:
        return None
    lines = [f"`{output.token}`", "", f"Defined by catalog owner `{output.owner}`."]
    if output.parameters:
        lines.extend(("", "Inputs:"))
        for parameter in output.parameters:
            description = f" - {parameter.descriptions[0]}" if parameter.descriptions else ""
            inherited = " (through a referenced message or term)" if not parameter.direct else ""
            lines.append(f"- `${parameter.name}`: `{parameter.type_name}`{inherited}{description}")
    attributes = sorted(
        candidate.attribute
        for candidate in index.outputs.values()
        if candidate.message == output.message and candidate.attribute is not None
    )
    if attributes and use.attribute is None:
        lines.extend(("", f"Attributes: {', '.join(f'`.{name}`' for name in attributes)}"))
    return types.Hover(types.MarkupContent(types.MarkupKind.Markdown, "\n".join(lines)), range=use.range)


def _i18n_definition(
    use: _I18nUse,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
    document: DocumentState,
) -> types.Location | list[types.Location] | None:
    if use.kind == "term":
        for region in document.messages_regions:
            if region.key != use.source_unit:
                continue
            analysis = _analyze_messages_source(region)
            if analysis is None:
                return None
            for symbol in analysis.get("definitions", []):
                if type(symbol) is dict and symbol.get("kind") == "term" and symbol.get("token") == use.value:
                    range_ = _messages_symbol_range(region, symbol)
                    return types.Location(document.uri, range_) if range_ is not None else None
        return None
    if use.kind == "parameter" and project.i18n is not None:
        output = _i18n_parameter_output(use, project.i18n)
        if output is None:
            return None
        parameter = next((item for item in output.parameters if item.name == use.value), None)
        if parameter is None:
            return None
        locations = tuple(
            location
            for declaration in parameter.declarations
            if (location := _i18n_parameter_declaration_location(declaration, open_documents)) is not None
        )
        if not locations:
            return None
        return locations[0] if len(locations) == 1 else list(locations)
    if use.kind != "message" or project.i18n is None:
        return None
    output = project.i18n.output(use.value, use.attribute)
    if output is None and use.attribute is None:
        output = next((item for item in project.i18n.outputs.values() if item.message == use.value), None)
    return _i18n_definition_location(output, open_documents) if output is not None else None


def _i18n_parameter_output(use: _I18nUse, index: Any) -> I18nOutputRecord | None:
    """Resolve the output whose argument name is under the cursor."""
    if use.message is None:
        return None
    return index.output(use.message, use.attribute)


def _i18n_parameter_declaration_location(
    declaration: I18nParameterDeclarationRecord,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Location | None:
    """Map one compiler-proven @param comment back to its authored file."""
    return _i18n_source_location(
        declaration.path,
        declaration.start,
        declaration.end,
        open_documents,
    )


def _i18n_definition_location(
    output: I18nOutputRecord,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Location | None:
    definition = output.definition
    return _i18n_source_location(definition.path, definition.start, definition.end, open_documents)


def _i18n_source_location(
    authored_path: str,
    start_index: int,
    end_index: int,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Location | None:
    """Map one catalog byte range through an inline messages declaration."""
    path_text, separator, inline = authored_path.rpartition("::")
    path = Path(path_text if separator else authored_path).resolve()
    if not path.is_file():
        return None
    uri = path.as_uri()
    source = _open_document_source(path, open_documents) if open_documents is not None else None
    if source is None:
        try:
            with tokenize.open(path) as stream:
                source = stream.read()
        except (OSError, SyntaxError, UnicodeError):
            return None
    if separator and inline.endswith(".messages"):
        component_name = inline.removesuffix(".messages")
        source_map = python_messages_source_map(source, component_name)
        if source_map is None:
            return None
        try:
            mapped = source_map.map_range(start_index, end_index)
        except ValueError:
            return None
        return types.Location(uri, _range(mapped))
    try:
        start = parser_char_index(source, start_index)
        end = parser_char_index(source, end_index)
        range_ = _range(document_range_for_offsets(source, start, end))
    except ValueError:
        return None
    return types.Location(uri, range_)


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
    i18n_use = _i18n_use_at(document, position, project)
    if i18n_use is not None:
        return _i18n_completion_result(i18n_use, project)
    catalog = project.catalog
    event_result = _browser_event_completion_result(document, position, project, open_documents)
    if event_result is not None:
        return event_result
    modifier_result = _citry_binding_modifier_completion_result(document, position)
    if modifier_result is not None:
        return modifier_result
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
        static_text = (
            schema_field.name
            if attribute_context.preserve_value or schema_field.type_display == "bool"
            else f'{schema_field.name}="$1"'
        )
        dynamic_name = f"c-{schema_field.name}"
        dynamic_text = dynamic_name if attribute_context.preserve_value else f'{dynamic_name}="$1"'
        for label, new_text, detail in (
            (schema_field.name, static_text, _field_detail(schema_field)),
            (dynamic_name, dynamic_text, f"Dynamic Python expression · {_field_detail(schema_field)}"),
        ):
            items.append(
                types.CompletionItem(
                    label=label,
                    kind=types.CompletionItemKind.Field,
                    detail=detail,
                    documentation=_markdown(schema_field.description),
                    insert_text=new_text,
                    insert_text_format=types.InsertTextFormat.Snippet,
                    filter_text=label,
                    text_edit=types.InsertReplaceEdit(
                        new_text=new_text,
                        insert=attribute_context.edit_range,
                        replace=attribute_context.edit_range,
                    ),
                )
            )
    return CompletionResult(tuple(items), is_incomplete=True)


def _citry_binding_reference(
    document: DocumentState,
    position: types.Position,
) -> tuple[TemplateRegion, _CitryBindingReference] | None:
    """Resolve one binding-key segment through the current template source map."""
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    parsed = document.parsed.get(region.key)
    if parser_index is None or parsed is None:
        return None
    reference = _citry_binding_reference_at(parsed.template, parser_index)
    return (region, reference) if reference is not None else None


def _citry_binding_hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> types.Hover | None:
    """Explain Citry binding bases and modifier segments at their exact ranges."""
    resolved = _citry_binding_reference(document, position)
    if resolved is None:
        return None
    region, reference = resolved
    source = region.source_map.template_source
    try:
        start = parser_char_index(source, reference.start_index)
        end = parser_char_index(source, reference.end_index)
    except ValueError:
        return None
    mapped_range = _mapped_template_range(region, source, start, end)
    if mapped_range is None:
        return None

    if reference.part == "modifier":
        markdown = _citry_binding_modifier_markdown(reference)
    elif reference.channel == "event":
        markdown = _citry_event_binding_markdown(reference)
    else:
        markdown = _citry_state_binding_markdown(
            document,
            region,
            reference,
            project,
            open_documents,
        )
    if markdown is None:
        return None
    return types.Hover(
        types.MarkupContent(types.MarkupKind.Markdown, markdown),
        range=mapped_range,
    )


def _citry_event_binding_markdown(reference: _CitryBindingReference) -> str:
    """Describe one open DOM-event name without pretending the name is closed."""
    if reference.base_name == "poll":
        description = (
            "Call the named Python Events handler on the interval supplied by one modifier such as `.30s`. "
            "Citry pauses polling while the tab is hidden."
        )
    else:
        description = (
            f"Listen for the `{reference.base_name}` DOM event on this element and send the attribute's value "
            "to the matching Python Events handler."
        )
    return f"### `{reference.value}`\n\n{description}\n\n[Read the Citry documentation]({_EVENT_BINDINGS_URL})"


def _citry_state_binding_markdown(
    document: DocumentState,
    region: TemplateRegion,
    reference: _CitryBindingReference,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> str:
    """Describe a State binding and add proven Python type and origin facts."""
    consumers = _template_consumers(document, region, project, open_documents)
    roots = _shared_state_roots(consumers, document, project, open_documents)
    root = next((candidate for candidate in roots or () if candidate.name == reference.base_name), None)
    records = _shared_state_field_records(consumers, project, reference.base_name) if root is not None else ()
    if root is None:
        lines = [f"### `{reference.value}`"]
    else:
        type_displays = tuple(dict.fromkeys(record.type_display for record in records if record.type_display))
        rendered_type = " | ".join(type_displays) if type_displays else root.wire_type.javascript
        lines = ["```python", f"(field) {reference.base_name}: {rendered_type}", "```"]
    lines.extend(
        (
            "",
            f"`{reference.value}` connects this control to the public "
            f"`Component.State.{reference.base_name}` field. A handler value makes the binding two-way: "
            "Citry sends the field update and calls that handler together.",
        )
    )
    origins: dict[str, str | None] = {f"{record.qualname}.{record.name}": record.description for record in records}
    if origins:
        lines.extend(("", "Python declarations:"))
        for origin, description in origins.items():
            lines.append(f"- `{origin}`")
            if description:
                lines.append(f"  {description}")
    lines.extend(("", f"[Read the Citry documentation]({_EVENT_BINDINGS_URL})"))
    return "\n".join(lines)


def _citry_binding_modifier_markdown(reference: _CitryBindingReference) -> str | None:
    """Explain only modifier shapes accepted by this binding's runtime channel."""
    display = f".{reference.value}"
    if _CITRY_TIME_SEGMENT.fullmatch(reference.value):
        if reference.channel == "event" and reference.base_name == "poll":
            documentation = "Use one whole number of seconds, such as `.30s`, as the polling interval."
        elif reference.previous_modifier in {"debounce", "throttle"}:
            documentation = (
                "Use a whole number followed by `ms` or `s`, such as `.300ms` or `.1s`, "
                f"as the `.{reference.previous_modifier}` duration."
            )
        else:
            return None
    else:
        modifier_name = "on" if reference.value.startswith("on:") else reference.value
        spec = _CITRY_BINDING_MODIFIERS_BY_NAME.get(modifier_name)
        if spec is None or reference.channel not in spec.channels:
            return None
        documentation = spec.documentation
    return f"### `{display}`\n\n{documentation}\n\n[Read the Citry documentation]({_EVENT_BINDINGS_URL})"


def _citry_state_binding_origin_locations(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> tuple[types.Location, ...]:
    """Navigate a ``:c-*`` base name to the exact public State declaration."""
    resolved = _citry_binding_reference(document, position)
    if resolved is None:
        return ()
    region, reference = resolved
    if reference.channel != "state" or reference.part != "base":
        return ()
    consumers = _template_consumers(document, region, project, open_documents)
    roots = _shared_state_roots(consumers, document, project, open_documents)
    root = next((candidate for candidate in roots or () if candidate.name == reference.base_name), None)
    return root.locations if root is not None else ()


def hover(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None = None,
) -> types.Hover | None:
    """Return Citry syntax, lexical, or catalog documentation under cursor."""
    i18n_use = _i18n_use_at(document, position, project)
    if i18n_use is not None:
        i18n_hover = _i18n_hover(i18n_use, project)
        if i18n_hover is not None:
            return i18n_hover
    citry_binding_hover = _citry_binding_hover(document, position, project, open_documents)
    if citry_binding_hover is not None:
        return citry_binding_hover
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
                    _syntax_markdown(syntax_reference.spec, syntax_reference.display_label),
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
    state_binding_locations = _citry_state_binding_origin_locations(
        document,
        position,
        project,
        open_documents,
    )
    if state_binding_locations:
        return state_binding_locations[0] if len(state_binding_locations) == 1 else list(state_binding_locations)
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
    i18n_use = _i18n_use_at(document, position, project)
    if i18n_use is not None:
        i18n_location = _i18n_definition(i18n_use, project, open_documents, document)
        if i18n_location is not None:
            return i18n_location
    state_binding_locations = _citry_state_binding_origin_locations(
        document,
        position,
        project,
        open_documents,
    )
    if state_binding_locations:
        return state_binding_locations[0] if len(state_binding_locations) == 1 else list(state_binding_locations)
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
        roots = tuple(
            TemplatePythonRoot(
                root.name,
                root.presence,
                root.access,
                root.type_field.source_module if root.type_field is not None else None,
                root.type_field.source_qualname if root.type_field is not None else None,
                root.shadow_type_display,
            )
            for root in context.roots
        )
        roots, analysis_preamble = _i18n_template_analysis_contract(context.source, roots)
        consumers.append(
            _ExpressionShadowConsumer(
                identity=owner.definition_id,
                source_file=context.source_file,
                source=context.source,
                source_kind=cast("Literal['schema', 'inferred']", context.source_kind),
                source_module=context.source_module,
                source_qualname=context.source_qualname,
                kwargs_type=context.kwargs_type,
                roots=roots,
                analysis_preamble=analysis_preamble,
            )
        )
    return tuple(consumers)


def _i18n_template_analysis_contract(
    source: str,
    roots: tuple[TemplatePythonRoot, ...],
) -> tuple[tuple[TemplatePythonRoot, ...], str]:
    """Provide local i18n types when an editable install is opaque to ty."""
    if not any(root.name in {"fmt", "tr"} for root in roots):
        return roots, ""

    formatter_type = "CitryLspI18nFormatterType"
    while formatter_type in source:
        formatter_type += "_"
    rewritten = tuple(
        replace(root, type_display=formatter_type)
        if root.name == "fmt"
        else replace(root, type_display="typing.Callable[..., str]")
        if root.name == "tr"
        else root
        for root in roots
    )
    preamble = f"""\
class {formatter_type}:
    def number(self, value: object, *, format: str) -> str:
        return ""
    def percent(self, value: object, *, format: str) -> str:
        return ""
    def currency(self, value: object, currency: str, *, format: str) -> str:
        return ""
    def date(self, value: object, *, format: str) -> str:
        return ""
    def time(self, value: object, *, format: str) -> str:
        return ""
    def datetime(self, value: object, *, format: str) -> str:
        return ""
    def relative_time(self, value: object, *, unit: str, format: str) -> str:
        return ""
    def list(self, values: object, *, format: str) -> str:
        return ""
    def unit(self, value: object, unit: str, *, format: str) -> str:
        return ""
"""
    return rewritten, preamble


def _insert_shadow_preamble(document: ShadowPythonDocument, preamble: str) -> ShadowPythonDocument:
    """Place analysis declarations before queries and shift exact source maps."""
    if not preamble:
        return document
    try:
        module = ast.parse(document.source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return replace(document, source=f"{document.source}\n{preamble.rstrip()}\n")

    prefix_end_line = 0
    for index, statement in enumerate(module.body):
        is_docstring = (
            index == 0
            and isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        )
        if is_docstring or (isinstance(statement, ast.ImportFrom) and statement.module == "__future__"):
            prefix_end_line = statement.end_lineno or statement.lineno
            continue
        break
    insertion = sum(len(line) for line in document.source.splitlines(keepends=True)[:prefix_end_line])
    if any(copied.shadow_start < insertion for copied in document.copies):
        return replace(document, source=f"{document.source}\n{preamble.rstrip()}\n")

    inserted = f"\n{preamble.rstrip()}\n" if insertion else f"{preamble.rstrip()}\n\n"
    width = len(inserted)
    shifted_copies = tuple(
        replace(
            copied,
            shadow_start=copied.shadow_start + width,
            shadow_end=copied.shadow_end + width,
        )
        for copied in document.copies
    )
    shifted_source_copies = []
    for copied in document.source_copies:
        if copied.shadow_end <= insertion:
            shifted_source_copies.append(copied)
        elif copied.shadow_start >= insertion:
            shifted_source_copies.append(
                replace(
                    copied,
                    shadow_start=copied.shadow_start + width,
                    shadow_end=copied.shadow_end + width,
                )
            )
        else:
            source_split = copied.source_start + insertion - copied.shadow_start
            shifted_source_copies.extend(
                (
                    replace(copied, shadow_end=insertion, source_end=source_split),
                    replace(
                        copied,
                        shadow_start=insertion + width,
                        shadow_end=copied.shadow_end + width,
                        source_start=source_split,
                    ),
                )
            )
    return replace(
        document,
        source=f"{document.source[:insertion]}{inserted}{document.source[insertion:]}",
        copies=shifted_copies,
        source_copies=tuple(shifted_source_copies),
    )


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
        shadow = _insert_shadow_preamble(shadow, consumer.analysis_preamble)
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
    source = query.source.rstrip()
    framed = f"[\nNone for {source}\n]" if query.host_kind == "loop" else source
    try:
        tree = ast.parse(framed, mode="eval")
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return True
    return any(isinstance(node, ast.NamedExpr) for node in ast.walk(tree))


def _query_contains_lambda_named_expression(query: TemplatePythonQuery) -> bool:
    """Detect Citry's context-leaking lambda assignment special case."""
    source = query.source.rstrip()
    framed = f"[\nNone for {source}\n]" if query.host_kind == "loop" else source
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
) -> list[types.Diagnostic]:
    return [
        types.Diagnostic(
            _range(
                region.source_map.map_range(
                    finding.start_index,
                    finding.end_index,
                )
            ),
            render_diagnostic(TEMPLATE_UNKNOWN_COMPONENT, tag=finding.tag),
            severity=types.DiagnosticSeverity.Error,
            code=TEMPLATE_UNKNOWN_COMPONENT,
            code_description=types.CodeDescription(diagnostic_documentation_url(TEMPLATE_UNKNOWN_COMPONENT)),
            source="citry",
        )
        for finding in unknown_component_uses(template, known_names)
    ]


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
    """One documented spelling shared by completion and hover."""

    label: str
    kind: str
    detail: str
    documentation: str
    documentation_url: str
    context: str | None = None
    insert_text: str | None = None
    repeatable: bool = False
    primary_attribute: str | None = None


@dataclass(frozen=True, slots=True)
class _CitryBindingModifierSpec:
    """One modifier that Citry's Events runtime accepts on a binding channel."""

    name: str
    channels: frozenset[Literal["event", "state"]]
    detail: str
    documentation: str
    insert_text: str | None = None


_BUILTINS_URL = "https://citry.dev/reference/builtins/"
_CONTROL_FLOW_URL = "https://citry.dev/syntax/control-flow/"
_DYNAMIC_ATTRIBUTES_URL = "https://citry.dev/syntax/dynamic-attributes/"
_SLOTS_URL = "https://citry.dev/concepts/slots/"
_CLIENT_INTERACTIVITY_URL = "https://citry.dev/concepts/client-interactivity/"
_DYNAMIC_COMPONENTS_URL = "https://citry.dev/advanced/dynamic-components/"
_BROWSER_I18N_URL = "https://citry.dev/i18n/browser/"
_EVENT_BINDINGS_URL = "https://citry.dev/events/bindings/"

_CITRY_BINDING_MODIFIERS = (
    _CitryBindingModifierSpec(
        "prevent",
        frozenset({"event"}),
        "Prevent the browser's default action",
        "Call `preventDefault()` before Citry sends the server event.",
    ),
    _CitryBindingModifierSpec(
        "stop",
        frozenset({"event"}),
        "Stop DOM event propagation",
        "Call `stopPropagation()` before Citry sends the server event.",
    ),
    _CitryBindingModifierSpec(
        "self",
        frozenset({"event"}),
        "Require this element as the event target",
        "Send only when the bound element itself is the DOM event target.",
    ),
    _CitryBindingModifierSpec(
        "once",
        frozenset({"event"}),
        "Send at most once",
        "Let this binding send its server event only once during the element's lifetime.",
    ),
    _CitryBindingModifierSpec(
        "enter",
        frozenset({"event", "state"}),
        "Require the Enter key",
        "Send only when the triggering event's key is `Enter`.",
    ),
    _CitryBindingModifierSpec(
        "escape",
        frozenset({"event", "state"}),
        "Require the Escape key",
        "Send only when the triggering event's key is `Escape`.",
    ),
    _CitryBindingModifierSpec(
        "debounce",
        frozenset({"event", "state"}),
        "Wait for a quiet period",
        "Add a duration such as `.300ms` or `.1s`. Bare `.debounce` uses 250 ms.",
    ),
    _CitryBindingModifierSpec(
        "throttle",
        frozenset({"event", "state"}),
        "Limit how often the binding sends",
        "Add a duration such as `.300ms` or `.1s`. Bare `.throttle` uses 250 ms.",
    ),
    _CitryBindingModifierSpec(
        "lazy",
        frozenset({"state"}),
        "Wait for the committed control value",
        "Use the control's committed-value event instead of its active update event.",
    ),
    _CitryBindingModifierSpec(
        "on",
        frozenset({"state"}),
        "Choose the control's update event",
        "Write `.on:<event>` with any nonempty DOM event name, such as `.on:keyup`.",
        insert_text="on:${1:event}",
    ),
)
_CITRY_BINDING_MODIFIERS_BY_NAME = {spec.name: spec for spec in _CITRY_BINDING_MODIFIERS}
_CITRY_TIMING_EXAMPLES = ("100ms", "250ms", "300ms", "500ms", "1s")
_CITRY_POLL_EXAMPLES = ("1s", "5s", "30s", "60s")
_CITRY_TIME_SEGMENT = re.compile(r"\d+(?:ms|s)\Z")

_ALPINE_SYNTAX = (
    _SyntaxSpec(
        "x-data",
        "attribute",
        "Declare Alpine state",
        "Create the reactive Alpine scope available to this element and its descendants.",
        "https://alpinejs.dev/directives/data",
        insert_text='x-data="${1:{}}"',
    ),
    _SyntaxSpec(
        "x-init",
        "attribute",
        "Initialize an Alpine element",
        "Run this JavaScript statement when Alpine initializes the element.",
        "https://alpinejs.dev/directives/init",
        insert_text='x-init="${1:expression}"',
    ),
    _SyntaxSpec(
        "x-show",
        "attribute",
        "Toggle element visibility",
        "Show the element while this Alpine expression is truthy.",
        "https://alpinejs.dev/directives/show",
        insert_text='x-show="${1:expression}"',
    ),
    _SyntaxSpec(
        "x-bind",
        "attribute",
        "Bind an HTML attribute",
        "Keep an HTML attribute synchronized with an Alpine expression.",
        "https://alpinejs.dev/directives/bind",
        insert_text='x-bind:${1:attribute}="${2:expression}"',
        repeatable=True,
    ),
    _SyntaxSpec(
        "x-on",
        "attribute",
        "Listen for a browser event",
        "Run this Alpine statement when the selected browser event fires.",
        "https://alpinejs.dev/directives/on",
        insert_text='x-on:${1:event}="${2:expression}"',
        repeatable=True,
    ),
    _SyntaxSpec(
        "x-text",
        "attribute",
        "Set text content",
        "Set the element's text content from an Alpine expression.",
        "https://alpinejs.dev/directives/text",
        insert_text='x-text="${1:expression}"',
    ),
    _SyntaxSpec(
        "x-html",
        "attribute",
        "Set HTML content",
        "Set the element's inner HTML from an Alpine expression.",
        "https://alpinejs.dev/directives/html",
        insert_text='x-html="${1:expression}"',
    ),
    _SyntaxSpec(
        "x-model",
        "attribute",
        "Bind a form value",
        "Synchronize a form control's value with Alpine state.",
        "https://alpinejs.dev/directives/model",
        insert_text='x-model="${1:value}"',
    ),
    _SyntaxSpec(
        "x-modelable",
        "attribute",
        "Expose a modelable value",
        "Expose an Alpine property for a parent `x-model` binding.",
        "https://alpinejs.dev/directives/modelable",
        insert_text='x-modelable="${1:value}"',
    ),
    _SyntaxSpec(
        "x-for",
        "attribute",
        "Repeat a template",
        "Render this `<template>` once for each item in an Alpine collection.",
        "https://alpinejs.dev/directives/for",
        insert_text='x-for="${1:item} in ${2:items}"',
    ),
    _SyntaxSpec(
        "x-transition",
        "attribute",
        "Animate visibility changes",
        "Apply an Alpine transition when an element enters or leaves.",
        "https://alpinejs.dev/directives/transition",
        insert_text="x-transition",
    ),
    _SyntaxSpec(
        "x-effect",
        "attribute",
        "Run a reactive effect",
        "Rerun this statement when the Alpine values it reads change.",
        "https://alpinejs.dev/directives/effect",
        insert_text='x-effect="${1:expression}"',
    ),
    _SyntaxSpec(
        "x-ignore",
        "attribute",
        "Skip Alpine initialization",
        "Prevent Alpine from initializing this element and its descendants.",
        "https://alpinejs.dev/directives/ignore",
        insert_text="x-ignore",
    ),
    _SyntaxSpec(
        "x-ref",
        "attribute",
        "Name an element reference",
        "Expose this element through Alpine's `$refs` magic.",
        "https://alpinejs.dev/directives/ref",
        insert_text='x-ref="${1:name}"',
    ),
    _SyntaxSpec(
        "x-cloak",
        "attribute",
        "Hide content until Alpine starts",
        "Keep the element hidden until Alpine has initialized it.",
        "https://alpinejs.dev/directives/cloak",
        insert_text="x-cloak",
    ),
    _SyntaxSpec(
        "x-teleport",
        "attribute",
        "Move template content",
        "Render this `<template>` at the element selected by the expression.",
        "https://alpinejs.dev/directives/teleport",
        insert_text='x-teleport="${1:selector}"',
    ),
    _SyntaxSpec(
        "x-id",
        "attribute",
        "Create scoped IDs",
        "Declare names that Alpine's `$id` magic resolves uniquely in this scope.",
        "https://alpinejs.dev/directives/id",
        insert_text="x-id=\"['${1:name}']\"",
    ),
    _SyntaxSpec(
        "x-if",
        "attribute",
        "Conditionally render a template",
        "Render this `<template>` while the Alpine expression is truthy.",
        "https://alpinejs.dev/directives/if",
        insert_text='x-if="${1:expression}"',
    ),
)
_ALPINE_SYNTAX_BY_LABEL = {spec.label: spec for spec in _ALPINE_SYNTAX}
_ALPINE_TEMPLATE_ONLY = frozenset({"x-for", "x-if", "x-teleport"})
_ALPINE_COMMON_EVENTS = ("click", "submit", "input", "change", "keydown", "keyup", "focus", "blur")
_ALPINE_COMMON_BINDINGS = (
    "class",
    "style",
    "disabled",
    "hidden",
    "value",
    "checked",
    "selected",
    "aria-expanded",
    "aria-controls",
    "aria-current",
    "aria-hidden",
)
_ALPINE_EVENT_COMPLETIONS = tuple(
    _SyntaxSpec(
        f"@{event}",
        "attribute",
        _ALPINE_SYNTAX_BY_LABEL["x-on"].detail,
        _ALPINE_SYNTAX_BY_LABEL["x-on"].documentation,
        _ALPINE_SYNTAX_BY_LABEL["x-on"].documentation_url,
        insert_text=f'@{event}="${{1:expression}}"',
        repeatable=True,
    )
    for event in _ALPINE_COMMON_EVENTS
)
_ALPINE_BINDING_COMPLETIONS = tuple(
    _SyntaxSpec(
        f":{attribute}",
        "attribute",
        _ALPINE_SYNTAX_BY_LABEL["x-bind"].detail,
        _ALPINE_SYNTAX_BY_LABEL["x-bind"].documentation,
        _ALPINE_SYNTAX_BY_LABEL["x-bind"].documentation_url,
        insert_text=f':{attribute}="${{1:expression}}"',
        repeatable=True,
    )
    for attribute in _ALPINE_COMMON_BINDINGS
)

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
_I18N_BINDING_DIRECTIVES = (
    _SyntaxSpec(
        "$c-tr:",
        "attribute",
        "Bind a translated DOM value",
        "Keep server-rendered text or an allowlisted HTML attribute current in the browser.",
        _BROWSER_I18N_URL,
        context="i18n-binding",
        insert_text='\\$c-tr:${1:message}="${2:{}}"',
        repeatable=True,
    ),
    _SyntaxSpec(
        "c-$c-tr:",
        "attribute",
        "Compute a translation values expression in Python",
        "Evaluate Python to produce the Alpine named-values expression for a browser translation binding.",
        _BROWSER_I18N_URL,
        context="i18n-binding",
        insert_text='c-\\$c-tr:${1:message}="${2:expression}"',
        repeatable=True,
    ),
)
_STRUCTURAL_ATTRIBUTES: dict[str, tuple[_SyntaxSpec, ...]] = {
    name: _syntax_specs(kind="attribute", context=name) for name in RESERVED_TAG_NAMES
}
# Slots may also carry condition/loop directives, unlike the other structural
# tags, so add the parser's five control-flow forms after slot-owned fields.
_STRUCTURAL_ATTRIBUTES["c-slot"] = (*_STRUCTURAL_ATTRIBUTES["c-slot"], *_GENERAL_DIRECTIVES[:5])
_DYNAMIC_TARGET_ATTRIBUTES = _syntax_specs(kind="attribute", context="dynamic-target")


def _is_semantic_component_tag(tag_name: str, registered_component: bool = False) -> bool:
    """Return whether Alpine syntax must cross a Citry component boundary."""
    normalized = tag_name.lower()
    return registered_component or (tag_name.startswith("c-") and normalized not in {*RESERVED_TAG_NAMES, "c-element"})


def _alpine_completion_specs(tag_name: str, *, semantic_component: bool) -> tuple[_SyntaxSpec, ...]:
    """Select Alpine spellings that are valid on this authored element."""
    normalized = tag_name.lower()
    if normalized in RESERVED_TAG_NAMES:
        return ()
    event_specs = (_ALPINE_SYNTAX_BY_LABEL["x-on"], *_ALPINE_EVENT_COMPLETIONS)
    if semantic_component:
        # Component boundaries relocate only Alpine event listeners. Other
        # directives belong on the concrete HTML roots inside the component.
        return event_specs
    fixed = tuple(
        spec for spec in _ALPINE_SYNTAX if spec.label not in _ALPINE_TEMPLATE_ONLY or normalized == "template"
    )
    return (*fixed, *_ALPINE_EVENT_COMPLETIONS, *_ALPINE_BINDING_COMPLETIONS)


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
    alpine_labels = [spec.label for spec in _ALPINE_SYNTAX]
    if len(alpine_labels) != len(set(alpine_labels)):
        msg = "Alpine syntax metadata contains a duplicate directive name."
        raise RuntimeError(msg)
    if any(not spec.documentation_url.startswith("https://alpinejs.dev/directives/") for spec in _ALPINE_SYNTAX):
        msg = "Alpine syntax hover metadata must link to canonical Alpine.js directive documentation."
        raise RuntimeError(msg)


_validate_syntax_metadata()


def _citry_binding_reference_at(
    template: Any,
    index: int,
    *,
    base_index: int = 0,
) -> _CitryBindingReference | None:
    """Find one Citry binding-key segment from parser-proven template nodes."""
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        for attr in node.start_tag.attrs:
            name = attr.key.content
            if name.startswith(("@c-", ":c-")) and _token_contains(attr.key, index, base_index=base_index):
                return _citry_binding_part_reference(
                    name,
                    index,
                    base_index + attr.key.start_index,
                )
            if attr.kind != HtmlAttrKind.Template or attr.inner_value is None:
                continue
            parsed_nested = _parse_nested_template(attr.inner_value.content)
            if parsed_nested is None:
                continue
            nested, nested_start = parsed_nested
            reference = _citry_binding_reference_at(
                nested,
                index,
                base_index=base_index + attr.inner_value.start_index + nested_start,
            )
            if reference is not None:
                return reference
        body = getattr(node, "body", None)
        if body is not None:
            reference = _citry_binding_reference_at(body, index, base_index=base_index)
            if reference is not None:
                return reference
    return None


def _citry_binding_part_reference(
    attribute_name: str,
    index: int,
    attribute_start: int,
) -> _CitryBindingReference | None:
    """Split one binding key while retaining exact UTF-8 source ranges."""
    channel: Literal["event", "state"] = "event" if attribute_name.startswith("@c-") else "state"
    parts = attribute_name.split(".")
    base = parts[0]
    base_end = attribute_start + len(base.encode("utf-8"))
    if attribute_start <= index < base_end:
        return _CitryBindingReference(
            channel,
            attribute_name,
            base[3:],
            "base",
            base,
            None,
            attribute_start,
            base_end,
        )

    character_offset = len(base)
    previous_modifier: str | None = None
    for modifier in parts[1:]:
        part_start = character_offset
        part_end = part_start + 1 + len(modifier)
        start_index = attribute_start + len(attribute_name[:part_start].encode("utf-8"))
        end_index = attribute_start + len(attribute_name[:part_end].encode("utf-8"))
        if start_index <= index < end_index:
            return _CitryBindingReference(
                channel,
                attribute_name,
                base[3:],
                "modifier",
                modifier,
                previous_modifier,
                start_index,
                end_index,
            )
        character_offset = part_end
        previous_modifier = modifier
    return None


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
                        attr.key.content,
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
    translated_name = attr_name.removeprefix("c-")
    if looks_like_i18n_binding(translated_name):
        if normalized_tag.startswith("c-"):
            return None
        label = "c-$c-tr:" if attr_name.startswith("c-") else "$c-tr:"
        return next(spec for spec in _I18N_BINDING_DIRECTIVES if spec.label == label)
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
    citry_spec = next(
        (
            spec
            for context in contexts
            for spec in _CITRY_SYNTAX
            if spec.kind == "attribute" and spec.context == context and spec.label == attr_name
        ),
        None,
    )
    return citry_spec or _alpine_attribute_spec(tag_name, attr_name)


def _alpine_attribute_spec(tag_name: str, attr_name: str) -> _SyntaxSpec | None:
    """Resolve one core Alpine directive without claiming Citry-owned channels."""
    if attr_name.startswith(("@c-", ":c-")):
        return None
    canonical = attr_name.lower()
    spec: _SyntaxSpec | None
    if canonical.startswith(("@", "x-on:")):
        spec = _ALPINE_SYNTAX_BY_LABEL["x-on"]
    elif canonical.startswith((":", "x-bind:")):
        spec = _ALPINE_SYNTAX_BY_LABEL["x-bind"]
    else:
        base_name = canonical.split(".", 1)[0]
        if base_name.startswith("x-transition:"):
            base_name = "x-transition"
        spec = _ALPINE_SYNTAX_BY_LABEL.get(base_name)
    if spec is None:
        return None
    if _is_semantic_component_tag(tag_name) and spec.label != "x-on":
        return None
    if spec.label in _ALPINE_TEMPLATE_ONLY and tag_name.lower() != "template":
        return None
    return spec


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
                tag_text[name_start:name_end],
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


def _syntax_markdown(spec: _SyntaxSpec, display_label: str | None = None) -> str:
    """Render one concise first-party hover with its canonical guide link."""
    subject = f"<{spec.label}>" if spec.kind == "tag" else display_label or spec.label
    documentation_owner = "Alpine.js" if spec.documentation_url.startswith("https://alpinejs.dev/") else "Citry"
    return (
        f"### `{subject}`\n\n{spec.documentation}\n\n"
        f"[Read the {documentation_owner} documentation]({spec.documentation_url})"
    )


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
    semantic_component = _is_semantic_component_tag(tag_name, registered_component)
    if normalized_tag in _STRUCTURAL_ATTRIBUTES:
        specs = _STRUCTURAL_ATTRIBUTES[normalized_tag]
    elif normalized_tag == "c-component":
        specs = (*_DYNAMIC_TARGET_ATTRIBUTES, *_GENERAL_DIRECTIVES, *_CLIENT_PROP_DIRECTIVES)
    elif normalized_tag == "c-element":
        specs = (*_DYNAMIC_TARGET_ATTRIBUTES, *_GENERAL_DIRECTIVES)
    else:
        i18n_specs = () if semantic_component or normalized_tag.startswith("c-") else _I18N_BINDING_DIRECTIVES
        specs = (*_GENERAL_DIRECTIVES, *(_CLIENT_PROP_DIRECTIVES if semantic_component else ()), *i18n_specs)
    specs = (*specs, *_alpine_completion_specs(tag_name, semantic_component=semantic_component))

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

    active: tuple[str, int, int, int | None] | None = None
    for attribute in attributes:
        _name, start, end, assignment = attribute
        if start <= cursor <= end or (assignment is not None and end < cursor < assignment):
            active = attribute
            break

    # The position immediately after a complete name is also the position of
    # its following `=`. Keep that boundary owned by the name so completion can
    # replace a just-typed modifier without disturbing the existing value.
    active_name_end = active is not None and cursor == active[2]
    if not active_name_end and any(
        start <= cursor < end or (include_end and cursor == end) for start, end, include_end in blocked
    ):
        return None, False

    if active is None:
        if cursor == 0 or not source[cursor - 1].isspace():
            return None, False
        edit_start = edit_end = cursor
        preserve_value = False
        authored_name = ""
    else:
        authored_name, edit_start, edit_end, assignment = active
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
    return (
        _AttributeCompletionContext(
            mapped,
            authored_attrs,
            preserve_value,
            authored_name,
            edit_start,
            edit_end,
        ),
        True,
    )


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
    member_match = re.fullmatch(r"([A-Za-z_$][\w$]*)\??\.([A-Za-z_$][\w$]*)", source)
    if member_match is not None:
        owner, member = member_match.groups()
        root = next((candidate for candidate in roots if candidate.name == owner), None)
        if root is not None and root.wire_type.kind == "object":
            field = next((candidate for candidate in root.wire_type.fields if candidate.name == member), None)
            if field is not None:
                return field.value
            if root.wire_type.additional is not None:
                return root.wire_type.additional
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
    "$i18n": _BrowserApiSpec(
        "magic",
        "CitryI18nService",
        "Translate, format, parse, or switch locale inside the nearest client-enabled i18n subtree.",
        "https://citry.dev/i18n/browser/",
    ),
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
    "i18n": _BrowserApiSpec(
        "parameter",
        "CitryI18nService | null",
        "The nearest browser i18n service, or null outside a client-enabled i18n subtree.",
        "https://citry.dev/i18n/browser/",
    ),
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
        if identifier is None:
            return None
        if identifier.name == "$i18n":
            if "$i18n" not in expression.bindings:
                return None
        elif not identifier.root:
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
        if binding.name == "i18n" and (project.i18n is None or not project.i18n.configured):
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
    i18n: Any | None = None,
) -> str:
    """Render collision-tolerant JSDoc facts for VS Code's JS provider."""
    lines = ["// Generated Citry browser-analysis declarations."]
    lines.extend(_i18n_browser_typedefs(i18n))
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
        if binding == "$i18n" and i18n is not None and i18n.configured:
            binding_type = "CitryI18nService"
        elif binding == "i18n" and i18n is not None and i18n.configured:
            binding_type = "CitryI18nService | null"
        else:
            binding_type = (binding_types or {}).get(binding, JsonWireType("unknown")).javascript
        lines.extend((f"/** @type {{{binding_type}}} */", f"var {binding};"))
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
            " * @property {CitryI18nService | null} i18n",
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


def _i18n_browser_typedefs(index: Any) -> tuple[str, ...]:
    """Render the checked browser i18n service shape for the JS provider."""

    def profiles(namespace: str, operation: str) -> str:
        if index is None or not index.configured:
            return "string"
        names = index.profile_names(namespace, operation)
        return " | ".join(_js_string_literal(name) for name in names) or "string"

    number = profiles("format", "number")
    percent = profiles("format", "percent")
    currency = profiles("format", "currency")
    date = profiles("format", "date")
    time = profiles("format", "time")
    datetime = profiles("format", "datetime")
    relative_time = profiles("format", "relative_time")
    list_ = profiles("format", "list")
    unit = profiles("format", "unit")
    parse_number = profiles("parse", "number")
    parse_percent = profiles("parse", "percent")
    return (
        "/** @typedef {'ltr' | 'rtl'} CitryI18nDirection */",
        "/** @typedef {Object} CitryI18nContext",
        " * @property {string} locale",
        " * @property {CitryI18nDirection} direction",
        " * @property {readonly string[]} fallback_locales",
        " * @property {string | null} time_zone",
        " * @property {string} catalog_revision",
        " * @property {string} formats_revision",
        " * @property {string} tzdb_revision",
        " */",
        "/** @typedef {Object} CitryI18nNumericParseResult",
        " * @property {'valid' | 'incomplete' | 'invalid'} state",
        " * @property {boolean} valid",
        " * @property {string | null} value",
        " * @property {string | null} error",
        " * @property {string} input",
        " */",
        "/** @typedef {Object} CitryI18nResolvedMessage",
        " * @property {CitryI18nDirection} direction",
        " * @property {string} locale",
        " * @property {string} text",
        " * @property {boolean} usedFallback",
        " */",
        "/** @typedef {Object} CitryI18nBinding",
        " * @property {() => void} dispose",
        " * @property {() => void} refresh",
        " */",
        "/** @typedef {Object} CitryI18nFormatter",
        f" * @property {{(value: unknown, options: {{format: {number}}}) => string}} number",
        f" * @property {{(value: unknown, options: {{format: {percent}}}) => string}} percent",
        f" * @property {{(value: unknown, currency: string, options: {{format: {currency}}}) => string}} currency",
        " * @property {"
        f"(value: {{year: number, month: number, day: number}}, options: {{format: {date}}}) => string"
        "} date",
        " * @property {"
        f"(value: {{hour: number, minute: number, second?: number, millisecond?: number}}, "
        f"options: {{format: {time}}}) => string"
        "} time",
        f" * @property {{(value: Date, options: {{format: {datetime}}}) => string}} datetime",
        " * @property {"
        f"(value: unknown, options: {{format: {relative_time}, unit: string}}) => string"
        "} relativeTime",
        f" * @property {{(values: readonly string[], options: {{format: {list_}}}) => string}} list",
        f" * @property {{(value: unknown, unit: string, options: {{format: {unit}}}) => string}} unit",
        " */",
        "/** @typedef {Object} CitryI18nParser",
        f" * @property {{(input: string, options: {{format: {parse_number}}}) => CitryI18nNumericParseResult}} number",
        " * @property {"
        f"(input: string, options: {{format: {parse_percent}}}) => CitryI18nNumericParseResult"
        "} percent",
        " */",
        "/** @typedef {Object} CitryI18nService",
        " * @property {Readonly<CitryI18nContext>} context",
        " * @property {CitryI18nFormatter} format",
        " * @property {CitryI18nParser} parse",
        " * @property {"
        "(message: string, values?: Readonly<Record<string, unknown>>, options?: {attr?: string}) => string"
        "} tr",
        " * @property {"
        "(message: string, values?: Readonly<Record<string, unknown>>, options?: {attr?: string}) => "
        "Readonly<CitryI18nResolvedMessage>"
        "} resolve",
        " * @property {"
        "(options: {message: string, output?: string, values?: () => Readonly<Record<string, unknown>>, "
        "onChange: (text: string, resolved: Readonly<CitryI18nResolvedMessage>) => void}) => CitryI18nBinding"
        "} bind",
        " * @property {(messages: string | readonly string[]) => Promise<void>} ensureMessages",
        " * @property {"
        "(locale: string) => Promise<Readonly<{status: 'committed' | 'stale', context?: CitryI18nContext}>>"
        "} switchLocale",
        " */",
    )


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


def _citry_binding_modifier_completion_result(
    document: DocumentState,
    position: types.Position,
) -> CompletionResult | None:
    """Complete only modifiers accepted by the active Citry binding channel."""
    region = document.region_at(position)
    if region is None:
        return None
    parser_index = region.source_map.parser_index_at(_citry_position(position))
    if parser_index is None:
        return None
    source = region.source_map.template_source
    cursor = parser_char_index(source, parser_index)
    chain = _unfinished_start_tag_chain(source[:cursor])
    if not chain:
        return None
    tag_start, _tag_name, _tag_text = chain[-1]
    context, attribute_position = _attribute_completion_context(
        document,
        region,
        source,
        tag_start,
        cursor,
    )
    if not attribute_position or context is None:
        return None
    authored_name = context.authored_name
    if authored_name.startswith("@c-"):
        channel: Literal["event", "state"] = "event"
    elif authored_name.startswith(":c-"):
        channel = "state"
    else:
        return None

    relative_cursor = cursor - context.start_index
    modifier_dot = authored_name.rfind(".", 3, relative_cursor)
    if modifier_dot < 0:
        return None
    segment_start = modifier_dot + 1
    next_dot = authored_name.find(".", relative_cursor)
    segment_end = len(authored_name) if next_dot < 0 else next_dot
    prefix = authored_name[segment_start:relative_cursor]
    parts = authored_name.split(".")
    current_part = authored_name[:relative_cursor].count(".")
    previous_modifier = parts[current_part - 1] if current_part > 1 else None
    used = {
        "on" if value.startswith("on:") else value
        for index, value in enumerate(parts[1:], start=1)
        if index != current_part and value
    }
    edit_range = _mapped_template_range(
        region,
        source,
        context.start_index + segment_start,
        context.start_index + segment_end,
    )
    if edit_range is None:
        return CompletionResult((), is_incomplete=True)

    base_name = parts[0][3:]
    candidates = _citry_binding_modifier_candidates(channel, base_name, previous_modifier, used)
    items: list[types.CompletionItem] = []
    for label, filter_text, new_text, detail, documentation, snippet in candidates:
        if not filter_text.startswith(prefix):
            continue
        items.append(
            types.CompletionItem(
                label=label,
                kind=types.CompletionItemKind.Keyword,
                detail=detail,
                documentation=_markdown(f"{documentation}\n\n[Read the Citry documentation]({_EVENT_BINDINGS_URL})"),
                filter_text=filter_text,
                insert_text_format=(types.InsertTextFormat.Snippet if snippet else types.InsertTextFormat.PlainText),
                text_edit=types.TextEdit(edit_range, new_text),
            )
        )
    return CompletionResult(tuple(items), is_incomplete=True)


def _citry_binding_modifier_candidates(
    channel: Literal["event", "state"],
    base_name: str,
    previous_modifier: str | None,
    used: set[str],
) -> tuple[tuple[str, str, str, str, str, bool], ...]:
    """Build channel-aware modifier choices, including representative durations."""
    if channel == "event" and base_name == "poll":
        return tuple(
            (
                f".{duration}",
                duration,
                duration,
                "Citry polling interval",
                "Use one whole-second interval such as `.30s`.",
                False,
            )
            for duration in _CITRY_POLL_EXAMPLES
        )

    candidates: list[tuple[str, str, str, str, str, bool]] = []
    if previous_modifier in {"debounce", "throttle"}:
        candidates.extend(
            (
                f".{duration}",
                duration,
                duration,
                "Citry timing duration",
                "Use a whole number followed by `ms` or `s`, such as `.300ms` or `.1s`.",
                False,
            )
            for duration in _CITRY_TIMING_EXAMPLES
        )
    key_filter_used = bool(used & {"enter", "escape"})
    for spec in _CITRY_BINDING_MODIFIERS:
        if channel not in spec.channels or spec.name in used:
            continue
        if key_filter_used and spec.name in {"enter", "escape"}:
            continue
        if (spec.name == "lazy" and "on" in used) or (spec.name == "on" and "lazy" in used):
            continue
        label = ".on:<event>" if spec.name == "on" else f".{spec.name}"
        filter_text = "on:" if spec.name == "on" else spec.name
        candidates.append(
            (
                label,
                filter_text,
                spec.insert_text or spec.name,
                spec.detail,
                spec.documentation,
                spec.insert_text is not None,
            )
        )
    return tuple(candidates)


def _browser_event_completion_result(
    document: DocumentState,
    position: types.Position,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState] | None,
) -> CompletionResult | None:
    """Complete server handlers in Citry calls and declarative binding values."""
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
        r"(?:^|[ \t\r\n])(?:@c-|:c-)[^\s=/>]+\s*=\s*(['\"])([^'\"()\s]*)$",
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


def _shared_state_field_records(
    consumers: tuple[ComponentRecord, ...],
    project: ProjectState,
    name: str,
) -> tuple[SourceStateFieldRecord, ...]:
    """Return one public State field record from every proven template owner."""
    if not consumers or project.source_analysis is None:
        return ()
    records: list[SourceStateFieldRecord] = []
    for component in consumers:
        fields = project.source_analysis.state_fields(component)
        if fields is None:
            return ()
        field = next((candidate for candidate in fields if candidate.name == name), None)
        if field is None:
            return ()
        records.append(field)
    return tuple(records)


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
            match = component_name_match(
                prefix,
                label,
                is_class_name=is_class_name,
                variant_index=variant_index,
            )
            if match is None:
                continue
            items.append(
                types.CompletionItem(
                    label=label,
                    kind=types.CompletionItemKind.Class,
                    detail=_component_detail(component),
                    documentation=_markdown(component.description),
                    insert_text=label,
                    filter_text=match.filter_text,
                    sort_text=match.sort_text,
                    text_edit=types.InsertReplaceEdit(
                        new_text=label,
                        insert=edit_range,
                        replace=edit_range,
                    ),
                )
            )
    return items


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
    "i18n_diagnostics",
    "map_expression_shadow_range",
    "references",
    "render_template_variable_hover",
    "semantic_dependencies",
    "template_lint_diagnostics",
    "template_variable_hover",
]
