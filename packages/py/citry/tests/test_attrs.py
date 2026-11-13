"""
Tests for the attribute value helpers (docs/design/template_html_attrs.md sections 3
and 4): class/style normalization, merging, and formatting.

Ported from django-components' tests/test_attributes.py where the semantics
match. Divergences from django-components are tested explicitly and marked
with a comment saying what changed and why.
"""

# ruff: noqa: ANN

import random
import re
import tracemalloc

import pytest

from citry import (
    Citry,
    Component,
    Const,
    Markup,
    format_attrs,
    merge_attrs,
    normalize_class,
    normalize_style,
    parse_string_style,
)
from citry.attrs import _split_style_declarations, _style_property_re, exact_str, validate_html_attr_name
from citry.nodes import ElementKeyNode

from ._growth import assert_grows_in_step


class TestFormatAttrs:
    def test_repeated_class_merges_keep_mutable_removals_live(self):
        left = {"class": "alpha\talpha beta"}
        right = {"CLASS": "beta gamma"}
        assert merge_attrs(left, right) == {"class": "alpha beta gamma"}
        assert merge_attrs(left, right) == {"class": "alpha beta gamma"}
        flags = {"alpha": False}
        right["CLASS"] = flags
        assert merge_attrs(left, right) == {"class": "beta"}
        flags["alpha"] = True
        assert merge_attrs(left, right) == {"class": "alpha beta"}

    def test_attribute_name_cache_does_not_retain_or_hash_string_subclasses(self):
        class AttributeName(str):
            __slots__ = ()

            def __hash__(self):
                raise AssertionError("a user-defined string must not enter the shared validation cache")

        assert validate_html_attr_name(AttributeName("data-item")) == "data-item"

    def test_simple_attribute(self):
        assert format_attrs({"foo": "bar"}) == 'foo="bar"'

    def test_multiple_attributes(self):
        assert format_attrs({"class": "foo", "style": "color: red;"}) == 'class="foo" style="color: red;"'

    def test_case_variants_share_html_identity_and_first_spelling(self):
        assert format_attrs({"ID": "first", "id": "second", "DATA-X": "x"}) == 'ID="second" DATA-X="x"'

    def test_case_variant_class_and_style_accumulate(self):
        attrs = {
            "CLASS": "base",
            "class": {"active": True},
            "STYLE": "color: red",
            "style": {"width": "1px"},
        }
        assert format_attrs(attrs) == 'CLASS="base active" STYLE="color: red; width: 1px;"'

    def test_citry_directive_payloads_remain_case_sensitive(self):
        attrs = {
            "@c-Ready": "first",
            "@c-ready": "second",
            ":c-Value": True,
            ":c-value": True,
            "$c-tr:Save[aria-label]": True,
            "$c-tr:save[aria-label]": True,
            "c-$c-tr:Title[title]": "binding",
        }
        assert format_attrs(attrs) == (
            '@c-Ready="first" @c-ready="second" :c-Value :c-value '
            '$c-tr:Save[aria-label] $c-tr:save[aria-label] c-$c-tr:Title[title]="binding"'
        )

    def test_escapes_special_characters(self):
        assert format_attrs({"x-on:click": "bar", "@click": "'baz'"}) == 'x-on:click="bar" @click="&#39;baz&#39;"'

    def test_escapes_markup_as_attribute_text(self):
        # Markup vouches for HTML, not attribute text: a quote in it must not
        # end the attribute.
        assert format_attrs({"foo": Markup("'bar'")}) == 'foo="&#39;bar&#39;"'
        assert format_attrs({"foo": Markup('a" onclick="x')}) == 'foo="a&#34; onclick=&#34;x"'
        assert format_attrs({"foo": Markup("<i>")}) == 'foo="&lt;i&gt;"'

    def test_markup_class_and_style_pieces_are_decoded_once(self):
        # Splitting or merging a Markup class or style turns it into plain
        # text, which must not escape its entities a second time.
        value = Markup("a &amp;b")
        assert format_attrs({"class": [value]}) == 'class="a &amp;b"'
        assert format_attrs(merge_attrs({"class": value}, {"class": "c"})) == 'class="a &amp;b c"'
        style = Markup('content: "&amp;"')
        assert format_attrs({"style": [style]}) == 'style="content: &#34;&amp;&#34;;"'
        assert format_attrs({"style": {"content": Markup("&lt;")}}) == 'style="content: &lt;;"'

    def test_markup_entities_keep_the_text_they_stand_for(self):
        # Markup's HTML is decoded to what a browser reads, then escaped, so
        # an entity is not escaped a second time.
        assert format_attrs({"foo": Markup("Tom &amp; Jerry")}) == 'foo="Tom &amp; Jerry"'
        assert format_attrs({"foo": Markup("&quot;q&#39;")}) == 'foo="&#34;q&#39;"'
        # A browser keeps a legacy entity before "=" as typed in an attribute.
        assert format_attrs({"href": Markup("/x?a=1&copy=2")}) == 'href="/x?a=1&amp;copy=2"'
        assert format_attrs({"foo": Markup("&copy 2026")}) == 'foo="\u00a9 2026"'

    def test_result_is_markup(self):
        result = format_attrs({"foo": "bar"})
        assert isinstance(result, Markup)

    def test_none_value_omits_attribute(self):
        assert format_attrs({"required": None}) == ""

    def test_false_value_omits_attribute(self):
        assert format_attrs({"required": False}) == ""

    def test_true_value_renders_bare_attribute(self):
        assert format_attrs({"required": True}) == "required"

    @pytest.mark.parametrize(("value", "expected"), [(True, "required"), (False, ""), (None, "")])
    def test_const_marked_booleans_render_like_plain_ones(self, value, expected):
        # Every kwarg reaching a template is Const-wrapped, and a transparent
        # proxy is never identical to True, False, or None. Before the unwrap in
        # format_attrs, `required=False` rendered `required="False"`, which a
        # browser reads as required because the attribute is present at all.
        assert format_attrs({"required": Const(value)}) == expected

    def test_number_value(self):
        assert format_attrs({"data-id": 3}) == 'data-id="3"'

    def test_non_string_attribute_name_raises(self):
        with pytest.raises(TypeError, match="must use string attribute names"):
            format_attrs({1: "value"})

    @pytest.mark.parametrize(
        "name",
        [
            "",
            "bad name",
            "bad\tname",
            "bad\nname",
            "bad\rname",
            "bad=name",
            "bad/name",
            "bad>name",
            "bad<name",
            "bad{#name",
        ],
    )
    def test_malformed_attribute_name_raises(self, name):
        with pytest.raises(ValueError, match="invalid HTML attribute name"):
            format_attrs({name: "value"})

    def test_structured_class_value(self):
        # format_attrs normalizes structured class/style itself, so
        # merge_attrs output and hand-built dicts render the same.
        assert format_attrs({"class": ["btn", {"active": True, "hidden": False}]}) == 'class="btn active"'

    def test_structured_style_value(self):
        assert format_attrs({"style": {"color": "red", "width": False}}) == 'style="color: red;"'

    def test_structured_class_normalizing_to_empty_is_omitted(self):
        # An empty class="" would read as a boolean attribute under citry's
        # HTML rules, so the attribute is dropped instead.
        assert format_attrs({"class": {"hidden": False}, "id": "x"}) == 'id="x"'

    def test_structured_style_normalizing_to_empty_is_omitted(self):
        assert format_attrs({"style": {"color": False}, "id": "x"}) == 'id="x"'

    def test_empty_class_and_style_strings_are_omitted(self):
        assert format_attrs({"class": "", "style": "", "id": "x"}) == 'id="x"'

    def test_empty_class_and_style_from_merge_are_omitted(self):
        attrs = merge_attrs(
            {"class": "shown", "style": {"color": "red"}},
            {"class": {"shown": False}, "style": {"color": False}},
        )

        assert format_attrs(attrs) == ""


