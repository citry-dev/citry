import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedEditable(Component):
    template = """
      <c-CEditable
        value="Branded title" editing
        style="--cui-editable-background:#fff8eb; --cui-editable-border-color:#f79009;
               --cui-editable-focus-color:#b54708; --cui-editable-radius:1rem"
        c-input_attrs="{'aria-label':'Branded title'}"
      />
    """


preview = CustomizedEditable()
preview  # noqa: B018
