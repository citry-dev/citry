"""Shared DateRange scenario used by repository quality tools."""

# ruff: noqa: E501 - template expressions stay readable as authored HTML

from citry import Citry, Component


def date_range_states_component(app: Citry) -> type[Component]:
    """Create the reusable DateRange state and environment scenario."""

    class CitryUiDateRangeStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack date-range-quality" aria-labelledby="date-range-states-title" x-data="{value:{start:'2026-08-19',end:'2026-08-23'},open:false,last:'No DateRange action yet'}">
            <h1 id="date-range-states-title">DateRange states</h1>
            <form id="date-range-quality-form" @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))">
              <fieldset>
                <legend>Required travel dates</legend>
                <p id="date-range-description">Choose an available interval in August or September 2026.</p>
                <c-CDateRange start_name="arrival" end_name="departure" start="2026-08-16" end="2026-08-19" min="2026-08-10" max="2026-09-15" c-unavailable_dates="('2026-08-20','2026-08-24')" required c-attrs="{'aria-describedby':'date-range-description','data-quality-states':'required canonical form fieldset legend description popup calendar keyboard pointer draft preview same-day normalized reset bounds unavailable localized display trigger-name'}" />
              </fieldset>
              <button type="submit">Submit range</button><button type="reset">Reset range</button>
            </form>
            <div class="citry-ui-quality-grid">
              <fieldset><legend>Controlled range</legend><c-CDateRange start="2026-08-19" end="2026-08-23" $c-props="{value,open,onValueChange:(next,detail)=>{last=`value ${JSON.stringify(next)}`;value=next},onOpenChange:(next,detail)=>{last=`open ${next}`;open=next}}" c-attrs="{'data-quality-states':'controlled value open refusal acceptance callbacks native-events clearable'}" /></fieldset>
              <fieldset><legend>Compact filled</legend><c-CDateRange start="2026-02-14" end="2026-02-16" size="sm" variant="filled" c-fixed_weeks="False" c-show_adjacent_days="False" c-attrs="{'data-quality-states':'filled sm natural-weeks hidden-adjacent'}" /></fieldset>
              <fieldset><legend>Readonly</legend><c-CDateRange start="2026-08-21" end="2026-08-23" size="lg" readonly c-attrs="{'data-quality-states':'readonly submitted lg outline inspectable'}" /></fieldset>
              <fieldset><legend>Disabled</legend><c-CDateRange start="2026-08-22" end="2026-08-23" disabled c-attrs="{'data-quality-states':'disabled omitted md outline'}" /></fieldset>
              <fieldset><legend>Invalid</legend><c-CDateRange start="2026-08-22" end="2026-08-23" invalid c-attrs="{'data-quality-states':'invalid'}" /></fieldset>
              <fieldset lang="ar" dir="rtl" style="color-scheme:dark"><legend>RTL dark range with a deliberately long label</legend><c-CDateRange start="2026-08-24" end="2026-08-27" placement="top-end" c-first_day_of_week="7" c-attrs="{'data-quality-states':'rtl dark locale-week-start placement collision touch long-content'}" /></fieldset>
            </div>
            <output x-text="last">No DateRange action yet</output>
          </section>
        """
        css = """
          :where(.date-range-quality form){display:grid;justify-items:start;gap:.75rem}
          :where(.date-range-quality fieldset){display:grid;align-content:start;gap:.5rem;min-inline-size:0}
          :where(.date-range-quality [dir="rtl"]){padding:1rem;background:#172033;color:#f8fafc}
        """

    return CitryUiDateRangeStates


__all__ = ["date_range_states_component"]
