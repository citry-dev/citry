from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CStep, CStepper


def _render(template: str, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    source = template + ("<c-css />" if include_css else "")

    class Page(Component):
        citry = app
        template = source

    return str(Page())


def _tag(html: str, part: str, index: int = 0) -> str:
    tags = re.findall(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert len(tags) > index
    return tags[index]


def test_public_schemas_and_aliases_are_exact() -> None:
    assert [item.name for item in fields(CStepper.Kwargs)] == [
        "label",
        "active",
        "interactive",
        "linear",
        "disabled",
        "orientation",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CStep.Kwargs)] == [
        "disabled",
        "optional",
        "error",
        "class_",
        "style",
        "attrs",
    ]
    hints = get_type_hints(CStepper.Kwargs)
    assert hints["orientation"] == citry_ui.CStepperOrientation
    assert hints["variant"] == citry_ui.CStepperVariant
    assert hints["size"] == citry_ui.CStepperSize
    assert CStepper in citry_ui.COMPONENTS
    assert CStep in citry_ui.COMPONENTS


def test_static_stepper_is_named_ordered_progress() -> None:
    html = _render(
        '<c-CStepper label="Setup" c-active="1">'
        "<c-CStep>Profile</c-CStep><c-CStep>Security</c-CStep><c-CStep>Review</c-CStep>"
        "</c-CStepper>"
    )
    root = _tag(html, "stepper")
    assert root.startswith("<nav")
    assert 'aria-label="Setup"' in root
    assert 'data-active="1"' in root
    assert '<ol class="cui-stepper__list"' in html
    assert len(re.findall('data-citry-ui-part="step"', html.split("<script", 1)[0])) == 3
    assert 'data-state="complete"' in _tag(html, "step", 0)
    assert 'data-state="current"' in _tag(html, "step", 1)
    assert 'data-state="upcoming"' in _tag(html, "step", 2)
    assert _tag(html, "trigger", 0).startswith("<span")
    assert 'aria-current="step"' in _tag(html, "trigger", 1)


def test_interactive_stepper_uses_form_safe_buttons() -> None:
    html = _render(
        '<form><c-CStepper label="Setup" interactive c-active="1">'
        "<c-CStep>Profile</c-CStep><c-CStep>Security</c-CStep><c-CStep>Review</c-CStep>"
        "</c-CStepper></form>"
    )
    triggers = re.findall(r'<button[^>]+data-citry-ui-part="trigger"[^>]*>', html)
    assert len(triggers) == 3
    assert all('type="button"' in trigger for trigger in triggers)
    assert "disabled" not in triggers[0]
    assert "disabled" not in triggers[1]
    assert "disabled" in triggers[2]


def test_non_linear_keeps_future_step_available() -> None:
    html = _render(
        '<c-CStepper label="Setup" interactive c-linear="False">'
        "<c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>"
    )
    assert "disabled" not in _tag(html, "trigger", 1)


def test_step_description_relationship_and_metadata() -> None:
    html = _render(
        '<c-CStepper label="Setup"><c-CStep optional error>'
        '<c-fill name="default">Profile</c-fill>'
        '<c-fill name="description">Needs attention</c-fill>'
        "</c-CStep><c-CStep>Review</c-CStep></c-CStepper>"
    )
    step = _tag(html, "step", 0)
    trigger = _tag(html, "trigger", 0)
    description = _tag(html, "description")
    assert "data-optional" in step
    assert "data-error" in step
    description_id = re.search(r'id="([^"]+)"', description)
    assert description_id is not None
    assert f'aria-describedby="{description_id.group(1)}"' in trigger


def test_custom_indicator_replaces_numeric_fallback() -> None:
    html = _render(
        '<c-CStepper label="Setup"><c-CStep>'
        '<c-fill name="default">Profile</c-fill><c-fill name="indicator">P</c-fill>'
        "</c-CStep><c-CStep>Review</c-CStep></c-CStepper>"
    )
    assert ">P<" in html
    assert 'aria-hidden="true"' in _tag(html, "indicator", 0)


def test_root_and_step_class_style_attrs_reach_concrete_roots() -> None:
    html = _render(
        '<c-CStepper label="Setup" class_="brand" style="inline-size:20rem" '
        "c-attrs=\"{'data-test': 'root'}\">"
        "<c-CStep class_=\"first\" c-attrs=\"{'data-test': 'step'}\">One</c-CStep>"
        "<c-CStep>Two</c-CStep></c-CStepper>"
    )
    assert 'class="cui-stepper brand"' in _tag(html, "stepper")
    assert 'style="inline-size: 20rem;"' in _tag(html, "stepper")
    assert 'data-test="root"' in _tag(html, "stepper")
    assert 'class="cui-stepper__step first"' in _tag(html, "step", 0)
    assert 'data-test="step"' in _tag(html, "step", 0)


@pytest.mark.parametrize(
    ("template", "message"),
    [
        (
            "<c-CStepper c-label=\"''\"><c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>",
            "label must be nonempty",
        ),
        (
            '<c-CStepper label="Setup" c-active="-1"><c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>',
            "nonnegative",
        ),
        (
            '<c-CStepper label="Setup" orientation="diagonal">'
            "<c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>",
            "orientation must be one of",
        ),
        ('<c-CStepper label="Setup"><c-CStep>Only</c-CStep></c-CStepper>', "at least two"),
        (
            '<c-CStepper label="Setup" c-active="2"><c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>',
            "outside",
        ),
        (
            '<c-CStepper label="Setup" c-active="1">'
            "<c-CStep>One</c-CStep><c-CStep disabled>Two</c-CStep></c-CStepper>",
            "disabled Step",
        ),
    ],
)
def test_invalid_family_inputs_fail(template: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(template)


def test_step_outside_stepper_fails() -> None:
    with pytest.raises(ValueError, match="must be rendered directly inside CStepper"):
        _render("<c-CStep>Orphan</c-CStep>")


def test_non_declaration_root_content_fails() -> None:
    with pytest.raises(ValueError, match="only CStep declarations"):
        _render('<c-CStepper label="Setup"><p>Wrong</p><c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>')


@pytest.mark.parametrize(
    "template",
    [
        "<c-CStepper label=\"Setup\" c-attrs=\"{'role': 'list'}\">"
        "<c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>",
        "<c-CStepper label=\"Setup\" c-attrs=\"{':data-active': 'active'}\">"
        "<c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>",
        "<c-CStepper label=\"Setup\" c-attrs=\"{'x-html': 'content'}\">"
        "<c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>",
        "<c-CStepper label=\"Setup\"><c-CStep c-attrs=\"{'data-state': 'current'}\">"
        "One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>",
        "<c-CStepper label=\"Setup\"><c-CStep c-attrs=\"{':disabled': 'off'}\">"
        "One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>",
    ],
)
def test_owned_attrs_and_directives_are_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(template)


def test_css_exposes_public_variables_environment_rules_and_parts() -> None:
    html = _render(
        '<c-CStepper label="Setup"><c-CStep>One</c-CStep><c-CStep>Two</c-CStep></c-CStepper>',
        include_css=True,
    )
    for token in (
        "--cui-stepper-gap",
        "--cui-stepper-indicator-size",
        "--cui-stepper-active-color",
        "--cui-stepper-complete-color",
        "prefers-reduced-motion",
        "forced-colors",
        "@media print",
        'data-citry-ui-part="separator"',
    ):
        assert token in html
