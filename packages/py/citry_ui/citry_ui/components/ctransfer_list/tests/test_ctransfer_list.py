from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CTransferList, CTransferListItem


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>"

    return str(Page())


def test_public_schema_and_registration_are_explicit():
    assert [item.name for item in fields(CTransferList.Kwargs)] == [
        "id",
        "value",
        "name",
        "form",
        "required",
        "disabled",
        "show_move_all",
        "show_reorder",
        "size",
        "available_label",
        "chosen_label",
        "available_empty_label",
        "chosen_empty_label",
        "count_label",
        "transfer_controls_label",
        "add_label",
        "add_all_label",
        "remove_label",
        "remove_all_label",
        "reorder_controls_label",
        "move_top_label",
        "move_up_label",
        "move_down_label",
        "move_bottom_label",
        "added_label",
        "removed_label",
        "reordered_label",
        "required_label",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CTransferListItem.Kwargs)] == [
        "value",
        "label",
        "disabled",
        "class_",
        "style",
        "attrs",
    ]
    assert get_type_hints(CTransferList.Kwargs)["required"] is bool
    assert CTransferList in citry_ui.COMPONENTS
    assert CTransferListItem in citry_ui.COMPONENTS


def test_initial_anatomy_progressive_fallback_and_form_owner():
    html = _render(
        '<c-CTransferList id="people" name="reviewers" form="account" c-required="True" '
        'c-value="[\'grace\']"><c-CTransferListItem value="ada" label="Ada" />'
        '<c-CTransferListItem value="grace" label="Grace" /></c-CTransferList>'
    )

    assert 'id="people"' in html
    select = re.search(r"<select[^>]+>", html)
    assert select is not None
    assert 'name="reviewers"' in select.group(0)
    assert 'form="account"' in select.group(0)
    assert "required" in select.group(0)
    assert html.count('role="listbox"') == 2
    assert html.count('aria-multiselectable="true"') == 2
    assert len(re.findall(r"<div[^>]+data-citry-transfer-option", html)) == 2
    assert 'data-citry-transfer-action="add"' in html
    assert 'data-citry-transfer-action="move-bottom"' in html
    assert 'aria-live="polite"' in html


def test_value_controls_initial_panes_native_order_and_selected_state():
    html = _render(
        "<c-CTransferList c-value=\"['c','a']\">"
        '<c-CTransferListItem value="a" label="A" />'
        '<c-CTransferListItem value="b" label="B" />'
        '<c-CTransferListItem value="c" label="C" />'
        "</c-CTransferList>"
    )
    select = re.search(r"<select[^>]*>(.*?)</select>", html, re.DOTALL)
    assert select is not None
    option_values = re.findall(r'<option[^>]+value="([^"]+)"', select.group(1))
    assert option_values == ["b", "c", "a"]
    assert len(re.findall(r"<option[^>]+selected", select.group(1))) == 2
    chosen = html[html.index('data-citry-transfer-pane="chosen"') :]
    assert re.findall(r'data-value="([^"]+)"', chosen) == ["c", "a"]


def test_item_slot_data_and_rich_content_are_lazy_and_ordered():
    html = _render(
        "<c-CTransferList c-value=\"['b']\">"
        '<c-CTransferListItem value="a" label="Alpha"><c-fill name="default" '
        'data="{ value, label, disabled, in_target, index }">'
        "{{ value }}:{{ label }}:{{ disabled }}:{{ in_target }}:{{ index }}"
        "</c-fill></c-CTransferListItem>"
        '<c-CTransferListItem value="b" label="Beta" c-disabled="True"><strong>Rich beta</strong>'
        "</c-CTransferListItem></c-CTransferList>"
    )
    assert "a:Alpha:False:False:0" in html
    assert "<strong>Rich beta</strong>" in html
    option = re.search(r'<div[^>]+data-value="b"[^>]+>', html)
    assert option is not None
    assert 'aria-disabled="true"' in option.group(0)


def test_chosen_disabled_item_keeps_an_ordered_native_form_value_proxy():
    html = _render(
        "<c-CTransferList name=\"reviewers\" c-value=\"['locked','open']\">"
        '<c-CTransferListItem value="locked" label="Locked" c-disabled="True" />'
        '<c-CTransferListItem value="open" label="Open" />'
        "</c-CTransferList>"
    )
    select = re.search(r"<select[^>]*>(.*?)</select>", html, re.DOTALL)
    assert select is not None
    selected_values = re.findall(r'<option[^>]+value="([^"]+)"[^>]+selected', select.group(1))
    assert selected_values == ["locked", "locked", "open"]
    assert "data-citry-transfer-disabled-value-proxy" in select.group(1)
    assert re.search(r'<option[^>]+value="locked"[^>]+label="Locked"[^>]+hidden', select.group(1))
    assert re.search(r'<option[^>]+value="locked"[^>]+disabled', select.group(1))


def test_empty_list_and_visibility_flags_are_server_deterministic():
    empty = _render("<c-CTransferList />")
    assert "data-available-empty" in empty
    assert "data-chosen-empty" in empty
    assert empty.count("No available items") >= 1
    assert empty.count("No chosen items") >= 1

    available = _render('<c-CTransferList><c-CTransferListItem value="a" label="A" /></c-CTransferList>')
    root = re.search(r'<div class="cui-transfer-list"[^>]+>', available)
    assert root is not None
    assert "data-available-empty" not in root.group(0)
    assert "data-chosen-empty" in root.group(0)


