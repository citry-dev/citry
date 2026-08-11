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
        x-data
        x-init="Alpine.store('nativeSelectFleet', {
          controlled: true,
          vessel: 'nautilus',
        })"
      >
        <c-CField>
          <c-fill name="label">Survey vessel</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="vessel"
              c-options="vessels"
              placeholder="Unassigned"
              $c-props="{
                value: $store.nativeSelectFleet.controlled
                  ? $store.nativeSelectFleet.vessel
                  : undefined,
              }"
              @input="$store.nativeSelectFleet.vessel = $event.target.value"
            />
          </c-fill>
          <c-fill name="description">
            <span
              x-text="$store.nativeSelectFleet.controlled
                ? 'Application controlled'
                : 'Browser controlled'"
            ></span>
          </c-fill>
        </c-CField>

        <div class="ocean-controlled__actions">
          <c-CButton
            type="button"
            size="sm"
            @click="$store.nativeSelectFleet.controlled = false"
          >
            Release
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="outline"
            @click="
              $store.nativeSelectFleet.vessel = 'calypso';
              $store.nativeSelectFleet.controlled = true;
            "
          >
            Assign Calypso
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="ghost"
            @click="
              $store.nativeSelectFleet.vessel = null;
              $store.nativeSelectFleet.controlled = true;
            "
          >
            Clear
          </c-CButton>
        </div>
      </section>
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
