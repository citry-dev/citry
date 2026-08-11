"""Shared Listbox scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def listbox_states_component(app: Citry) -> type[Component]:
    class CitryUiListboxStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-listbox-ready>
            <h1>Listbox states</h1>
            <c-CListbox label="Single" value="one" variant="outline">
              <c-CListboxOption value="one">One</c-CListboxOption>
              <c-CListboxOption value="two" disabled>Two</c-CListboxOption>
              <c-CListboxOption value="three">Three</c-CListboxOption>
            </c-CListbox>
            <c-CListbox label="Multiple" multiple c-value="['alpha', 'gamma']" variant="soft" size="sm">
              <c-CListboxGroup label="Letters">
                <c-CListboxOption value="alpha">Alpha</c-CListboxOption>
                <c-CListboxOption value="beta">Beta</c-CListboxOption>
                <c-CListboxOption value="gamma">Gamma</c-CListboxOption>
              </c-CListboxGroup>
            </c-CListbox>
            <fieldset disabled>
              <legend>Locked Listbox</legend>
              <c-CListbox label="Locked">
                <c-CListboxOption value="locked-a">A</c-CListboxOption>
                <c-CListboxOption value="locked-b">B</c-CListboxOption>
              </c-CListbox>
            </fieldset>
            <div dir="rtl">
              <c-CListbox label="قائمة" value="rtl-b" variant="outline">
                <c-CListboxOption value="rtl-a">خيار طويل للغاية</c-CListboxOption>
                <c-CListboxOption value="rtl-b">خيار ثان طويل للغاية</c-CListboxOption>
              </c-CListbox>
            </div>
            <div style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem">
              <c-CListbox label="Night" value="night-b" variant="soft" size="lg">
                <c-CListboxOption value="night-a">Night A</c-CListboxOption>
                <c-CListboxOption value="night-b">Night B</c-CListboxOption>
              </c-CListbox>
            </div>
          </section>
        """

    return CitryUiListboxStates