class TestMergeAttrs:
    def test_single_dict(self):
        assert merge_attrs({"foo": "bar"}) == {"foo": "bar"}

    def test_appends_classes_across_dicts(self):
        assert merge_attrs({"class": "foo", "id": "bar"}, {"class": "baz"}) == {
            "class": "foo baz",
            "id": "bar",
        }

    def test_merge_with_empty_dict(self):
        assert merge_attrs({}, {"foo": "bar"}) == {"foo": "bar"}

    def test_overlapping_keys_last_one_wins(self):
        # Divergence from django-components, which joins repeated plain keys
        # with a space. Citry resolves every non-class/style key
        # last-one-wins (docs/design/template_html_attrs.md section 4).
        assert merge_attrs({"foo": "bar"}, {"foo": "baz"}) == {"foo": "baz"}
        assert merge_attrs({"foo": None}, {"foo": "bar"}) == {"foo": "bar"}
        assert merge_attrs({"foo": "bar"}, {"foo": None}) == {"foo": None}
        assert merge_attrs({"foo": "bar"}, {"foo": False}) == {"foo": False}

    def test_key_order_is_first_seen(self):
        merged = merge_attrs({"id": "a", "class": "x"}, {"data-x": "1", "id": "b"})
        assert list(merged) == ["id", "class", "data-x"]
        assert merged["id"] == "b"

    def test_case_variants_merge_by_html_identity(self):
        merged = merge_attrs(
            {"ID": "first", "CLASS": "base", "STYLE": "color: red"},
            {"id": "second", "class": "active", "style": {"width": "1px"}},
        )
        assert merged == {
            "ID": "second",
            "CLASS": "base active",
            "STYLE": "color: red; width: 1px;",
        }

    def test_merge_classes(self):
        assert merge_attrs(
            {"class": "foo"},
            {
                "class": [
                    "bar",
                    "tuna",
                    "tuna2",
                    "tuna3",
                    {"baz": True, "baz2": False, "tuna": False, "tuna2": True, "tuna3": None},
                    ["extra", {"extra2": False, "baz2": True, "tuna": True, "tuna2": False}],
                ],
            },
        ) == {"class": "foo bar tuna baz baz2 extra"}

    def test_merge_styles(self):
        assert merge_attrs(
            {"style": "color: red; width: 100px; height: 100px;"},
            {
                "style": [
                    "background-color: blue;",
                    {"background-color": "green", "color": None, "width": False},
                    ["position: absolute", {"height": "12px"}],
                ],
            },
        ) == {"style": "color: red; height: 12px; background-color: green; position: absolute;"}

    def test_merge_class_with_none_values(self):
        # A class is kept only if its last value is truthy.
        assert merge_attrs({"class": {"bar": None}}, {"class": {"bar": True}}) == {"class": "bar"}
        assert merge_attrs({"class": {"bar": True}}, {"class": {"bar": None}}) == {"class": ""}

    def test_merge_class_with_false_values(self):
        assert merge_attrs({"class": {"bar": False}}, {"class": {"bar": True}}) == {"class": "bar"}
        assert merge_attrs({"class": {"bar": True}}, {"class": {"bar": False}}) == {"class": ""}

    def test_merge_style_none_skips_false_removes(self):
        # `None` lets an earlier value stand; `False` removes the property.
        assert merge_attrs({"style": {"color": None}}, {"style": {"color": "blue"}}) == {"style": "color: blue;"}
        assert merge_attrs({"style": {"color": "blue"}}, {"style": {"color": None}}) == {"style": "color: blue;"}
        assert merge_attrs({"style": {"color": False}}, {"style": {"color": "blue"}}) == {"style": "color: blue;"}
        assert merge_attrs({"style": {"color": "blue"}}, {"style": {"color": False}}) == {"style": ""}


