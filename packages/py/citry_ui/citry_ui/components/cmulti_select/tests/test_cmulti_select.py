from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CField, CMultiSelect, CMultiSelectOption


def _render(template: str, *, data: dict[str, object] | None = None, css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    source = template + ("<c-css />" if css else "")

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data or {}

    page = Page()
    return str(page) if css else page.render().serialize(deps_strategy="ignore")


def _options() -> list[CMultiSelectOption]:
    return [
        CMultiSelectOption("earth", "Earth"),
        CMultiSelectOption("mars", "Mars", "The red planet", group="Rocky"),
        CMultiSelectOption("venus", "Venus", disabled=True, group="Rocky"),
        CMultiSelectOption("jupiter", "Jupiter", group="Gas giants"),
    ]


def _select(extra: str = "") -> str:
    return (
        '<c-CMultiSelect placeholder="Choose planets" c-options="options" '
        "c-trigger_attrs=\"{'aria-label': 'Planets'}\" "
        f"{extra} />"
    )


def _tag(html: str, part: str, index: int = 0) -> str:
    tags = re.findall(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert len(tags) > index
    return tags[index]


def test_public_schema_types_and_registration_are_exact() -> None:
    assert [item.name for item in fields(CMultiSelect.Kwargs)] == [
        "options",
        "placeholder",
        "name",
        "form",
        "id",
        "value",
        "open",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "loop",
        "close_on_select",
        "placement",
        "match_width",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
        "trigger_attrs",
        "listbox_attrs",
    ]
    hints = get_type_hints(CMultiSelect.Kwargs)
    assert hints["placement"] == citry_ui.CMultiSelectPlacement
    assert hints["variant"] == citry_ui.CMultiSelectVariant
    assert CMultiSelect in citry_ui.COMPONENTS


def test_progressive_native_proxy_and_custom_combobox_share_values() -> None:
    html = _render(
        _select("name=\"planet\" c-value=\"['earth', 'mars']\""),
        data={"options": _options()},
    )
    root = _tag(html, "root")
    control = _tag(html, "control")
    listbox = _tag(html, "listbox")
    assert "data-empty" not in root
    assert 'role="combobox"' in control
    assert 'aria-expanded="false"' in control
    assert 'aria-multiselectable="true"' in listbox
    assert re.search(r'<select[^>]+name="planet"[^>]+multiple[^>]*>', html)
    assert re.search(r'<option value="earth" selected>Earth</option>', html)
    assert re.search(r'<option value="mars" selected>Mars</option>', html)
    assert html.count('data-citry-ui-part="chip"') == 2


def test_groups_descriptions_disabled_and_selection_aria_are_exact() -> None:
    html = _render(_select("c-value=\"['mars']\""), data={"options": _options()})
    assert 'role="group"' in _tag(html, "group")
    assert "aria-labelledby=" in _tag(html, "group")
    mars = _tag(html, "option", 1)
    venus = _tag(html, "option", 2)
    assert 'aria-selected="true"' in mars
    assert "aria-describedby=" in mars
    assert 'aria-disabled="true"' in venus


def test_required_readonly_uses_repeated_hidden_inputs() -> None:
    html = _render(
        _select("name=\"planet\" c-value=\"['earth', 'mars']\" required readonly"),
        data={"options": _options()},
    )
    assert 'aria-required="true"' in _tag(html, "control")
    assert 'aria-readonly="true"' in _tag(html, "control")
    native = re.search(r"<select[^>]+data-cui-multi-select-native[^>]*>", html).group(0)
    assert " disabled" in native
    assert " required" not in native
    assert html.count('<input name="planet"') == 2


def test_field_owns_state_and_accessible_relationships() -> None:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "{{ field }}"

        def template_data(self, kwargs, slots):
            return {
                "field": CField(
                    required=True,
                    readonly=True,
                    slots={
                        "label": "Planets",
                        "description": "Pick several",
                        "default": CMultiSelect(options=_options(), placeholder="Choose"),
                    },
                )
            }

    html = Page().render().serialize(deps_strategy="ignore")
    control = _tag(html, "control", 1)
    native = re.search(r"<select[^>]+data-cui-multi-select-native[^>]*>", html).group(0)
    assert "aria-labelledby=" in control
    assert "aria-describedby=" in control
    assert "aria-describedby=" in native
    assert 'aria-required="true"' in control


@pytest.mark.parametrize(
    ("template", "data", "message"),
    [
        (_select(), {"options": []}, "at least one"),
        (_select("c-value=\"['unknown']\""), {"options": _options()}, "unknown Options"),
        (
            _select(),
            {"options": [CMultiSelectOption("a", "A"), CMultiSelectOption("a", "Again")]},
            "unique",
        ),
        (
            _select(),
            {
                "options": [
                    CMultiSelectOption("a", "A", group="One"),
                    CMultiSelectOption("b", "B"),
                    CMultiSelectOption("c", "C", group="One"),
                ]
            },
            "contiguous",
        ),
        (_select('placement="left"'), {"options": _options()}, "placement must be one of"),
        (
            '<c-CMultiSelect placeholder="Choose" c-options="options" />',
            {"options": _options()},
            "requires aria-label",
        ),
    ],
)
def test_invalid_server_contracts_fail(
    template: str,
    data: dict[str, object],
    message: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(template, data=data)


@pytest.mark.parametrize(
    "extra",
    [
        "c-attrs=\"{'role': 'application'}\"",
        "c-listbox_attrs=\"{'x-show':'open'}\"",
    ],
)
def test_owned_attrs_and_runtime_directives_are_rejected(extra: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(_select(extra), data={"options": _options()})


def test_owned_trigger_attributes_are_rejected() -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(
            '<c-CMultiSelect placeholder="Choose" c-options="options" '
            "c-trigger_attrs=\"{'aria-label':'Planets', 'type':'submit'}\" />",
            data={"options": _options()},
        )


def test_values_are_canonicalized_deduplicated_and_nul_is_rejected() -> None:
    html = _render(
        _select('c-value="selected"'),
        data={"selected": ["a\rb"], "options": [CMultiSelectOption("a\r\nb", "Line")]},
    )
    assert 'value="a\nb" selected' in html
    with pytest.raises(ValueError, match="duplicate"):
        _render(_select('c-value="selected"'), data={"selected": ["a", "a"], "options": _options()})
    with pytest.raises(ValueError, match="U\\+0000"):
        _render(_select(), data={"options": [CMultiSelectOption("a\0b", "Bad")]})


def test_css_exposes_tokens_progressive_enhancement_and_environment_rules() -> None:
    html = _render(_select(), data={"options": _options()}, css=True)
    for token in (
        "--cui-multi-select-background",
        "--cui-multi-select-selected-background",
        "--cui-multi-select-chip-background",
        "--cui-multi-select-duration",
    ):
        assert token in html
    assert ":not([data-citry-multi-select-initialized])" in html
    assert "prefers-reduced-motion" in html
    assert "forced-colors" in html
    assert "@media print" in html
