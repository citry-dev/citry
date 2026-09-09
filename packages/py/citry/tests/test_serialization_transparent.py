"""Transparent instance caps belong to a whole output, not each interior fragment."""

import json
import re
from collections import Counter

import pytest

from citry import Citry, Component
from citry.slots import Slot


@pytest.mark.parametrize(
    "source",
    [
        '<c-for each="value in [1, 2]"><c-widget /></c-for>',
        '<div c-for="value in [1, 2]"><c-widget /></div>',
        '<c-for each="outer in [1]"><c-for each="inner in [1, 2]"><c-widget /></c-for></c-for>',
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
            $component(({ els }) => { els[0].setAttribute('data-ready', 'true'); });
        """

    def content(ctx):
        return app.render_template(source, provides=ctx.provides)

    rendered = app.render_template('<main><c-slot name="content" /></main>', slots={"content": Slot(content)})
    html = rendered.serialize()
    caps = Counter(re.findall(r"<!--(citry:g1:[^>]+)-->", html))
    assert caps
    assert set(caps.values()) == {1}
    manifest = json.loads(re.search(r'<script type="application/json" data-citry-graph>(.*?)</script>', html).group(1))
    for graph in manifest["graphs"]:
        for instance in graph["componentInstances"]:
            for side in ("s", "e"):
                suffix = f":{graph['graphId']}:i:{instance['instanceId']}:{side}"
                assert sum(count for cap, count in caps.items() if cap.endswith(suffix)) == 1
    assert html.count('data-citry-root=""') == 2
    assert html.count('data-cid="') == 2


def test_nested_transparent_provide_preserves_child_markers_and_values():
    app = Citry()
    app.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = app
        template = """
            <button>{{ value }}</button>
        """
        js = """
            $component(({ els }) => { els[0].setAttribute('data-ready', 'true'); });
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
                    '<c-for each="value in [1, 2]"><c-widget /></c-for>', provides=ctx.provides
                )
            )
        }
    ).render()
    html = rendered.serialize()
    caps = Counter(re.findall(r"<!--(citry:g1:[^>]+)-->", html))
    assert set(caps.values()) == {1}
    assert html.count("violet</button>") == 2
    assert html.count('data-cid-c1=""') == 2
    assert html.count('data-citry-root=""') == 2


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
            <button x-text="label"></button>
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
    caps = Counter(re.findall(r"<!--(citry:g1:[^>]+)-->", html))
    assert caps
    assert set(caps.values()) == {1}
    assert "Preview</h1>" in html
    assert html.count('data-citry-root=""') == 1
