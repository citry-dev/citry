"""Shared TimeInput and TimePicker scenario used by repository quality tools."""

# ruff: noqa: E501 - template expressions stay readable as authored HTML

from citry import Citry, Component


def time_states_component(app: Citry) -> type[Component]:
    """Create the reusable Time family state and environment scenario."""

    class CitryUiTimeStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack time-quality" aria-labelledby="time-states-title" x-data="{selected:'09:30',open:false,last:'No time action yet'}">
            <h1 id="time-states-title">TimeInput and TimePicker states</h1>
            <form id="time-quality-form" @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))">
              <c-CField required>
                <c-fill name="label">Required native start time</c-fill>
                <c-fill name="description">Choose a time from 09:00 through 17:00.</c-fill>
                <c-fill name="default"><c-CTimeInput name="native-start" value="09:30" min="09:00" max="17:00" c-step="900" c-attrs="{'data-quality-states':'time-input required canonical native form field description keyboard pointer picker reset bounds step browser-locale'}" /></c-fill>
              </c-CField>
              <c-CField required>
                <c-fill name="label">Required scheduled start time</c-fill>
                <c-fill name="description">Choose one localized finite option.</c-fill>
                <c-fill name="default"><c-CTimePicker name="picker-start" value="09:30" min="09:00" max="12:00" c-attrs="{'data-quality-states':'time-picker required canonical form field description popup listbox keyboard pointer reset bounds step localized display trigger-name native-events clearable'}" /></c-fill>
              </c-CField>
              <button type="submit">Submit times</button><button type="reset">Reset times</button>
            </form>
            <div class="citry-ui-quality-grid">
              <c-CTimePicker value="09:30" min="09:00" max="12:00" $c-props="{value:selected,open,onValueChange:(value,detail)=>{last=`value ${value}`;selected=value},onOpenChange:(value,detail)=>{last=`open ${value}`;open=value}}" c-attrs="{'data-quality-states':'controlled value open refusal acceptance callbacks'}" />
              <c-CTimePicker value="23:00" min="23:00" max="01:00" c-step="3600" size="sm" variant="filled" c-attrs="{'data-quality-states':'wrapped filled sm'}" />
              <c-CTimePicker value="10:00" min="09:00" max="12:00" size="lg" readonly c-attrs="{'data-quality-states':'readonly submitted lg outline inspectable'}" />
              <c-CTimePicker value="10:15" min="09:00" max="12:00" disabled c-attrs="{'data-quality-states':'disabled omitted md outline'}" />
              <c-CTimePicker value="10:30" min="09:00" max="12:00" invalid c-attrs="{'data-quality-states':'invalid'}" />
              <c-CTimeInput value="11:00" variant="plain" readonly c-attrs="{'aria-label':'Readonly native time','data-quality-states':'time-input plain readonly submitted'}" />
              <div lang="ar" dir="rtl" style="color-scheme:dark"><c-CTimePicker value="14:30" min="13:00" max="16:00" placement="top-end" c-attrs="{'data-quality-states':'rtl dark placement collision touch long-content'}" /></div>
            </div>
            <output x-text="last">No time action yet</output>
          </section>
        """
        css = """
          :where(.time-quality form){display:grid;justify-items:start;gap:.75rem}
          :where(.time-quality [dir="rtl"]){display:grid;align-content:start;padding:1rem;background:#172033;color:#f8fafc}
        """

    return CitryUiTimeStates


__all__ = ["time_states_component"]
