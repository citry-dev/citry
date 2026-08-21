# This file adds typing for the API exposed from Rust via maturin.
#
# IMPORTANT: The filename `_rust.pyi` matches the `<rust_module_name>` part of
# the `module-name` setting in `pyproject.toml` (`tool.maturin.module-name = "citry_core._rust"`).
# This ensures type checkers can find the type stubs for the Rust extension module.
#
# Since the Rust code exposed to Python is scoped under modules, we need to define
# the API as class attributes, e.g.
#
# ```py
# class template_parser:
#     class Tag:
#         ...
# ```
#
# So that in Python we can access it as:
#
# ```py
# from citry_core import _rust
# _rust.template_parser.Tag(...)
# ```
#
# Notes:
# - Functions without `self` are treated as module-level functions.
#   This matches how typeshed defines modules.

from collections.abc import Mapping

########################################################
# Internationalization
########################################################

class i18n:
    class I18nCompileError(ValueError):
        code: str
        diagnostic_json: str

    class CompiledCatalog:
        @property
        def schema_version(self) -> int: ...
        @property
        def revision(self) -> str: ...
        @property
        def formats_revision(self) -> str: ...
        def artifact_json(self) -> str: ...
        def browser_artifact_json(self, locale: str, request_json: str) -> str: ...
        def browser_parser_artifact_json(self, locale: str) -> str: ...
        def format(
            self,
            locale: str,
            message_id: str,
            args_json: str = "{}",
            attribute: str | None = None,
        ) -> str: ...
        def resolve_json(
            self,
            locale: str,
            message_id: str,
            args_json: str = "{}",
            attribute: str | None = None,
        ) -> str: ...
        def resolve_rich_json(
            self,
            locale: str,
            message_id: str,
            args_json: str,
            slot_names_json: str,
            attribute: str | None = None,
        ) -> str: ...
        def format_number(self, locale: str, profile: str, value: str) -> str: ...
        def parse_number_json(self, locale: str, profile: str, input: str) -> str: ...
        def format_percent(self, locale: str, profile: str, value: str) -> str: ...
        def parse_percent_json(self, locale: str, profile: str, input: str) -> str: ...
        def format_currency(
            self,
            locale: str,
            profile: str,
            value: str,
            currency: str,
        ) -> str: ...
        def format_date(
            self,
            locale: str,
            profile: str,
            year: int,
            month: int,
            day: int,
        ) -> str: ...
        def parse_date_json(self, locale: str, profile: str, input: str) -> str: ...
        def parse_date_segments_json(
            self,
            locale: str,
            profile: str,
            year: str,
            month: str,
            day: str,
        ) -> str: ...
        def format_time(
            self,
            locale: str,
            profile: str,
            hour: int,
            minute: int,
            second: int,
            nanosecond: int,
        ) -> str: ...
        def parse_time_json(self, locale: str, profile: str, input: str) -> str: ...
        def parse_time_segments_json(
            self,
            locale: str,
            profile: str,
            hour: str,
            minute: str,
            second: str | None,
            day_period: str | None,
        ) -> str: ...
        def format_datetime(
            self,
            locale: str,
            profile: str,
            year: int,
            month: int,
            day: int,
            hour: int,
            minute: int,
            second: int,
            nanosecond: int,
            time_zone: str,
            offset_seconds: int,
            epoch_seconds: int,
        ) -> str: ...
        def parse_datetime_json(self, locale: str, profile: str, input: str) -> str: ...
        def parse_datetime_segments_json(
            self,
            locale: str,
            profile: str,
            year: str,
            month: str,
            day: str,
            hour: str,
            minute: str,
            second: str | None,
            day_period: str | None,
        ) -> str: ...
        def format_relative_time(
            self,
            locale: str,
            profile: str,
            value: str,
            unit: str,
        ) -> str: ...
        def format_list(self, locale: str, profile: str, values: list[str]) -> str: ...
        def format_unit(
            self,
            locale: str,
            profile: str,
            value: str,
            unit: str,
        ) -> str: ...

    class CatalogCompiler:
        def __init__(self) -> None: ...
        def compile(self, request_json: str) -> i18n.CompiledCatalog: ...
        def compile_link_unit(self, request_json: str) -> str: ...
        def analyze_source(self, path: str, source: str) -> str: ...
        def clear(self) -> None: ...

    class TextCatalog:
        def __init__(self, locale: str, source: str, origin: str) -> None: ...
        @property
        def origin(self) -> str: ...
        def entries(self) -> list[tuple[str, bool, list[str]]]: ...
        def format(self, message_id: str, attribute: str | None = None) -> str: ...

    @staticmethod
    def canonicalize_locale(value: str) -> str: ...
    @staticmethod
    def locale_direction(value: str) -> str | None: ...

