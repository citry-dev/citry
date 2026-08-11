import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertAtAGlance(Component):
    template = """
      <section class="alert-glance" aria-label="Observatory alerts">
        <c-CAlert intent="info">
          <c-fill name="title">Meteor shower tonight</c-fill>
          <c-fill name="default">Peak activity begins near 23:10.</c-fill>
        </c-CAlert>
        <c-CAlert intent="success">
          <c-fill name="title">Telescope aligned</c-fill>
          <c-fill name="default">Tracking error is below 0.2 arcseconds.</c-fill>
        </c-CAlert>
        <c-CAlert intent="warn">
          <c-fill name="title">Cloud bank approaching</c-fill>
          <c-fill name="default">The western horizon may close after midnight.</c-fill>
        </c-CAlert>
        <c-CAlert intent="error">
          <c-fill name="title">Camera link lost</c-fill>
          <c-fill name="default">Reconnect before starting the next exposure.</c-fill>
        </c-CAlert>
      </section>
    """

    css = """
      :where(.alert-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 0.875rem;
        max-width: 72rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertAtAGlance()

preview  # noqa: B018
