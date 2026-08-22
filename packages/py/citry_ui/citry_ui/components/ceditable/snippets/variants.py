import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableVariants(Component):
    template = """
      <c-CCol>
        <c-CEditable value="Small outline" variant="outline" size="sm" />
        <c-CEditable value="Medium filled" variant="filled" />
        <c-CEditable value="Large plain" variant="plain" size="lg" />
      </c-CCol>
    """


preview = EditableVariants()
preview  # noqa: B018
