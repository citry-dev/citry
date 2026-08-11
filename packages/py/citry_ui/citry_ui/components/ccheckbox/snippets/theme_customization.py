import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxThemeCustomization(Component):
    template = """
      <section class="checkbox-themes">
        <article class="checkbox-themes__conservatory">
          <p>Sunlit conservatory</p>
          <c-CCheckbox checked>
            Mist the cloud-forest ferns
          </c-CCheckbox>
          <c-CCheckbox variant="outline">
            Rotate the orchid trays
          </c-CCheckbox>
        </article>
        <article class="checkbox-themes__night" style="color-scheme: dark">
          <p>Moonlit field station</p>
          <c-CCheckbox checked>
            Log nocturnal flower opening
          </c-CCheckbox>
          <c-CCheckbox indeterminate variant="outline">
            Review moth-pollination images
          </c-CCheckbox>
        </article>
      </section>
    """

    css = """
      :where(.checkbox-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-themes article) {
        display: grid;
        align-content: start;
        gap: 0.9rem;
        padding: 1.1rem;
        border-radius: 1rem;
      }

      :where(.checkbox-themes article > p) {
        margin: 0;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.checkbox-themes__conservatory) {
        --cui-checkbox-active-color: #24734a;
        --cui-checkbox-focus-color: #4b9b69;
        --cui-checkbox-radius: 0.45rem;

        border: 1px solid #a9cbb3;
        background: #f3fbf4;
        color: #173c25;
      }

      :where(.checkbox-themes__night) {
        --cui-checkbox-active-color: #c4a7ff;
        --cui-checkbox-indicator-color: #22173d;
        --cui-checkbox-focus-color: #e2d5ff;
        --cui-checkbox-description-color: #cbbde7;

        border: 1px solid #584873;
        background: #191426;
        color: #f2ecff;
      }

      :where(.checkbox-themes__night [data-citry-ui-part="input"]) {
        border-width: 2px;
      }
    """


preview = CheckboxThemeCustomization()

preview  # noqa: B018
