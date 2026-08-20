from citry import Component


class RangeSliderExample(Component):
    template = """
      <c-CField>
        <c-fill name="label">Price range</c-fill>
        <c-fill name="description">Lower and upper values stay at least 10 apart.</c-fill>
        <c-fill name="default">
          <c-CRangeSlider name="price" c-value="(20, 80)" c-min_steps_between_thumbs="10" />
        </c-fill>
      </c-CField>
    """


preview = RangeSliderExample()
preview  # noqa: B018
