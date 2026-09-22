from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class ControlledNativeSelect(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "vessels": [
                CNativeSelectOption("calypso", "Calypso"),
                CNativeSelectOption("nautilus", "Nautilus"),
                CNativeSelectOption("aronnax", "Aronnax"),
            ],
        }

    template = """
      <section
        class="ocean-controlled"
      >
        <c-CField>
          <c-fill name="label">Survey vessel</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="vessel"
              c-options="vessels"
              placeholder="Unassigned"
              :value="controlled
                  ? vessel
                  : undefined"
              @input="vessel = $event.target.value"
            />
          </c-fill>
          <c-fill name="description">
            <span
              v-text="controlled
                ? 'Application controlled'
                : 'Browser controlled'"
            ></span>
          </c-fill>
        </c-CField>

        <div class="ocean-controlled__actions">
          <c-CButton
            type="button"
            size="sm"
            @click="controlled = false"
          >
            Release
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="outline"
            @click="
              vessel = 'calypso';
              controlled = true;
            "
          >
            Assign Calypso
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="ghost"
            @click="
              vessel = null;
              controlled = true;
            "
          >
            Clear
          </c-CButton>
        </div>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            controlled: true,
            vessel: 'nautilus',
          };
        },
      });
    """

    css = """
      :where(.ocean-controlled) {
        display: grid;
        gap: 1rem;
        max-width: 36rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-controlled__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ControlledNativeSelect()

preview  # noqa: B018
