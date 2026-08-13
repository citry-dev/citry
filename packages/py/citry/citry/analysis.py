"""Supported template analysis and Python-to-LSP source coordinates."""

from __future__ import annotations

import ast
import hashlib
import re
import unicodedata
from bisect import bisect_left, bisect_right
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from itertools import pairwise
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from citry._alpine_csp import classify_alpine_csp
from citry._browser_expressions import (
    SERVER_EVENT_CALL_NAMES,
    BrowserBinding,
    BrowserCompletion,
    BrowserComponentBinding,
    BrowserComponentPropsUse,
    BrowserComponentSourceAnalysis,
    BrowserDeclarativeEvent,
    BrowserExpression,
    BrowserExpressionMode,
    BrowserFreeReference,
    BrowserI18nBindingDirective,
    BrowserI18nMessageCall,
    BrowserI18nProfileCall,
    BrowserIdentifier,
    BrowserLiteralCall,
    BrowserMember,
    BrowserMemberLiteralCall,
    BrowserObjectProperty,
    BrowserProp,
    BrowserScopeWrite,
    BrowserSourceAnalysis,
    analyze_browser_component_source,
    analyze_browser_expression,
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
    browser_member_literal_calls,
)
from citry._browser_expressions import (
    python_event_handler_coordinates as _python_event_handler_coordinates,
)
from citry._diagnostic_catalog import (
    ALPINE_UNKNOWN_VARIABLE,
    COMPONENT_JS_UNKNOWN_VARIABLE,
    CSP_INCOMPATIBLE_BROWSER_CODE,
    FORMAT_EMBEDDED_INTERPOLATION_UNSUPPORTED,
    FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED,
    FORMAT_HOST_SYNTAX,
    FORMAT_INELIGIBLE,
    FORMAT_INVARIANT,
    FORMAT_PROVIDER_INVALID,
    FORMAT_PROVIDER_UNAVAILABLE,
    TEMPLATE_UNKNOWN_VARIABLE,
)
from citry._diagnostics import render_diagnostic
from citry._inline_assets import normalize_inline_asset
from citry._json_wire import JsonWireField, JsonWireKind, JsonWireType, merge_json_wire_types
from citry._json_wire import json_wire_type_from_annotation as _json_wire_type_from_annotation
from citry._json_wire import json_wire_type_from_expression as _json_wire_type_from_expression
from citry._linting import TemplateLintInfo
from citry._portable_ide import (
    ComponentNameMatch,
    TemplateTagUse,
    UnknownComponentUse,
    component_name_match,
    template_tag_uses,
    unknown_component_uses,
)
from citry._template_python import ShadowPythonCopy as _ShadowPythonCopy
from citry._template_python import ShadowPythonDocument as _ShadowPythonDocument
from citry._template_python import ShadowPythonSourceCopy as _ShadowPythonSourceCopy
from citry._template_python import TemplatePythonControl as _TemplatePythonControl
from citry._template_python import TemplatePythonQuery as _TemplatePythonQuery
from citry._template_python import TemplatePythonRoot as _TemplatePythonRoot
from citry._template_python import build_inferred_template_shadow as _build_inferred_template_shadow
from citry._template_python import build_schema_template_shadow as _build_schema_template_shadow
from citry._template_python import template_python_queries as _template_python_queries
from citry._template_python import template_python_query_at as _template_python_query_at
from citry_core.template_formatter import (
    EmbeddedFormatPlan as _CoreEmbeddedFormatPlan,
)
from citry_core.template_formatter import (
    EmbeddedFormatResult,
    EmbeddedLanguage,
    EmbeddedRegionKind,
    EmbeddedResultStatus,
)
from citry_core.template_formatter import (
    TemplateFormatError as _CoreTemplateFormatError,
)
from citry_core.template_formatter import (
    finish_embedded_format as _finish_embedded_format,
)
from citry_core.template_formatter import format_template as _format_template
from citry_core.template_formatter import (
    prepare_embedded_format as _prepare_embedded_format,
)
from citry_core.template_parser import TagRules
from citry_core.template_parser import parse_template as _parse_template

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry._template_data_source import TemplateDataSourceShape
    from citry_core.template_parser import Template


TEMPLATE_ANALYSIS_SCHEMA_VERSION = 1
# Compatibility name for callers that already import the analysis constant.
UNKNOWN_TEMPLATE_VARIABLE_CODE = TEMPLATE_UNKNOWN_VARIABLE

# Keep the portable query records on the supported analysis surface while the
# implementation details remain in a focused private module.
TemplatePythonControl = _TemplatePythonControl
TemplatePythonQuery = _TemplatePythonQuery
TemplatePythonRoot = _TemplatePythonRoot
ShadowPythonCopy = _ShadowPythonCopy
ShadowPythonDocument = _ShadowPythonDocument
ShadowPythonSourceCopy = _ShadowPythonSourceCopy


@dataclass(frozen=True, slots=True)
class CssDataReference:
    """One exact unescaped ``var(--name)`` custom-property reference."""

    name: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class CssDataCompletion:
    """One incomplete or complete custom-property token at the cursor."""

    prefix: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class TemplateLintConsumer:
    """
    Describe one proven component namespace used by a physical template.

    Attributes:
        known_names: Root names available to this component's template.
        namespace_policy: Whether those names exhaust normalized template data.
        rule_unknown_template_variable: Configured severity for undeclared
            free roots.

    """

    known_names: frozenset[str]
    namespace_policy: Literal["closed", "allow-extra", "unknown"]
    rule_unknown_template_variable: Literal["ignore", "warning", "error"]

    def __post_init__(self) -> None:
        if type(self.known_names) is not frozenset or any(
            type(name) is not str or not name for name in self.known_names
        ):
            msg = "TemplateLintConsumer.known_names must be a frozenset of non-empty strings"
            raise TypeError(msg)
        if type(self.namespace_policy) is not str or self.namespace_policy not in {
            "closed",
            "allow-extra",
            "unknown",
        }:
            msg = f"Unknown template namespace policy: {self.namespace_policy!r}"
            raise ValueError(msg)
        if type(self.rule_unknown_template_variable) is not str or self.rule_unknown_template_variable not in {
            "ignore",
            "warning",
            "error",
        }:
            msg = f"Unknown template-variable rule severity: {self.rule_unknown_template_variable!r}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class TemplateLintFinding:
    """Report one parser-proven free root missing from a known namespace."""

    name: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class AlpineLintConsumer:
    """Describe one proven browser namespace used by a physical template."""

    known_names: frozenset[str]
    rule_unknown_alpine_variable: Literal["ignore", "warning", "error"]

    def __post_init__(self) -> None:
        if type(self.known_names) is not frozenset or any(
            type(name) is not str or not name for name in self.known_names
        ):
            msg = "AlpineLintConsumer.known_names must be a frozenset of non-empty strings"
            raise TypeError(msg)
        if type(self.rule_unknown_alpine_variable) is not str or self.rule_unknown_alpine_variable not in {
            "ignore",
            "warning",
            "error",
        }:
            msg = f"Unknown Alpine-variable rule severity: {self.rule_unknown_alpine_variable!r}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class AlpineLintFinding:
    """Report one OXC-proven free root missing from a browser namespace."""

    name: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class CspCompatibilityFinding:
    """Report one browser host incompatible with the selected Alpine CSP build."""

    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class ComponentJsLintConsumer:
    """Describe globals and severity for one component JavaScript consumer."""

    known_names: frozenset[str]
    rule_unknown_component_js_variable: Literal["ignore", "warning", "error"]

    def __post_init__(self) -> None:
        if type(self.known_names) is not frozenset or any(
            type(name) is not str or not name for name in self.known_names
        ):
            msg = "ComponentJsLintConsumer.known_names must be a frozenset of non-empty strings"
            raise TypeError(msg)
        if type(self.rule_unknown_component_js_variable) is not str or self.rule_unknown_component_js_variable not in {
            "ignore",
            "warning",
            "error",
        }:
            msg = f"Unknown component-JavaScript-variable rule severity: {self.rule_unknown_component_js_variable!r}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ComponentJsLintFinding:
    """Report one OXC-proven free name inside a `$component` initializer."""

    name: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int


COMPONENT_JS_AMBIENT_NAMES = frozenset(
    {
        # ECMAScript built-ins and browser globals are supplied by the runtime,
        # not by the component callback's destructuring pattern.
        "AggregateError",
        "Array",
        "ArrayBuffer",
        "Atomics",
        "BigInt",
        "BigInt64Array",
        "BigUint64Array",
        "Boolean",
        "CustomEvent",
        "DataView",
        "Date",
        "Element",
        "Error",
        "EvalError",
        "Event",
        "FinalizationRegistry",
        "Float32Array",
        "Float64Array",
        "Function",
        "HTMLElement",
        "Infinity",
        "Int16Array",
        "Int32Array",
        "Int8Array",
        "Intl",
        "JSON",
        "Map",
        "Math",
        "NaN",
        "Number",
        "Object",
        "Promise",
        "Proxy",
        "RangeError",
        "ReferenceError",
        "Reflect",
        "RegExp",
        "Set",
        "SharedArrayBuffer",
        "String",
        "Symbol",
        "SyntaxError",
        "TypeError",
        "URIError",
        "URL",
        "URLSearchParams",
        "Uint16Array",
        "Uint32Array",
        "Uint8Array",
        "Uint8ClampedArray",
        "WeakMap",
        "WeakRef",
        "WeakSet",
        "WebAssembly",
        "cancelAnimationFrame",
        "clearInterval",
        "clearTimeout",
        "console",
        "decodeURI",
        "decodeURIComponent",
        "document",
        "encodeURI",
        "encodeURIComponent",
        "escape",
        "eval",
        "fetch",
        "globalThis",
        "history",
        "isFinite",
        "isNaN",
        "localStorage",
        "location",
        "navigator",
        "parseFloat",
        "parseInt",
        "performance",
        "queueMicrotask",
        "requestAnimationFrame",
        "sessionStorage",
        "setInterval",
        "setTimeout",
        "structuredClone",
        "undefined",
        "unescape",
        "window",
    }
)


ALPINE_AMBIENT_NAMES = frozenset(
    {
        *COMPONENT_JS_AMBIENT_NAMES,
        # Alpine's documented magic properties.
        "$data",
        "$dispatch",
        "$el",
        "$event",
        "$id",
        "$nextTick",
        "$refs",
        "$root",
        "$store",
        "$watch",
        # Citry's Alpine magic/context surface.
        "$error",
        "$inject",
        "$loading",
        "$onEvent",
        "$provide",
        "$sendEvent",
        "$state",
        "$unprovide",
        "sendEvent",
        "onEvent",
    }
)


def lint_unknown_template_variables(
    template: object,
    consumers: Sequence[TemplateLintConsumer],
) -> tuple[TemplateLintFinding, ...]:
    """
    Diagnose free roots missing from at least one proven component namespace.

    Args:
        template: Parsed Citry template AST. Its parser-reported free variables
            already exclude lexical and Python-local bindings.
        consumers: Every proven component that consumes this physical template.

    Returns:
        Findings in the parser's stable free-variable order. No consumer means
        no finding because syntax-only analysis cannot prove ownership.

    Raises:
        TypeError: If the parsed object lacks Citry free-variable records.

    """
    if not consumers:
        return ()
    uses = getattr(template, "used_variables", None)
    if type(uses) is not list:
        msg = "template must expose parser-reported used_variables"
        raise TypeError(msg)

    findings: list[TemplateLintFinding] = []
    normalized_consumers = [
        (consumer, {_identifier_identity(name) for name in consumer.known_names}) for consumer in consumers
    ]
    for use in uses:
        name = getattr(use, "content", None)
        start_index = getattr(use, "start_index", None)
        end_index = getattr(use, "end_index", None)
        line_col = getattr(use, "line_col", None)
        if (
            type(name) is not str
            or type(start_index) is not int
            or type(end_index) is not int
            or type(line_col) is not tuple
            or len(line_col) != 2
            or type(line_col[0]) is not int
            or type(line_col[1]) is not int
        ):
            msg = "template used_variables contains an invalid token"
            raise TypeError(msg)
        missing = [
            consumer for consumer, known_names in normalized_consumers if _identifier_identity(name) not in known_names
        ]
        active = [consumer for consumer in missing if consumer.rule_unknown_template_variable != "ignore"]
        if not active:
            continue
        severity: Literal["warning", "error"] = (
            "error"
            if any(
                consumer.rule_unknown_template_variable == "error" and consumer.namespace_policy != "allow-extra"
                for consumer in active
            )
            else "warning"
        )
        policies = {consumer.namespace_policy for consumer in active}
        if policies == {"allow-extra"}:
            variant = "allow-extra"
        elif "unknown" in policies:
            variant = "unknown"
        else:
            variant = "closed"
        findings.append(
            TemplateLintFinding(
                name=name,
                message=render_diagnostic(TEMPLATE_UNKNOWN_VARIABLE, variant=variant, name=name),
                code=UNKNOWN_TEMPLATE_VARIABLE_CODE,
                severity=severity,
                start_index=start_index,
                end_index=end_index,
                line=line_col[0],
                column=line_col[1],
            )
        )
    return tuple(findings)


def lint_unknown_alpine_variables(
    expressions: Sequence[BrowserExpression],
    consumers: Sequence[AlpineLintConsumer],
) -> tuple[AlpineLintFinding, ...]:
    """Diagnose OXC-proven Alpine roots missing from any physical owner."""
    if not consumers:
        return ()
    findings: list[AlpineLintFinding] = []
    for expression in expressions:
        analysis = analyze_browser_expression(expression)
        if not analysis.valid:
            continue
        lexical = frozenset((*ALPINE_AMBIENT_NAMES, *expression.bindings))
        for reference in analysis.references:
            if reference.name in lexical:
                continue
            missing = [consumer for consumer in consumers if reference.name not in consumer.known_names]
            active = [consumer for consumer in missing if consumer.rule_unknown_alpine_variable != "ignore"]
            if not active:
                continue
            severity: Literal["warning", "error"] = (
                "error" if any(consumer.rule_unknown_alpine_variable == "error" for consumer in active) else "warning"
            )
            findings.append(
                AlpineLintFinding(
                    name=reference.name,
                    message=render_diagnostic(ALPINE_UNKNOWN_VARIABLE, name=reference.name),
                    code=ALPINE_UNKNOWN_VARIABLE,
                    severity=severity,
                    start_index=reference.start_index,
                    end_index=reference.end_index,
                )
            )
    return tuple(findings)


def lint_csp_compatibility(
    expressions: Sequence[BrowserExpression],
    consumers: Sequence[AlpineLintConsumer],
    mode: Literal["off", "warn", "strict"] | None,
) -> tuple[CspCompatibilityFinding, ...]:
    """Diagnose source-proven incompatibilities with Alpine CSP 3.16.1."""
    if mode in {None, "off"}:
        return ()
    if mode not in {"warn", "strict"}:
        msg = f"Unknown CSP compatibility mode: {mode!r}"
        raise ValueError(msg)
    severity: Literal["warning", "error"] = "warning" if mode == "warn" else "error"
    findings: list[CspCompatibilityFinding] = []
    seen: set[tuple[int, int, str]] = set()
    for expression in expressions:
        classification = classify_alpine_csp(expression)
        if classification.outcome == "incompatible":
            detail = classification.detail or "this browser expression"
            _append_csp_finding(
                findings,
                seen,
                detail,
                severity,
                classification.start_index,
                classification.end_index,
            )
            continue
        if not consumers:
            continue
        analysis = analyze_browser_expression(expression)
        if not analysis.valid:
            continue
        lexical = frozenset(expression.bindings)
        for reference in analysis.references:
            if (
                reference.name == "undefined"
                or reference.name in lexical
                or reference.name not in COMPONENT_JS_AMBIENT_NAMES
            ):
                continue
            if any(reference.name not in consumer.known_names for consumer in consumers):
                _append_csp_finding(
                    findings,
                    seen,
                    f"the unprovided JavaScript global {reference.name!r}",
                    severity,
                    reference.start_index,
                    reference.end_index,
                )
                break
    return tuple(findings)


