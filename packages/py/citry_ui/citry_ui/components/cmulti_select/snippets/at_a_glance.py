import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class MultiSelectAtAGlance(Component):
    template = """
      <c-CField>
        <c-fill name="label">Workspaces</c-fill>
        <c-fill name="description">Choose every workspace that should receive this observation.</c-fill>
        <c-fill name="default">
          <c-CMultiSelect c-options="options" placeholder="Choose workspaces" c-value="['atlas', 'aurora']" />
        </c-fill>
      </c-CField>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("atlas", "Atlas research", "12 collaborators"),
                CMultiSelectOption("aurora", "Aurora field notes", "7 collaborators"),
                CMultiSelectOption("archive", "Archived studies", disabled=True),
            ]
        }


preview = MultiSelectAtAGlance()
preview  # noqa: B018
