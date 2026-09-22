# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledCarousel(Component):
    template = """
      <section ><p>Slide <strong v-text="index + 1"></strong> of 3</p><c-CCarousel label="Controlled stories" :index="index" :onIndexChange="(next)=>index=next"><c-CCarouselSlide value="one" label="First story"><c-CAlert>First controlled Slide</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="two" label="Second story"><c-CAlert intent="success">Second controlled Slide</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="three" label="Third story"><c-CAlert intent="warn">Third controlled Slide</c-CAlert></c-CCarouselSlide></c-CCarousel></section>
    """
    js = """
      $component({
        data() {
          return {
            index:0
          };
        },
      });
    """


preview = ControlledCarousel()
preview  # noqa: B018