class TestNormalizeClass:
    def test_nested_string_subclass_does_not_require_hashing(self):
        class ClassText(str):
            __slots__ = ()

            def __hash__(self):
                raise AssertionError("class normalization must not hash a string subclass")

        assert normalize_class([ClassText("base active"), {"active": False}, ["next"]]) == "base next"

    def test_repeated_class_text_still_observes_mutated_mapping(self):
        flags = {"active": True}
        values = ["base active", flags]
        assert normalize_class(values) == "base active"
        flags["active"] = False
        assert normalize_class(values) == "base"

    def test_string_used_as_is(self):
        assert normalize_class(" btn  btn-lg ") == "btn  btn-lg"

    def test_dict_keeps_truthy_keys(self):
        assert normalize_class({"btn": True, "hidden": False}) == "btn"

    def test_list_mixes_forms(self):
        assert normalize_class(["btn btn-lg", {"active": True, "hidden": False}]) == "btn btn-lg active"

    def test_later_falsy_removes_earlier_class(self):
        # Documented divergence from Vue (django-components behavior): a
        # later falsy dict entry removes a class added earlier.
        assert normalize_class(["a", "b", {"b": False}]) == "a"

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            normalize_class(42)  # type: ignore[arg-type]


class TestNormalizeStyle:
    def test_string_used_as_is(self):
        assert normalize_style(" color: red; ") == "color: red;"

    def test_dict_renders_properties(self):
        assert normalize_style({"color": "red", "background-color": "blue"}) == "color: red; background-color: blue;"

    def test_number_values_render_bare(self):
        assert normalize_style({"width": 100}) == "width: 100;"

    def test_list_merges_last_value_wins(self):
        assert normalize_style(["color: red; width: 100px", {"color": "green", "width": False}]) == "color: green;"

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            normalize_style(42)  # type: ignore[arg-type]


