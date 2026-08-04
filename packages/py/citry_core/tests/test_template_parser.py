"""
Tests for the V3 template parser Python surface.

Covers: parse_template, compile_template, AST inspection, round-trip
(parse -> compile -> exec with stub nodes), error handling, and the
lang parameter.
"""

# ruff: noqa: S102,ANN

import pytest

from citry_core.template_parser import (
    RESERVED_TAG_NAMES,
    FillDataField,
    FillDataPattern,
    HtmlAttr,
    HtmlAttrKind,
    ParseDiagnostic,
    TagRules,
    Template,
    Token,
    compile_template,
    parse_diagnostic,
    parse_template,
)


def test_reserved_tag_names_are_exposed_from_the_parser() -> None:
    assert "c-if" in RESERVED_TAG_NAMES
    assert "c-slot" in RESERVED_TAG_NAMES
    assert all(name.startswith("c-") for name in RESERVED_TAG_NAMES)


# =========================================================================
# Dummy runtime node classes
# =========================================================================
#
# The compiler emits source code that instantiates runtime node classes by
# name. citry_core owns only the parser and compiler; the real node classes
# live in the higher-level ``citry`` package, which depends on citry_core
# (not the other way around). To keep these tests within citry_core's own
# layer, we define minimal stand-ins here.
#
# Each constructor mirrors the exact argument order the compiler emits (the
# compiler output is the contract). The stubs only capture those arguments as
# attributes so the round-trip tests can assert on the resulting node tree.


class ExprNode:
    def __init__(self, source, position, expr, used_vars):
        self.source = source
        self.position = position
        self.expr = expr
        self.used_vars = used_vars


class TemplateNode:
    def __init__(self, source, position, expr, used_vars):
        self.source = source
        self.position = position
        self.expr = expr
        self.used_vars = used_vars


class StaticHtmlAttr:
    def __init__(self, source, position, key, value, used_vars):
        self.source = source
        self.position = position
        self.key = key
        self.value = value
        self.used_vars = used_vars


class FillDataBinding:
    def __init__(self, fields, rest):
        self.fields = fields
        self.rest = rest


class ExprHtmlAttr:
    def __init__(self, source, position, key, expr, used_vars):
        self.source = source
        self.position = position
        self.key = key
        self.expr = expr
        self.used_vars = used_vars


class ElementKeyNode:
    def __init__(self, attr):
        self.attr = attr


class TemplateHtmlAttr:
    def __init__(self, source, position, key, template, used_vars):
        self.source = source
        self.position = position
        self.key = key
        self.template = template
        self.used_vars = used_vars


class ComponentNode:
    # The trailing `key` argument is emitted only when the tag carries
    # `#c-key`, so it defaults here like in the real runtime class.
    def __init__(self, source, position, attrs, body, used_vars, name, contains_fills, key=None):
        self.source = source
        self.position = position
        self.attrs = attrs
        self.body = body
        self.used_vars = used_vars
        self.name = name
        self.contains_fills = contains_fills
        self.key = key


class IfNode:
    def __init__(self, source, branches, used_vars):
        self.source = source
        self.branches = branches
        self.used_vars = used_vars


class ForNode:
    def __init__(self, source, branches, used_vars):
        self.source = source
        self.branches = branches
        self.used_vars = used_vars


class SlotNode:
    def __init__(self, source, position, attrs, body, used_vars, introduced_vars):
        self.source = source
        self.position = position
        self.attrs = attrs
        self.body = body
        self.used_vars = used_vars
        self.introduced_vars = introduced_vars


class FillNode:
    def __init__(self, source, position, attrs, body, used_vars, introduced_vars):
        self.source = source
        self.position = position
        self.attrs = attrs
        self.body = body
        self.used_vars = used_vars
        self.introduced_vars = introduced_vars


# =========================================================================
# parse_template - basic parsing
# =========================================================================


