from __future__ import annotations

import re

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui.components._context import FORM_CONTEXT_KEY


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

    return str(Page())


def test_standalone_toggle_uses_native_pressed_button():
    html = _render('<c-CToggle c-pressed="True">Pin</c-CToggle>')
    root = re.search(r'<button[^>]+data-citry-ui-part="toggle"[^>]*>', html)
    assert root is not None
    assert 'type="button"' in root.group(0)
    assert 'aria-pressed="true"' in root.group(0)
    assert "data-pressed" in root.group(0)


def test_group_provides_initial_single_selection_and_name():
    html = _render(
        '<c-CToggleGroup label="View" value="sky">'
        '<c-CToggle value="sky">Sky</c-CToggle>'
        '<c-CToggle value="map">Map</c-CToggle>'
        "</c-CToggleGroup>"
    )
    assert 'role="group"' in html
    assert 'aria-label="View"' in html
    assert html.count('aria-pressed="true"') == 1
    assert html.count('aria-pressed="false"') == 1


def test_enclosing_form_disabled_context_dominates_local_toggle_configuration():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class DisabledFormContext(Component):
        citry = app
        template = "<c-slot />"

        def template_data(self, kwargs, slots):
            self.provide(
                FORM_CONTEXT_KEY,
                form_id="disabled-form",
                disabled=True,
                readonly=False,
            )
            return {}

    app.register(DisabledFormContext)

    class Page(Component):
        citry = app
        template = """
          <c-DisabledFormContext>
            <c-CToggle>Pin</c-CToggle>
            <c-CToggleGroup label="View">
              <c-CToggle value="sky">Sky</c-CToggle>
            </c-CToggleGroup>
          </c-DisabledFormContext>
        """

    html = str(Page())
    buttons = re.findall(r"<button[^>]+>", html)
    assert len(buttons) == 2
    assert all(" disabled" in button for button in buttons)
    assert html.count("data-disabled") >= 3


def test_multiple_values_and_group_fallback_presentation():
    html = _render(
        '<c-CToggleGroup label="Layers" c-value="[\'stars\', \'grid\']" c-multiple="True" variant="soft" size="lg">'
        '<c-CToggle value="stars">Stars</c-CToggle>'
        '<c-CToggle value="grid">Grid</c-CToggle>'
        "</c-CToggleGroup>"
    )
    assert html.count('aria-pressed="true"') == 2
    assert html.count('data-variant="soft"') >= 3
    assert html.count('data-size="lg"') >= 3


@pytest.mark.parametrize(
    "source",
    [
        '<c-CToggleGroup label="View" value="missing"><c-CToggle value="sky">Sky</c-CToggle></c-CToggleGroup>',
        '<c-CToggleGroup label="View"><c-CToggle value="sky">Sky</c-CToggle>'
        '<c-CToggle value="sky">Again</c-CToggle></c-CToggleGroup>',
        '<c-CToggleGroup label="View" c-mandatory="True"><c-CToggle value="sky">Sky</c-CToggle></c-CToggleGroup>',
        '<c-CToggleGroup label="View"><c-CToggle>Sky</c-CToggle></c-CToggleGroup>',
        '<c-CToggleGroup label="View"><c-CToggle value="sky" variant="plain">Sky</c-CToggle></c-CToggleGroup>',
    ],
)
def test_invalid_group_contracts_fail(source):
    with pytest.raises(ValueError, match="CToggle"):
        _render(source)


@pytest.mark.parametrize(
    "attribute",
    ["role", "aria-label", "aria-pressed", "type", "tabindex", "x-if", "data-citry-morph"],
)
def test_toggle_owned_attributes_fail(attribute):
    source = '<c-CToggle c-attrs="attrs">Pin</c-CToggle>'
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return {"attrs": {attribute: "bad"}}

    with pytest.raises(ValueError, match="cannot"):
        str(Page())
