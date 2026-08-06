import pytest

from citry_ui.quality.exit_record import qualification_record


def test_exit_record_distinguishes_configured_passed_manual_and_unavailable_work():
    record = qualification_record(
        results={"scenario-catalog": "passed", "scaling": "diagnostic-only"},
        artifacts={"scenario-catalog": "artifact://scenario-manifest"},
    )

    profiles = {profile["id"]: profile for profile in record["profiles"]}
    manual = {task["id"]: task for task in record["manual_tasks"]}
    assert record["schema"] == "citry-ui-phase-7.5-exit/v1"
    assert profiles["scenario-catalog"]["status"] == "passed"
    assert profiles["scenario-catalog"]["artifact"] == "artifact://scenario-manifest"
    assert profiles["routes"]["status"] == "configured"
    assert profiles["scaling"]["status"] == "diagnostic-only"
    assert manual["visual-design-approval"]["status"] == "awaiting-human-review"
    assert manual["multi-release-lifecycle"]["status"] == "unavailable"
    assert manual["assistive-technology"]["instructions"].endswith("#assistive-technology-sessions")
    assert manual["real-devices"]["instructions"].endswith("#real-device-and-environmental-sessions")
    assert record["environment"]["chromium"] == "not-inspected"


@pytest.mark.parametrize(
    ("results", "artifacts", "message"),
    [
        ({"missing": "passed"}, {}, "Unknown qualification profiles"),
        ({"routes": "maybe"}, {}, "Unknown qualification statuses"),
        ({}, {"missing": "artifact://x"}, "Unknown qualification profiles"),
    ],
)
def test_exit_record_rejects_unknown_profiles_and_statuses(results, artifacts, message):
    with pytest.raises(ValueError, match=message):
        qualification_record(results=results, artifacts=artifacts)
