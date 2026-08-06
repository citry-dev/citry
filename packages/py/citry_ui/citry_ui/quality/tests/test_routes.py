import re

import pytest

from citry_ui.quality.routes import render_scenario, renderable_scenario_ids
from citry_ui.quality.scenarios import SCENARIOS


def _root_section(html: str) -> str:
    start = html.index("<section")
    end = html.rindex("</section>") + len("</section>")
    section = re.sub(r"<!--.*?-->", "", html[start:end], flags=re.DOTALL)
    return re.sub(r"c[0-9a-z]{8,}", "<generated-id>", section)


@pytest.mark.parametrize("scenario_id", [scenario.id for scenario in SCENARIOS])
def test_scenario_uses_the_same_component_markup_embedded_and_standalone(scenario_id):
    embedded = render_scenario(scenario_id, embedded=True)
    standalone = render_scenario(scenario_id)

    assert _root_section(embedded) == _root_section(standalone)
    assert "<!doctype html>" in standalone
    assert '<meta name="viewport"' in standalone
    assert f'data-citry-ui-scenario="{scenario_id}"' in standalone
    assert "citry_ui" not in standalone


def test_every_ready_scenario_has_exactly_one_renderer():
    assert renderable_scenario_ids() == tuple(scenario.id for scenario in SCENARIOS)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario.id)
def test_scenario_documents_emit_the_assets_declared_by_the_catalog(scenario):
    html = render_scenario(scenario.id)

    if "css" in scenario.expected_assets:
        assert "data-citry-css-class" in html
    if "js" in scenario.expected_assets:
        assert "registerComponent" in html


def test_unknown_scenario_fails_instead_of_silently_skipping():
    with pytest.raises(KeyError, match="Unknown Citry UI scenario"):
        render_scenario("missing.states")
