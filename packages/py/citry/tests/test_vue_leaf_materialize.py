import xml.etree.ElementTree as ET

import pytest

from citry import Citry, Component
from citry._vue.capture import PreparedElementClose, PreparedElementOpen, PreparedStaticRun
from citry._vue.leaf_program import PreparedLeafProgram, typed_leaf_parts


def _leaf_html(component) -> str:
    rendered = component.render()
    assert isinstance(rendered.parts[0], PreparedLeafProgram)
    return rendered.serialize(deps_strategy="ignore")


def test_leaf_materializes_self_closing_svg_elements_as_siblings() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Icon(Component):
        citry = app
        template = '<svg><path c-fill="color"/><circle c-r="radius"/></svg>'

        def template_data(self, kwargs, slots):
            return {"color": "red", "radius": 2}

    html = _leaf_html(Icon())
    root = ET.fromstring(html)  # noqa: S314 -- parses only fixed test output
    rendered = Icon().render()
    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    element_parts = [
        ("open" if isinstance(part, PreparedElementOpen) else "close", part.tag)
        for part in typed_leaf_parts(program)
        if isinstance(part, (PreparedElementOpen, PreparedElementClose))
    ]

    assert '<path fill="red"></path><circle r="2"></circle>' in html
    assert [child.tag for child in root] == ["path", "circle"]
    assert element_parts == [("open", "path"), ("close", "path"), ("open", "circle"), ("close", "circle")]


def test_leaf_materializes_nonvoid_html_self_close_before_next_sibling() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Content(Component):
        citry = app
        template = '<section><div c-title="title"/><span c-title="title"/></section>'

        def template_data(self, kwargs, slots):
            return {"title": "value"}

    html = _leaf_html(Content())
    root = ET.fromstring(html)  # noqa: S314 -- parses only fixed test output

    assert '</div><span title="value"></span>' in html
    assert [child.tag for child in root] == ["div", "span"]


def test_leaf_materializes_html_siblings_inside_svg_foreign_object() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Mixed(Component):
        citry = app
        template = '<svg><foreignObject><div c-title="title"/><p c-title="title"/></foreignObject></svg>'

        def template_data(self, kwargs, slots):
            return {"title": "value"}

    html = _leaf_html(Mixed())
    root = ET.fromstring(html)  # noqa: S314 -- parses only fixed test output
    foreign = root.find("foreignObject")

    assert foreign is not None
    assert [child.tag for child in foreign] == ["div", "p"]
    assert '</div><p title="value"></p>' in html


def test_leaf_preserves_self_closing_html_void_elements() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Voids(Component):
        citry = app
        template = '<main><br c-class="style"/><img c-alt="label"/></main>'

        def template_data(self, kwargs, slots):
            return {"style": "break", "label": "image"}

    html = _leaf_html(Voids())

    assert '<br class="break"/><img alt="image"/>' in html
    assert "</br>" not in html
    assert "</img>" not in html


@pytest.mark.parametrize(
    ("template_source", "expected_openings", "expected_transitions"),
    [
        (
            '<main><div id="empty"/><span id="next"/></main>',
            (("main", 0), ("div", 1), ("span", 1)),
            (
                ("open", "main"),
                ("open", "div"),
                ("close", "div"),
                ("open", "span"),
                ("close", "span"),
                ("close", "main"),
            ),
        ),
        (
            '<main><x-box id="empty"/><span id="next"/></main>',
            (("main", 0), ("x-box", 1), ("span", 1)),
            (
                ("open", "main"),
                ("open", "x-box"),
                ("close", "x-box"),
                ("open", "span"),
                ("close", "span"),
                ("close", "main"),
            ),
        ),
        (
            '<svg><path id="empty"/><circle id="next"/></svg>',
            (("svg", 0), ("path", 1), ("circle", 1)),
            (
                ("open", "svg"),
                ("open", "path"),
                ("close", "path"),
                ("open", "circle"),
                ("close", "circle"),
                ("close", "svg"),
            ),
        ),
        (
            '<svg><foreignObject><div id="empty"/><p id="next"/></foreignObject></svg>',
            (("svg", 0), ("foreignObject", 1), ("div", 2), ("p", 2)),
            (
                ("open", "svg"),
                ("open", "foreignobject"),
                ("open", "div"),
                ("close", "div"),
                ("open", "p"),
                ("close", "p"),
                ("close", "foreignobject"),
                ("close", "svg"),
            ),
        ),
    ],
    ids=("html", "custom-element", "svg", "foreign-object"),
)
def test_static_coalescer_tracks_explicit_self_closing_boundaries(
    template_source: str,
    expected_openings: tuple[tuple[str, int], ...],
    expected_transitions: tuple[tuple[str, str], ...],
) -> None:
    app = Citry(autodiscover=False, extensions=[])

    class StaticMarkup(Component):
        citry = app
        template = template_source

    rendered = StaticMarkup().render()
    assert len(rendered.parts) == 1
    run = rendered.parts[0]
    assert isinstance(run, PreparedStaticRun)
    structure = run.root_structure
    assert structure is not None

    openings = tuple(
        (run.html[item.start_at : item.end_at], item.relative_depth, item.insert_at, item.end_at)
        for item in structure.openings
    )
    assert structure.final_depth_delta == 0
    assert structure.tag_transitions == expected_transitions
    assert len(openings) == len(expected_openings)
    for (tag, depth), (opening, actual_depth, insert_at, end_at) in zip(expected_openings, openings, strict=True):
        assert opening.startswith(f"<{tag}")
        assert opening.endswith(">")
        assert not opening.endswith("/>")
        assert actual_depth == depth
        assert insert_at == end_at - 1
        assert run.html[insert_at] == ">"
