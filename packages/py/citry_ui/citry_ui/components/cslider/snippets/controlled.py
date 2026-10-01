from citry import Component


class ControlledRangeSlider(Component):
    template = """
      <section class="slider-example-stack">
        <c-CRangeSlider
          c-value="(20, 80)"
          :value="range" :onValueChange="(next)=>range=next"
        />
        <output v-text="`Selected ${range[0]} through ${range[1]}`">Selected 20 through 80</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            range:['20','80']
          };
        },
      });
    """
    css = ":where(.slider-example-stack){display:grid;gap:1rem;max-inline-size:32rem}"


preview = ControlledRangeSlider()
preview  # noqa: B018
