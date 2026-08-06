"""Machine-readable catalog for bounded Citry UI quality scenarios."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from enum import StrEnum


class ScenarioStatus(StrEnum):
    """Whether tools may currently count a scenario as executable evidence."""

    READY = "ready"
    PLANNED = "planned"


class QualityTool(StrEnum):
    """A Phase 7.5 consumer of rendered scenarios."""

    AXE = "axe"
    BROWSER = "browser"
    CSS = "css-coexistence"
    DOCS = "docs"
    HTML = "nu-html"
    LIGHTHOUSE = "lighthouse"
    PERFORMANCE = "performance"
    SCREENSHOT = "screenshot"


@dataclass(frozen=True, slots=True)
class Scenario:
    """One stable scenario and the public states it deliberately exercises."""

    id: str
    family: str
    purpose: str
    states: tuple[str, ...]
    profiles: tuple[str, ...]
    tools: tuple[QualityTool, ...]
    expected_components: tuple[str, ...]
    expected_assets: tuple[str, ...]
    fixture: str
    action_states: tuple[str, ...]
    ready_selector: str
    standalone: bool
    status: ScenarioStatus

    def manifest_value(self) -> dict[str, object]:
        value = asdict(self)
        value["status"] = self.status.value
        value["tools"] = [tool.value for tool in self.tools]
        return value


SCENARIOS = (
    Scenario(
        id="button.states",
        family="button",
        purpose="Compare native actions and links, variants, intent, size, loading, disabled, and slot anatomy.",
        states=(
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
            "block",
            "loading-start",
            "loading-center",
            "loading-end",
            "disabled",
            "start-slot",
            "end-slot",
        ),
        profiles=("light", "dark", "keyboard", "forced-colors", "reduced-motion", "touch"),
        tools=(QualityTool.AXE, QualityTool.BROWSER, QualityTool.DOCS, QualityTool.HTML, QualityTool.SCREENSHOT),
        expected_components=("CButton",),
        expected_assets=("css", "js"),
        fixture="button_states_component",
        action_states=("submit", "reset", "loading-start"),
        ready_selector="[data-citry-button-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="field-input.states",
        family="field-input",
        purpose="Exercise native constraints, inherited form state, messages, resets, and controlled input state.",
        states=(
            "required",
            "disabled",
            "readonly",
            "invalid",
            "described",
            "controlled",
            "uncontrolled",
            "reset",
        ),
        profiles=("light", "dark", "keyboard", "narrow", "zoom-200", "zoom-400", "forced-colors"),
        tools=(QualityTool.AXE, QualityTool.BROWSER, QualityTool.DOCS, QualityTool.HTML, QualityTool.SCREENSHOT),
        expected_components=("CForm", "CField", "CInput"),
        expected_assets=("css", "js"),
        fixture="field_input_states_component",
        action_states=("controlled", "invalid", "reset"),
        ready_selector="[data-citry-input-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="form.states",
        family="form",
        purpose=(
            "Exercise native validity and submission, inherited state, dynamic membership, "
            "external ownership, and reset."
        ),
        states=(
            "native-valid",
            "native-invalid",
            "attempted",
            "disabled",
            "readonly",
            "submitting",
            "dynamic-membership",
            "external-control",
            "reset",
        ),
        profiles=("light", "dark", "keyboard", "reduced-motion"),
        tools=(QualityTool.AXE, QualityTool.BROWSER, QualityTool.DOCS, QualityTool.HTML),
        expected_components=("CForm", "CField", "CInput", "CButton"),
        expected_assets=("css", "js"),
        fixture="form_states_component",
        action_states=("attempted", "dynamic-membership", "reset", "submitting"),
        ready_selector="[data-citry-form-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="tabs.overview",
        family="tabs",
        purpose="Prove server selection, pointer and keyboard changes, a disabled tab, and callback delivery.",
        states=(
            "horizontal",
            "vertical",
            "automatic",
            "manual",
            "ltr",
            "rtl",
            "loop",
            "no-loop",
            "pill",
            "underline",
            "compact",
            "disabled-tab",
            "uncontrolled",
            "controlled",
            "callback",
            "keyboard-selection",
            "long-label",
            "nested",
            "reordered",
            "removed",
        ),
        profiles=(
            "light",
            "dark",
            "keyboard",
            "narrow",
            "rtl",
            "reduced-motion",
            "forced-colors",
            "zoom-200",
            "zoom-400",
            "touch",
        ),
        tools=(
            QualityTool.AXE,
            QualityTool.BROWSER,
            QualityTool.CSS,
            QualityTool.DOCS,
            QualityTool.HTML,
            QualityTool.LIGHTHOUSE,
            QualityTool.SCREENSHOT,
        ),
        expected_components=("CTabs", "CTab", "CTabPanel"),
        expected_assets=("css", "js"),
        fixture="tabs_overview_component",
        action_states=("callback", "keyboard-selection", "reordered", "removed"),
        ready_selector="[data-citry-tabs-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="dialog.states",
        family="dialog",
        purpose="Exercise opening, dismissal, controlled state, nested focus, long content, and trigger removal.",
        states=(
            "closed",
            "open",
            "controlled",
            "persistent",
            "nested",
            "long-content",
            "form",
            "removed-trigger",
            "removed-open",
        ),
        profiles=(
            "light",
            "dark",
            "keyboard",
            "narrow",
            "reduced-motion",
            "forced-colors",
            "touch",
            "zoom-200",
            "zoom-400",
        ),
        tools=(QualityTool.AXE, QualityTool.BROWSER, QualityTool.DOCS, QualityTool.HTML, QualityTool.SCREENSHOT),
        expected_components=("CDialog", "CButton"),
        expected_assets=("css", "js"),
        fixture="dialog_states_component",
        action_states=("open", "nested", "removed-trigger", "removed-open"),
        ready_selector="[data-citry-dialog-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="combobox.states",
        family="combobox",
        purpose="Exercise local and remote selection plus representative native Form states.",
        states=(
            "local",
            "remote",
            "open",
            "selected",
            "empty",
            "loading",
            "disabled",
            "readonly",
            "invalid",
        ),
        profiles=(
            "light",
            "dark",
            "keyboard",
            "narrow",
            "rtl",
            "touch",
            "reduced-motion",
            "forced-colors",
            "zoom-200",
            "zoom-400",
        ),
        tools=(QualityTool.AXE, QualityTool.BROWSER, QualityTool.DOCS, QualityTool.HTML, QualityTool.SCREENSHOT),
        expected_components=("CCombobox",),
        expected_assets=("css", "js"),
        fixture="combobox_states_component",
        action_states=("open", "remote"),
        ready_selector="[data-citry-combobox-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="table.states",
        family="table",
        purpose="Exercise semantic rows, state messages, density, overflow, and representative large output.",
        states=(
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
        ),
        profiles=("light", "dark", "rtl", "narrow", "zoom-200", "zoom-400", "forced-colors"),
        tools=(
            QualityTool.AXE,
            QualityTool.BROWSER,
            QualityTool.DOCS,
            QualityTool.HTML,
            QualityTool.PERFORMANCE,
            QualityTool.SCREENSHOT,
        ),
        expected_components=("CTable",),
        expected_assets=("css",),
        fixture="table_states_component",
        action_states=(),
        ready_selector="[data-citry-ui-part='table']",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="workflow.repeatable-contacts",
        family="composition",
        purpose="Pressure add, remove, reorder, focus, edits, validation, and native submission together.",
        states=("add", "remove", "reorder", "focus", "edited-values", "invalid", "submit"),
        profiles=("light", "keyboard", "narrow", "touch", "reduced-motion"),
        tools=(QualityTool.AXE, QualityTool.BROWSER, QualityTool.HTML, QualityTool.PERFORMANCE),
        expected_components=("CForm", "CField", "CInput", "CCombobox", "CButton"),
        expected_assets=("css", "js"),
        fixture="repeatable_contacts_component",
        action_states=("add", "remove", "reorder", "submit"),
        ready_selector="[data-citry-form-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="composition.orbit-access",
        family="composition",
        purpose="Qualify a branded account-access form assembled only from public component contracts.",
        states=("light", "form", "required", "combobox", "native-submit", "brand-override"),
        profiles=("light", "keyboard", "narrow", "zoom-200", "zoom-400", "forced-colors"),
        tools=(
            QualityTool.AXE,
            QualityTool.BROWSER,
            QualityTool.CSS,
            QualityTool.DOCS,
            QualityTool.HTML,
            QualityTool.LIGHTHOUSE,
            QualityTool.SCREENSHOT,
        ),
        expected_components=("CForm", "CField", "CInput", "CCombobox", "CButton"),
        expected_assets=("css", "js"),
        fixture="orbit_access_component",
        action_states=("native-submit",),
        ready_selector="[data-citry-form-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
    Scenario(
        id="composition.ledger-dashboard",
        family="composition",
        purpose="Qualify a dark operations dashboard with Tabs, Table, Dialog, and public brand overrides.",
        states=(
            "dark",
            "tabs",
            "table",
            "dialog",
            "overflow",
            "brand-override",
            "tab-selection",
            "dialog-open",
            "dialog-close",
        ),
        profiles=(
            "dark",
            "keyboard",
            "narrow",
            "rtl",
            "zoom-200",
            "zoom-400",
            "forced-colors",
            "reduced-motion",
            "touch",
        ),
        tools=(
            QualityTool.AXE,
            QualityTool.BROWSER,
            QualityTool.CSS,
            QualityTool.DOCS,
            QualityTool.HTML,
            QualityTool.LIGHTHOUSE,
            QualityTool.SCREENSHOT,
        ),
        expected_components=("CTabs", "CTab", "CTabPanel", "CTable", "CDialog", "CButton"),
        expected_assets=("css", "js"),
        fixture="ledger_dashboard_component",
        action_states=("tab-selection", "dialog-open", "dialog-close"),
        ready_selector="[data-citry-tabs-initialized]",
        standalone=True,
        status=ScenarioStatus.READY,
    ),
)


def scenario_by_id(scenario_id: str) -> Scenario:
    """Return one scenario or raise a pointed error for an unknown ID."""
    for scenario in SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    choices = ", ".join(scenario.id for scenario in SCENARIOS)
    msg = f"Unknown Citry UI scenario {scenario_id!r}; choose one of: {choices}."
    raise KeyError(msg)


def manifest_json() -> str:
    """Serialize the ordered catalog for CI artifacts and release records."""
    return (
        json.dumps(
            {
                "schema": "citry-ui-quality-scenarios/v1",
                "scenarios": [scenario.manifest_value() for scenario in SCENARIOS],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    sys.stdout.write(manifest_json())
