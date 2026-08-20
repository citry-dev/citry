from decimal import Decimal
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNumberInput

citry.register_library(citry_ui)


class BasicNumberInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "python_control": CNumberInput(
                name="threshold",
                value=Decimal("2.5"),
                min=Decimal(0),
                max=Decimal(10),
                step=Decimal("0.5"),
                input_attrs={"aria-label": "Python threshold"},
            )
        }

    template = """
      <section class="number-input-demo-grid">
        <c-CField required>
          <c-fill name="label">Crates</c-fill>
          <c-fill name="description">Choose from 1 through 20.</c-fill>
          <c-fill name="default">
            <c-CNumberInput name="crates" value="2" min="1" max="20" />
          </c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_control }}</article>
      </section>
    """

    css = """
      :where(.number-input-demo-grid) {
        display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem;align-items:start
      }
      :where(.number-input-demo-grid article) { display:grid;gap:.75rem }
      :where(.number-input-demo-grid h3) { margin:0 }
    """


preview = BasicNumberInput()
preview  # noqa: B018
