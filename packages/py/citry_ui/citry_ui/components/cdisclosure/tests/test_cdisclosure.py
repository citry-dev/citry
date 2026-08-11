"""Server contract tests for the Disclosure component family."""

from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cdisclosure import (
    CDisclosure,
    CDisclosureActionsSlotData,
    CDisclosureDefaultSlotData,
    CDisclosureHeadingLevel,
    CDisclosureIndicatorPos,
    CDisclosureOpenChangeDetail,
    CDisclosureSize,
    CDisclosureTitleSlotData,
    CDisclosureVariant,
)
from citry_ui.components.cdisclosure.cdisclosure import (
    CInternalDisclosureActionsContent,
    CInternalDisclosurePanelContent,
    CInternalDisclosureTitleContent,
)

_DISCLOSURE_COMPONENTS = (
    CDisclosure,
    CInternalDisclosureTitleContent,
    CInternalDisclosureActionsContent,
    CInternalDisclosurePanelContent,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-disclosure-tests", _DISCLOSURE_COMPONENTS))
    return app


def _render(
    template: str,
    data: dict[str, object] | None = None,
    *,
    full_library: bool = False,
) -> str:
    app = Citry(autodiscover=False) if full_library else _app()
    if full_library:
        app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return data or {}

    Page.template = template
    return Page().render().serialize(deps_strategy="ignore")


def _disclosure(
    title: str = "System requirements",
    panel: str = "Python 3.12 or newer",
    *,
    inputs: str = "",
    actions: str | None = None,
) -> str:
    actions_fill = "" if actions is None else f'<c-fill name="actions">{actions}</c-fill>'
    return f"""
      <c-CDisclosure {inputs}>
        <c-fill name="title">{title}</c-fill>
        {actions_fill}
        <c-fill name="default">{panel}</c-fill>
      </c-CDisclosure>
    """


def test_schema_aliases_and_exports_are_exact():
    assert [field.name for field in fields(CDisclosure.Kwargs)] == [
        "open",
        "disabled",
        "variant",
        "size",
        "indicator",
        "indicator_pos",
        "heading_level",
        "region",
        "actions_label",
        "id",
        "class_",
        "style",
        "attrs",
        "heading_attrs",
        "trigger_attrs",
        "panel_attrs",
        "actions_attrs",
    ]
    assert [field.name for field in fields(CDisclosure.Slots)] == ["title", "default", "actions"]
    hints = get_type_hints(CDisclosure.Kwargs)
    assert hints["variant"] == CDisclosureVariant
    assert hints["size"] == CDisclosureSize
    assert hints["indicator_pos"] == CDisclosureIndicatorPos
    assert hints["heading_level"] == CDisclosureHeadingLevel
    assert CDisclosureOpenChangeDetail.__required_keys__ == {
        "open",
        "previousOpen",
        "source",
        "controlled",
    }

    from citry_ui.components import cdisclosure

    assert cdisclosure.__all__ == [
        "CDisclosure",
        "CDisclosureActionsSlotData",
        "CDisclosureDefaultSlotData",
        "CDisclosureHeadingLevel",
        "CDisclosureIndicatorPos",
        "CDisclosureOpenChangeDetail",
        "CDisclosureSize",
        "CDisclosureTitleSlotData",
        "CDisclosureVariant",
    ]
    assert CDisclosureTitleSlotData()
    assert CDisclosureDefaultSlotData()
    assert CDisclosureActionsSlotData()


def test_native_anatomy_ids_states_region_and_actions_are_exact():
    html = _render(
        _disclosure(
            "<strong>System requirements</strong>",
            "<p>Python 3.12 or newer</p>",
            inputs=(
                'id="requirements" open disabled region heading_level="2" '
                'variant="soft" size="lg" indicator_pos="start" '
                'actions_label="Requirement actions"'
            ),
            actions='<button type="button">Copy link</button>',
        )
    )

    assert 'id="requirements"' in html
    assert 'data-citry-ui-part="disclosure"' in html
    assert '<h2 class="cui-disclosure__heading"' in html
    assert re.search(r"<h2[^>]*>\s*<button", html)
    assert 'type="button" id="requirements-trigger"' in html
    assert 'aria-expanded="true" aria-controls="requirements-panel"' in html
    assert 'id="requirements-panel" role="region" aria-labelledby="requirements-trigger"' in html
    assert 'data-variant="soft" data-size="lg" data-state="open" data-disabled' in html
    assert 'data-indicator-pos="start"' in html
    assert 'role="group" aria-label="Requirement actions"' in html
    assert html.index('data-citry-ui-part="disclosure-heading"') < html.index(
        'data-citry-ui-part="disclosure-actions"'
    )
    assert 'focusable="false" aria-hidden="true"' in html

    closed = _render(_disclosure(inputs='id="closed" c-indicator="False"'))
    assert re.search(r'id="closed-panel"[^>]* aria-hidden="true" hidden inert', closed)
    assert 'data-state="closed"' in closed
    assert re.search(r'cui-disclosure__indicator" hidden aria-hidden="true"', closed)
    assert 'role="region"' not in closed
    assert "aria-labelledby=" not in closed


@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        ('c-open="1"', "open must be a bool"),
        ('c-disabled="1"', "disabled must be a bool"),
        ('variant="loud"', "variant must be one of"),
        ('size="xl"', "size must be one of"),
        ('indicator_pos="middle"', "indicator_pos must be one of"),
        ('heading_level="1"', "heading_level must be one of"),
        ('id="two words"', "cannot contain ASCII whitespace"),
        ('actions_label="   "', "must contain non-whitespace text"),
    ],
)
def test_invalid_configuration_is_rejected(inputs: str, message: str):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(_disclosure(inputs=inputs))


