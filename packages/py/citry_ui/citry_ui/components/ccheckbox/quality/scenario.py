"""Shared Checkbox scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def checkbox_states_component(app: Citry) -> type[Component]:
    """Create the reusable Checkbox state and environment scenario."""

    class CitryUiCheckboxStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack checkbox-quality"
            aria-labelledby="checkbox-states-title"
            x-data
            x-init="Alpine.store('checkboxQuality', {
              controlled: true,
              checked: false,
              mixed: true,
            })"
          >
            <h1 id="checkbox-states-title">Checkbox states</h1>
            <c-CForm id="checkbox-quality-form">
              <c-CField control_id="checkbox-quality-controlled" required>
                <c-fill name="label">Controlled botanical record</c-fill>
                <c-fill name="default">
                  <c-CCheckbox
                    id="checkbox-quality-controlled"
                    name="verified"
                    value="yes"
                    $c-props="{
                      checked: $store.checkboxQuality.controlled
                        ? $store.checkboxQuality.checked
                        : undefined,
                      indeterminate: $store.checkboxQuality.controlled
                        ? $store.checkboxQuality.mixed
                        : undefined,
                    }"
                    @input="$store.checkboxQuality.checked = $event.target.checked;
                      $store.checkboxQuality.mixed = false"
                  />
                </c-fill>
                <c-fill name="description">Required Field-owned description.</c-fill>
                <c-fill name="error">Verify the record.</c-fill>
              </c-CField>

              <div class="citry-ui-quality-grid">
                <c-for each="variant in variants">
                  <c-CCheckbox c-variant="variant" checked>
                    {{ variant }} Checkbox
                  </c-CCheckbox>
                </c-for>
                <c-for each="size in sizes">
                  <c-CCheckbox c-size="size" indeterminate>
                    {{ size }} mixed Checkbox
                  </c-CCheckbox>
                </c-for>
                <c-CCheckbox disabled checked>Disabled Checkbox</c-CCheckbox>
                <c-CCheckbox invalid>Invalid Checkbox</c-CCheckbox>
                <c-CCheckbox required>Required Checkbox</c-CCheckbox>
                <c-CCheckbox label_pos="start" variant="outline">
                  Start-position label
                </c-CCheckbox>
              </div>

              <div dir="rtl">
                <c-CCheckbox label_pos="start">
                  ملاحظة نباتية طويلة للاختبار
                </c-CCheckbox>
              </div>
              <div class="checkbox-quality__dark" style="color-scheme: dark">
                <c-CCheckbox checked>
                  <c-fill name="default">Dark-scheme Checkbox</c-fill>
                  <c-fill name="description">Nested color-scheme description.</c-fill>
                </c-CCheckbox>
              </div>
              <div class="checkbox-quality__actions">
                <c-CButton
                  type="button"
                  @click="$store.checkboxQuality.controlled = false"
                >
                  Release controlled state
                </c-CButton>
                <c-CButton type="reset" variant="outline">
                  Reset checklist
                </c-CButton>
              </div>
            </c-CForm>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "variants": ("solid", "outline"),
                "sizes": ("sm", "md", "lg"),
            }

        css = """
          :where(.checkbox-quality) {
            --cui-checkbox-focus-color: light-dark(#18794e, #86efac);
          }

          :where(.checkbox-quality__dark) {
            --cui-checkbox-active-color: #c4a7ff;
            --cui-checkbox-indicator-color: #21143a;
            --cui-checkbox-description-color: #d6c9ee;

            padding: 1rem;
            background: #171222;
            color: #f4efff;
          }

          :where(.checkbox-quality__actions) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
          }
        """

    return CitryUiCheckboxStates
