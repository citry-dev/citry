import pytest

from citry import Citry, Component


def _render(template):
    engine = Citry()

    class Root(Component):
        citry = engine

    Root.template = template
    return Root().render().serialize()


@pytest.mark.parametrize(
    "template",
    [
        '<p c-if="<></>">if</p>',
        '<p c-if="<>{{ x }}</>">if</p>',
        '<p c-if="<c-child />">if</p>',
        '<p c-if="x">if</p><p c-elif="<>{{ y }}</>">elif</p>',
        '<p c-for="<></>">item</p>',
        '<p c-if="x">if</p><p c-else="x">else</p>',
        '<p c-for="i in items">item</p><p c-empty="x">empty</p>',
    ],
)
def test_invalid_shorthand_values_raise_syntax_error(template):
    with pytest.raises(SyntaxError):
        _render(template)


@pytest.mark.parametrize(
    "template",
    [
        '<p c-elif="x">orphan</p>',
        "<p c-else>orphan</p>",
        "<p c-empty>orphan</p>",
        '<p c-if="x">if</p>text<p c-else>else</p>',
        '<p c-for="i in items">item</p>text<p c-empty>empty</p>',
        '<p c-if="x">if</p><p c-else>else</p><p c-elif="y">late</p>',
    ],
)
def test_invalid_shorthand_grouping_raises_syntax_error(template):
    with pytest.raises(SyntaxError, match="must follow one of"):
        _render(template)
