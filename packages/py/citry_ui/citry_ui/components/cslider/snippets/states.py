from citry import Component


class SliderStates(Component):
    template = """
      <section class="slider-state-grid">
        <c-CSlider value="30" variant="solid" size="sm" c-input_attrs="{'aria-label':'Small solid'}" />
        <c-CSlider value="50" variant="subtle" show_value="always" c-input_attrs="{'aria-label':'Subtle'}" />
        <c-CSlider value="70" size="lg" readonly c-input_attrs="{'aria-label':'Readonly'}" />
        <c-CSlider value="90" disabled invalid c-input_attrs="{'aria-label':'Disabled invalid'}" />
      </section>
    """
    css = ":where(.slider-state-grid){display:grid;gap:1.5rem;max-inline-size:36rem}"


preview = SliderStates()
preview  # noqa: B018
