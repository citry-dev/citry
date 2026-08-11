"""Shared Card scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def card_states_component(app: Citry) -> type[Component]:
    """Create the reusable Card anatomy, environment, and composition scenario."""

    class CitryUiCardStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section class="citry-ui-quality-stack" aria-labelledby="card-states-title">
            <h1 id="card-states-title">Card states</h1>
            <div class="citry-ui-quality-grid">
              <c-CCard><c-fill name="default">Body-only Card</c-fill></c-CCard>
              <c-CCard variant="outline"><c-fill name="header"><h2>Header-only Card</h2></c-fill></c-CCard>
              <c-for each="variant in variants">
                <c-CCard c-variant="variant">
                  <c-fill name="header"><h2>{{ variant }} Card</h2></c-fill>
                  <c-fill name="default">Complete static surface treatment.</c-fill>
                </c-CCard>
              </c-for>
              <c-for each="size in sizes">
                <c-CCard c-size="size" variant="outline">
                  <c-fill name="header"><h2>{{ size }} Card</h2></c-fill>
                  <c-fill name="default">Size changes spacing only.</c-fill>
                </c-CCard>
              </c-for>
            </div>

            <c-CCard
              variant="outline"
              c-header_actions_attrs="{'role': 'group', 'aria-label': 'Header actions'}"
              c-actions_attrs="{'role': 'group', 'aria-label': 'Footer actions'}"
            >
              <c-fill name="media"><div class="card-quality-media">Media</div></c-fill>
              <c-fill name="header"><h2>Complete anatomy</h2></c-fill>
              <c-fill name="header_actions"><c-CButton size="sm">Save</c-CButton></c-fill>
              <c-fill name="default">
                Header, body, footer, actions, and a deliberately long unbroken value:
                abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz.
              </c-fill>
              <c-fill name="footer">Footer metadata</c-fill>
              <c-fill name="actions">
                <c-CButton size="sm">Primary</c-CButton>
                <c-CButton size="sm" variant="outline">Secondary</c-CButton>
              </c-fill>
            </c-CCard>

            <div class="card-quality-brand card-quality-brand--linen">
              <c-CCard><c-fill name="header"><h2>Linen brand</h2></c-fill></c-CCard>
            </div>
            <div class="card-quality-brand card-quality-brand--studio">
              <c-CCard variant="outline"><c-fill name="header"><h2>Studio brand</h2></c-fill></c-CCard>
            </div>
            <div dir="rtl">
              <c-CCard variant="subtle">
                <c-fill name="header"><h2>بطاقة من اليمين إلى اليسار</h2></c-fill>
                <c-fill name="actions"><c-CButton size="sm">متابعة</c-CButton></c-fill>
              </c-CCard>
            </div>
            <div style="color-scheme: dark">
              <c-CCard><c-fill name="default">Nested dark scheme</c-fill></c-CCard>
            </div>
            <c-CCard variant="outline">
              <c-fill name="header"><h2>Outer Card</h2></c-fill>
              <c-fill name="default">
                <c-CCard variant="subtle"><c-fill name="default">Nested Card</c-fill></c-CCard>
              </c-fill>
            </c-CCard>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {
                "variants": ("elevated", "outline", "subtle"),
                "sizes": ("sm", "md", "lg"),
            }

        css = """
          :where(.card-quality-media) {
            display: grid;
            place-items: center;
            min-block-size: 7rem;
            background: linear-gradient(135deg, #b88758, #768e6d);
            color: #ffffff;
          }

          :where(.card-quality-brand) {
            padding: 1rem;
          }

          :where(.card-quality-brand--linen) {
            --cui-card-background: #fffaf0;
            --cui-card-foreground: #3d3328;
            --cui-card-radius: 1.1rem;
            background: #efe4d0;
          }

          :where(.card-quality-brand--studio) {
            color-scheme: dark;
            --cui-card-background: #182235;
            --cui-card-foreground: #e7eefc;
            --cui-card-border-color: #607aa5;
            --cui-card-radius: 0.35rem;
            background: #0d1421;
          }
        """

    return CitryUiCardStates