def _append_csp_finding(
    findings: list[CspCompatibilityFinding],
    seen: set[tuple[int, int, str]],
    detail: str,
    severity: Literal["warning", "error"],
    start_index: int,
    end_index: int,
) -> None:
    key = (start_index, end_index, CSP_INCOMPATIBLE_BROWSER_CODE)
    if key in seen:
        return
    seen.add(key)
    findings.append(
        CspCompatibilityFinding(
            message=render_diagnostic(CSP_INCOMPATIBLE_BROWSER_CODE, detail=detail),
            code=CSP_INCOMPATIBLE_BROWSER_CODE,
            severity=severity,
            start_index=start_index,
            end_index=end_index,
        )
    )


def lint_unknown_component_js_variables(
    source: str,
    consumers: Sequence[ComponentJsLintConsumer],
) -> tuple[ComponentJsLintFinding, ...]:
    """Diagnose free names inside proven `$component` initializers."""
    if not consumers:
        return ()
    analysis = analyze_browser_component_source(source)
    if not analysis.valid:
        return ()
    findings: list[ComponentJsLintFinding] = []
    for reference in analysis.references:
        if reference.name in COMPONENT_JS_AMBIENT_NAMES:
            continue
        missing = [consumer for consumer in consumers if reference.name not in consumer.known_names]
        active = [consumer for consumer in missing if consumer.rule_unknown_component_js_variable != "ignore"]
        if not active:
            continue
        severity: Literal["warning", "error"] = (
            "error"
            if any(consumer.rule_unknown_component_js_variable == "error" for consumer in active)
            else "warning"
        )
        findings.append(
            ComponentJsLintFinding(
                name=reference.name,
                message=render_diagnostic(COMPONENT_JS_UNKNOWN_VARIABLE, name=reference.name),
                code=COMPONENT_JS_UNKNOWN_VARIABLE,
                severity=severity,
                start_index=reference.start_index,
                end_index=reference.end_index,
            )
        )
    return tuple(findings)


def _identifier_identity(name: str) -> str:
    """Join parser tokens and Python schema fields by normalized identifier identity."""
    return unicodedata.normalize("NFKC", name)


def template_python_query_at(
    template: object,
    index: int,
    *,
    parse_nested: Callable[[str], object] = _parse_template,
) -> TemplatePythonQuery | None:
    """
    Return the analyzer context for one parser byte index in a template.

    Args:
        template: Parsed Citry template AST.
        index: UTF-8 byte index in the parsed template source.
        parse_nested: Parser used for nested-template attribute values.

    Returns:
        The exact Python host and lexical controls, or ``None`` outside one.

    """
    return _template_python_query_at(template, index, parse_nested=parse_nested)


def template_python_queries(
    template: object,
    *,
    parse_nested: Callable[[str], object] = _parse_template,
) -> tuple[TemplatePythonQuery, ...]:
    """
    Return every analyzer-ready Python host in a parsed template.

    Args:
        template: Parsed Citry template AST.
        parse_nested: Parser used for nested-template attribute values.

    Returns:
        Analyzer-ready hosts ordered by their authored source position.

    """
    return _template_python_queries(template, parse_nested=parse_nested)


def build_inferred_template_shadow(
    module_source: str,
    class_qualname: str,
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    source_module: str | None = None,
    source_is_package: bool = False,
    kwargs_type: tuple[str, str] | None = None,
) -> ShadowPythonDocument | None:
    """
    Build analyzer input from one statically accepted ``template_data`` method.

    Args:
        module_source: Current Python module source.
        class_qualname: Exact class that directly owns ``template_data``.
        roots: Conservatively proven template roots.
        query: Authored expression and its lexical template controls.
        source_module: Importable module name used to mirror relative imports.
        source_is_package: Whether that module is implemented by ``__init__.py``.
        kwargs_type: Optional module and qualified name for typed ``Kwargs``.

    Returns:
        Generated Python plus exact source mappings, or ``None`` when the
        source no longer matches the accepted static shape.

    """
    return _build_inferred_template_shadow(
        module_source,
        class_qualname,
        roots,
        query,
        source_module=source_module,
        source_is_package=source_is_package,
        kwargs_type=kwargs_type,
    )


def build_schema_template_shadow(
    module_source: str,
    schema_qualname: str,
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    source_module: str | None = None,
    source_is_package: bool = False,
) -> ShadowPythonDocument | None:
    """
    Build analyzer input from one statically resolved ``TemplateData`` schema.

    Args:
        module_source: Current Python module source.
        schema_qualname: Exact qualified name of the schema class.
        roots: Conservatively proven template roots.
        query: Authored expression and its lexical template controls.
        source_module: Importable module name used to mirror relative imports.
        source_is_package: Whether that module is implemented by ``__init__.py``.

    Returns:
        Generated Python plus exact source mappings, or ``None`` when the
        schema cannot be resolved from current source.

    """
    return _build_schema_template_shadow(
        module_source,
        schema_qualname,
        roots,
        query,
        source_module=source_module,
        source_is_package=source_is_package,
    )


@dataclass(frozen=True, slots=True)
class LspPosition:
    """
    A zero-based line and UTF-16 character position used by LSP clients.

    Attributes:
        line: Zero-based source line.
        character: Zero-based UTF-16 code-unit offset on that line.

    """

    line: int
    character: int


@dataclass(frozen=True, slots=True)
class LspRange:
    """
    A half-open LSP range in a source document.

    Attributes:
        start: Inclusive start position.
        end: Exclusive end position.

    """

    start: LspPosition
    end: LspPosition


@dataclass(frozen=True, slots=True, init=False)
class TemplateAnalysis:
    """
    A complete, immutable snapshot of one Citry component registry.

    Attributes:
        component_names: Normalized registered names without the ``c-`` tag
            prefix. The set includes aliases and built-in component names.
        lint: Application lint settings and known global variables.
        component_lint: Effective lint settings and known variables keyed by
            stable component definition ID.

    """

    component_names: frozenset[str]
    lint: TemplateLintInfo
    component_lint: Mapping[str, TemplateLintInfo]
    _tag_rules: Mapping[str, TagRules] = field(repr=False)

    @classmethod
    def _create(
        cls,
        component_names: frozenset[str],
        tag_rules: Mapping[str, TagRules],
        lint: TemplateLintInfo,
        component_lint: Mapping[str, TemplateLintInfo],
    ) -> TemplateAnalysis:
        analysis = object.__new__(cls)
        object.__setattr__(analysis, "component_names", component_names)
        object.__setattr__(analysis, "lint", lint)
        object.__setattr__(analysis, "component_lint", MappingProxyType(dict(component_lint)))
        object.__setattr__(analysis, "_tag_rules", MappingProxyType(dict(tag_rules)))
        return analysis

    def parse_template(self, source: str) -> Template:
        """
        Parse authored Citry source with this registry's component contracts.

        The parser checks registered component inputs and slots. Extension
        transforms are not run because they do not currently provide a mapping
        back to the authored source. Names absent from ``component_names`` need
        a separate unknown-component diagnostic after a successful parse.

        Args:
            source: Authored Citry template source.

        Returns:
            The parsed template AST.

        Raises:
            SyntaxError: If syntax or a registered component contract is
                invalid.
            ValueError: If parser configuration is invalid.

        """
        return _parse_template(source, user_rules=dict(self._tag_rules))

    def to_dict(self) -> dict[str, object]:
        """Return a fresh JSON-ready copy of this analysis snapshot."""
        return {
            "schema_version": TEMPLATE_ANALYSIS_SCHEMA_VERSION,
            "component_names": sorted(self.component_names),
            "lint": self.lint.to_dict(),
            "component_lint": {
                definition_id: info.to_dict() for definition_id, info in sorted(self.component_lint.items())
            },
            "tag_rules": {
                name: {
                    "allowed_attrs": rule.allowed_attrs,
                    "required_attrs": rule.required_attrs,
                    "allowed_slots": rule.allowed_slots,
                    "required_slots": rule.required_slots,
                    "slot_data_fields": rule.slot_data_fields,
                }
                for name, rule in sorted(self._tag_rules.items())
            },
        }

    @classmethod
    def from_dict(cls, value: object) -> TemplateAnalysis:
        """Rebuild a snapshot from :meth:`to_dict` portable data."""
        if type(value) is not dict:
            msg = "template analysis data must be a dict"
            raise TypeError(msg)
        payload = value
        if payload.get("schema_version") != TEMPLATE_ANALYSIS_SCHEMA_VERSION:
            msg = f"unsupported template analysis schema version: {payload.get('schema_version')!r}"
            raise ValueError(msg)
        names = payload.get("component_names")
        lint = payload.get("lint")
        component_lint = payload.get("component_lint")
        rules = payload.get("tag_rules")
        if type(names) is not list or any(type(name) is not str or not name for name in names):
            msg = "component_names must be a list of non-empty strings"
            raise ValueError(msg)
        if type(rules) is not dict or any(type(name) is not str or not name for name in rules):
            msg = "tag_rules must be a string-keyed dict"
            raise ValueError(msg)
        if type(component_lint) is not dict or any(
            type(definition_id) is not str or not definition_id for definition_id in component_lint
        ):
            msg = "component_lint must be a non-empty-string-keyed dict"
            raise ValueError(msg)

        restored: dict[str, TagRules] = {}
        for name, raw_rule in rules.items():
            if type(raw_rule) is not dict:
                msg = f"tag rule {name!r} must be a dict"
                raise ValueError(msg)
            restored[name] = TagRules(
                allowed_attrs=_optional_string_groups(raw_rule.get("allowed_attrs"), "allowed_attrs"),
                required_attrs=_string_groups(raw_rule.get("required_attrs"), "required_attrs"),
                allowed_slots=_optional_string_list(raw_rule.get("allowed_slots"), "allowed_slots"),
                required_slots=_string_list(raw_rule.get("required_slots"), "required_slots"),
                slot_data_fields=_string_list_mapping(raw_rule.get("slot_data_fields"), "slot_data_fields"),
            )
        return cls._create(
            frozenset(names),
            restored,
            TemplateLintInfo.from_dict(lint),
            {
                definition_id: TemplateLintInfo.from_dict(raw_info)
                for definition_id, raw_info in component_lint.items()
            },
        )


def _string_list(value: object, field_name: str) -> list[str]:
    if type(value) is not list or any(type(item) is not str for item in value):
        msg = f"{field_name} must be a list of strings"
        raise ValueError(msg)
    return list(value)


def _optional_string_list(value: object, field_name: str) -> list[str] | None:
    if value is None:
        return None
    return _string_list(value, field_name)


def _string_groups(value: object, field_name: str) -> list[list[str]]:
    if type(value) is not list:
        msg = f"{field_name} must be a list of string lists"
        raise ValueError(msg)
    return [_string_list(group, field_name) for group in value]


def _optional_string_groups(value: object, field_name: str) -> list[list[str]] | None:
    if value is None:
        return None
    return _string_groups(value, field_name)


def _string_list_mapping(value: object, field_name: str) -> dict[str, list[str]]:
    if type(value) is not dict or any(type(name) is not str for name in value):
        msg = f"{field_name} must be a string-keyed dict"
        raise ValueError(msg)
    return {name: _string_list(items, field_name) for name, items in value.items()}


@dataclass(frozen=True, slots=True)
class _MappedChar:
    value: str
    host_start: int
    host_end: int


@dataclass(frozen=True, slots=True)
class _LiteralPart:
    literal_start: int
    body_start: int
    body_end: int
    literal_end: int
    prefix: str
    delimiter: str
    closed: bool


@dataclass(frozen=True, slots=True)
class _HostReplacement:
    start: int
    end: int
    text: str


