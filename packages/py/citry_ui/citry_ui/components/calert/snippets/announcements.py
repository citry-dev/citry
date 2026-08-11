import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertAnnouncements(Component):
    template = """
      <section class="alert-announcements" aria-label="Alert announcement modes">
        <c-CAlert announce="off">
          Static observing instructions use no live-region role.
        </c-CAlert>
        <c-CAlert announce="polite" intent="success">
          <c-fill name="title">Exposure saved</c-fill>
          <c-fill name="default">Use polite urgency for a nonblocking update.</c-fill>
        </c-CAlert>
        <c-CAlert announce="assertive" intent="error">
          <c-fill name="title">Shutter obstruction</c-fill>
          <c-fill name="default">Use assertive urgency only when attention is immediate.</c-fill>
        </c-CAlert>
      </section>
    """

    css = """
      :where(.alert-announcements) {
        display: grid;
        gap: 0.75rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertAnnouncements()

preview  # noqa: B018
