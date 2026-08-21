import json
import re

from citry_ui.quality.routes import render_scenario
from citry_ui.quality.scenarios import SCENARIOS, ScenarioStatus, manifest_json, scenario_by_id


def test_scenario_catalog_has_stable_unique_ordered_ids():
    ids = [scenario.id for scenario in SCENARIOS]

    assert ids == [
        "accordion.states",
        "disclosure.states",
        "alert.states",
        "button.states",
        "split-button.states",
        "avatar.states",
        "image.states",
        "badge.states",
        "divider.states",
        "field-input.states",
        "file-input.states",
        "progress.states",
        "spinner.states",
        "splitter.states",
        "stepper.states",
        "sidebar.states",
        "flow.states",
        "grid-container.states",
        "scroll-area.states",
        "radio.states",
        "skeleton.states",
        "switch.states",
        "breadcrumbs.states",
        "form.states",
        "textarea.states",
        "native-select.states",
        "checkbox.states",
        "tabs.overview",
        "dialog.states",
        "alert-dialog.states",
        "popover.states",
        "drawer.states",
        "tour.states",
        "tooltip.states",
        "hover-card.states",
        "menu.states",
        "context-menu.states",
        "navigation-menu.states",
        "carousel.states",
        "toast.states",
        "combobox.states",
        "command-palette.states",
        "table.states",
        "icon.states",
        "card.states",
        "button-group.states",
        "toggle.states",
        "pagination.states",
        "list.states",
        "data-grid.states",
        "timeline.states",
        "transfer-list.states",
        "virtual-list.states",
        "tag.states",
        "toolbar.states",
        "listbox.states",
        "select.states",
        "multi-select.states",
        "tags-input.states",
        "number-input.states",
        "slider.states",
        "rating.states",
        "pin-input.states",
        "date-input.states",
        "calendar.states",
        "date-picker.states",
        "date-range.states",
        "time.states",
        "editable.states",
        "tree.states",
        "workflow.repeatable-contacts",
        "composition.orbit-access",
        "composition.ledger-dashboard",
    ]
    assert len(ids) == len(set(ids))
    assert all(scenario.states for scenario in SCENARIOS)
    assert all(len(scenario.tools) == len(set(scenario.tools)) for scenario in SCENARIOS)


def test_ready_scenarios_are_explicit_and_standalone():
    ready = [scenario for scenario in SCENARIOS if scenario.status is ScenarioStatus.READY]

    assert [scenario.id for scenario in ready] == [scenario.id for scenario in SCENARIOS]
    assert all(scenario.standalone for scenario in ready)
    assert all(scenario.fixture for scenario in ready)
    assert all(scenario.expected_assets for scenario in ready)
    assert all(set(scenario.action_states) <= set(scenario.states) for scenario in ready)


def test_manifest_is_deterministic_and_round_trips():
    first = manifest_json()
    second = manifest_json()

    assert first == second
    value = json.loads(first)
    assert value["schema"] == "citry-ui-quality-scenarios/v1"
    assert value["scenarios"][0]["id"] == "accordion.states"
    assert scenario_by_id("tabs.overview").family == "tabs"


