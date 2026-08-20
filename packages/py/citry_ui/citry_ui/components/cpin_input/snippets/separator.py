from citry import Component


class SeparatedPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-demo-stack">
        <c-CPinInput label="Grouped recovery code" type="alphanumeric" c-separator_after="(2,)">
          <c-fill name="separator" data="{ index }">-</c-fill>
        </c-CPinInput>
        <c-CPinInput label="Attached four-digit code" c-length="4" attached />
      </section>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = SeparatedPinInput()
preview  # noqa: B018
