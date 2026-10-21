"""
Render errors on a page that uses Vue name the component, its template, the line, and the fix.

Two mistakes reach the author only when the page renders:

- a component that a `<c-for>` repeats with no `#c-key`, or with a
  `#c-key` that two items share;
- `v-model` on an element that holds no value, such as `<div>`. Vue's
  compiler reports it with no position, so Citry finds the element in the
  authored template with the rule `citry check` uses.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component
from citry._vue.capture import UnsupportedPreparedView
from citry._vue.compiler import VueCompilerDiagnosticsError

if TYPE_CHECKING:
    from pathlib import Path

# Any browser code makes the page use Vue.
_VUE_JS = """
    export default { data() { return { query: "" } } }
"""


def _render(component: Component) -> str:
    """Render to HTML, the point where the page's Vue template is built and compiled."""
    return str(component.render())


def _card(registry: Citry) -> type[Component]:
    class Card(Component):
        citry = registry
        template = """
            <i>card</i>
        """

    return Card


# A repeated component without a usable #c-key (m51)


def test_repeated_component_without_key_names_tag_template_and_line() -> None:
    registry = Citry(autodiscover=False)
    _card(registry)

    class Page(Component):
        citry = registry
        template = """
            <ul>
              <c-for each="item in items"><c-card /></c-for>
            </ul>
        """
        js = _VUE_JS

        def template_data(self, kwargs, slots):
            return {"items": [1, 2]}

    with pytest.raises(UnsupportedPreparedView) as info:
        _render(Page())
    message = str(info.value)
    # The line counts from the start of the inline template string.
    assert re.search(r"<c-card> in template \S+::Page, line 3 repeats inside a loop but has no #c-key", message)
    assert 'needs a #c-key whose value identifies its item, such as #c-key="item.id" on <c-card>.' in message


def test_repeated_component_key_of_none_counts_as_missing() -> None:
    registry = Citry(autodiscover=False)
    _card(registry)

    class Page(Component):
        citry = registry
        template = """
            <c-for each="item in items"><c-card #c-key="None" /></c-for>
        """
        js = _VUE_JS

        def template_data(self, kwargs, slots):
            return {"items": [1, 2]}

    with pytest.raises(UnsupportedPreparedView, match=r"has no #c-key, or its #c-key is None"):
        _render(Page())


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        ("<c-card />", "repeats inside a loop but has no #c-key"),
        (
            "<c-card #c-key=\"'same'\" />",
            "has a duplicate #c-key, 'same': two of its repetitions got that value",
        ),
    ],
)
def test_repeated_component_errors_name_the_template_file(tmp_path: Path, call: str, expected: str) -> None:
    registry = Citry(autodiscover=False)
    _card(registry)
    template_path = tmp_path / "page.html"
    template_path.write_text(f'<ul>\n  <c-for each="item in items">\n    {call}\n  </c-for>\n</ul>\n')

    class Page(Component):
        citry = registry
        template_file = str(template_path)
        js = _VUE_JS

        def template_data(self, kwargs, slots):
            return {"items": [1, 2]}

    with pytest.raises(UnsupportedPreparedView) as info:
        _render(Page())
    assert f"<c-card> in template {template_path.resolve()}, line 3 {expected}" in str(info.value)


def test_duplicate_key_names_tag_template_line_and_value() -> None:
    registry = Citry(autodiscover=False)
    _card(registry)

    class Page(Component):
        citry = registry
        template = """
            <c-for each="item in items">
              <c-card #c-key="item" />
            </c-for>
        """
        js = _VUE_JS

        def template_data(self, kwargs, slots):
            return {"items": ["a", "a"]}

    with pytest.raises(UnsupportedPreparedView) as info:
        _render(Page())
    assert re.search(
        r"<c-card> in template \S+::Page, line 3 has a duplicate #c-key, 'a': "
        r"two of its repetitions got that value\. Each repetition needs its own key",
        str(info.value),
    )