def test_actions_options_require_the_actions_slot():
    with pytest.raises(ValueError, match="actions_label requires"):
        _render(_disclosure(inputs='actions_label="Actions"'))
    with pytest.raises(ValueError, match="actions_attrs requires"):
        _render(_disclosure(inputs="c-actions_attrs=\"{'class': 'tools'}\""))


def test_attribute_maps_are_copied_merged_and_land_only_on_their_destination():
    root_attrs = {"data-owner": "root", "class": "from-map"}
    heading_attrs = {"data-owner": "heading"}
    trigger_attrs = {"data-owner": "trigger", "aria-describedby": "help"}
    panel_attrs = {"data-owner": "panel"}
    actions_attrs = {"data-owner": "actions"}
    html = _render(
        _disclosure(
            inputs=(
                'class_="from-class" style="color: red" '
                'c-attrs="root_attrs" c-heading_attrs="heading_attrs" '
                'c-trigger_attrs="trigger_attrs" c-panel_attrs="panel_attrs" '
                'c-actions_attrs="actions_attrs"'
            ),
            actions='<button type="button">Copy</button>',
        ),
        {
            "root_attrs": root_attrs,
            "heading_attrs": heading_attrs,
            "trigger_attrs": trigger_attrs,
            "panel_attrs": panel_attrs,
            "actions_attrs": actions_attrs,
        },
    )

    assert 'class="cui-disclosure from-map from-class"' in html
    assert re.search(r'style="color:\s*red;?"', html)
    assert html.count('data-owner="root"') == 1
    assert html.count('data-owner="heading"') == 1
    assert html.count('data-owner="trigger"') == 1
    assert html.count('data-owner="panel"') == 1
    assert html.count('data-owner="actions"') == 1
    assert 'aria-describedby="help"' in html
    assert root_attrs == {"data-owner": "root", "class": "from-map"}


@pytest.mark.parametrize(
    ("input_name", "attribute"),
    [
        ("attrs", "id"),
        ("attrs", "data-citry-disclosure-root"),
        ("heading_attrs", "aria-level"),
        ("trigger_attrs", "aria-expanded"),
        ("trigger_attrs", ":disabled"),
        ("panel_attrs", "x-bind:hidden"),
        ("actions_attrs", "role"),
        ("actions_attrs", "data-cev-action"),
        ("attrs", "x-html"),
    ],
)
def test_owned_runtime_and_dynamic_attribute_aliases_are_rejected(
    input_name: str,
    attribute: str,
):
    actions = '<button type="button">Copy</button>' if input_name == "actions_attrs" else None
    with pytest.raises(ValueError, match="cannot"):
        _render(
            _disclosure(
                inputs=f'c-{input_name}="{{{attribute!r}: True}}"',
                actions=actions,
            )
        )


def test_root_presence_and_supplementary_trigger_metadata_remain_allowed():
    html = _render(
        _disclosure(
            inputs=(
                "c-attrs=\"{'hidden': False, 'x-show': 'visible'}\" "
                "c-trigger_attrs=\"{'aria-describedby': 'help', "
                "'aria-details': 'details', 'aria-keyshortcuts': 'Alt+S'}\""
            )
        )
    )
    assert 'x-show="visible"' in html
    assert 'aria-describedby="help"' in html
    assert 'aria-details="details"' in html
    assert 'aria-keyshortcuts="Alt+S"' in html


def test_title_accepts_the_exact_phrasing_and_decorative_svg_contract():
    title = """
      <abbr title="Representational state transfer">REST</abbr>
      <picture><source srcset="small.png" /><img src="large.png" alt="" /></picture>
      <svg aria-hidden="true" focusable="false" viewBox="0 0 10 10">
        <g><path d="M0 0L1 1" /></g>
      </svg>
      <code>API</code>
    """
    html = _render(_disclosure(title))
    assert "REST" in html
    assert re.search(r'<img src="large\.png" alt(?:="")?\s*/?>', html)
    assert "<code>API</code>" in html


