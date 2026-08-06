import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InputVariants(Component):
    template = """
      <section class="shore-grid">
        <c-CField>
          <c-fill name="label">
            Outline
          </c-fill>
          <c-fill name="default">
            <c-CInput name="outline" value="Rocky shelf" variant="outline" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Filled
          </c-fill>
          <c-fill name="default">
            <c-CInput name="filled" value="Kelp channel" variant="filled" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Plain
          </c-fill>
          <c-fill name="default">
            <c-CInput name="plain" value="Sand basin" variant="plain" />
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = InputVariants()

preview  # noqa: B018
