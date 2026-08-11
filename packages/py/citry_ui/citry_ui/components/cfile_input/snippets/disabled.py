import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisabledFiles(Component):
    template = """
      <c-CStack>
        <c-CFileInput c-attrs="{'aria-label': 'Disabled picker'}" disabled />
        <fieldset disabled>
          <legend>Archived upload</legend>
          <c-CDropTarget label="Archived evidence" c-disabled="False">
            Uploads are unavailable
          </c-CDropTarget>
        </fieldset>
      </c-CStack>
    """


preview = DisabledFiles()

preview  # noqa: B018
