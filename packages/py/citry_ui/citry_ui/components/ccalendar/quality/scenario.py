"""Shared Calendar scenario used by repository quality tools."""

# ruff: noqa: E501 - template expressions stay readable as authored HTML

from citry import Citry, Component


def calendar_states_component(app: Citry) -> type[Component]:
    """Create the reusable Calendar state and environment scenario."""

    class CitryUiCalendarStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack calendar-quality" aria-labelledby="calendar-states-title" x-data="{selected:'2026-08-19',visible:'2026-08-19',last:'No Calendar action yet'}">
            <h1 id="calendar-states-title">Calendar states</h1>
            <form id="calendar-quality-form" @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))">
              <c-CField required>
                <c-fill name="label">Required arrival date</c-fill>
                <c-fill name="description">Choose an available date in August or September 2026.</c-fill>
                <c-fill name="default"><c-CCalendar name="arrival" value="2026-08-19" min="2026-08-10" max="2026-09-15" c-unavailable_dates="('2026-08-20','2026-08-24')" c-attrs="{'data-quality-states':'required canonical form field description keyboard pointer reset bounds unavailable localized heading weekdays adjacent fixed-weeks'}" /></c-fill>
                <c-fill name="error">Choose an arrival date.</c-fill>
              </c-CField>
              <button type="submit">Submit date</button><button type="reset">Reset date</button>
            </form>
            <div class="citry-ui-quality-grid">
              <c-CCalendar label="Controlled calendar" value="2026-08-19" visible_date="2026-08-19" $c-props="{value:selected,visibleDate:visible,onValueChange:(value,detail)=>{last=`value ${value}`;selected=value},onVisibleDateChange:(value,detail)=>{last=`visible ${value}`;visible=value}}" c-attrs="{'data-quality-states':'controlled value visible-date refusal acceptance callbacks native-events'}" />
              <c-CCalendar label="Small plain natural calendar" value="2026-02-14" size="sm" variant="plain" c-fixed_weeks="False" c-show_adjacent_days="False" c-attrs="{'data-quality-states':'plain sm natural-weeks hidden-adjacent'}" />
              <c-CCalendar label="Readonly large calendar" value="2026-08-21" size="lg" readonly c-attrs="{'data-quality-states':'readonly submitted lg outline'}" />
              <c-CCalendar label="Disabled calendar" value="2026-08-22" disabled c-attrs="{'data-quality-states':'disabled omitted md outline'}" />
              <c-CCalendar label="Invalid calendar" value="2026-08-23" invalid c-attrs="{'data-quality-states':'invalid'}" />
              <div lang="ar" dir="rtl" style="color-scheme:dark"><c-CCalendar label="تقويم الوصول" value="2026-08-24" c-first_day_of_week="7" c-attrs="{'data-quality-states':'rtl dark locale-week-start arrow-direction touch long-content'}" /></div>
            </div>
            <output x-text="last">No Calendar action yet</output>
          </section>
        """
        css = """
          :where(.calendar-quality form){display:grid;justify-items:start;gap:.75rem}
          :where(.calendar-quality [dir="rtl"]){display:grid;justify-items:start;padding:1rem;background:#172033;color:#f8fafc}
        """

    return CitryUiCalendarStates


__all__ = ["calendar_states_component"]
