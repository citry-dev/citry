"""
Tests for reading which classes and custom properties CSS declares, and which classes a template uses.

The CSS lint rules in ``citry check`` trust these readers to tell a selector
from a value, a comment, or a string, so each case here is a place where a
looser reader would invent or miss a declaration.
"""

import pytest

from citry._css_lint import TemplateClass, code_custom_properties, template_css
from citry._css_scan import ClassPattern, scan_css, split_class_attribute
from citry_core.template_parser import parse_template


@pytest.mark.parametrize(
    ("css", "classes"),
    [
        # A class anywhere in a selector counts, not only the first one.
        (".a .b, .c:hover > .d.e, :is(.f, .g) :not(.h) {}", {"a", "b", "c", "d", "e", "f", "g", "h"}),
        # Rules inside at-rules and nested rules count.
        ("@media (min-width: 10.5em) { .a {} @supports (display: grid) { .b {} } }", {"a", "b"}),
        (".a { color: red; &.b {} .c & {} @media print { .d {} } }", {"a", "b", "c", "d"}),
        ("@layer base { .a {} } @container card (width > 1px) { .b {} }", {"a", "b"}),
        ("@scope (.card) to (.content) { .title {} }", {"card", "content", "title"}),
        # Values, comments, and strings hold no selector.
        (".a { margin: .5em; font: 1.5em/1.2 serif; }", {"a"}),
        ("/* .b */ .a[title='.c'] { content: '.d'; }", {"a"}),
        # An unquoted url() may hold `;` and `{` that end nothing.
        (".a { background: url(x.png?.b;c{) } .d {}", {"a", "d"}),
        # Keyframe selectors and font faces name no class.
        ("@keyframes spin { 12.5% { opacity: .5 } to {} } @font-face { src: url(x.woff); }", set()),
        # Escapes are decoded, so Tailwind-style names match the template.
        (r".md\:flex, .w-1\/2, .\31 23 {}", {"md:flex", "w-1/2", "123"}),
        # A class name cannot start with a digit, or with a hyphen and a digit.
        (".-ok, .--ok, .-0no, .0no {}", {"-ok", "--ok"}),
        # A block-less at-rule ends at its semicolon.
        ("@import url(foo.css); @charset 'utf-8'; .a {}", {"a"}),
        ("@when media(width > 1px) { .a {} } @else { .b {} }", {"a", "b"}),
        # A view transition class is not a class on an element.
        ("::view-transition-group(.card) {} .a {}", {"a"}),
        ("::view-transition, .a, ::before .b {}", {"a", "b"}),
        # An unquoted url() in a custom property's value ends nothing.
        (".a { --bg: url(a{b.png) } .b {}", {"a", "b"}),
    ],
)
def test_class_selectors_are_read_from_every_part_of_a_selector(css, classes):
    assert scan_css(css).classes == classes


@pytest.mark.parametrize(
    ("css", "classes"),
    [
        # An unclosed block ends with the source.
        (".a { color: red", {"a"}),
        # A stray closing brace at the top level is skipped.
        ("} .a {}", {"a"}),
        # An unclosed string ends at its line, as in a browser.
        (".a::after { content: 'x\n} .b {}", {"a", "b"}),
        # An unclosed comment hides the rest of the source.
        (".a {} /* .b {}", {"a"}),
        # A custom property at the top level is an invalid rule a browser
        # drops alone, so the rules after it still count.
        ("--x: {} .a {} .b {}", {"a", "b"}),
        # Thousands of unclosed blocks do not exhaust Python's call stack.
        ("@media x {" * 5000 + ".a {}", {"a"}),
    ],
    # Short ids: pytest puts a test's id in the PYTEST_CURRENT_TEST variable,
    # and Windows rejects an environment variable over 32,767 characters.
    ids=[
        "unclosed-block",
        "stray-closing-brace",
        "unclosed-string",
        "unclosed-comment",
        "top-level-custom-property",
        "deeply-nested-blocks",
    ],
)
def test_malformed_css_is_read_as_far_as_a_browser_reads_it(css, classes):
    assert scan_css(css).classes == classes


def test_class_attribute_selectors_declare_whole_classes_or_patterns():
    declarations = scan_css(
        """[class~='a'], [class="b c"], [class^=btn-], [class*="ICON" i],
        [class|=tag], [data-x='.nope'], [svg|class$="-end"],
        [class~="no match"] {}"""
    )

    assert declarations.classes == {"a", "b", "c"}
    assert declarations.class_patterns == (
        ClassPattern("^=", "btn-", ignore_case=False),
        ClassPattern("*=", "ICON", ignore_case=True),
        ClassPattern("|=", "tag", ignore_case=False),
        ClassPattern("$=", "-end", ignore_case=False),
    )
    assert declarations.declares_class("btn-primary")
    assert declarations.declares_class("my-icon")
    assert declarations.declares_class("tag-red")
    assert declarations.declares_class("box-end")
    assert not declarations.declares_class("button")
    assert not declarations.declares_class("tagged")


