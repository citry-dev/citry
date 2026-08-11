"""Shared Radio scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def radio_states_component(app: Citry) -> type[Component]:
    """Create the reusable Radio state and environment scenario."""

    class CitryUiRadioStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section class="citry-ui-quality-stack" aria-labelledby="radio-states-title">
            <h1 id="radio-states-title">Radio states</h1>
            <div class="citry-ui-quality-grid">
              <c-CRadioGroup name="quality-basic" value="fern">
                <c-fill name="label">Garden layer</c-fill>
                <c-fill name="default">
                  <c-CRadio value="fern">Fern understory</c-CRadio>
                  <c-CRadio value="canopy">Tree canopy</c-CRadio>
                  <c-CRadio value="pond" disabled>Pond edge</c-CRadio>
                </c-fill>
              </c-CRadioGroup>
              <c-CRadioGroup name="quality-outline" variant="outline" orientation="horizontal" size="sm">
                <c-fill name="label">Small outline</c-fill>
                <c-fill name="default">
                  <c-CRadio value="dawn">Dawn</c-CRadio>
                  <c-CRadio value="dusk">Dusk</c-CRadio>
                </c-fill>
              </c-CRadioGroup>
              <c-CRadioGroup name="quality-large" value="leaf" size="lg" label_pos="start">
                <c-fill name="label">Large labels first</c-fill>
                <c-fill name="default">
                  <c-CRadio value="leaf">Leaf</c-CRadio>
                  <c-CRadio value="flower">Flower</c-CRadio>
                </c-fill>
              </c-CRadioGroup>
              <c-CRadioGroup name="quality-disabled" value="rest" disabled>
                <c-fill name="label">Disabled group</c-fill>
                <c-fill name="default"><c-CRadio value="rest">Winter rest</c-CRadio></c-fill>
              </c-CRadioGroup>
            </div>
            <div x-data="{value: 'moss'}" data-quality-state="controlled">
              <c-CRadioGroup
                name="quality-controlled"
                $c-props="{value}"
                @input="value = $event.target.value"
                orientation="horizontal"
              >
                <c-fill name="label">Controlled ground cover</c-fill>
                <c-fill name="default">
                  <c-CRadio value="moss">Moss</c-CRadio>
                  <c-CRadio value="clover">Clover</c-CRadio>
                </c-fill>
              </c-CRadioGroup>
              <button type="button" @click="value = value === 'moss' ? 'clover' : 'moss'">Change choice</button>
            </div>
            <form data-quality-state="formdata">
              <c-CRadioGroup name="quality-form" required>
                <c-fill name="label">Required plot</c-fill>
                <c-fill name="default">
                  <c-CRadio value="north">North plot</c-CRadio>
                  <c-CRadio value="south">South plot</c-CRadio>
                </c-fill>
              </c-CRadioGroup>
              <button type="reset">Reset</button>
            </form>
            <c-CField control_id="quality-radio-field" required>
              <c-fill name="label">Field-owned exposure</c-fill>
              <c-fill name="default">
                <c-CRadioGroup name="quality-field">
                  <c-CRadio value="sun">Sun</c-CRadio>
                  <c-CRadio value="shade">Shade</c-CRadio>
                </c-CRadioGroup>
              </c-fill>
              <c-fill name="description">Choose the light available to the planting bed.</c-fill>
              <c-fill name="error">Choose one light level.</c-fill>
            </c-CField>
            <div dir="rtl">
              <c-CRadioGroup name="quality-rtl" value="east" orientation="horizontal">
                <c-fill name="label">اتجاه الحديقة</c-fill>
                <c-fill name="default">
                  <c-CRadio value="east">الشرق</c-CRadio>
                  <c-CRadio value="west">الغرب</c-CRadio>
                </c-fill>
              </c-CRadioGroup>
            </div>
            <div style="color-scheme: dark">
              <c-CRadioGroup name="quality-dark" value="night">
                <c-fill name="label">Nested dark</c-fill>
                <c-fill name="default"><c-CRadio value="night">Night garden</c-CRadio></c-fill>
              </c-CRadioGroup>
            </div>
            <div class="radio-quality-brand radio-quality-brand--fern">
              <c-CRadioGroup name="quality-fern" value="fern">
                <c-fill name="label">Fern brand</c-fill>
                <c-fill name="default"><c-CRadio value="fern">Fern</c-CRadio></c-fill>
              </c-CRadioGroup>
            </div>
            <div class="radio-quality-brand radio-quality-brand--bloom">
              <c-CRadioGroup name="quality-bloom" value="bloom">
                <c-fill name="label">Bloom brand</c-fill>
                <c-fill name="default"><c-CRadio value="bloom">Bloom</c-CRadio></c-fill>
              </c-CRadioGroup>
            </div>
          </section>
        """

        css = """
          :where(.radio-quality-brand) {
            padding: 1rem;
            border-radius: 0.75rem;
          }

          :where(.radio-quality-brand--fern) {
            --cui-radio-active-color: light-dark(#28784c, #6ee7a3);
            --cui-radio-foreground: light-dark(#173927, #d9f5e2);
            background: light-dark(#edf8f0, #10251a);
          }

          :where(.radio-quality-brand--bloom) {
            --cui-radio-active-color: light-dark(#a33b72, #f4a5ce);
            --cui-radio-foreground: light-dark(#4f1736, #fde0ef);
            background: light-dark(#fff1f7, #321325);
          }
        """

    return CitryUiRadioStates
