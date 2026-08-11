from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"variants": ("outline", "filled", "plain")}

    template = """
      <section class="forest-variants">
        <c-for each="variant in variants">
          <c-CField>
            <c-fill name="label">{{ variant.title() }} field note</c-fill>
            <c-fill name="default">
              <c-CTextarea
                c-name="variant"
                c-variant="variant"
                value="Bracket fungi found on the fallen birch."
                rows="3"
              />
            </c-fill>
          </c-CField>
        </c-for>
      </section>
    """

    css = """
      :where(.forest-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = TextareaVariants()

preview  # noqa: B018
