import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerAtAGlance(Component):
    template = """
      <section class="divider-glance" aria-labelledby="divider-glance-title">
        <p class="divider-glance__eyebrow">Deep-sky field guide</p>
        <h2 id="divider-glance-title">Northern summer</h2>
        <p>Trace bright nebulae before the Milky Way reaches the western horizon.</p>
        <c-CDivider>After midnight</c-CDivider>
        <div class="divider-glance__row">
          <span>Cygnus</span>
          <c-CDivider orientation="vertical" c-decorative="True" />
          <span>Lyra</span>
          <c-CDivider orientation="vertical" c-decorative="True" />
          <span>Aquila</span>
        </div>
      </section>
    """
    css = """
      :where(.divider-glance) {
        max-inline-size: 36rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9c9e8, #41557c);
        border-radius: 0.9rem;
        background: light-dark(#f7f9ff, #141b30);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-glance h2, .divider-glance p) {
        margin: 0;
      }

      :where(.divider-glance h2) {
        margin-block: 0.2rem 0.5rem;
        font-size: 1.15rem;
      }

      :where(.divider-glance__eyebrow) {
        color: light-dark(#3d5c9a, #a9bfe8);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.divider-glance [data-citry-ui-part="divider"][data-labeled]) {
        margin-block: 1rem;
      }

      :where(.divider-glance__row) {
        display: flex;
        min-block-size: 2.25rem;
        align-items: stretch;
        gap: 0.75rem;
      }
    """


preview = DividerAtAGlance()

preview  # noqa: B018
