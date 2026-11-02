"""
A template cannot read attribute paths through the format methods of a `Markup` value.

`Markup.format` and `Markup.format_map` follow the `{0.name}` paths written in the string
with the real `getattr`, so before the sandbox refused them a template could read what the
sandbox hides everywhere else, such as a function's module globals. `Markup` is the string
type Citry's own helpers return, so these tests render real components with a `Markup`
value in the context.
"""

import pytest
from markupsafe import Markup

from citry import Citry, Component, SecurityError, Slot

# A module global that the test template tries to read through a function's `__globals__`.
SECRET_SETTING = "SECRET-MARKER"  # noqa: S105 - a marker value that tests look for, not a password


def a_helper() -> None:
    """A function the app puts in the context; its `__globals__` is this module's namespace."""


def _component(app: Citry, text: str, *, items: list[str] | None = None) -> type[Component]:
    """Define a page that renders `text` with a `Markup` value and a function in its context."""

    class Page(Component):
        citry = app
        template = text

        def template_data(self, kwargs, slots):
            return {
                "m": Markup("x"),
                "body": Slot("x"),
                "f": a_helper,
                "mapping": {"o": a_helper},
                "items": items or [],
            }

    return Page


# The text sits in an expression the template author wrote, in each place one can go.
_READ_THROUGH_FORMAT = 'm.replace("x", "{0.__globals__[SECRET_SETTING]}").format(f)'
_READ_THROUGH_FORMAT_MAP = 'm.replace("x", "{o.__globals__[SECRET_SETTING]}").format_map(mapping)'


@pytest.mark.parametrize(
    "template",
    [
        pytest.param(f"<p>{{{{ {_READ_THROUGH_FORMAT} }}}}</p>", id="text-format"),
        pytest.param(f"<p>{{{{ {_READ_THROUGH_FORMAT_MAP} }}}}</p>", id="text-format_map"),
        pytest.param(f"<p c-title='{_READ_THROUGH_FORMAT}'>x</p>", id="attribute-format"),
        pytest.param(f"<p c-if='{_READ_THROUGH_FORMAT}'>x</p>", id="c-if-format"),
        pytest.param(f"<p>{{{{ f'{{{_READ_THROUGH_FORMAT}}}' }}}}</p>", id="inside-f-string"),
    ],
)
def test_the_sandbox_refuses_markup_format_methods(template):
    page = _component(Citry(), template)
    with pytest.raises(SecurityError) as error:
        page().render().serialize()
    # The refusal comes before the lookup, so the value never reaches the message.
    assert "SECRET-MARKER" not in str(error.value)


def test_the_text_a_slot_returns_is_covered_too():
    # Calling a `Slot` gives Citry's own `Markup` subclass, so a template that holds a
    # slot needs no `Markup` from the app to reach `format`.
    template = '<p>{{ body().replace("x", "{0.__globals__[SECRET_SETTING]}").format(f) }}</p>'
    page = _component(Citry(), template)
    with pytest.raises(SecurityError) as error:
        page().render().serialize()
    assert "SECRET-MARKER" not in str(error.value)


@pytest.mark.parametrize("template", [f"<p>{{{{ {_READ_THROUGH_FORMAT} }}}}</p>"])
def test_the_same_template_reads_the_value_when_the_sandbox_is_off(template):
    # Control: the template does read the value without the sandbox, so the test above
    # fails if the refusal stops working.
    page = _component(Citry(sandbox_expressions=False), template)
    assert "SECRET-MARKER" in page().render().serialize()


def test_other_markup_methods_still_work():
    page = _component(Citry(), '<p>{{ m.upper() }}{{ m.replace("x", "y") }}{{ m + "!" }}</p>')
    assert "Xyx!" in page().render().serialize()


@pytest.mark.parametrize("sandbox", [True, False])
@pytest.mark.parametrize("name", ["source", "template", "context", "call", "variable"])
def test_a_loop_variable_named_like_a_sandbox_helper_renders(sandbox, name):
    # The sandbox's own helpers have `_sx_` names, so a loop variable such as
    # `source` in `<source c-for="source in sources">` is an ordinary name.
    page = _component(
        Citry(sandbox_expressions=sandbox),
        f'<ul><c-for each="{name} in items"><li>{{{{ {name}.upper() }}}}</li></c-for></ul>',
        items=["a", "b"],
    )
    html = page().render().serialize()
    assert "<li>A</li><li>B</li>" in html


@pytest.mark.parametrize("sandbox", [True, False])
def test_a_loop_variable_with_the_sandbox_prefix_is_a_syntax_error(sandbox):
    page = _component(
        Citry(sandbox_expressions=sandbox),
        '<ul><c-for each="_sx_item in items"><li>{{ _sx_item }}</li></c-for></ul>',
        items=["a"],
    )
    with pytest.raises(SyntaxError, match="'_sx_item' starts with '_sx_'"):
        page().render().serialize()
