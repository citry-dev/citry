"""Shared PinInput scenario used by repository quality tools."""

# ruff: noqa: E501 - template expressions stay readable as authored HTML

from citry import Citry, Component


def pin_input_states_component(app: Citry) -> type[Component]:
    """Create the reusable PinInput state and environment scenario."""

    class CitryUiPinInputStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack pin-input-quality" aria-labelledby="pin-input-states-title" x-data="{code:'12',last:'No PinInput action yet'}">
            <h1 id="pin-input-states-title">PinInput states</h1>
            <form id="pin-input-quality-form" @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))">
              <c-CField required>
                <c-fill name="label">Required verification code</c-fill>
                <c-fill name="description">Enter all six digits.</c-fill>
                <c-fill name="default">
                  <c-CPinInput name="verification" value="01" c-attrs="{'data-quality-states':'required numeric partial form field description keyboard pointer paste autofill invalid-filter reset one-time-code'}" $c-props="{onValueChange:(next,detail)=>last=`${detail.source}: ${next}`,onComplete:(next)=>last=`Complete: ${next}`}" />
                </c-fill>
              </c-CField>
              <button type="submit">Submit code</button><button type="reset">Reset code</button>
            </form>
            <div class="citry-ui-quality-grid">
              <c-CPinInput label="Controlled code" value="12" c-length="4" c-attrs="{'data-quality-states':'controlled callback refusal acceptance'}" $c-props="{value:code,onValueChange:(next)=>{code=next;last=`Accepted ${next}`}}" />
              <c-CPinInput label="Alphanumeric recovery code" value="A7C9" type="alphanumeric" c-length="6" size="sm" variant="subtle" c-attrs="{'data-quality-states':'alphanumeric subtle sm'}" />
              <c-CPinInput label="Masked code" value="987654" mask c-attrs="{'data-quality-states':'masked md outline'}" />
              <c-CPinInput label="Readonly code" value="246810" readonly name="readonly-code" size="lg" c-attrs="{'data-quality-states':'readonly submitted lg complete'}" />
              <c-CPinInput label="Disabled code" value="135790" disabled name="disabled-code" c-attrs="{'data-quality-states':'disabled omitted'}" />
              <c-CPinInput label="Invalid grouped code" value="12" invalid attached c-separator_after="(2,)" c-attrs="{'data-quality-states':'invalid separator attached touch long-content'}"><c-fill name="separator" data="{ index }">-</c-fill></c-CPinInput>
              <div dir="rtl" style="color-scheme:dark"><c-CPinInput label="رمز التحقق" value="104" c-attrs="{'data-quality-states':'rtl dark ltr-token'}" /></div>
            </div>
            <output x-text="last">No PinInput action yet</output>
          </section>
        """
        css = """
          :where(.pin-input-quality form){display:grid;justify-items:start;gap:.75rem}
          :where(.pin-input-quality [dir="rtl"]){padding:1rem;background:#172033;color:#f8fafc}
        """

    return CitryUiPinInputStates


__all__ = ["pin_input_states_component"]
