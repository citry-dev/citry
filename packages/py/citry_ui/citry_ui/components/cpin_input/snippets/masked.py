from citry import Component


class MaskedPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-demo-stack">
        <c-CPinInput label="Private access code" name="access-code" value="7412" c-length="4" mask />
        <p>Masking changes the visual cells only. Treat the submitted token as sensitive data.</p>
      </section>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = MaskedPinInput()
preview  # noqa: B018
