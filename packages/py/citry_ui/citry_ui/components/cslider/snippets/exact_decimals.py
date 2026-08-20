from decimal import Decimal
from typing import Any

from citry import Component


class ExactDecimalSlider(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        return {
            "value": Decimal("0.30"),
            "marks": {Decimal("0.1"): "Low", Decimal("0.3"): "Target", Decimal("0.5"): "High"},
        }

    template = """
      <c-CField>
        <c-fill name="label">Opacity</c-fill>
        <c-fill name="description">Exact 0.05 steps avoid binary floating-point drift.</c-fill>
        <c-fill name="default">
          <c-CSlider c-value="value" min="0.1" max="0.5" step="0.05" c-marks="marks" show_value="always" />
        </c-fill>
      </c-CField>
    """


preview = ExactDecimalSlider()
preview  # noqa: B018
