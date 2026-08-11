import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconAtAGlance(Component):
    template = """
      <section class="icon-glance" aria-label="Botanical field notes">
        <article>
          <c-CIcon name="search" size="lg" />
          <div>
            <strong>Canopy survey</strong>
            <span>Search the northern transect</span>
          </div>
        </article>
        <article>
          <c-CIcon name="leaf" size="lg" />
          <div>
            <strong>Silver fern</strong>
            <span>Three new fronds recorded</span>
          </div>
        </article>
        <article>
          <c-CIcon name="calendar" size="lg" />
          <div>
            <strong>Next observation</strong>
            <span>At first light on 14 August</span>
          </div>
        </article>
        <article class="icon-glance__status">
          <c-CIcon name="success" size="lg" />
          <div>
            <strong>Specimen verified</strong>
            <span>Matched to the field key</span>
          </div>
        </article>
      </section>
    """

    css = """
      :where(.icon-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 0.75rem;
        max-width: 68rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-glance article) {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#cbd5c0, #3e5b3a);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.icon-glance [data-citry-ui-part="icon"]) {
        margin-block-start: 0.1rem;
        color: light-dark(#2f6f3e, #80d49a);
      }

      :where(.icon-glance strong, .icon-glance span) {
        display: block;
      }

      :where(.icon-glance span) {
        margin-block-start: 0.2rem;
        color: light-dark(#52604e, #b8c9b5);
        font-size: 0.875rem;
      }
    """


preview = IconAtAGlance()

preview  # noqa: B018
