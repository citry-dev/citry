"""Tests for the Rust-backed template formatter Python surface."""

from __future__ import annotations

import pickle

import pytest

from citry_core import _rust
from citry_core.template_formatter import TemplateFormatError, format_template


def test_formats_authored_template_text() -> None:
    source = '<c-CButton  class = "primary"  disabled ></c-CButton>'
    expected = '<c-CButton class="primary" disabled></c-CButton>'

    assert _rust.template_formatter.format_template(source) == expected
    assert format_template(source) == expected
    assert format_template(expected) == expected


def test_format_error_preserves_structured_syntax_details() -> None:
    with pytest.raises(TemplateFormatError) as raised:
        format_template("<c-raw>unterminated")

    error = raised.value
    assert isinstance(error, ValueError)
    assert error.code == "citry.format.syntax"
    assert error.message == str(error)
    assert error.range is not None
    assert error.diagnostic is not None
    assert error.diagnostic.code == "citry.parse.syntax"


def test_suppression_error_has_no_parser_diagnostic() -> None:
    with pytest.raises(TemplateFormatError) as raised:
        format_template("{# fmt: on #}<div></div>")

    error = raised.value
    assert error.code == "citry.format.suppression"
    assert error.range == (0, 13)
    assert error.diagnostic is None


def test_error_has_the_public_importable_module_identity() -> None:
    assert TemplateFormatError.__module__ == "citry_core.template_formatter"

    error = TemplateFormatError("failure")
    restored = pickle.loads(pickle.dumps(error))  # noqa: S301 - trusted local round-trip

    assert type(restored) is TemplateFormatError
    assert str(restored) == "failure"


def test_non_string_input_remains_a_type_error() -> None:
    with pytest.raises(TypeError):
        format_template(42)  # type: ignore[arg-type]
