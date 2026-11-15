"""Citry UI refuses attribute names its browser code reads when they arrive in an `attrs=` map from Python."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CTableCell, CTableColumn, CTableRow
from citry_ui.components._attrs import (
    CitryUiOwnedValue,
    citry_ui_owned_value,
    reject_citry_ui_reserved_attr,
    reject_citry_ui_reserved_attrs,
)

PACKAGE_ROOT = Path(citry_ui.__file__).resolve().parent
REFUSED = "are reserved for the browser"


# A fresh app per test, because each test defines its own `Page` class and an
# app refuses a second class with the same name.
@pytest.fixture
def app() -> Citry:
    registry = Citry(autodiscover=False)
    registry.register_library(citry_ui)
    return registry


def _render(app: Citry, template: str, data: dict[str, Any] | None = None) -> str:
    """Render `template` with `data` and return the page HTML."""
    values = data or {}

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return values

    Page.template = template
    return Page().render().serialize(security_javascript="omit")


# --- The shared check ---------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "data-citry-dialog-close",
        "DATA-CITRY-DIALOG-CLOSE",
        "data-citry-",
        "data-cev-action",
        "data-cid",
        "data-cid-c00example",
    ],
)
def test_reserved_names_are_refused_with_a_plain_value(name: str) -> None:
    with pytest.raises(ValueError, match=rf"CButton attrs cannot set '{re.escape(name)}'\. .*{REFUSED}"):
        reject_citry_ui_reserved_attr(name, "", where="CButton attrs")


@pytest.mark.parametrize("value", ["", "x", True, 0, citry_ui_owned_value("")])
def test_core_citry_names_stay_refused_even_with_an_owned_value(value: object) -> None:
    """Only `data-citry-*` names can carry a value Citry UI wrote; `data-cid` never can."""
    with pytest.raises(ValueError, match=REFUSED):
        reject_citry_ui_reserved_attr("data-cid", value, where="CButton attrs")


@pytest.mark.parametrize(
    "name",
    [
        "title",
        "data-state",
        "data-citrine",
        # Browsers fold only ASCII letters, so a dotless i is another name.
        "data-c\N{LATIN SMALL LETTER DOTLESS I}try-dialog-close",
    ],
)
def test_other_names_pass(name: str) -> None:
    reject_citry_ui_reserved_attr(name, "x", where="CButton attrs")


@pytest.mark.parametrize("value", [None, False])
def test_a_value_that_writes_no_attribute_passes(value: object) -> None:
    reject_citry_ui_reserved_attr("data-citry-dialog-close", value, where="CButton attrs")


def test_a_value_citry_ui_wrote_passes_for_a_data_citry_name() -> None:
    value = citry_ui_owned_value()
    assert isinstance(value, CitryUiOwnedValue)
    assert value == ""
    reject_citry_ui_reserved_attr("data-citry-dialog-close", value, where="CButton attrs")


def test_a_component_can_reserve_more_prefixes() -> None:
    reject_citry_ui_reserved_attr("data-cni-step", "1", where="CNumberInput attrs")
    with pytest.raises(ValueError, match="'data-cni'"):
        reject_citry_ui_reserved_attr("data-cni-step", "1", where="CNumberInput attrs", extra_prefixes=("data-cni",))


def test_the_map_check_reads_every_entry() -> None:
    reject_citry_ui_reserved_attrs(None, "CButton attrs")
    with pytest.raises(ValueError, match="'data-citry-tour-trigger'"):
        reject_citry_ui_reserved_attrs({"title": "x", "data-citry-tour-trigger": ""}, "CButton attrs")


# --- Every name the browser code reads is covered ------------------------------


def _browser_code_names() -> set[str]:
    """
    Return every `data-citry-*` name in the source Citry UI ships.

    Component `js`, the shared runtime modules, `runtime.source.js` files,
    templates and CSS all count: the browser reads a name in a script, a
    selector or a stylesheet. `element.dataset.citryToastId` is the name
    `data-citry-toast-id`.
    """
    names: set[str] = set()
    for path in PACKAGE_ROOT.rglob("*"):
        if path.suffix not in {".py", ".js", ".css"} or "tests" in path.parts or ".min." in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        names.update(re.findall(r"data-citry-[a-z0-9-]*[a-z0-9]", text))
        for prop in re.findall(r"dataset\.(citry[A-Z][A-Za-z0-9]*)", text):
            names.add("data-" + re.sub(r"[A-Z]", lambda match: "-" + match.group(0).lower(), prop))
    return names


def test_every_data_citry_name_in_citry_ui_source_is_refused() -> None:
    """
    Fails when the check stops covering a name Citry UI's browser code reads.

    The check refuses the whole `data-citry-` prefix, so this holds as long as
    nobody narrows it to a list that misses a name.
    """
    names = _browser_code_names()
    # Guards the scan itself: an empty or tiny result means the regex or the
    # file walk broke, not that the check is complete.
    assert {"data-citry-dialog-close", "data-citry-ui-part", "data-citry-toast-id"} <= names
    assert len(names) > 100
    missed = []
    for name in sorted(names):
        try:
            reject_citry_ui_reserved_attr(name, "", where="CButton attrs")
        except ValueError:
            continue
        missed.append(name)
    assert missed == []


# --- Components ---------------------------------------------------------------


def test_button_refuses_another_components_marker_from_data(app: Citry) -> None:
    """The case from the issue: request data that names `data-citry-dialog-close` on a Button."""
    with pytest.raises(ValueError, match=f"CButton attrs cannot set 'data-citry-dialog-close'.*{REFUSED}"):
        _render(
            app,
            """
            <c-CButton c-attrs="attrs">Save</c-CButton>
            """,
            {"attrs": {"data-citry-dialog-close": ""}},
        )


def test_button_takes_the_dialog_slot_attrs_it_is_handed(app: Citry) -> None:
    """The documented composition keeps working: Dialog's slot attrs carry values Citry UI wrote."""
    html = _render(
        app,
        """
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open</c-CButton>
          </c-fill>
          <c-fill name="title">Title</c-fill>
          <c-fill name="default">Body</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Done</c-CButton>
          </c-fill>
        </c-CDialog>
        """,
    )

    buttons = re.findall(r'<button class="cui-button"[^>]*>', html)
    assert any("data-citry-dialog-trigger" in button for button in buttons)
    assert any("data-citry-dialog-close" in button for button in buttons)


