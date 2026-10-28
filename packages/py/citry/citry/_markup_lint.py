"""
Lint rules that read a template's HTML elements and attributes.

These rules need nothing but the parsed template, so ``citry check --static``
and an editor that has not loaded the application run them too. One walk over
the elements serves every rule, because several of them need to know what
surrounds an element: an open ``<p>``, an enclosing condition or loop, or an
``<svg>`` subtree.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from difflib import get_close_matches
from typing import TYPE_CHECKING, Any, Literal

from citry._browser_expressions import (
    BrowserExpression,
    BrowserSyntaxError,
    _ascii_lower,
    _nested_template,
    _tokens,
    analyze_browser_expression,
)
from citry._diagnostic_catalog import (
    BROWSER_INVALID_MODEL_TARGET,
    TEMPLATE_CSP_INCOMPATIBLE,
    TEMPLATE_DUPLICATE_ID,
    TEMPLATE_INVALID_NESTING,
    TEMPLATE_MISSING_IMAGE_ALT,
    TEMPLATE_MISSPELLED_ATTRIBUTE,
    TEMPLATE_MISSPELLED_ELEMENT,
    TEMPLATE_UNKNOWN_ARIA_ATTRIBUTE,
    VUE_INVALID_EXPRESSION,
    VUE_MISSPELLED_EVENT,
)
from citry._diagnostics import render_diagnostic
from citry._html_attribute_values import (
    ARIA_ATTRIBUTES,
    DOM_EVENT_NAMES,
    ELEMENT_ATTRIBUTES,
    GLOBAL_ATTRIBUTES,
    HTML_ELEMENTS,
    OBSOLETE_ELEMENTS,
    SVG_ELEMENTS,
)
from citry._output_policy import check_output_html
from citry._walk import Call, run
from citry.settings import _ALLOWED_SECURITY_CSP_MODES
from citry.util.html import decode_attribute_entities
from citry_core.html_transform import _csp_attribute_problem
from citry_core.template_parser import HtmlAttr, HtmlAttrKind, TemplateElement
from citry_core.template_parser import parse_template as _parse_template

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence

    from citry.settings import SecurityCspMode
    from citry_core.template_parser import Template

_Severity = Literal["ignore", "warning", "error"]
_SEVERITIES = frozenset({"ignore", "warning", "error"})
# The key of the strict-CSP rule among the active severities. It is not a
# `rule_*` field, because the engine's `security_csp` sets its severity.
_CSP_RULE = "csp"


@dataclass(frozen=True, slots=True)
class MarkupLintConsumer:
    """
    Carry one consuming component's severities for the rules that read a template's HTML.

    Each field takes ``"ignore"``, ``"warning"``, or ``"error"``, and its
    default matches the ``LintSettings`` field of the same name.

    Attributes:
        rule_misspelled_attribute: An attribute name one typing slip from an
            attribute its HTML element accepts, such as ``titel``.
        rule_misspelled_element: A lowercase tag one typing slip from an HTML
            element, such as ``<dvi>``.
        rule_unknown_aria_attribute: An ``aria-*`` name that ARIA does not
            define, such as ``aria-expandd``.
        rule_invalid_nesting: An element that the browser moves out of an
            open ``<p>``, such as ``<div>`` inside ``<p>``.
        rule_duplicate_id: A literal ``id`` that two elements of one template
            always render.
        rule_missing_image_alt: An ``<img>`` with no ``alt`` text.
        rule_invalid_model_target: ``v-model`` on an element that holds no
            value, such as ``<form>``.
        rule_misspelled_event: A listener on an HTML element whose event name
            is one typing slip from a DOM event, such as ``@clik``.
        rule_invalid_vue_expression: A Vue expression, such as the value of
            ``v-if`` or ``@click``, that is not valid JavaScript.
        rule_vue_compile_error: Anything else Vue's compiler rejects in the
            template, such as a ``<div>`` directly inside a ``<table>``.
        root_may_receive_attributes: Whether a parent's attributes may reach
            the component's single root element. Vue passes them there for a
            component with browser code, unless its JavaScript sets
            ``inheritAttrs: false``, so an ``<img>`` root may get its ``alt``
            from the parent. The default, ``True``, is for a check that
            cannot tell.
        csp: The engine's ``security_csp``. ``"warn"`` and ``"strict"``
            report, as a warning or an error, what a strict Content Security
            Policy blocks: a raw ``<script>`` or ``<style>``, an ``on*``
            attribute, or a ``javascript:`` URL. The default, ``"off"``,
            reports nothing, as the engine's own default does.

    """

    rule_misspelled_attribute: _Severity = "error"
    rule_misspelled_element: _Severity = "error"
    rule_unknown_aria_attribute: _Severity = "error"
    rule_invalid_nesting: _Severity = "error"
    rule_duplicate_id: _Severity = "error"
    rule_missing_image_alt: _Severity = "warning"
    rule_invalid_model_target: _Severity = "error"
    rule_misspelled_event: _Severity = "warning"
    rule_invalid_vue_expression: _Severity = "error"
    rule_vue_compile_error: _Severity = "error"
    root_may_receive_attributes: bool = True
    csp: SecurityCspMode = "off"

    def __post_init__(self) -> None:
        for rule_name in MARKUP_LINT_RULES:
            severity = getattr(self, rule_name)
            if type(severity) is not str or severity not in _SEVERITIES:
                msg = f"Unknown {rule_name} severity: {severity!r}"
                raise ValueError(msg)
        if type(self.root_may_receive_attributes) is not bool:
            msg = "MarkupLintConsumer.root_may_receive_attributes must be a bool"
            raise TypeError(msg)
        if type(self.csp) is not str or self.csp not in _ALLOWED_SECURITY_CSP_MODES:
            msg = f"Unknown csp mode: {self.csp!r}"
            raise ValueError(msg)


# The severity fields of MarkupLintConsumer, in the order the LintSettings
# docstring lists them.
MARKUP_LINT_RULES = (
    "rule_misspelled_attribute",
    "rule_misspelled_element",
    "rule_unknown_aria_attribute",
    "rule_invalid_nesting",
    "rule_duplicate_id",
    "rule_missing_image_alt",
    "rule_invalid_model_target",
    "rule_misspelled_event",
    "rule_invalid_vue_expression",
    "rule_vue_compile_error",
)


@dataclass(frozen=True, slots=True)
class MarkupLintFinding:
    """
    Report one mistake in a template's HTML, spanning the name or value it is about.

    ``context_start_index`` and ``context_end_index`` are set when the finding
    spans only part of a value, such as the token where a Vue expression stops
    parsing: they span the whole expression, so a check that hides a second
    report of the same mistake can still match it.
    """

    name: str
    message: str
    code: str
    severity: Literal["warning", "error"]
    start_index: int
    end_index: int
    context_start_index: int | None = None
    context_end_index: int | None = None


def lint_markup(
    template: Template,
    consumers: Sequence[MarkupLintConsumer],
    *,
    parse_nested: Callable[[str], Template] = _parse_template,
) -> tuple[MarkupLintFinding, ...]:
    """
    Report mistakes in a template's HTML that the browser or Vue does not report, or reports only at runtime.

    The rules, each with its own severity in ``MarkupLintConsumer``:

    - a misspelled attribute name, such as ``titel`` for ``title``;
    - a misspelled element, such as ``<dvi>``;
    - an ``aria-*`` name that ARIA does not define;
    - an element the browser moves out of an open ``<p>``, such as ``<div>``;
    - a literal ``id`` that two elements always render;
    - an ``<img>`` with no ``alt`` text;
    - ``v-model`` on an element that holds no value;
    - a misspelled DOM event in a listener, such as ``@clik``;
    - when a consumer's ``csp`` is not ``"off"``, what a strict Content
      Security Policy blocks.

    A typing slip is two neighboring letters swapped, one letter typed
    twice, or one letter left out. A replaced letter does not count, because
    it mostly gives another real word.

    A finding is reported unless every consumer ignores its rule, and it is
    an error when any reporting consumer says ``"error"``. With an empty
    ``consumers``, which ``citry check --static`` and an editor that has not
    loaded the application pass for a template whose owner they cannot find,
    each rule uses its default.

    Args:
        template: Parsed Citry template AST.
        consumers: Every component known to render this template.
        parse_nested: Parser for template-valued attributes, so nested
            templates use the same parse options as the outer one.

    Returns:
        Findings in source order.

    """
    effective = tuple(consumers) or (MarkupLintConsumer(),)
    severities = _active_severities(effective)
    if not severities:
        return ()
    walker = _MarkupWalker(
        severities=severities,
        parse_nested=parse_nested,
        # A shared template keeps its root `<img>` unreported when any owner
        # may hand it an `alt`, because the check cannot tell which owner
        # renders it.
        root_may_receive_attributes=any(consumer.root_may_receive_attributes for consumer in effective),
    )
    walker.walk_template(template, base_index=0)
    return tuple(sorted(walker.found, key=lambda item: (item.start_index, item.end_index)))


# A consumer that turns on only the `v-model` target rule. Every other rule
# is listed as ignored, so a rule added later stays off here too.
_MODEL_TARGET_ONLY = MarkupLintConsumer(
    **(dict.fromkeys(MARKUP_LINT_RULES, "ignore") | {"rule_invalid_model_target": "error"}),  # type: ignore[arg-type]
)


def find_invalid_model_targets(
    template: Template,
    *,
    parse_nested: Callable[[str], Template] = _parse_template,
) -> tuple[MarkupLintFinding, ...]:
    """
    Return every ``v-model`` on an element that holds no value, as ``rule_invalid_model_target`` finds them.

    A render whose Vue compile fails on such a ``v-model`` uses this to name
    the element, so the runtime error names the same elements the static
    rule reports.

    Args:
        template: Parsed Citry template AST.
        parse_nested: Parser for template-valued attributes.

    Returns:
        Findings in source order, each spanning the ``v-model`` attribute
        name, with byte offsets into the template source.

    """
    return lint_markup(template, (_MODEL_TARGET_ONLY,), parse_nested=parse_nested)


def lint_invalid_vue_expressions(
    template: Template,
    expressions: Sequence[BrowserExpression],
    consumers: Sequence[MarkupLintConsumer],
    *,
    parse_nested: Callable[[str], Template] = _parse_template,
) -> tuple[MarkupLintFinding, ...]:
    """
    Report Vue expressions that are not valid JavaScript, such as ``v-if="open &&"``.

    Vue compiles the template in the browser, or when Citry renders it, and a
    syntax error there stops the page. This check parses each expression with
    the same JavaScript parser the other Vue rules use, after decoding
    character references such as ``&amp;&amp;`` the way Vue does. A listener
    such as ``@click`` may hold statements or a function expression. The
    arguments of a server call such as ``@c-click="save({...})"`` are checked
    too.

    Skipped: a valueless ``:title``, which Vue 3.4 and later read as
    ``:title="title"``; everything inside an element with ``v-pre``, which
    Vue never compiles, while Citry's own bindings on that element are still
    checked; a dynamic slot name; and the value of a custom
    directive, which Citry does not read, although Vue still fails on one
    that is not valid JavaScript.

    Args:
        template: Parsed Citry template AST, used to find ``v-pre`` elements.
        expressions: The template's browser expressions, from
            ``browser_expressions``.
        consumers: Every component known to render this template.
        parse_nested: Parser for template-valued attributes, so nested
            templates use the same parse options as the outer one.

    The finding names the parser's error and spans the place it points to,
    such as the end of ``open &&``. It spans the whole expression, with a
    message that names no parser error, when the parser gives no position,
    or when the expression holds a character reference that Vue decodes,
    because positions in the decoded text do not match the template.

    Returns:
        Findings in source order, each with ``context_start_index`` and
        ``context_end_index`` spanning the whole expression.

    """
    severity = _active_severities(tuple(consumers) or (MarkupLintConsumer(),)).get("rule_invalid_vue_expression")
    if severity is None:
        return ()
    unchecked = run(_v_pre_ranges(template, parse_nested=parse_nested, base_index=0))
    found: list[MarkupLintFinding] = []
    for expression in expressions:
        if expression.transform == "dynamic-slot":
            continue
        # `:title` with no value is Vue's same-name shorthand, and `v-on=""`
        # or `v-bind=""` bind nothing. A value of only spaces is an error.
        if not expression.source and expression.mode == "expression":
            continue
        if any(start <= expression.start_index < end for start, end in unchecked):
            continue
        valid, error = _vue_expression_error(expression)
        if valid:
            continue
        if error is None:
            message = render_diagnostic(VUE_INVALID_EXPRESSION, attribute=expression.attribute)
            start_index, end_index = expression.start_index, expression.end_index
        else:
            message = render_diagnostic(
                VUE_INVALID_EXPRESSION,
                variant="parser",
                attribute=expression.attribute,
                detail=error.message,
            )
            start_index, end_index = _visible_error_range(expression, error)
        found.append(
            MarkupLintFinding(
                name=expression.attribute,
                message=message,
                code=VUE_INVALID_EXPRESSION,
                severity=severity,
                start_index=start_index,
                end_index=end_index,
                context_start_index=expression.start_index,
                context_end_index=expression.end_index,
            )
        )
    return tuple(sorted(found, key=lambda item: (item.start_index, item.end_index)))


def _vue_expression_error(expression: BrowserExpression) -> tuple[bool, BrowserSyntaxError | None]:
    """
    Return whether Vue can compile one expression, and when it cannot, the parser's error to report.

    The expression is valid when it parses as written or after Vue decodes
    its character references. The error is the one in the text as written,
    so its position is a template position. A listener is parsed both as
    statements and as an expression, and the error from the parse that got
    further is reported, so a broken ``function () {...}`` listener is not
    blamed for a missing function name. The error is ``None`` when decoding
    changes the text, because the
    as-written error may then point into a reference the author wrote
    correctly, and when the analysis has no parser error to give.
    """
    candidates = [expression]
    decoded = decode_attribute_entities(expression.source) if "&" in expression.source else expression.source
    # Vue decodes `&gt;` and the like before it parses the expression, so a
    # template may write `a &gt; b` for `a > b`.
    if decoded != expression.source:
        candidates.append(replace(expression, source=decoded))
    as_written: BrowserSyntaxError | None = None
    for candidate in candidates:
        analysis = analyze_browser_expression(candidate)
        if analysis.valid:
            return True, None
        errors = [analysis.error]
        # Vue also accepts a function expression or an arrow function as a
        # listener, which is not a statement on its own.
        if candidate.mode == "statement":
            as_expression = analyze_browser_expression(replace(candidate, mode="expression"))
            if as_expression.valid:
                return True, None
            errors.append(as_expression.error)
        if candidate is expression:
            # The parse that got further read more of what the author meant.
            found = [error for error in errors if error is not None]
            as_written = max(found, key=lambda error: error.start_index, default=None)
    if decoded != expression.source:
        return False, None
    return False, as_written


def _visible_error_range(expression: BrowserExpression, error: BrowserSyntaxError) -> tuple[int, int]:
    """
    Return a non-empty template range for a parser error inside one expression.

    An error at the end of the text, as in ``open &&``, has an empty range,
    which an editor would not underline, so it moves back to the last token
    the author wrote before it, skipping spaces and comments; a punctuation
    token is one character, so ``open &&`` underlines its last ``&``. An
    expression with no token spans itself.
    """
    if error.start_index < error.end_index:
        return error.start_index, error.end_index
    encoded = expression.source.encode("utf-8")
    # Parser offsets fall on character boundaries, so the prefix decodes.
    written = encoded[: error.start_index - expression.start_index].decode("utf-8")
    tokens = _tokens(written)
    if not tokens:
        return expression.start_index, expression.end_index
    last = tokens[-1]
    text = last.source
    # The tokenizer does not know regular expressions, so a quote inside
    # one, as in `a.match(/'/) &&`, starts a string that never ends; the
    # last character written is then the safer place to point.
    if last.kind == "string" and (len(text) < 2 or text[-1] != text[0]):
        stripped = written.rstrip()
        text = stripped[-1]
        start = expression.start_index + len(stripped[:-1].encode("utf-8"))
        return start, start + len(text.encode("utf-8"))
    start = expression.start_index + len(written[: last.start].encode("utf-8"))
    return start, start + len(text.encode("utf-8"))


def _v_pre_ranges(
    template: Template,
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> Generator[Call, Any, list[tuple[int, int]]]:
    """
    Return the source ranges of the contents of elements with ``v-pre``, which Vue leaves as written.

    A range starts after the element's start tag. Citry still renders the
    ``@c-*`` and ``$c-tr`` bindings on the ``v-pre`` element itself, so those
    are still checked, while the render refuses them inside the contents.
    """
    ranges: list[tuple[int, int]] = []
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        if any(_ascii_lower(attr.key.content) == "v-pre" for attr in node.start_tag.attrs):
            end_tag = getattr(node, "end_tag", None)
            end = end_tag.token.end_index if end_tag is not None else node.start_tag.token.end_index
            ranges.append((base_index + node.start_tag.token.end_index, base_index + end))
            continue
        for attr in node.start_tag.attrs:
            inner = attr.inner_value
            if attr.kind == HtmlAttrKind.Template and inner is not None:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    ranges.extend(
                        (
                            yield Call(
                                _v_pre_ranges,
                                parsed,
                                parse_nested=parse_nested,
                                base_index=base_index + inner.start_index + nested_start,
                            )
                        )
                    )
        body = getattr(node, "body", None)
        if body is not None:
            ranges.extend((yield Call(_v_pre_ranges, body, parse_nested=parse_nested, base_index=base_index)))
    return ranges


def _active_severities(consumers: Sequence[MarkupLintConsumer]) -> dict[str, Literal["warning", "error"]]:
    """
    Return each rule's severity across the consumers, leaving out the rules they all ignore.

    A shared template is reported when any owner reports the rule, as an
    error when any owner says ``"error"``.
    """
    severities: dict[str, Literal["warning", "error"]] = {}
    for rule_name in MARKUP_LINT_RULES:
        active = [getattr(consumer, rule_name) for consumer in consumers]
        active = [severity for severity in active if severity != "ignore"]
        if active:
            severities[rule_name] = "error" if "error" in active else "warning"
    # The engine's policy decides the strict-CSP rule: an error when any
    # owner's engine is strict, a warning when one only warns.
    modes = {consumer.csp for consumer in consumers}
    if "strict" in modes:
        severities[_CSP_RULE] = "error"
    elif "warn" in modes:
        severities[_CSP_RULE] = "warning"
    return severities


# Vue's built-in components that a template writes as lowercase tags. They
# are not HTML elements, but they are not typos either.
_VUE_BUILTIN_TAGS = frozenset(
    {"component", "keep-alive", "slot", "suspense", "teleport", "template", "transition", "transition-group"},
)
# Every lowercase tag that names a real element outside `<math>`. SVG names
# are here because a component's root can be `<path>`, and obsolete names
# because `<frame>` is one letter short of `<iframe>`. MathML names are left
# out: outside `<math>` the browser does not treat them as MathML, and
# `<min>`, a MathML content element, is more likely a typo of `<main>`.
_KNOWN_LOWERCASE_TAGS = frozenset(
    {
        *HTML_ELEMENTS,
        *(_ascii_lower(name) for name in SVG_ELEMENTS),
        *OBSOLETE_ELEMENTS,
        *_VUE_BUILTIN_TAGS,
    }
)

# Start tags that close an open `<p>` (WHATWG HTML 13.2.6.4.7, "in body"), so
# the browser moves them, and everything after them, out of the paragraph.
# `table` closes it only in no-quirks mode, which `<!DOCTYPE html>` selects.
_P_CLOSING_TAGS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "center",
        "dd",
        "details",
        "dialog",
        "dir",
        "div",
        "dl",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hgroup",
        "hr",
        "li",
        "listing",
        "main",
        "menu",
        "nav",
        "ol",
        "p",
        "plaintext",
        "pre",
        "search",
        "section",
        "summary",
        "table",
        "ul",
        "xmp",
    }
)
# Elements that hide an open `<p>` from what they contain ("button scope" in
# the same section): a `<div>` inside `<p><button>` closes nothing. When
# scripts run, the browser reads `<noscript>` content as text.
_P_SCOPE_BOUNDARIES = frozenset(
    {"applet", "button", "caption", "html", "marquee", "noscript", "object", "table", "td", "template", "th"},
)
# Citry tags whose body renders in place, so an open `<p>` around them stays
# open around their content: conditions, loops, and a slot's fallback.
_IN_PLACE_TAGS = frozenset({"c-if", "c-elif", "c-else", "c-for", "c-empty", "c-slot"})
# Citry tags and directives whose content may render zero or several times,
# so an `id` inside them is not known to appear exactly once.
_REPEATING_OR_CONDITIONAL_TAGS = frozenset({"c-if", "c-elif", "c-else", "c-for", "c-empty", "c-fill", "c-slot"})
_REPEATING_OR_CONDITIONAL_ATTRIBUTES = frozenset(
    {"c-if", "c-elif", "c-else", "c-for", "c-empty", "v-if", "v-else-if", "v-else", "v-for"},
)
# The Citry ones among them, which still apply under `v-pre`, because Citry
# renders the element before Vue sees it.
_CITRY_REPEATING_OR_CONDITIONAL_ATTRIBUTES = frozenset({"c-if", "c-elif", "c-else", "c-for", "c-empty"})
# Names Vue reads on any element besides the HTML attributes.
_VUE_SPECIAL_ATTRIBUTES = frozenset({"key", "ref", "ref_for", "ref_key", "is"})
# The elements `v-model` can read a value from. A component tag and
# `<c-element>` are allowed too, because they decide for themselves.
_MODEL_TARGETS = frozenset({"input", "select", "textarea"})
# Words that are one typing slip from a DOM event but are ordinary custom
# event names, such as `scrolled` for `scrollend`.
_EVENT_LOOKALIKE_WORDS = frozenset({"scrolled", "touched"})
# A name this short is too likely to be another word to read as a typo.
_MIN_TYPO_LENGTH = 3
# Elements whose content the page's CSP check reads as text, as the browser
# does, so the tags written inside them are not checked here either.
_CSP_TEXT_CONTENT_TAGS = frozenset({"noscript", "xmp", "iframe", "noembed", "noframes", "plaintext"})
# Element names the browser knows in any letter case. A capitalized tag with
# one of these names is that element; any other may be a Vue component.
_CSP_ELEMENT_TAGS = _KNOWN_LOWERCASE_TAGS - _VUE_BUILTIN_TAGS


@dataclass(slots=True)
class _Context:
    """What surrounds the elements being visited."""

    # Inside `<svg>` or `<math>`, whose elements and attributes are not HTML.
    foreign: bool = False
    # An open `<p>` that a block element would close.
    in_paragraph: bool = False
    # Inside a condition, loop, fill, slot fallback, component body, or
    # `<template>`, so the content may render zero or several times.
    may_repeat: bool = False
    # On or inside an element with `v-pre`, which Vue leaves as written, so
    # the rules about Vue directives and listeners do not apply.
    vue_skipped: bool = False
    # Inside an element whose content the browser reads as text, such as
    # `<noscript>`, so the page check sees no tags there.
    csp_hidden: bool = False


@dataclass(slots=True)
class _MarkupWalker:
    """Visit every element once and run each active rule on it."""

    severities: dict[str, Literal["warning", "error"]]
    parse_nested: Callable[[str], Template]
    root_may_receive_attributes: bool
    found: list[MarkupLintFinding] = field(default_factory=list)
    # The first element that always renders each literal id.
    first_ids: dict[str, int] = field(default_factory=dict)

    def walk_template(self, template: Template, *, base_index: int) -> None:
        """Visit one template; a nested template starts with nothing open around it."""
        run(self._walk(template, _Context(), base_index=base_index, roots=run(_single_root_starts(template))))

    def _walk(
        self,
        template: Template,
        context: _Context,
        *,
        base_index: int,
        roots: frozenset[int] = frozenset(),
    ) -> Generator[Call, Any, None]:
        for element in template.elements:
            if not isinstance(element, TemplateElement.Node):
                continue
            node = element._0
            tag = node.start_tag.name.content
            lower = _ascii_lower(tag)
            attrs = node.start_tag.attrs
            names = {_ascii_lower(attr.key.content) for attr in attrs}
            foreign = context.foreign or lower in {"svg", "math"}
            vue_skipped = context.vue_skipped or "v-pre" in names
            html = not foreign and tag in HTML_ELEMENTS
            # A lowercase tag with a hyphen is a custom element; `c-*` tags are
            # Citry tags and PascalCase tags are Vue components. Under `v-pre`
            # Vue resolves no component, so a PascalCase tag is a plain element.
            custom = not foreign and _is_custom_element(tag)
            component = not foreign and (
                (tag != lower and not vue_skipped) or (lower.startswith("c-") and lower != "c-element")
            )
            if not foreign:
                self._check_element_name(node, tag, base_index)
            # `v-pre` does not hide anything here: Vue still sets the
            # attributes it leaves as written, and the browser applies them.
            if not context.csp_hidden:
                self._check_csp_element(node, tag, lower, attrs, component=component, base_index=base_index)
            # Obsolete block elements such as `<center>` close a paragraph too.
            block = not foreign and (html or tag in OBSOLETE_ELEMENTS)
            if block and context.in_paragraph and lower in _P_CLOSING_TAGS:
                self._report(
                    "rule_invalid_nesting",
                    TEMPLATE_INVALID_NESTING,
                    tag,
                    render_diagnostic(TEMPLATE_INVALID_NESTING, tag=tag),
                    node.start_tag.name.start_index,
                    node.start_tag.name.end_index,
                    base_index,
                )
            # Under `v-pre`, Vue leaves `v-if` and `v-for` as written, so both
            # branches of a `v-if`/`v-else` are on the page; only Citry's own
            # `c-if` and `c-for` still choose or repeat an element there.
            conditional = (
                _CITRY_REPEATING_OR_CONDITIONAL_ATTRIBUTES if vue_skipped else _REPEATING_OR_CONDITIONAL_ATTRIBUTES
            )
            may_repeat = (
                context.may_repeat
                or lower in _REPEATING_OR_CONDITIONAL_TAGS
                or lower == "template"
                or bool(names & conditional)
                or (component and lower not in _IN_PLACE_TAGS)
            )
            for attr in attrs:
                # Under `v-pre`, `:titl` is an attribute literally named `:titl`,
                # not a binding of `titl`, so only plain and `c-` names are checked.
                plain_name = not (vue_skipped and attr.key.content.startswith((":", "v-bind:")))
                if not component and plain_name:
                    self._check_aria_attribute(attr, base_index)
                if html and plain_name:
                    self._check_attribute_name(tag, attr, base_index)
                if html and not vue_skipped:
                    self._check_event_name(attr, base_index)
                if (html or custom) and not vue_skipped:
                    self._check_model_target(tag, lower, attr, base_index)
                if not may_repeat:
                    self._record_id(attr, base_index)
                # A template-valued attribute holds more HTML, whose offsets
                # are relative to the nested source, so shift them into this
                # template. It renders apart from this element.
                inner = attr.inner_value
                if attr.kind == HtmlAttrKind.Template and inner is not None:
                    nested = _nested_template(inner.content, self.parse_nested)
                    if nested is not None:
                        parsed, nested_start = nested
                        yield Call(
                            self._walk,
                            parsed,
                            _Context(
                                foreign=foreign,
                                may_repeat=True,
                                vue_skipped=vue_skipped,
                                # Where a nested template's HTML lands is up
                                # to the code that renders it, so the
                                # render-time check judges it.
                                csp_hidden=True,
                            ),
                            base_index=base_index + inner.start_index + nested_start,
                        )
            if (
                html
                and lower == "img"
                and not (node.start_tag.token.start_index in roots and self.root_may_receive_attributes)
            ):
                self._check_image_alt(node, names, attrs, base_index)
            body = getattr(node, "body", None)
            if body is not None:
                yield Call(
                    self._walk,
                    body,
                    _Context(
                        foreign=foreign,
                        in_paragraph=self._paragraph_stays_open(context, lower, html=html, component=component)
                        and not foreign,
                        may_repeat=may_repeat,
                        vue_skipped=vue_skipped,
                        csp_hidden=context.csp_hidden or lower in _CSP_TEXT_CONTENT_TAGS,
                    ),
                    base_index=base_index,
                    # A root inside a top-level condition is still the
                    # element Vue passes a parent's attributes to.
                    roots=roots,
                )

    @staticmethod
    def _paragraph_stays_open(context: _Context, lower: str, *, html: bool, component: bool) -> bool:
        """Return whether a `<p>` is open around this element's content."""
        if html and lower == "p":
            return True
        if not context.in_paragraph:
            return False
        if lower in _IN_PLACE_TAGS:
            return True
        # A component renders markup the check cannot see, and an element
        # that closes the paragraph is already reported.
        return not (component or lower == "c-element" or lower in _P_SCOPE_BOUNDARIES or lower in _P_CLOSING_TAGS)

    def _check_csp_element(
        self,
        node: object,
        tag: str,
        lower: str,
        attrs: Sequence[HtmlAttr],
        *,
        component: bool,
        base_index: int,
    ) -> None:
        """Report what a strict Content Security Policy blocks in one element's own text."""
        if _CSP_RULE not in self.severities:
            return
        # `<c-raw>` writes its content out unchanged, so that content is
        # read as the HTML the browser gets.
        if lower == "c-raw":
            self._check_csp_raw_content(node, base_index)
            return
        # A component's attributes are inputs, not HTML, so only the
        # render-time check can see what the component writes. The browser
        # ignores letter case in tag names, so `<BUTTON>` and `<Script>` are
        # the HTML elements; only a capitalized name that is no element,
        # such as `<Card>`, may be a Vue component.
        element_tag = tag
        if lower == "c-element":
            # `<c-element is="object">` renders an `<object>`, so the rules
            # that depend on the element use the name `is` gives as text.
            written_is = next(
                (
                    attr.inner_value.content
                    for attr in attrs
                    if attr.kind == HtmlAttrKind.Static
                    and not attr.foreign_parts
                    and _ascii_lower(attr.key.content) == "is"
                    and attr.inner_value is not None
                ),
                None,
            )
            # The value is used as written, as the template compiler reads it.
            element_tag = written_is if written_is is not None else tag
        elif component and (lower.startswith("c-") or lower not in _CSP_ELEMENT_TAGS):
            return
        name = node.start_tag.name  # type: ignore[attr-defined]
        if _ascii_lower(element_tag) in {"script", "style"}:
            self._report(
                _CSP_RULE,
                TEMPLATE_CSP_INCOMPATIBLE,
                tag,
                render_diagnostic(TEMPLATE_CSP_INCOMPATIBLE, variant="raw-tag", tag=element_tag),
                name.start_index,
                name.end_index,
                base_index,
            )
        for attr in attrs:
            # Only an attribute with a fixed value is known before the page
            # renders. A binding, a directive, and a listener are not plain
            # attributes. Their names start with a prefix such as `c-`,
            # `:`, `@`, `v-`, `#`, or `$`; any other name is the attribute
            # the browser gets, even one with a dot such as `onclick.x`.
            if attr.kind != HtmlAttrKind.Static:
                continue
            written = attr.key.content
            if written.startswith(("c-", ":", "@", "v-", "#", "$", ".", "[")):
                continue
            inner = attr.inner_value
            # The value goes in as written, character references and all,
            # because the shared rule decodes it as the page check does.
            problem = _csp_attribute_problem(element_tag, written, None if inner is None else inner.content)
            if problem is None:
                continue
            # A value that holds extension syntax is known only after the
            # extension runs, so only the name, which decides an event
            # handler, can be judged here.
            if problem == "javascript-url" and attr.foreign_parts:
                continue
            # A javascript: URL is in the value; an event handler is the name.
            start, end = (
                (inner.start_index, inner.end_index)
                if problem == "javascript-url" and inner is not None
                else (attr.key.start_index, attr.key.end_index)
            )
            self._report(
                _CSP_RULE,
                TEMPLATE_CSP_INCOMPATIBLE,
                written,
                render_diagnostic(TEMPLATE_CSP_INCOMPATIBLE, variant=problem, name=written),
                start,
                end,
                base_index,
            )

    def _check_csp_raw_content(self, node: object, base_index: int) -> None:
        """Report what a strict Content Security Policy blocks in ``<c-raw>`` content, using the page check."""
        body = getattr(node, "body", None)
        if body is None:
            return
        for element in body.elements:
            if not isinstance(element, TemplateElement.Text):
                continue
            token = element._0.token
            check = check_output_html(token.content, csp=True)
            written_bytes = token.content.encode()
            # Content the page check cannot read is reported when the page
            # renders, with the reason, so nothing is guessed here.
            if check.error is not None:
                continue
            for event in check.events:
                # Offsets in the events are UTF-8 bytes into the content, as
                # the template's own offsets are bytes into the template.
                if event[0] == "element":
                    _, _, _, name_start, name_end, _, trusted, *_ = event
                    if trusted:
                        continue
                    # The page check names elements in lowercase; the
                    # message shows the name as the template writes it.
                    raw_tag = written_bytes[name_start:name_end].decode()
                    self._report(
                        _CSP_RULE,
                        TEMPLATE_CSP_INCOMPATIBLE,
                        raw_tag,
                        render_diagnostic(TEMPLATE_CSP_INCOMPATIBLE, variant="raw-tag", tag=raw_tag),
                        token.start_index + name_start,
                        token.start_index + name_end,
                        base_index,
                    )
                    continue
                rule, _, attribute, start, end, *_ = event
                variant = {"csp-native-event": "native-event", "csp-javascript-url": "javascript-url"}.get(rule)
                if variant is None:
                    continue
                # A native event finding spans the name, a URL finding the
                # value, so the written name comes from the event's own name.
                attribute = _written_attribute_name(written_bytes, start, attribute)
                self._report(
                    _CSP_RULE,
                    TEMPLATE_CSP_INCOMPATIBLE,
                    attribute,
                    render_diagnostic(TEMPLATE_CSP_INCOMPATIBLE, variant=variant, name=attribute),
                    token.start_index + start,
                    token.start_index + end,
                    base_index,
                )

    def _check_element_name(self, node: object, tag: str, base_index: int) -> None:
        """Report a lowercase tag that is one typing slip from an HTML element."""
        if "rule_misspelled_element" not in self.severities:
            return
        # Vue resolves any other name as a component, which a plugin may
        # register, so only a near typo of a real element is reported.
        if tag != _ascii_lower(tag) or "-" in tag or tag.startswith("c-") or tag in _KNOWN_LOWERCASE_TAGS:
            return
        if len(tag) < _MIN_TYPO_LENGTH:
            return
        suggestion = next(
            (element for element in sorted(HTML_ELEMENTS) if one_slip_from(tag, element)),
            None,
        )
        if suggestion is None:
            return
        name = node.start_tag.name  # type: ignore[attr-defined]
        self._report(
            "rule_misspelled_element",
            TEMPLATE_MISSPELLED_ELEMENT,
            tag,
            render_diagnostic(TEMPLATE_MISSPELLED_ELEMENT, tag=tag, suggestion=suggestion),
            name.start_index,
            name.end_index,
            base_index,
        )

    def _check_attribute_name(self, tag: str, attr: HtmlAttr, base_index: int) -> None:
        """Report an attribute name one typing slip from an attribute this HTML element accepts."""
        if "rule_misspelled_attribute" not in self.severities or attr.foreign_parts:
            return
        written = attr.key.content
        prefix, attribute = _split_attribute_prefix(written)
        if attribute is None:
            return
        lowered = _ascii_lower(attribute)
        # `data-*`, `aria-*`, `hx-*`, and other families with a hyphen or a
        # namespace colon are open, so only a plain name can be a typo.
        if len(lowered) < _MIN_TYPO_LENGTH or "-" in lowered or ":" in lowered or "$" in lowered:
            return
        # `c-iff` is both `c-if` and an attribute `iff`; the misspelled
        # directive rule reports the `c-*` names that look like a directive.
        if prefix == "c-" and _looks_like_c_directive(lowered):
            return
        # On Vue's `<slot>`, a binding is a slot prop with any name.
        if tag == "slot" and prefix in {":", "v-bind:"}:
            return
        accepted = (GLOBAL_ATTRIBUTES, ELEMENT_ATTRIBUTES.get(tag, ()), _VUE_SPECIAL_ATTRIBUTES)
        if any(lowered in names for names in accepted):
            return
        suggestion = next(
            (name for names in accepted for name in sorted(names) if one_slip_from(lowered, name)),
            None,
        )
        if suggestion is None:
            return
        self._report(
            "rule_misspelled_attribute",
            TEMPLATE_MISSPELLED_ATTRIBUTE,
            written,
            render_diagnostic(
                TEMPLATE_MISSPELLED_ATTRIBUTE,
                name=written,
                element=tag,
                suggestion=f"{prefix}{suggestion}",
            ),
            attr.key.start_index,
            attr.key.end_index,
            base_index,
        )

    def _check_aria_attribute(self, attr: HtmlAttr, base_index: int) -> None:
        """Report an ``aria-*`` name that ARIA does not define."""
        if "rule_unknown_aria_attribute" not in self.severities or attr.foreign_parts:
            return
        written = attr.key.content
        _prefix, attribute = _split_attribute_prefix(written)
        if attribute is None:
            return
        lowered = _ascii_lower(attribute)
        # ARIA lets no author invent `aria-*` names, so every unknown name is
        # reported, not only near typos.
        if not lowered.startswith("aria-") or lowered in ARIA_ATTRIBUTES:
            return
        # Compare the part after `aria-`, which every name shares, so a short
        # unrelated name such as `aria-foo` gets no suggestion.
        nearest = get_close_matches(
            lowered.removeprefix("aria-"),
            sorted(name.removeprefix("aria-") for name in ARIA_ATTRIBUTES),
            n=1,
            cutoff=0.8,
        )
        message = (
            render_diagnostic(
                TEMPLATE_UNKNOWN_ARIA_ATTRIBUTE,
                variant="suggestion",
                name=written,
                suggestion=f"aria-{nearest[0]}",
            )
            if nearest
            else render_diagnostic(TEMPLATE_UNKNOWN_ARIA_ATTRIBUTE, name=written)
        )
        self._report(
            "rule_unknown_aria_attribute",
            TEMPLATE_UNKNOWN_ARIA_ATTRIBUTE,
            written,
            message,
            attr.key.start_index,
            attr.key.end_index,
            base_index,
        )

    def _check_event_name(self, attr: HtmlAttr, base_index: int) -> None:
        """Report a listener on an HTML element whose event is one typing slip from a DOM event."""
        if "rule_misspelled_event" not in self.severities:
            return
        written = attr.key.content
        if written.startswith("@"):
            raw = written[1:]
        elif _ascii_lower(written).startswith("v-on:"):
            raw = written[len("v-on:") :]
        else:
            return
        event = raw.split(".", 1)[0]
        # A name with a hyphen, colon, or capital is a custom event; `@c-*`
        # is a Citry server event and `@[name]` is chosen at runtime.
        if event != event.lower() or not event.isascii() or not event.isalpha():
            return
        if event in DOM_EVENT_NAMES or event in _EVENT_LOOKALIKE_WORDS or len(event) < _MIN_TYPO_LENGTH:
            return
        suggestion = next((name for name in sorted(DOM_EVENT_NAMES) if one_slip_from(event, name)), None)
        if suggestion is None:
            return
        self._report(
            "rule_misspelled_event",
            VUE_MISSPELLED_EVENT,
            written,
            render_diagnostic(VUE_MISSPELLED_EVENT, event=event, suggestion=suggestion),
            attr.key.start_index,
            attr.key.end_index,
            base_index,
        )

    def _check_model_target(self, tag: str, lower: str, attr: HtmlAttr, base_index: int) -> None:
        """Report ``v-model`` on an element that holds no value."""
        if "rule_invalid_model_target" not in self.severities:
            return
        written = attr.key.content
        # `v-model:arg` on an element is already a parse error.
        if written != "v-model" and not written.startswith("v-model."):
            return
        if lower in _MODEL_TARGETS:
            return
        self._report(
            "rule_invalid_model_target",
            BROWSER_INVALID_MODEL_TARGET,
            written,
            render_diagnostic(BROWSER_INVALID_MODEL_TARGET, tag=tag),
            attr.key.start_index,
            attr.key.end_index,
            base_index,
        )

    def _check_image_alt(
        self,
        node: object,
        names: set[str],
        attrs: Sequence[HtmlAttr],
        base_index: int,
    ) -> None:
        """Report an ``<img>`` that gives assistive technology no text."""
        if "rule_missing_image_alt" not in self.severities:
            return
        # A spread may add `alt`, and an attribute name written in extension
        # syntax may turn out to be `alt` once rendered.
        if names & {"c-bind", "v-bind"} or any(attr.foreign_parts for attr in attrs):
            return
        labelled = {_split_attribute_prefix(name)[1] for name in names}
        if labelled & {"alt", "aria-label", "aria-labelledby"}:
            return
        for attr in attrs:
            if _split_attribute_prefix(_ascii_lower(attr.key.content))[1] != "role":
                continue
            # A bound role may be "presentation", so only a static one decides.
            if attr.kind != HtmlAttrKind.Static or _ascii_lower(attr.key.content) != "role":
                return
            value = attr.inner_value.content if attr.inner_value is not None else ""
            if _ascii_lower(decode_attribute_entities(value).strip()) in {"none", "presentation"}:
                return
        name = node.start_tag.name  # type: ignore[attr-defined]
        self._report(
            "rule_missing_image_alt",
            TEMPLATE_MISSING_IMAGE_ALT,
            "img",
            render_diagnostic(TEMPLATE_MISSING_IMAGE_ALT),
            name.start_index,
            name.end_index,
            base_index,
        )

    def _record_id(self, attr: HtmlAttr, base_index: int) -> None:
        """Remember a literal ``id`` that always renders, and report a second element with it."""
        if "rule_duplicate_id" not in self.severities:
            return
        if attr.kind != HtmlAttrKind.Static or attr.foreign_parts or _ascii_lower(attr.key.content) != "id":
            return
        inner = attr.inner_value
        if inner is None or not inner.content:
            return
        value = decode_attribute_entities(inner.content)
        # The start index identifies the place; a nested template has its
        # own offsets, but it is never visited here because it may repeat.
        if value not in self.first_ids:
            self.first_ids[value] = base_index + inner.start_index
            return
        self._report(
            "rule_duplicate_id",
            TEMPLATE_DUPLICATE_ID,
            value,
            render_diagnostic(TEMPLATE_DUPLICATE_ID, id=value),
            inner.start_index,
            inner.end_index,
            base_index,
        )

    def _report(
        self,
        rule_name: str,
        code: str,
        name: str,
        message: str,
        start_index: int,
        end_index: int,
        base_index: int,
    ) -> None:
        # Every check calls this, so a rule all consumers ignore stops here.
        severity = self.severities.get(rule_name)
        if severity is None:
            return
        self.found.append(
            MarkupLintFinding(
                name=name,
                message=message,
                code=code,
                severity=severity,
                start_index=base_index + start_index,
                end_index=base_index + end_index,
            )
        )


