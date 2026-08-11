import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SingleSelection(Component):
    template = """
      <c-CListbox label="Density" value="comfortable" mandatory variant="outline">
        <c-CListboxOption value="compact">Compact</c-CListboxOption>
        <c-CListboxOption value="comfortable">Comfortable</c-CListboxOption>
        <c-CListboxOption value="spacious">Spacious</c-CListboxOption>
      </c-CListbox>
    """


preview = SingleSelection()
preview  # noqa: B018
