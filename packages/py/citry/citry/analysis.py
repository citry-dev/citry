"""Supported template analysis and Python-to-LSP source coordinates."""

from __future__ import annotations

import ast
import hashlib
import re
import unicodedata
from array import array
from bisect import bisect_left, bisect_right
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from difflib import SequenceMatcher, get_close_matches
from enum import Enum
from itertools import pairwise
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from citry._browser_expressions import (
    SERVER_EVENT_CALL_NAMES,
    BrowserBinding,
    BrowserCompletion,
    BrowserComponentBinding,
    BrowserComponentCall,
    BrowserComponentContextName,
    BrowserComponentMemberReference,
    BrowserComponentPropContribution,
    BrowserComponentPropFinding,
    BrowserComponentPropSite,
    BrowserComponentPublicName,
    BrowserComponentSection,
    BrowserComponentSourceAnalysis,
    BrowserDeclarativeEvent,
    BrowserEmitName,
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
    BrowserSourceAnalysis,
    BrowserStateBinding,
    BrowserStateBindingTargetError,
    MarkLiteralFinding,
    _ascii_lower,
    _nested_template,
    analyze_browser_component_source,
    analyze_browser_expression,
    browser_bindings,
    browser_client_prop_accepts,
    browser_completion_at,
    browser_component_prop_findings,
    browser_component_prop_sites,
    browser_component_props,
    browser_declarative_events,
    browser_expression_at,
    browser_expressions,
    browser_i18n_bind_calls,
    browser_i18n_binding_directives,
    browser_i18n_calls_checkable,
    browser_i18n_message_calls,
    browser_i18n_profile_calls,
    browser_identifier_at,
    browser_identifiers,
    browser_literal_calls,
    browser_literal_wire_type,
    browser_member_at,
    browser_member_literal_calls,
    browser_proven_member_literal_calls,
    browser_state_binding_target_errors,
    browser_state_bindings,
    component_js_i18n_owners,
    mark_literal_findings,
)
from citry._browser_expressions import (
    python_event_handler_coordinates as _python_event_handler_coordinates,
)
from citry._diagnostic_catalog import (
    BROWSER_PROP_ASSIGNMENT,
    BROWSER_UNDECLARED_COMPONENT_EVENT,
    BROWSER_UNDECLARED_EMIT,
    COMPONENT_JS_UNKNOWN_MEMBER,
    COMPONENT_JS_UNKNOWN_VARIABLE,
    CSS_MISSPELLED_VARIABLE,
    FORMAT_EMBEDDED_INTERPOLATION_UNSUPPORTED,
    FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED,
    FORMAT_HOST_SYNTAX,
    FORMAT_INELIGIBLE,
    FORMAT_INVARIANT,
    FORMAT_PROVIDER_INVALID,
    FORMAT_PROVIDER_UNAVAILABLE,
    TEMPLATE_ALPINE_ATTRIBUTE,
    TEMPLATE_ALPINE_CLOAK,
    TEMPLATE_INVALID_ATTRIBUTE_VALUE,
    TEMPLATE_MISSPELLED_DIRECTIVE,
    TEMPLATE_UNKNOWN_VARIABLE,
    VUE_PYTHON_VARIABLE,
    VUE_UNKNOWN_VARIABLE,
)
from citry._diagnostics import render_diagnostic
from citry._html_attribute_values import (
    BOOLEAN_ATTRIBUTES as _BOOLEAN_ATTRIBUTES,
)
from citry._html_attribute_values import (
    CASE_SENSITIVE_KEYWORDS as _CASE_SENSITIVE_KEYWORDS,
)
from citry._html_attribute_values import (
    CUSTOM_ELEMENT_ATTRIBUTES as _CUSTOM_ELEMENT_ATTRIBUTES,
)
from citry._html_attribute_values import (
    DOM_EVENT_NAMES as _DOM_EVENT_NAMES,
)
from citry._html_attribute_values import (
    ELEMENT_ATTRIBUTES as _ELEMENT_ATTRIBUTES,
)
from citry._html_attribute_values import (
    ENUMERATED_VALUES as _ENUMERATED_ATTRIBUTE_VALUES,
)
from citry._html_attribute_values import (
    FRAME_NAME_ELEMENTS as _FRAME_NAME_ELEMENTS,
)
from citry._html_attribute_values import (
    GLOBAL_ATTRIBUTES as _GLOBAL_ATTRIBUTES,
)
from citry._html_attribute_values import (
    HTML_ELEMENTS as _HTML_ELEMENTS,
)
from citry._html_attribute_values import (
    NAVIGABLE_TARGET_ATTRIBUTES as _NAVIGABLE_TARGET_ATTRIBUTES,
)
from citry._html_attribute_values import (
    NAVIGABLE_TARGET_KEYWORDS as _NAVIGABLE_TARGET_KEYWORDS,
)
from citry._inline_assets import normalize_inline_asset
from citry._json_wire import JsonWireField, JsonWireKind, JsonWireType, WireClass, merge_json_wire_types
from citry._json_wire import json_wire_type_from_annotation as _json_wire_type_from_annotation
from citry._json_wire import json_wire_type_from_expression as _json_wire_type_from_expression
from citry._linting import TemplateLintInfo
from citry._markup_lint import ELEMENT_DIRECTIVES as _ELEMENT_DIRECTIVES
from citry._markup_lint import FOREIGN_DIRECTIVES as _FOREIGN_DIRECTIVES
from citry._markup_lint import (
    MARKUP_LINT_RULES,
    MarkupLintConsumer,
    MarkupLintFinding,
    _is_directive_typo,
    lint_invalid_vue_expressions,
    lint_markup,
    one_slip_from,
)
from citry._markup_lint import SPELLED_OUT_ELIF as _SPELLED_OUT_ELIF
from citry._portable_ide import (
    ComponentNameMatch,
    TemplateTagUse,
    UnknownComponentUse,
    component_name_match,
    template_tag_uses,
    unknown_component_uses,
)
from citry._source_lines import source_lines
from citry._template_python import ShadowPythonCopy as _ShadowPythonCopy
from citry._template_python import ShadowPythonDocument as _ShadowPythonDocument
from citry._template_python import ShadowPythonSourceCopy as _ShadowPythonSourceCopy
from citry._template_python import ShadowRevealDocument as _ShadowRevealDocument
from citry._template_python import TemplatePythonControl as _TemplatePythonControl
from citry._template_python import TemplatePythonQuery as _TemplatePythonQuery
from citry._template_python import TemplatePythonRoot as _TemplatePythonRoot
from citry._template_python import TemplatePythonValueType as _TemplatePythonValueType
from citry._template_python import build_inferred_template_shadow as _build_inferred_template_shadow
from citry._template_python import build_reveal_shadow as _build_reveal_shadow
from citry._template_python import build_schema_template_shadow as _build_schema_template_shadow
from citry._template_python import template_python_queries as _template_python_queries
from citry._template_python import template_python_query_at as _template_python_query_at
from citry._template_python import template_static_input_queries as _template_static_input_queries
from citry.util.html import decode_attribute_entities
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
from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttr, HtmlAttrKind, TagRules, TemplateElement
from citry_core.template_parser import parse_template as _parse_template

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

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
TemplatePythonValueType = _TemplatePythonValueType
ShadowPythonCopy = _ShadowPythonCopy
ShadowPythonDocument = _ShadowPythonDocument
ShadowPythonSourceCopy = _ShadowPythonSourceCopy
ShadowRevealDocument = _ShadowRevealDocument


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
class VueLintConsumer:
    """Describe one proven browser namespace used by a physical template."""

    known_names: frozenset[str]
    rule_unknown_vue_variable: Literal["ignore", "warning", "error"]
    namespace_policy: Literal["closed", "unknown"] = "closed"
    rule_vue_python_variable: Literal["ignore", "warning", "error"] = "warning"

    def __post_init__(self) -> None:
        if type(self.known_names) is not frozenset or any(
            type(name) is not str or not name for name in self.known_names
        ):
            msg = "VueLintConsumer.known_names must be a frozenset of non-empty strings"
            raise TypeError(msg)
        if type(self.rule_unknown_vue_variable) is not str or self.rule_unknown_vue_variable not in {
            "ignore",
            "warning",
            "error",
        }:
            msg = f"Unknown Vue-variable rule severity: {self.rule_unknown_vue_variable!r}"
            raise ValueError(msg)
        if self.namespace_policy not in {"closed", "unknown"}:
            msg = f"Unknown Vue namespace policy: {self.namespace_policy!r}"
            raise ValueError(msg)
        if type(self.rule_vue_python_variable) is not str or self.rule_vue_python_variable not in {
            "ignore",
            "warning",
            "error",
        }:
            msg = f"Unknown Vue Python-variable rule severity: {self.rule_vue_python_variable!r}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class VueLintFinding:
    """Report one OXC-proven free root missing from a browser namespace."""

    name: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class AlpineAttributeLintConsumer:
    """
    Carry one consuming component's severities for leftover Alpine attributes.

    Attributes:
        rule_alpine_attribute: Configured severity for an ``x-*`` attribute
            other than ``x-cloak``.
        rule_alpine_cloak: Configured severity for ``x-cloak``.

    """

    rule_alpine_attribute: Literal["ignore", "warning", "error"] = "warning"
    rule_alpine_cloak: Literal["ignore", "warning", "error"] = "error"

    def __post_init__(self) -> None:
        for rule_name in ("rule_alpine_attribute", "rule_alpine_cloak"):
            severity = getattr(self, rule_name)
            if type(severity) is not str or severity not in {"ignore", "warning", "error"}:
                msg = f"Unknown {rule_name} severity: {severity!r}"
                raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class AlpineAttributeFinding:
    """Report one Alpine ``x-*`` attribute on an HTML element, spanning its name."""

    name: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int


# Severity of an invalid attribute value when no setting chooses one, as in
# `citry check --static` for a component whose source Lint class does not
# set the rule. The application's LintSettings cannot be read there, so a
# warning keeps a value that a page script reads from failing the check.
_NO_SETTINGS_ATTRIBUTE_VALUE_SEVERITY: Literal["warning"] = "warning"


@dataclass(frozen=True, slots=True)
class AttributeValueLintConsumer:
    """
    Carry one consuming component's severity for invalid enumerated and boolean attribute values.

    Attributes:
        rule_invalid_attribute_value: Configured severity for a static value
            outside an enumerated HTML attribute's keywords. The default,
            ``"error"``, matches ``LintSettings``.

    """

    rule_invalid_attribute_value: Literal["ignore", "warning", "error"] = "error"

    def __post_init__(self) -> None:
        severity = self.rule_invalid_attribute_value
        if type(severity) is not str or severity not in {"ignore", "warning", "error"}:
            msg = f"Unknown rule_invalid_attribute_value severity: {severity!r}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class MisspelledDirectiveLintConsumer:
    """
    Carry one consuming component's severity for a ``c-*`` or ``v-*`` attribute that looks like a misspelled directive.

    Attributes:
        rule_misspelled_directive: Configured severity for a name such as
            ``c-iff``, which Citry renders as an ordinary HTML attribute, or
            ``v-iff``, which Vue reads as an unknown custom directive.

    """

    rule_misspelled_directive: Literal["ignore", "warning", "error"] = "error"

    def __post_init__(self) -> None:
        severity = self.rule_misspelled_directive
        if type(severity) is not str or severity not in {"ignore", "warning", "error"}:
            msg = f"Unknown rule_misspelled_directive severity: {severity!r}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class MisspelledDirectiveFinding:
    """Report one ``c-*`` or ``v-*`` attribute that looks like a misspelled directive, spanning its name."""

    name: str
    suggestion: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int


# The rules a check can run without importing the application. They need
# no component data, only the template and each owner's severity.
_SOURCE_LINT_RULES = (
    "rule_alpine_attribute",
    "rule_alpine_cloak",
    "rule_invalid_attribute_value",
    "rule_misspelled_directive",
    *MARKUP_LINT_RULES,
)


