import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableAtAGlance(Component):
    template = """
      <c-CField>
        <c-fill name="label">Project name</c-fill>
        <c-fill name="description">Use the pencil to rename this project in place.</c-fill>
        <c-fill name="default">
          <c-CEditable value="Aurora atlas" name="project-name" />
        </c-fill>
      </c-CField>
    """


preview = EditableAtAGlance()
preview  # noqa: B018
