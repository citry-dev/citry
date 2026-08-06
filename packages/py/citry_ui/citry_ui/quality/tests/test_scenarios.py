import json

from citry_ui.quality.scenarios import SCENARIOS, ScenarioStatus, manifest_json, scenario_by_id


def test_scenario_catalog_has_stable_unique_ordered_ids():
    ids = [scenario.id for scenario in SCENARIOS]

    assert ids == [
        "button.states",
        "field-input.states",
        "form.states",
        "tabs.overview",
        "dialog.states",
        "combobox.states",
        "table.states",
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
    assert value["scenarios"][0]["id"] == "button.states"
    assert scenario_by_id("tabs.overview").family == "tabs"


def test_catalog_maps_every_phase_7_5_family_state_to_a_scenario():
    required = {
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
    }

    for scenario_id, states in required.items():
        assert states <= set(scenario_by_id(scenario_id).states)
