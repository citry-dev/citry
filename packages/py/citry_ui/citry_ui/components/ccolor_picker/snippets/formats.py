# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ColorPickerFormats(Component):
    template = """<div class="color-format-grid"><c-CColorPicker label="RGB color" value="#12b76a" format="rgb" /><c-CColorPicker label="HSL color" value="#f79009" format="hsl" /></div>"""
    css = ":where(.color-format-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem}"


preview = ColorPickerFormats()
preview  # noqa: B018
