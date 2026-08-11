"""Shared Container and Grid scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def grid_container_states_component(app: Citry) -> type[Component]:
    """Create the reusable Container and Grid environment scenario."""

    class CitryUiGridContainerStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section class="citry-ui-quality-stack grid-quality" aria-labelledby="grid-quality-title">
            <h1 id="grid-quality-title">Container and Grid states</h1>

            <c-CContainer size="sm" c-attrs="{'data-quality-state': 'container-sm'}">
              Small centered Container
            </c-CContainer>
            <c-CContainer fluid c-attrs="{'data-quality-state': 'container-fluid'}">
              Fluid Container
            </c-CContainer>

            <c-CGrid sm="2" lg="4" c-attrs="{'data-quality-state': 'responsive-equal'}">
              <c-for each="item in items">
                <article class="grid-quality__cell">Specimen {{ item }}</article>
              </c-for>
            </c-CGrid>

            <c-CGrid min_col="12rem" c-attrs="{'data-quality-state': 'intrinsic'}">
              <c-for each="item in items">
                <article class="grid-quality__cell">Intrinsic {{ item }}</article>
              </c-for>
            </c-CGrid>

            <c-CGrid cols="12" c-attrs="{'data-quality-state': 'asymmetric'}">
              <c-CGridItem span="12" md="8" class_="grid-quality__cell">Main record</c-CGridItem>
              <c-CGridItem span="12" md="4" class_="grid-quality__cell">Index</c-CGridItem>
            </c-CGrid>

            <c-CGrid tag="ul" sm="2" class_="grid-quality__list" c-attrs="{'data-quality-state': 'semantic-list'}">
              <c-CGridItem tag="li">
                Silicates
                <c-CGrid cols="2" gap="xs" c-attrs="{'data-quality-state': 'nested'}">
                  <span>Quartz</span><span>Feldspar</span>
                </c-CGrid>
              </c-CGridItem>
              <c-CGridItem tag="li">Carbonates</c-CGridItem>
            </c-CGrid>

            <div class="grid-quality__narrow">
              <c-CGrid cols="2" c-attrs="{'data-quality-state': 'narrow'}">
                <span>unbreakable-geological-classification-token</span><span>Basalt</span>
              </c-CGrid>
            </div>

            <div dir="rtl" class="grid-quality__rtl">
              <c-CContainer gutter="xl" c-attrs="{'data-quality-state': 'rtl'}">
                Logical inline gutters
              </c-CContainer>
            </div>

            <div class="grid-quality__brand grid-quality__brand--copper">
              <c-CGrid cols="3"><span>Azurite</span><span>Malachite</span><span>Cuprite</span></c-CGrid>
            </div>
            <div class="grid-quality__brand grid-quality__brand--slate">
              <c-CGrid min_col="8rem"><span>Slate</span><span>Schist</span><span>Gneiss</span></c-CGrid>
            </div>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {"items": tuple(range(1, 9))}

        css = """
          :where(.grid-quality__cell, .grid-quality__list > li) {
            min-inline-size: 0;
            padding: 0.65rem;
            border: 1px solid GrayText;
            overflow-wrap: anywhere;
          }

          :where(.grid-quality__list) {
            margin: 0;
            padding: 0;
            list-style: none;
          }

          :where(.grid-quality__narrow) {
            inline-size: 10rem;
          }

          :where(.grid-quality__narrow span) {
            overflow-wrap: anywhere;
          }

          :where(.grid-quality__rtl) {
            border-inline-start: 0.25rem solid #7a5aa6;
          }

          :where(.grid-quality__brand) {
            padding: 0.75rem;
            color: var(--grid-quality-brand-foreground);
            background: var(--grid-quality-brand-background);
          }

          :where(.grid-quality__brand span) {
            padding: 0.5rem;
            border: 1px solid currentColor;
          }

          :where(.grid-quality__brand--copper) {
            --cui-grid-gap: 0.35rem;
            --grid-quality-brand-background: light-dark(#f4e5d8, #3c281e);
            --grid-quality-brand-foreground: light-dark(#4a2616, #ffe9d7);
          }

          :where(.grid-quality__brand--slate) {
            --cui-grid-gap: 1rem;
            --grid-quality-brand-background: light-dark(#e4ebef, #202d35);
            --grid-quality-brand-foreground: light-dark(#24353f, #e8f3f8);
          }
        """

    return CitryUiGridContainerStates
