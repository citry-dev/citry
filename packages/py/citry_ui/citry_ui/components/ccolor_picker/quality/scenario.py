"""Shared Color Picker scenario used by repository quality tools."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from citry import Citry, Component
from citry_ui import CColorSwatch


def color_picker_states_component(app: Citry) -> type[Component]:
    class CitryUiColorPickerStates(Component):
        citry = app

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "swatches": [
                    CColorSwatch("#7f56d9", "Violet"),
                    CColorSwatch("#12b76a", "Green"),
                    CColorSwatch("#f04438", "Red"),
                ],
                "quality_attrs": {
                    "data-quality-states": "native open keyboard pointer text swatch form controlled disabled readonly rtl narrow localized cleanup"
                },
            }

        template = """<section class="citry-ui-quality-stack" data-quality-color-picker-ready><h1>Color Picker states</h1><form><c-CColorPicker id="quality-color-picker" label="Brand color" name="brand" value="#7f56d9" c-swatches="swatches" c-attrs="quality_attrs" /><button type="reset">Reset</button></form></section>"""

    return CitryUiColorPickerStates


__all__ = ["color_picker_states_component"]
