"""
Runtime tests for `<c-raw>`: a verbatim block that emits its contents
literally, with no template processing.

`<c-raw>` used to compile to a `ComponentNode` named "raw" and raise
`NotRegistered` at render time; it now compiles to a literal text part.
"""

from citry import Citry, Component


def _render(template):
    """Render a single-component template to a string (fresh Citry each call)."""
    c = Citry()

    class T(Component):
        citry = c

    T.template = template
    return str(T())


def test_raw_renders_literal_text():
    # The inner `{{ x }}` is emitted verbatim, not evaluated: there is no `x` in
    # scope, and rendering still succeeds precisely because it stays literal.
    assert _render("<c-raw>hi {{ x }}</c-raw>") == "hi {{ x }}"


def test_raw_does_not_raise_not_registered():
    # Regression: `<c-raw>` used to compile to a ComponentNode("raw") and raise
    # NotRegistered: "No component registered as 'raw'".
    assert _render("<c-raw>plain</c-raw>") == "plain"


def test_raw_empty_renders_nothing():
    assert _render("<c-raw></c-raw>") == ""


def test_raw_inner_component_tag_not_resolved():
    # `<c-Foo />` inside a raw block is literal text, never looked up as a
    # component (which would raise NotRegistered).
    assert _render("<div><c-raw><c-Foo /></c-raw></div>") == '<div data-cid-c1=""><c-Foo /></div>'


def test_raw_content_not_html_escaped():
    # Raw means raw: `<` and `&&` pass through unescaped.
    assert _render("<div><c-raw>a < b && c</c-raw></div>") == '<div data-cid-c1="">a < b && c</div>'