def _single_root_starts(template: Template) -> Generator[Call, Any, frozenset[int]]:
    """
    Return where the start tag of each element that may be the template's only root begins.

    Vue passes a parent's attributes to a component's single root element.
    A template whose top level is one element, or a chain of ``c-if``,
    ``c-elif``, and ``c-else`` blocks that each hold one element, has such a
    root. The parser builds a new node object on each access, so an element
    is identified by where its start tag begins.
    """
    nodes = [element._0 for element in template.elements if isinstance(element, TemplateElement.Node)]
    tags = [_ascii_lower(node.start_tag.name.content) for node in nodes]
    # One chain starts with the only `c-if`; a second `c-if` starts another
    # chain that can render at the same time.
    if tags and tags[0] == "c-if" and all(tag in {"c-elif", "c-else"} for tag in tags[1:]):
        starts: set[int] = set()
        for node in nodes:
            body = getattr(node, "body", None)
            if body is not None:
                starts.update((yield Call(_single_root_starts, body)))
        return frozenset(starts)
    if len(nodes) == 1:
        return frozenset({nodes[0].start_tag.token.start_index})
    return frozenset()


def _written_attribute_name(content: bytes, start: int, lowered: str) -> str:
    """
    Return an attribute name as ``<c-raw>`` content writes it, given the page check's lowercase name.

    The page check reports a native event attribute by its name and a
    ``javascript:`` URL by its value, so the name is looked for at ``start``
    first and otherwise just before the value.
    """
    size = len(lowered.encode())
    if _ascii_lower(content[start : start + size].decode(errors="replace")) == lowered:
        return content[start : start + size].decode(errors="replace")
    # The value follows `name=` and an optional quote; search back from it.
    before = content[:start].decode(errors="replace")
    index = _ascii_lower(before).rfind(lowered)
    return before[index : index + len(lowered)] if index >= 0 else lowered


