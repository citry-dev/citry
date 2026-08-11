"""Shared Textarea scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def textarea_states_component(app: Citry) -> type[Component]:
    """Create the reusable Textarea state, form, and environment scenario."""

    class CitryUiTextareaStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack textarea-quality"
            aria-labelledby="textarea-states-title"
            x-data
            x-init="Alpine.store('textareaQuality', {
              controlled: true,
              draft: 'Moss beside the north marker.',
            })"
          >
            <h1 id="textarea-states-title">Textarea states</h1>
            <c-CForm id="textarea-quality-form">
              <c-CField control_id="textarea-quality-controlled" required>
                <c-fill name="label">Controlled observation</c-fill>
                <c-fill name="default">
                  <c-CTextarea
                    id="textarea-quality-controlled"
                    name="observation"
                    value="Server observation"
                    $c-props="{
                      value: $store.textareaQuality.controlled
                        ? $store.textareaQuality.draft
                        : undefined,
                    }"
                    @input="$store.textareaQuality.draft = $event.target.value"
                  />
                </c-fill>
                <c-fill name="description">A required multiline field.</c-fill>
                <c-fill name="error">Add an observation.</c-fill>
              </c-CField>

              <div class="citry-ui-quality-grid">
                <c-for each="variant in variants">
                  <c-CTextarea
                    c-variant="variant"
                    c-value="variant + ' forest note'"
                    c-attrs="{'aria-label': variant + ' Textarea'}"
                  />
                </c-for>
                <c-for each="size in sizes">
                  <c-CTextarea
                    c-size="size"
                    c-value="size + ' specimen record'"
                    c-attrs="{'aria-label': size + ' Textarea'}"
                  />
                </c-for>
                <c-CTextarea
                  disabled
                  value="Closed survey plot"
                  c-attrs="{'aria-label': 'Disabled Textarea'}"
                />
                <c-CTextarea
                  readonly
                  value="Archived trail record"
                  c-attrs="{'aria-label': 'Read-only Textarea'}"
                />
                <c-CTextarea
                  invalid
                  value="Unclear location"
                  c-attrs="{'aria-label': 'Invalid Textarea'}"
                />
                <c-CTextarea
                  wrap="hard"
                  cols="32"
                  resize="both"
                  c-value="long_note"
                  c-attrs="{'aria-label': 'Hard-wrapped Textarea'}"
                />
              </div>

              <div dir="rtl">
                <c-CTextarea
                  c-value="rtl_note"
                  c-attrs="{'aria-label': 'ملاحظة الغابة', 'dir': 'rtl'}"
                />
              </div>
              <div class="textarea-quality__dark" style="color-scheme: dark">
                <c-CTextarea
                  variant="filled"
                  value="Dark nested scheme"
                  c-attrs="{'aria-label': 'Dark Textarea'}"
                />
              </div>
              <div class="textarea-quality__actions">
                <c-CButton
                  type="button"
                  @click="$store.textareaQuality.controlled = false"
                >
                  Release controlled value
                </c-CButton>
                <c-CButton type="reset" variant="outline">
                  Reset journal
                </c-CButton>
              </div>
            </c-CForm>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "variants": ("outline", "filled", "plain"),
                "sizes": ("sm", "md", "lg"),
                "long_note": "A-long-unbroken-forest-observation-code-that-stays-inside-the-native-control.",
                "rtl_note": "كانت أوراق البلوط تتحرك قرب الجدول.",
            }

        css = """
          :where(.textarea-quality) {
            --cui-textarea-focus-color: light-dark(#166534, #86efac);
          }

          :where(.textarea-quality__dark) {
            --cui-textarea-background: #142019;
            --cui-textarea-foreground: #e5f4e8;
            --cui-textarea-border-color: #66806d;
            padding: 1rem;
            background: #0b120d;
          }

          :where(.textarea-quality__actions) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
          }
        """

    return CitryUiTextareaStates
