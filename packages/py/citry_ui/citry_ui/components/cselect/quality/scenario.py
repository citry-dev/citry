"""Shared Select scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component
from citry_ui import CSelectOption


def select_states_component(app: Citry) -> type[Component]:
    class CitryUiSelectStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-select-ready>
            <h1>Select states</h1>
            <c-CField required>
              <c-fill name="label">Planet</c-fill>
              <c-fill name="description">Choose one destination.</c-fill>
              <c-fill name="default">
                <c-CSelect c-options="options" placeholder="Choose a planet" name="planet" value="earth" />
              </c-fill>
            </c-CField>
            <c-CSelect
              c-options="options" placeholder="Choose" readonly value="mars"
              c-trigger_attrs="{'aria-label':'Read-only planet'}"
            />
            <c-CSelect
              c-options="options" placeholder="Choose" disabled
              c-trigger_attrs="{'aria-label':'Disabled planet'}"
            />
            <div dir="rtl" style="inline-size:12rem">
              <c-CSelect
                c-options="options" placeholder="اختر" variant="filled"
                c-trigger_attrs="{'aria-label':'كوكب'}"
              />
            </div>
            <div style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem">
              <c-CSelect
                c-options="options" placeholder="Choose" variant="plain" size="lg"
                c-trigger_attrs="{'aria-label':'Night planet'}"
              />
            </div>
          </section>
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "options": [
                    CSelectOption("earth", "Earth"),
                    CSelectOption("mars", "Mars", "The red planet", group="Rocky"),
                    CSelectOption("venus", "Venus", disabled=True, group="Rocky"),
                ]
            }

    return CitryUiSelectStates
