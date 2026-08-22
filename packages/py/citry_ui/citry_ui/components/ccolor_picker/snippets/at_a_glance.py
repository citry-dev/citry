import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ColorPickerAtAGlance(Component):
    template = '<c-CColorPicker label="Brand color" value="#7f56d9" />'


preview = ColorPickerAtAGlance()
preview  # noqa: B018
