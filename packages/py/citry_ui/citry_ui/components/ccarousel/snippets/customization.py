# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomCarousel(Component):
    template = """
      <c-CCarousel label="Aurora stories" class_="aurora-carousel" variant="surface"><c-CCarouselSlide value="ridge" label="Northern ridge"><c-CAlert intent="info">The northern ridge at blue hour.</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="lake" label="Glacial lake"><c-CAlert intent="success">Reflections on the glacial lake.</c-CAlert></c-CCarouselSlide></c-CCarousel>
    """
    css = """
      .aurora-carousel { --cui-carousel-radius:1.25rem; --cui-carousel-indicator-active-color:#7c3aed; --cui-carousel-control-background:#ede9fe; }
    """


preview = CustomCarousel()
preview  # noqa: B018
