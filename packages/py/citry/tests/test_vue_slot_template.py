"""Vue slot syntax (`<template #name>`, `v-slot`) inside a Citry component tag fails when the template loads."""

from __future__ import annotations

import re
from typing import Any

import pytest

from citry import Citry, Component


def _page(page_template: str, *, page_options: dict[str, Any] | None = None) -> type[Component]:
    registry = Citry(autodiscover=False)

    class Card(Component):
        citry = registry
        template = """
            <section><h2><c-slot name="title">default title</c-slot></h2><c-slot /></section>
        """

    class Outer(Component):
        citry = registry
        template = """
            <article><c-slot name="body" /></article>
        """

    # Each page kind loads the template on a different render path, so the
    # same rejection is checked on all of them.
    body: dict[str, Any] = {"citry": registry, "template": page_template, **(page_options or {})}
    return type("Page", (Component,), body)


# Without Vue, with Vue, and the two instance-free `simple` modes.
_PAGE_KINDS = {
    "html": {},
    "vue": {"js": "$component({});"},
    "simple": {"simple": True},
    "simple-vue": {"simple": "vue"},
}
# `simple="vue"` refuses a page that passes content to a child, so the
# rendering checks below leave it out.
_RENDERING_PAGE_KINDS = ["html", "vue", "simple"]


@pytest.mark.parametrize("page_kind", list(_PAGE_KINDS))
@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            "<c-card><template #title>My title</template></c-card>",
            "Vue slot syntax '<template #title>' does not fill a slot of <c-card>; "
            "use '<c-fill name=\"title\">' instead.",
        ),
        (
            "<c-card><template v-slot:title>My title</template></c-card>",
            "'<template v-slot:title>' does not fill a slot of <c-card>; use '<c-fill name=\"title\">'",
        ),
        (
            "<c-card><template v-slot>Body</template></c-card>",
            "'<template v-slot>' does not fill a slot of <c-card>; use '<c-fill name=\"default\">'",
        ),
        (
            "<c-card><template #default>Body</template></c-card>",
            "'<template #default>' does not fill a slot of <c-card>; use '<c-fill name=\"default\">'",
        ),
        (
            "<c-card><template #[name]>Body</template></c-card>",
            "use '<c-fill c-name=\"...\">' with the slot name as a Python expression instead.",
        ),
        (
            "<c-card><template V-SLOT:title>My title</template></c-card>",
            "'<template V-SLOT:title>' does not fill a slot of <c-card>",
        ),
        (
            '<c-outer><c-fill name="body"><c-card><template #title>T</template></c-card></c-fill></c-outer>',
            "'<template #title>' does not fill a slot of <c-card>",
        ),
        (
            "<c-outer><c-card><template #title>T</template></c-card></c-outer>",
            "'<template #title>' does not fill a slot of <c-card>",
        ),
    ],
)
def test_vue_slot_template_in_component_tag_fails_to_load(page_kind, body, message):
    page = _page(f"<main>{body}</main>", page_options=_PAGE_KINDS[page_kind])

    with pytest.raises(SyntaxError, match=re.escape(message)):
        page().render()


@pytest.mark.parametrize("page_kind", _RENDERING_PAGE_KINDS)
def test_c_fill_and_plain_template_still_render(page_kind):
    page = _page(
        '<main><c-card><c-fill name="title">Fill title</c-fill></c-card>'
        "<c-card><template>plain</template></c-card></main>",
        page_options=_PAGE_KINDS[page_kind],
    )

    html = page().render().serialize(deps_strategy="ignore")

    assert "Fill title" in html
    assert "default title" in html


@pytest.mark.parametrize("page_kind", _RENDERING_PAGE_KINDS)
def test_vue_slot_template_outside_a_citry_component_tag_loads(page_kind):
    # `<c-element>` renders a plain element, a non-`c-` tag may be a Vue
    # component from a plugin, and a fill's root content can end up inside one.
    page = _page(
        '<main><c-element is="section"><template #header>H</template></c-element>'
        "<div><template #title>T</template></div>"
        '<c-outer><c-fill name="body"><template #title>F</template></c-fill></c-outer></main>',
        page_options=_PAGE_KINDS[page_kind],
    )

    page().render().serialize(deps_strategy="ignore")
