"""Transparent instance caps belong to a whole output, not each interior fragment."""

import re

import pytest

from citry import Citry, Component
from citry._vue.serialization import vue_serialization_requirements
from citry.slots import Slot


def test_server_resolved_dynamic_element_does_not_require_vue_by_itself():
    app = Citry()

    class Page(Component):
        citry = app
        template = '<c-element c-is="tag">plain</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "section"}

    rendered = Page().render()
    assert vue_serialization_requirements(rendered) == frozenset()
    html = rendered.serialize()
    assert html.startswith("<section ")
    assert html.endswith(">plain</section>")
    assert 'id="citry-vue-' not in html


def test_dynamic_element_remains_in_prepared_view_when_parent_is_interactive():
    app = Citry()
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = '<c-element c-is="tag">{{ label }}</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "section", "label": "ready"}

        def js_data(self, kwargs, slots):
            return {"active": True}

    rendered = Page().render()
    assert vue_serialization_requirements(rendered) == frozenset({"js_data"})
    html = rendered.serialize()
    assert 'id="citry-vue-' in html
    assert '"tag":"section"' in html


@pytest.mark.parametrize(
    "source",
    [
        "<c-for each=\"value in ['one', 'two']\"><c-widget #c-key=\"value\" /></c-for>",
        "<div c-for=\"value in ['one', 'two']\"><c-widget #c-key=\"value\" /></div>",
        (
            "<c-for each=\"outer in ['group']\"><c-for each=\"inner in ['one', 'two']\"><c-widget"
            ' #c-key="inner" /></c-for></c-for>'
        ),
    ],
)
def test_nested_template_loop_emits_one_cap_pair_per_instance(source):
    app = Citry()
    app.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = app
        template = """
            <button>ready</button>
        """
        js = """
            $component(({ component }) => { component.$el.setAttribute('data-ready', 'true'); });
        """

    def content(ctx):
        return app.render_template(source, provides=ctx.provides)

    rendered = app.render_template('<main><c-slot name="content" /></main>', slots={"content": Slot(content)})
    html = rendered.serialize()
    assert html.count('id="citry-vue-') == 1
    assert len(set(re.findall(r"citryOccurrence[0-9a-f]{24}", html))) == 3
    assert "data-citry-graph" not in html


def test_nested_transparent_provide_preserves_child_markers_and_values():
    app = Citry()
    app.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = app
        template = """
            <button>{{ value }}</button>
        """
        js = """
            $component(({ component }) => { component.$el.setAttribute('data-ready', 'true'); });
        """

        def template_data(self, kwargs, slots):
            return {"value": self.inject("theme").value}

    class Parent(Component):
        citry = app
        template = """
            <c-provide key="theme" value="violet"><c-slot name="content" /></c-provide>
        """

    rendered = Parent(
        slots={
            "content": Slot(
                lambda ctx: app.render_template(
                    "<c-for each=\"value in ['one', 'two']\"><c-widget #c-key=\"value\" /></c-for>",
                    provides=ctx.provides,
                )
            )
        }
    ).render()
    html = rendered.serialize()
    assert html.count('id="citry-vue-') == 1
    assert len(set(re.findall(r"citryOccurrence[0-9a-f]{24}", html))) == 3
    assert html.count("violet") == 2


def test_transparent_lexical_fill_owner_keeps_one_boundary_across_child_frame():
    app = Citry()
    app.set_mounted_prefix("/citry")

    class Shell(Component):
        citry = app
        template = """
            <main><c-slot name="header" /><c-slot /></main>
        """

    class Widget(Component):
        citry = app
        template = """
            <button v-text="label"></button>
        """

        def js_data(self, kwargs, slots):
            return {"label": "ready"}

    content = Slot(lambda ctx: Widget().render(provides=ctx.provides))
    rendered = app.render_template(
        '<c-shell><c-fill name="header"><h1>Preview</h1></c-fill>'
        '<c-fill name="default"><c-slot name="content" /></c-fill></c-shell>',
        slots={"content": content},
    )
    html = rendered.serialize()
    assert html.count('id="citry-vue-') == 1
    assert '"label":"ready"' in html
    assert len(set(re.findall(r"citryOccurrence[0-9a-f]{24}", html))) == 3
