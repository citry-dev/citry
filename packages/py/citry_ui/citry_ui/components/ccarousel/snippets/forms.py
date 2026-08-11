# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselForms(Component):
    template = """
      <form><c-CCarousel label="Profile setup" c-indicators="False"><c-CCarouselSlide value="identity" label="Identity form"><c-CField><c-fill name="label">Project name</c-fill><c-fill name="default"><c-CInput name="project" /></c-fill></c-CField></c-CCarouselSlide><c-CCarouselSlide value="preferences" label="Preferences form"><c-CCheckbox name="updates">Receive updates</c-CCheckbox></c-CCarouselSlide></c-CCarousel><c-CButton type="submit">Save profile</c-CButton></form>
    """


preview = CarouselForms()
preview  # noqa: B018
