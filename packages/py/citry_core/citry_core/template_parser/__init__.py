"""
Citry template parser - parse and compile Citry templates.

This module exposes the V3 template parser (Rust-powered) to Python.
It provides two main functions and the AST types they produce.
Parser failures retain their built-in exception types; ``parse_diagnostic``
returns their stable code and UTF-8 byte range.

Quick start::

    from citry_core.template_parser import parse_template, compile_template

    # Parse a template into an AST
    t = parse_template('<p>Hello {{ name }}!</p>')

    # Inspect the AST
    print(t.used_variables)   # [Token(content='name', ...)]
    print(len(t.elements))    # 1 (a <p> node containing text + expression)

    # Compile the AST into Python source code
    code = compile_template(t)
    print(code)
    # def generate_template():
    #     body = [...]
    #     return body

The generated code instantiates runtime node classes (``ExprNode``,
``ComponentNode``, etc.) defined in ``citry.nodes``.
See ``nodes.py`` for the full list and their constructor signatures.
"""

# ruff: noqa: RUF022
from collections.abc import Mapping
from typing import TypeAlias

from citry_core import _rust
from citry_core.template_parser.compile import compile_template
from citry_core.template_parser.parse import parse_diagnostic, parse_template

analyze_browser_source = _rust.template_parser.analyze_browser_source
analyze_component_scope_writes = _rust.template_parser.analyze_component_scope_writes
analyze_component_source = _rust.template_parser.analyze_component_source

# AST types (re-exported from Rust)
ParseDiagnostic: TypeAlias = _rust.template_parser.ParseDiagnostic
Token: TypeAlias = _rust.template_parser.Token
Comment: TypeAlias = _rust.template_parser.Comment
HtmlAttrKind: TypeAlias = _rust.template_parser.HtmlAttrKind
FillDataField: TypeAlias = _rust.template_parser.FillDataField
FillDataPattern: TypeAlias = _rust.template_parser.FillDataPattern
HtmlAttr: TypeAlias = _rust.template_parser.HtmlAttr
HtmlStartTag: TypeAlias = _rust.template_parser.HtmlStartTag
HtmlEndTag: TypeAlias = _rust.template_parser.HtmlEndTag
Expr: TypeAlias = _rust.template_parser.Expr
Text: TypeAlias = _rust.template_parser.Text
ForeignSourcePart: TypeAlias = _rust.template_parser.ForeignSourcePart
Node: TypeAlias = _rust.template_parser.Node
TemplateElement: TypeAlias = _rust.template_parser.TemplateElement
StaticNamedSlot: TypeAlias = _rust.template_parser.StaticNamedSlot
Template: TypeAlias = _rust.template_parser.Template

# Config types
TagRules: TypeAlias = _rust.template_parser.TagRules
ForeignSpan: TypeAlias = _rust.template_parser.ForeignSpan
ParseOptions: TypeAlias = _rust.template_parser.ParseOptions

# Constants
# HTML void elements (elements that cannot have children, e.g. <br/>),
# single-sourced from the Rust parser.
HTML_VOID_ELEMENTS: frozenset[str] = _rust.template_parser.HTML_VOID_ELEMENTS
# Structural ``<c-*>`` tags, single-sourced from the Rust parser.
RESERVED_TAG_NAMES: frozenset[str] = _rust.template_parser.RESERVED_TAG_NAMES
# Fixed directives and structural attributes, single-sourced from the parser.
CITRY_DIRECTIVE_NAMES: frozenset[str] = _rust.template_parser.CITRY_DIRECTIVE_NAMES
STRUCTURAL_TAG_ATTRIBUTE_NAMES: Mapping[str, frozenset[str]] = _rust.template_parser.STRUCTURAL_TAG_ATTRIBUTE_NAMES

__all__ = [
    # Functions
    "analyze_browser_source",
    "analyze_component_scope_writes",
    "analyze_component_source",
    "parse_template",
    "parse_diagnostic",
    "compile_template",
    # AST types
    "ParseDiagnostic",
    "Token",
    "Comment",
    "HtmlAttrKind",
    "FillDataField",
    "FillDataPattern",
    "HtmlAttr",
    "HtmlStartTag",
    "HtmlEndTag",
    "Expr",
    "Text",
    "ForeignSourcePart",
    "Node",
    "TemplateElement",
    "StaticNamedSlot",
    "Template",
    # Config types
    "TagRules",
    "ForeignSpan",
    "ParseOptions",
    # Constants
    "HTML_VOID_ELEMENTS",
    "RESERVED_TAG_NAMES",
    "CITRY_DIRECTIVE_NAMES",
    "STRUCTURAL_TAG_ATTRIBUTE_NAMES",
]
