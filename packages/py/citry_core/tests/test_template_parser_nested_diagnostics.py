import pytest

from citry_core.template_parser import parse_template


@pytest.mark.parametrize(
    "source",
    [
        '<c-long-component c-body="<div><span></span>" />',
        '<c-x c-body="<><div></>" />',
    ],
)
def test_unclosed_nested_template_raises_syntax_error(source):
    with pytest.raises(SyntaxError):
        parse_template(source)


def test_nested_mismatch_uses_root_source_coordinates():
    source = 'before\n<c-x c-body="<div></span>" />'
    with pytest.raises(SyntaxError) as exc_info:
        parse_template(source)

    message = str(exc_info.value)
    assert "--> 2:19" in message
    assert '<c-x c-body="<div></span>" />' in message


def test_nested_expression_error_uses_root_source_coordinates():
    source = 'before\n<c-x c-body="<div>{{ 1 + }}</div>" />'
    with pytest.raises(SyntaxError) as exc_info:
        parse_template(source)

    message = str(exc_info.value)
    assert "--> 2:22" in message
    assert '<c-x c-body="<div>{{ 1 + }}</div>" />' in message


def test_nested_validation_error_uses_root_source_coordinates():
    source = 'before\n<c-x c-body="<c-if>oops</c-if>" />'
    with pytest.raises(SyntaxError) as exc_info:
        parse_template(source)

    message = str(exc_info.value)
    assert "--> 2:14" in message
    assert '<c-x c-body="<c-if>oops</c-if>" />' in message


def test_nested_grammar_error_is_not_a_diagnostic_inside_a_diagnostic():
    source = 'before\n<c-x c-body="<>{{</>" />'
    with pytest.raises(SyntaxError) as exc_info:
        parse_template(source)

    message = str(exc_info.value)
    assert "--> 2:" in message
    assert '<c-x c-body="<>{{</>" />' in message
    assert message.count("-->") == 1
