import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class KeyboardListbox(Component):
    template = """
      <c-CListbox label="Jump to a city" value="brno" loop variant="outline">
        <c-CListboxOption value="brno">Brno</c-CListboxOption>
        <c-CListboxOption value="budapest">Budapest</c-CListboxOption>
        <c-CListboxOption value="krakow">Kraków</c-CListboxOption>
        <c-CListboxOption value="prague">Prague</c-CListboxOption>
        <c-CListboxOption value="vienna">Vienna</c-CListboxOption>
      </c-CListbox>
    """


preview = KeyboardListbox()
preview  # noqa: B018
