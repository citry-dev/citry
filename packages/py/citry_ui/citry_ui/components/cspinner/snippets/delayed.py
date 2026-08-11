import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DelayedSpinner(Component):
    template = """
      <section class="spinner-delayed" x-data="{visible: false}">
        <button type="button" @click="visible = !visible">Toggle long-running observation</button>
        <div x-show="visible" class="spinner-delayed__status">
          <c-CSpinner label="Waiting for long exposure" size="sm" />
          <span>Waiting for the long exposure</span>
        </div>
        <p>Real applications show this only after their chosen delay.</p>
      </section>
    """
    css = """
      :where(.spinner-delayed) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-delayed__status) {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      :where(.spinner-delayed p) {
        margin: 0;
        color: light-dark(#57566f, #c8c6df);
        font-size: 0.78rem;
      }
    """


preview = DelayedSpinner()

preview  # noqa: B018
