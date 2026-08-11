from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativePickerBoundary(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "currents": [
                CNativeSelectOption("north", "North Equatorial Current"),
                CNativeSelectOption("counter", "Equatorial Countercurrent"),
                CNativeSelectOption("south", "South Equatorial Current"),
            ],
        }

    template = """
      <section class="ocean-picker" dir="rtl">
        <form id="current-survey"></form>
        <label for="current-select">تيار المحيط</label>
        <c-CNativeSelect
          id="current-select"
          name="current"
          c-options="currents"
          value="counter"
          c-attrs="{'form': 'current-survey', 'dir': 'rtl'}"
          @change="document.querySelector('#picker-value').textContent = $event.target.value"
        />
        <div class="ocean-picker__actions">
          <c-CButton
            type="button"
            size="sm"
            @click="
              const select = document.querySelector('#current-select');
              if (select.showPicker) select.showPicker();
              else select.focus();
            "
          >
            Open native picker
          </c-CButton>
          <output id="picker-value">counter</output>
        </div>
      </section>
    """

    css = """
      :where(.ocean-picker) {
        display: grid;
        gap: 0.75rem;
        max-width: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-picker__actions) {
        display: flex;
        align-items: center;
        gap: 1rem;
      }

      :where(.ocean-picker output) {
        font-family: ui-monospace, monospace;
      }
    """


preview = NativePickerBoundary()

preview  # noqa: B018