@dataclass(frozen=True, slots=True)
class ComponentSourceLint:
    """
    Hold the severities a component's ``Lint`` class sets, read from its Python source.

    ``citry check --static`` and an editor that has not loaded the
    application cannot read ``LintSettings``, but they can read the string
    literals a component writes in its ``Lint`` class, so the component's
    own choice still applies there. Values a ``Lint`` inherits from a
    component class in the same file are included, nearest first. Only the
    rules those tools run are read.

    A field is ``None`` when the component does not set that rule, or when
    the value cannot be read from the source, such as a name imported from
    another module. The rule then keeps the severity it has without an
    application: the ``LintSettings`` default, except that an invalid
    attribute value is a warning.

    Attributes:
        rule_alpine_attribute: ``Lint.rule_alpine_attribute``, when readable.
        rule_alpine_cloak: ``Lint.rule_alpine_cloak``, when readable.
        rule_invalid_attribute_value: ``Lint.rule_invalid_attribute_value``,
            when readable.
        rule_misspelled_directive: ``Lint.rule_misspelled_directive``, when
            readable.
        rule_misspelled_attribute: ``Lint.rule_misspelled_attribute``, when
            readable.
        rule_misspelled_element: ``Lint.rule_misspelled_element``, when
            readable.
        rule_unknown_aria_attribute: ``Lint.rule_unknown_aria_attribute``,
            when readable.
        rule_invalid_nesting: ``Lint.rule_invalid_nesting``, when readable.
        rule_duplicate_id: ``Lint.rule_duplicate_id``, when readable.
        rule_missing_image_alt: ``Lint.rule_missing_image_alt``, when
            readable.
        rule_invalid_model_target: ``Lint.rule_invalid_model_target``, when
            readable.
        rule_misspelled_event: ``Lint.rule_misspelled_event``, when readable.
        rule_invalid_vue_expression: ``Lint.rule_invalid_vue_expression``,
            when readable.

    """

    rule_alpine_attribute: Literal["ignore", "warning", "error"] | None = None
    rule_alpine_cloak: Literal["ignore", "warning", "error"] | None = None
    rule_invalid_attribute_value: Literal["ignore", "warning", "error"] | None = None
    rule_misspelled_directive: Literal["ignore", "warning", "error"] | None = None
    rule_misspelled_attribute: Literal["ignore", "warning", "error"] | None = None
    rule_misspelled_element: Literal["ignore", "warning", "error"] | None = None
    rule_unknown_aria_attribute: Literal["ignore", "warning", "error"] | None = None
    rule_invalid_nesting: Literal["ignore", "warning", "error"] | None = None
    rule_duplicate_id: Literal["ignore", "warning", "error"] | None = None
    rule_missing_image_alt: Literal["ignore", "warning", "error"] | None = None
    rule_invalid_model_target: Literal["ignore", "warning", "error"] | None = None
    rule_misspelled_event: Literal["ignore", "warning", "error"] | None = None
    rule_invalid_vue_expression: Literal["ignore", "warning", "error"] | None = None

    def __post_init__(self) -> None:
        for rule_name in _SOURCE_LINT_RULES:
            severity = getattr(self, rule_name)
            if severity is not None and (type(severity) is not str or severity not in {"ignore", "warning", "error"}):
                msg = f"Unknown {rule_name} severity: {severity!r}"
                raise ValueError(msg)

    def alpine_consumer(self) -> AlpineAttributeLintConsumer:
        """Return this component's severities for the Alpine rules, with the defaults for unset ones."""
        defaults = AlpineAttributeLintConsumer()
        return AlpineAttributeLintConsumer(
            self.rule_alpine_attribute or defaults.rule_alpine_attribute,
            self.rule_alpine_cloak or defaults.rule_alpine_cloak,
        )

    def attribute_value_consumer(self) -> AttributeValueLintConsumer:
        """Return this component's severity for invalid attribute values, a warning when unset."""
        # Unset matches what lint_attribute_values does with no consumers,
        # so a template keeps one severity whether or not its owner is known.
        return AttributeValueLintConsumer(self.rule_invalid_attribute_value or _NO_SETTINGS_ATTRIBUTE_VALUE_SEVERITY)

    def directive_consumer(self) -> MisspelledDirectiveLintConsumer:
        """Return this component's severity for misspelled directives, the default when unset."""
        if self.rule_misspelled_directive is None:
            return MisspelledDirectiveLintConsumer()
        return MisspelledDirectiveLintConsumer(self.rule_misspelled_directive)

    def markup_consumer(self) -> MarkupLintConsumer:
        """Return this component's severities for the rules that read a template's HTML, the defaults when unset."""
        # The source does not show whether the component has browser code,
        # so a root `<img>` may get its `alt` from a parent, as the
        # consumer's default assumes.
        return MarkupLintConsumer(
            **{rule: getattr(self, rule) for rule in MARKUP_LINT_RULES if getattr(self, rule) is not None},
        )


@dataclass(frozen=True, slots=True)
class AttributeValueFinding:
    """
    Report one static HTML attribute value outside its enumerated keywords, or a boolean attribute's value.

    The span covers the value inside its quotes, or the attribute name when
    the value is empty or missing.
    """

    element: str
    attribute: str
    value: str
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
    """Report one invalid name inside a `$component` initializer."""

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


# Component JavaScript runs as an ordinary browser script, so Citry's own
# global and the page's DOM interfaces are in scope there. Vue template
# expressions cannot reach them, so these stay out of VUE_AMBIENT_NAMES.
_COMPONENT_JS_BROWSER_GLOBALS = frozenset(
    {
        "AbortController",
        "AbortSignal",
        "Blob",
        "CSS",
        "CSSStyleSheet",
        "Citry",
        "DOMException",
        "DOMParser",
        "DOMRect",
        "DataTransfer",
        "Document",
        "DocumentFragment",
        "EventTarget",
        "File",
        "FileReader",
        "FormData",
        "HTMLCollection",
        "Headers",
        "Image",
        "IntersectionObserver",
        "MutationObserver",
        "Node",
        "NodeList",
        "Range",
        "Request",
        "ResizeObserver",
        "Response",
        "Selection",
        "ShadowRoot",
        "Text",
        "TextDecoder",
        "TextEncoder",
        "WebSocket",
        "Window",
        "Worker",
        "XMLHttpRequest",
        "alert",
        "atob",
        "btoa",
        "cancelIdleCallback",
        "confirm",
        "crypto",
        "customElements",
        "getComputedStyle",
        "getSelection",
        "innerHeight",
        "innerWidth",
        "matchMedia",
        "prompt",
        "requestIdleCallback",
        "scrollX",
        "scrollY",
        "self",
    }
)
# Every element interface, such as HTMLInputElement or SVGPathElement, and
# every event class, such as KeyboardEvent or MessageEvent.
_DOM_INTERFACE = re.compile(r"(?:HTML|SVG)[A-Za-z]*Element|[A-Z][A-Za-z]*Event")


