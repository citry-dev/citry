# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselCards(Component):
    template = """
      <c-CCarousel label="Research stories"><c-CCarouselSlide value="forest" label="Forest canopy story"><c-CCard variant="elevated"><c-fill name="header"><c-CBadge intent="success">Canopy</c-CBadge><h3>Listening above the forest floor</h3></c-fill><c-fill name="default">Sensors reveal the canopy's changing rhythm.</c-fill></c-CCard></c-CCarouselSlide><c-CCarouselSlide value="coast" label="Coastal story"><c-CCard variant="elevated"><c-fill name="header"><c-CBadge intent="primary">Coast</c-CBadge><h3>Mapping a moving shoreline</h3></c-fill><c-fill name="default">Field teams compare a decade of tidal change.</c-fill></c-CCard></c-CCarouselSlide></c-CCarousel>
    """


preview = CarouselCards()
preview  # noqa: B018
