# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CColorSwatch

citry.register_library(citry_ui)


class ColorPickerSwatches(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "swatches": [
                CColorSwatch("#7f56d9", "Violet"),
                CColorSwatch("#12b76a", "Green"),
                CColorSwatch("#f04438", "Red"),
                CColorSwatch("#f79009", "Orange"),
            ]
        }

    template = '<c-CColorPicker label="Accent" c-swatches="swatches" />'


preview = ColorPickerSwatches()
preview  # noqa: B018
