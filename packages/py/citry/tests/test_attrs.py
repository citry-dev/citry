"""
Tests for the attribute value helpers (docs/design/html_attrs.md sections 3
and 4): class/style normalization, merging, and formatting.

Ported from django-components' tests/test_attributes.py where the semantics
match. Divergences from django-components are tested explicitly and marked
with a comment saying what changed and why.
"""

# ruff: noqa: ANN

import pytest

from citry import format_attrs, merge_attrs, normalize_class, normalize_style, parse_string_style
from citry.util.html import SafeString


class TestFormatAttrs:
    def test_simple_attribute(self):
        assert format_attrs({"foo": "bar"}) == 'foo="bar"'

    def test_multiple_attributes(self):
        assert format_attrs({"class": "foo", "style": "color: red;"}) == 'class="foo" style="color: red;"'

    def test_escapes_special_characters(self):
        assert format_attrs({"x-on:click": "bar", "@click": "'baz'"}) == 'x-on:click="bar" @click="&#39;baz&#39;"'

    def test_does_not_escape_safe_strings(self):
        assert format_attrs({"foo": SafeString("'bar'")}) == "foo=\"'bar'\""

    def test_result_is_safe_string(self):
        result = format_attrs({"foo": "bar"})
        assert isinstance(result, SafeString)

    def test_none_value_omits_attribute(self):
        assert format_attrs({"required": None}) == ""

    def test_false_value_omits_attribute(self):
        assert format_attrs({"required": False}) == ""

    def test_true_value_renders_bare_attribute(self):
        assert format_attrs({"required": True}) == "required"

    def test_number_value(self):
        assert format_attrs({"data-id": 3}) == 'data-id="3"'

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
        # last-one-wins (docs/design/html_attrs.md section 4).
        assert merge_attrs({"foo": "bar"}, {"foo": "baz"}) == {"foo": "baz"}
        assert merge_attrs({"foo": None}, {"foo": "bar"}) == {"foo": "bar"}
        assert merge_attrs({"foo": "bar"}, {"foo": None}) == {"foo": None}
        assert merge_attrs({"foo": "bar"}, {"foo": False}) == {"foo": False}

    def test_key_order_is_first_seen(self):
        merged = merge_attrs({"id": "a", "class": "x"}, {"data-x": "1", "id": "b"})
        assert list(merged) == ["id", "class", "data-x"]
        assert merged["id"] == "b"

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
