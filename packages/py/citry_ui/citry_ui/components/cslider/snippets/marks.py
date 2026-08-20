from typing import Any

from citry import Component


class SliderMarks(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        return {"marks": {0: "Silent", 25: "Quiet", 50: "Medium", 75: "Loud", 100: "Maximum"}}

    template = """
      <c-CField>
        <c-fill name="label">Playback volume</c-fill>
        <c-fill name="default"><c-CSlider value="50" c-marks="marks" show_value="always" /></c-fill>
      </c-CField>
    """


preview = SliderMarks()
preview  # noqa: B018
