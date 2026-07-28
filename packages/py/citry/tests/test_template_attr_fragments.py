"""Regression tests for ``<>...</>`` inside template-valued attributes."""

import re

from citry import Citry, Component

_CID_RE = re.compile(r' data-cid-\w+=""')


def _without_component_markers(html: str) -> str:
    return _CID_RE.sub("", html)


def test_fragment_template_attr_renders_text_and_expression() -> None:
    c = Citry()

    class Card(Component):
        citry = c
        template = """
<section>{{ body }}</section>
""".strip()

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

    class Page(Component):
        citry = c
        template = """
<main><c-card c-body="<>hello {{ n }}</>" /></main>
""".strip()

        def template_data(self, kwargs, slots):
            return {"n": 3}

    assert _without_component_markers(Page().render().serialize()) == ("<main><section>hello 3</section></main>")


def test_fragment_template_attr_renders_nested_component_among_multiple_roots() -> None:
    c = Citry()

    class Inner(Component):
        citry = c
        template = """
<em>{{ label }}</em>
""".strip()

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Card(Component):
        citry = c
        template = """
<section>{{ body }}</section>
""".strip()

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

    class Page(Component):
        citry = c
        template = """
<main><c-card c-body="<>before <c-inner c-label='n' /> after {{ n }}</>" /></main>
""".strip()

        def template_data(self, kwargs, slots):
            return {"n": "value"}

    assert _without_component_markers(Page().render().serialize()) == (
        "<main><section>before <em>value</em> after value</section></main>"
    )


def test_empty_fragment_template_attr_renders_empty_content() -> None:
    c = Citry()

    class Card(Component):
        citry = c
        template = """
<section>{{ body }}</section>
""".strip()

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

    class Page(Component):
        citry = c
        template = """
<main><c-card c-body="<></>" /></main>
""".strip()

    assert _without_component_markers(Page().render().serialize()) == "<main><section></section></main>"