class PythonTemplateSourceMap:
    """
    Map Citry parser byte ranges back into an authored Python document.

    The map decodes plain, raw, and Unicode string literals, including
    implicit literal concatenation. Parser indices address the decoded
    template as UTF-8 bytes. Returned positions address the Python document
    with the zero-based UTF-16 coordinates required by LSP.

    Build a map with [`from_ast`][citry.PythonTemplateSourceMap.from_ast] for
    valid Python or
    [`from_coordinates`][citry.PythonTemplateSourceMap.from_coordinates] for a
    literal region found by a conservative lexical scanner.

    Attributes:
        template_source: Decoded, common-indent-normalized Citry template text
            passed to the parser.

    """

    _byte_boundaries: tuple[int, ...]
    _empty_anchor: int
    _host_source: str
    _literal_parts: tuple[_LiteralPart, ...]
    _line_starts: tuple[int, ...]
    _normalization_changed: bool
    _units: tuple[_MappedChar, ...]
    template_source: str

    __slots__ = (
        "_byte_boundaries",
        "_empty_anchor",
        "_host_source",
        "_line_starts",
        "_literal_parts",
        "_normalization_changed",
        "_units",
        "template_source",
    )

    @classmethod
    def _create(
        cls,
        host_source: str,
        template_source: str,
        units: tuple[_MappedChar, ...],
        empty_anchor: int,
        literal_parts: tuple[_LiteralPart, ...],
    ) -> PythonTemplateSourceMap:
        normalized_source, normalized_units = _normalize_mapped_inline_asset(template_source, units)
        source_map = object.__new__(cls)
        object.__setattr__(source_map, "_host_source", host_source)
        object.__setattr__(source_map, "template_source", normalized_source)
        object.__setattr__(source_map, "_units", normalized_units)
        object.__setattr__(source_map, "_normalization_changed", normalized_source != template_source)
        object.__setattr__(source_map, "_empty_anchor", empty_anchor)
        object.__setattr__(source_map, "_literal_parts", literal_parts)
        object.__setattr__(source_map, "_line_starts", _line_starts(host_source))
        byte_boundaries = [0]
        for unit in normalized_units:
            try:
                byte_length = len(unit.value.encode("utf-8"))
            except UnicodeEncodeError as exc:
                msg = "Python string contains a surrogate that cannot be parsed as UTF-8"
                raise ValueError(msg) from exc
            byte_boundaries.append(byte_boundaries[-1] + byte_length)
        object.__setattr__(source_map, "_byte_boundaries", tuple(byte_boundaries))
        return source_map

    def __setattr__(self, name: str, value: object) -> None:
        msg = f"{type(self).__name__} is immutable"
        raise AttributeError(msg)

    @classmethod
    def from_ast(cls, host_source: str, node: ast.Constant) -> PythonTemplateSourceMap:
        """
        Build a map for a string-valued Python AST constant.

        Python AST columns are interpreted as zero-based UTF-8 byte offsets,
        matching CPython's contract. Adjacent literals represented by the same
        constant are decoded as one template.

        Args:
            host_source: Complete Python document text.
            node: A string-valued ``ast.Constant`` from ``host_source``.

        Returns:
            A source map whose ``template_source`` is the normalized inline
            form of ``node.value``.

        Raises:
            TypeError: If ``node`` is not a string-valued ``ast.Constant``.
            ValueError: If source positions are missing or the authored text
                does not decode to ``node.value``.

        """
        if not isinstance(node, ast.Constant) or type(node.value) is not str:
            msg = "node must be a string-valued ast.Constant"
            raise TypeError(msg)
        if node.end_lineno is None or node.end_col_offset is None:
            msg = "AST string node must include end source coordinates"
            raise ValueError(msg)
        source_map = cls.from_coordinates(
            host_source,
            lineno=node.lineno,
            col_offset=node.col_offset,
            end_lineno=node.end_lineno,
            end_col_offset=node.end_col_offset,
        )
        if source_map.template_source != normalize_inline_asset(node.value):
            msg = "authored string decoding does not match the AST value"
            raise ValueError(msg)
        return source_map

    @classmethod
    def from_coordinates(
        cls,
        host_source: str,
        *,
        lineno: int,
        col_offset: int,
        end_lineno: int | None = None,
        end_col_offset: int | None = None,
        accept_incomplete: bool = False,
    ) -> PythonTemplateSourceMap:
        """
        Build a map from Python parser coordinates around a literal expression.

        Supply both end coordinates for complete source. A conservative
        lexical scanner may omit them and set ``accept_incomplete=True`` for
        an unfinished final triple-quoted literal, in which case the document
        end is the temporary content boundary.

        Args:
            host_source: Complete Python document text.
            lineno: 1-based line containing the first literal prefix or quote.
            col_offset: Zero-based UTF-8 byte column of that prefix or quote.
            end_lineno: 1-based line immediately after the expression.
            end_col_offset: Zero-based UTF-8 byte column immediately after the
                expression.
            accept_incomplete: Accept an unfinished final triple-quoted
                literal and map its content through the end of the document.

        Returns:
            A map for the decoded string expression.

        Raises:
            ValueError: If coordinates, literal syntax, or escape syntax are
                invalid or unsupported.

        """
        if type(accept_incomplete) is not bool:
            msg = "accept_incomplete must be a bool"
            raise TypeError(msg)
        if (end_lineno is None) is not (end_col_offset is None):
            msg = "end_lineno and end_col_offset must be supplied together"
            raise ValueError(msg)
        start = _python_coordinate_to_offset(host_source, lineno, col_offset)
        if end_lineno is None:
            if not accept_incomplete:
                msg = "end coordinates are required for complete Python source"
                raise ValueError(msg)
            end = len(host_source)
        else:
            if end_col_offset is None:
                msg = "end_lineno and end_col_offset must be supplied together"
                raise ValueError(msg)
            end = _python_coordinate_to_offset(host_source, end_lineno, end_col_offset)
        if end < start:
            msg = "end coordinates precede the start coordinates"
            raise ValueError(msg)

        template_source, units, empty_anchor, literal_parts = _decode_literal_expression(
            host_source,
            start,
            end,
            accept_incomplete=accept_incomplete,
        )
        return cls._create(host_source, template_source, units, empty_anchor, literal_parts)

    def _contains_host_offset(self, host_offset: int) -> bool:
        return any(part.body_start <= host_offset <= part.body_end for part in self._literal_parts)

    def _rewrite_replacements(self, formatted: str) -> tuple[_HostReplacement, ...]:
        part = self._require_rewrite_literal()

        if self._normalization_changed:
            return self._rewrite_complete_literal(formatted)

        replacements: list[_HostReplacement] = []
        matcher = SequenceMatcher(a=self.template_source, b=formatted, autojunk=False)
        for operation, old_start, old_end, new_start, new_end in matcher.get_opcodes():
            if operation == "equal":
                continue
            host_start = self._rewrite_boundary(old_start, part)
            host_end = self._rewrite_boundary(old_end, part)
            authored = self._host_source[host_start:host_end]
            decoded = self.template_source[old_start:old_end]
            if authored != decoded:
                msg = "an escape or physical newline makes a required rewrite non-bijective"
                raise ValueError(msg)
            replacements.append(
                _HostReplacement(
                    host_start,
                    host_end,
                    self._encode_replacement_text(formatted[new_start:new_end]),
                ),
            )
        return tuple(replacements)

    def _rewrite_complete_literal(self, formatted: str) -> tuple[_HostReplacement, ...]:
        """Encode a complete provider-owned asset into its existing literal."""
        part = self._require_rewrite_literal()
        if formatted == self.template_source:
            return ()
        encoded = _encode_literal_body(
            formatted,
            prefix=part.prefix,
            delimiter=part.delimiter,
            newline=_detected_newline(self._host_source),
        )
        if self._host_source[part.body_start : part.body_end] == encoded:
            return ()
        return (_HostReplacement(part.body_start, part.body_end, encoded),)

    def _encode_replacement_text(self, text: str) -> str:
        newline = _detected_newline(self._host_source)
        return text if newline == "\n" else text.replace("\n", newline)

    def _canonicalize_multiline_framing(self, formatted: str) -> str:
        """Indent multiline triple-string content relative to its assignment."""
        part = self._require_rewrite_literal()
        if len(part.delimiter) != 3 or "\n" not in formatted:
            return formatted
        if any(
            unit.value.isspace()
            and self._host_source[unit.host_start : unit.host_end] != unit.value
            and self._host_source[unit.host_start : unit.host_end] not in {"\n", "\r", "\r\n"}
            for unit in self._units
        ):
            return formatted
        if re.search(r"\{#\s*fmt:\s+off\s*#\}", self.template_source):
            return formatted

        lines = formatted.split("\n")
        while lines and not lines[0].strip(" \t\f"):
            lines.pop(0)
        while lines and not lines[-1].strip(" \t\f"):
            lines.pop()
        if not lines:
            return formatted

        content_indent = _common_line_indent(lines)
        relative_lines = [line.removeprefix(content_indent) for line in lines]
        assignment_indent = _line_indent_at(self._host_source, part.literal_start)
        template_indent = f"{assignment_indent}  "
        body = "\n".join(f"{template_indent}{line}" for line in relative_lines)
        return f"\n{body}\n{assignment_indent}"

    def _require_rewrite_literal(self) -> _LiteralPart:
        if len(self._literal_parts) != 1:
            msg = "implicit string literal concatenation is not eligible for formatting"
            raise ValueError(msg)
        part = self._literal_parts[0]
        if not part.closed:
            msg = "an incomplete Python string literal is not eligible for formatting"
            raise ValueError(msg)
        return part

    def _rewrite_boundary(self, decoded_index: int, part: _LiteralPart) -> int:
        if decoded_index < 0 or decoded_index > len(self._units):
            msg = "decoded rewrite boundary is outside the template"
            raise ValueError(msg)
        if not self._units:
            return part.body_start
        if decoded_index == 0:
            boundary = self._units[0].host_start
            expected = part.body_start
        elif decoded_index == len(self._units):
            boundary = self._units[-1].host_end
            expected = part.body_end
        else:
            boundary = self._units[decoded_index - 1].host_end
            expected = self._units[decoded_index].host_start
        if boundary != expected:
            msg = "a Python escape or literal gap makes an insertion boundary ambiguous"
            raise ValueError(msg)
        return boundary

    def map_range(self, start_index: int, end_index: int) -> LspRange:
        """
        Convert one half-open parser byte range to Python-document coordinates.

        Args:
            start_index: Inclusive UTF-8 byte offset in ``template_source``.
            end_index: Exclusive UTF-8 byte offset in ``template_source``.

        Returns:
            The corresponding zero-based LSP range in the Python document.

        Raises:
            ValueError: If the range is reversed, outside the template, or
                splits a UTF-8 code point.

        """
        start_boundary = self._boundary_index(start_index)
        end_boundary = self._boundary_index(end_index)
        if end_boundary < start_boundary:
            msg = "end_index precedes start_index"
            raise ValueError(msg)

        if not self._units:
            host_start = self._empty_anchor
            host_end = self._empty_anchor
        elif start_boundary == end_boundary:
            host_start = self._right_host_offset(start_boundary)
            host_end = host_start
        else:
            host_start = self._right_host_offset(start_boundary)
            host_end = self._left_host_offset(end_boundary)

        return LspRange(
            start=_lsp_position(self._host_source, self._line_starts, host_start),
            end=_lsp_position(self._host_source, self._line_starts, host_end),
        )

    def range_is_unambiguous(self, start_index: int, end_index: int) -> bool:
        """
        Return whether a parser range stays inside one authored literal body.

        Normalized indentation and Python escapes remain mappable inside one
        literal. Crossing an implicit-concatenation boundary is ambiguous for
        editor edits and semantic result ranges.

        Args:
            start_index: Inclusive UTF-8 byte offset in ``template_source``.
            end_index: Exclusive UTF-8 byte offset in ``template_source``.

        Returns:
            ``True`` when both boundaries belong to one literal body.

        Raises:
            ValueError: If the range is reversed, outside the template, or
                splits a UTF-8 code point.

        """
        host_start, host_end = self._host_range(start_index, end_index)
        return any(part.body_start <= host_start <= host_end <= part.body_end for part in self._literal_parts)

    def _host_range(self, start_index: int, end_index: int) -> tuple[int, int]:
        start_boundary = self._boundary_index(start_index)
        end_boundary = self._boundary_index(end_index)
        if end_boundary < start_boundary:
            msg = "end_index precedes start_index"
            raise ValueError(msg)
        if not self._units:
            return self._empty_anchor, self._empty_anchor
        if start_boundary == end_boundary:
            host_offset = self._right_host_offset(start_boundary)
            return host_offset, host_offset
        return self._right_host_offset(start_boundary), self._left_host_offset(end_boundary)

    def parser_index_at(self, position: LspPosition) -> int | None:
        """
        Return the parser byte boundary at an authored LSP position.

        Positions in quotes, prefixes, comments between concatenated literals,
        or other Python outside the decoded template return ``None``. A
        position inside an authored escape maps to the byte boundary after the
        decoded character.
        """
        if type(position) is not LspPosition:
            msg = "position must be an LspPosition"
            raise TypeError(msg)
        host_offset = _lsp_position_to_offset(self._host_source, self._line_starts, position)
        for index, unit in enumerate(self._units):
            if host_offset == unit.host_start:
                return self._byte_boundaries[index]
            if unit.host_start < host_offset <= unit.host_end:
                return self._byte_boundaries[index + 1]
            if host_offset < unit.host_start:
                return None
        return None

    def _boundary_index(self, byte_offset: int) -> int:
        if type(byte_offset) is not int:
            msg = "parser byte offsets must be integers"
            raise TypeError(msg)
        boundary = bisect_left(self._byte_boundaries, byte_offset)
        if boundary == len(self._byte_boundaries) or self._byte_boundaries[boundary] != byte_offset:
            msg = f"{byte_offset} is outside the template or splits a UTF-8 code point"
            raise ValueError(msg)
        return boundary

    def _left_host_offset(self, boundary: int) -> int:
        if boundary == 0:
            return self._units[0].host_start
        return self._units[boundary - 1].host_end

    def _right_host_offset(self, boundary: int) -> int:
        if boundary == len(self._units):
            return self._units[-1].host_end
        return self._units[boundary].host_start


_SIMPLE_ESCAPES = {
    "\\": "\\",
    "'": "'",
    '"': '"',
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
}
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
_STRING_PREFIX_CHARS = frozenset("rRuUbBfFtT")


def _normalize_mapped_inline_asset(
    source: str,
    units: tuple[_MappedChar, ...],
) -> tuple[str, tuple[_MappedChar, ...]]:
    """Apply inline dedenting while retaining each surviving host span."""
    normalized = normalize_inline_asset(source)
    if normalized == source:
        return source, units

    blank_normalized = re.sub(r"^[ \t]+$", "", source, flags=re.MULTILINE)
    indents = re.findall(r"(^[ \t]*)(?:[^ \t\n])", blank_normalized, flags=re.MULTILINE)
    margin = _dedent_margin(indents)
    deleted: set[int] = set()
    line_start = 0
    while line_start <= len(source):
        newline_index = source.find("\n", line_start)
        line_end = len(source) if newline_index < 0 else newline_index
        content = source[line_start:line_end]
        if content and not content.strip(" \t"):
            deleted.update(range(line_start, line_start + len(content)))
        elif margin and content.startswith(margin):
            deleted.update(range(line_start, line_start + len(margin)))
        if newline_index < 0:
            break
        line_start = newline_index + 1

    surviving = tuple(unit for index, unit in enumerate(units) if index not in deleted)
    if "".join(unit.value for unit in surviving) != normalized:
        msg = "inline asset normalization could not preserve Python source coordinates"
        raise ValueError(msg)
    return normalized, surviving


def _dedent_margin(indents: list[str]) -> str:
    margin: str | None = None
    for indent in indents:
        if margin is None:
            margin = indent
        elif indent.startswith(margin):
            continue
        elif margin.startswith(indent):
            margin = indent
        else:
            index = 0
            while index < len(margin) and index < len(indent) and margin[index] == indent[index]:
                index += 1
            margin = margin[:index]
    return margin or ""


def _decode_literal_expression(
    source: str,
    start: int,
    end: int,
    *,
    accept_incomplete: bool,
) -> tuple[str, tuple[_MappedChar, ...], int, tuple[_LiteralPart, ...]]:
    units: list[_MappedChar] = []
    literal_parts: list[_LiteralPart] = []
    literal_count = 0
    empty_anchor = start
    index = start

    while True:
        index = _skip_literal_spacing(source, index, end)
        if index >= end:
            break
        prefix_start = index
        while index < end and source[index] in _STRING_PREFIX_CHARS:
            index += 1
        prefix = source[prefix_start:index]
        if index >= end or source[index] not in {'"', "'"}:
            msg = f"unexpected Python source at character offset {prefix_start}"
            raise ValueError(msg)
        normalized_prefix = prefix.lower()
        if normalized_prefix not in {"", "r", "u"}:
            msg = f"Python string prefix {prefix!r} does not produce a static text value"
            raise ValueError(msg)

        quote_char = source[index]
        delimiter = quote_char * (3 if source.startswith(quote_char * 3, index) else 1)
        content_start = index + len(delimiter)
        if literal_count == 0:
            empty_anchor = content_start
        part_units, next_index, closed = _decode_literal_part(
            source,
            content_start,
            end,
            delimiter=delimiter,
            raw=normalized_prefix == "r",
        )
        units.extend(part_units)
        literal_count += 1
        body_end = next_index - len(delimiter) if closed else next_index
        literal_parts.append(
            _LiteralPart(
                literal_start=prefix_start,
                body_start=content_start,
                body_end=body_end,
                literal_end=next_index,
                prefix=prefix,
                delimiter=delimiter,
                closed=closed,
            ),
        )
        index = next_index
        if not closed:
            if not accept_incomplete or len(delimiter) != 3:
                msg = "Python string literal is not terminated"
                raise ValueError(msg)
            break

    if literal_count == 0:
        msg = "source range does not contain a Python string literal"
        raise ValueError(msg)
    template_source = "".join(unit.value for unit in units)
    return template_source, tuple(units), empty_anchor, tuple(literal_parts)


