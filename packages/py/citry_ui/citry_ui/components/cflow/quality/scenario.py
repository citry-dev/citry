"""Shared Flow layout scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def flow_states_component(app: Citry) -> type[Component]:
    """Create the reusable Col and Row environment scenario."""

    class CitryUiFlowStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section class="citry-ui-quality-stack" aria-labelledby="flow-states-title">
            <h1 id="flow-states-title">Col and Row states</h1>

            <c-for each="gap in gaps">
              <c-CCol c-gap="gap" c-attrs="{'data-quality-gap': gap}">
                <span>Clay</span>
                <span>Slip</span>
              </c-CCol>
            </c-for>

            <c-for each="justify in justifies">
              <c-CRow
                c-justify="justify"
                c-attrs="{'data-quality-justify': justify}"
              >
                <span>Shape</span>
                <span>Dry</span>
                <span>Fire</span>
              </c-CRow>
            </c-for>

            <c-CRow class_="flow-quality-narrow" gap="xs">
              <span>Long porcelain preparation</span>
              <span>Reduction firing schedule</span>
              <span>Transparent celadon glaze</span>
            </c-CRow>

            <c-CCol tag="section" gap="lg">
              <h2>Nested kiln plan</h2>
              <c-CRow align="baseline" justify="between">
                <strong>1,280°C</strong>
                <small>12 hour cycle</small>
              </c-CRow>
            </c-CCol>

            <c-CRow tag="nav" reverse c-attrs="{'aria-label': 'Studio sections'}">
              <a href="#clay">Clay</a>
              <a href="#glaze">Glaze</a>
            </c-CRow>

            <div dir="rtl">
              <c-CRow justify="between">
                <span>الطين</span>
                <span>التزجيج</span>
              </c-CRow>
            </div>

            <div class="flow-quality-brand flow-quality-brand--chalk">
              <c-CCol><span>Chalk studio</span><span>Quiet spacing</span></c-CCol>
            </div>
            <div class="flow-quality-brand flow-quality-brand--ink">
              <c-CRow><span>Ink studio</span><span>Compact tools</span></c-CRow>
            </div>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {
                "gaps": ("0", "xs", "sm", "md", "lg", "xl"),
                "justifies": ("start", "center", "end", "between", "around", "evenly"),
            }

        css = """
          :where([data-quality-gap], [data-quality-justify]) {
            min-block-size: 3rem;
            padding: 0.5rem;
            border: 1px solid GrayText;
          }

          :where(.flow-quality-narrow) {
            max-inline-size: 12rem;
          }

          :where(.flow-quality-narrow > span) {
            padding: 0.25rem;
            background: light-dark(#ead8bd, #4a3d31);
          }

          :where(.flow-quality-brand) {
            padding: 1rem;
          }

          :where(.flow-quality-brand--chalk) {
            --cui-col-gap: 1.125rem;
            background: light-dark(#fff8eb, #2e281f);
            color: light-dark(#392d21, #f8ead7);
          }

          :where(.flow-quality-brand--ink) {
            --cui-row-gap: 0.375rem;
            background: light-dark(#e7f0f6, #16242e);
            color: light-dark(#172d3b, #e6f2f8);
          }
        """

    return CitryUiFlowStates
