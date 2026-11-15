"""
The Citry internals that citry-lsp uses, kept stable for all of citry 1.x.

citry-lsp (the Citry language server, a separate package) imports the
Citry names it needs from this module and from the public ``citry``
package, and from nowhere else in Citry. Its own tests import a few more
names from here, such as ``_check_template``, because a release check
runs an older citry-lsp's tests against a newer citry. Private attribute
and setting names that citry-lsp reads by name are here as constants,
such as ``DEFINITION_ID_ATTRIBUTE``.

A citry-lsp 1.x release must keep working next to any citry 1.x, older
or newer than the one it was released with, so during 1.x each name here
keeps working:

- do not remove or rename a name;
- do not remove a parameter, make one required, move a positional one,
  or change its default;
- keep what a function returns and the arguments it passes to a callback;
- do not remove a public attribute or method of a class listed here;
- a string or number constant keeps its value, and a collection constant
  keeps its type and its entries (it may gain entries).

You may add names, and add optional parameters, attributes and methods.
``tests/test_lsp_support_module.py`` checks most of these rules against
``tests/lsp_support_names.json``; it cannot check return types and
callback arguments, which the release check covers. A name added in a
later 1.x release is missing from older releases, so citry-lsp imports
such a name in a ``try`` block and turns the feature that needs it off
when the import fails.

Users must not import this module. It is not part of Citry's public API,
and the rules above exist only for citry-lsp. Most of these names are
private to Citry, and the template analysis names are experimental.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from citry._authored_expression import (
    parse_authored_expression,
)
from citry._browser_expressions import (
    _ascii_lower,
    _normalized_dynamic_slot_source,
    _tokens,
    _vue_hyphenated_prop_name,
    _vue_prop_name,
)
from citry._checker import (
    CheckFinding,
    CheckReport,
    _BrowserSource,
    _check_browser_source,
    _check_template,
    _TemplateSource,
)
from citry._class_introspection import (
    _safe_class_text,
    _static_class_dict,
    _static_class_mro,
)
from citry._component_introspection import (
    _loaded_python_file,
)
from citry._diagnostic_catalog import (
    BROWSER_INCOMPATIBLE_COMPONENT_PROP,
    BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD,
    BROWSER_INVALID_STATE_BINDING_TARGET,
    BROWSER_MISSING_COMPONENT_PROP,
    BROWSER_MISSING_FORM_FIELD,
    BROWSER_MISSING_SERVER_EVENT_FIELD,
    BROWSER_PROP_ASSIGNMENT,
    BROWSER_UNDECLARED_COMPONENT_EVENT,
    BROWSER_UNDECLARED_EMIT,
    BROWSER_UNKNOWN_FORM_FIELD,
    BROWSER_UNKNOWN_SERVER_EVENT,
    BROWSER_UNKNOWN_SERVER_EVENT_FIELD,
    BROWSER_UNKNOWN_STATE_FIELD,
    CHECK_TEMPLATE_NOT_CHECKED,
    COMPONENT_JS_UNKNOWN_MEMBER,
    COMPONENT_JS_UNKNOWN_VARIABLE,
    FORMAT_INELIGIBLE,
    FORMAT_PROVIDER_INVALID,
    FORMAT_STALE_DOCUMENT,
    I18N_ARGUMENT_INVALID,
    I18N_CATALOG_INVALID,
    I18N_UNKNOWN_MESSAGE,
    JS_DATA_PUBLIC_NAME_COLLISION,
    JS_DATA_UNSUPPORTED_TYPE,
    PARSE_CONFIGURATION,
    TEMPLATE_INVALID_ATTRIBUTE_VALUE,
    TEMPLATE_MARKER_NAME_INVALID,
    TEMPLATE_UNKNOWN_COMPONENT,
    VUE_INVALID_EXPRESSION,
    VUE_PYTHON_VARIABLE,
    VUE_UNKNOWN_VARIABLE,
)
from citry._diagnostics import (
    diagnostic_definition,
    diagnostic_documentation_url,
    render_diagnostic,
)
from citry._django_startup import (
    start_django_from_environment,
)
from citry._html_attribute_values import (
    ENUMERATED_VALUES,
    HTML_ELEMENTS,
)
from citry._i18n_directives import (
    looks_like_i18n_binding,
)
from citry._i18n_guards import (
    i18n_configured_guarded_calls,
)
from citry._json_wire import (
    SECRET_NOT_SENT_REASON,
)
from citry._linting import (
    TemplateLintInfo,
    TemplateVariableInfo,
    _component_lint_variable_owners,
)
from citry._markup_lint import (
    MARKUP_LINT_RULES,
)
from citry._nested_declarations import (
    _nearest_data_shape_declaration,
)
from citry._path_checks import (
    engine_path_verdicts,
)
from citry._provide_keys import (
    engine_inject_keys,
)
from citry._registry_lint import (
    ServerEventPayload,
    server_event_calls,
    server_event_form_findings,
    server_event_forms,
    server_event_payload_findings,
    server_event_payload_from_description,
    template_urls,
    unknown_inject_key_findings,
    unknown_url_findings,
)
from citry._schema_introspection import (
    _inspect_schema_class,
)
from citry._slot_props import (
    ScopedFill,
    SlotOutlet,
    lint_unknown_slot_props,
    outlets_for_slot,
    scoped_fills,
    slot_outlets,
    slot_prop_name,
    unknown_slot_props_for,
)
from citry._source_lines import (
    line_break_count,
    source_lines,
)
from citry._symbol_table import (
    EDITOR_NOTE,
    symtable,
    symtable_missing,
)
from citry._template_data_source import (
    TemplateDataSourceShape,
)
from citry._template_python import (
    _method_bound_names,
    _renamable_method_locals,
)
from citry._vue_compile_lint import (
    lint_vue_compile,
)
from citry._walk import (
    Call,
    run,
)
from citry._wire_classes import (
    KwargsWireClasses,
    SlotDataWireClass,
    kwargs_wire_classes,
    slot_data_wire_classes,
)
from citry.analysis import (
    SERVER_EVENT_CALL_NAMES,
    AlpineAttributeFinding,
    AlpineAttributeLintConsumer,
    AttributeValueFinding,
    AttributeValueLintConsumer,
    BrowserBinding,
    BrowserComponentBinding,
    BrowserComponentPropContribution,
    BrowserComponentPropSite,
    BrowserComponentSourceAnalysis,
    BrowserExpression,
    BrowserObjectProperty,
    BrowserProp,
    ComponentJsLintConsumer,
    ComponentSourceLint,
    JsonWireField,
    JsonWireType,
    MarkupLintConsumer,
    MarkupLintFinding,
    MisspelledDirectiveFinding,
    MisspelledDirectiveLintConsumer,
    PythonComponentAssetKind,
    PythonComponentAssetNotice,
    PythonComponentAssetPlan,
    PythonComponentAssetRequest,
    PythonTemplateFormatError,
    PythonTemplateSourceMap,
    ShadowPythonDocument,
    TemplateAnalysis,
    TemplateLintConsumer,
    TemplatePythonControl,
    TemplatePythonQuery,
    TemplatePythonRoot,
    TemplatePythonSlotDataType,
    TemplatePythonValueType,
    VueLintConsumer,
    analyze_browser_component_source,
    analyze_browser_expression,
    analyze_css_data_source,
    analyze_js_data_source,
    analyze_template_data_source,
    browser_bindings,
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
    browser_state_binding_target_errors,
    browser_state_bindings,
    build_inferred_template_shadow,
    build_reveal_shadow,
    build_schema_template_shadow,
    component_js_i18n_owners,
    component_name_match,
    css_data_completion_at,
    css_data_reference_at,
    css_data_references,
    discover_python_component_assets,
    discover_python_templates,
    discover_untraced_component_templates,
    finish_python_component_assets,
    format_python_templates,
    json_wire_type_from_annotation,
    json_wire_type_from_expression,
    lint_alpine_attributes,
    lint_attribute_values,
    lint_component_js_prop_assignments,
    lint_invalid_vue_expressions,
    lint_markup,
    lint_misspelled_directives,
    lint_prop_assignments,
    lint_undeclared_component_js_emits,
    lint_undeclared_component_listeners,
    lint_undeclared_template_emits,
    lint_unknown_component_js_members,
    lint_unknown_component_js_variables,
    lint_unknown_template_variables,
    lint_unknown_vue_variables,
    lint_vue_python_variables,
    mark_literal_findings,
    merge_json_wire_types,
    prepare_python_component_assets,
    project_module_exists,
    python_application_lint_variable_range,
    python_class_asset_resolution_signature,
    python_class_defines_direct_method,
    python_class_direct_method_first_line,
    python_class_resolution_signature,
    python_class_static_asset_matches,
    python_component_lint_variable_range,
    python_event_handler_range,
    template_python_queries,
    template_python_query_at,
    template_static_input_queries,
    unknown_component_uses,
    vue_listener_event_names,
)
from citry.assets import (
    _find_pair_declaration,
)
from citry.commands.check import (
    _with_type_findings,
)
from citry.ext.events.extension import (
    _component_events_info,
)
from citry.ext.events.handlers import (
    event_options,
)
from citry.library_component import _COMPONENT_ROOT_FLAG, _DEFINITION_FLAG

# Private class attributes and settings keys that citry-lsp reads by name,
# from a class's own namespace or from source code, without calling Citry.
# Each value is the name Citry uses, so it can change only with citry 2.0.0.
DEFINITION_ID_ATTRIBUTE = "_definition_id"
OWNER_ATTRIBUTE = "_citry_owner"
LIBRARY_DEFINITION_ATTRIBUTE = _DEFINITION_FLAG
COMPONENT_ROOT_ATTRIBUTE = _COMPONENT_ROOT_FLAG
CSRF_FIELD_NAMES_SETTING = "_csrf_field_names"

if TYPE_CHECKING:
    from citry.citry import Citry


def i18n_tooling_index(engine: Citry) -> dict[str, object] | None:
    """
    Return the i18n extension's index of messages for citry-lsp's app worker.

    Returns ``None`` when the engine has no i18n extension. The index is
    plain JSON data; citry-lsp reads it in ``citry_lsp/project.py``, so
    during 1.x the index only gains keys.
    """
    # The worker loads an app with any set of extensions, and an app may
    # replace the i18n extension with its own class, so a missing index is
    # normal and turns the editor's i18n checks off rather than failing.
    try:
        extension = engine.extensions.get_extension("i18n")
    except ValueError:
        return None
    inspector = getattr(extension, "_tooling_index", None)
    if not callable(inspector):
        return None
    index: dict[str, object] = inspector()
    return index


__all__ = [
    "BROWSER_INCOMPATIBLE_COMPONENT_PROP",
    "BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD",
    "BROWSER_INVALID_STATE_BINDING_TARGET",
    "BROWSER_MISSING_COMPONENT_PROP",
    "BROWSER_MISSING_FORM_FIELD",
    "BROWSER_MISSING_SERVER_EVENT_FIELD",
    "BROWSER_PROP_ASSIGNMENT",
    "BROWSER_UNDECLARED_COMPONENT_EVENT",
    "BROWSER_UNDECLARED_EMIT",
    "BROWSER_UNKNOWN_FORM_FIELD",
    "BROWSER_UNKNOWN_SERVER_EVENT",
    "BROWSER_UNKNOWN_SERVER_EVENT_FIELD",
    "BROWSER_UNKNOWN_STATE_FIELD",
    "CHECK_TEMPLATE_NOT_CHECKED",
    "COMPONENT_JS_UNKNOWN_MEMBER",
    "COMPONENT_JS_UNKNOWN_VARIABLE",
    "COMPONENT_ROOT_ATTRIBUTE",
    "CSRF_FIELD_NAMES_SETTING",
    "DEFINITION_ID_ATTRIBUTE",
    "EDITOR_NOTE",
    "ENUMERATED_VALUES",
    "FORMAT_INELIGIBLE",
    "FORMAT_PROVIDER_INVALID",
    "FORMAT_STALE_DOCUMENT",
    "HTML_ELEMENTS",
    "I18N_ARGUMENT_INVALID",
    "I18N_CATALOG_INVALID",
    "I18N_UNKNOWN_MESSAGE",
    "JS_DATA_PUBLIC_NAME_COLLISION",
    "JS_DATA_UNSUPPORTED_TYPE",
    "LIBRARY_DEFINITION_ATTRIBUTE",
    "MARKUP_LINT_RULES",
    "OWNER_ATTRIBUTE",
    "PARSE_CONFIGURATION",
    "SECRET_NOT_SENT_REASON",
    "SERVER_EVENT_CALL_NAMES",
    "TEMPLATE_INVALID_ATTRIBUTE_VALUE",
    "TEMPLATE_MARKER_NAME_INVALID",
    "TEMPLATE_UNKNOWN_COMPONENT",
    "VUE_INVALID_EXPRESSION",
    "VUE_PYTHON_VARIABLE",
    "VUE_UNKNOWN_VARIABLE",
    "AlpineAttributeFinding",
    "AlpineAttributeLintConsumer",
    "AttributeValueFinding",
    "AttributeValueLintConsumer",
    "BrowserBinding",
    "BrowserComponentBinding",
    "BrowserComponentPropContribution",
    "BrowserComponentPropSite",
    "BrowserComponentSourceAnalysis",
    "BrowserExpression",
    "BrowserObjectProperty",
    "BrowserProp",
    "Call",
    "CheckFinding",
    "CheckReport",
    "ComponentJsLintConsumer",
    "ComponentSourceLint",
    "JsonWireField",
    "JsonWireType",
    "KwargsWireClasses",
    "MarkupLintConsumer",
    "MarkupLintFinding",
    "MisspelledDirectiveFinding",
    "MisspelledDirectiveLintConsumer",
    "PythonComponentAssetKind",
    "PythonComponentAssetNotice",
    "PythonComponentAssetPlan",
    "PythonComponentAssetRequest",
    "PythonTemplateFormatError",
    "PythonTemplateSourceMap",
    "ScopedFill",
    "ServerEventPayload",
    "ShadowPythonDocument",
    "SlotDataWireClass",
    "SlotOutlet",
    "TemplateAnalysis",
    "TemplateDataSourceShape",
    "TemplateLintConsumer",
    "TemplateLintInfo",
    "TemplatePythonControl",
    "TemplatePythonQuery",
    "TemplatePythonRoot",
    "TemplatePythonSlotDataType",
    "TemplatePythonValueType",
    "TemplateVariableInfo",
    "VueLintConsumer",
    "_BrowserSource",
    "_TemplateSource",
    "_ascii_lower",
    "_check_browser_source",
    "_check_template",
    "_component_events_info",
    "_component_lint_variable_owners",
    "_find_pair_declaration",
    "_inspect_schema_class",
    "_loaded_python_file",
    "_method_bound_names",
    "_nearest_data_shape_declaration",
    "_normalized_dynamic_slot_source",
    "_renamable_method_locals",
    "_safe_class_text",
    "_static_class_dict",
    "_static_class_mro",
    "_tokens",
    "_vue_hyphenated_prop_name",
    "_vue_prop_name",
    "_with_type_findings",
    "analyze_browser_component_source",
    "analyze_browser_expression",
    "analyze_css_data_source",
    "analyze_js_data_source",
    "analyze_template_data_source",
    "browser_bindings",
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
    "diagnostic_definition",
    "diagnostic_documentation_url",
    "discover_python_component_assets",
    "discover_python_templates",
    "discover_untraced_component_templates",
    "engine_inject_keys",
    "engine_path_verdicts",
    "event_options",
    "finish_python_component_assets",
    "format_python_templates",
    "i18n_configured_guarded_calls",
    "i18n_tooling_index",
    "json_wire_type_from_annotation",
    "json_wire_type_from_expression",
    "kwargs_wire_classes",
    "line_break_count",
    "lint_alpine_attributes",
    "lint_attribute_values",
    "lint_component_js_prop_assignments",
    "lint_invalid_vue_expressions",
    "lint_markup",
    "lint_misspelled_directives",
    "lint_prop_assignments",
    "lint_undeclared_component_js_emits",
    "lint_undeclared_component_listeners",
    "lint_undeclared_template_emits",
    "lint_unknown_component_js_members",
    "lint_unknown_component_js_variables",
    "lint_unknown_slot_props",
    "lint_unknown_template_variables",
    "lint_unknown_vue_variables",
    "lint_vue_compile",
    "lint_vue_python_variables",
    "looks_like_i18n_binding",
    "mark_literal_findings",
    "merge_json_wire_types",
    "outlets_for_slot",
    "parse_authored_expression",
    "prepare_python_component_assets",
    "project_module_exists",
    "python_application_lint_variable_range",
    "python_class_asset_resolution_signature",
    "python_class_defines_direct_method",
    "python_class_direct_method_first_line",
    "python_class_resolution_signature",
    "python_class_static_asset_matches",
    "python_component_lint_variable_range",
    "python_event_handler_range",
    "render_diagnostic",
    "run",
    "scoped_fills",
    "server_event_calls",
    "server_event_form_findings",
    "server_event_forms",
    "server_event_payload_findings",
    "server_event_payload_from_description",
    "slot_data_wire_classes",
    "slot_outlets",
    "slot_prop_name",
    "source_lines",
    "start_django_from_environment",
    "symtable",
    "symtable_missing",
    "template_python_queries",
    "template_python_query_at",
    "template_static_input_queries",
    "template_urls",
    "unknown_component_uses",
    "unknown_inject_key_findings",
    "unknown_slot_props_for",
    "unknown_url_findings",
    "vue_listener_event_names",
]
