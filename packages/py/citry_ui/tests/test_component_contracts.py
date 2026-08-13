"""Cross-family authoring contracts learned from the Tabs production pass."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
COMPONENT_ROOT = REPO_ROOT / "packages/py/citry_ui/citry_ui/components"
SPEC_ROOT = REPO_ROOT / "docs/design/ui_components"

SPEC_HEADINGS = (
    "## 1. Purpose and product bar",
    "## 2. Prior art and complaints",
    "## 3. Public composition and anatomy",
    "## 4. Server inputs and client inputs",
    "## 5. State model",
    "## 6. Slots and slot data",
    "## 7. Callbacks, native events, and methods",
    "## 8. Semantics, keyboard, focus, and assistive technology",
    "## 9. Native forms and validation",
    "## 10. Styling and theme contract",
    "## 11. Environmental behavior",
    "## 12. Overlay and layering behavior",
    "## 13. Collections, async data, and identity",
    "## 14. Server render, morph, and cleanup",
    "## 15. Security and content trust",
    "## 16. Assets and performance",
    "## 17. Acceptance matrix",
    "## 18. Compatibility classification",
    "## 19. Public documentation contract",
    "## 20. Open decisions and deferred work",
    "## 21. Internationalization",
)


@dataclass(frozen=True, slots=True)
class FamilyContract:
    package: str
    module: str
    spec: str
    reflected_attributes: frozenset[str]
    shared_parts: frozenset[str] = frozenset()
    theme_variables: frozenset[str] = frozenset()


FAMILIES = (
    FamilyContract(
        "caccordion",
        "caccordion.py",
        "accordion.md",
        frozenset(
            {
                "aria-controls",
                "aria-disabled",
                "aria-expanded",
                "aria-hidden",
                "aria-labelledby",
                "data-collapsible",
                "data-disabled",
                "data-indicator",
                "data-indicator-pos",
                "data-loop",
                "data-multiple",
                "data-size",
                "data-state",
                "data-value",
                "data-variant",
                "disabled",
                "hidden",
                "id",
                "inert",
                "role",
            }
        ),
    ),
    FamilyContract(
        "cdisclosure",
        "cdisclosure.py",
        "disclosure.md",
        frozenset(
            {
                "aria-controls",
                "aria-expanded",
                "aria-hidden",
                "aria-labelledby",
                "data-disabled",
                "data-indicator",
                "data-indicator-pos",
                "data-size",
                "data-state",
                "data-variant",
                "disabled",
                "hidden",
                "id",
                "inert",
                "role",
            }
        ),
    ),
    FamilyContract(
        "calert",
        "calert.py",
        "alert.md",
        frozenset(
            {
                "data-announce",
                "data-icon",
                "data-intent",
                "data-size",
                "data-variant",
                "role",
            }
        ),
    ),
    FamilyContract(
        "calert_dialog",
        "calert_dialog.py",
        "alert-dialog.md",
        frozenset(
            {"aria-describedby", "aria-labelledby", "aria-modal", "data-open", "data-scroll", "data-size", "role"}
        ),
    ),
    FamilyContract(
        "cbreadcrumbs",
        "cbreadcrumbs.py",
        "breadcrumbs.md",
        frozenset({"aria-current", "aria-label", "data-size", "data-wrap", "href"}),
    ),
    FamilyContract(
        "ccard",
        "ccard.py",
        "card.md",
        frozenset({"data-size", "data-variant"}),
    ),
    FamilyContract(
        "cflow",
        "cflow.py",
        "flow-layout.md",
        frozenset({"data-align", "data-gap", "data-justify", "data-reverse", "data-wrap"}),
    ),
    FamilyContract(
        "cgrid",
        "cgrid.py",
        "grid-container.md",
        frozenset(
            {
                "data-cols",
                "data-cols-sm",
                "data-cols-md",
                "data-cols-lg",
                "data-cols-xl",
                "data-cols-xxl",
                "data-fluid",
                "data-gap",
                "data-gutter",
                "data-intrinsic",
                "data-size",
                "data-span",
                "data-span-sm",
                "data-span-md",
                "data-span-lg",
                "data-span-xl",
                "data-span-xxl",
            }
        ),
    ),
    FamilyContract(
        "cscroll_area",
        "cscroll_area.py",
        "scroll-area.md",
        frozenset(
            {
                "aria-label",
                "aria-labelledby",
                "data-axis",
                "data-overscroll",
                "data-scrollbar-gutter",
                "data-scrollbar-width",
                "id",
                "role",
                "tabindex",
            }
        ),
    ),
    FamilyContract(
        "cfile_input",
        "cfile_input.py",
        "file-input.md",
        frozenset(
            {
                "data-disabled",
                "data-dragging",
                "data-has-files",
                "data-invalid",
                "data-required",
                "data-size",
                "data-variant",
            }
        ),
    ),
    FamilyContract(
        "cbadge",
        "cbadge.py",
        "badge.md",
        frozenset({"data-intent", "data-shape", "data-size", "data-variant"}),
    ),
    FamilyContract(
        "cprogress",
        "cprogress.py",
        "progress.md",
        frozenset(
            {
                "aria-label",
                "aria-valuetext",
                "data-intent",
                "data-shape",
                "data-size",
                "data-state",
                "max",
                "value",
            }
        ),
    ),
    FamilyContract(
        "cspinner",
        "cspinner.py",
        "spinner.md",
        frozenset({"aria-label", "data-intent", "data-size", "role"}),
    ),
    FamilyContract(
        "cradio",
        "cradio.py",
        "radio.md",
        frozenset(
            {
                "aria-invalid",
                "checked",
                "data-checked",
                "data-disabled",
                "data-invalid",
                "data-label-pos",
                "data-orientation",
                "data-required",
                "data-size",
                "data-value",
                "data-variant",
                "disabled",
                "name",
                "value",
            }
        ),
    ),
    FamilyContract(
        "cswitch",
        "cswitch.py",
        "switch.md",
        frozenset(
            {
                "checked",
                "data-checked",
                "data-disabled",
                "data-invalid",
                "data-label-pos",
                "data-required",
                "data-size",
                "disabled",
                "required",
                "role",
            }
        ),
    ),
    FamilyContract(
        "cbutton",
        "cbutton.py",
        "button.md",
        frozenset(
            {
                "data-loading",
                "data-disabled",
                "data-variant",
                "data-intent",
                "data-size",
                "data-block",
                "data-loading-position",
            }
        ),
        frozenset({"split-button-primary-end", "split-button-primary-start"}),
    ),
    FamilyContract(
        "cfield",
        "cfield.py",
        "field-input.md",
        frozenset(
            {
                "data-required",
                "data-disabled",
                "data-readonly",
                "data-invalid",
                "data-orientation",
                "data-density",
                "data-variant",
                "data-size",
            }
        ),
    ),
    FamilyContract(
        "cform",
        "cform.py",
        "form.md",
        frozenset(
            {
                "data-disabled",
                "data-readonly",
                "data-submitting",
                "data-validation-attempted",
            }
        ),
    ),
    FamilyContract(
        "cdialog",
        "cdialog.py",
        "dialog.md",
        frozenset({"data-open", "data-size", "data-scroll"}),
    ),
    FamilyContract(
        "cdrawer",
        "cdrawer.py",
        "drawer.md",
        frozenset({"data-open", "data-placement", "data-size", "data-scroll"}),
    ),
    FamilyContract(
        "cpopover",
        "cpopover.py",
        "popover.md",
        frozenset(
            {
                "aria-controls",
                "aria-describedby",
                "aria-expanded",
                "aria-haspopup",
                "aria-labelledby",
                "data-match-width",
                "data-open",
                "data-placement",
                "popover",
                "role",
            }
        ),
    ),
    FamilyContract(
        "ctooltip",
        "ctooltip.py",
        "tooltip.md",
        frozenset(
            {
                "aria-describedby",
                "data-open",
                "data-placement",
                "popover",
                "role",
            }
        ),
    ),
    FamilyContract(
        "cavatar",
        "cavatar.py",
        "avatar.md",
        frozenset(
            {
                "aria-label",
                "data-shape",
                "data-size",
                "data-status",
                "data-variant",
                "role",
            }
        ),
    ),
    FamilyContract(
        "cimage",
        "cimage.py",
        "image.md",
        frozenset(
            {
                "alt",
                "aria-hidden",
                "crossorigin",
                "data-citry-image-initialized",
                "data-fit",
                "data-has-fallback",
                "data-has-placeholder",
                "data-status",
                "decoding",
                "draggable",
                "fetchpriority",
                "height",
                "hidden",
                "inert",
                "loading",
                "media",
                "referrerpolicy",
                "sizes",
                "src",
                "srcset",
                "type",
                "width",
            }
        ),
        theme_variables=frozenset(
            {
                "--cui-color-muted-bg",
                "--cui-color-muted-fg",
                "--cui-radius-md",
            }
        ),
    ),
    FamilyContract(
        "cskeleton",
        "cskeleton.py",
        "skeleton.md",
        frozenset({"aria-hidden", "data-animation", "data-kind"}),
    ),
    FamilyContract(
        "cdivider",
        "cdivider.py",
        "divider.md",
        frozenset(
            {
                "aria-hidden",
                "aria-orientation",
                "data-decorative",
                "data-inset",
                "data-label-pos",
                "data-labeled",
                "data-orientation",
                "data-size",
                "data-variant",
            }
        ),
    ),
    FamilyContract(
        "ccombobox",
        "ccombobox.py",
        "combobox.md",
        frozenset(
            {
                "data-open",
                "data-loading",
                "data-empty",
                "data-error",
                "data-required",
                "data-disabled",
                "data-readonly",
                "data-invalid",
                "data-variant",
                "data-size",
                "data-value",
                "data-selected",
                "data-highlighted",
            }
        ),
    ),
    FamilyContract(
        "ccommand_palette",
        "ccommand_palette.py",
        "command-palette.md",
        frozenset(
            {
                "aria-activedescendant",
                "aria-autocomplete",
                "aria-controls",
                "aria-disabled",
                "aria-expanded",
                "aria-labelledby",
                "aria-selected",
                "data-active",
                "data-disabled",
                "data-empty",
                "data-intent",
                "data-open",
                "data-size",
                "disabled",
                "id",
                "open",
                "role",
                "type",
            }
        ),
    ),
    FamilyContract(
        "ctable",
        "ctable.py",
        "table.md",
        frozenset(
            {
                "data-state",
                "data-variant",
                "data-density",
                "data-striped",
                "data-hover",
                "data-sticky-header",
                "data-column-borders",
                "data-layout",
                "data-overflow",
                "data-caption-side",
                "data-row-key",
                "data-column-key",
                "data-align",
            }
        ),
    ),
    FamilyContract(
        "cicon",
        "cicon.py",
        "icon.md",
        frozenset({"data-name", "data-size"}),
    ),
    FamilyContract(
        "ctextarea",
        "ctextarea.py",
        "textarea.md",
        frozenset(
            {
                "data-required",
                "data-disabled",
                "data-readonly",
                "data-invalid",
                "data-variant",
                "data-size",
                "data-resize",
            }
        ),
    ),
    FamilyContract(
        "cnative_select",
        "cnative_select.py",
        "native-select.md",
        frozenset(
            {
                "data-required",
                "data-disabled",
                "data-invalid",
                "data-empty",
                "data-variant",
                "data-size",
            }
        ),
    ),
    FamilyContract(
        "ccheckbox",
        "ccheckbox.py",
        "checkbox.md",
        frozenset(
            {
                "data-checked",
                "data-indeterminate",
                "data-required",
                "data-disabled",
                "data-invalid",
                "data-variant",
                "data-size",
                "data-label-pos",
            }
        ),
    ),
    FamilyContract(
        "cbutton_group",
        "cbutton_group.py",
        "button-group.md",
        frozenset({"data-attached", "data-grow", "data-orientation"}),
    ),
    FamilyContract(
        "ctoggle",
        "ctoggle.py",
        "toggle.md",
        frozenset(
            {
                "aria-pressed",
                "data-disabled",
                "data-grow",
                "data-mandatory",
                "data-multiple",
                "data-orientation",
                "data-pressed",
                "data-size",
                "data-value",
                "data-variant",
            }
        ),
    ),
    FamilyContract(
        "ctag",
        "ctag.py",
        "tag.md",
        frozenset(
            {
                "aria-disabled",
                "aria-selected",
                "data-actionable",
                "data-disabled",
                "data-removable",
                "data-selected",
                "data-selection-mode",
                "data-size",
                "data-value",
                "data-variant",
            }
        ),
    ),
    FamilyContract(
        "ctoolbar",
        "ctoolbar.py",
        "toolbar.md",
        frozenset(
            {
                "aria-label",
                "aria-orientation",
                "data-loop",
                "data-orientation",
                "data-size",
                "data-variant",
                "role",
                "tabindex",
            }
        ),
    ),
    FamilyContract(
        "ctree",
        "ctree.py",
        "tree.md",
        frozenset(
            {
                "aria-disabled",
                "aria-expanded",
                "aria-label",
                "aria-selected",
                "data-disabled",
                "data-expanded",
                "data-level",
                "data-selected",
                "data-selection-mode",
                "data-size",
                "data-value",
                "data-variant",
                "hidden",
                "inert",
                "role",
                "tabindex",
            }
        ),
    ),
    FamilyContract(
        "csplitter",
        "csplitter.py",
        "splitter.md",
        frozenset(
            {
                "aria-controls",
                "aria-disabled",
                "aria-label",
                "aria-orientation",
                "aria-valuemax",
                "aria-valuemin",
                "aria-valuenow",
                "data-active",
                "data-disabled",
                "data-handle-index",
                "data-index",
                "data-max-size",
                "data-min-size",
                "data-orientation",
                "data-panel-id",
                "data-resizing",
                "data-size",
                "data-size-percent",
                "data-variant",
                "role",
                "tabindex",
            }
        ),
    ),
    FamilyContract(
        "cstepper",
        "cstepper.py",
        "stepper.md",
        frozenset(
            {
                "aria-current",
                "aria-label",
                "data-active",
                "data-disabled",
                "data-error",
                "data-index",
                "data-interactive",
                "data-linear",
                "data-optional",
                "data-orientation",
                "data-size",
                "data-state",
                "data-variant",
            }
        ),
    ),
    FamilyContract(
        "cpagination",
        "cpagination.py",
        "pagination.md",
        frozenset(
            {
                "aria-current",
                "data-current",
                "data-disabled",
                "data-kind",
                "data-page",
                "data-size",
                "data-variant",
            }
        ),
    ),
    FamilyContract(
        "clist",
        "clist.py",
        "list.md",
        frozenset(
            {
                "aria-current",
                "data-current",
                "data-density",
                "data-disabled",
                "data-divided",
                "data-interactive",
                "data-marker",
                "data-variant",
            }
        ),
    ),
    FamilyContract(
        "clistbox",
        "clistbox.py",
        "listbox.md",
        frozenset(
            {
                "aria-disabled",
                "aria-labelledby",
                "aria-multiselectable",
                "aria-selected",
                "data-active",
                "data-disabled",
                "data-mandatory",
                "data-multiple",
                "data-selected",
                "data-size",
                "data-value",
                "data-variant",
                "role",
                "tabindex",
            }
        ),
    ),
    FamilyContract(
        "cselect",
        "cselect.py",
        "select.md",
        frozenset(
            {
                "aria-activedescendant",
                "aria-controls",
                "aria-disabled",
                "aria-expanded",
                "aria-invalid",
                "aria-readonly",
                "aria-required",
                "aria-selected",
                "data-disabled",
                "data-empty",
                "data-highlighted",
                "data-invalid",
                "data-match-width",
                "data-open",
                "data-placement",
                "data-readonly",
                "data-required",
                "data-selected",
                "data-size",
                "data-value",
                "data-variant",
                "role",
            }
        ),
    ),
    FamilyContract(
        "cmulti_select",
        "cmulti_select.py",
        "multi-select.md",
        frozenset(
            {
                "aria-activedescendant",
                "aria-controls",
                "aria-disabled",
                "aria-expanded",
                "aria-invalid",
                "aria-multiselectable",
                "aria-readonly",
                "aria-required",
                "aria-selected",
                "data-close-on-select",
                "data-disabled",
                "data-empty",
                "data-highlighted",
                "data-invalid",
                "data-match-width",
                "data-open",
                "data-placement",
                "data-readonly",
                "data-required",
                "data-selected",
                "data-size",
                "data-value",
                "data-variant",
                "role",
            }
        ),
    ),
    FamilyContract(
        "ctags_input",
        "ctags_input.py",
        "tags-input.md",
        frozenset(
            {
                "aria-atomic",
                "aria-describedby",
                "aria-hidden",
                "aria-invalid",
                "aria-label",
                "aria-labelledby",
                "aria-live",
                "aria-required",
                "data-at-max",
                "data-disabled",
                "data-empty",
                "data-focused",
                "data-highlighted",
                "data-invalid",
                "data-readonly",
                "data-required",
                "data-size",
                "data-variant",
                "disabled",
                "form",
                "id",
                "multiple",
                "name",
                "readonly",
                "required",
                "role",
                "tabindex",
                "type",
            }
        ),
    ),
    FamilyContract(
        "ceditable",
        "ceditable.py",
        "editable.md",
        frozenset(
            {
                "aria-describedby",
                "aria-errormessage",
                "aria-invalid",
                "data-action-position",
                "data-disabled",
                "data-editing",
                "data-empty",
                "data-invalid",
                "data-readonly",
                "data-required",
                "data-size",
                "data-submit-mode",
                "data-variant",
            }
        ),
    ),
    FamilyContract(
        "chover_card",
        "chover_card.py",
        "hover-card.md",
        frozenset(
            {
                "aria-hidden",
                "data-arrow",
                "data-open",
                "data-placement",
                "data-side",
                "data-size",
                "popover",
            }
        ),
    ),
    FamilyContract(
        "ccarousel",
        "ccarousel.py",
        "carousel.md",
        frozenset(
            {
                "aria-current",
                "aria-label",
                "aria-roledescription",
                "data-active",
                "data-disabled",
                "data-draggable",
                "data-index",
                "data-loop",
                "data-orientation",
                "data-size",
                "data-value",
                "data-variant",
                "disabled",
                "role",
                "tabindex",
            }
        ),
    ),
    FamilyContract(
        "cnavigation_menu",
        "cnavigation_menu.py",
        "navigation-menu.md",
        frozenset(
            {
                "aria-controls",
                "aria-current",
                "aria-expanded",
                "aria-label",
                "data-disabled",
                "data-loop",
                "data-open",
                "data-orientation",
                "data-size",
                "data-value",
                "data-variant",
                "disabled",
                "hidden",
                "inert",
            }
        ),
    ),
    FamilyContract(
        "cmenu",
        "cmenu.py",
        "menu.md",
        frozenset(
            {
                "aria-checked",
                "aria-controls",
                "aria-describedby",
                "aria-disabled",
                "aria-expanded",
                "aria-haspopup",
                "aria-labelledby",
                "data-checked",
                "data-disabled",
                "data-intent",
                "data-match-width",
                "data-open",
                "data-placement",
                "data-size",
                "popover",
                "role",
            }
        ),
    ),
    FamilyContract(
        "ctoast",
        "ctoast.py",
        "toast.md",
        frozenset(
            {
                "data-intent",
                "data-paused",
                "data-placement",
                "data-priority",
            }
        ),
    ),
)


def _family_sources(family: FamilyContract) -> tuple[str, str, str]:
    package = COMPONENT_ROOT / family.package
    return (
        (package / family.module).read_text(encoding="utf-8"),
        (package / "api.md").read_text(encoding="utf-8"),
        (SPEC_ROOT / family.spec).read_text(encoding="utf-8"),
    )


def _documented_api_surface(family: FamilyContract) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    path = COMPONENT_ROOT / family.package / "api.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    variables = frozenset(entry["name"] for table in data["css"] for entry in table["entries"])
    attributes = frozenset(entry["name"] for table in data["attributes"] for entry in table["entries"])
    parts: set[str] = set()
    for table in data["selectors"]:
        for entry in table["entries"]:
            match = re.fullmatch(r'\[data-citry-ui-part="([a-z0-9-]+)"\]', entry["selector"])
            if match is not None:
                parts.add(match.group(1))
    return variables, attributes, frozenset(parts)


def test_every_public_component_reference_exposes_direct_class_and_style_inputs():
    for path in sorted(COMPONENT_ROOT.glob("c*/api.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        server_inputs = {
            table["component"]: {entry["name"] for entry in table["entries"]}
            for table in data["inputs"]
            if table["channel"] == "server"
        }

        assert set(server_inputs) == set(data["components"])
        for component, names in server_inputs.items():
            assert {"class_", "style"} <= names, f"{path.name} omits root styling inputs for {component}"


def test_checkbox_reference_preserves_the_native_on_token_as_a_string():
    path = COMPONENT_ROOT / "ccheckbox" / "api.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    server_inputs = next(
        table for table in data["inputs"] if table["component"] == "CCheckbox" and table["channel"] == "server"
    )
    value_input = next(entry for entry in server_inputs["entries"] if entry["name"] == "value")

    assert value_input["default"]["value"] == "on"
    assert type(value_input["default"]["value"]) is str


def test_tags_input_reference_preserves_exact_structured_detail_fields():
    path = COMPONENT_ROOT / "ctags_input" / "api.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    records = {
        table["name"]: tuple(entry["name"] for entry in table["entries"])
        for table in data["interfaces"]
        if table["kind"] == "record"
    }

    assert data["components"] == ["CTagsInput"]
    assert data["slots"] == []
    assert data["methods"] == []
    assert records == {
        "CTagsInputMessages": (
            "remove_label",
            "added_message",
            "removed_message",
            "selected_message",
            "duplicate_message",
            "maximum_message",
            "empty_message",
            "invalid_message",
            "uncommitted_message",
        ),
        "CTagsInputValueChangeDetail": (
            "source",
            "added",
            "removed",
            "candidates",
            "previousValue",
            "nextInputValue",
            "controlled",
        ),
        "CTagsInputInputValueChangeDetail": (
            "source",
            "previousValue",
            "nextValue",
            "controlled",
            "composing",
        ),
        "CTagsInputInvalidDetail": (
            "source",
            "candidate",
            "candidates",
            "value",
            "inputValue",
            "maxTags",
            "controlled",
        ),
    }


def test_scroll_area_reference_preserves_the_exact_structured_contract():
    path = COMPONENT_ROOT / "cscroll_area" / "api.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    inputs = {table["channel"]: tuple(entry["name"] for entry in table["entries"]) for table in data["inputs"]}
    aliases = tuple(
        entry["name"] for table in data["interfaces"] if table["kind"] == "aliases" for entry in table["entries"]
    )
    records = {
        table["name"]: tuple(entry["name"] for entry in table["entries"])
        for table in data["interfaces"]
        if table["kind"] == "record"
    }

    assert data["components"] == ["CScrollArea"]
    assert inputs == {
        "server": (
            "id",
            "aria_label",
            "aria_labelledby",
            "axis",
            "scrollbar_width",
            "scrollbar_gutter",
            "overscroll",
            "class_",
            "style",
            "attrs",
        ),
        "client": (
            "axis",
            "scrollbarWidth",
            "scrollbarGutter",
            "overscroll",
            "onScrollChange",
        ),
    }
    assert [entry["name"] for table in data["slots"] for entry in table["entries"]] == ["default"]
    assert [entry["name"] for table in data["events"] for entry in table["entries"]] == ["onScrollChange"]
    assert data["methods"] == []
    assert [entry["name"] for table in data["css"] for entry in table["entries"]] == [
        "--cui-scroll-area-max-block-size",
        "--cui-scroll-area-background",
        "--cui-scroll-area-foreground",
        "--cui-scroll-area-border-color",
        "--cui-scroll-area-border-width",
        "--cui-scroll-area-radius",
        "--cui-scroll-area-padding",
        "--cui-scroll-area-scrollbar-color",
        "--cui-scroll-area-focus-color",
        "--cui-scroll-area-scroll-padding",
    ]
    assert [entry["name"] for table in data["attributes"] for entry in table["entries"]] == [
        "id",
        "tabindex",
        "role",
        "aria-label",
        "aria-labelledby",
        "data-axis",
        "data-scrollbar-width",
        "data-scrollbar-gutter",
        "data-overscroll",
    ]
    assert [entry["selector"] for table in data["selectors"] for entry in table["entries"]] == [
        '[data-citry-ui-part="scroll-area"]'
    ]
    assert aliases == (
        "CClassValue",
        "CStyleValue",
        "CScrollAreaAxis",
        "CScrollAreaScrollbarWidth",
        "CScrollAreaScrollbarGutter",
        "CScrollAreaOverscroll",
    )
    assert records == {
        "CScrollAreaScrollDetail": (
            "inlineOffset",
            "blockOffset",
            "source",
        ),
    }


def test_image_reference_preserves_the_exact_structured_contract():
    path = COMPONENT_ROOT / "cimage" / "api.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    inputs = {table["channel"]: tuple(entry["name"] for entry in table["entries"]) for table in data["inputs"]}
    aliases = tuple(
        entry["name"] for table in data["interfaces"] if table["kind"] == "aliases" for entry in table["entries"]
    )
    records = {
        table["name"]: tuple(entry["name"] for entry in table["entries"])
        for table in data["interfaces"]
        if table["kind"] == "record"
    }

    assert data["components"] == ["CImage"]
    assert inputs == {
        "server": (
            "src",
            "alt",
            "width",
            "height",
            "srcset",
            "sizes",
            "sources",
            "loading",
            "decoding",
            "fetch_priority",
            "cross_origin",
            "referrer_policy",
            "fit",
            "position",
            "draggable",
            "onStatusChange",
            "class_",
            "style",
            "attrs",
            "img_attrs",
        ),
        "client": (
            "src",
            "alt",
            "width",
            "height",
            "srcset",
            "sizes",
            "loading",
            "decoding",
            "fetchPriority",
            "crossOrigin",
            "referrerPolicy",
            "fit",
            "position",
            "draggable",
            "onStatusChange",
        ),
    }
    assert [entry["name"] for table in data["slots"] for entry in table["entries"]] == [
        "placeholder",
        "fallback",
    ]
    assert [entry["name"] for table in data["events"] for entry in table["entries"]] == ["onStatusChange"]
    assert data["methods"] == []
    assert [entry["name"] for table in data["css"] for entry in table["entries"]] == [
        "--cui-image-aspect-ratio",
        "--cui-image-fit",
        "--cui-image-position",
        "--cui-image-radius",
        "--cui-image-background",
        "--cui-image-fallback-color",
        "--cui-image-fallback-background",
    ]
    assert [entry["selector"] for table in data["selectors"] for entry in table["entries"]] == [
        '[data-citry-ui-part="image-root"]',
        '[data-citry-ui-part="picture"]',
        '[data-citry-ui-part="image"]',
        '[data-citry-ui-part="placeholder"]',
        '[data-citry-ui-part="fallback"]',
    ]
    assert aliases == (
        "CClassValue",
        "CStyleValue",
        "CImageFit",
        "CImageLoading",
        "CImageDecoding",
        "CImageFetchPriority",
        "CImageCrossOrigin",
        "CImageReferrerPolicy",
        "CImageStatus",
    )
    assert records == {
        "CImageSource": (
            "srcset",
            "media",
            "type",
            "sizes",
            "width",
            "height",
        ),
        "CImageStatusChangeDetail": (
            "status",
            "src",
            "current_src",
            "natural_width",
            "natural_height",
        ),
    }


def test_command_palette_reference_preserves_the_exact_structured_contract():
    path = COMPONENT_ROOT / "ccommand_palette" / "api.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    inputs = {table["channel"]: tuple(entry["name"] for entry in table["entries"]) for table in data["inputs"]}
    aliases = tuple(
        entry["name"] for table in data["interfaces"] if table["kind"] == "aliases" for entry in table["entries"]
    )
    records = {
        table["name"]: tuple(entry["name"] for entry in table["entries"])
        for table in data["interfaces"]
        if table["kind"] == "record"
    }

    assert data["components"] == ["CCommandPalette"]
    assert inputs == {
        "server": (
            "entries",
            "label",
            "id",
            "open",
            "query",
            "disabled",
            "loop",
            "close_on_action",
            "size",
            "placeholder",
            "search_label",
            "empty_label",
            "close_label",
            "class_",
            "style",
            "attrs",
            "input_attrs",
        ),
        "client": (
            "open",
            "query",
            "disabled",
            "loop",
            "closeOnAction",
            "size",
            "onOpenChange",
            "onQueryChange",
            "onAction",
        ),
    }
    assert [entry["name"] for table in data["slots"] for entry in table["entries"]] == [
        "activator",
        "item_start",
        "item_end",
        "empty",
    ]
    assert [entry["name"] for table in data["events"] for entry in table["entries"]] == [
        "onOpenChange",
        "onQueryChange",
        "onAction",
    ]
    assert data["methods"] == []
    assert aliases == (
        "CClassValue",
        "CStyleValue",
        "CCommandPaletteEntry",
        "CCommandPaletteIntent",
        "CCommandPaletteSize",
        "CCommandPaletteActionSource",
        "CCommandPaletteOpenReason",
        "CCommandPaletteQueryReason",
    )
    assert records == {
        "CCommandPaletteCommand": (
            "value",
            "label",
            "description",
            "keywords",
            "shortcut",
            "disabled",
            "close_on_action",
            "intent",
        ),
        "CCommandPaletteGroup": ("label", "commands"),
        "CCommandPaletteSeparator": (),
        "CCommandPaletteItemSlotData": (
            "value",
            "label",
            "description",
            "keywords",
            "shortcut",
            "disabled",
            "close_on_action",
            "intent",
        ),
        "CCommandPaletteOpenChangeDetail": ("reason", "controlled", "source"),
        "CCommandPaletteQueryChangeDetail": ("reason", "closeReason", "controlled", "source"),
        "CCommandPaletteActionDetail": ("query", "source", "item", "event", "closeOnAction"),
    }


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.package)
def test_production_spec_uses_the_complete_authoring_template(family: FamilyContract):
    _, _, spec = _family_sources(family)
    headings = tuple(line for line in spec.splitlines() if line.startswith("## "))

    assert headings == SPEC_HEADINGS


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.package)
def test_runtime_public_css_contract_is_documented_in_spec_and_api(family: FamilyContract):
    source, _, spec = _family_sources(family)
    parts = frozenset(re.findall(r'data-citry-ui-part=["\']([a-z0-9-]+)', source))
    variables = frozenset(re.findall(r"(?<!_)--cui-[a-z0-9-]+", source))
    documented_variables, documented_attributes, documented_parts = _documented_api_surface(family)

    assert parts
    assert variables
    assert documented_parts.isdisjoint(family.shared_parts)
    assert documented_variables.isdisjoint(family.theme_variables)
    assert documented_parts | family.shared_parts == parts
    assert documented_variables | family.theme_variables == variables
    assert documented_attributes == family.reflected_attributes
    for public_name in (*sorted(documented_parts), *sorted(variables), *sorted(family.reflected_attributes)):
        assert public_name in spec, f"{family.spec} omits {public_name}"


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.package)
def test_public_variables_resolve_through_private_effective_variables(family: FamilyContract):
    source, _, _ = _family_sources(family)
    variables = frozenset(re.findall(r"(?<!_)--cui-[a-z0-9-]+", source))

    for public_name in variables - family.theme_variables:
        private_name = public_name.replace("--cui-", "--_cui-", 1)
        resolution = re.compile(
            rf"{re.escape(private_name)}\s*:\s*var\(\s*{re.escape(public_name)}\s*,",
            re.MULTILINE,
        )
        assert resolution.search(source), f"{public_name} is not resolved by {private_name}"


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.package)
def test_owned_part_marker_follows_consumer_attribute_spread(family: FamilyContract):
    source, _, _ = _family_sources(family)
    tags = re.findall(r"<[a-zA-Z][^>]*>", source, flags=re.DOTALL)
    bound_parts = [tag for tag in tags if "c-bind=" in tag and "data-citry-ui-part=" in tag]

    assert bound_parts
    for tag in bound_parts:
        assert tag.index("c-bind=") < tag.index("data-citry-ui-part=")


def test_split_button_public_contract_composes_shared_button_and_menu_assets():
    split_source = (COMPONENT_ROOT / "csplitbutton/csplitbutton.py").read_text(encoding="utf-8")
    button_source = (COMPONENT_ROOT / "cbutton/cbutton.py").read_text(encoding="utf-8")
    menu_source = (COMPONENT_ROOT / "cmenu/cmenu.py").read_text(encoding="utf-8")
    spec = (SPEC_ROOT / "split-button.md").read_text(encoding="utf-8")
    headings = tuple(line for line in spec.splitlines() if line.startswith("## "))
    reference = yaml.safe_load((COMPONENT_ROOT / "csplitbutton/api.yml").read_text(encoding="utf-8"))

    documented_variables = frozenset(entry["name"] for table in reference["css"] for entry in table["entries"])
    documented_attributes = frozenset(entry["name"] for table in reference["attributes"] for entry in table["entries"])
    documented_parts = frozenset(
        match.group(1)
        for table in reference["selectors"]
        for entry in table["entries"]
        if (match := re.fullmatch(r'\[data-citry-ui-part="([a-z0-9-]+)"\]', entry["selector"])) is not None
    )
    split_parts = frozenset(re.findall(r'data-citry-ui-part=["\']([a-z0-9-]+)', split_source))
    menu_parts = frozenset(re.findall(r'data-citry-ui-part=["\']([a-z0-9-]+)', menu_source))
    effective_source = f"{split_source}\n{button_source}\n{menu_source}"
    effective_variables = frozenset(re.findall(r"(?<!_)--cui-[a-z0-9-]+", effective_source))

    assert headings == SPEC_HEADINGS
    assert documented_parts == split_parts | menu_parts
    assert documented_variables == effective_variables
    assert documented_attributes == {
        "aria-busy",
        "aria-checked",
        "aria-controls",
        "aria-describedby",
        "aria-disabled",
        "aria-expanded",
        "aria-haspopup",
        "aria-label",
        "aria-labelledby",
        "data-block",
        "data-checked",
        "data-disabled",
        "data-intent",
        "data-loading",
        "data-loading-position",
        "data-match-width",
        "data-menu-disabled",
        "data-open",
        "data-placement",
        "data-primary-disabled",
        "data-size",
        "data-variant",
        "disabled",
        "id",
        "popover",
        "role",
        "type",
    }
    assert "build_shared_component_assets" not in split_source
    for public_name in documented_variables:
        private_name = public_name.replace("--cui-", "--_cui-", 1)
        resolution = re.compile(
            rf"{re.escape(private_name)}\s*:\s*var\(\s*{re.escape(public_name)}\s*,",
            re.MULTILINE,
        )
        assert resolution.search(effective_source), f"{public_name} is not resolved by {private_name}"
    for public_name in (*sorted(documented_parts), *sorted(documented_variables), *sorted(documented_attributes)):
        assert public_name in spec, f"split-button.md omits {public_name}"


def test_context_menu_public_contract_reuses_the_existing_menu_surface():
    context_source = (COMPONENT_ROOT / "ccontext_menu/ccontext_menu.py").read_text(encoding="utf-8")
    menu_source = (COMPONENT_ROOT / "cmenu/cmenu.py").read_text(encoding="utf-8")
    spec = (SPEC_ROOT / "context-menu.md").read_text(encoding="utf-8")
    reference = yaml.safe_load((COMPONENT_ROOT / "ccontext_menu/api.yml").read_text(encoding="utf-8"))
    headings = tuple(line for line in spec.splitlines() if line.startswith("## "))
    inputs = {table["channel"]: tuple(entry["name"] for entry in table["entries"]) for table in reference["inputs"]}
    records = {
        table["name"]: tuple(entry["name"] for entry in table["entries"])
        for table in reference["interfaces"]
        if table["kind"] == "record"
    }
    documented_variables = frozenset(entry["name"] for table in reference["css"] for entry in table["entries"])
    documented_attributes = frozenset(entry["name"] for table in reference["attributes"] for entry in table["entries"])
    documented_parts = frozenset(
        match.group(1)
        for table in reference["selectors"]
        for entry in table["entries"]
        if (match := re.fullmatch(r'\[data-citry-ui-part="([a-z0-9-]+)"\]', entry["selector"])) is not None
    )
    context_parts = frozenset(re.findall(r'data-citry-ui-part=["\']([a-z0-9-]+)', context_source))
    menu_parts = frozenset(re.findall(r'data-citry-ui-part=["\']([a-z0-9-]+)', menu_source))
    menu_variables = frozenset(re.findall(r"(?<!_)--cui-menu-[a-z0-9-]+", menu_source))

    assert headings == SPEC_HEADINGS
    assert reference["components"] == ["CContextMenu"]
    assert inputs == {
        "server": (
            "id",
            "aria_label",
            "open",
            "disabled",
            "loop",
            "close_on_select",
            "size",
            "class_",
            "style",
            "attrs",
            "target_attrs",
        ),
        "client": (
            "open",
            "disabled",
            "loop",
            "closeOnSelect",
            "size",
            "onOpenChange",
            "onAction",
        ),
    }
    assert [entry["name"] for table in reference["slots"] for entry in table["entries"]] == [
        "target",
        "menu",
    ]
    assert [entry["name"] for table in reference["events"] for entry in table["entries"]] == [
        "onOpenChange",
        "onAction",
    ]
    assert reference["methods"] == []
    assert documented_variables == menu_variables
    assert documented_parts == context_parts | menu_parts
    assert documented_attributes == {
        "aria-checked",
        "aria-controls",
        "aria-describedby",
        "aria-disabled",
        "aria-expanded",
        "aria-haspopup",
        "aria-label",
        "aria-labelledby",
        "data-checked",
        "data-citry-context-menu-native",
        "data-disabled",
        "data-intent",
        "data-invocation",
        "data-open",
        "data-placement",
        "data-size",
        "id",
        "popover",
        "role",
    }
    assert records == {
        "CContextMenuTargetSlotData": ("target_attrs",),
        "CContextMenuMenuSlotData": (),
        "CContextMenuOpenChangeDetail": (
            "reason",
            "controlled",
            "forced",
            "source",
            "clientX",
            "clientY",
        ),
        "CMenuActionDetail": ("kind", "item", "event", "path"),
    }
    assert "<c-CInternalMenuSurface" in context_source
    assert "<c-CMenu" not in context_source
    for public_name in documented_variables:
        private_name = public_name.replace("--cui-", "--_cui-", 1)
        resolution = re.compile(
            rf"{re.escape(private_name)}\s*:\s*var\(\s*{re.escape(public_name)}\s*,",
            re.MULTILINE,
        )
        assert resolution.search(menu_source), f"{public_name} is not resolved by {private_name}"
    # ContextMenu inherits Menu's already-guarded public parts, variables, and
    # item attributes by reference. Only its own additions must be repeated in
    # this family spec.
    for public_name in (
        *sorted(context_parts),
        "data-citry-context-menu-native",
        "data-invocation",
    ):
        assert public_name in spec, f"context-menu.md omits {public_name}"
