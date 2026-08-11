import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarDisabled(Component):
    template = """
      <fieldset disabled>
        <legend>Unavailable editor</legend>
        <c-CToolbar label="Unavailable tools" variant="outline">
          <c-CButton>Cut</c-CButton>
          <c-CButton>Copy</c-CButton>
          <c-CButton>Paste</c-CButton>
        </c-CToolbar>
      </fieldset>
    """


preview = ToolbarDisabled()

preview  # noqa: B018
