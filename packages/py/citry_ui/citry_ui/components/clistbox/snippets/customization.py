import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedListbox(Component):
    css = """
      .copper-listbox {
        --cui-listbox-radius: 1.1rem;
        --cui-listbox-selected-background: light-dark(#7c2d12, #fed7aa);
        --cui-listbox-selected-foreground: light-dark(#fff7ed, #431407);
        --cui-listbox-border-color: light-dark(#c2410c, #fdba74);
        --cui-listbox-option-padding: 0.7rem 0.8rem;
      }
    """
    template = """
      <c-CListbox label="Finish" value="copper" class_="copper-listbox" variant="outline">
        <c-CListboxOption value="copper">
          <c-fill name="start"><span aria-hidden="true">◆</span></c-fill>
          <c-fill name="default">Burnished copper</c-fill>
          <c-fill name="description">Warm and tactile</c-fill>
        </c-CListboxOption>
        <c-CListboxOption value="slate">Deep slate</c-CListboxOption>
        <c-CListboxOption value="linen">Soft linen</c-CListboxOption>
      </c-CListbox>
    """


preview = CustomizedListbox()
preview  # noqa: B018
