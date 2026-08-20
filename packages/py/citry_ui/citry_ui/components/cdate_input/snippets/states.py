from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class DateInputStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="date-input-state-grid">
        <c-CDateInput c-attrs="{'aria-label':'Small outlined date'}" value="2026-08-19" size="sm" />
        <c-CDateInput c-attrs="{'aria-label':'Filled date'}" value="2026-08-20" variant="filled" />
        <c-CDateInput c-attrs="{'aria-label':'Large plain date'}" value="2026-08-21" size="lg" variant="plain" />
        <c-CDateInput c-attrs="{'aria-label':'Readonly date'}" value="2026-08-22" readonly />
        <c-CDateInput c-attrs="{'aria-label':'Disabled date'}" value="2026-08-23" disabled />
        <c-CDateInput c-attrs="{'aria-label':'Invalid date'}" value="2026-08-24" invalid />
      </section>
    """
    css = ":where(.date-input-state-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:1rem}"


preview = DateInputStates()
preview  # noqa: B018
