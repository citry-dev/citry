from decimal import Decimal
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CRating

citry.register_library(citry_ui)

# ruff: noqa: E501 - template and CSS lines stay readable in public source examples


class BasicRating(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"python_rating": CRating(label="Python-composed rating", value=Decimal("4.0"))}

    template = """
      <section class="rating-demo-grid">
        <c-CField required>
          <c-fill name="label">Product rating</c-fill>
          <c-fill name="description">Choose one through five stars.</c-fill>
          <c-fill name="default"><c-CRating name="rating" value="3" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_rating }}</article>
      </section>
    """
    css = """
      :where(.rating-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1.25rem}
      :where(.rating-demo-grid article){display:grid;align-content:start;gap:.75rem}:where(.rating-demo-grid h3){margin:0}
    """


preview = BasicRating()
preview  # noqa: B018
