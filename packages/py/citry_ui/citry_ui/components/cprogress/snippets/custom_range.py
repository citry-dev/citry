import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomRangeProgress(Component):
    template = """
      <section class="progress-range">
        <c-CGroup justify="between"><h2>Sample crates cataloged</h2><strong>6 / 10</strong></c-CGroup>
        <c-CProgress
          label="Sample crates cataloged"
          c-value="6"
          c-max="10"
          value_text="6 of 10 sample crates"
          intent="success"
        />
      </section>
    """
    css = """
      :where(.progress-range) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 32rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-range h2) {
        margin: 0;
        font-size: 0.95rem;
      }
    """


preview = CustomRangeProgress()

preview  # noqa: B018
