"""Shared Alert scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def alert_states_component(app: Citry) -> type[Component]:
    """Create the reusable Alert state and environment scenario."""

    class CitryUiAlertStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack alert-quality"
            aria-labelledby="alert-states-title"
            x-data
            x-init="Alpine.store('alertQuality', {
              intent: 'info',
              variant: 'soft',
              size: 'md',
              announce: 'off',
              icon: true,
            })"
          >
            <h1 id="alert-states-title">Alert states</h1>
            <c-CAlert
              actions_label="Observation actions"
              $c-props="{
                intent: $store.alertQuality.intent,
                variant: $store.alertQuality.variant,
                size: $store.alertQuality.size,
                announce: $store.alertQuality.announce,
                icon: $store.alertQuality.icon,
              }"
            >
              <c-fill name="title">Controlled observation status</c-fill>
              <c-fill name="default">The guide camera is following the selected star.</c-fill>
              <c-fill name="actions">
                <button
                  type="button"
                  @click="$store.alertQuality.intent = 'success';
                    $store.alertQuality.announce = 'polite'"
                >
                  Mark synchronized
                </button>
                <a href="#observation-log">Open log</a>
              </c-fill>
            </c-CAlert>

            <div class="citry-ui-quality-grid">
              <c-for each="intent in intents">
                <c-CAlert c-intent="intent">
                  {{ intent }} Alert
                </c-CAlert>
              </c-for>
              <c-for each="variant in variants">
                <c-CAlert intent="warn" c-variant="variant">
                  {{ variant }} Alert
                </c-CAlert>
              </c-for>
              <c-for each="size in sizes">
                <c-CAlert c-size="size">
                  {{ size }} Alert
                </c-CAlert>
              </c-for>
              <c-CAlert icon_name="star" variant="outline">
                Fixed registered icon
              </c-CAlert>
              <c-CAlert c-icon="False">Icon hidden</c-CAlert>
              <c-CAlert announce="polite">Polite status</c-CAlert>
              <c-CAlert announce="assertive" intent="error">Assertive alert</c-CAlert>
            </div>

            <div dir="rtl">
              <c-CAlert icon_name="back" class_="alert-quality__long">
                observatoryobservatoryobservatoryobservatoryobservatory
              </c-CAlert>
            </div>
            <div class="alert-quality__dark" style="color-scheme: dark">
              <c-CAlert intent="success" variant="solid">
                Dark-scheme synchronization complete
              </c-CAlert>
            </div>
            <c-CAlert class_="alert-quality__brand" intent="warn">
              Brand-adapted weather notice
            </c-CAlert>
            <c-CAlert>
              <c-fill name="title">Nested Alert container</c-fill>
              <c-fill name="default">
                <c-CAlert size="sm" intent="success">
                  Nested instrument check complete
                </c-CAlert>
              </c-fill>
            </c-CAlert>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {
                "intents": ("info", "success", "warn", "error"),
                "variants": ("soft", "solid", "outline"),
                "sizes": ("sm", "md", "lg"),
            }

        css = """
          :where(.alert-quality__dark) {
            --cui-alert-radius: 1rem;
          }

          :where(.alert-quality__brand[data-citry-ui-part="alert"]) {
            --cui-alert-background: light-dark(#fff8df, #30270b);
            --cui-alert-border-color: light-dark(#d99d13, #ffd166);
            --cui-alert-icon-color: light-dark(#9a6700, #ffd166);
          }

          :where(.alert-quality__long) {
            inline-size: 9rem;
          }
        """

    return CitryUiAlertStates
