import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InputSizesAndLayout(Component):
    template = """
      <section class="shore-layout">
        <c-CField density="compact">
          <c-fill name="label">
            Small marker code
          </c-fill>
          <c-fill name="default">
            <c-CInput name="small" value="A-14" size="sm" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Medium marker code
          </c-fill>
          <c-fill name="default">
            <c-CInput name="medium" value="B-27" size="md" />
          </c-fill>
        </c-CField>
        <c-CField density="comfortable">
          <c-fill name="label">
            Large marker code
          </c-fill>
          <c-fill name="default">
            <c-CInput name="large" value="C-08" size="lg" />
          </c-fill>
        </c-CField>
        <c-CField orientation="horizontal">
          <c-fill name="label">
            Long observation label
          </c-fill>
          <c-fill name="default">
            <c-CInput name="long" placeholder="Describe the waterline" />
          </c-fill>
          <c-fill name="description">
            Horizontal Fields return to one column on narrow viewports.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-layout) {
        display: grid;
        gap: 1.25rem;
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = InputSizesAndLayout()

preview  # noqa: B018
