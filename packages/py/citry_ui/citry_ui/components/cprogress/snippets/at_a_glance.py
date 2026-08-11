import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ProgressAtAGlance(Component):
    template = """
      <section class="progress-glance">
        <c-CGroup justify="between">
          <div><p>Research dive 08</p><h2>Mapping the reef shelf</h2></div>
          <strong>68%</strong>
        </c-CGroup>
        <c-CProgress label="Mapping the reef shelf" c-value="68" shape="pill" />
        <p>Sonar pass 17 of 25 · 42 minutes remaining</p>
      </section>
    """
    css = """
      :where(.progress-glance) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#9fc5d4, #406572);
        border-radius: 0.85rem;
        background: light-dark(#f0fbff, #11252c);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-glance h2, .progress-glance p) {
        margin: 0;
      }

      :where(.progress-glance > p, .progress-glance [data-citry-ui-part="group"] p) {
        color: light-dark(#416a78, #a7cbd7);
        font-size: 0.78rem;
      }
    """


preview = ProgressAtAGlance()

preview  # noqa: B018
