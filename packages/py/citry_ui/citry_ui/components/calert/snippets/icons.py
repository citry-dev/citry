import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertIcons(Component):
    template = """
      <section class="alert-icons" aria-label="Alert icons">
        <c-CAlert intent="success">
          Automatic success icon follows intent.
        </c-CAlert>
        <c-CAlert intent="warn" c-icon="False">
          Icon hidden; the message still carries the meaning.
        </c-CAlert>
        <c-CAlert icon_name="star" variant="outline">
          Fixed registered star icon stays constant when intent changes.
        </c-CAlert>
      </section>
    """

    css = """
      :where(.alert-icons) {
        display: grid;
        gap: 0.75rem;
        max-width: 50rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertIcons()

preview  # noqa: B018