class TestParseTemplate:
    def test_plain_text(self):
        t = parse_template("Hello, world!")
        assert isinstance(t, Template)
        assert len(t.elements) == 1

    def test_expression(self):
        t = parse_template("{{ name }}")
        assert len(t.elements) == 1
        assert len(t.used_variables) == 1
        assert t.used_variables[0].content == "name"

    def test_html_tag(self):
        t = parse_template("<div>hi</div>")
        assert len(t.elements) == 1
        node = t.elements[0]._0
        assert node.name == "div"

    def test_component(self):
        t = parse_template('<c-Card title="Hello" />')
        assert len(t.elements) == 1
        node = t.elements[0]._0
        assert node.name == "c-Card"
        assert len(node.start_tag.attrs) == 1
        assert node.start_tag.attrs[0].key.content == "title"

    def test_expression_variables_tracked(self):
        t = parse_template("{{ a + b }}")
        var_names = [v.content for v in t.used_variables]
        assert "a" in var_names
        assert "b" in var_names

    def test_control_flow_if(self):
        t = parse_template('<c-if cond="x">yes</c-if>')
        assert len(t.elements) == 1

    def test_control_flow_for(self):
        t = parse_template('<c-for each="item in items">{{ item }}</c-for>')
        assert len(t.elements) == 1

    def test_slot_and_fill(self):
        t = parse_template('<c-Card><c-fill name="header">h</c-fill></c-Card>')
        assert len(t.elements) == 1
        comp = t.elements[0]._0
        assert comp.contains_fills is True

    def test_fill_data_pattern_is_exposed_through_python_ast(self):
        t = parse_template('<c-Card><c-fill name="header" data="{ a, b as c, **rest }">body</c-fill></c-Card>')
        fill = t.elements[0]._0.body.elements[0]._0
        data_attr = next(attr for attr in fill.start_tag.attrs if attr.key.content == "data")
        pattern = data_attr.fill_data_pattern

        assert isinstance(pattern, FillDataPattern)
        assert pattern.whole is None
        assert all(isinstance(field, FillDataField) for field in pattern.fields)
        assert [(field.source.content, field.target.content) for field in pattern.fields] == [
            ("a", "a"),
            ("b", "c"),
        ]
        assert pattern.rest.content == "rest"

    def test_html_attr_constructor_keeps_the_pre_pattern_signature(self):
        token = Token("title", 0, 5, (1, 1))
        attr = HtmlAttr(token, token, None, None, None, HtmlAttrKind.Static, [], [])

        assert attr.fill_data_pattern is None

    def test_raw(self):
        t = parse_template("<c-raw>{{ not parsed }}</c-raw>")
        assert len(t.elements) == 1

    def test_meta_kind_enum_member(self):
        # The `#c-*` framework channel's attribute kind is part of the
        # Python contract (mirrored in _rust.pyi).
        assert isinstance(HtmlAttrKind.Meta, HtmlAttrKind)
        # A template carrying the channel parses through the binding.
        t = parse_template('<li #c-key="item.id">x</li>')
        assert len(t.elements) == 1
        assert t.used_variables[0].content == "item"
        assert t.elements[0]._0.start_tag.attrs[0].kind == HtmlAttrKind.Meta

    def test_comment_tracked(self):
        t = parse_template("Hello {# comment #} world")
        assert len(t.comments) == 1
        assert t.comments[0].value.content == " comment "

    def test_python_comment_text_does_not_change_interpolation_boundary(self):
        t = parse_template('{{ x # say "}}" then stop }}')

        assert t.comments[0].token.content == '# say "'
        assert t.elements[1]._0.token.content == '" then stop }}'

    def test_empty_template(self):
        t = parse_template("")
        assert len(t.elements) == 0


# =========================================================================
# compile_template - check generated source
# =========================================================================


class TestCompileTemplate:
    def test_plain_text(self):
        t = parse_template("Hello!")
        code = compile_template(t)
        assert "def generate_template():" in code
        assert '"""Hello!"""' in code

    def test_expression(self):
        t = parse_template("{{ x }}")
        code = compile_template(t)
        assert "ExprNode" in code
        assert '"x"' in code

    def test_component(self):
        t = parse_template("<c-Card />")
        code = compile_template(t)
        assert "ComponentNode" in code
        assert '"""card"""' in code

    def test_if_node(self):
        t = parse_template('<c-if cond="x">yes</c-if>')
        code = compile_template(t)
        assert "IfNode" in code

    def test_for_node(self):
        t = parse_template('<c-for each="item in items">{{ item }}</c-for>')
        code = compile_template(t)
        assert "ForNode" in code

    def test_static_html_attr(self):
        t = parse_template('<c-Card title="Hello" />')
        code = compile_template(t)
        assert "StaticHtmlAttr" in code

    def test_expr_html_attr(self):
        t = parse_template('<c-Card c-title="t" />')
        code = compile_template(t)
        assert "ExprHtmlAttr" in code

    def test_meta_key_on_element(self):
        t = parse_template('<li #c-key="item.id">x</li>')
        code = compile_template(t)
        assert "ElementKeyNode(ExprHtmlAttr(" in code
        assert '"""item.id"""' in code

    def test_meta_ignore_on_element(self):
        t = parse_template("<div #c-ignore>x</div>")
        code = compile_template(t)
        assert 'data-citry-morph=\\"ignore\\"' in code


