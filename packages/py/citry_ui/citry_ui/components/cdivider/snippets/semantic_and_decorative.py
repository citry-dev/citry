import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SemanticAndDecorativeDividers(Component):
    template = """
      <section class="divider-meaning">
        <article>
          <h2>Semantic break</h2>
          <p>Observation notes end here.</p>
          <c-CDivider />
          <p>A new topic begins with the equipment log.</p>
        </article>
        <article>
          <h2>Decorative line</h2>
          <div class="divider-meaning__metric">
            <span>Exposure</span>
            <c-CDivider c-decorative="True" />
            <strong>180 s</strong>
          </div>
        </article>
      </section>
    """
    css = """
      :where(.divider-meaning) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
        gap: 1rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-meaning article) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border: 1px solid light-dark(#cbd5e1, #475569);
        border-radius: 0.75rem;
      }

      :where(.divider-meaning h2, .divider-meaning p) {
        margin: 0;
      }

      :where(.divider-meaning h2) {
        font-size: 1rem;
      }

      :where(.divider-meaning__metric) {
        display: grid;
        gap: 0.5rem;
      }
    """


preview = SemanticAndDecorativeDividers()

preview  # noqa: B018
