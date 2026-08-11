import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class SelectAtAGlance(Component):
    template = """
      <c-CField>
        <c-fill name="label">Workspace</c-fill>
        <c-fill name="description">Choose where new observations belong.</c-fill>
        <c-fill name="default">
          <c-CSelect c-options="options" placeholder="Choose a workspace" value="atlas" />
        </c-fill>
      </c-CField>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CSelectOption("atlas", "Atlas research", "12 collaborators"),
                CSelectOption("aurora", "Aurora field notes", "7 collaborators"),
                CSelectOption("archive", "Archived studies", disabled=True),
            ]
        }


preview = SelectAtAGlance()
preview  # noqa: B018
