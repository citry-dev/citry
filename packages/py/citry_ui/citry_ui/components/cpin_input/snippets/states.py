from citry import Component


class PinInputStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-state-grid">
        <c-CPinInput label="Small subtle code" value="12" size="sm" variant="subtle" />
        <c-CPinInput label="Default code" value="123" />
        <c-CPinInput label="Large complete code" value="123456" size="lg" />
        <c-CPinInput label="Readonly code" value="246810" readonly />
        <c-CPinInput label="Disabled code" value="135790" disabled />
        <c-CPinInput label="Invalid code" value="12" invalid class_="pin-input-brand" />
      </section>
    """
    css = """
      :where(.pin-input-state-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:1.5rem;align-items:start}
      :where(.pin-input-brand){--cui-pin-input-focus-color:#7c3aed;--cui-pin-input-radius:.75rem}
    """


preview = PinInputStates()
preview  # noqa: B018
