# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselControls(Component):
    template = """
      <c-CStack gap="lg"><c-CCarousel label="Buttons only" c-indicators="False"><c-CCarouselSlide value="one" label="First">Previous and next controls only.</c-CCarouselSlide><c-CCarouselSlide value="two" label="Second">Second Slide.</c-CCarouselSlide></c-CCarousel><c-CCarousel label="Pickers only" c-controls="False"><c-CCarouselSlide value="alpha" label="Alpha">Choose with a named picker.</c-CCarouselSlide><c-CCarouselSlide value="beta" label="Beta">Second picker target.</c-CCarouselSlide></c-CCarousel></c-CStack>
    """


preview = CarouselControls()
preview  # noqa: B018