@pytest.mark.parametrize(
    ("title", "message"),
    [
        ("   \n\t", "nonempty textual content"),
        ('<img src="icon.png" alt="" />', "nonempty textual content"),
        ('<svg aria-hidden="true" focusable="false"><path /></svg>', "nonempty textual content"),
        ('<img src="icon.png" alt="Icon" />Name', "requires alt"),
        ('<svg aria-hidden="false" focusable="false"></svg>Name', "requires aria-hidden"),
        ('<svg aria-hidden="true" focusable="false"><text>Name</text></svg>Name', "unsupported"),
        ('<a href="/help">Help</a>', "unsupported"),
        ('<span role="button">Help</span>', "cannot use"),
        ('<span aria-label="Hidden">Help</span>', "cannot use"),
        ('<span @click="run">Help</span>', "event attribute"),
        ('<span :href="target">Help</span>', "dynamically bind"),
    ],
)
def test_title_rejects_interactive_hidden_renamed_or_decorative_only_output(
    title: str,
    message: str,
):
    with pytest.raises(ValueError, match=message):
        _render(_disclosure(title))


@pytest.mark.parametrize(
    ("destination", "content", "message"),
    [
        ("panel", "<dialog>Unsafe</dialog>", "dialog"),
        ("panel", "<x-help>Unsafe</x-help>", "custom element"),
        ("panel", '<button is="fancy-button">Unsafe</button>', "customized built-ins"),
        ("panel", '<div popover="manual">Unsafe</div>', "raw or unrecognized"),
        (
            "panel",
            '<div popover="auto" data-citry-ui-part="popover">Unsafe</div>',
            "raw or unrecognized",
        ),
        ("actions", "<dialog>Unsafe</dialog>", "dialog"),
        ("actions", "<x-help>Unsafe</x-help>", "custom element"),
    ],
)
def test_panel_and_actions_reject_forbidden_rendered_surfaces(
    destination: str,
    content: str,
    message: str,
):
    template = _disclosure(panel=content) if destination == "panel" else _disclosure(actions=content)
    with pytest.raises(ValueError, match=message):
        _render(template)


def test_panel_accepts_exact_coordinator_marker_and_ordinary_form_controls():
    html = _render(
        _disclosure(
            panel=('<input name="email" required /><div popover="manual" data-citry-ui-part="popover">Help</div>')
        )
    )
    assert 'name="email" required' in html
    assert 'popover="manual" data-citry-ui-part="popover"' in html


def test_disclosure_nesting_is_panel_only():
    nested = _disclosure("Nested title", "Nested panel", inputs='id="nested"')
    html = _render(_disclosure(panel=nested, inputs='id="outer"'))
    assert html.count('data-citry-ui-part="disclosure"') == 2

    with pytest.raises(ValueError, match="only inside a CDisclosure panel"):
        _render(_disclosure(title=nested))
    with pytest.raises(ValueError, match="only inside a CDisclosure panel"):
        _render(_disclosure(actions=nested))


def test_accordion_nesting_is_accepted_in_panel_and_rejected_in_actions():
    accordion = """
      <c-CAccordion id="troubleshooting">
        <c-CAccordionItem value="logs">
          <c-fill name="title">Logs</c-fill>
          <c-fill name="default">Read the log file.</c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """
    html = _render(_disclosure(panel=accordion), full_library=True)
    assert 'data-citry-ui-part="accordion"' in html

    with pytest.raises(ValueError, match="only in panel content"):
        _render(_disclosure(actions=accordion), full_library=True)


def test_disclosure_inside_accordion_is_also_panel_only():
    nested = _disclosure("Nested disclosure", "Nested details", inputs='id="nested-disclosure"')
    panel = f"""
      <c-CAccordion id="panel-owner">
        <c-CAccordionItem value="entry">
          <c-fill name="title">Entry</c-fill>
          <c-fill name="default">{nested}</c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """
    html = _render(panel, full_library=True)
    assert 'id="nested-disclosure"' in html

    for slot in ("title", "actions"):
        invalid = f"""
          <c-CAccordion id="invalid-owner">
            <c-CAccordionItem value="entry">
              <c-fill name="title">{nested if slot == "title" else "Entry"}</c-fill>
              <c-fill name="actions">{nested if slot == "actions" else "Action"}</c-fill>
              <c-fill name="default">Panel</c-fill>
            </c-CAccordionItem>
          </c-CAccordion>
        """
        with pytest.raises(ValueError, match="only inside an Accordion item panel"):
            _render(invalid, full_library=True)


def test_hostile_text_is_escaped_in_every_slot():
    html = _render(
        """
          <c-CDisclosure>
            <c-fill name="title">{{ title }}</c-fill>
            <c-fill name="actions"><button type="button">{{ action }}</button></c-fill>
            <c-fill name="default">{{ panel }}</c-fill>
          </c-CDisclosure>
        """,
        {
            "title": '<img src=x onerror="alert(1)">Title',
            "action": "<script>alert(2)</script>",
            "panel": "<dialog open>Unsafe</dialog>",
        },
    )
    assert "&lt;img src=x onerror=" in html
    assert "&lt;script&gt;alert(2)&lt;/script&gt;" in html
    assert "&lt;dialog open&gt;Unsafe&lt;/dialog&gt;" in html
    assert "<dialog open>" not in html
