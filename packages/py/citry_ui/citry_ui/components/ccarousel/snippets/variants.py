# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselVariants(Component):
    template = """
      <c-CCol gap="lg"><c-CCarousel label="Small plain" size="sm"><c-CCarouselSlide value="small" label="Small Slide"><c-CAlert>Compact content</c-CAlert></c-CCarouselSlide></c-CCarousel><c-CCarousel label="Large surface" variant="surface" size="lg"><c-CCarouselSlide value="large" label="Large Slide"><c-CAlert intent="success">Spacious content</c-CAlert></c-CCarouselSlide></c-CCarousel></c-CCol>
    """


preview = CarouselVariants()
preview  # noqa: B018
