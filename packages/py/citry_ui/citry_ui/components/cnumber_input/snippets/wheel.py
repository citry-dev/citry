from citry import Component


class WheelNumberInput(Component):
    template = """
      <section class="number-input-example-grid">
        <c-CField>
          <c-fill name="label">Wheel remains page scrolling</c-fill>
          <c-fill name="default"><c-CNumberInput value="4" /></c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Focused wheel changes value</c-fill>
          <c-fill name="description">Explicitly enabled for this control.</c-fill>
          <c-fill name="default"><c-CNumberInput value="4" wheel /></c-fill>
        </c-CField>
      </section>
    """
    css = """
      :where(.number-input-example-grid) {
        display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem
      }
    """


preview = WheelNumberInput()
preview  # noqa: B018
