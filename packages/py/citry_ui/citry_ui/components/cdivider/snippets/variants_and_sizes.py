from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerVariantsAndSizes(Component):
    template = """
      <section class="divider-matrix">
        <c-for each="variant in variants">
          <div class="divider-matrix__row">
            <code>{{ variant }}</code>
            <c-for each="size in sizes">
              <div>
                <span>{{ size }}</span>
                <c-CDivider c-variant="variant" c-size="size" c-decorative="True" />
              </div>
            </c-for>
          </div>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Any,  # noqa: ARG002
        slots: Any,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "variants": ("solid", "dashed", "dotted"),
            "sizes": ("sm", "md", "lg"),
        }

    css = """
      :where(.divider-matrix) {
        display: grid;
        gap: 1rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-matrix__row) {
        display: grid;
        grid-template-columns: 5rem repeat(3, minmax(4rem, 1fr));
        align-items: center;
        gap: 0.75rem;
      }

      :where(.divider-matrix__row > div) {
        display: grid;
        gap: 0.35rem;
      }

      :where(.divider-matrix span) {
        color: light-dark(#475569, #cbd5e1);
        font-size: 0.72rem;
        text-align: center;
      }
    """


preview = DividerVariantsAndSizes()

preview  # noqa: B018