def _decode_literal_part(
    source: str,
    start: int,
    end: int,
    *,
    delimiter: str,
    raw: bool,
) -> tuple[list[_MappedChar], int, bool]:
    units: list[_MappedChar] = []
    index = start
    while index < end:
        if source.startswith(delimiter, index):
            return units, index + len(delimiter), True
        char = source[index]
        if char == "\\":
            if raw:
                units.append(_MappedChar("\\", index, index + 1))
                index += 1
                if index >= end:
                    break
                value, next_index = _physical_char(source, index, end)
                units.append(_MappedChar(value, index, next_index))
                index = next_index
                continue
            decoded, index = _decode_escape(source, index, end)
            units.extend(decoded)
            continue
        if char in {"\r", "\n"}:
            if len(delimiter) == 1:
                msg = "single-quoted Python string crosses a physical line"
                raise ValueError(msg)
            value, next_index = _physical_char(source, index, end)
            units.append(_MappedChar(value, index, next_index))
            index = next_index
            continue
        units.append(_MappedChar(char, index, index + 1))
        index += 1
    return units, end, False


def _decode_escape(source: str, start: int, end: int) -> tuple[list[_MappedChar], int]:
    escaped_index = start + 1
    if escaped_index >= end:
        msg = "Python string ends inside an escape sequence"
        raise ValueError(msg)
    escaped = source[escaped_index]
    if escaped in {"\r", "\n"}:
        _, next_index = _physical_char(source, escaped_index, end)
        return [], next_index
    if escaped in _SIMPLE_ESCAPES:
        return [_MappedChar(_SIMPLE_ESCAPES[escaped], start, escaped_index + 1)], escaped_index + 1
    if escaped in "01234567":
        next_index = escaped_index
        while next_index < end and next_index < escaped_index + 3 and source[next_index] in "01234567":
            next_index += 1
        value = chr(int(source[escaped_index:next_index], 8))
        return [_MappedChar(value, start, next_index)], next_index
    if escaped == "x":
        return _decode_fixed_hex_escape(source, start, escaped_index + 1, end, 2)
    if escaped == "u":
        return _decode_fixed_hex_escape(source, start, escaped_index + 1, end, 4)
    if escaped == "U":
        return _decode_fixed_hex_escape(source, start, escaped_index + 1, end, 8)
    if escaped == "N":
        name_start = escaped_index + 1
        if name_start >= end or source[name_start] != "{":
            msg = "named Unicode escape must start with '{'"
            raise ValueError(msg)
        name_end = source.find("}", name_start + 1, end)
        if name_end < 0:
            msg = "named Unicode escape is not terminated"
            raise ValueError(msg)
        name = source[name_start + 1 : name_end]
        try:
            value = unicodedata.lookup(name)
        except KeyError as exc:
            msg = f"unknown Unicode character name {name!r}"
            raise ValueError(msg) from exc
        return [_MappedChar(value, start, name_end + 1)], name_end + 1

    return [
        _MappedChar("\\", start, start + 1),
        _MappedChar(escaped, escaped_index, escaped_index + 1),
    ], escaped_index + 1


def _decode_fixed_hex_escape(
    source: str,
    escape_start: int,
    digits_start: int,
    end: int,
    width: int,
) -> tuple[list[_MappedChar], int]:
    digits_end = digits_start + width
    if digits_end > end or any(char not in _HEX_DIGITS for char in source[digits_start:digits_end]):
        msg = f"Unicode escape requires exactly {width} hexadecimal digits"
        raise ValueError(msg)
    try:
        value = chr(int(source[digits_start:digits_end], 16))
    except ValueError as exc:
        msg = "Unicode escape is outside the valid code point range"
        raise ValueError(msg) from exc
    return [_MappedChar(value, escape_start, digits_end)], digits_end


def _physical_char(source: str, index: int, end: int) -> tuple[str, int]:
    if source[index] == "\r":
        next_index = index + 2 if index + 1 < end and source[index + 1] == "\n" else index + 1
        return "\n", next_index
    return source[index], index + 1


def _skip_literal_spacing(source: str, start: int, end: int) -> int:
    index = start
    while index < end:
        if source[index].isspace():
            index += 1
            continue
        if source[index] == "#":
            newline = source.find("\n", index, end)
            return end if newline < 0 else _skip_literal_spacing(source, newline + 1, end)
        if source[index] == "\\" and index + 1 < end and source[index + 1] in {"\r", "\n"}:
            _, index = _physical_char(source, index + 1, end)
            continue
        break
    return index


def _python_coordinate_to_offset(source: str, lineno: int, col_offset: int) -> int:
    if type(lineno) is not int or type(col_offset) is not int:
        msg = "Python source coordinates must be integers"
        raise TypeError(msg)
    if lineno < 1 or col_offset < 0:
        msg = "Python lines are 1-based and byte columns are non-negative"
        raise ValueError(msg)
    starts = _line_starts(source)
    if lineno > len(starts):
        msg = f"Python line {lineno} is outside the source"
        raise ValueError(msg)
    line_start = starts[lineno - 1]
    line_end = starts[lineno] if lineno < len(starts) else len(source)
    line = source[line_start:line_end]
    encoded = line.encode("utf-8")
    if col_offset > len(encoded):
        msg = f"Python byte column {col_offset} is outside line {lineno}"
        raise ValueError(msg)
    try:
        prefix = encoded[:col_offset].decode("utf-8")
    except UnicodeDecodeError as exc:
        msg = f"Python byte column {col_offset} splits a UTF-8 code point on line {lineno}"
        raise ValueError(msg) from exc
    return line_start + len(prefix)


def _line_starts(source: str) -> tuple[int, ...]:
    starts = [0]
    index = 0
    while index < len(source):
        if source[index] == "\r":
            index += 2 if index + 1 < len(source) and source[index + 1] == "\n" else 1
            starts.append(index)
            continue
        if source[index] == "\n":
            index += 1
            starts.append(index)
            continue
        index += 1
    return tuple(starts)


def _lsp_position(source: str, line_starts: tuple[int, ...], host_offset: int) -> LspPosition:
    line = bisect_right(line_starts, host_offset) - 1
    line_prefix = source[line_starts[line] : host_offset]
    character = sum(2 if ord(char) > 0xFFFF else 1 for char in line_prefix)
    return LspPosition(line=line, character=character)


def _lsp_position_to_offset(
    source: str,
    line_starts: tuple[int, ...],
    position: LspPosition,
) -> int:
    if position.line < 0 or position.character < 0 or position.line >= len(line_starts):
        msg = "LSP position is outside the source"
        raise ValueError(msg)
    start = line_starts[position.line]
    end = line_starts[position.line + 1] if position.line + 1 < len(line_starts) else len(source)
    units = 0
    for offset in range(start, end):
        if units == position.character:
            return offset
        units += 2 if ord(source[offset]) > 0xFFFF else 1
        if units > position.character:
            msg = "LSP position splits a UTF-16 surrogate pair"
            raise ValueError(msg)
    if units == position.character:
        return end
    msg = "LSP position is outside the source line"
    raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PythonTemplateRegion:
    """One definite direct literal template on a Citry component class."""

    component_name: str
    source_map: PythonTemplateSourceMap


@dataclass(frozen=True, slots=True)
class PythonTemplateNotice:
    """One definite component template skipped for an explicit reason."""

    component_name: str
    message: str


@dataclass(frozen=True, slots=True)
class PythonTemplateDiscovery:
    """Conservative inline template regions and non-parser notices."""

    regions: tuple[PythonTemplateRegion, ...]
    notices: tuple[PythonTemplateNotice, ...]
    valid_python: bool


def discover_python_templates(
    source: str,
    *,
    recover_incomplete: bool = False,
) -> PythonTemplateDiscovery:
    """
    Discover direct literal templates on provable Citry component classes.

    Normal batch tooling leaves ``recover_incomplete`` false and receives the
    original Python ``SyntaxError``. An interactive editor may opt into the
    narrow recovery of one unfinished direct triple-quoted template literal.
    """
    try:
        module = ast.parse(source)
    except SyntaxError:
        if not recover_incomplete:
            raise
        return PythonTemplateDiscovery(
            tuple(_incomplete_template_regions(source)),
            (),
            valid_python=False,
        )
    regions, notices = _ast_template_regions(source, module)
    return PythonTemplateDiscovery(tuple(regions), tuple(notices), valid_python=True)


@dataclass(frozen=True, slots=True)
class PythonTemplateFormatResult:
    """One validated, atomic Python template-formatting result."""

    source: str
    changed_component_names: tuple[str, ...]
    notices: tuple[PythonTemplateNotice, ...]


