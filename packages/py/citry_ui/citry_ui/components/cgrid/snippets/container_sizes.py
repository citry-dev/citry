import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridContainerSizes(Component):
    template = """
      <section class="container-sizes" aria-labelledby="container-sizes-title">
        <h2 id="container-sizes-title">Atlas page widths</h2>
        <c-CContainer size="sm" class_="container-sizes__sample container-sizes__sample--sm">
          <strong>sm · 40rem maximum</strong>
          <span>Focused specimen notes</span>
        </c-CContainer>
        <c-CContainer size="md" class_="container-sizes__sample container-sizes__sample--md">
          <strong>md · 48rem maximum</strong>
          <span>Illustrated field article</span>
        </c-CContainer>
        <c-CContainer fluid class_="container-sizes__sample container-sizes__sample--fluid">
          <strong>fluid · no maximum</strong>
          <span>Full-width comparison plate</span>
        </c-CContainer>
      </section>
    """

    css = """
      :where(.container-sizes) {
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.container-sizes h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.container-sizes__sample) {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        margin-block: 0.5rem;
        padding-block: 0.65rem;
        border: 1px solid light-dark(#cbc7bb, #5c5952);
        border-radius: 0.45rem;
        font-size: 0.74rem;
      }

      :where(.container-sizes__sample span) {
        color: GrayText;
        text-align: end;
      }

      :where(.container-sizes__sample--sm) {
        border-inline-start: 0.3rem solid #b56b3f;
      }

      :where(.container-sizes__sample--md) {
        border-inline-start: 0.3rem solid #4c7a6a;
      }

      :where(.container-sizes__sample--fluid) {
        border-inline-start: 0.3rem solid #596fb1;
      }
    """


preview = GridContainerSizes()

preview  # noqa: B018
