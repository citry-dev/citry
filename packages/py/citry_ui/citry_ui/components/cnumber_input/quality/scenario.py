"""Shared NumberInput scenario used by repository quality tools."""

from citry import Citry, Component


def number_input_states_component(app: Citry) -> type[Component]:
    """Create the reusable NumberInput state and environment scenario."""

    class CitryUiNumberInputStates(Component):
        citry = app
        template = """
          <section
            class="citry-ui-quality-stack number-input-quality"
            aria-labelledby="number-input-states-title"
            x-data="{controlled:'2.5',last:'No NumberInput action yet'}"
          >
            <h1 id="number-input-states-title">NumberInput states</h1>
            <form
              id="number-input-quality-form"
              @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))"
            >
              <c-CField required>
                <c-fill name="label">Required crate quantity</c-fill>
                <c-fill name="description">Exact quarter steps from 0 through 10.</c-fill>
                <c-fill name="default">
                  <c-CNumberInput
                    name="quantity"
                    value="1.5"
                    min="0"
                    max="10"
                    step="0.25"
                    c-attrs="{'data-quality-states':'required exact form step keyboard reset field description'}"
                    $c-props="{onValueChange:(next,detail)=>last=`${detail.source}: ${next}`}"
                  />
                </c-fill>
              </c-CField>
              <button type="submit">Submit exact value</button>
              <button type="reset">Reset value</button>
            </form>
            <div class="citry-ui-quality-grid">
              <c-CNumberInput
                value="2.5"
                c-input_attrs="{'aria-label':'Controlled quantity'}"
                c-attrs="{'data-quality-states':'controlled refusal acceptance callback'}"
                $c-props="{value:controlled,onValueChange:(next)=>{controlled=next;last=`Accepted ${next}`}}"
              />
              <c-CNumberInput
                value="2"
                min="0"
                max="3"
                step="0.5"
                c-input_attrs="{'aria-label':'Validation quantity'}"
                c-attrs="{'data-quality-states':'minimum maximum invalid incomplete step-grid'}"
              />
              <c-CNumberInput
                value="2"
                c-show_controls="False"
                variant="plain"
                size="sm"
                c-input_attrs="{'aria-label':'Text-only quantity'}"
                c-attrs="{'data-quality-states':'controls-hidden plain sm'}"
              />
              <c-CNumberInput
                value="2"
                readonly
                variant="filled"
                c-input_attrs="{'aria-label':'Readonly quantity'}"
                c-attrs="{'data-quality-states':'readonly filled md submitted'}"
              />
              <c-CNumberInput
                value="2"
                disabled
                size="lg"
                c-input_attrs="{'aria-label':'Disabled quantity'}"
                c-attrs="{'data-quality-states':'disabled lg omitted'}"
              />
              <div dir="rtl" style="color-scheme:dark">
                <c-CNumberInput
                  value="1234.5"
                  step="0.1"
                  wheel
                  c-input_attrs="{'aria-label':'RTL localized quantity'}"
                  c-attrs="{'data-quality-states':'rtl dark localized wheel touch long-content'}"
                />
              </div>
            </div>
            <output x-text="last">No NumberInput action yet</output>
          </section>
        """
        css = """
          :where(.number-input-quality form) { display:grid;gap:.75rem }
          :where(.number-input-quality [dir="rtl"]) { padding:1rem;background:#172033;color:#f8fafc }
        """

    return CitryUiNumberInputStates


__all__ = ["number_input_states_component"]