class TestParseStringStyle:
    def test_single_style(self):
        assert parse_string_style("color: red;") == {"color": "red"}

    def test_multiple_styles(self):
        assert parse_string_style("color: red; background-color: blue;") == {
            "color": "red",
            "background-color": "blue",
        }

    def test_with_comments(self):
        assert parse_string_style("color: red /* comment */; background-color: blue;") == {
            "color": "red",
            "background-color": "blue",
        }

    @pytest.mark.parametrize(
        ("css_text", "expected"),
        [
            # Each expected result is what `parseStringStyle` in Vue 3.5.44's
            # `@vue/shared` returns for the same text.
            ('content: "/* keep */"; color: red', {"content": '"/* keep */"', "color": "red"}),
            ("background: url('a/*b*/c.png'); color: red", {"background": "url('a/*b*/c.png')", "color": "red"}),
            ("content: 'it\\'s /* in */'; b: 2", {"content": "'it\\'s /* in */'", "b": "2"}),
            ("font-family: \\/* odd */; color: red", {"font-family": "\\/* odd */", "color": "red"}),
            # An unclosed quote does not protect what follows it.
            ('content: "unclosed /* gone */; color: red', {"content": '"unclosed', "color": "red"}),
            ("a: 1 /* open", {"a": "1 /* open"}),
            ('content: "\\"/* x */"; color: blue', {"content": '"\\"/* x */"', "color": "blue"}),
            ('x: "é/*ü*/"; y: 3', {"x": '"é/*ü*/"', "y": "3"}),
            ('z: "trail\\', {"z": '"trail\\'}),
            # An escape inside a string can be a newline.
            ('content: "a\\\n/* x */"; b: 1', {"content": '"a\\\n/* x */"', "b": "1"}),
        ],
    )
    def test_comment_like_text_in_quotes_and_escapes_is_kept(self, css_text, expected):
        assert parse_string_style(css_text) == expected

    @pytest.mark.parametrize(
        "value",
        ['"' + "a" * 1_000_000 + '"', '"' + "\\a" * 500_000 + '"', "'" + "a" * 1_000_000 + "'", '"' + "a" * 1_000_000],
        ids=["double", "escapes", "single", "unclosed"],
    )
    def test_a_long_quoted_value_costs_about_a_few_copies_of_the_text(self, value):
        css_text = "content: " + value + "; color: red"
        tracemalloc.start()
        try:
            parsed = parse_string_style(css_text)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        assert parsed["color"] == "red"
        assert peak < 8 * len(css_text)

    @pytest.mark.parametrize(
        ("value", "comments"),
        [
            ("\\a" * 500_000, ""),
            ('"a"' * 330_000, ""),
            ("'a'" * 330_000, ""),
            ("a" * 1_000, "/**/" * 250_000),
        ],
        ids=["escapes", "short-strings", "short-single-quoted", "comments"],
    )
    def test_many_short_escapes_strings_or_comments_cost_about_one_copy_of_the_text(self, value, comments):
        css_text = "content: " + value + comments + "; color: red"
        expected = {"content": value, "color": "red"}
        tracemalloc.start()
        try:
            parsed = parse_string_style(css_text)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        assert parsed == expected
        # The text kept between comments is copied once; a small string per
        # escape or quoted string would cost many bytes per character.
        assert peak < 4 * len(css_text)

    def test_with_whitespace(self):
        assert parse_string_style("  color: red;  background-color: blue;  ") == {
            "color": "red",
            "background-color": "blue",
        }

    def test_empty_string(self):
        assert parse_string_style("") == {}

    def test_semicolon_inside_parentheses_is_kept(self):
        assert parse_string_style("background: url(data:image/png;base64,abc); color: red") == {
            "background": "url(data:image/png;base64,abc)",
            "color": "red",
        }

    def test_no_delimiters(self):
        assert parse_string_style("color: red background-color: blue") == {"color": "red background-color: blue"}

    def test_incomplete_style(self):
        assert parse_string_style("color: red; background-color") == {"color": "red"}


