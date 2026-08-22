# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselStates(Component):
    template = """
      <c-CCol gap="lg"><c-CCarousel label="Looping stories" loop><c-CCarouselSlide value="one" label="First loop Slide">Previous wraps to the end.</c-CCarouselSlide><c-CCarouselSlide value="two" label="Second loop Slide">Next wraps to the start.</c-CCarouselSlide></c-CCarousel><c-CCarousel label="Disabled stories" disabled><c-CCarouselSlide value="locked" label="Locked Slide">Owned controls are disabled.</c-CCarouselSlide></c-CCarousel></c-CCol>
    """


preview = CarouselStates()
preview  # noqa: B018
