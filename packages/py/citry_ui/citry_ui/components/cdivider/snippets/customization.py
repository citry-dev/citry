import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerCustomization(Component):
    template = """
      <section class="divider-themes">
        <div class="divider-themes__aurora">
          <c-CDivider>Polar observatory</c-CDivider>
        </div>
        <div class="divider-themes__eclipse">
          <c-CDivider variant="dotted">Eclipse watch</c-CDivider>
        </div>
      </section>
    """
    css = """
      :where(.divider-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
        gap: 1rem;
        max-inline-size: 40rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-themes > div) {
        padding: 1.25rem;
        border-radius: 0.75rem;
      }

      :where(.divider-themes__aurora) {
        --cui-divider-color: #138a7b;
        --cui-divider-label-color: #12584f;
        --cui-divider-thickness: 2px;
        background: #e7faf6;
      }

      :where(.divider-themes__eclipse) {
        color-scheme: dark;
        --cui-divider-color: #f2b84b;
        --cui-divider-label-color: #ffe2a6;
        --cui-divider-label-font-weight: 750;
        background: #171421;
      }

      :where(.divider-themes [data-citry-ui-part="label"]) {
        letter-spacing: 0.03em;
      }
    """


preview = DividerCustomization()

preview  # noqa: B018
