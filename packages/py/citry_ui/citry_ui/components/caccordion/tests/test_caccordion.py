from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from dataclasses import fields
from typing import get_type_hints

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import (
    CAccordion,
    CAccordionHeadingLevel,
    CAccordionIndicatorPos,
    CAccordionItem,
    CAccordionSize,
    CAccordionVariant,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    return app


def _render_template(template: str, data: dict[str, object] | None = None) -> str:
    app = _app()

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return data or {}

    Page.template = template
    return Page().render().serialize(deps_strategy="ignore")


def _basic_template(root_inputs: str = "", first_inputs: str = "") -> str:
    return f"""
      <c-CAccordion {root_inputs}>
        <c-CAccordionItem value="canopy" {first_inputs}>
          <c-fill name="title">Canopy</c-fill>
          <c-fill name="default">High leaves</c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="floor">
          <c-fill name="title">Forest floor</c-fill>
          <c-fill name="default">Ferns</c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """


def test_accordion_schema_is_exact_and_runtime_introspectable():
    assert [field.name for field in fields(CAccordion.Kwargs)] == [
        "value",
        "multiple",
        "collapsible",
        "disabled",
        "loop",
        "variant",
        "size",
        "indicator",
        "indicator_pos",
        "heading_level",
        "region",
        "id",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CAccordionItem.Kwargs)] == [
        "value",
        "disabled",
        "actions_label",
        "class_",
        "style",
        "attrs",
        "heading_attrs",
        "trigger_attrs",
        "panel_attrs",
        "actions_attrs",
    ]
    hints = get_type_hints(CAccordion.Kwargs)
    assert hints["variant"] == CAccordionVariant
    assert hints["size"] == CAccordionSize
    assert hints["indicator_pos"] == CAccordionIndicatorPos
    assert hints["heading_level"] == CAccordionHeadingLevel


def test_accordion_renders_native_anatomy_and_conditional_region_pair():
    html = _render_template(_basic_template('value="canopy" heading_level="2" region'))

    assert html.count('data-citry-ui-part="accordion-item"') == 2
    assert html.count('data-citry-ui-part="accordion-heading"') == 2
    assert html.count('data-citry-ui-part="accordion-trigger"') == 2
    assert html.count('data-citry-ui-part="accordion-panel"') == 2
    assert "<h2" in html
    assert 'type="button"' in html
    assert 'aria-expanded="true"' in html
    assert 'role="region"' in html
    assert 'aria-labelledby="' in html
    assert re.search(r'<div class="cui-accordion__panel"[^>]+ hidden inert', html)

    neutral = _render_template(_basic_template('value="canopy"'))
    assert 'role="region"' not in neutral
    assert "aria-labelledby=" not in neutral


def test_multiple_mode_normalizes_by_item_membership_and_accepts_disabled_open_item():
    html = _render_template(
        _basic_template(
            "multiple c-value=\"['floor', 'canopy']\"",
            "disabled",
        )
    )

    assert html.count('data-state="open"') == 6
    assert 'data-value="canopy" data-state="open" data-disabled' in html


@pytest.mark.parametrize(
    ("root_inputs", "message"),
    [
        ('value="unknown"', "unknown item value"),
        ('multiple c-collapsible="False"', "must remain true"),
        ('variant="loud"', "variant must be one of"),
        ('heading_level="1"', "heading_level must be one of"),
    ],
)
def test_accordion_rejects_invalid_root_configuration(root_inputs: str, message: str):
    with pytest.raises((TypeError, ValueError), match=message):
        _render_template(_basic_template(root_inputs))


def test_accordion_rejects_duplicate_items_and_stray_direct_output():
    duplicate = """
      <c-CAccordion>
        <c-CAccordionItem value="same">
          <c-fill name="title">One</c-fill>
          <c-fill name="default">First</c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="same">
          <c-fill name="title">Two</c-fill>
          <c-fill name="default">Second</c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """
    with pytest.raises(ValueError, match="every item value to be unique"):
        _render_template(duplicate)

    with pytest.raises(ValueError, match="only direct CAccordionItem"):
        _render_template(
            """
              <c-CAccordion>
                <div>Stray</div>
                <c-CAccordionItem value="real">
                  <c-fill name="title">Real</c-fill>
                  <c-fill name="default">Panel</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
            """
        )

    with pytest.raises(ValueError, match="only direct CAccordionItem"):
        _render_template(
            """
              <c-CAccordion>
                <div data-citry-accordion-item>
                  <c-CAccordionItem value="real">
                    <c-fill name="title">Real</c-fill>
                    <c-fill name="default">Panel</c-fill>
                  </c-CAccordionItem>
                </div>
              </c-CAccordion>
            """
        )


