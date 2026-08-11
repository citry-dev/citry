import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledProgress(Component):
    template = """
      <section class="progress-controlled" x-data="{value: 28}">
        <c-CGroup justify="between"><h2>Transect upload</h2><output x-text="`${value}%`"></output></c-CGroup>
        <c-CProgress label="Transect upload" $c-props="{value}" shape="pill" />
        <label>Completion <input type="range" min="0" max="100" x-model.number="value" /></label>
      </section>
    """
    css = """
      :where(.progress-controlled) {
        display: grid;
        gap: 0.85rem;
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-controlled h2) {
        margin: 0;
        font-size: 1rem;
      }

      :where(.progress-controlled label) {
        display: grid;
        gap: 0.35rem;
        font-size: 0.8rem;
      }

      :where(.progress-controlled input) {
        inline-size: 100%;
      }
    """


preview = ControlledProgress()

preview  # noqa: B018
