import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MultipleSelection(Component):
    template = """
      <c-CListbox label="Include signals" multiple c-value="['temperature', 'humidity']" variant="outline">
        <c-CListboxOption value="temperature">Temperature</c-CListboxOption>
        <c-CListboxOption value="humidity">Humidity</c-CListboxOption>
        <c-CListboxOption value="pressure">Pressure</c-CListboxOption>
        <c-CListboxOption value="wind">Wind speed</c-CListboxOption>
      </c-CListbox>
    """


preview = MultipleSelection()
preview  # noqa: B018
