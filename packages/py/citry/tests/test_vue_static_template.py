"""
`citry check` writes the same Vue template a render compiles.

A render builds the Vue template from what it rendered; `citry check` builds
it from the template alone (`citry._vue.static_template`). These tests render
real components and compare the two, once the names of the data keys, slot
sites, and component tags each side picks are made equal.
"""

from __future__ import annotations

import re

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.static_template import UnsupportedStaticTemplate, static_vue_template
from citry.component_render import _exec_template_code
from citry_core.template_parser import parse_template
from citry_core.template_parser.compile import _compile_prepared_template


def _static(source: str, *, renders_in_place=None):
    nodes = _exec_template_code(_compile_prepared_template(parse_template(source)), source, prepared=True)()
    return static_vue_template(source, nodes, renders_in_place=renders_in_place)


def _same_names(template: str) -> str:
    """Replace the names each side picks on its own with fixed ones."""
    template = re.sub(r"\$citryPrepared\.(calls|opaqueHtml)\.\w+", r"$citryPrepared.\1.KEY", template)
    template = re.sub(r"\$citryPrepared\.(?!calls\.|opaqueHtml\.|selectedSlots\[)\w+", "$citryPrepared.KEY", template)
    template = re.sub(r"selectedSlots\['[^']*'\]", "selectedSlots['SITE']", template)
    template = re.sub(r"v-slot:\['[^']*'\]", "v-slot:['SITE']", template)
    template = re.sub(r'(<slot [^>]*?name=")[^"]*"', r'\1SITE"', template)
    # Some render paths mark every property of a form control as Vue's,
    # without reading the input's type; the marker does not change what
    # the compiler accepts.
    return re.sub(r'v-citry-vue-owned="[^"]*"', 'v-citry-vue-owned="PROPERTIES"', template)


def _rendered_template(source: str) -> str:
    """Render a component with `source` as its template and return the Vue template the render compiles."""
    app = Citry(autodiscover=False)

    class Chip(Component):
        citry = app
        template = '<span><c-slot name="default">fallback</c-slot></span>'

    class Page(Component):
        citry = app
        template = source
        js = "$component({ data() { return { q: '', ok: true, n: 0, t: 1 }; } });"

        def template_data(self, _kwargs, _slots):
            return {"title": "T", "cls": "c", "items": [1], "ok": True}

    assembly = assemble_typed_render(
        render_prepared(Page()),
        revision=0,
        # The check's component tag, so the two templates can be compared.
        tag_for_type=lambda key: "citry-check-call" if key.startswith("Chip") else "x-page",
    )
    (occurrence,) = [item for item in assembly.view.occurrences if item.type_key.startswith("Page")]
    return assembly.compile_inputs[occurrence.definition_id].template


@pytest.mark.parametrize(
    "source",
    [
        '<section class="a"  id=\'b\'><h4 :title="t">{{ title }}</h4><span v-if="ok">x</span><span v-else>y</span>'
        "</section>",
        '<div c-class="cls" #c-key="title"><input v-model="q" type="text"><br/><p/></div>',
        '<div><c-chip :p="title" v-if="ok"><c-fill name="default">F {{ title }}</c-fill></c-chip></div>',
        "<div><c-chip>body {{ title }}</c-chip></div>",
        "<div #c-ignore><b>{{ title }}</b></div><c-raw><i>raw</i></c-raw>",
        '<!doctype html><html><head><title>x</title></head><body><main @click="n++">{{ title }}</main></body></html>',
        # A body with no component call is compiled as a leaf program, which
        # wraps each `<c-if>` branch and `<c-for>` body in a `<template>`.
        '<ul><c-for each="i in items"><li>{{ i }}</li></c-for></ul><c-if cond="ok"><em @click="n++">{{ title }}</em>'
        "</c-if>",
        # With a component call, a render writes the branch it picks in place.
        '<c-chip /><c-if cond="ok"><em>{{ title }}</em></c-if>',
        '<div><c-slot name="extra">fallback {{ title }}</c-slot></div><c-chip />',
        '<c-element is="section" class="a">{{ title }}</c-element><c-chip />',
        '<p v-if="ok">x</p><c-chip v-else @close="n++" /><c-chip v-show="ok" :p="title" />',
        '<c-chip><c-fill name="default" data="d">{{ title }}</c-fill></c-chip>',
        '<p v-if="ok">1</p><c-provide key="k" data="1"><p v-else>{{ title }}</p></c-provide><c-chip />',
        # Vue reads a `v-pre` element as written, so its form controls take no
        # ownership marker; the input after it does.
        "<main><div v-pre><input :value='q'></div><input v-pre :value='q'><input :value='q'></main>",
    ],
)
def test_check_writes_the_vue_template_a_render_compiles(source):
    assert _same_names(_static(source).compile_input.template) == _same_names(_rendered_template(source))


