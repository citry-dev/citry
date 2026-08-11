from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicDividers(Component):
    template = """
      <section class="divider-basic">
        <article>
          <h2>Orion Nebula</h2>
          <p>A luminous stellar nursery around 1,300 light-years away.</p>
        </article>
        <c-CDivider />
        {{ python_divider }}
        <article>
          <h2>Lagoon Nebula</h2>
          <p>Dark dust lanes cross a glowing cloud in Sagittarius.</p>
        </article>
      </section>
    """

    def template_data(
        self,
        kwargs: Any,  # noqa: ARG002
        slots: Any,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"python_divider": citry_ui.CDivider(variant="dotted")}

    css = """
      :where(.divider-basic) {
        display: grid;
        gap: 1rem;
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-basic h2, .divider-basic p) {
        margin: 0;
      }

      :where(.divider-basic h2) {
        font-size: 1rem;
      }
    """


preview = BasicDividers()

preview  # noqa: B018
