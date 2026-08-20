"""Shared Slider scenario used by repository quality tools."""

# ruff: noqa: E501 - quality coverage tokens remain legible beside their component

from citry import Citry, Component


def slider_states_component(app: Citry) -> type[Component]:
    """Create the reusable Slider and RangeSlider state scenario."""

    class CitryUiSliderStates(Component):
        citry = app
        template = """
          <section
            class="citry-ui-quality-stack slider-quality"
            aria-labelledby="slider-states-title"
            x-data="{controlled:['20','80'],last:'No Slider action yet'}"
          >
            <h1 id="slider-states-title">Slider and RangeSlider states</h1>
            <form
              id="slider-quality-form"
              @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))"
            >
              <c-CField>
                <c-fill name="label">Exact volume</c-fill>
                <c-fill name="description">Quarter steps from 0 through 10.</c-fill>
                <c-fill name="default">
                  <c-CSlider
                    name="volume"
                    value="2.5"
                    min="0"
                    max="10"
                    step="0.25"
                    c-marks="{0:'Silent',5:'Medium',10:'Maximum'}"
                    c-attrs="{'data-quality-states':'single exact form marks keyboard pointer reset field description'}"
                    $c-props="{onValueChange:(next,detail)=>last=`${detail.source}: ${next}`}"
                  />
                </c-fill>
              </c-CField>
              <button type="submit">Submit exact value</button>
              <button type="reset">Reset value</button>
            </form>
            <div class="citry-ui-quality-grid">
              <c-CRangeSlider
                name="price"
                c-value="(20, 80)"
                c-min_steps_between_thumbs="10"
                c-attrs="{'data-quality-states':'range lower upper collision tab-order localized labels'}"
                $c-props="{value:controlled,onValueChange:(next)=>{controlled=next;last=`Accepted ${next.join('-')}`}}"
              />
              <c-CSlider
                value="30"
                variant="subtle"
                size="sm"
                c-input_attrs="{'aria-label':'Subtle small value'}"
                c-attrs="{'data-quality-states':'subtle sm interaction-value'}"
              />
              <c-CSlider
                value="50"
                show_value="always"
                c-input_attrs="{'aria-label':'Always visible value'}"
                c-attrs="{'data-quality-states':'solid md value-always'}"
              />
              <c-CSlider
                value="70"
                readonly
                size="lg"
                c-input_attrs="{'aria-label':'Readonly value'}"
                c-attrs="{'data-quality-states':'readonly submitted lg'}"
              />
              <c-CSlider
                value="90"
                disabled
                invalid
                c-input_attrs="{'aria-label':'Disabled invalid value'}"
                c-attrs="{'data-quality-states':'disabled omitted invalid'}"
              />
              <div dir="rtl" style="color-scheme:dark">
                <c-CRangeSlider
                  c-value="('1234.5', '5678.5')"
                  min="0"
                  max="10000"
                  step="0.5"
                  show_value="always"
                  c-attrs="{'data-quality-states':'rtl dark localized long-content touch'}"
                />
              </div>
              <c-CSlider
                value="40"
                orientation="vertical"
                c-input_attrs="{'aria-label':'Vertical level'}"
                c-attrs="{'data-quality-states':'vertical narrow'}"
              />
            </div>
            <output x-text="last">No Slider action yet</output>
          </section>
        """
        css = """
          :where(.slider-quality form){display:grid;gap:1rem}
          :where(.slider-quality [dir="rtl"]){padding:1rem;background:#172033;color:#f8fafc}
          :where(.slider-quality [data-orientation="vertical"]){min-block-size:12rem}
        """

    return CitryUiSliderStates


__all__ = ["slider_states_component"]
