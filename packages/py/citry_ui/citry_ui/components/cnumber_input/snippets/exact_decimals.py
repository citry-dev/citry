from citry import Component


class ExactDecimalNumberInput(Component):
    template = """
      <section class="number-input-example-stack">
        <c-CField>
          <c-fill name="label">Calibration offset</c-fill>
          <c-fill name="description">Exact increments of 0.0001.</c-fill>
          <c-fill name="default">
            <c-CNumberInput name="offset" value="0.1001" min="-1" max="1" step="0.0001" />
          </c-fill>
        </c-CField>
        <p>The submitted enhanced value remains the exact string <code>0.1001</code>.</p>
      </section>
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:28rem}"


preview = ExactDecimalNumberInput()
preview  # noqa: B018
