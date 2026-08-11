from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"sizes": ("sm", "md", "lg")}

    template = """
      <section class="forest-sizes">
        <c-for each="size in sizes">
          <c-CField>
            <c-fill name="label">{{ size.upper() }} specimen note</c-fill>
            <c-fill name="default">
              <c-CTextarea
                c-name="size"
                c-size="size"
                value="Three fox prints beside the stream crossing."
                rows="3"
              />
            </c-fill>
          </c-CField>
        </c-for>
      </section>
    """

    css = """
      :where(.forest-sizes) {
        display: grid;
        gap: 1rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = TextareaSizes()

preview  # noqa: B018
