"""Shared DatePicker scenario used by repository quality tools."""

# ruff: noqa: E501 - template expressions stay readable as authored HTML

from citry import Citry, Component


def date_picker_states_component(app: Citry) -> type[Component]:
    """Create the reusable DatePicker state and environment scenario."""

    class CitryUiDatePickerStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack date-picker-quality" aria-labelledby="date-picker-states-title" x-data="{selected:'2026-08-19',open:false,last:'No DatePicker action yet'}">
            <h1 id="date-picker-states-title">DatePicker states</h1>
            <form id="date-picker-quality-form" @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))">
              <c-CField required>
                <c-fill name="label">Required arrival date</c-fill>
                <c-fill name="description">Choose an available date in August or September 2026.</c-fill>
                <c-fill name="default"><c-CDatePicker name="arrival" value="2026-08-19" min="2026-08-10" max="2026-09-15" c-unavailable_dates="('2026-08-20','2026-08-24')" c-attrs="{'data-quality-states':'required canonical form field description popup calendar keyboard pointer reset bounds unavailable localized display trigger-name'}" /></c-fill>
                <c-fill name="error">Choose an arrival date.</c-fill>
              </c-CField>
              <button type="submit">Submit date</button><button type="reset">Reset date</button>
            </form>
            <div class="citry-ui-quality-grid">
              <c-CDatePicker value="2026-08-19" $c-props="{value:selected,open,onValueChange:(value,detail)=>{last=`value ${value}`;selected=value},onOpenChange:(value,detail)=>{last=`open ${value}`;open=value}}" c-attrs="{'data-quality-states':'controlled value open refusal acceptance callbacks native-events clearable'}" />
              <c-CDatePicker value="2026-02-14" size="sm" variant="filled" c-fixed_weeks="False" c-show_adjacent_days="False" c-attrs="{'data-quality-states':'filled sm natural-weeks hidden-adjacent'}" />
              <c-CDatePicker value="2026-08-21" size="lg" readonly c-attrs="{'data-quality-states':'readonly submitted lg outline inspectable'}" />
              <c-CDatePicker value="2026-08-22" disabled c-attrs="{'data-quality-states':'disabled omitted md outline'}" />
              <c-CDatePicker value="2026-08-23" invalid c-attrs="{'data-quality-states':'invalid'}" />
              <div lang="ar" dir="rtl" style="color-scheme:dark"><c-CDatePicker value="2026-08-24" placement="top-end" c-first_day_of_week="7" c-attrs="{'data-quality-states':'rtl dark locale-week-start placement collision touch long-content'}" /></div>
            </div>
            <output x-text="last">No DatePicker action yet</output>
          </section>
        """
        css = """
          :where(.date-picker-quality form){display:grid;justify-items:start;gap:.75rem}
          :where(.date-picker-quality [dir="rtl"]){display:grid;align-content:start;padding:1rem;background:#172033;color:#f8fafc}
        """

    return CitryUiDatePickerStates


__all__ = ["date_picker_states_component"]
