from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeTextareaText(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "preserved_text": "\nFirst line after a deliberate blank.\n\nThird observation.",
            "transect_text": ("A long plain-text observation wraps visually without becoming markup: <fern> & moss."),
        }

    template = """
      <section class="forest-native">
        <c-CField>
          <c-fill name="label">Preserved blank lines</c-fill>
          <c-fill name="default">
            <c-CTextarea name="preserved" c-value="preserved_text" rows="6" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Hard-wrapped transect log</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="transect"
              wrap="hard"
              cols="32"
              c-value="transect_text"
              c-attrs="{'spellcheck': True, 'enterkeyhint': 'enter'}"
            />
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.forest-native) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeTextareaText()

preview  # noqa: B018
