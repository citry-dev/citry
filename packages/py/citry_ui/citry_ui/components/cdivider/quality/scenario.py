"""Shared Divider scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def divider_states_component(app: Citry) -> type[Component]:
    """Create the reusable Divider state and environment scenario."""

    class CitryUiDividerStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="divider-states-title"
            data-quality-divider-ready
          >
            <h1 id="divider-states-title">Divider states</h1>
            <c-CDivider />
            <c-CDivider c-decorative="True" />

            <c-for each="variant in variants">
              <c-for each="size in sizes">
                <c-CDivider
                  c-variant="variant"
                  c-size="size"
                  c-attrs="{'data-quality-divider': f'{variant}-{size}'}"
                  c-decorative="True"
                />
              </c-for>
            </c-for>

            <c-for each="position in label_positions">
              <c-CDivider c-label_pos="position">
                {{ position }} observatory sector
              </c-CDivider>
            </c-for>

            <div class="divider-quality-row">
              <span>East</span>
              <c-CDivider orientation="vertical" />
              <span>Zenith</span>
              <c-CDivider orientation="vertical" c-decorative="True" />
              <span>West</span>
            </div>

            <c-for each="inset in insets">
              <c-CDivider c-inset="inset" c-decorative="True" />
            </c-for>

            <div class="divider-quality-narrow">
              <c-CDivider>Exceptionallylongunbrokenconstellationcatalogidentifier</c-CDivider>
            </div>
            <div dir="rtl"><c-CDivider inset="start" c-decorative="True" /></div>
            <div style="color-scheme: dark"><c-CDivider>Nested dark sky</c-CDivider></div>
            <div class="divider-quality-brand divider-quality-brand--aurora">
              <c-CDivider>Aurora brand</c-CDivider>
            </div>
            <div class="divider-quality-brand divider-quality-brand--eclipse">
              <c-CDivider variant="dotted">Eclipse brand</c-CDivider>
            </div>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {
                "variants": ("solid", "dashed", "dotted"),
                "sizes": ("sm", "md", "lg"),
                "label_positions": ("start", "center", "end"),
                "insets": ("none", "start", "end", "both"),
            }

        css = """
          :where(.divider-quality-row) {
            display: flex;
            min-block-size: 4rem;
            align-items: stretch;
            gap: 0.75rem;
          }

          :where(.divider-quality-narrow) {
            inline-size: 9rem;
          }

          :where(.divider-quality-brand) {
            padding: 1rem;
          }

          :where(.divider-quality-brand--aurora) {
            --cui-divider-color: light-dark(#0f766e, #5eead4);
            --cui-divider-label-color: light-dark(#115e59, #99f6e4);
            background: light-dark(#e6fffb, #12312f);
          }

          :where(.divider-quality-brand--eclipse) {
            --cui-divider-color: light-dark(#7c3aed, #f2b84b);
            --cui-divider-label-color: light-dark(#5b21b6, #ffe2a6);
            background: light-dark(#f5f0ff, #171421);
          }
        """

    return CitryUiDividerStates
