# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeColorForm(Component):
    template = """<form><c-CColorPicker label="Profile color" name="profile_color" value="#1570ef" /><button type="reset">Reset</button><button type="submit">Save</button></form>"""


preview = NativeColorForm()
preview  # noqa: B018
