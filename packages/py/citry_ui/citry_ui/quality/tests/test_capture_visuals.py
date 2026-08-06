from citry_ui.quality.capture_visuals import VISUAL_PROFILES, capture_plan
from citry_ui.quality.scenarios import SCENARIOS, QualityTool


def test_capture_plan_is_deterministic_and_covers_every_visual_scenario():
    first = capture_plan()
    second = capture_plan()

    assert first == second
    assert len(first) == len({(entry.scenario_id, entry.profile.id) for entry in first})
    expected = {scenario.id for scenario in SCENARIOS if QualityTool.SCREENSHOT in scenario.tools}
    assert {entry.scenario_id for entry in first} == expected
    assert all(entry.profile.id in VISUAL_PROFILES for entry in first)
    assert any(entry.profile.id == "zoom-400-reflow" for entry in first)


def test_capture_plan_adds_only_profiles_declared_by_each_scenario():
    by_scenario = {scenario.id: scenario for scenario in SCENARIOS}

    for entry in capture_plan():
        scenario = by_scenario[entry.scenario_id]
        if entry.profile.id == "desktop-dark":
            assert "dark" in scenario.profiles
        elif entry.profile.id == "narrow-light":
            assert "narrow" in scenario.profiles
        elif entry.profile.id == "rtl-light":
            assert "rtl" in scenario.profiles
        elif entry.profile.id == "reduced-motion":
            assert "reduced-motion" in scenario.profiles
        elif entry.profile.id == "forced-colors":
            assert "forced-colors" in scenario.profiles
        elif entry.profile.id == "touch-light":
            assert "touch" in scenario.profiles
        elif entry.profile.id == "zoom-200-reflow":
            assert "zoom-200" in scenario.profiles
        elif entry.profile.id == "zoom-400-reflow":
            assert "zoom-400" in scenario.profiles