def test_catalog_maps_every_phase_7_5_family_state_to_a_scenario():
    required = {
        "accordion.states": {
            "controlled",
            "single",
            "multiple",
            "collapsible",
            "noncollapsible",
            "open",
            "closed",
            "disabled-item",
            "actions",
            "region",
            "outline",
            "soft",
            "separated",
            "plain",
            "sm",
            "md",
            "lg",
            "indicator-start",
            "indicator-end",
            "ltr",
            "rtl",
            "long-content",
            "nested",
            "nested-dark",
            "form-content",
            "brand-fern",
            "brand-river",
        },
        "disclosure.states": {
            "controlled",
            "open",
            "closed",
            "disabled-open",
            "disabled-closed",
            "actions",
            "region",
            "outline",
            "soft",
            "plain",
            "sm",
            "md",
            "lg",
            "indicator-start",
            "indicator-end",
            "indicator-hidden",
            "ltr",
            "rtl",
            "long-content",
            "nested",
            "nested-dark",
            "form-content",
            "brand-orchard",
            "brand-harbor",
        },
        "alert.states": {
            "controlled",
            "info",
            "success",
            "warn",
            "error",
            "soft",
            "solid",
            "outline",
            "sm",
            "md",
            "lg",
            "icon-auto",
            "icon-fixed",
            "icon-hidden",
            "announce-off",
            "announce-polite",
            "announce-assertive",
            "actions",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "avatar.states": {
            "fallback",
            "decorative",
            "named",
            "soft",
            "solid",
            "outline",
            "sm",
            "md",
            "lg",
            "circle",
            "rounded",
            "square",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "image.states": {
            "informative",
            "decorative",
            "empty-alt",
            "geometry",
            "responsive",
            "source-order",
            "candidate-switch",
            "placeholder",
            "fallback",
            "error",
            "reactive",
            "native-events",
            "cors",
            "referrer-policy",
            "csp",
            "csp-blocked",
            "functional-alt",
            "lifecycle",
            "retained-root",
            "replacement-root",
            "removal",
            "restore",
            "shadow-root",
            "hostile-fail-closed",
            "readiness",
        },
        "button.states": {
            "button",
            "submit",
            "reset",
            "link",
            "solid",
            "outline",
            "ghost",
            "neutral",
            "primary",
            "success",
            "warn",
            "danger",
            "sm",
            "md",
            "lg",
            "loading-start",
            "loading-center",
            "loading-end",
            "disabled",
            "start-slot",
            "end-slot",
        },
        "split-button.states": {
            "submit",
            "reset",
            "open-layer",
            "commands",
            "link",
            "choices",
            "group",
            "separator",
            "submenu",
            "danger",
            "controlled",
            "match-width",
            "loading",
            "primary-disabled",
            "menu-disabled",
            "fieldset-disabled",
            "brand-orchard",
            "brand-harbor",
            "rtl",
            "narrow",
            "long-content",
            "lifecycle",
            "removal",
            "restore",
            "morph-target",
        },
        "tags-input.states": {
            "required",
            "ordered",
            "form-data",
            "repeated-values",
            "draft",
            "unfinished-validity",
            "paste",
            "selection",
            "ime",
            "delimiter",
            "maximum",
            "controlled",
            "controlled-value",
            "controlled-draft",
            "refusal",
            "acceptance",
            "readonly",
            "dormant-draft",
            "hidden-transport",
            "disabled",
            "omitted-transport",
            "external-form",
            "fieldset-disabled",
            "invalid-focus",
            "lifecycle",
            "morph-target",
            "cleanup",
            "composition-node",
            "selection-preservation",
        },
        "scroll-area.states": {
            "block",
            "inline",
            "both",
            "named-region",
            "unnamed",
            "focus",
            "keyboard",
            "rtl",
            "logical-offset",
            "configuration",
            "controlled",
            "disabled-axis",
            "callback",
            "native-scroll",
            "native-scrollend",
            "nested",
            "contain",
            "print",
            "forced-colors",
            "lifecycle",
            "retained-root",
            "replacement-root",
            "morph-target",
            "cleanup",
        },
        "divider.states": {
            "semantic",
            "decorative",
            "horizontal",
            "vertical",
            "solid",
            "dashed",
            "dotted",
            "sm",
            "md",
            "lg",
            "label-start",
            "label-center",
            "label-end",
            "inset-none",
            "inset-start",
            "inset-end",
            "inset-both",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "skeleton.states": {
            "rect",
            "circle",
            "text",
            "multi-line",
            "pulse",
            "wave",
            "none",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "field-input.states": {
            "required",
            "disabled",
            "readonly",
            "invalid",
            "described",
            "controlled",
            "uncontrolled",
            "reset",
        },
        "form.states": {
            "native-valid",
            "native-invalid",
            "attempted",
            "disabled",
            "readonly",
            "submitting",
            "dynamic-membership",
            "external-control",
            "reset",
        },
        "textarea.states": {
            "controlled",
            "uncontrolled",
            "reset",
            "required",
            "disabled",
            "readonly",
            "invalid",
            "outline",
            "filled",
            "plain",
            "sm",
            "md",
            "lg",
            "hard-wrap",
            "both-resize",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "native-select.states": {
            "controlled",
            "uncontrolled",
            "reset",
            "placeholder",
            "required",
            "disabled",
            "invalid",
            "grouped",
            "disabled-option",
            "outline",
            "filled",
            "plain",
            "sm",
            "md",
            "lg",
            "ltr",
            "rtl",
            "long-label",
            "nested-dark",
        },
        "checkbox.states": {
            "controlled",
            "uncontrolled",
            "checked",
            "unchecked",
            "indeterminate",
            "reset",
            "required",
            "disabled",
            "invalid",
            "solid",
            "outline",
            "sm",
            "md",
            "lg",
            "label-start",
            "label-end",
            "description",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "tabs.overview": {
            "horizontal",
            "vertical",
            "automatic",
            "manual",
            "ltr",
            "rtl",
            "loop",
            "no-loop",
            "disabled-tab",
            "long-label",
            "nested",
            "controlled",
            "reordered",
            "removed",
        },
        "dialog.states": {
            "open",
            "closed",
            "controlled",
            "persistent",
            "nested",
            "long-content",
            "form",
            "removed-trigger",
            "removed-open",
        },
        "alert-dialog.states": {
            "closed",
            "open",
            "controlled",
            "cancel",
            "action",
            "escape",
            "outside-refusal",
            "supplemental-content",
            "sm",
            "lg",
            "brand",
        },
        "combobox.states": {
            "local",
            "remote",
            "open",
            "selected",
            "empty",
            "loading",
            "disabled",
            "readonly",
            "invalid",
        },
        "command-palette.states": {
            "open",
            "filter",
            "disabled",
            "controlled-open",
            "controlled-query",
            "action-once",
            "form",
            "ime",
            "nested-dialog",
            "open-shadow-root",
            "retained-equal",
            "changed-records",
            "replacement-root",
            "removal",
            "restore",
            "resource-cleanup",
        },
        "table.states": {
            "ready",
            "empty",
            "loading",
            "error",
            "compact",
            "striped",
            "hover",
            "sticky-header",
            "overflow",
            "large-output",
            "footer",
        },
        "icon.states": {
            "catalog",
            "decorative",
            "meaningful",
            "sm",
            "md",
            "lg",
            "current-color",
            "custom-size",
            "custom-stroke",
            "ltr",
            "rtl",
            "logical-direction",
        },
        "card.states": {
            "body-only",
            "header-only",
            "media",
            "header-actions",
            "footer",
            "footer-actions",
            "elevated",
            "outline",
            "subtle",
            "sm",
            "md",
            "lg",
            "long-content",
            "nested-card",
            "linen-brand",
            "studio-brand",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "button-group.states": {
            "attached",
            "spaced",
            "horizontal",
            "vertical",
            "mixed-buttons",
            "disabled-button",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "toggle.states": {
            "standalone",
            "pressed",
            "single",
            "multiple",
            "mandatory",
            "disabled-item",
            "horizontal",
            "vertical",
            "soft",
            "outline",
            "ltr",
            "rtl",
        },
        "pagination.states": {
            "link",
            "button",
            "large-range",
            "first-page",
            "last-page",
            "edges",
            "disabled",
            "soft",
            "outline",
            "plain",
            "sm",
            "md",
            "lg",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "list.states": {
            "unordered",
            "ordered",
            "navigation",
            "action",
            "current",
            "disabled-item",
            "start-slot",
            "description-slot",
            "end-slot",
            "comfortable",
            "compact",
            "plain",
            "surface",
            "divided",
            "ltr",
            "rtl",
            "nested-dark",
        },
        "popover.states": {
            "closed",
            "open",
            "controlled",
            "explicit-only",
            "nested",
            "form-content",
            "top",
            "bottom",
            "start",
            "end",
            "match-width",
            "brand-aurora",
            "brand-lunar",
        },
        "drawer.states": {
            "closed",
            "open",
            "dismissible",
            "persistent",
            "controlled",
            "form",
            "nested",
            "inline-start",
            "inline-end",
            "block-end",
            "sm",
            "md",
            "lg",
            "body",
            "drawer-scroll",
            "long-content",
            "rtl",
            "brand-aurora",
        },
        "tooltip.states": {
            "closed",
            "open",
            "controlled",
            "disabled",
            "text",
            "formatted",
            "top",
            "bottom",
            "start",
            "end",
            "long-content",
            "brand-aurora",
            "brand-lunar",
        },
        "menu.states": {
            "closed",
            "open",
            "commands",
            "links",
            "choices",
            "groups",
            "separator",
            "submenu",
            "two-level",
            "danger",
            "form-safe",
            "controlled",
            "loop-false",
            "match-width",
            "disabled",
            "fieldset-disabled",
            "sm",
            "md",
            "lg",
            "placement",
            "rtl",
            "brand-moon",
            "brand-ember",
        },
        "context-menu.states": {
            "pointer",
            "keyboard",
            "controlled",
            "claim",
            "accept",
            "refuse",
            "native",
            "selection",
            "editable",
            "link",
            "media",
            "custom-element",
            "closed-shadow-marker",
            "open-shadow",
            "iframe",
            "shift-secondary",
            "touch",
            "pen",
            "long-press",
            "derived-click",
            "submit",
            "nested",
            "deepest-boundary",
            "logical-layer",
            "point",
            "transform",
            "visual-viewport",
            "rtl",
            "lifecycle",
            "morph-target",
            "retained-root",
            "replacement-root",
            "removal",
            "restore",
            "cleanup",
            "focus",
            "disabled",
            "fieldset-disabled",
            "no-js",
            "server-open-fallback",
        },
        "toast.states": {
            "queue",
            "polite",
            "assertive",
            "neutral",
            "info",
            "success",
            "warn",
            "error",
            "action",
            "dismissal",
            "persistent",
            "timed",
            "visible-limit",
            "pause",
            "f6",
            "block-start-start",
            "block-end-end",
            "long-content",
            "rtl",
            "brand",
        },
    }

    for scenario_id, states in required.items():
        assert states <= set(scenario_by_id(scenario_id).states)


def test_drawer_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("drawer.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<dialog(?=[^>]*data-citry-ui-part="drawer")[^>]*data-quality-states="([^"]+)"',
        html,
    )

    assert state_groups
    assert set(scenario.states) <= {state for group in state_groups for state in group.split()}


def test_accordion_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("accordion.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<div(?=[^>]*data-citry-accordion-root)[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_disclosure_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("disclosure.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<div(?=[^>]*data-citry-ui-part="disclosure")[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_split_button_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("split-button.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<div(?=[^>]*data-citry-ui-part="split-button")[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_tags_input_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("tags-input.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<div(?=[^>]*data-citry-ui-part="tags-input")[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_image_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("image.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<span(?=[^>]*data-citry-ui-part="image-root")[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_scroll_area_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("scroll-area.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<div(?=[^>]*data-citry-ui-part="scroll-area")[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_menu_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("menu.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<div(?=[^>]*data-citry-menu-root)[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_context_menu_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("context-menu.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<div(?=[^>]*data-citry-ui-part="context-menu")[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_command_palette_fixture_marks_every_declared_state_on_a_component_root():
    scenario = scenario_by_id("command-palette.states")
    html = render_scenario(scenario.id)
    state_groups = re.findall(
        r'<dialog(?=[^>]*data-citry-ui-part="command-palette")[^>]*data-quality-states="([^"]+)"',
        html,
    )
    covered = {state for group in state_groups for state in group.split()}

    assert covered == set(scenario.states)


def test_toast_fixture_marks_every_declared_state_on_the_region() -> None:
    scenario = scenario_by_id("toast.states")
    html = render_scenario(scenario.id)
    [state_group] = re.findall(
        r'<section(?=[^>]*data-citry-ui-part="region")[^>]*data-quality-states="([^"]+)"',
        html,
    )

    assert set(state_group.split()) == set(scenario.states)
