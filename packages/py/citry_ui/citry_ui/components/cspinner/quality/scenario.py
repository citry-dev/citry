"""Shared Spinner scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def spinner_states_component(app: Citry) -> type[Component]:
    """Create the reusable Spinner state and environment scenario."""

    class CitryUiSpinnerStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section class="citry-ui-quality-stack" aria-labelledby="spinner-states-title">
            <h1 id="spinner-states-title">Spinner states</h1>
            <div class="citry-ui-quality-grid">
              <c-for each="intent in intents">
                <c-CRow>
                  <c-CSpinner c-label="f'{intent} observatory task'" c-intent="intent" />
                  <span>{{ intent }}</span>
                </c-CRow>
              </c-for>
            </div>
            <c-CRow align="center">
              <c-for each="size in sizes">
                <c-CSpinner c-label="f'{size} catalog task'" c-size="size" />
              </c-for>
            </c-CRow>
            <div
              x-init="Alpine.store('spinnerQuality', {size: 'md'})"
              data-quality-state="controlled"
            >
              <c-CRow>
                <c-CSpinner
                  label="Controlled sky survey"
                  $c-props="{size: $store.spinnerQuality.size}"
                />
                <button
                  type="button"
                  @click="$store.spinnerQuality.size = $store.spinnerQuality.size === 'md' ? 'lg' : 'md'"
                >
                  Change size
                </button>
              </c-CRow>
            </div>
            <section aria-busy="true" aria-describedby="quality-spinner-busy">
              <c-CRow>
                <c-CSpinner label="Refreshing constellation index" c-attrs="{'id': 'quality-spinner-busy'}" />
                <span>Refreshing constellation index</span>
              </c-CRow>
            </section>
            <div dir="rtl"><c-CSpinner label="تحديث فهرس النجوم" /></div>
            <div style="color-scheme: dark"><c-CSpinner label="Nested dark" intent="success" /></div>
            <div class="spinner-quality-brand spinner-quality-brand--violet">
              <c-CSpinner label="Violet brand" size="lg" />
            </div>
            <div class="spinner-quality-brand spinner-quality-brand--solar">
              <c-CSpinner label="Solar brand" size="lg" />
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
                "sizes": ("sm", "md", "lg"),
            }

        css = """
          :where(.spinner-quality-brand) {
            display: grid;
            place-items: center;
            min-block-size: 5rem;
          }

          :where(.spinner-quality-brand--violet) {
            --cui-spinner-color: light-dark(#6d28d9, #c4b5fd);
            --cui-spinner-track-color: light-dark(#ddd6fe, #4c1d95);
            background: light-dark(#f5f3ff, #21153b);
          }

          :where(.spinner-quality-brand--solar) {
            --cui-spinner-color: light-dark(#c2410c, #fdba74);
            --cui-spinner-track-color: light-dark(#fed7aa, #7c2d12);
            --cui-spinner-thickness: 0.24rem;
            background: light-dark(#fff7ed, #32160d);
          }
        """

    return CitryUiSpinnerStates
