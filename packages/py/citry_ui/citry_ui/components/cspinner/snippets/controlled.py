import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSpinner(Component):
    template = """
      <section
        class="spinner-controlled"
        x-init="Alpine.store('spinnerControls', {intent: 'primary', size: 'md'})"
      >
        <c-CRow>
          <c-CSpinner
            label="Refreshing orbital catalog"
            $c-props="{
              intent: $store.spinnerControls.intent,
              size: $store.spinnerControls.size,
            }"
          />
          <span>Refreshing orbital catalog</span>
        </c-CRow>
        <c-CRow wrap>
          <label>
            Intent
            <select x-model="$store.spinnerControls.intent">
              <option>primary</option><option>success</option>
              <option>warn</option><option>danger</option>
            </select>
          </label>
          <label>
            Size
            <select x-model="$store.spinnerControls.size">
              <option>sm</option><option>md</option><option>lg</option>
            </select>
          </label>
        </c-CRow>
      </section>
    """
    css = """
      :where(.spinner-controlled) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-controlled label) {
        display: grid;
        gap: 0.3rem;
        font-size: 0.75rem;
      }
    """


preview = ControlledSpinner()

preview  # noqa: B018