def test_check_writes_every_server_branch_and_loop_body_once_where_a_render_writes_them_in_place():
    # A render that is not a leaf program writes the branch it picks and
    # every row. The check writes each branch and the loop body once, so
    # every branch a render may pick is compiled.
    written = _static(
        '<c-chip /><ul><c-for each="i in items"><li>{{ i }}</li></c-for><c-empty><li>none</li></c-empty></ul>'
        '<c-if cond="a"><b>1</b></c-if><c-elif cond="b"><i>2</i></c-elif><c-else>3</c-else>'
    )

    assert _same_names(written.compile_input.template).endswith(
        "<ul><li>{{ $citryPrepared.KEY }}</li><li>none</li></ul><b>1</b><i>2</i>3"
    )


def test_check_wraps_each_branch_and_loop_body_where_a_render_compiles_a_leaf_program():
    written = _static(
        '<ul><c-for each="i in items"><li>{{ i }}</li></c-for><c-empty><li>none</li></c-empty></ul>'
        '<c-if cond="a"><b>1</b></c-if><c-else>2</c-else>'
    )

    assert _same_names(written.compile_input.template) == (
        '<ul><template v-for="$citryPrepared in $citryPrepared.KEY"><li>{{ $citryPrepared.KEY }}</li></template>'
        '<template v-if="$citryPrepared.KEY.length === 0"><li>none</li></template></ul>'
        '<template v-if="$citryPrepared.KEY === 0"><b>1</b></template>'
        '<template v-else-if="$citryPrepared.KEY === 1">2</template>'
    )


def test_check_writes_a_component_that_renders_in_place_as_nothing():
    written = _static('<p v-if="a">1</p><c-chip>x</c-chip>', renders_in_place=lambda _name: True)

    assert written.compile_input.template == '<p v-if="a">1</p>'
    assert written.compile_input.local_calls == ()


def test_check_passes_every_fill_and_renames_one_repeated_in_another_branch():
    written = _static(
        '<c-chip><c-if cond="a"><c-fill name="body">1</c-fill></c-if><c-else><c-fill name="body">2</c-fill>'
        "</c-else></c-chip>"
    )

    assert "v-slot:['body']>1</template><template v-slot:['body-2']>2</template>" in written.compile_input.template


def test_check_records_component_calls_for_the_compiler():
    written = _static('<c-chip v-if="ok" :p="title" @c-close="close">x</c-chip>')

    (call,) = written.compile_input.local_calls
    template = written.compile_input.template.encode()
    assert call["typeKey"] == "chip"
    assert template[call["sourceStart"] : call["sourceEnd"]].startswith(b'<citry-check-call v-if="ok" :p="title" ')
    # The `@c-close` binding belongs to the Events extension, which writes
    # its own listener during a render.
    assert [binding["name"] for binding in call["bindings"]] == ["v-if", ":p"]


def test_authored_range_maps_copied_text_exactly_and_generated_text_to_nothing():
    source = '<p   title="č"  c-class="x">{{ name }} tail</p>'
    written = _static(source)
    template = written.compile_input.template.encode()
    encoded = source.encode()

    attribute = template.index('title="č"'.encode())
    assert written.authored_range(attribute, attribute + len('title="č"'.encode())) == (
        encoded.index(b"title"),
        encoded.index(b"title") + len('title="č"'.encode()),
    )
    tail = template.index(b" tail")
    assert written.authored_range(tail, tail + 5) == (encoded.index(b" tail"), encoded.index(b" tail") + 5)
    # The placeholder for `{{ name }}` and the generated `v-bind` were never
    # written by the author.
    assert written.authored_range(template.index(b"{{"), template.index(b"}}")) is None
    assert written.authored_range(template.index(b"v-bind"), template.index(b"v-bind") + 6) is None
    assert written.generated_source(template.index(b"{{")) == (encoded.index(b"{{"), encoded.index(b" tail"))


def test_check_rejects_a_whole_document_without_a_body():
    with pytest.raises(UnsupportedStaticTemplate, match="body element"):
        _static("<!doctype html><html><head><title>x</title></head></html>")