class PythonTemplateFormatError(ValueError):
    """
    A formatting refusal that never exposes a partial Python candidate.

    Attributes:
        code: Stable formatter failure code.
        notices: Component-specific reasons relevant to the refusal.
        range: Optional absolute half-open Python string-offset range.
        diagnostic: Optional nested parser diagnostic. Template parser
            diagnostic offsets remain relative to the decoded template.

    """

    code: str
    notices: tuple[PythonTemplateNotice, ...]
    range: tuple[int, int] | None
    diagnostic: object | None

    def __init__(
        self,
        message: str,
        *,
        code: str,
        notices: tuple[PythonTemplateNotice, ...] = (),
        host_range: tuple[int, int] | None = None,
        diagnostic: object | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.notices = notices
        self.range = host_range
        self.diagnostic = diagnostic


class PythonComponentAssetKind(str, Enum):
    """A direct Citry component asset selected for formatting."""

    TEMPLATE = "template"
    JS = "js"
    CSS = "css"


@dataclass(frozen=True, slots=True)
class PythonComponentAssetRegion:
    """
    One definite direct literal asset on a Citry component class.

    Attributes:
        component_name: Name of the declaring component class.
        kind: Component attribute represented by this region.
        source_map: Mapping between the decoded asset and its Python literal.

    """

    component_name: str
    kind: PythonComponentAssetKind
    source_map: PythonTemplateSourceMap


@dataclass(frozen=True, slots=True)
class PythonComponentAssetFile:
    """One statically proven direct component asset-file declaration."""

    component_name: str
    kind: PythonComponentAssetKind
    path: str


@dataclass(frozen=True, slots=True)
class PythonComponentAssetNotice:
    """A component-specific reason why one asset was skipped or unchanged."""

    component_name: str
    kind: PythonComponentAssetKind
    code: str
    message: str
    request_id: str | None = None


@dataclass(frozen=True, slots=True)
class PythonComponentAssetDiscovery:
    """Conservative direct literal and static file component assets."""

    regions: tuple[PythonComponentAssetRegion, ...]
    files: tuple[PythonComponentAssetFile, ...]
    notices: tuple[PythonComponentAssetNotice, ...]
    valid_python: bool


@dataclass(frozen=True, slots=True)
class PythonComponentAssetRequest:
    """
    One standalone JavaScript or CSS document offered to a provider.

    Attributes:
        plan_id: Identity of the source-bound Python formatting plan.
        id: Identity of this request within the plan.
        component_name: Name of the declaring component class.
        asset_kind: Component asset containing this provider region.
        language: Standalone language expected by the provider.
        region_kind: Template body kind, or ``None`` for a direct ``js`` or
            ``css`` literal.
        source: Decoded provider-owned source.
        virtual_source: Standalone source to send to the provider.

    """

    plan_id: str
    id: str
    component_name: str
    asset_kind: PythonComponentAssetKind
    language: EmbeddedLanguage
    region_kind: EmbeddedRegionKind | None
    source: str
    virtual_source: str


@dataclass(frozen=True, slots=True)
class _PreparedPythonComponentAsset:
    region_index: int
    region: PythonComponentAssetRegion
    formatted_source: str
    core_plan: _CoreEmbeddedFormatPlan | None
    request_ids: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class PythonComponentAssetPlan:
    """
    An immutable Python-source plan awaiting JavaScript and CSS providers.

    A plan is bound to the complete source passed to
    [`prepare_python_component_assets`][citry.prepare_python_component_assets].
    Provider work may happen asynchronously before the caller passes every
    reply to [`finish_python_component_assets`][citry.finish_python_component_assets].

    Attributes:
        id: Stable source and selection identity echoed by provider results.
        source: Complete original Python source.
        requests: Standalone JavaScript and CSS provider requests.
        notices: Non-fatal embedded regions that could not be delegated.

    """

    id: str
    source: str
    requests: tuple[PythonComponentAssetRequest, ...]
    notices: tuple[PythonComponentAssetNotice, ...]
    _regions: tuple[PythonComponentAssetRegion, ...] = field(repr=False)
    _files: tuple[PythonComponentAssetFile, ...] = field(repr=False)
    _prepared: tuple[_PreparedPythonComponentAsset, ...] = field(repr=False)


@dataclass(frozen=True, slots=True)
class PythonComponentAssetFormatResult:
    """
    One validated, atomic Python component-asset formatting result.

    Attributes:
        source: Complete formatted Python source.
        changed_component_assets: Changed ``(component_name, kind)`` pairs.
        notices: Assets left unchanged with an explicit reason.
        providers: Sorted provider identities reported by accepted results.

    """

    source: str
    changed_component_assets: tuple[tuple[str, PythonComponentAssetKind], ...]
    notices: tuple[PythonComponentAssetNotice, ...]
    providers: tuple[str, ...]


def discover_python_component_assets(source: str) -> PythonComponentAssetDiscovery:
    """
    Discover direct literal and static file assets on proven components.

    Discovery recognizes direct ``template``, ``js``, and ``css`` literals,
    plus constant ``template_file``, ``js_file``, and ``css_file`` paths. It
    never imports the module or evaluates a computed declaration.

    Args:
        source: Complete Python module source.

    Returns:
        Definite inline regions, file declarations, and explicit notices.

    Raises:
        SyntaxError: If ``source`` is not a complete valid Python module.
        TypeError: If ``source`` is not a string.

    """
    if type(source) is not str:
        msg = "source must be a str"
        raise TypeError(msg)
    module = ast.parse(source)
    regions, files, notices = _ast_component_asset_discovery(source, module)
    return PythonComponentAssetDiscovery(
        tuple(regions),
        tuple(files),
        tuple(notices),
        valid_python=True,
    )


def prepare_python_component_assets(
    source: str,
    *,
    kinds: Collection[PythonComponentAssetKind | str] = tuple(PythonComponentAssetKind),
    host_offset: int | None = None,
) -> PythonComponentAssetPlan:
    """
    Prepare one atomic Python component-asset formatting operation.

    Templates first receive Citry structure and Python-expression formatting.
    Safe ``script`` and ``style`` bodies, plus direct ``js`` and ``css``
    literals, become standalone provider requests. The returned plan makes no
    source edit, so callers may resolve those requests asynchronously.

    Args:
        source: Complete Python module source.
        kinds: Explicit component asset kinds selected for this operation.
        host_offset: Optional zero-based Python string offset. When supplied,
            only the containing selected direct asset is prepared.

    Returns:
        A source-bound plan and its provider requests.

    Raises:
        PythonTemplateFormatError: If Python or selected asset syntax is
            invalid, or a selected literal cannot be rewritten safely.
        TypeError: If an argument has the wrong type.
        ValueError: If ``host_offset`` is outside ``source`` or a kind is
            unknown.

    """
    _validate_python_asset_arguments(source, host_offset)
    selected_kinds = _normalize_component_asset_kinds(kinds)
    try:
        module = ast.parse(source)
    except SyntaxError as error:
        msg = f"Python source is invalid: {error.msg}"
        raise PythonTemplateFormatError(
            msg,
            code=FORMAT_HOST_SYNTAX,
            host_range=_syntax_error_host_range(source, error),
            diagnostic=error,
        ) from None

    regions, files, discovered_notices = _ast_component_asset_discovery(
        source,
        module,
        rewrite_notices=True,
    )
    relevant_notices = tuple(notice for notice in discovered_notices if notice.kind in selected_kinds)
    if host_offset is None:
        if relevant_notices:
            raise PythonTemplateFormatError(
                _component_asset_notice_message(relevant_notices),
                code=FORMAT_INELIGIBLE,
            )
        selected = [(index, region) for index, region in enumerate(regions) if region.kind in selected_kinds]
        plan_notices: list[PythonComponentAssetNotice] = []
    else:
        selected = [
            (index, region)
            for index, region in enumerate(regions)
            if region.kind in selected_kinds and region.source_map._contains_host_offset(host_offset)
        ]
        if len(selected) != 1:
            msg = f"host offset {host_offset} does not contain a definite selected Citry component asset"
            raise PythonTemplateFormatError(
                msg,
                code=FORMAT_INELIGIBLE,
            )
        plan_notices = list(relevant_notices)

    plan_id = _python_component_asset_plan_id(source, selected_kinds, host_offset)
    requests: list[PythonComponentAssetRequest] = []
    prepared: list[_PreparedPythonComponentAsset] = []
    failures: list[PythonComponentAssetNotice] = []
    first_failure: tuple[str, tuple[int, int] | None, object | None] | None = None
    for region_index, region in selected:
        try:
            region.source_map._require_rewrite_literal()
            if region.kind is PythonComponentAssetKind.TEMPLATE:
                core_plan = _prepare_embedded_format(region.source_map.template_source)
                formatted_source = core_plan.formatted_source
                request_ids: list[tuple[str, str]] = []
                core_ids_to_public: dict[str, str] = {}
                for core_request in core_plan.requests:
                    request_id = f"python-component-asset-{region_index}-{len(request_ids)}"
                    request_ids.append((request_id, core_request.id))
                    core_ids_to_public[core_request.id] = request_id
                    requests.append(
                        PythonComponentAssetRequest(
                            plan_id=plan_id,
                            id=request_id,
                            component_name=region.component_name,
                            asset_kind=region.kind,
                            language=core_request.language,
                            region_kind=core_request.kind,
                            source=core_request.source,
                            virtual_source=core_request.virtual_source,
                        ),
                    )
                for notice in core_plan.notices:
                    plan_notices.append(
                        PythonComponentAssetNotice(
                            component_name=region.component_name,
                            kind=region.kind,
                            code=notice.code,
                            message=notice.message,
                            request_id=core_ids_to_public.get(notice.region_id or ""),
                        ),
                    )
                prepared.append(
                    _PreparedPythonComponentAsset(
                        region_index,
                        region,
                        formatted_source,
                        core_plan,
                        tuple(request_ids),
                    ),
                )
                continue

            language = (
                EmbeddedLanguage.JAVASCRIPT if region.kind is PythonComponentAssetKind.JS else EmbeddedLanguage.CSS
            )
            request_id = f"python-component-asset-{region_index}-0"
            requests.append(
                PythonComponentAssetRequest(
                    plan_id=plan_id,
                    id=request_id,
                    component_name=region.component_name,
                    asset_kind=region.kind,
                    language=language,
                    region_kind=None,
                    source=region.source_map.template_source,
                    virtual_source=region.source_map.template_source,
                ),
            )
            prepared.append(
                _PreparedPythonComponentAsset(
                    region_index,
                    region,
                    region.source_map.template_source,
                    None,
                    ((request_id, request_id),),
                ),
            )
        except _CoreTemplateFormatError as error:
            failures.append(
                PythonComponentAssetNotice(
                    region.component_name,
                    region.kind,
                    error.code,
                    str(error),
                ),
            )
            if first_failure is None:
                host_range = region.source_map._host_range(*error.range) if error.range is not None else None
                first_failure = (error.code, host_range, error.diagnostic)
        except ValueError as error:
            failures.append(
                PythonComponentAssetNotice(
                    region.component_name,
                    region.kind,
                    FORMAT_INELIGIBLE,
                    str(error),
                ),
            )
            if first_failure is None:
                first_failure = (FORMAT_INELIGIBLE, None, None)

    if failures:
        failure_code, failure_range, failure_diagnostic = first_failure or (
            FORMAT_INELIGIBLE,
            None,
            None,
        )
        raise PythonTemplateFormatError(
            _component_asset_notice_message(failures),
            code=failure_code,
            host_range=failure_range,
            diagnostic=failure_diagnostic,
        )

    return PythonComponentAssetPlan(
        id=plan_id,
        source=source,
        requests=tuple(requests),
        notices=tuple(plan_notices),
        _regions=tuple(regions),
        _files=tuple(files),
        _prepared=tuple(prepared),
    )


def finish_python_component_assets(
    plan: PythonComponentAssetPlan,
    results: Sequence[EmbeddedFormatResult],
    *,
    require_providers: bool = False,
) -> PythonComponentAssetFormatResult:
    """
    Validate provider replies and atomically finish one Python source plan.

    Every selected literal is rewritten only after every provider reply,
    Python parse, asset rediscovery, and decoded-value check succeeds. A
    failure raises without exposing a partial source candidate.

    Args:
        plan: Exact plan returned by
            [`prepare_python_component_assets`][citry.prepare_python_component_assets].
        results: One source-bound reply for every request in ``plan``.
        require_providers: Reject unavailable providers and embedded regions
            that could not be delegated.

    Returns:
        The complete formatted Python source and provider metadata.

    Raises:
        PythonTemplateFormatError: If replies are missing, stale, duplicated,
            unavailable when required, invalid, or unsafe to rewrite.
        TypeError: If ``plan``, ``results``, or ``require_providers`` has the
            wrong type.

    """
    if type(plan) is not PythonComponentAssetPlan:
        msg = "plan must be a PythonComponentAssetPlan"
        raise TypeError(msg)
    if not isinstance(results, Sequence) or isinstance(results, (str, bytes)):
        msg = "results must be a sequence of EmbeddedFormatResult values"
        raise TypeError(msg)
    if type(require_providers) is not bool:
        msg = "require_providers must be a bool"
        raise TypeError(msg)

    by_id = _validate_python_component_asset_results(plan, results)
    notices = list(plan.notices)
    unavailable_plan_notices = [
        notice
        for notice in notices
        if notice.code
        in {
            FORMAT_PROVIDER_UNAVAILABLE,
            FORMAT_EMBEDDED_INTERPOLATION_UNSUPPORTED,
            FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED,
        }
    ]
    if require_providers and unavailable_plan_notices:
        raise PythonTemplateFormatError(
            _component_asset_notice_message(unavailable_plan_notices),
            code=FORMAT_PROVIDER_UNAVAILABLE,
        )

    replacements: list[_HostReplacement] = []
    formatted_sources: dict[int, str] = {}
    providers: set[str] = set()
    for prepared in plan._prepared:
        if prepared.core_plan is not None:
            core_results = []
            for public_id, core_id in prepared.request_ids:
                result = by_id[public_id]
                core_results.append(
                    EmbeddedFormatResult(
                        status=result.status,
                        plan_id=prepared.core_plan.id,
                        region_id=core_id,
                        text=result.text,
                        provider=result.provider,
                        message=result.message,
                    ),
                )
            try:
                outcome = _finish_embedded_format(prepared.core_plan, core_results)
            except _CoreTemplateFormatError as error:
                raise PythonTemplateFormatError(
                    str(error),
                    code=error.code,
                    diagnostic=error.diagnostic,
                ) from None
            if require_providers and any(notice.code == FORMAT_PROVIDER_UNAVAILABLE for notice in outcome.notices):
                unavailable = [
                    PythonComponentAssetNotice(
                        prepared.region.component_name,
                        prepared.region.kind,
                        notice.code,
                        notice.message,
                    )
                    for notice in outcome.notices
                    if notice.code == FORMAT_PROVIDER_UNAVAILABLE
                ]
                raise PythonTemplateFormatError(
                    _component_asset_notice_message(unavailable),
                    code=FORMAT_PROVIDER_UNAVAILABLE,
                )
            for outcome_notice in outcome.notices:
                translated_notice = PythonComponentAssetNotice(
                    component_name=prepared.region.component_name,
                    kind=prepared.region.kind,
                    code=outcome_notice.code,
                    message=outcome_notice.message,
                    request_id=next(
                        (
                            public_id
                            for public_id, core_id in prepared.request_ids
                            if core_id == outcome_notice.region_id
                        ),
                        None,
                    ),
                )
                if translated_notice not in notices:
                    notices.append(translated_notice)
            formatted = prepared.region.source_map._canonicalize_multiline_framing(outcome.source)
            providers.update(outcome.providers)
        else:
            public_id, _direct_id = prepared.request_ids[0]
            result = by_id[public_id]
            formatted, direct_notice = _finish_direct_component_asset_result(prepared.region, result)
            if direct_notice is not None:
                if require_providers:
                    raise PythonTemplateFormatError(
                        _component_asset_notice_message((direct_notice,)),
                        code=FORMAT_PROVIDER_UNAVAILABLE,
                    )
                notices.append(direct_notice)
            if result.status is EmbeddedResultStatus.FORMATTED and result.provider is not None:
                providers.add(result.provider)

        try:
            if prepared.core_plan is None:
                region_replacements = prepared.region.source_map._rewrite_complete_literal(formatted)
            else:
                region_replacements = prepared.region.source_map._rewrite_replacements(formatted)
        except ValueError as error:
            notice = PythonComponentAssetNotice(
                prepared.region.component_name,
                prepared.region.kind,
                FORMAT_INELIGIBLE,
                str(error),
            )
            raise PythonTemplateFormatError(
                _component_asset_notice_message((notice,)),
                code=FORMAT_INELIGIBLE,
            ) from None
        if region_replacements:
            replacements.extend(region_replacements)
            formatted_sources[prepared.region_index] = formatted

    ordered = sorted(replacements, key=lambda replacement: (replacement.start, replacement.end))
    if any(current.start < previous.end for previous, current in pairwise(ordered)):
        raise PythonTemplateFormatError(
            "component asset formatter rewrites overlap",
            code=FORMAT_INVARIANT,
        )

    candidate = plan.source
    for replacement in reversed(ordered):
        candidate = candidate[: replacement.start] + replacement.text + candidate[replacement.end :]
    _validate_python_component_asset_candidate(plan, candidate, formatted_sources)

    changed = tuple((plan._regions[index].component_name, plan._regions[index].kind) for index in formatted_sources)
    return PythonComponentAssetFormatResult(
        source=candidate,
        changed_component_assets=changed,
        notices=tuple(notices),
        providers=tuple(sorted(providers)),
    )


def format_python_component_assets(
    source: str,
    *,
    kinds: Collection[PythonComponentAssetKind | str] = tuple(PythonComponentAssetKind),
    host_offset: int | None = None,
    provider: Callable[[PythonComponentAssetRequest], EmbeddedFormatResult] | None = None,
    require_providers: bool = False,
) -> PythonComponentAssetFormatResult:
    """
    Format selected direct component assets in one atomic Python-file edit.

    This synchronous convenience function prepares a plan, invokes ``provider``
    once per JavaScript or CSS request, then validates and finishes the plan.
    Call the two-pass prepare and finish functions directly when provider work
    must be asynchronous. With no provider, M2 template formatting still runs
    while JavaScript and CSS requests remain unchanged with notices.

    Args:
        source: Complete Python module source.
        kinds: Explicit ``template``, ``js``, and ``css`` kinds to select.
        host_offset: Optional zero-based Python string offset selecting only
            the containing direct asset.
        provider: Optional synchronous JavaScript/CSS formatting callback.
        require_providers: Reject the complete operation when any selected
            embedded region has no provider.

    Returns:
        The validated complete source, changed asset identities, notices, and
        accepted provider identities.

    Raises:
        PythonTemplateFormatError: If discovery, formatting, a provider, or
            final validation fails. No partial candidate is exposed.
        TypeError: If an argument or provider reply has the wrong type.
        ValueError: If ``host_offset`` or a selected kind is invalid.

    """
    if provider is not None and not callable(provider):
        msg = "provider must be callable or None"
        raise TypeError(msg)
    plan = prepare_python_component_assets(source, kinds=kinds, host_offset=host_offset)
    results: list[EmbeddedFormatResult] = []
    for request in plan.requests:
        if provider is None:
            results.append(
                EmbeddedFormatResult.unavailable(
                    plan.id,
                    request.id,
                    f"no {request.language.value} provider was supplied",
                ),
            )
            continue
        try:
            result = provider(request)
        except Exception as error:
            notice = PythonComponentAssetNotice(
                request.component_name,
                request.asset_kind,
                FORMAT_PROVIDER_INVALID,
                f"provider raised {type(error).__name__}: {error}",
                request.id,
            )
            raise PythonTemplateFormatError(
                _component_asset_notice_message((notice,)),
                code=FORMAT_PROVIDER_INVALID,
            ) from error
        results.append(result)
    return finish_python_component_assets(
        plan,
        results,
        require_providers=require_providers,
    )


def format_python_templates(
    source: str,
    *,
    host_offset: int | None = None,
) -> PythonTemplateFormatResult:
    """
    Format proven direct Citry template literals in complete Python source.

    With no offset, every definite inline template is one atomic operation. A
    host offset selects only the literal content containing that Python string
    position. The result preserves string prefixes, delimiters, and all host
    text outside the exact decoded-template rewrite hunks.

    Args:
        source: Complete Python module source.
        host_offset: Optional zero-based Python string offset inside one
            template literal body.

    Returns:
        The validated source, changed component names, and discovery notices.

    Raises:
        PythonTemplateFormatError: If Python or Citry syntax is invalid, a
            selected literal is not safely rewriteable, or validation fails.
        TypeError: If ``source`` or ``host_offset`` has the wrong type.
        ValueError: If ``host_offset`` is outside ``source``.

    """
    if type(source) is not str:
        msg = "source must be a str"
        raise TypeError(msg)
    if host_offset is not None:
        if type(host_offset) is not int:
            msg = "host_offset must be an int or None"
            raise TypeError(msg)
        if host_offset < 0 or host_offset > len(source):
            msg = "host_offset is outside the Python source"
            raise ValueError(msg)

    try:
        module = ast.parse(source)
    except SyntaxError as error:
        msg = f"Python source is invalid: {error.msg}"
        raise PythonTemplateFormatError(
            msg,
            code=FORMAT_HOST_SYNTAX,
            host_range=_syntax_error_host_range(source, error),
            diagnostic=error,
        ) from None

    regions, discovered_notices = _ast_template_regions(
        source,
        module,
        rewrite_notices=True,
    )
    notices = tuple(discovered_notices)
    if host_offset is None:
        if notices:
            raise PythonTemplateFormatError(
                _notice_message(notices),
                code=FORMAT_INELIGIBLE,
                notices=notices,
            )
        selected = list(enumerate(regions))
    else:
        selected = [
            (index, region)
            for index, region in enumerate(regions)
            if region.source_map._contains_host_offset(host_offset)
        ]
        if len(selected) != 1:
            msg = f"host offset {host_offset} does not contain a definite Citry template"
            raise PythonTemplateFormatError(
                msg,
                code=FORMAT_INELIGIBLE,
                notices=notices,
            )

    replacements: list[_HostReplacement] = []
    formatted_sources: dict[int, str] = {}
    failure_notices: list[PythonTemplateNotice] = []
    first_failure: tuple[str, tuple[int, int] | None, object | None] | None = None
    for region_index, region in selected:
        try:
            region.source_map._require_rewrite_literal()
            formatted = _format_template(region.source_map.template_source)
            formatted = region.source_map._canonicalize_multiline_framing(formatted)
            region_replacements = region.source_map._rewrite_replacements(formatted)
        except _CoreTemplateFormatError as error:
            failure_notices.append(PythonTemplateNotice(region.component_name, str(error)))
            if first_failure is None:
                host_range = region.source_map._host_range(*error.range) if error.range is not None else None
                first_failure = (
                    error.code,
                    host_range,
                    error.diagnostic,
                )
            continue
        except ValueError as error:
            failure_notices.append(PythonTemplateNotice(region.component_name, str(error)))
            if first_failure is None:
                first_failure = (FORMAT_INELIGIBLE, None, None)
            continue

        if region_replacements:
            replacements.extend(region_replacements)
            formatted_sources[region_index] = formatted

    if failure_notices:
        failure_code, failure_range, failure_diagnostic = first_failure or (
            FORMAT_INELIGIBLE,
            None,
            None,
        )
        relevant_notices = (*notices, *failure_notices)
        raise PythonTemplateFormatError(
            _notice_message(relevant_notices),
            code=failure_code,
            notices=relevant_notices,
            host_range=failure_range,
            diagnostic=failure_diagnostic,
        )

    if not replacements:
        return PythonTemplateFormatResult(source, (), notices)

    ordered = sorted(replacements, key=lambda replacement: (replacement.start, replacement.end))
    if any(current.start < previous.end for previous, current in pairwise(ordered)):
        changed_notices = tuple(
            PythonTemplateNotice(regions[index].component_name, "formatter rewrites overlap")
            for index in formatted_sources
        )
        raise PythonTemplateFormatError(
            _notice_message(changed_notices),
            code=FORMAT_INVARIANT,
            notices=changed_notices,
        )

    candidate = source
    for replacement in reversed(ordered):
        candidate = candidate[: replacement.start] + replacement.text + candidate[replacement.end :]

    try:
        candidate_module = ast.parse(candidate)
    except SyntaxError:
        changed_notices = tuple(
            PythonTemplateNotice(
                regions[index].component_name,
                "formatted template cannot be represented with the existing Python literal framing",
            )
            for index in formatted_sources
        )
        raise PythonTemplateFormatError(
            _notice_message(changed_notices),
            code=FORMAT_INELIGIBLE,
            notices=changed_notices,
        ) from None

    candidate_regions, _candidate_notices = _ast_template_regions(
        candidate,
        candidate_module,
        rewrite_notices=True,
    )
    if len(candidate_regions) != len(regions) or any(
        candidate_region.component_name != original_region.component_name
        for original_region, candidate_region in zip(regions, candidate_regions, strict=False)
    ):
        raise PythonTemplateFormatError(
            "formatted Python source did not rediscover the same component templates",
            code=FORMAT_INVARIANT,
        )
    for region_index, formatted in formatted_sources.items():
        if candidate_regions[region_index].source_map.template_source != normalize_inline_asset(formatted):
            notice = PythonTemplateNotice(
                regions[region_index].component_name,
                "rewritten Python literal does not decode to the formatter output",
            )
            raise PythonTemplateFormatError(
                notice.message,
                code=FORMAT_INVARIANT,
                notices=(notice,),
            )

    changed_component_names = tuple(regions[index].component_name for index in formatted_sources)
    return PythonTemplateFormatResult(candidate, changed_component_names, notices)


def _notice_message(notices: tuple[PythonTemplateNotice, ...] | list[PythonTemplateNotice]) -> str:
    return "; ".join(f"{notice.component_name}: {notice.message}" for notice in notices)


def _component_asset_notice_message(
    notices: Sequence[PythonComponentAssetNotice],
) -> str:
    return "; ".join(f"{notice.component_name}.{notice.kind.value}: {notice.message}" for notice in notices)


def _validate_python_asset_arguments(source: object, host_offset: object) -> None:
    if type(source) is not str:
        msg = "source must be a str"
        raise TypeError(msg)
    if host_offset is not None and type(host_offset) is not int:
        msg = "host_offset must be an int or None"
        raise TypeError(msg)
    if isinstance(host_offset, int) and (host_offset < 0 or host_offset > len(source)):
        msg = "host_offset is outside the Python source"
        raise ValueError(msg)


def _normalize_component_asset_kinds(
    kinds: Collection[PythonComponentAssetKind | str],
) -> frozenset[PythonComponentAssetKind]:
    if isinstance(kinds, (str, bytes)) or not isinstance(kinds, Collection):
        msg = "kinds must be a collection of component asset kinds"
        raise TypeError(msg)
    selected: set[PythonComponentAssetKind] = set()
    for kind in kinds:
        if isinstance(kind, PythonComponentAssetKind):
            selected.add(kind)
            continue
        if type(kind) is str:
            try:
                selected.add(PythonComponentAssetKind(kind))
            except ValueError:
                msg = f"unknown component asset kind: {kind!r}"
                raise ValueError(msg) from None
            continue
        msg = "component asset kinds must be PythonComponentAssetKind or str values"
        raise TypeError(msg)
    return frozenset(selected)


def _python_component_asset_plan_id(
    source: str,
    kinds: frozenset[PythonComponentAssetKind],
    host_offset: int | None,
) -> str:
    digest = hashlib.sha256()
    digest.update(b"citry-python-component-assets-v1\0")
    digest.update(source.encode())
    digest.update(b"\0")
    digest.update(",".join(sorted(kind.value for kind in kinds)).encode())
    digest.update(b"\0")
    digest.update(str(host_offset).encode())
    return digest.hexdigest()


def _validate_python_component_asset_results(
    plan: PythonComponentAssetPlan,
    results: Sequence[EmbeddedFormatResult],
) -> dict[str, EmbeddedFormatResult]:
    if len(results) != len(plan.requests):
        msg = f"provider result count {len(results)} does not match request count {len(plan.requests)}"
        raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
    expected_ids = {request.id for request in plan.requests}
    by_id: dict[str, EmbeddedFormatResult] = {}
    for result in results:
        if type(result) is not EmbeddedFormatResult:
            msg = "provider results must be EmbeddedFormatResult values"
            raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
        if result.plan_id != plan.id:
            msg = "provider result belongs to a different Python component-asset plan"
            raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
        if result.region_id not in expected_ids:
            msg = f"unknown Python component-asset request ID {result.region_id!r}"
            raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
        if result.region_id in by_id:
            msg = f"duplicate provider result for {result.region_id!r}"
            raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
        _validate_embedded_result_payload(result)
        by_id[result.region_id] = result
    return by_id


def _validate_embedded_result_payload(result: EmbeddedFormatResult) -> None:
    if type(result.status) is not EmbeddedResultStatus:
        msg = "provider result status must be an EmbeddedResultStatus"
        raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
    if result.status is EmbeddedResultStatus.FORMATTED:
        if type(result.text) is not str:
            msg = "a formatted provider result requires string text"
            raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
        if result.provider is not None and type(result.provider) is not str:
            msg = "a provider identity must be a string or None"
            raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
        if result.message is not None:
            msg = "a formatted provider result cannot carry an error message"
            raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
        return
    if result.status is EmbeddedResultStatus.UNCHANGED:
        if result.text is not None or result.provider is not None or result.message is not None:
            msg = "an unchanged provider result cannot carry output fields"
            raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
        return
    if (
        result.status in {EmbeddedResultStatus.UNAVAILABLE, EmbeddedResultStatus.ERROR}
        and type(result.message) is not str
    ):
        msg = f"a {result.status.value} provider result requires a string message"
        raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)
    if result.text is not None or result.provider is not None:
        msg = f"a {result.status.value} provider result cannot carry formatted output"
        raise PythonTemplateFormatError(msg, code=FORMAT_PROVIDER_INVALID)


