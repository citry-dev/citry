import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileCaptureHints(Component):
    template = """
      <c-CGroup>
        <c-CField>
          <c-fill name="label">Take a photo</c-fill>
          <c-fill name="default">
            <c-CFileInput name="photo" accept="image/*" capture="environment" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Record a note</c-fill>
          <c-fill name="default">
            <c-CFileInput name="note" accept="audio/*" capture="user" />
          </c-fill>
        </c-CField>
      </c-CGroup>
    """


preview = FileCaptureHints()

preview  # noqa: B018
