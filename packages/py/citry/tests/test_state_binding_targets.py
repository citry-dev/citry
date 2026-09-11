"""Portable State target checks agree with the runtime control contract."""

import re

import pytest

from citry import Citry, Component
from citry.analysis import browser_state_binding_target_errors
from citry_core.template_parser import parse_template


def _render(source):
    app = Citry(secret="test-secret")  # noqa: S106 - isolated test signing key

    class Target(Component):
        citry = app
        template = source

        class State:
            q: str = ""

        class Events:
            def go(self):
                return None

    return Target().render().serialize()


@pytest.mark.parametrize(
    "source",
    [
        "<head :c-q></head>",
        '<div :c-q.on:click="go"></div>',
        "<annotation-xml :c-q></annotation-xml>",
        '<input type="file" :c-q>',
        '<input TYPE="submit" :c-q>',
        '<input type="hidden" :c-q="go">',
        '<input type="wat" :c-q>',
        '<my-widget :c-q="go"></my-widget>',
        '<c-element is="head" :c-q></c-element>',
    ],
)
def test_portable_target_error_matches_runtime_wording(source):
    errors = browser_state_binding_target_errors(parse_template(source))
    assert len(errors) == 1
    error = errors[0]
    assert source.encode()[error.start_index : error.end_index].decode().startswith(":c-q")
    with pytest.raises(ValueError, match=re.escape(error.message)) as raised:
        _render(source)
    assert error.message in str(raised.value)


@pytest.mark.parametrize(
    "source",
    [
        "<input :c-q>",
        '<input type="hidden" :c-q>',
        '<input type="text" :c-q="go">',
        '<textarea :c-q="go"></textarea>',
        '<select :c-q="go"></select>',
        '<my-widget :c-q.on:change="go"></my-widget>',
        "<my-widget :c-q></my-widget>",
        '<c-element is="input" :c-q></c-element>',
    ],
)
def test_supported_target_has_no_error_and_renders(source):
    assert browser_state_binding_target_errors(parse_template(source)) == ()
    assert "data-cev-bind" in _render(source)


@pytest.mark.parametrize(
    "source",
    [
        '<c-element c-is="tag" :c-q></c-element>',
        '<c-element is="head" c-bind="attrs" :c-q></c-element>',
        '<input c-type="kind" :c-q>',
        '<input type="file" :type="kind" :c-q>',
        '<input type="file" c-bind="attrs" :c-q>',
    ],
)
def test_dynamic_target_checks_defer(source):
    assert browser_state_binding_target_errors(parse_template(source)) == ()


def test_utf8_key_range_and_non_attribute_text():
    source = 'é<!-- <head :c-q> --><script>"<head :c-q>"</script><head :c-q.on:click="go"></head>'
    (error,) = browser_state_binding_target_errors(parse_template(source))
    assert source.encode()[error.start_index : error.end_index] == b":c-q.on:click"
    assert error.start_index == len(source[: source.rindex(":c-q")].encode())


def test_nested_template_key_range_and_component_target():
    source = 'é<c-panel c-body="<><head :c-q></head></>" :c-q />'
    errors = browser_state_binding_target_errors(parse_template(source))
    assert len(errors) == 2
    assert [source.encode()[error.start_index : error.end_index] for error in errors] == [b":c-q", b":c-q"]
    assert "<head>" in errors[0].message
    assert "<c-panel>" in errors[1].message


def test_raw_template_body_is_not_a_binding_target():
    assert browser_state_binding_target_errors(parse_template("<c-raw><head :c-q></head></c-raw>")) == ()


@pytest.mark.parametrize("two_way", [False, True])
@pytest.mark.parametrize(
    "input_type",
    [
        "text",
        "search",
        "tel",
        "url",
        "email",
        "password",
        "date",
        "month",
        "week",
        "time",
        "datetime-local",
        "number",
        "range",
        "color",
        "checkbox",
        "radio",
        "hidden",
        "file",
        "submit",
        "image",
        "reset",
        "button",
    ],
)
def test_complete_input_direction_matrix(input_type, two_way):
    handler = '="go"' if two_way else ""
    source = f'<input type="{input_type}" :c-q{handler}>'
    invalid = input_type in {"file", "submit", "image", "reset", "button"} or (input_type == "hidden" and two_way)
    errors = browser_state_binding_target_errors(parse_template(source))
    assert bool(errors) is invalid
