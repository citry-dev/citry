import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertCustomization(Component):
    template = """
      <section class="alert-themes" aria-label="Alert theme customization">
        <article class="alert-themes__solar">
          <h2>Solar observatory</h2>
          <c-CAlert intent="warn">
            Coronal imaging pauses during the calibration sweep.
          </c-CAlert>
        </article>
        <article class="alert-themes__radio">
          <h2>Radio observatory</h2>
          <c-CAlert class_="radio-success" intent="success" variant="outline">
            The receiver array is synchronized.
          </c-CAlert>
        </article>
      </section>
    """

    css = """
      :where(.alert-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 60rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.alert-themes article) {
        display: grid;
        gap: 0.75rem;
      }

      :where(.alert-themes h2) {
        margin: 0;
        font-size: 1rem;
      }

      :where(.alert-themes__solar) {
        --cui-alert-background: light-dark(#fff8df, #30270b);
        --cui-alert-border-color: light-dark(#d99d13, #ffd166);
        --cui-alert-icon-color: light-dark(#9a6700, #ffd166);
      }

      :where(.radio-success[data-citry-ui-part="alert"]) {
        --cui-alert-border-color: light-dark(#6d28d9, #c4b5fd);
        --cui-alert-icon-color: light-dark(#6d28d9, #c4b5fd);
        --cui-alert-radius: 1.25rem;
      }
    """


preview = AlertCustomization()

preview  # noqa: B018
