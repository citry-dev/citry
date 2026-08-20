from citry import Component


class NumberInputConstraints(Component):
    template = """
      <section class="number-input-example-grid">
        <c-CField required>
          <c-fill name="label">Validate the draft</c-fill>
          <c-fill name="description">Enter a quarter step from 0 through 3.</c-fill>
          <c-fill name="default"><c-CNumberInput value="1" min="0" max="3" step="0.25" /></c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Clamp on commit</c-fill>
          <c-fill name="description">A parse-valid outside value moves to the nearest bound.</c-fill>
          <c-fill name="default"><c-CNumberInput value="1" min="0" max="3" commit_behavior="clamp" /></c-fill>
        </c-CField>
      </section>
    """
    css = """
      :where(.number-input-example-grid) {
        display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem
      }
    """


preview = NumberInputConstraints()
preview  # noqa: B018