VUE_AMBIENT_NAMES = frozenset(
    {
        *COMPONENT_JS_AMBIENT_NAMES,
        # Vue template public-instance properties.
        "$attrs",
        "$data",
        "$el",
        "$emit",
        "$event",
        "$forceUpdate",
        "$nextTick",
        "$options",
        "$parent",
        "$props",
        "$refs",
        "$root",
        "$slots",
        "$watch",
        # Citry's Vue magic/context surface.
        "$error",
        "$loading",
        "$onEvent",
        "$sendEvent",
        "$state",
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


def lint_unknown_vue_variables(
    expressions: Sequence[BrowserExpression],
    consumers: Sequence[VueLintConsumer],
) -> tuple[VueLintFinding, ...]:
    """Diagnose OXC-proven Vue roots missing from any physical owner."""
    if not consumers:
        return ()
    findings: list[VueLintFinding] = []
    for expression in expressions:
        analysis = analyze_browser_expression(expression)
        if not analysis.valid:
            continue
        lexical = frozenset((*VUE_AMBIENT_NAMES, *expression.bindings))
        for reference in analysis.references:
            if reference.name in lexical:
                continue
            missing = [
                consumer
                for consumer in consumers
                if consumer.namespace_policy == "closed" and reference.name not in consumer.known_names
            ]
            active = [consumer for consumer in missing if consumer.rule_unknown_vue_variable != "ignore"]
            if not active:
                continue
            severity: Literal["warning", "error"] = (
                "error" if any(consumer.rule_unknown_vue_variable == "error" for consumer in active) else "warning"
            )
            # A Python loop or slot variable of the same name is the likely
            # cause, so say so in the one finding this span gets.
            variant = "python" if _is_python_bound(reference.name, expression) else "default"
            findings.append(
                VueLintFinding(
                    name=reference.name,
                    message=render_diagnostic(VUE_UNKNOWN_VARIABLE, variant=variant, name=reference.name),
                    code=VUE_UNKNOWN_VARIABLE,
                    severity=severity,
                    start_index=reference.start_index,
                    end_index=reference.end_index,
                )
            )
    return tuple(findings)


def lint_vue_python_variables(
    expressions: Sequence[BrowserExpression],
    consumers: Sequence[VueLintConsumer],
) -> tuple[VueLintFinding, ...]:
    """
    Warn when a Vue expression reads a name that a Python loop or slot binds there.

    Inside `<li c-for="item in items" :title="item">`, Python renders one `li`
    per item, but Vue evaluates `item` later in the browser against the
    component's Vue state, so the binding never sees the loop value.

    When a closed browser namespace proves the name missing, the
    unknown-variable rule already reports the read as an error that names the
    Python variable, so this rule stays quiet to give each read one finding.
    It covers the remaining cases: an open namespace that cannot prove the
    name missing, an unknown-variable rule set to ``"ignore"``, and a
    component whose browser data also defines the name. In the last case Vue
    shows the component's value without any error, so the message names both
    meanings of the name.

    Args:
        expressions: Browser expressions with their enclosing Python bindings.
        consumers: Every proven component that consumes this physical template.

    Returns:
        Findings in expression and source order. No consumer means no finding,
        matching the unknown-variable rule, because syntax-only analysis cannot
        prove which browser names exist.

    """
    if not consumers:
        return ()
    findings: list[VueLintFinding] = []
    for expression in expressions:
        # Most expressions sit outside any Python loop, so skip parsing them.
        if not expression.python_bindings:
            continue
        analysis = analyze_browser_expression(expression)
        if not analysis.valid:
            continue
        # A Vue `v-for` or slot alias, or a Vue helper, owns the name in the
        # browser, so the expression reads the value the author bound there.
        lexical = frozenset((*VUE_AMBIENT_NAMES, *expression.bindings))
        for reference in analysis.references:
            if reference.name in lexical or not _is_python_bound(reference.name, expression):
                continue
            # The unknown-variable rule reports this read already.
            if any(
                consumer.namespace_policy == "closed"
                and reference.name not in consumer.known_names
                and consumer.rule_unknown_vue_variable != "ignore"
                for consumer in consumers
            ):
                continue
            active = [consumer for consumer in consumers if consumer.rule_vue_python_variable != "ignore"]
            if not active:
                continue
            severity: Literal["warning", "error"] = (
                "error" if any(consumer.rule_vue_python_variable == "error" for consumer in active) else "warning"
            )
            # When the component's browser data also defines the name, Vue shows
            # that value instead of the loop value and nothing fails, so the
            # message names both meanings rather than calling the name missing.
            # Only a component that reports the read decides which message it gets.
            browser_known = any(reference.name in consumer.known_names for consumer in active)
            attribute = _python_attribute_for(expression, reference.name)
            if attribute is not None:
                variant = "browser-attribute" if browser_known else "attribute"
                message = render_diagnostic(
                    VUE_PYTHON_VARIABLE, variant=variant, name=reference.name, attribute=attribute
                )
            else:
                message = render_diagnostic(
                    VUE_PYTHON_VARIABLE, variant="browser" if browser_known else "default", name=reference.name
                )
            findings.append(
                VueLintFinding(
                    name=reference.name,
                    message=message,
                    code=VUE_PYTHON_VARIABLE,
                    severity=severity,
                    start_index=reference.start_index,
                    end_index=reference.end_index,
                )
            )
    return tuple(findings)


def _is_python_bound(name: str, expression: BrowserExpression) -> bool:
    """Return whether an enclosing `c-for` or `c-fill` binds this JavaScript name in Python."""
    # The parser stores Python names NFKC-normalized, as Python itself does,
    # so `ﬁ` in JavaScript must match the Python loop variable `fi`.
    return _identifier_identity(name) in {_identifier_identity(item) for item in expression.python_bindings}


# `:name` or `v-bind:name` with no modifiers. A modifier such as `.prop` or
# `.camel` changes what the binding sets, so `c-name` would not be equivalent.
_VUE_BOUND_ATTRIBUTE = re.compile(r"(?::|v-bind:)([A-Za-z_][A-Za-z0-9_:-]*)")
# Vue treats these bindings as instructions, not HTML attributes.
_VUE_SPECIAL_BINDINGS = frozenset({"key", "ref", "is"})


def _python_attribute_for(expression: BrowserExpression, name: str) -> str | None:
    """Return the attribute that `c-<attribute>="<name>"` can set from Python instead."""
    # Only a plain element attribute bound to exactly the Python name has an
    # equivalent `c-` attribute. Anything else gets the general suggestion:
    # `:title="item + label"` also reads Vue state, and a component tag's
    # `:title` is a Vue prop, where `c-title` would become a Python kwarg.
    if expression.host != "vue" or expression.evaluator == "raw" or expression.source.strip() != name:
        return None
    match = _VUE_BOUND_ATTRIBUTE.fullmatch(expression.attribute)
    if match is None:
        return None
    attribute = match.group(1)
    # `:c-name` binds Citry State, so prefixing it again would name nothing.
    if attribute.startswith("c-") or attribute in _VUE_SPECIAL_BINDINGS:
        return None
    return attribute


def lint_alpine_attributes(
    template: Template,
    consumers: Sequence[AlpineAttributeLintConsumer],
    *,
    parse_nested: Callable[[str], Template] = _parse_template,
) -> tuple[AlpineAttributeFinding, ...]:
    """
    Report Alpine ``x-*`` attributes left on HTML elements.

    Citry uses Vue, so it renders an attribute such as ``x-data`` unchanged
    and nothing in the browser reads it. ``x-cloak`` is worse: nothing removes
    it, so a ``[x-cloak]`` CSS rule hides the element for good. ``x-cloak``
    gets only the cloak finding, never both. Names compare without regard to
    ASCII letter case, as HTML attribute names do.

    Only plain HTML elements and ``<c-element>`` are checked, including
    elements inside nested templates. On a component tag an ``x-*`` attribute
    is an ordinary Python keyword argument.

    A finding is reported unless every consumer ignores its rule, and it is an
    error when any reporting consumer says ``"error"``. Unlike the
    unknown-variable rules, this check needs no component namespace, so it
    still runs when no consumer is proven. An empty ``consumers`` uses the
    built-in defaults: ``"warning"`` for ``x-*`` attributes and ``"error"``
    for ``x-cloak``. ``citry check --static`` and an editor without project
    analysis rely on this; a caller that knows the application's
    [`LintSettings`][citry.LintSettings] passes them as one consumer.

    Args:
        template: Parsed Citry template AST.
        consumers: Every proven component that consumes this physical template.
        parse_nested: Parser for template-valued attributes, so nested
            templates use the same parse options as the outer one.

    Returns:
        Findings in source order, each spanning the attribute name.

    """
    # With no proven owner the defaults still apply, because whether an
    # attribute is an Alpine leftover does not depend on the component.
    effective = tuple(consumers) or (AlpineAttributeLintConsumer(),)
    found: list[tuple[str, int, int]] = []
    _collect_alpine_attributes(template, found, parse_nested=parse_nested, base_index=0)
    findings: list[AlpineAttributeFinding] = []
    for name, start_index, end_index in sorted(found, key=lambda item: (item[1], item[2])):
        is_cloak = _ascii_lower(name) == "x-cloak"
        severities = [
            consumer.rule_alpine_cloak if is_cloak else consumer.rule_alpine_attribute for consumer in effective
        ]
        active = [severity for severity in severities if severity != "ignore"]
        if not active:
            continue
        code = TEMPLATE_ALPINE_CLOAK if is_cloak else TEMPLATE_ALPINE_ATTRIBUTE
        findings.append(
            AlpineAttributeFinding(
                name=name,
                message=render_diagnostic(code) if is_cloak else render_diagnostic(code, name=name),
                code=code,
                severity="error" if "error" in active else "warning",
                start_index=start_index,
                end_index=end_index,
            )
        )
    return tuple(findings)


# Alpine's own directives and those of its official plugins. Other `x-*`
# names, such as the vendor attribute `x-webkit-airplay`, are ordinary HTML
# that browsers or other libraries read, so they are not reported.
_ALPINE_DIRECTIVES = frozenset(
    {
        "data", "init", "show", "bind", "on", "text", "html", "model", "modelable", "for",
        "transition", "effect", "ignore", "ref", "cloak", "teleport", "if", "id",
        "intersect", "trap", "collapse", "anchor", "mask", "sort", "resize", "persist",
    }
)  # fmt: skip


def _is_alpine_attribute(name: str) -> bool:
    """Return whether an attribute name is an Alpine directive, with any argument or modifiers."""
    lowered = _ascii_lower(name)
    if not lowered.startswith("x-"):
        return False
    directive = re.split(r"[:.]", lowered[2:], maxsplit=1)[0]
    return directive in _ALPINE_DIRECTIVES


def _collect_alpine_attributes(
    template: Template,
    found: list[tuple[str, int, int]],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> None:
    """Collect each ``x-*`` attribute name on an HTML element with its byte span."""
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        tag = _ascii_lower(node.start_tag.name.content)
        # A component tag passes `x-*` to Python as a keyword argument, and
        # the other built-in tags do not render their own attributes. Only
        # `<c-element>` writes its attributes onto a real HTML element.
        renders_attributes = not tag.startswith("c-") or tag == "c-element"
        for attr in node.start_tag.attrs:
            if renders_attributes and _is_alpine_attribute(attr.key.content):
                found.append((attr.key.content, base_index + attr.key.start_index, base_index + attr.key.end_index))
            # A template-valued attribute holds more HTML, whose offsets are
            # relative to the nested source, so shift them into this template.
            inner = attr.inner_value
            if attr.kind == HtmlAttrKind.Template and inner is not None:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    _collect_alpine_attributes(
                        parsed,
                        found,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                    )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_alpine_attributes(body, found, parse_nested=parse_nested, base_index=base_index)


def lint_attribute_values(
    template: Template,
    consumers: Sequence[AttributeValueLintConsumer],
    *,
    parse_nested: Callable[[str], Template] = _parse_template,
) -> tuple[AttributeValueFinding, ...]:
    """
    Report static HTML attribute values that an enumerated or boolean attribute does not accept.

    Some HTML attributes take only fixed keywords, such as ``draggable``
    (``"true"`` or ``"false"``) or ``type`` on ``<input>``. A browser ignores
    any other value or falls back to a default, so ``draggable="treu"``
    silently does nothing. The keywords come from the HTML Standard; see
    ``scripts/generate_html_attribute_values.py``.

    Keywords compare without regard to ASCII letter case, except the list
    markers ``1``, ``a``, ``A``, ``i``, and ``I`` of ``type`` on ``<ol>`` and
    ``<li>``. Character references are decoded first, as the browser does,
    and an attribute with no value counts as the empty string. For
    ``target`` and ``formtarget``, only a value starting with ``_`` is
    checked, because any other value is a valid window name; the ``name`` of
    an ``<iframe>`` or ``<object>`` may not start with ``_`` at all.

    Only static attributes on lowercase HTML element names are checked,
    including elements inside nested templates, and Vue bindings whose
    value is one JavaScript string, such as ``:dir="'rlt'"``, which set the
    same text. Component tags, ``<c-element>``, custom elements, PascalCase
    Vue components, elements inside ``<svg>`` or ``<math>``, other bound
    values, bindings with a modifier such as ``.prop``, and attributes whose
    value contains syntax an extension handles are skipped.

    An ``http-equiv`` value that is not a standard pragma, such as
    ``Cache-Control``, is reported with a message that browsers ignore it
    and that it belongs in an HTTP response header.

    A boolean attribute, such as ``disabled``, is on whenever it is present,
    so any value other than the empty string or the attribute's own name,
    in any letter case, is reported, including ``"false"``. ``draggable``,
    ``spellcheck``, and ``contenteditable`` take ``"true"`` and ``"false"`` as
    keywords; they are not boolean.

    A finding is reported unless every consumer ignores the rule, and it is an
    error when any reporting consumer says ``"error"``. The check needs no
    component namespace, so it also runs with an empty ``consumers``, as
    ``citry check --static`` and an editor without project analysis call it
    for a template whose owner they cannot find. Findings are then warnings,
    because the application's ``LintSettings``, which might turn the rule
    off, cannot be read there.
    [`ComponentSourceLint`][citry.ComponentSourceLint] builds the consumers
    for an owner those tools can read.

    Args:
        template: Parsed Citry template AST.
        consumers: Every proven component that consumes this physical template.
        parse_nested: Parser for template-valued attributes, so nested
            templates use the same parse options as the outer one.

    Returns:
        Findings in source order.

    """
    effective = tuple(consumers) or (AttributeValueLintConsumer(_NO_SETTINGS_ATTRIBUTE_VALUE_SEVERITY),)
    active = [consumer.rule_invalid_attribute_value for consumer in effective]
    active = [severity for severity in active if severity != "ignore"]
    if not active:
        return ()
    severity: Literal["warning", "error"] = "error" if "error" in active else "warning"
    found: list[AttributeValueFinding] = []
    _collect_attribute_values(template, found, severity, parse_nested=parse_nested, base_index=0)
    return tuple(sorted(found, key=lambda item: (item.start_index, item.end_index)))


def _collect_attribute_values(
    template: Template,
    found: list[AttributeValueFinding],
    severity: Literal["warning", "error"],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> None:
    """Check each static attribute of each HTML element in one template and its nested templates."""
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        tag = node.start_tag.name.content
        # SVG and MathML elements have their own attributes with other values,
        # so their whole subtree is left unchecked.
        if _ascii_lower(tag) in {"svg", "math"}:
            continue
        # Vue resolves only lowercase names as native tags; `<Button>` may be
        # a component, and a custom element or `c-*` tag has its own attributes.
        checked = tag in _HTML_ELEMENTS
        for attr in node.start_tag.attrs:
            if checked:
                finding = _attribute_value_finding(tag, attr, severity, base_index)
                if finding is not None:
                    found.append(finding)
            # A template-valued attribute holds more HTML, whose offsets are
            # relative to the nested source, so shift them into this template.
            inner = attr.inner_value
            if attr.kind == HtmlAttrKind.Template and inner is not None:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    _collect_attribute_values(
                        parsed,
                        found,
                        severity,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                    )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_attribute_values(body, found, severity, parse_nested=parse_nested, base_index=base_index)


def _attribute_value_finding(
    element: str,
    attr: HtmlAttr,
    severity: Literal["warning", "error"],
    base_index: int,
) -> AttributeValueFinding | None:
    """Return a finding for one static attribute whose value its element does not accept."""
    # Template-valued attributes are typed by other checks, and an
    # extension-owned part means the written text is not the rendered value.
    if attr.kind != HtmlAttrKind.Static or attr.foreign_parts:
        return None
    name = attr.key.content
    inner = attr.inner_value
    value = inner.content if inner is not None else ""
    # The browser decodes character references such as `&#116;` before it
    # reads the keyword, with the attribute-value rules, so compare the text
    # it decodes.
    decoded = decode_attribute_entities(value)
    bound = _bound_string_attribute(name, decoded)
    if bound is not None:
        # `:dir="'rlt'"` sets the same text as `dir="rlt"`. The finding marks
        # the whole quoted string, where TypeScript reports a value Vue's
        # types reject, so the editor keeps only this finding.
        name, decoded = bound
        value = decoded
        if not decoded:
            return None
    elif name.startswith((":", "v-bind:", "@", "v-", "#")):
        # Other bindings, listeners, and directives hold an expression.
        return None
    attribute = _ascii_lower(name)
    # The value span sits inside the quotes; an empty or missing value marks the name.
    span = (inner.start_index, inner.end_index) if inner is not None and inner.content else None
    start, end = span if span is not None else (attr.key.start_index, attr.key.end_index)
    boolean_elements = _BOOLEAN_ATTRIBUTES.get(attribute, ())
    if element in boolean_elements or "*" in boolean_elements:
        # A boolean attribute is on whenever it is present. The standard
        # allows only the empty string or the attribute's own name, and any
        # other value, such as "false", still turns it on.
        if not decoded or _ascii_lower(decoded) == attribute:
            return None
        # A bound string is fixed by binding a JavaScript boolean instead,
        # so its message says that rather than how to write the attribute.
        message = render_diagnostic(
            TEMPLATE_INVALID_ATTRIBUTE_VALUE,
            variant="boolean" if bound is None else "boolean-binding",
            value=value,
            attribute=name,
            element=element,
        )
    elif attribute == "name" and element in _FRAME_NAME_ELEMENTS:
        # A frame name may be anything that does not start with "_".
        if not decoded.startswith("_"):
            return None
        message = render_diagnostic(
            TEMPLATE_INVALID_ATTRIBUTE_VALUE,
            variant="frame-name",
            value=value,
            attribute=name,
            element=element,
        )
    elif element in _NAVIGABLE_TARGET_ATTRIBUTES.get(attribute, ()):
        # Any window name is valid, unless it starts with "_" and is not a keyword.
        if not decoded.startswith("_") or _ascii_lower(decoded) in _NAVIGABLE_TARGET_KEYWORDS:
            return None
        message = render_diagnostic(
            TEMPLATE_INVALID_ATTRIBUTE_VALUE,
            variant="target",
            value=value,
            attribute=name,
            element=element,
            allowed=", ".join(_NAVIGABLE_TARGET_KEYWORDS),
        )
    else:
        by_element = _ENUMERATED_ATTRIBUTE_VALUES.get(attribute)
        if by_element is None:
            return None
        allowed = by_element.get(element, by_element.get("*"))
        if allowed is None:
            return None
        exact = _CASE_SENSITIVE_KEYWORDS.get((element, attribute), ())
        if decoded in exact or _ascii_lower(decoded) in {
            _ascii_lower(keyword) for keyword in allowed if keyword not in exact
        }:
            return None
        message = _attribute_value_message(name, element, value, decoded, allowed)
    return AttributeValueFinding(
        element=element,
        attribute=name,
        value=value,
        message=message,
        code=TEMPLATE_INVALID_ATTRIBUTE_VALUE,
        severity=severity,
        start_index=base_index + start,
        end_index=base_index + end,
    )


def _bound_string_attribute(name: str, value: str) -> tuple[str, str] | None:
    """
    Return the attribute name and text of a Vue binding whose value is one JavaScript string.

    ``:dir="'rtl'"`` and ``v-bind:dir="`rtl`"`` set ``dir`` to ``rtl``.
    Returns ``None`` for a binding with a modifier, a dynamic name, an escape
    sequence, or a template literal with a placeholder, because its text is
    not simply the quoted characters.
    """
    for prefix in (":", "v-bind:"):
        if name.startswith(prefix):
            attribute = name.removeprefix(prefix)
            break
    else:
        return None
    if not attribute or "." in attribute or attribute.startswith("["):
        return None
    literal = value.strip()
    if len(literal) < 2 or literal[0] not in "'\"`" or literal[-1] != literal[0]:
        return None
    text = literal[1:-1]
    if literal[0] in text or "\\" in text or "\n" in text or (literal[0] == "`" and "${" in text):
        return None
    return attribute, text


# A typo of a standard pragma is this close to it; a different HTTP header,
# such as `Content-Security-Policy-Report-Only`, is not.
_PRAGMA_SUGGESTION_CUTOFF = 0.8


def _attribute_value_message(
    name: str,
    element: str,
    value: str,
    decoded: str,
    allowed: tuple[str, ...],
) -> str:
    """Render the message for a value outside ``allowed``, naming the closest keyword when one is near."""
    listed = ", ".join(f"'{keyword}'" for keyword in allowed if keyword) + (", or no value" if "" in allowed else "")
    if not decoded:
        return render_diagnostic(
            TEMPLATE_INVALID_ATTRIBUTE_VALUE,
            variant="empty",
            attribute=name,
            element=element,
            allowed=listed,
        )
    # A pragma value is often an HTTP header, such as `Cache-Control`, which
    # browsers ignore in a <meta>; only a near typo gets a suggestion.
    pragma = _ascii_lower(name) == "http-equiv" and element == "meta"
    # Suggest the nearest keyword so a typo such as "treu" names its fix.
    keywords = [keyword for keyword in allowed if keyword]
    nearest = get_close_matches(
        _ascii_lower(decoded),
        [_ascii_lower(keyword) for keyword in keywords],
        n=1,
        cutoff=_PRAGMA_SUGGESTION_CUTOFF if pragma else 0.6,
    )
    if not nearest and pragma:
        return render_diagnostic(
            TEMPLATE_INVALID_ATTRIBUTE_VALUE,
            variant="pragma",
            value=value,
            attribute=name,
            element=element,
            allowed=listed,
        )
    if not nearest:
        return render_diagnostic(
            TEMPLATE_INVALID_ATTRIBUTE_VALUE,
            value=value,
            attribute=name,
            element=element,
            allowed=listed,
        )
    suggestion = next(keyword for keyword in keywords if _ascii_lower(keyword) == nearest[0])
    return render_diagnostic(
        TEMPLATE_INVALID_ATTRIBUTE_VALUE,
        variant="suggestion",
        value=value,
        attribute=name,
        element=element,
        suggestion=suggestion,
        allowed=listed,
    )


def lint_misspelled_directives(
    template: Template,
    consumers: Sequence[MisspelledDirectiveLintConsumer],
    *,
    parse_nested: Callable[[str], Template] = _parse_template,
) -> tuple[MisspelledDirectiveFinding, ...]:
    """
    Report ``c-*`` and ``v-*`` attributes that look like a misspelled directive.

    Citry reads only its fixed directive names, such as ``c-if``. Any other
    ``c-*`` name on an HTML element binds an ordinary attribute, so
    ``<div c-iff="show">`` renders ``<div iff>`` and the element shows up
    whatever ``show`` is. A name is reported when the part after ``c-`` is
    not an HTML attribute that the element accepts and it:

    - is ``if``, ``elif``, ``else``, ``for``, ``empty``, or ``bind`` with
      two neighboring letters swapped (``c-fro``), one letter typed twice
      (``c-iff``), or one letter left out (``c-ele``);
    - is one of those names in other letter case, such as ``c-If``;
    - is a spelled-out ``elif``, such as ``c-else-if``; or
    - is ``show`` or ``model``, directive names from Vue, or ``key`` or
      ``ignore``, which Citry spells ``#c-key`` and ``#c-ignore``.

    An attribute of the element is not reported, in any letter case, so
    ``c-id``, ``c-ID``, ``c-form`` on ``<input>``, and ``c-data-*`` or
    ``c-aria-*`` names pass. ``<c-element>``, whose tag is chosen at render
    time, accepts the attributes of every element. A custom element accepts
    the global attributes and those of a form-associated custom element, and
    because it may define its own, such as ``show``, a name from the last
    bullet is not reported there.

    A replaced letter, or an added letter that is not a double, does not
    count as a typo, because it mostly gives an ordinary word, such as
    ``kind`` for ``bind`` or ``form`` for ``for``. Neither does a missing
    letter that leaves a one-letter name or the word ``or``, ``bid``, or
    ``bin``.
    For ``c-*`` names, component tags, the other ``c-*`` tags, PascalCase Vue
    components, and elements inside ``<svg>`` or ``<math>`` are skipped.

    The rule also reports a ``v-*`` name on any tag outside ``<svg>`` and
    ``<math>``, component tags included, that is one typing slip from a Vue
    built-in directive, such as ``v-iff`` or ``v-shwo``, or a spelled-out
    ``v-else-if``, such as ``v-elif``. Vue reads it as a custom directive,
    and Citry's browser code stops with an error when none of that name is
    registered. Names on or inside an element with ``v-pre`` are skipped,
    because Vue leaves them as written, and no message suggests ``v-once``
    or ``v-memo``, which Citry does not support.

    A finding is reported unless every consumer ignores the rule, and it is an
    error when any reporting consumer says ``"error"``. The check needs no
    component namespace. With an empty ``consumers``, which ``citry check
    --static`` and an editor without project analysis pass for a template
    whose owner they cannot find, findings use the default ``"error"``. An
    attribute that is really meant for the browser can go through
    ``c-bind``, which this rule does not read.

    Args:
        template: Parsed Citry template AST.
        consumers: Every proven component that consumes this physical template.
        parse_nested: Parser for template-valued attributes, so nested
            templates use the same parse options as the outer one.

    Returns:
        Findings in source order, each spanning the attribute name.

    """
    effective = tuple(consumers) or (MisspelledDirectiveLintConsumer(),)
    active = [consumer.rule_misspelled_directive for consumer in effective]
    active = [severity for severity in active if severity != "ignore"]
    if not active:
        return ()
    severity: Literal["warning", "error"] = "error" if "error" in active else "warning"
    found: list[MisspelledDirectiveFinding] = []
    _collect_misspelled_directives(template, found, severity, parse_nested=parse_nested, base_index=0)
    return tuple(sorted(found, key=lambda item: (item.start_index, item.end_index)))


def _collect_misspelled_directives(
    template: Template,
    found: list[MisspelledDirectiveFinding],
    severity: Literal["warning", "error"],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
    vue_skipped: bool = False,
) -> None:
    """
    Check each ``c-*`` and ``v-*`` attribute of each element in one template and its nested templates.

    ``vue_skipped`` is true on and inside an element with ``v-pre``, which
    Vue leaves as written, so its ``v-*`` names are not directives.
    """
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        tag = node.start_tag.name.content
        # SVG and MathML elements have their own attribute names, so their
        # whole subtree is left unchecked.
        if _ascii_lower(tag) in {"svg", "math"}:
            continue
        accepted = _accepted_attribute_names(tag)
        # A custom element defines its own attributes, such as `show` on a
        # disclosure widget, so `show`, `model`, `key`, and `ignore` pass there.
        custom_element = tag not in _HTML_ELEMENTS and tag != "c-element"
        inside_v_pre = vue_skipped or any(_ascii_lower(attr.key.content) == "v-pre" for attr in node.start_tag.attrs)
        for attr in node.start_tag.attrs:
            # Vue reads a `v-*` name as a directive on any tag, components
            # included, so its typos are checked everywhere Vue compiles.
            vue_finding = None if inside_v_pre else _misspelled_vue_directive_finding(attr, severity, base_index)
            if vue_finding is not None:
                found.append(vue_finding)
            if accepted is not None:
                finding = _misspelled_directive_finding(
                    attr,
                    accepted,
                    severity,
                    base_index,
                    custom_element=custom_element,
                )
                if finding is not None:
                    found.append(finding)
            # A template-valued attribute holds more HTML, whose offsets are
            # relative to the nested source, so shift them into this template.
            inner = attr.inner_value
            if attr.kind == HtmlAttrKind.Template and inner is not None:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    _collect_misspelled_directives(
                        parsed,
                        found,
                        severity,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                        vue_skipped=inside_v_pre,
                    )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_misspelled_directives(
                body,
                found,
                severity,
                parse_nested=parse_nested,
                base_index=base_index,
                vue_skipped=inside_v_pre,
            )


def _accepted_attribute_names(tag: str) -> tuple[Collection[str], ...] | None:
    """Return the groups of HTML attribute names one tag accepts, or ``None`` when ``c-*`` names there are inputs."""
    # The groups are returned as they are, without merging them into one
    # set, because most elements have no `c-*` attribute to look up.
    if tag in _HTML_ELEMENTS:
        return _GLOBAL_ATTRIBUTES, _ELEMENT_ATTRIBUTES.get(tag, ())
    if tag == "c-element":
        # The rendered tag is chosen at render time, so any element's
        # attribute may be meant.
        return (_ALL_ELEMENT_ATTRIBUTES,)
    # A custom element is lowercase with a hyphen. Other `c-*` tags are Citry
    # components or built-in tags, whose `c-*` names are inputs, and
    # PascalCase names are Vue components, whose names are props.
    if tag.startswith("c-") or "-" not in tag or tag != _ascii_lower(tag):
        return None
    return _GLOBAL_ATTRIBUTES, _CUSTOM_ELEMENT_ATTRIBUTES


_ALL_ELEMENT_ATTRIBUTES = _GLOBAL_ATTRIBUTES.union(
    _CUSTOM_ELEMENT_ATTRIBUTES,
    *_ELEMENT_ATTRIBUTES.values(),
)


def _misspelled_directive_finding(
    attr: HtmlAttr,
    accepted: tuple[Collection[str], ...],
    severity: Literal["warning", "error"],
    base_index: int,
    *,
    custom_element: bool,
) -> MisspelledDirectiveFinding | None:
    """Return a finding for one ``c-*`` attribute that looks like a directive but renders as an attribute."""
    name = attr.key.content
    # The parser binds only a lowercase `c-` prefix; `C-if` is a static
    # attribute, and an exact directive name is the directive itself.
    if not name.startswith("c-"):
        return None
    attribute = name[2:]
    if attribute in _ELEMENT_DIRECTIVES:
        return None
    lowered = _ascii_lower(attribute)
    # HTML attribute names ignore letter case, so `c-ID` still sets `id`.
    if any(lowered in names for names in accepted) or lowered.startswith(("data-", "aria-")):
        return None
    suggestion = _directive_suggestion(lowered, custom_element=custom_element)
    if suggestion is None:
        return None
    target, variant = suggestion
    return MisspelledDirectiveFinding(
        name=name,
        suggestion=target,
        message=render_diagnostic(
            TEMPLATE_MISSPELLED_DIRECTIVE,
            variant=variant,
            name=name,
            attribute=attribute,
            suggestion=target,
        ),
        code=TEMPLATE_MISSPELLED_DIRECTIVE,
        severity=severity,
        start_index=base_index + attr.key.start_index,
        end_index=base_index + attr.key.end_index,
    )


def _directive_suggestion(
    lowered: str,
    *,
    custom_element: bool,
) -> tuple[str, Literal["default", "vue"]] | None:
    """
    Return the directive a lowercased ``c-*`` suffix most likely meant, with its message variant.

    On a custom element, ``show``, ``model``, ``key``, and ``ignore`` may be
    the element's own attributes, so only typos, other letter case, and a
    spelled-out ``elif`` are reported there.
    """
    if lowered in _SPELLED_OUT_ELIF:
        return "c-elif", "default"
    if lowered in _FOREIGN_DIRECTIVES:
        return None if custom_element else _FOREIGN_DIRECTIVES[lowered]
    # A name in other letter case, such as `If`, equals the directive here,
    # so the same loop finds it. The first directive in the list wins a tie,
    # which keeps the suggestion stable.
    for directive in _ELEMENT_DIRECTIVES:
        if lowered == directive or _is_directive_typo(lowered, directive):
            return f"c-{directive}", "default"
    return None


# Vue's built-in directives, as written after `v-`, in the order a tie
# between two suggestions is broken. `v-is` is left out: the parser rejects it.
_VUE_DIRECTIVES = (
    "if",
    "else-if",
    "else",
    "for",
    "show",
    "model",
    "bind",
    "on",
    "slot",
    "html",
    "text",
    "once",
    "memo",
    "cloak",
    "pre",
)
# Vue directives Citry rejects in templates, so no message suggests them.
_UNSUPPORTED_VUE_DIRECTIVES = frozenset({"once", "memo"})
# Spellings an author brings from other languages for `v-else-if`.
_SPELLED_OUT_VUE_ELSE_IF = frozenset({"elif", "elseif", "elsif", "else_if"})


def _misspelled_vue_directive_finding(
    attr: HtmlAttr,
    severity: Literal["warning", "error"],
    base_index: int,
) -> MisspelledDirectiveFinding | None:
    """
    Return a finding for a ``v-*`` name that looks like a misspelled Vue directive.

    Vue reads any other ``v-*`` name as a custom directive, so ``v-iff``
    makes Vue look up a directive named ``iff``, and Citry's browser code
    stops with an error when none is registered. A built-in name in other letter case, such as ``v-If``, is a parse
    error already; ``v-IFF`` is not, because ``iff`` is not built in.
    """
    name = attr.key.content
    if not name.startswith("v-"):
        return None
    # The argument and modifiers, as in `v-on:click.stop`, do not change
    # which directive the name selects.
    directive = name[2:].split(":", 1)[0].split(".", 1)[0]
    lowered = _ascii_lower(directive)
    if not lowered or lowered in _VUE_DIRECTIVES:
        return None
    if lowered in _SPELLED_OUT_VUE_ELSE_IF:
        suggestion = "else-if"
    else:
        suggestion = next(
            (
                item
                for item in _VUE_DIRECTIVES
                if item not in _UNSUPPORTED_VUE_DIRECTIVES and _is_directive_typo(lowered, item)
            ),
            "",
        )
        if not suggestion:
            return None
    target = f"v-{suggestion}"
    return MisspelledDirectiveFinding(
        name=name,
        suggestion=target,
        message=render_diagnostic(
            TEMPLATE_MISSPELLED_DIRECTIVE,
            variant="vue-directive",
            name=name,
            suggestion=target,
        ),
        code=TEMPLATE_MISSPELLED_DIRECTIVE,
        severity=severity,
        start_index=base_index + attr.key.start_index,
        end_index=base_index + attr.key.end_index,
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
        if (
            reference.name in COMPONENT_JS_AMBIENT_NAMES
            or reference.name in _COMPONENT_JS_BROWSER_GLOBALS
            or _DOM_INTERFACE.fullmatch(reference.name)
        ):
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


_JSON_OBJECT_MEMBERS = frozenset(
    {
        "constructor",
        "__defineGetter__",
        "__defineSetter__",
        "hasOwnProperty",
        "__lookupGetter__",
        "__lookupSetter__",
        "isPrototypeOf",
        "propertyIsEnumerable",
        "toString",
        "valueOf",
        "__proto__",
        "toLocaleString",
    }
)


def lint_unknown_component_js_members(
    source: str,
    known_data_names: frozenset[str] | None,
    *,
    severity: Literal["ignore", "warning", "error"] = "error",
) -> tuple[ComponentJsLintFinding, ...]:
    """
    Report `this.<name>` and `component.<name>` reads the component instance lacks.

    The JavaScript analyzer proves which reads target the live Vue instance:
    `this.<name>` in Vue Options methods, computed values, `data()`, lifecycle
    hooks, `provide()`, and `watch` handlers, and `component.<name>` in an
    `onServerRender` or `init` callback. Each name must then be a
    `js_data()` key or a name the Vue Options declare (props, `data()`, `setup`,
    methods, computed values, injections).

    Args:
        source: Authored component JavaScript.
        known_data_names: `js_data()` keys available to every owning component,
            or None when that namespace is open or cannot be established.
        severity: The `rule_unknown_component_js_member` severity that applies
            to this source. `"ignore"` reports nothing.

    Returns:
        Findings at the given severity for unknown member names, in source
        order. Nothing is reported when the source is invalid, when any Vue
        Options section cannot be read statically, or when the source may add
        members at run time.

    Raises:
        ValueError: If `severity` is not `"ignore"`, `"warning"`, or `"error"`.

    """
    if severity not in {"ignore", "warning", "error"}:
        msg = f"Unknown component-JavaScript-member rule severity: {severity!r}"
        raise ValueError(msg)
    # An ignored rule skips the source analysis, not only the findings.
    if known_data_names is None or severity == "ignore":
        return ()
    reported: Literal["warning", "error"] = "warning" if severity == "warning" else "error"
    analysis = analyze_browser_component_source(source)
    # An Options section built at run time (a spread, a computed data() result)
    # can declare any name, so no missing name can be proven.
    if not analysis.valid or any(section.state == "unknown" for section in analysis.sections):
        return ()
    assigned = _assigned_instance_member_names(source, analysis)
    if assigned is None:
        return ()
    known = (
        known_data_names
        | {item.exposed_name for item in analysis.public_names}
        | assigned
        | _RUNTIME_INSTANCE_MEMBERS
        | _JSON_OBJECT_MEMBERS
    )
    findings: dict[tuple[int, int], ComponentJsLintFinding] = {}
    for member in analysis.member_references:
        # Vue's own instance API and every extension's instance helper start
        # with $ or _, and plugins can add them, so they are never "unknown".
        if member.name.startswith(("$", "_")) or member.name in known:
            continue
        findings[(member.start_index, member.end_index)] = ComponentJsLintFinding(
            name=member.name,
            message=render_diagnostic(COMPONENT_JS_UNKNOWN_MEMBER, name=member.name),
            code=COMPONENT_JS_UNKNOWN_MEMBER,
            severity=reported,
            start_index=member.start_index,
            end_index=member.end_index,
        )
    return tuple(findings[span] for span in sorted(findings))


# Citry adds this prop to every component itself, so authored Options never
# declare it.
_RUNTIME_INSTANCE_MEMBERS = frozenset({"citryId"})


def lint_undeclared_component_js_emits(source: str) -> tuple[ComponentJsLintFinding, ...]:
    """
    Report `this.$emit('name')` and `component.$emit('name')` calls for undeclared events.

    Vue checks emitted names against the component's `emits` option, and
    accepts a name that matches a declared `on<Event>` prop too. Only calls
    whose receiver the analyzer proves is the live instance, with a string
    literal event name, are checked.

    Args:
        source: Authored component JavaScript.

    Returns:
        Error findings spanning each undeclared event name, in source order.
        Nothing is reported when the component declares no `emits` (Vue then
        accepts every name) or builds `emits` in a way the analyzer cannot read.

    """
    analysis = analyze_browser_component_source(source)
    if analysis.declared_events is None:
        return ()
    spans = frozenset(
        (member.start_index, member.end_index) for member in analysis.member_references if member.name == "$emit"
    )
    return tuple(
        ComponentJsLintFinding(
            name=call.value,
            message=render_diagnostic(BROWSER_UNDECLARED_EMIT, name=call.value),
            code=BROWSER_UNDECLARED_EMIT,
            severity="error",
            start_index=call.start_index,
            end_index=call.end_index,
        )
        for call in browser_proven_member_literal_calls(source, spans)
        if not _emit_is_declared(call.value, analysis)
    )


def lint_undeclared_template_emits(
    expressions: Sequence[BrowserExpression],
    component_sources: Sequence[str],
) -> tuple[VueLintFinding, ...]:
    """
    Report `$emit('name')` calls in Vue expressions for events the component does not declare.

    Args:
        expressions: The Vue expressions of one template.
        component_sources: The JavaScript of every component that renders the
            template. An expression runs in each of them, so a name must be
            declared by all of them.

    Returns:
        Error findings spanning each undeclared event name. Nothing is reported
        when any component declares no `emits`, or builds it in a way the
        analyzer cannot read, since that component accepts every name.

    """
    analyses = [analyze_browser_component_source(source) for source in component_sources]
    if not analyses or any(analysis.declared_events is None for analysis in analyses):
        return ()
    findings: list[VueLintFinding] = []
    for expression in expressions:
        # A `v-for` or slot binding named `$emit` is not Vue's `$emit`.
        if expression.host != "vue" or "$emit" in expression.bindings:
            continue
        findings.extend(
            VueLintFinding(
                name=call.value,
                message=render_diagnostic(BROWSER_UNDECLARED_EMIT, name=call.value),
                code=BROWSER_UNDECLARED_EMIT,
                severity="error",
                start_index=call.start_index,
                end_index=call.end_index,
            )
            for call in browser_literal_calls(expression, frozenset({"$emit"}))
            if not all(_emit_is_declared(call.value, analysis) for analysis in analyses)
        )
    return tuple(findings)


def lint_undeclared_component_listeners(
    expressions: Sequence[BrowserExpression],
    child_source: Callable[[str], str | None],
    *,
    severities: Sequence[Literal["ignore", "warning", "error"]] = (),
) -> tuple[VueLintFinding, ...]:
    """
    Report listeners on child component tags for events the child does not declare.

    Vue turns `@drop-task` on a component into an `onDropTask` listener and
    matches it against the child's `emits` in camelCase or kebab-case, or
    against an `on<Event>` prop. A listener the child does not declare is
    passed to the child's root element as a DOM listener instead, where it
    fires only if that element dispatches a DOM event with this name, so a
    misspelled event name goes unnoticed. A plain lowercase name, such as
    `hdie`, is reported only when it is not a DOM event such as `click`,
    which the child's root element may fire. When the name is one typing
    slip from a declared event, the message suggests that event.

    Args:
        expressions: The Vue expressions of one template.
        child_source: Return the JavaScript of the component a `c-*` tag
            renders, or None when the tag resolves to no component with
            readable JavaScript.
        severities: ``rule_undeclared_component_event`` of every component
            that renders the template. A finding is reported unless all of
            them ignore the rule, and it is an error when any says
            ``"error"``. With none, findings are warnings.

    Returns:
        Findings spanning each listener's attribute name.

    """
    active = [severity for severity in (severities or ("warning",)) if severity != "ignore"]
    if not active:
        return ()
    severity: Literal["warning", "error"] = "error" if "error" in active else "warning"
    sources: dict[str, BrowserComponentSourceAnalysis | None] = {}
    findings: list[VueLintFinding] = []
    for expression in expressions:
        element = expression.element
        event = component_listener_event(expression)
        if element is None or event is None or expression.attribute_start_index is None:
            continue
        if element not in sources:
            source = child_source(element)
            sources[element] = None if source is None else analyze_browser_component_source(source)
        analysis = sources[element]
        if analysis is None or analysis.declared_events is None:
            continue
        # The child's root element may fire a DOM event such as `click`, and
        # Vue passes the listener there, so a DOM event name is not a typo.
        if event in _DOM_EVENT_NAMES:
            continue
        if _listener_is_declared(event, analysis):
            continue
        suggestion = _declared_event_suggestion(event, analysis)
        findings.append(
            VueLintFinding(
                name=event,
                message=(
                    render_diagnostic(BROWSER_UNDECLARED_COMPONENT_EVENT, name=event, component=element)
                    if suggestion is None
                    else render_diagnostic(
                        BROWSER_UNDECLARED_COMPONENT_EVENT,
                        variant="suggestion",
                        name=event,
                        component=element,
                        suggestion=suggestion,
                    )
                ),
                code=BROWSER_UNDECLARED_COMPONENT_EVENT,
                severity=severity,
                start_index=expression.attribute_start_index,
                end_index=expression.attribute_end_index or expression.attribute_start_index,
            )
        )
    return tuple(findings)


def _declared_event_suggestion(event: str, analysis: BrowserComponentSourceAnalysis) -> str | None:
    """Return the declared event one typing slip from a listener's name, written the way the listener writes it."""
    declared = analysis.declared_events or ()
    # A listener in kebab-case is compared with each event's kebab-case form,
    # so `@drop-tsak` finds `dropTask` and suggests `drop-task`.
    hyphenated = "-" in event or event == event.lower()
    for item in declared:
        candidate = _vue_hyphenate(item.name) if hyphenated else item.name
        if one_slip_from(event, candidate):
            return candidate
    return None


# An assignment or update right after a name, as in `open = false`,
# `count += 1`, or `count++`. `==`, `===`, and `=>` are not assignments.
_WRITE_AFTER_NAME = re.compile(rb"\s*(?:(?:\*\*|<<|>>>?|&&|\|\||\?\?|[-+*/%&|^])?=(?![=>])|\+\+|--)")
# An update right before a name, as in `++count`, possibly through `this.`.
_UPDATE_BEFORE_NAME = re.compile(rb"(?:\+\+|--)\s*(?:[A-Za-z_$][\w$]*\s*\.\s*)?$")


def _declared_prop_names(source: str) -> frozenset[str] | None:
    """Return the props a component's JavaScript declares, or None when its source cannot be read."""
    analysis = analyze_browser_component_source(source)
    if not analysis.valid:
        return None
    return frozenset(item.exposed_name for item in analysis.public_names if item.origin == "props")


def _writes_name(source: bytes, start: int, end: int) -> bool:
    """Return whether the name at ``source[start:end]`` is assigned or updated there."""
    if _WRITE_AFTER_NAME.match(source, end):
        return True
    update = _UPDATE_BEFORE_NAME.search(source[:start])
    # `++` or `--` right after a value, as in `a--` before a line break, ends
    # that value's expression, so it does not update the name that follows.
    return update is not None and not re.search(rb"[\w$)\]]\s*$", source[: update.start()])


def lint_prop_assignments(
    expressions: Sequence[BrowserExpression],
    component_sources: Sequence[str],
    *,
    severities: Sequence[Literal["ignore", "warning", "error"]] = (),
) -> tuple[VueLintFinding, ...]:
    """
    Report Vue expressions in a component's template that assign to one of its own props.

    Vue props are read-only: `@click="open = false"` in the component that
    receives `open` leaves the value unchanged and only logs a warning in
    the browser. This reports an assignment (`=`, `+=`, and the other
    assignment operators), an update (`++`, `--`), and `v-model` bound to a
    prop. A write to a field of an object prop, such as `open.count = 1`, is
    allowed by Vue and not reported, and neither is a name that an enclosing
    `v-for` or slot binds.

    Args:
        expressions: The Vue expressions of one template.
        component_sources: The JavaScript of every component that renders
            the template. A name is reported only when every one of them
            declares it as a prop.
        severities: ``rule_prop_assignment`` of every component that renders
            the template. A finding is reported unless all of them ignore
            the rule, and it is an error when any says ``"error"``. With
            none, findings are errors.

    Returns:
        Findings spanning each written name.

    """
    active = [severity for severity in (severities or ("error",)) if severity != "ignore"]
    if not active or not component_sources:
        return ()
    severity: Literal["warning", "error"] = "error" if "error" in active else "warning"
    declared = [_declared_prop_names(source) for source in component_sources]
    # A source the analyzer cannot read may not declare the name as a prop.
    if any(names is None for names in declared):
        return ()
    props = frozenset.intersection(*(names for names in declared if names is not None))
    if not props:
        return ()
    findings: list[VueLintFinding] = []
    for expression in expressions:
        # Only a Vue expression written as authored maps its offsets one to
        # one; the arguments of a server call are sent, not evaluated here.
        if expression.host != "vue" or expression.transform not in {"identity", "v-model"}:
            continue
        if expression.transform == "v-model":
            name = expression.source.strip()
            if name in props and name not in expression.bindings:
                findings.append(_prop_assignment_finding(name, expression, severity, variant="v-model"))
            continue
        encoded = expression.source.encode("utf-8")
        for reference in analyze_browser_expression(expression).references:
            if reference.name not in props or reference.name in expression.bindings:
                continue
            start = reference.start_index - expression.start_index
            end = reference.end_index - expression.start_index
            if _writes_name(encoded, start, end):
                findings.append(
                    VueLintFinding(
                        name=reference.name,
                        message=render_diagnostic(BROWSER_PROP_ASSIGNMENT, name=reference.name),
                        code=BROWSER_PROP_ASSIGNMENT,
                        severity=severity,
                        start_index=reference.start_index,
                        end_index=reference.end_index,
                    )
                )
    return tuple(findings)


def _prop_assignment_finding(
    name: str,
    expression: BrowserExpression,
    severity: Literal["warning", "error"],
    *,
    variant: str,
) -> VueLintFinding:
    return VueLintFinding(
        name=name,
        message=render_diagnostic(BROWSER_PROP_ASSIGNMENT, variant=variant, name=name),
        code=BROWSER_PROP_ASSIGNMENT,
        severity=severity,
        start_index=expression.start_index,
        end_index=expression.end_index,
    )


def lint_component_js_prop_assignments(
    source: str,
    *,
    severities: Sequence[Literal["ignore", "warning", "error"]] = (),
) -> tuple[VueLintFinding, ...]:
    """
    Report component JavaScript that assigns to one of the component's own props, such as `this.open = false`.

    Only a write through `this` or the `$component` context counts, because
    the analyzer proves those receivers are the component. The operator
    after the name is read from the text, so a finding is at most a warning,
    even when the rule says ``"error"``.

    Args:
        source: The component's JavaScript.
        severities: ``rule_prop_assignment`` of every component that runs
            this JavaScript, combined as for ``lint_prop_assignments``.

    Returns:
        Warning findings spanning each written prop name.

    """
    active = [severity for severity in (severities or ("error",)) if severity != "ignore"]
    if not active:
        return ()
    analysis = analyze_browser_component_source(source)
    if not analysis.valid:
        return ()
    props = frozenset(item.exposed_name for item in analysis.public_names if item.origin == "props")
    encoded = source.encode("utf-8")
    return tuple(
        VueLintFinding(
            name=reference.name,
            message=render_diagnostic(BROWSER_PROP_ASSIGNMENT, name=reference.name),
            code=BROWSER_PROP_ASSIGNMENT,
            severity="warning",
            start_index=reference.start_index,
            end_index=reference.end_index,
        )
        for reference in analysis.member_references
        if reference.name in props and _writes_name(encoded, reference.start_index, reference.end_index)
    )


@dataclass(frozen=True, slots=True)
class CssVariableFinding:
    """One ``var(--name)`` in component CSS that looks like a misspelled ``css_data()`` key."""

    name: str
    suggestion: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int


# A custom property the CSS sets itself, as in `--accent: red`.
_CSS_CUSTOM_PROPERTY_DECLARATION = re.compile(r"(?<![\w-])--([\w-]+)\s*:")


def lint_misspelled_css_variables(
    source: str,
    keys: Collection[str],
    *,
    severity: Literal["ignore", "warning", "error"] = "warning",
) -> tuple[CssVariableFinding, ...]:
    """
    Report ``var(--name)`` in a component's CSS that is one typing slip from a ``css_data()`` key.

    Citry sets one custom property per ``css_data()`` key, named after the
    key. When a ``var()`` names a property nothing sets, the browser ignores
    the declaration without an error: the property inherits from the parent
    element or takes its initial value.
    Only a name one typing slip from a key is reported, because a site
    stylesheet or a parent component may set any other property. A ``var()``
    with a fallback, and a property the same CSS sets itself, are left alone.

    Args:
        source: The component's own CSS.
        keys: Every key the component's ``css_data()`` or ``CssData`` returns.
            Pass them only when the full set is known.
        severity: ``rule_misspelled_css_variable``.

    Returns:
        Findings spanning each ``--name``, in source order.

    """
    if severity == "ignore" or not keys:
        return ()
    # Comments are blanked so a commented-out declaration does not count.
    uncommented = re.sub(r"/\*.*?\*/", lambda match: " " * len(match.group(0)), source, flags=re.DOTALL)
    declared = {match.group(1) for match in _CSS_CUSTOM_PROPERTY_DECLARATION.finditer(uncommented)}
    boundaries = _utf8_boundaries(source)
    findings: list[CssVariableFinding] = []
    for name, start, end, terminated in _css_var_arguments(source):
        # `var(--x, fallback)` still has a value, and an unterminated or
        # escaped argument is not one Citry reads exactly.
        if not name or not terminated or name in keys or name in declared:
            continue
        after = _skip_css_trivia(source, end)
        if source[after : after + 1] != ")":
            continue
        suggestion = next((key for key in sorted(keys) if one_slip_from(name, key)), None)
        if suggestion is None:
            continue
        findings.append(
            CssVariableFinding(
                name=name,
                suggestion=suggestion,
                message=render_diagnostic(CSS_MISSPELLED_VARIABLE, name=name, suggestion=suggestion),
                code=CSS_MISSPELLED_VARIABLE,
                severity=severity,
                start_index=boundaries[start],
                end_index=boundaries[end],
            )
        )
    return tuple(findings)


def component_listener_event(expression: BrowserExpression) -> str | None:
    """
    Return the event name of a `@name` or `v-on:name` listener on a component tag.

    Citry server events (`@c-*`), dynamic names (`@[name]`), native tags, and
    Citry's structural tags have no child `emits` to check.
    """
    element = expression.element
    if (
        expression.mode != "statement"
        or element is None
        or not element.startswith("c-")
        or element == "c-element"
        or element in RESERVED_TAG_NAMES
    ):
        return None
    attribute = expression.attribute
    if attribute.startswith("@"):
        raw = attribute[1:]
    elif attribute.lower().startswith("v-on:"):
        raw = attribute[len("v-on:") :]
    else:
        return None
    # `@vue:mounted` and the other `vue:` names are Vue's own vnode lifecycle
    # hooks, which a component never emits.
    if not raw or raw.startswith(("[", "c-", "vue:")):
        return None
    # Modifiers such as `.once` or `.stop` do not change which event is heard.
    return raw.split(".", 1)[0] or None


def _vue_camelize(name: str) -> str:
    """Camelize the way Vue does: `drop-task` becomes `dropTask`."""
    return re.sub(r"-(\w)", lambda match: match.group(1).upper(), name)


def _vue_hyphenate(name: str) -> str:
    """Hyphenate the way Vue does: `dropTask` becomes `drop-task`."""
    return re.sub(r"\B([A-Z])", r"-\1", name).lower()


def _emit_is_declared(name: str, analysis: BrowserComponentSourceAnalysis) -> bool:
    """
    Whether Vue accepts `$emit(name)` without a missing-declaration warning.

    Vue looks the name up exactly in `emits`, or accepts an `on<Event>` prop
    for its camelized form.
    """
    declared = analysis.declared_events
    if declared is None or name in {event.name for event in declared}:
        return True
    camel = _vue_camelize(name)
    handler = f"on{camel[:1].upper()}{camel[1:]}"
    return any(item.origin == "props" and item.exposed_name == handler for item in analysis.public_names)


def vue_listener_event_names(event: str) -> tuple[str, str, str]:
    """
    Return the `emits` names Vue accepts for one listener on a component tag.

    Vue compiles `@drop-task` to an `onDropTask` prop and its `isEmitListener`
    then looks for `dropTask`, `drop-task`, and `DropTask` in `emits`.
    """
    camel = _vue_camelize(event)
    key = camel[:1].upper() + camel[1:]
    return (key[:1].lower() + key[1:], _vue_hyphenate(key), key)


def _listener_is_declared(event: str, analysis: BrowserComponentSourceAnalysis) -> bool:
    """
    Match a parent's listener name to the child's `emits` as Vue's `isEmitListener` does.

    A child may also take the listener as an `on<Event>` prop, which Vue
    binds to the prop instead of passing it on.
    """
    declared = analysis.declared_events
    if declared is None:
        return True
    names: tuple[str, ...] = vue_listener_event_names(event)
    # Vue strips a trailing `Once` before the lookup, as for `.once`.
    if names[2].endswith("Once") and len(names[2]) > len("Once"):
        names = (*names, *vue_listener_event_names(names[2][: -len("Once")]))
    if set(names) & {item.name for item in declared}:
        return True
    handler = f"on{names[2]}"
    return any(item.origin == "props" and item.exposed_name == handler for item in analysis.public_names)


# A property write such as `this.timer = ...` or `vm.count += 1`. Vue lets code
# add plain properties to an instance this way, so a later read is not a typo.
_PROPERTY_WRITE = re.compile(
    r"\.\s*([A-Za-z_$][\w$]*)\s*(?:(?:\*\*|<<|>>>?|&&|\|\||\?\?|[-+*/%&|^])?=(?![=>])|\+\+|--)"
)
_PROPERTY_PREFIX_UPDATE = re.compile(r"(?:\+\+|--)\s*[\w$.]*\.\s*([A-Za-z_$][\w$]*)")
# A member used as a `for` target, as in `for (this.key of keys)`.
_PROPERTY_FOR_TARGET = re.compile(r"\bfor\s*\([^;)]*?\.\s*([A-Za-z_$][\w$]*)\s+(?:of|in)\b")
# A member name inside a destructuring pattern.
_PATTERN_MEMBER = re.compile(r"\.\s*([A-Za-z_$][\w$]*)")
# Calls that can add arbitrary properties to their first argument.
_BULK_PROPERTY_WRITE = re.compile(
    r"\b(?:Object\s*\.\s*(?:assign|defineProperty|defineProperties)|Reflect\s*\.\s*(?:set|defineProperty))\s*\(\s*"
    r"([A-Za-z_$][\w$]*)"
)


def _assigned_instance_member_names(
    source: str,
    analysis: BrowserComponentSourceAnalysis,
) -> frozenset[str] | None:
    """
    Collect property names the source writes, or None when writes are unbounded.

    This reads the source text rather than resolving receivers, so it also
    counts writes to unrelated objects. Over-counting only skips findings, which
    keeps the rule from reporting a member the component really adds.
    """
    # A class body gives `this` a different meaning that the analyzer does not
    # separate from the component, so nothing about `this` can be proven.
    if re.search(r"\bclass\b", source):
        return None
    names = {match.group(1) for match in _PROPERTY_WRITE.finditer(source)}
    names.update(match.group(1) for match in _PROPERTY_PREFIX_UPDATE.finditer(source))
    names.update(match.group(1) for match in _PROPERTY_FOR_TARGET.finditer(source))
    # `[this.x] = pair` and `({ a: this.y } = obj)` write every member named
    # inside the pattern. A `const`/`let`/`var` pattern only declares locals.
    destructuring: list[tuple[int, int]] = []
    for match in re.finditer(rf"[}}\]]\s*{_ASSIGNMENT_OPERATOR}", source):
        opening = _matching_opening_bracket(source, match.start())
        if opening is None:
            return None
        if re.search(r"\b(?:const|let|var)\s*$", source[:opening]):
            continue
        destructuring.append((opening, match.start()))
        names.update(member.group(1) for member in _PATTERN_MEMBER.finditer(source, opening, match.start()))
    component_names = {binding.local_name for binding in analysis.bindings if binding.name == "component"}
    # A local copy (`const self = this`) is the same instance under another name.
    aliases = {
        match.group(1)
        for match in re.finditer(r"([A-Za-z_$][\w$]*)\s*=\s*(this|[A-Za-z_$][\w$]*)\s*[;,\n)]", source)
        if match.group(2) == "this" or match.group(2) in component_names
    }
    instance = "|".join(re.escape(name) for name in sorted({"this"} | component_names | aliases))
    # `Object.assign(this, ...)` or `this[key] = value` can add names the text
    # never spells out.
    if any(match.group(1) in {"this"} | component_names | aliases for match in _BULK_PROPERTY_WRITE.finditer(source)):
        return None
    if re.search(rf"(?<![\w$.])(?:{instance})\s*(?:\?\.)?\s*\[[^\]]*\]\s*{_ASSIGNMENT_OPERATOR}", source):
        return None
    # A reassigned callback parameter no longer holds the component, so its
    # members say nothing about the instance. That includes a destructuring
    # assignment such as `({ component } = next)`; a `const`/`let`/`var`
    # declaration pattern creates a new variable instead, so it is skipped.
    for name in component_names:
        if re.search(rf"(?<![\w$.]){re.escape(name)}\s*{_ASSIGNMENT_OPERATOR}", source):
            return None
        for opening, closing in destructuring:
            if re.search(rf"(?<![\w$.]){re.escape(name)}(?![\w$])", source[opening:closing]):
                return None
    return frozenset(names)


def _matching_opening_bracket(source: str, closing: int) -> int | None:
    """Return the index of the bracket that `source[closing]` closes, if any."""
    pairs = {"}": "{", "]": "["}
    stack: list[str] = []
    for index in range(closing, -1, -1):
        character = source[index]
        if character in pairs:
            stack.append(pairs[character])
        elif character in "{[":
            # A mismatched bracket means strings or comments confused the
            # count, so the caller must not trust the result.
            if not stack or stack.pop() != character:
                return None
            if not stack:
                return index
    return None


# `=` or a compound assignment such as `+=`, but not `==`, `===`, or `=>`.
_ASSIGNMENT_OPERATOR = r"(?:(?:\*\*|<<|>>>?|&&|\|\||\?\?|[-+*/%&|^])?=(?![=>]))"


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


def template_static_input_queries(
    template: object,
    *,
    parse_nested: Callable[[str], object] = _parse_template,
) -> tuple[TemplatePythonQuery, ...]:
    """
    Return a query for each quoted static attribute on a ``c-*`` component tag.

    The quoted text is a Python string literal with the value the child
    component receives, so it can be checked against the child's input type.

    Args:
        template: Parsed Citry template AST.
        parse_nested: Parser used for nested-template attribute values.

    Returns:
        Queries ordered by their authored source position.

    """
    return _template_static_input_queries(template, parse_nested=parse_nested)


def build_inferred_template_shadow(
    module_source: str,
    class_qualname: str,
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    source_module: str | None = None,
    source_is_package: bool = False,
    kwargs_type: tuple[str, str] | None = None,
    value_type: TemplatePythonValueType | None = None,
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
        value_type: Optional type the query's value must have, such as the
            child component input a ``c-*`` value sets.

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
        value_type=value_type,
    )


def build_schema_template_shadow(
    module_source: str,
    schema_qualname: str,
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    source_module: str | None = None,
    source_is_package: bool = False,
    value_type: TemplatePythonValueType | None = None,
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
        value_type: Optional type the query's value must have, such as the
            child component input a ``c-*`` value sets.

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
        value_type=value_type,
    )


def build_reveal_shadow(
    module_source: str,
    spans: tuple[tuple[int, int], ...],
    *,
    source_module: str | None = None,
    source_is_package: bool = False,
) -> ShadowRevealDocument | None:
    """
    Copy one module so a type checker states the type of chosen expressions.

    Args:
        module_source: Current Python module source.
        spans: Start and end string offsets of whole, non-overlapping
            expressions in ``module_source``.
        source_module: Importable module name used to mirror relative imports.
        source_is_package: Whether that module is implemented by ``__init__.py``.

    Returns:
        The copy with each expression wrapped in ``reveal_type()`` and the
        offsets of each wrapped expression, or ``None`` when the module
        cannot be copied that way.

    """
    return _build_reveal_shadow(
        module_source,
        spans,
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
        """Rebuild a snapshot from the data that ``to_dict()`` returned."""
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
    _utf16_prefix: array[int]
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
        "_utf16_prefix",
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
        utf16_prefix = array("I" if len(host_source) <= 0x7FFFFFFF else "Q", [0])
        for char in host_source:
            utf16_prefix.append(utf16_prefix[-1] + (2 if ord(char) > 0xFFFF else 1))
        object.__setattr__(source_map, "_utf16_prefix", utf16_prefix)
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

    def _position_at(self, offset: int) -> LspPosition:
        line = bisect_right(self._line_starts, offset) - 1
        return LspPosition(line, self._utf16_prefix[offset] - self._utf16_prefix[self._line_starts[line]])

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

        assignment_indent = _line_indent_at(self._host_source, part.literal_start)
        has_canonical_multiline_framing = (
            len(part.delimiter) == 3 and formatted.startswith("\n") and formatted.endswith(f"\n{assignment_indent}")
        )
        if self._normalization_changed or has_canonical_multiline_framing:
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
        """Indent multiline triple-string asset content relative to its assignment."""
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
            start=self._position_at(host_start),
            end=self._position_at(host_end),
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
    """
    One definite direct literal template on a Citry component class.

    Attributes:
        component_name: Name of the class that declares the template.
        source_map: Maps template offsets back to the Python source.
        owner_lint: The ``Lint`` severities read from the source of each
            class in the module that renders this template: the declaring
            class, and each subclass with that one component base that sets
            neither ``template`` nor ``template_file`` and keeps native Citry
            as the template language. Empty when the classes cannot be read,
            as for a template in Python that does not parse yet.

    """

    component_name: str
    source_map: PythonTemplateSourceMap
    owner_lint: tuple[ComponentSourceLint, ...] = ()


@dataclass(frozen=True, slots=True)
class PythonTemplateNotice:
    """One definite component template skipped for an explicit reason."""

    component_name: str
    message: str


@dataclass(frozen=True, slots=True)
class UntracedComponentTemplate:
    """
    One class with a literal template whose base class comes from another module of the project.

    The class may well be a component, but nothing in its own file proves
    it, so tools that read files one at a time do not check its template.

    Attributes:
        component_name: The class name.
        base: The imported class it extends, directly or through a class
            in the same file, as written, such as ``BaseCard``.
        line: The 1-based line of the class name.
        start_column: The character in that line where the class name starts.
        end_column: The character in that line where the class name ends.

    """

    component_name: str
    base: str
    line: int
    start_column: int
    end_column: int


def discover_untraced_component_templates(
    source: str,
    *,
    is_project_module: Callable[[str, int], bool],
    app_components: Mapping[str, bool] | None = None,
) -> tuple[UntracedComponentTemplate, ...]:
    """
    Find classes that set a literal template but whose component base Citry cannot see from this file.

    A class counts when it sits at module level, sets ``template`` to a
    string literal that contains a tag, is not proven to be a Citry
    component, and one of its bases is imported from a module of the
    project, directly or through a base class defined in the same file.
    A base from an installed package, such as another framework's
    ``Component``, does not count. A base written as ``module.Name`` is not
    followed.

    Args:
        source: The Python source of one file.
        is_project_module: Return whether ``from <module> import ...`` with
            the given module name and number of leading dots imports a
            module of the project.
        app_components: The classes a loaded application registers as
            components, as passed to
            [`discover_python_templates`][citry.discover_python_templates].
            Discovery finds their templates, so they are not reported.

    Returns:
        The classes in source order. Empty when the source does not parse.

    """
    try:
        module = ast.parse(source)
    except (SyntaxError, ValueError):
        return ()
    proven = {
        declaration.name
        for declaration, _language in _ast_component_declarations(module, app_components=app_components)
    }
    imported: dict[str, tuple[str, int]] = {}
    classes: dict[str, ast.ClassDef] = {}
    found: list[UntracedComponentTemplate] = []
    # Lines are counted as Python's parser counts them, like `lineno`.
    lines = source_lines(source)
    for statement in module.body:
        if isinstance(statement, ast.ImportFrom):
            for alias in statement.names:
                imported[alias.asname or alias.name] = (statement.module or "", statement.level)
            continue
        if not isinstance(statement, ast.ClassDef):
            continue
        classes[statement.name] = statement
        if statement.name in proven or not _sets_markup_template(statement):
            continue
        base = _project_base(statement, imported, classes, is_project_module, seen=set())
        if base is None:
            continue
        line = lines[statement.lineno - 1] if statement.lineno <= len(lines) else ""
        # The class name follows `class` on the statement's first line.
        match = re.search(rf"\bclass\s+({re.escape(statement.name)})\b", line)
        start = match.start(1) if match else 0
        found.append(
            UntracedComponentTemplate(statement.name, base, statement.lineno, start, start + len(statement.name))
        )
    return tuple(found)


def _sets_markup_template(class_node: ast.ClassDef) -> bool:
    """Return whether a class body sets ``template`` to a string literal that contains a tag."""
    for statement in class_node.body:
        value = statement.value if isinstance(statement, (ast.Assign, ast.AnnAssign)) else None
        if value is None or "template" not in _template_statement_bound_names(statement):
            continue
        # Other frameworks use `template` for a file name or a plain format
        # string; a Citry template has markup.
        if isinstance(value, ast.Constant) and isinstance(value.value, str) and "<" in value.value:
            return True
    return False


def _project_base(
    class_node: ast.ClassDef,
    imported: Mapping[str, tuple[str, int]],
    classes: Mapping[str, ast.ClassDef],
    is_project_module: Callable[[str, int], bool],
    *,
    seen: set[str],
) -> str | None:
    """Return the imported class, as written, that a class extends directly or through a class in this file."""
    seen.add(class_node.name)
    for base in class_node.bases:
        if not isinstance(base, ast.Name):
            continue
        origin = imported.get(base.id)
        if origin is not None and is_project_module(*origin):
            return base.id
        # A base defined earlier in this file may itself extend an imported class.
        local = classes.get(base.id)
        if local is not None and local.name not in seen:
            found = _project_base(local, imported, classes, is_project_module, seen=seen)
            if found is not None:
                return found
    return None


def project_module_exists(module: str, level: int, *, file: Path, root: Path) -> bool:
    """
    Return whether ``from <module> import ...`` in ``file`` imports a module of the project under ``root``.

    A relative import counts when its target is inside ``root``. An absolute
    one counts when ``root`` or a directory between it and the file holds
    the module as a ``.py`` file or a package, which covers a project run
    from a parent directory.
    """
    parts = [part for part in module.split(".") if part]
    if level:
        base = file.parent
        for _step in range(level - 1):
            base = base.parent
        candidates = [base]
    else:
        candidates = [directory for directory in (file.parent, *file.parent.parents) if directory.is_relative_to(root)]
    resolved_root = root.resolve()
    for directory in candidates:
        target = directory.joinpath(*parts)
        for path in (target.with_suffix(".py"), target / "__init__.py") if parts else (directory / "__init__.py",):
            if path.is_file() and path.resolve().is_relative_to(resolved_root):
                return True
    return False


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
    app_components: Mapping[str, bool] | None = None,
) -> PythonTemplateDiscovery:
    """
    Discover direct literal templates on provable Citry component classes.

    Normal batch tooling leaves ``recover_incomplete`` false and receives the
    original Python ``SyntaxError``. An interactive editor may opt into the
    narrow recovery of one unfinished direct triple-quoted template literal.

    Reading one file proves a class is a component only when it extends
    ``Component`` or ``LibraryComponent`` from ``citry``, or a component
    class defined earlier in the same file. A tool that has loaded the
    application can name more classes in ``app_components``.

    Args:
        source: Complete Python module source.
        recover_incomplete: Return the template regions of a module that
            does not parse yet instead of raising ``SyntaxError``.
        app_components: Module-level classes in this file that the loaded
            application registers as components, by class name. Each maps
            to whether the application renders that class's template as
            Citry's own template language (its ``template_lang`` is
            ``None``). A listed class counts as a component even when its
            base class comes from another module; its template is found
            only when the value is ``True``. A class the file already
            proves is read the same way with or without this. Leave it
            out when no application is loaded.

    Returns:
        The template regions, the notices for templates that were skipped,
        and whether the module parsed.

    Raises:
        SyntaxError: If ``source`` does not parse and ``recover_incomplete``
            is false.

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
    regions, notices = _ast_template_regions(source, module, app_components=app_components)
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


def discover_python_component_assets(
    source: str,
    *,
    app_components: Mapping[str, bool] | None = None,
) -> PythonComponentAssetDiscovery:
    """
    Discover direct literal and static file assets on proven components.

    Discovery recognizes direct ``template``, ``js``, and ``css`` literals,
    plus constant ``template_file``, ``js_file``, and ``css_file`` paths. It
    never imports the module or evaluates a computed declaration.

    Args:
        source: Complete Python module source.
        app_components: The classes a loaded application registers as
            components, as passed to
            [`discover_python_templates`][citry.discover_python_templates].
            Their ``js`` and ``css`` are found whatever the value; their
            template only when the value is ``True``.

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
    regions, files, notices = _ast_component_asset_discovery(source, module, app_components=app_components)
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
            else:
                formatted = prepared.region.source_map._canonicalize_multiline_framing(formatted)
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
    must be asynchronous. With no provider, template formatting still runs
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
    if len(delimiter) == 1:
        encoded = encoded.replace(delimiter[0], f"\\{delimiter[0]}")
        return encoded.replace("\n", "\\n").replace("\r", "\\r")
    encoded = _escape_triple_delimiter_runs(encoded, delimiter[0])
    return encoded.replace("\n", newline)


def _escape_triple_delimiter_runs(source: str, quote: str) -> str:
    """Escape only quote bytes that could terminate a triple-quoted literal."""
    result: list[str] = []
    index = 0
    while index < len(source):
        if source[index] != quote:
            result.append(source[index])
            index += 1
            continue
        end = index + 1
        while end < len(source) and source[end] == quote:
            end += 1
        run_length = end - index
        for run_index in range(run_length):
            is_run_break = (run_index + 1) % 3 == 0
            is_literal_tail = end == len(source) and run_index == run_length - 1
            result.append(f"\\{quote}" if is_run_break or is_literal_tail else quote)
        index = end
    return "".join(result)


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
    app_components: Mapping[str, bool] | None = None,
) -> tuple[list[PythonTemplateRegion], list[PythonTemplateNotice]]:
    regions: list[PythonTemplateRegion] = []
    notices: list[PythonTemplateNotice] = []

    parents: dict[ast.ClassDef, object] = {}
    declarations = _ast_component_declarations(module, parents, app_components=app_components)
    owner_lint = _template_owner_lint(declarations, parents)
    for statement, language in declarations:
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
            regions.append(PythonTemplateRegion(statement.name, source_map, owner_lint.get(statement, ())))
    return regions, notices


# A class with more than one base, such as a mixin next to the component
# base, may get a `Lint` from a base the source does not show.
_UNKNOWN_COMPONENT_BASE = object()
# A `Lint` value the source does not show, such as a name imported from
# another module. It hides what a base component sets for the same rule.
_UNREADABLE_LINT_VALUE = object()
_TEMPLATE_SOURCE_NAMES = frozenset({"template", "template_file"})


def _template_owner_lint(
    declarations: list[tuple[ast.ClassDef, object]],
    parents: dict[ast.ClassDef, object],
) -> dict[ast.ClassDef, tuple[ComponentSourceLint, ...]]:
    """
    Map each class that declares a template to the ``Lint`` of every class in the module that renders it.

    A subclass renders its base's template when it sets neither
    ``template`` nor ``template_file``, so it is an owner of that template
    too, and the strictest severity among the owners applies, as it does
    with a loaded application. A subclass whose template language is not
    proven to be native Citry, a subclass with a mixin, and subclasses in
    other modules are not counted.
    """
    resolved: dict[ast.ClassDef, dict[str, object]] = {}
    owners: dict[ast.ClassDef, list[ComponentSourceLint]] = {}
    for declaration, language in declarations:
        # Another template language renders something other than this
        # Citry template, and an unknown one is not proven to render it.
        if language is not None:
            continue
        owner = _template_declaring_class(declaration, parents)
        if owner is None:
            continue
        values = _resolved_source_lint(declaration, parents, resolved)
        owners.setdefault(owner, []).append(
            ComponentSourceLint(
                **{rule: value for rule, value in values.items() if value is not _UNREADABLE_LINT_VALUE},  # type: ignore[arg-type]
            ),
        )
    return {owner: tuple(lint) for owner, lint in owners.items()}


def _template_declaring_class(declaration: ast.ClassDef, parents: dict[ast.ClassDef, object]) -> ast.ClassDef | None:
    """Return the class whose template this class renders, or ``None`` when the source does not prove one."""
    current: ast.ClassDef = declaration
    while True:
        if _binds_template_source(current):
            return current
        parent = parents.get(current)
        if not isinstance(parent, ast.ClassDef):
            return None
        current = parent


def _binds_template_source(class_node: ast.ClassDef) -> bool:
    """Return whether a class body sets ``template`` or ``template_file`` in any way."""
    for statement in class_node.body:
        # A bare annotation such as `template: str` sets nothing.
        if isinstance(statement, ast.AnnAssign) and statement.value is None:
            continue
        if _template_statement_bound_names(statement) & _TEMPLATE_SOURCE_NAMES:
            return True
    return False


def _resolved_source_lint(
    class_node: ast.ClassDef,
    parents: dict[ast.ClassDef, object],
    resolved: dict[ast.ClassDef, dict[str, object]],
) -> dict[str, object]:
    """Combine a class's own ``Lint`` with its bases' the way Citry does, nearest setting first."""
    if class_node in resolved:
        return resolved[class_node]
    values, rest = _own_source_lint(class_node)
    combined = dict(values)
    parent = parents.get(class_node)
    if rest == "inherit" and isinstance(parent, ast.ClassDef):
        for rule, value in _resolved_source_lint(parent, parents, resolved).items():
            combined.setdefault(rule, value)
    elif rest == "unreadable" or (rest == "inherit" and parent is _UNKNOWN_COMPONENT_BASE):
        # Something the source does not show may set the remaining rules,
        # so a base component's literal value would be a guess.
        for rule in _SOURCE_LINT_RULES:
            combined.setdefault(rule, _UNREADABLE_LINT_VALUE)
    resolved[class_node] = combined
    return combined


def _own_source_lint(class_node: ast.ClassDef) -> tuple[dict[str, object], Literal["inherit", "stop", "unreadable"]]:
    """
    Read the rules one class's own ``Lint`` binding sets, and what happens to the rules it leaves out.

    ``"inherit"`` reads them from the base component, ``"stop"`` follows
    ``Lint = None``, which drops every inherited ``Lint``, and
    ``"unreadable"`` means the source does not show them.
    """
    binding: ast.stmt | None = None
    for statement in class_node.body:
        if isinstance(statement, ast.ClassDef) and statement.name == "Lint":
            binding = statement
            continue
        assignment = _direct_template_assignment(statement)
        if assignment is not None and assignment[0] == "Lint":
            if assignment[1] is not None:
                binding = statement
            continue
        # `Lint` bound inside an `if`, a loop, or an import may be anything.
        if "Lint" in _template_statement_bound_names(statement):
            return {}, "unreadable"
    if binding is None:
        return {}, "inherit"
    if not isinstance(binding, ast.ClassDef):
        value = binding.value if isinstance(binding, (ast.Assign, ast.AnnAssign)) else None
        if isinstance(value, ast.Constant) and value.value is None:
            return {}, "stop"
        return {}, "unreadable"
    # A decorator may return a different class.
    if binding.decorator_list:
        return {}, "unreadable"
    values: dict[str, object] = {}
    for statement in binding.body:
        assignment = _direct_template_assignment(statement)
        if assignment is not None and assignment[0] in _SOURCE_LINT_RULES:
            name, value = assignment
            if value is None:
                continue
            # Only a literal severity can be read here: a name or a call
            # needs the code to run, and Citry rejects an unknown string
            # when the class is created.
            if (
                isinstance(value, ast.Constant)
                and type(value.value) is str
                and value.value in {"ignore", "warning", "error"}
            ):
                values[name] = value.value
            else:
                values[name] = _UNREADABLE_LINT_VALUE
            continue
        for name in _template_statement_bound_names(statement) & set(_SOURCE_LINT_RULES):
            values[name] = _UNREADABLE_LINT_VALUE
    # A `Lint` class with bases inherits rules this body does not show.
    return values, ("unreadable" if binding.bases or binding.keywords else "inherit")


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
    app_components: Mapping[str, bool] | None = None,
) -> tuple[
    list[PythonComponentAssetRegion],
    list[PythonComponentAssetFile],
    list[PythonComponentAssetNotice],
]:
    regions: list[PythonComponentAssetRegion] = []
    files: list[PythonComponentAssetFile] = []
    notices: list[PythonComponentAssetNotice] = []
    for statement, language in _ast_component_declarations(module, app_components=app_components):
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


def _ast_component_declarations(
    module: ast.Module,
    parents: dict[ast.ClassDef, object] | None = None,
    *,
    app_components: Mapping[str, bool] | None = None,
) -> list[tuple[ast.ClassDef, object]]:
    """
    Track definite Citry component classes and their statically known template language.

    When ``parents`` is given, it receives each class's one same-module
    component base, ``None`` for Citry's own base, or
    ``_UNKNOWN_COMPONENT_BASE`` for a class with more than one base or a
    base the file does not show.

    ``app_components`` names module-level classes that a loaded application
    registers as components, each mapped to whether its template is
    Citry's own template language. A listed class whose base this file
    cannot trace is accepted too, so a component whose base class comes
    from another module is still found.
    """
    class_nodes: dict[str, ast.ClassDef] = {}
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
            # A class this file cannot trace to a component base is still a
            # component when the loaded application registers it, for
            # example when its base class comes from another module. A
            # traceable class keeps the rules below, so the app never
            # changes how a class this file already proves is read. A
            # decorated class, which this file alone never proves, is read
            # when the app lists it too.
            accepted_by_app = False
            inherited_language: object
            if (
                (not component_bases or statement.decorator_list)
                and app_components is not None
                and statement.name in app_components
            ):
                accepted_by_app = True
                # The app read the template language through the class's
                # bases; anything it could not prove native skips the template.
                inherited_language = None if app_components[statement.name] else _UNKNOWN_TEMPLATE_LANGUAGE
            else:
                inherited_language = (
                    _base_template_language(component_bases[0], component_symbols, component_languages)
                    if len(statement.bases) == 1 and len(component_bases) == 1
                    else _UNKNOWN_TEMPLATE_LANGUAGE
                )
            # Read the base before this statement rebinds its own name. A
            # name still in component_classes is bound to the class
            # statement recorded for it, because any rebinding drops it.
            parent: object = _UNKNOWN_COMPONENT_BASE
            # A base from another module may set a `Lint` this file does not
            # show, so an app-accepted class keeps the unknown parent.
            if len(statement.bases) == 1 and not accepted_by_app:
                base = statement.bases[0]
                parent = class_nodes[base.id] if isinstance(base, ast.Name) and base.id in component_classes else None
            _discard_template_binding(
                statement.name,
                component_symbols,
                citry_modules,
                component_classes,
                component_languages,
            )
            # A decorator may replace a class this file proves, so it is not
            # read as a component; the app's record already names the class
            # that declares the template, decorated or not.
            if (component_bases and not statement.decorator_list) or accepted_by_app:
                class_nodes[statement.name] = statement
                if parents is not None:
                    parents[statement] = parent
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
    lines = source_lines(source)
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
    member_annotations: Mapping[str, Mapping[str, str | None]] | None = None,
    classes: Mapping[str, WireClass] | None = None,
    inferred: Mapping[tuple[int, int], JsonWireType] | None = None,
    unproven: list[tuple[int, int]] | None = None,
    widen_literals: bool = False,
) -> JsonWireType:
    """
    Infer portable JSON-wire metadata using optional proven members.

    ``member_types`` types ``name.attr``. ``member_annotations`` and
    ``classes`` let a longer chain such as ``kwargs.task.lane`` follow the
    attribute annotations of the classes it passes through. ``inferred``
    types a part the rules leave unknown, keyed by its start and end
    offset in ``source``; ``unproven`` collects the offsets of the parts
    still unknown. ``widen_literals`` types a constant by its kind only.
    """
    if type(source) is not str:
        msg = "source must be a str"
        raise TypeError(msg)
    return _json_wire_type_from_expression(
        source,
        member_types=member_types,
        member_annotations=member_annotations,
        classes=classes,
        inferred=inferred,
        unproven=unproven,
        widen_literals=widen_literals,
    )


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
    "SERVER_EVENT_CALL_NAMES",
    "VUE_AMBIENT_NAMES",
    "AlpineAttributeFinding",
    "AlpineAttributeLintConsumer",
    "AttributeValueFinding",
    "AttributeValueLintConsumer",
    "BrowserBinding",
    "BrowserCompletion",
    "BrowserComponentBinding",
    "BrowserComponentCall",
    "BrowserComponentContextName",
    "BrowserComponentMemberReference",
    "BrowserComponentPropContribution",
    "BrowserComponentPropFinding",
    "BrowserComponentPropSite",
    "BrowserComponentPublicName",
    "BrowserComponentSection",
    "BrowserComponentSourceAnalysis",
    "BrowserDeclarativeEvent",
    "BrowserEmitName",
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
    "BrowserSourceAnalysis",
    "BrowserStateBinding",
    "BrowserStateBindingTargetError",
    "ComponentJsLintConsumer",
    "ComponentJsLintFinding",
    "ComponentNameMatch",
    "ComponentSourceLint",
    "CssDataCompletion",
    "CssDataReference",
    "CssVariableFinding",
    "JsonWireField",
    "JsonWireKind",
    "JsonWireType",
    "LspPosition",
    "LspRange",
    "MarkLiteralFinding",
    "MarkupLintConsumer",
    "MarkupLintFinding",
    "MisspelledDirectiveFinding",
    "MisspelledDirectiveLintConsumer",
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
    "ShadowRevealDocument",
    "TemplateAnalysis",
    "TemplateLintConsumer",
    "TemplateLintFinding",
    "TemplatePythonControl",
    "TemplatePythonQuery",
    "TemplatePythonRoot",
    "TemplatePythonValueType",
    "TemplateTagUse",
    "UnknownComponentUse",
    "UntracedComponentTemplate",
    "VueLintConsumer",
    "VueLintFinding",
    "WireClass",
    "analyze_browser_component_source",
    "analyze_browser_expression",
    "analyze_css_data_source",
    "analyze_js_data_source",
    "analyze_template_data_source",
    "browser_bindings",
    "browser_client_prop_accepts",
    "browser_completion_at",
    "browser_component_prop_findings",
    "browser_component_prop_sites",
    "browser_component_props",
    "browser_declarative_events",
    "browser_expression_at",
    "browser_expressions",
    "browser_i18n_bind_calls",
    "browser_i18n_binding_directives",
    "browser_i18n_calls_checkable",
    "browser_i18n_message_calls",
    "browser_i18n_profile_calls",
    "browser_identifier_at",
    "browser_identifiers",
    "browser_literal_calls",
    "browser_literal_wire_type",
    "browser_member_at",
    "browser_member_literal_calls",
    "browser_state_binding_target_errors",
    "browser_state_bindings",
    "build_inferred_template_shadow",
    "build_reveal_shadow",
    "build_schema_template_shadow",
    "component_js_i18n_owners",
    "component_name_match",
    "css_data_completion_at",
    "css_data_reference_at",
    "css_data_references",
    "discover_python_component_assets",
    "discover_python_templates",
    "discover_untraced_component_templates",
    "finish_python_component_assets",
    "format_python_component_assets",
    "format_python_templates",
    "json_wire_type_from_annotation",
    "json_wire_type_from_expression",
    "lint_alpine_attributes",
    "lint_attribute_values",
    "lint_component_js_prop_assignments",
    "lint_invalid_vue_expressions",
    "lint_markup",
    "lint_misspelled_css_variables",
    "lint_misspelled_directives",
    "lint_prop_assignments",
    "lint_undeclared_component_js_emits",
    "lint_undeclared_component_listeners",
    "lint_undeclared_template_emits",
    "lint_unknown_component_js_members",
    "lint_unknown_component_js_variables",
    "lint_unknown_template_variables",
    "lint_unknown_vue_variables",
    "lint_vue_python_variables",
    "mark_literal_findings",
    "merge_json_wire_types",
    "prepare_python_component_assets",
    "project_module_exists",
    "python_class_asset_resolution_signature",
    "python_class_defines_direct_method",
    "python_class_direct_method_first_line",
    "python_class_resolution_signature",
    "python_class_static_asset_matches",
    "python_event_handler_range",
    "template_python_queries",
    "template_python_query_at",
    "template_static_input_queries",
    "template_tag_uses",
    "unknown_component_uses",
]