def test_custom_properties_come_from_declarations_and_at_property():
    declarations = scan_css(
        """
        :root { --accent: red; --object: { a: b }; }
        .a { --gap : 1rem }
        .b { --data: url(a;b); color: var(--unset); }
        @property --size { syntax: '<length>'; inherits: false; initial-value: 0; }
        """
    )

    assert declarations.custom_properties == {"accent", "object", "gap", "data", "size"}
    # A custom property's value holds no selector, even with braces in it.
    assert declarations.classes == {"a", "b"}


def test_split_class_attribute_splits_on_html_whitespace_and_keeps_positions():
    assert split_class_attribute(" a\tbb\n c ") == [("a", 1, 2), ("bb", 3, 5), ("c", 7, 8)]


def _template_css(source: str):
    return template_css(parse_template(source), parse_nested=parse_template)


def test_template_classes_are_read_with_byte_offsets():
    source = '<p title="é"><span class="x  é-b"></span></p>'

    used = _template_css(source)

    encoded = source.encode("utf-8")
    assert used.classes == (
        TemplateClass("x", encoded.index(b"x  "), encoded.index(b"x  ") + 1),
        TemplateClass("é-b", encoded.index("é-b".encode()), encoded.index("é-b".encode()) + len("é-b".encode())),
    )


def test_template_classes_skip_bindings_control_tags_and_written_expressions():
    used = _template_css(
        """
        <div :class="a" c-class="b" v-bind:class="c" class="d {{ e }} {{f}}g"></div>
        <p class="m {{ n o"></p>
        <template class="f"></template>
        <c-if cond="x"><i class="g&amp;h"></i></c-if>
        <c-Card class="k" />
        """
    )

    # `d` renders as typed; the words inside `{{ }}`, and a word joined to
    # one, are an expression the author meant to bind.
    assert [item.name for item in used.classes] == ["d", "m", "g&h", "k"]


def test_code_names_custom_properties_in_strings():
    source = """el.style.setProperty('--gap', size); style = f"--accent: {color};"; x = "--flag" """

    assert code_custom_properties(source) == {"gap", "accent", "flag"}


def test_template_style_elements_and_attributes_declare_css():
    used = _template_css(
        """
        <style>.from-style { --from-style: 1; }</style>
        <style lang="scss">.from-scss { --from-scss: 1; }</style>
        <style :lang="language">.from-bound { --from-bound: 1; }</style>
        <style type>.from-bare-type {}</style>
        <div style="--from-attribute: 2; color: red" :style="{'--from-binding': size}"></div>
        """
    )

    assert used.declarations.classes == {"from-style", "from-bare-type"}
    assert used.declarations.custom_properties == {"from-style", "from-attribute", "from-binding"}


@pytest.mark.parametrize(
    "source",
    [
        # Vue leaves `:style` under `v-pre` as an attribute literally named
        # `:style`, which sets no custom property.
        "<div v-pre :style=\"{'--gap': size}\"></div>",
        "<section v-pre><div :style=\"{'--gap': size}\"></div></section>",
        "<div v-pre v-bind:style=\"{'--gap': size}\"></div>",
        # In a template-valued attribute, whether `v-pre` is inside or outside it.
        "<c-card c-header='<><p v-pre :style=\"{`--gap`: size}\"></p></>' />",
        "<div v-pre><c-card c-header='<><p :style=\"{`--gap`: size}\"></p></>' /></div>",
    ],
)
def test_a_style_binding_at_or_inside_v_pre_sets_no_custom_property(source):
    assert _template_css(source).declarations.custom_properties == set()


@pytest.mark.parametrize(
    "source",
    [
        # Citry renders `c-style` on the server before Vue sees the page.
        "<div v-pre c-style=\"{'--gap': size}\"></div>",
        "<section v-pre><div c-style=\"{'--gap': size}\"></div></section>",
        # A plain `style` attribute is read by the browser, not by Vue.
        '<div v-pre style="--gap: 1rem"></div>',
        # Outside `v-pre` the binding still sets it, including after a `v-pre` sibling.
        "<div v-pre></div><div :style=\"{'--gap': size}\"></div>",
        "<c-card c-header='<><p :style=\"{`--gap`: size}\"></p></>' />",
    ],
)
def test_citry_and_plain_styles_at_or_inside_v_pre_and_bindings_outside_it_still_set_a_custom_property(source):
    assert _template_css(source).declarations.custom_properties == {"gap"}
