from citry import Component


class AlphanumericPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CField>
        <c-fill name="label">Recovery code</c-fill>
        <c-fill name="description">Use the eight letters and digits printed with your account.</c-fill>
        <c-fill name="default"><c-CPinInput name="recovery" type="alphanumeric" c-length="8" /></c-fill>
      </c-CField>
    """


preview = AlphanumericPinInput()
preview  # noqa: B018
