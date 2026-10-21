"""
Lint rules that compare a template's classes and a stylesheet's custom properties with the CSS that Citry reads.

``citry check`` runs these only with the loaded application, because each one
needs every registered component's CSS: a class or a custom property that
one component uses may be declared by another. The editor does not run them.

The CSS that Citry reads is, for every registered component: its ``css`` or
``css_file``, the stylesheets in its ``Dependencies`` that are inline
(``Style(content=...)`` or a pre-rendered ``<style>`` tag) or local files,
and the ``<style>`` elements in its template. For custom properties it also
counts the ``style`` attributes in its template, the ``--name`` strings in
its ``:style`` and ``c-style`` bindings, its JavaScript, and its Python
module, and the keys its ``css_data()`` returns. A stylesheet linked by URL,
a local file that cannot be read as UTF-8, a source written in another
language through ``css_lang``, and CSS an extension adds while loading are
not read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from citry._browser_expressions import _ascii_lower, _nested_template
from citry._css_scan import CssDeclarations, scan_css, split_class_attribute
from citry._diagnostic_catalog import CSS_MISSPELLED_CLASS, CSS_UNDECLARED_CLASS, CSS_UNDECLARED_VARIABLE
from citry._diagnostics import render_diagnostic
from citry._markup_lint import one_slip_from
from citry.analysis import _css_var_arguments, _skip_css_trivia, _utf8_boundaries
from citry.util.html import decode_attribute_entities
from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttrKind, TemplateElement

if TYPE_CHECKING:
    from collections.abc import Callable, Collection

    from citry_core.template_parser import HtmlAttr, Template

# Tags that render no element of their own, so a class written on them never
# reaches the page: Citry's control tags and Vue's `<template>` and `<slot>`.
_NO_ELEMENT_TAGS = frozenset({*RESERVED_TAG_NAMES, "template", "slot"})

# Bindings whose value Vue or Citry turns into a `style` attribute, where a
# quoted `--name` key sets that custom property.
_STYLE_BINDINGS = frozenset({":style", "v-bind:style", "c-style"})

# A custom property named in code: quoted, as in `{'--progress': value}` in a
# style binding or `style.setProperty("--progress", value)` in JavaScript, or
# followed by a colon inside a string, as in `f"--accent: {color};"` in Python.
_CUSTOM_PROPERTY_IN_CODE = re.compile(r"""["'`]--([A-Za-z0-9_-]+)["'`]|(?<![\w-])--([A-Za-z_][\w-]*)\s*:""")

# A shorter name is too often a different, real class one letter away.
_MIN_CLASS_TYPO_LENGTH = 3

# `{{ ... }}` in a plain attribute, which Citry renders as typed.
# An unclosed `{{` runs to the end of the value.
_WRITTEN_EXPRESSION = re.compile(r"\{\{.*?(?:\}\}|\Z)", re.DOTALL)

# A `<style>` element's `type` or `lang` that names something other than CSS,
# such as `lang="scss"`, which Citry cannot read.
_CSS_STYLE_TYPES = frozenset({"", "css", "text/css"})


@dataclass(frozen=True, slots=True)
class TemplateClass:
    """One class name written in a static ``class`` attribute, with its place in the template."""

    name: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class TemplateCss:
    """
    What one template uses and declares for the CSS rules.

    Attributes:
        classes: Every class in a static ``class`` attribute on an element
            or a component tag, in source order.
        declarations: What the template's ``<style>`` elements declare, plus
            the custom properties its ``style`` attributes set and its
            ``:style`` and ``c-style`` bindings name in quotes.

    """

    classes: tuple[TemplateClass, ...]
    declarations: CssDeclarations


@dataclass(frozen=True, slots=True)
class CssLintFinding:
    """One class or custom property that the CSS Citry reads does not declare."""

    name: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int


def template_css(template: Template, *, parse_nested: Callable[[str], Template]) -> TemplateCss:
    """
    Read the classes a template uses and the CSS it declares.

    In ``class="card {{ kind }}"``, Citry renders the text as written, so
    ``card`` is read and the words inside ``{{ }}`` are left out: they are
    an expression the author meant to bind, not class names. Bound classes
    (``:class``, ``v-bind:class``, ``c-class``) are left out too, because
    their value is known only when the page renders.

    Args:
        template: Parsed Citry template AST.
        parse_nested: Parser for template-valued attributes, so nested
            templates use the same parse options as the outer one.

    Returns:
        The classes, with UTF-8 byte offsets into the template source, and
        the declarations.

    """
    walker = _TemplateCssWalker(parse_nested=parse_nested)
    walker.walk(template, base_index=0)
    declarations = CssDeclarations(custom_properties=frozenset(walker.custom_properties))
    for text in walker.stylesheets:
        declarations = declarations.merged(scan_css(text))
    return TemplateCss(classes=tuple(walker.classes), declarations=declarations)


def code_custom_properties(source: str) -> frozenset[str]:
    """
    Return each custom property that JavaScript or Python source names in a string.

    A name counts when it is quoted on its own, as in ``"--progress"``, or
    followed by a colon, as in ``f"--accent: {color};"``. The source is not
    parsed, so a match outside a string counts too; that only makes the
    rule that uses it quieter.
    """
    return frozenset(match.group(1) or match.group(2) for match in _CUSTOM_PROPERTY_IN_CODE.finditer(source))


def lint_misspelled_css_classes(
    classes: Collection[TemplateClass],
    own: CssDeclarations,
    declared: CssDeclarations,
    *,
    severity: Literal["ignore", "warning", "error"] = "warning",
) -> tuple[CssLintFinding, ...]:
    """
    Report a template class that is one typing slip from a class the component's own CSS styles.

    The slips are those of ``one_slip_from``: two neighboring letters
    swapped, one letter typed twice, or one letter left out. Component CSS is
    not scoped, so any stylesheet, script, or test may use any class name.
    A class is therefore reported only when no CSS Citry reads declares it,
    and only when it is that close to one of the component's own selectors.
    Two near misses are real, different classes too often to report: a slip
    that moves, doubles, or drops a digit, such as ``col-1`` next to
    ``col-12``, and a missing final ``s``, such as ``tab`` next to
    ``tabs``.

    Args:
        classes: The classes in the template's static ``class`` attributes.
        own: What the component's own ``css`` or ``css_file`` declares.
        declared: What every stylesheet Citry reads declares, ``own``
            included.
        severity: ``rule_misspelled_css_class``.

    Returns:
        Findings spanning each misspelled class, in source order.

    """
    if severity == "ignore" or not own.classes:
        return ()
    suggestions = sorted(own.classes)
    findings: list[CssLintFinding] = []
    for item in classes:
        if len(item.name) < _MIN_CLASS_TYPO_LENGTH or declared.declares_class(item.name):
            continue
        suggestion = next((name for name in suggestions if _is_class_typo(item.name, name)), None)
        if suggestion is None:
            continue
        findings.append(
            CssLintFinding(
                name=item.name,
                message=render_diagnostic(CSS_MISSPELLED_CLASS, name=item.name, suggestion=suggestion),
                code=CSS_MISSPELLED_CLASS,
                severity=severity,
                start_index=item.start_index,
                end_index=item.end_index,
            )
        )
    return tuple(findings)


def lint_undeclared_css_classes(
    classes: Collection[TemplateClass],
    declared: CssDeclarations,
    *,
    severity: Literal["ignore", "warning", "error"] = "warning",
    reported: Collection[tuple[int, int]] = (),
) -> tuple[CssLintFinding, ...]:
    """
    Report every template class that no CSS Citry reads declares.

    Args:
        classes: The classes in the template's static ``class`` attributes.
        declared: What every stylesheet Citry reads declares.
        severity: ``rule_undeclared_css_class``.
        reported: The spans another CSS rule already reported, which this
            rule skips so one class gets one finding.

    Returns:
        Findings spanning each class, in source order.

    """
    if severity == "ignore":
        return ()
    skipped = set(reported)
    return tuple(
        CssLintFinding(
            name=item.name,
            message=render_diagnostic(CSS_UNDECLARED_CLASS, name=item.name),
            code=CSS_UNDECLARED_CLASS,
            severity=severity,
            start_index=item.start_index,
            end_index=item.end_index,
        )
        for item in classes
        if (item.start_index, item.end_index) not in skipped and not declared.declares_class(item.name)
    )


def lint_undeclared_css_variables(
    source: str,
    known: Collection[str],
    *,
    severity: Literal["ignore", "warning", "error"] = "warning",
    reported: Collection[tuple[int, int]] = (),
) -> tuple[CssLintFinding, ...]:
    """
    Report every ``var(--name)`` without a fallback in a component's CSS whose property nothing Citry reads sets.

    Args:
        source: The component's own CSS.
        known: Every custom property, without the leading ``--``, that the
            CSS Citry reads sets, that code names, or that a component's
            ``css_data()`` returns.
        severity: ``rule_undeclared_css_variable``.
        reported: The UTF-8 spans another CSS rule already reported, which
            this rule skips so one ``var()`` gets one finding.

    Returns:
        Findings spanning each ``--name``, with UTF-8 byte offsets, in
        source order.

    """
    if severity == "ignore":
        return ()
    skipped = set(reported)
    boundaries = _utf8_boundaries(source)
    findings: list[CssLintFinding] = []
    for name, start, end, terminated in _css_var_arguments(source):
        # An escaped or unterminated name is not one Citry reads exactly.
        if not name or not terminated or name in known:
            continue
        # `var(--name, fallback)` still has a value when nothing sets --name.
        after = _skip_css_trivia(source, end)
        if source[after : after + 1] != ")":
            continue
        span = (boundaries[start], boundaries[end])
        if span in skipped:
            continue
        findings.append(
            CssLintFinding(
                name=name,
                message=render_diagnostic(CSS_UNDECLARED_VARIABLE, name=name),
                code=CSS_UNDECLARED_VARIABLE,
                severity=severity,
                start_index=span[0],
                end_index=span[1],
            )
        )
    return tuple(findings)


class _TemplateCssWalker:
    """Visit every element once and collect its classes, style text, and style bindings."""

    def __init__(self, *, parse_nested: Callable[[str], Template]) -> None:
        self.parse_nested = parse_nested
        self.classes: list[TemplateClass] = []
        self.stylesheets: list[str] = []
        self.custom_properties: set[str] = set()

    def walk(self, template: Template, *, base_index: int) -> None:
        for element in template.elements:
            if not isinstance(element, TemplateElement.Node):
                continue
            node = element._0
            lower = _ascii_lower(node.start_tag.name.content)
            for attr in node.start_tag.attrs:
                inner = attr.inner_value
                if inner is None:
                    continue
                # A template-valued attribute holds more HTML, whose offsets
                # are relative to the nested source.
                if attr.kind == HtmlAttrKind.Template:
                    nested = _nested_template(inner.content, self.parse_nested)
                    if nested is not None:
                        parsed, nested_start = nested
                        self.walk(parsed, base_index=base_index + inner.start_index + nested_start)
                    continue
                key = _ascii_lower(attr.key.content)
                if key in _STYLE_BINDINGS:
                    self.custom_properties.update(code_custom_properties(inner.content))
                    continue
                # An attribute written in an extension's syntax may render as
                # anything, so only plain text is read.
                if attr.kind != HtmlAttrKind.Static or attr.foreign_parts:
                    continue
                if key == "style":
                    # A type selector wraps the declarations so they read as one
                    # rule without adding a class.
                    self.stylesheets.append(f"a{{{decode_attribute_entities(inner.content)}}}")
                # A `class` on a component tag is an input, which the component
                # usually puts on one of its elements, so it is read too.
                elif key == "class" and lower not in _NO_ELEMENT_TAGS:
                    self._record_classes(inner.content, base_index + inner.start_index)
            body = getattr(node, "body", None)
            if body is None:
                continue
            if lower == "style":
                if not _holds_css(node.start_tag.attrs):
                    continue
                # Only the literal text is CSS Citry can read; an expression
                # inside the element is known only when the page renders.
                self.stylesheets.append(
                    "".join(item._0.token.content for item in body.elements if isinstance(item, TemplateElement.Text))
                )
                continue
            self.walk(body, base_index=base_index)

    def _record_classes(self, written: str, value_start: int) -> None:
        # Citry renders `{{ }}` in a plain attribute as written, so the words
        # around it are real classes, but the words inside are an expression
        # the author meant to bind.
        expressions = [match.span() for match in _WRITTEN_EXPRESSION.finditer(written)]
        for raw, start, end in split_class_attribute(written):
            if any(
                start < expression_end and end > expression_start for expression_start, expression_end in expressions
            ):
                continue
            # A stray `}}` is part of a broken expression too.
            if "{{" in raw or "}}" in raw:
                continue
            name = decode_attribute_entities(raw)
            # A character reference can stand for whitespace, which would
            # make this two classes; such a value is not worth guessing at.
            if not name or any(char in name for char in " \t\n\f\r"):
                continue
            self.classes.append(
                TemplateClass(
                    name=name,
                    start_index=value_start + len(written[:start].encode("utf-8")),
                    end_index=value_start + len(written[:end].encode("utf-8")),
                )
            )


def _is_class_typo(written: str, expected: str) -> bool:
    """
    Return whether a template class is a typing slip of a class the component's CSS styles.

    A slip that moves, doubles, or drops a digit, such as ``col-1`` for
    ``col-12``, and a missing final ``s``, such as ``tab`` for ``tabs``,
    usually name a different class of the same family, so they do not
    count.
    """
    if not one_slip_from(written, expected):
        return False
    if _without_digits(written) == _without_digits(expected):
        return False
    return expected != f"{written}s"


def _without_digits(name: str) -> str:
    return "".join(char for char in name if not char.isdigit())


def style_type_is_css(value: str) -> bool:
    """Return whether a ``<style>`` element's ``type`` or ``lang`` value, entities decoded, names CSS."""
    return _ascii_lower(value) in _CSS_STYLE_TYPES


def _holds_css(attrs: Collection[HtmlAttr]) -> bool:
    """Return whether a ``<style>`` element holds CSS, not a language such as ``lang="scss"``."""
    for attr in attrs:
        key = _ascii_lower(attr.key.content)
        name = key.removeprefix("v-bind:").removeprefix(":").removeprefix("c-")
        if name not in {"type", "lang"}:
            continue
        # A bound `type` or `lang` is known only when the page renders.
        if name != key or attr.kind != HtmlAttrKind.Static:
            return False
        # A bare `<style type>` is CSS, as it is for the browser.
        value = "" if attr.inner_value is None else decode_attribute_entities(attr.inner_value.content)
        if not style_type_is_css(value):
            return False
    return True
