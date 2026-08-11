import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GroupedOptions(Component):
    template = """
      <c-CListbox label="Choose a destination" value="prague">
        <c-CListboxGroup label="Europe">
          <c-CListboxOption value="prague">Prague</c-CListboxOption>
          <c-CListboxOption value="lisbon">Lisbon</c-CListboxOption>
        </c-CListboxGroup>
        <c-CListboxGroup label="Asia Pacific">
          <c-CListboxOption value="kyoto">Kyoto</c-CListboxOption>
          <c-CListboxOption value="wellington">Wellington</c-CListboxOption>
        </c-CListboxGroup>
      </c-CListbox>
    """


preview = GroupedOptions()
preview  # noqa: B018