# =========================================================================
# Round-trip: parse -> compile -> exec with stub nodes
# =========================================================================


class TestRoundTrip:
    @staticmethod
    def _exec_template(input_str):
        """Parse, compile, exec, and return the body list."""
        t = parse_template(input_str)
        code = compile_template(t)
        ns = {
            "source": input_str,
            "ExprNode": ExprNode,
            "TemplateNode": TemplateNode,
            "ComponentNode": ComponentNode,
            "IfNode": IfNode,
            "ForNode": ForNode,
            "SlotNode": SlotNode,
            "FillNode": FillNode,
            "FillDataBinding": FillDataBinding,
            "StaticHtmlAttr": StaticHtmlAttr,
            "ExprHtmlAttr": ExprHtmlAttr,
            "ElementKeyNode": ElementKeyNode,
            "TemplateHtmlAttr": TemplateHtmlAttr,
        }
        exec(code, ns)
        return ns["generate_template"]()

    def test_plain_text(self):
        body = self._exec_template("Hello!")
        assert body == ["Hello!"]

    def test_expression(self):
        body = self._exec_template("{{ x }}")
        assert len(body) == 1
        assert isinstance(body[0], ExprNode)
        assert body[0].used_vars == ("x",)

    def test_text_and_expression(self):
        body = self._exec_template("Hello {{ name }}!")
        assert len(body) == 3
        assert body[0] == "Hello "
        assert isinstance(body[1], ExprNode)
        assert body[2] == "!"

    def test_component(self):
        body = self._exec_template("<c-Card />")
        assert len(body) == 1
        assert isinstance(body[0], ComponentNode)
        assert body[0].name == "card"

    def test_component_with_static_attr(self):
        body = self._exec_template('<c-Card title="Hello" />')
        comp = body[0]
        assert isinstance(comp, ComponentNode)
        assert len(comp.attrs) == 1
        assert isinstance(comp.attrs[0], StaticHtmlAttr)

    def test_component_with_meta_key(self):
        body = self._exec_template('<c-Card #c-key="item.id" title="Hi" />')
        comp = body[0]
        assert isinstance(comp, ComponentNode)
        # The key rides as the trailing argument, never inside attrs (so it
        # can never become a kwarg).
        assert isinstance(comp.key, ExprHtmlAttr)
        assert comp.key.key == "#c-key"
        assert comp.key.expr == "item.id"
        assert comp.key.used_vars == ("item",)
        assert len(comp.attrs) == 1
        assert isinstance(comp.attrs[0], StaticHtmlAttr)

    def test_unkeyed_component_key_defaults_none(self):
        body = self._exec_template("<c-Card />")
        assert body[0].key is None

    def test_element_meta_key(self):
        body = self._exec_template('<li #c-key="item.id">x</li>')
        assert body[0] == "<li"
        assert isinstance(body[1], ElementKeyNode)
        assert isinstance(body[1].attr, ExprHtmlAttr)
        assert body[1].attr.key == "#c-key"
        assert body[1].attr.expr == "item.id"
        assert body[1].attr.used_vars == ("item",)
        assert body[2] == ">x</li>"

    def test_element_meta_ignore(self):
        body = self._exec_template("<div #c-ignore>x</div>")
        assert body == ['<div data-citry-morph="ignore">x</div>']

    def test_if_node(self):
        body = self._exec_template('<c-if cond="x">yes</c-if>')
        assert len(body) == 1
        assert isinstance(body[0], IfNode)
        assert len(body[0].branches) == 1

    def test_if_elif_else(self):
        body = self._exec_template('<c-if cond="x">a</c-if><c-elif cond="y">b</c-elif><c-else>c</c-else>')
        assert isinstance(body[0], IfNode)
        assert len(body[0].branches) == 3

    def test_for_node(self):
        body = self._exec_template('<c-for each="item in items">{{ item }}</c-for>')
        assert isinstance(body[0], ForNode)

    def test_for_with_empty(self):
        body = self._exec_template('<c-for each="item in items">{{ item }}</c-for><c-empty>none</c-empty>')
        assert isinstance(body[0], ForNode)
        assert len(body[0].branches) == 2

    def test_slot(self):
        body = self._exec_template('<c-slot name="header" />')
        assert isinstance(body[0], SlotNode)

    def test_fill_inside_component(self):
        body = self._exec_template('<c-Card><c-fill name="header">h</c-fill></c-Card>')
        comp = body[0]
        assert isinstance(comp, ComponentNode)
        assert comp.contains_fills is True
        assert len(comp.body) == 1
        assert isinstance(comp.body[0], FillNode)

    def test_static_html_coalesced(self):
        body = self._exec_template("<div>hi</div>")
        assert body == ["<div>hi</div>"]

    def test_raw(self):
        # <c-raw> is a verbatim block: it compiles to a literal text part, not a
        # component. The inner {{ ... }} is kept as literal text, not parsed.
        body = self._exec_template("<c-raw>{{ not parsed }}</c-raw>")
        assert body == ["{{ not parsed }}"]

    def test_nested_components(self):
        body = self._exec_template("<c-Outer><c-Inner /></c-Outer>")
        outer = body[0]
        assert isinstance(outer, ComponentNode)
        assert outer.name == "outer"
        inner = outer.body[0]
        assert isinstance(inner, ComponentNode)
        assert inner.name == "inner"


