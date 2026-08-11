"""Shared Progress scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def progress_states_component(app: Citry) -> type[Component]:
    """Create the reusable native Progress state scenario."""

    class CitryUiProgressStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section class="citry-ui-quality-stack" aria-labelledby="progress-states-title">
            <h1 id="progress-states-title">Progress states</h1>
            <div class="citry-ui-quality-grid">
              <c-for each="intent in intents">
                <div>
                  <span>{{ intent }}</span>
                  <c-CProgress c-label="intent" c-value="62" c-intent="intent" />
                </div>
              </c-for>
            </div>
            <c-CProgress label="Indeterminate expedition task" shape="pill" />
            <c-CProgress
              label="Sample crates cataloged"
              c-value="6"
              c-max="10"
              value_text="6 of 10 sample crates"
              intent="success"
            />
            <c-CGroup>
              <c-for each="size in sizes">
                <c-CProgress c-label="f'{size} progress'" c-value="48" c-size="size" />
              </c-for>
            </c-CGroup>
            <div x-data="{value: 28}" data-quality-state="controlled">
              <c-CProgress label="Controlled sonar upload" $c-props="{value}" />
              <button type="button" @click="value = value === null ? 28 : null">Toggle duration</button>
            </div>
            <section aria-busy="true" aria-describedby="quality-progress-busy">
              <p>Busy survey region</p>
              <c-CProgress
                label="Updating busy survey region"
                c-value="74"
                c-attrs="{'id': 'quality-progress-busy'}"
              />
            </section>
            <div dir="rtl"><c-CProgress label="مسح قاع البحر" c-value="44" /></div>
            <div style="color-scheme: dark"><c-CProgress label="Nested dark" c-value="52" /></div>
            <div class="progress-quality-brand progress-quality-brand--coral">
              <c-CProgress label="Coral brand" c-value="58" shape="pill" />
            </div>
            <div class="progress-quality-brand progress-quality-brand--abyss">
              <c-CProgress label="Abyss brand" c-value="58" shape="pill" />
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
          :where(.progress-quality-brand) {
            padding: 1rem;
          }

          :where(.progress-quality-brand--coral) {
            --cui-progress-track-color: #f8ddd6;
            --cui-progress-range-color: #b9382f;
            --cui-progress-height: 0.75rem;
            background: #fff6f2;
          }

          :where(.progress-quality-brand--abyss) {
            color-scheme: dark;
            --cui-progress-track-color: #1f3b48;
            --cui-progress-range-color: #63d4e8;
            --cui-progress-height: 0.75rem;
            background: #0b1b24;
          }
        """

    return CitryUiProgressStates