def test_declaration_values_and_parent_value_are_validated():
    with pytest.raises(ValueError, match="duplicated"):
        _render(
            '<c-CTransferList><c-CTransferListItem value="a" label="A" />'
            '<c-CTransferListItem value="a" label="Again" /></c-CTransferList>'
        )
    with pytest.raises(ValueError, match="unknown item values"):
        _render("<c-CTransferList c-value=\"['missing']\" />")
    with pytest.raises(ValueError, match="must not contain duplicate"):
        _render(
            '<c-CTransferList c-value="[\'a\',\'a\']"><c-CTransferListItem value="a" label="A" /></c-CTransferList>'
        )
    with pytest.raises(ValueError, match="value must be nonempty"):
        _render('<c-CTransferList><c-CTransferListItem value=" " label="A" /></c-CTransferList>')
    with pytest.raises(ValueError, match="label must be nonempty"):
        _render('<c-CTransferList><c-CTransferListItem value="a" label=" " /></c-CTransferList>')


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('<c-CTransferList c-required="1" />', "required must be a bool"),
        ('<c-CTransferList size="xl" />', "size must be one of"),
        ('<c-CTransferList form="bad id" />', "cannot contain ASCII whitespace"),
        ("<c-CTransferList c-value=\"'a'\" />", "sequence of strings"),
        (
            '<c-CTransferList count_label="Selected"><c-CTransferListItem value="a" label="A" /></c-CTransferList>',
            "count_label must contain",
        ),
    ],
)
def test_invalid_configuration_fails_early(source: str, message: str):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(source)


def test_attrs_merge_and_owned_surfaces_are_rejected():
    html = _render(
        "<c-CTransferList class_=\"brand\" c-style=\"{'color':'red'}\" c-attrs=\"{'data-test':'root'}\">"
        '<c-CTransferListItem value="a" label="A" class_="row" '
        "c-attrs=\"{'data-test-item':'a'}\" /></c-CTransferList>"
    )
    assert re.search(r'<div class="cui-transfer-list brand"[^>]+data-test="root"', html)
    assert re.search(r'<div class="cui-transfer-list__option row"[^>]+data-test-item="a"', html)
    assert "color: red" in html

    with pytest.raises(ValueError, match="owned attribute 'id'"):
        _render("<c-CTransferList c-attrs=\"{'id':'wrong'}\" />")
    with pytest.raises(ValueError, match="owned attribute 'aria-selected'"):
        _render(
            '<c-CTransferList><c-CTransferListItem value="a" label="A" '
            "c-attrs=\"{'aria-selected':'true'}\" /></c-CTransferList>"
        )


def test_misplacement_extra_output_and_direct_nesting_are_rejected():
    with pytest.raises(ValueError, match="directly inside CTransferList"):
        _render('<c-CTransferListItem value="a" label="A" />')
    with pytest.raises(ValueError, match="may contain only CTransferListItem"):
        _render("<c-CTransferList><p>Unexpected</p></c-CTransferList>")
    with pytest.raises(ValueError, match="Nested CTransferList"):
        _render("<c-CTransferList><c-CTransferList /></c-CTransferList>")


def test_nested_transfer_list_inside_item_content_gets_fresh_scope():
    html = _render(
        '<c-CTransferList><c-CTransferListItem value="outer" label="Outer">'
        '<c-CTransferList><c-CTransferListItem value="inner" label="Inner" /></c-CTransferList>'
        "</c-CTransferListItem></c-CTransferList>"
    )
    assert len(re.findall(r'<div class="cui-transfer-list"', html)) == 2
    assert len(re.findall(r'data-value="outer"', html)) == 1
    assert len(re.findall(r'data-value="inner"', html)) == 1


def test_explicit_label_overrides_keep_caller_text_and_skip_that_binding():
    html = _render(
        '<c-CTransferList add_label="Include selected" chosen_label="Assigned">'
        '<c-CTransferListItem value="a" label="A" /></c-CTransferList>'
    )
    add = re.search(r'<button[^>]+data-citry-transfer-action="add"[^>]*>(.*?)</button>', html, re.DOTALL)
    assert add is not None
    assert "Include selected" in add.group(1)
    assert "Assigned" in html


def test_runtime_has_delegation_controlled_state_forms_i18n_and_cleanup():
    source = (Path(__file__).parents[1] / "runtime.source.js").read_text(encoding="utf8")
    assert "props: {value: {}, required: {}, disabled: {}, onValueChange: {}}" in source
    assert "i18n.bind" in source
    assert "citry-ui-transfer-list-added-one" in source
    assert "native.dispatchEvent(new Event('input'" in source
    assert "form?.addEventListener('reset'" in source
    assert "new MutationObserver" in source
    assert "transport.replaceChildren" in source
    assert "interactive descendants" in source
    assert "removeEventListener('keydown'" in source
    assert "data-citry-transfer-list-initialized" in source


def test_messages_are_final_component_member_and_cover_browser_outputs():
    keys = set(re.findall(r"^\s*(citry-ui-transfer-list-[a-z-]+)\s*=", CTransferList.messages, re.MULTILINE))
    assert {
        "citry-ui-transfer-list-available",
        "citry-ui-transfer-list-chosen",
        "citry-ui-transfer-list-count",
        "citry-ui-transfer-list-add",
        "citry-ui-transfer-list-remove",
        "citry-ui-transfer-list-move-bottom",
        "citry-ui-transfer-list-added-one",
        "citry-ui-transfer-list-added",
        "citry-ui-transfer-list-required",
    } <= keys
    members = list(CTransferList.__dict__)
    assert members.index("messages") > members.index("css_file")
    assert "messages" not in CTransferListItem.__dict__
