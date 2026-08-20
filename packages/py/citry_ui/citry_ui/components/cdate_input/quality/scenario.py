"""Shared DateInput scenario used by repository quality tools."""

# ruff: noqa: E501 - template expressions stay readable as authored HTML

from citry import Citry, Component


def date_input_states_component(app: Citry) -> type[Component]:
    """Create the reusable DateInput state and environment scenario."""

    class CitryUiDateInputStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack date-input-quality" aria-labelledby="date-input-states-title" x-data="{day:'2026-08-19',last:'No DateInput action yet'}">
            <h1 id="date-input-states-title">DateInput states</h1>
            <form id="date-input-quality-form" @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))">
              <c-CField required>
                <c-fill name="label">Required arrival date</c-fill>
                <c-fill name="description">Choose an alternating day in August 2026.</c-fill>
                <c-fill name="default"><c-CDateInput name="arrival" value="2026-08-19" min="2026-08-01" max="2026-08-31" c-step="2" c-attrs="{'data-quality-states':'required canonical native form field description keyboard pointer picker reset bounds step autocomplete'}" /></c-fill>
              </c-CField>
              <button type="submit">Submit date</button><button type="reset">Reset date</button>
            </form>
            <div class="citry-ui-quality-grid">
              <c-CDateInput value="2026-08-19" c-attrs="{'aria-label':'Controlled date','data-quality-states':'controlled native-event refusal acceptance'}" $c-props="{value:day}" @input="last=$event.currentTarget.value" />
              <c-CDateInput value="2026-08-20" size="sm" variant="filled" c-attrs="{'aria-label':'Small filled date','data-quality-states':'filled sm'}" />
              <c-CDateInput value="2026-08-21" size="lg" variant="plain" readonly name="readonly-date" c-attrs="{'aria-label':'Readonly date','data-quality-states':'readonly submitted lg plain'}" />
              <c-CDateInput value="2026-08-22" disabled name="disabled-date" c-attrs="{'aria-label':'Disabled date','data-quality-states':'disabled omitted md outline'}" />
              <c-CDateInput value="2026-08-23" invalid c-attrs="{'aria-label':'Invalid date','data-quality-states':'invalid'}" />
              <div lang="ar" dir="rtl" style="color-scheme:dark"><label for="rtl-date">تاريخ الوصول</label><c-CDateInput id="rtl-date" value="2026-08-24" c-attrs="{'data-quality-states':'rtl dark browser-locale touch long-content'}" /></div>
            </div>
            <output x-text="last">No DateInput action yet</output>
          </section>
        """
        css = """
          :where(.date-input-quality form){display:grid;justify-items:start;gap:.75rem}
          :where(.date-input-quality [dir="rtl"]){display:grid;gap:.5rem;padding:1rem;background:#172033;color:#f8fafc}
        """

    return CitryUiDateInputStates


__all__ = ["date_input_states_component"]
