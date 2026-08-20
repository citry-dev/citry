from citry import Component


class SliderForm(Component):
    template = """
      <form
        x-data="{result:'Submit to inspect values'}"
        @submit.prevent="result=JSON.stringify(Array.from(new FormData($event.target).entries()))"
        class="slider-example-stack"
      >
        <c-CField>
          <c-fill name="label">Budget</c-fill>
          <c-fill name="default">
            <c-CRangeSlider lower_name="minimum" upper_name="maximum" c-value="(25, 75)" />
          </c-fill>
        </c-CField>
        <div><button type="submit">Submit</button> <button type="reset">Reset</button></div>
        <output x-text="result">Submit to inspect values</output>
      </form>
    """
    css = ":where(.slider-example-stack){display:grid;gap:1rem;max-inline-size:32rem}"


preview = SliderForm()
preview  # noqa: B018
