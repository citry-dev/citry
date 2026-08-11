import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerCustomization(Component):
    template = """
      <c-CGroup class_="spinner-custom" gap="lg">
        <div class="spinner-custom__violet"><c-CSpinner label="Violet observatory task" /></div>
        <div class="spinner-custom__solar"><c-CSpinner label="Solar observatory task" /></div>
        <div class="spinner-custom__ice"><c-CSpinner label="Ice observatory task" /></div>
      </c-CGroup>
    """
    css = """
      :where(.spinner-custom > div) {
        display: grid;
        place-items: center;
        min-inline-size: 5rem;
        min-block-size: 5rem;
        border-radius: 0.75rem;
        background: light-dark(#f5f4ff, #17172a);
      }

      :where(.spinner-custom__violet) {
        --cui-spinner-color: #7c3aed;
        --cui-spinner-track-color: #ddd6fe;
        --cui-spinner-size: 2rem;
      }

      :where(.spinner-custom__solar) {
        --cui-spinner-color: #c2410c;
        --cui-spinner-track-color: #fed7aa;
        --cui-spinner-thickness: 0.24rem;
      }

      :where(.spinner-custom__ice) {
        --cui-spinner-color: #0891b2;
        --cui-spinner-track-color: #a5f3fc;
        --cui-spinner-duration: 1.2s;
      }
    """


preview = SpinnerCustomization()

preview  # noqa: B018