def _finish_direct_component_asset_result(
    region: PythonComponentAssetRegion,
    result: EmbeddedFormatResult,
) -> tuple[str, PythonComponentAssetNotice | None]:
    if result.status is EmbeddedResultStatus.FORMATTED:
        return _normalize_provider_newlines(result.text or ""), None
    if result.status is EmbeddedResultStatus.UNCHANGED:
        return region.source_map.template_source, None
    notice = PythonComponentAssetNotice(
        region.component_name,
        region.kind,
        (
            FORMAT_PROVIDER_UNAVAILABLE
            if result.status is EmbeddedResultStatus.UNAVAILABLE
            else FORMAT_PROVIDER_INVALID
        ),
        result.message or "embedded provider failed",
        result.region_id,
    )
    if result.status is EmbeddedResultStatus.ERROR:
        raise PythonTemplateFormatError(
            _component_asset_notice_message((notice,)),
            code=FORMAT_PROVIDER_INVALID,
        )
    return region.source_map.template_source, notice


def _validate_python_component_asset_candidate(
    plan: PythonComponentAssetPlan,
    candidate: str,
    formatted_sources: Mapping[int, str],
) -> None:
    try:
        candidate_module = ast.parse(candidate)
    except SyntaxError:
        raise PythonTemplateFormatError(
            "formatted component assets cannot be represented with the existing Python literal framing",
            code=FORMAT_INELIGIBLE,
        ) from None
    candidate_regions, candidate_files, _notices = _ast_component_asset_discovery(
        candidate,
        candidate_module,
        rewrite_notices=True,
    )
    original_identities = [(region.component_name, region.kind) for region in plan._regions]
    candidate_identities = [(region.component_name, region.kind) for region in candidate_regions]
    if candidate_identities != original_identities or candidate_files != list(plan._files):
        raise PythonTemplateFormatError(
            "formatted Python source did not rediscover the same component assets",
            code=FORMAT_INVARIANT,
        )
    for region_index, formatted in formatted_sources.items():
        if candidate_regions[region_index].source_map.template_source != normalize_inline_asset(formatted):
            region = plan._regions[region_index]
            notice = PythonComponentAssetNotice(
                region.component_name,
                region.kind,
                FORMAT_INVARIANT,
                "rewritten Python literal does not decode to the formatter output",
            )
            raise PythonTemplateFormatError(
                _component_asset_notice_message((notice,)),
                code=FORMAT_INVARIANT,
            )


def _syntax_error_host_range(source: str, error: SyntaxError) -> tuple[int, int] | None:
    if error.lineno is None or error.offset is None:
        return None
    starts = _line_starts(source)
    start = _syntax_error_offset(source, starts, error.lineno, error.offset)
    end = _syntax_error_offset(
        source,
        starts,
        error.end_lineno or error.lineno,
        error.end_offset or error.offset,
    )
    return start, max(start, end)


def _syntax_error_offset(
    source: str,
    starts: tuple[int, ...],
    lineno: int,
    offset: int,
) -> int:
    if lineno < 1 or lineno > len(starts):
        return len(source)
    line_start = starts[lineno - 1]
    line_end = starts[lineno] if lineno < len(starts) else len(source)
    return min(line_start + max(offset - 1, 0), line_end)


def _detected_newline(source: str) -> str:
    match = re.search(r"\r\n|\r|\n", source)
    return match.group(0) if match is not None else "\n"


def _normalize_provider_newlines(source: str) -> str:
    return source.replace("\r\n", "\n").replace("\r", "\n")


def _encode_literal_body(text: str, *, prefix: str, delimiter: str, newline: str) -> str:
    normalized = _normalize_provider_newlines(text)
    if prefix.lower() == "r":
        encoded = normalized.replace("\n", newline)
        try:
            represented = ast.literal_eval(f"{prefix}{delimiter}{encoded}{delimiter}")
        except (SyntaxError, ValueError) as error:
            msg = "provider output cannot be represented by the existing raw literal"
            raise ValueError(msg) from error
        if represented != normalized:
            msg = "provider output does not round-trip through the existing raw literal"
            raise ValueError(msg)
        return encoded

    encoded = normalized.replace("\\", "\\\\")
    encoded = encoded.replace("\0", "\\x00")
    encoded = encoded.replace("\b", "\\b").replace("\f", "\\f").replace("\v", "\\v")
    for codepoint in range(1, 8):
        encoded = encoded.replace(chr(codepoint), f"\\x{codepoint:02x}")
    for codepoint in range(14, 32):
        encoded = encoded.replace(chr(codepoint), f"\\x{codepoint:02x}")
    encoded = encoded.replace(chr(127), "\\x7f")
    encoded = encoded.replace(delimiter[0], f"\\{delimiter[0]}")
    if len(delimiter) == 1:
        return encoded.replace("\n", "\\n").replace("\r", "\\r")
    return encoded.replace("\n", newline)


def _line_indent_at(source: str, offset: int) -> str:
    line_start = max(source.rfind("\n", 0, offset), source.rfind("\r", 0, offset)) + 1
    match = re.match(r"[ \t\f]*", source[line_start:offset])
    return match.group(0) if match is not None else ""


def _common_line_indent(lines: list[str]) -> str:
    indents = [line[: len(line) - len(line.lstrip(" \t\f"))] for line in lines if line.strip(" \t\f")]
    if not indents:
        return ""
    common = indents[0]
    for indent in indents[1:]:
        while common and not indent.startswith(common):
            common = common[:-1]
    return common


def _ast_template_regions(
    source: str,
    module: ast.Module,
    *,
    rewrite_notices: bool = False,
) -> tuple[list[PythonTemplateRegion], list[PythonTemplateNotice]]:
    regions: list[PythonTemplateRegion] = []
    notices: list[PythonTemplateNotice] = []

    for statement, language in _ast_component_declarations(module):
        node, notice = _literal_template_node(
            statement,
            language,
            rewrite_notices=rewrite_notices,
        )
        if notice is not None:
            notices.append(PythonTemplateNotice(statement.name, notice))
        if node is not None:
            try:
                source_map = PythonTemplateSourceMap.from_ast(source, node)
            except (TypeError, ValueError) as error:
                if rewrite_notices:
                    notices.append(
                        PythonTemplateNotice(
                            statement.name,
                            f"template literal cannot be mapped for rewriting: {error}",
                        ),
                    )
                continue
            regions.append(PythonTemplateRegion(statement.name, source_map))
    return regions, notices


_COMPONENT_ASSET_NAMES = frozenset(
    {"template", "template_file", "js", "js_file", "css", "css_file"},
)
_COMPONENT_ASSET_ATTRIBUTES = (
    (PythonComponentAssetKind.TEMPLATE, "template", "template_file"),
    (PythonComponentAssetKind.JS, "js", "js_file"),
    (PythonComponentAssetKind.CSS, "css", "css_file"),
)


