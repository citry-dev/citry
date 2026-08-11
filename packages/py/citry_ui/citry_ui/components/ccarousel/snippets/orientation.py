# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VerticalCarousel(Component):
    template = """
      <c-CCarousel label="Vertical updates" orientation="vertical" style="--cui-carousel-block-size:12rem"><c-CCarouselSlide value="morning" label="Morning update"><c-CAlert>Morning observations</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="evening" label="Evening update"><c-CAlert intent="info">Evening observations</c-CAlert></c-CCarouselSlide></c-CCarousel>
    """


preview = VerticalCarousel()
preview  # noqa: B018
