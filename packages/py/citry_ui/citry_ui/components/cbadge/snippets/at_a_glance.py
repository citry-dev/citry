import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeAtAGlance(Component):
    template = """
      <section class="badge-glance" aria-labelledby="badge-glance-title">
        <div>
          <p>Mineral archive · specimen 184</p>
          <h2 id="badge-glance-title">Azurite rosette</h2>
        </div>
        <c-CRow>
          <c-CBadge intent="primary">Copper carbonate</c-CBadge>
          <c-CBadge intent="success" variant="outline">Verified</c-CBadge>
          <c-CBadge shape="pill">3 fragments</c-CBadge>
        </c-CRow>
      </section>
    """
    css = """
      :where(.badge-glance) {
        display: flex;
        flex-wrap: wrap;
        align-items: end;
        justify-content: space-between;
        gap: 1rem;
        max-inline-size: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b7c6cf, #526873);
        border-radius: 0.85rem;
        background: light-dark(#f5fbff, #17232a);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-glance h2, .badge-glance p) {
        margin: 0;
      }

      :where(.badge-glance p) {
        color: light-dark(#496471, #a9c5d2);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.badge-glance h2) {
        margin-block-start: 0.25rem;
        font-size: 1.1rem;
      }
    """


preview = BadgeAtAGlance()

preview  # noqa: B018