def test_server_only_component_in_vue_page_names_its_own_template() -> None:
    # The list has no browser code, but the page around it does, so its
    # loop still needs keys; the error points at the list's template.
    registry = Citry(autodiscover=False)
    _card(registry)

    class ServerList(Component):
        citry = registry
        template = """
            <ul>
              <c-for each="item in [1, 2]"><c-card /></c-for>
            </ul>
        """

    class Page(Component):
        citry = registry
        template = """
            <main><c-server-list /></main>
        """
        js = _VUE_JS

    with pytest.raises(UnsupportedPreparedView, match=r"<c-card> in template \S+::ServerList, line 3 repeats"):
        _render(Page())


def test_repeated_component_in_slot_fill_names_the_template_that_wrote_it() -> None:
    registry = Citry(autodiscover=False)
    _card(registry)

    class Frame(Component):
        citry = registry
        template = """
            <section><c-slot /></section>
        """

    class Page(Component):
        citry = registry
        template = """
            <c-frame>
              <c-for each="item in [1, 2]">
                <c-card />
              </c-for>
            </c-frame>
        """
        js = _VUE_JS

    with pytest.raises(UnsupportedPreparedView, match=r"<c-card> in template \S+::Page, line 4 repeats"):
        _render(Page())


def test_duplicate_key_across_nested_loops_suggests_combining_values() -> None:
    registry = Citry(autodiscover=False)
    _card(registry)

    class Page(Component):
        citry = registry
        template = """
            <c-for each="group in [1, 2]">
              <div>
                <c-for each="item in [1, 2]"><c-card #c-key="item" /></c-for>
              </div>
            </c-for>
        """
        js = _VUE_JS

    with pytest.raises(UnsupportedPreparedView, match="combine the outer and inner loop values into one key"):
        _render(Page())


def test_keys_combined_across_nested_loops_render() -> None:
    registry = Citry(autodiscover=False)
    _card(registry)

    class Page(Component):
        citry = registry
        template = """
            <c-for each="group in [1, 2]">
              <div>
                <c-for each="item in [1, 2]">
                  <c-card #c-key="f'{group}-{item}'" />
                </c-for>
              </div>
            </c-for>
        """
        js = _VUE_JS

    assert _render(Page()).count("<i>card</i>") == 4


def test_call_in_template_valued_attribute_reports_the_template_line() -> None:
    registry = Citry(autodiscover=False)
    _card(registry)

    class Holder(Component):
        citry = registry
        template = """
            <div>{{ body }}</div>
        """

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

    class Page(Component):
        citry = registry
        template = """
            <main>
              <c-holder
                c-body="<ul>
                  <c-for each='item in [1, 2]'>
                    <c-card />
                  </c-for>
                </ul>"
              />
            </main>
        """
        js = _VUE_JS

    # Line 6 of the template, not line 3 of the attribute value.
    with pytest.raises(UnsupportedPreparedView, match=r"<c-card> in template \S+::Page, line 6 repeats"):
        _render(Page())


def test_repeated_component_with_unique_keys_renders() -> None:
    registry = Citry(autodiscover=False)
    _card(registry)

    class Page(Component):
        citry = registry
        template = """
            <c-for each="item in items"><c-card #c-key="item" /></c-for>
        """
        js = _VUE_JS

        def template_data(self, kwargs, slots):
            return {"items": ["a", "b"]}

    assert _render(Page()).count("<i>card</i>") == 2


def test_element_key_from_python_beside_c_key_names_the_element() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = """
            <c-for each="item in ['a']">
              <div #c-key="item" c-key="'other'">x</div>
            </c-for>
        """
        js = _VUE_JS

    # Columns count in the inline template after its common indent is
    # removed, as the template parser's own errors do.
    with pytest.raises(
        UnsupportedPreparedView,
        match=r"The <div> element that starts at line 3, column 3 of its template has '#c-key' and also gets",
    ):
        _render(Page())


# v-model on an element that holds no value (m63)


def test_model_on_div_names_element_component_template_and_line() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = """
            <main>
              <div v-model="query">x</div>
            </main>
        """
        js = _VUE_JS

    with pytest.raises(ValueError, match="Vue could not compile component Page") as info:
        _render(Page())
    message = str(info.value)
    assert re.search(r"in template \S+::Page, line 3: v-model does not work on <div>, which holds no value", message)
    assert "Put it on an <input>, <textarea>, or <select>, or on a component." in message
    # The compiler's own diagnostics stay attached for debugging.
    assert isinstance(info.value.__cause__, VueCompilerDiagnosticsError)