# =========================================================================
# Error handling
# =========================================================================


class TestErrors:
    def test_parse_error_keeps_builtin_class_and_exposes_diagnostic(self):
        source = "<div></span>"

        with pytest.raises(SyntaxError) as exc_info:
            parse_template(source)

        error = exc_info.value
        diagnostic = parse_diagnostic(error)
        assert type(error) is SyntaxError
        assert isinstance(diagnostic, ParseDiagnostic)
        assert diagnostic.code == "citry.parse.syntax"
        assert diagnostic.message == str(error)
        assert source.encode("utf-8")[diagnostic.start_index : diagnostic.end_index] == b"</span>"
        assert (diagnostic.start_line, diagnostic.start_column) == (1, 6)
        assert (diagnostic.end_line, diagnostic.end_column) == (1, 13)

    def test_non_parser_value_error_has_no_parse_diagnostic(self):
        with pytest.raises(ValueError, match="Unknown language") as exc_info:
            parse_template("hello", lang="cobol")

        assert parse_diagnostic(exc_info.value) is None

    def test_unknown_meta_attr_raises_naming_members(self):
        # The `#c-*` channel has exactly two members; the parse error names
        # them so the author knows what exists.
        with pytest.raises(SyntaxError, match="'#c-key' and '#c-ignore'"):
            parse_template('<div #c-bogus="1">x</div>')

    def test_unclosed_tag_raises_syntax_error(self):
        with pytest.raises(SyntaxError):
            parse_template("<c-my-tag>")

    def test_mismatched_tags_raises_syntax_error(self):
        with pytest.raises(SyntaxError):
            parse_template("<div></span>")

    def test_unknown_lang_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown language"):
            parse_template("hello", lang="cobol")


# =========================================================================
# Lang parameter
# =========================================================================


class TestLangParameter:
    def test_default_is_python(self):
        t = parse_template("{{ x }}")
        assert len(t.used_variables) == 1

    def test_explicit_python(self):
        t = parse_template("{{ x }}", lang="python")
        assert len(t.used_variables) == 1

    def test_js_parses_text_only(self):
        # JS lang stub is structural only; expressions raise "not yet implemented".
        # But text-only templates parse fine with any lang.
        t = parse_template("<div>hi</div>", lang="js")
        assert len(t.elements) == 1

    def test_js_expression_not_implemented(self):
        # JS expression parsing is a stub and raises SyntaxError.
        with pytest.raises(SyntaxError, match="not yet implemented"):
            parse_template("{{ x }}", lang="js")

    def test_javascript_alias(self):
        # "javascript" is accepted as an alias for "js".
        t = parse_template("<div>hi</div>", lang="javascript")
        assert len(t.elements) == 1


# =========================================================================
# TagRules (user_rules parameter)
# =========================================================================


class TestTagRules:
    def test_slot_data_fields_round_trip(self):
        rules = TagRules(slot_data_fields={"row": ["item", "index"], "empty": []})
        assert rules.slot_data_fields == {"empty": [], "row": ["item", "index"]}

    def test_allowed_attrs_passes(self):
        rules = {"c-card": TagRules(allowed_attrs=[["title"]])}
        t = parse_template('<c-card title="hi"></c-card>', user_rules=rules)
        assert len(t.elements) == 1

    def test_disallowed_attr_raises(self):
        rules = {"c-card": TagRules(allowed_attrs=[["title"]])}
        with pytest.raises(SyntaxError):
            parse_template('<c-card bogus="no"></c-card>', user_rules=rules)

    def test_required_attr_missing_raises(self):
        rules = {"c-card": TagRules(required_attrs=[["title"]])}
        with pytest.raises(SyntaxError):
            parse_template("<c-card></c-card>", user_rules=rules)
