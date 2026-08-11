"""Shared Carousel scenario used by repository quality tools."""

# ruff: noqa: E501

from __future__ import annotations

from citry import Citry, Component


def carousel_states_component(app: Citry) -> type[Component]:
    class CitryUiCarouselStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-carousel-ready>
            <h1>Carousel states</h1>
            <c-CCarousel label="Featured stories" variant="surface"><c-CCarouselSlide value="aurora" label="Aurora story"><c-CCard variant="subtle"><c-fill name="default">Aurora field report</c-fill></c-CCard></c-CCarouselSlide><c-CCarouselSlide value="tide" label="Tide story"><c-CCard variant="subtle"><c-fill name="default">Tide field report</c-fill></c-CCard></c-CCarouselSlide><c-CCarouselSlide value="forest" label="Forest story"><c-CCard variant="subtle"><c-fill name="default">Forest field report</c-fill></c-CCard></c-CCarouselSlide></c-CCarousel>
            <div dir="rtl"><c-CCarousel label="RTL stories" size="lg" loop><c-CCarouselSlide value="rtl-one" label="القصة الأولى"><c-CAlert>الملاحظة الأولى</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="rtl-two" label="القصة الثانية"><c-CAlert intent="info">الملاحظة الثانية</c-CAlert></c-CCarouselSlide></c-CCarousel></div>
            <c-CCarousel label="Vertical stories" orientation="vertical" size="sm" style="--cui-carousel-block-size:10rem"><c-CCarouselSlide value="vertical-one" label="First vertical Slide">First</c-CCarouselSlide><c-CCarouselSlide value="vertical-two" label="Second vertical Slide">Second</c-CCarouselSlide></c-CCarousel>
            <c-CCarousel label="Static disabled story" c-disabled="True" c-controls="False" c-indicators="False" c-draggable="False"><c-CCarouselSlide value="static" label="Static story">Static disabled content</c-CCarouselSlide></c-CCarousel>
          </section>
        """

    return CitryUiCarouselStates
