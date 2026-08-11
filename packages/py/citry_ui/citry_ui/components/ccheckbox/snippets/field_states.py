import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxFieldStates(Component):
    template = """
      <section class="checkbox-field-states">
        <c-CField required>
          <c-fill name="label">Seed-bank handling agreement</c-fill>
          <c-fill name="default">
            <c-CCheckbox name="agreement" value="accepted" />
          </c-fill>
          <c-fill name="description">Required before opening a preserved packet.</c-fill>
          <c-fill name="error">Accept the handling agreement.</c-fill>
        </c-CField>

        <c-CField invalid>
          <c-fill name="label">Provenance confirmed</c-fill>
          <c-fill name="default">
            <c-CCheckbox name="provenance" />
          </c-fill>
          <c-fill name="error">Confirm the collector and location first.</c-fill>
        </c-CField>

        <c-CField disabled>
          <c-fill name="label">Destructive pollen sampling</c-fill>
          <c-fill name="default">
            <c-CCheckbox name="pollen" />
          </c-fill>
          <c-fill name="description">Unavailable for this rare specimen.</c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.checkbox-field-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1.25rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-field-states > [data-citry-ui-part="field"]) {
        align-content: start;
        padding: 1rem;
        border: 1px solid light-dark(#c5d5c1, #3e5541);
        border-radius: 0.75rem;
        background: Canvas;
      }
    """


preview = CheckboxFieldStates()

preview  # noqa: B018
