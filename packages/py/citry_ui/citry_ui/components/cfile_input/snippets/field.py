import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileInputField(Component):
    template = """
      <c-CField required>
        <c-fill name="label">Supporting document</c-fill>
        <c-fill name="default">
          <c-CFileInput name="document" accept="application/pdf" />
        </c-fill>
        <c-fill name="description">Choose one PDF for review.</c-fill>
        <c-fill name="error">Choose a supporting document.</c-fill>
      </c-CField>
    """


preview = FileInputField()

preview  # noqa: B018