########################################################
# HTML transform
########################################################

class html_transform:
    @staticmethod
    def scan_alpine_html(html_fragments: list[str]) -> list[bool]: ...
    @staticmethod
    def mark_html(
        html: str,
        root_attributes: list[str],
        placeholder_attr: str,
    ) -> tuple[list[str], list[tuple[str, str, list[str]]]]:
        """
        Splice attributes onto root-level tags and split the HTML around child
        placeholder elements, in a single scan.

        This is the serializer's fast path. Each attribute in `root_attributes`
        is added (as `attr=""`) to every root-level (depth 0) tag. A placeholder
        is a `<template>` element carrying `placeholder_attr` with a
        whitespace-only body; the output is split around placeholders so the
        caller can join in each child's finished HTML without scanning again.

        Unlike `transform_html`, bytes outside root-level tags are copied
        through verbatim (no re-serialization or normalization), and malformed
        markup is treated as text rather than raising.

        **Arguments**

        - `html` (str): The HTML string to mark. Can be a fragment or full document.
        - `root_attributes` (List[str]): Attribute names to add to root-level tags.
        - `placeholder_attr` (str): The attribute that identifies placeholder elements.

        **Returns**

        A tuple `(segments, placeholders)`:
            - `segments` (List[str]): the marked HTML split around placeholders;
                always exactly `len(placeholders) + 1` entries.
            - `placeholders` (List[Tuple[str, str, List[str]]]): one entry per
                placeholder, in document order: `(id, placeholder_html, added_attributes)`
                where `id` is the placeholder attribute's value, `placeholder_html`
                is the placeholder element's text (with any spliced attributes,
                for callers that leave unknown ids in place), and
                `added_attributes` lists the attributes spliced into it
                (non-empty only for root-level placeholders).

        The marked HTML is `segments[0] + placeholders[0][1] + segments[1] + ...`.

        **Example**

        ```python
        >>> segments, placeholders = mark_html(
        ...     '<div><template c-render-id="c2"></template></div>',
        ...     ['data-cid-c1'],
        ...     'c-render-id',
        ... )
        >>> segments
        ['<div data-cid-c1="">', '</div>']
        >>> placeholders
        [('c2', '<template c-render-id="c2"></template>', [])]
        ```
        """

    @staticmethod
    def transform_html(
        html: str,
        root_attributes: list[str],
        all_attributes: list[str],
        check_end_names: bool | None = None,
        track_added_attributes_for_tags_with_this_attribute: str | None = None,
    ) -> tuple[str, dict[str, list[str]]]:
        """
        Transform given HTML string.

        This function performs the following transformations:

        1. **Add root attributes**: Attributes specified in `root_attributes` are added
        only to root-level elements (elements at depth 0).

        2. **Add attributes to all elements**: Attributes specified in `all_attributes`
        are added to every element in the HTML.

        In addition, this transformer also:

        1. **Tracks added attributes**: If `track_added_attributes_for_tags_with_this_attribute`
        is set, captures which attributes were added to elements that have the specified
        attribute, returning a dictionary mapping attribute values to lists of attributes added to tag.

        2. **Validates end tags**: If `check_end_names` is enabled, validates that
        closing tags match their corresponding opening tags.

        **Arguments**

        - `html` (str): The HTML string to transform. Can be a fragment or full document.
        - `root_attributes` (List[str]): List of attribute names to add to root elements only.
        - `all_attributes` (List[str]): List of attribute names to add to all elements.
        - `check_end_names` (Optional[bool]): Whether to validate matching of end tags. Defaults to False.
        - `track_added_attributes_for_tags_with_this_attribute` (Optional[str]): If set, captures which attributes were added to elements with this attribute.

        **Returns**

        A tuple containing:
            - The transformed HTML string
            - A dictionary mapping captured attribute values to lists of attributes that were added
                to those elements. Only populated if `track_added_attributes_for_tags_with_this_attribute` is set, otherwise empty dict.

        **Example**

        ```python
        >>> html = '<div data-id="123"><p>Hello</p></div>'
        >>> html, captured = transform_html(html, ['data-root-id'], ['data-v-123'], track_added_attributes_for_tags_with_this_attribute='data-id')
        >>> print(captured)
        {'123': ['data-root-id', 'data-v-123']}
        ```

        **Raises**

        ValueError: If the HTML is malformed or cannot be parsed.
        """

