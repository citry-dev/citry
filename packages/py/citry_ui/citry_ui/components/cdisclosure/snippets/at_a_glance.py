import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureAtAGlance(Component):
    template = """
      <c-CDisclosure>
        <c-fill name="title">System requirements</c-fill>
        <c-fill name="default">
          <p>Python 3.13 or newer and 512 MB of available storage.</p>
        </c-fill>
      </c-CDisclosure>
    """


preview = DisclosureAtAGlance()
preview  # noqa: B018