class TestStyleDeclarationSplit:
    r"""
    The style splitter walks the text once and splits as Vue's regex does.

    Vue's ``parseStringStyle`` splits on ``;(?![^(]*\))``. Running that regex
    takes time growing with the square of the length, and a style can come
    from data, so Citry applies the same rule in one pass.
    """

    _VUE_SPLIT = re.compile(r";(?![^(]*\))", re.DOTALL)

    def test_it_splits_exactly_as_the_regex_on_random_text(self):
        rng = random.Random(1234)  # noqa: S311 - test data, not secrets
        alphabet = ";():a \n\\\"'/*"
        for _ in range(20_000):
            text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
            assert _split_style_declarations(text) == self._VUE_SPLIT.split(text), text

    @pytest.mark.parametrize(
        "text",
        [
            "",
            ";",
            "a;b",
            "url(a;b)",
            # The regex only looks for the next parenthesis, so a `;` before
            # a nested `(` splits even inside an outer `url(`.
            "url(a;(b))",
            "a;b)",
            "(;",
            "x:url(data:image/png;base64,abc);y:1",
        ],
    )
    def test_edge_cases_match_the_regex(self, text):
        assert _split_style_declarations(text) == self._VUE_SPLIT.split(text)

    def test_a_long_style_from_data_parses_quickly(self):
        def parse(semicolons):
            assert parse_string_style(";" * semicolons + "color: red") == {"color": "red"}
            assert parse_string_style("(" + ";" * semicolons + ")") == {}

        # The regex took seconds for 100,000 semicolons. Eight times as many
        # may take about eight times as long, not sixty-four.
        assert_grows_in_step(parse, 12_500, 100_000, factor=8)

    def test_a_long_style_from_data_renders_quickly_on_the_static_and_vue_paths(self):
        app = Citry(secret="s" * 40)

        class Plain(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"attrs": kwargs["attrs"]}

            template = """
                <div style="color: red" c-bind="attrs">p</div>
            """

        class Interactive(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"attrs": kwargs["attrs"]}

            template = """
                <div style="color: red" c-bind="attrs">v</div>
            """

            js = """
                $component({})
            """

        for component in (Plain, Interactive):

            def render(semicolons, component=component):
                html = str(component(attrs={"style": ";" * semicolons + "width: 1px"}))
                assert "width: 1px" in html

            assert_grows_in_step(render, 12_500, 100_000, factor=8)