def _ast_component_asset_discovery(
    source: str,
    module: ast.Module,
    *,
    rewrite_notices: bool = False,
) -> tuple[
    list[PythonComponentAssetRegion],
    list[PythonComponentAssetFile],
    list[PythonComponentAssetNotice],
]:
    regions: list[PythonComponentAssetRegion] = []
    files: list[PythonComponentAssetFile] = []
    notices: list[PythonComponentAssetNotice] = []
    for statement, language in _ast_component_declarations(module):
        direct, nested_bindings = _direct_component_asset_values(statement)
        for kind, inline_name, file_name in _COMPONENT_ASSET_ATTRIBUTES:
            inline_node, file_path, notice = _literal_component_asset_declaration(
                direct,
                nested_bindings,
                kind=kind,
                inline_name=inline_name,
                file_name=file_name,
                template_language=language,
            )
            if notice is not None and (
                rewrite_notices
                or direct[inline_name]
                or direct[file_name]
                or inline_name in nested_bindings
                or file_name in nested_bindings
            ):
                notices.append(
                    PythonComponentAssetNotice(
                        statement.name,
                        kind,
                        FORMAT_INELIGIBLE,
                        notice,
                    ),
                )
            if file_path is not None:
                files.append(PythonComponentAssetFile(statement.name, kind, file_path))
            if inline_node is None:
                continue
            try:
                source_map = PythonTemplateSourceMap.from_ast(source, inline_node)
            except (TypeError, ValueError) as error:
                if rewrite_notices:
                    notices.append(
                        PythonComponentAssetNotice(
                            statement.name,
                            kind,
                            FORMAT_INELIGIBLE,
                            f"{inline_name} literal cannot be mapped for rewriting: {error}",
                        ),
                    )
                continue
            regions.append(PythonComponentAssetRegion(statement.name, kind, source_map))
    return regions, files, notices


def _literal_component_asset_declaration(
    direct: dict[str, list[ast.expr | None]],
    nested_bindings: set[str],
    *,
    kind: PythonComponentAssetKind,
    inline_name: str,
    file_name: str,
    template_language: object,
) -> tuple[ast.Constant | None, str | None, str | None]:
    if {inline_name, file_name} & nested_bindings:
        return None, None, f"conditional or nested {kind.value} binding cannot be resolved statically"
    has_declaration = bool(direct[inline_name] or direct[file_name])
    if not has_declaration:
        return None, None, None
    if kind is PythonComponentAssetKind.TEMPLATE:
        if template_language is _UNKNOWN_TEMPLATE_LANGUAGE:
            return None, None, "template language cannot be proven to be native Citry"
        if template_language is not None:
            return (
                None,
                None,
                f"unsupported non-None template_lang ({type(template_language).__name__})",
            )

    inline_value = _constant_template_value(direct[inline_name])
    file_value = _constant_template_value(direct[file_name])
    if direct[file_name] and file_value is _MISSING_TEMPLATE_VALUE:
        return None, None, f"computed {file_name} cannot be resolved statically"
    if file_value is not _MISSING_TEMPLATE_VALUE and file_value is not None:
        if type(file_value) is not str:
            return None, None, f"{file_name} must be a string or None, not {type(file_value).__name__}"
        if direct[inline_name] and inline_value is _MISSING_TEMPLATE_VALUE:
            return None, None, f"computed {inline_name} prevents proving the active {kind.value} source"
        if inline_value is not _MISSING_TEMPLATE_VALUE and inline_value is not None:
            return None, None, f"non-None {inline_name} and {file_name} declarations conflict"
        return None, file_value, None

    if direct[inline_name] and inline_value is None:
        return None, None, None
    inline_node = direct[inline_name][-1] if direct[inline_name] else None
    if inline_node is None:
        return None, None, None
    if not isinstance(inline_node, ast.Constant) or type(inline_node.value) is not str:
        if isinstance(inline_node, ast.JoinedStr):
            declaration_kind = f"f-string {inline_name} is computed"
        elif type(inline_node).__name__ == "TemplateStr":
            declaration_kind = f"t-string {inline_name} is computed"
        elif isinstance(inline_node, ast.Constant) and type(inline_node.value) is bytes:
            declaration_kind = f"bytes {inline_name} is not supported"
        else:
            declaration_kind = f"computed {inline_name} declaration"
        return None, None, declaration_kind
    return inline_node, None, None


def _direct_component_asset_values(
    class_node: ast.ClassDef,
) -> tuple[dict[str, list[ast.expr | None]], set[str]]:
    direct: dict[str, list[ast.expr | None]] = {name: [] for name in _COMPONENT_ASSET_NAMES}
    nested_bindings: set[str] = set()
    for statement in class_node.body:
        assignment = _direct_template_assignment(statement)
        if assignment is not None:
            name, value = assignment
            if name in _COMPONENT_ASSET_NAMES:
                if isinstance(statement, ast.AnnAssign) and value is None:
                    continue
                direct[name].append(value)
                continue
        nested_bindings.update(
            _template_statement_bound_names(statement) & _COMPONENT_ASSET_NAMES,
        )
    return direct, nested_bindings


@dataclass(frozen=True, slots=True)
class _PythonTemplateFileDeclaration:
    component_name: str
    value: str


@dataclass(frozen=True, slots=True)
class _PythonTemplateFileDiscovery:
    declarations: tuple[_PythonTemplateFileDeclaration, ...]
    notices: tuple[PythonTemplateNotice, ...]


def _discover_python_template_files(source: str) -> _PythonTemplateFileDiscovery:
    """Return statically proven direct native ``template_file`` declarations."""
    module = ast.parse(source)
    declarations: list[_PythonTemplateFileDeclaration] = []
    notices: list[PythonTemplateNotice] = []
    for statement, language in _ast_component_declarations(module):
        value, notice = _literal_template_file_value(statement, language)
        if value is not None:
            declarations.append(_PythonTemplateFileDeclaration(statement.name, value))
        if notice is not None:
            notices.append(PythonTemplateNotice(statement.name, notice))
    return _PythonTemplateFileDiscovery(tuple(declarations), tuple(notices))


def _ast_component_declarations(module: ast.Module) -> list[tuple[ast.ClassDef, object]]:
    """Track definite Citry component classes and their statically known template language."""
    component_symbols: set[str] = set()
    citry_modules: set[str] = set()
    component_classes: set[str] = set()
    component_languages: dict[str, object] = {}
    declarations: list[tuple[ast.ClassDef, object]] = []

    for statement in module.body:
        if isinstance(statement, ast.ImportFrom) and statement.module == "citry" and statement.level == 0:
            for alias in statement.names:
                bound = alias.asname or alias.name
                _discard_template_binding(
                    bound,
                    component_symbols,
                    citry_modules,
                    component_classes,
                    component_languages,
                )
                if alias.name in {"Component", "LibraryComponent"}:
                    component_symbols.add(bound)
            continue
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                _discard_template_binding(
                    bound,
                    component_symbols,
                    citry_modules,
                    component_classes,
                    component_languages,
                )
                if alias.name == "citry":
                    citry_modules.add(bound)
            continue
        if isinstance(statement, ast.ClassDef):
            component_bases = [
                base
                for base in statement.bases
                if _is_template_component_base(base, component_symbols, citry_modules, component_classes)
            ]
            inherited_language = (
                _base_template_language(component_bases[0], component_symbols, component_languages)
                if len(statement.bases) == 1 and len(component_bases) == 1
                else _UNKNOWN_TEMPLATE_LANGUAGE
            )
            _discard_template_binding(
                statement.name,
                component_symbols,
                citry_modules,
                component_classes,
                component_languages,
            )
            if component_bases and not statement.decorator_list:
                component_classes.add(statement.name)
                language = _class_template_language(statement, inherited_language)
                component_languages[statement.name] = language
                declarations.append((statement, language))
            continue
        for bound in _template_statement_bound_names(statement):
            _discard_template_binding(
                bound,
                component_symbols,
                citry_modules,
                component_classes,
                component_languages,
            )
    return declarations


_COMPONENT_CLASS_RE = re.compile(
    r"^(?P<indent>[ \t]*)class\s+(?P<name>[A-Za-z_]\w*)\s*\(\s*"
    r"(?P<base>(?:citry\.)?(?:Component|LibraryComponent))\s*\)\s*:\s*(?:#.*)?$"
)
_TEMPLATE_ASSIGNMENT_RE = re.compile(
    r"^(?P<indent>[ \t]+)template(?:\s*:\s*[^=]+)?\s*=\s*(?P<prefix>[rRuU]?)"
    r"(?P<quote>\"\"\"|''')"
)


def _incomplete_template_regions(source: str) -> list[PythonTemplateRegion]:
    imported_names: set[str] = set()
    import_citry = False
    active_class: tuple[str, int] | None = None
    lines = source.splitlines(keepends=True)
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("from citry import "):
            imported_names.update(
                part.strip().split(" as ")[-1]
                for part in stripped.removeprefix("from citry import ").split(",")
                if part.strip().split(" as ")[0] in {"Component", "LibraryComponent"}
            )
        elif stripped in {"import citry", "import citry as citry"}:
            import_citry = True

        class_match = _COMPONENT_CLASS_RE.match(line.rstrip("\r\n"))
        if class_match is not None:
            base = class_match.group("base")
            proven = (base.startswith("citry.") and import_citry) or base in imported_names
            active_class = (class_match.group("name"), len(class_match.group("indent"))) if proven else None
            continue
        if active_class is None:
            continue
        indent = len(line) - len(line.lstrip(" \t"))
        if stripped and indent <= active_class[1]:
            active_class = None
            continue
        template_match = _TEMPLATE_ASSIGNMENT_RE.match(line.rstrip("\r\n"))
        if template_match is None or len(template_match.group("indent")) <= active_class[1]:
            continue
        start_text = line[: template_match.start("prefix")]
        try:
            source_map = PythonTemplateSourceMap.from_coordinates(
                source,
                lineno=line_number,
                col_offset=len(start_text.encode("utf-8")),
                accept_incomplete=True,
            )
        except ValueError:
            continue
        return [PythonTemplateRegion(active_class[0], source_map)]
    return []


def _literal_template_node(
    class_node: ast.ClassDef,
    language: object,
    *,
    rewrite_notices: bool = False,
) -> tuple[ast.Constant | None, str | None]:
    direct, nested_bindings = _direct_template_values(class_node)
    if nested_bindings:
        return None, None
    if language is _UNKNOWN_TEMPLATE_LANGUAGE:
        if rewrite_notices and direct["template"]:
            return None, "template language cannot be proven to be native Citry; template skipped"
        return None, None
    if language is not None:
        return None, f"unsupported non-None template_lang ({type(language).__name__}); template skipped"
    file_value = _constant_template_value(direct["template_file"])
    inline_value = direct["template"][-1] if direct["template"] else None
    if direct["template_file"] and file_value is _MISSING_TEMPLATE_VALUE:
        if rewrite_notices and inline_value is not None:
            return None, "computed template_file prevents proving the active template source; template skipped"
        return None, None
    if file_value not in (_MISSING_TEMPLATE_VALUE, None):
        if rewrite_notices and inline_value is not None:
            return None, "non-None template_file prevents formatting the inline template; template skipped"
        return None, None
    node = inline_value
    if not isinstance(node, ast.Constant) or type(node.value) is not str:
        if not rewrite_notices or node is None:
            return None, None
        if isinstance(node, ast.JoinedStr):
            kind = "f-string template is computed"
        elif type(node).__name__ == "TemplateStr":
            kind = "t-string template is computed"
        elif isinstance(node, ast.Constant) and type(node.value) is bytes:
            kind = "bytes template is not supported"
        else:
            kind = "computed template declaration"
        return None, f"{kind}; template skipped"
    return node, None


def _literal_template_file_value(
    class_node: ast.ClassDef,
    language: object,
) -> tuple[str | None, str | None]:
    direct, nested_bindings = _direct_template_values(class_node)
    values = direct["template_file"]
    if not values and "template_file" not in nested_bindings:
        return None, None
    if "template_file" in nested_bindings:
        return None, "conditional or nested template_file binding cannot be resolved statically"
    value = _constant_template_value(direct["template_file"])
    if value is _MISSING_TEMPLATE_VALUE:
        return None, "computed template_file cannot be resolved statically"
    if value is None:
        return None, None
    if language is _UNKNOWN_TEMPLATE_LANGUAGE:
        return None, "template language cannot be proven to be native Citry"
    if language is not None:
        return None, f"unsupported non-None template_lang ({type(language).__name__})"
    if type(value) is not str:
        return None, f"template_file must be a string or None, not {type(value).__name__}"
    return value, None


def _direct_template_values(
    class_node: ast.ClassDef,
) -> tuple[dict[str, list[ast.expr | None]], set[str]]:
    relevant = {"template", "template_file"}
    direct: dict[str, list[ast.expr | None]] = {name: [] for name in relevant}
    nested_bindings: set[str] = set()
    for statement in class_node.body:
        assignment = _direct_template_assignment(statement)
        if assignment is not None:
            name, value = assignment
            if name in relevant:
                if isinstance(statement, ast.AnnAssign) and value is None:
                    continue
                direct[name].append(value)
                continue
        nested_bindings.update(_template_statement_bound_names(statement) & relevant)
    return direct, nested_bindings


def _class_template_language(class_node: ast.ClassDef, inherited: object) -> object:
    values: list[ast.expr | None] = []
    for statement in class_node.body:
        assignment = _direct_template_assignment(statement)
        if assignment is not None and assignment[0] == "template_lang":
            if isinstance(statement, ast.AnnAssign) and assignment[1] is None:
                continue
            values.append(assignment[1])
            continue
        if "template_lang" in _template_statement_bound_names(statement):
            return _UNKNOWN_TEMPLATE_LANGUAGE
    if not values:
        return inherited
    final = values[-1]
    return final.value if isinstance(final, ast.Constant) else _UNKNOWN_TEMPLATE_LANGUAGE


_MISSING_TEMPLATE_VALUE = object()
_UNKNOWN_TEMPLATE_LANGUAGE = object()


def _constant_template_value(values: list[ast.expr | None]) -> object:
    if not values or values[-1] is None or not isinstance(values[-1], ast.Constant):
        return _MISSING_TEMPLATE_VALUE
    return values[-1].value


def _direct_template_assignment(statement: ast.stmt) -> tuple[str, ast.expr | None] | None:
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ):
        return statement.targets[0].id, statement.value
    if isinstance(statement, ast.AnnAssign) and statement.simple and isinstance(statement.target, ast.Name):
        return statement.target.id, statement.value
    return None


def _template_statement_bound_names(statement: ast.stmt) -> set[str]:
    names: set[str] = set()

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            return
        if isinstance(node, ast.Lambda):
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        elif isinstance(node, ast.alias):
            names.add(node.asname or node.name.split(".", 1)[0])
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name is not None:
            names.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest is not None:
            names.add(node.rest)
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(statement)
    return names


def _discard_template_binding(
    name: str,
    component_symbols: set[str],
    citry_modules: set[str],
    component_classes: set[str],
    component_languages: dict[str, object],
) -> None:
    component_symbols.discard(name)
    citry_modules.discard(name)
    component_classes.discard(name)
    component_languages.pop(name, None)


def _base_template_language(
    base: ast.expr,
    component_symbols: set[str],
    component_languages: dict[str, object],
) -> object:
    if isinstance(base, ast.Name):
        if base.id in component_symbols:
            return None
        return component_languages.get(base.id, _UNKNOWN_TEMPLATE_LANGUAGE)
    return None


def _is_template_component_base(
    base: ast.expr,
    component_symbols: set[str],
    citry_modules: set[str],
    component_classes: set[str],
) -> bool:
    if isinstance(base, ast.Name):
        return base.id in component_symbols or base.id in component_classes
    return (
        isinstance(base, ast.Attribute)
        and base.attr in {"Component", "LibraryComponent"}
        and isinstance(base.value, ast.Name)
        and base.value.id in citry_modules
    )


def analyze_template_data_source(
    source: str,
    class_qualname: str,
    *,
    kwargs_fields: tuple[str, ...] | None,
) -> TemplateDataSourceShape | None:
    """Run Citry's conservative ``template_data()`` source-shape pass."""
    from citry._template_data_source import analyze_template_data_source as analyze  # noqa: PLC0415

    return analyze(source, class_qualname, kwargs_fields=kwargs_fields)