def test_model_errors_list_every_element_in_a_template_file(tmp_path: Path) -> None:
    registry = Citry(autodiscover=False)
    template_path = tmp_path / "search.html"
    template_path.write_text(
        '<form v-model="query">\n  <input v-model="query">\n</form>\n<my-input v-model="query"></my-input>\n'
    )

    class Page(Component):
        citry = registry
        template_file = str(template_path)
        js = _VUE_JS

    with pytest.raises(ValueError, match="Vue could not compile component Page") as info:
        _render(Page())
    lines = str(info.value).splitlines()[1:]
    # The <input> is a valid target, and a custom element is rejected like
    # the static rule rejects it.
    assert [line.split(": ", 1)[0] for line in lines] == [
        f"  in template {template_path.resolve()}, line 1",
        f"  in template {template_path.resolve()}, line 4",
    ]
    assert "<form>" in lines[0]
    assert "<my-input>" in lines[1]


def test_model_in_transparent_component_names_its_template() -> None:
    registry = Citry(autodiscover=False)

    class Field(Component):
        citry = registry
        transparent = True
        template = """
            <label>
              <span v-model="query">x</span>
            </label>
        """

    class Page(Component):
        citry = registry
        template = """
            <main><c-field /></main>
        """
        js = _VUE_JS

    with pytest.raises(ValueError, match=r"in template \S+::Field, line 3: v-model does not work on <span>"):
        _render(Page())


def test_model_in_simple_child_names_the_child_template() -> None:
    # A simple=True component writes its HTML into its caller's template,
    # so its v-model fails in the caller's compile.
    registry = Citry(autodiscover=False)

    class Inner(Component):
        citry = registry
        simple = True
        template = """
            <div v-model="query">x</div>
        """

    class Page(Component):
        citry = registry
        template = """
            <main><c-inner /></main>
        """
        js = _VUE_JS

    with pytest.raises(ValueError, match=r"in template \S+::Inner, line 2: v-model does not work on <div>"):
        _render(Page())


def test_model_error_keeps_compiler_text_when_no_element_is_found() -> None:
    # The search skips component tags, which decide for themselves what
    # v-model binds, so a tag Vue cannot resolve is not named.
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = """
            <main><MyInput v-model="query" /></main>
        """
        js = _VUE_JS

    with pytest.raises(ValueError, match=r"^Vue could not compile component Page \(template \S+::Page\): ") as info:
        _render(Page())
    assert "Put v-model on an <input>, <textarea>, or <select>, or on a Citry component tag" in str(info.value)
    cause = info.value.__cause__
    assert isinstance(cause, VueCompilerDiagnosticsError)
    assert cause.codes() == {"MODEL_HELPER_MISMATCH"}
    # The compiler's own text stays at the end of the message.
    assert str(info.value).endswith(str(cause))


def test_model_error_passes_on_other_compiler_errors() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = """
            <main>
              <div v-model="query">x</div>
              <p v-if="query &&">y</p>
            </main>
        """
        js = _VUE_JS

    with pytest.raises(ValueError, match="Check each v-model below") as info:
        _render(Page())
    assert "\nVue also reported InvalidExpression: " in str(info.value)


def test_model_error_in_render_template_names_the_template() -> None:
    # render_template() renders through a private class, which the
    # message does not name.
    registry = Citry(autodiscover=False)

    with pytest.raises(ValueError, match=r"^Vue could not compile the template given to render_template\(\)"):
        str(registry.render_template('<p v-model="query">x</p>'))


@pytest.mark.parametrize(
    "element",
    [
        '<input v-model="query">',
        '<textarea v-model="query"></textarea>',
        '<select v-model="query"><option>a</option></select>',
        '<c-field v-model="query" />',
    ],
)
def test_model_on_value_elements_and_components_renders(element: str) -> None:
    registry = Citry(autodiscover=False)

    class Field(Component):
        citry = registry
        template = """
            <input>
        """
        js = """
            export default { props: ["modelValue"] }
        """

    class Page(Component):
        citry = registry
        template = f"""
            <main>{element}</main>
        """
        js = _VUE_JS

    assert "<main" in _render(Page())