class TestStyleCommentRemoval:
    """
    Comments are removed from a style string in one pass, with the same result as before.

    ``_RELEASED_COMMENT_RE`` is the comment regex of Citry 0.7.0 and earlier:
    it removes each ``/* ... */`` and keeps quoted strings and escapes. On
    text with many ``/*`` and no ``*/`` it searches to the end again from
    every ``/*``, which took over 2 s for a 60,000-character style from data.
    """

    _RELEASED_COMMENT_RE = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\\.|/\*.*?\*/", re.DOTALL)

    def _released_parse(self, text):
        # parse_string_style's steps with the released comment regex.
        text = self._RELEASED_COMMENT_RE.sub(
            lambda match: "" if match.group().startswith("/*") else match.group(), text
        )
        result = {}
        for declaration in _split_style_declarations(text):
            parts = _style_property_re.split(declaration)
            if len(parts) > 1:
                result[parts[0].strip()] = parts[1].strip()
        return result

    def test_it_parses_exactly_as_the_released_regex_on_random_text(self):
        rng = random.Random(4321)  # noqa: S311 - test data, not secrets
        pieces = ["/*", "*/", "/", "*", '"', "'", "\\", "a", ";", ":", "(", ")", " ", "\n", "é"]
        for _ in range(20_000):
            text = "".join(rng.choice(pieces) for _ in range(rng.randint(0, 30)))
            assert parse_string_style(text) == self._released_parse(text), text

    @pytest.mark.parametrize(
        ("css_text", "expected"),
        [
            # An unclosed comment stays, and so does any later `/*`.
            ("a: 1; b: 2 /* x /* y", {"a": "1", "b": "2 /* x /* y"}),
            # `/*/` does not close itself.
            ("a: 1 /*/ b: 2", {"a": "1 /*/ b: 2"}),
            ("a: 1 /*/ x */; b: 2", {"a": "1", "b": "2"}),
            ("a: 1 /**/; b: 2", {"a": "1", "b": "2"}),
            ("a: 1; /* x */ /* y", {"a": "1"}),
        ],
    )
    def test_closed_and_unclosed_comments(self, css_text, expected):
        assert parse_string_style(css_text) == self._released_parse(css_text)
        assert parse_string_style(css_text) == expected

    # Every unit opens a comment that nothing closes; the released regex took
    # 1.3 s to 2.8 s on each of these texts.
    @pytest.mark.parametrize("unit", ["/* ", "/*a", "/*\n", "/* ;", "/*(", '"/*', "'/*", '/*"'])
    def test_many_unclosed_comments_parse_quickly(self, unit):
        def parse(length):
            result = parse_string_style("a: 1; b: " + unit * (length // len(unit)))
            assert result["a"] == "1"

        # Eight times as much text may take about eight times as long.
        assert_grows_in_step(parse, 7_500, 60_000, factor=8)

    def test_a_style_from_data_with_unclosed_comments_renders_quickly(self):
        app = Citry(secret="s" * 40)

        class Plain(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"style": kwargs["style"]}

            template = """
                <div style="color: red" c-style="style">p</div>
            """

        class Interactive(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"style": kwargs["style"]}

            template = """
                <div style="color: red" c-style="style">v</div>
            """

            js = """
                $component({})
            """

        for component in (Plain, Interactive):

            def render(comments, component=component):
                html = str(component(style="width: 1px; " + "/* " * comments))
                assert "width: 1px" in html

            assert_grows_in_step(render, 2_500, 20_000, factor=8)


class TestConstMarkedValues:
    """
    The normalizers accept ``Const``-marked strings. The engine auto-marks
    template literals on component tags, so such a value can flow unchanged
    into a class or style position; it is a transparent proxy that passes
    ``isinstance(str)`` but would otherwise break the internal regex calls.
    """

    def test_const_string_in_class_list(self):
        from citry import Const

        # The marker survives until it reaches a class list; normalization
        # must still split it into class names.
        assert normalize_class([Const("a b"), "c"]) == "a b c"

    def test_const_class_dict_value(self):
        from citry import Const

        assert normalize_class(["base", {"on": Const(True), "off": Const(False)}]) == "base on"  # noqa: FBT003

    def test_const_string_in_style_list(self):
        from citry import Const

        assert normalize_style([Const("color: red"), {"width": "1px"}]) == "color: red; width: 1px;"

    def test_const_passed_to_parse_string_style(self):
        from citry import Const

        assert parse_string_style(Const("color: red; width: 1px")) == {"color": "red", "width": "1px"}

    def test_const_wrapped_whole_list_is_not_flattened_to_repr(self):
        from citry import Const

        # The whole list (not just an element) can arrive marked. Unwrapping
        # must keep it a list so each class name is split out, not str()-ed
        # into the list's repr.
        assert normalize_class(Const(["a", "b"])) == "a b"


class TestElementKeyText:
    def test_markup_key_is_escaped_as_text(self):
        # The key is identity text, so Markup in it cannot add markup to the
        # tag, the same as on the prepared path.
        class Attr:
            source = "s"
            position = (0, 1)
            used_vars = ()

            def resolve(self, _context):
                return Markup('a"b<i>')

        assert ElementKeyNode(Attr()).render(None) == ' data-citry-key=":a&#34;b&lt;i&gt;"'


class TestExactStr:
    def test_an_exact_str_is_returned_as_is(self):
        name = "@click"
        assert exact_str(name) is name

    def test_a_subclass_comes_back_as_an_exact_str_with_the_same_text(self):
        class Disguised(str):
            __slots__ = ()

            def startswith(self, *_args, **_kwargs):
                return False

            def __str__(self):
                return "title"

        result = exact_str(Disguised("@click"))
        assert type(result) is str
        assert result == "@click"
        assert result.startswith("@")
