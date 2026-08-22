import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileInputAtAGlance(Component):
    template = """
      <c-CCol gap="lg">
        <c-CField>
          <c-fill name="label">Profile photo</c-fill>
          <c-fill name="default"><c-CFileInput name="photo" accept="image/*" /></c-fill>
        </c-CField>
        <c-CDropTarget label="Project files" name="project_files" multiple>
          Drop files here or browse from this device
        </c-CDropTarget>
      </c-CCol>
    """


preview = FileInputAtAGlance()

preview  # noqa: B018
