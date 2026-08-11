import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardActions(Component):
    template = """
      <section class="card-actions">
        <c-CCard
          variant="outline"
          c-header_actions_attrs="{'role': 'group', 'aria-label': 'Shelf shortcuts'}"
          c-actions_attrs="{'role': 'group', 'aria-label': 'Shelf actions'}"
        >
          <c-fill name="header">
            <p class="card-actions__eyebrow">Library</p>
            <h2>Floating walnut shelf</h2>
          </c-fill>
          <c-fill name="header_actions">
            <c-CButton
              size="sm"
              variant="ghost"
              c-attrs="{'aria-label': 'Save floating walnut shelf'}"
            >
              <c-CIcon name="heart" />
              <span class="card-actions__sr-only">Save</span>
            </c-CButton>
          </c-fill>
          <c-fill name="default">
            Hidden steel brackets keep the profile light while supporting a row of hardbacks.
          </c-fill>
          <c-fill name="footer">
            90 by 18 cm · walnut veneer
          </c-fill>
          <c-fill name="actions">
            <c-CButton size="sm">Add to room</c-CButton>
            <c-CButton size="sm" variant="outline">Compare finishes</c-CButton>
            <c-CButton size="sm" variant="ghost">Dimensions</c-CButton>
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-actions) {
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-actions h2, .card-actions p) {
        margin: 0;
      }

      :where(.card-actions h2) {
        font-size: 1.05rem;
      }

      :where(.card-actions__eyebrow) {
        margin-block-end: 0.25rem;
        color: light-dark(#7c4f28, #e2b581);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.card-actions__sr-only) {
        position: absolute;
        inline-size: 1px;
        block-size: 1px;
        overflow: hidden;
        clip-path: inset(50%);
        white-space: nowrap;
      }
    """


preview = CardActions()

preview  # noqa: B018
