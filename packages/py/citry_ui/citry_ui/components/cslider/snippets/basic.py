from decimal import Decimal
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CSlider

citry.register_library(citry_ui)


class BasicSlider(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "python_slider": CSlider(
                value=Decimal("0.5"),
                min=Decimal(0),
                max=Decimal(1),
                step=Decimal("0.1"),
                input_attrs={"aria-label": "Python opacity"},
            )
        }

    template = """
      <section class="slider-example-grid">
        <c-CField>
          <c-fill name="label">Volume</c-fill>
          <c-fill name="description">Use arrow keys for one-percent steps.</c-fill>
          <c-fill name="default"><c-CSlider name="volume" value="40" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_slider }}</article>
      </section>
    """
    css = """
      :where(.slider-example-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1.5rem}
      :where(.slider-example-grid article){display:grid;gap:.75rem}:where(.slider-example-grid h3){margin:0}
    """


preview = BasicSlider()
preview  # noqa: B018
