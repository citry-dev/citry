from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerInsets(Component):
    template = """
      <section class="divider-insets">
        <c-for each="inset in insets">
          <div>
            <span>{{ inset }}</span>
            <c-CDivider c-inset="inset" c-decorative="True" />
          </div>
        </c-for>
        <div dir="rtl">
          <span>start in RTL</span>
          <c-CDivider inset="start" c-decorative="True" />
        </div>
      </section>
    """

    def template_data(
        self,
        kwargs: Any,  # noqa: ARG002
        slots: Any,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"insets": ("none", "start", "end", "both")}

    css = """
      :where(.divider-insets) {
        display: grid;
        gap: 1rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-insets > div) {
        display: grid;
        gap: 0.35rem;
        padding: 0.5rem;
        border-inline: 1px dashed light-dark(#94a3b8, #64748b);
      }

      :where(.divider-insets span) {
        font-size: 0.75rem;
      }
    """


preview = DividerInsets()

preview  # noqa: B018
