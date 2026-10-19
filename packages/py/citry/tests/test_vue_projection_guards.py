from __future__ import annotations

from citry import Citry, Component
from citry._vue.capture import render_prepared
from citry._vue.direct_capture import assemble_typed_render


def test_multibyte_source_offsets_accept_slot_and_nested_template_sites() -> None:
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = "<article>{{ body }}<c-slot /></article>"

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

    class Page(Component):
        citry = app
        template = 'é🙂<c-Card c-body="<b>nested</b>"><span>supplied</span></c-Card>'

    assembly = assemble_typed_render(
        render_prepared(Page()),
        revision=0,
        tag_for_type=lambda value: f"x-{value.lower().replace('_', '-')}",
    )
    templates = [value.template for value in assembly.compile_inputs.values()]
    assert any("nested" in value for value in templates)
    assert any("supplied" in value for value in templates)
