from citry import Component


class NumberInputStates(Component):
    template = """
      <section class="number-input-state-grid">
        <c-CNumberInput value="2" variant="outline" size="sm" c-input_attrs="{'aria-label':'Small outline'}" />
        <c-CNumberInput value="2" variant="filled" size="md" c-input_attrs="{'aria-label':'Medium filled'}" />
        <c-CNumberInput value="2" variant="plain" size="lg" c-input_attrs="{'aria-label':'Large plain'}" />
        <c-CNumberInput value="2" readonly c-input_attrs="{'aria-label':'Readonly'}" />
        <c-CNumberInput value="2" disabled c-input_attrs="{'aria-label':'Disabled'}" />
        <c-CNumberInput value="2" invalid c-input_attrs="{'aria-label':'Application invalid'}" />
      </section>
    """
    css = """
      :where(.number-input-state-grid) {
        display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem;align-items:start
      }
    """


preview = NumberInputStates()
preview  # noqa: B018
