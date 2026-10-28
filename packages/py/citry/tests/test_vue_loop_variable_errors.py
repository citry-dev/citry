"""Render errors for a server expression that reads a Vue ``v-for`` variable (#240)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component
from citry._vue_loop_errors import VueLoopVariableError

if TYPE_CHECKING:
    from pathlib import Path

# Component JavaScript, so the page also mounts Vue code of its own.
_VUE_JS = """
export default {
  data() {
    return { members: [{ name: "Ada" }] };
  },
};
"""

_LIST = """
    <ul>
      <li v-for="(member, index) in members">{inner}</li>
    </ul>
"""


def _page(
    inner: str,
    *,
    with_js: bool = True,
    template: str = _LIST,
    server_members: bool = True,
) -> type[Component]:
    """Build a page whose template puts ``inner`` inside a Vue v-for over ``members``."""
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
            <i>{{ name }}</i>
        """

        def template_data(self, kwargs, slots):
            return {"name": kwargs.get("name")}

    class Box(Component):
        citry = engine
        template = """
            <b><c-slot /></b>
        """

    class Page(Component):
        citry = engine

        def template_data(self, kwargs, slots):
            # `members` is also a server variable unless a test leaves it
            # out, so the advice can name a `<c-for>` that would work.
            return {"lookup": {}, "flag": True, **({"members": []} if server_members else {})}

    Page.template = template.format(inner=inner)
    if with_js:
        Page.js = _VUE_JS
    return Page


@pytest.mark.parametrize("with_js", [True, False], ids=["with-js", "template-only"])
def test_component_input_reading_the_loop_variable_explains_the_server_loop(with_js):
    page = _page('<c-card c-name="member.name" />', with_js=with_js)

    with pytest.raises(VueLoopVariableError) as exc_info:
        page().render()

    message = str(exc_info.value)
    # The message names the call, the template, and the line, says why the
    # variable is missing, and gives the server-side fix.
    assert "<c-card> in template " in message
    assert "::Page, line 3 reads 'member' in c-name=\"member.name\"" in message
    assert "'member' exists only in the browser: the Vue v-for on <li> (line 3) declares it" in message
    assert 'with <c-for each="member in members"> in place of the v-for' in message
    # It keeps the template snippet, prints its line breaks as written, and
    # stays a KeyError whose cause is the failed lookup.
    assert "In template of 'Page'" in message
    assert '<c-card c-name="member.name" />' in message
    assert not message.startswith("'")
    assert isinstance(exc_info.value, KeyError)
    assert type(exc_info.value.__cause__) is KeyError


def test_server_text_reading_the_loop_variable_suggests_v_text():
    page = _page("Name: {{ member.name }}")

    with pytest.raises(VueLoopVariableError, match=r"\{\{ member\.name \}\} in template \S+::Page, line 3") as info:
        page().render()

    # The suggestion keeps the text around the value.
    assert '<span v-text="member.name"></span> in place of {{ member.name }}' in str(info.value)


def test_server_attribute_reading_the_loop_variable_suggests_its_vue_binding():
    page = _page('<a c-title="member.name">Profile</a>')

    with pytest.raises(VueLoopVariableError, match=r'c-title="member\.name" in template \S+::Page, line 3') as info:
        page().render()

    assert 'with :title="member.name", or repeat on the server' in str(info.value)


def test_a_python_only_expression_is_not_pasted_into_a_vue_binding():
    page = _page('<a c-title="member.name if flag else None">Profile</a>')

    with pytest.raises(VueLoopVariableError) as exc_info:
        page().render()

    # The expression is Python, which Vue cannot run, so the advice names
    # the binding without copying it.
    assert "with a :title binding" in str(exc_info.value)


def test_server_condition_reading_the_loop_variable_names_its_tag_and_shows_the_snippet():
    page = _page('<c-if cond="member.name">Named</c-if>')

    with pytest.raises(VueLoopVariableError, match=r'<c-if cond="member\.name"> in template \S+::Page') as info:
        page().render()

    message = str(info.value)
    assert "Use v-if in the browser instead" in message
    # A <c-if> node has no span of its own; its branch supplies the snippet.
    assert "In template of 'Page'" in message