def _split_attribute_prefix(written: str) -> tuple[str, str | None]:
    """
    Split a written attribute name into its binding prefix and the HTML attribute it sets.

    ``:title``, ``v-bind:title``, and ``c-title`` all set ``title``. Returns
    ``None`` as the attribute for a name that sets no plain attribute: a
    listener, a directive, a slot, a spread, a dynamic name, a binding with a
    modifier such as ``.prop``, which sets a DOM property, or a Citry
    directive written as ``c-if``.
    """
    for prefix in (":", "v-bind:", "c-"):
        if written.startswith(prefix):
            attribute = written[len(prefix) :]
            break
    else:
        prefix, attribute = "", written
    if not attribute or attribute.startswith(("[", ".", "@", "#", "$")) or "." in attribute:
        return prefix, None
    if not prefix and attribute.startswith(("v-", "@", "#", ":", ".")):
        return prefix, None
    if prefix == "c-" and attribute in ELEMENT_DIRECTIVES:
        return prefix, None
    return prefix, attribute


# The directives an author writes as `c-<name>` on an element. A name one
# typing mistake from one of these is the likely typo.
ELEMENT_DIRECTIVES = ("if", "elif", "else", "for", "empty", "bind")
# Spellings an author brings from other languages for `c-elif`.
SPELLED_OUT_ELIF = frozenset({"else-if", "elseif", "elsif", "else_if"})
# Names that are a directive elsewhere but not in Citry, with what to write
# instead. `c-show` keeps its Python condition with `c-if`; `v-model` has no
# Python form, so the message names Vue's directive.
FOREIGN_DIRECTIVES: dict[str, tuple[str, Literal["default", "vue"]]] = {
    "show": ("c-if", "default"),
    "model": ("v-model", "vue"),
    "key": ("#c-key", "default"),
    "ignore": ("#c-ignore", "default"),
}


