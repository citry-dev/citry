"""Shared Badge scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def badge_states_component(app: Citry) -> type[Component]:
    """Create the reusable Badge state and environment scenario."""

    class CitryUiBadgeStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section class="citry-ui-quality-stack" aria-labelledby="badge-states-title">
            <h1 id="badge-states-title">Badge states</h1>
            <div class="citry-ui-quality-grid">
              <c-for each="intent in intents">
                <c-for each="variant in variants">
                  <c-CBadge c-intent="intent" c-variant="variant">
                    {{ intent }} {{ variant }}
                  </c-CBadge>
                </c-for>
              </c-for>
            </div>
            <c-CGroup align="baseline">
              <c-for each="size in sizes">
                <c-CBadge c-size="size" shape="pill">{{ size }} · 12</c-CBadge>
              </c-for>
            </c-CGroup>
            <c-CBadge intent="success">
              <c-fill name="start"><c-CIcon name="check" /></c-fill>
              <c-fill name="default">Verified specimen</c-fill>
              <c-fill name="end"><c-CIcon name="leaf" /></c-fill>
            </c-CBadge>
            <div class="badge-quality-narrow">
              <c-CBadge>Exceptionallylongunbrokenspecimencatalogidentifier</c-CBadge>
            </div>
            <div dir="rtl"><c-CBadge intent="primary">عينة موثقة</c-CBadge></div>
            <div style="color-scheme: dark"><c-CBadge variant="solid">Nested dark</c-CBadge></div>
            <div class="badge-quality-brand badge-quality-brand--quartz">
              <c-CBadge>Quartz brand</c-CBadge>
            </div>
            <div class="badge-quality-brand badge-quality-brand--basalt">
              <c-CBadge variant="outline">Basalt brand</c-CBadge>
            </div>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {
                "intents": ("neutral", "primary", "success", "warn", "danger"),
                "variants": ("soft", "solid", "outline"),
                "sizes": ("sm", "md", "lg"),
            }

        css = """
          :where(.badge-quality-narrow) {
            inline-size: 9rem;
          }

          :where(.badge-quality-brand) {
            padding: 1rem;
          }

          :where(.badge-quality-brand--quartz) {
            --cui-badge-background: #f0e7ff;
            --cui-badge-foreground: #4c1d75;
            --cui-badge-radius: 0.2rem;
            background: #faf7ff;
          }

          :where(.badge-quality-brand--basalt) {
            color-scheme: dark;
            --cui-badge-background: #1e2930;
            --cui-badge-foreground: #d7edf2;
            --cui-badge-border-color: #72a8b5;
            --cui-badge-radius: 999px;
            background: #10171b;
          }
        """

    return CitryUiBadgeStates
