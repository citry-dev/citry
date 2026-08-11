import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisabledListbox(Component):
    template = """
      <c-CStack gap="lg">
        <c-CListbox label="Deployment region" value="eu" variant="outline">
          <c-CListboxOption value="eu">Europe</c-CListboxOption>
          <c-CListboxOption value="us" disabled>United States — unavailable</c-CListboxOption>
          <c-CListboxOption value="apac">Asia Pacific</c-CListboxOption>
        </c-CListbox>
        <c-CListbox label="Locked policy" value="strict" disabled variant="soft">
          <c-CListboxOption value="standard">Standard</c-CListboxOption>
          <c-CListboxOption value="strict">Strict</c-CListboxOption>
        </c-CListbox>
      </c-CStack>
    """


preview = DisabledListbox()
preview  # noqa: B018
