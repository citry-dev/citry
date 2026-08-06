import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledValues(Component):
    template = """
      <section
        class="shore-values"
        x-data
        x-init="Alpine.store('shoreValues', {
          controlled: true,
          value: 'Ochre sea star',
        })"
      >
        <c-CField>
          <c-fill name="label">
            Browser-owned note
          </c-fill>
          <c-fill name="default">
            <c-CInput name="uncontrolled" value="Calm water" />
          </c-fill>
          <c-fill name="description">
            Edit freely, then use native reset.
          </c-fill>
        </c-CField>

        <c-CField>
          <c-fill name="label">
            Application-owned species
          </c-fill>
          <c-fill name="default">
            <c-CInput
              name="controlled"
              $c-props="{
                value: $store.shoreValues.controlled
                  ? $store.shoreValues.value
                  : undefined,
              }"
              @input="$store.shoreValues.value = $event.target.value"
            />
          </c-fill>
          <c-fill name="description">
            The native input event updates the supplied value.
          </c-fill>
        </c-CField>

        <div class="shore-values__actions">
          <button
            type="button"
            @click="$store.shoreValues.controlled = false"
          >
            Release control
          </button>
          <button
            type="button"
            @click="
              $store.shoreValues.value = 'Giant green anemone';
              $store.shoreValues.controlled = true;
            "
          >
            Set controlled value
          </button>
        </div>
      </section>
    """

    css = """
      :where(.shore-values) {
        display: grid;
        gap: 1.25rem;
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-values__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.shore-values__actions button) {
        min-height: 2.5rem;
      }
    """


preview = ControlledValues()

preview  # noqa: B018