def analyze_css_data_source(source: str, class_qualname: str) -> TemplateDataSourceShape | None:
    """Run Citry's conservative ``css_data()`` source-shape pass."""
    from citry._template_data_source import analyze_css_data_source as analyze  # noqa: PLC0415

    return analyze(source, class_qualname)


def analyze_js_data_source(source: str, class_qualname: str) -> TemplateDataSourceShape | None:
    """Run Citry's conservative ``js_data()`` source-shape pass."""
    from citry._template_data_source import analyze_js_data_source as analyze  # noqa: PLC0415

    return analyze(source, class_qualname)


def python_event_handler_range(
    source: str,
    function_qualname: str,
    method_name: str,
    wire_name: str,
) -> LspRange | None:
    """Locate one effective server-event method in synchronized source."""
    coordinates = _python_event_handler_coordinates(source, function_qualname, method_name, wire_name)
    if coordinates is None:
        return None
    start_line, start_character, end_line, end_character = coordinates
    return LspRange(
        LspPosition(start_line, start_character),
        LspPosition(end_line, end_character),
    )


def json_wire_type_from_annotation(source: str) -> JsonWireType:
    """Convert one Python annotation into portable JSON-wire metadata."""
    if type(source) is not str:
        msg = "source must be a str"
        raise TypeError(msg)
    return _json_wire_type_from_annotation(source)


def json_wire_type_from_expression(
    source: str,
    *,
    member_types: Mapping[str, Mapping[str, JsonWireType]] | None = None,
) -> JsonWireType:
    """Infer portable JSON-wire metadata using optional proven members."""
    if type(source) is not str:
        msg = "source must be a str"
        raise TypeError(msg)
    return _json_wire_type_from_expression(source, member_types=member_types)


def css_data_references(source: str) -> tuple[CssDataReference, ...]:
    """Return exact unescaped custom-property arguments of CSS ``var()`` calls."""
    if type(source) is not str:
        msg = "source must be a str"
        raise TypeError(msg)
    boundaries = _utf8_boundaries(source)
    return tuple(
        CssDataReference(argument[0], boundaries[argument[1]], boundaries[argument[2]])
        for argument in _css_var_arguments(source)
        if argument[0] and argument[3]
    )


def css_data_reference_at(source: str, index: int) -> CssDataReference | None:
    """Return the exact ``var(--name)`` reference containing one UTF-8 index."""
    references = css_data_references(source)
    return next(
        (reference for reference in references if reference.start_index <= index < reference.end_index),
        None,
    )


def css_data_completion_at(source: str, index: int) -> CssDataCompletion | None:
    """Return the custom-property token that completion should replace."""
    if type(source) is not str:
        msg = "source must be a str"
        raise TypeError(msg)
    boundaries = _utf8_boundaries(source)
    try:
        cursor = boundaries.index(index)
    except ValueError:
        return None
    for name, start, end, _terminated in _css_var_arguments(source):
        if start + 2 <= cursor <= end:
            return CssDataCompletion(name[: max(0, cursor - start - 2)], boundaries[start], boundaries[end])
    return None


def _css_var_arguments(source: str) -> tuple[tuple[str, int, int, bool], ...]:
    """Scan only the first custom-property argument while leaving CSS to its provider."""
    arguments: list[tuple[str, int, int, bool]] = []
    index = 0
    while index < len(source):
        if source.startswith("/*", index):
            closing = source.find("*/", index + 2)
            index = len(source) if closing < 0 else closing + 2
            continue
        if source[index] in {'"', "'"}:
            index = _skip_css_string(source, index)
            continue
        if (
            source[index : index + 3].lower() == "var"
            and index + 3 < len(source)
            and source[index + 3] == "("
            and (index == 0 or not _css_name_char(source[index - 1]))
        ):
            argument = _css_var_argument(source, index + 4)
            if argument is not None:
                arguments.append(argument)
            index += 4
            continue
        index += 1
    return tuple(arguments)


def _css_var_argument(source: str, index: int) -> tuple[str, int, int, bool] | None:
    start = _skip_css_trivia(source, index)
    if not source.startswith("--", start):
        return None
    end = start + 2
    while end < len(source) and _css_name_char(source[end]):
        end += 1
    # CSS escapes can denote the same custom property with different authored
    # text, so the first slice declines them until a positioned decoder exists.
    if end < len(source) and source[end] == "\\":
        return None
    after = _skip_css_trivia(source, end)
    terminated = after < len(source) and source[after] in {",", ")"}
    return source[start + 2 : end], start, end, terminated


def _skip_css_trivia(source: str, index: int) -> int:
    while index < len(source):
        if source[index] in " \t\r\n\f":
            index += 1
            continue
        if source.startswith("/*", index):
            closing = source.find("*/", index + 2)
            return len(source) if closing < 0 else _skip_css_trivia(source, closing + 2)
        return index
    return index


def _skip_css_string(source: str, start: int) -> int:
    quote = source[start]
    index = start + 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
            continue
        if source[index] == quote:
            return index + 1
        index += 1
    return len(source)


def _css_name_char(char: str) -> bool:
    codepoint = ord(char)
    return (char.isascii() and (char.isalnum() or char in "-_")) or (
        codepoint >= 0x80 and not 0xD800 <= codepoint <= 0xDFFF
    )


def _utf8_boundaries(source: str) -> tuple[int, ...]:
    boundaries = [0]
    for char in source:
        boundaries.append(boundaries[-1] + len(char.encode("utf-8")))
    return tuple(boundaries)


def python_application_lint_variable_range(
    source: str,
    target_name: str,
    variable_name: str,
) -> LspRange | None:
    """Locate one variable in a direct application ``LintSettings`` call."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError, ValueError, MemoryError, RecursionError):
        return None
    target = _unique_python_binding(tree.body, target_name, before_line=None)
    if target is None:
        return None
    target_value, target_line = target
    app_call = _resolve_python_value(tree, tree.body, target_value, before_line=target_line)
    lint_value = _call_keyword(app_call, "lint")
    if lint_value is None:
        return None
    lint_call = _resolve_python_value(tree, tree.body, lint_value, before_line=target_line)
    variables_value = _call_keyword(lint_call, "template_variables")
    if variables_value is None:
        return None
    variables = _resolve_python_value(tree, tree.body, variables_value, before_line=target_line)
    key = _unique_string_mapping_key(variables, variable_name)
    return _python_node_lsp_range(source, key) if key is not None else None


def python_component_lint_variable_range(
    source: str,
    lint_qualname: str,
    variable_name: str,
) -> LspRange | None:
    """Locate one variable in an exact nested component ``Lint`` class."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError, ValueError, MemoryError, RecursionError):
        return None
    lint_class = _python_class_for_qualname(tree, lint_qualname)
    if lint_class is None:
        return None
    binding = _unique_python_binding(lint_class.body, "template_variables", before_line=None)
    if binding is None:
        return None
    value, line = binding
    variables = _resolve_python_value(tree, lint_class.body, value, before_line=line)
    key = _unique_string_mapping_key(variables, variable_name)
    return _python_node_lsp_range(source, key) if key is not None else None


def _resolve_python_value(
    tree: ast.Module,
    local_body: list[ast.stmt],
    value: ast.expr,
    *,
    before_line: int,
) -> ast.expr:
    """Follow only direct earlier name bindings needed by authored settings."""
    current = value
    seen: set[str] = set()
    for _depth in range(8):
        if not isinstance(current, ast.Name) or current.id in seen:
            return current
        seen.add(current.id)
        binding = _unique_python_binding(local_body, current.id, before_line=before_line)
        if binding is None and local_body is not tree.body:
            binding = _unique_python_binding(tree.body, current.id, before_line=before_line)
        if binding is None:
            return current
        current, before_line = binding
    return current


def _unique_python_binding(
    body: list[ast.stmt],
    name: str,
    *,
    before_line: int | None,
) -> tuple[ast.expr, int] | None:
    if not name.isidentifier():
        return None
    candidates: list[tuple[ast.expr, int]] = []
    for statement in body:
        if before_line is not None and statement.lineno >= before_line:
            continue
        value: ast.expr | None = None
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in statement.targets
        ):
            value = statement.value
        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == name
            and statement.value is not None
        ):
            value = statement.value
        if value is not None:
            candidates.append((value, statement.lineno))
    return candidates[0] if len(candidates) == 1 else None


def _call_keyword(value: ast.expr, name: str) -> ast.expr | None:
    if not isinstance(value, ast.Call):
        return None
    matches = [keyword.value for keyword in value.keywords if keyword.arg == name]
    return matches[0] if len(matches) == 1 else None


def _unique_string_mapping_key(value: ast.expr, name: str) -> ast.Constant | None:
    if not isinstance(value, ast.Dict):
        return None
    matches = [
        key for key in value.keys if isinstance(key, ast.Constant) and type(key.value) is str and key.value == name
    ]
    return matches[0] if len(matches) == 1 else None


def _python_class_for_qualname(tree: ast.Module, qualname: str) -> ast.ClassDef | None:
    if not qualname or "<locals>" in qualname:
        return None
    body = tree.body
    current: ast.ClassDef | None = None
    for part in qualname.split("."):
        matches = [statement for statement in body if isinstance(statement, ast.ClassDef) and statement.name == part]
        if len(matches) != 1:
            return None
        current = matches[0]
        body = current.body
    return current


def _python_node_lsp_range(source: str, node: ast.expr) -> LspRange | None:
    end_line = getattr(node, "end_lineno", None)
    end_column = getattr(node, "end_col_offset", None)
    if type(end_line) is not int or type(end_column) is not int:
        return None
    try:
        start = _python_coordinate_to_offset(source, node.lineno, node.col_offset)
        end = _python_coordinate_to_offset(source, end_line, end_column)
    except (TypeError, ValueError, UnicodeError):
        return None
    starts = _line_starts(source)
    return LspRange(
        start=_lsp_position(source, starts, start),
        end=_lsp_position(source, starts, end),
    )


def python_class_defines_direct_method(source: str, class_qualname: str, method_name: str) -> bool | None:
    """Return direct method presence, or ``None`` for unprovable source."""
    from citry._template_data_source import python_class_defines_direct_method as resolve  # noqa: PLC0415

    return resolve(source, class_qualname, method_name)


def python_class_direct_method_first_line(source: str, class_qualname: str, method_name: str) -> int | None:
    """Return the authored first line of one exact direct function binding."""
    from citry._template_data_source import python_class_direct_method_first_line as resolve  # noqa: PLC0415

    return resolve(source, class_qualname, method_name)


def python_class_resolution_signature(source: str, class_qualname: str) -> str | None:
    """Fingerprint source that can change one loaded class resolution chain."""
    from citry._template_data_source import python_class_resolution_signature as resolve  # noqa: PLC0415

    return resolve(source, class_qualname)


def python_class_asset_resolution_signature(
    source: str,
    class_qualname: str,
    kind: Literal["template", "js", "css"] = "template",
) -> str | None:
    """Fingerprint current MRO and asset bindings for one component class."""
    from citry._template_data_source import python_class_asset_resolution_signature as resolve  # noqa: PLC0415

    return resolve(source, class_qualname, kind)


def python_class_static_asset_matches(
    source: str,
    class_qualname: str,
    inline_value: object,
    file_value: object,
    kind: Literal["template", "js", "css"] = "template",
) -> bool:
    """Prove that one direct static asset declaration matches runtime state."""
    from citry._template_data_source import python_class_static_asset_matches as resolve  # noqa: PLC0415

    return resolve(source, class_qualname, inline_value, file_value, kind)


__all__ = [
    "ALPINE_AMBIENT_NAMES",
    "SERVER_EVENT_CALL_NAMES",
    "AlpineLintConsumer",
    "AlpineLintFinding",
    "BrowserBinding",
    "BrowserCompletion",
    "BrowserComponentBinding",
    "BrowserComponentPropsUse",
    "BrowserComponentSourceAnalysis",
    "BrowserDeclarativeEvent",
    "BrowserExpression",
    "BrowserExpressionMode",
    "BrowserFreeReference",
    "BrowserI18nBindingDirective",
    "BrowserI18nMessageCall",
    "BrowserI18nProfileCall",
    "BrowserIdentifier",
    "BrowserLiteralCall",
    "BrowserMember",
    "BrowserMemberLiteralCall",
    "BrowserObjectProperty",
    "BrowserProp",
    "BrowserScopeWrite",
    "BrowserSourceAnalysis",
    "ComponentJsLintConsumer",
    "ComponentJsLintFinding",
    "ComponentNameMatch",
    "CspCompatibilityFinding",
    "CssDataCompletion",
    "CssDataReference",
    "JsonWireField",
    "JsonWireKind",
    "JsonWireType",
    "LspPosition",
    "LspRange",
    "PythonComponentAssetDiscovery",
    "PythonComponentAssetFile",
    "PythonComponentAssetFormatResult",
    "PythonComponentAssetKind",
    "PythonComponentAssetNotice",
    "PythonComponentAssetPlan",
    "PythonComponentAssetRegion",
    "PythonComponentAssetRequest",
    "PythonTemplateDiscovery",
    "PythonTemplateFormatError",
    "PythonTemplateFormatResult",
    "PythonTemplateNotice",
    "PythonTemplateRegion",
    "PythonTemplateSourceMap",
    "ShadowPythonCopy",
    "ShadowPythonDocument",
    "ShadowPythonSourceCopy",
    "TemplateAnalysis",
    "TemplateLintConsumer",
    "TemplateLintFinding",
    "TemplatePythonControl",
    "TemplatePythonQuery",
    "TemplatePythonRoot",
    "TemplateTagUse",
    "UnknownComponentUse",
    "analyze_browser_component_source",
    "analyze_browser_expression",
    "analyze_css_data_source",
    "analyze_js_data_source",
    "analyze_template_data_source",
    "browser_bindings",
    "browser_client_prop_accepts",
    "browser_completion_at",
    "browser_component_prop_uses",
    "browser_component_props",
    "browser_component_scope_writes",
    "browser_declarative_events",
    "browser_expression_at",
    "browser_expressions",
    "browser_i18n_bind_calls",
    "browser_i18n_binding_directives",
    "browser_i18n_message_calls",
    "browser_i18n_profile_calls",
    "browser_identifier_at",
    "browser_identifiers",
    "browser_literal_calls",
    "browser_literal_wire_type",
    "browser_member_at",
    "browser_member_literal_calls",
    "build_inferred_template_shadow",
    "build_schema_template_shadow",
    "component_name_match",
    "css_data_completion_at",
    "css_data_reference_at",
    "css_data_references",
    "discover_python_component_assets",
    "discover_python_templates",
    "finish_python_component_assets",
    "format_python_component_assets",
    "format_python_templates",
    "json_wire_type_from_annotation",
    "json_wire_type_from_expression",
    "lint_csp_compatibility",
    "lint_unknown_alpine_variables",
    "lint_unknown_component_js_variables",
    "lint_unknown_template_variables",
    "merge_json_wire_types",
    "prepare_python_component_assets",
    "python_class_asset_resolution_signature",
    "python_class_defines_direct_method",
    "python_class_direct_method_first_line",
    "python_class_resolution_signature",
    "python_class_static_asset_matches",
    "python_event_handler_range",
    "template_python_queries",
    "template_python_query_at",
    "template_tag_uses",
    "unknown_component_uses",
]