def test_an_index_variable_gets_the_plain_server_loop_tag():
    page = _page('<c-card c-name="index" />')

    with pytest.raises(VueLoopVariableError) as exc_info:
        page().render()

    assert "with a <c-for> over the same list in place of the v-for" in str(exc_info.value)


def test_a_list_only_the_browser_has_is_named_as_a_template_variable_to_add():
    page = _page('<c-card c-name="member.name" />', server_members=False)

    with pytest.raises(VueLoopVariableError) as exc_info:
        page().render()

    message = str(exc_info.value)
    # `<c-for each="member in members">` would fail on the server too, so the
    # advice says the list must become a template variable first.
    assert 'each="member in members"' not in message
    assert "The <c-for> needs that list as a template variable, for example from template_data()." in message


def test_the_innermost_loop_that_declares_the_name_is_blamed():
    template = """
        <ul>
          <li v-for="item in groups">
            <span v-for="item in item.members"><b c-title="item.name">x</b></span>
          </li>
        </ul>
    """
    page = _page("", template=template)

    with pytest.raises(VueLoopVariableError) as exc_info:
        page().render()

    message = str(exc_info.value)
    assert "the Vue v-for on <span> (line 4) declares it" in message
    # The inner list comes from the outer browser loop, so the server has
    # no list to name.
    assert "a <c-for> over the same list" in message


def test_a_fill_inside_a_component_call_gets_only_the_server_loop_fix():
    page = _page('<c-box><c-fill name="default">{{ member.name }}</c-fill></c-box>')

    with pytest.raises(VueLoopVariableError) as exc_info:
        page().render()

    message = str(exc_info.value)
    # Vue cannot show the value here: the component call around it cannot
    # sit in the v-for either, so only the server loop fixes it.
    assert "v-text" not in message
    assert "Repeat this part on the server with" in message


def test_a_file_template_reports_the_line_in_the_file(tmp_path: Path):
    (tmp_path / "page.html").write_text(
        '<p>é</p>\n<ul>\n  <li v-for="member in members"><c-card c-name="member.name" /></li>\n</ul>\n',
        encoding="utf-8",
    )
    page = _page("")
    page.template = None
    page.template_file = str(tmp_path / "page.html")

    with pytest.raises(VueLoopVariableError) as exc_info:
        page().render()

    assert f"<c-card> in template {tmp_path / 'page.html'}, line 3 reads 'member'" in str(exc_info.value)


@pytest.mark.parametrize(
    "inner",
    [
        # A name no v-for declares is an ordinary missing variable.
        '<c-card c-name="nope" />',
        # A failed lookup inside a value the server has is not about the loop.
        """<c-card c-name="lookup['missing'] + member" />""",
        # The lookup that failed is `nope`, even though `member` is also missing.
        "{{ nope if flag else member }}",
    ],
    ids=["unknown-name", "lookup-in-a-known-value", "other-missing-name"],
)
def test_other_key_errors_inside_the_loop_stay_key_errors(inner):
    page = _page(inner)

    with pytest.raises(KeyError) as exc_info:
        page().render()

    assert type(exc_info.value) is KeyError


@pytest.mark.parametrize(
    "template",
    [
        # Vue does not run a `v-for` on an element with `v-pre`, or one
        # inside it, so no browser loop declares `member`.
        '<ul><li v-for="(member, index) in members" v-pre>{inner}</li></ul>',
        '<ul><li v-pre><span v-for="(member, index) in members">{inner}</span></li></ul>',
    ],
    ids=["v-pre-on-the-loop-element", "loop-inside-v-pre"],
)
def test_a_v_for_at_or_inside_v_pre_is_not_blamed_for_a_missing_variable(template):
    page = _page("{{ member.name }}", template=template)

    with pytest.raises(KeyError) as exc_info:
        page().render()

    # The hint about a browser-only loop variable would send the author to a
    # loop that does not exist.
    assert type(exc_info.value) is KeyError
    assert "exists only in the browser" not in str(exc_info.value)


def test_a_v_pre_sibling_does_not_stop_the_hint_for_a_loop_that_runs():
    page = _page(
        "{{ member.name }}",
        template='<ul><li v-for="(member, index) in members"><div v-pre></div>{inner}</li></ul>',
    )

    with pytest.raises(VueLoopVariableError, match="exists only in the browser"):
        page().render()
