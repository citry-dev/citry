"""Rust-backed formatting for authored Citry template text."""

from typing import TypeAlias

from citry_core import _rust

TemplateFormatError: TypeAlias = _rust.template_formatter.TemplateFormatError


def format_template(source: str) -> str:
    """
    Format authored Citry template text without loading an application.

    Args:
        source: Complete Citry template text.

    Returns:
        The formatted template.

    Raises:
        TemplateFormatError: If the template is invalid or cannot be formatted
            while preserving the formatter invariants.

    """
    return _rust.template_formatter.format_template(source)


__all__ = ["TemplateFormatError", "format_template"]
