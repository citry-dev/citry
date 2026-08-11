from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "canopy_note": "Beech leaves moving in a light western wind.\nA woodpecker crossed the clearing twice.",
        }

    template = """
      <section class="forest-glance" aria-label="Woodland field journal">
        <c-CField>
          <c-fill name="label">Canopy observation</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="canopy"
              c-value="canopy_note"
              rows="5"
            />
          </c-fill>
          <c-fill name="description">Record light, weather, and visible wildlife.</c-fill>
        </c-CField>

        <div class="forest-glance__night" style="color-scheme: dark">
          <c-CField required invalid>
            <c-fill name="label">Nocturnal call</c-fill>
            <c-fill name="default">
              <c-CTextarea name="night_call" placeholder="Describe the sound" />
            </c-fill>
            <c-fill name="error">Add enough detail to identify the call.</c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.forest-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 54rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-glance > *) {
        padding: 1rem;
        border: 1px solid light-dark(#a9c6ae, #43634a);
        border-radius: 0.875rem;
        background: light-dark(#f4faf4, #132319);
      }

      :where(.forest-glance__night) {
        --cui-textarea-background: #17251c;
        --cui-textarea-border-color: #5f8067;
        --cui-textarea-focus-color: #91d39d;
      }
    """


preview = TextareaAtAGlance()

preview  # noqa: B018
