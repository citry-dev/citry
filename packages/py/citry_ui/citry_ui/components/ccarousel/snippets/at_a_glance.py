# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselAtAGlance(Component):
    template = """
      <c-CCarousel label="Featured observations" variant="surface"><c-CCarouselSlide value="aurora" label="Aurora observation"><c-CCard variant="subtle"><c-fill name="header"><strong>Aurora field notes</strong></c-fill><c-fill name="default">A clear night above the northern ridge.</c-fill></c-CCard></c-CCarouselSlide><c-CCarouselSlide value="tide" label="Tide observation"><c-CCard variant="subtle"><c-fill name="header"><strong>Tide field notes</strong></c-fill><c-fill name="default">A spring tide reshaped the eastern inlet.</c-fill></c-CCard></c-CCarouselSlide></c-CCarousel>
    """


preview = CarouselAtAGlance()
preview  # noqa: B018
