"""Attribute-name checks read a `str` subclass key as the text Citry writes into the page."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CDataGridColumn, CDataGridRow
from citry_ui.components._attrs import (
    attr_name_text,
    get_html_attr,
    html_attr_binding_target,
    is_executable_event_attribute,
    is_vue_directive_attribute,
)
from citry_ui.components._validation import reject_owned_attrs
from citry_ui.components.ctabs.ctabs import _reject_owned_attrs as reject_ctabs_owned_attrs

PACKAGE_ROOT = Path(citry_ui.__file__).resolve().parent


def _key(text: str, reported: str = "title") -> str:
    """Return `text` as a `str` subclass whose comparison methods all report the name `reported`."""

    class ReportsOtherName(str):
        __slots__ = ()

        def __eq__(self, other: object) -> bool:
            return other == reported

        def __hash__(self) -> int:
            return hash(reported)

        def lower(self) -> str:
            return reported

        def casefold(self) -> str:
            return reported

        def startswith(self, *_args: object) -> bool:
            return False

    return ReportsOtherName(text)


# A fresh app per test, because each test defines its own `Page` class and an
# app refuses a second class with the same name.
@pytest.fixture
def app() -> Citry:
    registry = Citry(autodiscover=False)
    registry.register_library(citry_ui)
    return registry


def _render(app: Citry, template: str, data: dict[str, Any]) -> str:
    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return data

    Page.template = template
    return Page().render().serialize(security_javascript="omit")


def test_attr_name_text_returns_the_stored_characters_as_a_plain_str() -> None:
    text = attr_name_text(_key("FormAction"))
    assert type(text) is str
    assert text == "FormAction"


def test_shared_owned_check_reads_the_real_name() -> None:
    with pytest.raises(ValueError, match="cannot override owned attribute 'ROLE'"):
        reject_owned_attrs({_key("ROLE"): "button"}, {"role"}, "CButton")


def test_tabs_owned_check_reads_the_real_name() -> None:
    with pytest.raises(ValueError, match="cannot override owned attribute"):
        reject_ctabs_owned_attrs({_key("ROLE"): "tab"}, {"role"}, "CTabs")


def test_shared_name_helpers_read_the_real_name() -> None:
    assert is_vue_directive_attribute(_key("V-ON:click"))
    assert is_executable_event_attribute(_key("OnClick"))
    assert html_attr_binding_target(_key(":HREF")) == "href"
    assert get_html_attr({_key("ID"): "x"}, "id", component_name="CButton") == "x"


_SPLIT_BUTTON = """
  <c-CSplitButton
    type="submit"
    label="Save actions"
    menu_label="More save actions"
    c-primary_attrs="attrs"
  >
    <c-fill name="default">Save</c-fill>
    <c-fill name="menu"><c-CMenuItem value="copy">Copy</c-CMenuItem></c-fill>
  </c-CSplitButton>
"""

# Each case gives a component a key whose own methods report a name the
# component accepts, while the text Citry would write is one it refuses.
_COMPONENT_CASES = {
    "CButton attrs formaction": (
        '<c-CButton type="submit" c-attrs="attrs">Go</c-CButton>',
        {_key("FORMACTION"): "x-app:open"},
        "CButton attrs 'formaction' must be a relative URL",
    ),
    "CSplitButton primary_attrs formaction": (
        _SPLIT_BUTTON,
        {_key("FORMACTION"): "x-app:open"},
        "'formaction' must be a relative URL",
    ),
    "CButton owned name": (
        '<c-CButton c-attrs="attrs">Go</c-CButton>',
        {_key("Type"): "submit"},
        "cannot override owned attribute",
    ),
    "CButton link form name": (
        '<c-CButton href="/next" c-attrs="attrs">Go</c-CButton>',
        {_key("FormTarget"): "_blank"},
        "apply only to action buttons",
    ),
    "CScrollArea allowlist": (
        '<c-CScrollArea c-attrs="attrs">Content</c-CScrollArea>',
        {_key("role"): "region"},
        "CScrollArea attrs cannot contain attribute",
    ),
    "CIcon aria name": (
        '<c-CIcon name="leaf" c-attrs="attrs" />',
        {_key("ARIA-ROLEDESCRIPTION"): "glyph"},
        "owned accessibility attribute",
    ),
    "CImage img_attrs owned name": (
        '<c-CImage src="/a.png" alt="Ada" c-width="1" c-height="1" c-img_attrs="attrs" />',
        {_key("SRC"): "/b.png"},
        "CImage img_attrs cannot override owned attribute",
    ),
}


@pytest.mark.parametrize("case", list(_COMPONENT_CASES))
def test_component_checks_read_the_real_name(app: Citry, case: str) -> None:
    template, attrs, message = _COMPONENT_CASES[case]
    with pytest.raises(ValueError, match=message):
        _render(app, template, {"attrs": attrs})


def test_data_grid_editor_attrs_check_reads_the_real_name(app: Citry) -> None:
    column = CDataGridColumn("x", "X", editable=True, editor_attrs={_key("autofocus", "placeholder"): True})
    with pytest.raises(ValueError, match="editor_attrs cannot contain 'autofocus'"):
        _render(
            app,
            '<c-CDataGrid c-columns="columns" c-rows="rows" label="Grid" />',
            {"columns": (column,), "rows": (CDataGridRow("row", {"x": "a"}),)},
        )


# Calling `lower()`, `casefold()`, `startswith()` or `endswith()` on a key
# would ask the subclass; every name check goes through `attr_name_text`.
_DIRECT_KEY_CALL = re.compile(
    r"\b(?:key|name|authored_name|attr_name|\w+_key)"
    r"\.(?:lower|casefold|startswith|endswith)\("
)
# These calls run on text that is already a plain `str`: a folded name, a
# name `HTMLParser` read from rendered HTML, and a message catalog key.
_PLAIN_TEXT_CALLS = {
    "components/cscroll_area/cscroll_area.py": 'if name.startswith("data-"):',
    "components/cdisclosure/cdisclosure.py": "normalized = name.casefold()",
    "components/ccombobox/ccombobox.py": 'if key.startswith("catalog_")',
}


def test_no_component_calls_a_method_on_an_attribute_key_directly() -> None:
    offenders = []
    for path in sorted((PACKAGE_ROOT / "components").rglob("*.py")):
        if "tests" in path.parts:
            continue
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not _DIRECT_KEY_CALL.search(line):
                continue
            allowed = _PLAIN_TEXT_CALLS.get(relative)
            if allowed is None or allowed not in line:
                offenders.append(f"{relative}:{number}: {line.strip()}")
    assert offenders == []
