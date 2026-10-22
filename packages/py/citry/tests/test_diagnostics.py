from __future__ import annotations

import dataclasses

import pytest

from citry import LintSettings
from citry._diagnostic_catalog import DIAGNOSTICS, JS_DATA_PUBLIC_NAME_COLLISION, TEMPLATE_UNKNOWN_VARIABLE
from citry._diagnostics import (
    diagnostic_definition,
    diagnostic_documentation_url,
    render_diagnostic,
)
from citry._linting import TemplateLintInfo


def test_catalog_definition_and_documentation_url() -> None:
    definition = diagnostic_definition(TEMPLATE_UNKNOWN_VARIABLE)

    assert definition.title == "Unknown template variable"
    assert definition.configurable_severity is True
    assert diagnostic_documentation_url(TEMPLATE_UNKNOWN_VARIABLE) == (
        "https://citry.dev/ide/diagnostics/#citry.template.unknown-variable"
    )


# Each LintSettings severity setting and the catalog code it controls.
_LINT_RULE_CODES = {
    "rule_unknown_template_variable": "citry.template.unknown-variable",
    "rule_i18n_missing_param_type": "citry.i18n.missing-param-type",
    "rule_unknown_vue_variable": "citry.vue.unknown-variable",
    "rule_unknown_component_js_variable": "citry.component-js.unknown-variable",
    "rule_unknown_component_js_member": "citry.component-js.unknown-member",
    "rule_vue_python_variable": "citry.vue.python-variable",
    "rule_alpine_attribute": "citry.template.alpine-attribute",
    "rule_alpine_cloak": "citry.template.alpine-cloak",
    "rule_invalid_attribute_value": "citry.template.invalid-attribute-value",
    "rule_misspelled_directive": "citry.template.misspelled-directive",
    "rule_misspelled_attribute": "citry.template.misspelled-attribute",
    "rule_misspelled_element": "citry.template.misspelled-element",
    "rule_unknown_aria_attribute": "citry.template.unknown-aria-attribute",
    "rule_invalid_nesting": "citry.template.invalid-nesting",
    "rule_duplicate_id": "citry.template.duplicate-id",
    "rule_missing_image_alt": "citry.template.missing-image-alt",
    "rule_invalid_model_target": "citry.browser.invalid-model-target",
    "rule_misspelled_event": "citry.vue.misspelled-event",
    "rule_invalid_vue_expression": "citry.vue.invalid-expression",
    "rule_vue_compile_error": "citry.vue.compile-error",
    "rule_undeclared_component_event": "citry.browser.undeclared-component-event",
    "rule_missing_component_key": "citry.browser.missing-component-key",
    "rule_prop_assignment": "citry.browser.prop-assignment",
    "rule_unknown_server_event_field": "citry.browser.unknown-server-event-field",
    "rule_unknown_form_field": "citry.browser.unknown-form-field",
    "rule_missing_form_field": "citry.browser.missing-form-field",
    "rule_missing_server_event_field": "citry.browser.missing-server-event-field",
    "rule_incompatible_server_event_field": "citry.browser.incompatible-server-event-field",
    "rule_misspelled_css_variable": "citry.css.misspelled-variable",
    "rule_misspelled_css_class": "citry.css.misspelled-class",
    "rule_undeclared_css_class": "citry.css.undeclared-class",
    "rule_undeclared_css_variable": "citry.css.undeclared-variable",
    "rule_unknown_url": "citry.template.unknown-url",
    "rule_unknown_inject_key": "citry.template.unknown-inject-key",
    "rule_i18n_cross_language_fallback": "citry.i18n.cross-language-fallback",
}


def test_catalog_default_severities_match_the_lint_settings_defaults() -> None:
    # The catalog feeds the diagnostics reference page, and LintSettings
    # decides what users get, so the two copies of each default must agree.
    settings_rules = {
        field.name: field.default for field in dataclasses.fields(LintSettings) if field.name.startswith("rule_")
    }
    configurable_codes = {code for code, item in DIAGNOSTICS.items() if item.get("configurableSeverity")}
    # A new rule must be added to the mapping, so it cannot skip this check.
    assert set(settings_rules) == set(_LINT_RULE_CODES)
    assert configurable_codes == set(_LINT_RULE_CODES.values())
    assert {name: diagnostic_definition(code).default_severity for name, code in _LINT_RULE_CODES.items()} == (
        settings_rules
    )
    # The record the app worker sends the editor carries its own defaults;
    # a rule it leaves without one is always filled in from the settings.
    lint_info_rules = {
        field.name: field.default
        for field in dataclasses.fields(TemplateLintInfo)
        if field.name.startswith("rule_") and field.default is not dataclasses.MISSING
    }
    assert lint_info_rules == {name: settings_rules[name] for name in lint_info_rules}


def test_catalog_message_variants_are_the_runtime_wording() -> None:
    assert render_diagnostic(TEMPLATE_UNKNOWN_VARIABLE, variant="closed", name="missing") == (
        "Template variable 'missing' is not available in this template."
    )
    assert render_diagnostic(TEMPLATE_UNKNOWN_VARIABLE, variant="allow-extra", name="missing") == (
        "Template variable 'missing' is not declared. It may be supplied dynamically."
    )


def test_js_data_public_name_collision_catalog_definition_and_messages() -> None:
    definition = diagnostic_definition(JS_DATA_PUBLIC_NAME_COLLISION)

    assert definition.title == "JsData field conflicts with a public instance name"
    assert definition.default_severity == "error"
    assert definition.surfaces == ("lsp",)
    assert diagnostic_documentation_url(JS_DATA_PUBLIC_NAME_COLLISION) == (
        "https://citry.dev/ide/diagnostics/#citry.js-data.public-name-collision"
    )
    assert render_diagnostic(JS_DATA_PUBLIC_NAME_COLLISION, name="displayName") == (
        "JsData field 'displayName' conflicts with a reserved or component-defined public instance name."
    )
    assert render_diagnostic(JS_DATA_PUBLIC_NAME_COLLISION, variant="conditional", name="save") == (
        "JsData field 'save' conflicts with a reserved or component-defined public instance name when supplied."
    )


def test_catalog_renderer_rejects_parameter_drift() -> None:
    with pytest.raises(TypeError, match="missing name"):
        render_diagnostic(TEMPLATE_UNKNOWN_VARIABLE, variant="closed")
    with pytest.raises(TypeError, match="unexpected typo"):
        render_diagnostic(TEMPLATE_UNKNOWN_VARIABLE, variant="closed", name="missing", typo=True)


def test_every_catalog_entry_carries_the_fields_the_runtime_reads() -> None:
    # The generated table keeps only some catalog fields to stay small in the
    # wheel, so check that each entry still has every field the lookup reads.
    for code in DIAGNOSTICS:
        definition = diagnostic_definition(code)
        assert definition.code == code
        assert diagnostic_documentation_url(code) == f"https://citry.dev/ide/diagnostics/#{code}"
