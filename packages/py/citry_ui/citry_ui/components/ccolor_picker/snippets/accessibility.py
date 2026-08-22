# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CColorSwatch

citry.register_library(citry_ui)


class AccessibleColorPicker(Component):
    def template_data(self, _kwargs, _slots):
        return {"swatches": [CColorSwatch("#005ea8", "Accessible blue"), CColorSwatch("#00703c", "Accessible green")]}

    template = '<c-CColorPicker label="Published theme color" value="#005ea8" c-swatches="swatches" readonly />'


preview = AccessibleColorPicker()
preview  # noqa: B018
