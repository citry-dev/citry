"""Render complete standalone pages from ready Citry UI scenarios."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import citry_ui
from citry import Citry, Component
from citry_ui.components.cbutton.quality.scenario import button_states_component
from citry_ui.components.ccombobox.quality.scenario import combobox_states_component
from citry_ui.components.cdialog.quality.scenario import dialog_states_component
from citry_ui.components.cfield.quality.scenario import field_input_states_component
from citry_ui.components.cform.quality.scenario import form_states_component
from citry_ui.components.ctable.quality.scenario import table_states_component
from citry_ui.components.ctabs.quality.scenario import tabs_overview_component
from citry_ui.quality.compositions import (
    ledger_dashboard_component,
    orbit_access_component,
    repeatable_contacts_component,
)
from citry_ui.quality.scenarios import Scenario, ScenarioStatus, scenario_by_id

if TYPE_CHECKING:
    from collections.abc import Callable

_SCENARIO_FACTORIES = {
    "button.states": button_states_component,
    "field-input.states": field_input_states_component,
    "form.states": form_states_component,
    "tabs.overview": tabs_overview_component,
    "dialog.states": dialog_states_component,
    "combobox.states": combobox_states_component,
    "table.states": table_states_component,
    "workflow.repeatable-contacts": repeatable_contacts_component,
    "composition.orbit-access": orbit_access_component,
    "composition.ledger-dashboard": ledger_dashboard_component,
}

_PAGE_CSS = """
  :where(html) {
    color-scheme: light dark;
    background: Canvas;
    color: CanvasText;
    font-family: ui-sans-serif, system-ui, sans-serif;
  }

  :where(body) {
    margin: 0;
  }

  :where(main) {
    box-sizing: border-box;
    inline-size: min(100%, 72rem);
    margin-inline: auto;
    padding: 2rem;
  }

  :where(.citry-ui-quality-stack) {
    display: grid;
    gap: 1rem;
  }

  :where(.citry-ui-quality-grid) {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
    gap: 1rem;
    align-items: start;
  }

  :where(.citry-ui-quality-grid > h1) {
    grid-column: 1 / -1;
  }
"""


def renderable_scenario_ids() -> tuple[str, ...]:
    """Return scenario IDs that have a registered standalone renderer."""
    return tuple(_SCENARIO_FACTORIES)


@dataclass(frozen=True, slots=True)
class RenderedScenario:
    """One complete scenario document and the Citry instance that owns it."""

    scenario: Scenario
    app: Citry
    html: str


def build_scenario(
    scenario_id: str,
    *,
    configure_app: Callable[[Citry], None] | None = None,
) -> RenderedScenario:
    """Build a complete scenario after an optional host configures Citry."""
    scenario = scenario_by_id(scenario_id)
    if scenario.status is not ScenarioStatus.READY:
        msg = f"Citry UI scenario {scenario_id!r} is {scenario.status.value}; no route is available yet."
        raise RuntimeError(msg)
    factory = _SCENARIO_FACTORIES.get(scenario_id)
    if factory is None:
        msg = f"No renderer is registered for ready scenario {scenario_id!r}."
        raise RuntimeError(msg)

    app = Citry(secret="citry-ui-quality-scenarios", autodiscover=False)  # noqa: S106
    app.register_library(citry_ui)
    if configure_app is not None:
        configure_app(app)
    scenario_component = factory(app)

    class ScenarioPage(Component):
        citry = app
        css = _PAGE_CSS

        class Kwargs:
            pass

        class Slots:
            pass

        template = f"""
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <meta name="color-scheme" content="light dark" />
              <title>{{{{ page_title }}}}</title>
              <c-css />
            </head>
            <body data-citry-ui-scenario="{scenario.id}">
              <main id="main-content">
                <c-{scenario_component.__name__} />
              </main>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"page_title": f"{scenario.purpose} | Citry UI quality"}

    return RenderedScenario(scenario=scenario, app=app, html=str(ScenarioPage()))


def render_scenario(scenario_id: str, *, embedded: bool = False) -> str:
    """Render a ready scenario as a component fragment or complete page."""
    if not embedded:
        return build_scenario(scenario_id).html

    scenario = scenario_by_id(scenario_id)
    if scenario.status is not ScenarioStatus.READY:
        msg = f"Citry UI scenario {scenario_id!r} is {scenario.status.value}; no route is available yet."
        raise RuntimeError(msg)
    factory = _SCENARIO_FACTORIES.get(scenario_id)
    if factory is None:
        msg = f"No renderer is registered for ready scenario {scenario_id!r}."
        raise RuntimeError(msg)
    app = Citry(secret="citry-ui-quality-scenarios", autodiscover=False)  # noqa: S106
    app.register_library(citry_ui)
    return str(factory(app)())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a ready Citry UI quality scenario.")
    parser.add_argument("scenario_id")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--embedded", action="store_true")
    args = parser.parse_args()

    html = render_scenario(args.scenario_id, embedded=args.embedded)
    if args.output is None:
        sys.stdout.write(html + "\n")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
