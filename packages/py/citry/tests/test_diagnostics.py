from __future__ import annotations

import pytest

from citry._diagnostic_catalog import TEMPLATE_UNKNOWN_VARIABLE
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


def test_catalog_renderer_rejects_parameter_drift() -> None:
    with pytest.raises(TypeError, match="missing name"):
        render_diagnostic(TEMPLATE_UNKNOWN_VARIABLE, variant="closed")
    with pytest.raises(TypeError, match="unexpected typo"):
        render_diagnostic(TEMPLATE_UNKNOWN_VARIABLE, variant="closed", name="missing", typo=True)
