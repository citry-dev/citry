"""
A component call works inside the HTML elements that accept only a few kinds of children.

In a component that uses Vue, Citry writes each component call into the Vue
template as a tag of its own, such as ``<citry-row-1a2b>``. HTML lets a table
section hold only rows, a row only cells, and so on, and Vue's compiler
reads the template with those rules. The tag Citry writes never reaches the
browser, because Vue renders the child's own HTML in its place, so the
compiler must keep it where the template put it. Each test renders through
Vue and checks the HTML the server writes for the browser to adopt.
"""

from __future__ import annotations

import re

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission


def _host(html: str) -> str:
    """Return the Vue host's contents as the server wrote them for hydration."""
    match = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert match is not None, html[:500]
    return match.group(1)


def _page(page_template: str, row_template: str) -> type[Component]:
    registry = Citry(autodiscover=False)

    # The child uses Vue too, so the parent's Vue template holds a call to it.
    class Row(Component):
        citry = registry
        template = row_template
        js = """
            $component({});
        """

    class Page(Component):
        citry = registry
        template = page_template
        js = """
            $component({ data() { return { open: true }; } });
        """

        def template_data(self, kwargs, slots):
            return {"names": ["ada", "bo"]}

    return Page


@pytest.mark.parametrize(
    ("page_template", "row_template", "host"),
    [
        pytest.param(
            "<table><tbody><c-row /></tbody></table>",
            "<tr><td>Ada</td></tr>",
            "<table><tbody><tr><td>Ada</td></tr></tbody></table>",
            id="tbody",
        ),
        pytest.param(
            "<table><thead><c-row /></thead></table>",
            "<tr><th>Name</th></tr>",
            "<table><thead><tr><th>Name</th></tr></thead></table>",
            id="thead",
        ),
        pytest.param(
            "<table><tfoot><c-row /></tfoot></table>",
            "<tr><td>Total</td></tr>",
            "<table><tfoot><tr><td>Total</td></tr></tfoot></table>",
            id="tfoot",
        ),
        pytest.param(
            "<table><tbody><tr><c-row /></tr></tbody></table>",
            "<td>Ada</td>",
            "<table><tbody><tr><td>Ada</td></tr></tbody></table>",
            id="tr",
        ),
        pytest.param(
            '<table><tbody><c-for each="name in names"><c-row #c-key="name" /></c-for></tbody></table>',
            "<tr><td>Ada</td></tr>",
            "<table><tbody><!--[--><tr><td>Ada</td></tr><tr><td>Ada</td></tr><!--]--></tbody></table>",
            id="tbody-loop",
        ),
        pytest.param(
            '<table><tbody><c-if cond="names"><c-row /></c-if></tbody></table>',
            "<tr><td>Ada</td></tr>",
            "<table><tbody><tr><td>Ada</td></tr></tbody></table>",
            id="tbody-c-if",
        ),
        pytest.param(
            '<table><tbody><c-row v-if="open" /></tbody></table>',
            "<tr><td>Ada</td></tr>",
            # A browser-side `v-if` leaves the row for Vue to build.
            '<table><tbody data-allow-mismatch="children"><tr><td>Ada</td></tr></tbody></table>',
            id="tbody-v-if",
        ),
        pytest.param(
            '<table><tbody><c-row><c-fill name="cell">Ada</c-fill></c-row></tbody></table>',
            '<tr><td><c-slot name="cell" /></td></tr>',
            "<table><tbody><tr><td><!--[-->Ada<!--]--></td></tr></tbody></table>",
            id="tbody-fill",
        ),
        pytest.param("<ul><c-row /></ul>", "<li>Ada</li>", "<ul><li>Ada</li></ul>", id="ul"),
        pytest.param(
            "<select><c-row /></select>",
            "<option>Ada</option>",
            "<select><option>Ada</option></select>",
            id="select",
        ),
        pytest.param("<dl><c-row /></dl>", "<dt>Ada</dt>", "<dl><dt>Ada</dt></dl>", id="dl"),
        pytest.param(
            "<table><colgroup><c-row /></colgroup></table>",
            "<col>",
            "<table><colgroup><col></colgroup></table>",
            id="colgroup",
        ),
    ],
)
def test_call_renders_inside_a_restricted_parent(page_template: str, row_template: str, host: str) -> None:
    rendered = _page(page_template, row_template)().render()
    document = rendered.serialize()

    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.hydrated
    assert _host(document) == host


@pytest.mark.parametrize(
    ("page_template", "row_template", "shell_tag", "decline"),
    [
        # A row written straight into a <table> gets a <tbody> from the
        # browser, so Vue builds the table's contents in the browser instead.
        pytest.param("<table><c-row /></table>", "<tr><td>Ada</td></tr>", "table", "parser-repair", id="table"),
    ],
)
def test_call_whose_html_the_browser_would_rearrange_leaves_its_parent_to_vue(
    page_template: str, row_template: str, shell_tag: str, decline: str
) -> None:
    rendered = _page(page_template, row_template)().render()
    document = rendered.serialize()

    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.hydrated
    assert [(item.code, item.outcome, item.shell_tag) for item in admission.declines] == [
        (decline, "shell", shell_tag)
    ]
    assert f'<{shell_tag} data-allow-mismatch="children">' in _host(document)


@pytest.mark.parametrize("element", ["<div>Ada</div>", "<my-row>Ada</my-row>"])
def test_an_element_the_author_puts_directly_in_a_table_still_fails(element: str) -> None:
    # Only the tags Citry writes for component calls stay put. An element the
    # author writes reaches the browser, which would move it out of the table.
    page = _page(f"<table><tbody>{element}<c-row /></tbody></table>", "<tr><td>Bo</td></tr>")

    with pytest.raises(ValueError, match="Foster parenting moved this element"):
        page().render().serialize()
