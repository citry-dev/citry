import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FlowAtAGlance(Component):
    template = """
      <c-CStack class_="flow-glance" gap="lg">
        <c-CStack gap="xs">
          <p class="flow-glance__eyebrow">Kiln room · shelf 4</p>
          <h2>Moon jar firing notes</h2>
          <p>Hold at 1,280°C until the glaze softens to a pale blue-white.</p>
        </c-CStack>
        <c-CGroup>
          <span class="flow-glance__tag">Porcelain</span>
          <span class="flow-glance__tag">Reduction</span>
          <span class="flow-glance__tag">12 hours</span>
        </c-CGroup>
        <c-CGroup justify="end">
          <c-CButton variant="ghost">Archive</c-CButton>
          <c-CButton>Save firing</c-CButton>
        </c-CGroup>
      </c-CStack>
    """

    css = """
      :where(.flow-glance) {
        max-inline-size: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#d7c8b4, #6f6357);
        border-radius: 0.85rem;
        background: light-dark(#fffaf2, #241f1a);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-glance h2, .flow-glance p) {
        margin: 0;
      }

      :where(.flow-glance h2) {
        font-size: 1.05rem;
      }

      :where(.flow-glance__eyebrow) {
        color: light-dark(#8a4b2b, #f0aa7d);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.flow-glance__tag) {
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        background: light-dark(#ead8bd, #4a3d31);
        font-size: 0.78rem;
      }
    """


preview = FlowAtAGlance()

preview  # noqa: B018
