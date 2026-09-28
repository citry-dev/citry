from __future__ import annotations

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CComboboxOption


def _render(destination: str, attrs: dict[str, object]) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, _kwargs, _slots):
            return {"attrs": attrs, "options": (CComboboxOption("mars", "Mars"),)}

        template = f'<c-CCombobox c-options="options" c-{destination}="attrs" />'

    return str(Page())


@pytest.mark.parametrize(
    ("destination", "attribute", "message"),
    [
        ("attrs", "data-open", "cannot override owned attribute"),
        ("attrs", ":data-open", "CCombobox attrs cannot contain the Vue directive"),
        ("attrs", "v-if", "Vue directive"),
        ("attrs", "V-IF", "Vue directive"),
        ("attrs", "#default", "Vue directive"),
        ("input_attrs", "role", "cannot override owned attribute"),
        ("input_attrs", "v-bind:aria-expanded", "CCombobox input_attrs cannot contain the Vue directive"),
        ("input_attrs", ".value", "Vue directive"),
        ("input_attrs", "v-model", "Vue directive"),
        ("input_attrs", "@input", "Vue directive"),
    ],
)
def test_attrs_reject_owned_attributes_and_vue_directives(destination: str, attribute: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _render(destination, {attribute: "x"})


def test_attrs_without_vue_syntax_stay_ordinary_attributes() -> None:
    html = _render("attrs", {"x-show": "plain", "data-workflow": "people"})
    # The Combobox root renders in the browser, so its attributes travel in the prepared data.
    assert '"x-show":"plain"' in html
