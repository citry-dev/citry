from __future__ import annotations

import pytest

from citry._diagnostic_catalog import JS_DATA_PUBLIC_NAME_COLLISION, TEMPLATE_UNKNOWN_VARIABLE
from citry._diagnostics import (
    diagnostic_definition,
    diagnostic_documentation_url,
    render_diagnostic,
)


def test_catalog_definition_and_documentation_url() -> None:
    definition = diagnostic_definition(TEMPLATE_UNKNOWN_VARIABLE)

    assert definition.title == "Unknown template variable"
    assert definition.configurable_severity is True
    assert diagnostic_documentation_url(TEMPLATE_UNKNOWN_VARIABLE) == (
        "https://citry.dev/ide/diagnostics/#citry.template.unknown-variable"
    )


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