########################################################
# Client graph
########################################################

class client_graph:
    @staticmethod
    def canonical_json_and_revision(value: object) -> tuple[str, str]: ...

########################################################
# Safe eval
########################################################

class safe_eval:
    @staticmethod
    def safe_eval(source: str) -> str:
        """
        Transform a Python expression string to make it safe for evaluation.

        This function takes a Python expression string and transforms it into safe code
        by wrapping potentially unsafe operations (like variable access, function calls,
        attribute access, etc.) with sandboxed function calls.

        **Args:**

        - source (str): The Python expression string to transform.

        **Returns:**

        - str: The transformed Python expression as a string.

        **Raises:**

        - SyntaxError: If the input is not valid Python syntax or contains forbidden constructs.

        **Examples:**

        ```python
        >>> safe_eval("my_var + 1")
        'variable("my_var") + 1'

        >>> safe_eval("lambda x: x + my_var")
        'lambda x: x + variable("my_var")'
        ```

        **Transformations:**

        The following transformations are applied to make expressions safe for evaluation:

        1. **Variable access** - `my_var` → `variable("my_var")`
        2. **Function calls** - `foo(1, 2, a=3, *args, **kwargs)` → `call(foo, 1, 2, a=x, *args, **kwargs)`
        3. **Attribute access** - `obj.attr` → `attribute(obj, "attr")`
        4. **Subscript access** - `obj[key]` → `subscript(obj, key)`
        5. **Walrus operator** - `(x := value)` → `assign("x", value)`

        Because of the changes above, we also need to transform:

        6. **Slice notation** - `obj[1:10:2]` → `subscript(obj, slice(1, 10, 2))`
           - Because slice syntax is valid only inside square brackets.
        7. **F-strings** - `f"Hello {price!r:.2f}"` → `format("Hello {}", (variable("price"), "r", ".2f"))`
           - To avoid issues with quote escaping and enable error reporting
        8. **T-strings** - `t"Hello {name!r:>10}"` → `template("Hello ", interpolation(variable("name"), "expr", "r", ">10"))`
           - To avoid issues with quote escaping
        """

########################################################
# Template formatter
########################################################

class template_formatter:
    class TemplateFormatError(ValueError):
        """A structured refusal to format authored Citry template text."""

        code: str
        message: str
        range: tuple[int, int] | None
        diagnostic: template_parser.ParseDiagnostic | None

    class _EmbeddedFormatPlan:
        """Opaque source-bound handle for an embedded-formatting pass."""

        @property
        def id(self) -> str: ...
        @property
        def formatted_source(self) -> str: ...
        @property
        def requests(
            self,
        ) -> list[
            tuple[
                str,
                str,
                str,
                str,
                str,
                tuple[int, int],
                int,
                str,
            ]
        ]: ...
        @property
        def notices(
            self,
        ) -> list[tuple[str, str, str | None, str | None]]: ...

    @staticmethod
    def format_template(source: str) -> str: ...
    @staticmethod
    def python_expression_provider() -> str: ...
    @staticmethod
    def prepare_embedded_format(source: str) -> template_formatter._EmbeddedFormatPlan: ...
    @staticmethod
    def finish_embedded_format(
        plan: template_formatter._EmbeddedFormatPlan,
        results: list[
            tuple[
                str,
                str,
                str,
                str | None,
                str | None,
                str | None,
            ]
        ],
    ) -> tuple[
        str,
        list[tuple[str, str, str | None, str | None]],
        list[str],
    ]: ...