def test_transparent_component_may_produce_direct_items_without_a_wrapper():
    app = _app()

    class Items(Component):
        citry = app
        transparent = True
        template = """
          <c-CAccordionItem value="canopy">
            <c-fill name="title">Canopy</c-fill>
            <c-fill name="default">High leaves</c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="floor">
            <c-fill name="title">Forest floor</c-fill>
            <c-fill name="default">Ferns</c-fill>
          </c-CAccordionItem>
        """

    class Page(Component):
        citry = app
        template = """
          <c-CAccordion>
            <c-items />
          </c-CAccordion>
        """

    html = Page().render().serialize(deps_strategy="ignore")

    assert html.count('data-citry-ui-part="accordion-item"') == 2


class _OneShotValueSequence(Sequence[str]):
    def __init__(self, values: tuple[str, ...]) -> None:
        self.values = values
        self.iterations = 0

    def __getitem__(self, index: int) -> str:
        return self.values[index]

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[str]:
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("Accordion value was read more than once")
        return iter(self.values)


def test_server_value_is_snapshotted_once_for_html_and_browser_data():
    value = _OneShotValueSequence(("canopy",))

    html = _render_template(
        _basic_template('multiple c-value="value"'),
        {"value": value},
    )

    assert value.iterations == 1
    assert 'data-value="canopy" data-state="open"' in html


def test_item_is_direct_only_and_nested_accordion_is_panel_only():
    with pytest.raises(ValueError, match="direct child"):
        _render_template(
            """
              <c-CAccordionItem value="orphan">
                <c-fill name="title">Orphan</c-fill>
                <c-fill name="default">No owner</c-fill>
              </c-CAccordionItem>
            """
        )

    with pytest.raises(ValueError, match="only inside a CAccordionItem panel"):
        _render_template(
            """
              <c-CAccordion>
                <c-CAccordionItem value="outer">
                  <c-fill name="title">
                    Outer
                    <c-CAccordion>
                      <c-CAccordionItem value="wrong">
                        <c-fill name="title">Wrong</c-fill>
                        <c-fill name="default">Wrong place</c-fill>
                      </c-CAccordionItem>
                    </c-CAccordion>
                  </c-fill>
                  <c-fill name="default">Panel</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
            """
        )

    html = _render_template(
        """
          <c-CAccordion>
            <c-CAccordionItem value="outer">
              <c-fill name="title">Outer</c-fill>
              <c-fill name="default">
                <c-CAccordion>
                  <c-CAccordionItem value="inner">
                    <c-fill name="title">Inner</c-fill>
                    <c-fill name="default">Nested panel</c-fill>
                  </c-CAccordionItem>
                </c-CAccordion>
              </c-fill>
            </c-CAccordionItem>
          </c-CAccordion>
        """
    )
    assert html.count('data-citry-ui-part="accordion"') == 2


@pytest.mark.parametrize(
    ("destination", "attribute"),
    [
        ("attrs", "aria-label"),
        ("attrs", "popover"),
        ("heading_attrs", "x-show"),
        ("trigger_attrs", "popovertarget"),
        ("trigger_attrs", ":commandfor"),
        ("panel_attrs", "popover"),
        ("panel_attrs", "x-show.immediate"),
        ("panel_attrs", "aria-label"),
        ("panel_attrs", ":aria-roledescription"),
        ("actions_attrs", "aria-live"),
        ("actions_attrs", "aria-roledescription"),
    ],
)
def test_owned_attribute_and_directive_aliases_are_rejected(
    destination: str,
    attribute: str,
):
    with pytest.raises(ValueError, match="cannot"):
        _render_template(
            _basic_template(first_inputs=f'c-{destination}="mapping"'),
            {"mapping": {attribute: "x"}},
        )


def test_attributes_are_copied_and_hostile_identity_strings_are_detrusted():
    attrs = {"data-owner": "reader"}
    html = _render_template(
        _basic_template(
            'id="field-guide" class_="guide" style="color: green"',
            'c-attrs="attrs"',
        ),
        {"attrs": attrs},
    )
    attrs["data-citry-ui-part"] = "stolen"

    assert 'id="field-guide"' in html
    assert 'class="cui-accordion guide"' in html
    assert 'style="color: green;"' in html
    assert 'data-owner="reader"' in html
    assert 'data-citry-ui-part="accordion-item"' in html

    hostile = Markup('canopy" autofocus="true')
    html = _render_template(
        _basic_template().replace('value="canopy"', 'c-value="hostile"', 1),
        {"hostile": hostile},
    )
    assert 'data-value="canopy&#34; autofocus=&#34;true"' in html


def test_actions_are_outside_heading_and_group_label_is_atomic():
    html = _render_template(
        """
          <c-CAccordion>
            <c-CAccordionItem value="canopy" actions_label="Canopy actions">
              <c-fill name="title">Canopy</c-fill>
              <c-fill name="actions"><button type="button">Bookmark</button></c-fill>
              <c-fill name="default">Panel</c-fill>
            </c-CAccordionItem>
          </c-CAccordion>
        """
    )
    heading_end = html.index("</h3>")
    actions_start = html.index('data-citry-ui-part="accordion-actions"')
    assert actions_start > heading_end
    assert 'role="group"' in html
    assert 'aria-label="Canopy actions"' in html
