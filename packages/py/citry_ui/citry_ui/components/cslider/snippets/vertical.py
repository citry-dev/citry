from citry import Component


class VerticalSliders(Component):
    template = """
      <section class="vertical-slider-row">
        <c-CSlider value="30" orientation="vertical" c-input_attrs="{'aria-label':'Level'}" />
        <c-CRangeSlider c-value="(20, 70)" orientation="vertical" lower_label="Floor" upper_label="Ceiling" />
      </section>
    """
    css = ":where(.vertical-slider-row){display:flex;gap:3rem;min-block-size:14rem;align-items:center}"


preview = VerticalSliders()
preview  # noqa: B018
