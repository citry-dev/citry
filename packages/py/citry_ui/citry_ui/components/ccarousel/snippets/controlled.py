# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledCarousel(Component):
    template = """
      <section x-data="{index:0}"><p>Slide <strong x-text="index + 1"></strong> of 3</p><c-CCarousel label="Controlled stories" $c-props="{index,onIndexChange:(next)=>index=next}"><c-CCarouselSlide value="one" label="First story"><c-CAlert>First controlled Slide</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="two" label="Second story"><c-CAlert intent="success">Second controlled Slide</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="three" label="Third story"><c-CAlert intent="warn">Third controlled Slide</c-CAlert></c-CCarouselSlide></c-CCarousel></section>
    """


preview = ControlledCarousel()
preview  # noqa: B018