def test_slot_attrs_still_work_after_the_caller_adds_names(app: Citry) -> None:
    """Merging your own names into slot attrs keeps the values Citry UI wrote."""
    html = _render(
        app,
        """
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="{**activator_attrs, 'title': 'More'}">Open</c-CButton>
          </c-fill>
          <c-fill name="title">Title</c-fill>
          <c-fill name="default">Body</c-fill>
        </c-CPopover>
        """,
    )

    assert re.search(r'<button class="cui-button"[^>]*data-citry-popover-trigger[^>]*title="More"', html)


def test_context_menu_target_keeps_its_documented_native_escape(app: Citry) -> None:
    """`data-citry-context-menu-native` on the target only turns ContextMenu off, so it stays allowed."""
    html = _render(
        app,
        """
        <c-CContextMenu aria_label="Actions" c-target_attrs="target">
          <c-fill name="target" data="{ target_attrs }">
            <c-CButton c-attrs="target_attrs">Target</c-CButton>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="copy">Copy</c-CMenuItem>
          </c-fill>
        </c-CContextMenu>
        """,
        {"target": {"data-citry-context-menu-native": ""}},
    )

    assert re.search(r'<button class="cui-button"[^>]*data-citry-context-menu-native', html)


# One case per component that checked only the names it writes itself before
# the shared check existed, plus a data object input.
COMPONENT_CASES: dict[str, tuple[str, dict[str, Any]]] = {
    "dialog": (
        """
        <c-CDialog c-attrs="attrs">
          <c-fill name="title">Title</c-fill>
          <c-fill name="default">Body</c-fill>
        </c-CDialog>
        """,
        {},
    ),
    "drawer": (
        """
        <c-CDrawer c-attrs="attrs">
          <c-fill name="title">Title</c-fill>
          <c-fill name="default">Body</c-fill>
        </c-CDrawer>
        """,
        {},
    ),
    "form": (
        """
        <c-CForm c-attrs="attrs">x</c-CForm>
        """,
        {},
    ),
    "combobox-input": (
        """
        <c-CCombobox name="plan" c-options="options" c-input_attrs="attrs" />
        """,
        {"options": ()},
    ),
    "table-cell": (
        """
        <c-CTable c-columns="columns" c-rows="rows" />
        """,
        {},
    ),
}


@pytest.mark.parametrize("case", list(COMPONENT_CASES))
def test_components_refuse_reserved_names_from_data(app: Citry, case: str) -> None:
    template, data = COMPONENT_CASES[case]
    attrs = {"data-citry-popover-close": ""}
    values = {**data, "attrs": attrs}
    if case == "table-cell":
        values = {
            "columns": (CTableColumn("n", "Name"),),
            "rows": (CTableRow("r1", {"n": CTableCell("x", attrs=attrs)}),),
        }
    with pytest.raises(ValueError, match=f"'data-citry-popover-close'.*{REFUSED}"):
        _render(app, template, values)


# --- Every component module runs the check -------------------------------------

_CHECKS = {"reject_citry_ui_reserved_attr", "reject_citry_ui_reserved_attrs", "reject_owned_attrs"}


def _declares_attrs_input(tree: ast.Module) -> bool:
    """Return whether a module declares an `attrs` or `*_attrs` field on a class other than slot data."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and not node.name.endswith("SlotData"):
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    name = statement.target.id
                    if name == "attrs" or name.endswith("_attrs"):
                        return True
    return False


def _calls_a_check(tree: ast.Module) -> bool:
    """Return whether any function in the module calls one of the shared checks."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name in _CHECKS:
                return True
    return False


def test_every_component_module_with_an_attrs_input_runs_the_shared_check() -> None:
    """
    A new component with an `attrs=` input fails here until it calls the shared check.

    The test reads the source rather than rendering every component, which
    would need a working set of inputs and slots for each one. The rendering
    cases above prove the check fires once it is called.
    """
    missing = []
    for path in sorted((PACKAGE_ROOT / "components").glob("c*/c*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _declares_attrs_input(tree) and not _calls_a_check(tree):
            missing.append(path.parent.name)
    assert missing == []
