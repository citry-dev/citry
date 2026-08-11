import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListboxAtAGlance(Component):
    template = """
      <c-CListbox label="Choose a workspace" value="atlas" variant="soft">
        <c-CListboxOption value="atlas">
          <c-fill name="default">Atlas research</c-fill>
          <c-fill name="description">12 collaborators</c-fill>
          <c-fill name="end">Active</c-fill>
        </c-CListboxOption>
        <c-CListboxOption value="aurora">
          <c-fill name="default">Aurora field notes</c-fill>
          <c-fill name="description">7 collaborators</c-fill>
        </c-CListboxOption>
        <c-CListboxOption value="archive" disabled>Archived studies</c-CListboxOption>
      </c-CListbox>
    """


preview = ListboxAtAGlance()
preview  # noqa: B018
