import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardAtAGlance(Component):
    template = """
      <section class="card-glance" aria-label="Rooms and furnishings">
        <c-CCard>
          <c-fill name="media">
            <div class="card-glance__scene card-glance__scene--sunroom" aria-hidden="true">
              <span></span>
            </div>
          </c-fill>
          <c-fill name="header">
            <p class="card-glance__eyebrow">Sunroom</p>
            <h2>Window reading chair</h2>
          </c-fill>
          <c-fill name="default">
            Oak arms, woven rush, and a linen cushion for slow afternoons.
          </c-fill>
          <c-fill name="footer">
            Natural oak · 76 cm wide
          </c-fill>
          <c-fill name="actions">
            <c-CButton size="sm">View chair</c-CButton>
          </c-fill>
        </c-CCard>

        <c-CCard variant="outline">
          <c-fill name="media">
            <div class="card-glance__scene card-glance__scene--studio" aria-hidden="true">
              <span></span>
            </div>
          </c-fill>
          <c-fill name="header">
            <p class="card-glance__eyebrow">Studio</p>
            <h2>Cloud pendant</h2>
          </c-fill>
          <c-fill name="header_actions">
            <c-CButton
              size="sm"
              variant="ghost"
              c-attrs="{'aria-label': 'Save Cloud pendant'}"
            >
              <c-CIcon name="heart" />
              <span class="card-glance__sr-only">Save</span>
            </c-CButton>
          </c-fill>
          <c-fill name="default">
            A softly diffused shade for desks, drawing tables, and late-night sketches.
          </c-fill>
        </c-CCard>

        <c-CCard variant="subtle">
          <c-fill name="header">
            <p class="card-glance__eyebrow">Library</p>
            <h2>Walnut wall shelf</h2>
          </c-fill>
          <c-fill name="default">
            Three slim shelves keep favorite books close without crowding the room.
          </c-fill>
          <c-fill name="actions">
            <c-CButton size="sm" variant="outline">See dimensions</c-CButton>
            <c-CButton size="sm" variant="ghost">Add to room</c-CButton>
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        max-width: 68rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-glance [data-citry-ui-part="card"]) {
        align-self: start;
      }

      :where(.card-glance h2, .card-glance p) {
        margin: 0;
      }

      :where(.card-glance h2) {
        font-size: 1.05rem;
      }

      :where(.card-glance__eyebrow) {
        margin-block-end: 0.25rem;
        color: light-dark(#72531b, #e4bd70);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.card-glance__scene) {
        position: relative;
        block-size: 8.5rem;
        overflow: hidden;
      }

      :where(.card-glance__scene::before) {
        position: absolute;
        inset: 0;
        content: "";
      }

      :where(.card-glance__scene--sunroom::before) {
        background:
          linear-gradient(90deg, transparent 66%, rgb(255 255 255 / 46%) 66% 70%, transparent 70%),
          linear-gradient(160deg, #e9cfa0, #8aaa79);
      }

      :where(.card-glance__scene--studio::before) {
        background:
          radial-gradient(circle at 62% 38%, #fff1c7 0 13%, transparent 14%),
          linear-gradient(145deg, #8ba4bd, #3f5068);
      }

      :where(.card-glance__scene span) {
        position: absolute;
        inset-inline: 18%;
        inset-block-end: 16%;
        block-size: 30%;
        border-radius: 999px 999px 0.35rem 0.35rem;
        background: rgb(255 255 255 / 62%);
      }

      :where(.card-glance__sr-only) {
        position: absolute;
        inline-size: 1px;
        block-size: 1px;
        overflow: hidden;
        clip-path: inset(50%);
        white-space: nowrap;
      }
    """


preview = CardAtAGlance()

preview  # noqa: B018