def _looks_like_c_directive(lowered: str) -> bool:
    """Return whether the misspelled-directive rule may report ``c-<lowered>``, so this module leaves it alone."""
    return (
        lowered in SPELLED_OUT_ELIF
        or lowered in FOREIGN_DIRECTIVES
        or any(lowered == directive or _is_directive_typo(lowered, directive) for directive in ELEMENT_DIRECTIVES)
    )


# Words one letter short of a directive that are ordinary names an author
# may give an attribute or a custom directive, such as `bid` on an auction
# item or `v-tex` for formulas, so they are not read as a missing letter.
_WORDS_ONE_LETTER_SHORT = frozenset({"or", "bid", "bin", "tex", "mode", "one"})


def _is_directive_typo(written: str, expected: str) -> bool:
    """
    Return whether ``written`` is the directive ``expected`` with one common typing slip.

    The slips are those of ``one_slip_from``. A missing letter that leaves a
    one-letter name, or an ordinary word such as ``bid``, does not count.
    """
    if len(written) + 1 == len(expected) and (len(written) < 2 or written in _WORDS_ONE_LETTER_SHORT):
        return False
    return one_slip_from(written, expected)


def _is_custom_element(tag: str) -> bool:
    """Return whether a tag is a lowercase custom element name, such as ``my-widget``."""
    return "-" in tag and tag == _ascii_lower(tag) and not tag.startswith("c-") and tag[:1].isalpha()


