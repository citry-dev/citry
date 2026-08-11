import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListCustomization(Component):
    template = """
      <c-CList class_="violet-list" label="Nebula catalog" variant="surface">
        <c-CListItem href="/nebula/orion" c-current="True">Orion Nebula</c-CListItem>
        <c-CListItem href="/nebula/lagoon">Lagoon Nebula</c-CListItem>
      </c-CList>
    """
    css = """
      :where(.violet-list) {
        --cui-list-current-background: light-dark(#ede9fe, #4c1d95);
        --cui-list-radius: 1rem;
      }
    """


preview = ListCustomization()
preview  # noqa: B018
