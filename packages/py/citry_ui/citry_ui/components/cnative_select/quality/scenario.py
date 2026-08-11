"""Shared Native Select scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component
from citry_ui import CNativeSelectGroup, CNativeSelectOption


def native_select_states_component(app: Citry) -> type[Component]:
    """Create the reusable Native Select state and environment scenario."""

    class CitryUiNativeSelectStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack native-select-quality"
            aria-labelledby="native-select-states-title"
            x-data
            x-init="Alpine.store('nativeSelectQuality', {
              controlled: true,
              value: 'reef',
            })"
          >
            <h1 id="native-select-states-title">Native Select states</h1>
            <c-CForm id="native-select-quality-form">
              <c-CField control_id="native-select-quality-controlled" required>
                <c-fill name="label">Controlled habitat</c-fill>
                <c-fill name="default">
                  <c-CNativeSelect
                    id="native-select-quality-controlled"
                    name="habitat"
                    c-options="grouped_options"
                    placeholder="Choose a habitat"
                    value="reef"
                    $c-props="{
                      value: $store.nativeSelectQuality.controlled
                        ? $store.nativeSelectQuality.value
                        : undefined,
                    }"
                    @input="$store.nativeSelectQuality.value = $event.target.value"
                  />
                </c-fill>
                <c-fill name="description">A required native grouped choice.</c-fill>
                <c-fill name="error">Choose a habitat.</c-fill>
              </c-CField>

              <div class="citry-ui-quality-grid">
                <c-for each="variant in variants">
                  <c-CNativeSelect
                    c-options="flat_options"
                    c-variant="variant"
                    c-attrs="{'aria-label': variant + ' Native Select'}"
                  />
                </c-for>
                <c-for each="size in sizes">
                  <c-CNativeSelect
                    c-options="flat_options"
                    c-size="size"
                    c-attrs="{'aria-label': size + ' Native Select'}"
                  />
                </c-for>
                <c-CNativeSelect
                  c-options="flat_options"
                  disabled
                  c-attrs="{'aria-label': 'Disabled Native Select'}"
                />
                <c-CNativeSelect
                  c-options="flat_options"
                  invalid
                  c-attrs="{'aria-label': 'Invalid Native Select'}"
                />
              </div>

              <div dir="rtl">
                <c-CNativeSelect
                  c-options="long_options"
                  value="current"
                  c-attrs="{'aria-label': 'تيار المحيط', 'dir': 'rtl'}"
                />
              </div>
              <div class="native-select-quality__dark" style="color-scheme: dark">
                <c-CNativeSelect
                  c-options="flat_options"
                  variant="filled"
                  c-attrs="{'aria-label': 'Dark Native Select'}"
                />
              </div>
              <div class="native-select-quality__actions">
                <c-CButton
                  type="button"
                  @click="$store.nativeSelectQuality.controlled = false"
                >
                  Release controlled value
                </c-CButton>
                <c-CButton type="reset" variant="outline">
                  Reset survey
                </c-CButton>
              </div>
            </c-CForm>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "variants": ("outline", "filled", "plain"),
                "sizes": ("sm", "md", "lg"),
                "flat_options": (
                    CNativeSelectOption("reef", "Coral reef"),
                    CNativeSelectOption("kelp", "Kelp forest"),
                ),
                "grouped_options": (
                    CNativeSelectOption("reef", "Coral reef"),
                    CNativeSelectGroup(
                        "Open ocean",
                        (
                            CNativeSelectOption("pelagic", "Pelagic zone"),
                            CNativeSelectOption("abyss", "Abyssal plain", disabled=True),
                        ),
                    ),
                ),
                "long_options": (
                    CNativeSelectOption(
                        "current",
                        "التيار الاستوائي الطويل عبر محطة الرصد البحرية",
                    ),
                    CNativeSelectOption("gyre", "الدوران المحيطي"),
                ),
            }

        css = """
          :where(.native-select-quality) {
            --cui-native-select-focus-color: light-dark(#087e8b, #76e4f7);
          }

          :where(.native-select-quality__dark) {
            --cui-native-select-background: #10262d;
            --cui-native-select-foreground: #e0f7fa;
            --cui-native-select-border-color: #527b86;
            padding: 1rem;
            background: #08191e;
          }

          :where(.native-select-quality__actions) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
          }
        """

    return CitryUiNativeSelectStates