def one_slip_from(written: str, expected: str) -> bool:
    """
    Return whether ``written`` is ``expected`` with one common typing slip.

    The slips are two neighboring letters swapped (``fro`` for ``for``), one
    letter typed twice (``iff`` for ``if``), and one letter left out (``ele``
    for ``else``). A replaced letter, or an added letter that is not a
    double, is not a slip here, because it mostly gives another real word,
    such as ``kind`` for ``bind`` or ``form`` for ``for``.
    """
    if len(written) == len(expected):
        differences = [
            index for index, (left, right) in enumerate(zip(written, expected, strict=True)) if left != right
        ]
        return (
            len(differences) == 2
            and differences[1] == differences[0] + 1
            and written[differences[0]] == expected[differences[1]]
            and written[differences[1]] == expected[differences[0]]
        )
    if len(written) == len(expected) + 1:
        # Dropping one letter of a doubled pair gives the expected name back.
        return any(
            written[index] == written[index + 1] and written[:index] + written[index + 1 :] == expected
            for index in range(len(written) - 1)
        )
    if len(written) + 1 == len(expected):
        return any(expected[:index] + expected[index + 1 :] == written for index in range(len(expected)))
    return False


__all__ = [
    "MARKUP_LINT_RULES",
    "MarkupLintConsumer",
    "MarkupLintFinding",
    "lint_invalid_vue_expressions",
    "lint_markup",
    "one_slip_from",
]