########################################################
# Template parser (V3)
########################################################

class template_parser:
    @staticmethod
    def analyze_browser_source(
        input: str,
        mode: str,
    ) -> tuple[bool, list[tuple[str, int, int]]]: ...
    @staticmethod
    def analyze_component_scope_writes(
        input: str,
    ) -> list[tuple[str, int, int, int, int]]: ...
    @staticmethod
    def analyze_component_source(
        input: str,
    ) -> tuple[
        bool,
        list[tuple[str, int, int]],
        list[tuple[str, str, int, int, list[tuple[int, int]]]],
        list[tuple[str, int, int, int, int]],
    ]: ...
    # Functions
    @staticmethod
    def parse_template(
        input: str,
        lang: str | None = None,
        user_rules: dict[str, template_parser.TagRules] | None = None,
    ) -> template_parser.Template: ...
    @staticmethod
    def compile_template(
        template: template_parser.Template,
        lang: str | None = None,
    ) -> str: ...
    def format_number(self, locale: str, profile: str, value: str) -> str: ...
    def format_currency(self, locale: str, profile: str, value: str, currency: str) -> str: ...
    def format_date(self, locale: str, profile: str, year: int, month: int, day: int) -> str: ...
    def format_relative_time(self, locale: str, profile: str, value: str, unit: str) -> str: ...
    def format_list(self, locale: str, profile: str, values: list[str]) -> str: ...

    # AST types

    class ParseDiagnostic:
        """Machine-readable details attached to a template parse exception."""

        code: str
        message: str
        start_index: int | None
        end_index: int | None
        start_line: int | None
        start_column: int | None
        end_line: int | None
        end_column: int | None

    class Token:
        """A span in the template source with position information."""

        def __init__(
            self,
            content: str,
            start_index: int,
            end_index: int,
            line_col: tuple[int, int],
        ) -> None: ...
        content: str
        start_index: int
        end_index: int
        line_col: tuple[int, int]

    class Comment:
        """A template comment `{# ... #}` or HTML comment `<!-- ... -->`."""

        def __init__(self, token: template_parser.Token, value: template_parser.Token) -> None: ...
        token: template_parser.Token
        value: template_parser.Token

    class HtmlAttrKind:
        """Enum: Static, Expression, Template, or Meta."""

        Static: template_parser.HtmlAttrKind
        Expression: template_parser.HtmlAttrKind
        Template: template_parser.HtmlAttrKind
        Meta: template_parser.HtmlAttrKind

    class FillDataField:
        """One source-to-target field in a fill-data destructuring pattern."""

        def __init__(self, source: template_parser.Token, target: template_parser.Token) -> None: ...
        source: template_parser.Token
        target: template_parser.Token

    class FillDataPattern:
        """A parsed whole-record or one-level fill-data binding."""

        def __init__(
            self,
            token: template_parser.Token,
            whole: template_parser.Token | None,
            fields: list[template_parser.FillDataField],
            rest: template_parser.Token | None,
        ) -> None: ...
        token: template_parser.Token
        whole: template_parser.Token | None
        fields: list[template_parser.FillDataField]
        rest: template_parser.Token | None

    class HtmlAttr:
        """An HTML attribute (static, dynamic expression, nested template, or #c-* framework metadata)."""

        def __init__(
            self,
            token: template_parser.Token,
            key: template_parser.Token,
            value: template_parser.Token | None,
            inner_value: template_parser.Token | None,
            quote_char: str | None,
            kind: template_parser.HtmlAttrKind,
            comments: list[template_parser.Comment],
            used_variables: list[template_parser.Token],
            fill_data_pattern: template_parser.FillDataPattern | None = None,
        ) -> None: ...
        token: template_parser.Token
        key: template_parser.Token
        value: template_parser.Token | None
        inner_value: template_parser.Token | None
        quote_char: str | None
        kind: template_parser.HtmlAttrKind
        used_variables: list[template_parser.Token]
        comments: list[template_parser.Comment]
        fill_data_pattern: template_parser.FillDataPattern | None

    class HtmlStartTag:
        """An HTML opening tag with its attributes."""

        token: template_parser.Token
        name: template_parser.Token
        attrs: list[template_parser.HtmlAttr]
        is_self_closing: bool
        comments: list[template_parser.Comment]

    class HtmlEndTag:
        """An HTML closing tag."""

        token: template_parser.Token
        name: template_parser.Token
        comments: list[template_parser.Comment]

    class Expr:
        """A template expression `{{ ... }}`."""

        token: template_parser.Token
        value: template_parser.Token
        used_variables: list[template_parser.Token]
        comments: list[template_parser.Comment]

    class Text:
        """Plain text content."""

        token: template_parser.Token

    class Node_SelfClosing:
        """A self-closing HTML/component tag."""

        start_tag: template_parser.HtmlStartTag
        used_variables: list[template_parser.Token]
        introduced_variables: list[template_parser.Token]
        comments: list[template_parser.Comment]
        contains_fills: bool
        name: str

    class Node_WithBody:
        """An HTML/component tag with a body."""

        start_tag: template_parser.HtmlStartTag
        end_tag: template_parser.HtmlEndTag
        body: template_parser.Template
        used_variables: list[template_parser.Token]
        introduced_variables: list[template_parser.Token]
        comments: list[template_parser.Comment]
        contains_fills: bool
        name: str

    class Node:
        """Enum: SelfClosing or WithBody. Access the variant via `._0`."""

        SelfClosing: type[template_parser.Node_SelfClosing]
        WithBody: type[template_parser.Node_WithBody]
        name: str

    class TemplateElement_Text:
        """A TemplateElement variant wrapping Text. Access via `._0`."""

        _0: template_parser.Text

    class TemplateElement_Expr:
        """A TemplateElement variant wrapping Expr. Access via `._0`."""

        _0: template_parser.Expr

    class TemplateElement_Node:
        """A TemplateElement variant wrapping Node. Access via `._0`."""

        _0: template_parser.Node_SelfClosing | template_parser.Node_WithBody

    class TemplateElement:
        """
        Enum: Text, Expr, or Node. The concrete variant type is one of
        TemplateElement_Text, TemplateElement_Expr, TemplateElement_Node.
        """

        Text: type[template_parser.TemplateElement_Text]
        Expr: type[template_parser.TemplateElement_Expr]
        Node: type[template_parser.TemplateElement_Node]

    class StaticNamedSlot:
        """A slot with a statically-known name."""

        token: template_parser.Token
        required: bool | None

    class Template:
        """The parsed template AST."""

        elements: list[
            template_parser.TemplateElement_Text
            | template_parser.TemplateElement_Expr
            | template_parser.TemplateElement_Node
        ]
        comments: list[template_parser.Comment]
        used_variables: list[template_parser.Token]
        slots: list[template_parser.StaticNamedSlot]

    # Config types

    class TagRules:
        """Validation rules for custom component tags."""

        def __init__(
            self,
            allowed_attrs: list[list[str]] | None = None,
            required_attrs: list[list[str]] | None = None,
            allowed_slots: list[str] | None = None,
            required_slots: list[str] | None = None,
            slot_data_fields: dict[str, list[str]] | None = None,
        ) -> None: ...
        allowed_attrs: list[list[str]] | None
        required_attrs: list[list[str]]
        allowed_slots: list[str] | None
        required_slots: list[str]
        slot_data_fields: dict[str, list[str]]

    # Constants

    HTML_VOID_ELEMENTS: frozenset[str]
    """HTML void elements (elements that cannot have children, e.g. ``<br/>``)."""

    RESERVED_TAG_NAMES: frozenset[str]
    """Structural ``<c-*>`` tags the parser handles itself (e.g. ``c-if``, ``c-slot``),
    so they never resolve to a user component."""

    CITRY_DIRECTIVE_NAMES: frozenset[str]
    """Fixed Citry attribute directives whose spelling is owned by the parser."""

    STRUCTURAL_TAG_ATTRIBUTE_NAMES: Mapping[str, frozenset[str]]
    """Fixed parser-owned attribute spellings keyed by structural tag name."""
