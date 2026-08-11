from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CField, CSelect, CSelectOption


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


def _options() -> list[CSelectOption]:
    return [
        CSelectOption("earth", "Earth"),
        CSelectOption("mars", "Mars", "The red planet", group="Rocky"),
        CSelectOption("venus", "Venus", disabled=True, group="Rocky"),
    ]


def _select(extra: str = "") -> str:
    return (
        '<c-CSelect placeholder="Choose a planet" c-options="options" '
        "c-trigger_attrs=\"{'aria-label': 'Planet'}\" "
        f"{extra} />"
    )


def _tag(html: str, part: str, index: int = 0) -> str:
    tags = re.findall(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert len(tags) > index
    return tags[index]


def test_public_schema_types_and_registration_are_exact() -> None:
    assert [item.name for item in fields(CSelect.Kwargs)] == [
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
    hints = get_type_hints(CSelect.Kwargs)
    assert hints["placement"] == citry_ui.CSelectPlacement
    assert hints["variant"] == citry_ui.CSelectVariant
    assert CSelect in citry_ui.COMPONENTS


def test_progressive_native_proxy_and_custom_combobox_share_exact_value() -> None:
    html = _render(_select('name="planet" value="earth"'), data={"options": _options()})
    root = _tag(html, "root")
    control = _tag(html, "control")
    listbox = _tag(html, "listbox")
    assert 'data-variant="outline"' in root
    assert 'role="combobox"' in control
    assert 'aria-expanded="false"' in control
    assert 'aria-label="Planet"' in control
    assert 'role="listbox"' in listbox
    assert 'aria-label="Planet"' in listbox
    assert re.search(r'<select[^>]+name="planet"[^>]*>', html)
    assert re.search(r'<option value="earth" selected>Earth</option>', html)
    assert "tabindex" not in re.search(r"<select[^>]+data-cui-select-native[^>]*>", html).group(0)


def test_group_description_disabled_and_selected_aria_are_exact() -> None:
    html = _render(_select('value="mars"'), data={"options": _options()})
    assert 'role="group"' in _tag(html, "group")
    assert "aria-labelledby=" in _tag(html, "group")
    mars = _tag(html, "option", 1)
    venus = _tag(html, "option", 2)
    assert 'aria-selected="true"' in mars
    assert "aria-describedby=" in mars
    assert 'aria-disabled="true"' in venus


def test_empty_required_readonly_and_form_proxy_states_are_coherent() -> None:
    html = _render(
        _select('name="planet" required readonly'),
        data={"options": _options()},
    )
    assert "data-empty" in _tag(html, "root")
    assert 'aria-required="true"' in _tag(html, "control")
    assert 'aria-readonly="true"' in _tag(html, "control")
    native = re.search(r"<select[^>]+data-cui-select-native[^>]*>", html).group(0)
    assert " disabled" in native
    assert " required" not in native
    assert re.search(r'<input name="planet" value="" type="hidden"', html)


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
                        "label": "Planet",
                        "description": "Pick one",
                        "default": CSelect(options=_options(), placeholder="Choose"),
                    },
                )
            }

    html = Page().render().serialize(deps_strategy="ignore")
    control = _tag(html, "control", 1)
    assert "aria-labelledby=" in control
    assert "aria-describedby=" in control
    assert 'aria-required="true"' in control
    assert 'aria-readonly="true"' in control


@pytest.mark.parametrize(
    ("template", "data", "message"),
    [
        (_select(), {"options": []}, "at least one"),
        (_select('value="unknown"'), {"options": _options()}, "does not match"),
        (_select(), {"options": [CSelectOption("a", "A"), CSelectOption("a", "Again")]}, "unique"),
        (
            _select(),
            {
                "options": [
                    CSelectOption("a", "A", group="One"),
                    CSelectOption("b", "B"),
                    CSelectOption("c", "C", group="One"),
                ]
            },
            "contiguous",
        ),
        (_select('placement="left"'), {"options": _options()}, "placement must be one of"),
        (
            '<c-CSelect placeholder="Choose" c-options="options" />',
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


@pytest.mark.parametrize(
    "attrs",
    [
        "{'aria-label':'Planet', ':aria-describedby':'ids'}",
        "{'aria-label':'Planet', 'type':'submit'}",
    ],
)
def test_owned_trigger_attrs_are_rejected(attrs: str) -> None:
    template = f'<c-CSelect placeholder="Choose" c-options="options" c-trigger_attrs="{attrs}" />'
    with pytest.raises(ValueError, match="cannot"):
        _render(template, data={"options": _options()})


def test_direct_strings_are_canonicalized_and_nul_is_rejected() -> None:
    html = _render(
        _select('c-value="selected"'),
        data={"selected": "a\rb", "options": [CSelectOption("a\r\nb", "Line")]},
    )
    assert 'value="a\nb" selected' in html
    with pytest.raises(ValueError, match="U\\+0000"):
        _render(_select(), data={"options": [CSelectOption("a\0b", "Bad")]})


def test_css_exposes_public_tokens_progressive_enhancement_and_environment_rules() -> None:
    html = _render(_select(), data={"options": _options()}, css=True)
    for token in (
        "--cui-select-background",
        "--cui-select-selected-background",
        "--cui-select-control-padding",
        "--cui-select-duration",
    ):
        assert token in html
    assert ":not([data-citry-select-initialized])" in html
    assert "prefers-reduced-motion" in html
    assert "forced-colors" in html
    assert "@media print" in html
