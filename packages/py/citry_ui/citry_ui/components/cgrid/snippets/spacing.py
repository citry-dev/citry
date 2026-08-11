import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridSpacing(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="grid-spacing" aria-labelledby="grid-spacing-title">
        <h2 id="grid-spacing-title">Spacing scale</h2>
        <c-CGrid sm="2" gap="lg">
          <c-for each="gap in gaps">
            <article class="grid-spacing__example">
              <strong>gap={{ gap }}</strong>
              <c-CGrid cols="3" c-gap="gap">
                <span></span><span></span><span></span>
              </c-CGrid>
            </article>
          </c-for>
        </c-CGrid>
        <c-CContainer gutter="xl" class_="grid-spacing__gutter">
          Container gutter=xl keeps this note away from both inline edges.
        </c-CContainer>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"gaps": ("0", "sm", "md", "xl")}

    css = """
      :where(.grid-spacing) {
        max-inline-size: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.grid-spacing h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.grid-spacing__example) {
        padding: 0.7rem;
        border: 1px solid light-dark(#d4d0c5, #56534c);
        border-radius: 0.5rem;
        font-size: 0.7rem;
      }

      :where(.grid-spacing__example strong) {
        display: block;
        margin-block-end: 0.45rem;
      }

      :where(.grid-spacing__example span) {
        min-block-size: 1.8rem;
        border-radius: 0.25rem;
        background: light-dark(#d1e3dd, #285044);
      }

      :where(.grid-spacing__gutter) {
        margin-block-start: 1rem;
        padding-block: 0.65rem;
        border-block: 1px dashed light-dark(#8d7662, #b9a28d);
        background: light-dark(#f9f3ea, #30271f);
        font-size: 0.74rem;
      }
    """


preview = GridSpacing()

preview  # noqa: B018
