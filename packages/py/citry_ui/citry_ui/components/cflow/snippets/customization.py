import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FlowCustomization(Component):
    template = """
      <section class="flow-custom" aria-label="Customized Flow layouts">
        <div class="flow-custom__brand flow-custom__brand--cobalt">
          <c-CStack><strong>Cobalt studio</strong><span>Wide vertical rhythm</span></c-CStack>
        </div>
        <div class="flow-custom__brand flow-custom__brand--clay">
          <c-CGroup><strong>Clay archive</strong><span>Compact action spacing</span></c-CGroup>
        </div>
      </section>
    """

    css = """
      :where(.flow-custom) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        max-inline-size: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-custom__brand) {
        padding: 1rem;
        border-radius: 0.75rem;
      }

      :where(.flow-custom__brand--cobalt) {
        --cui-stack-gap: 1.35rem;
        background: light-dark(#dbe8f5, #172b40);
      }

      :where(.flow-custom__brand--clay) {
        --cui-group-gap: 0.25rem;
        background: light-dark(#f2dfd0, #3b2820);
      }

      :where(.flow-custom__brand [data-citry-ui-part="stack"], .flow-custom__brand [data-citry-ui-part="group"]) {
        padding: 0.7rem;
        border: 1px solid currentColor;
        border-radius: 0.5rem;
      }
    """


preview = FlowCustomization()

preview  # noqa: B018
